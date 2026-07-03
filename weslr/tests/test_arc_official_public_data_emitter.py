from __future__ import annotations

import json

import pytest

from weslr.arc_official_public_data_adapter import load_arc_official_public_dummy_no_data_bundle_v1
from weslr.arc_official_public_data_emitter import (
    build_arc_official_public_candidate_grids_v1,
    emit_arc_official_public_two_output_packet_v1,
    infer_dummy_public_rule_v1,
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


def test_emitter_enforces_exactly_two_outputs() -> None:
    bundle = load_arc_official_public_dummy_no_data_bundle_v1()
    packet = bundle["solver_visible_tasks"][0]
    emission = emit_arc_official_public_two_output_packet_v1(solver_visible_packet=packet)
    assert emission["attempt_count"] == 2
    assert len(emission["top2_packet"]["attempts"]) == 2
    assert emission["top2_packet"]["metadata"]["exact_two_output_required"] is True


def test_emitter_rejects_non_grid_candidates() -> None:
    bundle = load_arc_official_public_dummy_no_data_bundle_v1()
    packet = dict(bundle["solver_visible_tasks"][0])
    packet["test_inputs"] = [{"input_grid": "not-a-grid"}]
    with pytest.raises(ValueError):
        build_arc_official_public_candidate_grids_v1(solver_visible_packet=packet)


def test_emitter_infers_dummy_rule_from_train_pairs_only() -> None:
    bundle = load_arc_official_public_dummy_no_data_bundle_v1()
    first = bundle["solver_visible_tasks"][0]
    second = bundle["solver_visible_tasks"][1]
    assert infer_dummy_public_rule_v1(train_pairs=first["train_pairs"]) == "copy_input"
    assert infer_dummy_public_rule_v1(train_pairs=second["train_pairs"]) == "invert_binary"


def test_emitted_packet_is_metadata_safe() -> None:
    bundle = load_arc_official_public_dummy_no_data_bundle_v1()
    packet = bundle["solver_visible_tasks"][1]
    emission = emit_arc_official_public_two_output_packet_v1(solver_visible_packet=packet)
    serialized = json.dumps(emission, ensure_ascii=False).lower()
    assert all(token not in serialized for token in FORBIDDEN_TOKENS)
