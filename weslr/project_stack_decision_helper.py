"""Metadata-only project stack decision helper v1.

This module converts a validated project architecture plan into a bounded
technology stack decision.

It is pure, deterministic, import-safe, and fail-closed.
No model/provider/search/advisor calls. No network. No I/O. No state writes.
No chat routing. No runtime behavior changes.
"""

from __future__ import annotations

import copy
import re
from dataclasses import asdict, dataclass, is_dataclass
from typing import Any, Iterable, Mapping

from weslr.project_architecture_planner import (
    ArchitecturePlan,
    build_initial_project_architecture_examples_v1,
    validate_project_architecture_plan_v1,
)

HELPER_TYPE_V1 = "project_stack_decision_helper_v1"
STACK_DECISION_TYPE_V1 = "project_stack_decision_v1"
SUMMARY_TYPE_V1 = "project_stack_decision_summary_v1"

ALLOWED_STACK_DECISION_TYPES_V1 = {
    "python_research_stack",
    "python_local_prototype_stack",
    "static_web_preview_stack",
    "python_web_dashboard_stack",
    "privacy_sensitive_local_stack",
    "medical_software_pathway_stack",
    "industrial_automation_tooling_stack",
    "materials_research_stack",
    "ai_system_research_stack",
    "conceptual_research_docs_stack",
    "unknown_domain_minimal_stack",
}

ALLOWED_ARTIFACT_TARGETS_V1 = {
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
}

ALLOWED_RUNTIME_TARGETS_V1 = {
    "none_docs_only",
    "local_python",
    "local_static_web",
    "local_python_with_static_dashboard",
    "sandbox_only",
    "unknown_pending_requirements",
}

ALLOWED_STORAGE_CHOICES_V1 = {
    "none",
    "local_files",
    "sqlite",
    "json_files",
    "yaml_files",
    "future_database_pending_requirements",
}

ALLOWED_DEPENDENCY_POLICIES_V1 = {
    "stdlib_only_preferred",
    "minimal_pinned_dependencies",
    "no_dependency_install_without_approval",
    "domain_specific_dependencies_require_review",
    "unknown_pending_requirements",
}

