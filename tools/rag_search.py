"""
RAG Search Tool for LangChain Integration

규제 문서 데이터베이스에서 관련 정보를 검색하는 LangChain Tool
Pinecone 또는 ChromaDB 지원
"""
import logging
from langchain_core.tools import tool
from config import settings

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
        logger.info(f"RAG Search ({settings.VECTOR_DB_TYPE}): {query}")

        # Vector DB 선택
        if settings.VECTOR_DB_TYPE == "pinecone":
            from rag.pinecone_client import get_pinecone_client
            client = get_pinecone_client()
            docs = client.search(query, top_k=settings.TOP_K)

        else:  # chromadb
            from rag.retriever import retrieve
            docs = retrieve(query, top_k=settings.TOP_K)

        if not docs:
            logger.warning("RAG Hit: 0 documents")
            return "관련 규제 문서를 찾을 수 없습니다."

        logger.info(f"RAG Hit: {len(docs)} documents")

        # 결과 포맷팅
        result = []
        for i, doc in enumerate(docs, start=1):
            score = doc.get('score', 0)
            source = doc.get('source', 'unknown')
            page = doc.get('page', 0)
            text = doc.get('text', '')

            result.append(f"""
### 문서 {i} (유사도: {score:.2f})
**출처**: {source} (p.{page})

{text}
""")

        return "\n\n".join(result)

    except Exception as e:
        logger.error(f"RAG 검색 오류: {str(e)}")
        return f"RAG 검색 오류: {str(e)}"
