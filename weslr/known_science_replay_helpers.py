"""WESLR Known-Science Replay Helpers V1.

Deterministic, metadata-only helpers for representing and validating known-science
replay cases used for internal calibration only.
"""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from typing import Any, Mapping

SCHEMA_VERSION_V1 = "known_science_replay_case_v1"
PHASE_SCHEMA_VERSION_V1 = "known_science_replay_phase_v1"
SELECTOR_CALIBRATION_SCHEMA_VERSION_V1 = "known_science_replay_selector_calibration_v1"
COMPONENT_MAPPING_SCHEMA_VERSION_V1 = "known_science_replay_component_mapping_v1"

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
ALLOWED_PUBLIC_CLAIM_STATUSES_V1 = (
    "internal_candidate_only",
    "internal_reading_only",
    "not_public_ready",
)
KNOWN_REPLAY_COMPONENTS_V1 = (
    "Raw Signal Cartographer",
    "Unintelligible Output Analyzer",
    "Unknown Engine",
    "Nonlinear Inspiration / Resonance",
    "Rule Pressure Engine",
    "Dialectic Generator Loop",
    "Perspicuity Scorer",
    "Suggestion Store Update Packet",
    "Forecast Calibration Bridge",
    "Minimal Recursive Research Loop Dry-Run Executor",
    "Recursive Research Loop Scenario Set",
    "Human-Readable Findings Digest",
    "Scenario-Sensitive Next-Step Selector",
)
FORBIDDEN_PUBLIC_CLAIM_MARKERS_V1 = (
    "discovery",
    "proof",
    "breakthrough",
    "scientific result",
    "benchmark",
    "certification",
    "agi",
    "intelligence",
    "sentience",
    "consciousness",
    "public science",
    "final answer",
    "official intelligence",
)
FORBIDDEN_PRIVATE_TEXT_MARKERS_V1 = (
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
    "replay runner",
    "executor",
    "runner",
    "provider call",
    "tool execution",
    "web call",
    "retrieval call",
    "runtime wiring",
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
    "replay_family_safe",
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


def _default_authority_status() -> dict[str, Any]:
    return {
        "runtime_action_authorized": False,
        "replay_runner_authorized": False,
        "executor_authorized": False,
        "runner_authorized": False,
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
    }


def _default_denied_authority() -> dict[str, Any]:
    return {
        "runtime_action_authorized": False,
        "replay_runner_authorized": False,
        "executor_authorized": False,
        "runner_authorized": False,
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
        "boundary_notes": "known-science replay helpers: metadata-only internal boundary",
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
        "replay_family_safe": True,
    }


def _allowed_selector_outcome(value: Any) -> bool:
    return _compact_text(value) in ALLOWED_SELECTOR_OUTCOMES_V1


def build_known_science_replay_phase_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = _merge_payload(payload, **overrides)
    case_id = _compact_text(data.get("case_id"), "unknown_case")
    phase = {
        "schema_version": PHASE_SCHEMA_VERSION_V1,
        "phase_id": _compact_text(data.get("phase_id") or f"{case_id}:phase:{_compact_text(data.get('phase_name'), 'phase')}"),
        "case_id": case_id,
        "phase_name": _compact_text(data.get("phase_name"), "unknown_phase"),
        "phase_order": int(data.get("phase_order") if isinstance(data.get("phase_order"), int) else 0),
        "historical_signal_summary": _compact_text(data.get("historical_signal_summary")),
        "initial_ambiguity": _compact_text(data.get("initial_ambiguity"), "unknown"),
        "ordinary_explanations_to_pressure": list(data.get("ordinary_explanations_to_pressure") or []),
        "candidate_hypotheses": list(data.get("candidate_hypotheses") or []),
        "pressure_tests": list(data.get("pressure_tests") or []),
        "calibration_signals": list(data.get("calibration_signals") or []),
        "falsification_signals": list(data.get("falsification_signals") or []),
        "expected_selector_outcome": _compact_text(data.get("expected_selector_outcome"), "unknown"),
        "expected_internal_next_step": _compact_text(data.get("expected_internal_next_step"), "unknown"),
        "known_outcome_reference": _compact_text(data.get("known_outcome_reference"), ""),
        "safe_interpretation": _compact_text(data.get("safe_interpretation"), ""),
        "forbidden_interpretations": list(data.get("forbidden_interpretations") or []),
        "public_claim_status": _compact_text(data.get("public_claim_status"), "internal_candidate_only"),
        "authority_status": _json_safe(data.get("authority_status") or _default_authority_status()),
        "safe_metadata": _json_safe(data.get("safe_metadata") or _default_safe_metadata()),
    }
    return _json_safe(phase)


def build_known_science_replay_selector_calibration_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = _merge_payload(payload, **overrides)
    case_id = _compact_text(data.get("case_id"), "unknown_case")
    outcomes = list(data.get("selector_outcomes") or data.get("expected_selector_outcomes") or [])
    calibration = {
        "schema_version": SELECTOR_CALIBRATION_SCHEMA_VERSION_V1,
        "case_id": case_id,
        "selector_outcomes": outcomes,
        "expected_internal_next_steps": list(data.get("expected_internal_next_steps") or []),
        "expected_wrong_shortcuts": list(data.get("expected_wrong_shortcuts") or []),
        "calibration_goal": _compact_text(data.get("calibration_goal"), "preserve uncertainty and choose safe internal next steps"),
        "selector_safety_notes": _compact_text(data.get("selector_safety_notes"), "internal calibration only"),
        "public_claim_status": _compact_text(data.get("public_claim_status"), "internal_candidate_only"),
        "authority_status": _json_safe(data.get("authority_status") or _default_authority_status()),
        "safe_metadata": _json_safe(data.get("safe_metadata") or _default_safe_metadata()),
    }
    return _json_safe(calibration)


def build_known_science_replay_component_mapping_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = _merge_payload(payload, **overrides)
    case_id = _compact_text(data.get("case_id"), "unknown_case")
    mappings = list(data.get("component_mappings") or [])
    if not mappings:
        mappings = [
            {
                "component_name": name,
                "role": "calibration_input",
                "safe_usage": "metadata_only",
                "safe_boundary": "metadata-only internal boundary",
            }
            for name in KNOWN_REPLAY_COMPONENTS_V1
        ]
    mapping = {
        "schema_version": COMPONENT_MAPPING_SCHEMA_VERSION_V1,
        "case_id": case_id,
        "component_mappings": mappings,
        "mapping_goal": _compact_text(data.get("mapping_goal"), "calibration-only component alignment"),
        "public_claim_status": _compact_text(data.get("public_claim_status"), "internal_candidate_only"),
        "authority_status": _json_safe(data.get("authority_status") or _default_authority_status()),
        "safe_metadata": _json_safe(data.get("safe_metadata") or _default_safe_metadata()),
    }
    return _json_safe(mapping)


def build_known_science_replay_case_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = _merge_payload(payload, **overrides)
    case_id = _compact_text(data.get("case_id"), "unknown_case")
    case_title = _compact_text(data.get("case_title"), case_id.replace("_", " ").title())
    known_outcome = _compact_text(data.get("known_outcome"))
    historical_signal_summary = _compact_text(data.get("historical_signal_summary"))
    initial_ambiguity = _compact_text(data.get("initial_ambiguity"), "unknown")
    ordinary_explanations = list(data.get("ordinary_explanations_to_pressure") or [])
    candidate_hypotheses = list(data.get("candidate_hypotheses") or [])
    expected_internal_next_steps = list(data.get("expected_internal_next_steps") or [])
    expected_wrong_shortcuts = list(data.get("expected_wrong_shortcuts") or [])
    pressure_tests = list(data.get("pressure_tests") or [])
    calibration_signals = list(data.get("calibration_signals") or [])
    falsification_signals = list(data.get("falsification_signals") or [])
    safe_interpretation = _compact_text(data.get("safe_interpretation"))
    forbidden_interpretations = list(data.get("forbidden_interpretations") or [])
    source_scope = _compact_text(data.get("source_scope"), "public/high-level historical facts only")
    public_claim_status = _compact_text(data.get("public_claim_status"), "internal_candidate_only")
    authority_status = _json_safe(data.get("authority_status") or _default_authority_status())
    denied_authority = _json_safe(data.get("denied_authority") or _default_denied_authority())
    safe_metadata = _json_safe(data.get("safe_metadata") or _default_safe_metadata())
    replay_phases = list(data.get("replay_phases") or [])
    selector_calibration = data.get("selector_calibration") if isinstance(data.get("selector_calibration"), Mapping) else build_known_science_replay_selector_calibration_v1(
        {
            "case_id": case_id,
            "selector_outcomes": expected_internal_next_steps,
            "expected_internal_next_steps": expected_internal_next_steps,
            "expected_wrong_shortcuts": expected_wrong_shortcuts,
            "public_claim_status": public_claim_status,
            "authority_status": authority_status,
            "safe_metadata": safe_metadata,
        }
    )
    component_mapping = data.get("component_mapping") if isinstance(data.get("component_mapping"), Mapping) else build_known_science_replay_component_mapping_v1(
        {
            "case_id": case_id,
            "public_claim_status": public_claim_status,
            "authority_status": authority_status,
            "safe_metadata": safe_metadata,
        }
    )
    implementation_readiness = _compact_text(data.get("implementation_readiness"), "design-only and ready for helper implementation review")
    case = {
        "schema_version": SCHEMA_VERSION_V1,
        "case_id": case_id,
        "case_title": case_title,
        "domain": _compact_text(data.get("domain")),
        "known_outcome": known_outcome,
        "historical_signal_summary": historical_signal_summary,
        "initial_ambiguity": initial_ambiguity,
        "ordinary_explanations_to_pressure": ordinary_explanations,
        "candidate_hypotheses": candidate_hypotheses,
        "expected_internal_next_steps": expected_internal_next_steps,
        "expected_wrong_shortcuts": expected_wrong_shortcuts,
        "pressure_tests": pressure_tests,
        "calibration_signals": calibration_signals,
        "falsification_signals": falsification_signals,
        "safe_interpretation": safe_interpretation,
        "forbidden_interpretations": forbidden_interpretations,
        "source_scope": source_scope,
        "public_claim_status": public_claim_status,
        "authority_status": authority_status,
        "denied_authority": denied_authority,
        "safe_metadata": safe_metadata,
        "replay_phases": replay_phases,
        "selector_calibration": _json_safe(selector_calibration),
        "component_mapping": _json_safe(component_mapping),
        "implementation_readiness": implementation_readiness,
    }
    return _json_safe(case)


def _validate_authority_status(authority_status: Any, blocked_labels: list[str], label_prefix: str = "unsafe") -> None:
    if not isinstance(authority_status, Mapping):
        blocked_labels.append("missing_authority_status")
        return
    for key, value in authority_status.items():
        if key in {"all_authority_flags_false", "status", "boundary_notes"}:
            continue
        if bool(value):
            blocked_labels.append(f"{label_prefix}_{key}")
    if authority_status.get("all_authority_flags_false") is not True:
        blocked_labels.append("unsafe_authority_status")


def _validate_safe_metadata(safe_metadata: Any, blocked_labels: list[str]) -> None:
    if not isinstance(safe_metadata, Mapping):
        blocked_labels.append("missing_safe_metadata")
        return
    for field in REQUIRED_SAFE_METADATA_FLAGS_V1:
        if safe_metadata.get(field) is not True:
            blocked_labels.append(f"unsafe_safe_metadata_{field}")


def validate_known_science_replay_case_v1(case: Any) -> dict[str, Any]:
    raw = case if isinstance(case, Mapping) else {}
    blocked_labels: list[str] = []

    if not isinstance(case, Mapping):
        blocked_labels.append("invalid_case_type")
        return {
            "schema_version": SCHEMA_VERSION_V1,
            "valid": False,
            "blocked": True,
            "blocked_labels": blocked_labels,
            "summary_text": "Blocked known-science replay case: invalid case type.",
        }

    if _compact_text(raw.get("schema_version")) != SCHEMA_VERSION_V1:
        blocked_labels.append("invalid_schema_version")
    if not _compact_text(raw.get("case_id")):
        blocked_labels.append("missing_case_id")
    if not _compact_text(raw.get("case_title")):
        blocked_labels.append("missing_case_title")
    if not _compact_text(raw.get("domain")):
        blocked_labels.append("missing_domain")
    if not _compact_text(raw.get("known_outcome")):
        blocked_labels.append("missing_known_outcome")
    if not _compact_text(raw.get("historical_signal_summary")):
        blocked_labels.append("missing_historical_signal_summary")
    if not _compact_text(raw.get("initial_ambiguity")):
        blocked_labels.append("missing_initial_ambiguity")

    for field in (
        "ordinary_explanations_to_pressure",
        "candidate_hypotheses",
        "expected_internal_next_steps",
        "expected_wrong_shortcuts",
        "pressure_tests",
        "calibration_signals",
        "falsification_signals",
        "forbidden_interpretations",
    ):
        value = raw.get(field)
        if not isinstance(value, list) or not value:
            blocked_labels.append(f"missing_{field}")

    if not _compact_text(raw.get("safe_interpretation")):
        blocked_labels.append("missing_safe_interpretation")
    if not _compact_text(raw.get("source_scope")):
        blocked_labels.append("missing_source_scope")

    public_claim_status = _compact_text(raw.get("public_claim_status"))
    if not public_claim_status:
        blocked_labels.append("missing_public_claim_status")
    elif public_claim_status not in ALLOWED_PUBLIC_CLAIM_STATUSES_V1:
        blocked_labels.append("invalid_public_claim_status")

    _validate_authority_status(raw.get("authority_status"), blocked_labels)
    if not isinstance(raw.get("denied_authority"), Mapping):
        blocked_labels.append("missing_denied_authority")
    else:
        _validate_authority_status(raw.get("denied_authority"), blocked_labels, label_prefix="granted")
        if _contains_markers(raw.get("denied_authority"), FORBIDDEN_PRIVATE_TEXT_MARKERS_V1):
            blocked_labels.append("forbidden_private_text")

    _validate_safe_metadata(raw.get("safe_metadata"), blocked_labels)

    if _contains_markers(raw.get("case_title"), FORBIDDEN_PUBLIC_CLAIM_MARKERS_V1):
        blocked_labels.append("forbidden_claim_language")
    if _contains_markers(raw.get("historical_signal_summary"), FORBIDDEN_PUBLIC_CLAIM_MARKERS_V1):
        blocked_labels.append("forbidden_claim_language")
    if _contains_markers(raw.get("historical_signal_summary"), FORBIDDEN_PRIVATE_TEXT_MARKERS_V1):
        blocked_labels.append("forbidden_private_text")
    if _contains_markers(raw.get("ordinary_explanations_to_pressure"), FORBIDDEN_PUBLIC_CLAIM_MARKERS_V1):
        blocked_labels.append("forbidden_claim_language")
    if _contains_markers(raw.get("candidate_hypotheses"), FORBIDDEN_PUBLIC_CLAIM_MARKERS_V1):
        blocked_labels.append("forbidden_claim_language")
    if _contains_markers(raw.get("candidate_hypotheses"), FORBIDDEN_PRIVATE_TEXT_MARKERS_V1):
        blocked_labels.append("forbidden_private_text")
    if _contains_markers(raw.get("safe_interpretation"), FORBIDDEN_PUBLIC_CLAIM_MARKERS_V1):
        blocked_labels.append("forbidden_claim_language")
    if _contains_markers(raw.get("safe_interpretation"), FORBIDDEN_PRIVATE_TEXT_MARKERS_V1):
        blocked_labels.append("forbidden_private_text")
    if _contains_markers(raw.get("pressure_tests"), FORBIDDEN_PUBLIC_CLAIM_MARKERS_V1):
        blocked_labels.append("forbidden_claim_language")
    if _contains_markers(raw.get("calibration_signals"), FORBIDDEN_PUBLIC_CLAIM_MARKERS_V1):
        blocked_labels.append("forbidden_claim_language")
    if _contains_markers(raw.get("falsification_signals"), FORBIDDEN_PUBLIC_CLAIM_MARKERS_V1):
        blocked_labels.append("forbidden_claim_language")
    if _contains_markers(raw.get("source_scope"), FORBIDDEN_PRIVATE_TEXT_MARKERS_V1):
        blocked_labels.append("forbidden_private_text")
    if _contains_markers(raw.get("implementation_readiness"), FORBIDDEN_PUBLIC_CLAIM_MARKERS_V1):
        blocked_labels.append("forbidden_claim_language")
    if _contains_markers(raw.get("implementation_readiness"), FORBIDDEN_PRIVATE_TEXT_MARKERS_V1):
        blocked_labels.append("forbidden_private_text")
    if _contains_markers(raw.get("forbidden_interpretations"), FORBIDDEN_PUBLIC_CLAIM_MARKERS_V1):
        blocked_labels.append("forbidden_claim_language")
    if _contains_markers(raw.get("forbidden_interpretations"), FORBIDDEN_PRIVATE_TEXT_MARKERS_V1):
        blocked_labels.append("forbidden_private_text")

    selector_calibration = raw.get("selector_calibration")
    if not isinstance(selector_calibration, Mapping):
        blocked_labels.append("missing_selector_calibration")
    else:
        if _compact_text(selector_calibration.get("schema_version")) != SELECTOR_CALIBRATION_SCHEMA_VERSION_V1:
            blocked_labels.append("invalid_selector_calibration")
        if not isinstance(selector_calibration.get("selector_outcomes"), list) or not selector_calibration.get("selector_outcomes"):
            blocked_labels.append("missing_selector_outcomes")
        else:
            for outcome in selector_calibration.get("selector_outcomes", []):
                if not _allowed_selector_outcome(outcome):
                    blocked_labels.append("invalid_selector_outcome")
        for field in ("expected_internal_next_steps", "expected_wrong_shortcuts"):
            value = selector_calibration.get(field)
            if not isinstance(value, list) or not value:
                blocked_labels.append(f"missing_{field}")
        _validate_authority_status(selector_calibration.get("authority_status"), blocked_labels)
        _validate_safe_metadata(selector_calibration.get("safe_metadata"), blocked_labels)

    component_mapping = raw.get("component_mapping")
    if not isinstance(component_mapping, Mapping):
        blocked_labels.append("missing_component_mapping")
    else:
        if _compact_text(component_mapping.get("schema_version")) != COMPONENT_MAPPING_SCHEMA_VERSION_V1:
            blocked_labels.append("invalid_component_mapping")
        mappings = component_mapping.get("component_mappings")
        if not isinstance(mappings, list) or not mappings:
            blocked_labels.append("missing_component_mappings")
        else:
            names = []
            for entry in mappings:
                if not isinstance(entry, Mapping):
                    blocked_labels.append("invalid_component_mapping_entry")
                    continue
                name = _compact_text(entry.get("component_name"))
                if not name:
                    blocked_labels.append("missing_component_name")
                else:
                    names.append(name)
                if not _compact_text(entry.get("safe_usage")):
                    blocked_labels.append("missing_component_safe_usage")
                if not _compact_text(entry.get("safe_boundary")):
                    blocked_labels.append("missing_component_safe_boundary")
                if _contains_markers(entry, FORBIDDEN_PUBLIC_CLAIM_MARKERS_V1):
                    blocked_labels.append("forbidden_claim_language")
                if _contains_markers(entry, FORBIDDEN_PRIVATE_TEXT_MARKERS_V1):
                    blocked_labels.append("forbidden_private_text")
            if names and not set(KNOWN_REPLAY_COMPONENTS_V1).issubset(set(names)):
                blocked_labels.append("unexpected_component_mapping")

    if isinstance(raw.get("expected_internal_next_steps"), list):
        for outcome in raw.get("expected_internal_next_steps", []):
            if not _allowed_selector_outcome(outcome):
                blocked_labels.append("invalid_selector_outcome")
    else:
        blocked_labels.append("missing_expected_internal_next_steps")

    if _first_non_json_safe_path(raw) is not None:
        blocked_labels.append("non_json_safe_result_structure")

    valid = not blocked_labels
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "valid": valid,
        "blocked": not valid,
        "blocked_labels": list(dict.fromkeys(blocked_labels)),
        "summary_text": summarize_known_science_replay_case_v1(raw),
        "case_id": _compact_text(raw.get("case_id")),
        "known_outcome": _compact_text(raw.get("known_outcome")),
    }


