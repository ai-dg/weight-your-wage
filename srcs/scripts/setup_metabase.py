from fastapi import HTTPException, status
from api.config import settings
import time
import requests
import logging


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("metabase_setter")


def wait_for_metabase():
    """
    Blocks execution and polls the Metabase health endpoint at regular intervals
    until the service is fully online and responsive.
    -----------
    Arguments:
    None
    -----------
    Return:
    None
    """
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
    """
    Retrieves the temporary 'setup-token' from Metabase session properties.
    This token is required for the initial configuration and is only
    available if the instance hasn't been set up yet.
    -----------
    Arguments:
    None
    -----------
    Return:
    str | None: The setup token string if available, or None if the instance is already configured.
    """
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
    """
    Executes the first-time setup for Metabase by creating the primary admin
    account and defining site-wide preferences such as language and site name.
    -----------
    Arguments:
    - token (str): The valid setup token obtained from the Metabase instance.
    -----------
    Return:
    str: The session ID (token) for the newly created administrator account.
    """
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
    """
    Registers the application's PostgreSQL database as a data source within
    Metabase using an authenticated admin session.
    -----------
    Arguments:
    - session_id (str): A valid Metabase session token with admin privileges.
    -----------
    Return:
    None
    """
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
    """
    Orchestrates the entire Metabase initialization workflow: waits for
    availability, fetches the setup token, creates the admin, and connects
    the PostgreSQL analytics database.
    -----------
    Arguments:
    None
    -----------
    Return:
    None
    """
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
