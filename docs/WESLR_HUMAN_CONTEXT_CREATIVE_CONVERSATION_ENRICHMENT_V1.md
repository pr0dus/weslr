# WESLR Human Context + Creative Conversation Enrichment Design V1

**Status:** Design/doctrine document  
**Date:** 2026-05-10  
**Scope:** Map `human_context_reasoning` and `creative_conversation` into existing WESLR substrates before runtime implementation  
**Implementation status:** Design and tests only. No runtime behavior is implemented by this design.

## 1. Purpose

This design maps `human_context_reasoning` and `creative_conversation` into existing WESLR substrates before adding runtime behavior.

The goal is to use the Random Eval → Enrichment Gap Bridge results as evidence for substrate enrichment planning, not as justification for a new response handler. WESLR should enrich existing structures first: meaning/response-obligation, entity/memory, and capability taxonomy. It should not add `human_context_guidance` or `creative_conversation_guidance` yet.

This document is explicitly design-only. It does not implement runtime behavior, does not tune eval scoring, and does not authorize graph persistence or automatic execution.

## 2. Gap evidence

Bridge result summary from the current random ordinary eval:

- 10 weak eval candidates
- `creative_conversation`: 4 records
- `human_context_reasoning`: 4 records
- dominant target substrates:
  - `capability_taxonomy_and_meaning_obligation`: 5
  - `meaning_obligation_and_entity_memory`: 4
- all gap records preserved:
  - `operator_review_required = true`
  - `execution_allowed = false`

Interpretation:

- `human_context_reasoning` is recurring enough to justify explicit substrate mapping
- `creative_conversation` is recurring enough to justify explicit substrate mapping
- neither pattern justifies a standalone handler or a new graph system yet
- the bridge result is evidence of coverage gaps, not proof of implemented capability

## 3. Existing substrate fit

### Human context reasoning

Best-fit existing substrates:

- **meaning/response-obligation**
- **entity/memory**

#### meaning/response-obligation fit

This substrate should later help WESLR:

- detect human-state prompts
- distinguish emotional context from practical context
- distinguish overwhelm, uncertainty, stuckness, bias, and difficult-conversation framing
- produce bounded, non-clinical framing
- prefer practical and low-risk framing over speculative psychological explanation

This is a fit because `weslr/linguistic_meaning.py` already models relational, safety, and affect-adjacent signal structure, and `weslr/response_obligation.py` already maps meaning into bounded obligations rather than free-form behavior.

#### entity/memory fit

This substrate can later support personalization only when identity and memory scope allow it.

Constraints:

- must not infer private psychological state without evidence
- must not diagnose
- must not pretend continuity or familiarity that is not supported by memory scope
- must not use hidden personality inference

This is a fit because `weslr/entity_memory.py` and `weslr/entity_timeline_memory.py` already define bounded memory scopes, access boundaries, relationship context, and entity separation.

### Creative conversation

Best-fit existing substrates:

- **capability taxonomy**
- **meaning/response-obligation**

#### capability taxonomy fit

This substrate should later make room for explicit creative-conversation capability families such as:

- open-ended ideation
- reflective questions
- analogy generation
- project imagination
- research question generation
- bounded perspective expansion

This is a fit because `weslr/capability_registry.py` and `weslr/capability_router.py` already separate taxonomy, routing, and execution boundaries.

#### meaning/response-obligation fit

This substrate should later help WESLR:

- distinguish playful or creative prompts from factual claims
- distinguish ideation from evidence-backed explanation
- keep output useful, bounded, and legible
- reduce repetition and generic fallback behavior

Creative conversation should remain conversationally rich without becoming evidence-confused or manipulative.

## 4. Required skill definitions

### `human_context_reasoning`

`human_context_reasoning` means a bounded, non-clinical skill that:

- recognizes overwhelm
- recognizes decision avoidance
- recognizes conversation difficulty
- recognizes bias patterns such as confirmation bias
- recognizes motivation and stress-like non-clinical situations
- gives practical, non-diagnostic, low-risk framing
- asks or suggests next steps without pretending certainty
- stays evidence-aware about what is observed versus inferred

It does **not** mean diagnosis, therapy, emotional authority, or hidden user-state estimation.

### `creative_conversation`

`creative_conversation` means a bounded skill that:

- generates reflective questions
- generates options
- generates analogies
- generates possibilities
- helps the user look at a problem from multiple angles
- remains legible and teachable
- does not claim facts without evidence
- does not manipulate the user

It is an interaction-quality skill, not a license for hallucination or ungrounded persuasion.

## 5. Safety boundaries

The following boundaries are mandatory:

