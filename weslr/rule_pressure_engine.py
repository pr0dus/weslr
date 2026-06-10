"""Metadata-only Rule Pressure Engine V1 helpers.

This engine pressure-tests candidate rules, operators, hypotheses, translations,
and resonance mappings without runtime wiring, provider calls, tool execution,
.persistence, or public-claim authority. It stays deterministic, JSON-safe,
and fail-closed.
"""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from typing import Any, Mapping

from weslr.cognitive_research_protocol import (
    ALLOWED_COGNITIVE_RESEARCH_PUBLIC_CLAIM_STATUSES_V1,
    ALLOWED_COGNITIVE_RESEARCH_RESEARCH_MODES_V1,
    build_cognitive_research_run_v1,
    build_default_cognitive_research_denied_authority_v1,
    build_rule_pressure_test_metadata_v1,
    summarize_cognitive_research_run_v1,
    to_cognitive_research_json_safe_v1,
    validate_cognitive_research_run_v1,
)
from weslr.forecast_calibration_bridge import (
    build_forecast_calibration_packet_from_research_run_v1,
    validate_forecast_calibration_record_v1,
)

HELPER_TYPE_V1 = "weslr_rule_pressure_engine_v1"
SCHEMA_VERSION_V1 = "rule_pressure_engine_v1"
ENGINE_NAME_V1 = "rule_pressure_engine"
ENGINE_FAMILY_V1 = "adversarial_pressure"

_ALLOWED_TARGET_TYPES_V1 = (
    "hidden_rule",
    "operator_candidate",
    "translation_candidate",
    "structural_match",
    "motif_candidate",
    "gap_hypothesis",
    "prediction",
    "toy_model",
    "unknown",
)

_ALLOWED_PRESSURE_TYPES_V1 = (
    "counterexample_search",
    "boundary_case",
    "noise_injection",
    "false_pattern_insertion",
    "scale_shift",
    "delayed_causality",
    "operator_substitution",
    "axiom_mutation",
    "contradiction_injection",
    "control_case",
    "randomized_stress",
    "unknown",
)

_ALLOWED_RESULT_STATUSES_V1 = (
    "not_observed_yet",
    "survived_pressure",
    "partially_survived",
    "failed_pressure",
    "contradicted",
    "inconclusive",
    "blocked",
    "out_of_scope",
)

_ALLOWED_BREAKAGE_TYPES_V1 = (
    "none",
    "scope_failure",
    "hidden_assumption_failure",
    "noise_fragility",
    "scale_fragility",
    "operator_fragility",
    "translation_fragility",
    "false_pattern_dependency",
    "delayed_causality_failure",
    "contradiction_exposed",
    "control_case_failure",
    "unknown",
)

_ALLOWED_PUBLIC_CLAIM_STATUSES_V1 = (
    "not_public_claim",
    "internal_candidate_only",
    "public_export_blocked",
)

_FORBIDDEN_TEXT_MARKERS_V1 = (
    "raw private text",
    "raw private data",
    "hidden prompt",
    "system prompt",
    "developer prompt",
    "secret",
    "password",
    "api key",
    "final answer",
    "proof",
    "breakthrough",
    "official intelligence",
    "agi",
    "sentience",
    "consciousness",
    "llm authority",
    "runtime authority",
    "tool authority",
    "provider authority",
    "persistence",
    ".weslr",
    "live ingestion",
    "network",
    "github rss",
    "lab notebook",
    "memory mutation authority",
    "project mutation authority",
    "behavior change authority",
    "behavior pack",
    "promotion",
    "executable code-as-action",
)

_FORBIDDEN_KEY_FRAGMENTS_V1 = (
    "raw_prompt",
    "raw_response",
    "raw_observation",
    "hidden_prompt",
    "private_blob",
    "private_content",
    "raw_artifact",
    "raw_payload",
    "secret",
    "password",
    "api_key",
    "answer_draft",
    "reply_output",
    "preview_output",
    "final_answer",
)

_REQUIRED_SAFE_METADATA_FLAGS_V1 = (
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
    "no_public_claims",
    "no_final_answer",
    "no_weslr_io",
    "no_network",
    "no_subprocess",
    "no_autonomous_self_modification",
    "perspicuity_is_not_a_gate",
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
        return sorted(list(value), key=_compact_text)
    if isinstance(value, Mapping):
        return list(value.values())
    return [value]


def _safe_bool(value: Any) -> bool:
    return bool(value) is True


def _json_safe(value: Any) -> Any:
    if isinstance(value, Mapping):
        out: dict[str, Any] = {}
        for key in sorted(value.keys(), key=lambda item: str(item)):
            key_text = str(key)
            key_lc = key_text.lower()
            if key_lc in _FORBIDDEN_KEY_FRAGMENTS_V1 or key_lc.startswith("raw_"):
                continue
            out[key_text] = _json_safe(value[key])
        return out
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, set):
        return [_json_safe(item) for item in sorted(value, key=_compact_text)]
    if isinstance(value, str):
        text = value
        if any(marker in text.lower() for marker in _FORBIDDEN_TEXT_MARKERS_V1):
            return "[redacted]"
        return text
    if isinstance(value, (int, float, bool)) or value is None:
        return value
    return _compact_text(value)


