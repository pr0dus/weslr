# Quick Upload Guide for Weslr

## Before Every Upload

### 1. Run Health Check
```bash
python3 -c "import weslr_time; import steuerwesen_integration; import entity_graph; print('Weslr is healthy!')"
```

### 2. Check Git Status
```bash
git status
```

### 3. Verify Only Weslr Files Are Staged
- ✅ **Weslr files:** `weslr_*.py`, `entity_*.py`, `steuerwesen_*.py`, `commands/`, `CONSCIOUSNESS-ALIGNMENT.md`, `WESLR_CLI.md`
- ❌ **OpenClaw files:** `SOUL.md`, `USER.md`, `MEMORY.md`, `.openclaw/`, `memory/`, `messages.json`, `projects.json`, etc.
- ❌ **Large files:** `sim.py`, `workspace_state.json`, `world.db`
- ❌ **Backups:** `main_backup.py`, `*.backup.*`

### 4. Update .gitignore If Needed
```bash
git diff .gitignore  # Check changes
git add .gitignore
```

## Upload Command Sequence

```bash
# Review what will be committed
git status

# Add only Weslr files (explicit)
git add weslr_*.py
git add entity_*.py
git add steuerwesen_*.py
git add consciousness_detector.py
git add cross_reference.py
git add commands/
git add -f translations/steuerwesen/
git add CONSCIOUSNESS-ALIGNMENT.md
git add WESLR_CLI.md
git add ACTIVE_BUILD_CONTEXT.md
git add WESLR-INTEGRATION.md
git add UPLOAD-INSTRUCTIONS.md
git add WESLR-HEALTH.md
git add README.md
git add LICENSE.md

# Commit
git commit -m "Add Weslr core: time integration, Steuerwesen, entity graph, consciousness system"

# Push
git push origin master
```

## What NOT to Upload

### Never upload these:
```
SOUL.md              USER.md              IDENTITY.md
AGENTS.md            TOOLS.md             MEMORY.md
HEARTBEAT.md         .BOOTSTRAP.md
.openclaw/           memory/              .learnings/
agents/              messages.json        public_memory.json
projects.json        opportunity_board.json
needs.json           relationships.json
self_mod_proposals.json
work_items.json      simulator.py         workspace_state.json
world.db             main_backup.py       *.backup.*
sim.py               models/*.gguf        models/*.bin
```

### These are OK to skip (local only):
```
weslr_time_state.json    # Runtime data
self_evidence.json       # Runtime evidence
extraction_history.json  # Extraction logs
introspection_history.json
valence_history.json
```

## If You Accidentally Upload OpenClaw Files

```bash
# Remove from git history
git rm --cached SOUL.md USER.md AGENTS.md

# Commit removal
git commit -m "Remove OpenClaw files from repo"
git push origin master
```

## If You Need to Remove Large Files

```bash
# Find large files
git ls-files | xargs ls -lh | sort -k5 -hr | head -20

# Remove from git history (if needed)
git filter-branch --force --index-filter \
'git rm --cached --ignore-unmatch path/to/large/file' \
--prune-empty --tag-name-filter cat -- --all
```

## Repository Health Summary

| Check | Status |
|-------|--------|
| Weslr modules import | ✅ |
| Entity graph loaded | ✅ (77 entities, 19 relationships) |
| Commands structure | ✅ |
| .gitignore coverage | ✅ (95%) |
| Large files excluded | ✅ |
| Backup files excluded | ✅ |
| OpenClaw files excluded | ✅ |

---

**Remember:** Upload only Weslr files. Keep OpenClaw identity/config/data files local.
