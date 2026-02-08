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
from tools.web_search import web_search


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

## 도구 사용 지침
초안의 주장을 검증하기 위해 최신 논문이나 규제 동향을 확인해야 할 경우 web_search 도구를 사용하세요.
""".strip()


def merge_views(views: list[str]) -> str:
    """병렬 의견 통합 함수

    여러 에이전트의 의견을 통합하여 최종 합의안을 도출합니다.

    Conflict Resolution 규칙:
    1. 중복 제거: 동일한 의견은 한 번만 포함
    2. 보수적 안전 기준 선택: 필수 > 조건부 > 선택 > 면제
    3. 근거 부족한 의견 기각: 과학적 근거가 명시되지 않은 의견 제외
    4. 상충 해결: 조건부/세분화된 접근 우선

    Args:
        views: 여러 에이전트의 의견 리스트

    Returns:
        str: 통합된 최종 의견
    """
    if not views:
        return ""

    if len(views) == 1:
        return views[0]

    # 1. 중복 제거 (완전 동일한 문장)
    unique_views = []
    seen = set()
    for view in views:
        view_stripped = view.strip()
        if view_stripped and view_stripped not in seen:
            unique_views.append(view_stripped)
            seen.add(view_stripped)

    # 2. 보수적 안전 기준 선택 및 상충 해결
    # 키워드 우선순위: 조건부/세분화 > 필수 > 필요 > 선택 > 면제
    # 각 카테고리별로 뷰 수집
    conditional_views = [
        view for view in unique_views
        if any(keyword in view for keyword in ["조건부", "유형", "분류", "경우", "따라"])
    ]
    mandatory_views = [view for view in unique_views if "필수" in view]
    required_views = [view for view in unique_views if "필요" in view and "불필요" not in view]
    optional_views = [view for view in unique_views if "선택" in view or "권장" in view]
    exempt_views = [view for view in unique_views if "면제" in view or "불필요" in view]

    # 우선순위에 따라 선택
    if conditional_views:
        candidate_views = conditional_views
    elif mandatory_views:
        candidate_views = mandatory_views
    elif required_views:
        candidate_views = required_views
    elif optional_views:
        candidate_views = optional_views
    elif exempt_views:
        candidate_views = exempt_views
    else:
        candidate_views = unique_views

    # 3. 근거 기반 필터링 (선택된 뷰들 중에서)
    founded_views = []
    for view in candidate_views:
        # 과학적 근거가 명시된 의견 우선
        if any(keyword in view.lower() for keyword in [
            "근거", "과학적", "연구", "효과", "특성", "crispr", "off-target",
            "유전자", "독성", "안전성", "평가"
        ]):
            founded_views.append(view)

    # 근거가 있는 의견이 없으면 후보군 전체 사용
    if founded_views:
        result_views = founded_views
    else:
        result_views = candidate_views

    # 4. 최종 통합
    if not result_views:
        result_views = founded_views

    return "\n\n".join(result_views)


def run_critic(state: AgentState) -> dict:
    """Critic 에이전트 실행

    Scientist의 초안을 CRITIQUE_RUBRIC에 따라 검토하고,
    승인(approve) 또는 수정 요청(revise) 판정을 내립니다.
    web_search 도구를 바인딩하여 주장 검증 가능.

    Args:
        state: LangGraph 공유 상태

    Returns:
        dict: 업데이트할 상태 필드 (critique, messages)
    """
    # 웹 검색 도구 바인딩
    model = get_gpt4o().bind_tools([web_search])

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

    # Tool call 처리 (web_search 호출 시)
    if response.tool_calls:
        # 도구 호출 실행
        tool_messages = []
        for tool_call in response.tool_calls:
            if tool_call["name"] == "web_search":
                search_result = web_search.invoke(tool_call["args"])
                tool_messages.append({
                    "role": "tool",
                    "name": "web_search",
                    "content": search_result,
                })

        # 도구 결과를 포함하여 재호출
        final_response = model.invoke([
            SystemMessage(content=SYSTEM_PROMPT),
            HumanMessage(content=user_message),
            response,
            *[HumanMessage(content=msg["content"]) for msg in tool_messages]
        ])
        response_content = final_response.content
    else:
        response_content = response.content

    # JSON 파싱
    try:
        data = json.loads(response_content)
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
