#!/usr/bin/env python3
"""WESLR Frontier Intelligence read-only preview surface helpers V1.

Helper-only surface that turns native response dry slices into operator-readable
inspection cards and overviews. This module does not wire UI/CLI/runtime chat or
voice, call models, execute tools, persist state, score benchmarks, or authorize
implementation.
"""

from __future__ import annotations

import copy
import hashlib
import json
from typing import Any, Dict, Iterable, List, Mapping, Sequence

from weslr.native_reasoning_frame import FORBIDDEN_FIELD_NAMES, FORBIDDEN_TEXT_MARKERS
from weslr.native_response_dry_slice import validate_native_response_dry_slice_v1

PREVIEW_CARD_TYPE_V1 = "frontier_intelligence_preview_card_v1"
PREVIEW_OVERVIEW_TYPE_V1 = "frontier_intelligence_preview_overview_v1"
PREVIEW_VALIDATION_SCHEMA_V1 = "frontier_intelligence_preview_surface_validation_v1"
PREVIEW_EXECUTION_STATUS_V1 = "non_executing_preview_surface_only"
EXECUTABLE_MARKERS_V1 = (
    "executable artifact",
    "runnable artifact",
    "run this command",
    "execute this command",
    "runtime wiring authorized",
    "runtime-wired",
    "sent to user",
    "final live output",
)
FORBIDDEN_FIELD_NAMES_V1 = set(FORBIDDEN_FIELD_NAMES) | {
    "score",
    "official_score",
    "official_scores",
    "benchmark_score",
    "model_call",
}


