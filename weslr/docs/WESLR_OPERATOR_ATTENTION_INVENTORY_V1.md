# WESLR OPERATOR ATTENTION INVENTORY V1 — FIRST PASS

**Version:** 1.0 — First Pass
**Date:** 2026-05-01
**Status:** ACTIVE DOCTRINE — inspection only, no implementation
**Scope:** This pass covers only /chat path, public signal capture, contract observation, contract insufficiency detector, contract proposal review bridge, and read-only review interface. ISS, deployment, frontend, and OmniChat are excluded.

---

## SOURCE 1 — /chat Response Path

| Field | Value |
|-------|-------|
| **Source name** | `/chat` response path |
| **File / module** | `weslr/chat_responder.py`, `weslr/deterministic_handlers.py`, `weslr/response_formatter.py` |
| **Implemented status** | LIVE |
| **What triggers operator attention** | Handler returns a path that is `unknown`, `fallback_safe`, or `blocked_write`; `rate_limited` path fires |
| **Mandatory or optional attention** | **Optional** — these are normal operational signals; operator awareness only unless patterns persist |
| **Risk level** | **low** |
| **Suggested AAI handling** | **track silently** — fallback and blocked_write paths are expected behavior in `public_demo_readonly` mode |
| **Can it be automated safely?** | **yes, low-risk** — these paths are deterministic, governed, and mode-enforced |
| **Can it change behavior/state?** | **no** — all /chat paths are read-only or write-blocked in current mode |

### Notes / Concerns

- `fallback_safe` and `blocked_write` are expected in public mode. Silent tracking is sufficient.
- `rate_limited` path from `safety.py` RateLimiter could indicate abuse or legitimate high traffic. Track silently, surface in periodic summary if frequency exceeds baseline.
- No direct operator interruption required from /chat path itself.
- Response path classification is deterministic — no ambiguity.

---

## SOURCE 2 — Public Signal Capture

| Field | Value |
|-------|-------|
| **Source name** | Public signal capture (`/chat` → `website_signal_integration.py`) |
| **File / module** | `weslr/website_signal_integration.py`, `weslr/user_signal_intake.py`, `weslr/public_signal_store.py` |
| **Implemented status** | LIVE |
| **What triggers operator attention** | `classify_public_signal()` returns `safe_to_record: False` (forbidden field detected or PII-like content found); append fails |
| **Mandatory or optional attention** | **Optional** — append failures are fire-and-forget, storage is append-only; however, persistent append failures could indicate systemic issue |
| **Risk level** | **medium** |
| **Suggested AAI handling** | **track silently** — fire-and-forget design means failures are acceptable; track failure rate to detect systemic issues |
| **Can it be automated safely?** | **yes, low-risk** — PII/forbidden-field detection is deterministic and conservative; no LLM used |
| **Can it change behavior/state?** | **no** — signal capture is purely observational, no behavior change, no state mutation |

### Notes / Concerns

- The module explicitly does not store raw prompts, PII, or change behavior. Design is sound.
- Append failures are silently ignored — this is intentional but means gaps in signal history are invisible.
- 200 records in `public_signals.jsonl` as of this inspection. Signal volume is low.
- `contains_forbidden_field()` and `detect_pii_like_content()` are pure functions — no side effects.
- **Concern:** If append failures are silently ignored AND the failure rate is not monitored, systemic storage issues could go undetected. Consider tracking failure rate in periodic summary.

---

## SOURCE 3 — Contract Observation

