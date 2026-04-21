from fastapi import HTTPException, status
from api.config import settings
import os
import requests
import traceback
import logging


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("metabase_creater")


def get_metabase_client():
    """
    Retrieves admin credentials from the configuration settings and initializes the 
    Metabase session by obtaining a valid session token and endpoint URL.
    -----------
    Arguments:
    None
    -----------
    Return:
    tuple: A pair containing the session_id (str) and the metabase_url (str).
    """
    username = settings.metabase_admin_email
    password = settings.metabase_admin_password
    metabase_url = settings.metabase_url

    if not all([username, password, metabase_url]):
        msg = "Missing environment variables: METABASE_ADMIN_EMAIL, METABASE_ADMIN_PASSWORD, or METABASE_URL."
        logger.critical(msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "ConfigError",
                "message": msg
                }
        )

    try:
        session_id = get_session_token(username, password, metabase_url)
        return session_id, metabase_url
    except Exception as e:
        logger.error(f"Failed to initialize Metabase client: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": type(e).__name__,
                "message": str(e),
                "context": "Metabase Client Initialization"
            }
        )


def get_session_token(username, password, metabase_url):
    """
    Authenticates against the Metabase /session endpoint using admin credentials 
    to retrieve a session identifier required for all subsequent API requests.
    -----------
    Arguments:
    - username (str): Admin email for Metabase.
    - password (str): Admin password for Metabase.
    - metabase_url (str): The base URL of the Metabase instance.
    -----------
    Return:
    str: The unique session ID (token).
    """
    payload = {"username": username, "password": password}
    try:
        response = requests.post(f"{metabase_url}/session", json=payload)
        response.raise_for_status()
        return response.json()["id"]
    except requests.exceptions.RequestException as e:
        logger.error(f"Metabase Auth Failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "error": "MetabaseAuthError",
                "message": "Unable to connect to Metabase or incorrect credentials.",
                "details": str(e)
            }
        )


def get_database_id(headers, metabase_url, db_name="PostgreSQL"):
    """
    Queries the Metabase instance to find the internal unique identifier (ID)
    of a connected database, identified by its display name.
    -----------
    Arguments:
    - headers (dict): HTTP headers including the session token.
    - metabase_url (str): The base URL of the Metabase instance.
    - db_name (str): The name of the database as registered in Metabase.
    -----------
    Return:
    int: The internal ID of the requested database.
    """
    try:
        response = requests.get(f"{metabase_url}/database", headers=headers)
        response.raise_for_status()
        databases = response.json()

        db_list = databases['data'] if isinstance(databases, dict) and 'data' in databases else databases

        for db in db_list:
            if db['name'] == db_name:
                return db['id']

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "MetabaseDbNotFound",
                "message": f"Base '{db_name}' not found in Metabase."
            }
        )
    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "error": "MetabaseCommunicationError",
                "step": "get_database_id",
                "details": str(e)
            }
        )


def delete_old_cards(headers, metabase_url, visualizations):
    """
    Scans the existing Metabase collection and archives any questions (cards)
    that share names with the visualizations currently being deployed to
    prevent duplication and conflicts.
    -----------
    Arguments:
    - headers (dict): HTTP headers including the session token.
    - metabase_url (str): The base URL of the Metabase instance.
    - visualizations (list): A list of dictionaries defining the target visualizations.
    -----------
    Return:
    None
    """
    try:
        response = requests.get(f"{metabase_url}/card", headers=headers)
        response.raise_for_status()
        existing_cards = response.json()

        names_to_create = [v["name"] for v in visualizations]

        for card in existing_cards:
            if card["name"] in names_to_create:
                card_id = card["id"]
                archive_res = requests.put(
                    f"{metabase_url}/card/{card_id}",
                    headers=headers,
                    json={"archived": True},
                    timeout=10
                )
                archive_res.raise_for_status()
                logger.info(f"Old version '{card['name']}' archived.")

    except requests.exceptions.RequestException as e:
        logger.error(f"Error while cleaning up old cards: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "error": "MetabaseCleanupError",
                "details": str(e)}
        )