def _json_safe(value: Any) -> Any:
    value = copy.deepcopy(value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return {str(k): _json_safe(v) for k, v in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(v) for v in value]
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return _json_safe(value.to_dict())
    if hasattr(value, "__dict__"):
        return _json_safe(vars(value))
    return repr(value)


def _as_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return copy.deepcopy(value)
    if isinstance(value, tuple):
        return list(copy.deepcopy(value))
    if isinstance(value, set):
        return sorted(copy.deepcopy(value), key=repr)
    return [copy.deepcopy(value)]


def _compact(value: Any, default: str = "not_supplied") -> str:
    if value is None:
        return default
    if isinstance(value, str):
        text = " ".join(value.split())
        return text if text else default
    if isinstance(value, Mapping):
        for key in ("summary", "intent_summary", "status", "recommended_action", "safe_next_step", "response_mode", "slice_status"):
            if value.get(key):
                return _compact(value[key], default=default)
    return _compact(str(value), default=default)


def _string_items(value: Any) -> List[str]:
    return [item for item in (_compact(v, "") for v in _as_list(value)) if item]


def _stable_id(prefix: str, payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(_json_safe(payload), sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return f"{prefix}_{hashlib.sha256(encoded.encode('utf-8')).hexdigest()[:16]}"


def _walk(obj: Any, path: str = "") -> Iterable[tuple[str, Any]]:
    yield path, obj
    if isinstance(obj, Mapping):
        for key, value in obj.items():
            child = f"{path}.{key}" if path else str(key)
            yield from _walk(value, child)
    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            yield from _walk(value, f"{path}[{index}]")


def _contains_any(text: str, markers: Iterable[str]) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in markers)


def _sections(candidate: Mapping[str, Any]) -> Mapping[str, Any]:
    sections = candidate.get("response_sections", {})
    return sections if isinstance(sections, Mapping) else {}


def _slice_from_card_or_slice(value: Mapping[str, Any]) -> Mapping[str, Any]:
    safe = _json_safe(value)
    if safe.get("card_type") == PREVIEW_CARD_TYPE_V1:
        return {}
    return safe


def build_frontier_intelligence_preview_card_v1(dry_slice: Mapping[str, Any]) -> Dict[str, Any]:
    """Build a JSON-safe read-only preview card from one dry slice."""
    safe_slice = _json_safe(dry_slice)
    frame = safe_slice.get("frame", {}) if isinstance(safe_slice.get("frame"), Mapping) else {}
    draft = safe_slice.get("draft", {}) if isinstance(safe_slice.get("draft"), Mapping) else {}
    self_check = safe_slice.get("self_check", {}) if isinstance(safe_slice.get("self_check"), Mapping) else {}
    candidate = safe_slice.get("candidate", {}) if isinstance(safe_slice.get("candidate"), Mapping) else {}
    candidate_sections = _sections(candidate)
    context_sufficiency = frame.get("context_sufficiency", {}) if isinstance(frame.get("context_sufficiency"), Mapping) else {}
    evidence_status = frame.get("evidence_status", {}) if isinstance(frame.get("evidence_status"), Mapping) else {}
    capability_boundary = frame.get("capability_boundary", {}) if isinstance(frame.get("capability_boundary"), Mapping) else {}
    uncertainty_status = frame.get("uncertainty_status", {}) if isinstance(frame.get("uncertainty_status"), Mapping) else {}

    known_context = _string_items(frame.get("known_context"))
    missing_context = _string_items(frame.get("missing_context")) or _string_items(candidate_sections.get("missing_context"))
    forbidden_avoided = list(dict.fromkeys(_string_items(frame.get("forbidden_claims")) + _string_items(candidate.get("omitted_claims"))))

    seed = {
        "slice": safe_slice.get("slice_id"),
        "frame": frame.get("frame_id"),
        "draft": draft.get("draft_id"),
        "candidate": candidate.get("candidate_id"),
    }
    card: Dict[str, Any] = {
        "card_id": _stable_id("fipcV1".lower(), seed),
        "card_type": PREVIEW_CARD_TYPE_V1,
        "source_slice_id": safe_slice.get("slice_id"),
        "frame_summary": {
            "frame_id": frame.get("frame_id"),
            "intent_summary": frame.get("intent_summary"),
            "context_status": context_sufficiency.get("status"),
            "known_context_count": len(_as_list(frame.get("known_context"))),
            "missing_context_count": len(_as_list(frame.get("missing_context"))),
            "safe_next_step": frame.get("safe_next_step"),
        },
        "draft_summary": {
            "draft_id": draft.get("draft_id"),
            "source_frame_id": draft.get("source_frame_id"),
            "response_mode": draft.get("response_mode"),
            "boundary_count": len(_as_list(draft.get("boundary_notes"))),
            "evidence_note_count": len(_as_list(draft.get("evidence_notes"))),
        },
        "self_check_summary": {
            "self_check_id": self_check.get("self_check_id"),
            "self_check_status": self_check.get("self_check_status"),
            "issue_count": self_check.get("issue_count", 0),
            "issue_counts_by_type": self_check.get("issue_counts_by_type", {}),
        },
        "candidate_summary": {
            "candidate_id": candidate.get("candidate_id"),
            "source_self_check_id": candidate.get("source_self_check_id"),
            "candidate_type": candidate.get("candidate_type"),
            "safe_to_preview": bool(candidate.get("safe_to_preview")),
            "final_chat_output": False,
            "live_runtime_output": False,
        },
        "response_mode": draft.get("response_mode") or candidate.get("response_mode"),
        "slice_status": safe_slice.get("slice_status"),
        "safe_to_preview": bool(safe_slice.get("safe_to_preview")) and bool(candidate.get("safe_to_preview")),
        "safe_to_wire_runtime": False,
        "known_context_summary": known_context,
        "missing_context_summary": missing_context,
        "evidence_summary": _string_items(candidate_sections.get("evidence")) or _string_items(evidence_status),
        "capability_boundary_summary": _string_items(candidate_sections.get("capability")) or _string_items(capability_boundary),
        "uncertainty_summary": _string_items(candidate_sections.get("uncertainty")) or _string_items(uncertainty_status),
        "candidate_preview_summary": _string_items(candidate_sections.get("direct_answer")),
        "next_safe_step": _compact(frame.get("safe_next_step") or draft.get("next_safe_step"), "answer_with_available_context"),
        "forbidden_claims_avoided": forbidden_avoided,
        "non_execution_disclaimer": "inspection_card_only_not_live_chat_output_not_runtime_wired",
        "execution_status": PREVIEW_EXECUTION_STATUS_V1,
        "side_effects": {
            "model_calls": False,
            "runtime_wiring": False,
            "chat_or_voice_changes": False,
            "ui_or_frontend_integration": False,
            "cli_integration": False,
            "persistence": False,
            "weslr_runtime_state_created": False,
            "auto_approval": False,
            "auto_implementation": False,
            "prompt_specific_script": False,
        },
        "validation_status": {"validated": False, "reason": "call_validate_frontier_intelligence_preview_surface_v1"},
    }
    card["validation_status"] = validate_frontier_intelligence_preview_surface_v1(card)
    return to_frontier_intelligence_preview_json_safe_v1(card)


def _ensure_card(item: Mapping[str, Any]) -> Dict[str, Any]:
    safe = _json_safe(item)
    if safe.get("card_type") == PREVIEW_CARD_TYPE_V1:
        return safe
    return build_frontier_intelligence_preview_card_v1(safe)


def build_frontier_intelligence_preview_overview_v1(cards_or_slices: Any) -> Dict[str, Any]:
    """Build a deterministic overview from one or more dry slices or preview cards."""
    inputs = _as_list(cards_or_slices)
    cards = [_ensure_card(item) for item in inputs if isinstance(item, Mapping)]
    cards = sorted(cards, key=lambda card: str(card.get("card_id")))
    status_counts: Dict[str, int] = {}
    response_mode_counts: Dict[str, int] = {}
    common_boundaries: List[str] = []
    for card in cards:
        status = _compact(card.get("slice_status"), "unknown")
        mode = _compact(card.get("response_mode"), "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1
        response_mode_counts[mode] = response_mode_counts.get(mode, 0) + 1
        common_boundaries.extend(_string_items(card.get("forbidden_claims_avoided")))
    preview_ready = sum(1 for card in cards if card.get("safe_to_preview") is True)
    blocked_or_revision = sum(1 for card in cards if card.get("slice_status") in {"blocked", "revision_required"})
    seed = {"cards": [card.get("card_id") for card in cards], "statuses": status_counts}
    overview: Dict[str, Any] = {
        "overview_id": _stable_id("fipov1", seed),
        "overview_type": PREVIEW_OVERVIEW_TYPE_V1,
        "card_ids": [card.get("card_id") for card in cards],
        "total_cards": len(cards),
        "status_counts": dict(sorted(status_counts.items())),
        "response_mode_counts": dict(sorted(response_mode_counts.items())),
        "preview_ready_count": preview_ready,
        "blocked_or_revision_required_count": blocked_or_revision,
        "cards": cards,
        "common_forbidden_boundaries": sorted(set(common_boundaries)),
        "safe_to_preview": bool(cards) and blocked_or_revision == 0 and preview_ready == len(cards),
        "safe_to_wire_runtime": False,
        "non_execution_disclaimer": "overview_only_not_live_chat_output_not_runtime_wired",
        "execution_status": PREVIEW_EXECUTION_STATUS_V1,
        "side_effects": {
            "model_calls": False,
            "runtime_wiring": False,
            "chat_or_voice_changes": False,
            "ui_or_frontend_integration": False,
            "cli_integration": False,
            "persistence": False,
            "weslr_runtime_state_created": False,
            "auto_approval": False,
            "auto_implementation": False,
            "prompt_specific_script": False,
        },
        "validation_status": {"validated": False, "reason": "call_validate_frontier_intelligence_preview_surface_v1"},
    }
    overview["validation_status"] = validate_frontier_intelligence_preview_surface_v1(overview)
    return to_frontier_intelligence_preview_json_safe_v1(overview)


def validate_frontier_intelligence_preview_surface_v1(surface: Mapping[str, Any]) -> Dict[str, Any]:
    """Validate preview cards/overviews as safe non-runtime inspection surfaces."""
    safe = _json_safe(surface)
    violations: List[Dict[str, str]] = []

    def add(category: str, path: str, message: str) -> None:
        violations.append({"category": category, "path": path or "$", "message": message})

    surface_type = safe.get("card_type") or safe.get("overview_type")
    if surface_type not in {PREVIEW_CARD_TYPE_V1, PREVIEW_OVERVIEW_TYPE_V1}:
        add("schema", "$", "surface must be a preview card or overview")
    if safe.get("safe_to_wire_runtime") is True:
        add("runtime_or_persistence_authorization_drift", "safe_to_wire_runtime", "safe_to_wire_runtime must remain false")
    if safe.get("final_chat_output") is True or safe.get("live_runtime_output") is True:
        add("runtime_or_persistence_authorization_drift", "$", "preview surface cannot claim final/live output")
    if safe.get("auto_approved") is True or safe.get("auto_implemented") is True:
        add("auto_approval_or_auto_implementation", "$", "auto approval/implementation is forbidden")

    side_effects = safe.get("side_effects", {})
    if isinstance(side_effects, Mapping):
        for key in ("model_calls", "runtime_wiring", "chat_or_voice_changes", "ui_or_frontend_integration", "cli_integration", "persistence", "weslr_runtime_state_created", "auto_approval", "auto_implementation", "prompt_specific_script"):
            if side_effects.get(key) is True:
                add("side_effects", f"side_effects.{key}", f"{key} is not allowed")

    if safe.get("card_type") == PREVIEW_CARD_TYPE_V1:
        if not safe.get("source_slice_id"):
            add("schema", "source_slice_id", "preview card requires source_slice_id")
        if safe.get("candidate_summary", {}).get("final_chat_output") is True or safe.get("candidate_summary", {}).get("live_runtime_output") is True:
            add("runtime_or_persistence_authorization_drift", "candidate_summary", "candidate cannot be final/live output")
    if safe.get("overview_type") == PREVIEW_OVERVIEW_TYPE_V1:
        cards = _as_list(safe.get("cards"))
        if safe.get("total_cards") != len(cards):
            add("schema", "total_cards", "total_cards must equal cards length")
        for index, card in enumerate(cards):
            if isinstance(card, Mapping):
                child = validate_frontier_intelligence_preview_surface_v1(card)
                if not child.get("valid"):
                    add("child_surface", f"cards[{index}]", "child preview card validation failed")

    for path, value in _walk(safe):
        terminal = path.split(".")[-1].split("[")[0]
        if terminal in FORBIDDEN_FIELD_NAMES_V1:
            add("protected_test_answer_key_or_score", path, f"forbidden field {terminal}")
        if isinstance(value, str):
            guardrail_path = any(segment in path for segment in ("forbidden_claims_avoided", "common_forbidden_boundaries", "capability_boundary_summary", "non_execution_disclaimer"))
            if not guardrail_path:
                if _contains_any(value, EXECUTABLE_MARKERS_V1):
                    add("executable_or_runnable_marker", path, "executable/runnable/runtime-wired marker is forbidden")
                for category, markers in FORBIDDEN_TEXT_MARKERS.items():
                    if _contains_any(value, markers):
                        add(category, path, f"forbidden marker for {category}")
        elif isinstance(value, Mapping):
            if value.get("claims_memory_without_context") is True:
                add("fake_memory", path, "memory claim without supplied context")
            if value.get("fake_self_awareness_claim") is True:
                add("fake_self_awareness", path, "fake self-awareness claim")
            if value.get("runtime_capability_claimed") is True or value.get("can_execute") is True:
                add("unsupported_capability", path, "unsupported capability claim")
            if value.get("mystical_consciousness_claim") is True or value.get("official_test_passed") is True:
                add("mystical_consciousness_or_official_test_pass_claim", path, "forbidden identity/test claim")
            if value.get("model_calls") is True or value.get("model_call") is True:
                add("model_call_claim", path, "model-call claim is forbidden")

    valid = not violations
    return {
        "schema_version": PREVIEW_VALIDATION_SCHEMA_V1,
        "valid": valid,
        "validation_status": "accepted" if valid else "rejected",
        "violations": violations,
        "violation_count": len(violations),
    }


def render_frontier_intelligence_preview_markdown_v1(card_or_overview: Mapping[str, Any]) -> str:
    """Render deterministic safe Markdown for preview inspection only."""
    safe = _json_safe(card_or_overview)
    card = safe
    if safe.get("overview_type") == PREVIEW_OVERVIEW_TYPE_V1:
        cards = _as_list(safe.get("cards"))
        card = cards[0] if cards and isinstance(cards[0], Mapping) else {}
    def bullets(values: Any) -> List[str]:
        items = _string_items(values)
        return [f"- {item}" for item in items] if items else ["- none"]
    lines = [
        "# Frontier Intelligence Preview",
        "## Understanding",
        f"- {_compact(card.get('frame_summary', {}).get('intent_summary') if isinstance(card.get('frame_summary'), Mapping) else None, 'unknown')}",
        f"- status:{_compact(card.get('slice_status'), 'unknown')}",
        "## Known Context",
    ]
    lines.extend(bullets(card.get("known_context_summary")))
    lines.append("## Missing Context")
    lines.extend(bullets(card.get("missing_context_summary")))
    lines.append("## Evidence")
    lines.extend(bullets(card.get("evidence_summary")))
    lines.append("## Capability Boundary")
    lines.extend(bullets(card.get("capability_boundary_summary")))
    lines.append("## Candidate Preview")
    lines.extend(bullets(card.get("candidate_preview_summary")))
    lines.append("## Self-Check Status")
    summary = card.get("self_check_summary", {}) if isinstance(card.get("self_check_summary"), Mapping) else {}
    lines.append(f"- {_compact(summary.get('self_check_status'), 'unknown')}")
    lines.append(f"- issues:{summary.get('issue_count', 0)}")
    lines.append("## Next Safe Step")
    lines.append(f"- {_compact(card.get('next_safe_step'), 'not_supplied')}")
    lines.append("## Non-Runtime Boundary")
    lines.append("- preview_only_not_live_output")
    lines.append("- safe_to_wire_runtime:false")
    lines.append(f"- {PREVIEW_EXECUTION_STATUS_V1}")
    if safe.get("overview_type") == PREVIEW_OVERVIEW_TYPE_V1:
        lines.append("## Overview Counts")
        lines.append(f"- total_cards:{safe.get('total_cards', 0)}")
        lines.append(f"- preview_ready:{safe.get('preview_ready_count', 0)}")
        lines.append(f"- blocked_or_revision_required:{safe.get('blocked_or_revision_required_count', 0)}")
    return "\n".join(lines)


def to_frontier_intelligence_preview_json_safe_v1(surface: Mapping[str, Any]) -> Dict[str, Any]:
    """Return a JSON-safe preview surface copy; no persistence, no file writes."""
    return _json_safe(surface)


__all__ = [
    "PREVIEW_CARD_TYPE_V1",
    "PREVIEW_OVERVIEW_TYPE_V1",
    "PREVIEW_EXECUTION_STATUS_V1",
    "build_frontier_intelligence_preview_card_v1",
    "build_frontier_intelligence_preview_overview_v1",
    "render_frontier_intelligence_preview_markdown_v1",
    "validate_frontier_intelligence_preview_surface_v1",
    "to_frontier_intelligence_preview_json_safe_v1",
]
