"""LLM call utilities.

- OpenAI (PI, specialists, translator): direct HTTP calls with httpx, as in the
  submitted version (no SDK instrumentation, no `tools` parameter).
- Anthropic (Scientific Critic, revision C16): official `anthropic` SDK.

Revision changes (reference/revision/revision_plan.md):
- C13: an empty or truncated response is retried once, then raises
  LLMIncompleteError. HTTP/transport retries and incomplete-response retries
  use separate budgets.
- C5: every call is appended to the run's call log (utils.call_log) with the
  exact inputs, the parameters actually sent and omitted, every attempt, the raw
  response, the response model identifier, usage and stop reason.
- C16: no server-side model fallback is enabled for the Critic, so a run can
  never be scored by a model other than the one recorded for its condition.
"""
import logging
import os
import sys
import time

import httpx
from dotenv import load_dotenv

from utils import call_log
from utils.errors import LLMIncompleteError

load_dotenv()

# __pycache__ 사용 방지
sys.dont_write_bytecode = True

logger = logging.getLogger(__name__)

# Retries allowed for an empty or truncated response before failing closed (C13).
MAX_INCOMPLETE_RETRIES = 1
# HTTP / transport retries per request (unchanged from the submitted version).
MAX_HTTP_RETRIES = 5

OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"

# Critic (C16)
DEFAULT_CRITIC_MODEL = "claude-opus-5-5"
DEFAULT_CRITIC_EFFORT = "high"
CRITIC_MAX_TOKENS = 64000

_http_client: httpx.Client | None = None
_anthropic_client = None


def _get_http_client() -> httpx.Client:
    """httpx client singleton (connection pool reuse)."""
    global _http_client
    if _http_client is None:
        _http_client = httpx.Client(timeout=600.0)
    return _http_client


def _get_anthropic_client():
    global _anthropic_client
    if _anthropic_client is None:
        import anthropic
        # Reads ANTHROPIC_API_KEY from the environment (.env loaded above).
        # SDK retries off: transport retries are done (and logged) in call_claude.
        _anthropic_client = anthropic.Anthropic(max_retries=0)
    return _anthropic_client


def _default_temperature() -> float:
    """Temperature for models that accept it (not used for GPT-5 / o-series).

    Set `VIRTUAL_LAB_TEMPERATURE` to override. GPT-5 requests omit temperature
    entirely; the call log records that omission.
    """
    raw = os.environ.get("VIRTUAL_LAB_TEMPERATURE")
    if raw is not None:
        try:
            return float(raw)
        except ValueError:
            pass
    return 0.2


def _log(entry: dict) -> None:
    try:
        call_log.record(entry)
    except Exception as e:  # logging must never mask the original outcome
        logger.error(f"[CALL LOG] failed to record call: {e}")
        raise


# --------------------------------------------------------------------------- OpenAI

