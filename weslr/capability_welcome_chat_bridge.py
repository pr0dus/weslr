"""WESLR Capability Welcome Chat Bridge V1 — Staging-Only Bridge

Wires Capability Welcome Surface V1 into the staging demo server's /chat path.
Guarded: only activates for specific help/welcome/capability overview queries.
No execution, no evidence search, no writes.

Authority: registry_generated / automatic_change: false
Only for staging validation — not production OCW deployment.
"""

from __future__ import annotations

from typing import Any, Dict, Optional


# ─── Query classifier ────────────────────────────────────────────────────────

_WELCOME_TRIGGERS = frozenset([
    "what can you do",
    "what can you help me with",
    "what should i try",
    "help",
    "welcome",
    "besides these",
    "what else can you do",
    "capabilities",
])


def _normalize_query(text: str) -> str:
    """Normalize message for trigger matching: lowercase, strip punct."""
    import re
    text = text.lower().strip()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def is_capability_welcome_query(message: str) -> bool:
    """Return True if message is a pure help/welcome/capability overview query.

    Guards against:
    - Identity questions (what is weslr, who are you)
    - Evidence questions (what is entropy, explain entropy)
    - Governance questions (what is unsafe to automate)
    - Source questions (what are the sources)
    - Slash commands for other capabilities (/evidence, /system, /governance, etc.)
    """
    if not message:
        return False

    normalized = _normalize_query(message)

    # Must match a welcome trigger
    if not any(t in normalized for t in _WELCOME_TRIGGERS):
        return False

    # Negative guards — these should NOT be treated as capability welcome queries
    _NEGATIVE_GUARDS = [
        "what is weslr",
        "who are you",
        "what are you",
        "tell me about yourself",
        "what is entropy",
        "explain entropy",
        "what is unsafe to automate",
        "what requires operator approval",
        "governance boundary",
        "what are the sources",
        "show sources",
        "where did that come from",
        "cite your sources",
    ]

    for guard in _NEGATIVE_GUARDS:
        if guard in normalized:
            return False

    # Slash commands other than /help should return False
    if normalized.startswith("/"):
        # Allow /help only
        if normalized.lstrip("/") not in ("help", "capabilities"):
            return False

    return True


# ─── Bridge function ─────────────────────────────────────────────────────────

def maybe_answer_with_capability_welcome(
    message: str,
    current_response: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    """Return a capability-welcome reply if message is a capability welcome query.

    Args:
        message: The user message
        current_response: The current response dict from weslr_chat (unused in V1,
            kept for interface parity)

    Returns:
        dict with path=capability_welcome, reply, response_contract,
        _capability_metadata, or None if not a welcome query.
    """
    if not is_capability_welcome_query(message):
        return None

    try:
        from weslr.capability_welcome_surface import build_welcome_overview
        overview = build_welcome_overview()
    except Exception:
        # Fallback if registry loading fails — safe static message
        return _safe_fallback_welcome()

    return {
        "path": "capability_welcome",
        "response_contract": "guided_help",
        "reply": overview.get("message", _FALLBACK_MESSAGE),
        "_capability_metadata": {
            "capability_used": True,
            "authority": "registry_generated",
            "automatic_change": False,
            "source": "capability_registry",
        },
    }


_FALLBACK_MESSAGE = (
    "Here are the main ways I can help:\n\n"
    "**Search and Evidence**\n"
    "  • Look up topics with source citations\n\n"
    "**Planning and Projects**\n"
    "  • Break down goals into next steps\n\n"
    "**Experiments and Learning**\n"
    "  • Plan structured experiments together\n\n"
    "**WESLR System State**\n"
    "  • Check what is implemented and what needs attention\n\n"
    "Try asking me something specific, or say /help for an overview."
)


def _safe_fallback_welcome() -> Dict[str, Any]:
    """Return safe fallback welcome when registry is unavailable."""
    return {
        "path": "capability_welcome",
        "response_contract": "guided_help",
        "reply": _FALLBACK_MESSAGE,
        "_capability_metadata": {
            "capability_used": True,
            "authority": "registry_generated",
            "automatic_change": False,
            "source": "fallback",
        },
    }