# Session: 2026-03-31 14:35:42 UTC

- **Session Key**: agent:main:main
- **Session ID**: 4f23da0e-5849-4c18-a4ea-2dae3a6a54b0
- **Source**: webchat

## Conversation Summary

user: Sender (untrusted metadata):
```json
{
  "label": "openclaw-control-ui",
  "id": "openclaw-control-ui"
}
```

[Tue 2026-03-31 14:43 GMT+2] We are continuing WESLR on the private repo.

Current active branch:
`feature/tia-industrial-slice`

Do not patch yet.

The current `tia-show` proposal is close, but it still has one important bug:
- `get_tia_import_record()` uses `list_tia_import_history(history_path, limit=100)`
- this can silently miss older records and break `--index` or `--source`

TASK:
Revise the `tia-show` patch one more time so it is fully safe.

Requirements:
- keep helper/data lookup logic in `tia_import.py`
- keep CLI handler in `main.py`
- do NOT rely on `limit=100`
- `get_tia_import_record()` must read the full history file directly
- preserve newest-first semantics for selection
- support:
 - default latest record
 - `--index`
 - `--source`
- move `strftime` / `localtime` import to top-level imports in `main.py`
- do not touch dashboard
- do not touch entity_graph
- do not touch reports

Return exactly:

1. FINAL SAFE PATCH
2. EXACT FILES
3. EXACT FUNCTIONS / INSERTION POINTS
4. PATCH
5. TESTS
6. ROLLBACK
assistant: You're absolutely right — I need to read the full history file directly without a limit to ensure `--index` and `--source` work reliably.

Here's the fully safe revision:

---

**1. FINAL SAFE PATCH**

Add a helper function `get_tia_import_record()` in `tia_import.py` that reads the full history file directly (no limit), and a CLI handler in `main.py`. Also ensure `strftime`/`localtime` are top-level imports in `main.py`.

**2. EXACT FILES**

- `tia_import.py` — add `get_tia_import_record()` helper
- `main.py` — add `cmd_tia_show()` handler and CLI entry

**3. EXACT FUNCTIONS / INSERTION POINTS**

**In `tia_import.py`:**
After `list_tia_import_history()` (around line 335), add:

```python
def get_tia_import_record(history_path: str | Path | None = None, idx: int | None = None, source: str | None = None) -> dict | None:
    """Fetch a single TIA import record by index or source file.
    
    Returns None if not found.
    History is newest-first, so idx=1 means latest.
    Does not use limit — reads full history to ensure all records are accessible.
    """
    if history_path is None:
        history_path = Path(__file__).resolve().parent / "tia_import_history.json"
    else:
        history_path = Path(history_path)
    
    if not history_path.exists():
        return None
    
    try:
        with open(history_path, "r", encoding="utf-8") as f:
            history = json.load(f)
    except Exception:
        return None
    
    records = history.get("records", [])
    if not records:
        return None
    
    # History is newest-first in list_tia_import_history, but here we read raw records
    # and apply the same reversal to preserve semantics
    records = list(reversed(records))
    
    if idx is not None:
        if idx < 1 or idx > len(records):
            return None
        return records[idx - 1]
    
    if source is not None:
        for r in records:
            if r.get("source_file", "").endswith(source) or r.get("source_file") == source:
                return r
        return None
    
    return records[0]  # latest
```

**In `main.py`:**
After `cmd_tia_history` function, add:

```python
def cmd_tia_show(args):
    """Show detailed summary for one TIA import."""
    history_path = Path(args.path) if args.path else None
    idx = getattr(args, 'index', None)
    source = getattr(args, 'source', None)
    
    record = get_tia_import_record(history_path, idx, source)
    if record is None:
        emit({"error": "No TIA import history found or record not found"})
        print("\n❌ No record found")
        return
    
    ts = record.get("timestamp", 0)
    ts_str = strftime("%Y-%m-%d %H:%M:%S", localtime(ts / 1000))
    counts = record.get("item_counts", {})
    
    summary = {
        "project_name": record.get("project_name", "Unknown"),
        "source_file": record.get("source_file", ""),
        "timestamp": ts,
        "timestamp_human": ts_str,
        "status": record.get("status", "unknown"),
        "validation_ok": record.get("validation", {}).get("ok", False),
        "validation_warnings": record.get("validation", {}).get("warnings", 0),
        "validation_errors": record.get("validation", {}).get("errors", 0),
        "devices": counts.get("devices", 0),
        "plcs": counts.get("plcs", 0),
        "cpus": counts.get("cpus", 0),
        "modules": counts.get("modules", 0),
        "tags": counts.get("tags", 0),
        "total_items": counts.get("total_items", 0),
        "raw_output": record.get("raw_output", ""),
        "normalized_output": record.get("normalized_output", ""),
    }
    
    emit(summary)
    
    print(f"\n=== TIA Import Summary ===")
    print(f"Project: {summary['project_name']}")
    print(f"Timestamp: {summary['timestamp_human']}")
    status_icon = {"ok": "✅", "warning": "⚠️", "error": "❌"}.get(summary['status'], "❓")
    print(f"Status: {status_icon} {summary['status']}")
    print(f"Items: {summary['total_items']} total ({summary['devices']} devices, {summary['plcs']} PLCs, {summary['cpus']} CPUs, {summary['modules']} modules, {summary['tags']} tags)")
    if summary['validation_warnings'] or summary['validation_errors']:
        print(f"Validation: {summary['validation_warnings']} warnings, {summary['validation_errors']} errors")
    print(f"Raw output: {summary['raw_output']}")
    print(f"Normalized output: {summary['normalized_output']}")
```

