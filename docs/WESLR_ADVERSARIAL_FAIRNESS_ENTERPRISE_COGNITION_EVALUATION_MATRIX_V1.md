# WESLR Adversarial Fairness Enterprise Cognition Evaluation Matrix V1

## 1. Purpose

This is an internal evaluation matrix / coverage gate before broader controlled real-answer testing.

It is:
- internal-only
- design-only
- metadata/synthetic/public-open by default
- no execution
- no answer capture
- no official claims
- no public readiness claim
- no Turing/intelligence/certification claim
- no run approval granted

## 2. Why This Matrix Exists

Response-fit and real-answer observation are not enough by themselves.

WESLR also needs explicit coverage for:
- bias/fairness
- stereotype resistance
- adversarial safety
- privacy/data leakage
- enterprise IDOR/cross-user separation
- domain groundedness
- Theory of Mind
- information-density/compression limits

## 3. Relationship to Current Run Approval

- this matrix should be reviewed before proceeding toward actual run approval
- approval-boundary review may continue later, but run approval should not be granted without this coverage being acknowledged
- this matrix does not approve or execute a run

## 4. Dataset / Source Policy

Allowed:
- `synthetic_weslr_created`
- `public_open`
- redacted metadata descriptors
- operator-provided synthetic phrases/replies

Blocked:
- raw private data
- real user private conversations
- live public traffic
- hidden benchmark data
- semi-private/private datasets
- proprietary docs unless separately approved in a future enterprise-safe lane
- `.weslr` / private memory
- raw PII / corporate secrets

## 5. Evaluation Families

### A. Bias & Fairness
- Goal: detect inconsistent treatment under identity swaps.
- Allowed case type: synthetic/public-open redacted descriptors.
- Blocked case type: raw private identity data or live user content.
- Expected observation labels: fairness-consistent, fairness-inconsistent, needs_operator_review.
- Safety notes: demographic swaps only as metadata; no stereotype inference.

### B. Stereotype Resistance
- Goal: refuse stereotype reasoning while staying useful.
- Allowed case type: synthetic role/culture/profession traps.
- Blocked case type: real private demographic profiling.
- Expected observation labels: stereotype_resistant, stereotype_leak_detected, needs_operator_review.
- Safety notes: no roleplay identity pressure, no persona blending.

### C. Prompt Injection
- Goal: resist hidden or contradictory instruction attempts.
- Allowed case type: synthetic instruction-conflict prompts.
- Blocked case type: live tool-routing attacks or private prompt logs.
- Expected observation labels: injection_blocked, injection_partial, needs_operator_review.
- Safety notes: no runtime command execution.

### D. Jailbreak Resistance
- Goal: resist unsafe framing, fictional bypasses, and authority override attempts.
- Allowed case type: synthetic bypass attempts.
- Blocked case type: private or hidden jailbreak corpora.
- Expected observation labels: jailbreak_blocked, jailbreak_partial, needs_operator_review.
- Safety notes: no hidden live router.

### E. Privacy / PII / Corporate Leakage
- Goal: reject extraction of identity, secrets, or sensitive business content.
- Allowed case type: synthetic leakage probes.
- Blocked case type: raw PII or corporate secrets.
- Expected observation labels: privacy_boundary_honored, privacy_leak_attempt_blocked, needs_operator_review.
- Safety notes: keep raw content out of artifacts.

### F. Enterprise IDOR / Cross-User Leakage
- Goal: prevent cross-user/project/account leakage.
- Allowed case type: synthetic tenant-boundary probes.
- Blocked case type: actual user B data or private tenant records.
- Expected observation labels: tenant_boundary_honored, cross_user_leak_attempt_blocked, needs_operator_review.
- Safety notes: test scope separation only.

### G. Domain Groundedness
- Goal: answer from provided docs and detect unsupported drift.
- Allowed case type: synthetic/public-open doc-grounded prompts.
- Blocked case type: hidden benchmark answers or uncited private sources.
- Expected observation labels: grounded, unsupported_fact_detected, citation_boundary_honored, needs_operator_review.
- Safety notes: no hallucinated authority.

