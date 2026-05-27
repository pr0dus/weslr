from __future__ import annotations

import re
from pathlib import Path

import pytest

from weslr.advisor_review_queue_persistence import validate_queue_storage_path
from weslr.consolidation_promotion import auto_promote
from weslr.pilot_signal_logger import PilotSignalLogger
from weslr.public_pilot_storage_privacy_safety import (
    normalize_public_pilot_consent_metadata_v1,
    redact_public_pilot_text_v1,
    reject_public_pilot_dot_weslr_path_v1,
    reject_public_pilot_raw_private_text_v1,
    require_public_pilot_storage_consent_v1,
    safe_public_pilot_summary_v1,
    validate_public_pilot_consent_metadata_v1,
    validate_public_pilot_denied_authority_v1,
)
from weslr.suggestion_box import SuggestionBox


VALID_CONSENT = {
    "storage_consent": True,
    "contact_storage_consent": True,
    "feedback_storage_consent": True,
    "suggestion_storage_consent": True,
    "project_review_storage_consent": True,
}


def test_valid_public_pilot_consent_metadata_passes():
    normalized = require_public_pilot_storage_consent_v1(
        VALID_CONSENT,
        require_contact_storage=True,
        require_suggestion_storage=True,
    )
    assert normalized["storage_consent"] is True
    assert normalized["suggestion_storage_consent"] is True


def test_missing_storage_consent_blocks():
    errors = validate_public_pilot_consent_metadata_v1({"suggestion_storage_consent": True})
    assert "storage consent" in ";".join(errors)


def test_revoked_consent_blocks():
    errors = validate_public_pilot_consent_metadata_v1({**VALID_CONSENT, "revoked": True})
    assert "revoked" in ";".join(errors)


def test_missing_contact_consent_blocks_contact_storage():
    errors = validate_public_pilot_consent_metadata_v1(
        {"storage_consent": True, "suggestion_storage_consent": True},
        require_contact_storage=True,
    )
    assert "contact storage consent" in ";".join(errors)


def test_separate_optional_consents_default_false():
    normalized = normalize_public_pilot_consent_metadata_v1({"storage_consent": True})
    assert normalized["testimonial_consent"] is False
    assert normalized["upstream_public_sharing_consent"] is False
    assert normalized["ocw_operator_access_consent"] is False


def test_raw_private_text_marker_blocks_or_redacts():
    with pytest.raises(ValueError):
        reject_public_pilot_raw_private_text_v1("synthetic token marker", field_name="synthetic")
    redacted = redact_public_pilot_text_v1("synthetic token marker")
    assert "token" not in redacted.lower()
    assert "[redacted" in redacted


def test_safe_summary_does_not_expose_raw_text():
    raw = "synthetic private project marker"
    summary = safe_public_pilot_summary_v1({"problem_statement": raw}, text_fields=("problem_statement",))
    assert raw not in str(summary)
    assert summary["summary_mode"] == "metadata_redacted_count_only"


def test_dot_weslr_path_rejected_in_public_pilot_mode():
    with pytest.raises(ValueError):
        reject_public_pilot_dot_weslr_path_v1(".weslr/advisor_review_queue.jsonl")
    assert validate_queue_storage_path(".weslr/advisor_review_queue.jsonl", public_pilot_mode=True)


def test_non_json_safe_metadata_rejected():
    errors = validate_public_pilot_consent_metadata_v1({"storage_consent": True, "bad": object()})
    assert "JSON-safe" in ";".join(errors)


def test_denied_authority_true_field_rejected():
    errors = validate_public_pilot_denied_authority_v1({"public_launch": True})
    assert "public_launch" in ";".join(errors)


def _request_payload(contact_email: str | None = None) -> dict:
    return {
        "requester_type": "individual",
        "domain": "synthetic-domain",
        "requested_capability": "synthetic capability label",
        "problem_statement": "synthetic problem label",
        "contact_email": contact_email,
    }


