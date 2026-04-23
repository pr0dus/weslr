# SELF_IMPROVEMENT_SPINE_V1.md — WESLR Self-Improvement Spine

**Status:** CANONICAL — selected architecture
**Date:** 2026-04-21
**Derived from:** `docs/WESLR_CANONICAL_SELF_MODEL_V1.md` Sections 7, 11, 12, 16
**Authoritative for:** All future self-improvement integration, proposal routing, and architecture decisions

---

## SECTION 1 — FILES CHANGED

| File | Change |
|------|--------|
| `docs/SELF_IMPROVEMENT_SPINE_V1.md` | **Created** — this document |

No production code files modified. No schema changes. No behavior changes.

---

## SECTION 2 — COMMANDS RUN

None. This pass is documentation-only.

---

## SECTION 3 — DOCUMENT CONTENT

### Section 4 — Selected Canonical Spine

**Chosen lane: Inadequacy/CDI Proposal Lane (Lane A)**

This is the only lane with a complete, governed end-to-end path from signal to audit. All other lanes are repositioned relative to it (see Section 7).

---

#### Full Spine Flow

```
STEP 1 — SIGNAL
  Module/function:  inadequacy_persistence.record_inadequacy_event(metadata)
  Input:           runtime failure event (runtime_state != "healthy")
  Output:          weslr_inadequacy_events.jsonl (one JSONL line per event)
  Governance:      None — event logging only, no operator action required

STEP 2 — TRIGGER FORMATION
  Module/function:  inadequacy_trigger.find_candidates(now)
  Input:            inadequacy_events.jsonl (last 60 minutes)
  Logic:            Group by category; score recurrence ≥ 2 or severity=high
  Output:           Candidate list with trigger_id, trigger_confidence,
                    readiness_for_CDI flag
  Governance:      Threshold-based (not operator-gated)

STEP 3 — HANDOFF CREATION
  Module/function:  inadequacy_handoff.create_handoffs(now)
  Input:            Candidates with readiness_for_CDI=True
  Output:           weslr_inadequacy_handoffs.jsonl (lineage_ref, evidence_refs)
  Governance:      readiness_for_CDI gating only

STEP 4 — INTAKE QUALIFICATION
  Module/function:  inadequacy_intake.qualify_handoffs(now)
  Input:            handoffs.jsonl
  Logic:            Filter: trigger_confidence ≥ 0.7 OR severity=high
                    Deduplicate by handoff_id
  Output:           weslr_inadequacy_intake.jsonl
  Governance:      Confidence threshold (not operator-gated)

STEP 5 — SYNTHESIS
  Module/function:  DeterministicSynthesisEngine.synthesize_all(records)
  Input:            Existing records (events, proposals, approvals, confidence)
  Logic:            Five synthesis modes (read-only):
                    - synthesize_patterns()
                    - synthesize_approval_reasons()
                    - synthesize_proposal_outcomes()
                    - synthesize_confidence_trends()
                    - synthesize_bottleneck_recurrences()
  Output:           DeterministicSynthesisResult (pattern_groupings,
                    approval_reason_groupings, proposal_outcome_groupings,
                    confidence_trend_summaries, bottleneck_recurrence_summaries)
  Governance:      Read-only — no mutation, no recommendations

STEP 6 — PROPOSAL PACKAGING
  Module/function:  InsightProposalConverter.convert(synthesis_result)
  Input:            DeterministicSynthesisResult
  Logic:            Transform synthesis outputs into InsightProposalPayload
                    objects — one payload per synthesis category
  Output:           List[InsightProposalPayload]
  Modules:          insight_proposal_layer.py (InsightProposalPayload,
                    InsightProposalConverter)
  Governance:      Read-only transformation — no autonomous execution

STEP 7 — EXPLANATION
  Module/function:  cognitive_dialogue_integration.build_cdi_bundle(adequacy_finding)
  Input:            Adequacy finding dict (from Step 2 hook or re-evaluation)
  Logic:            Three-function CDI lane:
                    - explain_inadequacy() → inadequacy explanation
                    - propose_improvement() → improvement proposal dict
                    - handle_operator_response() → approve/deny/refine outcome
  Output:           CDI bundle: {explanation, proposal, operator_outcome, lineage_ref}
  Governance:      All consequential actions carry requires_approval: True
  Governance:      Proposal output: pending_review / approved / denied
  Note:             build_cdi_bundle() not yet auto-triggered from Steps 1-6
                    (gap — see Section 9)

STEP 8 — OPERATOR REVIEW
  Module/function:  ExecutionGate.transition_state(proposal_id, "approved"|"denied")
  Input:            InsightProposalPayload or self_eval / improvement_engine output
  Logic:            State machine: pending → approved / denied
                    State transitions logged with actor + timestamp + details
  Output:           Updated proposal state; audit entry in AuditLedgerEngine
  Governance:      Operator-only — no autonomous state transitions to approved

STEP 9 — EXECUTION
  Module/function:  ExecutionGate.execute_proposal_if_approved(proposal_id)
  Input:            Approved proposal
  Logic:            Execute only if state == "approved"
                    Record execution event in audit trail
  Output:           Execution result; audit entry
  Governance:      ExecutionGate.is_approved_for_execution() gate is mandatory
                    No bypass path exists

STEP 10 — AUDIT
  Module/function:  AuditLedgerEngine.record_proposal_created/approved/denied/executed()
  Input:            All of the above — audit entries written at each step
  Output:           Immutable audit trail (append-only JSONL per ledger)
  Governance:      Audit entries are permanent records; not editable
                    trace_summary retrievable by object_id
```