| Field | Value |
|-------|-------|
| **Source name** | Contract observation layer |
| **File / module** | `weslr/contract_observation.py` |
| **Implemented status** | LIVE |
| **What triggers operator attention** | `append_contract_observation()` returns `stored: False`; `validate_contract_observation()` detects a malformed record; PII or forbidden field detected in a record |
| **Mandatory or optional attention** | **Optional** — observation is passive, read-only, and append-only; validation failures indicate either bad data or an upstream bug |
| **Risk level** | **low** |
| **Suggested AAI handling** | **track silently** — validation failures are internal signals; they do not affect user-facing responses |
| **Can it be automated safely?** | **yes, low-risk** — `build_contract_observation()` is a pure function; validation is deterministic; forbidden-field scan is recursive and explicit |
| **Can it change behavior/state?** | **no** — observation module is explicitly read-only; `safe_to_record: True` and all safety flags set to `False`; `behavior_change_allowed: false` |

### Notes / Concerns

- Very clean design — pure function for building records, side-effect only at append step, fire-and-forget at call site (`website_signal_integration.py`).
- `_FORBIDDEN_FIELDS` is a frozenset — well-defined, explicit.
- PII scan is conservative but not aggressive — email, phone, IPv4, street patterns.
- 31 records in `contract_observations.jsonl` as of this inspection.
- **No path currently exists for the operator to review validation failures** — they are silently dropped. This is acceptable for V1 but worth monitoring.
- Observation records do NOT flow back into `/chat` pipeline — one-way only.

---

## SOURCE 4 — Contract Insufficiency Detector

| Field | Value |
|-------|-------|
| **Source name** | Contract insufficiency detector |
| **File / module** | `weslr/contract_insufficiency_detector.py` |
| **Implemented status** | LIVE |
| **What triggers operator attention** | `detect_insufficiency()` returns `insufficiency_found: True` AND `proposal_ready: True`; a pattern becomes stable across 3 consecutive checks; a new `contract_insufficiency_v1` record is appended to log |
| **Mandatory or optional attention** | **Optional** — sufficiency detection runs passively; operator needs awareness when `proposal_ready: True`, but no mandatory interrupt |
| **Risk level** | **medium** |
| **Suggested AAI handling** | **include in summary** — `proposal_ready: True` patterns should appear in periodic operator summary; not urgent enough to interrupt |
| **Can it be automated safely?** | **partially** — insufficiency detection logic is sound, but stability tracker uses in-memory state (`_STABILITY_COUNTS`, `_STABLE_PATTERNS`) that resets on process restart. Cross-check with log file. |
| **Can it change behavior/state?** | **no** — detector reads from observation log and appends to insufficiency log; no behavior change at detector level |

### Notes / Concerns

- **Stability tracker is in-memory.** `_STABILITY_COUNTS` and `_STABLE_PATTERNS` are module-level dicts. Process restart resets stability counts. For V1 this is acceptable; production should persist stability state.
- Insufficiency log (`contract_insufficiency_log.jsonl`) had 37 records as of inspection — most with `stable_across_checks: 1`, `proposal_ready: false`. Low current burden.
- Pattern types: `weak_entry_repetition`, `fallback_repetition`, `task_help_degradation`, `explanation_degradation`, `unknown_frame_stabilization`.
- AND-logic for detection is well-specified (IC1–IC4 all required).
- **Known gap:** `detect_insufficiency()` is never called automatically in the current pipeline — it runs via CLI or when explicitly invoked. No automatic periodic check.
- Evidence appended via `_append_insufficiency_evidence()` — fire-and-forget, silent on failure.

---

## SOURCE 5 — Contract Proposal Review Bridge

| Field | Value |
|-------|-------|
| **Source name** | Contract improvement proposal bridge |
| **File / module** | `weslr/contract_improvement_proposal_bridge.py` |
| **Implemented status** | LIVE |
| **What triggers operator attention** | `generate_proposals()` returns `generated: N` where N > 0; a new `contract_proposal_review_v1` record is appended to proposal log; duplicate proposal is skipped |
| **Mandatory or optional attention** | **Optional** — bridge generates review records passively; operator needs awareness of new proposals but can batch-review |
| **Risk level** | **medium** |
| **Suggested AAI handling** | **ask operator** — when `generated > 0`, surface to operator in next interaction or periodic summary; not urgent interrupt |
| **Can it be automated safely?** | **partially** — deduplication logic is correct; PII filter is conservative; but the bridge only generates records, it does not update any state. Safe to run automatically. |
| **Can it change behavior/state?** | **no** — bridge appends to `contract_proposal_review_log.jsonl` only; does not modify contracts, proposals, or handler behavior |

