# SATUI_FEEDBACK_AND_ARTIFACT_REVISION_CANON_V1.md

**Status:** DESIGN DRAFT — canonical workflow definition
**Date:** 2026-04-21
**Based on:** Inspection reports `SATUI_INSPECT` and `SATUI_MULTI_USER_INSPECT`
**Authoritative for:** SatUi feedback loop, artifact revision storage, and multi-user governance

---

## SECTION 1 — FILES CHANGED

| File | Change |
|------|--------|
| `docs/SATUI_FEEDBACK_AND_ARTIFACT_REVISION_CANON_V1.md` | **Created** — this document |

No production code files modified. No schema changes. No behavior changes.

---

## SECTION 2 — COMMANDS RUN

None. This pass is documentation-only.

---

## SECTION 3 — DESIGN SUMMARY

### Section A — Purpose

The SatUi feedback and artifact revision workflow is the mechanism by which users (operators, admins, or external requesters) interact with **artifacts WESLR has generated** — memos, hypotheses, reports, summaries — to request revisions, compare alternatives, and feed structured feedback back into WESLR's governed improvement systems.

**Why this is different from main chat:**
- Main chat processes natural-language dialogue and routes intents to various systems
- SatUi feedback operates on **persistent objects** (artifacts) with **object IDs**, not free text
- Main chat generates responses that are transient; SatUi feedback generates **stored revisions** that can be compared, judged, and re-used
- Main chat has no reference resolution; SatUi feedback requires resolving "improve this" → a specific stored artifact ID

**Why it is needed for institutional deployment:**
- Institutions require **accountability**: who requested what revision, who approved it, what changed
- Institutions require **comparison**: option A vs option B, with judgment recorded
- Institutions require **audit trails**: feedback must feed back into the proposal governance system, not disappear
- External users (universities, labs, companies) submitting suggestions need to see their suggestions converted to proposals, tracked, and resolved

---

### Section B — Current Reality (Proven by Inspection)

#### B.1 — Suggestion Flow

| Step | File | Function |
|------|------|----------|
| Created | `weslr/suggestion_box.py` | `SuggestionBox.submit_request()` → `continuity/suggestion_box/requests.json` |
| Surfaced | `weslr/suggestion_bridge.py` | `SuggestionBridge.list_proposal_candidates()` → `review_queue.json` |
| Routed to review | `weslr/suggestion_bridge.py` | `SuggestionBridge.convert_to_proposal_candidate()` → `review_queue.json` |
| Operator reviews | `weslr_backend_contract.py` | `review_suggestion(candidate_id, action, reason)` → updates candidate `review_status` |

#### B.2 — Self-Improvement Proposal Flow

| Step | File | Function |
|------|------|----------|
| Weakness detected | `self_improvement_observation.record_observation()` | Writes to `self_improvement_observations.json` |
| Proposal created | `self_improvement_proposal.create_proposal()` | Writes to `self_improvement_proposals.json` |
| Surfaced | `self_improvement_chat.py` | `handle_chat_intent()` — parses `show pending proposals`, `show proposal <id>` |
| Operator approves | `self_improvement_proposal.approve_proposal()` | Updates `review.state` → `approved` |
| Operator applies | `self_improvement_apply.apply_proposal()` | Applies change + runs tests + records `rollback_command` |
| Rollback if needed | `self_improvement_apply.rollback_proposal()` | Records status → `rolled_back` |

#### B.3 — Artifact Revision Text Generation (Single)

| Step | File | Function |
|------|------|----------|
| Proposal intent detected | `dialogue.py` | Tokens `["improve this", "better version", "suggest a better", ...]` → `is_proposal_intent = True` |
| Revision generated | `dialogue.py` | `_artifact_proposal_answer()` — returns `Proposed revision:` text |
| Fallback generation | `dialogue.py` | `_artifact_proposal_answer_from_question()` |
| Version comparison | `dialogue.py` | `_compare_versions_for_teaching(version_a, version_b, level)` — requires explicit IDs passed in `research_context` |

**CRITICAL GAP:** Artifact revisions are **never stored**. `_artifact_proposal_answer()` generates text in-memory only. No artifact ID, no store, no reference possible.

#### B.4 — Explicit Version Comparison Support

`_compare_versions_for_teaching()` in `dialogue.py` (line 686) exists and functional, but requires `version_a`/`version_b` passed as explicit dicts in `research_context`. There is no stored version pair with IDs.

---

