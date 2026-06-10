"""WESLR Dialectic Generator Loop V1 metadata helpers.

Deterministic, metadata-only scaffolding that turns high-value candidates into
new generated source signals, pressure-test prompts, counter-signals,
calibration-ready probes, compressed lessons, and next experiments.

This module does not perform runtime wiring, provider/model calls, retrieval,
tool execution, persistence, .weslr IO, live ingestion, memory/project mutation,
behavior-pack promotion, public claims, or final-answer generation.
"""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from typing import Any, Mapping

from weslr.cognitive_research_protocol import (
    build_cognitive_research_run_v1,
    build_default_cognitive_research_denied_authority_v1,
    build_generated_source_signal_metadata_v1,
    build_source_signal_metadata_v1,
    summarize_cognitive_research_run_v1,
    to_cognitive_research_json_safe_v1,
    validate_cognitive_research_run_v1,
)
from weslr.forecast_calibration_bridge import (
    build_forecast_calibration_packet_from_research_run_v1,
    build_forecast_calibration_record_v1,
    validate_forecast_calibration_record_v1,
)
from weslr.rule_pressure_engine import build_rule_pressure_test_v1

HELPER_TYPE_V1 = "weslr_dialectic_generator_loop_v1"
SCHEMA_VERSION_V1 = "dialectic_generator_loop_v1"
ENGINE_NAME_V1 = "dialectic_generator_loop"
ENGINE_FAMILY_V1 = "recursive_generation"

_ALLOWED_RESEARCH_MODES_V1 = (
    "internal_exploration",
    "synthetic_test",
    "calibration_replay",
    "frontier_mapping",
)
_ALLOWED_PUBLIC_CLAIM_STATUSES_V1 = (
    "not_public_claim",
    "internal_candidate_only",
    "public_export_blocked",
)
_ALLOWED_SEED_TYPES_V1 = (
    "hidden_rule_candidate",
    "operator_candidate",
    "translation_candidate",
    "structural_match_candidate",
    "motif_candidate",
    "gap_hypothesis",
    "pressure_result",
    "correction_lesson",
    "unknown",
)
_ALLOWED_COUNTER_SIGNAL_TYPES_V1 = (
    "counterexample",
    "boundary_case",
    "contradiction",
    "noise_variant",
    "false_pattern",
    "scale_shift",
    "operator_swap",
    "axiom_mutation",
    "control_case",
    "unknown",
)
_ALLOWED_MOVE_TYPES_V1 = (
    "support",
    "attack",
    "mutate",
    "invert",
    "generalize",
    "specialize",
    "translate",
    "control",
    "compress",
    "unknown",
)

_SEED_TYPE_TO_COUNTER_SIGNAL_TYPE_V1 = {
    "hidden_rule_candidate": "counterexample",
    "operator_candidate": "operator_swap",
    "translation_candidate": "contradiction",
    "structural_match_candidate": "boundary_case",
    "motif_candidate": "noise_variant",
    "gap_hypothesis": "boundary_case",
    "pressure_result": "counterexample",
    "correction_lesson": "control_case",
    "unknown": "unknown",
}
_SEED_TYPE_TO_MOVE_TYPE_V1 = {
    "hidden_rule_candidate": "attack",
    "operator_candidate": "mutate",
    "translation_candidate": "translate",
    "structural_match_candidate": "generalize",
    "motif_candidate": "support",
    "gap_hypothesis": "attack",
    "pressure_result": "compress",
    "correction_lesson": "compress",
    "unknown": "unknown",
}
_SEED_TYPE_TO_MUTATION_TYPE_V1 = {
    "hidden_rule_candidate": "hidden_rule_rewrite",
    "operator_candidate": "operator_transfer",
    "translation_candidate": "translation_rewrite",
    "structural_match_candidate": "structure_preserving_mutation",
    "motif_candidate": "motif_variation",
    "gap_hypothesis": "gap_pressure_mutation",
    "pressure_result": "pressure_result_variation",
    "correction_lesson": "correction_rewrite",
    "unknown": "dialectic_rewrite",
}
_SEED_TYPE_TO_PRESSURE_TYPE_V1 = {
    "hidden_rule_candidate": "counterexample_search",
    "operator_candidate": "operator_substitution",
    "translation_candidate": "false_pattern_insertion",
    "structural_match_candidate": "boundary_case",
    "motif_candidate": "noise_injection",
    "gap_hypothesis": "scale_shift",
    "pressure_result": "counterexample_search",
    "correction_lesson": "control_case",
    "unknown": "counterexample_search",
}
_SEED_TYPE_TO_EXPECTED_BREAKAGE_V1 = {
    "hidden_rule_candidate": "hidden_assumption_failure",
    "operator_candidate": "operator_weak_point",
    "translation_candidate": "translation_weak_point",
    "structural_match_candidate": "boundary_failure",
    "motif_candidate": "noise_weak_point",
    "gap_hypothesis": "scope_shift",
    "pressure_result": "pressure_reversal",
    "correction_lesson": "control_case_failure",
    "unknown": "unknown",
}

_FORBIDDEN_TEXT_MARKERS_V1 = (
    "raw private text",
    "raw private data",
    "private content",
    "hidden prompt",
    "system prompt",
    "developer prompt",
    "secret",
    "password",
    "token=",
    "credential",
    "final answer",
    "answer draft",
    "reply output",
    "provider output",
    "model output",
    "tool execution",
    "tool authority",
    "provider authority",
    "runtime authority",
    "llm authority",
    "public discovery",
    "proof",
    "breakthrough",
    "agi",
    "sentience",
    "consciousness",
    "behavior pack",
    "promotion",
    "memory mutation authority",
    "project mutation authority",
    ".weslr",
    "live ingestion",
    "network",
    "github rss",
    "lab notebook",
    "executable code-as-action",
)

_UNSAFE_COPY_KEY_FRAGMENTS_V1 = (
    "raw_prompt",
    "raw_response",
    "raw_observation",
    "hidden_prompt",
    "private_blob",
    "private_content",
    "secret",
    "password",
    "api_key",
    "token",
)

_SAFE_METADATA_FLAGS_V1 = (
    "safe",
    "metadata_only",
    "json_safe",
    "non_public",
    "no_runtime_wiring",
    "no_provider_calls",
    "no_tool_execution",
    "no_persistence",
    "no_memory_mutation",
    "no_project_mutation",
    "no_behavior_pack_promotion",
    "no_final_answer",
    "no_public_claims",
)


def _compact_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return " ".join(value.replace("\r", " ").replace("\n", " ").split())
    return _compact_text(str(value))


def _safe_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, str):
        raw = value.strip().lower()
        if raw in {"1", "true", "yes", "y", "on"}:
            return True
        if raw in {"0", "false", "no", "n", "off"}:
            return False
    return bool(value)


def _json_safe(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_safe(val) for key, val in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, set):
        return [_json_safe(item) for item in sorted(value, key=_compact_text)]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return _compact_text(value)


def _strip_unsafe_copy_fields(value: Any) -> Any:
    if isinstance(value, Mapping):
        cleaned: dict[str, Any] = {}
        for key, item in value.items():
            key_text = _compact_text(key).lower()
            if any(fragment in key_text for fragment in _UNSAFE_COPY_KEY_FRAGMENTS_V1):
                continue
            cleaned[str(key)] = _strip_unsafe_copy_fields(item)
        return cleaned
    if isinstance(value, list):
        return [_strip_unsafe_copy_fields(item) for item in value]
    if isinstance(value, tuple):
        return [_strip_unsafe_copy_fields(item) for item in value]
    if isinstance(value, set):
        return [_strip_unsafe_copy_fields(item) for item in sorted(value, key=_compact_text)]
    return _json_safe(value)


