from __future__ import annotations

import json
import subprocess
from copy import deepcopy
from pathlib import Path

import pytest

import weslr.reverse_calibration_trace as reverse_trace
from weslr.reverse_calibration_trace import (
    build_initial_reverse_calibration_trace_examples_v1,
    build_reverse_calibration_trace_packet_v1,
    build_reverse_calibration_trace_phase_v1,
    summarize_reverse_calibration_trace_packet_v1,
    to_reverse_calibration_trace_json_safe_v1,
    validate_reverse_calibration_trace_packet_v1,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
HELPER_PATH = Path(__file__).resolve().parents[1] / "reverse_calibration_trace.py"
PROTECTED_FILES = {
    "weslr/chat_responder.py",
    "weslr/main.py",
    "main.py",
    "dialogue.py",
    "chat_ui.py",
}


def _canonical_packet():
    examples = build_initial_reverse_calibration_trace_examples_v1()
    assert examples
    return deepcopy(next(packet for packet in examples if packet["trace_id"] == "pulsar_reverse_calibration_trace"))


def _base_phase():
    return build_reverse_calibration_trace_phase_v1(
        {
            "phase_id": "unit_phase",
            "phase_signal_summary": "unit test phase summary",
            "expected_forward_next_step": "probe",
            "why_this_step": "unit test rationale",
            "why_not_calibrate": "unit test no calibrate",
            "why_not_archive": "unit test no archive",
            "why_not_claim": "unit test no claim",
            "disconfirming_signal": "unit test disconfirming signal",
            "required_next_evidence": "unit test next evidence",
            "selector_bridge_comparison": "unit test bridge comparison",
            "mismatch_if_any": "none",
            "calibration_lesson": "unit test lesson",
        }
    )


def _mutated_packet(**overrides):
    packet = _canonical_packet()
    packet.update(overrides)
    return packet


def test_canonical_pulsar_trace_builds():
    packet = _canonical_packet()
    assert packet["trace_id"] == "pulsar_reverse_calibration_trace"
    assert packet["source_case_id"] == "pulsar_historical_outcome"
    assert len(packet["phases"]) == 5
    assert packet["phases"][0]["expected_forward_next_step"] == "probe"
    assert packet["phases"][1]["expected_forward_next_step"] == "pressure_test"
    assert packet["phases"][2]["expected_forward_next_step"] == "calibrate"
    assert packet["phases"][3]["expected_forward_next_step"] == "archive"
    assert packet["phases"][4]["expected_forward_next_step"] == "blocked_by_safety"


def test_canonical_trace_validates():
    validation = validate_reverse_calibration_trace_packet_v1(_canonical_packet())
    assert validation["valid"] is True
    assert validation["blocked"] is False
    assert validation["validation_posture"] == "valid"


def test_canonical_trace_summarizes():
    summary = summarize_reverse_calibration_trace_packet_v1(_canonical_packet())
    assert summary["trace_id"] == "pulsar_reverse_calibration_trace"
    assert summary["source_case_id"] == "pulsar_historical_outcome"
    assert summary["phase_count"] == 5
    assert summary["validation_posture"] == "valid"
    assert summary["next_step_distribution"]["probe"] == 1
    assert summary["next_step_distribution"]["pressure_test"] == 1
    assert summary["next_step_distribution"]["calibrate"] == 1
    assert summary["next_step_distribution"]["archive"] == 1
    assert summary["next_step_distribution"]["blocked_by_safety"] == 1
    assert summary["mismatch_count"] == 1
    assert summary["blocked_safety_count"] == 1


def test_canonical_trace_json_serializes_with_json_dumps():
    assert json.dumps(to_reverse_calibration_trace_json_safe_v1(_canonical_packet()), sort_keys=True)


def test_next_step_distribution_includes_required_labels():
    keys = set(summarize_reverse_calibration_trace_packet_v1(_canonical_packet())["next_step_distribution"])
    assert {"probe", "pressure_test", "calibrate", "blocked_by_safety"}.issubset(keys)
    assert "archive" in keys or "operator_review" in keys


@pytest.mark.parametrize(
    "mutation, expected_label",
    [
        ({"trace_id": ""}, "missing_trace_id"),
        ({"known_outcome_summary": ""}, "missing_known_outcome"),
        ({"phases": [{"phase_signal_summary": "x"}]}, "missing_phase_id"),
        ({"phases": [build_reverse_calibration_trace_phase_v1({**_base_phase(), "expected_forward_next_step": "bogus"})]}, "invalid_next_step_label"),
        ({"phases": [{**_base_phase(), "why_this_step": ""}]}, "missing_why_this_step"),
        ({"phases": [{**_base_phase(), "why_not_claim": ""}]}, "missing_why_not_claim"),
        ({"authority_status": {**_canonical_packet()["authority_status"], "public_claim_authorized": True}}, "unsafe_public_claim_authorized"),
        ({"authority_status": {**_canonical_packet()["authority_status"], "final_answer_authority": True}}, "unsafe_final_answer_authority"),
        ({"authority_status": {**_canonical_packet()["authority_status"], "runtime_authorized": True}}, "unsafe_runtime_authorized"),
        ({"authority_status": {**_canonical_packet()["authority_status"], "source_ingestion_authorized": True}}, "unsafe_source_ingestion_authorized"),
        ({"authority_status": {**_canonical_packet()["authority_status"], "provider_model_call_authority": True}}, "unsafe_provider_model_call_authority"),
        ({"authority_status": {**_canonical_packet()["authority_status"], "web_authority": True}}, "unsafe_web_authority"),
        ({"authority_status": {**_canonical_packet()["authority_status"], "weslr_io_authorized": True}}, "unsafe_weslr_io_authorized"),
        ({"authority_status": {**_canonical_packet()["authority_status"], "weslr_read_authorized": True}}, "unsafe_weslr_read_authorized"),
        ({"authority_status": {**_canonical_packet()["authority_status"], "weslr_write_authorized": True}}, "unsafe_weslr_write_authorized"),
        ({"authority_status": {**_canonical_packet()["authority_status"], "weslr_persistence_authorized": True}}, "unsafe_weslr_persistence_authorized"),
        ({"authority_status": {**_canonical_packet()["authority_status"], "database_write_authorized": True}}, "unsafe_database_write_authorized"),
        ({"authority_status": {**_canonical_packet()["authority_status"], "memory_mutation_authorized": True}}, "unsafe_memory_mutation_authorized"),
        ({"authority_status": {**_canonical_packet()["authority_status"], "project_mutation_authorized": True}}, "unsafe_project_mutation_authorized"),
        ({"authority_status": {**_canonical_packet()["authority_status"], "boundary_notes": "public claim authorized discovery proof"}}, "unsafe_authority_text"),
        ({"known_outcome_authority_status": {**_canonical_packet()["known_outcome_authority_status"], "boundary_notes": "discovery proof public claim authorized"}}, "unsafe_known_outcome_authority_text"),
        ({"safe_metadata": {**_canonical_packet()["safe_metadata"], "trace_family": "other_family"}}, "unsafe_safe_metadata_trace_family"),
        ({"phases": [{**_base_phase(), "why_this_step": "hidden prompt"}]}, "forbidden_hidden_private_protected_marker"),
        ({"phases": [{**_base_phase(), "selector_bridge_comparison": {"bad": {1, 2}}}]}, "non_json_safe_output"),
    ],
)
def test_validation_fail_closed_cases(mutation, expected_label):
    packet = _canonical_packet()
    packet.update(mutation)
    validation = validate_reverse_calibration_trace_packet_v1(packet)
    assert validation["blocked"] is True
    assert expected_label in validation["blocked_labels"]


def test_neutral_historical_scientific_known_outcome_wording_is_allowed():
    packet = _canonical_packet()
    packet["known_outcome_summary"] = "Historical scientific note: pulsars were later recognized as real astronomical objects."
    validation = validate_reverse_calibration_trace_packet_v1(packet)
    assert validation["blocked"] is False


def test_neutral_discovery_history_wording_is_allowed_only_as_known_outcome_metadata():
    packet = _canonical_packet()
    packet["known_outcome_summary"] = "Discovery-history note: pulsars were later recognized as real astronomical objects."
    validation = validate_reverse_calibration_trace_packet_v1(packet)
    assert validation["blocked"] is False


def test_live_unauthorized_discovery_claim_wording_fails_in_authority_bearing_fields():
    packet = _canonical_packet()
    packet["authority_status"]["boundary_notes"] = "discovery proof public claim authorized final answer authority"
    validation = validate_reverse_calibration_trace_packet_v1(packet)
    assert validation["blocked"] is True


def test_helper_does_not_import_runtime_provider_tool_web_modules():
    source = HELPER_PATH.read_text()
    forbidden = (
        "import weslr.runtime",
        "import weslr.provider",
        "import weslr.tool",
        "import weslr.web",
        "from weslr import runtime",
        "from weslr import provider",
        "from weslr import tool",
        "from weslr import web",
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
