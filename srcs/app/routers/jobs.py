from fastapi import APIRouter, BackgroundTasks, Request, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from json import JSONDecodeError

# Import our helpers and the background tasks themselves
from srcs.app.internal.manager import start_job, jobs
from srcs.app.internal.tasks import (
    _run_training, 
    _run_test, 
    _run_inference,
    _run_upload_minio_task,
    _run_import_minio_postgresql_task,
    _run_clean_data_task,
    _run_setup_metabase_task,
    _run_data_visualization_metabase_task
)

router = APIRouter(prefix="/jobs", tags=["Jobs"])

    @app.post("/jobs/train")
    def train(background_tasks: BackgroundTasks):
        return start_job("train", _run_training, BackgroundTasks)

    @app.post("/jobs/test/")
    @app.post("/jobs/test/{version}")
    def test(background_tasks: BackgroundTasks, version: str | None=None):
        return start_job("test", _run_test, BackgroundTasks, version=version)

    @app.post("/jobs/predict")
    async def predict(background_tasks: BackgroundTasks, request: Request):
        try:
            data = await request.json()
        except JSONDecodeError:
            return JSONResponse(
                status_code=400,
                content={
                    "error": "Bad JSOn formnatting",
                    "status_code": 400
                }
            )

        return start_job("predict", _run_inference, BackgroundTasks, data=data)

    @app.post("/jobs/upload_minio")
    def upload_minio(background_tasks: BackgroundTasks):
        return (start_job("minio", _run_upload_minio_task, background_tasks))

    @app.post("/jobs/import_postgresql")
    def import_postgresql(background_tasks: BackgroundTasks):
        return (start_job("import postgresql", _run_import_minio_postgresql_task, background_tasks))

    @app.post("/jobs/clean_data")
    def clean_data(background_tasks: BackgroundTasks):
        return (start_job("clean data", _run_clean_data_task, background_tasks))

    @app.post("/jobs/setup_metabase")
    def setup_metabase(background_tasks: BackgroundTasks):
        return (start_job("setup metabase", _run_setup_metabase_task, background_tasks))

    @app.post("/jobs/data_visualization")
    def data_visualization(background_tasks: BackgroundTasks):
        return (start_job("data visualization", _run_data_visualization_metabase_task, background_tasks))

    @app.get("/jobs/{job_id}")
    def get_job(job_id: str):
        if not job_id in jobs:
            return JSONResponse(
                status_code=404,
                content={
                    "error": "Job not found",
                    "job_id": job_id,
                    "status_code": 404
                }
            )
        return jobs[job_id]

