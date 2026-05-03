# P1-T2 완료 리포트: PDF 처리 파이프라인

**Phase**: 1
**Task**: T2
**Worktree**: `worktree/phase-1-rag`
**완료 시각**: 2026-02-08

---

## 목표

PDF → 청크 → 임베딩 → ChromaDB 저장 파이프라인 구현

---

## 구현 내용

### 1. 생성된 파일

```
rag/
├── pdf_processor.py       # PDF 처리 파이프라인 (신규)
└── cli.py                 # CLI 인터페이스 (신규)

data/
└── regulatory/
    ├── sample.txt         # 테스트용 샘플 (신규)
    └── README.md          # PDF 다운로드 가이드 (신규)

tests/
└── test_pdf_processor.py  # 단위 테스트 (신규)

demo_chunking.py           # 청킹 검증 데모 (신규)
requirements.txt           # PDF 라이브러리 추가 (수정)
```

### 2. 추가된 라이브러리

```txt
pypdf>=4.0.0                    # PDF 텍스트 추출
langchain-text-splitters>=0.0.1 # 청크 분할
```

### 3. 핵심 기능

#### `rag/pdf_processor.py`

```python
def extract_text_from_pdf(pdf_path: str) -> str:
    """PyPDF로 PDF 텍스트 추출"""
    # - 파일 존재 확인
    # - 페이지별 텍스트 추출
    # - 빈 PDF 검증

def chunk_text(text: str, chunk_size=1000, chunk_overlap=200) -> list[str]:
    """RecursiveCharacterTextSplitter로 청크 분할"""
    # - 단락 구조 보존 (\n\n, \n, ". ", " " 순서로 분할)
    # - 청크 크기 및 오버랩 설정

def process_pdf(pdf_path, source, document_type, year, ...) -> dict:
    """PDF 파일 처리 및 ChromaDB 저장"""
    # 1. PDF → 텍스트 추출
    # 2. 텍스트 → 청크 분할
    # 3. 청크 → 임베딩 생성 (배치 처리)
    # 4. ChromaDB 저장 (메타데이터 포함)

def process_text_file(text_path, ...) -> dict:
    """텍스트 파일 처리 (테스트용)"""
    # PDF 대신 .txt 파일 지원
```

#### `rag/cli.py`

```bash
# 명령어 예시
python -m rag.cli process --file data/regulatory/codex.pdf --source Codex --year 2023
python -m rag.cli query "NGT safety assessment"
python -m rag.cli stats
```

**주요 옵션:**
- `--chunk-size`: 청크 최대 크기 (기본값: 1000)
- `--chunk-overlap`: 청크 간 오버랩 (기본값: 200)
- `--batch-size`: 임베딩 배치 크기 (기본값: 100)

---

## 테스트 결과

### 단위 테스트 (TDD)

```bash
cd worktree/phase-1-rag
pytest tests/test_pdf_processor.py -v
```

**결과**: ✅ 11 passed in 20.42s

| 테스트 클래스 | 테스트 수 | 상태 |
|---------------|-----------|------|
| `TestChunkText` | 4 | ✅ PASS |
| `TestExtractTextFromPdf` | 3 | ✅ PASS |
| `TestProcessTextFile` | 2 | ✅ PASS |
| `TestProcessPdf` | 2 | ✅ PASS |

**주요 검증 항목:**
- 청크 크기 제한 (chunk_size + overlap)
- 빈 텍스트 처리
- 단락 구조 보존
- PDF 파일 없음 예외 처리
- 빈 PDF 예외 처리
- 잘못된 파라미터 검증

### 청킹 로직 검증

```bash
python demo_chunking.py
```

**결과**:

| 청크 설정 | 청크 수 | 청크 크기 범위 |
|-----------|---------|---------------|
| 500/100 | 5 | 333-471 chars |
| 1000/200 | 2 | 910-951 chars |
| 1500/300 | 2 | 565-1485 chars |

**원본 텍스트**: 1,837 characters (샘플 규제 문서)

**대규모 문서 추정:**
- 문서 크기: 100,000 chars (약 100페이지 PDF)
- 예상 청크 수: ~126 chunks (1000/200 설정)
- 예상 API 호출: 2 batches (batch_size=100)

### CLI 동작 확인

