# CircleForge Opportunity Model

CircleForge should not rely on a human to choose every artifact family up front.

The more interesting target is that entities can:
- notice friction
- research repeated pain
- infer a niche
- propose a buyer/problem pair
- generate an artifact hypothesis
- build toward that niche

## Core principle

The entities should not just code.
They should also help decide **what is worth coding**.

This should happen through world state, memory, reinforcement, decay, and accumulated evidence — not hidden prompt steering.

That means each promising artifact should carry an opportunity hypothesis:
- who it is for
- what repeated pain it addresses
- why existing options are annoying, bloated, expensive, or too broad
- what kind of small tool could win anyway
- how it might be packaged into a narrow paid offer

## Opportunity fields

Artifacts should accumulate fields like:
- `niche_theme`
- `target_user`
- `problem_statement`
- `gap_reason`
- `existing_solution_friction`
- `artifact_hypothesis`
- `offer_hypothesis`
- `delivery_mode_guess`
- `price_band_guess`
- `research_confidence`
- `opportunity_score`

## Opportunity score

This is separate from sellability.

- **Opportunity score** asks whether the niche/idea looks real.
- **Sellability score** asks whether the artifact looks packageable.
- **Validation score / proof signals** ask whether reality agrees.

### Suggested dimensions

| Dimension | Why it matters |
| --- | --- |
| Pain clarity | Is the problem specific and repeated? |
| Buyer specificity | Can we name the likely user? |
| Gap severity | Are existing solutions too annoying, heavy, or broad? |
| Packaging ease | Can this become a small reusable offer? |
| Research confidence | How grounded does the niche hypothesis look? |
| External proof | Has anything in reality supported the idea yet? |

## Desired behavior from entities

Over time, entities should drift toward saying things like:

> Small operators need a dead-simple backup confidence check.
> Existing solutions are too large for the actual problem.
> A small local report or validation tool may win here.

Or:

> Local AI tinkerers repeatedly lose time to config mistakes.
> Existing validators are too generic.
> A tighter local-first sanity checker could be a practical micro-product.

That is the behavior CircleForge should cultivate.

## Narrowness matters

The system should strongly prefer:
- boring useful software
- small scope
- visible output
- local-first usage
- simple install path
- repeat pain over novelty theater

It should avoid drifting toward:
- fake startups
- generic AI platforms
- vague orchestration stories
- artifacts that only make sense inside CircleForge

## Practical v0.0.43 direction

v0.0.43 should begin by:
- attaching opportunity metadata to artifacts
- letting entity action plans include niche/problem hypotheses
- computing an opportunity score alongside sellability
- surfacing niche/problem framing in explain output

This is only the first step.
Later versions should:
- cluster repeated niche signals
- track rejected niches
- compare internal opportunity claims against external evidence
- rank emerging micro-product categories discovered by the entities themselves

## Rejection learning

Opportunity themes should not only strengthen when they seem promising.
They should also weaken when reality pushes back.

That means repeated outcomes like:
- human rejection
- handoff rejection
- repeated revision requests
- persistent low-value artifacts

should reduce a theme's influence over time.

A good system does not just remember success.
It also learns what to stop believing.
