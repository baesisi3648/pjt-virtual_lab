"""
RAG 구조 검증 스크립트

환경변수 없이 파일 구조 및 import 가능 여부만 테스트
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_file_structure():
    """RAG 디렉토리 구조 테스트"""
    print("[1/4] RAG 디렉토리 구조 검증")

    rag_dir = project_root / "rag"
    required_files = [
        "__init__.py",
        "config.py",
        "chroma_client.py",
        "embeddings.py"
    ]

    all_exist = True
    for filename in required_files:
        filepath = rag_dir / filename
        if filepath.exists():
            print(f"  OK {filename}")
        else:
            print(f"  X {filename} - NOT FOUND")
            all_exist = False

    if all_exist:
        print("OK RAG 디렉토리 구조 검증 완료")
    else:
        print("X 일부 파일이 누락되었습니다")

    print()
    return all_exist


def test_rag_config():
    """rag/config.py 설정값 테스트"""
    print("[2/4] RAG 설정 검증")

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
        print(f"  OK CHROMA_COLLECTION_NAME: {CHROMA_COLLECTION_NAME}")
        print(f"  OK EMBEDDING_MODEL: {EMBEDDING_MODEL}")
        print(f"  OK CHUNK_SIZE: {CHUNK_SIZE}")
        print(f"  OK CHUNK_OVERLAP: {CHUNK_OVERLAP}")
        print(f"  OK TOP_K: {TOP_K}")
        print(f"  OK SIMILARITY_THRESHOLD: {SIMILARITY_THRESHOLD}")
        print(f"  OK METADATA_SCHEMA keys: {list(METADATA_SCHEMA.keys())}")
        print("OK RAG 설정 로드 성공")
        print()
        return True
    except Exception as e:
        print(f"X RAG 설정 로드 실패: {e}")
        print()
        return False


def test_function_imports():
    """함수 import 테스트 (환경변수 불필요)"""
    print("[3/4] 함수 Import 검증")

    try:
        # chroma_client 함수 import (환경변수 사용 X)
        import rag.chroma_client as chroma_client
        print(f"  OK get_chroma_client: {callable(chroma_client.get_chroma_client)}")
        print(f"  OK get_or_create_collection: {callable(chroma_client.get_or_create_collection)}")
        print(f"  OK delete_collection: {callable(chroma_client.delete_collection)}")

        # embeddings 함수 import (환경변수 사용 X)
        import rag.embeddings as embeddings
        print(f"  OK get_embedding_function: {callable(embeddings.get_embedding_function)}")
        print(f"  OK get_single_embedding: {callable(embeddings.get_single_embedding)}")

        print("OK 함수 Import 성공")
        print()
        return True
    except Exception as e:
        print(f"X 함수 Import 실패: {e}")
        print()
        return False


def test_metadata_schema():
    """메타데이터 스키마 검증"""
    print("[4/4] 메타데이터 스키마 검증")

    try:
        from rag.config import METADATA_SCHEMA

        required_keys = ["source", "document_type", "year", "page", "section"]
        all_keys_exist = all(key in METADATA_SCHEMA for key in required_keys)

        for key in required_keys:
            if key in METADATA_SCHEMA:
                print(f"  OK {key}: {METADATA_SCHEMA[key]}")
            else:
                print(f"  X {key} - MISSING")

        if all_keys_exist:
            print("OK 메타데이터 스키마 검증 완료")
        else:
            print("X 일부 필드가 누락되었습니다")

        print()
        return all_keys_exist
    except Exception as e:
        print(f"X 메타데이터 스키마 검증 실패: {e}")
        print()
        return False


def main():
    print("=" * 60)
    print("RAG 구조 검증 (환경변수 불필요)")
    print("=" * 60)
    print()

    results = []

    # 1. 파일 구조
    results.append(test_file_structure())

    # 2. RAG 설정
    results.append(test_rag_config())

    # 3. 함수 import
    results.append(test_function_imports())

    # 4. 메타데이터 스키마
    results.append(test_metadata_schema())

    print("=" * 60)
    if all(results):
        print("검증 완료: 모든 테스트 통과")
    else:
        print(f"검증 실패: {sum(results)}/{len(results)} 테스트 통과")
    print("=" * 60)
    print()
    print("주의: ChromaDB 연결 테스트는 .env 파일 설정 후 진행하세요")
    print("  docker-compose up -d chroma")
    print("  python test_rag_setup.py")


if __name__ == "__main__":
    main()
