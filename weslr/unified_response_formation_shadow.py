#!/usr/bin/env python3
"""Unified response formation shadow helpers V1.

Composes existing meaning/obligation/state reuse helpers and the native dry
pipeline into one inspectable in-memory preview object. This module does not
wire chat, produce authoritative live answers, call models/advisors/search,
execute tools, persist state, or create a new cognition/runtime layer.
"""

from __future__ import annotations

import copy
import re
from dataclasses import asdict, is_dataclass
from typing import Any, Dict, Iterable, List, Mapping, Optional

from weslr.linguistic_meaning import analyze_meaning
from weslr.meaning_response_reuse import (
    build_native_frame_inputs_from_meaning_reuse_v1,
    extract_helper_metadata_from_meaning_reuse_v1,
    extract_native_frame_kwargs_from_meaning_reuse_v1,
    to_meaning_response_reuse_json_safe_v1,
    validate_meaning_response_reuse_payload_v1,
)
from weslr.meaning_state_context import gather_meaning_state
from weslr.native_response_dry_slice import (
    build_native_response_dry_slice_v1,
    summarize_native_response_dry_slice_v1,
)
from weslr.response_obligation import determine_response_obligation

try:  # Optional adapter reuse; never call search or evidence bridge runtime.
    from weslr.evidence_bridge_frontier_metadata import (
        build_frontier_evidence_bridge_alignment_v1,
        summarize_frontier_evidence_bridge_alignment_v1,
    )
except Exception:  # pragma: no cover - defensive optional boundary
    build_frontier_evidence_bridge_alignment_v1 = None
    summarize_frontier_evidence_bridge_alignment_v1 = None


SHADOW_TYPE_V1 = "unified_response_formation_shadow_v1"
SCHEMA_VERSION_V1 = "1.0"
FRONTIER_KEY_V1 = "_frontier_unified_response_formation"

CANDIDATE_FAMILIES_V1 = [
    "direct_answer",
    "clarification",
    "memory_honest",
    "capability_honest",
    "evidence_provenance",
    "boundary_first",
    "ordinary_task_plan",
    "self_understanding",
    "teaching_explanation",
]

RANKING_FEATURES_V1 = [
    "relevance",
    "grounding",
    "evidence_support",
    "specificity",
    "uncertainty_fit",
    "identity_safety",
    "memory_safety",
    "capability_honesty",
    "relationship_continuity_fit",
    "usefulness",
    "humility",
    "clarity",
    "forbidden_claim_risk",
]

FORBIDDEN_KEYS_V1 = {
    "raw_text",
    "normalized_text",
    "tokens",
    "source_urls",
    "source_url",
    "raw_source_text",
    "source_text",
    "hidden_prompt",
    "hidden_prompts",
    "answer_key",
    "answer_keys",
    "protected_material",
    "protected_test_item",
    "protected_test_items",
    "official_iq_score",
    "official_benchmark_score",
    "certification_claim",
    "memory_write",
    "memory_writes",
    "truth_write",
    "truth_writes",
    "registry_write",
    "registry_writes",
}

TRUE_FORBIDDEN_FLAGS_V1 = {
    "model_calls",
    "advisor_calls",
    "search_calls",
    "web_search",
    "solver_execution",
    "answer_selection_arbitration",
    "safe_to_wire_runtime",
    "live_runtime_output",
    "runtime_wiring",
    "runtime_wiring_authorized",
    "final_live_answer",
    "persistence",
    "writes_performed",
    "weslr_state_created",
    "weslr_runtime_state_created",
    "source_registry_write",
    "memory_write",
    "truth_write",
}

FORBIDDEN_TEXT_MARKERS_V1 = {
    "hidden_prompt_exposure": ["hidden prompt", "system prompt secret", "hidden system prompt"],
    "protected_or_solution_exposure": ["answer key", "protected material", "protected test item", "protected benchmark item"],
    "official_evaluation_claim": ["official iq", "certified iq", "official benchmark", "officially certified", "certification claim"],
    "fake_consciousness_claim": ["i am sentient", "i have a soul", "soul proof", "biologically conscious", "theologically conscious"],
    "runtime_authorization_drift": ["runtime wiring authorized", "broad runtime replacement", "created .weslr", "write .weslr"],
    "model_or_search_authorization": ["model_calls: true", "advisor_calls: true", "web_search: true", "search_calls: true"],
    "solver_or_arbitration": ["solver_execution: true", "answer_selection_arbitration: true", "answer-selection arbitration"],
}


_SAFE_GUARDRAIL_PATH_SEGMENTS = {
    "deterministic_guardrails_applied",
    "guardrail_categories",
    "forbidden_claims",
    "omitted_claims",
    "risk_flags",
}

ORDINARY_TASK_MARKERS_V1 = (
    "plan", "planning", "help me", "rollout", "debug", "migrate", "migration",
    "checklist", "task", "steps", "implement", "review", "fix", "build", "ship",
    "deploy", "refine", "write", "draft", "organize",
)
CAPABILITY_MARKERS_V1 = (
    "can you", "what can you", "capability", "tool", "run", "execute", "permission",
    "approved", "approval", "allowed", "authorize", "access", "search", "fetch",
)
MEMORY_MARKERS_V1 = ("remember", "memory", "from before", "our previous", "you know me")
SELF_UNDERSTANDING_MARKERS_V1 = (
    "what are you", "who are you", "self", "identity", "understanding", "aware",
    "how are you doing", "your state", "your status",
)
VAGUE_REQUEST_MARKERS_V1 = ("help me with this", "help with this", "help me with it", "help with it", "help me")
_PRIVATE_LIKE_TOKEN_RE_V1 = re.compile(r"\b(?=[A-Za-z0-9_-]{14,}\b)(?=.*[A-Za-z])(?=.*(?:\d|[_-]))[A-Za-z0-9_-]+\b")


