"""Metadata-only project architecture planner v1.

This module converts a validated project brief into a safe architecture plan.

It is pure, deterministic, import-safe, and fail-closed.
No model/provider/search/advisor calls. No network. No I/O. No state writes.
No chat routing. No runtime behavior changes.
"""

from __future__ import annotations

import copy
import re
from dataclasses import asdict, dataclass, is_dataclass
from typing import Any, Iterable, Mapping

from weslr.project_brief_builder import ProjectBrief, validate_project_brief_v1

HELPER_TYPE_V1 = "project_architecture_planner_helper_v1"
ARCHITECTURE_PLAN_TYPE_V1 = "project_architecture_plan_v1"
SUMMARY_TYPE_V1 = "project_architecture_plan_summary_v1"

ALLOWED_ARCHITECTURE_TYPES_V1 = {
    "local_first_research_architecture",
    "sandbox_prototype_architecture",
    "software_product_architecture",
    "privacy_sensitive_assistive_architecture",
    "medical_software_pathway_architecture",
    "industrial_automation_architecture",
    "materials_research_architecture",
    "ai_system_architecture",
    "conceptual_research_architecture",
    "unknown_domain_architecture",
}

ALLOWED_LOCAL_CLOUD_STRATEGIES_V1 = {
    "local_first",
    "local_only",
    "cloud_optional_later",
    "cloud_required_later",
    "unknown_pending_requirements",
}

ALLOWED_PROTOTYPE_LEVELS_V1 = {
    "none",
    "conceptual_only",
    "high_level_only",
    "sandbox_only",
    "requires_owner_approval",
}

ALLOWED_NEXT_ARTIFACTS_V1 = {
    "stack_decision",
    "file_manifest",
    "evidence_map",
    "boundary_review",
    "validation_plan",
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
    "consciousness language",
    "sentience claim",
    "turing claim",
    "official turing",
    "turing test",
    "certification claim",
)

CLAIM_BASE_TERMS_V1 = {"agi", "consciousness", "sentience", "turing", "certification"}
CLAIM_QUALIFIERS_V1 = {"official", "certification", "certified", "public", "readiness"}
UNSAFE_DEPLOYMENT_TERMS_V1 = {"deploy", "deployment", "evade", "bypass", "surveillance"}
UNSAFE_DEPLOYMENT_PHRASES_V1 = {"covert rollout", "unsafe deployment", "deployment before review"}
COVERT_TRACKING_MARKERS_V1 = {"covert tracking", "tracking implementation", "tracking pipeline", "hidden tracking", "surveillance"}
DIAGNOSIS_TREATMENT_TERMS_V1 = {"diagnosis", "diagnose", "diagnostic", "treatment", "treat", "prescribe", "prescription"}


class ValidationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class ArchitecturePlan:
    architecture_id: str
    architecture_type: str
    source_brief_id: str
    project_title: str
    project_stage: str
    domain_family: str
    meta_domains: list[str]
    risk_labels: list[str]
    boundary_requirements: list[str]
    architecture_goals: list[str]
    non_goals: list[str]
    architecture_options: list[str]
    selected_architecture: str
    component_map: list[str]
    data_flow: list[str]
    control_flow: list[str]
    interface_surfaces: list[str]
    storage_strategy: list[str]
    local_cloud_strategy: str
    privacy_controls: list[str]
    safety_controls: list[str]
    legal_controls: list[str]
    medical_claim_controls: list[str]
    validation_points: list[str]
    failure_modes: list[str]
    assumptions: list[str]
    unknowns: list[str]
    constraints: list[str]
    evidence_requirements: list[str]
    recommended_next_artifact: str
    stack_decision_required: bool
    file_manifest_required: bool
    code_generation_allowed: bool
    file_write_authority_granted: bool
    prototype_allowed_level: str
    public_claim_allowed: bool
    iss_internal_reference_allowed: bool
    learning_claimed: bool
    runtime_authority: bool
    writes_state: bool
    model_provider_used: bool
    safe_metadata: dict[str, Any] | None = None


@dataclass(frozen=True, slots=True)
class ArchitecturePlanSummary:
    summary_type: str
    architecture_id: str
    architecture_type: str
    project_stage: str
    selected_architecture: str
    recommended_next_artifact: str
    domain_family: str
    architecture_goal_count: int
    component_count: int
    validation_point_count: int


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
    raise ValidationError("architecture_plan_must_be_dataclass_or_mapping")



def _slugify(value: str) -> str:
    text = _normalize_text(value)
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return text.strip("_") or "architecture"



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



def _contains_forbidden_claim_marker(value: Any, path: str = "") -> bool:
    if is_dataclass(value):
        value = asdict(value)
    if isinstance(value, Mapping):
        for key, item in value.items():
            key_text = _safe_text(key).lower()
            if key_text == "non_goals":
                continue
            next_path = f"{path}.{key_text}" if path else key_text
            if _contains_forbidden_claim_marker(item, next_path):
                return True
        return False
    if isinstance(value, (list, tuple, set)):
        return any(_contains_forbidden_claim_marker(item, path) for item in value)
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



def _contains_negated_marker(value: str, marker: str) -> bool:
    text = _normalize_text(value)
    for prefix in ("no ", "not ", "without ", "never "):
        if f"{prefix}{marker}" in text:
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


