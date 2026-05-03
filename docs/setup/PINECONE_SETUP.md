# Pinecone 설정 가이드

> ChromaDB 대신 Pinecone으로 RAG 검색 설정하기

---

## 🌟 Pinecone vs ChromaDB

| 항목 | Pinecone | ChromaDB |
|------|----------|----------|
| **타입** | ✨ 클라우드 (SaaS) | 🏠 셀프 호스팅 (Docker) |
| **설치** | ✅ 계정만 생성 | ⚠️ Docker 필요 |
| **확장성** | ✅ 무제한 (자동) | ⚠️ 수동 확장 |
| **속도** | ⚡ 매우 빠름 (최적화) | 🚀 빠름 |
| **가격** | 💰 무료 (100만 벡터) | ✅ 무료 |
| **관리** | ✅ Pinecone이 관리 | ⚠️ 직접 관리 |
| **추천** | **Production** ✅ | MVP/개발 |

**Pinecone 장점**:
- 설치 불필요 (계정만 있으면 됨)
- 자동 백업 및 확장
- 전 세계 CDN (빠른 속도)
- 무료 티어 (100만 벡터까지)

---

## 📝 1단계: Pinecone 계정 생성

### 1.1 회원가입

1. **Pinecone 사이트 접속**:
   ```
   https://app.pinecone.io
   ```

2. **Sign Up** 클릭

3. **Google 계정** 또는 **이메일**로 가입

4. **무료 플랜 선택**:
   - Starter Plan (무료)
   - 100만 벡터까지
   - 1개 인덱스

### 1.2 API 키 발급

1. 로그인 후 왼쪽 메뉴에서 **API Keys** 클릭

2. **Create API Key** 버튼 클릭

3. API 키 복사:
   ```
   예: pcsk_abc123_xyz789...
   ```

4. `.env` 파일에 추가:
   ```env
   PINECONE_API_KEY=pcsk_abc123_xyz789...
   ```

---

## 🗂️ 2단계: Pinecone 인덱스 생성

### 2.1 인덱스 생성 (웹 UI)

1. **Indexes** 메뉴 클릭

2. **Create Index** 버튼 클릭

3. **설정 입력**:
   ```
   Name: virtual-lab-regulatory-docs
   Dimensions: 1536  (OpenAI text-embedding-3-small)
   Metric: cosine
   Environment: us-east-1  (무료 티어)
   ```

4. **Create Index** 클릭

### 2.2 인덱스 생성 (Python 코드)

또는 코드로 자동 생성:

```python
# rag/pinecone_setup.py
from pinecone import Pinecone, ServerlessSpec
from config import settings

# Pinecone 클라이언트 초기화
pc = Pinecone(api_key=settings.PINECONE_API_KEY)

# 인덱스 생성
pc.create_index(
    name=settings.PINECONE_INDEX_NAME,
    dimension=1536,  # OpenAI text-embedding-3-small
    metric="cosine",
    spec=ServerlessSpec(
        cloud="aws",
        region=settings.PINECONE_ENVIRONMENT
    )
)

print(f"✅ 인덱스 생성 완료: {settings.PINECONE_INDEX_NAME}")
```

실행:
```bash
python rag/pinecone_setup.py
```

---

## 📦 3단계: Python 패키지 설치

### 3.1 requirements.txt 업데이트

```bash
# Pinecone 클라이언트 추가
pip install pinecone-client>=3.0.0
```

또는 requirements.txt에 추가:
```
pinecone-client>=3.0.0
openai>=1.0.0  # 임베딩용
```

설치:
```bash
pip install -r requirements.txt
```

---

## 🔧 4단계: Pinecone 클라이언트 코드 작성

### 4.1 rag/pinecone_client.py 생성

```python
"""Pinecone Vector Database Client"""
from pinecone import Pinecone
from openai import OpenAI
from config import settings
from typing import List, Dict
import logging

logger = logging.getLogger(__name__)


class PineconeRAGClient:
    """Pinecone 기반 RAG 검색 클라이언트"""

    def __init__(self):
        # Pinecone 초기화
        self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        self.index = self.pc.Index(settings.PINECONE_INDEX_NAME)

        # OpenAI 임베딩 클라이언트
        self.openai = OpenAI(api_key=settings.OPENAI_API_KEY)

    def embed_text(self, text: str) -> List[float]:
        """텍스트를 벡터로 변환"""
        response = self.openai.embeddings.create(
            model=settings.EMBEDDING_MODEL,
            input=text
        )
        return response.data[0].embedding

    def upsert_documents(self, documents: List[Dict]):
        """문서 추가 (PDF 청크)"""
        vectors = []
        for i, doc in enumerate(documents):
            vector_id = f"doc_{i}"
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

        logger.info(f"✅ {len(documents)}개 문서 추가 완료")

    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        """쿼리 검색"""
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
                "text": match["metadata"]["text"],
                "source": match["metadata"]["source"],
                "page": match["metadata"].get("page", 0),
                "score": match["score"]
            })

        return documents


# 싱글톤 인스턴스
_pinecone_client = None

def get_pinecone_client() -> PineconeRAGClient:
    """Pinecone 클라이언트 싱글톤"""
    global _pinecone_client
    if _pinecone_client is None:
        _pinecone_client = PineconeRAGClient()
    return _pinecone_client
```

---

## 📄 5단계: PDF 문서 로드

### 5.1 rag/pdf_processor.py 생성

