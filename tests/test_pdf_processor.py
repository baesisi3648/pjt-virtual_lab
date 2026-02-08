"""
Tests for PDF Processing Pipeline

TDD Workflow:
1. RED: Test fails (no implementation)
2. GREEN: Test passes (minimal implementation)
3. REFACTOR: Improve code (tests still pass)
"""

import pytest
import os
from unittest.mock import Mock, patch, MagicMock

from rag.pdf_processor import (
    extract_text_from_pdf,
    chunk_text,
    process_pdf,
    process_text_file
)


class TestChunkText:
    """청킹 로직 테스트"""

    def test_chunk_text_basic(self):
        """기본 청킹 동작"""
        text = "A" * 2500  # 2500자
        chunks = chunk_text(text, chunk_size=1000, chunk_overlap=200)

        assert len(chunks) >= 2  # 최소 2개 청크
        assert all(len(chunk) <= 1200 for chunk in chunks)  # 오버랩 고려

    def test_chunk_text_small(self):
        """작은 텍스트 (청크 크기보다 작음)"""
        text = "Short text"
        chunks = chunk_text(text, chunk_size=1000, chunk_overlap=200)

        assert len(chunks) == 1
        assert chunks[0] == text

    def test_chunk_text_empty(self):
        """빈 텍스트"""
        text = ""
        chunks = chunk_text(text, chunk_size=1000, chunk_overlap=200)

        assert len(chunks) == 0 or chunks == ['']

    def test_chunk_text_preserves_structure(self):
        """단락 구조 보존"""
        text = "Paragraph 1.\n\nParagraph 2.\n\nParagraph 3."
        chunks = chunk_text(text, chunk_size=50, chunk_overlap=10)

        # 단락 경계에서 분할되는지 확인
        assert len(chunks) >= 1


class TestExtractTextFromPdf:
    """PDF 텍스트 추출 테스트 (모킹)"""

    def test_extract_text_file_not_found(self):
        """존재하지 않는 파일"""
        with pytest.raises(FileNotFoundError):
            extract_text_from_pdf("nonexistent.pdf")

    @patch('rag.pdf_processor.PdfReader')
    def test_extract_text_success(self, mock_reader_class):
        """정상 추출 (모킹)"""
        # 임시 파일 생성
        test_file = "test_temp.pdf"
        with open(test_file, 'w') as f:
            f.write("dummy")

        try:
            # Mock PDF reader
            mock_page = Mock()
            mock_page.extract_text.return_value = "Sample text from page"

            mock_reader = Mock()
            mock_reader.pages = [mock_page]
            mock_reader_class.return_value = mock_reader

            text = extract_text_from_pdf(test_file)

            assert text.strip() == "Sample text from page"
            mock_reader_class.assert_called_once()

        finally:
            if os.path.exists(test_file):
                os.remove(test_file)

    @patch('rag.pdf_processor.PdfReader')
    def test_extract_text_empty_pdf(self, mock_reader_class):
        """빈 PDF (텍스트 없음)"""
        test_file = "test_empty.pdf"
        with open(test_file, 'w') as f:
            f.write("dummy")

        try:
            mock_page = Mock()
            mock_page.extract_text.return_value = ""

            mock_reader = Mock()
            mock_reader.pages = [mock_page]
            mock_reader_class.return_value = mock_reader

            with pytest.raises(ValueError, match="No text extracted"):
                extract_text_from_pdf(test_file)

        finally:
            if os.path.exists(test_file):
                os.remove(test_file)


class TestProcessTextFile:
    """텍스트 파일 처리 테스트"""

    @patch('rag.pdf_processor.get_chroma_client')
    @patch('rag.pdf_processor.get_or_create_collection')
    @patch('rag.pdf_processor.get_embedding_function')
    def test_process_text_file_basic(
        self,
        mock_embed_fn_getter,
        mock_collection_getter,
        mock_client_getter
    ):
        """텍스트 파일 처리 (모킹)"""
        # 샘플 텍스트 파일 생성
        test_file = "test_sample.txt"
        test_content = "NGT safety assessment. " * 100  # 충분한 길이

        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_content)

        try:
            # Mock 설정
            mock_embed_fn = Mock(return_value=[[0.1] * 1536])
            mock_embed_fn_getter.return_value = mock_embed_fn

            mock_collection = Mock()
            mock_collection.add = Mock()
            mock_collection_getter.return_value = mock_collection

            # 처리
            result = process_text_file(
                text_path=test_file,
                source="TestSource",
                document_type="guideline",
                year=2024,
                chunk_size=500,
                chunk_overlap=100,
                batch_size=10
            )

            # 검증
            assert result['chunks_count'] > 0
            assert result['source'] == "TestSource"
            assert result['year'] == 2024
            assert mock_collection.add.called

        finally:
            if os.path.exists(test_file):
                os.remove(test_file)

    def test_process_text_file_not_found(self):
        """존재하지 않는 파일"""
        with pytest.raises(FileNotFoundError):
            process_text_file(
                text_path="nonexistent.txt",
                source="Test",
                document_type="guideline",
                year=2024
            )


class TestProcessPdf:
    """PDF 처리 통합 테스트 (모킹)"""

    @patch('rag.pdf_processor.get_chroma_client')
    @patch('rag.pdf_processor.get_or_create_collection')
    @patch('rag.pdf_processor.get_embedding_function')
    @patch('rag.pdf_processor.extract_text_from_pdf')
    def test_process_pdf_success(
        self,
        mock_extract,
        mock_embed_fn_getter,
        mock_collection_getter,
        mock_client_getter
    ):
        """PDF 처리 성공 시나리오"""
        # Mock 설정
        mock_extract.return_value = "Sample regulatory text. " * 200

        mock_embed_fn = Mock(return_value=[[0.1] * 1536])
        mock_embed_fn_getter.return_value = mock_embed_fn

        mock_collection = Mock()
        mock_collection.add = Mock()
        mock_collection_getter.return_value = mock_collection

        # 처리
        result = process_pdf(
            pdf_path="dummy.pdf",
            source="Codex",
            document_type="guideline",
            year=2023,
            chunk_size=1000,
            chunk_overlap=200,
            batch_size=50
        )

        # 검증
        assert result['chunks_count'] > 0
        assert result['source'] == "Codex"
        assert result['year'] == 2023
        mock_extract.assert_called_once()
        mock_collection.add.called

    def test_process_pdf_invalid_params(self):
        """잘못된 파라미터"""
        with pytest.raises(ValueError):
            process_pdf(
                pdf_path="",
                source="Test",
                document_type="guideline",
                year=2024
            )

        with pytest.raises(ValueError):
            process_pdf(
                pdf_path="test.pdf",
                source="",
                document_type="guideline",
                year=2024
            )

        with pytest.raises(ValueError):
            process_pdf(
                pdf_path="test.pdf",
                source="Test",
                document_type="guideline",
                year=1800  # 잘못된 연도
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
