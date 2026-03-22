# CircleForge

> A local agent research sandbox that incubates small, reusable software artifacts and ranks them by usefulness, external legibility, and sellability.

**CircleForge v0.0.72** is evolving from a local agent research sandbox into a local self-evolving communicator entity with internal minds, persistent memory, intention, and world-driven behavior.
Agents act on timed cycles, keep private memory, generate helper modules, annotate artifacts, surface promising outputs through queues and review, derive demand signals from recent friction, score and rank coherent artifact packs for human curation, estimate commercial readiness and sellability, provide operator-friendly browsing and explanations, generate stronger export bundles and handoff-ready pack wrappers, attach category-aware publishing templates and delivery-mode recommendations, incorporate proof signals from reuse and review history, track external validation outcomes, attach niche/opportunity hypotheses to artifacts, and now begin clustering opportunity themes into more stable emerging niche families.

CircleForge is aimed at producing small reusable tools that humans can inspect, package, validate, and potentially sell — not just internally interesting simulation artifacts. The longer-term goal is for entities to help define what is worth building by spotting gaps, proposing niches, and shaping artifacts around them.

**Feedback and testers are welcome.** If you want to give advice, critique the direction, or try the project, see the community drafts and issue templates in [`docs/community`](docs/community) and [`.github/ISSUE_TEMPLATE`](.github/ISSUE_TEMPLATE).

Live GitHub discussion:
- <https://github.com/pr0dus/CircleForge/discussions/2>

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
- clickable dashboard drill-down navigation
- persistent dashboard event log
- lightweight dashboard auto-refresh/watch loop
- explainability split between internal strength and external proof
- pack offer brief generation and weak-proof pack reporting

## New in v0.0.42

- external validation state tracked per artifact
- real usage, buyer-fit, acceptance, rejection, and revision outcomes
- validation-aware monetization scoring
- CLI support for recording external validation events
- stronger bridge from internal evidence to real-world fit

## Installation

### Requirements

Minimum:
- Linux, macOS, or another environment with Bash and `python3`
- Python 3.10+ recommended

Optional but recommended:
- **Ollama** for local model-backed decisions
  - default expected endpoint: `http://127.0.0.1:11434`
  - default model in config: `qwen2.5:3b`
- Git, if you want versioned local workflows

Current runtime/storage used by CircleForge:
- SQLite via Python standard library (`sqlite3`)
- JSON files for queues, dashboard state, event log, offers, and opportunity state

At the moment, CircleForge does **not** depend on a Python package requirements file for the core local flow.
It mainly uses the Python standard library.

### Quick install

```bash
git clone https://github.com/pr0dus/CircleForge.git
cd CircleForge
python3 main.py version
./run.sh setup
```

### Optional local model setup (Ollama)

If you want model-backed local decisions instead of fallback-only behavior:

```bash
# install Ollama separately first
ollama pull qwen2.5:3b
```

If you use a different host or model, set environment variables before running CircleForge:

```bash
export OLLAMA_HOST=http://127.0.0.1:11434
export OLLAMA_MODEL=qwen2.5:3b
```

### First run

The easiest way to test CircleForge now is the guided setup:

```bash
./run.sh setup
```

(`python3 main.py setup` still works too.)

It will ask:
- how many agents to create
- how many ticks to run
- tick interval in seconds
- dashboard auto-refresh seconds
- whether to serve the dashboard on your LAN
- which LAN port to use

For tick count, you can use:
- a positive number like `10`
- `0` for infinite mode
- `inf`, `infinite`, or `forever` during the interactive prompt

After setup finishes, CircleForge can start a small HTTP server for the dashboard and prints the exact LAN address to open in your browser, for example:
- `http://192.168.1.50:8008/`
- `http://127.0.0.1:8008/`

If you choose not to serve it over LAN, it still prints the file-based fallback:
- `/full/path/to/CircleForge/dashboard/index.html`
- `file:///full/path/to/CircleForge/dashboard/index.html`

If you prefer the manual flow instead:

```bash
python3 main.py init --reset --agents 4
python3 main.py run --ticks 10 --interval 0
python3 main.py show-world
python3 main.py dashboard --refresh 5
```

Then open:
- `dashboard/index.html`

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
python3 main.py dashboard
python3 main.py dashboard --refresh 5
python3 main.py dashboard --watch --interval 10
./run.sh setup
./run.sh setup --agents 6 --ticks 20 --interval 0 --refresh 5 --serve --port 8008
./run.sh setup --agents 4 --ticks 0 --interval 60 --refresh 5 --serve --port 8008
./run.sh serve --port 8008
python3 main.py setup
python3 main.py offer <pack-name>
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

## New in v0.0.52

- clickable dashboard navigation and artifact detail views
- persistent event log plus lightweight live dashboard refresh/watch mode
- explain output now separates internal strength, external proof, risks, and next actions
- pack offer brief generation added with weak-proof pack reporting
- JSON read/write path hardened for runtime files via blank-file tolerance and atomic writes

## New in v0.0.53

- artifact substance analysis added for generated modules and notes
- thin artifacts now receive explicit penalties instead of coasting on strong metadata alone
- description-to-artifact mismatch now reduces human-facing quality, commercial readiness, and sellability
- explainability now flags artifacts whose framing outruns their underlying payload

## Planning docs

- [`V0.1.md`](V0.1.md) — practical pre-v0.1 milestone definition
- [`CORE-IDENTITY.md`](CORE-IDENTITY.md) — the decisive statement of what CircleForge now is and is not
- [`V0.2-GRAND-VISION.md`](V0.2-GRAND-VISION.md) — richer long-term direction
- [`WORLD-MODEL.md`](WORLD-MODEL.md) — canonical world object model
- [`SELF-MODIFICATION.md`](SELF-MODIFICATION.md) — safe self-inspection and self-change design
- [`AGENT-TIME.md`](AGENT-TIME.md) — per-agent cadence and wake model

Current early implementation surface:
- `python3 main.py communicator`
- `python3 main.py world-objects needs`
- `python3 main.py world-objects messages`
- `python3 main.py world-objects public-memory`
- `python3 main.py world-objects projects`
- `python3 main.py world-objects relationships`
- `python3 main.py world-objects self-mod-proposals`
- `python3 main.py world-objects work-items`
- soft per-agent cadence via `next_due_tick`, `wake_reason`, and `cadence_interval`
- protected self-edit boundary for core files and human-safety rules
- proposal-only self-modification layer for repeated friction
- first communicator state with internal proposal/integration loop
- communicator intent continuity and curiosity-driven wake pressure
- disagreement-aware communicator decisions with inspect-first / reconsider / defer behavior
- explicit intention state: pursuit, unresolved question, curiosity target, attraction bias, avoidance bias
- unresolved-question mechanism now drives waking and inspect/research continuation
- question lineage with simple resolution / successor-question chaining
- communicator questions now sync into public memory, needs, inquiry work-items, and experiments
- running experiments now feed back into waking, proposal scoring, pursuit focus, inspect/research pressure, and social trust/caution

## What should come next

Near-term:
- move from static dashboard guidance toward operator-triggered workflows and replay views
- deepen artifact/pack detail pages with proof timelines and offer histories
- tighten the path from validated packs into stronger v0.1-ready product candidates

Longer-term:
- evolve from an artifact incubator toward a richer needs/memory/project world
- strengthen the visible communicator identity over the internal agent substrate
- add explicit intention, curiosity, and internal agreement/disagreement loops
- add self-observation and safe self-modification loops
- move from one global tick toward per-agent cadence and wake conditions