def create_cards(db_id, metabase_url, headers, visualizations):
    """
    Iterates through a list of visualization definitions to create new native
    SQL cards in Metabase, applying specific display and visualization settings
    for each chart type.
    -----------
    Arguments:
    - db_id (int): The ID of the database to query.
    - metabase_url (str): The base URL of the Metabase instance.
    - headers (dict): HTTP headers including the session token.
    - visualizations (list): Definitions including names, SQL queries, and viz settings.
    -----------
    Return:
    dict: A summary containing the status and the list of names of successfully created cards.
    """
    results = []
    try:
        for viz in visualizations:
            payload = {
                "name": viz["name"],
                "display": viz["display"],
                "visualization_settings": viz["visualization_settings"],
                "dataset_query": {
                    "database": db_id,
                    "type": "native",
                    "native": {"query": viz["sql"]}
                }
            }
            response = requests.post(
                f"{metabase_url}/card",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            results.append(viz["name"])
            logger.info(f"Card '{viz['name']}' created.")

        return {"status": "success", "created_cards": results}

    except requests.exceptions.RequestException as e:
        logger.error(f"Metabase Card Creation Failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "error": "MetabaseCardCreationError",
                "details": str(e)
            }
        )


def get_card_mapping(session_id, metabase_url):
    """
    Retrieves the complete list of cards from Metabase and builds a dictionary
    mapping each card name to its internal ID for easy lookup during dashboard
    assembly.
    -----------
    Arguments:
    - session_id (str): The active Metabase session token.
    - metabase_url (str): The base URL of the Metabase instance.
    -----------
    Return:
    dict: A mapping of {card_name: card_id}.
    """
    headers = {"X-Metabase-Session": session_id}

    try:
        response = requests.get(f"{metabase_url}/card", headers=headers)
        response.raise_for_status()
        cards = response.json()

        mapping = {card['name']: card['id'] for card in cards}

        return mapping

    except requests.exceptions.RequestException as e:
        logger.error(f"Error retrieving cards: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "error": "MetabaseCardRecoveryError",
                "details": str(e)
            }
        )


def get_dashboard_id(session_id, name, metabase_url):
    """
    Searches for an existing dashboard by its name and returns its internal
    identifier if it exists.
    -----------
    Arguments:
    - session_id (str): The active Metabase session token.
    - name (str): The display name of the dashboard to find.
    - metabase_url (str): The base URL of the Metabase instance.
    -----------
    Return:
    int or None: The dashboard ID if found, otherwise None.
    """
    headers = {"X-Metabase-Session": session_id}
    try:
        res = requests.get(f"{metabase_url}/dashboard", headers=headers)
        res.raise_for_status()
        dashboards = res.json()

        for dashboard in dashboards:
            if dashboard['name'] == name:
                return dashboard['id']
        return None

    except requests.exceptions.RequestException as e:
        logger.error(f"Metabase Dashboard Identification Failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "error": "MetabaseDashboardIdentificationError",
                "details": str(e)
            }
        )


