from __future__ import annotations

import json
from pathlib import Path

import pytest

from weslr.advisor_review_queue_persistence import (
    apply_public_pilot_queue_suppression_to_event_v1,
    build_public_pilot_queue_removal_receipt_v1,
    build_public_pilot_queue_suppression_marker_v1,
    validate_queue_storage_path,
)
from weslr.pilot_signal_logger import PilotSignalLogger
from weslr.public_pilot_storage_privacy_safety import (
    build_public_pilot_deletion_request_v1,
    build_public_pilot_removal_receipt_v1,
    build_public_pilot_revocation_request_v1,
    build_public_pilot_suppression_marker_v1,
    validate_public_pilot_deletion_request_v1,
    validate_public_pilot_revocation_request_v1,
)
from weslr.review_interface import get_public_pilot_review_quarantine_result
from weslr.suggestion_box import SuggestionBox


TEST_SAFE_CONTEXT = {
    "test_safe_storage": True,
    "synthetic_temp_path": True,
    "denied_authority": {
        "queue_processing": False,
        "runtime_behavior": False,
        "final_answer_behavior": False,
        "public_launch": False,
        "promotion_approval": False,
    },
}

VALID_REMOVAL = {
    "requester": "person@example.invalid",
    "surface": "suggestion_box",
    "scope": ["contact", "suggestion", "project_review"],
    "reason": "remove synthetic public pilot record",
}

VALID_REVOCATION = {
    "requester": "person@example.invalid",
    "surface": "pilot_signals",
    "scope": ["consent", "future_use"],
    "reason": "revoke future use",
}


def _synthetic_suggestion_box(tmp_path: Path, *, public_pilot_mode: bool = True) -> SuggestionBox:
    return SuggestionBox(
        tmp_path / "requests.json",
        tmp_path / "continuity.json",
        public_pilot_mode=public_pilot_mode,
        quarantine_authorization_metadata=TEST_SAFE_CONTEXT,
    )


def _submit_synthetic_request(box: SuggestionBox) -> dict:
    req = box.submit_request(
        {
            "requester_type": "individual",
            "domain": "synthetic-domain",
            "requested_capability": "synthetic capability",
            "problem_statement": "synthetic problem statement",
            "requester_id": "person@example.invalid",
            "contact_email": "person@example.invalid",
            "additional_notes": "synthetic note",
        },
        public_pilot_mode=True,
        consent_metadata={
            "storage_consent": True,
            "contact_storage_consent": True,
            "feedback_storage_consent": True,
            "suggestion_storage_consent": True,
            "project_review_storage_consent": True,
        },
    )
    return req.to_dict()


def test_valid_deletion_request_metadata_passes():
    errors = validate_public_pilot_deletion_request_v1(VALID_REMOVAL)
    assert errors == []
    request = build_public_pilot_deletion_request_v1(VALID_REMOVAL)
    assert request["validated"] is True
    assert request["real_deletion_allowed"] is False


def test_valid_revocation_request_metadata_passes():
    errors = validate_public_pilot_revocation_request_v1(VALID_REVOCATION)
    assert errors == []
    request = build_public_pilot_revocation_request_v1(VALID_REVOCATION)
    assert request["validated"] is True
    assert request["future_use_suppression_requested"] is True


@pytest.mark.parametrize(
    "payload, expected",
    [
        ({"surface": "suggestion_box", "scope": ["contact"], "reason": "x"}, "requester"),
        ({"requester": "person@example.invalid", "scope": ["contact"], "reason": "x"}, "surface"),
        ({"requester": "person@example.invalid", "surface": "suggestion_box", "reason": "x"}, "scope"),
        ({"requester": "person@example.invalid", "surface": "suggestion_box", "scope": ["contact"]}, "reason"),
    ],
)
def test_missing_requester_scope_surface_blocks(payload, expected):
    errors = validate_public_pilot_deletion_request_v1(payload)
    assert expected in ";".join(errors)


def test_non_json_safe_metadata_blocks():
    payload = {**VALID_REMOVAL, "bad": object()}
    errors = validate_public_pilot_deletion_request_v1(payload)
    assert "JSON-safe" in ";".join(errors)


