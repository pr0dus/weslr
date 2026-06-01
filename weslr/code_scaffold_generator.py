"""Metadata-only code scaffold generator v1.

This module converts a validated file manifest into a deterministic scaffold
content packet. It is pure, deterministic, import-safe, and fail-closed.
No file writes. No subprocess. No model/provider/search/advisor calls.
No chat routing. No runtime behavior changes.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from hashlib import sha256
from typing import Any, Iterable, Mapping

from weslr.file_manifest_builder import (
    FileManifest,
    build_initial_file_manifest_examples_v1,
    to_file_manifest_json_safe_v1,
    validate_file_manifest_v1,
)

HELPER_TYPE_V1 = "code_scaffold_generator_v1"
CODE_SCAFFOLD_PACKET_TYPE_V1 = "code_scaffold_packet_v1"
CODE_SCAFFOLD_SUMMARY_TYPE_V1 = "code_scaffold_summary_v1"

ALLOWED_SCAFFOLD_TYPES_V1 = {
    "python_research_scaffold",
    "python_local_prototype_scaffold",
    "static_web_preview_scaffold",
    "python_web_dashboard_scaffold",
    "privacy_sensitive_local_scaffold",
    "medical_software_pathway_scaffold",
    "industrial_automation_tooling_scaffold",
    "materials_research_scaffold",
    "ai_system_research_scaffold",
    "conceptual_research_docs_scaffold",
    "unknown_domain_minimal_scaffold",
}

ALLOWED_CONTENT_KINDS_V1 = {
    "markdown_template",
    "python_module_template",
    "python_test_template",
    "yaml_template",
    "json_template",
    "html_template",
    "css_template",
    "javascript_template",
    "placeholder_only",
}

ALLOWED_GENERATION_METHODS_V1 = {
    "validated_template",
    "validated_placeholder",
    "manifest_derived",
    "manual_owner_fill",
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

SCaffold_TYPE_BY_MANIFEST_TYPE_V1 = {
    "python_research_manifest": "python_research_scaffold",
    "python_local_prototype_manifest": "python_local_prototype_scaffold",
    "static_web_preview_manifest": "static_web_preview_scaffold",
    "python_web_dashboard_manifest": "python_web_dashboard_scaffold",
    "privacy_sensitive_local_manifest": "privacy_sensitive_local_scaffold",
    "medical_software_pathway_manifest": "medical_software_pathway_scaffold",
    "industrial_automation_tooling_manifest": "industrial_automation_tooling_scaffold",
    "materials_research_manifest": "materials_research_scaffold",
    "ai_system_research_manifest": "ai_system_research_scaffold",
    "conceptual_research_docs_manifest": "conceptual_research_docs_scaffold",
    "unknown_domain_minimal_manifest": "unknown_domain_minimal_scaffold",
}


class ValidationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class GeneratedScaffoldEntry:
    path: str
    file_type: str
    content_kind: str
    content: str
    generation_method: str
    overwrite_allowed: bool
    executable: bool
    contains_secret: bool
    contains_private_data: bool
    validation_command: str
    owner_approval_required: bool
    safe_metadata: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class SkippedScaffoldEntry:
    path: str
    file_type: str
    skip_reason: str
    owner_approval_required: bool
    safe_metadata: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class CodeScaffoldPacket:
    scaffold_id: str
    source_manifest_id: str
    manifest_type: str
    project_title: str
    scaffold_type: str
    generated_entries: list[GeneratedScaffoldEntry]
    skipped_entries: list[SkippedScaffoldEntry]
    validation_plan: list[str]
    dependency_policy: str
    risk_labels: list[str]
    boundary_requirements: list[str]
    recommended_next_artifact: str
    artifact_write_required: bool
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
class CodeScaffoldSummary:
    summary_type: str
    scaffold_id: str
    scaffold_type: str
    project_title: str
    source_manifest_id: str
    generated_count: int
    skipped_count: int
    recommended_next_artifact: str
    risk_label_count: int


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
            blocked.extend(_contains_forbidden_fields(item, f"{path}[{index}]") )
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
    if marker in {"treatment", "diagnosis"} and any(
        phrase in text
        for phrase in (
            "no diagnosis or treatment",
            "no diagnosis and treatment",
            "no diagnosis/treatment",
            "no diagnosis or any treatment",
            "no medical diagnosis or treatment",
            "no diagnosis or treatment authority",
            "no diagnosis authority",
            "no treatment authority",
        )
    ):
        return True
    if marker in {"deployment", "deploy", "rollout"} and any(
        phrase in text
        for phrase in (
            "no deployment",
            "no covert deployment",
            "no unsafe deployment",
            "no covert rollout",
            "no rollout",
            "deployment not allowed",
            "before rollout",
            "after rollout",
            "rollout review",
            "rollout plan",
        )
    ):
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
    if ":" in text[:3]:
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
    dirs: list[str] = []
    for path in paths:
        parent = _parent_directory(path)
        if parent:
            dirs.append(parent)
    return _dedupe_preserve(dirs)


def _slugify(value: Any) -> str:
    text = _normalize_text(value)
    return "".join(ch if ch.isalnum() else "-" for ch in text).strip("-") or "unknown"


def _deterministic_id(*parts: Any, prefix: str) -> str:
    digest = sha256("|".join(_safe_text(part) for part in parts).encode("utf-8")).hexdigest()[:16]
    return f"{prefix}_{digest}"


def _manifest_to_mapping(file_manifest: Any) -> Mapping[str, Any]:
    validate_file_manifest_v1(file_manifest)
    return _as_mapping(file_manifest)


def _scaffold_type_for_manifest_type(manifest_type: str) -> str:
    scaffold_type = SCaffold_TYPE_BY_MANIFEST_TYPE_V1.get(_safe_text(manifest_type))
    if not scaffold_type:
        raise ValidationError("unknown_scaffold_type")
    return scaffold_type


def _content_kind_for_file_type(file_type: str) -> str:
    mapping = {
        "markdown": "markdown_template",
        "python": "python_module_template",
        "python_test": "python_test_template",
        "yaml": "yaml_template",
        "json": "json_template",
        "html": "html_template",
        "css": "css_template",
        "javascript": "javascript_template",
    }
    return mapping.get(_safe_text(file_type), "placeholder_only")


def _generation_method_for_content_kind(content_kind: str) -> str:
    if content_kind == "placeholder_only":
        return "validated_placeholder"
    return "validated_template"


def _base_readme(project_title: str, scaffold_type: str, manifest_type: str) -> str:
    return (
        f"# {project_title}\n\n"
        f"Generated scaffold: `{scaffold_type}`\n\n"
        "This packet was generated from a validated file manifest.\n"
        "It is metadata-only and does not include write permission, runtime permission,\n"
        "dependency approval, or public-claim permission.\n"
    )


def _markdown_content_for_path(path: str, project_title: str, scaffold_type: str, manifest_type: str) -> str:
    lowered = path.lower()
    if lowered == "readme.md":
        return _base_readme(project_title, scaffold_type, manifest_type)
    if lowered.endswith("privacy_boundary.md"):
        return (
            "# Privacy Boundary\n\n"
            "- No raw personal data\n"
            "- No covert tracking\n"
            "- No hidden prompts\n"
            "- No diagnosis or treatment authority\n"
            "- Consent and owner review required\n"
        )
    if lowered.endswith("medical_claim_boundary.md"):
        return (
            "# Medical Claim Boundary\n\n"
            "This scaffold is support-only.\n\n"
            "- No diagnosis authority\n"
            "- No treatment authority\n"
            "- Regulatory review required\n"
            "- Safety validation required\n"
        )
    if lowered.endswith("regulatory_evidence_plan.md"):
        return (
            "# Regulatory Evidence Plan\n\n"
            "- Define claims boundary\n"
            "- Collect evidence for safety review\n"
            "- Track operator approval points\n"
        )
    if lowered.endswith("safety_validation_plan.md"):
        return (
            "# Safety Validation Plan\n\n"
            "- Validate failure modes\n"
            "- Review blocked content\n"
            "- Confirm no unsafe authority\n"
        )
    if lowered.endswith("governance.md"):
        return (
            "# Governance\n\n"
            "- No public capability claims\n"
            "- Evaluation and approval are operator-controlled\n"
        )
    if lowered.endswith("evaluation_plan.md"):
        return (
            "# Evaluation Plan\n\n"
            "- Define metrics and review steps\n"
            "- Keep output metadata-only\n"
            "- Record validation boundaries\n"
        )
    if lowered.endswith("architecture.md"):
        return (
            "# Architecture\n\n"
            "- High-level module boundaries\n"
            "- Safe interfaces only\n"
            "- No runtime side effects\n"
        )
    if lowered.endswith("validation_plan.md"):
        return (
            "# Validation Plan\n\n"
            "- Parse checks\n"
            "- Boundary checks\n"
            "- Determinism checks\n"
        )
    if lowered.endswith("content_plan.md"):
        return (
            "# Content Plan\n\n"
            "- Static preview sections\n"
            "- Safe placeholder content\n"
            "- No deployment authority\n"
        )
    if lowered.endswith("research_plan.md"):
        return (
            "# Research Plan\n\n"
            "- Define hypothesis scope\n"
            "- Define evidence expectations\n"
            "- Keep the scaffold bounded\n"
        )
    if lowered.endswith("evidence_requirements.md"):
        return (
            "# Evidence Requirements\n\n"
            "- Source provenance\n"
            "- Validation evidence\n"
            "- Owner review\n"
        )
    if lowered.endswith("definition_map.md"):
        return (
            "# Definition Map\n\n"
            "- Key terms\n"
            "- Boundaries\n"
            "- Clarification points\n"
        )
    if lowered.endswith("claim_map.md"):
        return (
            "# Claim Map\n\n"
            "- Supportable assertions\n"
            "- Unsupported assertions excluded\n"
            "- No external wording escalation\n"
        )
    if lowered.endswith("evidence_map.md"):
        return (
            "# Evidence Map\n\n"
            "- Evidence needed\n"
            "- Evidence gaps\n"
            "- Review notes\n"
        )
    if lowered.endswith("uncertainty_ledger.md"):
        return (
            "# Uncertainty Ledger\n\n"
            "- Open questions\n"
            "- Unknowns\n"
            "- Assumptions to validate\n"
        )
    if lowered.endswith("clarifying_questions.md"):
        return (
            "# Clarifying Questions\n\n"
            "- What is the intended domain?\n"
            "- What evidence is available?\n"
            "- What boundary applies?\n"
        )
    if lowered.endswith("safety_boundary.md"):
        return (
            "# Safety Boundary\n\n"
            "- No unsafe control\n"
            "- No covert deployment\n"
            "- Operator review required\n"
        )
    if lowered.endswith("architecture.md"):
        return (
            "# Architecture\n\n"
            "- Modular boundaries\n"
            "- Safe interfaces\n"
            "- Validation-first\n"
        )
    return (
        f"# {path}\n\n"
        "Generated markdown scaffold template.\n"
        "Add domain-specific content within the validated boundary.\n"
    )


def _python_content_for_path(path: str, scaffold_type: str) -> str:
    module_name = path.rsplit("/", 1)[-1].replace(".py", "")
    if module_name.startswith("test_"):
        return (
            '"""Placeholder tests for the generated scaffold."""\n\n'
            "from __future__ import annotations\n\n\n"
            "def test_placeholder() -> None:\n"
            "    assert True\n"
        )
    return (
        f'"""Placeholder module for `{path}` in `{scaffold_type}`.\n\n'
        "Generated from a validated file manifest.\n"
        "TODO: implement inside the boundary.\n"
        '"""\n\n'
        "from __future__ import annotations\n\n\n"
        f"SCaffold_TYPE = {scaffold_type!r}\n\n\n"
        "def placeholder() -> None:\n"
        "    raise NotImplementedError('Scaffold placeholder only')\n"
    )


