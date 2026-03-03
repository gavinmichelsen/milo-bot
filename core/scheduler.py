"""
Scheduled tasks for Milo bot.

Handles recurring cron jobs like daily morning check-ins,
weekly progress summaries, and periodic data syncs from
Whoop and Withings.
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from utils.logger import setup_logger

logger = setup_logger("milo.scheduler")

scheduler = AsyncIOScheduler()


async def morning_checkin():
    """Send a daily morning check-in message to active users.

    Pulls the user's latest Whoop recovery score and Withings
    weight, then sends a personalized coaching message with
    training recommendations for the day.
    """
    logger.info("Running morning check-in job")
    # TODO: Fetch active users from Supabase
    # TODO: Pull latest Whoop recovery + Withings weight
    # TODO: Generate personalized morning message via agent
    # TODO: Send messages via Telegram bot


async def weekly_progress_summary():
    """Send a weekly progress summary to active users.

    Compiles the week's training volume, body composition trends,
    sleep averages, and recovery patterns into a single
    coaching summary.
    """
    logger.info("Running weekly progress summary job")
    # TODO: Aggregate weekly data per user
    # TODO: Generate summary via agent
    # TODO: Send messages via Telegram bot


def start_scheduler():
    """Register all scheduled jobs and start the scheduler."""
    scheduler.add_job(morning_checkin, "cron", hour=7, minute=0, id="morning_checkin")
    scheduler.add_job(weekly_progress_summary, "cron", day_of_week="sun", hour=18, minute=0, id="weekly_summary")
    scheduler.start()
    logger.info("Scheduler started with morning check-in (7:00 AM) and weekly summary (Sunday 6:00 PM)")
