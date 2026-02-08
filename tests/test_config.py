"""Test config.py with pytest"""
import os
import pytest
from pydantic import ValidationError


def test_config_loads_with_valid_env_vars(monkeypatch):
    """Test Settings loads correctly with valid environment variables"""
    # Set valid environment variables
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key-123")
    monkeypatch.setenv("POSTGRES_URL", "postgresql://virtual_lab:password@localhost:5432/virtual_lab")
    monkeypatch.setenv("CHROMA_HOST", "localhost")
    monkeypatch.setenv("CHROMA_PORT", "8001")
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-test-key-456")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379")

    # Import after setting env vars
    from config import Settings
    settings = Settings()

    assert settings.OPENAI_API_KEY == "sk-test-key-123"
    assert settings.POSTGRES_URL == "postgresql://virtual_lab:password@localhost:5432/virtual_lab"
    assert settings.CHROMA_HOST == "localhost"
    assert settings.CHROMA_PORT == 8001
    assert settings.TAVILY_API_KEY == "tvly-test-key-456"
    assert settings.REDIS_URL == "redis://localhost:6379"


def test_config_with_optional_langsmith(monkeypatch):
    """Test Settings with optional LangSmith API key"""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
    monkeypatch.setenv("POSTGRES_URL", "postgresql://localhost/test")
    monkeypatch.setenv("CHROMA_HOST", "localhost")
    monkeypatch.setenv("CHROMA_PORT", "8001")
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-test")
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379")
    monkeypatch.setenv("LANGSMITH_API_KEY", "lsv2_test_key")

    from config import Settings
    settings = Settings()

    assert settings.LANGSMITH_API_KEY == "lsv2_test_key"
    assert settings.LANGSMITH_PROJECT == "virtual-lab"


def test_config_default_values(monkeypatch):
    """Test Settings default values"""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("POSTGRES_URL", "postgresql://localhost/test")
    monkeypatch.setenv("CHROMA_HOST", "localhost")
    monkeypatch.setenv("CHROMA_PORT", "8001")
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-test")
    monkeypatch.setenv("REDIS_URL", "redis://localhost")

    from config import Settings
    settings = Settings()

    assert settings.FASTAPI_HOST == "0.0.0.0"
    assert settings.FASTAPI_PORT == 8000
    assert settings.GPT4O_MODEL == "gpt-4o"
    assert settings.GPT4O_MINI_MODEL == "gpt-4o-mini"
    assert settings.LLM_TEMPERATURE == 0.7
    assert settings.LLM_MAX_TOKENS == 4096


def test_validate_secrets_valid_keys(monkeypatch):
    """Test validate_secrets with valid API keys"""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-valid-key")
    monkeypatch.setenv("POSTGRES_URL", "postgresql://localhost/test")
    monkeypatch.setenv("CHROMA_HOST", "localhost")
    monkeypatch.setenv("CHROMA_PORT", "8001")
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-valid-key")
    monkeypatch.setenv("REDIS_URL", "redis://localhost")

    from config import Settings
    settings = Settings()

    # Should not raise any exception
    settings.validate_secrets()


def test_validate_secrets_invalid_tavily_key(monkeypatch):
    """Test validate_secrets rejects invalid TAVILY_API_KEY"""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-valid-key")
    monkeypatch.setenv("POSTGRES_URL", "postgresql://localhost/test")
    monkeypatch.setenv("CHROMA_HOST", "localhost")
    monkeypatch.setenv("CHROMA_PORT", "8001")
    monkeypatch.setenv("TAVILY_API_KEY", "invalid-key")  # Missing tvly- prefix
    monkeypatch.setenv("REDIS_URL", "redis://localhost")

    from config import Settings
    settings = Settings()

    with pytest.raises(ValueError, match="TAVILY_API_KEY must start with 'tvly-'"):
        settings.validate_secrets()


def test_validate_secrets_invalid_openai_key(monkeypatch):
    """Test validate_secrets rejects invalid OPENAI_API_KEY"""
    monkeypatch.setenv("OPENAI_API_KEY", "invalid-key")  # Missing sk- prefix
    monkeypatch.setenv("POSTGRES_URL", "postgresql://localhost/test")
    monkeypatch.setenv("CHROMA_HOST", "localhost")
    monkeypatch.setenv("CHROMA_PORT", "8001")
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-valid-key")
    monkeypatch.setenv("REDIS_URL", "redis://localhost")

    from config import Settings
    settings = Settings()

    with pytest.raises(ValueError, match="OPENAI_API_KEY must start with 'sk-'"):
        settings.validate_secrets()


def test_validate_secrets_invalid_langsmith_key(monkeypatch):
    """Test validate_secrets rejects invalid LANGSMITH_API_KEY"""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-valid-key")
    monkeypatch.setenv("POSTGRES_URL", "postgresql://localhost/test")
    monkeypatch.setenv("CHROMA_HOST", "localhost")
    monkeypatch.setenv("CHROMA_PORT", "8001")
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-valid-key")
    monkeypatch.setenv("REDIS_URL", "redis://localhost")
    monkeypatch.setenv("LANGSMITH_API_KEY", "invalid-key")  # Missing lsv2_ prefix

    from config import Settings
    settings = Settings()

    with pytest.raises(ValueError, match="LANGSMITH_API_KEY must start with 'lsv2_'"):
        settings.validate_secrets()


def test_config_missing_required_field(monkeypatch):
    """Test Settings raises ValidationError when required field is missing"""
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    # Missing POSTGRES_URL, CHROMA_HOST, etc.

    from config import Settings

    with pytest.raises(ValidationError):
        Settings()
