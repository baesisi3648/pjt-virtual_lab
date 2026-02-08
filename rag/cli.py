"""
RAG CLI

규제 문서 처리를 위한 명령줄 인터페이스

Usage:
    python -m rag.cli process --file data/regulatory/codex.pdf --source Codex --year 2023
    python -m rag.cli process --file data/regulatory/sample.txt --source FDA --year 2024
    python -m rag.cli query "NGT safety assessment"
    python -m rag.cli stats
"""

import argparse
import sys
import os

from .pdf_processor import process_pdf, process_text_file
from .chroma_client import get_chroma_client, get_or_create_collection
from .embeddings import get_single_embedding


def cmd_process(args):
    """PDF 또는 텍스트 파일 처리"""
    file_path = args.file
    source = args.source
    document_type = args.type
    year = args.year
    chunk_size = args.chunk_size
    chunk_overlap = args.chunk_overlap
    batch_size = args.batch_size

    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        return 1

    try:
        # 파일 확장자에 따라 처리
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()

        if ext == '.pdf':
            result = process_pdf(
                pdf_path=file_path,
                source=source,
                document_type=document_type,
                year=year,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                batch_size=batch_size
            )
        elif ext in ['.txt', '.md']:
            result = process_text_file(
                text_path=file_path,
                source=source,
                document_type=document_type,
                year=year,
                chunk_size=chunk_size,
                chunk_overlap=chunk_overlap,
                batch_size=batch_size
            )
        else:
            print(f"Error: Unsupported file type: {ext}")
            print("Supported types: .pdf, .txt, .md")
            return 1

        print("\n=== Processing Complete ===")
        print(f"File: {result['filename']}")
        print(f"Source: {result['source']}")
        print(f"Year: {result['year']}")
        print(f"Document Type: {result['document_type']}")
        print(f"Chunks Created: {result['chunks_count']}")

        return 0

    except Exception as e:
        print(f"Error processing file: {e}")
        import traceback
        traceback.print_exc()
        return 1


def cmd_query(args):
    """벡터 검색 수행"""
    query = args.query
    top_k = args.top_k

    try:
        client = get_chroma_client()
        collection = get_or_create_collection(client)

        # 쿼리 임베딩 생성
        query_embedding = get_single_embedding(query)

        # 검색
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )

        print(f"\n=== Search Results for: '{query}' ===\n")

        if not results['ids'] or not results['ids'][0]:
            print("No results found.")
            return 0

        for i, (doc_id, doc, metadata, distance) in enumerate(zip(
            results['ids'][0],
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0]
        )):
            print(f"[{i+1}] ID: {doc_id}")
            print(f"    Source: {metadata.get('source')} ({metadata.get('year')})")
            print(f"    Type: {metadata.get('document_type')}")
            print(f"    Distance: {distance:.4f}")
            print(f"    Preview: {doc[:200]}...")
            print()

        return 0

    except Exception as e:
        print(f"Error querying: {e}")
        import traceback
        traceback.print_exc()
        return 1


def cmd_stats(args):
    """컬렉션 통계 출력"""
    try:
        client = get_chroma_client()
        collection = get_or_create_collection(client)

        count = collection.count()
        print(f"\n=== ChromaDB Collection Stats ===")
        print(f"Total Documents: {count}")

        if count > 0:
            # 샘플 메타데이터 확인
            sample = collection.get(limit=10)
            if sample['metadatas']:
                sources = set(m.get('source') for m in sample['metadatas'])
                years = set(m.get('year') for m in sample['metadatas'])
                types = set(m.get('document_type') for m in sample['metadatas'])

                print(f"\nSample Metadata:")
                print(f"  Sources: {', '.join(str(s) for s in sources)}")
                print(f"  Years: {', '.join(str(y) for y in sorted(years))}")
                print(f"  Types: {', '.join(str(t) for t in types)}")

        return 0

    except Exception as e:
        print(f"Error getting stats: {e}")
        import traceback
        traceback.print_exc()
        return 1


def main():
    parser = argparse.ArgumentParser(
        description="RAG CLI for regulatory document processing"
    )
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # process 명령
    process_parser = subparsers.add_parser('process', help='Process PDF or text file')
    process_parser.add_argument('--file', required=True, help='Path to PDF or text file')
    process_parser.add_argument('--source', required=True, help='Document source (e.g., Codex, FDA)')
    process_parser.add_argument('--type', default='guideline', help='Document type (default: guideline)')
    process_parser.add_argument('--year', type=int, required=True, help='Publication year')
    process_parser.add_argument('--chunk-size', type=int, default=1000, help='Chunk size (default: 1000)')
    process_parser.add_argument('--chunk-overlap', type=int, default=200, help='Chunk overlap (default: 200)')
    process_parser.add_argument('--batch-size', type=int, default=100, help='Embedding batch size (default: 100)')

    # query 명령
    query_parser = subparsers.add_parser('query', help='Query the vector store')
    query_parser.add_argument('query', help='Search query')
    query_parser.add_argument('--top-k', type=int, default=5, help='Number of results (default: 5)')

    # stats 명령
    stats_parser = subparsers.add_parser('stats', help='Show collection statistics')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    if args.command == 'process':
        return cmd_process(args)
    elif args.command == 'query':
        return cmd_query(args)
    elif args.command == 'stats':
        return cmd_stats(args)
    else:
        parser.print_help()
        return 1


if __name__ == '__main__':
    sys.exit(main())