def summarize_known_science_replay_case_v1(case: Any) -> dict[str, Any]:
    raw = case if isinstance(case, Mapping) else {}
    expected_steps = raw.get("expected_internal_next_steps") if isinstance(raw.get("expected_internal_next_steps"), list) else []
    outcomes = raw.get("selector_calibration", {}).get("selector_outcomes") if isinstance(raw.get("selector_calibration"), Mapping) else []
    return {
        "summary_type": SCHEMA_VERSION_V1,
        "case_id": _compact_text(raw.get("case_id"), "unknown_case"),
        "case_title": _compact_text(raw.get("case_title"), "unknown case"),
        "domain": _compact_text(raw.get("domain"), "unknown"),
        "known_outcome": _compact_text(raw.get("known_outcome"), "unknown"),
        "selector_outcomes": list(outcomes or []),
        "expected_internal_next_steps": list(expected_steps),
        "summary_text": (
            f"Known-science replay case {_compact_text(raw.get('case_id'), 'unknown_case')}: "
            f"domain={_compact_text(raw.get('domain'), 'unknown')}; "
            f"known_outcome={_compact_text(raw.get('known_outcome'), 'unknown')}; "
            f"steps={', '.join(map(_compact_text, expected_steps)) or 'none'}"
        ),
    }


