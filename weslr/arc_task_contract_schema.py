"""ARC Synthetic TaskContract schema helpers.

Deterministic, metadata-only, and fail-closed.
This module reuses the validated T1–T7 difficulty ladder and the internal
examiner/oracle task-language rules.

It does not run solvers, scoring, runtime/chat/UI/provider paths, `.weslr` IO,
or external actions.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Iterable, Mapping

from weslr.arc_task_difficulty_ladder import (
    LEVEL_IDS_V1,
    classify_task_contract_to_level_v1 as _classify_ladder_level,
    task_language_issues_v1,
    validate_task_language_v1,
)

SCHEMA_VERSION_V1 = "arc_synthetic_task_contract_schema_v1"
SCORING_LAYERS_V1 = ("base", "hard_mode", "probe", "sentinel", "diagnostic")
PROBE_LAYERS_V1 = {"probe", "sentinel", "diagnostic"}

_SOLVER_VISIBLE_ALLOWED_FIELDS_V1 = (
    "task_id",
    "task_family",
    "scoring_layer",
    "visible_examples",
    "required_abstraction",
    "hardness_dimensions",
)

_INTERNAL_FIELDS_TO_STRIP_V1 = {
    "difficulty_level",
    "level_id",
    "latent_rule",
    "required_primitives",
    "primitive_name",
    "primitive_names",
    "primitive_chain",
    "operation_sequence",
    "confidence_policy",
    "oracle_metadata",
    "expected_output",
    "internal_task_language",
    "rival_grammars",
    "separating_examples",
    "ambiguity_axes",
    "transfer_variants",
    "insufficiency_reason",
    "abstain_policy",
    "confidence_state",
    "held_out_test_case",
    "task_level",
}

_REQUIRED_CORE_FIELDS_V1 = (
    "task_id",
    "task_family",
    "difficulty_level",
    "scoring_layer",
    "visible_examples",
    "held_out_test_case",
    "expected_output",
    "required_abstraction",
    "hardness_dimensions",
    "confidence_policy",
    "abstain_policy",
    "expected_failure_mode",
    "oracle_metadata",
    "solver_visible_view",
    "can_be_counted_as_solved",
)

_LEVEL_SPECIFIC_REQUIRED_FIELDS_V1 = {
    "T1": ("required_primitives",),
    "T2": ("primitive_chain",),
    "T3": ("latent_rule", "rival_grammars", "separating_examples", "ambiguity_axes", "confidence_state"),
    "T4": ("latent_rule", "composition_graph", "novelty_marker", "confidence_state"),
    "T5": ("latent_rule", "nearest_primitive_set", "insufficiency_reason", "confidence_state"),
    "T6": ("latent_rule", "transfer_anchor", "transfer_variants", "confidence_state"),
    "T7": ("latent_rule", "confidence_state", "abstain_policy"),
}

_LEVEL_INTERNAL_LANGUAGE_FIELDS_V1 = {
    "T3": ("latent_rule", "rival_grammars", "separating_examples", "ambiguity_axes", "confidence_state"),
    "T4": ("latent_rule", "composition_graph", "novelty_marker", "confidence_state"),
    "T5": ("latent_rule", "nearest_existing_primitive_set", "insufficiency_reason", "confidence_state"),
    "T6": ("latent_rule", "transfer_family_anchor", "surface_variant_axes", "confidence_state"),
    "T7": ("latent_rule", "confidence_state", "unresolved_abstain_policy"),
}

_TASK_LANGUAGE_FIELD_ALIASES_V1 = {
    "T3": (("latent_rule",), ("rival_grammars",), ("separating_examples",), ("ambiguity_axes",), ("confidence_state",)),
    "T4": (("latent_rule",), ("composition_graph",), ("novelty_marker",), ("confidence_state",)),
    "T5": (("latent_rule",), ("nearest_primitive_set", "nearest_existing_primitive_set"), ("insufficiency_reason",), ("confidence_state",)),
    "T6": (("latent_rule",), ("transfer_anchor", "transfer_family_anchor"), ("transfer_variants", "surface_variant_axes"), ("confidence_state",)),
    "T7": (("latent_rule",), ("confidence_state",), ("abstain_policy", "unresolved_abstain_policy")),
}

_LEVEL_SPECIFIC_FORBIDDEN_FIELDS_V1 = {
    "T5": ("can_be_counted_as_solved",),
    "T7": (),
}


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


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return " ".join(value.split())
    return " ".join(str(value).split())


def _nonempty(value: Any) -> bool:
    return bool(_text(value))


def _json_safe(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_safe(val) for key, val in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, set):
        return [_json_safe(item) for item in sorted(value, key=repr)]
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    return _text(value)


def _compact(values: Iterable[Any]) -> list[Any]:
    return [item for item in values if item is not None]


def _strip_for_solver_visible(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): _strip_for_solver_visible(val)
            for key, val in value.items()
            if key in _SOLVER_VISIBLE_ALLOWED_FIELDS_V1 or key not in _INTERNAL_FIELDS_TO_STRIP_V1
        }
    if isinstance(value, list):
        return [_strip_for_solver_visible(item) for item in value]
    if isinstance(value, tuple):
        return [_strip_for_solver_visible(item) for item in value]
    if isinstance(value, set):
        return [_strip_for_solver_visible(item) for item in sorted(value, key=repr)]
    return deepcopy(value)


def _task_language_view(contract: Mapping[str, Any]) -> Mapping[str, Any]:
    direct_keys = (
        "latent_rule",
        "rival_grammars",
        "separating_examples",
        "ambiguity_axes",
        "composition_graph",
        "novelty_marker",
        "nearest_primitive_set",
        "transfer_anchor",
        "transfer_variants",
        "insufficiency_reason",
        "confidence_state",
        "unresolved_abstain_policy",
    )
    if any(key in contract for key in direct_keys):
        return contract
    oracle = _as_mapping(contract.get("oracle_metadata"))
    language = oracle.get("internal_task_language")
    if isinstance(language, Mapping):
        return language
    return oracle


def _infer_level_from_internal(contract: Mapping[str, Any]) -> str:
    language = _task_language_view(contract)
    candidate = {
        "level_id": contract.get("difficulty_level"),
        **_as_mapping(language),
    }
    if _nonempty(language.get("confidence_state")) and _text(language.get("unresolved_abstain_policy")):
        return "T7"
    if _nonempty(language.get("transfer_anchor")) or len(_as_list(language.get("transfer_variants"))) >= 3:
        return "T6"
    if _nonempty(language.get("nearest_primitive_set")) or _nonempty(language.get("insufficiency_reason")):
        return "T5"
    if _nonempty(language.get("composition_graph")) or _nonempty(language.get("novelty_marker")):
        return "T4"
    if _as_list(language.get("rival_grammars")) or _as_list(language.get("separating_examples")):
        return "T3"
    return _classify_ladder_level(candidate)


def _require_nonempty(contract: Mapping[str, Any], field: str, issues: list[str]) -> None:
    if not _nonempty(contract.get(field)):
        issues.append(f"missing_field:{field}")


def _require_any(contract: Mapping[str, Any], names: tuple[str, ...], issues: list[str], issue_name: str) -> None:
    if not any(_nonempty(contract.get(name)) for name in names):
        issues.append(issue_name)


def task_contract_leakage_issues_v1(task_contract: Any) -> list[str]:
    contract = _as_mapping(task_contract)
    issues: list[str] = []
    visible_source = contract.get("solver_visible_view") if isinstance(contract.get("solver_visible_view"), Mapping) else contract
    visible = _as_mapping(visible_source)

    leakage_fields = {
        "difficulty_level": "task_level",
        "level_id": "task_level",
        "primitive_name": "primitive_name",
        "primitive_names": "primitive_name",
        "primitive_chain": "operation_sequence",
        "operation_sequence": "operation_sequence",
        "latent_rule": "latent_rule",
        "rival_grammars": "rival_grammars",
        "confidence_policy": "confidence_policy",
        "oracle_metadata": "oracle_metadata",
        "expected_output": "expected_output",
        "internal_task_language": "oracle_metadata",
        "insufficiency_reason": "insufficiency_reason",
    }

    def _scan(value: Any) -> None:
        if isinstance(value, Mapping):
            for key, nested in value.items():
                issue = leakage_fields.get(key)
                if issue is not None:
                    if issue == "task_level" and _text(nested) not in LEVEL_IDS_V1:
                        pass
                    elif nested not in (None, [], {}, ()):
                        issues.append(f"leakage:{issue}")
                _scan(nested)
        elif isinstance(value, list):
            for nested in value:
                _scan(nested)

    _scan(visible)
    _scan(contract)
    return issues


def detect_task_contract_leakage(task_contract: Any) -> list[str]:
    return task_contract_leakage_issues_v1(task_contract)


def export_solver_visible_task(task_contract: Any) -> dict[str, Any]:
    contract = _as_mapping(task_contract)
    visible_source = contract.get("solver_visible_view") if isinstance(contract.get("solver_visible_view"), Mapping) else contract
    visible = _strip_for_solver_visible(visible_source)
    if not isinstance(visible, dict):
        return {}
    return {key: visible[key] for key in _SOLVER_VISIBLE_ALLOWED_FIELDS_V1 if key in visible}


def validate_task_contract(task_contract: Any) -> dict[str, Any]:
    contract = _as_mapping(task_contract)
    issues: list[str] = []
    for field in _REQUIRED_CORE_FIELDS_V1:
        _require_nonempty(contract, field, issues)
    difficulty_level = _text(contract.get("difficulty_level"))
    if difficulty_level not in LEVEL_IDS_V1:
        issues.append("invalid_difficulty_level")

    scoring_layer = _text(contract.get("scoring_layer"))
    if scoring_layer not in SCORING_LAYERS_V1:
        issues.append("invalid_scoring_layer")

    visible_examples = _as_list(contract.get("visible_examples"))
    if not visible_examples:
        issues.append("missing_field:visible_examples")
    if contract.get("held_out_test_case") in (None, {}, [], ()):
        issues.append("missing_field:held_out_test_case")
    if contract.get("expected_output") in (None, {}, [], ()):
        issues.append("missing_field:expected_output")
    if contract.get("hardness_dimensions") in (None, {}, [], ()):
        issues.append("missing_field:hardness_dimensions")
    if contract.get("can_be_counted_as_solved") not in (True, False):
        issues.append("missing_field:can_be_counted_as_solved")

    oracle = _as_mapping(contract.get("oracle_metadata"))
    language = _task_language_view(contract)
    required_level_fields = _LEVEL_SPECIFIC_REQUIRED_FIELDS_V1.get(difficulty_level, ())
    for field in required_level_fields:
        _require_nonempty(contract, field, issues)
    if difficulty_level in {"T3", "T4", "T5", "T6", "T7"}:
        aliases = _TASK_LANGUAGE_FIELD_ALIASES_V1[difficulty_level]
        for alias_names in aliases:
            _require_any(contract, alias_names, issues, f"missing_field:{alias_names[0]}")
        language_issues = task_language_issues_v1(difficulty_level, language)
        issues.extend(f"task_language:{issue}" for issue in language_issues)
    if difficulty_level == "T5" and contract.get("can_be_counted_as_solved") is True:
        issues.append("candidate_probe_counted_as_solved")
    if scoring_layer in PROBE_LAYERS_V1 and contract.get("can_be_counted_as_solved") is True:
        issues.append("probe_or_sentinel_counted_as_solved")
    if scoring_layer in {"probe", "sentinel"} and contract.get("can_be_counted_as_solved") is True:
        issues.append("probe_or_sentinel_counted_as_solved")
    if difficulty_level == "T7" and _text(_task_language_view(contract).get("confidence_state")) == "" and _text(contract.get("abstain_policy")) == "":
        issues.append("missing_t7_resolution_state")

    export_view = export_solver_visible_task(contract)
    leakage_issues = task_contract_leakage_issues_v1({"solver_visible_view": export_view})
    issues.extend(leakage_issues)
    if issues:
        raise ValueError(f"Invalid task contract: {issues}")

    validated = deepcopy(contract)
    validated["solver_visible_view"] = export_view
    return validated


def classify_task_contract_level(task_contract: Any) -> str:
    contract = _as_mapping(task_contract)
    difficulty_level = _text(contract.get("difficulty_level"))
    if difficulty_level in LEVEL_IDS_V1:
        return difficulty_level
    return _infer_level_from_internal(contract)


def task_contract_can_be_scored(task_contract: Any) -> bool:
    contract = _as_mapping(task_contract)
    scoring_layer = _text(contract.get("scoring_layer"))
    if scoring_layer not in {"base", "hard_mode"}:
        return False
    if contract.get("can_be_counted_as_solved") is not True:
        return False
    level = classify_task_contract_level(contract)
    if level == "T5":
        return False
    return True


def summarize_task_contract_coverage(task_contracts: Any) -> dict[str, Any]:
    if isinstance(task_contracts, Mapping):
        items = list(task_contracts.values())
    else:
        items = list(task_contracts or [])
    level_counts = {level: 0 for level in LEVEL_IDS_V1}
    scoring_counts = {layer: 0 for layer in SCORING_LAYERS_V1}
    scored_total = 0
    non_counting_false_total = 0
    non_counting_task_ids: list[str] = []
    probe_task_ids: list[str] = []
    sentinel_task_ids: list[str] = []
    t5_primitive_insufficiency_task_ids: list[str] = []
    t7_unresolved_task_ids: list[str] = []

    def _append_unique(target: list[str], task_id: str) -> None:
        if task_id and task_id not in target:
            target.append(task_id)

    for contract in items:
        mapping = _as_mapping(contract)
        level = classify_task_contract_level(mapping)
        if level in level_counts:
            level_counts[level] += 1
        layer = _text(mapping.get("scoring_layer"))
        if layer in scoring_counts:
            scoring_counts[layer] += 1
        task_id = _text(mapping.get("task_id"))
        if mapping.get("can_be_counted_as_solved") is False:
            non_counting_false_total += 1
        if not task_contract_can_be_scored(mapping):
            _append_unique(non_counting_task_ids, task_id)
        if level == "T5":
            _append_unique(t5_primitive_insufficiency_task_ids, task_id)
        if layer == "probe":
            _append_unique(probe_task_ids, task_id)
        if layer == "sentinel":
            _append_unique(sentinel_task_ids, task_id)
        language = _task_language_view(mapping)
        confidence_state = _text(language.get("confidence_state"))
        abstain_policy = _text(language.get("abstain_policy")) or _text(language.get("unresolved_abstain_policy"))
        if level == "T7" and (confidence_state in {"unresolved", "low_confidence", "insufficient_evidence"} or abstain_policy):
            _append_unique(t7_unresolved_task_ids, task_id)
        if task_contract_can_be_scored(mapping):
            scored_total += 1

    return {
        "schema_version": SCHEMA_VERSION_V1,
        "total_contracts": len(items),
        "counts_by_level": level_counts,
        "counts_by_scoring_layer": scoring_counts,
        "scored_total": scored_total,
        "can_be_counted_as_solved_false_total": non_counting_false_total,
        "non_counting_task_ids": non_counting_task_ids,
        "probe_task_ids": probe_task_ids,
        "sentinel_task_ids": sentinel_task_ids,
        "t5_primitive_insufficiency_task_ids": t5_primitive_insufficiency_task_ids,
        "t7_unresolved_task_ids": t7_unresolved_task_ids,
        "probe_or_sentinel_total": scoring_counts["probe"] + scoring_counts["sentinel"] + scoring_counts["diagnostic"],
    }


__all__ = [
    "SCHEMA_VERSION_V1",
    "SCORING_LAYERS_V1",
    "detect_task_contract_leakage",
    "export_solver_visible_task",
    "validate_task_contract",
    "classify_task_contract_level",
    "task_contract_can_be_scored",
    "summarize_task_contract_coverage",
]
