from __future__ import annotations

import json
from pathlib import Path

import pytest

from weslr.advisor_review_queue_persistence import validate_queue_storage_path
from weslr.consolidation_promotion import auto_promote
from weslr.pilot_signal_logger import PilotSignalLogger
from weslr.public_pilot_storage_privacy_safety import (
    build_public_pilot_quarantine_result_v1,
    is_public_pilot_storage_surface_quarantined_v1,
    require_public_pilot_storage_surface_not_quarantined_v1,
    validate_public_pilot_quarantine_authorization_v1,
)
from weslr.review_interface import (
    get_public_pilot_review_quarantine_result,
    load_pending_contract_reviews,
)
from weslr.suggestion_box import SuggestionBox


TEST_SAFE_AUTH = {
    "test_safe_storage": True,
    "synthetic_temp_path": True,
    "denied_authority": {
        "queue_processing": False,
        "promotion_approval": False,
        "runtime_behavior": False,
        "final_answer_behavior": False,
        "public_launch": False,
    },
}

VALID_CONSENT = {
    "storage_consent": True,
    "suggestion_storage_consent": True,
    "contact_storage_consent": True,
}


def test_dot_weslr_path_quarantined_in_public_pilot_mode():
    assert is_public_pilot_storage_surface_quarantined_v1(".weslr/advisor_review_queue.jsonl", public_pilot_mode=True)
    with pytest.raises(ValueError):
        require_public_pilot_storage_surface_not_quarantined_v1(".weslr/advisor_review_queue.jsonl", public_pilot_mode=True)


def test_public_pilot_legacy_surfaces_quarantined():
    paths = [
        "continuity/suggestion_box/requests.json",
        "continuity/suggestion_box/continuity.json",
        "continuity/pilot_signals/user_events.json",
        "continuity/pilot_signals/interventions.json",
        "review_queue.json",
    ]
    for path in paths:
        assert is_public_pilot_storage_surface_quarantined_v1(path, public_pilot_mode=True)


def test_missing_quarantine_authorization_blocks():
    errors = validate_public_pilot_quarantine_authorization_v1(None)
    assert "authorization metadata is required" in ";".join(errors)


def test_denied_authority_true_field_blocks():
    errors = validate_public_pilot_quarantine_authorization_v1(
        {**TEST_SAFE_AUTH, "denied_authority": {"public_launch": True}}
    )
    assert "public_launch" in ";".join(errors)


def test_non_json_safe_authorization_metadata_blocks():
    errors = validate_public_pilot_quarantine_authorization_v1({"test_safe_storage": True, "bad": object()})
    assert "JSON-safe" in ";".join(errors)


def test_suggestion_public_pilot_legacy_read_blocked():
    box = SuggestionBox(public_pilot_mode=True)
    result = box.get_public_pilot_quarantine_result()
    assert result["quarantined"] is True
    assert result["raw_records_read"] is False
    assert box.requests == []


def test_suggestion_public_pilot_unsafe_write_blocked():
    box = SuggestionBox(public_pilot_mode=True)
    with pytest.raises(ValueError):
        box.submit_request(
            {
                "requester_type": "individual",
                "domain": "synthetic",
                "requested_capability": "synthetic capability",
                "problem_statement": "synthetic problem",
            },
            public_pilot_mode=True,
            consent_metadata=VALID_CONSENT,
        )
    assert box.requests == []


def test_suggestion_synthetic_temp_path_allowed_with_test_safe_authorization(tmp_path: Path):
    box = SuggestionBox(
        tmp_path / "requests.json",
        tmp_path / "continuity.json",
        public_pilot_mode=True,
        quarantine_authorization_metadata=TEST_SAFE_AUTH,
    )
    req = box.submit_request(
        {
            "requester_type": "individual",
            "domain": "synthetic",
            "requested_capability": "synthetic capability",
            "problem_statement": "synthetic problem",
        },
        public_pilot_mode=True,
        consent_metadata=VALID_CONSENT,
    )
    assert req.request_id.startswith("req-")


def test_pilot_logger_public_pilot_raw_display_export_blocked():
    logger = PilotSignalLogger(public_pilot_safe_mode=True)
    with pytest.raises(ValueError):
        logger.require_safe_display(raw_display=True)
    with pytest.raises(ValueError):
        logger.require_safe_display(raw_export=True)


def test_pilot_logger_legacy_storage_quarantined_without_real_file_reads():
    logger = PilotSignalLogger(public_pilot_safe_mode=True)
    result = logger.get_public_pilot_safe_event_summary()
    assert result["quarantined"] is True
    assert result["raw_records_read"] is False
    with pytest.raises(ValueError):
        logger.log_user_event("synthetic", "user", "session", {"note": "synthetic"})


def test_advisor_queue_dot_weslr_public_pilot_path_blocked():
    errors = validate_queue_storage_path(".weslr/advisor_review_queue.jsonl", public_pilot_mode=True)
    assert errors
    assert any(".weslr" in error or "quarantined" in error for error in errors)


def test_review_interface_raw_public_pilot_review_read_display_blocked():
    with pytest.raises(ValueError):
        load_pending_contract_reviews("review_queue.json", public_pilot_mode=True)
    result = get_public_pilot_review_quarantine_result("review_queue.json")
    assert result["quarantined"] is True
    assert result["raw_records_read"] is False


def test_consolidation_promotion_public_pilot_path_blocked_before_write_or_audit():
    result = auto_promote(
        {"cluster_id": "synthetic", "proposed_destination": "continuity_summary"},
        public_pilot_mode=True,
    )
    assert result.promoted is False
    assert result.record_written is False
    assert result.decision == "blocked"


def test_quarantine_result_json_safe_and_contains_no_raw_user_text():
    result = build_public_pilot_quarantine_result_v1(
        "synthetic_surface",
        ["synthetic_reason"],
        path_label="continuity/suggestion_box/requests.json",
    )
    encoded = json.dumps(result, sort_keys=True)
    assert "synthetic private user text" not in encoded
    assert result["raw_records_included"] is False
    assert result["queue_processing_allowed"] is False
    assert result["public_launch_allowed"] is False


def test_authorized_temp_path_not_quarantined():
    assert not is_public_pilot_storage_surface_quarantined_v1(
        "synthetic/temp/path.json",
        public_pilot_mode=True,
        authorization_metadata=TEST_SAFE_AUTH,
    )


def test_no_public_launch_runtime_final_answer_authority_in_quarantine_result():
    result = build_public_pilot_quarantine_result_v1("surface", ["blocked"])
    assert result["runtime_behavior_allowed"] is False
    assert result["final_answer_behavior_allowed"] is False
    assert result["public_launch_allowed"] is False
    assert result["promotion_allowed"] is False


def test_no_real_continuity_or_dot_weslr_paths_created_by_temp_tests(tmp_path: Path):
    box = SuggestionBox(
        tmp_path / "requests.json",
        tmp_path / "continuity.json",
        public_pilot_mode=True,
        quarantine_authorization_metadata=TEST_SAFE_AUTH,
    )
    assert str(box.storage_path).startswith(str(tmp_path))
    logger = PilotSignalLogger(
        str(tmp_path / "pilot"),
        public_pilot_safe_mode=True,
        quarantine_authorization_metadata=TEST_SAFE_AUTH,
    )
    assert str(logger.log_dir).startswith(str(tmp_path))
