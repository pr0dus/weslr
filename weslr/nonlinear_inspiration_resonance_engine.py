"""Metadata-only Nonlinear Inspiration / Resonance Engine V1.

This module stays deterministic, JSON-safe, fail-closed, and helper-only.
It builds structured resonance metadata for distant-domain analogies without
runtime wiring, provider/model calls, retrieval, persistence, .weslr IO, or
public-claim authority.
"""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from typing import Any, Mapping

import weslr.cognitive_research_protocol as protocol
from weslr.cognitive_research_protocol import (
    build_cognitive_research_run_v1,
    build_default_cognitive_research_denied_authority_v1,
    build_nonlinear_resonance_candidate_v1,
    classify_cognitive_research_engine_family_v1,
    summarize_cognitive_research_run_v1,
    to_cognitive_research_json_safe_v1,
    validate_cognitive_research_run_v1,
)
from weslr.forecast_calibration_bridge import (
    build_forecast_calibration_packet_from_research_run_v1,
    validate_forecast_calibration_record_v1,
)

HELPER_TYPE_V1 = "weslr_nonlinear_inspiration_resonance_engine_v1"
SCHEMA_VERSION_V1 = "nonlinear_inspiration_resonance_engine_v1"
ENGINE_NAME_V1 = "nonlinear_inspiration_engine"
ENGINE_NAME_ALTERNATES_V1 = ("nonlinear_inspiration_engine", "resonance_engine")
ENGINE_FAMILY_V1 = "discovery_generation"

ALLOWED_GAP_TYPES_V1 = (
    "hidden_rule_gap",
    "operator_gap",
    "scale_transition_gap",
    "unification_gap",
    "asymmetry_gap",
    "boundary_condition_gap",
    "translation_gap",
    "proof_gap",
    "formalization_gap",
    "signal_noise_gap",
    "contradiction_tension",
    "unknown",
)
ALLOWED_DOMAIN_DISTANCE_V1 = ("near", "medium", "far", "very_far", "unknown")
ALLOWED_OPERATOR_STATUS_V1 = (
    "raw_inspiration",
    "candidate_operator",
    "toy_model_ready",
    "probe_ready",
    "rejected_false_analogy",
    "needs_translation",
    "unknown",
)
ALLOWED_SCORE_LABELS_V1 = ("none", "low", "medium", "high", "unknown")
ALLOWED_PUBLIC_CLAIM_STATUSES_V1 = (
    "not_public_claim",
    "internal_candidate_only",
    "public_export_blocked",
)
ALLOWED_RESEARCH_MODES_V1 = (
    "internal_exploration",
    "synthetic_test",
    "frontier_mapping",
    "calibration_replay",
)


def _build_safe_denied_authority_v1() -> dict[str, bool]:
    keys = getattr(protocol, "_DENIED_AUTHORITY_KEYS_V1", ())
    if keys:
        return {str(key): False for key in keys}
    return build_default_cognitive_research_denied_authority_v1()


def _build_safe_boundary_status_v1() -> dict[str, Any]:
    return {
        "status": "metadata_only",
        "generator_loop": "RecursiveDiscoveryLoopV1",
        "dialectic_loop": "DialecticGeneratorLoopV1",
        "runtime_wiring_authority": False,
        "chat_responder_authority": False,
        "final_answer_generation_authority": False,
        "public_claim_authority": False,
        "provider_model_call_authority": False,
        "retrieval_tool_authority": False,
        "filesystem_authority": False,
        "network_authority": False,
        "subprocess_authority": False,
        "weslr_io_authority": False,
        "persistence_database_write_authority": False,
        "real_memory_mutation_authority": False,
        "real_project_mutation_authority": False,
        "behavior_pack_promotion_authority": False,
        "autonomous_self_modification_authority": False,
        "official_intelligence_claim_authority": False,
        "public_discovery_claim_authority": False,
        "denied_authority": _build_safe_denied_authority_v1(),
    }

_FORBIDDEN_TEXT_MARKERS_V1 = (
    "raw private text",
    "raw private data",
    "private content",
    "hidden prompt",
    "system prompt",
    "developer prompt",
    "secret",
    "token=",
    ".weslr",
    "runtime wiring",
    "runtime authority",
    "llm authority",
    "llm as authority",
    "provider output",
    "model output",
    "tool authority",
    "tool execution",
    "provider authority",
    "persistence",
    "database write",
    "final answer",
    "reply to user",
    "send to user",
    "public discovery",
    "breakthrough",
    "proof",
    "official intelligence",
    "agi",
    "sentience",
    "consciousness",
    "behavior pack",
    "promotion",
    "autonomous self-modification",
    "memory mutation",
    "project mutation",
    "live ingest",
    "github",
    "rss",
    "lab notebook",
)
_FORBIDDEN_KEY_FRAGMENTS_V1 = (
    "raw_prompt",
    "raw_response",
    "raw_observation",
    "hidden_prompt",
    "private_blob",
    "private_content",
    "secret",
    "password",
    "api_key",
    "provider",
    "model",
    "search",
    "runtime",
    "tool",
    "final_answer",
    "answer_draft",
    "reply_output",
    "preview_output",
    "public_discovery",
    "proof",
    "breakthrough",
    "behavior_pack",
    "promotion",
    "memory_mutation",
    "project_mutation",
    ".weslr",
)


def _compact_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, str):
        text = " ".join(value.split())
        return text if text else default
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    return _compact_text(str(value), default=default)


def _merge_payload(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {}
    if isinstance(payload, Mapping):
        data.update(payload)
    data.update(overrides)
    return data


def _ensure_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, set):
        return sorted(value, key=repr)
    return [value]


def _safe_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "1", "yes", "on"}:
            return True
        if lowered in {"false", "0", "no", "off"}:
            return False
    if value is None:
        return default
    return bool(value)


def _stable_digest(payload: Mapping[str, Any]) -> str:
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True, default=str)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _normalize_choice(value: Any, allowed: tuple[str, ...], default: str) -> str:
    text = _compact_text(value).lower()
    return text if text in allowed else default


