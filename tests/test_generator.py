"""
Tests for content_generator.py
Covers: Claude API mocking, JSON parsing, dedup logic, IMAGE_MODE switching.

Run with: python -m pytest tests/test_generator.py -v
"""

import json
import os
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _set_env(monkeypatch):
    """Set required env vars for every test."""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-key")
    monkeypatch.setenv("DRY_RUN", "true")


@pytest.fixture
def tmp_post_log(tmp_path, monkeypatch):
    """Provide a temporary post_log.json path."""
    log_path = tmp_path / "post_log.json"
    monkeypatch.setattr("agent.content_generator.POST_LOG_PATH", log_path)
    return log_path


@pytest.fixture
def sample_claude_response():
    """A valid Claude JSON response."""
    return {
        "tweet_text": "Building in DeFi means building for financial sovereignty. Oeconomia is the foundation.",
        "post_type": "philosophical",
        "image_prompt": "A glowing digital fortress on a dark landscape, neon teal beams rising from decentralized nodes",
        "thread": None,
    }


# ---------------------------------------------------------------------------
# JSON Parsing Tests
# ---------------------------------------------------------------------------

class TestJSONParsing:
    """Test that Claude responses are parsed correctly."""

    @patch("agent.content_generator.anthropic")
    def test_valid_json_parsed(self, mock_anthropic, tmp_post_log, sample_claude_response):
        """Valid JSON from Claude is parsed into expected dict."""
        from agent.content_generator import generate_content

        mock_client = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_client

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps(sample_claude_response))]
        mock_client.messages.create.return_value = mock_response

        result = generate_content(post_type="philosophical")

        assert result is not None
        assert result["tweet_text"] == sample_claude_response["tweet_text"]
        assert result["post_type"] == "philosophical"
        assert result["image_prompt"] is not None

    @patch("agent.content_generator.anthropic")
    def test_json_with_code_fences(self, mock_anthropic, tmp_post_log, sample_claude_response):
        """JSON wrapped in markdown code fences is still parsed."""
        from agent.content_generator import generate_content

        mock_client = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_client

        wrapped = f"```json\n{json.dumps(sample_claude_response)}\n```"
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=wrapped)]
        mock_client.messages.create.return_value = mock_response

        result = generate_content(post_type="technical")
        assert result is not None
        assert result["tweet_text"] == sample_claude_response["tweet_text"]

    @patch("agent.content_generator.anthropic")
    def test_invalid_json_returns_none(self, mock_anthropic, tmp_post_log):
        """Invalid JSON after all retries returns None."""
        from agent.content_generator import generate_content

        mock_client = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_client

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="This is not JSON at all")]
        mock_client.messages.create.return_value = mock_response

        result = generate_content(post_type="hype", max_retries=2)
        assert result is None

    @patch("agent.content_generator.anthropic")
    def test_empty_tweet_text_retries(self, mock_anthropic, tmp_post_log):
        """Empty tweet_text triggers retry."""
        from agent.content_generator import generate_content

        mock_client = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_client

        empty_response = json.dumps({
            "tweet_text": "",
            "post_type": "hype",
            "image_prompt": None,
            "thread": None,
        })
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=empty_response)]
        mock_client.messages.create.return_value = mock_response

        result = generate_content(post_type="hype", max_retries=2)
        assert result is None  # All retries exhausted with empty text


# ---------------------------------------------------------------------------
# Dedup Tests
# ---------------------------------------------------------------------------

