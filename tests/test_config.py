"""Tests for app configuration (Settings class)."""

import pytest
from app.config import Settings


class TestSettingsClass:
    """Test suite for Settings class."""

    def test_settings_has_required_fields(self):
        """Test that Settings class has all required fields."""
        settings_fields = Settings.model_fields
        assert "ENV" in settings_fields
        assert "DB_HOST" in settings_fields
        assert "DB_PORT" in settings_fields
        assert "DB_USER" in settings_fields
        assert "VAULT_ENABLED" in settings_fields
        assert "JWT_SECRET" in settings_fields

    def test_settings_env_defaults(self):
        """Test that ENV field defaults to development."""
        assert Settings.model_fields["ENV"].default == "development"

    def test_settings_db_port_default(self):
        """Test that DB_PORT defaults to 5432."""
        assert Settings.model_fields["DB_PORT"].default == 5432

    def test_settings_vault_disabled_default(self):
        """Test that VAULT_ENABLED defaults to False."""
        assert Settings.model_fields["VAULT_ENABLED"].default is False

    def test_settings_env_var_overrides(self, monkeypatch, tmp_path):
        """Test that environment variables override defaults."""
        # Create a temporary .env file
        env_file_path = tmp_path / ".env"
        env_file_path.write_text("""
ENV=production
DB_HOST=prod-db.example.com
DB_PORT=5433
DB_USER=prod_user
DB_PASSWORD=secure_password
DB_NAME=prod_db
""")

        # Create a Settings instance with custom env_file
        class TestSettings(Settings):
            class Config:
                env_file = str(env_file_path)
                case_sensitive = True

        settings = TestSettings()
        assert settings.ENV == "production"
        assert settings.DB_HOST == "prod-db.example.com"
        assert settings.DB_PORT == 5433
        assert settings.DB_USER == "prod_user"

    def test_settings_loads_from_env_file(self):
        """Test that settings loads from .env file."""
        # The app should load from the actual .env file if it exists
        from app.config import settings

        # These should have values from the actual .env file
        assert isinstance(settings.ENV, str)
        assert isinstance(settings.DB_HOST, str)
        assert isinstance(settings.DB_PORT, int)
