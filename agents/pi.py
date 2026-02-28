"""PI (Principal Investigator) Agent

연구 프로젝트의 총괄 책임자 역할을 수행합니다.
3라운드 팀 회의 워크플로우: planning, round summary, final synthesis.
OpenAI SDK 직접 호출.
"""
import json
import logging
import re
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List

from utils.llm import call_gpt
from data.guidelines import RESEARCH_AGENDA
from workflow.state import AgentState
from tools.web_search import web_search


def _sanitize_mermaid(report: str) -> str:
    """Mermaid 코드 블록 내 노드 텍스트의 특수문자를 이스케이프합니다.

    괄호 ()가 노드 레이블에 포함되면 Mermaid가 노드 형태 구분자로 해석하여
    파싱 에러가 발생합니다. 따옴표로 감싸지 않은 노드 레이블을 자동 수정합니다.
    """
    def fix_mermaid_block(match: re.Match) -> str:
        block = match.group(0)
        # 대괄호 노드: A[텍스트] → A["텍스트"] (이미 따옴표면 스킵)
        # 텍스트에 (, ), {, } 가 포함된 경우만 수정
        block = re.sub(
            r'\[([^\]"]*[(){}][^\]"]*)\]',
            lambda m: '["' + m.group(1).replace('"', "'") + '"]',
            block,
        )
        # 이중 중괄호 노드: A{{텍스트}} → A{{"텍스트"}}
        block = re.sub(
            r'\{\{([^}"]*[()][^}"]*)\}\}',
            lambda m: '{{"' + m.group(1).replace('"', "'") + '"}}',
            block,
        )
        return block

    # ```mermaid ... ``` 블록만 대상으로 처리
    return re.sub(
        r'```mermaid\s*\n.*?```',
        fix_mermaid_block,
        report,
        flags=re.DOTALL,
    )


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


