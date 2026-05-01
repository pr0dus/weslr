# WESLR Observation-to-Review-Queue Loop — Phase 1 Canon

**Date:** 2026-05-01
**Checkpoint:** WESLR_OBSERVATION_LOOP_PHASE_1_CANNON_DEFINED
**Commit:** `89edb94`

---

## Phase 1 Scope (Operator-Layer Expansion — Stopped)

The observation-to-review-queue loop was completed to a stable internal ceiling:

| Layer | File | Status |
|-------|------|--------|
| Observation | `weslr/contract_observation.py` | ✅ Complete |
| Insufficiency detection | `weslr/contract_insufficiency_detector.py` | ✅ Complete |
| Proposal bridge | `weslr/contract_improvement_proposal_bridge.py` | ✅ Complete |
| Review interface | `weslr/review_interface.py` | ✅ Complete |
| Decision log | — | NOT BUILT |
| Operator consistency | — | NOT BUILT |
| Contract reply modification | — | NOT BUILT |

**Decision:** Stopping operator-layer expansion. The four-layer observation loop (observe → detect → propose → review) is canon-complete for this phase. The decision log, approval workflow, and contract modification path are out of scope until a future operator decision authorizes them.

---

## Public Readiness Inspection — 6 Blockers Assessed

### 1. Read-Only Mode Isolation ✅

**Question:** Does the observation layer maintain read-only isolation from the response path?

**Evidence:**
- `contract_observation.append_contract_observation()` is called as fire-and-forget (wrapped in `try/except`) after `public_signal_store.append_public_signal_record()` succeeds
- Integration point: `weslr/website_signal_integration.py`, `capture_website_signal()` function, after public signal append
- Failures are silently ignored — zero impact on `/chat` response
- Separate storage file: `weslr/contract_observations.jsonl` — append-only, never touches `public_signals.jsonl`
- No `open()` calls with write mode in the observation layer
- `build_contract_observation()` is a pure function — no side effects

**Verdict:** ✅ READ_ONLY_MODE_ISOLATION_CONFIRMED

---

### 2. Rate Limiting ⚠️ NOT PRESENT

**Question:** Is there a rate limit on observation recording to prevent abuse?

**Evidence:**
- No rate limit found in `contract_observation.py`, `website_signal_integration.py`, or `public_signal_store.py`
- `contract_observations.jsonl` currently has 31 records from a 12-interaction observation batch
- No per-session, per-IP, or per-session-hash throttle

**Verdict:** ⚠️ RATE_LIMITING_NOT_PRESENT — acceptable for current private-phase deployment; must be added before public exposure

---

### 3. Max Input Length ✅

**Question:** Does the observation layer truncate or reject oversized inputs?

**Evidence:**
- `build_contract_observation()` does not include raw message or prompt in the record
- `session_id_hash` is derived from a hash of `event.get("session_id_hash", "")` — input length independent
- `message_length_bucket` is used instead of actual message length — buckets (e.g. "short"/"medium"/"long"/"oversize")
- No field in the observation record stores the raw message content regardless of length

**Verdict:** ✅ MAX_INPUT_LENGTH_SAFE — raw message never stored, so length is irrelevant to the observation record

---

### 4. Write-Path Blocking ✅

**Question:** Can the observation layer be abused to write to production state?

**Evidence:**
- `build_contract_observation()` is a pure read function — no file I/O
- `append_contract_observation()` uses append-only mode (`"a"`) and rejects invalid records before writing
- `validate_contract_observation()` rejects any record with `safe_to_record != true`, `raw_prompt_stored != false`, `behavior_change_allowed != false`, or `value_inference_allowed != false`
- Forbidden field check is recursive — any nested presence of `message`, `raw_message`, `prompt`, `user_input`, `email`, `phone`, `address`, `ip`, `name`, `location` causes rejection
- Fire-and-forget integration in `website_signal_integration.py` — failures do not propagate
- No write to `proposal_trace.jsonl`, `implementation_plans.json`, `public_signals.jsonl`, or any production truth file

**Verdict:** ✅ WRITE_PATH_BLOCKING_CONFIRMED

