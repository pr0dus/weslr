# RUNTIME CONTAMINATION METADATA V1
**Generated:** 2026-04-22 19:31 GMT+2
**Mode:** STRICT — design only, no code changes, no routing changes, no scoring changes, no governance changes
**Authors:** Main agent
**Sources:** docs/CONTINUITY_CONTAMINATION_CONTROL_V1.md, docs/TIMELINE_NATIVE_CONTINUITY_RESOLUTION_V1.md, weslr/cross_session_artifact_eval.py, weslr/relevance_eval_analysis.py, dialogue.py, weslr/timeline_resolution.py

---

## SECTION 1 — PURPOSE

### Why Contamination Should Become Visible in Runtime Metadata

WESLR's runtime currently produces continuity metadata (`_has_active_artifact`, `_resolution_path`, `artifact_id`, `resolved_artifact_content`) that tells the operator *what* resolved. It does not tell the operator whether that resolution is **healthy** or **contaminated**.

The contamination advisory in eval artifacts (csc-008) proved contamination is real and detectable. But eval artifacts are post-hoc — they are written after evaluation runs, not during live sessions. The operator has no visibility into contamination risk during actual runtime.

Making contamination visible in runtime metadata means:
- The operator can see when "this" resolved to something that may not belong in the current context
- SatUi can surface contamination risk as a yellow/red indicator
- The operator remains in control — they decide what to do with the signal
- It is the minimum viable observability layer for contamination risk

### Why This Must Remain Advisory-Only

Contamination is not a failure state. It is a **signal**. The operator may genuinely want to apply a photovoltaic artifact to an accounting question as a metaphorical comparison. Blocking or redirecting resolution based on contamination would remove operator agency — which is the most important property WESLR maintains.

The metadata exists so the operator can **see** contamination risk, not so the system can **act on** it automatically. This is the same advisory model used throughout WESLR: observe, flag, surface — but do not block without operator intent.

### How This Differs from Runtime Filtering

| Concern | Runtime Filtering | Runtime Contamination Metadata |
|---|---|---|
| Authority | System acts automatically | Operator sees and decides |
| Behavior change | Changes what gets resolved | Only changes what operator sees |
| Risk | Removes operator agency | Preserves operator agency |
| Implementation | Blocking/redirect logic | Additive metadata field |
| Governance | Would require new authority | No new authority |

---

## SECTION 2 — CURRENT REALITY

### Where Continuity Signals Come From

```
User says "improve this"
  → dialogue.py:_is_artifact_reference_phrase() — detects reference phrase
  → dialogue.py:_resolve_active_artifact()
      Level 1: timeline_resolution.resolve_active_artifact_for_user(user_id)
        → active_thread_registry[user_id] → thread_id → latest artifact in thread
      Level 2: artifact_store.get_active_artifact(session_id) [registry fallback]
      Level 3: _no_active_artifact = True [safe path]
  → Resolution path stored: _resolution_path = "active_thread" | "registry_fallback" | "none"
```

### What Runtime Metadata Already Exists

| Field | Source | Purpose |
|---|---|---|
| `artifact_id` | dialogue.py | ID of resolved artifact |
| `resolved_artifact_content` | dialogue.py | Content of resolved artifact |
| `resolved_artifact_context` | dialogue.py | Context block from artifact |
| `_has_active_artifact` | dialogue.py | Boolean flag |
| `_resolution_path` | dialogue.py | "active_thread" \| "registry_fallback" \| "none" |
| `_no_active_artifact` | dialogue.py | Boolean flag when no artifact found |
| `contamination_check` | timeline_resolution | Lightweight heuristic (True/False) |
| `confidence` | timeline_resolution | "high" \| "medium" \| "none" |
| `relevant_interests_snapshot` | relevance_surface | Active interests at resolution time |

### What Is Missing Today

