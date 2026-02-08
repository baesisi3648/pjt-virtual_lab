# @TASK P1-R1-T1 - OpenAI 모델 초기화 유틸리티
# @SPEC TASKS.md#P1-R1-T1
# @TEST tests/test_llm.py
"""OpenAI 모델 초기화 유틸리티

GPT-4o (PI, Critic 에이전트용)와 GPT-4o-mini (Scientist 에이전트용)
모델 인스턴스를 생성하는 팩토리 함수를 제공합니다.
"""
import os

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()


def get_gpt4o(temperature: float = 0.7, max_tokens: int = 4096) -> ChatOpenAI:
    """GPT-4o 모델 반환 (PI, Critic용)

    Args:
        temperature: 생성 온도 (기본 0.7)
        max_tokens: 최대 토큰 수 (기본 4096)

    Returns:
        ChatOpenAI: GPT-4o 모델 인스턴스

    Raises:
        ValueError: OPENAI_API_KEY 환경 변수가 설정되지 않은 경우
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")

    return ChatOpenAI(
        model=os.environ.get("GPT4O_MODEL", "gpt-4o"),
        temperature=temperature,
        max_tokens=max_tokens,
        api_key=api_key,
    )


def get_gpt4o_mini(temperature: float = 0.7, max_tokens: int = 4096) -> ChatOpenAI:
    """GPT-4o-mini 모델 반환 (Scientist용)

    Args:
        temperature: 생성 온도 (기본 0.7)
        max_tokens: 최대 토큰 수 (기본 4096)

    Returns:
        ChatOpenAI: GPT-4o-mini 모델 인스턴스

    Raises:
        ValueError: OPENAI_API_KEY 환경 변수가 설정되지 않은 경우
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")

    return ChatOpenAI(
        model=os.environ.get("GPT4O_MINI_MODEL", "gpt-4o-mini"),
        temperature=temperature,
        max_tokens=max_tokens,
        api_key=api_key,
    )
