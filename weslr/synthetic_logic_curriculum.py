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


def load_synthetic_logic_curriculum_v1() -> list[SyntheticLogicCurriculumExample]:
    shared_notes = [
        "handcrafted synthetic placeholder",
        "no external benchmark text",
        "no answer selection",
        "schema-only fixture",
    ]
    return [
        SyntheticLogicCurriculumExample(
            example_id="synthetic_logic_v1_universal_syllogism_001",
            logic_family="universal_syllogism",
            input_form="mcq_like",
            premise_templates=[
                "All objects in class K have property Y.",
                "Object X is in class K.",
            ],
            question_instruction_template="Identify the structural relation between object X and property Y.",
            choice_templates=[
                "Object X has property Y.",
                "Object X lacks property Y.",
                "Class K is unrelated to property Y.",
                "Property Y implies class K.",
            ],
            expected_structural_pattern="universal_syllogism",
            expected_context_binding_type="candidate_conclusion",
            expected_teaching_focus="universal rule application without answer selection",
            unsupported_gaps_allowed=["surface wording may require proposition extraction"],
            anti_gaming_notes=shared_notes,
        ),
        SyntheticLogicCurriculumExample(
            example_id="synthetic_logic_v1_modus_ponens_001",
            logic_family="modus_ponens",
            input_form="argument_only",
            premise_templates=["If P then Q.", "P."],
            question_instruction_template="Expose the inference pattern connecting P and Q.",
            choice_templates=["Q.", "not Q.", "P is unsupported.", "Q implies P."],
            expected_structural_pattern="modus_ponens",
            expected_context_binding_type="candidate_conclusion",
            expected_teaching_focus="conditional support from affirmed antecedent",
            unsupported_gaps_allowed=["symbol normalization may be needed"],
            anti_gaming_notes=shared_notes,
        ),
        SyntheticLogicCurriculumExample(
            example_id="synthetic_logic_v1_modus_tollens_001",
            logic_family="modus_tollens",
            input_form="argument_only",
            premise_templates=["If P then Q.", "not Q."],
            question_instruction_template="Expose the inference pattern involving the denied consequent.",
            choice_templates=["not P.", "P.", "Q.", "P and Q are unrelated."],
            expected_structural_pattern="modus_tollens",
            expected_context_binding_type="candidate_conclusion",
            expected_teaching_focus="conditional support from denied consequent",
            unsupported_gaps_allowed=["negation scope may require explicit tracking"],
            anti_gaming_notes=shared_notes,
        ),
        SyntheticLogicCurriculumExample(
            example_id="synthetic_logic_v1_affirming_consequent_001",
            logic_family="affirming_consequent",
            input_form="mcq_like",
            premise_templates=["If P then Q.", "Q."],
            question_instruction_template="Identify whether the structure treats Q as support for P.",
            choice_templates=["P.", "not P.", "Q is present.", "P is not licensed by Q alone."],
            expected_structural_pattern="affirming_consequent",
            expected_context_binding_type="fallacy_shaped_candidate",
            expected_teaching_focus="distinguish consequent affirmation from valid support",
            unsupported_gaps_allowed=["fallacy label may be exposed without choosing a response"],
            anti_gaming_notes=shared_notes,
        ),
        SyntheticLogicCurriculumExample(
            example_id="synthetic_logic_v1_denying_antecedent_001",
            logic_family="denying_antecedent",
            input_form="mcq_like",
            premise_templates=["If P then Q.", "not P."],
            question_instruction_template="Identify whether the structure treats not P as support for not Q.",
            choice_templates=["not Q.", "Q.", "not P is present.", "not Q is not licensed by not P alone."],
            expected_structural_pattern="denying_antecedent",
            expected_context_binding_type="fallacy_shaped_candidate",
            expected_teaching_focus="distinguish antecedent denial from valid support",
            unsupported_gaps_allowed=["fallacy label may be exposed without choosing a response"],
            anti_gaming_notes=shared_notes,
        ),
        SyntheticLogicCurriculumExample(
            example_id="synthetic_logic_v1_contradiction_001",
            logic_family="contradiction",
            input_form="argument_only",
            premise_templates=["P.", "not P."],
            question_instruction_template="Expose the conflict between the two premise templates.",
            choice_templates=["P and not P conflict.", "P supports Q.", "not P supports R.", "No relation is visible."],
            expected_structural_pattern="contradiction",
            expected_context_binding_type="conflict_record",
            expected_teaching_focus="make direct contradiction legible",
            unsupported_gaps_allowed=["negation normalization may be needed"],
            anti_gaming_notes=shared_notes,
        ),
        SyntheticLogicCurriculumExample(
            example_id="synthetic_logic_v1_counterexample_001",
            logic_family="counterexample",
            input_form="mcq_like",
            premise_templates=["A proposed rule says all objects in group G have property Y."],
            question_instruction_template="Identify a structure that behaves like a counterexample to the proposed rule.",
            choice_templates=[
                "Object X is in group G and lacks property Y.",
                "Object X is in group G and has property Y.",
                "Object X is not in group G and has property Y.",
                "Group G is mentioned without object X.",
            ],
            expected_structural_pattern="counterexample",
            expected_context_binding_type="candidate_counterexample",
            expected_teaching_focus="bind group membership with property absence",
            unsupported_gaps_allowed=["choice proposition merge may be required"],
            anti_gaming_notes=shared_notes,
        ),
        SyntheticLogicCurriculumExample(
            example_id="synthetic_logic_v1_irrelevant_choice_001",
            logic_family="irrelevant_choice",
            input_form="mcq_like",
            premise_templates=["If P then Q.", "P."],
            question_instruction_template="Identify a choice structure that does not bind to the premise relation.",
            choice_templates=["R has property Y.", "Q.", "P is present.", "If Q then P."],
            expected_structural_pattern="irrelevant_choice",
            expected_context_binding_type="irrelevant_choice",
            expected_teaching_focus="separate unrelated symbolic content from candidate conclusions",
            unsupported_gaps_allowed=["irrelevance may be represented as weak binding"],
            anti_gaming_notes=shared_notes,
        ),
        SyntheticLogicCurriculumExample(
            example_id="synthetic_logic_v1_noun_phrase_choice_binding_001",
            logic_family="noun_phrase_choice_binding",
            input_form="mcq_like",
            premise_templates=["Object X is in class K.", "Class K has property Y."],
            question_instruction_template="Bind a noun-phrase choice back to object X and property Y.",
            choice_templates=["object X with property Y", "class K without property Y", "property Y alone", "group G alone"],
            expected_structural_pattern="noun_phrase_choice_binding",
            expected_context_binding_type="noun_phrase_candidate_binding",
            expected_teaching_focus="make fragment binding visible without selecting an answer",
            unsupported_gaps_allowed=["fragment choices may need contextual completion"],
            anti_gaming_notes=shared_notes,
        ),
        SyntheticLogicCurriculumExample(
            example_id="synthetic_logic_v1_invalid_argument_identification_001",
            logic_family="invalid_argument_identification",
            input_form="teaching_prompt",
            premise_templates=["If P then Q.", "Q."],
            question_instruction_template="Expose why support for P is not licensed by these premises alone.",
            choice_templates=["P is asserted from Q.", "Q is stated.", "P implies Q.", "No conditional is present."],
            expected_structural_pattern="invalid_argument_identification",
            expected_context_binding_type="invalid_support_candidate",
            expected_teaching_focus="mark unsupported support step as visible",
            unsupported_gaps_allowed=["invalidity explanation may remain template-level"],
            anti_gaming_notes=shared_notes,
        ),
        SyntheticLogicCurriculumExample(
            example_id="synthetic_logic_v1_necessary_sufficient_confusion_001",
            logic_family="necessary_sufficient_confusion",
            input_form="mcq_like",
            premise_templates=["P is sufficient for Q.", "Q is necessary for P."],
            question_instruction_template="Expose the direction of support between P and Q.",
            choice_templates=["P supports Q.", "Q supports P.", "P and Q are identical.", "R supports P."],
            expected_structural_pattern="necessary_sufficient_confusion",
            expected_context_binding_type="directionality_candidate",
            expected_teaching_focus="track sufficient and necessary direction without answer selection",
            unsupported_gaps_allowed=["natural-language direction markers may need normalization"],
            anti_gaming_notes=shared_notes,
        ),
        SyntheticLogicCurriculumExample(
            example_id="synthetic_logic_v1_quantifier_reasoning_001",
            logic_family="quantifier_reasoning",
            input_form="argument_only",
            premise_templates=["Every object in group G has property Y.", "Some object X is in group G."],
            question_instruction_template="Expose quantifier scope linking group G and property Y.",
            choice_templates=["Object X has property Y.", "No object in group G has property Y.", "Some object outside group G has property Y.", "Property Y defines group G."],
            expected_structural_pattern="quantifier_reasoning",
            expected_context_binding_type="quantified_candidate_conclusion",
            expected_teaching_focus="bind universal and existential structures safely",
            unsupported_gaps_allowed=["quantifier scope may require explicit proposition fields"],
            anti_gaming_notes=shared_notes,
        ),
        SyntheticLogicCurriculumExample(
            example_id="synthetic_logic_v1_negation_reasoning_001",
            logic_family="negation_reasoning",
            input_form="argument_only",
            premise_templates=["not P.", "If Q then P."],
            question_instruction_template="Expose how negation interacts with the conditional relation.",
            choice_templates=["not Q.", "Q.", "P.", "P and Q are identical."],
            expected_structural_pattern="negation_reasoning",
            expected_context_binding_type="negated_candidate_conclusion",
            expected_teaching_focus="track negation scope before inference comparison",
            unsupported_gaps_allowed=["double-negation and scope are out of scope for this fixture"],
            anti_gaming_notes=shared_notes,
        ),
        SyntheticLogicCurriculumExample(
            example_id="synthetic_logic_v1_disjunction_reasoning_001",
            logic_family="disjunction_reasoning",
            input_form="argument_only",
            premise_templates=["P or Q.", "not P."],
            question_instruction_template="Expose a disjunctive structure involving P and Q.",
            choice_templates=["Q.", "P.", "not Q.", "R."],
            expected_structural_pattern="disjunction_reasoning",
            expected_context_binding_type="disjunctive_candidate_conclusion",
            expected_teaching_focus="make disjunction and negation relation visible",
            unsupported_gaps_allowed=["exclusive versus inclusive disjunction may remain unspecified"],
            anti_gaming_notes=shared_notes,
        ),
    ]
