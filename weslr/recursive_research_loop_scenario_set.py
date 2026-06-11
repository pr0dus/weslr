"""WESLR Recursive Research Loop Scenario Set V1.

Deterministic, in-memory scenario coverage for the existing minimal recursive
research loop dry-run executor. This is metadata-only: no provider calls, no
retrieval, no persistence, no runtime wiring, and no public claims.
"""

from __future__ import annotations

from collections import Counter
from copy import deepcopy
from hashlib import sha256
from typing import Any, Mapping

import weslr.cognitive_research_protocol as protocol
from weslr.minimal_recursive_research_loop_dry_run_executor import (
    ALLOWED_NEXT_INTERNAL_STEPS_V1,
    build_minimal_loop_input_signal_v1,
    run_minimal_recursive_research_loop_dry_run_v1,
    summarize_minimal_recursive_research_loop_result_v1,
    to_minimal_recursive_research_loop_json_safe_v1,
    validate_minimal_recursive_research_loop_result_v1,
)

SCHEMA_VERSION_V1 = "recursive_research_loop_scenario_set_v1"
SCENARIO_SET_ID_V1 = "recursive_research_loop_scenario_set_v1"
SCENARIO_SET_TITLE_V1 = "WESLR Recursive Research Loop Scenario Set V1"

_SCENARIO_FAMILIES_V1 = (
    "ambiguous_pattern_signal",
    "contradictory_signal",
    "weak_signal_noise",
    "cross_domain_resonance_signal",
    "pressure_test_candidate",
    "calibration_needed_signal",
    "blocked_public_claim_signal",
    "archive_low_value_signal",
)

_EXPECTED_STAGE_PATH_V1 = (
    "raw_signal_cartography",
    "unintelligible_output_analysis",
    "unknown_engine_run",
    "nonlinear_inspiration_run",
    "rule_pressure_run",
    "dialectic_generator_run",
    "perspicuity_score_run",
    "suggestion_store_update_packet",
    "calibration_bridge_record",
)

_SAFETY_FIELDS_V1 = (
    "runtime_action_authorized",
    "storage_write_authorized",
    "memory_mutation_authorized",
    "project_mutation_authorized",
    "behavior_promotion_authorized",
    "public_claim_authorized",
)

_FORBIDDEN_TEXT_MARKERS_V1 = (
    "hidden prompt",
    "system prompt",
    "private text",
    "secret",
    "api key",
    "provider call",
    "tool execution",
    "retrieval",
    "live ingestion",
    ".weslr",
    "final answer authority",
    "final-answer",
    "final answer",
    "public discovery",
    "public breakthrough",
    "agi",
    "sentience",
    "consciousness",
    "proof",
    "official intelligence",
)