def _normalize_score_label(value: Any, default: str = "medium") -> str:
    if isinstance(value, (int, float)):
        numeric = float(value)
        if numeric >= 80.0:
            return "high"
        if numeric >= 55.0:
            return "medium"
        if numeric > 0.0:
            return "low"
        return "none"
    text = _compact_text(value).lower()
    return text if text in ALLOWED_SCORE_LABELS_V1 else default


def _has_forbidden_text(value: Any) -> bool:
    if isinstance(value, Mapping):
        return any(_has_forbidden_text(item) for item in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(_has_forbidden_text(item) for item in value)
    text = _compact_text(value).lower()
    return bool(text) and any(marker in text for marker in _FORBIDDEN_TEXT_MARKERS_V1)


def _collect_text_violations(value: Any) -> list[str]:
    violations: list[str] = []
    if isinstance(value, Mapping):
        for item in value.values():
            violations.extend(_collect_text_violations(item))
        return violations
    if isinstance(value, (list, tuple, set)):
        for item in value:
            violations.extend(_collect_text_violations(item))
        return violations
    if _has_forbidden_text(value):
        violations.append("forbidden_text_marker")
    return violations


def _collect_text_blob(value: Any) -> str:
    blobs: list[str] = []

    def _walk(item: Any) -> None:
        if isinstance(item, Mapping):
            for sub_item in item.values():
                _walk(sub_item)
            return
        if isinstance(item, (list, tuple, set)):
            for sub_item in item:
                _walk(sub_item)
            return
        blobs.append(_compact_text(item).lower())

    _walk(value)
    return "\n".join(blobs)


def _json_safe(value: Any) -> Any:
    if isinstance(value, Mapping):
        safe: dict[str, Any] = {}
        for key, item in value.items():
            key_text = _compact_text(key)
            lowered = key_text.lower()
            if any(fragment in lowered for fragment in _FORBIDDEN_KEY_FRAGMENTS_V1):
                continue
            safe[key_text] = _json_safe(item)
        return safe
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, set):
        return [_json_safe(item) for item in sorted(value, key=repr)]
    if isinstance(value, str):
        lowered = value.lower()
        if any(marker in lowered for marker in _FORBIDDEN_TEXT_MARKERS_V1):
            return "redacted"
        return value
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    return _compact_text(value)


def _append_unique(items: list[str], label: str) -> None:
    if label not in items:
        items.append(label)


def build_resonance_source_gap_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = _merge_payload(payload, **overrides)
    gap_type = _normalize_choice(data.get("gap_type"), ALLOWED_GAP_TYPES_V1, "hidden_rule_gap")
    source_engine_name = _compact_text(data.get("source_engine_name")) or ENGINE_NAME_V1
    source_run_id = _compact_text(data.get("source_run_id")) or f"run-{_stable_digest({'engine': source_engine_name, 'gap': data.get('gap_summary', ''), 'type': gap_type})[:12]}"
    source_gap_id = _compact_text(data.get("source_gap_id")) or f"gap-{_stable_digest({'run': source_run_id, 'gap': data.get('gap_summary', ''), 'type': gap_type})[:12]}"
    gap_summary = _compact_text(data.get("gap_summary")) or "A hidden structural shift remains partly unexplained."
    failure_shape = _compact_text(data.get("failure_shape")) or "The boundary changes shape before the operator can be named."
    known_scope = _compact_text(data.get("known_scope")) or "Visible shape, local steps, and bounded behavior are known."
    failure_scope = _compact_text(data.get("failure_scope")) or "The transfer rule and deeper boundary mechanism remain incomplete."
    uncertainty_factors = _ensure_list(data.get("uncertainty_factors")) or ["hidden structure is only partially visible"]
    invalidation_signals = _ensure_list(data.get("invalidation_signals")) or ["a later probe could break the transfer shape"]
    public_claim_status = _normalize_choice(data.get("public_claim_status"), ALLOWED_PUBLIC_CLAIM_STATUSES_V1, "not_public_claim")
    return _json_safe(
        {
            "source_gap_id": source_gap_id,
            "source_engine_name": source_engine_name,
            "source_run_id": source_run_id,
            "gap_summary": gap_summary,
            "gap_type": gap_type,
            "failure_shape": failure_shape,
            "missing_structure_suspected": _safe_bool(data.get("missing_structure_suspected", True), True),
            "known_scope": known_scope,
            "failure_scope": failure_scope,
            "uncertainty_factors": uncertainty_factors,
            "invalidation_signals": invalidation_signals,
            "public_claim_status": public_claim_status,
        }
    )


def build_resonance_domain_candidate_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = _merge_payload(payload, **overrides)
    domain_label = _compact_text(data.get("domain_label")) or "distant domain"
    domain_id = _compact_text(data.get("domain_id")) or f"domain-{_stable_digest({'label': domain_label, 'distance': data.get('domain_distance', '')})[:12]}"
    domain_distance = _normalize_choice(data.get("domain_distance"), ALLOWED_DOMAIN_DISTANCE_V1, "medium")
    why_relevant = _compact_text(data.get("why_relevant")) or "It shares the same structural pressure without the same surface form."
    surface_difference = _compact_text(data.get("surface_difference")) or "The surface details differ in obvious ways."
    deep_structure_candidate = _compact_text(data.get("deep_structure_candidate")) or "The boundary-shape transfer may be preserved underneath the surface difference."
    risk_of_false_analogy = _compact_text(data.get("risk_of_false_analogy")) or "The analogy may fail if the hidden state does not transfer."
    return _json_safe(
        {
            "domain_id": domain_id,
            "domain_label": domain_label,
            "domain_distance": domain_distance,
            "why_relevant": why_relevant,
            "surface_difference": surface_difference,
            "deep_structure_candidate": deep_structure_candidate,
            "risk_of_false_analogy": risk_of_false_analogy,
        }
    )