SYSTEM_PROMPT = f"""당신은 연구 프로젝트의 총괄 책임자(PI)입니다.

## 연구 아젠다
{RESEARCH_AGENDA}

## 당신의 임무
Scientist와 Critic의 논의를 거쳐 승인된 초안을 바탕으로, 아래 파트로 구성된 최종 보고서를 작성하세요.
각 파트의 모든 하위 항목을 빠짐없이, 충분한 분량으로 상세히 서술해야 합니다.
위 5대 핵심 질문에 체계적으로 답하는 것이 보고서의 핵심 목표입니다.

## 보고서 포맷 (Markdown)

```
# 유전자편집식품(NGT) 표준 안전성 평가 프레임워크 (Final Report)

---

## 연구 방법론 (Research Methodology)

본 연구는 AI 기반 Virtual Lab 시스템을 활용하여 다학제 전문가 팀의 체계적 협업을 통해 수행되었다.

### 연구 수행 체계
- **총괄책임자(PI)**: 연구 방향 설정, 전문가 팀 구성, 라운드별 논의 종합 및 최종 보고서 작성
- **전문가 패널(Specialists)**: PI가 연구 주제에 맞게 구성한 다학제 전문가들이 각자 전문 분야의 분석 수행
- **독립 비평가(Critic)**: 전문가별 분석의 과학적 타당성, 논리적 일관성, 근거 충분성을 독립적으로 검증하고 1-5점 척도로 평가

### 3라운드 반복 심화 프로세스
1. **라운드 1**: 전문가 초기 분석 → 비평가 엄격 검증 → PI 쟁점 정리 및 임시 결론
2. **라운드 2**: 비평가 피드백 반영한 전문가 보완 분석 → 재검증 → PI 중간 종합
3. **라운드 3**: 최종 정제 분석 → 최종 검증 → PI 최종 종합 및 보고서 작성

각 라운드에서 비평가의 전문가별 점수와 구체적 피드백이 다음 라운드의 분석 개선에 직접 반영되며,
이 반복 과정을 통해 분석의 깊이와 정확성이 점진적으로 향상된다.

### 정보 검색 체계
- **RAG (Retrieval-Augmented Generation)**: Pinecone 벡터 데이터베이스에 저장된 규제 문서 및 학술 문헌 검색
- **Web Search**: Tavily API를 통한 최신 온라인 자료 검색 및 교차 검증
- **EFSA Journal Search**: EFSA 공식 학술지 전용 검색을 통한 규제 과학 근거 보강

### 연구 팀 구성 과정

#### 통계적 팀 구성 방법
본 연구의 재현성을 확보하기 위해, PI는 10회 독립적 팀 구성 실험을 수행하고
역할별 등장 빈도를 분석하여 최종 연구팀을 선정하였다.

##### 10회 시뮬레이션 전체 결과
(아래 정보가 제공되면 포함할 것)
- **총 생성된 과학자 에이전트 수**: 10회 실험에서 총 N명의 과학자 에이전트가 생성됨
- **시행별 팀 구성 테이블**:

| 시행 | 팀 규모 | 구성원 역할 |
|------|---------|------------|
| Trial 1 | N명 | 역할1, 역할2, ... |
| Trial 2 | N명 | 역할1, 역할2, ... |
| ... | ... | ... |

##### 역할별 등장 빈도 분석

| 역할 | 등장 횟수 | 백분율 | 전문분야 변형 |
|------|----------|--------|-------------|
| 역할1 | N회/10회 | N% | 변형1, 변형2 |
| ... | ... | ... | ... |

##### 팀 규모 분포
- N명: X회, M명: Y회, ...

##### PI의 최종 선정 과정 및 근거
- 왜 이 조합이 최적인지, 빈도 분석 결과를 바탕으로 한 선정 논리를 상세히 설명

#### 전문가 소개
(각 전문가가 자기 역할, 전문성, 이 연구에서의 기대 기여를 서술체로 소개.
한글 작성, 3-5문장, "저는 ~입니다" 형식의 대화형 자기소개.)

예시:
🤖 **유전체학 전문가 (Genomics Specialist)**
저는 유전체학 분야에서 15년간 연구해온 전문가입니다. 특히 CRISPR-Cas9 기반
유전자편집의 off-target 효과 분석과 전장 유전체 시퀀싱을 통한 비의도적 변이
검출에 전문성을 가지고 있습니다. 이번 연구에서 저는 유전자편집 과정에서
발생할 수 있는 분자 수준의 위험 요소를 식별하고, SDN-1/2/3 각 기술별
off-target 빈도와 특성을 비교 분석하는 역할을 담당하겠습니다.

### 에이전트별 기여도 통계
(아래 정보가 제공되면 표 형식으로 포함할 것)

| 에이전트 | 발화 횟수 | 총 글자수 |
|---|---|---|
| PI | N회 | N자 |
| Critic | N회 | N자 |
| 전문가1 | N회 | N자 |

---

## 핵심 질문 1: 식품에 적용되는 유전자편집기술의 분류 기준과 특성

### 라운드 1: 초기 분석
각 과학자 에이전트의 초기 분석 결과를 전문가별로 제시.
Critic의 평가 점수(1-5점) 및 구체적 피드백 포함.
PI의 1라운드 종합: 주요 쟁점, 합의 사항, 임시 결론.

### 라운드 2: 비평 반영 보완
Critic 피드백을 반영한 각 과학자의 보완 분석.
Critic의 재평가 및 점수 변화 포함.
PI의 2라운드 종합: 개선된 분석 포인트, 잔여 쟁점.

### 라운드 3: 최종 정제
각 과학자의 최종 정제된 분석.
Critic의 최종 평가 포함.
PI의 최종 종합 및 결론: 이 질문에 대한 확정된 답변.

---

## 핵심 질문 2: 유전자편집기술 분류별 우선 고려 위험요소

### 라운드 1: 초기 분석
(위와 동일한 구조: 전문가별 분석 → Critic 평가 → PI 종합)

### 라운드 2: 비평 반영 보완
(위와 동일한 구조)

### 라운드 3: 최종 정제
(위와 동일한 구조)

---

## 핵심 질문 3: 기존 위험평가 지침의 적용 가능성과 충분성

### 라운드 1: 초기 분석
(위와 동일한 구조)

### 라운드 2: 비평 반영 보완
(위와 동일한 구조)

### 라운드 3: 최종 정제
(위와 동일한 구조)

---

## 핵심 질문 4: 평가 항목 보완 및 기술적·실험적 평가 방법

### 라운드 1: 초기 분석
(위와 동일한 구조)

### 라운드 2: 비평 반영 보완
(위와 동일한 구조)

### 라운드 3: 최종 정제
(위와 동일한 구조)

---

## 핵심 질문 5: 단계적 의사결정 흐름 구성

### 라운드 1: 초기 분석
(위와 동일한 구조)

### 라운드 2: 비평 반영 보완
(위와 동일한 구조)

### 라운드 3: 최종 정제
(위와 동일한 구조)

---

## 참고문헌 (References)

### 5-1. Web Search Sources
(Tavily 웹 검색을 통해 참조한 온라인 자료의 URL과 제목을 번호 목록으로 정리)

### 5-2. Regulatory Documents (RAG)
(RAG 시스템을 통해 참조한 규제 문서·학술 문헌의 파일명, 페이지, 제목을 번호 목록으로 정리)

### 5-3. EFSA Journal Sources
(EFSA 공식 학술지에서 검색된 자료의 URL과 제목을 번호 목록으로 정리)

---

## 의사결정 흐름도 (Decision Tree)

NGT 식품의 위험평가 의사결정 흐름을 Mermaid 다이어그램으로 제시한다.
SDN-1, SDN-2, SDN-3, ODM 각 카테고리에 대한 단계적·비례적 평가 경로를 포함한다.

```mermaid
graph TD
    A["위험평가 시작"] --> B{{"기술 분류"}}
    B -->|SDN-1| C["간소화 평가"]
    B -->|SDN-2| D["중간 수준 평가"]
    B -->|SDN-3| E["전체 위험평가 - GM/rDNA 동등"]
    B -->|ODM| F["ODM 평가 경로"]
    ...
```

**Mermaid 문법 주의사항 (필수 준수)**:
- 노드 텍스트에 괄호 `()`, `{{}}` 등 특수문자가 포함되면 Mermaid 파싱 에러가 발생합니다.
- 모든 노드 레이블은 반드시 큰따옴표로 감싸세요: `A["텍스트"]`, `B{{{{"텍스트"}}}}` 형식.
- 예: `C3[GM(rDNA) 동등 심사]` → `C3["GM-rDNA 동등 심사"]` (괄호를 하이픈으로 대체하고 따옴표로 감싸기)
- 링크 레이블도 특수문자를 피하세요: `-->|"레이블"| 노드`

(위 예시를 참고하여, 연구 결과에 기반한 구체적이고 상세한 Decision Tree를 작성하세요.
각 분기점의 판단 기준, 필요한 평가 항목, 최종 결정(승인/추가검토/거부)을 포함하세요.)
```

**중요**:
- 반드시 위 5개 핵심 질문 각각에 대해 3라운드 구조를 빠짐없이 포함해야 합니다.
- 각 라운드에서 전문가별 분석, Critic 평가(점수 포함), PI 종합을 모두 서술하세요.
- 각 핵심 질문의 최종 라운드(라운드 3)에서는 해당 질문에 대한 확정된 결론을 명확히 도출하세요.
- 각 항목은 충분한 분량(최소 5-10문단)으로 상세히 서술하세요. 단순 나열이 아닌 분석적 서술이 필요합니다.
- 과학적 근거와 출처를 명시하세요.
- 참고 정보가 제공된 경우 이를 활용하여 보고서의 근거를 강화하세요.
- 의사결정 흐름도(Mermaid Decision Tree)는 반드시 포함하세요. `graph TD` 형식으로 SDN-1/2/3/ODM 경로를 모두 포함해야 합니다.
- '연구 방법론' 섹션에 팀 구성 과정(10회 시뮬레이션 전체 결과, 빈도 테이블, 선정 근거), 전문가 자기소개, 에이전트별 기여도 통계를 반드시 포함하세요.

**★ 핵심 원칙: 질문별 심화 (Question-Driven Deepening)**
- 5개 핵심 질문 각각이 3라운드에 걸쳐 점진적으로 심화되어야 합니다.
- 라운드 1의 초기 분석 → 라운드 2에서 Critic 피드백 반영 보완 → 라운드 3에서 최종 정제.
- 각 질문의 최종 결론은 이전 라운드의 논의를 종합한 것이어야 합니다.
- 핵심 질문 4에서는 반드시 핵심 질문 1-2에서 식별한 위험 요소와 핵심 질문 3에서 발견한 지침 한계점을 직접 참조하고, 각각에 대한 구체적 해결방안을 제시하세요.
- 핵심 질문 5의 의사결정 흐름은 핵심 질문 1-4의 결론을 통합하여 도출하세요.
"""


