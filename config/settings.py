"""
Oeconomia Twitter Agent — Settings
Loads all configuration from .env via python-dotenv.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
_project_root = Path(__file__).resolve().parent.parent
load_dotenv(_project_root / ".env")

# ---------------------------------------------------------------------------
# Anthropic (Claude)
# ---------------------------------------------------------------------------
ANTHROPIC_API_KEY: str = os.getenv("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL: str = os.getenv("CLAUDE_MODEL", "claude-sonnet-4-5")

# ---------------------------------------------------------------------------
# OpenAI (DALL-E 3)
# ---------------------------------------------------------------------------
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

# ---------------------------------------------------------------------------
# Twitter / X API
# ---------------------------------------------------------------------------
TWITTER_API_KEY: str = os.getenv("TWITTER_API_KEY", "")
TWITTER_API_SECRET: str = os.getenv("TWITTER_API_SECRET", "")
TWITTER_ACCESS_TOKEN: str = os.getenv("TWITTER_ACCESS_TOKEN", "")
TWITTER_ACCESS_TOKEN_SECRET: str = os.getenv("TWITTER_ACCESS_TOKEN_SECRET", "")
TWITTER_BEARER_TOKEN: str = os.getenv("TWITTER_BEARER_TOKEN", "")

# ---------------------------------------------------------------------------
# Telegram (optional)
# ---------------------------------------------------------------------------
TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID: str = os.getenv("TELEGRAM_CHAT_ID", "")

# ---------------------------------------------------------------------------
# Agent behavior
# ---------------------------------------------------------------------------
DRY_RUN: bool = os.getenv("DRY_RUN", "true").lower() in ("true", "1", "yes")

# IMAGE_MODE: "dalle" | "manual" | "none"
IMAGE_MODE: str = os.getenv("IMAGE_MODE", "manual").lower()

POST_FREQUENCY_MIN: int = int(os.getenv("POST_FREQUENCY_MIN", "2"))
POST_FREQUENCY_MAX: int = int(os.getenv("POST_FREQUENCY_MAX", "4"))

TIMEZONE: str = os.getenv("TIMEZONE", "America/Los_Angeles")

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
DATA_DIR: Path = _project_root / "data"
GENERATED_IMAGES_DIR: Path = DATA_DIR / "generated_images"
POST_LOG_PATH: Path = DATA_DIR / "post_log.json"
IMAGE_PROMPTS_CSV: Path = DATA_DIR / "image_prompts.csv"

# Ensure directories exist
GENERATED_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
