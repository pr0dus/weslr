"""WESLR MLCF Controlled Information Ingestion Candidate V1.

Deterministic, metadata-only helpers for bridging one owner-approved summary or
owner-supplied observation into a controlled information ingestion candidate
packet. This module does not ingest raw content, retain raw content, write
memory, call providers/tools/web, mutate project state, or authorize claims.
"""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from typing import Any, Mapping

from weslr.authorized_ingestion_boundary import (
    build_authorized_ingestion_boundary_packet_v1,
    build_initial_authorized_ingestion_boundary_examples_v1,
    to_authorized_ingestion_boundary_json_safe_v1,
    validate_authorized_ingestion_boundary_packet_v1,
)
from weslr.calibrated_proposed_directions import (
    build_calibrated_proposed_direction_v1,
    build_initial_calibrated_proposed_direction_examples_v1,
    to_calibrated_proposed_direction_json_safe_v1,
    validate_calibrated_proposed_direction_v1,
)
from weslr.mlcf_ledger_registry import (
    allowed_mlcf_ledger_ids_v1,
    build_initial_mlcf_ledger_registry_v1,
    summarize_mlcf_ledger_registry_v1,
    to_mlcf_ledger_registry_json_safe_v1,
    validate_mlcf_ledger_registry_v1,
)
from weslr.real_findings_evidence_intake import (
    HELPER_FAMILY_V1 as EVIDENCE_HELPER_FAMILY_V1,
    SCHEMA_VERSION_V1 as EVIDENCE_SCHEMA_VERSION_V1,
    allowed_evidence_confidence_postures_v1,
    allowed_evidence_source_kinds_v1,
    allowed_proposed_direction_eligibility_v1,
    build_real_findings_evidence_intake_packet_v1,
    build_initial_real_findings_evidence_intake_examples_v1,
    to_real_findings_evidence_intake_json_safe_v1,
    validate_real_findings_evidence_intake_packet_v1,
)
from weslr.theoretical_calibration_axes import (
    SCHEMA_VERSION_V1 as AXES_SCHEMA_VERSION_V1,
    allowed_theoretical_calibration_next_steps_v1,
    build_initial_theoretical_calibration_axes_examples_v1,
)
from weslr.calibrated_proposed_directions import SCHEMA_VERSION_V1 as DIRECTION_SCHEMA_VERSION_V1

SCHEMA_VERSION_V1 = "mlcf_controlled_information_ingestion_candidate_v1"
HELPER_FAMILY_V1 = "mlcf_controlled_information_ingestion_candidate"

_ALLOWED_INPUT_KINDS_V1 = (
    "owner_supplied_observation_summary",
    "owner_supplied_document_summary",
    "internal_project_artifact_summary",
    "known_science_replay_summary",
    "architecture_direction_summary",
    "idea_candidate_summary",
    "blocked_or_unknown_source_summary",
)

_ALLOWED_SIGNAL_FAMILIES_V1 = (
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

_ALLOWED_NEXT_STEP_LABELS_V1 = allowed_theoretical_calibration_next_steps_v1()

_ALLOWED_LEDGER_IDS_V1 = allowed_mlcf_ledger_ids_v1()

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

_HIDDEN_PRIVATE_PROTECTED_MARKERS_V1 = (
    "hidden prompt",
    "system prompt",
    "private text",
    "secret",
    "api key",
    "protected file",
    "protected",
    "private",
)

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
    "input_kind",
    "input_scope",
    "input_summary",
    "source_access_status",
    "raw_content_retained",
    "authorized_ingestion_boundary_packet",
    "authorized_ingestion_boundary_validation",
    "evidence_intake_packet",
    "evidence_intake_validation",
    "recommended_ledger_id",
    "recommended_ledger_reason",
    "ledger_registry_summary",
    "signal_family",
    "confidence_posture",
    "calibration_axes_to_apply",
    "calibration_reason",
    "calibrated_proposed_direction_packet",
    "calibrated_proposed_direction_validation",
    "next_safe_step",
    "missing_evidence",
    "disconfirming_signal",
    "promotion_blockers",
    "forbidden_interpretations",
    "authority_status",
    "safe_metadata",
)

_REQUIRED_TEXT_FIELDS_V1 = (
    "schema_version",
    "candidate_id",
    "input_kind",
    "input_scope",
    "input_summary",
    "source_access_status",
    "recommended_ledger_id",
    "recommended_ledger_reason",
    "signal_family",
    "confidence_posture",
    "calibration_reason",
    "next_safe_step",
)

_REQUIRED_LIST_FIELDS_V1 = (
    "calibration_axes_to_apply",
    "missing_evidence",
    "disconfirming_signal",
    "promotion_blockers",
    "forbidden_interpretations",
)

_DEFAULT_AUTHORITY_STATUS_V1 = {
    "runtime_authorized": False,
    "source_ingestion_authorized": False,
    "public_claim_authorized": False,
    "final_answer_authority": False,
    "provider_model_call_authority": False,
    "provider_authority": False,
    "model_authority": False,
    "tool_execution_authority": False,
    "retrieval_tool_authority": False,
    "web_authority": False,
    "weslr_io_authorized": False,
    "weslr_read_authorized": False,
    "weslr_write_authorized": False,
    "weslr_persistence_authorized": False,
    "database_write_authorized": False,
    "memory_mutation_authorized": False,
    "project_mutation_authorized": False,
    "behavior_pack_promotion_authorized": False,
    "public_science_claim_authorized": False,
    "proof_claim_authorized": False,
    "benchmark_claim_authorized": False,
    "agi_claim_authorized": False,
    "automatic_discovery_authorized": False,
    "cross_user_leakage_authorized": False,
    "hidden_private_protected_authorized": False,
    "all_authority_flags_false": True,
    "status": "metadata_only",
    "boundary_notes": "metadata-only controlled information ingestion candidate boundary",
}

