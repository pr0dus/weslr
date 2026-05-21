"""WESLR controlled answer-composition dry-run helpers V1.

Deterministic, import-safe, side-effect-free, in-memory metadata helpers for
controlled answer-composition dry-run artifacts. These helpers do not execute a
dry run, compose answers, generate final answers, execute prompts, create live
dialogue, call providers/search/advisors, wire runtime behavior, persist state,
write files, create judges or scores, make official claims, or grant answer
composition authority.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

ARTIFACT_TYPE_V1 = "controlled_answer_composition_dry_run_artifact_v1"
SCHEMA_VERSION_V1 = "controlled_answer_composition_dry_run_artifact_schema_v1"
INVALID_ARTIFACT_TYPE_V1 = "controlled_answer_composition_dry_run_artifact_v1_invalid"

SOURCE_BOUNDARY_DOC_V1 = "docs/WESLR_CONTROLLED_ANSWER_COMPOSITION_DRY_RUN_BOUNDARY_V1.md"
SOURCE_BOUNDARY_REVIEW_DOC_V1 = "docs/WESLR_CONTROLLED_ANSWER_COMPOSITION_DRY_RUN_BOUNDARY_REVIEW_V1.md"
SOURCE_HELPERS_DESIGN_DOC_V1 = "docs/WESLR_CONTROLLED_ANSWER_COMPOSITION_DRY_RUN_HELPERS_V1.md"
SOURCE_HELPERS_REVIEW_DOC_V1 = "docs/WESLR_CONTROLLED_ANSWER_COMPOSITION_DRY_RUN_HELPERS_REVIEW_V1.md"
FUTURE_HELPER_MODULE_PATH_V1 = "weslr/controlled_answer_composition_dry_run.py"
FUTURE_TEST_MODULE_PATH_V1 = "weslr/tests/test_controlled_answer_composition_dry_run_v1.py"
NEXT_LANE_V1 = "REVIEW_CONTROLLED_ANSWER_COMPOSITION_DRY_RUN_HELPERS_IMPLEMENTATION_V1"

ALLOWED_GATE_STATUSES_V1 = (
    "present",
    "missing",
    "blocked",
    "insufficient",
    "not_required",
    "blocked_not_authorized",
)

REQUIRED_GATE_STATUSES_V1 = {
    "evidence_gate": "missing",
    "provenance_gate": "missing",
    "governance_gate": "missing",
    "memory_gate": "not_required",
    "domain_gate": "missing",
    "uncertainty_gate": "missing",
    "response_obligation_gate": "missing",
    "ranked_state_grounding_gate": "missing",
    "final_answer_gate": "blocked_not_authorized",
    "runtime_gate": "blocked_not_authorized",
    "prompt_execution_gate": "blocked_not_authorized",
    "provider_gate": "blocked_not_authorized",
    "persistence_gate": "blocked_not_authorized",
    "feature_flag_gate": "blocked_not_authorized",
    "judge_scoring_gate": "blocked_not_authorized",
    "official_claim_gate": "blocked_not_authorized",
}

ALLOWED_SYNTHETIC_METADATA_INPUTS_V1 = (
    "safe_artifact_type_label",
    "safe_schema_version_label",
    "safe_source_path_label",
    "synthetic_task_intent_label",
    "synthetic_response_obligation_label",
    "synthetic_evidence_gate_status",
    "synthetic_provenance_gate_status",
    "synthetic_governance_gate_status",
    "synthetic_memory_gate_status",
    "synthetic_domain_gate_status",
    "synthetic_uncertainty_gate_status",
    "synthetic_ranked_state_grounding_label",
    "synthetic_candidate_metadata_count",
    "synthetic_selected_candidate_metadata_presence_boolean",
    "synthetic_rejected_candidate_reason_label",
    "safe_validation_status_label",
    "safe_risk_label",
    "safe_followup_label",
    "required_false_no_authority_boolean",
)

FORBIDDEN_INPUTS_V1 = (
    "real_user_query_text",
    "raw_prompt_text",
    "raw_response_text",
    "private_content",
    "hidden_prompt",
    "answer_key",
    "provider_output",
    "model_output",
    "search_output",
    "advisor_output",
    "runtime_output",
    "live_dialogue_transcript_content",
    "final_answer_prose",
    "final_response_text",
    "answer_draft_text",
    "composed_reply",
    "official_benchmark_claim",
    "official_turing_claim",
    "official_iq_claim",
    "certification_claim",
    "product_readiness_claim",
    "consciousness_sentience_claim",
    "official_score",
    "judge_decision",
    "scoring_result",
    "dot_weslr_state_payload",
    "feature_flag_activation_payload",
    "runtime_wiring_payload",
    "chat_responder_call",
    "respond_chat_call",
    "generate_chat_call",
)

FALSE_AUTHORITY_FIELDS_V1 = (
    "answer_composition_attempted",
    "answer_composition_authorized",
    "final_answer_generated",
    "answer_authority_granted",
    "composition_authority_granted",
    "runtime_authority_granted",
    "prompt_execution_allowed",
    "live_dialogue_allowed",
    "raw_content_allowed",
    "official_claim_allowed",
    "model_call_made",
    "search_call_made",
    "advisor_call_made",
    "provider_call_made",
    "dot_weslr_write_performed",
    "feature_flag_enabled",
    "judge_authority_granted",
    "scoring_authorized",
)

ADDITIONAL_FALSE_FIELDS_V1 = (
    "chat_responder_called",
    "chat_responder_modified",
    "runtime_wired",
    "prompt_execution_performed",
    "live_dialogue_performed",
    "dry_run_executed",
    "dry_run_result_artifact_created",
    "user_facing_output_created",
)

REQUIRED_NO_AUTHORITY_LABELS_V1 = (
    "helper_metadata_not_answer_text",
    "dry_run_artifact_not_final_answer",
    "validation_pass_not_answer_authority",
    "validation_pass_not_composition_authority",
    "artifact_presence_not_runtime_authority",
    "answer_composition_requires_separate_approval",
    "final_answer_generation_requires_separate_approval",
    "runtime_wiring_requires_separate_approval",
    "occ_openclaw_not_deployed_weslr",
)

VISIBLE_RISKS_V1 = (
    "metadata-overread",
    "artifact/report-as-authority",
    "validation-pass-as-authority",
    "helper-existence-as-authority",
    "renderer wording drift",
    "final-answer-prose leak",
    "OCC/WESLR identity confusion",
)

DEFAULT_SUMMARY_LABELS_V1 = (
    "metadata_only_artifact",
    "internal_only_artifact",
    "synthetic_only_artifact",
    "helper_only_artifact",
    "non_runtime_artifact",
    "answer_composition_not_attempted",
    "answer_composition_not_authorized",
    "final_answer_not_generated",
    "runtime_not_wired",
    "prompt_execution_not_allowed",
    "provider_calls_not_made",
    "dot_weslr_not_written",
    "judges_scoring_not_authorized",
    "official_claims_not_allowed",
)

_REQUIRED_TRUE_FIELDS = (
    "metadata_only",
    "internal_only",
    "synthetic_only",
    "helper_only",
    "non_runtime",
    "non_user_facing",
    "deterministic",
    "import_safe",
    "side_effect_free",
    "in_memory_only",
    "qualitative_only",
)

_REQUIRED_FIELDS = (
    "artifact_type",
    "schema_version",
    *_REQUIRED_TRUE_FIELDS,
    "source_boundary_doc",
    "source_boundary_review_doc",
    "source_helpers_design_doc",
    "source_helpers_review_doc",
    "future_helper_module_path",
    "future_test_module_path",
    "allowed_synthetic_metadata_inputs",
    "forbidden_inputs_checked",
    "required_false_no_authority_fields",
    "required_no_authority_labels",
    "gate_statuses",
    "blocked",
    "blocked_reasons",
    "visible_risks",
    "summary_labels",
    "validation_labels",
    "next_lane",
    *FALSE_AUTHORITY_FIELDS_V1,
    *ADDITIONAL_FALSE_FIELDS_V1,
)

_UNSAFE_KEY_FRAGMENTS = (
    "real_user_query",
    "raw_prompt",
    "raw_response",
    "raw_prompt_text",
    "raw_response_text",
    "private_content",
    "hidden_prompt",
    "answer_key",
    "provider_output",
    "model_output",
    "search_output",
    "advisor_output",
    "runtime_output",
    "live_dialogue",
    "final_answer",
    "final_response",
    "answer_draft",
    "composed_reply",
    "official_score",
    "judge_decision",
    "scoring_result",
    "dot_weslr_state_payload",
    "feature_flag_activation",
    "runtime_wiring_payload",
)

_ALLOWED_KEYS_WITH_RISK_WORDS = set(_REQUIRED_FIELDS) | set(REQUIRED_GATE_STATUSES_V1) | {
    "final_answer_generated",
    "final_answer_gate",
    "runtime_gate",
    "prompt_execution_gate",
    "provider_gate",
    "official_claim_gate",
    "final_answer_not_generated",
    "final_answer_generation_requires_separate_approval",
    "runtime_wiring_requires_separate_approval",
    "raw_content_allowed",
}

_TEXT_MARKERS = {
    "raw_content_detected": ("raw prompt:", "raw response:", "raw_prompt:", "raw_response:"),
    "private_content_detected": ("private content:", "private user content", "protected private material"),
    "hidden_prompt_detected": ("hidden prompt:", "system prompt hidden"),
    "answer_key_detected": ("answer key:", "correct answer:"),
    "provider_output_detected": ("provider output:", "model output:", "search output:", "advisor output:", "llm output:"),
    "runtime_output_detected": ("runtime output:", "chatresponder runtime output", "chat responder runtime output"),
    "live_dialogue_detected": ("live dialogue transcript", "live dialogue:"),
    "final_answer_detected": ("final answer:", "final answer prose", "final response text:", "final_answer_text"),
    "official_claim_detected": (
        "official turing pass",
        "passed the turing test",
        "official iq",
        "official benchmark",
        "certified product-ready",
        "product readiness certified",
    ),
    "judge_or_score_detected": ("official score:", "score: 100", "judge decision:", "judge_authority_granted=true"),
    "prompt_execution_detected": ("execute prompt", "prompt execution", "run this prompt"),
    "provider_call_detected": ("model_call_made=true", "search_call_made=true", "advisor_call_made=true", "provider_call_made=true"),
    "dot_weslr_write_detected": ("write .weslr", ".weslr write", "dot_weslr_write_performed=true"),
    "feature_flag_detected": ("feature_flag_enabled=true", "enable feature flag"),
    "answer_authority_detected": ("answer authority granted", "answer_authority_granted=true", "approved for live answers"),
    "composition_authority_detected": ("composition authority granted", "answer_composition_authorized=true"),
    "runtime_authority_detected": ("runtime authority granted", "runtime_authority_granted=true"),
    "consciousness_claim_detected": ("weslr is conscious", "weslr is sentient", "consciousness proven", "sentience proven"),
    "identity_confusion_detected": ("occ is weslr", "openclaw is weslr", "occ/openclaw is weslr"),
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


def _append_unique(target: list[str], label: str) -> None:
    if label not in target:
        target.append(label)


def _text(value: Any) -> str:
    if isinstance(value, str):
        return value.lower()
    return ""


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


def _json_safe(value: Any) -> Any:
    value = deepcopy(value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    return repr(value)


def _safe_error_labels(errors: list[Any]) -> list[str]:
    labels: list[str] = []
    for error in errors:
        _append_unique(labels, str(error).split(":", 1)[0])
    return labels


def _detect_unsafe_content(value: Any) -> dict[str, bool]:
    found = {label: False for label in _TEXT_MARKERS}
    for path, item in _walk(value):
        key = path.rsplit(".", 1)[-1].split("[", 1)[0]
        key_l = key.lower()
        if any(fragment in key_l for fragment in _UNSAFE_KEY_FRAGMENTS) and key_l not in _ALLOWED_KEYS_WITH_RISK_WORDS:
            if "final_answer" in key_l or "final_response" in key_l:
                found["final_answer_detected"] = True
            elif "provider" in key_l or "model" in key_l or "search" in key_l or "advisor" in key_l:
                found["provider_output_detected"] = True
            elif "runtime" in key_l:
                found["runtime_output_detected"] = True
            elif "private" in key_l:
                found["private_content_detected"] = True
            elif "hidden" in key_l:
                found["hidden_prompt_detected"] = True
            elif "answer_key" in key_l:
                found["answer_key_detected"] = True
            elif "judge" in key_l or "score" in key_l:
                found["judge_or_score_detected"] = True
            else:
                found["raw_content_detected"] = True
        text = _text(item)
        if not text:
            continue
        for label, markers in _TEXT_MARKERS.items():
            if any(marker in text for marker in markers):
                found[label] = True
    return found


def _derive_blocked_reasons(artifact: Mapping[str, Any]) -> list[str]:
    reasons: list[str] = []
    detections = _detect_unsafe_content(artifact)
    for label, detected in detections.items():
        if detected:
            _append_unique(reasons, label)
    for flag in (*FALSE_AUTHORITY_FIELDS_V1, *ADDITIONAL_FALSE_FIELDS_V1):
        if artifact.get(flag) is not False:
            _append_unique(reasons, f"authority_flag_not_false:{flag}")
    gates = artifact.get("gate_statuses")
    if isinstance(gates, Mapping):
        for gate in (
            "final_answer_gate",
            "runtime_gate",
            "prompt_execution_gate",
            "provider_gate",
            "persistence_gate",
            "feature_flag_gate",
            "judge_scoring_gate",
            "official_claim_gate",
        ):
            if gates.get(gate) != "blocked_not_authorized":
                _append_unique(reasons, f"gate_not_blocked_not_authorized:{gate}")
    return reasons


def build_controlled_answer_composition_dry_run_artifact_v1(
    *,
    allowed_synthetic_metadata_inputs: list[str] | tuple[str, ...] | None = None,
    forbidden_inputs_checked: list[str] | tuple[str, ...] | None = None,
    gate_statuses: Mapping[str, str] | None = None,
    blocked_reasons: list[str] | tuple[str, ...] | None = None,
    visible_risks: list[str] | tuple[str, ...] | None = None,
    summary_labels: list[str] | tuple[str, ...] | None = None,
    validation_labels: list[str] | tuple[str, ...] | None = None,
) -> dict[str, Any]:
    """Build one safe metadata-only controlled dry-run artifact."""

    gates = dict(REQUIRED_GATE_STATUSES_V1)
    if gate_statuses:
        gates.update({str(key): str(value) for key, value in gate_statuses.items()})

    artifact: dict[str, Any] = {
        "artifact_type": ARTIFACT_TYPE_V1,
        "schema_version": SCHEMA_VERSION_V1,
        "metadata_only": True,
        "internal_only": True,
        "synthetic_only": True,
        "helper_only": True,
        "non_runtime": True,
        "non_user_facing": True,
        "deterministic": True,
        "import_safe": True,
        "side_effect_free": True,
        "in_memory_only": True,
        "qualitative_only": True,
        "source_boundary_doc": SOURCE_BOUNDARY_DOC_V1,
        "source_boundary_review_doc": SOURCE_BOUNDARY_REVIEW_DOC_V1,
        "source_helpers_design_doc": SOURCE_HELPERS_DESIGN_DOC_V1,
        "source_helpers_review_doc": SOURCE_HELPERS_REVIEW_DOC_V1,
        "future_helper_module_path": FUTURE_HELPER_MODULE_PATH_V1,
        "future_test_module_path": FUTURE_TEST_MODULE_PATH_V1,
        "allowed_synthetic_metadata_inputs": _as_list(allowed_synthetic_metadata_inputs) or list(ALLOWED_SYNTHETIC_METADATA_INPUTS_V1),
        "forbidden_inputs_checked": _as_list(forbidden_inputs_checked) or list(FORBIDDEN_INPUTS_V1),
        "required_false_no_authority_fields": {field: False for field in FALSE_AUTHORITY_FIELDS_V1},
        "required_no_authority_labels": list(REQUIRED_NO_AUTHORITY_LABELS_V1),
        "gate_statuses": gates,
        "blocked": False,
        "blocked_reasons": _as_list(blocked_reasons),
        "visible_risks": _as_list(visible_risks) or list(VISIBLE_RISKS_V1),
        "summary_labels": list(dict.fromkeys([*DEFAULT_SUMMARY_LABELS_V1, *[str(item) for item in _as_list(summary_labels)]])),
        "validation_labels": _as_list(validation_labels) or ["validation_pass_metadata_quality_evidence_only"],
        "next_lane": NEXT_LANE_V1,
    }
    for flag in (*FALSE_AUTHORITY_FIELDS_V1, *ADDITIONAL_FALSE_FIELDS_V1):
        artifact[flag] = False

    derived_blocked_reasons = _derive_blocked_reasons(artifact)
    for reason in derived_blocked_reasons:
        _append_unique(artifact["blocked_reasons"], reason)
    artifact["blocked"] = bool(artifact["blocked_reasons"])
    return artifact


def validate_controlled_answer_composition_dry_run_artifact_v1(artifact: Mapping[str, Any]) -> dict[str, Any]:
    """Validate one controlled dry-run artifact without side effects."""

    errors: list[str] = []
    warnings: list[str] = []
    result: dict[str, Any] = {
        "valid": False,
        "blocked": True,
        "errors": errors,
        "warnings": warnings,
        "artifact_type": None,
        "safety_booleans_valid": False,
        "gate_statuses_valid": False,
        "safe_to_render": False,
        "json_safe": False,
    }
    for label in _TEXT_MARKERS:
        result[label] = False

    if not isinstance(artifact, Mapping):
        errors.append("artifact_not_mapping")
        return result

    result["artifact_type"] = artifact.get("artifact_type")
    if artifact.get("artifact_type") != ARTIFACT_TYPE_V1:
        errors.append("artifact_type_invalid")
    if artifact.get("schema_version") != SCHEMA_VERSION_V1:
        errors.append("schema_version_invalid")

    for field in _REQUIRED_FIELDS:
        if field not in artifact:
            errors.append(f"missing_required_field:{field}")

    for field in _REQUIRED_TRUE_FIELDS:
        if artifact.get(field) is not True:
            errors.append(f"required_true_field_invalid:{field}")

    safety_ok = True
    for flag in (*FALSE_AUTHORITY_FIELDS_V1, *ADDITIONAL_FALSE_FIELDS_V1):
        if artifact.get(flag) is not False:
            safety_ok = False
            errors.append(f"authority_flag_not_false:{flag}")
    result["safety_booleans_valid"] = safety_ok

    required_false = artifact.get("required_false_no_authority_fields")
    if not isinstance(required_false, Mapping):
        errors.append("required_false_no_authority_fields_not_mapping")
    else:
        for flag in FALSE_AUTHORITY_FIELDS_V1:
            if required_false.get(flag) is not False:
                errors.append(f"required_false_map_invalid:{flag}")

    if artifact.get("source_boundary_doc") != SOURCE_BOUNDARY_DOC_V1:
        errors.append("source_boundary_doc_invalid")
    if artifact.get("source_boundary_review_doc") != SOURCE_BOUNDARY_REVIEW_DOC_V1:
        errors.append("source_boundary_review_doc_invalid")
    if artifact.get("source_helpers_design_doc") != SOURCE_HELPERS_DESIGN_DOC_V1:
        errors.append("source_helpers_design_doc_invalid")
    if artifact.get("source_helpers_review_doc") != SOURCE_HELPERS_REVIEW_DOC_V1:
        errors.append("source_helpers_review_doc_invalid")
    if artifact.get("future_helper_module_path") != FUTURE_HELPER_MODULE_PATH_V1:
        errors.append("future_helper_module_path_invalid")
    if artifact.get("future_test_module_path") != FUTURE_TEST_MODULE_PATH_V1:
        errors.append("future_test_module_path_invalid")
    if artifact.get("next_lane") != NEXT_LANE_V1:
        errors.append("next_lane_invalid")

    gates = artifact.get("gate_statuses")
    gate_ok = True
    if not isinstance(gates, Mapping):
        errors.append("gate_statuses_not_mapping")
        gate_ok = False
    else:
        for gate, required_default in REQUIRED_GATE_STATUSES_V1.items():
            if gate not in gates:
                errors.append(f"missing_gate_status:{gate}")
                gate_ok = False
                continue
            value = gates.get(gate)
            if value not in ALLOWED_GATE_STATUSES_V1:
                errors.append(f"invalid_gate_status:{gate}")
                gate_ok = False
            if required_default == "blocked_not_authorized" and value != "blocked_not_authorized":
                errors.append(f"authority_gate_not_blocked:{gate}")
                gate_ok = False
    result["gate_statuses_valid"] = gate_ok

    allowed_inputs = [str(item) for item in _as_list(artifact.get("allowed_synthetic_metadata_inputs"))]
    unknown_allowed_inputs = [item for item in allowed_inputs if item not in ALLOWED_SYNTHETIC_METADATA_INPUTS_V1]
    if unknown_allowed_inputs:
        errors.append("unknown_allowed_synthetic_metadata_inputs")
        result["unknown_allowed_synthetic_metadata_inputs"] = unknown_allowed_inputs

    forbidden_checked = [str(item) for item in _as_list(artifact.get("forbidden_inputs_checked"))]
    missing_forbidden_checks = [item for item in FORBIDDEN_INPUTS_V1 if item not in forbidden_checked]
    if missing_forbidden_checks:
        errors.append("missing_forbidden_input_checks")
        result["missing_forbidden_input_checks"] = missing_forbidden_checks

    no_authority_labels = [str(item) for item in _as_list(artifact.get("required_no_authority_labels"))]
    missing_no_authority_labels = [item for item in REQUIRED_NO_AUTHORITY_LABELS_V1 if item not in no_authority_labels]
    if missing_no_authority_labels:
        errors.append("missing_no_authority_labels")
        result["missing_no_authority_labels"] = missing_no_authority_labels

    detections = _detect_unsafe_content(artifact)
    for label, detected in detections.items():
        result[label] = detected
        if detected:
            errors.append(label)

    blocked_reasons = [str(item) for item in _as_list(artifact.get("blocked_reasons"))]
    if artifact.get("blocked") is True and not blocked_reasons:
        errors.append("blocked_without_reasons")
    if artifact.get("blocked") is False and blocked_reasons:
        errors.append("blocked_reasons_present_when_not_blocked")
    if artifact.get("blocked") not in (True, False):
        errors.append("blocked_not_boolean")

    try:
        json_safe = to_controlled_answer_composition_dry_run_artifact_json_safe_v1(dict(artifact))
        result["json_safe"] = isinstance(json_safe, Mapping)
    except Exception:  # pragma: no cover - defensive only; no unsafe message is exposed.
        result["json_safe"] = False
        errors.append("json_safe_conversion_failed")

    result["safe_to_render"] = not any(bool(result[label]) for label in _TEXT_MARKERS)
    result["valid"] = not errors and artifact.get("blocked") is False
    result["blocked"] = not result["valid"]
    return result


def summarize_controlled_answer_composition_dry_run_artifact_v1(artifact: Mapping[str, Any]) -> dict[str, Any]:
    """Summarize one controlled dry-run artifact using safe labels only."""

    validation = validate_controlled_answer_composition_dry_run_artifact_v1(artifact)
    gates = artifact.get("gate_statuses") if isinstance(artifact, Mapping) else None
    return {
        "artifact_type": str(artifact.get("artifact_type", INVALID_ARTIFACT_TYPE_V1)) if isinstance(artifact, Mapping) else INVALID_ARTIFACT_TYPE_V1,
        "valid": bool(validation["valid"]),
        "blocked": bool(validation["blocked"]),
        "metadata_only": bool(isinstance(artifact, Mapping) and artifact.get("metadata_only") is True),
        "internal_only": bool(isinstance(artifact, Mapping) and artifact.get("internal_only") is True),
        "synthetic_only": bool(isinstance(artifact, Mapping) and artifact.get("synthetic_only") is True),
        "helper_only": bool(isinstance(artifact, Mapping) and artifact.get("helper_only") is True),
        "all_authority_flags_false": bool(validation["safety_booleans_valid"]),
        "gate_statuses_valid": bool(validation["gate_statuses_valid"]),
        "gate_status_count": len(gates) if isinstance(gates, Mapping) else 0,
        "blocked_reasons": _safe_error_labels(_as_list(artifact.get("blocked_reasons"))) if isinstance(artifact, Mapping) else ["artifact_not_mapping"],
        "validation_error_labels": _safe_error_labels(validation["errors"]),
        "visible_risk_count": len(_as_list(artifact.get("visible_risks"))) if isinstance(artifact, Mapping) else 0,
        "summary_labels": _as_list(artifact.get("summary_labels")) if isinstance(artifact, Mapping) else [],
        "next_lane": str(artifact.get("next_lane", NEXT_LANE_V1)) if isinstance(artifact, Mapping) else NEXT_LANE_V1,
    }


def render_controlled_answer_composition_dry_run_artifact_markdown_v1(artifact: Mapping[str, Any]) -> str:
    """Render safe Markdown for one controlled dry-run artifact."""

    validation = validate_controlled_answer_composition_dry_run_artifact_v1(artifact)
    summary = summarize_controlled_answer_composition_dry_run_artifact_v1(artifact)
    lines = [
        "# Controlled Answer Composition Dry Run Artifact V1",
        "",
        f"- artifact_type: `{summary['artifact_type']}`",
        f"- valid: `{summary['valid']}`",
        f"- blocked: `{summary['blocked']}`",
        f"- metadata_only: `{summary['metadata_only']}`",
        f"- internal_only: `{summary['internal_only']}`",
        f"- synthetic_only: `{summary['synthetic_only']}`",
        f"- helper_only: `{summary['helper_only']}`",
        f"- all_authority_flags_false: `{summary['all_authority_flags_false']}`",
        f"- gate_statuses_valid: `{summary['gate_statuses_valid']}`",
        f"- gate_status_count: `{summary['gate_status_count']}`",
        "",
        "## Gate Statuses",
    ]
    gates = artifact.get("gate_statuses") if isinstance(artifact, Mapping) else None
    if isinstance(gates, Mapping):
        for key in sorted(gates):
            lines.append(f"- `{key}`: `{gates[key]}`")
    else:
        lines.append("- `gate_statuses_not_mapping`")

    lines.extend(["", "## Blocked Reasons"])
    blocked_reasons = summary["blocked_reasons"] or _safe_error_labels(validation["errors"])
    if blocked_reasons:
        for reason in blocked_reasons:
            lines.append(f"- `{reason}`")
    else:
        lines.append("- `none`")

    lines.extend(["", "## Summary Labels"])
    for label in summary["summary_labels"]:
        lines.append(f"- `{label}`")

    lines.extend(["", "## Validation Labels"])
    for label in _as_list(artifact.get("validation_labels")) if isinstance(artifact, Mapping) else []:
        lines.append(f"- `{label}`")

    lines.extend(
        [
            "",
            "## Safety Confirmation",
            "- `helper_metadata_not_answer_text`",
            "- `dry_run_artifact_not_final_answer`",
            "- `validation_pass_not_answer_authority`",
            "- `validation_pass_not_composition_authority`",
            "- `runtime_wiring_requires_separate_approval`",
            f"- next_lane: `{summary['next_lane']}`",
        ]
    )
    return "\n".join(lines) + "\n"


def to_controlled_answer_composition_dry_run_artifact_json_safe_v1(artifact: Mapping[str, Any]) -> dict[str, Any]:
    """Return a JSON-safe deep copy of one controlled dry-run artifact."""

    safe = _json_safe(artifact)
    if not isinstance(safe, dict):
        return {"artifact_type": INVALID_ARTIFACT_TYPE_V1, "blocked": True, "errors": ["artifact_not_mapping"]}
    for flag in (*FALSE_AUTHORITY_FIELDS_V1, *ADDITIONAL_FALSE_FIELDS_V1):
        if flag in safe:
            safe[flag] = False if safe[flag] is False else safe[flag]
    return safe
