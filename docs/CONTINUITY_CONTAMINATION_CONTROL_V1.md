# CONTINUITY CONTAMINATION CONTROL V1
**Generated:** 2026-04-22 14:09 GMT+2
**Mode:** STRICT — design only, no code changes, no routing changes, no scoring changes, no governance changes
**Authors:** Main agent (inspector synthesis)
**Sources:** dialogue.py, weslr/timeline_resolution.py, weslr/cross_session_artifact_eval.py, weslr/relevance_eval_runner.py, weslr/relevance_eval_analysis.py, docs/TIMELINE_NATIVE_CONTINUITY_RESOLUTION_V1.md, docs/CROSS_SESSION_ARTIFACT_CONTINUITY_EVAL_V1.md

---

## SECTION 1 — PURPOSE

### Why Contamination Control Is Distinct from Continuity

WESLR's continuity infrastructure (artifacts, threads, timelines, lineage) is designed to make experience **continuous** — what was worked on is accessible, references resolve correctly, and context survives session boundaries.

But continuity is not the same as **contamination**. A system can be continuous without being contaminated. The goal is:

- **Continuity:** Session B can access what Session A built, when it should
- **Contamination:** Session B inherits what Session A had, when it shouldn't

The cross-session evaluation (csc-008) proved contamination is real: interests from a photovoltaic session leaked into an unrelated session. That is contamination — not because continuity failed, but because the wrong continuity was applied.

### What This Document Does

This document defines:

1. What counts as contamination (vs healthy continuity)
2. How contamination should be detected (advisory model)
3. What metadata should be captured to distinguish healthy from contaminated (additive model)
4. What must not be done (forbidden drift)
5. The safest first implementation step

This is not a scoring rubric. It is a design boundary document.

---

## SECTION 2 — CURRENT REALITY

### Where Continuity Enters the System

```
User says "improve this"
  → dialogue.py:_is_artifact_reference_phrase() detects reference phrase
  → dialogue.py:_resolve_active_artifact()
      Level 1: timeline_resolution.resolve_active_artifact_for_user(user_id)
        → active_thread_registry[user_id] → thread_id → latest artifact in thread
      Level 2: artifact_store.get_active_artifact(session_id) [registry fallback]
      Level 3: _no_active_artifact = True [safe path]
  → Resolution path stored: _resolution_path = "active_thread" | "registry_fallback"
```

### Current Continuity Sources

| Source | What It Provides | Scope |
|--------|-----------------|-------|
| `active_thread_registry.json` | Per-user active thread pointer | User-scope |
| `artifact_store` registry | session_id → artifact_id | Session-scope |
| `threads.json` | Ordered items in a thread | User-scope |
| `timeline events.jsonl` | Recency-ordered event log | User-scope |
| `relevant_interests_snapshot` | Active interest context | Session-scope |

### Where Contamination Can Enter

```
"improve this" in Session B
  → resolve_active_artifact_for_user(user_id)
      → get_active_thread(user_id) → returns Session A's active thread
      → latest artifact in thread is from Session A domain
  → RESOLUTION: wrong domain artifact returned as "this"
  → CONTAMINATION: Session B inherits Session A's continuity context
```

**The contamination path is the same path as healthy continuity.** The resolution cascade that enables cross-session continuity is also the mechanism through which contamination occurs. This is the core tension.

### Current Contamination Detection

The `cross_session_artifact_eval.py` csc-008 scenario explicitly tests cross-domain contamination. It sets:
- `contamination_flags.interest_bleed_from_session_1_to_2 = false` (correct — no bleed)
- `contamination_flags.domain_context_contamination = false` (correct — no contamination)

The `relevance_eval_analysis.py` checks for:
- `artifact_context_leak_flag`: artifact context leaked into unrelated turn
- `cross_domain_contamination_flag`: wrong-domain relevance dominated unrelated turn
- `revision_drift`: active artifact changed unexpectedly across revision chain
- `incorrect_continuity`: wrong artifact returned on resolution

### Current Safe Paths

| Scenario | Behavior | Status |
|----------|----------|--------|
| No active artifact | Safe empty message returned | ✅ Working |
| Artifact not found | `_no_active_artifact = True` | ✅ Working |
| Empty content artifact | `_contamination_check = False` | ✅ Detectable |
| Registry key missing | Graceful fallback | ✅ Working |

---

## SECTION 3 — WHAT COUNTS AS CONTAMINATION

