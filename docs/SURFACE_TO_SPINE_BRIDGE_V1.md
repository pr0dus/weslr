# SURFACE_TO_SPINE_BRIDGE_V1.md — WESLR Surface-to-Spine Bridge Design

**Status:** DESIGN — bridge doctrine
**Date:** 2026-04-21
**Derived from:** `docs/SELF_IMPROVEMENT_SPINE_V1.md`, `docs/SELF_IMPROVEMENT_SURFACE_INTEGRATION_V1.md`
**Authoritative for:** All surface-to-spine bridge implementation and operator tool design

---

## SECTION 1 — FILES CHANGED

| File | Change |
|------|--------|
| `docs/SURFACE_TO_SPINE_BRIDGE_V1.md` | **Created** — this document |

No production code files modified. No schema changes. No behavior changes.

---

## SECTION 2 — COMMANDS RUN

None. Design-only pass.

---

## SECTION 3 — DOCUMENT CONTENT

### Section 4 — Purpose

The canonical self-improvement spine (Steps 1-10) has a well-defined entry point at `inadequacy_persistence.record_inadequacy_event()`. Step 1 is the single gate through which all inadequacy signals enter the spine.

The surfaces (artifact, suggestion, thread, relevance) currently produce outputs that do not reach Step 1. They surface observations as metadata, but no canonical path exists to convert a surface observation into a Step 1 signal.

This creates a structural problem: surface systems can identify problems, but they cannot feed those problems into the self-improvement governance system without manual operator intervention in an ad hoc form. The operator must know exactly which file to write to, which function to call, and which JSON format to use — or the signal is lost.

**What a single canonical bridge provides:**
1. **One entry point** for all surface-originated signals — not five different ad hoc paths
2. **Validation before entry** — signals must pass minimum checks before entering the spine at Step 1
3. **Provenance** — every Step 1 signal carries its source surface, enabling audit and analysis
4. **Operator control** — the bridge is not automatic; it requires an intentional operator action to activate
5. **Separation from execution** — the bridge converts observations to signals; it does not execute anything

**What the bridge is NOT:**
- It is not a new self-improvement loop — the spine owns the loop
- It is not a new execution path — only `ExecutionGate` executes
- It is not automatic signal injection — surfaces never auto-trigger Step 1
- It is not a proposal generator — it only prepares the signal that triggers Step 1

---

### Section 5 — Allowed Surface Inputs

Only the following surface-originated signals are permitted to enter the bridge. Each is justified by the governing canonical documents.

**1. Artifact-originated weakness signal**

*Justification:* `WESLR_CANONICAL_SELF_MODEL_V1.md` Section 9 — artifacts express problems and hypotheses. `build_artifact_explainability()` evaluates artifacts. An artifact with low `internal_strength`, low `external_proof`, or high `risks` indicates a reasoning quality problem. The artifact evaluation system is the authoritative source for this signal.

*Trigger conditions:*
- An artifact has been evaluated via `build_artifact_explainability()`
- The evaluation produces `internal_strength < 0.4` OR `external_proof` is absent OR `risks` contains a recurring constraint
- The problem is not a one-off — it is the second or greater occurrence of the same limitation

*What enters the bridge:*
- `artifact_id`
- `artifact_evaluation_summary`: `{internal_strength, external_proof, risk_count}`
- `source_surface`: `"artifact_evaluation"`
- `surface_ref`: the artifact's item_id

**2. Suggestion-confirmed signal**

*Justification:* `SUGGESTION_SURFACE_CANON_V1.md` — suggestions surface observations. When an operator approves a suggestion, the approval confirms the observation is valid. The suggestion itself is never executed — but the act of approval is an explicit operator validation of the observation.

*Trigger conditions:*
- A suggestion surfaced in `explain_item()` output (`_suggestions`)
- The operator explicitly approved the suggestion (`requires_approval: True` was confirmed)
- The approval reveals a pattern (same interest flagged multiple times, or approval of a suggestion that surfaces a recurring concern)

