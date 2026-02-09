# @TASK P3-T2 - Dynamic Agent Factory
# @SPEC TASKS.md#P3-T2
# @TEST tests/test_factory.py
"""Dynamic Agent Factory - PI가 전문가 프로필을 동적으로 생성

전문가 프로필을 받아 동적으로 System Prompt를 생성하고
LangChain ChatOpenAI 인스턴스를 래핑한 에이전트를 반환합니다.
"""
from typing import Any

from utils.llm import call_gpt4o


def generate_system_prompt(profile: dict) -> str:
    """프로필로부터 System Prompt 생성

    Args:
        profile: 전문가 프로필 (role, focus, tools)

    Returns:
        str: 생성된 System Prompt
    """
    role = profile.get("role", "")
    focus = profile.get("focus", "")

    prompt = f"""
당신은 {role}입니다.

## 전문 분야
{focus}

## 당신의 임무
주어진 질문에 대해 전문 지식을 활용하여 정확하고 상세한 답변을 제공하세요.
유전자편집식품(NGT)의 안전성 평가와 관련된 질문이라면, 과학적 근거를 바탕으로
규제 당국이 활용할 수 있는 실질적인 정보를 제공해야 합니다.

**중요**: 답변은 명확하고 간결하게, 그리고 실무에 즉시 활용 가능한 형태로 작성하세요.
""".strip()

    return prompt


class SpecialistAgent:
    """동적으로 생성된 전문가 에이전트"""

    def __init__(self, system_prompt: str):
        """
        Args:
            system_prompt: System Prompt
        """
        self.system_prompt = system_prompt

    def invoke(self, query: str) -> str:
        """전문가 에이전트 실행

        Args:
            query: 사용자 질문

        Returns:
            str: LLM 응답 내용
        """
        return call_gpt4o(self.system_prompt, query)


def create_specialist(profile: dict) -> SpecialistAgent:
    """전문가 에이전트 생성

    프로필 정보를 바탕으로 동적으로 System Prompt를 생성하고
    GPT-4o를 사용하는 전문가 에이전트를 반환합니다.

    Args:
        profile: 전문가 프로필
            - role (str, required): 전문가 역할 (예: "Allergy Specialist")
            - focus (str, required): 전문 분야 (예: "allergen cross-reactivity")
            - tools (list, optional): 사용 가능한 도구 목록 (현재 미사용)

    Returns:
        SpecialistAgent: 호출 가능한 전문가 에이전트

    Raises:
        ValueError: 필수 필드(role, focus)가 누락된 경우

    Example:
        >>> profile = {
        ...     "role": "Plant Metabolomics Expert",
        ...     "focus": "fatty acid composition",
        ...     "tools": []
        ... }
        >>> agent = create_specialist(profile)
        >>> response = agent.invoke("대두 P34 단백질 분석")
    """
    # 필수 필드 검증
    if "role" not in profile:
        raise ValueError("프로필에 'role' 필드가 필요합니다.")
    if "focus" not in profile:
        raise ValueError("프로필에 'focus' 필드가 필요합니다.")

    # System Prompt 생성
    system_prompt = generate_system_prompt(profile)

    # 에이전트 생성 및 반환
    return SpecialistAgent(system_prompt=system_prompt)
