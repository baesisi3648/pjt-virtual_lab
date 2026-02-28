# Virtual Lab for NGT Safety Framework (MVP)

## Project Overview
AI 에이전트 시스템 - 유전자편집식품(NGT) 표준 안전성 평가 프레임워크 도출

## Tech Stack
- Backend: FastAPI + LangGraph + OpenAI API (GPT_MODEL 단일 모델)
- Frontend: Next.js 16 + React 19 + Tailwind CSS 4
- Database: SQLite (MVP) + Pinecone (Vector DB, 316 docs)
- Tools: Tavily (Web Search + EFSA Journal Search) + LangChain RAG

## Commands
```bash
# Backend (권장)
./restart_server.bat

# 또는 수동:
python -B -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload

# Frontend
cd frontend && npm run dev

# Test
pytest tests/ -v
```

## Critical Architecture Notes

### LangGraph Workflow - 3라운드 팀 회의
- planning → researching → critique → pi_summary → [check_round]
- round < 3: increment_round → round_revision → critique (루프)
- round >= 3: final_synthesis → END
- 모든 에이전트가 3라운드 팀 회의에 참여
- StateGraph로 워크플로우 오케스트레이션
- LangChain @tool decorator로 RAG/Web Search 도구 정의

### OpenAI Direct Calls
- `utils/llm.py`: httpx로 OpenAI API 직접 호출
- Agents: `call_gpt()` 단일 함수 사용 (env `GPT_MODEL`, 기본값 `gpt-4o`)
- `call_gpt4o()` / `call_gpt4o_mini()`는 `call_gpt()`의 alias로 하위 호환성 유지
- **NO** `bind_tools()`, **NO** `ChatOpenAI` in agents
- Tools (RAG/Web Search/EFSA Search)는 prompt injection 방식으로 호출

### 보고서 개편 (v2)
- 10팀 통계적 선별: PI가 10회 독립적 팀 구성 → 빈도 분석 → 최종 선정
- 전문가 자기소개: 선별된 전문가별 2-3문장 자기소개 생성
- 연구 아젠다: 5대 핵심 질문이 에이전트 프롬프트에 주입됨
- 발화 통계: 에이전트별 발화 횟수/글자수를 보고서에 포함
- Mermaid Decision Tree: SDN-1/2/3/ODM 의사결정 흐름도
- EFSA Journal 검색: efsa.onlinelibrary.wiley.com 전용 검색

### Windows Development
- `__pycache__` 캐시가 구 코드를 로드할 수 있음
- `restart_server.bat`이 자동으로 프로세스 종료 + 캐시 삭제
- `python -B` 플래그로 .pyc 생성 방지

## Lessons Learned

### tool_calls Error (RESOLVED)
- **근본 원인**: 이전 uvicorn 프로세스가 포트 8000에서 계속 실행
- **해결**: `restart_server.bat` 스크립트 사용
- 서버 재시작 없이 코드 수정만 하면 변경사항 미반영
- Windows에서 `kill -9`는 작동 안 함 → PowerShell의 `Stop-Process` 필요

### Frontend useEffect Infinite Loop
- callback props (onComplete, onError)를 useEffect deps에 포함 금지
- `useRef`로 callback 참조 관리
- `AbortController`로 SSE cleanup

### workflow.stream() Per-Node Output
- `workflow.stream()`은 노드별 출력 반환 (`{"node_name": {...}}`)
- 전체 state가 아니므로 직접 접근 시 KeyError
- 로컬 변수로 값 추적 필요 (예: `current_round`)

## Project Structure
```
pjt-virtual_lab/
├── agents/          # AI 에이전트 (OpenAI SDK 직접 호출)
├── workflow/        # LangGraph StateGraph
├── tools/           # RAG + Web Search (LangChain @tool)
├── frontend/        # Next.js 16 프론트엔드
├── tests/           # pytest 테스트
├── docs/            # 문서 (completion reports, setup guides)
├── scripts/         # 유틸리티 스크립트
└── worktree/        # Phase별 개발 히스토리 (보존)
```

## Phase History
- Phase 0: Project Setup (PostgreSQL, ChromaDB, Redis - 스킵)
- Phase 1: RAG System (Pinecone + PDF 로딩)
- Phase 2: Web Search (Tavily API + Observability)
- Phase 3: Dynamic Factory (PI team composition)
- Phase 4: Next.js UI (SSE 스트리밍 + 보고서 에디터)

## Quick Fixes

### Backend not loading new code?
```bash
./restart_server.bat
```

### Frontend can't reach API?
```bash
# Check backend health
curl http://localhost:8000/health
```

### Pinecone connection error?
```bash
# Check .env has:
# PINECONE_API_KEY=pcsk_...
# PINECONE_HOST=https://...
```
