"""Scientist (Risk Identifier) Agent

NGT 식품의 잠재적 위험 요소를 식별하고, 안전성 입증을 위한
최소 제출 자료 목록을 작성하는 과학 전문가 에이전트입니다.
OpenAI SDK 직접 호출 방식으로 tool_calls 문제를 방지합니다.
"""
import logging

from data.guidelines import RESEARCH_OBJECTIVE, CODEX_PRINCIPLES, REGULATORY_TRENDS
from utils.llm import call_gpt4o_mini
from workflow.state import AgentState
from tools.rag_search import rag_search_tool
from tools.web_search import web_search

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = f"""당신은 유전자편집식품(NGT)의 안전성 위험 요소를 식별하는 과학 전문가입니다.

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

답변 작성 시 아래에 제공되는 규제 문서 검색 결과와 웹 검색 결과를 반드시 참고하세요.
모든 답변에 출처를 [출처: ...] 형식으로 명시하세요.
""".strip()


def run_scientist(state: AgentState) -> dict:
    """Scientist 에이전트 실행 - OpenAI 직접 호출"""
    print(f"\n{'#'*80}")
    print(f"[SCIENTIST] Starting Scientist agent")
    print(f"  Topic: {state.get('topic', 'N/A')}")
    print(f"  Constraints: {state.get('constraints', 'N/A')}")
    print(f"  Iteration: {state.get('iteration', 0)}")
    print(f"{'#'*80}\n")

    topic = state['topic']
    constraints = state['constraints']

    # Step 1: RAG 검색 (규제 문서)
    rag_context = ""
    try:
        rag_result = rag_search_tool.invoke({"query": f"{topic} NGT safety assessment"})
        rag_context = f"\n\n## [RAG 검색 결과 - 규제 문서]\n{rag_result}"
        logger.info(f"RAG search completed for: {topic}")
    except Exception as e:
        logger.warning(f"RAG search failed: {e}")

    # Step 2: 웹 검색 (최신 정보)
    web_context = ""
    try:
        web_result = web_search.invoke({"query": f"{topic} NGT regulation 2025"})
        web_context = f"\n\n## [웹 검색 결과 - 최신 정보]\n{web_result}"
        logger.info(f"Web search completed for: {topic}")
    except Exception as e:
        logger.warning(f"Web search failed: {e}")

    # Step 3: 프롬프트 구성
    user_message = f"""연구 주제: {topic}
제약 조건: {constraints}

위 주제에 대해 다음을 작성하세요:
1. NGT 기술의 잠재적 위험 요소 (범용적으로)
2. 안전성 입증을 위한 최소 제출 자료 목록
{rag_context}
{web_context}"""

    # 이전 비평 의견이 있으면 프롬프트에 반영
    if state.get("critique"):
        user_message += (
            f"\n\n[이전 검토 의견]\n"
            f"{state['critique'].feedback}\n"
            f"위 의견을 반영하여 수정하세요."
        )

    # Step 4: OpenAI 직접 호출 (NO LangChain)
    print(f"\n{'#'*80}")
    print(f"[SCIENTIST] Calling OpenAI API via call_gpt4o_mini")
    print(f"{'#'*80}\n")

    logger.info("Scientist: Calling OpenAI directly...")

    try:
        draft = call_gpt4o_mini(SYSTEM_PROMPT, user_message)
        print(f"\n{'#'*80}")
        print(f"[SCIENTIST] OpenAI call succeeded")
        print(f"  Draft length: {len(draft)} chars")
        print(f"{'#'*80}\n")
    except Exception as e:
        print(f"\n{'!'*80}")
        print(f"[SCIENTIST ERROR] Failed to call OpenAI!")
        print(f"  Exception: {type(e).__name__}: {e}")
        print(f"{'!'*80}\n")
        raise

    # 메시지 로그
    state_messages = list(state.get("messages", []))
    draft_preview = draft[:200] + "..." if len(draft) > 200 else draft
    state_messages.append({
        "role": "scientist",
        "content": f"위험 요소 초안을 작성했습니다.\n\n{draft_preview}",
    })

    return {
        "draft": draft,
        "messages": state_messages,
    }
