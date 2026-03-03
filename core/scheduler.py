"""
Scheduled tasks for Milo bot.

Handles recurring cron jobs like daily morning check-ins,
weekly progress summaries, and periodic Whoop token refresh.
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from utils.logger import setup_logger

logger = setup_logger("milo.scheduler")

scheduler = AsyncIOScheduler()


async def morning_checkin():
    """Send a daily morning check-in message to active users."""
    logger.info("Running morning check-in job")
    # TODO: Fetch active users from Supabase
    # TODO: Pull latest Whoop recovery + Withings weight
    # TODO: Generate personalized morning message via agent
    # TODO: Send messages via Telegram bot


async def weekly_progress_summary():
    """Send a weekly progress summary to active users."""
    logger.info("Running weekly progress summary job")
    # TODO: Aggregate weekly data per user
    # TODO: Generate summary via agent
    # TODO: Send messages via Telegram bot


async def refresh_whoop_tokens_job():
    """Refresh Whoop access tokens for all connected users.

    Runs every 50 minutes. Whoop tokens expire after 60 minutes,
    so this keeps them fresh with a 10-minute buffer.
    """
    from core.database import get_all_whoop_tokens, store_whoop_tokens
    from integrations.whoop import refresh_whoop_token

    logger.info("Running Whoop token refresh job")

    try:
        all_tokens = get_all_whoop_tokens()
    except Exception as e:
        logger.error(f"Failed to fetch whoop_tokens table: {e}")
        return

    if not all_tokens:
        logger.info("No Whoop tokens to refresh")
        return

    refreshed = 0
    failed = 0

    for row in all_tokens:
        telegram_id = row.get("telegram_id")
        refresh_token = row.get("refresh_token")

        if not refresh_token:
            logger.warning(f"No refresh_token for telegram_id={telegram_id}, skipping")
            failed += 1
            continue

        try:
            new_tokens = await refresh_whoop_token(refresh_token)
            store_whoop_tokens(telegram_id, new_tokens)
            refreshed += 1
        except Exception as e:
            logger.error(f"Failed to refresh token for telegram_id={telegram_id}: {e}")
            failed += 1

    logger.info(f"Whoop token refresh complete: {refreshed} refreshed, {failed} failed")


async def start_scheduler(app):
    """Register all scheduled jobs and start the scheduler."""
    scheduler.add_job(morning_checkin, "cron", hour=7, minute=0, id="morning_checkin")
    scheduler.add_job(weekly_progress_summary, "cron", day_of_week="sun", hour=18, minute=0, id="weekly_summary")
    scheduler.add_job(refresh_whoop_tokens_job, "interval", minutes=50, id="whoop_token_refresh")
    scheduler.start()
    logger.info("Scheduler started with morning check-in (7:00 AM), weekly summary (Sunday 6:00 PM), and Whoop token refresh (every 50 min)")