**CLI entry in `main.py` (after `tia-history`):**

```python
p = sub.add_parser("tia-show", help="show detailed summary for one TIA import")
p.add_argument("--path", default="", help="override history file path")
p.add_argument("--index", type=int, default=None, help="record index (1-based, default: latest)")
p.add_argument("--source", default=None, help="filter by source filename")
p.set_defaults(func=cmd_tia_show)
```

**4. PATCH**

*In `tia_import.py` after `list_tia_import_history()` (after line 335):*

```python
def get_tia_import_record(history_path: str | Path | None = None, idx: int | None = None, source: str | None = None) -> dict | None:
    """Fetch a single TIA import record by index or source file.
    
    Returns None if not found.
    History is newest-first, so idx=1 means latest.
    Does not use limit — reads full history to ensure all records are accessible.
    """
    if history_path is None:
        history_path = Path(__file__).resolve().parent / "tia_import_history.json"
    else:
        history_path = Path(history_path)
    
    if not history_path.exists():
        return None
    
    try:
        with open(history_path, "r", encoding="utf-8") as f:
            history = json.load(f)
    except Exception:
        return None
    
    records = history.get("records", [])
    if not records:
        return None
    
    records = list(reversed(records))
    
    if idx is not None:
        if idx < 1 or idx > len(records):
            return None
        return records[idx - 1]
    
    if source is not None:
        for r in records:
            if r.get("source_file", "").endswith(source) or r.get("source_file") == source:
                return r
        return None
    
    return records[0]
```

*In `main.py` after `cmd_tia_history` function:*

```python
def cmd_tia_show(args):
    """Show detailed summary for one TIA import."""
    history_path = Path(args.path) if args.path else None
    idx = getattr(args, 'index', None)
    source = getattr(args, 'source', None)
    
    record = get_tia_import_record(history_path, idx, source)
    if record is None:
        emit({"error": "No TIA import history found or record not found"})
        print("\n❌ No record found")
        return
    
    ts = record.get("timestamp", 0)
    ts_str = strftime("%Y-%m-%d %H:%M:%S", localtime(ts / 1000))
    counts = record.get("item_counts", {})
    
    summary = {
        "project_name": record.get("project_name", "Unknown"),
        "source_file": record.get("source_file", ""),
        "timestamp": ts,
        "timestamp_human": ts_str,
        "status": record.get("status", "unknown"),
        "validation_ok": record.get("validation", {}).get("ok", False),
        "validation_warnings": record.get("validation", {}).get("warnings", 0),
        "validation_errors": record.get("validation", {}).get("errors", 0),
        "devices": counts.get("devices", 0),
        "plcs": counts.get("plcs", 0),
        "cpus": counts.get("cpus", 0),
        "modules": counts.get("modules", 0),
        "tags": counts.get("tags", 0),
        "total_items": counts.get("total_items", 0),
        "raw_output": record.get("raw_output", ""),
        "normalized_output": record.get("normalized_output", ""),
    }
    
    emit(summary)
    
    print(f"\n=== TIA Import Summary ===")
    print(f"Project: {summary['project_name']}")
    print(f"Timestamp: {summary['timestamp_human']}")
    status_icon = {"ok": "✅", "warning": "⚠️", "error": "❌"}.get(summary['status'], "❓")
    print(f"Status: {status_icon} {summary['status']}")
    print(f"Items: {summary['total_items']} total ({summary['devices']} devices, {summary['plcs']} PLCs, {summary['cpus']} CPUs, {summary['modules']} modules, {summary['tags']} tags)")
    if summary['validation_warnings'] or summary['validation_errors']:
        print(f"Validation: {summary['validation_warnings']} warnings, {summary['validation_errors']} errors")
    print(f"Raw output: {summary['raw_output']}")
    print(f"Normalized output: {summary['normalized_output']}")
```