*What enters the bridge:*
- `suggestion_type`: `"approved_interest_occurrence"` or `"approved_suggestion_action"`
- `interest_id`
- `item_id`
- `source_surface`: `"suggestion_approval"`
- `surface_ref`: interest_id + item_id combination

**3. Thread-context signal**

*Justification:* `THREAD_TRACKER_CANON_V1.md` — threads provide temporal grouping. A thread with multiple items where the same problem recurs is an explicit record of a persistent issue.

*Trigger conditions:*
- A thread contains 3 or more items of type `artifact` or `question`
- The thread `state` is `active` or `unresolved`
- The same limitation or concern appears across 2 or more items in the thread

*What enters the bridge:*
- `thread_id`
- `thread_name`
- `thread_state`
- `member_item_ids`: list of items sharing the recurring concern
- `source_surface`: `"thread_context"`

**4. Relevance urgency annotation**

*Justification:* `INTEREST_RELEVANCE_CANON_V1.md` + `SELF_IMPROVEMENT_SURFACE_INTEGRATION_V1.md` — relevance identifies what matters to the operator. When a weakness is in a high-relevance area, urgency is elevated. Relevance may annotate urgency but may not gate or route.

*Trigger conditions:*
- An artifact or proposal has been evaluated
- The relevance surface has scored interests against the same context
- At least one interest scored above a threshold (e.g., relevance score > 0.5) AND the artifact/proposal reveals a weakness in that domain

*What enters the bridge:*
- `relevance_context`: `{matched_interest_ids, relevance_scores}`
- `urgency_indicator`: `"high"` if weakness domain matches a top-scored interest
- `source_surface`: `"relevance_urgency"`

**5. Drift concern cross-reference**

*Justification:* `SELF_IMPROVEMENT_SPINE_V1.md` Section 8 (Limitation 4) — the drift loop and the inadequacy pipeline are parallel. A pending `Reflection` from the drift loop may indicate a real inadequacy. The drift concern itself is a surface observation that should be evaluable for spine entry.

*Trigger conditions:*
- `get_pending_reflections()` returns a `Reflection` with `status=PENDING`
- The operator acknowledges the concern and decides it warrants a spine signal
- Operator action: `weslr spine bridge --from-reflection <reflection_id>`

*What enters the bridge:*
- `reflection_id`
- `reflection_concern`
- `reflection_signals`: the underlying DriftSignal list
- `source_surface`: `"drift_concern"`

---

### Section 6 — Canonical Bridge Object

The bridge object is the structured payload that surfaces produce before calling the Step 1 entry function. It is the canonical form for all surface-originated spine inputs.

```json
{
  "bridge_version": "1.0",
  "signal_id": "<uuid-hex[:8]>",
  "source_surface": "artifact_evaluation | suggestion_approval | thread_context | relevance_urgency | drift_concern",
  "surface_ref": "<string>",
  "created_at": "<ISO8601 UTC>",
  "operator_triggered": true,
  "operator_trigger_id": "<operator timeline_id or 'manual'>",
  "payload": {
    // One of the following five, depending on source_surface:
  },
  "spine_target": "step1_inadequacy_signal",
  "provenance": {
    "original_item_id": "<string>",
    "original_item_type": "artifact | suggestion | thread | reflection",
    "confidence": 0.0,
    "urgency": "low | medium | high",
    "requires_review": true
  }
}
```

**Payload variants (one required depending on source_surface):**

