# @TASK P2-R1-T1 - Scientist (Risk Identifier) 에이전트 구현
# @SPEC TASKS.md#P2-R1-T1
# @TEST tests/test_agents.py::TestScientist
"""Scientist (Risk Identifier) Agent - GPT-4o-mini

NGT 식품의 잠재적 위험 요소를 식별하고, 안전성 입증을 위한
최소 제출 자료 목록을 작성하는 과학 전문가 에이전트입니다.

P1-T4 Update: RAG Tool 통합 - 규제 문서 검색 기능 추가
"""
import logging
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage, ToolMessage

from data.guidelines import RESEARCH_OBJECTIVE, CODEX_PRINCIPLES, REGULATORY_TRENDS
from utils.llm import get_gpt4o_mini
from workflow.state import AgentState
from tools.rag_search import rag_search_tool

logger = logging.getLogger(__name__)


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

## RAG 도구 사용 규칙 (P1-T4)
답변 작성 시 반드시 다음 절차를 따르세요:
1. **먼저 rag_search_tool을 사용하여 관련 규제 문서를 검색**하세요.
2. 검색된 규제 기준을 **근거로 활용하여** 답변을 작성하세요.
3. 답변에 반드시 **출처를 [출처: ...] 형식으로 명시**하세요.
4. 규제 문서를 찾을 수 없는 경우, 일반적인 과학적 원칙에 기반하여 답변하되 이를 명시하세요.

예시:
- 알레르기 평가 방법을 묻는 질문 → rag_search_tool("알레르기 평가 방법 NGT") 호출
- 검색 결과를 바탕으로 답변 작성 + [출처: Codex Guideline (2003), p.12] 추가
""".strip()


def run_scientist(state: AgentState) -> dict:
    """Scientist 에이전트 실행 (P1-T4: RAG Tool 통합)

    LLM을 호출하여 NGT 식품의 위험 요소 초안을 작성합니다.
    이전 critique가 존재하면 해당 피드백을 반영하여 수정합니다.

    P1-T4 Update:
    - RAG Tool을 bind하여 LLM이 필요 시 규제 문서 검색 가능
    - Tool 호출 시 자동으로 재귀적 실행 (최대 3회)

    Args:
        state: LangGraph 공유 상태

    Returns:
        dict: 업데이트할 상태 필드 (draft, messages)
    """
    # RAG Tool이 bind된 모델 생성
    model = get_gpt4o_mini()
    model_with_tools = model.bind_tools([rag_search_tool])

    # 프롬프트 구성
    user_message = f"""
연구 주제: {state['topic']}
제약 조건: {state['constraints']}

위 주제에 대해 다음을 작성하세요:
1. NGT 기술의 잠재적 위험 요소 (범용적으로)
2. 안전성 입증을 위한 최소 제출 자료 목록

**반드시 먼저 rag_search_tool을 사용하여 관련 규제 문서를 검색한 후 답변하세요.**
""".strip()

    # 이전 비평 의견이 있으면 프롬프트에 반영
    if state.get("critique"):
        user_message += (
            f"\n\n[이전 검토 의견]\n"
            f"{state['critique'].feedback}\n"
            f"위 의견을 반영하여 수정하세요."
        )

    # 메시지 체인 (Tool 호출 포함)
    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=user_message),
    ]

    # Tool 호출을 포함한 재귀적 실행 (최대 3회)
    max_iterations = 3
    for i in range(max_iterations):
        logger.info(f"Scientist iteration {i+1}/{max_iterations}")
        response = model_with_tools.invoke(messages)

        # Tool 호출이 있는지 확인 (없으면 빈 리스트로 처리)
        tool_calls = getattr(response, 'tool_calls', None)

        # tool_calls가 없거나, 빈 리스트이거나, iterable하지 않으면 최종 답변
        if not tool_calls or not isinstance(tool_calls, (list, tuple)):
            # Tool 호출 없음 - 최종 답변
            draft = response.content
            break

        # Tool 호출 있음 - Tool 실행 후 결과를 메시지에 추가
        messages.append(response)

        for tool_call in tool_calls:
            logger.info(f"Tool called: {tool_call['name']} with args: {tool_call['args']}")

            # Tool 실행
            tool_result = rag_search_tool.invoke(tool_call["args"])

            # Tool 결과를 메시지에 추가
            messages.append(
                ToolMessage(
                    content=tool_result,
                    tool_call_id=tool_call["id"],
                )
            )

        # 다음 iteration에서 LLM이 Tool 결과를 보고 최종 답변 생성
    else:
        # 최대 반복 도달 - 마지막 응답 사용
        logger.warning(f"Max iterations ({max_iterations}) reached without final answer")
        draft = response.content if hasattr(response, 'content') else "답변 생성 실패"

    # 메시지 로그 추가 (원본 리스트 불변성 보장)
    state_messages = list(state.get("messages", []))

    # draft 미리보기 생성 (안전하게)
    draft_str = str(draft) if draft else ""
    draft_preview = draft_str[:200] + "..." if len(draft_str) > 200 else draft_str

    state_messages.append({
        "role": "scientist",
        "content": f"위험 요소 초안을 작성했습니다.\n\n{draft_preview}",
    })

    return {
        "draft": draft,
        "messages": state_messages,
    }
