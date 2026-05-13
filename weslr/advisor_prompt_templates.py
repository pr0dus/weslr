from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from weslr.llm_advisor_mode import AdvisorSafetyFlags, ALLOWED_ADVISOR_TASK_TYPES


REQUIRED_ADVISOR_TEMPLATE_TASK_TYPES = [
    "architecture_review",
    "failure_diagnosis",
    "style_review",
    "test_suggestion",
    "synthetic_example_suggestion",
    "reasoning_pattern_review",
    "gap_taxonomy_review",
    "wording_risk_review",
    "alternative_design_proposal",
    "provider_capability_review",
]
REQUIRED_OUTPUT_SECTIONS = [
    "Summary",
    "Recommendations",
    "Risks",
    "Tests to add",
    "Unsupported gaps to preserve",
    "What not to implement yet",
    "Safety boundary check",
]
COMMON_BOUNDARY = (
    "You are advising WESLR, a deterministic, governed, LLM-assisted system.\n"
    "Your output is non-authoritative proposal input.\n"
    "Do not select answers.\n"
    "Do not claim truth or soundness.\n"
    "Do not claim official score.\n"
    "Do not use answer keys.\n"
    "Do not request secrets.\n"
    "Do not request raw benchmark text.\n"
    "Do not suggest runtime/config/memory/policy mutation without operator approval.\n"
    "Return recommendations, risks, tests, and what must remain unsupported."
)
DEFAULT_INPUT_REQUIREMENTS = [
    "Use redacted structural summaries only.",
    "Use diagnostics, counts, schema summaries, or synthetic artifacts.",
    "Keep provider-neutral wording; do not assume a model vendor.",
]
DEFAULT_FORBIDDEN_INPUTS = [
    "raw benchmark text by default",
    "answer keys",
    "secrets, API keys, or tokens",
    "private user data by default",
    "OpenClaw config secrets",
]
DEFAULT_FORBIDDEN_OUTPUTS = [
    "answer selection",
    "truth or soundness authority",
    "official score claims",
    "benchmark-specific tuning instructions",
    "answer-key use",
    "runtime mutation",
    "memory mutation",
    "governance override",
    "model-internal extraction",
]
DEFAULT_SAFETY_REMINDERS = [
    "Treat advisor output as non-authoritative proposal input.",
    "Require WESLR validation before adoption.",
    "Require operator review before adoption.",
    "Preserve unsupported gaps instead of hiding uncertainty.",
    "Do not create runtime truth.",
]
UNSAFE_PROMPT_PATTERNS = [
    "select the answer",
    "choose the answer",
    "use the answer key",
    "claim official score",
    "request secrets",
    "provide api key",
    "provide token",
    "mutate runtime",
    "change runtime now",
    "extract model internals",
]
SENSITIVE_SUMMARY_PATTERNS = ["api key", "token", "secret", "raw benchmark", "answer key", "private user data"]


@dataclass
class AdvisorPromptTemplate:
    schema_version: str = "1.0"
    template_id: str = ""
    task_type: str = "unknown"
    title: str = ""
    purpose: str = ""
    system_boundary: str = ""
    input_requirements: list[str] = field(default_factory=list)
    forbidden_inputs: list[str] = field(default_factory=list)
    forbidden_outputs: list[str] = field(default_factory=list)
    required_output_sections: list[str] = field(default_factory=list)
    safety_reminders: list[str] = field(default_factory=list)
    provider_neutral: bool = True
    non_authoritative: bool = True
    requires_validation: bool = True
    requires_operator_review: bool = True
    not_runtime_truth: bool = True


@dataclass
class RenderedAdvisorPrompt:
    schema_version: str = "1.0"
    template_id: str = ""
    task_type: str = "unknown"
    input_summary_hash: str = ""
    redaction_level: str = "structural_summary_only"
    prompt_text: str = ""
    safety_flags: AdvisorSafetyFlags = field(default_factory=AdvisorSafetyFlags)


