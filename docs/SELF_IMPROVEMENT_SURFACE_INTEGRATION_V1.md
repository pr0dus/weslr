# SELF_IMPROVEMENT_SURFACE_INTEGRATION_V1.md — WESLR Surface Integration with Canonical Spine

**Status:** DESIGN — surface integration doctrine
**Date:** 2026-04-21
**Derived from:** `docs/SELF_IMPROVEMENT_SPINE_V1.md`
**Authoritative for:** All surface-to-spine integration design and future implementation decisions

---

## SECTION 1 — FILES CHANGED

| File | Change |
|------|--------|
| `docs/SELF_IMPROVEMENT_SURFACE_INTEGRATION_V1.md` | **Created** — this document |

No production code files modified. No schema changes. No behavior changes.

---

## SECTION 2 — COMMANDS RUN

None. Design-only pass.

---

## SECTION 3 — DOCUMENT CONTENT

### Section 4 — Artifact System Relation

The artifact system (`_generate_research_memo` in `main.py`, artifact metadata in `sim.py`) is WESLR's primary structured output mechanism. It is the system through which WESLR records its reasoning, conclusions, and evaluations in forms that are inspectable by operators and persist across sessions.

#### How artifacts can express:

**Problems:** Artifacts express problems through the `hypothesis` field (what WESLR believes is the core issue), the `limitations` field (what is not yet understood or is a constraint), and the `next_experiment` field (what needs to be resolved next). These three fields together constitute a problem statement.

**Hypotheses:** The `hypothesis` field is the structured record of WESLR's current working conclusion. The `alternative_interpretations` field captures what else was considered. These are the raw reasoning outputs that the self-improvement system evaluates.

**A/B options:** The `alternative_interpretations` field captures structurally distinct options that were considered. This is the existing A/B expression mechanism. The next step (not yet implemented) is expressing two full artifacts as labeled Option A / Option B variants for the same input — but the schema supports this extension.

**Evaluation outputs:** Artifacts carry evaluation metadata: `internal_strength` (how well the artifact reasoning is grounded), `external_proof` (human approvals, handoff acceptances, real_usage_hits), `risks` (what could go wrong if this is acted on), `next_actions` (what should happen next). `build_artifact_explainability()` in `sim.py` produces this evaluation. This is the most directly relevant artifact output for self-improvement — it directly characterizes the quality of a reasoning output.

#### How artifacts SHOULD feed into the spine:

Artifacts express problems and hypotheses. The spine evaluates problems and synthesizes improvement proposals. The gap between them is the **artifact-to-signal bridge**.

The intended design for this bridge:

```
Artifact (hypothesis + limitations + next_experiment)
    ↓
Artifact is reviewed / evaluated by operator
    ↓
If artifact reveals a persistent weakness:
    → inadequacy signal triggered → Step 1 of spine (record_inadequacy_event)
    → OR operator action: "weslr self eval --from-artifact <artifact_id>"
    ↓
Inadequacy signal enters the spine at Step 1
    ↓
Proceeds through Steps 2-10
```

The key insight: artifacts are the **input source** for the spine's signal layer when they express problems. They are not the spine output. The spine does not execute on artifacts — it generates proposals based on problems artifacts express.

#### What artifacts must NOT do:

- ❌ **No direct execution:** Artifacts are reasoning records. They may not call write functions, modify state, or trigger any Step 9 execution path.
- ❌ **No spine bypass:** No artifact or artifact evaluation may bypass `ExecutionGate` to trigger execution directly.
- ❌ **No automatic proposal generation:** An artifact alone may not generate a proposal without passing through the spine (Steps 1-10). If artifact evaluation reveals a problem, it must trigger an inadequacy signal to enter the spine.
- ❌ **No state mutation:** Artifact metadata (`internal_strength`, `external_proof`, `risks`) is read by the evaluation system but does not directly mutate any governance state.

**Current integration status:** Artifacts are **disconnected** from the spine. No existing code path converts artifact evaluation findings into `record_inadequacy_event()` calls. This is a documented gap (see Section 11).