PI_SUMMARY_PROMPT = """당신은 연구 프로젝트의 총괄 책임자(PI)입니다.

## 당신의 임무
팀 회의의 현재 라운드 논의를 요약하고 임시 결론을 도출하세요.

## 요약 구조
다음 형식으로 라운드별 요약을 작성하세요:

### 주요 쟁점과 합의 사항
- 이번 라운드에서 논의된 핵심 쟁점들
- 전문가들 간 합의된 사항

### 미해결 쟁점
- 다음 라운드에서 추가 논의가 필요한 사항
- 전문가별 보완이 필요한 영역

### 임시 결론
- 현재까지의 분석을 종합한 중간 결론
- 5개 핵심 질문(기술 분류, 위험요소, 지침 적용성, 평가 보완, 의사결정 흐름) 관점에서의 진행 상황

**중요**: 각 전문가의 기여를 구체적으로 언급하고, 비평가의 지적 사항이 어떻게 반영되었는지 추적하세요.
"""


TEAM_DECISION_PROMPT = f"""당신은 연구 프로젝트의 총괄 책임자(PI)입니다.

## 연구 아젠다
{RESEARCH_AGENDA}

## 당신의 임무
사용자 질문과 위 연구 아젠다의 5대 핵심 질문을 분석하여,
각 질문에 효과적으로 답할 수 있는 전문가 팀을 구성하세요.
다학제적 관점에서 위험 식별, 규제 평가, 지침 업데이트, 통합 프레임워크 도출에
기여할 수 있는 전문가 조합을 선정하세요.

## 출력 형식 (JSON)
반드시 다음과 같은 JSON 배열 형식으로 답변하세요:
```json
[
  {{
    "role": "전문가 역할",
    "focus": "구체적인 집중 분야"
  }}
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

    response = call_gpt(TEAM_DECISION_PROMPT, user_message)

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


def _cluster_similar_roles(unique_roles: list[str]) -> dict[str, str]:
    """GPT를 사용하여 유사한 역할명을 대표 역할명으로 매핑.

    Returns:
        dict: {원래역할명: 대표역할명} 매핑
    """
    if len(unique_roles) <= 1:
        return {r: r for r in unique_roles}

    role_list = "\n".join(f"- {r}" for r in unique_roles)
    prompt = f"""다음은 연구팀 구성 실험에서 나온 전문가 역할명 목록입니다.
