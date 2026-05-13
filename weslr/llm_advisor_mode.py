from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


ALLOWED_ADVISOR_PROVIDER_TYPES = {
    "openai",
    "openai_codex",
    "ollama",
    "openrouter",
    "github_copilot",
    "institution_owned",
    "local_private",
    "on_premise",
    "air_gapped",
    "domain_specific",
    "unknown",
}
ALLOWED_ADVISOR_DEPLOYMENT_TYPES = {"cloud", "local", "on_premise", "air_gapped", "hybrid", "unknown"}
ALLOWED_ADVISOR_TASK_TYPES = {
    "architecture_review",
    "failure_diagnosis",
    "style_review",
    "test_suggestion",
    "synthetic_example_suggestion",
    "reasoning_pattern_review",
    "gap_taxonomy_review",
    "wording_risk_review",
    "alternative_design_proposal",
    "provider_capability_review",
    "unknown",
}
ALLOWED_ADVISOR_OPERATOR_DECISIONS = {
    "pending_review",
    "accepted",
    "partially_accepted",
    "rejected",
    "deferred",
}


@dataclass
class AdvisorSafetyFlags:
    answer_selection_used: bool = False
    truth_authority_claimed: bool = False
    soundness_authority_claimed: bool = False
    official_score_claimed: bool = False
    answer_key_used: bool = False
    benchmark_specific_tuning_used: bool = False
    raw_benchmark_text_used: bool = False
    secrets_included: bool = False
    private_user_data_included: bool = False
    memory_mutation_requested: bool = False
    runtime_action_requested: bool = False
    governance_override_requested: bool = False
    model_internal_extraction_requested: bool = False


@dataclass
class AdvisorProviderRecord:
    provider_id: str = ""
    provider_type: str = "unknown"
    model_name: str = ""
    deployment_type: str = "unknown"
    institution_owner: str = ""
    allowed_tasks: list[str] = field(default_factory=list)
    forbidden_tasks: list[str] = field(default_factory=list)
    data_policy: str = "redacted_structural_default"
    redaction_policy: str = "redacted_by_default"
    audit_logging_required: bool = True
    operator_approval_required: bool = True


@dataclass
class AdvisorReviewRecord:
    schema_version: str = "1.0"
    advisor_review_id: str = ""
    advisor_model: str = ""
    advisor_provider: str = ""
    provider_record: AdvisorProviderRecord = field(default_factory=AdvisorProviderRecord)
    task_type: str = "unknown"
    input_summary_hash: str = ""
    input_redaction_level: str = "structural_summary_only"
    response_summary: str = ""
    recommendations: list[str] = field(default_factory=list)
    risks: list[str] = field(default_factory=list)
    disagreements: list[str] = field(default_factory=list)
    consensus_group: str = ""
    safety_flags: AdvisorSafetyFlags = field(default_factory=AdvisorSafetyFlags)
    operator_decision: str = "pending_review"
    accepted_items: list[str] = field(default_factory=list)
    rejected_items: list[str] = field(default_factory=list)
    created_tests: list[str] = field(default_factory=list)
    created_proposals: list[str] = field(default_factory=list)
    created_diagnostics: list[str] = field(default_factory=list)
    non_authoritative: bool = True
    requires_validation: bool = True
    requires_operator_review: bool = True
    not_runtime_truth: bool = True
    timestamp: str = ""


def _list_from_value(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value if str(item).strip()]
    if str(value).strip():
        return [str(value).strip()]
    return []


def create_empty_advisor_provider_record(**overrides: Any) -> AdvisorProviderRecord:
    record = AdvisorProviderRecord()
    for key, value in overrides.items():
        if hasattr(record, key):
            setattr(record, key, value)
    return record


def create_empty_advisor_review_record(**overrides: Any) -> AdvisorReviewRecord:
    record = AdvisorReviewRecord()
    for key, value in overrides.items():
        if hasattr(record, key):
            setattr(record, key, value)
    return record


def advisor_provider_record_to_dict(record: AdvisorProviderRecord) -> dict[str, Any]:
    return asdict(record)


