# WESLR ARC UNKNOWN ENGINE LEVEL LADDER SYNTHETIC SMOKE REVIEW V1

## Recovery status
This document is a **recovered / reconstructed current-branch review artifact**.

- Recovered on current branch: **yes**
- Original cited commit `98eed788b2a76ba2b41276ea41fc45c5694fa456` present locally: **no**
- Original prior review provenance can be proven: **no**
- This review is reconstructed from current branch code, current local smoke-metrics output, later committed smoke-metrics repair/review docs, and owner receipts where explicitly marked

## Core review finding
The original smoke summary was vulnerable to ambiguity because packet exact counts and attempted task counts were mixed into a single implied success story.

### Ambiguity explained
- Attempted levels / tasks are counted at the **task level**
- Top-2 exact matches are counted at the **packet level**
- A task can contribute more than one evaluated packet
- Therefore packet exact count can exceed attempted task count without any contradiction

Current branch recovered values show the distinction clearly:
- Attempted task count: **36**
- Task exact count: **31**
- Task exact rate: **31 / 36 = 0.8611111111111112**
- Packet exact count: **41**
- Packet exact rate: **41 / 48 = 0.8541666666666666**

## Corrected metric distinction
### Primary internal metric
- Primary metric: **`task_exact_rate`**
- Threshold basis: **`task_exact_rate`**
- Internal pass 85 rule: pass only if `task_exact_rate >= 0.85`
- Current task-level signal: **above threshold**

### Diagnostic metric
- Diagnostic metric: **`packet_exact_rate`**
- Packet exact remains useful for understanding top-2 packet quality
- Packet exact must **not** unlock hardening by itself

## 85% hardening rule
Recovered current branch rule:
- `internal_pass_85` depends on `task_exact_rate`
- `level_hardening_allowed` currently mirrors that task-rate threshold in code

Governance note:
- Hardening is **not authorized yet**
- Before any hardening decision, the branch must have:
  1. recovered branch artifacts in place
  2. stronger metric coverage tests
  3. a confirming Smoke V2 lane after those tests

## Boundary review
- No public ARC data
- No Kaggle data
- No benchmark claims
- No official scoring claims
- No ARC-AGI-1 / ARC-AGI-2 performance claims
- No solver/generator behavior changes are authorized in this review artifact

## Recommended next lane
`ADD_ARC_UNKNOWN_ENGINE_SMOKE_METRICS_COVERAGE_TESTS_V1`

Reason:
- the recovered docs can now restore continuity on the current branch
- the threshold-policy tests are still only 3 cases deep
- stronger negative and discrimination tests should land before Smoke V2 is used as a decision signal
