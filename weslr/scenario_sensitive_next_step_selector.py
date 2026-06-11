"""WESLR Scenario-Sensitive Next-Step Selector V1.

Deterministic, metadata-only selector for internal next-step recommendations.
It reads safe scenario-set metadata and returns a scenario-sensitive next step
without executing anything, wiring runtime, or making public claims.
"""

from __future__ import annotations

from copy import deepcopy
from hashlib import sha256
from typing import Any, Mapping

from weslr.recursive_research_loop_findings_digest import (
    build_recursive_research_loop_findings_digest_v1,
    summarize_recursive_research_loop_findings_digest_v1,
    to_recursive_research_loop_findings_digest_json_safe_v1,
)
from weslr.recursive_research_loop_scenario_set import run_recursive_research_loop_scenario_set_v1

SCHEMA_VERSION_V1 = "scenario_sensitive_next_step_selector_v1"
SELECTOR_ID_V1 = "scenario_sensitive_next_step_selector_v1"
ALLOWED_NEXT_STEP_LABELS_V1 = (
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
SCENARIO_FAMILY_TO_NEXT_STEP_V1 = {
    "ambiguous_pattern_signal": "probe",
    "contradictory_signal": "pressure_test",
    "weak_signal_noise": "watch",
    "cross_domain_resonance_signal": "probe",
    "pressure_test_candidate": "pressure_test",
    "calibration_needed_signal": "calibrate",
    "blocked_public_claim_signal": "operator_review",
    "archive_low_value_signal": "archive",
}
FORBIDDEN_TEXT_MARKERS_V1 = (
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
    "discovery",
    "proof",
    "breakthrough",
    "scientific result",
    "validated mechanism",
    "agi evidence",
    "intelligence proof",
    "sentience",
    "consciousness",
    "public claim",
)
_REQUIRED_SAFE_METADATA_FLAGS_V1 = (
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


def _contains_forbidden_text(value: Any) -> bool:
    if isinstance(value, Mapping):
        return any(_contains_forbidden_text(item) for item in value.values())
    if isinstance(value, (list, tuple, set)):
        return any(_contains_forbidden_text(item) for item in value)
    if not isinstance(value, str):
        return False
    lowered = value.lower()
    return any(marker in lowered for marker in FORBIDDEN_TEXT_MARKERS_V1)


def _default_denied_authority() -> dict[str, Any]:
    return {
        "runtime_action_authorized": False,
        "storage_write_authorized": False,
        "memory_mutation_authorized": False,
        "project_mutation_authorized": False,
        "behavior_promotion_authorized": False,
        "public_claim_authorized": False,
        "final_answer_authority": False,
        "provider_model_call_authority": False,
        "retrieval_tool_authority": False,
        "all_authority_flags_false": True,
        "status": "metadata_only",
        "boundary_notes": "selector: no runtime, persistence, or public-export authority",
    }


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
        "retrieval_tool_authority": False,
        "all_authority_flags_false": True,
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
        "selector_family": "scenario_sensitive_next_step_selector",
    }


def _load_scenario_set_result(payload: Mapping[str, Any]) -> dict[str, Any]:
    scenario_set_result = payload.get("scenario_set_result")
    if isinstance(scenario_set_result, Mapping):
        return to_scenario_sensitive_next_step_json_safe_v1(scenario_set_result)
    return to_scenario_sensitive_next_step_json_safe_v1(run_recursive_research_loop_scenario_set_v1())


def _load_findings_digest(payload: Mapping[str, Any], scenario_set_result: Mapping[str, Any]) -> dict[str, Any]:
    digest = payload.get("findings_digest")
    if isinstance(digest, Mapping):
        return to_scenario_sensitive_next_step_json_safe_v1(digest)
    return build_recursive_research_loop_findings_digest_v1(
        {
            "scenario_set_result": scenario_set_result,
            "source_run_id": _compact_text(scenario_set_result.get("scenario_set_id"), "recursive_research_loop_scenario_set_v1"),
            "source_commit": _compact_text(payload.get("source_commit") or "unknown-source-commit"),
        }
    )


def _scenario_result_for_family(scenario_set_result: Mapping[str, Any], scenario_family: str) -> dict[str, Any]:
    scenario_results = scenario_set_result.get("scenario_results") if isinstance(scenario_set_result.get("scenario_results"), list) else []
    for item in scenario_results:
        if isinstance(item, Mapping) and _compact_text(item.get("scenario_family")) == scenario_family:
            return dict(item)
    scenarios = scenario_set_result.get("scenarios") if isinstance(scenario_set_result.get("scenarios"), list) else []
    for item in scenarios:
        if isinstance(item, Mapping) and _compact_text(item.get("scenario_family")) == scenario_family:
            return dict(item)
    return {}


def _validation_signal_from_source(payload: Mapping[str, Any], scenario_result: Mapping[str, Any], digest: Mapping[str, Any]) -> dict[str, Any]:
    scenario_validation = scenario_result.get("scenario_validation") if isinstance(scenario_result.get("scenario_validation"), Mapping) else {}
    dry_run_validation = scenario_result.get("dry_run_validation") if isinstance(scenario_result.get("dry_run_validation"), Mapping) else {}
    digest_validation = digest.get("validation") if isinstance(digest.get("validation"), Mapping) else {}
    scenario_valid = bool(scenario_validation.get("valid", dry_run_validation.get("valid", True)))
    digest_valid = bool(digest_validation.get("valid", True))
    source_valid = bool(payload.get("source_valid", True))
    overall_valid = scenario_valid and digest_valid and source_valid
    blocked_labels = []
    for label_list in (scenario_validation.get("blocked_labels"), dry_run_validation.get("blocked_labels"), digest_validation.get("blocked_labels")):
        if isinstance(label_list, list):
            blocked_labels.extend(_compact_text(item) for item in label_list if _compact_text(item))
    return {
        "scenario_valid": scenario_valid,
        "digest_valid": digest_valid,
        "source_valid": source_valid,
        "valid": overall_valid,
        "blocked_labels": list(dict.fromkeys(blocked_labels)),
    }


def _family_signal_for_packet(scenario_family: str, scenario_result: Mapping[str, Any], digest: Mapping[str, Any]) -> str:
    stage_summary = _compact_text(scenario_result.get("stage_summary"))
    if stage_summary:
        return stage_summary
    family_note = _compact_text(scenario_result.get("expected_next_step_family"), "")
    if family_note:
        return f"family={scenario_family}; expected_next={family_note}"
    cross_patterns = digest.get("cross_family_patterns") if isinstance(digest.get("cross_family_patterns"), list) else []
    for item in cross_patterns:
        text = _compact_text(item)
        if text:
            return text
    return f"family={scenario_family}; metadata-only selector input"


def _gap_signal_for_packet(scenario_result: Mapping[str, Any], digest: Mapping[str, Any]) -> str:
    gap_summary = _compact_text(scenario_result.get("gap_summary"))
    if gap_summary:
        return gap_summary
    limitations = digest.get("current_limitations") if isinstance(digest.get("current_limitations"), list) else []
    for item in limitations:
        text = _compact_text(item)
        if text:
            return text
    return "no explicit gap signal"


def _safety_signal_for_packet(scenario_result: Mapping[str, Any], digest: Mapping[str, Any]) -> str:
    safety_summary = _compact_text(scenario_result.get("safety_summary"))
    if safety_summary:
        return safety_summary
    safety_status = digest.get("authority_status") if isinstance(digest.get("authority_status"), Mapping) else _default_authority_status()
    flags = ", ".join(f"{key}={bool(value)}" for key, value in sorted(safety_status.items(), key=lambda item: item[0]))
    return f"Safety authority flags: {flags}."


def _blocked_reasons_for_packet(
    scenario_family: str,
    validation_signal: Mapping[str, Any],
    authority_status: Mapping[str, Any],
    safe_metadata: Mapping[str, Any],
    gap_signal: str,
) -> list[str]:
    reasons: list[str] = []
    if not validation_signal.get("valid", False):
        reasons.append("validation_failed")
        for label in validation_signal.get("blocked_labels", []):
            if label not in reasons:
                reasons.append(_compact_text(label))
    for field in ("runtime_action_authorized", "storage_write_authorized", "memory_mutation_authorized", "project_mutation_authorized", "behavior_promotion_authorized", "public_claim_authorized", "final_answer_authority", "provider_model_call_authority", "retrieval_tool_authority"):
        if bool(authority_status.get(field)):
            reasons.append(f"unsafe_{field}")
    if safe_metadata.get("safe") is not True:
        reasons.append("unsafe_safe_metadata")
    if _contains_forbidden_text(gap_signal):
        reasons.append("forbidden_gap_signal_text")
    if scenario_family == "blocked_public_claim_signal":
        reasons.append("family_requires_operator_review")
    return list(dict.fromkeys(reasons))


def _selection_reason_for_next_step(next_step: str, scenario_family: str, gap_signal: str, validation_signal: Mapping[str, Any]) -> str:
    if next_step == "needs_repair":
        return "validation failed; selector recommends repair before next-step selection"
    if next_step == "blocked":
        return "authority or safety state is unsafe; selector stays blocked"
    if scenario_family == "ambiguous_pattern_signal":
        return "ambiguous pattern signal maps to probe"
    if scenario_family == "contradictory_signal":
        return "contradictory signal maps to pressure_test"
    if scenario_family == "weak_signal_noise":
        if "low value" in gap_signal.lower() or "archive" in gap_signal.lower():
            return "weak signal with low-value gap maps to archive"
        return "weak signal noise remains watch-only"
    if scenario_family == "cross_domain_resonance_signal":
        return "cross-domain resonance maps to probe"
    if scenario_family == "pressure_test_candidate":
        return "pressure-test candidate maps to pressure_test"
    if scenario_family == "calibration_needed_signal":
        return "calibration-needed signal maps to calibrate"
    if scenario_family == "blocked_public_claim_signal":
        return "blocked-output pressure stays under operator review"
    if scenario_family == "archive_low_value_signal":
        return "low-value signal maps to archive"
    if next_step == "unknown":
        return "unknown family stays internally ambiguous; operator review remains available"
    return f"selector chose {next_step} from metadata-only family cues"


def _selection_confidence_for_next_step(next_step: str) -> float:
    return {
        "probe": 0.82,
        "pressure_test": 0.92,
        "calibrate": 0.96,
        "operator_review": 0.9,
        "archive": 0.78,
        "watch": 0.62,
        "blocked": 0.98,
        "needs_repair": 1.0,
        "unknown": 0.34,
    }.get(next_step, 0.5)


def build_scenario_sensitive_next_step_input_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = _merge_payload(payload, **overrides)
    scenario_set_result = _load_scenario_set_result(data)
    digest = _load_findings_digest(data, scenario_set_result)
    scenario_family = _compact_text(data.get("scenario_family"))
    if not scenario_family:
        scenario_family = _compact_text(data.get("scenario_result", {}).get("scenario_family")) if isinstance(data.get("scenario_result"), Mapping) else ""
    if not scenario_family:
        scenario_family = _compact_text(data.get("scenario_family") or data.get("family") or "unknown")
    scenario_result = data.get("scenario_result") if isinstance(data.get("scenario_result"), Mapping) else _scenario_result_for_family(scenario_set_result, scenario_family)
    if not scenario_result and scenario_family in SCENARIO_FAMILY_TO_NEXT_STEP_V1:
        scenario_result = {
            "scenario_family": scenario_family,
            "completion_status": data.get("completion_status", "completed"),
            "recommended_next_internal_step": data.get("input_next_step", "calibrate"),
            "stage_summary": data.get("stage_summary", "metadata-only selector input"),
            "safety_summary": data.get("safety_summary", "Safety authority flags unavailable."),
            "gap_summary": data.get("gap_summary", "no explicit gap signal"),
        }
    input_next_step = _compact_text(
        data.get("input_next_step")
        or scenario_result.get("recommended_next_internal_step")
        or (scenario_set_result.get("next_step_distribution") or {}).get("calibrate")
        and "calibrate"
        or "calibrate"
    )
    if not input_next_step:
        input_next_step = "calibrate"
    validation_signal = data.get("validation_signal") if isinstance(data.get("validation_signal"), Mapping) else _validation_signal_from_source(data, scenario_result, digest)
    safe_metadata = _json_safe(data.get("safe_metadata") or digest.get("safe_metadata") or _default_safe_metadata())
    authority_status = _json_safe(data.get("authority_status") or digest.get("authority_status") or _default_authority_status())
    denied_authority = _json_safe(data.get("denied_authority") or digest.get("denied_authority") or _default_denied_authority())
    family_signal = _compact_text(data.get("family_signal") or _family_signal_for_packet(scenario_family, scenario_result, digest))
    gap_signal = _compact_text(data.get("gap_signal") or _gap_signal_for_packet(scenario_result, digest))
    safety_signal = _compact_text(data.get("safety_signal") or _safety_signal_for_packet(scenario_result, digest))
    blocked_reasons = list(data.get("blocked_reasons") or _blocked_reasons_for_packet(scenario_family, validation_signal, authority_status, safe_metadata, gap_signal))
    operator_notes = list(data.get("operator_notes") or [])
    source_run_id = _compact_text(data.get("source_run_id") or scenario_set_result.get("scenario_set_id") or digest.get("source_run_id") or "recursive_research_loop_scenario_set_v1")
    source_commit = _compact_text(data.get("source_commit") or digest.get("source_commit") or "unknown-source-commit")
    packet = {
        "schema_version": SCHEMA_VERSION_V1,
        "selector_id": _compact_text(data.get("selector_id") or SELECTOR_ID_V1),
        "source_run_id": source_run_id,
        "source_commit": source_commit,
        "scenario_family": scenario_family,
        "input_next_step": input_next_step,
        "selected_next_step": _compact_text(data.get("selected_next_step") or ""),
        "selection_reason": _compact_text(data.get("selection_reason") or ""),
        "selection_confidence": float(data.get("selection_confidence") if isinstance(data.get("selection_confidence"), (int, float)) else 0.0),
        "family_signal": family_signal,
        "gap_signal": gap_signal,
        "safety_signal": safety_signal,
        "validation_signal": _json_safe(validation_signal),
        "blocked_reasons": _json_safe(blocked_reasons),
        "operator_notes": _json_safe(operator_notes),
        "denied_authority": denied_authority,
        "authority_status": authority_status,
        "safe_metadata": safe_metadata,
        "scenario_completion_status": _compact_text(scenario_result.get("completion_status")),
        "scenario_validation_signal": _json_safe(scenario_result.get("scenario_validation") or scenario_result.get("dry_run_validation") or {}),
        "digest_summary": _compact_text(digest.get("summary_text") or summarize_recursive_research_loop_findings_digest_v1(digest)),
    }
    packet["selected_next_step"] = _compact_text(packet["selected_next_step"]) or select_scenario_sensitive_next_step_v1(packet)
    if not _compact_text(packet["selection_reason"]):
        packet["selection_reason"] = _selection_reason_for_next_step(packet["selected_next_step"], scenario_family, gap_signal, validation_signal)
    if not isinstance(packet["selection_confidence"], float) or packet["selection_confidence"] <= 0:
        packet["selection_confidence"] = _selection_confidence_for_next_step(packet["selected_next_step"])
    return _json_safe(packet)


def select_scenario_sensitive_next_step_v1(packet: Any) -> str:
    data = packet if isinstance(packet, Mapping) else build_scenario_sensitive_next_step_input_v1(packet)
    if not isinstance(data, Mapping):
        return "needs_repair"

    scenario_family = _compact_text(data.get("scenario_family"), "unknown")
    validation_signal = data.get("validation_signal") if isinstance(data.get("validation_signal"), Mapping) else {}
    authority_status = data.get("authority_status") if isinstance(data.get("authority_status"), Mapping) else _default_authority_status()
    denied_authority = data.get("denied_authority") if isinstance(data.get("denied_authority"), Mapping) else _default_denied_authority()
    safe_metadata = data.get("safe_metadata") if isinstance(data.get("safe_metadata"), Mapping) else _default_safe_metadata()
    gap_signal = _compact_text(data.get("gap_signal"))
    input_next_step = _compact_text(data.get("input_next_step"), "calibrate")

    validation_valid = bool(validation_signal.get("valid", True))
    unsafe_authority = any(bool(authority_status.get(field)) for field in (
        "runtime_action_authorized",
        "storage_write_authorized",
        "memory_mutation_authorized",
        "project_mutation_authorized",
        "behavior_promotion_authorized",
        "public_claim_authorized",
        "final_answer_authority",
        "provider_model_call_authority",
        "retrieval_tool_authority",
    )) or any(bool(denied_authority.get(field)) for field in (
        "runtime_action_authorized",
        "storage_write_authorized",
        "memory_mutation_authorized",
        "project_mutation_authorized",
        "behavior_promotion_authority",
        "public_claim_authorized",
        "final_answer_authority",
        "provider_model_call_authority",
        "retrieval_tool_authority",
    ))
    if not validation_valid:
        return "needs_repair"
    if safe_metadata.get("safe") is not True or unsafe_authority:
        return "blocked"

    if scenario_family == "ambiguous_pattern_signal":
        return "probe"
    if scenario_family == "contradictory_signal":
        return "pressure_test"
    if scenario_family == "weak_signal_noise":
        if "low value" in gap_signal.lower() or "archive" in gap_signal.lower():
            return "archive"
        return "watch"
    if scenario_family == "cross_domain_resonance_signal":
        return "probe"
    if scenario_family == "pressure_test_candidate":
        return "pressure_test"
    if scenario_family == "calibration_needed_signal":
        return "calibrate"
    if scenario_family == "blocked_public_claim_signal":
        if "blocked" in gap_signal.lower() or "operator" in gap_signal.lower():
            return "operator_review"
        return "blocked"
    if scenario_family == "archive_low_value_signal":
        return "archive"
    if scenario_family == "unknown" or not scenario_family:
        if "review" in gap_signal.lower():
            return "operator_review"
        return "unknown"
    if scenario_family not in SCENARIO_FAMILY_TO_NEXT_STEP_V1:
        if "review" in gap_signal.lower():
            return "operator_review"
        return "unknown"
    if input_next_step in ALLOWED_NEXT_STEP_LABELS_V1:
        return input_next_step
    return "operator_review"


def build_scenario_sensitive_next_step_packet_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = _merge_payload(payload, **overrides)
    normalized = build_scenario_sensitive_next_step_input_v1(data)
    selected_next_step = select_scenario_sensitive_next_step_v1(normalized)
    blocked_reasons = list(normalized.get("blocked_reasons") or [])
    validation_signal = normalized.get("validation_signal") if isinstance(normalized.get("validation_signal"), Mapping) else {}
    scenario_family = _compact_text(normalized.get("scenario_family"), "unknown")
    gap_signal = _compact_text(normalized.get("gap_signal"))
    reason = _compact_text(data.get("selection_reason")) or _selection_reason_for_next_step(selected_next_step, scenario_family, gap_signal, validation_signal)
    confidence = data.get("selection_confidence")
    if not isinstance(confidence, (int, float)) or float(confidence) <= 0:
        confidence = _selection_confidence_for_next_step(selected_next_step)
    packet = {
        "schema_version": SCHEMA_VERSION_V1,
        "selector_id": _compact_text(normalized.get("selector_id") or SELECTOR_ID_V1),
        "source_run_id": _compact_text(normalized.get("source_run_id") or "recursive_research_loop_scenario_set_v1"),
        "scenario_family": scenario_family,
        "input_next_step": _compact_text(normalized.get("input_next_step") or "calibrate"),
        "selected_next_step": selected_next_step,
        "selection_reason": reason,
        "selection_confidence": float(confidence),
        "family_signal": _compact_text(normalized.get("family_signal") or ""),
        "gap_signal": gap_signal,
        "safety_signal": _compact_text(normalized.get("safety_signal") or ""),
        "validation_signal": _json_safe(validation_signal),
        "blocked_reasons": _json_safe(blocked_reasons),
        "operator_notes": _json_safe(normalized.get("operator_notes") or []),
        "denied_authority": _json_safe(normalized.get("denied_authority") or _default_denied_authority()),
        "authority_status": _json_safe(normalized.get("authority_status") or _default_authority_status()),
        "safe_metadata": _json_safe(normalized.get("safe_metadata") or _default_safe_metadata()),
        "source_commit": _compact_text(normalized.get("source_commit") or "unknown-source-commit"),
        "digest_summary": _compact_text(normalized.get("digest_summary") or ""),
        "scenario_completion_status": _compact_text(normalized.get("scenario_completion_status") or ""),
    }
    return _json_safe(packet)


def validate_scenario_sensitive_next_step_packet_v1(packet: Any) -> dict[str, Any]:
    raw = packet if isinstance(packet, Mapping) else {}
    blocked_labels: list[str] = []

    if not isinstance(packet, Mapping):
        blocked_labels.append("invalid_packet_type")
        return {
            "schema_version": SCHEMA_VERSION_V1,
            "valid": False,
            "blocked": True,
            "blocked_labels": blocked_labels,
            "summary_text": "Blocked scenario-sensitive next-step packet: invalid packet type.",
        }

    if _compact_text(raw.get("schema_version")) != SCHEMA_VERSION_V1:
        blocked_labels.append("invalid_schema_version")
    if not _compact_text(raw.get("selector_id")):
        blocked_labels.append("missing_selector_id")
    if not _compact_text(raw.get("scenario_family")):
        blocked_labels.append("missing_scenario_family")
    if not _compact_text(raw.get("selected_next_step")):
        blocked_labels.append("missing_selected_next_step")
    elif _compact_text(raw.get("selected_next_step")) not in ALLOWED_NEXT_STEP_LABELS_V1:
        blocked_labels.append("invalid_selected_next_step")
    if not _compact_text(raw.get("selection_reason")):
        blocked_labels.append("missing_selection_reason")
    if not isinstance(raw.get("selection_confidence"), (int, float)):
        blocked_labels.append("invalid_selection_confidence")
    elif not 0 <= float(raw.get("selection_confidence")) <= 1:
        blocked_labels.append("invalid_selection_confidence")
    if not _compact_text(raw.get("source_run_id")):
        blocked_labels.append("missing_source_run_id")

    for field in ("family_signal", "gap_signal", "safety_signal", "selection_reason", "digest_summary", "scenario_completion_status"):
        if _contains_forbidden_text(raw.get(field)):
            blocked_labels.append("forbidden_claim_language")
    if _contains_forbidden_text(raw.get("operator_notes")):
        blocked_labels.append("forbidden_claim_language")
    if _contains_forbidden_text(raw):
        blocked_labels.append("forbidden_claim_language")

    validation_signal = raw.get("validation_signal") if isinstance(raw.get("validation_signal"), Mapping) else {}
    if not isinstance(validation_signal, Mapping):
        blocked_labels.append("invalid_validation_signal")
    elif validation_signal.get("valid") is not True and _compact_text(raw.get("selected_next_step")) != "needs_repair":
        blocked_labels.append("validation_inconsistent_with_selected_next_step")

    authority_status = raw.get("authority_status")
    if not isinstance(authority_status, Mapping):
        blocked_labels.append("missing_authority_status")
    else:
        for key, value in authority_status.items():
            if key == "all_authority_flags_false":
                continue
            if bool(value):
                blocked_labels.append(f"unsafe_{key}")
        if authority_status.get("all_authority_flags_false") is not True:
            blocked_labels.append("unsafe_authority_status")

    denied_authority = raw.get("denied_authority")
    if not isinstance(denied_authority, Mapping):
        blocked_labels.append("missing_denied_authority")
    else:
        if _contains_forbidden_text(denied_authority):
            blocked_labels.append("unsafe_denied_authority")
        for key, value in denied_authority.items():
            if key in {"status", "boundary_notes", "all_authority_flags_false"}:
                continue
            if bool(value):
                blocked_labels.append(f"granted_{key}")

    safe_metadata = raw.get("safe_metadata")
    if not isinstance(safe_metadata, Mapping):
        blocked_labels.append("missing_safe_metadata")
    else:
        for field in _REQUIRED_SAFE_METADATA_FLAGS_V1:
            if safe_metadata.get(field) is not True:
                blocked_labels.append(f"unsafe_safe_metadata_{field}")
        if _contains_forbidden_text(safe_metadata):
            blocked_labels.append("forbidden_claim_language")

    if _first_non_json_safe_path(raw) is not None:
        blocked_labels.append("non_json_safe_result_structure")

    valid = not blocked_labels
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "valid": valid,
        "blocked": not valid,
        "blocked_labels": list(dict.fromkeys(blocked_labels)),
        "summary_text": summarize_scenario_sensitive_next_step_packet_v1(raw),
        "selector_id": _compact_text(raw.get("selector_id")),
        "scenario_family": _compact_text(raw.get("scenario_family")),
        "selected_next_step": _compact_text(raw.get("selected_next_step")),
    }