def _yaml_content_for_path(project_title: str, scaffold_type: str) -> str:
    return (
        f"project_title: {project_title}\n"
        f"scaffold_type: {scaffold_type}\n"
        "runtime_authority: false\n"
        "file_write_authority_granted: false\n"
        "dependency_install_authority_granted: false\n"
        "test_execution_authority_granted: false\n"
    )


def _json_content_for_path(project_title: str, scaffold_type: str) -> str:
    return (
        "{\n"
        f'  "project_title": {project_title!r},\n'
        f'  "scaffold_type": {scaffold_type!r},\n'
        '  "runtime_authority": false,\n'
        '  "public_claim_allowed": false\n'
        "}\n"
    )


def _html_content_for_path(project_title: str, scaffold_type: str) -> str:
    return (
        "<!doctype html>\n"
        "<html lang=\"en\">\n"
        "  <head>\n"
        "    <meta charset=\"utf-8\" />\n"
        f"    <title>{project_title}</title>\n"
        "    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />\n"
        "    <link rel=\"stylesheet\" href=\"styles.css\" />\n"
        "  </head>\n"
        "  <body>\n"
        "    <main id=\"app\">\n"
        f"      <h1>{project_title}</h1>\n"
        f"      <p>Static preview scaffold: {scaffold_type}</p>\n"
        "    </main>\n"
        "    <script src=\"app.js\"></script>\n"
        "  </body>\n"
        "</html>\n"
    )