def test_true_denied_authority_field_blocks():
    payload = {**VALID_REMOVAL, "denied_authority": {"public_launch": True}}
    errors = validate_public_pilot_deletion_request_v1(payload)
    assert "public_launch" in ";".join(errors)


def test_deletion_request_does_not_imply_real_deletion_by_default():
    request = build_public_pilot_deletion_request_v1(VALID_REMOVAL)
    assert request["real_deletion_allowed"] is False
    assert request["blocked"] is False


def test_revocation_request_blocks_future_use_by_metadata():
    request = build_public_pilot_revocation_request_v1(VALID_REVOCATION)
    assert request["future_use_suppression_requested"] is True
    assert request["consent_revocation_requested"] is True


def test_contact_removal_receipt_contains_no_raw_contact_value():
    receipt = build_public_pilot_removal_receipt_v1(
        {
            **VALID_REMOVAL,
            "request_kind": "deletion",
            "contact_email": "person@example.invalid",
            "contact_value": "person@example.invalid",
        }
    )
    encoded = json.dumps(receipt, sort_keys=True)
    assert "person@example.invalid" not in encoded
    assert receipt["raw_contact_value_included"] is False


def test_feedback_suggestion_project_review_removal_receipt_contains_no_raw_text():
    raw_text = "raw feedback suggestion project text"
    receipt = build_public_pilot_removal_receipt_v1(
        {
            "requester": "person@example.invalid",
            "surface": "review_interface",
            "scope": ["feedback", "suggestion", "project_review"],
            "reason": "remove feedback suggestion project-review content",
            "feedback_text": raw_text,
            "suggestion_text": raw_text,
            "project_review_text": raw_text,
        }
    )
    encoded = json.dumps(receipt, sort_keys=True)
    assert raw_text not in encoded
    assert receipt["raw_user_text_included"] is False


def test_suppression_marker_json_safe_and_blocks_display_export_promotion():
    marker = build_public_pilot_suppression_marker_v1(VALID_REMOVAL)
    assert json.dumps(marker, sort_keys=True)
    assert marker["display_allowed"] is False
    assert marker["export_allowed"] is False
    assert marker["promotion_allowed"] is False


def test_suggestion_synthetic_temp_removal_suppression_works_without_raw_return(tmp_path: Path):
    box = _synthetic_suggestion_box(tmp_path)
    request = _submit_synthetic_request(box)
    result = box.request_public_pilot_deletion(
        {
            "request_id": request["request_id"],
            "requester": request["requester_id"],
            "surface": "suggestion_box",
            "scope": ["contact", "suggestion"],
            "reason": "remove synthetic request",
        },
        public_pilot_mode=True,
        synthetic_safe_storage_context=TEST_SAFE_CONTEXT,
    )
    assert result.get("suppressed") is True or result.get("display_allowed") is False
    assert "synthetic problem statement" not in json.dumps(result, sort_keys=True)
    assert all(req.get("request_id") != request["request_id"] for req in box.requests)


def test_suggestion_real_legacy_path_blocked_in_public_pilot_mode():
    box = SuggestionBox(public_pilot_mode=True)
    result = box.request_public_pilot_deletion(
        {
            "requester": "person@example.invalid",
            "surface": "suggestion_box",
            "scope": ["suggestion"],
            "reason": "remove legacy path",
        },
        public_pilot_mode=True,
    )
    assert result["real_deletion_allowed"] is False
    assert box.get_public_pilot_quarantine_result()["quarantined"] is True


def test_pilot_logger_synthetic_suppression_works_without_raw_details(tmp_path: Path):
    logger = PilotSignalLogger(str(tmp_path / "pilot"), public_pilot_safe_mode=True)
    result = logger.request_public_pilot_deletion(
        {
            "requester": "person@example.invalid",
            "surface": "pilot_signals",
            "scope": ["feedback"],
            "reason": "remove signal",
            "details": {"note": "raw signal note"},
            "user_id": "user-123",
            "session_id": "session-456",
        },
        public_pilot_safe_mode=True,
        synthetic_safe_storage_context=TEST_SAFE_CONTEXT,
    )
    encoded = json.dumps(result, sort_keys=True)
    assert "raw signal note" not in encoded
    assert "user-123" not in encoded
    assert "session-456" not in encoded
    assert result.get("suppressed") is True or result.get("display_allowed") is False