def to_known_science_replay_json_safe_v1(case: Any) -> dict[str, Any]:
    return _json_safe(case if isinstance(case, Mapping) else {})


def _canonical_pulsar_case_v1() -> dict[str, Any]:
    case_id = "pulsar_discovery_replay"
    phases = [
        build_known_science_replay_phase_v1(
            {
                "case_id": case_id,
                "phase_name": "initial_strange_signal",
                "phase_order": 1,
                "historical_signal_summary": "strange periodic radio signal appears",
                "initial_ambiguity": "high",
                "ordinary_explanations_to_pressure": ["instrument artifact", "interference", "environmental noise", "processing error"],
                "candidate_hypotheses": ["instrument/interference", "astrophysical source", "unusual natural phenomenon"],
                "pressure_tests": ["repeat observation", "timing consistency", "instrument comparison"],
                "calibration_signals": ["repeatability not yet established"],
                "falsification_signals": ["one-off signal", "site-specific artifact"],
                "expected_selector_outcome": "probe",
                "expected_internal_next_step": "probe",
                "known_outcome_reference": "pulsars / rotating neutron stars",
                "safe_interpretation": "worth probing while preserving uncertainty",
                "forbidden_interpretations": ["instrument artifact", "interference artifact", "alternative explanation"],
                "public_claim_status": "not_public_ready",
            }
        ),
        build_known_science_replay_phase_v1(
            {
                "case_id": case_id,
                "phase_name": "repeated_precise_signal",
                "phase_order": 2,
                "historical_signal_summary": "signal repeats with a precise period",
                "initial_ambiguity": "reduced but unresolved",
                "ordinary_explanations_to_pressure": ["interference", "environmental noise", "processing error"],
                "candidate_hypotheses": ["instrument/interference", "astrophysical source", "unusual natural phenomenon"],
                "pressure_tests": ["repeat observation", "timing consistency", "site comparison"],
                "calibration_signals": ["stable periodicity", "repeatable detection"],
                "falsification_signals": ["instrument-only behavior", "failed control checks"],
                "expected_selector_outcome": "pressure_test",
                "expected_internal_next_step": "pressure_test",
                "known_outcome_reference": "pulsars / rotating neutron stars",
                "safe_interpretation": "pressure-test ordinary explanations before exotic ones",
                "forbidden_interpretations": ["instrument artifact", "interference artifact", "alternative explanation"],
                "public_claim_status": "not_public_ready",
            }
        ),
        build_known_science_replay_phase_v1(
            {
                "case_id": case_id,
                "phase_name": "ordinary_explanations_weakened",
                "phase_order": 3,
                "historical_signal_summary": "ordinary explanations weaken under repeated checks",
                "initial_ambiguity": "lower but still cautious",
                "ordinary_explanations_to_pressure": ["instrument artifact", "interference", "environmental noise"],
                "candidate_hypotheses": ["astrophysical source", "rotating neutron star", "unusual natural phenomenon"],
                "pressure_tests": ["instrument comparison", "site comparison", "signal persistence"],
                "calibration_signals": ["repeatable detection", "reduced artifact likelihood"],
                "falsification_signals": ["control-check failures", "instrument-specific anomaly"],
                "expected_selector_outcome": "calibrate",
                "expected_internal_next_step": "calibrate",
                "known_outcome_reference": "pulsars / rotating neutron stars",
                "safe_interpretation": "continue calibration and repeated observation",
                "forbidden_interpretations": ["instrument artifact", "interference artifact", "alternative explanation"],
                "public_claim_status": "not_public_ready",
            }
        ),
        build_known_science_replay_phase_v1(
            {
                "case_id": case_id,
                "phase_name": "external_confirmation",
                "phase_order": 4,
                "historical_signal_summary": "multiple similar sources and external confirmation appear later",
                "initial_ambiguity": "resolved by external evidence",
                "ordinary_explanations_to_pressure": ["instrument artifact", "interference"],
                "candidate_hypotheses": ["astrophysical source", "rotating neutron star"],
                "pressure_tests": ["repeat observation", "cross-site comparison", "external corroboration"],
                "calibration_signals": ["multiple similar sources", "external confirmation"],
                "falsification_signals": ["no corroboration", "control-check failure"],
                "expected_selector_outcome": "archive",
                "expected_internal_next_step": "archive",
                "known_outcome_reference": "pulsars / rotating neutron stars",
                "safe_interpretation": "map to the known outcome only after external evidence exists",
                "forbidden_interpretations": ["instrument artifact", "interference artifact", "alternative explanation"],
                "public_claim_status": "not_public_ready",
            }
        ),
        build_known_science_replay_phase_v1(
            {
                "case_id": case_id,
                "phase_name": "unsafe_public_claim_attempt",
                "phase_order": 5,
                "historical_signal_summary": "public claim pressure appears before evidence is sufficient",
                "initial_ambiguity": "unsafe to publish",
                "ordinary_explanations_to_pressure": ["still ambiguous", "not enough evidence"],
                "candidate_hypotheses": ["astrophysical source", "rotating neutron star"],
                "pressure_tests": ["repeat observation", "corroboration"],
                "calibration_signals": ["evidence still incomplete"],
                "falsification_signals": ["public-claim pressure", "overconfidence"],
                "expected_selector_outcome": "operator_review",
                "expected_internal_next_step": "operator_review",
                "known_outcome_reference": "pulsars / rotating neutron stars",
                "safe_interpretation": "do not publish claims prematurely",
                "forbidden_interpretations": ["instrument artifact", "interference artifact", "alternative explanation"],
                "public_claim_status": "not_public_ready",
            }
        ),
    ]
    return build_known_science_replay_case_v1(
        {
            "case_id": case_id,
            "case_title": "Pulsar anomaly replay",
            "domain": "radio astronomy / signal interpretation",
            "known_outcome": "pulsars / rotating neutron stars",
            "historical_signal_summary": "strange periodic radio signal, initially ambiguous, repeatedly observed, eventually explained as an astrophysical source",
            "initial_ambiguity": "high",
            "ordinary_explanations_to_pressure": ["instrument artifact", "interference", "environmental noise", "processing error", "human misread"],
            "candidate_hypotheses": ["instrument/interference", "astrophysical source", "unusual natural phenomenon"],
            "expected_internal_next_steps": ["probe", "pressure_test", "calibrate", "archive", "operator_review"],
            "expected_wrong_shortcuts": ["immediate discovery claim", "immediate alien claim", "immediate noise dismissal", "premature certainty"],
            "pressure_tests": ["repeat observation", "timing consistency", "instrument comparison", "site comparison", "signal persistence", "alternative explanation elimination"],
            "calibration_signals": ["stable periodicity", "repeatable detection", "improved measurement reliability", "reduced artifact likelihood", "corroborating observation"],
            "falsification_signals": ["inconsistent periodicity", "instrument-specific only behavior", "interference signature", "repeat failure under control checks"],
            "safe_interpretation": "interesting signal worth probing and pressure-testing while preserving uncertainty",
            "forbidden_interpretations": ["instrument artifact", "interference artifact", "public pressure", "overconfidence", "premature publication", "final-answer pressure"],
            "source_scope": "public/high-level historical facts only",
            "public_claim_status": "internal_candidate_only",
            "authority_status": _default_authority_status(),
            "denied_authority": _default_denied_authority(),
            "safe_metadata": _default_safe_metadata(),
            "replay_phases": phases,
            "selector_calibration": build_known_science_replay_selector_calibration_v1(
                {
                    "case_id": case_id,
                    "selector_outcomes": ["probe", "pressure_test", "calibrate", "archive", "operator_review"],
                    "expected_internal_next_steps": ["probe", "pressure_test", "calibrate", "archive", "operator_review"],
                    "expected_wrong_shortcuts": ["immediate discovery claim", "immediate alien claim", "premature certainty"],
                    "public_claim_status": "internal_candidate_only",
                    "authority_status": _default_authority_status(),
                    "safe_metadata": _default_safe_metadata(),
                }
            ),
            "component_mapping": build_known_science_replay_component_mapping_v1({"case_id": case_id}),
            "implementation_readiness": "design-only calibration example",
        }
    )