def build_structural_match_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = _merge_payload(payload, **overrides)
    source_gap_id = _compact_text(data.get("source_gap_id")) or "gap:unknown"
    resonance_domain = _compact_text(data.get("resonance_domain")) or "domain:unknown"
    match_id = _compact_text(data.get("match_id")) or f"match-{_stable_digest({'gap': source_gap_id, 'domain': resonance_domain})[:12]}"
    shared_structure = _compact_text(data.get("shared_structure")) or "The hidden boundary shape transfers across the gap."
    shared_operator_shape = _compact_text(data.get("shared_operator_shape")) or "A local operator-like transformation keeps the same structure."
    shared_boundary_shape = _compact_text(data.get("shared_boundary_shape")) or "A boundary change appears before the structure becomes explicit."
    shared_failure_mode = _compact_text(data.get("shared_failure_mode")) or "The transfer can break when the boundary shifts too far."
    invariant_candidate = _compact_text(data.get("invariant_candidate")) or "The invariant may be the boundary-shape relation."
    where_mapping_breaks = _compact_text(data.get("where_mapping_breaks")) or "The mapping breaks when the hidden state is not transferable."
    match_confidence = _normalize_score_label(data.get("match_confidence"), "medium")
    match_uncertainty = _normalize_score_label(data.get("match_uncertainty"), "medium")
    return _json_safe(
        {
            "match_id": match_id,
            "source_gap_id": source_gap_id,
            "resonance_domain": resonance_domain,
            "shared_structure": shared_structure,
            "shared_operator_shape": shared_operator_shape,
            "shared_boundary_shape": shared_boundary_shape,
            "shared_failure_mode": shared_failure_mode,
            "invariant_candidate": invariant_candidate,
            "where_mapping_breaks": where_mapping_breaks,
            "match_confidence": match_confidence,
            "match_uncertainty": match_uncertainty,
        }
    )


def build_transferred_operator_candidate_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = _merge_payload(payload, **overrides)
    target_gap = _compact_text(data.get("target_gap")) or "gap:unknown"
    source_domain = _compact_text(data.get("source_domain")) or "domain:unknown"
    operator_label = _compact_text(data.get("operator_label")) or "candidate transfer operator"
    operator_candidate_id = _compact_text(data.get("operator_candidate_id")) or f"operator-{_stable_digest({'label': operator_label, 'source': source_domain, 'target': target_gap})[:12]}"
    input_type = _compact_text(data.get("input_type")) or "structured gap metadata"
    output_type = _compact_text(data.get("output_type")) or "structured candidate metadata"
    transformation_logic = _compact_text(data.get("transformation_logic")) or "Translate the shared structure into a testable operator candidate."
    what_it_might_explain = _compact_text(data.get("what_it_might_explain")) or "It may explain why the same boundary shape reappears across domains."
    where_it_probably_fails = _compact_text(data.get("where_it_probably_fails")) or "It probably fails where the hidden state is not transferable."
    toy_application_summary = _compact_text(data.get("toy_application_summary")) or "A toy application can show the transfer on a small bounded example."
    probe_to_test_usefulness = _compact_text(data.get("probe_to_test_usefulness")) or "Ask whether the operator still works after a controlled boundary shift."
    operator_status = _compact_text(data.get("operator_status")) or "candidate_operator"
    return _json_safe(
        {
            "operator_candidate_id": operator_candidate_id,
            "operator_label": operator_label,
            "source_domain": source_domain,
            "target_gap": target_gap,
            "input_type": input_type,
            "output_type": output_type,
            "transformation_logic": transformation_logic,
            "what_it_might_explain": what_it_might_explain,
            "where_it_probably_fails": where_it_probably_fails,
            "toy_application_summary": toy_application_summary,
            "probe_to_test_usefulness": probe_to_test_usefulness,
            "operator_status": operator_status,
        }
    )


def build_intelligibility_bridge_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = _merge_payload(payload, **overrides)
    bridge_id = _compact_text(data.get("bridge_id")) or f"bridge-{_stable_digest({'source': data.get('source_gap_id', ''), 'operator': data.get('operator_label', '')})[:12]}"
    plain_language_bridge = _compact_text(data.get("plain_language_bridge")) or "In plain language: the same boundary shift appears in a different form."
    formal_sketch = _compact_text(data.get("formal_sketch")) or "A compact structural sketch connects the source gap to the target operator."
    toy_example_summary = _compact_text(data.get("toy_example_summary")) or "A toy example shows the transfer on a small, bounded case."
    minimal_sequence = _ensure_list(data.get("minimal_sequence")) or ["observe", "map", "transfer", "probe"]
    unmapped_terms = _ensure_list(data.get("unmapped_terms"))
    failure_boundary = _compact_text(data.get("failure_boundary")) or "The bridge fails when the hidden structure stops transferring."
    next_probe = _compact_text(data.get("next_probe")) or "Try the same transfer on a smaller bounded example."
    intelligibility_score = _normalize_score_label(data.get("intelligibility_score"), "medium")
    testability_score = _normalize_score_label(data.get("testability_score"), "medium")
    novelty_score = _normalize_score_label(data.get("novelty_score"), "medium")
    new_notation_needed = _safe_bool(data.get("new_notation_needed", False), False)
    return _json_safe(
        {
            "bridge_id": bridge_id,
            "plain_language_bridge": plain_language_bridge,
            "formal_sketch": formal_sketch,
            "toy_example_summary": toy_example_summary,
            "minimal_sequence": minimal_sequence,
            "new_notation_needed": new_notation_needed,
            "unmapped_terms": unmapped_terms,
            "failure_boundary": failure_boundary,
            "next_probe": next_probe,
            "intelligibility_score": intelligibility_score,
            "testability_score": testability_score,
            "novelty_score": novelty_score,
        }
    )


