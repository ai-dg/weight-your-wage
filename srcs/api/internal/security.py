from fastapi import HTTPException, Security, status
from fastapi.security.api_key import APIKeyHeader
import os

GENERAL_KEY_NAME = "X-General-API-Key"
ML_KEY_NAME = "X-ML-Engineer-Key"

general_header = APIKeyHeader(name=GENERAL_KEY_NAME, auto_error=True)
ml_header = APIKeyHeader(name=ML_KEY_NAME, auto_error=False)

APP_ENV = os.getenv("APP_ENV", "dev").lower()
GENERAL_API_KEY = os.getenv("GENERAL_API_KEY", "")
ML_ENGINEER_API_KEY = os.getenv("ML_ENGINEER_API_KEY", "")

def validate_general_key(api_key: str = Security(general_header)):
    """Validate the general API key."""
    if api_key != GENERAL_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid General API KEY"
        )
    return api_key

def validate_ml_engineer(api_key: str = Security(ml_header)):
    """Validate ML engineer access in production."""
    if APP_ENV != "prod":
        return

    if not ML_ENGINEER_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ML_ENGINEER_API_KEY is not configured in production"
        )
    
    if api_key != ML_ENGINEER_API_KEY:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: ML Engineer access required"
            )
