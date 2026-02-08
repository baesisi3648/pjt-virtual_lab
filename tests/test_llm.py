# @TASK P1-R1-T1 - OpenAI 모델 초기화 모듈 테스트
# @SPEC TASKS.md#P1-R1-T1
"""LLM 유틸리티 테스트"""
import pytest
from unittest.mock import patch, MagicMock


class TestGetGPT4o:
    """GPT-4o 모델 초기화 테스트"""

    @patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test-key"})
    def test_returns_chat_model(self):
        from utils.llm import get_gpt4o
        model = get_gpt4o()
        assert model is not None

    @patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test-key"})
    def test_model_name_is_gpt4o(self):
        from utils.llm import get_gpt4o
        model = get_gpt4o()
        assert model.model_name == "gpt-4o"

    @patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test-key"})
    def test_temperature_is_set(self):
        from utils.llm import get_gpt4o
        model = get_gpt4o()
        assert model.temperature == 0.7


class TestGetGPT4oMini:
    """GPT-4o-mini 모델 초기화 테스트"""

    @patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test-key"})
    def test_returns_chat_model(self):
        from utils.llm import get_gpt4o_mini
        model = get_gpt4o_mini()
        assert model is not None

    @patch.dict("os.environ", {"OPENAI_API_KEY": "sk-test-key"})
    def test_model_name_is_gpt4o_mini(self):
        from utils.llm import get_gpt4o_mini
        model = get_gpt4o_mini()
        assert model.model_name == "gpt-4o-mini"


class TestAPIKeyValidation:
    """API 키 검증 테스트"""

    @patch.dict("os.environ", {}, clear=True)
    def test_raises_without_api_key(self):
        # 모듈 캐시 제거하여 재로드
        import importlib
        import utils.llm
        importlib.reload(utils.llm)
        from utils.llm import get_gpt4o
        with pytest.raises((ValueError, Exception)):
            get_gpt4o()
