# WESLR Releases

Release notes and version history for WESLR platform.

---

## v75 — Recovery Recommendation Service Sealed (2026-04-07)

**Commit:** `22e8011c38801cd84c0a20cacb2c07c5597c505c`

**Status:** ✅ Sealed

**Changes:**
- v75 Recovery Recommendation Service fully tested and sealed
- Test suite: 22/22 tests passed
- Confidence guidance for operator recommendations
- Diagnostics integration hooks
- Export formatting hooks with `hint_certainty: "suggestion"` markers

**Files:**
- `weslr/recovery_recommendation_service.py` (existing, no changes needed)
- `weslr/test_recovery_recommendation_service.py` (new, 494 lines)

**Backward Compatibility:**
- Fully compatible with v71-v74 diagnostic flow
- Read-only behavior preserved
- No breaking changes

---

## v74 — Architecture Memory Refresh (2026-04-07)

**Commit:** `cb782ef876e20f919539288871d30b60dc3bdcc0`

**Status:** ✅ Sealed

**Changes:**
- Updated ARCHITECTURE.md to v74 seal
- Updated OPERATOR_STATE.json to v74
- CLI Entry Surface Decomposition seal

**Files:**
- `weslr/ARCHITECTURE.md`
- `weslr/operator_control/OPERATOR_STATE.json`

---

## v73 — Capability Boundary Hardening (2026-04-07)

**Commit:** `646fb958101458d151d720c15f7f0b45d8ced34a`

**Status:** ✅ Sealed

**Changes:**
- Explicit TIA/C# exclusion
- Scope boundary enforcement
- No orchestrations/shardings/aggregations

---

## v72 — Operator Workflow Validation (2026-04-07)

**Status:** ✅ Sealed

**Changes:**
- Operator-initiated workflow enforcement
- No autonomous execution

---

## v71 — CLI Entry Surface Decomposition (2026-04-07)

**Status:** ✅ Sealed

**Changes:**
- CLI surface separated into legacy/self_mod/external modules
- Parser structure unchanged

---

## v70 — Recovery Recommendation Service (2026-04-07)

**Status:** ✅ Sealed

**Changes:**
- Initial recovery recommendation service implementation

---

## v61-v69 — Distributed Execution Layers (2026-04-05)

**Status:** ✅ Sealed

**Layers:**
- v61: Remote Action Proposal
- v62: Controlled Execution Envelope
- v63: Remote Execution Receipt
- v64: Distributed Execution Integration
- v65: Remote Node Handshake
- v66: Handshake-Execution Integration
- v67: Execution Timeout / Deadline Propagation
- v68: Distributed Execution Telemetry
- v69: Distributed Telemetry Export Hooks

---

*WESLR Release Notes v1.0.0*
