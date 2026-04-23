from fastapi import APIRouter, BackgroundTasks, Request, Depends
from fastapi.responses import JSONResponse, HTMLResponse
from json import JSONDecodeError
from srcs.api.internal.security import validate_general_key, validate_ml_engineer

# Import our helpers and the background tasks themselves
from srcs.api.internal.manager import start_job, jobs
from srcs.api.internal.tasks import (
    _run_training, 
    _run_test, 
    _run_inference,
    _run_upload_minio_task,
    _run_import_minio_postgresql_task,
    _run_clean_data_task,
    _run_setup_metabase_task,
    _run_data_visualization_metabase_task
)

router = APIRouter(
    prefix="/jobs",
    tags=["Jobs"],
    dependencies=[Depends(validate_general_key)]
)

@router.get("/eda")
def eda(_ = Depends(validate_ml_engineer)):
    from srcs.model.data_preprocessor import SalaryDataModule
    data_module = SalaryDataModule(data="./srcs/model/datasets/survey_results_public.csv")
    data_module.setup("EDA")

    with open("./srcs/model/EDA.html") as f:
            html_content= f.read()
    return HTMLResponse(
        content=html_content,
        status_code=200
    )

@router.post("/train")
def train(
    background_tasks: BackgroundTasks,
    _ = Depends(validate_ml_engineer)
):
    return start_job("train", _run_training, background_tasks)

@router.post("/test/")
@router.post("/test/{version}")
def test(
    background_tasks: BackgroundTasks,
    version: str | None = None,
    _ = Depends(validate_ml_engineer)
):
    return start_job("test", _run_test, background_tasks, version=version)

@router.post("/predict")
async def predict(background_tasks: BackgroundTasks, request: Request):
    try:
        data = await request.json()
    except JSONDecodeError:
        return JSONResponse(
            status_code=400,
            content={
                "error": "Bad JSON formnatting",
                "status_code": 400
            }
        )
    return start_job("predict", _run_inference, background_tasks, data=data)

@router.post("/upload_minio")
def upload_minio(
    background_tasks: BackgroundTasks,
    _ = Depends(validate_ml_engineer)
):
    return (start_job("minio", _run_upload_minio_task, background_tasks))

@router.post("/import_postgresql")
def import_postgresql(
    background_tasks: BackgroundTasks,
    _ = Depends(validate_ml_engineer)
):
    return (start_job("import postgresql", _run_import_minio_postgresql_task, background_tasks))

@router.post("/clean_data")
def clean_data(
    background_tasks: BackgroundTasks,
    _ = Depends(validate_ml_engineer)
):
    return (start_job("clean data", _run_clean_data_task, background_tasks))

@router.post("/setup_metabase")
def setup_metabase(
    background_tasks: BackgroundTasks,
    _ = Depends(validate_ml_engineer)
):
    return (start_job("setup metabase", _run_setup_metabase_task, background_tasks))

@router.post("/data_visualization")
def data_visualization(
    background_tasks: BackgroundTasks,
    _ = Depends(validate_ml_engineer)
):
    return (start_job("data visualization", _run_data_visualization_metabase_task, background_tasks))

@router.get("/{job_id}")
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

