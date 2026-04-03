"""
Oeconomia Twitter Agent — Telegram Client
Sends notifications to a Telegram channel/chat.
Fully wired stub: skips gracefully if TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID are not set.
"""

import logging
from pathlib import Path
from typing import Optional

from config.settings import TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID

logger = logging.getLogger(__name__)

# Only import telegram if credentials are configured
_telegram_available = False
_bot = None

if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
    try:
        import telegram
        _telegram_available = True
    except ImportError:
        logger.warning(
            "python-telegram-bot not installed — Telegram notifications disabled"
        )


async def _get_bot():
    """Lazy-init the Telegram bot instance."""
    global _bot
    if _bot is None and _telegram_available:
        import telegram
        _bot = telegram.Bot(token=TELEGRAM_BOT_TOKEN)
    return _bot


async def send_notification(
    text: str,
    image_path: Optional[Path] = None,
) -> bool:
    """
    Send a notification to the configured Telegram chat.

    Args:
        text: Message text (supports Markdown).
        image_path: Optional image to send as a photo.

    Returns:
        True if sent successfully, False otherwise.
    """
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        logger.debug("Telegram not configured — skipping notification")
        return False

    if not _telegram_available:
        logger.debug("Telegram library not available — skipping notification")
        return False

    try:
        bot = await _get_bot()
        if bot is None:
            return False

        if image_path and image_path.exists():
            with open(image_path, "rb") as photo:
                await bot.send_photo(
                    chat_id=TELEGRAM_CHAT_ID,
                    photo=photo,
                    caption=text[:1024],  # Telegram caption limit
                    parse_mode="Markdown",
                )
        else:
            await bot.send_message(
                chat_id=TELEGRAM_CHAT_ID,
                text=text,
                parse_mode="Markdown",
            )

        logger.info("Telegram notification sent")
        return True

    except Exception as e:
        logger.error("Telegram notification failed: %s", e)
        return False


def send_notification_sync(
    text: str,
    image_path: Optional[Path] = None,
) -> bool:
    """
    Synchronous wrapper for send_notification.
    Use this from non-async contexts (e.g., the scheduler).
    """
    import asyncio

    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If we're already in an async context, create a task
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(
                    asyncio.run, send_notification(text, image_path)
                )
                return future.result(timeout=30)
        else:
            return loop.run_until_complete(send_notification(text, image_path))
    except RuntimeError:
        return asyncio.run(send_notification(text, image_path))
