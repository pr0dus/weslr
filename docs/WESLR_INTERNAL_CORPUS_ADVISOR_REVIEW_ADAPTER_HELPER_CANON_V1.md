# WESLR Internal Corpus Advisor Review Adapter Helper Canon V1

## Status

- `APPROVE_WESLR_INTERNAL_CORPUS_ADVISOR_REVIEW_ADAPTER_HELPER_CANON_V1_ONLY`
- `internal_corpus_advisor_review_adapter_helpers`
- `helper_ready`
- `redacted_review_ready`
- `non_executing`
- `non_scoring`
- `non_authoritative`
- `local_scan_advisor_review_compatible_only`
- `advisor_call_allowed = false`
- `model_calls = false`
- `safe_to_execute = false`
- `queue_persistence_performed = false`
- `not_advisor_call_ready`
- `not_model_call_ready`
- `not_queue_persistence_ready`
- `not_scoring_ready`
- `not_certification_ready`

This canon locks the meaning and boundaries of the WESLR internal corpus advisor review adapter helpers.

The helpers are ready only for redacted, in-memory, non-authoritative, non-executing advisor-review-compatible payload construction and operator review. They are not advisor execution, not model execution, not queue persistence, not scoring, not certification, and not runtime authority.

## 1. Canon Status

The adapter helpers are canonically:

- helper-ready
- redacted-review-ready
- non-executing
- non-scoring
- non-authoritative
- local-scan/advisor-review compatible only

The adapter helpers are not:

- advisor-call-ready
- model-call-ready
- queue-persistence-ready
- scoring-ready
- certification-ready

`helper_ready` means the implemented helpers can construct, validate, summarize, copy, and render a redacted advisor-review-compatible payload for operator inspection. It does not authorize sending that payload to an advisor, model, queue persistence system, runner, scoring engine, or runtime surface.

## 2. Helper Chain

The canonical helper chain is:

1. `docs/WESLR_INTERNAL_CORPUS_TO_ADVISOR_REVIEW_ADAPTER_DESIGN_V1.md`
2. `weslr/internal_corpus_advisor_review_adapter.py`
3. `build_internal_corpus_advisor_review_payload_v1`
4. `validate_internal_corpus_advisor_review_payload_v1`
5. `summarize_internal_corpus_advisor_review_payload_v1`
6. `to_internal_corpus_advisor_review_payload_json_safe_v1`
7. `render_internal_corpus_advisor_review_payload_markdown_v1`
8. `weslr/tests/test_internal_corpus_advisor_review_adapter_v1.py`

The helper chain is in-memory only. It builds proposal payloads, validation diagnostics, count-only summaries, JSON-safe copies, and redacted Markdown surfaces. It does not write files, persist queue items, call advisors, call models, execute cases, score outputs, or mutate runtime state.

## 3. Existing Advisor/Audit Infrastructure Reuse

The adapter reuses or aligns with existing WESLR advisor/audit infrastructure, including:

- `AdvisorReviewQueueSafetyFlags`
- `create_empty_advisor_review_queue_item`
- `advisor_review_queue_item_to_dict`
- `validate_advisor_review_queue_item`
- `get_advisor_prompt_template`
- `advisor_call_mode="local_scan_only"`
- non-authoritative/operator-review semantics
- source-registry/local-scan mapping pattern
- AI-audit redacted/count-only posture

This means the adapter maps toward the existing advisor-review vocabulary instead of inventing a separate execution layer.

Explicitly:

- no parallel advisor queue
- no parallel prompt system
- no parallel audit layer
- no advisor execution path

Advisor-review compatibility means shape compatibility for review proposal payloads. It does not mean advisor calls are allowed.

## 4. Plain-Language Interpretation

The adapter turns WESLR's internal corpus status/review artifacts into a redacted, non-authoritative advisor-review-compatible payload.

It does not call an advisor.
It does not call a model.
It does not persist a queue item.
It does not score WESLR.
It does not certify WESLR.
It does not execute corpus cases.
It does not become runtime truth.

The adapter helps an operator inspect whether the internal corpus status/review surface may deserve later advisor-style review under separately approved boundaries.

## 5. Safety Boundaries

This canon explicitly preserves:

- no model calls
- no advisor LLM calls
- no queue persistence
- no runner
- no scoring
- no numeric grading
- no official benchmark/IQ/certification claims
- no protected items
- no answer keys
- no hidden prompts
- no raw private text
- no live web/tool execution requirement
- no solver execution
- no answer-selection arbitration
- no auto-approval
- no auto-implementation
- no `.weslr` state
- no runtime/chat/voice changes

No helper in this lane may imply execution authority, runtime truth, answer correctness, official score status, public benchmark status, certification status, or model/advisor authority.

## 6. Non-Blocking Hardening Notes

The helper review identified these future hardening opportunities. They are not blockers for this canon:

- forbidden field matching is currently mostly exact-match; future refinement may normalize camelCase and suffix variants
- top-level `advisor_prompt_template_id` alignment could be clearer when invalid-case template selection differs internally
- queue persistence indicator aliases could be expanded
- allowed advisor task names should remain explicitly non-executing and redacted-only

These notes may be addressed in a later refinement task. They do not authorize queue persistence, advisor/model calls, runner creation, scoring, or runtime integration.

## 7. Allowed Next Steps

Allowed next steps are non-executing unless separately approved:

- review this canon
- refine adapter validation
- improve template ID alignment
- expand persistence-indicator rejection aliases
- design queue integration only
- design advisor call approval gate only
- add more redacted helper tests

Each allowed next step must preserve redaction, non-execution, non-scoring, non-authoritative semantics, local-scan-only posture, and operator review boundaries.

## 8. Blocked Next Steps

The following are blocked unless separately approved:

- call advisor LLM
- call external model
- persist queue item
- create scoring engine
- create corpus runner
- run official benchmark
- claim official score
- ingest protected items
- store answer keys
- probe hidden prompts
- write `.weslr` corpus state
- runtime chat replacement
- certification/public claim

These remain blocked even when a helper payload validates successfully.

## 9. Anti-Drift Rule

Any future change that interprets the adapter helpers as advisor execution, queue persistence, scoring, official evaluation, certification, runtime authority, or model authority violates this canon unless separately approved by doctrine, tests, release gate, and owner review.

A valid future change must preserve the distinction between a redacted advisor-review-compatible helper payload and an actual advisor/model execution path.
