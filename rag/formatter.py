"""
Citation Formatter

검색된 문서를 Citation 포맷으로 변환
"""

from typing import Dict, List


def format_citation(document: Dict) -> str:
    """
    문서를 [출처: ...] 형식으로 포맷팅

    Args:
        document: 검색된 문서 (text, metadata, distance)

    Returns:
        Citation 문자열

    Example:
        >>> doc = {
        ...     'text': 'Sample text',
        ...     'metadata': {'source': 'Codex', 'year': 2023, 'page': 5},
        ...     'distance': 0.1
        ... }
        >>> citation = format_citation(doc)
        >>> assert citation == "[출처: Codex (2023), p.5]"
    """
    metadata = document['metadata']
    source = metadata.get('source', 'Unknown')
    year = metadata.get('year', 'N/A')
    page = metadata.get('page', '')

    if page:
        return f"[출처: {source} ({year}), p.{page}]"
    else:
        return f"[출처: {source} ({year})]"


def format_context(documents: List[Dict]) -> str:
    """
    검색된 문서들을 컨텍스트로 병합

    Args:
        documents: 검색된 문서 리스트

    Returns:
        병합된 컨텍스트 문자열

    Example:
        >>> docs = [
        ...     {
        ...         'text': 'First document.',
        ...         'metadata': {'source': 'Codex', 'year': 2023, 'page': 1},
        ...         'distance': 0.1
        ...     }
        ... ]
        >>> context = format_context(docs)
        >>> assert 'First document.' in context
        >>> assert '[출처: Codex (2023), p.1]' in context
    """
    if not documents:
        return ""

    context = ""
    for doc in documents:
        citation = format_citation(doc)
        context += f"{doc['text']}\n{citation}\n\n"

    return context
