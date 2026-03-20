# agent-ecosim-v1

Minimal but complete v1 prototype for a persistent world of self-improving coding agents.

## What it does

- Runs a **60-second tick loop**
- Each agent gets up to **40 seconds** to think and act
- Remaining time is cooldown / world maintenance
- Agents have:
  - persistent private memory
  - resources
  - simple reputation
  - inspect/trade cooldown timestamps
  - local modules and artifacts folders
- Uses **Ollama** for decisions if available
- Falls back to a deterministic local policy if Ollama is unavailable
- Executes generated Python in a **restricted sandbox subprocess** with timeout
- Stores world state in **SQLite**

This is intentionally constrained and small so you can test it on a normal PC.

## Requirements

- Python 3.10+
- Optional: Ollama running locally
- Optional model example: `qwen2.5:3b` or similar small local model

## Quick start

```bash
cd agent-ecosim-v1
python main.py init
python main.py tick
python main.py run --ticks 10 --interval 60
```

## Useful commands

```bash
python main.py init --agents 4
python main.py tick
python main.py tick --verbose
python main.py show-world
python main.py show-agent agent-1
python main.py reset
```

## Ollama config

By default the project uses:

- host: `http://127.0.0.1:11434`
- model: `qwen2.5:3b`

Override with environment variables:

```bash
export OLLAMA_HOST=http://127.0.0.1:11434
export OLLAMA_MODEL=qwen2.5:3b
```

If Ollama is offline or the model fails, the sim still runs using fallback decisions.

## World rules in v1

- No sabotage
- No stealing
- Inspect allowed only once per 24h per agent
- Trade allowed only once per 24h per agent
- Search/internet not provided
- GPU is abstracted as a limited quota field, not a real GPU scheduler yet
- Agents mainly optimize their own modules, memory, and resources

## Files

- `main.py` - CLI entrypoint
- `sim.py` - world/tick orchestration
- `agent_runtime.py` - agent planning + fallback policy
- `sandbox.py` - restricted execution runner
- `models.py` - dataclasses and state helpers
- `config.py` - tunable constants
- `world.db` - SQLite state after init (generated, gitignored)
- `agents/` - per-agent folders and generated files (generated, gitignored)

## Notes

This is a **testable v0.0.1 skeleton**, not a finished game.
The point is to validate:

- minute ticks
- persistent agents
- self-improvement through generated helper modules
- resource accounting
- local-model orchestration on a single PC

Once this works, the next step is adding:

- spatial map / regions
- richer trading
- better inspection views
- artifact marketplace
- stricter code permissions
- metrics dashboard

