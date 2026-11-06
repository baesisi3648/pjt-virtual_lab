"""Secret redaction for logs and metadata (revision C5).

Removes API keys from any text written to calls.jsonl or meta.json: the exact
values of the configured keys, and anything shaped like an OpenAI, Anthropic,
Tavily or Pinecone key (for example a key echoed back in an HTTP error body).
"""
from __future__ import annotations

import os
import re

SECRET_ENV_VARS = ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "TAVILY_API_KEY", "PINECONE_API_KEY",
                   "LANGSMITH_API_KEY")
# Key-shaped tokens only: a known prefix not preceded by a letter or digit (so words
# such as "risk-assessment" are untouched) and a long secret body.
_KEY_PATTERN = re.compile(r"(?<![A-Za-z0-9])(?:sk-ant-|sk-|tvly-|pcsk_|lsv2_)[A-Za-z0-9_\-]{20,}")
REDACTED = "[REDACTED]"


def redact(text: str) -> str:
    if not text:
        return text
    for var in SECRET_ENV_VARS:
        value = os.environ.get(var)
        if value and len(value) >= 8:
            text = text.replace(value, REDACTED)
    return _KEY_PATTERN.sub(REDACTED, text)
