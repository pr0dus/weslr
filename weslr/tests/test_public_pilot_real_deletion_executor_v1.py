from __future__ import annotations

import json
from pathlib import Path

import pytest

from weslr.public_pilot_real_deletion_executor import (
    build_public_pilot_real_deletion_audit_event_v1,
    build_public_pilot_real_deletion_plan_v1,
    build_public_pilot_real_deletion_receipt_v1,
    classify_public_pilot_deletion_surface_v1,
    execute_public_pilot_real_deletion_plan_v1,
    redact_public_pilot_deletion_audit_metadata_v1,
    validate_public_pilot_real_deletion_plan_v1,
    validate_public_pilot_real_deletion_receipt_v1,
)


BASE_PLAN = {
    "requester": "person@example.invalid",
    "surface_scope": "suggestion_requests_json",
    "target_id": "record-alpha",
    "scope": ["contact", "suggestion"],
    "reason": "remove synthetic record",
    "operator_authorized": True,
    "dry_run": False,
    "test_safe_storage": True,
    "synthetic_temp_path": True,
    "future_real_execution_authorization": False,
    "denied_authority": {
        "queue_processing": False,
        "runtime_behavior": False,
        "final_answer_behavior": False,
        "public_launch": False,
        "promotion_approval": False,
    },
}


@pytest.mark.parametrize(
    "path, expected",
    [
        ("continuity/suggestion_box/requests.json", "suggestion_requests_json"),
        ("continuity/suggestion_box/continuity.json", "suggestion_continuity_json"),
        ("continuity/pilot_signals/user_events.json", "pilot_user_events_json"),
        ("continuity/pilot_signals/interventions.json", "pilot_interventions_json"),
        ("continuity/pilot_signals/redteam_events.json", "pilot_redteam_events_json"),
        ("review_queue.json", "review_queue_json"),
        (".weslr/advisor_review_queue.jsonl", "advisor_queue_jsonl"),
        ("synthetic/unknown.json", "unknown_or_blocked"),
    ],
)
def test_surface_classifier_labels(path: str, expected: str):
    assert classify_public_pilot_deletion_surface_v1(path) == expected


def test_valid_deletion_plan_passes(tmp_path: Path):
    plan = build_public_pilot_real_deletion_plan_v1({**BASE_PLAN, "path": str(tmp_path / "requests.json")})
    assert plan["validated"] is True
    assert plan["blocked"] is False
    assert plan["real_execution_allowed"] is False
    assert validate_public_pilot_real_deletion_plan_v1({**BASE_PLAN, "path": str(tmp_path / "requests.json")}) == []


@pytest.mark.parametrize(
    "patch, expected",
    [
        ({"operator_authorized": False}, "operator authorization is required"),
        ({"requester": None}, "requester metadata is required"),
        ({"surface_scope": None}, "surface scope metadata is required"),
        ({"target_id": None}, "target metadata id is required"),
        ({"scope": []}, "scope metadata is required"),
        ({"reason": None}, "reason metadata is required"),
    ],
)
def test_missing_required_plan_fields_block(patch, expected, tmp_path: Path):
    plan = {**BASE_PLAN, **patch, "path": str(tmp_path / "requests.json")}
    errors = validate_public_pilot_real_deletion_plan_v1(plan)
    assert expected in ";".join(errors)


def test_non_json_safe_metadata_blocks(tmp_path: Path):
    plan = {**BASE_PLAN, "path": str(tmp_path / "requests.json"), "bad": object()}
    errors = validate_public_pilot_real_deletion_plan_v1(plan)
    assert "JSON-safe" in ";".join(errors)


def test_true_denied_authority_field_blocks(tmp_path: Path):
    plan = {**BASE_PLAN, "path": str(tmp_path / "requests.json"), "denied_authority": {"public_launch": True}}
    errors = validate_public_pilot_real_deletion_plan_v1(plan)
    assert "public_launch" in ";".join(errors)


@pytest.mark.parametrize(
    "path, expected",
    [
        (".weslr/advisor_review_queue.jsonl", ".weslr path authority is denied"),
        ("continuity/suggestion_box/requests.json", "real continuity paths are blocked"),
        ("continuity/pilot_signals/user_events.json", "real continuity paths are blocked"),
        ("review_queue.json", "real continuity paths are blocked"),
        ("synthetic/records.sqlite", "blocked_db_surface_not_supported_v1"),
        ("synthetic/*.json", "glob deletion is denied"),
        ("synthetic/subdir/", "directory deletion is denied"),
        ("synthetic/../escape.json", "path traversal is denied"),
    ],
)
def test_path_blocks(path: str, expected: str):
    plan = {**BASE_PLAN, "path": path}
    errors = validate_public_pilot_real_deletion_plan_v1(plan)
    assert expected in ";".join(errors)


def test_unknown_surface_blocks(tmp_path: Path):
    plan = {**BASE_PLAN, "surface_scope": "unknown_or_blocked", "path": str(tmp_path / "unknown.json")}
    errors = validate_public_pilot_real_deletion_plan_v1(plan)
    assert "unknown or blocked surface scope" in ";".join(errors)


