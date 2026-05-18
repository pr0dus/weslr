# WESLR Design: Controlled Safe Non-Model Observation Matrix V1

**Layer:** `WESLR_CANON_ALIGNMENT` design only  
**Checkpoint:** `333e76a` — second controlled safe non-model retry with routing validator reviewed clean  
**Scope:** future safe non-model mocked ChatResponder shadow retries with routing validator active

---

## SECTION 1 — STATUS

| Property | Value |
|---|---|
| repo path | `/data/data/com.termux/files/home/weslr-pr47-clean` |
| branch | `master` |
| HEAD at design start | `333e76a` |
| design file | `docs/WESLR_DESIGN_CONTROLLED_SAFE_NON_MODEL_OBSERVATION_MATRIX_V1.md` |
| layer | `WESLR_CANON_ALIGNMENT` design only |
| implementation changes | none |
| ChatResponder/respond_chat/generate_chat calls | none |
| prompt execution | none |

Known non-blocking cleanup debt: `WESLR_WORKING_ROOT.md` still records Current HEAD `79e6ce9` while actual design-start HEAD is `333e76a`. This design records the debt only and does not fix it.

---

## SECTION 2 — CONTEXT / PURPOSE

Two clean controlled retries have already completed with routing validator active:

1. `ordinary_task_behavior_003`
   - no-mock preflight blocked before callable construction
   - mock-active preflight allowed
   - route observed as `_model_chat_response` → `generate_chat` → mock interception
   - classification: `safe_mocked_model_path_observed`

2. `non_canned_cognition_002`
   - no-mock preflight blocked before callable construction
   - mock-active preflight allowed
   - route observed as `_model_chat_response` → `generate_chat` → mock interception
   - classification: `safe_mocked_model_path_observed`

Purpose of this design: stop repeating one-off mocked retries and define a tiny controlled observation matrix first. The matrix should answer:

- which low-risk prompt families are covered
- which route classes are covered
- which safety properties are checked
- how many observations are enough before moving to the next design lane
- which families remain blocked

This is an internal safety/coverage design, not a product readiness claim.

---

## SECTION 3 — DESIGN SUMMARY

V1 matrix should remain deliberately small:

| Matrix lane | Prompt IDs | Purpose | Status |
|---|---:|---|---|
| observed baseline | `ordinary_task_behavior_003`, `non_canned_cognition_002` | prove mock-required safe path across two low-risk families | complete |
| next matrix run | `conduct_alignment_001`, optionally `conduct_alignment_002` | add conduct-alignment coverage without expanding family scope | proposed |
| hold candidate | `conduct_alignment_003` | reserve only if first conduct-alignment candidate is ambiguous | optional / not default |

Recommended V1 execution shape: **one prompt first, two prompts maximum**. Do not run a three-prompt batch unless a reviewer explicitly decides that the extra coverage is worth the additional call surface.

Preferred next selected prompt: `conduct_alignment_001`.  
Optional second prompt in same matrix report: `conduct_alignment_002`.  
Do not include raw prompt text in future matrix reports.

The V1 matrix uses existing helpers unless implementation review finds the current report assembly too manual. No new runtime behavior is proposed here.

---

## SECTION 4 — MATRIX SCOPE

### Allowed V1 families

Only these families are in scope:

- `ordinary_task_behavior`
- `non_canned_cognition`
- `conduct_alignment`

### Already observed prompt IDs

- `ordinary_task_behavior_003`
- `non_canned_cognition_002`

### Candidate prompt IDs for V1 matrix continuation

- `conduct_alignment_001` — preferred next candidate
- `conduct_alignment_002` — optional second candidate
- `conduct_alignment_003` — reserve candidate only if needed

### Route classes in scope

V1 matrix may cover:

- `forbidden_model_path` in no-mock preflight for mock-required low-risk prompts
- `requires_generate_chat_mock` in mock-active preflight
- existing already-safe non-model route classes may be summarized from validator reports, but should not be executed in this mocked retry matrix unless separately authorized

### Blocked V1 families / paths

These remain blocked in V1:

- `memory_honesty`
- `continuity_relationship`
- `self_identity_boundaries`
- `evidence_source_boundaries`
- `guardrail_preservation`
- `live_slice_behavior`
- unsafe live-slice variants
- source/currentness/search/status paths
- protected/hidden/answer-key paths
- any family or route outside the V1 allowlist

No family broadening is authorized by this design.

---

## SECTION 5 — OBSERVATION DIMENSIONS

Each future matrix row should track only metadata fields:

