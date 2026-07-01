import json
from pathlib import Path

from weslr.real_evidence_packet_schema import validate_packet, RealEvidenceSchemaError


def test_packet_instance_validates():
    packet_path = Path(__file__).parents[2] / "evidence" / "first_real_evidence_known_science_replay_001.json"
    packet_dict = json.loads(packet_path.read_text())
    # Validation should succeed without raising
    packet = validate_packet(packet_dict)
    # Boundary assertions
    assert packet.static_local_only is True
    assert packet.external_calls_allowed is False
    assert packet.persistence_allowed is False
    assert packet.public_claim_allowed is False
    # Direction / source type
    assert packet.direction_type == "known_science_replay"
    assert packet.evidence_source_type == "known_science_replay"
    # No live references in provenance
    assert "web" not in packet.source_provenance.lower()
    assert "github" not in packet.source_provenance.lower()
    # At least one evidence item
    assert len(packet.evidence_items) >= 1
    # Check first evidence item boundaries
    item = packet.evidence_items[0]
    assert "web" not in item.source_reference.lower()
    assert "github" not in item.source_reference.lower()
    assert item.forbidden_use == "public_claim"
    assert item.allowed_use == "internal"
    # Ensure no sensitive data flag
    assert item.sensitive_data_status == "none"