1. **No contamination risk level** — runtime has no `risk_level` field (none/low/medium/high)
2. **No contamination type** — runtime has no `contamination_type` field distinguishing cross_domain, stale_context, wrong_artifact_persistence, unrelated_topic_bleed
3. **No source signals** — no list of specific signals that triggered contamination assessment
4. **No confidence in contamination assessment** — no `contamination_confidence` (low/medium/high)
5. **No domain mismatch signal** — no explicit domain match/mismatch between artifact and current message
6. **`contamination_check` is binary** — `timeline_resolution._contamination_check()` returns only True/False, not a type + severity model

### Where Contamination Is Currently Detected

| Location | Method | Output |
|---|---|---|
| `cross_session_artifact_eval.py` | Keyword set comparison between session A and B messages | `contamination_advisory` block in eval artifacts |
| `relevance_eval_analysis.py` | Pattern aggregation over eval artifacts | `contamination_observed_patterns` in analysis report |
| `timeline_resolution._contamination_check()` | Lightweight content + context heuristic | Boolean `contamination_check` in resolution metadata |

---

## SECTION 3 — WHAT RUNTIME CONTAMINATION METADATA SHOULD REPRESENT

### Semantic Meaning

The `_contamination_metadata` block answers one question for the operator:

> *"Did 'this' resolve to something that might not belong here, and how confident are we?"*

It is a **risk signal**, not a **risk verdict**. The operator uses it to decide whether the resolution is appropriate.

### Risk Levels

| Level | Meaning | Operator Action |
|---|---|---|
| `none` | No contamination signals detected. Resolution is clean. | None needed |
| `low` | Minor signals present but likely not meaningful. Resolution probably fine. | Informational only |
| `medium` | Clear signals of possible contamination. Operator should review. | Surface in UI |
| `high` | Strong signals of contamination. Resolution may be wrong. | Flag prominently in UI |

### Contamination Types

| Type | Description |
|---|---|
| `none` | No contamination |
| `cross_domain_contamination` | Artifact from domain X resolving in domain Y conversation without explicit operator reference |
| `stale_context_dominance` | Stale artifact (older generation in lineage) resolving when newer version exists |
| `wrong_active_artifact_persistence` | Wrong artifact persisted as active due to thread/session confusion |
| `unrelated_topic_bleed` | Interests from an unrelated session influencing the current resolution |

### Confidence in the Assessment

| Level | Meaning |
|---|---|
| `low` | Limited signals; contamination is speculative |
| `medium` | Some signals present; assessment is plausible |
| `high` | Multiple strong signals; contamination is likely |

---

## SECTION 4 — OUTPUT / METADATA MODEL

### Shape

```json
{
  "_contamination_metadata": {
    "present": true,
    "risk_level": "none|low|medium|high",
    "type": "cross_domain_contamination|stale_context_dominance|wrong_active_artifact_persistence|unrelated_topic_bleed|none",
    "reason": "Human-readable summary of why this risk level was assigned.",
    "source_signals": [
      "message_domain_mismatch",
      "artifact_context_present",
      "reference_phrase_absent"
    ],
    "confidence": "low|medium|high",
    "advisory_only": true
  }
}
```

### When It Should Be Absent

`_contamination_metadata` should be **absent** (not `present: false`) when:
- The turn is not a reference turn (no artifact was resolved)
- There is no active artifact and `_no_active_artifact` is True
- The resolution was explicitly safe-path (no contamination assessment needed)

**Rationale:** Absence means "not applicable" — not "clean." A clean resolution would have `present: true, risk_level: none`. Absence avoids false confidence on non-reference turns.

### When It Should Be Present

`_contamination_metadata` should be **present** when:
- A reference phrase was detected AND an artifact was resolved (Level 1 or Level 2)
- An active artifact exists even without a reference phrase (for transparency on continuity-rich turns)

### Backward Compatibility

All fields have defaults for backward compatibility:
- `present` defaults to `false` (field absent)
- `risk_level` defaults to `"none"`
- `type` defaults to `"none"`
- `reason` defaults to `""`
- `source_signals` defaults to `[]`
- `confidence` defaults to `"high"`
- `advisory_only` is always `true` and immutable

**No existing schema field is modified or removed.**

---

## SECTION 5 — WHEN IT SHOULD APPEAR

