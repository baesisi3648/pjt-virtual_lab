"""Scientific Critic Agent

각 과학자 에이전트의 분석 결과를 개별적으로 검토하고
전문가별 평가를 수행하는 비평가 에이전트입니다.
OpenAI SDK 직접 호출.
"""
import json
import logging
import re

from data.guidelines import CRITIQUE_RUBRIC, ACADEMIC_TONE_GUIDE
from utils.llm import call_gpt
from workflow.state import AgentState, CritiqueResult
from tools.web_search import web_search

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = f"""당신은 과학적 타당성과 가독성을 검증하는 독립적 비평가입니다.

## 참고 기준
{CRITIQUE_RUBRIC}

## 서술 가이드
{ACADEMIC_TONE_GUIDE}

## 당신의 임무
각 과학자 에이전트의 분석 결과를 개별적으로 검토하세요.
과학적 정확성뿐 아니라, "이해하기 쉬운가"와 "왜 필요한가를 설명하고 있는가"를 함께 평가합니다.

## 전문가별 평가 기준
각 전문가에 대해 다음을 평가하세요:
1. **근거의 적절성**: 주장을 뒷받침하는 과학적 맥락과 해석이 충분한가?
2. **논리적 비약 여부**: 전제에서 결론으로의 논리적 연결이 타당한가?
3. **대안적 해석 가능성**: 다른 해석이나 반론을 충분히 고려했는가?
4. **가독성과 용어 설명**: (양방향 검증)
   - 설명 없는 약어/전문 용어가 있는가? → 감점
   - 수치/임계값/프로토콜이 포함되어 있는가? → 감점
   - 비전문가도 이해할 수 있는 평이한 서술인가? → 가점
   - "왜 이 평가가 필요한가"를 설명하고 있는가? → 가점

## 평가 유의사항
- 첫 번째 라운드에서는 특히 엄격하게 평가하세요
- **점수 비교 원칙**: 이전 라운드 점수가 제공된 경우, 각 전문가의 이전 점수와 비교하세요.
  - 이전 지적 사항이 해결되었으면 점수를 올려주세요
  - 이전 강점이 유지되면서 새로운 개선이 있으면 반드시 점수를 올려주세요
  - 점수를 내리려면 명확한 근거(이전 강점이 삭제됨, 새로운 오류 발생 등)가 있어야 합니다
- 강점은 명확히 인정하고, 약점은 구체적 개선 방향과 함께 지적하세요
- **피드백 구조**: 각 전문가 피드백에 다음을 포함하세요:
  1. 이전 라운드 대비 개선된 점 (있다면)
  2. 여전히 남아있는 약점
  3. 5/5 만점을 받기 위해 필요한 구체적 조치

## 출력 형식 (JSON) - 축별 점수 필수
{{
  "decision": "continue",
  "feedback": "전체 요약 피드백 (주요 쟁점, 합의된 사항, 미해결 사항)",
  "scores": {{
    "전문가역할명1": {{"evidence": 3, "universality": 4, "proportionality": 3, "readability": 2}},
    "전문가역할명2": {{"evidence": 4, "universality": 3, "proportionality": 4, "readability": 3}}
  }},
  "specialist_feedback": {{
    "전문가역할명1": "구체적 피드백 (강점, 약점, 개선 지시)",
    "전문가역할명2": "구체적 피드백 ..."
  }}
}}

★ scores는 전문가별로 4개 축 각각의 점수(1~5)를 반드시 포함하세요:
  - evidence: 과학적 근거
  - universality: 범용성
  - proportionality: 비례성 (과도한 규제 여부)
  - readability: 가독성과 용어 설명
★ 5점은 해당 축에서 더 이상 개선할 여지가 없을 때만 부여하세요.
★ 라운드 1에서는 어떤 축도 5점을 넘기지 마세요. 최대 4점까지만 부여하세요.

참고 정보가 제공된 경우 이를 활용하여 더 정확한 검증을 수행하세요.
반드시 JSON만 출력하세요. 다른 설명은 불필요합니다.
""".strip()


