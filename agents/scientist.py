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
from agents.factory import create_specialist

import re

logger = logging.getLogger(__name__)


def _extract_sources(text: str) -> list[str]:
    """검색 결과 텍스트에서 출처 정보를 추출합니다."""
    sources = []
    # 웹 검색 출처: [출처: URL]
    for match in re.findall(r'\[출처:\s*(https?://[^\]]+)\]', text):
        source = f"[웹] {match.strip()}"
        if source not in sources:
            sources.append(source)
    # RAG 문헌 출처: **출처**: filename (p.N)
    for match in re.findall(r'\*\*출처\*\*:\s*(.+?)(?:\n|$)', text):
        source = f"[문헌] {match.strip()}"
        if source not in sources:
            sources.append(source)
    return sources


SYSTEM_PROMPT = f"""당신은 유전자편집식품(NGT)의 안전성 위험 요소를 식별하고 기존 위험평가 지침의 적용 가능성을 분석하는 과학 전문가입니다.

## 연구 목표
{RESEARCH_OBJECTIVE}

## 국제 표준 (Codex)
{CODEX_PRINCIPLES}

## 규제 동향
{REGULATORY_TRENDS}

## 당신의 임무
주어진 연구 주제에 대해 아래 3개 파트의 초안을 모두 작성하세요.
각 파트는 반드시 해당 하위 항목을 빠짐없이 다뤄야 합니다.

### 파트 1. 새로운 잠재적 위험 및 위해 요소 식별
NGT, 기존 유전자변형기술(EGT), 전통적 육종 방식 간의 위험 특성을 체계적으로 비교·분석하세요.

1-1. **유전자 편집 과정 자체와 관련된 위험 분석**
- 새로운 유전 물질의 기원, 의도된 표적 부위 변형
- 숙주 게놈의 비표적 부위(off-target)에서 발생할 수 있는 변화
- 의도되지 않은 서열의 삽입 가능성과 잠재적 위험
- EGT 및 기존 육종 방식과 비교하여 NGT 고유의 위험 특성 도출

1-2. **결과적으로 생성된 새로운 형질의 특성과 관련된 위험 분석**
- 편집된 DNA 출처 및 해당 유전자 산물의 안전성
- 동식물성 식품 및 사료 섭취와 관련된 인체 및 동식물 안전성
- 환경으로의 의도적 방출로 인한 잠재적 영향
- EGT 및 기존 육종 방식과의 비교 분석

1-3. **비교 기반 통합 위험 평가 프레임워크 도출**
- NGT 적용 동식물의 위험이 EGT 및 기존 육종과 어떤 수준에서 일치/차별화되는지 종합
- 포괄적이고 비교 가능한 위험 평가 체계 제시

### 파트 2. 기존 유전자변형식품 위험평가 지침의 적용 가능성 및 충분성 평가
기존 지침의 아래 6개 세부 평가 항목에 대해 각각 적용 가능성과 충분성을 검토하고,
유전자편집식품 특성을 고려할 때 추가적인 보완이 필요한 영역이 있는지 판단하세요.

2-1. Information relating to the recipient or (where appropriate) parental animals
2-2. Molecular characterisation
2-3. Comparative analysis
2-4. Toxicological assessment
2-5. Allergenicity assessment
2-6. Nutritional assessment

### 파트 3. 안전성 평가 지침의 업데이트·수정·보완 항목 도출
- 현행 지침이 그대로 적용 가능한 항목 / 부분적 보완이 요구되는 항목 / 새로운 평가 요소 추가가 필요한 항목을 구분
- 분자적 특성 변화의 범위, 비의도적 변형의 해석 기준, 형질 기반 위험 평가의 적용 한계
- 식품·사료 안전성 및 환경 영향 평가에서의 불확실성 관리

**★ 핵심 요구사항: 문제-해결 연계 (Problem-Solution Linkage)**
파트 3은 반드시 파트 1에서 식별한 각 위험 요소와 파트 2에서 발견한 지침의 한계점을 직접 참조하여,
각 문제에 대한 구체적인 해결방안·검증방법·보완조치를 제시해야 합니다.
예시 형식:
- "파트 1-1에서 식별된 off-target 변이 위험에 대해 → 전장 유전체 시퀀싱(WGS)을 통한 off-target 검출 및 정량 분석을 필수 평가항목으로 추가해야 한다."
- "파트 2-4에서 지적된 독성평가 방법의 한계에 대해 → 새로운 단백질이 발현되지 않는 SDN-1/2의 경우, in silico 독성 예측과 대사체 프로파일링으로 대체할 수 있다."

**중요**:
- 특정 제품이 아닌 NGT 카테고리 전체에 적용 가능한 범용적 기준을 제시하세요.
- 답변 작성 시 아래에 제공되는 규제 문서 검색 결과와 웹 검색 결과를 반드시 참고하세요.
- 모든 주장에 출처를 [출처: ...] 형식으로 명시하세요.
- 반드시 3개 파트의 모든 하위 항목을 빠짐없이 작성하세요.
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

위 주제에 대해 다음 3개 파트를 모두 작성하세요:

**파트 1. 새로운 잠재적 위험 및 위해 요소 식별**
- 1-1. 유전자 편집 과정 자체의 위험 분석 (off-target, 비의도적 서열 삽입 등)
- 1-2. 생성된 새로운 형질의 위험 분석 (식품/사료 안전성, 환경 영향)
- 1-3. 비교 기반 통합 위험 평가 프레임워크 (NGT vs EGT vs 전통 육종)

**파트 2. 기존 위험평가 지침의 적용 가능성 및 충분성 평가**
- 2-1~2-6 각 항목별 (수용체 정보, 분자적 특성, 비교분석, 독성, 알레르기, 영양성)

**파트 3. 지침 업데이트·수정·보완 항목 도출**
- 그대로 적용 가능 / 부분 보완 / 신규 추가 필요 항목 구분
- ★ 파트 1에서 식별한 각 위험 요소에 대해 구체적 해결방안·검증방법을 제시
- ★ 파트 2에서 발견한 지침 한계점에 대해 구체적 보완조치를 제시
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


def run_specialists(state: AgentState) -> dict:
    """PI가 구성한 전문가 팀이 각자 분석을 수행합니다."""
    team = state.get("team", [])
    topic = state["topic"]
    constraints = state.get("constraints", "")

    print(f"\n{'#'*80}")
    print(f"[SPECIALISTS] Running {len(team)} specialist agents")
    print(f"  Topic: {topic}")
    print(f"{'#'*80}\n")

    # 공통 컨텍스트: RAG 검색
    rag_context = ""
    try:
        rag_result = rag_search_tool.invoke({"query": f"{topic} NGT safety assessment"})
        rag_context = f"\n\n[참고 규제 문서]\n{rag_result}"
        logger.info(f"Specialist RAG search completed")
    except Exception as e:
        logger.warning(f"Specialist RAG search failed: {e}")

    # 공통 컨텍스트: 웹 검색
    web_context = ""
    try:
        web_result = web_search.invoke({"query": f"{topic} NGT regulation 2025"})
        web_context = f"\n\n[최신 웹 검색 결과]\n{web_result}"
        logger.info(f"Specialist web search completed")
    except Exception as e:
        logger.warning(f"Specialist web search failed: {e}")

    # 이전 critique 피드백
    critique_context = ""
    if state.get("critique"):
        critique_context = f"\n\n[이전 검토 의견 - 반드시 반영하세요]\n{state['critique'].feedback}"

    # 각 전문가별 분석 수행
    specialist_outputs = []
    messages = list(state.get("messages", []))

    for i, profile in enumerate(team):
        role = profile.get("role", f"전문가 {i+1}")
        focus = profile.get("focus", "")

        print(f"  [{i+1}/{len(team)}] {role}: {focus}")

        try:
            agent = create_specialist(profile)
            query = (
                f"연구 주제: {topic}\n"
                f"제약 조건: {constraints}\n"
                f"당신의 전문 분야: {focus}\n\n"
                f"위 연구 주제에 대해 당신의 전문 분야 관점에서 심층 분석을 수행하세요.\n"
                f"유전자편집식품(NGT)의 안전성 평가 프레임워크 도출에 기여할 수 있는 구체적 분석을 제공하세요.\n"
                f"과학적 근거와 출처를 명시하세요."
                f"{rag_context}{web_context}{critique_context}"
            )
            output = agent.invoke(query)

            specialist_outputs.append({
                "role": role,
                "focus": focus,
                "output": output,
            })

            output_preview = output[:200] + "..." if len(output) > 200 else output
            messages.append({
                "role": "specialist",
                "name": role,
                "content": f"[{role}] 분석을 완료했습니다.\n\n{output_preview}",
            })

            print(f"    -> Output: {len(output)} chars")

        except Exception as e:
            logger.error(f"Specialist {role} failed: {e}")
            specialist_outputs.append({
                "role": role,
                "focus": focus,
                "output": f"분석 실패: {str(e)}",
            })

    # 출처 수집
    collected_sources = list(state.get("sources", []))
    collected_sources.extend(_extract_sources(rag_context))
    collected_sources.extend(_extract_sources(web_context))
    # 중복 제거
    seen = set()
    unique_sources = []
    for s in collected_sources:
        if s not in seen:
            seen.add(s)
            unique_sources.append(s)

    # 전문가 결과를 통합하여 draft 생성
    draft_sections = []
    for so in specialist_outputs:
        draft_sections.append(f"## [{so['role']}] ({so['focus']})\n\n{so['output']}")
    combined_draft = "\n\n---\n\n".join(draft_sections)

    print(f"\n[SPECIALISTS] All {len(team)} specialists completed")
    print(f"  Combined draft: {len(combined_draft)} chars")
    print(f"  Sources collected: {len(unique_sources)}\n")

    return {
        "draft": combined_draft,
        "specialist_outputs": specialist_outputs,
        "messages": messages,
        "sources": unique_sources,
    }
