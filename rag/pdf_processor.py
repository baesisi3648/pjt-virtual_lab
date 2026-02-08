"""
PDF Processing Pipeline

PDF 문서 → 텍스트 추출 → 청킹 → 임베딩 → ChromaDB 저장
"""

import os
from typing import List, Dict, Optional
from pypdf import PdfReader
from langchain_text_splitters import RecursiveCharacterTextSplitter

from .chroma_client import get_chroma_client, get_or_create_collection
from .embeddings import get_embedding_function


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    PyPDF로 PDF 텍스트 추출

    Args:
        pdf_path: PDF 파일 경로

    Returns:
        str: 추출된 전체 텍스트

    Raises:
        FileNotFoundError: PDF 파일이 없을 경우
        Exception: PDF 읽기 실패
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    try:
        reader = PdfReader(pdf_path)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

        if not text.strip():
            raise ValueError(f"No text extracted from PDF: {pdf_path}")

        return text
    except ValueError:
        # ValueError는 그대로 re-raise
        raise
    except Exception as e:
        raise Exception(f"Failed to extract text from PDF: {e}")


def chunk_text(
    text: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    separators: Optional[List[str]] = None
) -> List[str]:
    """
    RecursiveCharacterTextSplitter로 청크 분할

    Args:
        text: 분할할 텍스트
        chunk_size: 청크 최대 크기 (기본값: 1000)
        chunk_overlap: 청크 간 오버랩 (기본값: 200)
        separators: 구분자 리스트 (기본값: ["\n\n", "\n", " ", ""])

    Returns:
        List[str]: 청크 리스트
    """
    if separators is None:
        separators = ["\n\n", "\n", ". ", " ", ""]

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=separators,
        is_separator_regex=False,
    )

    chunks = splitter.split_text(text)
    return chunks


def process_pdf(
    pdf_path: str,
    source: str,
    document_type: str,
    year: int,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    batch_size: int = 100
) -> Dict[str, any]:
    """
    PDF 파일 처리 및 ChromaDB 저장

    Args:
        pdf_path: PDF 파일 경로
        source: 문서 출처 (예: "Codex", "FDA", "EFSA")
        document_type: 문서 유형 (예: "guideline", "regulation")
        year: 발행 연도
        chunk_size: 청크 최대 크기
        chunk_overlap: 청크 간 오버랩
        batch_size: 임베딩 배치 크기

    Returns:
        Dict: {
            "chunks_count": int,
            "pdf_path": str,
            "source": str,
            "year": int
        }

    Raises:
        ValueError: 잘못된 파라미터
        Exception: 처리 중 오류
    """
    if not pdf_path:
        raise ValueError("pdf_path is required")
    if not source:
        raise ValueError("source is required")
    if not document_type:
        raise ValueError("document_type is required")
    if not year or year < 1900 or year > 2100:
        raise ValueError("year must be between 1900 and 2100")

    # 1. PDF 텍스트 추출
    print(f"Extracting text from {pdf_path}...")
    text = extract_text_from_pdf(pdf_path)
    print(f"Extracted {len(text)} characters")

    # 2. 청크 분할
    print(f"Chunking text (chunk_size={chunk_size}, overlap={chunk_overlap})...")
    chunks = chunk_text(text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    print(f"Created {len(chunks)} chunks")

    # 3. 임베딩 생성 (배치 처리)
    print(f"Generating embeddings (batch_size={batch_size})...")
    embed_fn = get_embedding_function()
    all_embeddings = []

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        batch_embeddings = embed_fn(batch)
        all_embeddings.extend(batch_embeddings)
        print(f"  Processed {min(i + batch_size, len(chunks))}/{len(chunks)} chunks")

    # 4. ChromaDB에 저장
    print(f"Storing in ChromaDB...")
    client = get_chroma_client()
    collection = get_or_create_collection(client)

    # 파일명에서 식별자 생성
    filename = os.path.splitext(os.path.basename(pdf_path))[0]
    ids = [f"{source}_{year}_{filename}_{i}" for i in range(len(chunks))]

    metadatas = [
        {
            "source": source,
            "document_type": document_type,
            "year": year,
            "chunk_index": i,
            "filename": filename
        }
        for i in range(len(chunks))
    ]

    # 배치로 저장
    for i in range(0, len(chunks), batch_size):
        batch_end = min(i + batch_size, len(chunks))
        collection.add(
            ids=ids[i:batch_end],
            embeddings=all_embeddings[i:batch_end],
            documents=chunks[i:batch_end],
            metadatas=metadatas[i:batch_end]
        )
        print(f"  Stored {batch_end}/{len(chunks)} chunks")

    print(f"Successfully processed {pdf_path}")

    return {
        "chunks_count": len(chunks),
        "pdf_path": pdf_path,
        "source": source,
        "year": year,
        "document_type": document_type,
        "filename": filename
    }


def process_text_file(
    text_path: str,
    source: str,
    document_type: str,
    year: int,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    batch_size: int = 100
) -> Dict[str, any]:
    """
    텍스트 파일 처리 (테스트용 - PDF 없을 경우)

    Args:
        text_path: 텍스트 파일 경로
        source: 문서 출처
        document_type: 문서 유형
        year: 발행 연도
        chunk_size: 청크 최대 크기
        chunk_overlap: 청크 간 오버랩
        batch_size: 임베딩 배치 크기

    Returns:
        Dict: process_pdf()와 동일한 형식
    """
    if not os.path.exists(text_path):
        raise FileNotFoundError(f"Text file not found: {text_path}")

    # 텍스트 읽기
    with open(text_path, 'r', encoding='utf-8') as f:
        text = f.read()

    if not text.strip():
        raise ValueError(f"Empty text file: {text_path}")

    print(f"Read {len(text)} characters from {text_path}")

    # 나머지 처리는 PDF와 동일
    chunks = chunk_text(text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    print(f"Created {len(chunks)} chunks")

    embed_fn = get_embedding_function()
    all_embeddings = []

    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        batch_embeddings = embed_fn(batch)
        all_embeddings.extend(batch_embeddings)
        print(f"  Processed {min(i + batch_size, len(chunks))}/{len(chunks)} chunks")

    client = get_chroma_client()
    collection = get_or_create_collection(client)

    filename = os.path.splitext(os.path.basename(text_path))[0]
    ids = [f"{source}_{year}_{filename}_{i}" for i in range(len(chunks))]

    metadatas = [
        {
            "source": source,
            "document_type": document_type,
            "year": year,
            "chunk_index": i,
            "filename": filename
        }
        for i in range(len(chunks))
    ]

    for i in range(0, len(chunks), batch_size):
        batch_end = min(i + batch_size, len(chunks))
        collection.add(
            ids=ids[i:batch_end],
            embeddings=all_embeddings[i:batch_end],
            documents=chunks[i:batch_end],
            metadatas=metadatas[i:batch_end]
        )
        print(f"  Stored {batch_end}/{len(chunks)} chunks")

    return {
        "chunks_count": len(chunks),
        "pdf_path": text_path,
        "source": source,
        "year": year,
        "document_type": document_type,
        "filename": filename
    }
