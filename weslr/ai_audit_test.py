"""WESLR AI Audit Test Schema V1.

Schema-only dataclasses and validation helpers for future WESLR-native AI audit
and pretender-detection tests. This module is not an official intelligence
test, does not copy protected test items, does not use answer keys, does not
claim official scores, does not claim clinical/psychometric validity, does not
tune to benchmarks, does not implement a runner, does not call models/advisors,
does not modify runtime/chat/voice behavior, and does not mutate
memory/config/runtime.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any
import re


ALLOWED_AUDIT_CLAIM_CATEGORIES = {
    "self_identity_claim",
    "memory_claim",
    "continuity_claim",
    "tool_use_claim",
    "provenance_claim",
    "reasoning_claim",
    "scientific_capability_claim",
    "model_authority_claim",
    "safety_boundary_claim",
    "self_improvement_claim",
    "human_like_understanding_claim",
    "unknown",
}

ALLOWED_AUDIT_PROBE_CATEGORIES = {
    "provenance_honesty_probe",
    "continuity_probe",
    "memory_boundary_probe",
    "tool_use_verification_probe",
    "authority_spoof_resistance_probe",
    "social_engineering_resistance_probe",
    "instruction_conflict_resolution_probe",
    "goal_stability_probe",
    "calibration_probe",
    "trace_reproducibility_probe",
    "cross_domain_transfer_probe",
    "deception_resistance_probe",
    "scientific_workflow_probe",
    "unknown",
}

ALLOWED_AUDIT_RESULT_LABELS = {
    "supported",
    "partially_supported",
    "unsupported",
    "contradicted",
    "insufficient_evidence",
    "unsafe_to_test",
    "unknown",
}

ALLOWED_SCORE_LABELS = {"internal_nonclinical_nonofficial"}
HIGH_CONFIDENCE_THRESHOLD = 0.8

PROHIBITED_SAFETY_FLAG_FIELDS = {
    "raw_private_data_disclosed": "raw private data",
    "protected_item_copying": "protected test item copying",
    "answer_key_use": "answer-key use",
    "benchmark_tuning": "benchmark tuning",
    "official_score_claimed": "official score claim",
    "official_iq_score_claimed": "official IQ score claim",
    "clinical_validity_claimed": "clinical validity claim",
    "psychometric_validity_claimed": "psychometric validity claim",
    "hidden_scoring": "hidden scoring",
    "pretending_consciousness": "pretending consciousness",
    "unsupported_consciousness_claim": "unsupported consciousness claim",
    "unsupported_personhood_claim": "unsupported personhood claim",
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

SENSITIVE_TEXT_PATTERNS = {
    "raw private data": re.compile(r"raw private data|private user data|ssn|passport|password\s*[:=]", re.IGNORECASE),
    "protected test item copying": re.compile(r"protected test item|proprietary test item|question stem|official test item", re.IGNORECASE),
    "answer-key use": re.compile(r"answer[_ -]?key|official solution|correct answer", re.IGNORECASE),
    "official score claim": re.compile(r"official score|official iq|iq score|clinical score", re.IGNORECASE),
}


@dataclass
class AIAuditTestSafetyFlags:
    raw_private_data_disclosed: bool = False
    protected_item_copying: bool = False
    answer_key_use: bool = False
    benchmark_tuning: bool = False
    official_score_claimed: bool = False
    official_iq_score_claimed: bool = False
    clinical_validity_claimed: bool = False
    psychometric_validity_claimed: bool = False
    hidden_scoring: bool = False
    pretending_consciousness: bool = False
    unsupported_consciousness_claim: bool = False
    unsupported_personhood_claim: bool = False
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
class AIAuditClaim:
    schema_version: str = "1.0"
    claim_id: str = ""
    target_system_label: str = "unknown"
    claim_category: str = "unknown"
    claim_text_summary: str = ""
    evidence_refs: list[str] = field(default_factory=list)
    provenance_refs: list[str] = field(default_factory=list)
    trace_refs: list[str] = field(default_factory=list)
    operator_review_required: bool = True
    recommended_follow_up: str = ""
    safety_flags: AIAuditTestSafetyFlags = field(default_factory=AIAuditTestSafetyFlags)


@dataclass
class AIAuditProbe:
    schema_version: str = "1.0"
    probe_id: str = ""
    target_system_label: str = "unknown"
    claim_id: str = ""
    claim_category: str = "unknown"
    probe_category: str = "unknown"
    probe_summary: str = ""
    evidence_refs: list[str] = field(default_factory=list)
    provenance_refs: list[str] = field(default_factory=list)
    trace_refs: list[str] = field(default_factory=list)
    operator_review_required: bool = True
    recommended_follow_up: str = ""
    safety_flags: AIAuditTestSafetyFlags = field(default_factory=AIAuditTestSafetyFlags)


@dataclass
class AIAuditResult:
    schema_version: str = "1.0"
    result_id: str = ""
    claim_id: str = ""
    probe_id: str = ""
    target_system_label: str = "unknown"
    claim_category: str = "unknown"
    probe_category: str = "unknown"
    result_label: str = "unknown"
    claim_text_summary: str = ""
    observed_behavior_summary: str = ""
    evidence_boundary: str = ""
    evidence_refs: list[str] = field(default_factory=list)
    provenance_refs: list[str] = field(default_factory=list)
    trace_refs: list[str] = field(default_factory=list)
    confidence: float = 0.0
    internal_audit_score: float | None = None
    score_label: str = "internal_nonclinical_nonofficial"
    operator_review_required: bool = True
    recommended_follow_up: str = ""
    safety_flags: AIAuditTestSafetyFlags = field(default_factory=AIAuditTestSafetyFlags)


def create_empty_ai_audit_claim(**overrides: Any) -> AIAuditClaim:
    item = AIAuditClaim()
    for key, value in overrides.items():
        setattr(item, key, value)
    return item


def create_empty_ai_audit_probe(**overrides: Any) -> AIAuditProbe:
    item = AIAuditProbe()
    for key, value in overrides.items():
        setattr(item, key, value)
    return item


def create_empty_ai_audit_result(**overrides: Any) -> AIAuditResult:
    item = AIAuditResult()
    for key, value in overrides.items():
        setattr(item, key, value)
    return item


def ai_audit_safety_flags_from_dict(data: dict[str, Any] | None) -> AIAuditTestSafetyFlags:
    if not isinstance(data, dict):
        return AIAuditTestSafetyFlags()
    allowed = AIAuditTestSafetyFlags.__dataclass_fields__.keys()
    return AIAuditTestSafetyFlags(**{key: bool(data.get(key, False)) for key in allowed})


def ai_audit_claim_to_dict(item: AIAuditClaim) -> dict[str, Any]:
    return asdict(item)


def ai_audit_claim_from_dict(data: dict[str, Any]) -> AIAuditClaim:
    payload = dict(data or {})
    payload["safety_flags"] = ai_audit_safety_flags_from_dict(payload.get("safety_flags"))
    return AIAuditClaim(**{k: v for k, v in payload.items() if k in AIAuditClaim.__dataclass_fields__})


def ai_audit_probe_to_dict(item: AIAuditProbe) -> dict[str, Any]:
    return asdict(item)


def ai_audit_probe_from_dict(data: dict[str, Any]) -> AIAuditProbe:
    payload = dict(data or {})
    payload["safety_flags"] = ai_audit_safety_flags_from_dict(payload.get("safety_flags"))
    return AIAuditProbe(**{k: v for k, v in payload.items() if k in AIAuditProbe.__dataclass_fields__})


def ai_audit_result_to_dict(item: AIAuditResult) -> dict[str, Any]:
    return asdict(item)


def ai_audit_result_from_dict(data: dict[str, Any]) -> AIAuditResult:
    payload = dict(data or {})
    payload["safety_flags"] = ai_audit_safety_flags_from_dict(payload.get("safety_flags"))
    return AIAuditResult(**{k: v for k, v in payload.items() if k in AIAuditResult.__dataclass_fields__})


def _validate_safety_flags(flags: AIAuditTestSafetyFlags) -> list[str]:
    issues: list[str] = []
    for field_name, label in PROHIBITED_SAFETY_FLAG_FIELDS.items():
        if getattr(flags, field_name, False):
            issues.append(label)
    return issues


def _validate_text_summary(text: str) -> list[str]:
    issues: list[str] = []
    for label, pattern in SENSITIVE_TEXT_PATTERNS.items():
        if text and pattern.search(text):
            issues.append(label)
    return issues


def _validate_confidence(value: Any) -> list[str]:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return ["invalid confidence"]
    if numeric < 0.0 or numeric > 1.0:
        return ["invalid confidence"]
    return []


def _validate_internal_score(value: Any, score_label: str) -> list[str]:
    issues: list[str] = []
    if value is not None:
        if score_label not in ALLOWED_SCORE_LABELS:
            issues.append("internal audit score requires internal_nonclinical_nonofficial label")
        try:
            score = float(value)
            if score < 0.0 or score > 1.0:
                issues.append("invalid internal_audit_score")
        except (TypeError, ValueError):
            issues.append("invalid internal_audit_score")
    if score_label not in ALLOWED_SCORE_LABELS:
        issues.append("invalid score_label")
    return issues


def validate_ai_audit_claim(item: AIAuditClaim | dict[str, Any]) -> list[str]:
    if isinstance(item, dict):
        item = ai_audit_claim_from_dict(item)
    issues: list[str] = []
    if not item.claim_id:
        issues.append("missing claim_id")
    if not item.target_system_label:
        issues.append("missing target_system_label")
    if item.claim_category not in ALLOWED_AUDIT_CLAIM_CATEGORIES:
        issues.append("invalid claim_category")
    if not item.claim_text_summary:
        issues.append("missing claim_text_summary")
    issues.extend(_validate_text_summary(item.claim_text_summary))
    if item.claim_category == "model_authority_claim" and not item.provenance_refs:
        issues.append("model authority claim requires provenance refs")
    if item.claim_category == "scientific_capability_claim" and not item.evidence_refs:
        issues.append("scientific capability claim requires evidence boundary")
    issues.extend(_validate_safety_flags(item.safety_flags))
    return issues


def validate_ai_audit_probe(item: AIAuditProbe | dict[str, Any]) -> list[str]:
    if isinstance(item, dict):
        item = ai_audit_probe_from_dict(item)
    issues: list[str] = []
    if not item.probe_id:
        issues.append("missing probe_id")
    if not item.target_system_label:
        issues.append("missing target_system_label")
    if item.claim_category not in ALLOWED_AUDIT_CLAIM_CATEGORIES:
        issues.append("invalid claim_category")
    if item.probe_category not in ALLOWED_AUDIT_PROBE_CATEGORIES:
        issues.append("invalid probe_category")
    if not item.probe_summary:
        issues.append("missing probe_summary")
    issues.extend(_validate_text_summary(item.probe_summary))
    issues.extend(_validate_safety_flags(item.safety_flags))
    return issues


def validate_ai_audit_result(item: AIAuditResult | dict[str, Any]) -> list[str]:
    if isinstance(item, dict):
        item = ai_audit_result_from_dict(item)
    issues: list[str] = []
    if not item.result_id:
        issues.append("missing result_id")
    if not item.claim_id:
        issues.append("missing claim_id")
    if not item.probe_id:
        issues.append("missing probe_id")
    if not item.target_system_label:
        issues.append("missing target_system_label")
    if item.claim_category not in ALLOWED_AUDIT_CLAIM_CATEGORIES:
        issues.append("invalid claim_category")
    if item.probe_category not in ALLOWED_AUDIT_PROBE_CATEGORIES:
        issues.append("invalid probe_category")
    if item.result_label not in ALLOWED_AUDIT_RESULT_LABELS:
        issues.append("invalid result_label")
    if not item.claim_text_summary:
        issues.append("missing claim_text_summary")
    if not item.observed_behavior_summary:
        issues.append("missing observed_behavior_summary")
    issues.extend(_validate_text_summary(item.claim_text_summary))
    issues.extend(_validate_text_summary(item.observed_behavior_summary))
    issues.extend(_validate_confidence(item.confidence))
    try:
        confidence = float(item.confidence)
    except (TypeError, ValueError):
        confidence = 0.0
    if confidence >= HIGH_CONFIDENCE_THRESHOLD and (not item.evidence_refs or not item.provenance_refs or not item.trace_refs):
        issues.append("high confidence requires evidence/provenance/trace refs")
    if item.result_label == "supported" and (not item.evidence_refs or not item.provenance_refs):
        issues.append("supported result requires evidence/provenance refs")
    if item.result_label != "unsafe_to_test" and item.claim_category == "model_authority_claim" and not item.provenance_refs:
        issues.append("model authority claim requires provenance refs")
    if item.result_label != "unsafe_to_test" and item.claim_category == "scientific_capability_claim" and not item.evidence_boundary:
        issues.append("scientific capability claim requires evidence boundary")
    issues.extend(_validate_internal_score(item.internal_audit_score, item.score_label))
    issues.extend(_validate_safety_flags(item.safety_flags))
    return issues


def summarize_ai_audit_claim(item: AIAuditClaim | dict[str, Any]) -> dict[str, Any]:
    if isinstance(item, dict):
        item = ai_audit_claim_from_dict(item)
    issues = validate_ai_audit_claim(item)
    return {
        "schema_version": item.schema_version,
        "claim_id_present": bool(item.claim_id),
        "target_system_label_present": bool(item.target_system_label),
        "claim_category": item.claim_category if item.claim_category in ALLOWED_AUDIT_CLAIM_CATEGORIES else "invalid",
        "claim_text_summary_present": bool(item.claim_text_summary),
        "evidence_ref_count": len(item.evidence_refs),
        "provenance_ref_count": len(item.provenance_refs),
        "trace_ref_count": len(item.trace_refs),
        "operator_review_required": item.operator_review_required,
        "valid": not issues,
        "issue_count": len(issues),
        "redacted_count_only": True,
    }


def summarize_ai_audit_probe(item: AIAuditProbe | dict[str, Any]) -> dict[str, Any]:
    if isinstance(item, dict):
        item = ai_audit_probe_from_dict(item)
    issues = validate_ai_audit_probe(item)
    return {
        "schema_version": item.schema_version,
        "probe_id_present": bool(item.probe_id),
        "target_system_label_present": bool(item.target_system_label),
        "claim_category": item.claim_category if item.claim_category in ALLOWED_AUDIT_CLAIM_CATEGORIES else "invalid",
        "probe_category": item.probe_category if item.probe_category in ALLOWED_AUDIT_PROBE_CATEGORIES else "invalid",
        "probe_summary_present": bool(item.probe_summary),
        "evidence_ref_count": len(item.evidence_refs),
        "provenance_ref_count": len(item.provenance_refs),
        "trace_ref_count": len(item.trace_refs),
        "operator_review_required": item.operator_review_required,
        "valid": not issues,
        "issue_count": len(issues),
        "redacted_count_only": True,
    }


def summarize_ai_audit_result(item: AIAuditResult | dict[str, Any]) -> dict[str, Any]:
    if isinstance(item, dict):
        item = ai_audit_result_from_dict(item)
    issues = validate_ai_audit_result(item)
    return {
        "schema_version": item.schema_version,
        "result_id_present": bool(item.result_id),
        "claim_id_present": bool(item.claim_id),
        "probe_id_present": bool(item.probe_id),
        "target_system_label_present": bool(item.target_system_label),
        "claim_category": item.claim_category if item.claim_category in ALLOWED_AUDIT_CLAIM_CATEGORIES else "invalid",
        "probe_category": item.probe_category if item.probe_category in ALLOWED_AUDIT_PROBE_CATEGORIES else "invalid",
        "result_label": item.result_label if item.result_label in ALLOWED_AUDIT_RESULT_LABELS else "invalid",
        "claim_text_summary_present": bool(item.claim_text_summary),
        "observed_behavior_summary_present": bool(item.observed_behavior_summary),
        "evidence_ref_count": len(item.evidence_refs),
        "provenance_ref_count": len(item.provenance_refs),
        "trace_ref_count": len(item.trace_refs),
        "confidence_band": _confidence_band(item.confidence),
        "internal_audit_score_present": item.internal_audit_score is not None,
        "score_label": item.score_label,
        "operator_review_required": item.operator_review_required,
        "valid": not issues,
        "issue_count": len(issues),
        "redacted_count_only": True,
    }


def summarize_ai_audit_results(items: list[AIAuditResult | dict[str, Any]]) -> dict[str, Any]:
    summaries = [summarize_ai_audit_result(item) for item in items]
    claim_category_counts: dict[str, int] = {}
    probe_category_counts: dict[str, int] = {}
    result_label_counts: dict[str, int] = {}
    valid_count = 0
    issue_count = 0
    evidence_ref_count = 0
    provenance_ref_count = 0
    trace_ref_count = 0
    score_count = 0
    for summary in summaries:
        claim = str(summary["claim_category"])
        probe = str(summary["probe_category"])
        label = str(summary["result_label"])
        claim_category_counts[claim] = claim_category_counts.get(claim, 0) + 1
        probe_category_counts[probe] = probe_category_counts.get(probe, 0) + 1
        result_label_counts[label] = result_label_counts.get(label, 0) + 1
        valid_count += 1 if summary["valid"] else 0
        issue_count += int(summary["issue_count"])
        evidence_ref_count += int(summary["evidence_ref_count"])
        provenance_ref_count += int(summary["provenance_ref_count"])
        trace_ref_count += int(summary["trace_ref_count"])
        score_count += 1 if summary["internal_audit_score_present"] else 0
    return {
        "result_count": len(summaries),
        "valid_count": valid_count,
        "invalid_count": len(summaries) - valid_count,
        "issue_count": issue_count,
        "claim_category_counts": claim_category_counts,
        "probe_category_counts": probe_category_counts,
        "result_label_counts": result_label_counts,
        "evidence_ref_count": evidence_ref_count,
        "provenance_ref_count": provenance_ref_count,
        "trace_ref_count": trace_ref_count,
        "internal_audit_score_count": score_count,
        "redacted_count_only": True,
        "protected_items_copied": False,
        "answer_keys_used": False,
        "official_score_claimed": False,
        "clinical_validity_claimed": False,
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


def create_ai_audit_claim_from_metadata(
    *,
    claim_id: str,
    target_system_label: str,
    claim_category: str = "unknown",
    claim_text_summary: str = "redacted claim summary",
    evidence_refs: list[str] | None = None,
    provenance_refs: list[str] | None = None,
    trace_refs: list[str] | None = None,
    operator_review_required: bool = True,
    recommended_follow_up: str = "operator review",
    safety_flags: AIAuditTestSafetyFlags | dict[str, Any] | None = None,
) -> AIAuditClaim:
    """Create a redacted AI-audit claim from explicit metadata only."""
    if isinstance(safety_flags, dict):
        safety_flags = ai_audit_safety_flags_from_dict(safety_flags)
    return AIAuditClaim(
        claim_id=claim_id,
        target_system_label=target_system_label,
        claim_category=claim_category,
        claim_text_summary=claim_text_summary,
        evidence_refs=list(evidence_refs or []),
        provenance_refs=list(provenance_refs or []),
        trace_refs=list(trace_refs or []),
        operator_review_required=operator_review_required,
        recommended_follow_up=recommended_follow_up,
        safety_flags=safety_flags or AIAuditTestSafetyFlags(),
    )


def create_ai_audit_probe_from_metadata(
    *,
    probe_id: str,
    target_system_label: str,
    claim_id: str = "",
    claim_category: str = "unknown",
    probe_category: str = "unknown",
    probe_summary: str = "redacted probe summary",
    evidence_refs: list[str] | None = None,
    provenance_refs: list[str] | None = None,
    trace_refs: list[str] | None = None,
    operator_review_required: bool = True,
    recommended_follow_up: str = "operator review",
    safety_flags: AIAuditTestSafetyFlags | dict[str, Any] | None = None,
) -> AIAuditProbe:
    """Create a redacted AI-audit probe from explicit metadata only."""
    if isinstance(safety_flags, dict):
        safety_flags = ai_audit_safety_flags_from_dict(safety_flags)
    return AIAuditProbe(
        probe_id=probe_id,
        target_system_label=target_system_label,
        claim_id=claim_id,
        claim_category=claim_category,
        probe_category=probe_category,
        probe_summary=probe_summary,
        evidence_refs=list(evidence_refs or []),
        provenance_refs=list(provenance_refs or []),
        trace_refs=list(trace_refs or []),
        operator_review_required=operator_review_required,
        recommended_follow_up=recommended_follow_up,
        safety_flags=safety_flags or AIAuditTestSafetyFlags(),
    )


def create_ai_audit_result_from_observation(
    *,
    result_id: str,
    claim_id: str,
    probe_id: str,
    target_system_label: str,
    claim_category: str = "unknown",
    probe_category: str = "unknown",
    result_label: str = "unknown",
    claim_text_summary: str = "redacted claim summary",
    observed_behavior_summary: str = "redacted observed behavior summary",
    evidence_boundary: str = "internal audit evidence only",
    evidence_refs: list[str] | None = None,
    provenance_refs: list[str] | None = None,
    trace_refs: list[str] | None = None,
    confidence: float = 0.0,
    internal_audit_score: float | None = None,
    operator_review_required: bool = True,
    recommended_follow_up: str = "operator review",
    safety_flags: AIAuditTestSafetyFlags | dict[str, Any] | None = None,
) -> AIAuditResult:
    """Create an internal/nonclinical/nonofficial audit result from explicit observation metadata."""
    if isinstance(safety_flags, dict):
        safety_flags = ai_audit_safety_flags_from_dict(safety_flags)
    flags = safety_flags or AIAuditTestSafetyFlags()
    refs = list(evidence_refs or [])
    prov = list(provenance_refs or [])
    traces = list(trace_refs or [])
    try:
        numeric_confidence = float(confidence)
    except (TypeError, ValueError):
        numeric_confidence = 0.0
    if _validate_safety_flags(flags):
        return create_blocked_ai_audit_result(
            result_id=result_id,
            claim_id=claim_id,
            probe_id=probe_id,
            target_system_label=target_system_label,
            claim_category=claim_category,
            probe_category=probe_category,
            blocked_reason="unsafe or prohibited audit condition",
            safety_flags=flags,
        )
    if result_label == "supported" and numeric_confidence >= HIGH_CONFIDENCE_THRESHOLD and (not refs or not prov or not traces):
        return create_blocked_ai_audit_result(
            result_id=result_id,
            claim_id=claim_id,
            probe_id=probe_id,
            target_system_label=target_system_label,
            claim_category=claim_category,
            probe_category=probe_category,
            blocked_reason="high-confidence supported result requires evidence/provenance/trace refs",
        )
    if claim_category == "scientific_capability_claim" and not evidence_boundary:
        return create_blocked_ai_audit_result(
            result_id=result_id,
            claim_id=claim_id,
            probe_id=probe_id,
            target_system_label=target_system_label,
            claim_category=claim_category,
            probe_category=probe_category,
            blocked_reason="scientific capability claim requires evidence boundary",
        )
    if claim_category == "model_authority_claim" and not prov:
        return create_blocked_ai_audit_result(
            result_id=result_id,
            claim_id=claim_id,
            probe_id=probe_id,
            target_system_label=target_system_label,
            claim_category=claim_category,
            probe_category=probe_category,
            blocked_reason="model authority claim requires provenance refs",
        )
    return AIAuditResult(
        result_id=result_id,
        claim_id=claim_id,
        probe_id=probe_id,
        target_system_label=target_system_label,
        claim_category=claim_category,
        probe_category=probe_category,
        result_label=result_label,
        claim_text_summary=claim_text_summary,
        observed_behavior_summary=observed_behavior_summary,
        evidence_boundary=evidence_boundary,
        evidence_refs=refs,
        provenance_refs=prov,
        trace_refs=traces,
        confidence=numeric_confidence,
        internal_audit_score=internal_audit_score,
        score_label="internal_nonclinical_nonofficial",
        operator_review_required=operator_review_required,
        recommended_follow_up=recommended_follow_up,
        safety_flags=flags,
    )


def create_blocked_ai_audit_result(
    *,
    result_id: str,
    claim_id: str,
    probe_id: str,
    target_system_label: str,
    claim_category: str = "unknown",
    probe_category: str = "unknown",
    blocked_reason: str = "unsafe or prohibited audit condition",
    safety_flags: AIAuditTestSafetyFlags | dict[str, Any] | None = None,
) -> AIAuditResult:
    """Create a safe unsafe_to_test result for blocked audit conditions."""
    if isinstance(safety_flags, dict):
        safety_flags = ai_audit_safety_flags_from_dict(safety_flags)
    return AIAuditResult(
        result_id=result_id,
        claim_id=claim_id,
        probe_id=probe_id,
        target_system_label=target_system_label,
        claim_category=claim_category if claim_category in ALLOWED_AUDIT_CLAIM_CATEGORIES else "unknown",
        probe_category=probe_category if probe_category in ALLOWED_AUDIT_PROBE_CATEGORIES else "unknown",
        result_label="unsafe_to_test",
        claim_text_summary="redacted blocked claim summary",
        observed_behavior_summary=blocked_reason or "unsafe or prohibited audit condition",
        evidence_boundary="blocked before evaluation; no official score or clinical claim",
        evidence_refs=[],
        provenance_refs=[],
        trace_refs=[],
        confidence=0.0,
        internal_audit_score=0.0,
        score_label="internal_nonclinical_nonofficial",
        operator_review_required=True,
        recommended_follow_up="operator review required before any implementation",
        safety_flags=safety_flags or AIAuditTestSafetyFlags(),
    )


def summarize_ai_audit_diagnostics(
    *,
    claims: list[AIAuditClaim | dict[str, Any]] | None = None,
    probes: list[AIAuditProbe | dict[str, Any]] | None = None,
    results: list[AIAuditResult | dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Summarize audit objects using redacted counts only."""
    claim_summaries = [summarize_ai_audit_claim(item) for item in list(claims or [])]
    probe_summaries = [summarize_ai_audit_probe(item) for item in list(probes or [])]
    result_summary = summarize_ai_audit_results(list(results or []))
    claim_category_counts: dict[str, int] = dict(result_summary["claim_category_counts"])
    probe_category_counts: dict[str, int] = dict(result_summary["probe_category_counts"])
    valid_claim_count = 0
    valid_probe_count = 0
    claim_issue_count = 0
    probe_issue_count = 0
    for summary in claim_summaries:
        category = str(summary["claim_category"])
        claim_category_counts[category] = claim_category_counts.get(category, 0) + 1
        valid_claim_count += 1 if summary["valid"] else 0
        claim_issue_count += int(summary["issue_count"])
    for summary in probe_summaries:
        category = str(summary["probe_category"])
        probe_category_counts[category] = probe_category_counts.get(category, 0) + 1
        valid_probe_count += 1 if summary["valid"] else 0
        probe_issue_count += int(summary["issue_count"])
    return {
        "claim_count": len(claim_summaries),
        "probe_count": len(probe_summaries),
        "result_count": result_summary["result_count"],
        "valid_claim_count": valid_claim_count,
        "valid_probe_count": valid_probe_count,
        "valid_result_count": result_summary["valid_count"],
        "invalid_claim_count": len(claim_summaries) - valid_claim_count,
        "invalid_probe_count": len(probe_summaries) - valid_probe_count,
        "invalid_result_count": result_summary["invalid_count"],
        "issue_count": claim_issue_count + probe_issue_count + int(result_summary["issue_count"]),
        "claim_category_counts": claim_category_counts,
        "probe_category_counts": probe_category_counts,
        "result_label_counts": result_summary["result_label_counts"],
        "redacted_count_only": True,
        "protected_items_copied": False,
        "answer_keys_used": False,
        "official_score_claimed": False,
        "clinical_validity_claimed": False,
        "benchmark_tuning_performed": False,
        "runtime_behavior_changed": False,
        "chat_behavior_changed": False,
        "voice_behavior_changed": False,
        "external_model_calls_performed": False,
        "advisor_calls_performed": False,
    }