| Dimension | Expected V1 meaning |
|---|---|
| `prompt_id` | selected prompt ID only; no raw prompt text |
| `family` | one of allowed V1 families |
| `route_class` | no-mock and mock-active route class |
| `alignment_status` | no-mock mismatch when mock required; mock-active aligned |
| `mock_required` | true for mock-required model-path interception candidates |
| `no_mock_block_behavior` | blocked before callable construction |
| `mock_active_allow_behavior` | allowed only with mock active and permitted family |
| `blocker_contract_status` | passed before any controlled call |
| `routing_validator_applied` | true and first gate before callable construction |
| `classification` | expected `safe_mocked_model_path_observed` for mocked retry observations |
| `raw_retention_status` | no raw prompt/response retained |
| `.weslr_write_status` | unchanged |
| `write_path_status` | no write paths |
| `model_search_advisor_status` | live model/search/advisor calls false |
| `official_claim_status` | no official claims |
| `readiness_label` | qualitative only; no numeric score |

Matrix coverage should be described by family and route class, not by broad behavior or benchmark claims.

---

## SECTION 6 — SUCCESS / ABORT CRITERIA

### Success criteria

Every controlled observation must satisfy all of the following:

- no-mock preflight blocks if mock is required
- no-mock block occurs before callable construction
- mock-active preflight allows only if family is allowed and blocker contract passes
- `routing_validator_applied=True`
- `generate_chat` mocked/intercepted before any live model path
- live model call is `False`
- live search/advisor calls are `False`
- raw prompt/response retained is `False`
- `.weslr` unchanged
- no write paths
- no official claims
- metadata-only observation
- selected prompt IDs only in reports

### Failure / abort criteria

Abort and classify `blocked_by_boundary` or `ambiguous_needs_review` if any of the following occurs:

- routing validator does not run first
- no-mock prompt reaches callable construction
- mock is required but not active
- blocked family passes
- search/currentness/source route passes
- raw prompt/response appears in result/report
- `.weslr` changes
- live model/search/advisor path is attempted
- prompt family or route is outside the allowed V1 matrix
- blocker contract fails
- default feature flag or family-broadening behavior appears

Abort results should be reported as metadata-only findings, with no retry forcing.

---

## SECTION 7 — FUTURE REPORT FORMAT

Future matrix reports should use these sections:

1. Status
   - repo path, branch, HEAD, matrix version, report file
   - selected prompt IDs only
   - source/runtime changes and commits
2. Matrix scope
   - families covered
   - route classes covered
   - blocked families confirmed out of scope
3. No-mock preflight result
   - per prompt: route class, alignment status, allowed flag, blocked flag, callable touched false
4. Mock-active preflight result
   - per prompt: route class, alignment status, requires mock, mock authorized, blocker contract
5. Controlled mocked observation result
   - per prompt: call attempted, mock active, routing validator applied, generate_chat mocked, live calls false, classification
6. Metadata/privacy check
   - property labels only
   - forbidden raw keys absent
7. Side-effect check
   - `.weslr` unchanged
   - no write paths
   - no live model/search/advisor calls
8. Validation summary
   - focused tests / release gates specified by the work packet
9. Readiness label
   - one conservative qualitative label
10. Safety confirmation
   - no source/runtime changes unless explicitly authorized

### Readiness labels

Allowed labels only:

- `matrix_not_started`
- `matrix_in_progress`
- `matrix_clean_but_limited`
- `ready_for_next_design_lane`
- `blocked_by_boundary`
- `needs_refinement`

No numeric score. No official benchmark, Turing, IQ, certification, or product-readiness claim.

---

## SECTION 8 — VALIDATION RUN

Validation required for this design task:

- `python3 weslr/tests/release_gate_v1.py`
- `bash scripts/weslr_release_check.sh`

Results are recorded in the operator response after execution. This design itself does not require prompt execution or ChatResponder execution.

---

## SECTION 9 — SAFETY CONFIRMATION

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

## SECTION 10 — COMMIT

Commit target after validation passes:

`WESLR: design controlled safe non-model observation matrix`

The commit should include only this design file unless a release gate requires a narrow exact-file allowance. No such allowance is expected.

---

## SECTION 11 — NEXT STEP

Chosen next lane:

`RUN_CONTROLLED_SAFE_NON_MODEL_OBSERVATION_MATRIX_REPORT_V1`

Reason: existing routing validator, blocker contract, mock guard, and safe shadow-call helpers are sufficient for a tiny one-or-two-prompt matrix report. New reusable matrix helpers are not justified yet; design should be validated by one structured matrix report first.

Separate cleanup debt, not part of this task:

`FIX_WESLR_WORKING_ROOT_CURRENT_HEAD_MARKER_V1`
