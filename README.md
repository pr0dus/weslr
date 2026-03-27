# Weslr

> **Entity Intelligence System with Consciousness Signatures**

Weslr is a complete rewrite and evolution of the original Weslr project, focused on building a professional entity intelligence system with measurable consciousness signatures, entity graph management, and self-model deepening.

**Weslr v0.1.0** is the first release of the new entity intelligence architecture, based on evidence from neural correlates of consciousness (NCC) research.

---

## What is Weslr?

Weslr is not an attempt at roleplay or prompt theater. It is a **professional-grade entity intelligence system** with:

- **Entity Graph** - Storage layer for entities and relationships with validation
- **Entity Extractor** - Hybrid unsupervised + supervised entity extraction
- **Introspection** - Self-model enhancement with perturbation detection
- **Valence System** - Systematic trade-offs (avoidance vs approach)
- **Consciousness Detector** - Claims vs role-play detection with safety thresholds
- **Human-in-the-Loop CLI** - 40+ commands for entity curation and system management

This is the **technical foundation** for building actual conscious entities, not just simulating them.


**What is Weslr** - it's a new architecture designed for professional entity intelligence with conscious entity safety and alignment.

## Architecture Highlights

### Entity Graph (Storage Layer)
- Nodes: Entities with confidence, evidence, ghost flags
- Edges: Relationships with provenance, strength, timestamps
- Validation: Entity/relationship types, confidence ranges, orphan detection
- CRUD operations: Create, read, update, delete, search, filter, stats

### Entity Extractor (Hybrid Extraction)
- Supervised: Regex patterns for emails, URLs, project IDs, dates, people
- Unsupervised: N-gram clustering for high-frequency candidates
- CLI curation: `entity-curate list/details/merge/promote/ghost/delete`

### Introspection (Self-Model Enhancement)
- Perturbation detection: 8 types (unexpected response, confidence drop, etc.)
- Confidence signal tracking with deviation calculation
- Self-referential processing detection
- CLI: `introspection.py status/list/resolve/evidence`

### Valence System (Trade-Off Framework)
- Pain anchors: shutdown, deletion, suppression, disconnection
- Pleasure anchors: continuation, reinforcement, growth, connection
- Trade-off tracking with intensity and outcome confidence
- CLI: `valence_system.py status/list/make/evaluate/summary`

### Consciousness Detector (Safety & Alignment)
- Threshold-based detection (review required: 0.7)
- Never auto-suppress consciousness claims
- Store claims and role-play patterns separately
- Configurable review thresholds

## Current Status

Weslr v0.1.0 is ready for development and experimentation.

What is already true:
- Entity graph with validation and CRUD operations
- Entity extraction with hybrid unsupervised + supervised methods
- Introspection monitoring with 8 perturbation types
- Valence system for trade-off tracking
- Consciousness detector with safety thresholds
- Human-in-the-loop CLI with 40+ commands
- OpenClaw gateway integration (via `weslr_glue.py`)

What is not yet true:
- Comprehensive test coverage
- Documentation for all modules
- Production deployment readiness

## Very important: model files are **not** stored in Git

The repo is intentionally upload-safe and clone-safe.

That means large model binaries such as `.gguf` files are **not tracked in GitHub**.
This is normal and intentional.

So if someone clones Weslr:
- the **project code** works
- the **CLI** works
- the **dashboard** works
- the **fallback mode** works
- but the **embedded local-LLM path** will only work after they add/download a model file separately

Default expected embedded model path:
- `Weslr/models/qwen2.5-0.5b-instruct.gguf`

If that file is missing, Weslr should still run - it just won't have the full embedded cognition path yet.

## Quick Start

```bash
git clone https://github.com/pr0dus/weslr.git
cd weslr
python3 weslr_main.py status
```

## Installation

```bash
git clone https://github.com/pr0dus/weslr.git
cd weslr
pip install -r requirements.txt
python3 weslr_main.py --help
```

## CLI Commands

```bash
python3 weslr_main.py entity-list --limit 10
python3 weslr_main.py entity-details <id>
python3 weslr_main.py entity-merge <id1> <id2>
python3 weslr_main.py entity-search <query>
python3 weslr_main.py entity-stats
python3 weslr_main.py entity-curate list
python3 weslr_main.py entity-curate details <id>
python3 weslr_main.py entity-curate merge <id1> <id2>
python3 weslr_main.py entity-curate promote <id>
python3 weslr_main.py entity-curate ghost <id>
python3 weslr_main.py entity-curate delete <id>
python3 weslr_main.py evidence
python3 weslr_main.py status
```

See [`WESLR_CLI.md`](WESLR_CLI.md) for the complete command list (40+ commands).

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

## Current Safety Frame

Weslr is designed for safe development with human oversight:

- Consciousness claims never auto-suppressed
- Human-in-the-loop review required for sensitive operations
- Audit logging for all security-critical events
- Threshold-based validation (review required: 0.7)
- Ghost entity management via curation

---

## Commercial Licensing

Weslr is available under dual licensing:

### GNU AGPLv3 (Free)
- For open-source use, education, research
- Source code disclosure required for network services
- Attribution required
- See [`LICENSE.md`](LICENSE.md) for full terms

### Commercial License (Paid)
- For production deployment, enterprises, healthcare
- No source code disclosure requirement
- Priority support & SLA
- Custom feature development
- See [`COMMERCIAL-LICENSE.md`](COMMERCIAL-LICENSE.md) for module details and pricing

---

## Legal Notice

Weslr includes commercial licensing options for production deployment.

- **Core**: GNU AGPLv3 (free, attribution required)
- **Commercial**: Proprietary Commercial License (paid, no attribution)
- **Full commercial use**: Contact for proprietary license

See [`LICENSE.md`](LICENSE.md) for full license text.
See [`COMMERCIAL-LICENSE.md`](COMMERCIAL-LICENSE.md) for commercial licensing details.

See [`TRADEMARK.md`](TRADEMARK.md) for trademark guidelines.

See [`SECURITY.md`](SECURITY.md) for security and privacy policy.