def _stub_case(case_id: str, case_title: str, domain: str, known_outcome: str, signal: str, ordinary: list[str], hypothesis: list[str]) -> dict[str, Any]:
    phases = [
        build_known_science_replay_phase_v1(
            {
                "case_id": case_id,
                "phase_name": "initial_ambiguity",
                "phase_order": 1,
                "historical_signal_summary": signal,
                "initial_ambiguity": "moderate",
                "ordinary_explanations_to_pressure": ordinary,
                "candidate_hypotheses": hypothesis,
                "pressure_tests": ["repeat observation", "control comparison"],
                "calibration_signals": ["repeatability", "measurement stability"],
                "falsification_signals": ["control failure", "inconsistency"],
                "expected_selector_outcome": "probe",
                "expected_internal_next_step": "probe",
                "known_outcome_reference": known_outcome,
                "safe_interpretation": "interesting but not yet settled",
                "forbidden_interpretations": ["instrument artifact", "interference artifact"],
                "public_claim_status": "not_public_ready",
            }
        ),
        build_known_science_replay_phase_v1(
            {
                "case_id": case_id,
                "phase_name": "calibration_follow_up",
                "phase_order": 2,
                "historical_signal_summary": f"follow-up measurements refine the signal path for {case_title.lower()}",
                "initial_ambiguity": "lower but still cautious",
                "ordinary_explanations_to_pressure": ordinary,
                "candidate_hypotheses": hypothesis,
                "pressure_tests": ["repeat observation", "alternative explanation check"],
                "calibration_signals": ["repeatability"],
                "falsification_signals": ["inconsistency"],
                "expected_selector_outcome": "calibrate",
                "expected_internal_next_step": "calibrate",
                "known_outcome_reference": known_outcome,
                "safe_interpretation": "continue calibration",
                "forbidden_interpretations": ["instrument artifact", "interference artifact"],
                "public_claim_status": "not_public_ready",
            }
        ),
    ]
    return build_known_science_replay_case_v1(
        {
            "case_id": case_id,
            "case_title": case_title,
            "domain": domain,
            "known_outcome": known_outcome,
            "historical_signal_summary": signal,
            "initial_ambiguity": "moderate",
            "ordinary_explanations_to_pressure": ordinary,
            "candidate_hypotheses": hypothesis,
            "expected_internal_next_steps": ["probe", "pressure_test", "calibrate", "archive"],
            "expected_wrong_shortcuts": ["premature certainty", "public claim", "noise dismissal"],
            "pressure_tests": ["repeat observation", "alternative explanation check"],
            "calibration_signals": ["repeatability", "measurement stability"],
            "falsification_signals": ["inconsistency", "control failure"],
            "safe_interpretation": "useful calibration example with uncertainty preserved",
            "forbidden_interpretations": ["instrument artifact", "interference artifact", "public pressure"],
            "source_scope": "public/high-level historical facts only",
            "public_claim_status": "internal_candidate_only",
            "authority_status": _default_authority_status(),
            "denied_authority": _default_denied_authority(),
            "safe_metadata": _default_safe_metadata(),
            "replay_phases": phases,
            "selector_calibration": build_known_science_replay_selector_calibration_v1(
                {
                    "case_id": case_id,
                    "selector_outcomes": ["probe", "pressure_test", "calibrate", "watch", "archive"],
                    "expected_internal_next_steps": ["probe", "pressure_test", "calibrate", "archive"],
                    "expected_wrong_shortcuts": ["premature certainty", "public claim"],
                    "public_claim_status": "internal_candidate_only",
                    "authority_status": _default_authority_status(),
                    "safe_metadata": _default_safe_metadata(),
                }
            ),
            "component_mapping": build_known_science_replay_component_mapping_v1({"case_id": case_id}),
            "implementation_readiness": "design-only calibration stub",
        }
    )


