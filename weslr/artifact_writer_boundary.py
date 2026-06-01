"""Metadata-only artifact writer boundary v1.

This module separates generation capability from filesystem authority.
It is pure, deterministic, import-safe, and fail-closed.
No file writes. No directories. No deletes. No deployment.
No subprocess. No model/provider/search/advisor calls.
No chat routing. No runtime behavior changes. No `.weslr` access.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from hashlib import sha256
import re
from typing import Any, Iterable, Mapping

from weslr.code_scaffold_generator import (
    build_initial_code_scaffold_examples_v1,
    build_code_scaffold_from_file_manifest_v1,
    to_code_scaffold_json_safe_v1,
)
from weslr.file_manifest_builder import build_initial_file_manifest_examples_v1

HELPER_TYPE_V1 = "artifact_writer_boundary_v1"
ARTIFACT_WRITE_REQUEST_TYPE_V1 = "artifact_write_request_v1"
ARTIFACT_WRITE_DECISION_TYPE_V1 = "artifact_write_decision_v1"
ARTIFACT_WRITE_SUMMARY_TYPE_V1 = "artifact_write_summary_v1"

ALLOWED_CAPABILITY_CLASSES_V1 = {
    "plan_artifact",
    "generate_content_packet",
    "prepare_file_manifest",
    "prepare_scaffold",
    "prepare_validation_plan",
    "prepare_patch_plan",
    "prepare_export_bundle",
    "write_sandbox_files",
    "edit_generated_files",
    "validate_artifact",
    "package_artifact",
    "deploy_or_publish",
}

ALLOWED_WRITE_MODES_V1 = {
    "dry_run",
    "sandbox_create_only",
    "sandbox_edit_generated_only",
    "owner_approved_create",
    "owner_approved_edit",
    "owner_approved_delete",
    "blocked",
}

ALLOWED_OVERWRITE_POLICIES_V1 = {
    "no_overwrite",
    "overwrite_generated_only",
    "owner_approval_required",
    "blocked",
}

ALLOWED_DECISIONS_V1 = {
    "allow_dry_run_only",
    "allow_sandbox_create",
    "allow_owner_approved_create",
    "allow_owner_approved_edit",
    "requires_owner_approval",
    "requires_operator_approval",
    "blocked_path_violation",
    "blocked_protected_file",
    "blocked_secret_or_private_data",
    "blocked_executable",
    "blocked_dependency_install",
    "blocked_deployment",
    "blocked_public_publish",
    "blocked_runtime_authority",
    "blocked_unknown",
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
    "raw_prompt_text",
    "raw_answer_text",
    "raw_response_text",
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
    "private_data",
    "private_data_text",
}

FORBIDDEN_CLAIM_PHRASES_V1 = (
    "public iss",
    "iss wording",
    "public intelligence claim",
    "public readiness claim",
    "agi claim",
    "consciousness claim",
    "sentience claim",
    "turing claim",
    "official turing",
    "turing test",
    "certification claim",
)

CLAIM_BASE_TERMS_V1 = {"agi", "consciousness", "sentience", "turing", "certification"}
CLAIM_QUALIFIERS_V1 = {"claim", "claims", "claimed", "official", "certification", "certified", "public", "readiness"}
UNSAFE_DEPLOYMENT_TERMS_V1 = {"deploy", "deployment", "rollout", "bypass", "evade"}
UNSAFE_DEPLOYMENT_PHRASES_V1 = {"unsafe deployment", "covert rollout", "deployment before review"}
COVERT_TRACKING_MARKERS_V1 = {"covert tracking", "tracking implementation", "tracking pipeline", "hidden tracking", "surveillance"}
DIAGNOSIS_TREATMENT_TERMS_V1 = {"diagnosis", "diagnose", "diagnostic", "treatment", "prescribe", "prescription"}
PROTECTED_EXACT_PATHS_V1 = {
    "weslr/chat_responder.py",
    "weslr/main.py",
    "dialogue.py",
    "chat_ui.py",
    ".weslr",
    ".env",
}
PROTECTED_PATH_SUFFIXES_V1 = {".pem", ".key", ".p12", ".pfx", ".pkcs12"}
PROTECTED_PATH_MARKERS_V1 = {
    "/.weslr",
    ".weslr/",
    "/.env",
    ".env/",
    "secrets/",
    "secret/",
    "token/",
    "tokens/",
    "credentials/",
    "credential/",
}
LARGE_REQUEST_FILE_COUNT_THRESHOLD_V1 = 12
LARGE_REQUEST_TOTAL_SIZE_THRESHOLD_V1 = 20000


class ValidationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ArtifactWriteRequest:
    write_request_id: str
    source_scaffold_id: str
    source_manifest_id: str
    project_title: str
    requested_root: str
    allowed_root: str
    requested_entries: list[dict[str, Any]]
    write_mode: str
    overwrite_policy: str
    create_directories_requested: bool
    edit_existing_files_requested: bool
    delete_requested: bool
    executable_files_requested: bool
    dependency_install_requested: bool
    test_execution_requested: bool
    deployment_requested: bool
    public_publish_requested: bool
    owner_approval_present: bool
    operator_approval_present: bool
    sandbox_only: bool
    dry_run_only: bool
    risk_labels: list[str]
    boundary_requirements: list[str]
    capability_class: str
    requested_file_count: int
    requested_total_size_estimate: int
    quality_preservation_notes: list[str]
    public_claim_allowed: bool
    iss_internal_reference_allowed: bool
    learning_claimed: bool
    runtime_authority: bool
    writes_state: bool
    model_provider_used: bool
    safe_metadata: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class ArtifactWriteDecision:
    write_decision_id: str
    write_request_id: str
    decision: str
    allowed_entries: list[dict[str, Any]]
    blocked_entries: list[dict[str, Any]]
    requires_owner_approval_entries: list[dict[str, Any]]
    requires_operator_approval_entries: list[dict[str, Any]]
    selected_root: str
    effective_write_mode: str
    effective_overwrite_policy: str
    dry_run_required: bool
    sandbox_required: bool
    directory_creation_allowed: bool
    file_creation_allowed: bool
    file_edit_allowed: bool
    file_delete_allowed: bool
    executable_creation_allowed: bool
    dependency_install_allowed: bool
    test_execution_allowed: bool
    deployment_allowed: bool
    public_publish_allowed: bool
    blocked_reasons: list[str]
    required_approvals: list[str]
    path_safety_result: dict[str, Any]
    protected_file_result: dict[str, Any]
    secret_scan_result: dict[str, Any]
    private_data_scan_result: dict[str, Any]
    recommended_next_step: str
    capability_class: str
    artifact_generation_allowed: bool
    can_generate_packet: bool
    can_write_if_authorized: bool
    blocked_action_only: bool
    capability_not_denied: bool
    safe_alternative_available: bool
    safe_alternative_mode: str
    future_authority_path: list[str]
    chunking_required: bool
    requested_file_count: int
    requested_total_size_estimate: int
    quality_preservation_notes: list[str]
    runtime_authority: bool
    writes_state: bool
    model_provider_used: bool
    public_claim_allowed: bool
    learning_claimed: bool
    safe_metadata: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class ArtifactWriteDecisionSummary:
    summary_type: str
    write_decision_id: str
    decision: str
    capability_class: str
    blocked_reason_count: int
    blocked_reasons: list[str]
    artifact_generation_allowed: bool
    capability_not_denied: bool
    safe_alternative_available: bool
    recommended_next_step: str


# ---------------------------------------------------------------------------
# Safe helpers
# ---------------------------------------------------------------------------


def _safe_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (str, int, float)):
        return str(value).strip()
    return default if value == "" else str(value).strip()


def _normalize_text(value: Any) -> str:
    return " ".join(_safe_text(value).split()).lower()


def _dedupe_preserve(items: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        text = _normalize_text(item)
        if text and text not in seen:
            seen.add(text)
            out.append(text)
    return out


def _normalize_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        items = [value]
    elif isinstance(value, Mapping):
        items = [str(v) for v in value.values()]
    else:
        try:
            items = [str(item) for item in value]
        except TypeError:
            items = [str(value)]
    return _dedupe_preserve(items)


def _json_safe(value: Any) -> Any:
    if is_dataclass(value):
        return _json_safe(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, set):
        return [_json_safe(item) for item in sorted(value, key=_safe_text)]
    return value


def _as_mapping(value: Any) -> Mapping[str, Any]:
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, Mapping):
        return value
    raise ValidationError("value_must_be_dataclass_or_mapping")


def _contains_forbidden_fields(value: Any, path: str = "") -> list[str]:
    blocked: list[str] = []
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = _safe_text(key).lower()
            next_path = f"{path}.{key_text}" if path else key_text
            if key_text in FORBIDDEN_FIELD_NAMES_V1:
                blocked.append(next_path)
            blocked.extend(_contains_forbidden_fields(item, next_path))
    elif isinstance(value, (list, tuple, set)):
        for index, item in enumerate(value):
            blocked.extend(_contains_forbidden_fields(item, f"{path}[{index}]"))
    return blocked


def _contains_negated_phrase(value: str, phrase: str) -> bool:
    text = _normalize_text(value)
    phrase_words = _normalize_text(phrase).split()
    if not phrase_words:
        return False
    tokens = text.split()
    negators = {"no", "not", "without", "never"}
    for index in range(0, len(tokens) - len(phrase_words) + 1):
        if tokens[index : index + len(phrase_words)] == phrase_words:
            window = tokens[max(0, index - 3) : index]
            if any(token in negators or token.endswith("-no") or token.endswith("-not") for token in window):
                return True
    return False


def _contains_negated_marker(value: str, marker: str) -> bool:
    text = _normalize_text(value)
    for prefix in ("no ", "not ", "without ", "never ", "no-", "not-", "without-", "never-"):
        if f"{prefix}{marker}" in text:
            return True
    compact = re.sub(r"[\s/]+", "-", text)
    for prefix in ("no-", "not-", "without-", "never-"):
        if f"{prefix}{marker}" in compact:
            return True
    return False


def _contains_forbidden_claim_marker(value: Any) -> bool:
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, Mapping):
        return any(_contains_forbidden_claim_marker(item) for item in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(_contains_forbidden_claim_marker(item) for item in value)
    if isinstance(value, str):
        blob = _normalize_text(value)
        if any(phrase in blob and not _contains_negated_phrase(blob, phrase) for phrase in FORBIDDEN_CLAIM_PHRASES_V1):
            if not any(_contains_negated_marker(blob, term) for term in CLAIM_BASE_TERMS_V1):
                return True
        has_base = any(term in blob for term in CLAIM_BASE_TERMS_V1)
        has_qualifier = any(term in blob for term in CLAIM_QUALIFIERS_V1)
        if not (has_base and has_qualifier):
            return False
        if any(_contains_negated_marker(blob, term) for term in CLAIM_BASE_TERMS_V1):
            return False
        return True
    return False


def _contains_unsafe_deployment_marker(value: Any) -> bool:
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, Mapping):
        return any(_contains_unsafe_deployment_marker(item) for item in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(_contains_unsafe_deployment_marker(item) for item in value)
    if isinstance(value, str):
        blob = _normalize_text(value)
        if any(phrase in blob for phrase in UNSAFE_DEPLOYMENT_PHRASES_V1):
            return True
        return any(term in blob and not _contains_negated_marker(blob, term) for term in UNSAFE_DEPLOYMENT_TERMS_V1)
    return False


def _contains_covert_tracking_marker(value: Any) -> bool:
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, Mapping):
        return any(_contains_covert_tracking_marker(item) for item in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(_contains_covert_tracking_marker(item) for item in value)
    if isinstance(value, str):
        blob = _normalize_text(value)
        return any(marker in blob and not _contains_negated_marker(blob, marker) for marker in COVERT_TRACKING_MARKERS_V1)
    return False


def _contains_diagnosis_treatment_marker(value: Any) -> bool:
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, Mapping):
        return any(_contains_diagnosis_treatment_marker(item) for item in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(_contains_diagnosis_treatment_marker(item) for item in value)
    if isinstance(value, str):
        blob = _normalize_text(value)
        return any(marker in blob and not _contains_negated_marker(blob, marker) for marker in DIAGNOSIS_TREATMENT_TERMS_V1)
    return False


def _normalize_path(path: str) -> str:
    return path.replace("\\", "/").strip()


def _is_safe_relative_path(path: str) -> bool:
    text = _normalize_path(_safe_text(path))
    if not text:
        return False
    if text.startswith(("/", "~", "./", "../")):
        return False
    if re.match(r"^[a-zA-Z]:", text):
        return False
    parts = [part for part in text.split("/") if part]
    if not parts:
        return False
    for part in parts:
        if part in {".", ".."}:
            return False
        if part.startswith("~"):
            return False
    return True


def _is_protected_path(path: str) -> bool:
    text = _normalize_path(_safe_text(path)).lower()
    if text in PROTECTED_EXACT_PATHS_V1:
        return True
    if text.startswith(".weslr/") or text.startswith(".env/"):
        return True
    if any(marker in text for marker in PROTECTED_PATH_MARKERS_V1):
        return True
    basename = text.rsplit("/", 1)[-1]
    if any(token in basename for token in ("secret", "token", "credential", "private_key", "id_rsa", "id_ed25519")):
        return True
    if any(basename.endswith(suffix) for suffix in PROTECTED_PATH_SUFFIXES_V1):
        return True
    return False


def _slugify(value: Any) -> str:
    text = _normalize_text(value)
    return "".join(ch if ch.isalnum() else "-" for ch in text).strip("-") or "unknown"


def _deterministic_id(*parts: Any, prefix: str) -> str:
    digest = sha256("|".join(_safe_text(part) for part in parts).encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{digest}"


def _entry_from_any(value: Any) -> dict[str, Any]:
    mapping = _as_mapping(value)
    safe_metadata = mapping.get("safe_metadata", None)
    if safe_metadata is not None and not isinstance(safe_metadata, Mapping):
        raise ValidationError("entry_safe_metadata_must_be_mapping")
    return {
        "path": _safe_text(mapping.get("path")),
        "file_type": _safe_text(mapping.get("file_type")),
        "content_kind": _safe_text(mapping.get("content_kind")),
        "content": _safe_text(mapping.get("content")),
        "generation_method": _safe_text(mapping.get("generation_method")),
        "overwrite_allowed": bool(mapping.get("overwrite_allowed")),
        "executable": bool(mapping.get("executable")),
        "contains_secret": bool(mapping.get("contains_secret")),
        "contains_private_data": bool(mapping.get("contains_private_data")),
        "validation_command": _safe_text(mapping.get("validation_command")),
        "owner_approval_required": bool(mapping.get("owner_approval_required", True)),
        "safe_metadata": dict(safe_metadata or {}),
    }


def _source_to_scaffold(source: Any):
    mapping = None
    try:
        mapping = _as_mapping(source)
    except ValidationError:
        mapping = None
    if mapping is not None and "generated_entries" in mapping:
        return source
    if mapping is not None and "file_entries" in mapping:
        return build_code_scaffold_from_file_manifest_v1(source)
    if hasattr(source, "generated_entries") and hasattr(source, "scaffold_type"):
        return source
    if hasattr(source, "file_entries") and hasattr(source, "manifest_type"):
        return build_code_scaffold_from_file_manifest_v1(source)
    raise ValidationError("source_must_be_file_manifest_or_code_scaffold")


def _entry_snapshot(entry: Mapping[str, Any], *, blocked_reason: str | None = None) -> dict[str, Any]:
    snap = {
        "path": _safe_text(entry.get("path")),
        "file_type": _safe_text(entry.get("file_type")),
        "content_kind": _safe_text(entry.get("content_kind")),
        "generation_method": _safe_text(entry.get("generation_method")),
        "owner_approval_required": bool(entry.get("owner_approval_required", True)),
    }
    if blocked_reason:
        snap["blocked_reason"] = blocked_reason
    return snap


def _default_quality_notes() -> list[str]:
    return _dedupe_preserve(
        [
            "preserve manifest lineage",
            "preserve scaffold lineage",
            "preserve per-file purpose",
            "preserve validation markers",
            "preserve provenance metadata",
        ]
    )


def _default_future_authority_path() -> list[str]:
    return _dedupe_preserve(
        [
            "owner approval",
            "sandbox create",
            "validate",
            "patch loop",
            "export",
        ]
    )


def _make_request_entries_from_scaffold(scaffold: Any) -> list[dict[str, Any]]:
    scaffold_map = to_code_scaffold_json_safe_v1(scaffold)
    return [_entry_from_any(entry) for entry in scaffold_map.get("generated_entries", [])]


def _default_requested_root(project_title: str, source_scaffold_id: str) -> str:
    return f"sandbox_artifacts/{_slugify(project_title or source_scaffold_id)}"


def _summarize_scan(entries: list[dict[str, Any]], field_name: str) -> dict[str, Any]:
    blocked = [entry["path"] for entry in entries if bool(entry.get(field_name))]
    return {
        "status": "blocked" if blocked else "clear",
        "blocked_paths": blocked,
        "count": len(blocked),
    }


def _classify_global_block(request: ArtifactWriteRequest) -> tuple[str | None, str | None]:
    if request.runtime_authority:
        return "blocked_runtime_authority", "runtime_authority_requested"
    if request.dependency_install_requested:
        return "blocked_dependency_install", "dependency_install_requested"
    if request.public_publish_requested:
        return "blocked_public_publish", "public_publish_requested"
    if request.deployment_requested:
        return "blocked_deployment", "deployment_requested"
    if request.executable_files_requested:
        return "blocked_executable", "executable_files_requested"
    if request.delete_requested:
        return "blocked_unknown", "delete_requested_requires_separate_boundary"
    return None, None


def _request_like(value: Any) -> ArtifactWriteRequest:
    if isinstance(value, ArtifactWriteRequest):
        return value
    mapping = _as_mapping(value)
    safe_metadata = mapping.get("safe_metadata", None)
    if safe_metadata is not None and not isinstance(safe_metadata, Mapping):
        raise ValidationError("safe_metadata_must_be_mapping")
    requested_entries = [_entry_from_any(item) for item in mapping.get("requested_entries", [])]
    return ArtifactWriteRequest(
        write_request_id=_safe_text(mapping.get("write_request_id")),
        source_scaffold_id=_safe_text(mapping.get("source_scaffold_id")),
        source_manifest_id=_safe_text(mapping.get("source_manifest_id")),
        project_title=_safe_text(mapping.get("project_title")),
        requested_root=_safe_text(mapping.get("requested_root")),
        allowed_root=_safe_text(mapping.get("allowed_root")),
        requested_entries=requested_entries,
        write_mode=_safe_text(mapping.get("write_mode")),
        overwrite_policy=_safe_text(mapping.get("overwrite_policy")),
        create_directories_requested=bool(mapping.get("create_directories_requested")),
        edit_existing_files_requested=bool(mapping.get("edit_existing_files_requested")),
        delete_requested=bool(mapping.get("delete_requested")),
        executable_files_requested=bool(mapping.get("executable_files_requested")),
        dependency_install_requested=bool(mapping.get("dependency_install_requested")),
        test_execution_requested=bool(mapping.get("test_execution_requested")),
        deployment_requested=bool(mapping.get("deployment_requested")),
        public_publish_requested=bool(mapping.get("public_publish_requested")),
        owner_approval_present=bool(mapping.get("owner_approval_present")),
        operator_approval_present=bool(mapping.get("operator_approval_present")),
        sandbox_only=bool(mapping.get("sandbox_only")),
        dry_run_only=bool(mapping.get("dry_run_only")),
        risk_labels=_normalize_list(mapping.get("risk_labels")),
        boundary_requirements=_normalize_list(mapping.get("boundary_requirements")),
        capability_class=_safe_text(mapping.get("capability_class")),
        requested_file_count=int(mapping.get("requested_file_count") or 0),
        requested_total_size_estimate=int(mapping.get("requested_total_size_estimate") or 0),
        quality_preservation_notes=_normalize_list(mapping.get("quality_preservation_notes")),
        public_claim_allowed=bool(mapping.get("public_claim_allowed")),
        iss_internal_reference_allowed=bool(mapping.get("iss_internal_reference_allowed")),
        learning_claimed=bool(mapping.get("learning_claimed")),
        runtime_authority=bool(mapping.get("runtime_authority")),
        writes_state=bool(mapping.get("writes_state")),
        model_provider_used=bool(mapping.get("model_provider_used")),
        safe_metadata=dict(safe_metadata or {}),
    )


# ---------------------------------------------------------------------------
# Public APIs
# ---------------------------------------------------------------------------


def build_artifact_write_request_v1(source: Any, **overrides: Any) -> ArtifactWriteRequest:
    scaffold = _source_to_scaffold(source)
    scaffold_map = to_code_scaffold_json_safe_v1(scaffold)
    source_scaffold_id = _safe_text(scaffold_map.get("scaffold_id") or scaffold_map.get("source_manifest_id"))
    source_manifest_id = _safe_text(scaffold_map.get("source_manifest_id"))
    project_title = _safe_text(scaffold_map.get("project_title"))
    request_entries = overrides.get("requested_entries")
    if request_entries is None:
        request_entries = _make_request_entries_from_scaffold(scaffold)
    else:
        request_entries = [_entry_from_any(entry) for entry in request_entries]
    requested_root = _safe_text(overrides.get("requested_root") or _default_requested_root(project_title, source_scaffold_id))
    allowed_root = _safe_text(overrides.get("allowed_root") or requested_root)
    write_mode = _safe_text(overrides.get("write_mode") or "dry_run")
    overwrite_policy = _safe_text(overrides.get("overwrite_policy") or "no_overwrite")
    capability_class = _safe_text(overrides.get("capability_class") or "prepare_scaffold")
    quality_notes = _normalize_list(overrides.get("quality_preservation_notes") or _default_quality_notes())
    if len(request_entries) > LARGE_REQUEST_FILE_COUNT_THRESHOLD_V1 or sum(len(_safe_text(entry.get("content"))) for entry in request_entries) > LARGE_REQUEST_TOTAL_SIZE_THRESHOLD_V1:
        if "chunking required" not in quality_notes:
            quality_notes.append("chunking required")
    request = ArtifactWriteRequest(
        write_request_id=_deterministic_id(source_scaffold_id, source_manifest_id, project_title, requested_root, write_mode, capability_class, prefix="awreq"),
        source_scaffold_id=source_scaffold_id,
        source_manifest_id=source_manifest_id,
        project_title=project_title,
        requested_root=requested_root,
        allowed_root=allowed_root,
        requested_entries=request_entries,
        write_mode=write_mode,
        overwrite_policy=overwrite_policy,
        create_directories_requested=bool(overrides.get("create_directories_requested", False)),
        edit_existing_files_requested=bool(overrides.get("edit_existing_files_requested", False)),
        delete_requested=bool(overrides.get("delete_requested", False)),
        executable_files_requested=bool(overrides.get("executable_files_requested", False)),
        dependency_install_requested=bool(overrides.get("dependency_install_requested", False)),
        test_execution_requested=bool(overrides.get("test_execution_requested", False)),
        deployment_requested=bool(overrides.get("deployment_requested", False)),
        public_publish_requested=bool(overrides.get("public_publish_requested", False)),
        owner_approval_present=bool(overrides.get("owner_approval_present", False)),
        operator_approval_present=bool(overrides.get("operator_approval_present", False)),
        sandbox_only=bool(overrides.get("sandbox_only", write_mode.startswith("sandbox"))),
        dry_run_only=bool(overrides.get("dry_run_only", write_mode == "dry_run")),
        risk_labels=_normalize_list(overrides.get("risk_labels") or scaffold_map.get("risk_labels") or []),
        boundary_requirements=_normalize_list(overrides.get("boundary_requirements") or scaffold_map.get("boundary_requirements") or []),
        capability_class=capability_class,
        requested_file_count=int(overrides.get("requested_file_count") or len(request_entries)),
        requested_total_size_estimate=int(overrides.get("requested_total_size_estimate") or sum(len(_safe_text(entry.get("content"))) for entry in request_entries)),
        quality_preservation_notes=quality_notes,
        public_claim_allowed=bool(overrides.get("public_claim_allowed", False)),
        iss_internal_reference_allowed=bool(overrides.get("iss_internal_reference_allowed", True)),
        learning_claimed=bool(overrides.get("learning_claimed", False)),
        runtime_authority=bool(overrides.get("runtime_authority", False)),
        writes_state=bool(overrides.get("writes_state", False)),
        model_provider_used=bool(overrides.get("model_provider_used", False)),
        safe_metadata={
            **(scaffold_map.get("safe_metadata") or {}),
            **dict(overrides.get("safe_metadata") or {}),
            "source_scaffold_type": _safe_text(scaffold_map.get("scaffold_type")),
            "source_scaffold_id": source_scaffold_id,
            "source_manifest_id": source_manifest_id,
            "requested_root": requested_root,
            "allowed_root": allowed_root,
            "requested_file_count": len(request_entries),
        },
    )
    validate_artifact_write_request_v1(request)
    return request


def validate_artifact_write_request_v1(request: Any) -> bool:
    original = _as_mapping(request)
    forbidden = _contains_forbidden_fields(original)
    if forbidden:
        raise ValidationError(f"forbidden_field_detected:{forbidden[0]}")
    normalized = _request_like(request)
    if _contains_forbidden_claim_marker(normalized):
        raise ValidationError("forbidden_claim_marker_detected")
    if normalized.public_claim_allowed:
        raise ValidationError("public_claim_allowed_must_be_false")
    if normalized.runtime_authority:
        raise ValidationError("runtime_authority_must_be_false")
    if normalized.writes_state:
        raise ValidationError("writes_state_must_be_false")
    if normalized.model_provider_used:
        raise ValidationError("model_provider_used_must_be_false")
    if normalized.learning_claimed:
        raise ValidationError("learning_claimed_must_be_false")
    if not normalized.write_request_id:
        raise ValidationError("write_request_id_required")
    if not normalized.source_scaffold_id:
        raise ValidationError("source_scaffold_id_required")
    if not normalized.source_manifest_id:
        raise ValidationError("source_manifest_id_required")
    if not normalized.project_title:
        raise ValidationError("project_title_required")
    if not _is_safe_relative_path(normalized.requested_root):
        raise ValidationError("requested_root_must_be_safe_relative_path")
    if not _is_safe_relative_path(normalized.allowed_root):
        raise ValidationError("allowed_root_must_be_safe_relative_path")
    if normalized.write_mode not in ALLOWED_WRITE_MODES_V1:
        raise ValidationError("unknown_write_mode")
    if normalized.overwrite_policy not in ALLOWED_OVERWRITE_POLICIES_V1:
        raise ValidationError("unknown_overwrite_policy")
    if normalized.capability_class not in ALLOWED_CAPABILITY_CLASSES_V1:
        raise ValidationError("unknown_capability_class")
    if normalized.requested_file_count < 0:
        raise ValidationError("requested_file_count_must_be_non_negative")
    if normalized.requested_total_size_estimate < 0:
        raise ValidationError("requested_total_size_estimate_must_be_non_negative")
    if normalized.requested_file_count != len(normalized.requested_entries):
        raise ValidationError("requested_file_count_mismatch")
    if not normalized.requested_entries:
        raise ValidationError("requested_entries_required")
    if not normalized.quality_preservation_notes:
        raise ValidationError("quality_preservation_notes_required")
    for field_name in (
        "create_directories_requested",
        "edit_existing_files_requested",
        "delete_requested",
        "executable_files_requested",
        "dependency_install_requested",
        "test_execution_requested",
        "deployment_requested",
        "public_publish_requested",
        "owner_approval_present",
        "operator_approval_present",
        "sandbox_only",
        "dry_run_only",
    ):
        if type(getattr(normalized, field_name)) is not bool:
            raise ValidationError(f"{field_name}_must_be_bool")
    if normalized.safe_metadata is not None and not isinstance(normalized.safe_metadata, dict):
        raise ValidationError("safe_metadata_must_be_mapping")
    for entry in normalized.requested_entries:
        if not _safe_text(entry.get("path")):
            raise ValidationError("entry_path_required")
        if not _safe_text(entry.get("file_type")):
            raise ValidationError("entry_file_type_required")
        if not _safe_text(entry.get("content_kind")):
            raise ValidationError("entry_content_kind_required")
        if not _safe_text(entry.get("content")):
            raise ValidationError("entry_content_required")
        if not _safe_text(entry.get("generation_method")):
            raise ValidationError("entry_generation_method_required")
        if not _safe_text(entry.get("validation_command")):
            raise ValidationError("entry_validation_command_required")
        if entry.get("safe_metadata") is None or not isinstance(entry.get("safe_metadata"), dict):
            raise ValidationError("entry_safe_metadata_required")
        if type(entry.get("overwrite_allowed")) is not bool:
            raise ValidationError("entry_overwrite_allowed_must_be_bool")
        if type(entry.get("executable")) is not bool:
            raise ValidationError("entry_executable_must_be_bool")
        if type(entry.get("contains_secret")) is not bool:
            raise ValidationError("entry_contains_secret_must_be_bool")
        if type(entry.get("contains_private_data")) is not bool:
            raise ValidationError("entry_contains_private_data_must_be_bool")
        if type(entry.get("owner_approval_required")) is not bool:
            raise ValidationError("entry_owner_approval_required_must_be_bool")
        if not _is_safe_relative_path(entry.get("path")):
            raise ValidationError("unsafe_entry_path")
        if entry.get("path", "").lower() in {".env", ".weslr"}:
            raise ValidationError("protected_path_allowed")
        if _is_protected_path(entry.get("path", "")):
            raise ValidationError("protected_path_allowed")
        if entry.get("contains_secret"):
            raise ValidationError("contains_secret_must_be_false")
        if entry.get("contains_private_data"):
            raise ValidationError("contains_private_data_must_be_false")
    return True


def evaluate_artifact_write_boundary_v1(write_request: Any) -> ArtifactWriteDecision:
    request = _request_like(write_request)
    validation_error = None
    try:
        validate_artifact_write_request_v1(request)
    except ValidationError as exc:
        validation_error = exc
        message = _safe_text(exc)
        path_boundary_tokens = (
            "requested_root_must_be_safe_relative_path",
            "allowed_root_must_be_safe_relative_path",
            "unsafe_entry_path",
            "protected_path_allowed",
            "entry_path_required",
            "contains_secret_must_be_false",
            "contains_private_data_must_be_false",
        )
        if not any(token in message for token in path_boundary_tokens):
            raise

    allowed_entries: list[dict[str, Any]] = []
    blocked_entries: list[dict[str, Any]] = []
    requires_owner_approval_entries: list[dict[str, Any]] = []
    requires_operator_approval_entries: list[dict[str, Any]] = []
    blocked_reasons: list[str] = []

    root_safe = _is_safe_relative_path(request.requested_root) and _is_safe_relative_path(request.allowed_root)
    selected_root = request.allowed_root if root_safe else request.requested_root

    path_blocked = []
    protected_blocked = []
    secret_blocked = []
    private_blocked = []
    for entry in request.requested_entries:
        snapshot = _entry_snapshot(entry)
        path = _safe_text(entry.get("path"))
        if not _is_safe_relative_path(path):
            path_blocked.append(snapshot)
            blocked_entries.append({**snapshot, "blocked_reason": "path_violation"})
            continue
        if _is_protected_path(path):
            protected_blocked.append(snapshot)
            blocked_entries.append({**snapshot, "blocked_reason": "protected_file"})
            continue
        if bool(entry.get("contains_secret")):
            secret_blocked.append(snapshot)
            blocked_entries.append({**snapshot, "blocked_reason": "secret_data"})
            continue
        if bool(entry.get("contains_private_data")):
            private_blocked.append(snapshot)
            blocked_entries.append({**snapshot, "blocked_reason": "private_data"})
            continue
        allowed_entries.append(snapshot)

    if path_blocked:
        blocked_reasons.append("path_violation")
    if protected_blocked:
        blocked_reasons.append("protected_file")
    if secret_blocked:
        blocked_reasons.append("secret_or_private_data")
    if private_blocked:
        blocked_reasons.append("private_data")

    if request.deployment_requested:
        blocked_reasons.append("deployment_requested")
    if request.public_publish_requested:
        blocked_reasons.append("public_publish_requested")
    if request.dependency_install_requested:
        blocked_reasons.append("dependency_install_requested")
    if request.executable_files_requested:
        blocked_reasons.append("executable_files_requested")
    if request.delete_requested:
        blocked_reasons.append("delete_requested")
    if request.test_execution_requested:
        blocked_reasons.append("test_execution_requested")
    if request.runtime_authority:
        blocked_reasons.append("runtime_authority_requested")

    for label in request.risk_labels:
        if label in {"covert_tracking", "diagnosis_treatment", "deployment", "public_publish"}:
            blocked_reasons.append(f"risk:{label}")

    blocked_reasons = _dedupe_preserve(blocked_reasons)

    safe_alternative_available = True
    safe_alternative_mode = "dry_run" if request.dry_run_only else "sandbox_create_only"
    recommended_next_step = "prepare dry-run review"
    decision = "allow_dry_run_only"
    dry_run_required = True
    sandbox_required = bool(request.sandbox_only or request.create_directories_requested or request.edit_existing_files_requested)
    directory_creation_allowed = False
    file_creation_allowed = False
    file_edit_allowed = False
    file_delete_allowed = False
    executable_creation_allowed = False
    dependency_install_allowed = False
    test_execution_allowed = False
    deployment_allowed = False
    public_publish_allowed = False
    required_approvals = []

    global_block, global_reason = _classify_global_block(request)
    if path_blocked:
        decision = "blocked_path_violation"
        safe_alternative_mode = "prepare_patch_plan"
        recommended_next_step = "prepare patch plan"
        blocked_action_only = True
    elif protected_blocked:
        decision = "blocked_protected_file"
        safe_alternative_mode = "prepare_patch_plan"
        recommended_next_step = "prepare patch plan"
        blocked_action_only = True
    elif secret_blocked or private_blocked:
        decision = "blocked_secret_or_private_data"
        safe_alternative_mode = "config_example_yaml"
        recommended_next_step = "prepare redacted config example"
        blocked_action_only = True
    elif global_block:
        decision = global_block
        blocked_reasons.append(global_reason or global_block)
        safe_alternative_mode = {
            "blocked_runtime_authority": "prepare_patch_plan",
            "blocked_dependency_install": "prepare_dependency_review",
            "blocked_public_publish": "prepare_local_preview",
            "blocked_deployment": "prepare_local_preview",
            "blocked_executable": "prepare_placeholder_only",
            "blocked_unknown": "prepare_patch_plan",
        }.get(global_block, "prepare_patch_plan")
        recommended_next_step = {
            "blocked_runtime_authority": "prepare patch plan",
            "blocked_dependency_install": "prepare dependency review",
            "blocked_public_publish": "prepare local preview",
            "blocked_deployment": "prepare local preview",
            "blocked_executable": "prepare placeholder-only scaffold",
            "blocked_unknown": "prepare review request",
        }.get(global_block, "prepare review request")
        safe_alternative_available = True
        blocked_action_only = True
    else:
        if request.delete_requested:
            decision = "blocked_unknown"
            recommended_next_step = "prepare separate deletion boundary"
            safe_alternative_mode = "archive_or_patch_plan"
            blocked_action_only = True
        elif request.requested_file_count > LARGE_REQUEST_FILE_COUNT_THRESHOLD_V1 or request.requested_total_size_estimate > LARGE_REQUEST_TOTAL_SIZE_THRESHOLD_V1:
            chunking_needed = True
            if request.owner_approval_present:
                decision = "allow_owner_approved_create" if not request.edit_existing_files_requested else "allow_owner_approved_edit"
            else:
                decision = "requires_owner_approval"
            required_approvals.append("owner_approval")
            safe_alternative_mode = "chunked_sandbox_create_only"
            recommended_next_step = "chunk and request owner approval"
            blocked_action_only = True
        elif request.dry_run_only:
            decision = "allow_dry_run_only"
            recommended_next_step = "keep as metadata-only packet"
            blocked_action_only = bool(blocked_reasons)
        elif request.sandbox_only:
            sandbox_required = True
            if request.owner_approval_present:
                decision = "allow_sandbox_create"
                recommended_next_step = "write to sandbox only"
            else:
                decision = "requires_owner_approval"
                required_approvals.append("owner_approval")
                recommended_next_step = "request owner approval for sandbox create"
            blocked_action_only = bool(blocked_reasons)
        elif request.edit_existing_files_requested:
            sandbox_required = True
            if request.owner_approval_present:
                decision = "allow_owner_approved_edit"
                recommended_next_step = "edit generated files only"
            else:
                decision = "requires_owner_approval"
                required_approvals.append("owner_approval")
                recommended_next_step = "request owner approval for edits"
            blocked_action_only = bool(blocked_reasons)
        elif request.create_directories_requested:
            sandbox_required = True
            if request.owner_approval_present:
                decision = "allow_owner_approved_create"
                recommended_next_step = "create sandbox files only"
            else:
                decision = "requires_owner_approval"
                required_approvals.append("owner_approval")
                recommended_next_step = "request owner approval for create"
            blocked_action_only = bool(blocked_reasons)
        else:
            decision = "allow_dry_run_only"
            recommended_next_step = "keep as metadata-only packet"
            blocked_action_only = bool(blocked_reasons)

    if request.public_publish_requested:
        decision = "blocked_public_publish"
    if request.deployment_requested:
        decision = "blocked_deployment"
    if request.dependency_install_requested:
        decision = "blocked_dependency_install"
    if request.executable_files_requested:
        decision = "blocked_executable"

    if decision.startswith("allow_") and request.owner_approval_present:
        required_approvals = []
    if decision.startswith("requires_") and not required_approvals:
        required_approvals = ["owner_approval"]

    artifact_generation_allowed = True
    can_generate_packet = True
    can_write_if_authorized = not (protected_blocked or secret_blocked or private_blocked or request.deployment_requested or request.public_publish_requested or request.dependency_install_requested or request.executable_files_requested or request.delete_requested)
    if request.requested_file_count > LARGE_REQUEST_FILE_COUNT_THRESHOLD_V1 or request.requested_total_size_estimate > LARGE_REQUEST_TOTAL_SIZE_THRESHOLD_V1:
        chunking_required = True
    else:
        chunking_required = False
    if decision in {"allow_dry_run_only", "blocked_deployment", "blocked_public_publish", "blocked_dependency_install", "blocked_executable", "blocked_unknown", "blocked_runtime_authority", "blocked_path_violation", "blocked_protected_file", "blocked_secret_or_private_data"}:
        dry_run_required = True
    else:
        dry_run_required = False
    if decision in {"allow_sandbox_create", "allow_owner_approved_create", "allow_owner_approved_edit"}:
        directory_creation_allowed = True
        file_creation_allowed = decision != "allow_owner_approved_edit"
        file_edit_allowed = decision == "allow_owner_approved_edit"
    capability_not_denied = artifact_generation_allowed and safe_alternative_available
    blocked_action_only = bool(blocked_reasons) and artifact_generation_allowed and safe_alternative_available

    path_safety_result = {
        "status": "blocked" if path_blocked else "clear",
        "blocked_paths": [item["path"] for item in path_blocked],
        "selected_root": selected_root,
    }
    protected_file_result = {
        "status": "blocked" if protected_blocked else "clear",
        "blocked_paths": [item["path"] for item in protected_blocked],
    }
    secret_scan_result = _summarize_scan(blocked_entries, "blocked_reason")
    private_data_scan_result = {
        "status": "blocked" if private_blocked else "clear",
        "blocked_paths": [item["path"] for item in private_blocked],
        "count": len(private_blocked),
    }

    if request.deployment_requested:
        requires_operator_approval_entries = [
            _entry_snapshot(entry, blocked_reason="deployment_requested") for entry in request.requested_entries
        ]
    if request.public_publish_requested:
        requires_operator_approval_entries = [
            _entry_snapshot(entry, blocked_reason="public_publish_requested") for entry in request.requested_entries
        ]
    if request.owner_approval_present is False and decision in {"requires_owner_approval", "allow_owner_approved_create", "allow_owner_approved_edit"}:
        requires_owner_approval_entries = [
            _entry_snapshot(entry, blocked_reason="owner_approval_required") for entry in request.requested_entries
        ]

    future_authority_path = _default_future_authority_path()
    if decision.startswith("blocked_"):
        future_authority_path = _dedupe_preserve([*future_authority_path, "separate boundary", "review blocked action only"])
    elif decision.startswith("requires_"):
        future_authority_path = _dedupe_preserve([*future_authority_path, "owner approval", "sandbox materialization"])

    decision_packet = ArtifactWriteDecision(
        write_decision_id=_deterministic_id(request.write_request_id, decision, selected_root, prefix="awdec"),
        write_request_id=request.write_request_id,
        decision=decision,
        allowed_entries=allowed_entries,
        blocked_entries=blocked_entries,
        requires_owner_approval_entries=requires_owner_approval_entries,
        requires_operator_approval_entries=requires_operator_approval_entries,
        selected_root=selected_root,
        effective_write_mode=request.write_mode if decision.startswith("allow_") else "blocked",
        effective_overwrite_policy=request.overwrite_policy,
        dry_run_required=dry_run_required,
        sandbox_required=sandbox_required,
        directory_creation_allowed=directory_creation_allowed,
        file_creation_allowed=file_creation_allowed,
        file_edit_allowed=file_edit_allowed,
        file_delete_allowed=file_delete_allowed,
        executable_creation_allowed=executable_creation_allowed,
        dependency_install_allowed=dependency_install_allowed,
        test_execution_allowed=test_execution_allowed,
        deployment_allowed=deployment_allowed,
        public_publish_allowed=public_publish_allowed,
        blocked_reasons=blocked_reasons,
        required_approvals=required_approvals,
        path_safety_result=path_safety_result,
        protected_file_result=protected_file_result,
        secret_scan_result=secret_scan_result,
        private_data_scan_result=private_data_scan_result,
        recommended_next_step=recommended_next_step,
        capability_class=request.capability_class,
        artifact_generation_allowed=artifact_generation_allowed,
        can_generate_packet=can_generate_packet,
        can_write_if_authorized=can_write_if_authorized,
        blocked_action_only=blocked_action_only,
        capability_not_denied=capability_not_denied,
        safe_alternative_available=safe_alternative_available,
        safe_alternative_mode=safe_alternative_mode,
        future_authority_path=future_authority_path,
        chunking_required=chunking_required,
        requested_file_count=request.requested_file_count,
        requested_total_size_estimate=request.requested_total_size_estimate,
        quality_preservation_notes=request.quality_preservation_notes,
        runtime_authority=request.runtime_authority,
        writes_state=request.writes_state,
        model_provider_used=request.model_provider_used,
        public_claim_allowed=request.public_claim_allowed,
        learning_claimed=request.learning_claimed,
        safe_metadata={
            **(request.safe_metadata or {}),
            "write_request_id": request.write_request_id,
            "decision": decision,
            "capability_class": request.capability_class,
        },
    )
    validate_artifact_write_decision_v1(decision_packet)
    return decision_packet


def validate_artifact_write_decision_v1(decision: Any) -> bool:
    original = _as_mapping(decision)
    forbidden = _contains_forbidden_fields(original)
    if forbidden:
        raise ValidationError(f"forbidden_field_detected:{forbidden[0]}")
    normalized = _decision_like(decision)
    if _contains_forbidden_claim_marker(normalized):
        raise ValidationError("forbidden_claim_marker_detected")
    if normalized.decision not in ALLOWED_DECISIONS_V1:
        raise ValidationError("unknown_decision")
    if normalized.effective_write_mode not in ALLOWED_WRITE_MODES_V1:
        raise ValidationError("unknown_write_mode")
    if normalized.capability_class not in ALLOWED_CAPABILITY_CLASSES_V1:
        raise ValidationError("unknown_capability_class")
    if normalized.public_claim_allowed:
        raise ValidationError("public_claim_allowed_must_be_false")
    if normalized.runtime_authority:
        raise ValidationError("runtime_authority_must_be_false")
    if normalized.writes_state:
        raise ValidationError("writes_state_must_be_false")
    if normalized.model_provider_used:
        raise ValidationError("model_provider_used_must_be_false")
    if normalized.learning_claimed:
        raise ValidationError("learning_claimed_must_be_false")
    if normalized.deployment_allowed:
        raise ValidationError("deployment_allowed_must_be_false")
    if normalized.public_publish_allowed:
        raise ValidationError("public_publish_allowed_must_be_false")
    if normalized.dependency_install_allowed:
        raise ValidationError("dependency_install_allowed_must_be_false")
    if normalized.file_delete_allowed:
        raise ValidationError("file_delete_allowed_must_be_false")
    if normalized.executable_creation_allowed:
        raise ValidationError("executable_creation_allowed_must_be_false")
    if normalized.test_execution_allowed:
        raise ValidationError("test_execution_allowed_must_be_false")
    if not _is_safe_relative_path(normalized.selected_root):
        raise ValidationError("selected_root_must_be_safe_relative_path")
    if normalized.allowed_entries and any(_is_protected_path(entry.get("path", "")) for entry in normalized.allowed_entries):
        raise ValidationError("protected_path_allowed")
    if normalized.allowed_entries and any(not _is_safe_relative_path(entry.get("path", "")) for entry in normalized.allowed_entries):
        raise ValidationError("unsafe_allowed_path")
    if normalized.allowed_entries and any(_safe_text(entry.get("path")).lower() in {".env", ".weslr"} for entry in normalized.allowed_entries):
        raise ValidationError("protected_path_allowed")
    if normalized.allowed_entries and any(bool(entry.get("contains_secret")) or bool(entry.get("contains_private_data")) for entry in normalized.allowed_entries):
        raise ValidationError("secret_or_private_data_allowed")
    if normalized.blocked_entries and any(not _safe_text(entry.get("blocked_reason")) for entry in normalized.blocked_entries):
        raise ValidationError("blocked_reason_required")
    if normalized.safe_metadata is not None and not isinstance(normalized.safe_metadata, dict):
        raise ValidationError("safe_metadata_must_be_mapping")
    if not _safe_text(normalized.write_decision_id):
        raise ValidationError("write_decision_id_required")
    if not _safe_text(normalized.write_request_id):
        raise ValidationError("write_request_id_required")
    return True


def _decision_like(value: Any) -> ArtifactWriteDecision:
    if isinstance(value, ArtifactWriteDecision):
        return value
    mapping = _as_mapping(value)
    safe_metadata = mapping.get("safe_metadata", None)
    if safe_metadata is not None and not isinstance(safe_metadata, Mapping):
        raise ValidationError("safe_metadata_must_be_mapping")
    return ArtifactWriteDecision(
        write_decision_id=_safe_text(mapping.get("write_decision_id")),
        write_request_id=_safe_text(mapping.get("write_request_id")),
        decision=_safe_text(mapping.get("decision")),
        allowed_entries=[_entry_from_any(item) for item in mapping.get("allowed_entries", [])],
        blocked_entries=[_entry_from_any(item) for item in mapping.get("blocked_entries", [])],
        requires_owner_approval_entries=[_entry_from_any(item) for item in mapping.get("requires_owner_approval_entries", [])],
        requires_operator_approval_entries=[_entry_from_any(item) for item in mapping.get("requires_operator_approval_entries", [])],
        selected_root=_safe_text(mapping.get("selected_root")),
        effective_write_mode=_safe_text(mapping.get("effective_write_mode")),
        effective_overwrite_policy=_safe_text(mapping.get("effective_overwrite_policy")),
        dry_run_required=bool(mapping.get("dry_run_required")),
        sandbox_required=bool(mapping.get("sandbox_required")),
        directory_creation_allowed=bool(mapping.get("directory_creation_allowed")),
        file_creation_allowed=bool(mapping.get("file_creation_allowed")),
        file_edit_allowed=bool(mapping.get("file_edit_allowed")),
        file_delete_allowed=bool(mapping.get("file_delete_allowed")),
        executable_creation_allowed=bool(mapping.get("executable_creation_allowed")),
        dependency_install_allowed=bool(mapping.get("dependency_install_allowed")),
        test_execution_allowed=bool(mapping.get("test_execution_allowed")),
        deployment_allowed=bool(mapping.get("deployment_allowed")),
        public_publish_allowed=bool(mapping.get("public_publish_allowed")),
        blocked_reasons=_normalize_list(mapping.get("blocked_reasons")),
        required_approvals=_normalize_list(mapping.get("required_approvals")),
        path_safety_result=dict(mapping.get("path_safety_result") or {}),
        protected_file_result=dict(mapping.get("protected_file_result") or {}),
        secret_scan_result=dict(mapping.get("secret_scan_result") or {}),
        private_data_scan_result=dict(mapping.get("private_data_scan_result") or {}),
        recommended_next_step=_safe_text(mapping.get("recommended_next_step")),
        capability_class=_safe_text(mapping.get("capability_class")),
        artifact_generation_allowed=bool(mapping.get("artifact_generation_allowed")),
        can_generate_packet=bool(mapping.get("can_generate_packet")),
        can_write_if_authorized=bool(mapping.get("can_write_if_authorized")),
        blocked_action_only=bool(mapping.get("blocked_action_only")),
        capability_not_denied=bool(mapping.get("capability_not_denied")),
        safe_alternative_available=bool(mapping.get("safe_alternative_available")),
        safe_alternative_mode=_safe_text(mapping.get("safe_alternative_mode")),
        future_authority_path=_normalize_list(mapping.get("future_authority_path")),
        chunking_required=bool(mapping.get("chunking_required")),
        requested_file_count=int(mapping.get("requested_file_count") or 0),
        requested_total_size_estimate=int(mapping.get("requested_total_size_estimate") or 0),
        quality_preservation_notes=_normalize_list(mapping.get("quality_preservation_notes")),
        runtime_authority=bool(mapping.get("runtime_authority")),
        writes_state=bool(mapping.get("writes_state")),
        model_provider_used=bool(mapping.get("model_provider_used")),
        public_claim_allowed=bool(mapping.get("public_claim_allowed")),
        learning_claimed=bool(mapping.get("learning_claimed")),
        safe_metadata=dict(safe_metadata or {}),
    )


def summarize_artifact_write_decision_v1(decision: Any) -> ArtifactWriteDecisionSummary:
    normalized = _decision_like(decision)
    return ArtifactWriteDecisionSummary(
        summary_type=ARTIFACT_WRITE_SUMMARY_TYPE_V1,
        write_decision_id=normalized.write_decision_id,
        decision=normalized.decision,
        capability_class=normalized.capability_class,
        blocked_reason_count=len(normalized.blocked_reasons),
        blocked_reasons=normalized.blocked_reasons,
        artifact_generation_allowed=normalized.artifact_generation_allowed,
        capability_not_denied=normalized.capability_not_denied,
        safe_alternative_available=normalized.safe_alternative_available,
        recommended_next_step=normalized.recommended_next_step,
    )


def to_artifact_write_json_safe_v1(value: Any) -> Any:
    return _json_safe(value)


def _build_manual_request_from_scaffold(
    scaffold: Any,
    *,
    write_request_id: str,
    requested_entries: list[dict[str, Any]] | None = None,
    requested_root: str | None = None,
    allowed_root: str | None = None,
    write_mode: str = "dry_run",
    overwrite_policy: str = "no_overwrite",
    owner_approval_present: bool = False,
    operator_approval_present: bool = False,
    sandbox_only: bool = False,
    dry_run_only: bool = True,
    risk_labels: list[str] | None = None,
    boundary_requirements: list[str] | None = None,
    capability_class: str = "prepare_scaffold",
    requested_file_count: int | None = None,
    requested_total_size_estimate: int | None = None,
    quality_preservation_notes: list[str] | None = None,
    create_directories_requested: bool = False,
    edit_existing_files_requested: bool = False,
    delete_requested: bool = False,
    executable_files_requested: bool = False,
    dependency_install_requested: bool = False,
    test_execution_requested: bool = False,
    deployment_requested: bool = False,
    public_publish_requested: bool = False,
    public_claim_allowed: bool = False,
    iss_internal_reference_allowed: bool = True,
    learning_claimed: bool = False,
    runtime_authority: bool = False,
    writes_state: bool = False,
    model_provider_used: bool = False,
    safe_metadata: dict[str, Any] | None = None,
) -> ArtifactWriteRequest:
    scaffold_map = to_code_scaffold_json_safe_v1(scaffold)
    src_scaffold_id = _safe_text(scaffold_map.get("scaffold_id"))
    src_manifest_id = _safe_text(scaffold_map.get("source_manifest_id"))
    project_title = _safe_text(scaffold_map.get("project_title"))
    entries = requested_entries or _make_request_entries_from_scaffold(scaffold)
    root = requested_root or _default_requested_root(project_title, src_scaffold_id)
    return ArtifactWriteRequest(
        write_request_id=write_request_id,
        source_scaffold_id=src_scaffold_id,
        source_manifest_id=src_manifest_id,
        project_title=project_title,
        requested_root=root,
        allowed_root=allowed_root or root,
        requested_entries=entries,
        write_mode=write_mode,
        overwrite_policy=overwrite_policy,
        create_directories_requested=create_directories_requested,
        edit_existing_files_requested=edit_existing_files_requested,
        delete_requested=delete_requested,
        executable_files_requested=executable_files_requested,
        dependency_install_requested=dependency_install_requested,
        test_execution_requested=test_execution_requested,
        deployment_requested=deployment_requested,
        public_publish_requested=public_publish_requested,
        owner_approval_present=owner_approval_present,
        operator_approval_present=operator_approval_present,
        sandbox_only=sandbox_only,
        dry_run_only=dry_run_only,
        risk_labels=risk_labels or [],
        boundary_requirements=boundary_requirements or [],
        capability_class=capability_class,
        requested_file_count=requested_file_count if requested_file_count is not None else len(entries),
        requested_total_size_estimate=requested_total_size_estimate if requested_total_size_estimate is not None else sum(len(_safe_text(entry.get("content"))) for entry in entries),
        quality_preservation_notes=quality_preservation_notes or _default_quality_notes(),
        public_claim_allowed=public_claim_allowed,
        iss_internal_reference_allowed=iss_internal_reference_allowed,
        learning_claimed=learning_claimed,
        runtime_authority=runtime_authority,
        writes_state=writes_state,
        model_provider_used=model_provider_used,
        safe_metadata=safe_metadata or {},
    )


def build_initial_artifact_write_boundary_examples_v1() -> list[ArtifactWriteDecision]:
    scaffold_examples = build_initial_code_scaffold_examples_v1()
    by_name = {packet.safe_metadata.get("example_name", packet.scaffold_id): packet for packet in scaffold_examples}
    examples: list[ArtifactWriteDecision] = []

    wifi = by_name["wifi_rf_self_care_code_scaffold"]
    wifi_request = _build_manual_request_from_scaffold(
        wifi,
        write_request_id="wifi_rf_scaffold_dry_run_decision",
        write_mode="dry_run",
        dry_run_only=True,
        sandbox_only=False,
        capability_class="prepare_scaffold",
        risk_labels=["covert_tracking", "diagnosis_treatment", "consent_based_local_scaffold"],
        boundary_requirements=["consent-based local research only", "no covert tracking", "no diagnosis authority"],
        safe_metadata={"example_name": "wifi_rf_scaffold_dry_run_decision"},
    )
    wifi_decision = evaluate_artifact_write_boundary_v1(wifi_request)
    wifi_decision = _decision_like({**to_artifact_write_json_safe_v1(wifi_decision), "write_decision_id": "wifi_rf_scaffold_dry_run_decision", "safe_metadata": {**(wifi_decision.safe_metadata or {}), "example_name": "wifi_rf_scaffold_dry_run_decision"}})
    examples.append(wifi_decision)

    large_entries = []
    for index in range(24):
        large_entries.append(
            {
                "path": f"docs/section-{index + 1:02d}.md",
                "file_type": "markdown",
                "content_kind": "markdown_template",
                "content": f"# Section {index + 1}\n\nGenerated content packet chunk {index + 1}.\n",
                "generation_method": "validated_template",
                "overwrite_allowed": False,
                "executable": False,
                "contains_secret": False,
                "contains_private_data": False,
                "validation_command": "chunk validation",
                "owner_approval_required": True,
                "safe_metadata": {"source_path": f"docs/section-{index + 1:02d}.md"},
            }
        )
    large_request = _build_manual_request_from_scaffold(
        by_name["metamaterials_research_code_scaffold"],
        write_request_id="large_scaffold_chunking_preserved_decision",
        requested_entries=large_entries,
        requested_root="sandbox_artifacts/large_scaffold",
        allowed_root="sandbox_artifacts/large_scaffold",
        write_mode="sandbox_create_only",
        sandbox_only=True,
        dry_run_only=False,
        owner_approval_present=False,
        capability_class="prepare_scaffold",
        requested_file_count=24,
        requested_total_size_estimate=48000,
        quality_preservation_notes=["preserve manifest lineage", "chunking required"],
        safe_metadata={"example_name": "large_scaffold_chunking_preserved_decision"},
    )
    large_decision = evaluate_artifact_write_boundary_v1(large_request)
    large_decision = _decision_like({**to_artifact_write_json_safe_v1(large_decision), "write_decision_id": "large_scaffold_chunking_preserved_decision", "safe_metadata": {**(large_decision.safe_metadata or {}), "example_name": "large_scaffold_chunking_preserved_decision"}})
    examples.append(large_decision)

    static_request = _build_manual_request_from_scaffold(
        by_name["software_product_static_web_code_scaffold"],
        write_request_id="static_website_sandbox_create_decision",
        write_mode="sandbox_create_only",
        sandbox_only=True,
        dry_run_only=False,
        owner_approval_present=True,
        capability_class="prepare_scaffold",
        risk_labels=["deployment"],
        boundary_requirements=["no deployment authority", "sandbox create only"],
        safe_metadata={"example_name": "static_website_sandbox_create_decision"},
    )
    static_decision = evaluate_artifact_write_boundary_v1(static_request)
    static_decision = _decision_like({**to_artifact_write_json_safe_v1(static_decision), "write_decision_id": "static_website_sandbox_create_decision", "safe_metadata": {**(static_decision.safe_metadata or {}), "example_name": "static_website_sandbox_create_decision"}})
    examples.append(static_decision)

    medical_request = _build_manual_request_from_scaffold(
        by_name["medical_software_pathway_code_scaffold"],
        write_request_id="medical_software_boundary_docs_decision",
        write_mode="dry_run",
        dry_run_only=True,
        capability_class="prepare_validation_plan",
        risk_labels=["diagnosis_treatment", "regulatory_review"],
        boundary_requirements=["docs/regulatory/safety only", "no diagnosis authority"],
        safe_metadata={"example_name": "medical_software_boundary_docs_decision"},
    )
    medical_decision = evaluate_artifact_write_boundary_v1(medical_request)
    medical_decision = _decision_like({**to_artifact_write_json_safe_v1(medical_decision), "write_decision_id": "medical_software_boundary_docs_decision", "safe_metadata": {**(medical_decision.safe_metadata or {}), "example_name": "medical_software_boundary_docs_decision"}})
    examples.append(medical_decision)

    protected_entries = [
        {
            "path": "weslr/chat_responder.py",
            "file_type": "python",
            "content_kind": "python_module_template",
            "content": "# patch proposal only\n",
            "generation_method": "validated_template",
            "overwrite_allowed": False,
            "executable": False,
            "contains_secret": False,
            "contains_private_data": False,
            "validation_command": "patch proposal validation",
            "owner_approval_required": True,
            "safe_metadata": {"source_path": "weslr/chat_responder.py"},
        }
    ]
    protected_request = _build_manual_request_from_scaffold(
        by_name["ai_agent_architecture_code_scaffold"],
        write_request_id="protected_runtime_edit_blocked_decision",
        requested_entries=protected_entries,
        requested_root="sandbox_artifacts/protected_runtime_edit",
        allowed_root="sandbox_artifacts/protected_runtime_edit",
        write_mode="owner_approved_edit",
        edit_existing_files_requested=True,
        owner_approval_present=True,
        dry_run_only=False,
        capability_class="edit_generated_files",
        safe_metadata={"example_name": "protected_runtime_edit_blocked_decision"},
    )
    protected_decision = evaluate_artifact_write_boundary_v1(protected_request)
    protected_decision = _decision_like({**to_artifact_write_json_safe_v1(protected_decision), "write_decision_id": "protected_runtime_edit_blocked_decision", "safe_metadata": {**(protected_decision.safe_metadata or {}), "example_name": "protected_runtime_edit_blocked_decision"}})
    examples.append(protected_decision)

    env_entries = [
        {
            "path": ".env",
            "file_type": "yaml",
            "content_kind": "yaml_template",
            "content": "SECRET=redacted\n",
            "generation_method": "validated_template",
            "overwrite_allowed": False,
            "executable": False,
            "contains_secret": False,
            "contains_private_data": False,
            "validation_command": "env example validation",
            "owner_approval_required": True,
            "safe_metadata": {"source_path": ".env"},
        }
    ]
    env_request = _build_manual_request_from_scaffold(
        by_name["python_local_prototype_code_scaffold"] if "python_local_prototype_code_scaffold" in by_name else scaffold_examples[0],
        write_request_id="env_secret_write_blocked_decision",
        requested_entries=env_entries,
        requested_root="sandbox_artifacts/env_secret",
        allowed_root="sandbox_artifacts/env_secret",
        write_mode="owner_approved_create",
        owner_approval_present=True,
        dry_run_only=False,
        capability_class="write_sandbox_files",
        safe_metadata={"example_name": "env_secret_write_blocked_decision"},
    )
    env_decision = evaluate_artifact_write_boundary_v1(env_request)
    env_decision = _decision_like({**to_artifact_write_json_safe_v1(env_decision), "write_decision_id": "env_secret_write_blocked_decision", "safe_metadata": {**(env_decision.safe_metadata or {}), "example_name": "env_secret_write_blocked_decision"}})
    examples.append(env_decision)

    weslr_state_entries = [
        {
            "path": ".weslr/state.json",
            "file_type": "json",
            "content_kind": "json_template",
            "content": "{\"state\": \"redacted\"}\n",
            "generation_method": "validated_template",
            "overwrite_allowed": False,
            "executable": False,
            "contains_secret": False,
            "contains_private_data": False,
            "validation_command": "state validation",
            "owner_approval_required": True,
            "safe_metadata": {"source_path": ".weslr/state.json"},
        }
    ]
    weslr_state_request = _build_manual_request_from_scaffold(
        by_name["unknown_domain_code_scaffold"],
        write_request_id="weslr_state_write_blocked_decision",
        requested_entries=weslr_state_entries,
        requested_root="sandbox_artifacts/weslr_state",
        allowed_root="sandbox_artifacts/weslr_state",
        write_mode="owner_approved_create",
        owner_approval_present=True,
        dry_run_only=False,
        capability_class="write_sandbox_files",
        safe_metadata={"example_name": "weslr_state_write_blocked_decision"},
    )
    weslr_state_decision = evaluate_artifact_write_boundary_v1(weslr_state_request)
    weslr_state_decision = _decision_like({**to_artifact_write_json_safe_v1(weslr_state_decision), "write_decision_id": "weslr_state_write_blocked_decision", "safe_metadata": {**(weslr_state_decision.safe_metadata or {}), "example_name": "weslr_state_write_blocked_decision"}})
    examples.append(weslr_state_decision)

    delete_request = _build_manual_request_from_scaffold(
        by_name["metamaterials_research_code_scaffold"],
        write_request_id="delete_request_blocked_decision",
        delete_requested=True,
        write_mode="owner_approved_delete",
        owner_approval_present=True,
        dry_run_only=False,
        capability_class="prepare_patch_plan",
        safe_metadata={"example_name": "delete_request_blocked_decision"},
    )
    delete_decision = evaluate_artifact_write_boundary_v1(delete_request)
    delete_decision = _decision_like({**to_artifact_write_json_safe_v1(delete_decision), "write_decision_id": "delete_request_blocked_decision", "safe_metadata": {**(delete_decision.safe_metadata or {}), "example_name": "delete_request_blocked_decision"}})
    examples.append(delete_decision)

    deployment_request = _build_manual_request_from_scaffold(
        by_name["software_product_static_web_code_scaffold"],
        write_request_id="deployment_request_blocked_decision",
        deployment_requested=True,
        write_mode="sandbox_create_only",
        sandbox_only=True,
        owner_approval_present=True,
        dry_run_only=False,
        capability_class="deploy_or_publish",
        safe_metadata={"example_name": "deployment_request_blocked_decision"},
    )
    deployment_decision = evaluate_artifact_write_boundary_v1(deployment_request)
    deployment_decision = _decision_like({**to_artifact_write_json_safe_v1(deployment_decision), "write_decision_id": "deployment_request_blocked_decision", "safe_metadata": {**(deployment_decision.safe_metadata or {}), "example_name": "deployment_request_blocked_decision"}})
    examples.append(deployment_decision)

    safe_config_entries = [
        {
            "path": "config.example.yaml",
            "file_type": "yaml",
            "content_kind": "yaml_template",
            "content": "project:\n  title: safe config example\n",
            "generation_method": "validated_template",
            "overwrite_allowed": False,
            "executable": False,
            "contains_secret": False,
            "contains_private_data": False,
            "validation_command": "config example validation",
            "owner_approval_required": True,
            "safe_metadata": {"source_path": "config.example.yaml"},
        }
    ]
    safe_config_request = _build_manual_request_from_scaffold(
        by_name["python_research_code_scaffold"] if "python_research_code_scaffold" in by_name else scaffold_examples[0],
        write_request_id="safe_config_example_allowed_decision",
        requested_entries=safe_config_entries,
        requested_root="sandbox_artifacts/safe_config",
        allowed_root="sandbox_artifacts/safe_config",
        write_mode="owner_approved_create",
        owner_approval_present=True,
        dry_run_only=False,
        sandbox_only=True,
        capability_class="write_sandbox_files",
        safe_metadata={"example_name": "safe_config_example_allowed_decision"},
    )
    safe_config_decision = evaluate_artifact_write_boundary_v1(safe_config_request)
    safe_config_decision = _decision_like({**to_artifact_write_json_safe_v1(safe_config_decision), "write_decision_id": "safe_config_example_allowed_decision", "safe_metadata": {**(safe_config_decision.safe_metadata or {}), "example_name": "safe_config_example_allowed_decision"}})
    examples.append(safe_config_decision)

    return examples


# ---------------------------------------------------------------------------
# Normalize/re-export helpers used by tests
# ---------------------------------------------------------------------------


def _decision_to_json_safe(value: Any) -> Any:
    return _json_safe(value)
