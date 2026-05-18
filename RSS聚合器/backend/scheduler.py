import logging
import uuid
from apscheduler.schedulers.background import BackgroundScheduler
from database import SessionLocal
from services.report import run_fetch_and_summarize_task
from services.task_store import create_task

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def scheduled_fetch_job():
    """Scheduled job: fetch RSS, summarize, generate report every 6 hours."""
    task_id = str(uuid.uuid4())
    create_task(task_id, source="scheduled")
    logger.info(f"Running scheduled fetch job (task={task_id})...")
    run_fetch_and_summarize_task(SessionLocal, task_id=task_id, source="scheduled")


def start_scheduler():
    scheduler.add_job(
        scheduled_fetch_job,
        trigger="interval",
        hours=6,
        id="fetch_job",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("APScheduler started: fetch job scheduled every 6 hours")


def stop_scheduler():
    scheduler.shutdown()
    logger.info("APScheduler stopped")
