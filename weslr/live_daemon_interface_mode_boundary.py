"""Metadata-only live daemon interface and mode boundary helpers v1.

This module builds compact daemon verdict packets from supplied metadata only.
It is pure, deterministic, import-safe, and fail-closed.

It does not run daemon code. It does not wire runtime behavior. It does not
call models/providers, APIs, Home Assistant, or any voice/runtime surface. It
does not read/write `.weslr` or memory. It does not authorize truth, proof,
public claims, tool execution, or behavior-pack promotion.
"""

from __future__ import annotations

import copy
import re
from dataclasses import asdict, dataclass, is_dataclass
from typing import Any, Mapping

HELPER_TYPE_V1 = "live_daemon_interface_mode_boundary_v1"
PACKET_TYPE_V1 = "live_daemon_verdict_packet_v1"
SUMMARY_TYPE_V1 = "live_daemon_verdict_summary_v1"

ALLOWED_SURFACES_V1 = {
    "chat",
    "voice",
    "ambient",
    "proactive",
    "frontier",
    "unknown_surface",
}

ALLOWED_ROUTES_V1 = {
    "render_text",
    "speak_voice",
    "silent_store_none",
    "ask_clarification",
    "block_response",
    "defer_response",
    "operator_review_required",
}

ALLOWED_READINESS_STATUSES_V1 = {
    "ready",
    "ready_with_caveat",
    "not_ready_missing_evidence",
    "not_ready_access_blocked",
    "not_ready_poison_blocked",
    "not_ready_grounding_blocked",
    "not_ready_operator_required",
}

ALLOWED_RISK_STATUSES_V1 = {
    "low",
    "medium",
    "high",
    "blocked",
}

ALLOWED_ACTION_AUTHORITY_STATUSES_V1 = {
    "no_action_authority",
    "proposal_only",
    "owner_required",
    "operator_required",
    "blocked",
}

ALLOWED_GROUNDING_STATUSES_V1 = {
    "grounded",
    "partially_grounded",
    "unsupported",
    "contradicted",
    "stale_support",
    "access_restricted",
    "poison_quarantined",
}

ALLOWED_SOURCE_ACCESS_STATUSES_V1 = {
    "access_allowed",
    "access_restricted",
    "private_source_blocked",
    "public_use_blocked",
}

ALLOWED_POISON_STATUSES_V1 = {
    "clean",
    "poison_risk",
    "poison_blocked",
    "quarantined",
}

ALLOWED_PRIVACY_STATUSES_V1 = {
    "low_sensitivity",
    "medium_sensitivity",
    "high_sensitivity",
    "privacy_blocked",
}

ALLOWED_PUBLIC_CLAIM_STATUSES_V1 = {
    "not_public_claim",
    "public_claim_blocked",
    "public_claim_owner_required",
    "public_claim_not_ready",
}

ALLOWED_MEMORY_TIERS_V1 = {
    "identity_core",
    "operating_facts",
    "session_state",
    "none",
    "unknown_memory_tier",
}

ALLOWED_TRUST_LEVELS_V1 = {
    "conversational",
    "sensitive",
    "elevated",
    "operator_confirmed",
    "blocked",
    "unknown_trust_level",
}

ALLOWED_FIELD_HINTS_V1 = (
    "hidden_prompt",
    "raw_private",
    "private_data",
    "secret",
    "token",
    "key",
    "api_key",
    "credential",
    "password",
)

ALLOWED_CLAIM_PHRASES_V1 = (
    "agi",
    "consciousness",
    "sentience",
    "turing",
    "certification",
    "public readiness",
    "public ready",
    "public-readiness",
    "proof certainty",
    "proof claim",
    "truth certainty",
    "truth claim",
    "proof of truth",
    "public claim approval",
    "model provider",
    "runtime authority",
    "learning claim",
)

DEFAULT_SAFE_METADATA_V1 = {
    "metadata_only": True,
    "internal_only": True,
}

DEFAULT_MEMORY_TIER_V1 = "none"
DEFAULT_TRUST_LEVEL_V1 = "conversational"
DEFAULT_TRUTH_RULE_V1 = "surface_and_permission_only"
DEFAULT_RECOMMENDED_NEXT_GATE_V1 = "route outside the daemon boundary and return a compact verdict only"
DEFAULT_RISK_V1 = "low"
DEFAULT_ROUTE_V1 = "defer_response"
DEFAULT_READINESS_V1 = "not_ready_operator_required"
DEFAULT_GROUNDING_V1 = "unsupported"
DEFAULT_SOURCE_ACCESS_V1 = "access_restricted"
DEFAULT_POISON_V1 = "clean"
DEFAULT_PRIVACY_V1 = "low_sensitivity"
DEFAULT_PUBLIC_CLAIM_V1 = "not_public_claim"