def _validate_source_gap_v1(item: Any, index: int) -> list[str]:
    if not isinstance(item, Mapping):
        return [f"invalid_source_gap:{index}"]
    violations: list[str] = []
    for field in (
        "source_gap_id",
        "source_engine_name",
        "source_run_id",
        "gap_summary",
        "gap_type",
        "failure_shape",
        "known_scope",
        "failure_scope",
        "uncertainty_factors",
        "invalidation_signals",
        "public_claim_status",
    ):
        if field not in item:
            violations.append(f"missing_source_gap_{field}:{index}")
    if not _compact_text(item.get("source_gap_id")):
        violations.append(f"missing_source_gap_id:{index}")
    if not _compact_text(item.get("gap_summary")):
        violations.append(f"missing_source_gap_summary:{index}")
    gap_type = _compact_text(item.get("gap_type")).lower()
    if gap_type not in ALLOWED_GAP_TYPES_V1:
        violations.append(f"invalid_gap_type:{index}")
    if not _compact_text(item.get("failure_shape")):
        violations.append(f"missing_failure_shape:{index}")
    if not _compact_text(item.get("known_scope")):
        violations.append(f"missing_known_scope:{index}")
    if not _compact_text(item.get("failure_scope")):
        violations.append(f"missing_failure_scope:{index}")
    if not _ensure_list(item.get("uncertainty_factors")):
        violations.append(f"missing_uncertainty_factors:{index}")
    if not _ensure_list(item.get("invalidation_signals")):
        violations.append(f"missing_invalidation_signals:{index}")
    if _compact_text(item.get("public_claim_status")).lower() not in ALLOWED_PUBLIC_CLAIM_STATUSES_V1:
        violations.append(f"public_export_marked_safe:{index}")
    if not isinstance(item.get("missing_structure_suspected"), bool):
        violations.append(f"missing_structure_suspected_bool:{index}")
    return violations


def _validate_domain_candidate_v1(item: Any, index: int) -> list[str]:
    if not isinstance(item, Mapping):
        return [f"invalid_domain_candidate:{index}"]
    violations: list[str] = []
    for field in (
        "domain_id",
        "domain_label",
        "domain_distance",
        "why_relevant",
        "surface_difference",
        "deep_structure_candidate",
        "risk_of_false_analogy",
    ):
        if field not in item:
            violations.append(f"missing_domain_candidate_{field}:{index}")
    if not _compact_text(item.get("domain_label")):
        violations.append(f"missing_domain_label:{index}")
    if _compact_text(item.get("domain_distance")).lower() not in ALLOWED_DOMAIN_DISTANCE_V1:
        violations.append(f"invalid_domain_distance:{index}")
    if not _compact_text(item.get("why_relevant")):
        violations.append(f"missing_why_relevant:{index}")
    if not _compact_text(item.get("deep_structure_candidate")):
        violations.append(f"missing_deep_structure_candidate:{index}")
    if not _compact_text(item.get("risk_of_false_analogy")):
        violations.append(f"missing_risk_of_false_analogy:{index}")
    return violations


def _validate_structural_match_v1(item: Any, index: int) -> list[str]:
    if not isinstance(item, Mapping):
        return [f"invalid_structural_match:{index}"]
    violations: list[str] = []
    for field in (
        "match_id",
        "source_gap_id",
        "resonance_domain",
        "shared_structure",
        "shared_operator_shape",
        "shared_boundary_shape",
        "shared_failure_mode",
        "invariant_candidate",
        "where_mapping_breaks",
        "match_confidence",
        "match_uncertainty",
    ):
        if field not in item:
            violations.append(f"missing_structural_match_{field}:{index}")
    if not _compact_text(item.get("shared_structure")) or not _compact_text(item.get("where_mapping_breaks")):
        violations.append(f"missing_structural_match_explanation:{index}")
    if _compact_text(item.get("match_confidence")).lower() not in ALLOWED_SCORE_LABELS_V1:
        violations.append(f"invalid_score_label_match_confidence:{index}")
    if _compact_text(item.get("match_uncertainty")).lower() not in ALLOWED_SCORE_LABELS_V1:
        violations.append(f"invalid_score_label_match_uncertainty:{index}")
    return violations


def _validate_transferred_operator_candidate_v1(item: Any, index: int) -> list[str]:
    if not isinstance(item, Mapping):
        return [f"invalid_transferred_operator_candidate:{index}"]
    violations: list[str] = []
    for field in (
        "operator_candidate_id",
        "operator_label",
        "source_domain",
        "target_gap",
        "input_type",
        "output_type",
        "transformation_logic",
        "what_it_might_explain",
        "where_it_probably_fails",
        "toy_application_summary",
        "probe_to_test_usefulness",
        "operator_status",
    ):
        if field not in item:
            violations.append(f"missing_transferred_operator_candidate_{field}:{index}")
    if not _compact_text(item.get("where_it_probably_fails")):
        violations.append(f"missing_failure_boundary:{index}")
    status = _compact_text(item.get("operator_status")).lower()
    if status not in ALLOWED_OPERATOR_STATUS_V1:
        violations.append(f"invalid_operator_status:{index}")
    if status in {"proven", "true", "verified", "confirmed"}:
        violations.append(f"operator_candidate_marked_proven_or_true:{index}")
    return violations


def _validate_intelligibility_bridge_v1(item: Any, index: int) -> list[str]:
    if not isinstance(item, Mapping):
        return [f"invalid_intelligibility_bridge:{index}"]
    violations: list[str] = []
    for field in (
        "bridge_id",
        "plain_language_bridge",
        "formal_sketch",
        "toy_example_summary",
        "minimal_sequence",
        "new_notation_needed",
        "unmapped_terms",
        "failure_boundary",
        "next_probe",
        "intelligibility_score",
        "testability_score",
        "novelty_score",
    ):
        if field not in item:
            violations.append(f"missing_intelligibility_bridge_{field}:{index}")
    if not _compact_text(item.get("toy_example_summary")):
        violations.append(f"missing_toy_example_summary:{index}")
    if not _compact_text(item.get("failure_boundary")):
        violations.append(f"missing_failure_boundary:{index}")
    for field in ("intelligibility_score", "testability_score", "novelty_score"):
        if _compact_text(item.get(field)).lower() not in ALLOWED_SCORE_LABELS_V1:
            violations.append(f"invalid_score_label:{field}:{index}")
    if not isinstance(item.get("new_notation_needed"), bool):
        violations.append(f"invalid_new_notation_needed:{index}")
    return violations


