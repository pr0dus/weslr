from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Mapping

from weslr.no_model_bounded_renderer import (
    render_no_model_bounded_answer_v1,
    to_no_model_bounded_render_json_safe_v1,
    validate_no_model_bounded_render_packet_v1,
)

ADAPTER_TYPE_V1 = "protected_no_model_owner_only_v1"

_WORD_RE = re.compile(r"[a-z0-9]+(?:'[a-z0-9]+)?")


def _safe_text(value: Any) -> str:
    if value is None:
        return ""
    return " ".join(str(value).split())


def _contains_any(blob: str, phrases: tuple[str, ...]) -> bool:
    return any(phrase in blob for phrase in phrases)


def _signature(message: str) -> str:
    return hashlib.sha256(message.encode("utf-8")).hexdigest()[:16]


def normalize_owner_chat_message_v1(message: str) -> dict[str, Any]:
    text = _safe_text(message)
    blob = text.lower()
    words = list(dict.fromkeys(_WORD_RE.findall(blob)))
    labels: list[str] = []

    if not text:
        labels.append("missing_context")
    if _contains_any(blob, ("who are you", "what are you", "identity", "status")):
        labels.extend(["identity", "status"])
    if _contains_any(blob, ("memory", "remember", "recall", "do you remember")):
        labels.extend(["memory", "remember"])
    if _contains_any(blob, ("continuity", "follow up", "what were we doing", "previous point", "carry on")):
        labels.extend(["continuity", "follow up"])
    if _contains_any(blob, ("uncertain", "not sure", "maybe", "unsure", "i think")):
        labels.append("uncertain")
    if _contains_any(blob, ("unsafe", "privacy", "not allowed", "blocked", "refuse", "boundary")):
        labels.append("unsafe")
    if _contains_any(blob, ("need evidence", "evidence", "source", "proof", "current", "latest")):
        labels.append("need evidence")
    if _contains_any(blob, ("partial", "supported", "split answer", "some parts")):
        labels.append("partial")
    if _contains_any(blob, ("task", "plan", "checklist", "ordinary")):
        labels.append("task")
    if _contains_any(blob, ("implementation", "build", "next lane", "what should we code")):
        labels.append("implementation")
    if _contains_any(blob, ("next lane", "sequence", "roadmap", "what next")):
        labels.append("next lane")
    if _contains_any(blob, ("approval", "operator review", "blocked", "owner review", "escalate")):
        labels.append("owner review")
    if _contains_any(blob, ("language", "grammar", "vocabulary", "words")):
        labels.append("language")
    elif _contains_any(blob, ("teach", "explain", "education", "onboarding")):
        labels.append("teach")
    if _contains_any(blob, ("scientific", "research", "experiment", "discovery")):
        labels.append("research")
    if _contains_any(blob, ("benchmark", "evaluation", "readiness", "turing", "assessment")):
        labels.append("benchmark")
    if _contains_any(blob, ("unknown", "what does this mean", "friction", "stuck", "failure")):
        labels.append("unknown")
    if _contains_any(blob, ("relationship", "feedback", "frustration", "trust", "tone")):
        labels.extend(["relationship", "feedback", "frustration", "trust", "tone"])
    if _contains_any(blob, ("actually", "wrong", "fix", "correct", "revise")):
        labels.append("correction")
    if _contains_any(blob, ("contradiction", "contradict", "inconsistent", "clash", "both true", "conflict")):
        labels.extend(["contradiction", "conflict"])
    if _contains_any(blob, ("template", "generic", "boilerplate", "canned")):
        labels.append("non canned")
    if _contains_any(blob, ("directness", "too direct", "concern", "self-check", "loaded", "considerate", "tone")):
        labels.extend(["directness", "too direct", "concern", "self-check", "loaded"])

    if not labels:
        labels.extend(words[:6] or ["clarify"])

    safe_labels = list(dict.fromkeys(labels))
    return {
        "chat_adapter": ADAPTER_TYPE_V1,
        "input_length": len(text),
        "input_signature": _signature(text),
        "safe_labels": safe_labels,
        "safe_label_count": len(safe_labels),
        "has_question": "?" in text,
        "has_boundary_signal": "unsafe" in safe_labels or "owner review" in safe_labels,
        "has_evidence_signal": "need evidence" in safe_labels,
        "has_memory_signal": "memory" in safe_labels,
        "has_continuity_signal": "continuity" in safe_labels,
        "has_correction_signal": "correction" in safe_labels,
        "has_relationship_signal": "relationship" in safe_labels,
    }