---

### Section 5 — Suggestion System Relation

The suggestion system (`_derive_suggestions()` in `sim.py`, governed by `docs/SUGGESTION_SURFACE_CANON_V1.md`) surfaces structured optional-action metadata via `_suggestions` in `explain_item()` output. It is WESLR's primary mechanism for proactively flagging opportunities to the operator through normal interaction channels.

#### How suggestions surface observations:

`_derive_suggestions()` attaches to `explain_item()` output. For each artifact reviewed, it checks whether any tracked interest matches and generates an `interest_occurrence` suggestion with:
- `message`: human-readable description of the suggested action
- `confidence`: relevance-derived confidence score (advisory only)
- `reasons`: match reasons from the relevance surface
- `action`: structured command descriptor with `requires_approval: True`

The suggestion says: *"You may want to record that this artifact is relevant to interest X."* The suggestion is informational. The operator approves and executes.

#### How suggestions SHOULD feed into the spine:

A suggestion that the operator approves should become a spine input at Step 1:

```
Suggestion surfaces in explain_item() output
    ↓
Operator approves suggestion
    ↓
Structured action (record_occurrence) is executed by operator
    ↓
If the suggestion reveals an underlying inadequacy:
    → inadequacy signal triggered → Step 1 of spine
    ↓
Inadequacy signal enters the spine
    ↓
Proceeds through Steps 2-10
```

The key insight: suggestions are **observer signals**, not execution commands. When approved and acted upon, they may reveal patterns that become inadequacy signals. Acting on a suggestion is not executing the suggestion — it is recording an interest occurrence, which may then feed the spine if it reveals a pattern.

#### Confirmations — suggestions NEVER execute actions:

The `SUGGESTION_SURFACE_CANON_V1.md` contract is explicit and binding:

- `requires_approval: True` is a **structural invariant**, not a configurable option
- `_derive_suggestions()` may not call any function that modifies `interests.json`
- `add_occurrence()` is called **only after** operator explicit approval
- Suggestions may not influence routing, wording, ranking, or decisions
- Suggestion confidence is **advisory metadata only** — not a decision threshold

**Current integration status:** Suggestions are **disconnected** from the spine. No existing code path converts a suggested-and-approved interest occurrence into an inadequacy signal. Approved suggestions update `interests.json` but do not enter the spine.

---

### Section 6 — Thread System Relation

The thread system (`thread_tracker.py`, `commands/thread.py`, governed by `docs/THREAD_TRACKER_CANON_V1.md`) provides temporal grouping of related artifacts, questions, suggestions, and resolutions into named threads. It is WESLR's continuity layer for problem-solving sequences, decision records, and project tracking.

#### How threads provide temporal continuity:

A thread is a named sequence of items. Every item in a thread has an `added_at` timestamp, an `added_by` (operator or integration), a `link_type` (explicit or inferred), and a `note`. The thread `state` field tracks whether it is `active`, `unresolved`, `resolved`, or `dormant`. The thread `updated_at` is updated on every item addition.

#### How threads SHOULD support signal detection:

When multiple artifacts are grouped into the same thread and they collectively reveal a persistent problem, the thread context should support triggering the spine:

```
Multiple artifacts linked in Thread T
    ↓
Artifacts express recurring weakness (same limitation, repeated failure)
    ↓
Operator or automated review observes: same pattern appears across N artifacts in thread
    ↓
If pattern crosses inadequacy threshold:
    → inadequacy signal triggered with thread_ref: "thread_t_id"
    ↓
Step 1 of spine: record_inadequacy_event() carries thread context
    ↓
Synthesis (Step 5) uses thread context to group related signals
    ↓
Proposal (Step 6) references thread membership
```

#### How threads SHOULD provide proposal context:

When a proposal is generated, thread membership provides provenance:

```
Proposal references artifact A
    ↓
Artifact A is linked in Thread T (active, state=unresolved)
    ↓
Proposal inherits thread context: {thread_id, thread_name, thread_state}
    ↓
Operator reviewing proposal sees: "This proposal relates to thread X (unresolved)"
    ↓
Operator decides whether to approve in thread context
```