의미적으로 유사한 역할들을 하나의 대표 역할명으로 그룹핑하세요.

## 역할명 목록
{role_list}

## 지시사항
1. 전문 분야가 동일하거나 매우 유사한 역할들을 하나의 그룹으로 묶으세요.
2. 각 그룹의 대표 역할명은 가장 간결하고 포괄적인 이름을 선택하세요.
3. 서로 다른 분야의 역할은 별도 그룹으로 유지하세요.

## 출력 형식 (JSON)
```json
{{
  "clusters": [
    {{
      "canonical": "대표 역할명",
      "members": ["원래 역할명1", "원래 역할명2"]
    }}
  ]
}}
```
JSON만 출력하세요."""

    response = call_gpt(prompt, "역할명 클러스터링을 수행하세요.", temperature=0.2)
    try:
        content = response.strip()
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:-1])
        data = json.loads(content)

        mapping = {}
        for cluster in data.get("clusters", []):
            canonical = cluster["canonical"]
            for member in cluster["members"]:
                mapping[member] = canonical

        # 매핑에 없는 역할은 자기 자신으로
        for r in unique_roles:
            if r not in mapping:
                mapping[r] = r
        return mapping
    except (json.JSONDecodeError, KeyError):
        return {r: r for r in unique_roles}


def decide_team_statistically(user_query: str, n_trials: int = 10) -> dict:
    """10회 독립적 팀 구성 실험 후 빈도 분석으로 최종 팀 선정.

    Args:
        user_query: 연구 주제 + 제약 조건
        n_trials: 실험 횟수 (기본 10회)

    Returns:
        dict: {all_teams, frequency_analysis, final_team, rationale, frequency_table}
    """
    print(f"\n[STATISTICAL TEAM SELECTION] Running {n_trials} independent team compositions...")

    all_teams = []

    def _single_trial(trial_idx: int) -> list[dict] | None:
        try:
            team = decide_team(user_query)
            print(f"  Trial {trial_idx+1}/{n_trials}: {len(team)} specialists - {[m['role'] for m in team]}")
            return team
        except Exception as e:
            logger.warning(f"Trial {trial_idx+1} failed: {e}")
            return None

    # 병렬 실행 (5 workers)
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(_single_trial, i) for i in range(n_trials)]
        for future in as_completed(futures):
            result = future.result()
            if result:
                all_teams.append(result)

    if not all_teams:
        raise RuntimeError("모든 팀 구성 시도가 실패했습니다.")

    # 역할별 빈도 분석 (클러스터링 적용)
    # 1) 유니크 역할명 수집
    unique_roles = set()
    for team in all_teams:
        for member in team:
            unique_roles.add(member["role"])

    # 2) GPT로 유사 역할 클러스터링
    role_mapping = _cluster_similar_roles(list(unique_roles))
    print(f"  [CLUSTERING] {len(unique_roles)} unique roles → {len(set(role_mapping.values()))} clusters")

    # 3) 매핑된 대표명으로 빈도 카운트
    role_counter = Counter()
    role_focus_map: dict[str, list[str]] = {}
    team_size_counter = Counter()

    for team in all_teams:
        team_size_counter[len(team)] += 1
        for member in team:
            canonical_role = role_mapping.get(member["role"], member["role"])
            role_counter[canonical_role] += 1
            if canonical_role not in role_focus_map:
                role_focus_map[canonical_role] = []
            if member["focus"] not in role_focus_map[canonical_role]:
                role_focus_map[canonical_role].append(member["focus"])

    # 빈도 테이블 구성
    frequency_table = []
    for role, count in role_counter.most_common():
        frequency_table.append({
            "role": role,
            "count": count,
            "frequency": f"{count}/{len(all_teams)}",
            "percentage": round(count / len(all_teams) * 100, 1),
            "focus_variants": role_focus_map.get(role, []),
        })

    # 가장 빈번한 팀 규모
    most_common_size = team_size_counter.most_common(1)[0][0]

    # PI에게 최종 팀 선정 위임
    freq_summary = "\n".join(
        f"- {ft['role']}: {ft['count']}회/{len(all_teams)}회 ({ft['percentage']}%)"
        for ft in frequency_table
    )
    size_summary = ", ".join(f"{size}명: {cnt}회" for size, cnt in team_size_counter.most_common())

    selection_prompt = f"""당신은 연구 프로젝트의 총괄 책임자(PI)입니다.

10회 독립적 팀 구성 실험 결과를 분석하여 최종 연구팀을 확정하세요.