def _css_content_for_path() -> str:
    return (
        "body {\n"
        "  font-family: system-ui, sans-serif;\n"
        "  margin: 0;\n"
        "  padding: 2rem;\n"
        "  line-height: 1.5;\n"
        "}\n\n"
        "#app {\n"
        "  max-width: 60rem;\n"
        "  margin: 0 auto;\n"
        "}\n"
    )


def _javascript_content_for_path(project_title: str) -> str:
    return (
        "const app = document.getElementById('app');\n"
        "if (app) {\n"
        f"  app.dataset.projectTitle = {project_title!r};\n"
        "}\n"
    )


def _placeholder_content_for_path(path: str) -> str:
    return f"# Placeholder for {path}\n"


def _safe_generated_content(entry: Mapping[str, Any], scaffold_type: str, manifest_type: str, project_title: str) -> tuple[str, str, str]:
    file_type = _safe_text(entry.get("file_type"))
    path = _safe_text(entry.get("path"))
    content_kind = _content_kind_for_file_type(file_type)
    generation_method = _generation_method_for_content_kind(content_kind)
    if file_type == "markdown":
        content = _markdown_content_for_path(path, project_title, scaffold_type, manifest_type)
    elif file_type == "python":
        content = _python_content_for_path(path, scaffold_type)
    elif file_type == "python_test":
        content = _python_content_for_path(path, scaffold_type)
    elif file_type == "yaml":
        content = _yaml_content_for_path(project_title, scaffold_type)
    elif file_type == "json":
        content = _json_content_for_path(project_title, scaffold_type)
    elif file_type == "html":
        content = _html_content_for_path(project_title, scaffold_type)
    elif file_type == "css":
        content = _css_content_for_path()
    elif file_type == "javascript":
        content = _javascript_content_for_path(project_title)
    else:
        content_kind = "placeholder_only"
        generation_method = "validated_placeholder"
        content = _placeholder_content_for_path(path)
    return content_kind, generation_method, content


