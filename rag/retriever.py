"""
RAG Retriever

쿼리 → 관련 문서 검색
"""

from typing import List, Dict, Optional

from .chroma_client import get_chroma_client, get_or_create_collection
from .embeddings import get_single_embedding


def retrieve(
    query: str,
    top_k: int = 5,
    filter: Optional[Dict] = None
) -> List[Dict]:
    """
    쿼리에 대한 관련 문서 검색

    Args:
        query: 검색 쿼리
        top_k: 반환할 문서 수
        filter: 메타데이터 필터 (예: {"source": "Codex"})

    Returns:
        List of documents with metadata and distance

    Example:
        >>> docs = retrieve("What is substantial equivalence?", top_k=5)
        >>> assert len(docs) == 5
        >>> assert "Codex" in docs[0]['metadata']['source']
    """
    # 1. 쿼리 임베딩 생성
    query_embedding = get_single_embedding(query)

    # 2. ChromaDB에서 검색
    client = get_chroma_client()
    collection = get_or_create_collection(client)

    # 3. 쿼리 실행
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where=filter  # 메타데이터 필터링
    )

    # 4. 결과 포맷팅
    documents = []
    if results['documents'][0]:  # 결과가 있을 경우
        for i in range(len(results['documents'][0])):
            documents.append({
                'text': results['documents'][0][i],
                'metadata': results['metadatas'][0][i],
                'distance': results['distances'][0][i]
            })

    return documents