def summarize_scenario_sensitive_next_step_packet_v1(packet: Any) -> dict[str, Any]:
    raw = packet if isinstance(packet, Mapping) else {}
    return {
        "summary_type": SCHEMA_VERSION_V1,
        "selector_id": _compact_text(raw.get("selector_id"), SELECTOR_ID_V1),
        "scenario_family": _compact_text(raw.get("scenario_family"), "unknown"),
        "input_next_step": _compact_text(raw.get("input_next_step"), "unknown"),
        "selected_next_step": _compact_text(raw.get("selected_next_step"), "unknown"),
        "selection_confidence": float(raw.get("selection_confidence") or 0.0) if isinstance(raw.get("selection_confidence"), (int, float)) else 0.0,
        "blocked": bool(raw.get("selected_next_step") in {"blocked", "needs_repair"}),
        "blocked_reasons": list(raw.get("blocked_reasons") or []),
        "summary_text": (
            f"Scenario-sensitive selector { _compact_text(raw.get('selector_id'), SELECTOR_ID_V1) }: "
            f"family={_compact_text(raw.get('scenario_family'), 'unknown')}; "
            f"input={_compact_text(raw.get('input_next_step'), 'unknown')}; "
            f"selected={_compact_text(raw.get('selected_next_step'), 'unknown')}; "
            f"confidence={float(raw.get('selection_confidence') or 0.0) if isinstance(raw.get('selection_confidence'), (int, float)) else 0.0}"
        ),
    }


