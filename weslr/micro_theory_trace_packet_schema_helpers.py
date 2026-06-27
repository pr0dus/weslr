# Micro‑Theory Trace‑Packet Schema Helpers

"""Pure helper utilities for the Micro‑Theory trace‑packet design.

This module provides immutable constants and pure functions that model the
planning vocabulary defined in the trace‑packet schema planning documents.
All functions are deterministic, have no side‑effects, and operate only on
standard Python data structures (dict, list, tuple, set, frozenset).
"""

from __future__ import annotations

from typing import Mapping, Iterable, Tuple

# ---------------------------------------------------------------------------
# Canonical pressure families (immutable frozenset for safety)
# ---------------------------------------------------------------------------
CANONICAL_PRESSURES = frozenset(
    {
        "role_stability",
        "relation_stability",
        "absence",
        "exception",
        "contradiction_precedence",
        "negative_evidence",
        "non_change",
        "distractor_rejection",
        "color_appearance_bait",
        "target_location",
        "action_type",
        "output_shape",
        "rival_grammar",
        "unresolved_ambiguity",
        "counterfactual_stability",
        "concept_bloat",
        "coordinate_overfit",
    }
)

# ---------------------------------------------------------------------------
# Alias definitions
# ---------------------------------------------------------------------------
ALLOWED_ALIASES = {
    "absence_of_expected_change_pressure": ("negative_evidence", "non_change"),
    "salience_distractor_pressure": ("distractor_rejection", "color_appearance_bait"),
}

FORBIDDEN_ALIASES = {"overfit_specificity_pressure"}

# ---------------------------------------------------------------------------
# Helper predicates
# ---------------------------------------------------------------------------
def is_overfit_family(name: str) -> bool:
    """Return ``True`` if *name* is an overfit family.

    Overfit families are ``concept_bloat`` and ``coordinate_overfit``.
    """
    return name in {"concept_bloat", "coordinate_overfit"}


def expand_alias(alias_name: str) -> Tuple[str, ...]:
    """Return the canonical expansion for *alias_name*.

    Raises:
        ValueError – if *alias_name* is a forbidden alias.
        KeyError – if *alias_name* is unknown.
    """
    if alias_name in FORBIDDEN_ALIASES:
        raise ValueError(f"Alias '{alias_name}' is forbidden and cannot be expanded.")
    try:
        return tuple(ALLOWED_ALIASES[alias_name])
    except KeyError:
        raise KeyError(f"Alias '{alias_name}' is not defined.")


def is_allowed_alias(alias_name: str) -> bool:
    """Return ``True`` if *alias_name* is an allowed alias."""
    return alias_name in ALLOWED_ALIASES

# ---------------------------------------------------------------------------
# Packet section names (exact strings as used in planning document)
# ---------------------------------------------------------------------------
PACKET_SECTIONS = (
    "packet_identity",
    "boundary_metadata",
    "synthetic_case_identity",
    "solver_visible_train_material",
    "solver_visible_test_material",
    "evaluator_only_post_check_material",
    "activation_gate_result",
    "canonical_pressure_families",
    "alias_reporting_shorthand",
    "certainty_channels",
    "rival_grammar_ambiguity_state",
    "contradiction_precedence_state",
    "absence_exception_non_change_state",
    "overfit_diagnostics",
    "rejected_output_audit",
    "why_not_other_output_reasoning",
    "inevitability_safe_failure_summary",
    "auditability_notes",
    "ceremony_compactness_notes",
    "schema_readiness_notes",
)

# ---------------------------------------------------------------------------
# Field classification (solver_visible / evaluator_only / reviewer_only)
# ---------------------------------------------------------------------------
SOLVER_VISIBLE_FIELDS = {
    "train_inputs",
    "train_outputs_canonical",
    "test_input",
    "gate_mode",
    "activated_families",
    "dormant_families",
    "canonical_pressure_families",
    "certainty_target",
    "certainty_action",
    "certainty_representation",
    "rival_grammar",
    "contradiction_precedence",
    "overfit_concept_bloat",
    "overfit_coordinate_overfit",
}

