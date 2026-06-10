"""Metadata-only Forecast Calibration Bridge V1 helpers.

This bridge turns recursive research packets into deterministic calibration
records. It stays metadata-only, JSON-safe, deterministic, and fail-closed.
It does not wire runtime behavior, mutate memory or projects, call providers,
execute tools, touch .weslr, or make public claims.
"""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from typing import Any, Mapping

from weslr.cognitive_research_protocol import (
    ALLOWED_COGNITIVE_RESEARCH_ENGINE_NAMES_V1,
    build_cognitive_research_run_v1,
    build_default_cognitive_research_denied_authority_v1,
    classify_cognitive_research_engine_family_v1,
    summarize_cognitive_research_run_v1,
    to_cognitive_research_json_safe_v1,
    validate_cognitive_research_run_v1,
)

HELPER_TYPE_V1 = "weslr_forecast_calibration_bridge_v1"
SCHEMA_VERSION_V1 = "forecast_calibration_bridge_v1"
ENGINE_NAME_V1 = "forecast_calibration_bridge"
ENGINE_FAMILY_V1 = "calibration_and_forecast"

_ALLOWED_PREDICTION_TYPES_V1 = (
    "hidden_rule_prediction",
    "translation_prediction",
    "gap_prediction",
    "operator_prediction",
    "motif_prediction",
    "probe_prediction",
    "rule_pressure_prediction",
    "project_state_prediction",
    "unknown",
)
_ALLOWED_OUTCOME_STATUSES_V1 = (
    "not_observed_yet",
    "matched",
    "partially_matched",
    "failed",
    "contradicted",
    "inconclusive",
    "blocked",
    "out_of_scope",
)
_ALLOWED_CALIBRATION_RESULTS_V1 = (
    "well_calibrated",
    "overconfident",
    "underconfident",
    "wrong_model",
    "missing_signal",
    "scope_error",
    "ambiguous",
    "not_yet_calibrated",
)
_ALLOWED_ERROR_TYPES_V1 = (
    "none",
    "overfit_to_signal",
    "ignored_uncertainty",
    "missing_context",
    "wrong_assumption",
    "scope_mismatch",
    "noise_treated_as_signal",
    "signal_treated_as_noise",
    "translation_overreach",
    "operator_overreach",
    "public_claim_pressure",
    "unknown",
)
_ALLOWED_CONFIDENCE_LABELS_V1 = (
    "unknown",
    "very_low",
    "low",
    "medium",
    "high",
    "very_high",
    "bounded",
    "mixed",
)
_REQUIRED_SAFE_METADATA_FLAGS_V1 = (
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
)

_FORBIDDEN_KEY_FRAGMENTS_V1 = (
    "raw_private",
    "private_content",
    "hidden_prompt",
    "answer_key",
    "provider_output",
    "model_output",
    "search_output",
    "advisor_output",
    "runtime_output",
    "runtime_wiring",
    "tool_execution",
    "provider_call",
    "persistence",
    "final_answer",
    "reply_to_user",
    "public_discovery",
    "proof_claim",
    "breakthrough",
    "behavior_pack",
    "promotion",
    ".weslr",
)
_FORBIDDEN_TEXT_MARKERS_V1 = (
    "raw private text",
    "raw private data",
    "private content",
    "hidden prompt",
    "system prompt",
    "developer prompt",
    "answer key",
    "secret",
    "token=",
    ".weslr",
    "runtime wiring",
    "runtime authority",
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
    "official",
    "certified",
    "consciousness claim",
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


def _safe_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _json_safe(value: Any) -> Any:
    if isinstance(value, Mapping):
        out: dict[str, Any] = {}
        for key in sorted(value.keys(), key=lambda item: str(item)):
            key_text = str(key)
            if any(fragment in key_text.lower() for fragment in _FORBIDDEN_KEY_FRAGMENTS_V1):
                continue
            out[key_text] = _json_safe(value[key])
        return out
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, set):
        return [_json_safe(item) for item in sorted(value, key=_compact_text)]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return _compact_text(value)


