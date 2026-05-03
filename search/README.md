# Tavily Search Client

Web search capabilities for Virtual Lab using Tavily API.

## Features

- Async and sync search interfaces
- Domain filtering for academic/government sources
- Rate limiting protection
- Comprehensive error handling

## Installation

1. Install dependencies:
```bash
pip install tavily-python
```

2. Set API key in `.env`:
```bash
TAVILY_API_KEY=tvly-your-api-key-here
```

Get your API key from: https://tavily.com/

## Usage

### Basic Usage

```python
from search import TavilySearchClient

# Initialize client (reads from environment)
client = TavilySearchClient()

# Async search
results = await client.search("CRISPR off-target effects 2025")

# Sync search
results = client.search_sync("NGT safety assessment")
```

### Custom Domain Filtering

```python
# Initialize with custom domains
client = TavilySearchClient(
    include_domains=[
        ".gov",
        "nature.com",
        "sciencedirect.com",
        "nih.gov"
    ]
)

# Or override per search
results = await client.search(
    query="gene editing regulations",
    include_domains=["fda.gov", "efsa.europa.eu"]
)
```

### Advanced Configuration

```python
client = TavilySearchClient(
    api_key="tvly-xxx",  # Optional: override env
    max_results=10,      # Default: 5
    search_depth="advanced"  # Default: "advanced"
)
```

## Testing

```bash
# Unit tests (no API key required)
pytest tests/test_tavily_client.py::TestTavilySearchClient -v

# Integration tests (requires API key)
TAVILY_API_KEY=tvly-xxx pytest tests/test_tavily_client.py::TestTavilySearchIntegration -v
```

## Rate Limiting

Client automatically applies rate limiting (1 second between requests) to prevent API throttling.

## Domain Filtering Defaults

By default, searches prioritize:
- `.gov` - Government sources
- `nature.com` - Nature journals
- `sciencedirect.com` - ScienceDirect database

This ensures high-quality academic and regulatory information for NGT safety research.