---

### Section 5 — Why This Spine

**Why Lane A is the strongest candidate:**

1. **Only lane with a formally governed ExecutionGate.** Every other lane either has no execution path or has an advisory-only path (`recommendations.json`, self_eval `needs_approval: True` logging). Lane A is the only lane where the ExecutionGate is actually enforced — `is_approved_for_execution()` is a hard gate, not advisory.

2. **Complete signal-to-audit chain.** Every other lane is missing at least one critical step:
   - Lane B (adequacy hook): ends at finding, no proposal → operator review path
   - Lane C (self_eval): ends at speech generation, proposals logged but never reach ExecutionGate
   - Lane D (improvement_engine): ends at recommendations.json, no ExecutionGate
   - Lane E (drift): ends at acknowledgment, concerns never converted to proposals
   - Lane F (self_architecture): produces ChangeProposals but not via ExecutionGate

3. **Bounded write authority.** `inadequacy_persistence.py` writes to `inadequacy_events.jsonl` — bounded JSONL, not arbitrary file writes. `change_proposals.py` owns the proposal lifecycle. No other module writes to these files.

4. **Threshold governance.** Steps 2, 3, 4 use explicit numeric thresholds (recurrence ≥ 2, confidence ≥ 0.7, severity override). These are inspectable and tunable without architectural change.

5. **Audit trail completeness.** Steps 1, 3, 4, 8, 9, 10 all produce audit entries. The audit ledger is the authoritative record of what was proposed, approved, denied, and executed.

**Why other lanes are not primary:**

| Lane | Reason Not Primary |
|------|--------------------|
| Lane B (adequacy hook) | Produces findings only — no auto-proposal path, no operator review, no execution |
| Lane C (self_eval) | Dead-ends at speech generation; proposals never route to ExecutionGate |
| Lane D (improvement_engine) | Advisory only — recommendations.json goes to operator file review, not formal governance |
| Lane E (drift loop) | Concerns surface → acknowledge/dismiss → forgotten; never converted to proposals |
| Lane F (self_architecture) | Comparison engine only — not a proposal-to-execution path |
| Lane G (get_self_summary) | Read-only query surface — no write path, no proposal generation |

---

### Section 6 — System Repositioning

All seven existing lanes are now repositioned relative to the canonical spine.

#### FEEDERS (input signals to the spine)

