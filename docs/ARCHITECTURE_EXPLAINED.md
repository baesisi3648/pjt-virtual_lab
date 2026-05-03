# Virtual Lab 아키텍처 상세 설명

> ChromaDB, PostgreSQL, Redis의 역할과 대안

---

## 📊 각 컴포넌트의 역할

### 1. ChromaDB (Vector Database)

**역할**: RAG (Retrieval-Augmented Generation) 검색 엔진

**하는 일**:
```
1. 규제 문서 PDF를 벡터로 변환하여 저장
   - Codex 가이드라인
   - FDA 규제 문서
   - EU NGT 법안 등

2. 사용자 질문을 벡터로 변환

3. 유사도 검색으로 관련 문서 조각 찾기
   - 예: "알레르기 평가 방법" 질문
   - → Codex Guideline의 관련 섹션 반환

4. 검색된 문서를 에이전트에게 제공
```

**예시**:
```python
# 사용자: "대두 알레르기 평가 방법은?"

# ChromaDB 검색
docs = chromadb.search("allergen assessment soybean")

# 결과:
# 1. Codex Guideline (2003), Section 4.2: "Allergenicity Assessment"
# 2. FDA Guidance: "Allergen Cross-reactivity Protocol"
# 3. EU Novel Food Regulation, Article 12

# 에이전트가 이 문서들을 근거로 답변 생성
```

**없으면?**:
- ✅ 여전히 작동함 (MVP 모드)
- ❌ 규제 문서 검색 불가
- ✅ 웹 검색(Tavily)으로 대체 가능
- ❌ 내부 지식 기반 부족

---

### 2. PostgreSQL (Relational Database)

**역할**: 세션 및 이력 저장소

**하는 일**:
```
1. 연구 세션 저장
   - 사용자 질문
   - 생성된 보고서
   - 생성 시각

2. 에이전트 행동 로그
   - 어떤 에이전트가 언제 무엇을 했는지
   - Tool 사용 기록 (RAG 검색, 웹 검색)
   - 성능 메트릭

3. 히스토리 조회
   - 이전 연구 결과 재사용
   - 트렌드 분석
```

**스키마**:
```python
# models/session.py
class Session(Base):
    id: UUID                    # 세션 ID
    user_query: Text            # "CRISPR 토마토 안전성"
    final_report: Text          # 최종 생성된 보고서
    created_at: DateTime        # 2026-02-08 14:30:00

class AgentLog(Base):
    id: UUID
    session_id: UUID           # 어느 세션인지
    agent_name: str            # "Scientist", "Critic", "PI"
    action: str                # "draft_created", "tool_used"
    tool_name: str             # "rag_search", "web_search"
    duration_ms: int           # 실행 시간
```

**없으면?**:
- ✅ 여전히 작동함 (MVP 모드)
- ❌ 세션 저장 불가 (메모리만 사용)
- ❌ 히스토리 조회 불가
- ❌ 분석/로깅 불가

**SQLite 대안 가능?**
- ✅ **완전히 가능!**
- SQLite는 파이썬 내장 라이브러리
- 파일 기반이라 설치 불필요
- 작은 규모에 적합

---

### 3. Redis (In-Memory Cache)

**역할**: 캐싱 레이어

**하는 일**:
```
1. 웹 검색 결과 캐싱
   - "CRISPR off-target effects" 검색 → Redis 저장
   - 같은 질문 다시 오면 → Redis에서 즉시 반환 (Tavily API 절약)

2. Celery 작업 큐 (장시간 연구)
   - 비동기 작업 관리
   - 백그라운드 처리

3. Rate Limiting
   - API 호출 횟수 제한
```

**예시**:
```python
# 첫 검색 (5초 소요)
result = web_search("CRISPR safety 2025")
redis.set("search:CRISPR_safety_2025", result, ex=3600)  # 1시간 캐시

# 같은 검색 (0.01초 소요)
cached = redis.get("search:CRISPR_safety_2025")  # 즉시 반환!
```

**없으면?**:
- ✅ 여전히 작동함 (MVP 모드)
- ❌ 캐싱 불가 (매번 API 호출)
- ❌ 비동기 작업 불가
- 💰 API 비용 증가

