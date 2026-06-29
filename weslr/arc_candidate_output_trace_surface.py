"""ARC candidate-output and trace-surface schema helpers.

Schema/helper-only module.
Does not load expected answers.
Does not wire replay scoring.
Does not affect generator or assembler deservedness.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any
import json

CANDIDATE_OUTPUT_SURFACE_SCHEMA_VERSION = "arc_candidate_output_surface_v1"
CANDIDATE_TRACE_SURFACE_SCHEMA_VERSION = "arc_candidate_trace_surface_v1"
COMPOSED_TRACE_SURFACE_SCHEMA_VERSION = "arc_composed_trace_surface_v1"
MDL_TRACE_SURFACE_SCHEMA_VERSION = "arc_mdl_trace_surface_v1"

ALLOWED_OUTPUT_TYPES = {
    "grid_int_matrix",
    "grid_symbolic_matrix",
    "object_graph_projection",
    "descriptor_only",
    "grammar_emitted_grid",
    "intermediate_only",
    "missing",
}

ALLOWED_OUTPUT_PROVENANCE = {
    "generator_emitted_final_output",
    "generator_emitted_projection",
    "candidate_override",
    "replay_preserved_candidate_output",
    "missing",
}

ALLOWED_SERIALIZATION_STATUSES = {
    "json_safe",
    "non_json_safe_rejected",
    "missing",
}

ALLOWED_INCOMPARABLE_REASON_CODES = {
    "none",
    "candidate_output_missing",
    "expected_output_missing",
    "output_type_not_comparable",
    "ambiguous_output_surface",
    "non_json_safe_output",
    "normalization_failed",
}

FORBIDDEN_UPSTREAM_SCORING_FIELDS = {
    "synthetic_expected_answer_for_scoring_only",
    "expected_output",
    "expected_answer",
    "post_ledger_scoring_status",
    "post_ledger_scoring_result",
    "deserved_exact_result",
    "deserved_but_wrong_result",
    "scoring_result",
    "scoring_label",
}

CANDIDATE_OUTPUT_SURFACE_KEYS = {
    "present",
    "output_type",
    "normalized_output",
    "raw_output_reference",
    "output_provenance",
    "serialization_status",
    "comparable_to_expected",
    "incomparable_reason_code",
    "schema_version",
}

CANDIDATE_TRACE_SURFACE_KEYS = {
    "construction_mode",
    "construction_trace_complete",
    "forced_uniqueness_trace_present",
    "train_evidence_grounded",
    "missing_required_trace_fields",
    "unresolved_rivals",
    "candidate_trace_provenance",
    "trace_schema_version",
    "candidate_output_surface_present",
    "candidate_output_surface_type",
}

COMPOSED_TRACE_SURFACE_KEYS = {
    "ordered_component_list",
    "component_execution_order",
    "component_records",
    "intermediate_outputs_after_each_component",
    "component_support_map",
    "component_only_support",
    "whole_composition_support",
    "interaction_assumptions",
    "alternative_order_surfaces",
    "alternative_subset_surfaces",
    "partial_transform_surfaces",
    "full_composition_alternatives",
    "sufficient_for_alternative_enumeration",
    "trace_schema_version",
}

MDL_TRACE_SURFACE_KEYS = {
    "accepted_grammar_id",
    "accepted_grammar_record",
    "grammar_output_surface",
    "grammar_train_support_evidence",
    "simplicity_primary_evidence",
    "negative_evidence_present",
    "competing_grammar_records",
    "train_forced_grammar",
    "compact_but_not_forced",
    "sufficient_for_competing_grammar_diagnosis",
    "trace_schema_version",
}

_JSON_SAFE_PRIMITIVES = (str, int, float, bool, type(None))


def _deepcopy(value: Any) -> Any:
    return deepcopy(value)



def _is_json_safe(value: Any) -> bool:
    try:
        json.dumps(value)
    except (TypeError, ValueError):
        return False
    return True



def detect_forbidden_upstream_scoring_fields(payload: Any) -> list[str]:
    found: set[str] = set()

    def _walk(node: Any) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                if str(key) in FORBIDDEN_UPSTREAM_SCORING_FIELDS:
                    found.add(str(key))
                _walk(value)
        elif isinstance(node, list):
            for item in node:
                _walk(item)

    _walk(payload)
    return sorted(found)



def strip_forbidden_upstream_scoring_fields(payload: Any) -> Any:
    if isinstance(payload, dict):
        sanitized: dict[str, Any] = {}
        for key, value in payload.items():
            if str(key) in FORBIDDEN_UPSTREAM_SCORING_FIELDS:
                continue
            sanitized[str(key)] = strip_forbidden_upstream_scoring_fields(value)
        return sanitized
    if isinstance(payload, list):
        return [strip_forbidden_upstream_scoring_fields(item) for item in payload]
    return _deepcopy(payload)



def build_candidate_output_surface(
    *,
    present: bool = False,
    output_type: str = "missing",
    normalized_output: Any = None,
    raw_output_reference: Any = None,
    output_provenance: str = "missing",
    serialization_status: str = "missing",
    comparable_to_expected: bool = False,
    incomparable_reason_code: str = "candidate_output_missing",
) -> dict:
    if output_type not in ALLOWED_OUTPUT_TYPES:
        raise ValueError(f"Unsupported output_type: {output_type}")
    if output_provenance not in ALLOWED_OUTPUT_PROVENANCE:
        raise ValueError(f"Unsupported output_provenance: {output_provenance}")
    if serialization_status not in ALLOWED_SERIALIZATION_STATUSES:
        raise ValueError(f"Unsupported serialization_status: {serialization_status}")
    if incomparable_reason_code not in ALLOWED_INCOMPARABLE_REASON_CODES:
        raise ValueError(f"Unsupported incomparable_reason_code: {incomparable_reason_code}")

    return {
        "present": bool(present),
        "output_type": output_type,
        "normalized_output": _deepcopy(normalized_output),
        "raw_output_reference": _deepcopy(raw_output_reference),
        "output_provenance": output_provenance,
        "serialization_status": serialization_status,
        "comparable_to_expected": bool(comparable_to_expected),
        "incomparable_reason_code": incomparable_reason_code,
        "schema_version": CANDIDATE_OUTPUT_SURFACE_SCHEMA_VERSION,
    }



def normalize_grid_int_matrix(value: Any) -> list[list[int]]:
    if not isinstance(value, list) or not value:
        raise ValueError("grid_int_matrix must be a non-empty list of rows")

    normalized: list[list[int]] = []
    expected_width: int | None = None

    for row in value:
        if not isinstance(row, list) or not row:
            raise ValueError("grid_int_matrix rows must be non-empty lists")
        if expected_width is None:
            expected_width = len(row)
        elif len(row) != expected_width:
            raise ValueError("grid_int_matrix must be rectangular")

        normalized_row: list[int] = []
        for cell in row:
            if isinstance(cell, bool) or not isinstance(cell, int):
                raise ValueError("grid_int_matrix cells must be integers")
            normalized_row.append(int(cell))
        normalized.append(normalized_row)

    return normalized



def _validate_comparable_grid_int_matrix(normalized_output: Any) -> bool:
    try:
        normalize_grid_int_matrix(normalized_output)
    except ValueError:
        return False
    return True



def validate_json_safe_candidate_output_surface(surface: dict) -> dict:
    cloned = _deepcopy(surface)
    if not _is_json_safe(cloned):
        cloned["serialization_status"] = "non_json_safe_rejected"
        cloned["comparable_to_expected"] = False
        cloned["incomparable_reason_code"] = "non_json_safe_output"
        return cloned
    return cloned



def derive_candidate_output_comparability(
    candidate_output_surface: dict,
    *,
    expected_output_available: bool,
) -> dict:
    surface = validate_json_safe_candidate_output_surface(candidate_output_surface)

    if surface.get("present") is not True:
        surface["comparable_to_expected"] = False
        surface["incomparable_reason_code"] = "candidate_output_missing"
        return surface

    if expected_output_available is not True:
        surface["comparable_to_expected"] = False
        surface["incomparable_reason_code"] = "expected_output_missing"
        return surface

    if surface.get("serialization_status") != "json_safe":
        surface["comparable_to_expected"] = False
        surface["incomparable_reason_code"] = "non_json_safe_output"
        return surface

    output_type = surface.get("output_type")
    if output_type != "grid_int_matrix":
        surface["comparable_to_expected"] = False
        surface["incomparable_reason_code"] = "output_type_not_comparable"
        return surface

    normalized = surface.get("normalized_output")
    if normalized is None:
        surface["comparable_to_expected"] = False
        surface["incomparable_reason_code"] = "ambiguous_output_surface"
        return surface

    if not _validate_comparable_grid_int_matrix(normalized):
        surface["comparable_to_expected"] = False
        surface["incomparable_reason_code"] = "normalization_failed"
        return surface

    surface["comparable_to_expected"] = True
    surface["incomparable_reason_code"] = "none"
    return surface



def derive_unscorable_reason(
    candidate_output_surface: dict,
    *,
    expected_output_available: bool,
) -> str:
    return derive_candidate_output_comparability(
        candidate_output_surface,
        expected_output_available=expected_output_available,
    ).get("incomparable_reason_code", "normalization_failed")



def compare_normalized_grid_int_matrices(candidate_output: Any, expected_output: Any) -> bool:
    return normalize_grid_int_matrix(candidate_output) == normalize_grid_int_matrix(expected_output)



def build_candidate_trace_surface(
    *,
    construction_mode: str,
    construction_trace_complete: bool,
    forced_uniqueness_trace_present: bool,
    train_evidence_grounded: bool,
    missing_required_trace_fields: list[str] | None = None,
    unresolved_rivals: list[str] | None = None,
    candidate_trace_provenance: str,
    candidate_output_surface_present: bool,
    candidate_output_surface_type: str,
) -> dict:
    return {
        "construction_mode": str(construction_mode),
        "construction_trace_complete": bool(construction_trace_complete),
        "forced_uniqueness_trace_present": bool(forced_uniqueness_trace_present),
        "train_evidence_grounded": bool(train_evidence_grounded),
        "missing_required_trace_fields": list(missing_required_trace_fields or []),
        "unresolved_rivals": list(unresolved_rivals or []),
        "candidate_trace_provenance": str(candidate_trace_provenance),
        "trace_schema_version": CANDIDATE_TRACE_SURFACE_SCHEMA_VERSION,
        "candidate_output_surface_present": bool(candidate_output_surface_present),
        "candidate_output_surface_type": str(candidate_output_surface_type),
    }



def build_composed_trace_surface(
    *,
    ordered_component_list: list[str] | None = None,
    component_execution_order: list[str] | None = None,
    component_records: list[dict] | None = None,
    intermediate_outputs_after_each_component: list[Any] | None = None,
    component_support_map: dict[str, bool] | None = None,
    component_only_support: bool = False,
    whole_composition_support: bool = False,
    interaction_assumptions: list[str] | None = None,
    alternative_order_surfaces: list[dict] | None = None,
    alternative_subset_surfaces: list[dict] | None = None,
    partial_transform_surfaces: list[dict] | None = None,
    full_composition_alternatives: list[dict] | None = None,
    sufficient_for_alternative_enumeration: bool = False,
) -> dict:
    return {
        "ordered_component_list": list(ordered_component_list or []),
        "component_execution_order": list(component_execution_order or []),
        "component_records": _deepcopy(component_records or []),
        "intermediate_outputs_after_each_component": _deepcopy(intermediate_outputs_after_each_component or []),
        "component_support_map": dict(component_support_map or {}),
        "component_only_support": bool(component_only_support),
        "whole_composition_support": bool(whole_composition_support),
        "interaction_assumptions": list(interaction_assumptions or []),
        "alternative_order_surfaces": _deepcopy(alternative_order_surfaces or []),
        "alternative_subset_surfaces": _deepcopy(alternative_subset_surfaces or []),
        "partial_transform_surfaces": _deepcopy(partial_transform_surfaces or []),
        "full_composition_alternatives": _deepcopy(full_composition_alternatives or []),
        "sufficient_for_alternative_enumeration": bool(sufficient_for_alternative_enumeration),
        "trace_schema_version": COMPOSED_TRACE_SURFACE_SCHEMA_VERSION,
    }



def build_mdl_trace_surface(
    *,
    accepted_grammar_id: str = "",
    accepted_grammar_record: dict | None = None,
    grammar_output_surface: dict | None = None,
    grammar_train_support_evidence: list[str] | None = None,
    simplicity_primary_evidence: bool = False,
    negative_evidence_present: bool = False,
    competing_grammar_records: list[dict] | None = None,
    train_forced_grammar: bool = False,
    compact_but_not_forced: bool = False,
    sufficient_for_competing_grammar_diagnosis: bool = False,
) -> dict:
    return {
        "accepted_grammar_id": str(accepted_grammar_id),
        "accepted_grammar_record": _deepcopy(accepted_grammar_record or {}),
        "grammar_output_surface": _deepcopy(grammar_output_surface or {}),
        "grammar_train_support_evidence": list(grammar_train_support_evidence or []),
        "simplicity_primary_evidence": bool(simplicity_primary_evidence),
        "negative_evidence_present": bool(negative_evidence_present),
        "competing_grammar_records": _deepcopy(competing_grammar_records or []),
        "train_forced_grammar": bool(train_forced_grammar),
        "compact_but_not_forced": bool(compact_but_not_forced),
        "sufficient_for_competing_grammar_diagnosis": bool(sufficient_for_competing_grammar_diagnosis),
        "trace_schema_version": MDL_TRACE_SURFACE_SCHEMA_VERSION,
    }



def preserve_candidate_output_surface_for_replay(
    candidate_output_surface: dict | None,
    *,
    expected_output_available: bool = False,
) -> dict:
    source = strip_forbidden_upstream_scoring_fields(candidate_output_surface or {})
    preserved = build_candidate_output_surface(
        present=source.get("present", False),
        output_type=source.get("output_type", "missing"),
        normalized_output=source.get("normalized_output"),
        raw_output_reference=source.get("raw_output_reference"),
        output_provenance=source.get("output_provenance", "missing"),
        serialization_status=source.get("serialization_status", "missing"),
        comparable_to_expected=False,
        incomparable_reason_code=source.get("incomparable_reason_code", "candidate_output_missing"),
    )
    return derive_candidate_output_comparability(
        preserved,
        expected_output_available=expected_output_available,
    )



def preserve_candidate_trace_surface_for_replay(candidate_trace_surface: dict | None) -> dict:
    source = strip_forbidden_upstream_scoring_fields(candidate_trace_surface or {})
    return build_candidate_trace_surface(
        construction_mode=source.get("construction_mode", ""),
        construction_trace_complete=source.get("construction_trace_complete", False),
        forced_uniqueness_trace_present=source.get("forced_uniqueness_trace_present", False),
        train_evidence_grounded=source.get("train_evidence_grounded", False),
        missing_required_trace_fields=source.get("missing_required_trace_fields") or [],
        unresolved_rivals=source.get("unresolved_rivals") or [],
        candidate_trace_provenance=source.get("candidate_trace_provenance", ""),
        candidate_output_surface_present=source.get("candidate_output_surface_present", False),
        candidate_output_surface_type=source.get("candidate_output_surface_type", "missing"),
    )



def preserve_composed_trace_surface_for_replay(composed_trace_surface: dict | None) -> dict:
    source = strip_forbidden_upstream_scoring_fields(composed_trace_surface or {})
    return build_composed_trace_surface(
        ordered_component_list=source.get("ordered_component_list") or [],
        component_execution_order=source.get("component_execution_order") or [],
        component_records=source.get("component_records") or [],
        intermediate_outputs_after_each_component=source.get("intermediate_outputs_after_each_component") or [],
        component_support_map=source.get("component_support_map") or {},
        component_only_support=source.get("component_only_support", False),
        whole_composition_support=source.get("whole_composition_support", False),
        interaction_assumptions=source.get("interaction_assumptions") or [],
        alternative_order_surfaces=source.get("alternative_order_surfaces") or [],
        alternative_subset_surfaces=source.get("alternative_subset_surfaces") or [],
        partial_transform_surfaces=source.get("partial_transform_surfaces") or [],
        full_composition_alternatives=source.get("full_composition_alternatives") or [],
        sufficient_for_alternative_enumeration=source.get("sufficient_for_alternative_enumeration", False),
    )



def preserve_mdl_trace_surface_for_replay(mdl_trace_surface: dict | None) -> dict:
    source = strip_forbidden_upstream_scoring_fields(mdl_trace_surface or {})
    return build_mdl_trace_surface(
        accepted_grammar_id=source.get("accepted_grammar_id", ""),
        accepted_grammar_record=source.get("accepted_grammar_record") or {},
        grammar_output_surface=source.get("grammar_output_surface") or {},
        grammar_train_support_evidence=source.get("grammar_train_support_evidence") or [],
        simplicity_primary_evidence=source.get("simplicity_primary_evidence", False),
        negative_evidence_present=source.get("negative_evidence_present", False),
        competing_grammar_records=source.get("competing_grammar_records") or [],
        train_forced_grammar=source.get("train_forced_grammar", False),
        compact_but_not_forced=source.get("compact_but_not_forced", False),
        sufficient_for_competing_grammar_diagnosis=source.get("sufficient_for_competing_grammar_diagnosis", False),
    )



def build_replay_preserved_surface_bundle(
    *,
    candidate_output_surface: dict | None = None,
    candidate_trace_surface: dict | None = None,
    composed_trace_surface: dict | None = None,
    mdl_trace_surface: dict | None = None,
    expected_output_available: bool = False,
) -> dict:
    return {
        "candidate_output_surface": preserve_candidate_output_surface_for_replay(
            candidate_output_surface,
            expected_output_available=expected_output_available,
        ),
        "candidate_trace_surface": preserve_candidate_trace_surface_for_replay(candidate_trace_surface),
        "composed_trace_surface": preserve_composed_trace_surface_for_replay(composed_trace_surface),
        "mdl_trace_surface": preserve_mdl_trace_surface_for_replay(mdl_trace_surface),
        "replay_surface_provenance": {
            "candidate_output_surface_source": "candidate_output_surface",
            "expected_output_load_stage": "not_loaded_for_replay_preservation",
            "expected_output_loaded_after_ledger_decision": False,
        },
    }