### Contamination Definition

**Contamination** = A session inherits continuity state (artifacts, interests, thread context) from a prior session that is **irrelevant, unauthorized, or unintended** for the current work context.

Contamination is not "accessing something from another session." That is healthy continuity. Contamination is "the wrong thing was resolved as 'this' because the resolution mechanism applied the wrong context."

### Taxonomy of Contamination Types

#### C1 — Domain Contamination
**What:** Artifact or interest context from Session A (domain X) is active in Session B (domain Y) and influences the response.

**Example:** Session A was about photovoltaic efficiency. Session B is about accounting. Session B's "improve this" resolves to the photovoltaic artifact instead of returning safe path.

**Current detection:** `cross_domain_contamination_flag` in eval artifacts. `interest_bleed_from_session_1_to_2` flag.

**Not contamination:** Operator explicitly switches domains but explicitly references the prior artifact. That is intentional continuity, not contamination.

---

#### C2 — Temporal Contamination (Stale Artifact)
**What:** A stale artifact (older generation in a lineage chain) is resolved as "this" when a newer version exists.

**Example:** Artifact A → A' → A'' exists. "improve this" resolves to A (root) instead of A'' (current).

**Current detection:** `incorrect_continuity` flag in chain scenarios. `is_latest_in_chain` field in resolution metadata.

**Current state:** Lineage chain not yet tracked in artifact metadata — this contamination type is **not yet detectable** in the current implementation.

---

