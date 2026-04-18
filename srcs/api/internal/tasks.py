from functools import wraps
from loguru import logger
from fastapi import HTTPException
from srcs.api.internal.manager import jobs # Crucial: import the shared dict

def job_handler(task_name: str):
    def decorator(func):
        @wraps(func)
        def wrapper(job_id: str, *args, **kwargs):
            logger.info(f"[{task_name}] Starting ...")
            try:
                result = func(job_id, *args, **kwargs)
                jobs[job_id]["status"] = "done"
                if result is not None:
                    jobs[job_id].update(result)
                logger.info(f"[{task_name}] Completed.")
            except HTTPException as e:
                jobs[job_id]["status"] = "failed"
                jobs[job_id]["error"] = e.detail
                logger.error(f"Job {job_id} failed with HTTP error: {e.detail}")
            except Exception as e:
                jobs[job_id]["status"] = "failed"
                logger.error(f"[{task_name}] Error : {e}")
        return wrapper
    return decorator

@job_handler("test")
def _run_test(job_id: str, version:str | None):
    from srcs.model.test import GeneralTester
    GeneralTester(version=version)

@job_handler("train")
def _run_training(job_id: str):
    from srcs.model.train import GeneralTrainer
    GeneralTrainer()

@job_handler("inference")
def _run_inference(job_id: str, data: dict | None):
    from srcs.model.predict import GeneralInferencer
    return {"Salary" : GeneralInferencer(data)}

@job_handler("upload minio")
def _run_upload_minio_task(job_id: str):
    from srcs.scripts.minio_file_uploader import run_csv_import_minio
    run_csv_import_minio()

@job_handler("import minio postgresql")
def _run_import_minio_postgresql_task(job_id: str):
    from srcs.scripts.main_import import run_minio_import_postgresql
    run_minio_import_postgresql()

@job_handler("clean data")
def _run_clean_data_task(job_id: str):
    from srcs.scripts.clean_data import run_clean_data
    run_clean_data()

@job_handler("setup metabase")
def _run_setup_metabase_task(job_id: str):
    from srcs.scripts.setup_metabase import run_setup_metabase
    run_setup_metabase()

@job_handler("data visualization metabase")
def _run_data_visualization_metabase_task(job_id: str):
    from srcs.scripts.data_visualization_metabase import run_data_visualization_metabase
    run_data_visualization_metabase()
