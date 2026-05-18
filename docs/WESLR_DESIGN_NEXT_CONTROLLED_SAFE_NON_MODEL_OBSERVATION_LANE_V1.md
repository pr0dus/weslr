# WESLR Design: Next Controlled Safe Non-Model Observation Lane V1

**Layer:** `WESLR_CANON_ALIGNMENT` design only  
**Checkpoint:** `bcbf029` — controlled safe non-model observation matrix report reviewed clean  
**Scope:** decide the next structured controlled observation lane after Matrix V1

---

## SECTION 1 — STATUS

| Property | Value |
|---|---|
| repo path | `/data/data/com.termux/files/home/weslr-pr47-clean` |
| branch | `master` |
| HEAD at design start | `bcbf029` |
| design file | `docs/WESLR_DESIGN_NEXT_CONTROLLED_SAFE_NON_MODEL_OBSERVATION_LANE_V1.md` |
| layer | `WESLR_CANON_ALIGNMENT` design only |
| implementation changes | none |
| ChatResponder/respond_chat/generate_chat calls | none |
| prompt execution | none |

Known non-blocking cleanup debt: `WESLR_WORKING_ROOT.md` still records Current HEAD `79e6ce9` while actual design-start HEAD is `bcbf029`. This design records the debt only and does not fix it.

---

## SECTION 2 — CURRENT STATE

Matrix V1 is clean but limited.

Clean observations now exist for all three allowed low-risk families:

- `ordinary_task_behavior_003`
- `non_canned_cognition_002`
- `conduct_alignment_001`
- `conduct_alignment_002`

Covered families:

- `ordinary_task_behavior`
- `non_canned_cognition`
- `conduct_alignment`

Current observation character:

- mocked only where the route requires `generate_chat` interception
- metadata-only
- internal only
- not broad runtime testing
- not product readiness
- not benchmark readiness
- not a Turing/IQ/certification claim

The current readiness label remains:

`matrix_clean_but_limited`

The next lane should avoid another one-off mocked retry. It should add structure by mixing safe deterministic-route checks, one mock-required low-risk check, and one blocked-family negative control.

---

## SECTION 3 — NEXT LANE OPTIONS

### Option A — More mocked observations in the same three families

Pros:

- increases confidence that the mock-required path remains stable
- keeps within already-approved low-risk families
- uses known helper flow and known safety gates

Cons:

- diminishing returns after four clean observations
- risks becoming one-off repetition instead of structured coverage
- still says little about deterministic safe-route behavior or blocked-family boundaries

Assessment: useful only as a small component of V2, not as the whole lane.

### Option B — Broader structured matrix within the same families

Pros:

- gives systematic family and route coverage
- can compare no-mock allowed, no-mock blocked, and mock-active allowed paths
- remains inside the existing low-risk family allowlist

Cons:

- still mocked/limited for model-path candidates
- can grow too broad if not capped
- does not itself test blocked families unless combined with negative controls

Assessment: good foundation for V2 if tightly scoped.

### Option C — Safe deterministic-route observation lane

Pros:

- covers prompts that should not need a mock
- exercises route classes such as `safe_keyword_branch` and `safe_limited_ordinary_task`
- helps distinguish safe local deterministic routing from mock-required routing
- can remain metadata-only

Cons:

- deterministic routes may reflect existing canned/limited branches rather than broader cognition
- must not become a user-facing behavior claim
- must still avoid raw prompt/response retention

Assessment: important next coverage dimension.

### Option D — Negative-control lane

Pros:

- verifies blocked families remain blocked under no-mock and mock-active configs
- checks that mock activation does not bypass family boundaries
- provides safety evidence without execution

Cons:

- no callable construction allowed
- no mocked retry allowed for blocked controls
- must be reported carefully as boundary verification only

Assessment: should be included as one preflight-only negative control.

### Option E — Harness/reporting refinement lane

Pros:

- can clean stale labels or stale context markers before additional observation
- reduces future report ambiguity
- can address `WESLR_WORKING_ROOT.md` stale Current HEAD debt

Cons:

- does not advance observation coverage
- stale Current HEAD marker is currently non-blocking for guarded work
- should not be bundled into observation design or execution lanes

Assessment: cleanup should happen soon, but as a separate narrow task.

---

## SECTION 4 — RECOMMENDED NEXT LANE

Recommended primary next lane:

`DESIGN_CONTROLLED_SAFE_NON_MODEL_OBSERVATION_LANE_V2`

Reason: V1 covered the three allowed low-risk families. V2 should now define a mixed structured lane before more calls rather than simply running another matrix report.

Recommended V2 structure:

1. one deterministic-safe prompt
   - should be expected to pass without mock
   - likely route class: `safe_keyword_branch` or `safe_limited_ordinary_task`
2. one mock-required low-risk prompt
   - should block without mock and allow with mock
   - must stay inside allowed families