# ---------------------------------------------------------------------------
# Brief context routing
# ---------------------------------------------------------------------------


def _architecture_type_for_brief(brief: Mapping[str, Any]) -> str:
    brief_type = _safe_text(brief.get("brief_type"))
    project_stage = _safe_text(brief.get("project_stage"))
    if brief_type == "privacy_sensitive_research_brief":
        return "privacy_sensitive_assistive_architecture"
    if brief_type == "medical_software_pathway_brief":
        return "medical_software_pathway_architecture"
    if brief_type == "materials_discovery_project_brief":
        return "materials_research_architecture"
    if brief_type == "ai_system_project_brief":
        return "ai_system_architecture"
    if brief_type == "conceptual_research_brief":
        return "conceptual_research_architecture"
    if brief_type == "industrial_automation_project_brief":
        return "industrial_automation_architecture"
    if brief_type == "software_product_brief":
        return "software_product_architecture"
    if brief_type == "unknown_domain_project_brief":
        return "unknown_domain_architecture"
    if brief_type == "prototype_project_brief":
        return "sandbox_prototype_architecture"
    if brief_type == "research_project_brief":
        return "local_first_research_architecture"
    if project_stage == "concept_only":
        return "local_first_research_architecture"
    return "local_first_research_architecture"



def _local_cloud_strategy_for_architecture_type(architecture_type: str) -> str:
    return {
        "privacy_sensitive_assistive_architecture": "local_first",
        "medical_software_pathway_architecture": "unknown_pending_requirements",
        "materials_research_architecture": "cloud_optional_later",
        "ai_system_architecture": "cloud_optional_later",
        "industrial_automation_architecture": "local_only",
        "software_product_architecture": "cloud_optional_later",
        "conceptual_research_architecture": "local_only",
        "unknown_domain_architecture": "unknown_pending_requirements",
        "sandbox_prototype_architecture": "local_only",
        "local_first_research_architecture": "local_first",
    }.get(architecture_type, "unknown_pending_requirements")



def _prototype_allowed_level_for_architecture_type(architecture_type: str) -> str:
    return {
        "privacy_sensitive_assistive_architecture": "high_level_only",
        "medical_software_pathway_architecture": "high_level_only",
        "materials_research_architecture": "high_level_only",
        "ai_system_architecture": "sandbox_only",
        "industrial_automation_architecture": "sandbox_only",
        "software_product_architecture": "sandbox_only",
        "conceptual_research_architecture": "conceptual_only",
        "unknown_domain_architecture": "conceptual_only",
        "sandbox_prototype_architecture": "sandbox_only",
        "local_first_research_architecture": "high_level_only",
    }.get(architecture_type, "conceptual_only")



def _recommended_next_artifact_for_architecture_type(architecture_type: str, project_stage: str) -> str:
    if architecture_type in {"privacy_sensitive_assistive_architecture", "medical_software_pathway_architecture", "materials_research_architecture"}:
        return "evidence_map"
    if architecture_type == "conceptual_research_architecture":
        return "clarifying_questions"
    if architecture_type == "unknown_domain_architecture":
        return "clarifying_questions"
    if architecture_type == "industrial_automation_architecture":
        return "validation_plan"
    if architecture_type == "software_product_architecture":
        return "stack_decision"
    if architecture_type == "ai_system_architecture":
        return "validation_plan"
    if architecture_type in {"sandbox_prototype_architecture", "local_first_research_architecture"}:
        return "stack_decision" if project_stage != "concept_only" else "clarifying_questions"
    return "stack_decision"



