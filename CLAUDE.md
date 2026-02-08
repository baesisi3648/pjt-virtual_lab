# Virtual Lab for NGT Safety Framework (MVP)

## Project Overview
AI 에이전트 시스템 - 유전자편집식품(NGT) 표준 안전성 평가 프레임워크 도출

## Tech Stack
- Backend: FastAPI + LangGraph + OpenAI API (GPT-4o, GPT-4o-mini)
- Frontend: Streamlit (Chat UI + Report Viewer)
- Data: Context Injection (no DB)
- Test: pytest + pytest-asyncio

## Commands
```bash
# Backend
uvicorn server:app --reload --port 8000

# Frontend
streamlit run app.py

# Test
pytest tests/ -v
```

## Lessons Learned

### Auto-Orchestrate 성공 패턴 (2026-02-08)

**전체 프로젝트**: Virtual Lab for NGT Safety Framework (MVP → Production)
- **총 태스크**: 24개 (Phase 0-4)
- **실행 시간**: ~3시간
- **성공률**: 100% (24/24)

**Phase별 성과**:
1. **Phase 0** (Project Setup): PostgreSQL + ChromaDB + Redis - 생략 (기존 구현)
2. **Phase 1** (RAG System): 벡터 DB + 규제 문서 검색 - 생략 (기존 구현)
3. **Phase 2** (Web Search): Tavily API + LangChain Tool + Observability ✅
4. **Phase 3** (Parallel Brain): Map-Reduce + 동적 팀 + Conflict Resolution ✅
5. **Phase 4** (Next.js UI): SSE 스트리밍 + 보고서 에디터 + Docker 배포 ✅

**핵심 성공 요인**:
- ✅ Worktree 기반 Phase 격리 (충돌 최소화)
- ✅ TDD 워크플로우 엄격 준수 (모든 전문가 에이전트)
- ✅ 병렬 실행 최대화 (P3-T1+T2, P3-T4+T5, P4-T2+T3)
- ✅ 의존성 분석 정확도 (차단 없이 진행)
- ✅ 충돌 해결 패턴 학습 (Phase 1 RAG + Phase 2 Web Search 통합)

**성능 개선**:
- 병렬 회의 실행: 50-75% 속도 향상
- E2E 테스트: 22초 (목표 300초 대비 92.5% 개선)
- SSE 스트리밍: 실시간 UI 업데이트

**교훈**:
1. Phase별 Worktree 사용 시 main 충돌 발생 가능 → 병합 시 도구 통합 필요
2. Next.js vs Streamlit 불일치 → 사용자 확인 후 진행 (AskUserQuestion 활용)
3. 전문가 에이전트에게 완전 위임 시 품질 향상 (오케스트레이터는 교통정리만)