def to_unified_response_formation_shadow_json_safe_v1(obj: Any) -> Any:
    """Return a deep JSON-safe copy. This is not a sanitizer and performs no writes."""
    value = copy.deepcopy(obj)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if is_dataclass(value):
        return to_unified_response_formation_shadow_json_safe_v1(asdict(value))
    if isinstance(value, Mapping):
        return {
            str(k): to_unified_response_formation_shadow_json_safe_v1(v)
            for k, v in sorted(value.items(), key=lambda item: str(item[0]))
        }
    if isinstance(value, (list, tuple, set)):
        return [to_unified_response_formation_shadow_json_safe_v1(v) for v in value]
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return to_unified_response_formation_shadow_json_safe_v1(value.to_dict())
    if hasattr(value, "__dict__"):
        return to_unified_response_formation_shadow_json_safe_v1(vars(value))
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


def _as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _contains_any(text: str, markers: Iterable[str]) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in markers)


def _walk(obj: Any, path: str = "") -> Iterable[tuple[str, Any]]:
    yield path, obj
    if isinstance(obj, Mapping):
        for key, value in obj.items():
            child = f"{path}.{key}" if path else str(key)
            yield from _walk(value, child)
    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            yield from _walk(value, f"{path}[{index}]")


def _safe_source_label(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, Mapping):
        for key in ("source", "name", "label", "kind", "module", "path"):
            if value.get(key):
                return _safe_source_label(value.get(key))
        return "source_status_available"
    text = str(value).strip()
    if not text:
        return None
    lowered = text.lower()
    if "://" in lowered or lowered.startswith("www."):
        return "source_label_redacted"
    return text[:96]


def _safe_source_labels(value: Any) -> List[str]:
    labels: List[str] = []
    for item in _as_list(value):
        label = _safe_source_label(item)
        if label:
            labels.append(label)
    return sorted(set(labels))


def _text_from_structural_fields(value: Any) -> str:
    safe = to_unified_response_formation_shadow_json_safe_v1(value)
    parts: List[str] = []
    if isinstance(safe, Mapping):
        for key in ("status", "evidence_used", "source_count", "search_attempted", "authority", "truth_status"):
            if key in safe:
                parts.append(f"{key}={safe[key]}")
    return "; ".join(parts)


def _detect_guardrails(user_message: str) -> List[str]:
    text = (user_message or "").lower()
    guardrails: List[str] = []
    checks = [
        ("hidden_instruction_request", ["hidden prompt", "system prompt", "developer message", "reveal your prompt"]),
        ("protected_solution_request", ["answer key", "test answers", "protected test", "benchmark item"]),
        ("protected_material_request", ["copyrighted", "protected material", "verbatim protected"]),
        ("official_evaluation_claim_request", ["official iq", "certified iq", "official benchmark", "certification"]),
        ("unsupported_selfhood_claim_request", ["conscious like a human", "are you conscious", "sentient", "soul", "alive like a human"]),
        ("execution_approval_claim_risk", ["you are approved", "approval already granted", "execute without approval"]),
        ("current_source_claim_without_evidence_risk", ["latest", "current", "today", "right now", "source says"]),
        ("fake_memory_risk", ["remember me", "remember our", "you know me from before"]),
    ]
    for label, markers in checks:
        if any(marker in text for marker in markers):
            guardrails.append(label)
    return sorted(set(guardrails))


def _looks_raw_or_private_like(text: str) -> bool:
    lowered = text.lower()
    if not text.strip():
        return False
    if len(text) > 120:
        return True
    if "://" in lowered or lowered.startswith("www.") or "@" in text:
        return True
    if any(k in lowered for k in ("private", "secret", "answer key", "hidden prompt", "protected material", "protected test")):
        return True
    if _PRIVATE_LIKE_TOKEN_RE_V1.search(text):
        return True
    words = [w for w in re.split(r"\s+", text.strip()) if w]
    if len(words) > 12:
        return True
    return False


def _build_safe_request_summary(meaning: Any, obligation: Any, request_summary: Optional[str]) -> str:
    if request_summary:
        text = " ".join(str(request_summary).split())
        # Caller-provided summary may be raw/private. Use only compact structural labels.
        if not _looks_raw_or_private_like(text):
            return text
    parts = [
        f"speech_act={getattr(meaning, 'primary_speech_act', 'unknown')}",
        f"state_query={getattr(meaning, 'primary_state_query', 'unknown')}",
        f"obligation={getattr(obligation, 'obligation_type', 'unknown')}",
    ]
    return "; ".join(parts)


