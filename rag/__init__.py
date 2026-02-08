"""
RAG (Retrieval-Augmented Generation) Module

규제 문서 검색 및 컨텍스트 주입을 위한 ChromaDB 기반 벡터 스토어
"""

from .chroma_client import get_chroma_client, get_or_create_collection
from .embeddings import get_embedding_function, get_single_embedding
from .pdf_processor import (
    extract_text_from_pdf,
    chunk_text,
    process_pdf,
    process_text_file
)

__all__ = [
    "get_chroma_client",
    "get_or_create_collection",
    "get_embedding_function",
    "get_single_embedding",
    "extract_text_from_pdf",
    "chunk_text",
    "process_pdf",
    "process_text_file",
]