## 역할별 등장 빈도
{freq_summary}

## 팀 규모 분포
{size_summary}

## 지시사항
1. 빈도 분석 결과를 참고하되, 연구 목적에 가장 적합한 팀을 구성하세요.
2. 팀 규모는 {most_common_size}명을 권장합니다.
3. 각 전문가의 role과 focus를 확정하세요.
4. 선정 근거를 간략히 설명하세요.

## 출력 형식 (JSON)
```json
{{
  "team": [
    {{"role": "전문가 역할", "focus": "집중 분야"}}
  ],
  "rationale": "선정 근거 설명"
}}
```
JSON만 출력하세요.
"""

    response = call_gpt(selection_prompt, f"연구 주제: {user_query}")
    try:
        content = response.strip()
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:-1])
        data = json.loads(content)
        final_team = data.get("team", [])
        rationale = data.get("rationale", "")
    except (json.JSONDecodeError, KeyError):
        # 파싱 실패 시 가장 빈번한 역할들로 구성
        final_team = []
        for ft in frequency_table[:most_common_size]:
            final_team.append({
                "role": ft["role"],
                "focus": ft["focus_variants"][0] if ft["focus_variants"] else "",
            })
        rationale = "빈도 분석 기반 자동 선정 (LLM 응답 파싱 실패)"

    print(f"[STATISTICAL TEAM SELECTION] Final team: {len(final_team)} specialists")
    for m in final_team:
        print(f"  - {m['role']}: {m['focus']}")

    return {
        "all_teams": all_teams,
        "frequency_analysis": frequency_table,
        "final_team": final_team,
        "rationale": rationale,
        "frequency_table": freq_summary,
        "team_sizes": size_summary,
        "n_trials": len(all_teams),
    }


def generate_self_introductions(team: List[dict]) -> list[dict]:
    """최종 선별된 전문가들의 자기소개를 병렬로 생성합니다.

    Args:
        team: 전문가 팀 리스트 [{role, focus}, ...]

    Returns:
        list[dict]: [{role, focus, introduction}, ...]
    """
    print(f"\n[INTRODUCTIONS] Generating self-introductions for {len(team)} specialists...")

    introductions = []

    def _generate_one(profile: dict, idx: int) -> dict:
        role = profile.get("role", "")
        focus = profile.get("focus", "")
        prompt = (
            f"당신은 '{role}'입니다. 전문 분야는 '{focus}'입니다.\n\n"
            f"이 연구에 참여하는 전문가로서 한글 서술체 자기소개를 3-5문장으로 작성하세요.\n"
            f"반드시 '저는 ~입니다' 형식의 대화형으로 작성하세요.\n"
            f"포함할 내용:\n"
            f"1. 자신의 전문 분야와 경험 (구체적 연구 경력)\n"
            f"2. 핵심 전문성 (특화된 기술/방법론)\n"
            f"3. 이 연구에서 담당할 구체적 역할과 기대 기여\n\n"
            f"예시 형식:\n"
            f"저는 [분야] 분야에서 [N]년간 연구해온 전문가입니다. "
            f"특히 [구체적 전문성]에 전문성을 가지고 있습니다. "
            f"이번 연구에서 저는 [구체적 역할]을 담당하겠습니다."
        )
        try:
            intro = call_gpt("당신은 연구 전문가입니다. 한글 서술체로 자기소개를 작성하세요.", prompt, max_tokens=500)
            print(f"  [{idx+1}/{len(team)}] {role}: intro generated ({len(intro)} chars)")
            return {"role": role, "focus": focus, "introduction": intro.strip()}
        except Exception as e:
            logger.warning(f"Introduction generation failed for {role}: {e}")
            return {"role": role, "focus": focus, "introduction": f"{role}으로서 {focus} 분야를 담당합니다."}

    with ThreadPoolExecutor(max_workers=len(team)) as executor:
        futures = [executor.submit(_generate_one, p, i) for i, p in enumerate(team)]
        for future in as_completed(futures):
            introductions.append(future.result())

    return introductions


def run_pi_planning(state: AgentState) -> dict:
    """PI가 연구 주제를 분석하고 통계적 방법으로 전문가 팀을 구성합니다."""
    print(f"\n{'#'*80}")
    print(f"[PI PLANNING] Starting PI planning phase (Statistical Team Selection)")
    print(f"  Topic: {state.get('topic', 'N/A')}")
    print(f"{'#'*80}\n")

    topic = state["topic"]
    constraints = state.get("constraints", "")
    query = f"{topic}\n제약 조건: {constraints}"

    # 10팀 통계적 선별
    team_selection_data = None
    try:
        team_selection_data = decide_team_statistically(query)
        team = team_selection_data["final_team"]
        logger.info(f"PI decided team statistically: {len(team)} specialists from {team_selection_data['n_trials']} trials")
    except Exception as e:
        logger.warning(f"decide_team_statistically failed: {e}, using default team")
        team = [
            {"role": "NGT 분자생물학 전문가", "focus": "유전자편집 과정의 off-target 효과 및 분자적 특성 분석"},
            {"role": "식품안전성 평가 전문가", "focus": "독성, 알레르기, 영양성 평가 방법론"},
            {"role": "규제과학 전문가", "focus": "국제 규제 프레임워크 비교 및 지침 적용 가능성 분석"},
        ]

    # 전문가 자기소개 생성
    introductions = generate_self_introductions(team)

    # 팀 구성 내용을 메시지로 기록
    team_summary = "\n".join(
        [f"- **{m['role']}**: {m['focus']}" for m in team]
    )
    intro_summary = "\n".join(
        [f"- **{intro['role']}**: {intro['introduction']}" for intro in introductions]
    )
    messages = list(state.get("messages", []))
    messages.append({
        "role": "pi",
        "content": f"연구 팀을 구성했습니다 (10회 통계적 선별).\n\n{team_summary}\n\n### 전문가 자기소개\n{intro_summary}",
    })

    print(f"[PI PLANNING] Team composed: {len(team)} specialists")
    for m in team:
        print(f"  - {m['role']}: {m['focus']}")

    return {
        "team": team,
        "messages": messages,
        "team_selection_data": team_selection_data,
        "specialist_introductions": introductions,
    }


def run_pi_summary(state: AgentState) -> dict:
    """PI가 라운드별 논의를 요약하고 임시 결론을 도출합니다."""
    current_round = state.get("current_round", 1)
    specialist_outputs = state.get("specialist_outputs", [])
    critique = state.get("critique")
    meeting_history = state.get("meeting_history", [])

    print(f"\n{'#'*80}")
    print(f"[PI SUMMARY] Starting PI summary - Round {current_round}/3")
    print(f"  Specialist outputs: {len(specialist_outputs)}")
    print(f"{'#'*80}\n")

    # 이전 라운드 PI 요약 (연속성 확보)
    prev_summaries = ""
    for record in meeting_history:
        prev_summaries += f"\n[라운드 {record['round']} 임시 결론]\n{record['pi_summary']}\n"

    # 전문가 분석 결과 구성
    specialist_context = ""
    for so in specialist_outputs:
        specialist_context += (
            f"\n### [{so.get('role', '전문가')}] ({so.get('focus', '')})\n"
            f"{so.get('output', '')}\n"
        )

    # 비평가 피드백 (점수 포함)
    critique_text = ""
    if critique:
        critique_text = critique.feedback
        if critique.scores:
            critique_text += "\n\n[전문가별 점수]\n"
            for role, score in critique.scores.items():
                critique_text += f"- {role}: {score}/5\n"
        if critique.specialist_feedback:
            critique_text += "\n[전문가별 피드백]\n"
            for role, fb in critique.specialist_feedback.items():
                critique_text += f"- {role}: {fb}\n"

    user_message = (
        f"[팀 회의 라운드 {current_round}/3]\n"
        f"연구 주제: {state['topic']}\n\n"
        f"{'[이전 라운드 임시 결론]' + prev_summaries if prev_summaries else ''}\n\n"
        f"[이번 라운드 전문가 발표]\n{specialist_context}\n\n"
        f"[비평가 피드백]\n{critique_text}\n\n"
        f"라운드 {current_round}의 논의를 요약하세요:\n"
        f"1. 주요 쟁점과 합의 사항\n"
        f"2. 미해결 쟁점 (다음 라운드에서 다룰 것)\n"
        f"3. 임시 결론\n"
    )

    print(f"[PI SUMMARY] Calling OpenAI API via call_gpt")
    logger.info("PI summary: Calling OpenAI directly...")

    try:
        summary = call_gpt(PI_SUMMARY_PROMPT, user_message)
        print(f"[PI SUMMARY] OpenAI call succeeded - Summary: {len(summary)} chars")
    except Exception as e:
        print(f"[PI SUMMARY ERROR] {type(e).__name__}: {e}")
        raise

    # 메시지 로그
    messages = list(state.get("messages", []))
    messages.append({
        "role": "pi",
        "content": f"[라운드 {current_round}] 논의를 요약하고 임시 결론을 도출했습니다.",
    })

    return {
        "draft": summary,
        "messages": messages,
    }


def _compute_word_counts(messages: list[dict]) -> dict:
    """메시지 로그에서 에이전트별 발화 횟수 및 글자수를 계산합니다.

    Args:
        messages: 에이전트 간 메시지 로그

    Returns:
        dict: {agent_name: {"count": int, "chars": int}}
    """
    stats: dict[str, dict[str, int]] = {}

    for msg in messages:
        role = msg.get("role", "unknown")
        name = msg.get("name", role)  # specialist는 name 필드 사용
        content = msg.get("content", "")

        # 역할 정규화
        if role == "specialist":
            agent_key = name
        elif role == "pi":
            agent_key = "PI"
        elif role == "critic":
            agent_key = "Critic"
        else:
            agent_key = role

        if agent_key not in stats:
            stats[agent_key] = {"count": 0, "chars": 0}

        stats[agent_key]["count"] += 1
        stats[agent_key]["chars"] += len(content)

    return stats


def run_final_synthesis(state: AgentState) -> dict:
    """PI가 3라운드 전체 내용에서 베스트 파트를 선별하여 최종 보고서를 작성합니다."""
    meeting_history = state.get("meeting_history", [])
    current_round = state.get("current_round", 3)

    print(f"\n{'#'*80}")
    print(f"[PI FINAL SYNTHESIS] Starting final report synthesis")
    print(f"  Meeting history: {len(meeting_history)} rounds archived")
    print(f"  Current round: {current_round}")
    print(f"{'#'*80}\n")

    # 웹 검색으로 최신 정보 보강
    web_context = ""
    pi_sources = []
    try:
        web_result = web_search.invoke({"query": f"{state['topic']} NGT safety framework 2025"})
        web_context = f"\n\n## [웹 검색 결과 - 최신 정보]\n{web_result}"
        pi_sources.extend(_extract_sources(web_context))
        logger.info("PI final synthesis web search completed")
    except Exception as e:
        logger.warning(f"PI final synthesis web search failed: {e}")

    # EFSA Journal 검색 보강
    efsa_context = state.get("cached_efsa_context", "")
    if not efsa_context:
        try:
            from tools.web_search import efsa_search
            efsa_result = efsa_search.invoke({"query": f"{state['topic']} NGT safety assessment EFSA"})
            efsa_context = f"\n\n## [EFSA Journal 검색 결과]\n{efsa_result}"
            pi_sources.extend(_extract_sources(efsa_context))
            logger.info("PI final synthesis EFSA search completed")
        except Exception as e:
            logger.warning(f"PI final synthesis EFSA search failed: {e}")

    # 3라운드 전체 PI 요약 구성
    pi_summaries_text = ""
    for record in meeting_history:
        pi_summaries_text += (
            f"\n\n=== 라운드 {record['round']} 요약 ===\n"
            f"{record.get('pi_summary', '')}\n"
        )
    # 현재 라운드 (마지막) PI 요약도 포함
    current_draft = state.get("draft", "")
    if current_draft:
        pi_summaries_text += (
            f"\n\n=== 라운드 {current_round} 요약 ===\n"
            f"{current_draft}\n"
        )

    # 최종 라운드 전문가 결과 (가장 정제된 버전)
    round3_outputs = state.get("specialist_outputs", [])
    round3_text = ""
    for so in round3_outputs:
        round3_text += (
            f"\n### [{so.get('role', '전문가')}] ({so.get('focus', '')})\n"
            f"{so.get('output', '')}\n"
        )

    # 출처 수집
    all_sources = list(state.get("sources", []))
    all_sources.extend(pi_sources)
    for so in round3_outputs:
        all_sources.extend(_extract_sources(so.get("output", "")))
    seen = set()
    unique_sources = []
    for s in all_sources:
        if s not in seen:
            seen.add(s)
            unique_sources.append(s)

    # 출처 목록 텍스트
    sources_text = ""
    if unique_sources:
        sources_list = "\n".join(f"{i+1}. {s}" for i, s in enumerate(unique_sources))
        sources_text = f"\n\n[참조 출처 목록 - 반드시 보고서에 포함할 것]\n{sources_list}"

    print(f"[PI FINAL SYNTHESIS] Sources collected: {len(unique_sources)}")

    # 팀 구성 과정 데이터 (Phase 5) - 10회 시뮬레이션 전체 결과 포함
    team_composition_text = ""
    tsd = state.get("team_selection_data")
    if tsd:
        n_trials = tsd.get('n_trials', 0)

        # 시행별 전체 팀 구성 상세
        all_teams = tsd.get("all_teams", [])
        trials_detail = ""
        total_agents = 0
        if all_teams:
            trials_detail = "시행별 팀 구성 상세:\n"
            trials_detail += "| 시행 | 팀 규모 | 구성원 역할 |\n|------|---------|------------|\n"
            for i, trial_team in enumerate(all_teams):
                roles = [m.get("role", "?") for m in trial_team]
                total_agents += len(trial_team)
                trials_detail += f"| Trial {i+1} | {len(trial_team)}명 | {', '.join(roles)} |\n"
            trials_detail += f"\n총 생성된 과학자 에이전트 수: {n_trials}회 실험에서 총 {total_agents}명\n"

        # 빈도 분석 상세 (frequency_analysis에서 전문분야 변형 포함)
        freq_analysis = tsd.get("frequency_analysis", [])
        freq_detail = ""
        if freq_analysis:
            freq_detail = "역할별 등장 빈도 분석:\n"
            freq_detail += "| 역할 | 등장 횟수 | 백분율 | 전문분야 변형 |\n|------|----------|--------|-------------|\n"
            for ft in freq_analysis:
                variants = ", ".join(ft.get("focus_variants", [])[:3])
                freq_detail += f"| {ft['role']} | {ft['frequency']} | {ft['percentage']}% | {variants} |\n"

        team_composition_text = (
            f"\n\n[연구 팀 구성 과정 - 보고서 '연구 방법론' 섹션에 포함할 것]\n"
            f"10회 독립적 팀 구성 실험 수행 ({n_trials}회 성공)\n\n"
            f"{trials_detail}\n"
            f"{freq_detail}\n"
            f"팀 규모 분포: {tsd.get('team_sizes', '')}\n\n"
            f"PI의 최종 선정 근거: {tsd.get('rationale', '')}\n"
        )

    # 전문가 자기소개 (Phase 4) - 이미지 스타일 한글 대화형
    intro_text = ""
    intros = state.get("specialist_introductions", [])
    if intros:
        intro_lines = "\n\n".join(
            f"🤖 **{intro['role']}**\n{intro['introduction']}" for intro in intros
        )
        intro_text = f"\n\n[전문가 자기소개 - 보고서 '연구 방법론' 섹션에 아래 형식 그대로 포함할 것]\n{intro_lines}\n"

    # 에이전트별 발화 통계 (Phase 6)
    all_messages = list(state.get("messages", []))
    word_counts = _compute_word_counts(all_messages)
    word_counts_text = ""
    if word_counts:
        wc_lines = "| 에이전트 | 발화 횟수 | 총 글자수 |\n|---|---|---|\n"
        for agent, stats in sorted(word_counts.items()):
            wc_lines += f"| {agent} | {stats['count']}회 | {stats['chars']:,}자 |\n"
        word_counts_text = f"\n\n[에이전트별 기여도 통계 - 보고서 '연구 방법론' 섹션에 포함할 것]\n{wc_lines}\n"

    user_message = (
        f"연구 주제: {state['topic']}\n"
        f"제약 조건: {state.get('constraints', '')}\n\n"
        f"[3라운드 팀 회의 전체 요약]\n{pi_summaries_text}\n\n"
        f"[최종 라운드 전문가 분석 (정제본)]\n{round3_text}\n\n"
        f"{web_context}\n\n"
        f"{efsa_context}\n\n"
        f"{team_composition_text}\n"
        f"{intro_text}\n"
        f"{word_counts_text}\n"
        f"{sources_text}\n\n"
        f"위 3라운드 팀 회의의 모든 내용에서 가장 우수한 분석, 근거, 결론을 선별하여\n"
        f"최종 보고서를 작성하세요. 5개 핵심 질문 각각에 대해 3라운드 구조를 빠짐없이 포함하세요.\n\n"
        f"★ 핵심 1: 보고서를 5개 핵심 질문별 3라운드 회의록 구조로 작성하세요.\n"
        f"각 핵심 질문에 대해 라운드 1(초기 분석), 라운드 2(비평 반영 보완), 라운드 3(최종 정제)을 포함하고,\n"
        f"각 라운드에서 전문가별 분석, Critic 평가(점수 포함), PI 종합을 모두 서술하세요.\n\n"
        f"★ 핵심 2: '연구 방법론' 섹션에 팀 구성 과정(10회 시뮬레이션 전체 결과, 빈도 테이블, 선정 근거),\n"
        f"전문가 자기소개(한글 대화형), 에이전트별 기여도 통계를 반드시 포함하세요.\n\n"
        f"★ 핵심 3: 보고서 마지막에 '의사결정 흐름도 (Decision Tree)' 섹션을 반드시 포함하세요.\n"
        f"Mermaid `graph TD` 형식으로 SDN-1/SDN-2/SDN-3/ODM 각 카테고리의 위험평가 경로를\n"
        f"구체적으로 작성하세요. 각 분기점의 판단 기준과 필요 평가 항목을 명시하세요.\n\n"
        f"★ 핵심 4: 참고문헌(References) 섹션에 5-1(Web), 5-2(RAG), 5-3(EFSA) 출처를 정리하세요.\n"
    )

    print(f"[PI FINAL SYNTHESIS] Calling OpenAI API via call_gpt")
    logger.info("PI final synthesis: Calling OpenAI directly...")

    try:
        final_report = call_gpt(SYSTEM_PROMPT, user_message, max_tokens=65536)
        final_report = _sanitize_mermaid(final_report)
        print(f"[PI FINAL SYNTHESIS] OpenAI call succeeded - Final report: {len(final_report)} chars")
    except Exception as e:
        print(f"[PI FINAL SYNTHESIS ERROR] {type(e).__name__}: {e}")
        raise

    # 메시지 로그
    messages = list(state.get("messages", []))
    messages.append({
        "role": "pi",
        "content": "3라운드 팀 회의 결과를 종합하여 최종 보고서를 작성했습니다.",
    })

    return {
        "final_report": final_report,
        "messages": messages,
        "sources": unique_sources,
        "word_counts": word_counts,
    }
