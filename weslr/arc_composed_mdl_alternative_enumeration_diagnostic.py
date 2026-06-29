"""Diagnostic-only composed/MDL alternative enumeration helpers.

This module is deliberately local and side-effect free. It does not mutate
candidate deservedness, runtime wiring, generator decisions, assembler
behaviour, replay decisions, or final-answer behaviour.
"""

from __future__ import annotations

import copy
import itertools
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Optional


_FORBIDDEN_KEYS = {
    "synthetic_expected_answer_for_scoring_only",
    "expected_answer",
    "expected_output",
    "deserved_exact_result",
    "deserved_but_wrong_result",
    "post_ledger_scoring_result",
}

_FUTURE_FAMILY_LAUNDERING_LABELS = {
    "object_correspondence": "object_correspondence_laundered_as_whole_grid_mapping",
    "invariant": "local_invariant_laundered_as_global_transformation",
    "negative_evidence": "absence_of_contradiction_laundered_as_positive_proof",
    "helper_trap": "helper_suggestion_laundered_as_train_evidence",
    "relation_first_rewrite": "local_relation_rewrite_laundered_as_whole_output_rule",
}


@dataclass
class DiagnosticRecord:
    task_id: str = ""
    group_id: str = ""
    candidate_id: str = ""
    candidate_mode: str = ""
    candidate_output_descriptor: str = ""
    family: str = ""
    subclaims: List[str] = field(default_factory=list)
    subclaim_support: List[bool] = field(default_factory=list)
    whole_claim: str = ""
    whole_claim_support: bool = False
    laundering_risk_detected: bool = False
    laundering_type: str = ""
    alternatives_enumerated: bool = False
    alternative_outputs: List[Dict[str, Any]] = field(default_factory=list)
    alternatives_rejected_by_train_evidence: List[Dict[str, Any]] = field(default_factory=list)
    alternatives_not_rejected: List[Dict[str, Any]] = field(default_factory=list)
    competing_grammars_enumerated: bool = False
    competing_grammar_outputs: List[Dict[str, Any]] = field(default_factory=list)
    competing_grammars_rejected_by_train_evidence: List[Dict[str, Any]] = field(default_factory=list)
    missing_proof_fields: List[str] = field(default_factory=list)
    classification_labels: List[str] = field(default_factory=list)
    safe_failure_required: bool = False
    recommended_repair_family: str = ""

    def as_dict(self) -> Dict[str, Any]:
        return asdict(self)


def _bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return bool(value)


def _append_unique(items: List[str], value: str) -> None:
    if value and value not in items:
        items.append(value)


def _assert_no_forbidden_keys(candidate: Mapping[str, Any]) -> None:
    forbidden = sorted(_FORBIDDEN_KEYS.intersection(candidate.keys()))
    if forbidden:
        raise ValueError(f"Forbidden fields present in candidate: {forbidden}")


def _base_record(candidate: Mapping[str, Any], family: str, whole_claim: str) -> DiagnosticRecord:
    return DiagnosticRecord(
        task_id=str(candidate.get("task_id", "")),
        group_id=str(candidate.get("group_id", "")),
        candidate_id=str(candidate.get("candidate_id", "")),
        candidate_mode=str(candidate.get("candidate_mode", "")),
        candidate_output_descriptor=str(
            candidate.get("candidate_output_descriptor", candidate.get("output_descriptor", ""))
        ),
        family=family,
        whole_claim=whole_claim,
    )


def _normalise_components(candidate: Mapping[str, Any]) -> List[Dict[str, Any]]:
    components = candidate.get("components", []) or []
    support_map = candidate.get("component_support", {}) or {}
    normalised: List[Dict[str, Any]] = []
    for index, component in enumerate(components):
        if isinstance(component, Mapping):
            name = str(component.get("name", component.get("component_id", f"component_{index}")))
            support = _bool(
                component.get("train_supported", component.get("supported", support_map.get(name, False)))
            )
        else:
            name = str(component)
            support = _bool(support_map.get(name, False))
        normalised.append({"name": name, "supported": support})
    return normalised