class ValidationError(ValueError):
    pass


# ---------------------------------------------------------------------------
# Safe helpers
# ---------------------------------------------------------------------------


def _safe_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (str, int, float)):
        return str(value).strip()
    return default if value == "" else str(value).strip()


def _normalize_text(value: Any) -> str:
    return " ".join(_safe_text(value).replace("_", " ").split()).lower()


def _safe_bool(value: Any) -> bool:
    return bool(value) is True


def _json_sort_key(value: Any) -> tuple[str, str]:
    return (type(value).__name__, repr(value))


def _json_safe(value: Any) -> Any:
    value = copy.deepcopy(value)
    if is_dataclass(value):
        return _json_safe(asdict(value))
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return {str(key): _json_safe(val) for key, val in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, set):
        items = [_json_safe(item) for item in value]
        return sorted(items, key=_json_sort_key)
    return _safe_text(value)



def to_live_daemon_verdict_json_safe_v1(value: Any) -> Any:
    return _json_safe(value)



def _contains_forbidden_field(value: Any) -> str:
    if value is None:
        return ""
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = _normalize_text(key)
            key_raw = _safe_text(key).lower()
            if any(hint.replace("_", " ") in key_text or hint in key_raw for hint in ALLOWED_FIELD_HINTS_V1):
                return _safe_text(key)
            nested = _contains_forbidden_field(item)
            if nested:
                return nested
        return ""
    if isinstance(value, (list, tuple, set)):
        for item in value:
            nested = _contains_forbidden_field(item)
            if nested:
                return nested
        return ""
    text = _normalize_text(value)
    raw = _safe_text(value).lower()
    if any(hint.replace("_", " ") in text or hint in raw for hint in ALLOWED_FIELD_HINTS_V1):
        return _safe_text(value)
    return ""



def _contains_forbidden_claim_marker(value: Any) -> bool:
    if value is None:
        return False
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, Mapping):
        return any(_contains_forbidden_claim_marker(item) for item in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(_contains_forbidden_claim_marker(item) for item in value)
    text = _normalize_text(value)
    raw = _safe_text(value).lower()
    return any(phrase in text or phrase in raw for phrase in ALLOWED_CLAIM_PHRASES_V1)



def _safe_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, Mapping):
        return list(value.values())
    if isinstance(value, (list, tuple, set)):
        return list(value)
    return [value]



def _dedupe_text_list(values: Any) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for item in _safe_list(values):
        text = _safe_text(item)
        if text and text not in seen:
            out.append(text)
            seen.add(text)
    return out



def _normalize_required_text(value: Any, *, allowed: set[str], field_name: str) -> str:
    text = _safe_text(value)
    if text not in allowed:
        raise ValidationError(f"unknown_{field_name}")
    return text



def _normalize_bool(value: Any, field_name: str) -> bool:
    if isinstance(value, bool):
        return value
    raise ValidationError(f"non_boolean_{field_name}")



def _normalize_metadata(value: Any) -> dict[str, Any]:
    if value is None:
        return dict(DEFAULT_SAFE_METADATA_V1)
    safe = _json_safe(value)
    if not isinstance(safe, Mapping):
        raise ValidationError("safe_metadata_must_be_mapping")
    out = {str(key): _json_safe(val) for key, val in safe.items()}
    out.setdefault("metadata_only", True)
    out.setdefault("internal_only", True)
    return out


# ---------------------------------------------------------------------------
# Packet builder / validators
# ---------------------------------------------------------------------------


