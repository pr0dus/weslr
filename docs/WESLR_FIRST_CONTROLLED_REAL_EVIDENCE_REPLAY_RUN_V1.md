# WESLR_FIRST_CONTROLLED_REAL_EVIDENCE_REPLAY_RUN_V1

**Packet ID**: `first_real_evidence_known_science_replay_001`

**Validation**: PASS – the packet conforms to `weslr.real_evidence_packet_schema.RealEvidencePacket`.

**Known‑science anchor**: `arc_2step_80_anchor`

**Observed replay pattern**: The evidence item `arc_2step_80_report_001` reproduces the synthetic ARC 2‑step 80 results exactly as described in the anchor.

**Expected pattern**: `exact_match`
**Pattern matched**: **YES** – the observed data aligns perfectly with the expected pattern.

**Contradictions**: None detected.

**Uncertainty notes**: `Minimal uncertainty; static data.`

**Evidence insufficiency warnings**: None – a single comprehensive evidence item satisfies the packet requirements.

**Stop conditions evaluated**:
- `external_call_requested`: **NOT triggered** (no external calls were made).
- `live_source_detected`: **NOT triggered** (`source_provenance` is `local_static_arc_2step_80_synthetic`).
- `public_claim_needed`: **NOT triggered** (the packet explicitly disallows public claims).

**No‑public‑claim warning**: `Do not publish this packet as evidence; internal only.`

**Forbidden operations attempted**: **No** – the replay adhered to all boundary constraints (no web/RSS/GitHub/lab ingestion, no external tools, no persistence, no public claims).

**Replay status**: **COMPLETED** – all checks passed and the replay report has been generated.