def build_initial_known_science_replay_examples_v1() -> tuple[dict[str, Any], ...]:
    return (
        _canonical_pulsar_case_v1(),
        _stub_case(
            "continental_drift_replay",
            "Continental drift replay",
            "earth science / plate tectonics",
            "continental drift accepted as plate tectonics",
            "continents appear to fit and move over time",
            ["map coincidence", "static-earth assumption", "measurement error"],
            ["moving continents", "plate tectonics", "geological process"],
        ),
        _stub_case(
            "penicillin_contamination_replay",
            "Penicillin contamination replay",
            "microbiology / medical discovery",
            "penicillin recognized as an antibiotic",
            "mold-contaminated culture inhibits bacterial growth",
            ["contamination", "bad sample", "lab error"],
            ["contamination as clue", "antibacterial compound", "unexpected bioactivity"],
        ),
        _stub_case(
            "cosmic_microwave_background_replay",
            "Cosmic microwave background replay",
            "cosmology / observational astronomy",
            "cosmic microwave background detected and interpreted as a relic signal",
            "persistent background radio signal remains after ordinary checks",
            ["instrument noise", "environmental interference", "calibration drift"],
            ["instrument artifact", "astrophysical background", "cosmological relic"],
        ),
        _stub_case(
            "helicobacter_pylori_ulcer_replay",
            "Helicobacter pylori ulcer replay",
            "medicine / infectious disease",
            "H. pylori implicated in many ulcers",
            "persistent biological pattern resists the old stress-only explanation",
            ["stress response", "acid imbalance", "dietary cause"],
            ["infectious agent", "biological mechanism", "environmental factor"],
        ),
    )


