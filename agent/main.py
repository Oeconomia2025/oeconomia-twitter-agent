"""
Oeconomia Twitter Agent — Main Entry Point
Wires together: content generation -> image prompt logging -> DALL-E image ->
Twitter posting -> Telegram notification -> post log.
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
    POST_LOG_PATH,
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
# Post log persistence
# ---------------------------------------------------------------------------

def _append_post_log(entry: dict) -> None:
    """Append a completed post entry to post_log.json."""
    log = []
    if POST_LOG_PATH.exists():
        try:
            with open(POST_LOG_PATH, "r", encoding="utf-8") as f:
                log = json.load(f)
        except (json.JSONDecodeError, IOError):
            log = []

    log.append(entry)

    POST_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(POST_LOG_PATH, "w", encoding="utf-8") as f:
        json.dump(log, f, indent=2, ensure_ascii=False)

    logger.info("Post logged (#%d total)", len(log))


# ---------------------------------------------------------------------------
# Core post cycle
# ---------------------------------------------------------------------------

def run_post_cycle(post_type: str = "technical") -> bool:
    """
    Execute one full post cycle:
      1. Generate content (Claude)
      2. Log image prompt
      3. Generate image (if IMAGE_MODE == "dalle")
      4. Post tweet
      5. Send Telegram notification
      6. Append to post_log.json

    Args:
        post_type: One of "technical", "hype", "educational", "philosophical".

    Returns:
        True if the cycle completed successfully.
    """
    logger.info("=" * 60)
    logger.info("Starting post cycle — type: %s, mode: %s, dry_run: %s",
                post_type, IMAGE_MODE, DRY_RUN)
    logger.info("=" * 60)

    # 1. Generate content
    content = generate_content(post_type=post_type)
    if not content:
        logger.error("Content generation failed — aborting cycle")
        return False

    tweet_text = content["tweet_text"]
    image_prompt = content.get("image_prompt")
    actual_post_type = content.get("post_type", post_type)

    # 2. Handle image based on IMAGE_MODE
    image_path: Optional[Path] = None
    image_status = "skipped"

    if IMAGE_MODE == "dalle" and image_prompt:
        # Auto-generate via DALL-E 3
        image_path = generate_image(image_prompt)
        image_status = "generated" if image_path else "policy_blocked"

    elif IMAGE_MODE == "manual" and image_prompt:
        # Log the prompt for manual creation
        image_status = "manual_pending"
        logger.info("IMAGE_MODE=manual — prompt logged for manual image creation")

    elif IMAGE_MODE == "none":
        image_status = "skipped"

    # 3. Log image prompt (always, regardless of mode)
    log_image_prompt(
        post_type=actual_post_type,
        tweet_text=tweet_text,
        image_prompt=image_prompt,
        dalle_path=image_path,
        status=image_status,
    )

    # 4. Post tweet
    tweet_id = post_tweet(text=tweet_text, image_path=image_path)
    if tweet_id is None:
        logger.error("Tweet posting failed — cycle incomplete")
        # Still log the attempt
        _append_post_log({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "tweet_text": tweet_text,
            "post_type": actual_post_type,
            "image_prompt": image_prompt,
            "image_path": str(image_path) if image_path else None,
            "tweet_id": None,
            "status": "failed",
            "dry_run": DRY_RUN,
        })
        return False

    # 5. Send Telegram notification
    tg_text = (
        f"*New Oeconomia Tweet* ({actual_post_type})\n\n"
        f"{tweet_text}\n\n"
        f"{'[DRY RUN]' if DRY_RUN else f'Tweet ID: {tweet_id}'}"
    )
    send_notification_sync(tg_text, image_path)

    # 6. Log to post_log.json
    _append_post_log({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "tweet_text": tweet_text,
        "post_type": actual_post_type,
        "image_prompt": image_prompt,
        "image_path": str(image_path) if image_path else None,
        "tweet_id": tweet_id,
        "status": "posted" if tweet_id != "DRY_RUN" else "dry_run",
        "dry_run": DRY_RUN,
    })

    logger.info("Post cycle complete: %s", tweet_text[:80])
    return True


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main():
    """Start the Oeconomia Twitter Agent."""
    logger.info("=" * 60)
    logger.info("  Oeconomia Twitter Agent")
    logger.info("  DRY_RUN: %s | IMAGE_MODE: %s", DRY_RUN, IMAGE_MODE)
    logger.info("=" * 60)

    if DRY_RUN:
        logger.info("DRY RUN MODE — tweets will be logged but NOT posted to Twitter")

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

    # Keep the main thread alive
    try:
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutting down...")
        scheduler.shutdown(wait=False)
        logger.info("Agent stopped.")


if __name__ == "__main__":
    main()