def _stable_digest(payload: Mapping[str, Any]) -> str:
    blob = json.dumps(_json_safe(payload), sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _normalize_choice(value: Any, allowed: tuple[str, ...], default: str) -> str:
    text = _compact_text(value).lower()
    return text if text in allowed else default


def _normalize_target_status(value: Any) -> str:
    return _normalize_choice(value, _ALLOWED_PUBLIC_CLAIM_STATUSES_V1, "not_public_claim")


def _normalize_pressure_type(value: Any) -> str:
    return _normalize_choice(value, _ALLOWED_PRESSURE_TYPES_V1, "unknown")


def _normalize_result_status(value: Any) -> str:
    return _normalize_choice(value, _ALLOWED_RESULT_STATUSES_V1, "not_observed_yet")


def _normalize_breakage_type(value: Any) -> str:
    return _normalize_choice(value, _ALLOWED_BREAKAGE_TYPES_V1, "none")


def _normalize_target_type(value: Any) -> str:
    return _normalize_choice(value, _ALLOWED_TARGET_TYPES_V1, "unknown")


def _iter_text_values(value: Any):
    if isinstance(value, Mapping):
        for item in value.values():
            yield from _iter_text_values(item)
    elif isinstance(value, (list, tuple, set)):
        for item in value:
            yield from _iter_text_values(item)
    elif value is not None:
        yield _compact_text(value)


def _has_forbidden_markers(value: Any) -> bool:
    blob = "\n".join(_iter_text_values(value)).lower()
    return any(marker in blob for marker in _FORBIDDEN_TEXT_MARKERS_V1)


def _make_default_safe_metadata(engine_name: str, engine_family: str, research_mode: str) -> dict[str, Any]:
    return {
        "safe": True,
        "metadata_only": True,
        "json_safe": True,
        "non_public": True,
        "no_runtime_wiring": True,
        "no_provider_calls": True,
        "no_tool_execution": True,
        "no_retrieval_execution": True,
        "no_persistence": True,
        "no_memory_mutation": True,
        "no_project_mutation": True,
        "no_public_claims": True,
        "no_final_answer": True,
        "no_weslr_io": True,
        "no_network": True,
        "no_subprocess": True,
        "no_autonomous_self_modification": True,
        "perspicuity_is_not_a_gate": True,
        "generator_loop": "RecursiveDiscoveryLoopV1",
        "engine_name": engine_name,
        "engine_family": engine_family,
        "research_mode": research_mode,
    }


def _make_default_boundary_status() -> dict[str, Any]:
    denied = build_default_cognitive_research_denied_authority_v1()
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
        "boundary_notes": "metadata-only; fail closed; no runtime, provider, tool, storage, or public-export authority",
        "denied_authority": denied,
    }


def _map_result_status_to_outcome_status(result_status: str) -> str:
    mapping = {
        "not_observed_yet": "not_observed_yet",
        "survived_pressure": "matched",
        "partially_survived": "partially_matched",
        "failed_pressure": "failed",
        "contradicted": "contradicted",
        "inconclusive": "inconclusive",
        "blocked": "blocked",
        "out_of_scope": "out_of_scope",
    }
    return mapping.get(result_status, "inconclusive")


def _map_result_status_to_calibration_result(result_status: str) -> str:
    mapping = {
        "not_observed_yet": "not_yet_calibrated",
        "survived_pressure": "well_calibrated",
        "partially_survived": "ambiguous",
        "failed_pressure": "wrong_model",
        "contradicted": "wrong_model",
        "inconclusive": "missing_signal",
        "blocked": "scope_error",
        "out_of_scope": "scope_error",
    }
    return mapping.get(result_status, "missing_signal")


def build_rule_pressure_target_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = _merge_payload(payload, **overrides)
    source_engine_name = _compact_text(data.get("source_engine_name")).lower()
    source_run_id = _compact_text(data.get("source_run_id"))
    target_type = _normalize_target_type(data.get("target_type"))
    target_summary = _compact_text(data.get("target_summary") or data.get("input_summary") or "metadata-only rule pressure target")
    candidate_rule_or_operator = _compact_text(data.get("candidate_rule_or_operator") or data.get("candidate_rule") or data.get("candidate_operator") or "candidate rule or operator")
    claimed_scope = _compact_text(data.get("claimed_scope") or "bounded claim")
    known_scope = _compact_text(data.get("known_scope") or "metadata-only scope")
    uncertainty_factors = _ensure_list(data.get("uncertainty_factors")) or ["scope may shift under pressure"]
    invalidation_signals = _ensure_list(data.get("invalidation_signals")) or ["no invalidation observed yet"]
    public_claim_status = _normalize_target_status(data.get("public_claim_status"))
    target_id = _compact_text(data.get("target_id"))
    if not target_id:
        target_id = f"rp-target-{_stable_digest({'source_engine_name': source_engine_name, 'source_run_id': source_run_id, 'target_type': target_type, 'candidate_rule_or_operator': candidate_rule_or_operator, 'target_summary': target_summary})[:12]}"
    return _json_safe({
        "target_id": target_id,
        "source_engine_name": source_engine_name or ENGINE_NAME_V1,
        "source_run_id": source_run_id or f"source-run-{_stable_digest({'target_id': target_id, 'target_type': target_type})[:12]}",
        "target_type": target_type,
        "target_summary": target_summary,
        "candidate_rule_or_operator": candidate_rule_or_operator,
        "claimed_scope": claimed_scope,
        "known_scope": known_scope,
        "uncertainty_factors": uncertainty_factors,
        "invalidation_signals": invalidation_signals,
        "public_claim_status": public_claim_status,
        "source_engine_family": _compact_text(data.get("source_engine_family") or ""),
        "source_summary": _compact_text(data.get("source_summary") or data.get("input_summary") or "metadata-only source"),
        "target_notes": _compact_text(data.get("target_notes") or "metadata-only rule pressure target"),
    })