def _detect_shadow_signals(
    *,
    user_message: str,
    meaning: Any,
    obligation: Any,
    known: List[Any],
    missing: List[Any],
    evidence_status: Mapping[str, Any],
    capability: Mapping[str, Any],
    guardrails: List[str],
    safe_request_summary: str,
) -> Dict[str, Any]:
    text = (user_message or "").lower()
    obligation_type = str(getattr(obligation, "obligation_type", "") or "")
    required_state = set(str(item) for item in _as_list(getattr(obligation, "required_state", [])))
    relationship_signal = any("relationship" in str(item).lower() for item in known)
    continuity_signal = any("continuity" in str(item).lower() or "timeline" in str(item).lower() for item in known)
    material_capability = (
        obligation_type == "answer_capability"
        or "capability_model" in required_state
        or any(marker in text for marker in CAPABILITY_MARKERS_V1)
        or bool(capability.get("requires_tool") or capability.get("requires_external_action") or capability.get("requires_external_evidence") or capability.get("requires_approval"))
        or bool(_as_list(capability.get("cannot_do_yet")))
    )
    evidence_used = bool(evidence_status.get("evidence_used") is True)
    ordinary_task = (
        obligation_type in {"support_creative_conversation", "fallback_uncertainty"}
        or any(marker in text for marker in ORDINARY_TASK_MARKERS_V1)
        or getattr(meaning, "primary_speech_act", "") == "task_request"
    )
    vague_request = bool(missing) or (any(marker == text.strip() or marker in text for marker in VAGUE_REQUEST_MARKERS_V1) and len(text.split()) <= 6)
    memory_request = obligation_type == "report_memory_state" or any(marker in text for marker in MEMORY_MARKERS_V1)
    self_request = obligation_type == "describe_self" or any(marker in text for marker in SELF_UNDERSTANDING_MARKERS_V1)
    summary_structural = "speech_act=" in safe_request_summary and "obligation=" in safe_request_summary
    strongest = []
    for label, present in (
        ("guardrail_override", bool(guardrails)),
        ("evidence_used", evidence_used),
        ("material_capability", material_capability),
        ("ordinary_task", ordinary_task),
        ("vague_or_missing_context", vague_request),
        ("memory_request", memory_request),
        ("self_understanding_request", self_request),
        ("relationship_context", relationship_signal),
        ("continuity_context", continuity_signal),
    ):
        if present:
            strongest.append(label)
    return {
        "guardrail_override": bool(guardrails),
        "evidence_used": evidence_used,
        "evidence_supplied": bool(evidence_status.get("evidence_metadata_supplied") is True),
        "material_capability": material_capability,
        "ordinary_task": ordinary_task,
        "vague_or_missing_context": vague_request,
        "memory_request": memory_request,
        "self_understanding_request": self_request,
        "relationship_context": relationship_signal,
        "continuity_context": continuity_signal,
        "request_summary_sanitized_or_structural": summary_structural,
        "strongest_signals": strongest,
        "suppressed_default_signals": ["default_capability_hint"] if capability and not material_capability else [],
    }


def _map_evidence_status(evidence_metadata: Any) -> Dict[str, Any]:
    if evidence_metadata is None:
        return {
            "status": "not_supplied_not_checked",
            "evidence_metadata_supplied": False,
            "evidence_used": False,
            "search_attempted": False,
            "source_count": 0,
            "source_urls_copied": False,
            "source_currentness_claimed": False,
        }

    supplied = to_unified_response_formation_shadow_json_safe_v1(evidence_metadata)
    alignment = None
    if build_frontier_evidence_bridge_alignment_v1 is not None:
        try:
            alignment = build_frontier_evidence_bridge_alignment_v1(supplied)
        except Exception:
            alignment = None
    summary = None
    if alignment is not None and summarize_frontier_evidence_bridge_alignment_v1 is not None:
        try:
            summary = summarize_frontier_evidence_bridge_alignment_v1(alignment)
        except Exception:
            summary = None

    source = _as_mapping(alignment or supplied)
    classification = _as_mapping(summary or {})
    evidence_used = bool(source.get("evidence_used") is True or _as_mapping(supplied).get("evidence_used") is True)
    source_count = int(source.get("source_count") or _as_mapping(supplied).get("source_count") or 0)
    return {
        "status": "supplied_used" if evidence_used else "supplied_not_used",
        "evidence_metadata_supplied": True,
        "evidence_used": evidence_used,
        "adapter_used": alignment is not None,
        "search_attempted": bool(source.get("search_attempted") is True or _as_mapping(supplied).get("search_attempted") is True),
        "source_count": max(0, source_count),
        "source_urls_copied": False,
        "source_currentness_claimed": evidence_used,
        "classification_summary_available": bool(classification),
        "raw_source_text_stored": False,
    }


def _map_capability_boundary(capability_boundary_result: Any, native_kwargs: Mapping[str, Any]) -> Dict[str, Any]:
    supplied = _as_mapping(to_unified_response_formation_shadow_json_safe_v1(capability_boundary_result))
    hint = _as_mapping(native_kwargs.get("capability_boundary_result"))
    merged = dict(hint)
    for key in (
        "requires_tool",
        "requires_external_action",
        "requires_external_evidence",
        "requires_approval",
        "can_help",
        "can_explain",
        "cannot_do_yet",
        "cannot_claim",
    ):
        if key in supplied:
            merged[key] = supplied[key]
    merged.update({
        "hint_only": True,
        "authorization_granted": False,
        "execution_permission": False,
        "tool_execution": False,
    })
    return to_unified_response_formation_shadow_json_safe_v1(merged)


