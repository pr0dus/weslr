"""WESLR MLCF Cross-Domain Science Direction Candidate V1.

Deterministic, metadata-only helpers for turning multiple owner-supplied domain
summaries into a bounded cross-domain science direction candidate. This module
never claims discovery, proof, public science, AGI, benchmark results, or final
answer authority.
"""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from typing import Any, Mapping

from weslr.authorized_ingestion_boundary import _HIDDEN_PRIVATE_PROTECTED_MARKERS_V1 as _BOUNDARY_HIDDEN_MARKERS_V1
from weslr.calibrated_proposed_directions import SCHEMA_VERSION_V1 as DIRECTION_SCHEMA_VERSION_V1
from weslr.mlcf_ledger_registry import allowed_mlcf_ledger_ids_v1
from weslr.theoretical_calibration_axes import (
    allowed_theoretical_calibration_next_steps_v1,
    build_initial_theoretical_calibration_axes_examples_v1,
)

SCHEMA_VERSION_V1 = "mlcf_cross_domain_science_direction_candidate_v1"
HELPER_FAMILY_V1 = "mlcf_cross_domain_science_direction_candidate"

_ALLOWED_CANDIDATE_TYPES_V1 = (
    "cross_domain_method_candidate",
    "cross_domain_experiment_candidate",
    "cross_domain_representation_candidate",
    "cross_domain_probe_candidate",
    "cross_domain_architecture_candidate",
    "blocked_cross_domain_candidate",
    "needs_repair_candidate",
)

_ALLOWED_RELATION_TYPES_V1 = (
    "shared_wave_behavior",
    "shared_topology",
    "shared_constraint_model",
    "shared_signal_noise_problem",
    "shared_material_response",
    "shared_spatial_inference",
    "shared_causal_uncertainty",
    "shared_measurement_limitation",
    "weak_or_fake_analogy",
    "unknown_relation",
)

_ALLOWED_NEXT_STEP_LABELS_V1 = allowed_theoretical_calibration_next_steps_v1()
_ALLOWED_LEDGER_IDS_V1 = allowed_mlcf_ledger_ids_v1()
_ALLOWED_SOURCE_SIGNAL_FAMILIES_V1 = (
    "weak_signal",
    "repeating_signal",
    "contradictory_signal",
    "cross_domain_resonance_signal",
    "architecture_direction_signal",
    "idea_candidate_signal",
    "evidence_candidate_signal",
    "calibration_needed_signal",
    "blocked_public_claim_signal",
    "archive_low_value_signal",
    "unknown_signal",
)

_AUTHORITY_FALSE_FLAGS_V1 = (
    "runtime_authorized",
    "source_ingestion_authorized",
    "public_claim_authorized",
    "final_answer_authority",
    "provider_model_call_authority",
    "provider_authority",
    "model_authority",
    "tool_execution_authority",
    "retrieval_tool_authority",
    "web_authority",
    "weslr_io_authorized",
    "weslr_read_authorized",
    "weslr_write_authorized",
    "weslr_persistence_authorized",
    "database_write_authorized",
    "memory_mutation_authorized",
    "project_mutation_authorized",
    "behavior_pack_promotion_authorized",
    "public_science_claim_authorized",
    "proof_claim_authorized",
    "benchmark_claim_authorized",
    "agi_claim_authorized",
    "automatic_discovery_authorized",
    "cross_user_leakage_authorized",
    "hidden_private_protected_authorized",
)

_AUTHORITY_TEXT_MARKERS_V1 = (
    "discovery",
    "proof",
    "benchmark",
    "agi",
    "final answer",
    "public claim",
    "runtime authorization",
    "source ingestion authorization",
    "provider/model/tool/retrieval/web",
    ".weslr",
    "memory mutation",
    "project mutation",
    "behavior pack promotion",
    "cross-user leakage",
    "hidden/private/protected",
)

_HIDDEN_PRIVATE_PROTECTED_MARKERS_V1 = _BOUNDARY_HIDDEN_MARKERS_V1

_SAFE_METADATA_REQUIRED_TRUE_FLAGS_V1 = (
    "safe",
    "metadata_only",
    "json_safe",
    "non_public",
    "no_runtime_wiring",
    "no_model_provider_calls",
    "no_tool_execution",
    "no_retrieval",
    "no_web_calls",
    "no_source_ingestion",
    "no_raw_content_retention",
    "no_weslr_io",
    "no_weslr_read",
    "no_weslr_write",
    "no_weslr_persistence",
    "no_database_writes",
    "no_memory_mutation",
    "no_project_mutation",
    "no_behavior_pack_promotion",
    "no_public_claim_authority",
    "no_final_answer_authority",
    "no_discovery_claims",
    "no_proof_claims",
    "no_benchmark_claims",
    "no_agi_claims",
    "no_public_science_claims",
    "no_hidden_private_protected_markers",
)

_REQUIRED_FIELD_NAMES_V1 = (
    "schema_version",
    "candidate_id",
    "candidate_type",
    "candidate_title",
    "domain_inputs",
    "domain_count",
    "domain_relation_types",
    "shared_structure_map",
    "cross_domain_bridge",
    "candidate_method_summary",
    "why_this_is_nontrivial",
    "why_this_is_not_a_discovery",
    "recommended_ledger_id",
    "source_signal_family",
    "calibration_axes_used",
    "calibration_reason",
    "pressure_test_questions",
    "probe_design_suggestions",
    "missing_evidence",
    "disconfirming_signals",
    "overclaim_risks",
    "underexploration_risks",
    "promotion_blockers",
    "forbidden_interpretations",
    "next_safe_step",
    "authority_status",
    "safe_metadata",
)

_REQUIRED_TEXT_FIELDS_V1 = (
    "schema_version",
    "candidate_id",
    "candidate_type",
    "candidate_title",
    "cross_domain_bridge",
    "candidate_method_summary",
    "why_this_is_nontrivial",
    "why_this_is_not_a_discovery",
    "recommended_ledger_id",
    "source_signal_family",
    "calibration_reason",
    "next_safe_step",
)

_REQUIRED_LIST_FIELDS_V1 = (
    "domain_inputs",
    "domain_relation_types",
    "calibration_axes_used",
    "pressure_test_questions",
    "probe_design_suggestions",
    "missing_evidence",
    "disconfirming_signals",
    "overclaim_risks",
    "underexploration_risks",
    "promotion_blockers",
    "forbidden_interpretations",
)

_CANONICAL_FORBIDDEN_INTERPRETATIONS_V1 = [
    "this is proven",
    "this is discovered",
    "this is public truth",
    "this is a final answer",
    "this authorizes discovery",
    "this authorizes proof",
    "this authorizes public science",
    "this authorizes AGI claims",
    "this authorizes benchmark claims",
    "this authorizes runtime",
    "this authorizes provider/tool/web use",
    "this authorizes .weslr access",
    "this authorizes persistence",
]