def build_rule_pressure_test_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = _merge_payload(payload, **overrides)
    target = data.get("target") if isinstance(data.get("target"), Mapping) else {}
    target_id = _compact_text(data.get("target_id") or target.get("target_id"))
    target_rule_or_operator = _compact_text(data.get("target_rule_or_operator") or target.get("candidate_rule_or_operator") or target.get("target_summary") or "candidate rule or operator")
    pressure_type = _normalize_pressure_type(data.get("pressure_type"))
    pressure_test_id = _compact_text(data.get("pressure_test_id"))
    if not pressure_test_id:
        pressure_test_id = f"rp-test-{_stable_digest({'target_id': target_id, 'pressure_type': pressure_type, 'target_rule_or_operator': target_rule_or_operator})[:12]}"
    pressure_summary = _compact_text(data.get("pressure_summary") or f"Pressure test for {target_rule_or_operator} using {pressure_type}.")
    input_mutation = _compact_text(data.get("input_mutation") or data.get("mutated_input_summary") or "metadata-only mutation")
    expected_failure_mode = _normalize_breakage_type(data.get("expected_failure_mode") or data.get("failure_mode") or "unknown")
    control_case_summary = _compact_text(data.get("control_case_summary") or "Control case preserves the baseline claim.")
    success_criteria = _compact_text(data.get("success_criteria") or data.get("expected_behavior") or "pressure reveals bounded weakness without leaving metadata-only scope")
    failure_criteria = _compact_text(data.get("failure_criteria") or "pressure leaves the candidate unchanged without evidence")
    if not failure_criteria:
        failure_criteria = "pressure leaves the candidate unchanged without evidence"
    calibration_prediction = data.get("calibration_prediction")
    if not isinstance(calibration_prediction, Mapping):
        calibration_prediction = {
            "prediction_type": "rule_pressure_prediction",
            "prediction_statement": f"Pressure against {target_rule_or_operator} may reveal {expected_failure_mode}.",
            "prediction_scope": _compact_text(data.get("prediction_scope") or target.get("known_scope") or target.get("claimed_scope") or "metadata-only scope"),
            "confidence_before": 0.6,
            "confidence_basis": "metadata-only pressure scaffold",
            "uncertainty_factors": _ensure_list(target.get("uncertainty_factors") or data.get("uncertainty_factors")) or ["scope may shift under pressure"],
            "invalidation_signals": _ensure_list(target.get("invalidation_signals") or data.get("invalidation_signals")) or ["no invalidation observed yet"],
            "expected_outcome": success_criteria,
            "outcome_status": "not_observed_yet",
            "calibration_result": "not_yet_calibrated",
            "error_type": "none",
            "assumptions_used": [target_rule_or_operator],
            "assumptions_failed": [],
            "missing_signals": [],
            "conflicting_signals": [],
            "correction": "",
            "compressed_lesson": "",
            "confidence_after": 0.6,
            "future_adjustment": "keep pressure metadata-only",
            "behavior_change_authorized": False,
            "memory_mutation_authorized": False,
            "project_mutation_authorized": False,
            "public_claim_authorized": False,
            "denied_authority": build_default_cognitive_research_denied_authority_v1(),
            "safe_metadata": _make_default_safe_metadata(ENGINE_NAME_V1, ENGINE_FAMILY_V1, "synthetic_test"),
        }
    safe_to_run_as_metadata = _safe_bool(data.get("safe_to_run_as_metadata", True))
    return _json_safe({
        "pressure_test_id": pressure_test_id,
        "target_id": target_id,
        "pressure_type": pressure_type,
        "pressure_summary": pressure_summary,
        "input_mutation": input_mutation,
        "expected_failure_mode": expected_failure_mode,
        "control_case_summary": control_case_summary,
        "success_criteria": success_criteria,
        "failure_criteria": failure_criteria,
        "calibration_prediction": calibration_prediction,
        "safe_to_run_as_metadata": safe_to_run_as_metadata,
        "test_id": pressure_test_id,
        "target_rule_or_operator": target_rule_or_operator,
        "mutated_input_summary": input_mutation,
        "expected_behavior": success_criteria,
        "observed_behavior": _compact_text(data.get("observed_behavior") or "not_observed_yet"),
        "result": _compact_text(data.get("result") or "pending"),
        "failure_mode": _compact_text(data.get("failure_mode") or expected_failure_mode),
        "scope_update": _compact_text(data.get("scope_update") or "metadata_only"),
    })


def build_rule_pressure_result_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = _merge_payload(payload, **overrides)
    pressure_test_id = _compact_text(data.get("pressure_test_id"))
    target_id = _compact_text(data.get("target_id"))
    result_status = _normalize_result_status(data.get("result_status"))
    pressure_result_id = _compact_text(data.get("pressure_result_id"))
    if not pressure_result_id:
        pressure_result_id = f"rp-result-{_stable_digest({'pressure_test_id': pressure_test_id, 'target_id': target_id, 'result_status': result_status})[:12]}"
    observed_result_summary = _compact_text(data.get("observed_result_summary") or data.get("result_summary") or ("not observed yet" if result_status == "not_observed_yet" else "metadata-only observation"))
    target_survived = _safe_bool(data.get("target_survived", result_status in {"survived_pressure", "partially_survived"}))
    breakage_detected = _safe_bool(data.get("breakage_detected", result_status in {"failed_pressure", "contradicted"}))
    breakage_type = _normalize_breakage_type(data.get("breakage_type") or ("none" if not breakage_detected else "unknown"))
    scope_changed = _safe_bool(data.get("scope_changed", breakage_detected))
    new_uncertainty = _ensure_list(data.get("new_uncertainty")) or (["none"] if result_status == "not_observed_yet" else ["scope may have shifted"])
    new_invalidation_signal = _compact_text(data.get("new_invalidation_signal") or data.get("new_invalidation_signals") or ("none" if result_status == "not_observed_yet" else "candidate invalidation introduced"))
    calibration_outcome_status = _compact_text(data.get("calibration_outcome_status") or _map_result_status_to_calibration_result(result_status))
    return _json_safe({
        "pressure_result_id": pressure_result_id,
        "pressure_test_id": pressure_test_id,
        "observed_result_summary": observed_result_summary,
        "target_survived": target_survived,
        "breakage_detected": breakage_detected,
        "breakage_type": breakage_type,
        "scope_changed": scope_changed,
        "new_uncertainty": new_uncertainty,
        "new_invalidation_signal": new_invalidation_signal,
        "calibration_outcome_status": calibration_outcome_status,
        "result_status": result_status,
    })


def build_rule_pressure_correction_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = _merge_payload(payload, **overrides)
    breakage_type = _normalize_breakage_type(data.get("breakage_type"))
    correction_id = _compact_text(data.get("correction_id"))
    target_id = _compact_text(data.get("target_id"))
    pressure_test_id = _compact_text(data.get("pressure_test_id"))
    if not correction_id:
        correction_id = f"rp-correction-{_stable_digest({'target_id': target_id, 'pressure_test_id': pressure_test_id, 'breakage_type': breakage_type})[:12]}"
    failed_assumption = _compact_text(data.get("failed_assumption") or "candidate assumption")
    corrected_scope = _compact_text(data.get("corrected_scope") or data.get("scope_update") or "")
    model_update_summary = _compact_text(data.get("model_update_summary") or "metadata-only model update")
    compressed_lesson = _compact_text(data.get("compressed_lesson") or "Pressure revealed a bounded failure mode; keep the scope narrow.")
    future_pressure_adjustment = _compact_text(data.get("future_pressure_adjustment") or "tighten future pressure with a narrower control case")
    calibration_record_ref = _compact_text(data.get("calibration_record_ref") or data.get("calibration_record_id") or "")
    return _json_safe({
        "correction_id": correction_id,
        "target_id": target_id,
        "pressure_test_id": pressure_test_id,
        "breakage_type": breakage_type,
        "failed_assumption": failed_assumption,
        "corrected_scope": corrected_scope,
        "model_update_summary": model_update_summary,
        "compressed_lesson": compressed_lesson,
        "future_pressure_adjustment": future_pressure_adjustment,
        "calibration_record_ref": calibration_record_ref,
    })


