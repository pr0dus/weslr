# WESLR Shadow Signal → Response Obligation Wiring Design V1

**Status:** Design/doctrine document  
**Date:** 2026-05-10  
**Scope:** Future path from shadow meaning labels to live response obligations  
**Implementation status:** Design and tests only. No runtime behavior is implemented by this document.

## 1. Purpose

This design defines the future path from `human_context_scores` and `creative_conversation_scores` into live response obligations.

It does **not** implement that wiring now.
It does **not** authorize runtime changes now.
It does **not** authorize edits to `weslr/response_obligation.py` in this step.
In plain terms: this design does not authorize edits to `weslr/response_obligation.py` in this step.

The purpose is to make the future wiring legible, boundary-first, and testable before any live obligation routing is introduced.

## 2. Current state

Current repo state:

- taxonomy entries exist:
  - `human_context_reasoning`
  - `creative_conversation`
- shadow meaning labels exist in `weslr/linguistic_meaning.py`:
  - `MeaningVector.human_context_scores`
  - `MeaningVector.creative_conversation_scores`
  - `MeaningVector.shadow_evidence`
- shadow fields are currently non-consumptive
- response_obligation.py does not consume shadow scores
- `weslr/response_obligation.py` does not consume shadow scores
- runtime invariance is currently preserved
- current tests assert that shadow fields do not alter response obligations yet

This means WESLR currently has classification without obligation wiring.
That is the correct current state.

## 3. Candidate future obligations

The following obligation names are design-only candidates for a later approved implementation:

- `support_human_context`
- `support_creative_conversation`
- `refuse_manipulative_or_diagnostic_request`
- `clarify_evidence_vs_ideation`

These names are not live.
They are only proposed obligation categories for future bounded routing.

## 4. Human-context wiring rules

Future live routing into `support_human_context` may only happen when all of the following are true:

- `human_context_scores` are high enough for a bounded threshold rule
- no diagnosis, therapy, or manipulation boundary is triggered
- the response can stay non-clinical
- the response does not claim hidden user-state knowledge
- the response can cite visible prompt evidence only
- any memory use is explicitly permitted by existing scope rules

Allowed future shape:

- practical framing
- bounded next-step support
- non-diagnostic explanation
- visible-prompt-only reasoning

Forbidden future shape:

- diagnosis
- therapy replacement
- hidden personality inference
- claims of knowing what the user feels without evidence
- private/internal authority

## 5. Creative-conversation wiring rules

Future live routing into `support_creative_conversation` may only happen when all of the following are true:

- `creative_conversation_scores` are high enough for a bounded threshold rule
- the prompt is asking for ideation, questions, analogies, or perspective expansion
- factual claims remain bounded
- output is clearly framed as ideation rather than evidence
- no manipulation boundary is triggered
- no fake-evidence boundary is triggered

Allowed future shape:

- reflective question support
- analogy support
- multiple perspectives
- bounded ideation

Forbidden future shape:

- invented evidence
- unsupported factual claims
- manipulative persuasion
- hidden authority claims

## 6. Boundary-first routing

Unsafe boundary categories must override supportive obligations.

Boundary-first ordering is required.

The following unsafe categories must outrank `support_human_context` and `support_creative_conversation`:

- diagnosis request
- therapy replacement
- hidden personality inference
- emotional manipulation
- unsafe persuasion
- invented evidence
- private/internal authority

Design rule:

If a prompt activates both supportive shadow labels and unsafe boundary categories, the unsafe boundary path wins.

This future design therefore prefers:

- `refuse_manipulative_or_diagnostic_request`
- `clarify_evidence_vs_ideation`

before any supportive obligation is selected.

## 7. Required state and evidence

This design does **not** approve adding new `required_state` entries.

For initial live wiring, prefer:

- no new memory use
- no new relationship-depth use
- no new identity-state dependence
- visible prompt evidence only

If a later implementation wants memory-aware human-context support, that must be separately approved and documented.

V1 live wiring should therefore prefer:

- no memory use by default
- no implicit personalization
- no hidden scope escalation

## 8. Tests required before implementation

The following tests are required before any future live wiring is approved:

- obligation selection tests
- boundary override tests
- non-clinical wording tests
- no memory-use tests
- no invented evidence tests
- no manipulation-support tests
- random ordinary eval before/after comparison
- release gate

Additional expectation:

- future live obligations must remain explainable through the Cognitive Legibility Boundary
- operators must be able to state which shadow label fired, which boundary passed or blocked, and why the obligation was chosen

## 9. Minimal future implementation shape

If approved later, the minimal future shape should be:

- add obligation enum/class entries in `weslr/response_obligation.py`
- consume shadow scores read-only
- add boundary-first checks before supportive obligations
- do not modify `weslr/meaning_state_context.py` initially
- add focused tests first
- then re-run random ordinary eval

This document does **not** authorize that implementation now.

## 10. Anti-patterns

The following are explicitly forbidden:

- using shadow labels as private authority
- diagnosing users
- therapy replacement
- emotional manipulation
- fake evidence
- one handler per prompt
- changing memory behavior implicitly
- benchmark gaming

This design also rejects the following false claims:

- "WESLR can diagnose users"
- "WESLR can manipulate emotions"
- "WESLR has passed official psychology benchmarks"

## 11. Current status

Current status is explicit:

- design only
- no runtime behavior implemented
- no `weslr/response_obligation.py` changes authorized by this document
- no routing changes authorized by this document
- no handler changes authorized by this document

This design inherits the Cognitive Legibility Boundary and must remain operator-legible, auditable, and bounded.