---

## 🔬 RAG 검색이 사용되는 곳

### RAG를 사용하는 에이전트

#### 1. **Scientist (주 사용자)**

```python
# agents/scientist.py
from tools.rag_search import rag_search_tool
from tools.web_search import web_search

# Scientist는 두 가지 검색 도구 보유
model = get_gpt4o_mini().bind_tools([
    rag_search_tool,    # ChromaDB 검색 (내부 규제 문서)
    web_search          # Tavily API (최신 웹 정보)
])
```

**사용 시나리오**:
```
사용자: "대두 알레르기 평가 방법은?"

Scientist 사고 과정:
1. "먼저 규제 문서를 확인해야겠다"
   → rag_search_tool("allergen assessment soybean")
   → Codex Guideline 섹션 4.2 발견

2. "최신 연구도 확인하자"
   → web_search("soybean allergen assessment 2025")
   → Nature 논문 발견

3. 두 정보를 종합하여 답변 생성
```

#### 2. **Critic (검증 시 사용 가능)**

```python
# agents/critic.py
# Critic도 RAG를 사용할 수 있음 (선택적)
# "이 답변이 규제 기준에 맞는지 확인"
```

#### 3. **PI (필요 시 사용)**

```python
# agents/pi.py
# 최종 보고서 작성 시 규제 근거 확인
```

---

## 💡 RAG가 없을 때 답변 방식

### MVP 모드 (현재 설정)

**답변 소스**:
1. **LLM 자체 지식** (GPT-4o의 학습 데이터)
   - 2023년까지의 일반적인 NGT 지식
   - Codex 원칙 (유명하므로 학습됨)
   - 일반적인 안전성 평가 방법

2. **웹 검색** (Tavily API)
   - 최신 논문 (2024-2025)
   - 최신 규제 동향
   - 실시간 정보

3. **프롬프트에 주입된 가이드라인**
   ```python
   # data/guidelines.py
   CODEX_PRINCIPLES = """
   1. Substantial Equivalence
   2. Allergenicity Assessment
   3. Toxicity Testing
   4. Nutritional Assessment
   """

   # 이것이 Scientist의 시스템 프롬프트에 포함됨
   ```

**비교**:

| 질문 | RAG 있을 때 | RAG 없을 때 (MVP) |
|------|-------------|-------------------|
| "Codex 알레르기 평가 기준?" | ✅ 정확한 섹션 인용<br>`[출처: Codex Guideline (2003), p.12]` | ✅ 일반적 답변<br>"Codex는 알레르기 평가를..."<br>(웹 검색으로 보완) |
| "2025년 EU NGT 법안?" | ✅ 내부 문서 검색<br>+ 웹 검색 | ✅ 웹 검색만<br>(충분히 정확) |
| "FDA Calyxt 승인 사례?" | ✅ 내부 문서 + 웹 검색 | ✅ 웹 검색<br>(FDA 사이트에서 찾음) |

**결론**:
- RAG 없어도 웹 검색으로 대부분 해결 가능 ✅
- 단, 내부 규제 문서가 많으면 RAG 추천
- MVP는 웹 검색 + LLM 지식으로 충분

---

## 🔄 SQLite 대안 구현

### PostgreSQL → SQLite 변경 방법

#### 1. config.py 수정

```python
# config.py (현재)
POSTGRES_URL: str | None = None

# SQLite로 변경
DATABASE_URL: str = "sqlite:///./virtual_lab.db"  # 파일 기반
```

#### 2. models 그대로 사용

```python
# SQLAlchemy는 PostgreSQL과 SQLite 모두 지원
# models/session.py 수정 불필요!

from sqlalchemy import create_engine

# PostgreSQL
engine = create_engine("postgresql://user:pass@localhost/db")

# SQLite (자동 변환!)
engine = create_engine("sqlite:///./virtual_lab.db")
```

#### 3. 장단점 비교

| 항목 | PostgreSQL | SQLite |
|------|-----------|--------|
| **설치** | Docker 필요 | ✅ 내장 (설치 불필요) |
| **성능** | 대규모 (1000+ 세션) | 소규모 (100 세션) |
| **동시 접속** | ✅ 수천 명 | ⚠️ 1명 (파일 잠금) |
| **백업** | dump 명령 | ✅ 파일 복사 |
| **배포** | 서버 필요 | ✅ 파일만 배포 |
| **추천** | Production | **MVP/개발** ✅ |