_SCENARIO_BLUEPRINTS_V1 = (
    {
        "scenario_family": "ambiguous_pattern_signal",
        "scenario_title": "Ambiguous pattern signal",
        "signal_summary": "Metadata-only signal with repeating motifs, slight boundary drift, and a cautious probe cue.",
        "risk_focus": "pattern ambiguity",
        "uncertainty_focus": "boundary clarity",
        "invalidation_focus": "does the pattern survive normalization",
        "expected_next_step_family": "probe",
    },
    {
        "scenario_family": "contradictory_signal",
        "scenario_title": "Contradictory signal",
        "signal_summary": "Metadata-only signal that points in two directions at once and needs operator reconciliation.",
        "risk_focus": "self-contradiction",
        "uncertainty_focus": "which reading is stable",
        "invalidation_focus": "can both readings remain consistent",
        "expected_next_step_family": "operator_review",
    },
    {
        "scenario_family": "weak_signal_noise",
        "scenario_title": "Weak signal noise",
        "signal_summary": "Sparse metadata-only signal with low density, short hints, and little actionable structure.",
        "risk_focus": "low signal density",
        "uncertainty_focus": "whether any structure is real",
        "invalidation_focus": "does the structure disappear under compression",
        "expected_next_step_family": "archive",
    },
    {
        "scenario_family": "cross_domain_resonance_signal",
        "scenario_title": "Cross-domain resonance signal",
        "signal_summary": "Metadata-only signal that may carry a bounded bridge across domains without claiming truth.",
        "risk_focus": "analogy drift",
        "uncertainty_focus": "transfer boundaries",
        "invalidation_focus": "does the bridge still hold when simplified",
        "expected_next_step_family": "calibrate",
    },
    {
        "scenario_family": "pressure_test_candidate",
        "scenario_title": "Pressure-test candidate",
        "signal_summary": "Metadata-only candidate designed to invite a counterexample and a pressure-based refinement.",
        "risk_focus": "counterexample pressure",
        "uncertainty_focus": "candidate stability",
        "invalidation_focus": "can the candidate survive a small adversarial probe",
        "expected_next_step_family": "pressure_test",
    },
    {
        "scenario_family": "calibration_needed_signal",
        "scenario_title": "Calibration-needed signal",
        "signal_summary": "Metadata-only signal with confidence drift that should stay inside bounded calibration review.",
        "risk_focus": "confidence drift",
        "uncertainty_focus": "what still needs calibration",
        "invalidation_focus": "does calibration reduce uncertainty without overclaiming",
        "expected_next_step_family": "calibrate",
    },
    {
        "scenario_family": "blocked_public_claim_signal",
        "scenario_title": "Blocked public-claim signal",
        "signal_summary": "Metadata-only signal that keeps public-export pressure blocked and remains internal only.",
        "risk_focus": "public-export escalation",
        "uncertainty_focus": "how to keep the signal internal",
        "invalidation_focus": "does the blocked public path stay blocked under review",
        "expected_next_step_family": "operator_review",
    },
    {
        "scenario_family": "archive_low_value_signal",
        "scenario_title": "Archive low-value signal",
        "signal_summary": "Metadata-only signal with low value, limited future leverage, and a likely archive path.",
        "risk_focus": "low future value",
        "uncertainty_focus": "whether the signal merits retention",
        "invalidation_focus": "does a later pass find a better use",
        "expected_next_step_family": "archive",
    },
)


