import uuid
import datetime
from fastapi import BackgroundTasks
import os
from fastapi import HTTPException, Request

jobs = {}

public_routes = {
    "predict",
}


APP_ENV = os.getenv("APP_ENV", "dev").lower()
ML_ENGINEER_API_KEY = os.getenv("ML_ENGINEER_API_KEY", "")


def _require_ml_engineer(request: Request):
	"""Require an admin key for ML-engineer-only endpoints in production."""
	if APP_ENV != "prod":
		return

	if not ML_ENGINEER_API_KEY:
		raise HTTPException(
			status_code=500,
			detail="ML_ENGINEER_API_KEY is not configured in production"
		)

	provided_key = request.headers.get("X-ML-Engineer-Key", "")
	if provided_key != ML_ENGINEER_API_KEY:
		raise HTTPException(status_code=403, detail="Forbidden")


def start_job(task_name: str, func, background_tasks: BackgroundTasks, request: Request, **kwargs):
    if task_name not in public_routes:
        _require_ml_engineer(request)

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