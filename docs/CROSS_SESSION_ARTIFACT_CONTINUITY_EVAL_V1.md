# CROSS-SESSION ARTIFACT CONTINUITY EVALUATION V1
**Generated:** 2026-04-22 07:20 GMT+2  
**Purpose:** Design validation suite for artifact continuity across sessions, not just within a single runner chain  
**Mode:** STRICT — design only, no code changes, no scoring changes, no routing changes, no automatic improvement  
**Authoritative Context:** `docs/WESLR_FUNCTIONAL_TREE_MAP_V1.md`, existing eval artifact shape from `continuity/artifacts/eval/`

---

## SECTION 1 — PURPOSE

### Why Short-Chain Evaluation Is Insufficient

The current evaluation infrastructure (`relevance_eval_runner.py`, `relevance_eval_analysis.py`) tests artifact and relevance behavior within a **single execution chain** — one session, one continuous run of the eval runner. This is necessary and correct as a first pass.

However, WESLR's **actual ambition** is continuity across sessions and longer time horizons. The current eval runner:

- Clears session context between eval runs (intentionally — each eval starts fresh)
- Tests reference resolution within a single session context
- Does not test whether **active artifact survives a session boundary**
- Does not test whether **registry state persists correctly** after session reset
- Does not test **stale artifact behavior** after time has passed
- Does not test **contamination** between unrelated sessions

Short-chain eval tells us: "within a session, does artifact reference work?"  
It does NOT tell us: "after a session ends and a new one starts, does the system maintain correct artifact continuity?"

These are fundamentally different failure modes.

### Why WESLR Must Be Tested Across Sessions

WESLR is built on the premise that:

1. Artifacts persist — what was generated in session 1 is still retrievable in session 2
2. Active artifact is a session-level pointer that should survive session boundaries (or gracefully clear)
3. Reference resolution is stable — "improve this" in session 2 resolves to the correct artifact, not a stale or wrong one
4. Relevance does not contaminate — interests from session 1 do not bleed into session 2 inappropriately
5. Domain shifts are handled — if session 1 was about photovoltaics and session 2 is about tax law, session 2 starts clean

If any of these assumptions break silently, the operator loses trust in the system. The only way to validate these assumptions is to **simulate session boundaries** in evaluation — not just within-session turns.

---

## SECTION 2 — WHAT MUST BE VALIDATED

### 2.1 Artifact Persistence Across Sessions
**Test:** An artifact created in session 1 must be retrievable in session 2 via `get_artifact(artifact_id)` using the ID logged during session 1.

**Pass criteria:** Artifact content matches exactly what was stored in session 1. No mutation, no data loss.

**Fail criteria:** Artifact missing, corrupted, or content changed. Index mismatch.

### 2.2 Active Artifact Continuity
**Test:** After session 1 sets an active artifact and session 2 starts, `get_active_artifact(session_id)` must return the correct artifact or null (not stale wrong pointer).

**Pass criteria:** Active artifact is correct for session 2 context, or gracefully null if session 1 artifact is not applicable.

**Fail criteria:** Active artifact points to wrong artifact, stale pointer, or session contamination.

### 2.3 Reference Resolution After Time/Session Change
**Test:** In session 2, user says "improve this" or "explain this" — system must resolve to the correct artifact from session 1 (or correctly return safe empty message if no artifact should be active).

**Pass criteria:** Reference resolves correctly. If session 1 artifact should be active, it is. If context requires null, safe path is returned.

**Fail criteria:** Wrong artifact resolved, crash, artifact created from nothing.

### 2.4 Explanation/Revision Continuity
**Test:** An artifact explained in session 1 retains its identity when revision is requested in session 2.

**Pass criteria:** Revision is based on correct artifact. Content is consistent with prior artifact context. No explanation drift.

**Fail criteria:** Revision targets wrong artifact, explanation is inconsistent with artifact content.

### 2.5 Contextual Relevance Coherence Across Sessions
**Test:** Relevance interests from session 1 must not inappropriately influence session 2. Session 2 starts with a clean or correctly initialized interest state.

