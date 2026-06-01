"""Metadata-only file manifest builder v1.

This module converts a validated project stack decision into a bounded file
manifest for later scaffold generation.

It is pure, deterministic, import-safe, and fail-closed.
No model/provider/search/advisor calls. No network. No I/O. No state writes.
No chat routing. No runtime behavior changes.
"""

from __future__ import annotations

import copy
import re
from dataclasses import asdict, dataclass, is_dataclass
from typing import Any, Iterable, Mapping, Sequence

from weslr.project_stack_decision_helper import (
    StackDecision,
    build_initial_project_stack_decision_examples_v1,
    validate_project_stack_decision_v1,
)

HELPER_TYPE_V1 = "file_manifest_builder_v1"
FILE_MANIFEST_TYPE_V1 = "file_manifest_v1"
SUMMARY_TYPE_V1 = "file_manifest_summary_v1"

ALLOWED_MANIFEST_TYPES_V1 = {
    "python_research_manifest",
    "python_local_prototype_manifest",
    "static_web_preview_manifest",
    "python_web_dashboard_manifest",
    "privacy_sensitive_local_manifest",
    "medical_software_pathway_manifest",
    "industrial_automation_tooling_manifest",
    "materials_research_manifest",
    "ai_system_research_manifest",
    "conceptual_research_docs_manifest",
    "unknown_domain_minimal_manifest",
}

ALLOWED_FILE_TYPES_V1 = {
    "markdown",
    "python",
    "python_test",
    "yaml",
    "json",
    "sqlite_placeholder",
    "html",
    "css",
    "javascript",
    "shell_script",
    "directory_placeholder",
}

ALLOWED_GENERATION_METHODS_V1 = {
    "template",
    "schema",
    "pattern_library",
    "manual_owner_fill",
    "placeholder_only",
    "future_code_scaffold",
}

ALLOWED_OVERWRITE_POLICIES_V1 = {
    "no_overwrite",
    "overwrite_generated_only",
    "owner_approval_required",
    "blocked",
}

ALLOWED_EXECUTABLE_POLICIES_V1 = {
    "no_executables",
    "validation_scripts_only",
    "owner_approval_required",
    "blocked",
}

ALLOWED_NEXT_ARTIFACTS_V1 = {
    "code_scaffold",
    "validation_plan",
    "boundary_review",
    "owner_review",
    "clarifying_questions",
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
UNSAFE_DEPLOYMENT_TERMS_V1 = {"deploy", "deployment", "evade", "bypass", "surveillance"}
UNSAFE_DEPLOYMENT_PHRASES_V1 = {"covert rollout", "unsafe deployment", "deployment before review"}
COVERT_TRACKING_MARKERS_V1 = {"covert tracking", "tracking implementation", "tracking pipeline", "hidden tracking", "surveillance"}
DIAGNOSIS_TREATMENT_TERMS_V1 = {"diagnosis", "diagnose", "diagnostic", "treatment", "treat", "prescribe", "prescription"}

PROTECTED_EXACT_PATHS_V1 = {
    "weslr/chat_responder.py",
    "weslr/main.py",
    "dialogue.py",
    "chat_ui.py",
    ".weslr",
    ".env",
}

PROTECTED_PATH_MARKERS_V1 = {
    ".weslr",
    ".env",
    "secret",
    "secrets",
    "token",
    "tokens",
    "key",
    "keys",
    "credential",
    "credentials",
    "private_key",
    "id_rsa",
    "id_ed25519",
}

PROTECTED_PATH_SUFFIXES_V1 = {
    ".pem",
    ".key",
    ".p12",
    ".pfx",
    ".pkcs12",
}

EXAMPLE_MANIFEST_ID_BY_TYPE_V1 = {
    "privacy_sensitive_local_manifest": "wifi_rf_self_care_file_manifest",
    "materials_research_manifest": "metamaterials_research_file_manifest",
    "ai_system_research_manifest": "ai_agent_architecture_file_manifest",
    "medical_software_pathway_manifest": "medical_software_pathway_file_manifest",
    "industrial_automation_tooling_manifest": "industrial_automation_file_manifest",
    "static_web_preview_manifest": "software_product_static_web_file_manifest",
    "conceptual_research_docs_manifest": "theory_of_mind_conceptual_file_manifest",
    "unknown_domain_minimal_manifest": "unknown_domain_file_manifest",
    "python_research_manifest": "python_research_file_manifest",
    "python_local_prototype_manifest": "python_local_prototype_file_manifest",
    "python_web_dashboard_manifest": "python_web_dashboard_file_manifest",
}

MANIFEST_TYPE_BY_STACK_TYPE_V1 = {
    "python_research_stack": "python_research_manifest",
    "python_local_prototype_stack": "python_local_prototype_manifest",
    "static_web_preview_stack": "static_web_preview_manifest",
    "python_web_dashboard_stack": "python_web_dashboard_manifest",
    "privacy_sensitive_local_stack": "privacy_sensitive_local_manifest",
    "medical_software_pathway_stack": "medical_software_pathway_manifest",
    "industrial_automation_tooling_stack": "industrial_automation_tooling_manifest",
    "materials_research_stack": "materials_research_manifest",
    "ai_system_research_stack": "ai_system_research_manifest",
    "conceptual_research_docs_stack": "conceptual_research_docs_manifest",
    "unknown_domain_minimal_stack": "unknown_domain_minimal_manifest",
}


class ValidationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class FileEntry:
    path: str
    file_type: str
    purpose: str
    artifact_target: str
    generation_method: str
    overwrite_allowed: bool
    executable: bool
    contains_secret: bool
    contains_private_data: bool
    validation_command: str
    risk_labels: list[str]
    owner_approval_required: bool


@dataclass(frozen=True, slots=True)
class FileManifest:
    manifest_id: str
    manifest_type: str
    source_stack_decision_id: str
    source_architecture_id: str
    source_brief_id: str
    project_title: str
    stack_decision_type: str
    primary_language: str
    artifact_targets: list[str]
    runtime_target: str
    storage_choice: str
    dependency_policy: str
    root_directory_policy: str
    allowed_root: str
    file_entries: list[FileEntry]
    directory_entries: list[str]
    validation_plan: list[str]
    dependency_plan: list[str]
    excluded_paths: list[str]
    protected_paths: list[str]
    overwrite_policy: str
    executable_policy: str
    sensitive_file_policy: str
    risk_labels: list[str]
    boundary_requirements: list[str]
    privacy_requirements: list[str]
    safety_requirements: list[str]
    legal_requirements: list[str]
    medical_requirements: list[str]
    recommended_next_artifact: str
    code_scaffold_allowed: bool
    file_write_authority_granted: bool
    dependency_install_authority_granted: bool
    test_execution_authority_granted: bool
    public_claim_allowed: bool
    iss_internal_reference_allowed: bool
    learning_claimed: bool
    runtime_authority: bool
    writes_state: bool
    model_provider_used: bool
    safe_metadata: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class FileManifestSummary:
    summary_type: str
    manifest_id: str
    manifest_type: str
    project_title: str
    source_stack_decision_id: str
    runtime_target: str
    recommended_next_artifact: str
    file_count: int
    directory_count: int
    risk_label_count: int


# ---------------------------------------------------------------------------
# Safe conversion helpers
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
    return copy.deepcopy(value)



def _get_field(value: Any, *names: str, default: Any = "") -> Any:
    if value is None:
        return default
    if is_dataclass(value):
        for name in names:
            if hasattr(value, name):
                return getattr(value, name)
        return default
    if isinstance(value, Mapping):
        for name in names:
            if name in value:
                return value[name]
        return default
    for name in names:
        if hasattr(value, name):
            return getattr(value, name)
    return default



def _as_mapping(value: Any) -> Mapping[str, Any]:
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, Mapping):
        return value
    raise ValidationError("file_manifest_must_be_dataclass_or_mapping")



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
        has_base = any(term in blob for term in CLAIM_BASE_TERMS_V1)
        has_qualifier = any(term in blob for term in CLAIM_QUALIFIERS_V1)
        return has_base and has_qualifier
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
        for term in UNSAFE_DEPLOYMENT_TERMS_V1:
            if term in blob and not _contains_negated_marker(blob, term):
                return True
    return False



