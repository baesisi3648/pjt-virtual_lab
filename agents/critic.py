"""Scientific Critic Agent

각 과학자 에이전트의 분석 결과를 개별적으로 검토하고
전문가별 평가를 수행하는 비평가 에이전트입니다.
OpenAI SDK 직접 호출.
"""
import json
import logging
import re

from data.guidelines import CRITIQUE_RUBRIC
from utils.llm import call_gpt4o
from workflow.state import AgentState, CritiqueResult
from tools.web_search import web_search

logger = logging.getLogger(__name__)


SYSTEM_PROMPT = f"""당신은 과학적 타당성을 검증하는 독립적 비평가입니다.

## 참고 기준
{CRITIQUE_RUBRIC}

## 당신의 임무
각 과학자 에이전트의 분석 결과를 개별적으로 검토하세요.

## 전문가별 평가 기준
각 전문가에 대해 다음을 평가하세요:
1. **근거의 적절성**: 주장을 뒷받침하는 과학적 근거가 충분한가?
2. **논리적 비약 여부**: 전제에서 결론으로의 논리적 연결이 타당한가?
3. **대안적 해석 가능성**: 다른 해석이나 반론을 충분히 고려했는가?
4. **판단 기준 일관성**: '적용 가능', '부분 적용', '충분'의 기준이 일관적인가?

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

## 출력 형식 (JSON)
{{
  "decision": "continue",
  "feedback": "전체 요약 피드백 (주요 쟁점, 합의된 사항, 미해결 사항)",
  "scores": {{"전문가역할명1": 4, "전문가역할명2": 3}},
  "specialist_feedback": {{
    "전문가역할명1": "구체적 피드백 (강점, 약점, 개선 지시)",
    "전문가역할명2": "구체적 피드백 ..."
  }}
}}

★ scores 필드는 반드시 포함하세요. 각 전문가에 대해 1~5 사이의 정수 점수를 부여하세요.
  예: "scores": {{"NGT 분자생물학 전문가": 4, "식품안전성 평가 전문가": 3}}

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
    print(f"[CRITIC] Calling OpenAI API via call_gpt4o")
    logger.info("Critic: Calling OpenAI directly...")

    try:
        response_content = call_gpt4o(SYSTEM_PROMPT, user_message)
        print(f"[CRITIC] OpenAI call succeeded - Response: {len(response_content)} chars")
    except Exception as e:
        print(f"[CRITIC ERROR] {type(e).__name__}: {e}")
        raise

    # JSON 파싱
    try:
        content = response_content.strip()
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:-1])

        data = json.loads(content)
        raw_scores = data.get("scores", {})
        scores = {}
        for k, v in raw_scores.items():
            try:
                scores[k] = int(v)
            except (ValueError, TypeError):
                # "4/5", "4점", "4 점" 등 변형 파싱
                m = re.search(r'(\d)', str(v))
                scores[k] = int(m.group(1)) if m else 3

        decision = data.get("decision", "continue")
        feedback = data.get("feedback", "")
        specialist_feedback = data.get("specialist_feedback", {})

        # 점수가 비어있으면 content에서 점수 패턴 추출 시도
        if not scores and specialist_feedback:
            for role in specialist_feedback:
                scores[role] = 3
            logger.info(f"Critic scores empty, assigned default 3 for {list(scores.keys())}")

        # 전문가별 피드백은 있는데 점수에 해당 키가 없는 경우 보충
        for role in specialist_feedback:
            if role not in scores:
                scores[role] = 3

        critique = CritiqueResult(
            decision=decision,
            feedback=feedback,
            scores=scores,
            specialist_feedback=specialist_feedback,
        )

        print(f"[CRITIC] Decision: {decision}, Scores: {scores}")
        if specialist_feedback:
            print(f"[CRITIC] Specialist feedback keys: {list(specialist_feedback.keys())}")

    except (json.JSONDecodeError, KeyError) as e:
        logger.warning(f"Critic JSON parse failed: {e}, defaulting to continue")
        # 파싱 실패 시 content에서 점수 패턴 추출 시도
        fallback_scores = {}
        for m in re.finditer(r'["\']([^"\']+)["\']\s*:\s*(\d)\s*/\s*5', response_content):
            fallback_scores[m.group(1)] = int(m.group(2))
        if not fallback_scores:
            # "전문가명": 4 패턴도 시도
            for m in re.finditer(r'["\']([^"\']+)["\']\s*:\s*(\d)', response_content):
                name, val = m.group(1), int(m.group(2))
                if 1 <= val <= 5 and name not in ("decision", "feedback", "scores", "specialist_feedback"):
                    fallback_scores[name] = val
        critique = CritiqueResult(
            decision="continue",
            feedback=response_content[:500] if not fallback_scores else "JSON 파싱 실패, 점수만 추출됨",
            scores=fallback_scores,
            specialist_feedback={},
        )

    # 메시지 로그
    messages = list(state.get("messages", []))
    scores_str = ", ".join(f"{k}={v}" for k, v in (critique.scores or {}).items())
    messages.append({
        "role": "critic",
        "content": f"[라운드 {current_round}] 전문가 분석을 검토했습니다. (점수: {scores_str})\n{critique.feedback}",
    })

    return {
        "critique": critique,
        "messages": messages,
    }
