"""
Oeconomia Twitter Agent — Image Prompt Logger
Writes image prompt metadata to the Supabase image_prompts table.
"""

import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from config.settings import get_supabase

logger = logging.getLogger(__name__)


def log_image_prompt(
    post_type: str,
    tweet_text: str,
    image_prompt: Optional[str],
    dalle_path: Optional[Path],
    status: str = "generated",
    style_tags: str = "dark_cinematic,neon_teal,amber,defi",
    post_id: Optional[str] = None,
) -> None:
    """
    Insert a row into the Supabase image_prompts table.

    Args:
        post_type: The type of post (technical, hype, etc.).
        tweet_text: Full tweet text (will be truncated to 80 chars for preview).
        image_prompt: The DALL-E prompt used (or None).
        dalle_path: Path to the generated image file (or None).
        status: One of "generated", "manual_pending", "skipped", "policy_blocked".
        style_tags: Comma-separated style descriptors.
        post_id: Optional UUID of the parent twitter_posts row.
    """
    row = {
        "post_type": post_type,
        "tweet_text_preview": tweet_text[:80] if tweet_text else "",
        "image_prompt": image_prompt or "",
        "style_tags": [t.strip() for t in style_tags.split(",") if t.strip()],
        "dalle_path": str(dalle_path) if dalle_path else None,
        "status": status,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    if post_id:
        row["post_id"] = post_id

    try:
        sb = get_supabase()
        result = sb.table("image_prompts").insert(row).execute()
        logger.info("Logged image prompt to Supabase (%s): %s", status, (image_prompt or "")[:60])
    except Exception as e:
        logger.error("Failed to write to Supabase image_prompts: %s", e)
