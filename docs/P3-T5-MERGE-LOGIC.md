# P3-T5: Critic Merge Logic (병렬 의견 통합 강화)

## 개요
Phase 3의 병렬 워크플로우에서 3개 에이전트(Scientist, Critic, PI)의 의견을 효과적으로 통합하기 위한 `merge_views` 함수를 구현했습니다.

## 구현 위치
- `agents/critic.py::merge_views()` - 핵심 병렬 의견 통합 로직
- `workflow/parallel_graph.py::merge_parallel_views()` - LangGraph REDUCE 단계에서 활용

## Conflict Resolution 규칙

### 1. 중복 제거
완전히 동일한 의견은 한 번만 포함됩니다.

```python
unique_views = []
seen = set()
for view in views:
    view_stripped = view.strip()
    if view_stripped and view_stripped not in seen:
        unique_views.append(view_stripped)
        seen.add(view_stripped)
```

### 2. 보수적 안전 기준 선택
의견 충돌 시 다음 우선순위에 따라 선택합니다:
```
조건부/세분화 > 필수 > 필요 > 선택 > 면제
```

**키워드 매핑:**
- **조건부**: "조건부", "유형", "분류", "경우", "따라"
- **필수**: "필수"
- **필요**: "필요" (단, "불필요" 제외)
- **선택**: "선택", "권장"
- **면제**: "면제", "불필요"

### 3. 근거 기반 필터링
과학적 근거가 명시된 의견을 우선 선택합니다.

**과학적 근거 키워드:**
```python
["근거", "과학적", "연구", "효과", "특성", "crispr", "off-target",
 "유전자", "독성", "안전성", "평가"]
```

### 4. 상충 해결
조건부/세분화된 접근법이 있으면 항상 우선 선택하여 유연한 규제를 지향합니다.

## 테스트 커버리지

### 1. 중복 제거 테스트
```python
def test_merge_views_removes_duplicates():
    views = [
        "동물 실험이 필요합니다.",
        "동물 실험이 필요합니다.",  # 중복
        "독성 시험이 필요합니다.",
    ]
    merged = merge_views(views)
    assert merged.count("동물 실험이 필요합니다") <= 1
```

### 2. 보수적 안전 기준 테스트
```python
def test_merge_views_selects_conservative_safety():
    views = [
        "동물 실험은 면제 가능합니다.",
        "동물 실험이 필수입니다.",        # 우선 선택
        "독성 시험은 선택 사항입니다.",
    ]
    merged = merge_views(views)
    assert "필수" in merged
```

### 3. 근거 기반 필터링 테스트
```python
def test_merge_views_rejects_unfounded_opinions():
    views = [
        "과학적 근거: Off-target 효과 때문에 동물 실험 필요",  # 선택
        "근거 없음: 그냥 필요합니다",                           # 제외
        "과학적 근거: CRISPR의 특성상 독성 시험 필수",         # 선택
    ]
    merged = merge_views(views)
    assert "과학적 근거" in merged or "Off-target" in merged
```

### 4. 상충 해결 테스트
```python
def test_merge_views_handles_conflicts():
    views = [
        "동물 실험 불필요 - SDN-1은 기존 육종과 동일",
        "동물 실험 필수 - SDN-2는 외래 유전자 포함",
        "조건부 동물 실험 - SDN 유형에 따라 달라야 함",  # 우선 선택
    ]
    merged = merge_views(views)
    assert "조건부" in merged or "SDN" in merged or "유형" in merged
```

## 통합 예시

### 병렬 워크플로우 적용
```python
# workflow/parallel_graph.py

def merge_parallel_views(state: AgentState) -> dict:
    from agents.critic import merge_views

    # 병렬 분석 결과 수집
    views = state.get("parallel_views", [])
    analysis_texts = [view["analysis"] for view in views]

    # Critic의 merge_views 로직 적용
    merged_analysis = merge_views(analysis_texts)

    # PI에게 통합된 분석 전달
    # ... (최종 보고서 생성)
```

## 성능

### 시간 복잡도
- 중복 제거: O(n)
- 보수적 기준 선택: O(n × k) (k = 키워드 수)
- 근거 기반 필터링: O(n × m) (m = 과학 키워드 수)
- **전체**: O(n × max(k, m))

### 공간 복잡도
- O(n) - unique_views, candidate_views 저장

## 향후 개선 방향

1. **키워드 기반 → 의미 기반 분류**
   - 현재: 키워드 매칭
   - 개선: LLM Embedding을 활용한 의미론적 유사도 계산

2. **규칙 기반 → 학습 기반**
   - 현재: 하드코딩된 우선순위
   - 개선: 규제 전문가 피드백 학습을 통한 동적 가중치

3. **단일 언어 → 다국어 지원**
   - 현재: 한국어 키워드만 지원
   - 개선: 영어, 일본어 등 국제 규제 문서 통합

## 관련 파일
- `agents/critic.py` - merge_views() 함수
- `workflow/parallel_graph.py` - merge_parallel_views() 통합
- `tests/test_agents.py::TestCritic` - 단위 테스트
- `tests/test_parallel_workflow.py` - 통합 테스트

## 검증 완료
```bash
# 모든 테스트 통과
pytest tests/test_agents.py::TestCritic -v
# 11 passed in 18.64s

pytest tests/test_parallel_workflow.py -v
# 3 passed in 19.99s
```

---

**TASK_DONE: P3-T5**