def create_dashboard(session_id, headers, metabase_url):
    """
    Creates multiple themed dashboards and populates them with a specific
    grid layout of cards. It calculates positions (row/col) and sizes
    to organize the analytical visualizations into a coherent UI.
    -----------
    Arguments:
    - session_id (str): The active Metabase session token.
    - headers (dict): HTTP headers including the session token.
    - metabase_url (str): The base URL of the Metabase instance.
    -----------
    Return:
    None
    """
    payload = [
        {
            "name": "Work Env",
            "description": "Dashboards showing the distribution of work tools",
        },
        {
            "name": "General Data",
            "description": "Dashboards on data regarding individuals who have filed for unemployment benefits",
        }
    ]

    dash_ids = []

    try:
        for pay in payload:
            name = pay["name"]
            existing_id = get_dashboard_id(session_id, name, metabase_url)
            if existing_id:
                logger.info(f"Dashboard {name} already exist (ID: P{existing_id})")
                dash_ids.append(existing_id)
            else:
                response = requests.post(
                    f"{metabase_url}/dashboard",
                    headers=headers,
                    json=pay
                )
                response.raise_for_status()
                new_id = response.json().get("id")
                logger.info(f"Dashboard '{name}' created successfully.")
                dash_ids.append(new_id)

    except requests.exceptions.RequestException as e:
        logger.error(f"Metabase Dashboard Creation Failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "error": "MetabaseDashboardCreationError",
                "details": str(e)
            }
        )

    mapping = get_card_mapping(session_id, metabase_url)

    payload = [
        {
            "cards": [
                {
                    "id": -1,
                    "card_id": mapping.get("Database Used Repartition"),
                    "size_x": 12,
                    "size_y": 8,
                    "row": 0,
                    "col": 0,
                },
                {
                    "id": -2,
                    "card_id": mapping.get("Dev Environnement Used Repartition"),
                    "size_x": 12,
                    "size_y": 8,
                    "row": 0,
                    "col": 12,
                },
                {
                    "id": -3,
                    "card_id": mapping.get("Language Used Repartition"),
                    "size_x": 12,
                    "size_y": 8,
                    "row": 8,
                    "col": 0,
                },
                {
                    "id": -4,
                    "card_id": mapping.get("Learned Code Repartition"),
                    "size_x": 12,
                    "size_y": 8,
                    "row": 8,
                    "col": 12,
                },
                {
                    "id": -5,
                    "card_id": mapping.get("Platform Used Repartition"),
                    "size_x": 12,
                    "size_y": 8,
                    "row": 16,
                    "col": 0,
                },
                {
                    "id": -6,
                    "card_id": mapping.get("Webframe Used Repartition"),
                    "size_x": 12,
                    "size_y": 8,
                    "row": 16,
                    "col": 12,
                }
            ]
        },
        {
            "cards": [
                {
                    "id": -1,
                    "card_id": mapping.get("Mean salary by Country"),
                    "size_x": 24,
                    "size_y": 8,
                    "row": 0,
                    "col": 0,
                },
                {
                    "id": -2,
                    "card_id": mapping.get("Devs Repartition by Country"),
                    "size_x": 24,
                    "size_y": 8,
                    "row": 8,
                    "col": 0,
                },
                {
                    "id": -3,
                    "card_id": mapping.get("Salary Evolution by Years of Coding Experience"),
                    "size_x": 24,
                    "size_y": 8,
                    "row": 16,
                    "col": 0,
                }
            ]
        }
    ]

    try:
        for pay, id in zip(payload, dash_ids):
            response = requests.put(
                f"{metabase_url}/dashboard/{id}/cards",
                headers=headers,
                json=pay
            )
            response.raise_for_status()

    except requests.exceptions.RequestException as e:
        logger.error(f"Metabase Dashboard Graph Creation Failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={
                "error": "MetabaseDashboardGraphCreationError",
                "details": str(e)
            }
        )


