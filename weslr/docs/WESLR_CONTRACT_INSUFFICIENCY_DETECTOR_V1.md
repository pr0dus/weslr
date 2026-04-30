# WESLR CONTRACT INSUFFICIENCY DETECTOR V1

**Version:** 1.0
**Status:** SPEC ONLY — no runtime effect
**Date:** 2026-04-30

---

## Section 1 — Purpose

Detect when a response contract produces insufficient outcomes repeatedly — without changing behavior, creating proposals automatically, or using LLM inference.

This is a **read-only signal analyzer**. It reads from `contract_observations.jsonl` and produces local evidence records. It does not modify WESLR behavior, does not create proposals, and does not infer values beyond what is directly observed.

**What it does:**
- Tracks which contracts fire how often over a sliding window
- Detects repeated weak outcomes (same contract, same path, same frame)
- Records insufficiency evidence locally for later operator review
- Does NOT propose changes, trigger handlers, or modify responses

**What it does NOT:**
- Never changes behavior
- Never writes to production truth files
- Never creates proposals
- Never infers values beyond direct signal counts
- Never uses LLM

---

## Section 2 — Input Source

**File:** `weslr/contract_observations.jsonl` (append-only, created by Contract Observation Layer V1)

**Read-only.** This module reads from the observation file. It does not write to it.

**Schema of each line:**
```json
{
  "record_type": "contract_observation_v1",
  "response_contract": "guided_help",
  "interaction_frame": "task_help",
  "turn_type": "question",
  "reply_shape": "deterministic_answer",
  "signal_type": "S4",
  "response_path": "task_help_query",
  "source": "website_public",
  "safe_to_record": true,
  "raw_prompt_stored": false,
  "pii_stored": false,
  "behavior_change_allowed": false,
  "value_inference_allowed": false,
  "timestamp": "2026-04-30T18:00:00Z",
  "session_id_hash": "aabbccdd"
}
```

---

## Section 3 — Insufficiency Criteria

A contract outcome is considered **insufficient** when it meets ALL of:

| # | Criterion | Description |
|---|-----------|-------------|
| IC1 | Same contract fires ≥ 3 times in window | The same `response_contract` value appears ≥3× in the sliding window |
| IC2 | Same `response_path` | All occurrences share the same `response_path` |
| IC3 | No signal_type improvement | All have `signal_type` in (null, S4) — no S1/S2 improvement signals |
| IC4 | Same `interaction_frame` or no frame classification | All map to `entry` or `unknown` (weak frames) |
| IC5 | Observation window ≥ 10 records | At least 10 records in window before declaring insufficiency |

**Insufficiency pattern types:**

| Pattern | Description |
|---------|-------------|
| `weak_entry_repetition` | `conversational_entry` fires ≥3× with null S-type, same path |
| `fallback_repetition` | `fallback_safe` path fires ≥3× with no S1/S2 signal |
| `task_help_degradation` | `task_help` frame fires but never upgrades to S1/S2 |
| `explanation_degradation` | `structured_explanation` frame fires but never produces S1/S2 |
| `unknown_frame_stabilization` | `unknown` frame persists across ≥3 records, no resolution |

---

## Section 4 — Detection Logic

### Sliding Window

- Window size: configurable, default 50 records (read from `contract_observations.jsonl` tail)
- Insufficiency check runs on each new record append (polling or event-driven)
- Window is a simple tail-read of the JSONL file — no database, no state file

### Insufficiency Detection Steps

```
1. append_contract_observation() writes new record to contract_observations.jsonl
       ↓
2. detector reads tail(N=50) records from contract_observations.jsonl
       ↓
3. if len(window) < 10: insufficient_check = no_result
       ↓
4. group records by response_contract
       ↓
5. for each contract group with count >= 3:
       a. check IC2-IC4 criteria
       b. if all ICs met: record insufficiency_evidence
       c. if not all ICs met: no result
       ↓
6. log insufficiency_evidence locally (append to detector log, not production)
       ↓
7. if stable insufficiency (same pattern across 3+ consecutive checks): flag for proposal bridge
```

### Evidence Record

```json
{
  "record_type": "contract_insufficiency_v1",
  "pattern_type": "weak_entry_repetition|fallback_repetition|...",
  "detected_at": "2026-04-30T20:00:00Z",
  "window_size": 50,
  "record_count_in_window": 37,
  "contract": "conversational_entry",
  "response_path": "fallback_safe",
  "occurrence_count": 4,
  "signal_types_seen": ["S4", null, "S4"],
  "frame_distribution": {"entry": 3, "unknown": 1},
  "insufficiency_confirmed": true,
  "stable_across_checks": 3,
  "proposal_ready": false
}
```

