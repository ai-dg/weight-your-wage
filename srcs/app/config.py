from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Pydantic va chercher automatiquement ces noms en MAJUSCULES dans l'OS
    minio_endpoint: str
    minio_root_user: str
    minio_root_password: str
    postgres_db: str
    postgres_user: str
    postgres_password: str
    postgres_host: str
    postgres_port: str
    metabase_url: str
    metabase_admin_first_name: str
    metabase_admin_last_name: str
    metabase_admin_email: str
    metabase_admin_password: str
    
    # Tu peux aussi définir des valeurs par défaut
    app_uid: int = 1000

    class Config:
        # Permet de lire un .env si jamais tu es hors Docker
        env_file = ".env"

settings = Settings()