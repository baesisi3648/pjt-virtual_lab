"""
Tavily Search Client for Virtual Lab
Provides web search capabilities with domain filtering and rate limiting
"""

import os
import asyncio
from typing import Dict, List, Optional, Any
from tavily import TavilyClient


class TavilySearchClient:
    """
    Tavily API Client with domain filtering and rate limiting.

    Features:
    - Async search interface
    - Domain filtering for academic/government sources
    - Rate limiting protection
    - Error handling
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        include_domains: Optional[List[str]] = None,
        max_results: int = 5,
        search_depth: str = "advanced"
    ):
        """
        Initialize Tavily Search Client

        Args:
            api_key: Tavily API key (defaults to env TAVILY_API_KEY)
            include_domains: List of domains to prioritize
            max_results: Maximum number of results to return
            search_depth: "basic" or "advanced"

        Raises:
            ValueError: If API key is not provided
        """
        # Get API key from parameter or environment
        self.api_key = api_key or os.environ.get("TAVILY_API_KEY")

        if not self.api_key:
            raise ValueError(
                "TAVILY_API_KEY required. "
                "Set via environment variable or constructor parameter."
            )

        # Initialize Tavily client
        self.client = TavilyClient(api_key=self.api_key)

        # Set domain filtering
        # Default: academic and government sources
        self.include_domains = include_domains or [
            ".gov",
            "nature.com",
            "sciencedirect.com"
        ]

        self.max_results = max_results
        self.search_depth = search_depth

        # Rate limiting
        self._last_request_time = 0
        self._min_request_interval = 1.0  # seconds between requests

    async def search(
        self,
        query: str,
        max_results: Optional[int] = None,
        include_domains: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Perform async search with domain filtering

        Args:
            query: Search query string
            max_results: Override default max_results
            include_domains: Override default include_domains

        Returns:
            Dict containing search results:
            {
                'results': [
                    {
                        'url': str,
                        'title': str,
                        'content': str,
                        'score': float
                    },
                    ...
                ],
                'query': str
            }
        """
        # Rate limiting
        await self._apply_rate_limit()

        # Use provided parameters or defaults
        _max_results = max_results or self.max_results
        _include_domains = include_domains or self.include_domains

        try:
            # Tavily client.search is synchronous, run in executor
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                lambda: self.client.search(
                    query=query,
                    max_results=_max_results,
                    search_depth=self.search_depth,
                    include_domains=_include_domains
                )
            )

            return results

        except Exception as e:
            # Handle API errors gracefully
            raise RuntimeError(f"Tavily search failed: {str(e)}") from e

    async def _apply_rate_limit(self):
        """Apply rate limiting between requests"""
        current_time = asyncio.get_event_loop().time()
        time_since_last_request = current_time - self._last_request_time

        if time_since_last_request < self._min_request_interval:
            wait_time = self._min_request_interval - time_since_last_request
            await asyncio.sleep(wait_time)

        self._last_request_time = asyncio.get_event_loop().time()

    def search_sync(
        self,
        query: str,
        max_results: Optional[int] = None,
        include_domains: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Synchronous version of search (for backwards compatibility)

        Args:
            query: Search query string
            max_results: Override default max_results
            include_domains: Override default include_domains

        Returns:
            Dict containing search results
        """
        _max_results = max_results or self.max_results
        _include_domains = include_domains or self.include_domains

        try:
            results = self.client.search(
                query=query,
                max_results=_max_results,
                search_depth=self.search_depth,
                include_domains=_include_domains
            )
            return results

        except Exception as e:
            raise RuntimeError(f"Tavily search failed: {str(e)}") from e
