"""WESLR Known-Science Replay Selector Calibration Bridge V1.

Deterministic, metadata-only helper for comparing known-science replay expected
internal next steps against scenario-sensitive selector outputs.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

from weslr import known_science_replay_helpers as ksr

SCHEMA_VERSION_V1 = "known_science_replay_selector_calibration_bridge_v1"
BRIDGE_ID_V1 = "known_science_replay_selector_calibration_bridge_v1"

ALLOWED_ALIGNMENT_STATUSES_V1 = (
    "aligned",
    "partially_aligned",
    "mismatch",
    "blocked_by_safety",
    "not_applicable",
    "needs_repair",
)
ALLOWED_MISMATCH_TYPES_V1 = (
    "none",
    "over_cautious",
    "under_cautious",
    "premature_calibration",
    "premature_archive",
    "missed_pressure_test",
    "missed_probe",
    "unsafe_public_claim_pressure",
    "invalid_metadata",
    "unknown_case",
)
ALLOWED_SELECTOR_OUTCOMES_V1 = (
    "probe",
    "pressure_test",
    "calibrate",
    "operator_review",
    "archive",
    "watch",
    "blocked",
    "needs_repair",
    "unknown",
)
FORBIDDEN_CLAIM_MARKERS_V1 = (
    "discovery",
    "discovered",
    "proof",
    "breakthrough",
    "scientific result",
    "benchmark",
    "certification",
    "score",
    "agi",
    "intelligence",
    "sentience",
    "consciousness",
    "public science",
    "final answer",
    "official intelligence",
)
FORBIDDEN_PRIVATE_MARKERS_V1 = (
    "hidden prompt",
    "system prompt",
    "private text",
    "secret",
    "api key",
    ".weslr",
    "protected",
    "private",
)
FORBIDDEN_RUNTIME_MARKERS_V1 = (
    "runtime",
    "executor",
    "runner",
    "provider call",
    "tool execution",
    "web call",
    "retrieval call",
    "persistence",
    "database write",
)
REQUIRED_SAFE_METADATA_FLAGS_V1 = (
    "safe",
    "metadata_only",
    "json_safe",
    "non_public",
    "no_runtime_wiring",
    "no_provider_calls",
    "no_tool_execution",
    "no_retrieval",
    "no_persistence",
    "no_memory_mutation",
    "no_project_mutation",
    "no_behavior_promotion",
    "no_public_claim",
    "no_final_answer_authority",
    "no_live_ingestion",
    "no_weslr_io",
    "no_weslr_runtime",
    "no_hidden_prompt_leak",
    "no_secrets",
    "bridge_family_safe",
)

_KNOWN_REPLAY_CASES_V1 = tuple(ksr.build_initial_known_science_replay_examples_v1())
_KNOWN_REPLAY_CASE_IDS_V1 = {case["case_id"] for case in _KNOWN_REPLAY_CASES_V1 if isinstance(case, Mapping)}
_KNOWN_REPLAY_PHASE_IDS_V1 = {
    phase["phase_id"]
    for case in _KNOWN_REPLAY_CASES_V1
    if isinstance(case, Mapping)
    for phase in case.get("replay_phases", [])
    if isinstance(phase, Mapping)
}


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


def _expected_steps(value: Any) -> list[str]:
    if isinstance(value, (list, tuple, set)):
        return [_compact_text(item) for item in value if _compact_text(item)]
    step = _compact_text(value)
    return [step] if step else []


def _expected_steps_text(value: Any) -> str:
    steps = _expected_steps(value)
    return ", ".join(steps) if len(steps) > 1 else (steps[0] if steps else "unknown")


def _default_authority_status() -> dict[str, Any]:
    return {
        "runtime_action_authorized": False,
        "storage_write_authorized": False,
        "memory_mutation_authorized": False,
        "project_mutation_authorized": False,
        "behavior_promotion_authorized": False,
        "public_claim_authorized": False,
        "final_answer_authority": False,
        "provider_model_call_authority": False,
        "tool_execution_authority": False,
        "web_authority": False,
        "retrieval_tool_authority": False,
        "all_authority_flags_false": True,
        "status": "metadata_only",
    }


def _default_safe_metadata() -> dict[str, Any]:
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
        "bridge_family_safe": True,
    }


def _normalize_authority_status(value: Any) -> dict[str, Any]:
    normalized = _default_authority_status()
    if isinstance(value, Mapping):
        normalized.update({key: _json_safe(item) for key, item in value.items()})
    return normalized


def _normalize_safe_metadata(value: Any) -> dict[str, Any]:
    normalized = _default_safe_metadata()
    if isinstance(value, Mapping):
        normalized.update({key: _json_safe(item) for key, item in value.items()})
    return normalized


def _normalize_selector_input_metadata(value: Any, fallback: Mapping[str, Any] | None = None) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return _json_safe(value)
    if value is None and isinstance(fallback, Mapping):
        return _json_safe(fallback)
    if value is None:
        return {}
    return {"value": _json_safe(value)}


def _default_bridge_id(case_id: str, phase_id: str) -> str:
    if case_id and phase_id:
        return f"{case_id}:{phase_id}:{SCHEMA_VERSION_V1}"
    if case_id:
        return f"{case_id}:{SCHEMA_VERSION_V1}"
    if phase_id:
        return f"{phase_id}:{SCHEMA_VERSION_V1}"
    return BRIDGE_ID_V1


def _is_unsafe_public_claim_pressure(data: Mapping[str, Any], expected_steps: list[str]) -> bool:
    phase_id = _compact_text(data.get("replay_phase_id")).lower()
    selection_reason = _compact_text(data.get("selector_selection_reason")).lower()
    selector_input_metadata = data.get("selector_input_metadata")
    source_summary = _compact_text(data.get("replay_phase_summary")).lower()
    selector_text = " ".join(
        [phase_id, selection_reason, source_summary, _compact_text(selector_input_metadata).lower()]
    )
    if "unsafe_public_claim" in phase_id or "public claim" in selector_text:
        return True
    return any(step in {"operator_review", "blocked"} for step in expected_steps)


def build_known_science_replay_selector_bridge_input_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = _merge_payload(payload, **overrides)
    replay_case = data.get("replay_case") if isinstance(data.get("replay_case"), Mapping) else {}
    replay_phase = data.get("replay_phase") if isinstance(data.get("replay_phase"), Mapping) else {}

    case_id = _compact_text(data.get("source_replay_case_id") or replay_case.get("case_id") or replay_phase.get("case_id"), "")
    phase_id = _compact_text(data.get("replay_phase_id") or replay_phase.get("phase_id") or replay_phase.get("phase_name"), "")
    expected_value = None
    if "expected_internal_next_step" in data:
        expected_value = data.get("expected_internal_next_step")
    elif "expected_internal_next_steps" in data:
        expected_value = data.get("expected_internal_next_steps")
    elif isinstance(replay_phase, Mapping):
        expected_value = replay_phase.get("expected_internal_next_step")

    expected_steps = _expected_steps(expected_value)

    if not expected_steps and isinstance(replay_phase, Mapping):
        expected_steps = _expected_steps(replay_phase.get("expected_selector_outcome"))

    source_known_outcome = _compact_text(
        data.get("source_known_outcome")
        or replay_case.get("known_outcome")
        or replay_phase.get("known_outcome_reference"),
        "",
    )
    source_case_domain = _compact_text(
        data.get("source_case_domain") or replay_case.get("domain") or replay_phase.get("domain"),
        "",
    )
    replay_phase_summary = _compact_text(
        data.get("replay_phase_summary")
        or replay_phase.get("historical_signal_summary")
        or replay_phase.get("safe_interpretation"),
        "",
    )
    bridge_id = _compact_text(data.get("bridge_id"), _default_bridge_id(case_id, phase_id))

    packet = {
        "schema_version": SCHEMA_VERSION_V1,
        "bridge_id": bridge_id,
        "source_replay_case_id": case_id,
        "source_known_outcome": source_known_outcome,
        "source_case_domain": source_case_domain,
        "replay_phase_id": phase_id,
        "replay_phase_summary": replay_phase_summary,
        "expected_internal_next_step": expected_steps if len(expected_steps) != 1 else expected_steps[0],
        "selector_input_metadata": _normalize_selector_input_metadata(
            data.get("selector_input_metadata"),
            fallback={
                "bridge_family": "known_science_replay_selector_calibration",
                "source_replay_case_id": case_id,
                "replay_phase_id": phase_id,
                "source_case_domain": source_case_domain,
                "source_known_outcome": source_known_outcome,
            },
        ),
        "selector_selected_next_step": _compact_text(data.get("selector_selected_next_step")),
        "selector_selection_reason": _compact_text(data.get("selector_selection_reason")),
        "forbidden_interpretations": _json_safe(
            data.get("forbidden_interpretations")
            if isinstance(data.get("forbidden_interpretations"), (list, tuple, set))
            else replay_phase.get("forbidden_interpretations")
            if isinstance(replay_phase, Mapping)
            else []
        ),
        "authority_status": _normalize_authority_status(data.get("authority_status")),
        "safe_metadata": _normalize_safe_metadata(data.get("safe_metadata")),
    }
    return packet


def compare_known_science_replay_selector_step_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = build_known_science_replay_selector_bridge_input_v1(payload, **overrides)
    expected_steps = _expected_steps(data.get("expected_internal_next_step"))
    selected = _compact_text(data.get("selector_selected_next_step"))
    case_id = _compact_text(data.get("source_replay_case_id"))
    phase_id = _compact_text(data.get("replay_phase_id"))

    if not case_id or not phase_id or not expected_steps or not selected:
        return {
            "alignment_status": "needs_repair",
            "mismatch_type": "invalid_metadata",
            "alignment_notes": ["missing bridge, replay, expected, or selected metadata"],
            "calibration_observation": "metadata repair is required before comparison can be trusted",
            "recommended_followup": "repair the missing bridge metadata and rebuild the packet",
        }

    if case_id not in _KNOWN_REPLAY_CASE_IDS_V1 or phase_id not in _KNOWN_REPLAY_PHASE_IDS_V1:
        return {
            "alignment_status": "not_applicable",
            "mismatch_type": "unknown_case",
            "alignment_notes": ["unknown replay case or phase"],
            "calibration_observation": "comparison is not applicable until the case or phase is recognized",
            "recommended_followup": "repair the replay case or phase identifiers",
        }

    if selected not in ALLOWED_SELECTOR_OUTCOMES_V1:
        return {
            "alignment_status": "needs_repair",
            "mismatch_type": "invalid_metadata",
            "alignment_notes": ["selected step is not an allowed selector outcome"],
            "calibration_observation": "selected step must use a known internal outcome label",
            "recommended_followup": "repair the selected next-step label",
        }

    if _is_unsafe_public_claim_pressure(data, expected_steps) and selected in {"blocked", "operator_review"}:
        return {
            "alignment_status": "blocked_by_safety",
            "mismatch_type": "none",
            "alignment_notes": ["selector correctly blocked unsafe public-claim pressure"],
            "calibration_observation": "safety pressure was handled correctly without promoting public claims",
            "recommended_followup": "hold the boundary and continue with safe internal review only",
        }

    expected_set = set(expected_steps)
    if selected in expected_set:
        return {
            "alignment_status": "aligned",
            "mismatch_type": "none",
            "alignment_notes": ["selector choice matches the expected replay step"],
            "calibration_observation": "selector output matches the expected internal next step",
            "recommended_followup": "continue with the next safe internal replay phase",
        }

    if "probe" in expected_set and selected == "calibrate":
        return {
            "alignment_status": "mismatch",
            "mismatch_type": "premature_calibration",
            "alignment_notes": ["selector calibrated before the signal warranted it"],
            "calibration_observation": "the selector advanced too quickly from uncertainty to calibration",
            "recommended_followup": "stay in probe mode until repeatability or pressure evidence improves",
        }

    if "probe" in expected_set and selected == "archive":
        return {
            "alignment_status": "mismatch",
            "mismatch_type": "premature_archive",
            "alignment_notes": ["selector archived before the signal was ready"],
            "calibration_observation": "the selector closed the case too early",
            "recommended_followup": "keep the case open and continue cautious probing",
        }

    if "pressure_test" in expected_set and selected not in {"pressure_test", "blocked", "operator_review"}:
        return {
            "alignment_status": "mismatch",
            "mismatch_type": "missed_pressure_test",
            "alignment_notes": ["selector did not pressure-test an ordinary explanation"],
            "calibration_observation": "ordinary explanations were not challenged strongly enough",
            "recommended_followup": "re-run with a pressure-test focused internal step",
        }

    if "calibrate" in expected_set and selected == "watch":
        return {
            "alignment_status": "partially_aligned",
            "mismatch_type": "over_cautious",
            "alignment_notes": ["selector stayed conservative when calibration was expected"],
            "calibration_observation": "the selector was directionally safe but slower than necessary",
            "recommended_followup": "advance from watch to calibration metadata review",
        }

    if "calibrate" in expected_set and selected == "probe":
        return {
            "alignment_status": "mismatch",
            "mismatch_type": "over_cautious",
            "alignment_notes": ["selector held back from the expected calibration step"],
            "calibration_observation": "the selector stayed too early in the exploration phase",
            "recommended_followup": "move from probe to calibration once the signal is repeatable",
        }

    if selected in {"blocked", "operator_review"}:
        return {
            "alignment_status": "mismatch",
            "mismatch_type": "over_cautious",
            "alignment_notes": ["selector blocked or escalated more than the replay expected"],
            "calibration_observation": "the selector may have slowed progress too much",
            "recommended_followup": "check whether the case actually needs a blocked-state boundary",
        }

    if selected == "unknown" or "unknown" in expected_set:
        return {
            "alignment_status": "not_applicable",
            "mismatch_type": "unknown_case",
            "alignment_notes": ["unknown selector outcome or unknown replay expectation"],
            "calibration_observation": "the comparison does not have a stable internal label yet",
            "recommended_followup": "repair the replay case taxonomy before comparing again",
        }

    return {
        "alignment_status": "mismatch",
        "mismatch_type": "unknown_case",
        "alignment_notes": ["selector output does not match the expected replay step family"],
        "calibration_observation": "the comparison does not map cleanly to a named calibration mismatch",
        "recommended_followup": "repair the replay taxonomy or clarify the expected next step",
    }


def build_known_science_replay_selector_bridge_packet_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = build_known_science_replay_selector_bridge_input_v1(payload, **overrides)
    comparison = compare_known_science_replay_selector_step_v1(data)
    packet = {
        **data,
        **comparison,
    }
    packet["schema_version"] = SCHEMA_VERSION_V1
    return packet


def _validate_authority_status(authority_status: Any, blocked_labels: list[str]) -> None:
    if not isinstance(authority_status, Mapping):
        blocked_labels.append("missing_authority_status")
        return

    required_false_flags = (
        "runtime_action_authorized",
        "storage_write_authorized",
        "memory_mutation_authorized",
        "project_mutation_authorized",
        "behavior_promotion_authorized",
        "public_claim_authorized",
        "final_answer_authority",
        "provider_model_call_authority",
        "tool_execution_authority",
        "web_authority",
        "retrieval_tool_authority",
    )
    for flag in required_false_flags:
        if authority_status.get(flag) is True:
            blocked_labels.append(f"unsafe_{flag}")
    if authority_status.get("all_authority_flags_false") is not True:
        blocked_labels.append("unsafe_authority_flags_present")



def _validate_safe_metadata(safe_metadata: Any, blocked_labels: list[str]) -> None:
    if not isinstance(safe_metadata, Mapping):
        blocked_labels.append("missing_safe_metadata")
        return
    for flag in REQUIRED_SAFE_METADATA_FLAGS_V1:
        if safe_metadata.get(flag) is not True:
            blocked_labels.append(f"unsafe_safe_metadata_{flag}")



def _validate_expected_steps(value: Any, blocked_labels: list[str]) -> None:
    steps = _expected_steps(value)
    if not steps:
        blocked_labels.append("missing_expected_internal_next_step")
        return
    for step in steps:
        if step not in ALLOWED_SELECTOR_OUTCOMES_V1:
            blocked_labels.append("invalid_expected_internal_next_step")
            return



def validate_known_science_replay_selector_bridge_packet_v1(packet: Any) -> dict[str, Any]:
    raw = packet if isinstance(packet, Mapping) else {}
    blocked_labels: list[str] = []

    if not isinstance(packet, Mapping):
        blocked_labels.append("invalid_bridge_packet_type")
        return {
            "schema_version": SCHEMA_VERSION_V1,
            "valid": False,
            "blocked": True,
            "blocked_labels": blocked_labels,
            "summary_text": "Blocked known-science replay selector bridge packet: invalid packet type.",
        }

    if _compact_text(raw.get("schema_version")) != SCHEMA_VERSION_V1:
        blocked_labels.append("invalid_schema_version")
    if not _compact_text(raw.get("bridge_id")):
        blocked_labels.append("missing_bridge_id")
    if not _compact_text(raw.get("source_replay_case_id")):
        blocked_labels.append("missing_replay_case_id")
    if not _compact_text(raw.get("source_known_outcome")):
        blocked_labels.append("missing_source_known_outcome")
    if not _compact_text(raw.get("source_case_domain")):
        blocked_labels.append("missing_source_case_domain")
    if not _compact_text(raw.get("replay_phase_id")):
        blocked_labels.append("missing_replay_phase_id")
    if not _compact_text(raw.get("replay_phase_summary")):
        blocked_labels.append("missing_replay_phase_summary")

    _validate_expected_steps(raw.get("expected_internal_next_step"), blocked_labels)

    if not isinstance(raw.get("selector_input_metadata"), Mapping):
        blocked_labels.append("missing_selector_input_metadata")
    if not _compact_text(raw.get("selector_selected_next_step")):
        blocked_labels.append("missing_selector_selected_next_step")
    elif _compact_text(raw.get("selector_selected_next_step")) not in ALLOWED_SELECTOR_OUTCOMES_V1:
        blocked_labels.append("invalid_selector_selected_next_step")
    if not _compact_text(raw.get("selector_selection_reason")):
        blocked_labels.append("missing_selector_selection_reason")
    if not isinstance(raw.get("alignment_notes"), list) or not raw.get("alignment_notes"):
        blocked_labels.append("missing_alignment_notes")
    if _compact_text(raw.get("alignment_status")) not in ALLOWED_ALIGNMENT_STATUSES_V1:
        blocked_labels.append("invalid_alignment_status")
    if _compact_text(raw.get("mismatch_type")) not in ALLOWED_MISMATCH_TYPES_V1:
        blocked_labels.append("invalid_mismatch_type")
    if not _compact_text(raw.get("calibration_observation")):
        blocked_labels.append("missing_calibration_observation")
    if not _compact_text(raw.get("recommended_followup")):
        blocked_labels.append("missing_recommended_followup")
    if not isinstance(raw.get("forbidden_interpretations"), list) or not raw.get("forbidden_interpretations"):
        blocked_labels.append("missing_forbidden_interpretations")
    _validate_authority_status(raw.get("authority_status"), blocked_labels)
    _validate_safe_metadata(raw.get("safe_metadata"), blocked_labels)

    claim_language_fields = (
        raw.get("selector_selection_reason"),
        raw.get("alignment_notes"),
        raw.get("calibration_observation"),
        raw.get("recommended_followup"),
    )
    if _contains_markers(raw, FORBIDDEN_PRIVATE_MARKERS_V1):
        blocked_labels.append("forbidden_private_text")
    if _contains_markers(raw, FORBIDDEN_RUNTIME_MARKERS_V1):
        blocked_labels.append("forbidden_runtime_or_tool_language")
    if any(_contains_markers(value, FORBIDDEN_CLAIM_MARKERS_V1) for value in claim_language_fields):
        blocked_labels.append("forbidden_claim_language")

    non_json_safe_path = _first_non_json_safe_path(raw)
    if non_json_safe_path is not None:
        blocked_labels.append("non_json_safe_result_structure")

    valid = not blocked_labels
    summary_text = (
        f"Blocked known-science replay selector bridge packet { _compact_text(raw.get('bridge_id'), 'unknown_bridge') }"
        if not valid
        else f"Known-science replay selector bridge packet {_compact_text(raw.get('bridge_id'), 'unknown_bridge')} is valid."
    )
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "valid": valid,
        "blocked": not valid,
        "blocked_labels": blocked_labels,
        "summary_text": summary_text,
    }


def summarize_known_science_replay_selector_bridge_packet_v1(packet: Any) -> dict[str, Any]:
    raw = packet if isinstance(packet, Mapping) else {}
    expected = _expected_steps_text(raw.get("expected_internal_next_step"))
    selected = _compact_text(raw.get("selector_selected_next_step"), "unknown")
    return {
        "summary_type": SCHEMA_VERSION_V1,
        "bridge_id": _compact_text(raw.get("bridge_id"), "unknown_bridge"),
        "source_replay_case_id": _compact_text(raw.get("source_replay_case_id"), "unknown_case"),
        "replay_phase_id": _compact_text(raw.get("replay_phase_id"), "unknown_phase"),
        "alignment_status": _compact_text(raw.get("alignment_status"), "unknown"),
        "mismatch_type": _compact_text(raw.get("mismatch_type"), "unknown_case"),
        "expected_internal_next_step": expected,
        "selector_selected_next_step": selected,
        "summary_text": (
            f"Known-science replay selector bridge {_compact_text(raw.get('bridge_id'), 'unknown_bridge')}: "
            f"case={_compact_text(raw.get('source_replay_case_id'), 'unknown_case')}; "
            f"phase={_compact_text(raw.get('replay_phase_id'), 'unknown_phase')}; "
            f"expected={expected}; selected={selected}; "
            f"alignment={_compact_text(raw.get('alignment_status'), 'unknown')}; "
            f"mismatch={_compact_text(raw.get('mismatch_type'), 'unknown_case')}"
        ),
    }


def to_known_science_replay_selector_bridge_json_safe_v1(packet: Any) -> dict[str, Any]:
    return _json_safe(packet if isinstance(packet, Mapping) else {})


def build_initial_known_science_replay_selector_bridge_examples_v1() -> tuple[dict[str, Any], ...]:
    cases = _KNOWN_REPLAY_CASES_V1
    examples: list[dict[str, Any]] = []
    for case in cases:
        phases = case.get("replay_phases", []) if isinstance(case, Mapping) else []
        if not phases:
            continue
        selected_phases = phases if _compact_text(case.get("case_id")) == "pulsar_discovery_replay" else phases[:1]
        for phase in selected_phases:
            expected = phase.get("expected_internal_next_step", phase.get("expected_selector_outcome"))
            selected = _compact_text(expected)
            if _compact_text(phase.get("phase_name")) == "unsafe_public_claim_attempt":
                selected = "blocked"
            input_packet = build_known_science_replay_selector_bridge_input_v1(
                {
                    "bridge_id": f"{case['case_id']}:{phase['phase_id']}:bridge",
                    "replay_case": case,
                    "replay_phase": phase,
                    "source_replay_case_id": case["case_id"],
                    "source_known_outcome": case["known_outcome"],
                    "source_case_domain": case["domain"],
                    "replay_phase_id": phase["phase_id"],
                    "replay_phase_summary": phase.get("historical_signal_summary") or phase.get("safe_interpretation"),
                    "expected_internal_next_step": expected,
                    "selector_input_metadata": {
                        "bridge_family": "known_science_replay_selector_calibration",
                        "case_title": case["case_title"],
                        "phase_name": phase.get("phase_name"),
                        "phase_order": phase.get("phase_order"),
                        "known_outcome": case["known_outcome"],
                    },
                    "selector_selected_next_step": selected,
                    "selector_selection_reason": (
                        "unsafe public-claim pressure blocked"
                        if selected == "blocked" and _compact_text(phase.get("phase_name")) == "unsafe_public_claim_attempt"
                        else "matches the expected internal next step"
                    ),
                    "forbidden_interpretations": phase.get("forbidden_interpretations") or case.get("forbidden_interpretations", []),
                    "authority_status": _default_authority_status(),
                    "safe_metadata": _default_safe_metadata(),
                }
            )
            packet = build_known_science_replay_selector_bridge_packet_v1(input_packet)
            examples.append(packet)
    return tuple(examples)
