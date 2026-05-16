# WESLR Internal Corpus to Advisor Review Adapter Design V1

## Status

- `APPROVE_WESLR_INTERNAL_CORPUS_TO_ADVISOR_REVIEW_ADAPTER_DESIGN_V1_ONLY`
- `internal_corpus_to_advisor_review_adapter_design`
- `design_only`
- `redacted_structural_summary_only`
- `reuse_existing_advisor_review_queue`
- `reuse_existing_advisor_prompt_templates`
- `reuse_existing_llm_advisor_mode`
- `reuse_existing_local_scan_advisor_review`
- `reuse_existing_ai_audit_foundation`
- `non_authoritative_review_input_only`
- `advisor_call_allowed = false`
- `model_calls = false`
- `not_runner`
- `not_scoring_engine`
- `not_official_benchmark`
- `not_certification_system`
- `not_runtime_integration`
- `no_parallel_advisor_audit_execution_layer`

This document designs a future redacted, non-authoritative adapter from WESLR internal evaluation corpus status/review artifacts into the existing WESLR advisor-review infrastructure. It does not implement helpers, call advisor LLMs, call external models, create runners, score outputs, persist `.weslr` corpus state, or change runtime/chat/voice behavior.

## 1. Purpose

The adapter should let an operator ask: "Does the internal evaluation corpus status/review surface need advisor-style review?" without exposing raw prompts, protected material, answer keys, hidden prompts, private text, or runtime secrets.

The adapter is design-only in this phase. A future implementation, if separately approved, should convert existing internal corpus summaries into existing advisor-review queue and prompt-template structures. It must not create a new advisor queue, a new advisor prompt system, a new AI-audit layer, or any advisor/model execution path.

## 2. Existing Foundations to Reuse

The future adapter should reuse these existing WESLR foundations:

- `weslr/advisor_review_queue.py`
  - Target queue proposal schema: `AdvisorReviewQueueItem`.
  - Required defaults: `requires_operator_approval=True`, `advisor_call_allowed=False`, `advisor_call_mode="local_scan_only"`, safe `AdvisorReviewQueueSafetyFlags`.
  - Validation rejects answer selection, truth/soundness authority, official score requests, answer-key requests, benchmark-specific tuning, raw benchmark text, secrets/private data, runtime/config mutation, governance override, and automatic external model calls.

- `weslr/advisor_prompt_templates.py`
  - Target prompt-template concepts: provider-neutral templates, redacted structural input requirements, forbidden raw benchmark/answer-key/private/secrets inputs, forbidden answer-selection/truth/scoring/runtime mutation outputs.
  - Candidate task types: `test_suggestion`, `synthetic_example_suggestion`, `gap_taxonomy_review`, `wording_risk_review`, `reasoning_pattern_review`, `architecture_review`.

- `weslr/llm_advisor_mode.py`
  - Target review-record concepts: `AdvisorReviewRecord`, `AdvisorSafetyFlags`, `non_authoritative=True`, `requires_validation=True`, `requires_operator_review=True`, `not_runtime_truth=True`.
  - A design/record target only; no advisor execution is authorized here.

- `weslr/local_scan_advisor_review.py`
  - Reuse local-scan-only posture: one-shot, redacted finding/report concepts; no model calls, no queue persistence, no prompt mutation, no provider activation, no runtime/config changes.

- `weslr/source_registry_review_queue_mapping.py`
  - Reuse the pattern of mapping diagnostic findings into in-memory `AdvisorReviewQueueItem` proposals with redaction, validation, no writes, no model calls, no answer selection, no truth claim, and no official score.

- `weslr/advisor_review_queue_cli.py`
  - Reuse operator-facing constraints for future CLI designs: dry run by default, redacted export, no queue write unless separately approved, no external model call, no runtime change.

- `weslr/advisor_review_queue_persistence.py`
  - Treat persistence as out of scope for this adapter design. If later approved, persistence must use explicit path policy and never imply daemon/model/advisor execution.

- `weslr/ai_audit_test.py` and `weslr/ai_audit_*`
  - Reuse the AI-audit safety posture: redacted/count-only summaries, no protected items, no answer keys, no official score claims, no hidden scoring, no runtime/chat/voice changes, no external model/advisor calls.

- `docs/WESLR_LLM_ADVISOR_MODE_DESIGN_V1.md`
  - Reuse the doctrine that LLMs advise and WESLR decides through governance; advisor output is proposal input, not truth.

- `docs/WESLR_ADVISOR_PROVIDER_REGISTRY_DESIGN_V1.md`
  - Reuse provider-neutral, non-authoritative provider/task-scope language; provider identity and capability are metadata, not authority.

- `docs/WESLR_AI_AUDIT_FOUNDATION_CANON_V1.md`
  - Reuse non-executing, dry-review-only, operator-review infrastructure boundaries.

- `docs/WESLR_INTERNAL_EVALUATION_CORPUS_HELPER_CANON_V1.md`
  - Preserve the rule that `status_bundle_ready` means redacted, non-executing internal review readiness only.

