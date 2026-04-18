# REPO_HYGIENE_STANDARD_V1 — WESLR Repository Boundary Contract

## 1. Purpose

This standard defines the authoritative boundary between tracked source and runtime state
in the WESLR repository. It resolves a structural ambiguity: the .weslr/ directory
contains both runtime-generated state (which must never be committed) and approved
compact tier artifacts (which must be tracked).

Everyone touching this repo: read this before adding or removing anything in .weslr/.

---

## 2. Canonical Rule for ".weslr/"

```
.weslr/ is RUNTIME STATE by default.
It is IGNORED by git unless explicitly allowlisted here.
```

---

## 3. Tracked Exceptions — Only These Files

These are compact, handseedable tier artifacts. They are intentionally committed
because they are the L0/L1 memory bootstrap — WESLR cannot start correctly
without them, and they are small enough to review in full.

| File | Purpose |
|---|---|
| `.weslr/memory_tiers/l0_identity.json` | Identity core: identity_anchor, core_drives, operator name/role |
| `.weslr/memory_tiers/l1_operating.json` | Operating facts: affect, narrative, intent, governance |

**Adding a new tier file to .weslr/memory_tiers/:**
1. Seed the file with meaningful initial data
2. Update `load_tier()` in `sim.py` to handle the new tier name
3. Update this document to list the new file
4. Commit as part of the tier implementation pass

**No other .weslr/ content belongs in the index.**

---

## 4. Explicitly Ignored Runtime Artifacts

These are generated at runtime. They MUST NOT be committed.

| Pattern | Reason |
|---|---|
| `.weslr/charter.json` | Seeded at runtime, changes over time |
| `.weslr/timelines/` | Append-only event logs, grows indefinitely |
| `*.jsonl` | Runtime execution logs |
| `checkpoints/` | Backup artifacts from editor sessions |
| `exports/` | Generated export bundles |
| `__pycache__/` | Python bytecode cache |
| `memory/` | Session session log files |
| `.pytest_cache/` | Test runner artifact |
| `.openclaw/` | OpenClaw agent runtime state |
| `.learnings/` | OpenClaw learning state |

---

## 5. Commit Discipline Rules

**Before committing anything:**
- Run `git status` — confirm only intended source files are staged
- Confirm no `.weslr/` content is staged unless it matches the allowlist in Section 3
- Confirm no `*.jsonl`, `checkpoints/`, `exports/`, or `memory/` files are staged

**When adding files to .weslr/memory_tiers/:**
- Always update this document in the same commit
- Always update `load_tier()` in the same commit
- Do not add runtime state files to the tier directory

**When merging branches:**
- If a merge introduces .weslr/ content, apply Section 3 rules to the result
- If unsure, treat .weslr/ content as ignored — operator review is required
  before committing .weslr/ additions from external branches

**Squash merges are acceptable for hygiene-only commits** (gitignore updates,
artifact removal, tier file additions). Full history merges are preferred for
feature commits where history matters.

---

## 6. Merge / Review Rule

```
If .weslr/ content appears in a diff and is not in Section 3,
it is an accident until proven otherwise.
```

Treat all unlisted .weslr/ files as rejected unless an explicit hygiene review
confirms they belong. This applies to PRs, merges, and branch diffs.

---

## 7. Related Documents

- `docs/UI_SATELLITE_STANDARD_V1.md` — Satellite UI contract
- `docs/APPROVAL_GATED_SELF_IMPROVEMENT_LOOP_V1.md` — Self-modification governance
- `.gitignore` — Machine-enforced boundary (read it; it mirrors this contract)

---

_Evolves when a new memory tier is added. Operator approval required for changes._