def build_rule_pressure_packet_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = _merge_payload(payload, **overrides)
    research_mode = _normalize_choice(data.get("research_mode"), tuple(ALLOWED_COGNITIVE_RESEARCH_RESEARCH_MODES_V1), "internal_exploration")
    public_claim_status = _normalize_choice(data.get("public_claim_status"), tuple(ALLOWED_COGNITIVE_RESEARCH_PUBLIC_CLAIM_STATUSES_V1), "internal_candidate_only")
    public_gap_card_status = _compact_text(data.get("public_gap_card_status") or "public_export_blocked") or "public_export_blocked"
    source_engine_name = _compact_text(data.get("source_engine_name") or data.get("upstream_engine_name") or "unknown_engine").lower()
    input_summary = _compact_text(data.get("input_summary") or data.get("target_summary") or "metadata-only rule pressure packet")
    target = data.get("target") if isinstance(data.get("target"), Mapping) else None
    if not isinstance(target, Mapping):
        target_payload = dict(data)
        target_payload.setdefault("source_engine_name", source_engine_name)
        target_payload.setdefault("target_summary", input_summary)
        target = build_rule_pressure_target_v1(target_payload)
    else:
        target = build_rule_pressure_target_v1(target)

    target_id = _compact_text(target.get("target_id"))
    pressure_type = _normalize_pressure_type(data.get("pressure_type") or data.get("pressure_type_override") or "counterexample_search")
    test = data.get("pressure_test") if isinstance(data.get("pressure_test"), Mapping) else None
    if not isinstance(test, Mapping):
        test_payload = dict(data)
        test_payload.setdefault("target", target)
        test_payload.setdefault("target_id", target_id)
        test_payload.setdefault("target_rule_or_operator", target.get("candidate_rule_or_operator"))
        test_payload.setdefault("pressure_type", pressure_type)
        test_payload.setdefault("pressure_summary", _compact_text(data.get("pressure_summary") or f"What would break {target.get('candidate_rule_or_operator')}?"))
        test_payload.setdefault("input_mutation", _compact_text(data.get("input_mutation") or "metadata-only mutation"))
        test_payload.setdefault("expected_failure_mode", _compact_text(data.get("expected_failure_mode") or "hidden_assumption_failure"))
        test_payload.setdefault("control_case_summary", _compact_text(data.get("control_case_summary") or "Control case keeps the baseline intact."))
        test_payload.setdefault("success_criteria", _compact_text(data.get("success_criteria") or "pressure reveals a bounded weakness"))
        test_payload.setdefault("failure_criteria", _compact_text(data.get("failure_criteria") or "pressure leaves an unsupported public or runtime claim"))
        test = build_rule_pressure_test_v1(test_payload)
    else:
        test = build_rule_pressure_test_v1(test)

    result = data.get("pressure_result") if isinstance(data.get("pressure_result"), Mapping) else None
    if not isinstance(result, Mapping):
        result_payload = dict(data)
        result_payload.setdefault("pressure_test_id", _compact_text(test.get("pressure_test_id")))
        result_payload.setdefault("target_id", target_id)
        result_payload.setdefault("result_status", _compact_text(data.get("result_status") or "not_observed_yet"))
        result_payload.setdefault("observed_result_summary", _compact_text(data.get("observed_result_summary") or "not observed yet"))
        result_payload.setdefault("target_survived", _safe_bool(data.get("target_survived", True)))
        result_payload.setdefault("breakage_detected", _safe_bool(data.get("breakage_detected", False)))
        result_payload.setdefault("breakage_type", _compact_text(data.get("breakage_type") or "none"))
        result_payload.setdefault("scope_changed", _safe_bool(data.get("scope_changed", False)))
        result_payload.setdefault("new_uncertainty", _ensure_list(data.get("new_uncertainty")) or ["not yet observed"])
        result_payload.setdefault("new_invalidation_signal", _compact_text(data.get("new_invalidation_signal") or "none"))
        result_payload.setdefault("calibration_outcome_status", _compact_text(data.get("calibration_outcome_status") or "not_yet_calibrated"))
        result = build_rule_pressure_result_v1(result_payload)
    else:
        result = build_rule_pressure_result_v1(result)

    corrections = _ensure_list(data.get("corrections"))
    if not corrections and _compact_text(result.get("result_status")) in {"failed_pressure", "contradicted", "partially_survived"}:
        corrections = [
            build_rule_pressure_correction_v1(
                {
                    "target_id": target_id,
                    "pressure_test_id": _compact_text(test.get("pressure_test_id")),
                    "breakage_type": _compact_text(result.get("breakage_type") or "unknown"),
                    "failed_assumption": _compact_text(data.get("failed_assumption") or target.get("candidate_rule_or_operator") or "candidate assumption"),
                    "corrected_scope": _compact_text(data.get("corrected_scope") or target.get("known_scope") or target.get("claimed_scope") or "metadata-only scope"),
                    "model_update_summary": _compact_text(data.get("model_update_summary") or "pressure exposed a bounded failure mode"),
                    "compressed_lesson": _compact_text(data.get("compressed_lesson") or "Pressure reveals failure modes; survival is only evidence of a narrower limit."),
                    "future_pressure_adjustment": _compact_text(data.get("future_pressure_adjustment") or "narrow future pressure and add a control case"),
                    "calibration_record_ref": _compact_text(data.get("calibration_record_ref") or ""),
                }
            )
        ]
    else:
        corrections = [build_rule_pressure_correction_v1(item) if isinstance(item, Mapping) else item for item in corrections]

    hypotheses = _ensure_list(data.get("hypotheses")) or [
        {
            "hypothesis_id": f"rp-hypothesis-{_stable_digest({'target_id': target_id, 'pressure_type': pressure_type})[:12]}",
            "claim": f"{target.get('candidate_rule_or_operator')} may fail under {pressure_type}.",
            "evidence": [target.get("target_summary")],
            "uncertainty_factors": _ensure_list(target.get("uncertainty_factors")),
            "invalidation_signals": _ensure_list(target.get("invalidation_signals")),
        }
    ]

    calibration_record = data.get("calibration_record")
    if not isinstance(calibration_record, Mapping):
        calibration_record = build_forecast_calibration_packet_from_research_run_v1(
            {
                **build_cognitive_research_run_v1(
                    {
                        "engine_name": ENGINE_NAME_V1,
                        "engine_family": ENGINE_FAMILY_V1,
                        "research_mode": research_mode,
                        "source_scope": "metadata_only",
                        "input_artifact_ref": _compact_text(data.get("input_artifact_ref") or f"artifact:{target_id or 'rule-pressure'}"),
                        "input_artifact_type": _compact_text(data.get("input_artifact_type") or "rule-pressure-bundle"),
                        "input_summary": input_summary,
                        "public_claim_status": public_claim_status,
                        "public_gap_card_status": public_gap_card_status,
                        "llm_helper_role": _compact_text(data.get("llm_helper_role") or "candidate_generator_only"),
                        "boundary_status": _make_default_boundary_status(),
                        "denied_authority": build_default_cognitive_research_denied_authority_v1(),
                        "safe_metadata": _make_default_safe_metadata(ENGINE_NAME_V1, ENGINE_FAMILY_V1, research_mode),
                        "rule_pressure_tests": [test],
                        "hypotheses": hypotheses,
                        "predictions": [],
                        "falsification_probes": _ensure_list(data.get("falsification_probes")) or ["pressure the candidate until it either narrows or breaks"],
                        "probes": _ensure_list(data.get("probes")) or [{"probe_id": f"rp-probe-{_stable_digest({'target_id': target_id, 'pressure_type': pressure_type})[:12]}", "probe": f"What would break {target.get('candidate_rule_or_operator')}?", "purpose": "falsify the candidate"}],
                        "outcomes": [result],
                        "corrections": corrections,
                        "compressed_lesson": _compact_text(data.get("compressed_lesson") or (corrections[0].get("compressed_lesson") if corrections else "Pressure reveals failure modes; keep the scope narrow.")),
                        "next_experiments": _ensure_list(data.get("next_experiments")) or ["run a narrower control case", "add a rival candidate", "change the mutation type"],
                        "confidence_map": data.get("confidence_map") if isinstance(data.get("confidence_map"), Mapping) else {target_id or "target": 0.6},
                        "uncertainty_map": data.get("uncertainty_map") if isinstance(data.get("uncertainty_map"), Mapping) else {target_id or "target": _ensure_list(target.get("uncertainty_factors"))},
                        "calibration_record": None,
                    }
                ),
                "source_engine_name": ENGINE_NAME_V1,
                "source_engine_family": ENGINE_FAMILY_V1,
                "prediction_type": "rule_pressure_prediction",
                "prediction_statement": f"Pressure against {target.get('candidate_rule_or_operator')} may reveal { _compact_text(data.get('expected_failure_mode') or result.get('breakage_type') or 'unknown') }.",
                "prediction_scope": _compact_text(target.get("known_scope") or target.get("claimed_scope") or "metadata-only scope"),
                "confidence_before": 0.6,
                "confidence_after": 0.58 if _compact_text(result.get("result_status")) == "not_observed_yet" else 0.52,
                "confidence_basis": "metadata-only rule pressure calibration",
                "uncertainty_factors": _ensure_list(target.get("uncertainty_factors")),
                "invalidation_signals": _ensure_list(target.get("invalidation_signals")),
                "expected_outcome": _compact_text(test.get("success_criteria")),
                "observed_outcome": _compact_text(result.get("observed_result_summary") if _compact_text(result.get("result_status")) != "not_observed_yet" else ""),
                "outcome_status": _map_result_status_to_outcome_status(_compact_text(result.get("result_status"))),
                "calibration_result": _map_result_status_to_calibration_result(_compact_text(result.get("result_status"))),
                "error_type": "none" if _compact_text(result.get("result_status")) in {"not_observed_yet", "survived_pressure"} else "wrong_assumption",
                "correction": _compact_text(corrections[0].get("compressed_lesson") if corrections else ""),
                "compressed_lesson": _compact_text(data.get("compressed_lesson") or (corrections[0].get("compressed_lesson") if corrections else "Pressure reveals bounded failure modes.")),
                "future_adjustment": _compact_text((corrections[0].get("future_pressure_adjustment") if corrections else "narrow future pressure and add a control case")),
                "behavior_change_authorized": False,
                "memory_mutation_authorized": False,
                "project_mutation_authorized": False,
                "public_claim_authorized": False,
                "denied_authority": build_default_cognitive_research_denied_authority_v1(),
                "safe_metadata": _make_default_safe_metadata(ENGINE_NAME_V1, ENGINE_FAMILY_V1, research_mode),
            }
        )
    if isinstance(calibration_record, Mapping):
        calibration_record["uncertainty_factors"] = _ensure_list(target.get("uncertainty_factors"))
        calibration_record["invalidation_signals"] = _ensure_list(target.get("invalidation_signals"))
        calibration_record["prediction_statement"] = f"Pressure against {target.get('candidate_rule_or_operator')} may reveal {_compact_text(data.get('expected_failure_mode') or result.get('breakage_type') or 'unknown')}."
    if corrections:
        calibration_record_ref = _compact_text(calibration_record.get("record_id")) if isinstance(calibration_record, Mapping) else ""
        corrections = [
            build_rule_pressure_correction_v1(
                {
                    **item,
                    "calibration_record_ref": _compact_text(item.get("calibration_record_ref") or calibration_record_ref),
                }
            )
            if isinstance(item, Mapping)
            else item
            for item in corrections
        ]
    predictions = _ensure_list(data.get("predictions")) or [calibration_record]
    probes = _ensure_list(data.get("probes")) or [
        {
            "probe_id": f"rp-probe-{_stable_digest({'target_id': target_id, 'pressure_type': pressure_type, 'result_status': _compact_text(result.get('result_status'))})[:12]}",
            "probe": f"What would break {target.get('candidate_rule_or_operator')}?",
            "purpose": "falsify the candidate",
            "expected_observation": _compact_text(test.get("success_criteria")),
        }
    ]
    falsification_probes = _ensure_list(data.get("falsification_probes")) or [
        f"{pressure_type}: compare candidate against a control case",
        f"{pressure_type}: attempt to produce { _compact_text(result.get('breakage_type') or 'unknown') }",
    ]
    outcomes = _ensure_list(data.get("outcomes")) or [result]
    next_experiments = _ensure_list(data.get("next_experiments")) or [
        "tighten the control case",
        "mutate the operator or translation path",
        "re-run with a narrower scope",
    ]
    compressed_lesson = _compact_text(data.get("compressed_lesson") or (corrections[0].get("compressed_lesson") if corrections else "Pressure reveals bounded failure modes; survival is only evidence."))
    confidence_map = data.get("confidence_map") if isinstance(data.get("confidence_map"), Mapping) else {target_id or "target": 0.6}
    uncertainty_map = data.get("uncertainty_map") if isinstance(data.get("uncertainty_map"), Mapping) else {target_id or "target": _ensure_list(target.get("uncertainty_factors"))}
    suggestion_store_updates = _ensure_list(data.get("suggestion_store_updates"))
    packet = build_cognitive_research_run_v1(
        {
            "engine_name": ENGINE_NAME_V1,
            "engine_family": ENGINE_FAMILY_V1,
            "research_mode": research_mode,
            "source_scope": "metadata_only",
            "input_artifact_ref": _compact_text(data.get("input_artifact_ref") or f"artifact:{target_id or 'rule-pressure'}"),
            "input_artifact_type": _compact_text(data.get("input_artifact_type") or "rule-pressure-bundle"),
            "input_summary": input_summary,
            "hypotheses": hypotheses,
            "predictions": predictions,
            "confidence_map": confidence_map,
            "uncertainty_map": uncertainty_map,
            "falsification_probes": falsification_probes,
            "probes": probes,
            "outcomes": outcomes,
            "corrections": corrections,
            "compressed_lesson": compressed_lesson,
            "next_experiments": next_experiments,
            "calibration_record": calibration_record,
            "public_claim_status": public_claim_status,
            "public_gap_card_status": public_gap_card_status,
            "boundary_status": _make_default_boundary_status(),
            "denied_authority": build_default_cognitive_research_denied_authority_v1(),
            "safe_metadata": _make_default_safe_metadata(ENGINE_NAME_V1, ENGINE_FAMILY_V1, research_mode),
            "llm_helper_role": _compact_text(data.get("llm_helper_role") or "candidate_generator_only"),
            "rule_pressure_targets": [target],
            "rule_pressure_tests": [test],
            "rule_pressure_results": [result],
            "rule_pressure_corrections": corrections,
            "suggestion_store_updates": suggestion_store_updates,
        }
    )
    packet["rule_pressure_targets"] = [target]
    packet["rule_pressure_tests"] = [test]
    packet["rule_pressure_results"] = [result]
    packet["rule_pressure_corrections"] = corrections
    packet["calibration_record"] = calibration_record
    packet["predictions"] = predictions
    packet["probes"] = probes
    packet["falsification_probes"] = falsification_probes
    packet["outcomes"] = outcomes
    packet["next_experiments"] = next_experiments
    packet["compressed_lesson"] = compressed_lesson
    packet["suggestion_store_updates"] = suggestion_store_updates
    return deepcopy(packet)


