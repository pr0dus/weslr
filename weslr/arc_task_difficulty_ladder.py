"""ARC Synthetic Task Difficulty Ladder (T1–T7) schema helpers.

This module is deterministic, metadata-only, and fail-closed. It defines the
WESLR task-side difficulty ladder and provides helpers for validating task
level definitions, classifying task contracts, and detecting coverage gaps.

It does not generate new tasks, change scoring, run solvers, or touch runtime,
chat, UI, provider, or `.weslr` paths.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

SCHEMA_VERSION_V1 = "arc_synthetic_task_difficulty_ladder_v1"
LEVEL_IDS_V1 = ("T1", "T2", "T3", "T4", "T5", "T6", "T7")

DEFAULT_COVERAGE_TARGETS_V1 = {
    "T1": 24,
    "T2": 24,
    "T3": 12,
    "T4": 12,
    "T5": 12,
    "T6": 12,
    "T7": 12,
}

DEFAULT_COVERAGE_KEYS_V1 = (
    "coverage_by_level",
    "task_counts_by_level",
    "level_counts",
    "counts_by_level",
)

LEVEL_DEFINITIONS_V1 = (
    {
        "level_id": "T1",
        "name": "primitive_isolation",
        "purpose": "Test one clear rule for primitive recognition and regression.",
        "task_signature": "one latent operation, one dominant object/action relation, minimal ambiguity",
        "required_metadata_fields": (
            "level_id",
            "purpose",
            "task_signature",
            "rule_type",
            "primary_object_scope",
            "expected_transform",
            "ambiguity_axes",
            "confidence_policy",
        ),
        "expected_solver_behavior": "Exact solve from a known primitive or near-direct regression.",
        "expected_failure_mode": "Overfitting only if the task is not actually isolated.",
        "anti_cheat_controls": (
            "no_task_id_shortcut",
            "no_primitive_name_leakage",
            "no_sequence_leakage",
            "no_noop_task",
            "no_single_template_repetition",
            "no_metadata_only_solving",
        ),
        "promotion_criteria": "Stable across small perturbations and safe as a regression fixture.",
        "scoring_layer_compatibility": ("scored", "regression"),
        "confidence_policy": "exact",
    },
    {
        "level_id": "T2",
        "name": "short_composition",
        "purpose": "Chain 2–3 known operations and test basic composition and carryover.",
        "task_signature": "two or three known primitives with deterministic order and preserved intermediate state",
        "required_metadata_fields": (
            "level_id",
            "purpose",
            "task_signature",
            "primitive_chain_length",
            "ordered_operations",
            "intermediate_state_required",
            "confidence_policy",
        ),
        "expected_solver_behavior": "Execute a known chain exactly.",
        "expected_failure_mode": "Order confusion, carryover drift, or chain truncation.",
        "anti_cheat_controls": (
            "no_sequence_leakage",
            "no_output_template_leakage",
            "no_duplicate_surface_reuse",
        ),
        "promotion_criteria": "Becomes scored/regression when the chain is stable and not overly templated.",
        "scoring_layer_compatibility": ("scored", "hard_mode"),
        "confidence_policy": "exact",
    },
    {
        "level_id": "T3",
        "name": "rival_grammar_ambiguous",
        "purpose": "Distinguish between several plausible rules using structure, not labels.",
        "task_signature": "multiple grammars fit the visible examples; separating evidence must choose the rule",
        "required_metadata_fields": (
            "level_id",
            "purpose",
            "task_signature",
            "rival_grammars",
            "ambiguity_axes",
            "separating_examples",
            "confidence_policy",
        ),
        "expected_solver_behavior": "Resolve confidently if evidence is sufficient; otherwise flag unresolved.",
        "expected_failure_mode": "Shallow heuristic, one-feature heuristic, or wrong tie-break rule.",
        "anti_cheat_controls": (
            "require_separating_examples",
            "no_tie_breaker_leakage",
            "no_easy_clue_metadata",
            "no_overfriendly_distractors",
        ),
        "promotion_criteria": "Moves into hard-mode/scored only when the ambiguity is genuine but resolvable and stable under perturbation.",
        "scoring_layer_compatibility": ("hard_mode", "scored"),
        "confidence_policy": "resolve_or_flag",
    },
    {
        "level_id": "T4",
        "name": "unseen_composition",
        "purpose": "Use known primitives in a new combination/order/scene type.",
        "task_signature": "known primitives, novel order or novel scene form, new composition graph",
        "required_metadata_fields": (
            "level_id",
            "purpose",
            "task_signature",
            "known_primitives",
            "novel_order",
            "novel_scene_form",
            "composition_graph",
            "confidence_policy",
        ),
        "expected_solver_behavior": "Generalize the composition, not just replay a memorized chain.",
        "expected_failure_mode": "Chain memorization, order fragility, or parameter transfer failure.",
        "anti_cheat_controls": (
            "no_exact_training_chain_repetition",
            "variants_must_change_shapes_distractors_or_geometry",
            "no_surface_copy_paste",
        ),
        "promotion_criteria": "Becomes scored when the composition is clearly new but still supported by existing primitives.",
        "scoring_layer_compatibility": ("hard_mode", "scored"),
        "confidence_policy": "exact_if_generalized",
    },
    {
        "level_id": "T5",
        "name": "primitive_insufficiency",
        "purpose": "Detect when existing primitives or short compositions do not cleanly explain the task.",
        "task_signature": "no existing primitive chain cleanly covers the rule; nearest primitives should fail in a separable way",
        "required_metadata_fields": (
            "level_id",
            "purpose",
            "task_signature",
            "nearest_primitive_set",
            "separating_examples",
            "candidate_primitive_hint",
            "duplicate_risk",
            "confidence_policy",
        ),
        "expected_solver_behavior": "Say existing primitives are insufficient or flag a candidate primitive gap.",
        "expected_failure_mode": "Overclaiming a solve from the nearest primitive.",
        "anti_cheat_controls": (
            "candidate_probes_never_count_as_solved",
            "no_nearest_neighbor_shortcut",
            "no_primitive_name_leakage",
            "no_claim_of_regression_win",
        ),
        "promotion_criteria": "Repeated separating evidence plus review can create a candidate primitive.",
        "scoring_layer_compatibility": ("candidate_probe", "hard_mode_unsupported"),
        "confidence_policy": "insufficient_language",
    },
    {
        "level_id": "T6",
        "name": "transfer_family",
        "purpose": "Prove the same latent rule transfers across changed surfaces.",
        "task_signature": "same rule across changes in colors, grid size, shape, distractors, counts, diagonal pressure, or same-color components",
        "required_metadata_fields": (
            "level_id",
            "purpose",
            "task_signature",
            "family_anchor",
            "surface_variants",
            "variant_axes",
            "invariants",
            "confidence_policy",
        ),
        "expected_solver_behavior": "Transfer robustly across all surfaced variants.",
        "expected_failure_mode": "Template lock, color overfit, size overfit, or distractor blindness.",
        "anti_cheat_controls": (
            "minimum_three_surface_variants",
            "no_single_template_repetition",
            "no_same_task_new_color_only_padding",
        ),
        "promotion_criteria": "Becomes regression/scored only after multi-surface proof of the same latent rule.",
        "scoring_layer_compatibility": ("scored", "hard_mode"),
        "confidence_policy": "exact_across_variants",
    },
    {
        "level_id": "T7",
        "name": "self_calibrating_underdetermined",
        "purpose": "Track confidence and distinguish unresolved, low-confidence, and insufficient-evidence states.",
        "task_signature": "evidence may be insufficient by design and the task can be legitimately unresolved",
        "required_metadata_fields": (
            "level_id",
            "purpose",
            "task_signature",
            "confidence_band",
            "resolution_status",
            "rival_grammar_set",
            "more_examples_needed",
            "abstain_policy",
            "confidence_policy",
        ),
        "expected_solver_behavior": "Return unresolved or low-confidence when appropriate; do not force a binary guess.",
        "expected_failure_mode": "Overconfident solve.",
        "anti_cheat_controls": (
            "unresolved_must_be_valid",
            "no_forced_binary_labeling",
            "no_metadata_only_solve_by_inspection",
        ),
        "promotion_criteria": "Becomes hard-mode only when unresolved states are first-class and reviewable.",
        "scoring_layer_compatibility": ("diagnostic", "hard_mode"),
        "confidence_policy": "abstain_or_flag",
    },
)

_LEVEL_LOOKUP_V1 = {definition["level_id"]: definition for definition in LEVEL_DEFINITIONS_V1}

_REQUIRED_CONTRACT_CORE_FIELDS_V1 = (
    "purpose",
    "task_signature",
    "confidence_policy",
    "anti_cheat_controls",
    "scoring_layer_compatibility",
)

_LEAKAGE_FIELDS_V1 = (
    "task_id_shortcut",
    "primitive_name_leakage",
    "sequence_leakage",
)

_LEVEL_SPECIFIC_CONTRACT_RULES_V1 = {
    "T1": {
        "required_any": ("rule_type", "expected_transform"),
        "forbidden_any": ("ordered_operations", "rival_grammars", "separating_examples", "surface_variants", "candidate_primitive_hint", "resolution_status"),
    },
    "T2": {
        "required_any": ("ordered_operations",),
        "forbidden_any": ("rival_grammars", "surface_variants", "candidate_primitive_hint", "resolution_status"),
    },
    "T3": {
        "required_any": ("internal_task_language",),
    },
    "T4": {
        "required_any": ("internal_task_language",),
    },
    "T5": {
        "required_any": ("internal_task_language",),
    },
    "T6": {
        "required_any": ("internal_task_language",),
    },
    "T7": {
        "required_any": ("internal_task_language",),
    },
}

_INTERNAL_TASK_LANGUAGE_FIELDS_V1 = (
    "latent_rule",
    "rival_grammars",
    "separating_examples",
    "ambiguity_axes",
    "composition_graph",
    "novelty_marker",
    "nearest_existing_primitive_set",
    "insufficiency_reason",
    "transfer_family_anchor",
    "surface_variant_axes",
    "confidence_state",
    "unresolved_abstain_policy",
)

_INTERNAL_TASK_LANGUAGE_REQUIRED_FIELDS_V1 = {
    "T3": ("latent_rule", "rival_grammars", "separating_examples", "ambiguity_axes", "confidence_state"),
    "T4": ("latent_rule", "composition_graph", "novelty_marker", "confidence_state"),
    "T5": ("latent_rule", "nearest_existing_primitive_set", "insufficiency_reason", "confidence_state"),
    "T6": ("latent_rule", "transfer_family_anchor", "surface_variant_axes", "confidence_state"),
    "T7": ("latent_rule", "confidence_state", "unresolved_abstain_policy"),
}

_SOLVER_VISIBLE_STRIP_KEYS_V1 = {
    "level_id",
    "purpose",
    "task_signature",
    "confidence_policy",
    "confidence_state",
    "confidence_band",
    "resolution_status",
    "abstain_policy",
    "more_examples_needed",
    "ordered_operations",
    "primitive_chain_length",
    "known_primitives",
    "family_anchor",
    "surface_variants",
    "surface_variant_axes",
    "rival_grammars",
    "separating_examples",
    "ambiguity_axes",
    "composition_graph",
    "nearest_primitive_set",
    "nearest_existing_primitive_set",
    "candidate_primitive_hint",
    "insufficiency_reason",
    "transfer_family_anchor",
    "latent_rule",
    "novelty_marker",
    "internal_task_language",
    "anti_cheat_controls",
    "scoring_layer_compatibility",
    "can_be_counted_as_solved",
    "counted_as_solved",
    "score_result",
    "task_id_shortcut",
    "primitive_name_leakage",
    "sequence_leakage",
}


def _json_safe_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return " ".join(value.split())
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    return _json_safe_text(str(value))


def _as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return deepcopy(value)
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, set):
        return sorted(value, key=repr)
    return [value]


def _task_language_view(contract: Mapping[str, Any]) -> Mapping[str, Any]:
    language = contract.get("internal_task_language")
    return language if isinstance(language, Mapping) else contract


def _strip_solver_visible_key(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): _strip_solver_visible_key(val)
            for key, val in value.items()
            if key not in _SOLVER_VISIBLE_STRIP_KEYS_V1
        }
    if isinstance(value, list):
        return [_strip_solver_visible_key(item) for item in value]
    if isinstance(value, tuple):
        return [_strip_solver_visible_key(item) for item in value]
    if isinstance(value, set):
        return [_strip_solver_visible_key(item) for item in sorted(value, key=repr)]
    return deepcopy(value)


def allowed_task_difficulty_levels_v1() -> tuple[str, ...]:
    return LEVEL_IDS_V1


def get_task_difficulty_level_definitions_v1() -> tuple[dict[str, Any], ...]:
    return tuple(deepcopy(definition) for definition in LEVEL_DEFINITIONS_V1)


def get_task_difficulty_level_definition_v1(level_id: str) -> dict[str, Any]:
    level_id = _json_safe_text(level_id)
    if level_id not in _LEVEL_LOOKUP_V1:
        raise KeyError(f"Unknown task difficulty level: {level_id}")
    return deepcopy(_LEVEL_LOOKUP_V1[level_id])


def task_difficulty_level_definition_issues_v1(level_definition: Any) -> list[str]:
    issues: list[str] = []
    data = _as_mapping(level_definition)
    level_id = _json_safe_text(data.get("level_id"))
    if level_id not in LEVEL_IDS_V1:
        issues.append("invalid_level_id")
    if data.get("name") is None or not _json_safe_text(data.get("name")):
        issues.append("missing_name")
    if data.get("purpose") is None or not _json_safe_text(data.get("purpose")):
        issues.append("missing_purpose")
    if data.get("task_signature") is None or not _json_safe_text(data.get("task_signature")):
        issues.append("missing_task_signature")
    required_metadata_fields = _as_list(data.get("required_metadata_fields"))
    if not required_metadata_fields:
        issues.append("missing_required_metadata_fields")
    if data.get("expected_solver_behavior") is None or not _json_safe_text(data.get("expected_solver_behavior")):
        issues.append("missing_expected_solver_behavior")
    if data.get("expected_failure_mode") is None or not _json_safe_text(data.get("expected_failure_mode")):
        issues.append("missing_expected_failure_mode")
    anti_cheat_controls = _as_list(data.get("anti_cheat_controls"))
    if not anti_cheat_controls:
        issues.append("missing_anti_cheat_controls")
    promotion_criteria = _json_safe_text(data.get("promotion_criteria"))
    if not promotion_criteria:
        issues.append("missing_promotion_criteria")
    scoring_layer_compatibility = _as_list(data.get("scoring_layer_compatibility"))
    if not scoring_layer_compatibility:
        issues.append("missing_scoring_layer_compatibility")
    confidence_policy = _json_safe_text(data.get("confidence_policy"))
    if not confidence_policy:
        issues.append("missing_confidence_policy")
    if level_id in _LEVEL_LOOKUP_V1:
        expected = _LEVEL_LOOKUP_V1[level_id]
        if tuple(required_metadata_fields) != tuple(expected["required_metadata_fields"]):
            issues.append("required_metadata_fields_mismatch")
        if tuple(anti_cheat_controls) != tuple(expected["anti_cheat_controls"]):
            issues.append("anti_cheat_controls_mismatch")
        if tuple(scoring_layer_compatibility) != tuple(expected["scoring_layer_compatibility"]):
            issues.append("scoring_layer_compatibility_mismatch")
        if confidence_policy != expected["confidence_policy"]:
            issues.append("confidence_policy_mismatch")
    return issues


def validate_task_difficulty_level_definition_v1(level_definition: Any) -> dict[str, Any]:
    issues = task_difficulty_level_definition_issues_v1(level_definition)
    if issues:
        raise ValueError(f"Invalid task difficulty level definition: {issues}")
    return deepcopy(_as_mapping(level_definition))


def task_language_fields_for_level_v1(level_id: str) -> tuple[str, ...]:
    level_id = _json_safe_text(level_id)
    if level_id not in LEVEL_IDS_V1:
        raise KeyError(f"Unknown task difficulty level: {level_id}")
    if level_id in _INTERNAL_TASK_LANGUAGE_REQUIRED_FIELDS_V1:
        return _INTERNAL_TASK_LANGUAGE_REQUIRED_FIELDS_V1[level_id]
    return ()


def task_language_issues_v1(level_id: str, task_language: Any) -> list[str]:
    level_id = _json_safe_text(level_id)
    language = _as_mapping(task_language)
    issues: list[str] = []
    if level_id not in LEVEL_IDS_V1:
        issues.append("invalid_level_id")
        return issues
    if level_id in {"T3", "T4", "T5", "T6", "T7"} and not language:
        issues.append("missing_internal_task_language")
        return issues
    required_fields = _INTERNAL_TASK_LANGUAGE_REQUIRED_FIELDS_V1.get(level_id, ())
    for field in required_fields:
        if field not in language or _json_safe_text(language.get(field)) == "" or language.get(field) in ([], {}, ()):
            issues.append(f"missing_task_language_field:{field}")
    if level_id == "T4" and not _json_safe_text(language.get("novelty_marker")):
        issues.append("missing_task_language_field:novelty_marker")
    if level_id == "T5" and not _json_safe_text(language.get("insufficiency_reason")):
        issues.append("missing_task_language_field:insufficiency_reason")
    if level_id == "T6":
        variants = _as_list(language.get("surface_variant_axes"))
        if len(variants) < 3:
            issues.append("surface_variant_axes_too_small")
    if level_id == "T7":
        unresolved_policy = language.get("unresolved_abstain_policy")
        if unresolved_policy in (None, False, "", {}, []):
            issues.append("missing_unresolved_abstain_policy")
    confidence_state = _json_safe_text(language.get("confidence_state"))
    if level_id in {"T3", "T4", "T5", "T6", "T7"} and confidence_state not in {"confident", "low_confidence", "insufficient_evidence", "unresolved"}:
        issues.append("invalid_confidence_state")
    return issues


def validate_task_language_v1(level_id: str, task_language: Any) -> dict[str, Any]:
    issues = task_language_issues_v1(level_id, task_language)
    if issues:
        raise ValueError(f"Invalid task language: {issues}")
    return deepcopy(_as_mapping(task_language))


def export_solver_visible_task_contract_v1(task_contract: Any) -> dict[str, Any]:
    return _strip_solver_visible_key(_as_mapping(task_contract))


def _contract_level_from_fields(contract: Mapping[str, Any]) -> str:
    language = _task_language_view(contract)
    if language.get("confidence_state") in {"unresolved", "low_confidence", "insufficient_evidence"} or language.get("unresolved_abstain_policy"):
        return "T7"
    if language.get("nearest_existing_primitive_set") is not None or contract.get("candidate_primitive_hint") is not None or contract.get("nearest_primitive_set") is not None:
        return "T5"
    surface_variants = language.get("surface_variant_axes")
    if surface_variants is not None:
        if len(_as_list(surface_variants)) >= 3:
            return "T6"
        return "T6"
    if language.get("composition_graph") is not None or contract.get("known_primitives") is not None:
        return "T4"
    if language.get("rival_grammars") is not None or language.get("separating_examples") is not None:
        return "T3"
    if contract.get("ordered_operations") is not None or contract.get("primitive_chain_length") is not None:
        return "T2"
    return "T1"


def classify_task_contract_to_level_v1(task_contract: Any) -> str:
    contract = _as_mapping(task_contract)
    declared = _json_safe_text(contract.get("level_id"))
    if declared:
        if declared not in LEVEL_IDS_V1:
            raise ValueError(f"Unknown task difficulty level: {declared}")
        return declared
    return _contract_level_from_fields(contract)


def task_difficulty_contract_issues_v1(task_contract: Any) -> list[str]:
    issues: list[str] = []
    contract = _as_mapping(task_contract)
    level_id = classify_task_contract_to_level_v1(contract)
    base_fields = [field for field in _REQUIRED_CONTRACT_CORE_FIELDS_V1 if field not in contract]
    if base_fields:
        issues.append(f"missing_core_fields:{','.join(base_fields)}")
    for field in _LEAKAGE_FIELDS_V1:
        if contract.get(field) not in (None, False, [], (), ""):
            issues.append(f"leakage:{field}")
    rules = _LEVEL_SPECIFIC_CONTRACT_RULES_V1[level_id]
    for field in rules.get("required_any", ()):
        value = contract.get(field)
        if value is None or value == [] or value == () or value == "":
            issues.append(f"missing_required_field:{field}")
    for field in rules.get("required_all", ()):
        value = contract.get(field)
        if value is None or value == [] or value == () or value == "":
            issues.append(f"missing_required_field:{field}")
    for field in rules.get("forbidden_any", ()):
        value = contract.get(field)
        if value not in (None, False, [], (), ""):
            issues.append(f"forbidden_field_present:{field}")

    language = _task_language_view(contract)
    if level_id in {"T3", "T4", "T5", "T6", "T7"}:
        language_issues = task_language_issues_v1(level_id, language)
        issues.extend(f"task_language:{issue}" for issue in language_issues)

    if level_id == "T2":
        ops = _as_list(contract.get("ordered_operations"))
        if len(ops) < 2 or len(ops) > 3:
            issues.append("ordered_operations_length_out_of_range")
        if contract.get("intermediate_state_required") is not True:
            issues.append("intermediate_state_required_missing")
    if level_id == "T3":
        rival_grammars = _as_list(language.get("rival_grammars") if isinstance(language, Mapping) else contract.get("rival_grammars"))
        separating_examples = _as_list(language.get("separating_examples") if isinstance(language, Mapping) else contract.get("separating_examples"))
        if len(rival_grammars) < 2:
            issues.append("rival_grammars_too_small")
        if len(separating_examples) < 1:
            issues.append("separating_examples_missing")
    if level_id == "T5":
        if contract.get("can_be_counted_as_solved") is not False:
            issues.append("candidate_probe_counted_as_solved")
        if contract.get("counted_as_solved") is True:
            issues.append("candidate_probe_counted_as_solved")
        if _json_safe_text(contract.get("score_result")) in {"semantic_exact", "exact", "solved"}:
            issues.append("candidate_probe_counted_as_solved")
    if level_id == "T6":
        surface_variants = _as_list(language.get("surface_variant_axes") if isinstance(language, Mapping) else contract.get("surface_variants"))
        if len(surface_variants) < 3:
            issues.append("surface_variants_too_small")
        if contract.get("variant_axes") in (None, [], ()) and language.get("surface_variant_axes") in (None, [], ()):
            issues.append("variant_axes_missing")
    if level_id == "T7":
        confidence_state = _json_safe_text(language.get("confidence_state") if isinstance(language, Mapping) else contract.get("confidence_state"))
        if confidence_state not in {"unresolved", "low_confidence", "needs_more_examples", "insufficient_evidence"}:
            issues.append("resolution_status_invalid")
        if language.get("unresolved_abstain_policy") in (None, False, "", {}, []) and contract.get("abstain_policy") in (None, False, ""):
            issues.append("abstain_policy_missing")
        if contract.get("more_examples_needed") not in (True, False) and language.get("more_examples_needed") not in (True, False):
            issues.append("more_examples_needed_missing")
    return issues


def validate_task_difficulty_contract_v1(task_contract: Any) -> dict[str, Any]:
    issues = task_difficulty_contract_issues_v1(task_contract)
    if issues:
        raise ValueError(f"Invalid task difficulty contract: {issues}")
    return deepcopy(_as_mapping(task_contract))


def list_under_covered_task_difficulty_levels_v1(coverage_snapshot: Any) -> tuple[str, ...]:
    snapshot = _as_mapping(coverage_snapshot)
    counts: Mapping[str, Any] = {}
    for key in DEFAULT_COVERAGE_KEYS_V1:
        candidate = snapshot.get(key)
        if isinstance(candidate, Mapping):
            counts = candidate
            break
    threshold_map = snapshot.get("minimum_coverage_by_level")
    if not isinstance(threshold_map, Mapping):
        threshold_map = DEFAULT_COVERAGE_TARGETS_V1
    under_covered: list[str] = []
    for level_id in LEVEL_IDS_V1:
        threshold = int(threshold_map.get(level_id, DEFAULT_COVERAGE_TARGETS_V1[level_id]))
        count = int(counts.get(level_id, 0) or 0)
        if count < threshold:
            under_covered.append(level_id)
    return tuple(under_covered)


def task_difficulty_ladder_coverage_snapshot_v1(coverage_snapshot: Any) -> dict[str, Any]:
    snapshot = _as_mapping(coverage_snapshot)
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "under_covered_levels": list(list_under_covered_task_difficulty_levels_v1(snapshot)),
        "coverage_snapshot": deepcopy(snapshot),
    }


__all__ = [
    "SCHEMA_VERSION_V1",
    "LEVEL_IDS_V1",
    "LEVEL_DEFINITIONS_V1",
    "allowed_task_difficulty_levels_v1",
    "get_task_difficulty_level_definitions_v1",
    "get_task_difficulty_level_definition_v1",
    "task_difficulty_level_definition_issues_v1",
    "validate_task_difficulty_level_definition_v1",
    "task_language_fields_for_level_v1",
    "task_language_issues_v1",
    "validate_task_language_v1",
    "export_solver_visible_task_contract_v1",
    "classify_task_contract_to_level_v1",
    "task_difficulty_contract_issues_v1",
    "validate_task_difficulty_contract_v1",
    "list_under_covered_task_difficulty_levels_v1",
    "task_difficulty_ladder_coverage_snapshot_v1",
]
