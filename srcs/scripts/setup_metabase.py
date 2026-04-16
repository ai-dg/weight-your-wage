import os
import time
import requests
from fastapi import HTTPException, status
import logging
from api.config import settings


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("metabase_setter")


def wait_for_metabase():
    metabase_url = settings.metabase_url
    if not metabase_url:
        msg = "Missing environment variable: METABASE_URL."
        logger.critical(msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "ConfigError",
                "message": msg
                }
        )

    while True:
        try:
            response = requests.get(f"{metabase_url}/health")
            response.raise_for_status()
            logger.info("Metabase online")
            break
        except requests.exceptions.RequestException:
            pass
        time.sleep(5)

def get_setup_token():
    metabase_url = settings.metabase_url
    if not metabase_url:
        msg = "Missing environment variable: METABASE_URL."
        logger.critical(msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "ConfigError",
                "message": msg
                }
        )
    try:
        response = requests.get(f"{metabase_url}/session/properties")
        response.raise_for_status()
        data = response.json()
        token = data.get("setup-token")
        if not token:
            logger.info("Token not found (already setup).")
            return None
        return token
    except requests.exceptions.RequestException as e:
        logger.error(f"Error while getting Metabase token {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "error": "MetabaseTokenError",
                "details": str(e)}
        )

def perform_setup(token):
    first_name = settings.metabase_admin_first_name
    last_name = settings.metabase_admin_last_name
    email = settings.metabase_admin_email
    password = settings.metabase_admin_password
    metabase_url = settings.metabase_url

    if not all([first_name, last_name, email, password, metabase_url]):
        msg = "Missing environment variables: METABASE_ADMIN_FIRST_NAME, METABASE_ADMIN_LAST_NAME, METABASE_ADMIN_EMAIL, METABASE_ADMIN_PASSWORD, METABASE_URL or METABASE_URL."
        logger.critical(msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "ConfigError",
                "message": msg
                }
        )
                
    payload = {
        "token": token,
        "user": {
            "first_name": first_name,
            "last_name": last_name,
            "email": email,
            "password": password,
            
        },
        "prefs": {
            "site_name": "Data Analytics Stack",
            "site_locale": "fr",
            "allow_tracking": False
        }
    }
    
    try:
        logger.info(f"Initializing the admin ({email})...")
        response = requests.post(f"{metabase_url}/setup", json=payload)
        response.raise_for_status()
        session_id = response.json().get("id")
        logger.info("User create sucessfully.")
        return session_id
    
    except requests.exceptions.RequestException as e:
        logger.error(f"Metabase User Creation Failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "error": "MetabaseUserCreationError",
                "details": str(e)
            }
        )

def connect_database(session_id):
    headers = {"X-Metabase-Session": session_id}
    metabase_url = settings.metabase_url


    db_payload = {
        "name": "PostgreSQL",
        "engine": "postgres",
        "details": {
            "host": settings.postgres_host,
            "port": int(settings.postgres_port),
            "db": settings.postgres_db,
            "user": settings.postgres_user,
            "password": settings.postgres_password,
            "ssl": False
        }
    }

    try:
        response = requests.post(f"{metabase_url}/database", headers=headers, json=db_payload)
        response.raise_for_status()
        logger.info("Database connected sucessfully.")
    except requests.exceptions.RequestException as e:
        logger.error(f"Metabase Database Connection Failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "error": "MetabaseDatabaseConnectionError",
                "details": str(e)
            }
        )


def run_setup_metabase():
    wait_for_metabase()
    token = get_setup_token()
    if token:
        session_id = perform_setup(token)
        if session_id:
            connect_database(session_id)


if __name__ == "__main__":
    try:
        run_setup_metabase()
    except HTTPException as e:
        print(f"Error {e.status_code}: {e.detail}")
    except Exception as e:
        print(f"Error : {str(e)}")