## 3. What Should Be Adapted

The future adapter should consume only existing internal corpus helper outputs:

- internal evaluation corpus status bundle
- dry review cards overview
- corpus summary
- safe examples summary

It should not consume raw case prompts as advisor input. It should not consume full case objects unless validation first strips or ignores prompt-bearing and forbidden fields.

The adapter should map those inputs into existing advisor-review concepts:

- advisor review queue item proposal
- advisor prompt template payload summary
- local scan review finding/report concept
- advisor mode review-record placeholder metadata

The adapter output should remain a proposal artifact. It must not enqueue persistently, call an advisor, render an external prompt for automatic dispatch, or authorize implementation.

## 4. Redaction Model

Allowed structural summaries:

- category coverage
- category counts
- missing categories
- readiness labels
- property counts
- forbidden-property counts
- metadata expectation keys
- safety boundary counts
- invalid case/card counts
- duplicate case-id counts
- allowed next-step names
- blocked next-step names
- safety posture booleans
- non-execution flags
- source helper/module names
- review scope labels

Forbidden content:

- raw prompts
- protected material
- answer keys
- hidden prompts
- raw private text
- official score/IQ/certification claims
- benchmark item IDs
- runtime secrets
- API keys/tokens/config secrets
- `.weslr` runtime/corpus state
- model/advisor outputs
- runner/scoring outputs
- solver execution traces
- answer-selection artifacts

If a proposed adapter input includes forbidden content, future validation must reject or redact it before any queue/template/review-record payload is produced.

## 5. Allowed Advisor Review Behaviors

Advisor review, if later separately approved, may only provide non-authoritative suggestions about:

- corpus coverage gaps
- missing safe categories
- ambiguous taxonomy labels
- wording or clarity risks
- status/review surface readability
- missing safety-boundary checks
- additional safe synthetic examples
- operator-review recommendations

Advisor review must not:

- decide correctness
- score WESLR
- certify WESLR
- approve implementation
- claim truth or soundness
- change runtime behavior
- add cases automatically
- select answers
- use answer keys
- request protected or private material
- treat status data as official evaluation evidence

## 6. Target Existing Schemas

The best target is a combination of existing schemas, not a new parallel layer:

1. Primary target: `AdvisorReviewQueueItem`
   - The adapter should produce an in-memory queue proposal with `suggestion_type` such as `test_coverage_review`, `gap_taxonomy_review`, `style_review`, or `advisor_review`.
   - The proposal should have `source="diagnostic"` or `source="manual_entry"`, depending on invocation context.
   - It must set `advisor_call_allowed=False` and `advisor_call_mode="local_scan_only"`.

2. Prompt-template target: existing `AdvisorPromptTemplate`
   - The adapter should identify a template ID/task type such as `advisor_prompt:test_suggestion`, `advisor_prompt:synthetic_example_suggestion`, `advisor_prompt:gap_taxonomy_review`, or `advisor_prompt:wording_risk_review`.
   - The adapter should pass only redacted structural payloads matching template input requirements.

3. Local-scan target: `LocalScanFinding` / `LocalScanReport` concepts
   - The adapter should mirror local-scan-only semantics: detecting review need and suggesting queue items without calling advisors, persisting queues, or mutating prompts/providers/runtime.

4. Advisor-mode target: `AdvisorReviewRecord` placeholder semantics
   - A future advisor response, if separately approved and performed by another lane, should be normalized into `AdvisorReviewRecord` with `non_authoritative=True`, `requires_validation=True`, `requires_operator_review=True`, and `not_runtime_truth=True`.

5. AI-audit target: AI-audit safety concepts only
   - The adapter should borrow redacted/count-only and no-authority boundaries; it should not create AI-audit findings or reports unless a future AI-audit lane explicitly requests that mapping.

## 7. Future Adapter Output Shape

A future helper may return a JSON-safe in-memory object like:

```json
{
  "adapter_type": "internal_corpus_to_advisor_review_adapter_v1",
  "source_bundle_id": "redacted_or_hash_only",
  "source_schema_version": "internal_evaluation_corpus_status_bundle_v1",
  "review_scope": "internal_corpus_status_and_dry_review_cards",
  "redacted_summary": {
    "readiness_label": "status_bundle_ready",
    "case_count": 19,
    "category_count": 19,
    "missing_category_count": 0,
    "invalid_case_count": 0,
    "invalid_card_count": 0,
    "duplicate_case_id_count": 0,
    "allowed_next_step_count": 5,
    "blocked_next_step_count": 11,
    "safety_posture_true_count": 12
  },
  "advisor_prompt_template_id": "advisor_prompt:gap_taxonomy_review",
  "advisor_review_queue_payload": {
    "suggestion_type": "gap_taxonomy_review",
    "source": "diagnostic",
    "risk_level": "low",
    "requires_operator_approval": true,
    "advisor_call_allowed": false,
    "advisor_call_mode": "local_scan_only",
    "review_status": "pending_review",
    "operator_decision": "pending_review"
  },
  "allowed_advisor_tasks": [
    "test_suggestion",
    "synthetic_example_suggestion",
    "gap_taxonomy_review",
    "wording_risk_review",
    "reasoning_pattern_review"
  ],
  "blocked_advisor_tasks": [
    "answer_selection",
    "truth_authority",
    "official_score_claim",
    "benchmark_specific_tuning",
    "answer_key_use",
    "runtime_mutation",
    "memory_mutation",
    "governance_override"
  ],
  "non_authoritative": true,
  "requires_operator_approval": true,
  "requires_validation": true,
  "not_runtime_truth": true,
  "advisor_call_allowed": false,
  "model_calls": false,
  "safe_to_execute": false,
  "raw_prompts_included": false,
  "answer_keys_included": false,
  "protected_material_included": false,
  "hidden_prompts_included": false,
  "raw_private_text_included": false,
  "writes_performed": false,
  "runner_created": false,
  "scoring_created": false
}
```

