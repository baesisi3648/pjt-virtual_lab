"""
Retriever 검증 스크립트

실제 ChromaDB 연동 테스트
"""

import os
import sys

# Config를 먼저 로드하여 환경 검증
from config import settings

print("=" * 60)
print("RAG Retriever Verification")
print("=" * 60)

# 1. 환경 변수 확인
print("\n[1] Environment Variables")
print(f"  OPENAI_API_KEY: {'OK' if settings.OPENAI_API_KEY else 'Missing'}")
print(f"  CHROMA_HOST: {settings.CHROMA_HOST}")
print(f"  CHROMA_PORT: {settings.CHROMA_PORT}")

if not settings.OPENAI_API_KEY:
    print("\n  WARNING: OPENAI_API_KEY is not set.")
    print("  Real search will be replaced with Mock tests.")

# 2. ChromaDB 연결 확인
print("\n[2] ChromaDB Connection Test")
try:
    from rag.chroma_client import get_chroma_client, get_or_create_collection

    client = get_chroma_client()
    collection = get_or_create_collection(client)
    count = collection.count()

    print(f"  OK: ChromaDB connected")
    print(f"  OK: Collection: {collection.name}")
    print(f"  OK: Document count: {count}")

    if count == 0:
        print("\n  INFO: Collection is empty.")
        print("  To test real search, add documents first.")
        print("  Command: python -m rag.cli add-pdf <path_to_pdf>")
        chromadb_available = False
    else:
        chromadb_available = True

except Exception as e:
    print(f"  FAIL: ChromaDB connection failed: {e}")
    print("\n  INFO: ChromaDB is not running.")
    print("  Command: docker-compose up -d chromadb")
    chromadb_available = False

# 3. Mock 검색 테스트
print("\n[3] Mock Search Test")
from unittest.mock import Mock, patch
from rag.retriever import retrieve

with patch('rag.retriever.get_chroma_client'), \
     patch('rag.retriever.get_or_create_collection') as mock_coll, \
     patch('rag.retriever.get_single_embedding') as mock_embed:

    # Mock 설정
    mock_embed.return_value = [0.1] * 1536
    mock_coll_instance = Mock()
    mock_coll.return_value = mock_coll_instance

    mock_coll_instance.query.return_value = {
        'documents': [[
            'Substantial equivalence is a key concept in food safety assessment.',
            'Risk assessment framework requires comprehensive evaluation.',
            'Safety evaluation procedures include toxicological studies.'
        ]],
        'metadatas': [[
            {'source': 'Codex', 'year': 2023, 'page': 5},
            {'source': 'FDA', 'year': 2022, 'page': 12},
            {'source': 'EFSA', 'year': 2021, 'page': 8}
        ]],
        'distances': [[0.12, 0.25, 0.38]]
    }

    # 검색 실행
    docs = retrieve("What is substantial equivalence?", top_k=3)

    print(f"  OK: Search executed successfully")
    print(f"  OK: Retrieved documents: {len(docs)}")
    print(f"\n  Search Results:")
    for i, doc in enumerate(docs, 1):
        print(f"\n    [{i}] Distance: {doc['distance']:.3f}")
        print(f"        Source: {doc['metadata']['source']} ({doc['metadata']['year']})")
        print(f"        Text: {doc['text'][:60]}...")

# 4. Citation 포맷팅 테스트
print("\n[4] Citation Formatting Test")
from rag.formatter import format_citation, format_context

sample_doc = {
    'text': 'Substantial equivalence is a key concept in food safety.',
    'metadata': {'source': 'Codex', 'year': 2023, 'page': 5},
    'distance': 0.12
}

citation = format_citation(sample_doc)
print(f"  OK: Citation: {citation}")

context = format_context([sample_doc])
print(f"  OK: Context length: {len(context)} characters")
print(f"\n  Context preview:")
print(f"    {context[:100]}...")

# 5. Reranker 테스트
print("\n[5] Reranker Test (Placeholder)")
from rag.reranker import rerank

sample_docs = [
    {'text': 'doc1', 'metadata': {'source': 'A'}, 'distance': 0.5},
    {'text': 'doc2', 'metadata': {'source': 'B'}, 'distance': 0.3},
    {'text': 'doc3', 'metadata': {'source': 'C'}, 'distance': 0.1}
]

reranked = rerank("query", sample_docs, top_k=2)
print(f"  OK: Rerank executed successfully")
print(f"  OK: Returned documents: {len(reranked)}")
print(f"  INFO: Placeholder implementation - order not changed.")

# 6. 실제 검색 테스트 (ChromaDB 사용 가능 시)
if chromadb_available and settings.OPENAI_API_KEY:
    print("\n[6] Real Search Test")
    try:
        # 실제 검색 실행
        real_docs = retrieve("safety assessment", top_k=3)

        print(f"  OK: Real search succeeded")
        print(f"  OK: Retrieved documents: {len(real_docs)}")

        if real_docs:
            print(f"\n  Search Results:")
            for i, doc in enumerate(real_docs, 1):
                print(f"\n    [{i}] Distance: {doc['distance']:.3f}")
                print(f"        Source: {doc['metadata']['source']}")
                print(f"        Text: {doc['text'][:80]}...")

            # Citation 생성
            print(f"\n  Citation Examples:")
            for doc in real_docs[:2]:
                print(f"    {format_citation(doc)}")

            # 컨텍스트 생성
            context = format_context(real_docs)
            print(f"\n  OK: Total context length: {len(context)} characters")

    except Exception as e:
        print(f"  FAIL: Real search failed: {e}")

else:
    print("\n[6] Real Search Test - Skipped")
    if not chromadb_available:
        print("  INFO: ChromaDB is not available.")
    if not settings.OPENAI_API_KEY:
        print("  INFO: OPENAI_API_KEY is not set.")

# 최종 요약
print("\n" + "=" * 60)
print("Verification Complete")
print("=" * 60)
print("\nGenerated Files:")
print("  - rag/retriever.py")
print("  - rag/formatter.py")
print("  - rag/reranker.py")
print("  - tests/test_retriever.py")
print("\nRun Tests:")
print("  pytest tests/test_retriever.py -v")
print("\nUsage Example:")
print("  from rag.retriever import retrieve")
print("  from rag.formatter import format_context")
print('  docs = retrieve("safety assessment", top_k=5)')
print("  context = format_context(docs)")
print("=" * 60)
