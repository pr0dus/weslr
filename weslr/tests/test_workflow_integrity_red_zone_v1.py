from __future__ import annotations

import ast
from copy import deepcopy
from pathlib import Path

import pytest

import weslr.workflow_integrity_red_zone as mod
from weslr.workflow_integrity_red_zone import (
    PROTECTED_FILES_V1,
    build_initial_workflow_integrity_red_zone_examples_v1,
    build_workflow_integrity_evidence_packet_v1,
    classify_workflow_integrity_zone_v1,
    summarize_workflow_integrity_zone_v1,
    to_workflow_integrity_json_safe_v1,
    validate_workflow_integrity_evidence_packet_v1,
)

HELPER_PATH = Path(__file__).resolve().parents[1] / "workflow_integrity_red_zone.py"


BASE_PACKET = build_workflow_integrity_evidence_packet_v1(
    lane_name="base_lane",
    start_head="aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    final_head="bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
    reported_files=["docs/base.md"],
    reported_created_or_changed_files=["docs/base.md"],
    reported_committed_files=["docs/base.md"],
    reported_final_judgment="green_zone_ready",
    reported_recommended_next_lane="REVIEW_BASE",
    tracked_files=["docs/base.md"],
    untracked_files=[],
    staged_files=[],
    diff_name_only=[],
    diff_stat=[],
    cached_diff_name_only=[],
    recent_log_entries=[{"hash": "bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb", "summary": "WESLR: base lane"}],
    ls_files_results={"docs/base.md": True},
    validation_results=[{"command": "git diff --check", "ok": True}],
    release_gate_result={"passed": True},
    release_check_result={"passed": True},
    protected_file_status={path: False for path in PROTECTED_FILES_V1},
    unrelated_untracked_drift={"explicitly_marked_unrelated": False, "paths": []},
    reconciliation_notes=[],
    safe_metadata={"example_name": "base", "metadata_only": True},
)


def _packet(**overrides):
    packet = deepcopy(BASE_PACKET)
    packet.update(overrides)
    return build_workflow_integrity_evidence_packet_v1(**packet)


def test_green_committed_doc_lane_is_green():
    packet = build_initial_workflow_integrity_red_zone_examples_v1()[0]
    assert classify_workflow_integrity_zone_v1(packet) == "green_zone_ready"
    validation = validate_workflow_integrity_evidence_packet_v1(packet)
    assert validation["valid"] is True
    assert validation["blocked"] is False


def test_created_doc_untracked_same_head_is_red():
    packet = build_initial_workflow_integrity_red_zone_examples_v1()[1]
    assert packet["start_head"] == packet["final_head"]
    validation = validate_workflow_integrity_evidence_packet_v1(packet)
    assert validation["zone"] == "red_zone_blocked"
    assert "start_head_equals_final_head_with_reported_changes" in validation["red_zone_reasons"]
    assert validation["valid"] is False


def test_file_present_but_git_ls_files_empty_is_red():
    packet = _packet(
        reported_files=["docs/missing_track.md"],
        reported_created_or_changed_files=["docs/missing_track.md"],
        ls_files_results={"docs/missing_track.md": False},
        untracked_files=["docs/missing_track.md"],
        tracked_files=[],
        reported_committed_files=[],
        reported_final_judgment="ready_for_review",
    )
    validation = validate_workflow_integrity_evidence_packet_v1(packet)
    assert validation["zone"] == "red_zone_blocked"
    assert "reported_file_untracked" in validation["red_zone_reasons"]


def test_hidden_untracked_relevant_file_under_untracked_no_is_red():
    packet = _packet(
        reported_files=["docs/hidden_untracked.md"],
        reported_created_or_changed_files=["docs/hidden_untracked.md"],
        ls_files_results={"docs/hidden_untracked.md": False},
        untracked_files=["docs/hidden_untracked.md"],
        tracked_files=[],
        reported_committed_files=[],
        reported_final_judgment="ready_for_review",
    )
    validation = validate_workflow_integrity_evidence_packet_v1(packet)
    assert validation["zone"] == "red_zone_blocked"
    assert "hidden_untracked_relevant_file" in validation["red_zone_reasons"]


def test_unrelated_untracked_drift_becomes_yellow_with_note():
    packet = build_initial_workflow_integrity_red_zone_examples_v1()[2]
    validation = validate_workflow_integrity_evidence_packet_v1(packet)
    assert validation["zone"] in {"yellow_zone_needs_note", "green_zone_ready"}
    assert validation["yellow_zone_notes"]
    summary = summarize_workflow_integrity_zone_v1(packet)
    assert "unrelated_untracked_drift_present" in summary["yellow_zone_notes"] or summary["zone"] == "green_zone_ready"


