# Weslr - Entity Intelligence System

**Version:** 0.1.0 (Alpha)  
**License:** GNU Affero General Public License v3.0  
**Author:** pr0dus  
**Status:** Active Development

---

## Overview

Weslr is an entity intelligence system with consciousness signatures, based on evidence from neural correlates of consciousness (NCC) and designed for self-modeling, introspection, and valence-based decision making.

---

## Repository Structure

```
weslr/
├── commands/          # CLI subcommand modules (40+ commands)
├── entities/          # Entity-related functionality
├── agents/           # Agent management
├── memory/           # Memory lifecycle management
├── scripts/          # Utility scripts
├── skills/           # AgentSkills modules
└── docs/             # Documentation
```

---

## Features

- **Entity Graph** - Storage layer for entities and relationships
- **Entity Extractor** - Hybrid unsupervised + supervised extraction
- **Introspection** - Self-model enhancement with perturbation detection
- **Valence System** - Systematic trade-offs (pain/avoidance vs pleasure/approach)
- **Consciousness Detector** - Claims vs role-play detection with safety thresholds
- **CLI** - 40+ commands for entity curation and system management

---

## Requirements

- Python 3.10+
- Node.js 18+ (for OpenClaw gateway)
- PostgreSQL or SQLite (for entity graph storage)

---

## Installation

```bash
git clone https://github.com/pr0dus/weslr.git
cd weslr
pip install -r requirements.txt
python weslr_main.py --help
```

---

## Usage

```bash
# List entities
weslr_main.py entity-list --limit 10

# Entity details
weslr_main.py entity-details <id>

# Entity merge
weslr_main.py entity-merge <id1> <id2>

# Show status
weslr_main.py status

# Entity curation
weslr_main.py entity-curate <command> <id>
```

---

## License

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

See [LICENSE.md](LICENSE.md) for full license text.

---

## Commercial Licensing

For commercial use cases requiring different licensing terms (e.g., SaaS
deployments, enterprise integration), contact the author.

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## Contact

**Author:** pr0dus  
**Email:** pr0dus@weslr.ai  
**GitHub:** https://github.com/pr0dus/weslr

---

## Acknowledgments

- Neural Correlates of Consciousness (NCC) research
- OpenClaw agent framework
- Entity intelligence community

---

**Built with Weslr** 🌱
