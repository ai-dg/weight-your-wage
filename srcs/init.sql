-- Create the user for MLflow
CREATE USER mlflow_user WITH PASSWORD 'mlflow_password';

-- Create the database for MLflow
CREATE DATABASE mlflow_db OWNER mlflow_user;

-- Give the user permissions
GRANT ALL PRIVILEGES ON DATABASE mlflow_db TO mlflow_user;