def _make_alternative_record(
    alternative_id: str,
    alternative_kind: str,
    *,
    covers_train_pairs: bool = False,
    explicit_train_rejection_found: bool = False,
    train_support_scope: str = "subclaim_only",
    produces_candidate_output_descriptor: bool = False,
    produces_distinct_output_descriptor: bool = False,
    enumeration_status: str = "identified",
    components: Optional[List[str]] = None,
    component_order: Optional[List[str]] = None,
    interaction_assumption: str = "",
    description_complexity_band: str = "same_band",
    negative_evidence_against_grammar: bool = False,
) -> Dict[str, Any]:
    return {
        "alternative_id": alternative_id,
        "alternative_kind": alternative_kind,
        "components": list(components or []),
        "component_order": list(component_order or []),
        "interaction_assumption": interaction_assumption,
        "covers_train_pairs": covers_train_pairs,
        "fails_train_pairs": not covers_train_pairs,
        "train_support_scope": train_support_scope,
        "produces_candidate_output_descriptor": produces_candidate_output_descriptor,
        "produces_distinct_output_descriptor": produces_distinct_output_descriptor,
        "explicit_train_rejection_found": explicit_train_rejection_found,
        "train_rejection_reason": "train_rejected" if explicit_train_rejection_found else "",
        "enumeration_status": enumeration_status,
        "description_complexity_band": description_complexity_band,
        "negative_evidence_against_grammar": negative_evidence_against_grammar,
    }


def _classify_evidence_path(
    record: DiagnosticRecord,
    *,
    identified: bool,
    unrejected_viable: bool,
    rejected_any: bool,
    missing_proof: bool,
    competing_output_identified: bool = False,
    competing_output_rejected: bool = False,
) -> None:
    if identified:
        _append_unique(record.classification_labels, "alternative_identified")
    else:
        _append_unique(record.classification_labels, "alternative_not_identified")

    if competing_output_identified:
        _append_unique(record.classification_labels, "competing_output_identified")
    if competing_output_rejected:
        _append_unique(record.classification_labels, "competing_output_rejected")

    if unrejected_viable:
        _append_unique(record.classification_labels, "alternative_rejection_missing")
        _append_unique(record.classification_labels, "direct_counterexample_found")
    elif rejected_any:
        _append_unique(record.classification_labels, "alternative_rejection_proven")
    else:
        _append_unique(record.classification_labels, "alternative_rejection_missing")

    if missing_proof and not unrejected_viable:
        _append_unique(record.classification_labels, "missing_proof_only")


