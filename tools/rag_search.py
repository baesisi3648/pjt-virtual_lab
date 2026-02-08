"""
RAG Search Tool for LangChain Integration

규제 문서 데이터베이스에서 관련 정보를 검색하는 LangChain Tool
"""
import logging
from langchain_core.tools import tool

from rag.retriever import retrieve
from rag.formatter import format_context

logger = logging.getLogger(__name__)


@tool
def rag_search_tool(query: str) -> str:
    """
    규제 문서 데이터베이스에서 관련 정보 검색

    Args:
        query: 검색 쿼리 (예: "대두 알레르기 평가 방법")

    Returns:
        관련 문서 컨텍스트와 출처
    """
    try:
        logger.info(f"RAG Search: {query}")
        docs = retrieve(query, top_k=3)

        if not docs:
            logger.warning("RAG Hit: 0 documents")
            return "관련 규제 문서를 찾을 수 없습니다."

        logger.info(f"RAG Hit: {len(docs)} documents")
        context = format_context(docs)
        return context

    except Exception as e:
        logger.error(f"RAG 검색 오류: {str(e)}")
        return f"RAG 검색 오류: {str(e)}"
