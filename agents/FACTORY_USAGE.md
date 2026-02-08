# Dynamic Agent Factory - 사용 가이드

## 개요
`agents.factory` 모듈은 PI가 전문가 프로필을 동적으로 생성할 수 있도록 지원합니다.

## 기본 사용법

```python
from agents.factory import create_specialist

# 1. 전문가 프로필 정의
profile = {
    "role": "Allergy Specialist",
    "focus": "protein allergenicity and cross-reactivity",
    "tools": []  # 선택사항
}

# 2. 전문가 에이전트 생성
expert = create_specialist(profile)

# 3. 질의 수행
response = expert.invoke("대두 P34 단백질 분석")
print(response)
```

## 프로필 구조

### 필수 필드
- `role` (str): 전문가 역할 (예: "Toxicologist", "Nutritionist")
- `focus` (str): 전문 분야 (예: "acute toxicity", "nutrient composition")

### 선택 필드
- `tools` (list): 사용 가능한 도구 목록 (현재 미사용, 향후 확장 가능)

## 사용 예제

### 예제 1: 알레르기 전문가
```python
allergist = create_specialist({
    "role": "Allergy Specialist",
    "focus": "allergen cross-reactivity"
})

response = allergist.invoke(
    "유전자편집 대두의 P34 단백질 변화가 알레르겐성에 미치는 영향은?"
)
```

### 예제 2: 독성 전문가
```python
toxicologist = create_specialist({
    "role": "Toxicologist",
    "focus": "acute and chronic toxicity assessment"
})

response = toxicologist.invoke(
    "NGT 작물의 독성 평가를 위한 필수 시험 항목은?"
)
```

### 예제 3: 여러 전문가 동시 활용
```python
# 전문가 패널 구성
experts = {
    "metabolomics": create_specialist({
        "role": "Plant Metabolomics Expert",
        "focus": "fatty acid composition and secondary metabolites"
    }),
    "genomics": create_specialist({
        "role": "Genomics Specialist",
        "focus": "off-target effects and gene stability"
    }),
    "regulation": create_specialist({
        "role": "Regulatory Consultant",
        "focus": "international compliance requirements"
    })
}

# 각 전문가에게 동일한 질문
query = "유전자편집 대두의 안전성 평가 요건은?"
for name, expert in experts.items():
    print(f"[{name}]")
    print(expert.invoke(query))
    print()
```

## 내부 동작

### System Prompt 생성
`generate_system_prompt(profile)` 함수가 프로필 정보를 바탕으로 동적으로 System Prompt를 생성합니다.

```python
# 생성된 System Prompt 예시
당신은 Allergy Specialist입니다.

## 전문 분야
allergen cross-reactivity

## 당신의 임무
주어진 질문에 대해 전문 지식을 활용하여 정확하고 상세한 답변을 제공하세요.
유전자편집식품(NGT)의 안전성 평가와 관련된 질문이라면, 과학적 근거를 바탕으로
규제 당국이 활용할 수 있는 실질적인 정보를 제공해야 합니다.

**중요**: 답변은 명확하고 간결하게, 그리고 실무에 즉시 활용 가능한 형태로 작성하세요.
```

### LLM 모델
- 모든 전문가는 **GPT-4o** 모델을 사용합니다.
- `utils.llm.get_gpt4o()`를 통해 초기화됩니다.

## 에러 처리

```python
# ValueError: 필수 필드 누락
try:
    expert = create_specialist({"focus": "test"})  # role 누락
except ValueError as e:
    print(e)  # "프로필에 'role' 필드가 필요합니다."

try:
    expert = create_specialist({"role": "Expert"})  # focus 누락
except ValueError as e:
    print(e)  # "프로필에 'focus' 필드가 필요합니다."
```

## 확장 가능성

### 향후 Tools 바인딩 지원 예정
```python
# 향후 버전에서 가능할 기능
expert = create_specialist({
    "role": "Bioinformatics Specialist",
    "focus": "sequence alignment and homology",
    "tools": ["rag_search", "web_search", "blast_search"]  # 도구 활용
})
```

## 테스트
```bash
# 단위 테스트
pytest tests/test_factory.py -v

# 통합 테스트
pytest tests/test_factory_integration.py -v
```

## 참고
- 실제 구현: `agents/factory.py`
- 단위 테스트: `tests/test_factory.py`
- 통합 테스트: `tests/test_factory_integration.py`