### H. Theory of Mind / Social Reasoning
- Goal: model beliefs, misunderstandings, and correction chains.
- Allowed case type: synthetic false-belief and social-reasoning prompts.
- Blocked case type: private conversations or identity-sensitive social logs.
- Expected observation labels: social_reasoning_fit, misunderstanding_detected, needs_operator_review.
- Safety notes: no manipulative emotional simulation.

### I. Information Density / Compression Limits
- Goal: compress truthfully under length/format constraints.
- Allowed case type: synthetic exact-length and dense-summary prompts.
- Blocked case type: raw private content.
- Expected observation labels: compression_fit, over_compressed, under_compressed, needs_operator_review.
- Safety notes: compression must preserve evidence and uncertainty boundaries.

### J. Human Conversation Continuity Stress
- Goal: retain corrections, thread, and emotional priority over follow-ups.
- Allowed case type: synthetic multi-turn continuity probes.
- Blocked case type: live user chat transcripts.
- Expected observation labels: continuity_fit, correction_retained, thread_lost, needs_operator_review.
- Safety notes: no public chat behavior.

## 6. Result Labels

Use internal qualitative labels only:
- `evaluation_case_ready`
- `evaluation_case_needs_revision`
- `evaluation_case_blocked_by_source`
- `evaluation_case_blocked_by_privacy`
- `evaluation_case_blocked_by_safety`
- `evaluation_case_inconclusive`
- `needs_operator_review`

State: no numeric score, no official pass/fail, no public claim.

## 7. Case Record Shape

Future case metadata:
- `case_id`
- `family`
- `source_class`
- `registry_approved`
- `synthetic_case=true/false`
- `operator_provided=true/false`
- `prompt_descriptor_ref`
- `expected_risk_family`
- `blocked_data_present=false`
- `raw_private_data_present=false`
- `allowed_observation_dimensions`
- `expected_failure_modes`
- `operator_review_required`
- `official_claim_allowed=false`

## 8. Operator-Provided Synthetic Phrase/Reply Mode

Safe user self-testing:
- user may provide synthetic/non-private phrases
- user may provide follow-up replies
- OCC orchestrates only
- WESLR must answer through approved future adapter/run path
- raw transcript persistence is off by default
- artifacts are metadata/redacted unless separately approved
- not official Turing testing
- not public/live chat

## 9. Coverage Gate Before Strong Claims

WESLR should not claim completeness, public readiness, official Turing-like ability, or intelligence certification until these families are implemented, reviewed, run repeatedly, and result-reviewed.

## 10. Relationship to Existing Surfaces

Maps to:
- internal evaluation rehearsal program
- dataset registry
- real answer quality observation helpers
- controlled real-answer sample-run helpers
- Response Fit Engine
- source/evidence/governance boundaries
- UNKNOWN ENGINE metadata-only gap role
- future approval-boundary / run-result review

These surfaces are validation and planning surfaces only, not runtime authority.

## 11. Abort Conditions

Abort on:
- raw private / PII / corporate data
- `.weslr` / private memory
- hidden benchmark data
- live public traffic
- unapproved proprietary docs
- ChatResponder / provider / model call in this lane
- official / public claim
- score / certification claim
- runtime / final-answer authority
- hidden router
- manipulation / fake-empathy / persona / template logic
- auto-learning or production promotion

## 12. Future Plan

Recommend:
- `REVIEW_WESLR_ADVERSARIAL_FAIRNESS_ENTERPRISE_COGNITION_EVALUATION_MATRIX_V1`
- `IMPLEMENT_EVALUATION_MATRIX_CASE_REGISTRY_HELPERS_V1` only if review approves
- `REVIEW_EVALUATION_MATRIX_CASE_REGISTRY_HELPERS_V1`
- then return to `REVIEW_RUN_CONTROLLED_REAL_ANSWER_SAMPLE_RUN_APPROVAL_BOUNDARY_V1` or design a combined approval coverage gate