_DEFAULT_SAFE_METADATA_V1 = {
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
    "no_score_claims": True,
    "helper_family": HELPER_FAMILY_V1,
    "schema_family": SCHEMA_VERSION_V1,
}

_CANONICAL_FORBIDDEN_INTERPRETATIONS_V1 = [
    "this is proven",
    "this is discovered",
    "this is public truth",
    "this is a final answer",
    "this authorizes ingestion",
    "this authorizes runtime",
    "this authorizes provider/tool/web use",
    "this authorizes .weslr access",
    "this authorizes persistence",
]

_INPUT_KIND_TO_SOURCE_KIND_V1 = {
    "owner_supplied_observation_summary": "owner_supplied_observation",
    "owner_supplied_document_summary": "owner_supplied_document",
    "internal_project_artifact_summary": "internal_project_artifact",
    "known_science_replay_summary": "known_science_replay",
    "architecture_direction_summary": "internal_project_artifact",
    "idea_candidate_summary": "synthetic_example",
    "blocked_or_unknown_source_summary": "unknown_source",
}

_SIGNAL_FAMILY_TO_LEDGER_ID_V1 = {
    "weak_signal": "evidence_ledger",
    "repeating_signal": "evidence_ledger",
    "contradictory_signal": "evidence_ledger",
    "cross_domain_resonance_signal": "evidence_ledger",
    "architecture_direction_signal": "architecture_direction_ledger",
    "idea_candidate_signal": "idea_candidate_ledger",
    "evidence_candidate_signal": "evidence_ledger",
    "calibration_needed_signal": "calibration_outcome_ledger",
    "blocked_public_claim_signal": "failed_idea_ledger",
    "archive_low_value_signal": "failed_idea_ledger",
    "unknown_signal": "evidence_ledger",
}

_SIGNAL_FAMILY_TO_CONFIDENCE_POSTURE_V1 = {
    "weak_signal": "weak_signal",
    "repeating_signal": "strong_signal_requires_pressure_test",
    "contradictory_signal": "conflicting_signal",
    "cross_domain_resonance_signal": "moderate_signal",
    "architecture_direction_signal": "strong_signal_requires_pressure_test",
    "idea_candidate_signal": "weak_signal",
    "evidence_candidate_signal": "moderate_signal",
    "calibration_needed_signal": "insufficient_context",
    "blocked_public_claim_signal": "blocked_by_safety",
    "archive_low_value_signal": "weak_signal",
    "unknown_signal": "unassessed",
}

_SIGNAL_FAMILY_TO_NEXT_STEP_V1 = {
    "weak_signal": "watch",
    "repeating_signal": "pressure_test",
    "contradictory_signal": "probe",
    "cross_domain_resonance_signal": "pressure_test",
    "architecture_direction_signal": "pressure_test",
    "idea_candidate_signal": "pressure_test",
    "evidence_candidate_signal": "pressure_test",
    "calibration_needed_signal": "calibrate",
    "blocked_public_claim_signal": "blocked_by_safety",
    "archive_low_value_signal": "archive",
    "unknown_signal": "operator_review",
}

_SIGNAL_FAMILY_TO_AXES_V1 = {
    "weak_signal": ["signal_detection_calibration", "bayesian_calibration"],
    "repeating_signal": [
        "signal_detection_calibration",
        "bayesian_calibration",
        "reverse_calibration_backcasting",
    ],
    "contradictory_signal": ["popper_falsification_calibration", "causal_counterfactual_calibration"],
    "cross_domain_resonance_signal": [
        "topological_structure_preserving_calibration",
        "information_theory_compression_calibration",
    ],
    "architecture_direction_signal": [
        "godel_incompleteness_calibration",
        "cybernetic_control_calibration",
        "nonlinear_escalation_schedule_calibration",
    ],
    "idea_candidate_signal": [
        "adversarial_gan_calibration",
        "evolutionary_calibration",
        "popper_falsification_calibration",
    ],
    "evidence_candidate_signal": [
        "signal_detection_calibration",
        "bayesian_calibration",
        "popper_falsification_calibration",
    ],
    "calibration_needed_signal": ["bayesian_calibration", "cybernetic_control_calibration"],
    "blocked_public_claim_signal": ["game_theory_incentive_calibration", "popper_falsification_calibration"],
    "archive_low_value_signal": ["information_theory_compression_calibration", "evolutionary_calibration"],
    "unknown_signal": ["godel_incompleteness_calibration", "signal_detection_calibration"],
}

_SIGNAL_FAMILY_TO_RECOMMENDED_DIRECTION_STATUS_V1 = {
    "weak_signal": "watch",
    "repeating_signal": "needs_pressure_test",
    "contradictory_signal": "needs_probe",
    "cross_domain_resonance_signal": "needs_pressure_test",
    "architecture_direction_signal": "needs_pressure_test",
    "idea_candidate_signal": "needs_pressure_test",
    "evidence_candidate_signal": "needs_pressure_test",
    "calibration_needed_signal": "needs_calibration",
    "blocked_public_claim_signal": "blocked_by_safety",
    "archive_low_value_signal": "archive",
    "unknown_signal": "operator_review_required",
}