```python
"""PDF 문서를 Pinecone에 로드"""
import PyPDF2
from pathlib import Path
from typing import List, Dict
from rag.pinecone_client import get_pinecone_client
import logging

logger = logging.getLogger(__name__)


def extract_text_from_pdf(pdf_path: Path) -> List[Dict]:
    """PDF에서 텍스트 추출"""
    documents = []

    with open(pdf_path, 'rb') as file:
        reader = PyPDF2.PdfReader(file)

        for page_num, page in enumerate(reader.pages, start=1):
            text = page.extract_text()

            # 청크로 분할 (1000자씩)
            chunk_size = 1000
            for i in range(0, len(text), chunk_size):
                chunk = text[i:i + chunk_size]

                if len(chunk.strip()) > 50:  # 너무 짧은 청크 제외
                    documents.append({
                        "text": chunk,
                        "source": pdf_path.name,
                        "page": page_num
                    })

    logger.info(f"📄 {pdf_path.name}: {len(documents)}개 청크 추출")
    return documents


def load_pdfs_to_pinecone(pdf_dir: str = "data/regulatory"):
    """모든 PDF를 Pinecone에 로드"""
    pdf_path = Path(pdf_dir)

    if not pdf_path.exists():
        logger.error(f"❌ 디렉토리 없음: {pdf_dir}")
        return

    # Pinecone 클라이언트
    client = get_pinecone_client()

    # 모든 PDF 파일 처리
    pdf_files = list(pdf_path.glob("*.pdf"))
    logger.info(f"📚 {len(pdf_files)}개 PDF 파일 발견")

    all_documents = []
    for pdf_file in pdf_files:
        docs = extract_text_from_pdf(pdf_file)
        all_documents.extend(docs)

    # Pinecone에 업로드
    logger.info(f"⬆️ Pinecone에 업로드 중... (총 {len(all_documents)}개 청크)")
    client.upsert_documents(all_documents)

    logger.info("✅ 완료!")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    load_pdfs_to_pinecone()
```

### 5.2 PDF 문서 로드 실행

```bash
# data/regulatory/ 폴더에 PDF 파일 배치
# 예: codex_guideline.pdf, fda_guidance.pdf

# 로드 실행
python rag/pdf_processor.py
```

출력 예:
```
📚 3개 PDF 파일 발견
📄 codex_guideline.pdf: 245개 청크 추출
📄 fda_guidance.pdf: 189개 청크 추출
📄 eu_ngt_regulation.pdf: 312개 청크 추출
⬆️ Pinecone에 업로드 중... (총 746개 청크)
✅ 완료!
```

---

## 🔗 6단계: LangChain Tool 통합

### 6.1 tools/rag_search.py 수정

```python
"""RAG Search Tool (Pinecone)"""
from langchain_core.tools import tool
from rag.pinecone_client import get_pinecone_client
from config import settings


@tool
def rag_search_tool(query: str) -> str:
    """규제 문서 검색 (Pinecone)

    Args:
        query: 검색 쿼리 (예: "알레르기 평가 방법")

    Returns:
        검색된 문서 내용 및 출처
    """
    client = get_pinecone_client()
    documents = client.search(query, top_k=settings.TOP_K)

    if not documents:
        return "❌ 관련 문서를 찾을 수 없습니다."

    # 결과 포맷팅
    result = []
    for i, doc in enumerate(documents, start=1):
        result.append(f"""
### 문서 {i} (유사도: {doc['score']:.2f})
**출처**: {doc['source']} (p.{doc['page']})

{doc['text']}
""")

    return "\n\n".join(result)
```

---

## ✅ 7단계: 테스트

### 7.1 Pinecone 연결 테스트

```python
# test_pinecone.py
from rag.pinecone_client import get_pinecone_client

client = get_pinecone_client()

# 검색 테스트
results = client.search("allergen assessment soybean")

print(f"✅ {len(results)}개 문서 발견")
for i, doc in enumerate(results, start=1):
    print(f"\n{i}. {doc['source']} (p.{doc['page']}) - 유사도: {doc['score']:.2f}")
    print(doc['text'][:200] + "...")
```

실행:
```bash
python test_pinecone.py
```

### 7.2 RAG Tool 테스트

```python
# test_rag_tool.py
from tools.rag_search import rag_search_tool

result = rag_search_tool.invoke({"query": "대두 알레르기 평가 방법"})
print(result)
```

---

## 📊 Pinecone 대시보드 확인

1. **https://app.pinecone.io** 접속

2. **Indexes** 메뉴에서 인덱스 클릭

3. **통계 확인**:
   - Total Vectors: 746 (예시)
   - Dimension: 1536
   - Storage: 2.3 MB

---

## 🎯 완료 체크리스트

- [ ] Pinecone 계정 생성
- [ ] API 키 발급 및 `.env` 설정
- [ ] 인덱스 생성 (virtual-lab-regulatory-docs)
- [ ] `pinecone-client` 패키지 설치
- [ ] `rag/pinecone_client.py` 작성
- [ ] PDF 문서 로드 (`python rag/pdf_processor.py`)
- [ ] Pinecone 대시보드에서 벡터 확인
- [ ] RAG Tool 테스트

---

## ⚠️ 문제 해결

### API 키 에러

**에러**:
```
InvalidApiKeyException
```

**해결**:
- `.env`의 `PINECONE_API_KEY` 확인
- Pinecone 대시보드에서 API 키 재발급

### 인덱스 없음

**에러**:
```
Index 'virtual-lab-regulatory-docs' not found
```

**해결**:
```python
python rag/pinecone_setup.py  # 인덱스 생성
```

### Dimension 불일치

**에러**:
```
Dimension mismatch: expected 1536, got 512
```

**해결**:
- OpenAI `text-embedding-3-small` 사용 확인 (1536 차원)
- 인덱스 dimension을 1536으로 생성

---

**Pinecone 설정 완료!** 🎉

이제 RAG 검색이 클라우드 기반으로 작동합니다.