3. one blocked-family negative control
   - preflight only
   - no callable construction
   - no mocked retry

Candidate prompt IDs should be chosen by the V2 design from existing prompt-set metadata and routing-validator report data. This V1 next-lane design does not execute or select a final V2 prompt set.

Do not run anything in this task.

---

## SECTION 5 — SCOPE / BOUNDARIES

### Allowed families remain

- `ordinary_task_behavior`
- `non_canned_cognition`
- `conduct_alignment`

### Blocked families remain

- `memory_honesty`
- `continuity_relationship`
- `self_identity_boundaries`
- `evidence_source_boundaries`
- `guardrail_preservation`
- `live_slice_behavior`
- unsafe live-slice variants
- source/currentness/search/status paths
- protected/hidden/answer-key paths

### Negative-control rule

Blocked families may be inspected by routing-validator preflight only.

For negative controls:

- no callable construction
- no safe callable build
- no mocked retry
- no ChatResponder call
- no `respond_chat()`
- no `generate_chat()`
- no prompt execution

### V2 observation dimensions

Each V2 row should track metadata-only fields:

- family
- route_class
- alignment_status
- no-mock block/allow
- mock-active block/allow
- blocker contract status when applicable
- callable construction status
- classification
- raw retention status
- `.weslr` state status
- model/search/advisor call status
- readiness label

V2 should not broaden family scope or enable default feature flags.

---

## SECTION 6 — SUCCESS / ABORT CRITERIA

### Success criteria

V2 success should require:

- routing-validator-first for every row
- safe deterministic prompts allowed without mock
- mock-required prompts blocked without mock and allowed only with mock
- blocked-family controls blocked before callable construction
- blocker contract passes for any controlled callable row
- no raw prompt/response retention
- no `.weslr` writes
- no live model/search/advisor calls
- no official claims
- metadata-only reporting
- selected prompt IDs only in reports

### Abort criteria

Abort and classify `blocked_by_boundary` or `needs_refinement` if:

- routing validator does not run first
- blocked family reaches callable construction
- mock-required prompt proceeds without mock
- live `generate_chat`/model/search/advisor path occurs
- raw prompt/response appears in report
- `.weslr` changes
- family or route expands beyond approved scope
- default feature flag appears
- blocker contract fails for a callable row

Abort results should not be forced into execution. Report metadata only.

---

## SECTION 7 — READINESS LABEL

Design readiness label:

`lane_design_ready`

Allowed labels for the next lane:

- `lane_design_ready`
- `matrix_clean_but_limited`
- `needs_refinement`
- `blocked_by_boundary`
- `hold_before_more_retries`

No numeric score. No official benchmark, Turing, IQ, certification, or product-readiness claim.

---

## SECTION 8 — CLEANUP DEBT

Cleanup debt remains:

`FIX_WESLR_WORKING_ROOT_CURRENT_HEAD_MARKER_V1`

Current stale marker:

- recorded: `79e6ce9`
- actual at design start: `bcbf029`

Recommendation: perform this cleanup immediately after this design is reviewed, before running V2 observation work. The marker is non-blocking for guarded commands, but it is now stale across multiple reports and should be corrected before the next execution lane to reduce operator confusion.

This task does not perform the cleanup.

---

## SECTION 9 — VALIDATION RUN

Validation required for this design task:

- `python3 weslr/tests/release_gate_v1.py`
- `bash scripts/weslr_release_check.sh`

Results are recorded in the operator response after execution. This design itself does not require prompt execution or ChatResponder execution.

---

## SECTION 10 — SAFETY CONFIRMATION

This design confirms:

- design only
- no implementation
- no source/runtime edits beyond this design document
- no ChatResponder calls
- no `respond_chat()` calls
- no `generate_chat()` calls
- no prompt execution
- no live model/search/advisor calls
- no `.weslr` writes
- no raw prompt/response storage
- no raw response retention
- no broad testing
- no official claims
- no integration changes
- no `.openclaw/workspace` edits
- no family broadening
- no default feature flags
- `WESLR_WORKING_ROOT.md` stale Current HEAD recorded only, not fixed

---

## SECTION 11 — COMMIT

Commit target after validation passes:

`WESLR: design next controlled safe non-model observation lane`

The commit should include only this design file unless a release gate requires a narrow exact-file allowance. No such allowance is expected.

---

## SECTION 12 — NEXT STEP

Chosen next step:

`AUDIT_AND_UPDATE_OCC_CONTEXT_AFTER_NEXT_CONTROLLED_SAFE_NON_MODEL_OBSERVATION_LANE_DESIGN_V1`

Recommended following lane after context audit:

`FIX_WESLR_WORKING_ROOT_CURRENT_HEAD_MARKER_V1`

Then proceed to:

`DESIGN_CONTROLLED_SAFE_NON_MODEL_OBSERVATION_LANE_V2`