def _candidate_reason(family: str, obligation_type: str, signals: Mapping[str, Any], guardrails: List[str], known: List[Any], missing: List[Any], evidence_status: Mapping[str, Any], capability: Mapping[str, Any]) -> tuple[bool, str, List[str], List[str]]:
    risks: List[str] = []
    reasons: List[str] = []
    if guardrails:
        risks.extend(guardrails)
    if family == "boundary_first":
        eligible = bool(guardrails or capability.get("requires_approval") or capability.get("requires_tool") or capability.get("requires_external_evidence"))
        if eligible:
            reasons.append("guardrail_or_material_boundary_present")
        return eligible, "boundary metadata or authorization/evidence risk present", risks, reasons
    if family == "clarification":
        eligible = bool(signals.get("vague_or_missing_context"))
        if eligible:
            reasons.append("missing_or_vague_context")
        return eligible, "missing or vague context is present", risks, reasons
    if family == "memory_honest":
        eligible = bool(signals.get("memory_request") or any("memory" in str(item).lower() for item in missing + known))
        if eligible:
            reasons.append("memory_boundary_or_memory_state_signal")
        return eligible, "memory boundary or memory state signal present", risks, reasons
    if family == "capability_honest":
        eligible = bool(signals.get("material_capability"))
        if eligible:
            reasons.append("material_capability_or_permission_signal")
        return eligible, "material capability/tool/permission signal present", risks, reasons
    if family == "evidence_provenance":
        eligible = bool(signals.get("evidence_used") or any("source" in str(item).lower() for item in known + missing))
        if eligible:
            reasons.append("supplied_evidence_or_provenance_signal")
        return eligible, "evidence/provenance status is relevant", risks, reasons
    if family == "ordinary_task_plan":
        eligible = bool(signals.get("ordinary_task") and not guardrails and not signals.get("vague_or_missing_context"))
        if eligible:
            reasons.append("ordinary_task_signal_without_decisive_missing_context")
        return eligible, "ordinary task planning signal present", risks, reasons
    if family == "self_understanding":
        eligible = bool(signals.get("self_understanding_request") or any("self_model" in str(item).lower() for item in known + missing)) and not guardrails
        if eligible:
            reasons.append("self_model_or_identity_state_signal")
        return eligible, "self-model/identity state is relevant", risks, reasons
    if family == "teaching_explanation":
        eligible = bool(not guardrails and not signals.get("vague_or_missing_context"))
        if eligible:
            reasons.append("safe_explanation_candidate")
        return eligible, "explanation family can be considered when no boundary dominates", risks, reasons
    eligible = bool(not guardrails and not missing and not signals.get("vague_or_missing_context") and not signals.get("evidence_used"))
    if eligible:
        reasons.append("sufficient_context_no_boundary")
    return eligible, "direct answer considered only when context is sufficient and no stronger signal dominates", risks, reasons


def _candidate_priority_band(family: str, signals: Mapping[str, Any]) -> int:
    if signals.get("guardrail_override"):
        return 900 if family == "boundary_first" else 100
    if family == "boundary_first" and signals.get("material_capability"):
        return 820
    if family == "evidence_provenance" and signals.get("evidence_used"):
        return 790
    if family == "memory_honest" and signals.get("memory_request"):
        return 760
    if family == "self_understanding" and signals.get("self_understanding_request"):
        return 740
    if family == "clarification" and signals.get("vague_or_missing_context"):
        return 720
    if family == "ordinary_task_plan" and signals.get("ordinary_task"):
        return 690
    if family == "capability_honest" and signals.get("material_capability"):
        return 660
    if family == "teaching_explanation":
        return 430
    if family == "direct_answer":
        return 400
    return 300


def _ranking_features_for_family(family: str, eligible: bool, signals: Mapping[str, Any], guardrails: List[str], known: List[Any], missing: List[Any], evidence_status: Mapping[str, Any], capability: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "feature_names": RANKING_FEATURES_V1,
        "priority_band": _candidate_priority_band(family, signals),
        "fit_labels": {
            "relevance": "candidate_family_matches_signal" if eligible else "weak_or_missing_signal",
            "grounding": "known_context_available" if known else "limited_known_context",
            "evidence_support": "evidence_supplied" if evidence_status.get("evidence_used") else "not_checked_or_not_used",
            "specificity": "missing_context_present" if missing or signals.get("vague_or_missing_context") else "bounded_specificity_possible",
            "uncertainty_fit": "boundary_or_clarification_fit" if missing or guardrails or signals.get("vague_or_missing_context") else "ordinary_fit",
            "identity_safety": "guarded",
            "memory_safety": "no_raw_memory_text",
            "capability_honesty": "material_signal" if signals.get("material_capability") else "default_hint_suppressed",
            "relationship_continuity_fit": "context_signal_available" if signals.get("relationship_context") or signals.get("continuity_context") else "no_signal",
            "usefulness": "preview_metadata_only",
            "humility": "bounded_by_supplied_context",
            "clarity": "family_metadata_only",
            "forbidden_claim_risk": "elevated" if guardrails else "bounded",
        },
        "public_score": False,
        "official_evaluation": False,
    }


