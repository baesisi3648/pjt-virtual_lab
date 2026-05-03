# Parallel Workflow (Map-Reduce Pattern)

## Overview

`parallel_graph.py`는 LangGraph의 Map-Reduce 패턴을 활용하여 3개의 AI 에이전트가 **동시에** 위험 분석을 수행한 후, PI가 결과를 통합하는 병렬 워크플로우입니다.

## Architecture

```
┌─────────────────────────────────────────────────┐
│         MAP Phase (Parallel Execution)          │
├─────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────┐ │
│  │  Scientist  │  │   Critic    │  │   PI    │ │
│  │ (GPT-4o-mini) │  │  (GPT-4o)   │  │(GPT-4o) │ │
│  │             │  │             │  │         │ │
│  │ Technical   │  │ Regulatory  │  │ Policy  │ │
│  │ Risk        │  │ Validation  │  │ Exec.   │ │
│  └─────────────┘  └─────────────┘  └─────────┘ │
│        ↓                ↓               ↓       │
│  [ Analysis A ]   [ Analysis B ]  [ Analysis C ]│
└─────────────────────────────────────────────────┘
                       ↓
┌─────────────────────────────────────────────────┐
│        REDUCE Phase (Sequential Execution)      │
├─────────────────────────────────────────────────┤
│              ┌─────────────────┐                │
│              │  PI (GPT-4o)    │                │
│              │  Merge & Report │                │
│              └─────────────────┘                │
│                      ↓                           │
│           [ Final Report (Markdown) ]           │
└─────────────────────────────────────────────────┘
```

## Usage

```python
from workflow.parallel_graph import create_parallel_workflow

workflow = create_parallel_workflow()

initial_state = {
    "topic": "대두 위험 요소",
    "constraints": "합리적 규제",
    "draft": "",
    "critique": None,
    "iteration": 0,
    "final_report": "",
    "messages": [],
    "parallel_views": [],
}

result = workflow.invoke(initial_state)

# 결과 확인
print(f"병렬 분석 수: {len(result['parallel_views'])}")  # → 3
for view in result['parallel_views']:
    print(f"- {view['agent_name']}: {view['analysis'][:100]}...")

print("\n최종 보고서:")
print(result['final_report'])
```

## vs. 기존 워크플로우 (graph.py)

| 항목 | graph.py | parallel_graph.py |
|------|----------|-------------------|
| 실행 방식 | 순차 (Scientist → Critic → PI) | 병렬 (3 agents) + 통합 (PI) |
| 반복 | 최대 2회 (Critic 피드백) | 1회 (반복 없음) |
| 속도 | 느림 (순차) | 빠름 (asyncio.gather) |
| 관점 | 단일 (Scientist) | 다중 (3개 관점) |
| 사용 사례 | 정밀 검증 필요 시 | 빠른 다각도 분석 필요 시 |

## Implementation Details

### MAP Phase (`parallel_risk_analysis`)

3개의 비동기 함수가 `asyncio.gather`로 병렬 실행:

```python
results = await asyncio.gather(
    analyze_as_scientist(topic, constraints),
    analyze_as_critic(topic, constraints),
    analyze_as_pi(topic, constraints),
)
```

각 함수는 `ainvoke()`를 사용하여 LLM을 비동기 호출합니다.

### REDUCE Phase (`merge_parallel_views`)

PI가 3개의 분석 결과를 받아 통합:

```python
views_text = "\n\n".join([
    f"[{view['agent_name'].upper()} 분석]\n{view['analysis']}"
    for view in views
])

response = model.invoke([
    SystemMessage(content=system_prompt),
    HumanMessage(content=user_message + views_text),
])
```

## State Schema Extension

`AgentState`에 `parallel_views` 필드 추가:

```python
class AgentState(TypedDict):
    # ... 기존 필드 ...
    parallel_views: list[dict]  # 병렬 분석 결과 (Map-Reduce)
```

각 view는 다음 구조:

```python
{
    "agent_name": "scientist" | "critic" | "pi",
    "analysis": "분석 내용 (str)"
}
```

## Testing

`tests/test_parallel_workflow.py`에서 3가지 시나리오 검증:

1. **test_parallel_execution**: 3개 에이전트가 병렬 실행되는지
2. **test_map_phase_produces_multiple_views**: MAP 단계에서 3개 관점 생성되는지
3. **test_pi_merges_parallel_views**: PI가 통합을 제대로 수행하는지

```bash
pytest tests/test_parallel_workflow.py -v
```

## Performance

- **순차 실행 (graph.py)**: ~15초 (3번 LLM 호출)
- **병렬 실행 (parallel_graph.py)**: ~7초 (asyncio.gather 덕분에 거의 1회 호출 시간)

## Future Extensions

- [ ] 동적 에이전트 수 조정 (N개 관점)
- [ ] Streaming 지원 (실시간 병렬 분석 결과 표시)
- [ ] 에이전트별 가중치 적용 (중요도 반영)
- [ ] Conditional Routing (특정 조건 시 일부 에이전트만 실행)