### Section C — What Is Missing (Proven Gaps)

| Gap | Evidence |
|-----|----------|
| **Persistent artifact identity** | `_artifact_proposal_answer()` returns text only; no artifact store; no ID assigned |
| **Object reference resolution** | No code resolves "improve this" → a specific stored artifact; each call generates from scratch |
| **A/B option storage** | No function generates stored Option A / Option B artifact pairs |
| **Comparison/judgment persistence** | `_compare_versions_for_teaching()` output is transient; no comparison artifact stored |
| **User identity/session/role model** | `requester_id` in `SuggestionBox` is optional, not enforced; no login, no session, no user ID in `chat_ui.py` |
| **Operator/admin institutional oversight** | `suggestion_bridge` and `self_improvement_proposal` are separate systems; no unified review surface; no web admin panel |
| **Closed SatUi feedback loop** | "improve this" → generates text → returns response → **NOT STORED** → cannot be referenced again |

---

### Section D — Core Objects

The canonical object types required for this workflow:

#### D.1 — Artifact

A WESLR-generated output (memo, hypothesis, report, summary, research artifact).

| Field | Type | Purpose |
|-------|------|---------|
| `artifact_id` | `str` | Unique ID (e.g., `art-<timestamp>-<seq>`) |
| `type` | `str` | One of: `memo`, `hypothesis`, `report`, `summary`, `research` |
| `content` | `dict` | The artifact content (hypothesis, next_experiment, limitations, confidence, etc.) |
| `created_by` | `str` | User ID or `weslr` for system-generated |
| `created_at` | `int` | Unix timestamp in milliseconds |
| `version` | `int` | Version number (starts at 1) |
| `parent_artifact_id` | `str \| null` | If this is a revision of a previous artifact |
| `source_intent` | `str` | What prompted creation: `proposal_intent`, `suggestion`, `operator_request`, `self_improvement` |
| `status` | `str` | One of: `draft`, `active`, `superseded`, `archived` |
| `metadata` | `dict` | Free-form additional context |

#### D.2 — Artifact Revision

A revised version of an existing artifact, generated in response to user feedback.

| Field | Type | Purpose |
|-------|------|---------|
| `revision_id` | `str` | Unique ID (e.g., `rev-<timestamp>-<seq>`) |
| `artifact_id` | `str` | ID of the artifact being revised |
| `feedback_id` | `str` | ID of the feedback that triggered this revision |
| `revision_type` | `str` | One of: `hypothesis`, `next_experiment`, `limitations`, `confidence`, `full` |
| `original_section` | `str` | Which section was revised |
| `original_content` | `str` | Content before revision |
| `proposed_content` | `str` | Content after revision |
| `diagnosis` | `str` | Why the revision was suggested |
| `generated_by` | `str` | `weslr` or operator ID |
| `generated_at` | `int` | Unix timestamp in milliseconds |
| `status` | `str` | One of: `proposed`, `approved`, `rejected`, `applied` |

#### D.3 — Option A Artifact / Option B Artifact

A pair of alternative artifacts generated for the same input/context, for user comparison.

| Field | Type | Purpose |
|-------|------|---------|
| `pair_id` | `str` | Shared ID linking the pair (e.g., `pair-<timestamp>-<seq>`) |
| `option_label` | `str` | Either `A` or `B` |
| `artifact_id` | `str` | ID of the artifact for this option |
| `generation_context` | `dict` | The input that produced this option |
| `method` | `str` | How it was generated: `markov`, `bandit`, `entropy`, `gradient`, `hybrid`, `manual` |
| `score` | `float` | Quality/relevance score (0.0–1.0) |
| `generated_at` | `int` | Unix timestamp in milliseconds |

#### D.4 — Comparison Artifact

A structured comparison of Option A vs Option B.

| Field | Type | Purpose |
|-------|------|---------|
| `comparison_id` | `str` | Unique ID |
| `pair_id` | `str` | ID of the compared pair |
| `option_a_id` | `str` | ID of Option A artifact |
| `option_b_id` | `str` | ID of Option B artifact |
| `comparison_text` | `str` | Natural-language comparison (from `_compare_versions_for_teaching()`) |
| `assessment_criteria` | `list[str]` | Which criteria were used: `rigor`, `specificity`, `verifiability`, etc. |
| `winner` | `str \| null` | `A`, `B`, or `null` if no winner determined |
| `created_by` | `str` | User ID or `weslr` |
| `created_at` | `int` | Unix timestamp in milliseconds |

