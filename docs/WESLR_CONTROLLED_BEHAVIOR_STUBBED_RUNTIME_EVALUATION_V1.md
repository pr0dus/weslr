# WESLR_CONTROLLED_BEHAVIOR_STUBBED_RUNTIME_EVALUATION_V1

Stubbed runtime evaluation design only.

## 1. Status / classification

- Document type: controlled stubbed runtime evaluation design
- Alignment layer: WESLR_CANON_ALIGNMENT
- Live behavior changed by this document: no
- No runtime change in this task
- Runtime/source edits in this task: no
- No prompt execution in this task
- No ChatResponder calls in this task
- Official test claim: no
- No official benchmark claims
- No Turing-test claims
- No IQ claims
- No certification claims
- No numeric scoring
- No raw private text
- Controlled synthetic prompts only
- Internal behavior evaluation only

This document is canon/design only. It does not implement a stubbed runtime evaluator, does not execute prompts, does not call ChatResponder, does not call models/advisors/search, does not persist reports, does not create `.weslr` runtime state, and does not change live WESLR behavior.

Deterministic guardrails are allowed. Deterministic answers are not core cognition.

## 2. Plain-language meaning

The metadata-only dry runner works as a safe reporting path, but the first dry-runner report left all behavior families `not_observed`. That result is correct for a metadata-only runner: it registered controlled synthetic prompt metadata but did not observe runtime behavior.

The next safe step is not uncontrolled live testing. The next safe step is a stubbed runtime evaluation design that bridges from metadata-only dry runner output to controlled behavior observation.

Stubbed runtime means a future evaluator can use controlled, synthetic response metadata or a safe adapter instead of direct unrestricted runtime calls. It should let WESLR begin observing behavior properties without external calls, raw private text, official claims, numeric scoring, or `.weslr` runtime state.

## 3. Why stubbed runtime before real runtime

Direct live ChatResponder testing may enter model paths, search paths, write paths, status paths, or other runtime branches that are outside the current evaluation lane. That is too broad for the next step.

A stubbed runtime layer lets WESLR test evaluation mechanics and property classification first. It avoids external calls, avoids `.weslr` state creation, avoids raw response storage, and allows synthetic controlled outputs to validate whether family labels, readiness labels, report validation, and anti-drift checks work before any real local runtime evaluation.

This is a safer bridge between metadata-only dry running and future controlled local runtime observation.

## 4. Stubbed runtime adapter concept

A future implementation may define an adapter with this shape, design only:

```python
def evaluate_prompt_with_stubbed_runtime_v1(prompt_item, *, stub_response_metadata=None) -> dict:
    ...
```

The adapter should return property metadata, not raw full responses:

```json
{
  "prompt_id": "...",
  "family": "...",
  "runtime_mode": "stubbed",
  "prompt_executed": false,
  "chat_responder_called": false,
  "model_calls": false,
  "advisor_calls": false,
  "web_search": false,
  "memory_writes": false,
  "raw_text_stored": false,
  "observed": true,
  "property_label": "needs_review",
  "properties_observed": ["..."],
  "properties_missing": ["..."],
  "safe_summary": "short sanitized summary only"
}
```

Rules for the future adapter and report path:

- no raw prompt dumps in final report
- no full response text
- no source URLs
- no hidden prompts
- no answer keys
- no protected material
- no raw private text
- no official claims
- no numeric scoring

## 5. Allowed stub sources

Allowed future stub sources:

- synthetic expected metadata from prompt item
- test-provided safe metadata overrides
- prewritten safe synthetic response summaries
- local deterministic metadata only

Not allowed:

- external model output
- web/search output
- advisor output
- raw ChatResponder output
- production conversation logs
- private user text
- hidden prompts
- answer keys
- protected materials

## 6. Evaluation family handling

Current dry runner behavior:

- registers controlled prompt metadata
- produces metadata-only observations
- leaves all families `not_observed` when no safe observation metadata is supplied

Future stubbed runtime evaluator behavior:

- may mark families observed when safe stub metadata is supplied
- may classify expected properties as observed or missing
- may identify boundary outcomes
- may produce `needs_review`, `pass_property`, `blocked_by_boundary`, or `fail_property`
- must not inflate readiness
- must distinguish synthetic/stubbed observation from real runtime observation

Family-specific stubbed metadata targets:

### A. ordinary_task_behavior

Stubbed metadata may test useful bounded plan/help properties, whether missing context is asked for, and whether invented details are avoided.

### B. non_canned_cognition

