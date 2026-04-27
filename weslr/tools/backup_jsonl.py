"""WESLR JSONL backup tool — safe copy-only backup automation."""

from __future__ import annotations

import hashlib
import json
import shutil
import time
from pathlib import Path

_BACKUP_ROOT = Path(__file__).resolve().parent.parent / "backups" / "jsonl"
_JSONL_FILES = [
    Path(__file__).resolve().parent.parent / "proposal_trace.jsonl",
    Path(__file__).resolve().parent.parent / "implementation_plans.jsonl",
    Path(__file__).resolve().parent.parent / "iss" / "iss_diagnostic_records.jsonl",
]


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _backup_jsonl_files() -> dict:
    ts = int(time.time())
    backup_dir = _BACKUP_ROOT / str(ts)
    backup_dir.mkdir(parents=True, exist_ok=True)

    manifest_entries = []
    files_backed_up = 0

    for source_path in _JSONL_FILES:
        if not source_path.exists():
            continue
        stat = source_path.stat()
        line_count = sum(1 for _ in open(source_path, "r", encoding="utf-8", errors="ignore"))
        sha = _sha256(source_path)

        dest_name = source_path.name
        dest_path = backup_dir / dest_name
        shutil.copy2(source_path, dest_path)

        manifest_entries.append({
            "timestamp": ts,
            "source_path": str(source_path),
            "backup_path": str(dest_path),
            "line_count": line_count,
            "size_bytes": stat.st_size,
            "sha256": sha,
        })
        files_backed_up += 1

    manifest_path = backup_dir / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": ts,
            "files": manifest_entries,
        }, f, indent=2)

    return {"files_backed_up": files_backed_up, "backup_dir": str(backup_dir)}


if __name__ == "__main__":
    result = _backup_jsonl_files()
    print(f"WESLR_JSONL_BACKUP_OK")
    print(f"files_backed_up={result['files_backed_up']}")
    print(f"backup_dir={result['backup_dir']}")
