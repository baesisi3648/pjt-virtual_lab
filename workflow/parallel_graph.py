# @TASK P3-T1 - Parallel Meeting Architecture (LangGraph Map-Reduce)
# @SPEC Phase 3 - Parallel & Dynamic
# @TEST tests/test_parallel_workflow.py
"""LangGraph Map-Reduce 패턴 구현

3개 에이전트가 동시에 위험 분석을 수행하고 (MAP),
PI가 결과를 통합하여 최종 보고서를 생성합니다 (REDUCE).

## 아키텍처

```
[MAP 단계] - 병렬 실행 (asyncio.gather)
    ├─ Scientist Agent (GPT-4o-mini) → 기술적 위험 분석
    ├─ Critic Agent (GPT-4o) → 규제 검증 관점 분석
    └─ PI Agent (GPT-4o) → 정책 실행 관점 분석
         ↓
[REDUCE 단계] - 순차 실행
    └─ PI Agent (GPT-4o) → 3개 분석 통합 및 최종 보고서 생성
```

## 사용 예시

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

# result["parallel_views"] → 3개 에이전트의 분석 결과
# result["final_report"] → PI가 통합한 최종 보고서
```

## 기존 워크플로우와의 차이

- **graph.py**: Scientist → Critic → PI (순차적, 반복 가능)
- **parallel_graph.py**: [Scientist, Critic, PI] → Merge (병렬, 1회)
"""
import asyncio
from typing import Any

from langgraph.graph import StateGraph, END

from workflow.state import AgentState
from utils.llm import call_gpt4o, call_gpt4o_mini


async def analyze_as_scientist(topic: str, constraints: str) -> dict:
    """Scientist 관점에서 위험 분석

    Args:
        topic: 연구 주제
        constraints: 제약 조건

    Returns:
        dict: agent_name과 analysis가 포함된 분석 결과
    """
    from data.guidelines import RESEARCH_OBJECTIVE, CODEX_PRINCIPLES

    system_prompt = f"""
당신은 유전자편집식품(NGT)의 기술적 위험을 분석하는 과학자입니다.

## 연구 목표
{RESEARCH_OBJECTIVE}

## 국제 표준 (Codex)
{CODEX_PRINCIPLES}

주어진 주제에 대해 NGT 기술의 잠재적 위험 요소를 식별하세요.
Off-target 효과, 유전적 안정성 등 기술적 관점에서 분석하세요.
""".strip()

    user_message = f"""
연구 주제: {topic}
제약 조건: {constraints}

위 주제에 대해 기술적 위험 요소를 분석하세요.
""".strip()

    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(
        None, call_gpt4o_mini, system_prompt, user_message
    )

    return {
        "agent_name": "scientist",
        "analysis": response,
    }


async def analyze_as_critic(topic: str, constraints: str) -> dict:
    """Critic 관점에서 위험 분석

    Args:
        topic: 연구 주제
        constraints: 제약 조건

    Returns:
        dict: agent_name과 analysis가 포함된 분석 결과
    """
    from data.guidelines import CRITIQUE_RUBRIC

    system_prompt = f"""
당신은 과학적 타당성을 검증하는 비평가입니다.

## 비평 기준
{CRITIQUE_RUBRIC}

주어진 주제에 대해 규제 관점에서 중요한 위험 요소를 식별하세요.
과학적 근거, 범용성, 규제 적절성 등을 고려하세요.
""".strip()

    user_message = f"""
연구 주제: {topic}
제약 조건: {constraints}

위 주제에 대해 규제 검증 관점에서 위험 요소를 분석하세요.
""".strip()

    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(
        None, call_gpt4o, system_prompt, user_message
    )

    return {
        "agent_name": "critic",
        "analysis": response,
    }


async def analyze_as_pi(topic: str, constraints: str) -> dict:
    """PI 관점에서 위험 분석

    Args:
        topic: 연구 주제
        constraints: 제약 조건

    Returns:
        dict: agent_name과 analysis가 포함된 분석 결과
    """
    from data.guidelines import REGULATORY_TRENDS

    system_prompt = f"""
당신은 연구 프로젝트를 총괄하는 책임자(PI)입니다.

## 규제 동향
{REGULATORY_TRENDS}

주어진 주제에 대해 정책 및 실무 관점에서 중요한 위험 요소를 식별하세요.
규제 실행 가능성, 국제 조화, 이해관계자 수용성 등을 고려하세요.
""".strip()

    user_message = f"""
연구 주제: {topic}
제약 조건: {constraints}

위 주제에 대해 정책 실행 관점에서 위험 요소를 분석하세요.
""".strip()

    loop = asyncio.get_event_loop()
    response = await loop.run_in_executor(
        None, call_gpt4o, system_prompt, user_message
    )

    return {
        "agent_name": "pi",
        "analysis": response,
    }