### Minimal Safe Conditions

`_contamination_metadata` is produced when ALL of these are true:
1. A reference phrase was detected (`_is_artifact_reference_phrase` returned True)
2. An artifact was resolved (Level 1: active_thread, or Level 2: registry_fallback)
3. The resolution produced an `artifact_id`

### Optional Enhancement (Not Required for First Slice)

For continuity-rich turns where no reference phrase was used but an active artifact is present, `_contamination_metadata` with `risk_level: none` may be added for transparency — but this is optional and should not change behavior.

### What Triggers Each Risk Level

| Condition | Risk Level |
|---|---|
| No contamination signals detected | `none` |
| Reference phrase detected, artifact resolved, but artifact content is empty | `low` |
| Artifact context interests present AND message relevance is empty | `medium` |
| Obvious domain mismatch between artifact domain and current message | `medium` |
| Both domain mismatch AND interest bleed present | `high` |
| Multiple strong signals converging | `high` |

### What Does NOT Trigger Contamination Metadata

- Safe path taken (`_no_active_artifact = True`) — field is absent, not `none`
- Generation turns — field is absent
- Non-reference turns — field is absent unless active artifact exists

---

## SECTION 6 — RELATION TO EXISTING SYSTEMS

### dialogue.py

The primary integration point is `_resolve_active_artifact()`. After resolution completes and `research_context` is populated with `_has_active_artifact`, `_resolution_path`, and `artifact_id`, a contamination assessment is added as `_contamination_metadata`.

**No routing changes. No new calls to external modules during assessment.**

### _reference_metadata (dialogue.py)

The `_reference_metadata` block that dialogue.py produces for SatUi is separate from `_contamination_metadata`. They are not merged. `_reference_metadata` covers what was resolved. `_contamination_metadata` covers whether the resolution was healthy.

### timeline_resolution.py

`timeline_resolution.resolve_active_artifact_for_user()` currently returns `contamination_check: True|False`. This is a lightweight binary heuristic.

The runtime `_contamination_metadata` supersedes the binary `contamination_check` for UI purposes, but `timeline_resolution.py` is **not modified** in this slice. The contamination assessment in `_contamination_metadata` uses different signals (domain mismatch, interest bleed) rather than the lightweight content heuristic.

### cross_session_artifact_eval.py

The `contamination_advisory` block in eval artifacts uses the same detection logic as runtime `_contamination_metadata` (keyword-based cross-domain detection). This ensures eval and runtime use consistent signals.

Future eval artifacts may incorporate runtime `_contamination_metadata` as an additional input source — but not in this slice.

### relevance_eval_analysis.py

The contamination analysis in `relevance_eval_analysis.py` reads `contamination_advisory` from eval artifacts. It does **not** read from runtime `_contamination_metadata`. These are separate flows:
- Runtime metadata: for live operator visibility
- Eval artifacts: for post-hoc analysis

### SatUi / Operator Display

`_contamination_metadata` is surfaced through SatUi as a contamination risk indicator. The operator decides what action to take. No automatic behavior change occurs.

---

## SECTION 7 — FORBIDDEN DRIFT

### F1 — No Runtime Behavior Changes
**Forbidden:** Using `_contamination_metadata` to change how "this" is resolved, to block resolutions, or to redirect to a different artifact.

**Why:** This metadata is visibility only. The operator sees it; the system continues as normal.

### F2 — No Routing Changes
**Forbidden:** Adding contamination risk level to routing decisions.

**Why:** Routing is unchanged. Contamination metadata is observational.

### F3 — No Governance Triggers
**Forbidden:** Auto-triggering governance review, proposal generation, or operator alerts based on contamination risk level.

**Why:** The operator sees the signal and decides. No automatic escalation.

### F4 — No Prompt-Only Hacks
**Forbidden:** Adding prompt instructions to "ignore contaminated artifacts" or "don't use X artifact when Y message arrives" as a substitute for structured metadata.

**Why:** This masks contamination without fixing the resolution pathway.

