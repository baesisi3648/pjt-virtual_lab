import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Required
    OPENAI_API_KEY: str

    # Database (SQLite for MVP, PostgreSQL for Production)
    DATABASE_URL: str = "sqlite:///./virtual_lab.db"  # SQLite (파일 기반)
    # DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/virtual_lab"  # Production

    # Vector Database (Pinecone 또는 ChromaDB)
    VECTOR_DB_TYPE: str = "pinecone"  # "pinecone" 또는 "chromadb"

    # Pinecone Settings
    PINECONE_API_KEY: str | None = None
    PINECONE_ENVIRONMENT: str = "us-east-1"  # Pinecone 환경
    PINECONE_INDEX_NAME: str = "virtual-lab-regulatory-docs"

    # ChromaDB Settings (대안)
    CHROMA_HOST: str = "localhost"
    CHROMA_PORT: int = 8001
    CHROMA_COLLECTION_NAME: str = "regulatory_docs"

    # Redis Cache
    REDIS_URL: str | None = None

    # Phase 2 Web Search
    TAVILY_API_KEY: str | None = None

    # Optional
    LANGSMITH_API_KEY: str | None = None
    LANGSMITH_PROJECT: str = "virtual-lab"

    # Server Config
    FASTAPI_HOST: str = "0.0.0.0"
    FASTAPI_PORT: int = 8000

    # LLM Config
    GPT_MODEL: str = "gpt-4o"
    LLM_TEMPERATURE: float = 0.7
    LLM_MAX_TOKENS: int = 4096

    # RAG Config
    EMBEDDING_MODEL: str = "text-embedding-3-small"  # OpenAI 임베딩 모델
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

        # Pinecone 사용 시 API 키 필요
        if self.VECTOR_DB_TYPE == "pinecone" and not self.PINECONE_API_KEY:
            raise ValueError("PINECONE_API_KEY is required when VECTOR_DB_TYPE='pinecone'")


settings = Settings()
