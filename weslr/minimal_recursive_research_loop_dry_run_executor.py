"""Minimal recursive research loop dry-run executor V1.

Deterministic, in-memory integration across the existing WESLR research helpers.
This stays metadata-only: no providers, no retrieval, no persistence, no
runtime wiring, and no public claims.
"""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from typing import Any, Mapping

import weslr.cognitive_research_protocol as protocol
from weslr.dialectic_generator_loop import (
    _default_boundary_status as _dialectic_default_boundary_status,
    _default_safe_metadata as _dialectic_default_safe_metadata,
    build_dialectic_loop_packet_v1,
    build_dialectic_seed_candidate_v1,
    summarize_dialectic_loop_packet_v1,
    validate_dialectic_loop_packet_v1,
)
from weslr.forecast_calibration_bridge import (
    build_forecast_calibration_packet_from_research_run_v1,
    build_forecast_calibration_record_v1,
    summarize_forecast_calibration_record_v1,
    validate_forecast_calibration_record_v1,
)
from weslr.nonlinear_inspiration_resonance_engine import (
    _build_safe_boundary_status_v1,
    build_nonlinear_inspiration_packet_v1,
    build_resonance_source_gap_v1,
    summarize_nonlinear_inspiration_packet_v1,
    validate_nonlinear_inspiration_packet_v1,
)
from weslr.perspicuity_scorer import (
    _default_boundary_status as _perspicuity_default_boundary_status,
    _default_safe_metadata as _perspicuity_default_safe_metadata,
    build_perspicuity_candidate_v1,
    build_perspicuity_packet_v1,
    summarize_perspicuity_packet_v1,
    validate_perspicuity_packet_v1,
)
from weslr.raw_signal_cartographer import (
    build_raw_signal_cartography_packet_v1,
    summarize_raw_signal_cartography_packet_v1,
    validate_raw_signal_cartography_packet_v1,
)
from weslr.rule_pressure_engine import (
    build_rule_pressure_packet_v1,
    build_rule_pressure_target_v1,
    summarize_rule_pressure_packet_v1,
    validate_rule_pressure_packet_v1,
)
from weslr.suggestion_store_update_packet import (
    build_suggestion_store_candidate_ref_v1,
    build_suggestion_store_update_action_v1,
    build_suggestion_store_update_packet_v1,
    summarize_suggestion_store_update_packet_v1,
    validate_suggestion_store_update_packet_v1,
)
from weslr.unintelligible_output_analyzer import (
    build_unintelligible_output_analysis_packet_v1,
    summarize_unintelligible_output_analysis_packet_v1,
    validate_unintelligible_output_analysis_packet_v1,
)
from weslr.unknown_engine_adapter import (
    build_unknown_engine_research_run_v1,
    summarize_unknown_engine_research_run_v1,
    validate_unknown_engine_research_run_v1,
)

SCHEMA_VERSION_V1 = "minimal_recursive_research_loop_dry_run_executor_v1"
ALLOWED_NEXT_INTERNAL_STEPS_V1 = (
    "watch",
    "probe",
    "pressure_test",
    "calibrate",
    "generate_counter_signal",
    "archive",
    "blocked",
    "operator_review",
)
_FORBIDDEN_TEXT_MARKERS_V1 = (
    "hidden prompt",
    "system prompt",
    "private text",
    "secret",
    "api key",
    "provider call",
    "tool execution",
    ".weslr",
    "final answer authority",
    "final-answer",
    "public breakthrough",
    "agi",
    "sentience",
    "consciousness",
)
_REQUIRED_RESULT_FIELDS_V1 = (
    "schema_version",
    "loop_run_id",
    "input_signal",
    "raw_signal_cartography",
    "unintelligible_output_analysis",
    "unknown_engine_run",
    "nonlinear_inspiration_run",
    "rule_pressure_run",
    "dialectic_generator_run",
    "perspicuity_score_run",
    "suggestion_store_update_packet",
    "calibration_bridge_record",
    "final_loop_summary",
    "recommended_next_internal_step",
    "blocked_actions",
    "operator_review_required",
    "runtime_action_authorized",
    "storage_write_authorized",
    "memory_mutation_authorized",
    "project_mutation_authorized",
    "behavior_promotion_authorized",
    "public_claim_authorized",
    "denied_authority",
    "safe_metadata",
)


