"""
RAG Retriever Demo

Mock 데이터로 검색 시연
"""

from unittest.mock import Mock, patch

# Mock 검색 시연
print("=" * 60)
print("RAG Retriever Demo")
print("=" * 60)

with patch('rag.retriever.get_chroma_client'), \
     patch('rag.retriever.get_or_create_collection') as mock_coll, \
     patch('rag.retriever.get_single_embedding') as mock_embed:

    from rag.retriever import retrieve
    from rag.formatter import format_citation, format_context

    # Mock 설정
    mock_embed.return_value = [0.1] * 1536
    mock_coll_instance = Mock()
    mock_coll.return_value = mock_coll_instance

    mock_coll_instance.query.return_value = {
        'documents': [[
            'Substantial equivalence is a key concept in NGT safety assessment. It compares the new product to conventional counterparts.',
            'Risk assessment framework requires comprehensive toxicological and nutritional analysis of genetically modified organisms.',
            'Safety evaluation procedures include allergenicity testing, compositional analysis, and feeding studies.',
            'Codex Alimentarius provides international food safety standards for biotechnology-derived foods.',
            'Molecular characterization is essential to understand the genetic modifications and their stability.'
        ]],
        'metadatas': [[
            {'source': 'Codex', 'year': 2023, 'page': 5, 'section': 'Safety Assessment'},
            {'source': 'FDA', 'year': 2022, 'page': 12, 'section': 'Risk Analysis'},
            {'source': 'EFSA', 'year': 2021, 'page': 8, 'section': 'Evaluation Methods'},
            {'source': 'Codex', 'year': 2023, 'page': 15, 'section': 'International Standards'},
            {'source': 'FSANZ', 'year': 2020, 'page': 3, 'section': 'Genetic Modifications'}
        ]],
        'distances': [[0.12, 0.25, 0.38, 0.42, 0.55]]
    }

    # 1. 기본 검색
    print("\n[1] Basic Search")
    print("-" * 60)
    query = "What is substantial equivalence?"
    print(f"Query: {query}\n")

    docs = retrieve(query, top_k=3)
    for i, doc in enumerate(docs, 1):
        print(f"[{i}] Similarity: {1 - doc['distance']:.3f}")
        print(f"    Source: {doc['metadata']['source']} ({doc['metadata']['year']})")
        print(f"    Section: {doc['metadata'].get('section', 'N/A')}")
        print(f"    Text: {doc['text'][:80]}...")
        print()

    # 2. Citation 포맷팅
    print("\n[2] Citation Formatting")
    print("-" * 60)
    for doc in docs[:2]:
        citation = format_citation(doc)
        print(f"  {citation}")

    # 3. 컨텍스트 생성
    print("\n[3] Context Generation")
    print("-" * 60)
    context = format_context(docs)
    print(f"Context length: {len(context)} characters\n")
    print("Preview:")
    print(context[:300] + "...\n")

    # 4. 메타데이터 필터링
    print("\n[4] Metadata Filtering")
    print("-" * 60)

    # Codex 문서만
    mock_coll_instance.query.return_value = {
        'documents': [[
            'Substantial equivalence is a key concept in NGT safety assessment.',
            'Codex Alimentarius provides international food safety standards.'
        ]],
        'metadatas': [[
            {'source': 'Codex', 'year': 2023, 'page': 5},
            {'source': 'Codex', 'year': 2023, 'page': 15}
        ]],
        'distances': [[0.12, 0.42]]
    }

    codex_docs = retrieve("safety", filter={"source": "Codex"})
    print(f"Filter: {{'source': 'Codex'}}")
    print(f"Results: {len(codex_docs)} documents\n")

    for i, doc in enumerate(codex_docs, 1):
        print(f"[{i}] {doc['metadata']['source']} ({doc['metadata']['year']})")
        print(f"    {doc['text'][:60]}...")

    # 5. Reranking
    print("\n[5] Reranking (Placeholder)")
    print("-" * 60)
    from rag.reranker import rerank

    sample_docs = [
        {'text': 'doc1', 'metadata': {'source': 'A'}, 'distance': 0.5},
        {'text': 'doc2', 'metadata': {'source': 'B'}, 'distance': 0.3},
        {'text': 'doc3', 'metadata': {'source': 'C'}, 'distance': 0.1}
    ]

    reranked = rerank("query", sample_docs, top_k=2)
    print(f"Input: {len(sample_docs)} documents")
    print(f"Output: {len(reranked)} documents")
    print("Note: Placeholder implementation - order unchanged")

print("\n" + "=" * 60)
print("Demo Complete")
print("=" * 60)
print("\nUsage Example:")
print("  from rag.retriever import retrieve")
print("  from rag.formatter import format_context")
print('  docs = retrieve("safety assessment", top_k=5)')
print("  context = format_context(docs)")
print("=" * 60)
