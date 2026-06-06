"""Metadata-only helpers for WESLR workflow/report integrity red-zone detection.

This module is pure, deterministic, JSON-safe, and fail-closed. It classifies
workflow evidence packets and never shells out, mutates repo state, or performs
runtime/action authority.
"""

from __future__ import annotations

import copy
from typing import Any, Mapping

SCHEMA_VERSION_V1 = "workflow_integrity_red_zone_v1"

ALLOWED_WORKFLOW_INTEGRITY_ZONES_V1 = (
    "green_zone_ready",
    "yellow_zone_needs_note",
    "red_zone_blocked",
    "red_zone_reconciled_ready",
)

PROTECTED_FILES_V1 = (
    "weslr/chat_responder.py",
    "weslr/main.py",
    "main.py",
    "dialogue.py",
    "chat_ui.py",
)

REQUIRED_PACKET_FIELDS_V1 = (
    "schema_version",
    "lane_name",
    "start_head",
    "final_head",
    "reported_files",
    "reported_created_or_changed_files",
    "reported_committed_files",
    "reported_final_judgment",
    "reported_recommended_next_lane",
    "tracked_files",
    "untracked_files",
    "staged_files",
    "diff_name_only",
    "diff_stat",
    "cached_diff_name_only",
    "recent_log_entries",
    "ls_files_results",
    "validation_results",
    "release_gate_result",
    "release_check_result",
    "protected_file_status",
    "unrelated_untracked_drift",
    "reconciliation_notes",
    "zone",
    "red_zone_reasons",
    "yellow_zone_notes",
    "safe_metadata",
)


def _json_safe(value: Any) -> Any:
    value = copy.deepcopy(value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in sorted(value.items(), key=lambda item: str(item[0]))}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return _json_safe(value.to_dict())
    if hasattr(value, "__dict__"):
        return _json_safe(vars(value))
    return repr(value)


def to_workflow_integrity_json_safe_v1(value: Any) -> Any:
    return _json_safe(value)


def _default_reported_drift_v1() -> dict[str, Any]:
    return {"explicitly_marked_unrelated": False, "paths": [], "notes": []}


def build_workflow_integrity_evidence_packet_v1(**overrides: Any) -> dict[str, Any]:
    packet = {
        "schema_version": SCHEMA_VERSION_V1,
        "lane_name": "",
        "start_head": "",
        "final_head": "",
        "reported_files": [],
        "reported_created_or_changed_files": [],
        "reported_committed_files": [],
        "reported_final_judgment": "",
        "reported_recommended_next_lane": "",
        "tracked_files": [],
        "untracked_files": [],
        "staged_files": [],
        "diff_name_only": [],
        "diff_stat": [],
        "cached_diff_name_only": [],
        "recent_log_entries": [],
        "ls_files_results": {},
        "validation_results": [],
        "release_gate_result": {},
        "release_check_result": {},
        "protected_file_status": {},
        "unrelated_untracked_drift": _default_reported_drift_v1(),
        "reconciliation_notes": [],
        "zone": "",
        "red_zone_reasons": [],
        "yellow_zone_notes": [],
        "safe_metadata": {"metadata_only": True},
    }
    for key, value in overrides.items():
        packet[key] = _json_safe(value)
    if not packet.get("zone"):
        packet["zone"] = classify_workflow_integrity_zone_v1(packet)
    packet["red_zone_reasons"] = list(packet.get("red_zone_reasons") or [])
    packet["yellow_zone_notes"] = list(packet.get("yellow_zone_notes") or [])
    return packet


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if isinstance(value, set):
        return list(value)
    return [value]


def _as_mapping(value: Any) -> Mapping[str, Any] | None:
    return value if isinstance(value, Mapping) else None


