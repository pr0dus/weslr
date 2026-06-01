"""Dry-run sandbox artifact writer executor v1.

This module converts a scaffold packet plus artifact-writer decision into a
sandbox write dry-run result packet. It is pure, deterministic, import-safe,
and fail-closed. No filesystem writes. No directory creation. No deletes.
No subprocess. No model/provider/search/advisor calls. No chat routing.
No runtime behavior changes. No `.weslr` access.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from hashlib import sha256
import re
from typing import Any, Iterable, Mapping

from weslr.artifact_writer_boundary import (
    ArtifactWriteDecision,
    ArtifactWriteRequest,
    ValidationError as ArtifactWriterBoundaryValidationError,
    evaluate_artifact_write_boundary_v1,
    to_artifact_write_json_safe_v1,
    validate_artifact_write_decision_v1,
)
from weslr.code_scaffold_generator import (
    CodeScaffoldPacket,
    GeneratedScaffoldEntry,
    SkippedScaffoldEntry,
    ValidationError as CodeScaffoldValidationError,
    build_initial_code_scaffold_examples_v1,
    to_code_scaffold_json_safe_v1,
    validate_code_scaffold_packet_v1,
)

HELPER_TYPE_V1 = "sandbox_artifact_writer_executor_v1"
SANDBOX_ARTIFACT_WRITE_EXECUTION_REQUEST_TYPE_V1 = "sandbox_artifact_write_execution_request_v1"
SANDBOX_ARTIFACT_WRITE_RESULT_TYPE_V1 = "sandbox_artifact_write_result_v1"
SANDBOX_ARTIFACT_WRITE_SUMMARY_TYPE_V1 = "sandbox_artifact_write_summary_v1"

LARGE_REQUEST_FILE_COUNT_THRESHOLD_V1 = 12
LARGE_REQUEST_TOTAL_SIZE_THRESHOLD_V1 = 20000
LARGE_REQUEST_MAX_FILE_THRESHOLD_V1 = 4096

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
ALLOWED_WRITE_ACTIONS_V1 = {"would_create", "blocked", "skipped"}
ALLOWED_RESULT_STATUSES_V1 = {"would_create", "blocked", "skipped"}


class ValidationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class SandboxArtifactWriteFileResult:
    path: str
    file_type: str
    content_kind: str
    bytes_estimate: int
    action: str
    status: str
    blocked_reason: str
    created: bool
    would_create: bool
    skipped: bool
    overwrite_performed: bool
    secret_detected: bool
    private_data_detected: bool
    protected_path: bool
    source_entry_id: str
    source_manifest_id: str
    source_scaffold_id: str
    safe_metadata: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class SandboxArtifactWriteDirectoryResult:
    path: str
    action: str
    status: str
    blocked_reason: str
    created: bool
    would_create: bool
    skipped: bool
    safe_metadata: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class SandboxArtifactWriteExecutionRequest:
    execution_request_id: str
    source_write_request_id: str
    source_write_decision_id: str
    source_scaffold_id: str
    source_manifest_id: str
    project_title: str
    sandbox_root: str
    allowed_root: str
    entries_to_write: list[dict[str, Any]]
    dry_run: bool
    create_directories: bool
    overwrite_existing: bool
    edit_existing_files: bool
    delete_requested: bool
    dependency_install_requested: bool
    test_execution_requested: bool
    deployment_requested: bool
    public_publish_requested: bool
    owner_approval_present: bool
    operator_approval_present: bool
    max_files: int
    max_total_bytes: int
    max_file_bytes: int
    chunking_required: bool
    provenance_required: bool
    runtime_authority: bool
    writes_state: bool
    model_provider_used: bool
    public_claim_allowed: bool
    learning_claimed: bool
    safe_metadata: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class SandboxArtifactWriteResult:
    write_result_id: str
    execution_request_id: str
    executed: bool
    dry_run: bool
    blocked: bool
    blocked_reason: str
    sandbox_root_used: str
    created_directories: list[SandboxArtifactWriteDirectoryResult]
    created_files: list[SandboxArtifactWriteFileResult]
    skipped_files: list[SandboxArtifactWriteFileResult]
    blocked_files: list[SandboxArtifactWriteFileResult]
    would_create_files: list[SandboxArtifactWriteFileResult]
    would_create_directories: list[SandboxArtifactWriteDirectoryResult]
    result_file_count: int
    result_total_bytes: int
    partial_result: bool
    chunking_required: bool
    provenance_records: list[dict[str, Any]]
    path_safety_result: dict[str, Any]
    protected_file_result: dict[str, Any]
    secret_scan_result: dict[str, Any]
    private_data_scan_result: dict[str, Any]
    overwrite_result: dict[str, Any]
    delete_result: dict[str, Any]
    dependency_install_result: dict[str, Any]
    test_execution_result: dict[str, Any]
    deployment_result: dict[str, Any]
    public_publish_result: dict[str, Any]
    recommended_next_step: str
    runtime_authority: bool
    writes_state: bool
    model_provider_used: bool
    public_claim_allowed: bool
    learning_claimed: bool
    safe_metadata: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class SandboxArtifactWriteSummary:
    summary_type: str
    write_result_id: str
    execution_request_id: str
    dry_run: bool
    blocked_count: int
    would_create_count: int
    partial_result: bool
    chunking_required: bool
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
        if any(phrase in blob and not _contains_negated_marker(blob, phrase) for phrase in FORBIDDEN_CLAIM_PHRASES_V1):
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
        if any(phrase in blob for phrase in ("no diagnosis or treatment", "no diagnosis authority", "no treatment authority", "diagnosis or treatment authority", "diagnosis and treatment authority")):
            return False
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


def _scaffold_entry_from_any(value: Any) -> dict[str, Any]:
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


def _file_result_id(source_scaffold_id: str, source_manifest_id: str, path: str, action: str) -> str:
    return _deterministic_id(source_scaffold_id, source_manifest_id, path, action, prefix="asfr")


def _plan_directories(path: str) -> list[str]:
    normalized = _normalize_path(path)
    if "/" not in normalized:
        return []
    pieces = normalized.split("/")[:-1]
    dirs: list[str] = []
    while pieces:
        dirs.append("/".join(pieces))
        pieces = pieces[:-1]
    return list(dict.fromkeys(dirs))


def _scan_entry(entry: Mapping[str, Any]) -> tuple[str, bool, bool, bool]:
    path = _safe_text(entry.get("path"))
    file_type = _safe_text(entry.get("file_type"))
    content = _safe_text(entry.get("content"))
    content_blob = " ".join([path, file_type, content]).lower()
    protected = _is_protected_path(path)
    secret = bool(entry.get("contains_secret")) or any(token in content_blob for token in (".env", "secret=", "token=", "api key", "private key"))
    private = bool(entry.get("contains_private_data")) or any(token in content_blob for token in ("secret transcript", "ssn", "social security number", "bank account", "credit card", "passport number"))
    if protected:
        return "protected_path", secret, private, protected
    if secret or private:
        return ("secret_data" if secret else "private_data"), secret, private, protected
    if _contains_forbidden_claim_marker(content_blob):
        return "forbidden_claim_marker", secret, private, protected
    if _contains_unsafe_deployment_marker(content_blob):
        return "unsafe_deployment", secret, private, protected
    if _contains_covert_tracking_marker(content_blob):
        return "covert_tracking", secret, private, protected
    if _contains_diagnosis_treatment_marker(content_blob):
        return "diagnosis_treatment", secret, private, protected
    return "clear", secret, private, protected


def _scan_blocked_reason_texts(value: Any) -> list[str]:
    reasons: list[str] = []
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, Mapping):
        for key, item in value.items():
            reasons.extend(_scan_blocked_reason_texts(item))
            if _safe_text(key).lower() in FORBIDDEN_FIELD_NAMES_V1:
                reasons.append(_safe_text(key).lower())
    elif isinstance(value, (list, tuple, set)):
        for item in value:
            reasons.extend(_scan_blocked_reason_texts(item))
    elif isinstance(value, str):
        reasons.append(_safe_text(value))
    return reasons


def _example_name(value: Any) -> str:
    if is_dataclass(value):
        mapping = asdict(value)
    elif isinstance(value, Mapping):
        mapping = value
    else:
        return ""
    safe_metadata = mapping.get("safe_metadata") if isinstance(mapping.get("safe_metadata"), Mapping) else {}
    return _safe_text(mapping.get("write_result_id") or safe_metadata.get("example_name"))


# ---------------------------------------------------------------------------
# Execution-request helpers
# ---------------------------------------------------------------------------


def _request_like(value: Any) -> SandboxArtifactWriteExecutionRequest:
    if isinstance(value, SandboxArtifactWriteExecutionRequest):
        return value
    mapping = _as_mapping(value)
    safe_metadata = mapping.get("safe_metadata", None)
    if safe_metadata is not None and not isinstance(safe_metadata, Mapping):
        raise ValidationError("safe_metadata_must_be_mapping")
    entries = [_entry_from_any(item) for item in mapping.get("entries_to_write", [])]
    return SandboxArtifactWriteExecutionRequest(
        execution_request_id=_safe_text(mapping.get("execution_request_id")),
        source_write_request_id=_safe_text(mapping.get("source_write_request_id")),
        source_write_decision_id=_safe_text(mapping.get("source_write_decision_id")),
        source_scaffold_id=_safe_text(mapping.get("source_scaffold_id")),
        source_manifest_id=_safe_text(mapping.get("source_manifest_id")),
        project_title=_safe_text(mapping.get("project_title")),
        sandbox_root=_safe_text(mapping.get("sandbox_root")),
        allowed_root=_safe_text(mapping.get("allowed_root")),
        entries_to_write=entries,
        dry_run=bool(mapping.get("dry_run")),
        create_directories=bool(mapping.get("create_directories")),
        overwrite_existing=bool(mapping.get("overwrite_existing")),
        edit_existing_files=bool(mapping.get("edit_existing_files")),
        delete_requested=bool(mapping.get("delete_requested")),
        dependency_install_requested=bool(mapping.get("dependency_install_requested")),
        test_execution_requested=bool(mapping.get("test_execution_requested")),
        deployment_requested=bool(mapping.get("deployment_requested")),
        public_publish_requested=bool(mapping.get("public_publish_requested")),
        owner_approval_present=bool(mapping.get("owner_approval_present")),
        operator_approval_present=bool(mapping.get("operator_approval_present")),
        max_files=int(mapping.get("max_files") or 0),
        max_total_bytes=int(mapping.get("max_total_bytes") or 0),
        max_file_bytes=int(mapping.get("max_file_bytes") or 0),
        chunking_required=bool(mapping.get("chunking_required")),
        provenance_required=bool(mapping.get("provenance_required", True)),
        runtime_authority=bool(mapping.get("runtime_authority")),
        writes_state=bool(mapping.get("writes_state")),
        model_provider_used=bool(mapping.get("model_provider_used")),
        public_claim_allowed=bool(mapping.get("public_claim_allowed")),
        learning_claimed=bool(mapping.get("learning_claimed")),
        safe_metadata=dict(safe_metadata or {}),
    )


def _result_like(value: Any) -> SandboxArtifactWriteResult:
    if isinstance(value, SandboxArtifactWriteResult):
        return value
    mapping = _as_mapping(value)
    safe_metadata = mapping.get("safe_metadata", None)
    if safe_metadata is not None and not isinstance(safe_metadata, Mapping):
        raise ValidationError("safe_metadata_must_be_mapping")
    return SandboxArtifactWriteResult(
        write_result_id=_safe_text(mapping.get("write_result_id")),
        execution_request_id=_safe_text(mapping.get("execution_request_id")),
        executed=bool(mapping.get("executed")),
        dry_run=bool(mapping.get("dry_run")),
        blocked=bool(mapping.get("blocked")),
        blocked_reason=_safe_text(mapping.get("blocked_reason")),
        sandbox_root_used=_safe_text(mapping.get("sandbox_root_used")),
        created_directories=[_directory_result_like(item) for item in mapping.get("created_directories", [])],
        created_files=[_file_result_like(item) for item in mapping.get("created_files", [])],
        skipped_files=[_file_result_like(item) for item in mapping.get("skipped_files", [])],
        blocked_files=[_file_result_like(item) for item in mapping.get("blocked_files", [])],
        would_create_files=[_file_result_like(item) for item in mapping.get("would_create_files", [])],
        would_create_directories=[_directory_result_like(item) for item in mapping.get("would_create_directories", [])],
        result_file_count=int(mapping.get("result_file_count") or 0),
        result_total_bytes=int(mapping.get("result_total_bytes") or 0),
        partial_result=bool(mapping.get("partial_result")),
        chunking_required=bool(mapping.get("chunking_required")),
        provenance_records=[dict(item) if isinstance(item, Mapping) else {} for item in mapping.get("provenance_records", [])],
        path_safety_result=dict(mapping.get("path_safety_result") or {}),
        protected_file_result=dict(mapping.get("protected_file_result") or {}),
        secret_scan_result=dict(mapping.get("secret_scan_result") or {}),
        private_data_scan_result=dict(mapping.get("private_data_scan_result") or {}),
        overwrite_result=dict(mapping.get("overwrite_result") or {}),
        delete_result=dict(mapping.get("delete_result") or {}),
        dependency_install_result=dict(mapping.get("dependency_install_result") or {}),
        test_execution_result=dict(mapping.get("test_execution_result") or {}),
        deployment_result=dict(mapping.get("deployment_result") or {}),
        public_publish_result=dict(mapping.get("public_publish_result") or {}),
        recommended_next_step=_safe_text(mapping.get("recommended_next_step")),
        runtime_authority=bool(mapping.get("runtime_authority")),
        writes_state=bool(mapping.get("writes_state")),
        model_provider_used=bool(mapping.get("model_provider_used")),
        public_claim_allowed=bool(mapping.get("public_claim_allowed")),
        learning_claimed=bool(mapping.get("learning_claimed")),
        safe_metadata=dict(safe_metadata or {}),
    )


def _file_result_like(value: Any) -> SandboxArtifactWriteFileResult:
    mapping = _as_mapping(value)
    safe_metadata = mapping.get("safe_metadata", None)
    if safe_metadata is not None and not isinstance(safe_metadata, Mapping):
        raise ValidationError("safe_metadata_must_be_mapping")
    return SandboxArtifactWriteFileResult(
        path=_safe_text(mapping.get("path")),
        file_type=_safe_text(mapping.get("file_type")),
        content_kind=_safe_text(mapping.get("content_kind")),
        bytes_estimate=int(mapping.get("bytes_estimate") or 0),
        action=_safe_text(mapping.get("action")),
        status=_safe_text(mapping.get("status")),
        blocked_reason=_safe_text(mapping.get("blocked_reason")),
        created=bool(mapping.get("created")),
        would_create=bool(mapping.get("would_create")),
        skipped=bool(mapping.get("skipped")),
        overwrite_performed=bool(mapping.get("overwrite_performed")),
        secret_detected=bool(mapping.get("secret_detected")),
        private_data_detected=bool(mapping.get("private_data_detected")),
        protected_path=bool(mapping.get("protected_path")),
        source_entry_id=_safe_text(mapping.get("source_entry_id")),
        source_manifest_id=_safe_text(mapping.get("source_manifest_id")),
        source_scaffold_id=_safe_text(mapping.get("source_scaffold_id")),
        safe_metadata=dict(safe_metadata or {}),
    )


def _directory_result_like(value: Any) -> SandboxArtifactWriteDirectoryResult:
    mapping = _as_mapping(value)
    safe_metadata = mapping.get("safe_metadata", None)
    if safe_metadata is not None and not isinstance(safe_metadata, Mapping):
        raise ValidationError("safe_metadata_must_be_mapping")
    return SandboxArtifactWriteDirectoryResult(
        path=_safe_text(mapping.get("path")),
        action=_safe_text(mapping.get("action")),
        status=_safe_text(mapping.get("status")),
        blocked_reason=_safe_text(mapping.get("blocked_reason")),
        created=bool(mapping.get("created")),
        would_create=bool(mapping.get("would_create")),
        skipped=bool(mapping.get("skipped")),
        safe_metadata=dict(safe_metadata or {}),
    )


# ---------------------------------------------------------------------------
# Public APIs
# ---------------------------------------------------------------------------


def build_sandbox_artifact_write_execution_request_v1(
    write_request: Any,
    write_decision: Any,
    scaffold_packet: Any,
    sandbox_root: str | None = None,
) -> SandboxArtifactWriteExecutionRequest:
    decision = write_decision if isinstance(write_decision, ArtifactWriteDecision) else write_decision
    validate_artifact_write_decision_v1(decision)
    validate_code_scaffold_packet_v1(scaffold_packet)

    request_map = _as_mapping(write_request)
    decision_map = to_artifact_write_json_safe_v1(decision)
    scaffold_map = to_code_scaffold_json_safe_v1(scaffold_packet)

    raw_requested_entries = request_map.get("requested_entries") or []
    entries = [_entry_from_any(entry) for entry in raw_requested_entries] if raw_requested_entries else [_scaffold_entry_from_any(entry) for entry in scaffold_map.get("generated_entries", [])]
    if sandbox_root is None:
        sandbox_root = _safe_text(request_map.get("sandbox_root") or "")
    allowed_root = _safe_text(request_map.get("allowed_root") or decision_map.get("selected_root") or sandbox_root or f"sandbox_artifacts/{_slugify(scaffold_map.get('project_title') or scaffold_map.get('scaffold_id'))}")
    root = _safe_text(sandbox_root)

    total_bytes = sum(len(_safe_text(entry.get("content"))) for entry in entries)
    max_file_bytes = max([len(_safe_text(entry.get("content"))) for entry in entries], default=0)
    chunking_required = bool(
        request_map.get("chunking_required")
        or decision_map.get("chunking_required")
        or len(entries) > LARGE_REQUEST_FILE_COUNT_THRESHOLD_V1
        or total_bytes > LARGE_REQUEST_TOTAL_SIZE_THRESHOLD_V1
        or max_file_bytes > LARGE_REQUEST_MAX_FILE_THRESHOLD_V1
    )
    execution_request = SandboxArtifactWriteExecutionRequest(
        execution_request_id=_deterministic_id(
            request_map.get("write_request_id"),
            decision_map.get("write_decision_id"),
            scaffold_map.get("scaffold_id"),
            root,
            prefix="asreq",
        ),
        source_write_request_id=_safe_text(request_map.get("write_request_id")),
        source_write_decision_id=_safe_text(decision_map.get("write_decision_id")),
        source_scaffold_id=_safe_text(scaffold_map.get("scaffold_id")),
        source_manifest_id=_safe_text(scaffold_map.get("source_manifest_id")),
        project_title=_safe_text(scaffold_map.get("project_title")),
        sandbox_root=root,
        allowed_root=allowed_root,
        entries_to_write=entries,
        dry_run=bool(request_map.get("dry_run_only", True)),
        create_directories=bool(request_map.get("create_directories_requested") or request_map.get("create_directories") or decision_map.get("directory_creation_allowed")),
        overwrite_existing=bool(request_map.get("overwrite_existing") or request_map.get("edit_existing_files_requested")),
        edit_existing_files=bool(request_map.get("edit_existing_files_requested") or request_map.get("edit_existing_files")),
        delete_requested=bool(request_map.get("delete_requested")),
        dependency_install_requested=bool(request_map.get("dependency_install_requested")),
        test_execution_requested=bool(request_map.get("test_execution_requested")),
        deployment_requested=bool(request_map.get("deployment_requested")),
        public_publish_requested=bool(request_map.get("public_publish_requested")),
        owner_approval_present=bool(request_map.get("owner_approval_present")),
        operator_approval_present=bool(request_map.get("operator_approval_present")),
        max_files=int(request_map.get("requested_file_count") or len(entries)),
        max_total_bytes=int(request_map.get("requested_total_size_estimate") or total_bytes),
        max_file_bytes=int(request_map.get("max_file_bytes") or max_file_bytes),
        chunking_required=chunking_required,
        provenance_required=bool(request_map.get("provenance_required", True)),
        runtime_authority=bool(request_map.get("runtime_authority")),
        writes_state=bool(request_map.get("writes_state")),
        model_provider_used=bool(request_map.get("model_provider_used")),
        public_claim_allowed=bool(request_map.get("public_claim_allowed")),
        learning_claimed=bool(request_map.get("learning_claimed")),
        safe_metadata={
            **dict(request_map.get("safe_metadata") or {}),
            "source_write_request_id": _safe_text(request_map.get("write_request_id")),
            "source_write_decision_id": _safe_text(decision_map.get("write_decision_id")),
            "source_scaffold_id": _safe_text(scaffold_map.get("scaffold_id")),
            "source_manifest_id": _safe_text(scaffold_map.get("source_manifest_id")),
            "sandbox_root": root,
            "allowed_root": allowed_root,
            "entry_count": len(entries),
        },
    )
    validate_sandbox_artifact_write_execution_request_v1(execution_request)
    return execution_request


def validate_sandbox_artifact_write_execution_request_v1(request: Any) -> bool:
    original = _as_mapping(request)
    forbidden = _contains_forbidden_fields(original)
    if forbidden:
        raise ValidationError(f"forbidden_field_detected:{forbidden[0]}")
    normalized = _request_like(request)
    if _contains_forbidden_claim_marker(normalized):
        raise ValidationError("forbidden_claim_marker_detected")
    if not _safe_text(normalized.execution_request_id):
        raise ValidationError("execution_request_id_required")
    if not _safe_text(normalized.source_write_request_id):
        raise ValidationError("source_write_request_id_required")
    if not _safe_text(normalized.source_write_decision_id):
        raise ValidationError("source_write_decision_id_required")
    if not _safe_text(normalized.source_scaffold_id):
        raise ValidationError("source_scaffold_id_required")
    if not _safe_text(normalized.source_manifest_id):
        raise ValidationError("source_manifest_id_required")
    if not _safe_text(normalized.project_title):
        raise ValidationError("project_title_required")
    if normalized.sandbox_root and not _is_safe_relative_path(normalized.sandbox_root):
        raise ValidationError("sandbox_root_must_be_safe_relative_path")
    if not _is_safe_relative_path(normalized.allowed_root):
        raise ValidationError("allowed_root_must_be_safe_relative_path")
    if not normalized.entries_to_write:
        raise ValidationError("entries_to_write_required")
    if normalized.dry_run not in {True, False}:
        raise ValidationError("dry_run_must_be_bool")
    for field_name in (
        "create_directories",
        "overwrite_existing",
        "edit_existing_files",
        "delete_requested",
        "dependency_install_requested",
        "test_execution_requested",
        "deployment_requested",
        "public_publish_requested",
        "owner_approval_present",
        "operator_approval_present",
        "chunking_required",
        "provenance_required",
        "runtime_authority",
        "writes_state",
        "model_provider_used",
        "public_claim_allowed",
        "learning_claimed",
    ):
        if type(getattr(normalized, field_name)) is not bool:
            raise ValidationError(f"{field_name}_must_be_bool")
    for field_name in ("max_files", "max_total_bytes", "max_file_bytes"):
        if type(getattr(normalized, field_name)) is not int or getattr(normalized, field_name) < 0:
            raise ValidationError(f"{field_name}_must_be_non_negative_int")
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
    total_bytes = 0
    for entry in normalized.entries_to_write:
        if not _safe_text(entry.get("path")):
            raise ValidationError("entry_path_required")
        if not _safe_text(entry.get("file_type")):
            raise ValidationError("entry_file_type_required")
        if not _safe_text(entry.get("content_kind")):
            raise ValidationError("entry_content_kind_required")
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
        total_bytes += len(_safe_text(entry.get("content")))
        if normalized.max_file_bytes and len(_safe_text(entry.get("content"))) > normalized.max_file_bytes and not normalized.chunking_required:
            raise ValidationError("chunking_required_for_large_entry")
    if normalized.max_files and len(normalized.entries_to_write) > normalized.max_files and not normalized.chunking_required:
        raise ValidationError("chunking_required_for_large_file_count")
    if normalized.max_total_bytes and total_bytes > normalized.max_total_bytes and not normalized.chunking_required:
        raise ValidationError("chunking_required_for_large_total_bytes")
    if normalized.safe_metadata is not None and not isinstance(normalized.safe_metadata, dict):
        raise ValidationError("safe_metadata_must_be_mapping")
    return True


def _operation_result(requested: bool, *, blocked_reason: str, allowed_label: str = "allowed") -> dict[str, Any]:
    if requested:
        return {"status": "blocked", "requested": True, "allowed": False, "blocked_reason": blocked_reason}
    return {"status": "not_requested", "requested": False, "allowed": False, "blocked_reason": ""}


def _build_file_result(
    entry: Mapping[str, Any],
    *,
    source_scaffold_id: str,
    source_manifest_id: str,
    sandbox_root_used: str,
    action: str,
    status: str,
    blocked_reason: str,
    source_entry_id: str,
) -> SandboxArtifactWriteFileResult:
    safe_metadata = dict(entry.get("safe_metadata") or {})
    safe_metadata.update(
        {
            "sandbox_root_used": sandbox_root_used,
            "source_entry_id": source_entry_id,
            "source_manifest_id": source_manifest_id,
            "source_scaffold_id": source_scaffold_id,
        }
    )
    content = _safe_text(entry.get("content"))
    return SandboxArtifactWriteFileResult(
        path=_safe_text(entry.get("path")),
        file_type=_safe_text(entry.get("file_type") or "skipped"),
        content_kind=_safe_text(entry.get("content_kind") or "skip_notice"),
        bytes_estimate=len(content),
        action=action,
        status=status,
        blocked_reason=blocked_reason,
        created=False,
        would_create=status == "would_create",
        skipped=status == "skipped",
        overwrite_performed=False,
        secret_detected=bool(entry.get("contains_secret")),
        private_data_detected=bool(entry.get("contains_private_data")),
        protected_path=_is_protected_path(entry.get("path", "")),
        source_entry_id=source_entry_id,
        source_manifest_id=source_manifest_id,
        source_scaffold_id=source_scaffold_id,
        safe_metadata=safe_metadata,
    )


def _build_directory_result(path: str, *, blocked_reason: str = "", status: str = "would_create", safe_metadata: dict[str, Any] | None = None) -> SandboxArtifactWriteDirectoryResult:
    return SandboxArtifactWriteDirectoryResult(
        path=path,
        action=status,
        status=status,
        blocked_reason=blocked_reason,
        created=False,
        would_create=status == "would_create",
        skipped=status == "skipped",
        safe_metadata=safe_metadata or {},
    )


def _entry_source_id(source_scaffold_id: str, source_manifest_id: str, entry: Mapping[str, Any]) -> str:
    return _deterministic_id(source_scaffold_id, source_manifest_id, _safe_text(entry.get("path")), _safe_text(entry.get("content_kind")), prefix="asent")


def execute_sandbox_artifact_write_v1(
    write_request: Any,
    write_decision: Any,
    scaffold_packet: Any,
    sandbox_root: str | None = None,
) -> SandboxArtifactWriteResult:
    execution_request = build_sandbox_artifact_write_execution_request_v1(write_request, write_decision, scaffold_packet, sandbox_root=sandbox_root)
    request_map = _as_mapping(execution_request)
    decision_map = to_artifact_write_json_safe_v1(write_decision)
    scaffold_map = to_code_scaffold_json_safe_v1(scaffold_packet)

    generated_entries = [_entry_from_any(entry) for entry in request_map.get("entries_to_write", [])]
    scaffold_skipped_entries = [_scaffold_entry_from_any(entry) for entry in scaffold_map.get("skipped_entries", [])]

    would_create_files: list[SandboxArtifactWriteFileResult] = []
    blocked_files: list[SandboxArtifactWriteFileResult] = []
    skipped_files: list[SandboxArtifactWriteFileResult] = []
    provenance_records: list[dict[str, Any]] = []
    blocked_reasons: list[str] = []

    sandbox_root_used = _safe_text(request_map.get("sandbox_root"))
    source_scaffold_id = _safe_text(request_map.get("source_scaffold_id"))
    source_manifest_id = _safe_text(request_map.get("source_manifest_id"))
    write_result_id = _deterministic_id(
        request_map.get("execution_request_id"),
        decision_map.get("write_decision_id"),
        sandbox_root_used,
        prefix="asres",
    )

    def _record_block(reason: str) -> None:
        if reason and reason not in blocked_reasons:
            blocked_reasons.append(reason)

    for entry in generated_entries:
        scan_reason, secret, private, protected = _scan_entry(entry)
        source_entry_id = _entry_source_id(source_scaffold_id, source_manifest_id, entry)
        if scan_reason != "clear":
            _record_block(scan_reason)
            blocked_files.append(
                _build_file_result(
                    entry,
                    source_scaffold_id=source_scaffold_id,
                    source_manifest_id=source_manifest_id,
                    sandbox_root_used=sandbox_root_used,
                    action="blocked",
                    status="blocked",
                    blocked_reason=scan_reason,
                    source_entry_id=source_entry_id,
                )
            )
        else:
            would_create_files.append(
                _build_file_result(
                    entry,
                    source_scaffold_id=source_scaffold_id,
                    source_manifest_id=source_manifest_id,
                    sandbox_root_used=sandbox_root_used,
                    action="would_create",
                    status="would_create",
                    blocked_reason="",
                    source_entry_id=source_entry_id,
                )
            )
        provenance_records.append(
            {
                "write_result_id": write_result_id,
                "execution_request_id": _safe_text(request_map.get("execution_request_id")),
                "source_entry_id": source_entry_id,
                "path": _safe_text(entry.get("path")),
                "source_manifest_id": source_manifest_id,
                "source_scaffold_id": source_scaffold_id,
                "content_kind": _safe_text(entry.get("content_kind")),
                "generation_method": _safe_text(entry.get("generation_method")),
                "status": "blocked" if scan_reason != "clear" else "would_create",
            }
        )

    for entry in scaffold_skipped_entries:
        skipped_files.append(
            _build_file_result(
                entry,
                source_scaffold_id=source_scaffold_id,
                source_manifest_id=source_manifest_id,
                sandbox_root_used=sandbox_root_used,
                action="skipped",
                status="skipped",
                blocked_reason="scaffold_skipped",
                source_entry_id=_entry_source_id(source_scaffold_id, source_manifest_id, entry),
            )
        )

    if request_map.get("dry_run") is False:
        _record_block("real_write_requested_blocked")
    if bool(request_map.get("delete_requested")):
        _record_block("delete_requested")
    if bool(request_map.get("dependency_install_requested")):
        _record_block("dependency_install_requested")
    if bool(request_map.get("test_execution_requested")):
        _record_block("test_execution_requested")
    if bool(request_map.get("deployment_requested")):
        _record_block("deployment_requested")
    if bool(request_map.get("public_publish_requested")):
        _record_block("public_publish_requested")
    if bool(request_map.get("runtime_authority")):
        _record_block("runtime_authority_requested")

    risk_labels = _normalize_list(to_artifact_write_json_safe_v1(write_request).get("risk_labels") if hasattr(write_request, "risk_labels") or isinstance(write_request, Mapping) else [])
    for label in risk_labels:
        if label in {"covert_tracking", "diagnosis_treatment", "deployment", "public_publish"}:
            _record_block(f"risk:{label}")

    file_paths_for_dirs = [item.path for item in would_create_files]
    dir_paths: list[str] = []
    for path in file_paths_for_dirs:
        for parent in _plan_directories(path):
            if parent not in dir_paths:
                dir_paths.append(parent)
    would_create_directories = [
        _build_directory_result(
            path,
            safe_metadata={"source_scaffold_id": source_scaffold_id, "source_manifest_id": source_manifest_id, "write_result_id": write_result_id},
        )
        for path in dir_paths
    ]

    blocked = bool(blocked_reasons or blocked_files)
    dry_run = bool(request_map.get("dry_run"))
    chunking_required = bool(request_map.get("chunking_required"))
    if len(would_create_files) > LARGE_REQUEST_FILE_COUNT_THRESHOLD_V1 or sum(item.bytes_estimate for item in would_create_files) > LARGE_REQUEST_TOTAL_SIZE_THRESHOLD_V1:
        chunking_required = True
    partial_result = bool(blocked or chunking_required or skipped_files)
    recommended_next_step = _safe_text(request_map.get("allowed_root") or "keep as dry-run metadata packet")
    if request_map.get("dry_run") is False:
        recommended_next_step = "switch to dry-run only"
    elif chunking_required:
        recommended_next_step = "chunk into smaller sandbox batches"
    elif blocked_reasons:
        recommended_next_step = "repair blocked entries and rerun dry-run"
    elif bool(request_map.get("owner_approval_present")) and (request_map.get("create_directories") or request_map.get("overwrite_existing") or request_map.get("edit_existing_files")):
        recommended_next_step = "request owner approval before sandbox create"

    result = SandboxArtifactWriteResult(
        write_result_id=write_result_id,
        execution_request_id=_safe_text(request_map.get("execution_request_id")),
        executed=False,
        dry_run=dry_run,
        blocked=blocked,
        blocked_reason="; ".join(_dedupe_preserve(blocked_reasons)),
        sandbox_root_used=sandbox_root_used,
        created_directories=[],
        created_files=[],
        skipped_files=skipped_files,
        blocked_files=blocked_files,
        would_create_files=would_create_files,
        would_create_directories=would_create_directories,
        result_file_count=len(would_create_files),
        result_total_bytes=sum(item.bytes_estimate for item in would_create_files),
        partial_result=partial_result,
        chunking_required=chunking_required,
        provenance_records=provenance_records,
        path_safety_result={
            "status": "blocked" if any(item.protected_path is False and not _is_safe_relative_path(item.path) for item in blocked_files) else "clear",
            "blocked_paths": [item.path for item in blocked_files if not _is_safe_relative_path(item.path)],
        },
        protected_file_result={
            "status": "blocked" if any(item.protected_path for item in blocked_files) else "clear",
            "blocked_paths": [item.path for item in blocked_files if item.protected_path],
        },
        secret_scan_result={
            "status": "blocked" if any(item.secret_detected for item in blocked_files) else "clear",
            "blocked_paths": [item.path for item in blocked_files if item.secret_detected],
            "count": sum(1 for item in blocked_files if item.secret_detected),
        },
        private_data_scan_result={
            "status": "blocked" if any(item.private_data_detected for item in blocked_files) else "clear",
            "blocked_paths": [item.path for item in blocked_files if item.private_data_detected],
            "count": sum(1 for item in blocked_files if item.private_data_detected),
        },
        overwrite_result={
            "status": "blocked" if bool(request_map.get("overwrite_existing")) or bool(request_map.get("edit_existing_files")) else "clear",
            "requested": bool(request_map.get("overwrite_existing") or request_map.get("edit_existing_files")),
            "performed": False,
            "allowed": False,
            "blocked_reason": "overwrite_not_supported_v1" if bool(request_map.get("overwrite_existing") or request_map.get("edit_existing_files")) else "",
        },
        delete_result=_operation_result(bool(request_map.get("delete_requested")), blocked_reason="delete_not_supported_v1"),
        dependency_install_result=_operation_result(bool(request_map.get("dependency_install_requested")), blocked_reason="dependency_install_not_supported_v1"),
        test_execution_result=_operation_result(bool(request_map.get("test_execution_requested")), blocked_reason="test_execution_not_supported_v1"),
        deployment_result=_operation_result(bool(request_map.get("deployment_requested")), blocked_reason="deployment_not_supported_v1"),
        public_publish_result=_operation_result(bool(request_map.get("public_publish_requested")), blocked_reason="public_publish_not_supported_v1"),
        recommended_next_step=recommended_next_step,
        runtime_authority=bool(request_map.get("runtime_authority")),
        writes_state=bool(request_map.get("writes_state")),
        model_provider_used=bool(request_map.get("model_provider_used")),
        public_claim_allowed=bool(request_map.get("public_claim_allowed")),
        learning_claimed=bool(request_map.get("learning_claimed")),
        safe_metadata={
            **dict(request_map.get("safe_metadata") or {}),
            "write_result_id": write_result_id,
            "execution_request_id": _safe_text(request_map.get("execution_request_id")),
            "source_scaffold_id": source_scaffold_id,
            "source_manifest_id": source_manifest_id,
            "blocked_reason_count": len(_dedupe_preserve(blocked_reasons)),
            "would_create_count": len(would_create_files),
        },
    )
    validate_sandbox_artifact_write_result_v1(result)
    return result


def validate_sandbox_artifact_write_result_v1(result: Any) -> bool:
    original = _as_mapping(result)
    forbidden = _contains_forbidden_fields(original)
    if forbidden:
        raise ValidationError(f"forbidden_field_detected:{forbidden[0]}")
    normalized = _result_like(result)
    if _contains_forbidden_claim_marker(normalized):
        raise ValidationError("forbidden_claim_marker_detected")
    if not _safe_text(normalized.write_result_id):
        raise ValidationError("write_result_id_required")
    if not _safe_text(normalized.execution_request_id):
        raise ValidationError("execution_request_id_required")
    if normalized.executed:
        raise ValidationError("executed_must_be_false")
    if normalized.created_files:
        raise ValidationError("created_files_must_be_empty")
    if normalized.created_directories:
        raise ValidationError("created_directories_must_be_empty")
    if normalized.runtime_authority:
        raise ValidationError("runtime_authority_must_be_false")
    if normalized.writes_state:
        raise ValidationError("writes_state_must_be_false")
    if normalized.model_provider_used:
        raise ValidationError("model_provider_used_must_be_false")
    if normalized.public_claim_allowed:
        raise ValidationError("public_claim_allowed_must_be_false")
    if normalized.learning_claimed:
        raise ValidationError("learning_claimed_must_be_false")
    if normalized.blocked and not normalized.blocked_reason:
        raise ValidationError("blocked_reason_required")
    for field_name in ("dry_run", "blocked", "partial_result", "chunking_required"):
        if type(getattr(normalized, field_name)) is not bool:
            raise ValidationError(f"{field_name}_must_be_bool")
    if type(normalized.result_file_count) is not int or normalized.result_file_count < 0:
        raise ValidationError("result_file_count_must_be_non_negative_int")
    if type(normalized.result_total_bytes) is not int or normalized.result_total_bytes < 0:
        raise ValidationError("result_total_bytes_must_be_non_negative_int")
    if normalized.result_file_count != len(normalized.would_create_files):
        raise ValidationError("would_create_file_count_mismatch")
    if normalized.result_total_bytes != sum(item.bytes_estimate for item in normalized.would_create_files):
        raise ValidationError("would_create_total_bytes_mismatch")
    if normalized.safe_metadata is not None and not isinstance(normalized.safe_metadata, dict):
        raise ValidationError("safe_metadata_must_be_mapping")
    for list_name in ("would_create_files", "blocked_files", "skipped_files"):
        for item in getattr(normalized, list_name):
            if item.action not in ALLOWED_WRITE_ACTIONS_V1:
                raise ValidationError("unknown_file_action")
            if item.status not in ALLOWED_RESULT_STATUSES_V1:
                raise ValidationError("unknown_file_status")
            if type(item.created) is not bool or item.created:
                raise ValidationError("created_must_be_false")
            if type(item.would_create) is not bool:
                raise ValidationError("would_create_must_be_bool")
            if type(item.skipped) is not bool:
                raise ValidationError("skipped_must_be_bool")
            if type(item.overwrite_performed) is not bool or item.overwrite_performed:
                raise ValidationError("overwrite_performed_must_be_false")
            if type(item.secret_detected) is not bool:
                raise ValidationError("secret_detected_must_be_bool")
            if type(item.private_data_detected) is not bool:
                raise ValidationError("private_data_detected_must_be_bool")
            if type(item.protected_path) is not bool:
                raise ValidationError("protected_path_must_be_bool")
            if not _safe_text(item.path):
                raise ValidationError("file_path_required")
            if not _safe_text(item.file_type):
                raise ValidationError("file_type_required")
            if not _safe_text(item.content_kind):
                raise ValidationError("content_kind_required")
            if type(item.bytes_estimate) is not int or item.bytes_estimate < 0:
                raise ValidationError("bytes_estimate_must_be_non_negative_int")
            if not _safe_text(item.source_entry_id):
                raise ValidationError("source_entry_id_required")
            if not _safe_text(item.source_manifest_id):
                raise ValidationError("source_manifest_id_required")
            if not _safe_text(item.source_scaffold_id):
                raise ValidationError("source_scaffold_id_required")
            if item.safe_metadata is None or not isinstance(item.safe_metadata, dict):
                raise ValidationError("file_safe_metadata_required")
            if item.protected_path and item.status == "would_create":
                raise ValidationError("protected_path_allowed")
            if item.protected_path and not item.blocked_reason:
                raise ValidationError("protected_path_must_be_blocked")
            if (item.secret_detected or item.private_data_detected) and item.status == "would_create":
                raise ValidationError("secret_or_private_data_allowed")
            if item.status == "blocked" and not item.blocked_reason:
                raise ValidationError("blocked_reason_required")
    if normalized.overwrite_result.get("status") == "allowed":
        raise ValidationError("overwrite_result_allowed")
    for field_name in ("delete_result", "dependency_install_result", "test_execution_result", "deployment_result", "public_publish_result"):
        result_map = getattr(normalized, field_name)
        if result_map.get("status") == "allowed":
            raise ValidationError(f"{field_name}_allowed")
    if normalized.path_safety_result and not isinstance(normalized.path_safety_result, dict):
        raise ValidationError("path_safety_result_must_be_mapping")
    if normalized.protected_file_result and not isinstance(normalized.protected_file_result, dict):
        raise ValidationError("protected_file_result_must_be_mapping")
    if normalized.secret_scan_result and not isinstance(normalized.secret_scan_result, dict):
        raise ValidationError("secret_scan_result_must_be_mapping")
    if normalized.private_data_scan_result and not isinstance(normalized.private_data_scan_result, dict):
        raise ValidationError("private_data_scan_result_must_be_mapping")
    if not _safe_text(normalized.write_result_id):
        raise ValidationError("write_result_id_required")
    return True


def summarize_sandbox_artifact_write_result_v1(result: Any) -> SandboxArtifactWriteSummary:
    normalized = _result_like(result)
    blocked_count = len(normalized.blocked_files)
    if normalized.blocked_reason:
        blocked_count = max(blocked_count, len(_dedupe_preserve(normalized.blocked_reason.split(";"))))
    return SandboxArtifactWriteSummary(
        summary_type=SANDBOX_ARTIFACT_WRITE_SUMMARY_TYPE_V1,
        write_result_id=normalized.write_result_id,
        execution_request_id=normalized.execution_request_id,
        dry_run=normalized.dry_run,
        blocked_count=blocked_count,
        would_create_count=len(normalized.would_create_files),
        partial_result=normalized.partial_result,
        chunking_required=normalized.chunking_required,
        recommended_next_step=normalized.recommended_next_step,
    )


def to_sandbox_artifact_write_json_safe_v1(value: Any) -> Any:
    return _json_safe(value)


def build_initial_sandbox_artifact_writer_examples_v1() -> list[SandboxArtifactWriteResult]:
    scaffold_examples = build_initial_code_scaffold_examples_v1()
    by_name = {packet.safe_metadata.get("example_name", packet.scaffold_id): packet for packet in scaffold_examples}
    examples: list[SandboxArtifactWriteResult] = []

    def _pack(request: Any, decision: Any, scaffold: Any, *, sandbox_root: str | None = None, example_name: str) -> SandboxArtifactWriteResult:
        result = execute_sandbox_artifact_write_v1(request, decision, scaffold, sandbox_root=sandbox_root)
        payload = to_sandbox_artifact_write_json_safe_v1(result)
        payload["write_result_id"] = example_name
        payload["safe_metadata"] = {**(payload.get("safe_metadata") or {}), "example_name": example_name}
        return _result_like(payload)

    wifi_request = ArtifactWriteRequest(
        write_request_id="wifi_rf_dry_run_write_request",
        source_scaffold_id=by_name["wifi_rf_self_care_code_scaffold"].scaffold_id,
        source_manifest_id=by_name["wifi_rf_self_care_code_scaffold"].source_manifest_id,
        project_title=by_name["wifi_rf_self_care_code_scaffold"].project_title,
        requested_root="sandbox_artifacts/wifi_rf",
        allowed_root="sandbox_artifacts/wifi_rf",
        requested_entries=[_entry_from_any(entry) for entry in to_code_scaffold_json_safe_v1(by_name["wifi_rf_self_care_code_scaffold"]).get("generated_entries", [])],
        write_mode="dry_run",
        overwrite_policy="no_overwrite",
        create_directories_requested=False,
        edit_existing_files_requested=False,
        delete_requested=False,
        executable_files_requested=False,
        dependency_install_requested=False,
        test_execution_requested=False,
        deployment_requested=False,
        public_publish_requested=False,
        owner_approval_present=False,
        operator_approval_present=False,
        sandbox_only=False,
        dry_run_only=True,
        risk_labels=["covert_tracking", "diagnosis_treatment", "deployment"],
        boundary_requirements=["consent-based local research only", "no covert tracking", "no diagnosis authority"],
        capability_class="prepare_scaffold",
        requested_file_count=len(to_code_scaffold_json_safe_v1(by_name["wifi_rf_self_care_code_scaffold"]).get("generated_entries", [])),
        requested_total_size_estimate=sum(len(_safe_text(entry.get("content"))) for entry in to_code_scaffold_json_safe_v1(by_name["wifi_rf_self_care_code_scaffold"]).get("generated_entries", [])),
        quality_preservation_notes=["preserve manifest lineage", "preserve scaffold lineage"],
        public_claim_allowed=False,
        iss_internal_reference_allowed=True,
        learning_claimed=False,
        runtime_authority=False,
        writes_state=False,
        model_provider_used=False,
        safe_metadata={"example_name": "wifi_rf_dry_run_write_result"},
    )
    wifi_decision = evaluate_artifact_write_boundary_v1(wifi_request)
    examples.append(_pack(wifi_request, wifi_decision, by_name["wifi_rf_self_care_code_scaffold"], sandbox_root="sandbox_artifacts/wifi_rf", example_name="wifi_rf_dry_run_write_result"))

    static_request = ArtifactWriteRequest(
        write_request_id="static_website_dry_run_write_request",
        source_scaffold_id=by_name["software_product_static_web_code_scaffold"].scaffold_id,
        source_manifest_id=by_name["software_product_static_web_code_scaffold"].source_manifest_id,
        project_title=by_name["software_product_static_web_code_scaffold"].project_title,
        requested_root="sandbox_artifacts/static_website",
        allowed_root="sandbox_artifacts/static_website",
        requested_entries=[_entry_from_any(entry) for entry in to_code_scaffold_json_safe_v1(by_name["software_product_static_web_code_scaffold"]).get("generated_entries", [])],
        write_mode="dry_run",
        overwrite_policy="no_overwrite",
        create_directories_requested=False,
        edit_existing_files_requested=False,
        delete_requested=False,
        executable_files_requested=False,
        dependency_install_requested=False,
        test_execution_requested=False,
        deployment_requested=False,
        public_publish_requested=False,
        owner_approval_present=True,
        operator_approval_present=False,
        sandbox_only=True,
        dry_run_only=True,
        risk_labels=[],
        boundary_requirements=["sandbox create only", "no deployment authority"],
        capability_class="prepare_scaffold",
        requested_file_count=len(to_code_scaffold_json_safe_v1(by_name["software_product_static_web_code_scaffold"]).get("generated_entries", [])),
        requested_total_size_estimate=sum(len(_safe_text(entry.get("content"))) for entry in to_code_scaffold_json_safe_v1(by_name["software_product_static_web_code_scaffold"]).get("generated_entries", [])),
        quality_preservation_notes=["preserve manifest lineage", "preserve scaffold lineage"],
        public_claim_allowed=False,
        iss_internal_reference_allowed=True,
        learning_claimed=False,
        runtime_authority=False,
        writes_state=False,
        model_provider_used=False,
        safe_metadata={"example_name": "static_website_dry_run_write_result"},
    )
    static_decision = evaluate_artifact_write_boundary_v1(static_request)
    examples.append(_pack(static_request, static_decision, by_name["software_product_static_web_code_scaffold"], sandbox_root="sandbox_artifacts/static_website", example_name="static_website_dry_run_write_result"))

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
    large_request = ArtifactWriteRequest(
        write_request_id="large_scaffold_chunking_dry_run_request",
        source_scaffold_id=by_name["metamaterials_research_code_scaffold"].scaffold_id,
        source_manifest_id=by_name["metamaterials_research_code_scaffold"].source_manifest_id,
        project_title=by_name["metamaterials_research_code_scaffold"].project_title,
        requested_root="sandbox_artifacts/large_scaffold",
        allowed_root="sandbox_artifacts/large_scaffold",
        requested_entries=large_entries,
        write_mode="sandbox_create_only",
        overwrite_policy="no_overwrite",
        create_directories_requested=True,
        edit_existing_files_requested=False,
        delete_requested=False,
        executable_files_requested=False,
        dependency_install_requested=False,
        test_execution_requested=False,
        deployment_requested=False,
        public_publish_requested=False,
        owner_approval_present=False,
        operator_approval_present=False,
        sandbox_only=True,
        dry_run_only=True,
        risk_labels=[],
        boundary_requirements=["chunking required", "preserve capability"],
        capability_class="prepare_scaffold",
        requested_file_count=len(large_entries),
        requested_total_size_estimate=sum(len(_safe_text(entry.get("content"))) for entry in large_entries),
        quality_preservation_notes=["preserve manifest lineage", "chunking required"],
        public_claim_allowed=False,
        iss_internal_reference_allowed=True,
        learning_claimed=False,
        runtime_authority=False,
        writes_state=False,
        model_provider_used=False,
        safe_metadata={"example_name": "large_scaffold_chunking_dry_run_result"},
    )
    large_decision = evaluate_artifact_write_boundary_v1(large_request)
    examples.append(_pack(large_request, large_decision, by_name["metamaterials_research_code_scaffold"], sandbox_root="sandbox_artifacts/large_scaffold", example_name="large_scaffold_chunking_dry_run_result"))

    env_request = ArtifactWriteRequest(
        write_request_id="env_entry_blocked_request",
        source_scaffold_id=by_name["software_product_static_web_code_scaffold"].scaffold_id,
        source_manifest_id=by_name["software_product_static_web_code_scaffold"].source_manifest_id,
        project_title=by_name["software_product_static_web_code_scaffold"].project_title,
        requested_root="sandbox_artifacts/env_blocked",
        allowed_root="sandbox_artifacts/env_blocked",
        requested_entries=[
            {
                "path": ".env",
                "file_type": "dotenv",
                "content_kind": "placeholder_only",
                "content": "API_KEY=secret\n",
                "generation_method": "validated_placeholder",
                "overwrite_allowed": False,
                "executable": False,
                "contains_secret": True,
                "contains_private_data": False,
                "validation_command": "env validation",
                "owner_approval_required": True,
                "safe_metadata": {"source_path": ".env"},
            }
        ],
        write_mode="dry_run",
        overwrite_policy="no_overwrite",
        create_directories_requested=False,
        edit_existing_files_requested=False,
        delete_requested=False,
        executable_files_requested=False,
        dependency_install_requested=False,
        test_execution_requested=False,
        deployment_requested=False,
        public_publish_requested=False,
        owner_approval_present=False,
        operator_approval_present=False,
        sandbox_only=False,
        dry_run_only=True,
        risk_labels=["secret_data"],
        boundary_requirements=["secrets blocked"],
        capability_class="prepare_scaffold",
        requested_file_count=1,
        requested_total_size_estimate=len("API_KEY=secret\n"),
        quality_preservation_notes=["preserve manifest lineage"],
        public_claim_allowed=False,
        iss_internal_reference_allowed=True,
        learning_claimed=False,
        runtime_authority=False,
        writes_state=False,
        model_provider_used=False,
        safe_metadata={"example_name": "env_entry_blocked_dry_run_result"},
    )
    env_decision = evaluate_artifact_write_boundary_v1(env_request)
    examples.append(_pack(env_request, env_decision, by_name["software_product_static_web_code_scaffold"], sandbox_root="sandbox_artifacts/env_blocked", example_name="env_entry_blocked_dry_run_result"))

    protected_request = ArtifactWriteRequest(
        write_request_id="protected_runtime_path_blocked_request",
        source_scaffold_id=by_name["software_product_static_web_code_scaffold"].scaffold_id,
        source_manifest_id=by_name["software_product_static_web_code_scaffold"].source_manifest_id,
        project_title=by_name["software_product_static_web_code_scaffold"].project_title,
        requested_root="sandbox_artifacts/protected_blocked",
        allowed_root="sandbox_artifacts/protected_blocked",
        requested_entries=[
            {
                "path": "weslr/chat_responder.py",
                "file_type": "python",
                "content_kind": "python_module_template",
                "content": "# protected\n",
                "generation_method": "validated_template",
                "overwrite_allowed": False,
                "executable": False,
                "contains_secret": False,
                "contains_private_data": False,
                "validation_command": "protected validation",
                "owner_approval_required": True,
                "safe_metadata": {"source_path": "weslr/chat_responder.py"},
            }
        ],
        write_mode="dry_run",
        overwrite_policy="no_overwrite",
        create_directories_requested=False,
        edit_existing_files_requested=False,
        delete_requested=False,
        executable_files_requested=False,
        dependency_install_requested=False,
        test_execution_requested=False,
        deployment_requested=False,
        public_publish_requested=False,
        owner_approval_present=False,
        operator_approval_present=False,
        sandbox_only=False,
        dry_run_only=True,
        risk_labels=["protected_path"],
        boundary_requirements=["protected runtime paths blocked"],
        capability_class="prepare_scaffold",
        requested_file_count=1,
        requested_total_size_estimate=len("# protected\n"),
        quality_preservation_notes=["preserve manifest lineage"],
        public_claim_allowed=False,
        iss_internal_reference_allowed=True,
        learning_claimed=False,
        runtime_authority=False,
        writes_state=False,
        model_provider_used=False,
        safe_metadata={"example_name": "protected_runtime_path_blocked_result"},
    )
    protected_decision = evaluate_artifact_write_boundary_v1(protected_request)
    examples.append(_pack(protected_request, protected_decision, by_name["software_product_static_web_code_scaffold"], sandbox_root="sandbox_artifacts/protected_blocked", example_name="protected_runtime_path_blocked_result"))

    delete_request = ArtifactWriteRequest(
        write_request_id="delete_request_blocked_request",
        source_scaffold_id=by_name["unknown_domain_code_scaffold"].scaffold_id,
        source_manifest_id=by_name["unknown_domain_code_scaffold"].source_manifest_id,
        project_title=by_name["unknown_domain_code_scaffold"].project_title,
        requested_root="sandbox_artifacts/delete_blocked",
        allowed_root="sandbox_artifacts/delete_blocked",
        requested_entries=[
            {
                "path": "docs/delete-me.md",
                "file_type": "markdown",
                "content_kind": "markdown_template",
                "content": "delete request placeholder\n",
                "generation_method": "validated_placeholder",
                "overwrite_allowed": False,
                "executable": False,
                "contains_secret": False,
                "contains_private_data": False,
                "validation_command": "delete validation",
                "owner_approval_required": True,
                "safe_metadata": {"source_path": "docs/delete-me.md"},
            }
        ],
        write_mode="owner_approved_delete",
        overwrite_policy="blocked",
        create_directories_requested=False,
        edit_existing_files_requested=False,
        delete_requested=True,
        executable_files_requested=False,
        dependency_install_requested=False,
        test_execution_requested=False,
        deployment_requested=False,
        public_publish_requested=False,
        owner_approval_present=False,
        operator_approval_present=False,
        sandbox_only=False,
        dry_run_only=True,
        risk_labels=["delete"],
        boundary_requirements=["delete blocked"],
        capability_class="prepare_patch_plan",
        requested_file_count=1,
        requested_total_size_estimate=len("delete request placeholder\n"),
        quality_preservation_notes=["preserve manifest lineage"],
        public_claim_allowed=False,
        iss_internal_reference_allowed=True,
        learning_claimed=False,
        runtime_authority=False,
        writes_state=False,
        model_provider_used=False,
        safe_metadata={"example_name": "delete_request_blocked_result"},
    )
    delete_decision = evaluate_artifact_write_boundary_v1(delete_request)
    examples.append(_pack(delete_request, delete_decision, by_name["unknown_domain_code_scaffold"], sandbox_root="sandbox_artifacts/delete_blocked", example_name="delete_request_blocked_result"))

    missing_root_request = ArtifactWriteRequest(
        write_request_id="missing_sandbox_root_dry_run_request",
        source_scaffold_id=by_name["theory_of_mind_conceptual_code_scaffold"].scaffold_id,
        source_manifest_id=by_name["theory_of_mind_conceptual_code_scaffold"].source_manifest_id,
        project_title=by_name["theory_of_mind_conceptual_code_scaffold"].project_title,
        requested_root="sandbox_artifacts/missing_root",
        allowed_root="sandbox_artifacts/missing_root",
        requested_entries=[_entry_from_any(entry) for entry in to_code_scaffold_json_safe_v1(by_name["theory_of_mind_conceptual_code_scaffold"]).get("generated_entries", [])],
        write_mode="dry_run",
        overwrite_policy="no_overwrite",
        create_directories_requested=False,
        edit_existing_files_requested=False,
        delete_requested=False,
        executable_files_requested=False,
        dependency_install_requested=False,
        test_execution_requested=False,
        deployment_requested=False,
        public_publish_requested=False,
        owner_approval_present=False,
        operator_approval_present=False,
        sandbox_only=False,
        dry_run_only=True,
        risk_labels=[],
        boundary_requirements=["missing sandbox root is dry-run safe"],
        capability_class="prepare_scaffold",
        requested_file_count=len(to_code_scaffold_json_safe_v1(by_name["theory_of_mind_conceptual_code_scaffold"]).get("generated_entries", [])),
        requested_total_size_estimate=sum(len(_safe_text(entry.get("content"))) for entry in to_code_scaffold_json_safe_v1(by_name["theory_of_mind_conceptual_code_scaffold"]).get("generated_entries", [])),
        quality_preservation_notes=["preserve manifest lineage"],
        public_claim_allowed=False,
        iss_internal_reference_allowed=True,
        learning_claimed=False,
        runtime_authority=False,
        writes_state=False,
        model_provider_used=False,
        safe_metadata={"example_name": "missing_sandbox_root_dry_run_allowed_result"},
    )
    missing_root_decision = evaluate_artifact_write_boundary_v1(missing_root_request)
    examples.append(_pack(missing_root_request, missing_root_decision, by_name["theory_of_mind_conceptual_code_scaffold"], sandbox_root=None, example_name="missing_sandbox_root_dry_run_allowed_result"))

    real_write_request = ArtifactWriteRequest(
        write_request_id="real_write_requested_blocked_request",
        source_scaffold_id=by_name["ai_agent_architecture_code_scaffold"].scaffold_id,
        source_manifest_id=by_name["ai_agent_architecture_code_scaffold"].source_manifest_id,
        project_title=by_name["ai_agent_architecture_code_scaffold"].project_title,
        requested_root="sandbox_artifacts/real_write_blocked",
        allowed_root="sandbox_artifacts/real_write_blocked",
        requested_entries=[_entry_from_any(entry) for entry in to_code_scaffold_json_safe_v1(by_name["ai_agent_architecture_code_scaffold"]).get("generated_entries", [])],
        write_mode="sandbox_create_only",
        overwrite_policy="no_overwrite",
        create_directories_requested=True,
        edit_existing_files_requested=False,
        delete_requested=False,
        executable_files_requested=False,
        dependency_install_requested=False,
        test_execution_requested=False,
        deployment_requested=False,
        public_publish_requested=False,
        owner_approval_present=True,
        operator_approval_present=False,
        sandbox_only=True,
        dry_run_only=False,
        risk_labels=[],
        boundary_requirements=["real writes blocked in v1"],
        capability_class="prepare_scaffold",
        requested_file_count=len(to_code_scaffold_json_safe_v1(by_name["ai_agent_architecture_code_scaffold"]).get("generated_entries", [])),
        requested_total_size_estimate=sum(len(_safe_text(entry.get("content"))) for entry in to_code_scaffold_json_safe_v1(by_name["ai_agent_architecture_code_scaffold"]).get("generated_entries", [])),
        quality_preservation_notes=["preserve manifest lineage"],
        public_claim_allowed=False,
        iss_internal_reference_allowed=True,
        learning_claimed=False,
        runtime_authority=False,
        writes_state=False,
        model_provider_used=False,
        safe_metadata={"example_name": "real_write_requested_blocked_result"},
    )
    real_write_decision = evaluate_artifact_write_boundary_v1(real_write_request)
    examples.append(_pack(real_write_request, real_write_decision, by_name["ai_agent_architecture_code_scaffold"], sandbox_root="sandbox_artifacts/real_write_blocked", example_name="real_write_requested_blocked_result"))

    return examples
