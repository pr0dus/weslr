from __future__ import annotations

import json


from weslr.arc_synthetic_official_shape_blind_projection import (
    BLIND_BATCH_COUNT_V1,
    BLIND_BATCH_SEEDS_V1,
    BLIND_TASKS_PER_BATCH_V1,
    build_arc_synthetic_official_shape_blind_projection_bundle_v1,
    project_blind_task_packet_v1,
    validate_arc_synthetic_official_shape_blind_task_packet_v1,
)


FORBIDDEN_TOKENS = (
    "family_id",
    "variant",
    "toy_task_type",
    "primitive",
    "reflect",
    "rotate",
    "transform",
    "label",
    "expected_output",
    "source_task_id",
)


def test_blind_projection_bundle_is_deterministic_and_anonymized(tmp_path) -> None:
    bundle = build_arc_synthetic_official_shape_blind_projection_bundle_v1()
    assert bundle == build_arc_synthetic_official_shape_blind_projection_bundle_v1()
    assert bundle["synthetic_only"] is True
    assert bundle["official_data_touched"] is False
    assert bundle["public_data_touched"] is False
    assert bundle["network_touched"] is False
    assert bundle["batch_count"] == BLIND_BATCH_COUNT_V1
    assert bundle["task_count"] == BLIND_BATCH_COUNT_V1 * BLIND_TASKS_PER_BATCH_V1
    assert bundle["seeds"] == list(BLIND_BATCH_SEEDS_V1)
    assert len(bundle["family_manifest"]) == BLIND_BATCH_COUNT_V1
    assert all(entry["task_count"] == BLIND_TASKS_PER_BATCH_V1 for entry in bundle["family_manifest"])

    first_task = bundle["batches"][0]["selected_tasks"][0]
    visible_packet = project_blind_task_packet_v1(first_task, batch_index=0, batch_seed=bundle["seeds"][0], batch_task_index=0)
    validation = validate_arc_synthetic_official_shape_blind_task_packet_v1(visible_packet)
    assert validation["valid"] is True
    assert "family_id" not in visible_packet
    assert "variant_index" not in visible_packet
    assert "expected_output" not in visible_packet

    serialized = json.dumps(visible_packet, ensure_ascii=False, sort_keys=True)
    assert all(token not in serialized.lower() for token in FORBIDDEN_TOKENS)

    out_path = tmp_path / "blind-visible-packet.json"
    out_path.write_text(serialized)
    assert all(token not in out_path.read_text().lower() for token in FORBIDDEN_TOKENS)


def test_blind_projection_validator_rejects_semantic_leakage() -> None:
    packet = {
        "task_id": "blind_00_00",
        "train_pairs": [],
        "test_input": [],
        "grid_format": {"format_id": "grid_v1"},
        "palette": {},
        "family_id": "reflect_object_horizontal_or_vertical",
    }
    validation = validate_arc_synthetic_official_shape_blind_task_packet_v1(packet)
    assert validation["valid"] is False
    assert "semantic_metadata_visible_to_solver" in validation["blocked_reason_labels"]