#### D.5 — Feedback Object

User feedback on a specific artifact, captured through SatUi input.

| Field | Type | Purpose |
|-------|------|---------|
| `feedback_id` | `str` | Unique ID |
| `artifact_id` | `str \| null` | ID of artifact beingFeedback (null if new artifact requested) |
| `feedback_type` | `str` | One of: `improve`, `alternative_request`, `explanation_request`, `weakness_flag`, `approval`, `rejection` |
| `raw_input` | `str` | Original user text |
| `resolved_intent` | `str` | Interpreted intent: `improve_this`, `give_option_B`, `explain_this`, `this_is_weak` |
| `user_id` | `str` | ID of user providing feedback |
| `session_id` | `str` | Current session ID |
| `created_at` | `int` | Unix timestamp in milliseconds |
| `status` | `str` | One of: `received`, `routed`, `resolved` |

#### D.6 — Judgment Artifact

Operator or user judgment on an artifact or comparison.

| Field | Type | Purpose |
|-------|------|---------|
| `judgment_id` | `str` | Unique ID |
| `target_type` | `str` | One of: `artifact`, `revision`, `comparison`, `option_pair` |
| `target_id` | `str` | ID of the target object |
| `judgment` | `str` | One of: `approved`, `rejected`, `superseded`, `needs_revision` |
| `reason` | `str` | Free-text reason for judgment |
| `judged_by` | `str` | Operator or admin ID |
| `judged_at` | `int` | Unix timestamp in milliseconds |
| `institution_id` | `str \| null` | Institution scope (if applicable) |

#### D.7 — Operator Review Record

Auditable record of operator review action on any governed object.

| Field | Type | Purpose |
|-------|------|---------|
| `record_id` | `str` | Unique ID |
| `object_type` | `str` | Type of reviewed object |
| `object_id` | `str` | ID of reviewed object |
| `action` | `str` | One of: `approved`, `denied`, `applied`, `rolled_back`, `superseded` |
| `operator_id` | `str` | Operator who performed action |
| `institution_id` | `str \| null` | Institution scope |
| `timestamp` | `int` | Unix timestamp in milliseconds |
| `notes` | `str \| null` | Optional notes |
| `audit_ref` | `str` | Reference to audit ledger entry |

---

### Section E — Feedback Resolution Model

This section defines how SatUi input resolves to stored objects. **This is not yet implemented.**

#### E.1 — Resolution Rules

| User Input Pattern | Resolved Intent | Resolution Path |
|--------------------|-----------------|-----------------|
| `"improve this"` / `"improve the hypothesis"` | `improve_this` | Look up most recent `active` artifact for current user/session in `active_artifact_registry.json`. Route to `_artifact_proposal_answer()` with that `artifact_id` as context. |
| `"give option B"` / `"show alternative"` | `give_option_B` | Look up most recent `option_pair` for current user/session. Return Option B artifact. If no pair exists, generate Option B via `variation_generator.py`. |
| `"explain this"` / `"explain this artifact"` | `explain_this` | Look up `artifact_id` from registry. Generate explanation via `dialogue.py` `_compare_versions_for_teaching()` with stored version history. |
| `"this is weak"` / `"this is not good"` | `weakness_flag` | Look up `artifact_id`. Create `Feedback` object with `feedback_type = weakness_flag`. Route to proposal system if repeated. |
| `"approve it"` / `"deny it"` | `judgment` | Look up current `proposal_id` or `artifact_id` in chat context. Execute governance action via existing `approve_proposal()` / `deny_proposal()`. |

#### E.2 — Active Artifact Registry

A required new component: `active_artifact_registry.json`

| Field | Type |
|-------|------|
| `user_id` | `str` |
| `session_id` | `str` |
| `current_artifact_id` | `str` |
| `current_proposal_id` | `str` |
| `current_option_pair_id` | `str \| null` |
| `last_updated` | `int` |

The registry tracks the **current working context** per user session, enabling reference resolution without explicit IDs in every message.

**This component does not exist yet.**

---

### Section F — Multi-User / Institution Model

This section defines the required institutional model. **Not implemented.**

#### F.1 — Required Identity Model

| Entity | Required |
|--------|----------|
| `user_id` | Required for all external users |
| `session_id` | Required per session |
| `operator_id` | Required for admin/operator actions |
| `institution_id` | Required for institutional scope |

#### F.2 — Role Authority

