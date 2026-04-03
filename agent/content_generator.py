"""
Oeconomia Twitter Agent — Content Generator
Uses Claude API to generate tweets + image prompts as structured JSON.
Includes dedup logic against Supabase twitter_posts table (50-char prefix match within 30 days).
"""

import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional

import anthropic

from config.settings import (
    ANTHROPIC_API_KEY,
    CLAUDE_MODEL,
    IMAGE_MODE,
    get_supabase,
)
from config.brand_voice import BRAND_SYSTEM_PROMPT

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Post log helpers (Supabase)
# ---------------------------------------------------------------------------


def _load_recent_posts(window_days: int = 30) -> list[dict]:
    """Load recent posts from Supabase twitter_posts table."""
    try:
        sb = get_supabase()
        cutoff = (datetime.now(timezone.utc) - timedelta(days=window_days)).isoformat()
        result = (
            sb.table("twitter_posts")
            .select("tweet_text, created_at")
            .gte("created_at", cutoff)
            .execute()
        )
        return result.data or []
    except Exception as e:
        logger.warning("Could not load posts from Supabase for dedup: %s", e)
        return []


def _is_duplicate(tweet_text: str, recent_posts: list[dict]) -> bool:
    """
    Check if the first 50 characters of tweet_text match any post
    from the recent posts list.
    """
    prefix = tweet_text[:50].strip().lower()

    for entry in recent_posts:
        existing_prefix = entry.get("tweet_text", "")[:50].strip().lower()
        if existing_prefix == prefix:
            return True

    return False


# ---------------------------------------------------------------------------
# Content generation
# ---------------------------------------------------------------------------

def generate_content(
    post_type: str = "technical",
    max_retries: int = 3,
) -> Optional[dict]:
    """
    Call Claude to generate a tweet + optional image prompt.

    Args:
        post_type: One of "technical", "hype", "educational", "philosophical".
        max_retries: Number of dedup retries before giving up.

    Returns:
        Dict with keys: tweet_text, post_type, image_prompt, thread
        or None on failure.
    """
    if not ANTHROPIC_API_KEY:
        logger.error("ANTHROPIC_API_KEY not set — cannot generate content")
        return None

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    recent_posts = _load_recent_posts()

    # Build the user prompt
    image_instruction = ""
    if IMAGE_MODE == "none":
        image_instruction = 'Set "image_prompt" to null — no image for this post.'
    else:
        image_instruction = (
            'Include a vivid "image_prompt" suitable for DALL-E 3. '
            "Describe a scene, not text. Focus on atmosphere, lighting, and symbolism."
        )

    user_prompt = (
        f"Generate a single {post_type} tweet for the Oeconomia (@CryptoM33156512) Twitter account.\n\n"
        f"{image_instruction}\n\n"
        "Respond with ONLY valid JSON matching the schema in your system prompt. "
        "No markdown fences, no explanation."
    )

    for attempt in range(1, max_retries + 1):
        try:
            logger.info(
                "Generating %s tweet (attempt %d/%d)...",
                post_type, attempt, max_retries,
            )

            response = client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=1024,
                system=BRAND_SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_prompt}],
            )

            raw_text = response.content[0].text.strip()

            # Strip markdown code fences if Claude wraps them anyway
            if raw_text.startswith("```"):
                raw_text = raw_text.split("\n", 1)[-1]
            if raw_text.endswith("```"):
                raw_text = raw_text.rsplit("```", 1)[0]
            raw_text = raw_text.strip()

            result = json.loads(raw_text)

            # Validate required fields
            tweet_text = result.get("tweet_text", "")
            if not tweet_text:
                logger.warning("Empty tweet_text in Claude response — retrying")
                continue

            # Dedup check
            if _is_duplicate(tweet_text, recent_posts):
                logger.info(
                    "Duplicate detected (50-char prefix match) — retrying"
                )
                user_prompt += "\n\nIMPORTANT: Your previous suggestion was too similar to a recent post. Generate something substantially different."
                continue

            # Normalize fields
            result.setdefault("post_type", post_type)
            result.setdefault("image_prompt", None)
            result.setdefault("thread", None)

            # Nullify image prompt if mode is "none"
            if IMAGE_MODE == "none":
                result["image_prompt"] = None

            logger.info("Generated tweet: %s", tweet_text[:80])
            return result

        except json.JSONDecodeError as e:
            logger.error("Failed to parse Claude JSON (attempt %d): %s", attempt, e)
            logger.debug("Raw response: %s", raw_text if 'raw_text' in dir() else "N/A")
        except anthropic.APIError as e:
            logger.error("Claude API error (attempt %d): %s", attempt, e)
        except Exception as e:
            logger.error("Unexpected error (attempt %d): %s", attempt, e)

    logger.error("Failed to generate content after %d attempts", max_retries)
    return None