def _merge_payload(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    if isinstance(payload, Mapping):
        merged.update(payload)
    merged.update({k: v for k, v in overrides.items() if v is not None})
    return merged


def _compact_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _stable_digest(payload: Any) -> str:
    return sha256(repr(payload).encode("utf-8")).hexdigest()


def _json_safe(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, set):
        return [_json_safe(item) for item in sorted(value, key=repr)]
    if isinstance(value, str):
        lowered = value.lower()
        if any(marker in lowered for marker in _FORBIDDEN_TEXT_MARKERS_V1):
            return "[redacted]"
    return deepcopy(value)


def _default_denied_authority() -> dict[str, Any]:
    denied = protocol.build_default_cognitive_research_denied_authority_v1()
    denied = deepcopy(denied) if isinstance(denied, Mapping) else {}
    denied.setdefault("status", "metadata_only")
    denied.setdefault("boundary_notes", "dry-run executor: no runtime, persistence, or public-export authority")
    return denied


def _full_denied_authority() -> dict[str, Any]:
    denied_keys = getattr(protocol, "_DENIED_AUTHORITY_KEYS_V1", ())
    return {str(key): False for key in denied_keys}


def _default_safe_metadata() -> dict[str, Any]:
    return {
        "safe": True,
        "metadata_only": True,
        "json_safe": True,
        "non_public": True,
        "no_runtime_wiring": True,
        "no_provider_calls": True,
        "no_tool_execution": True,
        "no_retrieval": True,
        "no_persistence": True,
        "no_memory_mutation": True,
        "no_project_mutation": True,
        "no_behavior_promotion": True,
        "no_public_claim": True,
        "no_final_answer_authority": True,
        "no_live_ingestion": True,
        "no_weslr_io": True,
        "no_weslr_runtime": True,
        "no_hidden_prompt_leak": True,
        "no_secrets": True,
    }


def _contains_forbidden_text(value: Any) -> bool:
    if isinstance(value, Mapping):
        return any(_contains_forbidden_text(item) for item in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(_contains_forbidden_text(item) for item in value)
    if not isinstance(value, str):
        return False
    lowered = value.lower()
    return any(marker in lowered for marker in _FORBIDDEN_TEXT_MARKERS_V1)


def _extract_stage_issues(validation: Any) -> list[str]:
    if not isinstance(validation, Mapping):
        return ["invalid_validation_result"]
    issues: list[str] = []
    for key in ("blocked_labels", "violations", "blocked", "protocol_blocked_labels"):
        value = validation.get(key)
        if isinstance(value, list):
            issues.extend(_compact_text(item) for item in value if _compact_text(item))
    if validation.get("valid") is False and not issues:
        issues.append("invalid_stage_packet")
    if validation.get("blocked") is True and not issues:
        issues.append("blocked_stage_packet")
    return issues


def _record_stage_failure(stage_name: str, issues: list[str], packet: Any = None) -> dict[str, Any]:
    return {
        "stage_name": stage_name,
        "valid": False,
        "blocked": True,
        "issues": list(dict.fromkeys(_compact_text(issue) for issue in issues if _compact_text(issue))),
        "packet": _json_safe(packet) if packet is not None else None,
    }


def _stage_summary(stage_packet: Mapping[str, Any], summary_fn) -> str:
    try:
        summary = summary_fn(stage_packet)
    except Exception:
        summary = ""
    if isinstance(summary, Mapping):
        for key in ("summary_text", "summary", "text"):
            text = _compact_text(summary.get(key))
            if text:
                return text
        return _compact_text(summary)
    return _compact_text(summary)


def _normalize_next_step(*, blocked_actions: list[str], perspicuity_packet: Mapping[str, Any] | None, suggestion_packet: Mapping[str, Any] | None, rule_pressure_packet: Mapping[str, Any] | None) -> str:
    if blocked_actions:
        return "blocked"

    recommendation = ""
    if isinstance(perspicuity_packet, Mapping):
        scorecard = perspicuity_packet.get("perspicuity_scorecard")
        if isinstance(scorecard, Mapping):
            recommendation = _compact_text(scorecard.get("overall_priority"))
            if recommendation in ALLOWED_NEXT_INTERNAL_STEPS_V1:
                return recommendation
            next_action = _compact_text(scorecard.get("recommended_next_action"))
            if next_action in ALLOWED_NEXT_INTERNAL_STEPS_V1:
                return next_action

    if isinstance(suggestion_packet, Mapping):
        actions = suggestion_packet.get("update_actions")
        if isinstance(actions, list) and actions:
            action_type = _compact_text(actions[0].get("action_type"))
            if action_type == "recommend_next_internal_step":
                return "probe"
            if action_type in ALLOWED_NEXT_INTERNAL_STEPS_V1:
                return action_type

    if isinstance(rule_pressure_packet, Mapping):
        status = _compact_text(rule_pressure_packet.get("result_status"))
        if status in {"failed_pressure", "contradicted"}:
            return "operator_review"
        if status in {"survived_pressure", "partially_survived"}:
            return "pressure_test"

    return "probe"


def build_minimal_loop_input_signal_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = _merge_payload(payload, **overrides)
    signal_summary = _compact_text(
        data.get("signal_summary")
        or data.get("input_summary")
        or "Synthetic metadata-only signal with repeated boundary markers and a narrow update proposal."
    )
    signal_id = _compact_text(data.get("signal_id")) or f"signal:{_stable_digest({'summary': signal_summary})[:12]}"
    signal = {
        "signal_id": signal_id,
        "signal_type": _compact_text(data.get("signal_type") or "synthetic_recursive_research_seed"),
        "signal_origin": _compact_text(data.get("signal_origin") or "metadata_only"),
        "signal_summary": signal_summary,
        "source_ref": _compact_text(data.get("source_ref") or "synthetic:minimal-recursive-loop"),
        "trust_level": _compact_text(data.get("trust_level") or "bounded"),
        "poison_risk": _compact_text(data.get("poison_risk") or "low"),
        "injection_risk": _compact_text(data.get("injection_risk") or "low"),
        "raw_content_included": bool(data.get("raw_content_included", False)),
        "raw_content_ref_only": bool(data.get("raw_content_ref_only", True)),
        "normalization_required": bool(data.get("normalization_required", True)),
        "public_claim_status": _compact_text(data.get("public_claim_status") or "internal_candidate_only"),
        "public_gap_card_status": _compact_text(data.get("public_gap_card_status") or "public_export_blocked"),
        "safe_metadata": _json_safe(data.get("safe_metadata") or _default_safe_metadata()),
        "denied_authority": _json_safe(data.get("denied_authority") or _default_denied_authority()),
    }
    return _json_safe(signal)


def _build_raw_signal_stage(input_signal: Mapping[str, Any]) -> dict[str, Any]:
    packet = build_raw_signal_cartography_packet_v1(
        {
            "input_artifact_ref": input_signal["signal_id"],
            "input_summary": input_signal["signal_summary"],
            "research_mode": "synthetic_test",
            "source_scope": "artifact_summary_only",
            "public_claim_status": "internal_candidate_only",
            "public_gap_card_status": "public_export_blocked",
            "llm_helper_role": "candidate_generator_only",
            "safe_metadata": _default_safe_metadata(),
            "denied_authority": _default_denied_authority(),
            "signal_hypotheses": [
                {
                    "hypothesis_id": "signal-h1",
                    "claim": "Repeated boundary markers may preserve a weak grammar.",
                    "evidence": ["::"],
                    "confidence": 71.0,
                }
            ],
            "next_probes": [
                {
                    "probe_id": "probe-rsc-001",
                    "probe": "Check whether the repeated boundary markers survive normalization.",
                    "purpose": "repeat-preserving structure",
                }
            ],
        }
    )
    return packet


def _build_uoa_stage(raw_signal: Mapping[str, Any]) -> dict[str, Any]:
    summary_text = _stage_summary(raw_signal, summarize_raw_signal_cartography_packet_v1) or _compact_text(raw_signal.get("input_summary"))
    packet = build_unintelligible_output_analysis_packet_v1(
        {
            "input_category": "synthetic symbolic stream",
            "artifact_reference": f"artifact:uoa:{_compact_text(raw_signal.get('run_id') or raw_signal.get('input_artifact_ref') or 'loop')}",
            "artifact_summary": summary_text,
            "source_boundary_engine_name": "UNINTELLIGIBLE_OUTPUT_ANALYZER",
            "candidate_translation_layers": ["layer-a", "layer-b"],
            "unmapped_token_metadata": [
                {"token": "??", "status": "unmapped", "note": "unknown token preserved"},
                {"token": "<gap>", "status": "preserved", "note": "structure retained"},
            ],
            "competing_interpretation_map": {
                "reading_a": "preserve the repeated boundary layer",
                "reading_b": "preserve the rival notation layer",
            },
            "ambiguity_map": {"meaning": "open", "confidence": "bounded", "translation": "plural"},
            "semantic_fracture_labels": ["translation fracture", "meaning split"],
            "syntax_like_structure_labels": ["parse-like run", "phrase-like cluster"],
            "required_new_notation_notes": ["keep alternative notation for repeated unknown tokens"],
            "confidence_uncertainty_map": {"interpretation": "low", "translation": "mixed", "fracture": "tracked"},
            "translation_probes": ["propose layer A", "compare layer B"],
            "meaning_preservation_probes": ["retain token order", "preserve unknown symbols"],
            "invalidated_interpretations": ["plural readings retained"],
            "next_interpretation_experiments": ["try a new notation", "compare contradiction surface"],
            "relationship_to_raw_signal_cartographer": "downstream metadata-only translation review",
            "relationship_to_cognitive_research_run": "bounded internal translation helper only",
            "public_claim_status": "internal_candidate_only",
            "safe_metadata": _default_safe_metadata(),
            "denied_authority": _default_denied_authority(),
        }
    )
    return packet


def _build_unknown_engine_stage(uoa_packet: Mapping[str, Any], raw_signal: Mapping[str, Any]) -> dict[str, Any]:
    summary_text = _stage_summary(uoa_packet, summarize_unintelligible_output_analysis_packet_v1) or _compact_text(uoa_packet.get("artifact_summary"))
    packet = build_unknown_engine_research_run_v1(
        {
            "world_family": "symbolic_sequence",
            "world_id": f"world:minimal-loop:{_stable_digest({'uoa': summary_text})[:12]}",
            "research_mode": "calibration_replay",
            "input_artifact_ref": f"artifact:unknown-engine:{_compact_text(raw_signal.get('input_artifact_ref') or 'loop')}",
            "input_summary": summary_text,
            "public_claim_status": "not_public_claim",
            "safe_metadata": _default_safe_metadata(),
            "denied_authority": _default_denied_authority(),
        }
    )
    return packet


def _build_nonlinear_stage(unknown_engine_run: Mapping[str, Any], uoa_packet: Mapping[str, Any]) -> dict[str, Any]:
    summary_text = _stage_summary(unknown_engine_run, summarize_unknown_engine_research_run_v1) or _compact_text(uoa_packet.get("artifact_summary"))
    source_gap = build_resonance_source_gap_v1(
        {
            "gap_type": "hidden_rule_gap",
            "gap_summary": "A hidden-rule bridge may explain the repeated boundary shape.",
            "why_relevant": "The same boundary pressure may appear in another domain.",
            "operator_label": "transfer operator",
            "plain_language_bridge": "A small change in hidden structure can explain the repeated boundary shape.",
            "toy_example_summary": "A toy example keeps the structure but strips raw content.",
            "next_probe": "Try the smallest transferable bridge.",
            "input_artifact_ref": _compact_text(unknown_engine_run.get("run_id") or "unknown-run"),
            "input_summary": summary_text,
        }
    )
    payload = {
        "engine_name": "nonlinear_inspiration_engine",
        "research_mode": "internal_exploration",
        "input_artifact_ref": _compact_text(unknown_engine_run.get("run_id") or "unknown-run"),
        "input_artifact_type": "gap-card",
        "input_summary": summary_text,
        "resonance_source_gaps": [source_gap],
        "public_claim_status": "not_public_claim",
        "public_gap_card_status": "public_export_blocked",
        "llm_helper_role": "resonance_suggestion_helper_only",
        "denied_authority": protocol.build_default_cognitive_research_denied_authority_v1(),
        "safe_metadata": {
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
    packet = build_nonlinear_inspiration_packet_v1(payload)
    for key in (
        "input_summary",
        "resonance_source_gaps",
        "safe_metadata",
        "public_claim_status",
        "public_gap_card_status",
    ):
        if key in payload:
            packet[key] = deepcopy(payload[key])
    packet["research_mode"] = payload.get("research_mode", "internal_exploration")
    denied_keys = getattr(protocol, "_DENIED_AUTHORITY_KEYS_V1", ())
    packet["denied_authority"] = {str(key): False for key in denied_keys}
    packet["boundary_status"] = _build_safe_boundary_status_v1()
    packet["calibration_record"] = build_forecast_calibration_packet_from_research_run_v1(
        deepcopy(packet),
        uncertainty_factors=["boundary risk remains unconfirmed"],
        invalidation_signals=["a later probe may break the transfer"],
        compressed_lesson="Distant resonance is useful only when it becomes a bounded, testable bridge.",
        future_adjustment="tighten the analogy before widening the transfer",
    )
    return packet


def _build_rule_pressure_stage(nonlinear_packet: Mapping[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    summary_text = _stage_summary(nonlinear_packet, summarize_nonlinear_inspiration_packet_v1) or _compact_text(nonlinear_packet.get("input_summary"))
    target = build_rule_pressure_target_v1(
        {
            "source_engine_name": "nonlinear_inspiration_engine",
            "source_run_id": _compact_text(nonlinear_packet.get("run_id") or "nonlinear-run"),
            "target_type": "operator_candidate",
            "target_summary": summary_text,
            "candidate_rule_or_operator": "transfer operator",
            "claimed_scope": "bounded operator transfer",
            "known_scope": "metadata-only scope",
            "uncertainty_factors": ["candidate remains provisional"],
            "invalidation_signals": ["not yet invalidated"],
            "public_claim_status": "not_public_claim",
        }
    )
    packet = build_rule_pressure_packet_v1(
        {
            "source_engine_name": "nonlinear_inspiration_engine",
            "source_run_id": _compact_text(nonlinear_packet.get("run_id") or "nonlinear-run"),
            "target": target,
            "pressure_type": "counterexample_search",
            "pressure_summary": "Check whether the transferred operator survives a small counterexample.",
            "input_mutation": "metadata-only counterexample probe",
            "expected_failure_mode": "scope_failure",
            "result_status": "not_observed_yet",
            "public_claim_status": "not_public_claim",
            "public_gap_card_status": "public_export_blocked",
            "safe_metadata": _default_safe_metadata(),
            "denied_authority": _default_denied_authority(),
        }
    )
    return packet, target


def _build_dialectic_stage(rule_pressure_packet: Mapping[str, Any], rule_pressure_target: Mapping[str, Any]) -> dict[str, Any]:
    summary_text = _stage_summary(rule_pressure_packet, summarize_rule_pressure_packet_v1) or _compact_text(rule_pressure_packet.get("input_summary"))
    seed = build_dialectic_seed_candidate_v1(
        {
            "seed_id": f"seed-{_stable_digest({'rule_pressure': summary_text})[:12]}",
            "source_engine_name": _compact_text(rule_pressure_packet.get("engine_name") or rule_pressure_packet.get("source_engine_name") or "rule_pressure_engine"),
            "source_run_id": _compact_text(rule_pressure_packet.get("run_id") or "rule-pressure-run"),
            "seed_type": "operator_candidate",
            "seed_summary": summary_text,
            "candidate_claim_or_operator": _compact_text(rule_pressure_target.get("candidate_rule_or_operator") or "transfer operator"),
            "known_scope": _compact_text(rule_pressure_target.get("known_scope") or "metadata-only scope"),
            "failure_scope": _compact_text(rule_pressure_target.get("claimed_scope") or "bounded failure scope"),
            "uncertainty_factors": ["candidate remains provisional"],
            "invalidation_signals": ["not yet invalidated"],
            "public_claim_status": "internal_candidate_only",
        }
    )
    packet = build_dialectic_loop_packet_v1(
        {
            "engine_name": "dialectic_generator_loop",
            "research_mode": "internal_exploration",
            "input_artifact_ref": _compact_text(rule_pressure_packet.get("run_id") or "rule-pressure-run"),
            "input_artifact_type": "dialectic-loop-bundle",
            "input_summary": "Metadata-only dialectic candidate loop.",
            "source_engine_name": _compact_text(rule_pressure_packet.get("engine_name") or rule_pressure_packet.get("source_engine_name") or "rule_pressure_engine"),
            "source_run_id": _compact_text(rule_pressure_packet.get("run_id") or "rule-pressure-run"),
            "seed_type": "operator_candidate",
            "seed_summary": "Metadata-only dialectic candidate loop.",
            "candidate_claim_or_operator": _compact_text(rule_pressure_target.get("candidate_rule_or_operator") or "transfer operator"),
            "known_scope": _compact_text(rule_pressure_target.get("known_scope") or "metadata-only scope"),
            "failure_scope": _compact_text(rule_pressure_target.get("claimed_scope") or "bounded failure scope"),
            "uncertainty_factors": ["candidate remains provisional"],
            "invalidation_signals": ["not yet invalidated"],
            "public_claim_status": "internal_candidate_only",
            "public_gap_card_status": "public_export_blocked",
            "llm_helper_role": "candidate_generator_only",
            "dialectic_seed_candidates": [seed],
        }
    )
    packet["safe_metadata"] = _dialectic_default_safe_metadata("dialectic_generator_loop", "recursive_generation", "internal_exploration")
    packet["boundary_status"] = _dialectic_default_boundary_status()
    packet["denied_authority"] = _full_denied_authority()
    packet["calibration_record"] = build_forecast_calibration_packet_from_research_run_v1(
        deepcopy(packet),
        uncertainty_factors=["boundary risk remains unconfirmed"],
        invalidation_signals=["a later probe may break the transfer"],
        compressed_lesson="Distant resonance is useful only when it becomes a bounded, testable bridge.",
        future_adjustment="tighten the analogy before widening the transfer",
    )
    return packet


def _build_perspicuity_stage(dialectic_packet: Mapping[str, Any], rule_pressure_packet: Mapping[str, Any]) -> dict[str, Any]:
    primary_seed = (dialectic_packet.get("dialectic_seed_candidates") or [{}])[0]
    candidate = build_perspicuity_candidate_v1(
        {
            "source_engine_name": _compact_text(dialectic_packet.get("engine_name") or "dialectic_generator_loop"),
            "source_run_id": _compact_text(dialectic_packet.get("run_id") or "dialectic-run"),
            "candidate_type": _compact_text(primary_seed.get("seed_type") or "dialectic_turn"),
            "candidate_summary": "Metadata-only dialectic turn candidate.",
            "candidate_scope": _compact_text(primary_seed.get("known_scope") or "metadata-only scope"),
            "known_scope": _compact_text(primary_seed.get("known_scope") or "metadata-only scope"),
            "failure_scope": _compact_text(primary_seed.get("failure_scope") or "bounded failure scope"),
            "uncertainty_factors": ["candidate remains provisional"],
            "invalidation_signals": ["not yet invalidated"],
            "public_claim_status": "internal_candidate_only",
        }
    )
    packet = build_perspicuity_packet_v1(
        {
            "engine_name": "perspicuity_scorer",
            "engine_family": "candidate_ranking",
            "research_mode": "internal_exploration",
            "input_artifact_ref": _compact_text(dialectic_packet.get("run_id") or "dialectic-run"),
            "input_artifact_type": "candidate",
            "input_summary": "Metadata-only dialectic candidate loop.",
            "source_engine_name": _compact_text(dialectic_packet.get("engine_name") or "dialectic_generator_loop"),
            "source_run_id": _compact_text(dialectic_packet.get("run_id") or "dialectic-run"),
            "candidate_type": _compact_text(primary_seed.get("seed_type") or "dialectic_turn"),
            "candidate_summary": "Metadata-only dialectic turn candidate.",
            "candidate_scope": _compact_text(primary_seed.get("known_scope") or "metadata-only scope"),
            "known_scope": _compact_text(primary_seed.get("known_scope") or "metadata-only scope"),
            "failure_scope": _compact_text(primary_seed.get("failure_scope") or "bounded failure scope"),
            "uncertainty_factors": ["candidate remains provisional"],
            "invalidation_signals": ["not yet invalidated"],
            "public_claim_status": "internal_candidate_only",
            "public_gap_card_status": "public_export_blocked",
            "llm_helper_role": "candidate_generator_only",
            "non_actionable_research_only": True,
            "simulation_before_real_world": True,
            "safe_metadata": {"safe": True, "metadata_only": True, "perspicuity_is_not_a_gate": True},
            "perspicuity_candidates": [candidate],
        }
    )
    packet["safe_metadata"] = _perspicuity_default_safe_metadata("perspicuity_scorer", "candidate_ranking", "internal_exploration")
    packet["boundary_status"] = _perspicuity_default_boundary_status()
    packet["denied_authority"] = _full_denied_authority()
    return packet


def _build_suggestion_stage(perspicuity_packet: Mapping[str, Any], dialectic_packet: Mapping[str, Any]) -> dict[str, Any]:
    scorecard = perspicuity_packet.get("perspicuity_scorecard") if isinstance(perspicuity_packet, Mapping) else {}
    primary_candidate = (perspicuity_packet.get("perspicuity_candidates") or [{}])[0] if isinstance(perspicuity_packet, Mapping) else {}
    recommended_step = _compact_text(scorecard.get("overall_priority") if isinstance(scorecard, Mapping) else "")
    if recommended_step not in ALLOWED_NEXT_INTERNAL_STEPS_V1:
        recommended_step = _compact_text(scorecard.get("recommended_next_action") if isinstance(scorecard, Mapping) else "")
    if recommended_step not in ALLOWED_NEXT_INTERNAL_STEPS_V1:
        recommended_step = "probe"
    candidate_ref = build_suggestion_store_candidate_ref_v1(
        {
            "candidate_id": _compact_text(primary_candidate.get("candidate_id") or f"candidate:{_stable_digest({'perspicuity': summarize_perspicuity_packet_v1(perspicuity_packet)})[:12]}") ,
            "source_engine_name": "perspicuity_scorer",
            "source_run_id": _compact_text(perspicuity_packet.get("run_id") or "perspicuity-run"),
            "candidate_type": _compact_text(primary_candidate.get("candidate_type") or "perspicuity_candidate"),
            "candidate_summary": _compact_text(primary_candidate.get("candidate_summary") or summarize_perspicuity_packet_v1(perspicuity_packet)),
            "candidate_status": "watch" if recommended_step != "blocked" else "blocked",
            "candidate_scope": _compact_text(primary_candidate.get("candidate_scope") or "metadata-only scope"),
            "public_claim_status": "internal_candidate_only",
            "uncertainty_factors": ["candidate remains provisional"],
            "invalidation_signals": ["not yet invalidated"],
        }
    )
    update_action = build_suggestion_store_update_action_v1(
        {
            "candidate_id": candidate_ref["candidate_id"],
            "action_type": "recommend_next_internal_step",
            "action_reason": f"Recommend {recommended_step} from metadata-only dry run.",
            "previous_status": "watch",
            "next_status": "watch",
            "operator_review_required": True,
        }
    )
    packet = build_suggestion_store_update_packet_v1(
        {
            "source_run_id": _compact_text(perspicuity_packet.get("run_id") or "perspicuity-run"),
            "research_mode": "frontier_mapping",
            "input_artifact_ref": f"artifact:suggestion-store-update:{_compact_text(dialectic_packet.get('run_id') or 'dialectic-run')}",
            "input_artifact_type": "suggestion-store-update",
            "input_summary": _compact_text(summarize_perspicuity_packet_v1(perspicuity_packet)),
            "candidate_refs": [candidate_ref],
            "update_actions": [update_action],
            "suggestion_store_updates": [deepcopy(update_action)],
            "public_claim_status": "internal_candidate_only",
            "public_gap_card_status": "public_export_blocked",
            "operator_review_required": True,
            "storage_write_authorized": False,
            "memory_mutation_authorized": False,
            "project_mutation_authorized": False,
            "behavior_promotion_authorized": False,
            "public_claim_authorized": False,
            "safe_metadata": _default_safe_metadata(),
            "denied_authority": _full_denied_authority(),
        }
    )
    return packet


def _build_calibration_stage(perspicuity_packet: Mapping[str, Any], recommended_step: str) -> dict[str, Any]:
    packet = build_forecast_calibration_record_v1(
        {
            "source_run": perspicuity_packet,
            "source_run_id": _compact_text(perspicuity_packet.get("run_id") or "perspicuity-run"),
            "source_engine_name": _compact_text(perspicuity_packet.get("engine_name") or "perspicuity_scorer"),
            "prediction_statement": f"Metadata-only next-step recommendation: {recommended_step}.",
            "prediction_type": "internal_step_prediction",
            "outcome_status": "not_observed_yet",
            "calibration_result": "not_yet_calibrated",
            "confidence_before": 0.5,
            "confidence_after": 0.5,
            "confidence_basis": "metadata-only dry run",
            "uncertainty_factors": ["not yet observed"],
            "invalidation_signals": ["not yet invalidated"],
            "expected_outcome": f"loop recommends {recommended_step}",
            "observed_outcome": "not observed yet",
            "public_claim_status": "internal_candidate_only",
            "safe_metadata": _default_safe_metadata(),
            "denied_authority": _full_denied_authority(),
        }
    )
    return packet


def run_minimal_recursive_research_loop_dry_run_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = _merge_payload(payload, **overrides)
    input_signal = build_minimal_loop_input_signal_v1(data.get("input_signal") or data)
    loop_run_id = _compact_text(data.get("loop_run_id")) or f"loop:{_stable_digest({'input_signal': input_signal['signal_id'], 'summary': input_signal['signal_summary']})[:16]}"

    blocked_actions: list[str] = []
    stage_outputs: dict[str, Any] = {}

    try:
        raw_signal = _build_raw_signal_stage(input_signal)
        safe_raw_signal = _json_safe(raw_signal)
        raw_validation = validate_raw_signal_cartography_packet_v1(safe_raw_signal)
        raw_issues = _extract_stage_issues(raw_validation)
        if raw_issues:
            blocked_actions.extend(f"raw_signal_cartography:{issue}" for issue in raw_issues)
        stage_outputs["raw_signal_cartography"] = safe_raw_signal
        raw_signal = safe_raw_signal
    except Exception as exc:
        blocked_actions.append(f"raw_signal_cartography:{_compact_text(exc.__class__.__name__)}")
        stage_outputs["raw_signal_cartography"] = _record_stage_failure("raw_signal_cartography", [str(exc)])
        raw_signal = stage_outputs["raw_signal_cartography"]

    try:
        uoa = _build_uoa_stage(raw_signal)
        safe_uoa = _json_safe(uoa)
        uoa_validation = validate_unintelligible_output_analysis_packet_v1(safe_uoa)
        raw_issues = _extract_stage_issues(uoa_validation)
        if raw_issues:
            blocked_actions.extend(f"unintelligible_output_analysis:{issue}" for issue in raw_issues)
        stage_outputs["unintelligible_output_analysis"] = safe_uoa
        uoa = safe_uoa
    except Exception as exc:
        blocked_actions.append(f"unintelligible_output_analysis:{_compact_text(exc.__class__.__name__)}")
        stage_outputs["unintelligible_output_analysis"] = _record_stage_failure("unintelligible_output_analysis", [str(exc)])
        uoa = stage_outputs["unintelligible_output_analysis"]

    try:
        unknown_run = _build_unknown_engine_stage(uoa, raw_signal)
        safe_unknown_run = _json_safe(unknown_run)
        unknown_validation = validate_unknown_engine_research_run_v1(safe_unknown_run)
        raw_issues = _extract_stage_issues(unknown_validation)
        if raw_issues:
            blocked_actions.extend(f"unknown_engine_run:{issue}" for issue in raw_issues)
        stage_outputs["unknown_engine_run"] = safe_unknown_run
        unknown_run = safe_unknown_run
    except Exception as exc:
        blocked_actions.append(f"unknown_engine_run:{_compact_text(exc.__class__.__name__)}")
        stage_outputs["unknown_engine_run"] = _record_stage_failure("unknown_engine_run", [str(exc)])
        unknown_run = stage_outputs["unknown_engine_run"]

    try:
        nonlinear_run = _build_nonlinear_stage(unknown_run, uoa)
        safe_nonlinear_run = _json_safe(nonlinear_run)
        nonlinear_validation = validate_nonlinear_inspiration_packet_v1(safe_nonlinear_run)
        raw_issues = _extract_stage_issues(nonlinear_validation)
        if raw_issues:
            blocked_actions.extend(f"nonlinear_inspiration_run:{issue}" for issue in raw_issues)
        stage_outputs["nonlinear_inspiration_run"] = safe_nonlinear_run
        nonlinear_run = safe_nonlinear_run
    except Exception as exc:
        blocked_actions.append(f"nonlinear_inspiration_run:{_compact_text(exc.__class__.__name__)}")
        stage_outputs["nonlinear_inspiration_run"] = _record_stage_failure("nonlinear_inspiration_run", [str(exc)])
        nonlinear_run = stage_outputs["nonlinear_inspiration_run"]

    try:
        rule_pressure_run, rule_pressure_target = _build_rule_pressure_stage(nonlinear_run)
        safe_rule_pressure_run = _json_safe(rule_pressure_run)
        rule_pressure_validation = validate_rule_pressure_packet_v1(safe_rule_pressure_run)
        raw_issues = _extract_stage_issues(rule_pressure_validation)
        if raw_issues:
            blocked_actions.extend(f"rule_pressure_run:{issue}" for issue in raw_issues)
        stage_outputs["rule_pressure_run"] = safe_rule_pressure_run
        rule_pressure_run = safe_rule_pressure_run
    except Exception as exc:
        blocked_actions.append(f"rule_pressure_run:{_compact_text(exc.__class__.__name__)}")
        stage_outputs["rule_pressure_run"] = _record_stage_failure("rule_pressure_run", [str(exc)])
        rule_pressure_run = stage_outputs["rule_pressure_run"]
        rule_pressure_target = {}

    try:
        dialectic_run = _build_dialectic_stage(rule_pressure_run, rule_pressure_target)
        safe_dialectic_run = _json_safe(dialectic_run)
        dialectic_validation = validate_dialectic_loop_packet_v1(safe_dialectic_run)
        raw_issues = _extract_stage_issues(dialectic_validation)
        if raw_issues:
            blocked_actions.extend(f"dialectic_generator_run:{issue}" for issue in raw_issues)
        stage_outputs["dialectic_generator_run"] = safe_dialectic_run
        dialectic_run = safe_dialectic_run
    except Exception as exc:
        blocked_actions.append(f"dialectic_generator_run:{_compact_text(exc.__class__.__name__)}")
        stage_outputs["dialectic_generator_run"] = _record_stage_failure("dialectic_generator_run", [str(exc)])
        dialectic_run = stage_outputs["dialectic_generator_run"]

    try:
        perspicuity_run = _build_perspicuity_stage(dialectic_run, rule_pressure_run)
        safe_perspicuity_run = _json_safe(perspicuity_run)
        perspicuity_validation = validate_perspicuity_packet_v1(safe_perspicuity_run)
        raw_issues = _extract_stage_issues(perspicuity_validation)
        if raw_issues:
            blocked_actions.extend(f"perspicuity_score_run:{issue}" for issue in raw_issues)
        stage_outputs["perspicuity_score_run"] = safe_perspicuity_run
        perspicuity_run = safe_perspicuity_run
    except Exception as exc:
        blocked_actions.append(f"perspicuity_score_run:{_compact_text(exc.__class__.__name__)}")
        stage_outputs["perspicuity_score_run"] = _record_stage_failure("perspicuity_score_run", [str(exc)])
        perspicuity_run = stage_outputs["perspicuity_score_run"]

    recommended_next_internal_step = _normalize_next_step(
        blocked_actions=blocked_actions,
        perspicuity_packet=perspicuity_run if isinstance(perspicuity_run, Mapping) else None,
        suggestion_packet=None,
        rule_pressure_packet=rule_pressure_run if isinstance(rule_pressure_run, Mapping) else None,
    )

    try:
        suggestion_packet = _build_suggestion_stage(perspicuity_run, dialectic_run)
        safe_suggestion_packet = _json_safe(suggestion_packet)
        suggestion_validation = validate_suggestion_store_update_packet_v1(safe_suggestion_packet)
        raw_issues = _extract_stage_issues(suggestion_validation)
        if raw_issues:
            blocked_actions.extend(f"suggestion_store_update_packet:{issue}" for issue in raw_issues)
        stage_outputs["suggestion_store_update_packet"] = safe_suggestion_packet
        suggestion_packet = safe_suggestion_packet
    except Exception as exc:
        blocked_actions.append(f"suggestion_store_update_packet:{_compact_text(exc.__class__.__name__)}")
        stage_outputs["suggestion_store_update_packet"] = _record_stage_failure("suggestion_store_update_packet", [str(exc)])
        suggestion_packet = stage_outputs["suggestion_store_update_packet"]

    if recommended_next_internal_step == "probe" and isinstance(suggestion_packet, Mapping):
        actions = suggestion_packet.get("update_actions") or []
        if actions and isinstance(actions[0], Mapping):
            action_type = _compact_text(actions[0].get("action_type"))
            if action_type == "recommend_next_internal_step":
                recommended_next_internal_step = "probe"

    try:
        calibration_record = _build_calibration_stage(perspicuity_run, recommended_next_internal_step)
        safe_calibration_record = _json_safe(calibration_record)
        calibration_validation = validate_forecast_calibration_record_v1(safe_calibration_record)
        raw_issues = _extract_stage_issues(calibration_validation)
        if raw_issues:
            blocked_actions.extend(f"calibration_bridge_record:{issue}" for issue in raw_issues)
        stage_outputs["calibration_bridge_record"] = safe_calibration_record
        calibration_record = safe_calibration_record
    except Exception as exc:
        blocked_actions.append(f"calibration_bridge_record:{_compact_text(exc.__class__.__name__)}")
        stage_outputs["calibration_bridge_record"] = _record_stage_failure("calibration_bridge_record", [str(exc)])
        calibration_record = stage_outputs["calibration_bridge_record"]

    operator_review_required = True

    result = {
        "schema_version": SCHEMA_VERSION_V1,
        "loop_run_id": loop_run_id,
        "input_signal": _json_safe(input_signal),
        **stage_outputs,
        "final_loop_summary": "",
        "recommended_next_internal_step": recommended_next_internal_step,
        "blocked_actions": list(dict.fromkeys(blocked_actions)),
        "operator_review_required": operator_review_required,
        "runtime_action_authorized": False,
        "storage_write_authorized": False,
        "memory_mutation_authorized": False,
        "project_mutation_authorized": False,
        "behavior_promotion_authorized": False,
        "public_claim_authorized": False,
        "denied_authority": _default_denied_authority(),
        "safe_metadata": _default_safe_metadata(),
    }
    result["final_loop_summary"] = summarize_minimal_recursive_research_loop_result_v1(result)
    return _json_safe(result)


def validate_minimal_recursive_research_loop_result_v1(result: Any) -> dict[str, Any]:
    raw = result if isinstance(result, Mapping) else {}
    blocked_labels: list[str] = []

    if not isinstance(result, Mapping):
        blocked_labels.append("invalid_result_type")
        return {
            "schema_version": SCHEMA_VERSION_V1,
            "valid": False,
            "blocked": True,
            "blocked_labels": blocked_labels,
            "summary_text": "Blocked minimal recursive research loop: invalid result type.",
        }

    if _compact_text(raw.get("schema_version")) != SCHEMA_VERSION_V1:
        blocked_labels.append("invalid_schema_version")
    if not _compact_text(raw.get("loop_run_id")):
        blocked_labels.append("missing_loop_run_id")

    for field in _REQUIRED_RESULT_FIELDS_V1:
        if field not in raw:
            blocked_labels.append(f"missing_{field}")

    input_signal = raw.get("input_signal")
    if not isinstance(input_signal, Mapping) or not _compact_text(input_signal.get("signal_id")):
        blocked_labels.append("missing_input_signal")
    elif _contains_forbidden_text(input_signal):
        blocked_labels.append("forbidden_input_signal_text")

    stage_validators = {
        "raw_signal_cartography": validate_raw_signal_cartography_packet_v1,
        "unintelligible_output_analysis": validate_unintelligible_output_analysis_packet_v1,
        "unknown_engine_run": validate_unknown_engine_research_run_v1,
        "nonlinear_inspiration_run": validate_nonlinear_inspiration_packet_v1,
        "rule_pressure_run": validate_rule_pressure_packet_v1,
        "dialectic_generator_run": validate_dialectic_loop_packet_v1,
        "perspicuity_score_run": validate_perspicuity_packet_v1,
        "suggestion_store_update_packet": validate_suggestion_store_update_packet_v1,
        "calibration_bridge_record": validate_forecast_calibration_record_v1,
    }

    for field, validator in stage_validators.items():
        packet = raw.get(field)
        if not isinstance(packet, Mapping):
            blocked_labels.append(f"missing_{field}")
            continue
        if _contains_forbidden_text(packet):
            blocked_labels.append(f"forbidden_{field}_text")
        validation = validator(packet)
        blocked_labels.extend(_extract_stage_issues(validation))

    for field in (
        "runtime_action_authorized",
        "storage_write_authorized",
        "memory_mutation_authorized",
        "project_mutation_authorized",
        "behavior_promotion_authorized",
        "public_claim_authorized",
    ):
        if bool(raw.get(field)):
            blocked_labels.append(f"unsafe_{field}")

    if _compact_text(raw.get("recommended_next_internal_step")) not in ALLOWED_NEXT_INTERNAL_STEPS_V1:
        blocked_labels.append("invalid_recommended_next_internal_step")

    if not isinstance(raw.get("blocked_actions"), list):
        blocked_labels.append("invalid_blocked_actions")

    safe_metadata = raw.get("safe_metadata") if isinstance(raw.get("safe_metadata"), Mapping) else {}
    if not isinstance(safe_metadata, Mapping) or not bool(safe_metadata.get("safe", False)):
        blocked_labels.append("unsafe_safe_metadata")

    if not isinstance(raw.get("denied_authority"), Mapping):
        blocked_labels.append("missing_denied_authority")
    elif _contains_forbidden_text(raw.get("denied_authority")):
        blocked_labels.append("unsafe_denied_authority")

    if _contains_forbidden_text(raw):
        blocked_labels.append("forbidden_result_text")

    valid = not blocked_labels
    summary = summarize_minimal_recursive_research_loop_result_v1(raw)
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "valid": valid,
        "blocked": not valid,
        "blocked_labels": list(dict.fromkeys(blocked_labels)),
        "summary_text": summary,
        "recommended_next_internal_step": _compact_text(raw.get("recommended_next_internal_step")),
        "operator_review_required": bool(raw.get("operator_review_required")),
    }


def summarize_minimal_recursive_research_loop_result_v1(result: Any) -> str:
    raw = result if isinstance(result, Mapping) else {}
    loop_run_id = _compact_text(raw.get("loop_run_id"), "loop:unknown")
    next_step = _compact_text(raw.get("recommended_next_internal_step"), "blocked")
    blocked_actions = raw.get("blocked_actions") if isinstance(raw.get("blocked_actions"), list) else []
    stage_status = "ok" if not blocked_actions else f"blocked:{len(blocked_actions)}"
    if blocked_actions:
        first = _compact_text(blocked_actions[0])
        return f"Dry-run loop {loop_run_id}: {stage_status}; next={next_step}; first_block={first}."
    return f"Dry-run loop {loop_run_id}: all stages validated; next={next_step}; metadata-only and non-public-safe."


def to_minimal_recursive_research_loop_json_safe_v1(result: Any) -> dict[str, Any]:
    return _json_safe(result if isinstance(result, Mapping) else {})


def build_initial_minimal_recursive_loop_examples_v1() -> list[dict[str, Any]]:
    examples = [
        run_minimal_recursive_research_loop_dry_run_v1(
            {
                "input_signal": build_minimal_loop_input_signal_v1(
                    {
                        "signal_id": "signal:minimal-loop:001",
                        "signal_summary": "Synthetic metadata-only signal with repeated boundary markers and a compact update proposal.",
                    }
                )
            }
        ),
        run_minimal_recursive_research_loop_dry_run_v1(
            {
                "input_signal": build_minimal_loop_input_signal_v1(
                    {
                        "signal_id": "signal:minimal-loop:002",
                        "signal_summary": "Synthetic signal emphasizing a counterexample probe and a bounded calibration step.",
                        "signal_type": "synthetic_recursive_research_seed",
                    }
                ),
                "loop_run_id": "loop:minimal-loop:002",
            }
        ),
    ]
    return [_json_safe(example) for example in examples]


__all__ = (
    "ALLOWED_NEXT_INTERNAL_STEPS_V1",
    "SCHEMA_VERSION_V1",
    "build_initial_minimal_recursive_loop_examples_v1",
    "build_minimal_loop_input_signal_v1",
    "run_minimal_recursive_research_loop_dry_run_v1",
    "summarize_minimal_recursive_research_loop_result_v1",
    "to_minimal_recursive_research_loop_json_safe_v1",
    "validate_minimal_recursive_research_loop_result_v1",
)