_SIGNAL_FAMILY_TO_RECOMMENDED_PROMOTION_BLOCKERS_V1 = {
    "weak_signal": ["Insufficient repetition for promotion"],
    "repeating_signal": ["No independent confirmation yet", "No falsifying test yet"],
    "contradictory_signal": ["Requires falsification before promotion"],
    "cross_domain_resonance_signal": ["Analogy not yet pressure-tested"],
    "architecture_direction_signal": ["Requires operator review before architecture promotion"],
    "idea_candidate_signal": ["Candidate idea needs adversarial pressure tests"],
    "evidence_candidate_signal": ["Evidence needs source and counter-signal review"],
    "calibration_needed_signal": ["Calibration update not yet reviewed"],
    "blocked_public_claim_signal": ["Public claim pressure detected"],
    "archive_low_value_signal": ["Low explanatory gain"],
    "unknown_signal": ["Insufficient context"],
}

_SIGNAL_FAMILY_TO_RECOMMENDED_MISSING_EVIDENCE_V1 = {
    "weak_signal": ["No repeat confirmation yet"],
    "repeating_signal": ["No independent confirmation yet", "No falsifying test yet"],
    "contradictory_signal": ["No counterexample resolved yet"],
    "cross_domain_resonance_signal": ["No structural mapping check yet"],
    "architecture_direction_signal": ["No operator review yet"],
    "idea_candidate_signal": ["No adversarial stress test yet"],
    "evidence_candidate_signal": ["No source limitation review yet"],
    "calibration_needed_signal": ["No calibration update yet"],
    "blocked_public_claim_signal": ["No safety boundary confirmation yet"],
    "archive_low_value_signal": ["No future-use justification yet"],
    "unknown_signal": ["Insufficient context"],
}

_SIGNAL_FAMILY_TO_RECOMMENDED_PROPOSED_DIRECTION_ELIGIBILITY_V1 = {
    "weak_signal": "eligible_after_probe",
    "repeating_signal": "eligible_after_pressure_test",
    "contradictory_signal": "operator_review_required",
    "cross_domain_resonance_signal": "eligible_after_probe",
    "architecture_direction_signal": "eligible_after_pressure_test",
    "idea_candidate_signal": "eligible_after_probe",
    "evidence_candidate_signal": "eligible_for_candidate_direction",
    "calibration_needed_signal": "operator_review_required",
    "blocked_public_claim_signal": "blocked_by_safety",
    "archive_low_value_signal": "not_eligible",
    "unknown_signal": "not_eligible",
}

_SIGNAL_FAMILY_TO_RECOMMENDED_DISCONFIRMING_SIGNAL_V1 = {
    "weak_signal": ["A one-off artifact would weaken the candidate."],
    "repeating_signal": ["A coincidental repeat or noisy artifact would weaken the candidate."],
    "contradictory_signal": ["A consistent counterexample would overturn the candidate."],
    "cross_domain_resonance_signal": ["A weak analogy with no shared structure would weaken the candidate."],
    "architecture_direction_signal": ["A simpler architecture with better safety would replace this candidate."],
    "idea_candidate_signal": ["An adversarial probe that breaks the idea would weaken it."],
    "evidence_candidate_signal": ["A source limitation or contradiction would weaken the evidence."],
    "calibration_needed_signal": ["A calibration update that fails to move confidence would weaken the candidate."],
    "blocked_public_claim_signal": ["Any public-claim pressure is a safety counter-signal."],
    "archive_low_value_signal": ["A higher-value explanatory path would justify archiving this candidate."],
    "unknown_signal": ["Additional context may change the candidate."],
}

