"""
청킹 로직 검증 데모

ChromaDB 없이 청킹 동작만 확인
"""

from rag.pdf_processor import chunk_text, extract_text_from_pdf
import os


def demo_chunking():
    """샘플 텍스트로 청킹 검증"""

    # 샘플 파일 읽기
    sample_file = "data/regulatory/sample.txt"

    if not os.path.exists(sample_file):
        print(f"Sample file not found: {sample_file}")
        return

    with open(sample_file, 'r', encoding='utf-8') as f:
        text = f.read()

    print("=== Chunking Demo ===\n")
    print(f"Original Text Length: {len(text)} characters")
    print(f"Original Text Preview:\n{text[:200]}...\n")

    # 다양한 청크 크기로 테스트
    configs = [
        (500, 100),
        (1000, 200),
        (1500, 300)
    ]

    for chunk_size, chunk_overlap in configs:
        chunks = chunk_text(text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)

        print(f"\n--- Chunk Size: {chunk_size}, Overlap: {chunk_overlap} ---")
        print(f"Number of Chunks: {len(chunks)}")
        print(f"Chunk Sizes: {[len(c) for c in chunks]}")

        if chunks:
            print(f"\nFirst Chunk Preview:\n{chunks[0][:150]}...\n")

            if len(chunks) > 1:
                print(f"Last Chunk Preview:\n{chunks[-1][:150]}...\n")

    print("\n=== Estimation for Large Document ===")
    # 실제 규제 문서 크기 예상
    estimated_doc_size = 100000  # 100KB (약 100페이지 PDF)
    estimated_chunks = estimated_doc_size // (1000 - 200) + 1
    print(f"Estimated document size: {estimated_doc_size} chars")
    print(f"Estimated chunks (1000/200): ~{estimated_chunks} chunks")
    print(f"Estimated embeddings API calls: {estimated_chunks // 100 + 1} batches (batch_size=100)")


if __name__ == "__main__":
    demo_chunking()