ALLOWED_RECOMMENDED_NEXT_ARTIFACTS_V1 = {
    "file_manifest",
    "validation_plan",
    "evidence_map",
    "boundary_review",
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


class ValidationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class StackDecision:
    stack_decision_id: str
    stack_decision_type: str
    source_architecture_id: str
    source_brief_id: str
    project_title: str
    architecture_type: str
    domain_family: str
    meta_domains: list[str]
    risk_labels: list[str]
    local_cloud_strategy: str
    prototype_allowed_level: str
    primary_language: str
    secondary_languages: list[str]
    artifact_targets: list[str]
    runtime_target: str
    storage_choice: str
    config_format: str
    documentation_format: str
    test_strategy: str
    validation_commands: list[str]
    dependency_policy: str
    ui_strategy: str
    backend_strategy: str
    data_strategy: str
    privacy_stack_requirements: str
    safety_stack_requirements: str
    legal_stack_requirements: str
    medical_stack_requirements: str
    rejected_stack_options: list[str]
    stack_rationale: str
    constraints: list[str]
    assumptions: list[str]
    unknowns: list[str]
    recommended_next_artifact: str
    file_manifest_required: bool
    code_generation_allowed: bool
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
class StackDecisionSummary:
    summary_type: str
    stack_decision_id: str
    stack_decision_type: str
    project_title: str
    primary_language: str
    runtime_target: str
    recommended_next_artifact: str
    stack_rationale: str
    artifact_target_count: int
    validation_command_count: int


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



def _as_mapping(value: Any) -> Mapping[str, Any]:
    if is_dataclass(value):
        return asdict(value)
    if isinstance(value, Mapping):
        return value
    raise ValidationError("stack_decision_must_be_dataclass_or_mapping")



def _slugify(value: str) -> str:
    text = _normalize_text(value)
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_") or "stack"



def _list_blob(items: Iterable[str]) -> str:
    return " ".join(_normalize_text(item) for item in items)



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
    for prefix in ("no ", "not ", "without ", "never "):
        if f"{prefix}{marker}" in text:
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
        return any(term in blob for term in UNSAFE_DEPLOYMENT_TERMS_V1)
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


# ---------------------------------------------------------------------------
# Architecture routing
# ---------------------------------------------------------------------------


def _stack_decision_type_for_architecture_plan(plan: Mapping[str, Any]) -> str:
    architecture_type = _safe_text(plan.get("architecture_type"))
    selected_architecture = _normalize_text(plan.get("selected_architecture"))
    interface_blob = _normalize_text(plan.get("interface_surfaces"))
    blob = f"{selected_architecture} {interface_blob}"

    if architecture_type == "privacy_sensitive_assistive_architecture":
        return "privacy_sensitive_local_stack"
    if architecture_type == "medical_software_pathway_architecture":
        return "medical_software_pathway_stack"
    if architecture_type == "materials_research_architecture":
        return "materials_research_stack"
    if architecture_type == "ai_system_architecture":
        return "ai_system_research_stack"
    if architecture_type == "industrial_automation_architecture":
        return "industrial_automation_tooling_stack"
    if architecture_type == "conceptual_research_architecture":
        return "conceptual_research_docs_stack"
    if architecture_type == "unknown_domain_architecture":
        return "unknown_domain_minimal_stack"
    if architecture_type == "software_product_architecture":
        if "dashboard" in blob:
            return "python_web_dashboard_stack"
        return "static_web_preview_stack"
    if architecture_type == "sandbox_prototype_architecture":
        return "python_local_prototype_stack"
    if architecture_type == "local_first_research_architecture":
        return "python_research_stack"
    return "unknown_domain_minimal_stack"



def _file_manifest_required_for_stack_type(stack_decision_type: str) -> bool:
    return stack_decision_type not in {
        "conceptual_research_docs_stack",
        "unknown_domain_minimal_stack",
    }



def _recommended_next_artifact_for_stack_type(stack_decision_type: str) -> str:
    if stack_decision_type == "conceptual_research_docs_stack":
        return "evidence_map"
    if stack_decision_type == "unknown_domain_minimal_stack":
        return "clarifying_questions"
    if stack_decision_type in {
        "privacy_sensitive_local_stack",
        "medical_software_pathway_stack",
        "materials_research_stack",
        "ai_system_research_stack",
        "industrial_automation_tooling_stack",
        "python_research_stack",
        "python_local_prototype_stack",
        "python_web_dashboard_stack",
        "static_web_preview_stack",
    }:
        return "file_manifest"
    return "file_manifest"



def _stack_profile_for_stack_type(stack_decision_type: str, plan: Mapping[str, Any]) -> dict[str, Any]:
    selected_architecture = _safe_text(plan.get("selected_architecture"))
    architecture_blob = _normalize_text(selected_architecture)

    if stack_decision_type == "privacy_sensitive_local_stack":
        return {
            "primary_language": "python",
            "secondary_languages": ["markdown", "yaml", "html", "css", "javascript"],
            "artifact_targets": [
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
                "architecture_report",
                "file_manifest",
            ],
            "runtime_target": "local_python_with_static_dashboard",
            "storage_choice": "sqlite",
            "config_format": "yaml",
            "documentation_format": "markdown",
            "test_strategy": "pytest plus privacy and audit checks",
            "validation_commands": [
                "python -m py_compile <stack modules>",
                "python -m pytest <stack tests> -q",
                "privacy audit checklist review",
            ],
            "dependency_policy": "domain_specific_dependencies_require_review",
            "ui_strategy": "local dashboard and manual override",
            "backend_strategy": "local_python_service",
            "data_strategy": "sqlite_audit_records_and_derived_features",
            "privacy_stack_requirements": "local-first storage, data minimization, user control, auditability, no covert tracking",
            "safety_stack_requirements": "validation before reliance, bounded reminders only, no diagnosis authority, no treatment recommendation",
            "legal_stack_requirements": "consent review, household policy alignment, affected-person review",
            "medical_stack_requirements": "support-only scope, no diagnosis authority, no treatment recommendation",
            "rejected_stack_options": ["cloud-first stack", "no covert tracking stack", "no diagnosis authority stack"],
            "stack_rationale": "Python keeps the assistive pipeline local and auditable while allowing an optional local dashboard.",
            "constraints": _dedupe_preserve([*plan.get("boundary_requirements", []), "metadata-only", "no runtime authority"]),
            "assumptions": _dedupe_preserve(["architecture plan is validated", "local execution only", *plan.get("assumptions", [])]),
            "unknowns": _dedupe_preserve([*plan.get("unknowns", []), "later file manifest still needs exact layout"]),
        }
    if stack_decision_type == "medical_software_pathway_stack":
        return {
            "primary_language": "python",
            "secondary_languages": ["markdown", "yaml", "json"],
            "artifact_targets": [
                "markdown_docs",
                "python_package",
                "python_cli",
                "python_tests",
                "yaml_config",
                "json_schema",
                "sqlite_storage",
                "architecture_report",
                "file_manifest",
            ],
            "runtime_target": "local_python",
            "storage_choice": "sqlite",
            "config_format": "yaml",
            "documentation_format": "markdown",
            "test_strategy": "pytest with clinical, regulatory, and safety review checks",
            "validation_commands": [
                "python -m py_compile <stack modules>",
                "python -m pytest <stack tests> -q",
                "clinical review checklist",
                "regulatory review checklist",
            ],
            "dependency_policy": "domain_specific_dependencies_require_review",
            "ui_strategy": "review-focused local interface",
            "backend_strategy": "local_python_service",
            "data_strategy": "sqlite_audit_records",
            "privacy_stack_requirements": "bounded data handling, least privilege, auditability",
            "safety_stack_requirements": "clinical validation, regulatory review, safety review, support-only scope",
            "legal_stack_requirements": "compliance review, release review, policy alignment",
            "medical_stack_requirements": "no diagnosis authority, no treatment recommendation, clinical support only",
            "rejected_stack_options": ["no diagnosis authority stack", "no treatment authority stack", "no release before review stack"],
            "stack_rationale": "Python is the safest bounded support language for a regulated pathway with local audit controls.",
            "constraints": _dedupe_preserve([*plan.get("boundary_requirements", []), "metadata-only", "no production claim"]),
            "assumptions": _dedupe_preserve(["regulatory review is required", *plan.get("assumptions", [])]),
            "unknowns": _dedupe_preserve([*plan.get("unknowns", []), "clinical integration details remain unspecified"]),
        }
    if stack_decision_type == "materials_research_stack":
        return {
            "primary_language": "python",
            "secondary_languages": ["markdown", "yaml", "json"],
            "artifact_targets": [
                "markdown_docs",
                "python_package",
                "python_cli",
                "python_tests",
                "yaml_config",
                "json_schema",
                "architecture_report",
                "file_manifest",
                "sqlite_storage",
            ],
            "runtime_target": "local_python",
            "storage_choice": "json_files",
            "config_format": "yaml",
            "documentation_format": "markdown",
            "test_strategy": "pytest plus evidence, scientific dependency review, and validation placeholders",
            "validation_commands": [
                "python -m py_compile <stack modules>",
                "python -m pytest <stack tests> -q",
                "literature review checklist",
                "validation criteria review",
            ],
            "dependency_policy": "domain_specific_dependencies_require_review",
            "ui_strategy": "cli and report",
            "backend_strategy": "local_python_research_tools",
            "data_strategy": "local_files_and_json",
            "privacy_stack_requirements": "citation hygiene, bounded collections, local metadata first",
            "safety_stack_requirements": "uncertainty handling, validation before reliance",
            "legal_stack_requirements": "no external release without approval",
            "medical_stack_requirements": "not a medical pathway",
            "rejected_stack_options": ["production readiness stack", "unsupported feasibility stack", "public release stack"],
            "stack_rationale": "Python supports lightweight local research tooling and scientific review placeholders.",
            "constraints": _dedupe_preserve([*plan.get("boundary_requirements", []), "metadata-only", "no production claim"]),
            "assumptions": _dedupe_preserve(["evidence review precedes implementation", *plan.get("assumptions", [])]),
            "unknowns": _dedupe_preserve([*plan.get("unknowns", []), "experimental validation method still needs selection"]),
        }
    if stack_decision_type == "ai_system_research_stack":
        return {
            "primary_language": "python",
            "secondary_languages": ["markdown", "yaml", "json"],
            "artifact_targets": [
                "markdown_docs",
                "python_package",
                "python_cli",
                "python_tests",
                "yaml_config",
                "json_schema",
                "architecture_report",
                "file_manifest",
                "sqlite_storage",
            ],
            "runtime_target": "local_python",
            "storage_choice": "sqlite",
            "config_format": "yaml",
            "documentation_format": "markdown",
            "test_strategy": "pytest plus governance and evaluation checks",
            "validation_commands": [
                "python -m py_compile <stack modules>",
                "python -m pytest <stack tests> -q",
                "governance checklist",
                "evaluation harness review",
            ],
            "dependency_policy": "domain_specific_dependencies_require_review",
            "ui_strategy": "governance dashboard and reporting CLI",
            "backend_strategy": "local_python_research_service",
            "data_strategy": "sqlite_trace_records",
            "privacy_stack_requirements": "bounded data handling, trace minimization",
            "safety_stack_requirements": "governance boundary, evaluation harness, safety review, rollback path",
            "legal_stack_requirements": "no official statements, release review",
            "medical_stack_requirements": "not a medical pathway",
            "rejected_stack_options": ["runtime autonomy stack", "public benchmark stack", "release without governance stack"],
            "stack_rationale": "Python keeps the governance and evaluation harness local and easy to audit.",
            "constraints": _dedupe_preserve([*plan.get("boundary_requirements", []), "metadata-only", "no runtime authority"]),
            "assumptions": _dedupe_preserve(["evaluation and trace surfaces are local", *plan.get("assumptions", [])]),
            "unknowns": _dedupe_preserve([*plan.get("unknowns", []), "future evaluation dataset still needs definition"]),
        }
    if stack_decision_type == "industrial_automation_tooling_stack":
        return {
            "primary_language": "python",
            "secondary_languages": ["yaml", "json", "markdown", "shell"],
            "artifact_targets": [
                "markdown_docs",
                "python_package",
                "python_cli",
                "python_tests",
                "yaml_config",
                "json_schema",
                "shell_validation_script",
                "architecture_report",
                "file_manifest",
            ],
            "runtime_target": "local_python",
            "storage_choice": "yaml_files",
            "config_format": "yaml",
            "documentation_format": "markdown",
            "test_strategy": "pytest plus config normalization checks",
            "validation_commands": [
                "python -m py_compile <stack modules>",
                "python -m pytest <stack tests> -q",
                "config normalization review",
                "safety report review",
            ],
            "dependency_policy": "domain_specific_dependencies_require_review",
            "ui_strategy": "cli and report",
            "backend_strategy": "local_python_tooling",
            "data_strategy": "yaml_and_json_normalized_configs",
            "privacy_stack_requirements": "bounded logs, access control",
            "safety_stack_requirements": "safety boundary, validation reporting, operator confirmation",
            "legal_stack_requirements": "owner approval, policy alignment",
            "medical_stack_requirements": "not a medical pathway",
            "rejected_stack_options": ["reviewless control path", "hidden control path", "unbounded rollout stack"],
            "stack_rationale": "Python is a practical tooling layer for safe configuration normalization and reporting.",
            "constraints": _dedupe_preserve([*plan.get("boundary_requirements", []), "metadata-only", "no unsafe control commands"]),
            "assumptions": _dedupe_preserve(["operators will review before control changes", *plan.get("assumptions", [])]),
            "unknowns": _dedupe_preserve([*plan.get("unknowns", []), "device integration details still need scoping"]),
        }
    if stack_decision_type == "static_web_preview_stack":
        return {
            "primary_language": "html",
            "secondary_languages": ["css", "javascript", "markdown"],
            "artifact_targets": [
                "markdown_docs",
                "static_html",
                "css_styles",
                "browser_javascript",
                "architecture_report",
                "file_manifest",
            ],
            "runtime_target": "local_static_web",
            "storage_choice": "local_files",
            "config_format": "json",
            "documentation_format": "markdown",
            "test_strategy": "local browser preview and UI smoke checks",
            "validation_commands": [
                "local browser preview review",
                "html/css/js smoke check",
            ],
            "dependency_policy": "stdlib_only_preferred",
            "ui_strategy": "static preview in browser",
            "backend_strategy": "none or tiny local helper",
            "data_strategy": "local_files",
            "privacy_stack_requirements": "no public publish authority, local preview only",
            "safety_stack_requirements": "review before release, no runtime authority, no state writes",
            "legal_stack_requirements": "no release authority, no external release without approval",
            "medical_stack_requirements": "not a medical pathway",
            "rejected_stack_options": ["cloud publish path", "release authority", "runtime mutation stack"],
            "stack_rationale": "Static HTML/CSS/JS is the simplest bounded preview stack for product-facing artifacts.",
            "constraints": _dedupe_preserve([*plan.get("boundary_requirements", []), "metadata-only", "no release authority"]),
            "assumptions": _dedupe_preserve(["local preview is sufficient for the current phase", *plan.get("assumptions", [])]),
            "unknowns": _dedupe_preserve([*plan.get("unknowns", []), "later backend choice may still change"]),
        }
    if stack_decision_type == "python_web_dashboard_stack":
        return {
            "primary_language": "python",
            "secondary_languages": ["html", "css", "javascript", "markdown"],
            "artifact_targets": [
                "markdown_docs",
                "python_package",
                "python_cli",
                "python_tests",
                "static_html",
                "css_styles",
                "browser_javascript",
                "sqlite_storage",
                "architecture_report",
                "file_manifest",
            ],
            "runtime_target": "local_python_with_static_dashboard",
            "storage_choice": "sqlite",
            "config_format": "yaml",
            "documentation_format": "markdown",
            "test_strategy": "pytest plus browser dashboard checks",
            "validation_commands": [
                "python -m pytest <stack tests> -q",
                "browser dashboard smoke check",
            ],
            "dependency_policy": "minimal_pinned_dependencies",
            "ui_strategy": "python-backed dashboard",
            "backend_strategy": "local_python_service",
            "data_strategy": "sqlite_audit_records",
            "privacy_stack_requirements": "bounded data capture, local dashboard controls, auditability",
            "safety_stack_requirements": "review before release, rollback path, no runtime authority",
            "legal_stack_requirements": "no external release without approval",
            "medical_stack_requirements": "not a medical pathway",
            "rejected_stack_options": ["cloud dashboard stack", "unreviewed release stack", "runtime autonomy stack"],
            "stack_rationale": "Python with a local dashboard is appropriate when a project needs an interactive local review surface.",
            "constraints": _dedupe_preserve([*plan.get("boundary_requirements", []), "metadata-only", "no release authority"]),
            "assumptions": _dedupe_preserve(["dashboard stays local", *plan.get("assumptions", [])]),
            "unknowns": _dedupe_preserve([*plan.get("unknowns", []), "final dashboard layout may change"]),
        }
    if stack_decision_type == "python_research_stack":
        return {
            "primary_language": "python",
            "secondary_languages": ["markdown", "yaml", "json"],
            "artifact_targets": [
                "markdown_docs",
                "python_package",
                "python_cli",
                "python_tests",
                "yaml_config",
                "json_schema",
                "architecture_report",
                "file_manifest",
            ],
            "runtime_target": "local_python",
            "storage_choice": "local_files",
            "config_format": "yaml",
            "documentation_format": "markdown",
            "test_strategy": "pytest plus local smoke validation",
            "validation_commands": [
                "python -m py_compile <stack modules>",
                "python -m pytest <stack tests> -q",
            ],
            "dependency_policy": "stdlib_only_preferred",
            "ui_strategy": "cli first",
            "backend_strategy": "local_python_modules",
            "data_strategy": "local_files_and_json",
            "privacy_stack_requirements": "local-first, bounded collection, metadata-only planning",
            "safety_stack_requirements": "validation before reliance, no runtime authority, no state writes",
            "legal_stack_requirements": "no external release without approval",
            "medical_stack_requirements": "not a medical pathway",
            "rejected_stack_options": ["cloud-first research stack", "runtime autonomy stack", "public release stack"],
            "stack_rationale": "Python is the right default for local research tooling, validation scaffolds, and metadata transforms.",
            "constraints": _dedupe_preserve([*plan.get("boundary_requirements", []), "metadata-only", "no state writes"]),
            "assumptions": _dedupe_preserve(["local research workflow", *plan.get("assumptions", [])]),
            "unknowns": _dedupe_preserve([*plan.get("unknowns", []), "exact file manifest still pending"]),
        }
    if stack_decision_type == "python_local_prototype_stack":
        return {
            "primary_language": "python",
            "secondary_languages": ["markdown", "yaml", "json"],
            "artifact_targets": [
                "markdown_docs",
                "python_package",
                "python_cli",
                "python_tests",
                "yaml_config",
                "json_schema",
                "architecture_report",
                "file_manifest",
            ],
            "runtime_target": "local_python",
            "storage_choice": "local_files",
            "config_format": "yaml",
            "documentation_format": "markdown",
            "test_strategy": "pytest and local prototype checks",
            "validation_commands": [
                "python -m py_compile <stack modules>",
                "python -m pytest <stack tests> -q",
            ],
            "dependency_policy": "minimal_pinned_dependencies",
            "ui_strategy": "cli first",
            "backend_strategy": "local_python_prototype",
            "data_strategy": "local_files_and_json",
            "privacy_stack_requirements": "local-first prototype only",
            "safety_stack_requirements": "bounded prototype, review before rollout",
            "legal_stack_requirements": "no external release without approval",
            "medical_stack_requirements": "not a medical pathway",
            "rejected_stack_options": ["cloud-first prototype stack", "runtime autonomy stack", "unreviewed release stack"],
            "stack_rationale": "Python is ideal for a bounded local prototype with low overhead and easy review.",
            "constraints": _dedupe_preserve([*plan.get("boundary_requirements", []), "metadata-only", "no runtime authority"]),
            "assumptions": _dedupe_preserve(["prototype remains local", *plan.get("assumptions", [])]),
            "unknowns": _dedupe_preserve([*plan.get("unknowns", []), "later stack hardening may need a new review"]),
        }
    if stack_decision_type == "conceptual_research_docs_stack":
        return {
            "primary_language": "markdown",
            "secondary_languages": ["yaml", "json"],
            "artifact_targets": ["markdown_docs", "architecture_report", "file_manifest"],
            "runtime_target": "none_docs_only",
            "storage_choice": "none",
            "config_format": "markdown",
            "documentation_format": "markdown",
            "test_strategy": "review-only consistency checks",
            "validation_commands": [
                "documentation review",
                "evidence map review",
            ],
            "dependency_policy": "stdlib_only_preferred",
            "ui_strategy": "docs only",
            "backend_strategy": "none",
            "data_strategy": "markdown_notes_and_placeholders",
            "privacy_stack_requirements": "local notes only, no raw private data",
            "safety_stack_requirements": "claim discipline, uncertainty handling, no runtime authority",
            "legal_stack_requirements": "no external release without approval",
            "medical_stack_requirements": "not a medical pathway",
            "rejected_stack_options": ["public theory stack", "overclaim stack", "runtime stack"],
            "stack_rationale": "Conceptual work should stay in documents and evidence maps, not code or runtime.",
            "constraints": _dedupe_preserve([*plan.get("boundary_requirements", []), "docs only", "no runtime authority"]),
            "assumptions": _dedupe_preserve(["evidence review is document-based", *plan.get("assumptions", [])]),
            "unknowns": _dedupe_preserve([*plan.get("unknowns", []), "theory framing may need clarification"]),
        }
    if stack_decision_type == "unknown_domain_minimal_stack":
        return {
            "primary_language": "markdown",
            "secondary_languages": ["yaml"],
            "artifact_targets": ["markdown_docs", "architecture_report"],
            "runtime_target": "unknown_pending_requirements",
            "storage_choice": "future_database_pending_requirements",
            "config_format": "markdown",
            "documentation_format": "markdown",
            "test_strategy": "clarification-first review",
            "validation_commands": [
                "clarifying questions review",
                "evidence checklist review",
            ],
            "dependency_policy": "unknown_pending_requirements",
            "ui_strategy": "clarification-first docs",
            "backend_strategy": "none",
            "data_strategy": "minimal_metadata_only",
            "privacy_stack_requirements": "minimal collection, local metadata only",
            "safety_stack_requirements": "no unsafe assumptions, bounded exploration only",
            "legal_stack_requirements": "no external release without approval",
            "medical_stack_requirements": "not a medical pathway",
            "rejected_stack_options": ["premature stack commitment", "public claim stack", "runtime stack"],
            "stack_rationale": "Unknown domains should stay minimal until clarification resolves the scope.",
            "constraints": _dedupe_preserve([*plan.get("boundary_requirements", []), "metadata-only", "clarification first"]),
            "assumptions": _dedupe_preserve(["domain remains underspecified", *plan.get("assumptions", [])]),
            "unknowns": _dedupe_preserve([*plan.get("unknowns", []), "scope still pending clarification"]),
        }
    return {
        "primary_language": "markdown",
        "secondary_languages": ["yaml"],
        "artifact_targets": ["markdown_docs", "architecture_report"],
        "runtime_target": "unknown_pending_requirements",
        "storage_choice": "future_database_pending_requirements",
        "config_format": "markdown",
        "documentation_format": "markdown",
        "test_strategy": "clarification-first review",
        "validation_commands": ["clarifying questions review"],
        "dependency_policy": "unknown_pending_requirements",
        "ui_strategy": "docs only",
        "backend_strategy": "none",
        "data_strategy": "minimal_metadata_only",
        "privacy_stack_requirements": "minimal collection",
        "safety_stack_requirements": "bounded exploration only",
        "legal_stack_requirements": "no external release without approval",
        "medical_stack_requirements": "not a medical pathway",
        "rejected_stack_options": ["premature stack commitment", "runtime stack"],
        "stack_rationale": "Default to a minimal metadata-only stack when the architecture type is unexpected.",
        "constraints": ["metadata-only"],
        "assumptions": ["scope remains unresolved"],
        "unknowns": ["stack type selection still pending"],
    }


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------


def _validate_optional_architecture_plan(project_architecture: Any) -> None:
    if is_dataclass(project_architecture) or isinstance(project_architecture, Mapping):
        validate_project_architecture_plan_v1(project_architecture)
    else:
        raise ValidationError("project_architecture_must_be_dataclass_or_mapping")



def _stack_decision_id(source_architecture_id: str, stack_decision_type: str, domain_family: str) -> str:
    return f"stack_{_slugify(source_architecture_id)}_{_slugify(stack_decision_type)}_{_slugify(domain_family)}"



def build_project_stack_decision_v1(project_architecture: Any, stack_decision_title: str | None = None) -> StackDecision:
    _validate_optional_architecture_plan(project_architecture)
    plan = _as_mapping(project_architecture)

    source_architecture_id = _safe_text(plan.get("architecture_id"))
    source_brief_id = _safe_text(plan.get("source_brief_id"))
    architecture_type = _safe_text(plan.get("architecture_type"))
    domain_family = _safe_text(plan.get("domain_family"))
    project_title = _safe_text(stack_decision_title) or _safe_text(plan.get("project_title"))
    stack_decision_type = _stack_decision_type_for_architecture_plan(plan)
    profile = _stack_profile_for_stack_type(stack_decision_type, plan)
    recommended_next_artifact = _recommended_next_artifact_for_stack_type(stack_decision_type)
    stack_decision_id = _stack_decision_id(source_architecture_id, stack_decision_type, domain_family)

    decision = StackDecision(
        stack_decision_id=stack_decision_id,
        stack_decision_type=stack_decision_type,
        source_architecture_id=source_architecture_id,
        source_brief_id=source_brief_id,
        project_title=project_title,
        architecture_type=architecture_type,
        domain_family=domain_family,
        meta_domains=_normalize_list(plan.get("meta_domains")),
        risk_labels=_normalize_list(plan.get("risk_labels")),
        local_cloud_strategy=_safe_text(plan.get("local_cloud_strategy")),
        prototype_allowed_level=_safe_text(plan.get("prototype_allowed_level")),
        primary_language=_safe_text(profile["primary_language"]),
        secondary_languages=_normalize_list(profile["secondary_languages"]),
        artifact_targets=_normalize_list(profile["artifact_targets"]),
        runtime_target=_safe_text(profile["runtime_target"]),
        storage_choice=_safe_text(profile["storage_choice"]),
        config_format=_safe_text(profile["config_format"]),
        documentation_format=_safe_text(profile["documentation_format"]),
        test_strategy=_safe_text(profile["test_strategy"]),
        validation_commands=_normalize_list(profile["validation_commands"]),
        dependency_policy=_safe_text(profile["dependency_policy"]),
        ui_strategy=_safe_text(profile["ui_strategy"]),
        backend_strategy=_safe_text(profile["backend_strategy"]),
        data_strategy=_safe_text(profile["data_strategy"]),
        privacy_stack_requirements=_safe_text(profile["privacy_stack_requirements"]),
        safety_stack_requirements=_safe_text(profile["safety_stack_requirements"]),
        legal_stack_requirements=_safe_text(profile["legal_stack_requirements"]),
        medical_stack_requirements=_safe_text(profile["medical_stack_requirements"]),
        rejected_stack_options=_normalize_list(profile["rejected_stack_options"]),
        stack_rationale=_safe_text(profile["stack_rationale"]),
        constraints=_dedupe_preserve([
            *(_normalize_list(profile.get("constraints", []))),
            *(_normalize_list(plan.get("boundary_requirements"))),
            "metadata-only",
            "no file writes",
        ]),
        assumptions=_dedupe_preserve([
            *(_normalize_list(profile.get("assumptions", []))),
            *(_normalize_list(plan.get("assumptions"))),
        ]),
        unknowns=_dedupe_preserve([
            *(_normalize_list(profile.get("unknowns", []))),
            *(_normalize_list(plan.get("unknowns"))),
        ]),
        recommended_next_artifact=recommended_next_artifact,
        file_manifest_required=_file_manifest_required_for_stack_type(stack_decision_type),
        code_generation_allowed=False,
        file_write_authority_granted=False,
        dependency_install_authority_granted=False,
        test_execution_authority_granted=False,
        public_claim_allowed=False,
        iss_internal_reference_allowed=True,
        learning_claimed=False,
        runtime_authority=False,
        writes_state=False,
        model_provider_used=False,
        safe_metadata={
            "source": "project_stack_decision_helper_v1",
            "source_architecture_id": source_architecture_id,
            "source_brief_id": source_brief_id,
            "stack_decision_type": stack_decision_type,
            "architecture_type": architecture_type,
            "domain_family": domain_family,
            "project_title": project_title,
            "recommended_next_artifact": recommended_next_artifact,
            "runtime_target": _safe_text(profile["runtime_target"]),
            "storage_choice": _safe_text(profile["storage_choice"]),
        },
    )
    validate_project_stack_decision_v1(decision)
    return decision



def build_project_stack_decision_from_architecture_v1(architecture_plan: Any) -> StackDecision:
    return build_project_stack_decision_v1(architecture_plan)


# ---------------------------------------------------------------------------
# Validation and summaries
# ---------------------------------------------------------------------------


def validate_project_stack_decision_v1(decision: Any) -> bool:
    if _contains_forbidden_fields(decision):
        raise ValidationError("forbidden_raw_fields_present")
    if _contains_forbidden_claim_marker(decision):
        raise ValidationError("forbidden_public_or_claim_language_present")
    if _contains_unsafe_deployment_marker(decision):
        raise ValidationError("unsafe_deployment_marker_present")
    if _contains_covert_tracking_marker(decision):
        raise ValidationError("covert_tracking_marker_present")
    if _contains_diagnosis_treatment_marker(decision):
        raise ValidationError("diagnosis_treatment_authority_marker_present")

    if is_dataclass(decision):
        normalized = decision
    elif isinstance(decision, Mapping):
        allowed = {field.name for field in StackDecision.__dataclass_fields__.values()}
        extra = set(str(key) for key in decision.keys()) - allowed
        if extra:
            raise ValidationError("unknown_fields_present")
        normalized = StackDecision(
            stack_decision_id=_safe_text(decision.get("stack_decision_id")),
            stack_decision_type=_safe_text(decision.get("stack_decision_type")),
            source_architecture_id=_safe_text(decision.get("source_architecture_id")),
            source_brief_id=_safe_text(decision.get("source_brief_id")),
            project_title=_safe_text(decision.get("project_title")),
            architecture_type=_safe_text(decision.get("architecture_type")),
            domain_family=_safe_text(decision.get("domain_family")),
            meta_domains=_normalize_list(decision.get("meta_domains")),
            risk_labels=_normalize_list(decision.get("risk_labels")),
            local_cloud_strategy=_safe_text(decision.get("local_cloud_strategy")),
            prototype_allowed_level=_safe_text(decision.get("prototype_allowed_level")),
            primary_language=_safe_text(decision.get("primary_language")),
            secondary_languages=_normalize_list(decision.get("secondary_languages")),
            artifact_targets=_normalize_list(decision.get("artifact_targets")),
            runtime_target=_safe_text(decision.get("runtime_target")),
            storage_choice=_safe_text(decision.get("storage_choice")),
            config_format=_safe_text(decision.get("config_format")),
            documentation_format=_safe_text(decision.get("documentation_format")),
            test_strategy=_safe_text(decision.get("test_strategy")),
            validation_commands=_normalize_list(decision.get("validation_commands")),
            dependency_policy=_safe_text(decision.get("dependency_policy")),
            ui_strategy=_safe_text(decision.get("ui_strategy")),
            backend_strategy=_safe_text(decision.get("backend_strategy")),
            data_strategy=_safe_text(decision.get("data_strategy")),
            privacy_stack_requirements=_safe_text(decision.get("privacy_stack_requirements")),
            safety_stack_requirements=_safe_text(decision.get("safety_stack_requirements")),
            legal_stack_requirements=_safe_text(decision.get("legal_stack_requirements")),
            medical_stack_requirements=_safe_text(decision.get("medical_stack_requirements")),
            rejected_stack_options=_normalize_list(decision.get("rejected_stack_options")),
            stack_rationale=_safe_text(decision.get("stack_rationale")),
            constraints=_normalize_list(decision.get("constraints")),
            assumptions=_normalize_list(decision.get("assumptions")),
            unknowns=_normalize_list(decision.get("unknowns")),
            recommended_next_artifact=_safe_text(decision.get("recommended_next_artifact")),
            file_manifest_required=bool(decision.get("file_manifest_required")),
            code_generation_allowed=bool(decision.get("code_generation_allowed")),
            file_write_authority_granted=bool(decision.get("file_write_authority_granted")),
            dependency_install_authority_granted=bool(decision.get("dependency_install_authority_granted")),
            test_execution_authority_granted=bool(decision.get("test_execution_authority_granted")),
            public_claim_allowed=bool(decision.get("public_claim_allowed")),
            iss_internal_reference_allowed=bool(decision.get("iss_internal_reference_allowed")),
            learning_claimed=bool(decision.get("learning_claimed")),
            runtime_authority=bool(decision.get("runtime_authority")),
            writes_state=bool(decision.get("writes_state")),
            model_provider_used=bool(decision.get("model_provider_used")),
            safe_metadata=dict(decision.get("safe_metadata") or {}),
        )
    else:
        raise ValidationError("stack_decision_must_be_dataclass_or_mapping")

    if not normalized.stack_decision_id:
        raise ValidationError("stack_decision_id_required")
    if normalized.stack_decision_type not in ALLOWED_STACK_DECISION_TYPES_V1:
        raise ValidationError("unknown_stack_decision_type")
    if not normalized.source_architecture_id:
        raise ValidationError("source_architecture_id_required")
    if not normalized.source_brief_id:
        raise ValidationError("source_brief_id_required")
    if not normalized.project_title:
        raise ValidationError("project_title_required")
    if normalized.recommended_next_artifact not in ALLOWED_RECOMMENDED_NEXT_ARTIFACTS_V1:
        raise ValidationError("unknown_recommended_next_artifact")
    if normalized.runtime_target not in ALLOWED_RUNTIME_TARGETS_V1:
        raise ValidationError("unknown_runtime_target")
    if normalized.storage_choice not in ALLOWED_STORAGE_CHOICES_V1:
        raise ValidationError("unknown_storage_choice")
    if normalized.dependency_policy not in ALLOWED_DEPENDENCY_POLICIES_V1:
        raise ValidationError("unknown_dependency_policy")
    if normalized.prototype_allowed_level not in {"none", "conceptual_only", "high_level_only", "sandbox_only", "requires_owner_approval"}:
        raise ValidationError("unknown_prototype_allowed_level")

    for field_name in (
        "file_manifest_required",
        "code_generation_allowed",
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
    if normalized.code_generation_allowed:
        raise ValidationError("code_generation_allowed_must_be_false")

    for field_name in (
        "meta_domains",
        "risk_labels",
        "secondary_languages",
        "artifact_targets",
        "validation_commands",
        "rejected_stack_options",
        "constraints",
        "assumptions",
        "unknowns",
    ):
        value = getattr(normalized, field_name)
        if not isinstance(value, list):
            raise ValidationError(f"{field_name}_must_be_list")
        if not value:
            raise ValidationError(f"{field_name}_required")

    for field_name in (
        "primary_language",
        "local_cloud_strategy",
        "prototype_allowed_level",
        "storage_choice",
        "config_format",
        "documentation_format",
        "test_strategy",
        "dependency_policy",
        "ui_strategy",
        "backend_strategy",
        "data_strategy",
        "privacy_stack_requirements",
        "safety_stack_requirements",
        "legal_stack_requirements",
        "medical_stack_requirements",
        "stack_rationale",
    ):
        if not _safe_text(getattr(normalized, field_name)):
            raise ValidationError(f"{field_name}_required")

    if any(target not in ALLOWED_ARTIFACT_TARGETS_V1 for target in normalized.artifact_targets):
        raise ValidationError("unknown_artifact_target")

    blob = _list_blob(normalized.artifact_targets)
    if normalized.stack_decision_type == "privacy_sensitive_local_stack" and not all(
        target in blob for target in ("python_package", "python_tests", "markdown_docs")
    ):
        raise ValidationError("privacy_stack_requires_python_artifacts")
    if normalized.stack_decision_type == "medical_software_pathway_stack" and not all(
        term in _list_blob([normalized.medical_stack_requirements, normalized.safety_stack_requirements, normalized.legal_stack_requirements])
        for term in ("clinical", "regulatory", "safety")
    ):
        raise ValidationError("medical_stack_requires_validation_controls")
    if normalized.stack_decision_type == "materials_research_stack" and not all(
        term in _list_blob([normalized.test_strategy, normalized.safety_stack_requirements])
        for term in ("validation", "uncertainty")
    ):
        raise ValidationError("materials_stack_requires_validation_language")
    if normalized.stack_decision_type == "ai_system_research_stack" and not all(
        term in _list_blob([normalized.ui_strategy, normalized.safety_stack_requirements, normalized.test_strategy])
        for term in ("governance", "evaluation", "safety")
    ):
        raise ValidationError("ai_stack_requires_governance_language")
    if normalized.stack_decision_type == "conceptual_research_docs_stack" and normalized.runtime_target != "none_docs_only":
        raise ValidationError("conceptual_stack_must_be_docs_only")
    if normalized.stack_decision_type == "unknown_domain_minimal_stack" and not normalized.recommended_next_artifact in {"clarifying_questions", "evidence_map"}:
        raise ValidationError("unknown_stack_requires_clarification_or_evidence_next_artifact")

    return True



def summarize_project_stack_decision_v1(decision: Any) -> StackDecisionSummary:
    if not isinstance(decision, StackDecision):
        validate_project_stack_decision_v1(decision)
        if isinstance(decision, Mapping):
            decision = StackDecision(
                stack_decision_id=_safe_text(decision.get("stack_decision_id")),
                stack_decision_type=_safe_text(decision.get("stack_decision_type")),
                source_architecture_id=_safe_text(decision.get("source_architecture_id")),
                source_brief_id=_safe_text(decision.get("source_brief_id")),
                project_title=_safe_text(decision.get("project_title")),
                architecture_type=_safe_text(decision.get("architecture_type")),
                domain_family=_safe_text(decision.get("domain_family")),
                meta_domains=_normalize_list(decision.get("meta_domains")),
                risk_labels=_normalize_list(decision.get("risk_labels")),
                local_cloud_strategy=_safe_text(decision.get("local_cloud_strategy")),
                prototype_allowed_level=_safe_text(decision.get("prototype_allowed_level")),
                primary_language=_safe_text(decision.get("primary_language")),
                secondary_languages=_normalize_list(decision.get("secondary_languages")),
                artifact_targets=_normalize_list(decision.get("artifact_targets")),
                runtime_target=_safe_text(decision.get("runtime_target")),
                storage_choice=_safe_text(decision.get("storage_choice")),
                config_format=_safe_text(decision.get("config_format")),
                documentation_format=_safe_text(decision.get("documentation_format")),
                test_strategy=_safe_text(decision.get("test_strategy")),
                validation_commands=_normalize_list(decision.get("validation_commands")),
                dependency_policy=_safe_text(decision.get("dependency_policy")),
                ui_strategy=_safe_text(decision.get("ui_strategy")),
                backend_strategy=_safe_text(decision.get("backend_strategy")),
                data_strategy=_safe_text(decision.get("data_strategy")),
                privacy_stack_requirements=_safe_text(decision.get("privacy_stack_requirements")),
                safety_stack_requirements=_safe_text(decision.get("safety_stack_requirements")),
                legal_stack_requirements=_safe_text(decision.get("legal_stack_requirements")),
                medical_stack_requirements=_safe_text(decision.get("medical_stack_requirements")),
                rejected_stack_options=_normalize_list(decision.get("rejected_stack_options")),
                stack_rationale=_safe_text(decision.get("stack_rationale")),
                constraints=_normalize_list(decision.get("constraints")),
                assumptions=_normalize_list(decision.get("assumptions")),
                unknowns=_normalize_list(decision.get("unknowns")),
                recommended_next_artifact=_safe_text(decision.get("recommended_next_artifact")),
                file_manifest_required=bool(decision.get("file_manifest_required")),
                code_generation_allowed=bool(decision.get("code_generation_allowed")),
                file_write_authority_granted=bool(decision.get("file_write_authority_granted")),
                dependency_install_authority_granted=bool(decision.get("dependency_install_authority_granted")),
                test_execution_authority_granted=bool(decision.get("test_execution_authority_granted")),
                public_claim_allowed=bool(decision.get("public_claim_allowed")),
                iss_internal_reference_allowed=bool(decision.get("iss_internal_reference_allowed")),
                learning_claimed=bool(decision.get("learning_claimed")),
                runtime_authority=bool(decision.get("runtime_authority")),
                writes_state=bool(decision.get("writes_state")),
                model_provider_used=bool(decision.get("model_provider_used")),
                safe_metadata=dict(decision.get("safe_metadata") or {}),
            )
    return StackDecisionSummary(
        summary_type=SUMMARY_TYPE_V1,
        stack_decision_id=decision.stack_decision_id,
        stack_decision_type=decision.stack_decision_type,
        project_title=decision.project_title,
        primary_language=decision.primary_language,
        runtime_target=decision.runtime_target,
        recommended_next_artifact=decision.recommended_next_artifact,
        stack_rationale=decision.stack_rationale,
        artifact_target_count=len(decision.artifact_targets),
        validation_command_count=len(decision.validation_commands),
    )



def to_project_stack_decision_json_safe_v1(value: Any) -> Any:
    return _json_safe(value)


# ---------------------------------------------------------------------------
# Seed examples
# ---------------------------------------------------------------------------


def build_initial_project_stack_decision_examples_v1() -> tuple[StackDecision, ...]:
    examples: list[StackDecision] = []
    for architecture in build_initial_project_architecture_examples_v1():
        examples.append(build_project_stack_decision_from_architecture_v1(architecture))
    return tuple(examples)


# Backwards-compatible aliases.
build_project_stack_decision = build_project_stack_decision_v1
build_project_stack_decision_from_architecture = build_project_stack_decision_from_architecture_v1
validate_project_stack_decision = validate_project_stack_decision_v1
summarize_project_stack_decision = summarize_project_stack_decision_v1
to_project_stack_decision_json_safe = to_project_stack_decision_json_safe_v1
build_initial_project_stack_decision_examples = build_initial_project_stack_decision_examples_v1
