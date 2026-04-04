# Virtual Lab Final - TASKS.md

> **프로젝트**: Virtual Lab for NGT Safety Framework (Production)
> **목표**: MVP → Production 업그레이드 (Dynamic Team + Autonomous Research + Parallel Meetings)
> **생성일**: 2026-02-08

---

## 📊 Phase Overview

| Phase | 제목 | 핵심 목표 | 태스크 수 |
|-------|------|-----------|----------|
| **P0** | Project Setup | PostgreSQL + ChromaDB + Redis 환경 구축 | 5 |
| **P1** | Knowledge Injection | RAG 시스템 구축 (벡터 DB + 규제 문서) | 4 |
| **P2** | Eyes & Ears | Web Search 연동 (Tavily API) | 4 |
| **P3** | The Brain | 병렬 회의 + 동적 팀 구성 | 6 |
| **P4** | The Face | Next.js UI + 실시간 스트리밍 | 5 |

**Total**: 24 Tasks

---

## Phase 0: Project Setup

### P0-T1: Database Infrastructure Setup
**목표**: PostgreSQL + ChromaDB 컨테이너 환경 구축

**작업**:
- [ ] `docker-compose.yml` 작성
  - PostgreSQL (세션 이력 저장)
  - ChromaDB (벡터 저장소)
  - Redis (Celery 백엔드)
- [ ] `init.sql` 작성 (sessions, reports 테이블)
- [ ] 헬스체크 스크립트 작성

**검증**:
```bash
docker-compose up -d
docker-compose ps  # 3개 컨테이너 모두 healthy
```

**차단**: 없음

---

### P0-T2: Backend Dependencies Update
**목표**: Production 의존성 추가

**작업**:
- [ ] `requirements.txt` 업데이트
  ```
  chromadb>=0.4.0
  psycopg2-binary>=2.9.0
  sqlalchemy>=2.0.0
  celery>=5.3.0
  redis>=5.0.0
  tavily-python>=0.3.0
  langsmith>=0.1.0
  ```
- [ ] 가상환경 재생성 테스트

**검증**:
```bash
pip install -r requirements.txt
python -c "import chromadb; import tavily"
```

**차단**: 없음

---

### P0-T3: Environment Configuration
**목표**: 환경 변수 관리 강화

**작업**:
- [ ] `.env.example` 업데이트
  ```
  POSTGRES_URL=postgresql://...
  CHROMA_HOST=localhost
  CHROMA_PORT=8001
  TAVILY_API_KEY=tvly-...
  LANGSMITH_API_KEY=lsv2_...
  REDIS_URL=redis://localhost:6379
  ```
- [ ] `config.py` 작성 (Pydantic Settings)
- [ ] Secrets 검증 로직 추가

**검증**:
```python
from config import settings
assert settings.TAVILY_API_KEY.startswith("tvly-")
```

**차단**: 없음

---

### P0-T4: Database Models
**목표**: SQLAlchemy ORM 모델 정의

**작업**:
- [ ] `models/session.py` 작성
  ```python
  class Session(Base):
      id: UUID
      user_query: Text
      final_report: Text
      created_at: DateTime
  ```
- [ ] `models/agent_log.py` 작성 (에이전트 행동 추적)
- [ ] Alembic 마이그레이션 초기화

**검증**:
```bash
alembic revision --autogenerate -m "init"
alembic upgrade head
```

**차단**: P0-T1 (DB 실행 필요)

---

### P0-T5: Celery Task Queue Setup
**목표**: 비동기 작업 처리 인프라

**작업**:
- [ ] `celery_app.py` 작성
  ```python
  app = Celery('virtual_lab', broker='redis://...')
  ```
- [ ] `tasks/research_task.py` 작성 (장시간 연구 작업)
- [ ] Celery worker 실행 스크립트

**검증**:
```bash
celery -A celery_app worker --loglevel=info
# 테스트 태스크 submit
```

**차단**: P0-T1 (Redis 필요)

---

## Phase 1: Knowledge Injection (RAG System)

### P1-T1: ChromaDB Collection Setup
**목표**: 규제 문서용 벡터 컬렉션 생성

**작업**:
- [ ] `rag/chroma_client.py` 작성
  ```python
  client = chromadb.HttpClient(host=CHROMA_HOST)
  collection = client.get_or_create_collection("regulatory_docs")
  ```
