# CircleForge

**CircleForge v0.0.35** is a lightweight persistent agent sandbox for local machines.
Agents act on timed cycles, keep private memory, generate helper modules, annotate artifacts, surface promising outputs through queues and review, and now derive demand signals from recent friction such as errors, skipped actions, and cooldown hits.

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

## New in v0.0.35

- failure-driven demand signals
- world output now includes `failure_signals`
- recent errors, skips, and cooldowns can influence the demand board
- the sim now surfaces friction, not just artifacts

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

- dashboard/status-page export templates
- replay dashboard
