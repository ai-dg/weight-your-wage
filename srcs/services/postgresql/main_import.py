import csv
import psycopg2
from psycopg2 import sql
import os
import sys
from dotenv import load_dotenv
import json
from pathlib import Path
from minio import Minio
import io
import logging
from fastapi import HTTPException, status
from typing import List, Tuple
from minio.error import S3Error
import traceback


logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("postgresql_importer")


csv.field_size_limit(sys.maxsize)


def get_db_client():
    dbname=os.getenv('DB_NAME')
    user=os.getenv('DB_USER')
    password=os.getenv('DB_PASSWORD')
    host=os.getenv('DB_HOST')
    port=os.getenv('DB_PORT')

    if not all([dbname, user, password, host, port]):
        msg = "Missing environment variables: DB_NAME, DB_USER, DB_PASSWORD, DB_HOST, or DB_PORT."
        logger.critical(msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "ConfigError",
                "message": msg
            }
        )
    try:
        conn = psycopg2.connect(
        dbname=dbname,
        user=user,
        password=password,
        host=host,
        port=port
        )
        return conn
    except Exception as e:
        logger.error(f"Failed to initialize PosgreSQL client: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": type(e).__name__,
                "message": str(e),
                "context": "PostgreSQL Client Initialization"
            }
        )


def get_minio_client() -> Minio:
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


def generate_staging_table(cursor, client, bucket, object_name, table_name):
    try:
        response = client.get_object(bucket, object_name)
        csv_text_stream = io.TextIOWrapper(response, encoding='utf-8')
        reader = csv.reader(csv_text_stream)
        columns = next(reader)

        column_definitions = [
            sql.SQL("{} TEXT").format(sql.Identifier(col)) 
            for col in columns
        ]

        cursor.execute(sql.SQL("DROP TABLE IF EXISTS {} CASCADE").format(sql.Identifier(table_name)))

        create_query = sql.SQL("CREATE TABLE {} ({})").format(
            sql.Identifier(table_name),
            sql.SQL(', ').join(column_definitions)
        )

        cursor.execute(create_query)
    except S3Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "MinioReadError",
                "object": object_name,
                "message": e.message
            }
        )
    except psycopg2.Error as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "PostgresSQLSyntaxError",
                "table": table_name,
                "message": e.pgerror
            }
        )
    finally:
        if 'response' in locals():
            response.close()
            response.release_conn()


def fill_staging_table(cursor, client, bucket, object_name, table_name):
    try:
        response = client.get_object(bucket, object_name)
    
        copy_sql = sql.SQL("COPY {} FROM STDIN WITH (FORMAT CSV, HEADER, DELIMITER ',')").format(
            sql.Identifier(table_name)
        )
        cursor.copy_expert(sql=copy_sql, file=response)
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail={
                "error": "DataCopyError",
                "table": table_name,
                "message": str(e)
            }
        )
    finally:
        if 'response' in locals():
            response.close()
            response.release_conn()

def create_production_table(cursor, mapping_file, table_name):
    try:
        with open(mapping_file, 'r', encoding='utf-8') as f:
            mapping = json.load(f)

        definitions = [
            sql.SQL("{} {}").format(sql.Identifier(col), sql.SQL(dtype))
            for col, dtype in mapping.items()
        ]

        cursor.execute(sql.SQL("DROP TABLE IF EXISTS {} CASCADE").format(sql.Identifier(table_name)))

        create_query = sql.SQL("CREATE TABLE {} ({})").format(
                sql.Identifier(table_name),
                sql.SQL(', ').join(definitions)
            )
        cursor.execute(create_query)
        logger.info(f"Production table '{table_name}' created.")
    
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON mapping file {mapping_file}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "InvalidMappingJSON",
                "file": str(mapping_file),
                "message": str(e)
            }
        )
    except psycopg2.Error as e:
        logger.error(f"Database error while creating {table_name}: {e.pgerror}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "TableCreationError",
                "table": table_name,
                "db_message": e.pgerror
            }
        )


