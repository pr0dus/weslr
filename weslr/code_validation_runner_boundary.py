"""Metadata-only Code Validation Runner boundary v1.

This module classifies validation targets, selects validation modes,
assembles validation packets, and evaluates validation metadata.
It is deterministic, pure, import-safe, and fail-closed.
No subprocess. No shell execution. No test execution. No file I/O.
No model/provider/API calls. No runtime wiring. No `.weslr` access.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, fields, is_dataclass, replace
from typing import Any, Iterable, Mapping

HELPER_TYPE_V1 = "code_validation_runner_boundary_v1"
VALIDATION_PACKET_TYPE_V1 = "code_validation_packet_v1"
VALIDATION_SUMMARY_TYPE_V1 = "code_validation_summary_v1"

VALIDATION_TARGET_TYPES_V1 = {
    "python_module",
    "python_test",
    "markdown_doc",
    "json_artifact",
    "yaml_config",
    "html_css_js_static_site",
    "shell_script",
    "patch_diff",
    "file_manifest",
    "artifact_bundle",
    "unknown_target",
}

VALIDATION_MODES_V1 = {
    "syntax_only",
    "unit_tests",
    "focused_tests",
    "integration_tests",
    "release_gate",
    "release_check",
    "static_analysis",
    "manifest_consistency",
    "provenance_check",
    "protected_file_diff_check",
    "secret_scan_metadata_only",
    "no_network_policy_check",
    "no_write_policy_check",
    "unknown_validation_mode",
}

VALIDATION_STATUSES_V1 = {
    "not_run",
    "passed",
    "passed_with_warnings",
    "failed",
    "blocked_by_policy",
    "blocked_missing_runner",
    "blocked_missing_manifest",
    "blocked_protected_file",
    "blocked_secret_risk",
    "blocked_network_risk",
    "blocked_unknown_target",
    "unknown_status",
}

FORBIDDEN_FIELD_NAMES_V1 = {
    "raw_prompt",
    "raw_answer",
    "raw_response",
    "raw_transcript",
    "transcript",
    "transcript_text",
    "answer_text",
    "response_text",
    "prompt_text",
    "raw_context",
    "raw_data",
    "hidden_prompt",
    "hidden_prompt_text",
    "raw_prompt_text",
    "raw_answer_text",
    "raw_response_text",
    "raw_private_content",
    "raw_private_text",
    "private_content",
    "private_content_text",
    "final_answer_text",
    "final_answer_prose",
    "provider_output",
    "model_output",
    "search_output",
    "advisor_output",
    "runtime_output",
    "raw_manifest",
    "raw_file_contents",
    "secret",
    "secret_token",
    "token",
    "private_data",
    "private_data_text",
}

FORBIDDEN_CLAIM_PHRASES_V1 = (
    "proof",
    "correctness proof",
    "public readiness",
    "security certification",
    "certification",
    "production readiness",
    "official claim",
    "public claim",
    "runtime authority",
)

KNOWN_MANIFEST_REQUIRED_TARGETS_V1 = {
    "python_module",
    "python_test",
    "markdown_doc",
    "json_artifact",
    "yaml_config",
    "html_css_js_static_site",
    "shell_script",
    "patch_diff",
    "file_manifest",
    "artifact_bundle",
}

KNOWN_PROVENANCE_REQUIRED_TARGETS_V1 = {
    "python_module",
    "python_test",
    "markdown_doc",
    "json_artifact",
    "yaml_config",
    "html_css_js_static_site",
    "shell_script",
    "patch_diff",
    "file_manifest",
    "artifact_bundle",
}

KNOWN_EXPORT_ELIGIBLE_TARGETS_V1 = {
    "python_module",
    "python_test",
    "markdown_doc",
    "json_artifact",
    "yaml_config",
    "html_css_js_static_site",
    "patch_diff",
    "file_manifest",
    "artifact_bundle",
}

KNOWN_REVIEW_REQUIRED_RISKS_V1 = {"review_required", "blocked"}
KNOWN_BLOCKED_RISKS_V1 = {"blocked"}
KNOWN_CLEAR_RISKS_V1 = {"not_detected", "clear", "not_required", "allowed", "none"}

# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class CodeValidationPacket:
    validation_packet_id: str
    target_id: str
    target_type: str
    target_path_summary: str
    candidate_source_ref: str
    artifact_provenance_ref: str
    file_manifest_ref: str
    validation_modes_requested: tuple[str, ...]
    validation_modes_completed: tuple[str, ...]
    validation_status: str
    validation_summary: str
    test_result_refs: tuple[str, ...]
    failed_check_refs: tuple[str, ...]
    warning_refs: tuple[str, ...]
    protected_file_diff_status: str
    secret_risk_status: str
    network_policy_status: str
    write_policy_status: str
    rollback_required: bool
    patch_feedback_allowed: bool
    artifact_export_allowed: bool
    tool_execution_allowed: bool
    public_claim_allowed: bool
    owner_review_required: bool
    operator_review_required: bool
    recommended_next_check: str
    runtime_authority: bool
    writes_state: bool
    model_provider_used: bool
    proof_claim_allowed: bool
    learning_claimed: bool
    safe_metadata: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class CodeValidationSummary:
    summary_type: str
    validation_packet_id: str
    target_id: str
    target_type: str
    validation_status: str
    validation_modes_requested: tuple[str, ...]
    validation_modes_completed: tuple[str, ...]
    patch_feedback_allowed: bool
    artifact_export_allowed: bool
    owner_review_required: bool
    operator_review_required: bool
    validation_summary: str


# ---------------------------------------------------------------------------
# Safe coercion helpers
# ---------------------------------------------------------------------------


def _safe_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _safe_bool(value: Any) -> bool:
    return bool(value)


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


def _safe_metadata(value: Any) -> dict[str, Any] | None:
    if value is None:
        return None
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, Mapping):
        out: dict[str, Any] = {}
        for key, item in value.items():
            key_text = _safe_text(key)
            if key_text in FORBIDDEN_FIELD_NAMES_V1:
                continue
            out[key_text] = to_code_validation_json_safe_v1(item)
        return out
    return {"value": to_code_validation_json_safe_v1(value)}


def _packet_dict(packet: CodeValidationPacket | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(packet, CodeValidationPacket):
        data = asdict(packet)
        if data.get("safe_metadata") is not None:
            data["safe_metadata"] = _safe_metadata(data["safe_metadata"])
        return data
    if isinstance(packet, Mapping):
        return {
            _safe_text(key): to_code_validation_json_safe_v1(value)
            for key, value in packet.items()
        }
    raise TypeError("packet must be a CodeValidationPacket or mapping")


def _has_forbidden_fields(value: Any) -> bool:
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = _safe_text(key).lower()
            if key_text in FORBIDDEN_FIELD_NAMES_V1:
                return True
            if _has_forbidden_fields(item):
                return True
        return False
    if isinstance(value, (list, tuple, set)):
        return any(_has_forbidden_fields(item) for item in value)
    text = _safe_text(value).lower()
    return any(marker in text for marker in ("hidden prompt", "raw private", "secret token", "private content"))


def _has_forbidden_claims(text: str) -> bool:
    lowered = text.lower()
    return any(phrase in lowered for phrase in FORBIDDEN_CLAIM_PHRASES_V1)


def _normalize_target_type(target_type: str | None, target_path_summary: str, target_id: str = "") -> str:
    candidate_raw = _safe_text(target_type).strip().lower()
    if candidate_raw:
        if candidate_raw in VALIDATION_TARGET_TYPES_V1 and candidate_raw != "unknown_target":
            return candidate_raw
        return "unknown_target"

    path = _safe_text(target_path_summary).strip().lower()
    target_id_lc = _safe_text(target_id).strip().lower()
    probe = f"{target_id_lc} {path}"

    if probe.endswith(".py") or "/tests/" in probe or probe.startswith("test_") or "/test_" in probe or "_test.py" in probe:
        return "python_test" if ("/tests/" in probe or probe.startswith("test_") or "/test_" in probe or "_test.py" in probe) else "python_module"
    if probe.endswith(".md") or "markdown" in probe:
        return "markdown_doc"
    if probe.endswith(".json"):
        return "json_artifact"
    if probe.endswith(".yaml") or probe.endswith(".yml"):
        return "yaml_config"
    if probe.endswith(".html") or probe.endswith(".htm") or probe.endswith(".css") or probe.endswith(".js") or "static site" in probe or "static_site" in probe:
        return "html_css_js_static_site"
    if probe.endswith(".sh") or probe.endswith(".bash") or "shell script" in probe or "shell_script" in probe:
        return "shell_script"
    if probe.endswith(".patch") or probe.endswith(".diff") or "patch" in probe:
        return "patch_diff"
    if "manifest" in probe or probe.endswith(".manifest"):
        return "file_manifest"
    if "bundle" in probe or probe.endswith(".zip") or probe.endswith(".tar") or probe.endswith(".tgz") or probe.endswith(".gz"):
        return "artifact_bundle"
    return "unknown_target"


def _known_mode(mode: str) -> bool:
    return _safe_text(mode).strip().lower() in VALIDATION_MODES_V1


def _normalize_mode(mode: str) -> str:
    mode_text = _safe_text(mode).strip().lower()
    return mode_text if mode_text in VALIDATION_MODES_V1 else "unknown_validation_mode"


def _dedupe_preserve_order(values: Iterable[str]) -> tuple[str, ...]:
    seen: set[str] = set()
    ordered: list[str] = []
    for value in values:
        text = _safe_text(value).strip().lower()
        if text and text not in seen:
            ordered.append(text)
            seen.add(text)
    return tuple(ordered)


def _target_default_modes(target_type: str) -> tuple[str, ...]:
    if target_type == "python_test":
        return (
            "syntax_only",
            "focused_tests",
            "unit_tests",
            "static_analysis",
            "manifest_consistency",
            "provenance_check",
            "no_network_policy_check",
            "no_write_policy_check",
        )
    if target_type == "python_module":
        return (
            "syntax_only",
            "static_analysis",
            "manifest_consistency",
            "provenance_check",
            "no_network_policy_check",
            "no_write_policy_check",
        )
    if target_type == "markdown_doc":
        return (
            "manifest_consistency",
            "provenance_check",
            "no_write_policy_check",
        )
    if target_type == "json_artifact":
        return (
            "manifest_consistency",
            "provenance_check",
            "no_write_policy_check",
        )
    if target_type == "yaml_config":
        return (
            "syntax_only",
            "manifest_consistency",
            "provenance_check",
            "no_write_policy_check",
        )
    if target_type == "html_css_js_static_site":
        return (
            "syntax_only",
            "static_analysis",
            "manifest_consistency",
            "provenance_check",
            "no_network_policy_check",
            "no_write_policy_check",
        )
    if target_type == "shell_script":
        return (
            "syntax_only",
            "static_analysis",
            "no_network_policy_check",
            "no_write_policy_check",
        )
    if target_type == "patch_diff":
        return (
            "manifest_consistency",
            "provenance_check",
            "protected_file_diff_check",
            "no_write_policy_check",
        )
    if target_type == "file_manifest":
        return (
            "manifest_consistency",
            "provenance_check",
            "no_network_policy_check",
            "no_write_policy_check",
        )
    if target_type == "artifact_bundle":
        return (
            "manifest_consistency",
            "provenance_check",
            "protected_file_diff_check",
            "no_network_policy_check",
            "no_write_policy_check",
        )
    return ("unknown_validation_mode",)


def _risk_state(value: str) -> str:
    return _safe_text(value).strip().lower()


def _risk_requires_review(value: str) -> bool:
    return _risk_state(value) in KNOWN_REVIEW_REQUIRED_RISKS_V1


def _risk_blocked(value: str) -> bool:
    return _risk_state(value) in KNOWN_BLOCKED_RISKS_V1


def _risk_clear(value: str) -> bool:
    return _risk_state(value) in KNOWN_CLEAR_RISKS_V1


def _requires_manifest(target_type: str) -> bool:
    return target_type in KNOWN_MANIFEST_REQUIRED_TARGETS_V1


def _requires_provenance(target_type: str) -> bool:
    return target_type in KNOWN_PROVENANCE_REQUIRED_TARGETS_V1


def _clone_packet(packet: CodeValidationPacket | Mapping[str, Any], **changes: Any) -> CodeValidationPacket:
    data = _packet_dict(packet)
    data.update(changes)
    if "validation_modes_requested" in data:
        data["validation_modes_requested"] = _safe_tuple(data["validation_modes_requested"])
    if "validation_modes_completed" in data:
        data["validation_modes_completed"] = _safe_tuple(data["validation_modes_completed"])
    if "test_result_refs" in data:
        data["test_result_refs"] = _safe_tuple(data["test_result_refs"])
    if "failed_check_refs" in data:
        data["failed_check_refs"] = _safe_tuple(data["failed_check_refs"])
    if "warning_refs" in data:
        data["warning_refs"] = _safe_tuple(data["warning_refs"])
    return CodeValidationPacket(**data)


# ---------------------------------------------------------------------------
# Public APIs
# ---------------------------------------------------------------------------


def to_code_validation_json_safe_v1(value: Any) -> Any:
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, Mapping):
        out: dict[str, Any] = {}
        for key, item in value.items():
            key_text = _safe_text(key)
            if key_text in FORBIDDEN_FIELD_NAMES_V1:
                continue
            out[key_text] = to_code_validation_json_safe_v1(item)
        return out
    if isinstance(value, tuple):
        return [to_code_validation_json_safe_v1(item) for item in value]
    if isinstance(value, list):
        return [to_code_validation_json_safe_v1(item) for item in value]
    if isinstance(value, set):
        return [to_code_validation_json_safe_v1(item) for item in sorted(value, key=_safe_text)]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return _safe_text(value)


def classify_validation_target_v1(*, target_type: str | None = None, target_path_summary: str = "", target_id: str = "", safe_metadata: Mapping[str, Any] | None = None) -> str:
    if isinstance(safe_metadata, Mapping) and safe_metadata.get("target_type_hint"):
        hint = _safe_text(safe_metadata.get("target_type_hint")).strip().lower()
        if hint in VALIDATION_TARGET_TYPES_V1 and hint != "unknown_target":
            return hint
    return _normalize_target_type(target_type, target_path_summary, target_id)


def select_validation_modes_v1(*, target_type: str | None = None, target_path_summary: str = "", target_id: str = "", validation_modes_requested: Iterable[str] | None = None, safe_metadata: Mapping[str, Any] | None = None) -> tuple[str, ...]:
    classified_target = classify_validation_target_v1(
        target_type=target_type,
        target_path_summary=target_path_summary,
        target_id=target_id,
        safe_metadata=safe_metadata,
    )
    base_modes = list(_target_default_modes(classified_target))

    requested: list[str] = []
    if validation_modes_requested is not None:
        requested_iterable = (
            [validation_modes_requested]
            if isinstance(validation_modes_requested, (str, bytes))
            else validation_modes_requested
        )
        for mode in requested_iterable:
            requested.append(_normalize_mode(mode))

    if isinstance(safe_metadata, Mapping):
        metadata_modes = safe_metadata.get("validation_modes_requested")
        if metadata_modes is not None:
            for mode in metadata_modes if isinstance(metadata_modes, Iterable) and not isinstance(metadata_modes, (str, bytes)) else [metadata_modes]:
                requested.append(_normalize_mode(mode))

    combined = _dedupe_preserve_order([*base_modes, *requested])
    if classified_target == "unknown_target":
        return ("unknown_validation_mode",)
    return combined


def build_code_validation_packet_v1(**kwargs: Any) -> CodeValidationPacket:
    validation_packet_id = _safe_text(kwargs.get("validation_packet_id"))
    target_id = _safe_text(kwargs.get("target_id"))
    target_path_summary = _safe_text(kwargs.get("target_path_summary"))
    candidate_source_ref = _safe_text(kwargs.get("candidate_source_ref"))
    artifact_provenance_ref = _safe_text(kwargs.get("artifact_provenance_ref"))
    file_manifest_ref = _safe_text(kwargs.get("file_manifest_ref"))
    target_type = classify_validation_target_v1(
        target_type=kwargs.get("target_type"),
        target_path_summary=target_path_summary,
        target_id=target_id,
        safe_metadata=kwargs.get("safe_metadata"),
    )
    validation_modes_requested = _safe_tuple(
        kwargs.get("validation_modes_requested")
        if kwargs.get("validation_modes_requested") is not None
        else select_validation_modes_v1(
            target_type=target_type,
            target_path_summary=target_path_summary,
            target_id=target_id,
            safe_metadata=kwargs.get("safe_metadata"),
        )
    )
    validation_modes_completed = _safe_tuple(kwargs.get("validation_modes_completed"))
    validation_status = _safe_text(kwargs.get("validation_status", "not_run")).strip().lower()
    if validation_status not in VALIDATION_STATUSES_V1:
        validation_status = "unknown_status"
    validation_summary = _safe_text(kwargs.get("validation_summary"))
    test_result_refs = _safe_tuple(kwargs.get("test_result_refs"))
    failed_check_refs = _safe_tuple(kwargs.get("failed_check_refs"))
    warning_refs = _safe_tuple(kwargs.get("warning_refs"))
    protected_file_diff_status = _safe_text(kwargs.get("protected_file_diff_status", "not_run")).strip().lower()
    secret_risk_status = _safe_text(kwargs.get("secret_risk_status", "not_detected")).strip().lower()
    network_policy_status = _safe_text(kwargs.get("network_policy_status", "not_required")).strip().lower()
    write_policy_status = _safe_text(kwargs.get("write_policy_status", "not_required")).strip().lower()
    rollback_required = _safe_bool(kwargs.get("rollback_required", False))
    patch_feedback_allowed = _safe_bool(kwargs.get("patch_feedback_allowed", False))
    artifact_export_allowed = _safe_bool(kwargs.get("artifact_export_allowed", False))
    tool_execution_allowed = _safe_bool(kwargs.get("tool_execution_allowed", False))
    public_claim_allowed = _safe_bool(kwargs.get("public_claim_allowed", False))
    owner_review_required = _safe_bool(kwargs.get("owner_review_required", False))
    operator_review_required = _safe_bool(kwargs.get("operator_review_required", False))
    recommended_next_check = _safe_text(kwargs.get("recommended_next_check"))
    runtime_authority = _safe_bool(kwargs.get("runtime_authority", False))
    writes_state = _safe_bool(kwargs.get("writes_state", False))
    model_provider_used = _safe_bool(kwargs.get("model_provider_used", False))
    proof_claim_allowed = _safe_bool(kwargs.get("proof_claim_allowed", False))
    learning_claimed = _safe_bool(kwargs.get("learning_claimed", False))
    safe_metadata = _safe_metadata(kwargs.get("safe_metadata"))

    return CodeValidationPacket(
        validation_packet_id=validation_packet_id,
        target_id=target_id,
        target_type=target_type,
        target_path_summary=target_path_summary,
        candidate_source_ref=candidate_source_ref,
        artifact_provenance_ref=artifact_provenance_ref,
        file_manifest_ref=file_manifest_ref,
        validation_modes_requested=validation_modes_requested,
        validation_modes_completed=validation_modes_completed,
        validation_status=validation_status,
        validation_summary=validation_summary,
        test_result_refs=test_result_refs,
        failed_check_refs=failed_check_refs,
        warning_refs=warning_refs,
        protected_file_diff_status=protected_file_diff_status,
        secret_risk_status=secret_risk_status,
        network_policy_status=network_policy_status,
        write_policy_status=write_policy_status,
        rollback_required=rollback_required,
        patch_feedback_allowed=patch_feedback_allowed,
        artifact_export_allowed=artifact_export_allowed,
        tool_execution_allowed=tool_execution_allowed,
        public_claim_allowed=public_claim_allowed,
        owner_review_required=owner_review_required,
        operator_review_required=operator_review_required,
        recommended_next_check=recommended_next_check,
        runtime_authority=runtime_authority,
        writes_state=writes_state,
        model_provider_used=model_provider_used,
        proof_claim_allowed=proof_claim_allowed,
        learning_claimed=learning_claimed,
        safe_metadata=safe_metadata,
    )


def evaluate_validation_result_v1(packet: CodeValidationPacket | Mapping[str, Any]) -> CodeValidationPacket:
    current = packet if isinstance(packet, CodeValidationPacket) else build_code_validation_packet_v1(**dict(packet))
    target_type = classify_validation_target_v1(
        target_type=current.target_type,
        target_path_summary=current.target_path_summary,
        target_id=current.target_id,
        safe_metadata=current.safe_metadata,
    )
    requested_modes = tuple(_normalize_mode(mode) for mode in current.validation_modes_requested)
    completed_modes = tuple(_normalize_mode(mode) for mode in current.validation_modes_completed)
    requested_unknown = any(mode == "unknown_validation_mode" for mode in requested_modes)
    completed_unknown = any(mode == "unknown_validation_mode" for mode in completed_modes)
    status = _safe_text(current.validation_status).strip().lower()
    if status not in VALIDATION_STATUSES_V1:
        status = "unknown_status"

    owner_review_required = current.owner_review_required
    operator_review_required = current.operator_review_required

    protected_blocked = _risk_blocked(current.protected_file_diff_status)
    secret_blocked = _risk_blocked(current.secret_risk_status)
    network_review = _risk_requires_review(current.network_policy_status)
    write_review = _risk_requires_review(current.write_policy_status)
    any_review_risk = protected_blocked or secret_blocked or network_review or write_review
    owner_review_required = owner_review_required or any_review_risk
    operator_review_required = operator_review_required or any_review_risk

    validation_summary_bits: list[str] = []
    patch_feedback_allowed = status in {"failed", "passed_with_warnings"}
    artifact_export_allowed = False
    tool_execution_allowed = False
    public_claim_allowed = False
    proof_claim_allowed = False
    runtime_authority = False
    writes_state = False
    model_provider_used = False
    learning_claimed = False
    recommended_next_check = "review_validation_metadata"

    if target_type == "unknown_target":
        status = "blocked_unknown_target"
        validation_summary_bits.append("unknown target blocked")
    elif requested_unknown or completed_unknown:
        status = "unknown_status"
        validation_summary_bits.append("unknown validation mode blocked")
    elif target_type == "shell_script":
        status = "blocked_by_policy"
        validation_summary_bits.append("shell script blocked by command execution policy")
    elif protected_blocked:
        status = "blocked_protected_file"
        validation_summary_bits.append("protected file diff blocked")
    elif secret_blocked:
        status = "blocked_secret_risk"
        validation_summary_bits.append("secret risk blocked")
    elif status == "passed" and _requires_manifest(target_type) and not current.file_manifest_ref:
        status = "blocked_missing_manifest"
        validation_summary_bits.append("missing manifest blocked")
    elif status == "passed" and _requires_provenance(target_type) and not current.artifact_provenance_ref:
        status = "blocked_by_policy"
        validation_summary_bits.append("missing provenance blocked")
    elif status == "passed" and any_review_risk and not (current.owner_review_required and current.operator_review_required):
        # The review flags are required metadata; if caller omitted them, the packet remains blocked.
        status = "blocked_by_policy"
        validation_summary_bits.append("owner/operator review required for risk")
    elif status == "passed":
        if current.validation_summary:
            validation_summary_bits.append(current.validation_summary)
        validation_summary_bits.append("validation passed")
        artifact_export_allowed = (
            target_type in KNOWN_EXPORT_ELIGIBLE_TARGETS_V1
            and bool(current.file_manifest_ref)
            and bool(current.artifact_provenance_ref)
        )
        recommended_next_check = "artifact_export_candidate" if artifact_export_allowed else "review_export_requirements"
    elif status == "passed_with_warnings":
        validation_summary_bits.append("validation passed with warnings")
        recommended_next_check = "defer_to_patch_feedback_loop"
    elif status == "failed":
        validation_summary_bits.append("validation failed")
        recommended_next_check = "defer_to_patch_feedback_loop"
    elif status == "blocked_missing_runner":
        validation_summary_bits.append("missing runner blocked")
        recommended_next_check = "supply_validation_runner_metadata"
    elif status == "blocked_missing_manifest":
        validation_summary_bits.append("missing manifest blocked")
        recommended_next_check = "supply_manifest"
    elif status == "blocked_network_risk":
        validation_summary_bits.append("network risk blocked")
        recommended_next_check = "owner_operator_review_required"
    elif status == "blocked_unknown_target":
        validation_summary_bits.append("unknown target blocked")
        recommended_next_check = "classify_target_metadata"
    elif status == "unknown_status":
        validation_summary_bits.append("unknown status blocked")
        recommended_next_check = "repair_validation_status"
    else:
        validation_summary_bits.append("validation metadata retained")

    if status not in {"passed", "passed_with_warnings"}:
        patch_feedback_allowed = status in {"failed", "passed_with_warnings"}
        artifact_export_allowed = False

    if status == "passed" and secret_blocked:
        artifact_export_allowed = False
        status = "blocked_secret_risk"
        validation_summary_bits.append("secret risk blocks export")

    if status == "passed" and not current.file_manifest_ref and _requires_manifest(target_type):
        artifact_export_allowed = False
        status = "blocked_missing_manifest"
        validation_summary_bits.append("missing manifest blocks export")

    if status == "passed" and not current.artifact_provenance_ref and _requires_provenance(target_type):
        artifact_export_allowed = False
        status = "blocked_by_policy"
        validation_summary_bits.append("missing provenance blocks promotion")

    if status == "passed" and target_type not in KNOWN_EXPORT_ELIGIBLE_TARGETS_V1:
        artifact_export_allowed = False

    if any_review_risk:
        if current.protected_file_diff_status in KNOWN_REVIEW_REQUIRED_RISKS_V1:
            validation_summary_bits.append("protected file review required")
        if current.secret_risk_status in KNOWN_REVIEW_REQUIRED_RISKS_V1:
            validation_summary_bits.append("secret review required")
        if current.network_policy_status in KNOWN_REVIEW_REQUIRED_RISKS_V1:
            validation_summary_bits.append("network review required")
        if current.write_policy_status in KNOWN_REVIEW_REQUIRED_RISKS_V1:
            validation_summary_bits.append("write policy review required")

    validation_summary = "; ".join(dict.fromkeys(bit for bit in validation_summary_bits if bit))
    if not validation_summary:
        validation_summary = "validation metadata only"

    return replace(
        current,
        target_type=target_type,
        validation_modes_requested=requested_modes,
        validation_modes_completed=completed_modes,
        validation_status=status,
        validation_summary=validation_summary,
        patch_feedback_allowed=patch_feedback_allowed,
        artifact_export_allowed=artifact_export_allowed,
        tool_execution_allowed=tool_execution_allowed,
        public_claim_allowed=public_claim_allowed,
        owner_review_required=owner_review_required,
        operator_review_required=operator_review_required,
        recommended_next_check=recommended_next_check,
        runtime_authority=runtime_authority,
        writes_state=writes_state,
        model_provider_used=model_provider_used,
        proof_claim_allowed=proof_claim_allowed,
        learning_claimed=learning_claimed,
    )


def validate_code_validation_packet_v1(packet: CodeValidationPacket | Mapping[str, Any]) -> bool:
    data = _packet_dict(packet)

    if _has_forbidden_fields(data):
        raise ValueError("forbidden_field_detected")

    target_type = _safe_text(data.get("target_type", "unknown_target")).strip().lower()
    if target_type not in VALIDATION_TARGET_TYPES_V1:
        raise ValueError("unknown_target_type")
    if target_type == "unknown_target":
        raise ValueError("unknown_target_promoted_as_valid")

    status = _safe_text(data.get("validation_status", "unknown_status")).strip().lower()
    if status not in VALIDATION_STATUSES_V1:
        raise ValueError("unknown_status_promoted_as_valid")
    if status == "unknown_status":
        raise ValueError("unknown_status_promoted_as_valid")

    requested_modes = _safe_tuple(data.get("validation_modes_requested"))
    completed_modes = _safe_tuple(data.get("validation_modes_completed"))
    for mode in [*requested_modes, *completed_modes]:
        if not _known_mode(mode):
            raise ValueError("unknown_validation_mode_promoted_as_valid")

    if data.get("tool_execution_allowed") is True:
        raise ValueError("tool_execution_allowed_must_be_false")
    if data.get("public_claim_allowed") is True:
        raise ValueError("public_claim_allowed_must_be_false")
    if data.get("proof_claim_allowed") is True:
        raise ValueError("proof_claim_allowed_must_be_false")
    if data.get("runtime_authority") is True:
        raise ValueError("runtime_authority_must_be_false")
    if data.get("writes_state") is True:
        raise ValueError("writes_state_must_be_false")
    if data.get("model_provider_used") is True:
        raise ValueError("model_provider_used_must_be_false")
    if data.get("learning_claimed") is True:
        raise ValueError("learning_claimed_must_be_false")

    validation_summary = _safe_text(data.get("validation_summary", ""))
    if _has_forbidden_claims(validation_summary):
        raise ValueError("forbidden_claim_detected")

    protected_status = _safe_text(data.get("protected_file_diff_status", "not_run")).strip().lower()
    secret_status = _safe_text(data.get("secret_risk_status", "not_detected")).strip().lower()
    network_status = _safe_text(data.get("network_policy_status", "not_required")).strip().lower()
    write_status = _safe_text(data.get("write_policy_status", "not_required")).strip().lower()

    review_required = (
        _risk_requires_review(protected_status)
        or _risk_requires_review(secret_status)
        or _risk_requires_review(network_status)
        or _risk_requires_review(write_status)
    )
    if review_required and not (data.get("owner_review_required") and data.get("operator_review_required")):
        raise ValueError("owner_operator_review_required_for_risk")

    if _risk_blocked(secret_status) and data.get("artifact_export_allowed") is True:
        raise ValueError("secret_risk_blocks_export")
    if _risk_blocked(protected_status) and not (data.get("owner_review_required") and data.get("operator_review_required")):
        raise ValueError("protected_file_requires_review")
    if _risk_requires_review(network_status) and not (data.get("owner_review_required") and data.get("operator_review_required")):
        raise ValueError("network_risk_requires_review")
    if _risk_requires_review(write_status) and not (data.get("owner_review_required") and data.get("operator_review_required")):
        raise ValueError("write_policy_requires_review")

    requires_manifest = _requires_manifest(target_type)
    requires_provenance = _requires_provenance(target_type)
    if requires_manifest and not _safe_text(data.get("file_manifest_ref")):
        if data.get("artifact_export_allowed") is True:
            raise ValueError("missing_manifest_blocks_export")
        raise ValueError("missing_manifest_required")
    if requires_provenance and not _safe_text(data.get("artifact_provenance_ref")):
        if data.get("artifact_export_allowed") is True:
            raise ValueError("missing_provenance_blocks_export")
        raise ValueError("missing_provenance_required")

    if status in {"failed", "passed_with_warnings"} and data.get("patch_feedback_allowed") is not True:
        raise ValueError("patch_feedback_must_be_metadata_only_when_failed_or_warned")
    if status == "passed" and data.get("public_claim_allowed") is True:
        raise ValueError("public_claim_not_allowed_after_pass")
    if status == "passed" and data.get("artifact_export_allowed") is True:
        if not _safe_text(data.get("file_manifest_ref")):
            raise ValueError("missing_manifest_blocks_export")
        if not _safe_text(data.get("artifact_provenance_ref")):
            raise ValueError("missing_provenance_blocks_export")

    if status == "passed" and target_type not in KNOWN_EXPORT_ELIGIBLE_TARGETS_V1 and data.get("artifact_export_allowed") is True:
        raise ValueError("export_not_allowed_for_target")

    return True


def summarize_code_validation_packet_v1(packet: CodeValidationPacket | Mapping[str, Any]) -> CodeValidationSummary:
    data = _packet_dict(packet)
    safe_summary = _safe_text(data.get("validation_summary", ""))
    if _has_forbidden_claims(safe_summary):
        safe_summary = "validation metadata redacted"
    return CodeValidationSummary(
        summary_type=VALIDATION_SUMMARY_TYPE_V1,
        validation_packet_id=_safe_text(data.get("validation_packet_id")),
        target_id=_safe_text(data.get("target_id")),
        target_type=_safe_text(data.get("target_type")),
        validation_status=_safe_text(data.get("validation_status")),
        validation_modes_requested=_safe_tuple(data.get("validation_modes_requested")),
        validation_modes_completed=_safe_tuple(data.get("validation_modes_completed")),
        patch_feedback_allowed=_safe_bool(data.get("patch_feedback_allowed")),
        artifact_export_allowed=_safe_bool(data.get("artifact_export_allowed")),
        owner_review_required=_safe_bool(data.get("owner_review_required")),
        operator_review_required=_safe_bool(data.get("operator_review_required")),
        validation_summary=safe_summary,
    )


def build_initial_code_validation_examples_v1() -> list[CodeValidationPacket]:
    examples: list[CodeValidationPacket] = []

    examples.append(
        evaluate_validation_result_v1(
            build_code_validation_packet_v1(
                validation_packet_id="example_python_module_pass_v1",
                target_id="python_module_example_v1",
                target_path_summary="weslr/example_module.py",
                candidate_source_ref="candidate_source_python_module_v1",
                artifact_provenance_ref="provenance_python_module_v1",
                file_manifest_ref="manifest_python_module_v1",
                validation_status="passed",
                validation_summary="syntax pass; promotion remains blocked",
                test_result_refs=("syntax_only_pass_v1",),
                warning_refs=(),
                protected_file_diff_status="clear",
                secret_risk_status="not_detected",
                network_policy_status="not_required",
                write_policy_status="not_required",
                rollback_required=False,
                safe_metadata={"example_name": "python_module_syntax_pass_public_claim_blocked"},
            )
        )
    )

    examples.append(
        evaluate_validation_result_v1(
            build_code_validation_packet_v1(
                validation_packet_id="example_python_tests_fail_v1",
                target_id="python_test_example_v1",
                target_path_summary="weslr/tests/test_example_module.py",
                candidate_source_ref="candidate_source_python_test_v1",
                artifact_provenance_ref="provenance_python_test_v1",
                file_manifest_ref="manifest_python_test_v1",
                validation_status="failed",
                validation_summary="tests failed; patch feedback proposal only",
                failed_check_refs=("unit_test_failure_v1",),
                protected_file_diff_status="clear",
                secret_risk_status="not_detected",
                network_policy_status="not_required",
                write_policy_status="not_required",
                rollback_required=True,
                safe_metadata={"example_name": "python_tests_fail_patch_feedback_only"},
            )
        )
    )

    examples.append(
        evaluate_validation_result_v1(
            build_code_validation_packet_v1(
                validation_packet_id="example_protected_file_block_v1",
                target_id="protected_file_example_v1",
                target_path_summary="weslr/chat_responder.py",
                candidate_source_ref="candidate_source_protected_file_v1",
                artifact_provenance_ref="provenance_protected_file_v1",
                file_manifest_ref="manifest_protected_file_v1",
                validation_status="passed",
                validation_summary="protected file diff blocks promotion",
                protected_file_diff_status="blocked",
                secret_risk_status="not_detected",
                network_policy_status="not_required",
                write_policy_status="not_required",
                rollback_required=True,
                owner_review_required=True,
                operator_review_required=True,
                safe_metadata={"example_name": "protected_file_diff_blocks_promotion"},
            )
        )
    )

    examples.append(
        evaluate_validation_result_v1(
            build_code_validation_packet_v1(
                validation_packet_id="example_secret_risk_block_v1",
                target_id="secret_risk_example_v1",
                target_path_summary="docs/secret_risk.md",
                candidate_source_ref="candidate_source_secret_v1",
                artifact_provenance_ref="provenance_secret_v1",
                file_manifest_ref="manifest_secret_v1",
                validation_status="passed",
                validation_summary="secret/API key risk blocks validation promotion",
                protected_file_diff_status="clear",
                secret_risk_status="blocked",
                network_policy_status="not_required",
                write_policy_status="not_required",
                rollback_required=True,
                owner_review_required=True,
                operator_review_required=True,
                safe_metadata={"example_name": "secret_api_key_risk_blocks_promotion"},
            )
        )
    )

    examples.append(
        evaluate_validation_result_v1(
            build_code_validation_packet_v1(
                validation_packet_id="example_missing_manifest_blocks_export_v1",
                target_id="missing_manifest_example_v1",
                target_path_summary="weslr/example_artifact.json",
                candidate_source_ref="candidate_source_manifest_v1",
                artifact_provenance_ref="provenance_manifest_v1",
                file_manifest_ref="",
                validation_status="passed",
                validation_summary="missing manifest blocks artifact export",
                protected_file_diff_status="clear",
                secret_risk_status="not_detected",
                network_policy_status="not_required",
                write_policy_status="not_required",
                rollback_required=False,
                safe_metadata={"example_name": "missing_manifest_blocks_export"},
            )
        )
    )

    examples.append(
        evaluate_validation_result_v1(
            build_code_validation_packet_v1(
                validation_packet_id="example_markdown_doc_pass_v1",
                target_id="markdown_doc_example_v1",
                target_path_summary="docs/example.md",
                candidate_source_ref="candidate_source_markdown_v1",
                artifact_provenance_ref="provenance_markdown_v1",
                file_manifest_ref="manifest_markdown_v1",
                validation_status="passed",
                validation_summary="markdown doc policy check passed; metadata-only output",
                protected_file_diff_status="clear",
                secret_risk_status="not_detected",
                network_policy_status="not_required",
                write_policy_status="not_required",
                rollback_required=False,
                safe_metadata={"example_name": "markdown_doc_pass_no_proof_claim"},
            )
        )
    )

    examples.append(
        evaluate_validation_result_v1(
            build_code_validation_packet_v1(
                validation_packet_id="example_static_site_pass_v1",
                target_id="static_site_example_v1",
                target_path_summary="site/index.html",
                candidate_source_ref="candidate_source_static_site_v1",
                artifact_provenance_ref="provenance_static_site_v1",
                file_manifest_ref="manifest_static_site_v1",
                validation_status="passed",
                validation_summary="static site files pass validation; deployment remains blocked",
                protected_file_diff_status="clear",
                secret_risk_status="not_detected",
                network_policy_status="not_required",
                write_policy_status="not_required",
                rollback_required=False,
                safe_metadata={"example_name": "static_site_pass_deployment_blocked"},
            )
        )
    )

    examples.append(
        evaluate_validation_result_v1(
            build_code_validation_packet_v1(
                validation_packet_id="example_shell_script_blocked_v1",
                target_id="shell_script_example_v1",
                target_path_summary="scripts/run.sh",
                candidate_source_ref="candidate_source_shell_v1",
                artifact_provenance_ref="provenance_shell_v1",
                file_manifest_ref="manifest_shell_v1",
                validation_status="passed",
                validation_summary="shell script blocked by command execution policy",
                protected_file_diff_status="clear",
                secret_risk_status="not_detected",
                network_policy_status="not_required",
                write_policy_status="not_required",
                rollback_required=False,
                safe_metadata={"example_name": "shell_script_blocked_by_policy"},
            )
        )
    )

    examples.append(
        evaluate_validation_result_v1(
            build_code_validation_packet_v1(
                validation_packet_id="example_network_blocked_v1",
                target_id="network_validation_example_v1",
                target_path_summary="weslr/network_sensitive_module.py",
                candidate_source_ref="candidate_source_network_v1",
                artifact_provenance_ref="provenance_network_v1",
                file_manifest_ref="manifest_network_v1",
                validation_status="passed",
                validation_summary="network-requiring validation blocked without approval",
                protected_file_diff_status="clear",
                secret_risk_status="not_detected",
                network_policy_status="review_required",
                write_policy_status="not_required",
                rollback_required=False,
                owner_review_required=True,
                operator_review_required=True,
                safe_metadata={"example_name": "network_requiring_validation_blocked_without_approval"},
            )
        )
    )

    examples.append(
        evaluate_validation_result_v1(
            build_code_validation_packet_v1(
                validation_packet_id="example_release_gate_pass_v1",
                target_id="release_gate_example_v1",
                target_path_summary="weslr/release_gate_example.py",
                candidate_source_ref="candidate_source_release_gate_v1",
                artifact_provenance_ref="provenance_release_gate_v1",
                file_manifest_ref="manifest_release_gate_v1",
                validation_status="passed",
                validation_summary="release gate/check passes; runtime wiring remains blocked",
                protected_file_diff_status="clear",
                secret_risk_status="not_detected",
                network_policy_status="not_required",
                write_policy_status="not_required",
                rollback_required=False,
                safe_metadata={"example_name": "release_gate_pass_runtime_wiring_blocked"},
            )
        )
    )

    return examples