| Role | Can Do |
|------|--------|
| `viewer` | Submit suggestions, view own artifacts |
| `contributor` | viewer + submit feedback on artifacts |
| `operator` | contributor + approve/deny proposals, review suggestions |
| `admin` | operator + manage institution members, view all artifacts |
| `system` | WESLR internal actions |

#### F.3 — Institution Scope

- Proposals and artifacts must be scoped to `institution_id` when the user belongs to an institution
- Cross-institution visibility: **forbidden** — users cannot see artifacts from other institutions
- Operator/admin can only see artifacts within their institution scope
- Public (unauthenticated) users: no institution scope, artifacts marked `public_guest`

#### F.4 — Visibility Rules

| Object | Public | Guest | Contributor | Operator | Admin |
|--------|--------|-------|-------------|----------|-------|
| Own artifacts | No | Yes | Yes | Yes | Yes |
| Own proposals | No | Yes | Yes | Yes | Yes |
| Institution artifacts | No | No | Yes | Yes | Yes |
| All proposals (institution) | No | No | No | Yes | Yes |
| System proposals | No | No | No | Yes | Yes |

---

### Section G — Relation to Existing Systems

This section defines how the SatUi workflow should integrate with existing systems. **Italics = reuse. Bold = do not create parallel system.**

#### G.1 — Systems to Reuse

| System | Role in SatUi Workflow |
|--------|------------------------|
| **`suggestion_box.py`** | Ingest external suggestions from `SuggestionBox.submit_request()`. Do NOT create a parallel suggestion intake. |
| **`suggestion_bridge.py`** | Convert suggestions to proposal candidates via `convert_to_proposal_candidate()`. Continue routing to `review_queue.json`. Do NOT create a parallel review queue. |
| **`self_improvement_proposal.py`** | Core proposal lifecycle: `create_proposal()`, `approve_proposal()`, `deny_proposal()`. SatUi feedback that becomes a proposal must use this system, not a new one. |
| **`self_improvement_apply.py`** | Apply approved proposals with tests and rollback. SatUi-generated proposals flow through here for execution. |
| **`change_proposals.py` / `ExecutionGate`** | Governance enforcement. All proposals that reach execution must pass `ExecutionGate.is_approved_for_execution()`. |
| **`dialogue.py` `_artifact_proposal_answer()`** | Single revised artifact text generation. SatUi revision generation should extend this, not replace it. Output should be persisted to artifact store. |
| **`variation_generator.py`** | Mathematical variation generation. Should be integrated as the Option A / Option B generation engine for the comparison workflow. |

#### G.2 — Systems to Extend (Not Replace)

| System | Extension Required |
|--------|-------------------|
| **`dialogue.py`** | `_artifact_proposal_answer()` must be extended to write its output to the artifact store instead of returning text only |
| **`self_improvement_chat.py`** | `handle_chat_intent()` must be extended to resolve artifact references via `active_artifact_registry.json` |
| **`suggestion_bridge.py`** | Must be extended to accept feedback objects that reference stored artifacts, not just raw suggestion dicts |

#### G.3 — Systems to Create (New Components)

| New Component | Purpose |
|---------------|---------|
| **Artifact Store** (`artifact_store.json` or `artifacts/`) | Persistent storage for all generated artifacts with IDs |
| **Active Artifact Registry** (`active_artifact_registry.json`) | Per-session tracking of current working context |
| **Feedback Store** (`feedback_store.json`) | Persistent storage for all feedback objects |
| **Option Pair Store** (`option_pairs.json`) | Persistent storage for Option A / Option B pairs |
| **Comparison Store** (`comparison_store.json`) | Persistent storage for comparison artifacts |
| **Session/Identity Service** | User authentication, session management, role resolution |

#### G.4 — Forbidden Parallel Systems

**Do NOT create:**
- A third proposal system alongside `self_improvement_proposal.py` and `suggestion_bridge.py`
- A separate artifact generation path alongside `dialogue.py`
- A separate feedback storage alongside `feedback_store.json`
- A second chat architecture alongside `chat_ui.py`

All SatUi feedback must route through existing systems where possible, or extend them via documented hooks, not parallel paths.

---

### Section H — Forbidden Drift

The following are explicitly forbidden in any implementation of this workflow:

1. **No third proposal system.** All proposals must flow through either `self_improvement_proposal.py` (internal weakness) or `suggestion_bridge.py` (external suggestions). No new proposal schema may proliferate without a normalization layer.

