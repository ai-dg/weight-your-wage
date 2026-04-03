from minio import Minio
from minio.error import S3Error
from dotenv import load_dotenv
from pathlib import Path
from typing import List, Tuple
from fastapi import HTTPException, status
import traceback
import os
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("minio_uploader")

def get_minio_client() -> Minio:
    load_dotenv()
    endpoint = os.getenv("MINIO_ENDPOINT")
    access_key=os.getenv("MINIO_ROOT_USER")
    secret_key=os.getenv("MINIO_ROOT_PASSWORD")

    if not all([endpoint, access_key, secret_key]):
        msg = "Missing environment variables: MINIO_ENDPOINT, MINIO_ROOT_USER, or MINIO_ROOT_PASSWORD."
        logger.critical(msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "ConfigError",
                "message": msg
                }
        )
    try:
        client = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=False)
        return client
    except Exception as e:
        logger.error(f"Failed to initialize MinIO client: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": type(e).__name__,
                "message": str(e),
                "context": "MinIO Client Initialization"
            }
        )

def run_csv_import_minio():
    client = get_minio_client()
    bucket_name = "raw-data"
    BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
    
    uploads: List[Tuple[Path, str]] = [
        (BASE_DIR / "srcs/model/datasets/survey_results_public.csv", "stack_overflow_2025.csv"),
        (BASE_DIR / "srcs/model/datasets/currency_2025.csv", "exchange_rate_2025.csv")
    ]

    try:
        if not client.bucket_exists(bucket_name):
            client.make_bucket(bucket_name)
            logger.info(f"Bucket ‘{bucket_name}’ created successfully.")
    except S3Error as e:
        logger.error(f"S3Error while verifying/creating the bucket: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "S3Error",
                "s3_code": e.code,
                "message": e.message,
                "bucket": bucket_name
                }
            )

    for src, dest in uploads:
        if not src.exists():
            logger.warning(f"Source file not found: {src}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "FileNotFound",
                    "path": str(src),
                    "message": "The source file does not exist on the server."
                    }
                )
        
        try:
            client.fput_object(bucket_name, dest, str(src))
            logger.info(f"Upload successful: {src.name} -> {dest}")
        except S3Error as e:
            logger.error(f"S3Error while uploading {src.name} : {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "S3UploadError",
                    "file": src.name,
                    "s3_code": e.code,
                    "message": e.message
                    }
                )
        except Exception as e:
            logger.error(f"Unexpected error while uploading {src.name}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": type(e).__name__,
                    "message": str(e),
                    "traceback": traceback.format_exc().splitlines()[-3:]
                    }
                )

    return {"status": "success", "imported_files": [u[1] for u in uploads]}

if __name__ == "__main__":
    try:
        print(run_csv_import_minio())
    except HTTPException as e:
        print(f"API Error [{e.status_code}]: {e.detail}")
