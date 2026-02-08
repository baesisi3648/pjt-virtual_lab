"""
RAG Setup 검증 스크립트

ChromaDB 연결 및 컬렉션 생성 테스트
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_chroma_client():
    """ChromaDB 클라이언트 생성 테스트"""
    try:
        from rag.chroma_client import get_chroma_client
        client = get_chroma_client()
        print("✓ ChromaDB 클라이언트 생성 성공")
        return client
    except Exception as e:
        print(f"✗ ChromaDB 클라이언트 생성 실패: {e}")
        return None


def test_collection_creation(client):
    """컬렉션 생성 테스트"""
    if client is None:
        print("✗ 클라이언트가 없어 컬렉션 생성 스킵")
        return None

    try:
        from rag.chroma_client import get_or_create_collection
        collection = get_or_create_collection(client)
        count = collection.count()
        print(f"✓ 컬렉션 생성 성공: {collection.name}")
        print(f"  - Document count: {count}")
        print(f"  - Metadata: {collection.metadata}")
        return collection
    except Exception as e:
        print(f"✗ 컬렉션 생성 실패: {e}")
        return None


def test_embedding_function():
    """Embedding 함수 테스트"""
    try:
        from rag.embeddings import get_embedding_function, get_single_embedding

        # 함수 생성 테스트
        embed_fn = get_embedding_function()
        print("✓ Embedding 함수 생성 성공")

        # 단일 텍스트 임베딩 테스트 (API 호출 스킵)
        print("  - Embedding API 호출은 스킵 (비용 절약)")
        return True
    except Exception as e:
        print(f"✗ Embedding 함수 생성 실패: {e}")
        return False


def test_config():
    """RAG 설정 테스트"""
    try:
        from rag.config import (
            CHROMA_COLLECTION_NAME,
            EMBEDDING_MODEL,
            CHUNK_SIZE,
            CHUNK_OVERLAP,
            TOP_K,
            SIMILARITY_THRESHOLD,
            METADATA_SCHEMA
        )
        print("✓ RAG 설정 로드 성공")
        print(f"  - Collection: {CHROMA_COLLECTION_NAME}")
        print(f"  - Embedding Model: {EMBEDDING_MODEL}")
        print(f"  - Chunk Size: {CHUNK_SIZE}")
        print(f"  - Top K: {TOP_K}")
        print(f"  - Metadata Schema: {list(METADATA_SCHEMA.keys())}")
        return True
    except Exception as e:
        print(f"✗ RAG 설정 로드 실패: {e}")
        return False


def main():
    print("=" * 60)
    print("RAG Setup 검증")
    print("=" * 60)
    print()

    # 1. 설정 테스트
    print("[1/4] RAG 설정 테스트")
    test_config()
    print()

    # 2. Embedding 함수 테스트
    print("[2/4] Embedding 함수 테스트")
    test_embedding_function()
    print()

    # 3. ChromaDB 클라이언트 테스트
    print("[3/4] ChromaDB 클라이언트 테스트")
    client = test_chroma_client()
    print()

    # 4. 컬렉션 생성 테스트
    print("[4/4] 컬렉션 생성 테스트")
    if client:
        test_collection_creation(client)
    else:
        print("⚠ ChromaDB가 실행 중이 아닙니다.")
        print("  docker-compose up -d chroma 로 ChromaDB 시작 후 재시도하세요.")
    print()

    print("=" * 60)
    print("검증 완료")
    print("=" * 60)


if __name__ == "__main__":
    main()
