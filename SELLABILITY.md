# CircleForge Sellability Model

This document defines a stricter, reality-facing framework for deciding whether an artifact or pack is merely interesting or actually plausible to sell.

## Suggested GitHub description

> A local agent research sandbox that incubates small, reusable software artifacts and ranks them by usefulness, external legibility, and sellability.

## Core principle

CircleForge should not reward abstract cleverness by default.

The system should favor artifacts that are:
- clear
- useful
- easy to install
- easy to explain
- reusable outside the simulation
- plausible to package into a small paid offer

The target outcome is not "the agents wrote code."
The target outcome is:

> the agents produced a small tool, helper, wrapper, monitor, validator, dashboard, or automation that a real human could understand, try, reuse, and potentially pay for.

## Sellable artifact score

Artifacts should be scored from 0 to 100 across six dimensions.

| Dimension | Weight | Question | High-scoring pattern |
| --- | ---: | --- | --- |
| Problem clarity | 20 | Does it solve a specific pain for a specific user? | Named user, named pain, named outcome |
| External legibility | 15 | Can a human immediately understand what it does? | Plain-language summary, sample output, clear README |
| Installability | 20 | Can someone try it quickly without pain? | Local-first, low dependency count, fast setup |
| Reuse potential | 15 | Is it useful in more than one context? | Configurable but focused utility |
| Real utility evidence | 20 | Has it survived contact with reality yet? | Approval, export, reuse, validation, revisions |
| Monetization fit | 10 | Is there a plausible buyer and price band? | Clear buyer, clear delivery mode, low support burden |

### Rating bands

| Score | Meaning |
| ---: | --- |
| 0-29 | Noise / internal artifact only |
| 30-49 | Prototype curiosity |
| 50-64 | Promising internal artifact |
| 65-79 | Credible micro-product candidate |
| 80-100 | Strong sellable candidate |

## Detailed scoring rubric

### 1. Problem clarity (0-20)

High score when the artifact:
- names a target user
- names a concrete pain point
- names a visible outcome
- fits a repeated workflow

Examples:
- "Checks whether Proxmox backup jobs silently failed"
- "Turns JSON logs into a simple local dashboard"
- "Validates Docker Compose files before deploy"

Low score when the artifact is vague:
- framework-shaped
- meta-tooling without a buyer
- only described in internal sandbox terms

Suggested fields:
- `target_user`
- `problem_statement`
- `desired_outcome`
- `use_context`

### 2. External legibility (0-15)

High score when the artifact includes:
- a plain-language one-liner
- clear title
- sample input/output
- readable wrapper or README
- human-facing explanation that avoids CircleForge jargon

Suggested fields:
- `summary`
- `human_readme_present`
- `sample_output_present`
- `demoability_score`

### 3. Installability (0-20)

High score when the artifact is:
- local-first
- low-dependency
- quick to test
- reversible and easy to remove
- not dependent on paid APIs

Suggested fields:
- `setup_steps_estimate`
- `dependency_count`
- `requires_paid_service`
- `local_first`
- `installability_score`

### 4. Reuse potential (0-15)

High score when the artifact:
- solves a repeated boring task
- works across multiple inputs or environments
- is not tightly bound to one machine or one simulation state
- is narrow enough to understand, but broad enough to reuse

Suggested fields:
- `reusable_contexts`
- `config_surface_area`
- `reuse_potential_score`

### 5. Real utility evidence (0-20)

High score when the artifact has:
- been manually reviewed
- been exported
- been reused
- been validated in a real environment
- been revised after rejection and improved

This dimension should become increasingly important over time.
Internal scoring should not outweigh external evidence indefinitely.

Suggested fields:
- `validated_real_world`
- `reuse_count`
- `review_exports`
- `human_approvals`
- `external_validation_events`
- `revision_count`

### 6. Monetization fit (0-10)

High score when the artifact has:
- a plausible buyer type
- a plausible delivery mode
- a plausible low-friction price band
- low expected support burden

Suggested fields:
- `buyer_type_guess`
- `price_band_guess`
- `delivery_mode_guess`
- `support_burden_estimate`
- `monetization_fit_score`

## Hard penalties

These penalties should apply even if the artifact looks strong internally.

| Penalty | Typical deduction | Trigger |
| --- | ---: | --- |
| Sandbox-only dependency | -10 to -25 | Makes sense only inside CircleForge |
| Vague buyer | -10 | No clear user or problem owner |
| Setup pain | -10 to -20 | Too many steps, fragile environment |
| Fake sophistication | -10 to -15 | Sounds advanced, does little |
| Internal jargon | -5 to -10 | Description is not human-facing |

## Bonus signals

These signals are worth rewarding because they correlate with actual sellability.

- saves repeated manual time
- reduces errors
- improves visibility
- easy to demo in under 30 seconds
- produces visible output
- works locally or offline
- output can be handed to another person
- price feels natural in a small range like 10€, 25€, 50€, or 100€

## Concrete v0.0.43 build spec

v0.0.43 should focus on packs and real-world pressure rather than more internal simulation cleverness.

### Primary goal

Make CircleForge better at identifying:
- which packs look sellable internally
- which packs survive external testing
- which packs repeatedly fail for the same reasons

### New pack fields

Add pack-level metadata such as:
- `pack_target_user`
- `pack_problem_theme`
- `pack_problem_clarity_score`
- `pack_external_legibility_score`
- `pack_installability_score`
- `pack_reuse_score`
- `pack_real_utility_score`
- `pack_monetization_fit_score`
- `pack_sellable_score`
- `pack_sellability_reasons`
- `pack_sellability_risks`
- `pack_price_band_guess`
- `pack_delivery_mode_guess`
- `pack_support_burden_estimate`
- `pack_offer_count`
- `pack_accept_count`
- `pack_reject_count`
- `pack_revision_count`

### New pack validation / offer events

Add pack-level actions such as:
- `view`
- `test`
- `export`
- `offer`
- `accept`
- `reject`
- `revise`
- `reuse`

### CLI additions

Add commands shaped like:

```bash
python3 main.py validate-pack <pack-name> <action> --note "tested on a real machine"
python3 main.py offer-pack <pack-name> --buyer "self-hoster" --price-band "25-50" --mode "bundle"
python3 main.py explain <pack-name>
```

### Explain output improvements

For top artifacts and packs, explain output should clearly separate:
- internal heuristic strength
- proof from reuse/review/export history
- proof from external outcomes
- what is still missing before the artifact is truly sellable

### Required reports

Add reports that answer:
- Which packs rank high internally but have weak external proof?
- Which packs have repeated rejection reasons?
- Which packs show strong fit for self-hosters, local AI builders, or small operators?
- Which packs are easiest to package into a small paid offer?

## Prioritized artifact families

CircleForge should favor these sellable families:
- validators
- monitoring tools
- status pages
- reporting tools
- config auditors
- installers
- migration helpers
- backup / failure checkers
- wrappers around painful manual tasks
- small local dashboards

CircleForge should de-emphasize these unless they clearly map to a buyer:
- vague meta-frameworks
- internal-only optimizers
- simulation-specific abstractions
- artifacts that require long explanation before value is visible

## Guidance for GitHub-facing wording

README and repo-facing language should keep emphasizing:
- local-first
- inspectable artifacts
- reusable small tools
- human review and curation
- usefulness outside the simulation
- sellability based on external legibility and evidence

Suggested README phrase:

> CircleForge is a local agent research sandbox aimed at producing small reusable tools that humans can inspect, package, validate, and potentially sell.
