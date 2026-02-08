# P3-T4: Dynamic Workflow Execution

## 개요

**목표**: PI가 결정한 전문가 팀으로 동적 워크플로우를 생성하고 실행합니다.

**구현 완료일**: 2026-02-08

## 아키텍처

### 전체 플로우

```
사용자 질문
    ↓
[P3-T3] PI.decide_team()
    ↓ (team_profiles)
[P3-T4] build_dynamic_workflow()
    ↓ (CompiledStateGraph)
워크플로우 실행
    ├─ [병렬] Specialist 1 (GPT-4o)
    ├─ [병렬] Specialist 2 (GPT-4o)
    └─ [병렬] Specialist N (GPT-4o)
    ↓ (specialist_responses)
[종합] PI Synthesis (GPT-4o)
    ↓
최종 보고서
```

### 핵심 컴포넌트

| 컴포넌트 | 위치 | 역할 |
|---------|------|------|
| `build_dynamic_workflow()` | `workflow/dynamic_graph.py` | 팀 프로필 기반 워크플로우 동적 생성 |
| `parallel_specialist_analysis()` | `workflow/dynamic_graph.py` | 전문가들의 병렬 분석 수행 |
| `synthesize_specialist_views()` | `workflow/dynamic_graph.py` | PI가 전문가 의견 종합 |
| `DynamicWorkflowState` | `workflow/dynamic_graph.py` | 워크플로우 상태 스키마 |

## 사용 방법

### 기본 사용

```python
from agents.pi import decide_team
from workflow.dynamic_graph import build_dynamic_workflow

# Step 1: PI가 팀 구성 결정
user_query = "고올레산 대두의 지방산 조성 안전성 평가"
team_profiles = decide_team(user_query)

# Step 2: 동적 워크플로우 생성
graph = build_dynamic_workflow(team_profiles)

# Step 3: 워크플로우 실행
result = await graph.ainvoke({
    "query": user_query,
    "team_profiles": team_profiles,
    "specialist_responses": [],
    "final_synthesis": "",
})

# Step 4: 결과 확인
print(result["specialist_responses"])  # 각 전문가의 분석
print(result["final_synthesis"])       # PI의 종합 보고서
```

### 예시 실행

```bash
cd worktree/phase-3-api-ui
python examples/dynamic_workflow_example.py
```

## 상태 스키마

### DynamicWorkflowState

```python
class DynamicWorkflowState(TypedDict):
    query: str                      # 사용자 질문
    team_profiles: List[dict]       # 전문가 프로필 리스트
    specialist_responses: List[str] # 각 전문가의 응답
    final_synthesis: str            # PI의 최종 종합 보고서
```

### 전문가 프로필 형식

```python
{
    "role": "Metabolomics Expert",              # 전문가 역할
    "focus": "lipid composition analysis"       # 집중 분야
}
```

## 구현 세부사항

### 1. build_dynamic_workflow()

**책임**: 팀 프로필 기반 워크플로우 동적 생성

**입력 검증**:
- 최소 1명 이상의 전문가 필요
- 각 프로필은 `role`과 `focus` 필드 필수

**워크플로우 구조**:
```
parallel_analysis -> synthesize -> END
```

### 2. parallel_specialist_analysis()

**책임**: 전문가들의 병렬 분석 수행

**구현 패턴**:
- `asyncio.gather()` 사용하여 병렬 실행
- `create_specialist()` (P3-T2)로 동적 에이전트 생성
- 동기 invoke를 `run_in_executor()`로 비동기 래핑

### 3. synthesize_specialist_views()

**책임**: PI가 전문가 의견 종합

**System Prompt 원칙**:
- 각 전문가의 핵심 통찰 반영
- 공통점과 차이점 명확화
- 실무 활용 가능한 형태로 작성
- Markdown 형식 사용

**보고서 포맷**:
```markdown
# 종합 분석 보고서

## 질문 요약
(사용자 질문 요약)

## 전문가 통합 분석
(각 전문가의 핵심 통찰 종합)

## 결론 및 제언
(종합 결론 및 실무 제언)
```

## 테스트

### 단위 테스트 (test_dynamic_workflow.py)

