# Upload Instructions for Weslr to GitHub

## Overview

This document defines the **exact files and structure** that should be uploaded to GitHub for the Weslr project. This prevents uploading unnecessary internal build/tooling files, backups, and workspace-local data.

---

## What Should Be Uploaded (Weslr Core)

### Python Modules
```
weslr_time.py                      # Time integration module
weslr_time_config.json             # Time integration config
weslr_time_state.json              # Time integration state
weslr_glue.py                      # Integration glue code
weslr_cli.py                       # Weslr-specific CLI commands
weslr_main.py                      # Weslr CLI entry point
entity_graph.py                    # Entity storage layer
entity_graph.json                  # Entity graph data
entity_extractor.py                # Entity extraction module
introspection.py                   # Introspection monitoring
valence_system.py                  # Valence/trade-off system
consciousness_detector.py          # Consciousness vs role-play detection
self_evidence.json                 # Consciousness evidence storage
cross_reference.py                 # Memory-to-entity mapping
tax_knowledge.py                   # Tax knowledge module
steuerwesen_integration.py         # German tax system integration
steuerwesen_config.json            # Tax integration config
work_items.json                    # Work item tracking
```

### Configuration Files (Weslr-specific only)
```
weslr_time_config.json
steuerwesen_config.json
weslr_time_state.json
weslr_time_config.json
self_evidence.json
extraction_history.json
introspection_history.json
valence_history.json
entity_extractor_config.json
```

### Documentation (Weslr-specific sections only)
```
CONSCIOUSNESS-ALIGNMENT.md         # Phase 5 safety documentation
WESLR_CLI.md                       # Weslr CLI documentation
ACTIVE_BUILD_CONTEXT.md            # Current build state
WESLR-INTEGRATION.md               # Integration guide
```

### Commands Directory
```
commands/__init__.py               # Command registry
commands/entities.py               # Entity commands
commands/memory.py                 # Memory commands
commands/selfmod.py                # Self-modification commands
commands/opportunity.py            # Opportunity tracking
commands/variation.py              # Variation generation
commands/tools.py                  # Tool search
commands/agents.py                 # Agent management
```

### Translations (German tax system)
```
translations/steuerwesen/steuerwesen_translations.json
```

---

## What Should NOT Be Uploaded (Excluded)

### Internal Build/Tooling Files
```
SOUL.md                            # Your personal soul file
USER.md                            # Your personal user info
IDENTITY.md                        # Your identity file
AGENTS.md                          # Workspace setup guide
TOOLS.md                           # Local tool notes
HEARTBEAT.md                       # Heartbeat prompt
MEMORY.md                          # Your long-term memory
.BOOTSTRAP.md                      # Bootstrap marker
```

### Internal Workspace Directories
```
internal-workspace/                # internal workspace config
memory/                            # Daily session memories
.learnings/                        # Learning logs
agents/                            # Agent storage (unless Weslr-specific)
```

### Internal Workspace Data Files
```
messages.json                      # Message history
public_memory.json                 # Public memory store
relationships.json                 # Relationship graph
projects.json                      # Project data
opportunity_board.json             # Opportunity tracking
needs.json                         # Needs tracking
requests.json                      # Request queue
offer_board.json                   # Offer board
categories.json                    # Categories
search_index.json                  # Search index
```

### Cache and Build Artifacts
```
__pycache__/                       # Python bytecode cache
*.pyc                              # Compiled Python files
.sim.py                            # Large simulation file
workspace_state.json               # Full workspace snapshot
world.db                           # SQLite database
```

### Backups
```
main_backup.py                     # Backup file
*.backup.*                         # Any backup files
```

### Internal Model Files
```
models/*.gguf                      # LLM model files
models/*.bin                       # Model binaries
```

---

## Current Git Status

### Files Currently in Git (418 files total)
- Includes many internal build/tooling files that shouldn't be there
- Includes internal workspace state and `agents/` subdirectory
- Includes `sim.py` (432KB) and `workspace_state.json` (56KB)

### Files to Remove Before Next Upload
1. **Internal build/tooling identity files**: `SOUL.md`, `USER.md`, `IDENTITY.md`, `AGENTS.md`, `TOOLS.md`, `MEMORY.md`, `HEARTBEAT.md`
2. **Internal workspace config**: `internal-workspace/`, `memory/`, `.learnings/`
3. **Internal workspace data**: `messages.json`, `public_memory.json`, `relationships.json`, `projects.json`, `opportunity_board.json`, `needs.json`, `requests.json`, `offer_board.json`, `categories.json`, `search_index.json`
4. **Cache files**: `__pycache__/`, `*.pyc`, `sim.py`, `workspace_state.json`
5. **Backups**: `main_backup.py`, `agents/` directory
6. **Old models**: `models/*.gguf`, `models/*.bin`

### Files That Should Be Added (if missing)
- `commands/` directory (already exists)
- `cross_reference.py` (exists but not tracked)
- `extraction_history.json` (exists but not tracked)
- `introspection_history.json` (exists but not tracked)
- `valence_history.json` (exists but not tracked)