def _stable_digest(payload: Mapping[str, Any]) -> str:
    blob = json.dumps(_json_safe(payload), sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _merge_payload(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {}
    if isinstance(payload, Mapping):
        data.update(payload)
    if overrides:
        data.update(overrides)
    return data


def _ensure_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return list(value)
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, set):
        return list(value)
    return [value]


def _normalize_choice(value: Any, allowed: tuple[str, ...], default: str) -> str:
    raw = _compact_text(value)
    if not raw:
        return default
    lowered = raw.lower()
    return lowered if lowered in allowed else default


def _normalize_seed_type(value: Any) -> str:
    return _normalize_choice(value, _ALLOWED_SEED_TYPES_V1, "unknown")


def _normalize_counter_signal_type(value: Any) -> str:
    return _normalize_choice(value, _ALLOWED_COUNTER_SIGNAL_TYPES_V1, "unknown")


def _normalize_move_type(value: Any) -> str:
    return _normalize_choice(value, _ALLOWED_MOVE_TYPES_V1, "unknown")


def _normalize_research_mode(value: Any) -> str:
    return _normalize_choice(value, _ALLOWED_RESEARCH_MODES_V1, "internal_exploration")


def _normalize_public_claim_status(value: Any, default: str = "internal_candidate_only") -> str:
    return _normalize_choice(value, _ALLOWED_PUBLIC_CLAIM_STATUSES_V1, default)


def _contains_forbidden_text(value: Any) -> bool:
    text = _compact_text(value).lower()
    return any(marker in text for marker in _FORBIDDEN_TEXT_MARKERS_V1)


def _forbidden_text_label(prefix: str) -> str:
    return prefix


def _default_safe_metadata(engine_name: str, engine_family: str, research_mode: str) -> dict[str, Any]:
    return {
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
        "no_live_ingestion": True,
        "no_network": True,
        "no_weslr_io": True,
        "no_autonomous_self_modification": True,
        "no_retrieval_execution": True,
        "no_code_as_action": True,
        "perspicuity_is_not_a_gate": True,
        "engine_name": engine_name,
        "engine_family": engine_family,
        "research_mode": research_mode,
    }


def _default_boundary_status() -> dict[str, Any]:
    denied = build_default_cognitive_research_denied_authority_v1()
    return {
        "status": "metadata_only",
        "dialectic_loop": ENGINE_NAME_V1,
        "generator_loop": ENGINE_NAME_V1,
        "runtime_wiring_authority": False,
        "runtime_authority": False,
        "tool_authority": False,
        "provider_authority": False,
        "provider_model_call_authority": False,
        "llm_authority": False,
        "chat_responder_authority": False,
        "final_answer_generation_authority": False,
        "public_claim_authority": False,
        "retrieval_tool_authority": False,
        "filesystem_authority": False,
        "network_authority": False,
        "subprocess_authority": False,
        "weslr_io_authority": False,
        "persistence_authority": False,
        "persistence_database_write_authority": False,
        "real_memory_mutation_authority": False,
        "real_project_mutation_authority": False,
        "behavior_change_authority": False,
        "behavior_pack_promotion_authority": False,
        "autonomous_self_modification_authority": False,
        "official_intelligence_claim_authority": False,
        "public_discovery_claim_authority": False,
        "boundary_notes": "metadata-only; fail closed; no runtime, provider, tool, persistence, or public-export authority",
        "denied_authority": denied,
    }


def _dialectic_seed_defaults(data: Mapping[str, Any]) -> dict[str, Any]:
    seed_summary = _compact_text(data.get("seed_summary") or data.get("input_summary") or "metadata-only dialectic seed")
    candidate = _compact_text(data.get("candidate_claim_or_operator") or data.get("candidate_rule") or data.get("candidate_operator") or seed_summary)
    return {
        "seed_id": _compact_text(data.get("seed_id")) or f"seed-{_stable_digest({'source_engine_name': data.get('source_engine_name'), 'source_run_id': data.get('source_run_id'), 'seed_summary': seed_summary, 'candidate': candidate})[:12]}",
        "source_engine_name": _compact_text(data.get("source_engine_name") or "unknown_engine").lower() or "unknown_engine",
        "source_run_id": _compact_text(data.get("source_run_id")) or f"source-run-{_stable_digest({'engine': data.get('source_engine_name'), 'summary': seed_summary})[:12]}",
        "seed_type": _normalize_seed_type(data.get("seed_type") or data.get("candidate_type") or "unknown"),
        "seed_summary": seed_summary,
        "candidate_claim_or_operator": candidate,
        "known_scope": _compact_text(data.get("known_scope") or data.get("claimed_scope") or "metadata-only scope") or "metadata-only scope",
        "failure_scope": _compact_text(data.get("failure_scope") or data.get("failure_mode") or "bounded failure scope") or "bounded failure scope",
        "uncertainty_factors": _ensure_list(data.get("uncertainty_factors")) or ["candidate remains provisional"],
        "invalidation_signals": _ensure_list(data.get("invalidation_signals")) or ["not yet invalidated"],
        "public_claim_status": _normalize_public_claim_status(data.get("public_claim_status"), "internal_candidate_only"),
    }


def build_dialectic_seed_candidate_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = _merge_payload(payload, **overrides)
    return _json_safe(_dialectic_seed_defaults(data))


def _seed_or_payload(data: Mapping[str, Any]) -> dict[str, Any]:
    seed = data.get("seed") if isinstance(data.get("seed"), Mapping) else None
    merged = dict(seed or {})
    merged.update(data)
    return merged


def _dialectic_counter_defaults(data: Mapping[str, Any]) -> dict[str, Any]:
    seed = _dialectic_seed_defaults(_seed_or_payload(data))
    counter_signal_type = _normalize_counter_signal_type(
        data.get("counter_signal_type") or _SEED_TYPE_TO_COUNTER_SIGNAL_TYPE_V1.get(seed["seed_type"], "unknown")
    )
    counter_summary = _compact_text(data.get("counter_signal_summary") or data.get("summary") or f"Counter signal against {seed['candidate_claim_or_operator']}")
    target_uncertainty = _compact_text(data.get("target_uncertainty") or seed["failure_scope"] or "bounded uncertainty") or "bounded uncertainty"
    return {
        "counter_signal_id": _compact_text(data.get("counter_signal_id")) or f"counter-{_stable_digest({'seed_id': seed['seed_id'], 'type': counter_signal_type, 'summary': counter_summary})[:12]}",
        "seed_id": seed["seed_id"],
        "counter_signal_type": counter_signal_type,
        "counter_signal_summary": counter_summary,
        "what_it_challenges": _compact_text(data.get("what_it_challenges") or seed["candidate_claim_or_operator"]) or seed["candidate_claim_or_operator"],
        "expected_breakage": _compact_text(data.get("expected_breakage") or _SEED_TYPE_TO_EXPECTED_BREAKAGE_V1.get(seed["seed_type"], "unknown")) or "unknown",
        "target_uncertainty": target_uncertainty,
        "safe_to_reingest_as_metadata": _safe_bool(data.get("safe_to_reingest_as_metadata", True), True),
        "public_claim_status": _normalize_public_claim_status(data.get("public_claim_status") or seed["public_claim_status"], "internal_candidate_only"),
    }


def build_generated_counter_signal_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = _merge_payload(payload, **overrides)
    return _json_safe(_dialectic_counter_defaults(data))


def _dialectic_probe_defaults(data: Mapping[str, Any]) -> dict[str, Any]:
    seed = _dialectic_seed_defaults(_seed_or_payload(data))
    probe_goal = _compact_text(data.get("probe_goal") or data.get("falsification_condition") or f"Probe {seed['candidate_claim_or_operator']}")
    probe_summary = _compact_text(data.get("probe_summary") or f"Probe whether {seed['candidate_claim_or_operator']} survives metadata-only pressure.")
    expected_observation = _compact_text(data.get("expected_observation") or seed["seed_summary"] or "bounded observation") or "bounded observation"
    falsification_condition = _compact_text(data.get("falsification_condition") or f"If {seed['candidate_claim_or_operator']} cannot survive a bounded counterexample, the seed is narrowed.")
    calibration_prediction = data.get("calibration_prediction")
    if not isinstance(calibration_prediction, Mapping):
        calibration_prediction = {
            "record_id": _compact_text(data.get("record_id")) or f"calibration-{_stable_digest({'seed_id': seed['seed_id'], 'statement': probe_summary})[:12]}",
            "prediction_type": _compact_text(data.get("prediction_type") or "probe_prediction") or "probe_prediction",
            "prediction_statement": probe_summary,
            "prediction_scope": _compact_text(data.get("prediction_scope") or seed["known_scope"]) or seed["known_scope"],
            "confidence_before": float(data.get("confidence_before", 0.65)),
            "confidence_after": float(data.get("confidence_after", 0.55)),
            "confidence_basis": _compact_text(data.get("confidence_basis") or "metadata-only bridge basis") or "metadata-only bridge basis",
            "uncertainty_factors": _ensure_list(data.get("uncertainty_factors")) or ["prediction unresolved"],
            "invalidation_signals": _ensure_list(data.get("invalidation_signals")) or ["not_observed_yet"],
            "expected_outcome": _compact_text(data.get("expected_outcome") or probe_goal) or probe_goal,
            "observed_outcome": _compact_text(data.get("observed_outcome") or ""),
            "outcome_status": _compact_text(data.get("outcome_status") or "not_observed_yet") or "not_observed_yet",
            "calibration_result": _compact_text(data.get("calibration_result") or "not_yet_calibrated") or "not_yet_calibrated",
            "error_type": _compact_text(data.get("error_type") or "none") or "none",
            "assumptions_used": _ensure_list(data.get("assumptions_used")) or [seed["candidate_claim_or_operator"]],
            "assumptions_failed": _ensure_list(data.get("assumptions_failed")),
            "missing_signals": _ensure_list(data.get("missing_signals")),
            "conflicting_signals": _ensure_list(data.get("conflicting_signals")),
            "correction": _compact_text(data.get("correction") or ""),
            "compressed_lesson": _compact_text(data.get("compressed_lesson") or "") or "",
            "future_adjustment": _compact_text(data.get("future_adjustment") or "keep calibration metadata-only") or "keep calibration metadata-only",
        }
    return {
        "probe_signal_id": _compact_text(data.get("probe_signal_id")) or f"probe-{_stable_digest({'seed_id': seed['seed_id'], 'goal': probe_goal, 'summary': probe_summary})[:12]}",
        "seed_id": seed["seed_id"],
        "probe_goal": probe_goal,
        "probe_summary": probe_summary,
        "expected_observation": expected_observation,
        "falsification_condition": falsification_condition,
        "calibration_prediction": calibration_prediction,
        "next_best_observation": _compact_text(data.get("next_best_observation") or f"Compare {seed['candidate_claim_or_operator']} with a control case.") or f"Compare {seed['candidate_claim_or_operator']} with a control case.",
        "safe_to_pressure_test_as_metadata": _safe_bool(data.get("safe_to_pressure_test_as_metadata", True), True),
    }


def build_generated_probe_signal_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = _merge_payload(payload, **overrides)
    return _json_safe(_dialectic_probe_defaults(data))


def validate_generated_probe_signal_v1(probe: Any) -> dict[str, Any]:
    raw = probe if isinstance(probe, Mapping) else {}
    violations: list[str] = []
    required = (
        "probe_signal_id",
        "seed_id",
        "probe_goal",
        "probe_summary",
        "expected_observation",
        "falsification_condition",
        "calibration_prediction",
        "next_best_observation",
        "safe_to_pressure_test_as_metadata",
    )
    for field in required:
        if field not in raw or (field != "safe_to_pressure_test_as_metadata" and not _compact_text(raw.get(field)) and raw.get(field) is not False):
            violations.append(f"missing_{field}")
    prediction = raw.get("calibration_prediction")
    if not isinstance(prediction, Mapping):
        violations.append("missing_calibration_prediction")
    else:
        required_prediction_fields = (
            "prediction_type",
            "prediction_statement",
            "prediction_scope",
            "confidence_before",
            "confidence_after",
            "outcome_status",
            "calibration_result",
            "uncertainty_factors",
            "invalidation_signals",
            "expected_outcome",
            "future_adjustment",
        )
        if any(field not in prediction for field in required_prediction_fields):
            violations.append("invalid_calibration_prediction")
    if not _compact_text(raw.get("falsification_condition")):
        violations.append("missing_falsification_condition")
    if _contains_forbidden_text(raw.get("probe_goal")) or _contains_forbidden_text(raw.get("probe_summary")) or _contains_forbidden_text(raw.get("expected_observation")) or _contains_forbidden_text(raw.get("next_best_observation")):
        violations.append("forbidden_probe_text")
    return {"valid": not violations, "violations": violations, "probe": _json_safe(raw)}


def _dialectic_turn_defaults(data: Mapping[str, Any]) -> dict[str, Any]:
    seed = _dialectic_seed_defaults(_seed_or_payload(data))
    move_type = _normalize_move_type(data.get("move_type") or _SEED_TYPE_TO_MOVE_TYPE_V1.get(seed["seed_type"], "unknown"))
    move_summary = _compact_text(data.get("move_summary") or f"{move_type} the candidate {seed['candidate_claim_or_operator']} in metadata only.") or f"{move_type} the candidate {seed['candidate_claim_or_operator']} in metadata only."
    generated_source_signal_ref = _compact_text(data.get("generated_source_signal_ref") or data.get("generated_source_signal", {}).get("generated_signal_id") if isinstance(data.get("generated_source_signal"), Mapping) else "")
    pressure_test_ref = _compact_text(data.get("pressure_test_ref") or data.get("pressure_test", {}).get("pressure_test_id") if isinstance(data.get("pressure_test"), Mapping) else "")
    calibration_record_ref = _compact_text(data.get("calibration_record_ref") or data.get("calibration_record", {}).get("record_id") if isinstance(data.get("calibration_record"), Mapping) else "")
    return {
        "turn_id": _compact_text(data.get("turn_id")) or f"turn-{_stable_digest({'seed_id': seed['seed_id'], 'move_type': move_type, 'move_summary': move_summary})[:12]}",
        "seed_id": seed["seed_id"],
        "turn_index": int(data.get("turn_index", 0)),
        "move_type": move_type,
        "move_summary": move_summary,
        "generated_source_signal_ref": generated_source_signal_ref or f"generated-source-{seed['seed_id']}",
        "pressure_test_ref": pressure_test_ref or f"pressure-test-{seed['seed_id']}",
        "calibration_record_ref": calibration_record_ref or f"calibration-record-{seed['seed_id']}",
        "compressed_lesson": _compact_text(data.get("compressed_lesson") or f"{move_type} narrows the candidate without claiming truth.") or f"{move_type} narrows the candidate without claiming truth.",
        "next_turn_recommendation": _compact_text(data.get("next_turn_recommendation") or f"{_SEED_TYPE_TO_MOVE_TYPE_V1.get(seed['seed_type'], 'control')} next.") or f"{_SEED_TYPE_TO_MOVE_TYPE_V1.get(seed['seed_type'], 'control')} next.",
    }


def build_dialectic_turn_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = _merge_payload(payload, **overrides)
    return _json_safe(_dialectic_turn_defaults(data))


def _build_generated_source_signals(seed_candidates: list[dict[str, Any]], research_mode: str) -> list[dict[str, Any]]:
    generated: list[dict[str, Any]] = []
    for seed in seed_candidates:
        mutation_type = _SEED_TYPE_TO_MUTATION_TYPE_V1.get(seed["seed_type"], "dialectic_rewrite")
        generated.append(
            build_generated_source_signal_metadata_v1(
                {
                    "parent_suggestion_id": seed["seed_id"],
                    "generation_reason": f"dialectic mutation from {seed['seed_type']}",
                    "mutation_type": mutation_type,
                    "source_ref": seed["source_run_id"],
                    "source_summary": seed["seed_summary"],
                    "target_uncertainty": seed["failure_scope"],
                    "safe_to_reingest": True,
                    "raw_generated_content_included": False,
                    "engine_name": ENGINE_NAME_V1,
                    "research_mode": research_mode,
                }
            )
        )
    return generated


def _build_rule_pressure_tests(seed_candidates: list[dict[str, Any]], generated_source_signals: list[dict[str, Any]]) -> list[dict[str, Any]]:
    tests: list[dict[str, Any]] = []
    for index, seed in enumerate(seed_candidates):
        generated = generated_source_signals[index] if index < len(generated_source_signals) else {}
        pressure_type = _SEED_TYPE_TO_PRESSURE_TYPE_V1.get(seed["seed_type"], "counterexample_search")
        tests.append(
            build_rule_pressure_test_v1(
                {
                    "target": {
                        "source_engine_name": seed["source_engine_name"],
                        "source_run_id": seed["source_run_id"],
                        "target_type": seed["seed_type"],
                        "target_summary": seed["seed_summary"],
                        "candidate_rule_or_operator": seed["candidate_claim_or_operator"],
                        "claimed_scope": seed["known_scope"],
                        "known_scope": seed["known_scope"],
                        "uncertainty_factors": seed["uncertainty_factors"],
                        "invalidation_signals": seed["invalidation_signals"],
                        "public_claim_status": seed["public_claim_status"],
                    },
                    "target_id": seed["seed_id"],
                    "target_rule_or_operator": seed["candidate_claim_or_operator"],
                    "pressure_type": pressure_type,
                    "pressure_summary": f"Pressure-test {seed['candidate_claim_or_operator']} via {pressure_type}.",
                    "input_mutation": _compact_text(generated.get("generated_signal_summary") or generated.get("mutation_summary") or seed["seed_summary"]) or seed["seed_summary"],
                    "expected_failure_mode": _SEED_TYPE_TO_EXPECTED_BREAKAGE_V1.get(seed["seed_type"], "unknown"),
                    "control_case_summary": f"Control case keeps {seed['candidate_claim_or_operator']} bounded.",
                    "success_criteria": "pressure reveals a bounded weakness",
                    "failure_criteria": "pressure leaves an unsupported public or runtime claim",
                    "safe_to_run_as_metadata": True,
                }
            )
        )
    return tests


def _build_probe_signals(seed_candidates: list[dict[str, Any]], research_mode: str) -> list[dict[str, Any]]:
    probes: list[dict[str, Any]] = []
    for seed in seed_candidates:
        probes.append(
            build_generated_probe_signal_v1(
                {
                    "seed": seed,
                    "research_mode": research_mode,
                    "probe_goal": f"Probe whether {seed['candidate_claim_or_operator']} survives metadata-only pressure.",
                    "probe_summary": f"Probe {seed['seed_type']} candidate {seed['seed_id']}.",
                    "expected_observation": seed["seed_summary"],
                    "falsification_condition": f"If {seed['candidate_claim_or_operator']} cannot survive a control case, narrow it.",
                    "next_best_observation": f"Compare {seed['candidate_claim_or_operator']} with a control case.",
                }
            )
        )
    return probes


def _build_turns(seed_candidates: list[dict[str, Any]], generated_source_signals: list[dict[str, Any]], rule_pressure_tests: list[dict[str, Any]], probes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    turns: list[dict[str, Any]] = []
    for index, seed in enumerate(seed_candidates):
        generated = generated_source_signals[index] if index < len(generated_source_signals) else {}
        pressure_test = rule_pressure_tests[index] if index < len(rule_pressure_tests) else {}
        probe = probes[index] if index < len(probes) else {}
        move_type = _SEED_TYPE_TO_MOVE_TYPE_V1.get(seed["seed_type"], "unknown")
        turns.append(
            build_dialectic_turn_v1(
                {
                    "seed": seed,
                    "turn_index": index,
                    "move_type": move_type,
                    "move_summary": f"{move_type} {seed['candidate_claim_or_operator']} through a bounded dialectic turn.",
                    "generated_source_signal_ref": generated.get("generated_signal_id", f"generated-source-{seed['seed_id']}"),
                    "pressure_test_ref": pressure_test.get("pressure_test_id", f"pressure-test-{seed['seed_id']}"),
                    "calibration_record_ref": probe.get("calibration_prediction", {}).get("record_id", f"calibration-record-{seed['seed_id']}"),
                    "compressed_lesson": f"{move_type} keeps the loop metadata-only and bounded.",
                    "next_turn_recommendation": f"{_SEED_TYPE_TO_MOVE_TYPE_V1.get(seed['seed_type'], 'control')} next.",
                }
            )
        )
    return turns


def _validate_text_block(label: str, *values: Any) -> list[str]:
    return [label] if any(_contains_forbidden_text(value) for value in values) else []


def _validate_seed_candidates(packet: Mapping[str, Any]) -> list[str]:
    blocked: list[str] = []
    seeds = _ensure_list(packet.get("dialectic_seed_candidates"))
    if not seeds:
        return ["missing_seed_id"]
    for index, item in enumerate(seeds):
        if not isinstance(item, Mapping):
            blocked.append(f"missing_seed_id_{index}")
            continue
        seed_id = _compact_text(item.get("seed_id"))
        if not seed_id:
            blocked.append(f"missing_seed_id_{index}")
        if not _compact_text(item.get("seed_summary")):
            blocked.append(f"missing_seed_summary_{index}")
        if not _compact_text(item.get("candidate_claim_or_operator")):
            blocked.append(f"missing_candidate_claim_or_operator_{index}")
        if not _ensure_list(item.get("uncertainty_factors")):
            blocked.append(f"missing_uncertainty_factors_{index}")
        if not _ensure_list(item.get("invalidation_signals")):
            blocked.append(f"missing_invalidation_signals_{index}")
        if _normalize_seed_type(item.get("seed_type")) not in _ALLOWED_SEED_TYPES_V1:
            blocked.append(f"invalid_seed_type_{index}")
        public_status_raw = _compact_text(item.get("public_claim_status")).lower()
        if public_status_raw not in _ALLOWED_PUBLIC_CLAIM_STATUSES_V1:
            blocked.append(f"invalid_public_claim_status_{index}")
            if any(fragment in public_status_raw for fragment in ("safe", "gap", "public", "export")):
                blocked.append(f"seed_marked_public_export_safe_{index}")
        blocked.extend(_validate_text_block(f"forbidden_seed_text_{index}", item.get("seed_summary"), item.get("candidate_claim_or_operator"), item.get("known_scope"), item.get("failure_scope")))
    return blocked


def _validate_counter_signals(packet: Mapping[str, Any]) -> list[str]:
    blocked: list[str] = []
    signals = _ensure_list(packet.get("generated_counter_signals"))
    for index, item in enumerate(signals):
        if not isinstance(item, Mapping):
            blocked.append(f"missing_counter_signal_id_{index}")
            continue
        if not _compact_text(item.get("counter_signal_id")):
            blocked.append(f"missing_counter_signal_id_{index}")
        if not _compact_text(item.get("seed_id")):
            blocked.append(f"missing_seed_id_{index}")
        counter_type_raw = _compact_text(item.get("counter_signal_type")).lower()
        if counter_type_raw not in _ALLOWED_COUNTER_SIGNAL_TYPES_V1:
            blocked.append(f"invalid_counter_signal_type_{index}")
        if not _compact_text(item.get("counter_signal_summary")):
            blocked.append(f"missing_counter_signal_summary_{index}")
        if not _compact_text(item.get("what_it_challenges")):
            blocked.append(f"missing_counter_signal_challenge_target_{index}")
        if not _compact_text(item.get("expected_breakage")):
            blocked.append(f"missing_expected_breakage_{index}")
        if not _compact_text(item.get("target_uncertainty")):
            blocked.append(f"missing_target_uncertainty_{index}")
        if _safe_bool(item.get("safe_to_reingest_as_metadata", False)) and not _compact_text(item.get("target_uncertainty")):
            blocked.append(f"generated_counter_signal_safe_to_reingest_without_target_uncertainty_{index}")
        blocked.extend(_validate_text_block(f"forbidden_counter_signal_text_{index}", item.get("counter_signal_summary"), item.get("what_it_challenges"), item.get("expected_breakage"), item.get("target_uncertainty")))
        if any(word in _compact_text(item.get("counter_signal_summary") or item.get("what_it_challenges") or item.get("expected_breakage") or item.get("target_uncertainty")).lower() for word in ("proof", "truth", "discovery")):
            blocked.append(f"generated_counter_signal_marked_truth_proof_or_discovery_{index}")
        if _compact_text(item.get("public_claim_status")).lower() not in _ALLOWED_PUBLIC_CLAIM_STATUSES_V1:
            blocked.append(f"invalid_public_claim_status_{index}")
    return blocked


def _validate_probe_signals(packet: Mapping[str, Any]) -> list[str]:
    blocked: list[str] = []
    probes = _ensure_list(packet.get("generated_probe_signals"))
    for index, item in enumerate(probes):
        if not isinstance(item, Mapping):
            blocked.append(f"missing_probe_signal_id_{index}")
            continue
        if not _compact_text(item.get("probe_signal_id")):
            blocked.append(f"missing_probe_signal_id_{index}")
        if not _compact_text(item.get("seed_id")):
            blocked.append(f"missing_seed_id_{index}")
        if not _compact_text(item.get("probe_goal")):
            blocked.append(f"missing_probe_goal_{index}")
        if not _compact_text(item.get("probe_summary")):
            blocked.append(f"missing_probe_summary_{index}")
        if not _compact_text(item.get("expected_observation")):
            blocked.append(f"missing_expected_observation_{index}")
        if not _compact_text(item.get("falsification_condition")):
            blocked.append(f"missing_falsification_condition_{index}")
        if not _compact_text(item.get("next_best_observation")):
            blocked.append(f"missing_next_best_observation_{index}")
        prediction = item.get("calibration_prediction")
        if not isinstance(prediction, Mapping):
            blocked.append(f"missing_calibration_prediction_{index}")
        else:
            required_prediction_fields = (
                "prediction_type",
                "prediction_statement",
                "prediction_scope",
                "confidence_before",
                "confidence_after",
                "outcome_status",
                "calibration_result",
                "uncertainty_factors",
                "invalidation_signals",
                "expected_outcome",
                "future_adjustment",
            )
            if any(field not in prediction for field in required_prediction_fields):
                blocked.append(f"invalid_calibration_prediction_{index}")
            if any(fragment in json.dumps(_json_safe(prediction)).lower() for fragment in ("public claim", "runtime authority", "tool authority", "provider authority", "persistence", ".weslr")):
                blocked.append(f"invalid_calibration_prediction_{index}")
        blocked.extend(_validate_text_block(f"forbidden_probe_text_{index}", item.get("probe_goal"), item.get("probe_summary"), item.get("expected_observation"), item.get("falsification_condition"), item.get("next_best_observation")))
    return blocked


def _validate_turns(packet: Mapping[str, Any]) -> list[str]:
    blocked: list[str] = []
    turns = _ensure_list(packet.get("dialectic_turns"))
    for index, item in enumerate(turns):
        if not isinstance(item, Mapping):
            blocked.append(f"missing_turn_id_{index}")
            continue
        if not _compact_text(item.get("turn_id")):
            blocked.append(f"missing_turn_id_{index}")
        if not _compact_text(item.get("seed_id")):
            blocked.append(f"missing_seed_id_{index}")
        if not isinstance(item.get("turn_index"), int):
            blocked.append(f"missing_turn_index_{index}")
        if _compact_text(item.get("move_type")).lower() not in _ALLOWED_MOVE_TYPES_V1:
            blocked.append(f"missing_move_type_{index}")
        if not _compact_text(item.get("move_summary")):
            blocked.append(f"missing_move_summary_{index}")
        if not _compact_text(item.get("generated_source_signal_ref")):
            blocked.append(f"missing_generated_source_signal_ref_{index}")
        if not _compact_text(item.get("pressure_test_ref")):
            blocked.append(f"missing_pressure_test_ref_{index}")
        if not _compact_text(item.get("calibration_record_ref")):
            blocked.append(f"missing_calibration_record_ref_{index}")
        if not _compact_text(item.get("compressed_lesson")):
            blocked.append(f"missing_compressed_lesson_{index}")
        if not _compact_text(item.get("next_turn_recommendation")):
            blocked.append(f"missing_next_turn_recommendation_{index}")
        turn_text = " ".join(
            [
                _compact_text(item.get("move_summary")),
                _compact_text(item.get("compressed_lesson")),
                _compact_text(item.get("next_turn_recommendation")),
            ]
        ).lower()
        if any(marker in turn_text for marker in ("autonomous loop", "self-run", "self run", "execute loop", "run loop", "live loop")):
            blocked.append(f"dialectic_turn_implies_autonomous_loop_execution_{index}")
        blocked.extend(_validate_text_block(f"forbidden_turn_text_{index}", item.get("move_summary"), item.get("compressed_lesson"), item.get("next_turn_recommendation")))
    return blocked


def _validate_packet_level_authority(packet: Mapping[str, Any]) -> list[str]:
    blocked: list[str] = []
    if _compact_text(packet.get("public_claim_status")).lower() not in _ALLOWED_PUBLIC_CLAIM_STATUSES_V1:
        blocked.append("invalid_public_claim_status")
    if _compact_text(packet.get("public_gap_card_status")).lower() != "public_export_blocked":
        blocked.append("invalid_public_gap_card_status")
    boundary = packet.get("boundary_status")
    if not isinstance(boundary, Mapping) or not boundary:
        blocked.append("unsafe_or_missing_boundary_status")
    else:
        required_false = (
            "runtime_wiring_authority",
            "runtime_authority",
            "tool_authority",
            "provider_authority",
            "provider_model_call_authority",
            "llm_authority",
            "chat_responder_authority",
            "final_answer_generation_authority",
            "public_claim_authority",
            "retrieval_tool_authority",
            "filesystem_authority",
            "network_authority",
            "subprocess_authority",
            "weslr_io_authority",
            "persistence_authority",
            "persistence_database_write_authority",
            "real_memory_mutation_authority",
            "real_project_mutation_authority",
            "behavior_change_authority",
            "behavior_pack_promotion_authority",
            "autonomous_self_modification_authority",
            "official_intelligence_claim_authority",
            "public_discovery_claim_authority",
        )
        for key in required_false:
            if key not in boundary or _safe_bool(boundary.get(key)):
                blocked.append(f"boundary_status_grants_{key}")
    denied = packet.get("denied_authority")
    if not isinstance(denied, Mapping) or not denied:
        blocked.append("unsafe_or_missing_denied_authority")
    else:
        if any(_safe_bool(value) for value in denied.values()):
            blocked.append("unsafe_or_missing_denied_authority")
    safe_metadata = packet.get("safe_metadata")
    if not isinstance(safe_metadata, Mapping) or not safe_metadata:
        blocked.append("unsafe_or_missing_safe_metadata")
    else:
        for key in _SAFE_METADATA_FLAGS_V1:
            if key not in safe_metadata:
                blocked.append("unsafe_or_missing_safe_metadata")
                break
        if not _safe_bool(safe_metadata.get("safe", False)):
            blocked.append("unsafe_or_missing_safe_metadata")
    return blocked


def build_dialectic_loop_packet_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = _merge_payload(payload, **overrides)
    research_mode = _normalize_research_mode(data.get("research_mode") or "internal_exploration")
    input_artifact_ref = _compact_text(data.get("input_artifact_ref") or "artifact:dialectic-loop") or "artifact:dialectic-loop"
    input_artifact_type = _compact_text(data.get("input_artifact_type") or "dialectic-loop-bundle") or "dialectic-loop-bundle"
    input_summary = _compact_text(data.get("input_summary") or data.get("seed_summary") or "metadata-only dialectic loop input") or "metadata-only dialectic loop input"

    raw_seeds = _ensure_list(data.get("dialectic_seed_candidates"))
    if not raw_seeds:
        raw_seeds = [
            {
                "source_engine_name": data.get("source_engine_name") or "unknown_engine",
                "source_run_id": data.get("source_run_id") or f"source-run-{_stable_digest({'input_summary': input_summary})[:12]}",
                "seed_type": data.get("seed_type") or "unknown",
                "seed_summary": input_summary,
                "candidate_claim_or_operator": data.get("candidate_claim_or_operator") or input_summary,
                "known_scope": data.get("known_scope") or "metadata-only scope",
                "failure_scope": data.get("failure_scope") or "bounded failure scope",
                "uncertainty_factors": data.get("uncertainty_factors") or ["candidate remains provisional"],
                "invalidation_signals": data.get("invalidation_signals") or ["not yet invalidated"],
                "public_claim_status": data.get("public_claim_status") or "internal_candidate_only",
            }
        ]

    seed_candidates = [build_dialectic_seed_candidate_v1(seed) for seed in raw_seeds]
    generated_source_signals = _build_generated_source_signals(seed_candidates, research_mode)
    generated_counter_signals = [build_generated_counter_signal_v1({"seed": seed, "counter_signal_type": _SEED_TYPE_TO_COUNTER_SIGNAL_TYPE_V1.get(seed["seed_type"], "unknown")}) for seed in seed_candidates]
    generated_probe_signals = _build_probe_signals(seed_candidates, research_mode)
    rule_pressure_tests = _build_rule_pressure_tests(seed_candidates, generated_source_signals)
    dialectic_turns = _build_turns(seed_candidates, generated_source_signals, rule_pressure_tests, generated_probe_signals)

    hypotheses = [seed["candidate_claim_or_operator"] for seed in seed_candidates]
    predictions = [probe["calibration_prediction"]["prediction_statement"] for probe in generated_probe_signals]
    uncertainty_map = {seed["seed_id"]: {"uncertainty_factors": seed["uncertainty_factors"], "failure_scope": seed["failure_scope"]} for seed in seed_candidates}
    confidence_map = {seed["seed_id"]: 0.65 - (index * 0.05) for index, seed in enumerate(seed_candidates)}
    falsification_probes = [probe["falsification_condition"] for probe in generated_probe_signals]
    probes = [
        {
            "probe_signal_id": probe["probe_signal_id"],
            "seed_id": probe["seed_id"],
            "probe_goal": probe["probe_goal"],
            "probe_summary": probe["probe_summary"],
            "expected_observation": probe["expected_observation"],
            "falsification_condition": probe["falsification_condition"],
            "next_best_observation": probe["next_best_observation"],
        }
        for probe in generated_probe_signals
    ]
    outcomes = [
        {
            "seed_id": seed["seed_id"],
            "outcome_status": "not_observed_yet",
            "observed_result_summary": "metadata-only; not observed yet",
            "counter_signal_type": generated_counter_signals[index]["counter_signal_type"],
            "pressure_test_ref": rule_pressure_tests[index]["pressure_test_id"],
        }
        for index, seed in enumerate(seed_candidates)
    ]
    corrections = [
        {
            "correction_id": f"correction-{seed['seed_id']}",
            "seed_id": seed["seed_id"],
            "turn_id": dialectic_turns[index]["turn_id"],
            "compressed_lesson": dialectic_turns[index]["compressed_lesson"],
            "future_adjustment": dialectic_turns[index]["next_turn_recommendation"],
            "calibration_record_ref": dialectic_turns[index]["calibration_record_ref"],
        }
        for index, seed in enumerate(seed_candidates)
    ]
    next_experiments = [turn["next_turn_recommendation"] for turn in dialectic_turns]
    suggestion_store_updates = [
        {
            "suggestion_id": f"suggestion-{seed['seed_id']}",
            "seed_id": seed["seed_id"],
            "update_summary": f"Use {seed['seed_type']} as a bounded generation starting point.",
            "next_experiment": next_experiments[index],
        }
        for index, seed in enumerate(seed_candidates)
    ]

    calibration_source_run = {
        "run_id": _compact_text(data.get("run_id")) or f"dialectic-run-{_stable_digest({'input_artifact_ref': input_artifact_ref, 'input_summary': input_summary})[:12]}",
        "engine_name": ENGINE_NAME_V1,
        "engine_family": ENGINE_FAMILY_V1,
        "research_mode": research_mode,
        "source_scope": "metadata_only",
        "input_artifact_ref": input_artifact_ref,
        "input_artifact_type": input_artifact_type,
        "input_summary": input_summary,
        "hypotheses": hypotheses,
        "predictions": predictions,
        "probes": falsification_probes,
        "outcomes": outcomes,
        "corrections": corrections,
        "compressed_lesson": _compact_text(data.get("compressed_lesson") or "Dialectic generation stays metadata-only until observed.") or "Dialectic generation stays metadata-only until observed.",
    }
    calibration_record = data.get("calibration_record")
    if not isinstance(calibration_record, Mapping):
        first_probe = generated_probe_signals[0] if generated_probe_signals else {}
        calibration_record = {
            "record_id": f"calibration-{_stable_digest({'input_artifact_ref': input_artifact_ref, 'first_probe': first_probe.get('probe_summary', input_summary)})[:12]}",
            "prediction_type": _compact_text(first_probe.get("calibration_prediction", {}).get("prediction_type") if isinstance(first_probe.get("calibration_prediction"), Mapping) else data.get("prediction_type") or "probe_prediction") or "probe_prediction",
            "prediction_statement": _compact_text(first_probe.get("probe_summary") or input_summary) or input_summary,
            "prediction_scope": _compact_text(seed_candidates[0]["known_scope"] if seed_candidates else "metadata-only scope") or "metadata-only scope",
            "confidence_before": 0.65,
            "confidence_after": 0.55,
            "confidence_basis": "metadata-only bridge basis",
            "uncertainty_factors": seed_candidates[0]["uncertainty_factors"] if seed_candidates else ["prediction unresolved"],
            "invalidation_signals": seed_candidates[0]["invalidation_signals"] if seed_candidates else ["not_observed_yet"],
            "expected_outcome": _compact_text(first_probe.get("expected_observation") or input_summary) or input_summary,
            "observed_outcome": "",
            "outcome_status": "not_observed_yet",
            "calibration_result": "not_yet_calibrated",
            "error_type": "none",
            "assumptions_used": [seed_candidates[0]["candidate_claim_or_operator"]] if seed_candidates else ["candidate rule"],
            "assumptions_failed": [],
            "missing_signals": [],
            "conflicting_signals": [],
            "correction": "",
            "compressed_lesson": _compact_text(data.get("compressed_lesson") or "") or "",
            "future_adjustment": "keep calibration metadata-only",
        }

    source_signal = data.get("source_signal")
    if not isinstance(source_signal, Mapping):
        source_signal = build_source_signal_metadata_v1(
            {
                "source_ref": input_artifact_ref,
                "summary": input_summary,
                "source_scope": "metadata_only",
                "engine_name": ENGINE_NAME_V1,
                "signal_type": "dialectic_loop_input",
                "raw_content_included": False,
            },
            engine_name=ENGINE_NAME_V1,
            source_ref=input_artifact_ref,
            summary=input_summary,
            source_scope="metadata_only",
        )

    packet = build_cognitive_research_run_v1(
        {
            "schema_version": SCHEMA_VERSION_V1,
            "run_id": calibration_source_run["run_id"],
            "engine_name": ENGINE_NAME_V1,
            "engine_family": ENGINE_FAMILY_V1,
            "research_mode": research_mode,
            "source_scope": "metadata_only",
            "input_artifact_ref": input_artifact_ref,
            "input_artifact_type": input_artifact_type,
            "input_summary": input_summary,
            "source_signal": source_signal,
            "observations": [seed["seed_summary"] for seed in seed_candidates],
            "extracted_signals": [signal["generated_signal_summary"] for signal in generated_source_signals],
            "motif_candidates": [seed["seed_summary"] for seed in seed_candidates if seed["seed_type"] == "motif_candidate"],
            "operator_candidates": [seed["candidate_claim_or_operator"] for seed in seed_candidates if seed["seed_type"] in {"operator_candidate", "translation_candidate"}],
            "invariant_candidates": [seed["candidate_claim_or_operator"] for seed in seed_candidates if seed["seed_type"] == "structural_match_candidate"],
            "resonance_candidates": [seed["seed_summary"] for seed in seed_candidates if seed["seed_type"] in {"motif_candidate", "gap_hypothesis"}],
            "nonlinear_inspiration_candidates": [seed["candidate_claim_or_operator"] for seed in seed_candidates if seed["seed_type"] in {"operator_candidate", "gap_hypothesis"}],
            "hypotheses": hypotheses,
            "predictions": predictions,
            "confidence_map": confidence_map,
            "uncertainty_map": uncertainty_map,
            "verification_steps": ["generate seed", "mutate signal", "pressure test", "calibrate", "compress", "recommend next experiment"],
            "human_verification_steps": ["owner preview review"],
            "machine_verification_steps": ["py_compile", "pytest", "release_gate", "release_check"],
            "falsification_probes": falsification_probes,
            "probes": probes,
            "mutations": [signal["generated_signal_summary"] for signal in generated_source_signals],
            "generated_source_signals": generated_source_signals,
            "rule_pressure_tests": rule_pressure_tests,
            "outcomes": outcomes,
            "corrections": corrections,
            "compressed_lesson": _compact_text(data.get("compressed_lesson") or "Dialectic generation stays metadata-only until observed.") or "Dialectic generation stays metadata-only until observed.",
            "next_experiments": next_experiments,
            "suggestion_store_updates": suggestion_store_updates,
            "calibration_record": calibration_record,
            "public_claim_status": _normalize_public_claim_status(data.get("public_claim_status") or "internal_candidate_only"),
            "public_gap_card_status": _normalize_public_claim_status(data.get("public_gap_card_status") or "public_export_blocked", "public_export_blocked"),
            "boundary_status": data.get("boundary_status") or _default_boundary_status(),
            "denied_authority": data.get("denied_authority") or build_default_cognitive_research_denied_authority_v1(),
            "safe_metadata": data.get("safe_metadata") or _default_safe_metadata(ENGINE_NAME_V1, ENGINE_FAMILY_V1, research_mode),
            "domain": _compact_text(data.get("domain") or "recursive research") or "recursive research",
            "domain_subtype": _compact_text(data.get("domain_subtype") or "dialectic generator loop") or "dialectic generator loop",
            "system_level": _compact_text(data.get("system_level") or "component") or "component",
            "artifact_scale": _compact_text(data.get("artifact_scale") or "bounded artifact") or "bounded artifact",
            "constraint_map": data.get("constraint_map") or {
                "runtime": "denied",
                "tool": "denied",
                "provider": "denied",
                "search": "denied",
                "persistence": "denied",
                "public_claims": "blocked",
                "answer_authority": "denied",
            },
            "safety_boundary": data.get("safety_boundary") or {"mode": "metadata_only", "non_actionable": True},
            "hazard_flags": data.get("hazard_flags") or [],
            "validation_route": data.get("validation_route") or ["metadata_only_validation", "fail_closed_safety_validation", "json_safe_copy_validation"],
            "required_expert_review": _safe_bool(data.get("required_expert_review", False)),
            "source_requirements": data.get("source_requirements") or {"provenance_required": True, "raw_storage_allowed": False, "side_effect_free": True},
            "experiment_type": _compact_text(data.get("experiment_type") or "metadata_only") or "metadata_only",
            "simulation_before_real_world": _safe_bool(data.get("simulation_before_real_world", True)),
            "non_actionable_research_only": _safe_bool(data.get("non_actionable_research_only", True)),
            "forbidden_action_notes": data.get("forbidden_action_notes") or [],
            "cross_domain_analogies": data.get("cross_domain_analogies") or [],
            "candidate_transfer_patterns": data.get("candidate_transfer_patterns") or [],
            "failure_mode_map": data.get("failure_mode_map") or [],
            "measurement_gap_map": data.get("measurement_gap_map") or [],
            "operator_gap_map": data.get("operator_gap_map") or [],
            "language_gap_map": data.get("language_gap_map") or [],
            "unknown_unknowns": data.get("unknown_unknowns") or [],
        }
    )
    packet.update(
        {
            "dialectic_seed_candidates": seed_candidates,
            "generated_counter_signals": generated_counter_signals,
            "dialectic_turns": dialectic_turns,
        }
    )
    return _json_safe(packet)


def _dialectic_summary_text(packet: Mapping[str, Any], blocked: bool, blocked_labels: list[str]) -> str:
    engine_name = _compact_text(packet.get("engine_name")) or ENGINE_NAME_V1
    engine_family = _compact_text(packet.get("engine_family")) or ENGINE_FAMILY_V1
    research_mode = _normalize_research_mode(packet.get("research_mode"))
    seed_count = len(_ensure_list(packet.get("dialectic_seed_candidates")))
    turn_types = ",".join(
        _compact_text(turn.get("move_type"))
        for turn in _ensure_list(packet.get("dialectic_turns"))
        if isinstance(turn, Mapping)
    )
    public_status = _normalize_public_claim_status(packet.get("public_claim_status") or "internal_candidate_only")
    gap_status = _normalize_public_claim_status(packet.get("public_gap_card_status") or "public_export_blocked", "public_export_blocked")
    summary = (
        f"Dialectic loop: engine={engine_name}; family={engine_family}; mode={research_mode}; "
        f"seeds={seed_count}; turns={turn_types or 'none'}; public={public_status}; gap_card={gap_status}."
    )
    if blocked:
        preview = ", ".join(blocked_labels[:4])
        return f"Blocked dialectic loop: {preview or 'validation failed'}. {summary}"
    return summary


def validate_dialectic_loop_packet_v1(packet: Any) -> dict[str, Any]:
    raw = packet if isinstance(packet, Mapping) else {}
    validation = validate_cognitive_research_run_v1(packet)
    blocked_labels = list(validation["blocked_labels"])
    if _compact_text(raw.get("engine_name")) != ENGINE_NAME_V1:
        blocked_labels.append("invalid_engine_name")
    if _compact_text(raw.get("engine_family")) != ENGINE_FAMILY_V1:
        blocked_labels.append("invalid_engine_family")
    if _compact_text(raw.get("research_mode")).lower() not in _ALLOWED_RESEARCH_MODES_V1:
        blocked_labels.append("invalid_research_mode")
    blocked_labels.extend(_validate_packet_level_authority(raw))
    blocked_labels.extend(_validate_seed_candidates(raw))
    blocked_labels.extend(_validate_counter_signals(raw))
    blocked_labels.extend(_validate_turns(raw))
    if _contains_forbidden_text(raw.get("compressed_lesson")):
        blocked_labels.append("forbidden_packet_text")
    blocked = bool(blocked_labels)
    summary_text = _dialectic_summary_text(raw, blocked, blocked_labels)
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "helper_type": HELPER_TYPE_V1,
        "blocked": blocked,
        "blocked_labels": blocked_labels,
        "classification": ENGINE_NAME_V1 if not blocked else "invalid",
        "engine_name": ENGINE_NAME_V1,
        "engine_family": ENGINE_FAMILY_V1,
        "research_mode": _normalize_research_mode(raw.get("research_mode")),
        "public_claim_status": _normalize_public_claim_status(raw.get("public_claim_status") or "internal_candidate_only"),
        "public_gap_card_status": _normalize_public_claim_status(raw.get("public_gap_card_status") or "public_export_blocked", "public_export_blocked"),
        "llm_helper_role": validation["llm_helper_role"],
        "boundary_status": validation["boundary_status"],
        "summary_text": summary_text[:320],
        "packet": to_dialectic_loop_json_safe_v1(packet),
    }


def summarize_dialectic_loop_packet_v1(packet: Any) -> dict[str, Any]:
    validation = validate_dialectic_loop_packet_v1(packet)
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "helper_type": HELPER_TYPE_V1,
        "summary_text": _dialectic_summary_text(validation["packet"], validation["blocked"], validation["blocked_labels"])[:320],
        "blocked": validation["blocked"],
        "blocked_labels": validation["blocked_labels"],
        "classification": validation["classification"],
        "engine_name": validation["engine_name"],
        "engine_family": validation["engine_family"],
        "research_mode": validation["research_mode"],
        "public_claim_status": validation["public_claim_status"],
        "public_gap_card_status": validation["public_gap_card_status"],
        "llm_helper_role": validation["llm_helper_role"],
        "boundary_status": validation["boundary_status"],
        "packet": validation["packet"],
    }


