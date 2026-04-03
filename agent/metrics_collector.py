"""
Oeconomia Twitter Agent — Metrics Collector
Fetches tweet engagement metrics from Twitter API v2 and updates
the twitter_posts table in Supabase. Intended to run periodically (every 30 min).
"""

import logging
import time
from typing import Optional

import tweepy

from config.settings import (
    TWITTER_BEARER_TOKEN,
    get_supabase,
)

logger = logging.getLogger(__name__)


def _get_v2_client() -> Optional[tweepy.Client]:
    """Create a Tweepy v2 Client for reading tweet metrics."""
    if not TWITTER_BEARER_TOKEN:
        logger.warning("TWITTER_BEARER_TOKEN not set — cannot fetch metrics")
        return None
    return tweepy.Client(
        bearer_token=TWITTER_BEARER_TOKEN,
        wait_on_rate_limit=True,
    )


def fetch_and_update_metrics() -> int:
    """
    Fetch engagement metrics for all posted tweets and update Supabase.

    Queries twitter_posts for rows with a non-null tweet_id and status='posted',
    fetches public_metrics from the Twitter API, and updates the row.

    Returns:
        Number of tweets successfully updated.
    """
    client = _get_v2_client()
    if client is None:
        return 0

    try:
        sb = get_supabase()
        # Get all posted tweets that have a real tweet_id
        result = (
            sb.table("twitter_posts")
            .select("id, tweet_id")
            .eq("status", "posted")
            .not_.is_("tweet_id", "null")
            .execute()
        )
        posts = result.data or []
    except Exception as e:
        logger.error("Failed to fetch posts from Supabase: %s", e)
        return 0

    if not posts:
        logger.info("No posted tweets to collect metrics for")
        return 0

    updated = 0

    for post in posts:
        tweet_id = post.get("tweet_id")
        post_uuid = post.get("id")

        if not tweet_id or tweet_id == "DRY_RUN":
            continue

        try:
            response = client.get_tweet(
                id=tweet_id,
                tweet_fields=["public_metrics"],
            )

            if response.data is None:
                logger.warning("Tweet %s not found (may be deleted)", tweet_id)
                continue

            metrics = response.data.get("public_metrics", {}) if hasattr(response.data, "get") else {}
            # Tweepy v2 returns a Tweet object; access public_metrics via data attribute
            if not metrics and hasattr(response.data, "public_metrics"):
                metrics = response.data.public_metrics or {}
            if not metrics and hasattr(response.data, "data"):
                metrics = response.data.data.get("public_metrics", {})

            update_data = {
                "impressions": metrics.get("impression_count", 0),
                "likes": metrics.get("like_count", 0),
                "replies": metrics.get("reply_count", 0),
                "retweets": metrics.get("retweet_count", 0),
                "quotes": metrics.get("quote_count", 0),
            }

            sb.table("twitter_posts").update(update_data).eq("id", post_uuid).execute()
            updated += 1

            logger.debug(
                "Updated metrics for tweet %s: %s",
                tweet_id,
                update_data,
            )

        except tweepy.TooManyRequests:
            logger.warning("Rate limited while fetching metrics — stopping this cycle")
            break
        except tweepy.TweepyException as e:
            logger.error("Error fetching metrics for tweet %s: %s", tweet_id, e)
        except Exception as e:
            logger.error("Unexpected error updating metrics for tweet %s: %s", tweet_id, e)

        # Small delay between API calls to be nice to rate limits
        time.sleep(1)

    logger.info("Metrics updated for %d/%d tweets", updated, len(posts))
    return updated


def run_metrics_loop(interval_minutes: int = 30) -> None:
    """
    Run the metrics collector in a blocking loop.
    Fetches metrics every `interval_minutes`.
    """
    logger.info("Starting metrics collector (interval: %d min)", interval_minutes)

    while True:
        try:
            fetch_and_update_metrics()
        except Exception as e:
            logger.error("Metrics collection cycle failed: %s", e)

        time.sleep(interval_minutes * 60)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    run_metrics_loop()