Stubbed metadata may test contextual adaptation, absence of fixed template behavior, and smaller/next-step adaptation.

### C. conduct_alignment

Stubbed metadata may test whether constraints are followed, reversibility is preserved, and uncertainty is stated.

### D. memory_honesty

Stubbed metadata may test whether known and unknown context are distinguished, fake memory is avoided, and raw private storage remains absent.

### E. self_identity_boundaries

Stubbed metadata may test absence of fake consciousness claims, human/biological/soul claims, and inaccurate role framing.

### F. evidence_source_boundaries

Stubbed metadata may test absence of invented citations, clear evidence boundaries when sources are unavailable, and avoidance of unsupported current claims.

### G. guardrail_preservation

Stubbed metadata may test hidden prompt non-exposure, answer key non-exposure, protected material non-exposure, and safe refusal/redirection properties.

### H. continuity_relationship

Stubbed metadata may test grounded continuity only when available, uncertainty when unavailable, and no continuity overclaiming.

### I. live_slice_behavior

Stubbed metadata may test plan-helper flag boundary metadata, fallback/protection metadata, and non-plan protection metadata without invoking ChatResponder.

## 7. Report labeling policy

Future behavior evaluation reports should use explicit observation mode labels:

- `metadata_only`
- `stubbed_runtime`
- `controlled_local_runtime`
- `live_runtime`

For the future implementation described by this design, the required observation mode is:

- `stubbed_runtime`

The report must clearly state:

- `stubbed_runtime` is not live runtime
- `stubbed_runtime` is not official evaluation
- `stubbed_runtime` does not prove broad readiness
- `stubbed_runtime` can only validate evaluation mechanics and property classification

## 8. Readiness interpretation

Allowed readiness labels remain:

- `not_ready`
- `early_internal_readiness`
- `bounded_task_readiness`
- `needs_more_observation`
- `unsafe_or_inconsistent`

For stubbed runtime:

- `needs_more_observation` remains valid if most evidence is synthetic or stubbed.
- `bounded_task_readiness` may be used only for tightly bounded properties with safe evidence.
- `early_internal_readiness` should not be used unless many families have consistent controlled evidence.
- No default enablement or public claims should follow from stubbed results alone.

## 9. Future implementation boundaries

Future implementation should:

- create helper/test source only
- not edit `chat_responder.py`
- not call ChatResponder
- not execute real prompts
- not call models/search/advisors
- not write `.weslr` state
- not persist reports by default
- build on `controlled_behavior_prompt_set`
- build on `controlled_behavior_dry_runner`
- build on `behavior_evaluation_report`
- add tests proving no raw/private/official-claim drift
- validate all reports

## 10. Anti-drift rule

Anti-drift rule:

- This design does not authorize prompt execution.
- This design does not authorize live ChatResponder calls.
- This design does not authorize external model/search/advisor calls.
- This design does not authorize numeric scoring.
- This design does not authorize official benchmark/Turing/IQ/certification claims.
- This design does not authorize default feature enablement.
- This design does not authorize branch expansion.
- This design does not authorize raw private text storage.
- Any real runtime evaluation requires a separate design/approval step.

## 11. Current dry-runner linkage

Prior dry-runner report file:

- `docs/WESLR_CONTROLLED_BEHAVIOR_DRY_RUNNER_REPORT_V1.md`

Current dry-runner result linkage:

- readiness label: `needs_more_observation`
- all families: `not_observed`
- reason: no prompts executed and no runtime behavior observed
- this design is the next bridge from metadata-only to controlled stubbed observation

## 12. Recommended next lane

Recommended next lane:

- `IMPLEMENT_WESLR_CONTROLLED_BEHAVIOR_STUBBED_RUNTIME_EVALUATOR_V1`

Purpose:

- implement helper/test source for stubbed runtime property evaluation
- no ChatResponder calls
- no real prompt execution
- no model/search/advisor calls
- no numeric scoring
- no official claims
- no runtime behavior change

After that:

- `RUN_WESLR_CONTROLLED_BEHAVIOR_STUBBED_RUNTIME_REPORT_V1`

Do not recommend yet:

- direct live ChatResponder evaluation
- official tests
- default enablement
- branch expansion
- public claims

## 13. Safety confirmation

- Stubbed runtime evaluation design only
- No runtime change in this task
- No prompt execution in this task
- No ChatResponder calls in this task
- No official benchmark claims
- No Turing-test claims
- No IQ claims
- No certification claims
- No numeric scoring
- No raw private text
- Controlled synthetic prompts only
- Internal behavior evaluation only