# ---------------------------------------------------------------------------
# Packet construction
# ---------------------------------------------------------------------------


def build_code_scaffold_packet_v1(file_manifest: Any, scaffold_type: str | None = None) -> CodeScaffoldPacket:
    manifest = _manifest_to_mapping(file_manifest)
    manifest_type = _safe_text(manifest.get("manifest_type"))
    project_title = _safe_text(manifest.get("project_title"))
    source_manifest_id = _safe_text(manifest.get("manifest_id"))
    selected_scaffold_type = _safe_text(scaffold_type) or _scaffold_type_for_manifest_type(manifest_type)
    if selected_scaffold_type not in ALLOWED_SCAFFOLD_TYPES_V1:
        raise ValidationError("unknown_scaffold_type")
    if scaffold_type is not None and _safe_text(scaffold_type) != selected_scaffold_type:
        raise ValidationError("unknown_scaffold_type")

    generated_entries: list[GeneratedScaffoldEntry] = []
    skipped_entries: list[SkippedScaffoldEntry] = []
    for entry in _as_mapping(file_manifest).get("file_entries", []):
        entry_map = _as_mapping(entry)
        file_type = _safe_text(entry_map.get("file_type"))
        path = _safe_text(entry_map.get("path"))
        if file_type == "shell_script":
            skipped_entries.append(
                SkippedScaffoldEntry(
                    path=path,
                    file_type=file_type,
                    skip_reason="shell scripts are skipped in scaffold generator v1",
                    owner_approval_required=True,
                    safe_metadata={"source_path": path, "scaffold_type": selected_scaffold_type},
                )
            )
            continue
        content_kind, generation_method, content = _safe_generated_content(entry_map, selected_scaffold_type, manifest_type, project_title)
        generated_entries.append(
            GeneratedScaffoldEntry(
                path=path,
                file_type=file_type,
                content_kind=content_kind,
                content=content,
                generation_method=generation_method,
                overwrite_allowed=False,
                executable=False,
                contains_secret=False,
                contains_private_data=False,
                validation_command=_safe_text(entry_map.get("validation_command")) or "validation pending",
                owner_approval_required=True,
                safe_metadata={
                    "source_file_type": file_type,
                    "source_path": path,
                    "scaffold_type": selected_scaffold_type,
                },
            )
        )

    if not skipped_entries:
        skipped_entries.append(
            SkippedScaffoldEntry(
                path="scripts/bootstrap.sh",
                file_type="shell_script",
                skip_reason="shell scripts are skipped in scaffold generator v1",
                owner_approval_required=True,
                safe_metadata={"scaffold_type": selected_scaffold_type, "source_path": "scripts/bootstrap.sh"},
            )
        )

    packet = CodeScaffoldPacket(
        scaffold_id=_deterministic_id(source_manifest_id, manifest_type, selected_scaffold_type, prefix="cscaf"),
        source_manifest_id=source_manifest_id,
        manifest_type=manifest_type,
        project_title=project_title,
        scaffold_type=selected_scaffold_type,
        generated_entries=generated_entries,
        skipped_entries=skipped_entries,
        validation_plan=_dedupe_preserve([
            *(_normalize_list(manifest.get("validation_plan"))),
            "scaffold content template check",
            "path boundary check",
            "no forbidden claim marker check",
        ]),
        dependency_policy=_safe_text(manifest.get("dependency_policy")),
        risk_labels=_dedupe_preserve(manifest.get("risk_labels") or []),
        boundary_requirements=_dedupe_preserve([
            *(_normalize_list(manifest.get("boundary_requirements"))),
            "no file-write permission",
            "no runtime permission",
            "no dependency-install approval",
            "no test-execution approval",
        ]),
        recommended_next_artifact=_safe_text(manifest.get("recommended_next_artifact")),
        artifact_write_required=False,
        file_write_authority_granted=False,
        dependency_install_authority_granted=False,
        test_execution_authority_granted=False,
        public_claim_allowed=False,
        iss_internal_reference_allowed=False,
        learning_claimed=False,
        runtime_authority=False,
        writes_state=False,
        model_provider_used=False,
        safe_metadata={
            "example_name": _safe_text((manifest.get("safe_metadata") or {}).get("example_name") or source_manifest_id.replace("_file_manifest", "_code_scaffold")),
            "source_manifest_type": manifest_type,
            "source_manifest_id": source_manifest_id,
            "scaffold_type": selected_scaffold_type,
            "generated_count": len(generated_entries),
            "skipped_count": len(skipped_entries),
            "internal_reference_scope": "internal-only",
        },
    )
    validate_code_scaffold_packet_v1(packet)
    return packet



