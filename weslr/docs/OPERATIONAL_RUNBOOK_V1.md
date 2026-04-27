# WESLR Operational Runbook — JSONL Backup Automation

**Version:** 1.0
**Status:** active reference
**Created:** 2026-04-27

---

## SECTION 1 — JSONL File Locations

| File | Path | Contents |
|---|---|---|
| `proposal_trace.jsonl` | `weslr/proposal_trace.jsonl` | Proposal lifecycle: created, decided, modified |
| `implementation_plans.jsonl` | `weslr/implementation_plans.jsonl` | Implementation plan records |
| `iss_diagnostic_records.jsonl` | `weslr/iss/iss_diagnostic_records.jsonl` | ISS probe results and gap signals |

All files are append-only. No line is ever modified or deleted.

---

## SECTION 2 — Backup Command

```bash
python3 weslr/tools/backup_jsonl.py
```

**Output:**
```
WESLR_JSONL_BACKUP_OK
files_backed_up=3
backup_dir=weslr/backups/jsonl/<timestamp>/
```

**What it does:**
- Creates a timestamped backup directory: `weslr/backups/jsonl/<unix_timestamp>/`
- Copies all existing JSONL files using `shutil.copy2` (preserves metadata)
- Writes `manifest.json` inside the backup directory with: timestamp, source_path, backup_path, line_count, size_bytes, sha256
- Source files are never modified

**What it does NOT do:**
- No deletion of source files
- No truncation of source files
- No compression
- No rotation

---

## SECTION 3 — When to Run Backups

Run a backup **before** each of these operations:

| Situation | Why |
|---|---|
| Before any schema migration | Schema changes may affect write validation or loader behavior |
| Before any refactor touching JSONL loaders/writers | Refactors risk breaking validation or append logic |
| Before any future `execution_allowed=True` change | Critical safety boundary — rollback point needed |
| Before running exploratory test scripts | Some tests use temp files; a backup ensures clean state |
| Weekly during active development | Accumulated state grows with each session |
| After any `record_*` call that写入s new data | Documents state before new records are added |

**Reminder:** JSONL state is not reverted by `git revert`. Backups are the only rollback mechanism for JSONL state.

---

## SECTION 4 — Backup Directory Structure

```
weslr/backups/jsonl/<timestamp>/
  proposal_trace.jsonl         # exact copy
  implementation_plans.jsonl   # exact copy
  iss_diagnostic_records.jsonl # exact copy
  manifest.json                # metadata + checksums
```

The timestamp is a Unix epoch integer. Sort by timestamp to get chronological backups.

---

## SECTION 5 — Restore Guidance

Restore is **manual only**. No automated restore script exists.

**To restore from backup:**

1. Identify the backup directory to restore from:
   ```bash
   ls weslr/backups/jsonl/
   ```

2. Inspect the manifest to confirm contents:
   ```bash
   cat weslr/backups/jsonl/<timestamp>/manifest.json
   ```

3. Verify sha256 matches expected file:
   ```bash
   sha256sum weslr/backups/jsonl/<timestamp>/proposal_trace.jsonl
   ```

4. Copy the backup file back after operator confirmation:
   ```bash
   cp weslr/backups/jsonl/<timestamp>/proposal_trace.jsonl weslr/proposal_trace.jsonl
   ```

5. Verify the restored file:
   ```bash
   wc -l weslr/proposal_trace.jsonl
   python3 -c "import json; [json.loads(l) for l in open('weslr/proposal_trace.jsonl')]"
   ```

**Important:**
- Backups do not rollback git commits. Git history is independent of JSONL state.
- `git revert` does not affect JSONL files. JSONL files are not tracked by git.
- Restoration is operator discretion. Confirm before copying back.

---

## SECTION 6 — Rotation Policy

No automatic rotation exists yet.

**Planned rotation (future):** Rotate when any JSONL file exceeds 1000 lines. Backup then truncate by archiving old records into a dated archive file.

**Until rotation is implemented:**
- Monitor file size manually with `wc -l weslr/*.jsonl weslr/iss/*.jsonl`
- Back up before any large write session

---

## SECTION 7 — Warnings

⚠️ **Backups do not rollback git commits.**
JSONL files are not tracked by git. Git history captures code, not data state.

⚠️ **`git revert` does not rollback JSONL state.**
If you revert a commit that changes code behavior affecting JSONL writes, the JSONL files retain all previously written records.

⚠️ **No automated restore exists.**
Manual copy-back is the only restore path. Always verify sha256 before restoring.

⚠️ **No compression.**
Backups use raw copies. Disk usage grows with each backup. Prune old backups manually when disk space is a concern.

---

## SECTION 8 — Backup Tool Reference

**File:** `weslr/tools/backup_jsonl.py`

```bash
python3 weslr/tools/backup_jsonl.py
# Returns: WESLR_JSONL_BACKUP_OK, files_backed_up=N, backup_dir=...
```

Exit codes:
- `0` — backup succeeded
- `1` — backup failed (e.g., directory creation error)

Dependencies: Python 3 standard library only (`pathlib`, `shutil`, `hashlib`, `json`, `time`)

---

*Document version: 1.0*
*Status: active reference*
*Next step: add rotation policy when any JSONL exceeds 1000 lines*
