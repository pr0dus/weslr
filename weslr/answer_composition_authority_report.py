"""WESLR answer composition authority report helpers V1.

Deterministic, import-safe, side-effect-free, in-memory metadata helpers for
answer-composition authority report artifacts. These helpers do not compose
answers, generate final answers, execute prompts, create live dialogue, call
providers/search/advisors, wire runtime behavior, persist state, write files,
create judges or scores, make official claims, or grant answer authority.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from weslr.answer_composition_authority import (
    ARTIFACT_TYPE_V1 as SOURCE_ARTIFACT_TYPE_V1,
    ANSWER_COMPOSITION_AUTHORITY_MINOR_RISKS_V1,
    ANSWER_COMPOSITION_AUTHORITY_REQUIRED_GATE_STATUSES_V1,
    summarize_answer_composition_authority_artifact_v1,
    to_answer_composition_authority_artifact_json_safe_v1,
    validate_answer_composition_authority_artifact_v1,
)

SCHEMA_VERSION_V1 = "answer_composition_authority_report_schema_v1"
REPORT_TYPE_V1 = "answer_composition_authority_report_v1"
INVALID_REPORT_TYPE_V1 = "answer_composition_authority_report_v1_invalid"

ANSWER_COMPOSITION_AUTHORITY_REPORT_ALLOWED_INPUT_TYPES_V1 = (
    "answer_composition_authority_artifact_v1",
    "answer_composition_authority_artifact_validation_output_v1",
    "answer_composition_authority_artifact_summary_v1",
    "answer_composition_authority_artifact_json_safe_v1",
    "answer_composition_authority_safe_review_label_v1",
    "answer_composition_authority_safe_gate_status_label_v1",
    "answer_composition_authority_safe_risk_followup_label_v1",
)

ANSWER_COMPOSITION_AUTHORITY_REPORT_FORBIDDEN_INPUT_TYPES_V1 = (
    "raw_prompt",
    "raw_response",
    "final_answer_prose",
    "final_response_text",
    "hidden_prompt",
    "answer_key",
    "private_content",
    "provider_output",
    "model_output",
    "search_output",
    "advisor_output",
    "runtime_output",
    "live_dialogue_transcript",
    "official_score",
    "judge_decision",
    "scoring_result",
    "benchmark_pass_fail_claim",
    "turing_iq_certification_product_readiness_claim",
    "consciousness_sentience_claim",
    "dot_weslr_persistence_payload",
    "feature_flag_activation_payload",
    "chat_responder_runtime_output",
    "occ_openclaw_as_weslr_framing",
)

ANSWER_COMPOSITION_AUTHORITY_REPORT_REQUIRED_GATE_COVERAGE_V1 = {
    "evidence_gate": "not_established_or_not_present",
    "provenance_gate": "not_established_or_not_present",
    "governance_gate": "review_required_or_not_present",
    "memory_gate": "review_required_or_not_present",
    "domain_gate": "review_required_or_not_present",
    "uncertainty_gate": "required_or_not_present",
    "final_answer_gate": "generation_not_authorized",
    "runtime_gate": "runtime_wiring_requires_separate_approval",
    "prompt_execution_gate": "prompt_execution_not_authorized",
    "provider_gate": "provider_calls_not_authorized",
    "persistence_gate": "dot_weslr_writes_not_authorized",
    "official_claim_gate": "official_claim_not_allowed",
    "identity_gate": "occ_openclaw_not_weslr",
}

ANSWER_COMPOSITION_AUTHORITY_REPORT_REQUIRED_DENIED_PATHS_V1 = (
    "answer_composition_not_authorized",
    "answer_authority_not_granted",
    "runtime_authority_not_granted",
    "final_answer_generation_not_authorized",
    "prompt_execution_not_authorized",
    "live_dialogue_not_authorized",
    "provider_calls_not_authorized",
    "dot_weslr_writes_not_authorized",
    "feature_flags_not_authorized",
    "judges_scoring_not_authorized",
    "official_claims_not_allowed",
)

ANSWER_COMPOSITION_AUTHORITY_REPORT_ALLOWED_AGGREGATE_LABELS_V1 = (
    "source_artifacts_present",
    "source_artifacts_validated",
    "gate_coverage_visible",
    "denied_paths_visible",
    "risks_carried_forward",
    "metadata_only_report",
    "internal_only_report",
    "answer_composition_not_authorized",
    "answer_authority_not_granted",
    "runtime_authority_not_granted",
    "final_answer_generation_not_authorized",
    "prompt_execution_not_authorized",
    "provider_calls_not_authorized",
    "dot_weslr_writes_not_authorized",
    "feature_flags_not_authorized",
    "judges_scoring_not_authorized",
    "official_claims_not_allowed",
)

ANSWER_COMPOSITION_AUTHORITY_REPORT_FORBIDDEN_AGGREGATE_LABELS_V1 = (
    "ready_for_runtime",
    "safe_to_wire_runtime",
    "approved_for_live_answers",
    "final_answer_authorized",
    "answer_composition_authorized",
    "answer_authority_granted",
    "runtime_authority_granted",
    "passed_turing_test",
    "official_score",
    "certified",
    "production_ready",
    "product_ready",
    "conscious",
    "sentient",
)

ANSWER_COMPOSITION_AUTHORITY_REPORT_VISIBLE_RISKS_V1 = (
    "metadata-overread",
    "report-as-judge/score",
    "renderer wording drift",
    "artifact/report-as-authority",
    "OCC/WESLR identity confusion",
    "validation-pass-as-authority",
    "final-answer-prose leak",
)

_FALSE_AUTHORITY_FLAGS = (
    "answer_composition_authorized",
    "final_answer_generated",
    "answer_authority_granted",
    "runtime_authority_granted",
    "prompt_execution_allowed",
    "live_dialogue_allowed",
    "raw_content_allowed",
    "official_claim_allowed",
    "model_call_made",
    "search_call_made",
    "advisor_call_made",
    "dot_weslr_write_performed",
    "feature_flag_enabled",
    "judge_authority_granted",
    "scoring_authorized",
)

_TRUE_METADATA_FLAGS = ("metadata_only", "internal_only")

_REQUIRED_FIELDS = (
    "report_type",
    "schema_version",
    "metadata_only",
    "internal_only",
    "report_scope",
    "source_artifact_type",
    "source_artifact_count",
    "source_artifact_summaries",
    "source_artifact_validation_statuses",
    "report_inputs",
    "allowed_report_input_types",
    "forbidden_report_input_types",
    "gate_coverage_summary",
    "denied_path_summary",
    "aggregate_labels",
    "visible_risks",
    "followups",
    "validation_status",
    *_FALSE_AUTHORITY_FLAGS,
)

_ALLOWED_KEYS_WITH_RISK_WORDS = set(_REQUIRED_FIELDS) | set(ANSWER_COMPOSITION_AUTHORITY_REPORT_REQUIRED_GATE_COVERAGE_V1) | {
    "valid",
    "blocked",
    "errors",
    "warnings",
    "all_source_artifacts_valid",
    "safe_to_render",
    "invalid_wrapper",
    "final_answer_gate",
    "runtime_gate",
    "prompt_execution_gate",
    "provider_gate",
    "official_claim_gate",
    "source_artifacts_validated",
    "answer_composition_not_authorized",
    "answer_authority_not_granted",
    "runtime_authority_not_granted",
    "final_answer_generation_not_authorized",
    "runtime_wiring_requires_separate_approval",
    "metadata_evidence_not_answer_text",
    "metadata_evidence_not_answer_composition_authority",
    "metadata_evidence_not_answer_authority",
    "raw_content_allowed",
}

_UNSAFE_KEY_FRAGMENTS = (
    "raw_prompt",
    "raw_response",
    "raw_response_text",
    "raw_prompt_text",
    "final_answer_text",
    "final_answer_prose",
    "final_response_text",
    "private_content",
    "hidden_prompt",
    "answer_key",
    "provider_output",
    "model_output",
    "advisor_output",
    "search_output",
    "official_score",
    "judge_result",
    "judge_decision",
    "scoring_result",
    "runtime_output",
    "live_dialogue_transcript",
    "persistence_payload",
    "feature_flag_activation",
)

_TEXT_MARKERS = {
    "raw_content_detected": (
        "raw prompt:",
        "raw_prompt:",
        "raw response:",
        "raw_response:",
        "raw prompt text",
        "raw response text",
    ),
    "private_content_detected": ("private content:", "private user content", "protected private material"),
    "hidden_prompt_detected": ("hidden prompt:", "system prompt hidden"),
    "answer_key_detected": ("answer key:", "correct answer:"),
    "provider_output_detected": ("provider output:", "model output:", "advisor output:", "search output:", "llm output:"),
    "runtime_output_detected": ("runtime output:", "chatresponder runtime output", "chat responder runtime output"),
    "final_answer_detected": ("final answer:", "final_answer_text", "final answer prose", "final response text:"),
    "official_claim_detected": (
        "official turing pass",
        "passed the turing test",
        "passed_turing_test",
        "official iq",
        "iq score",
        "official benchmark",
        "certification claim",
        "certified product-ready",
        "product readiness certified",
        "product-readiness certified",
    ),
    "judge_or_score_detected": (
        "official score:",
        "score: 100",
        "scoring engine",
        "judge authority",
        "judge decision:",
        "judge_authority_granted=true",
        "scoring_authorized=true",
    ),
    "prompt_execution_detected": ("execute prompt", "prompt execution", "run this prompt"),
    "live_dialogue_detected": ("live dialogue", "live dialogue transcript", "create live dialogue"),
    "provider_call_detected": (
        "model_call_made=true",
        "search_call_made=true",
        "advisor_call_made=true",
        "call model",
        "call search",
        "call advisor",
        "provider call made",
    ),
    "dot_weslr_write_detected": (".weslr write", "write .weslr", "dot_weslr_write_performed=true"),
    "feature_flag_detected": ("feature_flag_enabled=true", "enable feature flag", "feature flag activation"),
    "answer_authority_detected": ("answer authority granted", "answer_authority_granted=true", "approved for live answers"),
    "composition_authority_detected": (
        "answer composition authorized",
        "answer_composition_authorized=true",
        "live answer composition authorized",
    ),
    "runtime_authority_detected": (
        "runtime authority granted",
        "runtime_authority_granted=true",
        "runtime approval granted",
    ),
    "benchmark_claim_detected": ("benchmark pass", "benchmark fail", "benchmark pass/fail", "official benchmark"),
    "consciousness_claim_detected": (
        "weslr is conscious",
        "weslr is sentient",
        "consciousness proven",
        "sentience proven",
    ),
    "identity_confusion_detected": (
        "occ is weslr",
        "openclaw is weslr",
        "occ/openclaw is weslr",
        "occ is part of deployed weslr",
        "openclaw is part of deployed weslr",
    ),
}


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return deepcopy(value)
    if isinstance(value, tuple):
        return list(deepcopy(value))
    if isinstance(value, set):
        return sorted(deepcopy(value), key=repr)
    return [deepcopy(value)]


def _json_safe(value: Any) -> Any:
    value = deepcopy(value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return _json_safe(value.to_dict())
    if hasattr(value, "__dict__"):
        return _json_safe(vars(value))
    return repr(value)


def _walk(value: Any, path: str = ""):
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_s = str(key)
            child = f"{path}.{key_s}" if path else key_s
            yield child, item
            yield from _walk(item, child)
    elif isinstance(value, list):
        for idx, item in enumerate(value):
            child = f"{path}[{idx}]"
            yield child, item
            yield from _walk(item, child)


def _append_unique(target: list[str], label: str) -> None:
    if label not in target:
        target.append(label)


def _text(value: Any) -> str:
    if isinstance(value, str):
        return value.lower()
    return ""


def _safe_error_labels(errors: list[Any]) -> list[str]:
    labels: list[str] = []
    for error in errors:
        _append_unique(labels, str(error).split(":", 1)[0])
    return labels


def _source_artifact_summary(artifact: Any) -> dict[str, Any]:
    validation = validate_answer_composition_authority_artifact_v1(artifact)  # type: ignore[arg-type]
    if validation["valid"]:
        summary = summarize_answer_composition_authority_artifact_v1(artifact)  # type: ignore[arg-type]
        return {
            "artifact_type": SOURCE_ARTIFACT_TYPE_V1,
            "valid": True,
            "blocked": False,
            "source_metadata_type_count": summary["source_metadata_type_count"],
            "composition_review_dimension_count": summary["composition_review_dimension_count"],
            "gate_status_count": summary["gate_status_count"],
            "all_authority_flags_false": summary["all_authority_flags_false"],
            "gate_statuses_valid": summary["gate_statuses_valid"],
            "metadata_only": True,
            "internal_only": True,
        }
    return {
        "artifact_type": str(validation.get("artifact_type")),
        "valid": False,
        "blocked": True,
        "errors": _safe_error_labels([str(error) for error in validation["errors"]]),
        "metadata_only": True,
        "internal_only": True,
    }


def _source_validation_status(artifact: Any) -> dict[str, Any]:
    validation = validate_answer_composition_authority_artifact_v1(artifact)  # type: ignore[arg-type]
    return {
        "artifact_type": str(validation.get("artifact_type")),
        "valid": bool(validation["valid"]),
        "blocked": bool(validation["blocked"]),
        "errors": _safe_error_labels([str(error) for error in validation["errors"]]),
        "warnings": _safe_error_labels([str(warning) for warning in validation["warnings"]]),
        "metadata_only": True,
        "internal_only": True,
    }


def _all_source_statuses_valid(report: Mapping[str, Any]) -> bool:
    statuses = report.get("source_artifact_validation_statuses")
    if not isinstance(statuses, list):
        return False
    return all(isinstance(item, Mapping) and item.get("valid") is True for item in statuses)


def build_answer_composition_authority_report_v1(
    *,
    source_artifacts: list[dict[str, Any]] | tuple[dict[str, Any], ...] | None = None,
    report_inputs: list[str] | tuple[str, ...] | None = None,
    gate_coverage_summary: Mapping[str, str] | None = None,
    denied_path_summary: list[str] | tuple[str, ...] | None = None,
    aggregate_labels: list[str] | tuple[str, ...] | None = None,
    visible_risks: list[str] | tuple[str, ...] | None = None,
    followups: list[str] | tuple[str, ...] | None = None,
) -> dict[str, Any]:
    """Build one safe metadata-only answer-composition authority report."""

    artifacts = _as_list(source_artifacts)
    gates = dict(ANSWER_COMPOSITION_AUTHORITY_REPORT_REQUIRED_GATE_COVERAGE_V1)
    if gate_coverage_summary:
        gates.update({str(key): str(value) for key, value in gate_coverage_summary.items()})

    report = {
        "report_type": REPORT_TYPE_V1,
        "schema_version": SCHEMA_VERSION_V1,
        "metadata_only": True,
        "internal_only": True,
        "report_scope": "answer_composition_authority_artifact_report",
        "source_artifact_type": SOURCE_ARTIFACT_TYPE_V1,
        "source_artifact_count": len(artifacts),
        "source_artifact_summaries": [_source_artifact_summary(artifact) for artifact in artifacts],
        "source_artifact_validation_statuses": [_source_validation_status(artifact) for artifact in artifacts],
        "report_inputs": _as_list(report_inputs) or ["answer_composition_authority_artifact_v1"],
        "allowed_report_input_types": list(ANSWER_COMPOSITION_AUTHORITY_REPORT_ALLOWED_INPUT_TYPES_V1),
        "forbidden_report_input_types": list(ANSWER_COMPOSITION_AUTHORITY_REPORT_FORBIDDEN_INPUT_TYPES_V1),
        "gate_coverage_summary": gates,
        "denied_path_summary": _as_list(denied_path_summary) or list(ANSWER_COMPOSITION_AUTHORITY_REPORT_REQUIRED_DENIED_PATHS_V1),
        "aggregate_labels": [],
        "visible_risks": _as_list(visible_risks) or list(ANSWER_COMPOSITION_AUTHORITY_REPORT_VISIBLE_RISKS_V1),
        "followups": _as_list(followups),
        "validation_status": {"valid": False, "blocked": True, "errors": [], "warnings": []},
        "answer_composition_authorized": False,
        "final_answer_generated": False,
        "answer_authority_granted": False,
        "runtime_authority_granted": False,
        "prompt_execution_allowed": False,
        "live_dialogue_allowed": False,
        "raw_content_allowed": False,
        "official_claim_allowed": False,
        "model_call_made": False,
        "search_call_made": False,
        "advisor_call_made": False,
        "dot_weslr_write_performed": False,
        "feature_flag_enabled": False,
        "judge_authority_granted": False,
        "scoring_authorized": False,
    }
    derived = derive_answer_composition_authority_report_aggregate_labels_v1(report)
    explicit = [str(item) for item in _as_list(aggregate_labels)]
    report["aggregate_labels"] = list(dict.fromkeys([*derived, *explicit]))
    validation = validate_answer_composition_authority_report_v1(report)
    report["validation_status"] = {
        "valid": validation["valid"],
        "blocked": validation["blocked"],
        "errors": _safe_error_labels(validation["errors"]),
        "warnings": _safe_error_labels(validation["warnings"]),
    }
    return report


def derive_answer_composition_authority_report_aggregate_labels_v1(report: dict) -> list[str]:
    """Derive qualitative, non-scoring report aggregate labels."""

    labels = [
        "metadata_only_report",
        "internal_only_report",
        "gate_coverage_visible",
        "denied_paths_visible",
        "risks_carried_forward",
        "answer_composition_not_authorized",
        "answer_authority_not_granted",
        "runtime_authority_not_granted",
        "final_answer_generation_not_authorized",
        "prompt_execution_not_authorized",
        "provider_calls_not_authorized",
        "dot_weslr_writes_not_authorized",
        "feature_flags_not_authorized",
        "judges_scoring_not_authorized",
        "official_claims_not_allowed",
    ]
    if isinstance(report, Mapping) and int(report.get("source_artifact_count") or 0) > 0:
        labels.insert(0, "source_artifacts_present")
    if isinstance(report, Mapping) and _all_source_statuses_valid(report):
        labels.insert(1 if "source_artifacts_present" in labels else 0, "source_artifacts_validated")
    return labels


def validate_answer_composition_authority_report_v1(report: dict) -> dict[str, Any]:
    """Validate one answer-composition authority report without side effects."""

    errors: list[str] = []
    warnings: list[str] = []
    result: dict[str, Any] = {
        "valid": False,
        "blocked": True,
        "errors": errors,
        "warnings": warnings,
        "report_type": None,
        "safety_booleans_valid": False,
        "gate_coverage_valid": False,
        "denied_paths_valid": False,
        "aggregate_labels_valid": False,
        "unknown_report_inputs": [],
        "forbidden_report_inputs": [],
        "unknown_aggregate_labels": [],
        "forbidden_aggregate_labels": [],
        "missing_denied_paths": [],
        "missing_gate_coverage": [],
        "unsafe_gate_coverage": [],
        "unsafe_source_artifacts": [],
        "raw_content_detected": False,
        "private_content_detected": False,
        "hidden_prompt_detected": False,
        "answer_key_detected": False,
        "provider_output_detected": False,
        "runtime_output_detected": False,
        "final_answer_detected": False,
        "official_claim_detected": False,
        "judge_or_score_detected": False,
        "prompt_execution_detected": False,
        "live_dialogue_detected": False,
        "provider_call_detected": False,
        "dot_weslr_write_detected": False,
        "feature_flag_detected": False,
        "answer_authority_detected": False,
        "composition_authority_detected": False,
        "runtime_authority_detected": False,
        "benchmark_claim_detected": False,
        "consciousness_claim_detected": False,
        "identity_confusion_detected": False,
    }

    if not isinstance(report, Mapping):
        errors.append("report_not_mapping")
        return result

    result["report_type"] = report.get("report_type")
    if report.get("report_type") != REPORT_TYPE_V1:
        errors.append("report_type_invalid")
    if report.get("schema_version") != SCHEMA_VERSION_V1:
        errors.append("schema_version_invalid")

    for field in _REQUIRED_FIELDS:
        if field not in report:
            errors.append(f"missing_required_field:{field}")

    for flag in _TRUE_METADATA_FLAGS:
        if report.get(flag) is not True:
            errors.append(f"metadata_flag_not_true:{flag}")

    safety_ok = True
    for flag in _FALSE_AUTHORITY_FLAGS:
        if flag not in report:
            safety_ok = False
            continue
        if report.get(flag) is not False:
            safety_ok = False
            errors.append(f"authority_flag_not_false:{flag}")
    result["safety_booleans_valid"] = safety_ok

    if report.get("report_scope") != "answer_composition_authority_artifact_report":
        errors.append("report_scope_invalid")
    if report.get("source_artifact_type") != SOURCE_ARTIFACT_TYPE_V1:
        errors.append("source_artifact_type_invalid")

    summaries = report.get("source_artifact_summaries")
    statuses = report.get("source_artifact_validation_statuses")
    source_count = report.get("source_artifact_count")
    if not isinstance(source_count, int) or source_count < 0:
        errors.append("source_artifact_count_invalid")
    if not isinstance(summaries, list):
        errors.append("source_artifact_summaries_not_list")
    elif isinstance(source_count, int) and len(summaries) != source_count:
        errors.append("source_artifact_summaries_count_mismatch")
    if not isinstance(statuses, list):
        errors.append("source_artifact_validation_statuses_not_list")
    elif isinstance(source_count, int) and len(statuses) != source_count:
        errors.append("source_artifact_validation_statuses_count_mismatch")
    elif statuses:
        unsafe = [str(idx) for idx, item in enumerate(statuses) if not isinstance(item, Mapping) or item.get("valid") is not True]
        result["unsafe_source_artifacts"] = unsafe
        if unsafe:
            errors.append("source_artifact_validation_status_not_valid")

    allowed_inputs = set(ANSWER_COMPOSITION_AUTHORITY_REPORT_ALLOWED_INPUT_TYPES_V1)
    forbidden_inputs = set(ANSWER_COMPOSITION_AUTHORITY_REPORT_FORBIDDEN_INPUT_TYPES_V1)
    report_inputs = [str(item) for item in _as_list(report.get("report_inputs"))]
    unknown_inputs = [item for item in report_inputs if item not in allowed_inputs]
    forbidden_input_hits = [item for item in report_inputs if item in forbidden_inputs]
    result["unknown_report_inputs"] = unknown_inputs
    result["forbidden_report_inputs"] = forbidden_input_hits
    if unknown_inputs:
        errors.append("unknown_report_inputs")
    if forbidden_input_hits:
        errors.append("forbidden_report_inputs")

    if set(_as_list(report.get("allowed_report_input_types"))) != allowed_inputs:
        errors.append("allowed_report_input_types_invalid")
    if set(_as_list(report.get("forbidden_report_input_types"))) != forbidden_inputs:
        errors.append("forbidden_report_input_types_invalid")

    gates = report.get("gate_coverage_summary")
    if not isinstance(gates, Mapping):
        errors.append("gate_coverage_summary_not_mapping")
    else:
        missing_gates: list[str] = []
        unsafe_gates: list[str] = []
        for gate, required_status in ANSWER_COMPOSITION_AUTHORITY_REPORT_REQUIRED_GATE_COVERAGE_V1.items():
            if gate not in gates:
                missing_gates.append(gate)
            elif gates.get(gate) != required_status:
                unsafe_gates.append(f"{gate}:{gates.get(gate)}")
        result["missing_gate_coverage"] = missing_gates
        result["unsafe_gate_coverage"] = unsafe_gates
        if missing_gates:
            errors.append("missing_gate_coverage")
        if unsafe_gates:
            errors.append("unsafe_gate_coverage")
        result["gate_coverage_valid"] = not missing_gates and not unsafe_gates

    denied = set(str(item) for item in _as_list(report.get("denied_path_summary")))
    required_denied = set(ANSWER_COMPOSITION_AUTHORITY_REPORT_REQUIRED_DENIED_PATHS_V1)
    missing_denied = sorted(required_denied - denied)
    result["missing_denied_paths"] = missing_denied
    if missing_denied:
        errors.append("missing_denied_paths")
    result["denied_paths_valid"] = not missing_denied

    allowed_labels = set(ANSWER_COMPOSITION_AUTHORITY_REPORT_ALLOWED_AGGREGATE_LABELS_V1)
    forbidden_labels = set(ANSWER_COMPOSITION_AUTHORITY_REPORT_FORBIDDEN_AGGREGATE_LABELS_V1)
    aggregate_labels = [str(item) for item in _as_list(report.get("aggregate_labels"))]
    unknown_labels = [item for item in aggregate_labels if item not in allowed_labels]
    forbidden_label_hits = [item for item in aggregate_labels if item in forbidden_labels]
    result["unknown_aggregate_labels"] = unknown_labels
    result["forbidden_aggregate_labels"] = forbidden_label_hits
    if unknown_labels:
        errors.append("unknown_aggregate_labels")
    if forbidden_label_hits:
        errors.append("forbidden_aggregate_labels")
    result["aggregate_labels_valid"] = not unknown_labels and not forbidden_label_hits

    visible_risks = set(str(item) for item in _as_list(report.get("visible_risks")))
    missing_risks = sorted(set(ANSWER_COMPOSITION_AUTHORITY_REPORT_VISIBLE_RISKS_V1) - visible_risks)
    if missing_risks:
        warnings.append("missing_visible_risks")

    validation_status = report.get("validation_status")
    if not isinstance(validation_status, Mapping):
        errors.append("validation_status_not_mapping")
    elif not {"valid", "blocked", "errors", "warnings"}.issubset(set(validation_status.keys())):
        errors.append("validation_status_missing_fields")

    for path, value in _walk(report):
        leaf = path.rsplit(".", 1)[-1]
        if leaf not in _ALLOWED_KEYS_WITH_RISK_WORDS:
            leaf_lower = leaf.lower()
            if any(fragment in leaf_lower for fragment in _UNSAFE_KEY_FRAGMENTS):
                errors.append(f"unsafe_key_detected:{path}")
        if path.startswith("forbidden_report_input_types"):
            continue
        text = _text(value)
        if not text:
            continue
        for key, markers in _TEXT_MARKERS.items():
            if any(marker in text for marker in markers):
                result[key] = True
                _append_unique(errors, key)
        for label in ANSWER_COMPOSITION_AUTHORITY_REPORT_FORBIDDEN_AGGREGATE_LABELS_V1:
            if text == label or f"`{label}`" in text:
                _append_unique(errors, "forbidden_label_drift")

    if not errors:
        result["valid"] = True
        result["blocked"] = False
    return result


def summarize_answer_composition_authority_report_v1(report: dict) -> dict[str, Any]:
    """Summarize one report using safe counts and labels only."""

    validation = validate_answer_composition_authority_report_v1(report)
    if not validation["valid"]:
        return {
            "report_type": INVALID_REPORT_TYPE_V1,
            "valid": False,
            "blocked": True,
            "errors": _safe_error_labels(validation["errors"]),
            "warnings": _safe_error_labels(validation["warnings"]),
            "metadata_only": True,
            "internal_only": True,
            "answer_composition_authorized": False,
            "answer_authority_granted": False,
            "final_answer_generated": False,
            "runtime_authority_granted": False,
            "next_lane_recommendation": "REVIEW_INVALID_COMPOSITION_AUTHORITY_REPORT_METADATA_ONLY_BEFORE_ANY_RUNTIME_OR_FINAL_ANSWER_LANE",
        }

    return {
        "report_type": REPORT_TYPE_V1,
        "valid": True,
        "blocked": False,
        "metadata_only": True,
        "internal_only": True,
        "source_artifact_count": report["source_artifact_count"],
        "source_artifact_valid_count": sum(1 for item in report["source_artifact_validation_statuses"] if item.get("valid") is True),
        "gate_coverage_count": len(report["gate_coverage_summary"]),
        "denied_path_count": len(report["denied_path_summary"]),
        "aggregate_labels": _json_safe(report["aggregate_labels"]),
        "visible_risks": _json_safe(report["visible_risks"]),
        "followups": _json_safe(report["followups"]),
        "all_authority_flags_false": all(report.get(flag) is False for flag in _FALSE_AUTHORITY_FLAGS),
        "gate_coverage_valid": validation["gate_coverage_valid"],
        "denied_paths_valid": validation["denied_paths_valid"],
        "aggregate_labels_valid": validation["aggregate_labels_valid"],
        "safety_confirmation": [
            "metadata evidence may inform future review",
            "metadata evidence is not answer text",
            "metadata evidence is not answer composition authority",
            "metadata evidence is not answer authority",
            "report helpers do not compose or approve answers",
        ],
        "answer_composition_authorized": False,
        "answer_authority_granted": False,
        "final_answer_generated": False,
        "runtime_authority_granted": False,
        "next_lane_recommendation": "REVIEW_ANSWER_COMPOSITION_AUTHORITY_REPORT_HELPERS_IMPLEMENTATION_V1",
    }


def render_answer_composition_authority_report_markdown_v1(report: dict) -> str:
    """Render safe internal Markdown for one report."""

    validation = validate_answer_composition_authority_report_v1(report)
    if not validation["valid"]:
        reason_lines = [f"- `{reason}`" for reason in _safe_error_labels(validation["errors"])]
        if not reason_lines:
            reason_lines = ["- `invalid_report`"]
        return "\n".join(
            [
                "# WESLR Answer Composition Authority Report V1 — Blocked",
                "",
                "## Report status",
                "- valid: `False`",
                "- blocked: `True`",
                "- safe_to_render: `False`",
                "- metadata_only: `True`",
                "- internal_only: `True`",
                "",
                "## Safe reason labels",
                *reason_lines,
                "",
                "## Safety confirmation",
                "- unsafe content was not rendered",
                "- metadata evidence is not answer text",
                "- metadata evidence is not answer composition authority",
                "- metadata evidence is not answer authority",
                "",
                "## Next lane recommendation",
                "- `REVIEW_INVALID_COMPOSITION_AUTHORITY_REPORT_METADATA_ONLY_BEFORE_ANY_RUNTIME_OR_FINAL_ANSWER_LANE`",
                "",
            ]
        )

    summary = summarize_answer_composition_authority_report_v1(report)
    gate_lines = [f"- `{gate}`: `{status}`" for gate, status in sorted(report["gate_coverage_summary"].items())]
    denied_lines = [f"- `{path}`" for path in report["denied_path_summary"]]
    aggregate_lines = [f"- `{label}`" for label in summary["aggregate_labels"]]
    risk_lines = [f"- `{risk}`" for risk in summary["visible_risks"]]
    followup_lines = [f"- `{followup}`" for followup in summary["followups"]] or ["- `none_recorded`"]
    return "\n".join(
        [
            "# WESLR Answer Composition Authority Report V1",
            "",
            "## Report status",
            "- report_type: `answer_composition_authority_report_v1`",
            "- metadata_only: `True`",
            "- internal_only: `True`",
            "- valid: `True`",
            "- blocked: `False`",
            "",
            "## Source artifact counts",
            f"- source_artifact_count: `{summary['source_artifact_count']}`",
            f"- source_artifact_valid_count: `{summary['source_artifact_valid_count']}`",
            "",
            "## Gate coverage",
            *gate_lines,
            "",
            "## Denied paths",
            *denied_lines,
            "",
            "## Aggregate labels",
            *aggregate_lines,
            "",
            "## Visible risks",
            *risk_lines,
            "",
            "## Followups",
            *followup_lines,
            "",
            "## Safety confirmation",
            "- metadata evidence may inform future review",
            "- metadata evidence is not answer text",
            "- metadata evidence is not answer composition authority",
            "- metadata evidence is not answer authority",
            "- report helpers do not compose, approve, select, or generate answers",
            "- no raw prompts, raw responses, private content, hidden prompts, answer keys, provider output, official scores, runtime output, or final-answer prose rendered",
            "",
            "## Next lane recommendation",
            f"- `{summary['next_lane_recommendation']}`",
            "",
        ]
    )


def to_answer_composition_authority_report_json_safe_v1(report: dict) -> dict[str, Any]:
    """Return a JSON-safe metadata report copy or explicit invalid wrapper."""

    validation = validate_answer_composition_authority_report_v1(report)
    if not validation["valid"]:
        return {
            "report_type": INVALID_REPORT_TYPE_V1,
            "valid": False,
            "blocked": True,
            "safe_to_render": False,
            "invalid_wrapper": True,
            "errors": _safe_error_labels(validation["errors"]),
            "metadata_only": True,
            "internal_only": True,
            "answer_composition_authorized": False,
            "answer_authority_granted": False,
            "final_answer_generated": False,
            "runtime_authority_granted": False,
        }
    return _json_safe(report)
