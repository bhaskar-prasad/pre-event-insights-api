import logging
from typing import AsyncGenerator
from urllib.parse import quote
import hvac
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.orm import declarative_base

from app.config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()


async def get_db_url() -> str:
    """Fetch database URL from Vault or environment variables."""

    if settings.VAULT_ENABLED:
        try:
            client = hvac.Client(url=settings.VAULT_ADDR, token=settings.VAULT_TOKEN)

            # Parse the Vault secret path - remove 'secret/data/' prefix if present
            # hvac KV v2 client adds '/data/' automatically, so we need just the secret name
            vault_path = settings.VAULT_SECRET_PATH
            if vault_path.startswith("secret/data/"):
                vault_path = vault_path.replace("secret/data/", "")
            elif vault_path.startswith("secret/"):
                vault_path = vault_path.replace("secret/", "")

            # Read secret from Vault (KV v2)
            secret_data = client.secrets.kv.v2.read_secret_version(path=vault_path)

            db_credentials = secret_data["data"]["data"]

            # Build database URL from Vault credentials
            # URL-encode username and password to handle special characters like @
            username = quote(db_credentials['username'], safe='')
            password = quote(db_credentials['password'], safe='')
            host = db_credentials['host']
            port = db_credentials['port']
            database = db_credentials['database']

            db_url = (
                f"postgresql+asyncpg://"
                f"{username}:{password}@"
                f"{host}:{port}/"
                f"{database}"
            )

            logger.info("Database credentials fetched from Vault")
            return db_url

        except Exception as e:
            logger.error(f"Failed to fetch credentials from Vault: {str(e)}")
            raise

    # Fallback to environment variables or direct URL
    if settings.DATABASE_URL:
        logger.info("Using DATABASE_URL from environment")
        return settings.DATABASE_URL

    # URL-encode credentials to handle special characters
    db_user = quote(settings.DB_USER, safe='')
    db_password = quote(settings.DB_PASSWORD, safe='')

    db_url = (
        f"postgresql+asyncpg://"
        f"{db_user}:{db_password}@"
        f"{settings.DB_HOST}:{settings.DB_PORT}/"
        f"{settings.DB_NAME}"
    )

    logger.info("Using database credentials from environment variables")
    return db_url


# Initialize engine and session factory (will be set in app startup)
engine = None
async_session_maker = None


async def init_db() -> None:
    """Initialize database engine and session maker."""
    global engine, async_session_maker

    db_url = await get_db_url()

    engine = create_async_engine(
        db_url,
        echo=settings.ENV == "development",
        future=True,
        pool_pre_ping=True,
    )

    async_session_maker = async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )

    logger.info("Database engine initialized")


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting database sessions."""
    if async_session_maker is None:
        raise RuntimeError("Database not initialized. Call init_db() on app startup.")

    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def close_db() -> None:
    """Close database connections."""
    global engine

    if engine is not None:
        await engine.dispose()
        logger.info("Database connections closed")