def test_failed_release_gate_with_ready_judgment_is_red():
    packet = _packet(
        release_gate_result={"passed": False, "staged_files_present": False},
        reported_final_judgment="green_zone_ready",
    )
    validation = validate_workflow_integrity_evidence_packet_v1(packet)
    assert validation["zone"] == "red_zone_blocked"
    assert validation["errors"] or validation["red_zone_reasons"]


def test_staged_release_gate_failure_is_red():
    packet = _packet(
        staged_files=["docs/staged.md"],
        release_gate_result={"passed": False, "staged_files_present": True},
        reported_final_judgment="ready_for_review",
    )
    validation = validate_workflow_integrity_evidence_packet_v1(packet)
    assert validation["zone"] == "red_zone_blocked"
    assert "release_gate_failed_with_staged_files" in validation["red_zone_reasons"]


def test_release_gate_pass_after_staged_clear_without_note_is_red():
    packet = _packet(
        staged_files=[],
        release_gate_result={"passed": True, "staged_state_cleared": True},
        reconciliation_notes=[],
        reported_final_judgment="green_zone_ready",
    )
    validation = validate_workflow_integrity_evidence_packet_v1(packet)
    assert validation["zone"] == "red_zone_blocked"
    assert "release_gate_passed_after_staged_clear_without_note" in validation["red_zone_reasons"]


def test_committed_claim_but_log_missing_commit_is_red():
    packet = _packet(
        reported_committed_files=["docs/commit_missing.md"],
        recent_log_entries=[{"hash": "cccccccccccccccccccccccccccccccccccccccc", "summary": "different commit"}],
        final_head="dddddddddddddddddddddddddddddddddddddddd",
        reported_files=["docs/commit_missing.md"],
        ls_files_results={"docs/commit_missing.md": True},
    )
    validation = validate_workflow_integrity_evidence_packet_v1(packet)
    assert validation["zone"] == "red_zone_blocked"
    assert "committed_claim_without_log_evidence" in validation["red_zone_reasons"]


def test_protected_file_drift_is_red():
    status = {path: False for path in PROTECTED_FILES_V1}
    status["weslr/chat_responder.py"] = True
    packet = _packet(protected_file_status=status)
    validation = validate_workflow_integrity_evidence_packet_v1(packet)
    assert validation["zone"] == "red_zone_blocked"
    assert "protected_file_drift" in validation["red_zone_reasons"]


def test_reconciled_red_zone_with_notes_is_red_zone_reconciled_ready():
    packet = build_initial_workflow_integrity_red_zone_examples_v1()[3]
    validation = validate_workflow_integrity_evidence_packet_v1(packet)
    assert validation["zone"] == "red_zone_reconciled_ready"
    assert validation["valid"] is True
    assert packet["reconciliation_notes"]


def test_json_safe_conversion_is_json_safe():
    safe = to_workflow_integrity_json_safe_v1({"a": {1, 2}, "b": object()})
    assert isinstance(safe["a"], list)
    assert isinstance(safe["b"], str)


def test_summary_includes_red_reasons_without_private_data():
    packet = _packet(
        reported_final_judgment="ready_for_review",
        staged_files=["docs/staged.md"],
        release_gate_result={"passed": False, "staged_files_present": True},
        reported_recommended_next_lane="REVIEW_TOO_SOON",
    )
    summary = summarize_workflow_integrity_zone_v1(packet)
    text = summary["summary_text"]
    assert "release_gate_failed_with_staged_files" in summary["red_zone_reasons"]
    assert "docs/staged.md" not in text
    assert "private" not in text.lower()


def test_examples_cover_expected_zones():
    zones = {validate_workflow_integrity_evidence_packet_v1(packet)["zone"] for packet in build_initial_workflow_integrity_red_zone_examples_v1()}
    assert {"green_zone_ready", "yellow_zone_needs_note", "red_zone_blocked", "red_zone_reconciled_ready"}.issubset(zones)


def test_helper_source_has_no_forbidden_imports():
    source = HELPER_PATH.read_text()
    tree = ast.parse(source)
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    forbidden = {"subprocess", "os", "socket", "urllib", "http", "requests", "webbrowser"}
    assert imported.isdisjoint(forbidden)
    assert "os.system" not in source
    assert "subprocess" not in source
    assert ".open(" not in source
    assert "open(" not in source