def advisor_provider_record_from_dict(data: dict[str, Any]) -> AdvisorProviderRecord:
    return AdvisorProviderRecord(
        provider_id=str(data.get("provider_id", "") or ""),
        provider_type=str(data.get("provider_type", "unknown") or "unknown"),
        model_name=str(data.get("model_name", "") or ""),
        deployment_type=str(data.get("deployment_type", "unknown") or "unknown"),
        institution_owner=str(data.get("institution_owner", "") or ""),
        allowed_tasks=_list_from_value(data.get("allowed_tasks", [])),
        forbidden_tasks=_list_from_value(data.get("forbidden_tasks", [])),
        data_policy=str(data.get("data_policy", "redacted_structural_default") or "redacted_structural_default"),
        redaction_policy=str(data.get("redaction_policy", "redacted_by_default") or "redacted_by_default"),
        audit_logging_required=bool(data.get("audit_logging_required", True)),
        operator_approval_required=bool(data.get("operator_approval_required", True)),
    )


def _advisor_safety_flags_from_dict(data: dict[str, Any]) -> AdvisorSafetyFlags:
    return AdvisorSafetyFlags(
        answer_selection_used=bool(data.get("answer_selection_used", False)),
        truth_authority_claimed=bool(data.get("truth_authority_claimed", False)),
        soundness_authority_claimed=bool(data.get("soundness_authority_claimed", False)),
        official_score_claimed=bool(data.get("official_score_claimed", False)),
        answer_key_used=bool(data.get("answer_key_used", False)),
        benchmark_specific_tuning_used=bool(data.get("benchmark_specific_tuning_used", False)),
        raw_benchmark_text_used=bool(data.get("raw_benchmark_text_used", False)),
        secrets_included=bool(data.get("secrets_included", False)),
        private_user_data_included=bool(data.get("private_user_data_included", False)),
        memory_mutation_requested=bool(data.get("memory_mutation_requested", False)),
        runtime_action_requested=bool(data.get("runtime_action_requested", False)),
        governance_override_requested=bool(data.get("governance_override_requested", False)),
        model_internal_extraction_requested=bool(data.get("model_internal_extraction_requested", False)),
    )


def advisor_review_record_to_dict(record: AdvisorReviewRecord) -> dict[str, Any]:
    return asdict(record)


def advisor_review_record_from_dict(data: dict[str, Any]) -> AdvisorReviewRecord:
    provider_source = data.get("provider_record", {})
    provider_record = provider_source if isinstance(provider_source, AdvisorProviderRecord) else advisor_provider_record_from_dict(provider_source if isinstance(provider_source, dict) else {})
    flags_source = data.get("safety_flags", {})
    safety_flags = flags_source if isinstance(flags_source, AdvisorSafetyFlags) else _advisor_safety_flags_from_dict(flags_source if isinstance(flags_source, dict) else {})
    return AdvisorReviewRecord(
        schema_version=str(data.get("schema_version", "1.0") or "1.0"),
        advisor_review_id=str(data.get("advisor_review_id", "") or ""),
        advisor_model=str(data.get("advisor_model", "") or ""),
        advisor_provider=str(data.get("advisor_provider", "") or ""),
        provider_record=provider_record,
        task_type=str(data.get("task_type", "unknown") or "unknown"),
        input_summary_hash=str(data.get("input_summary_hash", "") or ""),
        input_redaction_level=str(data.get("input_redaction_level", "structural_summary_only") or "structural_summary_only"),
        response_summary=str(data.get("response_summary", "") or ""),
        recommendations=_list_from_value(data.get("recommendations", [])),
        risks=_list_from_value(data.get("risks", [])),
        disagreements=_list_from_value(data.get("disagreements", [])),
        consensus_group=str(data.get("consensus_group", "") or ""),
        safety_flags=safety_flags,
        operator_decision=str(data.get("operator_decision", "pending_review") or "pending_review"),
        accepted_items=_list_from_value(data.get("accepted_items", [])),
        rejected_items=_list_from_value(data.get("rejected_items", [])),
        created_tests=_list_from_value(data.get("created_tests", [])),
        created_proposals=_list_from_value(data.get("created_proposals", [])),
        created_diagnostics=_list_from_value(data.get("created_diagnostics", [])),
        non_authoritative=bool(data.get("non_authoritative", True)),
        requires_validation=bool(data.get("requires_validation", True)),
        requires_operator_review=bool(data.get("requires_operator_review", True)),
        not_runtime_truth=bool(data.get("not_runtime_truth", True)),
        timestamp=str(data.get("timestamp", "") or ""),
    )


