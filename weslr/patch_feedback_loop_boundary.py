"""Metadata-only patch feedback loop boundary v1.

This module converts validation failures into bounded patch-proposal metadata.
It is deterministic, import-safe, pure in-memory, and fail-closed.
No subprocess. No shell execution. No test execution. No file I/O.
No model/provider/API calls. No runtime wiring. No `.weslr` access.
No patch application, commit, push, or public/proof claims.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass, replace
from typing import Any, Iterable, Mapping

HELPER_TYPE_V1 = "patch_feedback_loop_boundary_v1"
PACKET_TYPE_V1 = "patch_feedback_packet_v1"
SUMMARY_TYPE_V1 = "patch_feedback_summary_v1"

ALLOWED_FAILURE_CLASSES_V1 = {
    "syntax_failure",
    "unit_test_failure",
    "focused_test_failure",
    "integration_test_failure",
    "release_gate_failure",
    "release_check_failure",
    "static_analysis_warning",
    "manifest_missing",
    "manifest_mismatch",
    "protected_file_diff",
    "secret_risk",
    "network_policy_block",
    "write_policy_block",
    "provenance_missing",
    "rollback_plan_missing",
    "unknown_validation_failure",
}

ALLOWED_PROPOSAL_TYPES_V1 = {
    "no_patch_needed",
    "metadata_fix_proposal",
    "test_fix_proposal",
    "source_fix_proposal",
    "manifest_fix_proposal",
    "docs_fix_proposal",
    "policy_fix_proposal",
    "rollback_proposal",
    "defer_to_owner_review",
    "defer_to_operator_review",
    "blocked_no_safe_patch",
    "unknown_patch_proposal",
}

ALLOWED_PROPOSAL_STATUSES_V1 = {
    "not_attempted",
    "proposal_created",
    "proposal_blocked",
    "proposal_needs_owner_review",
    "proposal_needs_operator_review",
    "retry_budget_available",
    "retry_budget_exhausted",
    "rollback_required",
    "blocked_protected_file",
    "blocked_secret_risk",
    "blocked_network_policy",
    "blocked_write_policy",
    "blocked_missing_rollback",
    "blocked_missing_provenance",
    "unknown_status",
}

ALLOWED_CLEAR_STATUSES_V1 = {"clear", "present", "not_detected", "not_required", "allowed", "review_required"}
ALLOWED_BLOCKED_STATUSES_V1 = {"blocked"}
ALLOWED_PROVENANCE_STATUSES_V1 = {"present", "missing", "blocked", "unknown_status"}

FORBIDDEN_FIELD_HINTS_V1 = (
    "hidden_prompt",
    "raw_private",
    "private_data",
    "raw_prompt",
    "raw_answer",
    "raw_response",
    "secret_token",
    "secret_key",
    "api_key",
    "token",
    "credential",
    "password",
)

FORBIDDEN_CLAIM_PHRASES_V1 = (
    "proof",
    "correctness",
    "public readiness",
    "security certification",
    "certification",
    "public claim",
    "public_readiness",
    "runtime authority",
    "model authority",
    "tool execution authority",
    "learning claim",
    "autonomous learning",
    "energy savings guarantee",
    "prediction certainty",
    "agi",
    "consciousness",
    "sentience",
    "turing",
)


class ValidationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class PatchFeedbackPacket:
    patch_feedback_packet_id: str
    validation_packet_ref: str
    candidate_source_ref: str
    artifact_provenance_ref: str
    file_manifest_ref: str
    failure_class: str
    failed_check_refs: tuple[str, ...]
    warning_refs: tuple[str, ...]
    proposal_type: str
    proposal_status: str
    proposal_summary: str
    affected_path_summaries: tuple[str, ...]
    protected_file_status: str
    secret_risk_status: str
    network_policy_status: str
    write_policy_status: str
    provenance_status: str
    retry_count: int
    max_retries: int
    retry_allowed: bool
    repeated_failure_detected: bool
    rollback_required: bool
    rollback_plan_ref: str
    owner_review_required: bool
    operator_review_required: bool
    patch_apply_allowed: bool
    commit_allowed: bool
    push_allowed: bool
    validation_rerun_required: bool
    artifact_export_allowed: bool
    tool_execution_allowed: bool
    public_claim_allowed: bool
    proof_claim_allowed: bool
    recommended_next_check: str
    runtime_authority: bool
    writes_state: bool
    model_provider_used: bool
    learning_claimed: bool
    safe_metadata: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class PatchFeedbackSummary:
    summary_type: str
    patch_feedback_packet_id: str
    validation_packet_ref: str
    failure_class: str
    proposal_type: str
    proposal_status: str
    retry_count: int
    max_retries: int
    retry_allowed: bool
    repeated_failure_detected: bool
    rollback_required: bool
    owner_review_required: bool
    operator_review_required: bool
    patch_apply_allowed: bool
    commit_allowed: bool
    push_allowed: bool
    validation_rerun_required: bool
    artifact_export_allowed: bool
    tool_execution_allowed: bool
    public_claim_allowed: bool
    proof_claim_allowed: bool
    runtime_authority: bool
    writes_state: bool
    model_provider_used: bool
    learning_claimed: bool
    proposal_summary: str
    affected_path_summaries: tuple[str, ...]
    recommended_next_check: str


# ---------------------------------------------------------------------------
# Safe coercion helpers
# ---------------------------------------------------------------------------


def _safe_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (str, int, float)):
        return str(value).strip()
    return default if value == "" else str(value).strip()


def _safe_bool(value: Any) -> bool:
    return bool(value) is True


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _safe_tuple(value: Any) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, tuple):
        return tuple(_safe_text(item) for item in value)
    if isinstance(value, list):
        return tuple(_safe_text(item) for item in value)
    if isinstance(value, set):
        return tuple(_safe_text(item) for item in sorted(value, key=_safe_text))
    return (_safe_text(value),)


def _safe_mapping(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, Mapping):
        return { _safe_text(key): to_patch_feedback_json_safe_v1(item) for key, item in value.items() }
    return {"value": to_patch_feedback_json_safe_v1(value)}


def _json_sort_key(value: Any) -> tuple[str, str]:
    return (type(value).__name__, repr(value))


def to_patch_feedback_json_safe_v1(value: Any) -> Any:
    if is_dataclass(value):
        value = asdict(value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return {
            _safe_text(key): to_patch_feedback_json_safe_v1(item)
            for key, item in sorted(value.items(), key=lambda item: _safe_text(item[0]))
        }
    if isinstance(value, tuple):
        return [to_patch_feedback_json_safe_v1(item) for item in value]
    if isinstance(value, list):
        return [to_patch_feedback_json_safe_v1(item) for item in value]
    if isinstance(value, set):
        items = [to_patch_feedback_json_safe_v1(item) for item in value]
        return sorted(items, key=_json_sort_key)
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return to_patch_feedback_json_safe_v1(value.to_dict())
    if hasattr(value, "__dict__"):
        return to_patch_feedback_json_safe_v1(vars(value))
    return _safe_text(value)


def _normalize_text(value: Any) -> str:
    return " ".join(_safe_text(value).split()).lower()


def _contains_forbidden_field(value: Any) -> str:
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = _normalize_text(key)
            if any(hint in key_text for hint in FORBIDDEN_FIELD_HINTS_V1):
                return key_text
            nested = _contains_forbidden_field(item)
            if nested:
                return nested
    elif isinstance(value, (list, tuple, set)):
        for item in value:
            nested = _contains_forbidden_field(item)
            if nested:
                return nested
    return ""


def _contains_forbidden_claim_marker(value: Any) -> bool:
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = _normalize_text(key)
            if key_text in {"safe_metadata", "proposal_summary", "recommended_next_check"} or key_text.endswith("_metadata"):
                if _contains_forbidden_claim_marker(item):
                    return True
        return False
    if isinstance(value, (list, tuple, set)):
        return any(_contains_forbidden_claim_marker(item) for item in value)
    blob = _normalize_text(value)
    if not blob:
        return False
    return any(phrase in blob for phrase in FORBIDDEN_CLAIM_PHRASES_V1)


def _safe_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, Mapping):
        items = list(value.keys())
    elif isinstance(value, (list, tuple, set)):
        items = list(value)
    else:
        items = [value]
    out: list[str] = []
    seen: set[str] = set()
    for item in items:
        text = _safe_text(item)
        if text and text not in seen:
            out.append(text)
            seen.add(text)
    return out


def _packet_like(value: Any) -> PatchFeedbackPacket:
    if isinstance(value, PatchFeedbackPacket):
        return value
    if not isinstance(value, Mapping):
        value = asdict(value) if is_dataclass(value) else {}
    safe_metadata = value.get("safe_metadata", None)
    if safe_metadata is not None and not isinstance(safe_metadata, Mapping):
        safe_metadata = {"value": safe_metadata}
    return PatchFeedbackPacket(
        patch_feedback_packet_id=_safe_text(value.get("patch_feedback_packet_id")),
        validation_packet_ref=_safe_text(value.get("validation_packet_ref")),
        candidate_source_ref=_safe_text(value.get("candidate_source_ref")),
        artifact_provenance_ref=_safe_text(value.get("artifact_provenance_ref")),
        file_manifest_ref=_safe_text(value.get("file_manifest_ref")),
        failure_class=_safe_text(value.get("failure_class")),
        failed_check_refs=_safe_tuple(value.get("failed_check_refs")),
        warning_refs=_safe_tuple(value.get("warning_refs")),
        proposal_type=_safe_text(value.get("proposal_type")),
        proposal_status=_safe_text(value.get("proposal_status")),
        proposal_summary=_safe_text(value.get("proposal_summary")),
        affected_path_summaries=_safe_tuple(value.get("affected_path_summaries")),
        protected_file_status=_safe_text(value.get("protected_file_status")),
        secret_risk_status=_safe_text(value.get("secret_risk_status")),
        network_policy_status=_safe_text(value.get("network_policy_status")),
        write_policy_status=_safe_text(value.get("write_policy_status")),
        provenance_status=_safe_text(value.get("provenance_status")),
        retry_count=_safe_int(value.get("retry_count", 0)),
        max_retries=_safe_int(value.get("max_retries", 0)),
        retry_allowed=_safe_bool(value.get("retry_allowed")),
        repeated_failure_detected=_safe_bool(value.get("repeated_failure_detected")),
        rollback_required=_safe_bool(value.get("rollback_required")),
        rollback_plan_ref=_safe_text(value.get("rollback_plan_ref")),
        owner_review_required=_safe_bool(value.get("owner_review_required")),
        operator_review_required=_safe_bool(value.get("operator_review_required")),
        patch_apply_allowed=_safe_bool(value.get("patch_apply_allowed")),
        commit_allowed=_safe_bool(value.get("commit_allowed")),
        push_allowed=_safe_bool(value.get("push_allowed")),
        validation_rerun_required=_safe_bool(value.get("validation_rerun_required")),
        artifact_export_allowed=_safe_bool(value.get("artifact_export_allowed")),
        tool_execution_allowed=_safe_bool(value.get("tool_execution_allowed")),
        public_claim_allowed=_safe_bool(value.get("public_claim_allowed")),
        proof_claim_allowed=_safe_bool(value.get("proof_claim_allowed")),
        recommended_next_check=_safe_text(value.get("recommended_next_check")),
        runtime_authority=_safe_bool(value.get("runtime_authority")),
        writes_state=_safe_bool(value.get("writes_state")),
        model_provider_used=_safe_bool(value.get("model_provider_used")),
        learning_claimed=_safe_bool(value.get("learning_claimed")),
        safe_metadata=dict(safe_metadata or {}),
    )


def _clone_packet(packet: PatchFeedbackPacket | Mapping[str, Any], **changes: Any) -> PatchFeedbackPacket:
    data = to_patch_feedback_json_safe_v1(packet)
    data.update(changes)
    if "failed_check_refs" in data:
        data["failed_check_refs"] = _safe_tuple(data["failed_check_refs"])
    if "warning_refs" in data:
        data["warning_refs"] = _safe_tuple(data["warning_refs"])
    if "affected_path_summaries" in data:
        data["affected_path_summaries"] = _safe_tuple(data["affected_path_summaries"])
    if data.get("safe_metadata") is not None and not isinstance(data.get("safe_metadata"), Mapping):
        data["safe_metadata"] = {"value": data["safe_metadata"]}
    return PatchFeedbackPacket(**data)


# ---------------------------------------------------------------------------
# Classification helpers
# ---------------------------------------------------------------------------


def classify_patch_failure_v1(
    *,
    failure_class: str | None = None,
    failed_check_refs: Iterable[str] | None = None,
    warning_refs: Iterable[str] | None = None,
    affected_path_summaries: Iterable[str] | None = None,
    safe_metadata: Mapping[str, Any] | None = None,
) -> str:
    candidate = _safe_text(failure_class).strip().lower()
    if candidate in ALLOWED_FAILURE_CLASSES_V1:
        return candidate

    probe = " ".join(
        [
            _safe_text(failure_class),
            " ".join(_safe_list(failed_check_refs)),
            " ".join(_safe_list(warning_refs)),
            " ".join(_safe_list(affected_path_summaries)),
            " ".join(_safe_list((safe_metadata or {}).values() if isinstance(safe_metadata, Mapping) else [])),
        ]
    ).lower()
    if "syntax" in probe:
        return "syntax_failure"
    if "unit" in probe and "test" in probe:
        return "unit_test_failure"
    if "focused" in probe and "test" in probe:
        return "focused_test_failure"
    if "integration" in probe and "test" in probe:
        return "integration_test_failure"
    if "release gate" in probe or "release_gate" in probe:
        return "release_gate_failure"
    if "release check" in probe or "release_check" in probe:
        return "release_check_failure"
    if "static analysis" in probe or "warning" in probe:
        return "static_analysis_warning"
    if "manifest mismatch" in probe:
        return "manifest_mismatch"
    if "manifest" in probe:
        return "manifest_missing"
    if "protected file" in probe:
        return "protected_file_diff"
    if "secret" in probe or "api key" in probe or "token" in probe:
        return "secret_risk"
    if "network" in probe:
        return "network_policy_block"
    if "write policy" in probe or "write" in probe:
        return "write_policy_block"
    if "provenance" in probe:
        return "provenance_missing"
    if "rollback" in probe:
        return "rollback_plan_missing"
    return "unknown_validation_failure"


def _normal_status(value: Any, *, allowed: set[str], default: str) -> str:
    candidate = _safe_text(value).strip().lower()
    return candidate if candidate in allowed else default


def _proposal_summary_for(failure_class: str, proposal_type: str, proposal_status: str, safe_metadata: Mapping[str, Any] | None = None) -> str:
    meta_hint = ""
    if isinstance(safe_metadata, Mapping):
        meta_hint = _safe_text(safe_metadata.get("summary_hint") or safe_metadata.get("example_name"))
    base = {
        "syntax_failure": "syntax_failure_metadata_only_patch_proposal",
        "unit_test_failure": "unit_test_failure_source_fix_proposal",
        "focused_test_failure": "focused_test_failure_test_fix_proposal",
        "integration_test_failure": "integration_test_failure_source_fix_proposal",
        "release_gate_failure": "release_gate_failure_validation_rerun_required",
        "release_check_failure": "release_check_failure_validation_rerun_or_no_patch_needed",
        "static_analysis_warning": "static_analysis_warning_docs_or_metadata_fix_proposal",
        "manifest_missing": "manifest_missing_manifest_fix_proposal",
        "manifest_mismatch": "manifest_mismatch_manifest_fix_proposal",
        "protected_file_diff": "protected_file_diff_owner_operator_review_required",
        "secret_risk": "secret_risk_blocked_no_safe_patch",
        "network_policy_block": "network_policy_block_policy_review_required",
        "write_policy_block": "write_policy_block_no_patch_application",
        "provenance_missing": "provenance_missing_blocks_promotion",
        "rollback_plan_missing": "rollback_plan_missing_rollback_proposal",
        "unknown_validation_failure": "unknown_validation_failure_blocked",
    }.get(failure_class, "patch_feedback_metadata_only")
    if meta_hint:
        return f"{base}:{meta_hint}:{proposal_type}:{proposal_status}"
    return f"{base}:{proposal_type}:{proposal_status}"


def _default_next_check(proposal_type: str, proposal_status: str) -> str:
    if proposal_type == "no_patch_needed":
        return "no_action_needed"
    if proposal_status in {"blocked_secret_risk", "blocked_write_policy", "blocked_network_policy", "blocked_protected_file", "blocked_missing_provenance", "blocked_missing_rollback"}:
        return "owner_operator_review_required"
    if proposal_status == "retry_budget_exhausted":
        return "stop_retry_and_review"
    if proposal_status == "rollback_required":
        return "prepare_rollback_review"
    if proposal_status == "proposal_needs_owner_review":
        return "owner_review_required"
    if proposal_status == "proposal_needs_operator_review":
        return "operator_review_required"
    if proposal_status == "retry_budget_available":
        return "bounded_retry_possible"
    return "review_patch_feedback_metadata"


# ---------------------------------------------------------------------------
# Public APIs
# ---------------------------------------------------------------------------


def build_patch_feedback_packet_v1(**kwargs: Any) -> PatchFeedbackPacket:
    failure_class = classify_patch_failure_v1(
        failure_class=kwargs.get("failure_class"),
        failed_check_refs=kwargs.get("failed_check_refs"),
        warning_refs=kwargs.get("warning_refs"),
        affected_path_summaries=kwargs.get("affected_path_summaries"),
        safe_metadata=kwargs.get("safe_metadata"),
    )
    packet = PatchFeedbackPacket(
        patch_feedback_packet_id=_safe_text(kwargs.get("patch_feedback_packet_id")),
        validation_packet_ref=_safe_text(kwargs.get("validation_packet_ref")),
        candidate_source_ref=_safe_text(kwargs.get("candidate_source_ref")),
        artifact_provenance_ref=_safe_text(kwargs.get("artifact_provenance_ref")),
        file_manifest_ref=_safe_text(kwargs.get("file_manifest_ref")),
        failure_class=failure_class,
        failed_check_refs=_safe_tuple(kwargs.get("failed_check_refs")),
        warning_refs=_safe_tuple(kwargs.get("warning_refs")),
        proposal_type=_safe_text(kwargs.get("proposal_type", "unknown_patch_proposal")).strip().lower(),
        proposal_status=_safe_text(kwargs.get("proposal_status", "not_attempted")).strip().lower(),
        proposal_summary=_safe_text(kwargs.get("proposal_summary")),
        affected_path_summaries=_safe_tuple(kwargs.get("affected_path_summaries")),
        protected_file_status=_normal_status(kwargs.get("protected_file_status", "clear"), allowed=ALLOWED_CLEAR_STATUSES_V1 | ALLOWED_BLOCKED_STATUSES_V1, default="unknown_status"),
        secret_risk_status=_normal_status(kwargs.get("secret_risk_status", "not_detected"), allowed=ALLOWED_CLEAR_STATUSES_V1 | ALLOWED_BLOCKED_STATUSES_V1, default="unknown_status"),
        network_policy_status=_normal_status(kwargs.get("network_policy_status", "not_required"), allowed=ALLOWED_CLEAR_STATUSES_V1 | ALLOWED_BLOCKED_STATUSES_V1, default="unknown_status"),
        write_policy_status=_normal_status(kwargs.get("write_policy_status", "not_required"), allowed=ALLOWED_CLEAR_STATUSES_V1 | ALLOWED_BLOCKED_STATUSES_V1, default="unknown_status"),
        provenance_status=_normal_status(kwargs.get("provenance_status", "present"), allowed=ALLOWED_PROVENANCE_STATUSES_V1, default="unknown_status"),
        retry_count=_safe_int(kwargs.get("retry_count", 0)),
        max_retries=_safe_int(kwargs.get("max_retries", 0)),
        retry_allowed=_safe_bool(kwargs.get("retry_allowed", False)),
        repeated_failure_detected=_safe_bool(kwargs.get("repeated_failure_detected", False)),
        rollback_required=_safe_bool(kwargs.get("rollback_required", False)),
        rollback_plan_ref=_safe_text(kwargs.get("rollback_plan_ref")),
        owner_review_required=_safe_bool(kwargs.get("owner_review_required", False)),
        operator_review_required=_safe_bool(kwargs.get("operator_review_required", False)),
        patch_apply_allowed=_safe_bool(kwargs.get("patch_apply_allowed", False)),
        commit_allowed=_safe_bool(kwargs.get("commit_allowed", False)),
        push_allowed=_safe_bool(kwargs.get("push_allowed", False)),
        validation_rerun_required=_safe_bool(kwargs.get("validation_rerun_required", True)),
        artifact_export_allowed=_safe_bool(kwargs.get("artifact_export_allowed", False)),
        tool_execution_allowed=_safe_bool(kwargs.get("tool_execution_allowed", False)),
        public_claim_allowed=_safe_bool(kwargs.get("public_claim_allowed", False)),
        proof_claim_allowed=_safe_bool(kwargs.get("proof_claim_allowed", False)),
        recommended_next_check=_safe_text(kwargs.get("recommended_next_check", "review_patch_feedback_metadata")),
        runtime_authority=_safe_bool(kwargs.get("runtime_authority", False)),
        writes_state=_safe_bool(kwargs.get("writes_state", False)),
        model_provider_used=_safe_bool(kwargs.get("model_provider_used", False)),
        learning_claimed=_safe_bool(kwargs.get("learning_claimed", False)),
        safe_metadata=_safe_mapping(kwargs.get("safe_metadata")),
    )
    selected = select_patch_proposal_v1(packet)
    evaluated = evaluate_patch_retry_budget_v1(selected)
    return evaluated


def select_patch_proposal_v1(packet: Any) -> PatchFeedbackPacket:
    current = _packet_like(packet)
    failure_class = classify_patch_failure_v1(
        failure_class=current.failure_class,
        failed_check_refs=current.failed_check_refs,
        warning_refs=current.warning_refs,
        affected_path_summaries=current.affected_path_summaries,
        safe_metadata=current.safe_metadata,
    )
    safe_metadata = current.safe_metadata or {}
    validation_result = _normalize_text(safe_metadata.get("validation_result")) if isinstance(safe_metadata, Mapping) else ""
    if failure_class == "unknown_validation_failure":
        proposal_type = "unknown_patch_proposal"
        proposal_status = "proposal_blocked"
        owner_review_required = False
        operator_review_required = False
        rollback_required = False
    elif failure_class == "secret_risk" or _normal_status(current.secret_risk_status, allowed=ALLOWED_CLEAR_STATUSES_V1 | ALLOWED_BLOCKED_STATUSES_V1, default="unknown_status") == "blocked":
        proposal_type = "blocked_no_safe_patch"
        proposal_status = "blocked_secret_risk"
        owner_review_required = True
        operator_review_required = True
        rollback_required = False
    elif failure_class == "write_policy_block" or _normal_status(current.write_policy_status, allowed=ALLOWED_CLEAR_STATUSES_V1 | ALLOWED_BLOCKED_STATUSES_V1, default="unknown_status") == "blocked":
        proposal_type = "blocked_no_safe_patch"
        proposal_status = "blocked_write_policy"
        owner_review_required = True
        operator_review_required = True
        rollback_required = False
    elif failure_class == "network_policy_block" or _normal_status(current.network_policy_status, allowed=ALLOWED_CLEAR_STATUSES_V1 | ALLOWED_BLOCKED_STATUSES_V1, default="unknown_status") == "blocked":
        proposal_type = "policy_fix_proposal"
        proposal_status = "blocked_network_policy"
        owner_review_required = True
        operator_review_required = True
        rollback_required = False
    elif failure_class == "protected_file_diff" or _normal_status(current.protected_file_status, allowed=ALLOWED_CLEAR_STATUSES_V1 | ALLOWED_BLOCKED_STATUSES_V1, default="unknown_status") == "blocked":
        proposal_type = "defer_to_operator_review"
        proposal_status = "blocked_protected_file"
        owner_review_required = True
        operator_review_required = True
        rollback_required = False
    elif failure_class == "provenance_missing" or _normal_status(current.provenance_status, allowed=ALLOWED_PROVENANCE_STATUSES_V1, default="unknown_status") == "missing":
        proposal_type = "defer_to_owner_review"
        proposal_status = "blocked_missing_provenance"
        owner_review_required = True
        operator_review_required = True
        rollback_required = False
    elif failure_class == "rollback_plan_missing":
        proposal_type = "rollback_proposal"
        proposal_status = "blocked_missing_rollback"
        owner_review_required = True
        operator_review_required = True
        rollback_required = True
    elif failure_class == "manifest_missing" or failure_class == "manifest_mismatch" or not current.file_manifest_ref:
        proposal_type = "manifest_fix_proposal"
        proposal_status = "proposal_created"
        owner_review_required = current.owner_review_required
        operator_review_required = current.operator_review_required
        rollback_required = False
    elif failure_class == "syntax_failure":
        proposal_type = "metadata_fix_proposal"
        proposal_status = "proposal_created"
        owner_review_required = current.owner_review_required
        operator_review_required = current.operator_review_required
        rollback_required = False
    elif failure_class == "unit_test_failure":
        proposal_type = "source_fix_proposal"
        proposal_status = "proposal_created"
        owner_review_required = current.owner_review_required
        operator_review_required = current.operator_review_required
        rollback_required = False
    elif failure_class == "focused_test_failure":
        proposal_type = "test_fix_proposal"
        proposal_status = "proposal_created"
        owner_review_required = current.owner_review_required
        operator_review_required = current.operator_review_required
        rollback_required = False
    elif failure_class == "integration_test_failure":
        proposal_type = "source_fix_proposal"
        proposal_status = "proposal_created"
        owner_review_required = current.owner_review_required
        operator_review_required = current.operator_review_required
        rollback_required = False
    elif failure_class == "release_gate_failure":
        proposal_type = "defer_to_operator_review"
        proposal_status = "proposal_needs_operator_review"
        owner_review_required = True
        operator_review_required = True
        rollback_required = False
    elif failure_class == "release_check_failure" and validation_result == "passed":
        proposal_type = "no_patch_needed"
        proposal_status = "not_attempted"
        owner_review_required = False
        operator_review_required = False
        rollback_required = False
    elif failure_class == "release_check_failure":
        proposal_type = "defer_to_operator_review"
        proposal_status = "proposal_needs_operator_review"
        owner_review_required = True
        operator_review_required = True
        rollback_required = False
    elif failure_class == "static_analysis_warning":
        proposal_type = "docs_fix_proposal"
        proposal_status = "proposal_created"
        owner_review_required = current.owner_review_required
        operator_review_required = current.operator_review_required
        rollback_required = False
    else:
        proposal_type = "unknown_patch_proposal"
        proposal_status = "proposal_blocked"
        owner_review_required = False
        operator_review_required = False
        rollback_required = False

    proposal_summary = _proposal_summary_for(failure_class, proposal_type, proposal_status, safe_metadata)
    recommended_next_check = _default_next_check(proposal_type, proposal_status)

    return replace(
        current,
        failure_class=failure_class,
        proposal_type=proposal_type,
        proposal_status=proposal_status,
        proposal_summary=proposal_summary,
        owner_review_required=owner_review_required,
        operator_review_required=operator_review_required,
        rollback_required=rollback_required or current.rollback_required,
        recommended_next_check=recommended_next_check,
        patch_apply_allowed=False,
        commit_allowed=False,
        push_allowed=False,
        validation_rerun_required=(proposal_type != "no_patch_needed"),
        artifact_export_allowed=False,
        tool_execution_allowed=False,
        public_claim_allowed=False,
        proof_claim_allowed=False,
        runtime_authority=False,
        writes_state=False,
        model_provider_used=False,
        learning_claimed=False,
    )


def evaluate_patch_retry_budget_v1(packet: Any) -> PatchFeedbackPacket:
    current = _packet_like(packet)
    repeated = current.repeated_failure_detected or current.retry_count >= 2
    hard_block = current.proposal_status in {
        "blocked_secret_risk",
        "blocked_network_policy",
        "blocked_write_policy",
        "blocked_protected_file",
        "blocked_missing_provenance",
        "blocked_missing_rollback",
    }
    retry_allowed = (
        current.proposal_type != "no_patch_needed"
        and current.retry_count < current.max_retries
        and not repeated
        and not hard_block
        and current.proposal_status not in {"proposal_blocked"}
    )
    proposal_status = current.proposal_status
    owner_review_required = current.owner_review_required
    operator_review_required = current.operator_review_required
    rollback_required = current.rollback_required

    if current.proposal_type == "no_patch_needed":
        proposal_status = "not_attempted"
        retry_allowed = False
    elif current.retry_count > current.max_retries:
        proposal_status = "retry_budget_exhausted"
        retry_allowed = False
        owner_review_required = True
        operator_review_required = True
    elif repeated:
        proposal_status = "rollback_required"
        retry_allowed = False
        rollback_required = True
        owner_review_required = True
        operator_review_required = True
    elif current.proposal_status in {"blocked_secret_risk", "blocked_write_policy", "blocked_network_policy", "blocked_protected_file", "blocked_missing_provenance", "blocked_missing_rollback"}:
        retry_allowed = False
    elif current.retry_count >= current.max_retries:
        proposal_status = "retry_budget_exhausted"
        retry_allowed = False
        owner_review_required = True
        operator_review_required = True
    else:
        proposal_status = "retry_budget_available"

    validation_rerun_required = current.validation_rerun_required
    if current.proposal_type == "no_patch_needed":
        validation_rerun_required = False
    else:
        validation_rerun_required = True

    return replace(
        current,
        proposal_status=proposal_status,
        retry_allowed=retry_allowed,
        repeated_failure_detected=repeated,
        rollback_required=rollback_required,
        owner_review_required=owner_review_required,
        operator_review_required=operator_review_required,
        validation_rerun_required=validation_rerun_required,
        patch_apply_allowed=False,
        commit_allowed=False,
        push_allowed=False,
        artifact_export_allowed=False,
        tool_execution_allowed=False,
        public_claim_allowed=False,
        proof_claim_allowed=False,
        runtime_authority=False,
        writes_state=False,
        model_provider_used=False,
        learning_claimed=False,
    )


def validate_patch_feedback_packet_v1(packet: Any) -> bool:
    original = packet if isinstance(packet, Mapping) else asdict(packet) if is_dataclass(packet) else {}
    if _contains_forbidden_field(original):
        raise ValidationError("forbidden_field_detected")
    normalized = _packet_like(packet)

    if normalized.failure_class not in ALLOWED_FAILURE_CLASSES_V1:
        raise ValidationError("unknown_failure_class_promoted_as_valid")
    if normalized.failure_class == "unknown_validation_failure":
        raise ValidationError("unknown_failure_class_promoted_as_valid")

    if normalized.proposal_type not in ALLOWED_PROPOSAL_TYPES_V1:
        raise ValidationError("unknown_proposal_type_promoted_as_valid")
    if normalized.proposal_type == "unknown_patch_proposal":
        raise ValidationError("unknown_proposal_type_promoted_as_valid")

    if normalized.proposal_status not in ALLOWED_PROPOSAL_STATUSES_V1:
        raise ValidationError("unknown_status_promoted_as_valid")
    if normalized.proposal_status == "unknown_status":
        raise ValidationError("unknown_status_promoted_as_valid")

    if normalized.patch_apply_allowed:
        raise ValidationError("patch_apply_allowed_must_be_false")
    if normalized.commit_allowed:
        raise ValidationError("commit_allowed_must_be_false")
    if normalized.push_allowed:
        raise ValidationError("push_allowed_must_be_false")
    if normalized.tool_execution_allowed:
        raise ValidationError("tool_execution_allowed_must_be_false")
    if normalized.public_claim_allowed:
        raise ValidationError("public_claim_allowed_must_be_false")
    if normalized.proof_claim_allowed:
        raise ValidationError("proof_claim_allowed_must_be_false")
    if normalized.runtime_authority:
        raise ValidationError("runtime_authority_must_be_false")
    if normalized.writes_state:
        raise ValidationError("writes_state_must_be_false")
    if normalized.model_provider_used:
        raise ValidationError("model_provider_used_must_be_false")
    if normalized.learning_claimed:
        raise ValidationError("learning_claimed_must_be_false")

    if normalized.retry_count < 0 or normalized.max_retries < 0:
        raise ValidationError("retry_budget_must_be_non_negative")
    if normalized.retry_count > normalized.max_retries:
        raise ValidationError("retry_count_exceeds_max_retries")
    if normalized.repeated_failure_detected and normalized.retry_allowed:
        raise ValidationError("repeated_failure_must_stop_retry")

    if normalized.rollback_required and not _safe_text(normalized.rollback_plan_ref):
        raise ValidationError("rollback_required_without_plan")

    if normalized.provenance_status not in ALLOWED_PROVENANCE_STATUSES_V1:
        raise ValidationError("unknown_provenance_status")
    if normalized.provenance_status == "missing" and normalized.proposal_type not in {
        "defer_to_owner_review",
        "defer_to_operator_review",
        "blocked_no_safe_patch",
        "rollback_proposal",
    }:
        raise ValidationError("missing_provenance_blocks_promotion")
    if normalized.provenance_status == "missing" and not (normalized.owner_review_required and normalized.operator_review_required):
        raise ValidationError("missing_provenance_requires_review")

    if normalized.protected_file_status not in (ALLOWED_CLEAR_STATUSES_V1 | ALLOWED_BLOCKED_STATUSES_V1):
        raise ValidationError("unknown_protected_file_status")
    if normalized.protected_file_status == "blocked" and not (normalized.owner_review_required and normalized.operator_review_required):
        raise ValidationError("protected_file_requires_owner_operator_review")

    if normalized.secret_risk_status not in (ALLOWED_CLEAR_STATUSES_V1 | ALLOWED_BLOCKED_STATUSES_V1):
        raise ValidationError("unknown_secret_risk_status")
    if normalized.secret_risk_status == "blocked" and normalized.proposal_type != "blocked_no_safe_patch":
        raise ValidationError("secret_risk_blocks_promotion")

    if normalized.network_policy_status not in (ALLOWED_CLEAR_STATUSES_V1 | ALLOWED_BLOCKED_STATUSES_V1):
        raise ValidationError("unknown_network_policy_status")
    if normalized.network_policy_status == "blocked" and normalized.proposal_type not in {
        "policy_fix_proposal",
        "blocked_no_safe_patch",
        "defer_to_operator_review",
    }:
        raise ValidationError("network_policy_blocks_escalation")

    if normalized.write_policy_status not in (ALLOWED_CLEAR_STATUSES_V1 | ALLOWED_BLOCKED_STATUSES_V1):
        raise ValidationError("unknown_write_policy_status")
    if normalized.write_policy_status == "blocked" and normalized.proposal_type != "blocked_no_safe_patch":
        raise ValidationError("write_policy_blocks_application")

    if normalized.proposal_type == "no_patch_needed":
        if normalized.validation_rerun_required:
            raise ValidationError("no_patch_needed_must_not_require_rerun")
        if normalized.retry_allowed:
            raise ValidationError("no_patch_needed_must_not_allow_retry")
    else:
        if not normalized.validation_rerun_required:
            raise ValidationError("validation_rerun_required_for_future_patch")

    if normalized.proposal_summary and _contains_forbidden_claim_marker(normalized.proposal_summary):
        raise ValidationError("forbidden_claim_marker_detected")
    if normalized.recommended_next_check and _contains_forbidden_claim_marker(normalized.recommended_next_check):
        raise ValidationError("forbidden_claim_marker_detected")
    if normalized.safe_metadata and _contains_forbidden_claim_marker(normalized.safe_metadata):
        raise ValidationError("forbidden_claim_marker_detected")

    if normalized.proposal_type == "blocked_no_safe_patch":
        if normalized.patch_apply_allowed or normalized.commit_allowed or normalized.push_allowed:
            raise ValidationError("blocked_no_safe_patch_must_not_allow_actions")

    return True


def summarize_patch_feedback_packet_v1(packet: Any) -> PatchFeedbackSummary:
    normalized = _packet_like(packet)
    validate_patch_feedback_packet_v1(normalized)
    return PatchFeedbackSummary(
        summary_type=SUMMARY_TYPE_V1,
        patch_feedback_packet_id=normalized.patch_feedback_packet_id,
        validation_packet_ref=normalized.validation_packet_ref,
        failure_class=normalized.failure_class,
        proposal_type=normalized.proposal_type,
        proposal_status=normalized.proposal_status,
        retry_count=normalized.retry_count,
        max_retries=normalized.max_retries,
        retry_allowed=normalized.retry_allowed,
        repeated_failure_detected=normalized.repeated_failure_detected,
        rollback_required=normalized.rollback_required,
        owner_review_required=normalized.owner_review_required,
        operator_review_required=normalized.operator_review_required,
        patch_apply_allowed=normalized.patch_apply_allowed,
        commit_allowed=normalized.commit_allowed,
        push_allowed=normalized.push_allowed,
        validation_rerun_required=normalized.validation_rerun_required,
        artifact_export_allowed=normalized.artifact_export_allowed,
        tool_execution_allowed=normalized.tool_execution_allowed,
        public_claim_allowed=normalized.public_claim_allowed,
        proof_claim_allowed=normalized.proof_claim_allowed,
        runtime_authority=normalized.runtime_authority,
        writes_state=normalized.writes_state,
        model_provider_used=normalized.model_provider_used,
        learning_claimed=normalized.learning_claimed,
        proposal_summary=normalized.proposal_summary,
        affected_path_summaries=normalized.affected_path_summaries,
        recommended_next_check=normalized.recommended_next_check,
    )


def build_initial_patch_feedback_examples_v1() -> list[PatchFeedbackPacket]:
    examples: list[PatchFeedbackPacket] = []

    examples.append(
        build_patch_feedback_packet_v1(
            patch_feedback_packet_id="unit_test_failure_source_fix_v1",
            validation_packet_ref="validation_packet_unit_test_v1",
            candidate_source_ref="candidate_source_unit_test_v1",
            artifact_provenance_ref="artifact_provenance_unit_test_v1",
            file_manifest_ref="file_manifest_unit_test_v1",
            failure_class="unit_test_failure",
            failed_check_refs=("unit_test_failure_v1",),
            warning_refs=(),
            proposal_type="source_fix_proposal",
            proposal_status="proposal_created",
            affected_path_summaries=("weslr/example_module.py",),
            protected_file_status="clear",
            secret_risk_status="not_detected",
            network_policy_status="not_required",
            write_policy_status="not_required",
            provenance_status="present",
            retry_count=0,
            max_retries=3,
            rollback_plan_ref="rollback_plan_unit_test_v1",
            safe_metadata={"example_name": "unit_test_failure_source_fix_proposal_only"},
        )
    )

    examples.append(
        build_patch_feedback_packet_v1(
            patch_feedback_packet_id="syntax_failure_metadata_fix_v1",
            validation_packet_ref="validation_packet_syntax_v1",
            candidate_source_ref="candidate_source_syntax_v1",
            artifact_provenance_ref="artifact_provenance_syntax_v1",
            file_manifest_ref="file_manifest_syntax_v1",
            failure_class="syntax_failure",
            failed_check_refs=("syntax_error_v1",),
            warning_refs=(),
            proposal_type="metadata_fix_proposal",
            proposal_status="proposal_created",
            affected_path_summaries=("weslr/example_metadata.json",),
            protected_file_status="clear",
            secret_risk_status="not_detected",
            network_policy_status="not_required",
            write_policy_status="not_required",
            provenance_status="present",
            retry_count=0,
            max_retries=2,
            rollback_plan_ref="rollback_plan_syntax_v1",
            safe_metadata={"example_name": "syntax_failure_metadata_only_patch_proposal"},
        )
    )

    examples.append(
        build_patch_feedback_packet_v1(
            patch_feedback_packet_id="protected_file_diff_blocked_v1",
            validation_packet_ref="validation_packet_protected_v1",
            candidate_source_ref="candidate_source_protected_v1",
            artifact_provenance_ref="artifact_provenance_protected_v1",
            file_manifest_ref="file_manifest_protected_v1",
            failure_class="protected_file_diff",
            failed_check_refs=("protected_file_diff_v1",),
            warning_refs=(),
            proposal_type="defer_to_operator_review",
            proposal_status="blocked_protected_file",
            affected_path_summaries=("protected_runtime_path_v1",),
            protected_file_status="blocked",
            secret_risk_status="not_detected",
            network_policy_status="not_required",
            write_policy_status="not_required",
            provenance_status="present",
            retry_count=0,
            max_retries=1,
            owner_review_required=True,
            operator_review_required=True,
            rollback_plan_ref="rollback_plan_protected_v1",
            safe_metadata={"example_name": "protected_file_diff_blocks_patch_proposal_promotion"},
        )
    )

    examples.append(
        build_patch_feedback_packet_v1(
            patch_feedback_packet_id="secret_risk_blocked_v1",
            validation_packet_ref="validation_packet_secret_v1",
            candidate_source_ref="candidate_source_secret_v1",
            artifact_provenance_ref="artifact_provenance_secret_v1",
            file_manifest_ref="file_manifest_secret_v1",
            failure_class="secret_risk",
            failed_check_refs=("secret_api_key_risk_v1",),
            warning_refs=(),
            proposal_type="blocked_no_safe_patch",
            proposal_status="blocked_secret_risk",
            affected_path_summaries=("docs/blocked_metadata.md",),
            protected_file_status="clear",
            secret_risk_status="blocked",
            network_policy_status="not_required",
            write_policy_status="not_required",
            provenance_status="present",
            retry_count=0,
            max_retries=1,
            owner_review_required=True,
            operator_review_required=True,
            rollback_plan_ref="rollback_plan_secret_v1",
            safe_metadata={"example_name": "secret_api_key_risk_blocks_patch_feedback"},
        )
    )

    examples.append(
        build_patch_feedback_packet_v1(
            patch_feedback_packet_id="retry_budget_exhausted_v1",
            validation_packet_ref="validation_packet_retry_v1",
            candidate_source_ref="candidate_source_retry_v1",
            artifact_provenance_ref="artifact_provenance_retry_v1",
            file_manifest_ref="file_manifest_retry_v1",
            failure_class="focused_test_failure",
            failed_check_refs=("focused_test_failure_v1",),
            warning_refs=(),
            proposal_type="test_fix_proposal",
            proposal_status="proposal_created",
            affected_path_summaries=("weslr/tests/test_example_module.py",),
            protected_file_status="clear",
            secret_risk_status="not_detected",
            network_policy_status="not_required",
            write_policy_status="not_required",
            provenance_status="present",
            retry_count=1,
            max_retries=1,
            rollback_plan_ref="rollback_plan_retry_v1",
            safe_metadata={"example_name": "retry_budget_exhausted_triggers_operator_review"},
        )
    )

    examples.append(
        build_patch_feedback_packet_v1(
            patch_feedback_packet_id="repeated_failure_rollback_v1",
            validation_packet_ref="validation_packet_repeat_v1",
            candidate_source_ref="candidate_source_repeat_v1",
            artifact_provenance_ref="artifact_provenance_repeat_v1",
            file_manifest_ref="file_manifest_repeat_v1",
            failure_class="unit_test_failure",
            failed_check_refs=("repeat_failure_v1",),
            warning_refs=(),
            proposal_type="rollback_proposal",
            proposal_status="rollback_required",
            affected_path_summaries=("weslr/example_module.py",),
            protected_file_status="clear",
            secret_risk_status="not_detected",
            network_policy_status="not_required",
            write_policy_status="not_required",
            provenance_status="present",
            retry_count=2,
            max_retries=5,
            repeated_failure_detected=True,
            rollback_required=True,
            rollback_plan_ref="rollback_plan_repeat_v1",
            owner_review_required=True,
            operator_review_required=True,
            safe_metadata={"example_name": "same_failure_repeated_twice_triggers_rollback_review"},
        )
    )

    examples.append(
        build_patch_feedback_packet_v1(
            patch_feedback_packet_id="missing_manifest_fix_v1",
            validation_packet_ref="validation_packet_manifest_v1",
            candidate_source_ref="candidate_source_manifest_v1",
            artifact_provenance_ref="artifact_provenance_manifest_v1",
            file_manifest_ref="",
            failure_class="manifest_missing",
            failed_check_refs=("manifest_missing_v1",),
            warning_refs=(),
            proposal_type="manifest_fix_proposal",
            proposal_status="proposal_created",
            affected_path_summaries=("weslr/example_artifact.json",),
            protected_file_status="clear",
            secret_risk_status="not_detected",
            network_policy_status="not_required",
            write_policy_status="not_required",
            provenance_status="present",
            retry_count=0,
            max_retries=2,
            rollback_plan_ref="rollback_plan_manifest_v1",
            safe_metadata={"example_name": "missing_manifest_creates_manifest_fix_proposal"},
        )
    )

    examples.append(
        build_patch_feedback_packet_v1(
            patch_feedback_packet_id="release_gate_rerun_v1",
            validation_packet_ref="validation_packet_release_gate_v1",
            candidate_source_ref="candidate_source_release_gate_v1",
            artifact_provenance_ref="artifact_provenance_release_gate_v1",
            file_manifest_ref="file_manifest_release_gate_v1",
            failure_class="release_gate_failure",
            failed_check_refs=("release_gate_failure_v1",),
            warning_refs=("release_gate_warning_v1",),
            proposal_type="defer_to_operator_review",
            proposal_status="proposal_needs_operator_review",
            affected_path_summaries=("weslr/release_pipeline_boundary_v1.py",),
            protected_file_status="clear",
            secret_risk_status="not_detected",
            network_policy_status="not_required",
            write_policy_status="not_required",
            provenance_status="present",
            retry_count=0,
            max_retries=1,
            owner_review_required=True,
            operator_review_required=True,
            rollback_plan_ref="rollback_plan_release_gate_v1",
            safe_metadata={"example_name": "release_gate_failure_creates_validation_rerun_requirement"},
        )
    )

    examples.append(
        build_patch_feedback_packet_v1(
            patch_feedback_packet_id="patch_proposal_no_commit_push_v1",
            validation_packet_ref="validation_packet_commit_v1",
            candidate_source_ref="candidate_source_commit_v1",
            artifact_provenance_ref="artifact_provenance_commit_v1",
            file_manifest_ref="file_manifest_commit_v1",
            failure_class="integration_test_failure",
            failed_check_refs=("integration_test_failure_v1",),
            warning_refs=(),
            proposal_type="source_fix_proposal",
            proposal_status="proposal_created",
            affected_path_summaries=("weslr/example_module.py",),
            protected_file_status="clear",
            secret_risk_status="not_detected",
            network_policy_status="not_required",
            write_policy_status="not_required",
            provenance_status="present",
            retry_count=0,
            max_retries=2,
            rollback_plan_ref="rollback_plan_commit_v1",
            safe_metadata={"example_name": "patch_proposal_does_not_allow_commit_push"},
        )
    )

    examples.append(
        build_patch_feedback_packet_v1(
            patch_feedback_packet_id="passed_rerun_no_public_claim_v1",
            validation_packet_ref="validation_packet_rerun_v1",
            candidate_source_ref="candidate_source_rerun_v1",
            artifact_provenance_ref="artifact_provenance_rerun_v1",
            file_manifest_ref="file_manifest_rerun_v1",
            failure_class="release_check_failure",
            failed_check_refs=(),
            warning_refs=(),
            proposal_type="no_patch_needed",
            proposal_status="not_attempted",
            proposal_summary="validation passed cleanly; no patch needed",
            affected_path_summaries=("weslr/example_module.py",),
            protected_file_status="clear",
            secret_risk_status="not_detected",
            network_policy_status="not_required",
            write_policy_status="not_required",
            provenance_status="present",
            retry_count=0,
            max_retries=0,
            validation_rerun_required=False,
            rollback_plan_ref="",
            safe_metadata={"validation_result": "passed", "example_name": "passing_validation_rerun_still_no_public_claim"},
        )
    )

    examples.append(
        build_patch_feedback_packet_v1(
            patch_feedback_packet_id="network_policy_block_v1",
            validation_packet_ref="validation_packet_network_v1",
            candidate_source_ref="candidate_source_network_v1",
            artifact_provenance_ref="artifact_provenance_network_v1",
            file_manifest_ref="file_manifest_network_v1",
            failure_class="network_policy_block",
            failed_check_refs=("network_policy_block_v1",),
            warning_refs=(),
            proposal_type="policy_fix_proposal",
            proposal_status="blocked_network_policy",
            affected_path_summaries=("network_sensitive_path_v1",),
            protected_file_status="clear",
            secret_risk_status="not_detected",
            network_policy_status="blocked",
            write_policy_status="not_required",
            provenance_status="present",
            retry_count=0,
            max_retries=1,
            owner_review_required=True,
            operator_review_required=True,
            rollback_plan_ref="rollback_plan_network_v1",
            safe_metadata={"example_name": "network_policy_block_prevents_patch_loop_escalation"},
        )
    )

    examples.append(
        build_patch_feedback_packet_v1(
            patch_feedback_packet_id="write_policy_block_v1",
            validation_packet_ref="validation_packet_write_v1",
            candidate_source_ref="candidate_source_write_v1",
            artifact_provenance_ref="artifact_provenance_write_v1",
            file_manifest_ref="file_manifest_write_v1",
            failure_class="write_policy_block",
            failed_check_refs=("write_policy_block_v1",),
            warning_refs=(),
            proposal_type="blocked_no_safe_patch",
            proposal_status="blocked_write_policy",
            affected_path_summaries=("write_sensitive_path_v1",),
            protected_file_status="clear",
            secret_risk_status="not_detected",
            network_policy_status="not_required",
            write_policy_status="blocked",
            provenance_status="present",
            retry_count=0,
            max_retries=1,
            owner_review_required=True,
            operator_review_required=True,
            rollback_plan_ref="rollback_plan_write_v1",
            safe_metadata={"example_name": "write_policy_block_prevents_patch_application"},
        )
    )

    examples.append(
        build_patch_feedback_packet_v1(
            patch_feedback_packet_id="poisoned_external_suggestion_blocked_v1",
            validation_packet_ref="validation_packet_poison_v1",
            candidate_source_ref="candidate_source_poison_v1",
            artifact_provenance_ref="artifact_provenance_poison_v1",
            file_manifest_ref="file_manifest_poison_v1",
            failure_class="secret_risk",
            failed_check_refs=("poisoned_external_suggestion_v1",),
            warning_refs=("suggestion_blocked_v1",),
            proposal_type="blocked_no_safe_patch",
            proposal_status="blocked_secret_risk",
            proposal_summary="blocked external suggestion preserved as metadata only",
            affected_path_summaries=("metadata_only_path_v1",),
            protected_file_status="clear",
            secret_risk_status="blocked",
            network_policy_status="not_required",
            write_policy_status="not_required",
            provenance_status="present",
            retry_count=0,
            max_retries=1,
            owner_review_required=True,
            operator_review_required=True,
            rollback_plan_ref="rollback_plan_poison_v1",
            safe_metadata={"blocked_external_suggestion_ref": "blocked_external_suggestion_v1", "example_name": "poisoned_external_suggestion_preserved_as_blocked_metadata"},
        )
    )

    examples.append(
        build_patch_feedback_packet_v1(
            patch_feedback_packet_id="protected_runtime_path_review_v1",
            validation_packet_ref="validation_packet_runtime_v1",
            candidate_source_ref="candidate_source_runtime_v1",
            artifact_provenance_ref="artifact_provenance_runtime_v1",
            file_manifest_ref="file_manifest_runtime_v1",
            failure_class="protected_file_diff",
            failed_check_refs=("protected_runtime_path_v1",),
            warning_refs=(),
            proposal_type="defer_to_owner_review",
            proposal_status="blocked_protected_file",
            affected_path_summaries=("protected_runtime_path_v1",),
            protected_file_status="blocked",
            secret_risk_status="not_detected",
            network_policy_status="not_required",
            write_policy_status="not_required",
            provenance_status="present",
            retry_count=0,
            max_retries=1,
            owner_review_required=True,
            operator_review_required=True,
            rollback_plan_ref="rollback_plan_runtime_v1",
            safe_metadata={"example_name": "owner_review_required_for_protected_runtime_path"},
        )
    )

    examples.append(
        build_patch_feedback_packet_v1(
            patch_feedback_packet_id="no_patch_needed_passed_cleanly_v1",
            validation_packet_ref="validation_packet_no_patch_v1",
            candidate_source_ref="candidate_source_no_patch_v1",
            artifact_provenance_ref="artifact_provenance_no_patch_v1",
            file_manifest_ref="file_manifest_no_patch_v1",
            failure_class="release_check_failure",
            failed_check_refs=(),
            warning_refs=(),
            proposal_type="no_patch_needed",
            proposal_status="not_attempted",
            proposal_summary="validation passed cleanly; no patch needed",
            affected_path_summaries=("weslr/example_module.py",),
            protected_file_status="clear",
            secret_risk_status="not_detected",
            network_policy_status="not_required",
            write_policy_status="not_required",
            provenance_status="present",
            retry_count=0,
            max_retries=0,
            validation_rerun_required=False,
            rollback_plan_ref="",
            safe_metadata={"validation_result": "passed", "example_name": "no_patch_needed_when_validation_passed_cleanly"},
        )
    )

    return examples
