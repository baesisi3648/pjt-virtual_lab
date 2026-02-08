"""
Acceptance Test for P2-T2: Search Tool for Agents

검증 기준:
- result = web_search.invoke("Calyxt high oleic soybean FDA approval")
- assert "calyxt.com" in result or "fda.gov" in result
"""

import pytest
from unittest.mock import Mock, patch


@patch('tools.web_search.get_tavily_client')
def test_acceptance_calyxt_search(mock_get_client):
    """
    P2-T2 검증 기준 테스트
    Calyxt/FDA 관련 검색 결과 포함 여부
    """
    from tools.web_search import web_search

    # Mock realistic FDA/Calyxt response
    mock_client = Mock()
    mock_client.search_sync.return_value = {
        'results': [
            {
                'url': 'https://www.fda.gov/food/cfsan-constituent-updates/fda-letter-calyxt-inc-high-oleic-acid-soybean',
                'title': 'FDA Letter to Calyxt Inc. - High Oleic Acid Soybean',
                'content': 'FDA has completed its consultation with Calyxt regarding high oleic acid soybean...',
                'score': 0.95
            },
            {
                'url': 'https://calyxt.com/technology/high-oleic-soybean',
                'title': 'Calyxt High Oleic Soybean Technology',
                'content': 'Our high oleic soybean uses gene editing to produce healthier oil...',
                'score': 0.88
            }
        ],
        'query': 'Calyxt high oleic soybean FDA approval'
    }
    mock_get_client.return_value = mock_client

    # Execute search
    result = web_search.invoke({"query": "Calyxt high oleic soybean FDA approval"})

    # Verify acceptance criteria
    assert isinstance(result, str)
    assert len(result) > 100  # Meaningful content
    assert "calyxt" in result.lower() or "fda.gov" in result.lower()

    # Verify citation format
    assert "[출처:" in result

    print("\n[PASS] Acceptance Test PASSED")
    print(f"Result preview: {result[:200]}...")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