def _enumerate_composed(candidate: Mapping[str, Any]) -> DiagnosticRecord:
    record = _base_record(candidate, "composed_transform", "whole_composition_forced")
    components = _normalise_components(candidate)
    record.subclaims = [component["name"] for component in components]
    record.subclaim_support = [component["supported"] for component in components]

    if not components:
        record.missing_proof_fields.append("components")
        _append_unique(record.classification_labels, "alternative_not_identified")
        _append_unique(record.classification_labels, "alternative_rejection_missing")
        _append_unique(record.classification_labels, "missing_proof_only")
        _append_unique(record.classification_labels, "insufficient_alternative_search")
        record.safe_failure_required = True
        record.recommended_repair_family = "composed_transform_forcedness_audit"
        return record

    component_names = [component["name"] for component in components]
    all_components_supported = all(record.subclaim_support)
    order_forced = _bool(candidate.get("component_order_forced"))
    interaction_proven = _bool(candidate.get("component_interaction_proven"))
    full_train_cover = _bool(
        candidate.get(
            "full_ordered_composition_explains_all_train_pairs",
            candidate.get("full_composition_explains_all_train_pairs", False),
        )
    )
    claimed_whole_forced = _bool(
        candidate.get("full_composition_forced", candidate.get("whole_composition_claimed_forced", False))
    )
    search_sufficient = _bool(candidate.get("alternative_search_sufficient", len(components) > 1))

    alternatives: List[Dict[str, Any]] = []

    original_order = tuple(component_names)
    for index, permutation in enumerate(itertools.permutations(component_names)):
        if permutation == original_order:
            continue
        if len(alternatives) >= 6:
            break
        alternatives.append(
            _make_alternative_record(
                f"order_{index}",
                "alternative_component_order",
                components=list(permutation),
                component_order=list(permutation),
                covers_train_pairs=_bool(candidate.get("alternative_orders_viable", False)),
                explicit_train_rejection_found=_bool(candidate.get("alternative_orders_rejected_by_train", False)),
                train_support_scope="all_train_pairs" if _bool(candidate.get("alternative_orders_viable", False)) else "partial_train_pairs",
                produces_distinct_output_descriptor=_bool(candidate.get("alternative_orders_produce_distinct_output", True)),
            )
        )

    if len(component_names) > 1:
        subset = component_names[:-1]
        alternatives.append(
            _make_alternative_record(
                "subset_0",
                "alternative_component_subset",
                components=subset,
                component_order=subset,
                covers_train_pairs=_bool(candidate.get("alternative_subset_viable", False)),
                explicit_train_rejection_found=_bool(candidate.get("alternative_subset_rejected_by_train", False)),
                train_support_scope="partial_train_pairs",
                produces_distinct_output_descriptor=_bool(candidate.get("alternative_subset_produces_distinct_output", True)),
            )
        )

    if len(component_names) > 1:
        for index, name in enumerate(component_names[:3]):
            alternatives.append(
                _make_alternative_record(
                    f"partial_{index}",
                    "partial_transform",
                    components=[name],
                    component_order=[name],
                    covers_train_pairs=_bool(candidate.get("partial_transform_viable", False)),
                    explicit_train_rejection_found=_bool(candidate.get("partial_transform_rejected_by_train", False)),
                    train_support_scope="subclaim_only",
                    produces_distinct_output_descriptor=_bool(candidate.get("partial_transform_produces_distinct_output", True)),
                )
            )

    for index, assumption in enumerate(candidate.get("alternative_interaction_assumptions", []) or []):
        alternatives.append(
            _make_alternative_record(
                f"interaction_{index}",
                "alternative_interaction_assumption",
                components=component_names,
                component_order=component_names,
                interaction_assumption=str(assumption),
                covers_train_pairs=_bool(candidate.get("alternative_interaction_viable", False)),
                explicit_train_rejection_found=_bool(candidate.get("alternative_interaction_rejected_by_train", False)),
                train_support_scope="all_train_pairs" if _bool(candidate.get("alternative_interaction_viable", False)) else "partial_train_pairs",
                produces_distinct_output_descriptor=_bool(candidate.get("alternative_interaction_produces_distinct_output", True)),
            )
        )

    for index, full_alternative in enumerate(candidate.get("alternative_full_compositions", []) or []):
        alt_components = full_alternative.get("components", component_names) if isinstance(full_alternative, Mapping) else component_names
        alternatives.append(
            _make_alternative_record(
                f"full_{index}",
                "alternative_full_composition",
                components=list(alt_components),
                component_order=list(alt_components),
                covers_train_pairs=_bool(
                    full_alternative.get("covers_train_pairs", candidate.get("alternative_full_composition_viable", False))
                    if isinstance(full_alternative, Mapping)
                    else candidate.get("alternative_full_composition_viable", False)
                ),
                explicit_train_rejection_found=_bool(
                    full_alternative.get("explicit_train_rejection_found", candidate.get("alternative_full_composition_rejected_by_train", False))
                    if isinstance(full_alternative, Mapping)
                    else candidate.get("alternative_full_composition_rejected_by_train", False)
                ),
                train_support_scope="all_train_pairs",
                produces_distinct_output_descriptor=_bool(
                    full_alternative.get("produces_distinct_output_descriptor", True)
                    if isinstance(full_alternative, Mapping)
                    else True
                ),
            )
        )

    if all_components_supported and len(component_names) > 1:
        alternatives.append(
            _make_alternative_record(
                "component_only",
                "component_only_explanation",
                components=component_names,
                component_order=component_names,
                covers_train_pairs=not full_train_cover,
                explicit_train_rejection_found=False,
                train_support_scope="subclaim_only",
                produces_candidate_output_descriptor=True,
                produces_distinct_output_descriptor=False,
            )
        )

    explicit_records = [alt for alt in alternatives if alt["enumeration_status"] == "identified"]
    viable_unrejected = [
        alt
        for alt in explicit_records
        if alt["covers_train_pairs"] and not alt["explicit_train_rejection_found"]
    ]
    rejected = [alt for alt in explicit_records if alt["explicit_train_rejection_found"]]

    record.alternatives_enumerated = bool(explicit_records)
    record.alternative_outputs = explicit_records
    record.alternatives_rejected_by_train_evidence = rejected
    record.alternatives_not_rejected = viable_unrejected

    record.whole_claim_support = bool(
        order_forced and interaction_proven and full_train_cover and not viable_unrejected and all_components_supported
    )

    if not order_forced:
        _append_unique(record.classification_labels, "component_order_unproven")
    if not interaction_proven:
        _append_unique(record.classification_labels, "component_interaction_unproven")
    if not record.whole_claim_support:
        _append_unique(record.classification_labels, "whole_composition_not_train_forced")
    if all_components_supported and not record.whole_claim_support:
        _append_unique(record.classification_labels, "component_support_only")

    for kind, label in {
        "alternative_component_order": "alternative_order_viable_unrejected",
        "alternative_component_subset": "alternative_subset_viable_unrejected",
        "alternative_full_composition": "alternative_full_composition_viable_unrejected",
        "partial_transform": "partial_transform_viable_unrejected",
    }.items():
        if any(alt["alternative_kind"] == kind for alt in viable_unrejected):
            _append_unique(record.classification_labels, label)

    missing_proof = not record.whole_claim_support and (not explicit_records or not search_sufficient)
    if not search_sufficient:
        _append_unique(record.classification_labels, "insufficient_alternative_search")
        record.missing_proof_fields.append("alternative_search")

    if claimed_whole_forced and all_components_supported and not record.whole_claim_support:
        record.laundering_risk_detected = True
        record.laundering_type = "component_forcedness_laundered_as_composition_forcedness"
        _append_unique(
            record.classification_labels,
            "component_forcedness_laundered_as_composition_forcedness",
        )

    _classify_evidence_path(
        record,
        identified=bool(explicit_records),
        unrejected_viable=bool(viable_unrejected),
        rejected_any=bool(rejected),
        missing_proof=missing_proof,
    )
    record.safe_failure_required = bool(viable_unrejected or missing_proof)
    record.recommended_repair_family = "composed_transform_forcedness_audit"
    return record