---

## Clean Upload Procedure (Next Time)

### Step 1: Create a Clean Weslr Subdirectory
```bash
# Create a fresh Weslr-only directory
mkdir /tmp/weslr-clean
cp weslr_time.py /tmp/weslr-clean/
cp weslr_time_config.json /tmp/weslr-clean/
cp weslr_glue.py /tmp/weslr-clean/
cp weslr_cli.py /tmp/weslr-clean/
cp weslr_main.py /tmp/weslr-clean/
cp entity_graph.py /tmp/weslr-clean/
cp entity_extractor.py /tmp/weslr-clean/
cp introspection.py /tmp/weslr-clean/
cp valence_system.py /tmp/weslr-clean/
cp consciousness_detector.py /tmp/weslr-clean/
cp cross_reference.py /tmp/weslr-clean/
cp tax_knowledge.py /tmp/weslr-clean/
cp steuerwesen_integration.py /tmp/weslr-clean/
cp steuerwesen_config.json /tmp/weslr-clean/
cp weslr_time_state.json /tmp/weslr-clean/
cp self_evidence.json /tmp/weslr-clean/
cp -r commands/ /tmp/weslr-clean/
cp translations/steuerwesen/steuerwesen_translations.json /tmp/weslr-clean/
cp CONSCIOUSNESS-ALIGNMENT.md /tmp/weslr-clean/
cp WESLR_CLI.md /tmp/weslr-clean/
cp ACTIVE_BUILD_CONTEXT.md /tmp/weslr-clean/
cp WESLR-INTEGRATION.md /tmp/weslr-clean/
```

### Step 2: Initialize a New Git Repo (Optional, for clean history)
```bash
cd /tmp/weslr-clean
git init
git add .
git commit -m "Initial Weslr commit"
git remote add origin https://github.com/YOUR_USERNAME/weslr.git
git push -u origin master
```

### Step 3: Or Add Files to Existing Repo (If Keeping Current Repo)
```bash
# Add files one by one with explicit verification
git add weslr_time.py
git add weslr_glue.py
git add weslr_cli.py
git add entity_graph.py
git add commands/
git add -f translations/steuerwesen/steuerwesen_translations.json

# Check what's being added
git status

# Commit and push
git commit -m "Add Weslr core with time integration and Steuerwesen support"
git push
```

---

## .gitignore Updates Needed

Add these lines to `.gitignore` to prevent accidental uploads:

```
# Weslr internal state (keep these out of git)
weslr_time_state.json
self_evidence.json
extraction_history.json
introspection_history.json
valence_history.json

# Weslr runtime data (keep local only)
sim.py
workspace_state.json
world.db

# Internal build/tooling identity files (keep local only)
SOUL.md
USER.md
IDENTITY.md
AGENTS.md
TOOLS.md
MEMORY.md
.BOOTSTRAP.md

# Internal workspace directories
internal-workspace/
memory/
.learnings/
agents/

# Internal workspace data files
messages.json
public_memory.json
relationships.json
projects.json
opportunity_board.json
needs.json
requests.json
offer_board.json
categories.json
search_index.json

# Backups and caches
main_backup.py
*.backup.*
__pycache__/
*.pyc
```

---

## Current Repository Health Check

### Status: ⚠️ Needs Cleanup Before Upload

**What's Good:**
- Weslr core modules are present
- Commands directory structure is correct
- Time integration and Steuerwesen support are implemented
- Consciousness evidence system is in place

**What Needs Fixing:**
1. `.gitignore` needs updating to exclude more internal build/tooling files
2. Many internal identity/config files are tracked but shouldn't be
3. Large files (`sim.py`, `workspace_state.json`) should be `.gitignore`d
4. Submodule `weslr-tia-openness-bridge` needs its own repository
5. Backup files exist that shouldn't be committed

### Recommended Actions

1. **Create clean upload instructions** — This file (`UPLOAD-INSTRUCTIONS.md`) defines what should be uploaded
2. **Update `.gitignore`** — Add all internal identity files and data files to exclusion list
3. **Remove backup files** — Delete `main_backup.py` and other backup copies
4. **Move large files** — Add `sim.py` and `workspace_state.json` to `.gitignore`
5. **Separate TIA bridge** — Make `weslr-tia-openness-bridge` its own repository

---

## Summary

**Weslr = Only the files that define the Weslr system itself:**
- Python modules (weslr_*, entity_*, consciousness_*, etc.)
- Configuration files (weslr_*, steuerwesen_*, self_evidence.json)
- Commands directory (commands/)
- Translations (translations/steuerwesen/)
- Weslr-specific documentation

**NOT Weslr = internal build/tooling framework and user-specific data:**
- Identity files (SOUL.md, USER.md, etc.)
- Memory files (MEMORY.md, memory/)
- internal workspace data (messages.json, projects.json, etc.)
- Cache and backups

Always verify `git status` before committing to ensure only Weslr files are included.