---

### 5. No Raw Prompt Storage ✅

**Question:** Does the observation record contain any raw user message content?

**Evidence:**
- Schema explicitly excludes: `message`, `raw_message`, `prompt`, `raw_prompt`, `user_input`
- `raw_prompt_stored` field is always `false` — enforced in `validate_contract_observation()`
- `validate_contract_observation()` rejects any record where `raw_prompt_stored != false`
- `pii_stored` field is always `false` — enforced in validation
- Sample record inspection (`contract_observations.jsonl`, 31 records): zero forbidden fields present in any record
- `behavior_change_allowed` always `false`, `value_inference_allowed` always `false` — enforced in both `build_contract_observation()` and `validate_contract_observation()`

**Verdict:** ✅ NO_RAW_PROMPT_STORAGE_CONFIRMED

---

### 6. No Internal Metadata Leakage ✅

**Question:** Does the observation record expose internal system state?

**Evidence:**
- `session_id_hash`: 8-byte hex string (e.g. `37a8eec1ce19687d`) — hashed, not the actual session ID — cannot be reversed to a session identifier
- `safe_to_record`, `raw_prompt_stored`, `pii_stored`, `behavior_change_allowed`, `value_inference_allowed`: all boolean flags describing the record's safety properties, not internal state
- `timestamp`: ISO-8601 wall-clock time of observation — public-facing, not internal clock
- `record_type`, `response_contract`, `interaction_frame`, `turn_type`, `reply_shape`, `signal_type`, `response_path`, `source`: all contract metadata — not internal memory, not operator identity
- No `/data/data/com.termux`, no internal file paths, no `execution_allowed` flags, no API keys, no tokens
- `source` is always `"website_public"` — static string, no leakage

**Verdict:** ✅ NO_INTERNAL_METADATA_LEAKAGE_CONFIRMED

---

### 7. Safe Fallback Behavior ✅

**Question:** Does the observation layer degrade safely when components fail?

**Evidence:**
- Missing `interpreted` kwarg → `interaction_frame="unknown"` used as fallback in `build_contract_observation()`
- Missing `public_signal_record` → `signal_type=null` used as fallback
- JSON parse failure in `append_contract_observation()` → record rejected, no crash
- Missing `event.session_id_hash` → empty string used as fallback
- Fire-and-forget in `website_signal_integration.py` → any exception during observation append is swallowed silently
- No behavior change, no response modification, no error returned to caller when observation fails

**Verdict:** ✅ SAFE_FALLBACK_BEHAVIOR_CONFIRMED

---

## Summary Table

| Blocker | Status | Notes |
|---------|--------|-------|
| Read-only mode isolation | ✅ | Fire-and-forget, pure functions, separate JSONL |
| Rate limiting | ⚠️ | Not present — acceptable for private deployment |
| Max input length | ✅ | Raw message never stored; length-independent schema |
| Write-path blocking | ✅ | Append-only, forbidden field validation, no production writes |
| No raw prompt storage | ✅ | `raw_prompt_stored=false`, `pii_stored=false`, schema enforces |
| No internal metadata leakage | ✅ | `session_id_hash` is hashed, no internal paths/flags/tokens |
| Safe fallback behavior | ✅ | Missing inputs → safe fallback values; exceptions swallowed |

---

## What Remains Open

| Item | Priority | Note |
|------|----------|------|
| Rate limiting | Medium | Add before public exposure |
| `contract_proposal_review_log.jsonl` decision log | Deferred | Requires operator-layer authorization |
| Contract response changes | Deferred | Requires operator approval workflow |

---

## Verdict

```
WESLR_OBSERVATION_LOOP_PHASE_1_CANNON_DEFINED
WESLR_OBSERVATION_LOOP_PHASE_1_BLOCKERS_ASSESSED
WESLR_RATE_LIMIT_REMAINING_OPEN
```

**Commit:** `89edb94` ("WESLR: add review interface v1 — read-only proposal inspection layer")

This canon closes the observation-to-review-queue loop for Phase 1. Operator-layer expansion is stopped. Rate limiting is the only public-readiness gap remaining before public exposure.
