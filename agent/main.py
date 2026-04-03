"""
Oeconomia Twitter Agent — Main Entry Point
Wires together: content generation -> image prompt logging -> DALL-E image ->
Twitter posting -> Telegram notification -> Supabase post log.
"""

import json
import logging
import signal
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from config.settings import (
    DRY_RUN,
    IMAGE_MODE,
    get_supabase,
)
from agent.content_generator import generate_content
from agent.image_prompt_logger import log_image_prompt
from agent.dalle_client import generate_image
from agent.twitter_client import post_tweet
from agent.telegram_client import send_notification_sync
from agent.scheduler import schedule_daily_posts

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("oeconomia-agent")


# ---------------------------------------------------------------------------
# Agent state helpers (Supabase)
# ---------------------------------------------------------------------------

def _read_agent_state() -> dict:
    """Read the agent_state singleton row from Supabase."""
    try:
        sb = get_supabase()
        result = sb.table("agent_state").select("*").eq("id", 1).single().execute()
        return result.data or {}
    except Exception as e:
        logger.warning("Could not read agent_state from Supabase: %s — using defaults", e)
        return {}


def _update_heartbeat(next_post_times: list[str] | None = None) -> None:
    """Update last_heartbeat (and optionally next_post_times) in agent_state."""
    try:
        sb = get_supabase()
        update_data = {
            "last_heartbeat": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        if next_post_times is not None:
            update_data["next_post_times"] = next_post_times
        sb.table("agent_state").update(update_data).eq("id", 1).execute()
    except Exception as e:
        logger.warning("Failed to update heartbeat: %s", e)


# ---------------------------------------------------------------------------
# Post log persistence (Supabase)
# ---------------------------------------------------------------------------

def _append_post_log(entry: dict) -> Optional[str]:
    """Insert a completed post entry into the Supabase twitter_posts table.

    Returns the UUID of the inserted row, or None on failure.
    """
    row = {
        "post_type": entry.get("post_type", "unknown"),
        "tweet_text": entry.get("tweet_text", ""),
        "hook": entry.get("hook"),
        "hashtags": entry.get("hashtags", []),
        "image_prompt": entry.get("image_prompt"),
        "image_style_tags": entry.get("image_style_tags", []),
        "tweet_id": entry.get("tweet_id"),
        "image_path": entry.get("image_path"),
        "image_url": entry.get("image_url"),
        "status": entry.get("status", "pending"),
        "created_at": entry.get("timestamp", datetime.now(timezone.utc).isoformat()),
        "posted_at": datetime.now(timezone.utc).isoformat() if entry.get("tweet_id") else None,
    }

    try:
        sb = get_supabase()
        result = sb.table("twitter_posts").insert(row).execute()
        post_id = result.data[0]["id"] if result.data else None
        logger.info("Post logged to Supabase (id=%s)", post_id)
        return post_id
    except Exception as e:
        logger.error("Failed to write post to Supabase: %s", e)
        return None


# ---------------------------------------------------------------------------
# Core post cycle
# ---------------------------------------------------------------------------

def run_post_cycle(post_type: str = "technical") -> bool:
    """
    Execute one full post cycle:
      1. Read agent_state for is_running/dry_run/image_mode
      2. Generate content (Claude)
      3. Log image prompt
      4. Generate image (if IMAGE_MODE == "dalle")
      5. Post tweet
      6. Send Telegram notification
      7. Append to Supabase twitter_posts

    Args:
        post_type: One of "technical", "hype", "educational", "philosophical".

    Returns:
        True if the cycle completed successfully.
    """
    # Read live agent_state from Supabase
    state = _read_agent_state()
    is_running = state.get("is_running", True)
    dry_run = state.get("dry_run", DRY_RUN)
    image_mode = state.get("image_mode", IMAGE_MODE)

    if not is_running:
        logger.info("Agent is paused via dashboard — skipping cycle")
        _update_heartbeat()
        return False

    logger.info("=" * 60)
    logger.info("Starting post cycle — type: %s, mode: %s, dry_run: %s",
                post_type, image_mode, dry_run)
    logger.info("=" * 60)

    # Update heartbeat
    _update_heartbeat()

    # 1. Generate content
    content = generate_content(post_type=post_type)
    if not content:
        logger.error("Content generation failed — aborting cycle")
        return False

    tweet_text = content["tweet_text"]
    image_prompt = content.get("image_prompt")
    actual_post_type = content.get("post_type", post_type)

    # 2. Handle image based on image_mode (from agent_state)
    image_path: Optional[Path] = None
    image_url: Optional[str] = None
    image_status = "skipped"

    if image_mode == "dalle" and image_prompt:
        # Auto-generate via DALL-E 3
        image_path, image_url = generate_image(image_prompt)
        image_status = "generated" if image_path else "policy_blocked"

    elif image_mode == "manual" and image_prompt:
        # Log the prompt for manual creation
        image_status = "manual_pending"
        logger.info("IMAGE_MODE=manual — prompt logged for manual image creation")

    elif image_mode == "none":
        image_status = "skipped"

    # 3. Post tweet
    tweet_id = post_tweet(text=tweet_text, image_path=image_path)

    if tweet_id is None:
        logger.error("Tweet posting failed — cycle incomplete")
        # Still log the attempt
        post_id = _append_post_log({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tweet_text": tweet_text,
            "post_type": actual_post_type,
            "image_prompt": image_prompt,
            "image_path": str(image_path) if image_path else None,
            "image_url": image_url,
            "tweet_id": None,
            "status": "failed",
        })

        # Log image prompt with post_id
        log_image_prompt(
            post_type=actual_post_type,
            tweet_text=tweet_text,
            image_prompt=image_prompt,
            dalle_path=image_path,
            status=image_status,
            post_id=post_id,
        )
        return False

    # 4. Send Telegram notification
    tg_text = (
        f"*New Oeconomia Tweet* ({actual_post_type})\n\n"
        f"{tweet_text}\n\n"
        f"{'[DRY RUN]' if dry_run else f'Tweet ID: {tweet_id}'}"
    )
    send_notification_sync(tg_text, image_path)

    # 5. Log to Supabase twitter_posts
    status = "posted" if tweet_id != "DRY_RUN" else "dry_run"
    post_id = _append_post_log({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tweet_text": tweet_text,
        "post_type": actual_post_type,
        "image_prompt": image_prompt,
        "image_path": str(image_path) if image_path else None,
        "image_url": image_url,
        "tweet_id": tweet_id,
        "status": status,
    })

    # 6. Log image prompt with post_id
    log_image_prompt(
        post_type=actual_post_type,
        tweet_text=tweet_text,
        image_prompt=image_prompt,
        dalle_path=image_path,
        status=image_status,
        post_id=post_id,
    )

    logger.info("Post cycle complete: %s", tweet_text[:80])
    return True


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main():
    """Start the Oeconomia Twitter Agent."""
    # Read initial state from Supabase
    state = _read_agent_state()
    dry_run = state.get("dry_run", DRY_RUN)
    image_mode = state.get("image_mode", IMAGE_MODE)

    logger.info("=" * 60)
    logger.info("  Oeconomia Twitter Agent")
    logger.info("  DRY_RUN: %s | IMAGE_MODE: %s", dry_run, image_mode)
    logger.info("=" * 60)

    if dry_run:
        logger.info("DRY RUN MODE — tweets will be logged but NOT posted to Twitter")

    # Update heartbeat on startup
    _update_heartbeat()

    # Handle graceful shutdown
    def signal_handler(sig, frame):
        logger.info("Shutdown signal received — stopping scheduler...")
        from agent.scheduler import get_scheduler
        scheduler = get_scheduler()
        if scheduler:
            scheduler.shutdown(wait=False)
        logger.info("Agent stopped.")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    # Start the scheduler
    scheduler = schedule_daily_posts(run_post_cycle)

    logger.info("Agent running. Press Ctrl+C to stop.")

    # Keep the main thread alive, update heartbeat every 60s
    try:
        while True:
            time.sleep(60)
            _update_heartbeat()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutting down...")
        scheduler.shutdown(wait=False)
        logger.info("Agent stopped.")


if __name__ == "__main__":
    main()