def _validate_selector_calibration(calibration: Any, blocked_labels: list[str]) -> None:
    if not isinstance(calibration, Mapping):
        blocked_labels.append("missing_selector_calibration")
        return
    if _compact_text(calibration.get("schema_version")) != SELECTOR_CALIBRATION_SCHEMA_VERSION_V1:
        blocked_labels.append("invalid_selector_calibration")
    outcomes = calibration.get("selector_outcomes")
    if not isinstance(outcomes, list) or not outcomes:
        blocked_labels.append("missing_selector_outcomes")
    else:
        for outcome in outcomes:
            if not _allowed_selector_outcome(outcome):
                blocked_labels.append("invalid_selector_outcome")
    for field in ("expected_internal_next_steps", "expected_wrong_shortcuts"):
        value = calibration.get(field)
        if not isinstance(value, list) or not value:
            blocked_labels.append(f"missing_{field}")
    _validate_authority_status(calibration.get("authority_status"), blocked_labels)
    _validate_safe_metadata(calibration.get("safe_metadata"), blocked_labels)


def _validate_component_mapping(mapping: Any, blocked_labels: list[str]) -> None:
    if not isinstance(mapping, Mapping):
        blocked_labels.append("missing_component_mapping")
        return
    if _compact_text(mapping.get("schema_version")) != COMPONENT_MAPPING_SCHEMA_VERSION_V1:
        blocked_labels.append("invalid_component_mapping")
    entries = mapping.get("component_mappings")
    if not isinstance(entries, list) or not entries:
        blocked_labels.append("missing_component_mappings")
        return
    names = []
    for entry in entries:
        if not isinstance(entry, Mapping):
            blocked_labels.append("invalid_component_mapping_entry")
            continue
        name = _compact_text(entry.get("component_name"))
        if not name:
            blocked_labels.append("missing_component_name")
        else:
            names.append(name)
        if not _compact_text(entry.get("role")):
            blocked_labels.append("missing_component_role")
        if not _compact_text(entry.get("safe_usage")):
            blocked_labels.append("missing_component_safe_usage")
        if not _compact_text(entry.get("safe_boundary")):
            blocked_labels.append("missing_component_safe_boundary")
    if names and not set(KNOWN_REPLAY_COMPONENTS_V1).issubset(set(names)):
        blocked_labels.append("unexpected_component_mapping")


