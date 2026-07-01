# DESIGN: First Real‑Evidence Packet Instance (V1)

**Repository**: `/data/data/com.termux/files/home/weslr-pr47-clean`
**Branch**: `occ-discovery-doctrine-implementation-20260613`
**Start HEAD**: `f5f2b99f2a2638dba306f3ab04c417321997a1a6`
**Dispatch**: `CREATE_FIRST_REAL_EVIDENCE_PACKET_INSTANCE_V1`
**Selected Direction**: `Known‑Science Replay`

---

## Purpose
Create a concrete packet instance that conforms to the schema defined in
`weslr/real_evidence_packet_schema.py`. The packet is a static, locally‑stored
JSON document used for the first controlled real‑evidence run.

---

## Packet Location
`evidence/first_real_evidence_known_science_replay_001.json`

---

## Packet Content (JSON)
```json
{
  "packet_id": "first_real_evidence_known_science_replay_001",
  "packet_version": "v1.0",
  "direction_id": "direction_known_science_replay_001",
  "direction_type": "known_science_replay",
  "domain": "knowledge_replay",
  "evidence_source_type": "known_science_replay",
  "source_provenance": "local_static_arc_2step_80_synthetic",
  "authorization_status": "manual",
  "static_local_only": true,
  "external_calls_allowed": false,
  "persistence_allowed": false,
  "public_claim_allowed": false,
  "evidence_items": [
    {
      "item_id": "arc_2step_80_report_001",
      "item_type": "text",
      "content_summary": "Summary of ARC synthetic 2‑step 80 results (77 exact, 3 partial, 0 unsupported, shuffle audit invariant).",
      "source_reference": "weslr/arc_synthetic_2step_80_report.txt",
      "provenance_status": "synthetic_replay",
      "allowed_use": "internal",
      "forbidden_use": "public_claim",
      "injection_risk_notes": "Static owner‑controlled packet; no executable instructions.",
      "sensitive_data_status": "none",
      "uncertainty_notes": "No uncertainty beyond synthetic reproducibility."
    }
  ],
  "known_science_anchor": "arc_2step_80_anchor",
  "hypothesis_or_direction_statement": "Replay the ARC synthetic 2‑step 80 packet to verify static reasoning without external calls.",
  "expected_replay_pattern": "exact_match",
  "allowed_reasoning_actions": ["match", "compare", "audit"],
  "forbidden_reasoning_actions": ["model_call", "web_fetch", "external_tool"],
  "uncertainty_notes": "Minimal uncertainty; static data.",
  "failure_modes": ["packet_missing", "schema_mismatch", "unexpected_mutation"],
  "stop_conditions": ["external_call_requested", "live_source_detected", "public_claim_needed"],
  "expected_output_type": "internal_report",
  "no_public_claim_warning": "Do not publish this packet…" 
}
```

---

## Validation Test (`weslr/tests/test_real_evidence_packet_instance.py`)
```python
import json
from pathlib import Path
from weslr.real_evidence_packet_schema import validate_packet, RealEvidenceSchemaError


def test_packet_instance_validates():
    packet_path = Path(__file__).parents[2] / "evidence" / "first_real_evidence_known_science_replay_001.json"
    packet_dict = json.loads(packet_path.read_text())
    # Should not raise
    packet = validate_packet(packet_dict)
    # Verify key boundary flags are false / true as required
    assert packet.static_local_only is True
    assert packet.external_calls_allowed is False
    assert packet.persistence_allowed is False
    assert packet.public_claim_allowed is False
    # Verify direction/type
    assert packet.direction_type == "known_science_replay"
    assert packet.evidence_source_type == "known_science_replay"
    # Ensure no live references in provenance
    assert "web" not in packet.source_provenance.lower()
    # Check that at least one evidence item is present
    assert len(packet.evidence_items) >= 1
    # Verify the evidence item respects boundaries
    item = packet.evidence_items[0]
    assert "web" not in item.source_reference.lower()
    assert item.forbidden_use == "public_claim"
```

---

## Boundary Enforcement
All prohibited categories are encoded in the schema and reinforced by the
validation test:
- **No live web / RSS / GitHub / lab‑notebook** – checked via `source_provenance`
  and each `evidence_items.source_reference`.
- **No provider/model calls** – `external_calls_allowed` is `False`.
- **No persistence** – `persistence_allowed` is `False`.
- **No public / benchmark claims** – `public_claim_allowed` is `False` and the
  evidence item’s `forbidden_use` is set to `public_claim`.
- **No final‑answer generation** – `expected_output_type` limited to
  `internal_report`.

---

## Release‑Gate Allowance
Only files inside `weslr/` and the new packet JSON under `evidence/` are
added; they satisfy the existing exact‑file allowance for new schema files.
No other repo areas are touched.

---

## Validation Checklist
- **`py_compile`** – all new modules import cleanly.
- **Focused pytest** – passes (`pytest -q weslr/tests/test_real_evidence_packet_instance.py`).
- **`python weslr/tests/release_gate_v1.py`** – PASS (no new staged disallowed paths).
- **`git diff --check`** – PASS (no whitespace errors).
- **`./scripts/weslr_release_check.sh`** – PASS.
- **`./scripts/chat_weslr_de_health_check.sh --mode source-repo`** – PASS.

---

*Prepared by OCC – OpenClaw Coder.*
