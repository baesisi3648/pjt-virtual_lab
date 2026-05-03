"""
Test RAG Retriever

쿼리 → 관련 문서 검색 테스트
"""

import pytest
from unittest.mock import Mock, patch
from typing import List, Dict


class TestRetriever:
    """RAG Retriever 테스트"""

    @patch('rag.retriever.get_chroma_client')
    @patch('rag.retriever.get_or_create_collection')
    @patch('rag.retriever.get_single_embedding')
    def test_retrieve_basic(self, mock_embedding, mock_collection, mock_client):
        """기본 검색 테스트"""
        from rag.retriever import retrieve

        # Mock 설정
        mock_embedding.return_value = [0.1] * 1536
        mock_coll_instance = Mock()
        mock_collection.return_value = mock_coll_instance

        # Mock ChromaDB query 결과
        mock_coll_instance.query.return_value = {
            'documents': [[
                'Substantial equivalence is a key concept.',
                'Risk assessment framework requires...',
                'Safety evaluation procedures include...',
                'Toxicological studies are essential.',
                'Allergenicity testing protocols...'
            ]],
            'metadatas': [[
                {'source': 'Codex', 'year': 2023, 'page': 5},
                {'source': 'FDA', 'year': 2022, 'page': 12},
                {'source': 'EFSA', 'year': 2021, 'page': 8},
                {'source': 'Codex', 'year': 2023, 'page': 15},
                {'source': 'FSANZ', 'year': 2020, 'page': 3}
            ]],
            'distances': [[0.1, 0.2, 0.3, 0.4, 0.5]]
        }

        # 실행
        docs = retrieve("What is substantial equivalence?", top_k=5)

        # 검증
        assert len(docs) == 5
        assert docs[0]['text'] == 'Substantial equivalence is a key concept.'
        assert docs[0]['metadata']['source'] == 'Codex'
        assert docs[0]['metadata']['year'] == 2023
        assert docs[0]['distance'] == 0.1

    @patch('rag.retriever.get_chroma_client')
    @patch('rag.retriever.get_or_create_collection')
    @patch('rag.retriever.get_single_embedding')
    def test_retrieve_with_filter(self, mock_embedding, mock_collection, mock_client):
        """메타데이터 필터링 테스트"""
        from rag.retriever import retrieve

        # Mock 설정
        mock_embedding.return_value = [0.1] * 1536
        mock_coll_instance = Mock()
        mock_collection.return_value = mock_coll_instance

        mock_coll_instance.query.return_value = {
            'documents': [['Codex guideline document 1', 'Codex guideline document 2']],
            'metadatas': [[
                {'source': 'Codex', 'year': 2023, 'page': 1},
                {'source': 'Codex', 'year': 2022, 'page': 3}
            ]],
            'distances': [[0.1, 0.15]]
        }

        # 실행
        docs = retrieve("safety", filter={"source": "Codex"})

        # 검증
        assert len(docs) == 2
        assert all(d['metadata']['source'] == 'Codex' for d in docs)

    @patch('rag.retriever.get_chroma_client')
    @patch('rag.retriever.get_or_create_collection')
    @patch('rag.retriever.get_single_embedding')
    def test_retrieve_empty_result(self, mock_embedding, mock_collection, mock_client):
        """빈 결과 처리 테스트"""
        from rag.retriever import retrieve

        # Mock 설정
        mock_embedding.return_value = [0.1] * 1536
        mock_coll_instance = Mock()
        mock_collection.return_value = mock_coll_instance

        mock_coll_instance.query.return_value = {
            'documents': [[]],
            'metadatas': [[]],
            'distances': [[]]
        }

        # 실행
        docs = retrieve("nonexistent query")

        # 검증
        assert docs == []


class TestFormatter:
    """Citation Formatter 테스트"""

    def test_format_citation(self):
        """Citation 포맷팅 테스트"""
        from rag.formatter import format_citation

        document = {
            'text': 'Sample text',
            'metadata': {'source': 'Codex', 'year': 2023, 'page': 5},
            'distance': 0.1
        }

        citation = format_citation(document)
        assert citation == "[출처: Codex (2023), p.5]"

    def test_format_context(self):
        """컨텍스트 병합 테스트"""
        from rag.formatter import format_context

        documents = [
            {
                'text': 'First document text.',
                'metadata': {'source': 'Codex', 'year': 2023, 'page': 1},
                'distance': 0.1
            },
            {
                'text': 'Second document text.',
                'metadata': {'source': 'FDA', 'year': 2022, 'page': 2},
                'distance': 0.2
            }
        ]

        context = format_context(documents)

        assert 'First document text.' in context
        assert 'Second document text.' in context
        assert '[출처: Codex (2023), p.1]' in context
        assert '[출처: FDA (2022), p.2]' in context

    def test_format_context_empty(self):
        """빈 문서 리스트 처리"""
        from rag.formatter import format_context

        context = format_context([])
        assert context == ""


class TestReranker:
    """Reranker 테스트 (옵션)"""

    def test_rerank_placeholder(self):
        """Rerank placeholder 테스트"""
        from rag.reranker import rerank

        documents = [
            {'text': 'doc1', 'metadata': {}, 'distance': 0.5},
            {'text': 'doc2', 'metadata': {}, 'distance': 0.3},
            {'text': 'doc3', 'metadata': {}, 'distance': 0.1}
        ]

        # Placeholder는 그대로 반환
        result = rerank("query", documents, top_k=2)
        assert len(result) == 2
        assert result == documents[:2]