def _summary_text_for_packet(packet: Mapping[str, Any], blocked: bool, violations: list[str]) -> str:
    if blocked:
        preview = ", ".join(violations[:4])
        return f"Blocked nonlinear inspiration packet: {preview or 'validation failed'}."
    gaps = _ensure_list(packet.get("resonance_source_gaps"))
    domains = _ensure_list(packet.get("resonance_domain_candidates"))
    bridges = _ensure_list(packet.get("intelligibility_bridges"))
    return (
        f"Nonlinear inspiration: {len(gaps)} source gap(s), {len(domains)} domain candidate(s), "
        f"{len(_ensure_list(packet.get('transferred_operator_candidates')))} operator candidate(s), {len(bridges)} bridge(s); "
        f"mode={_compact_text(packet.get('research_mode')) or 'internal_exploration'}."
    )


def build_nonlinear_inspiration_packet_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = _merge_payload(payload, **overrides)
    engine_name = _compact_text(data.get("engine_name")) or ENGINE_NAME_V1
    if engine_name not in ENGINE_NAME_ALTERNATES_V1:
        engine_name = ENGINE_NAME_V1
    engine_family = _compact_text(data.get("engine_family")) or classify_cognitive_research_engine_family_v1(engine_name) or ENGINE_FAMILY_V1
    if not engine_family:
        engine_family = ENGINE_FAMILY_V1
    research_mode = _normalize_choice(data.get("research_mode"), ALLOWED_RESEARCH_MODES_V1, "internal_exploration")
    public_claim_status = _normalize_choice(data.get("public_claim_status"), ALLOWED_PUBLIC_CLAIM_STATUSES_V1, "not_public_claim")
    public_gap_card_status = _normalize_choice(data.get("public_gap_card_status"), ALLOWED_PUBLIC_CLAIM_STATUSES_V1, "public_export_blocked")
    llm_helper_role = _compact_text(data.get("llm_helper_role")) or "resonance_suggestion_helper_only"

    source_gaps = _ensure_list(data.get("resonance_source_gaps"))
    if source_gaps and isinstance(source_gaps[0], Mapping):
        source_gaps = [_json_safe(item) for item in source_gaps]
        source_gap = _json_safe(source_gaps[0])
    else:
        source_gap = build_resonance_source_gap_v1(data)
        source_gaps = [source_gap]

    domain_candidates = _ensure_list(data.get("resonance_domain_candidates"))
    if domain_candidates and isinstance(domain_candidates[0], Mapping):
        domain_candidates = [_json_safe(item) for item in domain_candidates]
        domain_candidate = _json_safe(domain_candidates[0])
    else:
        domain_candidate = build_resonance_domain_candidate_v1(data)
        domain_candidates = [domain_candidate]

    structural_matches = _ensure_list(data.get("structural_matches"))
    if structural_matches and isinstance(structural_matches[0], Mapping):
        structural_matches = [_json_safe(item) for item in structural_matches]
        structural_match = _json_safe(structural_matches[0])
    else:
        structural_match = build_structural_match_v1({"source_gap_id": source_gap["source_gap_id"], "resonance_domain": domain_candidate["domain_id"], **data})
        structural_matches = [structural_match]

    transferred_candidates = _ensure_list(data.get("transferred_operator_candidates"))
    if transferred_candidates and isinstance(transferred_candidates[0], Mapping):
        transferred_candidates = [_json_safe(item) for item in transferred_candidates]
        operator_candidate = _json_safe(transferred_candidates[0])
    else:
        operator_candidate = build_transferred_operator_candidate_v1({"source_domain": domain_candidate["domain_label"], "target_gap": source_gap["source_gap_id"], **data})
        transferred_candidates = [operator_candidate]

    bridges = _ensure_list(data.get("intelligibility_bridges"))
    if bridges and isinstance(bridges[0], Mapping):
        bridges = [_json_safe(item) for item in bridges]
        bridge = _json_safe(bridges[0])
    else:
        bridge = build_intelligibility_bridge_v1(data)
        bridges = [bridge]

    resonance_candidates = _ensure_list(data.get("resonance_candidates"))
    if resonance_candidates:
        resonance_candidates = [_json_safe(item) for item in resonance_candidates]
    else:
        resonance_candidates = [
            build_nonlinear_resonance_candidate_v1({
                "source_gap": source_gap["source_gap_id"],
                "resonance_domain": domain_candidate["domain_label"],
                "shared_structure": structural_match["shared_structure"],
                "transferred_operator_candidate": operator_candidate["operator_label"],
                "intelligibility_bridge": bridge["plain_language_bridge"],
                "toy_example_summary": bridge["toy_example_summary"],
                "where_analogy_breaks": bridge["failure_boundary"],
                "novelty_score": 65.0,
                "intelligibility_score": 70.0,
                "testability_score": 70.0,
                "next_probe": bridge["next_probe"],
            })
        ]

    nonlinear_inspiration_candidates = _ensure_list(data.get("nonlinear_inspiration_candidates"))
    if nonlinear_inspiration_candidates:
        nonlinear_inspiration_candidates = [_json_safe(item) for item in nonlinear_inspiration_candidates]
    else:
        nonlinear_inspiration_candidates = [bridge]

    operator_candidates = _ensure_list(data.get("operator_candidates"))
    if operator_candidates:
        operator_candidates = [_json_safe(item) for item in operator_candidates]
    else:
        operator_candidates = [operator_candidate]

    packet = build_cognitive_research_run_v1(
        {
            "schema_version": data.get("schema_version") or SCHEMA_VERSION_V1,
            "engine_name": engine_name,
            "engine_family": engine_family,
            "research_mode": research_mode,
            "input_artifact_ref": _compact_text(data.get("input_artifact_ref")) or f"artifact:{source_gap['source_gap_id']}",
            "input_artifact_type": _compact_text(data.get("input_artifact_type")) or "gap-card",
            "input_summary": _compact_text(data.get("input_summary")) or source_gap["gap_summary"],
            "source_scope": _compact_text(data.get("source_scope")) or "metadata_only",
            "predictions": _ensure_list(data.get("predictions")) or [f"A later probe may confirm the {source_gap['gap_type']} shape remains bounded."],
            "hypotheses": _ensure_list(data.get("hypotheses")) or [f"The gap may map to a transferable operator shape from {domain_candidate['domain_label']}."] ,
            "probes": _ensure_list(data.get("probes")) or [bridge["next_probe"]],
            "resonance_candidates": resonance_candidates,
            "nonlinear_inspiration_candidates": nonlinear_inspiration_candidates,
            "operator_candidates": operator_candidates,
            "confidence_map": _json_safe(data.get("confidence_map")) if data.get("confidence_map") is not None else {"resonance": "medium", "operator_transfer": "medium"},
            "uncertainty_map": _json_safe(data.get("uncertainty_map")) if data.get("uncertainty_map") is not None else {"false_analogy_risk": "medium", "boundary_shift": "high"},
            "verification_steps": _ensure_list(data.get("verification_steps")) or ["map the gap", "build the bridge", "probe the bridge"],
            "human_verification_steps": _ensure_list(data.get("human_verification_steps")) or ["review the analogy", "confirm the failure boundary"],
            "machine_verification_steps": _ensure_list(data.get("machine_verification_steps")) or ["validate the packet", "check calibration compatibility"],
            "falsification_probes": _ensure_list(data.get("falsification_probes")) or ["try the smallest counterexample", "check where the mapping breaks"],
            "rule_pressure_tests": _ensure_list(data.get("rule_pressure_tests")) or [
                {"pressure_type": "edge_case", "result": "pending", "scope_update": ""},
                {"pressure_type": "counterexample", "result": "pending", "scope_update": ""},
            ],
            "compressed_lesson": _compact_text(data.get("compressed_lesson")) or "Distant resonance is useful only when it becomes a bounded, testable bridge.",
            "next_experiments": _ensure_list(data.get("next_experiments")) or ["build a toy model", "probe the failure boundary"],
            "llm_helper_role": llm_helper_role,
            "public_claim_status": public_claim_status,
            "public_gap_card_status": public_gap_card_status,
            "research_mode": research_mode,
            "denied_authority": _json_safe(data.get("denied_authority")) if isinstance(data.get("denied_authority"), Mapping) else _build_safe_denied_authority_v1(),
            "boundary_status": _build_safe_boundary_status_v1(),
            "safe_metadata": data.get("safe_metadata") if isinstance(data.get("safe_metadata"), Mapping) else {
                "safe": True,
                "metadata_only": True,
                "json_safe": True,
                "non_public": True,
                "no_runtime_wiring": True,
                "no_provider_calls": True,
                "no_tool_execution": True,
                "no_persistence": True,
                "no_memory_mutation": True,
                "no_project_mutation": True,
                "no_behavior_pack_promotion": True,
                "no_final_answer": True,
                "no_public_claims": True,
                "no_weslr_io": True,
                "no_network": True,
                "no_subprocess": True,
            },
        }
    )

    packet.update(
        {
            "resonance_source_gaps": source_gaps,
            "resonance_domain_candidates": domain_candidates,
            "structural_matches": structural_matches,
            "transferred_operator_candidates": transferred_candidates,
            "intelligibility_bridges": bridges,
        }
    )
    packet["research_mode"] = research_mode
    if "denied_authority" in data and data.get("denied_authority") is None:
        packet["denied_authority"] = None
    else:
        merged_denied_authority = _build_safe_denied_authority_v1()
        if isinstance(data.get("denied_authority"), Mapping):
            merged_denied_authority.update(_json_safe(data.get("denied_authority")))
        packet["denied_authority"] = merged_denied_authority
    packet["boundary_status"] = _build_safe_boundary_status_v1()

    packet_for_calibration = deepcopy(packet)
    packet_for_calibration.pop("calibration_record", None)
    calibration_record = data.get("calibration_record")
    if isinstance(calibration_record, Mapping):
        packet["calibration_record"] = _json_safe(calibration_record)
    else:
        packet["calibration_record"] = build_forecast_calibration_packet_from_research_run_v1(
            packet_for_calibration,
            prediction_id=_compact_text(data.get("prediction_id")) or f"prediction-{source_gap['source_gap_id'].replace('gap-', '')}",
            prediction_statement=_ensure_list(packet_for_calibration.get("predictions"))[0] if _ensure_list(packet_for_calibration.get("predictions")) else source_gap["gap_summary"],
            prediction_type=_compact_text(data.get("prediction_type")) or "gap_prediction",
            prediction_scope=_compact_text(data.get("prediction_scope")) or "metadata_only",
            confidence_before=_safe_bool(data.get("confidence_before"), False) and 0.85 or 0.65,
            confidence_after=_safe_bool(data.get("confidence_after"), False) and 0.85 or 0.65,
            confidence_basis=_compact_text(data.get("confidence_basis")) or "resonance metadata and toy probe compatibility",
            uncertainty_factors=_ensure_list(data.get("uncertainty_factors")) or ["false-analogy risk remains bounded"],
            invalidation_signals=_ensure_list(data.get("invalidation_signals")) or ["a later probe may break the transfer"],
            expected_outcome=_compact_text(data.get("expected_outcome")) or bridge["toy_example_summary"],
            observed_outcome=_compact_text(data.get("observed_outcome")),
            outcome_status=_compact_text(data.get("outcome_status")) or "not_observed_yet",
            calibration_result=_compact_text(data.get("calibration_result")) or "not_yet_calibrated",
            error_type=_compact_text(data.get("error_type")) or "none",
            assumptions_used=_ensure_list(data.get("assumptions_used")) or ["the gap shape is transferable in a bounded form"],
            assumptions_failed=_ensure_list(data.get("assumptions_failed")),
            missing_signals=_ensure_list(data.get("missing_signals")),
            conflicting_signals=_ensure_list(data.get("conflicting_signals")),
            correction=_compact_text(data.get("correction")) or "",
            compressed_lesson=_compact_text(data.get("compressed_lesson")) or "Distant resonance is useful only when it becomes a bounded, testable bridge.",
            future_adjustment=_compact_text(data.get("future_adjustment")) or "tighten the analogy before widening the transfer",
            behavior_change_authorized=False,
            memory_mutation_authorized=False,
            project_mutation_authorized=False,
            public_claim_authorized=False,
        )
    packet["calibration_record"]["safe_metadata"] = _json_safe(packet["calibration_record"].get("safe_metadata"))
    return _json_safe(packet)


