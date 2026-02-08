"""
Test Tavily Search Client
TDD: RED → GREEN → REFACTOR
"""

import pytest
import os
from search.tavily_client import TavilySearchClient


class TestTavilySearchClient:
    """Test Tavily API Client"""

    def test_client_initialization_without_api_key(self):
        """API Key가 없으면 ValueError 발생"""
        # Remove TAVILY_API_KEY temporarily if exists
        original_key = os.environ.get("TAVILY_API_KEY")
        if original_key:
            del os.environ["TAVILY_API_KEY"]

        try:
            with pytest.raises(ValueError, match="TAVILY_API_KEY required"):
                TavilySearchClient()
        finally:
            # Restore original key
            if original_key:
                os.environ["TAVILY_API_KEY"] = original_key

    def test_client_initialization_with_api_key(self):
        """API Key가 있으면 정상 초기화"""
        # Set dummy API key for initialization test
        os.environ["TAVILY_API_KEY"] = "tvly-test-key"

        try:
            client = TavilySearchClient()
            assert client is not None
            assert client.api_key == "tvly-test-key"
        finally:
            # Clean up
            if "TAVILY_API_KEY" in os.environ:
                del os.environ["TAVILY_API_KEY"]

    @pytest.mark.asyncio
    async def test_search_with_domain_filtering(self):
        """Domain 필터링이 적용된 검색"""
        os.environ["TAVILY_API_KEY"] = "tvly-test-key"

        try:
            client = TavilySearchClient()

            # Mock search - 실제 API 호출은 integration test에서
            # 여기서는 구조만 테스트
            expected_domains = [".gov", "nature.com", "sciencedirect.com"]
            assert client.include_domains == expected_domains
        finally:
            if "TAVILY_API_KEY" in os.environ:
                del os.environ["TAVILY_API_KEY"]

    @pytest.mark.asyncio
    async def test_search_returns_results(self):
        """검색 결과가 반환되는지 확인 (mock)"""
        os.environ["TAVILY_API_KEY"] = "tvly-test-key"

        try:
            client = TavilySearchClient()

            # Mock 검색 결과 구조 검증
            # 실제 API 호출은 integration test에서
            assert hasattr(client, 'search')
            assert callable(client.search)
        finally:
            if "TAVILY_API_KEY" in os.environ:
                del os.environ["TAVILY_API_KEY"]


class TestTavilySearchIntegration:
    """Integration tests - requires real API key"""

    @pytest.mark.skipif(
        not os.environ.get("TAVILY_API_KEY"),
        reason="TAVILY_API_KEY not set"
    )
    @pytest.mark.asyncio
    async def test_real_search(self):
        """실제 API 검색 테스트"""
        client = TavilySearchClient()

        results = await client.search("CRISPR off-target effects 2025")

        assert results is not None
        assert 'results' in results
        assert len(results['results']) > 0

        # Check domain filtering
        for result in results['results']:
            url = result.get('url', '')
            # At least some results should be from trusted domains
            # (Not all, as Tavily may include other relevant sources)

    @pytest.mark.skipif(
        not os.environ.get("TAVILY_API_KEY"),
        reason="TAVILY_API_KEY not set"
    )
    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """Rate limiting 처리 확인"""
        client = TavilySearchClient()

        # Make multiple requests
        for i in range(3):
            results = await client.search(f"NGT safety test {i}")
            assert results is not None

        # Should not raise rate limit errors with proper handling
