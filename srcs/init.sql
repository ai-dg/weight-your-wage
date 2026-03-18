-- Création de l'utilisateur pour MLflow
CREATE USER mlflow WITH PASSWORD 'mlflow';

-- Création de la base de données appartenant à cet utilisateur
CREATE DATABASE mlflowdb OWNER mlflow;