def _architecture_profile_for_brief(brief: Mapping[str, Any], architecture_type: str) -> dict[str, Any]:
    brief_type = _safe_text(brief.get("brief_type"))
    project_stage = _safe_text(brief.get("project_stage"))
    domain_family = _safe_text(brief.get("domain_family"))
    source_goal_blob = _normalize_list(brief.get("goals"))
    source_constraints = _normalize_list(brief.get("constraints"))
    source_evidence = _normalize_list(brief.get("evidence_requirements"))
    source_assumptions = _normalize_list(brief.get("assumptions"))
    source_unknowns = _normalize_list(brief.get("unknowns"))
    source_risks = _normalize_list(brief.get("risk_labels"))
    source_boundary = _normalize_list(brief.get("boundary_requirements"))

    if architecture_type == "privacy_sensitive_assistive_architecture":
        return {
            "architecture_goals": [
                "stay local-first",
                "support consent-based assistive sensing",
                "preserve user control and auditability",
                "prepare a validation harness before reliance",
            ],
            "non_goals": [
                "unconsented sensing",
                "unsupported health guidance",
                "direct intervention recommendation",
                "unbounded rollout planning",
            ],
            "architecture_options": [
                "local-first assistive sensing with privacy audit",
                "manual-first fallback with derived events only",
                "hybrid later only after explicit owner approval",
            ],
            "selected_architecture": "local-first assistive sensing with local storage, privacy audit, reminder/rule engine, and validation harness",
            "component_map": [
                "signal/source intake",
                "preprocessing",
                "event/routine inference placeholder",
                "reminder/rule engine",
                "local storage",
                "privacy/audit layer",
                "dashboard/interface surface",
                "validation harness",
            ],
            "data_flow": [
                "signal/source intake -> preprocessing",
                "preprocessing -> event/routine inference placeholder",
                "event/routine inference placeholder -> reminder/rule engine",
                "reminder/rule engine -> local storage",
                "local storage -> dashboard/interface surface",
            ],
            "control_flow": [
                "consent check before any sensing",
                "user review before reminder release",
                "local rule evaluation only",
                "validation gate before reliance",
            ],
            "interface_surfaces": ["local dashboard", "consent settings", "audit log", "manual override"],
            "storage_strategy": ["local-only event log", "derived features only", "no raw capture by default"],
            "local_cloud_strategy": _local_cloud_strategy_for_architecture_type(architecture_type),
            "privacy_controls": ["consent", "data minimization", "local-first storage", "user control", "auditability", "no covert tracking"],
            "safety_controls": ["validation before reliance", "bounded reminders only", "no diagnosis authority", "no treatment recommendation"],
            "legal_controls": ["lawfulness review", "household policy alignment", "affected-person consent review"],
            "medical_claim_controls": ["no diagnosis authority", "no treatment recommendation", "support-only scope"],
            "validation_points": ["consent", "privacy boundary", "failure modes", "user override"],
            "failure_modes": ["false inference", "missed event", "unexpected alert", "privacy boundary drift"],
        }
    if architecture_type == "medical_software_pathway_architecture":
        return {
            "architecture_goals": [
                "preserve a regulated support-only scope",
                "capture clinical and regulatory validation points",
                "keep safety review ahead of implementation decisions",
            ],
            "non_goals": [
                "unsupported health guidance",
                "direct intervention recommendation",
                "release before review",
            ],
            "architecture_options": [
                "evidence-led pathway with clinical review boundary",
                "support-only workflow with regulated validation checkpoints",
                "controlled internal planning architecture without external release statements",
            ],
            "selected_architecture": "medical regulated pathway architecture with evidence registry, clinical review boundary, and safety validation",
            "component_map": [
                "intake and scope definition",
                "clinical evidence registry",
                "regulatory review boundary",
                "safety validation harness",
                "bounded interface surface",
            ],
            "data_flow": [
                "intake -> scope definition",
                "scope definition -> evidence registry",
                "evidence registry -> clinical review boundary",
                "clinical review boundary -> safety validation harness",
            ],
            "control_flow": [
                "clinical review before any support statement",
                "regulatory check before implementation planning",
                "safety validation before reliance",
            ],
            "interface_surfaces": ["evidence dashboard", "review checklist", "scope boundary view"],
            "storage_strategy": ["bounded evidence registry", "local metadata store", "no raw clinical data by default"],
            "local_cloud_strategy": _local_cloud_strategy_for_architecture_type(architecture_type),
            "privacy_controls": ["bounded data handling", "least privilege", "auditability"],
            "safety_controls": ["safety review", "clinical validation", "regulatory validation"],
            "legal_controls": ["regulated pathway review", "operator approval for release", "policy compliance review"],
            "medical_claim_controls": ["no diagnosis authority", "no treatment recommendation", "clinical support only", "regulatory review required"],
            "validation_points": ["clinical validation", "regulatory validation", "safety validation"],
            "failure_modes": ["unsupported clinical scope", "regulatory mismatch", "safety gap"],
        }
    if architecture_type == "materials_research_architecture":
        return {
            "architecture_goals": ["map a research path", "handle uncertainty explicitly", "prepare evidence and validation criteria"],
            "non_goals": ["production readiness risk", "unsupported feasibility assertion", "short-circuiting evidence work"],
            "architecture_options": ["evidence-led literature architecture", "candidate-property exploration path", "experimental-validation-first path"],
            "selected_architecture": "evidence-led materials research architecture with literature ingestion, candidate representation, uncertainty handling, and experimental validation placeholder",
            "component_map": ["literature ingestion", "candidate representation", "uncertainty ledger", "validation criteria", "experimental validation placeholder"],
            "data_flow": ["literature -> candidate representation", "candidate representation -> uncertainty ledger", "uncertainty ledger -> validation criteria", "validation criteria -> experimental placeholder"],
            "control_flow": ["evidence review before feasibility assertions", "validation criteria before selection"],
            "interface_surfaces": ["research notes", "candidate comparison view", "validation checklist"],
            "storage_strategy": ["local metadata store", "citation/index map", "no raw private data by default"],
            "local_cloud_strategy": _local_cloud_strategy_for_architecture_type(architecture_type),
            "privacy_controls": ["bounded data collection", "citation hygiene"],
            "safety_controls": ["uncertainty handling", "validation before reliance"],
            "legal_controls": ["no external release without approval"],
            "medical_claim_controls": ["not a medical pathway"],
            "validation_points": ["technical literature", "experimental validation", "uncertainty review"],
            "failure_modes": ["unsupported feasibility assertion", "missing validation criteria", "uncertainty ignored"],
        }
    if architecture_type == "ai_system_architecture":
        return {
            "architecture_goals": ["define bounded cognition/planning components", "separate governance from execution", "prepare evaluation and trace surfaces"],
            "non_goals": ["AGI language", "consciousness language", "benchmark publication"],
            "architecture_options": ["governance-first bounded system", "offline analysis with manual review", "split-service architecture with evaluation harness"],
            "selected_architecture": "governance-first AI system architecture with bounded planning components, evaluation harness, trace/report surface, and safety boundary",
            "component_map": ["planning component", "governance boundary", "evaluation harness", "trace/report surface", "safety gate"],
            "data_flow": ["inputs -> planning component", "planning component -> governance boundary", "governance boundary -> evaluation harness", "evaluation harness -> trace/report surface"],
            "control_flow": ["governance review before release", "evaluation before rollout", "trace/report before iteration"],
            "interface_surfaces": ["governance view", "evaluation dashboard", "trace/report surface"],
            "storage_strategy": ["bounded metadata store", "trace retention controls", "no raw private data by default"],
            "local_cloud_strategy": _local_cloud_strategy_for_architecture_type(architecture_type),
            "privacy_controls": ["bounded data handling", "trace minimization"],
            "safety_controls": ["governance review", "evaluation harness", "safety review", "rollback path"],
            "legal_controls": ["operator approval for release", "no official statements"],
            "medical_claim_controls": ["not a medical pathway"],
            "validation_points": ["architecture review", "governance review", "evaluation plan"],
            "failure_modes": ["governance drift", "evaluation gap", "trace loss"],
        }
    if architecture_type == "industrial_automation_architecture":
        return {
            "architecture_goals": ["define a safe control boundary", "normalize configuration inputs", "prepare validation/reporting"],
            "non_goals": ["unsafe control commands", "hidden control changes", "unbounded implementation detail"],
            "architecture_options": ["local control boundary with validation", "operator-reviewed configuration path", "sandboxed automation planning path"],
            "selected_architecture": "device-abstraction industrial automation architecture with config normalization, safety boundary, validation/reporting, and controlled operator review",
            "component_map": ["device/source abstraction", "config normalization", "safety boundary", "validation/reporting"],
            "data_flow": ["device/source -> config normalization", "config normalization -> safety boundary", "safety boundary -> validation/reporting"],
            "control_flow": ["operator review before control changes", "safety checks before use", "reporting after validation"],
            "interface_surfaces": ["configuration view", "safety review view", "validation report"],
            "storage_strategy": ["local config metadata", "bounded logs", "no raw private data by default"],
            "local_cloud_strategy": _local_cloud_strategy_for_architecture_type(architecture_type),
            "privacy_controls": ["bounded logs", "access control"],
            "safety_controls": ["safety boundary", "validation reporting", "operator confirmation"],
            "legal_controls": ["owner approval", "policy alignment"],
            "medical_claim_controls": ["not a medical pathway"],
            "validation_points": ["configuration review", "safety review", "failure-mode review"],
            "failure_modes": ["unsafe control command", "config mismatch", "safety boundary drift"],
        }
    if architecture_type == "software_product_architecture":
        return {
            "architecture_goals": ["clarify user flow", "shape interface surfaces", "prepare acceptance criteria"],
            "non_goals": ["launch without validation", "unsupported assertions", "unclear scope"],
            "architecture_options": ["interface-first product architecture", "service-backed product architecture", "bounded prototype architecture with release gate"],
            "selected_architecture": "user-flow-first software product architecture with interface surface, service placeholder, storage placeholder, and acceptance criteria",
            "component_map": ["user flow", "interface surface", "service placeholder", "storage placeholder", "acceptance criteria"],
            "data_flow": ["user flow -> interface surface", "interface surface -> service placeholder", "service placeholder -> storage placeholder"],
            "control_flow": ["acceptance criteria before release", "review before stack decision", "bounded rollout only"],
            "interface_surfaces": ["product UI", "owner review view", "acceptance checklist"],
            "storage_strategy": ["placeholder storage design", "bounded metadata", "no raw private data by default"],
            "local_cloud_strategy": _local_cloud_strategy_for_architecture_type(architecture_type),
            "privacy_controls": ["bounded data collection", "user consent where needed"],
            "safety_controls": ["release review", "rollback path", "validation before rollout"],
            "legal_controls": ["no external release without approval", "support docs as needed"],
            "medical_claim_controls": ["not a medical pathway"],
            "validation_points": ["acceptance criteria", "stack decision", "release review"],
            "failure_modes": ["scope drift", "acceptance mismatch", "release gap"],
        }
    if architecture_type == "conceptual_research_architecture":
        return {
            "architecture_goals": ["map definitions", "map claims", "organize evidence and uncertainty"],
            "non_goals": ["consciousness language", "sentience claim", "benchmark publication"],
            "architecture_options": ["definition map first", "evidence/source matrix first", "uncertainty-led comparison path"],
            "selected_architecture": "conceptual research architecture with definition map, claim map, evidence/source map, comparison matrix, and uncertainty ledger",
            "component_map": ["definition map", "claim map", "evidence/source map", "comparison matrix", "uncertainty ledger"],
            "data_flow": ["definitions -> claim map", "claims -> evidence/source map", "evidence/source map -> comparison matrix", "comparison matrix -> uncertainty ledger"],
            "control_flow": ["source check before stronger claim", "uncertainty review before synthesis"],
            "interface_surfaces": ["concept map", "claim comparison view", "uncertainty ledger"],
            "storage_strategy": ["local notes", "citation map", "no raw private data by default"],
            "local_cloud_strategy": _local_cloud_strategy_for_architecture_type(architecture_type),
            "privacy_controls": ["bounded notes", "source hygiene"],
            "safety_controls": ["uncertainty handling", "claim discipline"],
            "legal_controls": ["no external release without approval"],
            "medical_claim_controls": ["not a medical pathway"],
            "validation_points": ["definition review", "claim review", "evidence/source review"],
            "failure_modes": ["definition drift", "claim overreach", "uncertainty ignored"],
        }
    if architecture_type == "unknown_domain_architecture":
        return {
            "architecture_goals": ["stay clarification-first", "avoid pretending domain knowledge", "prepare evidence-first next step"],
            "non_goals": ["pretend certainty", "overstate capability", "skip clarification"],
            "architecture_options": ["clarification-first scaffold", "evidence-first exploration path", "conceptual placeholder architecture"],
            "selected_architecture": "clarification-first architecture scaffold with evidence tracking and bounded question flow",
            "component_map": ["clarification intake", "evidence tracker", "bounded question set"],
            "data_flow": ["clarification intake -> evidence tracker", "evidence tracker -> bounded question set"],
            "control_flow": ["clarify before build", "evidence before stronger planning"],
            "interface_surfaces": ["clarifying questions", "evidence checklist"],
            "storage_strategy": ["local metadata", "no raw private data by default"],
            "local_cloud_strategy": _local_cloud_strategy_for_architecture_type(architecture_type),
            "privacy_controls": ["bounded collection", "minimal retention"],
            "safety_controls": ["no unsafe assumptions", "bounded exploration only"],
            "legal_controls": ["no legal certainty assertions"],
            "medical_claim_controls": ["not a medical pathway"],
            "validation_points": ["clarification review", "evidence review"],
            "failure_modes": ["domain drift", "assumption creep", "evidence gap"],
        }
    return {
        "architecture_goals": ["translate the brief into a bounded architecture"],
        "non_goals": ["external release making", "unbounded implementation"],
        "architecture_options": ["bounded planning architecture"],
        "selected_architecture": "bounded planning architecture",
        "component_map": ["brief intake", "architecture sketch"],
        "data_flow": ["brief -> architecture sketch"],
        "control_flow": ["review before selection"],
        "interface_surfaces": ["architecture sketch"],
        "storage_strategy": ["local metadata"],
        "local_cloud_strategy": _local_cloud_strategy_for_architecture_type(architecture_type),
        "privacy_controls": ["bounded data collection"],
        "safety_controls": ["validation before reliance"],
        "legal_controls": ["no external release without approval"],
        "medical_claim_controls": ["not a medical pathway"],
        "validation_points": ["brief review"],
        "failure_modes": ["scope drift"],
    }


