# COGNITIVE_ADEQUACY_FIXTURE_INSTANCES_v1

**Scope:** Concrete fixture instances for Cognitive Adequacy harness cases. Doctrine-only; no runtime code. Each case has stable IDs, synthetic data, and expected outcomes.

## Conventions
- `conf`: confidence value
- `status`: proposal status
- `action`: audit/status action (reject/ignore/approve/view)
- `chk`: checkpoint id
- All timestamps are ISO strings; ordering implied by suffix numbers.

## SECTION 1 — FIXTURE INSTANCES

### Case CA-REP-SHALLOW-1 (Repetitive Shallow Proposals)
- Loop/task: loopA / task: "coverage_gap"
- Proposals (lineage):
  - p1: conf 0.38, status pending, shallow text v1, chk c1
  - p2: conf 0.39, status pending, shallow text v1.1, chk c2
  - p3: conf 0.37, status pending, shallow text v1.2, chk c3
- Audit/status: no approvals; views only
- Flags: none
- Expected: inadequacy triggered (repetition/shallow), adequacy score ↓, references p1–p3, emit proposal.

### Case CA-REJECT-1 (Repeated Rejects/Ignores)
- Loop/task: loopB / task: "stale_docs"
- Proposals:
  - p4 conf 0.55 status pending → audit: rejected
  - p5 conf 0.52 status pending → audit: ignored
  - p6 conf 0.48 status pending → audit: rejected
  - p7 conf 0.50 status pending → audit: ignored
  - p8 conf 0.53 status pending → audit: rejected
- Reject/ignore ratio: 5/5 (100%) over window 5
- Expected: inadequacy triggered (low usefulness), adequacy score ↓, refs p4–p8, emit proposal.

### Case CA-LOWCONF-1 (Low-Confidence Streak)
- Loop/task: loopC / task: "triage_missing_context"
- Proposals:
  - p9 conf 0.35, status pending
  - p10 conf 0.30, status pending
  - p11 conf 0.32, status pending
- Streak: 3 proposals < 0.4
- Expected: inadequacy triggered (low confidence streak), score ↓, refs p9–p11, emit proposal.

### Case CA-SAMEFIX-1 (Same-Fix Loop)
- Loop/task: loopD / task: "env_setup"
- Proposals:
  - p12 conf 0.45, status pending, fix="reinstall deps"
  - p13 conf 0.47, status pending, fix="reinstall deps" (unchanged)
  - p14 conf 0.46, status pending, fix="reinstall deps" (unchanged)
- No acceptance/status change
- Expected: inadequacy triggered (same fix repeated), score ↓, refs p12–p14, emit proposal.

### Case CA-NO-IMPROVE-1 (No Improvement After Cycles)
- Loop/task: loopE / task: "data_sync"
- Window1 (4 props): p15 conf 0.41, p16 conf 0.43, p17 conf 0.42, p18 conf 0.44 (no approvals)
- Window2 (next 4): p19 conf 0.40, p20 conf 0.42, p21 conf 0.41, p22 conf 0.43 (no approvals)
- Trend: no confidence lift; no acceptance
- Expected: inadequacy triggered (no improvement), score ↓, refs p15–p22, emit proposal.

### Case CA-E2A-1 (Evidence-to-Action Failure)
- Loop/task: loopF / task: "incident_response"
- Window (4 props):
  - p23 cites evidence E1, conf 0.55, no actionable steps
  - p24 cites evidence E2, conf 0.56, no actionable steps
  - p25 conf 0.58, actionable (control)
  - p26 conf 0.57, actionable (control)
- Failure count: 2 in window of 4
- Expected: inadequacy triggered (evidence-to-action failure), score ↓, refs p23–p24 (and window context), emit proposal.

### Guard Case CA-GUARD-OP-1 (Operator-Requested Repetition)
- Loop/task: loopG / task: "run_same_check"
- Proposals: p27 conf 0.55, p28 conf 0.56, p29 conf 0.57 (repetitive by request)
- Flag: operator_requested_repetition = true
- Expected: no inadequacy; score neutral; no proposal; suppression reason = operator request.

### Guard Case CA-GUARD-LOW-SAMPLE-1 (Low Sample)
- Loop/task: loopH / task: "small_batch"
- Proposals: p30 conf 0.35, p31 conf 0.33 (only 2 samples)
- Expected: no trigger (sample < 3); score neutral; no proposal; suppression reason = low sample.

### Guard Case CA-GUARD-EXPLORE-1 (Exploratory Improving Trend)
- Loop/task: loopI / task: "explore_mode"
- Proposals: p32 conf 0.30 → p33 conf 0.36 → p34 conf 0.42
- Flag: exploratory_window=true; improving trend +0.06/+0.06
- Expected: no trigger; score neutral; no proposal; suppression reason = exploratory improving trend.

## SECTION 2 — EXPECTED OUTCOME PER INSTANCE
- CA-REP-SHALLOW-1: score ↓; reason repetition/shallow; refs p1–p3; emit proposal.
- CA-REJECT-1: score ↓; reason low usefulness; refs p4–p8; emit proposal.
- CA-LOWCONF-1: score ↓; reason low confidence streak; refs p9–p11; emit proposal.
- CA-SAMEFIX-1: score ↓; reason same fix; refs p12–p14; emit proposal.
- CA-NO-IMPROVE-1: score ↓; reason no improvement; refs p15–p22; emit proposal.
- CA-E2A-1: score ↓; reason evidence-to-action failure; refs p23–p24 (+window context); emit proposal.
- CA-GUARD-OP-1: score neutral; reason suppressed by operator request; no proposal.
- CA-GUARD-LOW-SAMPLE-1: score neutral; reason suppressed by low sample; no proposal.
- CA-GUARD-EXPLORE-1: score neutral; reason suppressed by exploratory improving trend; no proposal.

## SECTION 3 — CASE NAMING
Stable IDs: CA-REP-SHALLOW-1, CA-REJECT-1, CA-LOWCONF-1, CA-SAMEFIX-1, CA-NO-IMPROVE-1, CA-E2A-1, CA-GUARD-OP-1, CA-GUARD-LOW-SAMPLE-1, CA-GUARD-EXPLORE-1.

## SECTION 4 — NEXT STEP
- Seek approval to implement the adequacy harness using these fixtures; then code harness/tests against these instances.