### F5 — No Suppression of Continuity
**Forbidden:** Weakening the active thread registry or resolution cascade to prevent contamination, at the cost of reducing legitimate continuity.

**Why:** Contamination control must not weaken healthy continuity. If the two conflict, the system should surface contamination risk, not reduce continuity.

### F6 — No Auto-Proposals
**Forbidden:** Auto-generating improvement proposals or corrections when contamination is detected.

**Why:** The operator sees the contamination signal. They decide whether to request a correction.

### F7 — No Schema Modification of Existing Fields
**Forbidden:** Modifying or removing existing fields in the runtime response dict (`artifact_id`, `_has_active_artifact`, `_resolution_path`, etc.).

**Why:** `_contamination_metadata` is additive. Existing fields are unchanged.

---

## SECTION 8 — RECOMMENDED FIRST IMPLEMENTATION

### Integration Point

Modify `dialogue.py:_resolve_active_artifact()` — after the resolution cascade completes and `research_context` is populated with resolution fields, compute and attach `_contamination_metadata`.

### Specific Change

In `_resolve_active_artifact()`, after the resolution path is determined and `research_context` is populated, add:

```python
# Build contamination metadata (advisory only — no behavior change)
_contamination_metadata = _build_contamination_metadata(
    message=message,
    research_context=research_context,
)
research_context["_contamination_metadata"] = _contamination_metadata
```

### New Function: _build_contamination_metadata

```python
def _build_contamination_metadata(message: str, research_context: dict) -> dict:
    """Build advisory contamination metadata for a resolved reference.

    Returns dict with keys:
      - present: bool — whether contamination assessment applies
      - risk_level: str — "none"|"low"|"medium"|"high"
      - type: str — contamination type or "none"
      - reason: str — human-readable summary
      - source_signals: list[str] — specific signals detected
      - confidence: str — "low"|"medium"|"high"
      - advisory_only: True (always)
    """
    # Returns absent-compatible shape (all fields have defaults)
```

### Detection Signals Used

The implementation reuses the keyword-based detection from `cross_session_artifact_eval.py`:
- Domain mismatch between current message and artifact context keywords
- Presence of artifact context interests when message relevance is empty
- Reference phrase absent on what should be a domain-matched resolution
- Interest bleed: interests from a prior session detected in current session's relevance snapshot

### No Changes To

- `timeline_resolution.py` — resolution cascade unchanged
- `artifact_store.py` — no new writes
- `relevance_surface` — no new calls
- Any routing or scoring module
- `threads.json` or `interests.json`

### Verification

1. Run `python3 -m weslr.cross_session_artifact_eval run-all` — csc-001/006 show `risk_level: none`, csc-008 shows `risk_level: medium|high`
2. Run `python3 -m weslr.relevance_eval_analysis` — contamination section shows correct pattern
3. Runtime response dicts for reference turns include `_contamination_metadata` with `advisory_only: true`
4. No changes to `threads.json`, `interests.json`, or artifact schema

---

## SECTION 9 — STOP LINE

**DOCUMENTATION ONLY — NO CODE CHANGES**

This document defines the design for runtime contamination metadata:
- Advisory-only risk signal attached to resolved reference turns
- No runtime behavior changes, no routing changes, no scoring changes
- Consistent with existing contamination detection in eval artifacts
- Backward compatible — all fields additive, absent by default
- Operator sees contamination risk; operator decides what to do

### Document Completeness

| Section | Status |
|---|---|
| 1. Purpose | ✅ Complete |
| 2. Current Reality | ✅ Complete |
| 3. What Runtime Metadata Should Represent | ✅ Complete |
| 4. Output / Metadata Model | ✅ Complete |
| 5. When It Should Appear | ✅ Complete |
| 6. Relation to Existing Systems | ✅ Complete |
| 7. Forbidden Drift | ✅ Complete |
| 8. Recommended First Implementation | ✅ Complete |
| 9. Stop Line | ✅ Complete |

---

*RUNTIME_CONTAMINATION_METADATA_V1 — Design Specification*
*Design only. No code. No routing changes. No scoring changes. No governance changes.*