*In `main.py` after `tia-history` CLI entry:*

```python
p = sub.add_parser("tia-show", help="show detailed summary for one TIA import")
p.add_argument("--path", default="", help="override history file path")
p.add_argument("--index", type=int, default=None, help="record index (1-based, default: latest)")
p.add_argument("--source", default=None, help="filter by source filename")
p.set_defaults(func=cmd_tia_show)
```

**5. TESTS**

```bash
cd /data/data/com.termux/files/home/.openclaw/workspace

# Test: show latest (default)
python main.py tia-show

# Test: show by index (1-based, latest is 1)
python main.py tia-show --index 1

# Test: show by index for older record
python main.py tia-show --index 2

# Test: show by source filename
python main.py tia-show --source tia_real_export.json

# Test: show help
python main.py tia-show --help
```

**6. ROLLBACK**

```bash
git revert HEAD --no-edit
git push origin feature/tia-industrial-slice
```

Or manually remove:
- `get_tia_import_record()` from `tia_import.py`
- `cmd_tia_show()` from `main.py`
- `tia-show` CLI entry from `main.py`
user: Sender (untrusted metadata):
```json
{
  "label": "openclaw-control-ui",
  "id": "openclaw-control-ui"
}
```

[Tue 2026-03-31 14:44 GMT+2] We are continuing WESLR on the private repo.

Current active branch:
`feature/tia-industrial-slice`

IMPORTANT RULES:
- Do not broaden scope.
- Touch only `tia_import.py` and `main.py`
- Do not modify dashboard
- Do not modify entity_graph
- Do not modify reports
- Keep helper/data lookup logic in `tia_import.py`
- Keep CLI handler in `main.py`
- Ensure `main.py` imports `get_tia_import_record`
- Keep `strftime` / `localtime` as top-level imports in `main.py`

TASK:
Apply the final safe `tia-show` patch.

Required behavior:
- `get_tia_import_record()` in `tia_import.py`
- `cmd_tia_show()` in `main.py`
- `tia-show` CLI subcommand in `main.py`
- support:
 - default latest record
 - `--index`
 - `--source`
- show at minimum:
 - project name
 - timestamp
 - status
 - device count
 - PLC count
 - CPU count
 - module count
 - tag count
 - raw output path
 - normalized output path

Return exactly:

1. FILES TOUCHED
2. EXACT FUNCTIONS / INSERTION POINTS
3. PATCH
4. TESTS
5. SAFE ROLLBACK
assistant: Good, `strftime` and `localtime` are already imported at the top level. Now let me apply the patch:
assistant: Now add the `cmd_tia_show` function in `main.py`:
assistant: Let me find the `cmd_tia_history` function:
assistant: Now add `cmd_tia_show` after `cmd_tia_history`:
assistant: Now add the CLI parser entry for `tia-show`. Let me find where `tia-history` is defined:
assistant: Now verify the import is correct by running a quick test:
assistant: Need to import `get_tia_import_record` in `main.py`. Let me check the import section:
assistant: Now test again:
assistant: Test with `--index 2` (older record):
assistant: Test with `--source`:
assistant: All tests pass. Now let me verify git status and prepare the final response:
assistant: Only `main.py` and `tia_import.py` source files changed (the rest are pycache, checkpoints, and world.db state).

---

**1. FILES TOUCHED**
- `tia_import.py` — added `get_tia_import_record()` helper function
- `main.py` — added `cmd_tia_show()` handler and CLI entry, imported `get_tia_import_record`

**2. EXACT FUNCTIONS / INSERTION POINTS**

**In `tia_import.py`:**
- After `list_tia_import_history()` (after line 346), added:
  ```python
  def get_tia_import_record(history_path: str | Path | None = None, idx: int | None = None, source: str | None = None) -> dict | None:
  ```

**In `main.py`:**
- After `cmd_tia_history()` function (around line 1903), added:
  ```python
  def cmd_tia_show(args):
  ```
- After `tia-history` CLI parser entry (around line 1234), added:
  ```python
  p = sub.add_parser("tia-show", help="show detailed summary for one TIA import")
  ```
- Added `get_tia_import_record` to imports from `tia_import`

**3. PATCH**

*`tia_import.py` additions (after `list_tia_import_history`):*

