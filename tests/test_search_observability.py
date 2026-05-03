"""
Tests for Search Observability (P2-T4)

Verifies:
1. Search queries are logged to file
2. Log format is correct
3. Success/Error states are tracked
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from tools.web_search import web_search


class TestSearchLogging:
    """Test search query logging functionality"""

    @pytest.fixture(autouse=True)
    def setup_log_file(self):
        """Setup: Create temporary log file path"""
        self.log_file = os.path.join(
            os.path.dirname(__file__),
            "..",
            "search_queries.log"
        )
        yield
        # Teardown: Remove log file after tests (optional)
        # if os.path.exists(self.log_file):
        #     os.remove(self.log_file)

    def test_search_query_logged(self, tmp_path):
        """RED -> GREEN: Search query is logged to file"""
        with patch("tools.web_search.get_tavily_client") as mock_client:
            # Mock successful search
            mock_instance = MagicMock()
            mock_instance.search_sync.return_value = {
                "results": [
                    {
                        "title": "Test Paper",
                        "content": "Test content",
                        "url": "https://test.com",
                        "score": 0.95
                    }
                ]
            }
            mock_client.return_value = mock_instance

            # Execute search
            query = "NGT safety assessment"
            result = web_search.invoke({"query": query})

            # Verify log file exists
            assert os.path.exists(self.log_file), "Log file should be created"

            # Verify log content
            with open(self.log_file, "r", encoding="utf-8") as f:
                log_content = f.read()
                assert query in log_content, "Query should be logged"
                assert "SEARCH_QUERY" in log_content, "Log should contain SEARCH_QUERY marker"

    def test_search_success_logged(self):
        """GREEN: Search success is logged with result count"""
        with patch("tools.web_search.get_tavily_client") as mock_client:
            # Mock successful search with 3 results
            mock_instance = MagicMock()
            mock_instance.search_sync.return_value = {
                "results": [{"title": f"Paper {i}"} for i in range(3)]
            }
            mock_client.return_value = mock_instance

            # Execute search
            query = "test query"
            result = web_search.invoke({"query": query})

            # Verify log contains success marker
            with open(self.log_file, "r", encoding="utf-8") as f:
                log_content = f.read()
                assert "SEARCH_SUCCESS" in log_content, "Success should be logged"
                assert "results=3" in log_content, "Result count should be logged"

    def test_search_error_logged(self):
        """GREEN: Search error is logged"""
        with patch("tools.web_search.get_tavily_client") as mock_client:
            # Mock API error
            mock_instance = MagicMock()
            mock_instance.search_sync.side_effect = RuntimeError("API Error")
            mock_client.return_value = mock_instance

            # Execute search
            query = "error query"
            result = web_search.invoke({"query": query})

            # Verify log contains error marker
            with open(self.log_file, "r", encoding="utf-8") as f:
                log_content = f.read()
                assert "SEARCH_API_ERROR" in log_content, "Error should be logged"
                assert "API Error" in log_content, "Error message should be logged"


class TestLogFormat:
    """Test log format and structure"""

    def test_log_format_structure(self):
        """GREEN: Log format follows timestamp | level | message"""
        with patch("tools.web_search.get_tavily_client") as mock_client:
            # Mock successful search
            mock_instance = MagicMock()
            mock_instance.search_sync.return_value = {"results": []}
            mock_client.return_value = mock_instance

            # Execute search
            query = "format test"
            result = web_search.invoke({"query": query})

            # Verify log format
            log_file = os.path.join(
                os.path.dirname(__file__),
                "..",
                "search_queries.log"
            )
            with open(log_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
                last_line = lines[-1] if lines else ""

                # Check format: YYYY-MM-DD HH:MM:SS | LEVEL | MESSAGE
                assert "|" in last_line, "Log should contain pipe delimiters"
                parts = last_line.split("|")
                assert len(parts) >= 3, "Log should have timestamp, level, message"


class TestLangSmithIntegration:
    """Test LangSmith tracing (if enabled)"""

    def test_langsmith_env_vars(self):
        """GREEN: LangSmith can be enabled via environment variables"""
        # Check if LangSmith env vars are documented
        env_example = os.path.join(
            os.path.dirname(__file__),
            "..",
            ".env.example"
        )

        with open(env_example, "r") as f:
            content = f.read()
            assert "LANGCHAIN_TRACING_V2" in content, "LangSmith tracing should be documented"
            assert "LANGCHAIN_API_KEY" in content, "LangSmith API key should be documented"
            assert "LANGCHAIN_PROJECT" in content, "LangSmith project should be documented"

    def test_langsmith_trace_decorator(self):
        """GREEN: web_search is a LangChain tool (auto-traced by LangSmith)"""
        # LangChain @tool decorator automatically enables LangSmith tracing
        # when LANGCHAIN_TRACING_V2=true is set
        from langchain_core.tools import BaseTool

        assert isinstance(web_search, BaseTool), "web_search should be a LangChain tool"
        assert web_search.name == "web_search", "Tool should have correct name"


class TestSearchObservabilityAcceptance:
    """Acceptance test for P2-T4"""

    def test_p2t4_acceptance(self):
        """
        ACCEPTANCE: Search queries are observable via logs

        Criteria:
        1. All search queries are logged with timestamp
        2. Success/Error states are tracked
        3. Log file is created automatically
        4. LangSmith integration is documented (even if not enabled)
        """
        with patch("tools.web_search.get_tavily_client") as mock_client:
            # Mock successful search
            mock_instance = MagicMock()
            mock_instance.search_sync.return_value = {
                "results": [
                    {
                        "title": "Acceptance Test",
                        "content": "Test content",
                        "url": "https://test.com",
                        "score": 0.95
                    }
                ]
            }
            mock_client.return_value = mock_instance

            # Execute search
            query = "P2-T4 acceptance test"
            result = web_search.invoke({"query": query})

            # Verify observability
            log_file = os.path.join(
                os.path.dirname(__file__),
                "..",
                "search_queries.log"
            )

            assert os.path.exists(log_file), "1. Log file should exist"

            with open(log_file, "r", encoding="utf-8") as f:
                log_content = f.read()
                assert query in log_content, "2. Query should be logged"
                assert "SEARCH_SUCCESS" in log_content, "3. Success state should be tracked"

            # Verify LangSmith documentation
            env_example = os.path.join(
                os.path.dirname(__file__),
                "..",
                ".env.example"
            )
            with open(env_example, "r") as f:
                content = f.read()
                assert "LANGCHAIN_TRACING_V2" in content, "4. LangSmith should be documented"

            print("[OK] P2-T4 Acceptance Criteria Met")
            print(f"[OK] Log file: {log_file}")
            print("[OK] Query logging: ENABLED")
            print("[OK] Success/Error tracking: ENABLED")
            print("[OK] LangSmith integration: DOCUMENTED")