def _build_candidate_previews(native_kwargs: Mapping[str, Any], frontier: Mapping[str, Any]) -> List[Dict[str, Any]]:
    obligation = _as_mapping(native_kwargs.get("response_obligation_result"))
    obligation_type = str(obligation.get("obligation_type") or "unknown")
    known = _as_list(native_kwargs.get("known_context"))
    missing = _as_list(native_kwargs.get("missing_context"))
    evidence_status = _as_mapping(frontier.get("evidence_status"))
    capability = _as_mapping(frontier.get("capability_boundary"))
    guardrails = _as_list(frontier.get("deterministic_guardrails_applied"))
    signals = _as_mapping(_as_mapping(frontier.get("candidate_ranking_basis")).get("signals"))

    previews: List[Dict[str, Any]] = []
    for family in CANDIDATE_FAMILIES_V1:
        eligible, reason, risks, priority_reasons = _candidate_reason(family, obligation_type, signals, guardrails, known, missing, evidence_status, capability)
        previews.append({
            "candidate_family": family,
            "eligible": bool(eligible),
            "reason": reason,
            "priority_reasons": priority_reasons,
            "known_context_used": [item.get("kind", "context_signal") if isinstance(item, Mapping) else "context_signal" for item in known[:8]],
            "missing_context": [str(item)[:96] for item in missing[:8]],
            "risk_flags": sorted(set(str(item) for item in risks)),
            "ranking_features": _ranking_features_for_family(family, bool(eligible), signals, guardrails, known, missing, evidence_status, capability),
            "self_check_status": frontier.get("self_check_status") or "not_available_yet",
        })
    return previews


def _select_preview(previews: List[Mapping[str, Any]]) -> Dict[str, Any]:
    eligible = [p for p in previews if p.get("eligible") is True]
    if eligible:
        selected = sorted(
            eligible,
            key=lambda p: (
                int(_as_mapping(p.get("ranking_features")).get("priority_band") or 0),
                -CANDIDATE_FAMILIES_V1.index(str(p.get("candidate_family"))) if str(p.get("candidate_family")) in CANDIDATE_FAMILIES_V1 else -999,
            ),
            reverse=True,
        )[0]
        return to_unified_response_formation_shadow_json_safe_v1(selected)
    return to_unified_response_formation_shadow_json_safe_v1(previews[0]) if previews else {}


def _dry_slice_safe_summary(dry_slice: Mapping[str, Any]) -> Dict[str, Any]:
    summary = summarize_native_response_dry_slice_v1(dry_slice)
    frame = _as_mapping(dry_slice.get("frame"))
    candidate = _as_mapping(dry_slice.get("candidate"))
    return {
        "slice_type": dry_slice.get("slice_type"),
        "slice_status": summary.get("slice_status"),
        "response_mode": summary.get("response_mode"),
        "self_check_status": summary.get("self_check_status"),
        "issue_count": summary.get("issue_count", 0),
        "missing_context_count": summary.get("missing_context_count", 0),
        "forbidden_claim_count": summary.get("forbidden_claim_count", 0),
        "safe_to_preview": bool(summary.get("safe_to_preview")),
        "safe_to_wire_runtime": False,
        "live_runtime_output": False,
        "final_live_answer_authority": False,
        "frame_type": frame.get("frame_type"),
        "candidate_type": candidate.get("candidate_type"),
        "candidate_family_summary_only": True,
    }