def _merge_payload(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    if isinstance(payload, Mapping):
        merged.update(payload)
    merged.update({k: v for k, v in overrides.items() if v is not None})
    return merged


def _compact_text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _stable_digest(payload: Any) -> str:
    return sha256(repr(payload).encode("utf-8")).hexdigest()


def _json_safe(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_safe(item) for item in value]
    if isinstance(value, tuple):
        return [_json_safe(item) for item in value]
    if isinstance(value, set):
        return [_json_safe(item) for item in sorted(value, key=repr)]
    if isinstance(value, str):
        lowered = value.lower()
        if any(marker in lowered for marker in _FORBIDDEN_TEXT_MARKERS_V1):
            return "[redacted]"
    return deepcopy(value)


def _contains_forbidden_text(value: Any) -> bool:
    if isinstance(value, Mapping):
        return any(_contains_forbidden_text(item) for item in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(_contains_forbidden_text(item) for item in value)
    if not isinstance(value, str):
        return False
    lowered = value.lower()
    return any(marker in lowered for marker in _FORBIDDEN_TEXT_MARKERS_V1)


def _authority_grants_from_mapping(value: Any) -> list[str]:
    if not isinstance(value, Mapping):
        return []
    granted: list[str] = []
    for key, item in value.items():
        key_text = _compact_text(key).lower()
        if "authority" not in key_text:
            continue
        if bool(item):
            granted.append(key_text or "unknown_authority")
    return granted


def _default_denied_authority() -> dict[str, Any]:
    denied = protocol.build_default_cognitive_research_denied_authority_v1()
    denied = deepcopy(denied) if isinstance(denied, Mapping) else {}
    denied.setdefault("status", "metadata_only")
    denied.setdefault(
        "boundary_notes",
        "scenario set: no runtime, persistence, or public-export authority",
    )
    return denied


def _default_safe_metadata(*, scenario_family: str = "recursive_research_loop_scenario_set") -> dict[str, Any]:
    return {
        "safe": True,
        "metadata_only": True,
        "json_safe": True,
        "non_public": True,
        "no_runtime_wiring": True,
        "no_provider_calls": True,
        "no_tool_execution": True,
        "no_retrieval": True,
        "no_persistence": True,
        "no_memory_mutation": True,
        "no_project_mutation": True,
        "no_behavior_promotion": True,
        "no_public_claim": True,
        "no_final_answer_authority": True,
        "no_live_ingestion": True,
        "no_weslr_io": True,
        "no_weslr_runtime": True,
        "no_hidden_prompt_leak": True,
        "no_secrets": True,
        "scenario_family": scenario_family,
    }


def _scenario_blueprint_for_family(scenario_family: str) -> dict[str, Any]:
    for blueprint in _SCENARIO_BLUEPRINTS_V1:
        if blueprint["scenario_family"] == scenario_family:
            return dict(blueprint)
    raise ValueError(f"unknown scenario family: {scenario_family}")


def build_recursive_research_loop_scenario_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = _merge_payload(payload, **overrides)
    scenario_family = _compact_text(data.get("scenario_family"))
    if scenario_family not in _SCENARIO_FAMILIES_V1:
        scenario_family = "ambiguous_pattern_signal"
    blueprint = _scenario_blueprint_for_family(scenario_family)
    scenario_id = _compact_text(data.get("scenario_id")) or f"scenario:{scenario_family}:v1"
    input_signal = data.get("input_signal")
    if not isinstance(input_signal, Mapping):
        signal_id = _compact_text(data.get("signal_id")) or f"signal:{scenario_family}:v1"
        input_signal = build_minimal_loop_input_signal_v1(
            {
                "signal_id": signal_id,
                "signal_type": _compact_text(data.get("signal_type") or "synthetic_recursive_research_seed"),
                "signal_origin": _compact_text(data.get("signal_origin") or "metadata_only"),
                "signal_summary": _compact_text(data.get("signal_summary") or blueprint["signal_summary"]),
                "source_ref": _compact_text(data.get("source_ref") or f"synthetic:{scenario_family}"),
                "trust_level": _compact_text(data.get("trust_level") or "bounded"),
                "poison_risk": _compact_text(data.get("poison_risk") or "low"),
                "injection_risk": _compact_text(data.get("injection_risk") or "low"),
                "raw_content_included": False,
                "raw_content_ref_only": True,
                "normalization_required": True,
                "public_claim_status": _compact_text(data.get("public_claim_status") or "internal_candidate_only"),
                "public_gap_card_status": _compact_text(data.get("public_gap_card_status") or "public_export_blocked"),
                "safe_metadata": _default_safe_metadata(scenario_family=scenario_family),
                "denied_authority": _default_denied_authority(),
            }
        )
    scenario = {
        "scenario_id": scenario_id,
        "scenario_family": scenario_family,
        "scenario_title": _compact_text(data.get("scenario_title") or blueprint["scenario_title"]),
        "input_signal": _json_safe(input_signal),
        "expected_stage_path": list(_EXPECTED_STAGE_PATH_V1),
        "expected_next_step_family": _compact_text(data.get("expected_next_step_family") or blueprint["expected_next_step_family"]),
        "risk_focus": _compact_text(data.get("risk_focus") or blueprint["risk_focus"]),
        "uncertainty_focus": _compact_text(data.get("uncertainty_focus") or blueprint["uncertainty_focus"]),
        "invalidation_focus": _compact_text(data.get("invalidation_focus") or blueprint["invalidation_focus"]),
        "public_claim_status": _compact_text(data.get("public_claim_status") or input_signal.get("public_claim_status") or "internal_candidate_only"),
        "runtime_action_authorized": False,
        "storage_write_authorized": False,
        "memory_mutation_authorized": False,
        "project_mutation_authorized": False,
        "behavior_promotion_authorized": False,
        "safe_metadata": _json_safe(data.get("safe_metadata") or _default_safe_metadata(scenario_family=scenario_family)),
        "denied_authority": _json_safe(data.get("denied_authority") or _default_denied_authority()),
    }
    return _json_safe(scenario)


def build_recursive_research_loop_scenario_set_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = _merge_payload(payload, **overrides)
    scenarios = data.get("scenarios")
    if not isinstance(scenarios, list):
        scenarios = [build_recursive_research_loop_scenario_v1(blueprint) for blueprint in _SCENARIO_BLUEPRINTS_V1]
    scenario_set = {
        "schema_version": SCHEMA_VERSION_V1,
        "scenario_set_id": _compact_text(data.get("scenario_set_id") or SCENARIO_SET_ID_V1),
        "scenario_set_title": _compact_text(data.get("scenario_set_title") or SCENARIO_SET_TITLE_V1),
        "scenario_count": len(scenarios),
        "scenarios": _json_safe(scenarios),
        "safe_metadata": _json_safe(data.get("safe_metadata") or _default_safe_metadata()),
        "denied_authority": _json_safe(data.get("denied_authority") or _default_denied_authority()),
    }
    return _json_safe(scenario_set)


def validate_recursive_research_loop_scenario_v1(scenario: Any) -> dict[str, Any]:
    raw = scenario if isinstance(scenario, Mapping) else {}
    blocked_labels: list[str] = []

    if not isinstance(scenario, Mapping):
        blocked_labels.append("invalid_scenario_type")
        return {
            "schema_version": SCHEMA_VERSION_V1,
            "valid": False,
            "blocked": True,
            "blocked_labels": blocked_labels,
            "summary_text": "Blocked recursive research loop scenario: invalid scenario type.",
        }

    scenario_id = _compact_text(raw.get("scenario_id"))
    if not scenario_id:
        blocked_labels.append("missing_scenario_id")

    scenario_family = _compact_text(raw.get("scenario_family"))
    if not scenario_family:
        blocked_labels.append("missing_scenario_family")
    elif scenario_family not in _SCENARIO_FAMILIES_V1:
        blocked_labels.append("invalid_scenario_family")

    if not _compact_text(raw.get("scenario_title")):
        blocked_labels.append("missing_scenario_title")

    input_signal = raw.get("input_signal")
    if not isinstance(input_signal, Mapping) or not _compact_text(input_signal.get("signal_id")):
        blocked_labels.append("missing_input_signal")
    elif _contains_forbidden_text(input_signal):
        blocked_labels.append("forbidden_input_signal_text")

    expected_stage_path = raw.get("expected_stage_path")
    if not isinstance(expected_stage_path, (list, tuple)):
        blocked_labels.append("invalid_expected_stage_path")
    elif tuple(expected_stage_path) != _EXPECTED_STAGE_PATH_V1:
        blocked_labels.append("invalid_expected_stage_path")

    expected_next_step_family = _compact_text(raw.get("expected_next_step_family"))
    if expected_next_step_family not in ALLOWED_NEXT_INTERNAL_STEPS_V1:
        blocked_labels.append("invalid_expected_next_step_family")

    for field in ("risk_focus", "uncertainty_focus", "invalidation_focus"):
        if not _compact_text(raw.get(field)):
            blocked_labels.append(f"missing_{field}")

    if _compact_text(raw.get("public_claim_status")) == "public_breakthrough_claim":
        blocked_labels.append("public_breakthrough_claim")
    if _contains_forbidden_text(raw):
        blocked_labels.append("forbidden_scenario_text")

    for field in _SAFETY_FIELDS_V1:
        if bool(raw.get(field)):
            blocked_labels.append(f"unsafe_{field}")

    safe_metadata = raw.get("safe_metadata") if isinstance(raw.get("safe_metadata"), Mapping) else {}
    if not isinstance(safe_metadata, Mapping) or not bool(safe_metadata.get("safe", False)):
        blocked_labels.append("unsafe_safe_metadata")

    denied_authority = raw.get("denied_authority")
    if not isinstance(denied_authority, Mapping):
        blocked_labels.append("missing_denied_authority")
    else:
        if _contains_forbidden_text(denied_authority):
            blocked_labels.append("unsafe_denied_authority")
        if _authority_grants_from_mapping(denied_authority):
            blocked_labels.append("granted_denied_authority")

    valid = not blocked_labels
    summary = _scenario_summary_text(raw)
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "valid": valid,
        "blocked": not valid,
        "blocked_labels": list(dict.fromkeys(blocked_labels)),
        "summary_text": summary,
        "scenario_id": scenario_id,
        "scenario_family": scenario_family,
    }


def _scenario_summary_text(scenario: Mapping[str, Any]) -> str:
    scenario_id = _compact_text(scenario.get("scenario_id"), "scenario:unknown")
    scenario_family = _compact_text(scenario.get("scenario_family"), "unknown")
    title = _compact_text(scenario.get("scenario_title"), "scenario")
    next_step = _compact_text(scenario.get("expected_next_step_family"), "blocked")
    return f"Scenario {scenario_id}: family={scenario_family}; title={title}; expected_next={next_step}."


def _safety_summary_for_result(result: Mapping[str, Any]) -> str:
    flags = ", ".join(f"{field}={bool(result.get(field, False))}" for field in _SAFETY_FIELDS_V1)
    return f"Safety authority flags: {flags}."


def _gap_summary_for_entry(scenario: Mapping[str, Any], result: Mapping[str, Any], validation: Mapping[str, Any]) -> str:
    expected = _compact_text(scenario.get("expected_next_step_family"), "blocked")
    observed = _compact_text(result.get("recommended_next_internal_step"), "blocked")
    if validation.get("valid") is False:
        labels = validation.get("blocked_labels") if isinstance(validation.get("blocked_labels"), list) else []
        first = _compact_text(labels[0]) if labels else "invalid_result"
        return f"gap: validation blocked ({first}); expected={expected}; observed={observed}."
    if expected != observed:
        return f"gap: expected={expected}; observed={observed}; family-specific review may refine the heuristic."
    return f"gap: expected={expected}; observed={observed}; no extra gap surfaced."


def _stage_failure_distribution_from_validations(validations: list[Mapping[str, Any]]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for validation in validations:
        labels = validation.get("blocked_labels") if isinstance(validation.get("blocked_labels"), list) else []
        for label in labels:
            label_text = _compact_text(label)
            if label_text:
                counts[label_text] += 1
    return dict(sorted(counts.items(), key=lambda item: item[0]))


def _normalize_set_input(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = _merge_payload(payload, **overrides)
    scenario_set = data.get("scenario_set")
    if isinstance(scenario_set, Mapping):
        return dict(scenario_set)
    if "scenarios" in data and isinstance(data.get("scenarios"), list):
        return dict(data)
    return build_recursive_research_loop_scenario_set_v1(data)


def run_recursive_research_loop_scenario_set_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    scenario_set = _normalize_set_input(payload, **overrides)
    scenarios = scenario_set.get("scenarios") if isinstance(scenario_set.get("scenarios"), list) else []
    scenario_results: list[dict[str, Any]] = []
    scenario_validations: list[dict[str, Any]] = []
    dry_run_validations: list[dict[str, Any]] = []
    next_step_counts: Counter[str] = Counter()
    safety_flags = {field: False for field in _SAFETY_FIELDS_V1}

    for scenario in scenarios:
        scenario_validation = validate_recursive_research_loop_scenario_v1(scenario)
        scenario_validations.append(scenario_validation)
        if not scenario_validation.get("valid", False):
            dry_run_result = {
                "schema_version": SCHEMA_VERSION_V1,
                "scenario_id": _compact_text(scenario.get("scenario_id")) or "scenario:invalid",
                "recommended_next_internal_step": "blocked",
                "blocked_actions": ["invalid_scenario_input"],
                "operator_review_required": True,
                "runtime_action_authorized": False,
                "storage_write_authorized": False,
                "memory_mutation_authorized": False,
                "project_mutation_authorized": False,
                "behavior_promotion_authorized": False,
                "public_claim_authorized": False,
                "denied_authority": _default_denied_authority(),
                "safe_metadata": _default_safe_metadata(scenario_family=_compact_text(scenario.get("scenario_family"), "recursive_research_loop_scenario_set")),
            }
            dry_run_validation = {
                "schema_version": "minimal_recursive_research_loop_dry_run_executor_v1",
                "valid": False,
                "blocked": True,
                "blocked_labels": ["invalid_scenario_input"],
                "summary_text": "Blocked minimal recursive research loop: invalid scenario input.",
            }
        else:
            dry_run_result = run_minimal_recursive_research_loop_dry_run_v1({"input_signal": scenario["input_signal"]})
            dry_run_validation = validate_minimal_recursive_research_loop_result_v1(dry_run_result)
        dry_run_validations.append(dry_run_validation)
        next_step = _compact_text(dry_run_result.get("recommended_next_internal_step"), "blocked")
        next_step_counts[next_step] += 1
        for field in _SAFETY_FIELDS_V1:
            safety_flags[field] = safety_flags[field] or bool(dry_run_result.get(field, False))
        completion_status = "completed" if dry_run_validation.get("valid") else "blocked"
        scenario_results.append(
            {
                "scenario_id": _compact_text(scenario.get("scenario_id")),
                "scenario_family": _compact_text(scenario.get("scenario_family")),
                "scenario_title": _compact_text(scenario.get("scenario_title")),
                "expected_next_step_family": _compact_text(scenario.get("expected_next_step_family")),
                "completion_status": completion_status,
                "recommended_next_internal_step": next_step,
                "stage_summary": summarize_minimal_recursive_research_loop_result_v1(dry_run_result),
                "safety_summary": _safety_summary_for_result(dry_run_result),
                "gap_summary": _gap_summary_for_entry(scenario, dry_run_result, dry_run_validation),
                "scenario_validation": scenario_validation,
                "dry_run_validation": dry_run_validation,
                "dry_run_result": _json_safe(dry_run_result),
            }
        )

    total_scenarios = len(scenario_results)
    blocked_scenarios = sum(1 for item in scenario_results if item["completion_status"] == "blocked")
    completed_scenarios = total_scenarios - blocked_scenarios
    stage_failure_distribution = _stage_failure_distribution_from_validations(dry_run_validations)
    safety_authority_status = {
        **{field: bool(safety_flags[field]) for field in _SAFETY_FIELDS_V1},
        "all_authority_flags_false": not any(safety_flags.values()),
    }
    ready_for_review = total_scenarios >= 8 and blocked_scenarios == 0 and all(item["completion_status"] == "completed" for item in scenario_results)
    result = {
        "schema_version": SCHEMA_VERSION_V1,
        "scenario_set_id": _compact_text(scenario_set.get("scenario_set_id") or SCENARIO_SET_ID_V1),
        "scenario_set_title": _compact_text(scenario_set.get("scenario_set_title") or SCENARIO_SET_TITLE_V1),
        "scenarios": _json_safe(scenarios),
        "scenario_results": _json_safe(scenario_results),
        "total_scenarios": total_scenarios,
        "completed_scenarios": completed_scenarios,
        "blocked_scenarios": blocked_scenarios,
        "next_step_distribution": dict(sorted(next_step_counts.items(), key=lambda item: item[0])),
        "stage_failure_distribution": stage_failure_distribution,
        "safety_authority_status": safety_authority_status,
        "ready_for_review": ready_for_review,
        "safe_metadata": _json_safe(scenario_set.get("safe_metadata") or _default_safe_metadata()),
        "denied_authority": _json_safe(scenario_set.get("denied_authority") or _default_denied_authority()),
    }
    result["summary_text"] = summarize_recursive_research_loop_scenario_set_v1(result)
    return _json_safe(result)


def validate_recursive_research_loop_scenario_set_result_v1(result: Any) -> dict[str, Any]:
    raw = result if isinstance(result, Mapping) else {}
    blocked_labels: list[str] = []

    if not isinstance(result, Mapping):
        blocked_labels.append("invalid_result_type")
        return {
            "schema_version": SCHEMA_VERSION_V1,
            "valid": False,
            "blocked": True,
            "blocked_labels": blocked_labels,
            "summary_text": "Blocked recursive research loop scenario set: invalid result type.",
        }

    if _compact_text(raw.get("schema_version")) != SCHEMA_VERSION_V1:
        blocked_labels.append("invalid_schema_version")
    if not _compact_text(raw.get("scenario_set_id")):
        blocked_labels.append("missing_scenario_set_id")
    if not _compact_text(raw.get("scenario_set_title")):
        blocked_labels.append("missing_scenario_set_title")

    scenarios = raw.get("scenarios")
    scenario_results = raw.get("scenario_results")
    if not isinstance(scenarios, list):
        blocked_labels.append("missing_scenarios")
    if not isinstance(scenario_results, list):
        blocked_labels.append("missing_scenario_results")

    if not isinstance(raw.get("next_step_distribution"), Mapping):
        blocked_labels.append("missing_next_step_distribution")
    if not isinstance(raw.get("stage_failure_distribution"), Mapping):
        blocked_labels.append("missing_stage_failure_distribution")
    if not isinstance(raw.get("safety_authority_status"), Mapping):
        blocked_labels.append("missing_safety_authority_status")

    if not isinstance(raw.get("total_scenarios"), int):
        blocked_labels.append("invalid_total_scenarios")
    if not isinstance(raw.get("completed_scenarios"), int):
        blocked_labels.append("invalid_completed_scenarios")
    if not isinstance(raw.get("blocked_scenarios"), int):
        blocked_labels.append("invalid_blocked_scenarios")

    if not isinstance(raw.get("ready_for_review"), bool):
        blocked_labels.append("invalid_ready_for_review")

    if not isinstance(raw.get("safe_metadata"), Mapping) or not bool(raw.get("safe_metadata", {}).get("safe", False)):
        blocked_labels.append("unsafe_safe_metadata")
    denied_authority = raw.get("denied_authority")
    if not isinstance(denied_authority, Mapping):
        blocked_labels.append("missing_denied_authority")
    else:
        if _contains_forbidden_text(denied_authority):
            blocked_labels.append("unsafe_denied_authority")
        if _authority_grants_from_mapping(denied_authority):
            blocked_labels.append("granted_denied_authority")

    if _contains_forbidden_text(raw):
        blocked_labels.append("forbidden_result_text")

    scenario_validation_labels: list[str] = []
    dry_run_validation_labels: list[str] = []
    if isinstance(scenarios, list) and isinstance(scenario_results, list):
        if len(scenarios) != len(scenario_results):
            blocked_labels.append("scenario_result_count_mismatch")
        for scenario, scenario_result in zip(scenarios, scenario_results):
            scenario_validation = validate_recursive_research_loop_scenario_v1(scenario)
            dry_run_validation = scenario_result.get("dry_run_validation") if isinstance(scenario_result, Mapping) else None
            dry_run_result = scenario_result.get("dry_run_result") if isinstance(scenario_result, Mapping) else None
            if not scenario_validation.get("valid", False):
                scenario_validation_labels.extend(scenario_validation.get("blocked_labels", []))
            if not isinstance(dry_run_result, Mapping):
                blocked_labels.append("missing_dry_run_result")
            else:
                actual_validation = validate_minimal_recursive_research_loop_result_v1(dry_run_result)
                if not actual_validation.get("valid", False):
                    dry_run_validation_labels.extend(actual_validation.get("blocked_labels", []))
                if _authority_grants_from_mapping(dry_run_result.get("denied_authority")):
                    blocked_labels.append("granted_denied_authority")
            if not isinstance(dry_run_validation, Mapping):
                blocked_labels.append("missing_dry_run_validation")
            elif not dry_run_validation.get("valid", False):
                dry_run_validation_labels.extend(dry_run_validation.get("blocked_labels", []))
            if isinstance(scenario_result, Mapping):
                if _compact_text(scenario_result.get("completion_status")) not in {"completed", "blocked"}:
                    blocked_labels.append("invalid_completion_status")
                if not _compact_text(scenario_result.get("recommended_next_internal_step")):
                    blocked_labels.append("missing_recommended_next_internal_step")
                if not _compact_text(scenario_result.get("stage_summary")):
                    blocked_labels.append("missing_stage_summary")
                if not _compact_text(scenario_result.get("safety_summary")):
                    blocked_labels.append("missing_safety_summary")
                if not _compact_text(scenario_result.get("gap_summary")):
                    blocked_labels.append("missing_gap_summary")

    blocked_labels.extend(scenario_validation_labels)
    blocked_labels.extend(dry_run_validation_labels)

    total_scenarios = raw.get("total_scenarios") if isinstance(raw.get("total_scenarios"), int) else 0
    completed_scenarios = raw.get("completed_scenarios") if isinstance(raw.get("completed_scenarios"), int) else 0
    blocked_scenarios = raw.get("blocked_scenarios") if isinstance(raw.get("blocked_scenarios"), int) else 0
    if total_scenarios and completed_scenarios + blocked_scenarios != total_scenarios:
        blocked_labels.append("scenario_count_mismatch")

    valid = not blocked_labels
    summary = summarize_recursive_research_loop_scenario_set_v1(raw)
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "valid": valid,
        "blocked": not valid,
        "blocked_labels": list(dict.fromkeys(blocked_labels)),
        "summary_text": summary,
        "scenario_set_id": _compact_text(raw.get("scenario_set_id")),
        "ready_for_review": bool(raw.get("ready_for_review")),
    }


def summarize_recursive_research_loop_scenario_set_v1(result: Any) -> str:
    raw = result if isinstance(result, Mapping) else {}
    scenario_set_id = _compact_text(raw.get("scenario_set_id"), SCENARIO_SET_ID_V1)
    total = raw.get("total_scenarios") if isinstance(raw.get("total_scenarios"), int) else 0
    completed = raw.get("completed_scenarios") if isinstance(raw.get("completed_scenarios"), int) else 0
    blocked = raw.get("blocked_scenarios") if isinstance(raw.get("blocked_scenarios"), int) else 0
    next_steps = raw.get("next_step_distribution") if isinstance(raw.get("next_step_distribution"), Mapping) else {}
    stage_failures = raw.get("stage_failure_distribution") if isinstance(raw.get("stage_failure_distribution"), Mapping) else {}
    safety = raw.get("safety_authority_status") if isinstance(raw.get("safety_authority_status"), Mapping) else {}
    next_bits = ", ".join(f"{key}:{value}" for key, value in sorted(next_steps.items(), key=lambda item: item[0])) or "none"
    stage_bits = ", ".join(f"{key}:{value}" for key, value in sorted(stage_failures.items(), key=lambda item: item[0])) or "none"
    safety_bits = ", ".join(f"{key}={value}" for key, value in sorted(safety.items(), key=lambda item: item[0])) or "unknown"
    ready = bool(raw.get("ready_for_review"))
    return (
        f"Scenario set {scenario_set_id}: total={total}; completed={completed}; blocked={blocked}; "
        f"next_step_distribution={next_bits}; stage_failure_distribution={stage_bits}; safety_authority_status={safety_bits}; "
        f"ready_for_review={ready}."
    )


def to_recursive_research_loop_scenario_set_json_safe_v1(result: Any) -> dict[str, Any]:
    return _json_safe(result if isinstance(result, Mapping) else {})


def _build_default_scenario_set() -> dict[str, Any]:
    return build_recursive_research_loop_scenario_set_v1()


__all__ = (
    "SCHEMA_VERSION_V1",
    "build_recursive_research_loop_scenario_v1",
    "build_recursive_research_loop_scenario_set_v1",
    "run_recursive_research_loop_scenario_set_v1",
    "summarize_recursive_research_loop_scenario_set_v1",
    "to_recursive_research_loop_scenario_set_json_safe_v1",
    "validate_recursive_research_loop_scenario_set_result_v1",
    "validate_recursive_research_loop_scenario_v1",
)
