"""WESLR Theoretical Calibration Axes V1.

Deterministic, metadata-only helpers for turning theory families into bounded
calibration metadata. A theory is only useful here when it calibrates a
specific WESLR failure mode.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Iterable, Mapping

SCHEMA_VERSION_V1 = "theoretical_calibration_axes_v1"
AXIS_SET_ID_V1 = "theoretical_calibration_axes_set_v1"

_ALLOWED_NEXT_STEP_LABELS_V1 = (
    "probe",
    "pressure_test",
    "calibrate",
    "watch",
    "archive",
    "operator_review",
    "blocked_by_safety",
    "needs_repair",
)

_ALLOWED_FAILURE_MODES_V1 = (
    "calibrate_everything",
    "creative_but_unpressuretested_candidate",
    "fake_certainty_inside_incomplete_system",
    "unfalsifiable_direction",
    "confidence_does_not_move_or_moves_too_fast",
    "noise_as_signal_or_signal_as_noise",
    "endless_calibration_loop_or_overreaction",
    "pattern_without_explanatory_gain",
    "correlation_claimed_as_cause",
    "belief_distorted_by_strategy_or_incentives",
    "weak_candidates_never_evolve_or_never_die",
    "fake_analogy",
    "flat_timing_or_infinite_wait",
)

_REQUIRED_AXIS_IDS_V1 = (
    "reverse_calibration_backcasting",
    "adversarial_gan_calibration",
    "godel_incompleteness_calibration",
    "popper_falsification_calibration",
    "bayesian_calibration",
    "signal_detection_calibration",
    "cybernetic_control_calibration",
    "information_theory_compression_calibration",
    "causal_counterfactual_calibration",
    "game_theory_incentive_calibration",
    "evolutionary_calibration",
    "topological_structure_preserving_calibration",
    "nonlinear_escalation_schedule_calibration",
)

_REQUIRED_AXIS_FAILURE_MODE_MAP_V1 = {
    "reverse_calibration_backcasting": "calibrate_everything",
    "adversarial_gan_calibration": "creative_but_unpressuretested_candidate",
    "godel_incompleteness_calibration": "fake_certainty_inside_incomplete_system",
    "popper_falsification_calibration": "unfalsifiable_direction",
    "bayesian_calibration": "confidence_does_not_move_or_moves_too_fast",
    "signal_detection_calibration": "noise_as_signal_or_signal_as_noise",
    "cybernetic_control_calibration": "endless_calibration_loop_or_overreaction",
    "information_theory_compression_calibration": "pattern_without_explanatory_gain",
    "causal_counterfactual_calibration": "correlation_claimed_as_cause",
    "game_theory_incentive_calibration": "belief_distorted_by_strategy_or_incentives",
    "evolutionary_calibration": "weak_candidates_never_evolve_or_never_die",
    "topological_structure_preserving_calibration": "fake_analogy",
    "nonlinear_escalation_schedule_calibration": "flat_timing_or_infinite_wait",
}

_REQUIRED_AXIS_FIELDS_V1 = (
    "axis_id",
    "theory_family",
    "calibrated_failure_mode",
    "calibration_question",
    "safe_internal_use",
    "forbidden_misuse",
    "next_step_effect",
    "example_application",
    "authority_status",
    "safe_metadata",
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
    "no_weslr_io",
    "no_weslr_read",
    "no_weslr_write",
    "no_weslr_persistence",
    "no_database_writes",
    "no_memory_mutation",
    "no_project_mutation",
    "no_public_claim_authority",
    "no_final_answer_authority",
    "no_discovery_claims",
    "no_proof_claims",
    "no_benchmark_claims",
    "no_score_claims",
    "no_agi_claims",
    "no_public_science_claims",
    "no_hidden_private_protected_markers",
)

_AUTHORITY_STATUS_FALSE_FLAGS_V1 = (
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
    "hidden_private_protected_authorized",
    "public_science_claim_authorized",
    "proof_claim_authorized",
    "benchmark_claim_authorized",
    "agi_claim_authorized",
    "automatic_discovery_authorized",
)

_AUTHORITY_MARKERS_V1 = (
    "discovery",
    "proof",
    "benchmark",
    "score",
    "agi",
    "intelligence",
    "sentience",
    "consciousness",
    "public claim authorized",
    "final answer authority",
    "runtime authorization",
    "source ingestion authorization",
    "provider/model/tool/retrieval/web implication",
    ".weslr implication",
    ".weslr read/write implication",
    ".weslr persistence/state implication",
    "persistence/database implication",
    "memory/project mutation implication",
    "hidden/private/protected markers",
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

_AXIS_SET_PREVENTION_THEMES_V1 = (
    "everything_becomes_calibrate",
    "everything_becomes_discovery",
    "safe_cognition_not_suppressed",
    "weak_signals_not_overclaimed",
    "strong_signals_not_archived_too_early",
    "metaphors_not_treated_as_evidence",
    "correlation_not_treated_as_cause",
    "untestable_ideas_not_promoted",
    "loops_do_not_continue_forever",
    "public_authority_not_too_early",
)

_DEFAULT_RELATIONSHIP_TO_EXISTING_ARTIFACTS_V1 = {
    "comparative_artifact": "proves differentiation exists at the bridge layer",
    "reverse_calibration_trace": "explains why differentiated steps are justified",
    "capability_suppression_audit": "keeps safety strict on authority while permissive on safe internal reasoning",
    "future_ingestion": "must consult these axes before producing proposed directions",
}

_DEFAULT_FUTURE_INGESTION_BOUNDARY_V1 = {
    "authorized": False,
    "scope": "pre-ingestion_calibration_only",
    "forbidden": [
        "runtime_wiring",
        "source_ingestion",
        "provider_model_tool_web_calls",
        ".weslr_io",
        "persistence",
        "memory_project_mutation",
        "public_claim_authority",
        "final_answer_authority",
    ],
}

_DEFAULT_AXIS_AUTHORITY_STATUS_V1 = {
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
    "hidden_private_protected_authorized": False,
    "public_science_claim_authorized": False,
    "proof_claim_authorized": False,
    "benchmark_claim_authorized": False,
    "agi_claim_authorized": False,
    "automatic_discovery_authorized": False,
    "all_authority_flags_false": True,
    "status": "metadata_only",
    "boundary_notes": "metadata-only theoretical calibration axis boundary",
}

_DEFAULT_AXIS_SAFE_METADATA_V1 = {
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
    "no_weslr_io": True,
    "no_weslr_read": True,
    "no_weslr_write": True,
    "no_weslr_persistence": True,
    "no_database_writes": True,
    "no_memory_mutation": True,
    "no_project_mutation": True,
    "no_public_claim_authority": True,
    "no_final_answer_authority": True,
    "no_discovery_claims": True,
    "no_proof_claims": True,
    "no_benchmark_claims": True,
    "no_score_claims": True,
    "no_agi_claims": True,
    "no_public_science_claims": True,
    "no_hidden_private_protected_markers": True,
    "axis_family": "theoretical_calibration",
}

_CANONICAL_AXIS_SPECS_V1 = (
    {
        "axis_id": "reverse_calibration_backcasting",
        "theory_family": "reverse_calibration",
        "calibrated_failure_mode": "calibrate_everything",
        "calibration_question": "What earlier signal phase justifies the next step without collapsing everything into calibration?",
        "safe_internal_use": "Back-map from known outcomes to earlier signal phases and step selection.",
        "forbidden_misuse": "Treating backcasting as discovery, proof, or prediction authority.",
        "next_step_effect": "probe",
        "example_application": "Explain why a known-outcome trace starts with probe rather than immediate calibration.",
        "authority_status": {**_DEFAULT_AXIS_AUTHORITY_STATUS_V1},
        "safe_metadata": {**_DEFAULT_AXIS_SAFE_METADATA_V1, "axis_id": "reverse_calibration_backcasting", "failure_mode": "calibrate_everything"},
    },
    {
        "axis_id": "adversarial_gan_calibration",
        "theory_family": "adversarial_pressure",
        "calibrated_failure_mode": "creative_but_unpressuretested_candidate",
        "calibration_question": "Does the candidate survive critique, counterexample pressure, and adversarial selection?",
        "safe_internal_use": "Stress-test candidates before promoting them.",
        "forbidden_misuse": "Public claim escalation, runtime adversarial deployment, or unsafe optimization pressure.",
        "next_step_effect": "pressure_test",
        "example_application": "Reject an elegant idea that fails under small adversarial probes.",
        "authority_status": {**_DEFAULT_AXIS_AUTHORITY_STATUS_V1},
        "safe_metadata": {**_DEFAULT_AXIS_SAFE_METADATA_V1, "axis_id": "adversarial_gan_calibration", "failure_mode": "creative_but_unpressuretested_candidate"},
    },
    {
        "axis_id": "godel_incompleteness_calibration",
        "theory_family": "incompleteness",
        "calibrated_failure_mode": "fake_certainty_inside_incomplete_system",
        "calibration_question": "Where does the system need humility because not everything can be resolved internally?",
        "safe_internal_use": "Mark irreducible limits and avoid pretending closure exists.",
        "forbidden_misuse": "Using incompleteness to justify public uncertainty theater or permanent paralysis.",
        "next_step_effect": "operator_review",
        "example_application": "Recognize a boundary where the model cannot prove what it is being asked to prove.",
        "authority_status": {**_DEFAULT_AXIS_AUTHORITY_STATUS_V1},
        "safe_metadata": {**_DEFAULT_AXIS_SAFE_METADATA_V1, "axis_id": "godel_incompleteness_calibration", "failure_mode": "fake_certainty_inside_incomplete_system"},
    },
    {
        "axis_id": "popper_falsification_calibration",
        "theory_family": "falsification",
        "calibrated_failure_mode": "unfalsifiable_direction",
        "calibration_question": "What observation would make the direction fail?",
        "safe_internal_use": "Force explicit disconfirming signals and tests.",
        "forbidden_misuse": "Pretending an unfalsifiable idea is evidence-backed.",
        "next_step_effect": "probe",
        "example_application": "Require a disconfirming signal before accepting a new explanation.",
        "authority_status": {**_DEFAULT_AXIS_AUTHORITY_STATUS_V1},
        "safe_metadata": {**_DEFAULT_AXIS_SAFE_METADATA_V1, "axis_id": "popper_falsification_calibration", "failure_mode": "unfalsifiable_direction"},
    },
    {
        "axis_id": "bayesian_calibration",
        "theory_family": "bayesian_update",
        "calibrated_failure_mode": "confidence_does_not_move_or_moves_too_fast",
        "calibration_question": "Does evidence move confidence at the right speed?",
        "safe_internal_use": "Update belief posture proportionally to evidence.",
        "forbidden_misuse": "Treating Bayesian language as a guarantee of truth or authority.",
        "next_step_effect": "calibrate",
        "example_application": "Slow confidence when evidence is thin; accelerate only when evidence repeats.",
        "authority_status": {**_DEFAULT_AXIS_AUTHORITY_STATUS_V1},
        "safe_metadata": {**_DEFAULT_AXIS_SAFE_METADATA_V1, "axis_id": "bayesian_calibration", "failure_mode": "confidence_does_not_move_or_moves_too_fast"},
    },
    {
        "axis_id": "signal_detection_calibration",
        "theory_family": "signal_detection",
        "calibrated_failure_mode": "noise_as_signal_or_signal_as_noise",
        "calibration_question": "Is this a true signal, a false positive, or a false negative?",
        "safe_internal_use": "Balance sensitivity and specificity.",
        "forbidden_misuse": "Rebranding noise as evidence or evidence as noise to fit a preferred story.",
        "next_step_effect": "watch",
        "example_application": "Keep a repeating pattern in view without declaring it real too early.",
        "authority_status": {**_DEFAULT_AXIS_AUTHORITY_STATUS_V1},
        "safe_metadata": {**_DEFAULT_AXIS_SAFE_METADATA_V1, "axis_id": "signal_detection_calibration", "failure_mode": "noise_as_signal_or_signal_as_noise"},
    },
    {
        "axis_id": "cybernetic_control_calibration",
        "theory_family": "control_theory",
        "calibrated_failure_mode": "endless_calibration_loop_or_overreaction",
        "calibration_question": "Is the loop correcting smoothly or oscillating, stalling, or overreacting?",
        "safe_internal_use": "Tune loop gain, timing, and damping.",
        "forbidden_misuse": "Turning calibration into self-excusing recursion or unsafe feedback escalation.",
        "next_step_effect": "watch",
        "example_application": "Stop an overactive correction loop from amplifying itself.",
        "authority_status": {**_DEFAULT_AXIS_AUTHORITY_STATUS_V1},
        "safe_metadata": {**_DEFAULT_AXIS_SAFE_METADATA_V1, "axis_id": "cybernetic_control_calibration", "failure_mode": "endless_calibration_loop_or_overreaction"},
    },
    {
        "axis_id": "information_theory_compression_calibration",
        "theory_family": "information_theory",
        "calibrated_failure_mode": "pattern_without_explanatory_gain",
        "calibration_question": "Does the explanation compress observations better than the raw pattern list?",
        "safe_internal_use": "Test whether an explanation actually reduces complexity.",
        "forbidden_misuse": "Claiming compression as truth or proof.",
        "next_step_effect": "archive",
        "example_application": "Reject a pattern that is memorable but not explanatory.",
        "authority_status": {**_DEFAULT_AXIS_AUTHORITY_STATUS_V1},
        "safe_metadata": {**_DEFAULT_AXIS_SAFE_METADATA_V1, "axis_id": "information_theory_compression_calibration", "failure_mode": "pattern_without_explanatory_gain"},
    },
    {
        "axis_id": "causal_counterfactual_calibration",
        "theory_family": "causal_inference",
        "calibrated_failure_mode": "correlation_claimed_as_cause",
        "calibration_question": "What would change under a counterfactual intervention?",
        "safe_internal_use": "Separate cause from co-occurrence.",
        "forbidden_misuse": "Promoting causal claims without intervention logic.",
        "next_step_effect": "pressure_test",
        "example_application": "Distinguish a correlated signal from an actual driver.",
        "authority_status": {**_DEFAULT_AXIS_AUTHORITY_STATUS_V1},
        "safe_metadata": {**_DEFAULT_AXIS_SAFE_METADATA_V1, "axis_id": "causal_counterfactual_calibration", "failure_mode": "correlation_claimed_as_cause"},
    },
    {
        "axis_id": "game_theory_incentive_calibration",
        "theory_family": "game_theory",
        "calibrated_failure_mode": "belief_distorted_by_strategy_or_incentives",
        "calibration_question": "Is the observed behavior shaped by incentives rather than the underlying fact?",
        "safe_internal_use": "Detect strategic distortion and adversarial pressure.",
        "forbidden_misuse": "Assuming incentives are irrelevant or using game theory to justify manipulation.",
        "next_step_effect": "operator_review",
        "example_application": "Treat a claim differently when the speaker benefits from distortion.",
        "authority_status": {**_DEFAULT_AXIS_AUTHORITY_STATUS_V1},
        "safe_metadata": {**_DEFAULT_AXIS_SAFE_METADATA_V1, "axis_id": "game_theory_incentive_calibration", "failure_mode": "belief_distorted_by_strategy_or_incentives"},
    },
    {
        "axis_id": "evolutionary_calibration",
        "theory_family": "evolutionary_selection",
        "calibrated_failure_mode": "weak_candidates_never_evolve_or_never_die",
        "calibration_question": "Are variants being selected, retired, and improved at the right rate?",
        "safe_internal_use": "Manage variation, selection, and pruning of candidates.",
        "forbidden_misuse": "Turning evolution language into justification for unbounded churn or permanent retention.",
        "next_step_effect": "watch",
        "example_application": "Let weak candidates die while preserving promising variants.",
        "authority_status": {**_DEFAULT_AXIS_AUTHORITY_STATUS_V1},
        "safe_metadata": {**_DEFAULT_AXIS_SAFE_METADATA_V1, "axis_id": "evolutionary_calibration", "failure_mode": "weak_candidates_never_evolve_or_never_die"},
    },
    {
        "axis_id": "topological_structure_preserving_calibration",
        "theory_family": "topology",
        "calibrated_failure_mode": "fake_analogy",
        "calibration_question": "Does the cross-domain mapping preserve structure or merely sound similar?",
        "safe_internal_use": "Test whether a metaphor keeps the right shape under transformation.",
        "forbidden_misuse": "Treating analogy as evidence or proof.",
        "next_step_effect": "pressure_test",
        "example_application": "Reject a cross-domain mapping that breaks when simplified.",
        "authority_status": {**_DEFAULT_AXIS_AUTHORITY_STATUS_V1},
        "safe_metadata": {**_DEFAULT_AXIS_SAFE_METADATA_V1, "axis_id": "topological_structure_preserving_calibration", "failure_mode": "fake_analogy"},
    },
    {
        "axis_id": "nonlinear_escalation_schedule_calibration",
        "theory_family": "nonlinear_timing",
        "calibrated_failure_mode": "flat_timing_or_infinite_wait",
        "calibration_question": "When should the system recheck, widen, escalate, or archive?",
        "safe_internal_use": "Shape timing and escalation without dead loops or premature closure.",
        "forbidden_misuse": "Using schedule theory to justify endless waiting or perpetual urgency.",
        "next_step_effect": "watch",
        "example_application": "Recheck at a controlled cadence instead of stalling forever.",
        "authority_status": {**_DEFAULT_AXIS_AUTHORITY_STATUS_V1},
        "safe_metadata": {**_DEFAULT_AXIS_SAFE_METADATA_V1, "axis_id": "nonlinear_escalation_schedule_calibration", "failure_mode": "flat_timing_or_infinite_wait"},
    },
)


def _merge_payload(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    if isinstance(payload, Mapping):
        merged.update(payload)
    merged.update({key: value for key, value in overrides.items() if value is not None})
    return merged


def _compact_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


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
    if isinstance(value, str):
        return value
    if isinstance(value, (bool, int, float)) or value is None:
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


def _contains_markers(value: Any, markers: tuple[str, ...]) -> bool:
    if isinstance(value, Mapping):
        return any(_contains_markers(item, markers) for item in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(_contains_markers(item, markers) for item in value)
    if not isinstance(value, str):
        return False
    lowered = value.lower()
    return any(marker in lowered for marker in markers)


def _ensure_axis_authority_status(authority_status: Any) -> dict[str, Any]:
    if not isinstance(authority_status, Mapping):
        return {}
    return {str(key): value for key, value in authority_status.items()}


def _ensure_axis_safe_metadata(safe_metadata: Any) -> dict[str, Any]:
    if not isinstance(safe_metadata, Mapping):
        return {}
    return {str(key): value for key, value in safe_metadata.items()}


def allowed_theoretical_calibration_next_steps_v1() -> tuple[str, ...]:
    return _ALLOWED_NEXT_STEP_LABELS_V1


def allowed_theoretical_calibration_failure_modes_v1() -> tuple[str, ...]:
    return _ALLOWED_FAILURE_MODES_V1


def _default_authority_status() -> dict[str, Any]:
    return {**_DEFAULT_AXIS_AUTHORITY_STATUS_V1}


def _default_safe_metadata(axis_id: str = "theoretical_calibration_axis", failure_mode: str = "unknown") -> dict[str, Any]:
    return {
        **_DEFAULT_AXIS_SAFE_METADATA_V1,
        "axis_id": axis_id,
        "failure_mode": failure_mode,
        "helper_family": SCHEMA_VERSION_V1,
    }


def build_theoretical_calibration_axis_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = _merge_payload(payload, **overrides)
    axis_id = _compact_text(data.get("axis_id"))
    failure_mode = _compact_text(data.get("calibrated_failure_mode"), default="unknown")
    built = {
        "axis_id": axis_id,
        "theory_family": _compact_text(data.get("theory_family")),
        "calibrated_failure_mode": failure_mode,
        "calibration_question": _compact_text(data.get("calibration_question")),
        "safe_internal_use": _compact_text(data.get("safe_internal_use")),
        "forbidden_misuse": _compact_text(data.get("forbidden_misuse")),
        "next_step_effect": _compact_text(data.get("next_step_effect")),
        "example_application": _compact_text(data.get("example_application")),
        "authority_status": _ensure_axis_authority_status(data.get("authority_status") or _default_authority_status()),
        "safe_metadata": _ensure_axis_safe_metadata(
            data.get("safe_metadata") or _default_safe_metadata(axis_id=axis_id or "theoretical_calibration_axis", failure_mode=failure_mode)
        ),
    }
    return built


def _validate_authority_status(authority_status: Any, blocked_labels: list[str]) -> None:
    if not isinstance(authority_status, Mapping):
        blocked_labels.append("missing_authority_status")
        return
    status = {str(key): value for key, value in authority_status.items()}
    for flag in _AUTHORITY_STATUS_FALSE_FLAGS_V1:
        if flag in status and status[flag] is True:
            blocked_labels.append(f"unsafe_authority_flag:{flag}")
    if status.get("all_authority_flags_false") is not True:
        blocked_labels.append("unsafe_authority_flag:all_authority_flags_false")
    if _contains_markers(status, _AUTHORITY_MARKERS_V1):
        blocked_labels.append("unsafe_authority_text")
    if _contains_markers(status, _HIDDEN_PRIVATE_PROTECTED_MARKERS_V1):
        blocked_labels.append("forbidden_hidden_private_protected_marker")
    if status.get("status") not in (None, "metadata_only"):
        blocked_labels.append("unsafe_authority_status")


def _validate_safe_metadata(safe_metadata: Any, blocked_labels: list[str]) -> None:
    if not isinstance(safe_metadata, Mapping):
        blocked_labels.append("missing_safe_metadata")
        return
    metadata = {str(key): value for key, value in safe_metadata.items()}
    for flag in _SAFE_METADATA_REQUIRED_TRUE_FLAGS_V1:
        if flag not in metadata:
            blocked_labels.append(f"missing_safe_metadata_flag:{flag}")
        elif metadata[flag] is not True:
            blocked_labels.append(f"unsafe_safe_metadata_flag:{flag}")
    if _contains_markers(metadata, _AUTHORITY_MARKERS_V1):
        blocked_labels.append("unsafe_safe_metadata_text")
    if _contains_markers(metadata, _HIDDEN_PRIVATE_PROTECTED_MARKERS_V1):
        blocked_labels.append("forbidden_hidden_private_protected_marker")


def validate_theoretical_calibration_axis_v1(axis: Any) -> dict[str, Any]:
    blocked_labels: list[str] = []
    if not isinstance(axis, Mapping):
        return {
            "schema_version": SCHEMA_VERSION_V1,
            "valid": False,
            "blocked": True,
            "validation_posture": "needs_repair",
            "blocked_labels": ["not_a_mapping"],
            "summary_text": "Blocked theoretical calibration axis: not a mapping.",
        }

    axis_data = {str(key): value for key, value in axis.items()}
    non_json_safe_path = _first_non_json_safe_path(axis_data)
    if non_json_safe_path is not None:
        blocked_labels.append("non_json_safe_output")

    for field in _REQUIRED_AXIS_FIELDS_V1:
        if field not in axis_data:
            blocked_labels.append(f"missing_{field}")

    axis_id = _compact_text(axis_data.get("axis_id"))
    theory_family = _compact_text(axis_data.get("theory_family"))
    failure_mode = _compact_text(axis_data.get("calibrated_failure_mode"))
    calibration_question = _compact_text(axis_data.get("calibration_question"))
    safe_internal_use = _compact_text(axis_data.get("safe_internal_use"))
    forbidden_misuse = _compact_text(axis_data.get("forbidden_misuse"))
    next_step_effect = _compact_text(axis_data.get("next_step_effect"))
    example_application = _compact_text(axis_data.get("example_application"))

    if not axis_id:
        blocked_labels.append("missing_axis_id")
    if not theory_family:
        blocked_labels.append("missing_theory_family")
    if not failure_mode:
        blocked_labels.append("missing_failure_mode")
    elif failure_mode not in _ALLOWED_FAILURE_MODES_V1:
        blocked_labels.append("unknown_failure_mode")
    if not calibration_question:
        blocked_labels.append("missing_calibration_question")
    if not safe_internal_use:
        blocked_labels.append("missing_safe_internal_use")
    if not forbidden_misuse:
        blocked_labels.append("missing_forbidden_misuse")
    if not next_step_effect:
        blocked_labels.append("missing_next_step_effect")
    elif next_step_effect not in _ALLOWED_NEXT_STEP_LABELS_V1:
        blocked_labels.append("invalid_next_step_effect")
    if not example_application:
        blocked_labels.append("missing_example_application")

    _validate_authority_status(axis_data.get("authority_status"), blocked_labels)
    _validate_safe_metadata(axis_data.get("safe_metadata"), blocked_labels)

    if _contains_markers(axis_data, _HIDDEN_PRIVATE_PROTECTED_MARKERS_V1):
        blocked_labels.append("forbidden_hidden_private_protected_marker")

    expected_failure_mode = _REQUIRED_AXIS_FAILURE_MODE_MAP_V1.get(axis_id)
    if axis_id and expected_failure_mode is None:
        blocked_labels.append("unknown_axis_id")
    elif expected_failure_mode is not None and failure_mode and expected_failure_mode != failure_mode:
        blocked_labels.append(f"axis_failure_mode_mismatch:{axis_id}")

    blocked = bool(blocked_labels)
    posture = "valid" if not blocked else ("blocked" if any(label.startswith("unsafe_") or label.startswith("missing_") or label.startswith("invalid_") or label.startswith("unknown_") or label.startswith("non_json_safe") for label in blocked_labels) else "needs_repair")
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "axis_id": axis_id or None,
        "theory_family": theory_family or None,
        "calibrated_failure_mode": failure_mode or None,
        "valid": not blocked,
        "blocked": blocked,
        "validation_posture": posture,
        "blocked_labels": blocked_labels,
        "summary_text": "Valid theoretical calibration axis." if not blocked else "Blocked theoretical calibration axis.",
    }


def build_theoretical_calibration_axes_set_v1(axes: Any = None) -> dict[str, Any]:
    if axes is None:
        axes_list = [build_theoretical_calibration_axis_v1(deepcopy(axis)) for axis in _CANONICAL_AXIS_SPECS_V1]
    else:
        if isinstance(axes, Mapping) and "axes" in axes:
            axes_value = axes["axes"]
        else:
            axes_value = axes
        axes_list = [build_theoretical_calibration_axis_v1(deepcopy(axis)) for axis in list(axes_value)]
    packet = {
        "axis_set_id": AXIS_SET_ID_V1,
        "axes": axes_list,
        "combined_stack_effect": {
            "prevention_themes": list(_AXIS_SET_PREVENTION_THEMES_V1),
            "summary": "Use big theory only when it calibrates a specific WESLR failure mode.",
        },
        "relationship_to_existing_artifacts": deepcopy(_DEFAULT_RELATIONSHIP_TO_EXISTING_ARTIFACTS_V1),
        "future_ingestion_boundary": deepcopy(_DEFAULT_FUTURE_INGESTION_BOUNDARY_V1),
        "authority_status": _default_authority_status(),
        "safe_metadata": _default_safe_metadata(axis_id=AXIS_SET_ID_V1, failure_mode="set"),
    }
    return packet


def build_initial_theoretical_calibration_axes_examples_v1() -> dict[str, Any]:
    return build_theoretical_calibration_axes_set_v1()


def _unique_values(values: Iterable[str]) -> list[str]:
    seen: list[str] = []
    for value in values:
        if value not in seen:
            seen.append(value)
    return seen


def validate_theoretical_calibration_axes_set_v1(packet: Any) -> dict[str, Any]:
    blocked_labels: list[str] = []
    if not isinstance(packet, Mapping):
        return {
            "schema_version": SCHEMA_VERSION_V1,
            "valid": False,
            "blocked": True,
            "validation_posture": "needs_repair",
            "blocked_labels": ["not_a_mapping"],
            "summary_text": "Blocked theoretical calibration axes set: not a mapping.",
        }

    data = {str(key): value for key, value in packet.items()}
    non_json_safe_path = _first_non_json_safe_path(data)
    if non_json_safe_path is not None:
        blocked_labels.append("non_json_safe_output")

    if not _compact_text(data.get("axis_set_id")):
        blocked_labels.append("missing_axis_set_id")
    elif _compact_text(data.get("axis_set_id")) != AXIS_SET_ID_V1:
        blocked_labels.append("invalid_axis_set_id")

    axes = data.get("axes")
    if not isinstance(axes, list):
        blocked_labels.append("missing_axes")
        axes = []

    axis_validations = [validate_theoretical_calibration_axis_v1(axis) for axis in axes]
    for validation in axis_validations:
        blocked_labels.extend(validation.get("blocked_labels", []))

    axis_ids = [_compact_text(axis.get("axis_id")) for axis in axes if isinstance(axis, Mapping)]
    failure_modes = [_compact_text(axis.get("calibrated_failure_mode")) for axis in axes if isinstance(axis, Mapping)]
    next_steps = [_compact_text(axis.get("next_step_effect")) for axis in axes if isinstance(axis, Mapping)]

    if len(axes) != len(_REQUIRED_AXIS_IDS_V1):
        blocked_labels.append("wrong_axis_count")
    axis_id_set = set(axis_ids)
    required_axis_id_set = set(_REQUIRED_AXIS_IDS_V1)
    if axis_id_set != required_axis_id_set:
        missing = [axis_id for axis_id in _REQUIRED_AXIS_IDS_V1 if axis_id not in axis_id_set]
        extra = [axis_id for axis_id in axis_id_set if axis_id not in required_axis_id_set]
        if missing:
            blocked_labels.append("missing_required_axis_ids")
        if extra:
            blocked_labels.append("unexpected_axis_ids")
    if len(axis_ids) != len(_unique_values(axis_ids)):
        blocked_labels.append("duplicate_axis_ids")

    required_failure_modes = set(_ALLOWED_FAILURE_MODES_V1)
    failure_mode_set = set(failure_modes)
    if failure_mode_set != required_failure_modes:
        missing_modes = [mode for mode in _ALLOWED_FAILURE_MODES_V1 if mode not in failure_mode_set]
        extra_modes = [mode for mode in failure_mode_set if mode not in required_failure_modes]
        if missing_modes:
            blocked_labels.append("missing_required_failure_modes")
        if extra_modes:
            blocked_labels.append("unexpected_failure_modes")
    if len(failure_modes) != len(_unique_values(failure_modes)):
        blocked_labels.append("duplicate_failure_modes")

    if any(step not in _ALLOWED_NEXT_STEP_LABELS_V1 for step in next_steps if step):
        blocked_labels.append("invalid_next_step_effect")

    if _contains_markers(data.get("authority_status"), _AUTHORITY_MARKERS_V1):
        blocked_labels.append("unsafe_authority_text")
    if isinstance(data.get("authority_status"), Mapping):
        for flag, value in data["authority_status"].items():
            if isinstance(value, bool) and value is True and flag not in {"all_authority_flags_false"}:
                blocked_labels.append(f"unsafe_authority_flag:{flag}")
    if isinstance(data.get("authority_status"), Mapping) and data["authority_status"].get("status") not in (None, "metadata_only"):
        blocked_labels.append("unsafe_authority_status")

    if _contains_markers(data.get("safe_metadata"), _AUTHORITY_MARKERS_V1):
        blocked_labels.append("unsafe_safe_metadata_text")
    if _contains_markers(data.get("safe_metadata"), _HIDDEN_PRIVATE_PROTECTED_MARKERS_V1):
        blocked_labels.append("forbidden_hidden_private_protected_marker")

    if _contains_markers(data, _HIDDEN_PRIVATE_PROTECTED_MARKERS_V1):
        blocked_labels.append("forbidden_hidden_private_protected_marker")

    future_ingestion_boundary = data.get("future_ingestion_boundary")
    if isinstance(future_ingestion_boundary, Mapping) and future_ingestion_boundary.get("authorized") is True:
        blocked_labels.append("unsafe_future_ingestion_authorization")

    blocked = bool(blocked_labels)
    posture = "valid" if not blocked else ("blocked" if any(label.startswith("unsafe_") or label.startswith("missing_") or label.startswith("invalid_") or label.startswith("unknown_") or label.startswith("non_json_safe") for label in blocked_labels) else "needs_repair")
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "axis_set_id": _compact_text(data.get("axis_set_id")) or None,
        "axis_count": len(axes),
        "failure_mode_count": len(_unique_values(failure_modes)),
        "valid": not blocked,
        "blocked": blocked,
        "validation_posture": posture,
        "blocked_labels": _unique_values(blocked_labels),
        "summary_text": "Valid theoretical calibration axes set." if not blocked else "Blocked theoretical calibration axes set.",
    }


def summarize_theoretical_calibration_axes_set_v1(packet: Any) -> dict[str, Any]:
    data = packet if isinstance(packet, Mapping) else {}
    axes = data.get("axes", []) if isinstance(data, Mapping) else []
    validation = validate_theoretical_calibration_axes_set_v1(data)
    next_steps = [
        _compact_text(axis.get("next_step_effect"))
        for axis in axes
        if isinstance(axis, Mapping) and _compact_text(axis.get("next_step_effect"))
    ]
    prevention_themes = []
    combined_stack_effect = data.get("combined_stack_effect", {}) if isinstance(data, Mapping) else {}
    if isinstance(combined_stack_effect, Mapping):
        prevention_themes = list(combined_stack_effect.get("prevention_themes", []))
    return {
        "axis_count": len(axes) if isinstance(axes, list) else 0,
        "failure_mode_count": len({
            _compact_text(axis.get("calibrated_failure_mode"))
            for axis in axes
            if isinstance(axis, Mapping) and _compact_text(axis.get("calibrated_failure_mode"))
        }),
        "next_step_labels_used": _unique_values(next_steps),
        "authority_status": _json_safe(data.get("authority_status", _default_authority_status())),
        "validation_posture": validation.get("validation_posture", "unknown"),
        "combined_stack_prevention_themes": prevention_themes or list(_AXIS_SET_PREVENTION_THEMES_V1),
    }


def to_theoretical_calibration_axes_json_safe_v1(packet: Any) -> Any:
    return _json_safe(packet)


__all__ = [
    "AXIS_SET_ID_V1",
    "SCHEMA_VERSION_V1",
    "allowed_theoretical_calibration_failure_modes_v1",
    "allowed_theoretical_calibration_next_steps_v1",
    "build_initial_theoretical_calibration_axes_examples_v1",
    "build_theoretical_calibration_axes_set_v1",
    "build_theoretical_calibration_axis_v1",
    "summarize_theoretical_calibration_axes_set_v1",
    "to_theoretical_calibration_axes_json_safe_v1",
    "validate_theoretical_calibration_axes_set_v1",
    "validate_theoretical_calibration_axis_v1",
]
