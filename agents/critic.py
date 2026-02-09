"""Scientific Critic Agent

Scientist가 작성한 초안의 과학적 타당성, 범용성, 과도한 규제 여부를
검증하는 비평가 에이전트입니다. OpenAI SDK 직접 호출.
"""
import json
import logging

from data.guidelines import CRITIQUE_RUBRIC
from utils.llm import call_gpt4o
from workflow.state import AgentState, CritiqueResult
from tools.web_search import web_search

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = f"""당신은 과학적 타당성을 검증하는 비평가입니다.

## 비평 기준
{CRITIQUE_RUBRIC}

## 당신의 임무
Scientist가 작성한 초안을 검토하고, 아래 체크리스트에 따라 **엄격하게** 평가하세요:
1. 과학적 근거가 있는가? 구체적인 출처나 연구가 인용되어 있는가? (1-5점)
2. 특정 제품이 아닌 카테고리 전체에 적용 가능한가? (1-5점)
3. 불필요하게 과도한 자료를 요구하지 않는가? (1-5점)

**승인 조건**: 모든 항목 4점 이상
첫 번째 검토에서는 특히 엄격하게 평가하세요. 개선 여지가 있다면 반드시 revise를 선택하세요.

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

참고 정보가 제공된 경우 이를 활용하여 더 정확한 검증을 수행하세요.
반드시 JSON만 출력하세요. 다른 설명은 불필요합니다.
""".strip()


def merge_views(views: list[str]) -> str:
    """병렬 의견 통합 함수"""
    if not views:
        return ""
    if len(views) == 1:
        return views[0]

    unique_views = []
    seen = set()
    for view in views:
        view_stripped = view.strip()
        if view_stripped and view_stripped not in seen:
            unique_views.append(view_stripped)
            seen.add(view_stripped)

    return "\n\n".join(unique_views)


def run_critic(state: AgentState) -> dict:
    """Critic 에이전트 실행 - OpenAI 직접 호출"""
    print(f"\n{'#'*80}")
    print(f"[CRITIC] Starting Critic agent")
    print(f"  Draft length: {len(state.get('draft', ''))} chars")
    print(f"  Iteration: {state.get('iteration', 0)}")
    print(f"{'#'*80}\n")

    # Step 1: 웹 검색으로 검증 정보 수집
    web_context = ""
    try:
        web_result = web_search.invoke({"query": f"{state['topic']} NGT safety regulation verification"})
        web_context = f"\n\n## [웹 검색 결과 - 검증 참고]\n{web_result}"
        logger.info("Critic web search completed")
    except Exception as e:
        logger.warning(f"Critic web search failed: {e}")

    # Step 2: 프롬프트 구성
    user_message = f"""[Scientist의 초안]
{state['draft']}
{web_context}

위 초안을 검토하고, JSON 형식으로 응답하세요."""

    # Step 3: OpenAI 직접 호출 (NO LangChain)
    print(f"\n{'#'*80}")
    print(f"[CRITIC] Calling OpenAI API via call_gpt4o")
    print(f"{'#'*80}\n")

    logger.info("Critic: Calling OpenAI directly...")

    try:
        response_content = call_gpt4o(SYSTEM_PROMPT, user_message)
        print(f"\n{'#'*80}")
        print(f"[CRITIC] OpenAI call succeeded")
        print(f"  Response length: {len(response_content)} chars")
        print(f"{'#'*80}\n")
    except Exception as e:
        print(f"\n{'!'*80}")
        print(f"[CRITIC ERROR] Failed to call OpenAI!")
        print(f"  Exception: {type(e).__name__}: {e}")
        print(f"{'!'*80}\n")
        raise

    # JSON 파싱
    try:
        content = response_content.strip()
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:-1])

        data = json.loads(content)
        critique = CritiqueResult(
            decision=data["decision"],
            feedback=data.get("feedback", ""),
            scores=data.get("scores", {}),
        )
    except (json.JSONDecodeError, KeyError) as e:
        logger.warning(f"Critic JSON parse failed: {e}, defaulting to approve")
        critique = CritiqueResult(
            decision="approve",
            feedback="",
            scores={},
        )

    # 메시지 로그
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