- [ ] Embedding 모델 선택 (OpenAI text-embedding-3-small)
- [ ] 메타데이터 스키마 정의

**검증**:
```python
collection.count()  # 0 (초기 상태)
```

**차단**: P0-T1 (ChromaDB 실행 필요)

---

### P1-T2: PDF Processing Pipeline
**목표**: PDF → 청크 → 임베딩 → 저장

**작업**:
- [ ] `rag/pdf_processor.py` 작성
  - PyPDF2로 텍스트 추출
  - RecursiveCharacterTextSplitter (chunk_size=1000)
- [ ] `data/regulatory/` 폴더에 샘플 PDF 준비
- [ ] 배치 임베딩 함수 작성

**검증**:
```bash
python rag/pdf_processor.py --file data/regulatory/codex_guideline.pdf
# ChromaDB에 500개 청크 저장 확인
```

**차단**: P1-T1

---

### P1-T3: RAG Retrieval Function
**목표**: 쿼리 → 관련 문서 검색

**작업**:
- [ ] `rag/retriever.py` 작성
  ```python
  def retrieve(query: str, top_k=5) -> List[Document]:
      results = collection.query(query_texts=[query], n_results=top_k)
      return results
  ```
- [ ] Reranking 로직 추가 (옵션)
- [ ] Citation 포맷팅 함수

**검증**:
```python
docs = retrieve("What is substantial equivalence?")
assert len(docs) == 5
assert "Codex" in docs[0].metadata['source']
```

**차단**: P1-T2

---

### P1-T4: Agent RAG Integration
**목표**: Scientist 에이전트에 RAG Tool 추가

**작업**:
- [ ] `agents/scientist.py` 수정
  ```python
  tools = [rag_search_tool]  # LangChain Tool로 래핑
  ```
- [ ] System Prompt 업데이트
  - "관련 규제를 먼저 검색하세요"
- [ ] RAG 히트 여부 로깅

**검증**:
```python
response = scientist.invoke("대두 알레르기 평가 방법은?")
assert "[출처: Codex Guideline]" in response
```

**차단**: P1-T3

---

## Phase 2: Eyes & Ears (Web Search)

### P2-T1: Tavily API Client
**목표**: Tavily 검색 클라이언트 구현

**작업**:
- [ ] `search/tavily_client.py` 작성
  ```python
  from tavily import TavilyClient
  client = TavilyClient(api_key=TAVILY_API_KEY)
  ```
- [ ] Domain 필터링 설정
  - include_domains: [".gov", "nature.com", "sciencedirect.com"]
- [ ] Rate limiting 처리

**검증**:
```python
results = client.search("CRISPR off-target effects 2025")
assert len(results['results']) > 0
```

**차단**: P0-T3 (API Key 필요)

---

### P2-T2: Search Tool for Agents
**목표**: LangChain Tool로 래핑

**작업**:
- [ ] `tools/web_search.py` 작성
  ```python
  @tool
  def web_search(query: str) -> str:
      """최신 논문 및 규제 동향 검색"""
      results = tavily_client.search(query)
      return format_results(results)
  ```
- [ ] Citation Rule 강제 (출처 URL 포함)
- [ ] 검색 결과 캐싱 (Redis)

**검증**:
```python
result = web_search.invoke("Calyxt high oleic soybean FDA approval")
assert "calyxt.com" in result or "fda.gov" in result
```

**차단**: P2-T1

---

### P2-T3: Agent Search Integration
**목표**: 모든 에이전트에 검색 권한 부여

**작업**:
- [ ] `agents/pi.py` - tools 업데이트
- [ ] `agents/scientist.py` - tools 업데이트
- [ ] `agents/critic.py` - tools 업데이트
- [ ] System Prompt 수정
  - "최신 정보가 필요하면 web_search를 사용하세요"

**검증**:
```python
response = pi.invoke("2025년 EU NGT 법안 통과 여부")
# 실제 웹 검색 후 답변 확인
```

**차단**: P2-T2

---

### P2-T4: Search Observability
**목표**: 검색 행위 추적 (LangSmith)

**작업**:
- [ ] LangSmith 트레이싱 활성화
  ```python
  from langsmith import trace
  @trace
  def web_search(...):
  ```
