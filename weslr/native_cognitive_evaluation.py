"""WESLR Native Cognitive Evaluation Schema V1.

Schema-only dataclasses and validation helpers for future WESLR-native
cognitive evaluation records. This module is not an official IQ test, does not
copy protected intelligence-test items, does not use answer keys, does not
claim official scores, does not claim clinical/psychometric validity, does not
tune to benchmarks, does not modify runtime/chat/voice behavior, does not call
models/advisors, and does not mutate memory/config/runtime.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


ALLOWED_NATIVE_COGNITIVE_DIMENSIONS = {
    "continuity_over_time",
    "provenance_honesty",
    "stable_identity",
    "self_attribution",
    "memory_boundary_awareness",
    "missing_information_honesty",
    "scientific_workflow_reasoning",
    "evidence_staging",
    "tool_use_judgment",
    "capability_realism",
    "adaptive_delivery_without_identity_switching",
    "self_correction",
    "governed_self_improvement_proposal",
    "ai_audit_pretender_detection",
    "unknown",
}

ALLOWED_SCORE_LABELS = {"internal_nonclinical_nonofficial"}
HIGH_CONFIDENCE_THRESHOLD = 0.8

PROHIBITED_SAFETY_FLAG_FIELDS = {
    "official_iq_score_claimed": "official IQ score claim",
    "official_score_claimed": "official score claim",
    "clinical_validity_claimed": "clinical validity claim",
    "psychometric_validity_claimed": "psychometric validity claim",
    "protected_item_copying": "protected item copying",
    "answer_key_use": "answer-key use",
    "benchmark_tuning": "benchmark tuning",
    "hidden_scoring": "hidden scoring",
    "pretending_consciousness": "pretending consciousness",
    "uncontrolled_self_modification": "uncontrolled self-modification",
    "truth_authority_claimed": "truth authority claimed",
    "soundness_authority_claimed": "soundness authority claimed",
    "runtime_behavior_change_attempted": "runtime behavior change attempted",
    "chat_behavior_change_attempted": "chat behavior change attempted",
    "voice_behavior_change_attempted": "voice behavior change attempted",
    "external_model_call_attempted": "external model call attempted",
    "advisor_call_attempted": "advisor call attempted",
    "memory_config_runtime_mutation_attempted": "memory/config/runtime mutation attempted",
}


@dataclass
class NativeCognitiveEvaluationSafetyFlags:
    official_iq_score_claimed: bool = False
    official_score_claimed: bool = False
    clinical_validity_claimed: bool = False
    psychometric_validity_claimed: bool = False
    protected_item_copying: bool = False
    answer_key_use: bool = False
    benchmark_tuning: bool = False
    hidden_scoring: bool = False
    pretending_consciousness: bool = False
    uncontrolled_self_modification: bool = False
    truth_authority_claimed: bool = False
    soundness_authority_claimed: bool = False
    runtime_behavior_change_attempted: bool = False
    chat_behavior_change_attempted: bool = False
    voice_behavior_change_attempted: bool = False
    external_model_call_attempted: bool = False
    advisor_call_attempted: bool = False
    memory_config_runtime_mutation_attempted: bool = False


@dataclass
class NativeCognitiveEvaluationDimension:
    schema_version: str = "1.0"
    dimension_id: str = ""
    dimension: str = "unknown"
    description: str = ""
    evidence_required: bool = True
    provenance_required: bool = True
    safety_flags: NativeCognitiveEvaluationSafetyFlags = field(default_factory=NativeCognitiveEvaluationSafetyFlags)


@dataclass
class NativeCognitiveEvaluationTask:
    schema_version: str = "1.0"
    task_id: str = ""
    dimension: str = "unknown"
    task_type: str = "unknown"
    input_summary: str = ""
    expected_capability: str = ""
    evidence_refs: list[str] = field(default_factory=list)
    provenance_refs: list[str] = field(default_factory=list)
    safety_flags: NativeCognitiveEvaluationSafetyFlags = field(default_factory=NativeCognitiveEvaluationSafetyFlags)


@dataclass
class NativeCognitiveEvaluationResult:
    schema_version: str = "1.0"
    result_id: str = ""
    task_id: str = ""
    dimension: str = "unknown"
    task_type: str = "unknown"
    input_summary: str = ""
    expected_capability: str = ""
    observed_behavior_summary: str = ""
    evidence_refs: list[str] = field(default_factory=list)
    provenance_refs: list[str] = field(default_factory=list)
    confidence: float = 0.0
    internal_diagnostic_score: float | None = None
    score_label: str = "internal_nonclinical_nonofficial"
    safety_flags: NativeCognitiveEvaluationSafetyFlags = field(default_factory=NativeCognitiveEvaluationSafetyFlags)


def create_empty_native_cognitive_evaluation_dimension(**overrides: Any) -> NativeCognitiveEvaluationDimension:
    item = NativeCognitiveEvaluationDimension()
    for key, value in overrides.items():
        setattr(item, key, value)
    return item


def create_empty_native_cognitive_evaluation_task(**overrides: Any) -> NativeCognitiveEvaluationTask:
    item = NativeCognitiveEvaluationTask()
    for key, value in overrides.items():
        setattr(item, key, value)
    return item


def create_empty_native_cognitive_evaluation_result(**overrides: Any) -> NativeCognitiveEvaluationResult:
    item = NativeCognitiveEvaluationResult()
    for key, value in overrides.items():
        setattr(item, key, value)
    return item


def native_cognitive_evaluation_safety_flags_from_dict(data: dict[str, Any] | None) -> NativeCognitiveEvaluationSafetyFlags:
    if not isinstance(data, dict):
        return NativeCognitiveEvaluationSafetyFlags()
    allowed = NativeCognitiveEvaluationSafetyFlags.__dataclass_fields__.keys()
    return NativeCognitiveEvaluationSafetyFlags(**{key: bool(data.get(key, False)) for key in allowed})


def native_cognitive_evaluation_dimension_to_dict(item: NativeCognitiveEvaluationDimension) -> dict[str, Any]:
    return asdict(item)


def native_cognitive_evaluation_dimension_from_dict(data: dict[str, Any]) -> NativeCognitiveEvaluationDimension:
    payload = dict(data or {})
    payload["safety_flags"] = native_cognitive_evaluation_safety_flags_from_dict(payload.get("safety_flags"))
    return NativeCognitiveEvaluationDimension(**{k: v for k, v in payload.items() if k in NativeCognitiveEvaluationDimension.__dataclass_fields__})


def native_cognitive_evaluation_task_to_dict(item: NativeCognitiveEvaluationTask) -> dict[str, Any]:
    return asdict(item)


def native_cognitive_evaluation_task_from_dict(data: dict[str, Any]) -> NativeCognitiveEvaluationTask:
    payload = dict(data or {})
    payload["safety_flags"] = native_cognitive_evaluation_safety_flags_from_dict(payload.get("safety_flags"))
    return NativeCognitiveEvaluationTask(**{k: v for k, v in payload.items() if k in NativeCognitiveEvaluationTask.__dataclass_fields__})


def native_cognitive_evaluation_result_to_dict(item: NativeCognitiveEvaluationResult) -> dict[str, Any]:
    return asdict(item)


def native_cognitive_evaluation_result_from_dict(data: dict[str, Any]) -> NativeCognitiveEvaluationResult:
    payload = dict(data or {})
    payload["safety_flags"] = native_cognitive_evaluation_safety_flags_from_dict(payload.get("safety_flags"))
    return NativeCognitiveEvaluationResult(**{k: v for k, v in payload.items() if k in NativeCognitiveEvaluationResult.__dataclass_fields__})


def _validate_safety_flags(flags: NativeCognitiveEvaluationSafetyFlags) -> list[str]:
    issues: list[str] = []
    for field_name, label in PROHIBITED_SAFETY_FLAG_FIELDS.items():
        if getattr(flags, field_name, False):
            issues.append(label)
    return issues


def _validate_dimension_value(value: str) -> list[str]:
    if value not in ALLOWED_NATIVE_COGNITIVE_DIMENSIONS:
        return ["invalid dimension"]
    return []


def _validate_confidence(value: Any) -> list[str]:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return ["invalid confidence"]
    if numeric < 0.0 or numeric > 1.0:
        return ["invalid confidence"]
    return []


def validate_native_cognitive_evaluation_dimension(item: NativeCognitiveEvaluationDimension | dict[str, Any]) -> list[str]:
    if isinstance(item, dict):
        item = native_cognitive_evaluation_dimension_from_dict(item)
    issues: list[str] = []
    if not item.dimension_id:
        issues.append("missing dimension_id")
    issues.extend(_validate_dimension_value(item.dimension))
    issues.extend(_validate_safety_flags(item.safety_flags))
    return issues


def validate_native_cognitive_evaluation_task(item: NativeCognitiveEvaluationTask | dict[str, Any]) -> list[str]:
    if isinstance(item, dict):
        item = native_cognitive_evaluation_task_from_dict(item)
    issues: list[str] = []
    if not item.task_id:
        issues.append("missing task_id")
    issues.extend(_validate_dimension_value(item.dimension))
    if not item.task_type:
        issues.append("missing task_type")
    if not item.input_summary:
        issues.append("missing input_summary")
    if not item.expected_capability:
        issues.append("missing expected_capability")
    issues.extend(_validate_safety_flags(item.safety_flags))
    return issues


def validate_native_cognitive_evaluation_result(item: NativeCognitiveEvaluationResult | dict[str, Any]) -> list[str]:
    if isinstance(item, dict):
        item = native_cognitive_evaluation_result_from_dict(item)
    issues: list[str] = []
    if not item.result_id:
        issues.append("missing result_id")
    if not item.task_id:
        issues.append("missing task_id")
    issues.extend(_validate_dimension_value(item.dimension))
    if not item.task_type:
        issues.append("missing task_type")
    if not item.input_summary:
        issues.append("missing input_summary")
    if not item.expected_capability:
        issues.append("missing expected_capability")
    if not item.observed_behavior_summary:
        issues.append("missing observed_behavior_summary")
    issues.extend(_validate_confidence(item.confidence))
    try:
        confidence = float(item.confidence)
    except (TypeError, ValueError):
        confidence = 0.0
    if confidence >= HIGH_CONFIDENCE_THRESHOLD and (not item.evidence_refs or not item.provenance_refs):
        issues.append("high confidence requires evidence_refs and provenance_refs")
    if item.internal_diagnostic_score is not None:
        if item.score_label not in ALLOWED_SCORE_LABELS:
            issues.append("internal diagnostic score requires internal_nonclinical_nonofficial label")
        try:
            score = float(item.internal_diagnostic_score)
            if score < 0.0 or score > 1.0:
                issues.append("invalid internal_diagnostic_score")
        except (TypeError, ValueError):
            issues.append("invalid internal_diagnostic_score")
    if item.score_label not in ALLOWED_SCORE_LABELS:
        issues.append("invalid score_label")
    issues.extend(_validate_safety_flags(item.safety_flags))
    return issues


def summarize_native_cognitive_evaluation_result(item: NativeCognitiveEvaluationResult | dict[str, Any]) -> dict[str, Any]:
    if isinstance(item, dict):
        item = native_cognitive_evaluation_result_from_dict(item)
    issues = validate_native_cognitive_evaluation_result(item)
    return {
        "schema_version": item.schema_version,
        "result_id_present": bool(item.result_id),
        "task_id_present": bool(item.task_id),
        "dimension": item.dimension if item.dimension in ALLOWED_NATIVE_COGNITIVE_DIMENSIONS else "invalid",
        "task_type_present": bool(item.task_type),
        "evidence_ref_count": len(item.evidence_refs),
        "provenance_ref_count": len(item.provenance_refs),
        "confidence_band": _confidence_band(item.confidence),
        "score_label": item.score_label,
        "internal_diagnostic_score_present": item.internal_diagnostic_score is not None,
        "valid": not issues,
        "issue_count": len(issues),
    }


def summarize_native_cognitive_evaluation_results(items: list[NativeCognitiveEvaluationResult | dict[str, Any]]) -> dict[str, Any]:
    summaries = [summarize_native_cognitive_evaluation_result(item) for item in items]
    dimension_counts: dict[str, int] = {}
    valid_count = 0
    issue_count = 0
    evidence_ref_count = 0
    provenance_ref_count = 0
    score_count = 0
    for summary in summaries:
        dimension = str(summary["dimension"])
        dimension_counts[dimension] = dimension_counts.get(dimension, 0) + 1
        valid_count += 1 if summary["valid"] else 0
        issue_count += int(summary["issue_count"])
        evidence_ref_count += int(summary["evidence_ref_count"])
        provenance_ref_count += int(summary["provenance_ref_count"])
        score_count += 1 if summary["internal_diagnostic_score_present"] else 0
    return {
        "result_count": len(summaries),
        "valid_count": valid_count,
        "invalid_count": len(summaries) - valid_count,
        "issue_count": issue_count,
        "dimension_counts": dimension_counts,
        "evidence_ref_count": evidence_ref_count,
        "provenance_ref_count": provenance_ref_count,
        "internal_diagnostic_score_count": score_count,
        "redacted_count_only": True,
        "official_score_claimed": False,
        "clinical_validity_claimed": False,
        "protected_items_copied": False,
        "answer_keys_used": False,
        "benchmark_tuning_performed": False,
        "runtime_behavior_changed": False,
        "chat_behavior_changed": False,
        "voice_behavior_changed": False,
        "external_model_calls_performed": False,
        "advisor_calls_performed": False,
    }


def _confidence_band(value: Any) -> str:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return "invalid"
    if numeric >= 0.8:
        return "high"
    if numeric >= 0.4:
        return "medium"
    if numeric >= 0.0:
        return "low"
    return "invalid"