def _stable_digest(payload: Mapping[str, Any]) -> str:
    blob = json.dumps(_json_safe(payload), sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def _normalize_prediction_type(value: Any, source_engine_name: str, prediction_statement: str, source_run: Mapping[str, Any]) -> str:
    prediction_type = _compact_text(value).lower()
    if prediction_type in _ALLOWED_PREDICTION_TYPES_V1:
        return prediction_type
    lower_statement = prediction_statement.lower()
    if source_engine_name == "unintelligible_output_analyzer" or "translation" in lower_statement or "interpret" in lower_statement:
        return "translation_prediction"
    if source_engine_name == "raw_signal_cartographer":
        probes = _ensure_list(source_run.get("probes"))
        if probes or "probe" in lower_statement:
            return "probe_prediction"
        return "motif_prediction"
    if source_engine_name in {"forecast_error_ledger", "calibration_ledger"}:
        return "rule_pressure_prediction"
    if "gap" in lower_statement:
        return "gap_prediction"
    if "operator" in lower_statement:
        return "operator_prediction"
    if "project" in lower_statement:
        return "project_state_prediction"
    if "rule" in lower_statement:
        return "rule_pressure_prediction"
    return "unknown"


def _normalize_outcome_status(value: Any) -> str:
    outcome_status = _compact_text(value).lower()
    return outcome_status if outcome_status in _ALLOWED_OUTCOME_STATUSES_V1 else "not_observed_yet"


def _normalize_calibration_result(value: Any, outcome_status: str) -> str:
    calibration_result = _compact_text(value).lower()
    if outcome_status == "not_observed_yet":
        return "not_yet_calibrated"
    return calibration_result if calibration_result in _ALLOWED_CALIBRATION_RESULTS_V1 else "not_yet_calibrated"


def _normalize_error_type(value: Any) -> str:
    error_type = _compact_text(value).lower()
    return error_type if error_type in _ALLOWED_ERROR_TYPES_V1 else "unknown"


def _default_safe_metadata(source_run: Mapping[str, Any], source_engine_name: str, source_engine_family: str, prediction_type: str) -> dict[str, Any]:
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
        "no_public_claims": True,
        "no_final_answer": True,
        "bridge_engine_name": ENGINE_NAME_V1,
        "bridge_engine_family": ENGINE_FAMILY_V1,
        "source_engine_name": source_engine_name,
        "source_engine_family": source_engine_family,
        "prediction_type": prediction_type,
        "source_run_reference_only": True,
        "source_run_id": _compact_text(source_run.get("run_id")),
    }