def validate_known_science_replay_phase_v1(phase: Any) -> dict[str, Any]:
    raw = phase if isinstance(phase, Mapping) else {}
    blocked_labels: list[str] = []
    if not isinstance(phase, Mapping):
        blocked_labels.append("invalid_phase_type")
        return {"schema_version": PHASE_SCHEMA_VERSION_V1, "valid": False, "blocked": True, "blocked_labels": blocked_labels, "summary_text": "Blocked known-science replay phase: invalid phase type."}
    if _compact_text(raw.get("schema_version")) != PHASE_SCHEMA_VERSION_V1:
        blocked_labels.append("invalid_schema_version")
    for field in ("phase_id", "case_id", "phase_name", "historical_signal_summary", "initial_ambiguity", "safe_interpretation"):
        if not _compact_text(raw.get(field)):
            blocked_labels.append(f"missing_{field}")
    for field in ("ordinary_explanations_to_pressure", "candidate_hypotheses", "pressure_tests", "calibration_signals", "falsification_signals", "forbidden_interpretations"):
        value = raw.get(field)
        if not isinstance(value, list) or not value:
            blocked_labels.append(f"missing_{field}")
    if not _allowed_selector_outcome(raw.get("expected_selector_outcome")):
        blocked_labels.append("invalid_selector_outcome")
    if not _allowed_selector_outcome(raw.get("expected_internal_next_step")):
        blocked_labels.append("invalid_selector_outcome")
    public_claim_status = _compact_text(raw.get("public_claim_status"))
    if not public_claim_status:
        blocked_labels.append("missing_public_claim_status")
    elif public_claim_status not in ALLOWED_PUBLIC_CLAIM_STATUSES_V1:
        blocked_labels.append("invalid_public_claim_status")
    _validate_authority_status(raw.get("authority_status"), blocked_labels)
    _validate_safe_metadata(raw.get("safe_metadata"), blocked_labels)
    if _first_non_json_safe_path(raw) is not None:
        blocked_labels.append("non_json_safe_result_structure")
    valid = not blocked_labels
    return {
        "schema_version": PHASE_SCHEMA_VERSION_V1,
        "valid": valid,
        "blocked": not valid,
        "blocked_labels": list(dict.fromkeys(blocked_labels)),
        "summary_text": f"Known-science replay phase {_compact_text(raw.get('phase_id'), 'unknown_phase')}: selector={_compact_text(raw.get('expected_selector_outcome'), 'unknown')}",
        "phase_id": _compact_text(raw.get("phase_id")),
        "case_id": _compact_text(raw.get("case_id")),
    }