### Notes / Concerns

- 1 record in `contract_proposal_review_log.jsonl` as of inspection (`CP-20260501-001`, `proposal_status: pending_review`). Very low volume.
- Deduplication prevents duplicate proposals for the same pattern+contract+response_path combination.
- Proposal records have `automatic_change: false` and `operator_action_requested: "review_contract_outcome"` — explicitly operator-gated.
- **Validation is strict:** PII scan, forbidden-field scan, `proposal_ready` filter, `stable_across_checks >= 3` filter, `insufficiency_confirmed` filter.
- Proposals are NOT automatically applied — they require operator review via review interface.
- `_PRODUCTION_FILES` guard prevents writes to `proposal_trace.jsonl` or `implementation_plans.jsonl`.

---

## SOURCE 6 — Read-Only Review Interface

| Field | Value |
|-------|-------|
| **Source name** | Contract proposal review interface |
| **File / module** | `weslr/review_interface.py` |
| **Implemented status** | LIVE |
| **What triggers operator attention** | `load_pending_contract_reviews()` returns a non-empty list; `summarize_pending_reviews()` shows multiple pending reviews by pattern type or contract |
| **Mandatory or optional attention** | **Optional** — review interface is explicitly read-only; pending reviews wait for operator action; no mandatory interrupt |
| **Risk level** | **low** |
| **Suggested AAI handling** | **include in summary** — pending reviews should appear in operator periodic summary; operator chooses when to review |
| **Can it be automated safely?** | **yes, low-risk** — pure read-only functions; no side effects; forbidden-field stripping ensures no PII exposure |
| **Can it change behavior/state?** | **no** — interface does not write, does not approve/reject/defer proposals; only reads and summarizes |

### Notes / Concerns

- `load_pending_contract_reviews()` — returns pending reviews only (`proposal_status == "pending_review"`).
- `get_contract_review_by_id(proposal_id)` — single review lookup.
- `summarize_pending_reviews()` — aggregates by pattern_type, contract, response_path; provides `records` list with lightweight copies.
- All forbidden fields (raw_prompt, prompt, message, user_input, email, phone, ip, address, name, location) are stripped from every record before return.
- 1 pending review as of inspection — very low burden.
- **Important:** Review interface is a query surface, not a review workflow. It tells the operator what is pending but does not trigger review actions. Human reviews via `contract_proposal_review_log.jsonl` directly.
- No automatic proposal status transitions — operator must manually update `proposal_status` in the log.

---

## SECTION — FIRST PASS SUMMARY

### A) Must Interrupt Operator
*(Sources that require immediate operator interruption — none in this pass)*

```
None identified in this pass.
```

All inspected sources operate within expected parameters. No critical failures detected. The pipeline is functioning as designed with appropriate fire-and-forget safety nets.

---

### B) Should Ask Operator
*(Sources where AAI should prompt operator before any action)*

| Source | Reason |
|--------|--------|
| Contract Proposal Review Bridge | New review records generated (`generated > 0`) — operator should review at next convenient interaction. Not urgent. |

---

### C) Should Appear in Periodic Summary
*(Sources that should be included in scheduled operator digest)*

| Source | Reason |
|--------|--------|
| Contract Insufficiency Detector | `proposal_ready: True` patterns indicate contract outcomes that may need review. Include pattern type and occurrence count. |
| Contract Proposal Review Bridge | Pending review count + by-pattern breakdown. |
| Review Interface | Total pending reviews, grouped by pattern_type and contract. |

---

