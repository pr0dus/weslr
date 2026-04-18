// plugins/infinity/README.md - Infinity Plugin v1

# OpenClaw Infinity Plugin v1

Session immortality layer — captures and restores active coding context silently across `/reset`, `/new`, and context overflow events.

## Goals

- **Silent-first:** No user prompts during normal operation.
- **Safe restore:** Only restores if repo, branch, and files match.
- **No execution side-effects:** Pending tests restored to internal state only (no auto-run).
- **No manual workflow:** All capture/restore automatic.

## v1 Scope

### What it does

- Captures before `/reset`, `/new`, or context overflow.
- Restores on workspace init only if:
  - No active task (no open files)
  - Repo matches
  - Branch matches
  - Capsule is fresh (<2h old)
  - All active files exist
- Restored state:
  - Opens active files (silent)
  - Restores pending tests to internal state only (no execution)
  - Restores task summary to internal state only

### What it does NOT do (v1)

- No manual save/restore CLI
- No branch checkout
- No test execution
- No auto-cleanup scheduler
- No idle capture
- No `nextStep`/freshness replay

## Installation

```bash
npm install
```

## Testing

```bash
npm test
```

## Configuration

Configurable in `config.js`:

- `retentionMs`: 2 hours default
- `autoCaptureEnabled`: true
- `autoRestoreEnabled`: true
- `strictMissingFiles`: true (v1)
- `logLevel`: 'info'

## File Structure

```
plugins/infinity/
├── capsule/      # Schema & utilities
├── hooks/        # Capture & restore hooks
├── storage/      # CRUD on .openclaw/capsules/
├── config.js
├── index.js      # Plugin entry
└── package.json
```

## Logs

Silent logging to `.openclaw/logs/infinity.log`.

## Future (v1.1+)

- CLI: `/infinity list`, `/infinity restore <id>`, `/infinity export`
- Debug mode: verbose logging, inspection tools
- Idle capture
- Auto-cleanup scheduler
- `nextStep`, `freshness`, `confidence` restoration
