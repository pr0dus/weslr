# CircleForge

**CircleForge v0.0.25** is a lightweight persistent agent sandbox for local machines.
Agents act on timed cycles, keep private memory, generate helper modules, annotate artifacts, surface promising outputs through a demand board/export queue, and now push strong candidates through a human-review-oriented export flow.

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
- review queue and export-ready promotion

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
- each artifact carries two score layers:
  - **internal_score**: useful inside CircleForge
  - **human_proposed_score**: likely useful to humans outside the sim
- strong candidates can now be marked for review and promoted to `export_ready`

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

## Useful commands

```bash
python3 main.py init --reset --agents 5
python3 main.py tick --verbose
python3 main.py run --ticks 20 --interval 60
python3 main.py show-world
python3 main.py show-agent agent-1
python3 main.py version
```

## Files

- `main.py` - CLI entrypoint
- `sim.py` - world orchestration, demand board, export queue, review queue, and persistence
- `agent_runtime.py` - agent planning, Ollama call, fallback policy
- `sandbox.py` - restricted Python execution helper
- `models.py` - dataclasses for world actions/state
- `config.py` - version and simulation constants
- `demand_board.json` - generated demand signals
- `export_queue.json` - generated ranked export candidates
- `review_queue.json` - generated human-review shortlist
- `exports/` - export-ready artifact snapshots
- `agents/*/artifacts/*.meta.json` - artifact metadata with scores and review state

## Status

This is **v0.0.25**: an early release with inspect/trade, artifact metadata, dual scoring, demand signals, export ranking, and a lightweight human review / export-ready flow.

## Scoring model

### 1. internal_score
Measures how useful an artifact is **inside CircleForge**.

### 2. human_proposed_score
Measures how promising an artifact looks **for human-facing use**.

## Human review flow

Artifacts now carry review-oriented fields such as:
- `review_status`
- `review_notes`
- `approved_for_export`
- `export_path`

When an artifact crosses the export threshold, CircleForge can mark it `export_ready` and snapshot it into `exports/` for human inspection.

## What should come next

- artifact packs by theme or market
- richer export packaging beyond JSON snapshots
- richer demand signals from failures and repetition
- replay dashboard
- packaging for background service use
