from typing import Any, Dict, Optional

from .chat_responder import handle_request, Response


def normalize_request(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize raw channel input into a WESLR request dict.

    Stateless stance: main-door chat has no canonical persistent continuity. Valid context is limited to the
    current request fields and optional explicit chat_context. Hints (if used downstream) are helper-only, not continuity.
    """
    persona = raw.get("persona") or "general user"
    domain = raw.get("domain") or "general"
    previous_decision = raw.get("previous_decision")
    explanation_overrides = raw.get("explanation_overrides") or raw.get("mode")
    request_mode = raw.get("request_mode") or raw.get("mode")

    message = raw.get("message") or ""
    inferred_mode = request_mode
    if not inferred_mode:
        lowered = message.strip().lower()
        status_intents = {
            "status", "status?", "what matters now", "what matters now?",
            "anything important", "anything important?",
            "what should i focus on", "what is blocked", "what changed",
        }
        if lowered in status_intents:
            inferred_mode = "status"
        else:
            inferred_mode = "chat"

    normalized = {
        "message": message,
        "persona": persona,
        "domain": domain,
        "previous_decision": previous_decision,
        "request_mode": inferred_mode,
        "explanation_overrides": explanation_overrides,
        "chat_context": raw.get("chat_context"),  # explicit context only; no implicit continuity
    }
    return normalized


def route_request(raw: Dict[str, Any]) -> Response:
    """Thin ingress adapter: normalize then call handle_request once.

    No alternate logic; no governance changes. Returns Response from core.
    """
    normalized = normalize_request(raw)
    persona = normalized.pop("persona", "general user")
    domain = normalized.pop("domain", "general")
    previous_decision = normalized.pop("previous_decision", None)
    # explanation_overrides stays in normalized for handle_request to consume

    return handle_request(
        normalized,
        persona=persona,
        domain=domain,
        previous_decision=previous_decision,
    )