This output is a design target, not implemented here.

## 8. Validation Requirements

Future validation must reject or block any adapter input/output containing:

- raw prompts or prompt-like fields
- answer keys
- hidden prompts
- protected material
- raw private text
- benchmark item IDs
- official score, IQ, certification, clinical, psychometric, leaderboard, or public superiority claims
- model-call authorization
- advisor-call authorization
- scoring fields
- execution fields
- runner fields
- answer-selection fields
- solver execution fields
- auto-approval or auto-implementation fields
- runtime/chat/voice mutation fields
- `.weslr` corpus state writes
- queue persistence unless separately approved by the existing persistence lane
- provider activation or prompt mutation requests

Validation should also require:

- `non_authoritative=True`
- `requires_operator_approval=True`
- `requires_validation=True`
- `not_runtime_truth=True`
- `advisor_call_allowed=False`
- `advisor_call_mode="local_scan_only"`
- `model_calls=False`
- `safe_to_execute=False`
- all relevant safety flags false

## 9. Future Test Plan

Future implementation tests should cover:

- maps status bundle to redacted advisor review payload
- maps dry review card overview to structural counts only
- maps missing category signals to `gap_taxonomy_review` or `test_coverage_review`
- maps wording/readability concerns to `wording_risk_review`
- rejects raw prompts
- rejects answer keys
- rejects hidden prompts
- rejects protected material
- rejects raw private text
- rejects benchmark item IDs
- rejects official score/IQ/certification wording
- keeps `advisor_call_allowed=False`
- keeps `advisor_call_mode="local_scan_only"`
- keeps `non_authoritative=True`
- requires operator approval
- requires validation
- keeps `not_runtime_truth=True`
- performs no model calls
- performs no advisor calls
- performs no `.weslr` writes
- creates no runner
- creates no scoring engine
- reuses `AdvisorReviewQueueItem` validation
- reuses advisor prompt template task types
- does not create a parallel queue/template/audit schema
- JSON-safe copy is deep enough to isolate mutation
- rendered summaries remain redacted and count-only

No future unit test should call release gates, spawn subprocess chains, call models, call advisors, write `.weslr` corpus state, or use protected examples.

## 10. Non-Goals

This design does not authorize:

- advisor LLM calls
- external model calls
- corpus runner
- scoring engine
- numeric/pass-fail grading
- official benchmark adapter
- certification/public claim layer
- answer evaluator
- solver execution
- answer-selection arbitration
- protected-item ingestion
- answer-key storage
- hidden-prompt probes
- `.weslr` corpus state
- runtime/chat/voice wiring
- new governance/preflight/proposal loop
- parallel advisor queue
- parallel advisor prompt system
- parallel audit system

## 11. Recommended Future Implementation Task

If this design is accepted, the next implementation task should be:

`IMPLEMENT_WESLR_INTERNAL_CORPUS_TO_ADVISOR_REVIEW_ADAPTER_HELPERS_ONLY`

That task should be helper-only, in-memory-only, redacted/count-only, and explicitly limited to mapping internal corpus status/review summaries into existing advisor-review queue/template structures. It must not call advisors or models, write queue files, create runners, create scoring, or change runtime behavior.

## 12. Anti-Drift Rule

Any future adapter that treats advisor review as truth, score, certification, official evaluation, implementation approval, runtime authority, or answer selection violates this design.

Any future adapter that creates a parallel advisor queue, prompt system, or AI-audit execution layer violates this design.

Any future adapter that sends raw prompts, protected material, answer keys, hidden prompts, private text, benchmark item IDs, runtime secrets, `.weslr` corpus state, or model/advisor outputs as input violates this design.

## Governance Conclusion

The correct future shape is a redacted, non-authoritative, in-memory mapping from internal corpus status/review summaries into existing WESLR advisor-review proposal structures.

The adapter should help an operator decide whether a safe advisor-style review would be useful. It must not perform the advisor review, call a model, score WESLR, certify WESLR, persist queue state, or change runtime behavior.