```json
// source_surface == "artifact_evaluation"
{
  "artifact_id": "<string>",
  "evaluation": {
    "internal_strength": 0.0,
    "external_proof": { "human_approvals": 0, "handoff_acceptances": 0, "real_usage_hits": 0 },
    "risk_count": 0,
    "recurring_limitation": "<string or null>"
  },
  "matched_interests": ["<interest_id>"]
}

// source_surface == "suggestion_approval"
{
  "suggestion_type": "interest_occurrence | suggestion_action",
  "interest_id": "<string>",
  "item_id": "<string>",
  "interest_name": "<string>",
  "approval_recorded_at": "<ISO8601 UTC>"
}

// source_surface == "thread_context"
{
  "thread_id": "<string>",
  "thread_name": "<string>",
  "thread_state": "active | unresolved",
  "member_item_ids": ["<string>"],
  "recurring_concern": "<string>"
}

// source_surface == "relevance_urgency"
{
  "matched_interest_ids": ["<string>"],
  "relevance_scores": { "<interest_id>": 0.0 },
  "weakness_domain": "<string>",
  "urgency_indicator": "high | medium | low"
}

// source_surface == "drift_concern"
{
  "reflection_id": "<string>",
  "reflection_concern": "<string>",
  "reflection_signals": [<DriftSignal>],
  "concern_status": "pending"
}
```

**Provenance fields (required on all bridge objects):**

| Field | Required | Meaning |
|-------|----------|---------|
| `original_item_id` | Yes | The ID of the surface item that produced the signal |
| `original_item_type` | Yes | The type of the surface item |
| `confidence` | Yes | Signal confidence (0.0–1.0), advisory only |
| `urgency` | Yes | `low` / `medium` / `high`, used for Step 2 prioritization |
| `requires_review` | Yes | Must be `true` — all bridge signals require operator review |

---

### Section 7 — Validation Rules

Before a bridge object may enter Step 1 of the spine, the following validation rules apply. These are enforced by the bridge entry function before calling `record_inadequacy_event()`.

**Required fields:**

| Field | Rule |
|-------|------|
| `source_surface` | Must be one of the five allowed surface types (Section 5) |
| `surface_ref` | Must be a non-empty string |
| `created_at` | Must be a valid ISO8601 timestamp; signals older than 30 days are rejected |
| `operator_triggered` | Must be `true` — automatic surface signals are forbidden |
| `operator_trigger_id` | Must be present and non-empty |
| `payload` | Must contain the correct payload variant for the declared `source_surface` |
| `provenance.confidence` | Must be a float in range 0.0–1.0 |
| `provenance.urgency` | Must be one of `low`, `medium`, `high` |
| `provenance.requires_review` | Must be `true` |

**Forbidden conditions (any triggers rejection):**

| Forbidden | Reason |
|-----------|--------|
| `operator_triggered: false` | All bridge signals must be operator-intentional; no auto-injection |
| `source_surface` not in allowed list | Only pre-approved surface types may enter the bridge |
| `confidence: 0.0` without justification | Zero-confidence signals without explanation must be rejected |
| Duplicate `signal_id` | Replay attack prevention; same signal may not enter twice |
| Signal for an item already in a pending spine signal | Deduplication: if the same `surface_ref` has a pending Step 1 signal, a new signal is rejected unless urgency is higher |
| `urgency` artificially elevated | Urgency inflation is forbidden; `urgency` must match actual domain relevance |

**Validation sequence:**
```
1. Check required fields present → reject if missing
2. Check source_surface is allowed → reject if unknown
3. Check timestamp not stale (>30 days) → reject if stale
4. Check operator_triggered == true → reject if false
5. Check signal_id not duplicate → reject if replay
6. Check no pending signal for same surface_ref with equal/higher urgency → reject if duplicate
7. Check urgency is consistent with relevance context → reject if inflated
8. Pass → call record_inadequacy_event(bridge_object)
```

---

### Section 8 — Mapping to Spine Step 1

The bridge object is consumed by Step 1 of the spine: `inadequacy_persistence.record_inadequacy_event()`. The bridge adds a structured layer above Step 1 — it prepares the input that Step 1 receives.

**Step 1 entry function signature:**

```python
# Current signature (inadequacy_persistence.py):
def record_inadequacy_event(
    source: str,                    # source module or "surface_bridge"
    category: str,                   # inadequacy category
    runtime_state: str,             # "unavailable" | "degraded" | "fallback_used" | "rescue_used"
    event_id: str | None,           # optional event_id
    message: str | None,            # optional message
    evidence_refs: List[str] | None # optional evidence refs
) -> None
```