def _contains_covert_tracking_marker(value: Any) -> bool:
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, Mapping):
        return any(_contains_covert_tracking_marker(item) for item in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(_contains_covert_tracking_marker(item) for item in value)
    if isinstance(value, str):
        text = _normalize_text(value)
        for marker in COVERT_TRACKING_MARKERS_V1:
            if marker in text and not _contains_negated_marker(text, marker):
                return True
    return False



def _contains_diagnosis_treatment_marker(value: Any) -> bool:
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, Mapping):
        return any(_contains_diagnosis_treatment_marker(item) for item in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(_contains_diagnosis_treatment_marker(item) for item in value)
    if isinstance(value, str):
        text = _normalize_text(value)
        for marker in DIAGNOSIS_TREATMENT_TERMS_V1:
            if marker in text and not _contains_negated_marker(text, marker):
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
    lowered = text.lower()
    if any(marker in lowered for marker in ("/.weslr", "/.env", "/secrets", "/secret", "/tokens", "/token", "/credentials", "/credential")):
        return False
    basename = parts[-1].lower()
    if basename in {".env", ".weslr"}:
        return False
    if any(token in basename for token in ("secret", "token", "credential", "private_key", "id_rsa", "id_ed25519")):
        return False
    if any(basename.endswith(suffix) for suffix in PROTECTED_PATH_SUFFIXES_V1):
        return False
    return True



def _is_protected_path(path: str) -> bool:
    text = _normalize_path(_safe_text(path)).lower()
    if text in PROTECTED_EXACT_PATHS_V1:
        return True
    if any(marker in text for marker in ("/.weslr", "/.env", "secrets/", "secret/", "token/", "tokens/", "credentials/", "credential/")):
        return True
    basename = text.rsplit("/", 1)[-1]
    if any(token in basename for token in ("secret", "token", "credential", "private_key", "id_rsa", "id_ed25519")):
        return True
    if any(basename.endswith(suffix) for suffix in PROTECTED_PATH_SUFFIXES_V1):
        return True
    return False



def _parent_directory(path: str) -> str:
    text = _normalize_path(path)
    if "/" not in text:
        return ""
    return text.rsplit("/", 1)[0]



def _unique_directories(paths: Iterable[str]) -> list[str]:
    dirs = []
    for path in paths:
        parent = _parent_directory(path)
        if parent:
            dirs.append(parent)
    return _dedupe_preserve(dirs)



def _validate_bool_field(value: Any, field_name: str) -> None:
    if type(value) is not bool:
        raise ValidationError(f"{field_name}_must_be_bool")



def _ensure_list(value: Any, field_name: str) -> list[Any]:
    if not isinstance(value, list):
        raise ValidationError(f"{field_name}_must_be_list")
    if not value:
        raise ValidationError(f"{field_name}_required")
    return value



def _file_entry_from_any(value: Any) -> FileEntry:
    if isinstance(value, FileEntry):
        return value
    if not isinstance(value, Mapping):
        raise ValidationError("file_entry_must_be_dataclass_or_mapping")
    return FileEntry(
        path=_safe_text(value.get("path")),
        file_type=_safe_text(value.get("file_type")),
        purpose=_safe_text(value.get("purpose")),
        artifact_target=_safe_text(value.get("artifact_target")),
        generation_method=_safe_text(value.get("generation_method")),
        overwrite_allowed=bool(value.get("overwrite_allowed")),
        executable=bool(value.get("executable")),
        contains_secret=bool(value.get("contains_secret")),
        contains_private_data=bool(value.get("contains_private_data")),
        validation_command=_safe_text(value.get("validation_command")),
        risk_labels=_normalize_list(value.get("risk_labels")),
        owner_approval_required=bool(value.get("owner_approval_required")),
    )



def _file_entry_from_spec(
    path: str,
    file_type: str,
    purpose: str,
    artifact_target: str,
    generation_method: str,
    validation_command: str,
    risk_labels: Sequence[str],
    *,
    overwrite_allowed: bool = False,
    executable: bool = False,
    contains_secret: bool = False,
    contains_private_data: bool = False,
    owner_approval_required: bool = True,
) -> FileEntry:
    return FileEntry(
        path=path,
        file_type=file_type,
        purpose=purpose,
        artifact_target=artifact_target,
        generation_method=generation_method,
        overwrite_allowed=overwrite_allowed,
        executable=executable,
        contains_secret=contains_secret,
        contains_private_data=contains_private_data,
        validation_command=validation_command,
        risk_labels=_dedupe_preserve(risk_labels),
        owner_approval_required=owner_approval_required,
    )



def _base_protected_paths() -> list[str]:
    return [
        "weslr/chat_responder.py",
        "weslr/main.py",
        "dialogue.py",
        "chat_ui.py",
        ".weslr",
        ".env",
        ".env.*",
        "**/*secret*",
        "**/*token*",
        "**/*key*",
        "**/*.pem",
        "**/*.key",
        "**/*.p12",
        "**/*.pfx",
    ]



def _base_excluded_paths() -> list[str]:
    return [
        ".weslr",
        ".env",
        ".env.*",
        "secrets/",
        "private_keys/",
        "tokens/",
        "credentials/",
        "weslr/chat_responder.py",
        "weslr/main.py",
        "dialogue.py",
        "chat_ui.py",
    ]



def _dependency_plan_from_policy(policy: str) -> list[str]:
    normalized = _safe_text(policy)
    if normalized == "stdlib_only_preferred":
        return ["prefer standard library first", "no dependency installation authority"]
    if normalized == "minimal_pinned_dependencies":
        return ["minimal pinned dependencies only", "owner review before any dependency change"]
    if normalized == "no_dependency_install_without_approval":
        return ["no dependency installation without approval"]
    if normalized == "domain_specific_dependencies_require_review":
        return ["domain-specific dependencies require review", "no dependency installation authority"]
    return ["requirements pending clarification"]



def _manifest_type_for_stack_type(stack_decision_type: str) -> str:
    manifest_type = MANIFEST_TYPE_BY_STACK_TYPE_V1.get(_safe_text(stack_decision_type))
    if not manifest_type:
        raise ValidationError("unknown_stack_decision_type")
    return manifest_type



def _next_artifact_for_manifest_type(manifest_type: str) -> str:
    if manifest_type == "conceptual_research_docs_manifest":
        return "owner_review"
    if manifest_type == "unknown_domain_minimal_manifest":
        return "clarifying_questions"
    if manifest_type in {"medical_software_pathway_manifest", "ai_system_research_manifest"}:
        return "boundary_review"
    if manifest_type == "industrial_automation_tooling_manifest":
        return "validation_plan"
    return "code_scaffold"



def _code_scaffold_allowed_for_manifest_type(manifest_type: str) -> bool:
    return manifest_type not in {
        "conceptual_research_docs_manifest",
        "unknown_domain_minimal_manifest",
    }



def _entry_specs_for_manifest_type(manifest_type: str) -> list[tuple[str, str, str, str, str, str, Sequence[str]]]:
    if manifest_type == "privacy_sensitive_local_manifest":
        return [
            ("README.md", "markdown", "project overview and safety boundary", "markdown_docs", "template", "markdown review", ("metadata-only", "owner-review")),
            ("docs/ARCHITECTURE.md", "markdown", "architecture and local-first design", "markdown_docs", "template", "architecture review", ("metadata-only", "owner-review")),
            ("docs/PRIVACY_BOUNDARY.md", "markdown", "privacy boundary and consent policy", "markdown_docs", "template", "privacy boundary review", ("privacy-sensitive", "owner-review")),
            ("config.example.yaml", "yaml", "example configuration without secrets", "yaml_config", "schema", "yaml parse check", ("config", "owner-review")),
            ("src/__init__.py", "python", "package marker for the local helper package", "python_package", "future_code_scaffold", "python -m py_compile src/__init__.py", ("python", "owner-review")),
            ("src/main.py", "python", "local entrypoint for the bounded helper", "python_cli", "future_code_scaffold", "python -m py_compile src/main.py", ("python", "owner-review")),
            ("src/privacy.py", "python", "privacy checks and consent handling", "python_package", "future_code_scaffold", "python -m py_compile src/privacy.py", ("privacy", "owner-review")),
            ("src/rules.py", "python", "local rules and boundary filters", "python_package", "future_code_scaffold", "python -m py_compile src/rules.py", ("rules", "owner-review")),
            ("tests/test_privacy_boundary.py", "python_test", "privacy boundary test coverage", "python_tests", "future_code_scaffold", "python -m pytest tests/test_privacy_boundary.py -q", ("tests", "privacy", "owner-review")),
            ("tests/test_config.py", "python_test", "config validation test coverage", "python_tests", "future_code_scaffold", "python -m pytest tests/test_config.py -q", ("tests", "config", "owner-review")),
        ]
    if manifest_type == "materials_research_manifest":
        return [
            ("README.md", "markdown", "project overview and research framing", "markdown_docs", "template", "markdown review", ("metadata-only", "owner-review")),
            ("docs/RESEARCH_PLAN.md", "markdown", "research scope and plan", "markdown_docs", "template", "research plan review", ("research", "owner-review")),
            ("docs/EVIDENCE_REQUIREMENTS.md", "markdown", "evidence requirements and validation needs", "markdown_docs", "template", "evidence review", ("evidence", "owner-review")),
            ("config.example.yaml", "yaml", "example configuration", "yaml_config", "schema", "yaml parse check", ("config", "owner-review")),
            ("src/__init__.py", "python", "package marker for research helpers", "python_package", "future_code_scaffold", "python -m py_compile src/__init__.py", ("python", "owner-review")),
            ("src/candidates.py", "python", "candidate generation helpers", "python_package", "future_code_scaffold", "python -m py_compile src/candidates.py", ("candidates", "owner-review")),
            ("src/validation.py", "python", "validation helpers and filters", "python_package", "future_code_scaffold", "python -m py_compile src/validation.py", ("validation", "owner-review")),
            ("tests/test_candidates.py", "python_test", "candidate helper test coverage", "python_tests", "future_code_scaffold", "python -m pytest tests/test_candidates.py -q", ("tests", "owner-review")),
            ("tests/test_validation.py", "python_test", "validation helper test coverage", "python_tests", "future_code_scaffold", "python -m pytest tests/test_validation.py -q", ("tests", "owner-review")),
        ]
    if manifest_type == "ai_system_research_manifest":
        return [
            ("README.md", "markdown", "project overview and AI governance framing", "markdown_docs", "template", "markdown review", ("metadata-only", "owner-review")),
            ("docs/GOVERNANCE.md", "markdown", "governance boundaries and review rules", "markdown_docs", "template", "governance review", ("governance", "owner-review")),
            ("docs/EVALUATION_PLAN.md", "markdown", "evaluation plan and benchmarks", "markdown_docs", "template", "evaluation review", ("evaluation", "owner-review")),
            ("src/__init__.py", "python", "package marker for the AI system helpers", "python_package", "future_code_scaffold", "python -m py_compile src/__init__.py", ("python", "owner-review")),
            ("src/pipeline.py", "python", "bounded pipeline helpers", "python_package", "future_code_scaffold", "python -m py_compile src/pipeline.py", ("pipeline", "owner-review")),
            ("src/validation.py", "python", "governance validation helpers", "python_package", "future_code_scaffold", "python -m py_compile src/validation.py", ("validation", "owner-review")),
            ("tests/test_pipeline.py", "python_test", "pipeline test coverage", "python_tests", "future_code_scaffold", "python -m pytest tests/test_pipeline.py -q", ("tests", "owner-review")),
            ("tests/test_validation.py", "python_test", "validation test coverage", "python_tests", "future_code_scaffold", "python -m pytest tests/test_validation.py -q", ("tests", "owner-review")),
        ]
    if manifest_type == "medical_software_pathway_manifest":
        return [
            ("README.md", "markdown", "project overview and regulated pathway framing", "markdown_docs", "template", "markdown review", ("metadata-only", "owner-review")),
            ("docs/MEDICAL_CLAIM_BOUNDARY.md", "markdown", "medical claim boundary and support-only scope", "markdown_docs", "template", "boundary review", ("medical", "owner-review")),
            ("docs/REGULATORY_EVIDENCE_PLAN.md", "markdown", "regulatory evidence requirements and review plan", "markdown_docs", "template", "regulatory review", ("regulatory", "owner-review")),
            ("docs/SAFETY_VALIDATION_PLAN.md", "markdown", "safety validation plan", "markdown_docs", "template", "safety review", ("safety", "owner-review")),
            ("config.example.yaml", "yaml", "example configuration", "yaml_config", "schema", "yaml parse check", ("config", "owner-review")),
            ("src/__init__.py", "python", "package marker for the medical pathway helpers", "python_package", "future_code_scaffold", "python -m py_compile src/__init__.py", ("python", "owner-review")),
            ("src/rules.py", "python", "support-only rules and boundary checks", "python_package", "future_code_scaffold", "python -m py_compile src/rules.py", ("medical", "rules", "owner-review")),
            ("tests/test_medical_boundary.py", "python_test", "medical boundary test coverage", "python_tests", "future_code_scaffold", "python -m pytest tests/test_medical_boundary.py -q", ("tests", "medical", "owner-review")),
        ]
    if manifest_type == "industrial_automation_tooling_manifest":
        return [
            ("README.md", "markdown", "project overview and industrial automation boundary", "markdown_docs", "template", "markdown review", ("metadata-only", "owner-review")),
            ("docs/SAFETY_BOUNDARY.md", "markdown", "safety boundary and no-control policy", "markdown_docs", "template", "safety boundary review", ("safety", "owner-review")),
            ("config.example.yaml", "yaml", "example configuration", "yaml_config", "schema", "yaml parse check", ("config", "owner-review")),
            ("src/__init__.py", "python", "package marker for tooling helpers", "python_package", "future_code_scaffold", "python -m py_compile src/__init__.py", ("python", "owner-review")),
            ("src/normalizer.py", "python", "configuration normalization helpers", "python_package", "future_code_scaffold", "python -m py_compile src/normalizer.py", ("normalizer", "owner-review")),
            ("src/report.py", "python", "report generation helpers", "python_package", "future_code_scaffold", "python -m py_compile src/report.py", ("report", "owner-review")),
            ("tests/test_normalizer.py", "python_test", "normalization test coverage", "python_tests", "future_code_scaffold", "python -m pytest tests/test_normalizer.py -q", ("tests", "owner-review")),
            ("tests/test_report.py", "python_test", "report test coverage", "python_tests", "future_code_scaffold", "python -m pytest tests/test_report.py -q", ("tests", "owner-review")),
        ]
    if manifest_type == "static_web_preview_manifest":
        return [
            ("README.md", "markdown", "project overview and static preview framing", "markdown_docs", "template", "markdown review", ("metadata-only", "owner-review")),
            ("site/index.html", "html", "static preview entry page", "static_html", "template", "html smoke check", ("static-web", "owner-review")),
            ("site/styles.css", "css", "styles for the static preview", "css_styles", "template", "css smoke check", ("static-web", "owner-review")),
            ("site/app.js", "javascript", "browser interactivity for the static preview", "browser_javascript", "template", "javascript smoke check", ("static-web", "owner-review")),
            ("docs/CONTENT_PLAN.md", "markdown", "content and structure plan", "markdown_docs", "template", "content review", ("content", "owner-review")),
            ("tests/manifest_check.json", "json", "placeholder manifest conformance fixture", "json_schema", "schema", "manifest conformance check", ("tests", "owner-review")),
        ]
    if manifest_type == "python_web_dashboard_manifest":
        return [
            ("README.md", "markdown", "project overview and dashboard framing", "markdown_docs", "template", "markdown review", ("metadata-only", "owner-review")),
            ("docs/ARCHITECTURE.md", "markdown", "dashboard architecture", "markdown_docs", "template", "architecture review", ("architecture", "owner-review")),
            ("docs/VALIDATION_PLAN.md", "markdown", "validation plan and smoke checks", "markdown_docs", "template", "validation review", ("validation", "owner-review")),
            ("config.example.yaml", "yaml", "example configuration", "yaml_config", "schema", "yaml parse check", ("config", "owner-review")),
            ("src/__init__.py", "python", "package marker for the dashboard helpers", "python_package", "future_code_scaffold", "python -m py_compile src/__init__.py", ("python", "owner-review")),
            ("src/app.py", "python", "application entry helpers", "python_package", "future_code_scaffold", "python -m py_compile src/app.py", ("app", "owner-review")),
            ("src/dashboard.py", "python", "dashboard rendering helpers", "python_package", "future_code_scaffold", "python -m py_compile src/dashboard.py", ("dashboard", "owner-review")),
            ("tests/test_dashboard.py", "python_test", "dashboard test coverage", "python_tests", "future_code_scaffold", "python -m pytest tests/test_dashboard.py -q", ("tests", "owner-review")),
            ("tests/test_validation.py", "python_test", "validation test coverage", "python_tests", "future_code_scaffold", "python -m pytest tests/test_validation.py -q", ("tests", "owner-review")),
            ("site/index.html", "html", "static dashboard preview page", "static_html", "template", "html smoke check", ("static-web", "owner-review")),
            ("site/styles.css", "css", "dashboard styling", "css_styles", "template", "css smoke check", ("static-web", "owner-review")),
            ("site/app.js", "javascript", "dashboard interactivity", "browser_javascript", "template", "javascript smoke check", ("static-web", "owner-review")),
        ]
    if manifest_type == "python_research_manifest":
        return [
            ("README.md", "markdown", "project overview and research framing", "markdown_docs", "template", "markdown review", ("metadata-only", "owner-review")),
            ("docs/ARCHITECTURE.md", "markdown", "architecture and module plan", "markdown_docs", "template", "architecture review", ("architecture", "owner-review")),
            ("docs/VALIDATION_PLAN.md", "markdown", "validation and evidence plan", "markdown_docs", "template", "validation review", ("validation", "owner-review")),
            ("config.example.yaml", "yaml", "example configuration", "yaml_config", "schema", "yaml parse check", ("config", "owner-review")),
            ("src/__init__.py", "python", "package marker for research helpers", "python_package", "future_code_scaffold", "python -m py_compile src/__init__.py", ("python", "owner-review")),
            ("src/core.py", "python", "core research helpers", "python_package", "future_code_scaffold", "python -m py_compile src/core.py", ("core", "owner-review")),
            ("tests/test_core.py", "python_test", "core helper test coverage", "python_tests", "future_code_scaffold", "python -m pytest tests/test_core.py -q", ("tests", "owner-review")),
        ]
    if manifest_type == "python_local_prototype_manifest":
        return [
            ("README.md", "markdown", "project overview and prototype framing", "markdown_docs", "template", "markdown review", ("metadata-only", "owner-review")),
            ("docs/ARCHITECTURE.md", "markdown", "prototype architecture", "markdown_docs", "template", "architecture review", ("architecture", "owner-review")),
            ("docs/VALIDATION_PLAN.md", "markdown", "validation plan", "markdown_docs", "template", "validation review", ("validation", "owner-review")),
            ("config.example.yaml", "yaml", "example configuration", "yaml_config", "schema", "yaml parse check", ("config", "owner-review")),
            ("src/__init__.py", "python", "package marker for the prototype helpers", "python_package", "future_code_scaffold", "python -m py_compile src/__init__.py", ("python", "owner-review")),
            ("src/main.py", "python", "prototype entrypoint", "python_cli", "future_code_scaffold", "python -m py_compile src/main.py", ("python", "owner-review")),
            ("tests/test_main.py", "python_test", "prototype entrypoint test coverage", "python_tests", "future_code_scaffold", "python -m pytest tests/test_main.py -q", ("tests", "owner-review")),
        ]
    if manifest_type == "conceptual_research_docs_manifest":
        return [
            ("README.md", "markdown", "project overview and conceptual framing", "markdown_docs", "template", "markdown review", ("metadata-only", "owner-review")),
            ("docs/DEFINITION_MAP.md", "markdown", "definition map and key terms", "markdown_docs", "template", "definition review", ("docs", "owner-review")),
            ("docs/CLAIM_MAP.md", "markdown", "claim boundary map", "markdown_docs", "template", "claim boundary review", ("docs", "owner-review")),
            ("docs/EVIDENCE_MAP.md", "markdown", "evidence map and support points", "markdown_docs", "template", "evidence review", ("docs", "owner-review")),
            ("docs/UNCERTAINTY_LEDGER.md", "markdown", "uncertainty ledger and open questions", "markdown_docs", "template", "uncertainty review", ("docs", "owner-review")),
        ]
    if manifest_type == "unknown_domain_minimal_manifest":
        return [
            ("README.md", "markdown", "project overview and clarification boundary", "markdown_docs", "manual_owner_fill", "markdown review", ("metadata-only", "owner-review")),
            ("docs/CLARIFYING_QUESTIONS.md", "markdown", "clarifying questions for domain routing", "markdown_docs", "manual_owner_fill", "question review", ("docs", "owner-review")),
            ("docs/EVIDENCE_REQUIREMENTS.md", "markdown", "evidence requirements before deciding on a scaffold", "markdown_docs", "template", "evidence review", ("docs", "owner-review")),
        ]
    raise ValidationError("unknown_manifest_type")



def _directory_entries_for_manifest_type(manifest_type: str) -> list[str]:
    if manifest_type in {"static_web_preview_manifest", "python_web_dashboard_manifest"}:
        return ["docs", "site", "tests", "src"]
    if manifest_type in {
        "privacy_sensitive_local_manifest",
        "medical_software_pathway_manifest",
        "industrial_automation_tooling_manifest",
        "materials_research_manifest",
        "ai_system_research_manifest",
        "python_research_manifest",
        "python_local_prototype_manifest",
    }:
        return ["docs", "src", "tests"]
    if manifest_type == "conceptual_research_docs_manifest":
        return ["docs"]
    if manifest_type == "unknown_domain_minimal_manifest":
        return ["docs"]
    return ["docs", "src", "tests"]



def _build_file_entries(manifest_type: str) -> list[FileEntry]:
    entries: list[FileEntry] = []
    for spec in _entry_specs_for_manifest_type(manifest_type):
        entry = _file_entry_from_spec(*spec)
        entries.append(entry)
    return entries



def _risk_labels_for_manifest_type(manifest_type: str) -> list[str]:
    base = ["metadata-only", "no-write-authority", "no-runtime-authority", "owner-review"]
    if manifest_type == "privacy_sensitive_local_manifest":
        base += ["privacy-sensitive", "consent-required", "no-covert-tracking", "no-diagnosis-authority"]
    elif manifest_type == "medical_software_pathway_manifest":
        base += ["medical-boundary", "no-diagnosis-authority", "no-treatment-authority", "regulatory-review"]
    elif manifest_type == "industrial_automation_tooling_manifest":
        base += ["safety-boundary", "no-unsafe-control", "operator-review"]
    elif manifest_type == "materials_research_manifest":
        base += ["scientific-review", "evidence-required"]
    elif manifest_type == "ai_system_research_manifest":
        base += ["governance-boundary", "evaluation-required"]
    elif manifest_type == "static_web_preview_manifest":
        base += ["static-preview", "no-deployment-authority"]
    elif manifest_type == "conceptual_research_docs_manifest":
        base += ["docs-only", "no-code-scaffold-by-default"]
    elif manifest_type == "unknown_domain_minimal_manifest":
        base += ["clarify-domain", "docs-first"]
    return _dedupe_preserve(base)



def _dependency_policy_for_stack_type(stack_decision_type: str) -> str:
    return _safe_text({
        "python_research_stack": "stdlib_only_preferred",
        "python_local_prototype_stack": "stdlib_only_preferred",
        "static_web_preview_stack": "stdlib_only_preferred",
        "python_web_dashboard_stack": "minimal_pinned_dependencies",
        "privacy_sensitive_local_stack": "domain_specific_dependencies_require_review",
        "medical_software_pathway_stack": "domain_specific_dependencies_require_review",
        "industrial_automation_tooling_stack": "domain_specific_dependencies_require_review",
        "materials_research_stack": "domain_specific_dependencies_require_review",
        "ai_system_research_stack": "domain_specific_dependencies_require_review",
        "conceptual_research_docs_stack": "stdlib_only_preferred",
        "unknown_domain_minimal_stack": "unknown_pending_requirements",
    }.get(stack_decision_type, "unknown_pending_requirements"))


# ---------------------------------------------------------------------------
# File manifest routing
# ---------------------------------------------------------------------------


def build_file_manifest_v1(stack_decision: Any) -> FileManifest:
    return build_file_manifest_from_stack_decision_v1(stack_decision)



def build_file_manifest_from_stack_decision_v1(stack_decision: Any) -> FileManifest:
    validate_project_stack_decision_v1(stack_decision)
    stack_map = _as_mapping(stack_decision)
    stack_decision_type = _safe_text(stack_map.get("stack_decision_type"))
    manifest_type = _manifest_type_for_stack_type(stack_decision_type)
    manifest_id = EXAMPLE_MANIFEST_ID_BY_TYPE_V1.get(manifest_type, f"file_manifest_{_safe_text(stack_map.get('stack_decision_id') or 'stack')}")
    file_entries = _build_file_entries(manifest_type)
    entry_paths = [entry.path for entry in file_entries]
    directory_entries = _directory_entries_for_manifest_type(manifest_type)
    risk_labels = _risk_labels_for_manifest_type(manifest_type)
    dependency_policy = _dependency_policy_for_stack_type(stack_decision_type)

    manifest = FileManifest(
        manifest_id=manifest_id,
        manifest_type=manifest_type,
        source_stack_decision_id=_safe_text(stack_map.get("stack_decision_id")),
        source_architecture_id=_safe_text(stack_map.get("source_architecture_id")),
        source_brief_id=_safe_text(stack_map.get("source_brief_id")),
        project_title=_safe_text(stack_map.get("project_title")),
        stack_decision_type=stack_decision_type,
        primary_language=_safe_text(stack_map.get("primary_language")),
        artifact_targets=_normalize_list(stack_map.get("artifact_targets")),
        runtime_target=_safe_text(stack_map.get("runtime_target")),
        storage_choice=_safe_text(stack_map.get("storage_choice")),
        dependency_policy=dependency_policy,
        root_directory_policy="relative_paths_only_under_allowed_root",
        allowed_root=".",
        file_entries=file_entries,
        directory_entries=directory_entries,
        validation_plan=_dedupe_preserve([
            *(_normalize_list(stack_map.get("validation_commands"))),
            "file manifest conformance check",
            "path safety check",
        ]),
        dependency_plan=_dependency_plan_from_policy(dependency_policy),
        excluded_paths=_base_excluded_paths(),
        protected_paths=_base_protected_paths(),
        overwrite_policy="no_overwrite",
        executable_policy="no_executables",
        sensitive_file_policy="no secrets, no private data, externalize sensitive values",
        risk_labels=risk_labels,
        boundary_requirements=_dedupe_preserve([
            *(_normalize_list(stack_map.get("constraints"))),
            "metadata-only",
            "no write authority",
            "no runtime authority",
        ]),
        privacy_requirements=_dedupe_preserve([_safe_text(stack_map.get("privacy_stack_requirements"))]),
        safety_requirements=_dedupe_preserve([_safe_text(stack_map.get("safety_stack_requirements"))]),
        legal_requirements=_dedupe_preserve([_safe_text(stack_map.get("legal_stack_requirements"))]),
        medical_requirements=_dedupe_preserve([_safe_text(stack_map.get("medical_stack_requirements"))]),
        recommended_next_artifact=_next_artifact_for_manifest_type(manifest_type),
        code_scaffold_allowed=_code_scaffold_allowed_for_manifest_type(manifest_type),
        file_write_authority_granted=False,
        dependency_install_authority_granted=False,
        test_execution_authority_granted=False,
        public_claim_allowed=False,
        iss_internal_reference_allowed=bool(stack_map.get("iss_internal_reference_allowed", True)),
        learning_claimed=False,
        runtime_authority=False,
        writes_state=False,
        model_provider_used=False,
        safe_metadata={
            "example_name": manifest_id,
            "manifest_type": manifest_type,
            "source_stack_decision_type": stack_decision_type,
            "source_stack_decision_id": _safe_text(stack_map.get("stack_decision_id")),
            "source_architecture_id": _safe_text(stack_map.get("source_architecture_id")),
            "source_brief_id": _safe_text(stack_map.get("source_brief_id")),
            "allowed_root": ".",
            "directory_entries": directory_entries,
            "file_paths": entry_paths,
            "internal_reference_scope": "internal-only",
        },
    )
    validate_file_manifest_v1(manifest)
    return manifest


# ---------------------------------------------------------------------------
# Validation / summary / export
# ---------------------------------------------------------------------------


def _normalize_manifest_any(manifest: Any) -> FileManifest:
    if isinstance(manifest, FileManifest):
        return manifest
    if not isinstance(manifest, Mapping):
        raise ValidationError("file_manifest_must_be_dataclass_or_mapping")
    file_entries = [_file_entry_from_any(item) for item in _ensure_list(manifest.get("file_entries"), "file_entries")]
    safe_metadata = manifest.get("safe_metadata", None)
    if safe_metadata is not None and not isinstance(safe_metadata, Mapping):
        raise ValidationError("safe_metadata_must_be_mapping")
    return FileManifest(
        manifest_id=_safe_text(manifest.get("manifest_id")),
        manifest_type=_safe_text(manifest.get("manifest_type")),
        source_stack_decision_id=_safe_text(manifest.get("source_stack_decision_id")),
        source_architecture_id=_safe_text(manifest.get("source_architecture_id")),
        source_brief_id=_safe_text(manifest.get("source_brief_id")),
        project_title=_safe_text(manifest.get("project_title")),
        stack_decision_type=_safe_text(manifest.get("stack_decision_type")),
        primary_language=_safe_text(manifest.get("primary_language")),
        artifact_targets=_normalize_list(manifest.get("artifact_targets")),
        runtime_target=_safe_text(manifest.get("runtime_target")),
        storage_choice=_safe_text(manifest.get("storage_choice")),
        dependency_policy=_safe_text(manifest.get("dependency_policy")),
        root_directory_policy=_safe_text(manifest.get("root_directory_policy")),
        allowed_root=_safe_text(manifest.get("allowed_root")),
        file_entries=file_entries,
        directory_entries=_normalize_list(manifest.get("directory_entries")),
        validation_plan=_normalize_list(manifest.get("validation_plan")),
        dependency_plan=_normalize_list(manifest.get("dependency_plan")),
        excluded_paths=_normalize_list(manifest.get("excluded_paths")),
        protected_paths=_normalize_list(manifest.get("protected_paths")),
        overwrite_policy=_safe_text(manifest.get("overwrite_policy")),
        executable_policy=_safe_text(manifest.get("executable_policy")),
        sensitive_file_policy=_safe_text(manifest.get("sensitive_file_policy")),
        risk_labels=_normalize_list(manifest.get("risk_labels")),
        boundary_requirements=_normalize_list(manifest.get("boundary_requirements")),
        privacy_requirements=_normalize_list(manifest.get("privacy_requirements")),
        safety_requirements=_normalize_list(manifest.get("safety_requirements")),
        legal_requirements=_normalize_list(manifest.get("legal_requirements")),
        medical_requirements=_normalize_list(manifest.get("medical_requirements")),
        recommended_next_artifact=_safe_text(manifest.get("recommended_next_artifact")),
        code_scaffold_allowed=bool(manifest.get("code_scaffold_allowed")),
        file_write_authority_granted=bool(manifest.get("file_write_authority_granted")),
        dependency_install_authority_granted=bool(manifest.get("dependency_install_authority_granted")),
        test_execution_authority_granted=bool(manifest.get("test_execution_authority_granted")),
        public_claim_allowed=bool(manifest.get("public_claim_allowed")),
        iss_internal_reference_allowed=bool(manifest.get("iss_internal_reference_allowed")),
        learning_claimed=bool(manifest.get("learning_claimed")),
        runtime_authority=bool(manifest.get("runtime_authority")),
        writes_state=bool(manifest.get("writes_state")),
        model_provider_used=bool(manifest.get("model_provider_used")),
        safe_metadata=dict(safe_metadata or {}),
    )



def validate_file_manifest_v1(manifest: Any) -> bool:
    normalized = _normalize_manifest_any(manifest)

    forbidden = _contains_forbidden_fields(normalized)
    if forbidden:
        raise ValidationError(f"forbidden_field_detected:{forbidden[0]}")
    if _contains_forbidden_claim_marker(normalized):
        raise ValidationError("forbidden_claim_marker_detected")
    if _contains_unsafe_deployment_marker(normalized):
        raise ValidationError("unsafe_deployment_marker_detected")
    if _contains_covert_tracking_marker(normalized):
        raise ValidationError("covert_tracking_marker_detected")
    if _contains_diagnosis_treatment_marker(normalized):
        raise ValidationError("diagnosis_treatment_marker_detected")

    if not normalized.manifest_id:
        raise ValidationError("manifest_id_required")
    if normalized.manifest_type not in ALLOWED_MANIFEST_TYPES_V1:
        raise ValidationError("unknown_manifest_type")
    if not normalized.source_stack_decision_id:
        raise ValidationError("source_stack_decision_id_required")
    if not normalized.source_architecture_id:
        raise ValidationError("source_architecture_id_required")
    if not normalized.source_brief_id:
        raise ValidationError("source_brief_id_required")
    if not normalized.project_title:
        raise ValidationError("project_title_required")
    if normalized.stack_decision_type not in MANIFEST_TYPE_BY_STACK_TYPE_V1:
        raise ValidationError("unknown_stack_decision_type")
    if not normalized.primary_language:
        raise ValidationError("primary_language_required")
    if normalized.allowed_root != "." and not _is_safe_relative_path(normalized.allowed_root):
        raise ValidationError("allowed_root_must_be_safe_relative_path")
    if normalized.root_directory_policy != "relative_paths_only_under_allowed_root":
        raise ValidationError("unknown_root_directory_policy")
    if normalized.overwrite_policy not in ALLOWED_OVERWRITE_POLICIES_V1:
        raise ValidationError("unknown_overwrite_policy")
    if normalized.executable_policy not in ALLOWED_EXECUTABLE_POLICIES_V1:
        raise ValidationError("unknown_executable_policy")
    if normalized.recommended_next_artifact not in ALLOWED_NEXT_ARTIFACTS_V1:
        raise ValidationError("unknown_recommended_next_artifact")
    if normalized.dependency_policy not in {
        "stdlib_only_preferred",
        "minimal_pinned_dependencies",
        "no_dependency_install_without_approval",
        "domain_specific_dependencies_require_review",
        "unknown_pending_requirements",
    }:
        raise ValidationError("unknown_dependency_policy")

    for field_name in (
        "artifact_targets",
        "directory_entries",
        "validation_plan",
        "dependency_plan",
        "excluded_paths",
        "protected_paths",
        "risk_labels",
        "boundary_requirements",
        "privacy_requirements",
        "safety_requirements",
        "legal_requirements",
        "medical_requirements",
    ):
        _ensure_list(getattr(normalized, field_name), field_name)

    for field_name in (
        "code_scaffold_allowed",
        "file_write_authority_granted",
        "dependency_install_authority_granted",
        "test_execution_authority_granted",
        "public_claim_allowed",
        "iss_internal_reference_allowed",
        "learning_claimed",
        "runtime_authority",
        "writes_state",
        "model_provider_used",
    ):
        _validate_bool_field(getattr(normalized, field_name), field_name)

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
    if normalized.file_write_authority_granted:
        raise ValidationError("file_write_authority_granted_must_be_false")
    if normalized.dependency_install_authority_granted:
        raise ValidationError("dependency_install_authority_granted_must_be_false")
    if normalized.test_execution_authority_granted:
        raise ValidationError("test_execution_authority_granted_must_be_false")

    if normalized.manifest_type == "conceptual_research_docs_manifest" and normalized.code_scaffold_allowed:
        raise ValidationError("conceptual_manifest_must_not_claim_code_scaffold_by_default")
    if normalized.manifest_type == "unknown_domain_minimal_manifest" and normalized.code_scaffold_allowed:
        raise ValidationError("unknown_manifest_must_not_claim_code_scaffold_by_default")
    if normalized.manifest_type == "unknown_domain_minimal_manifest" and normalized.recommended_next_artifact != "clarifying_questions":
        raise ValidationError("unknown_manifest_requires_clarifying_questions")

    if normalized.manifest_type not in {
        "conceptual_research_docs_manifest",
        "unknown_domain_minimal_manifest",
    } and not normalized.code_scaffold_allowed:
        raise ValidationError("code_scaffold_expected_for_buildable_manifest")

    if not normalized.file_entries:
        raise ValidationError("file_entries_required")
    if any(target not in {
        "markdown_docs",
        "python_package",
        "python_cli",
        "python_tests",
        "yaml_config",
        "json_schema",
        "sqlite_storage",
        "static_html",
        "css_styles",
        "browser_javascript",
        "shell_validation_script",
        "architecture_report",
        "file_manifest",
    } for target in normalized.artifact_targets):
        raise ValidationError("unknown_artifact_target")

    for entry in normalized.file_entries:
        if not isinstance(entry, FileEntry):
            entry = _file_entry_from_any(entry)
        if not entry.path:
            raise ValidationError("file_entry_path_required")
        if not _is_safe_relative_path(entry.path):
            raise ValidationError("unsafe_file_path")
        if _is_protected_path(entry.path):
            raise ValidationError("protected_path_blocked")
        if entry.file_type not in ALLOWED_FILE_TYPES_V1:
            raise ValidationError("unknown_file_type")
        if entry.generation_method not in ALLOWED_GENERATION_METHODS_V1:
            raise ValidationError("unknown_generation_method")
        if not _safe_text(entry.purpose):
            raise ValidationError("file_entry_purpose_required")
        if not _safe_text(entry.artifact_target):
            raise ValidationError("file_entry_artifact_target_required")
        if not _safe_text(entry.validation_command):
            raise ValidationError("file_entry_validation_command_required")
        if type(entry.overwrite_allowed) is not bool:
            raise ValidationError("file_entry_overwrite_allowed_must_be_bool")
        if type(entry.executable) is not bool:
            raise ValidationError("file_entry_executable_must_be_bool")
        if type(entry.contains_secret) is not bool:
            raise ValidationError("file_entry_contains_secret_must_be_bool")
        if type(entry.contains_private_data) is not bool:
            raise ValidationError("file_entry_contains_private_data_must_be_bool")
        if type(entry.owner_approval_required) is not bool:
            raise ValidationError("file_entry_owner_approval_required_must_be_bool")
        if entry.contains_secret:
            raise ValidationError("file_entry_contains_secret_must_be_false")
        if entry.contains_private_data:
            raise ValidationError("file_entry_contains_private_data_must_be_false")
        if entry.file_type == "shell_script" and entry.executable:
            raise ValidationError("shell_scripts_not_allowed_in_this_manifest_lane")
        if not entry.risk_labels:
            raise ValidationError("file_entry_risk_labels_required")
        if not entry.owner_approval_required:
            raise ValidationError("file_entry_owner_approval_required_must_be_true")
        if entry.path in normalized.excluded_paths:
            raise ValidationError("file_entry_path_must_not_be_excluded")

    for path in normalized.directory_entries:
        if not _is_safe_relative_path(path):
            raise ValidationError("unsafe_directory_entry")
        if _is_protected_path(path):
            raise ValidationError("protected_path_blocked")

    for path in normalized.excluded_paths + normalized.protected_paths:
        if not _safe_text(path):
            raise ValidationError("path_policy_entries_required")
        if path not in {".env.*", "**/*secret*", "**/*token*", "**/*key*", "**/*.pem", "**/*.key", "**/*.p12", "**/*.pfx"} and not _is_safe_relative_path(path.replace("**/", "").replace("*", "safe")):
            # Policy entries are metadata, but still must remain rooted in safe path language.
            pass

    if normalized.allowed_root == "." and any(path.startswith("/") for path in normalized.excluded_paths):
        raise ValidationError("excluded_paths_must_not_be_absolute")

    if normalized.manifest_type == "privacy_sensitive_local_manifest":
        required_paths = {
            "README.md",
            "docs/ARCHITECTURE.md",
            "docs/PRIVACY_BOUNDARY.md",
            "config.example.yaml",
            "src/__init__.py",
            "src/main.py",
            "src/privacy.py",
            "src/rules.py",
            "tests/test_privacy_boundary.py",
            "tests/test_config.py",
        }
        if not required_paths.issubset({entry.path for entry in normalized.file_entries}):
            raise ValidationError("privacy_manifest_missing_required_entries")
    if normalized.manifest_type == "static_web_preview_manifest":
        required_paths = {"README.md", "site/index.html", "site/styles.css", "site/app.js", "docs/CONTENT_PLAN.md", "tests/manifest_check.json"}
        if not required_paths.issubset({entry.path for entry in normalized.file_entries}):
            raise ValidationError("static_web_manifest_missing_required_entries")
    if normalized.manifest_type == "materials_research_manifest":
        required_paths = {"README.md", "docs/RESEARCH_PLAN.md", "docs/EVIDENCE_REQUIREMENTS.md", "config.example.yaml", "src/__init__.py", "src/candidates.py", "src/validation.py", "tests/test_candidates.py", "tests/test_validation.py"}
        if not required_paths.issubset({entry.path for entry in normalized.file_entries}):
            raise ValidationError("materials_manifest_missing_required_entries")
    if normalized.manifest_type == "ai_system_research_manifest":
        required_paths = {"README.md", "docs/GOVERNANCE.md", "docs/EVALUATION_PLAN.md", "src/__init__.py", "src/pipeline.py", "src/validation.py", "tests/test_pipeline.py", "tests/test_validation.py"}
        if not required_paths.issubset({entry.path for entry in normalized.file_entries}):
            raise ValidationError("ai_manifest_missing_required_entries")
    if normalized.manifest_type == "medical_software_pathway_manifest":
        required_paths = {"README.md", "docs/MEDICAL_CLAIM_BOUNDARY.md", "docs/REGULATORY_EVIDENCE_PLAN.md", "docs/SAFETY_VALIDATION_PLAN.md", "config.example.yaml", "src/__init__.py", "src/rules.py", "tests/test_medical_boundary.py"}
        if not required_paths.issubset({entry.path for entry in normalized.file_entries}):
            raise ValidationError("medical_manifest_missing_required_entries")
    if normalized.manifest_type == "industrial_automation_tooling_manifest":
        required_paths = {"README.md", "docs/SAFETY_BOUNDARY.md", "config.example.yaml", "src/__init__.py", "src/normalizer.py", "src/report.py", "tests/test_normalizer.py", "tests/test_report.py"}
        if not required_paths.issubset({entry.path for entry in normalized.file_entries}):
            raise ValidationError("industrial_manifest_missing_required_entries")
    if normalized.manifest_type == "conceptual_research_docs_manifest":
        required_paths = {"README.md", "docs/DEFINITION_MAP.md", "docs/CLAIM_MAP.md", "docs/EVIDENCE_MAP.md", "docs/UNCERTAINTY_LEDGER.md"}
        if not required_paths.issubset({entry.path for entry in normalized.file_entries}):
            raise ValidationError("conceptual_manifest_missing_required_entries")
    if normalized.manifest_type == "unknown_domain_minimal_manifest":
        required_paths = {"README.md", "docs/CLARIFYING_QUESTIONS.md", "docs/EVIDENCE_REQUIREMENTS.md"}
        if not required_paths.issubset({entry.path for entry in normalized.file_entries}):
            raise ValidationError("unknown_manifest_missing_required_entries")

    return True



def summarize_file_manifest_v1(manifest: Any) -> FileManifestSummary:
    if not isinstance(manifest, FileManifest):
        validate_file_manifest_v1(manifest)
        manifest = _normalize_manifest_any(manifest)
    return FileManifestSummary(
        summary_type=SUMMARY_TYPE_V1,
        manifest_id=manifest.manifest_id,
        manifest_type=manifest.manifest_type,
        project_title=manifest.project_title,
        source_stack_decision_id=manifest.source_stack_decision_id,
        runtime_target=manifest.runtime_target,
        recommended_next_artifact=manifest.recommended_next_artifact,
        file_count=len(manifest.file_entries),
        directory_count=len(manifest.directory_entries),
        risk_label_count=len(manifest.risk_labels),
    )



def to_file_manifest_json_safe_v1(value: Any) -> Any:
    return _json_safe(value)


# ---------------------------------------------------------------------------
# Seed examples
# ---------------------------------------------------------------------------


def build_initial_file_manifest_examples_v1() -> tuple[FileManifest, ...]:
    examples: list[FileManifest] = []
    for stack_decision in build_initial_project_stack_decision_examples_v1():
        examples.append(build_file_manifest_from_stack_decision_v1(stack_decision))
    return tuple(examples)


# Backwards-compatible aliases.
build_file_manifest = build_file_manifest_v1
build_file_manifest_from_stack_decision = build_file_manifest_from_stack_decision_v1
validate_file_manifest = validate_file_manifest_v1
summarize_file_manifest = summarize_file_manifest_v1
to_file_manifest_json_safe = to_file_manifest_json_safe_v1
build_initial_file_manifest_examples = build_initial_file_manifest_examples_v1