def test_pilot_logger_real_legacy_path_blocked_in_public_pilot_mode(tmp_path: Path):
    logger = PilotSignalLogger(str(tmp_path / "pilot"), public_pilot_safe_mode=True)
    result = logger.request_public_pilot_deletion(
        {
            "requester": "person@example.invalid",
            "surface": "pilot_signals",
            "scope": ["feedback"],
            "reason": "remove legacy signal",
        },
        public_pilot_safe_mode=True,
    )
    assert result["real_deletion_allowed"] is False
    assert logger.require_safe_display(raw_display=False, raw_export=False) is None


def test_review_queue_synthetic_suppression_works_without_raw_record_return():
    event = {
        "schema_version": "1.0",
        "event_id": "queue-event-1",
        "event_type": "queue_item_created",
        "queue_item_id": "queue-item-1",
        "queue_item_snapshot": {"feedback_text": "raw queue text", "count": 1},
        "previous_status": "",
        "new_status": "pending_review",
        "operator_decision": "pending_review",
        "redacted_summary": "queue item created",
        "created_at": "2026-05-27T10:42:00Z",
        "actor": "operator_or_system",
        "safety_flags": {},
    }
    marker = build_public_pilot_queue_suppression_marker_v1(
        {
            "requester": "person@example.invalid",
            "surface": "review_queue",
            "scope": ["queue_item"],
            "reason": "suppress queue item",
        }
    )
    result = apply_public_pilot_queue_suppression_to_event_v1(event, marker)
    encoded = json.dumps(result, sort_keys=True)
    assert "raw queue text" not in encoded
    assert result["queue_processing_allowed"] is False
    assert result["display_allowed"] is False
    assert result["queue_item_snapshot_field_count"] == 2


def test_review_queue_real_raw_path_blocked_in_public_pilot_mode():
    errors = validate_queue_storage_path("review_queue.json", public_pilot_mode=True)
    assert errors
    quarantine = get_public_pilot_review_quarantine_result("review_queue.json")
    assert quarantine["quarantined"] is True
    assert quarantine["raw_records_read"] is False


def test_dot_weslr_path_blocked():
    errors = validate_queue_storage_path(".weslr/advisor_review_queue.jsonl", public_pilot_mode=True)
    assert errors


def test_no_queue_processing_or_provider_model_search_advisor_calls():
    safety_text = Path("weslr/public_pilot_storage_privacy_safety.py").read_text()
    queue_text = Path("weslr/advisor_review_queue_persistence.py").read_text()
    forbidden_terms = ["openai.", "anthropic.", "requests.", "provider_call(", "search_call(", "advisor_call("]
    assert not any(term in safety_text for term in forbidden_terms)
    assert not any(term in queue_text for term in forbidden_terms)
    receipt = build_public_pilot_queue_removal_receipt_v1({**VALID_REMOVAL, "request_kind": "deletion"})
    assert receipt["queue_processing_allowed"] is False


def test_no_public_launch_runtime_final_answer_authority():
    marker = build_public_pilot_suppression_marker_v1(VALID_REMOVAL)
    receipt = build_public_pilot_queue_removal_receipt_v1({**VALID_REMOVAL, "request_kind": "deletion"})
    assert marker["public_launch_allowed"] is False
    assert marker["runtime_behavior_allowed"] is False
    assert marker["final_answer_behavior_allowed"] is False
    assert receipt["public_launch_allowed"] is False
    assert receipt["runtime_behavior_allowed"] is False
    assert receipt["final_answer_behavior_allowed"] is False


def test_no_continuity_data_files_modified_by_synthetic_temp_paths(tmp_path: Path):
    box = _synthetic_suggestion_box(tmp_path)
    logger = PilotSignalLogger(
        str(tmp_path / "pilot"),
        public_pilot_safe_mode=True,
        quarantine_authorization_metadata=TEST_SAFE_CONTEXT,
    )
    assert str(box.storage_path).startswith(str(tmp_path))
    assert str(box.continuity_path).startswith(str(tmp_path))
    assert str(logger.log_dir).startswith(str(tmp_path))
    assert str(logger.user_events_file).startswith(str(tmp_path))