2. **No ephemeral artifact revisions without IDs.** `_artifact_proposal_answer()` output must not be treated as a stored object until it has an `artifact_id` and is written to the artifact store. Returning text in a response does not constitute persistence.

3. **No SatUi as a second chat architecture.** SatUi is a feedback and artifact management layer over the existing chat. It must not develop its own dialogue routing, intent parsing, or response generation that duplicates `dialogue.py`.

4. **No silent self-modification.** Artifact revisions proposed through SatUi must go through the same governance path as any other proposal: `pending_review` → `approved`/`denied` → `applied`. No direct code modification from SatUi feedback.

5. **No user feedback bypassing governance.** User feedback like "improve this" generates a proposed revision. That revision must be operator-reviewed before it becomes a new active artifact. Feedback cannot auto-apply.

6. **No A/B revisions without persistent references.** Option A and Option B artifacts must be stored with `pair_id` before comparison is surfaced to the user. In-memory generation is not sufficient.

7. **No cross-institution visibility.** Artifacts, proposals, and feedback from one institution must not be visible to users or operators of another institution.

---

### Section I — Recommended First Implementation

**Recommended first step: Persistent Artifact Identity and Reference Resolution**

**Choice:** Implement the **Artifact Store** + **Active Artifact Registry** as the foundational layer.

**Justification:**

All other components (feedback objects, revision objects, option pairs, comparisons) depend on having **persistent artifacts with IDs**. Without an artifact store:
- "improve this" cannot resolve to a stored object (E.1 resolution requires artifact_id)
- Option A / Option B cannot be stored and compared (D.3/D.4 require artifact store)
- Artifact revisions from `_artifact_proposal_answer()` are lost after the HTTP response
- No comparison can be persisted for operator review

The artifact store is the **smallest safe foundation** because:
1. It is additive — existing code that generates artifacts can continue to work, with the store as an optional write
2. It does not change existing behavior — no existing code depends on artifacts being stored (none are)
3. It enables all other workflows — feedback resolution, A/B comparison, and governance all require it
4. It is bounded — artifact store schema is well-defined (D.1)
5. It is testable — `_artifact_proposal_answer()` output can be captured and written to the store with minimal changes to `dialogue.py`

**What to implement:**
1. `artifacts/` directory with JSON storage (one file per artifact or `artifacts.jsonl`)
2. `artifact_store.py` module with CRUD operations: `create_artifact()`, `get_artifact()`, `update_artifact()`, `list_artifacts()`, `search_artifacts()`
3. `active_artifact_registry.json` for per-session context tracking
4. Extend `_artifact_proposal_answer()` to write proposed revisions to the store with `status=proposed`
5. Extend `handle_chat_intent()` to resolve "improve this" via registry

**What NOT to implement first:**
- User identity/session system (requires auth infrastructure, defer)
- Institution scope (depends on user identity, defer)
- Option A / Option B generation (depends on artifact store, implement second)
- Comparison store (depends on option pairs, implement third)

---

### Section J — Integration Points

Canonical integration points into existing systems:

| Existing System | Integration Point | Extension |
|-----------------|-------------------|-----------|
| `dialogue.py` | `_artifact_proposal_answer()` | Write output to artifact store before returning text |
| `self_improvement_chat.py` | `handle_chat_intent()` | Add `resolve_artifact_reference()` hook before calling `_artifact_proposal_answer()` |
| `variation_generator.py` | `generate_variations_for_theme()` | Call from SatUi Option A / Option B generation path |
| `self_improvement_proposal.py` | `create_proposal()` | SatUi feedback that qualifies as a proposal calls this with `observation_ids` from feedback |
| `suggestion_bridge.py` | `convert_to_proposal_candidate()` | SatUi feedback on suggestions routes through here |
| `change_proposals.py` / `ExecutionGate` | `ExecutionGate.review_proposal()` | All artifact revisions that become proposals go through governance |

---

### Section K — Stop Line

**Confirmed:**
- Documentation only ✅
- No production code changes ✅
- No schema changes ✅
- No behavior changes ✅
- No modifications to existing files ✅
- New document created: `docs/SATUI_FEEDBACK_AND_ARTIFACT_REVISION_CANON_V1.md` ✅

**Stop after this pass. No code changes. No schema changes. No behavior changes.**

---

*This document defines the canonical SatUi feedback and artifact revision workflow. All implementation work must reference this document before touching related code. When the artifact store is implemented, this document should be updated to reflect the new implementation state.*
