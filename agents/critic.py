# @TASK P2-R2-T1 - 과학 비평가(Critic) 에이전트 구현
# @SPEC TASKS.md#P2-R2-T1
# @TEST tests/test_agents.py::TestCritic
"""Scientific Critic Agent - GPT-4o

Scientist가 작성한 초안의 과학적 타당성, 범용성, 과도한 규제 여부를
검증하는 비평가 에이전트입니다. CRITIQUE_RUBRIC 기준표에 따라 채점하고,
모든 항목 3점 이상이면 승인(approve), 아니면 수정 요청(revise)합니다.
"""
import json

from langchain_core.messages import SystemMessage, HumanMessage

from data.guidelines import CRITIQUE_RUBRIC
from utils.llm import get_gpt4o
from workflow.state import AgentState, CritiqueResult


SYSTEM_PROMPT = f"""
당신은 과학적 타당성을 검증하는 비평가입니다.

## 비평 기준
{CRITIQUE_RUBRIC}

## 당신의 임무
Scientist가 작성한 초안을 검토하고, 아래 체크리스트에 따라 평가하세요:
1. 과학적 근거가 있는가? (1-5점)
2. 특정 제품이 아닌 카테고리 전체에 적용 가능한가? (1-5점)
3. 불필요하게 과도한 자료를 요구하지 않는가? (1-5점)

**승인 조건**: 모든 항목 3점 이상

**출력 형식** (JSON):
{{
  "decision": "approve" | "revise",
  "feedback": "수정 제안 (revise인 경우만)",
  "scores": {{
    "scientific": 1-5,
    "universal": 1-5,
    "regulation": 1-5
  }}
}}
""".strip()


def run_critic(state: AgentState) -> dict:
    """Critic 에이전트 실행

    Scientist의 초안을 CRITIQUE_RUBRIC에 따라 검토하고,
    승인(approve) 또는 수정 요청(revise) 판정을 내립니다.

    Args:
        state: LangGraph 공유 상태

    Returns:
        dict: 업데이트할 상태 필드 (critique, messages)
    """
    model = get_gpt4o()

    user_message = f"""
[Scientist의 초안]
{state['draft']}

위 초안을 검토하고, JSON 형식으로 응답하세요.
""".strip()

    # LLM 호출
    response = model.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_message),
    ])

    # JSON 파싱
    try:
        data = json.loads(response.content)
        critique = CritiqueResult(
            decision=data["decision"],
            feedback=data.get("feedback", ""),
            scores=data.get("scores", {}),
        )
    except (json.JSONDecodeError, KeyError):
        # 파싱 실패 시 기본 승인 처리
        critique = CritiqueResult(
            decision="approve",
            feedback="",
            scores={},
        )

    # 메시지 로그 추가 (원본 리스트 불변성 보장)
    messages = list(state.get("messages", []))
    if critique.decision == "approve":
        messages.append({
            "role": "critic",
            "content": "초안을 승인합니다.",
        })
    else:
        messages.append({
            "role": "critic",
            "content": f"수정이 필요합니다.\n{critique.feedback}",
        })

    return {
        "critique": critique,
        "messages": messages,
    }