class TestDedup:
    """Test 50-char prefix dedup within 30 days."""

    def test_duplicate_detected(self, tmp_post_log):
        """Exact 50-char prefix match within 30 days is detected."""
        from agent.content_generator import _is_duplicate

        existing_log = [
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "tweet_text": "Building in DeFi means building for financial sovereignty. Oeconomia is the foundation.",
            }
        ]

        # Same first 50 chars
        assert _is_duplicate(
            "Building in DeFi means building for financial sov— something different here",
            existing_log,
        )

    def test_old_post_not_duplicate(self, tmp_post_log):
        """Posts older than 30 days are NOT considered duplicates."""
        from agent.content_generator import _is_duplicate

        old_time = (datetime.now(timezone.utc) - timedelta(days=31)).isoformat()
        existing_log = [
            {
                "timestamp": old_time,
                "tweet_text": "Building in DeFi means building for financial sovereignty. Oeconomia is the foundation.",
            }
        ]

        assert not _is_duplicate(
            "Building in DeFi means building for financial sovereignty. Oeconomia is the foundation.",
            existing_log,
        )

    def test_different_text_not_duplicate(self, tmp_post_log):
        """Different text is not a duplicate."""
        from agent.content_generator import _is_duplicate

        existing_log = [
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "tweet_text": "Completely different tweet about something else entirely for testing purposes.",
            }
        ]

        assert not _is_duplicate(
            "Building in DeFi means building for financial sovereignty.",
            existing_log,
        )

    def test_empty_log_no_duplicate(self, tmp_post_log):
        """Empty log never triggers duplicate."""
        from agent.content_generator import _is_duplicate

        assert not _is_duplicate("Any tweet text here works fine", [])

    @patch("agent.content_generator.anthropic")
    def test_dedup_triggers_retry(self, mock_anthropic, tmp_post_log, sample_claude_response):
        """When Claude generates a duplicate, it retries with a new prompt."""
        from agent.content_generator import generate_content

        # Pre-populate log with existing tweet
        existing_log = [
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "tweet_text": sample_claude_response["tweet_text"],
            }
        ]
        with open(tmp_post_log, "w") as f:
            json.dump(existing_log, f)

        mock_client = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_client

        # Claude returns same text every time -> all retries fail dedup
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps(sample_claude_response))]
        mock_client.messages.create.return_value = mock_response

        result = generate_content(post_type="philosophical", max_retries=2)

        # Should fail after exhausting retries
        assert result is None
        # Claude was called multiple times (retries)
        assert mock_client.messages.create.call_count == 2


# ---------------------------------------------------------------------------
# IMAGE_MODE Tests
# ---------------------------------------------------------------------------

class TestImageMode:
    """Test that IMAGE_MODE correctly controls image_prompt output."""

    @patch("agent.content_generator.IMAGE_MODE", "none")
    @patch("agent.content_generator.anthropic")
    def test_image_mode_none_nullifies_prompt(self, mock_anthropic, tmp_post_log, sample_claude_response):
        """IMAGE_MODE=none sets image_prompt to null even if Claude provides one."""
        from agent.content_generator import generate_content

        mock_client = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_client

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps(sample_claude_response))]
        mock_client.messages.create.return_value = mock_response

        result = generate_content(post_type="technical")

        assert result is not None
        assert result["image_prompt"] is None

    @patch("agent.content_generator.IMAGE_MODE", "dalle")
    @patch("agent.content_generator.anthropic")
    def test_image_mode_dalle_preserves_prompt(self, mock_anthropic, tmp_post_log, sample_claude_response):
        """IMAGE_MODE=dalle preserves the image_prompt from Claude."""
        from agent.content_generator import generate_content

        mock_client = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_client

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps(sample_claude_response))]
        mock_client.messages.create.return_value = mock_response

        result = generate_content(post_type="hype")

        assert result is not None
        assert result["image_prompt"] == sample_claude_response["image_prompt"]

    @patch("agent.content_generator.IMAGE_MODE", "manual")
    @patch("agent.content_generator.anthropic")
    def test_image_mode_manual_preserves_prompt(self, mock_anthropic, tmp_post_log, sample_claude_response):
        """IMAGE_MODE=manual preserves the image_prompt (for manual use)."""
        from agent.content_generator import generate_content

        mock_client = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_client

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text=json.dumps(sample_claude_response))]
        mock_client.messages.create.return_value = mock_response

        result = generate_content(post_type="educational")

        assert result is not None
        assert result["image_prompt"] is not None


# ---------------------------------------------------------------------------
# API Key Validation
# ---------------------------------------------------------------------------

class TestAPIKeyValidation:

    @patch("agent.content_generator.ANTHROPIC_API_KEY", "")
    def test_missing_api_key_returns_none(self, tmp_post_log):
        """Missing API key returns None without calling the API."""
        from agent.content_generator import generate_content

        result = generate_content(post_type="technical")
        assert result is None
