"""Simple in-memory task status store."""

from datetime import datetime

_tasks: dict = {}


def create_task(task_id: str, source: str = "manual"):
    _tasks[task_id] = {
        "task_id": task_id,
        "status": "running",
        "source": source,  # "manual" or "scheduled"
        "created_at": datetime.utcnow().isoformat(),
        "result": None,
        "error": None,
    }


def update_task(task_id: str, status: str, result: dict = None, error: str = None):
    if task_id in _tasks:
        _tasks[task_id]["status"] = status
        if result:
            _tasks[task_id]["result"] = result
        if error:
            _tasks[task_id]["error"] = error


def get_task(task_id: str) -> dict | None:
    return _tasks.get(task_id)