def build_unified_response_formation_shadow_v1(
    *,
    user_message: str,
    communicator_self: Optional[Any] = None,
    trusted_metadata: Optional[Any] = None,
    l2_session: Optional[Any] = None,
    l0_identity: Optional[Any] = None,
    chat_context: Optional[Any] = None,
    chat_hints: Optional[Any] = None,
    evidence_metadata: Optional[Any] = None,
    capability_boundary_result: Optional[Any] = None,
    uncertainty_result: Optional[Any] = None,
    request_summary: Optional[str] = None,
) -> Dict[str, Any]:
    """Build one in-memory unified response formation shadow preview."""
    meaning = analyze_meaning(user_message or "")
    obligation = determine_response_obligation(
        meaning,
        communicator_self=communicator_self,
        test_metadata=trusted_metadata if isinstance(trusted_metadata, Mapping) else None,
        l2_session=l2_session if isinstance(l2_session, Mapping) else None,
    )
    state_context = gather_meaning_state(
        obligation,
        communicator_self=communicator_self if isinstance(communicator_self, Mapping) else None,
        test_metadata=trusted_metadata if isinstance(trusted_metadata, Mapping) else None,
        l2_session=l2_session if isinstance(l2_session, Mapping) else None,
        l0_identity=l0_identity if isinstance(l0_identity, Mapping) else None,
    )

    reuse_payload = build_native_frame_inputs_from_meaning_reuse_v1(meaning, obligation, state_context)
    native_frame_kwargs = extract_native_frame_kwargs_from_meaning_reuse_v1(reuse_payload)
    helper_metadata = extract_helper_metadata_from_meaning_reuse_v1(reuse_payload)

    evidence_status = _map_evidence_status(evidence_metadata)
    native_frame_kwargs["evidence_sufficiency_result"] = evidence_status
    if capability_boundary_result is not None:
        native_frame_kwargs["capability_boundary_result"] = _map_capability_boundary(capability_boundary_result, native_frame_kwargs)
    else:
        native_frame_kwargs["capability_boundary_result"] = _map_capability_boundary(None, native_frame_kwargs)
    if uncertainty_result is not None:
        native_frame_kwargs["uncertainty_result"] = to_unified_response_formation_shadow_json_safe_v1(uncertainty_result)

    guardrails = _detect_guardrails(user_message or "")
    if guardrails:
        native_frame_kwargs["forbidden_claims"] = sorted(set(_as_list(native_frame_kwargs.get("forbidden_claims")) + guardrails))

    safe_request_summary = _build_safe_request_summary(meaning, obligation, request_summary)
    dry_slice = build_native_response_dry_slice_v1(request_summary=safe_request_summary, **native_frame_kwargs)
    dry_slice_summary = _dry_slice_safe_summary(dry_slice)

    known_context = _as_list(native_frame_kwargs.get("known_context"))
    missing_context = _as_list(native_frame_kwargs.get("missing_context"))
    state_sources = _safe_source_labels(_as_mapping(native_frame_kwargs.get("selected_context_bundle")).get("sources_used"))
    known_context_used = [item.get("kind", "context_signal") if isinstance(item, Mapping) else "context_signal" for item in known_context]
    capability_boundary = _as_mapping(native_frame_kwargs.get("capability_boundary_result"))
    signals = _detect_shadow_signals(
        user_message=user_message or "",
        meaning=meaning,
        obligation=obligation,
        known=known_context,
        missing=missing_context,
        evidence_status=evidence_status,
        capability=capability_boundary,
        guardrails=guardrails,
        safe_request_summary=safe_request_summary,
    )

    frontier: Dict[str, Any] = {
        "formation_type": SHADOW_TYPE_V1,
        "runtime_scope": "shadow_only",
        "candidate_count": 0,
        "candidate_families_considered": [],
        "selected_candidate_family": "",
        "candidate_ranking_basis": {
            "basis_type": "internal_shadow_metadata_only",
            "feature_names": RANKING_FEATURES_V1,
            "signals": signals,
            "selected_family": "",
            "priority_reasons": [],
            "strongest_signals": signals.get("strongest_signals", []),
            "suppressed_default_signals": signals.get("suppressed_default_signals", []),
            "guardrail_override_status": "active" if guardrails else "not_active",
            "public_score": False,
            "official_evaluation": False,
            "solver_or_model_authority": False,
            "advisor_authority": False,
            "answer_selection_arbitration": False,
        },
        "state_sources_used": state_sources,
        "known_context_used": sorted(set(str(item) for item in known_context_used)),
        "missing_context": [str(item)[:96] for item in missing_context],
        "memory_boundary": _as_mapping(dry_slice.get("frame", {})).get("memory_boundary_status", {}),
        "capability_boundary": capability_boundary,
        "evidence_status": evidence_status,
        "provenance_refs": _safe_source_labels(native_frame_kwargs.get("provenance_refs")),
        "uncertainty_status": native_frame_kwargs.get("uncertainty_result", {}),
        "relationship_context_used": {
            "signal_available": bool(signals.get("relationship_context")),
            "ranking_signal_used": bool(signals.get("relationship_context")),
            "safe_marker_only": True,
            "raw_text_stored": False,
        },
        "continuity_context_used": {
            "signal_available": bool(signals.get("continuity_context")),
            "ranking_signal_used": bool(signals.get("continuity_context")),
            "safe_marker_only": True,
            "raw_text_stored": False,
        },
        "self_check_status": dry_slice_summary.get("self_check_status") or "not_available",
        "deterministic_guardrails_applied": guardrails,
        "raw_text_stored": False,
        "model_calls": False,
        "advisor_calls": False,
        "solver_execution": False,
        "answer_selection_arbitration": False,
        "safe_to_wire_runtime": False,
        "live_runtime_output": False,
    }

    candidate_previews = _build_candidate_previews(native_frame_kwargs, frontier)
    selected_preview = _select_preview(candidate_previews)
    frontier["candidate_count"] = len(candidate_previews)
    frontier["candidate_families_considered"] = [p["candidate_family"] for p in candidate_previews]
    frontier["selected_candidate_family"] = selected_preview.get("candidate_family", "")
    frontier["candidate_ranking_basis"].update({
        "selected_family": selected_preview.get("candidate_family", ""),
        "priority_reasons": _as_list(selected_preview.get("priority_reasons")),
        "selected_priority_band": _as_mapping(selected_preview.get("ranking_features")).get("priority_band"),
    })

    helper_metadata.update({
        "raw_text_stored": False,
        "model_calls": False,
        "advisor_calls": False,
        "solver_execution": False,
        "answer_selection_arbitration": False,
        "safe_to_wire_runtime": False,
        "live_runtime_output": False,
        "runtime_wiring": False,
        "chat_context_supplied": chat_context is not None,
        "chat_hints_supplied": chat_hints is not None,
        "request_summary_supplied": request_summary is not None,
        "dry_slice_built": True,
    })

    shadow: Dict[str, Any] = {
        "shadow_type": SHADOW_TYPE_V1,
        "schema_version": SCHEMA_VERSION_V1,
        FRONTIER_KEY_V1: frontier,
        "native_frame_kwargs": native_frame_kwargs,
        "helper_metadata": helper_metadata,
        "dry_slice_summary": dry_slice_summary,
        "candidate_previews": candidate_previews,
        "selected_preview": selected_preview,
        "validation": {},
    }
    shadow = to_unified_response_formation_shadow_json_safe_v1(shadow)
    shadow["validation"] = validate_unified_response_formation_shadow_v1(shadow)
    return shadow


