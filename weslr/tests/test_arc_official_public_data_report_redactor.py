from __future__ import annotations

import json

from weslr.arc_official_public_data_report_redactor import redact_arc_official_public_report_payload_v1


def test_report_redactor_strips_forbidden_fields_and_preserves_checksum_provenance() -> None:
    payload = {
        "aggregate_score": 2,
        "source_checksum": "sha256:abc",
        "provenance": {"source_location": "dummy.json", "checksum": "sha256:abc"},
        "task_results": [
            {
                "task_id": "anon_dummy_000",
                "expected_output": [[1, 2]],
                "reference_grid": [[1, 2]],
                "raw_task_json": {"train": []},
                "latent_rule": "copy_input",
                "answer_descriptor": "copy",
                "metadata": {"checksum": "sha256:abc"},
            }
        ],
        "summary_text": "expected_output reference_grid raw_task_json latent_rule answer_descriptor",
    }
    redacted = redact_arc_official_public_report_payload_v1(payload)
    text = json.dumps(redacted, ensure_ascii=False).lower()
    assert "expected_output" not in text
    assert "reference_grid" not in text
    assert "raw_task_json" not in text
    assert "latent_rule" not in text
    assert "answer_descriptor" not in text
    assert redacted["aggregate_score"] == 2
    assert redacted["source_checksum"] == "sha256:abc"
    assert redacted["provenance"]["checksum"] == "sha256:abc"
    assert redacted["task_results"][0]["metadata"]["checksum"] == "sha256:abc"


def test_report_redactor_redacts_forbidden_strings() -> None:
    payload = "expected_output hidden answer latent rule"
    redacted = redact_arc_official_public_report_payload_v1(payload)
    assert redacted == "[redacted]"