### D) Should Be Tracked Silently
*(Sources that should operate without disturbing the operator)*

| Source | Reason |
|--------|--------|
| `/chat` response path | Normal operational signal; fallback/blocked_write/rate_limited paths are expected behavior in public mode. |
| Public Signal Capture | Append failures are acceptable; track failure rate only to detect systemic issues. |

---

### E) Should Be Suppressed as Noise
*(Sources that should not be surfaced to the operator)*

| Source | Reason |
|--------|--------|
| Contract Observation — validation failures | Record-level validation failures are internal; they do not affect user experience. Silent tracking sufficient. |
| Contract Observation — stored records | Observation volume (31 records) is operational noise. No action needed unless volume spikes. |

---

## SECTION — NEXT INVENTORY PASS

Areas excluded from this pass, to be inspected in subsequent passes:

| # | Area | Priority rationale |
|---|------|---------------------|
| 1 | ISS diagnostics | Operator-facing diagnostic output; probe results and gap signals may require attention |
| 2 | Proposal traceability | `proposal_trace.jsonl` records (115 entries) — proposal lifecycle tracking |
| 3 | Implementation plans | `implementation_plans.jsonl` (8 entries) — operator approval gates |
| 4 | Write handlers | `write_handlers.py` — state-changing operations; highest operator-burden potential |
| 5 | Public readiness | `public_readiness_tests.py`, `safety.py` — readiness gates and security reflection |
| 6 | Controlled exposure | `WESLR_CONTROLLED_USER_EXPOSURE_PLAN_V1.md` — observation window rules |
| 7 | Deployment / OCW handoff | `deploy/WESLR_OCW_HANDOFF_CONTRACT_V1.json` — commit-gated deployment |
| 8 | Frontend / UI specs | `WESLR_FRONTDOOR_UI_SPEC_V1.md` — internal-only flags and structured output rules |
| 9 | OmniChat unification | `omnichat/` — response surface, evidence labels, fallback wording |
| 10 | Evidence workspace | `WESLR_EVIDENCE_WORKSPACE_V1.md` — human review triggers, evidence forgetting |
| 11 | Signal aggregation | `WESLR_SIGNAL_AGGREGATION_V1.md` — surfacing thresholds, S1–S6 signal types |
| 12 | Operator consistency | `WESLR_OPERATOR_CONSISTENCY_LAYER_V1.md` — decision log, diagnostic on operator |

---

## INSPECTION METADATA

| Field | Value |
|-------|-------|
| Pass | 1 of N |
| Sources inspected | 6 |
| Files examined | `website_signal_integration.py`, `user_signal_intake.py`, `public_signal_store.py`, `contract_observation.py`, `contract_insufficiency_detector.py`, `contract_improvement_proposal_bridge.py`, `review_interface.py`, `chat_responder.py`, `deterministic_handlers.py`, `safety.py`, `contracts.py` |
| JSONL files examined | `contract_observations.jsonl` (31 records), `contract_insufficiency_log.jsonl` (37 records), `contract_proposal_review_log.jsonl` (1 record), `public_signals.jsonl` (200 records) |
| Doctrines reviewed | `WESLR_SIGNAL_AGGREGATION_V1.md`, `WESLR_EVIDENCE_WORKSPACE_V1.md`, `WESLR_CONTROLLED_USER_EXPOSURE_PLAN_V1.md`, `WESLR_FRONTDOOR_UI_SPEC_V1.md`, `WESLR_OMNICHAT_UNIFICATION_PLAN_V1.md`, `WESLR_OPERATOR_CONSISTENCY_LAYER_V1.md`, `WESLR_REVIEW_DECISION_LOG_V1.md` |
| Live sources | 6 of 6 |
| Spec-only sources | 0 in this pass |
| Not-verified sources | 0 in this pass |

---

*No runtime behavior modified. No Python files changed. No JSONL files modified. No tests changed. No LLM integration. Inspection only.*