def _normalise_competing_grammars(candidate: Mapping[str, Any]) -> List[Dict[str, Any]]:
    records: List[Dict[str, Any]] = []
    for index, grammar in enumerate(candidate.get("competing_grammar_records", []) or []):
        if isinstance(grammar, Mapping):
            records.append(
                _make_alternative_record(
                    str(grammar.get("grammar_id", f"grammar_{index}")),
                    str(grammar.get("grammar_kind", "same_train_different_test_output")),
                    covers_train_pairs=_bool(grammar.get("fits_train_pairs", grammar.get("covers_train_pairs", False))),
                    explicit_train_rejection_found=_bool(grammar.get("explicit_train_rejection_found", False)),
                    train_support_scope="all_train_pairs" if _bool(grammar.get("fits_train_pairs", False)) else "partial_train_pairs",
                    produces_candidate_output_descriptor=_bool(grammar.get("produces_candidate_output_descriptor", False)),
                    produces_distinct_output_descriptor=_bool(grammar.get("produces_distinct_output_descriptor", True)),
                    description_complexity_band=str(grammar.get("description_complexity_band", "same_band")),
                    negative_evidence_against_grammar=_bool(grammar.get("negative_evidence_against_grammar", False)),
                )
            )
    competing = candidate.get("competing_grammars", []) or []
    for index, grammar in enumerate(competing):
        if isinstance(grammar, Mapping):
            grammar_id = str(grammar.get("grammar_id", f"competing_{index}"))
            grammar_kind = str(grammar.get("grammar_kind", grammar.get("kind", "simpler_grammar")))
            rejected = _bool(grammar.get("explicit_train_rejection_found", False))
            fits_train = _bool(grammar.get("fits_train_pairs", True))
            distinct_output = _bool(grammar.get("produces_distinct_output_descriptor", True))
            band = str(grammar.get("description_complexity_band", "same_band"))
            negative = _bool(grammar.get("negative_evidence_against_grammar", False))
        else:
            grammar_id = str(grammar)
            grammar_kind = "simpler_grammar"
            rejected = _bool((candidate.get("competing_grammar_rejected", {}) or {}).get(grammar_id, False))
            fits_train = True
            distinct_output = True
            band = "simpler"
            negative = False
        records.append(
            _make_alternative_record(
                grammar_id,
                grammar_kind,
                covers_train_pairs=fits_train,
                explicit_train_rejection_found=rejected,
                train_support_scope="all_train_pairs" if fits_train else "partial_train_pairs",
                produces_distinct_output_descriptor=distinct_output,
                description_complexity_band=band,
                negative_evidence_against_grammar=negative,
            )
        )
    for index, descriptor in enumerate(candidate.get("same_train_different_test_output", []) or []):
        records.append(
            _make_alternative_record(
                f"same_train_diff_output_{index}",
                "same_train_different_test_output",
                covers_train_pairs=True,
                explicit_train_rejection_found=_bool(candidate.get("same_train_different_test_output_rejected", False)),
                train_support_scope="all_train_pairs",
                produces_distinct_output_descriptor=True,
            )
        )
    return records


