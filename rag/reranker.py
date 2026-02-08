"""
Reranker (Placeholder)

Cross-encoder 기반 문서 재순위화
"""

from typing import List, Dict


def rerank(query: str, documents: List[Dict], top_k: int = 5) -> List[Dict]:
    """
    Cross-encoder로 문서 재순위화

    Args:
        query: 검색 쿼리
        documents: 검색된 문서 리스트
        top_k: 반환할 문서 수

    Returns:
        재순위화된 문서 리스트

    Note:
        현재는 placeholder 구현입니다.
        향후 sentence-transformers cross-encoder 통합 예정.

    Example:
        >>> docs = [
        ...     {'text': 'doc1', 'metadata': {}, 'distance': 0.5},
        ...     {'text': 'doc2', 'metadata': {}, 'distance': 0.3}
        ... ]
        >>> result = rerank("query", docs, top_k=2)
        >>> assert len(result) == 2
    """
    # TODO: sentence-transformers cross-encoder 구현
    # from sentence_transformers import CrossEncoder
    # model = CrossEncoder('cross-encoder/ms-marco-MiniLM-L-6-v2')
    # pairs = [[query, doc['text']] for doc in documents]
    # scores = model.predict(pairs)
    # sorted_docs = [doc for _, doc in sorted(zip(scores, documents), reverse=True)]
    # return sorted_docs[:top_k]

    # Placeholder: 상위 top_k개 반환
    return documents[:top_k]