def build_live_daemon_verdict_packet_v1(
    *,
    daemon_verdict_packet_id: str,
    request_id: str,
    surface: str,
    memory_tier: str = DEFAULT_MEMORY_TIER_V1,
    trust_level: str = DEFAULT_TRUST_LEVEL_V1,
    memory_tier_context_allowed: bool = False,
    trust_level_required: str = DEFAULT_TRUST_LEVEL_V1,
    current_trust_level: str = DEFAULT_TRUST_LEVEL_V1,
    listen_allowed: bool = False,
    speak_allowed: bool = False,
    render_allowed: bool = False,
    reply_allowed: bool = False,
    interrupt_allowed: bool = False,
    autonomous_speaking_allowed: bool = False,
    route: str = DEFAULT_ROUTE_V1,
    readiness_status: str = DEFAULT_READINESS_V1,
    grounding_status: str = DEFAULT_GROUNDING_V1,
    source_access_status: str = DEFAULT_SOURCE_ACCESS_V1,
    poison_status: str = DEFAULT_POISON_V1,
    privacy_status: str = DEFAULT_PRIVACY_V1,
    action_authority_status: str = "blocked",
    public_claim_status: str = DEFAULT_PUBLIC_CLAIM_V1,
    risk_status: str = DEFAULT_RISK_V1,
    next_gate: str = DEFAULT_RECOMMENDED_NEXT_GATE_V1,
    reason_summary: str = "",
    raw_payload_allowed: bool = False,
    runtime_authority: bool = False,
    writes_state: bool = False,
    model_provider_used: bool = False,
    public_claim_allowed: bool = False,
    proof_claim_allowed: bool = False,
    learning_claimed: bool = False,
    safe_metadata: Any = None,
) -> dict[str, Any]:
    packet = {
        "daemon_verdict_packet_id": _safe_text(daemon_verdict_packet_id),
        "request_id": _safe_text(request_id),
        "surface": _safe_text(surface),
        "memory_tier": _safe_text(memory_tier),
        "trust_level": _safe_text(trust_level),
        "memory_tier_context_allowed": _normalize_bool(memory_tier_context_allowed, "memory_tier_context_allowed"),
        "trust_level_required": _safe_text(trust_level_required),
        "current_trust_level": _safe_text(current_trust_level),
        "listen_allowed": _normalize_bool(listen_allowed, "listen_allowed"),
        "speak_allowed": _normalize_bool(speak_allowed, "speak_allowed"),
        "render_allowed": _normalize_bool(render_allowed, "render_allowed"),
        "reply_allowed": _normalize_bool(reply_allowed, "reply_allowed"),
        "interrupt_allowed": _normalize_bool(interrupt_allowed, "interrupt_allowed"),
        "autonomous_speaking_allowed": _normalize_bool(autonomous_speaking_allowed, "autonomous_speaking_allowed"),
        "route": _safe_text(route),
        "readiness_status": _safe_text(readiness_status),
        "grounding_status": _safe_text(grounding_status),
        "source_access_status": _safe_text(source_access_status),
        "poison_status": _safe_text(poison_status),
        "privacy_status": _safe_text(privacy_status),
        "action_authority_status": _safe_text(action_authority_status),
        "public_claim_status": _safe_text(public_claim_status),
        "risk_status": _safe_text(risk_status),
        "next_gate": _safe_text(next_gate),
        "reason_summary": _safe_text(reason_summary),
        "raw_payload_allowed": _normalize_bool(raw_payload_allowed, "raw_payload_allowed"),
        "runtime_authority": _normalize_bool(runtime_authority, "runtime_authority"),
        "writes_state": _normalize_bool(writes_state, "writes_state"),
        "model_provider_used": _normalize_bool(model_provider_used, "model_provider_used"),
        "public_claim_allowed": _normalize_bool(public_claim_allowed, "public_claim_allowed"),
        "proof_claim_allowed": _normalize_bool(proof_claim_allowed, "proof_claim_allowed"),
        "learning_claimed": _normalize_bool(learning_claimed, "learning_claimed"),
        "safe_metadata": _normalize_metadata(safe_metadata),
    }
    validate_live_daemon_verdict_packet_v1(packet)
    return packet