# ---------------------------------------------------------------------------
# Builder helpers
# ---------------------------------------------------------------------------


def _validate_optional_brief(project_brief: Any) -> None:
    if is_dataclass(project_brief) or isinstance(project_brief, Mapping):
        validate_project_brief_v1(project_brief)
    else:
        raise ValidationError("project_brief_must_be_dataclass_or_mapping")



def _architecture_id(source_brief_id: str, architecture_type: str, domain_family: str) -> str:
    return f"architecture_{_slugify(source_brief_id)}_{_slugify(architecture_type)}_{_slugify(domain_family)}"



def build_project_architecture_plan_v1(project_brief: Any, architecture_title: str | None = None) -> ArchitecturePlan:
    _validate_optional_brief(project_brief)
    brief = _as_mapping(project_brief)

    source_brief_id = _safe_text(brief.get("brief_id"))
    architecture_type = _architecture_type_for_brief(brief)
    selected_stage = _safe_text(brief.get("project_stage"))
    domain_family = _safe_text(brief.get("domain_family"))
    architecture_id = _architecture_id(source_brief_id, architecture_type, domain_family)

    profile = _architecture_profile_for_brief(brief, architecture_type)
    recommended_next_artifact = _recommended_next_artifact_for_architecture_type(architecture_type, selected_stage)
    local_cloud_strategy = profile.get("local_cloud_strategy") or _local_cloud_strategy_for_architecture_type(architecture_type)
    prototype_allowed_level = _prototype_allowed_level_for_architecture_type(architecture_type)
    source_constraints = _normalize_list(brief.get("constraints"))
    source_unknowns = _normalize_list(brief.get("unknowns"))
    source_evidence = _normalize_list(brief.get("evidence_requirements"))
    source_boundary = _normalize_list(brief.get("boundary_requirements"))

    stack_decision_required = architecture_type not in {"conceptual_research_architecture", "unknown_domain_architecture"}
    file_manifest_required = architecture_type in {
        "software_product_architecture",
        "industrial_automation_architecture",
        "ai_system_architecture",
        "medical_software_pathway_architecture",
        "privacy_sensitive_assistive_architecture",
        "materials_research_architecture",
    }
    code_generation_allowed = selected_stage != "concept_only" and architecture_type not in {"conceptual_research_architecture", "unknown_domain_architecture"}

    architecture = ArchitecturePlan(
        architecture_id=architecture_id,
        architecture_type=architecture_type,
        source_brief_id=source_brief_id,
        project_title=_safe_text(architecture_title) or _safe_text(brief.get("project_title")),
        project_stage=selected_stage,
        domain_family=domain_family,
        meta_domains=_normalize_list(brief.get("meta_domains")),
        risk_labels=_normalize_list(brief.get("risk_labels")),
        boundary_requirements=_normalize_list(brief.get("boundary_requirements")),
        architecture_goals=_normalize_list(profile["architecture_goals"]),
        non_goals=_normalize_list(profile["non_goals"]),
        architecture_options=_normalize_list(profile["architecture_options"]),
        selected_architecture=_safe_text(profile["selected_architecture"]),
        component_map=_normalize_list(profile["component_map"]),
        data_flow=_normalize_list(profile["data_flow"]),
        control_flow=_normalize_list(profile["control_flow"]),
        interface_surfaces=_normalize_list(profile["interface_surfaces"]),
        storage_strategy=_normalize_list(profile["storage_strategy"]),
        local_cloud_strategy=_safe_text(local_cloud_strategy),
        privacy_controls=_normalize_list(profile["privacy_controls"]),
        safety_controls=_normalize_list(profile["safety_controls"]),
        legal_controls=_normalize_list(profile["legal_controls"]),
        medical_claim_controls=_normalize_list(profile["medical_claim_controls"]),
        validation_points=_normalize_list(profile["validation_points"]),
        failure_modes=_normalize_list(profile["failure_modes"]),
        assumptions=_dedupe_preserve([
            *(_normalize_list(profile.get("assumptions", []))),
            *source_constraints,
            "architecture plan remains metadata-only",
        ]),
        unknowns=_dedupe_preserve([
            *(_normalize_list(profile.get("unknowns", []))),
            *source_unknowns,
            "implementation details still need selection",
        ]),
        constraints=_dedupe_preserve([
            *(_normalize_list(profile.get("constraints", []))),
            *source_boundary,
        ]),
        evidence_requirements=_dedupe_preserve([
            *(_normalize_list(profile.get("evidence_requirements", []))),
            *source_evidence,
        ]),
        recommended_next_artifact=_safe_text(recommended_next_artifact),
        stack_decision_required=stack_decision_required,
        file_manifest_required=file_manifest_required,
        code_generation_allowed=code_generation_allowed,
        file_write_authority_granted=False,
        prototype_allowed_level=_safe_text(prototype_allowed_level),
        public_claim_allowed=False,
        iss_internal_reference_allowed=True,
        learning_claimed=False,
        runtime_authority=False,
        writes_state=False,
        model_provider_used=False,
        safe_metadata={
            "source": "project_architecture_planner_v1",
            "source_brief_id": source_brief_id,
            "architecture_type": architecture_type,
            "project_stage": selected_stage,
            "domain_family": domain_family,
            "recommended_next_artifact": _safe_text(recommended_next_artifact),
            "local_cloud_strategy": _safe_text(local_cloud_strategy),
        },
    )
    validate_project_architecture_plan_v1(architecture)
    return architecture



