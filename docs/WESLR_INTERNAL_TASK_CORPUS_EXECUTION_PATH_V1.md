# WESLR Internal Task Corpus Execution Path V1

## 1. Purpose

This path defines how approved task-corpus metadata may be converted into a future controlled internal execution flow.
It is internal-only, non-official, non-public, and non-live.
It closes the next baseline blocker: **no actual task corpus execution path yet**.

## 2. Relationship to Existing Pieces

- **Dataset registry**: source/task approval gate; decides what is allowed to enter the corpus path.
- **Rehearsal runner**: planning, gap mapping, and review-packet metadata layer; it does not execute a corpus itself.
- **Real response executor adapter helpers**: future safe adapter boundary; only metadata-only preflight, call-plan, observation, and packet construction.
- **Baseline review**: confirmed there was no actual corpus execution path yet.
- **Live slice guard**: precedent only; it is not widened by this design.

## 3. Corpus Record Model

Future corpus records are metadata-only.
No raw private, hidden, benchmark, or live user content is stored in this model.

Required fields:
- `task_id`
- `task_family`
- `source_type`
- `registry_record_id`
- `contamination_risk`
- `expected_output_policy`
- `answer_key_policy`
- `task_prompt_redacted_or_synthetic_descriptor`
- `allowed_execution_mode`
- `blocked_execution_labels`
- `operator_review_required`
- `official_claim_allowed = false`
- `public_claim_allowed = false`
- `runtime_authority_allowed = false`
- `voice_authority_allowed = false`
- `unknown_engine_authority_allowed = false`

## 4. Execution Path Phases

A. Registry validation  
B. Corpus record validation  
C. Adapter preflight  
D. Non-executing call-plan construction  
E. Future separately approved controlled execution  
F. Observation normalization  
G. Gap/report packet creation  
H. Operator review

## 5. Allowed Future Execution

May allow later:
- synthetic WESLR-created tasks
- approved internal task descriptors
- metadata-only observation
- qualitative result/failure/gap labels
- predicted vs observed labels
- operator review packets

Must block:
- public/open benchmark use unless separately reviewed
- hidden/semi-private/private datasets
- raw private data
- blocked answer keys
- live user conversations
- `.weslr` / private memory by default
- provider/model/search/advisor unless separately approved
- public score or official claim
- final-answer / public UX / voice authority

## 6. Adapter Integration Rule

Future corpus path may call adapter helpers only after implementation review.
Adapter call plans must remain pending review or blocked unless a later lane explicitly approves controlled execution.
No hidden live router.

## 7. Raw Response / Artifact Policy

- raw response text is not stored by default
- result docs store only safe metadata
- final-answer authority is false
- user-facing prose authority is false
- operator review is required
- unsupported/raw fields must be redacted

## 8. UNKNOWN ENGINE Role

Allowed:
- propose synthetic task variants
- predict likely failure zones
- compare predicted vs observed labels
- compress repeated gap patterns

Forbidden:
- authority
- scoring/certification
- future certainty
- source/license approval
- runtime/live control
- automatic self-modification

## 9. Pressure-Test Carry Forward

Later separate lanes remain required for:
- human conversation evaluator boundary
- long-context / context-pressure tests
- clipboard / max-character pressure tests
- memory-pressure tests
- sealed eval workflow

## 10. Review Criteria

Future review must verify:
- no execution hidden in design
- no benchmark/private/hidden data
- no runtime/live/public/voice authority
- registry and adapter gates are mandatory
- raw persistence blocked by default
- no official claims

## 11. Recommended Next Lane

`REVIEW_WESLR_INTERNAL_TASK_CORPUS_EXECUTION_PATH_V1`
