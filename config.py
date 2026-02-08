import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Required
    OPENAI_API_KEY: str

    # Phase 0 Infrastructure (Optional for MVP mode)
    POSTGRES_URL: str | None = None
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8001
    REDIS_URL: str | None = None

    # Phase 2 Web Search (Optional)
    TAVILY_API_KEY: str | None = None

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

    # RAG Config
    CHROMA_COLLECTION_NAME: str = "regulatory_docs"
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    CHUNK_SIZE: int = 1000
    CHUNK_OVERLAP: int = 200
    TOP_K: int = 5
    SIMILARITY_THRESHOLD: float = 0.7

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).parent / ".env"),
        env_file_encoding='utf-8',
        extra='ignore'
    )

    def validate_secrets(self):
        """Validate API keys have correct format"""
        if not self.OPENAI_API_KEY.startswith("sk-"):
            raise ValueError("OPENAI_API_KEY must start with 'sk-'")

        if self.TAVILY_API_KEY and not self.TAVILY_API_KEY.startswith("tvly-"):
            raise ValueError("TAVILY_API_KEY must start with 'tvly-'")

        if self.LANGSMITH_API_KEY and not self.LANGSMITH_API_KEY.startswith("lsv2_"):
            raise ValueError("LANGSMITH_API_KEY must start with 'lsv2_'")


settings = Settings()