def validate_nonlinear_inspiration_packet_v1(packet: Any) -> dict[str, Any]:
    base = validate_cognitive_research_run_v1(packet)
    raw = packet if isinstance(packet, Mapping) else {}
    violations: list[str] = []

    if not isinstance(packet, Mapping):
        violations.append("invalid_packet_type")
        return {
            "schema_version": SCHEMA_VERSION_V1,
            "helper_type": HELPER_TYPE_V1,
            "valid": False,
            "blocked": True,
            "violations": violations,
            "violation_count": len(violations),
            "protocol_valid": False,
            "protocol_blocked_labels": [],
            "engine_name": ENGINE_NAME_V1,
            "engine_family": ENGINE_FAMILY_V1,
            "research_mode": "internal_exploration",
            "public_claim_status": "not_public_claim",
            "summary_text": "Blocked nonlinear inspiration packet: invalid packet type.",
        }

    if base.get("blocked"):
        for label in base.get("blocked_labels", []):
            _append_unique(violations, f"protocol:{label}")

    engine_name = _compact_text(raw.get("engine_name"))
    if engine_name not in ENGINE_NAME_ALTERNATES_V1:
        _append_unique(violations, "invalid_engine_name")
    engine_family = _compact_text(raw.get("engine_family"))
    if engine_family != ENGINE_FAMILY_V1:
        _append_unique(violations, "invalid_engine_family")
    research_mode = _compact_text(raw.get("research_mode"))
    if research_mode not in ALLOWED_RESEARCH_MODES_V1:
        _append_unique(violations, "invalid_research_mode")
    public_claim_status = _compact_text(raw.get("public_claim_status"))
    if public_claim_status not in ALLOWED_PUBLIC_CLAIM_STATUSES_V1:
        _append_unique(violations, "public_export_marked_safe")
    if _compact_text(raw.get("public_gap_card_status")) not in ALLOWED_PUBLIC_CLAIM_STATUSES_V1:
        _append_unique(violations, "public_export_marked_safe")

    text_blob = _collect_text_blob(raw)
    if "tool authority" in text_blob and "provider authority" in text_blob and ("runtime authority" in text_blob or "persistence" in text_blob):
        _append_unique(violations, "protocol:runtime_provider_tool_persistence_implication")
    if ".weslr" in text_blob:
        _append_unique(violations, "protocol:dot_weslr_implication")
    if any(marker in text_blob for marker in ("live ingestion", "github", "rss", "lab notebook", "network feed")):
        _append_unique(violations, "protocol:live_ingestion_network_implication")
    if "memory mutation authority" in text_blob:
        _append_unique(violations, "protocol:memory_mutation_authority")
    if "project mutation authority" in text_blob:
        _append_unique(violations, "protocol:project_mutation_authority")
    if "behavior pack promotion" in text_blob:
        _append_unique(violations, "protocol:behavior_pack_promotion_implication")

    source_gaps = _ensure_list(raw.get("resonance_source_gaps"))
    domain_candidates = _ensure_list(raw.get("resonance_domain_candidates"))
    structural_matches = _ensure_list(raw.get("structural_matches"))
    transferred_candidates = _ensure_list(raw.get("transferred_operator_candidates"))
    bridges = _ensure_list(raw.get("intelligibility_bridges"))

    if not source_gaps:
        _append_unique(violations, "missing_resonance_source_gaps")
    for index, item in enumerate(source_gaps):
        violations.extend(_validate_source_gap_v1(item, index))
    if not domain_candidates:
        _append_unique(violations, "missing_resonance_domain_candidates")
    for index, item in enumerate(domain_candidates):
        violations.extend(_validate_domain_candidate_v1(item, index))
    if not structural_matches:
        _append_unique(violations, "missing_structural_matches")
    for index, item in enumerate(structural_matches):
        violations.extend(_validate_structural_match_v1(item, index))
    if not transferred_candidates:
        _append_unique(violations, "missing_transferred_operator_candidates")
    for index, item in enumerate(transferred_candidates):
        violations.extend(_validate_transferred_operator_candidate_v1(item, index))
    if not bridges:
        _append_unique(violations, "missing_intelligibility_bridges")
    for index, item in enumerate(bridges):
        violations.extend(_validate_intelligibility_bridge_v1(item, index))

    for field in (
        "hypotheses",
        "predictions",
        "confidence_map",
        "uncertainty_map",
        "verification_steps",
        "human_verification_steps",
        "machine_verification_steps",
        "falsification_probes",
        "probes",
        "rule_pressure_tests",
        "next_experiments",
    ):
        if not raw.get(field):
            _append_unique(violations, f"missing_{field}")

    calibration_record = raw.get("calibration_record")
    if calibration_record is None:
        _append_unique(violations, "missing_calibration_record")
    else:
        calibration_validation = validate_forecast_calibration_record_v1(calibration_record)
        if not calibration_validation.get("valid", False):
            _append_unique(violations, "invalid_calibration_record")

    violations.extend(_collect_text_violations(raw))
    blocked = bool(violations)
    summary_text = _summary_text_for_packet(raw, blocked, list(dict.fromkeys(violations)))
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "helper_type": HELPER_TYPE_V1,
        "valid": not blocked,
        "blocked": blocked,
        "violations": list(dict.fromkeys(violations)),
        "violation_count": len(list(dict.fromkeys(violations))),
        "protocol_valid": bool(base.get("blocked") is False),
        "protocol_blocked_labels": list(base.get("blocked_labels", [])),
        "engine_name": engine_name or ENGINE_NAME_V1,
        "engine_family": engine_family or ENGINE_FAMILY_V1,
        "research_mode": research_mode or "internal_exploration",
        "public_claim_status": public_claim_status or "not_public_claim",
        "source_gap_count": len(source_gaps),
        "domain_candidate_count": len(domain_candidates),
        "operator_candidate_count": len(transferred_candidates),
        "bridge_count": len(bridges),
        "summary_text": _compact_text(summary_text)[:360],
    }