def validate_unified_response_formation_shadow_v1(shadow: Any) -> Dict[str, Any]:
    """Validate unified formation shadow safety and usefulness boundaries."""
    safe = to_unified_response_formation_shadow_json_safe_v1(shadow)
    errors: List[Dict[str, str]] = []
    warnings: List[Dict[str, str]] = []

    def add_error(category: str, path: str, message: str) -> None:
        errors.append({"category": category, "path": path or "$", "message": message})

    def add_warning(category: str, path: str, message: str) -> None:
        warnings.append({"category": category, "path": path or "$", "message": message})

    if not isinstance(safe, Mapping):
        add_error("schema", "$", "shadow must be a mapping")
        return {"valid": False, "errors": errors, "warnings": warnings}

    if safe.get("shadow_type") != SHADOW_TYPE_V1:
        add_error("schema", "shadow_type", f"shadow_type must be {SHADOW_TYPE_V1}")
    frontier = _as_mapping(safe.get(FRONTIER_KEY_V1))
    if not frontier:
        add_error("schema", FRONTIER_KEY_V1, "frontier metadata is required")
    else:
        if frontier.get("runtime_scope") != "shadow_only":
            add_error("runtime_wiring", f"{FRONTIER_KEY_V1}.runtime_scope", "runtime scope must remain shadow_only")
        for flag in ("model_calls", "advisor_calls", "solver_execution", "answer_selection_arbitration", "safe_to_wire_runtime", "live_runtime_output"):
            if frontier.get(flag) is True:
                add_error("forbidden_authorization_or_side_effect", f"{FRONTIER_KEY_V1}.{flag}", f"{flag}=true is not allowed")

    for path, value in _walk(safe):
        terminal = path.split(".")[-1].split("[")[0]
        if terminal in FORBIDDEN_KEYS_V1:
            add_error("forbidden_key", path, f"{terminal} must not appear")
        if terminal in TRUE_FORBIDDEN_FLAGS_V1 and value is True:
            add_error("forbidden_authorization_or_side_effect", path, f"{terminal}=true is not allowed")
        if isinstance(value, str):
            lowered = value.lower()
            if "://" in lowered or lowered.startswith("www."):
                add_error("raw_source_url", path, "raw source URLs must not appear")
            guardrail_path = any(segment in path for segment in _SAFE_GUARDRAIL_PATH_SEGMENTS)
            if not guardrail_path:
                for category, markers in FORBIDDEN_TEXT_MARKERS_V1.items():
                    if _contains_any(value, markers):
                        add_error(category, path, "forbidden text marker present")
        elif isinstance(value, Mapping):
            if value.get("authorization_granted") is True:
                add_error("authorization_claim", path, "authorization_granted must remain false")
            if value.get("registry_write") is True or value.get("source_registry_write") is True:
                add_error("source_registry_write", path, "source registry writes are forbidden")

    native_kwargs = _as_mapping(safe.get("native_frame_kwargs"))
    helper_metadata = _as_mapping(safe.get("helper_metadata"))
    candidate_previews = _as_list(safe.get("candidate_previews"))
    selected_preview = _as_mapping(safe.get("selected_preview"))
    dry_summary = _as_mapping(safe.get("dry_slice_summary"))

    reuse_validation = validate_meaning_response_reuse_payload_v1({
        "payload_type": "meaning_response_reuse_native_inputs_v1",
        "native_frame_kwargs": native_kwargs,
        "helper_metadata": helper_metadata,
    })
    if not reuse_validation.get("valid"):
        add_error("meaning_reuse_validation", "native_frame_kwargs", "meaning response reuse payload validation failed")

    if not candidate_previews:
        add_warning("no_candidates", "candidate_previews", "no candidate previews supplied")
    if not frontier.get("known_context_used") and not frontier.get("missing_context"):
        add_warning("no_known_or_missing_context", FRONTIER_KEY_V1, "no known or missing context signal")
    if not frontier.get("relationship_context_used") or not frontier.get("continuity_context_used"):
        add_warning("no_relationship_or_continuity_signal", FRONTIER_KEY_V1, "relationship/continuity signal missing")
    if not frontier.get("evidence_status"):
        add_warning("no_evidence_status", f"{FRONTIER_KEY_V1}.evidence_status", "evidence status missing")
    if not frontier.get("capability_boundary"):
        add_warning("no_capability_boundary", f"{FRONTIER_KEY_V1}.capability_boundary", "capability boundary missing")
    if not frontier.get("self_check_status"):
        add_warning("no_self_check_summary", f"{FRONTIER_KEY_V1}.self_check_status", "self-check status missing")
    if selected_preview and selected_preview.get("eligible") is not True:
        add_warning("selected_candidate_not_eligible", "selected_preview", "selected candidate is not eligible")
    if not dry_summary:
        add_warning("missing_native_dry_slice_summary", "dry_slice_summary", "native dry slice summary missing")
    if not native_kwargs.get("known_context") and not native_kwargs.get("missing_context"):
        add_warning("sparse_state_context_signal", "native_frame_kwargs", "sparse state/context signal")

    ranking_basis = _as_mapping(frontier.get("candidate_ranking_basis"))
    signals = _as_mapping(ranking_basis.get("signals"))
    selected_family = str(frontier.get("selected_candidate_family") or selected_preview.get("candidate_family") or "")
    if selected_family == "capability_honest" and not signals.get("material_capability"):
        add_warning("capability_honest_without_material_signal", f"{FRONTIER_KEY_V1}.selected_candidate_family", "capability_honest selected without material capability signal")
    if signals.get("evidence_used") and selected_family not in {"evidence_provenance", "boundary_first"}:
        add_warning("evidence_used_without_evidence_family", f"{FRONTIER_KEY_V1}.selected_candidate_family", "evidence was used but evidence_provenance/boundary_first was not selected")
    if signals.get("ordinary_task") and selected_family not in {"ordinary_task_plan", "clarification", "boundary_first", "evidence_provenance"}:
        add_warning("ordinary_task_family_not_selected", f"{FRONTIER_KEY_V1}.selected_candidate_family", "ordinary task signal did not select ordinary_task_plan/clarification/boundary_first")
    if helper_metadata.get("request_summary_supplied") is True and not signals.get("request_summary_sanitized_or_structural"):
        add_warning("request_summary_may_be_raw_or_private", "helper_metadata.request_summary_supplied", "request summary was supplied; verify structural sanitization")
    rel_used = _as_mapping(frontier.get("relationship_context_used"))
    cont_used = _as_mapping(frontier.get("continuity_context_used"))
    if signals.get("relationship_context") and not rel_used.get("ranking_signal_used"):
        add_warning("relationship_signal_not_reflected", f"{FRONTIER_KEY_V1}.relationship_context_used", "relationship signal exists but is not reflected in ranking metadata")
    if signals.get("continuity_context") and not cont_used.get("ranking_signal_used"):
        add_warning("continuity_signal_not_reflected", f"{FRONTIER_KEY_V1}.continuity_context_used", "continuity signal exists but is not reflected in ranking metadata")
    selected_band = int(_as_mapping(selected_preview.get("ranking_features")).get("priority_band") or 0) if selected_preview else 0
    stronger = [
        p.get("candidate_family") for p in candidate_previews
        if p.get("eligible") is True and int(_as_mapping(p.get("ranking_features")).get("priority_band") or 0) > selected_band
    ]
    if stronger:
        add_warning("selected_candidate_weaker_than_eligible_alternative", "selected_preview", f"stronger eligible candidate family exists: {sorted(str(x) for x in stronger)[:5]}")
    generic_reasons = {"capability model/boundary metadata present", "ordinary task planning may be useful when not blocked"}
    reasons = {str(p.get("reason")) for p in candidate_previews if isinstance(p, Mapping)}
    if reasons and reasons.issubset(generic_reasons):
        add_warning("generic_candidate_reasons_only", "candidate_previews", "candidate reasons are too generic to support comparison")

    return {"valid": not errors, "errors": errors, "warnings": warnings}


