"""
Embedding Functions

OpenAI Embedding API를 사용한 벡터 생성
"""

import os
from typing import List

from openai import OpenAI

from .config import EMBEDDING_MODEL


def get_embedding_function():
    """
    OpenAI Embedding 함수 생성

    Returns:
        callable: 텍스트를 벡터로 변환하는 함수

    Raises:
        ValueError: OPENAI_API_KEY가 설정되지 않은 경우
    """
    # Lazy import to avoid loading settings at module import time
    from config import settings

    if not settings.OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY must be set in environment")

    client = OpenAI(api_key=settings.OPENAI_API_KEY)

    def embed_texts(texts: List[str]) -> List[List[float]]:
        """
        텍스트 리스트를 벡터로 변환

        Args:
            texts: 임베딩할 텍스트 리스트

        Returns:
            List[List[float]]: 벡터 리스트
        """
        if not texts:
            return []

        response = client.embeddings.create(
            model=EMBEDDING_MODEL,
            input=texts
        )

        embeddings = [item.embedding for item in response.data]
        return embeddings

    return embed_texts


def get_single_embedding(text: str) -> List[float]:
    """
    단일 텍스트 임베딩 생성

    Args:
        text: 임베딩할 텍스트

    Returns:
        List[float]: 벡터
    """
    embed_fn = get_embedding_function()
    embeddings = embed_fn([text])
    return embeddings[0] if embeddings else []
