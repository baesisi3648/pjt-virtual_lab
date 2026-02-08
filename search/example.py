"""
Example usage of TavilySearchClient
Run with: python -m search.example
"""

import asyncio
import os
from dotenv import load_dotenv
from search import TavilySearchClient


async def main():
    """Demonstrate Tavily Search Client usage"""

    # Load environment variables
    load_dotenv()

    # Check if API key is set
    if not os.environ.get("TAVILY_API_KEY"):
        print("Error: TAVILY_API_KEY not set in .env file")
        print("Get your API key from: https://tavily.com/")
        return

    # Initialize client
    print("Initializing Tavily Search Client...")
    client = TavilySearchClient()
    print(f"✓ Client initialized with domains: {client.include_domains}\n")

    # Example 1: Basic search
    print("Example 1: Basic Search")
    print("-" * 50)
    query = "CRISPR off-target effects 2025"
    print(f"Query: {query}")

    try:
        results = await client.search(query)
        print(f"Found {len(results['results'])} results:\n")

        for i, result in enumerate(results['results'][:3], 1):
            print(f"{i}. {result['title']}")
            print(f"   URL: {result['url']}")
            print(f"   Preview: {result['content'][:100]}...")
            print()

    except Exception as e:
        print(f"Search failed: {e}")

    # Example 2: Custom domain filtering
    print("\nExample 2: Custom Domain Filtering")
    print("-" * 50)
    query = "NGT safety regulations Europe"
    custom_domains = ["efsa.europa.eu", "ec.europa.eu", ".gov"]
    print(f"Query: {query}")
    print(f"Domains: {custom_domains}")

    try:
        results = await client.search(
            query=query,
            include_domains=custom_domains,
            max_results=3
        )
        print(f"Found {len(results['results'])} results:\n")

        for i, result in enumerate(results['results'], 1):
            print(f"{i}. {result['title']}")
            print(f"   URL: {result['url']}")
            print()

    except Exception as e:
        print(f"Search failed: {e}")

    # Example 3: Rate limiting demonstration
    print("\nExample 3: Multiple Searches (Rate Limiting)")
    print("-" * 50)
    queries = [
        "gene editing safety assessment",
        "CRISPR cas9 unintended effects",
        "NGT risk evaluation framework"
    ]

    for i, query in enumerate(queries, 1):
        print(f"{i}. Searching: {query}")
        try:
            results = await client.search(query, max_results=2)
            print(f"   ✓ Found {len(results['results'])} results")
        except Exception as e:
            print(f"   ✗ Failed: {e}")

    print("\n✓ All searches completed with rate limiting")


if __name__ == "__main__":
    asyncio.run(main())
