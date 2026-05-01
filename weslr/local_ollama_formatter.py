"""
WESLR Local Ollama Formatter Adapter V1

A disabled-by-default formatter helper that uses local Ollama (qwen2.5:3b)
to rewrite deterministic WESLR responses into more natural wording.

Rules:
- Formatter ONLY — never decides truth, policy, or state
- Must preserve all safety boundaries
- Must preserve uncertainty markers
- Must preserve operator boundaries
- Fallback ALWAYS returns original deterministic text
- No JSONL writes, no state changes
"""

from __future__ import annotations

import os
import time
from typing import Any

import urllib.request
import urllib.error
import socket
import json


# Default Ollama endpoint — local only, no cloud
OLLAMA_API_URL = "http://localhost:11434/api/generate"
OLLAMA_MODEL = "qwen2.5:3b"
DEFAULT_TIMEOUT_SECONDS = 5

# Formatter rules template
FORMATTER_PROMPT_USER = """You are a formatting layer only. Rewrite the following WESLR response to sound natural and friendly. Do not add facts. Do not remove safety meaning. Do not mention internal architecture. Do not claim autonomy, feelings, goals, or values. Output only the rewritten user-facing reply.

Input:
{input_text}"""

FORMATTER_PROMPT_OPERATOR = """You are a formatting layer only. Rewrite the following WESLR operator message to be concise and clear. Do not imply automatic approval. Do not imply urgency. Do not suggest any system change. Output only the rewritten operator-facing message.

Input:
{input_text}"""

# Forbidden phrases that indicate the model is overstepping its role
FORBIDDEN_PHRASES_USER = [
    "I want",
    "I feel",
    "my values",
    "I decided",
    "I changed",
    "approved",
    "automatic change",
    "I learned",
    "as an AI language model",
]

FORBIDDEN_PHRASES_OPERATOR = [
    "I want",
    "I feel",
    "my values",
    "I decided",
    "I changed",
    "approved",
    "automatic change",
    "I learned",
    "as an AI language model",
    "operator review required",  # must not add bold headings or new emphasis
]

# Uncertainty markers that must be preserved
UNCERTAINTY_MARKERS = [
    "not confirmed",
    "not sure",
    "yet to",
    "pending",
    "looking into",
    "look into",
    "show you what I find",
    "structured system knowledge",
]


def is_formatter_enabled(config: dict[str, Any] | None = None) -> bool:
    """Check if formatter is enabled via environment variable.

    Default: False
    Enabled: WESLR_LOCAL_FORMATTER_ENABLED=true
    """
    if config is None:
        config = {}

    env_value = os.environ.get("WESLR_LOCAL_FORMATTER_ENABLED", "").strip().lower()
    if env_value == "true":
        return True

    # Config override (for testing)
    if config.get("enabled", False) is True:
        return True

    return False


def build_formatter_prompt(text: str, mode: str = "user") -> str:
    """Build a strict formatter-only prompt with rules.

    Modes:
    - user: friendly, natural rewrite
    - operator: concise, clear, no urgency/automatic approval
    """
    if mode == "user":
        return FORMATTER_PROMPT_USER.format(input_text=text)
    elif mode == "operator":
        return FORMATTER_PROMPT_OPERATOR.format(input_text=text)
    else:
        raise ValueError(f"Unknown mode: {mode}")


def call_ollama_formatter(
    text: str,
    model: str = OLLAMA_MODEL,
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    mode: str = "user",
) -> dict[str, Any]:
    """Call Ollama API and return formatted text or fallback.

    Returns:
        {
            "ok": bool,
            "formatted_text": str,
            "fallback_text": original_text,
            "model": model,
            "reason": "formatted|disabled|timeout|error|validation_failed"
        }
    """
    if not is_formatter_enabled():
        return {
            "ok": False,
            "formatted_text": "",
            "fallback_text": text,
            "model": model,
            "reason": "disabled",
        }

    prompt = build_formatter_prompt(text, mode)

    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
    }

    try:
        req = urllib.request.Request(
            OLLAMA_API_URL,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
            },
            method="POST",
        )

        start = time.time()
        with urllib.request.urlopen(req, timeout=timeout_seconds) as response:
            elapsed = time.time() - start
            result = json.loads(response.read().decode("utf-8"))

        formatted = result.get("response", "").strip()

        # Validate output
        validation = validate_formatted_output(text, formatted, mode)

        if validation["valid"]:
            return {
                "ok": True,
                "formatted_text": formatted,
                "fallback_text": text,
                "model": model,
                "reason": "formatted",
                "latency_seconds": elapsed,
            }
        else:
            return {
                "ok": False,
                "formatted_text": "",
                "fallback_text": text,
                "model": model,
                "reason": "validation_failed",
                "validation_error": validation.get("error", "unknown"),
            }

    except socket.timeout:
        return {
            "ok": False,
            "formatted_text": "",
            "fallback_text": text,
            "model": model,
            "reason": "timeout",
        }
    except Exception as e:
        return {
            "ok": False,
            "formatted_text": "",
            "fallback_text": text,
            "model": model,
            "reason": "error",
            "error_message": str(e),
        }


def validate_formatted_output(
    original: str,
    formatted: str,
    mode: str = "user",
) -> dict[str, Any]:
    """Validate formatted output against rules.

    Returns:
        {
            "valid": bool,
            "error": str (if invalid)
        }
    """
    # Empty output
    if not formatted or not formatted.strip():
        return {"valid": False, "error": "empty output"}

    # Length check: formatted must not exceed 1.5x original + 120 chars
    max_length = len(original) * 1.5 + 120
    if len(formatted) > max_length:
        return {"valid": False, "error": "output too long"}

    # Forbidden phrases
    forbidden = FORBIDDEN_PHRASES_USER if mode == "user" else FORBIDDEN_PHRASES_OPERATOR
    for phrase in forbidden:
        if phrase.lower() in formatted.lower():
            return {"valid": False, "error": f"forbidden phrase: {phrase}"}

    # Uncertainty markers must be preserved (for uncertainty mode)
    # Check if original has uncertainty markers
    has_uncertainty = any(
        marker in original.lower() for marker in UNCERTAINTY_MARKERS
    )
    if has_uncertainty and mode == "user":
        # Ensure uncertainty is still present
        if not any(marker in formatted.lower() for marker in UNCERTAINTY_MARKERS):
            return {"valid": False, "error": "uncertainty marker removed"}

    # Operator boundary: must not add bold headings or new emphasis
    if mode == "operator":
        if formatted.startswith("**") or formatted.endswith("**"):
            return {"valid": False, "error": "bold formatting added"}

    return {"valid": True}


def format_with_ollama(
    text: str,
    mode: str = "user",
    use_formatter: bool | None = None,
) -> str:
    """Primary API: format text using Ollama if enabled, else return original.

    This is the safe wrapper used by external callers.
    Always returns a deterministic result — never changes runtime behavior.

    Args:
        text: The deterministic response to format
        mode: "user" or "operator"
        use_formatter: Override config check (None = use config)

    Returns:
        Formatted text if successful, otherwise original deterministic text
    """
    # Check if formatter is enabled
    if use_formatter is None:
        use_formatter = is_formatter_enabled()

    if not use_formatter:
        return text

    # Call formatter
    result = call_ollama_formatter(text, mode=mode)

    # Return formatted or fallback
    if result["ok"] and result["reason"] == "formatted":
        return result["formatted_text"]

    # Fallback — always return original deterministic text
    return text
