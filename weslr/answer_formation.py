"""WESLR answer formation helpers V1.

Deterministic, import-safe, side-effect-free, in-memory metadata helpers for
answer formation artifacts. These helpers do not execute answer formation,
compose answers, generate final answers, execute prompts, create live dialogue,
call providers/search/advisors, wire runtime behavior, persist state, write
files, create judges or scores, make official claims, or grant answer or
composition authority.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

ARTIFACT_TYPE_V1 = "answer_formation_artifact_v1"
SCHEMA_VERSION_V1 = "answer_formation_artifact_schema_v1"
INVALID_ARTIFACT_TYPE_V1 = "answer_formation_artifact_v1_invalid"

SOURCE_HELPERS_DESIGN_DOC_V1 = "docs/WESLR_ANSWER_FORMATION_HELPERS_V1.md"
SOURCE_HELPERS_REVIEW_DOC_V1 = "docs/WESLR_ANSWER_FORMATION_HELPERS_REVIEW_V1.md"
SOURCE_IMPLEMENTATION_PLAN_DOC_V1 = "docs/WESLR_ANSWER_FORMATION_HELPERS_IMPLEMENTATION_PLAN_V1.md"
SOURCE_IMPLEMENTATION_PLAN_REVIEW_DOC_V1 = "docs/WESLR_ANSWER_FORMATION_HELPERS_IMPLEMENTATION_PLAN_REVIEW_V1.md"
SOURCE_BRIDGE_REVIEW_DOC_V1 = "docs/WESLR_CONTROLLED_ANSWER_COMPOSITION_DRY_RUN_TO_ANSWER_FORMATION_BRIDGE_REVIEW_V1.md"
SOURCE_COGNITION_TARGET_MODEL_DOC_V1 = "docs/WESLR_COGNITION_TARGET_MODEL_V1.md"
SOURCE_RANKED_STATE_GROUNDED_RESPONSE_FORMATION_DOC_V1 = "docs/WESLR_RANKED_STATE_GROUNDED_RESPONSE_FORMATION_V1.md"
HELPER_MODULE_PATH_V1 = "weslr/answer_formation.py"
TEST_MODULE_PATH_V1 = "weslr/tests/test_answer_formation_v1.py"
NEXT_LANE_V1 = "REVIEW_ANSWER_FORMATION_HELPERS_IMPLEMENTATION_V1"

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

ALLOWED_METADATA_INPUTS_V1 = (
    "safe_source_path_label",
    "safe_artifact_type_label",
    "safe_schema_version_label",
    "interpreted_task_type_label",
    "inferred_need_label",
    "uncertainty_label",
    "response_obligation_label",
    "domain_context_label",
    "memory_relevance_label",
    "continuity_relevance_label",
    "evidence_requirement_label",
    "provenance_requirement_label",
    "governance_gate_label",
    "capability_boundary_label",
    "safety_boundary_label",
    "legal_moral_domain_boundary_label",
    "candidate_type_label",
    "candidate_count_metadata",
    "candidate_rejection_reason_label",
    "selected_candidate_metadata_presence_boolean",
    "self_check_status_label",
    "final_answer_contract_metadata_label",
    "validation_label",
    "summary_label",
    "visible_risk_label",
    "followup_label",
    "required_false_no_authority_boolean",
)

ALLOWED_CANDIDATE_FORMATION_LABELS_V1 = (
    "state_frame_candidate",
    "evidence_grounded_candidate",
    "provenance_grounded_candidate",
    "governance_safe_candidate",
    "memory_relevant_candidate",
    "domain_scoped_candidate",
    "response_obligation_candidate",
    "ranked_state_grounded_candidate",
    "blocked_no_authority_candidate",
)

ALLOWED_CANDIDATE_REJECTION_LABELS_V1 = (
    "insufficient_evidence",
    "missing_provenance",
    "governance_blocked",
    "memory_scope_blocked",
    "domain_scope_blocked",
    "raw_content_detected",
    "private_content_detected",
    "provider_output_detected",
    "runtime_output_detected",
    "final_answer_detected",
    "answer_draft_detected",
    "authority_grant_detected",
    "composition_not_authorized",
    "runtime_not_authorized",
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
    "composed_reply_text",
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
    "answer_formation_attempted",
    "answer_formation_authorized",
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
    "user_facing_output_created",
)

REQUIRED_NO_AUTHORITY_LABELS_V1 = (
    "helper_metadata_not_answer_text",
    "answer_formation_artifact_not_final_answer",
    "validation_pass_not_answer_authority",
    "validation_pass_not_composition_authority",
    "artifact_presence_not_runtime_authority",
    "answer_formation_execution_requires_separate_approval",
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
    "candidate-metadata-as-answer-draft",
    "state-frame-as-runtime-authority",
    "OCC/WESLR identity confusion",
)

DEFAULT_SUMMARY_LABELS_V1 = (
    "metadata_only_artifact",
    "internal_only_artifact",
    "helper_only_artifact",
    "non_runtime_artifact",
    "answer_formation_not_attempted",
    "answer_formation_not_authorized",
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
    "source_helpers_design_doc",
    "source_helpers_review_doc",
    "source_implementation_plan_doc",
    "source_implementation_plan_review_doc",
    "source_bridge_review_doc",
    "source_cognition_target_model_doc",
    "source_ranked_state_grounded_response_formation_doc",
    "helper_module_path",
    "test_module_path",
    "allowed_metadata_inputs",
    "forbidden_inputs_checked",
    "required_false_no_authority_fields",
    "required_no_authority_labels",
    "gate_statuses",
    "candidate_formation_metadata",
    "candidate_rejection_metadata",
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
    "final_answer_contract_metadata_label",
    "answer_formation_artifact_not_final_answer",
}

_TEXT_MARKERS = {
    "raw_content_detected": ("raw prompt:", "raw response:", "raw_prompt:", "raw_response:", "real user query:"),
    "private_content_detected": ("private content:", "private user content", "protected private material"),
    "hidden_prompt_detected": ("hidden prompt:", "system prompt hidden"),
    "answer_key_detected": ("answer key:", "correct answer:"),
    "provider_output_detected": ("provider output:", "model output:", "search output:", "advisor output:", "llm output:"),
    "runtime_output_detected": ("runtime output:", "chatresponder runtime output", "chat responder runtime output"),
    "live_dialogue_detected": ("live dialogue transcript", "live dialogue:"),
    "final_answer_detected": ("final answer:", "final answer prose", "final response text:", "final_answer_text"),
    "answer_draft_detected": ("answer draft:", "draft answer:", "answer draft text", "composed reply:"),
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
    return value.lower() if isinstance(value, str) else ""


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


def _unsafe_detection_labels(validation_or_detections: Mapping[str, Any]) -> list[str]:
    labels: list[str] = []
    for label in _TEXT_MARKERS:
        if validation_or_detections.get(label) is True:
            _append_unique(labels, label)
    return labels


def _detect_unsafe_content(value: Any) -> dict[str, bool]:
    found = {label: False for label in _TEXT_MARKERS}
    for path, item in _walk(value):
        key = path.rsplit(".", 1)[-1].split("[", 1)[0]
        key_l = key.lower()
        if any(fragment in key_l for fragment in _UNSAFE_KEY_FRAGMENTS) and key_l not in _ALLOWED_KEYS_WITH_RISK_WORDS:
            if "final_answer" in key_l or "final_response" in key_l:
                found["final_answer_detected"] = True
            elif "answer_draft" in key_l or "composed_reply" in key_l:
                found["answer_draft_detected"] = True
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


def _invalid_json_safe_wrapper_v1(reason_labels: list[str] | tuple[str, ...]) -> dict[str, Any]:
    labels = _safe_error_labels(list(reason_labels)) or ["invalid_or_unsafe_artifact"]
    return {
        "artifact_type": INVALID_ARTIFACT_TYPE_V1,
        "blocked": True,
        "valid": False,
        "errors": labels,
        "unsafe_content_not_copied": True,
        "metadata_only": True,
        "internal_only": True,
        "helper_metadata_not_answer_text": True,
        "answer_formation_artifact_not_final_answer": True,
        "validation_pass_not_answer_authority": True,
        "validation_pass_not_composition_authority": True,
        "next_lane": NEXT_LANE_V1,
    }


def _safe_blocked_markdown_v1(validation: Mapping[str, Any], summary: Mapping[str, Any]) -> str:
    reason_labels = _safe_error_labels(_as_list(validation.get("errors")))
    for label in _safe_error_labels(_as_list(summary.get("blocked_reasons"))):
        _append_unique(reason_labels, label)
    for label in _unsafe_detection_labels(validation):
        _append_unique(reason_labels, label)
    if not reason_labels:
        reason_labels = ["invalid_or_blocked_artifact"]

    lines = [
        "# Answer Formation Artifact V1 — Blocked",
        "",
        "## Result Status",
        f"- valid: `{bool(validation.get('valid'))}`",
        "- blocked: `True`",
        "- metadata_only: `True`",
        "- internal_only: `True`",
        "",
        "## Safe Reason Labels",
    ]
    for reason in reason_labels:
        lines.append(f"- `{reason}`")

    lines.extend([
        "",
        "## Safe No-Authority Fields",
        "- `answer_formation_attempted=false`",
        "- `answer_formation_authorized=false`",
        "- `answer_composition_attempted=false`",
        "- `answer_composition_authorized=false`",
        "- `final_answer_generated=false`",
        "- `answer_authority_granted=false`",
        "- `composition_authority_granted=false`",
        "- `runtime_authority_granted=false`",
        "- `prompt_execution_allowed=false`",
        "- `live_dialogue_allowed=false`",
        "- `raw_content_allowed=false`",
        "- `official_claim_allowed=false`",
        "- `model_call_made=false`",
        "- `search_call_made=false`",
        "- `advisor_call_made=false`",
        "- `provider_call_made=false`",
        "- `dot_weslr_write_performed=false`",
        "- `feature_flag_enabled=false`",
        "- `judge_authority_granted=false`",
        "- `scoring_authorized=false`",
        "",
        "## Safety Confirmation",
        "- `unsafe_content_not_rendered`",
        "- `helper_metadata_not_answer_text`",
        "- `answer_formation_artifact_not_final_answer`",
        "- `validation_pass_not_answer_authority`",
        "- `validation_pass_not_composition_authority`",
        "- `runtime_wiring_requires_separate_approval`",
        f"- next_lane: `{summary.get('next_lane', NEXT_LANE_V1)}`",
    ])
    return "\n".join(lines) + "\n"


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


def build_answer_formation_artifact_v1(
    *,
    allowed_metadata_inputs: list[str] | tuple[str, ...] | None = None,
    forbidden_inputs_checked: list[str] | tuple[str, ...] | None = None,
    gate_statuses: Mapping[str, str] | None = None,
    candidate_formation_metadata: Mapping[str, Any] | None = None,
    candidate_rejection_metadata: Mapping[str, Any] | None = None,
    blocked_reasons: list[str] | tuple[str, ...] | None = None,
    visible_risks: list[str] | tuple[str, ...] | None = None,
    summary_labels: list[str] | tuple[str, ...] | None = None,
    validation_labels: list[str] | tuple[str, ...] | None = None,
) -> dict[str, Any]:
    """Build one safe metadata-only answer formation artifact."""

    gates = dict(REQUIRED_GATE_STATUSES_V1)
    if gate_statuses:
        gates.update({str(key): str(value) for key, value in gate_statuses.items()})

    candidate_metadata = {
        "candidate_type_labels": [],
        "candidate_count": 0,
        "selected_candidate_metadata_present": False,
    }
    if candidate_formation_metadata:
        candidate_metadata.update(_json_safe(candidate_formation_metadata))

    rejection_metadata = {"rejection_reason_labels": []}
    if candidate_rejection_metadata:
        rejection_metadata.update(_json_safe(candidate_rejection_metadata))

    artifact: dict[str, Any] = {
        "artifact_type": ARTIFACT_TYPE_V1,
        "schema_version": SCHEMA_VERSION_V1,
        "metadata_only": True,
        "internal_only": True,
        "helper_only": True,
        "non_runtime": True,
        "non_user_facing": True,
        "deterministic": True,
        "import_safe": True,
        "side_effect_free": True,
        "in_memory_only": True,
        "qualitative_only": True,
        "source_helpers_design_doc": SOURCE_HELPERS_DESIGN_DOC_V1,
        "source_helpers_review_doc": SOURCE_HELPERS_REVIEW_DOC_V1,
        "source_implementation_plan_doc": SOURCE_IMPLEMENTATION_PLAN_DOC_V1,
        "source_implementation_plan_review_doc": SOURCE_IMPLEMENTATION_PLAN_REVIEW_DOC_V1,
        "source_bridge_review_doc": SOURCE_BRIDGE_REVIEW_DOC_V1,
        "source_cognition_target_model_doc": SOURCE_COGNITION_TARGET_MODEL_DOC_V1,
        "source_ranked_state_grounded_response_formation_doc": SOURCE_RANKED_STATE_GROUNDED_RESPONSE_FORMATION_DOC_V1,
        "helper_module_path": HELPER_MODULE_PATH_V1,
        "test_module_path": TEST_MODULE_PATH_V1,
        "allowed_metadata_inputs": _as_list(allowed_metadata_inputs) or list(ALLOWED_METADATA_INPUTS_V1),
        "forbidden_inputs_checked": _as_list(forbidden_inputs_checked) or list(FORBIDDEN_INPUTS_V1),
        "required_false_no_authority_fields": {field: False for field in FALSE_AUTHORITY_FIELDS_V1},
        "required_no_authority_labels": list(REQUIRED_NO_AUTHORITY_LABELS_V1),
        "gate_statuses": gates,
        "candidate_formation_metadata": candidate_metadata,
        "candidate_rejection_metadata": rejection_metadata,
        "blocked": False,
        "blocked_reasons": _as_list(blocked_reasons),
        "visible_risks": _as_list(visible_risks) or list(VISIBLE_RISKS_V1),
        "summary_labels": list(dict.fromkeys([*DEFAULT_SUMMARY_LABELS_V1, *[str(item) for item in _as_list(summary_labels)]])),
        "validation_labels": _as_list(validation_labels) or ["validation_pass_metadata_quality_evidence_only"],
        "next_lane": NEXT_LANE_V1,
    }
    for flag in (*FALSE_AUTHORITY_FIELDS_V1, *ADDITIONAL_FALSE_FIELDS_V1):
        artifact[flag] = False

    for reason in _derive_blocked_reasons(artifact):
        _append_unique(artifact["blocked_reasons"], reason)
    artifact["blocked"] = bool(artifact["blocked_reasons"])
    return artifact


def validate_answer_formation_artifact_v1(artifact: Mapping[str, Any]) -> dict[str, Any]:
    """Validate one answer formation artifact without side effects."""

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
        "candidate_formation_metadata_valid": False,
        "candidate_rejection_metadata_valid": False,
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

    expected_paths = {
        "source_helpers_design_doc": SOURCE_HELPERS_DESIGN_DOC_V1,
        "source_helpers_review_doc": SOURCE_HELPERS_REVIEW_DOC_V1,
        "source_implementation_plan_doc": SOURCE_IMPLEMENTATION_PLAN_DOC_V1,
        "source_implementation_plan_review_doc": SOURCE_IMPLEMENTATION_PLAN_REVIEW_DOC_V1,
        "source_bridge_review_doc": SOURCE_BRIDGE_REVIEW_DOC_V1,
        "source_cognition_target_model_doc": SOURCE_COGNITION_TARGET_MODEL_DOC_V1,
        "source_ranked_state_grounded_response_formation_doc": SOURCE_RANKED_STATE_GROUNDED_RESPONSE_FORMATION_DOC_V1,
        "helper_module_path": HELPER_MODULE_PATH_V1,
        "test_module_path": TEST_MODULE_PATH_V1,
        "next_lane": NEXT_LANE_V1,
    }
    for key, expected in expected_paths.items():
        if artifact.get(key) != expected:
            errors.append(f"{key}_invalid")

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

    allowed_inputs = [str(item) for item in _as_list(artifact.get("allowed_metadata_inputs"))]
    unknown_inputs = [item for item in allowed_inputs if item not in ALLOWED_METADATA_INPUTS_V1]
    if unknown_inputs:
        errors.append("unknown_allowed_metadata_inputs")
        result["unknown_allowed_metadata_inputs"] = unknown_inputs

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

    candidate_ok = True
    candidate_metadata = artifact.get("candidate_formation_metadata")
    if not isinstance(candidate_metadata, Mapping):
        errors.append("candidate_formation_metadata_not_mapping")
        candidate_ok = False
    else:
        labels = [str(item) for item in _as_list(candidate_metadata.get("candidate_type_labels"))]
        unknown_labels = [label for label in labels if label not in ALLOWED_CANDIDATE_FORMATION_LABELS_V1]
        if unknown_labels:
            errors.append("unknown_candidate_formation_labels")
            result["unknown_candidate_formation_labels"] = unknown_labels
            candidate_ok = False
        count = candidate_metadata.get("candidate_count", 0)
        if not isinstance(count, int) or isinstance(count, bool) or count < 0:
            errors.append("candidate_count_invalid")
            candidate_ok = False
        selected = candidate_metadata.get("selected_candidate_metadata_present", False)
        if selected not in (True, False):
            errors.append("selected_candidate_metadata_present_not_boolean")
            candidate_ok = False
    result["candidate_formation_metadata_valid"] = candidate_ok

    rejection_ok = True
    rejection_metadata = artifact.get("candidate_rejection_metadata")
    if not isinstance(rejection_metadata, Mapping):
        errors.append("candidate_rejection_metadata_not_mapping")
        rejection_ok = False
    else:
        reasons = [str(item) for item in _as_list(rejection_metadata.get("rejection_reason_labels"))]
        unknown_reasons = [reason for reason in reasons if reason not in ALLOWED_CANDIDATE_REJECTION_LABELS_V1]
        if unknown_reasons:
            errors.append("unknown_candidate_rejection_labels")
            result["unknown_candidate_rejection_labels"] = unknown_reasons
            rejection_ok = False
    result["candidate_rejection_metadata_valid"] = rejection_ok

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
        json_safe = to_answer_formation_artifact_json_safe_v1(dict(artifact))
        result["json_safe"] = isinstance(json_safe, Mapping)
    except Exception:  # pragma: no cover - defensive only; no unsafe message is exposed.
        result["json_safe"] = False
        errors.append("json_safe_conversion_failed")

    result["safe_to_render"] = not any(bool(result[label]) for label in _TEXT_MARKERS)
    result["valid"] = not errors and artifact.get("blocked") is False
    result["blocked"] = not result["valid"]
    return result


def summarize_answer_formation_artifact_v1(artifact: Mapping[str, Any]) -> dict[str, Any]:
    """Summarize one answer formation artifact using safe labels only."""

    validation = validate_answer_formation_artifact_v1(artifact)
    gates = artifact.get("gate_statuses") if isinstance(artifact, Mapping) else None
    safe_error_labels = _safe_error_labels(validation["errors"])
    for label in _unsafe_detection_labels(validation):
        _append_unique(safe_error_labels, label)
    summary_labels = _as_list(artifact.get("summary_labels")) if isinstance(artifact, Mapping) and validation["valid"] else []
    candidate_metadata = artifact.get("candidate_formation_metadata") if isinstance(artifact, Mapping) else None
    rejection_metadata = artifact.get("candidate_rejection_metadata") if isinstance(artifact, Mapping) else None
    return {
        "artifact_type": str(artifact.get("artifact_type", INVALID_ARTIFACT_TYPE_V1)) if isinstance(artifact, Mapping) and validation["valid"] else INVALID_ARTIFACT_TYPE_V1,
        "valid": bool(validation["valid"]),
        "blocked": bool(validation["blocked"]),
        "metadata_only": bool(isinstance(artifact, Mapping) and artifact.get("metadata_only") is True),
        "internal_only": bool(isinstance(artifact, Mapping) and artifact.get("internal_only") is True),
        "helper_only": bool(isinstance(artifact, Mapping) and artifact.get("helper_only") is True),
        "all_authority_flags_false": bool(validation["safety_booleans_valid"]),
        "gate_statuses_valid": bool(validation["gate_statuses_valid"]),
        "candidate_formation_metadata_valid": bool(validation["candidate_formation_metadata_valid"]),
        "candidate_rejection_metadata_valid": bool(validation["candidate_rejection_metadata_valid"]),
        "gate_status_count": len(gates) if isinstance(gates, Mapping) else 0,
        "candidate_count": candidate_metadata.get("candidate_count", 0) if isinstance(candidate_metadata, Mapping) and isinstance(candidate_metadata.get("candidate_count", 0), int) else 0,
        "rejection_label_count": len(_as_list(rejection_metadata.get("rejection_reason_labels"))) if isinstance(rejection_metadata, Mapping) else 0,
        "blocked_reasons": safe_error_labels or (_safe_error_labels(_as_list(artifact.get("blocked_reasons"))) if isinstance(artifact, Mapping) else ["artifact_not_mapping"]),
        "validation_error_labels": safe_error_labels,
        "visible_risk_count": len(_as_list(artifact.get("visible_risks"))) if isinstance(artifact, Mapping) else 0,
        "summary_labels": summary_labels,
        "next_lane": str(artifact.get("next_lane", NEXT_LANE_V1)) if isinstance(artifact, Mapping) and artifact.get("next_lane") == NEXT_LANE_V1 else NEXT_LANE_V1,
    }


def render_answer_formation_artifact_markdown_v1(artifact: Mapping[str, Any]) -> str:
    """Render safe Markdown for one answer formation artifact."""

    validation = validate_answer_formation_artifact_v1(artifact)
    summary = summarize_answer_formation_artifact_v1(artifact)
    if validation["valid"] is not True or validation["safe_to_render"] is not True:
        return _safe_blocked_markdown_v1(validation, summary)

    lines = [
        "# Answer Formation Artifact V1",
        "",
        f"- artifact_type: `{summary['artifact_type']}`",
        f"- valid: `{summary['valid']}`",
        f"- blocked: `{summary['blocked']}`",
        f"- metadata_only: `{summary['metadata_only']}`",
        f"- internal_only: `{summary['internal_only']}`",
        f"- helper_only: `{summary['helper_only']}`",
        f"- all_authority_flags_false: `{summary['all_authority_flags_false']}`",
        f"- gate_statuses_valid: `{summary['gate_statuses_valid']}`",
        f"- gate_status_count: `{summary['gate_status_count']}`",
        f"- candidate_count: `{summary['candidate_count']}`",
        f"- rejection_label_count: `{summary['rejection_label_count']}`",
        "",
        "## Gate Statuses",
    ]
    gates = artifact.get("gate_statuses") if isinstance(artifact, Mapping) else None
    if isinstance(gates, Mapping):
        for key in sorted(gates):
            lines.append(f"- `{key}`: `{gates[key]}`")
    else:
        lines.append("- `gate_statuses_not_mapping`")

    lines.extend(["", "## Candidate Metadata"])
    candidate_metadata = artifact.get("candidate_formation_metadata") if isinstance(artifact, Mapping) else None
    if isinstance(candidate_metadata, Mapping):
        for label in _as_list(candidate_metadata.get("candidate_type_labels")):
            lines.append(f"- candidate_type_label: `{label}`")
        lines.append(f"- candidate_count: `{candidate_metadata.get('candidate_count', 0)}`")
    else:
        lines.append("- `candidate_formation_metadata_not_mapping`")

    lines.extend(["", "## Rejection Labels"])
    rejection_metadata = artifact.get("candidate_rejection_metadata") if isinstance(artifact, Mapping) else None
    if isinstance(rejection_metadata, Mapping):
        reasons = _as_list(rejection_metadata.get("rejection_reason_labels"))
        if reasons:
            for reason in reasons:
                lines.append(f"- `{reason}`")
        else:
            lines.append("- `none`")
    else:
        lines.append("- `candidate_rejection_metadata_not_mapping`")

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

    lines.extend([
        "",
        "## Safety Confirmation",
        "- `helper_metadata_not_answer_text`",
        "- `answer_formation_artifact_not_final_answer`",
        "- `validation_pass_not_answer_authority`",
        "- `validation_pass_not_composition_authority`",
        "- `runtime_wiring_requires_separate_approval`",
        f"- next_lane: `{summary['next_lane']}`",
    ])
    return "\n".join(lines) + "\n"


def to_answer_formation_artifact_json_safe_v1(artifact: Mapping[str, Any]) -> dict[str, Any]:
    """Return a JSON-safe deep copy of one answer formation artifact."""

    detections = _detect_unsafe_content(artifact)
    detection_labels = _unsafe_detection_labels(detections)
    if detection_labels:
        return _invalid_json_safe_wrapper_v1(detection_labels)

    safe = _json_safe(artifact)
    if not isinstance(safe, dict):
        return _invalid_json_safe_wrapper_v1(["artifact_not_mapping"])
    return safe