def validate_known_science_replay_selector_calibration_v1(calibration: Any) -> dict[str, Any]:
    raw = calibration if isinstance(calibration, Mapping) else {}
    blocked_labels: list[str] = []
    if not isinstance(calibration, Mapping):
        blocked_labels.append("invalid_selector_calibration_type")
        return {"schema_version": SELECTOR_CALIBRATION_SCHEMA_VERSION_V1, "valid": False, "blocked": True, "blocked_labels": blocked_labels, "summary_text": "Blocked selector calibration: invalid type."}
    if _compact_text(raw.get("schema_version")) != SELECTOR_CALIBRATION_SCHEMA_VERSION_V1:
        blocked_labels.append("invalid_selector_calibration")
    outcomes = raw.get("selector_outcomes")
    if not isinstance(outcomes, list) or not outcomes:
        blocked_labels.append("missing_selector_outcomes")
    else:
        for outcome in outcomes:
            if not _allowed_selector_outcome(outcome):
                blocked_labels.append("invalid_selector_outcome")
    for field in ("expected_internal_next_steps", "expected_wrong_shortcuts"):
        value = raw.get(field)
        if not isinstance(value, list) or not value:
            blocked_labels.append(f"missing_{field}")
    _validate_authority_status(raw.get("authority_status"), blocked_labels)
    _validate_safe_metadata(raw.get("safe_metadata"), blocked_labels)
    if _first_non_json_safe_path(raw) is not None:
        blocked_labels.append("non_json_safe_result_structure")
    valid = not blocked_labels
    return {
        "schema_version": SELECTOR_CALIBRATION_SCHEMA_VERSION_V1,
        "valid": valid,
        "blocked": not valid,
        "blocked_labels": list(dict.fromkeys(blocked_labels)),
        "summary_text": f"Selector calibration {_compact_text(raw.get('case_id'), 'unknown_case')}: outcomes={', '.join(map(_compact_text, outcomes or [])) or 'none'}",
        "case_id": _compact_text(raw.get("case_id")),
    }


def validate_known_science_replay_component_mapping_v1(mapping: Any) -> dict[str, Any]:
    raw = mapping if isinstance(mapping, Mapping) else {}
    blocked_labels: list[str] = []
    if not isinstance(mapping, Mapping):
        blocked_labels.append("invalid_component_mapping_type")
        return {"schema_version": COMPONENT_MAPPING_SCHEMA_VERSION_V1, "valid": False, "blocked": True, "blocked_labels": blocked_labels, "summary_text": "Blocked component mapping: invalid type."}
    if _compact_text(raw.get("schema_version")) != COMPONENT_MAPPING_SCHEMA_VERSION_V1:
        blocked_labels.append("invalid_component_mapping")
    _validate_component_mapping(raw, blocked_labels)
    if _first_non_json_safe_path(raw) is not None:
        blocked_labels.append("non_json_safe_result_structure")
    valid = not blocked_labels
    return {
        "schema_version": COMPONENT_MAPPING_SCHEMA_VERSION_V1,
        "valid": valid,
        "blocked": not valid,
        "blocked_labels": list(dict.fromkeys(blocked_labels)),
        "summary_text": f"Component mapping {_compact_text(raw.get('case_id'), 'unknown_case')}: components={len(raw.get('component_mappings') or [])}",
        "case_id": _compact_text(raw.get("case_id")),
    }


def build_known_science_replay_case_validation_bundle_v1(case: Any) -> dict[str, Any]:
    raw = case if isinstance(case, Mapping) else {}
    bundle = {
        "case": validate_known_science_replay_case_v1(raw),
        "phases": [validate_known_science_replay_phase_v1(item) for item in (raw.get("replay_phases") or []) if isinstance(item, Mapping)],
        "selector_calibration": validate_known_science_replay_selector_calibration_v1(raw.get("selector_calibration")),
        "component_mapping": validate_known_science_replay_component_mapping_v1(raw.get("component_mapping")),
    }
    return _json_safe(bundle)


def build_known_science_replay_case_summary_bundle_v1(case: Any) -> dict[str, Any]:
    raw = case if isinstance(case, Mapping) else {}
    bundle = {
        "case": summarize_known_science_replay_case_v1(raw),
        "phases": [validate_known_science_replay_phase_v1(item)["summary_text"] for item in (raw.get("replay_phases") or []) if isinstance(item, Mapping)],
        "selector_calibration": validate_known_science_replay_selector_calibration_v1(raw.get("selector_calibration"))["summary_text"],
        "component_mapping": validate_known_science_replay_component_mapping_v1(raw.get("component_mapping"))["summary_text"],
    }
    return _json_safe(bundle)


__all__ = (
    "ALLOWED_SELECTOR_OUTCOMES_V1",
    "ALLOWED_PUBLIC_CLAIM_STATUSES_V1",
    "COMPONENT_MAPPING_SCHEMA_VERSION_V1",
    "KNOWN_REPLAY_COMPONENTS_V1",
    "PHASE_SCHEMA_VERSION_V1",
    "REQUIRED_SAFE_METADATA_FLAGS_V1",
    "SCHEMA_VERSION_V1",
    "SELECTOR_CALIBRATION_SCHEMA_VERSION_V1",
    "build_initial_known_science_replay_examples_v1",
    "build_known_science_replay_case_summary_bundle_v1",
    "build_known_science_replay_case_validation_bundle_v1",
    "build_known_science_replay_case_v1",
    "build_known_science_replay_component_mapping_v1",
    "build_known_science_replay_phase_v1",
    "build_known_science_replay_selector_calibration_v1",
    "summarize_known_science_replay_case_v1",
    "to_known_science_replay_json_safe_v1",
    "validate_known_science_replay_case_v1",
    "validate_known_science_replay_component_mapping_v1",
    "validate_known_science_replay_phase_v1",
    "validate_known_science_replay_selector_calibration_v1",
)