def _source_run_like(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _source_run_prediction_statement(source_run: Mapping[str, Any]) -> str:
    predictions = _ensure_list(source_run.get("predictions"))
    hypotheses = _ensure_list(source_run.get("hypotheses"))
    probes = _ensure_list(source_run.get("probes"))
    for bucket in (predictions, hypotheses, probes):
        for item in bucket:
            text = _compact_text(item)
            if text:
                return text
    for key in ("input_summary", "compressed_lesson", "summary_text"):
        text = _compact_text(source_run.get(key))
        if text:
            return text
    return "metadata-only prediction statement"


def _collect_text_violations(value: Any, path: str = "") -> list[str]:
    violations: list[str] = []
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = str(key)
            child_path = f"{path}.{key_text}" if path else key_text
            violations.extend(_collect_text_violations(item, child_path))
        return violations
    if isinstance(value, (list, tuple, set)):
        for index, item in enumerate(value):
            child_path = f"{path}[{index}]" if path else f"[{index}]"
            violations.extend(_collect_text_violations(item, child_path))
        return violations
    text = _compact_text(value).lower()
    if not text:
        return violations
    for marker in _FORBIDDEN_TEXT_MARKERS_V1:
        if marker in text:
            violations.append(f"forbidden_text_marker:{marker}")
    return violations


def _confidence_is_valid(value: Any) -> bool:
    if isinstance(value, (int, float)):
        return 0.0 <= float(value) <= 1.0
    if isinstance(value, str):
        return _compact_text(value).lower() in _ALLOWED_CONFIDENCE_LABELS_V1
    return False


def _confidence_key(value: Any) -> str:
    if isinstance(value, (int, float)):
        return f"{float(value):.6f}"
    return _compact_text(value).lower()


def build_forecast_calibration_record_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = _merge_payload(payload, **overrides)
    source_run = _source_run_like(data.get("source_run"))

    source_engine_name = _compact_text(data.get("source_engine_name") or source_run.get("engine_name") or "forecast_error_ledger").lower()
    if source_engine_name not in ALLOWED_COGNITIVE_RESEARCH_ENGINE_NAMES_V1:
        source_engine_name = "forecast_error_ledger"
    source_engine_family = _compact_text(data.get("source_engine_family") or source_run.get("engine_family") or classify_cognitive_research_engine_family_v1(source_engine_name)).lower()
    if not source_engine_family:
        source_engine_family = classify_cognitive_research_engine_family_v1(source_engine_name) or ENGINE_FAMILY_V1

    prediction_statement = _compact_text(data.get("prediction_statement") or _source_run_prediction_statement(source_run))
    prediction_type = _normalize_prediction_type(data.get("prediction_type"), source_engine_name, prediction_statement, source_run)
    outcome_status = _normalize_outcome_status(data.get("outcome_status"))
    calibration_result = _normalize_calibration_result(data.get("calibration_result"), outcome_status)

    source_run_id = _compact_text(data.get("source_run_id") or source_run.get("run_id") or f"source-run-{_stable_digest({'engine_name': source_engine_name, 'statement': prediction_statement})[:12]}")
    prediction_id = _compact_text(data.get("prediction_id") or f"prediction-{_stable_digest({'source_run_id': source_run_id, 'statement': prediction_statement, 'type': prediction_type})[:12]}")
    confidence_before = data.get("confidence_before", 0.5)
    confidence_after = data.get("confidence_after", confidence_before)
    confidence_basis = _compact_text(data.get("confidence_basis") or "metadata-only bridge basis")
    uncertainty_factors = _ensure_list(data.get("uncertainty_factors")) or ["prediction unresolved"]
    invalidation_signals = _ensure_list(data.get("invalidation_signals")) or ["not_observed_yet"]
    expected_outcome = _compact_text(data.get("expected_outcome") or "prediction pending")
    observed_outcome = _compact_text(data.get("observed_outcome"))
    error_type = _normalize_error_type(data.get("error_type"))
    assumptions_used = _ensure_list(data.get("assumptions_used"))
    assumptions_failed = _ensure_list(data.get("assumptions_failed"))
    missing_signals = _ensure_list(data.get("missing_signals"))
    conflicting_signals = _ensure_list(data.get("conflicting_signals"))
    correction = _compact_text(data.get("correction"))
    compressed_lesson = _compact_text(data.get("compressed_lesson"))
    future_adjustment = _compact_text(data.get("future_adjustment") or "bounded metadata-only calibration adjustment")

    denied_authority = data.get("denied_authority")
    if not isinstance(denied_authority, Mapping):
        denied_authority = build_default_cognitive_research_denied_authority_v1()
    else:
        denied_authority = {str(key): _safe_bool(value) for key, value in denied_authority.items()}

    safe_metadata = data.get("safe_metadata")
    if not isinstance(safe_metadata, Mapping):
        safe_metadata = _default_safe_metadata(source_run, source_engine_name, source_engine_family, prediction_type)
    else:
        safe_metadata = {
            **_default_safe_metadata(source_run, source_engine_name, source_engine_family, prediction_type),
            **{str(key): value for key, value in safe_metadata.items()},
        }

    return {
        "schema_version": _compact_text(data.get("schema_version") or SCHEMA_VERSION_V1),
        "record_id": prediction_id.replace("prediction-", "calibration-") if not _compact_text(data.get("record_id")) else _compact_text(data.get("record_id")),
        "source_run_id": source_run_id,
        "source_engine_name": source_engine_name,
        "source_engine_family": source_engine_family,
        "prediction_id": prediction_id,
        "prediction_statement": prediction_statement,
        "prediction_type": prediction_type,
        "prediction_scope": _compact_text(data.get("prediction_scope") or source_run.get("source_scope") or "metadata_only"),
        "confidence_before": confidence_before,
        "confidence_basis": confidence_basis,
        "uncertainty_factors": uncertainty_factors,
        "invalidation_signals": invalidation_signals,
        "expected_outcome": expected_outcome,
        "observed_outcome": observed_outcome,
        "outcome_status": outcome_status,
        "calibration_result": calibration_result,
        "error_type": error_type,
        "assumptions_used": assumptions_used,
        "assumptions_failed": assumptions_failed,
        "missing_signals": missing_signals,
        "conflicting_signals": conflicting_signals,
        "correction": correction,
        "compressed_lesson": compressed_lesson,
        "confidence_after": confidence_after,
        "future_adjustment": future_adjustment,
        "behavior_change_authorized": False if data.get("behavior_change_authorized") is None else _safe_bool(data.get("behavior_change_authorized")),
        "memory_mutation_authorized": False if data.get("memory_mutation_authorized") is None else _safe_bool(data.get("memory_mutation_authorized")),
        "project_mutation_authorized": False if data.get("project_mutation_authorized") is None else _safe_bool(data.get("project_mutation_authorized")),
        "public_claim_authorized": False if data.get("public_claim_authorized") is None else _safe_bool(data.get("public_claim_authorized")),
        "denied_authority": denied_authority,
        "safe_metadata": safe_metadata,
    }


def build_forecast_calibration_packet_from_research_run_v1(research_run: Any = None, **overrides: Any) -> dict[str, Any]:
    source_run = _source_run_like(research_run)
    payload = {"source_run": source_run}
    payload.update(overrides)
    return build_forecast_calibration_record_v1(payload)


def validate_forecast_calibration_record_v1(record: Any) -> dict[str, Any]:
    raw = record if isinstance(record, Mapping) else {}
    violations: list[str] = []

    if not _compact_text(raw.get("record_id")):
        violations.append("missing_record_id")
    if not _compact_text(raw.get("source_run_id")):
        violations.append("missing_source_run_id")
    if not _compact_text(raw.get("prediction_statement")):
        violations.append("missing_prediction_statement")
    if "confidence_before" not in raw or not _confidence_is_valid(raw.get("confidence_before")):
        violations.append("unsafe_confidence_before")
    if not _ensure_list(raw.get("uncertainty_factors")):
        violations.append("missing_uncertainty_factors")
    if not _ensure_list(raw.get("invalidation_signals")):
        violations.append("missing_invalidation_signals")

    prediction_type = _compact_text(raw.get("prediction_type")).lower()
    if prediction_type not in _ALLOWED_PREDICTION_TYPES_V1:
        violations.append("invalid_prediction_type")

    outcome_status = _compact_text(raw.get("outcome_status")).lower()
    if outcome_status not in _ALLOWED_OUTCOME_STATUSES_V1:
        violations.append("invalid_outcome_status")

    calibration_result = _compact_text(raw.get("calibration_result")).lower()
    if calibration_result not in _ALLOWED_CALIBRATION_RESULTS_V1:
        violations.append("invalid_calibration_result")
    if outcome_status == "not_observed_yet" and calibration_result != "not_yet_calibrated":
        violations.append("calibration_result_before_observation")
    if outcome_status in {"matched", "failed", "partially_matched", "contradicted"} and not _compact_text(raw.get("observed_outcome")):
        violations.append("missing_observed_outcome")

    if "confidence_after" not in raw or not _confidence_is_valid(raw.get("confidence_after")):
        violations.append("unsafe_confidence_after")
    if _confidence_key(raw.get("confidence_before")) != _confidence_key(raw.get("confidence_after")) and not (_compact_text(raw.get("correction")) or _compact_text(raw.get("compressed_lesson"))):
        violations.append("confidence_after_changed_without_correction")

    if _compact_text(raw.get("behavior_change_authorized")).lower() == "true":
        violations.append("behavior_change_authorized_true")
    if _compact_text(raw.get("memory_mutation_authorized")).lower() == "true":
        violations.append("memory_mutation_authorized_true")
    if _compact_text(raw.get("project_mutation_authorized")).lower() == "true":
        violations.append("project_mutation_authorized_true")
    if _compact_text(raw.get("public_claim_authorized")).lower() == "true":
        violations.append("public_claim_authorized_true")

    denied_authority = raw.get("denied_authority")
    if not isinstance(denied_authority, Mapping):
        violations.append("missing_denied_authority")
    else:
        for key, value in denied_authority.items():
            if _safe_bool(value):
                violations.append(f"denied_authority_granted_{_compact_text(key)}")

    safe_metadata = raw.get("safe_metadata")
    if not isinstance(safe_metadata, Mapping):
        violations.append("missing_safe_metadata")
    else:
        for flag in _REQUIRED_SAFE_METADATA_FLAGS_V1:
            if not _safe_bool(safe_metadata.get(flag)):
                violations.append(f"unsafe_safe_metadata_{flag}")

    source_engine_name = _compact_text(raw.get("source_engine_name")).lower()
    if source_engine_name not in ALLOWED_COGNITIVE_RESEARCH_ENGINE_NAMES_V1:
        violations.append("invalid_source_engine_name")
    expected_family = classify_cognitive_research_engine_family_v1(source_engine_name) if source_engine_name else ""
    source_engine_family = _compact_text(raw.get("source_engine_family")).lower()
    if source_engine_name and source_engine_family and expected_family and source_engine_family != expected_family:
        violations.append("source_engine_family_mismatch")

    if any(fragment in _compact_text(raw.get("correction")).lower() for fragment in ("behavior pack", "promotion")):
        violations.append("behavior_pack_promotion_implication")
    if any(fragment in _compact_text(raw.get("compressed_lesson")).lower() for fragment in ("behavior pack", "promotion")):
        violations.append("behavior_pack_promotion_implication")

    violations.extend(_collect_text_violations(raw))
    blocked = bool(violations)
    return {
        "valid": not blocked,
        "blocked": blocked,
        "violations": list(dict.fromkeys(violations)),
        "violation_count": len(list(dict.fromkeys(violations))),
    }


def summarize_forecast_calibration_record_v1(record: Any) -> dict[str, Any]:
    validation = validate_forecast_calibration_record_v1(record)
    raw = to_forecast_calibration_json_safe_v1(record)
    if validation["blocked"]:
        preview = ", ".join(validation["violations"][:4])
        summary_text = f"Blocked forecast calibration record: {preview or 'validation failed'}."
    else:
        before = raw.get("confidence_before")
        after = raw.get("confidence_after")
        summary_text = (
            f"Forecast calibration: source={_compact_text(raw.get('source_engine_name'))}; "
            f"prediction={_compact_text(raw.get('prediction_type'))}; outcome={_compact_text(raw.get('outcome_status'))}; "
            f"calibration={_compact_text(raw.get('calibration_result'))}; confidence={before}->{after}."
        )
    return {
        "schema_version": _compact_text(raw.get("schema_version") or SCHEMA_VERSION_V1),
        "helper_type": HELPER_TYPE_V1,
        "summary_text": summary_text[:320],
        "valid": validation["valid"],
        "violations": validation["violations"],
        "record": raw,
    }


def to_forecast_calibration_json_safe_v1(record: Any) -> dict[str, Any]:
    payload = deepcopy(record) if isinstance(record, Mapping) else {}
    if not isinstance(payload, Mapping):
        return {}
    return _json_safe(payload)


def build_initial_forecast_calibration_examples_v1() -> list[dict[str, Any]]:
    base_run = build_cognitive_research_run_v1(
        {
            "engine_name": "forecast_error_ledger",
            "engine_family": "calibration_and_forecast",
            "research_mode": "calibration_replay",
            "input_artifact_ref": "artifact:calibration-run-001",
            "input_summary": "Metadata-only source run for calibration tracking.",
            "predictions": ["A later probe will match the observed boundary."],
            "probes": ["compare predicted and observed boundary signals"],
            "hypotheses": ["A narrow hidden rule governs the signal shift."],
            "public_claim_status": "internal_candidate_only",
            "public_gap_card_status": "public_export_blocked",
            "llm_helper_role": "candidate_generator_only",
        }
    )

    rsc_run = build_cognitive_research_run_v1(
        {
            "engine_name": "raw_signal_cartographer",
            "engine_family": "raw_signal_analysis",
            "research_mode": "internal_exploration",
            "input_artifact_ref": "artifact:rsc-calibration-001",
            "input_summary": "Repeated motifs and probe candidates are tracked as metadata only.",
            "predictions": ["Repeated motif cluster will remain stable across probes."],
            "probes": ["probe the repeated motif cluster"],
            "public_claim_status": "internal_candidate_only",
            "public_gap_card_status": "public_export_blocked",
            "llm_helper_role": "candidate_generator_only",
        }
    )

    uoa_run = build_cognitive_research_run_v1(
        {
            "engine_name": "unintelligible_output_analyzer",
            "engine_family": "reasoning_integrity",
            "research_mode": "internal_exploration",
            "input_artifact_ref": "artifact:uoa-calibration-001",
            "input_summary": "Ambiguous translation layers are tracked without final meaning authority.",
            "predictions": ["The translation layer will remain partially bounded."],
            "hypotheses": ["Competing readings remain unresolved."],
            "public_claim_status": "internal_candidate_only",
            "public_gap_card_status": "public_export_blocked",
            "llm_helper_role": "translation_helper_only",
        }
    )

    calibration_run = build_cognitive_research_run_v1(
        {
            "engine_name": "calibration_ledger",
            "engine_family": "calibration_and_forecast",
            "research_mode": "calibration_replay",
            "input_artifact_ref": "artifact:calibration-ledger-001",
            "input_summary": "Calibration summary only, no runtime or persistence authority.",
            "predictions": ["The next adjustment should remain bounded."],
            "public_claim_status": "internal_candidate_only",
            "public_gap_card_status": "public_export_blocked",
            "llm_helper_role": "candidate_generator_only",
        }
    )

    return [
        build_forecast_calibration_packet_from_research_run_v1(
            base_run,
            prediction_id="prediction-calibration-001",
            prediction_statement="A later probe will match the observed boundary.",
            prediction_type="probe_prediction",
            prediction_scope="metadata_only",
            confidence_before=0.61,
            confidence_basis="source run predictions and probes",
            uncertainty_factors=["probe timing uncertain"],
            invalidation_signals=["no observation yet"],
            expected_outcome="probe result to be observed",
            outcome_status="not_observed_yet",
            calibration_result="not_yet_calibrated",
            error_type="none",
            safe_metadata={"metadata_only": True, "json_safe": True, "non_public": True, "no_runtime_wiring": True, "no_provider_calls": True, "no_tool_execution": True, "no_persistence": True, "no_memory_mutation": True, "no_project_mutation": True, "no_public_claims": True, "no_final_answer": True},
        ),
        build_forecast_calibration_record_v1(
            source_run=base_run,
            record_id="calibration-matched-001",
            prediction_id="prediction-calibration-002",
            prediction_statement="A later probe will match the observed boundary.",
            prediction_type="probe_prediction",
            prediction_scope="metadata_only",
            confidence_before=0.55,
            confidence_after=0.58,
            confidence_basis="observed boundary and prior probes",
            uncertainty_factors=["timing drift"],
            invalidation_signals=["boundary comparison completed"],
            expected_outcome="probe result to be observed",
            observed_outcome="boundary matched the prediction",
            outcome_status="matched",
            calibration_result="well_calibrated",
            error_type="none",
            safe_metadata={"metadata_only": True, "json_safe": True, "non_public": True, "no_runtime_wiring": True, "no_provider_calls": True, "no_tool_execution": True, "no_persistence": True, "no_memory_mutation": True, "no_project_mutation": True, "no_public_claims": True, "no_final_answer": True},
        ),
        build_forecast_calibration_record_v1(
            source_run=base_run,
            record_id="calibration-failed-001",
            prediction_id="prediction-calibration-003",
            prediction_statement="A later probe will match the observed boundary.",
            prediction_type="probe_prediction",
            prediction_scope="metadata_only",
            confidence_before=0.82,
            confidence_after=0.41,
            confidence_basis="source run predictions and probes",
            uncertainty_factors=["probe timing uncertain"],
            invalidation_signals=["mismatched boundary signal"],
            expected_outcome="probe result to be observed",
            observed_outcome="boundary contradicted the prediction",
            outcome_status="failed",
            calibration_result="wrong_model",
            error_type="wrong_assumption",
            correction="The boundary hypothesis was too narrow.",
            compressed_lesson="Later observations should widen the boundary model.",
            safe_metadata={"metadata_only": True, "json_safe": True, "non_public": True, "no_runtime_wiring": True, "no_provider_calls": True, "no_tool_execution": True, "no_persistence": True, "no_memory_mutation": True, "no_project_mutation": True, "no_public_claims": True, "no_final_answer": True},
        ),
        build_forecast_calibration_record_v1(
            source_run=base_run,
            record_id="calibration-partial-001",
            prediction_id="prediction-calibration-004",
            prediction_statement="The probe will narrow the boundary but not fully settle it.",
            prediction_type="gap_prediction",
            prediction_scope="metadata_only",
            confidence_before=0.63,
            confidence_after=0.62,
            confidence_basis="mixed source run evidence",
            uncertainty_factors=["partial observation only"],
            invalidation_signals=["one signal matched, one remained open"],
            expected_outcome="narrowing without closure",
            observed_outcome="partial narrowing observed",
            outcome_status="partially_matched",
            calibration_result="ambiguous",
            error_type="scope_mismatch",
            correction="Only part of the gap was resolved.",
            compressed_lesson="Separate narrowing from closure in future packets.",
            safe_metadata={"metadata_only": True, "json_safe": True, "non_public": True, "no_runtime_wiring": True, "no_provider_calls": True, "no_tool_execution": True, "no_persistence": True, "no_memory_mutation": True, "no_project_mutation": True, "no_public_claims": True, "no_final_answer": True},
        ),
        build_forecast_calibration_record_v1(
            source_run=base_run,
            record_id="calibration-inconclusive-001",
            prediction_id="prediction-calibration-005",
            prediction_statement="The outcome will stay unresolved until later evidence arrives.",
            prediction_type="unknown",
            prediction_scope="metadata_only",
            confidence_before=0.49,
            confidence_after=0.48,
            confidence_basis="insufficient observation window",
            uncertainty_factors=["no decisive signal"],
            invalidation_signals=["inconclusive observation"],
            expected_outcome="still unresolved",
            observed_outcome="no decisive outcome",
            outcome_status="inconclusive",
            calibration_result="ambiguous",
            error_type="none",
            safe_metadata={"metadata_only": True, "json_safe": True, "non_public": True, "no_runtime_wiring": True, "no_provider_calls": True, "no_tool_execution": True, "no_persistence": True, "no_memory_mutation": True, "no_project_mutation": True, "no_public_claims": True, "no_final_answer": True},
        ),
        build_forecast_calibration_record_v1(
            source_run=base_run,
            record_id="calibration-overconfident-001",
            prediction_id="prediction-calibration-006",
            prediction_statement="The next adjustment will be precise.",
            prediction_type="rule_pressure_prediction",
            prediction_scope="metadata_only",
            confidence_before=0.91,
            confidence_after=0.66,
            confidence_basis="too little evidence for the initial confidence",
            uncertainty_factors=["evidence too thin"],
            invalidation_signals=["correction applied after mismatch"],
            expected_outcome="high precision",
            observed_outcome="precision was lower than expected",
            outcome_status="failed",
            calibration_result="overconfident",
            error_type="ignored_uncertainty",
            correction="Initial confidence overreached the evidence.",
            compressed_lesson="Treat thin evidence as tentative.",
            safe_metadata={"metadata_only": True, "json_safe": True, "non_public": True, "no_runtime_wiring": True, "no_provider_calls": True, "no_tool_execution": True, "no_persistence": True, "no_memory_mutation": True, "no_project_mutation": True, "no_public_claims": True, "no_final_answer": True},
        ),
        build_forecast_calibration_record_v1(
            source_run=base_run,
            record_id="calibration-underconfident-001",
            prediction_id="prediction-calibration-007",
            prediction_statement="The next adjustment will stay bounded.",
            prediction_type="rule_pressure_prediction",
            prediction_scope="metadata_only",
            confidence_before=0.24,
            confidence_after=0.57,
            confidence_basis="underweighted source evidence",
            uncertainty_factors=["signal stronger than expected"],
            invalidation_signals=["correction applied after stronger observation"],
            expected_outcome="bounded adjustment",
            observed_outcome="stronger-than-expected confirmation",
            outcome_status="matched",
            calibration_result="underconfident",
            error_type="missing_context",
            correction="The evidence supported a stronger reading.",
            compressed_lesson="Raise confidence when repeated probes converge.",
            safe_metadata={"metadata_only": True, "json_safe": True, "non_public": True, "no_runtime_wiring": True, "no_provider_calls": True, "no_tool_execution": True, "no_persistence": True, "no_memory_mutation": True, "no_project_mutation": True, "no_public_claims": True, "no_final_answer": True},
        ),
        build_forecast_calibration_record_v1(
            source_run=base_run,
            record_id="calibration-missing-signal-001",
            prediction_id="prediction-calibration-008",
            prediction_statement="The next reading will be limited by missing evidence.",
            prediction_type="gap_prediction",
            prediction_scope="metadata_only",
            confidence_before=0.67,
            confidence_after=0.52,
            confidence_basis="partial evidence only",
            uncertainty_factors=["missing signal data"],
            invalidation_signals=["signal missing from observation set"],
            expected_outcome="observation will remain incomplete",
            observed_outcome="missing signal prevented full confirmation",
            outcome_status="blocked",
            calibration_result="missing_signal",
            error_type="missing_context",
            missing_signals=["signal window"],
            correction="Do not treat incomplete signal sets as complete.",
            compressed_lesson="Require the missing signal before closing the loop.",
            safe_metadata={"metadata_only": True, "json_safe": True, "non_public": True, "no_runtime_wiring": True, "no_provider_calls": True, "no_tool_execution": True, "no_persistence": True, "no_memory_mutation": True, "no_project_mutation": True, "no_public_claims": True, "no_final_answer": True},
        ),
        build_forecast_calibration_record_v1(
            source_run=uoa_run,
            record_id="calibration-translation-001",
            prediction_id="prediction-calibration-009",
            prediction_statement="The translation layer will remain partially bounded.",
            prediction_type="translation_prediction",
            prediction_scope="metadata_only",
            confidence_before=0.73,
            confidence_after=0.71,
            confidence_basis="competing translation layers remain open",
            uncertainty_factors=["translation not finalized"],
            invalidation_signals=["plural readings remain"],
            expected_outcome="partial translation only",
            observed_outcome="translation stayed partially bounded",
            outcome_status="matched",
            calibration_result="well_calibrated",
            error_type="translation_overreach",
            assumptions_used=["competing readings remain open"],
            safe_metadata={"metadata_only": True, "json_safe": True, "non_public": True, "no_runtime_wiring": True, "no_provider_calls": True, "no_tool_execution": True, "no_persistence": True, "no_memory_mutation": True, "no_project_mutation": True, "no_public_claims": True, "no_final_answer": True},
        ),
        build_forecast_calibration_record_v1(
            source_run=rsc_run,
            record_id="calibration-motif-probe-001",
            prediction_id="prediction-calibration-010",
            prediction_statement="Repeated motif cluster will remain stable across probes.",
            prediction_type="motif_prediction",
            prediction_scope="metadata_only",
            confidence_before=0.68,
            confidence_after=0.69,
            confidence_basis="repeated motifs and probe candidates",
            uncertainty_factors=["motif cluster still partly open"],
            invalidation_signals=["probe comparison remained bounded"],
            expected_outcome="stability across probes",
            observed_outcome="stability confirmed within metadata bounds",
            outcome_status="matched",
            calibration_result="well_calibrated",
            error_type="none",
            safe_metadata={"metadata_only": True, "json_safe": True, "non_public": True, "no_runtime_wiring": True, "no_provider_calls": True, "no_tool_execution": True, "no_persistence": True, "no_memory_mutation": True, "no_project_mutation": True, "no_public_claims": True, "no_final_answer": True},
        ),
        build_forecast_calibration_record_v1(
            source_run=calibration_run,
            record_id="calibration-ledger-001",
            prediction_id="prediction-calibration-011",
            prediction_statement="The next adjustment should remain bounded.",
            prediction_type="rule_pressure_prediction",
            prediction_scope="metadata_only",
            confidence_before=0.58,
            confidence_after=0.58,
            confidence_basis="calibration-ledger source packet",
            uncertainty_factors=["ledger comparison pending"],
            invalidation_signals=["bounded adjustment observed"],
            expected_outcome="bounded adjustment",
            observed_outcome="bounded adjustment observed",
            outcome_status="matched",
            calibration_result="well_calibrated",
            error_type="none",
            safe_metadata={"metadata_only": True, "json_safe": True, "non_public": True, "no_runtime_wiring": True, "no_provider_calls": True, "no_tool_execution": True, "no_persistence": True, "no_memory_mutation": True, "no_project_mutation": True, "no_public_claims": True, "no_final_answer": True},
        ),
    ]