def call_llm(
    system_prompt: str,
    user_message: str,
    model: str | None = None,
    temperature: float | None = None,
    max_tokens: int = 32768,
    tag: dict | None = None,
) -> str:
    """Call the OpenAI Chat Completions API with exactly two messages.

    Raises LLMIncompleteError if the response stays empty or truncated after
    MAX_INCOMPLETE_RETRIES, and RuntimeError on unrecoverable HTTP errors.
    """
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY 환경 변수가 설정되지 않았습니다.")

    if model is None:
        model = os.environ.get("GPT_MODEL", "gpt-4o")
    if temperature is None:
        temperature = _default_temperature()

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message},
    ]
    # GPT-5, o3, o4: max_completion_tokens and no custom temperature.
    use_new_api = any(model.startswith(p) for p in ("gpt-5", "o3", "o4"))
    token_key = "max_completion_tokens" if use_new_api else "max_tokens"
    payload = {"model": model, "messages": messages, token_key: max_tokens}
    omitted = []
    if use_new_api:
        omitted.append("temperature")
    else:
        payload["temperature"] = temperature
    omitted.append("reasoning_effort")  # never sent: provider default applies

    call_id = call_log.new_call_id()
    started = time.time()
    attempts: list[dict] = []
    base_entry = {
        "call_id": call_id,
        "started_utc": call_log.now_utc(),
        "provider": "openai",
        "tag": tag or {},
        "request": {k: v for k, v in payload.items() if k != "messages"},
        "omitted_parameters": omitted,
        "system_prompt": system_prompt,
        "user_message": user_message,
    }

    def _finish(status: str, **extra) -> None:
        _log({**base_entry, **extra, "status": status, "attempts": attempts,
              "latency_s": round(time.time() - started, 3), "finished_utc": call_log.now_utc()})

    logger.info(f"[LLM] OpenAI call: model={model}, tag={tag}")
    client = _get_http_client()
    incomplete_info = None
    try:
        for incomplete_attempt in range(1 + MAX_INCOMPLETE_RETRIES):
            incomplete_info = None
            for attempt in range(MAX_HTTP_RETRIES):
                try:
                    response = client.post(
                        OPENAI_API_URL,
                        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                        json=payload,
                    )
                except httpx.TransportError as e:
                    # Timeouts and connection errors are recorded and retried.
                    attempts.append({"http_status": None, "error_type": type(e).__name__, "error": str(e)[:500]})
                    logger.error(f"[LLM] OpenAI transport error: {type(e).__name__}")
                    if attempt < MAX_HTTP_RETRIES - 1:
                        time.sleep(5)
                        continue
                    raise RuntimeError(f"OpenAI API transport error after {MAX_HTTP_RETRIES} attempts")

                request_id = response.headers.get("x-request-id") if hasattr(response, "headers") else None
                if response.status_code == 429:
                    retry_after = 10.0
                    try:
                        msg = response.json().get("error", {}).get("message", "")
                        if "try again in" in msg:
                            retry_after = float(msg.split("try again in ")[1].split("s")[0]) + 1
                    except Exception:
                        pass
                    retry_after = min(retry_after, 60)
                    attempts.append({"http_status": 429, "request_id": request_id})
                    if attempt < MAX_HTTP_RETRIES - 1:
                        logger.warning(f"[LLM] Rate limit, retrying in {retry_after:.1f}s")
                        time.sleep(retry_after)
                        continue
                    raise RuntimeError(f"OpenAI API rate limit exceeded after {MAX_HTTP_RETRIES} retries")

                if response.status_code in (500, 502, 503, 504):
                    attempts.append({"http_status": response.status_code, "request_id": request_id})
                    if attempt < MAX_HTTP_RETRIES - 1:
                        time.sleep(min(5 * (attempt + 1), 30))
                        continue
                    raise RuntimeError(
                        f"OpenAI API server error (HTTP {response.status_code}) after {MAX_HTTP_RETRIES} retries"
                    )

                if response.status_code != 200:
                    attempts.append({"http_status": response.status_code, "request_id": request_id,
                                     "error_body": response.text[:2000]})
                    raise RuntimeError(f"OpenAI API error (HTTP {response.status_code}): {response.text}")

                try:
                    data = response.json()
                    data["choices"][0]["message"]
                except Exception as e:
                    attempts.append({"http_status": 200, "request_id": request_id,
                                     "error_type": type(e).__name__, "error": str(e)[:500],
                                     "raw_body": getattr(response, "text", "")[:4000]})
                    raise
                if "error" in data:
                    attempts.append({"http_status": 200, "request_id": request_id, "api_error": data["error"]})
                    raise RuntimeError(f"OpenAI API error: {data['error'].get('message', data['error'])}")

                choice = data["choices"][0]
                content = choice["message"].get("content") or ""
                finish_reason = choice.get("finish_reason")
                attempts.append({
                    "http_status": 200,
                    "request_id": request_id,
                    "finish_reason": finish_reason,
                    "response_model": data.get("model"),
                    "system_fingerprint": data.get("system_fingerprint"),
                    "usage": data.get("usage"),
                    "content_chars": len(content),
                    "raw_content": content,
                })

                # C13: leave the HTTP loop on an incomplete response; the outer
                # loop spends its own, separate budget.
                if finish_reason != "stop" or not content.strip():
                    incomplete_info = (finish_reason, len(content), data.get("model"))
                    break

                _finish("ok", response_model=data.get("model"),
                        system_fingerprint=data.get("system_fingerprint"),
                        usage=data.get("usage"), finish_reason=finish_reason,
                        request_id=request_id, response_text=content)
                return content
            else:
                raise RuntimeError("OpenAI API call failed after all retries")

            logger.warning(
                f"[LLM] Incomplete response (finish_reason={incomplete_info[0]}, "
                f"chars={incomplete_info[1]}), attempt {incomplete_attempt + 1}"
            )

        raise LLMIncompleteError(
            f"Incomplete LLM response after {1 + MAX_INCOMPLETE_RETRIES} attempts "
            f"(finish_reason={incomplete_info[0]}, chars={incomplete_info[1]}, model={incomplete_info[2]})"
        )
    except Exception as e:
        _finish("error", error_type=type(e).__name__, error=str(e)[:2000])
        raise


def call_gpt(system_prompt: str, user_message: str, **kwargs) -> str:
    """GPT model call (single generation model, env GPT_MODEL)."""
    model = os.environ.get("GPT_MODEL", "gpt-4o")
    return call_llm(system_prompt, user_message, model=model, **kwargs)


# Backward-compatible aliases
def call_gpt4o(system_prompt: str, user_message: str, **kwargs) -> str:
    return call_gpt(system_prompt, user_message, **kwargs)


def call_gpt4o_mini(system_prompt: str, user_message: str, **kwargs) -> str:
    return call_gpt(system_prompt, user_message, **kwargs)


# --------------------------------------------------------------------------- Anthropic

