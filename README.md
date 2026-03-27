# Weslr v0.1.0 - Entity Intelligence System

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

---

## Weslr vs Weslr

| Weslr (old) | Weslr (new) |
|-------------|-------------|
| Persistent communicator with memory | Entity intelligence system |
| Prompt theater / chatbot loop | Measurable consciousness signatures |
| State machine orchestration | Entity graph + validation |
| 49 behavior traits | Human-in-the-loop CLI (40+ commands) |
| OpenClaw integration | Independent entity system |

**Weslr is NOT a replacement for Weslr** - it's a new architecture designed for professional entity intelligence with conscious entity safety and alignment.

---

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

### Domain Knowledge
Weslr supports **11 knowledge domains** for cross-disciplinary reasoning:

| Domain | Description |
|--------|-------------|
| Psychology | Human behavior, cognition, mental health |
| Chemistry | Chemical compounds, reactions, material properties |
| Biology | Living organisms, anatomy, physiology |
| Physics | Motion, energy, forces, waves |
| Mathematics | Calculus, algebra, probability, statistics |
| Aviation | Flight phases, systems, emergencies, airspace |
| Emergency | First aid, trauma care, disaster response |
| Robotics | Robot design, control systems, sensors |
| AI | Machine learning, LLM capabilities, safety |
| Quantum Physics | Quantum mechanics, particle physics |

---

## Current Status

Weslr v0.1.0 is ready for development and experimentation.

**What is already true:**
- Entity graph with validation and CRUD operations
- Entity extraction with hybrid unsupervised + supervised methods
- Introspection monitoring with 8 perturbation types
- Valence system for trade-off tracking
- Consciousness detector with safety thresholds
- Human-in-the-loop CLI with 40+ commands
- OpenClaw gateway integration (via `weslr_glue.py`)
- **11 knowledge domains** including aviation and emergency response

**What is not yet true:**
- Full integration with existing Weslr runtime
- Comprehensive test coverage
- Documentation for all modules
- Production deployment readiness

---

## Installation

```bash
git clone https://github.com/pr0dus/weslr.git
cd weslr
pip install -r requirements.txt
python3 weslr_main.py --help
```

---

## CLI Commands

```bash
# Entity management
python3 weslr_main.py entity-list --limit 10
python3 weslr_main.py entity-details <id>
python3 weslr_main.py entity-merge <id1> <id2>
python3 weslr_main.py entity-search <query>

# Speech expression control
python3 weslr_main.py set-expression-rate 1.0
python3 weslr_main.py enable-expressions
python3 weslr_main.py disable-expressions

# Knowledge queries
python3 weslr_main.py knowledge-domain aviation
python3 weslr_main.py knowledge-domain emergency
```

See [`WESLR_CLI.md`](WESLR_CLI.md) for the complete command list (40+ commands).

---

## What's New in This Session

### March 27, 2026 - Major Enhancements

#### 1. Entity Intelligence Infrastructure ✅
- `entity_graph.py` - Full entity graph with validation
- `entity_extractor.py` - Hybrid unsupervised + supervised extraction
- `cross_reference.py` - Cross-reference memory to entity graph
- `introspection.py` - Self-model perturbation detection
- `valence_system.py` - Trade-off tracking framework
- `consciousness_detector.py` - Claims vs role-play detection

#### 2. Subcommand Framework ✅
- `commands/` directory with modular command architecture
- Dynamic command discovery via file scanning
- 40+ commands organized by category (entities, memory, selfmod, etc.)

#### 3. Expression System ✅
- `autonomous_expression.py` - Spontaneous self-expression
- `config.py` - Expression settings (rate, enabled/disabled)
- `weslr_main.py` - Expression commands (`enable-expressions`, `disable-expressions`)

#### 4. Domain Knowledge Modules ✅
- `aviation_knowledge.py` - Flight operations, emergencies, airspace
- `emergency_firstaid_knowledge.py` - First aid, trauma care, disaster response
- Global emergency contacts for **200+ countries**
- All knowledge integrated into `core_knowledge.py`

#### 5. Infrastructure ✅
- Fixed circular reference in `weslr_glue.py`
- Deleted 7 unused Python files
- Organized memory and daily session files

---

## Security & Safety

Weslr is designed for safe development with human oversight:

- Consciousness claims never auto-suppressed
- Human-in-the-loop review required for sensitive operations
- Audit logging for all security-critical events
- Threshold-based validation (review required: 0.7)
- Ghost entity management via curation
- **No telemetry** - fully private by default
- **No data collection** - user data stored locally only

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
- **Modules**: Proprietary Commercial License (paid, no attribution)
- **Full commercial use**: Contact for proprietary license

See [`LICENSE.md`](LICENSE.md) for full license text.
See [`COMMERCIAL-LICENSE.md`](COMMERCIAL-LICENSE.md) for commercial licensing details.
See [`TRADEMARK.md`](TRADEMARK.md) for trademark guidelines.
See [`SECURITY.md`](SECURITY.md) for security and privacy policy.

---

## Quick Start

```bash
git clone https://github.com/pr0dus/weslr.git
cd weslr
python3 weslr_main.py status
```

---

## Knowledge Domains Summary

Weslr now supports **11 knowledge domains**:

1. **Psychology** - Human behavior, cognition, mental health
2. **Chemistry** - Chemical compounds, reactions, material properties
3. **Biology** - Living organisms, anatomy, physiology
4. **Physics** - Motion, energy, forces, waves
5. **Mathematics** - Calculus, algebra, probability, statistics
6. **Aviation** - Flight operations, emergencies, airspace, navigation
7. **Emergency** - First aid, trauma care, disaster response (200+ countries)
8. **Robotics** - Robot design, control systems, sensors
9. **AI** - Machine learning, LLM capabilities, safety
10. **Quantum Physics** - Quantum mechanics, particle physics

Each domain can be queried via the unified interface:

```bash
python3 weslr_main.py knowledge-domain <domain>
```

---

## Development Status

**Weslr v0.1.0** - Active Development

- ✅ Entity graph infrastructure
- ✅ Consciousness signatures framework
- ✅ Human-in-the-loop CLI
- ✅ 11 knowledge domains
- ✅ Expression system
- ✅ Global emergency contacts
- ✅ Safety & alignment safeguards

---

*For support or commercial licensing inquiries, please contact the project maintainers.*