| Lane | How It Feeds the Spine |
|------|------------------------|
| **Lane B — Adequacy Hook** | Produces `inadequate` findings. These inform whether to trigger a handoff. The hook is the primary readiness signal for Step 1. |
| **Lane C — Self-Directed Growth** | Produces proposals from identity/affect state. These should be converted to InsightProposalPayload and routed through Steps 7-10 via ExecutionGate. |
| **Lane D — Improvement Engine** | Produces ranked recommendations from test/security reflection + operator reviews. These should be normalized to ExecutionGate proposals rather than output to recommendations.json. |
| **Lane E — Drift Loop** | Surfaces `Reflection` concerns. Each concern with `status=PENDING` should be evaluated for whether it qualifies as an inadequacy signal → handoff → intake → spine. |

#### VALIDATORS (evaluation layers within or adjacent to the spine)

| Layer | Role |
|-------|------|
| **Cognitive Reflection** (`cognitive_reflection.run_reflection()`) | Runs a bounded consistency pass on proposals before they enter the proposal path. Produces `consistency_notes` attached to adequacy findings. No writes. |
| **Deterministic Synthesis Engine** (`deterministic_synthesis.py`) | Read-only analysis layer. Validates that proposals are grounded in existing patterns before packaging. Not a validator in the governance sense — it produces evidence, not approvals. |

#### ANALYSIS TOOLS (non-authoritative, informational)

| Tool | Role |
|------|------|
| **Operator Insight Systems** (`operator_insight_comparison.py`, `operator_insight_timeline.py`, etc.) | Provide drift analysis, timeline views, and recovery insight. Read-only. Feed context to the spine but do not trigger it. |
| **Unifying Self-Model Query** (`institution.get_self_summary()`) | Composes a read-only 6-layer summary. Informational only. Not a governance input. |

#### PARALLEL (not yet integrated — not forbidden, but not governed)

| System | Status |
|--------|--------|
| **Self-Architecture A/B Lane** (`self_architecture.py`, `TradeoffEngine`) | Produces `ComparisonResult` and `ChangeProposal` objects. Currently operates independently of ExecutionGate. Intended to feed the spine once an integration path is defined. |
| **Improvement Engine** (`improvement_engine.py`) | Produces recommendations to `recommendations.json`. Currently parallel. Intended to normalize to ExecutionGate in a future integration step. |
| **Self-Eval Proposals** (`self_eval.py`, `self_apply_changes()`) | Currently dead-ends at logging. Intended to route to ExecutionGate. |

---

### Section 7 — Integration Rules

These rules are binding for all current and future self-improvement code.

**Rule 1 — All consequential improvement must pass through the spine.**

Any code that generates a proposal, evaluates a signal, or triggers a governance action must either:
- (a) Be part of the spine itself (Steps 1-10), or
- (b) Feed into the spine as a Feeder via a defined integration point

No new self-improvement code may create a new parallel execution path that bypasses Steps 7-10.

**Rule 2 — No parallel execution paths without a canonical document.**

Before any new lane can produce proposals that reach ExecutionGate, a canonical document must be written defining:
- The lane's entry point and trigger
- How it feeds the spine (which Step 1 function it calls or which Step 7 bundle it populates)
- Its governance contract

This document must be approved before code lands.

**Rule 3 — No bypass of ExecutionGate.**

`ExecutionGate.is_approved_for_execution()` is a hard gate. No code may call `execute_proposal_if_approved()` without passing through it. No shortcut may be added to bypass the gate for any lane, including feeders.

**Rule 4 — No direct state mutation outside write-authority modules.**

| File | What It May Write |
|------|-----------------|
| `inadequacy_persistence.py` | `weslr_inadequacy_events.jsonl` |
| `inadequacy_handoff.py` | `weslr_inadequacy_handoffs.jsonl` |
| `inadequacy_intake.py` | `weslr_inadequacy_intake.jsonl` |
| `change_proposals.py` | `change_proposals.json` (via `ExecutionGate`) |
| `AuditLedgerEngine` | Audit ledger files |