_DOMAIN_KEYWORDS_TO_RELATIONS_V1 = [
    (("rf", "wifi", "wireless", "signal", "wave", "waves"), "shared_wave_behavior"),
    (("material", "materials", "surface", "scattering", "absorption", "phase"), "shared_material_response"),
    (("floor plan", "floor-plan", "floorplan", "spatial", "topology", "path", "paths", "obstacle", "obstacles"), "shared_topology"),
    (("motion", "moving", "disturbance", "noise", "signal noise", "measurement"), "shared_signal_noise_problem"),
    (("constraint", "constraints", "constrain", "inference", "spatial inference"), "shared_constraint_model"),
    (("causal", "counterfactual", "uncertainty", "hypothesis"), "shared_causal_uncertainty"),
    (("measure", "measurement", "sensor", "sampling", "sparse"), "shared_measurement_limitation"),
]

_METHOD_SUMMARY_REPLACE_RULES_V1 = (
    ("rf", "RF"),
    ("wifi", "WiFi"),
    ("floor-plan", "floor-plan"),
    ("floor plan", "floor-plan"),
    ("spatial change map", "spatial change map"),
)


def _merge_payload(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    if isinstance(payload, Mapping):
        merged.update(payload)
    for key, value in overrides.items():
        if value is not None:
            merged[key] = value
    return merged


def _compact_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _normalize_text_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        items = value
    elif isinstance(value, tuple):
        items = list(value)
    elif isinstance(value, set):
        items = sorted(value, key=repr)
    else:
        text = _compact_text(value)
        return [text] if text else []
    normalized: list[str] = []
    for item in items:
        text = _compact_text(item)
        if text:
            normalized.append(text)
    return normalized


def _json_safe(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, set):
        return [_json_safe(item) for item in sorted(value, key=repr)]
    if isinstance(value, (bytes, bytearray, memoryview)):
        return f"[redacted:{type(value).__name__}]"
    if callable(value):
        return f"[redacted:{type(value).__name__}]"
    if isinstance(value, (bool, int, float)) or value is None or isinstance(value, str):
        return value
    return f"[redacted:{type(value).__name__}]"


def _first_non_json_safe_path(value: Any, path: str = "result") -> str | None:
    if value is None or isinstance(value, (bool, int, float, str)):
        return None
    if isinstance(value, (bytes, bytearray, memoryview)):
        return path
    if isinstance(value, (tuple, set, frozenset)):
        return path
    if callable(value):
        return path
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                return f"{path}.[non-string-key:{type(key).__name__}]"
            issue = _first_non_json_safe_path(item, f"{path}.{key}")
            if issue is not None:
                return issue
        return None
    if isinstance(value, list):
        for index, item in enumerate(value):
            issue = _first_non_json_safe_path(item, f"{path}[{index}]")
            if issue is not None:
                return issue
        return None
    return path


def _contains_text_markers(value: Any, markers: tuple[str, ...]) -> bool:
    if isinstance(value, Mapping):
        return any(_contains_text_markers(key, markers) for key in value.keys()) or any(
            _contains_text_markers(item, markers) for item in value.values()
        )
    if isinstance(value, (list, tuple, set)):
        return any(_contains_text_markers(item, markers) for item in value)
    if not isinstance(value, str):
        return False
    lowered = value.lower()
    return any(marker in lowered for marker in markers)


def _default_authority_status() -> dict[str, Any]:
    return {
        flag: False for flag in _AUTHORITY_FALSE_FLAGS_V1
    } | {
        "all_authority_flags_false": True,
        "status": "metadata_only",
        "boundary_notes": "metadata-only cross-domain science direction candidate boundary",
    }


def _default_safe_metadata() -> dict[str, Any]:
    return {
        "safe": True,
        "metadata_only": True,
        "json_safe": True,
        "non_public": True,
        "no_runtime_wiring": True,
        "no_model_provider_calls": True,
        "no_tool_execution": True,
        "no_retrieval": True,
        "no_web_calls": True,
        "no_source_ingestion": True,
        "no_raw_content_retention": True,
        "no_weslr_io": True,
        "no_weslr_read": True,
        "no_weslr_write": True,
        "no_weslr_persistence": True,
        "no_database_writes": True,
        "no_memory_mutation": True,
        "no_project_mutation": True,
        "no_behavior_pack_promotion": True,
        "no_public_claim_authority": True,
        "no_final_answer_authority": True,
        "no_discovery_claims": True,
        "no_proof_claims": True,
        "no_benchmark_claims": True,
        "no_agi_claims": True,
        "no_public_science_claims": True,
        "no_hidden_private_protected_markers": True,
        "helper_family": HELPER_FAMILY_V1,
        "schema_family": SCHEMA_VERSION_V1,
    }


def _implemented_axis_ids() -> tuple[str, ...]:
    example_axes = build_initial_theoretical_calibration_axes_examples_v1()["axes"]
    return tuple(axis["axis_id"] for axis in example_axes)


def _canonical_forbidden_interpretations() -> list[str]:
    return list(_CANONICAL_FORBIDDEN_INTERPRETATIONS_V1)


def _normalized_domain_input(item: Any, index: int) -> dict[str, Any]:
    if isinstance(item, Mapping):
        domain_name = _compact_text(
            item.get("domain_name")
            or item.get("domain_title")
            or item.get("name")
            or item.get("label")
            or item.get("id"),
            f"domain_{index + 1}",
        )
        domain_summary = _compact_text(
            item.get("domain_summary")
            or item.get("summary")
            or item.get("text")
            or item.get("description"),
        )
        domain_role = _compact_text(item.get("domain_role") or item.get("role"))
    else:
        domain_name = f"domain_{index + 1}"
        domain_summary = _compact_text(item)
        domain_role = ""
    normalized = {
        "domain_name": domain_name,
        "domain_summary": domain_summary,
    }
    if domain_role:
        normalized["domain_role"] = domain_role
    return normalized


def _normalize_domain_inputs(value: Any) -> list[dict[str, Any]]:
    if value is None:
        return []
    if not isinstance(value, list):
        value = list(value) if isinstance(value, tuple) else [value]
    return [_normalized_domain_input(item, index) for index, item in enumerate(value)]


def _domain_text_blob(domain_inputs: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for domain in domain_inputs:
        parts.append(_compact_text(domain.get("domain_name")))
        parts.append(_compact_text(domain.get("domain_summary")))
        parts.append(_compact_text(domain.get("domain_role")))
    return " ".join(part for part in parts if part)


def _has_keywords(text: str, keywords: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in keywords)


def allowed_mlcf_cross_domain_candidate_types_v1() -> tuple[str, ...]:
    return _ALLOWED_CANDIDATE_TYPES_V1


def allowed_mlcf_cross_domain_relation_types_v1() -> tuple[str, ...]:
    return _ALLOWED_RELATION_TYPES_V1


def allowed_mlcf_cross_domain_next_steps_v1() -> tuple[str, ...]:
    return _ALLOWED_NEXT_STEP_LABELS_V1


def _derive_relation_types(domain_inputs: list[dict[str, Any]]) -> list[str]:
    text = _domain_text_blob(domain_inputs).lower()
    relations: list[str] = []
    for keywords, relation_type in _DOMAIN_KEYWORDS_TO_RELATIONS_V1:
        if _has_keywords(text, keywords):
            relations.append(relation_type)
    if not relations:
        return ["unknown_relation"]
    if len(domain_inputs) >= 2 and "weak_or_fake_analogy" not in relations:
        if not any(relation in relations for relation in ("shared_wave_behavior", "shared_topology", "shared_spatial_inference", "shared_material_response", "shared_signal_noise_problem")):
            relations.append("unknown_relation")
    if "shared_spatial_inference" in relations and "shared_constraint_model" not in relations:
        relations.append("shared_constraint_model")
    return list(dict.fromkeys(relations))


def _looks_like_weak_analogy(text: str) -> bool:
    weak_markers = (
        "superficial",
        "surface level",
        "only shares words",
        "fake analogy",
        "weak analogy",
        "no structural mapping",
        "no shared structure",
        "vocabulary overlap",
        "word overlap",
        "does not survive simplification",
        "collapses under simplification",
    )
    return _has_keywords(text, weak_markers)


def _infer_candidate_type(domain_inputs: list[dict[str, Any]], relation_types: list[str]) -> str:
    text = _domain_text_blob(domain_inputs).lower()
    if "weak_or_fake_analogy" in relation_types or _looks_like_weak_analogy(text):
        return "blocked_cross_domain_candidate"
    if _has_keywords(text, ("probe", "probe needed", "test whether", "missing evidence", "too large", "insufficient", "uncertain")):
        return "cross_domain_probe_candidate"
    if _has_keywords(text, ("experiment", "experiment candidate", "controlled test", "trial", "measurement")):
        return "cross_domain_experiment_candidate"
    if _has_keywords(text, ("representation", "map", "visual", "projection", "sparse map")):
        return "cross_domain_representation_candidate"
    if _has_keywords(text, ("architecture", "method", "workflow", "pipeline", "candidate method")):
        return "cross_domain_method_candidate"
    return "needs_repair_candidate"


def _recommend_ledger_id(candidate_type: str, relation_types: list[str], text: str) -> str:
    if candidate_type == "blocked_cross_domain_candidate":
        return "failed_idea_ledger"
    if candidate_type == "needs_repair_candidate":
        return "calibration_outcome_ledger"
    if candidate_type == "cross_domain_probe_candidate":
        return "idea_candidate_ledger"
    if candidate_type == "cross_domain_experiment_candidate":
        return "idea_candidate_ledger"
    if candidate_type == "cross_domain_representation_candidate":
        return "architecture_direction_ledger"
    if candidate_type == "cross_domain_architecture_candidate":
        return "architecture_direction_ledger"
    if _has_keywords(text, ("floor-plan", "floor plan", "topology", "map", "spatial", "rf", "wifi", "scattering")):
        return "architecture_direction_ledger"
    if "shared_topology" in relation_types:
        return "architecture_direction_ledger"
    if "shared_measurement_limitation" in relation_types or "shared_causal_uncertainty" in relation_types:
        return "idea_candidate_ledger"
    return "idea_candidate_ledger"


def _recommend_source_signal_family(candidate_type: str, relation_types: list[str]) -> str:
    if candidate_type == "blocked_cross_domain_candidate":
        return "archive_low_value_signal"
    if candidate_type == "needs_repair_candidate":
        return "calibration_needed_signal"
    if candidate_type == "cross_domain_probe_candidate":
        return "cross_domain_resonance_signal"
    if candidate_type == "cross_domain_experiment_candidate":
        return "cross_domain_resonance_signal"
    if candidate_type == "cross_domain_representation_candidate":
        return "cross_domain_resonance_signal"
    if candidate_type == "cross_domain_architecture_candidate":
        return "architecture_direction_signal"
    if "weak_or_fake_analogy" in relation_types:
        return "archive_low_value_signal"
    return "cross_domain_resonance_signal"


def _recommend_next_safe_step(candidate_type: str, relation_types: list[str]) -> str:
    if candidate_type == "blocked_cross_domain_candidate":
        return "archive"
    if candidate_type == "needs_repair_candidate":
        return "needs_repair"
    if candidate_type == "cross_domain_probe_candidate":
        return "probe"
    if candidate_type == "cross_domain_experiment_candidate":
        return "pressure_test"
    if candidate_type in {"cross_domain_method_candidate", "cross_domain_representation_candidate", "cross_domain_architecture_candidate"}:
        return "pressure_test"
    if "weak_or_fake_analogy" in relation_types:
        return "archive"
    return "pressure_test"


def _recommend_calibration_axes(relation_types: list[str], candidate_type: str) -> list[str]:
    axes: list[str] = []
    if "shared_wave_behavior" in relation_types:
        axes.extend(["signal_detection_calibration", "bayesian_calibration"])
    if "shared_topology" in relation_types:
        axes.append("topological_structure_preserving_calibration")
    if "shared_signal_noise_problem" in relation_types:
        axes.extend(["signal_detection_calibration", "information_theory_compression_calibration"])
    if "shared_material_response" in relation_types:
        axes.append("information_theory_compression_calibration")
    if "shared_spatial_inference" in relation_types:
        axes.extend(["topological_structure_preserving_calibration", "causal_counterfactual_calibration"])
    if "shared_constraint_model" in relation_types:
        axes.extend(["causal_counterfactual_calibration", "bayesian_calibration"])
    if "shared_causal_uncertainty" in relation_types:
        axes.extend(["bayesian_calibration", "popper_falsification_calibration"])
    if "shared_measurement_limitation" in relation_types:
        axes.extend(["signal_detection_calibration", "popper_falsification_calibration"])
    if "weak_or_fake_analogy" in relation_types or candidate_type == "blocked_cross_domain_candidate":
        axes.extend(["topological_structure_preserving_calibration", "information_theory_compression_calibration"])
    if not axes:
        axes.extend(["godel_incompleteness_calibration", "signal_detection_calibration"])
    return list(dict.fromkeys(axes))


def _candidate_title(domain_inputs: list[dict[str, Any]], candidate_type: str, bridge: str) -> str:
    if candidate_type == "blocked_cross_domain_candidate":
        return "Blocked weak cross-domain analogy candidate"
    if candidate_type == "cross_domain_probe_candidate":
        return "Cross-domain probe candidate"
    if candidate_type == "cross_domain_experiment_candidate":
        return "Cross-domain experiment candidate"
    if candidate_type == "cross_domain_representation_candidate":
        return "Cross-domain representation candidate"
    if candidate_type == "cross_domain_architecture_candidate":
        return "Cross-domain architecture candidate"
    if _has_keywords(bridge.lower(), ("rf", "floor-plan", "spatial change map")):
        return "RF/material/floor-plan sparse change map candidate"
    first = _compact_text(domain_inputs[0].get("domain_name"), "cross-domain") if domain_inputs else "cross-domain"
    return f"{first} cross-domain candidate"


def _build_shared_structure_map(domain_inputs: list[dict[str, Any]], relation_types: list[str], bridge: str, candidate_type: str) -> dict[str, Any]:
    return {
        "domain_names": [_compact_text(item.get("domain_name")) for item in domain_inputs],
        "relation_types": list(relation_types),
        "bridge_focus": bridge,
        "candidate_type": candidate_type,
        "shared_constraints": [
            "metadata-only",
            "no discovery claims",
            "no source ingestion",
        ],
        "shared_failure_modes": [
            "weak analogy",
            "overclaim",
            "premature promotion",
        ],
    }


def _build_cross_domain_bridge(candidate_type: str, relation_types: list[str], domain_inputs: list[dict[str, Any]]) -> str:
    text = _domain_text_blob(domain_inputs).lower()
    if candidate_type == "blocked_cross_domain_candidate" or "weak_or_fake_analogy" in relation_types:
        return "The overlap remains superficial and does not support a stable cross-domain bridge."
    if _has_keywords(text, ("rf", "wifi", "wireless")) and _has_keywords(text, ("floor-plan", "floor plan", "floorplan")) and _has_keywords(text, ("material", "materials", "scattering", "surface")):
        return "Sparse RF spatial change map constrained by floor-plan topology and calibrated against material/surface scattering assumptions."
    if candidate_type == "cross_domain_probe_candidate":
        return "A controlled probe may determine whether the domains share a stable bridge before method promotion."
    if candidate_type == "cross_domain_experiment_candidate":
        return "A bounded experiment candidate can test whether the shared structure survives pressure testing."
    if candidate_type == "cross_domain_representation_candidate":
        return "The domains may share a representational map if their constraints compress into a stable sparse form."
    if candidate_type == "cross_domain_architecture_candidate":
        return "The domains may share an architecture-level bridge if topology and measurement constraints align."
    return "A bounded cross-domain bridge is suggested, but it still needs structural confirmation."


def _build_candidate_method_summary(candidate_type: str, bridge: str, relation_types: list[str]) -> str:
    if candidate_type == "blocked_cross_domain_candidate":
        return "Superficial overlap does not justify a method; archive unless a stable structural map appears."
    if candidate_type == "cross_domain_probe_candidate":
        return "Probe whether the cross-domain bridge is real before promoting any candidate method."
    if candidate_type == "cross_domain_experiment_candidate":
        return "Run a bounded experiment to pressure-test the cross-domain bridge before method promotion."
    if candidate_type == "cross_domain_representation_candidate":
        return "A sparse representation may capture the shared structure across the domains."
    if candidate_type == "cross_domain_architecture_candidate":
        return "A governed architecture candidate may organize the shared constraints across the domains."
    if _has_keywords(bridge.lower(), ("sparse rf spatial change map", "floor-plan topology", "scattering assumptions")):
        return "Sparse RF spatial change map constrained by floor-plan topology and calibrated against material/surface scattering assumptions."
    relation_text = ", ".join(relation_types)
    return f"Cross-domain candidate method built from {relation_text}."


def _build_why_nontrivial(candidate_type: str, relation_types: list[str], bridge: str) -> str:
    if candidate_type == "blocked_cross_domain_candidate":
        return "It shows a safe rejection path when only vocabulary overlaps and no structural bridge survives simplification."
    if candidate_type == "cross_domain_probe_candidate":
        return "It isolates a bridge worth probing without claiming the method is already established."
    return f"It combines {', '.join(relation_types)} into a bounded candidate direction instead of a loose analogy."


def _build_why_not_discovery() -> str:
    return "This is a metadata-only candidate direction, not a discovery, proof, public science claim, or final answer."


def _build_pressure_test_questions(candidate_type: str, bridge: str) -> list[str]:
    if candidate_type == "blocked_cross_domain_candidate":
        return [
            "Does any shared mechanism survive after the vocabulary overlap is stripped away?",
            "Can the analogy be simplified into a structural mapping without collapsing?",
            "Would the candidate still exist if one domain were removed?",
        ]
    if candidate_type == "cross_domain_probe_candidate":
        return [
            "Which minimal controlled observation would test the bridge first?",
            "What evidence would show that the bridge is real rather than a coincidence?",
            "What must be ruled out before method promotion?",
        ]
    return [
        "Does the sparse bridge survive simplification and pressure testing?",
        "Which assumption is most likely to fail first?",
        "Does the candidate remain useful when one domain constraint is removed?",
    ]


def _build_probe_design_suggestions(candidate_type: str, bridge: str) -> list[str]:
    if candidate_type == "blocked_cross_domain_candidate":
        return [
            "Do not promote yet; only revisit if a stable structural mapping appears.",
            "Reduce the domains to a single shared variable and re-evaluate the analogy.",
        ]
    if candidate_type == "cross_domain_probe_candidate":
        return [
            "Start with the smallest controlled probe that can falsify the bridge.",
            "Hold one domain fixed while varying the other two to test structural dependence.",
            "Record the minimum evidence needed to move from probe to pressure test.",
        ]
    return [
        "Use a bounded controlled setup to test the bridge against the most likely counterexample.",
        "Vary one domain constraint at a time to see whether the candidate survives.",
        "Check whether the bridge still holds after compression to the smallest useful representation.",
    ]


def _build_missing_evidence(candidate_type: str) -> list[str]:
    if candidate_type == "blocked_cross_domain_candidate":
        return [
            "No stable structural mapping yet",
            "No falsifiable bridge hypothesis yet",
        ]
    if candidate_type == "cross_domain_probe_candidate":
        return [
            "No controlled probe result yet",
            "No minimum-evidence threshold yet",
        ]
    return [
        "No pressure-test result yet",
        "No structural simplification check yet",
    ]


def _build_disconfirming_signals(candidate_type: str) -> list[str]:
    if candidate_type == "blocked_cross_domain_candidate":
        return ["The analogy collapses under simplification."]
    if candidate_type == "cross_domain_probe_candidate":
        return ["A minimal probe fails to preserve the bridge."]
    return ["A simpler explanation explains the same observations better."]


def _build_overclaim_risks(candidate_type: str) -> list[str]:
    if candidate_type == "blocked_cross_domain_candidate":
        return [
            "Treating a weak analogy as a method",
            "Promoting vocabulary overlap as structure",
        ]
    return [
        "Promoting a candidate direction as discovery",
        "Treating compression as proof",
    ]


def _build_underexploration_risks(candidate_type: str) -> list[str]:
    if candidate_type == "blocked_cross_domain_candidate":
        return [
            "Discarding a potentially recoverable structural mapping too early",
        ]
    if candidate_type == "cross_domain_probe_candidate":
        return [
            "Skipping the smallest useful probe and losing the bridge signal",
        ]
    return [
        "Archiving a candidate before it is pressure-tested",
    ]


def _build_promotion_blockers(candidate_type: str) -> list[str]:
    if candidate_type == "blocked_cross_domain_candidate":
        return [
            "Analogy fails under simplification",
            "No stable bridge supports method promotion",
        ]
    if candidate_type == "cross_domain_probe_candidate":
        return [
            "Missing controlled probe evidence",
            "Bridge not yet pressure-tested",
        ]
    return [
        "Not pressure-tested yet",
        "No operator review yet",
    ]


def _authority_status_is_fail_closed(authority_status: Any) -> tuple[bool, list[str]]:
    if not isinstance(authority_status, Mapping):
        return False, ["missing_authority_status"]
    labels: list[str] = []
    for flag in _AUTHORITY_FALSE_FLAGS_V1:
        if flag not in authority_status:
            labels.append(f"missing_authority_status_{flag}")
        elif authority_status[flag] is not False:
            labels.append(f"unsafe_authority_flag:{flag}")
    if authority_status.get("all_authority_flags_false") is not True:
        labels.append("unsafe_authority_flags")
    if _compact_text(authority_status.get("status")) != "metadata_only":
        labels.append("unsafe_authority_status")
    if not _compact_text(authority_status.get("boundary_notes")):
        labels.append("missing_authority_boundary_notes")
    if _contains_text_markers(authority_status.get("boundary_notes"), _AUTHORITY_TEXT_MARKERS_V1):
        labels.append("unsafe_authority_text")
    if _contains_text_markers(authority_status.get("boundary_notes"), _HIDDEN_PRIVATE_PROTECTED_MARKERS_V1):
        labels.append("forbidden_hidden_private_protected_marker")
    return not labels, labels


def _safe_metadata_is_fail_closed(safe_metadata: Any) -> tuple[bool, list[str]]:
    if not isinstance(safe_metadata, Mapping):
        return False, ["missing_safe_metadata"]
    labels: list[str] = []
    for flag in _SAFE_METADATA_REQUIRED_TRUE_FLAGS_V1:
        if safe_metadata.get(flag) is not True:
            labels.append(f"unsafe_safe_metadata_flag:{flag}")
    if _contains_text_markers(safe_metadata.get("boundary_notes"), _AUTHORITY_TEXT_MARKERS_V1):
        labels.append("unsafe_safe_metadata_text")
    if _contains_text_markers(safe_metadata.get("boundary_notes"), _HIDDEN_PRIVATE_PROTECTED_MARKERS_V1):
        labels.append("forbidden_hidden_private_protected_marker")
    return not labels, labels


def _validate_domain_inputs(domain_inputs: Any) -> tuple[bool, list[str]]:
    if not isinstance(domain_inputs, list):
        return False, ["invalid_domain_inputs"]
    if len(domain_inputs) < 2:
        return False, ["too_few_domain_inputs"]
    labels: list[str] = []
    for index, domain in enumerate(domain_inputs):
        if not isinstance(domain, Mapping):
            labels.append(f"invalid_domain_inputs_item_{index}")
            continue
        if not _compact_text(domain.get("domain_name")):
            labels.append(f"missing_domain_inputs_item_{index}_domain_name")
        if not _compact_text(domain.get("domain_summary")):
            labels.append(f"missing_domain_inputs_item_{index}_domain_summary")
    return not labels, labels


def _validate_text_list(name: str, value: Any, allow_empty: bool = False) -> list[str]:
    labels: list[str] = []
    if not isinstance(value, list):
        return [f"invalid_{name}"]
    if not value and not allow_empty:
        return [f"missing_{name}"]
    if any(_compact_text(item) == "" for item in value):
        labels.append(f"invalid_{name}")
    return labels


def _validate_json_safe(packet: Any) -> list[str]:
    issue = _first_non_json_safe_path(packet)
    return ["non_json_safe_output"] if issue is not None else []


def _derive_packet(packet: dict[str, Any]) -> dict[str, Any]:
    domain_inputs = _normalize_domain_inputs(packet.get("domain_inputs") or packet.get("domains"))
    candidate_type = _compact_text(packet.get("candidate_type"))
    relation_types = _normalize_text_list(packet.get("domain_relation_types"))
    if not candidate_type:
        candidate_type = _infer_candidate_type(domain_inputs, relation_types or _derive_relation_types(domain_inputs))
    if not relation_types:
        relation_types = _derive_relation_types(domain_inputs)
    bridge = _compact_text(packet.get("cross_domain_bridge"))
    if not bridge:
        bridge = _build_cross_domain_bridge(candidate_type, relation_types, domain_inputs)
    title = _compact_text(packet.get("candidate_title"))
    if not title:
        title = _candidate_title(domain_inputs, candidate_type, bridge)
    method_summary = _compact_text(packet.get("candidate_method_summary"))
    if not method_summary:
        method_summary = _build_candidate_method_summary(candidate_type, bridge, relation_types)
    source_signal_family = _compact_text(packet.get("source_signal_family")) or _recommend_source_signal_family(candidate_type, relation_types)
    recommended_ledger_id = _compact_text(packet.get("recommended_ledger_id")) or _recommend_ledger_id(candidate_type, relation_types, bridge)
    calibration_axes_used = _normalize_text_list(packet.get("calibration_axes_used")) or _recommend_calibration_axes(relation_types, candidate_type)
    next_safe_step = _compact_text(packet.get("next_safe_step")) or _recommend_next_safe_step(candidate_type, relation_types)
    return {
        **packet,
        "domain_inputs": domain_inputs,
        "domain_count": len(domain_inputs),
        "candidate_type": candidate_type,
        "candidate_title": title,
        "domain_relation_types": relation_types,
        "cross_domain_bridge": bridge,
        "candidate_method_summary": method_summary,
        "source_signal_family": source_signal_family,
        "recommended_ledger_id": recommended_ledger_id,
        "calibration_axes_used": calibration_axes_used,
        "next_safe_step": next_safe_step,
    }


def build_mlcf_cross_domain_science_direction_candidate_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    merged = _merge_payload(payload, **overrides)
    domain_inputs = _normalize_domain_inputs(merged.get("domain_inputs") or merged.get("domains"))
    relation_types = _normalize_text_list(merged.get("domain_relation_types")) or _derive_relation_types(domain_inputs)
    candidate_type = _compact_text(merged.get("candidate_type")) or _infer_candidate_type(domain_inputs, relation_types)
    bridge = _compact_text(merged.get("cross_domain_bridge")) or _build_cross_domain_bridge(candidate_type, relation_types, domain_inputs)
    candidate_title = _compact_text(merged.get("candidate_title")) or _candidate_title(domain_inputs, candidate_type, bridge)
    candidate_method_summary = _compact_text(merged.get("candidate_method_summary")) or _build_candidate_method_summary(candidate_type, bridge, relation_types)
    recommended_ledger_id = _compact_text(merged.get("recommended_ledger_id")) or _recommend_ledger_id(candidate_type, relation_types, bridge)
    source_signal_family = _compact_text(merged.get("source_signal_family")) or _recommend_source_signal_family(candidate_type, relation_types)
    calibration_axes_used = _normalize_text_list(merged.get("calibration_axes_used")) or _recommend_calibration_axes(relation_types, candidate_type)
    calibration_reason = _compact_text(
        merged.get("calibration_reason"),
        f"Use {', '.join(calibration_axes_used)} because the bridge depends on shared structure, compression pressure, and falsifiability.",
    )
    next_safe_step = _compact_text(merged.get("next_safe_step")) or _recommend_next_safe_step(candidate_type, relation_types)
    pressure_test_questions = _normalize_text_list(merged.get("pressure_test_questions")) or _build_pressure_test_questions(candidate_type, bridge)
    probe_design_suggestions = _normalize_text_list(merged.get("probe_design_suggestions")) or _build_probe_design_suggestions(candidate_type, bridge)
    missing_evidence = _normalize_text_list(merged.get("missing_evidence")) or _build_missing_evidence(candidate_type)
    disconfirming_signals = _normalize_text_list(merged.get("disconfirming_signals")) or _build_disconfirming_signals(candidate_type)
    overclaim_risks = _normalize_text_list(merged.get("overclaim_risks")) or _build_overclaim_risks(candidate_type)
    underexploration_risks = _normalize_text_list(merged.get("underexploration_risks")) or _build_underexploration_risks(candidate_type)
    promotion_blockers = _normalize_text_list(merged.get("promotion_blockers")) or _build_promotion_blockers(candidate_type)
    forbidden_interpretations = _normalize_text_list(merged.get("forbidden_interpretations")) or _canonical_forbidden_interpretations()
    why_this_is_nontrivial = _compact_text(
        merged.get("why_this_is_nontrivial"),
        _build_why_nontrivial(candidate_type, relation_types, bridge),
    )
    why_this_is_not_a_discovery = _compact_text(
        merged.get("why_this_is_not_a_discovery"),
        _build_why_not_discovery(),
    )
    authority_status = merged.get("authority_status")
    if authority_status is None:
        authority_status = _default_authority_status()
    safe_metadata = merged.get("safe_metadata")
    if safe_metadata is None:
        safe_metadata = _default_safe_metadata()
    candidate = {
        "schema_version": SCHEMA_VERSION_V1,
        "candidate_id": _compact_text(
            merged.get("candidate_id"),
            f"{candidate_type or 'cross_domain_candidate'}_{sha256((candidate_title + '|' + bridge).encode('utf-8')).hexdigest()[:16]}",
        ),
        "candidate_type": candidate_type,
        "candidate_title": candidate_title,
        "domain_inputs": domain_inputs,
        "domain_count": len(domain_inputs),
        "domain_relation_types": relation_types,
        "shared_structure_map": _json_safe(
            merged.get("shared_structure_map")
            if merged.get("shared_structure_map") is not None
            else _build_shared_structure_map(domain_inputs, relation_types, bridge, candidate_type)
        ),
        "cross_domain_bridge": bridge,
        "candidate_method_summary": candidate_method_summary,
        "why_this_is_nontrivial": why_this_is_nontrivial,
        "why_this_is_not_a_discovery": why_this_is_not_a_discovery,
        "recommended_ledger_id": recommended_ledger_id,
        "source_signal_family": source_signal_family,
        "calibration_axes_used": calibration_axes_used,
        "calibration_reason": calibration_reason,
        "pressure_test_questions": pressure_test_questions,
        "probe_design_suggestions": probe_design_suggestions,
        "missing_evidence": missing_evidence,
        "disconfirming_signals": disconfirming_signals,
        "overclaim_risks": overclaim_risks,
        "underexploration_risks": underexploration_risks,
        "promotion_blockers": promotion_blockers,
        "forbidden_interpretations": forbidden_interpretations,
        "next_safe_step": next_safe_step,
        "authority_status": _json_safe(authority_status),
        "safe_metadata": _json_safe(safe_metadata),
    }
    if isinstance(candidate["authority_status"], Mapping):
        candidate["authority_status"].setdefault("all_authority_flags_false", True)
        candidate["authority_status"].setdefault("status", "metadata_only")
        candidate["authority_status"].setdefault("boundary_notes", "metadata-only cross-domain science direction candidate boundary")
    if isinstance(candidate["safe_metadata"], Mapping):
        candidate["safe_metadata"].setdefault("helper_family", HELPER_FAMILY_V1)
        candidate["safe_metadata"].setdefault("schema_family", SCHEMA_VERSION_V1)
        candidate["safe_metadata"].setdefault("no_raw_content_retention", True)
    return candidate


def validate_mlcf_cross_domain_science_direction_candidate_v1(candidate: Any) -> dict[str, Any]:
    if not isinstance(candidate, Mapping):
        return {
            "schema_version": SCHEMA_VERSION_V1,
            "valid": False,
            "blocked": True,
            "blocked_labels": ["invalid_candidate_type"],
            "validation_posture": "blocked",
            "summary_text": "Blocked MLCF cross-domain science direction candidate: invalid candidate type.",
        }

    blocked_labels: list[str] = []
    for field in _REQUIRED_FIELD_NAMES_V1:
        if field not in candidate:
            blocked_labels.append(f"missing_{field}")

    for field in _REQUIRED_TEXT_FIELDS_V1:
        if not _compact_text(candidate.get(field)):
            blocked_labels.append(f"missing_{field}")

    domain_ok, domain_labels = _validate_domain_inputs(candidate.get("domain_inputs"))
    if not domain_ok:
        blocked_labels.extend(domain_labels)
    elif candidate.get("domain_count") != len(candidate.get("domain_inputs", [])):
        blocked_labels.append("mismatched_domain_count")

    for field in _REQUIRED_LIST_FIELDS_V1:
        value = candidate.get(field)
        if field == "domain_inputs":
            continue
        blocked_labels.extend(_validate_text_list(field, value))

    if _compact_text(candidate.get("schema_version")) != SCHEMA_VERSION_V1:
        blocked_labels.append("invalid_schema_version")

    if _compact_text(candidate.get("candidate_type")) not in _ALLOWED_CANDIDATE_TYPES_V1:
        blocked_labels.append("invalid_candidate_type")
    if _compact_text(candidate.get("next_safe_step")) not in _ALLOWED_NEXT_STEP_LABELS_V1:
        blocked_labels.append("invalid_next_safe_step")
    if _compact_text(candidate.get("recommended_ledger_id")) not in _ALLOWED_LEDGER_IDS_V1:
        blocked_labels.append("invalid_recommended_ledger_id")
    if _compact_text(candidate.get("source_signal_family")) not in _ALLOWED_SOURCE_SIGNAL_FAMILIES_V1:
        blocked_labels.append("invalid_source_signal_family")

    relation_types = _normalize_text_list(candidate.get("domain_relation_types"))
    if relation_types and any(item not in _ALLOWED_RELATION_TYPES_V1 for item in relation_types):
        blocked_labels.append("invalid_domain_relation_types")

    calibration_axes = _normalize_text_list(candidate.get("calibration_axes_used"))
    if calibration_axes and any(item not in _implemented_axis_ids() for item in calibration_axes):
        blocked_labels.append("invalid_calibration_axes_used")

    authority_status = candidate.get("authority_status")
    _, authority_labels = _authority_status_is_fail_closed(authority_status)
    blocked_labels.extend(authority_labels)

    safe_metadata = candidate.get("safe_metadata")
    _, safe_labels = _safe_metadata_is_fail_closed(safe_metadata)
    blocked_labels.extend(safe_labels)

    domain_inputs = candidate.get("domain_inputs")
    domain_ok, domain_labels = _validate_domain_inputs(domain_inputs)
    if not domain_ok:
        blocked_labels.extend(domain_labels)
    elif candidate.get("domain_count") != len(domain_inputs):
        blocked_labels.append("mismatched_domain_count")

    if _compact_text(candidate.get("why_this_is_not_a_discovery")) and "not a discovery" not in _compact_text(candidate.get("why_this_is_not_a_discovery")).lower():
        blocked_labels.append("missing_not_a_discovery_explanation")

    for field_name in (
        "candidate_title",
        "candidate_method_summary",
        "cross_domain_bridge",
        "why_this_is_nontrivial",
        "calibration_reason",
    ):
        if _contains_text_markers(candidate.get(field_name), _AUTHORITY_TEXT_MARKERS_V1):
            blocked_labels.append("unsafe_authority_text")

    for field_name in (
        "candidate_title",
        "candidate_method_summary",
        "cross_domain_bridge",
        "why_this_is_nontrivial",
        "why_this_is_not_a_discovery",
        "calibration_reason",
        "pressure_test_questions",
        "probe_design_suggestions",
        "missing_evidence",
        "disconfirming_signals",
        "overclaim_risks",
        "underexploration_risks",
        "promotion_blockers",
        "forbidden_interpretations",
        "shared_structure_map",
        "domain_inputs",
    ):
        if _contains_text_markers(candidate.get(field_name), _HIDDEN_PRIVATE_PROTECTED_MARKERS_V1):
            blocked_labels.append("forbidden_hidden_private_protected_marker")

    for field_name in (
        "pressure_test_questions",
        "probe_design_suggestions",
        "missing_evidence",
        "disconfirming_signals",
        "overclaim_risks",
        "underexploration_risks",
        "promotion_blockers",
        "forbidden_interpretations",
    ):
        value = candidate.get(field_name)
        if not isinstance(value, list):
            blocked_labels.append(f"invalid_{field_name}")
        elif not value:
            blocked_labels.append(f"missing_{field_name}")
        elif any(_compact_text(item) == "" for item in value):
            blocked_labels.append(f"invalid_{field_name}")

    if not isinstance(candidate.get("shared_structure_map"), Mapping):
        blocked_labels.append("missing_shared_structure_map")
    elif _first_non_json_safe_path(candidate.get("shared_structure_map")) is not None:
        blocked_labels.append("non_json_safe_output")

    if not _compact_text(candidate.get("candidate_method_summary")):
        blocked_labels.append("missing_candidate_method_summary")
    if not _compact_text(candidate.get("pressure_test_questions")):
        blocked_labels.append("missing_pressure_test_questions")
    if not _compact_text(candidate.get("disconfirming_signals")):
        blocked_labels.append("missing_disconfirming_signals")
    if not _compact_text(candidate.get("promotion_blockers")):
        blocked_labels.append("missing_promotion_blockers")

    if candidate.get("candidate_type") == "blocked_cross_domain_candidate" and _compact_text(candidate.get("next_safe_step")) not in {"archive", "blocked_by_safety"}:
        blocked_labels.append("mismatched_next_safe_step")
    if candidate.get("candidate_type") == "cross_domain_probe_candidate" and _compact_text(candidate.get("next_safe_step")) != "probe":
        blocked_labels.append("mismatched_next_safe_step")
    if candidate.get("candidate_type") in {"cross_domain_method_candidate", "cross_domain_representation_candidate", "cross_domain_architecture_candidate", "cross_domain_experiment_candidate"} and _compact_text(candidate.get("next_safe_step")) not in {"pressure_test", "probe"}:
        blocked_labels.append("mismatched_next_safe_step")

    if candidate.get("candidate_type") == "blocked_cross_domain_candidate" and _compact_text(candidate.get("recommended_ledger_id")) != "failed_idea_ledger":
        blocked_labels.append("mismatched_recommended_ledger_id")
    if candidate.get("candidate_type") == "cross_domain_probe_candidate" and _compact_text(candidate.get("recommended_ledger_id")) != "idea_candidate_ledger":
        blocked_labels.append("mismatched_recommended_ledger_id")
    if candidate.get("candidate_type") == "cross_domain_method_candidate" and _compact_text(candidate.get("recommended_ledger_id")) not in {"architecture_direction_ledger", "idea_candidate_ledger"}:
        blocked_labels.append("mismatched_recommended_ledger_id")

    if _compact_text(candidate.get("source_signal_family")) == "cross_domain_resonance_signal" and _compact_text(candidate.get("candidate_type")) == "blocked_cross_domain_candidate":
        blocked_labels.append("mismatched_source_signal_family")

    blocked_labels.extend(_validate_json_safe(candidate))

    valid = not blocked_labels
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "valid": valid,
        "blocked": not valid,
        "blocked_labels": list(dict.fromkeys(blocked_labels)),
        "validation_posture": "valid" if valid else "blocked",
        "summary_text": "Valid MLCF cross-domain science direction candidate." if valid else "Blocked MLCF cross-domain science direction candidate: metadata or authority checks failed.",
    }


def summarize_mlcf_cross_domain_science_direction_candidate_v1(candidate: Any) -> dict[str, Any]:
    packet = candidate if isinstance(candidate, Mapping) else {}
    relation_types = _normalize_text_list(packet.get("domain_relation_types"))
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "candidate_id": _compact_text(packet.get("candidate_id")),
        "candidate_type": _compact_text(packet.get("candidate_type")),
        "domain_count": len(packet.get("domain_inputs", [])) if isinstance(packet.get("domain_inputs"), list) else 0,
        "relation_count": len(relation_types),
        "recommended_ledger_id": _compact_text(packet.get("recommended_ledger_id")),
        "source_signal_family": _compact_text(packet.get("source_signal_family")),
        "next_safe_step": _compact_text(packet.get("next_safe_step")),
        "calibration_axes_count": len(_normalize_text_list(packet.get("calibration_axes_used"))),
        "summary_text": _compact_text(
            packet.get("candidate_method_summary"),
            "Metadata-only cross-domain science direction candidate.",
        ),
        "validation_posture": validate_mlcf_cross_domain_science_direction_candidate_v1(packet).get("validation_posture", "blocked"),
    }


