"""OpenAI API 직접 호출 유틸리티 (httpx 사용)

OpenAI SDK 대신 httpx로 직접 HTTP 요청을 보냅니다.
SDK 레벨의 auto-instrumentation, monkey-patching 등을
완전히 우회하여 tool_calls 관련 문제를 근본적으로 방지합니다.
"""
import os
import sys
import json
import logging
import time
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
    max_tokens: int = 16384,
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
    max_retries = 5

    for attempt in range(max_retries):
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
            print(f"{'='*80}\n")

            # Rate Limit (429) 자동 재시도
            if response.status_code == 429:
                retry_after = 10  # 기본 대기 시간
                try:
                    err = response.json().get("error", {})
                    msg = err.get("message", "")
                    # "Please try again in 3.396s" 에서 대기 시간 추출
                    if "try again in" in msg:
                        wait_str = msg.split("try again in ")[1].split("s")[0]
                        retry_after = float(wait_str) + 1  # 여유 1초 추가
                except Exception:
                    pass
                retry_after = min(retry_after, 60)  # 최대 60초

                if attempt < max_retries - 1:
                    print(f"[LLM RATE LIMIT] 429 - waiting {retry_after:.1f}s before retry ({attempt+1}/{max_retries})")
                    logger.warning(f"[LLM] Rate limit hit, retrying in {retry_after:.1f}s (attempt {attempt+1})")
                    time.sleep(retry_after)
                    continue
                else:
                    error_body = response.text
                    raise RuntimeError(f"OpenAI API rate limit exceeded after {max_retries} retries: {error_body}")

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

            # API 레벨 에러 체크
            if "error" in data:
                error_msg = data["error"].get("message", str(data["error"]))
                logger.error(f"[LLM] OpenAI API Error: {error_msg}")
                raise RuntimeError(f"OpenAI API error: {error_msg}")

            # 응답 파싱
            choice = data["choices"][0]
            content = choice["message"].get("content") or ""

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
            print(f"[LLM TIMEOUT] Request timed out after 180 seconds")
            logger.error("[LLM] OpenAI API request timed out (180s)")
            if attempt < max_retries - 1:
                time.sleep(5)
                continue
            raise RuntimeError("OpenAI API request timed out")

        except RuntimeError:
            raise

        except Exception as e:
            print(f"[LLM EXCEPTION] {type(e).__name__}: {e}")
            logger.error(f"[LLM] Unexpected error: {type(e).__name__}: {e}")
            raise

    # for 루프가 정상 종료된 경우 (모든 재시도 소진)
    raise RuntimeError("OpenAI API call failed after all retries")


def call_gpt4o(system_prompt: str, user_message: str, **kwargs) -> str:
    """GPT-4o 호출 (PI, Critic용)"""
    model = os.environ.get("GPT4O_MODEL", "gpt-4o")
    return call_llm(system_prompt, user_message, model=model, **kwargs)


def call_gpt4o_mini(system_prompt: str, user_message: str, **kwargs) -> str:
    """GPT-4o-mini 호출 (Scientist용)"""
    model = os.environ.get("GPT4O_MINI_MODEL", "gpt-4o-mini")
    return call_llm(system_prompt, user_message, model=model, **kwargs)
