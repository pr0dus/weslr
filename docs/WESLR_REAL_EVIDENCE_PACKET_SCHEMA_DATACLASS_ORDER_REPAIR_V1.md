# WESLR_REAL_EVIDENCE_PACKET_SCHEMA_DATACLASS_ORDER_REPAIR_V1

**Lane**: `REPAIR_REAL_EVIDENCE_PACKET_SCHEMA_DATACLASS_ORDER_V1`

- **Start HEAD**: `e49799996c1af64a6d90075d482a70fb82855cc0`
- **End HEAD**: (to be filled after commit)
- **Report path**: `docs/WESLR_REAL_EVIDENCE_PACKET_SCHEMA_DATACLASS_ORDER_REPAIR_V1.md`

## Actions performed
1. Reordered fields in `weslr/real_evidence_packet_schema.py` so that all required (non‑default) fields appear before any fields with defaults.
2. Updated live‑web provenance check to explicitly block URLs (`http://`/`https://`).
3. Ran Python compilation (`python -m py_compile`).
4. Executed focused pytest suite:
   - `weslr/tests/test_real_evidence_packet_schema.py`
   - `weslr/tests/test_real_evidence_packet_instance.py`
   All tests **passed**.
5. Validated the packet JSON `evidence/first_real_evidence_known_science_replay_001.json` using `validate_packet`; validation succeeded.
6. Ran repository checks:
   - `git diff --check` – no whitespace errors.
   - `./scripts/weslr_release_check.sh` – passed.
   - `./scripts/chat_weslr_de_health_check.sh --mode source-repo` – passed.
   - `python weslr/tests/release_gate_v1.py` – passed.

## Results
- **Dataclass order repaired**: **yes**
- **Schema imports**: **yes** (no import errors)
- **Packet validates**: **yes**
- **Packet JSON changed**: **no**
- **Schema validation weakened**: **no** (same constraints, only stricter URL check)
- **Replay executed**: **no** (only schema repair)
- **Overall validation**: **PASS**
- **Push avoided**: **yes** (local only)

## Recommendations
Proceed to the next lane, e.g. `RUN_FIRST_CONTROLLED_REAL_EVIDENCE_REPLAY_V1`, now that the schema imports and packet validation succeed.