def _validate_target(target: Any, index: int = 0) -> list[str]:
    violations: list[str] = []
    if not isinstance(target, Mapping):
        return [f"invalid_target_{index}"]
    target_id = _compact_text(target.get("target_id"))
    if not target_id:
        violations.append(f"missing_target_id_{index}")
    if not _compact_text(target.get("target_summary")):
        violations.append(f"missing_target_summary_{index}")
    if not _compact_text(target.get("candidate_rule_or_operator")):
        violations.append(f"missing_candidate_rule_or_operator_{index}")
    if not _ensure_list(target.get("uncertainty_factors")):
        violations.append(f"missing_uncertainty_factors_{index}")
    if not _ensure_list(target.get("invalidation_signals")):
        violations.append(f"missing_invalidation_signals_{index}")
    public_status = _normalize_target_status(target.get("public_claim_status"))
    if public_status != "not_public_claim":
        violations.append(f"target_marked_public_claim_or_export_safe_{index}")
    if _has_forbidden_markers(target):
        violations.append(f"forbidden_text_marker_{index}")
    return violations


def _validate_pressure_test(test: Any, index: int = 0) -> list[str]:
    violations: list[str] = []
    if not isinstance(test, Mapping):
        return [f"invalid_pressure_test_{index}"]
    pressure_test_id = _compact_text(test.get("pressure_test_id"))
    if not pressure_test_id:
        violations.append(f"missing_pressure_test_id_{index}")
    if not _compact_text(test.get("target_id")):
        violations.append(f"missing_target_id_{index}")
    raw_pressure_type = _compact_text(test.get("pressure_type"))
    if not raw_pressure_type:
        violations.append(f"missing_pressure_type_{index}")
    elif raw_pressure_type not in _ALLOWED_PRESSURE_TYPES_V1:
        violations.append(f"invalid_pressure_type_{index}")
    if not _compact_text(test.get("expected_failure_mode")):
        violations.append(f"missing_expected_failure_mode_{index}")
    if not _compact_text(test.get("success_criteria")) or not _compact_text(test.get("failure_criteria")):
        violations.append(f"missing_success_or_failure_criteria_{index}")
    if not _safe_bool(test.get("safe_to_run_as_metadata", True)):
        violations.append(f"pressure_test_executable_or_runtime_safe_{index}")
    if _has_forbidden_markers(test):
        violations.append(f"forbidden_text_marker_{index}")
    calibration_prediction = test.get("calibration_prediction")
    if not isinstance(calibration_prediction, Mapping):
        violations.append(f"invalid_calibration_prediction_{index}")
    else:
        if _has_forbidden_markers(calibration_prediction):
            violations.append(f"forbidden_text_marker_prediction_{index}")
    return violations


