import numpy as np
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, exc
from fastapi import HTTPException, status
from model.features_answer import get_features
from api.config import settings
import sys
import os
import traceback
import logging


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger("data_cleaner")

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))


def get_db_engine():
    """
    Creates and validates a SQLAlchemy engine for PostgreSQL using the application
    settings. It performs a connectivity check before returning the engine.
    -----------
    Arguments:
    None
    -----------
    Return:
    sqlalchemy.engine.Engine: A verified database engine instance.
    """
    try:
        dbname = settings.postgres_db
        user = settings.postgres_user
        password = settings.postgres_password
        host = settings.postgres_host
        port = settings.postgres_port
    except Exception as e:
        logger.error(f"Failed to connect PosgreSQL engine: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": type(e).__name__,
                "message": str(e),
                "context": "PostgreSQL Engine Connection"
            }
        )

    if not all([user, password, host, port, dbname]):
        msg = "Missing environment variables: DB_USER, DB_PASSWORD, DB_HOST, DB_PORT or DB_NAME."
        logger.critical(msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "ConfigError",
                "message": msg
            }
        )
    db_url = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
    try:
        engine = create_engine(db_url)
        with engine.connect():
            pass
        return engine
    except exc.OperationalError as e:
        logger.error(f"Database connection failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "error": "DatabaseUnreachable",
                "message": str(e.orig)
            }
        )


def erase_str(value: str):
    """
    Truncates a string to its first three characters. This is primarily used
    to normalize currency strings into ISO-like codes (e.g., "USD", "EUR").
    -----------
    Arguments:
    - value (str): The string to be truncated.
    -----------
    Return:
    str: The first three characters of the input or the original value if not a string.
    """
    return value[:3] if isinstance(value, str) else value


def clean_data(df, df_exchange_rate):
    """
    Performs initial data cleaning on the survey DataFrame. It selects relevant
    features, removes rows with missing compensation data, and normalizes
    currency formats before triggering the conversion process.
    -----------
    Arguments:
    - df (pd.DataFrame): The raw survey data chunk.
    - df_exchange_rate (pd.DataFrame): The reference table for currency rates.
    -----------
    Return:
    pd.DataFrame: A cleaned DataFrame with selected features and converted salaries.
    """
    try:
        features = get_features()
        required_cols = list(set(['ResponseId'] + features))

        missing_cols = [c for c in required_cols if c not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing columns in source table: {missing_cols}")

        df = df[required_cols].copy()
        df = df.dropna(subset="CompTotal")
        df.loc[:, "Currency"] = df["Currency"].apply(erase_str)

        return update_currency(df, df_exchange_rate)
    except Exception as e:
        logger.error(f"Transformation error in clean_data: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "DataTransformationError",
                "step": "clean_data",
                "message": str(e)
            }
        )


def update_currency(df, df_exchange_rate):
    """
    Calculates salaries in Euro using vectorized mapping. It includes safety
    checks for overflow and filters out extreme outliers (salaries outside
    the 1,000 to 999,999 Euro range).
    -----------
    Arguments:
    - df (pd.DataFrame): Dataframe containing 'CompTotal' and 'Currency' columns.
    - df_exchange_rate (pd.DataFrame): Dataframe containing 'currency' and 'Value' (rate).
    -----------
    Return:
    pd.DataFrame: Dataframe with a new 'CompTotalEuro' column, stripped of original salary info.
    """
    Salary_min, Salary_max = 1000, 999999
    FLOAT_MAX = np.finfo(np.float64).max

    try:
        series_rate = df_exchange_rate.set_index("currency")['Value']
        rate = df["Currency"].map(series_rate)

        is_safe = (rate.notna()) & (rate > 0) & (df["CompTotal"] < (FLOAT_MAX / rate))

        df.loc[:, "CompTotalEuro"] = np.where(
                                            is_safe,
                                            df["CompTotal"] * rate,
                                            np.nan
                                            )

        mask = (df["CompTotalEuro"] >= Salary_min) & (df["CompTotalEuro"] <= Salary_max)
        df = df[mask].copy()

        df.drop(columns=["Currency", "CompTotal"], inplace=True)
        return df
    except Exception as e:
        logger.error(f"Currency update failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "CurrencyConversionError",
                "message": str(e)
            }
        )


def run_clean_data():
    """
    Orchestrates the end-to-end cleaning and modeling pipeline. It reads data
    in chunks, processes dimensions (expanding multi-value strings like
    languages/databases), and populates a star schema (fact_survey and
    associated analytics_* tables) in the database.
    -----------
    Arguments:
    None
    -----------
    Return:
    dict: A success message indicating that the analytics tables have been populated.
    """
    engine = get_db_engine()

    columns_to_extract = [
        "LearnCode",
        "LanguageHaveWorkedWith",
        "DatabaseHaveWorkedWith",
        "PlatformHaveWorkedWith",
        "WebframeHaveWorkedWith",
        "DevEnvsHaveWorkedWith"
    ]

    try:
        try:
            df_exchange_rate = pd.read_sql("SELECT * FROM prod_exchange", engine)
            chunks = pd.read_sql("SELECT * FROM prod_survey", engine, chunksize=10000)

        except exc.ProgrammingError as e:
            logger.error(f"Source tables missing: {e}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "SourceTableNotFound",
                    "message": "Ensure prod_survey and prod_exchange exist."}
            )

        last_df_fact = None
        for i, df_chunk in enumerate(chunks):
            mode = 'replace' if i == 0 else 'append'
            logger.info(f"Processing chunk {i}...")

            df_chunk = clean_data(df_chunk, df_exchange_rate)

            for col in columns_to_extract:
                clean_name = col.replace('HaveWorkedWith', '').lower()
                table_name = f"analytics_{clean_name}"

                try:
                    df_dim = df_chunk[['ResponseId', col]].copy()
                    df_dim[col] = df_dim[col].str.split(';')
                    df_dim = df_dim.explode(col).dropna()
                    df_dim[col] = df_dim[col].str.strip()

                    df_dim.to_sql(table_name, engine, if_exists=mode, index=False)

                except Exception as e:
                    logger.error(f"Failed to write dimension table {table_name}: {e}")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail={
                            "error": "WriteError",
                            "table": table_name,
                            "message": str(e)
                        }
                    )

            last_df_fact = df_chunk.drop(columns=columns_to_extract)
            last_df_fact.to_sql('fact_survey', engine, if_exists=mode, index=False)

        return {"status": "success", "message": "Data cleaned and analytics tables populated."}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Critical error during main process: {traceback.format_exc()}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "UnexpectedFailure",
                "message": str(e),
                "traceback": traceback.format_exc().splitlines()[-3:]
            }
        )


if __name__ == "__main__":
    try:
        print(run_clean_data())
    except HTTPException as e:
        print(f"API Error [{e.status_code}]: {e.detail}")