#### 4. SQLite 적용 코드

```python
# config.py
class Settings(BaseSettings):
    # SQLite 모드 (기본)
    DATABASE_URL: str = "sqlite:///./virtual_lab.db"

    # PostgreSQL 모드 (Production)
    # DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/virtual_lab"

# models/base.py
from sqlalchemy import create_engine

engine = create_engine(settings.DATABASE_URL)
```

**즉시 작동!** 추가 설정 불필요 ✅

---

## 🎯 권장 구성

### 개발/테스트 (현재 MVP)
```
✅ LLM: GPT-4o (OpenAI)
✅ 웹 검색: Tavily API
❌ RAG: 비활성화 (ChromaDB 없음)
❌ DB: 비활성화 (메모리만 사용)
❌ 캐시: 비활성화 (Redis 없음)
```

### SQLite 모드 (추천)
```
✅ LLM: GPT-4o
✅ 웹 검색: Tavily API
✅ DB: SQLite (파일 기반)
❌ RAG: 선택 (필요시 ChromaDB)
❌ 캐시: 선택 (필요시 Redis)
```

### Production 모드 (완전체)
```
✅ LLM: GPT-4o
✅ 웹 검색: Tavily API
✅ RAG: ChromaDB (규제 문서 1000+)
✅ DB: PostgreSQL (세션 10,000+)
✅ 캐시: Redis (성능 최적화)
```

---

## 📝 실제 동작 예시

### RAG 있을 때

```python
# 사용자 질문
query = "대두 알레르기 평가 방법은?"

# Scientist 에이전트
1. rag_search_tool("allergen assessment soybean")
   → ChromaDB: "Codex Guideline Section 4.2" 반환

2. LLM 답변 생성
   "Codex에 따르면 알레르기 평가는 다음과 같습니다:
    1. 출처 확인 (source of genetic material)
    2. 아미노산 서열 비교 (sequence homology)
    3. 혈청학적 검사 (serum screen)
    [출처: Codex Guideline (2003), Section 4.2]"
```

### RAG 없을 때 (MVP)

```python
# 사용자 질문
query = "대두 알레르기 평가 방법은?"

# Scientist 에이전트
1. web_search("soybean allergen assessment guidelines")
   → Tavily: FDA 사이트, Nature 논문 반환

2. LLM 자체 지식 활용
   "알레르기 평가는 일반적으로:
    1. 출처 확인
    2. 서열 유사성 분석
    3. 혈청학적 검사
    [출처: https://www.fda.gov/food/...] (웹 검색 결과)"
```

**결론**: 둘 다 정확하지만, RAG가 더 구체적인 인용 제공

---

## 🛠️ 다음 단계 (선택)

### 1. SQLite로 세션 저장 활성화

```bash
# config.py 수정
DATABASE_URL: str = "sqlite:///./virtual_lab.db"

# 서버 재시작
uvicorn server:app --reload
```

### 2. ChromaDB + RAG 활성화

```bash
# ChromaDB 시작
docker run -p 8001:8000 chromadb/chroma

# PDF 문서 로드
python rag/pdf_processor.py --dir data/regulatory/
```

### 3. Redis 캐싱 활성화

```bash
# Redis 시작
docker run -p 6379:6379 redis:7-alpine
```

---

## 요약

| 컴포넌트 | 역할 | 필수? | 대안 |
|---------|------|-------|------|
| **ChromaDB** | RAG 검색 (규제 문서) | ❌ | 웹 검색 + LLM 지식 |
| **PostgreSQL** | 세션/로그 저장 | ❌ | **SQLite** ✅ 또는 메모리 |
| **Redis** | 캐싱 | ❌ | 없음 (매번 API 호출) |
| **Tavily API** | 웹 검색 | ✅ | 필수! |
| **OpenAI API** | LLM | ✅ | 필수! |

**현재 MVP 모드**: Tavily + OpenAI만으로 충분히 작동! ✅
