import uuid
import threading

from fastapi import APIRouter, HTTPException

from database import SessionLocal
from services.report import run_fetch_and_summarize_task
from services.task_store import create_task, get_task
from schemas import FetchResponse

router = APIRouter(prefix="/api", tags=["fetch"])


@router.post("/fetch", response_model=FetchResponse)
def trigger_fetch():
    """Manually trigger fetch and summarize task. Runs asynchronously in a background thread."""
    task_id = str(uuid.uuid4())
    create_task(task_id, source="manual")

    def background_job():
        run_fetch_and_summarize_task(SessionLocal, task_id=task_id, source="manual")

    thread = threading.Thread(target=background_job, daemon=True)
    thread.start()

    return FetchResponse(
        task_id=task_id,
        message="抓取与总结任务已开始，请稍后刷新查看日报",
    )


@router.get("/task/{task_id}")
def query_task(task_id: str):
    """Query the status of a fetch task."""
    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="任务不存在")
    return task