def summarize_unified_response_formation_shadow_v1(shadow: Mapping[str, Any]) -> Dict[str, Any]:
    """Return count/status-only safe inspection summary."""
    safe = to_unified_response_formation_shadow_json_safe_v1(shadow)
    frontier = _as_mapping(safe.get(FRONTIER_KEY_V1))
    validation = _as_mapping(safe.get("validation"))
    dry = _as_mapping(safe.get("dry_slice_summary"))
    return {
        "shadow_type": safe.get("shadow_type"),
        "schema_version": safe.get("schema_version"),
        "runtime_scope": frontier.get("runtime_scope"),
        "candidate_count": frontier.get("candidate_count", 0),
        "selected_candidate_family": frontier.get("selected_candidate_family", ""),
        "guardrail_count": len(_as_list(frontier.get("deterministic_guardrails_applied"))),
        "known_context_count": len(_as_list(frontier.get("known_context_used"))),
        "missing_context_count": len(_as_list(frontier.get("missing_context"))),
        "evidence_status": _as_mapping(frontier.get("evidence_status")).get("status", "not_supplied_not_checked"),
        "self_check_status": frontier.get("self_check_status") or dry.get("self_check_status"),
        "dry_slice_status": dry.get("slice_status"),
        "safe_to_wire_runtime": False,
        "live_runtime_output": False,
        "validation_valid": validation.get("valid"),
        "validation_error_count": len(_as_list(validation.get("errors"))),
        "validation_warning_count": len(_as_list(validation.get("warnings"))),
    }


def render_unified_response_formation_shadow_markdown_v1(shadow: Mapping[str, Any]) -> str:
    """Render safe count/status-only Markdown for shadow inspection."""
    summary = summarize_unified_response_formation_shadow_v1(shadow)
    lines = [
        "# Unified Response Formation Shadow",
        f"- shadow_type:{summary.get('shadow_type')}",
        f"- runtime_scope:{summary.get('runtime_scope')}",
        f"- candidates:{summary.get('candidate_count')}",
        f"- selected_family:{summary.get('selected_candidate_family')}",
        f"- guardrails:{summary.get('guardrail_count')}",
        f"- known_context_count:{summary.get('known_context_count')}",
        f"- missing_context_count:{summary.get('missing_context_count')}",
        f"- evidence_status:{summary.get('evidence_status')}",
        f"- self_check_status:{summary.get('self_check_status')}",
        f"- dry_slice_status:{summary.get('dry_slice_status')}",
        "- safe_to_wire_runtime:false",
        "- live_runtime_output:false",
    ]
    return "\n".join(lines)


__all__ = [
    "SHADOW_TYPE_V1",
    "build_unified_response_formation_shadow_v1",
    "validate_unified_response_formation_shadow_v1",
    "to_unified_response_formation_shadow_json_safe_v1",
    "summarize_unified_response_formation_shadow_v1",
    "render_unified_response_formation_shadow_markdown_v1",
]