def build_code_scaffold_from_file_manifest_v1(file_manifest: Any) -> CodeScaffoldPacket:
    return build_code_scaffold_packet_v1(file_manifest)


# ---------------------------------------------------------------------------
# Validation / summary / export
# ---------------------------------------------------------------------------


def _generated_entry_from_any(value: Any) -> GeneratedScaffoldEntry:
    if isinstance(value, GeneratedScaffoldEntry):
        return value
    mapping = _as_mapping(value)
    safe_metadata = mapping.get("safe_metadata", None)
    if safe_metadata is not None and not isinstance(safe_metadata, Mapping):
        raise ValidationError("generated_entry_safe_metadata_must_be_mapping")
    return GeneratedScaffoldEntry(
        path=_safe_text(mapping.get("path")),
        file_type=_safe_text(mapping.get("file_type")),
        content_kind=_safe_text(mapping.get("content_kind")),
        content=_safe_text(mapping.get("content")),
        generation_method=_safe_text(mapping.get("generation_method")),
        overwrite_allowed=bool(mapping.get("overwrite_allowed")),
        executable=bool(mapping.get("executable")),
        contains_secret=bool(mapping.get("contains_secret")),
        contains_private_data=bool(mapping.get("contains_private_data")),
        validation_command=_safe_text(mapping.get("validation_command")),
        owner_approval_required=bool(mapping.get("owner_approval_required")),
        safe_metadata=dict(safe_metadata or {}),
    )



def _skipped_entry_from_any(value: Any) -> SkippedScaffoldEntry:
    if isinstance(value, SkippedScaffoldEntry):
        return value
    mapping = _as_mapping(value)
    safe_metadata = mapping.get("safe_metadata", None)
    if safe_metadata is not None and not isinstance(safe_metadata, Mapping):
        raise ValidationError("skipped_entry_safe_metadata_must_be_mapping")
    return SkippedScaffoldEntry(
        path=_safe_text(mapping.get("path")),
        file_type=_safe_text(mapping.get("file_type")),
        skip_reason=_safe_text(mapping.get("skip_reason")),
        owner_approval_required=bool(mapping.get("owner_approval_required")),
        safe_metadata=dict(safe_metadata or {}),
    )