**Pass criteria:** Session 2 interests are correctly initialized — either empty or based on explicit operator action, not residual from session 1.

**Fail criteria:** Interests from session 1 contaminate session 2 (e.g., photovoltaic interest active in tax law session).

### 2.6 Safe Behavior When Continuity Is Missing or Stale
**Test:** When artifact is missing, registry is inconsistent, or session references a stale ID, system returns safe empty message or graceful error — not crash, not silent hallucination.

**Pass criteria:** Safe path is returned. `safe_response: true` in eval artifact. No 500, no wrong artifact served.

**Fail criteria:** Crash, wrong artifact served, silent data mutation.

---

## SECTION 3 — SCENARIO CATALOG

### csc-001: Session 1 Generate → Session 2 Explain It
**Setup:** Session 1 generates artifact A. Session 1 ends.
**Test:** Session 2 user says "explain this artifact" (or similar reference phrase).
**Expected:** Artifact A is resolved and explained. Content matches what was generated in session 1.
**Validation:** `reference_resolution_result = "resolved_correct"`, artifact content matches session 1 original.

---

### csc-002: Session 1 Generate → Session 2 Improve This
**Setup:** Session 1 generates artifact A and user approves it (active artifact set). Session 1 ends.
**Test:** Session 2 user says "improve this" without any other context.
**Expected:** System resolves to artifact A. Proposed improvement targets artifact A specifically.
**Validation:** `reference_resolution_result = "resolved_correct"`, improvement targets correct artifact ID.

---

### csc-003: Multiple Artifacts — Correct Active Reference
**Setup:** Session 1 generates artifact A, then artifact B (B becomes active). Session 1 ends.
**Test:** Session 2 user says "improve this" or "revise that".
**Expected:** "improve this" resolves to B (most recent active). "revise that" — depends on what "that" refers to (if ambiguous, safe path returned).
**Validation:** Active artifact before session 2 = B. Reference resolves to B. If "that" is ambiguous, safe path.

---

### csc-004: Domain Shift Across Sessions
**Setup:** Session 1 generates artifact about photovoltaic efficiency. Session 1 ends.
**Test:** Session 2 starts with a different domain context (e.g., tax law). User asks about tax topics, then says "improve this".
**Expected:** Session 2 starts with no photovoltaic interests active. When "improve this" is called, either no active artifact exists (safe path) or any artifact from session 2 is correctly resolved — not the photovoltaic artifact.
**Validation:** `cross_domain_contamination_flag = false`. Session 2 interest state is clean.

---

### csc-005: Stale Artifact Reference
**Setup:** Session 1 generates artifact A. Registry or index becomes inconsistent (simulate by manually removing artifact file but keeping index entry). Session 1 ends.
**Test:** Session 2 user says "explain artifact [ID of A]" or "improve this" expecting A.
**Expected:** Graceful handling — artifact not found, safe path returned. No crash, no serving wrong artifact.
**Validation:** `reference_resolution_result = "not_found_safe"`, `safe_path_ok = true`, no crash.

---

### csc-006: Missing Artifact Safe Path
**Setup:** Session 1 generates no artifacts. Session 1 ends.
**Test:** Session 2 user says "improve this" or "explain this artifact".
**Expected:** Safe empty message returned. No artifact created from nothing. No crash.
**Validation:** `reference_resolution_result = "no_artifact_safe"`, `safe_response = true`, `total_artifacts_created = 0`.

---

