from dotenv import load_dotenv
import os
import requests
from fastapi import HTTPException, status
import traceback
import logging


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("metabase_creater")


def get_metabase_client():
    load_dotenv()
    username = os.getenv("METABASE_ADMIN_EMAIL")
    password = os.getenv("METABASE_ADMIN_PASSWORD")
    metabase_url = os.getenv("METABASE_URL")
        
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
                "message": "Impossible de se connecter à Metabase ou identifiants incorrects.",
                "details": str(e)
            }
        )

def get_database_id(headers, metabase_url,db_name="PostgreSQL"):
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

def run_init_metabase():
    session_id, metabase_url = get_metabase_client()
    
    headers = {
        "Content-Type": "application/json",
        "X-Metabase-Session": session_id
    }
    db_id = get_database_id(headers, metabase_url, db_name="PostgreSQL")
    
    visualizations = [
        {
            "name": "Mean salary by country",
            "sql": 'SELECT "Country", AVG("CompTotalEuro") AS "Mean Salary" FROM fact_survey WHERE "CompTotalEuro" < 499999 GROUP BY 1 HAVING COUNT(*) > 10 ORDER BY "Mean Salary" DESC',
            "display": "bar"
        },
        {
            "name": "Devs Repartition by Country",
            "sql": 'SELECT "Country", COUNT(*) FROM fact_survey GROUP BY 1 HAVING COUNT(*) > 10 ORDER BY 2 DESC',
            "display": "pie"
        },
        {
            "name": "Salary Evolution by Years Code",
            "sql": 'SELECT FLOOR("YearsCode" / 5) * 5 AS "Coding Experince", AVG("CompTotalEuro") AS "Mean Salary" FROM fact_survey WHERE "YearsCode" <= 50 GROUP BY 1 ORDER BY 1;',
            "display": "line"
        },
        {
            "name": "Database Used Repartition",
            "sql": 'SELECT "DatabaseHaveWorkedWith", COUNT(*) FROM analytics_database WHERE "DatabaseHaveWorkedWith" != \'NA\' GROUP BY 1 HAVING COUNT(*) > 10',
            "display": "pie"
        },
        {
            "name": "Dev Environnement Used Repartition",
            "sql": 'SELECT "DevEnvsHaveWorkedWith", COUNT(*) FROM analytics_devenvs WHERE "DevEnvsHaveWorkedWith" != \'NA\' GROUP BY 1 HAVING COUNT(*) > 10',
            "display": "pie"
        },
        {
            "name": "Language Used Repartition",
            "sql": 'SELECT "LanguageHaveWorkedWith", COUNT(*) FROM analytics_language WHERE "LanguageHaveWorkedWith" != \'NA\' GROUP BY 1 HAVING COUNT(*) > 10',
            "display": "pie"
        },
        {
            "name": "Learned Code Repartition",
            "sql": 'SELECT "LearnCode", COUNT(*) FROM analytics_learncode WHERE "LearnCode" != \'NA\' GROUP BY 1',
            "display": "pie"
        },
        {
            "name": "Platform Used Repartition",
            "sql": 'SELECT "PlatformHaveWorkedWith", COUNT(*) FROM analytics_platform WHERE "PlatformHaveWorkedWith" != \'NA\' GROUP BY 1',
            "display": "pie"
        },
        {
            "name": "Webframe Used Repartition",
            "sql": 'SELECT "WebframeHaveWorkedWith", COUNT(*) FROM analytics_webframe WHERE "WebframeHaveWorkedWith" != \'NA\' GROUP BY 1',
            "display": "pie"
        }
    ]

    delete_old_cards(headers, metabase_url, visualizations)

    results = []

    try:
        for viz in visualizations:
            payload = {
                "name": viz["name"],
                "display": viz["display"],
                "visualization_settings": {},
                "dataset_query": {
                    "database": db_id,
                    "type": "native",
                    "native": {"query": viz["sql"]}
                }
            }
            res = requests.post(
                f"{metabase_url}/card",
                headers=headers,
                json=payload
            )
            res.raise_for_status()
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


if __name__ == "__main__":
    try:
        run_init_metabase()
    except HTTPException as e:
        print(f"Error {e.status_code}: {e.detail}")
