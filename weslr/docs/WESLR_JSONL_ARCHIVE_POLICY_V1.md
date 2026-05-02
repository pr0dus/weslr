# WESLR JSONL Archive Policy V1

## Purpose

Prevent unbounded JSONL growth while preserving full audit history and maintaining governance safety. All archiving is operator-run, never automatic from runtime.

## What Is Archived (V1 — Allowed Low-Risk)

| File | Rationale |
|------|-----------|
| `weslr/public_signals.jsonl` | Append-only observational signal log |
| `weslr/contract_observations.jsonl` | Append-only contract observation records |
| `weslr/operator_feedback_log.jsonl` | Append-only operator feedback log |
| `weslr/iss/iss_diagnostic_records.jsonl` | Append-only ISS diagnostic records |

These files are append-only observational logs with low governance criticality. They can be safely archived without losing audit-relevant information.

## What Is Protected (V1 — No Auto-Archive)

| File | Rationale |
|------|-----------|
| `weslr/contract_insufficiency_log.jsonl` | Formal insufficiency records — full audit trail required |
| `weslr/contract_proposal_review_log.jsonl` | Formal proposal review records — governance critical |
| `weslr/proposal_trace.jsonl` | System proposal history — requires full traceability |
| `weslr/implementation_plans.jsonl` | Formal implementation plans — governance critical |

**Any unknown JSONL file** is also protected by default and will not be archived.

## Threshold Behavior

- **Default threshold:** 1000 lines
- **Default keep_tail:** 300 lines
- Files below threshold are **not archived** — they remain active
- Operator can override threshold and keep_tail via function arguments

## Dry-Run Default

`dry_run=True` is the default for all archiver functions. No files are modified until `dry_run=False` is explicitly passed.

## Archive Format

Archived files are stored under `weslr/archive/jsonl/<stem>/`.

Example:
```
weslr/archive/jsonl/public_signals/public_signals_20250502T123045Z.jsonl
```

The active file is rewritten to contain only the last `keep_tail_lines` records. Archived records are preserved in the archive file — **no data is deleted**.

## Archive Manifest

Each archive operation appends one manifest entry to `weslr/archive/jsonl/<stem>/manifest.jsonl`:

```json
{
  "source_file": "weslr/public_signals.jsonl",
  "archive_file": "weslr/archive/jsonl/public_signals/public_signals_20250502T123045Z.jsonl",
  "original_line_count": 1200,
  "archived_line_count": 900,
  "kept_line_count": 300,
  "sha256_before": "abc123...",
  "sha256_archive": "def456...",
  "sha256_after": "ghi789...",
  "timestamp": "2026-05-02T12:30:45+00:00",
  "dry_run": false,
  "status": "archived"
}
```

## Operator-Run Only

- **No runtime wiring** — the archiver is not invoked from `/chat` or any runtime handler
- **No automatic scheduling by default** — the operator runs archives manually or via a scheduled task they explicitly approve
- **Additive only** — the archive creates new files, never modifies governance-critical JSONL

## No Deletion

Archived records are **never deleted**. The archive file grows indefinitely (or until a future V2 policy defines retention). The active file is trimmed to `keep_tail_lines` but existing records are transferred to the archive, not erased.

## Future Possible Automation

A future V2 policy could introduce:
- Operator-approved scheduled tasks (cron-based) with explicit dry-run/confirm steps
- Retention policies for archive files
- Archive restoration procedures
- Protected file archival with additional approval gates

None of these are implemented in V1.

## Usage

```python
from weslr.jsonl_archiver import archive_jsonl_files, archive_jsonl_file

# Dry-run first
result = archive_jsonl_files(dry_run=True)
print(result["summary"])

# Real archive (operator approves)
result = archive_jsonl_files(dry_run=False)
print(result["summary"])
```