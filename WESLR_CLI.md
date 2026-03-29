# Weslr CLI Documentation

## Overview

Weslr is an entity intelligence system with consciousness signatures, built as a modular subcommand framework.

## Quick Start

```bash
python3 weslr_main.py --version
python3 weslr_main.py --help
```

## Available Commands

### Entity Management
- `entity-list [--limit N]` — List entities in the entity graph
- `entity-details <id>` — Show detailed entity information
- `entity-merge <id1> <id2>` — Merge two entities
- `entity-promote <id>` — Promote ghost entity to authoritative
- `entity-search <query>` — Search entities by name or aliases
- `entity-stats` — Show entity graph statistics

### Relationship Management
- `relationship-list [--limit N]` — List relationships
- `relationship-add <source_id> <target_id> [--rel-type] [--strength]` — Add relationship

### Memory Management
- `memory-list [--limit N]` — List memory items
- `memory-show <id>` — Show specific memory item
- `memory-prune [--older-than N]` — Prune old memory items
- `memory-lifecycle` — Show memory lifecycle report
- `memory-pressure` — Show memory pressure status

### Self-Modification
- `selfmod-list [--limit N]` — List self-modification proposals
- `selfmod-show <id>` — Show self-modification proposal
- `selfmod-apply <id>` — Apply self-modification
- `selfmod-rollback <id>` — Rollback self-modification
- `selfmod-status` — Show self-modification status

### Opportunity Management
- `opportunity-list [--limit N]` — List opportunities
- `opportunity-transition <id>` — Transition opportunity
- `opportunity-reject <id>` — Reject opportunity
- `opportunity-cluster` — Cluster opportunities
- `opportunity-revisit <id>` — Mark opportunity for revisit

### Variation Generation
- `variation-list [--limit N]` — List variations
- `variation-generate <theme>` — Generate variations for a theme
- `variation-show <id>` — Show specific variation
- `variation-promote <id>` — Promote variation

### Tool Search
- `tool-search <query>` — Search for tools
- `tool-explain <tool>` — Explain tool usage
- `tool-lookup <query>` — Look up tool usage

### Agent Management
- `agent-list [--limit N]` — List agents
- `agent-details <id>` — Show agent details
- `agent-create <name>` — Create a new agent

## Usage Examples

```bash
# List entities
python3 weslr_main.py entity-list --limit 5

# Search entities
python3 weslr_main.py entity-search "Local-first"

# Show entity details
python3 weslr_main.py entity-details 3b0ab780

# List opportunities
python3 weslr_main.py opportunity-list --limit 3

# Generate variations
python3 weslr_main.py variation-generate "entity_extraction"

# Show entity graph statistics
python3 weslr_main.py entity-stats

# List all self-modification proposals
python3 weslr_main.py selfmod-list --limit 10
```

## Architecture

### Command Modules

Commands are organized into modules under `commands/`:

```
commands/
├── __init__.py       # Command registry with dynamic discovery
├── agents.py         # Agent management (3 commands)
├── entities.py       # Entity/relationship management (8 commands)
├── memory.py         # Memory lifecycle management (5 commands)
├── opportunity.py    # Opportunity management (5 commands)
├── selfmod.py        # Self-modification management (5 commands)
├── tools.py          # Tool search and explanation (3 commands)
├── variation.py      # Variation generation (4 commands)
└── weslr_main.py     # Main CLI entry point
```

### Command Discovery

Commands are discovered automatically:
1. `weslr_main.py` scans `commands/` directory
2. Each module with `register_commands()` function is loaded
3. Subcommands are registered dynamically
4. Commands are executed via `func(args)`

### Benefits

- **Maintainability**: Smaller files (50-150 lines each)
- **Testability**: Each command module tested independently
- **Extensibility**: Easy to add new commands
- **Reusability**: Command modules can be reused in other tools

## Current Status

| Phase | Status | Commands | Result |
|-------|--------|----------|--------|
| Entity Graph | ✅ | 8 | 77 entities, 19 relationships |
| Memory | ✅ | 5 | Lifecycle management |
| Self-Modification | ✅ | 5 | Proposal management |
| Opportunities | ✅ | 5 | Opportunity tracking |
| Variation | ✅ | 4 | Generation framework |
| Tools | ✅ | 3 | Search functionality |
| Agents | ✅ | 3 | Management framework |

**Total Commands:** 40+

## Next Steps

- Integrate remaining commands from `main.py`
- Update documentation
- Create CI/CD pipeline
- Add tests for each command module
