# WESLR_SECOND_CONTROLLED_REAL_EVIDENCE_REPLAY_RUN_V1

**Packet ID**: `second_real_evidence_known_science_replay_001`

**Validation**: PASS – the packet conforms to `weslr.real_evidence_packet_schema.RealEvidencePacket`.

**Known‑science anchor**: `arc_single_step_canonical_anchor`

**Observed replay pattern**: The evidence item `arc_single_step_report_001` reproduces the ARC single‑step canonical results exactly (114 exact matches, 6 partial matches).

**Expected pattern**: `exact_match`
**Pattern matched**: **YES** – observed data aligns perfectly with the expected pattern.

**Contradictions**: None detected.

**Uncertainty notes**: `Minimal; static data.`

**Evidence insufficiency warnings**: None – the single comprehensive evidence item satisfies the packet requirements.

**Stop conditions evaluated**:
- `external_call_requested`: **NOT triggered** (no external calls were made).
- `live_source_detected`: **NOT triggered** (`source_provenance` is `local_static_arc_single_step_canonical`).
- `public_claim_needed`: **NOT triggered** (packet disallows public claims).

**No‑public‑claim warning**: `Do not publish this packet as evidence; internal only.`

**Forbidden operations attempted**: **No** – the replay adhered to all boundary constraints (no web/RSS/GitHub/lab ingestion, no external tools, no persistence, no public claims).

**Replay status**: **COMPLETED** – all checks passed and the internal replay report has been generated.