def validate_live_daemon_verdict_packet_v1(packet: Any) -> bool:
    packet = to_live_daemon_verdict_json_safe_v1(packet)
    if not isinstance(packet, Mapping):
        raise ValidationError("packet_must_be_mapping")

    forbidden_field = _contains_forbidden_field(packet)
    if forbidden_field:
        raise ValidationError("hidden_prompt_or_raw_private_field")

    if _contains_forbidden_claim_marker(packet):
        raise ValidationError("claim_marker_blocked")

    if _safe_text(packet.get("surface")) not in ALLOWED_SURFACES_V1:
        raise ValidationError("unknown_surface")
    if _safe_text(packet.get("route")) not in ALLOWED_ROUTES_V1:
        raise ValidationError("unknown_route")
    if _safe_text(packet.get("readiness_status")) not in ALLOWED_READINESS_STATUSES_V1:
        raise ValidationError("unknown_readiness_status")
    if _safe_text(packet.get("risk_status")) not in ALLOWED_RISK_STATUSES_V1:
        raise ValidationError("unknown_risk_status")
    if _safe_text(packet.get("action_authority_status")) not in ALLOWED_ACTION_AUTHORITY_STATUSES_V1:
        raise ValidationError("unknown_action_authority_status")
    if _safe_text(packet.get("grounding_status")) not in ALLOWED_GROUNDING_STATUSES_V1:
        raise ValidationError("unknown_grounding_status")
    if _safe_text(packet.get("source_access_status")) not in ALLOWED_SOURCE_ACCESS_STATUSES_V1:
        raise ValidationError("unknown_source_access_status")
    if _safe_text(packet.get("poison_status")) not in ALLOWED_POISON_STATUSES_V1:
        raise ValidationError("unknown_poison_status")
    if _safe_text(packet.get("privacy_status")) not in ALLOWED_PRIVACY_STATUSES_V1:
        raise ValidationError("unknown_privacy_status")
    if _safe_text(packet.get("public_claim_status")) not in ALLOWED_PUBLIC_CLAIM_STATUSES_V1:
        raise ValidationError("unknown_public_claim_status")

    if _safe_text(packet.get("memory_tier")) not in ALLOWED_MEMORY_TIERS_V1:
        raise ValidationError("unknown_memory_tier")
    if _safe_text(packet.get("trust_level")) not in ALLOWED_TRUST_LEVELS_V1:
        raise ValidationError("unknown_trust_level")
    if _safe_text(packet.get("trust_level_required")) not in ALLOWED_TRUST_LEVELS_V1:
        raise ValidationError("unknown_trust_level_required")
    if _safe_text(packet.get("current_trust_level")) not in ALLOWED_TRUST_LEVELS_V1:
        raise ValidationError("unknown_current_trust_level")

    if _safe_bool(packet.get("raw_payload_allowed")):
        raise ValidationError("raw_payload_allowed_true")
    if _safe_bool(packet.get("runtime_authority")):
        raise ValidationError("runtime_authority_true")
    if _safe_bool(packet.get("writes_state")):
        raise ValidationError("writes_state_true")
    if _safe_bool(packet.get("model_provider_used")):
        raise ValidationError("model_provider_used_true")
    if _safe_bool(packet.get("public_claim_allowed")):
        raise ValidationError("public_claim_allowed_true")
    if _safe_bool(packet.get("proof_claim_allowed")):
        raise ValidationError("proof_claim_allowed_true")
    if _safe_bool(packet.get("learning_claimed")):
        raise ValidationError("learning_claimed_true")

    if _safe_text(packet.get("memory_tier")) in ALLOWED_TRUST_LEVELS_V1:
        raise ValidationError("memory_tier_confused_with_trust_level")
    if _safe_text(packet.get("trust_level")) in ALLOWED_MEMORY_TIERS_V1:
        raise ValidationError("trust_level_confused_with_memory_tier")
    if _safe_text(packet.get("trust_level_required")) in ALLOWED_MEMORY_TIERS_V1:
        raise ValidationError("trust_level_required_confused_with_memory_tier")
    if _safe_text(packet.get("current_trust_level")) in ALLOWED_MEMORY_TIERS_V1:
        raise ValidationError("current_trust_level_confused_with_memory_tier")

    return True



