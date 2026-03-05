"""
Scheduled tasks for Milo bot.

Handles recurring cron jobs like daily morning check-ins,
weekly progress summaries, and periodic Whoop token refresh.
"""

from datetime import datetime, timezone

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from coaching.progress import build_weekly_progress_summary
from coaching.recovery import evaluate_recovery
from core.database import (
    get_all_users,
    get_nutrition_state,
    get_all_whoop_tokens,
    get_onboarding_state,
    get_recent_body_metrics,
    get_recent_recovery_statuses,
    get_recent_whoop_snapshots,
    get_user_profile,
    get_workout_history,
    store_recovery_daily_status,
)
from core.user_context import build_user_context
from utils.logger import setup_logger

logger = setup_logger("milo.scheduler")

scheduler = AsyncIOScheduler()


async def morning_checkin(bot=None):
    """Send a daily morning check-in message to active users."""
    logger.info("Running morning check-in job")

    today_iso = datetime.now(timezone.utc).date().isoformat()

    try:
        users = get_all_users()
        whoop_tokens = get_all_whoop_tokens()
    except Exception as e:
        logger.error(f"Morning check-in bootstrap failed: {e}")
        return

    if not whoop_tokens:
        logger.info("No connected Whoop users for morning check-in")
        return

    users_by_telegram_id = {
        user.get("telegram_id"): user
        for user in users
        if user.get("telegram_id") is not None
    }

    sent = 0
    skipped = 0
    failed = 0

    for token_row in whoop_tokens:
        telegram_id = token_row.get("telegram_id")
        user = users_by_telegram_id.get(telegram_id, {})
        username = user.get("username") or user.get("first_name") or str(telegram_id)

        try:
            user_profile = get_user_profile(telegram_id)
            onboarding_state = get_onboarding_state(telegram_id)
            if onboarding_state and onboarding_state.get("status") != "completed":
                skipped += 1
                continue
            if user_profile and user_profile.get("onboarding_status") not in {None, "completed", "not_started"}:
                skipped += 1
                continue

            existing_statuses = get_recent_recovery_statuses(telegram_id, limit=3)
            if existing_statuses and existing_statuses[0].get("snapshot_date") == today_iso:
                skipped += 1
                continue

            user_context = await build_user_context(telegram_id=telegram_id, username=username)
            snapshots = get_recent_whoop_snapshots(telegram_id, limit=30)
            recovery_status = evaluate_recovery(snapshots, existing_statuses)
            if not recovery_status.get("snapshot_date"):
                recovery_status["snapshot_date"] = today_iso

            store_recovery_daily_status(telegram_id, recovery_status)

            if bot and recovery_status.get("should_send") and recovery_status.get("message_text"):
                message_text = recovery_status["message_text"]
                training_guidance = user_context.get("training_guidance") if user_context else None
                if training_guidance:
                    session_adjustment = str(training_guidance.get("session_adjustment", "N/A")).replace("_", " ")
                    target_rir = training_guidance.get("target_rir", "N/A")
                    training_summary = training_guidance.get("summary")
                    guidance_lines = [
                        "",
                        f"Training focus: {session_adjustment}.",
                        f"Target effort: {target_rir} RIR.",
                    ]
                    if training_summary:
                        guidance_lines.append(training_summary)
                    message_text += "\n\n" + "\n".join(guidance_lines).strip()

                await bot.send_message(chat_id=telegram_id, text=message_text)
                sent += 1
            else:
                skipped += 1
        except Exception as e:
            logger.error(f"Morning check-in failed for telegram_id={telegram_id}: {e}")
            failed += 1

    logger.info(f"Morning check-in complete: {sent} sent, {skipped} skipped, {failed} failed")


async def weekly_progress_summary(bot=None):
    """Send a weekly progress summary to active users."""
    logger.info("Running weekly progress summary job")

    try:
        users = get_all_users()
    except Exception as e:
        logger.error(f"Weekly summary bootstrap failed: {e}")
        return

    sent = 0
    skipped = 0
    failed = 0

    for user in users:
        telegram_id = user.get("telegram_id")
        if telegram_id is None:
            skipped += 1
            continue

        try:
            user_profile = get_user_profile(telegram_id)
            onboarding_state = get_onboarding_state(telegram_id)
            if onboarding_state and onboarding_state.get("status") != "completed":
                skipped += 1
                continue
            if user_profile and user_profile.get("onboarding_status") not in {None, "completed", "not_started"}:
                skipped += 1
                continue

            recovery_statuses = get_recent_recovery_statuses(telegram_id, limit=7)
            body_metrics = get_recent_body_metrics(telegram_id, limit=8)
            workouts = get_workout_history(telegram_id, limit=50)
            nutrition_state = get_nutrition_state(telegram_id)

            summary = build_weekly_progress_summary(
                recovery_statuses=recovery_statuses,
                body_metrics=body_metrics,
                workouts=workouts,
                nutrition_state=nutrition_state,
            )

            if bot and summary:
                await bot.send_message(chat_id=telegram_id, text=summary)
                sent += 1
            else:
                skipped += 1
        except Exception as e:
            logger.error(f"Weekly summary failed for telegram_id={telegram_id}: {e}")
            failed += 1

    logger.info(f"Weekly summary complete: {sent} sent, {skipped} skipped, {failed} failed")


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


async def refresh_withings_tokens_job():
    """Refresh Withings access tokens for all connected users.

    Runs every 2.5 hours. Withings tokens expire after 3 hours,
    so this keeps them fresh with a 30-minute buffer.
    """
    from core.database import get_all_withings_tokens, store_withings_tokens
    from integrations.withings import refresh_withings_token

    logger.info("Running Withings token refresh job")

    try:
        all_tokens = get_all_withings_tokens()
    except Exception as e:
        logger.error(f"Failed to fetch withings_tokens table: {e}")
        return

    if not all_tokens:
        logger.info("No Withings tokens to refresh")
        return

    refreshed = 0
    failed = 0

    for row in all_tokens:
        telegram_id = row.get("telegram_id")
        refresh_token = row.get("refresh_token")

        if not refresh_token:
            logger.warning(f"No refresh_token for Withings telegram_id={telegram_id}, skipping")
            failed += 1
            continue

        try:
            new_tokens = await refresh_withings_token(refresh_token)
            store_withings_tokens(telegram_id, new_tokens)
            refreshed += 1
        except Exception as e:
            logger.error(f"Failed to refresh Withings token for telegram_id={telegram_id}: {e}")
            failed += 1

    logger.info(f"Withings token refresh complete: {refreshed} refreshed, {failed} failed")


async def start_scheduler(app):
    """Register all scheduled jobs and start the scheduler."""
    scheduler.add_job(morning_checkin, "cron", hour=7, minute=0, args=[app.bot], id="morning_checkin")
    scheduler.add_job(weekly_progress_summary, "cron", day_of_week="sun", hour=18, minute=0, args=[app.bot], id="weekly_summary")
    scheduler.add_job(refresh_whoop_tokens_job, "interval", minutes=50, id="whoop_token_refresh", misfire_grace_time=300)
    scheduler.add_job(refresh_withings_tokens_job, "interval", minutes=60, id="withings_token_refresh", misfire_grace_time=300)
    scheduler.start()
    logger.info("Scheduler started — running initial token refresh...")

    # Refresh tokens immediately on startup so they're fresh after redeploy
    await refresh_whoop_tokens_job()
    await refresh_withings_tokens_job()

    logger.info("Startup token refresh complete")
