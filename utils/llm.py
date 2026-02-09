"""OpenAI API 직접 호출 유틸리티 (httpx 사용)

OpenAI SDK 대신 httpx로 직접 HTTP 요청을 보냅니다.
SDK 레벨의 auto-instrumentation, monkey-patching 등을
완전히 우회하여 tool_calls 관련 문제를 근본적으로 방지합니다.
"""
import os
import sys
import json
import logging
import traceback

from dotenv import load_dotenv
import httpx

load_dotenv()

# __pycache__ 사용 방지
sys.dont_write_bytecode = True

logger = logging.getLogger(__name__)

# OpenAI API 엔드포인트
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

# httpx 클라이언트 (싱글톤, 커넥션 풀 재사용)
_http_client: httpx.Client | None = None


def _get_http_client() -> httpx.Client:
    """httpx 클라이언트 싱글톤 반환"""
    global _http_client
    if _http_client is None:
        _http_client = httpx.Client(timeout=180.0)
    return _http_client


def call_llm(
    system_prompt: str,
    user_message: str,
    model: str | None = None,
    temperature: float = 0.7,
    max_tokens: int = 4096,
) -> str:
    """OpenAI Chat Completion 직접 호출 (httpx)

    SDK를 거치지 않고 httpx로 직접 HTTP POST를 보냅니다.
    messages 배열은 항상 정확히 2개 (system + user)입니다.
    tools 파라미터를 절대 포함하지 않아 tool_calls 응답을 방지합니다.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")

    if model is None:
        model = os.environ.get("GPT4O_MODEL", "gpt-4o")

    # 메시지 배열: 정확히 2개만
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]

    # 요청 페이로드: tools 관련 파라미터 없음
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    # 상세 로깅: 요청 전 정보
    print(f"\n{'='*80}")
    print(f"[LLM REQUEST] Starting OpenAI API call")
    print(f"  Model: {model}")
    print(f"  Messages count: {len(messages)}")
    print(f"  System prompt: {len(system_prompt)} chars")
    print(f"  User message: {len(user_message)} chars")
    print(f"  Temperature: {temperature}, Max tokens: {max_tokens}")
    print(f"  Payload keys: {list(payload.keys())}")
    print(f"  Has 'tools' in payload: {'tools' in payload}")
    print(f"{'='*80}\n")

    logger.info(f"[LLM] httpx POST: model={model}, msg_count={len(messages)}")
    logger.info(f"[LLM] System prompt: {len(system_prompt)} chars")
    logger.info(f"[LLM] User message: {len(user_message)} chars")

    client = _get_http_client()

    try:
        response = client.post(
            OPENAI_API_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )

        # 상세 로깅: 응답 받음
        print(f"\n{'='*80}")
        print(f"[LLM RESPONSE] Received response from OpenAI")
        print(f"  Status code: {response.status_code}")
        print(f"  Response headers: {dict(response.headers)}")
        print(f"{'='*80}\n")

        # HTTP 에러 체크
        if response.status_code != 200:
            error_body = response.text
            print(f"\n{'!'*80}")
            print(f"[LLM ERROR] OpenAI API returned error!")
            print(f"  Status: {response.status_code}")
            print(f"  Error body: {error_body}")
            print(f"{'!'*80}\n")
            logger.error(f"[LLM] OpenAI API HTTP {response.status_code}: {error_body}")
            raise RuntimeError(
                f"OpenAI API error (HTTP {response.status_code}): {error_body}"
            )

        data = response.json()

        # 상세 로깅: 응답 데이터 구조
        print(f"\n{'='*80}")
        print(f"[LLM RESPONSE DATA] Parsing JSON response")
        print(f"  Response keys: {list(data.keys())}")
        if "choices" in data and len(data["choices"]) > 0:
            msg = data["choices"][0].get("message", {})
            print(f"  Message keys: {list(msg.keys())}")
            print(f"  Has 'tool_calls': {bool(msg.get('tool_calls'))}")
            if msg.get("tool_calls"):
                print(f"  Tool calls count: {len(msg['tool_calls'])}")
                print(f"  Tool call IDs: {[tc.get('id') for tc in msg['tool_calls']]}")
        print(f"{'='*80}\n")

        # API 레벨 에러 체크
        if "error" in data:
            error_msg = data["error"].get("message", str(data["error"]))
            error_type = data["error"].get("type", "unknown")
            error_param = data["error"].get("param", "unknown")

            print(f"\n{'!'*80}")
            print(f"[LLM API ERROR] OpenAI returned error in JSON!")
            print(f"  Type: {error_type}")
            print(f"  Param: {error_param}")
            print(f"  Message: {error_msg}")
            print(f"  Full error: {json.dumps(data['error'], indent=2)}")
            print(f"{'!'*80}\n")

            logger.error(f"[LLM] OpenAI API Error: {error_msg}")
            raise RuntimeError(f"OpenAI API error: {error_msg}")

        # 응답 파싱
        choice = data["choices"][0]
        content = choice["message"].get("content") or ""

        # tool_calls가 있으면 경고 (발생하면 안 됨)
        if choice["message"].get("tool_calls"):
            print(f"\n{'!'*80}")
            print(f"[LLM WARNING] Response contains tool_calls!")
            print(f"  This should NEVER happen - we didn't send 'tools' parameter")
            print(f"  Tool calls: {choice['message']['tool_calls']}")
            print(f"  Ignoring tool_calls and using text content only")
            print(f"{'!'*80}\n")

            logger.warning(
                "[LLM] WARNING: Response contains tool_calls despite no tools being sent! "
                "Ignoring tool_calls and returning text content only."
            )

        print(f"\n{'='*80}")
        print(f"[LLM SUCCESS] API call completed successfully")
        print(f"  Content length: {len(content)} chars")
        print(f"  Model used: {data.get('model', 'unknown')}")
        print(f"  Usage: {data.get('usage', {})}")
        print(f"{'='*80}\n")

        logger.info(
            f"[LLM] Response: {len(content)} chars, "
            f"model={data.get('model', 'unknown')}, "
            f"usage={data.get('usage', {})}"
        )
        return content

    except httpx.TimeoutException as e:
        print(f"\n{'!'*80}")
        print(f"[LLM TIMEOUT] Request timed out after 180 seconds")
        print(f"  Exception: {e}")
        print(f"{'!'*80}\n")
        logger.error("[LLM] OpenAI API request timed out (180s)")
        raise RuntimeError("OpenAI API request timed out")

    except Exception as e:
        print(f"\n{'!'*80}")
        print(f"[LLM EXCEPTION] Unexpected error occurred!")
        print(f"  Exception type: {type(e).__name__}")
        print(f"  Exception message: {e}")
        print(f"  Traceback:")
        print(traceback.format_exc())
        print(f"{'!'*80}\n")

        if not isinstance(e, RuntimeError):
            error_detail = traceback.format_exc()
            logger.error(f"[LLM] Unexpected error: {type(e).__name__}: {e}")
            logger.error(f"[LLM] Detail: {error_detail}")
        raise


def call_gpt4o(system_prompt: str, user_message: str, **kwargs) -> str:
    """GPT-4o 호출 (PI, Critic용)"""
    model = os.environ.get("GPT4O_MODEL", "gpt-4o")
    return call_llm(system_prompt, user_message, model=model, **kwargs)


def call_gpt4o_mini(system_prompt: str, user_message: str, **kwargs) -> str:
    """GPT-4o-mini 호출 (Scientist용)"""
    model = os.environ.get("GPT4O_MINI_MODEL", "gpt-4o-mini")
    return call_llm(system_prompt, user_message, model=model, **kwargs)
