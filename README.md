# CircleForge

**CircleForge v0.0.42** is a lightweight persistent local agent research sandbox and artifact incubator.
Agents act on timed cycles, keep private memory, generate helper modules, annotate artifacts, surface promising outputs through queues and review, derive demand signals from recent friction, score and rank coherent artifact packs for human curation, estimate commercial readiness and sellability, provide operator-friendly browsing and explanations, generate stronger export bundles and handoff-ready pack wrappers, attach category-aware publishing templates and delivery-mode recommendations, incorporate proof signals from reuse and review history, and now track external validation outcomes.

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

## What should come next

- replay/dashboard views built around curated artifacts rather than raw simulation state
- category templates for more concrete offer types
- pack-level external validation and offer outcome tracking