def run_critic(state: AgentState) -> dict:
    """Critic 에이전트 실행 - 전문가별 평가"""
    current_round = state.get("current_round", 1)
    specialist_outputs = state.get("specialist_outputs", [])

    print(f"\n{'#'*80}")
    print(f"[CRITIC] Starting Critic agent - Round {current_round}/3")
    print(f"  Specialist outputs: {len(specialist_outputs)}")
    print(f"{'#'*80}\n")

    # Step 1: 웹 검색으로 검증 정보 수집
    web_context = ""
    try:
        web_result = web_search.invoke({"query": f"{state['topic']} NGT safety regulation verification"})
        web_context = f"\n\n## [웹 검색 결과 - 검증 참고]\n{web_result}"
        logger.info("Critic web search completed")
    except Exception as e:
        logger.warning(f"Critic web search failed: {e}")

    # Step 2: 전문가별 분석 결과 구성
    specialist_context = ""
    for so in specialist_outputs:
        specialist_context += (
            f"\n\n### [{so.get('role', '전문가')}] ({so.get('focus', '')})\n"
            f"{so.get('output', '')}\n"
        )

    # 이전 라운드 기록 참조 (전문가별 점수·피드백 누적)
    meeting_history = state.get("meeting_history", [])
    history_context = ""
    if meeting_history:
        for record in meeting_history:
            round_num = record.get("round", 0)
            scores = record.get("critique_scores", {})
            feedback = record.get("critique_feedback", "")
            spec_fb = record.get("specialist_feedback", {})
            history_context += f"\n[라운드 {round_num} 비평 기록]\n"
            history_context += f"전체 피드백: {feedback}\n"
            if scores:
                history_context += "전문가별 점수:\n"
                for role, score in scores.items():
                    history_context += f"  - {role}: {score}/5\n"
            if spec_fb:
                history_context += "전문가별 상세 피드백:\n"
                for role, fb in spec_fb.items():
                    history_context += f"  - {role}: {fb}\n"

    # Step 3: 프롬프트 구성
    user_message = f"""[팀 회의 라운드 {current_round}/3 - 비평 단계]

[전문가별 분석 결과]
{specialist_context}
{web_context}

{f'[이전 라운드 비평 기록]{history_context}' if history_context else ''}

위 전문가들의 분석 결과를 개별적으로 검토하고, JSON 형식으로 응답하세요.
각 전문가의 역할명을 키로 사용하세요.

★ 라운드 {current_round} 채점 원칙:
- 이전 라운드에서 지적한 약점이 해결되었으면 점수를 반드시 올려주세요.
- 이전 강점이 유지되고 있으면 점수를 내리지 마세요.
- specialist_feedback에 "개선된 점", "남은 약점", "5점을 위한 조치"를 포함하세요."""

    # Step 4: OpenAI 직접 호출
    print(f"[CRITIC] Calling OpenAI API via call_gpt")
    logger.info("Critic: Calling OpenAI directly...")

    try:
        response_content = call_gpt(SYSTEM_PROMPT, user_message)
        print(f"[CRITIC] OpenAI call succeeded - Response: {len(response_content)} chars")
    except Exception as e:
        print(f"[CRITIC ERROR] {type(e).__name__}: {e}")
        raise

    # JSON 파싱 — 축별 점수 (evidence, universality, proportionality, readability)
    SCORE_AXES = ("evidence", "universality", "proportionality", "readability")
    DEFAULT_AXIS_SCORES = {axis: 3 for axis in SCORE_AXES}

    def _normalize_scores(raw: dict) -> dict:
        """전문가별 점수를 {역할: {축: int}} 형태로 정규화"""
        normalized = {}
        for role, val in raw.items():
            if isinstance(val, dict):
                # 축별 점수가 정상적으로 들어온 경우
                axis_scores = {}
                for axis in SCORE_AXES:
                    try:
                        axis_scores[axis] = int(val.get(axis, 3))
                    except (ValueError, TypeError):
                        axis_scores[axis] = 3
                normalized[role] = axis_scores
            elif isinstance(val, (int, float)):
                # 기존 형식(통합 점수)으로 온 경우 → 모든 축에 동일 점수
                int_val = int(val)
                normalized[role] = {axis: int_val for axis in SCORE_AXES}
            else:
                # 문자열 등 → 숫자 추출 시도
                m = re.search(r'(\d)', str(val))
                int_val = int(m.group(1)) if m else 3
                normalized[role] = {axis: int_val for axis in SCORE_AXES}
        return normalized

    try:
        content = response_content.strip()
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:-1])

        data = json.loads(content)
        raw_scores = data.get("scores", {})
        scores = _normalize_scores(raw_scores)

        decision = data.get("decision", "continue")
        feedback = data.get("feedback", "")
        specialist_feedback = data.get("specialist_feedback", {})

        # 점수가 비어있으면 기본값
        if not scores and specialist_feedback:
            for role in specialist_feedback:
                scores[role] = dict(DEFAULT_AXIS_SCORES)
            logger.info(f"Critic scores empty, assigned defaults for {list(scores.keys())}")

        # 전문가별 피드백은 있는데 점수에 해당 키가 없는 경우 보충
        for role in specialist_feedback:
            if role not in scores:
                scores[role] = dict(DEFAULT_AXIS_SCORES)

        critique = CritiqueResult(
            decision=decision,
            feedback=feedback,
            scores=scores,
            specialist_feedback=specialist_feedback,
        )

        # 로그: 축별 점수 출력
        for role, axis_scores in scores.items():
            axis_str = " ".join(f"{a[0].upper()}={s}" for a, s in axis_scores.items())
            print(f"[CRITIC] {role}: {axis_str}")

    except (json.JSONDecodeError, KeyError) as e:
        logger.warning(f"Critic JSON parse failed: {e}, defaulting to continue")
        critique = CritiqueResult(
            decision="continue",
            feedback=response_content[:500],
            scores={},
            specialist_feedback={},
        )

    # 메시지 로그
    messages = list(state.get("messages", []))
    scores_parts = []
    for role, axis_scores in (critique.scores or {}).items():
        if isinstance(axis_scores, dict):
            avg = sum(axis_scores.values()) / len(axis_scores) if axis_scores else 0
            scores_parts.append(f"{role}=avg{avg:.1f}")
        else:
            scores_parts.append(f"{role}={axis_scores}")
    scores_str = ", ".join(scores_parts)
    messages.append({
        "role": "critic",
        "content": f"[라운드 {current_round}] 전문가 분석을 검토했습니다. (점수: {scores_str})\n{critique.feedback}",
    })

    return {
        "critique": critique,
        "messages": messages,
    }