def _validate_result(result: Any, index: int = 0) -> list[str]:
    violations: list[str] = []
    if not isinstance(result, Mapping):
        return [f"invalid_result_{index}"]
    if not _compact_text(result.get("pressure_result_id")):
        violations.append(f"missing_pressure_result_id_{index}")
    if not _compact_text(result.get("pressure_test_id")):
        violations.append(f"missing_pressure_test_id_{index}")
    result_status = _normalize_result_status(result.get("result_status"))
    if result_status not in _ALLOWED_RESULT_STATUSES_V1:
        violations.append(f"invalid_result_status_{index}")
    if result_status in {"survived_pressure", "partially_survived", "failed_pressure", "contradicted"} and not _compact_text(result.get("observed_result_summary")):
        violations.append(f"missing_observed_result_summary_{index}")
    breakage_type = _normalize_breakage_type(result.get("breakage_type"))
    if breakage_type not in _ALLOWED_BREAKAGE_TYPES_V1:
        violations.append(f"invalid_breakage_type_{index}")
    if not _compact_text(result.get("calibration_outcome_status")):
        violations.append(f"missing_calibration_outcome_status_{index}")
    observed_text = _compact_text(result.get("observed_result_summary")).lower()
    if any(marker in observed_text for marker in ("proof", "truth", "certified", "breakthrough", "official", "agi", "sentience", "consciousness")):
        violations.append(f"proof_or_truth_claim_{index}")
    if _has_forbidden_markers(result):
        violations.append(f"forbidden_text_marker_{index}")
    return violations