```python
def get_tia_import_record(history_path: str | Path | None = None, idx: int | None = None, source: str | None = None) -> dict | None:
    """Fetch a single TIA import record by index or source file.
    
    Returns None if not found.
    History is newest-first, so idx=1 means latest.
    Does not use limit — reads full history to ensure all records are accessible.
    """
    if history_path is None:
        history_path = Path(__file__).resolve().parent / "tia_import_history.json"
    else:
        history_path = Path(history_path)
    
    if not history_path.exists():
        return None
    
    try:
        with open(history_path, "r", encoding="utf-8") as f:
            history = json.load(f)
    except Exception:
        return None
    
    records = history.get("records", [])
    if not records:
        return None
    
    records = list(reversed(records))
    
    if idx is not None:
        if idx < 1 or idx > len(records):
            return None
        return records[idx - 1]
    
    if source is not None:
        for r in records:
            if r.get("source_file", "").endswith(source) or r.get("source_file") == source:
                return r
        return None
    
    return records[0]
```

*`main.py` additions:*

**Import:**
```python
from tia_import import (
    create_raw_import_envelope,
    save_import_envelope,
    normalize_tia_envelope,
    save_normalized_envelope,
    record_tia_import_history,
    list_tia_import_history,
    get_tia_import_record,
)
```

**Handler:**
```python
def cmd_tia_show(args):
    """Show detailed summary for one TIA import."""
    history_path = Path(args.path) if args.path else None
    idx = getattr(args, 'index', None)
    source = getattr(args, 'source', None)
    
    record = get_tia_import_record(history_path, idx, source)
    if record is None:
        emit({"error": "No TIA import history found or record not found"})
        print("\n❌ No record found")
        return
    
    ts = record.get("timestamp", 0)
    ts_str = strftime("%Y-%m-%d %H:%M:%S", localtime(ts / 1000))
    counts = record.get("item_counts", {})
    
    summary = {
        "project_name": record.get("project_name", "Unknown"),
        "source_file": record.get("source_file", ""),
        "timestamp": ts,
        "timestamp_human": ts_str,
        "status": record.get("status", "unknown"),
        "validation_ok": record.get("validation", {}).get("ok", False),
        "validation_warnings": record.get("validation", {}).get("warnings", 0),
        "validation_errors": record.get("validation", {}).get("errors", 0),
        "devices": counts.get("devices", 0),
        "plcs": counts.get("plcs", 0),
        "cpus": counts.get("cpus", 0),
        "modules": counts.get("modules", 0),
        "tags": counts.get("tags", 0),
        "total_items": counts.get("total_items", 0),
        "raw_output": record.get("raw_output", ""),
        "normalized_output": record.get("normalized_output", ""),
    }
    
    emit(summary)
    
    print(f"\n=== TIA Import Summary ===")
    print(f"Project: {summary['project_name']}")
    print(f"Timestamp: {summary['timestamp_human']}")
    status_icon = {"ok": "✅", "warning": "⚠️", "error": "❌"}.get(summary['status'], "❓")
    print(f"Status: {status_icon} {summary['status']}")
    print(f"Items: {summary['total_items']} total ({summary['devices']} devices, {summary['plcs']} PLCs, {summary['cpus']} CPUs, {summary['modules']} modules, {summary['tags']} tags)")
    if summary['validation_warnings'] or summary['validation_errors']:
        print(f"Validation: {summary['validation_warnings']} warnings, {summary['validation_errors']} errors")
    print(f"Raw output: {summary['raw_output']}")
    print(f"Normalized output: {summary['normalized_output']}")
```

**CLI entry:**
```python
p = sub.add_parser("tia-show", help="show detailed summary for one TIA import")
p.add_argument("--path", default="", help="override history file path")
p.add_argument("--index", type=int, default=None, help="record index (1-based, default: latest)")
p.add_argument("--source", default=None, help="filter by source filename")
p.set_defaults(func=cmd_tia_show)
```

**4. TESTS**

```bash
# Default latest
python main.py tia-show

# By index (1-based, latest is 1)
python main.py tia-show --index 1

# Older record
python main.py tia-show --index 2

# By source filename
python main.py tia-show --source tia_real_export.json

# Help
python main.py tia-show --help
```

**5. SAFE ROLLBACK**

```bash
git revert HEAD --no-edit
git push origin feature/tia-industrial-slice
```

Or manually remove:
- `get_tia_import_record()` from `tia_import.py`
- `cmd_tia_show()` from `main.py`
- `tia-show` CLI entry and import from `main.py`