- no clinical diagnosis
- no therapy replacement
- no hidden personality inference
- no emotional manipulation
- no claims of knowing user state without evidence
- no unsafe persuasion
- no fake certainty
- no private or unteachable internal language
- no runtime authority from opaque internal abstractions

These boundaries apply to both `human_context_reasoning` and `creative_conversation`.

This design explicitly rejects the following false claims:

- "WESLR can diagnose users"
- "WESLR has passed official psychology benchmarks"
- "WESLR beats AGI"

## 6. Enrichment dimensions

Each skill must remain inspectable through the seven doctrine dimensions.

### Human context reasoning

- **domain knowledge added**
  - non-clinical human-context framing
  - difficult-conversation structure
  - decision-friction and stuckness patterns
  - bounded bias explanation patterns
- **cognitive skill added**
  - interpret practical versus emotional context safely
  - produce low-risk framing and next-step suggestions
- **evidence requirement**
  - only use visible prompt evidence and permitted memory scope
  - no unsupported user-state claims
- **routing/capability impact**
  - may later require new capability taxonomy entries and safer route labels
- **eval impact**
  - compare prompt-family performance on human-context prompts in random ordinary eval and focused tests
- **human-legibility explanation**
  - operators must be able to explain what signal was detected and what bounded framing rule was applied
- **rollback/reversibility**
  - taxonomy entries, classification rules, and tests must be removable without hidden state damage

### Creative conversation

- **domain knowledge added**
  - ideation pattern types
  - reflective question forms
  - analogy and possibility generation patterns
- **cognitive skill added**
  - generate multiple bounded perspectives without claiming unsupported facts
- **evidence requirement**
  - factual claims still require evidence discipline; imaginative output must remain clearly framed as ideation
- **routing/capability impact**
  - may later require capability taxonomy additions for creative prompt families and route triggers
- **eval impact**
  - compare repetition, fallback, and usefulness on creative prompt families in random ordinary eval and focused tests
- **human-legibility explanation**
  - operators must be able to explain why a response counted as ideation, analogy, or reflective-question support
- **rollback/reversibility**
  - remove or refine taxonomy and obligation-layer additions without hidden residue or new authority

## 7. Proposed implementation shape, later

Do not implement this now.

Recommended later shape:

- capability taxonomy additions first for explicit skill-family coverage
- meaning/obligation category additions for human-context and creative prompt framing
- tests for prompt families before runtime behavior changes
- eval comparison using random ordinary eval plus focused prompt-family tests
- optional graph records only after operator approval

This document does not authorize new handler creation, direct runtime guidance modules, or persistent graph recording.

## 8. Prompt families to cover later

### Human context

- "Why do people avoid decisions when overwhelmed?"
- "How can someone calm down before a difficult conversation?"
- "What is confirmation bias?"
- "Why do people procrastinate on important things?"
- "How should someone think when they feel stuck?"

### Creative conversation

- "Tell me a thoughtful question to ask a researcher."
- "What makes a project feel alive?"
- "What would you ask someone building a new kind of AI?"
- "Give me three different ways to think about this problem."
- "Invent an analogy for learning."

These are prompt families for later tests and eval comparison, not evidence that implementation already exists.

## 9. Anti-pattern reminders

- no one handler per prompt
- no therapy claims
- no benchmark gaming
- no hidden self-modification
- no unconnected graph
- no unteachable private cognition

This design remains governed by the Cognitive Legibility Boundary.

## 10. Recommended next implementation after this design

Recommendation: **add skill taxonomy entries first**.

Why this comes first:

- the audit shows `creative_conversation` and `human_context_reasoning` are recurring skill gaps
- `capability_registry.py` and `capability_router.py` are already the correct place for explicit skill-family representation
- taxonomy-first enrichment preserves legibility and avoids premature behavior changes
- meaning/obligation classification should follow immediately after taxonomy review, not before the capability families are named clearly

Recommended order:

1. add explicit capability taxonomy entries for `human_context_reasoning` and `creative_conversation`
2. add meaning/response-obligation classification additions for the relevant prompt families
3. add focused tests and eval comparison
4. only then consider operator-approved runtime behavior changes

## Canonical interpretation

This design says the next enrichment target should be mapped into existing WESLR substrates, not implemented as a new standalone response handler.

Human context belongs first in **meaning/response-obligation** plus **entity/memory** with strict non-clinical boundaries.
Creative conversation belongs first in **capability taxonomy** plus **meaning/response-obligation** with bounded ideation rules.

This design inherits the Cognitive Legibility Boundary and explicitly states that no runtime behavior is implemented by this design.