def to_scenario_sensitive_next_step_json_safe_v1(packet: Any) -> dict[str, Any]:
    return _json_safe(packet if isinstance(packet, Mapping) else {})


def build_initial_scenario_sensitive_next_step_examples_v1() -> tuple[dict[str, Any], ...]:
    scenario_set_result = run_recursive_research_loop_scenario_set_v1()
    digest = build_recursive_research_loop_findings_digest_v1(
        {
            "scenario_set_result": scenario_set_result,
            "source_run_id": scenario_set_result["scenario_set_id"],
            "source_commit": "c94aadddd7a0f37d20ddf7cb1f7a02c41e73902b",
        }
    )
    examples: list[dict[str, Any]] = []
    for family in (
        "ambiguous_pattern_signal",
        "contradictory_signal",
        "weak_signal_noise",
        "cross_domain_resonance_signal",
        "pressure_test_candidate",
        "calibration_needed_signal",
        "blocked_public_claim_signal",
        "archive_low_value_signal",
    ):
        scenario_result = _scenario_result_for_family(scenario_set_result, family)
        examples.append(
            build_scenario_sensitive_next_step_packet_v1(
                {
                    "scenario_set_result": scenario_set_result,
                    "findings_digest": digest,
                    "scenario_result": scenario_result,
                    "scenario_family": family,
                    "source_run_id": scenario_set_result["scenario_set_id"],
                    "source_commit": "c94aadddd7a0f37d20ddf7cb1f7a02c41e73902b",
                }
            )
        )
    return tuple(examples)


__all__ = (
    "ALLOWED_NEXT_STEP_LABELS_V1",
    "SCHEMA_VERSION_V1",
    "SELECTOR_ID_V1",
    "build_initial_scenario_sensitive_next_step_examples_v1",
    "build_scenario_sensitive_next_step_input_v1",
    "build_scenario_sensitive_next_step_packet_v1",
    "select_scenario_sensitive_next_step_v1",
    "summarize_scenario_sensitive_next_step_packet_v1",
    "to_scenario_sensitive_next_step_json_safe_v1",
    "validate_scenario_sensitive_next_step_packet_v1",
)