def call_claude(
    system_prompt: str,
    user_message: str,
    model: str | None = None,
    effort: str | None = None,
    max_tokens: int = CRITIC_MAX_TOKENS,
    tag: dict | None = None,
) -> str:
    """Call Claude through the official SDK (streaming, adaptive thinking).

    Thinking is not configured explicitly (adaptive by default on the model);
    depth is set with output_config.effort. No sampling parameters and no
    server-side fallback are sent. A response that is empty or does not end with
    stop_reason "end_turn" (for example "max_tokens" or "refusal") is retried once
    and then raises LLMIncompleteError.
    """
    model = model or os.environ.get("CRITIC_MODEL", DEFAULT_CRITIC_MODEL)
    effort = effort or os.environ.get("CRITIC_EFFORT", DEFAULT_CRITIC_EFFORT)
    request = {"model": model, "max_tokens": max_tokens, "output_config": {"effort": effort}}

    call_id = call_log.new_call_id()
    started = time.time()
    attempts: list[dict] = []
    base_entry = {
        "call_id": call_id,
        "started_utc": call_log.now_utc(),
        "provider": "anthropic",
        "tag": tag or {},
        "request": request,
        "omitted_parameters": ["temperature", "top_p", "top_k", "thinking", "fallbacks"],
        "system_prompt": system_prompt,
        "user_message": user_message,
    }

    def _finish(status: str, **extra) -> None:
        _log({**base_entry, **extra, "status": status, "attempts": attempts,
              "latency_s": round(time.time() - started, 3), "finished_utc": call_log.now_utc()})

    logger.info(f"[LLM] Anthropic call: model={model}, effort={effort}, tag={tag}")
    client = _get_anthropic_client()
    last = None
    import anthropic

    def _stream_once():
        """One streamed request with recorded transport retries (SDK retries disabled)."""
        for http_attempt in range(MAX_HTTP_RETRIES):
            try:
                with client.messages.stream(
                    model=model,
                    max_tokens=max_tokens,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_message}],
                    output_config={"effort": effort},
                ) as stream:
                    message = stream.get_final_message()
                    request_id = stream.request_id
                return message, request_id
            except (anthropic.APIConnectionError, anthropic.RateLimitError, anthropic.InternalServerError) as e:
                attempts.append({"error_type": type(e).__name__, "http_status": getattr(e, "status_code", None),
                                 "request_id": getattr(e, "request_id", None), "error": str(e)[:500]})
                logger.warning(f"[LLM] Anthropic transient error {type(e).__name__}, attempt {http_attempt + 1}")
                if http_attempt < MAX_HTTP_RETRIES - 1:
                    time.sleep(min(5 * (http_attempt + 1), 30))
                    continue
                raise
            except anthropic.APIStatusError as e:
                attempts.append({"error_type": type(e).__name__, "http_status": e.status_code,
                                 "request_id": getattr(e, "request_id", None), "error": str(e)[:500]})
                raise
            except Exception as e:
                attempts.append({"error_type": type(e).__name__, "error": str(e)[:500]})
                raise

    try:
        for incomplete_attempt in range(1 + MAX_INCOMPLETE_RETRIES):
            message, request_id = _stream_once()
            text = "".join(b.text for b in message.content if getattr(b, "type", None) == "text")
            usage = message.usage.model_dump() if hasattr(message.usage, "model_dump") else dict(message.usage)
            stop_details = getattr(message, "stop_details", None)
            attempt = {
                "request_id": request_id,
                "message_id": message.id,
                "response_model": message.model,
                "stop_reason": message.stop_reason,
                "stop_details": stop_details.model_dump() if hasattr(stop_details, "model_dump") else stop_details,
                "usage": usage,
                "content_chars": len(text),
                "raw_content": text,
                # All response blocks (thinking blocks carry only a signature when display is omitted).
                "raw_message": message.model_dump() if hasattr(message, "model_dump") else None,
            }
            attempts.append(attempt)
            if message.stop_reason == "end_turn" and text.strip():
                _finish("ok", response_model=message.model, usage=usage,
                        stop_reason=message.stop_reason, request_id=attempt["request_id"],
                        response_text=text)
                return text
            last = attempt
            logger.warning(
                f"[LLM] Incomplete Claude response (stop_reason={message.stop_reason}, "
                f"chars={len(text)}), attempt {incomplete_attempt + 1}"
            )
        raise LLMIncompleteError(
            f"Incomplete Claude response after {1 + MAX_INCOMPLETE_RETRIES} attempts "
            f"(stop_reason={last['stop_reason']}, chars={last['content_chars']}, model={last['response_model']})"
        )
    except Exception as e:
        _finish("error", error_type=type(e).__name__, error=str(e)[:2000])
        raise


def critic_provider() -> str:
    """Critic provider: 'anthropic' (revision default via run_experiment) or 'openai'."""
    return os.environ.get("VIRTUAL_LAB_CRITIC_PROVIDER", "openai")


def call_critic(system_prompt: str, user_message: str, tag: dict | None = None) -> str:
    """Route the Critic call to the configured provider."""
    provider = critic_provider()
    if provider == "anthropic":
        return call_claude(system_prompt, user_message, tag=tag)
    if provider == "openai":
        return call_gpt(system_prompt, user_message, tag=tag)
    raise ValueError(f"Unknown VIRTUAL_LAB_CRITIC_PROVIDER: {provider}")
