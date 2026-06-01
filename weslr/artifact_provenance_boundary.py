"""Metadata-only artifact provenance boundary v1.

This module defines provenance records and bundles for artifact lineage,
tamper evidence, and validation metadata. It is pure, deterministic,
import-safe, and fail-closed.
No file reads. No file writes. No hashing real files. No subprocess.
No model/provider/search/advisor calls. No chat routing. No runtime behavior changes.
No `.weslr` access.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from hashlib import sha256
import re
from typing import Any, Iterable, Mapping

from weslr.code_scaffold_generator import build_initial_code_scaffold_examples_v1
from weslr.file_manifest_builder import build_initial_file_manifest_examples_v1

HELPER_TYPE_V1 = "artifact_provenance_boundary_v1"
ARTIFACT_PROVENANCE_RECORD_TYPE_V1 = "artifact_provenance_record_v1"
ARTIFACT_PROVENANCE_BUNDLE_TYPE_V1 = "artifact_provenance_bundle_v1"
ARTIFACT_PROVENANCE_SUMMARY_TYPE_V1 = "artifact_provenance_summary_v1"

ALLOWED_TAMPER_EVIDENCE_STATUSES_V1 = {
    "not_yet_hashed",
    "hash_recorded",
    "hash_verified",
    "hash_mismatch",
    "missing_artifact",
    "provenance_incomplete",
    "verification_not_run",
}

ALLOWED_GENERATOR_TYPES_V1 = {
    "deterministic_template",
    "pattern_library",
    "schema_generated",
    "llm_candidate",
    "owner_supplied",
    "manual_edit",
    "unknown_generator",
}

ALLOWED_VERIFICATION_STATUSES_V1 = {
    "verification_not_run",
    "verified",
    "failed",
    "incomplete",
    "not_applicable",
    "mismatch_observed",
}

ALLOWED_AUTHORITY_LEVELS_V1 = {
    "none",
    "candidate_only",
    "owner_review",
    "operator_review",
    "sandbox_controlled",
    "manual",
    "unknown",
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
    "public iss",
    "iss wording",
    "public intelligence claim",
    "public readiness claim",
    "public validation claim",
    "official validation",
    "production safety",
    "official turing",
    "turing test",
    "turing result",
    "agi claim",
    "consciousness claim",
    "sentience claim",
    "certification claim",
    "certified intelligence",
)

CLAIM_BASE_TERMS_V1 = {"agi", "consciousness", "sentience", "turing", "certification", "validation", "production"}
CLAIM_QUALIFIERS_V1 = {"claim", "claims", "claimed", "official", "certification", "certified", "public", "readiness", "safety"}

PROTECTED_EXACT_PATHS_V1 = {
    "weslr/chat_responder.py",
    "weslr/main.py",
    "dialogue.py",
    "chat_ui.py",
    ".weslr",
    ".env",
}

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
    "private_key",
    "id_rsa",
    "id_ed25519",
}

PROTECTED_PATH_SUFFIXES_V1 = {".pem", ".key", ".p12", ".pfx", ".pkcs12"}


class ValidationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ArtifactProvenanceRecord:
    provenance_record_id: str
    artifact_path: str
    artifact_type: str
    content_hash: str
    hash_algorithm: str
    source_project_brief_id: str
    source_architecture_id: str
    source_stack_decision_id: str
    source_manifest_id: str
    source_scaffold_id: str
    source_write_request_id: str
    source_write_decision_id: str
    source_write_result_id: str
    owner_approval_id: str
    operator_approval_id: str
    validation_report_id: str
    created_timestamp: str
    modified_timestamp: str
    generator_type: str
    model_provider_used: bool
    provider_trace_id: str
    authority_level_used: str
    sandbox_root: str
    write_mode: str
    tamper_evidence_status: str
    verification_status: str
    public_claim_allowed: bool
    runtime_authority: bool
    writes_state: bool
    safe_metadata: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class ArtifactProvenanceBundle:
    provenance_bundle_id: str
    bundle_type: str
    records: list[ArtifactProvenanceRecord]
    safe_metadata: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class ArtifactProvenanceSummary:
    summary_type: str
    provenance_bundle_id: str
    record_count: int
    generator_types: list[str]
    tamper_evidence_statuses: list[str]
    verification_statuses: list[str]
    model_provider_use_count: int
    public_claim_allowed_count: int
    runtime_authority_count: int
    writes_state_count: int


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


def _as_mapping(value: Any) -> Mapping[str, Any]:
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, Mapping):
        return value
    raise ValidationError("mapping_or_dataclass_required")


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
        return [_json_safe(item) for item in sorted(value, key=lambda item: _safe_text(item))]
    return value


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
        if any(phrase in blob for phrase in FORBIDDEN_CLAIM_PHRASES_V1):
            return True
        for term in CLAIM_BASE_TERMS_V1:
            if term in blob and any(q in blob for q in CLAIM_QUALIFIERS_V1) and not _contains_negated_marker(blob, term):
                return True
    return False


def _contains_forbidden_field(value: Any) -> str:
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = _normalize_text(key)
            if key_text in FORBIDDEN_FIELD_NAMES_V1:
                return key_text
            if any(marker in key_text for marker in ("hidden_prompt", "raw_prompt", "raw_answer", "raw_transcript", "private_content", "raw_private_content", "secret_token", "private_key", "api_key", "token", "password", "credential")):
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


def _is_safe_relative_path(path: str) -> bool:
    text = _safe_text(path).replace("\\", "/")
    if not text:
        return False
    if text.startswith(("/", "~", "./", "../")):
        return False
    if re.match(r"^[a-zA-Z]:", text):
        return False
    if any(part in {".", ".."} for part in text.split("/")):
        return False
    return True


def _is_protected_path(path: str) -> bool:
    text = _safe_text(path).replace("\\", "/").lower()
    if text in PROTECTED_EXACT_PATHS_V1:
        return True
    if any(marker in text for marker in PROTECTED_PATH_MARKERS_V1):
        return True
    basename = text.rsplit("/", 1)[-1]
    if any(basename.endswith(suffix) for suffix in PROTECTED_PATH_SUFFIXES_V1):
        return True
    return False


def _deterministic_id(*parts: Any, prefix: str) -> str:
    digest = sha256("|".join(_safe_text(part) for part in parts).encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{digest}"


def _record_like(value: Any) -> ArtifactProvenanceRecord:
    if isinstance(value, ArtifactProvenanceRecord):
        return value
    mapping = _as_mapping(value)
    safe_metadata = mapping.get("safe_metadata", None)
    if safe_metadata is not None and not isinstance(safe_metadata, Mapping):
        raise ValidationError("safe_metadata_must_be_mapping")
    return ArtifactProvenanceRecord(
        provenance_record_id=_safe_text(mapping.get("provenance_record_id")),
        artifact_path=_safe_text(mapping.get("artifact_path")),
        artifact_type=_safe_text(mapping.get("artifact_type")),
        content_hash=_safe_text(mapping.get("content_hash")),
        hash_algorithm=_safe_text(mapping.get("hash_algorithm")),
        source_project_brief_id=_safe_text(mapping.get("source_project_brief_id")),
        source_architecture_id=_safe_text(mapping.get("source_architecture_id")),
        source_stack_decision_id=_safe_text(mapping.get("source_stack_decision_id")),
        source_manifest_id=_safe_text(mapping.get("source_manifest_id")),
        source_scaffold_id=_safe_text(mapping.get("source_scaffold_id")),
        source_write_request_id=_safe_text(mapping.get("source_write_request_id")),
        source_write_decision_id=_safe_text(mapping.get("source_write_decision_id")),
        source_write_result_id=_safe_text(mapping.get("source_write_result_id")),
        owner_approval_id=_safe_text(mapping.get("owner_approval_id")),
        operator_approval_id=_safe_text(mapping.get("operator_approval_id")),
        validation_report_id=_safe_text(mapping.get("validation_report_id")),
        created_timestamp=_safe_text(mapping.get("created_timestamp")),
        modified_timestamp=_safe_text(mapping.get("modified_timestamp")),
        generator_type=_safe_text(mapping.get("generator_type")),
        model_provider_used=bool(mapping.get("model_provider_used")),
        provider_trace_id=_safe_text(mapping.get("provider_trace_id")),
        authority_level_used=_safe_text(mapping.get("authority_level_used")),
        sandbox_root=_safe_text(mapping.get("sandbox_root")),
        write_mode=_safe_text(mapping.get("write_mode")),
        tamper_evidence_status=_safe_text(mapping.get("tamper_evidence_status")),
        verification_status=_safe_text(mapping.get("verification_status")),
        public_claim_allowed=bool(mapping.get("public_claim_allowed")),
        runtime_authority=bool(mapping.get("runtime_authority")),
        writes_state=bool(mapping.get("writes_state")),
        safe_metadata=dict(safe_metadata or {}),
    )


def _bundle_like(value: Any) -> ArtifactProvenanceBundle:
    if isinstance(value, ArtifactProvenanceBundle):
        return value
    mapping = _as_mapping(value)
    safe_metadata = mapping.get("safe_metadata", None)
    if safe_metadata is not None and not isinstance(safe_metadata, Mapping):
        raise ValidationError("safe_metadata_must_be_mapping")
    return ArtifactProvenanceBundle(
        provenance_bundle_id=_safe_text(mapping.get("provenance_bundle_id")),
        bundle_type=_safe_text(mapping.get("bundle_type")),
        records=[_record_like(item) for item in mapping.get("records", [])],
        safe_metadata=dict(safe_metadata or {}),
    )


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------


def build_artifact_provenance_record_v1(
    *,
    provenance_record_id: str,
    artifact_path: str,
    artifact_type: str,
    content_hash: str,
    hash_algorithm: str,
    source_project_brief_id: str,
    source_architecture_id: str,
    source_stack_decision_id: str,
    source_manifest_id: str,
    source_scaffold_id: str,
    source_write_request_id: str,
    source_write_decision_id: str,
    source_write_result_id: str,
    owner_approval_id: str,
    operator_approval_id: str,
    validation_report_id: str,
    created_timestamp: str,
    modified_timestamp: str,
    generator_type: str,
    model_provider_used: bool,
    provider_trace_id: str,
    authority_level_used: str,
    sandbox_root: str,
    write_mode: str,
    tamper_evidence_status: str,
    verification_status: str,
    public_claim_allowed: bool,
    runtime_authority: bool,
    writes_state: bool,
    safe_metadata: dict[str, Any] | None = None,
) -> ArtifactProvenanceRecord:
    record = ArtifactProvenanceRecord(
        provenance_record_id=provenance_record_id,
        artifact_path=artifact_path,
        artifact_type=artifact_type,
        content_hash=content_hash,
        hash_algorithm=hash_algorithm,
        source_project_brief_id=source_project_brief_id,
        source_architecture_id=source_architecture_id,
        source_stack_decision_id=source_stack_decision_id,
        source_manifest_id=source_manifest_id,
        source_scaffold_id=source_scaffold_id,
        source_write_request_id=source_write_request_id,
        source_write_decision_id=source_write_decision_id,
        source_write_result_id=source_write_result_id,
        owner_approval_id=owner_approval_id,
        operator_approval_id=operator_approval_id,
        validation_report_id=validation_report_id,
        created_timestamp=created_timestamp,
        modified_timestamp=modified_timestamp,
        generator_type=generator_type,
        model_provider_used=model_provider_used,
        provider_trace_id=provider_trace_id,
        authority_level_used=authority_level_used,
        sandbox_root=sandbox_root,
        write_mode=write_mode,
        tamper_evidence_status=tamper_evidence_status,
        verification_status=verification_status,
        public_claim_allowed=public_claim_allowed,
        runtime_authority=runtime_authority,
        writes_state=writes_state,
        safe_metadata=dict(safe_metadata or {}),
    )
    validate_artifact_provenance_record_v1(record)
    return record


def build_artifact_provenance_bundle_v1(
    *,
    provenance_bundle_id: str,
    records: list[Any],
    bundle_type: str = ARTIFACT_PROVENANCE_BUNDLE_TYPE_V1,
    safe_metadata: dict[str, Any] | None = None,
) -> ArtifactProvenanceBundle:
    bundle = ArtifactProvenanceBundle(
        provenance_bundle_id=provenance_bundle_id,
        bundle_type=bundle_type,
        records=[_record_like(item) for item in records],
        safe_metadata=dict(safe_metadata or {}),
    )
    validate_artifact_provenance_bundle_v1(bundle)
    return bundle


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


def validate_artifact_provenance_record_v1(record: Any) -> bool:
    original = _as_mapping(record)
    forbidden = _contains_forbidden_field(original)
    if forbidden:
        raise ValidationError(f"forbidden_field_detected:{forbidden}")
    normalized = _record_like(record)
    if _contains_forbidden_claim_marker(normalized):
        raise ValidationError("forbidden_claim_marker_detected")
    if not _safe_text(normalized.provenance_record_id):
        raise ValidationError("provenance_record_id_required")
    if not _safe_text(normalized.artifact_path):
        raise ValidationError("artifact_path_required")
    if not _safe_text(normalized.artifact_type):
        raise ValidationError("artifact_type_required")
    if not _safe_text(normalized.content_hash):
        raise ValidationError("content_hash_required")
    if not _safe_text(normalized.hash_algorithm):
        raise ValidationError("hash_algorithm_required")
    if not _safe_text(normalized.source_project_brief_id):
        raise ValidationError("missing_required_lineage")
    if not _safe_text(normalized.source_architecture_id):
        raise ValidationError("missing_required_lineage")
    if not _safe_text(normalized.source_stack_decision_id):
        raise ValidationError("missing_required_lineage")
    if not _safe_text(normalized.source_manifest_id):
        raise ValidationError("missing_required_lineage")
    if not _safe_text(normalized.source_scaffold_id):
        raise ValidationError("missing_required_lineage")
    if not _safe_text(normalized.source_write_request_id):
        raise ValidationError("missing_required_lineage")
    if not _safe_text(normalized.source_write_decision_id):
        raise ValidationError("missing_required_lineage")
    if not _safe_text(normalized.source_write_result_id):
        raise ValidationError("missing_required_lineage")
    if not _safe_text(normalized.owner_approval_id):
        raise ValidationError("owner_approval_id_required")
    if not _safe_text(normalized.operator_approval_id):
        raise ValidationError("operator_approval_id_required")
    if not _safe_text(normalized.validation_report_id):
        raise ValidationError("validation_report_id_required")
    if not _safe_text(normalized.created_timestamp):
        raise ValidationError("created_timestamp_required")
    if not _safe_text(normalized.modified_timestamp):
        raise ValidationError("modified_timestamp_required")
    if normalized.generator_type not in ALLOWED_GENERATOR_TYPES_V1:
        raise ValidationError("unknown_generator_type")
    if normalized.tamper_evidence_status not in ALLOWED_TAMPER_EVIDENCE_STATUSES_V1:
        raise ValidationError("unknown_tamper_evidence_status")
    if normalized.verification_status not in ALLOWED_VERIFICATION_STATUSES_V1:
        raise ValidationError("unknown_verification_status")
    if normalized.authority_level_used not in ALLOWED_AUTHORITY_LEVELS_V1:
        raise ValidationError("unknown_authority_level_used")
    if not _is_safe_relative_path(normalized.artifact_path):
        raise ValidationError("unsafe_artifact_path")
    if _is_protected_path(normalized.artifact_path):
        raise ValidationError("protected_artifact_path")
    if normalized.public_claim_allowed:
        raise ValidationError("public_claim_allowed_must_be_false")
    if normalized.runtime_authority:
        raise ValidationError("runtime_authority_must_be_false")
    if normalized.writes_state:
        raise ValidationError("writes_state_must_be_false")
    if normalized.model_provider_used and not _safe_text(normalized.provider_trace_id):
        raise ValidationError("provider_trace_id_required_when_provider_used")
    if normalized.model_provider_used and normalized.authority_level_used not in {"candidate_only", "owner_review", "operator_review", "sandbox_controlled", "manual", "none"}:
        raise ValidationError("provider_must_not_grant_authority")
    if normalized.validation_report_id in {normalized.owner_approval_id, normalized.operator_approval_id}:
        raise ValidationError("approval_treated_as_validation")
    if normalized.safe_metadata is not None and not isinstance(normalized.safe_metadata, dict):
        raise ValidationError("safe_metadata_must_be_mapping")
    if normalized.safe_metadata and _contains_forbidden_field(normalized.safe_metadata):
        raise ValidationError("forbidden_field_detected:safe_metadata")
    if _contains_forbidden_claim_marker(normalized.safe_metadata or {}):
        raise ValidationError("forbidden_claim_marker_detected")
    if normalized.tamper_evidence_status == "provenance_incomplete":
        return True
    if any(not _safe_text(field) for field in (
        normalized.source_project_brief_id,
        normalized.source_architecture_id,
        normalized.source_stack_decision_id,
        normalized.source_manifest_id,
        normalized.source_scaffold_id,
        normalized.source_write_request_id,
        normalized.source_write_decision_id,
        normalized.source_write_result_id,
    )):
        raise ValidationError("missing_required_lineage")
    return True


def validate_artifact_provenance_bundle_v1(bundle: Any) -> bool:
    original = _as_mapping(bundle)
    forbidden = _contains_forbidden_field(original)
    if forbidden:
        raise ValidationError(f"forbidden_field_detected:{forbidden}")
    normalized = _bundle_like(bundle)
    if normalized.bundle_type not in {ARTIFACT_PROVENANCE_BUNDLE_TYPE_V1}:
        raise ValidationError("unknown_bundle_type")
    if not _safe_text(normalized.provenance_bundle_id):
        raise ValidationError("provenance_bundle_id_required")
    if not normalized.records:
        raise ValidationError("records_required")
    seen: set[str] = set()
    for record in normalized.records:
        validate_artifact_provenance_record_v1(record)
        if record.provenance_record_id in seen:
            raise ValidationError("duplicate_provenance_record_id")
        seen.add(record.provenance_record_id)
    if normalized.safe_metadata is not None and not isinstance(normalized.safe_metadata, dict):
        raise ValidationError("safe_metadata_must_be_mapping")
    if normalized.safe_metadata and _contains_forbidden_field(normalized.safe_metadata):
        raise ValidationError("forbidden_field_detected:safe_metadata")
    if _contains_forbidden_claim_marker(normalized.safe_metadata or {}):
        raise ValidationError("forbidden_claim_marker_detected")
    return True


# ---------------------------------------------------------------------------
# Summary / JSON safety
# ---------------------------------------------------------------------------


def summarize_artifact_provenance_bundle_v1(bundle: Any) -> ArtifactProvenanceSummary:
    normalized = _bundle_like(bundle)
    validate_artifact_provenance_bundle_v1(normalized)
    generator_types = _dedupe_preserve(record.generator_type for record in normalized.records)
    tamper_statuses = _dedupe_preserve(record.tamper_evidence_status for record in normalized.records)
    verification_statuses = _dedupe_preserve(record.verification_status for record in normalized.records)
    return ArtifactProvenanceSummary(
        summary_type=ARTIFACT_PROVENANCE_SUMMARY_TYPE_V1,
        provenance_bundle_id=normalized.provenance_bundle_id,
        record_count=len(normalized.records),
        generator_types=generator_types,
        tamper_evidence_statuses=tamper_statuses,
        verification_statuses=verification_statuses,
        model_provider_use_count=sum(1 for record in normalized.records if record.model_provider_used),
        public_claim_allowed_count=sum(1 for record in normalized.records if record.public_claim_allowed),
        runtime_authority_count=sum(1 for record in normalized.records if record.runtime_authority),
        writes_state_count=sum(1 for record in normalized.records if record.writes_state),
    )


def to_artifact_provenance_json_safe_v1(value: Any) -> Any:
    return _json_safe(value)


# ---------------------------------------------------------------------------
# Initial examples
# ---------------------------------------------------------------------------


def build_initial_artifact_provenance_examples_v1() -> list[ArtifactProvenanceRecord]:
    scaffold_examples = build_initial_code_scaffold_examples_v1()
    manifest_examples = build_initial_file_manifest_examples_v1()
    scaffold_by_id = {item.scaffold_id: item for item in scaffold_examples}
    manifest_by_id = {item.manifest_id: item for item in manifest_examples}

    def _record(**kwargs: Any) -> ArtifactProvenanceRecord:
        return build_artifact_provenance_record_v1(**kwargs)

    examples: list[ArtifactProvenanceRecord] = []

    examples.append(
        _record(
            provenance_record_id="static_website_scaffold_provenance",
            artifact_path="site/index.html",
            artifact_type="html",
            content_hash="sha256:placeholder-static-website-v1",
            hash_algorithm="sha256",
            source_project_brief_id="project_brief_static_website_v1",
            source_architecture_id="architecture_static_website_v1",
            source_stack_decision_id="stack_static_website_v1",
            source_manifest_id=manifest_by_id["software_product_static_web_file_manifest"].manifest_id,
            source_scaffold_id=scaffold_by_id["software_product_static_web_code_scaffold"].scaffold_id,
            source_write_request_id="static_website_write_request_v1",
            source_write_decision_id="static_website_write_decision_v1",
            source_write_result_id="static_website_write_result_v1",
            owner_approval_id="no_owner_approval_v1",
            operator_approval_id="no_operator_approval_v1",
            validation_report_id="validation_pending_static_website_v1",
            created_timestamp="2026-06-01T20:40:00+02:00",
            modified_timestamp="2026-06-01T20:40:00+02:00",
            generator_type="deterministic_template",
            model_provider_used=False,
            provider_trace_id="none",
            authority_level_used="none",
            sandbox_root="sandbox/site",
            write_mode="sandbox_create_only",
            tamper_evidence_status="hash_recorded",
            verification_status="verification_not_run",
            public_claim_allowed=False,
            runtime_authority=False,
            writes_state=False,
            safe_metadata={"example_name": "static_website_scaffold_provenance"},
        )
    )

    examples.append(
        _record(
            provenance_record_id="wifi_rf_self_care_scaffold_provenance",
            artifact_path="docs/PRIVACY_BOUNDARY.md",
            artifact_type="markdown",
            content_hash="sha256:placeholder-wifi-rf-v1",
            hash_algorithm="sha256",
            source_project_brief_id="project_brief_wifi_rf_self_care_v1",
            source_architecture_id="architecture_wifi_rf_self_care_v1",
            source_stack_decision_id="stack_wifi_rf_self_care_v1",
            source_manifest_id=manifest_by_id["wifi_rf_self_care_file_manifest"].manifest_id,
            source_scaffold_id=scaffold_by_id["wifi_rf_self_care_code_scaffold"].scaffold_id,
            source_write_request_id="wifi_rf_self_care_write_request_v1",
            source_write_decision_id="wifi_rf_self_care_write_decision_v1",
            source_write_result_id="wifi_rf_self_care_write_result_v1",
            owner_approval_id="no_owner_approval_v1",
            operator_approval_id="operator_review_pending_v1",
            validation_report_id="validation_pending_wifi_rf_v1",
            created_timestamp="2026-06-01T20:40:10+02:00",
            modified_timestamp="2026-06-01T20:40:10+02:00",
            generator_type="pattern_library",
            model_provider_used=False,
            provider_trace_id="none",
            authority_level_used="sandbox_controlled",
            sandbox_root="sandbox/wifi_rf",
            write_mode="sandbox_create_only",
            tamper_evidence_status="not_yet_hashed",
            verification_status="verification_not_run",
            public_claim_allowed=False,
            runtime_authority=False,
            writes_state=False,
            safe_metadata={"example_name": "wifi_rf_self_care_scaffold_provenance", "privacy_sensitive": True},
        )
    )

    examples.append(
        _record(
            provenance_record_id="medical_software_boundary_docs_provenance",
            artifact_path="docs/MEDICAL_BOUNDARY.md",
            artifact_type="markdown",
            content_hash="sha256:placeholder-medical-boundary-v1",
            hash_algorithm="sha256",
            source_project_brief_id="project_brief_medical_software_v1",
            source_architecture_id="architecture_medical_software_v1",
            source_stack_decision_id="stack_medical_software_v1",
            source_manifest_id=manifest_by_id["medical_software_pathway_file_manifest"].manifest_id,
            source_scaffold_id=scaffold_by_id["medical_software_pathway_code_scaffold"].scaffold_id,
            source_write_request_id="medical_boundary_write_request_v1",
            source_write_decision_id="medical_boundary_write_decision_v1",
            source_write_result_id="medical_boundary_write_result_v1",
            owner_approval_id="owner_review_required_v1",
            operator_approval_id="no_operator_approval_v1",
            validation_report_id="validation_pending_medical_boundary_v1",
            created_timestamp="2026-06-01T20:40:20+02:00",
            modified_timestamp="2026-06-01T20:40:20+02:00",
            generator_type="deterministic_template",
            model_provider_used=False,
            provider_trace_id="none",
            authority_level_used="owner_review",
            sandbox_root="sandbox/medical",
            write_mode="sandbox_create_only",
            tamper_evidence_status="verification_not_run",
            verification_status="verification_not_run",
            public_claim_allowed=False,
            runtime_authority=False,
            writes_state=False,
            safe_metadata={"example_name": "medical_software_boundary_docs_provenance", "boundary_doc": True},
        )
    )

    examples.append(
        _record(
            provenance_record_id="ai_system_research_scaffold_provenance",
            artifact_path="src/architecture.py",
            artifact_type="python",
            content_hash="sha256:placeholder-ai-system-v1",
            hash_algorithm="sha256",
            source_project_brief_id="project_brief_ai_system_research_v1",
            source_architecture_id="architecture_ai_system_research_v1",
            source_stack_decision_id="stack_ai_system_research_v1",
            source_manifest_id=manifest_by_id["ai_agent_architecture_file_manifest"].manifest_id,
            source_scaffold_id=scaffold_by_id["ai_agent_architecture_code_scaffold"].scaffold_id,
            source_write_request_id="ai_system_research_write_request_v1",
            source_write_decision_id="ai_system_research_write_decision_v1",
            source_write_result_id="ai_system_research_write_result_v1",
            owner_approval_id="no_owner_approval_v1",
            operator_approval_id="operator_review_pending_v1",
            validation_report_id="validation_pending_ai_system_v1",
            created_timestamp="2026-06-01T20:40:30+02:00",
            modified_timestamp="2026-06-01T20:40:30+02:00",
            generator_type="schema_generated",
            model_provider_used=False,
            provider_trace_id="none",
            authority_level_used="sandbox_controlled",
            sandbox_root="sandbox/ai_system",
            write_mode="sandbox_create_only",
            tamper_evidence_status="hash_verified",
            verification_status="verified",
            public_claim_allowed=False,
            runtime_authority=False,
            writes_state=False,
            safe_metadata={"example_name": "ai_system_research_scaffold_provenance", "research_scope": "architecture"},
        )
    )

    examples.append(
        _record(
            provenance_record_id="hash_mismatch_example",
            artifact_path="src/generated.py",
            artifact_type="python",
            content_hash="sha256:placeholder-hash-mismatch-v1",
            hash_algorithm="sha256",
            source_project_brief_id="project_brief_hash_mismatch_v1",
            source_architecture_id="architecture_hash_mismatch_v1",
            source_stack_decision_id="stack_hash_mismatch_v1",
            source_manifest_id=manifest_by_id["unknown_domain_file_manifest"].manifest_id,
            source_scaffold_id=scaffold_by_id["unknown_domain_code_scaffold"].scaffold_id,
            source_write_request_id="hash_mismatch_write_request_v1",
            source_write_decision_id="hash_mismatch_write_decision_v1",
            source_write_result_id="hash_mismatch_write_result_v1",
            owner_approval_id="owner_review_pending_v1",
            operator_approval_id="operator_review_pending_v1",
            validation_report_id="validation_pending_hash_mismatch_v1",
            created_timestamp="2026-06-01T20:40:40+02:00",
            modified_timestamp="2026-06-01T20:40:41+02:00",
            generator_type="manual_edit",
            model_provider_used=False,
            provider_trace_id="none",
            authority_level_used="manual",
            sandbox_root="sandbox/hash_mismatch",
            write_mode="sandbox_create_only",
            tamper_evidence_status="hash_mismatch",
            verification_status="failed",
            public_claim_allowed=False,
            runtime_authority=False,
            writes_state=False,
            safe_metadata={"example_name": "hash_mismatch_example", "tamper_notice": True},
        )
    )

    examples.append(
        _record(
            provenance_record_id="llm_candidate_provenance_example",
            artifact_path="src/llm_candidate.py",
            artifact_type="python",
            content_hash="sha256:placeholder-llm-candidate-v1",
            hash_algorithm="sha256",
            source_project_brief_id="project_brief_llm_candidate_v1",
            source_architecture_id="architecture_llm_candidate_v1",
            source_stack_decision_id="stack_llm_candidate_v1",
            source_manifest_id=manifest_by_id["theory_of_mind_conceptual_file_manifest"].manifest_id,
            source_scaffold_id=scaffold_by_id["theory_of_mind_conceptual_code_scaffold"].scaffold_id,
            source_write_request_id="llm_candidate_write_request_v1",
            source_write_decision_id="llm_candidate_write_decision_v1",
            source_write_result_id="llm_candidate_write_result_v1",
            owner_approval_id="operator_review_pending_v1",
            operator_approval_id="operator_review_pending_v1",
            validation_report_id="validation_pending_llm_candidate_v1",
            created_timestamp="2026-06-01T20:40:50+02:00",
            modified_timestamp="2026-06-01T20:40:50+02:00",
            generator_type="llm_candidate",
            model_provider_used=True,
            provider_trace_id="provider-trace-llm-candidate-v1",
            authority_level_used="candidate_only",
            sandbox_root="sandbox/llm_candidate",
            write_mode="sandbox_create_only",
            tamper_evidence_status="provenance_incomplete",
            verification_status="verification_not_run",
            public_claim_allowed=False,
            runtime_authority=False,
            writes_state=False,
            safe_metadata={"example_name": "llm_candidate_provenance_example", "provider_role": "candidate_material"},
        )
    )

    examples.append(
        _record(
            provenance_record_id="owner_manual_edit_provenance_example",
            artifact_path="docs/manual_edit.md",
            artifact_type="markdown",
            content_hash="sha256:placeholder-owner-edit-v1",
            hash_algorithm="sha256",
            source_project_brief_id="project_brief_owner_manual_edit_v1",
            source_architecture_id="architecture_owner_manual_edit_v1",
            source_stack_decision_id="stack_owner_manual_edit_v1",
            source_manifest_id=manifest_by_id["software_product_static_web_file_manifest"].manifest_id,
            source_scaffold_id=scaffold_by_id["software_product_static_web_code_scaffold"].scaffold_id,
            source_write_request_id="owner_manual_edit_write_request_v1",
            source_write_decision_id="owner_manual_edit_write_decision_v1",
            source_write_result_id="owner_manual_edit_write_result_v1",
            owner_approval_id="owner_approval_manual_edit_v1",
            operator_approval_id="no_operator_approval_v1",
            validation_report_id="validation_pending_owner_manual_edit_v1",
            created_timestamp="2026-06-01T20:41:00+02:00",
            modified_timestamp="2026-06-01T20:41:01+02:00",
            generator_type="owner_supplied",
            model_provider_used=False,
            provider_trace_id="none",
            authority_level_used="owner_review",
            sandbox_root="sandbox/owner_edit",
            write_mode="owner_approved_edit",
            tamper_evidence_status="hash_recorded",
            verification_status="verification_not_run",
            public_claim_allowed=False,
            runtime_authority=False,
            writes_state=False,
            safe_metadata={"example_name": "owner_manual_edit_provenance_example", "edit_source": "owner"},
        )
    )

    return examples
