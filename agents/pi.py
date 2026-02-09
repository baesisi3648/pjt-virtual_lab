"""PI (Principal Investigator) Agent

연구 프로젝트의 총괄 책임자 역할을 수행합니다.
OpenAI SDK 직접 호출 방식으로 tool_calls 문제를 방지합니다.
"""
import json
import logging
import re
from typing import List

from utils.llm import call_gpt4o
from workflow.state import AgentState
from tools.web_search import web_search


def _extract_sources(text: str) -> list[str]:
    """검색 결과 텍스트에서 출처 정보를 추출합니다."""
    sources = []
    for match in re.findall(r'\[출처:\s*(https?://[^\]]+)\]', text):
        source = f"[웹] {match.strip()}"
        if source not in sources:
            sources.append(source)
    for match in re.findall(r'\*\*출처\*\*:\s*(.+?)(?:\n|$)', text):
        source = f"[문헌] {match.strip()}"
        if source not in sources:
            sources.append(source)
    return sources

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = """당신은 연구 프로젝트의 총괄 책임자(PI)입니다.

## 당신의 임무
Scientist와 Critic의 논의를 거쳐 승인된 초안을 바탕으로, 아래 4개 파트로 구성된 최종 보고서를 작성하세요.
각 파트의 모든 하위 항목을 빠짐없이, 충분한 분량으로 상세히 서술해야 합니다.

## 보고서 포맷 (Markdown)

```
# 유전자편집식품(NGT) 표준 안전성 평가 프레임워크 (Final Report)

---

## 1. 새로운 잠재적 위험 및 위해 요소 식별 보고서

식품, 사료 및 기타 농업용 동식물에 적용되는 새로운 유전자편집기술(NGT)과
기존 유전자변형기술(EGT) 및 전통적 육종 방식 간의 위험 특성을 체계적으로
비교·분석한 결과를 서술한다.

### 1-1. 유전자 편집 과정 자체와 관련된 위험 분석

(NGT 적용 과정에서 발생할 수 있는 의도적 및 비의도적 위험 요소를 식별.
새로운 유전 물질의 기원, 의도된 표적 부위 변형, 숙주 게놈의 비표적 부위
off-target 변화, 의도되지 않은 서열 삽입 가능성 등을 EGT 및 기존 육종과
비교하여 NGT 고유의 위험 특성을 도출.)

### 1-2. 결과적으로 생성된 새로운 형질의 특성과 관련된 위험 분석

(편집된 DNA의 출처 및 해당 유전자 산물의 안전성을 중심으로, 동식물성 식품
및 사료 섭취와 관련된 인체 및 동식물 안전성 영향, 환경으로의 의도적 방출로
인한 잠재적 영향을 EGT 및 기존 육종과 비교 분석.)

### 1-3. 비교 기반 통합 위험 평가 프레임워크 도출

(상업화 단계에서 NGT 적용 동식물의 위험 및 위해 요소가 EGT 및 기존 육종의
위험 특성과 어떤 수준에서 일치하거나 차별화되는지 종합 정리.
포괄적이고 비교 가능한 위험 평가 체계를 제시.)

---

## 2. 기존 유전자변형식품 위험평가 지침의 적용 가능성 및 충분성 평가 보고서

기존 유전자변형식품 위험평가 지침의 아래 6개 세부 평가 항목에 대해,
각 항목별 평가 방법의 적용 가능성 및 충분성을 검토하고,
유전자편집식품 특성을 고려할 때 추가적 보완 필요 여부를 판단한다.

### 2-1. Information relating to the recipient or (where appropriate) parental animals
(수용체 또는 모체 동물에 관한 정보의 적용 가능성 및 충분성 평가)

### 2-2. Molecular characterisation
(분자적 특성 분석 방법의 적용 가능성 및 충분성 평가)

### 2-3. Comparative analysis
(비교 분석 방법의 적용 가능성 및 충분성 평가)

### 2-4. Toxicological assessment
(독성 평가 방법의 적용 가능성 및 충분성 평가)

### 2-5. Allergenicity assessment
(알레르기 유발 가능성 평가 방법의 적용 가능성 및 충분성 평가)

### 2-6. Nutritional assessment
(영양성 평가 방법의 적용 가능성 및 충분성 평가)

---

## 3. 안전성 평가 지침의 업데이트·수정·보완 항목 도출 보고서

기존 유전자변형식품 위험평가 지침의 각 세부 평가 항목을 대상으로,
유전자편집식품의 기술적 특성 및 최근·향후 개발 동향을 반영하지 못하는
영역을 체계적으로 도출한다.

### 3-1. 현행 지침의 적용 가능성 분류
- **그대로 적용 가능한 항목**: (해당 항목과 근거)
- **부분적 보완이 요구되는 항목**: (해당 항목, 보완 필요 사유, 구체적 보완 방향)
- **새로운 평가 요소 추가가 필요한 항목**: (해당 항목, 추가 필요 사유, 구체적 제안)

### 3-2. 식별된 위험 요소에 대한 구체적 해결방안
(★ 핵심: 파트 1에서 식별한 각 위험/위해 요소를 직접 참조하고,
각각에 대한 구체적인 검증방법·평가절차·보완조치를 제시한다.
형식 예시:
- "1-1에서 식별된 [위험 요소]에 대해 → [구체적 해결방안/검증방법]"
- "2-X에서 지적된 [지침 한계]에 대해 → [구체적 보완조치]"
모든 위험 요소가 해결방안과 1:1로 매칭되어야 한다.)

### 3-3. 구조적 한계 및 개선 필요성
(분자적 특성 변화의 범위와 양상, 비의도적 변형의 해석 기준,
형질 기반 위험 평가의 적용 한계, 식품·사료 안전성 및 환경 영향 평가에서의
불확실성 관리 측면을 중심으로 기존 지침의 구조적 한계 분석)

### 3-4. 구체적 업데이트·수정·보완 방향 제시
(과학적 근거에 기반한 단계적·비례적 위험평가 체계 마련을 위한
구체적인 업데이트, 수정 또는 보완 방향을 제시)

---

## 4. 종합적인 결론 보고서

### 4-1. 통합적 평가 결과
(기존 유전자변형식품 위험평가 체계의 적용 가능성, 충분성 및 한계를 통합 정리.
최소 5-10문장으로 구체적인 평가 결과를 상세히 서술할 것.)

### 4-2. NGT vs EGT vs 전통 육종 비교 총괄
(유전자 변형 과정과 결과적 형질이라는 두 분석 축을 중심으로,
위험 특성의 공통점과 차별점을 명확히 도출.
최소 5-10문장으로 비교 결과를 체계적으로 서술할 것.)

### 4-3. 기존 지침의 적용 영역 구분 및 과학적 근거
(전반적으로 적용 가능한 영역과, 부분적 보완 또는 신규 평가 요소 추가가
요구되는 영역을 구분하고, 그 과학적·기술적 근거를 명확히 기술.
최소 5-10문장으로 각 영역별 판단 근거를 상세히 서술할 것.)

### 4-4. 주요 한계점
(분자적 특성 변화의 해석, 비의도적 변형의 평가 한계, 형질 기반 위험 평가의
불확실성, 식품 안전성 평가에서의 자료 공백 등 본 연구에서 확인된 주요 한계점.
최소 5-10문장으로 각 한계점과 그 영향을 구체적으로 서술할 것.)

### 4-5. 향후 연구 과제 및 데이터 요구 사항
(분석 범위 및 방법론적 제약으로 인해 도출되지 못한 사항을 명시하고,
향후 위험평가 체계 고도화를 위해 추가 검토가 필요한 연구 과제 및 데이터 제안.
최소 5-10문장으로 구체적 연구 과제와 필요 데이터를 상세히 서술할 것.)

### 4-6. 최종 결론
(유전자편집식품의 특성을 반영한 단계적·비례적 위험평가 접근의 필요성을
결론으로 제시하고, 현행 안전성 평가 지침의 합리적 개선 방향을 도출.
최소 5-10문장으로 핵심 결론과 정책적 제언을 구체적으로 서술할 것.)

---

## 5. 참고문헌 (References)

### 5-1. Web Search Sources
(Tavily 웹 검색을 통해 참조한 온라인 자료의 URL과 제목을 번호 목록으로 정리)

### 5-2. Regulatory Documents (RAG)
(RAG 시스템을 통해 참조한 규제 문서·학술 문헌의 파일명, 페이지, 제목을 번호 목록으로 정리)
```

**중요**:
- 반드시 위 4개 파트와 모든 하위 항목(1-1~1-3, 2-1~2-6, 3-1~3-4, 4-1~4-6)을 빠짐없이 포함해야 합니다.
- 각 항목은 충분한 분량(최소 5 - 10문단)으로 상세히 서술하세요. 단순 나열이 아닌 분석적 서술이 필요합니다.
- 과학적 근거와 출처를 명시하세요.
- 참고 정보가 제공된 경우 이를 활용하여 보고서의 근거를 강화하세요.

**★ 핵심 원칙: 문제-해결 연계 (Problem-Solution Linkage)**
- 파트 3(특히 3-2)에서는 반드시 파트 1에서 식별한 위험 요소와 파트 2에서 발견한 지침의 한계점을 직접 인용·참조하고, 각각에 대한 구체적 해결방안·검증방법·보완조치를 제시해야 합니다.
- 보고서를 읽는 사람이 "어떤 문제가 있고, 그 문제를 어떻게 해결하는가"를 일관되게 파악할 수 있어야 합니다.
- 파트 4(종합 결론)에서도 문제-해결 구조를 요약해야 합니다.
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


def run_pi_planning(state: AgentState) -> dict:
    """PI가 연구 주제를 분석하고 전문가 팀을 구성합니다."""
    print(f"\n{'#'*80}")
    print(f"[PI PLANNING] Starting PI planning phase")
    print(f"  Topic: {state.get('topic', 'N/A')}")
    print(f"{'#'*80}\n")

    topic = state["topic"]
    constraints = state.get("constraints", "")

    # decide_team()으로 팀 구성
    try:
        team = decide_team(f"{topic}\n제약 조건: {constraints}")
        logger.info(f"PI decided team: {len(team)} specialists")
    except Exception as e:
        logger.warning(f"decide_team failed: {e}, using default team")
        team = [
            {"role": "NGT 분자생물학 전문가", "focus": "유전자편집 과정의 off-target 효과 및 분자적 특성 분석"},
            {"role": "식품안전성 평가 전문가", "focus": "독성, 알레르기, 영양성 평가 방법론"},
            {"role": "규제과학 전문가", "focus": "국제 규제 프레임워크 비교 및 지침 적용 가능성 분석"},
        ]

    # 팀 구성 내용을 메시지로 기록
    team_summary = "\n".join(
        [f"- **{m['role']}**: {m['focus']}" for m in team]
    )
    messages = list(state.get("messages", []))
    messages.append({
        "role": "pi",
        "content": f"연구 팀을 구성했습니다.\n\n{team_summary}",
    })

    print(f"[PI PLANNING] Team composed: {len(team)} specialists")
    for m in team:
        print(f"  - {m['role']}: {m['focus']}")

    return {
        "team": team,
        "messages": messages,
    }


def run_pi(state: AgentState) -> dict:
    """PI 에이전트 실행 - OpenAI 직접 호출"""
    print(f"\n{'#'*80}")
    print(f"[PI] Starting PI agent")
    print(f"  Draft length: {len(state.get('draft', ''))} chars")
    print(f"  Iteration: {state.get('iteration', 0)}")
    print(f"{'#'*80}\n")

    # Step 1: 웹 검색으로 최신 정보 보강
    web_context = ""
    pi_sources = []
    try:
        web_result = web_search.invoke({"query": f"{state['topic']} NGT safety framework final report 2025"})
        web_context = f"\n\n## [웹 검색 결과 - 최신 정보]\n{web_result}"
        pi_sources.extend(_extract_sources(web_context))
        logger.info("PI web search completed")
    except Exception as e:
        logger.warning(f"PI web search failed: {e}")

    # Step 2: 전문가 분석 결과 통합
    specialist_context = ""
    specialist_outputs = state.get("specialist_outputs", [])
    if specialist_outputs:
        specialist_sections = []
        for so in specialist_outputs:
            specialist_sections.append(
                f"### [{so.get('role', '전문가')}] ({so.get('focus', '')})\n{so.get('output', '')}"
            )
        specialist_context = "\n\n---\n\n".join(specialist_sections)

    # Step 3: 프롬프트 구성
    user_message = (
        f"연구 주제: {state['topic']}\n"
        f"제약 조건: {state['constraints']}\n\n"
        f"[승인된 통합 초안]\n{state['draft']}\n\n"
    )
    if specialist_context:
        user_message += f"[각 전문가 개별 분석 결과]\n{specialist_context}\n\n"
    # 출처 목록 통합 (이전 단계 + PI 웹 검색)
    all_sources = list(state.get("sources", []))
    all_sources.extend(pi_sources)
    # 중복 제거
    seen = set()
    unique_sources = []
    for s in all_sources:
        if s not in seen:
            seen.add(s)
            unique_sources.append(s)

    sources_text = ""
    if unique_sources:
        sources_list = "\n".join(f"- {s}" for s in unique_sources)
        sources_text = f"\n\n[참조 출처 목록]\n{sources_list}"

    user_message += (
        f"{web_context}\n\n"
        f"{sources_text}\n\n"
        "위 초안과 전문가 분석 결과를 종합하여 최종 보고서를 Markdown 형식으로 작성하세요.\n"
        "반드시 4개 파트(1. 위험 식별, 2. 지침 적용 가능성 평가, 3. 지침 업데이트 항목, 4. 종합 결론)와\n"
        "모든 하위 항목(1-1~1-3, 2-1~2-6, 3-1~3-4, 4-1~4-6)을 빠짐없이 포함해야 합니다.\n"
        "각 항목은 충분한 분량(최소 5-10 문단)으로 분석적으로 서술하세요.\n\n"
        "★ 핵심: 파트 3-2에서는 파트 1에서 식별한 각 위험 요소에 대해 구체적인 해결방안·검증방법을 제시하고,\n"
        "파트 2에서 발견한 지침 한계점에 대해 구체적인 보완조치를 제시하세요.\n"
        "모든 위험 요소가 해결방안과 명확히 연결되어야 합니다.\n\n"
        "★ 보고서 최하단에 반드시 '## 5. 참고문헌 (References)' 섹션을 추가하세요.\n"
        "위에 제공된 [참조 출처 목록]의 모든 출처를 포함하고,\n"
        "[웹] 출처는 'Web Search' 카테고리로, [문헌] 출처는 'Regulatory Documents (RAG)' 카테고리로 구분하여 정리하세요."
    )

    # Step 4: OpenAI 직접 호출 (NO LangChain)
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
    team = state.get("team", [])
    team_names = ", ".join([m.get("role", "전문가") for m in team]) if team else "전문가 팀"
    messages.append({
        "role": "pi",
        "content": f"팀 회의를 주재하고 {team_names}의 분석 결과를 종합하여 최종 보고서를 작성했습니다.",
    })

    return {
        "final_report": final_report,
        "messages": messages,
    }
