"""
Web Search Tool for Virtual Lab Agents

LangChain Tool wrapper for Tavily Search with citation formatting

Features:
- Academic/Government domain prioritization (.gov, nature.com, sciencedirect.com)
- Citation formatting with source URLs
- Error handling for API failures
- LangSmith observability (query tracing)
- Python logging for search history
- TODO: Redis caching for repeated queries
"""

import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from langchain_core.tools import tool
from search.tavily_client import TavilySearchClient

# Configure logging for search queries
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Create file handler for search logs (if not exists)
if not logger.handlers:
    log_file = os.path.join(os.path.dirname(__file__), "..", "search_queries.log")
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)


# Initialize Tavily client (singleton pattern)
_tavily_client = None


def get_tavily_client() -> TavilySearchClient:
    """
    Get or create Tavily client singleton

    Returns:
        TavilySearchClient instance
    """
    global _tavily_client

    if _tavily_client is None:
        api_key = os.environ.get("TAVILY_API_KEY")
        if not api_key:
            raise ValueError(
                "TAVILY_API_KEY required for web_search tool. "
                "Set environment variable TAVILY_API_KEY."
            )

        _tavily_client = TavilySearchClient(
            api_key=api_key,
            include_domains=[".gov", "nature.com", "sciencedirect.com"],
            max_results=5,
            search_depth="advanced"
        )

    return _tavily_client


def format_search_results(results: Dict[str, Any]) -> str:
    """
    Format Tavily search results with citations

    Args:
        results: Dict containing search results from Tavily API

    Returns:
        Formatted string with citations in format:
        "Title: ...\nContent: ...\n[출처: URL]\n\n"
    """
    if not results or 'results' not in results:
        return "검색 결과가 없습니다."

    formatted = []
    for item in results['results']:
        title = item.get('title', 'No Title')
        content = item.get('content', '')
        url = item.get('url', '')
        score = item.get('score', 0.0)

        # Format each result with citation
        result_text = f"**{title}**\n"
        result_text += f"{content}\n"
        result_text += f"[출처: {url}] (relevance: {score:.2f})\n"

        formatted.append(result_text)

    return "\n".join(formatted)


@tool
def web_search(query: str) -> str:
    """
    최신 논문 및 규제 동향 검색

    학술 논문 및 정부 규제 정보를 검색합니다.
    신뢰할 수 있는 도메인(.gov, nature.com, sciencedirect.com)에서 우선 검색됩니다.

    Args:
        query (str): 검색 쿼리 (예: "Calyxt high oleic soybean FDA approval")

    Returns:
        str: 포맷팅된 검색 결과 (제목, 내용, 출처 URL 포함)

    Examples:
        >>> result = web_search("NGT safety assessment framework")
        >>> print(result)
        **NGT Safety Framework**
        New genomic techniques require comprehensive safety assessment...
        [출처: https://www.nature.com/articles/...] (relevance: 0.95)

    Raises:
        ValueError: TAVILY_API_KEY가 설정되지 않은 경우
        RuntimeError: Tavily API 호출 실패 시
    """
    # Log search query (observability)
    logger.info(f"SEARCH_QUERY | query='{query}'")

    try:
        # Get Tavily client
        client = get_tavily_client()

        # Perform search (synchronous for LangChain tool compatibility)
        results = client.search_sync(query)

        # Format results with citations
        formatted = format_search_results(results)

        # Log success with result count
        result_count = len(results.get('results', [])) if results else 0
        logger.info(f"SEARCH_SUCCESS | query='{query}' | results={result_count}")

        return formatted

    except ValueError as e:
        # Configuration error (missing API key)
        logger.error(f"SEARCH_CONFIG_ERROR | query='{query}' | error='{str(e)}'")
        return f"설정 오류: {str(e)}"

    except RuntimeError as e:
        # API error
        logger.error(f"SEARCH_API_ERROR | query='{query}' | error='{str(e)}'")
        return f"검색 실패: {str(e)}"

    except Exception as e:
        # Unexpected error
        logger.error(f"SEARCH_UNEXPECTED_ERROR | query='{query}' | error='{str(e)}'")
        return f"예상치 못한 오류: {str(e)}"


# TODO: Redis Caching
# Implement query result caching to reduce API calls
# Example structure:
# ```python
# import redis
# cache = redis.Redis(host='localhost', port=6379, db=0)
#
# def cached_search(query: str) -> str:
#     cache_key = f"search:{query}"
#     cached = cache.get(cache_key)
#     if cached:
#         return cached.decode('utf-8')
#
#     result = web_search.invoke({"query": query})
#     cache.setex(cache_key, 3600, result)  # 1 hour TTL
#     return result
# ```

# Expose for testing (patch target)
tavily_client = get_tavily_client