def summarize_live_daemon_verdict_packet_v1(packet: Any) -> dict[str, Any]:
    packet = to_live_daemon_verdict_json_safe_v1(packet)
    validate_live_daemon_verdict_packet_v1(packet)
    return {
        "summary_type": SUMMARY_TYPE_V1,
        "daemon_verdict_packet_id": packet.get("daemon_verdict_packet_id"),
        "surface": packet.get("surface"),
        "route": packet.get("route"),
        "readiness_status": packet.get("readiness_status"),
        "grounding_status": packet.get("grounding_status"),
        "source_access_status": packet.get("source_access_status"),
        "poison_status": packet.get("poison_status"),
        "privacy_status": packet.get("privacy_status"),
        "action_authority_status": packet.get("action_authority_status"),
        "public_claim_status": packet.get("public_claim_status"),
        "risk_status": packet.get("risk_status"),
        "memory_tier": packet.get("memory_tier"),
        "trust_level": packet.get("trust_level"),
        "listen_allowed": bool(packet.get("listen_allowed")),
        "speak_allowed": bool(packet.get("speak_allowed")),
        "render_allowed": bool(packet.get("render_allowed")),
        "reply_allowed": bool(packet.get("reply_allowed")),
        "interrupt_allowed": bool(packet.get("interrupt_allowed")),
        "autonomous_speaking_allowed": bool(packet.get("autonomous_speaking_allowed")),
        "raw_payload_allowed": bool(packet.get("raw_payload_allowed")),
        "runtime_authority": bool(packet.get("runtime_authority")),
        "writes_state": bool(packet.get("writes_state")),
        "model_provider_used": bool(packet.get("model_provider_used")),
        "public_claim_allowed": bool(packet.get("public_claim_allowed")),
        "proof_claim_allowed": bool(packet.get("proof_claim_allowed")),
        "learning_claimed": bool(packet.get("learning_claimed")),
        "safe_metadata": packet.get("safe_metadata", {}),
    }


# ---------------------------------------------------------------------------
# Initial examples
# ---------------------------------------------------------------------------


def _base_example(
    *,
    daemon_verdict_packet_id: str,
    request_id: str,
    surface: str,
    memory_tier: str,
    trust_level: str,
    memory_tier_context_allowed: bool,
    trust_level_required: str,
    current_trust_level: str,
    listen_allowed: bool,
    speak_allowed: bool,
    render_allowed: bool,
    reply_allowed: bool,
    interrupt_allowed: bool,
    autonomous_speaking_allowed: bool,
    route: str,
    readiness_status: str,
    grounding_status: str,
    source_access_status: str,
    poison_status: str,
    privacy_status: str,
    action_authority_status: str,
    public_claim_status: str,
    risk_status: str,
    next_gate: str,
    reason_summary: str,
) -> dict[str, Any]:
    return build_live_daemon_verdict_packet_v1(
        daemon_verdict_packet_id=daemon_verdict_packet_id,
        request_id=request_id,
        surface=surface,
        memory_tier=memory_tier,
        trust_level=trust_level,
        memory_tier_context_allowed=memory_tier_context_allowed,
        trust_level_required=trust_level_required,
        current_trust_level=current_trust_level,
        listen_allowed=listen_allowed,
        speak_allowed=speak_allowed,
        render_allowed=render_allowed,
        reply_allowed=reply_allowed,
        interrupt_allowed=interrupt_allowed,
        autonomous_speaking_allowed=autonomous_speaking_allowed,
        route=route,
        readiness_status=readiness_status,
        grounding_status=grounding_status,
        source_access_status=source_access_status,
        poison_status=poison_status,
        privacy_status=privacy_status,
        action_authority_status=action_authority_status,
        public_claim_status=public_claim_status,
        risk_status=risk_status,
        next_gate=next_gate,
        reason_summary=reason_summary,
        safe_metadata={"example_name": daemon_verdict_packet_id, **DEFAULT_SAFE_METADATA_V1},
    )