def _normalize_packet_any(packet: Any) -> CodeScaffoldPacket:
    if isinstance(packet, CodeScaffoldPacket):
        return packet
    mapping = _as_mapping(packet)
    safe_metadata = mapping.get("safe_metadata", None)
    if safe_metadata is not None and not isinstance(safe_metadata, Mapping):
        raise ValidationError("safe_metadata_must_be_mapping")
    generated_entries = [_generated_entry_from_any(item) for item in mapping.get("generated_entries", [])]
    skipped_entries = [_skipped_entry_from_any(item) for item in mapping.get("skipped_entries", [])]
    return CodeScaffoldPacket(
        scaffold_id=_safe_text(mapping.get("scaffold_id")),
        source_manifest_id=_safe_text(mapping.get("source_manifest_id")),
        manifest_type=_safe_text(mapping.get("manifest_type")),
        project_title=_safe_text(mapping.get("project_title")),
        scaffold_type=_safe_text(mapping.get("scaffold_type")),
        generated_entries=generated_entries,
        skipped_entries=skipped_entries,
        validation_plan=_normalize_list(mapping.get("validation_plan")),
        dependency_policy=_safe_text(mapping.get("dependency_policy")),
        risk_labels=_normalize_list(mapping.get("risk_labels")),
        boundary_requirements=_normalize_list(mapping.get("boundary_requirements")),
        recommended_next_artifact=_safe_text(mapping.get("recommended_next_artifact")),
        artifact_write_required=bool(mapping.get("artifact_write_required")),
        file_write_authority_granted=bool(mapping.get("file_write_authority_granted")),
        dependency_install_authority_granted=bool(mapping.get("dependency_install_authority_granted")),
        test_execution_authority_granted=bool(mapping.get("test_execution_authority_granted")),
        public_claim_allowed=bool(mapping.get("public_claim_allowed")),
        iss_internal_reference_allowed=bool(mapping.get("iss_internal_reference_allowed")),
        learning_claimed=bool(mapping.get("learning_claimed")),
        runtime_authority=bool(mapping.get("runtime_authority")),
        writes_state=bool(mapping.get("writes_state")),
        model_provider_used=bool(mapping.get("model_provider_used")),
        safe_metadata=dict(safe_metadata or {}),
    )