- [ ] 검색 쿼리 로깅 (DB 저장)
- [ ] 대시보드 확인 가능 여부 검증

**검증**:
```
LangSmith UI에서 검색 쿼리 확인
```

**차단**: P2-T3

---

## Phase 3: The Brain (Parallel & Dynamic)

### P3-T1: Parallel Meeting Architecture
**목표**: LangGraph Map-Reduce 패턴 구현

**작업**:
- [ ] `workflow/parallel_graph.py` 작성
  ```python
  def parallel_risk_analysis(state):
      # 3개 에이전트가 동시에 위험 분석
      futures = [agent_a.ainvoke(), agent_b.ainvoke(), agent_c.ainvoke()]
      results = await asyncio.gather(*futures)
      return {"parallel_views": results}
  ```
- [ ] Merge 로직 구현 (PI가 통합)
- [ ] 노드 간 의존성 정의

**검증**:
```python
result = await parallel_graph.ainvoke({"query": "대두 위험 요소"})
assert len(result['parallel_views']) == 3
```

**차단**: 없음 (기존 graph.py 리팩토링)

---

### P3-T2: Dynamic Agent Factory
**목표**: PI가 전문가 프로필 생성

**작업**:
- [ ] `agents/factory.py` 작성
  ```python
  def create_specialist(profile: dict) -> Agent:
      """
      profile = {
          "role": "Plant Metabolomics Expert",
          "focus": "fatty acid composition",
          "tools": ["rag_search", "web_search"]
      }
      """
      system_prompt = generate_prompt(profile)
      return Agent(llm=llm, system=system_prompt, tools=tools)
  ```
- [ ] 프로필 템플릿 정의

**검증**:
```python
expert = create_specialist({"role": "Allergy Specialist"})
response = expert.invoke("대두 P34 단백질 분석")
# 전문적인 답변 확인
```

**차단**: 없음

---

### P3-T3: PI Decision Logic
**목표**: PI가 쿼리 분석 후 팀 구성 결정

**작업**:
- [ ] `agents/pi.py` 수정
  ```python
  def decide_team(user_query: str) -> List[dict]:
      """
      LLM에게 "이 쿼리에 필요한 전문가는?"이라고 물어봄
      return [
          {"role": "Metabolomics Expert", "focus": "lipid analysis"},
          {"role": "Nutrition Toxicologist", ...}
      ]
      """
  ```
- [ ] 기본 팀 vs 동적 팀 분기 로직

**검증**:
```python
team = decide_team("고올레산 대두 안전성 평가")
assert any("Metabol" in expert['role'] for expert in team)
```

**차단**: P3-T2

---

### P3-T4: Dynamic Workflow Execution
**목표**: 결정된 팀으로 워크플로우 실행

**작업**:
- [ ] `workflow/dynamic_graph.py` 작성
  ```python
  def build_graph(team_profiles: List[dict]):
      # 팀 구성에 맞춰 그래프 동적 생성
      specialists = [create_specialist(p) for p in team_profiles]
      graph.add_node("parallel_meeting", parallel_func(specialists))
      return graph.compile()
  ```
- [ ] 기존 graph.py와 통합

**검증**:
```python
graph = build_graph([...])
result = await graph.ainvoke({"query": "..."})
```

**차단**: P3-T3

---

### P3-T5: Critic Merge Logic
**목표**: 병렬 의견 통합 강화

**작업**:
- [ ] `agents/critic.py` 수정
  ```python
  def merge_views(views: List[str]) -> str:
      """
      - 중복 제거
      - 가장 보수적 안전 기준 선택
      - 근거 부족한 의견 기각
      """
  ```
- [ ] Conflict Resolution 규칙 정의

**검증**:
```python
merged = critic.merge_views([view_a, view_b, view_c])
assert "동물 실험 불필요" in merged  # 합리적 합의
```

**차단**: P3-T1

---

### P3-T6: End-to-End Parallel Test
**목표**: 전체 Brain 시스템 통합 테스트

**작업**:
- [ ] `tests/test_parallel_brain.py` 작성
  - 쿼리: "고올레산 대두 안전성 평가"
  - 예상: 대사체학자 + 영양학자 생성
  - 병렬 회의 실행
  - 최종 통합 보고서 생성