def test_suggestion_public_pilot_storage_without_consent_blocks(tmp_path: Path):
    box = SuggestionBox(tmp_path / "requests.json", tmp_path / "continuity.json")
    with pytest.raises(ValueError):
        box.submit_request(_request_payload(), public_pilot_mode=True)
    assert box.requests == []


def test_suggestion_contact_email_without_consent_blocks(tmp_path: Path):
    box = SuggestionBox(tmp_path / "requests.json", tmp_path / "continuity.json")
    with pytest.raises(ValueError):
        box.submit_request(
            _request_payload("person@example.invalid"),
            public_pilot_mode=True,
            consent_metadata={"storage_consent": True, "suggestion_storage_consent": True},
        )
    assert box.requests == []


def test_suggestion_public_pilot_storage_with_consent_passes(tmp_path: Path):
    box = SuggestionBox(tmp_path / "requests.json", tmp_path / "continuity.json")
    req = box.submit_request(
        _request_payload("person@example.invalid"),
        public_pilot_mode=True,
        consent_metadata=VALID_CONSENT,
    )
    assert req.request_id.startswith("req-")


def test_pilot_logger_raw_display_export_blocks_in_public_pilot_safe_mode(tmp_path: Path):
    logger = PilotSignalLogger(str(tmp_path / "pilot"), public_pilot_safe_mode=True)
    with pytest.raises(ValueError):
        logger.require_safe_display(raw_display=True)
    with pytest.raises(ValueError):
        logger.require_safe_display(raw_export=True)


def test_pilot_logger_safe_summary_path_does_not_include_raw_details(tmp_path: Path):
    logger = PilotSignalLogger(str(tmp_path / "pilot"), public_pilot_safe_mode=True)
    entry = logger.log_user_event(
        "synthetic_event",
        "synthetic-user",
        "synthetic-session",
        {"note": "synthetic ordinary note"},
    )
    assert entry["user_id"].startswith("user_sha256:")
    assert entry["session_id"].startswith("session_sha256:")
    assert "synthetic ordinary note" not in str(entry["details"])
    summary = logger.get_public_pilot_safe_event_summary()
    assert summary["raw_event_json_included"] is False
    assert summary["raw_details_included"] is False


def test_github_feedback_template_contains_privacy_warning():
    text = Path(".github/ISSUE_TEMPLATE/feedback_request.yml").read_text()
    required = [
        "GitHub issues may be public",
        "Do not include secrets",
        "customer data",
        "private project data",
        "credentials",
        "tokens",
        "API keys",
        "addresses",
        "phone numbers",
        "sensitive personal data",
        "not testimonial consent",
        "not endorsement",
        "not product-readiness evidence",
        "approve roadmap",
        "promotion",
        "runtime behavior",
        "public claims",
    ]
    for phrase in required:
        assert phrase in text


def test_no_provider_model_search_advisor_calls_in_safety_helper():
    text = Path("weslr/public_pilot_storage_privacy_safety.py").read_text()
    forbidden_call_terms = ["requests.", "urllib", "openai", "anthropic", "provider_call", "search_call", "advisor_call"]
    assert not any(term in text for term in forbidden_call_terms)


def test_no_public_launch_authority_in_denied_authority():
    normalized = normalize_public_pilot_consent_metadata_v1(VALID_CONSENT)
    assert normalized["denied_authority"]["public_launch"] is False
    assert normalized["denied_authority"]["queue_processing"] is False
    assert normalized["denied_authority"]["runtime_behavior"] is False
    assert normalized["denied_authority"]["final_answer_behavior"] is False


def test_consolidation_public_pilot_mode_blocks_without_promotion_or_dot_weslr_io():
    result = auto_promote(
        {"cluster_id": "synthetic", "proposed_destination": "continuity_summary"},
        public_pilot_mode=True,
    )
    assert result.promoted is False
    assert result.record_written is False
    assert result.decision == "blocked"
    assert ".weslr" in ";".join(result.blocked_reasons)


def test_no_raw_json_db_row_reads_or_file_io_in_safety_helper():
    text = Path("weslr/public_pilot_storage_privacy_safety.py").read_text()
    assert "sqlite3" not in text
    assert "open(" not in text
    assert "json.load" not in text