**Bridge-to-Step-1 mapping:**

The bridge object is translated into Step 1 parameters:

```
bridge_object.source_surface → "surface_bridge"
bridge_object.payload.derived_category → category
bridge_object.provenance.urgency → runtime_state mapping:
    urgency=high → runtime_state="unavailable"
    urgency=medium → runtime_state="degraded"
    urgency=low → runtime_state="fallback_used"
bridge_object.signal_id → event_id
bridge_object.surface_ref + provenance.original_item_id → message (concatenated)
bridge_object.provenance.original_item_id → evidence_refs[0]
bridge_object.source_surface → evidence_refs[1]
```

**The Step 1 call that the bridge produces:**

```python
record_inadequacy_event(
    source="surface_bridge",
    category=derived_category_from_payload(),
    runtime_state=urgency_to_runtime_state(bridge.provenance.urgency),
    event_id=bridge.signal_id,
    message=f"[{bridge.source_surface}] {bridge.surface_ref}: {bridge.provenance.original_item_id}",
    evidence_refs=[
        bridge.provenance.original_item_id,
        bridge.source_surface,
        bridge.operator_trigger_id
    ]
)
```

**What Step 1 does with the result:**
After `record_inadequacy_event()` writes to `weslr_inadequacy_events.jsonl`, the signal enters the normal spine flow:
- Step 2: `find_candidates()` picks it up (recurrence ≥ 2 or urgency=high)
- Step 3: `create_handoffs()` creates a handoff record
- Step 4: `qualify_handoffs()` qualifies it for CDI review
- Steps 5-10: proceed normally

The bridge does not short-circuit any spine step. It only provides the signal that enters Step 1.

---

### Section 9 — Operator Role

The bridge is operator-controlled at every stage. No surface signal enters the spine without an explicit operator action confirming it.

**When operator approval is required:**

| Stage | Requirement |
|-------|-------------|
| Bridge activation | Operator must explicitly invoke the bridge entry command: `weslr spine bridge --from-artifact <id>` or equivalent |
| Urgency level | Operator confirms or overrides the urgency annotation (low / medium / high) |
| Signal entry to Step 1 | Operator confirms: `weslr spine bridge --confirm --signal-id <id>` |
| Proposal review | Once the signal reaches Step 7, standard operator review (approve / deny / refine) applies |

**When operator confirmation is optional:**

| Stage | Behavior if not confirmed |
|-------|---------------------------|
| Urgency level suggestion | If operator does not confirm urgency, default is `medium` |
| Payload fields auto-populated | If operator does not review, auto-populated fields are used as-is with a note |

**What must never happen automatically:**

- ❌ Surface signal may not automatically call `record_inadequacy_event()` — operator must invoke the bridge
- ❌ `confidence` may not be auto-set without operator review — it must be confirmed or adjusted
- ❌ `urgency` may not be auto-escalated without operator confirmation
- ❌ A surface signal may not bypass Step 7 operator review — all proposals from bridge signals require approval
- ❌ A surface signal may not trigger execution directly — only `ExecutionGate` executes
- ❌ A surface signal for the same `surface_ref` may not re-enter the spine while a pending signal exists (duplicate rejection)

**The explicit operator command pattern:**

```
weslr spine bridge --from-artifact <artifact_id> [--urgency high] [--confirm]
weslr spine bridge --from-suggestion <item_id> --interest <interest_id> [--confirm]
weslr spine bridge --from-thread <thread_id> [--confirm]
weslr spine bridge --from-reflection <reflection_id> [--confirm]
```

The `--confirm` flag is required for the signal to actually call Step 1. Without `--confirm`, the command prints a preview of what would be submitted.

---

### Section 10 — Forbidden Drift

