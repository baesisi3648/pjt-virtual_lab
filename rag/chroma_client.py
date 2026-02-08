"""
ChromaDB Client

규제 문서용 벡터 컬렉션 관리
"""

import chromadb
from chromadb.config import Settings as ChromaSettings

from .config import CHROMA_COLLECTION_NAME


def get_chroma_client():
    """
    ChromaDB HTTP 클라이언트 생성

    Returns:
        chromadb.Client: ChromaDB 클라이언트 인스턴스

    Raises:
        ValueError: CHROMA_HOST 또는 CHROMA_PORT가 없을 경우
    """
    # Lazy import to avoid loading settings at module import time
    from config import settings

    if not settings.CHROMA_HOST or not settings.CHROMA_PORT:
        raise ValueError("CHROMA_HOST and CHROMA_PORT must be set in environment")

    client = chromadb.HttpClient(
        host=settings.CHROMA_HOST,
        port=settings.CHROMA_PORT,
        settings=ChromaSettings(anonymized_telemetry=False)
    )
    return client


def get_or_create_collection(client, collection_name=None):
    """
    규제 문서용 컬렉션 생성 또는 조회

    Args:
        client: ChromaDB 클라이언트
        collection_name: 컬렉션 이름 (기본값: regulatory_docs)

    Returns:
        chromadb.Collection: 컬렉션 인스턴스

    Metadata Schema:
        - source: 문서 출처 (Codex, FDA, EFSA, FSANZ 등)
        - document_type: guideline, regulation, case_study
        - year: 발행 연도
        - page: 페이지 번호
        - section: 섹션 제목 (optional)
    """
    if collection_name is None:
        collection_name = CHROMA_COLLECTION_NAME

    collection = client.get_or_create_collection(
        name=collection_name,
        metadata={
            "description": "NGT safety regulatory documents",
            "embedding_model": "text-embedding-3-small",
            "hnsw:space": "cosine",  # 코사인 유사도 사용
        }
    )
    return collection


def delete_collection(client, collection_name=None):
    """
    컬렉션 삭제 (테스트용)

    Args:
        client: ChromaDB 클라이언트
        collection_name: 컬렉션 이름
    """
    if collection_name is None:
        collection_name = CHROMA_COLLECTION_NAME

    try:
        client.delete_collection(name=collection_name)
    except Exception:
        pass  # 컬렉션이 없으면 무시