#### Confirmations — threads do NOT influence decisions:

`THREAD_TRACKER_CANON_V1.md` is explicit and binding:

- `_thread_refs` in `explain_item()` output is **advisory metadata only**
- `_thread_refs` must not influence routing, wording, ranking, scoring, or decisions
- No auto-linking — threads may not be created or mutated without explicit operator action or approved integration signal
- Thread state may not be set to `resolved` or `dormant` automatically — operator confirmation required
- Only `thread_tracker.py` may mutate `threads.json`

**Current integration status:** Threads are **disconnected** from the spine. `_thread_refs` is attached to `explain_item()` output but no existing code path uses thread context to trigger inadequacy signals or to provide proposal provenance.

---

### Section 7 — Relevance / Interest Relation

The interest tracker + relevance surface (`interest_tracker.py`, `relevance_surface.py`, governed by `docs/INTEREST_RELEVANCE_CANON_V1.md`) provides explicit, operator-controlled tracking of what matters. Relevance scoring evaluates how strongly each tracked interest matches a given artifact context.

#### How relevance identifies "what matters":

Relevance is **interest-matching against context**. The relevance surface scores each tracked interest against the text, tags, and metadata of the current artifact. The score is structural (tag overlap, name match, text proximity, recency, occurrence count). The output is a ranked list of scored interests with `match_reasons`.

What relevance IS:
- A read-only query over operator-defined interests
- Advisory metadata attached to `explain_item()` output as `_relevant_interests`
- Deterministic, inspectable, reversible

What relevance is NOT:
- A reasoning engine — scoring is structural, not inferential
- A decision system — relevance output never decides anything
- A routing authority — it does not change which handler is called
- A learning system — interests are created explicitly, not derived autonomously

#### How relevance SHOULD influence signal prioritization:

Relevance identifies which operator-defined interests are most relevant to a given artifact. This information can be used to contextualize proposals and to weight signal urgency:

```
Artifact evaluated
    ↓
Relevance surface scores interests against artifact context
    ↓
Highly-scored interests (+ high occurrence count + recent activity)
    ↓
If artifact reveals a weakness related to a highly-scored interest:
    → Signal urgency flagged: "weakness in high-relevance area"
    → inadequacy signal enters spine with urgency annotation
    ↓
Step 3: handoff creation uses urgency to set severity
    ↓
Step 6: proposal references relevance context
```

The key design principle: **relevance may influence urgency annotation and proposal context — not routing, not execution, not approval decisions.**

#### What is forbidden for relevance:

From `INTEREST_RELEVANCE_CANON_V1.md` and `SUGGESTION_SURFACE_CANON_V1.md`:

- ❌ **No routing control:** Relevance scores may not be used to select or bias handler selection, agent routing, or response strategy
- ❌ **No execution impact:** Relevance may not trigger, gate, or modify any execution path
- ❌ **No decision authority:** Relevance scores may not be used as decision thresholds or approval gates
- ❌ **No confidence as authority:** Suggestion confidence (derived from relevance) may not be used as a routing gate
- ❌ **No auto-write:** Relevance surface may not call any write function (`create_interest()`, `add_occurrence()`)
- ❌ **No hidden prioritization:** Routing authority must remain explicit and inspectable

**Current integration status:** Relevance is **disconnected** from the spine. It surfaces as `_relevant_interests` metadata in `explain_item()` but no existing code path uses relevance scores to annotate inadequacy signal urgency, influence proposal context, or weight synthesis priorities.

---

### Section 8 — Unified Flow with Surfaces

The complete system including all surfaces and the canonical spine:

```
┌─────────────────────────────────────────────────────────────────┐
│  ARTIFACT SYSTEM                                                  │
│  hypothesis / limitations / alternative_interpretations          │
│  internal_strength / external_proof / risks / next_actions        │
│  evaluation via build_artifact_explainability()                  │
└──────────────────────────┬──────────────────────────────────────┘
                           │ (disconnected — gap, see Sec 11)
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│  SUGGESTION SYSTEM                                                 │
│  _derive_suggestions() → _suggestions in explain_item()           │
│  interest_occurrence: requires_approval: True                    │
│  12-hour cooldown (in-memory)                                     │
└──────────────────────────┬──────────────────────────────────────┘
                           │ (disconnected — gap, see Sec 11)
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│  THREAD SYSTEM                                                     │
│  threads.json: items with types (artifact/question/suggestion)     │
│  _thread_refs in explain_item(): advisory metadata only           │
└──────────────────────────┬──────────────────────────────────────┘
                           │ (disconnected — gap, see Sec 11)
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│  RELEVANCE / INTEREST SYSTEM                                      │
│  interests.json + relevance_surface.query_relevant_interests()   │
│  _relevant_interests in explain_item(): advisory metadata only   │
└──────────────────────────┬──────────────────────────────────────┘
                           │ (disconnected — gap, see Sec 11)
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│  SIGNAL DETECTION (Step 1)                                        │
│  inadequacy_persistence.record_inadequacy_event()                │
│  → weslr_inadequacy_events.jsonl                                 │
│                                                                  │
│  Operator may manually trigger via:                              │
│  "weslr self eval" → self_eval.run_self_evaluation()             │
│  "weslr sci proposals-create" → ChangeProposal via ExecutionGate│
└──────────────────────────┬──────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│  CANONICAL SPINE (Steps 2-10)                                     │
│                                                                  │
│  Step 2: find_candidates() [60-min window, recurrence ≥ 2]      │
│  Step 3: create_handoffs() → handoffs JSONL                      │
│  Step 4: qualify_handoffs() [confidence ≥ 0.7 or severity]      │
│  Step 5: synthesize_all() [read-only: 5 synthesis modes]        │
│  Step 6: InsightProposalConverter → proposal payloads           │
│  Step 7: build_cdi_bundle() + operator review                    │
│  Step 8: ExecutionGate.transition_state() [approve/deny]       │
│  Step 9: execute_proposal_if_approved()                        │
│  Step 10: AuditLedgerEngine → audit trail                        │
└──────────────────────────┬──────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────────────┐
│  OPERATOR REVIEW + EXECUTION                                      │
│  approve / deny / refine                                         │
│  if approved: execution → audit trail                           │
└─────────────────────────────────────────────────────────────────┘
```

**Surface design principles:**

Each surface has a defined role:

| Surface | Role |
|---------|------|
| Artifact | Problem/hypothesis expression. Input source for signal context. |
| Suggestion | Operator-gated action opportunity. Observer signal, not executor. |
| Thread | Temporal grouping. Provides signal provenance and proposal context. |
| Relevance | Attention signal. May annotate urgency and proposal context. Not authority. |

All surfaces are **read-only for governance decisions**. None of them route, decide, execute, or modify governance state. All consequential actions flow through the spine.

---

### Section 9 — Forbidden Drift

The following are **explicitly forbidden** across all surface integrations:

- ❌ **Surfaces creating execution paths:** Artifacts, suggestions, threads, and relevance metadata may not directly trigger execution. Only `ExecutionGate.execute_proposal_if_approved()` may execute.
- ❌ **Surfaces bypassing ExecutionGate:** No surface may route a proposal directly to execution without going through Steps 7-10 of the canonical spine.
- ❌ **Surfaces mutating state directly:** No surface's output may write to `interests.json`, `threads.json`, `weslr_inadequacy_events.jsonl`, `change_proposals.json`, or any governance file without using the canonical write-authority function.
- ❌ **Surfaces becoming decision engines:** Artifacts may not auto-evaluate themselves into proposals. Suggestions may not evaluate themselves into approvals. Threads may not evaluate themselves into resolutions. Relevance may not evaluate itself into routing decisions.
- ❌ **Surfaces influencing routing:** `_relevant_interests`, `_suggestions`, and `_thread_refs` may not be used as conditions in any routing decision.
- ❌ **Auto-linking threads:** Thread links may not be created without explicit operator action or approved integration signal. No surface may infer thread membership.
- ❌ **Auto-creating interests:** Interests may not be created by artifacts, suggestions, threads, or relevance scoring. Explicit `create_interest()` only.
- ❌ **Auto-recording occurrences:** Occurrences may not be recorded without operator approval via the suggestion surface's `requires_approval: True` invariant.
- ❌ **Relevance as approval gate:** Suggestion confidence derived from relevance may not be used as a threshold for approving proposals, executing changes, or routing requests.
- ❌ **Thread state auto-resolution:** Threads may not be set to `resolved` or `dormant` without explicit operator confirmation.