```bash
# Help 명령
python -m rag.cli --help
# ✅ 3개 명령어 표시 (process, query, stats)

# Process 명령 Help
python -m rag.cli process --help
# ✅ 7개 옵션 표시 (file, source, type, year, chunk-size, chunk-overlap, batch-size)
```

---

## 기술적 특징

### 1. 배치 임베딩 처리

```python
# 100개 청크씩 배치 처리 → API 호출 최소화
for i in range(0, len(chunks), batch_size):
    batch = chunks[i:i + batch_size]
    batch_embeddings = embed_fn(batch)
```

**효과**: 1,000개 청크 → 10번 API 호출 (vs. 1,000번)

### 2. 메타데이터 스키마

```python
{
    "source": "Codex",           # 문서 출처
    "document_type": "guideline", # 문서 유형
    "year": 2023,                # 발행 연도
    "chunk_index": 0,            # 청크 순서
    "filename": "codex_gm_foods" # 파일명
}
```

**활용**: 검색 시 필터링 (e.g., "Codex 2023년 이후 가이드라인만")

### 3. RecursiveCharacterTextSplitter

**분할 우선순위**:
1. 단락 구분 (`\n\n`)
2. 줄바꿈 (`\n`)
3. 문장 구분 (`. `)
4. 단어 구분 (` `)
5. 문자 (`""`)

**효과**: 의미 단위 보존, 검색 품질 향상

---

## ChromaDB 저장 검증 (조건부)

**주의**: ChromaDB가 실행 중이 아니므로 파일 생성 및 로직 검증까지만 완료

실제 저장 테스트 시:

```bash
# 1. Docker ChromaDB 실행
docker-compose up -d chromadb

# 2. 샘플 텍스트 처리
python -m rag.cli process \
  --file data/regulatory/sample.txt \
  --source "TestSource" \
  --type guideline \
  --year 2024

# 3. 통계 확인
python -m rag.cli stats
# Expected Output:
# Total Documents: 2 (chunk_size=1000)
# Sources: TestSource
# Years: 2024
# Types: guideline

# 4. 검색 테스트
python -m rag.cli query "NGT safety assessment" --top-k 3
# Expected: 3개 청크 반환 (관련도 순)
```

---

## 성능 추정

### 실제 규제 문서 기준

| 문서 | 예상 크기 | 청크 수 (1000/200) | API 호출 (batch=100) |
|------|-----------|-------------------|---------------------|
| Codex Guideline | 50KB | ~63 | 1 |
| FDA Guidance | 100KB | ~126 | 2 |
| EFSA Report | 200KB | ~252 | 3 |
| **Total (10 documents)** | 1MB | ~1,260 | ~13 |

**비용 추정** (OpenAI text-embedding-3-small):
- 1M 토큰당 $0.02
- 1,260 청크 × 평균 250 토큰 = 315,000 토큰
- 비용: ~$0.006 (매우 저렴)

---

## 다음 단계 (Phase 1 - T3)

1. **RAG 검색 함수 구현**
   ```python
   def search_regulatory_context(query: str, top_k=5) -> list[dict]:
       """쿼리와 관련된 규제 문서 검색"""
   ```

2. **컨텍스트 주입 유틸리티**
   ```python
   def inject_context(query: str, system_prompt: str) -> str:
       """검색 결과를 System Prompt에 주입"""
   ```

3. **에이전트 통합**
   - Scientist Agent가 RAG 검색 사용
   - Critic Agent가 규제 준수 검증

---

## 완료 체크리스트

- [x] `rag/pdf_processor.py` 작성
- [x] `rag/cli.py` 작성
- [x] `requirements.txt` 업데이트
- [x] `tests/test_pdf_processor.py` 작성
- [x] 단위 테스트 통과 (11/11)
- [x] 청킹 로직 검증
- [x] CLI 동작 확인
- [x] 샘플 데이터 준비
- [x] README 작성 (PDF 다운로드 가이드)
- [x] 성능 추정

---

## 특이사항

1. **ChromaDB 미실행 상태**: 파일 및 로직만 검증, 실제 저장은 Docker 실행 후 가능
2. **텍스트 파일 지원**: PDF 없이도 `.txt` 파일로 테스트 가능 (`process_text_file()`)
3. **배치 처리**: 임베딩 API 호출 최소화 (100개씩 배치)
4. **에러 처리**: ValueError는 re-raise, 기타 Exception만 래핑

---

**작성자**: Claude Code
**검토**: Backend Specialist
