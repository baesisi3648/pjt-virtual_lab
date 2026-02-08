"""
Tests for LangChain web_search Tool

TDD RED Phase: 테스트 먼저 작성
"""

import pytest
from unittest.mock import Mock, patch


def test_web_search_tool_import():
    """web_search tool이 올바르게 임포트되는지 확인"""
    from tools.web_search import web_search

    assert web_search is not None
    # LangChain Tool은 StructuredTool 객체 (invoke 메서드 보유)
    assert hasattr(web_search, 'invoke')


def test_web_search_tool_is_langchain_tool():
    """web_search가 LangChain Tool로 래핑되었는지 확인"""
    from tools.web_search import web_search

    # LangChain Tool은 name, description 속성을 가짐
    assert hasattr(web_search, 'name')
    assert hasattr(web_search, 'description')
    assert web_search.name == "web_search"


@patch('tools.web_search.get_tavily_client')
def test_web_search_basic_invoke(mock_get_client):
    """web_search.invoke() 기본 호출 테스트"""
    from tools.web_search import web_search

    # Mock Tavily client and response
    mock_client = Mock()
    mock_client.search_sync.return_value = {
        'results': [
            {
                'url': 'https://www.fda.gov/food/calyxt-soybean',
                'title': 'Calyxt High Oleic Soybean FDA Approval',
                'content': 'FDA approves Calyxt high oleic soybean...',
                'score': 0.95
            }
        ],
        'query': 'Calyxt high oleic soybean FDA approval'
    }
    mock_get_client.return_value = mock_client

    # Invoke tool
    result = web_search.invoke({"query": "Calyxt high oleic soybean FDA approval"})

    assert isinstance(result, str)
    assert "fda.gov" in result.lower() or "calyxt" in result.lower()


@patch('tools.web_search.get_tavily_client')
def test_web_search_citation_format(mock_get_client):
    """검색 결과에 Citation이 포함되는지 확인"""
    from tools.web_search import web_search

    mock_client = Mock()
    mock_client.search_sync.return_value = {
        'results': [
            {
                'url': 'https://www.nature.com/articles/ngt-safety',
                'title': 'NGT Safety Framework',
                'content': 'New genomic techniques safety assessment...',
                'score': 0.9
            }
        ],
        'query': 'NGT safety'
    }
    mock_get_client.return_value = mock_client

    result = web_search.invoke({"query": "NGT safety"})

    # Citation 형식: [출처: URL]
    assert "[출처:" in result or "[Source:" in result
    assert "nature.com" in result


@patch('tools.web_search.get_tavily_client')
def test_web_search_multiple_results(mock_get_client):
    """여러 검색 결과가 포맷팅되는지 확인"""
    from tools.web_search import web_search

    mock_client = Mock()
    mock_client.search_sync.return_value = {
        'results': [
            {
                'url': 'https://www.fda.gov/ngt-1',
                'title': 'NGT Regulation 1',
                'content': 'Content 1',
                'score': 0.95
            },
            {
                'url': 'https://www.nature.com/ngt-2',
                'title': 'NGT Research 2',
                'content': 'Content 2',
                'score': 0.85
            }
        ],
        'query': 'NGT'
    }
    mock_get_client.return_value = mock_client

    result = web_search.invoke({"query": "NGT"})

    # 두 결과 모두 포함되어야 함
    assert "fda.gov" in result
    assert "nature.com" in result


@patch('tools.web_search.get_tavily_client')
def test_web_search_error_handling(mock_get_client):
    """Tavily API 에러 처리 테스트"""
    from tools.web_search import web_search

    mock_client = Mock()
    mock_client.search_sync.side_effect = RuntimeError("API Error")
    mock_get_client.return_value = mock_client

    # 에러가 발생해도 예외가 전파되거나 안전하게 처리되어야 함
    result = web_search.invoke({"query": "test query"})

    # 에러 메시지가 포함되거나, 빈 결과를 반환해야 함
    assert isinstance(result, str)
    assert len(result) > 0  # 적어도 에러 메시지는 있어야 함


def test_web_search_integration():
    """
    실제 Tavily API 호출 통합 테스트 (TAVILY_API_KEY 필요)
    환경 변수가 없으면 skip
    """
    import os

    if not os.environ.get("TAVILY_API_KEY"):
        pytest.skip("TAVILY_API_KEY not set")

    from tools.web_search import web_search

    # 실제 검색 수행
    result = web_search.invoke({"query": "Calyxt high oleic soybean FDA approval"})

    # 검증
    assert isinstance(result, str)
    assert len(result) > 50  # 의미 있는 결과
    assert ("calyxt" in result.lower() or "fda" in result.lower())
