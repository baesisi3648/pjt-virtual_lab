"""
RAG Configuration

벡터 스토어 및 임베딩 설정
"""

# ChromaDB Collection
CHROMA_COLLECTION_NAME = "regulatory_docs"

# Embedding Model
EMBEDDING_MODEL = "text-embedding-3-small"
EMBEDDING_DIMENSION = 1536  # text-embedding-3-small dimension

# Chunking Strategy
CHUNK_SIZE = 1000  # 약 250 토큰 (4 chars ≈ 1 token)
CHUNK_OVERLAP = 200  # 청크 간 중복 길이 (컨텍스트 보존)

# Retrieval Config
TOP_K = 5  # 상위 K개 유사 문서 검색
SIMILARITY_THRESHOLD = 0.7  # 최소 유사도 임계값

# Metadata Schema
METADATA_SCHEMA = {
    "source": str,  # "Codex", "FDA", "EFSA", "FSANZ" 등
    "document_type": str,  # "guideline", "regulation", "case_study"
    "year": int,  # 발행 연도
    "page": int,  # 페이지 번호
    "section": str,  # 섹션 제목 (optional)
}
