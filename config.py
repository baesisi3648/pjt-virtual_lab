import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Required
    OPENAI_API_KEY: str
    POSTGRES_URL: str
    CHROMA_HOST: str
    CHROMA_PORT: int
    TAVILY_API_KEY: str
    REDIS_URL: str

    # Optional
    LANGSMITH_API_KEY: str | None = None
    LANGSMITH_PROJECT: str = "virtual-lab"

    # Server Config
    FASTAPI_HOST: str = "0.0.0.0"
    FASTAPI_PORT: int = 8000

    # LLM Config
    GPT4O_MODEL: str = "gpt-4o"
    GPT4O_MINI_MODEL: str = "gpt-4o-mini"
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 4096

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).parent / ".env"),
        env_file_encoding='utf-8',
        extra='ignore'
    )

    def validate_secrets(self):
        """Validate API keys have correct format"""
        if not self.TAVILY_API_KEY.startswith("tvly-"):
            raise ValueError("TAVILY_API_KEY must start with 'tvly-'")

        if not self.OPENAI_API_KEY.startswith("sk-"):
            raise ValueError("OPENAI_API_KEY must start with 'sk-'")

        if self.LANGSMITH_API_KEY and not self.LANGSMITH_API_KEY.startswith("lsv2_"):
            raise ValueError("LANGSMITH_API_KEY must start with 'lsv2_'")


settings = Settings()
