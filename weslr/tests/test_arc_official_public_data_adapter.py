from __future__ import annotations

import json
from pathlib import Path

import pytest

from weslr.arc_official_public_data_adapter import (
    DUMMY_FIXTURE_RELATIVE_PATH_V1,
    build_arc_official_public_dummy_approval_manifest_v1,
    load_arc_official_public_dummy_no_data_bundle_v1,
    open_dummy_fixture_source_path_v1,
    reject_official_public_source_path_v1,
    validate_arc_official_public_dummy_approval_manifest_v1,
    validate_solver_visible_packet_v1,
)


FORBIDDEN_TOKENS = (
    "expected_output",
    "reference_output",
    "latent_rule",
    "answer_descriptor",
    "toy_task_type",
    "family_id",
    "source_task_id",
)


def test_adapter_rejects_missing_approval() -> None:
    with pytest.raises(ValueError):
        validate_arc_official_public_dummy_approval_manifest_v1(None)


def test_adapter_rejects_invalid_manifest_checksum() -> None:
    manifest = build_arc_official_public_dummy_approval_manifest_v1()
    manifest["checksum"] = "sha256:wrong"
    with pytest.raises(ValueError):
        validate_arc_official_public_dummy_approval_manifest_v1(manifest)


def test_adapter_does_not_expose_expected_outputs_to_solver_visible_packet() -> None:
    bundle = load_arc_official_public_dummy_no_data_bundle_v1()
    packet = bundle["solver_visible_tasks"][0]
    validation = validate_solver_visible_packet_v1(packet)
    assert validation["valid"] is True
    assert packet["required_output_count"] == 2
    assert packet["source_kind"] == "dummy_no_data_fixture_v1"
    assert "reference_output" not in packet
    assert "expected_output" not in packet
    serialized = json.dumps(packet, ensure_ascii=False).lower()
    assert all(token not in serialized for token in FORBIDDEN_TOKENS)


def test_adapter_solver_visible_packet_contains_only_allowed_fields() -> None:
    bundle = load_arc_official_public_dummy_no_data_bundle_v1()
    packet = bundle["solver_visible_tasks"][0]
    allowed = {
        "task_id",
        "anonymized_task_id",
        "train_pairs",
        "test_inputs",
        "required_output_count",
        "format_metadata",
        "parse_status",
        "source_kind",
        "packet_metadata",
    }
    assert set(packet.keys()) == allowed


def test_adapter_rejects_official_public_source_path_in_this_lane() -> None:
    with pytest.raises(PermissionError):
        reject_official_public_source_path_v1(Path("/data/data/com.termux/files/home/weslr-pr47-clean/official/public/arc.json"))
    with pytest.raises(PermissionError):
        open_dummy_fixture_source_path_v1(Path("/data/data/com.termux/files/home/weslr-pr47-clean/official/public/arc.json"))


def test_dummy_fixture_path_is_the_only_allowed_source_location() -> None:
    manifest = build_arc_official_public_dummy_approval_manifest_v1()
    assert manifest["source_location"] == str(DUMMY_FIXTURE_RELATIVE_PATH_V1)
