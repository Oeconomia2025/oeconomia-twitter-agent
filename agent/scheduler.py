"""
Oeconomia Twitter Agent — Scheduler
Uses APScheduler BackgroundScheduler to post tweets at random times
between 8 AM and 10 PM, alternating between technical and hype post types.
Writes next_post_times to Supabase agent_state for the dashboard.
"""

import logging
import random
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
import pytz

from config.settings import (
    POST_FREQUENCY_MIN,
    POST_FREQUENCY_MAX,
    TIMEZONE,
    get_supabase,
)

logger = logging.getLogger(__name__)

# Post types to alternate between
POST_TYPES = ["technical", "hype", "educational", "philosophical"]

# Global scheduler instance
_scheduler: BackgroundScheduler | None = None


def _get_random_times(
    n: int,
    tz_name: str = TIMEZONE,
    start_hour: int = 8,
    end_hour: int = 22,
) -> list[datetime]:
    """
    Generate N random datetime objects for today between start_hour and end_hour.
    If some times have already passed, schedule them for tomorrow.
    """
    tz = pytz.timezone(tz_name)
    now = datetime.now(tz)

    times = []
    for _ in range(n):
        # Pick a random hour and minute
        hour = random.randint(start_hour, end_hour - 1)
        minute = random.randint(0, 59)

        candidate = now.replace(hour=hour, minute=minute, second=0, microsecond=0)

        # If the time already passed today, schedule for tomorrow
        if candidate <= now:
            candidate += timedelta(days=1)

        times.append(candidate)

    # Sort chronologically
    times.sort()
    return times


def _write_next_post_times(times: list[datetime], post_types: list[str]) -> None:
    """Write the next scheduled post times to Supabase agent_state."""
    try:
        sb = get_supabase()
        next_times = [
            {
                "time": t.isoformat(),
                "post_type": pt,
            }
            for t, pt in zip(times, post_types)
        ]
        sb.table("agent_state").update({
            "next_post_times": next_times,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }).eq("id", 1).execute()
        logger.info("Wrote %d next_post_times to Supabase", len(next_times))
    except Exception as e:
        logger.warning("Failed to write next_post_times to Supabase: %s", e)


def schedule_daily_posts(run_post_fn) -> BackgroundScheduler:
    """
    Create and start a scheduler that fires run_post_fn at random times today.
    Alternates post types across the scheduled times.

    Args:
        run_post_fn: Callable that accepts a post_type string argument.

    Returns:
        The running BackgroundScheduler instance.
    """
    global _scheduler

    # Determine how many posts for this cycle
    n_posts = random.randint(POST_FREQUENCY_MIN, POST_FREQUENCY_MAX)
    times = _get_random_times(n_posts)

    logger.info(
        "Scheduling %d posts for today (TZ: %s):",
        n_posts, TIMEZONE,
    )

    if _scheduler is not None:
        try:
            _scheduler.shutdown(wait=False)
        except Exception:
            pass

    _scheduler = BackgroundScheduler(timezone=TIMEZONE)

    # Build list of post types for each scheduled time
    scheduled_post_types = []

    for i, scheduled_time in enumerate(times):
        # Alternate post types
        post_type = POST_TYPES[i % len(POST_TYPES)]
        scheduled_post_types.append(post_type)

        _scheduler.add_job(
            run_post_fn,
            trigger=DateTrigger(run_date=scheduled_time),
            args=[post_type],
            id=f"post_{i}_{scheduled_time.strftime('%H%M')}",
            name=f"{post_type} post at {scheduled_time.strftime('%I:%M %p')}",
            misfire_grace_time=300,  # 5 min grace period
        )

        logger.info(
            "  [%d] %s — %s",
            i + 1,
            scheduled_time.strftime("%I:%M %p %Z"),
            post_type,
        )

    # Write next_post_times to Supabase for the dashboard
    _write_next_post_times(times, scheduled_post_types)

    # Schedule the next day's planning at midnight + 1 min
    tz = pytz.timezone(TIMEZONE)
    now = datetime.now(tz)
    tomorrow_midnight = (now + timedelta(days=1)).replace(
        hour=0, minute=1, second=0, microsecond=0
    )

    _scheduler.add_job(
        lambda: schedule_daily_posts(run_post_fn),
        trigger=DateTrigger(run_date=tomorrow_midnight),
        id="daily_replanner",
        name="Re-plan tomorrow's posts",
        misfire_grace_time=3600,
    )

    _scheduler.start()
    logger.info("Scheduler started. Next re-plan at %s", tomorrow_midnight.strftime("%I:%M %p %Z"))
    return _scheduler


def get_scheduler() -> BackgroundScheduler | None:
    """Return the current scheduler instance."""
    return _scheduler