def test_audit_metadata_redaction_hides_raw_values():
    redacted = redact_public_pilot_deletion_audit_metadata_v1(
        {
            "requester": "person@example.invalid",
            "reason": "raw free text note",
            "path": "/tmp/synthetic/requests.json",
            "target_id": "record-alpha",
            "nested": {"feedback": "raw nested feedback"},
        }
    )
    encoded = json.dumps(redacted, sort_keys=True)
    assert "person@example.invalid" not in encoded
    assert "raw free text note" not in encoded
    assert "raw nested feedback" not in encoded
    assert "requester_label" in redacted
    assert "reason_label" in redacted


def test_dry_run_on_synthetic_json_returns_count_only_and_no_raw_content(tmp_path: Path):
    path = tmp_path / "requests.json"
    original = [
        {"record_id": "record-alpha", "note": "synthetic private text"},
        {"record_id": "record-beta", "note": "synthetic other text"},
    ]
    path.write_text(json.dumps(original, indent=2), encoding="utf-8")
    plan = {**BASE_PLAN, "path": str(path), "dry_run": True}
    result = execute_public_pilot_real_deletion_plan_v1(plan)
    assert result["dry_run"] is True
    assert result["matches_count"] == 1
    assert result["changed_count"] == 0
    assert json.loads(path.read_text(encoding="utf-8")) == original
    encoded = json.dumps(result, sort_keys=True)
    assert "record-alpha" not in encoded
    assert "synthetic private text" not in encoded
    assert validate_public_pilot_real_deletion_receipt_v1(result["receipt"]) == []


def test_execute_on_synthetic_json_removes_matching_record_only(tmp_path: Path):
    path = tmp_path / "requests.json"
    path.write_text(
        json.dumps(
            [
                {"record_id": "record-alpha", "note": "synthetic alpha"},
                {"record_id": "record-beta", "note": "synthetic beta"},
            ],
            indent=2,
        ),
        encoding="utf-8",
    )
    plan = {**BASE_PLAN, "path": str(path)}
    result = execute_public_pilot_real_deletion_plan_v1(plan)
    assert result["matches_count"] == 1
    assert result["changed_count"] == 1
    remaining = json.loads(path.read_text(encoding="utf-8"))
    assert [row["record_id"] for row in remaining] == ["record-beta"]


def test_execute_on_synthetic_json_object_collection_removes_matching_record_only(tmp_path: Path):
    path = tmp_path / "records.json"
    path.write_text(
        json.dumps(
            {
                "records": {
                    "record-alpha": {"record_id": "record-alpha", "note": "synthetic alpha"},
                    "record-beta": {"record_id": "record-beta", "note": "synthetic beta"},
                },
                "meta": {"kind": "synthetic_collection"},
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    plan = {**BASE_PLAN, "surface_scope": "suggestion_continuity_json", "path": str(path)}
    result = execute_public_pilot_real_deletion_plan_v1(plan)
    assert result["matches_count"] == 1
    assert result["changed_count"] == 1
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert "record-alpha" not in payload["records"]
    assert "record-beta" in payload["records"]


def test_execute_on_synthetic_jsonl_suppresses_matching_event_only(tmp_path: Path):
    path = tmp_path / "events.jsonl"
    path.write_text(
        "\n".join(
            [
                json.dumps({"event_id": "event-alpha", "note": "synthetic alpha"}),
                json.dumps({"event_id": "event-beta", "note": "synthetic beta"}),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    plan = {**BASE_PLAN, "surface_scope": "advisor_queue_jsonl", "path": str(path), "target_id": "event-alpha"}
    result = execute_public_pilot_real_deletion_plan_v1(plan)
    assert result["matches_count"] == 1
    assert result["changed_count"] == 1
    lines = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert [line["event_id"] for line in lines] == ["event-beta"]


def test_receipt_and_audit_event_contain_no_raw_private_values(tmp_path: Path):
    path = tmp_path / "requests.json"
    path.write_text(
        json.dumps(
            [
                {
                    "record_id": "record-alpha",
                    "note": "raw feedback suggestion project text",
                    "contact_email": "person@example.invalid",
                }
            ],
            indent=2,
        ),
        encoding="utf-8",
    )
    plan = {**BASE_PLAN, "path": str(path), "reason": "remove raw feedback suggestion project text"}
    result = execute_public_pilot_real_deletion_plan_v1(plan)
    receipt = result["receipt"]
    audit_event = result["audit_event"]
    encoded = json.dumps({"receipt": receipt, "audit_event": audit_event}, sort_keys=True)
    assert "person@example.invalid" not in encoded
    assert "raw feedback suggestion project text" not in encoded
    assert receipt["raw_user_text_included"] is False
    assert receipt["raw_contact_value_included"] is False
    assert audit_event["raw_user_text_included"] is False
    assert audit_event["raw_contact_value_included"] is False
    assert validate_public_pilot_real_deletion_receipt_v1(receipt) == []


def test_no_provider_model_search_advisor_calls_in_executor_source():
    text = Path("weslr/public_pilot_real_deletion_executor.py").read_text(encoding="utf-8")
    forbidden_terms = ["openai", "anthropic", "provider_call", "search_call", "advisor_call", "queue_processing()"]
    assert not any(term in text for term in forbidden_terms)


def test_execute_blocked_by_real_continuity_path_strings_without_opening(tmp_path: Path):
    plan = {**BASE_PLAN, "path": "continuity/suggestion_box/requests.json"}
    result = execute_public_pilot_real_deletion_plan_v1(plan)
    assert result["blocked"] is True
    assert "real continuity paths are blocked" in ";".join(result["validation_errors"])
