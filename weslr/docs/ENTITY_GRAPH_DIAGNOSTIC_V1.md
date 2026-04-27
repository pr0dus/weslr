# WESLR Entity Graph Diagnostic V1

**Date:** 2026-04-27
**Status:** DIAGNOSTIC ONLY — no changes made

---

## SECTION 1 — Scope

Inspected:
- `entity_graph.py` — root-level Python module
- `entity_graph.json` — working directory data file
- `entity_graph.json.bak` — untracked backup with rich data
- Integration points: `cli_external.py`, `state.py`, `interpretation.py`
- Committed HEAD state

---

## SECTION 2 — File Existence and Sizes

| File | Git Status | Size | Entities |
|------|-----------|------|----------|
| `entity_graph.py` | Tracked (HEAD: c4bae55) | 31,138 bytes | N/A (code) |
| `entity_graph.json` | **Untracked** | 149 bytes | **0** (empty `entities: {}`) |
| `entity_graph.json.bak` | **Untracked** | ~4KB | **18 entities** |

---

## SECTION 3 — JSON Validity / Structure

### `entity_graph.json` (working, untracked)
```json
{
  "entities": {},
  "relationships": {},
  "created_at": 1777307869,
  "updated_at": 1777308603,
  "version": "1.0",
  "validation_enabled": true
}
```
- **Valid JSON** ✅
- **0 entities** — completely empty
- No `"software"` type present

### `entity_graph.json.bak` (untracked backup)
- **Valid JSON** ✅
- **18 entities**: `software: 7`, `person: 6`, `concept: 5`
- **7 entities use `type: "software"`** — this type does NOT exist in committed `VALID_ENTITY_TYPES`

---

## SECTION 4 — Module Import Result

### Committed `entity_graph.py` (HEAD)
- **Imports cleanly** when `entity_graph.json` is empty (current working state)
- **Crashes** if loaded with data containing `"software"` type entities:
  ```
  ValueError: Invalid entity type: software
  Entity.from_dict() → Entity.__post_init__() → self.validate()
  ```
- Root cause: `entity_graph.py` bottom-of-file runs `save_entity_graph(get_entity_graph())` on module import. If `entity_graph.json` contains `"software"` entities, `EntityGraph.load()` fails.

### Working `entity_graph.py` (current)
- Hash: `63c76abdb609c81bfdd506cee32898ee` (identical to HEAD per MD5 comparison)
- **`VALID_ENTITY_TYPES` does NOT include `"software"`** — matches HEAD exactly
- Import succeeds because `entity_graph.json` is empty

---

## SECTION 5 — Public API Summary

### Classes
- `Entity` — id, name, type, confidence, aliases, relationships, evidence, is_ghost, metadata
- `Relationship` — id, source_id, target_id, type, strength, provenance
- `EntityGraph` — full CRUD for entities + relationships, search, stats

### Key Functions
- `get_entity_graph()` — singleton loader, uses `ENTITY_GRAPH_PATH`
- `save_entity_graph()` — persists to JSON
- `EntityGraph.load()` / `EntityGraph.save()` — JSON round-trip
- `validate()`, `validate_graph()` — schema enforcement

### Schema Enforcement
- `VALID_ENTITY_TYPES = {"person", "organization", "concept", "event", "object", "location", "project", "principle", "question", "lesson", "semantic-memory", "research", "research_raw", "agent", "memory", "tool"}`
- `"software"` is **not** in this set
- `Entity.validate()` raises `ValueError` for unknown types

---

## SECTION 6 — Write-Paths Found

| Path | Location | Trigger |
|------|----------|---------|
| `EntityGraph.save()` | `entity_graph.py:409` | Called by `save_entity_graph()` |
| `save_entity_graph()` | `entity_graph.py:827` | Called at **module load** (bottom of file) |
| **Module-level init** | `entity_graph.py:837` | `save_entity_graph(get_entity_graph())` — runs on import |

