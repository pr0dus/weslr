# Test suite for Real Evidence Packet Schema

import pytest
from weslr.real_evidence_packet_schema import validate_packet, RealEvidenceSchemaError


def valid_packet_dict():
    return {
        "packet_id": "replay_001",
        "packet_version": "v1.0",
        "direction_id": "dir_001",
        "direction_type": "known_science_replay",
        "domain": "knowledge_replay",
        "evidence_source_type": "known_science_replay",
        "source_provenance": "local_repo",
        "authorization_status": "manual",
        "static_local_only": True,
        "external_calls_allowed": False,
        "persistence_allowed": False,
        "public_claim_allowed": False,
        "evidence_items": [
            {
                "item_id": "item_001",
                "item_type": "text",
                "content_summary": "Excerpt from ARC packet",
                "source_reference": "arc_packet_77.json",
                "provenance_status": "synthetic_replay",
                "allowed_use": "internal",
                "forbidden_use": "public_claim",
                "injection_risk_notes": "none",
                "sensitive_data_status": "none",
                "uncertainty_notes": "low"
            }
        ],
        "known_science_anchor": "arc_packet_77",
        "hypothesis_or_direction_statement": "WESLR can reproduce ARC reasoning using static packet.",
        "expected_replay_pattern": "exact_match",
        "allowed_reasoning_actions": ["match", "compare"],
        "forbidden_reasoning_actions": ["model_call", "web_fetch"],
        "uncertainty_notes": "minimal",
        "failure_modes": ["schema_mismatch", "missing_item"],
        "stop_conditions": ["insufficient_evidence", "public_claim_attempt"],
        "expected_output_type": "internal_report",
        "no_public_claim_warning": "Do not publish as public claim.",
        "review_status": "pending",
    }


def test_valid_packet_passes_validation():
    pkt = valid_packet_dict()
    # Should not raise
    result = validate_packet(pkt)
    assert result.packet_id == pkt["packet_id"]


def test_invalid_packet_fails_on_web_provenance():
    pkt = valid_packet_dict()
    pkt["source_provenance"] = "http://example.com/data"
    with pytest.raises(RealEvidenceSchemaError) as exc:
        validate_packet(pkt)
    assert "source_provenance must not reference live web" in str(exc.value)
