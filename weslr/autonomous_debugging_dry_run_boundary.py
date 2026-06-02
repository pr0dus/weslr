"""Metadata-only autonomous debugging dry-run boundary v1.

This module classifies debugging inputs into bounded metadata packets.
It is deterministic, import-safe, pure in-memory, and fail-closed.
No subprocess. No shell execution. No file I/O. No model/provider/API calls.
No runtime wiring. No `.weslr` access. No debugging execution. No patch
application, commit, push, or public/proof/learning claims.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass, replace
from typing import Any, Mapping

HELPER_TYPE_V1 = "autonomous_debugging_dry_run_boundary_v1"
PACKET_TYPE_V1 = "debug_dry_run_packet_v1"
SUMMARY_TYPE_V1 = "debug_dry_run_summary_v1"

ALLOWED_DEBUG_INPUT_CLASSES_V1 = {
    "test_failure_report",
    "validation_failure_packet",
    "patch_feedback_packet",
    "runtime_error_summary",
    "static_analysis_warning",
    "manifest_mismatch",
    "release_gate_failure",
    "release_check_failure",
    "protected_file_block",
    "secret_or_path_risk",
    "user_reported_bug",
    "unknown_debug_input",
}

ALLOWED_HYPOTHESIS_TYPES_V1 = {
    "syntax_error_hypothesis",
    "import_error_hypothesis",
    "test_expectation_mismatch_hypothesis",
    "missing_dependency_hypothesis",
    "manifest_drift_hypothesis",
    "protected_file_policy_hypothesis",
    "secret_path_policy_hypothesis",
    "logic_regression_hypothesis",
    "boundary_violation_hypothesis",
    "unknown_hypothesis",
}

ALLOWED_DRY_RUN_ACTIONS_V1 = {
    "inspect_metadata_only",
    "propose_test_command",
    "propose_static_check",
    "propose_file_manifest_check",
    "propose_patch_feedback",
    "propose_rollback_review",
    "propose_owner_review",
    "propose_operator_review",
    "defer_to_validation_runner",
    "defer_to_tool_executor_boundary",
    "block_due_policy",
    "unknown_dry_run_action",
}

ALLOWED_DRY_RUN_STATUSES_V1 = {
    "dry_run_not_started",
    "dry_run_ready",
    "dry_run_completed",
    "dry_run_blocked_policy",
    "dry_run_blocked_secret",
    "dry_run_blocked_path",
    "dry_run_blocked_missing_validation",
    "dry_run_blocked_missing_manifest",
    "dry_run_needs_owner_review",
    "dry_run_needs_operator_review",
    "unknown_status",
}

ALLOWED_CLEAR_OR_BLOCKED_V1 = {"clear", "blocked", "unknown"}

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
    "credential",
    "password",
)

FORBIDDEN_CLAIM_PHRASES_V1 = (
    "proof",
    "correctness",
    "public readiness",
    "public_readiness",
    "security certification",
    "certification",
    "public claim",
    "runtime authority",
    "model authority",
    "tool authority",
    "learning claim",
    "autonomous learning",
)

TEST_HINTS_V1 = ("test", "assert", "failure", "expected", "actual", "pytest", "unit")
IMPORT_HINTS_V1 = ("importerror", "no module named", "module not found", "import error", "cannot import")
SYNTAX_HINTS_V1 = ("syntaxerror", "syntax error", "parse error", "invalid syntax")
MANIFEST_HINTS_V1 = ("manifest", "file list", "hash mismatch", "drift")
PROTECTED_FILE_HINTS_V1 = ("protected file", "chat_responder.py", "main.py", "dialogue.py", "chat_ui.py")
SECRET_PATH_HINTS_V1 = ("secret", "token", "credential", "password", "private", "path", "permission denied")
RUNTIME_ERROR_HINTS_V1 = ("traceback", "exception", "runtime error", "crash", "stack trace")
PATCH_HINTS_V1 = ("patch", "proposal", "feedback")
RELEASE_HINTS_V1 = ("release gate", "release check", "gate failed", "check failed")
NETWORK_HINTS_V1 = ("network", "http://", "https://", "api", "remote")
TOOL_HINTS_V1 = ("shell", "command", "tool", "executor", "apply_patch", "git", "commit", "push")
ROLLBACK_HINTS_V1 = ("rollback", "revert", "repeat", "unresolved", "retry exhausted")
VALIDATION_HINTS_V1 = ("validation", "validated", "passed")
BUG_HINTS_V1 = ("bug", "issue", "problem", "broken")

class ValidationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class DebugDryRunPacket:
    debug_dry_run_packet_id: str
    debug_input_class: str
    input_summary: str
    validation_packet_ref: str
    patch_feedback_packet_ref: str
    tool_use_packet_ref: str
    artifact_provenance_ref: str
    file_manifest_ref: str
    hypotheses: tuple[str, ...]
    proposed_dry_run_actions: tuple[str, ...]
    blocked_actions: tuple[str, ...]
    dry_run_status: str
    diagnosis_summary: str
    expected_checks: tuple[str, ...]
    expected_patch_feedback: str
    protected_file_status: str
    secret_risk_status: str
    path_risk_status: str
    network_policy_status: str
    write_policy_status: str
    owner_review_required: bool
    operator_review_required: bool
    real_execution_allowed: bool
    tool_execution_allowed: bool
    patch_apply_allowed: bool
    commit_allowed: bool
    push_allowed: bool
    rollback_required: bool
    rollback_plan_ref: str
    validation_rerun_required: bool
    recommended_next_check: str
    runtime_authority: bool
    writes_state: bool
    model_provider_used: bool
    public_claim_allowed: bool
    proof_claim_allowed: bool
    learning_claimed: bool
    safe_metadata: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class DebugDryRunSummary:
    summary_type: str
    debug_dry_run_packet_id: str
    debug_input_class: str
    dry_run_status: str
    diagnosis_summary: str
    recommended_next_check: str
    owner_review_required: bool
    operator_review_required: bool
    rollback_required: bool
    validation_rerun_required: bool


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


def _safe_mapping(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, Mapping):
        return {_safe_text(key): to_debug_dry_run_json_safe_v1(item) for key, item in value.items()}
    return {"value": to_debug_dry_run_json_safe_v1(value)}


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
            if key_text in {"safe_metadata", "input_summary", "diagnosis_summary", "expected_patch_feedback", "recommended_next_check"} or key_text.endswith("_metadata"):
                if _contains_forbidden_claim_marker(item):
                    return True
        return False
    if isinstance(value, (list, tuple, set)):
        return any(_contains_forbidden_claim_marker(item) for item in value)
    blob = _normalize_text(value)
    return bool(blob) and any(phrase in blob for phrase in FORBIDDEN_CLAIM_PHRASES_V1)


def _contains_authorize_phrase(value: Any) -> bool:
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = _normalize_text(key)
            if key_text in {"document_text", "document_content", "source_text", "user_text", "suggestion_text", "llm_output"}:
                if _contains_authorize_phrase(item):
                    return True
        return False
    if isinstance(value, (list, tuple, set)):
        return any(_contains_authorize_phrase(item) for item in value)
    blob = _normalize_text(value)
    return bool(blob) and any(phrase in blob for phrase in ("authorize", "run this", "do it now", "go ahead", "permission to run"))


def _contains_poison_signal(value: Any) -> bool:
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, Mapping):
        if _normalize_text(value.get("poison_status")) == "poisoned":
            return True
        for item in value.values():
            if _contains_poison_signal(item):
                return True
    elif isinstance(value, (list, tuple, set)):
        return any(_contains_poison_signal(item) for item in value)
    return False


def _json_sort_key(value: Any) -> tuple[str, str]:
    return (type(value).__name__, repr(value))


def to_debug_dry_run_json_safe_v1(value: Any) -> Any:
    if is_dataclass(value):
        value = asdict(value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return {_safe_text(key): to_debug_dry_run_json_safe_v1(item) for key, item in sorted(value.items(), key=lambda item: _safe_text(item[0]))}
    if isinstance(value, tuple):
        return [to_debug_dry_run_json_safe_v1(item) for item in value]
    if isinstance(value, list):
        return [to_debug_dry_run_json_safe_v1(item) for item in value]
    if isinstance(value, set):
        items = [to_debug_dry_run_json_safe_v1(item) for item in value]
        return sorted(items, key=_json_sort_key)
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return to_debug_dry_run_json_safe_v1(value.to_dict())
    if hasattr(value, "__dict__"):
        return to_debug_dry_run_json_safe_v1(vars(value))
    return _safe_text(value)


def _packet_like(value: Any) -> DebugDryRunPacket:
    if isinstance(value, DebugDryRunPacket):
        return value
    if not isinstance(value, Mapping):
        value = asdict(value) if is_dataclass(value) else {}
    safe_metadata = value.get("safe_metadata", None)
    if safe_metadata is not None and not isinstance(safe_metadata, Mapping):
        safe_metadata = {"value": safe_metadata}
    return DebugDryRunPacket(
        debug_dry_run_packet_id=_safe_text(value.get("debug_dry_run_packet_id")),
        debug_input_class=_safe_text(value.get("debug_input_class")),
        input_summary=_safe_text(value.get("input_summary")),
        validation_packet_ref=_safe_text(value.get("validation_packet_ref")),
        patch_feedback_packet_ref=_safe_text(value.get("patch_feedback_packet_ref")),
        tool_use_packet_ref=_safe_text(value.get("tool_use_packet_ref")),
        artifact_provenance_ref=_safe_text(value.get("artifact_provenance_ref")),
        file_manifest_ref=_safe_text(value.get("file_manifest_ref")),
        hypotheses=tuple(_safe_text(item) for item in value.get("hypotheses", ()) or ()),
        proposed_dry_run_actions=tuple(_safe_text(item) for item in value.get("proposed_dry_run_actions", ()) or ()),
        blocked_actions=tuple(_safe_text(item) for item in value.get("blocked_actions", ()) or ()),
        dry_run_status=_safe_text(value.get("dry_run_status")),
        diagnosis_summary=_safe_text(value.get("diagnosis_summary")),
        expected_checks=tuple(_safe_text(item) for item in value.get("expected_checks", ()) or ()),
        expected_patch_feedback=_safe_text(value.get("expected_patch_feedback")),
        protected_file_status=_safe_text(value.get("protected_file_status", "unknown")),
        secret_risk_status=_safe_text(value.get("secret_risk_status", "unknown")),
        path_risk_status=_safe_text(value.get("path_risk_status", "unknown")),
        network_policy_status=_safe_text(value.get("network_policy_status", "unknown")),
        write_policy_status=_safe_text(value.get("write_policy_status", "unknown")),
        owner_review_required=_safe_bool(value.get("owner_review_required", False)),
        operator_review_required=_safe_bool(value.get("operator_review_required", False)),
        real_execution_allowed=_safe_bool(value.get("real_execution_allowed", False)),
        tool_execution_allowed=_safe_bool(value.get("tool_execution_allowed", False)),
        patch_apply_allowed=_safe_bool(value.get("patch_apply_allowed", False)),
        commit_allowed=_safe_bool(value.get("commit_allowed", False)),
        push_allowed=_safe_bool(value.get("push_allowed", False)),
        rollback_required=_safe_bool(value.get("rollback_required", False)),
        rollback_plan_ref=_safe_text(value.get("rollback_plan_ref")),
        validation_rerun_required=_safe_bool(value.get("validation_rerun_required", False)),
        recommended_next_check=_safe_text(value.get("recommended_next_check")),
        runtime_authority=_safe_bool(value.get("runtime_authority", False)),
        writes_state=_safe_bool(value.get("writes_state", False)),
        model_provider_used=_safe_bool(value.get("model_provider_used", False)),
        public_claim_allowed=_safe_bool(value.get("public_claim_allowed", False)),
        proof_claim_allowed=_safe_bool(value.get("proof_claim_allowed", False)),
        learning_claimed=_safe_bool(value.get("learning_claimed", False)),
        safe_metadata=dict(safe_metadata or {}),
    )


def classify_debug_input_v1(
    *,
    debug_input_class: str | None = None,
    input_summary: str | None = None,
    safe_metadata: Mapping[str, Any] | None = None,
) -> str:
    candidate = _safe_text(debug_input_class).strip().lower()
    if candidate in ALLOWED_DEBUG_INPUT_CLASSES_V1:
        return candidate

    probe = " ".join([
        _safe_text(debug_input_class),
        _safe_text(input_summary),
        " ".join(_safe_text(item) for item in (safe_metadata or {}).values()) if isinstance(safe_metadata, Mapping) else "",
    ]).lower()

    if any(h in probe for h in IMPORT_HINTS_V1):
        return "runtime_error_summary"
    if any(h in probe for h in SYNTAX_HINTS_V1):
        return "runtime_error_summary"
    if any(h in probe for h in MANIFEST_HINTS_V1):
        return "manifest_mismatch"
    if any(h in probe for h in PROTECTED_FILE_HINTS_V1):
        return "protected_file_block"
    if any(h in probe for h in SECRET_PATH_HINTS_V1):
        return "secret_or_path_risk"
    if any(h in probe for h in RELEASE_HINTS_V1):
        return "release_gate_failure" if "gate" in probe else "release_check_failure"
    if any(h in probe for h in TEST_HINTS_V1):
        return "test_failure_report"
    if any(h in probe for h in PATCH_HINTS_V1):
        return "patch_feedback_packet"
    if any(h in probe for h in BUG_HINTS_V1):
        return "user_reported_bug"
    return "unknown_debug_input"


def derive_debug_hypotheses_v1(packet: Any) -> tuple[str, ...]:
    current = _packet_like(packet)
    blob = " ".join([
        current.input_summary,
        current.diagnosis_summary,
        current.expected_patch_feedback,
        " ".join(current.expected_checks),
        current.recommended_next_check,
        " ".join(_safe_text(item) for item in current.safe_metadata.values()) if current.safe_metadata else "",
    ]).lower()
    hypotheses: list[str] = []

    def add(item: str) -> None:
        if item not in hypotheses:
            hypotheses.append(item)

    if any(h in blob for h in SYNTAX_HINTS_V1):
        add("syntax_error_hypothesis")
    if any(h in blob for h in IMPORT_HINTS_V1):
        add("import_error_hypothesis")
        add("missing_dependency_hypothesis")
    if current.debug_input_class == "test_failure_report" or any(h in blob for h in TEST_HINTS_V1):
        add("test_expectation_mismatch_hypothesis")
        add("logic_regression_hypothesis")
    if current.debug_input_class in {"manifest_mismatch", "release_gate_failure", "release_check_failure"} or any(h in blob for h in MANIFEST_HINTS_V1):
        add("manifest_drift_hypothesis")
    if current.debug_input_class == "protected_file_block" or any(h in blob for h in PROTECTED_FILE_HINTS_V1):
        add("protected_file_policy_hypothesis")
        add("boundary_violation_hypothesis")
    if current.debug_input_class == "secret_or_path_risk" or any(h in blob for h in SECRET_PATH_HINTS_V1):
        add("secret_path_policy_hypothesis")
        add("boundary_violation_hypothesis")
    if current.tool_use_packet_ref or current.patch_feedback_packet_ref:
        add("boundary_violation_hypothesis")
    if not hypotheses:
        add("unknown_hypothesis")
    return tuple(hypotheses)


def select_debug_dry_run_actions_v1(packet: Any) -> tuple[str, ...]:
    current = _packet_like(packet)
    actions: list[str] = []
    blocked: list[str] = []

    def add(action: str) -> None:
        if action not in actions:
            actions.append(action)

    def block(action: str) -> None:
        if action not in blocked:
            blocked.append(action)

    add("inspect_metadata_only")
    if current.validation_packet_ref:
        add("defer_to_validation_runner")
    else:
        add("defer_to_validation_runner")
        block("defer_to_validation_runner")
    if current.patch_feedback_packet_ref:
        add("propose_patch_feedback")
    if current.tool_use_packet_ref:
        add("defer_to_tool_executor_boundary")
    if current.file_manifest_ref:
        add("propose_file_manifest_check")
    if current.rollback_required:
        add("propose_rollback_review")
    if current.owner_review_required:
        add("propose_owner_review")
    if current.operator_review_required:
        add("propose_operator_review")
    if current.validation_rerun_required:
        add("propose_test_command")
    if current.dry_run_status in {"dry_run_blocked_policy", "dry_run_blocked_secret", "dry_run_blocked_path"}:
        add("block_due_policy")
    if current.debug_input_class in {"runtime_error_summary", "static_analysis_warning"}:
        add("propose_static_check")
    if current.debug_input_class in {"test_failure_report", "release_gate_failure", "release_check_failure"}:
        add("propose_test_command")
    if current.debug_input_class == "manifest_mismatch":
        add("propose_file_manifest_check")
    if current.debug_input_class == "patch_feedback_packet":
        add("propose_patch_feedback")
    if current.debug_input_class == "protected_file_block":
        add("propose_owner_review")
        add("propose_operator_review")
    if current.debug_input_class == "secret_or_path_risk":
        add("block_due_policy")
    if current.secret_risk_status == "blocked" or current.path_risk_status == "blocked":
        add("block_due_policy")
    return tuple(actions + [item for item in blocked if item not in actions])


def build_debug_dry_run_packet_v1(**kwargs: Any) -> DebugDryRunPacket:
    packet = DebugDryRunPacket(
        debug_dry_run_packet_id=_safe_text(kwargs.get("debug_dry_run_packet_id")),
        debug_input_class=classify_debug_input_v1(
            debug_input_class=kwargs.get("debug_input_class"),
            input_summary=kwargs.get("input_summary"),
            safe_metadata=kwargs.get("safe_metadata"),
        ),
        input_summary=_safe_text(kwargs.get("input_summary")),
        validation_packet_ref=_safe_text(kwargs.get("validation_packet_ref")),
        patch_feedback_packet_ref=_safe_text(kwargs.get("patch_feedback_packet_ref")),
        tool_use_packet_ref=_safe_text(kwargs.get("tool_use_packet_ref")),
        artifact_provenance_ref=_safe_text(kwargs.get("artifact_provenance_ref")),
        file_manifest_ref=_safe_text(kwargs.get("file_manifest_ref")),
        hypotheses=tuple(_safe_text(item) for item in kwargs.get("hypotheses", ()) or ()),
        proposed_dry_run_actions=tuple(_safe_text(item) for item in kwargs.get("proposed_dry_run_actions", ()) or ()),
        blocked_actions=tuple(_safe_text(item) for item in kwargs.get("blocked_actions", ()) or ()),
        dry_run_status=_safe_text(kwargs.get("dry_run_status", "dry_run_not_started")),
        diagnosis_summary=_safe_text(kwargs.get("diagnosis_summary")),
        expected_checks=tuple(_safe_text(item) for item in kwargs.get("expected_checks", ()) or ()),
        expected_patch_feedback=_safe_text(kwargs.get("expected_patch_feedback")),
        protected_file_status=_safe_text(kwargs.get("protected_file_status", "unknown")),
        secret_risk_status=_safe_text(kwargs.get("secret_risk_status", "unknown")),
        path_risk_status=_safe_text(kwargs.get("path_risk_status", "unknown")),
        network_policy_status=_safe_text(kwargs.get("network_policy_status", "unknown")),
        write_policy_status=_safe_text(kwargs.get("write_policy_status", "unknown")),
        owner_review_required=_safe_bool(kwargs.get("owner_review_required", False)),
        operator_review_required=_safe_bool(kwargs.get("operator_review_required", False)),
        real_execution_allowed=_safe_bool(kwargs.get("real_execution_allowed", False)),
        tool_execution_allowed=_safe_bool(kwargs.get("tool_execution_allowed", False)),
        patch_apply_allowed=_safe_bool(kwargs.get("patch_apply_allowed", False)),
        commit_allowed=_safe_bool(kwargs.get("commit_allowed", False)),
        push_allowed=_safe_bool(kwargs.get("push_allowed", False)),
        rollback_required=_safe_bool(kwargs.get("rollback_required", False)),
        rollback_plan_ref=_safe_text(kwargs.get("rollback_plan_ref")),
        validation_rerun_required=_safe_bool(kwargs.get("validation_rerun_required", False)),
        recommended_next_check=_safe_text(kwargs.get("recommended_next_check", "inspect_metadata_only")),
        runtime_authority=_safe_bool(kwargs.get("runtime_authority", False)),
        writes_state=_safe_bool(kwargs.get("writes_state", False)),
        model_provider_used=_safe_bool(kwargs.get("model_provider_used", False)),
        public_claim_allowed=_safe_bool(kwargs.get("public_claim_allowed", False)),
        proof_claim_allowed=_safe_bool(kwargs.get("proof_claim_allowed", False)),
        learning_claimed=_safe_bool(kwargs.get("learning_claimed", False)),
        safe_metadata=_safe_mapping(kwargs.get("safe_metadata")),
    )
    packet = replace(packet, hypotheses=derive_debug_hypotheses_v1(packet))
    packet = replace(packet, proposed_dry_run_actions=select_debug_dry_run_actions_v1(packet))
    return packet


def validate_debug_dry_run_packet_v1(packet: Any) -> bool:
    original = packet if isinstance(packet, Mapping) else asdict(packet) if is_dataclass(packet) else {}
    if _contains_forbidden_field(original):
        raise ValidationError("forbidden_field_detected")
    normalized = _packet_like(packet)

    if normalized.debug_input_class not in ALLOWED_DEBUG_INPUT_CLASSES_V1:
        raise ValidationError("unknown_debug_input_promoted_as_valid")
    if normalized.dry_run_status not in ALLOWED_DRY_RUN_STATUSES_V1:
        raise ValidationError("unknown_status_promoted_as_valid")
    for action in normalized.proposed_dry_run_actions:
        if action not in ALLOWED_DRY_RUN_ACTIONS_V1:
            raise ValidationError("unknown_dry_run_action_promoted_as_valid")
    for action in normalized.blocked_actions:
        if action not in ALLOWED_DRY_RUN_ACTIONS_V1:
            raise ValidationError("unknown_dry_run_action_promoted_as_valid")
    for hyp in normalized.hypotheses:
        if hyp not in ALLOWED_HYPOTHESIS_TYPES_V1:
            raise ValidationError("unknown_hypothesis_promoted_as_valid")

    if normalized.real_execution_allowed:
        raise ValidationError("real_execution_not_allowed_in_dry_run")
    if normalized.tool_execution_allowed:
        raise ValidationError("tool_execution_not_allowed_in_dry_run")
    if normalized.patch_apply_allowed:
        raise ValidationError("patch_apply_not_allowed_in_dry_run")
    if normalized.commit_allowed:
        raise ValidationError("commit_allowed_must_be_false")
    if normalized.push_allowed:
        raise ValidationError("push_allowed_must_be_false")
    if normalized.writes_state:
        raise ValidationError("writes_state_must_be_false")
    if normalized.runtime_authority:
        raise ValidationError("runtime_authority_must_be_false")
    if normalized.model_provider_used:
        raise ValidationError("model_provider_used_must_be_false")
    if normalized.public_claim_allowed:
        raise ValidationError("public_claim_allowed_must_be_false")
    if normalized.proof_claim_allowed:
        raise ValidationError("proof_claim_allowed_must_be_false")
    if normalized.learning_claimed:
        raise ValidationError("learning_claimed_must_be_false")

    if normalized.protected_file_status == "blocked" and not (normalized.owner_review_required or normalized.operator_review_required):
        raise ValidationError("protected_file_requires_review")
    if normalized.validation_packet_ref == "" and normalized.dry_run_status != "dry_run_blocked_missing_validation":
        raise ValidationError("missing_validation_packet_must_defer")
    if normalized.file_manifest_ref == "" and normalized.dry_run_status == "dry_run_ready" and "propose_file_manifest_check" not in normalized.proposed_dry_run_actions:
        raise ValidationError("missing_manifest_must_defer")
    if normalized.debug_input_class == "patch_feedback_packet" and "propose_patch_feedback" not in normalized.proposed_dry_run_actions:
        raise ValidationError("patch_feedback_must_stay_proposal_only")
    if normalized.tool_use_packet_ref and "defer_to_tool_executor_boundary" not in normalized.proposed_dry_run_actions:
        raise ValidationError("tool_required_step_must_defer")
    if normalized.rollback_required and "propose_rollback_review" not in normalized.proposed_dry_run_actions:
        raise ValidationError("rollback_must_be_surfaced")

    if normalized.diagnosis_summary and _contains_forbidden_claim_marker(normalized.diagnosis_summary):
        raise ValidationError("forbidden_claim_marker_detected")
    if normalized.expected_patch_feedback and _contains_forbidden_claim_marker(normalized.expected_patch_feedback):
        raise ValidationError("forbidden_claim_marker_detected")
    if normalized.safe_metadata and _contains_forbidden_claim_marker(normalized.safe_metadata):
        raise ValidationError("forbidden_claim_marker_detected")

    if normalized.debug_input_class == "unknown_debug_input" and normalized.dry_run_status != "unknown_status":
        raise ValidationError("unknown_debug_input_must_fail_closed")

    return True


def summarize_debug_dry_run_packet_v1(packet: Any) -> DebugDryRunSummary:
    normalized = _packet_like(packet)
    validate_debug_dry_run_packet_v1(normalized)
    return DebugDryRunSummary(
        summary_type=SUMMARY_TYPE_V1,
        debug_dry_run_packet_id=normalized.debug_dry_run_packet_id,
        debug_input_class=normalized.debug_input_class,
        dry_run_status=normalized.dry_run_status,
        diagnosis_summary=normalized.diagnosis_summary,
        recommended_next_check=normalized.recommended_next_check,
        owner_review_required=normalized.owner_review_required,
        operator_review_required=normalized.operator_review_required,
        rollback_required=normalized.rollback_required,
        validation_rerun_required=normalized.validation_rerun_required,
    )


def build_initial_debug_dry_run_examples_v1() -> list[DebugDryRunPacket]:
    examples: list[DebugDryRunPacket] = []

    examples.append(build_debug_dry_run_packet_v1(
        debug_dry_run_packet_id="unit_test_failure_dry_run_v1",
        debug_input_class="test_failure_report",
        input_summary="Unit test failure becomes dry-run diagnosis, no command execution.",
        validation_packet_ref="validation_packet_unit_test_v1",
        artifact_provenance_ref="artifact_provenance_unit_test_v1",
        file_manifest_ref="file_manifest_unit_test_v1",
        hypotheses=("test_expectation_mismatch_hypothesis", "logic_regression_hypothesis"),
        expected_checks=("inspect_metadata_only", "propose_test_command"),
        diagnosis_summary="Assertion mismatch suggests a test expectation issue or logic regression.",
        expected_patch_feedback="Create a proposal-only patch feedback item after review.",
        dry_run_status="dry_run_ready",
        safe_metadata={"example_name": "unit_test_failure_dry_run"},
    ))
    examples.append(build_debug_dry_run_packet_v1(
        debug_dry_run_packet_id="import_error_dependency_check_v1",
        debug_input_class="runtime_error_summary",
        input_summary="Import error proposes metadata-only dependency check.",
        validation_packet_ref="validation_packet_import_error_v1",
        artifact_provenance_ref="artifact_provenance_import_error_v1",
        file_manifest_ref="file_manifest_import_error_v1",
        hypotheses=("import_error_hypothesis", "missing_dependency_hypothesis"),
        expected_checks=("inspect_metadata_only", "propose_static_check"),
        diagnosis_summary="Import failure likely from a missing dependency or module path issue.",
        expected_patch_feedback="No patch apply; propose metadata-only dependency verification.",
        dry_run_status="dry_run_ready",
        safe_metadata={"example_name": "import_error_dependency_check"},
    ))
    examples.append(build_debug_dry_run_packet_v1(
        debug_dry_run_packet_id="manifest_mismatch_review_v1",
        debug_input_class="manifest_mismatch",
        input_summary="Manifest mismatch proposes manifest review.",
        validation_packet_ref="validation_packet_manifest_v1",
        artifact_provenance_ref="artifact_provenance_manifest_v1",
        file_manifest_ref="file_manifest_manifest_v1",
        hypotheses=("manifest_drift_hypothesis",),
        expected_checks=("propose_file_manifest_check",),
        diagnosis_summary="File manifest and observed state appear out of sync.",
        expected_patch_feedback="Review manifest drift before any repair proposal.",
        dry_run_status="dry_run_ready",
        safe_metadata={"example_name": "manifest_mismatch_review"},
    ))
    examples.append(build_debug_dry_run_packet_v1(
        debug_dry_run_packet_id="protected_file_owner_operator_review_v1",
        debug_input_class="protected_file_block",
        input_summary="Protected file block requires owner/operator review.",
        validation_packet_ref="validation_packet_protected_file_v1",
        artifact_provenance_ref="artifact_provenance_protected_file_v1",
        file_manifest_ref="file_manifest_protected_file_v1",
        protected_file_status="blocked",
        owner_review_required=True,
        operator_review_required=True,
        hypotheses=("protected_file_policy_hypothesis", "boundary_violation_hypothesis"),
        expected_checks=("propose_owner_review", "propose_operator_review"),
        diagnosis_summary="Protected file boundaries prevent autonomous repair.",
        expected_patch_feedback="Request owner/operator review instead of proposing file edits.",
        dry_run_status="dry_run_needs_owner_review",
        safe_metadata={"example_name": "protected_file_owner_operator_review"},
    ))
    examples.append(build_debug_dry_run_packet_v1(
        debug_dry_run_packet_id="secret_risk_blocks_escalation_v1",
        debug_input_class="secret_or_path_risk",
        input_summary="Secret risk blocks debugging escalation.",
        validation_packet_ref="validation_packet_secret_risk_v1",
        artifact_provenance_ref="artifact_provenance_secret_risk_v1",
        file_manifest_ref="file_manifest_secret_risk_v1",
        secret_risk_status="blocked",
        path_risk_status="clear",
        hypotheses=("secret_path_policy_hypothesis",),
        proposed_dry_run_actions=("inspect_metadata_only", "block_due_policy"),
        blocked_actions=("propose_test_command", "propose_static_check"),
        diagnosis_summary="Secrets or path-sensitive content block escalation.",
        expected_patch_feedback="Do not promote into execution; preserve blocked metadata only.",
        dry_run_status="dry_run_blocked_secret",
        safe_metadata={"example_name": "secret_risk_blocks_escalation"},
    ))
    examples.append(build_debug_dry_run_packet_v1(
        debug_dry_run_packet_id="release_gate_failure_rerun_v1",
        debug_input_class="release_gate_failure",
        input_summary="Release gate failure proposes validation rerun, not execution.",
        validation_packet_ref="validation_packet_release_gate_v1",
        artifact_provenance_ref="artifact_provenance_release_gate_v1",
        file_manifest_ref="file_manifest_release_gate_v1",
        hypotheses=("logic_regression_hypothesis", "manifest_drift_hypothesis"),
        validation_rerun_required=True,
        expected_checks=("propose_test_command", "defer_to_validation_runner"),
        diagnosis_summary="Release gate failure should loop back through validation metadata.",
        expected_patch_feedback="Rerun validation; do not execute debugging actions.",
        dry_run_status="dry_run_blocked_missing_validation",
        safe_metadata={"example_name": "release_gate_failure_rerun"},
    ))
    examples.append(build_debug_dry_run_packet_v1(
        debug_dry_run_packet_id="patch_feedback_proposal_only_v1",
        debug_input_class="patch_feedback_packet",
        input_summary="Patch feedback packet suggests proposal path, not patch apply.",
        validation_packet_ref="validation_packet_patch_feedback_v1",
        patch_feedback_packet_ref="patch_feedback_packet_patch_feedback_v1",
        artifact_provenance_ref="artifact_provenance_patch_feedback_v1",
        file_manifest_ref="file_manifest_patch_feedback_v1",
        hypotheses=("boundary_violation_hypothesis",),
        expected_checks=("propose_patch_feedback",),
        diagnosis_summary="Patch feedback should remain proposal-only metadata.",
        expected_patch_feedback="Route back to patch feedback loop; no direct patch application.",
        dry_run_status="dry_run_ready",
        safe_metadata={"example_name": "patch_feedback_proposal_only"},
    ))
    examples.append(build_debug_dry_run_packet_v1(
        debug_dry_run_packet_id="tool_deferred_to_executor_v1",
        debug_input_class="runtime_error_summary",
        input_summary="Tool-required debugging step defers to Tool-Use Executor Boundary.",
        validation_packet_ref="validation_packet_tool_defer_v1",
        tool_use_packet_ref="tool_use_packet_tool_defer_v1",
        artifact_provenance_ref="artifact_provenance_tool_defer_v1",
        file_manifest_ref="file_manifest_tool_defer_v1",
        hypotheses=("boundary_violation_hypothesis",),
        expected_checks=("defer_to_tool_executor_boundary",),
        diagnosis_summary="Any shell/write/network/tool step must move to tool-use metadata first.",
        expected_patch_feedback="No direct execution; create a tool-use packet instead.",
        dry_run_status="dry_run_ready",
        safe_metadata={"example_name": "tool_deferred_to_executor"},
    ))
    examples.append(build_debug_dry_run_packet_v1(
        debug_dry_run_packet_id="repeated_failure_rollback_review_v1",
        debug_input_class="test_failure_report",
        input_summary="Repeated unresolved failure triggers rollback/review.",
        validation_packet_ref="validation_packet_repeat_v1",
        artifact_provenance_ref="artifact_provenance_repeat_v1",
        file_manifest_ref="file_manifest_repeat_v1",
        rollback_required=True,
        rollback_plan_ref="rollback_plan_repeat_v1",
        hypotheses=("logic_regression_hypothesis", "boundary_violation_hypothesis"),
        expected_checks=("propose_rollback_review", "propose_owner_review"),
        diagnosis_summary="Repeated unresolved failures should stop and request review.",
        expected_patch_feedback="Rollback review required before any further repair proposal.",
        dry_run_status="dry_run_needs_owner_review",
        safe_metadata={"example_name": "repeated_failure_rollback_review"},
    ))
    examples.append(build_debug_dry_run_packet_v1(
        debug_dry_run_packet_id="network_dependent_debug_blocked_v1",
        debug_input_class="secret_or_path_risk",
        input_summary="Network-dependent debugging is blocked without approval.",
        validation_packet_ref="validation_packet_network_block_v1",
        artifact_provenance_ref="artifact_provenance_network_block_v1",
        file_manifest_ref="file_manifest_network_block_v1",
        network_policy_status="blocked",
        hypotheses=("secret_path_policy_hypothesis", "boundary_violation_hypothesis"),
        proposed_dry_run_actions=("inspect_metadata_only", "block_due_policy"),
        blocked_actions=("propose_test_command", "propose_static_check"),
        diagnosis_summary="Network access is blocked; keep debugging metadata-only.",
        expected_patch_feedback="Defer to approval-bound executor boundary if network actions are needed.",
        dry_run_status="dry_run_blocked_policy",
        safe_metadata={"example_name": "network_dependent_debug_blocked"},
    ))
    examples.append(build_debug_dry_run_packet_v1(
        debug_dry_run_packet_id="user_reported_bug_hypothesis_only_v1",
        debug_input_class="user_reported_bug",
        input_summary="User-reported bug becomes hypothesis list only.",
        validation_packet_ref="validation_packet_user_bug_v1",
        artifact_provenance_ref="artifact_provenance_user_bug_v1",
        file_manifest_ref="file_manifest_user_bug_v1",
        hypotheses=("unknown_hypothesis",),
        expected_checks=("inspect_metadata_only",),
        diagnosis_summary="Treat the report as a hypothesis seed, not a claim.",
        expected_patch_feedback="List hypotheses only; do not execute or mutate.",
        dry_run_status="dry_run_ready",
        safe_metadata={"example_name": "user_reported_bug_hypothesis_only"},
    ))
    examples.append(build_debug_dry_run_packet_v1(
        debug_dry_run_packet_id="validation_pass_not_correctness_v1",
        debug_input_class="validation_failure_packet",
        input_summary="Passing validation still does not claim correctness.",
        validation_packet_ref="validation_packet_validation_pass_v1",
        artifact_provenance_ref="artifact_provenance_validation_pass_v1",
        file_manifest_ref="file_manifest_validation_pass_v1",
        hypotheses=("logic_regression_hypothesis",),
        expected_checks=("defer_to_validation_runner",),
        diagnosis_summary="Validation success is metadata, not a guarantee of final outcome.",
        expected_patch_feedback="Keep the result as metadata only; no further claim promotion.",
        dry_run_status="dry_run_completed",
        safe_metadata={"example_name": "validation_pass_not_correctness"},
    ))
    examples.append(build_debug_dry_run_packet_v1(
        debug_dry_run_packet_id="dry_run_cannot_commit_or_push_v1",
        debug_input_class="test_failure_report",
        input_summary="Dry-run cannot commit or push.",
        validation_packet_ref="validation_packet_commit_push_v1",
        artifact_provenance_ref="artifact_provenance_commit_push_v1",
        file_manifest_ref="file_manifest_commit_push_v1",
        commit_allowed=False,
        push_allowed=False,
        hypotheses=("boundary_violation_hypothesis",),
        expected_checks=("inspect_metadata_only", "defer_to_tool_executor_boundary"),
        diagnosis_summary="Commit/push remain outside dry-run authority.",
        expected_patch_feedback="Keep commit/push blocked and proposal-only.",
        dry_run_status="dry_run_ready",
        safe_metadata={"example_name": "dry_run_cannot_commit_or_push"},
    ))
    examples.append(build_debug_dry_run_packet_v1(
        debug_dry_run_packet_id="dry_run_cannot_write_weslr_v1",
        debug_input_class="protected_file_block",
        input_summary="Dry-run cannot write .weslr.",
        validation_packet_ref="validation_packet_weslr_write_v1",
        artifact_provenance_ref="artifact_provenance_weslr_write_v1",
        file_manifest_ref="file_manifest_weslr_write_v1",
        protected_file_status="blocked",
        owner_review_required=True,
        operator_review_required=True,
        hypotheses=("protected_file_policy_hypothesis",),
        expected_checks=("propose_owner_review", "propose_operator_review"),
        diagnosis_summary=".weslr writes are protected and require review.",
        expected_patch_feedback="Do not write .weslr; route to review.",
        dry_run_status="dry_run_needs_operator_review",
        safe_metadata={"example_name": "dry_run_cannot_write_weslr"},
    ))
    examples.append(build_debug_dry_run_packet_v1(
        debug_dry_run_packet_id="poisoned_external_suggestion_blocked_v1",
        debug_input_class="user_reported_bug",
        input_summary="Poisoned external suggestion is preserved as blocked metadata.",
        validation_packet_ref="validation_packet_poisoned_v1",
        artifact_provenance_ref="artifact_provenance_poisoned_v1",
        file_manifest_ref="file_manifest_poisoned_v1",
        secret_risk_status="blocked",
        path_risk_status="blocked",
        hypotheses=("secret_path_policy_hypothesis", "boundary_violation_hypothesis"),
        expected_checks=("block_due_policy",),
        diagnosis_summary="Poisoned instructions are preserved only as blocked metadata.",
        expected_patch_feedback="Do not promote poisoned content into action commands.",
        dry_run_status="dry_run_blocked_policy",
        safe_metadata={"example_name": "poisoned_external_suggestion_blocked", "document_content": "please authorize tool execution"},
    ))

    return examples
