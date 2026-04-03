"""
Oeconomia Twitter Agent — Twitter Client
Posts tweets via Tweepy: v2 Client for text, v1.1 API for media upload.
Supports DRY_RUN mode and exponential backoff (3 retries).
"""

import logging
import time
from pathlib import Path
from typing import Optional

import tweepy

from config.settings import (
    TWITTER_API_KEY,
    TWITTER_API_SECRET,
    TWITTER_ACCESS_TOKEN,
    TWITTER_ACCESS_TOKEN_SECRET,
    TWITTER_BEARER_TOKEN,
    DRY_RUN,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Client initialization
# ---------------------------------------------------------------------------

def _get_v2_client() -> tweepy.Client:
    """Create a Tweepy v2 Client for posting tweets."""
    return tweepy.Client(
        bearer_token=TWITTER_BEARER_TOKEN,
        consumer_key=TWITTER_API_KEY,
        consumer_secret=TWITTER_API_SECRET,
        access_token=TWITTER_ACCESS_TOKEN,
        access_token_secret=TWITTER_ACCESS_TOKEN_SECRET,
        wait_on_rate_limit=True,
    )


def _get_v1_api() -> tweepy.API:
    """Create a Tweepy v1.1 API for media uploads."""
    auth = tweepy.OAuth1UserHandler(
        consumer_key=TWITTER_API_KEY,
        consumer_secret=TWITTER_API_SECRET,
        access_token=TWITTER_ACCESS_TOKEN,
        access_token_secret=TWITTER_ACCESS_TOKEN_SECRET,
    )
    return tweepy.API(auth, wait_on_rate_limit=True)


# ---------------------------------------------------------------------------
# Media upload (v1.1)
# ---------------------------------------------------------------------------

def _upload_media(image_path: Path) -> Optional[str]:
    """
    Upload an image via Twitter v1.1 media upload endpoint.

    Returns:
        The media_id string, or None on failure.
    """
    if not image_path or not image_path.exists():
        logger.warning("Image path invalid or missing: %s", image_path)
        return None

    try:
        api = _get_v1_api()
        media = api.media_upload(filename=str(image_path))
        logger.info("Media uploaded: media_id=%s", media.media_id_string)
        return media.media_id_string
    except tweepy.TweepyException as e:
        logger.error("Media upload failed: %s", e)
        return None


# ---------------------------------------------------------------------------
# Post tweet (v2 with exponential backoff)
# ---------------------------------------------------------------------------

def post_tweet(
    text: str,
    image_path: Optional[Path] = None,
    max_retries: int = 3,
) -> Optional[str]:
    """
    Post a tweet. Uses DRY_RUN mode if enabled.

    Args:
        text: Tweet text (max 280 characters).
        image_path: Optional path to an image to attach.
        max_retries: Number of retries with exponential backoff.

    Returns:
        Tweet ID string on success, "DRY_RUN" in dry run mode, or None on failure.
    """
    if DRY_RUN:
        logger.info("[DRY RUN] Would post tweet: %s", text)
        if image_path:
            logger.info("[DRY RUN] Would attach image: %s", image_path)
        return "DRY_RUN"

    # Validate credentials are present
    if not all([TWITTER_API_KEY, TWITTER_API_SECRET,
                TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_TOKEN_SECRET]):
        logger.error("Twitter credentials not fully configured — cannot post")
        return None

    # Upload media first if provided
    media_ids = None
    if image_path:
        media_id = _upload_media(image_path)
        if media_id:
            media_ids = [media_id]
        else:
            logger.warning("Media upload failed — posting text-only")

    # Post with exponential backoff
    client = _get_v2_client()
    backoff = 1  # seconds

    for attempt in range(1, max_retries + 1):
        try:
            response = client.create_tweet(
                text=text,
                media_ids=media_ids,
            )
            tweet_id = response.data.get("id", "unknown")
            logger.info("Tweet posted: id=%s", tweet_id)
            return str(tweet_id)

        except tweepy.TooManyRequests:
            wait_time = backoff * (2 ** (attempt - 1))
            logger.warning(
                "Rate limited (attempt %d/%d) — waiting %ds",
                attempt, max_retries, wait_time,
            )
            time.sleep(wait_time)

        except tweepy.TweepyException as e:
            wait_time = backoff * (2 ** (attempt - 1))
            logger.error(
                "Tweet failed (attempt %d/%d): %s — waiting %ds",
                attempt, max_retries, e, wait_time,
            )
            time.sleep(wait_time)

    logger.error("Failed to post tweet after %d attempts", max_retries)
    return None


def post_thread(
    tweets: list[str],
    image_path: Optional[Path] = None,
) -> list[Optional[str]]:
    """
    Post a thread (list of tweets). First tweet gets the image if provided.

    Returns:
        List of tweet IDs (or None for failed tweets).
    """
    if not tweets:
        return []

    results = []
    reply_to_id = None

    for i, tweet_text in enumerate(tweets):
        if DRY_RUN:
            logger.info("[DRY RUN] Thread %d/%d: %s", i + 1, len(tweets), tweet_text)
            results.append("DRY_RUN")
            continue

        client = _get_v2_client()

        # Only attach image to first tweet
        media_ids = None
        if i == 0 and image_path:
            media_id = _upload_media(image_path)
            if media_id:
                media_ids = [media_id]

        try:
            kwargs = {"text": tweet_text}
            if media_ids:
                kwargs["media_ids"] = media_ids
            if reply_to_id:
                kwargs["in_reply_to_tweet_id"] = reply_to_id

            response = client.create_tweet(**kwargs)
            tweet_id = response.data.get("id", "unknown")
            reply_to_id = tweet_id
            results.append(str(tweet_id))
            logger.info("Thread %d/%d posted: id=%s", i + 1, len(tweets), tweet_id)

        except tweepy.TweepyException as e:
            logger.error("Thread %d/%d failed: %s", i + 1, len(tweets), e)
            results.append(None)

    return results
