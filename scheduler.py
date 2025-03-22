import asyncio
from datetime import datetime

from apscheduler.jobstores.base import JobLookupError
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger

import db
from logger import logging
from send_notification import check_games_today, create_message, send

job_stores = {"SammyScheduler": MemoryJobStore()}

scheduler = BackgroundScheduler(jobstores=job_stores)


def run_job():
    asyncio.run(execute_cron_job())


async def execute_cron_job():
    generated_data = check_games_today(db.get_all_db_entries())
    detected_games_today = list(generated_data)

    if not detected_games_today:
        logging.info("No games today!")
        return

    message = create_message(detected_games_today)
    await send(message)
    logging.info("Cron job completed successfully")


def scheduler_update(job_id, new_sched_time):
    try:
        scheduler.reschedule_job(
            job_id,
            trigger=DateTrigger(run_date=new_sched_time, timezone="Asia/Jerusalem"),
        )
        logging.info(f"Job {job_id} rescheduled to {new_sched_time}")

    except JobLookupError as err:
        logging.error(f"Failed to reschedule job {job_id}: {str(err)}")
        scheduler_add(db.get_game_details(job_id))

    return True


def scheduler_delete(job_id):
    try:
        scheduler.remove_job(job_id)
    except Exception as err:
        # sometimes jobs are expired on their own so just log it
        logging.error(f"Failed to remove job {job_id}: {str(err)}")


def scheduler_add(game):
    try:
        job_id = game.get("game_id")
        scheduler_date = datetime.fromisoformat(game["scraped_date_time"]).date()
        scheduler_time_str = game.get("sched_time") or "09:00"
        scheduler_time = datetime.strptime(scheduler_time_str, "%H:%M").time()
        scheduler_dt = datetime.combine(scheduler_date, scheduler_time)

        scheduler.add_job(
            run_job,
            id=job_id,
            trigger=DateTrigger(run_date=scheduler_dt, timezone="Asia/Jerusalem"),
            name=f"{job_id} ({scheduler_dt})",
            replace_existing=True,
            jobstore="SammyScheduler",
        )
        return True

    except Exception as err:
        # sometimes jobs are expired on their own so just log it
        logging.error(f"Failed to add job {job_id}: {str(err)}")
        return False


def scheduler_onstart():
    if scheduler.running:
        logging.info("Scheduler already running, skipping...")
        return

    upcoming, _ = db.get_all_db_entries()

    for game in upcoming:
        job_id = game.get("game_id")
        scheduler_date = datetime.fromisoformat(game["scraped_date_time"]).date()
        scheduler_time_str = game.get("sched_time") or "09:00"
        scheduler_time = datetime.strptime(scheduler_time_str, "%H:%M").time()
        scheduler_dt = datetime.combine(scheduler_date, scheduler_time)

        scheduler.add_job(
            run_job,
            id=job_id,
            trigger=DateTrigger(run_date=scheduler_dt, timezone="Asia/Jerusalem"),
            name=f"{job_id} ({scheduler_dt})",
            replace_existing=True,
            jobstore="SammyScheduler",
        )

    scheduler.start()