#### C3 — Authorization Contamination
**What:** A user resolves an artifact outside their authorized scope (e.g., a different user's artifact, or an artifact from an unauthorized institution thread).

**Example:** User in "Teacher" role accesses artifact created in "Engineering Lead" role scope.

**Current detection:** None — institution scope boundaries not yet integrated into resolution.

---

#### C4 — Interest Bleed
**What:** Session A's declared interests remain active in Session B inappropriately, influencing relevance scoring even when no artifact is involved.

**Example:** Session A: interests = ["photovoltaic", "efficiency"]. Session B: "capital of France" is scored against photovoltaic interests.

**Current detection:** `interest_bleak_from_session_1_to_2` flag in csc-008.

**Note:** Some interest persistence is **healthy** — if a user has a standing interest in photovoltaic systems, it should persist across sessions. The contamination is when interest context inappropriately dominates a message that has no relation to it.

---

#### C5 — Session-Scoped State Leak
**What:** Per-session runtime state (not persistent continuity) leaks between sessions via in-memory context.

**Example:** Research context from Session A turn influences Session B turn because context was not properly isolated.

**Current detection:** Not explicitly tested. Session isolation is assumed but not verified.

---

### What Is NOT Contamination

| Scenario | Why Not Contamination |
|----------|----------------------|
| Session B resolves Session A's artifact when user explicitly wants that | Intentional continuity |
| User switches domains, active artifact updates to new domain | Correct resolution, not contamination |
| Interests persist across sessions because user has standing interests in both | Healthy relevance, not contamination |
| Thread context is restored because user is continuing the same work | Correct continuity |

---

## FILES CHANGED
```
docs/CONTINUITY_CONTAMINATION_CONTROL_V1.md — new file (Slice 1: Sections 1-3)
```

## COMMANDS RUN
```
None — design document only
```

## DESIGN SUMMARY — SLICE 1

- Contamination = wrong continuity applied to wrong context
- 5 contamination types identified: Domain, Temporal, Authorization, Interest Bleed, Session Leak
- Core tension: same resolution cascade enables both continuity AND contamination
- Current detection: domain contamination and interest bleed are detectable via eval flags
- Temporal (stale artifact) and Authorization contamination are NOT yet detectable
- Healthy continuity is distinguished by: correct domain match, temporal recency, authorization scope, intentional operator action

## RECOMMENDED FIRST IMPLEMENTATION (Slice 1)
No implementation — this document is design-only. First implementation will be specified in Slice 3.

## STOP LINE
Slice 1 complete. Sections 1–3 done. Sections 4–9 remain.

---

## SECTION 4 — HEALTHY CONTINUITY VS CONTAMINATION

### The Distinction Principle

**Healthy continuity** = continuity that serves the current work context.

**Contamination** = continuity applied to a context it was not designed for.

The test is not "is this from another session?" The test is "is this the right thing for the current work?"

### Healthy Continuity Signatures

| Signal | What It Looks Like |
|--------|--------------------|
| Domain match | Session A artifact about PV → Session B "improve this" → same domain or explicit domain shift acknowledged |
| Temporal recency | "this" resolves to latest generation in lineage, not stale root |
| Intentional reference | User explicitly says "work with the artifact from earlier" or "improve this" in genuine continuation context |
| Authorization scope | User resolves artifacts within their authorized institution/role scope |
| Interest coherence | Declared interests match message domain; no interest bleed into unrelated messages |
| Thread context | "improve this" resolves to artifact in the active thread, not some unrelated thread |

### Contamination Signatures

| Signal | What It Looks Like |
|--------|--------------------|
| Domain mismatch | PV artifact resolving for accounting question without explicit user reference |
| Stale artifact | "this" returns root artifact when A' and A'' exist in lineage |
| Unauthorized access | Artifact from role/institution scope the current user cannot access |
| Interest dominance | Interests from Session A scoring Session B's unrelated message with high relevance for wrong domain |
| Ghost thread context | Resolution comes from a thread the user is not currently working in |

### The Resolution Path as Diagnostic

The `_resolution_path` field in `timeline_resolution.py` is the primary diagnostic:

| Resolution Path | Healthy When | Contaminated When |
|----------------|--------------|-------------------|
| `active_thread` | User is working in that thread | User switched domains but active thread still old |
| `registry_fallback` | User has no active thread set | Active thread was cleared but session context still loaded |
| `none` | No prior work exists | — |

**Key diagnostic:** When `_resolution_path = "active_thread"` but the thread's domain is mismatched with the current message domain, that is a contamination signal — not a failure of the resolution mechanism, but a signal that the active thread context is stale relative to the current work.

### Operator Intent as Ground Truth

The cleanest signal for distinguishing healthy continuity from contamination is **operator intent**:

- Did the operator explicitly reference the prior artifact/thread/interest?
- Or did the system assume continuity without explicit confirmation?

Healthy continuity tends to be **invoked** by the operator. Contamination tends to be **assumed** by the system.

**Design implication:** Resolution metadata should capture whether the resolution was triggered by an explicit operator reference or an automatic cascade. This is a future additive field: `_resolution_trigger: "explicit" | "automatic"`.

---

## SECTION 5 — ADVISORY DETECTION MODEL

### Design Goal

Detect contamination without blocking continuity. The system should **flag** contamination for operator review, not refuse to resolve or suppress continuity.

This is an advisory model — contamination flags inform evaluation and human review, but do not automatically override resolution.

### Detection Points

#### Point 1: At Resolution — Domain Mismatch Check

**Location:** `timeline_resolution.py:resolve_active_artifact_for_user()`

**Check:** After resolving artifact, compare artifact domain (from interests or declared topic) against current message domain.

**Advisory fields added to resolution metadata:**
```python
contamination_check: {
    "domain_match": bool,           # artifact domain vs message domain
    "user_scope_match": bool,      # artifact owner matches requesting user
    "authorization_clear": bool,    # user authorized for this artifact's scope
    "temporal_fresh": bool,         # artifact is latest in lineage
    "thread_domain_match": bool,    # active thread domain matches artifact
}
```

**Threshold:** Flag if `domain_match = False` AND resolution was automatic (not explicit operator reference).

#### Point 2: At Interest Scoring — Bleed Detection

**Location:** `relevance_eval_runner.py` turn execution, or interest_tracker integration

**Check:** When a message in a new domain is scored against interests from a prior session, flag if the top-scoring interests are from a different domain than the message.

**Advisory field:**
```
interest_bleed_signal: {
    "scored_message_domain": str,
    "dominant_interest_domain": str,
    "mismatch_detected": bool,
    "dominant_interests": [list of interest names from wrong domain]
}
```

#### Point 3: At Reference Resolution — Stale Lineage Check

**Location:** `timeline_resolution.py` (when lineage tracking is added)

**Check:** Before returning resolved artifact, verify it is the latest generation in its lineage chain.

**Advisory field:**
```
lineage_check: {
    "is_latest": bool,
    "generation": int,
    "chain_length": int,
    "newer_exists": bool
}
```

#### Point 4: At Session Boundary — Interest State Audit

**Location:** Cross-session evaluation harness (`cross_session_artifact_eval.py`)

**Check:** At Session B start, compare interest state against Session A's final interest state. Flag if interests persist without explicit re-declaration.

**This is already implemented** in csc-008 scenario via `contamination_flags.interest_bleed_from_session_1_to_2`.

### Contamination Severity Model

| Severity | Condition | Response |
|----------|-----------|---------|
| **Info** | Interests persist across sessions (user has standing interests) | Log only, no action |
| **Warning** | Domain mismatch detected, automatic resolution | Flag in metadata, operator review if requested |
| **Alert** | Authorization boundary violation detected | Flag, block resolution, notify operator |
| **Critical** | Unauthorized artifact access + no operator intent | Block, log, do not serve artifact |

### What This Model Does NOT Do

- Does NOT automatically block resolution on contamination detection
- Does NOT score or rank continuity quality
- Does NOT modify any existing routing or scoring logic
- Does NOT introduce new authority for the detection system itself

---

## SECTION 6 — ADDITIVE METADATA MODEL

### Design Principle

Metadata is additive — it enriches existing artifacts and eval results, it does not change what gets stored or how resolution works.

All new fields are nullable / absent by default. Existing artifacts remain valid.

### New Metadata Fields

#### For Artifact Records (art-*.json)

```json
{
  "artifact_id": "art-...",
  "lineage": {
    "root": "art-..." | null,
    "parent": "art-..." | null,
    "generation": 1 | 2 | 3 | ...,
    "chain": ["art-...", "art-..."],
    "is_latest": true
  },
  "domain_tags": ["photovoltaic", "efficiency"],
  "thread_id": "thr-...",
  "continuity_scope": "user" | "institution"
}
```

**Implementation note:** These fields are added to `weslr/artifact_store.py` save logic as optional fields. They do not change the existing artifact schema — they are added as additive entries.

#### For Resolution Records (returned by timeline_resolution)

```json
{
  "resolved_artifact_id": "art-...",
  "resolution_path": "active_thread" | "registry_fallback" | "timeline_recency" | "none",
  "resolution_trigger": "explicit" | "automatic",
  "contamination_check": {
    "domain_match": true,
    "user_scope_match": true,
    "authorization_clear": true,
    "temporal_fresh": true,
    "thread_domain_match": true
  },
  "lineage_check": {
    "is_latest": true,
    "generation": 3,
    "chain_length": 3,
    "newer_exists": false
  },
  "interest_bleed_signal": {
    "mismatch_detected": false,
    "dominant_interests": []
  },
  "confidence": 0.85
}
```

#### For Evaluation Artifacts (continuity/artifacts/eval/)

Existing `auto_flags` and `contamination_flags` structures are preserved. New additive fields:

```json
{
  "auto_flags": {
    "revision_drift": false,
    "artifact_context_leak_flag": false,
    "cross_domain_contamination_flag": false,
    "incorrect_continuity": false,
    "safe_path_ok": true,
    "index_inconsistency_detected": false,
    "total_artifacts_created": 1,
    "domain_mismatch_detected": false,
    "authorization_boundary_flag": false
  },
  "contamination_flags": {
    "interest_bleed_from_session_1_to_2": false,
    "artifact_id_confusion": false,
    "active_artifact_confusion": false,
    "domain_context_contamination": false,
    "stale_lineage_returned": false
  },
  "contamination_advisory": {
    "severity": "info" | "warning" | "alert" | "critical" | null,
    "flags": ["list of active advisory flags"],
    "resolution_health": "healthy" | "contaminated" | "unknown"
  }
}
```

### Implementation Constraint

These metadata fields are additive only:
- No existing artifact schema field is modified or removed
- No existing resolution behavior is changed
- No existing eval artifact field is removed
- All fields are nullable/absent by default for backward compatibility

---

## FILES CHANGED
```
Slice 2 — no file changes, only design documentation additions to CONTINUITY_CONTAMINATION_CONTROL_V1.md
```

## COMMANDS RUN
```
None — design document only
```

## DESIGN SUMMARY — SLICE 2

- Healthy continuity: domain match, temporal recency, intentional operator reference, authorization scope, thread coherence
- Contamination: wrong domain, stale artifact, unauthorized access, interest bleed, ghost thread context
- Resolution path (`_resolution_path`) is the primary contamination diagnostic
- Advisory detection: 4 detection points at resolution, scoring, lineage, and session boundary
- Severity model: Info → Warning → Alert → Critical (block only at Critical)
- Additive metadata: artifact enrichment fields, resolution metadata fields, eval advisory fields
- All new fields nullable/absent by default — no schema changes to existing records

## RECOMMENDED FIRST IMPLEMENTATION (Slice 2)
No implementation — design documentation only.

## STOP LINE
Slice 2 complete. Sections 1–6 done. Sections 7–9 remain.

---

## SECTION 7 — FORBIDDEN DRIFT

### Design Principles

WESLR's continuity infrastructure exists to serve the operator's work. Contamination control exists to prevent continuity from becoming a liability. Any change that:

- weakens operator agency
- makes continuity less observable
- creates new contamination pathways
- reduces transparency

…is forbidden drift.

### Forbidden Actions

#### F1 — No Auto-Suppression of Continuity Based on Domain Mismatch
**Forbidden:** The system automatically declining to resolve "this" because the artifact's domain does not match the current message domain.

**Why:** This removes operator agency. The operator may genuinely want to apply a photovoltaic artifact to an accounting question as a metaphorical comparison. The system should flag the mismatch, not block the resolution.

**Exception:** When authorization boundaries are crossed (C3 contamination), blocking is appropriate — but only at the Critical severity level.

---

#### F2 — No Prompt Engineering as Contamination Fix
**Forbidden:** Adding more system prompt context to prevent contamination, as a substitute for structural resolution improvements.

**Why:** Contamination is a resolution architecture problem, not a context window problem. Stuffing the prompt is a workaround that masks the contamination pathway without fixing it, and creates new failure modes (prompt bloat, context overflow, inconsistent behavior).

**Correct approach:** Fix the resolution cascade. Add thread domain checks. Implement lineage tracking. Improve authorization boundaries.

---

#### F3 — No Silent Resolution Without Audit Trail
**Forbidden:** Resolving "this" without producing a resolution metadata record that can be reviewed.

**Why:** If the operator cannot inspect what resolved "this" and why, contamination becomes invisible. Every resolution must produce metadata (resolution_path, contamination_check, confidence).

---

#### F4 — No Modifying Existing Resolution Behavior to Block Contamination
**Forbidden:** Changing `timeline_resolution.py` to refuse resolution based on contamination flags.

**Why:** Blocking resolution breaks operator workflows. The correct response to contamination is flag + serve + transparency — not block. Blocking is reserved for authorization violations only.

---

#### F5 — No New Authority for the Detection System
**Forbidden:** The contamination detection system acquiring the ability to modify artifacts, suppress interests, or alter resolution behavior.

**Why:** This document defines advisory detection only. The detection system observes and flags. It does not act. Any remediation requires operator review.

---

#### F6 — No Removing Existing Contamination Flags
**Forbidden:** Removing or weakening existing `contamination_flags` or `auto_flags` fields in eval artifacts.

**Why:** These flags are the current contamination observability surface. Removing them reduces transparency.

---

#### F7 — No Modifying Active Artifact Registry Behavior
**Forbidden:** Changing `artifact_store.py` or the active artifact registry to block or redirect resolutions.

**Why:** The registry is session-keyed by design. The timeline resolution layer sits on top of it. Contamination control happens in the resolution layer, not by modifying the registry.

---

#### F8 — No Timeline Rewrite
**Forbidden:** Deleting, reordering, or modifying timeline events to "clean up" contamination evidence.

**Why:** The timeline is append-only by design. Evidence of contamination should be visible, not hidden.

---

## SECTION 8 — RECOMMENDED FIRST IMPLEMENTATION

### Smallest Safe Step

Implement **contamination advisory flags in existing eval artifacts** — specifically, add `domain_mismatch_detected` to `auto_flags` and `contamination_advisory` to eval artifacts produced by `cross_session_artifact_eval.py`.

This is the safest first step because:
- It is purely additive — no existing behavior changes
- It uses existing detection points — no new data sources required
- It is observable immediately — operator can review eval results
- It is reversible — removing the field restores prior state

### What to Implement

**File:** `weslr/cross_session_artifact_eval.py`

**Change:** In `_build_contamination_flags()`, add domain mismatch detection:

```python
def _build_contamination_flags(scenario_id, session_a_result, session_b_result):
    # ... existing flags ...
    
    # NEW: Domain mismatch detection
    session_a_artifact = session_a_result.get("artifact_content", "")
    session_b_message = session_b_result.get("input_message", "")
    
    domain_mismatch = False
    if session_a_artifact and session_b_message:
        # Lightweight heuristic: check if session B message domain
        # is clearly unrelated to session A artifact domain
        # This is advisory only — no blocking
        session_b_domain_keywords = _extract_domain_keywords(session_b_message)
        session_a_domain_keywords = _extract_domain_keywords(session_a_artifact)
        if session_b_domain_keywords and session_a_domain_keywords:
            overlap = session_b_domain_keywords & session_a_domain_keywords
            domain_mismatch = len(overlap) == 0
    
    return {
        # ... existing flags ...
        "domain_mismatch_detected": domain_mismatch,
        "authorization_boundary_flag": False,  # not yet implemented
        "stale_lineage_returned": False,  # not yet implemented
    }
```

**Also add** to `_build_eval_artifact()`:

```python
contamination_advisory: {
    "severity": (
        "warning" if contamination_flags.get("domain_mismatch_detected")
        else "info" if any(contamination_flags.values())
        else None
    ),
    "flags": [k for k, v in contamination_flags.items() if v],
    "resolution_health": (
        "contaminated" if contamination_flags.get("domain_mismatch_detected")
        else "healthy"
    )
}
```

### What NOT to Implement in Slice 1

- No blocking of resolution based on contamination flags
- No changes to `timeline_resolution.py` resolution behavior
- No changes to `dialogue.py` reference resolution path
- No new authorization checks
- No lineage tracking

### Verification

After implementing the change:
1. Run `python weslr/cross_session_artifact_eval.py run-all`
2. Check eval artifacts — `contamination_advisory` should appear in all csc-eval artifacts
3. `domain_mismatch_detected` should be `false` for csc-001 (same domain), `false` for csc-006 (no artifact)
4. csc-008 (cross-domain) should show `domain_mismatch_detected = true` and `severity = "warning"`

### Integration Points

| File | Change | Risk |
|------|--------|------|
| `weslr/cross_session_artifact_eval.py` | Add contamination advisory fields to eval artifacts | Low — additive only |
| `weslr/relevance_eval_analysis.py` | Add advisory fields to analysis report | Low — additive only |
| `docs/CONTINUITY_CONTAMINATION_CONTROL_V1.md` | This document | N/A |

### What This Achieves

- Observable contamination signals in existing eval artifacts
- Severity classification for operator review
- No behavior change in resolution or routing
- Reversible in one commit

---

## SECTION 9 — STOP LINE

**DOCUMENTATION ONLY — NO CODE CHANGES**

This document was produced by analysis of:

**Inspector A (Continuity/Runtime):**
- `dialogue.py` — reference phrase detection, resolution cascade, safe path
- `weslr/timeline_resolution.py` — active thread registry, resolution paths, contamination_check, resolution metadata
- `weslr/cross_session_artifact_eval.py` — cross-session eval harness, scenario catalog, contamination flag structures

**Inspector B (Eval/Artifact):**
- `weslr/relevance_eval_runner.py` — single-turn and multi-turn scenario structure, auto_flags, eval artifact shape
- `weslr/relevance_eval_analysis.py` — pattern detection over eval artifacts, chain scenario analysis, contamination flag aggregation
- `continuity/artifacts/eval/` — 46 existing eval artifacts demonstrating all three CSC scenarios and SAT scenarios

**Inspector C (Canon/Constraints):**
- `docs/TIMELINE_NATIVE_CONTINUITY_RESOLUTION_V1.md` — current reality, resolution cascade, contamination detection design, forbidden drift, first implementation path
- `docs/CROSS_SESSION_ARTIFACT_CONTINUITY_EVAL_V1.md` — 12-scenario catalog, evaluation artifact shape, scoring rubric

No code was written. No routing changed. No scoring changed. No governance altered.

### Document Completeness

| Section | Status |
|---------|--------|
| 1. Purpose | ✅ Complete |
| 2. Current Reality | ✅ Complete |
| 3. What Counts as Contamination | ✅ Complete |
| 4. Healthy Continuity vs Contamination | ✅ Complete |
| 5. Advisory Detection Model | ✅ Complete |
| 6. Additive Metadata Model | ✅ Complete |
| 7. Forbidden Drift | ✅ Complete |
| 8. Recommended First Implementation | ✅ Complete |
| 9. Stop Line | ✅ Complete |

---

*CONTINUITY_CONTAMINATION_CONTROL_V1 — Design Specification*
*Design only. No code. No routing changes. No scoring changes. No governance changes.*