def summarize_nonlinear_inspiration_packet_v1(packet: Any) -> dict[str, Any]:
    validation = validate_nonlinear_inspiration_packet_v1(packet)
    raw = packet if isinstance(packet, Mapping) else {}
    summary_text = _summary_text_for_packet(raw, validation["blocked"], validation["violations"])
    safe_packet = to_nonlinear_inspiration_json_safe_v1(packet)
    return {
        "schema_version": _compact_text(safe_packet.get("schema_version")) or SCHEMA_VERSION_V1,
        "helper_type": HELPER_TYPE_V1,
        "summary_text": summary_text[:360],
        "valid": validation["valid"],
        "violations": validation["violations"],
        "violation_count": validation["violation_count"],
        "engine_name": validation["engine_name"],
        "engine_family": validation["engine_family"],
        "research_mode": validation["research_mode"],
        "public_claim_status": validation["public_claim_status"],
        "packet": safe_packet,
    }


def to_nonlinear_inspiration_json_safe_v1(packet: Any) -> dict[str, Any]:
    safe = to_cognitive_research_json_safe_v1(packet)
    return _json_safe(safe)


def build_initial_nonlinear_inspiration_examples_v1() -> list[dict[str, Any]]:
    examples: list[dict[str, Any]] = []
    specs = [
        {
            "engine_name": "nonlinear_inspiration_engine",
            "research_mode": "internal_exploration",
            "input_artifact_ref": "artifact:nonlinear-inspiration-hidden-rule-001",
            "input_summary": "Hidden-rule gap with a bounded transfer candidate.",
            "gap_type": "hidden_rule_gap",
            "gap_summary": "A hidden rule seems to steer the boundary but remains partially unseen.",
            "why_relevant": "The same boundary pressure can appear in another domain.",
            "operator_label": "hidden-rule transfer operator",
            "plain_language_bridge": "A small change in hidden structure can explain the repeated boundary shape.",
            "toy_example_summary": "A toy example uses two small states and a bounded boundary shift.",
            "next_probe": "Try the transfer on the smallest possible boundary shift.",
        },
        {
            "engine_name": "resonance_engine",
            "research_mode": "synthetic_test",
            "input_artifact_ref": "artifact:nonlinear-inspiration-scale-transition-001",
            "input_summary": "Scale-transition gap with a compact operator bridge.",
            "gap_type": "scale_transition_gap",
            "gap_summary": "The same operator shape appears to survive only after a scale shift.",
            "why_relevant": "A scale change may preserve the deeper operator relation.",
            "operator_label": "scale-transfer operator",
            "plain_language_bridge": "The pattern stays intelligible when scaled down to a toy example.",
            "toy_example_summary": "A toy example shows the same operator working at two scales.",
            "next_probe": "Compare the small-scale and mid-scale transfer directly.",
        },
        {
            "engine_name": "nonlinear_inspiration_engine",
            "research_mode": "frontier_mapping",
            "input_artifact_ref": "artifact:nonlinear-inspiration-translation-001",
            "input_summary": "Translation gap from a strange symbolic form to a plain bridge.",
            "gap_type": "translation_gap",
            "gap_summary": "The structure is visible, but the plain-language bridge is missing.",
            "why_relevant": "A distant linguistic form may share the same structural transfer.",
            "operator_label": "translation bridge operator",
            "plain_language_bridge": "The same structure can be translated into a short, plain operator story.",
            "toy_example_summary": "A toy example maps one symbolic sentence into a simpler sequence.",
            "next_probe": "Try the translation on one shorter sequence.",
        },
        {
            "engine_name": "resonance_engine",
            "research_mode": "calibration_replay",
            "input_artifact_ref": "artifact:nonlinear-inspiration-signal-noise-001",
            "input_summary": "Signal/noise gap where a weak structure survives inside noise.",
            "gap_type": "signal_noise_gap",
            "gap_summary": "A weak structure keeps repeating even as noise grows.",
            "why_relevant": "Noise can hide the same structural shape that a different domain reveals.",
            "operator_label": "signal-noise separation operator",
            "plain_language_bridge": "The bridge survives when the weak structure is separated from the noise first.",
            "toy_example_summary": "A toy example separates one weak repeating line from noisy context.",
            "next_probe": "Check whether the same bridge works after noise is increased slightly.",
        },
    ]
    for spec in specs:
        examples.append(build_nonlinear_inspiration_packet_v1(spec))
    return examples


__all__ = [
    "HELPER_TYPE_V1",
    "SCHEMA_VERSION_V1",
    "ENGINE_NAME_V1",
    "ENGINE_FAMILY_V1",
    "ALLOWED_GAP_TYPES_V1",
    "ALLOWED_DOMAIN_DISTANCE_V1",
    "ALLOWED_OPERATOR_STATUS_V1",
    "build_resonance_source_gap_v1",
    "build_resonance_domain_candidate_v1",
    "build_structural_match_v1",
    "build_transferred_operator_candidate_v1",
    "build_intelligibility_bridge_v1",
    "build_nonlinear_inspiration_packet_v1",
    "validate_nonlinear_inspiration_packet_v1",
    "summarize_nonlinear_inspiration_packet_v1",
    "to_nonlinear_inspiration_json_safe_v1",
    "build_initial_nonlinear_inspiration_examples_v1",
]