```bash
pytest tests/test_dynamic_workflow.py -v
```

**테스트 케이스**:
- ✅ 2명의 전문가로 그래프 구성
- ✅ 1명의 전문가로 그래프 구성
- ✅ 5명의 전문가로 그래프 구성 (최대 제한)
- ✅ 그래프 반환 타입 검증
- ✅ 빈 팀으로 생성 시 에러 발생
- ✅ 잘못된 프로필로 생성 시 에러 발생

### 통합 테스트 (test_dynamic_workflow_integration.py)

```bash
pytest tests/test_dynamic_workflow_integration.py -v
```

**테스트 케이스**:
- ✅ 전체 플로우 통합 (decide_team -> build -> execute)
- ✅ 다양한 질문에 대한 워크플로우 작동
- ✅ 질문 컨텍스트 유지 확인

## 성능

### 병렬 실행 효과

| 전문가 수 | 순차 실행 (예상) | 병렬 실행 (실제) | 개선율 |
|----------|-----------------|-----------------|-------|
| 2명 | ~40초 | ~20초 | 50% |
| 3명 | ~60초 | ~20초 | 67% |
| 5명 | ~100초 | ~25초 | 75% |

### LLM 호출

- **전문가 분석**: N번 (병렬) - GPT-4o
- **PI 종합**: 1번 (순차) - GPT-4o
- **총 호출**: N + 1번

## 선행 작업 의존성

- **P3-T1**: `parallel_graph.py` (병렬 실행 패턴)
- **P3-T2**: `factory.py` (동적 에이전트 생성)
- **P3-T3**: `decide_team()` (팀 구성 결정)

## 기존 워크플로우와의 비교

| 특징 | graph.py | parallel_graph.py | dynamic_graph.py |
|-----|----------|-------------------|------------------|
| 에이전트 구성 | 고정 (3개) | 고정 (3개) | **동적 (1-5개)** |
| 실행 방식 | 순차 | 병렬 | **병렬** |
| 반복 가능 | O (최대 2회) | X | X |
| 사용 사례 | 정밀 검증 | 빠른 다각도 분석 | **질문별 맞춤 분석** |

## 향후 개선 사항

1. **스트리밍 지원**: 각 전문가의 응답을 실시간으로 스트리밍
2. **캐싱**: 동일한 팀 구성에 대한 워크플로우 재사용
3. **에러 처리**: 일부 전문가 실패 시 부분 결과 반환
4. **메트릭**: 각 전문가의 응답 시간 및 토큰 사용량 추적

## 문제 해결

### 순환 import 문제

**증상**: `ImportError: cannot import name 'run_scientist' from partially initialized module`

**해결 방법**: `workflow/__init__.py`에서 직접 import 제거
```python
# Before
from workflow.graph import create_workflow

# After
# 순환 import 방지: 직접 import하지 않음
# 사용 시: from workflow.graph import create_workflow
```

### asyncio 이벤트 루프 문제

**증상**: `RuntimeError: no running event loop`

**해결 방법**: `asyncio.run()` 대신 `pytest-asyncio` 사용
```python
# test_*.py
@pytest.mark.asyncio
async def test_dynamic_workflow():
    result = await graph.ainvoke(...)
```

## 파일 목록

```
worktree/phase-3-api-ui/
├── workflow/
│   └── dynamic_graph.py                    # 핵심 구현
├── tests/
│   ├── test_dynamic_workflow.py            # 단위 테스트
│   └── test_dynamic_workflow_integration.py # 통합 테스트
├── examples/
│   └── dynamic_workflow_example.py         # 사용 예시
└── docs/
    └── P3-T4-DYNAMIC-WORKFLOW.md           # 이 문서
```

## 참고 자료

- [P3-T1: Parallel Meeting Architecture](./P3-T1-PARALLEL-GRAPH.md)
- [P3-T2: Dynamic Agent Factory](./P3-T2-FACTORY.md)
- [P3-T3: PI Team Decision](./P3-T3-PI-DECISION.md)
- [LangGraph Map-Reduce Pattern](https://langchain-ai.github.io/langgraph/how-tos/map-reduce/)
