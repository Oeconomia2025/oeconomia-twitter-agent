"""
Oeconomia Twitter Agent — Image Prompt Logger
Appends image prompt metadata to data/image_prompts.csv for tracking.
"""

import csv
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from config.settings import IMAGE_PROMPTS_CSV

logger = logging.getLogger(__name__)

# CSV column headers
FIELDNAMES = [
    "timestamp",
    "post_type",
    "tweet_text_preview",
    "image_prompt",
    "style_tags",
    "dalle_path",
    "status",
]


def _ensure_csv_header() -> None:
    """Create the CSV file with headers if it doesn't exist."""
    if not IMAGE_PROMPTS_CSV.exists():
        IMAGE_PROMPTS_CSV.parent.mkdir(parents=True, exist_ok=True)
        with open(IMAGE_PROMPTS_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()
        logger.info("Created image_prompts.csv with headers")


def log_image_prompt(
    post_type: str,
    tweet_text: str,
    image_prompt: Optional[str],
    dalle_path: Optional[Path],
    status: str = "generated",
    style_tags: str = "dark_cinematic,neon_teal,amber,defi",
) -> None:
    """
    Append a row to the image prompts CSV.

    Args:
        post_type: The type of post (technical, hype, etc.).
        tweet_text: Full tweet text (will be truncated to 80 chars for preview).
        image_prompt: The DALL-E prompt used (or None).
        dalle_path: Path to the generated image file (or None).
        status: One of "generated", "manual_pending", "skipped", "policy_blocked".
        style_tags: Comma-separated style descriptors.
    """
    _ensure_csv_header()

    row = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "post_type": post_type,
        "tweet_text_preview": tweet_text[:80] if tweet_text else "",
        "image_prompt": image_prompt or "",
        "style_tags": style_tags,
        "dalle_path": str(dalle_path) if dalle_path else "",
        "status": status,
    }

    try:
        with open(IMAGE_PROMPTS_CSV, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writerow(row)
        logger.info("Logged image prompt (%s): %s", status, (image_prompt or "")[:60])
    except IOError as e:
        logger.error("Failed to write to image_prompts.csv: %s", e)