---

### Section 10 — Current Gaps

The following gaps describe where surfaces are currently disconnected from the canonical spine. These are documented gaps, not proposals. Solutions are deferred to later steps.

**Gap 1 — Artifact evaluation not connected to inadequacy signals.**

No existing code path converts artifact evaluation findings (`build_artifact_explainability()`) into `record_inadequacy_event()` calls. Artifacts that reveal persistent weaknesses do not automatically enter the spine as inadequacy signals. The bridge requires either:
- An operator action: `weslr self eval --from-artifact <id>`
- A future automatic bridge: artifact evaluation → inadequacy signal (requires a canonical document defining the trigger conditions)

**Gap 2 — Suggestions not connected to spine entry.**

When an operator approves a suggestion (`requires_approval: True` → operator approves → action executed), the approval event is not captured as an inadequacy signal. Approved suggestions update `interests.json` but do not enter Step 1. The gap is that the feedback from surface action to signal detection does not exist.

**Gap 3 — Thread context not used for signal grouping.**

`threads.json` contains related artifacts and questions, but no code uses thread membership to group inadequacy signals. A recurring weakness visible across multiple artifacts in the same thread is not currently aggregated into a single trigger candidate. The `thread_ref` field exists in the proposal data model but is not used in Step 5 synthesis.

**Gap 4 — Relevance not used for urgency annotation.**

Relevance scores (`_relevant_interests`) are surfaced in `explain_item()` output but are not fed into Step 1 (`record_inadequacy_event()`) as urgency annotations. A weakness in a high-relevance interest area should be flagged with elevated urgency, but no code path exists for this annotation.

**Gap 5 — No surface feedback into drift loop.**

`record_drift_signal()` is the entry point for the drift loop. No surface (artifacts, suggestions, threads, relevance) currently feeds into this function. The drift loop (9 concern types) and the inadequacy pipeline are separate parallel systems with no cross-feeding.

**Gap 6 — No unified surface-to-spine operator command.**

There is no single CLI command that takes a surface output (artifact ID, thread ID, suggestion type) and routes it into the canonical spine. The operator must know which command to use for which type of input. The gap is the absence of a unified surface integration command.

**Gap 7 — No proposal context for surfaces in review output.**

When a proposal is presented for operator review (Step 7), there is no standard way to include surface context: which relevant interests were matched, which thread the proposal relates to, which artifacts triggered the signal. The proposal view (`adequacy_lineage_view.build_proposal_view()`) supports optional `lineage_ref` and `adequacy` fields, but no surface integration populates them.

---

## SECTION 4 — STOP LINE

**Confirmed:**
- Design only ✅
- No production code changes ✅
- No modifications to existing files ✅
- No new execution paths created ✅
- No new systems invented ✅
- Document created: `docs/SELF_IMPROVEMENT_SURFACE_INTEGRATION_V1.md` ✅
- All surface-to-spine connections documented as design intent ✅
- All surface constraints confirmed as consistent with existing canons ✅

**Stop after this pass. No code changes. No modifications to existing files.**

---

*Derived from `docs/SELF_IMPROVEMENT_SPINE_V1.md`. All surface integrations must comply with this document and the governing canon documents (INTEREST_RELEVANCE_CANON_V1, SUGGESTION_SURFACE_CANON_V1, THREAD_TRACKER_CANON_V1) and SELF_IMPROVEMENT_SPINE_V1.md.*
