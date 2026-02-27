from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    ENV: str = "development"

    # Database settings
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "postgres"
    DB_PASSWORD: str = ""
    DB_NAME: str = "fastapi_db"
    DATABASE_URL: Optional[str] = None

    # Vault settings
    VAULT_ENABLED: bool = False
    VAULT_ADDR: str = "http://localhost:8200"
    VAULT_TOKEN: str = ""
    VAULT_SECRET_PATH: str = "fastapi/database"

    # JWT settings
    JWT_SECRET: str = "your-secret-key-change-in-production"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