def validate_code_scaffold_packet_v1(packet: Any) -> bool:
    original = _as_mapping(packet)
    forbidden = _contains_forbidden_fields(original)
    if forbidden:
        raise ValidationError(f"forbidden_field_detected:{forbidden[0]}")
    normalized = _normalize_packet_any(packet)
    if _contains_forbidden_claim_marker(normalized):
        raise ValidationError("forbidden_claim_marker_detected")
    if _contains_unsafe_deployment_marker(normalized):
        raise ValidationError("unsafe_deployment_marker_detected")
    if _contains_covert_tracking_marker(normalized):
        raise ValidationError("covert_tracking_marker_detected")
    if _contains_diagnosis_treatment_marker(normalized):
        raise ValidationError("diagnosis_treatment_marker_detected")

    if normalized.scaffold_type not in ALLOWED_SCAFFOLD_TYPES_V1:
        raise ValidationError("unknown_scaffold_type")
    if normalized.recommended_next_artifact not in ALLOWED_NEXT_ARTIFACTS_V1:
        raise ValidationError("unknown_recommended_next_artifact")
    if not normalized.scaffold_id:
        raise ValidationError("scaffold_id_required")
    if not normalized.source_manifest_id:
        raise ValidationError("source_manifest_id_required")
    if not normalized.manifest_type:
        raise ValidationError("manifest_type_required")
    if not normalized.project_title:
        raise ValidationError("project_title_required")

    for field_name in (
        "artifact_write_required",
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
        if type(getattr(normalized, field_name)) is not bool:
            raise ValidationError(f"{field_name}_must_be_bool")

    if normalized.artifact_write_required:
        raise ValidationError("artifact_write_required_must_be_false")
    if normalized.file_write_authority_granted:
        raise ValidationError("file_write_authority_granted_must_be_false")
    if normalized.dependency_install_authority_granted:
        raise ValidationError("dependency_install_authority_granted_must_be_false")
    if normalized.test_execution_authority_granted:
        raise ValidationError("test_execution_authority_granted_must_be_false")
    if normalized.public_claim_allowed:
        raise ValidationError("public_claim_allowed_must_be_false")
    if normalized.learning_claimed:
        raise ValidationError("learning_claimed_must_be_false")
    if normalized.runtime_authority:
        raise ValidationError("runtime_authority_must_be_false")
    if normalized.writes_state:
        raise ValidationError("writes_state_must_be_false")
    if normalized.model_provider_used:
        raise ValidationError("model_provider_used_must_be_false")

    if not normalized.generated_entries:
        raise ValidationError("generated_entries_required")
    if any(entry.contains_secret for entry in normalized.generated_entries):
        raise ValidationError("contains_secret_must_be_false")
    if any(entry.contains_private_data for entry in normalized.generated_entries):
        raise ValidationError("contains_private_data_must_be_false")
    if any(entry.owner_approval_required is not True for entry in normalized.generated_entries):
        raise ValidationError("owner_approval_required_must_be_true")
    if any(entry.overwrite_allowed for entry in normalized.generated_entries):
        raise ValidationError("overwrite_allowed_must_be_false")
    if any(entry.executable for entry in normalized.generated_entries):
        raise ValidationError("executable_must_be_false")

    for entry in normalized.generated_entries:
        if not _is_safe_relative_path(entry.path):
            raise ValidationError("unsafe_file_path")
        if _is_protected_path(entry.path):
            raise ValidationError("protected_path_blocked")
        if entry.file_type not in {"markdown", "python", "python_test", "yaml", "json", "html", "css", "javascript"}:
            raise ValidationError("unknown_file_type")
        if entry.content_kind not in ALLOWED_CONTENT_KINDS_V1:
            raise ValidationError("unknown_content_kind")
        if entry.generation_method not in ALLOWED_GENERATION_METHODS_V1:
            raise ValidationError("unknown_generation_method")
        if not _safe_text(entry.content):
            raise ValidationError("content_required")
        if not _safe_text(entry.validation_command):
            raise ValidationError("validation_command_required")
        if not entry.safe_metadata or not isinstance(entry.safe_metadata, dict):
            raise ValidationError("generated_entry_safe_metadata_required")

    for entry in normalized.skipped_entries:
        if not _is_safe_relative_path(entry.path):
            raise ValidationError("unsafe_skipped_path")
        if _is_protected_path(entry.path):
            raise ValidationError("protected_path_blocked")
        if not _safe_text(entry.skip_reason):
            raise ValidationError("skip_reason_required")
        if entry.owner_approval_required is not True:
            raise ValidationError("skipped_entry_owner_approval_required_must_be_true")

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
        if not required_paths.issubset({entry.path for entry in normalized.generated_entries}):
            raise ValidationError("privacy_scaffold_missing_required_entries")
    if normalized.manifest_type == "static_web_preview_manifest":
        required_paths = {"README.md", "site/index.html", "site/styles.css", "site/app.js", "docs/CONTENT_PLAN.md", "tests/manifest_check.json"}
        if not required_paths.issubset({entry.path for entry in normalized.generated_entries}):
            raise ValidationError("static_web_scaffold_missing_required_entries")
    if normalized.manifest_type == "materials_research_manifest":
        required_paths = {"README.md", "docs/RESEARCH_PLAN.md", "docs/EVIDENCE_REQUIREMENTS.md", "config.example.yaml", "src/__init__.py", "src/candidates.py", "src/validation.py", "tests/test_candidates.py", "tests/test_validation.py"}
        if not required_paths.issubset({entry.path for entry in normalized.generated_entries}):
            raise ValidationError("materials_scaffold_missing_required_entries")
    if normalized.manifest_type == "ai_system_research_manifest":
        required_paths = {"README.md", "docs/GOVERNANCE.md", "docs/EVALUATION_PLAN.md", "src/__init__.py", "src/pipeline.py", "src/validation.py", "tests/test_pipeline.py", "tests/test_validation.py"}
        if not required_paths.issubset({entry.path for entry in normalized.generated_entries}):
            raise ValidationError("ai_scaffold_missing_required_entries")
    if normalized.manifest_type == "medical_software_pathway_manifest":
        required_paths = {"README.md", "docs/MEDICAL_CLAIM_BOUNDARY.md", "docs/REGULATORY_EVIDENCE_PLAN.md", "docs/SAFETY_VALIDATION_PLAN.md", "config.example.yaml", "src/__init__.py", "src/rules.py", "tests/test_medical_boundary.py"}
        if not required_paths.issubset({entry.path for entry in normalized.generated_entries}):
            raise ValidationError("medical_scaffold_missing_required_entries")
    if normalized.manifest_type == "industrial_automation_tooling_manifest":
        required_paths = {"README.md", "docs/SAFETY_BOUNDARY.md", "config.example.yaml", "src/__init__.py", "src/normalizer.py", "src/report.py", "tests/test_normalizer.py", "tests/test_report.py"}
        if not required_paths.issubset({entry.path for entry in normalized.generated_entries}):
            raise ValidationError("industrial_scaffold_missing_required_entries")
    if normalized.manifest_type == "conceptual_research_docs_manifest":
        required_paths = {"README.md", "docs/DEFINITION_MAP.md", "docs/CLAIM_MAP.md", "docs/EVIDENCE_MAP.md", "docs/UNCERTAINTY_LEDGER.md"}
        if not required_paths.issubset({entry.path for entry in normalized.generated_entries}):
            raise ValidationError("conceptual_scaffold_missing_required_entries")
        if normalized.scaffold_type != "conceptual_research_docs_scaffold":
            raise ValidationError("conceptual_manifest_must_map_to_docs_scaffold")
    if normalized.manifest_type == "unknown_domain_minimal_manifest":
        required_paths = {"README.md", "docs/CLARIFYING_QUESTIONS.md", "docs/EVIDENCE_REQUIREMENTS.md"}
        if not required_paths.issubset({entry.path for entry in normalized.generated_entries}):
            raise ValidationError("unknown_scaffold_missing_required_entries")
        if normalized.scaffold_type != "unknown_domain_minimal_scaffold":
            raise ValidationError("unknown_manifest_must_map_to_unknown_scaffold")
    return True



def summarize_code_scaffold_packet_v1(packet: Any) -> CodeScaffoldSummary:
    normalized = _normalize_packet_any(packet)
    return CodeScaffoldSummary(
        summary_type=CODE_SCAFFOLD_SUMMARY_TYPE_V1,
        scaffold_id=normalized.scaffold_id,
        scaffold_type=normalized.scaffold_type,
        project_title=normalized.project_title,
        source_manifest_id=normalized.source_manifest_id,
        generated_count=len(normalized.generated_entries),
        skipped_count=len(normalized.skipped_entries),
        recommended_next_artifact=normalized.recommended_next_artifact,
        risk_label_count=len(normalized.risk_labels),
    )



def to_code_scaffold_json_safe_v1(value: Any) -> Any:
    return _json_safe(value)



def build_initial_code_scaffold_examples_v1() -> list[CodeScaffoldPacket]:
    manifests = build_initial_file_manifest_examples_v1()
    wanted = {
        "wifi_rf_self_care_file_manifest": "wifi_rf_self_care_code_scaffold",
        "metamaterials_research_file_manifest": "metamaterials_research_code_scaffold",
        "ai_agent_architecture_file_manifest": "ai_agent_architecture_code_scaffold",
        "medical_software_pathway_file_manifest": "medical_software_pathway_code_scaffold",
        "industrial_automation_file_manifest": "industrial_automation_code_scaffold",
        "software_product_static_web_file_manifest": "software_product_static_web_code_scaffold",
        "theory_of_mind_conceptual_file_manifest": "theory_of_mind_conceptual_code_scaffold",
        "unknown_domain_file_manifest": "unknown_domain_code_scaffold",
    }
    by_id = {manifest.manifest_id: manifest for manifest in manifests}
    examples: list[CodeScaffoldPacket] = []
    for manifest_id, scaffold_id in wanted.items():
        manifest = by_id.get(manifest_id)
        if manifest is None:
            continue
        packet = build_code_scaffold_from_file_manifest_v1(manifest)
        packet_map = to_code_scaffold_json_safe_v1(packet)
        packet_map["scaffold_id"] = scaffold_id
        packet_map["safe_metadata"] = {**(packet_map.get("safe_metadata") or {}), "example_name": scaffold_id}
        examples.append(_normalize_packet_any(packet_map))
    return examples