async def _parallel_risk_analysis_async(state: AgentState) -> dict:
    """MAP 단계: 3개 에이전트가 동시에 위험 분석 수행 (비동기)

    Args:
        state: LangGraph 공유 상태

    Returns:
        dict: parallel_views가 포함된 상태 업데이트
    """
    topic = state["topic"]
    constraints = state["constraints"]

    # 3개 에이전트가 동시에 분석 수행
    results = await asyncio.gather(
        analyze_as_scientist(topic, constraints),
        analyze_as_critic(topic, constraints),
        analyze_as_pi(topic, constraints),
    )

    # 메시지 로그 추가
    messages = list(state.get("messages", []))
    messages.append({
        "role": "system",
        "content": "3개 에이전트가 병렬로 위험 분석을 완료했습니다.",
    })

    return {
        "parallel_views": list(results),
        "messages": messages,
    }


def parallel_risk_analysis(state: AgentState) -> dict:
    """MAP 단계: 3개 에이전트가 동시에 위험 분석 수행 (동기 래퍼)

    Args:
        state: LangGraph 공유 상태

    Returns:
        dict: parallel_views가 포함된 상태 업데이트
    """
    return asyncio.run(_parallel_risk_analysis_async(state))


def merge_parallel_views(state: AgentState) -> dict:
    """REDUCE 단계: PI가 병렬 분석 결과를 통합

    Args:
        state: LangGraph 공유 상태

    Returns:
        dict: final_report가 포함된 상태 업데이트
    """
    from agents.critic import merge_views

    # 병렬 분석 결과 수집
    views = state.get("parallel_views", [])

    # 1단계: Critic의 merge_views 로직으로 의견 통합
    analysis_texts = [view["analysis"] for view in views]
    merged_analysis = merge_views(analysis_texts)

    # 2단계: PI에게 통합된 분석을 기반으로 최종 보고서 작성 요청
    system_prompt = """
당신은 연구 프로젝트 총괄 책임자(PI)입니다.

3명의 전문가(과학자, 비평가, 정책 전문가)가 각자의 관점에서 위험 분석을 완료했습니다.
이들의 분석이 이미 통합되었으며, 다음 원칙에 따라 필터링되었습니다:
- 중복 제거 완료
- 보수적 안전 기준 선택 (조건부 > 필수 > 필요 > 선택 > 면제)
- 과학적 근거 기반 의견 우선

통합된 분석을 바탕으로 최종 보고서를 작성하세요.

## 보고서 포맷 (Markdown)
```
# 유전자편집식품 표준 안전성 평가 프레임워크 (Final Report)

## 1. 개요
(연구 목적 및 범위 설명)

## 2. 공통 위험 식별 (General Risk Profile)
(통합된 위험 요소 - 중복 제거 및 우선순위화 완료)

## 3. 최소 제출 자료 요건 (Minimum Data Requirements)
- 필수 제출: ...
- 조건부 제출: ...
- 면제 가능: ...

## 4. 결론 및 제언
(규제 당국을 위한 제언)
```
""".strip()

    # 각 전문가의 원본 분석 결과도 참고용으로 제공
    original_views_text = "\n\n".join([
        f"[{view['agent_name'].upper()} 원본 분석]\n{view['analysis']}"
        for view in views
    ])

    user_message = f"""
연구 주제: {state['topic']}
제약 조건: {state['constraints']}

## 통합된 분석 (Merged Analysis)
{merged_analysis}

## 참고: 원본 분석 (Original Views)
{original_views_text}

위 통합된 분석을 기반으로 최종 보고서를 작성하세요.
""".strip()

    final_report = call_gpt4o(system_prompt, user_message)

    # 메시지 로그 추가
    messages = list(state.get("messages", []))
    messages.append({
        "role": "pi",
        "content": "병렬 분석 결과를 Critic 통합 로직으로 필터링하고 최종 보고서를 작성했습니다.",
    })

    return {
        "final_report": final_report,
        "messages": messages,
    }


def create_parallel_workflow():
    """LangGraph Map-Reduce 워크플로우 생성 및 컴파일

    그래프 구조:
        parallel_analysis (MAP) -> merge (REDUCE) -> END

    Returns:
        CompiledStateGraph: 컴파일된 LangGraph 워크플로우
    """
    workflow = StateGraph(AgentState)

    # 노드 추가
    workflow.add_node("parallel_analysis", parallel_risk_analysis)
    workflow.add_node("merge", merge_parallel_views)

    # 엣지 설정
    workflow.set_entry_point("parallel_analysis")
    workflow.add_edge("parallel_analysis", "merge")
    workflow.add_edge("merge", END)

    return workflow.compile()
