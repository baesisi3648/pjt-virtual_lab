"""
Demo: Search Observability (P2-T4)

Demonstrates:
1. Search query logging
2. Log file creation
3. Structured log format
"""

import os
from unittest.mock import patch, MagicMock
from tools.web_search import web_search


def demo_search_logging():
    """Demo search query logging functionality"""
    print("=== Search Observability Demo ===\n")

    # Mock Tavily client (no actual API calls)
    with patch("tools.web_search.get_tavily_client") as mock_client:
        # Setup mock
        mock_instance = MagicMock()
        mock_instance.search_sync.return_value = {
            "results": [
                {
                    "title": "EFSA NGT Guidelines 2024",
                    "content": "New genomic techniques require comprehensive safety assessment...",
                    "url": "https://www.efsa.europa.eu/ngt-2024",
                    "score": 0.95
                },
                {
                    "title": "FDA Gene Editing Policy",
                    "content": "FDA maintains product-based regulation for gene-edited foods...",
                    "url": "https://www.fda.gov/gene-editing",
                    "score": 0.88
                }
            ]
        }
        mock_client.return_value = mock_instance

        # Execute search
        query = "NGT safety assessment framework"
        print(f"Query: {query}\n")

        result = web_search.invoke({"query": query})
        print("Search Result:")
        print(result)
        print()

    # Check log file
    log_file = os.path.join(
        os.path.dirname(__file__),
        "search_queries.log"
    )

    if os.path.exists(log_file):
        print(f"[OK] Log file created: {log_file}\n")
        print("Recent log entries:")
        with open(log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()
            for line in lines[-5:]:
                print(f"  {line.rstrip()}")
    else:
        print("[FAIL] Log file not found")


def demo_langsmith_config():
    """Demo LangSmith configuration"""
    print("\n=== LangSmith Configuration ===\n")

    env_example = os.path.join(
        os.path.dirname(__file__),
        ".env.example"
    )

    print("LangSmith tracing can be enabled via environment variables:")
    print()

    with open(env_example, "r") as f:
        lines = f.readlines()
        in_langsmith_section = False
        for line in lines:
            if "LangSmith" in line:
                in_langsmith_section = True
            if in_langsmith_section:
                print(f"  {line.rstrip()}")
                if line.strip() == "":
                    break

    print("\nTo enable LangSmith:")
    print("1. Set LANGCHAIN_TRACING_V2=true in .env")
    print("2. Add your LangSmith API key")
    print("3. Visit https://smith.langchain.com/ to view traces")


def demo_log_format():
    """Demo log format structure"""
    print("\n=== Log Format ===\n")

    with patch("tools.web_search.get_tavily_client") as mock_client:
        # Mock successful search
        mock_instance = MagicMock()
        mock_instance.search_sync.return_value = {"results": []}
        mock_client.return_value = mock_instance

        web_search.invoke({"query": "format demo"})

    log_file = os.path.join(
        os.path.dirname(__file__),
        "search_queries.log"
    )

    with open(log_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
        if lines:
            sample = lines[-1].rstrip()
            parts = sample.split("|")

            print("Log Structure:")
            print(f"  Timestamp: {parts[0].strip()}")
            print(f"  Level:     {parts[1].strip()}")
            print(f"  Message:   {parts[2].strip()}")
            print()
            print(f"Full line:\n  {sample}")


if __name__ == "__main__":
    demo_search_logging()
    demo_langsmith_config()
    demo_log_format()

    print("\n=== Demo Complete ===")
    print("[OK] Search queries are logged")
    print("[OK] Log format is structured")
    print("[OK] LangSmith integration is documented")