EVALUATOR_ONLY_FIELDS = {
    "intended_rule",
    "expected_test_output",
    "evaluator_post_check",
    "expected_output_notes",
}

REVIEWER_ONLY_FIELDS = {
    "lane_name",
    "audit_log_id",
    "auditability_notes",
    "ceremony_compactness_notes",
    "schema_readiness_notes",
}

def field_visibility(field_name: str) -> str:
    """Return the visibility classification for *field_name*.

    One of ``"solver_visible"``, ``"evaluator_only"`` or ``"reviewer_only"``.
    Raises ``KeyError`` for unknown fields.
    """
    if field_name in SOLVER_VISIBLE_FIELDS:
        return "solver_visible"
    if field_name in EVALUATOR_ONLY_FIELDS:
        return "evaluator_only"
    if field_name in REVIEWER_ONLY_FIELDS:
        return "reviewer_only"
    raise KeyError(f"Unknown field '{field_name}'.")

def contains_evaluator_only_fields(field_names: Iterable[str]) -> bool:
    """Return ``True`` if any name in *field_names* is an evaluator‑only field."""
    return any(name in EVALUATOR_ONLY_FIELDS for name in field_names)

def alias_entry_is_safe(alias_entry: Mapping[str, object]) -> bool:
    """Validate a trace‑packet alias entry.

    ``alias_entry`` must contain the keys ``alias_name``, ``canonical_expansion``,
    ``sub_notes`` and ``fail_open_trigger``.
    Returns ``True`` if the entry obeys all policy rules; otherwise ``False``.
    """
    required_keys = {"alias_name", "canonical_expansion", "sub_notes", "fail_open_trigger"}
    if not required_keys.issubset(alias_entry.keys()):
        return False
    alias = alias_entry["alias_name"]
    if not is_allowed_alias(alias):
        return False
    # canonical_expansion must be a tuple matching the allowed expansion exactly
    try:
        expected = ALLOWED_ALIASES[alias]
    except KeyError:
        return False
    if tuple(alias_entry["canonical_expansion"]) != expected:
        return False
    # sub_notes must be a non‑empty iterable
    sub = alias_entry["sub_notes"]
    try:
        if not any(True for _ in sub):
            return False
    except Exception:
        return False
    # overfit families must not appear in the expansion
    if any(is_overfit_family(name) for name in alias_entry["canonical_expansion"]):
        return False
    return True

def certainty_channels_are_separate(packet: Mapping[str, object]) -> bool:
    """Check that all three certainty channels are present in *packet*.

    Returns ``True`` only if the keys ``certainty_target``, ``certainty_action``
    and ``certainty_representation`` exist.
    """
    required = {"certainty_target", "certainty_action", "certainty_representation"}
    return required.issubset(packet.keys())

def packet_respects_basic_boundaries(packet: Mapping[str, object]) -> bool:
    """Perform a minimal structural validation of a trace‑packet.

    Checks that:
        * No evaluator‑only fields appear in a ``solver_visible_fields`` list.
        * Alias entries (if any) are safe.
        * No forbidden alias is used.
        * Certainty channels are separate.
    """
    # 1. evaluator‑only leakage
    solver_fields = packet.get("solver_visible_fields", [])
    if contains_evaluator_only_fields(solver_fields):
        return False
    # 2. alias safety
    for alias_entry in packet.get("alias_entries", []):
        if not alias_entry_is_safe(alias_entry):
            return False
    # 3. forbidden alias usage
    for alias in packet.get("alias_names", []):
        if alias in FORBIDDEN_ALIASES:
            return False
    # 4. certainty separation
    if not certainty_channels_are_separate(packet):
        return False
    return True

# End of module