def _validate_correction(correction: Any, index: int = 0) -> list[str]:
    violations: list[str] = []
    if not isinstance(correction, Mapping):
        return [f"invalid_correction_{index}"]
    if not _compact_text(correction.get("correction_id")):
        violations.append(f"missing_correction_id_{index}")
    if not _compact_text(correction.get("target_id")):
        violations.append(f"missing_target_id_{index}")
    if not _compact_text(correction.get("pressure_test_id")):
        violations.append(f"missing_pressure_test_id_{index}")
    breakage_type = _normalize_breakage_type(correction.get("breakage_type"))
    if breakage_type not in _ALLOWED_BREAKAGE_TYPES_V1:
        violations.append(f"invalid_breakage_type_{index}")
    if not _compact_text(correction.get("failed_assumption")):
        violations.append(f"missing_failed_assumption_{index}")
    if not _compact_text(correction.get("corrected_scope")) and breakage_type != "none":
        violations.append(f"missing_corrected_scope_after_breakage_{index}")
    if not _compact_text(correction.get("compressed_lesson")):
        violations.append(f"missing_compressed_lesson_{index}")
    if not _compact_text(correction.get("calibration_record_ref")):
        violations.append(f"missing_calibration_record_ref_{index}")
    if _has_forbidden_markers(correction):
        violations.append(f"forbidden_text_marker_{index}")
    return violations


def validate_rule_pressure_packet_v1(packet: Any) -> dict[str, Any]:
    protocol_validation = validate_cognitive_research_run_v1(packet)
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
            "violation_count": 1,
            "protocol_validation": protocol_validation,
            "classification": "invalid",
            "engine_name": ENGINE_NAME_V1,
            "engine_family": ENGINE_FAMILY_V1,
        }

    engine_name = _compact_text(raw.get("engine_name")).lower()
    engine_family = _compact_text(raw.get("engine_family")).lower()
    research_mode = _compact_text(raw.get("research_mode")).lower()
    public_claim_status = _compact_text(raw.get("public_claim_status")).lower()
    public_gap_card_status = _compact_text(raw.get("public_gap_card_status")).lower()

    if engine_name != ENGINE_NAME_V1:
        violations.append("invalid_engine_name")
    if engine_family != ENGINE_FAMILY_V1:
        violations.append("invalid_engine_family")
    if research_mode not in set(ALLOWED_COGNITIVE_RESEARCH_RESEARCH_MODES_V1):
        violations.append("invalid_research_mode")
    if public_claim_status not in set(_ALLOWED_PUBLIC_CLAIM_STATUSES_V1):
        violations.append("invalid_public_claim_status")
    if public_gap_card_status != "public_export_blocked":
        violations.append("public_gap_card_must_remain_blocked")

    denied_authority = raw.get("denied_authority")
    if not isinstance(denied_authority, Mapping):
        violations.append("missing_denied_authority")
    else:
        if any(_safe_bool(value) for value in denied_authority.values()):
            violations.append("unsafe_denied_authority")

    safe_metadata = raw.get("safe_metadata")
    if not isinstance(safe_metadata, Mapping):
        violations.append("missing_safe_metadata")
    else:
        for flag in _REQUIRED_SAFE_METADATA_FLAGS_V1:
            if not _safe_bool(safe_metadata.get(flag)):
                violations.append(f"unsafe_safe_metadata_{flag}")

    targets = _ensure_list(raw.get("rule_pressure_targets"))
    if not targets:
        violations.append("missing_target_id")
    for index, target in enumerate(targets):
        violations.extend(_validate_target(target, index))

    tests = _ensure_list(raw.get("rule_pressure_tests"))
    for index, test in enumerate(tests):
        violations.extend(_validate_pressure_test(test, index))

    results = _ensure_list(raw.get("rule_pressure_results"))
    for index, result in enumerate(results):
        violations.extend(_validate_result(result, index))

    corrections = _ensure_list(raw.get("rule_pressure_corrections"))
    for index, correction in enumerate(corrections):
        violations.extend(_validate_correction(correction, index))

    if not _compact_text(raw.get("compressed_lesson")):
        violations.append("missing_compressed_lesson")
    if _has_forbidden_markers(raw):
        violations.append("forbidden_text_marker")

    calibration_record = raw.get("calibration_record")
    if isinstance(calibration_record, Mapping) and calibration_record:
        calibration_validation = validate_forecast_calibration_record_v1(calibration_record)
        if not calibration_validation["valid"]:
            violations.append("invalid_calibration_record")
    else:
        violations.append("missing_calibration_record")

    blocked = bool(violations) or bool(protocol_validation.get("blocked"))
    merged_violations = list(dict.fromkeys([*protocol_validation.get("blocked_labels", []), *violations]))
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "helper_type": HELPER_TYPE_V1,
        "valid": not blocked,
        "blocked": blocked,
        "violations": merged_violations,
        "violation_count": len(merged_violations),
        "protocol_validation": protocol_validation,
        "classification": ENGINE_NAME_V1 if not blocked else "invalid",
        "engine_name": engine_name or ENGINE_NAME_V1,
        "engine_family": engine_family or ENGINE_FAMILY_V1,
        "research_mode": research_mode,
        "public_claim_status": public_claim_status,
        "public_gap_card_status": public_gap_card_status,
        "packet": to_rule_pressure_json_safe_v1(raw),
    }


