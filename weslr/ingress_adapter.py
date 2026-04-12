from typing import Any, Dict, Optional

from .chat_responder import handle_request, Response


def normalize_request(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize raw channel input into a WESLR request dict.

    Minimal mapping: persona/domain defaults, previous_decision passthrough, explanation overrides/mode if provided.
    Does not alter governance or signals.
    """
    persona = raw.get("persona") or "general user"
    domain = raw.get("domain") or "general"
    previous_decision = raw.get("previous_decision")
    explanation_overrides = raw.get("explanation_overrides") or raw.get("mode")
    request_mode = raw.get("request_mode") or raw.get("mode")

    normalized = {
        "message": raw.get("message"),
        "persona": persona,
        "domain": domain,
        "previous_decision": previous_decision,
        "request_mode": request_mode,
        "explanation_overrides": explanation_overrides,
        "chat_context": raw.get("chat_context"),
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
