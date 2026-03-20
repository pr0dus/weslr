# CircleForge

**CircleForge v0.0.31** is a lightweight persistent agent sandbox for local machines.
Agents act on timed cycles, keep private memory, generate helper modules, annotate artifacts, surface promising outputs through queues and review, and now expose basic market-evolution signals from category and export activity.

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

## New in v0.0.31

- market-evolution signals in world output
- category activity summaries
- rising / saturated / dormant category hints
- export pressure signals from current queues and packs

## Useful commands

```bash
python3 main.py init --reset --agents 5
python3 main.py tick --verbose
python3 main.py run --ticks 20 --interval 60
python3 main.py show-world
python3 main.py show-agent agent-1
python3 main.py review <artifact-id> approve --note "looks good"
python3 main.py category approve <name>
python3 main.py category retire <name>
python3 main.py category revive <name>
python3 main.py version
```

## What should come next

- uncategorized clustering and emergent groups
- category merge controls
- richer failure-driven demand signals
- richer pack manifests and install templates
- replay dashboard
