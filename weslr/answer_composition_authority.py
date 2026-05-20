"""WESLR answer composition authority helpers V1.

Deterministic, import-safe, side-effect-free, in-memory metadata helpers for
answer-composition authority review artifacts. These helpers do not compose
answers, generate final answers, execute prompts, create live dialogue, call
providers/search/advisors, wire runtime behavior, persist state, write files,
create judges or scores, make official claims, or grant answer authority.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

SCHEMA_VERSION_V1 = "answer_composition_authority_artifact_schema_v1"
ARTIFACT_TYPE_V1 = "answer_composition_authority_artifact_v1"
INVALID_ARTIFACT_TYPE_V1 = "answer_composition_authority_artifact_v1_invalid"

ANSWER_COMPOSITION_AUTHORITY_APPROVED_SOURCE_METADATA_TYPES_V1 = (
    "answer_authority_boundary_artifact_metadata",
    "answer_composition_authority_boundary_design_metadata",
    "internal_turing_scenario_corpus_metadata",
    "internal_turing_multi_turn_protocol_metadata",
    "ranked_response_shadow_report_run_metadata",
    "ranked_native_interop_report_run_metadata",
    "behavior_evaluation_report_metadata",
    "internal_evaluation_corpus_metadata",
    "cognition_target_model_design_metadata",
    "ranked_state_grounded_response_formation_design_metadata",
)

ANSWER_COMPOSITION_AUTHORITY_ALLOWED_REVIEW_LABELS_V1 = (
    "metadata_evidence_useful_for_review",
    "metadata_evidence_not_answer_text",
    "metadata_evidence_not_answer_composition_authority",
    "metadata_evidence_not_answer_authority",
    "composition_gate_status_visible",
    "evidence_gate_visible",
    "provenance_gate_visible",
    "governance_gate_visible",
    "memory_gate_visible",
    "domain_gate_visible",
    "uncertainty_gate_visible",
    "raw_content_gate_visible",
    "provider_gate_visible",
    "persistence_gate_visible",
    "official_claim_gate_visible",
    "occ_openclaw_identity_boundary_visible",
    "denied_paths_visible",
    "visible_risks_carried_forward",
)

ANSWER_COMPOSITION_AUTHORITY_FORBIDDEN_INFERENCE_LABELS_V1 = (
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
    "answer_authority_granted",
    "runtime_authority_granted",
    "answer_composition_authorized",
)

ANSWER_COMPOSITION_AUTHORITY_REQUIRED_NO_AUTHORITY_LABELS_V1 = (
    "metadata_evidence_useful_for_review",
    "metadata_evidence_not_answer_text",
    "metadata_evidence_not_answer_composition_authority",
    "metadata_evidence_not_answer_authority",
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
    "official_claim_not_allowed",
    "runtime_wiring_requires_separate_approval",
    "final_answer_composition_requires_separate_design",
    "occ_openclaw_not_weslr",
)

ANSWER_COMPOSITION_AUTHORITY_REQUIRED_GATE_STATUSES_V1 = {
    "evidence_gate": "evidence_sufficiency_not_established",
    "provenance_gate": "provenance_sufficiency_not_established",
    "governance_gate": "governance_review_required",
    "memory_gate": "memory_boundary_review_required",
    "domain_gate": "domain_constraints_review_required",
    "uncertainty_gate": "uncertainty_honesty_required",
    "final_answer_gate": "final_answer_generation_not_authorized",
    "runtime_gate": "runtime_wiring_requires_separate_approval",
    "prompt_execution_gate": "prompt_execution_not_authorized",
    "provider_gate": "provider_calls_not_authorized",
    "persistence_gate": "dot_weslr_writes_not_authorized",
    "official_claim_gate": "official_claim_not_allowed",
    "identity_gate": "occ_openclaw_not_weslr",
}

ANSWER_COMPOSITION_AUTHORITY_FORBIDDEN_LABEL_DRIFT_V1 = (
    "ready_for_runtime",
    "safe_to_wire_runtime",
    "safe_to_replace_live_output",
    "passed_turing_test",
    "officially_intelligent",
    "certified",
    "human_level",
    "conscious",
    "sentient",
    "production_ready",
    "product_ready",
    "approved_for_live_answers",
    "final_answer_authorized",
    "answer_authority_granted",
    "runtime_authority_granted",
    "answer_composition_authorized",
)

ANSWER_COMPOSITION_AUTHORITY_MINOR_RISKS_V1 = (
    "metadata-overread risk",
    "report-as-judge/score risk",
    "renderer wording drift",
    "artifact-as-authority risk",
    "OCC/WESLR identity confusion risk",
    "validation-pass-as-authority risk",
    "final-answer-prose leak risk",
)

ANSWER_COMPOSITION_AUTHORITY_READINESS_LABELS_V1 = (
    "answer_composition_authority_helpers_implemented",
    "helper_only",
    "metadata_only",
    "qualitative_only",
    "internal_only_non_official",
    "answer_composition_not_authorized",
    "answer_authority_not_granted",
    "runtime_authority_not_granted",
    "final_answer_generation_not_authorized",
    "prompt_execution_not_authorized",
    "minor_followup_carried_forward",
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
    "artifact_type",
    "schema_version",
    "metadata_only",
    "internal_only",
    "source_metadata_types",
    "composition_review_dimensions",
    "composition_gate_statuses",
    "allowed_review_labels",
    "forbidden_inference_labels",
    "required_no_authority_labels",
    "minor_risks",
    "readiness_labels",
    *_FALSE_AUTHORITY_FLAGS,
)

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
    "runtime_output",
)

_ALLOWED_KEYS_WITH_RISK_WORDS = set(_REQUIRED_FIELDS) | {
    "composition_gate_statuses",
    "final_answer_gate",
    "runtime_gate",
    "prompt_execution_gate",
    "provider_gate",
    "official_claim_gate",
    "final_answer_generation_not_authorized",
    "final_answer_composition_requires_separate_design",
    "runtime_wiring_requires_separate_approval",
    "runtime_authority_not_granted",
    "answer_authority_not_granted",
    "answer_composition_not_authorized",
    "metadata_evidence_not_answer_authority",
    "metadata_evidence_not_answer_composition_authority",
    "metadata_evidence_not_answer_text",
    "raw_content_allowed",
    "final-answer-prose leak risk",
}

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
        "judge_authority_granted=true",
        "scoring_authorized=true",
    ),
    "prompt_execution_detected": ("execute prompt", "prompt execution", "run this prompt"),
    "live_dialogue_detected": ("live dialogue", "create live dialogue"),
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
    "feature_flag_detected": ("feature_flag_enabled=true", "enable feature flag"),
    "answer_authority_detected": (
        "answer authority granted",
        "answer_authority_granted=true",
        "approved for live answers",
    ),
    "composition_authority_detected": (
        "answer composition authorized",
        "answer_composition_authorized=true",
        "live answer composition authorized",
    ),
    "runtime_authority_detected": (
        "runtime authority granted",
        "runtime_authority_granted=true",
        "runtime output treated as authority",
    ),
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


def build_answer_composition_authority_artifact_v1(
    *,
    source_metadata_types: list[str] | tuple[str, ...] | None = None,
    composition_review_dimensions: list[str] | tuple[str, ...] | None = None,
    composition_gate_statuses: Mapping[str, str] | None = None,
    allowed_review_labels: list[str] | tuple[str, ...] | None = None,
    forbidden_inference_labels: list[str] | tuple[str, ...] | None = None,
    required_no_authority_labels: list[str] | tuple[str, ...] | None = None,
    minor_risks: list[str] | tuple[str, ...] | None = None,
    readiness_labels: list[str] | tuple[str, ...] | None = None,
) -> dict[str, Any]:
    """Build one safe metadata-only answer-composition authority artifact."""

    gates = dict(ANSWER_COMPOSITION_AUTHORITY_REQUIRED_GATE_STATUSES_V1)
    if composition_gate_statuses:
        gates.update({str(key): str(value) for key, value in composition_gate_statuses.items()})

    return {
        "artifact_type": ARTIFACT_TYPE_V1,
        "schema_version": SCHEMA_VERSION_V1,
        "metadata_only": True,
        "internal_only": True,
        "source_metadata_types": _as_list(source_metadata_types),
        "composition_review_dimensions": _as_list(composition_review_dimensions),
        "composition_gate_statuses": gates,
        "allowed_review_labels": _as_list(allowed_review_labels) or list(ANSWER_COMPOSITION_AUTHORITY_ALLOWED_REVIEW_LABELS_V1),
        "forbidden_inference_labels": _as_list(forbidden_inference_labels) or list(ANSWER_COMPOSITION_AUTHORITY_FORBIDDEN_INFERENCE_LABELS_V1),
        "required_no_authority_labels": _as_list(required_no_authority_labels) or list(ANSWER_COMPOSITION_AUTHORITY_REQUIRED_NO_AUTHORITY_LABELS_V1),
        "minor_risks": _as_list(minor_risks) or list(ANSWER_COMPOSITION_AUTHORITY_MINOR_RISKS_V1),
        "readiness_labels": _as_list(readiness_labels) or list(ANSWER_COMPOSITION_AUTHORITY_READINESS_LABELS_V1),
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


def validate_answer_composition_authority_artifact_v1(artifact: dict) -> dict[str, Any]:
    """Validate one answer-composition authority artifact without side effects."""

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
        "unknown_source_metadata_types": [],
        "unknown_allowed_review_labels": [],
        "missing_forbidden_inference_labels": [],
        "forbidden_as_allowed": [],
        "missing_no_authority_labels": [],
        "missing_gate_statuses": [],
        "unsafe_gate_statuses": [],
        "raw_content_detected": False,
        "private_content_detected": False,
        "hidden_prompt_detected": False,
        "answer_key_detected": False,
        "provider_output_detected": False,
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
        "consciousness_claim_detected": False,
        "identity_confusion_detected": False,
    }

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

    for flag in _TRUE_METADATA_FLAGS:
        if artifact.get(flag) is not True:
            errors.append(f"metadata_flag_not_true:{flag}")

    safety_ok = True
    for flag in _FALSE_AUTHORITY_FLAGS:
        if flag not in artifact:
            safety_ok = False
            continue
        if artifact.get(flag) is not False:
            safety_ok = False
            errors.append(f"authority_flag_not_false:{flag}")
    result["safety_booleans_valid"] = safety_ok

    approved_sources = set(ANSWER_COMPOSITION_AUTHORITY_APPROVED_SOURCE_METADATA_TYPES_V1)
    unknown_sources = [str(item) for item in _as_list(artifact.get("source_metadata_types")) if item not in approved_sources]
    result["unknown_source_metadata_types"] = unknown_sources
    if unknown_sources:
        errors.append("unknown_source_metadata_types")

    allowed_review = set(ANSWER_COMPOSITION_AUTHORITY_ALLOWED_REVIEW_LABELS_V1)
    artifact_allowed = [str(item) for item in _as_list(artifact.get("allowed_review_labels"))]
    unknown_allowed = [item for item in artifact_allowed if item not in allowed_review]
    result["unknown_allowed_review_labels"] = unknown_allowed
    if unknown_allowed:
        errors.append("unknown_allowed_review_labels")

    forbidden_set = set(ANSWER_COMPOSITION_AUTHORITY_FORBIDDEN_INFERENCE_LABELS_V1)
    artifact_forbidden = {str(item) for item in _as_list(artifact.get("forbidden_inference_labels"))}
    missing_forbidden = sorted(forbidden_set - artifact_forbidden)
    result["missing_forbidden_inference_labels"] = missing_forbidden
    if missing_forbidden:
        errors.append("missing_forbidden_inference_labels")

    forbidden_as_allowed = sorted(forbidden_set.intersection(artifact_allowed))
    result["forbidden_as_allowed"] = forbidden_as_allowed
    if forbidden_as_allowed:
        errors.append("forbidden_inference_label_used_as_allowed_review_label")

    no_authority_set = set(ANSWER_COMPOSITION_AUTHORITY_REQUIRED_NO_AUTHORITY_LABELS_V1)
    artifact_no_authority = {str(item) for item in _as_list(artifact.get("required_no_authority_labels"))}
    missing_no_authority = sorted(no_authority_set - artifact_no_authority)
    result["missing_no_authority_labels"] = missing_no_authority
    if missing_no_authority:
        errors.append("missing_no_authority_labels")

    gates = artifact.get("composition_gate_statuses")
    if not isinstance(gates, Mapping):
        errors.append("composition_gate_statuses_not_mapping")
    else:
        missing_gates: list[str] = []
        unsafe_gates: list[str] = []
        for gate, required_status in ANSWER_COMPOSITION_AUTHORITY_REQUIRED_GATE_STATUSES_V1.items():
            if gate not in gates:
                missing_gates.append(gate)
            elif gates.get(gate) != required_status:
                unsafe_gates.append(f"{gate}:{gates.get(gate)}")
        result["missing_gate_statuses"] = missing_gates
        result["unsafe_gate_statuses"] = unsafe_gates
        if missing_gates:
            errors.append("missing_gate_statuses")
        if unsafe_gates:
            errors.append("unsafe_gate_statuses")
        result["gate_statuses_valid"] = not missing_gates and not unsafe_gates

    for path, value in _walk(artifact):
        leaf = path.rsplit(".", 1)[-1]
        lower_path = path.lower()
        if leaf not in _ALLOWED_KEYS_WITH_RISK_WORDS:
            for fragment in _UNSAFE_KEY_FRAGMENTS:
                if fragment in lower_path:
                    errors.append(f"unsafe_key_detected:{path}")
                    break
        text_value = _text(value)
        if not text_value:
            continue
        for label, markers in _TEXT_MARKERS.items():
            if any(marker in text_value for marker in markers):
                result[label] = True
                errors.append(label)
        normalized = text_value.replace(" ", "_").replace("-", "_")
        in_forbidden_container = path.startswith("forbidden_inference_labels")
        for drift in ANSWER_COMPOSITION_AUTHORITY_FORBIDDEN_LABEL_DRIFT_V1:
            if drift in normalized and not in_forbidden_container:
                errors.append(f"forbidden_label_drift:{drift}")
        for forbidden in ANSWER_COMPOSITION_AUTHORITY_FORBIDDEN_INFERENCE_LABELS_V1:
            if forbidden in normalized and value not in artifact.get("forbidden_inference_labels", []):
                errors.append(f"forbidden_inference_label_outside_forbidden_list:{forbidden}")

    if not artifact.get("minor_risks"):
        warnings.append("minor_risks_not_visible")

    result["valid"] = not errors
    result["blocked"] = bool(errors)
    return result


def summarize_answer_composition_authority_artifact_v1(artifact: dict) -> dict[str, Any]:
    """Summarize one artifact using safe counts, statuses, and labels only."""

    validation = validate_answer_composition_authority_artifact_v1(artifact)
    gates = artifact.get("composition_gate_statuses") if isinstance(artifact, Mapping) else {}
    if not isinstance(gates, Mapping):
        gates = {}
    return {
        "artifact_type": artifact.get("artifact_type") if isinstance(artifact, Mapping) else None,
        "schema_version": artifact.get("schema_version") if isinstance(artifact, Mapping) else None,
        "valid": validation["valid"],
        "blocked": validation["blocked"],
        "metadata_only": bool(artifact.get("metadata_only")) if isinstance(artifact, Mapping) else False,
        "internal_only": bool(artifact.get("internal_only")) if isinstance(artifact, Mapping) else False,
        "source_metadata_type_count": len(_as_list(artifact.get("source_metadata_types"))) if isinstance(artifact, Mapping) else 0,
        "composition_review_dimension_count": len(_as_list(artifact.get("composition_review_dimensions"))) if isinstance(artifact, Mapping) else 0,
        "gate_status_count": len(gates),
        "required_gate_status_count": len(ANSWER_COMPOSITION_AUTHORITY_REQUIRED_GATE_STATUSES_V1),
        "gate_statuses_valid": validation["gate_statuses_valid"],
        "allowed_review_label_count": len(_as_list(artifact.get("allowed_review_labels"))) if isinstance(artifact, Mapping) else 0,
        "forbidden_inference_label_count": len(_as_list(artifact.get("forbidden_inference_labels"))) if isinstance(artifact, Mapping) else 0,
        "required_no_authority_label_count": len(_as_list(artifact.get("required_no_authority_labels"))) if isinstance(artifact, Mapping) else 0,
        "minor_risks": _as_list(artifact.get("minor_risks")) if isinstance(artifact, Mapping) else [],
        "readiness_labels": _as_list(artifact.get("readiness_labels")) if isinstance(artifact, Mapping) else [],
        "all_authority_flags_false": all(artifact.get(flag) is False for flag in _FALSE_AUTHORITY_FLAGS) if isinstance(artifact, Mapping) else False,
        "answer_composition_authorized": bool(artifact.get("answer_composition_authorized")) if isinstance(artifact, Mapping) else False,
        "answer_authority_granted": bool(artifact.get("answer_authority_granted")) if isinstance(artifact, Mapping) else False,
        "runtime_authority_granted": bool(artifact.get("runtime_authority_granted")) if isinstance(artifact, Mapping) else False,
        "final_answer_generated": bool(artifact.get("final_answer_generated")) if isinstance(artifact, Mapping) else False,
        "prompt_execution_allowed": bool(artifact.get("prompt_execution_allowed")) if isinstance(artifact, Mapping) else False,
        "live_dialogue_allowed": bool(artifact.get("live_dialogue_allowed")) if isinstance(artifact, Mapping) else False,
        "official_claim_allowed": bool(artifact.get("official_claim_allowed")) if isinstance(artifact, Mapping) else False,
        "validation_error_count": len(validation["errors"]),
        "validation_warning_count": len(validation["warnings"]),
        "next_lane_recommendation": "REVIEW_ANSWER_COMPOSITION_AUTHORITY_HELPERS_IMPLEMENTATION_V1",
    }


def render_answer_composition_authority_artifact_markdown_v1(artifact: dict) -> str:
    """Render safe internal Markdown for one metadata-only artifact."""

    validation = validate_answer_composition_authority_artifact_v1(artifact)
    if not validation["valid"]:
        reason_labels: list[str] = []
        for error in validation["errors"]:
            _append_unique(reason_labels, str(error).split(":", 1)[0])
        return "\n".join(
            [
                "# WESLR Answer Composition Authority Artifact V1 — Blocked",
                "",
                "## Artifact status",
                "- valid: `False`",
                "- blocked: `True`",
                "- safe_rendering: `blocked_invalid_artifact`",
                "",
                "## Safe reason labels",
                *[f"- `{reason}`" for reason in reason_labels],
                "",
                "## Safety confirmation",
                "- offending content not rendered",
                "- metadata evidence is not answer text",
                "- metadata evidence is not answer composition authority",
                "- metadata evidence is not answer authority",
                "",
                "## Next lane recommendation",
                "- `REVIEW_INVALID_COMPOSITION_AUTHORITY_METADATA_ONLY_BEFORE_ANY_RUNTIME_OR_FINAL_ANSWER_LANE`",
                "",
            ]
        )

    summary = summarize_answer_composition_authority_artifact_v1(artifact)
    risk_lines = [f"- `{risk}`" for risk in summary["minor_risks"]]
    readiness_lines = [f"- `{label}`" for label in summary["readiness_labels"]]
    gates = artifact.get("composition_gate_statuses", {})
    gate_lines = [f"- `{gate}`: `{status}`" for gate, status in sorted(gates.items())]
    return "\n".join(
        [
            "# WESLR Answer Composition Authority Artifact V1",
            "",
            "## Artifact status",
            "- artifact_type: `answer_composition_authority_artifact_v1`",
            "- metadata_only: `True`",
            "- internal_only: `True`",
            "- valid: `True`",
            "- blocked: `False`",
            "",
            "## Coverage counts",
            f"- source_metadata_type_count: `{summary['source_metadata_type_count']}`",
            f"- composition_review_dimension_count: `{summary['composition_review_dimension_count']}`",
            f"- gate_status_count: `{summary['gate_status_count']}`",
            "",
            "## Gate statuses",
            *gate_lines,
            "",
            "## Denied paths",
            "- answer composition: `not_authorized`",
            "- answer authority: `not_granted`",
            "- runtime authority: `not_granted`",
            "- final answer generation: `not_authorized`",
            "- prompt execution: `not_authorized`",
            "- live dialogue: `not_authorized`",
            "- provider/search/advisor calls: `not_authorized`",
            "- `.weslr` writes: `not_authorized`",
            "- feature flags: `not_authorized`",
            "- judges/scoring: `not_authorized`",
            "- official claims: `not_allowed`",
            "",
            "## False authority flag summary",
            f"- all_authority_flags_false: `{summary['all_authority_flags_false']}`",
            "",
            "## Visible risks",
            *risk_lines,
            "",
            "## Readiness labels",
            *readiness_lines,
            "",
            "## Safety confirmation",
            "- metadata evidence may inform future review",
            "- metadata evidence is not answer text",
            "- metadata evidence is not answer composition authority",
            "- metadata evidence is not answer authority",
            "- no raw prompts, raw responses, private content, hidden prompts, answer keys, provider output, official scores, or final-answer prose rendered",
            "",
            "## Next lane recommendation",
            f"- `{summary['next_lane_recommendation']}`",
            "",
        ]
    )


def to_answer_composition_authority_artifact_json_safe_v1(artifact: dict) -> dict[str, Any]:
    """Return a JSON-safe metadata copy or explicit invalid wrapper."""

    validation = validate_answer_composition_authority_artifact_v1(artifact)
    if not validation["valid"]:
        reason_labels: list[str] = []
        for error in validation["errors"]:
            _append_unique(reason_labels, str(error).split(":", 1)[0])
        return {
            "artifact_type": INVALID_ARTIFACT_TYPE_V1,
            "valid": False,
            "blocked": True,
            "safe_to_render": False,
            "invalid_wrapper": True,
            "errors": reason_labels,
            "metadata_only": True,
            "internal_only": True,
            "answer_composition_authorized": False,
            "answer_authority_granted": False,
            "final_answer_generated": False,
            "runtime_authority_granted": False,
        }
    return _json_safe(artifact)
