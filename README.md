# CircleForge

**CircleForge v0.0.40** is a lightweight persistent local agent research sandbox and artifact incubator.
Agents act on timed cycles, keep private memory, generate helper modules, annotate artifacts, surface promising outputs through queues and review, derive demand signals from recent friction, score and rank coherent artifact packs for human curation, estimate commercial readiness and sellability, provide operator-friendly browsing and explanations, generate stronger export bundles and handoff-ready pack wrappers, and now attach category-aware publishing templates and delivery-mode recommendations.

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

## New in v0.0.40

- category-specific wrapper copy for key families like observability, status pages, packaging, and local-ai-ops
- delivery-mode recommendations for artifacts and packs
- richer handoff files with buyer problem, install steps, and delivery checklist
- stronger bridge from ranked outputs to category-shaped offers
- more practical packaging for client work or small digital products

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
python3 main.py category approve <name>
python3 main.py category retire <name>
python3 main.py category revive <name>
python3 main.py version
```

## What should come next

- replay/dashboard views built around curated artifacts rather than raw simulation state
- stronger proof signals from real reuse and human approval outcomes
- category templates for more concrete offer types
