"""
RAG (Retrieval-Augmented Generation) Module

규제 문서 검색 및 컨텍스트 주입.
Pinecone (기본, 프로덕션) + ChromaDB (로컬 개발, optional) 지원.

ChromaDB는 Python 3.14+ 비호환 + 무거운 의존성이므로 Optional import로 처리.
배포 환경(VECTOR_DB_TYPE=pinecone)에서는 chromadb 미설치여도 정상 동작.
"""

from .embeddings import get_embedding_function, get_single_embedding
from .pdf_processor import (
    extract_text_from_pdf,
    chunk_text,
    process_pdf,
    process_text_file
)

# ChromaDB는 optional (설치되지 않은 환경에서 import 실패 방지)
try:
    from .chroma_client import get_chroma_client, get_or_create_collection
    _CHROMA_AVAILABLE = True
except ImportError:
    _CHROMA_AVAILABLE = False
    get_chroma_client = None  # type: ignore
    get_or_create_collection = None  # type: ignore

__all__ = [
    "get_embedding_function",
    "get_single_embedding",
    "extract_text_from_pdf",
    "chunk_text",
    "process_pdf",
    "process_text_file",
    "get_chroma_client",
    "get_or_create_collection",
]