---

## Section 5 — Stability Threshold

Before passing to the Proposal Bridge, a detected insufficiency must be **stable across multiple checks.**

| Parameter | Value |
|-----------|-------|
| Consecutive checks required | 3 |
| Check interval | Every new record appended |
| Stability definition | Same `pattern_type` + same `contract` across 3 consecutive checks |

**`proposal_ready` is set to `true` only when stability threshold is met.**

Once `proposal_ready = true`:
- The evidence is surfaced for the Contract Improvement Proposal Bridge V1
- The Bridge converts it into a reviewable operator proposal
- No automatic behavior change occurs

---

## Section 6 — What Is NOT Detected

This detector is conservative. It does NOT flag:

| Not flagged | Why |
|-------------|-----|
| Single occurrences of any pattern | Requires ≥3 occurrences |
| Mixed signal types (S1/S2 present) | S1/S2 signals indicate improvement — not insufficient |
| Varied response_paths | Path variety indicates healthy routing |
| Different interaction frames | Frame variety indicates correct classification |
| First-time contracts | New contracts need baseline observation |

**Goal:** Only flag patterns that are clearly repetitive and clearly not improving.

---

## Section 7 — Output

**Local evidence log:** `weslr/contract_insufficiency_log.jsonl`

Append-only. Does NOT write to production truth files. Does NOT trigger behavior changes.

**For each sufficiency check:**

```json
{
  "checked_at": "2026-04-30T20:00:00Z",
  "window_records": 37,
  "insufficiency_found": false,
  "contracts_checked": ["conversational_entry", "guided_help", "structured_explanation"],
  "proposal_ready_patterns": []
}
```

Or if insufficiency found:

```json
{
  "checked_at": "2026-04-30T20:00:00Z",
  "window_records": 37,
  "insufficiency_found": true,
  "contracts_checked": ["conversational_entry"],
  "proposal_ready_patterns": [
    {
      "pattern_type": "weak_entry_repetition",
      "contract": "conversational_entry",
      "proposal_ready": true,
      "stable_across_checks": 3
    }
  ]
}
```

---

## Section 8 — Constraints

| # | Constraint |
|---|------------|
| CD1 | Read-only from `contract_observations.jsonl` — never writes to it |
| CD2 | No behavior change from any detection output |
| CD3 | No LLM inference — all criteria are deterministic boolean checks |
| CD4 | No proposal creation — `proposal_ready=true` gates the Proposal Bridge, does not auto-create proposals |
| CD5 | Evidence log is append-only, never truncates production files |
| CD6 | No PII in any evidence record |
| CD7 | Detector runs isolated from /chat response path (no latency impact) |

---

## Section 9 — Relationship to Other Layers

```
Contract Observation Layer V1 (stores contract outcomes)
    ↓
Contract Insufficiency Detector V1 (this doc — reads observation file, detects patterns)
    ↓
Contract Improvement Proposal Bridge V1 (converts stable insufficiency → operator proposal)
    ↓
Controlled user exposure (WESLR_CONTROLLED_USER_EXPOSURE_PLAN_V1)
```

---

## Section 10 — Next Phase

After this spec is approved:

1. **Implement** `weslr/contract_insufficiency_detector.py`
   - `detect_insufficiency(window_size=50)` — reads tail of observation file, returns evidence
   - `check_stability(pattern, min_checks=3)` — tracks stability across checks
   - `append_insufficiency_evidence(evidence)` — appends to local evidence log

2. **Create tests** — `weslr/tests/test_contract_insufficiency_detector_v1.py`

3. **No integration into website_signal_integration.py** — runs separately as a background analysis tool, not in the /chat path

4. **Commit:** `git add weslr/contract_insufficiency_detector.py weslr/tests/test_contract_insufficiency_detector_v1.py`

---

## Section 11 — Verdict

```
WESLR_CONTRACT_INSUFFICIENCY_DETECTOR_V1_SPEC_DEFINED
```

**Spec version 1.0 — no runtime effect. Implements read-only pattern detection on contract_observations.jsonl. Gates the Proposal Bridge. No behavior change, no proposals auto-created, no LLM inference.**

---

*Spec version 1.0 — gates Contract Improvement Proposal Bridge V1*