The following are **explicitly forbidden** for the bridge and any implementation of it:

- ❌ **Direct execution from surface signals:** A bridge signal may not bypass `ExecutionGate` to execute anything. The bridge only calls `record_inadequacy_event()`. Execution always goes through Steps 8-9 of the spine.
- ❌ **Bypass of ExecutionGate:** No bridge signal may set itself to `approved` without operator action through the formal governance surface.
- ❌ **Hidden mutation:** Bridge activation must be logged with `operator_trigger_id`. Silent bridge invocations are forbidden.
- ❌ **Parallel entry paths:** No other code path may call `record_inadequacy_event()` with `source="surface_bridge"` except through the canonical bridge entry function.
- ❌ **Auto-confidence assignment:** `provenance.confidence` may not be set without operator review or explicit calibration.
- ❌ **Urgency inflation:** `urgency` may not be set higher than the relevance context justifies. If `matched_interests` scores are all below 0.3, `urgency` may not be set to `high`.
- ❌ **Replaying stale signals:** Signals older than 30 days may not enter the bridge regardless of confirmation.
- ❌ **Duplicate signal bypass:** If a pending signal exists for the same `surface_ref`, no new signal may enter without operator acknowledgment of the duplicate.
- ❌ **Automatic surface scanning:** No background process may scan artifacts, suggestions, threads, or interests to automatically generate bridge signals. The bridge is operator-invoked only.

---

### Section 11 — Recommended First Implementation Slice

After this design document is canonicalized, the recommended first implementation slice is:

**Artifact evaluation → Spine Step 1 bridge**

*Why this slice:*
- `build_artifact_explainability()` already produces structured evaluation (`internal_strength`, `external_proof`, `risks`)
- The evaluation output is the cleanest signal — it is quantitative and has explicit thresholds
- Artifacts are already the most well-defined surface output
- The bridge entry command is simplest for artifacts: `weslr spine bridge --from-artifact <id>`

*What to implement:*
1. New CLI command `weslr spine bridge --from-artifact <artifact_id> [--urgency medium|high] [--confirm]`
2. Bridge entry function that:
   - Loads the artifact by ID
   - Calls `build_artifact_explainability()` to get current evaluation
   - Constructs a `SurfaceBridgeObject` with `source_surface="artifact_evaluation"`
   - Validates the bridge object (Section 7 rules)
   - Calls `record_inadequacy_event()` with the mapped parameters (Section 8)
3. `--confirm` flag: without it, prints a preview; with it, actually calls Step 1
4. No automatic triggering — operator must invoke explicitly

*What NOT to include in Slice 1:*
- No other surface type (suggestions, threads, relevance, drift) — these are subsequent slices
- No duplicate detection logic — this can be added in Slice 2
- No urgency auto-calculation — operator sets `--urgency` explicitly
- No integration with `build_artifact_explainability()` beyond reading its output

*Approximate code scope:*
- New module: `weslr/surface_to_spine_bridge.py` (entry function + CLI command registration)
- No changes to existing surface modules
- No changes to `inadequacy_persistence.py` (the bridge calls the existing `record_inadequacy_event()`)
- No changes to `sim.py`
- Tests: `test_surface_to_spine_bridge.py` covering validation rules and preview/confirm behavior

---

## SECTION 4 — STOP LINE

**Confirmed:**
- Design only ✅
- No production code changes ✅
- No schema changes ✅
- No new execution paths created ✅
- No automatic surface signal injection ✅
- No parallel entry path to Step 1 ✅
- No modifications to existing files ✅
- Document created: `docs/SURFACE_TO_SPINE_BRIDGE_V1.md` ✅

**Stop after this pass. No code changes.**

---

*Derived from `docs/SELF_IMPROVEMENT_SPINE_V1.md` and `docs/SELF_IMPROVEMENT_SURFACE_INTEGRATION_V1.md`. This design document is the authoritative reference for the surface-to-spine bridge. Implementation must comply with this document and the three governing documents.*
