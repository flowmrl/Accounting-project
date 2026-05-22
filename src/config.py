"""Configuration de l'application via variables d'environnement."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Base de données
    database_url: str = "postgresql+psycopg2://compta:compta@localhost:5432/compta_pme"
    db_echo: bool = False

    # Auth JWT
    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 8  # 8 heures

    # App
    app_name: str = "Compta PME"
    debug: bool = False
    version: str = "0.1.0"


settings = Settings()
