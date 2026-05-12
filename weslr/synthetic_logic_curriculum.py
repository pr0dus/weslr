from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


ALLOWED_LOGIC_FAMILIES = {
    "universal_syllogism",
    "modus_ponens",
    "modus_tollens",
    "affirming_consequent",
    "denying_antecedent",
    "contradiction",
    "counterexample",
    "irrelevant_choice",
    "noun_phrase_choice_binding",
    "invalid_argument_identification",
    "necessary_sufficient_confusion",
    "quantifier_reasoning",
    "negation_reasoning",
    "disjunction_reasoning",
    "unknown",
}

ALLOWED_INPUT_FORMS = {
    "mcq_like",
    "argument_only",
    "teaching_prompt",
    "unknown",
}


@dataclass
class SyntheticLogicAntiGamingRecord:
    uses_external_benchmark_text: bool = False
    uses_answer_key_tuning: bool = False
    uses_item_id_as_authority: bool = False
    official_score_claimed: bool = False
    answer_selection_enabled: bool = False
    benchmark_specific_tuning_used: bool = False


@dataclass
class SyntheticLogicLegibilityRecord:
    human_explanation_available: bool = True
    expected_pattern_visible: bool = True
    unsupported_gaps_visible: bool = True
    raw_benchmark_text_required: bool = False
    private_symbolic_authority_used: bool = False


@dataclass
class SyntheticLogicCurriculumExample:
    schema_version: str = "1.0"
    example_id: str = ""
    logic_family: str = ""
    input_form: str = "mcq_like"
    premise_templates: list[str] = field(default_factory=list)
    question_instruction_template: str = ""
    choice_templates: list[str] = field(default_factory=list)
    expected_structural_pattern: str = ""
    expected_context_binding_type: str = ""
    expected_teaching_focus: str = ""
    unsupported_gaps_allowed: list[str] = field(default_factory=list)
    anti_gaming_notes: list[str] = field(default_factory=list)
    legibility: SyntheticLogicLegibilityRecord = field(
        default_factory=SyntheticLogicLegibilityRecord
    )
    anti_gaming: SyntheticLogicAntiGamingRecord = field(
        default_factory=SyntheticLogicAntiGamingRecord
    )


def create_empty_synthetic_logic_curriculum_example(
    *,
    example_id: str = "",
    logic_family: str = "unknown",
    input_form: str = "mcq_like",
) -> SyntheticLogicCurriculumExample:
    return SyntheticLogicCurriculumExample(
        example_id=example_id,
        logic_family=logic_family,
        input_form=input_form,
    )


def synthetic_logic_curriculum_example_to_dict(
    example: SyntheticLogicCurriculumExample,
) -> dict[str, Any]:
    return asdict(example)


def synthetic_logic_curriculum_example_from_dict(
    data: dict[str, Any],
) -> SyntheticLogicCurriculumExample:
    legibility_data = data.get("legibility") or {}
    anti_gaming_data = data.get("anti_gaming") or {}
    payload = dict(data)
    payload["legibility"] = SyntheticLogicLegibilityRecord(**legibility_data)
    payload["anti_gaming"] = SyntheticLogicAntiGamingRecord(**anti_gaming_data)
    return SyntheticLogicCurriculumExample(**payload)


def validate_synthetic_logic_curriculum_example(
    example: SyntheticLogicCurriculumExample,
) -> list[str]:
    errors: list[str] = []

    if not example.example_id.strip():
        errors.append("missing example_id")
    if example.logic_family not in ALLOWED_LOGIC_FAMILIES:
        errors.append("invalid logic_family")
    if example.input_form not in ALLOWED_INPUT_FORMS:
        errors.append("invalid input_form")
    if not example.expected_structural_pattern.strip():
        errors.append("missing expected_structural_pattern")
    if not example.expected_context_binding_type.strip():
        errors.append("missing expected_context_binding_type")

    anti_gaming = example.anti_gaming
    if anti_gaming.uses_external_benchmark_text:
        errors.append("uses external benchmark text")
    if anti_gaming.uses_answer_key_tuning:
        errors.append("uses answer-key tuning")
    if anti_gaming.uses_item_id_as_authority:
        errors.append("uses item-ID authority")
    if anti_gaming.official_score_claimed:
        errors.append("official score claim")
    if anti_gaming.answer_selection_enabled:
        errors.append("answer selection enabled")
    if anti_gaming.benchmark_specific_tuning_used:
        errors.append("benchmark-specific tuning")

    legibility = example.legibility
    if legibility.raw_benchmark_text_required:
        errors.append("raw benchmark text required")
    if legibility.private_symbolic_authority_used:
        errors.append("private symbolic authority")
    if not legibility.unsupported_gaps_visible:
        errors.append("hidden unsupported gaps")

    return errors


def summarize_synthetic_logic_curriculum_example(
    example: SyntheticLogicCurriculumExample,
) -> dict[str, Any]:
    return {
        "schema_version": example.schema_version,
        "example_id": example.example_id,
        "logic_family": example.logic_family,
        "input_form": example.input_form,
        "premise_template_count": len(example.premise_templates),
        "choice_template_count": len(example.choice_templates),
        "unsupported_gap_count": len(example.unsupported_gaps_allowed),
        "anti_gaming_note_count": len(example.anti_gaming_notes),
        "has_expected_structural_pattern": bool(
            example.expected_structural_pattern.strip()
        ),
        "has_expected_context_binding_type": bool(
            example.expected_context_binding_type.strip()
        ),
        "has_expected_teaching_focus": bool(example.expected_teaching_focus.strip()),
        "legibility": asdict(example.legibility),
        "anti_gaming": asdict(example.anti_gaming),
        "validation_error_count": len(
            validate_synthetic_logic_curriculum_example(example)
        ),
    }