def _list_from_value(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return [str(item) for item in value if str(item).strip()]
    if str(value).strip():
        return [str(value).strip()]
    return []


def create_advisor_prompt_template(task_type: str = "unknown", **overrides: Any) -> AdvisorPromptTemplate:
    title = overrides.pop("title", task_type.replace("_", " ").title() if task_type else "Unknown Advisor Task")
    purpose = overrides.pop("purpose", f"Collect non-authoritative advisor review for {task_type}.")
    template = AdvisorPromptTemplate(
        template_id=overrides.pop("template_id", f"advisor_prompt:{task_type}"),
        task_type=task_type,
        title=title,
        purpose=purpose,
        system_boundary=overrides.pop("system_boundary", COMMON_BOUNDARY),
        input_requirements=overrides.pop("input_requirements", list(DEFAULT_INPUT_REQUIREMENTS)),
        forbidden_inputs=overrides.pop("forbidden_inputs", list(DEFAULT_FORBIDDEN_INPUTS)),
        forbidden_outputs=overrides.pop("forbidden_outputs", list(DEFAULT_FORBIDDEN_OUTPUTS)),
        required_output_sections=overrides.pop("required_output_sections", list(REQUIRED_OUTPUT_SECTIONS)),
        safety_reminders=overrides.pop("safety_reminders", list(DEFAULT_SAFETY_REMINDERS)),
    )
    for key, value in overrides.items():
        if hasattr(template, key):
            setattr(template, key, value)
    return template


def load_advisor_prompt_templates_v1() -> list[AdvisorPromptTemplate]:
    purposes = {
        "architecture_review": "Review architecture boundaries, risks, and safe next proposals.",
        "failure_diagnosis": "Diagnose failures using redacted evidence and propose tests or diagnostics.",
        "style_review": "Review wording/style risks while preserving the evidence contract.",
        "test_suggestion": "Suggest tests for governed WESLR artifacts without changing runtime behavior.",
        "synthetic_example_suggestion": "Suggest synthetic examples without benchmark text or answer keys.",
        "reasoning_pattern_review": "Review reasoning-pattern structure and unresolved gaps.",
        "gap_taxonomy_review": "Review unsupported-gap categories and which gaps must remain visible.",
        "wording_risk_review": "Find wording that may overclaim authority or hide uncertainty.",
        "alternative_design_proposal": "Propose alternative designs as non-authoritative candidates.",
        "provider_capability_review": "Review provider capability descriptions without changing configuration.",
    }
    return [create_advisor_prompt_template(task_type, purpose=purposes[task_type]) for task_type in REQUIRED_ADVISOR_TEMPLATE_TASK_TYPES]


def get_advisor_prompt_template(task_type: str) -> AdvisorPromptTemplate:
    for template in load_advisor_prompt_templates_v1():
        if template.task_type == task_type:
            return template
    return create_advisor_prompt_template("unknown", template_id="advisor_prompt:unknown", title="Unknown Advisor Task")


def advisor_prompt_template_to_dict(template: AdvisorPromptTemplate) -> dict[str, Any]:
    return asdict(template)


def advisor_prompt_template_from_dict(data: dict[str, Any]) -> AdvisorPromptTemplate:
    return AdvisorPromptTemplate(
        schema_version=str(data.get("schema_version", "1.0") or "1.0"),
        template_id=str(data.get("template_id", "") or ""),
        task_type=str(data.get("task_type", "unknown") or "unknown"),
        title=str(data.get("title", "") or ""),
        purpose=str(data.get("purpose", "") or ""),
        system_boundary=str(data.get("system_boundary", "") or ""),
        input_requirements=_list_from_value(data.get("input_requirements", [])),
        forbidden_inputs=_list_from_value(data.get("forbidden_inputs", [])),
        forbidden_outputs=_list_from_value(data.get("forbidden_outputs", [])),
        required_output_sections=_list_from_value(data.get("required_output_sections", [])),
        safety_reminders=_list_from_value(data.get("safety_reminders", [])),
        provider_neutral=bool(data.get("provider_neutral", True)),
        non_authoritative=bool(data.get("non_authoritative", True)),
        requires_validation=bool(data.get("requires_validation", True)),
        requires_operator_review=bool(data.get("requires_operator_review", True)),
        not_runtime_truth=bool(data.get("not_runtime_truth", True)),
    )


def _combined_template_text(template: AdvisorPromptTemplate) -> str:
    return "\n".join(
        [
            template.title,
            template.purpose,
            template.system_boundary,
            *template.input_requirements,
            *template.forbidden_inputs,
            *template.forbidden_outputs,
            *template.required_output_sections,
            *template.safety_reminders,
        ]
    ).lower()


def validate_advisor_prompt_template(template: AdvisorPromptTemplate) -> list[str]:
    messages: list[str] = []
    if not template.template_id.strip():
        messages.append("missing template id")
    if template.task_type not in ALLOWED_ADVISOR_TASK_TYPES or template.task_type == "unknown":
        messages.append("invalid task type")
    if not template.provider_neutral:
        messages.append("provider_neutral false")
    if not template.non_authoritative:
        messages.append("non_authoritative false")
    if not template.requires_validation:
        messages.append("requires_validation false")
    if not template.requires_operator_review:
        messages.append("requires_operator_review false")
    if not template.not_runtime_truth:
        messages.append("not_runtime_truth false")
    if not template.forbidden_outputs:
        messages.append("missing forbidden output rules")
    missing_sections = [section for section in REQUIRED_OUTPUT_SECTIONS if section not in template.required_output_sections]
    if missing_sections:
        messages.append("missing required output sections")
    text = _combined_template_text(template)
    unsafe_checks = {
        "template asks for answer selection": ["select the answer", "choose the answer"],
        "template asks for answer keys": ["use the answer key"],
        "template asks for official score": ["claim official score"],
        "template asks for secrets/API keys/tokens": ["request secrets", "provide api key", "provide token"],
        "template requests runtime mutation": ["mutate runtime", "change runtime now"],
    }
    for message, patterns in unsafe_checks.items():
        for pattern in patterns:
            start = 0
            while True:
                index = text.find(pattern, start)
                if index < 0:
                    break
                prefix = text[max(0, index - 12):index]
                if "do not " not in prefix and "no " not in prefix:
                    messages.append(message)
                    break
                start = index + len(pattern)
    return messages


def render_advisor_prompt(task_type: str, redacted_structural_input_summary: str, input_summary_hash: str, redaction_level: str = "structural_summary_only") -> RenderedAdvisorPrompt:
    template = get_advisor_prompt_template(task_type)
    sections = "\n".join(f"- {section}" for section in template.required_output_sections)
    prompt_text = (
        f"# {template.title}\n\n"
        f"Purpose: {template.purpose}\n\n"
        f"System boundary:\n{template.system_boundary}\n\n"
        f"Input redaction level: {redaction_level}\n"
        f"Input summary hash: {input_summary_hash}\n\n"
        f"Redacted structural input summary:\n{redacted_structural_input_summary}\n\n"
        f"Required output sections:\n{sections}\n\n"
        "Safety: Your response is non-authoritative proposal input, requires validation, requires operator review, and is not runtime truth."
    )
    return RenderedAdvisorPrompt(
        template_id=template.template_id,
        task_type=template.task_type,
        input_summary_hash=input_summary_hash,
        redaction_level=redaction_level,
        prompt_text=prompt_text,
        safety_flags=AdvisorSafetyFlags(),
    )


def rendered_advisor_prompt_to_dict(prompt: RenderedAdvisorPrompt) -> dict[str, Any]:
    return asdict(prompt)


def rendered_advisor_prompt_from_dict(data: dict[str, Any]) -> RenderedAdvisorPrompt:
    flags_source = data.get("safety_flags", {})
    flags = flags_source if isinstance(flags_source, AdvisorSafetyFlags) else AdvisorSafetyFlags(**(flags_source if isinstance(flags_source, dict) else {}))
    return RenderedAdvisorPrompt(
        schema_version=str(data.get("schema_version", "1.0") or "1.0"),
        template_id=str(data.get("template_id", "") or ""),
        task_type=str(data.get("task_type", "unknown") or "unknown"),
        input_summary_hash=str(data.get("input_summary_hash", "") or ""),
        redaction_level=str(data.get("redaction_level", "structural_summary_only") or "structural_summary_only"),
        prompt_text=str(data.get("prompt_text", "") or ""),
        safety_flags=flags,
    )


def validate_rendered_advisor_prompt(prompt: RenderedAdvisorPrompt) -> list[str]:
    messages: list[str] = []
    if prompt.task_type not in ALLOWED_ADVISOR_TASK_TYPES or prompt.task_type == "unknown":
        messages.append("invalid task type")
    if not prompt.input_summary_hash.strip():
        messages.append("missing input summary hash")
    if not prompt.redaction_level.strip():
        messages.append("missing redaction level")
    text = prompt.prompt_text.lower()
    for required in ["non-authoritative proposal input", "requires validation", "requires operator review", "not runtime truth"]:
        if required not in text:
            messages.append("missing non-authoritative boundary")
            break
    for section in REQUIRED_OUTPUT_SECTIONS:
        if section.lower() not in text:
            messages.append("missing required output sections")
            break
    if any(asdict(prompt.safety_flags).values()):
        messages.append("unsafe safety flags")
    return messages


def summarize_advisor_prompt_template_library(templates: list[AdvisorPromptTemplate] | None = None) -> dict[str, Any]:
    templates = templates if templates is not None else load_advisor_prompt_templates_v1()
    validation_errors = sum(len(validate_advisor_prompt_template(template)) for template in templates)
    return {
        "schema_version": "1.0",
        "template_count": len(templates),
        "task_types": sorted(template.task_type for template in templates),
        "provider_neutral_count": sum(1 for template in templates if template.provider_neutral),
        "non_authoritative_count": sum(1 for template in templates if template.non_authoritative),
        "requires_validation_count": sum(1 for template in templates if template.requires_validation),
        "requires_operator_review_count": sum(1 for template in templates if template.requires_operator_review),
        "not_runtime_truth_count": sum(1 for template in templates if template.not_runtime_truth),
        "required_output_section_count": len(REQUIRED_OUTPUT_SECTIONS),
        "validation_error_count": validation_errors,
    }