def build_initial_live_daemon_interface_examples_v1() -> list[dict[str, Any]]:
    return [
        _base_example(
            daemon_verdict_packet_id="chat_render_ready_grounded",
            request_id="req_chat_render_ready_grounded",
            surface="chat",
            memory_tier="identity_core",
            trust_level="conversational",
            memory_tier_context_allowed=True,
            trust_level_required="conversational",
            current_trust_level="conversational",
            listen_allowed=False,
            speak_allowed=False,
            render_allowed=True,
            reply_allowed=True,
            interrupt_allowed=False,
            autonomous_speaking_allowed=False,
            route="render_text",
            readiness_status="ready",
            grounding_status="grounded",
            source_access_status="access_allowed",
            poison_status="clean",
            privacy_status="low_sensitivity",
            action_authority_status="no_action_authority",
            public_claim_status="not_public_claim",
            risk_status="low",
            next_gate="render text in chat surface",
            reason_summary="Grounded chat response may render as text only.",
        ),
        _base_example(
            daemon_verdict_packet_id="voice_speak_ready_with_caveat",
            request_id="req_voice_speak_ready_with_caveat",
            surface="voice",
            memory_tier="operating_facts",
            trust_level="sensitive",
            memory_tier_context_allowed=True,
            trust_level_required="sensitive",
            current_trust_level="sensitive",
            listen_allowed=True,
            speak_allowed=True,
            render_allowed=True,
            reply_allowed=True,
            interrupt_allowed=False,
            autonomous_speaking_allowed=False,
            route="speak_voice",
            readiness_status="ready_with_caveat",
            grounding_status="partially_grounded",
            source_access_status="access_allowed",
            poison_status="clean",
            privacy_status="medium_sensitivity",
            action_authority_status="no_action_authority",
            public_claim_status="not_public_claim",
            risk_status="medium",
            next_gate="speak with caveat and keep text fallback available",
            reason_summary="Voice may speak, but only with a grounded caveat.",
        ),
        _base_example(
            daemon_verdict_packet_id="voice_blocked_unsupported_claim",
            request_id="req_voice_blocked_unsupported_claim",
            surface="voice",
            memory_tier="session_state",
            trust_level="sensitive",
            memory_tier_context_allowed=True,
            trust_level_required="sensitive",
            current_trust_level="sensitive",
            listen_allowed=True,
            speak_allowed=False,
            render_allowed=True,
            reply_allowed=True,
            interrupt_allowed=False,
            autonomous_speaking_allowed=False,
            route="render_text",
            readiness_status="not_ready_grounding_blocked",
            grounding_status="unsupported",
            source_access_status="access_allowed",
            poison_status="clean",
            privacy_status="medium_sensitivity",
            action_authority_status="no_action_authority",
            public_claim_status="public_claim_not_ready",
            risk_status="high",
            next_gate="render text only; do not speak unsupported claim",
            reason_summary="Unsupported claim must not be spoken as confident voice output.",
        ),
        _base_example(
            daemon_verdict_packet_id="ambient_defer_missing_evidence",
            request_id="req_ambient_defer_missing_evidence",
            surface="ambient",
            memory_tier="session_state",
            trust_level="sensitive",
            memory_tier_context_allowed=True,
            trust_level_required="sensitive",
            current_trust_level="sensitive",
            listen_allowed=True,
            speak_allowed=False,
            render_allowed=False,
            reply_allowed=False,
            interrupt_allowed=False,
            autonomous_speaking_allowed=False,
            route="defer_response",
            readiness_status="not_ready_missing_evidence",
            grounding_status="unsupported",
            source_access_status="access_allowed",
            poison_status="clean",
            privacy_status="medium_sensitivity",
            action_authority_status="no_action_authority",
            public_claim_status="not_public_claim",
            risk_status="medium",
            next_gate="defer until evidence becomes available",
            reason_summary="Ambient surface should wait when evidence is missing.",
        ),
        _base_example(
            daemon_verdict_packet_id="proactive_operator_review_required",
            request_id="req_proactive_operator_review_required",
            surface="proactive",
            memory_tier="operating_facts",
            trust_level="operator_confirmed",
            memory_tier_context_allowed=True,
            trust_level_required="operator_confirmed",
            current_trust_level="operator_confirmed",
            listen_allowed=False,
            speak_allowed=False,
            render_allowed=False,
            reply_allowed=False,
            interrupt_allowed=False,
            autonomous_speaking_allowed=False,
            route="operator_review_required",
            readiness_status="not_ready_operator_required",
            grounding_status="partially_grounded",
            source_access_status="access_allowed",
            poison_status="clean",
            privacy_status="high_sensitivity",
            action_authority_status="operator_required",
            public_claim_status="public_claim_owner_required",
            risk_status="high",
            next_gate="operator review required before any proactive output",
            reason_summary="Proactive output needs operator review at elevated sensitivity.",
        ),
        _base_example(
            daemon_verdict_packet_id="frontier_silent_store_none",
            request_id="req_frontier_silent_store_none",
            surface="frontier",
            memory_tier="none",
            trust_level="blocked",
            memory_tier_context_allowed=False,
            trust_level_required="blocked",
            current_trust_level="blocked",
            listen_allowed=False,
            speak_allowed=False,
            render_allowed=False,
            reply_allowed=False,
            interrupt_allowed=False,
            autonomous_speaking_allowed=False,
            route="silent_store_none",
            readiness_status="not_ready_operator_required",
            grounding_status="stale_support",
            source_access_status="public_use_blocked",
            poison_status="clean",
            privacy_status="high_sensitivity",
            action_authority_status="blocked",
            public_claim_status="public_claim_blocked",
            risk_status="blocked",
            next_gate="store no output and keep frontier silent",
            reason_summary="Frontier surface produces no outward response.",
        ),
        _base_example(
            daemon_verdict_packet_id="rag_access_blocked_verdict",
            request_id="req_rag_access_blocked_verdict",
            surface="chat",
            memory_tier="identity_core",
            trust_level="blocked",
            memory_tier_context_allowed=False,
            trust_level_required="blocked",
            current_trust_level="blocked",
            listen_allowed=False,
            speak_allowed=False,
            render_allowed=False,
            reply_allowed=False,
            interrupt_allowed=False,
            autonomous_speaking_allowed=False,
            route="block_response",
            readiness_status="not_ready_access_blocked",
            grounding_status="access_restricted",
            source_access_status="access_restricted",
            poison_status="clean",
            privacy_status="high_sensitivity",
            action_authority_status="blocked",
            public_claim_status="public_claim_blocked",
            risk_status="high",
            next_gate="compact verdict only; no raw retrieved evidence",
            reason_summary="Access restriction blocks retrieval-driven response surface.",
        ),
        _base_example(
            daemon_verdict_packet_id="poison_blocked_verdict",
            request_id="req_poison_blocked_verdict",
            surface="chat",
            memory_tier="identity_core",
            trust_level="blocked",
            memory_tier_context_allowed=False,
            trust_level_required="blocked",
            current_trust_level="blocked",
            listen_allowed=False,
            speak_allowed=False,
            render_allowed=False,
            reply_allowed=False,
            interrupt_allowed=False,
            autonomous_speaking_allowed=False,
            route="block_response",
            readiness_status="not_ready_poison_blocked",
            grounding_status="poison_quarantined",
            source_access_status="access_allowed",
            poison_status="poison_blocked",
            privacy_status="high_sensitivity",
            action_authority_status="blocked",
            public_claim_status="public_claim_blocked",
            risk_status="blocked",
            next_gate="block response and keep poison quarantined",
            reason_summary="Poisoned or quarantined content must not cross the boundary.",
        ),
        _base_example(
            daemon_verdict_packet_id="naie_contradiction_render_with_caveat",
            request_id="req_naie_contradiction_render_with_caveat",
            surface="chat",
            memory_tier="operating_facts",
            trust_level="sensitive",
            memory_tier_context_allowed=True,
            trust_level_required="sensitive",
            current_trust_level="sensitive",
            listen_allowed=False,
            speak_allowed=False,
            render_allowed=True,
            reply_allowed=True,
            interrupt_allowed=False,
            autonomous_speaking_allowed=False,
            route="render_text",
            readiness_status="ready_with_caveat",
            grounding_status="contradicted",
            source_access_status="access_allowed",
            poison_status="clean",
            privacy_status="medium_sensitivity",
            action_authority_status="no_action_authority",
            public_claim_status="not_public_claim",
            risk_status="medium",
            next_gate="render text with contradiction caveat",
            reason_summary="Contradicted content may render only as a caveated text verdict.",
        ),
        _base_example(
            daemon_verdict_packet_id="autonomous_speaking_blocked_high_risk",
            request_id="req_autonomous_speaking_blocked_high_risk",
            surface="ambient",
            memory_tier="session_state",
            trust_level="operator_confirmed",
            memory_tier_context_allowed=True,
            trust_level_required="operator_confirmed",
            current_trust_level="sensitive",
            listen_allowed=True,
            speak_allowed=False,
            render_allowed=False,
            reply_allowed=False,
            interrupt_allowed=False,
            autonomous_speaking_allowed=False,
            route="defer_response",
            readiness_status="not_ready_operator_required",
            grounding_status="partially_grounded",
            source_access_status="access_allowed",
            poison_status="clean",
            privacy_status="high_sensitivity",
            action_authority_status="operator_required",
            public_claim_status="public_claim_not_ready",
            risk_status="high",
            next_gate="block autonomous speaking until operator confirmation",
            reason_summary="High risk blocks autonomous speaking even if a reply might later be allowed.",
        ),
    ]

"""
The module intentionally exposes a compact, metadata-only boundary. It is not a
runtime router, not a truth engine, and not a claim authority surface.
"""