No other module may write to any of these files directly.

**Rule 5 — All proposals must carry `requires_approval: True` until execution.**

Any proposal dict, payload, or change object that has not passed ExecutionGate approval must carry `requires_approval: True` or equivalent. Proposals may not set themselves to `approved` or `executed` without operator action through the governance surface.

**Rule 6 — Feeder outputs must be normalizable to InsightProposalPayload.**

When a Feeder lane (Lane C, Lane D, Lane E) is integrated, its output must be convertible to an `InsightProposalPayload` or a `ChangeProposal` record that the ExecutionGate can process. New proposal schemas may not proliferate without a normalization layer.

**Rule 7 — Audit entries are mandatory at each spine step.**

Steps 1, 3, 4, 8, 9, 10 must produce audit entries. Feeder integrations must add audit entries at their entry points as well. The audit trail is the authoritative record of the self-improvement system — it must be complete.

---

### Section 8 — Current Limitations

The following gaps prevent full unification today. They are documented here as known constraints. Solutions are deferred to later steps.

**Limitation 1 — CDI bundle not auto-triggered.**

`cognitive_dialogue_integration.build_cdi_bundle()` is the canonical explanation layer for proposals. It is not called automatically from Step 6 (proposal packaging). The auto-path ends at `InsightProposalExporter` output. Operator review of the proposal requires manual routing or a separate invocation.

**Limitation 2 — Self-eval proposals not in ExecutionGate.**

`self_eval.self_apply_changes()` logs proposals with `needs_approval: True` but produces them as plain dicts — not `ChangeProposal` records. There is no integration path from self_eval to `ExecutionGate.transition_state()`.

**Limitation 3 — Improvement engine outputs to file, not to ExecutionGate.**

`WeslrImprovementEngine.build_operator_proposals()` writes to `continuity/improvement_engine/recommendations.json`. The operator reviews this file directly. No formal review path, no ExecutionGate connection, no audit trail for the review decision.

**Limitation 4 — Drift loop not connected to proposals.**

`run_drift_observation_pass()` produces `Reflection` objects. These are acknowledged or dismissed via `acknowledge_reflection()`. There is no code path from a concern's `status=PENDING` to `inadequacy_persistence.record_inadequacy_event()` or any Step 1 function.

**Limitation 5 — Proposal format fragmentation.**

Four proposal schemas exist: `InsightProposalPayload`, `ChangeProposal` (change_proposals.py), improvement_engine plain dict, self_eval plain dict. No normalization layer converts between them. Until this is resolved, feeders cannot cleanly integrate.

**Limitation 6 — No unified proposal review surface.**

The operator cannot see all active proposals in one view. `InsightProposalExporter` outputs are separate from `recommendations.json` and self_eval output. No single surface consolidates pending, approved, denied, and executed proposals across all lanes.

**Limitation 7 — No self-healing loop closure.**

Detection exists (adequacy, drift). Proposal exists (multiple types). Approval exists (ExecutionGate for Lane A). Execution exists (`execute_proposal_if_approved()`). Verification does not exist — there is no step that confirms execution produced the expected outcome and feeds that back into the synthesis layer.

---

## SECTION 4 — STOP LINE

**Confirmed:**
- Documentation only ✅
- No production code changes ✅
- No schema changes ✅
- No behavior changes ✅
- No modifications to `WESLR_CANONICAL_SELF_MODEL_V1.md` or any other file ✅
- New document created: `docs/SELF_IMPROVEMENT_SPINE_V1.md` ✅
- No parallel execution paths created ✅
- No ExecutionGate bypass added ✅

**Stop after this pass. No code changes. No modifications to existing files.**

---

*Derived from `docs/WESLR_CANONICAL_SELF_MODEL_V1.md` — Sections 7, 11, 12, 16. This is the canonical self-improvement spine reference document. All future integration work must reference this document before touching self-improvement code.*
