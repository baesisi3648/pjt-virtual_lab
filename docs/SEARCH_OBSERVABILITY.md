# Search Observability Guide

## Overview
P2-T4 implements comprehensive observability for web search operations in the Virtual Lab MVP. All search queries are automatically logged with structured format for monitoring and debugging.

## Features

### 1. Automatic Query Logging
Every web search is logged to `search_queries.log`:
- Query text
- Timestamp
- Success/Error status
- Result count (for successful searches)
- Error details (for failures)

### 2. Structured Log Format
```
YYYY-MM-DD HH:MM:SS | LEVEL | EVENT_TYPE | details
```

**Example entries:**
```
2026-02-08 17:28:26 | INFO | SEARCH_QUERY | query='NGT safety assessment'
2026-02-08 17:28:26 | INFO | SEARCH_SUCCESS | query='NGT safety assessment' | results=1
2026-02-08 17:28:26 | ERROR | SEARCH_API_ERROR | query='error query' | error='API Error'
```

### 3. Event Types

#### SEARCH_QUERY
Logged when a search is initiated.
```
INFO | SEARCH_QUERY | query='your search text'
```

#### SEARCH_SUCCESS
Logged when a search completes successfully.
```
INFO | SEARCH_SUCCESS | query='your search text' | results=5
```

#### SEARCH_API_ERROR
Logged when the Tavily API fails.
```
ERROR | SEARCH_API_ERROR | query='your search text' | error='API Error'
```

#### SEARCH_CONFIG_ERROR
Logged when configuration is invalid (e.g., missing API key).
```
ERROR | SEARCH_CONFIG_ERROR | query='your search text' | error='TAVILY_API_KEY required'
```

## Usage

### View Logs

**Last 20 entries:**
```bash
tail -20 search_queries.log
```

**Follow in real-time:**
```bash
tail -f search_queries.log
```

**Filter errors:**
```bash
grep "ERROR" search_queries.log
```

**Count queries:**
```bash
grep "SEARCH_QUERY" search_queries.log | wc -l
```

### Example Session
```bash
$ tail -10 search_queries.log
2026-02-08 17:28:26 | INFO | SEARCH_QUERY | query='NGT safety assessment'
2026-02-08 17:28:26 | INFO | SEARCH_SUCCESS | query='NGT safety assessment' | results=1
2026-02-08 17:28:26 | INFO | SEARCH_QUERY | query='test query'
2026-02-08 17:28:26 | INFO | SEARCH_SUCCESS | query='test query' | results=3

$ grep "SEARCH_QUERY" search_queries.log | wc -l
30
$ grep "SEARCH_SUCCESS" search_queries.log | wc -l
25
$ grep "ERROR" search_queries.log | wc -l
5
```

## LangSmith Integration (Optional)

### Enable Tracing
1. Create a LangSmith account at https://smith.langchain.com/
2. Get your API key
3. Add to `.env`:
   ```bash
   LANGCHAIN_TRACING_V2=true
   LANGCHAIN_API_KEY=ls-your-api-key-here
   LANGCHAIN_PROJECT=virtual-lab-mvp
   ```

### Benefits
- Visual trace of LLM calls
- Tool invocation timeline
- Token usage tracking
- Latency analysis

### Auto-Tracing
The `@tool` decorator from LangChain automatically enables LangSmith tracing when `LANGCHAIN_TRACING_V2=true` is set. No code changes needed.

## Demo

Run the observability demo:
```bash
python demo_search_observability.py
```

Output:
```
=== Search Observability Demo ===

Query: NGT safety assessment framework

Search Result:
**EFSA NGT Guidelines 2024**
New genomic techniques require comprehensive safety assessment...
[Source: https://www.efsa.europa.eu/ngt-2024] (relevance: 0.95)

[OK] Log file created: search_queries.log

Recent log entries:
  2026-02-08 17:30:27 | INFO | SEARCH_QUERY | query='NGT safety assessment framework'
  2026-02-08 17:30:27 | INFO | SEARCH_SUCCESS | query='NGT safety assessment framework' | results=2

=== Demo Complete ===
[OK] Search queries are logged
[OK] Log format is structured
[OK] LangSmith integration is documented
```

## Testing

Run observability tests:
```bash
pytest tests/test_search_observability.py -v
```

All 7 tests pass:
- Query logging
- Success tracking
- Error tracking
- Log format validation
- LangSmith configuration
- Acceptance criteria

## Log Statistics (Current Session)
- Total log entries: 60
- Search queries: 30
- Successful searches: 25
- Errors: 5

## Future Improvements

### Database Storage
Store logs in PostgreSQL for:
- Advanced querying
- Analytics dashboards
- Long-term retention

### Redis Caching
Cache search results to:
- Reduce API calls
- Improve response time
- Lower costs

### Analytics Dashboard
Build Streamlit dashboard to show:
- Query trends
- Success rate
- Common errors
- Popular search terms

## Files

### Implementation
- `tools/web_search.py` - Logging implementation
- `search_queries.log` - Auto-generated log file

### Tests
- `tests/test_search_observability.py` - 7 tests
- `demo_search_observability.py` - Interactive demo

### Documentation
- `P2-T4-COMPLETION-REPORT.md` - Detailed completion report
- `SEARCH_OBSERVABILITY.md` - This file

## Support

For issues or questions:
1. Check `search_queries.log` for errors
2. Verify `TAVILY_API_KEY` is set in `.env`
3. Run `python demo_search_observability.py` to test
4. Review `P2-T4-COMPLETION-REPORT.md`

---

**Last Updated**: 2026-02-08
**Task**: P2-T4 (Search Observability)
**Status**: COMPLETED
