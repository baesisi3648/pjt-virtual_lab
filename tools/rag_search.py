"""
RAG Search Tool for LangChain Integration

규제 문서 데이터베이스에서 관련 정보를 검색하는 LangChain Tool
Pinecone 또는 ChromaDB 지원
"""
import logging
from langchain_core.tools import tool
from config import settings
from utils.errors import SearchError

logger = logging.getLogger(__name__)


def format_docs(docs: list) -> str:
    """Text injected into the agents for RAG results (also used by the snapshot builder)."""
    result = []
    for i, doc in enumerate(docs, start=1):
        score = doc.get('score', 0)
        source = doc.get('source', 'unknown')
        page = doc.get('page', 0)
        if isinstance(page, float) and page.is_integer():
            page = int(page)  # Pinecone returns numeric metadata as float ("p.12.0")
        text = doc.get('text', '')
        # Revision (corpus v1): XML documents carry a section label, not a page number.
        loc = f"p.{page}" if isinstance(page, (int, float)) or str(page).replace(".", "", 1).isdigit() else str(page)
        result.append(f"""
### 문서 {i} (유사도: {score:.2f})
**출처**: {source} ({loc})

{text}
""")
    return "\n\n".join(result)


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
            # C12 (revision): an empty result is injected as nothing, not as a message.
            return ""

        logger.info(f"RAG Hit: {len(docs)} documents")

        return format_docs(docs)

    except Exception as e:
        logger.error(f"RAG 검색 오류: {str(e)}")
        raise SearchError(f"rag_search error: {e}") from e
