"""Pinecone Vector Database Client"""
from pinecone.grpc import PineconeGRPC as Pinecone
from openai import OpenAI
from config import settings
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


class PineconeRAGClient:
    """Pinecone 기반 RAG 검색 클라이언트"""

    def __init__(self):
        # Pinecone 초기화 (gRPC)
        self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        self.index = self.pc.Index(settings.PINECONE_INDEX_NAME)

        # OpenAI 임베딩 클라이언트
        self.openai = OpenAI(api_key=settings.OPENAI_API_KEY)

        logger.info(f"✅ Pinecone 연결: {settings.PINECONE_INDEX_NAME}")

    def embed_text(self, text: str) -> List[float]:
        """텍스트를 벡터로 변환"""
        response = self.openai.embeddings.create(
            model=settings.EMBEDDING_MODEL,
            input=text
        )
        return response.data[0].embedding

    def upsert_documents(self, documents: List[Dict]):
        """문서 추가 (PDF 청크)

        Args:
            documents: [{"text": "...", "source": "file.pdf", "page": 1}, ...]
        """
        vectors = []
        for i, doc in enumerate(documents):
            vector_id = f"{doc.get('source', 'doc')}_{doc.get('page', 0)}_{i}"
            embedding = self.embed_text(doc["text"])

            vectors.append({
                "id": vector_id,
                "values": embedding,
                "metadata": {
                    "text": doc["text"],
                    "source": doc.get("source", "unknown"),
                    "page": doc.get("page", 0)
                }
            })

        # Batch upsert (100개씩)
        batch_size = 100
        for i in range(0, len(vectors), batch_size):
            batch = vectors[i:i + batch_size]
            self.index.upsert(vectors=batch)
            logger.info(f"📤 업로드: {i+len(batch)}/{len(vectors)}")

        logger.info(f"✅ {len(documents)}개 문서 추가 완료")

    def search_one_per_document(self, query: str, doc_ids: List[str], top_k: int = 5) -> List[Dict]:
        """Top-1 chunk of each document by a filtered query (doc_id) per document - Pinecone's approximate
        nearest-neighbour result, not an exhaustive comparison - then the top_k documents by score; ties broken
        by doc_id.
        Revision, corpus v1 (2026-11-07): set after the first v1 snapshot returned five chunks of one document.
        """
        vec = self.embed_text(query)
        best = []
        for doc_id in doc_ids:
            res = self.index.query(vector=vec, top_k=1, include_metadata=True, filter={"doc_id": {"$eq": doc_id}})
            matches = res["matches"]
            if not matches:
                raise RuntimeError(f"no chunk returned for document {doc_id}")
            m = matches[0]
            best.append({"id": m.get("id") if hasattr(m, "get") else getattr(m, "id", None),
                         "doc_id": doc_id, "text": m["metadata"]["text"], "source": m["metadata"]["source"],
                         "page": m["metadata"].get("page", 0), "score": m["score"]})
        best.sort(key=lambda d: (-d["score"], d["doc_id"]))
        return best[:top_k]

    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """쿼리 검색

        Args:
            query: 검색 쿼리
            top_k: 반환할 문서 수

        Returns:
            [{"text": "...", "source": "...", "page": 1, "score": 0.95}, ...]
        """
        # 쿼리를 벡터로 변환
        query_embedding = self.embed_text(query)

        # Pinecone 검색
        results = self.index.query(
            vector=query_embedding,
            top_k=top_k,
            include_metadata=True
        )

        # 결과 포맷팅
        documents = []
        for match in results["matches"]:
            documents.append({
                "id": match.get("id") if hasattr(match, "get") else getattr(match, "id", None),
                "text": match["metadata"]["text"],
                "source": match["metadata"]["source"],
                "page": match["metadata"].get("page", 0),
                "score": match["score"]
            })

        logger.info(f"🔍 검색 완료: {len(documents)}개 문서 발견")
        return documents


# 싱글톤 인스턴스
_pinecone_client = None


def get_pinecone_client() -> PineconeRAGClient:
    """Pinecone 클라이언트 싱글톤"""
    global _pinecone_client
    if _pinecone_client is None:
        _pinecone_client = PineconeRAGClient()
    return _pinecone_client