def clean_transfer_data(cursor, mapping_file, staging_table, prod_table):
    try:
        with open(mapping_file, 'r', encoding='utf-8') as f:
            mapping = json.load(f)

        cursor.execute(sql.SQL("SELECT * FROM {} LIMIT 0").format(sql.Identifier(staging_table)))
        actual_staging_cols = [desc[0] for desc in cursor.description]

        columns_names = []
        select_clauses = []

        for i, (col_name, data_type) in enumerate(mapping.items()):
            target_col = sql.Identifier(col_name)
            columns_names.append(target_col)

            source_col = sql.Identifier(actual_staging_cols[i])

            dtype_upper = data_type.upper()
            if any(x in dtype_upper for x in ["INT", "NUMERIC", "DECIMAL"]):
                clean_part = sql.SQL("CAST(NULLIF(TRIM({}), 'NA') AS {})").format(
                    source_col, sql.SQL(data_type)
                )
            elif "BOOL" in dtype_upper:
                clean_part = sql.SQL("CAST(NULLIF(TRIM({}), 'NA') AS BOOLEAN)").format(source_col)
            else:
                clean_part = sql.SQL("TRIM({})").format(source_col)
    
            select_clauses.append(clean_part)

        query = sql.SQL("INSERT INTO {} ({}) SELECT {} FROM {}").format(
            sql.Identifier(prod_table),
            sql.SQL(', ').join(columns_names),
            sql.SQL(', ').join(select_clauses),
            sql.Identifier(staging_table)
        )

        cursor.execute(query)
        logger.info(f"Data transferred and cleaned: {staging_table} -> {prod_table}")
    
    except (psycopg2.DataError, psycopg2.IntegrityError) as e:
        logger.error(f"Data conversion failed for {prod_table}: {e.pgerror}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "DataTransformationError",
                "message": "Column type mismatch or invalid data format in CSV.",
                "db_detail": e.pgerror.splitlines()[0]
            }
        )


def run_minio_import_postgresql():
    conn = None
    try:
        load_dotenv()
        conn = get_db_client()
        client = get_minio_client()
        bucket = "raw-data"
        BASE_DIR = Path(__file__).resolve().parent

        staging: List[Tuple[str, str]] = [
            ("stack_overflow_2025.csv", "staging_survey"),
            ("exchange_rate_2025.csv", "staging_exchange")
        ]

        production = List[Tuple[Path, str, str]] = [
            (BASE_DIR / "mapping_prod_survey.json", "staging_survey", "prod_survey"),
            (BASE_DIR / "mapping_prod_exchange.json", "staging_exchange", "prod_exchange")
        ]

        with conn.cursor() as cursor:
            for object, staging_table in staging:
                logger.info(f"Processing staging: {staging_table}")
                generate_staging_table(cursor, client, bucket, object, staging_table)
                fill_staging_table(cursor, client, bucket, object, staging_table)

            for mapping_file, staging_table, prod_table in production:
                if not mapping_file.exists():
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail={"error": "MappingFileNotFound",
                                "path": str(mapping_file)
                        }
                    )
                logger.info(f"Processing production: {prod_table}")
                create_production_table(cursor, mapping_file, prod_table)
                clean_transfer_data(cursor, mapping_file, staging_table, prod_table)

            conn.commit()
            logger.info("Transaction committed successfully.")
            return {"status": "success", "message": "ETL process completed."}

    except HTTPException:
        if conn: conn.rollback()
        raise
    except Exception as e:
        if conn: conn.rollback()
        logger.error(f"Critical ETL Failure: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "CriticalETLFailure",
                "message": str(e),
                "traceback": traceback.format_exc().splitlines()[-3:]
            }
        )
    
    finally:
        if 'conn' in locals(): conn.close()

if __name__ == "__main__":
    try:
        print(run_minio_import_postgresql())
    except HTTPException as e:
        print(f"API Error [{e.status_code}]: {e.detail}")
