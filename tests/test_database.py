"""Tests for database module."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from urllib.parse import quote
from app.database import get_db_url, get_session
from app.config import Settings


class TestGetDbUrl:
    """Test suite for get_db_url function."""

    @pytest.mark.asyncio
    async def test_get_db_url_with_env_vars(self, monkeypatch):
        """Test get_db_url constructs correct URL from env vars."""
        monkeypatch.setenv("VAULT_ENABLED", "false")
        monkeypatch.setenv("DB_HOST", "localhost")
        monkeypatch.setenv("DB_PORT", "5432")
        monkeypatch.setenv("DB_USER", "postgres")
        monkeypatch.setenv("DB_PASSWORD", "password123")
        monkeypatch.setenv("DB_NAME", "fastapi_db")

        url = await get_db_url()
        assert url == "postgresql+asyncpg://postgres:password123@localhost:5432/fastapi_db"

    @pytest.mark.asyncio
    async def test_get_db_url_url_encodes_special_chars(self, monkeypatch):
        """Test that special characters in username/password are URL-encoded."""
        monkeypatch.setenv("VAULT_ENABLED", "false")
        monkeypatch.setenv("DB_HOST", "localhost")
        monkeypatch.setenv("DB_PORT", "5432")
        monkeypatch.setenv("DB_USER", "user@domain")
        monkeypatch.setenv("DB_PASSWORD", "pass@word#123")
        monkeypatch.setenv("DB_NAME", "fastapi_db")

        url = await get_db_url()
        # @ and # should be URL-encoded
        expected_user = quote("user@domain", safe='')
        expected_pass = quote("pass@word#123", safe='')
        assert url == f"postgresql+asyncpg://{expected_user}:{expected_pass}@localhost:5432/fastapi_db"

    @pytest.mark.asyncio
    async def test_get_db_url_with_database_url_env_var(self, monkeypatch):
        """Test that DATABASE_URL env var is used if set."""
        monkeypatch.setenv("VAULT_ENABLED", "false")
        monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://custom:url@custom-host/custom_db")

        url = await get_db_url()
        assert url == "postgresql+asyncpg://custom:url@custom-host/custom_db"

    @pytest.mark.asyncio
    async def test_get_db_url_vault_enabled_path(self, monkeypatch):
        """Test get_db_url with Vault enabled."""
        monkeypatch.setenv("VAULT_ENABLED", "true")
        monkeypatch.setenv("VAULT_ADDR", "http://localhost:8200")
        monkeypatch.setenv("VAULT_TOKEN", "s.test-token")
        monkeypatch.setenv("VAULT_SECRET_PATH", "secret/data/fastapi/database")

        # Mock hvac client
        mock_client = MagicMock()
        mock_secret_data = {
            "data": {
                "data": {
                    "username": "vault_user",
                    "password": "vault_pass",
                    "host": "vault-db.example.com",
                    "port": "5432",
                    "database": "vault_db",
                }
            }
        }
        mock_client.secrets.kv.v2.read_secret_version.return_value = mock_secret_data

        with patch("app.database.hvac.Client", return_value=mock_client):
            url = await get_db_url()
            assert url == "postgresql+asyncpg://vault_user:vault_pass@vault-db.example.com:5432/vault_db"

    @pytest.mark.asyncio
    async def test_get_db_url_vault_strips_secret_prefix(self, monkeypatch):
        """Test that Vault secret path is normalized correctly."""
        monkeypatch.setenv("VAULT_ENABLED", "true")
        monkeypatch.setenv("VAULT_ADDR", "http://localhost:8200")
        monkeypatch.setenv("VAULT_TOKEN", "s.test-token")
        monkeypatch.setenv("VAULT_SECRET_PATH", "secret/data/fastapi/database")

        mock_client = MagicMock()
        mock_secret_data = {
            "data": {
                "data": {
                    "username": "user",
                    "password": "pass",
                    "host": "host",
                    "port": "5432",
                    "database": "db",
                }
            }
        }
        mock_client.secrets.kv.v2.read_secret_version.return_value = mock_secret_data

        with patch("app.database.hvac.Client", return_value=mock_client) as mock_hvac:
            await get_db_url()
            # Should strip "secret/data/" prefix
            mock_client.secrets.kv.v2.read_secret_version.assert_called_once_with(
                path="fastapi/database"
            )

    @pytest.mark.asyncio
    async def test_get_db_url_vault_error_handling(self, monkeypatch):
        """Test error handling when Vault fetch fails."""
        monkeypatch.setenv("VAULT_ENABLED", "true")
        monkeypatch.setenv("VAULT_ADDR", "http://localhost:8200")
        monkeypatch.setenv("VAULT_TOKEN", "s.test-token")

        mock_client = MagicMock()
        mock_client.secrets.kv.v2.read_secret_version.side_effect = Exception("Vault connection failed")

        with patch("app.database.hvac.Client", return_value=mock_client):
            with pytest.raises(Exception, match="Vault connection failed"):
                await get_db_url()


class TestGetSession:
    """Test suite for get_session dependency."""

    @pytest.mark.asyncio
    async def test_get_session_raises_without_init(self):
        """Test that get_session raises if database not initialized."""
        # Reset module-level variables
        import app.database as db_module
        original_maker = db_module.async_session_maker
        db_module.async_session_maker = None

        try:
            with pytest.raises(RuntimeError, match="Database not initialized"):
                async for _ in get_session():
                    pass
        finally:
            db_module.async_session_maker = original_maker

    @pytest.mark.asyncio
    async def test_get_session_yields_and_closes(self):
        """Test that get_session yields session and closes it."""
        mock_session = AsyncMock()
        mock_session_maker = AsyncMock()
        mock_session_maker.return_value.__aenter__.return_value = mock_session
        mock_session_maker.return_value.__aexit__.return_value = None

        import app.database as db_module
        original_maker = db_module.async_session_maker
        db_module.async_session_maker = mock_session_maker

        try:
            async for session in get_session():
                assert session == mock_session
            mock_session.close.assert_called_once()
        finally:
            db_module.async_session_maker = original_maker