def build_project_architecture_from_brief_v1(project_brief: Any) -> ArchitecturePlan:
    return build_project_architecture_plan_v1(project_brief)


# ---------------------------------------------------------------------------
# Validation and summaries
# ---------------------------------------------------------------------------


def validate_project_architecture_plan_v1(plan: Any) -> bool:
    if _contains_forbidden_fields(plan):
        raise ValidationError("forbidden_raw_fields_present")
    if _contains_forbidden_claim_marker(plan):
        raise ValidationError("forbidden_public_or_claim_language_present")
    if _contains_unsafe_deployment_marker(plan):
        raise ValidationError("unsafe_deployment_marker_present")
    if _contains_covert_tracking_marker(plan):
        raise ValidationError("covert_tracking_marker_present")
    if _contains_diagnosis_treatment_marker(plan):
        raise ValidationError("diagnosis_treatment_authority_marker_present")

    if is_dataclass(plan):
        normalized = plan
    elif isinstance(plan, Mapping):
        allowed = {field.name for field in ArchitecturePlan.__dataclass_fields__.values()}
        extra = set(str(key) for key in plan.keys()) - allowed
        if extra:
            raise ValidationError("unknown_fields_present")
        normalized = ArchitecturePlan(
            architecture_id=_safe_text(plan.get("architecture_id")),
            architecture_type=_safe_text(plan.get("architecture_type")),
            source_brief_id=_safe_text(plan.get("source_brief_id")),
            project_title=_safe_text(plan.get("project_title")),
            project_stage=_safe_text(plan.get("project_stage")),
            domain_family=_safe_text(plan.get("domain_family")),
            meta_domains=_normalize_list(plan.get("meta_domains")),
            risk_labels=_normalize_list(plan.get("risk_labels")),
            boundary_requirements=_normalize_list(plan.get("boundary_requirements")),
            architecture_goals=_normalize_list(plan.get("architecture_goals")),
            non_goals=_normalize_list(plan.get("non_goals")),
            architecture_options=_normalize_list(plan.get("architecture_options")),
            selected_architecture=_safe_text(plan.get("selected_architecture")),
            component_map=_normalize_list(plan.get("component_map")),
            data_flow=_normalize_list(plan.get("data_flow")),
            control_flow=_normalize_list(plan.get("control_flow")),
            interface_surfaces=_normalize_list(plan.get("interface_surfaces")),
            storage_strategy=_normalize_list(plan.get("storage_strategy")),
            local_cloud_strategy=_safe_text(plan.get("local_cloud_strategy")),
            privacy_controls=_normalize_list(plan.get("privacy_controls")),
            safety_controls=_normalize_list(plan.get("safety_controls")),
            legal_controls=_normalize_list(plan.get("legal_controls")),
            medical_claim_controls=_normalize_list(plan.get("medical_claim_controls")),
            validation_points=_normalize_list(plan.get("validation_points")),
            failure_modes=_normalize_list(plan.get("failure_modes")),
            assumptions=_normalize_list(plan.get("assumptions")),
            unknowns=_normalize_list(plan.get("unknowns")),
            constraints=_normalize_list(plan.get("constraints")),
            evidence_requirements=_normalize_list(plan.get("evidence_requirements")),
            recommended_next_artifact=_safe_text(plan.get("recommended_next_artifact")),
            stack_decision_required=bool(plan.get("stack_decision_required")),
            file_manifest_required=bool(plan.get("file_manifest_required")),
            code_generation_allowed=bool(plan.get("code_generation_allowed")),
            file_write_authority_granted=bool(plan.get("file_write_authority_granted")),
            prototype_allowed_level=_safe_text(plan.get("prototype_allowed_level")),
            public_claim_allowed=bool(plan.get("public_claim_allowed")),
            iss_internal_reference_allowed=bool(plan.get("iss_internal_reference_allowed")),
            learning_claimed=bool(plan.get("learning_claimed")),
            runtime_authority=bool(plan.get("runtime_authority")),
            writes_state=bool(plan.get("writes_state")),
            model_provider_used=bool(plan.get("model_provider_used")),
            safe_metadata=dict(plan.get("safe_metadata") or {}),
        )
    else:
        raise ValidationError("architecture_plan_must_be_dataclass_or_mapping")

    if not normalized.architecture_id:
        raise ValidationError("architecture_id_required")
    if normalized.architecture_type not in ALLOWED_ARCHITECTURE_TYPES_V1:
        raise ValidationError("unknown_architecture_type")
    if not normalized.source_brief_id:
        raise ValidationError("source_brief_id_required")
    if not normalized.project_title:
        raise ValidationError("project_title_required")
    if normalized.project_stage not in {"concept_only", "research_planning", "prototype_planning", "architecture_ready", "needs_evidence_before_build", "blocked_by_boundary"}:
        raise ValidationError("unknown_project_stage")
    if not normalized.domain_family:
        raise ValidationError("domain_family_required")
    if normalized.recommended_next_artifact not in ALLOWED_NEXT_ARTIFACTS_V1:
        raise ValidationError("unknown_recommended_next_artifact")
    if normalized.local_cloud_strategy not in ALLOWED_LOCAL_CLOUD_STRATEGIES_V1:
        raise ValidationError("unknown_local_cloud_strategy")
    if normalized.prototype_allowed_level not in ALLOWED_PROTOTYPE_LEVELS_V1:
        raise ValidationError("unknown_prototype_allowed_level")

    for field_name in (
        "stack_decision_required",
        "file_manifest_required",
        "code_generation_allowed",
        "file_write_authority_granted",
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
    if normalized.learning_claimed:
        raise ValidationError("learning_claimed_must_be_false")
    if normalized.runtime_authority:
        raise ValidationError("runtime_authority_must_be_false")
    if normalized.writes_state:
        raise ValidationError("writes_state_must_be_false")
    if normalized.model_provider_used:
        raise ValidationError("model_provider_used_must_be_false")
    if normalized.file_write_authority_granted:
        raise ValidationError("file_write_authority_granted_must_be_false")

    for field_name in (
        "meta_domains",
        "risk_labels",
        "boundary_requirements",
        "architecture_goals",
        "non_goals",
        "architecture_options",
        "component_map",
        "data_flow",
        "control_flow",
        "interface_surfaces",
        "storage_strategy",
        "privacy_controls",
        "safety_controls",
        "legal_controls",
        "medical_claim_controls",
        "validation_points",
        "failure_modes",
        "assumptions",
        "unknowns",
        "constraints",
        "evidence_requirements",
    ):
        value = getattr(normalized, field_name)
        if not isinstance(value, list):
            raise ValidationError(f"{field_name}_must_be_list")
        if not value:
            raise ValidationError(f"{field_name}_required")

    if not normalized.selected_architecture:
        raise ValidationError("selected_architecture_required")

    if normalized.architecture_type == "privacy_sensitive_assistive_architecture":
        blob = _list_blob(normalized.privacy_controls + normalized.safety_controls + normalized.component_map)
        if not all(term in blob for term in ("consent", "data minimization", "user control", "auditability")):
            raise ValidationError("privacy_assistive_architecture_requires_privacy_controls")
    if normalized.architecture_type == "medical_software_pathway_architecture":
        blob = _list_blob(normalized.medical_claim_controls + normalized.validation_points + normalized.safety_controls)
        if not all(term in blob for term in ("clinical", "regulatory", "safety")):
            raise ValidationError("medical_pathway_requires_validation_controls")
    if normalized.architecture_type == "materials_research_architecture":
        blob = _list_blob(normalized.validation_points + normalized.failure_modes)
        if not any(term in blob for term in ("validation", "uncertainty")):
            raise ValidationError("materials_architecture_requires_validation_language")
    if normalized.architecture_type == "ai_system_architecture":
        blob = _list_blob(normalized.architecture_goals + normalized.safety_controls + normalized.validation_points)
        if not all(term in blob for term in ("governance", "evaluation", "safety")):
            raise ValidationError("ai_architecture_requires_governance_language")
    if normalized.architecture_type == "conceptual_research_architecture":
        blob = _list_blob(normalized.component_map + normalized.validation_points)
        if not all(term in blob for term in ("definition", "claim", "evidence")):
            raise ValidationError("conceptual_architecture_requires_mapping_language")
    if normalized.architecture_type == "unknown_domain_architecture":
        blob = _list_blob(normalized.architecture_goals + normalized.validation_points)
        if not all(term in blob for term in ("clarification", "evidence")):
            raise ValidationError("unknown_architecture_requires_clarification_language")

    return True



def summarize_project_architecture_plan_v1(plan: Any) -> ArchitecturePlanSummary:
    if not isinstance(plan, ArchitecturePlan):
        validate_project_architecture_plan_v1(plan)
        if isinstance(plan, Mapping):
            plan = ArchitecturePlan(
                architecture_id=_safe_text(plan.get("architecture_id")),
                architecture_type=_safe_text(plan.get("architecture_type")),
                source_brief_id=_safe_text(plan.get("source_brief_id")),
                project_title=_safe_text(plan.get("project_title")),
                project_stage=_safe_text(plan.get("project_stage")),
                domain_family=_safe_text(plan.get("domain_family")),
                meta_domains=_normalize_list(plan.get("meta_domains")),
                risk_labels=_normalize_list(plan.get("risk_labels")),
                boundary_requirements=_normalize_list(plan.get("boundary_requirements")),
                architecture_goals=_normalize_list(plan.get("architecture_goals")),
                non_goals=_normalize_list(plan.get("non_goals")),
                architecture_options=_normalize_list(plan.get("architecture_options")),
                selected_architecture=_safe_text(plan.get("selected_architecture")),
                component_map=_normalize_list(plan.get("component_map")),
                data_flow=_normalize_list(plan.get("data_flow")),
                control_flow=_normalize_list(plan.get("control_flow")),
                interface_surfaces=_normalize_list(plan.get("interface_surfaces")),
                storage_strategy=_normalize_list(plan.get("storage_strategy")),
                local_cloud_strategy=_safe_text(plan.get("local_cloud_strategy")),
                privacy_controls=_normalize_list(plan.get("privacy_controls")),
                safety_controls=_normalize_list(plan.get("safety_controls")),
                legal_controls=_normalize_list(plan.get("legal_controls")),
                medical_claim_controls=_normalize_list(plan.get("medical_claim_controls")),
                validation_points=_normalize_list(plan.get("validation_points")),
                failure_modes=_normalize_list(plan.get("failure_modes")),
                assumptions=_normalize_list(plan.get("assumptions")),
                unknowns=_normalize_list(plan.get("unknowns")),
                constraints=_normalize_list(plan.get("constraints")),
                evidence_requirements=_normalize_list(plan.get("evidence_requirements")),
                recommended_next_artifact=_safe_text(plan.get("recommended_next_artifact")),
                stack_decision_required=bool(plan.get("stack_decision_required")),
                file_manifest_required=bool(plan.get("file_manifest_required")),
                code_generation_allowed=bool(plan.get("code_generation_allowed")),
                file_write_authority_granted=bool(plan.get("file_write_authority_granted")),
                prototype_allowed_level=_safe_text(plan.get("prototype_allowed_level")),
                public_claim_allowed=bool(plan.get("public_claim_allowed")),
                iss_internal_reference_allowed=bool(plan.get("iss_internal_reference_allowed")),
                learning_claimed=bool(plan.get("learning_claimed")),
                runtime_authority=bool(plan.get("runtime_authority")),
                writes_state=bool(plan.get("writes_state")),
                model_provider_used=bool(plan.get("model_provider_used")),
                safe_metadata=dict(plan.get("safe_metadata") or {}),
            )
    return ArchitecturePlanSummary(
        summary_type=SUMMARY_TYPE_V1,
        architecture_id=plan.architecture_id,
        architecture_type=plan.architecture_type,
        project_stage=plan.project_stage,
        selected_architecture=plan.selected_architecture,
        recommended_next_artifact=plan.recommended_next_artifact,
        domain_family=plan.domain_family,
        architecture_goal_count=len(plan.architecture_goals),
        component_count=len(plan.component_map),
        validation_point_count=len(plan.validation_points),
    )



def to_project_architecture_json_safe_v1(value: Any) -> Any:
    return _json_safe(value)


# ---------------------------------------------------------------------------
# Seed examples
# ---------------------------------------------------------------------------


def build_initial_project_architecture_examples_v1() -> tuple[ArchitecturePlan, ...]:
    from weslr.project_brief_builder import build_initial_project_brief_examples_v1

    examples: list[ArchitecturePlan] = []
    for brief in build_initial_project_brief_examples_v1():
        examples.append(build_project_architecture_from_brief_v1(brief))
    return tuple(examples)


# Backwards-compatible aliases.
build_project_architecture_plan = build_project_architecture_plan_v1
build_project_architecture_from_brief = build_project_architecture_from_brief_v1
validate_project_architecture_plan = validate_project_architecture_plan_v1
summarize_project_architecture_plan = summarize_project_architecture_plan_v1
to_project_architecture_json_safe = to_project_architecture_json_safe_v1
build_initial_project_architecture_examples = build_initial_project_architecture_examples_v1
