## 1. 프로젝트 개요 (Overview)

- **프로젝트명**: Virtual Lab for NGT Safety Framework (Production)
- **목표**: MVP의 논리 검증을 넘어, **자율적 리서치(Web Search)**와 **동적 팀 구성(Dynamic Team)**을 통해 실제 연구자 수준의 심도 있는 '표준 안전성 평가 프레임워크'를 도출하는 서비스.
- **핵심 차별점**:
    1. **Autonomous**: 에이전트가 스스로 필요한 최신 자료를 웹에서 검색.
    2. **Dynamic**: 연구 주제의 뉘앙스에 따라 PI가 적합한 전문가(독성학자, 분자생물학자 등)를 그때그때 채용.
    3. **Robust**: 병렬 회의(Parallel Meetings)를 통해 편향되지 않은 강건한 결론 도출.

## 2. 시스템 아키텍처 (Advanced Architecture)

### 2.1 기술 스택 업그레이드 (Tech Stack Migration)

MVP(Streamlit)에서 상용 서비스 수준으로 전환한다.

| 구분 | MVP | **Production (Final)** |
| --- | --- | --- |
| **Frontend** | Streamlit | **Next.js (React) + Tailwind CSS** (반응형 웹, 보고서 에디터) |
| **Backend** | FastAPI (Basic) | **FastAPI (Async) + Celery/Redis** (장시간 작업 비동기 처리) |
| **Database** | 없음 (Memory) | **PostgreSQL** (이력 저장), **ChromaDB** (RAG 벡터 저장소) |
| **Search** | 없음 | **Tavily API** or **Google Custom Search API** |
| **Agent Ops** | LangGraph | **LangGraph + LangSmith** (Tracer & Evaluation) |

### 2.2 동적 에이전트 오케스트레이션 (Dynamic Orchestration)

고정된 3명의 에이전트(MVP)를 넘어, 상황에 맞춰 팀을 짠다.

1. **PI (Principal Investigator)**:
    - 사용자의 복잡한 요구사항("대두의 알레르기성을 중점적으로 본 NGT 평가 틀")을 분석.
    - **[Action]**: "이번 연구엔 '알레르기 전문가'와 '식물 육종학자'가 필요하다"고 판단하고 에이전트 프로필(JSON) 생성.
2. **Specialist Generators (Factory)**:
    - PI가 정의한 프로필을 받아, 해당 분야에 특화된 System Prompt를 가진 LLM 인스턴스를 즉시 생성.

## 3. 핵심 기능 상세 (Core Features)

### 3.1 자율 검색 및 RAG (Research & Retrieval)

에이전트는 "모르는 게 있으면 찾아서" 답한다.

- **Vector DB (Ground Truth)**:
    - Codex, FDA, EFSA, 식약처 가이드라인 등 '절대 기준' 문서는 벡터 DB에 저장하여 **RAG**로 참조.
    - *목적*: 환각 방지, 법적 근거 확보.
- **Web Search (Active Research)**:
    - "최신 CRISPR-Cas9 오프타겟 부작용 논문", "2025년 영국 NGT 법안 통과 여부" 등 최신 동향 검색.
    - *도구*: Tavily API (LLM에 최적화된 검색 결과 제공).

### 3.2 병렬 회의 시스템 (Parallel Meetings for Robustness)

[cite_start]논문의 핵심 기능인 '다양성 확보'를 구현한다. [cite: 1417-1420]

- **Risk Identification Phase**:
    - 동일한 주제에 대해 3개의 서로 다른 에이전트(또는 높은 Temperature의 동일 에이전트)가 동시에 위험 요소를 분석.
    - **Agent A**: "알레르기가 제일 위험해."
    - **Agent B**: "환경 방출 시 생태계 교란이 문제야."
    - **Agent C**: "비의도적 단백질 생성이 핵심이야."
- **Merge & Synthesis**:
    - PI 에이전트가 3개의 의견을 취합하여 **"중복은 제거하고, 가장 보수적인 안전 기준"**으로 통합.

### 3.3 사용자 인터페이스 (React Frontend)

- **Live Process View**: 에이전트가 "검색 중...", "회의 중...", "비평 중..."인 상태를 실시간 타임라인으로 시각화.
- **Interactive Report**: 최종 생성된 마크다운 보고서를 사용자가 직접 클릭하여 수정하거나, 특정 문단에 대해 "재검토" 요청 가능.

## 4. 데이터 전략 (Data Strategy)

### 4.1 Knowledge Base 구축

사용자가 제공한 PDF들을 체계적인 데이터베이스로 변환한다.

- **Regulatory Documents**: PDF 파싱 -> 청크(Chunking) -> 임베딩 -> ChromaDB 저장.
- **Reference Cases**: 기승인된 유전자편집식품 사례(GABA 토마토 등) DB화.

### 4.2 검색 전략 (Search Policy)

에이전트가 무분별하게 웹을 믿지 않도록 제약을 건다.

- **Trusted Domains**: `.gov`, `.org`, `nature.com`, `sciencedirect.com` 등 신뢰할 수 있는 도메인 우선 검색.
- **Citation Rule**: 웹 검색 결과를 인용할 때는 반드시 `[출처: URL]`을 명시하도록 강제.

## 5. 단계별 구현 로드맵 (Phased Implementation)

### Phase 1: Knowledge Injection (MVP 직후)

- **목표**: RAG 시스템 구축.
- **작업**:
    - 제공된 규제 가이드라인 PDF를 벡터 DB에 적재.
    - Scientist 에이전트가 질문 시 DB에서 관련 조항을 꺼내오도록 연결.

### Phase 2: Eyes & Ears (Web Search)

- **목표**: 외부 정보 검색 능력 부여.
- **작업**:
    - Tavily API 연동.
    - 에이전트에게 `search_tool` 권한 부여 및 "필요할 때만 검색하라"는 로직 구현.

### Phase 3: The Brain (Parallel & Dynamic)

- **목표**: 논문급 추론 능력 확보.
- **작업**:
    - LangGraph의 `Map-Reduce` 패턴을 사용하여 병렬 회의 구현.
    - PI의 프롬프트를 고도화하여 하위 에이전트 정의(Define) 및 생성(Spawn) 로직 구현.

### Phase 4: The Face (UI Overhaul)

- **목표**: 사용자 친화적 서비스.
- **작업**:
    - Next.js 프로젝트 세팅.
    - FastAPI와 연동.
    - 실시간 스트리밍(Streaming Response) 구현.

## 6. 시나리오 예시 (End-User Experience)

1. **입력**: 준혁 님이 "대두(Soybean)의 올레산 함량을 높인 유전자편집 작물의 안전성 평가 틀을 짜줘."라고 입력.
2. **팀 구성 (PI)**: "작물 대사 경로가 바뀌었으니 '식물 대사체학 전문가'와 '영양학자'를 팀에 추가하겠습니다." (동적 생성)
3. **검색 (Agents)**: "최근 고올레산 대두 승인 사례를 검색합니다..." (Tavily 검색)
4. **병렬 분석**:
    - 대사체학자: "기존 대두와의 영양 성분 동등성 입증 필요."
    - 영양학자: "지방산 조성 변화에 따른 안전성 데이터 필요."
5. **비평 및 통합**: Critic이 "동물 실험은 불필요해 보임. 영양 성분 분석표로 대체 가능"이라고 제안 -> PI 수용.
6. **결과**: 대두 맞춤형 표준 평가 가이드라인 리포트 생성.

---