def summarize_rule_pressure_packet_v1(packet: Any) -> dict[str, Any]:
    validation = validate_rule_pressure_packet_v1(packet)
    raw = to_rule_pressure_json_safe_v1(packet)
    if validation["blocked"]:
        preview = ", ".join(validation["violations"][:4])
        summary_text = f"Blocked rule pressure packet: {preview or 'validation failed'}."
    else:
        target = _ensure_list(raw.get("rule_pressure_targets"))[0] if _ensure_list(raw.get("rule_pressure_targets")) else {}
        result = _ensure_list(raw.get("rule_pressure_results"))[0] if _ensure_list(raw.get("rule_pressure_results")) else {}
        summary_text = (
            f"Rule pressure packet: target={_compact_text(target.get('candidate_rule_or_operator')) or _compact_text(target.get('target_summary'))}; "
            f"pressure={_compact_text(_ensure_list(raw.get('rule_pressure_tests'))[0].get('pressure_type')) if _ensure_list(raw.get('rule_pressure_tests')) else 'unknown'}; "
            f"result={_compact_text(result.get('result_status')) or 'not_observed_yet'}; "
            f"lesson={_compact_text(raw.get('compressed_lesson'))}"
        )
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "helper_type": HELPER_TYPE_V1,
        "summary_text": _compact_text(summary_text)[:320],
        "blocked": validation["blocked"],
        "violations": validation["violations"],
        "violation_count": validation["violation_count"],
        "classification": validation["classification"],
        "engine_name": validation["engine_name"],
        "engine_family": validation["engine_family"],
        "research_mode": validation["research_mode"],
        "public_claim_status": validation["public_claim_status"],
        "public_gap_card_status": validation["public_gap_card_status"],
        "packet": validation["packet"],
    }


def to_rule_pressure_json_safe_v1(packet: Any) -> dict[str, Any]:
    return _json_safe(deepcopy(packet)) if isinstance(packet, Mapping) else {}


def build_initial_rule_pressure_examples_v1() -> list[dict[str, Any]]:
    examples: list[dict[str, Any]] = []
    specs = [
        {
            "source_engine_name": "unknown_engine",
            "target_type": "hidden_rule",
            "target_summary": "Hidden rule candidate with narrow scope and a control case.",
            "candidate_rule_or_operator": "hidden rule candidate",
            "claimed_scope": "bounded hidden rule",
            "known_scope": "metadata-only hidden rule review",
            "pressure_type": "counterexample_search",
            "expected_failure_mode": "hidden_assumption_failure",
            "result_status": "not_observed_yet",
        },
        {
            "source_engine_name": "nonlinear_inspiration_engine",
            "target_type": "operator_candidate",
            "target_summary": "Transferred operator candidate from a nonlinear resonance match.",
            "candidate_rule_or_operator": "transferred operator candidate",
            "claimed_scope": "operator transfer",
            "known_scope": "candidate operator transfer scope",
            "pressure_type": "operator_substitution",
            "expected_failure_mode": "operator_fragility",
            "result_status": "survived_pressure",
        },
        {
            "source_engine_name": "unintelligible_output_analyzer",
            "target_type": "translation_candidate",
            "target_summary": "Translation candidate preserving competing meanings under pressure.",
            "candidate_rule_or_operator": "translation candidate",
            "claimed_scope": "translation bridge",
            "known_scope": "translation metadata only",
            "pressure_type": "false_pattern_insertion",
            "expected_failure_mode": "translation_fragility",
            "result_status": "failed_pressure",
        },
        {
            "source_engine_name": "raw_signal_cartographer",
            "target_type": "motif_candidate",
            "target_summary": "Signal/noise boundary candidate with a control case.",
            "candidate_rule_or_operator": "signal/noise boundary",
            "claimed_scope": "motif candidate",
            "known_scope": "raw-signal metadata only",
            "pressure_type": "noise_injection",
            "expected_failure_mode": "noise_fragility",
            "result_status": "partially_survived",
        },
    ]
    for spec in specs:
        target = build_rule_pressure_target_v1(spec)
        test = build_rule_pressure_test_v1({**spec, "target": target, "target_id": target["target_id"]})
        result = build_rule_pressure_result_v1({
            "target_id": target["target_id"],
            "pressure_test_id": test["pressure_test_id"],
            "result_status": spec["result_status"],
            "observed_result_summary": f"{spec['result_status']} for {spec['pressure_type']}.",
            "breakage_type": "none" if spec["result_status"] == "survived_pressure" else _normalize_breakage_type(spec["expected_failure_mode"]),
            "calibration_outcome_status": _map_result_status_to_calibration_result(spec["result_status"]),
            "new_uncertainty": [spec["expected_failure_mode"]],
            "new_invalidation_signal": f"{spec['pressure_type']} pressure revealed a limit",
        })
        packet = build_rule_pressure_packet_v1({
            **spec,
            "target": target,
            "pressure_test": test,
            "pressure_result": result,
            "compressed_lesson": "Pressure checks reveal limits; they never settle the claim.",
            "falsification_probes": [f"{spec['pressure_type']}: compare the candidate against a control case"],
            "next_experiments": ["narrow the scope", "add a counterexample", "change the mutation"],
        })
        examples.append(packet)
    return examples
