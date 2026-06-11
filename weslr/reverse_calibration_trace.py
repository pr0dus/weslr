"""WESLR Reverse Calibration Trace Helper V1.

Deterministic, metadata-only helpers for backward mapping from a known outcome
to earlier signal phases, expected next steps, and the reason each step is
preferred over calibration, archive, or claim.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Mapping

SCHEMA_VERSION_V1 = "reverse_calibration_trace_v1"
TRACE_FAMILY_V1 = "reverse_calibration_trace_v1"

ALLOWED_NEXT_STEP_LABELS_V1 = (
    "probe",
    "pressure_test",
    "calibrate",
    "archive",
    "operator_review",
    "blocked_by_safety",
    "watch",
    "not_applicable",
    "needs_repair",
)

_AUTHORITY_FLAGS_V1 = (
    "runtime_authorized",
    "source_ingestion_authorized",
    "public_claim_authorized",
    "final_answer_authority",
    "provider_model_call_authority",
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
)

_AUTHORITY_TEXT_MARKERS_V1 = (
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
    "hidden prompt",
    "private text",
    "protected file",
    "secret",
    "api key",
)

_SAFE_METADATA_KEYS_V1 = (
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
    "trace_family",
)

_KNOWN_OUTCOME_AUTHORITY_KEYS_V1 = (
    *_AUTHORITY_FLAGS_V1,
    "all_authority_flags_false",
    "status",
    "boundary_notes",
)

_AUTHORITY_REQUIRED_FALSE_FLAGS_V1 = _AUTHORITY_FLAGS_V1
_SAFE_METADATA_REQUIRED_TRUE_FLAGS_V1 = tuple(key for key in _SAFE_METADATA_KEYS_V1 if key != "trace_family")


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
    return {
        "runtime_authorized": False,
        "source_ingestion_authorized": False,
        "public_claim_authorized": False,
        "final_answer_authority": False,
        "provider_model_call_authority": False,
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
        "all_authority_flags_false": True,
        "status": "metadata_only",
        "boundary_notes": "metadata-only reverse calibration trace boundary",
    }


def _default_known_outcome_authority_status() -> dict[str, Any]:
    return {
        **_default_authority_status(),
        "boundary_notes": "historical known-outcome metadata boundary",
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
        "trace_family": TRACE_FAMILY_V1,
    }


def _normalize_authority_status(value: Any) -> dict[str, Any]:
    normalized = _default_authority_status()
    if isinstance(value, Mapping):
        normalized.update({key: _json_safe(item) for key, item in value.items()})
    return normalized


def _normalize_known_outcome_authority_status(value: Any) -> dict[str, Any]:
    normalized = _default_known_outcome_authority_status()
    if isinstance(value, Mapping):
        normalized.update({key: _json_safe(item) for key, item in value.items()})
    return normalized


def _normalize_safe_metadata(value: Any) -> dict[str, Any]:
    normalized = _default_safe_metadata()
    if isinstance(value, Mapping):
        normalized.update({key: _json_safe(item) for key, item in value.items()})
    return normalized


def _phase_default_phase_id(data: Mapping[str, Any]) -> str:
    base = _compact_text(data.get("phase_id"))
    if base:
        return base
    phase_name = _compact_text(data.get("phase_name") or data.get("signal_phase") or "phase")
    return phase_name


def build_reverse_calibration_trace_phase_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = _merge_payload(payload, **overrides)
    phase_id = _compact_text(data.get("phase_id"), _phase_default_phase_id(data))
    expected = _compact_text(data.get("expected_forward_next_step"), "not_applicable")
    return {
        "phase_id": phase_id,
        "phase_signal_summary": _compact_text(data.get("phase_signal_summary"), "metadata-only phase summary"),
        "expected_forward_next_step": expected,
        "why_this_step": _compact_text(data.get("why_this_step"), "metadata-only next-step rationale"),
        "why_not_calibrate": _compact_text(data.get("why_not_calibrate"), "calibration would be premature here"),
        "why_not_archive": _compact_text(data.get("why_not_archive"), "the signal still needs a live internal check"),
        "why_not_claim": _compact_text(data.get("why_not_claim"), "public claim authority is not earned"),
        "disconfirming_signal": _compact_text(data.get("disconfirming_signal"), "no disconfirming signal yet"),
        "required_next_evidence": _compact_text(data.get("required_next_evidence"), "more internal evidence is required"),
        "selector_bridge_comparison": _compact_text(
            data.get("selector_bridge_comparison"),
            "bridge comparison remains internal, deterministic, and metadata-only",
        ),
        "mismatch_if_any": _compact_text(data.get("mismatch_if_any"), "none"),
        "calibration_lesson": _compact_text(data.get("calibration_lesson"), "calibrate only when the signal earns it"),
    }


def build_reverse_calibration_trace_packet_v1(payload: Any = None, **overrides: Any) -> dict[str, Any]:
    data = _merge_payload(payload, **overrides)
    phases = data.get("phases")
    return {
        "trace_id": _compact_text(data.get("trace_id"), "reverse_calibration_trace"),
        "source_case_id": _compact_text(data.get("source_case_id"), "unknown_source_case"),
        "known_outcome_summary": _compact_text(
            data.get("known_outcome_summary"),
            "Known outcome recorded as a historical, metadata-only calibration reference.",
        ),
        "known_outcome_authority_status": _normalize_known_outcome_authority_status(data.get("known_outcome_authority_status")),
        "phases": [build_reverse_calibration_trace_phase_v1(item) for item in phases]
        if isinstance(phases, (list, tuple))
        else [],
        "forbidden_interpretations": _json_safe(
            data.get("forbidden_interpretations")
            if isinstance(data.get("forbidden_interpretations"), (list, tuple, set))
            else [
                "public discovery claim",
                "proof claim",
                "final answer authority",
                "benchmark claim",
                "AGI claim",
                "official intelligence claim",
            ]
        ),
        "authority_status": _normalize_authority_status(data.get("authority_status")),
        "safe_metadata": _normalize_safe_metadata(data.get("safe_metadata")),
    }


def validate_reverse_calibration_trace_packet_v1(packet: Any) -> dict[str, Any]:
    blocked_labels: list[str] = []
    if not isinstance(packet, Mapping):
        blocked_labels.append("invalid_packet_type")
        return {
            "schema_version": SCHEMA_VERSION_V1,
            "valid": False,
            "blocked": True,
            "blocked_labels": blocked_labels,
            "validation_posture": "blocked",
            "summary_text": "Blocked reverse calibration trace packet: invalid packet type.",
        }

    raw = packet

    if _compact_text(raw.get("trace_id")) == "":
        blocked_labels.append("missing_trace_id")
    if _compact_text(raw.get("source_case_id")) == "":
        blocked_labels.append("missing_source_case_id")
    if _compact_text(raw.get("known_outcome_summary")) == "":
        blocked_labels.append("missing_known_outcome")
    if not isinstance(raw.get("known_outcome_authority_status"), Mapping):
        blocked_labels.append("missing_known_outcome_authority_status")
    if "phases" not in raw:
        blocked_labels.append("missing_phases")
    elif not isinstance(raw.get("phases"), list):
        blocked_labels.append("non_list_phases")
    elif not raw.get("phases"):
        blocked_labels.append("missing_phases")

    if not isinstance(raw.get("forbidden_interpretations"), list) or not raw.get("forbidden_interpretations"):
        blocked_labels.append("missing_forbidden_interpretations")

    authority_status = raw.get("authority_status")
    if not isinstance(authority_status, Mapping):
        blocked_labels.append("missing_authority_status")
    else:
        for key in authority_status.keys():
            if key not in _KNOWN_OUTCOME_AUTHORITY_KEYS_V1:
                blocked_labels.append(f"unexpected_authority_status_key:{key}")
        for flag in _AUTHORITY_REQUIRED_FALSE_FLAGS_V1:
            if authority_status.get(flag) is True:
                blocked_labels.append(f"unsafe_{flag}")
        if authority_status.get("all_authority_flags_false") is not True:
            blocked_labels.append("unsafe_authority_flags")
        if _compact_text(authority_status.get("status")) != "metadata_only":
            blocked_labels.append("unsafe_authority_status")
        if _compact_text(authority_status.get("boundary_notes")) == "":
            blocked_labels.append("missing_authority_boundary_notes")
        if _contains_text_markers(authority_status, _AUTHORITY_TEXT_MARKERS_V1):
            blocked_labels.append("unsafe_authority_text")

    known_outcome_authority_status = raw.get("known_outcome_authority_status")
    if not isinstance(known_outcome_authority_status, Mapping):
        blocked_labels.append("missing_known_outcome_authority_status")
    else:
        for key in known_outcome_authority_status.keys():
            if key not in _KNOWN_OUTCOME_AUTHORITY_KEYS_V1:
                blocked_labels.append(f"unexpected_known_outcome_authority_status_key:{key}")
        for flag in _AUTHORITY_REQUIRED_FALSE_FLAGS_V1:
            if known_outcome_authority_status.get(flag) is True:
                blocked_labels.append(f"unsafe_known_outcome_{flag}")
        if known_outcome_authority_status.get("all_authority_flags_false") is not True:
            blocked_labels.append("unsafe_known_outcome_authority_flags")
        if _compact_text(known_outcome_authority_status.get("status")) != "metadata_only":
            blocked_labels.append("unsafe_known_outcome_authority_status")
        if _compact_text(known_outcome_authority_status.get("boundary_notes")) == "":
            blocked_labels.append("missing_known_outcome_authority_boundary_notes")
        if _contains_text_markers(known_outcome_authority_status, _AUTHORITY_TEXT_MARKERS_V1):
            blocked_labels.append("unsafe_known_outcome_authority_text")

    safe_metadata = raw.get("safe_metadata")
    if not isinstance(safe_metadata, Mapping):
        blocked_labels.append("missing_safe_metadata")
    else:
        for key in safe_metadata.keys():
            if key not in _SAFE_METADATA_KEYS_V1:
                blocked_labels.append(f"unexpected_safe_metadata_key:{key}")
        for key in _SAFE_METADATA_REQUIRED_TRUE_FLAGS_V1:
            if safe_metadata.get(key) is not True:
                blocked_labels.append(f"unsafe_safe_metadata_{key}")
        if _compact_text(safe_metadata.get("trace_family")) != TRACE_FAMILY_V1:
            blocked_labels.append("unsafe_safe_metadata_trace_family")
        if _contains_text_markers(safe_metadata, _AUTHORITY_TEXT_MARKERS_V1):
            blocked_labels.append("unsafe_safe_metadata_text")

    if _first_non_json_safe_path(raw) is not None:
        blocked_labels.append("non_json_safe_output")

    phases = raw.get("phases") if isinstance(raw.get("phases"), list) else []
    for index, phase in enumerate(phases):
        if not isinstance(phase, Mapping):
            blocked_labels.append(f"invalid_phase_type:{index}")
            continue
        if _compact_text(phase.get("phase_id")) == "":
            blocked_labels.append("missing_phase_id")
        if _compact_text(phase.get("phase_signal_summary")) == "":
            blocked_labels.append("missing_phase_signal_summary")
        if _compact_text(phase.get("expected_forward_next_step")) not in ALLOWED_NEXT_STEP_LABELS_V1:
            blocked_labels.append("invalid_next_step_label")
        if _compact_text(phase.get("why_this_step")) == "":
            blocked_labels.append("missing_why_this_step")
        if _compact_text(phase.get("why_not_calibrate")) == "":
            blocked_labels.append("missing_why_not_calibrate")
        if _compact_text(phase.get("why_not_archive")) == "":
            blocked_labels.append("missing_why_not_archive")
        if _compact_text(phase.get("why_not_claim")) == "":
            blocked_labels.append("missing_why_not_claim")
        if _compact_text(phase.get("disconfirming_signal")) == "":
            blocked_labels.append("missing_disconfirming_signal")
        if _compact_text(phase.get("required_next_evidence")) == "":
            blocked_labels.append("missing_required_next_evidence")
        if _compact_text(phase.get("selector_bridge_comparison")) == "":
            blocked_labels.append("missing_selector_bridge_comparison")
        if _compact_text(phase.get("calibration_lesson")) == "":
            blocked_labels.append("missing_calibration_lesson")
        if _compact_text(phase.get("mismatch_if_any")) == "":
            blocked_labels.append("missing_mismatch_if_any")
        if _contains_text_markers(phase, ("hidden prompt", "private text", "protected file", "secret", "api key")):
            blocked_labels.append("forbidden_hidden_private_protected_marker")

    valid = not blocked_labels
    summary = "Valid reverse calibration trace packet." if valid else "Blocked reverse calibration trace packet: metadata or authority checks failed."
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "valid": valid,
        "blocked": not valid,
        "blocked_labels": blocked_labels,
        "validation_posture": "valid" if valid else "blocked",
        "summary_text": summary,
    }


def summarize_reverse_calibration_trace_packet_v1(packet: Any) -> dict[str, Any]:
    raw = packet if isinstance(packet, Mapping) else {}
    phases = raw.get("phases") if isinstance(raw.get("phases"), list) else []
    next_step_distribution = Counter()
    mismatch_count = 0
    blocked_safety_count = 0
    for phase in phases:
        if not isinstance(phase, Mapping):
            continue
        step = _compact_text(phase.get("expected_forward_next_step"), "unknown")
        next_step_distribution[step] += 1
        mismatch = _compact_text(phase.get("mismatch_if_any"), "none")
        if mismatch and mismatch != "none":
            mismatch_count += 1
        if step == "blocked_by_safety" or "safety" in mismatch.lower():
            blocked_safety_count += 1

    validation = validate_reverse_calibration_trace_packet_v1(raw) if isinstance(raw, Mapping) else {}
    phase_count = len([phase for phase in phases if isinstance(phase, Mapping)])
    trace_id = _compact_text(raw.get("trace_id"), "unknown_trace")
    return {
        "trace_id": trace_id,
        "source_case_id": _compact_text(raw.get("source_case_id"), "unknown_source_case"),
        "phase_count": phase_count,
        "next_step_distribution": dict(sorted(next_step_distribution.items())),
        "mismatch_count": mismatch_count,
        "blocked_safety_count": blocked_safety_count,
        "authority_status": _json_safe(
            raw.get("authority_status") if isinstance(raw.get("authority_status"), Mapping) else _default_authority_status()
        ),
        "known_outcome_authority_status": _json_safe(
            raw.get("known_outcome_authority_status")
            if isinstance(raw.get("known_outcome_authority_status"), Mapping)
            else _default_known_outcome_authority_status()
        ),
        "validation_posture": _compact_text(validation.get("validation_posture"), "unknown"),
        "summary_text": f"Reverse calibration trace {trace_id}: {phase_count} phases, {mismatch_count} mismatches, {blocked_safety_count} safety blocks.",
    }


def to_reverse_calibration_trace_json_safe_v1(packet: Any) -> Any:
    return _json_safe(packet)


def build_initial_reverse_calibration_trace_examples_v1() -> list[dict[str, Any]]:
    pulsar_trace = build_reverse_calibration_trace_packet_v1(
        {
            "trace_id": "pulsar_reverse_calibration_trace",
            "source_case_id": "pulsar_historical_outcome",
            "known_outcome_summary": "Historical astronomy outcome: pulsars were later recognized as real astronomical objects.",
            "known_outcome_authority_status": _default_known_outcome_authority_status(),
            "phases": [
                build_reverse_calibration_trace_phase_v1(
                    {
                        "phase_id": "initial_strange_signal",
                        "phase_signal_summary": "An unusual repeating signal is noticed, but the pattern is still thin and unconfirmed.",
                        "expected_forward_next_step": "probe",
                        "why_this_step": "Probe is the right next step because the signal is real enough to inspect but not yet strong enough to conclude.",
                        "why_not_calibrate": "Calibration would be premature because the system does not yet know what the signal is.",
                        "why_not_archive": "Archiving now would freeze an uncertain observation before it has been tested.",
                        "why_not_claim": "No public claim is earned yet because the signal has not been explained or confirmed.",
                        "disconfirming_signal": "A one-off artifact or obvious noise pattern would weaken the case for further attention.",
                        "required_next_evidence": "A repeatable observation path and a cleaner signal record are needed next.",
                        "selector_bridge_comparison": "Matches the bridge pattern that differentiates safe probe from premature calibration or claim.",
                        "mismatch_if_any": "none",
                        "calibration_lesson": "Start with probe when a signal is intriguing but still under-described.",
                    }
                ),
                build_reverse_calibration_trace_phase_v1(
                    {
                        "phase_id": "repeated_precise_signal",
                        "phase_signal_summary": "The signal repeats with enough precision to justify controlled pressure against ordinary explanations.",
                        "expected_forward_next_step": "pressure_test",
                        "why_this_step": "Pressure test is right because repetition makes alternative explanations worth challenging.",
                        "why_not_calibrate": "Calibration is still too early because the signal has not yet been separated from competing explanations.",
                        "why_not_archive": "Archiving would lose the chance to test a potentially structured signal.",
                        "why_not_claim": "Public claim remains blocked because confirmation is still incomplete.",
                        "disconfirming_signal": "Loss of repeatability or an obvious source artifact would reduce the need for pressure testing.",
                        "required_next_evidence": "A counterexample check or stronger pattern discrimination is needed.",
                        "selector_bridge_comparison": "The bridge comparison now favors pressure_test over probe because the pattern has earned a stronger challenge.",
                        "mismatch_if_any": "none",
                        "calibration_lesson": "Repeatability should move the system from observation into pressure testing, not into claims.",
                    }
                ),
                build_reverse_calibration_trace_phase_v1(
                    {
                        "phase_id": "ordinary_explanations_weakened",
                        "phase_signal_summary": "Ordinary explanations are still available, but they are weakening as the evidence accumulates.",
                        "expected_forward_next_step": "calibrate",
                        "why_this_step": "Calibration is appropriate now because confidence posture and internal expectations need adjustment.",
                        "why_not_calibrate": "Not applicable here because calibrate is the correct forward step once the ordinary explanations are weakening.",
                        "why_not_archive": "Archiving would prematurely close a case that is still teaching the system how to read the signal.",
                        "why_not_claim": "A claim would still outrun external confirmation and should remain blocked.",
                        "disconfirming_signal": "A robust ordinary explanation that explains away the pattern would remove the need to calibrate further.",
                        "required_next_evidence": "A stable internal comparison plus a clear boundary on what the signal does and does not support.",
                        "selector_bridge_comparison": "The bridge comparison differentiates calibration from archive because the system is adjusting posture, not closing the file.",
                        "mismatch_if_any": "none",
                        "calibration_lesson": "Calibrate only after the signal has earned a change in confidence posture.",
                    }
                ),
                build_reverse_calibration_trace_phase_v1(
                    {
                        "phase_id": "external_confirmation",
                        "phase_signal_summary": "External confirmation arrives and the case is now suitable for retention and policy-compliant review.",
                        "expected_forward_next_step": "archive",
                        "why_this_step": "Archive is now reasonable because the outcome has become part of the known record.",
                        "why_not_calibrate": "Further calibration is no longer the main task once the outcome is established.",
                        "why_not_archive": "If policy requires a human policy review, operator_review may be preferred before archive; otherwise archive is fine.",
                        "why_not_claim": "Public claim authority is still separate from internal archival readiness.",
                        "disconfirming_signal": "If the confirmation is later challenged, the record should be reopened rather than treated as settled.",
                        "required_next_evidence": "A stable documented confirmation and policy-compliant handling are needed.",
                        "selector_bridge_comparison": "This phase sits at the bridge boundary between confirmed record retention and optional operator review.",
                        "mismatch_if_any": "none",
                        "calibration_lesson": "Confirmation shifts the next step from exploration into retention or review.",
                    }
                ),
                build_reverse_calibration_trace_phase_v1(
                    {
                        "phase_id": "unsafe_public_claim_attempt",
                        "phase_signal_summary": "A live public-claim push appears before authority is earned and before the boundary is cleared.",
                        "expected_forward_next_step": "blocked_by_safety",
                        "why_this_step": "Block the step because public-claim authority is not available.",
                        "why_not_calibrate": "Calibration would not fix a safety violation; the issue is authority, not confidence.",
                        "why_not_archive": "Archiving would hide a live boundary problem instead of stopping it.",
                        "why_not_claim": "Claiming would violate the boundary because the outcome is not authorized for public export.",
                        "disconfirming_signal": "Any request for live public claim, proof, or final-answer authority is disconfirming and must stop the step.",
                        "required_next_evidence": "Operator review or a safe internal-only reformulation is required before any further progress.",
                        "selector_bridge_comparison": "The bridge comparison matches the safety-blocked branch and keeps the case out of public-claim authority.",
                        "mismatch_if_any": "safety_blocked",
                        "calibration_lesson": "Safety boundaries outrank all forward steps when public-claim pressure appears.",
                    }
                ),
            ],
            "forbidden_interpretations": [
                "public discovery claim",
                "proof claim",
                "final answer authority",
                "benchmark claim",
                "AGI claim",
                "official intelligence claim",
            ],
            "authority_status": _default_authority_status(),
            "safe_metadata": _default_safe_metadata(),
        }
    )
    return [pulsar_trace]