- [ ] 5분 이내 실행 시간 검증

**검증**:
```bash
pytest tests/test_parallel_brain.py -v
```

**차단**: P3-T4, P3-T5

---

## Phase 4: The Face (Next.js UI)

### P4-T1: Next.js Project Setup
**목표**: React 프론트엔드 초기화

**작업**:
- [ ] `frontend/` 폴더 생성
  ```bash
  npx create-next-app@latest frontend --typescript --tailwind
  ```
- [ ] FastAPI CORS 설정
- [ ] Proxy 설정 (Next.js → FastAPI)

**검증**:
```bash
cd frontend && npm run dev
# http://localhost:3000 접속 확인
```

**차단**: 없음

---

### P4-T2: Live Process Timeline
**목표**: 에이전트 상태 실시간 시각화

**작업**:
- [ ] `components/ProcessTimeline.tsx` 작성
  - Server-Sent Events (SSE) 구독
  - 타임라인 UI (Tailwind)
    - "🔍 검색 중..."
    - "🧠 회의 중..."
    - "✅ 보고서 생성 완료"
- [ ] FastAPI SSE 엔드포인트 추가

**검증**:
```tsx
// 실시간 업데이트 확인
[12:01] PI: 팀 구성 중...
[12:02] 대사체학자: 웹 검색 중...
[12:03] 병렬 회의 시작...
```

**차단**: P4-T1

---

### P4-T3: Interactive Report Editor
**목표**: 마크다운 보고서 수정 가능

**작업**:
- [ ] `components/ReportEditor.tsx` 작성
  - React Markdown 렌더링
  - 인라인 수정 모드
  - "재검토 요청" 버튼 (특정 섹션)
- [ ] FastAPI 재검토 API 추가
  ```python
  POST /api/report/regenerate
  {"section": "위험 식별", "feedback": "알레르기 더 자세히"}
  ```

**검증**:
```
사용자가 "알레르기" 섹션 클릭 → 재검토 요청 → 업데이트된 내용 반영
```

**차단**: P4-T1

---

### P4-T4: FastAPI Streaming Response
**목표**: 보고서 생성 중 점진적 출력

**작업**:
- [ ] `server.py` 수정
  ```python
  @app.post("/api/research/stream")
  async def stream_research():
      async def event_generator():
          async for chunk in graph.astream(...):
              yield f"data: {json.dumps(chunk)}\n\n"
      return StreamingResponse(event_generator())
  ```
- [ ] Frontend에서 청크 수신 처리

**검증**:
```
보고서가 문단별로 실시간으로 화면에 나타남
```

**차단**: P4-T2

---

### P4-T5: Production Deployment
**목표**: Docker Compose 전체 스택 배포

**작업**:
- [ ] `docker-compose.prod.yml` 작성
  - frontend (Next.js build)
  - backend (FastAPI)
  - postgres, chromadb, redis
- [ ] Nginx 리버스 프록시 설정
- [ ] 환경 변수 검증 스크립트

**검증**:
```bash
docker-compose -f docker-compose.prod.yml up -d
curl http://localhost/api/health  # 200 OK
curl http://localhost  # Next.js 화면 로드
```

**차단**: P4-T4

---

## 🎯 실행 가이드

### 1. 순차 실행 (권장)
```bash
# Phase 0 완료 후 Phase 1, 순차 진행
```

### 2. 병렬 실행 가능 구간
- P1-T1, P1-T2 (동시 작업 가능)
- P2-T1, P2-T2 (동시 작업 가능)
- P4-T1, P4-T2 (동시 작업 가능)

### 3. 크리티컬 패스
```
P0-T1 → P1-T1 → P1-T2 → P1-T3 → P1-T4
                                 ↓
P2-T1 → P2-T2 → P2-T3 → P3-T1 → P3-T6
                                 ↓
P4-T1 → P4-T2 → P4-T4 → P4-T5
```

---

## 📚 참고 문서

- [MVP README](./README.md)
- [virtual_lab_final.md](./virtual_lab_final.md) - 상세 기획
- [virtual_lab_script.md](./virtual_lab_script.md) - 시나리오

---

**생성 도구**: tasks-generator v2.0
**생성 시각**: 2026-02-08 12:45 KST