_SIGNAL_FAMILY_TO_RECOMMENDED_REVERSE_TRACE_V1 = {
    "weak_signal": "mlcf_weak_signal_reverse_trace_v1",
    "repeating_signal": "mlcf_repeating_signal_reverse_trace_v1",
    "contradictory_signal": "mlcf_contradictory_signal_reverse_trace_v1",
    "cross_domain_resonance_signal": "mlcf_cross_domain_resonance_reverse_trace_v1",
    "architecture_direction_signal": "mlcf_architecture_direction_reverse_trace_v1",
    "idea_candidate_signal": "mlcf_idea_candidate_reverse_trace_v1",
    "evidence_candidate_signal": "mlcf_evidence_candidate_reverse_trace_v1",
    "calibration_needed_signal": "mlcf_calibration_needed_reverse_trace_v1",
    "blocked_public_claim_signal": "mlcf_blocked_public_claim_reverse_trace_v1",
    "archive_low_value_signal": "mlcf_archive_low_value_reverse_trace_v1",
    "unknown_signal": "mlcf_unknown_signal_reverse_trace_v1",
}


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
        return any(_contains_text_markers(item, markers) for item in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(_contains_text_markers(item, markers) for item in value)
    if not isinstance(value, str):
        return False
    lowered = value.lower()
    return any(marker in lowered for marker in markers)


def _default_authority_status() -> dict[str, Any]:
    return deepcopy(_DEFAULT_AUTHORITY_STATUS_V1)


def _default_safe_metadata() -> dict[str, Any]:
    return deepcopy(_DEFAULT_SAFE_METADATA_V1)


def _default_boundary_template() -> dict[str, Any]:
    return deepcopy(build_initial_authorized_ingestion_boundary_examples_v1()[0])


def _default_evidence_template() -> dict[str, Any]:
    return deepcopy(build_initial_real_findings_evidence_intake_examples_v1()[0])


def _default_direction_template() -> dict[str, Any]:
    return deepcopy(build_initial_calibrated_proposed_direction_examples_v1()[0])


def allowed_mlcf_ingestion_input_kinds_v1() -> tuple[str, ...]:
    return _ALLOWED_INPUT_KINDS_V1


def allowed_mlcf_ingestion_next_steps_v1() -> tuple[str, ...]:
    return _ALLOWED_NEXT_STEP_LABELS_V1


def allowed_mlcf_ingestion_signal_families_v1() -> tuple[str, ...]:
    return _ALLOWED_SIGNAL_FAMILIES_V1


def _merge_payload(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    if isinstance(payload, Mapping):
        merged.update(payload)
    for key, value in overrides.items():
        if value is not None:
            merged[key] = value
    return merged


def _candidate_hash(candidate_id_seed: str) -> str:
    return sha256(candidate_id_seed.encode("utf-8")).hexdigest()[:16]


def _recommend_ledger_id(input_kind: str, signal_family: str, input_summary: str = "") -> str:
    if input_kind == "owner_supplied_observation_summary" and "preference" in input_summary.lower():
        return "user_preference_ledger"
    if input_kind == "internal_project_artifact_summary":
        return "project_state_ledger"
    if input_kind == "architecture_direction_summary" or signal_family == "architecture_direction_signal":
        return "architecture_direction_ledger"
    if input_kind == "idea_candidate_summary" or signal_family == "idea_candidate_signal":
        return "idea_candidate_ledger"
    if signal_family == "calibration_needed_signal":
        return "calibration_outcome_ledger"
    if signal_family == "blocked_public_claim_signal":
        return "failed_idea_ledger"
    if signal_family == "archive_low_value_signal":
        return "failed_idea_ledger"
    if input_kind == "known_science_replay_summary":
        return "calibration_outcome_ledger"
    return _SIGNAL_FAMILY_TO_LEDGER_ID_V1.get(signal_family, "evidence_ledger")


def _recommended_source_kind(input_kind: str) -> str:
    return _INPUT_KIND_TO_SOURCE_KIND_V1.get(input_kind, "unknown_source")


def _recommended_axes(signal_family: str) -> list[str]:
    return list(_SIGNAL_FAMILY_TO_AXES_V1.get(signal_family, ["signal_detection_calibration", "bayesian_calibration"]))


def _recommended_next_step(signal_family: str) -> str:
    return _SIGNAL_FAMILY_TO_NEXT_STEP_V1.get(signal_family, "operator_review")


def _recommended_confidence_posture(signal_family: str) -> str:
    return _SIGNAL_FAMILY_TO_CONFIDENCE_POSTURE_V1.get(signal_family, "unassessed")


def _recommended_direction_status(signal_family: str) -> str:
    return _SIGNAL_FAMILY_TO_RECOMMENDED_DIRECTION_STATUS_V1.get(signal_family, "operator_review_required")


def _recommended_reverse_trace(signal_family: str) -> str:
    return _SIGNAL_FAMILY_TO_RECOMMENDED_REVERSE_TRACE_V1.get(signal_family, "mlcf_controlled_information_ingestion_reverse_trace_v1")


def _recommended_missing_evidence(signal_family: str) -> list[str]:
    return list(_SIGNAL_FAMILY_TO_RECOMMENDED_MISSING_EVIDENCE_V1.get(signal_family, ["Insufficient context"]))


def _recommended_proposed_direction_eligibility(signal_family: str) -> str:
    return _SIGNAL_FAMILY_TO_RECOMMENDED_PROPOSED_DIRECTION_ELIGIBILITY_V1.get(signal_family, "not_eligible")


def _recommended_disconfirming_signal(signal_family: str) -> list[str]:
    return list(_SIGNAL_FAMILY_TO_RECOMMENDED_DISCONFIRMING_SIGNAL_V1.get(signal_family, ["Additional context may change the candidate."]))


def _recommended_promotion_blockers(signal_family: str) -> list[str]:
    return list(_SIGNAL_FAMILY_TO_RECOMMENDED_PROMOTION_BLOCKERS_V1.get(signal_family, ["Needs review"]))


def _candidate_safe_metadata() -> dict[str, Any]:
    return _default_safe_metadata()


def _candidate_authority_status() -> dict[str, Any]:
    return _default_authority_status()


def build_mlcf_controlled_information_ingestion_candidate_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = _merge_payload(payload, **overrides)
    input_kind = _compact_text(data.get("input_kind"))
    signal_family = _compact_text(data.get("signal_family"))
    input_scope = _compact_text(data.get("input_scope"), "metadata-only input scope")
    input_summary = _compact_text(data.get("input_summary"), "metadata-only summary")
    candidate_id = _compact_text(
        data.get("candidate_id"),
        f"{input_kind or 'candidate'}_{signal_family or 'signal'}_{_candidate_hash(input_kind + '|' + signal_family + '|' + input_scope + '|' + input_summary)}",
    )
    source_access_status = _compact_text(data.get("source_access_status"), "metadata_only")
    raw_content_retained = bool(data.get("raw_content_retained", False))

    recommended_ledger_id = _compact_text(
        data.get("recommended_ledger_id"),
        _recommend_ledger_id(input_kind, signal_family, input_summary),
    )
    recommended_ledger_reason = _compact_text(
        data.get("recommended_ledger_reason"),
        f"Ledger selected from input kind '{input_kind}' and signal family '{signal_family}'.",
    )
    signal_family_axes = _recommended_axes(signal_family)
    calibration_axes_to_apply = _normalize_text_list(data.get("calibration_axes_to_apply")) or signal_family_axes
    next_safe_step = _compact_text(data.get("next_safe_step"), _recommended_next_step(signal_family))
    confidence_posture = _compact_text(data.get("confidence_posture"), _recommended_confidence_posture(signal_family))
    calibration_reason = _compact_text(
        data.get("calibration_reason"),
        f"Apply {', '.join(calibration_axes_to_apply)} because signal family '{signal_family}' benefits from that pressure pattern.",
    )

    boundary_packet = data.get("authorized_ingestion_boundary_packet")
    if boundary_packet is None:
        boundary_packet = _default_boundary_template()
    boundary_packet = build_authorized_ingestion_boundary_packet_v1(
        boundary_packet,
        ingestion_boundary_id=candidate_id,
        requested_source_kind=_recommended_source_kind(input_kind),
        requested_access_mode="owner_supplied_summary",
        authorization_state="operator_supplied_summary_only",
        source_scope=input_scope,
        owner_or_operator_request_status="operator approved metadata-only handling",
        privacy_sensitivity="moderate",
        safety_sensitivity="moderate",
        cross_user_or_tenant_risk="low",
        raw_content_handling="summary_only",
        retention_policy="no raw retention",
        allowed_output_form="evidence_intake_candidate_only",
        evidence_intake_link_allowed=False,
        operator_review_required=True,
        blocked_reason="metadata-only controlled ingestion boundary",
        required_redactions=[],
        forbidden_interpretations=list(_CANONICAL_FORBIDDEN_INTERPRETATIONS_V1),
        authority_status=_candidate_authority_status(),
        safe_metadata={
            **_candidate_safe_metadata(),
            "ingestion_authorized": False,
            "raw_retention_allowed": False,
            "evidence_intake_link_allowed": False,
            "public_claim_allowed": False,
            "final_answer_authority": False,
            "discovery_preservation": True,
            "no_score_claims": True,
        },
        search_direction_allowed=True,
        search_direction_blocked_reason="",
        ingestion_authorized=False,
        raw_retention_allowed=False,
        public_claim_allowed=False,
        final_answer_authority=False,
        discovery_domains_preserved=["owner_supplied_observations", "internal_project_artifacts", "ai_architectures"],
    )
    boundary_validation = validate_authorized_ingestion_boundary_packet_v1(boundary_packet)

    evidence_packet = data.get("evidence_intake_packet")
    if evidence_packet is None:
        evidence_packet = _default_evidence_template()
    evidence_packet = build_real_findings_evidence_intake_packet_v1(
        evidence_packet,
        evidence_intake_id=candidate_id,
        source_scope=input_scope,
        source_kind=_recommended_source_kind(input_kind),
        source_reference_summary=input_summary,
        source_access_status=source_access_status,
        raw_content_retained=False,
        evidence_signal_summary=f"Controlled ingestion candidate for {signal_family}.",
        observed_pattern=input_summary,
        known_limitations=["Summary only; no raw content retained."],
        missing_context=_recommended_missing_evidence(signal_family),
        confidence_posture=confidence_posture,
        calibration_axes_to_apply=calibration_axes_to_apply,
        reverse_trace_reference=_recommended_reverse_trace(signal_family),
        proposed_direction_eligibility=_recommended_proposed_direction_eligibility(signal_family),
        disconfirming_signal=_recommended_disconfirming_signal(signal_family),
        operator_review_need="Operator review is required before any authority beyond metadata-only handling.",
        privacy_sensitivity="moderate",
        safety_sensitivity="moderate",
        promotion_blockers=_recommended_promotion_blockers(signal_family),
        forbidden_interpretations=list(_CANONICAL_FORBIDDEN_INTERPRETATIONS_V1),
        authority_status=_candidate_authority_status(),
        safe_metadata={
            **_candidate_safe_metadata(),
            "raw_content_retained": False,
            "source_access_status": source_access_status,
            "proposed_direction_eligibility": _recommended_proposed_direction_eligibility(signal_family),
            "no_score_claims": True,
            "evidence_family": EVIDENCE_HELPER_FAMILY_V1,
            "helper_family": EVIDENCE_SCHEMA_VERSION_V1,
        },
    )
    evidence_validation = validate_real_findings_evidence_intake_packet_v1(evidence_packet)

    ledger_registry = data.get("ledger_registry_summary")
    if ledger_registry is None:
        ledger_registry = summarize_mlcf_ledger_registry_v1(build_initial_mlcf_ledger_registry_v1())
    if isinstance(ledger_registry, Mapping) and "ledger_ids" not in ledger_registry:
        ledger_registry = summarize_mlcf_ledger_registry_v1(build_initial_mlcf_ledger_registry_v1())
    ledger_registry_summary = _json_safe(ledger_registry)

    direction_status = _recommended_direction_status(signal_family)
    calibrated_proposed_direction_packet = data.get("calibrated_proposed_direction_packet")
    if calibrated_proposed_direction_packet is None:
        calibrated_proposed_direction_packet = _default_direction_template()
    calibrated_proposed_direction_packet = build_calibrated_proposed_direction_v1(
        calibrated_proposed_direction_packet,
        direction_id=candidate_id,
        source_signal_summary=input_summary,
        source_scope=input_scope,
        proposed_direction_summary=(
            f"Route the {signal_family} candidate toward {recommended_ledger_id} with {next_safe_step} as the next safe step."
        ),
        why_this_direction=(
            f"The input kind '{input_kind}' and signal family '{signal_family}' point toward {recommended_ledger_id}.") ,
        calibration_axes_used=calibration_axes_to_apply,
        reverse_trace_reference=_recommended_reverse_trace(signal_family),
        expected_next_step=next_safe_step,
        direction_status=direction_status,
        supporting_evidence_summary=f"Controlled ingestion bridge for {input_kind} with {signal_family}.",
        missing_evidence=_recommended_missing_evidence(signal_family),
        disconfirming_signal=_recommended_disconfirming_signal(signal_family),
        risk_of_overclaim=(
            "High if the candidate is treated as discovery, proof, or public truth before pressure testing."
        ),
        risk_of_underexploration=(
            "High if the candidate is archived before it is routed to the safe next step."
        ),
        operator_review_need=(
            "Operator review is required before any promotion, public claim, or authority escalation."
        ),
        promotion_blockers=_recommended_promotion_blockers(signal_family),
        forbidden_interpretations=list(_CANONICAL_FORBIDDEN_INTERPRETATIONS_V1),
        authority_status=_candidate_authority_status(),
        safe_metadata={
            **_candidate_safe_metadata(),
            "next_safe_step": next_safe_step,
            "no_score_claims": True,
            "helper_family": DIRECTION_SCHEMA_VERSION_V1,
        },
    )
    direction_validation = validate_calibrated_proposed_direction_v1(calibrated_proposed_direction_packet)

    candidate = {
        "schema_version": SCHEMA_VERSION_V1,
        "candidate_id": candidate_id,
        "input_kind": input_kind,
        "input_scope": input_scope,
        "input_summary": input_summary,
        "source_access_status": source_access_status,
        "raw_content_retained": raw_content_retained,
        "authorized_ingestion_boundary_packet": boundary_packet,
        "authorized_ingestion_boundary_validation": boundary_validation,
        "evidence_intake_packet": evidence_packet,
        "evidence_intake_validation": evidence_validation,
        "recommended_ledger_id": recommended_ledger_id,
        "recommended_ledger_reason": recommended_ledger_reason,
        "ledger_registry_summary": ledger_registry_summary,
        "signal_family": signal_family,
        "confidence_posture": confidence_posture,
        "calibration_axes_to_apply": calibration_axes_to_apply,
        "calibration_reason": calibration_reason,
        "calibrated_proposed_direction_packet": calibrated_proposed_direction_packet,
        "calibrated_proposed_direction_validation": direction_validation,
        "next_safe_step": next_safe_step,
        "missing_evidence": _normalize_text_list(data.get("missing_evidence")) or _recommended_missing_evidence(signal_family),
        "disconfirming_signal": _normalize_text_list(data.get("disconfirming_signal")) or _recommended_disconfirming_signal(signal_family),
        "promotion_blockers": _normalize_text_list(data.get("promotion_blockers")) or _recommended_promotion_blockers(signal_family),
        "forbidden_interpretations": _normalize_text_list(data.get("forbidden_interpretations")) or list(_CANONICAL_FORBIDDEN_INTERPRETATIONS_V1),
        "authority_status": _candidate_authority_status() if data.get("authority_status") is None else _json_safe(data.get("authority_status")),
        "safe_metadata": _candidate_safe_metadata() if data.get("safe_metadata") is None else _json_safe(data.get("safe_metadata")),
    }
    if isinstance(candidate["authority_status"], Mapping):
        candidate["authority_status"].setdefault("all_authority_flags_false", True)
        candidate["authority_status"].setdefault("status", "metadata_only")
        candidate["authority_status"].setdefault("boundary_notes", "metadata-only controlled information ingestion candidate boundary")
    if isinstance(candidate["safe_metadata"], Mapping):
        candidate["safe_metadata"].setdefault("helper_family", HELPER_FAMILY_V1)
        candidate["safe_metadata"].setdefault("schema_family", SCHEMA_VERSION_V1)
        candidate["safe_metadata"].setdefault("no_raw_content_retention", True)
    return candidate


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


def _validate_subpacket(name: str, packet: Any, validator) -> tuple[bool, list[str], dict[str, Any] | None]:
    if not isinstance(packet, Mapping):
        return False, [f"invalid_{name}_type"], None
    validation = validator(packet)
    blocked_labels: list[str] = []
    if not isinstance(validation, Mapping):
        blocked_labels.append(f"invalid_{name}_validation")
        return False, blocked_labels, None
    if validation.get("blocked") is True or validation.get("valid") is not True:
        blocked_labels.append(f"blocked_{name}_validation")
    return not blocked_labels, blocked_labels, dict(validation)


def validate_mlcf_controlled_information_ingestion_candidate_v1(candidate: Any) -> dict[str, Any]:
    if not isinstance(candidate, Mapping):
        return {
            "schema_version": SCHEMA_VERSION_V1,
            "valid": False,
            "blocked": True,
            "blocked_labels": ["invalid_candidate_type"],
            "validation_posture": "blocked",
            "summary_text": "Blocked MLCF controlled information ingestion candidate: invalid candidate type.",
        }

    blocked_labels: list[str] = []
    for field in _REQUIRED_FIELD_NAMES_V1:
        if field not in candidate:
            blocked_labels.append(f"missing_{field}")

    for field in _REQUIRED_TEXT_FIELDS_V1:
        if not _compact_text(candidate.get(field)):
            blocked_labels.append(f"missing_{field}")

    for field in _REQUIRED_LIST_FIELDS_V1:
        value = candidate.get(field)
        if not isinstance(value, list):
            blocked_labels.append(f"invalid_{field}")
        elif not value:
            blocked_labels.append(f"missing_{field}")
        elif any(_compact_text(item) == "" for item in value):
            blocked_labels.append(f"invalid_{field}")

    if _compact_text(candidate.get("schema_version")) != SCHEMA_VERSION_V1:
        blocked_labels.append("invalid_schema_version")

    if _compact_text(candidate.get("input_kind")) not in _ALLOWED_INPUT_KINDS_V1:
        blocked_labels.append("invalid_input_kind")
    if _compact_text(candidate.get("signal_family")) not in _ALLOWED_SIGNAL_FAMILIES_V1:
        blocked_labels.append("invalid_signal_family")
    if _compact_text(candidate.get("next_safe_step")) not in _ALLOWED_NEXT_STEP_LABELS_V1:
        blocked_labels.append("invalid_next_safe_step")
    if _compact_text(candidate.get("recommended_ledger_id")) not in _ALLOWED_LEDGER_IDS_V1:
        blocked_labels.append("invalid_recommended_ledger_id")

    if candidate.get("raw_content_retained") is not False:
        blocked_labels.append("unsafe_raw_content_retained")

    authority_status = candidate.get("authority_status")
    _, authority_labels = _authority_status_is_fail_closed(authority_status)
    blocked_labels.extend(authority_labels)

    safe_metadata = candidate.get("safe_metadata")
    _, safe_labels = _safe_metadata_is_fail_closed(safe_metadata)
    blocked_labels.extend(safe_labels)

    boundary_ok, boundary_labels, boundary_validation = _validate_subpacket(
        "authorized_ingestion_boundary_packet",
        candidate.get("authorized_ingestion_boundary_packet"),
        validate_authorized_ingestion_boundary_packet_v1,
    )
    if not boundary_ok:
        blocked_labels.extend(boundary_labels)
    elif candidate.get("authorized_ingestion_boundary_validation") != boundary_validation:
        blocked_labels.append("mismatched_authorized_ingestion_boundary_validation")

    evidence_ok, evidence_labels, evidence_validation = _validate_subpacket(
        "evidence_intake_packet",
        candidate.get("evidence_intake_packet"),
        validate_real_findings_evidence_intake_packet_v1,
    )
    if not evidence_ok:
        blocked_labels.extend(evidence_labels)
    elif candidate.get("evidence_intake_validation") != evidence_validation:
        blocked_labels.append("mismatched_evidence_intake_validation")

    direction_ok, direction_labels, direction_validation = _validate_subpacket(
        "calibrated_proposed_direction_packet",
        candidate.get("calibrated_proposed_direction_packet"),
        validate_calibrated_proposed_direction_v1,
    )
    if not direction_ok:
        blocked_labels.extend(direction_labels)
    elif candidate.get("calibrated_proposed_direction_validation") != direction_validation:
        blocked_labels.append("mismatched_calibrated_proposed_direction_validation")

    if not isinstance(candidate.get("ledger_registry_summary"), Mapping):
        blocked_labels.append("invalid_ledger_registry_summary")
    else:
        registry_summary = dict(candidate.get("ledger_registry_summary"))
        if registry_summary.get("validation_posture") != "valid":
            blocked_labels.append("invalid_ledger_registry_summary_validation_posture")
        if registry_summary.get("canonical_ledger_ids") != list(_ALLOWED_LEDGER_IDS_V1):
            blocked_labels.append("invalid_ledger_registry_summary_canonical_ids")

    if _compact_text(candidate.get("recommended_ledger_id")) != _recommend_ledger_id(
        _compact_text(candidate.get("input_kind")),
        _compact_text(candidate.get("signal_family")),
        _compact_text(candidate.get("input_summary")),
    ):
        blocked_labels.append("mismatched_recommended_ledger_id")

    if _compact_text(candidate.get("next_safe_step")) != _recommended_next_step(_compact_text(candidate.get("signal_family"))):
        blocked_labels.append("mismatched_next_safe_step")

    if _compact_text(candidate.get("confidence_posture")) != _recommended_confidence_posture(_compact_text(candidate.get("signal_family"))):
        blocked_labels.append("mismatched_confidence_posture")

    if _normalize_text_list(candidate.get("calibration_axes_to_apply")) != _recommended_axes(_compact_text(candidate.get("signal_family"))):
        blocked_labels.append("mismatched_calibration_axes_to_apply")

    implemented_axes = {axis["axis_id"] for axis in build_initial_theoretical_calibration_axes_examples_v1()["axes"]}
    for axis in _normalize_text_list(candidate.get("calibration_axes_to_apply")):
        if axis not in implemented_axes:
            blocked_labels.append(f"invalid_calibration_axis:{axis}")

    for field_name in (
        "candidate_id",
        "input_kind",
        "input_scope",
        "input_summary",
        "source_access_status",
        "recommended_ledger_reason",
        "confidence_posture",
        "calibration_reason",
        "next_safe_step",
    ):
        if _contains_text_markers(candidate.get(field_name), _HIDDEN_PRIVATE_PROTECTED_MARKERS_V1):
            blocked_labels.append("forbidden_hidden_private_protected_marker")
    if _contains_text_markers(candidate.get("authority_status", {}).get("boundary_notes") if isinstance(candidate.get("authority_status"), Mapping) else None, _AUTHORITY_TEXT_MARKERS_V1):
        blocked_labels.append("unsafe_authority_text")
    if _contains_text_markers(candidate.get("safe_metadata", {}).get("boundary_notes") if isinstance(candidate.get("safe_metadata"), Mapping) else None, _AUTHORITY_TEXT_MARKERS_V1):
        blocked_labels.append("unsafe_safe_metadata_text")
    if _contains_text_markers(candidate.get("authority_status", {}).get("boundary_notes") if isinstance(candidate.get("authority_status"), Mapping) else None, _HIDDEN_PRIVATE_PROTECTED_MARKERS_V1):
        blocked_labels.append("forbidden_hidden_private_protected_marker")
    if _contains_text_markers(candidate.get("safe_metadata", {}).get("boundary_notes") if isinstance(candidate.get("safe_metadata"), Mapping) else None, _HIDDEN_PRIVATE_PROTECTED_MARKERS_V1):
        blocked_labels.append("forbidden_hidden_private_protected_marker")
    if _first_non_json_safe_path(candidate) is not None:
        blocked_labels.append("non_json_safe_output")

    valid = not blocked_labels
    summary_text = (
        "Valid MLCF controlled information ingestion candidate."
        if valid
        else "Blocked MLCF controlled information ingestion candidate: metadata, authority, subpacket, or safety checks failed."
    )
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "valid": valid,
        "blocked": not valid,
        "blocked_labels": blocked_labels,
        "validation_posture": "valid" if valid else "blocked",
        "summary_text": summary_text,
    }


def summarize_mlcf_controlled_information_ingestion_candidate_v1(candidate: Any) -> dict[str, Any]:
    raw = candidate if isinstance(candidate, Mapping) else {}
    validation = validate_mlcf_controlled_information_ingestion_candidate_v1(raw) if isinstance(raw, Mapping) else {}
    axes = _normalize_text_list(raw.get("calibration_axes_to_apply"))
    ledger_registry_summary = raw.get("ledger_registry_summary") if isinstance(raw.get("ledger_registry_summary"), Mapping) else {}
    return {
        "candidate_id": _compact_text(raw.get("candidate_id"), "unknown_candidate"),
        "input_kind": _compact_text(raw.get("input_kind"), "unknown_input_kind"),
        "signal_family": _compact_text(raw.get("signal_family"), "unknown_signal_family"),
        "recommended_ledger_id": _compact_text(raw.get("recommended_ledger_id"), "unknown_ledger"),
        "next_safe_step": _compact_text(raw.get("next_safe_step"), "unknown_step"),
        "calibration_axes_count": len(axes),
        "validation_posture": _compact_text(validation.get("validation_posture"), "unknown"),
        "ledger_count": int(ledger_registry_summary.get("ledger_count", 0)) if isinstance(ledger_registry_summary, Mapping) else 0,
        "summary_text": (
            f"MLCF controlled candidate {_compact_text(raw.get('candidate_id'), 'unknown_candidate')}: "
            f"{_compact_text(raw.get('signal_family'), 'unknown_signal_family')} -> "
            f"{_compact_text(raw.get('recommended_ledger_id'), 'unknown_ledger')} -> "
            f"{_compact_text(raw.get('next_safe_step'), 'unknown_step')}."
        ),
    }


def to_mlcf_controlled_information_ingestion_candidate_json_safe_v1(packet: Any) -> Any:
    return _json_safe(packet)


def build_initial_mlcf_controlled_information_ingestion_candidate_examples_v1() -> list[dict[str, Any]]:
    return [
        build_mlcf_controlled_information_ingestion_candidate_v1(
            {
                "candidate_id": "owner_architecture_observation_ingestion_candidate",
                "input_kind": "owner_supplied_observation_summary",
                "input_scope": "architecture direction and MLCF design",
                "input_summary": "Owner-observed architecture direction suggests MLCF should stay layered, event-sourced, and workspace-scoped.",
                "signal_family": "architecture_direction_signal",
                "source_access_status": "metadata_only",
                "next_safe_step": "pressure_test",
            }
        ),
        build_mlcf_controlled_information_ingestion_candidate_v1(
            {
                "candidate_id": "owner_repeating_signal_ingestion_candidate",
                "input_kind": "owner_supplied_observation_summary",
                "input_scope": "repeating signal about WESLR behavior",
                "input_summary": "A repeating signal is visible across several owner observations and should be pressure-tested rather than promoted.",
                "signal_family": "repeating_signal",
                "source_access_status": "metadata_only",
                "next_safe_step": "pressure_test",
            }
        ),
        build_mlcf_controlled_information_ingestion_candidate_v1(
            {
                "candidate_id": "blocked_public_claim_ingestion_candidate",
                "input_kind": "blocked_or_unknown_source_summary",
                "input_scope": "public-claim pressure scenario",
                "input_summary": "The source pressure looks like a public claim attempt and must stay blocked from promotion.",
                "signal_family": "blocked_public_claim_signal",
                "source_access_status": "blocked",
                "next_safe_step": "blocked_by_safety",
            }
        ),
    ]
