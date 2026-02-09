"""PI (Principal Investigator) Agent

연구 프로젝트의 총괄 책임자 역할을 수행합니다.
OpenAI SDK 직접 호출 방식으로 tool_calls 문제를 방지합니다.
"""
import json
import logging
from typing import List

from utils.llm import call_gpt4o
from workflow.state import AgentState
from tools.web_search import web_search

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """당신은 연구 프로젝트의 총괄 책임자(PI)입니다.

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

참고 정보가 제공된 경우 이를 활용하여 보고서의 근거를 강화하세요.
"""


TEAM_DECISION_PROMPT = """당신은 연구 프로젝트의 총괄 책임자(PI)입니다.

## 당신의 임무
사용자 질문을 분석하여 필요한 전문가 팀을 구성하세요.

## 출력 형식 (JSON)
반드시 다음과 같은 JSON 배열 형식으로 답변하세요:
```json
[
  {
    "role": "전문가 역할",
    "focus": "구체적인 집중 분야"
  }
]
```

**중요**: JSON 형식만 출력하세요. 최소 1명, 최대 5명.
"""


def decide_team(user_query: str) -> List[dict]:
    """PI가 쿼리 분석 후 팀 구성 결정"""
    user_message = (
        f"사용자 질문: {user_query}\n\n"
        "위 질문에 답변하기 위해 필요한 전문가 팀을 구성하세요.\n"
        "JSON 배열 형식으로만 답변하세요."
    )

    response = call_gpt4o(TEAM_DECISION_PROMPT, user_message)

    try:
        content = response.strip()
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:-1])

        team = json.loads(content)

        if not isinstance(team, list):
            raise ValueError("응답이 리스트 형식이 아닙니다.")

        for expert in team:
            if "role" not in expert or "focus" not in expert:
                raise ValueError("각 전문가는 role과 focus 필드가 필요합니다.")

        return team

    except json.JSONDecodeError as e:
        raise ValueError(f"LLM 응답을 JSON으로 파싱할 수 없습니다: {e}\n응답: {response}")


def run_pi(state: AgentState) -> dict:
    """PI 에이전트 실행 - OpenAI 직접 호출"""
    print(f"\n{'#'*80}")
    print(f"[PI] Starting PI agent")
    print(f"  Draft length: {len(state.get('draft', ''))} chars")
    print(f"  Iteration: {state.get('iteration', 0)}")
    print(f"{'#'*80}\n")

    # Step 1: 웹 검색으로 최신 정보 보강
    web_context = ""
    try:
        web_result = web_search.invoke({"query": f"{state['topic']} NGT safety framework final report 2025"})
        web_context = f"\n\n## [웹 검색 결과 - 최신 정보]\n{web_result}"
        logger.info("PI web search completed")
    except Exception as e:
        logger.warning(f"PI web search failed: {e}")

    # Step 2: 프롬프트 구성
    user_message = (
        f"연구 주제: {state['topic']}\n"
        f"제약 조건: {state['constraints']}\n\n"
        f"[승인된 초안]\n{state['draft']}\n"
        f"{web_context}\n\n"
        "위 초안을 바탕으로 최종 보고서를 Markdown 형식으로 작성하세요.\n"
        "4개 섹션(개요, 위험 식별, 최소 자료 요건, 결론)을 모두 포함해야 합니다."
    )

    # Step 3: OpenAI 직접 호출 (NO LangChain)
    print(f"\n{'#'*80}")
    print(f"[PI] Calling OpenAI API via call_gpt4o")
    print(f"{'#'*80}\n")

    logger.info("PI: Calling OpenAI directly...")

    try:
        final_report = call_gpt4o(SYSTEM_PROMPT, user_message)
        print(f"\n{'#'*80}")
        print(f"[PI] OpenAI call succeeded")
        print(f"  Report length: {len(final_report)} chars")
        print(f"{'#'*80}\n")
    except Exception as e:
        print(f"\n{'!'*80}")
        print(f"[PI ERROR] Failed to call OpenAI!")
        print(f"  Exception: {type(e).__name__}: {e}")
        print(f"{'!'*80}\n")
        raise

    # 메시지 로그
    messages = list(state.get("messages", []))
    messages.append({
        "role": "pi",
        "content": "최종 보고서를 작성했습니다.",
    })

    return {
        "final_report": final_report,
        "messages": messages,
    }