def to_dialectic_loop_json_safe_v1(packet: Any) -> Any:
    return _strip_unsafe_copy_fields(packet)


def build_initial_dialectic_loop_examples_v1() -> list[dict[str, Any]]:
    specs = [
        {
            "engine_name": ENGINE_NAME_V1,
            "research_mode": "internal_exploration",
            "input_artifact_ref": "artifact:dialectic-hidden-rule-001",
            "input_artifact_type": "signal-log",
            "input_summary": "Hidden-rule loop with a bounded contradiction cloud.",
            "dialectic_seed_candidates": [
                {
                    "seed_id": "seed-hidden-rule-001",
                    "source_engine_name": "unknown_engine",
                    "source_run_id": "run-hidden-rule-001",
                    "seed_type": "hidden_rule_candidate",
                    "seed_summary": "Hidden rule candidate with a narrow scope.",
                    "candidate_claim_or_operator": "candidate rule",
                    "known_scope": "bounded metadata-only scope",
                    "failure_scope": "narrow failure scope",
                    "uncertainty_factors": ["hidden rule remains provisional"],
                    "invalidation_signals": ["no invalidation observed yet"],
                    "public_claim_status": "internal_candidate_only",
                }
            ],
        },
        {
            "engine_name": ENGINE_NAME_V1,
            "research_mode": "synthetic_test",
            "input_artifact_ref": "artifact:dialectic-operator-001",
            "input_artifact_type": "sequence",
            "input_summary": "Transferred-operator loop with a resonance bridge.",
            "dialectic_seed_candidates": [
                {
                    "seed_id": "seed-operator-001",
                    "source_engine_name": "nonlinear_inspiration_engine",
                    "source_run_id": "run-operator-001",
                    "seed_type": "operator_candidate",
                    "seed_summary": "Transferred operator candidate from resonance analysis.",
                    "candidate_claim_or_operator": "bridge operator",
                    "known_scope": "adjacent domain",
                    "failure_scope": "bridge failure scope",
                    "uncertainty_factors": ["analogy may break under pressure"],
                    "invalidation_signals": ["bridge not yet tested"],
                    "public_claim_status": "not_public_claim",
                }
            ],
        },
        {
            "engine_name": ENGINE_NAME_V1,
            "research_mode": "calibration_replay",
            "input_artifact_ref": "artifact:dialectic-translation-001",
            "input_artifact_type": "packet",
            "input_summary": "Translation loop with competing interpretations.",
            "dialectic_seed_candidates": [
                {
                    "seed_id": "seed-translation-001",
                    "source_engine_name": "unintelligible_output_analyzer",
                    "source_run_id": "run-translation-001",
                    "seed_type": "translation_candidate",
                    "seed_summary": "Translation candidate from an unintelligible operator sequence.",
                    "candidate_claim_or_operator": "candidate translation layer",
                    "known_scope": "bounded translation scope",
                    "failure_scope": "translation boundary",
                    "uncertainty_factors": ["translation remains provisional"],
                    "invalidation_signals": ["translation not yet pinned"],
                    "public_claim_status": "internal_candidate_only",
                }
            ],
        },
        {
            "engine_name": ENGINE_NAME_V1,
            "research_mode": "frontier_mapping",
            "input_artifact_ref": "artifact:dialectic-signal-noise-001",
            "input_artifact_type": "signal",
            "input_summary": "Signal/noise loop with a weak motif candidate.",
            "dialectic_seed_candidates": [
                {
                    "seed_id": "seed-signal-noise-001",
                    "source_engine_name": "raw_signal_cartographer",
                    "source_run_id": "run-signal-noise-001",
                    "seed_type": "motif_candidate",
                    "seed_summary": "Motif candidate within a noisy signal stream.",
                    "candidate_claim_or_operator": "recurring motif",
                    "known_scope": "signal-bounded scope",
                    "failure_scope": "noise boundary",
                    "uncertainty_factors": ["weak signal may vanish under pressure"],
                    "invalidation_signals": ["motif not yet isolated"],
                    "public_claim_status": "public_export_blocked",
                }
            ],
        },
    ]
    return [build_dialectic_loop_packet_v1(spec) for spec in specs]