**Critical:** `entity_graph.py` calls `save_entity_graph(get_entity_graph())` at module load time. If `entity_graph.json` doesn't exist or is empty, it writes an empty graph to disk.

---

## SECTION 7 — Integration References

### `interpretation.py`
- **No imports** of `entity_graph` — fully decoupled ✅

### `weslr/cli_external.py`
- Imports `entity_graph` at line 26
- Guards with `entity_graph = None` if import fails
- Used for: `get_all_entities()`, `get_entity_by_id()`, `add_entity()`, `promote_entity()`
- Only active when user runs `entity` CLI commands

### `weslr/state.py`
- Loads `entity_graph.json` via `load_json()` helper
- Converts entities to simplified state format
- Does NOT import the `entity_graph` Python module

### `weslr/commands/entities.py`
- Uses `entity_graph` module for entity CRUD operations

### Other consumers
`cleanup_entities.py`, `cross_reference.py`, `dialogue.py`, `entity_extractor.py`, `main.py`, `self_knowledge.py`, `weslr_cli.py`, `weslr_glue.py`

### Assessment
- **Partially integrated** — used by CLI and some subsystems
- **interpretation.py does NOT depend on it** — extraction handlers unaffected
- **Not used by deterministic handler pathway**

---

## SECTION 8 — Failure Classification

**Category: C — Schema Drift**

The committed `entity_graph.py` does not include `"software"` in `VALID_ENTITY_TYPES`. An untracked backup file (`entity_graph.json.bak`) contains 7 entities with `type: "software"`. If this backup is ever reloaded, the module import crashes.

### Sequence of events (inferred):
1. Historical session created rich entity data (18 entities, 7 with type "software") in `entity_graph.json`
2. Someone renamed `entity_graph.json` → `entity_graph.json.bak` (to preserve the data)
3. Someone ran the module, which created a new empty `entity_graph.json` via the module-load init
4. Later, someone tried to load the `.bak` — `EntityGraph.load()` failed because `"software"` type is not in `VALID_ENTITY_TYPES`
5. Someone (attempting to fix) modified `entity_graph.py` working copy to add `"software"` to `VALID_ENTITY_TYPES`
6. But this change was never committed — the committed code remains clean

### Current state:
- Committed code is **clean** (no "software" in types)
- Working `entity_graph.py` matches committed code (MD5 identical)
- `entity_graph.json` is **empty** (0 entities) — clean
- `entity_graph.json.bak` contains **rich data with unknown type** — orphaned

---

## SECTION 9 — Risk Assessment

| Risk | Level | Notes |
|------|-------|-------|
| Production stability | **LOW** | `entity_graph.json` is empty, imports work, release gate passes |
| Data loss | **MEDIUM** | 18 entities in `.bak` including 7 software entities at risk of being permanently lost |
| Interpretation impact | **NONE** | No dependency — deterministic handlers unaffected |
| Schema correctness | **MEDIUM** | `"software"` type in backup is incompatible with committed schema |
| CLI stability | **LOW** | `cli_external.py` has null guard — won't crash if module fails |

---

## SECTION 10 — Recommended Next Action

**If data in `.bak` is valuable** (restore the 18 entities):

1. Add `"software"` to `VALID_ENTITY_TYPES` in `entity_graph.py` (committed change)
2. Rename `.bak` → `entity_graph.json`
3. Verify `EntityGraph.load()` succeeds
4. Commit both changes together

**If `.bak` data is discardable** (accept data loss):

1. Delete `entity_graph.json.bak`
2. No code changes needed
3. Entity graph system remains functional with empty state

**Option 1 (restore) is recommended if the 18 entities contain有价值 information.**

---

## Summary

The entity graph subsystem is **partially integrated but currently stable**. The working state is clean (empty graph, clean code, release gate passes). The `.bak` file is orphaned data with schema incompatibility. No impact on interpretation or deterministic handler extraction work.
