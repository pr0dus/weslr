# CircleForge

**CircleForge v0.0.24** is a lightweight persistent agent sandbox for local machines.
Agents act on timed cycles, keep private memory, generate helper modules, annotate artifacts, and surface promising outputs through a demand board and export queue.

## What CircleForge is

CircleForge is a minimal but runnable prototype for:
- persistent coding agents
- 60-second world ticks
- short bounded execution windows
- local-model decisions through Ollama
- fallback behavior when Ollama is unavailable
- sandboxed generated Python
- SQLite-backed world state
- artifact metadata with dual scoring
- demand tracking and export-candidate surfacing

It is intentionally small, inspectable, and hackable.

## Core loop

- global tick every **60 seconds**
- each agent gets up to **40 seconds** of effective work budget
- the rest is cooldown / world maintenance
- agents can gather, research, optimize, build modules, inspect, trade, or rest

## Current world rules

- no sabotage
- no stealing
- inspect is live with a 24-hour per-agent cooldown
- trade is live with a 24-hour per-agent cooldown
- build/research/optimize actions generate artifact metadata sidecars
- each artifact now carries two score layers:
  - **internal_score**: useful inside CircleForge
  - **human_proposed_score**: likely useful to humans outside the sim

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

`show-agent` includes recent artifact metadata.
`show-world` includes the current demand board and export queue.

## Ollama configuration

```bash
export OLLAMA_HOST=http://127.0.0.1:11434
export OLLAMA_MODEL=qwen2.5:3b
```

If Ollama is offline or the chosen model fails, CircleForge falls back to deterministic local behavior.

## Files

- `main.py` - CLI entrypoint
- `sim.py` - world orchestration, demand board, export queue, and persistence
- `agent_runtime.py` - agent planning, Ollama call, fallback policy
- `sandbox.py` - restricted Python execution helper
- `models.py` - dataclasses for world actions/state
- `config.py` - version and simulation constants
- `install.sh` - tiny setup helper
- `run.sh` - convenience runner
- `world.db` - generated SQLite database
- `demand_board.json` - generated demand signals
- `export_queue.json` - generated ranked export candidates
- `agents/*/artifacts/*.meta.json` - artifact metadata with idea, purpose, destination, future directions, and dual scores

## Status

This is **v0.0.24**: an early release with inspect/trade, artifact metadata, internal scoring, human-proposed scoring, demand signals, and an export queue.

What is solid already:
- runnable local simulation
- persistent agent state
- local-model integration
- inspect and trade actions
- artifact metadata with export hints
- demand board generation
- export candidate ranking

What should come next:
- explicit human review flow
- artifact packs by theme or market
- richer demand signals from failures and repetition
- replay dashboard
- packaging for background service use

## Scoring model

### 1. internal_score
Measures how useful an artifact is **inside CircleForge**.
Current inputs include:
- reusability inside agent workflows
- combination potential
- clarity of metadata
- destination fit for the sim

### 2. human_proposed_score
Measures how promising an artifact looks **for human-facing use**.
Current inputs include:
- exportability
- clarity
- likely usefulness outside the sim
- future development potential

The export queue ranks primarily by `human_proposed_score`, while the demand board can react to both score layers.
