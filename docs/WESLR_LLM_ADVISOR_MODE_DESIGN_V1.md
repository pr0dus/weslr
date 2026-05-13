# WESLR LLM Advisor Mode Design V1

## Status

- design_only
- advisor_mode
- operator_review_required
- execution_allowed = false
- official_score_claimed = false
- no_behavior_change
- no_runtime_integration

## Purpose

Design an advisor lane where external LLMs can suggest improvements while WESLR remains deterministic, governed, and model-assisted rather than model-dependent.

LLM Advisor Mode V1 is a design-only boundary for using external LLMs and cloud models as reviewers of WESLR-owned artifacts. It does not implement advisor mode, route live model calls, change runtime behavior, or authorize any automatic adoption of model output.

## Core Doctrine

- LLMs advise; WESLR decides through governance.
- LLM output is proposal input, not truth.
- LLM output cannot mutate memory, contracts, policies, or runtime behavior directly.
- LLM output must be converted into WESLR-owned artifacts:
  - proposals
  - tests
  - diagnostics
  - design notes
  - helper-rule candidates
  - review summaries

External advisor output is non-authoritative. It may help locate risks, suggest wording, propose tests, or compare design alternatives, but it does not become system state or final reasoning authority without validation and operator review.

## Allowed Advisor Tasks

- architecture review
- failure diagnosis
- style review
- test suggestion
- synthetic example suggestion
- reasoning-pattern review
- gap taxonomy review
- wording-risk review
- alternative design proposals

Allowed tasks must operate on redacted structural summaries, diagnostics, synthetic artifacts, or explicitly approved review packets. Advisor outputs are suggestions for WESLR-owned proposal and validation lanes.

## Forbidden Advisor Tasks

- answer selection
- truth/soundness authority
- official score claim
- benchmark-specific tuning
- answer-key use
- hidden state mutation
- memory overwrite
- policy/governance override
- runtime action without operator approval
- using advisor output as final proof
- extracting/copying model internals

Advisor mode must never decide final answers, claim a proof is true or sound, claim an official score, use answer keys, or become runtime authority.

## Advisor Input Rules

- send only redacted structural summaries by default
- no raw benchmark text by default
- no secrets
- no private user data unless explicitly approved
- no API keys/tokens/config secrets
- prefer diagnostics/counts/schema summaries over raw data

Inputs should be minimized, synthetic where possible, and bounded to the review task. Sensitive content, private user context, raw benchmark material, and configuration secrets are excluded by default.

## Advisor Output Handling

Every advisor response must be stored/treated as:

- non_authoritative
- proposal_candidate
- requires_validation
- requires_operator_review
- not_runtime_truth

Advisor output may be normalized into review records, proposal candidates, test candidates, rubric candidates, diagnostics, or design notes. It cannot mutate WESLR memory, contracts, policies, runtime behavior, or production state directly.

## Multi-Model Review Policy

- use 2–5 advisors for important architecture decisions
- record consensus and disagreements
- do not use long fallback chains
- do not let auto-routing hide which model answered
- failed/time-out advisors are recorded but ignored
- weaker models may be used as noise checks, not authority

Governed reviews should prefer an explicit small advisor set over opaque routing. Model identity, provider, failure, timeout, and disagreement should remain visible in review records.

## Proposed Advisor Record Fields

- advisor_review_id
- advisor_model
- advisor_provider
- task_type
- input_summary_hash
- response_summary
- recommendations
- risks
- disagreements
- consensus_group
- safety_flags
- operator_decision
- accepted_items
- rejected_items
- created_tests
- created_proposals
- created_diagnostics
- timestamp

These fields preserve provenance and separate model suggestions from WESLR-owned decisions.

## Governance Flow

```text
diagnostic/problem → advisor prompt → advisor responses → consensus summary → WESLR proposal/test → validation → operator decision → implementation
```

The governance boundary is explicit: advisor responses enter the proposal/test lane, not runtime truth. Validation and operator decision happen before any implementation.

## Safety Boundaries

- no answer selection
- no truth claim
- no official score
- no benchmark-specific tuning
- no answer keys
- no raw benchmark storage by default
- no hidden symbolic authority
- no automatic memory mutation
- no runtime integration in this phase

LLM Advisor Mode V1 is therefore a controlled design surface, not a live model router, scoring mechanism, or proof authority.

## Connection to Current Synthetic Teaching Lane

Advisor mode can help improve:

- explanation style
- gap taxonomy
- test coverage
- synthetic curriculum expansion
- proof-step pattern mapping

but only as proposal input.

The current internal lane is:

```text
synthetic curriculum → proof step → teaching explanation
```

Advisor mode may review this lane using sanitized synthetic artifacts and diagnostics. It must not turn synthetic teaching artifacts into public/runtime behavior or claim they are final proof-engine outputs.

## Non-Goals

- no implementation in this phase
- no live model router
- no background autonomous advisor loop
- no runtime advisor calls
- no public user-facing behavior
- no OpenClaw config changes
- no model fallback changes

## Future Phases

A. design doc — current
B. advisor review record schema
C. advisor prompt template library
D. offline advisor review runner
E. proposal/test extraction helpers
F. governance integration
G. runtime integration audit much later
H. no official score claim

## Operator Decisions

- APPROVE_LLM_ADVISOR_RECORD_SCHEMA_ONLY
- APPROVE_ADVISOR_PROMPT_TEMPLATE_LIBRARY_ONLY
- REQUEST_REVISION
- REJECT_OR_DEFER