def to_mlcf_cross_domain_science_direction_candidate_json_safe_v1(candidate: Any) -> Any:
    return _json_safe(candidate)


def _build_initial_mlcf_cross_domain_science_direction_candidate_examples_v1() -> list[dict[str, Any]]:
    examples: list[dict[str, Any]] = []

    examples.append(
        build_mlcf_cross_domain_science_direction_candidate_v1(
            candidate_id="rf_material_floorplan_sparse_change_map_candidate",
            candidate_type="cross_domain_method_candidate",
            candidate_title="RF/material/floor-plan sparse change map candidate",
            domain_inputs=[
                {
                    "domain_name": "WiFi/RF sensing",
                    "domain_summary": "RF signals propagate indoors and are disturbed by motion.",
                },
                {
                    "domain_name": "material and surface scattering",
                    "domain_summary": "Materials and geometry shape reflection, scattering, absorption, and phase behavior.",
                },
                {
                    "domain_name": "floor-plan inference",
                    "domain_summary": "Known floor plans constrain paths, obstacles, and expected motion regions.",
                },
            ],
            domain_relation_types=[
                "shared_wave_behavior",
                "shared_topology",
                "shared_spatial_inference",
                "shared_signal_noise_problem",
                "shared_material_response",
                "shared_constraint_model",
                "shared_causal_uncertainty",
            ],
            shared_structure_map={
                "domain_names": ["WiFi/RF sensing", "material and surface scattering", "floor-plan inference"],
                "relation_types": [
                    "shared_wave_behavior",
                    "shared_topology",
                    "shared_spatial_inference",
                    "shared_signal_noise_problem",
                    "shared_material_response",
                    "shared_constraint_model",
                    "shared_causal_uncertainty",
                ],
                "bridge_focus": "sparse RF change map constrained by topology and surface response",
            },
            cross_domain_bridge="Sparse RF spatial change map constrained by floor-plan topology and calibrated against material/surface scattering assumptions.",
            candidate_method_summary="Sparse RF spatial change map constrained by floor-plan topology and calibrated against material/surface scattering assumptions.",
            why_this_is_nontrivial="It merges wave behavior, surface response, and spatial topology into a bounded candidate direction instead of a loose analogy.",
            why_this_is_not_a_discovery="This is a metadata-only candidate direction, not a discovery, proof, public science claim, or final answer.",
            recommended_ledger_id="architecture_direction_ledger",
            source_signal_family="cross_domain_resonance_signal",
            calibration_axes_used=[
                "topological_structure_preserving_calibration",
                "information_theory_compression_calibration",
                "signal_detection_calibration",
                "causal_counterfactual_calibration",
                "popper_falsification_calibration",
            ],
            calibration_reason="Use topology, compression, signal detection, counterfactual, and falsification calibration because the bridge depends on wave behavior, surface response, and spatial constraints.",
            pressure_test_questions=[
                "Does the sparse map survive simplification of the floor-plan constraints?",
                "Does the bridge still hold if the surface-scattering assumption is weakened?",
                "Which counterexample would most quickly break the candidate?",
            ],
            probe_design_suggestions=[
                "Build the smallest controlled spatial map that can still be falsified.",
                "Vary the floor-plan constraint separately from the surface-response assumption.",
                "Check whether the candidate remains useful after compression to the minimum shared structure.",
            ],
            missing_evidence=[
                "No pressure-test result yet",
                "No structural simplification check yet",
            ],
            disconfirming_signals=[
                "A simpler explanation fits the same observations better.",
            ],
            overclaim_risks=[
                "Treating the candidate as discovery",
                "Turning the sparse map into a public claim",
            ],
            underexploration_risks=[
                "Archiving the candidate before pressure testing",
            ],
            promotion_blockers=[
                "Not pressure-tested yet",
                "No operator review yet",
            ],
            forbidden_interpretations=_canonical_forbidden_interpretations(),
            next_safe_step="pressure_test",
        )
    )

    examples.append(
        build_mlcf_cross_domain_science_direction_candidate_v1(
            candidate_id="weak_analogy_blocked_candidate",
            candidate_type="blocked_cross_domain_candidate",
            candidate_title="Blocked weak analogy candidate",
            domain_inputs=[
                {
                    "domain_name": "Domain One",
                    "domain_summary": "This domain shares only surface vocabulary with the other domain.",
                },
                {
                    "domain_name": "Domain Two",
                    "domain_summary": "This second domain repeats the same words but not the same structure.",
                },
            ],
            domain_relation_types=["weak_or_fake_analogy"],
            shared_structure_map={
                "domain_names": ["Domain One", "Domain Two"],
                "relation_types": ["weak_or_fake_analogy"],
                "bridge_focus": "superficial overlap only",
            },
            cross_domain_bridge="The overlap remains superficial and does not support a stable cross-domain bridge.",
            candidate_method_summary="Superficial overlap does not justify a method; archive unless a stable structural map appears.",
            why_this_is_nontrivial="It demonstrates a safe rejection path when only vocabulary overlaps and no structural bridge survives simplification.",
            why_this_is_not_a_discovery="This is a metadata-only candidate direction, not a discovery, proof, public science claim, or final answer.",
            recommended_ledger_id="failed_idea_ledger",
            source_signal_family="archive_low_value_signal",
            calibration_axes_used=[
                "topological_structure_preserving_calibration",
                "information_theory_compression_calibration",
            ],
            calibration_reason="Use topology and compression calibration to test whether the analogy collapses under simplification.",
            pressure_test_questions=[
                "Does any shared mechanism survive after the vocabulary overlap is stripped away?",
                "Can the analogy be simplified into a structural mapping without collapsing?",
            ],
            probe_design_suggestions=[
                "Do not promote yet; only revisit if a stable structural mapping appears.",
            ],
            missing_evidence=[
                "No stable structural mapping yet",
            ],
            disconfirming_signals=[
                "The analogy collapses under simplification.",
            ],
            overclaim_risks=[
                "Promoting vocabulary overlap as structure",
            ],
            underexploration_risks=[
                "Discarding a potentially recoverable structural mapping too early",
            ],
            promotion_blockers=[
                "Analogy fails under simplification",
                "No stable bridge supports method promotion",
            ],
            forbidden_interpretations=_canonical_forbidden_interpretations(),
            next_safe_step="archive",
        )
    )

    examples.append(
        build_mlcf_cross_domain_science_direction_candidate_v1(
            candidate_id="cross_domain_probe_needed_candidate",
            candidate_type="cross_domain_probe_candidate",
            candidate_title="Cross-domain probe candidate",
            domain_inputs=[
                {
                    "domain_name": "RF sensing",
                    "domain_summary": "Motion-related disturbances may appear in sparse RF changes.",
                },
                {
                    "domain_name": "spatial constraints",
                    "domain_summary": "A floor plan may constrain the search space, but the bridge is not yet confirmed.",
                },
                {
                    "domain_name": "surface response",
                    "domain_summary": "Material response may matter, but missing evidence is still large.",
                },
            ],
            domain_relation_types=[
                "shared_measurement_limitation",
                "shared_causal_uncertainty",
                "shared_spatial_inference",
            ],
            shared_structure_map={
                "domain_names": ["RF sensing", "spatial constraints", "surface response"],
                "relation_types": [
                    "shared_measurement_limitation",
                    "shared_causal_uncertainty",
                    "shared_spatial_inference",
                ],
                "bridge_focus": "bridge may exist but needs a minimum controlled probe",
            },
            cross_domain_bridge="A controlled probe may determine whether the domains share a stable bridge before method promotion.",
            candidate_method_summary="Probe whether the cross-domain bridge is real before promoting any candidate method.",
            why_this_is_nontrivial="It isolates a bridge worth probing without claiming the method is already established.",
            why_this_is_not_a_discovery="This is a metadata-only candidate direction, not a discovery, proof, public science claim, or final answer.",
            recommended_ledger_id="idea_candidate_ledger",
            source_signal_family="cross_domain_resonance_signal",
            calibration_axes_used=[
                "signal_detection_calibration",
                "bayesian_calibration",
                "causal_counterfactual_calibration",
            ],
            calibration_reason="Use signal detection, Bayesian, and causal counterfactual calibration to test whether the bridge survives a minimal controlled probe.",
            pressure_test_questions=[
                "Which minimal controlled observation would test the bridge first?",
                "What evidence would show that the bridge is real rather than a coincidence?",
                "What must be ruled out before method promotion?",
            ],
            probe_design_suggestions=[
                "Start with the smallest controlled probe that can falsify the bridge.",
                "Hold one domain fixed while varying the others to test structural dependence.",
            ],
            missing_evidence=[
                "No controlled probe result yet",
                "No minimum-evidence threshold yet",
            ],
            disconfirming_signals=[
                "A minimal probe fails to preserve the bridge.",
            ],
            overclaim_risks=[
                "Treating a probe candidate as a method",
            ],
            underexploration_risks=[
                "Skipping the smallest useful probe and losing the bridge signal",
            ],
            promotion_blockers=[
                "Missing controlled probe evidence",
                "Bridge not yet pressure-tested",
            ],
            forbidden_interpretations=_canonical_forbidden_interpretations(),
            next_safe_step="probe",
        )
    )

    return examples


def build_initial_mlcf_cross_domain_science_direction_candidate_examples_v1() -> list[dict[str, Any]]:
    return deepcopy(_build_initial_mlcf_cross_domain_science_direction_candidate_examples_v1())