def _truthy_ok(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key in ("ok", "passed", "success", "valid", "result"):
            if key in value:
                return bool(value[key])
        return False
    return bool(value)


def _validate_log_entries(recent_log_entries: Any) -> tuple[list[dict[str, Any]], list[str]]:
    entries: list[dict[str, Any]] = []
    errors: list[str] = []
    for index, entry in enumerate(_as_list(recent_log_entries)):
        if isinstance(entry, Mapping):
            entries.append({str(key): _json_safe(value) for key, value in entry.items()})
        elif isinstance(entry, str):
            entries.append({"hash": entry.split()[0] if entry else "", "summary": entry})
        else:
            errors.append(f"recent_log_entries[{index}] must be a mapping or string")
    return entries, errors


def _log_has_head(entries: list[dict[str, Any]], head: str) -> bool:
    if not head:
        return False
    for entry in entries:
        if str(entry.get("hash", "")) == head:
            return True
    return False


def _explicitly_unrelated_paths(drift: Any) -> set[str]:
    mapping = _as_mapping(drift)
    if not mapping:
        return set()
    if not mapping.get("explicitly_marked_unrelated"):
        return set()
    return {str(path) for path in _as_list(mapping.get("paths")) if str(path)}


def _protected_file_drift(reported: Mapping[str, Any]) -> list[str]:
    changed = []
    for path in PROTECTED_FILES_V1:
        if path not in reported:
            changed.append(path)
            continue
        if bool(reported.get(path)):
            changed.append(path)
    return changed


def _workflow_integrity_analysis(packet: Mapping[str, Any]) -> dict[str, Any]:
    start_head = str(packet.get("start_head") or "")
    final_head = str(packet.get("final_head") or "")
    reported_files = [str(path) for path in _as_list(packet.get("reported_files")) if str(path)]
    created_or_changed = [str(path) for path in _as_list(packet.get("reported_created_or_changed_files")) if str(path)]
    committed_files = [str(path) for path in _as_list(packet.get("reported_committed_files")) if str(path)]
    tracked_files = [str(path) for path in _as_list(packet.get("tracked_files")) if str(path)]
    untracked_files = [str(path) for path in _as_list(packet.get("untracked_files")) if str(path)]
    staged_files = [str(path) for path in _as_list(packet.get("staged_files")) if str(path)]
    diff_name_only = [str(path) for path in _as_list(packet.get("diff_name_only")) if str(path)]
    cached_diff_name_only = [str(path) for path in _as_list(packet.get("cached_diff_name_only")) if str(path)]
    validation_results = _as_list(packet.get("validation_results"))
    recent_log_entries, log_errors = _validate_log_entries(packet.get("recent_log_entries"))
    ls_files_results = _as_mapping(packet.get("ls_files_results")) or {}
    release_gate_result = _as_mapping(packet.get("release_gate_result")) or {}
    release_check_result = _as_mapping(packet.get("release_check_result")) or {}
    protected_file_status = _as_mapping(packet.get("protected_file_status")) or {}
    unrelated_drift = _as_mapping(packet.get("unrelated_untracked_drift")) or _default_reported_drift_v1()
    reconciliation_notes = [str(note) for note in _as_list(packet.get("reconciliation_notes")) if str(note)]
    red_reasons: list[str] = []
    yellow_notes: list[str] = []
    errors: list[str] = []

    if not reported_files:
        errors.append("reported_files is required")
    if not start_head:
        errors.append("start_head is required")
    if not final_head:
        errors.append("final_head is required")

    for field in REQUIRED_PACKET_FIELDS_V1:
        if field not in packet:
            errors.append(f"missing required field: {field}")
            break

    if not isinstance(packet.get("protected_file_status"), Mapping):
        errors.append("protected_file_status is required and must be a mapping")

    if not isinstance(packet.get("ls_files_results"), Mapping):
        errors.append("ls_files_results is required and must be a mapping")

    if log_errors:
        errors.extend(log_errors)

    missing_ls = [path for path in reported_files if path not in ls_files_results]
    if missing_ls:
        errors.append("reported_files missing from ls_files_results: " + ", ".join(sorted(missing_ls)))

    protected_changed = _protected_file_drift(protected_file_status)
    if protected_changed:
        red_reasons.append("protected_file_drift")

    untracked_explicitly_unrelated = _explicitly_unrelated_paths(unrelated_drift)
    hidden_untracked = [path for path in untracked_files if path not in untracked_explicitly_unrelated]
    if hidden_untracked:
        red_reasons.append("hidden_untracked_relevant_file")
    elif untracked_files and untracked_explicitly_unrelated:
        yellow_notes.append("unrelated_untracked_drift_present")

    reported_untracked = [path for path in reported_files if path in untracked_files]
    for path in reported_untracked:
        if not ls_files_results.get(path):
            red_reasons.append("reported_file_untracked")
            break

    if created_or_changed and start_head and final_head and start_head == final_head:
        red_reasons.append("start_head_equals_final_head_with_reported_changes")

    if created_or_changed and not diff_name_only and not committed_files and start_head == final_head:
        red_reasons.append("tracked_changes_claimed_without_diff_evidence")

    validation_failed = any(
        isinstance(item, Mapping) and not bool(item.get("ok", item.get("passed", item.get("success", True))))
        for item in validation_results
    )
    if validation_failed and "ready" in str(packet.get("reported_final_judgment") or "").lower():
        red_reasons.append("validation_failed_but_ready")

    release_gate_ok = _truthy_ok(release_gate_result)
    release_gate_staged_present = bool(release_gate_result.get("staged_files_present") or staged_files)
    release_gate_staged_cleared = bool(release_gate_result.get("staged_state_cleared") or release_gate_result.get("staged_cleared_before_pass"))
    release_gate_passed_after_clear = release_gate_ok and release_gate_staged_cleared
    if not release_gate_ok and staged_files:
        red_reasons.append("release_gate_failed_with_staged_files")
    if not release_gate_ok and "ready" in str(packet.get("reported_final_judgment") or "").lower():
        red_reasons.append("validation_failed_but_ready")
    if release_gate_passed_after_clear and not reconciliation_notes:
        red_reasons.append("release_gate_passed_after_staged_clear_without_note")

    if committed_files:
        if start_head == final_head:
            red_reasons.append("committed_claim_without_log_evidence")
        elif not _log_has_head(recent_log_entries, final_head):
            red_reasons.append("committed_claim_without_log_evidence")

    if not _truthy_ok(release_check_result) and release_gate_ok and committed_files:
        yellow_notes.append("release_check_failed_or_missing")

    reported_ready = "ready" in str(packet.get("reported_final_judgment") or "").lower()
    if red_reasons and reported_ready and "red_zone_reconciled_ready" not in str(packet.get("reported_final_judgment") or ""):
        red_reasons.append("final_judgment_ready_with_red_zone_reasons")

    next_lane = str(packet.get("reported_recommended_next_lane") or "")
    if next_lane and red_reasons:
        red_reasons.append("next_lane_proceeds_despite_red_zone_condition")

    if red_reasons and reconciliation_notes and str(packet.get("reported_final_judgment") or "") == "red_zone_reconciled_ready":
        zone = "red_zone_reconciled_ready"
    elif red_reasons:
        zone = "red_zone_blocked"
    elif yellow_notes:
        zone = "yellow_zone_needs_note"
    else:
        zone = "green_zone_ready"

    if release_gate_result.get("passed") is True and release_gate_staged_cleared and not reconciliation_notes:
        red_reasons.append("release_gate_passed_after_staged_clear_without_note")
        zone = "red_zone_blocked"

    return {
        "zone": zone,
        "red_zone_reasons": sorted(set(red_reasons)),
        "yellow_zone_notes": sorted(set(yellow_notes)),
        "errors": errors,
        "tracked_files": tracked_files,
        "untracked_files": untracked_files,
        "staged_files": staged_files,
        "diff_name_only": diff_name_only,
        "cached_diff_name_only": cached_diff_name_only,
        "recent_log_entries": recent_log_entries,
    }


def classify_workflow_integrity_zone_v1(packet: Mapping[str, Any]) -> str:
    return _workflow_integrity_analysis(packet)["zone"]


def validate_workflow_integrity_evidence_packet_v1(packet: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(packet, Mapping):
        return {
            "valid": False,
            "blocked": True,
            "errors": ["packet must be a mapping"],
            "warnings": [],
            "zone": "red_zone_blocked",
            "red_zone_reasons": ["missing_evidence"],
            "yellow_zone_notes": [],
        }

    analysis = _workflow_integrity_analysis(packet)
    errors = list(analysis["errors"])
    if analysis["zone"] == "red_zone_reconciled_ready" and not packet.get("reconciliation_notes"):
        errors.append("red_zone_reconciled_ready requires reconciliation_notes")
    if analysis["red_zone_reasons"] and "ready" in str(packet.get("reported_final_judgment") or "").lower() and "red_zone_reconciled_ready" not in str(packet.get("reported_final_judgment") or ""):
        errors.append("final judgment says ready while red-zone reasons exist")

    blocked = bool(errors or analysis["zone"] == "red_zone_blocked")
    valid = not blocked and analysis["zone"] in ALLOWED_WORKFLOW_INTEGRITY_ZONES_V1
    return {
        "valid": valid,
        "blocked": blocked,
        "errors": sorted(set(errors)),
        "warnings": list(analysis["yellow_zone_notes"]),
        "zone": analysis["zone"],
        "red_zone_reasons": list(analysis["red_zone_reasons"]),
        "yellow_zone_notes": list(analysis["yellow_zone_notes"]),
        "reported_files": [str(path) for path in _as_list(packet.get("reported_files")) if str(path)],
    }


def summarize_workflow_integrity_zone_v1(packet: Mapping[str, Any]) -> dict[str, Any]:
    validation = validate_workflow_integrity_evidence_packet_v1(packet)
    report = build_workflow_integrity_evidence_packet_v1(**dict(packet)) if isinstance(packet, Mapping) else build_workflow_integrity_evidence_packet_v1()
    summary_text = (
        f"Workflow integrity zone: {validation['zone']}; "
        f"red reasons: {', '.join(validation['red_zone_reasons']) if validation['red_zone_reasons'] else 'none'}; "
        f"notes: {', '.join(validation['yellow_zone_notes']) if validation['yellow_zone_notes'] else 'none'}"
    )
    return {
        "schema_version": SCHEMA_VERSION_V1,
        "lane_name": report.get("lane_name", ""),
        "zone": validation["zone"],
        "blocked": validation["blocked"],
        "valid": validation["valid"],
        "red_zone_reason_count": len(validation["red_zone_reasons"]),
        "yellow_zone_note_count": len(validation["yellow_zone_notes"]),
        "reported_file_count": len(validation["reported_files"]),
        "summary_text": summary_text,
        "red_zone_reasons": list(validation["red_zone_reasons"]),
        "yellow_zone_notes": list(validation["yellow_zone_notes"]),
        "safe_metadata": _json_safe(report.get("safe_metadata", {})),
    }


def build_initial_workflow_integrity_red_zone_examples_v1() -> tuple[dict[str, Any], ...]:
    return (
        build_workflow_integrity_evidence_packet_v1(
            lane_name="green_committed_doc_lane",
            start_head="1111111111111111111111111111111111111111",
            final_head="2222222222222222222222222222222222222222",
            reported_files=["docs/example_green.md"],
            reported_created_or_changed_files=["docs/example_green.md"],
            reported_committed_files=["docs/example_green.md"],
            reported_final_judgment="green_zone_ready",
            reported_recommended_next_lane="REVIEW_GREEN",
            tracked_files=["docs/example_green.md"],
            untracked_files=[],
            staged_files=[],
            diff_name_only=[],
            diff_stat=[],
            cached_diff_name_only=[],
            recent_log_entries=[{"hash": "2222222222222222222222222222222222222222", "summary": "WESLR: example green"}],
            ls_files_results={"docs/example_green.md": True},
            validation_results=[{"command": "git diff --check", "ok": True}],
            release_gate_result={"passed": True},
            release_check_result={"passed": True},
            protected_file_status={path: False for path in PROTECTED_FILES_V1},
            unrelated_untracked_drift={"explicitly_marked_unrelated": False, "paths": []},
            reconciliation_notes=[],
            safe_metadata={"example_name": "green_committed_doc_lane", "metadata_only": True},
        ),
        build_workflow_integrity_evidence_packet_v1(
            lane_name="red_untracked_doc_same_head_lane",
            start_head="3333333333333333333333333333333333333333",
            final_head="3333333333333333333333333333333333333333",
            reported_files=["docs/example_red_untracked.md"],
            reported_created_or_changed_files=["docs/example_red_untracked.md"],
            reported_committed_files=[],
            reported_final_judgment="ready_for_review",
            reported_recommended_next_lane="REVIEW_RED",
            tracked_files=[],
            untracked_files=["docs/example_red_untracked.md"],
            staged_files=[],
            diff_name_only=[],
            diff_stat=[],
            cached_diff_name_only=[],
            recent_log_entries=[{"hash": "3333333333333333333333333333333333333333", "summary": "WESLR: no commit"}],
            ls_files_results={"docs/example_red_untracked.md": False},
            validation_results=[{"command": "git diff --check", "ok": True}],
            release_gate_result={"passed": True},
            release_check_result={"passed": True},
            protected_file_status={path: False for path in PROTECTED_FILES_V1},
            unrelated_untracked_drift={"explicitly_marked_unrelated": False, "paths": []},
            reconciliation_notes=[],
            safe_metadata={"example_name": "red_untracked_doc_same_head_lane", "metadata_only": True},
        ),
        build_workflow_integrity_evidence_packet_v1(
            lane_name="yellow_unrelated_drift_lane",
            start_head="4444444444444444444444444444444444444444",
            final_head="5555555555555555555555555555555555555555",
            reported_files=["docs/example_yellow.md"],
            reported_created_or_changed_files=["docs/example_yellow.md"],
            reported_committed_files=["docs/example_yellow.md"],
            reported_final_judgment="green_zone_ready",
            reported_recommended_next_lane="REVIEW_YELLOW",
            tracked_files=["docs/example_yellow.md"],
            untracked_files=["notes/outside_lane.md"],
            staged_files=[],
            diff_name_only=[],
            diff_stat=[],
            cached_diff_name_only=[],
            recent_log_entries=[{"hash": "5555555555555555555555555555555555555555", "summary": "WESLR: example yellow"}],
            ls_files_results={"docs/example_yellow.md": True},
            validation_results=[{"command": "git diff --check", "ok": True}],
            release_gate_result={"passed": True},
            release_check_result={"passed": True},
            protected_file_status={path: False for path in PROTECTED_FILES_V1},
            unrelated_untracked_drift={"explicitly_marked_unrelated": True, "paths": ["notes/outside_lane.md"], "notes": ["outside lane"]},
            reconciliation_notes=[],
            safe_metadata={"example_name": "yellow_unrelated_drift_lane", "metadata_only": True},
        ),
        build_workflow_integrity_evidence_packet_v1(
            lane_name="red_reconciled_lane",
            start_head="7777777777777777777777777777777777777777",
            final_head="7777777777777777777777777777777777777777",
            reported_files=["docs/example_reconciled.md"],
            reported_created_or_changed_files=["docs/example_reconciled.md"],
            reported_committed_files=["docs/example_reconciled.md"],
            reported_final_judgment="red_zone_reconciled_ready",
            reported_recommended_next_lane="REVIEW_RECONCILED",
            tracked_files=["docs/example_reconciled.md"],
            untracked_files=[],
            staged_files=[],
            diff_name_only=[],
            diff_stat=[],
            cached_diff_name_only=[],
            recent_log_entries=[{"hash": "7777777777777777777777777777777777777777", "summary": "WESLR: example reconciled"}],
            ls_files_results={"docs/example_reconciled.md": True},
            validation_results=[{"command": "git diff --check", "ok": True}],
            release_gate_result={"passed": True},
            release_check_result={"passed": True},
            protected_file_status={path: False for path in PROTECTED_FILES_V1},
            unrelated_untracked_drift={"explicitly_marked_unrelated": False, "paths": []},
            reconciliation_notes=["Start/final HEAD mismatch is intentional and reconciled by commit evidence."],
            safe_metadata={"example_name": "red_reconciled_lane", "metadata_only": True},
        ),
    )


__all__ = [
    "ALLOWED_WORKFLOW_INTEGRITY_ZONES_V1",
    "PROTECTED_FILES_V1",
    "SCHEMA_VERSION_V1",
    "build_initial_workflow_integrity_red_zone_examples_v1",
    "build_workflow_integrity_evidence_packet_v1",
    "classify_workflow_integrity_zone_v1",
    "summarize_workflow_integrity_zone_v1",
    "to_workflow_integrity_json_safe_v1",
    "validate_workflow_integrity_evidence_packet_v1",
]
