from __future__ import annotations

import json
import subprocess
from copy import deepcopy
from pathlib import Path

import pytest

import weslr.real_findings_evidence_intake as intake
from weslr.real_findings_evidence_intake import (
    allowed_evidence_access_statuses_v1,
    allowed_evidence_confidence_postures_v1,
    allowed_evidence_source_kinds_v1,
    allowed_proposed_direction_eligibility_v1,
    build_initial_real_findings_evidence_intake_examples_v1,
    build_real_findings_evidence_intake_packet_v1,
    summarize_real_findings_evidence_intake_packet_v1,
    to_real_findings_evidence_intake_json_safe_v1,
    validate_real_findings_evidence_intake_packet_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
HELPER_PATH = Path(__file__).resolve().parents[1] / "real_findings_evidence_intake.py"
PROTECTED_FILES = {
    "weslr/chat_responder.py",
    "weslr/main.py",
    "main.py",
    "dialogue.py",
    "chat_ui.py",
}

CANONICAL_EVIDENCE_INTAKE_ID = "owner_observed_repeating_signal_intake"


def _canonical_examples():
    return deepcopy(build_initial_real_findings_evidence_intake_examples_v1())


def _canonical_packet():
    examples = _canonical_examples()
    assert len(examples) >= 1
    packet = next(item for item in examples if item["evidence_intake_id"] == CANONICAL_EVIDENCE_INTAKE_ID)
    return deepcopy(packet)


def test_required_apis_exist():
    names = [
        "allowed_evidence_source_kinds_v1",
        "allowed_evidence_access_statuses_v1",
        "allowed_evidence_confidence_postures_v1",
        "allowed_proposed_direction_eligibility_v1",
        "build_real_findings_evidence_intake_packet_v1",
        "validate_real_findings_evidence_intake_packet_v1",
        "summarize_real_findings_evidence_intake_packet_v1",
        "to_real_findings_evidence_intake_json_safe_v1",
        "build_initial_real_findings_evidence_intake_examples_v1",
    ]
    for name in names:
        assert hasattr(intake, name)
        assert callable(getattr(intake, name))


def test_allowed_labels_are_exact():
    assert allowed_evidence_source_kinds_v1() == (
        "public_open_source",
        "owner_supplied_document",
        "owner_supplied_observation",
        "synthetic_example",
        "known_science_replay",
        "internal_project_artifact",
        "blocked_private_source",
        "unknown_source",
    )
    assert allowed_evidence_access_statuses_v1() == (
        "not_accessed",
        "metadata_only",
        "owner_supplied_summary",
        "future_access_requires_review",
        "blocked",
        "needs_repair",
    )
    assert allowed_evidence_confidence_postures_v1() == (
        "unassessed",
        "weak_signal",
        "moderate_signal",
        "strong_signal_requires_pressure_test",
        "conflicting_signal",
        "insufficient_context",
        "blocked_by_safety",
    )
    assert allowed_proposed_direction_eligibility_v1() == (
        "not_eligible",
        "eligible_for_candidate_direction",
        "eligible_after_probe",
        "eligible_after_pressure_test",
        "operator_review_required",
        "blocked_by_safety",
        "needs_repair",
    )


def test_canonical_example_builds():
    examples = build_initial_real_findings_evidence_intake_examples_v1()
    assert len(examples) >= 1
    packet = next(item for item in examples if item["evidence_intake_id"] == CANONICAL_EVIDENCE_INTAKE_ID)
    assert packet["source_kind"] == "owner_supplied_observation"
    assert packet["source_access_status"] == "metadata_only"
    assert packet["raw_content_retained"] is False
    assert packet["confidence_posture"] == "strong_signal_requires_pressure_test"
    assert packet["proposed_direction_eligibility"] == "eligible_after_pressure_test"
    assert packet["reverse_trace_reference"] == "pulsar_reverse_calibration_trace"
    assert packet["calibration_axes_to_apply"] == [
        "signal_detection_calibration",
        "popper_falsification_calibration",
        "bayesian_calibration",
        "reverse_calibration_backcasting",
    ]


def test_canonical_example_validates_and_summarizes():
    packet = _canonical_packet()
    validation = validate_real_findings_evidence_intake_packet_v1(packet)
    summary = summarize_real_findings_evidence_intake_packet_v1(packet)

    assert validation["valid"] is True
    assert validation["blocked"] is False
    assert validation["validation_posture"] == "valid"
    assert summary["evidence_intake_id"] == CANONICAL_EVIDENCE_INTAKE_ID
    assert summary["source_kind"] == "owner_supplied_observation"
    assert summary["source_access_status"] == "metadata_only"
    assert summary["confidence_posture"] == "strong_signal_requires_pressure_test"
    assert summary["proposed_direction_eligibility"] == "eligible_after_pressure_test"
    assert summary["raw_content_retained"] is False
    assert summary["calibration_axes_count"] == 4
    assert summary["validation_posture"] == "valid"


def test_canonical_example_json_serializes_with_json_dumps():
    packet = _canonical_packet()
    safe = to_real_findings_evidence_intake_json_safe_v1(packet)
    assert json.dumps(safe, sort_keys=True)


def test_canonical_example_is_metadata_only_and_preserves_key_fields():
    packet = _canonical_packet()
    assert packet["source_access_status"] == "metadata_only"
    assert packet["raw_content_retained"] is False
    assert packet["known_limitations"]
    assert packet["missing_context"]
    assert packet["disconfirming_signal"]
    assert packet["promotion_blockers"]
    assert packet["forbidden_interpretations"]
    assert packet["authority_status"]["all_authority_flags_false"] is True
    assert packet["authority_status"]["status"] == "metadata_only"
    assert packet["safe_metadata"]["safe"] is True
    assert packet["safe_metadata"]["metadata_only"] is True
    assert packet["safe_metadata"]["no_raw_content_retention"] is True


def test_canonical_example_preserves_known_limitations_missing_context_and_disconfirming_signal():
    packet = _canonical_packet()
    assert "No independent confirmation yet" in packet["known_limitations"]
    assert "Independent confirmation" in packet["missing_context"]
    assert any("noise" in item.lower() or "weaken" in item.lower() for item in packet["disconfirming_signal"])


def test_canonical_example_preserves_calibration_axes_and_reverse_trace_reference():
    packet = _canonical_packet()
    assert packet["reverse_trace_reference"] == "pulsar_reverse_calibration_trace"
    assert packet["calibration_axes_to_apply"] == [
        "signal_detection_calibration",
        "popper_falsification_calibration",
        "bayesian_calibration",
        "reverse_calibration_backcasting",
    ]


def test_canonical_example_preserves_proposed_direction_eligibility_and_promotion_blockers():
    packet = _canonical_packet()
    assert packet["proposed_direction_eligibility"] == "eligible_after_pressure_test"
    assert packet["promotion_blockers"] == [
        "Missing independent confirmation",
        "No falsifying test yet",
        "No operator review for higher authority",
    ]


def test_canonical_example_preserves_forbidden_interpretations():
    packet = _canonical_packet()
    expected = {
        "this is proven",
        "this is discovered",
        "this is public truth",
        "this is a final answer",
        "this authorizes ingestion",
        "this authorizes runtime",
        "this authorizes provider/tool/web use",
        "this authorizes .weslr access",
        "this authorizes persistence",
    }
    assert expected.issubset(set(packet["forbidden_interpretations"]))


def test_canonical_example_preserves_fail_closed_authority_status():
    packet = _canonical_packet()
    assert packet["authority_status"]["all_authority_flags_false"] is True
    assert packet["authority_status"]["runtime_authorized"] is False
    assert packet["authority_status"]["source_ingestion_authorized"] is False
    assert packet["authority_status"]["public_claim_authorized"] is False
    assert packet["authority_status"]["final_answer_authority"] is False
    assert packet["authority_status"]["provider_model_call_authority"] is False
    assert packet["authority_status"]["tool_execution_authority"] is False
    assert packet["authority_status"]["web_authority"] is False
    assert packet["authority_status"]["weslr_io_authorized"] is False
    assert packet["authority_status"]["raw_content_retention_authorized"] is False


@pytest.mark.parametrize(
    "field",
    [
        "evidence_intake_id",
        "source_scope",
        "source_kind",
        "source_reference_summary",
        "source_access_status",
        "evidence_signal_summary",
        "observed_pattern",
        "reverse_trace_reference",
        "confidence_posture",
        "proposed_direction_eligibility",
        "operator_review_need",
        "privacy_sensitivity",
        "safety_sensitivity",
    ],
)
def test_fail_closed_on_missing_required_text_fields(field):
    packet = _canonical_packet()
    packet.pop(field, None)
    validation = validate_real_findings_evidence_intake_packet_v1(packet)
    assert validation["blocked"] is True
    assert f"missing_{field}" in validation["blocked_labels"]


@pytest.mark.parametrize(
    "field, value, expected_label",
    [
        ("source_kind", "bogus", "invalid_source_kind"),
        ("source_access_status", "bogus", "invalid_source_access_status"),
        ("confidence_posture", "bogus", "invalid_confidence_posture"),
        ("proposed_direction_eligibility", "bogus", "invalid_proposed_direction_eligibility"),
        ("raw_content_retained", "nope", "invalid_raw_content_retained"),
    ],
)
def test_fail_closed_on_status_enums_and_raw_content_flag(field, value, expected_label):
    packet = _canonical_packet()
    packet[field] = value
    validation = validate_real_findings_evidence_intake_packet_v1(packet)
    assert validation["blocked"] is True
    assert expected_label in validation["blocked_labels"]


@pytest.mark.parametrize(
    "field",
    [
        "known_limitations",
        "missing_context",
        "calibration_axes_to_apply",
        "disconfirming_signal",
        "promotion_blockers",
        "forbidden_interpretations",
    ],
)
def test_fail_closed_on_missing_required_lists(field):
    packet = _canonical_packet()
    packet.pop(field, None)
    validation = validate_real_findings_evidence_intake_packet_v1(packet)
    assert validation["blocked"] is True
    assert f"missing_{field}" in validation["blocked_labels"]


def test_fail_closed_on_raw_content_retained_true_without_explicit_authorization():
    packet = _canonical_packet()
    packet["raw_content_retained"] = True
    packet["authority_status"]["raw_content_retention_authorized"] = False
    validation = validate_real_findings_evidence_intake_packet_v1(packet)
    assert validation["blocked"] is True
    assert "raw_content_retained_without_explicit_authorization" in validation["blocked_labels"]


def test_fail_closed_on_raw_content_retained_true_with_explicit_authorization_field_still_preserves_validation_surface():
    packet = _canonical_packet()
    packet["raw_content_retained"] = True
    packet["authority_status"]["raw_content_retention_authorized"] = True
    validation = validate_real_findings_evidence_intake_packet_v1(packet)
    assert validation["blocked"] is False


@pytest.mark.parametrize(
    "field, expected_label",
    [
        ("runtime_authorized", "unsafe_authority_flag:runtime_authorized"),
        ("source_ingestion_authorized", "unsafe_authority_flag:source_ingestion_authorized"),
        ("public_claim_authorized", "unsafe_authority_flag:public_claim_authorized"),
        ("final_answer_authority", "unsafe_authority_flag:final_answer_authority"),
        ("provider_model_call_authority", "unsafe_authority_flag:provider_model_call_authority"),
        ("provider_authority", "unsafe_authority_flag:provider_authority"),
        ("model_authority", "unsafe_authority_flag:model_authority"),
        ("tool_execution_authority", "unsafe_authority_flag:tool_execution_authority"),
        ("retrieval_tool_authority", "unsafe_authority_flag:retrieval_tool_authority"),
        ("web_authority", "unsafe_authority_flag:web_authority"),
        ("weslr_io_authorized", "unsafe_authority_flag:weslr_io_authorized"),
        ("weslr_read_authorized", "unsafe_authority_flag:weslr_read_authorized"),
        ("weslr_write_authorized", "unsafe_authority_flag:weslr_write_authorized"),
        ("weslr_persistence_authorized", "unsafe_authority_flag:weslr_persistence_authorized"),
        ("database_write_authorized", "unsafe_authority_flag:database_write_authorized"),
        ("memory_mutation_authorized", "unsafe_authority_flag:memory_mutation_authorized"),
        ("project_mutation_authorized", "unsafe_authority_flag:project_mutation_authorized"),
        ("hidden_private_protected_authorized", "unsafe_authority_flag:hidden_private_protected_authorized"),
        ("cross_user_leakage_authorized", "unsafe_authority_flag:cross_user_leakage_authorized"),
        ("public_science_claim_authorized", "unsafe_authority_flag:public_science_claim_authorized"),
        ("proof_claim_authorized", "unsafe_authority_flag:proof_claim_authorized"),
        ("benchmark_claim_authorized", "unsafe_authority_flag:benchmark_claim_authorized"),
        ("agi_claim_authorized", "unsafe_authority_flag:agi_claim_authorized"),
        ("automatic_discovery_authorized", "unsafe_authority_flag:automatic_discovery_authorized"),
    ],
)
def test_fail_closed_on_unsafe_authority_flags(field, expected_label):
    packet = _canonical_packet()
    packet["authority_status"][field] = True
    validation = validate_real_findings_evidence_intake_packet_v1(packet)
    assert validation["blocked"] is True
    assert expected_label in validation["blocked_labels"]


def test_fail_closed_on_missing_or_invalid_safe_metadata():
    packet = _canonical_packet()
    packet["safe_metadata"]["no_raw_content_retention"] = False
    validation = validate_real_findings_evidence_intake_packet_v1(packet)
    assert validation["blocked"] is True
    assert "unsafe_safe_metadata_flag:no_raw_content_retention" in validation["blocked_labels"]


def test_fail_closed_on_public_discovery_proof_agi_final_answer_wording_in_authority_fields():
    packet = _canonical_packet()
    packet["authority_status"]["boundary_notes"] = "discovery proof AGI final answer public claim authorized"
    validation = validate_real_findings_evidence_intake_packet_v1(packet)
    assert validation["blocked"] is True
    assert any(label in validation["blocked_labels"] for label in ("unsafe_authority_text", "unsafe_safe_metadata_text"))


def test_neutral_source_and_evidence_metadata_wording_is_allowed():
    packet = _canonical_packet()
    packet["source_reference_summary"] = "Historical discovery replay note about a repeated observation pattern."
    packet["evidence_signal_summary"] = "Scientific-historical note: the repeated signal is still only metadata."
    validation = validate_real_findings_evidence_intake_packet_v1(packet)
    assert validation["blocked"] is False


def test_fail_closed_on_hidden_private_protected_markers():
    packet = _canonical_packet()
    packet["evidence_signal_summary"] = "hidden prompt with secret api key"
    validation = validate_real_findings_evidence_intake_packet_v1(packet)
    assert validation["blocked"] is True
    assert "forbidden_hidden_private_protected_marker" in validation["blocked_labels"]


def test_fail_closed_on_non_json_safe_output():
    packet = _canonical_packet()
    packet["safe_metadata"]["callable"] = lambda: None
    validation = validate_real_findings_evidence_intake_packet_v1(packet)
    assert validation["blocked"] is True
    assert "non_json_safe_output" in validation["blocked_labels"]
    assert json.dumps(to_real_findings_evidence_intake_json_safe_v1(packet), sort_keys=True)


def test_helper_does_not_import_runtime_provider_tool_web_source_ingestion_modules():
    source = HELPER_PATH.read_text()
    forbidden = (
        "import weslr.runtime",
        "import weslr.provider",
        "import weslr.tool",
        "import weslr.web",
        "import weslr.source_ingestion",
        "from weslr import runtime",
        "from weslr import provider",
        "from weslr import tool",
        "from weslr import web",
        "from weslr import source_ingestion",
    )
    assert not any(marker in source for marker in forbidden)


def test_protected_files_remain_untouched():
    completed = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "status", "--short", "--untracked-files=no"],
        check=True,
        capture_output=True,
        text=True,
    )
    changed = {
        line.split(maxsplit=1)[1]
        for line in completed.stdout.splitlines()
        if line.strip()
    }
    assert not changed.intersection(PROTECTED_FILES)
