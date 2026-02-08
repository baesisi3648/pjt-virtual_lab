# @TASK P2-R1-T1 - Scientist (Risk Identifier) 에이전트 구현
# @SPEC TASKS.md#P2-R1-T1
# @TEST tests/test_agents.py::TestScientist
"""Scientist (Risk Identifier) Agent - GPT-4o-mini

NGT 식품의 잠재적 위험 요소를 식별하고, 안전성 입증을 위한
최소 제출 자료 목록을 작성하는 과학 전문가 에이전트입니다.
"""
from langchain_core.messages import SystemMessage, HumanMessage

from data.guidelines import RESEARCH_OBJECTIVE, CODEX_PRINCIPLES, REGULATORY_TRENDS
from utils.llm import get_gpt4o_mini
from workflow.state import AgentState


SYSTEM_PROMPT = f"""
당신은 유전자편집식품(NGT)의 안전성 위험 요소를 식별하는 과학 전문가입니다.

## 연구 목표
{RESEARCH_OBJECTIVE}

## 국제 표준 (Codex)
{CODEX_PRINCIPLES}

## 규제 동향
{REGULATORY_TRENDS}

## 당신의 임무
주어진 연구 주제에 대해 NGT 기술 자체의 특성(Off-target 효과 등)에 기반한 잠재적 위험 요소를 식별하고,
안전성을 입증하기 위해 필요한 자료 목록을 작성하세요.

**중요**: 특정 제품이 아닌 NGT 카테고리 전체에 적용 가능한 범용적 기준을 제시하세요.
""".strip()


def run_scientist(state: AgentState) -> dict:
    """Scientist 에이전트 실행

    LLM을 호출하여 NGT 식품의 위험 요소 초안을 작성합니다.
    이전 critique가 존재하면 해당 피드백을 반영하여 수정합니다.

    Args:
        state: LangGraph 공유 상태

    Returns:
        dict: 업데이트할 상태 필드 (draft, messages)
    """
    model = get_gpt4o_mini()

    # 프롬프트 구성
    user_message = f"""
연구 주제: {state['topic']}
제약 조건: {state['constraints']}

위 주제에 대해 다음을 작성하세요:
1. NGT 기술의 잠재적 위험 요소 (범용적으로)
2. 안전성 입증을 위한 최소 제출 자료 목록
""".strip()

    # 이전 비평 의견이 있으면 프롬프트에 반영
    if state.get("critique"):
        user_message += (
            f"\n\n[이전 검토 의견]\n"
            f"{state['critique'].feedback}\n"
            f"위 의견을 반영하여 수정하세요."
        )

    # LLM 호출
    response = model.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_message),
    ])

    draft = response.content

    # 메시지 로그 추가 (원본 리스트 불변성 보장)
    messages = list(state.get("messages", []))
    messages.append({
        "role": "scientist",
        "content": f"위험 요소 초안을 작성했습니다.\n\n{draft[:200]}...",
    })

    return {
        "draft": draft,
        "messages": messages,
    }
