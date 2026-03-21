# CircleForge

> A local agent research sandbox that incubates small, reusable software artifacts and ranks them by usefulness, external legibility, and sellability.

**CircleForge v0.0.44** is a lightweight persistent local agent research sandbox and artifact incubator.
Agents act on timed cycles, keep private memory, generate helper modules, annotate artifacts, surface promising outputs through queues and review, derive demand signals from recent friction, score and rank coherent artifact packs for human curation, estimate commercial readiness and sellability, provide operator-friendly browsing and explanations, generate stronger export bundles and handoff-ready pack wrappers, attach category-aware publishing templates and delivery-mode recommendations, incorporate proof signals from reuse and review history, track external validation outcomes, attach niche/opportunity hypotheses to artifacts, and now begin clustering opportunity themes into more stable emerging niche families.

CircleForge is aimed at producing small reusable tools that humans can inspect, package, validate, and potentially sell — not just internally interesting simulation artifacts. The longer-term goal is for entities to help define what is worth building by spotting gaps, proposing niches, and shaping artifacts around them.

## Current core

CircleForge currently includes:
- persistent agents
- 60-second ticks
- local-model decisions via Ollama fallback flow
- inspect / trade actions
- artifact metadata
- lifecycle stages
- quality dimensions
- review + export flow
- category governance
- artifact packs
- simple lineage fields
- uncategorized handling
- dormant-category detection
- market-evolution signals
- emergent uncategorized groups
- practical artifact families
- richer export packaging
- failure-driven demand signals
- pack scoring and ranking
- release-candidate packs
- commercial qualification signals
- sellability scoring
- operator browsing and explanations
- publishable pack wrappers and handoff summaries
- category-aware templates and delivery modes
- proof-weighted monetization signals
- external validation outcomes

## New in v0.0.42

- external validation state tracked per artifact
- real usage, buyer-fit, acceptance, rejection, and revision outcomes
- validation-aware monetization scoring
- CLI support for recording external validation events
- stronger bridge from internal evidence to real-world fit

## Useful commands

```bash
python3 main.py init --reset --agents 5
python3 main.py tick --verbose
python3 main.py run --ticks 20 --interval 60
python3 main.py show-world
python3 main.py show-agent agent-1
python3 main.py browse export --limit 5
python3 main.py browse review --limit 5
python3 main.py browse packs --limit 5
python3 main.py explain <artifact-id-or-pack-name>
python3 main.py handoff --limit 5
python3 main.py review <artifact-id> approve --note "looks good"
python3 main.py validate <artifact-id> accept --note "used in a real client flow"
python3 main.py category approve <name>
python3 main.py category retire <name>
python3 main.py category revive <name>
python3 main.py version
```

## Sellability model

A stricter sellability rubric now exists in [`SELLABILITY.md`](SELLABILITY.md).
It defines a 100-point scoring framework based on:
- problem clarity
- external legibility
- installability
- reuse potential
- real utility evidence
- monetization fit

It also defines hard penalties for sandbox-only artifacts, vague buyers, setup pain, fake sophistication, and internal jargon.

## Opportunity model

The first niche-discovery layer now lives in [`OPPORTUNITY.md`](OPPORTUNITY.md).
It defines how entities should begin attaching:
- niche themes
- target users
- problem statements
- gap reasons
- packaging hypotheses
- opportunity scores

to the artifacts they generate.

The current direction is state-driven rather than prompt-driven: entities should drift toward niches through internal opportunity memory, world pressure, reinforcement, decay, and theme clustering.

## New in v0.0.49

- dashboard drill-down sections for top themes and packs
- simple event feed for lifecycle and pack-outcome changes
- dashboard becomes more navigable for human operators

## What should come next

- explain output that separates internal strength from external proof
- reports for high-scoring packs with weak real-world evidence
- clickable links from dashboard into artifacts/packs/explain actions
- replay/dashboard views built around curated artifacts rather than raw simulation state
