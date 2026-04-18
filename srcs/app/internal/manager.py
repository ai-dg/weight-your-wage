import uuid
import datetime
from fastapi import BackgroundTasks

jobs = {}

def start_job(task_name: str, func, background_tasks: BackgroundTasks, **kwargs):
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "task": task_name,
        "status": "pending",
        "created_at": str(datetime.datetime.now())
    }
    background_tasks.add_task(func, job_id=job_id, **kwargs)
    return {
        "status": f"{task_name} started",
        "job_id": job_id,
        "message": f"{task_name.capitalize()} is running in the background."
    }