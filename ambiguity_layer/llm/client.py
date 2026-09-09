"""OpenAI-compatible LLM client (LLM7 / OpenAI / etc.) with 429 retry."""

from __future__ import annotations

import json
import re
import time
from typing import Any

from openai import OpenAI, RateLimitError

from ambiguity_layer import config

_client: OpenAI | None = None


def get_client() -> OpenAI:
    global _client
    if _client is None:
        if not config.OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY is not set. Configure .env first.")
        _client = OpenAI(
            api_key=config.OPENAI_API_KEY,
            base_url=config.OPENAI_BASE_URL or None,
        )
    return _client


def _retry_after_seconds(exc: Exception, default: float = 60.0) -> float:
    """Parse retry_after from RateLimitError body / headers."""
    # openai.RateLimitError often has body dict or message text
    retry = None
    body = getattr(exc, "body", None)
    if isinstance(body, dict):
        err = body.get("error") if isinstance(body.get("error"), dict) else body
        retry = err.get("retry_after") or err.get("retryAfter")
    if retry is None:
        m = re.search(r"retry[_ ]after[\"'=\s:]+(\d+)", str(exc), re.I)
        if m:
            retry = int(m.group(1))
    try:
        return max(5.0, float(retry)) if retry is not None else default
    except (TypeError, ValueError):
        return default


def _create_with_retry(**kwargs):
    """Call chat.completions.create; sleep and retry on 429."""
    client = get_client()
    max_retries = int(getattr(config, "LLM_MAX_RETRIES", 3))
    last_exc: Exception | None = None

    for attempt in range(max_retries + 1):
        try:
            return client.chat.completions.create(**kwargs)
        except RateLimitError as exc:
            last_exc = exc
            wait = _retry_after_seconds(exc)
            if attempt >= max_retries:
                break
            mins = wait / 60.0
            print(
                f"\n[rate limit] Waiting {wait:.0f}s (~{mins:.1f} min) "
                f"before retry {attempt + 1}/{max_retries}...",
                flush=True,
            )
            time.sleep(wait + 2)
        except Exception:
            raise

    assert last_exc is not None
    raise last_exc


def chat_json(
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.0,
    model: str | None = None,
) -> dict[str, Any]:
    """Chat completion forced to JSON object; returns parsed dict."""
    resp = _create_with_retry(
        model=model or config.OPENAI_MODEL,
        messages=messages,
        temperature=temperature,
        response_format={"type": "json_object"},
    )
    content = (resp.choices[0].message.content or "").strip()
    if not content:
        raise ValueError("Empty LLM response.")
    return json.loads(_extract_json(content))


def chat_text(
    messages: list[dict[str, str]],
    *,
    temperature: float = 0.2,
    model: str | None = None,
) -> str:
    resp = _create_with_retry(
        model=model or config.OPENAI_MODEL,
        messages=messages,
        temperature=temperature,
    )
    content = (resp.choices[0].message.content or "").strip()
    if not content:
        raise ValueError("Empty LLM response.")
    return content


def _extract_json(text: str) -> str:
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", text, re.I)
    if fence:
        text = fence.group(1).strip()
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("No JSON object in model response.")
    return text[start : end + 1]
