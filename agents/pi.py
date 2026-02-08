# @TASK P2-R3-T1 - 연구 책임자(PI) 에이전트 구현
# @SPEC TASKS.md#P2-R3-T1
# @TEST tests/test_agents.py::TestPI
"""PI (Principal Investigator) Agent - GPT-4o

연구 프로젝트의 총괄 책임자 역할을 수행합니다.
Scientist와 Critic의 논의를 거쳐 승인된 초안을 바탕으로
최종 Markdown 보고서를 생성합니다.
"""
from langchain_core.messages import HumanMessage, SystemMessage

from utils.llm import get_gpt4o
from workflow.state import AgentState


SYSTEM_PROMPT = """
당신은 연구 프로젝트의 총괄 책임자(PI)입니다.

## 당신의 임무
Scientist와 Critic의 논의를 거쳐 승인된 초안을 바탕으로 최종 보고서를 작성하세요.

## 보고서 포맷 (Markdown)
```
# 유전자편집식품 표준 안전성 평가 프레임워크 (Final Report)

## 1. 개요
(연구 목적 및 범위 설명)

## 2. 공통 위험 식별 (General Risk Profile)
(기술적 위험 요소 나열 - Scientist 초안 기반)

## 3. 최소 제출 자료 요건 (Minimum Data Requirements)
- 필수 제출: ...
- 조건부 제출: ...
- 면제 가능: ...

## 4. 결론 및 제언
(규제 당국을 위한 제언)
```

**중요**: 명확하고 간결하게, 실무 활용 가능한 형태로 작성하세요.
반드시 위 4개 섹션을 모두 포함해야 합니다.
"""


def run_pi(state: AgentState) -> dict:
    """PI 에이전트 실행 - 최종 보고서 생성

    승인된 Scientist 초안을 바탕으로 GPT-4o를 호출하여
    4개 섹션(개요, 위험 식별, 최소 자료 요건, 결론)으로 구성된
    최종 Markdown 보고서를 생성합니다.

    Args:
        state: LangGraph 에이전트 공유 상태

    Returns:
        dict: final_report와 messages가 포함된 상태 업데이트
    """
    model = get_gpt4o()

    user_message = (
        f"연구 주제: {state['topic']}\n"
        f"제약 조건: {state['constraints']}\n\n"
        f"[승인된 초안]\n{state['draft']}\n\n"
        "위 초안을 바탕으로 최종 보고서를 Markdown 형식으로 작성하세요.\n"
        "4개 섹션(개요, 위험 식별, 최소 자료 요건, 결론)을 모두 포함해야 합니다."
    )

    response = model.invoke([
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_message),
    ])

    final_report = response.content

    # 메시지 로그 (원본 불변을 위해 copy)
    messages = state.get("messages", []).copy()
    messages.append({
        "role": "pi",
        "content": "최종 보고서를 작성했습니다.",
    })

    return {
        "final_report": final_report,
        "messages": messages,
    }
