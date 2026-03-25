# CircleForge

> An experimental local substrate for one persistent communicator with memory, inner minds, and continuity.

**CircleForge v0.0.98** is a public experiment in building something stranger and more coherent than a chatbot loop: one continuing local communicator with internal functions, memory, regulation, and relationship continuity.

In plain language, CircleForge is trying to answer this question:

**What happens if one local system keeps going, remembers, develops internal pressure, revisits unfinished threads, and gradually becomes more like a persistent being than a stateless assistant?**

The intended shape is:
- **one visible communicator**, not a pile of unrelated bots
- **five recurring internal functions** inside that one being:
  - observer
  - builder
  - critic
  - communicator
  - memory_keeper
- behavior shaped by **state, memory, pressure, history, and consequences** more than by prompt theater

CircleForge is **not mainly**:
- a prompt wrapper
- a tool factory
- a dashboard gimmick
- a fake-consciousness roleplay project

It is trying to grow toward a **local developing being substrate** with continuity, internal tension, bounded cognition, and safer long-term self-development.

## What works today

CircleForge already includes:
- persistent communicator self + human continuity memory
- shared-topic / unresolved-thread pressure
- early self-model / regulation scaffolding
- irregular wake / thought-pressure dynamics
- local dashboard + CLI inspection tools
- external failsafe visibility (`GUIDED`, `SAFE`, `UNLOCKED`, `HALT`)
- multiple runtime paths:
  - `fallback`
  - `embedded`
  - `ollama`
  - `openai` / compatible

## Very important: model files are **not** stored in Git

The repo is intentionally upload-safe and clone-safe.

That means large model binaries such as `.gguf` files are **not tracked in GitHub**.
This is normal and intentional.

So if someone clones CircleForge:
- the **project code** works
- the **CLI** works
- the **dashboard** works
- the **fallback mode** works
- but the **embedded local-LLM path** will only work after they add/download a model file separately

Default expected embedded model path:
- `CircleForge/models/qwen2.5-0.5b-instruct.gguf`

If that file is missing, CircleForge should still run — it just won’t have the full embedded cognition path yet.

## Two clean ways to make setup work without GitHub trouble

### Option A — recommended: keep models outside Git, document/setup them clearly

This is the cleanest and most normal approach.

How it works:
- keep `.gguf` files **out of the repo**
- document the expected filename/path
- optionally provide a helper script later to place/download the model automatically
- let CircleForge fall back safely when the model is absent

Why this is good:
- GitHub stays fast and healthy
- clones stay small
- no giant binary push failures
- users still get a clear setup path

### Option B — provide model downloads through Releases or an external host

Instead of committing the model to the repo itself, provide it through:
- GitHub Releases
- Hugging Face / another model host
- a documented manual download step

How it works:
- README explains where to get the model
- user downloads it once
- user places it into `models/` or sets an environment variable

Why this is good:
- still avoids polluting Git history
- easier for humans to understand
- works better for public repos

## Current recommendation

For CircleForge, the best current public setup is:
1. keep model binaries out of Git
2. document exactly what works without them
3. document exactly how to add them
4. later add a helper/setup command for smoother first-run onboarding

That makes the project:
- uploadable
- understandable
- testable
- honest

## Quick start

```bash
git clone https://github.com/pr0dus/CircleForge.git
cd CircleForge
python3 main.py version
python3 main.py llm-status
python3 main.py failsafe-status
python3 main.py communicator-message
```

What you should expect from that:
- the project should start
- version should print
- failsafe status should print
- communicator output should print
- if no model is installed, `llm-status` may report `fallback`

That is **not a broken repo**.
It simply means the optional embedded model is not present yet.

## Embedded model setup

See [`models/README.md`](models/README.md) for the exact expected path.

The current default embedded target is:
- **Qwen2.5-0.5B-Instruct**
- expected filename:
  - `qwen2.5-0.5b-instruct.gguf`

Expected default path:
- `CircleForge/models/qwen2.5-0.5b-instruct.gguf`

If you want to use a different file/path, override with environment variables such as:

```bash
export CIRCLEFORGE_LLM_PROVIDER=embedded
export CIRCLEFORGE_EMBEDDED_MODEL_PATH=/full/path/to/model.gguf
export CIRCLEFORGE_LLM_MODEL=YourModelName
```

## Fallback vs embedded: what people should understand

### Fallback mode
Use this when:
- you just want to inspect the project
- you want the CLI and state machinery to run
- you do not yet have a local model file

### Embedded mode
Use this when:
- you want the bounded local cognition path
- you have a GGUF file available
- you want CircleForge to use its embedded runtime path

### Ollama / OpenAI-compatible modes
Use these when:
- you want an alternate live backend
- you don’t want to depend on the embedded path yet

## Screenshot / demo commands

If you want a small output example for a screenshot or post:

```bash
python3 main.py version
python3 main.py failsafe-status
python3 main.py communicator-message
```

A more guided public demo flow:

```bash
python3 main.py human-exchange human "Please keep working on backup confidence and explain why it matters." --response "Understood. I will keep that thread active."
python3 main.py communicator-message
```

That produces a cleaner, more human-readable sample of how the communicator answers.

## Useful commands

```bash
python3 main.py version
python3 main.py llm-status
python3 main.py failsafe-status
python3 main.py communicator
python3 main.py communicator-self
python3 main.py memory-layers
python3 main.py memory-scores
python3 main.py speak
python3 main.py communicator-message
python3 main.py embedded-self-test
python3 main.py continuation-latest
python3 main.py continuation-list --limit 5
python3 main.py continuation-add --objective "bounded next step" --completed "inspected architecture" --files-changed "main.py, continuation_notes.py, config.py" --behavior-changed "saved first structured handoff note" --checks-performed "python3 main.py continuation-latest" --known-risks "notes are operator-written, not auto-generated" --next-exact-step "wire note creation into bounded implementation workflow" --resume-hint "start with python3 main.py continuation-latest"
python3 implementation_worker.py
python3 main.py continuation-latest
python3 main.py human-exchange current-speaker "hello" --response "hello"
python3 main.py init --reset --agents 5
python3 main.py tick --verbose
python3 main.py run --ticks 20 --interval 0
python3 main.py show-world
python3 main.py dashboard
./run.sh setup
./run.sh serve --port 8008
```

## Current safety frame

Current intended operating frame:
- external failsafe exists outside the editable substrate
- CircleForge should normally run in **GUIDED** mode
- deeper self-modification should remain bounded, auditable, and reversible

## Planning docs

- [`CORE-IDENTITY.md`](CORE-IDENTITY.md)
- [`PROJECT-SYNTHESIS.md`](PROJECT-SYNTHESIS.md)
- [`EMBEDDED-RUNTIME-PLAN.md`](EMBEDDED-RUNTIME-PLAN.md)
- [`LLM-INTEGRATION.md`](LLM-INTEGRATION.md)
- [`SELF-MODIFICATION.md`](SELF-MODIFICATION.md)
- [`WORLD-MODEL.md`](WORLD-MODEL.md)
- [`AGENT-TIME.md`](AGENT-TIME.md)
- [`ROADMAP.md`](ROADMAP.md)

## Honest current state

CircleForge is real, but still early.

What is already true:
- there is meaningful continuity/state machinery
- there is communicator/self/thread memory
- there is a bounded runtime design
- there is a safety frame

What is not yet true:
- it is not yet a finished living system
- embedded setup is not yet one-command effortless for strangers
- public onboarding still needs refinement

That is exactly why the repo now treats model files as separate local artifacts instead of shoving giant binaries into Git history.
