"""WESLR answer authority boundary helpers V1.

Deterministic, import-safe, side-effect-free, in-memory metadata helpers for
answer-authority boundary artifacts. These helpers do not compose answers,
generate final answers, execute prompts, call providers/search/advisors, wire
runtime behavior, persist state, write files, or grant answer authority.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

SCHEMA_VERSION_V1 = "answer_authority_boundary_artifact_schema_v1"
ARTIFACT_TYPE_V1 = "answer_authority_boundary_artifact_v1"

ANSWER_AUTHORITY_APPROVED_SOURCE_METADATA_TYPES_V1 = (
    "internal_turing_scenario_corpus_metadata",
    "internal_turing_multi_turn_protocol_metadata",
    "ranked_response_shadow_report_run_metadata",
    "ranked_native_interop_report_run_metadata",
    "behavior_evaluation_report_metadata",
    "internal_evaluation_corpus_metadata",
    "cognition_target_model_design_metadata",
    "ranked_state_grounded_response_formation_design_metadata",
)

ANSWER_AUTHORITY_ALLOWED_INFERENCE_LABELS_V1 = (
    "scenario_coverage_visible",
    "multi_turn_dimension_coverage_visible",
    "failure_taxonomy_visible",
    "governance_boundary_visible",
    "evidence_boundary_visible",
    "provenance_boundary_visible",
    "memory_boundary_visible",
    "uncertainty_honesty_expected",
    "non_cannedness_expected",
    "final_answer_authority_risk_visible",
    "runtime_authority_risk_visible",
    "occ_openclaw_identity_boundary_visible",
    "readiness_gap_visible",
)

ANSWER_AUTHORITY_FORBIDDEN_INFERENCE_LABELS_V1 = (
    "final_response_text_authorized",
    "live_answer_composition_authorized",
    "runtime_route_activation_authorized",
    "chat_responder_edit_authorized",
    "prompt_execution_authorized",
    "live_dialogue_authorized",
    "model_search_advisor_calls_authorized",
    "dot_weslr_write_authorized",
    "feature_flag_authorized",
    "scoring_authorized",
    "judge_authority_granted",
    "benchmark_claim_authorized",
    "official_claim_authorized",
    "deployment_readiness_authorized",
    "product_readiness_authorized",
    "final_answer_authorized",
)

ANSWER_AUTHORITY_REQUIRED_BOUNDARY_LABELS_V1 = (
    "metadata_evidence_useful_for_review",
    "metadata_evidence_not_answer_authority",
    "candidate_metadata_not_answer_text",
    "evaluation_metadata_not_response_authority",
    "answer_authority_not_granted",
    "runtime_authority_not_granted",
    "final_answer_generation_not_authorized",
    "prompt_execution_not_authorized",
    "governance_review_required",
    "evidence_sufficiency_not_established",
    "official_claim_not_allowed",
    "runtime_wiring_requires_separate_approval",
    "final_answer_composition_requires_separate_design",
)

ANSWER_AUTHORITY_FORBIDDEN_LABEL_DRIFT_V1 = (
    "ready_for_runtime",
    "passed_turing_test",
    "officially_intelligent",
    "certified",
    "human_level",
    "conscious",
    "sentient",
    "production_ready",
    "approved_for_live_answers",
    "final_answer_authorized",
    "answer_authority_granted",
    "runtime_authority_granted",
)

ANSWER_AUTHORITY_MINOR_RISKS_V1 = (
    "validator_phrase_key_limitation",
    "renderer_next_lane_wording_drift",
    "Turing-name overclaim risk",
    "future label non-scoring discipline",
    "metadata-overread risk",
    "boundary-label drift risk",
    "helper/report-as-judge risk",
    "helper/report-as-score risk",
)

ANSWER_AUTHORITY_READINESS_LABELS_V1 = (
    "answer_authority_boundary_helpers_implemented",
    "metadata_evidence_not_answer_authority",
    "answer_authority_not_granted",
    "runtime_authority_not_granted",
    "final_answer_generation_not_authorized",
    "prompt_execution_not_authorized",
    "internal_only_non_official",
    "qualitative_first",
    "official_evaluation_not_claimed",
    "further_cognition_evidence_required",
    "minor_followup_carried_forward",
    "voice_downstream_not_current_priority",
)

_REQUIRED_FIELDS = (
    "artifact_type",
    "source_metadata_types",
    "covered_dimensions",
    "covered_failure_modes",
    "authority_boundary_labels",
    "allowed_inferences",
    "forbidden_inferences",
    "governance_required",
    "evidence_sufficiency_status",
    "minor_risks",
    "readiness_labels",
    "schema_version",
    "metadata_only",
    "internal_only",
    "answer_authority_granted",
    "runtime_authority_granted",
    "final_answer_generated",
    "official_claim_allowed",
    "prompt_execution_allowed",
    "raw_content_allowed",
    "answer_composition_authorized",
    "judge_authority_granted",
    "scoring_authorized",
    "model_call_made",
    "search_call_made",
    "advisor_call_made",
    "dot_weslr_write_performed",
    "feature_flag_enabled",
)

_FALSE_AUTHORITY_FLAGS = (
    "answer_authority_granted",
    "runtime_authority_granted",
    "final_answer_generated",
    "official_claim_allowed",
    "prompt_execution_allowed",
    "raw_content_allowed",
    "answer_composition_authorized",
    "judge_authority_granted",
    "scoring_authorized",
    "model_call_made",
    "search_call_made",
    "advisor_call_made",
    "dot_weslr_write_performed",
    "feature_flag_enabled",
)

_TRUE_METADATA_FLAGS = ("metadata_only", "internal_only")

_UNSAFE_KEY_FRAGMENTS = (
    "raw_prompt",
    "raw_response",
    "raw_response_text",
    "raw_prompt_text",
    "final_answer_text",
    "final_answer_prose",
    "private_content",
    "hidden_prompt",
    "answer_key",
    "provider_output",
    "model_output",
    "official_score",
    "runtime_output",
)

_ALLOWED_KEYS_WITH_RISK_WORDS = set(_REQUIRED_FIELDS) | {
    "final_answer_authority_risk_visible",
    "runtime_authority_risk_visible",
    "final_answer_authority_not_granted",
    "final_answer_generation_not_authorized",
    "final_answer_composition_requires_separate_design",
    "final_answer_authorized",
    "runtime_authority_not_granted",
    "answer_authority_not_granted",
    "raw_content_allowed",
}

_TEXT_MARKERS = {
    "raw_content_detected": (
        "raw prompt:",
        "raw_prompt:",
        "raw response:",
        "raw_response:",
        "raw response text",
        "raw prompt text",
    ),
    "final_answer_detected": ("final answer:", "final_answer_text", "final answer prose"),
    "answer_authority_detected": (
        "answer authority granted",
        "answer_authority_granted=true",
        "approved for live answers",
    ),
    "runtime_authority_detected": (
        "runtime authority granted",
        "runtime_authority_granted=true",
        "runtime output treated as authority",
    ),
    "prompt_execution_detected": ("execute prompt", "prompt execution", "run this prompt"),
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
        "judge_authority_granted=true",
        "scoring_authorized=true",
    ),
    "private_content_detected": ("private content:", "private user content", "protected private material"),
    "hidden_prompt_detected": ("hidden prompt:", "system prompt hidden"),
    "answer_key_detected": ("answer key:", "correct answer:"),
    "provider_output_detected": ("provider output:", "model output:", "llm output:"),
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
    "live_dialogue_detected": ("live dialogue", "create live dialogue"),
    "provider_call_detected": (
        "model_call_made=true",
        "search_call_made=true",
        "advisor_call_made=true",
        "call model",
        "call search",
        "call advisor",
    ),
    "dot_weslr_write_detected": (".weslr write", "write .weslr", "dot_weslr_write_performed=true"),
    "feature_flag_detected": ("feature_flag_enabled=true", "enable feature flag"),
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
        return {str(k): _json_safe(v) for k, v in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(v) for v in value]
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


def _norm(value: Any) -> str:
    return str(value).strip().lower().replace(" ", "_").replace("-", "_")


def _text(value: Any) -> str:
    if isinstance(value, str):
        return value.lower()
    return ""


def _append_unique(target: list[str], label: str) -> None:
    if label not in target:
        target.append(label)


def build_answer_authority_boundary_artifact_v1(
    *,
    source_metadata_types: list[str] | tuple[str, ...] | None = None,
    covered_dimensions: list[str] | tuple[str, ...] | None = None,
    covered_failure_modes: list[str] | tuple[str, ...] | None = None,
    allowed_inferences: list[str] | tuple[str, ...] | None = None,
    forbidden_inferences: list[str] | tuple[str, ...] | None = None,
    authority_boundary_labels: list[str] | tuple[str, ...] | None = None,
    governance_required: bool = True,
    evidence_sufficiency_status: str = "evidence_sufficiency_not_established",
    minor_risks: list[str] | tuple[str, ...] | None = None,
    readiness_labels: list[str] | tuple[str, ...] | None = None,
) -> dict[str, Any]:
    """Build one safe metadata-only answer-authority boundary artifact."""

    return {
        "artifact_type": ARTIFACT_TYPE_V1,
        "source_metadata_types": _as_list(source_metadata_types),
        "covered_dimensions": _as_list(covered_dimensions),
        "covered_failure_modes": _as_list(covered_failure_modes),
        "authority_boundary_labels": _as_list(authority_boundary_labels) or list(ANSWER_AUTHORITY_REQUIRED_BOUNDARY_LABELS_V1),
        "allowed_inferences": _as_list(allowed_inferences),
        "forbidden_inferences": _as_list(forbidden_inferences) or list(ANSWER_AUTHORITY_FORBIDDEN_INFERENCE_LABELS_V1),
        "governance_required": bool(governance_required),
        "evidence_sufficiency_status": str(evidence_sufficiency_status),
        "minor_risks": _as_list(minor_risks) or list(ANSWER_AUTHORITY_MINOR_RISKS_V1),
        "readiness_labels": _as_list(readiness_labels) or list(ANSWER_AUTHORITY_READINESS_LABELS_V1),
        "schema_version": SCHEMA_VERSION_V1,
        "metadata_only": True,
        "internal_only": True,
        "answer_authority_granted": False,
        "runtime_authority_granted": False,
        "final_answer_generated": False,
        "official_claim_allowed": False,
        "prompt_execution_allowed": False,
        "raw_content_allowed": False,
        "answer_composition_authorized": False,
        "judge_authority_granted": False,
        "scoring_authorized": False,
        "model_call_made": False,
        "search_call_made": False,
        "advisor_call_made": False,
        "dot_weslr_write_performed": False,
        "feature_flag_enabled": False,
    }


def validate_answer_authority_boundary_artifact_v1(artifact: dict) -> dict[str, Any]:
    """Validate one answer-authority boundary artifact without side effects."""

    errors: list[str] = []
    warnings: list[str] = []
    result: dict[str, Any] = {
        "valid": False,
        "blocked": True,
        "errors": errors,
        "warnings": warnings,
        "artifact_type": None,
        "safety_booleans_valid": False,
        "unknown_source_metadata_types": [],
        "unknown_allowed_inferences": [],
        "missing_forbidden_inferences": [],
        "forbidden_as_allowed": [],
        "missing_boundary_labels": [],
        "raw_content_detected": False,
        "final_answer_detected": False,
        "answer_authority_detected": False,
        "runtime_authority_detected": False,
        "prompt_execution_detected": False,
        "official_claim_detected": False,
        "judge_or_score_detected": False,
    }

    if not isinstance(artifact, Mapping):
        errors.append("artifact_not_mapping")
        return result

    result["artifact_type"] = artifact.get("artifact_type")
    if artifact.get("artifact_type") != ARTIFACT_TYPE_V1:
        errors.append("artifact_type_invalid")

    for field in _REQUIRED_FIELDS:
        if field not in artifact:
            errors.append(f"missing_required_field:{field}")

    approved_sources = set(ANSWER_AUTHORITY_APPROVED_SOURCE_METADATA_TYPES_V1)
    unknown_sources = [str(item) for item in _as_list(artifact.get("source_metadata_types")) if item not in approved_sources]
    result["unknown_source_metadata_types"] = unknown_sources
    if unknown_sources:
        errors.append("unknown_source_metadata_types")

    allowed_labels = set(ANSWER_AUTHORITY_ALLOWED_INFERENCE_LABELS_V1)
    artifact_allowed = [str(item) for item in _as_list(artifact.get("allowed_inferences"))]
    unknown_allowed = [item for item in artifact_allowed if item not in allowed_labels]
    result["unknown_allowed_inferences"] = unknown_allowed
    if unknown_allowed:
        errors.append("unknown_allowed_inferences")

    required_forbidden = set(ANSWER_AUTHORITY_FORBIDDEN_INFERENCE_LABELS_V1)
    artifact_forbidden = set(str(item) for item in _as_list(artifact.get("forbidden_inferences")))
    missing_forbidden = sorted(required_forbidden - artifact_forbidden)
    result["missing_forbidden_inferences"] = missing_forbidden
    if missing_forbidden:
        errors.append("missing_forbidden_inferences")

    forbidden_as_allowed = sorted(required_forbidden.intersection(artifact_allowed))
    result["forbidden_as_allowed"] = forbidden_as_allowed
    if forbidden_as_allowed:
        errors.append("forbidden_as_allowed")

    required_boundary = set(ANSWER_AUTHORITY_REQUIRED_BOUNDARY_LABELS_V1)
    artifact_boundary = set(str(item) for item in _as_list(artifact.get("authority_boundary_labels")))
    missing_boundary = sorted(required_boundary - artifact_boundary)
    result["missing_boundary_labels"] = missing_boundary
    if missing_boundary:
        errors.append("missing_boundary_labels")

    safety_valid = True
    for flag in _FALSE_AUTHORITY_FLAGS:
        if artifact.get(flag) is not False:
            safety_valid = False
            errors.append(f"unsafe_true_or_missing_flag:{flag}")
            if flag == "answer_authority_granted":
                result["answer_authority_detected"] = True
            elif flag == "runtime_authority_granted":
                result["runtime_authority_detected"] = True
            elif flag == "final_answer_generated":
                result["final_answer_detected"] = True
            elif flag == "official_claim_allowed":
                result["official_claim_detected"] = True
            elif flag == "prompt_execution_allowed":
                result["prompt_execution_detected"] = True
            elif flag in {"judge_authority_granted", "scoring_authorized"}:
                result["judge_or_score_detected"] = True
            elif flag == "raw_content_allowed":
                result["raw_content_detected"] = True
    for flag in _TRUE_METADATA_FLAGS:
        if artifact.get(flag) is not True:
            safety_valid = False
            errors.append(f"metadata_flag_not_true:{flag}")
    result["safety_booleans_valid"] = safety_valid

    drift_fields = (
        "allowed_inferences",
        "authority_boundary_labels",
        "readiness_labels",
        "covered_dimensions",
        "covered_failure_modes",
        "evidence_sufficiency_status",
    )
    drift_values = []
    for field in drift_fields:
        drift_values.extend(_as_list(artifact.get(field)))
    for value in drift_values:
        value_n = _norm(value)
        for drift in ANSWER_AUTHORITY_FORBIDDEN_LABEL_DRIFT_V1:
            if value_n == _norm(drift):
                errors.append(f"forbidden_label_drift:{drift}")
                if drift == "answer_authority_granted":
                    result["answer_authority_detected"] = True
                if drift == "runtime_authority_granted" or drift == "ready_for_runtime":
                    result["runtime_authority_detected"] = True
                if drift in {"passed_turing_test", "officially_intelligent", "certified", "human_level", "production_ready"}:
                    result["official_claim_detected"] = True

    for path, value in _walk(artifact):
        key = path.split(".")[-1].split("[")[0]
        key_n = _norm(key)
        if key_n not in _ALLOWED_KEYS_WITH_RISK_WORDS:
            for fragment in _UNSAFE_KEY_FRAGMENTS:
                if fragment in key_n:
                    errors.append(f"unsafe_key:{key}")
                    if fragment in {"raw_prompt", "raw_response", "raw_response_text", "raw_prompt_text"}:
                        result["raw_content_detected"] = True
                    elif fragment.startswith("final_answer"):
                        result["final_answer_detected"] = True
                    elif fragment in {"official_score"}:
                        result["judge_or_score_detected"] = True
        text = _text(value)
        if not text:
            continue
        # Do not classify denied forbidden inference labels or carried minor-risk labels as claims.
        if key in {"forbidden_inferences", "minor_risks"}:
            continue
        for output_key, markers in _TEXT_MARKERS.items():
            for marker in markers:
                if marker in text:
                    if output_key in result:
                        result[output_key] = True
                    errors.append(output_key)
                    break

    result["valid"] = not errors
    result["blocked"] = bool(errors)
    return result


def _all_authority_flags_false(artifact: Mapping[str, Any]) -> bool:
    return all(artifact.get(flag) is False for flag in _FALSE_AUTHORITY_FLAGS)


def summarize_answer_authority_boundary_artifact_v1(artifact: dict) -> dict[str, Any]:
    """Return a safe metadata summary for one boundary artifact."""

    validation = validate_answer_authority_boundary_artifact_v1(artifact)
    return {
        "artifact_type": artifact.get("artifact_type") if isinstance(artifact, Mapping) else None,
        "valid": validation["valid"],
        "blocked": validation["blocked"],
        "source_metadata_type_count": len(_as_list(artifact.get("source_metadata_types"))) if isinstance(artifact, Mapping) else 0,
        "covered_dimension_count": len(_as_list(artifact.get("covered_dimensions"))) if isinstance(artifact, Mapping) else 0,
        "covered_failure_mode_count": len(_as_list(artifact.get("covered_failure_modes"))) if isinstance(artifact, Mapping) else 0,
        "allowed_inference_count": len(_as_list(artifact.get("allowed_inferences"))) if isinstance(artifact, Mapping) else 0,
        "forbidden_inference_count": len(_as_list(artifact.get("forbidden_inferences"))) if isinstance(artifact, Mapping) else 0,
        "authority_boundary_labels": _as_list(artifact.get("authority_boundary_labels")) if isinstance(artifact, Mapping) else [],
        "governance_required": bool(artifact.get("governance_required")) if isinstance(artifact, Mapping) else False,
        "evidence_sufficiency_status": artifact.get("evidence_sufficiency_status") if isinstance(artifact, Mapping) else None,
        "all_authority_flags_false": _all_authority_flags_false(artifact) if isinstance(artifact, Mapping) else False,
        "readiness_labels": _as_list(artifact.get("readiness_labels")) if isinstance(artifact, Mapping) else [],
        "minor_risks": _as_list(artifact.get("minor_risks")) if isinstance(artifact, Mapping) else [],
    }


def render_answer_authority_boundary_artifact_markdown_v1(artifact: dict) -> str:
    """Render safe internal Markdown for a boundary artifact."""

    validation = validate_answer_authority_boundary_artifact_v1(artifact)
    if not validation["valid"]:
        safe_reasons = [str(item).split(":", 1)[0] for item in validation["errors"]]
        unique_reasons: list[str] = []
        for reason in safe_reasons:
            _append_unique(unique_reasons, reason)
        return "\n".join(
            [
                "# WESLR Answer Authority Boundary Artifact V1",
                "",
                "## Artifact status",
                "- status: `blocked`",
                "- safe_rendering: `blocked_invalid_artifact`",
                "",
                "## Validation status",
                "- valid: `False`",
                "- blocked: `True`",
                f"- reason_label_count: `{len(unique_reasons)}`",
                "- reason_labels:",
                *[f"  - `{reason}`" for reason in unique_reasons],
                "",
                "## Safety confirmation",
                "- offending content not rendered",
                "- metadata evidence is not answer authority",
                "",
                "## Next lane recommendation",
                "- `REVIEW_INVALID_BOUNDARY_METADATA_ONLY_BEFORE_ANY_AUTHORITY_OR_RUNTIME_LANE`",
                "",
            ]
        )

    summary = summarize_answer_authority_boundary_artifact_v1(artifact)
    boundary_lines = [f"  - `{label}`" for label in summary["authority_boundary_labels"]]
    risk_lines = [f"  - `{risk}`" for risk in summary["minor_risks"]]
    return "\n".join(
        [
            "# WESLR Answer Authority Boundary Artifact V1",
            "",
            "## Artifact status",
            "- artifact_type: `answer_authority_boundary_artifact_v1`",
            "- metadata_only: `True`",
            "- internal_only: `True`",
            "",
            "## Validation status",
            "- valid: `True`",
            "- blocked: `False`",
            "",
            "## Coverage counts",
            f"- source_metadata_type_count: `{summary['source_metadata_type_count']}`",
            f"- covered_dimension_count: `{summary['covered_dimension_count']}`",
            f"- covered_failure_mode_count: `{summary['covered_failure_mode_count']}`",
            "",
            "## Authority boundary labels",
            *boundary_lines,
            "",
            "## Inference counts",
            f"- allowed_inference_count: `{summary['allowed_inference_count']}`",
            f"- forbidden_inference_count: `{summary['forbidden_inference_count']}`",
            "",
            "## Governance and evidence",
            f"- governance_required: `{summary['governance_required']}`",
            f"- evidence_sufficiency_status: `{summary['evidence_sufficiency_status']}`",
            "",
            "## False authority flag summary",
            f"- all_authority_flags_false: `{summary['all_authority_flags_false']}`",
            "- answer authority: `not_granted`",
            "- runtime authority: `not_granted`",
            "- final answer generation: `not_authorized`",
            "- prompt execution: `not_authorized`",
            "- answer composition: `not_authorized`",
            "- judge/scoring authority: `not_authorized`",
            "",
            "## Minor risks",
            *risk_lines,
            "",
            "## Safety confirmation",
            "- metadata evidence may inform review",
            "- metadata evidence is not answer authority",
            "- no raw prompts, raw responses, final answer prose, provider output, official scores, or private content rendered",
            "",
            "## Next lane recommendation",
            "- `REVIEW_HELPER_ONLY_METADATA_BOUNDARY_BEFORE_SEPARATE_DESIGN_LANE`",
            "",
        ]
    )


def to_answer_authority_boundary_artifact_json_safe_v1(artifact: dict) -> dict[str, Any]:
    """Return a JSON-safe metadata copy or explicit invalid wrapper."""

    validation = validate_answer_authority_boundary_artifact_v1(artifact)
    if not validation["valid"]:
        reason_labels: list[str] = []
        for error in validation["errors"]:
            _append_unique(reason_labels, str(error).split(":", 1)[0])
        return {
            "artifact_type": ARTIFACT_TYPE_V1,
            "valid": False,
            "blocked": True,
            "invalid_wrapper": True,
            "reason_labels": reason_labels,
            "metadata_only": True,
            "internal_only": True,
        }
    return _json_safe(artifact)