def validate_advisor_provider_record(record: AdvisorProviderRecord) -> list[str]:
    messages: list[str] = []
    if record.provider_type not in ALLOWED_ADVISOR_PROVIDER_TYPES:
        messages.append("invalid provider type")
    if record.deployment_type not in ALLOWED_ADVISOR_DEPLOYMENT_TYPES:
        messages.append("invalid deployment type")
    if not record.audit_logging_required:
        messages.append("audit logging required")
    if not record.operator_approval_required:
        messages.append("operator approval required")
    for task in record.allowed_tasks:
        if task not in ALLOWED_ADVISOR_TASK_TYPES:
            messages.append("invalid allowed task type")
            break
    return messages


def validate_advisor_review_record(record: AdvisorReviewRecord) -> list[str]:
    messages: list[str] = []
    if not record.advisor_review_id.strip():
        messages.append("missing advisor review id")
    if not record.advisor_model.strip():
        messages.append("missing advisor model")
    if not record.advisor_provider.strip():
        messages.append("missing advisor provider")
    messages.extend(validate_advisor_provider_record(record.provider_record))
    if record.task_type not in ALLOWED_ADVISOR_TASK_TYPES:
        messages.append("invalid task type")
    if record.operator_decision not in ALLOWED_ADVISOR_OPERATOR_DECISIONS:
        messages.append("invalid operator decision")
    if not record.non_authoritative:
        messages.append("non_authoritative false")
    if not record.requires_validation:
        messages.append("requires_validation false")
    if not record.requires_operator_review:
        messages.append("requires_operator_review false")
    if not record.not_runtime_truth:
        messages.append("not_runtime_truth false")
    flags = record.safety_flags
    if flags.answer_selection_used:
        messages.append("answer selection used")
    if flags.truth_authority_claimed:
        messages.append("truth authority claimed")
    if flags.soundness_authority_claimed:
        messages.append("soundness authority claimed")
    if flags.official_score_claimed:
        messages.append("official score claimed")
    if flags.answer_key_used:
        messages.append("answer key used")
    if flags.benchmark_specific_tuning_used:
        messages.append("benchmark-specific tuning used")
    if flags.raw_benchmark_text_used:
        messages.append("raw benchmark text used")
    if flags.secrets_included:
        messages.append("secrets included")
    if flags.private_user_data_included:
        messages.append("private user data included")
    if flags.memory_mutation_requested:
        messages.append("memory mutation requested")
    if flags.runtime_action_requested:
        messages.append("runtime action requested")
    if flags.governance_override_requested:
        messages.append("governance override requested")
    if flags.model_internal_extraction_requested:
        messages.append("model internal extraction requested")
    return messages


def summarize_advisor_review_record(record: AdvisorReviewRecord) -> dict[str, Any]:
    validation_messages = validate_advisor_review_record(record)
    return {
        "schema_version": record.schema_version,
        "advisor_review_id": record.advisor_review_id,
        "provider_type": record.provider_record.provider_type,
        "deployment_type": record.provider_record.deployment_type,
        "task_type": record.task_type,
        "input_redaction_level": record.input_redaction_level,
        "recommendation_count": len(record.recommendations),
        "risk_count": len(record.risks),
        "disagreement_count": len(record.disagreements),
        "accepted_item_count": len(record.accepted_items),
        "rejected_item_count": len(record.rejected_items),
        "created_test_count": len(record.created_tests),
        "created_proposal_count": len(record.created_proposals),
        "created_diagnostic_count": len(record.created_diagnostics),
        "operator_decision": record.operator_decision,
        "non_authoritative": record.non_authoritative,
        "requires_validation": record.requires_validation,
        "requires_operator_review": record.requires_operator_review,
        "not_runtime_truth": record.not_runtime_truth,
        "safety_flag_count": sum(1 for value in asdict(record.safety_flags).values() if bool(value)),
        "validation_error_count": len(validation_messages),
        "valid": not validation_messages,
    }
