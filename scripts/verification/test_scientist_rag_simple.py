"""
Scientist + RAG 통합 간단 검증

Circular import를 피하기 위해 scientist.py를 직접 실행하여 검증합니다.
"""
import sys
import os
from unittest.mock import patch, MagicMock

# Mock dependencies before importing
sys.path.insert(0, os.path.dirname(__file__))

# Mock RAG documents
MOCK_DOCS = [
    {
        'text': '알레르기 평가는 아미노산 서열 유사성 분석 및 in vitro 소화성 시험을 포함해야 한다.',
        'metadata': {'source': 'Codex Guideline CAC/GL 45-2003', 'year': 2003, 'page': 12},
        'distance': 0.05
    },
    {
        'text': 'Off-target 효과는 전장 유전체 시퀀싱(WGS)을 통해 검증되어야 한다.',
        'metadata': {'source': 'EFSA Scientific Opinion', 'year': 2023, 'page': 8},
        'distance': 0.08
    }
]

print("=" * 80)
print("Testing Scientist + RAG Integration")
print("=" * 80)

# Patch RAG before importing
with patch('rag.retriever.retrieve') as mock_retrieve:
    mock_retrieve.return_value = MOCK_DOCS

    # Import scientist (will fail due to circular import in workflow)
    # So let's test RAG tool directly first
    print("\n[TEST 1] RAG Tool Unit Test")
    from tools.rag_search import rag_search_tool

    result = rag_search_tool.invoke({"query": "알레르기 평가 방법"})
    print(f"Tool result preview: {result[:200]}...")

    assert "[출처: Codex Guideline" in result
    print("[OK] RAG Tool works correctly")

    # Test scientist function directly by copying its logic
    print("\n[TEST 2] Scientist Logic Test (Manual)")
    print("Note: Cannot import due to circular dependency")
    print("      Verifying that RAG tool is properly defined and accessible")

    from langchain_core.messages import SystemMessage, HumanMessage
    from utils.llm import get_gpt4o_mini

    # Test tool binding
    model = get_gpt4o_mini()
    model_with_tools = model.bind_tools([rag_search_tool])

    print(f"[OK] Model successfully bound with RAG tool")
    print(f"   Tool name: {rag_search_tool.name}")
    print(f"   Tool description: {rag_search_tool.description[:100]}...")

print("\n" + "=" * 80)
print("VERIFICATION COMPLETE")
print("=" * 80)
print("""
SUMMARY:
1. [OK] RAG Tool (rag_search_tool) created successfully
2. [OK] Tool can retrieve and format documents with citations
3. [OK] Tool can be bound to LLM using .bind_tools()
4. [WARN]  Scientist integration cannot be tested due to circular import
5. [INFO]  Scientist code has been updated to use RAG tool

Next Steps:
- Scientist will use RAG tool when called in production
- Tool will be invoked if LLM decides to use it
- Citations will be included in responses

Manual verification needed:
- Run workflow end-to-end test
- Or test via server API
""")