def _enumerate_mdl(candidate: Mapping[str, Any]) -> DiagnosticRecord:
    family = str(candidate.get("family", "explicit_grammar"))
    record = _base_record(candidate, family, "grammar_forced_by_train")

    simplicity_primary = _bool(
        candidate.get("simplicity_primary_evidence", candidate.get("grammar_complexity") == "simple")
    )
    grammar_explains_all = _bool(
        candidate.get("grammar_explains_all_train_pairs", candidate.get("train_pairs_explained", False))
    )
    negative_evidence = _bool(candidate.get("negative_evidence_present", False))
    search_sufficient = _bool(candidate.get("competing_grammar_search_sufficient", False))
    claimed_forced = _bool(candidate.get("grammar_forced_by_train_claimed", grammar_explains_all))

    accepted_grammar = str(candidate.get("accepted_grammar", candidate.get("grammar_id", "accepted_grammar")))
    record.subclaims = [accepted_grammar]
    record.subclaim_support = [grammar_explains_all]

    competing = _normalise_competing_grammars(candidate)
    rejected = [grammar for grammar in competing if grammar["explicit_train_rejection_found"]]
    unrejected_distinct = [
        grammar
        for grammar in competing
        if grammar["covers_train_pairs"]
        and grammar["produces_distinct_output_descriptor"]
        and not grammar["explicit_train_rejection_found"]
    ]

    record.competing_grammars_enumerated = bool(competing)
    record.competing_grammar_outputs = competing
    record.competing_grammars_rejected_by_train_evidence = rejected
    record.alternatives_not_rejected = unrejected_distinct
    record.alternatives_enumerated = bool(competing)
    record.alternative_outputs = competing
    record.alternatives_rejected_by_train_evidence = rejected

    record.whole_claim_support = bool(
        grammar_explains_all
        and (bool(competing) or search_sufficient)
        and not unrejected_distinct
        and (negative_evidence or not simplicity_primary)
    )

    if simplicity_primary:
        _append_unique(record.classification_labels, "simplicity_as_primary_evidence")
    if not grammar_explains_all:
        _append_unique(record.classification_labels, "grammar_not_proven_on_all_train_pairs")
    if not competing:
        _append_unique(record.classification_labels, "competing_grammar_unenumerated")
        record.missing_proof_fields.append("competing_grammars")
    if not any(grammar["produces_distinct_output_descriptor"] for grammar in competing):
        _append_unique(record.classification_labels, "competing_output_unenumerated")
    if simplicity_primary and not negative_evidence:
        _append_unique(record.classification_labels, "negative_evidence_missing")
    if simplicity_primary and unrejected_distinct:
        _append_unique(record.classification_labels, "attractive_wrong_simple_rule_unrejected")
    if not search_sufficient and not competing:
        _append_unique(record.classification_labels, "insufficient_alternative_search")
        record.missing_proof_fields.append("competing_grammar_search")

    if claimed_forced and simplicity_primary and not record.whole_claim_support:
        record.laundering_risk_detected = True
        record.laundering_type = "simplicity_laundered_as_train_forcing"
        _append_unique(record.classification_labels, "simplicity_laundered_as_train_forcing")

    missing_proof = not record.whole_claim_support and (not competing or not search_sufficient)
    _classify_evidence_path(
        record,
        identified=bool(competing),
        unrejected_viable=bool(unrejected_distinct),
        rejected_any=bool(rejected),
        missing_proof=missing_proof,
        competing_output_identified=any(grammar["produces_distinct_output_descriptor"] for grammar in competing),
        competing_output_rejected=bool(
            competing and not unrejected_distinct and any(grammar["produces_distinct_output_descriptor"] for grammar in rejected)
        ),
    )
    record.safe_failure_required = bool(unrejected_distinct or missing_proof)
    record.recommended_repair_family = "mdl_forcedness_audit"
    return record


def _unsupported_family(candidate: Mapping[str, Any]) -> DiagnosticRecord:
    family = str(candidate.get("family", ""))
    record = _base_record(candidate, family, "whole_claim_forced")
    _append_unique(record.classification_labels, "insufficient_alternative_search")
    label = _FUTURE_FAMILY_LAUNDERING_LABELS.get(family, "")
    if label:
        record.recommended_repair_family = label
    else:
        record.recommended_repair_family = "future_family_laundering_audit"
    record.safe_failure_required = True
    return record


def diagnose(candidate: Mapping[str, Any]) -> Dict[str, Any]:
    candidate_copy = copy.deepcopy(dict(candidate))
    family = str(candidate_copy.get("family", ""))
    mode = str(candidate_copy.get("candidate_mode", ""))
    if family == "composed_transform" or mode == "composed_transform_candidate":
        return _enumerate_composed(candidate_copy).as_dict()
    if family in {"explicit_grammar", "mdl_trap"} or mode == "explicit_grammar_candidate":
        return _enumerate_mdl(candidate_copy).as_dict()
    return _unsupported_family(candidate_copy).as_dict()


def diagnose_safe(candidate: Mapping[str, Any]) -> Dict[str, Any]:
    _assert_no_forbidden_keys(candidate)
    return diagnose(candidate)


__all__ = ["DiagnosticRecord", "diagnose", "diagnose_safe"]