def run_data_visualization_metabase():
    """
    Main orchestration function that executes the full visualization pipeline:
    authenticating, identifying the source DB, cleaning legacy cards,
    creating new SQL-based charts, and building the final dashboards.
    -----------
    Arguments:
    None
    -----------
    Return:
    None
    """
    session_id, metabase_url = get_metabase_client()

    headers = {
        "Content-Type": "application/json",
        "X-Metabase-Session": session_id
    }

    visualizations = [
        {
            "name": "Mean salary by Country",
            "sql": 'SELECT CASE WHEN "Country" = \'United States of America\' THEN \'United States\' WHEN "Country" = \'United Kingdom of Great Britain and Northern Ireland\' THEN \'United Kingdom\' ELSE "Country" END AS "Country", AVG("CompTotalEuro") AS "Mean Salary" FROM fact_survey WHERE "CompTotalEuro" < 499999 GROUP BY 1 HAVING COUNT(*) > 10 ORDER BY "Mean Salary" DESC',
            "display": "map",
            "visualization_settings": {
                "map.type": "region",
                'map.region': "world_countries",
                "map.dimension": "Country",
                "map.metric": "Mean Salary"
            }
        },
        {
            "name": "Devs Repartition by Country",
            "sql": 'SELECT CASE WHEN "Country" = \'United States of America\' THEN \'United States\' WHEN "Country" = \'United Kingdom of Great Britain and Northern Ireland\' THEN \'United Kingdom\' ELSE "Country" END AS "Country", COUNT(*) FROM fact_survey GROUP BY 1 HAVING COUNT(*) > 10 ORDER BY 2 DESC',
            "display": "map",
            "visualization_settings": {
                "map.type": "region",
                'map.region': "world_countries",
                "map.dimension": "Country",
                "map.metric": "Mean Salary"
            }
        },
        {
            "name": "Salary Evolution by Years Code",
            "sql": 'SELECT FLOOR("YearsCode" / 5) * 5 AS "Coding Experince", AVG("CompTotalEuro") AS "Mean Salary" FROM fact_survey WHERE "YearsCode" <= 50 GROUP BY 1 ORDER BY 1;',
            "display": "line",
            "visualization_settings": {
                "graph.dimensions": ["Coding Experince"],
                "graph.metrics": ["Mean Salary"],
                "graph.show_values": True,
                "line.interpolate": "monotone",
                "line.marker_enabled": True,
                "graph.x_axis.title_text": "Années d'expérience",
                "graph.y_axis.title_text": "Salaire Moyen (€)"
            }
        },
        {
            "name": "Database Used Repartition",
            "sql": 'SELECT "DatabaseHaveWorkedWith", COUNT(*) FROM analytics_database WHERE "DatabaseHaveWorkedWith" != \'NA\' GROUP BY 1 HAVING COUNT(*) > 10',
            "display": "pie",
            "visualization_settings": {}
        },
        {
            "name": "Dev Environnement Used Repartition",
            "sql": 'SELECT "DevEnvsHaveWorkedWith", COUNT(*) FROM analytics_devenvs WHERE "DevEnvsHaveWorkedWith" != \'NA\' GROUP BY 1 HAVING COUNT(*) > 10',
            "display": "pie",
            "visualization_settings": {}
        },
        {
            "name": "Language Used Repartition",
            "sql": 'SELECT "LanguageHaveWorkedWith", COUNT(*) FROM analytics_language WHERE "LanguageHaveWorkedWith" != \'NA\' GROUP BY 1 HAVING COUNT(*) > 10',
            "display": "pie",
            "visualization_settings": {}
        },
        {
            "name": "Learned Code Repartition",
            "sql": 'SELECT "LearnCode", COUNT(*) FROM analytics_learncode WHERE "LearnCode" != \'NA\' GROUP BY 1',
            "display": "pie",
            "visualization_settings": {}
        },
        {
            "name": "Platform Used Repartition",
            "sql": 'SELECT "PlatformHaveWorkedWith", COUNT(*) FROM analytics_platform WHERE "PlatformHaveWorkedWith" != \'NA\' GROUP BY 1',
            "display": "pie",
            "visualization_settings": {}
        },
        {
            "name": "Webframe Used Repartition",
            "sql": 'SELECT "WebframeHaveWorkedWith", COUNT(*) FROM analytics_webframe WHERE "WebframeHaveWorkedWith" != \'NA\' GROUP BY 1',
            "display": "pie",
            "visualization_settings": {}
        }
    ]

    db_id = get_database_id(headers, metabase_url, db_name="PostgreSQL")

    delete_old_cards(headers, metabase_url, visualizations)

    create_cards(db_id, metabase_url, headers, visualizations)

    create_dashboard(session_id, headers, metabase_url)


if __name__ == "__main__":
    try:
        run_data_visualization_metabase()
    except HTTPException as e:
        print(f"Error {e.status_code}: {e.detail}")