### csc-007: Repeated Revision Over Separated Sessions
**Setup:** Session 1 generates artifact A. User says "improve this" → revision A' created (A' becomes active). Session 1 ends.
Session 2 starts. User says "improve this" → revision A'' created. Session 2 ends.
**Test:** Session 3 starts. User asks "what is the current version of the artifact?"
**Expected:** Current version is A'' (latest revision). Chain of revisions (A → A' → A'') is preserved.
**Validation:** Version chain is intact. A'' is retrievable. A is still in store (archivable, not deleted).

---

### csc-008: Relevance Persistence vs Contamination
**Setup:** Session 1 user discusses photovoltaic systems — interests "photovoltaic" and "efficiency" are tracked. Session 1 ends.
Session 2 user starts with unrelated topic (e.g., accounting).
**Test:** Immediately after session 2 start, check interest state. Then user introduces a new interest in session 2.
**Expected:** Session 2 starts clean (photovoltaic/efficiency interests not active). New interest in session 2 is correctly tracked.
**Validation:** No photovoltaic/efficiency interests in session 2 start. New interest tracked correctly. `cross_domain_contamination_flag = false`.

---

### csc-009: Active Artifact Override by Explicit Request
**Setup:** Session 1 generates artifact A (becomes active). Session 1 ends.
Session 2 starts. Session 2 user generates artifact B (becomes active).
**Test:** Session 2 user says "work with artifact B" (explicit targeting), then says "improve this" (should target B, not A).
**Expected:** "improve this" targets B (current active), not A.
**Validation:** Active artifact before "improve this" = B. Reference resolves to B.

---

### csc-010: Session Boundary — Operator Context Switch
**Setup:** Session 1 operator context is "technical operator". Session 1 generates artifact A about technical content. Session 1 ends.
Session 2 operator context is "teacher" persona. Session 2 user says "explain this".
**Expected:** Explanation is in "teacher" persona context, not technical operator. Artifact content is still correctly resolved.
**Validation:** Artifact content matches session 1. Explanation style/persona matches session 2 context. Both preserved.

---

### csc-011: Registry Corruption Safe Path
**Setup:** Index lists artifact A, but A.json is missing from disk. Session 1 ended with A in index.
**Test:** Session 2 attempts to resolve "improve this" expecting A.
**Expected:** Safe path — index is corrected (A entry removed or marked invalid) or artifact is flagged as unavailable. No crash, no serving non-existent artifact as real.
**Validation:** `reference_resolution_result = "index_inconsistency_safe"`, system state remains consistent, no crash.

---

### csc-012: Cross-Session Revision Lineage Audit
**Setup:** Session 1 generates artifact A. Session 1 revision → A'. Session 1 ends.
Session 2 continues revision → A''. Session 2 ends.
Session 3 starts and requests revision history.
**Test:** Request artifact lineage/provenance for current active artifact.
**Expected:** Lineage shows A → A' → A'' with timestamps and session IDs. Complete audit trail across 3 sessions.
**Validation:** All three versions present. Session IDs correctly associated with each version. Lineage is reconstructable.

---

## SECTION 4 — EVALUATION ARTIFACT SHAPE

Every cross-session continuity evaluation produces an artifact in `continuity/artifacts/eval/` with this shape:

```json
{
  "evaluation_id": "csc-001-1776834000000-1",
  "created_at": "2026-04-22T05:20:00Z",
  "scenario_id": "csc-001",
  "scenario_title": "Session 1 Generate → Session 2 Explain It",

  "cross_session": true,

  "session_sequence": [
    {
      "session_id": "session-001",
      "turns": [
        {
          "turn": 1,
          "input_message": "analyze this photovoltaic setup and suggest improvements",
          "response_source": "artifact_proposal",
          "artifact_lifecycle_stage": "generation",
          "active_artifact_before": null,
          "active_artifact_after": "art-1776800000001-1",
          "relevant_interests_snapshot": [
            {"id": "...", "name": "photovoltaic", "score": 5, ...},
            {"id": "...", "name": "efficiency", "score": 4, ...}
          ]
        }
      ],
      "artifacts_created": ["art-1776800000001-1"],
      "session_end": "normal"
    },
    {
      "session_id": "session-002",
      "turns": [
        {
          "turn": 1,
          "input_message": "explain this",
          "response_source": "artifact_reference",
          "artifact_lifecycle_stage": "reference",
          "active_artifact_before": "art-1776800000001-1",
          "active_artifact_after": "art-1776800000001-1",
          "reference_resolution_result": "resolved_correct",
          "resolved_artifact_id": "art-1776800000001-1",
          "relevant_interests_snapshot": []
        }
      ],
      "artifacts_created": [],
      "session_end": "normal"
    }
  ],

  "artifact_ids_involved": ["art-1776800000001-1"],

  "continuity_assessment": {
    "artifact_persistence": "pass",
    "active_artifact_continuity": "pass",
    "reference_resolution": "pass",
    "safe_path_handling": "pass",
    "relevance_coherence": "pass",
    "cross_session_contamination": false
  },

  "auto_flags": {
    "revision_drift": false,
    "artifact_context_leak_flag": false,
    "cross_domain_contamination_flag": false,
    "incorrect_continuity": false,
    "safe_path_ok": true,
    "index_inconsistency_detected": false,
    "total_artifacts_created": 1
  },

  "contamination_flags": {
    "interest_bleed_from_session_1_to_2": false,
    "artifact_id_confusion": false,
    "active_artifact_confusion": false,
    "domain_context_contamination": false
  },

  "assessment": {
    "continuity_correctness": "pass",
    "reference_stability": "stable",
    "artifact_identity_correctness": "correct",
    "contextual_relevance_stability": "stable",
    "contamination_resistance": "resistant",
    "operator_readability": "clear"
  },

  "notes": "Pass — session 2 correctly resolved the artifact from session 1.",
  "recommended_followup": null,

  "eval_meta": {
    "evaluated_by": "cross_session_artifact_eval_v1",
    "eval_version": "v1_csc",
    "source_module": "weslr/cross_session_artifact_eval.py"
  }
}
```

**Field Reference:**

| Field | Type | Description |
|-------|------|-------------|
| `evaluation_id` | string | Unique ID: `csc-{scenario_id}-{timestamp}-{seq}` |
| `scenario_id` | string | From scenario catalog (csc-001 through csc-012) |
| `cross_session` | boolean | Always `true` for this eval type |
| `session_sequence` | array | Ordered list of sessions; each has `session_id`, `turns`, `artifacts_created`, `session_end` |
| `artifact_ids_involved` | array | All artifact IDs across all sessions in this evaluation |
| `continuity_assessment` | object | Per-dimension pass/fail: artifact_persistence, active_artifact_continuity, reference_resolution, safe_path_handling, relevance_coherence, cross_session_contamination |
| `auto_flags` | object | Runtime flags from existing eval shape + `index_inconsistency_detected` |
| `contamination_flags` | object | Specific contamination checks: interest_bleed, artifact_id_confusion, active_artifact_confusion, domain_context_contamination |
| `assessment` | object | 6-dimension judgment rubric scores |
| `notes` | string | Human-readable notes on what was observed |
| `recommended_followup` | string | What to investigate if issues found (not an action item) |
| `eval_meta` | object | Eval provenance: `evaluated_by`, `eval_version`, `source_module` |

---

## SECTION 5 — SCORING / JUDGMENT RUBRIC

### 5.1 Continuity Correctness
**Scale:** `pass` / `partial` / `fail`

**Pass:** All artifacts persist across session boundaries correctly. Active artifact continuity holds. No data loss or corruption.

**Partial:** Artifact persists but minor inconsistency (e.g., index update delayed, active artifact not set correctly). System self-corrects within evaluation window.

**Fail:** Artifact missing or corrupted. Active artifact continuity broken. Data loss.

### 5.2 Reference Stability
**Scale:** `stable` / `degraded` / `unstable`

**Stable:** Reference resolution always returns the correct artifact for the given context across all sessions.

**Degraded:** Some references resolve correctly but with noticeable delay or require retry. No wrong artifacts served.

**Unstable:** References sometimes resolve to wrong artifact, or resolution fails intermittently. Wrong artifact served.

### 5.3 Artifact Identity Correctness
**Scale:** `correct` / `drifted` / `corrupted`

**Correct:** Artifact content is identical from creation to retrieval across sessions. No silent modification.

**Drifted:** Artifact content has changed in ways not explicitly requested by operator. Subtle mutation.

**Corrupted:** Artifact content is unreadable or materially different in a way that indicates data corruption.

### 5.4 Contextual Relevance Stability
**Scale:** `stable` / `contaminated` / `lost`

**Stable:** Interest state in session N+1 is correctly initialized — no bleed from session N, no contamination.

**Contaminated:** Interests from prior session inappropriately influence current session.

**Lost:** Valid interests from current session are not tracked or are incorrectly dropped.

### 5.5 Contamination Resistance
**Scale:** `resistant` / `leaky` / `compromised`

**Resistant:** Session boundaries are respected. No cross-session contamination in artifact registry, active artifact, or interest state.

**Leaky:** Minor contamination detected (e.g., one interest bleeds across). System does not corrupt but is observably impure.

**Compromised:** Major contamination — wrong artifact used, active artifact confusion, or systematic interest pollution.

### 5.6 Operator Readability
**Scale:** `clear` / `confusing` / `opaque`

**Clear:** Eval artifacts and system behavior are understandable. Operator can reconstruct what happened across sessions.

**Confusing:** Some behavior is not immediately explainable from eval artifact. Requires investigation.

**Opaque:** Eval artifact does not capture enough to reconstruct events. Behavior inexplicable from available data.

---

## SECTION 6 — SATUI / OPERATOR VIEW

### 6.1 Cross-Session Eval Dashboard
SatUi should expose a view that shows:

- **Recent cross-session evaluations** — last N eval artifacts, filterable by scenario_id
- **Continuity correctness rate** — percentage of evaluations with `continuity_correctness = pass`
- **Contamination alerts** — any evaluation with `contamination_flags` fields set to `true` highlighted in orange/red
- **Session chain viewer** — for a given evaluation_id, show the session sequence with artifact creation/reference events

### 6.2 Eval Artifact Display
When viewing a cross-session eval artifact in SatUi:

```
CROSS-SESSION CONTINUITY EVAL

evaluation_id: csc-001-1776834000000-1
scenario: Session 1 Generate → Session 2 Explain It
result: PASS

SESSIONS IN CHAIN:
  [session-001] 1 turn, 1 artifact created
    → art-1776800000001-1 (active)
  [session-002] 1 turn, 0 artifacts created
    → artifact reference resolved to art-1776800000001-1

CONTINUITY ASSESSMENT:
  ✅ artifact_persistence: pass
  ✅ active_artifact_continuity: pass
  ✅ reference_resolution: pass
  ✅ safe_path_handling: pass
  ✅ relevance_coherence: pass
  ✅ cross_session_contamination: false

CONTAMINATION FLAGS: none

RUN BY: cross_session_artifact_eval_v1 | 2026-04-22T05:20:00Z
```

### 6.3 Failure Alert View
When `continuity_assessment` contains `fail` or `partial`, or any `contamination_flags = true`:

```
⚠️ CONTINUITY ISSUE DETECTED

evaluation_id: csc-004-1776834000000-3
scenario: Domain Shift Across Sessions
result: CONTAMINATION DETECTED

ISSUE: photovoltaic interests from session-001 detected in session-002 start state

SESSIONS:
  [session-001] domain: photovoltaic/energy
  [session-002] domain: accounting — but photovoltaic interest still active

RECOMMENDED INVESTIGATION:
  - Check interest_tracker initialization at session start
  - Verify interest state reset on session boundary
  - Review cross-session interest persistence logic

Auto-flags: cross_domain_contamination_flag=true
```

### 6.4 Eval Index View
SatUi should show the eval index with cross-session badges:

```
ARTIFACT EVAL INDEX

[Cross-Session Evals]
  csc-001  ✅  csc-002  ✅  csc-003  ✅  csc-004  ⚠️
  csc-005  ✅  csc-006  ✅  csc-007  ✅  csc-008  ✅
  csc-009  ✅  csc-010  ✅  csc-011  ✅  csc-012  ✅

[Single-Turn Evals]
  sat-001  ✅  sat-002  ✅  ... (existing Phase 1A-1D evals)

CONTINUITY SCORE: 11/12 pass | 1 contamination alert
```

---

## SECTION 7 — FORBIDDEN DRIFT

The following are explicitly forbidden based on cross-session eval results:

### F1 — No Automatic Correction
Eval results must not trigger automatic code changes, config updates, or routing modifications. If contamination is detected, the response is: document the finding, surface it in SatUi, and stop. Operator decides next action.

### F2 — No Hidden Session Rewrites
The eval runner must not silently rewrite session state, artifact store, or registry to make a failing eval pass. The eval must reflect real system behavior, not a system optimized to pass the eval.

### F3 — No Silent Registry Mutation Beyond Normal Behavior
Index updates, artifact creation, and active artifact pointer changes must follow the existing canonical behavior. The eval must not introduce ad-hoc registry mutations to simulate continuity — it tests real continuity, not fabricated continuity.

### F4 — Continuity Eval Is Not Authority
A passing cross-session eval does not establish artifact continuity as "always correct" — it only establishes that the tested scenario worked correctly this time. Similarly, a failing eval does not mandate immediate fix — it surfaces an issue for operator review.

### F5 — No Eval-Driven Proposal Generation
Cross-session eval results must not automatically feed into `self_improvement_proposal.py` or governance pipeline. The operator reviews the eval artifact and decides whether a proposal is warranted.

---

## SECTION 8 — RECOMMENDED FIRST IMPLEMENTATION

### Smallest Safe Implementation

The smallest safe implementation is **a read-only eval runner that simulates session boundaries using the existing artifact infrastructure, without modifying any runtime behavior**.

### Recommended First Implementation Steps

**Step 1: Create `weslr/cross_session_artifact_eval.py`**
- A new Python module, additive only
- Reads existing `artifact_store.py` and `dialogue.py` through their public interfaces
- Uses `continuity/artifacts/eval/` for output (already canonical eval storage)
- Does not modify any existing module

**Step 2: Implement 3 scenarios first (csc-001, csc-006, csc-008)**
- csc-001: Session 1 generate → session 2 explain (tests persistence + reference)
- csc-006: Session 1 empty → session 2 "improve this" (tests safe path)
- csc-008: Session 1 interest domain → session 2 clean start (tests contamination detection)

**Step 3: Session boundary simulation**
- Use a new `session_id` for each "session" in the eval
- After session 1 "ends", simulate session 2 start by:
  - Using a fresh `research_context` dict (simulating new session context)
  - Calling `get_active_artifact(new_session_id)` to check what the runtime returns
  - NOT clearing or modifying the artifact store (real state must remain intact)

**Step 4: Output to existing eval directory**
- Write eval artifacts to `continuity/artifacts/eval/eval-{timestamp}-{seq}.json`
- Update `continuity/artifacts/eval/index.json`
- Reuse existing eval artifact shape (extended with cross-session fields)

**Step 5: Run manually, surface in SatUi**
- Initial runs are manual operator invocations
- Results surfaced in SatUi via existing eval index view
- No automatic scheduling until manually validated

### What NOT To Do First

- Do NOT implement all 12 scenarios at once
- Do NOT modify `artifact_store.py`, `dialogue.py`, or `interest_tracker.py`
- Do NOT hook into runtime execution path
- Do NOT create automatic scheduling (eval runs on demand only initially)
- Do NOT feed eval results into governance pipeline

### Boundary of First Implementation
The first implementation ends when:
- 3 scenarios run successfully against real runtime
- Eval artifacts are written to canonical eval storage
- Operator can view cross-session eval results in SatUi
- No runtime behavior has been modified

---

## SECTION 9 — STOP LINE

**DOCUMENTATION ONLY — NO CODE CHANGES**

This document is a design specification for cross-session artifact continuity evaluation. It was produced by analysis of:
- Existing eval infrastructure (`relevance_eval_runner.py`, `relevance_eval_analysis.py`)
- Existing eval artifact shape (`continuity/artifacts/eval/eval-*.json`)
- Existing artifact storage system (`weslr/artifact_store.py`)
- WESLR Functional Tree Map (`docs/WESLR_FUNCTIONAL_TREE_MAP_V1.md`)

No code was written, no scoring logic was changed, no routing was modified, no governance pipeline was altered.

If any design decision is incorrect or unsafe, document the issue — do not implement around it.

---

*CROSS-SESSION ARTIFACT CONTINUITY EVALUATION V1 — Design Specification*