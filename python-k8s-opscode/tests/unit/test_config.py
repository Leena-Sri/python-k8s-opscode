"""Unit tests for configuration management."""

import os
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from app.core.config import Settings, get_settings


class TestSettings:
    """Test cases for Settings class."""

    def test_default_settings(self):
        """Test default configuration values."""
        settings = Settings()
        assert settings.app_name == "opscode"
        assert settings.app_version == "0.1.0"
        assert settings.environment == "development"
        assert settings.api_host == "0.0.0.0"
        assert settings.api_port == 8000
        assert settings.debug is False

    def test_settings_from_env(self):
        """Test loading settings from environment variables."""
        with patch.dict(os.environ, {
            'APP_NAME': 'test-app',
            'ENVIRONMENT': 'production',
            'API_PORT': '9000',
        }):
            settings = Settings()
            assert settings.app_name == 'test-app'
            assert settings.environment == 'production'
            assert settings.api_port == 9000

    def test_database_url_validation(self):
        """Test database URL validation."""
        with pytest.raises(ValidationError):
            Settings(database_url="invalid://url")

    def test_cors_origins_parsing(self):
        """Test CORS origins parsing."""
        settings = Settings(cors_origins="http://localhost:3000,http://localhost:8080")
        assert settings.cors_origins == ["http://localhost:3000", "http://localhost:8080"]

    def test_is_production(self):
        """Test production environment detection."""
        settings = Settings(environment="production")
        assert settings.is_production is True
        assert settings.is_development is False

    def test_is_development(self):
        """Test development environment detection."""
        settings = Settings(environment="development")
        assert settings.is_development is True
        assert settings.is_production is False

    def test_get_settings_caching(self):
        """Test that get_settings returns cached instance."""
        settings1 = get_settings()
        settings2 = get_settings()
        assert settings1 is settings2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
