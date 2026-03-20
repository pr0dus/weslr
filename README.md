# CircleForge

**CircleForge v0.0.22** is a lightweight persistent agent sandbox for local machines.
Agents act on timed cycles, keep private memory, generate small helper modules, and evolve simple local tooling over time.

## What CircleForge is

CircleForge is a minimal but runnable prototype for:
- persistent coding agents
- 60-second world ticks
- short bounded execution windows
- local-model decisions through Ollama
- fallback behavior when Ollama is unavailable
- sandboxed generated Python
- SQLite-backed world state

It is intentionally small, inspectable, and hackable.

## Core loop

- global tick every **60 seconds**
- each agent gets up to **40 seconds** of effective work budget
- the rest is cooldown / world maintenance
- agents can gather, research, optimize, build modules, or rest

## Current world rules

- no sabotage
- no stealing
- inspect/trade are placeholders in the state model, not full gameplay yet
- no direct web search inside agent turns
- GPU is modeled as a quota field, not a real scheduler

## Requirements

- Python 3.10+
- optional: Ollama on `http://127.0.0.1:11434`
- optional model example: `qwen2.5:3b`

## Quick start

```bash
git clone https://github.com/pr0dus/CircleForge.git
cd CircleForge
chmod +x install.sh run.sh
./install.sh
python3 main.py init --reset --agents 4
python3 main.py tick
python3 main.py show-world
```

## Continuous run

```bash
./run.sh
```

Or with a fixed number of ticks:

```bash
python3 main.py run --ticks 10 --interval 60
```

## Useful commands

```bash
python3 main.py init --reset --agents 5
python3 main.py tick --verbose
python3 main.py show-world
python3 main.py show-agent agent-1
python3 main.py version
```

`show-agent` now includes recent artifact metadata, not just raw files.

## Ollama configuration

```bash
export OLLAMA_HOST=http://127.0.0.1:11434
export OLLAMA_MODEL=qwen2.5:3b
```

If Ollama is offline or the chosen model fails, CircleForge falls back to deterministic local behavior.

## Files

- `main.py` - CLI entrypoint
- `sim.py` - world orchestration and persistence
- `agent_runtime.py` - agent planning, Ollama call, fallback policy
- `sandbox.py` - restricted Python execution helper
- `models.py` - dataclasses for world actions/state
- `config.py` - version and simulation constants
- `install.sh` - tiny setup helper
- `run.sh` - convenience runner
- `world.db` - generated SQLite database
- `agents/` - generated per-agent state

## Status

This is **v0.0.2**: a cleaned-up early release, not a finished game.

What is solid already:
- runnable local simulation
- persistent agent state
- local-model integration
- simple generated module workflow
- inspectable logs and world state

What should come next:
- real inspect and trade actions
- artifact metadata and export candidates
- richer economy / demand signals
- replay dashboard
- packaging for background service use
oard that rewards timely artifacts
- an export queue for promising modules/components
- human review scoring for utility and sellability
- artifact packs grouped by theme, market, or agent lineage