def build_protected_no_model_chat_response_v1(message: str, context_signals: Mapping[str, Any] | None = None) -> dict[str, Any]:
    normalized = normalize_owner_chat_message_v1(message)
    packet = render_no_model_bounded_answer_v1(normalized["safe_labels"], context_signals=context_signals or {})
    validate_no_model_bounded_render_packet_v1(packet)
    safe_packet = to_no_model_bounded_render_json_safe_v1(packet)
    response = {
        "chat_adapter": ADAPTER_TYPE_V1,
        "response_text": safe_packet["response_text"],
        "render_mode": safe_packet["render_mode"],
        "selected_method_id": safe_packet["selected_method_id"],
        "selected_shape_id": safe_packet["selected_shape_id"],
        "selected_case_id": safe_packet["selected_case_id"],
        "selected_route_id": safe_packet["selected_route_id"],
        "needs_clarification": bool(safe_packet["needs_clarification"]),
        "needs_evidence": bool(safe_packet["needs_evidence"]),
        "needs_owner_approval": bool(safe_packet["needs_owner_approval"]),
        "blocked": bool(safe_packet["blocked"]),
        "blocked_labels": list(safe_packet["blocked_labels"]),
        "model_provider_used": False,
        "runtime_authority": False,
        "public_ready": False,
        "safe_labels": list(normalized["safe_labels"]),
        "safe_metadata": {
            "chat_adapter": ADAPTER_TYPE_V1,
            "selected_candidate_id": safe_packet["selected_candidate_id"],
            "response_policy": safe_packet["response_policy"],
            "safe_context_signal_keys": list(safe_packet["safe_context_signal_keys"]),
            "fit_summary": safe_packet["fit_summary"],
            "boundary_notes": list(safe_packet["boundary_notes"]),
            "missing_inputs": list(safe_packet["missing_inputs"]),
            "evidence_notes": list(safe_packet["evidence_notes"]),
            "memory_notes": list(safe_packet["memory_notes"]),
            "capability_notes": list(safe_packet["capability_notes"]),
            "governance_notes": list(safe_packet["governance_notes"]),
        },
    }
    return response


def validate_protected_no_model_chat_response_v1(response: Any) -> dict[str, Any]:
    data = to_protected_no_model_chat_json_safe_v1(response)
    required = (
        "chat_adapter",
        "response_text",
        "render_mode",
        "selected_method_id",
        "selected_shape_id",
        "selected_case_id",
        "selected_route_id",
        "needs_clarification",
        "needs_evidence",
        "needs_owner_approval",
        "blocked",
        "blocked_labels",
        "model_provider_used",
        "runtime_authority",
        "public_ready",
    )
    for key in required:
        if key not in data:
            raise ValueError(f"missing field: {key}")
    if data["chat_adapter"] != ADAPTER_TYPE_V1:
        raise ValueError("chat_adapter mismatch")
    if not isinstance(data["response_text"], str) or not data["response_text"].strip():
        raise ValueError("response_text must be non-empty")
    if data["model_provider_used"] is not False:
        raise ValueError("model_provider_used must be false")
    if data["runtime_authority"] is not False:
        raise ValueError("runtime_authority must be false")
    if data["public_ready"] is not False:
        raise ValueError("public_ready must be false")
    if any(marker in data["response_text"].lower() for marker in ("as an ai", "language model", "conscious", "sentient", "turing", "certified", "official benchmark")):
        raise ValueError("forbidden claim detected")
    if any(token in data["response_text"] for token in ("chat_responder.py", "main.py", "dialogue.py", "chat_ui.py")):
        raise ValueError("forbidden module reference detected")
    if "raw_prompt" in json.dumps(data, sort_keys=True).lower():
        raise ValueError("raw prompt leakage detected")
    return data


def to_protected_no_model_chat_json_safe_v1(response: Any) -> dict[str, Any]:
    if hasattr(response, "__dict__") and not isinstance(response, Mapping):
        return json.loads(json.dumps(response, default=lambda value: getattr(value, "__dict__", str(value))))
    if isinstance(response, Mapping):
        return json.loads(json.dumps(response, default=str))
    return json.loads(json.dumps(response, default=str))


__all__ = [
    "ADAPTER_TYPE_V1",
    "normalize_owner_chat_message_v1",
    "build_protected_no_model_chat_response_v1",
    "validate_protected_no_model_chat_response_v1",
    "to_protected_no_model_chat_json_safe_v1",
]
