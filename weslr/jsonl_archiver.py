"""
JSONL Archiver V1 — WESLR
Safe, operator-run append-only JSONL archiver.
dry_run=True by default. No deletion of records.
"""

from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from weslr.jsonl_archive_policy import (
    classify_jsonl_file,
    get_jsonl_archive_policy,
)


def archive_jsonl_file(
    path: str,
    archive_root: str | None = None,
    threshold_lines: int | None = None,
    keep_tail_lines: int | None = None,
    dry_run: bool = True,
) -> dict:
    """
    Archive a JSONL file if it qualifies under the archive policy.

    Args:
        path: Relative path to the JSONL file (e.g. "weslr/public_signals.jsonl")
        archive_root: Root directory for archives. Defaults to weslr/archive/jsonl.
        threshold_lines: Lines threshold to trigger archive. Defaults to policy default.
        keep_tail_lines: Number of tail lines to keep in active file. Defaults to policy default.
        dry_run: If True, only returns planned archive — no writes.

    Returns:
        dict with status and metadata including manifest fields.
    """
    policy = get_jsonl_archive_policy()
    threshold = (
        threshold_lines
        if threshold_lines is not None
        else policy["default_threshold_lines"]
    )
    keep = (
        keep_tail_lines
        if keep_tail_lines is not None
        else policy["default_keep_tail_lines"]
    )
    archive_root = Path(
        archive_root if archive_root is not None else policy["archive_root"]
    )

    # Step 1: classify
    classification = classify_jsonl_file(path)
    if not classification["archive_allowed"]:
        reason_map = {
            "protected_governance": "skipped_protected",
            "unknown_file": "skipped_unknown",
        }
        return {
            "path": path,
            "status": reason_map.get(classification["reason"], "skipped"),
            "reason": classification["reason"],
            "dry_run": dry_run,
        }

    fp = Path(path)
    if not fp.exists():
        return {"path": path, "status": "error", "error": "file not found"}

    # Step 2: read all lines
    try:
        with open(fp, "r", encoding="utf-8") as fh:
            all_lines = [line.rstrip("\n") for line in fh if line.strip()]
    except Exception as e:
        return {"path": path, "status": "error", "error": str(e)}

    line_count = len(all_lines)

    # Step 3: threshold check
    if line_count <= threshold:
        return {
            "path": path,
            "status": "skipped_below_threshold",
            "line_count": line_count,
            "threshold": threshold,
            "dry_run": dry_run,
        }

    # Step 4: plan
    lines_to_archive = line_count - keep
    older_lines = all_lines[:-keep] if keep > 0 else all_lines[:]
    tail_lines = all_lines[-keep:] if keep > 0 else []

    sha256_before = _sha256(fp)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%z")

    # Build archive path
    archive_dir = archive_root / f"{fp.stem}"
    archive_dir.mkdir(parents=True, exist_ok=True)
    archive_file = archive_dir / f"{fp.stem}_{ts}.jsonl"

    manifest = {
        "source_file": path,
        "archive_file": str(archive_file),
        "original_line_count": line_count,
        "archived_line_count": len(older_lines),
        "kept_line_count": len(tail_lines),
        "sha256_before": sha256_before,
        "sha256_archive": None,  # filled after write
        "sha256_after": None,  # filled after rewrite
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "dry_run": dry_run,
        "status": "planned",
    }

    if dry_run:
        manifest["status"] = "planned"
        return manifest

    # Step 5: real archive
    try:
        # Write archive file
        with open(archive_file, "w", encoding="utf-8") as fh:
            for line in older_lines:
                fh.write(line + "\n")

        sha256_archive = _sha256(archive_file)

        # Rewrite active file with tail
        # Atomic-ish: write to temp then replace
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".jsonl", delete=False, dir=fp.parent, encoding="utf-8"
        ) as tmp:
            for line in tail_lines:
                tmp.write(line + "\n")
            tmp_path = Path(tmp.name)

        shutil.move(str(tmp_path), str(fp))

        sha256_after = _sha256(fp)

        # Update manifest
        manifest["sha256_archive"] = sha256_archive
        manifest["sha256_after"] = sha256_after
        manifest["status"] = "archived"

        # Write manifest (append to manifest.jsonl in archive_dir)
        manifest_file = archive_dir / "manifest.jsonl"
        with open(manifest_file, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(manifest, ensure_ascii=False) + "\n")

        # Verify
        with open(fp, "r", encoding="utf-8") as fh:
            actual_tail_lines = len([l for l in fh if l.strip()])
        with open(archive_file, "r", encoding="utf-8") as fh:
            actual_archived_lines = len([l for l in fh if l.strip()])

        if actual_tail_lines != len(tail_lines):
            return {
                "path": path,
                "status": "error",
                "error": f"tail line count mismatch: expected {len(tail_lines)}, got {actual_tail_lines}",
            }
        if actual_archived_lines != len(older_lines):
            return {
                "path": path,
                "status": "error",
                "error": f"archived line count mismatch: expected {len(older_lines)}, got {actual_archived_lines}",
            }

        return manifest

    except Exception as e:
        return {"path": path, "status": "error", "error": str(e)}


def archive_jsonl_files(
    paths: list[str] | None = None,
    archive_root: str | None = None,
    threshold_lines: int | None = None,
    keep_tail_lines: int | None = None,
    dry_run: bool = True,
) -> dict:
    """
    Batch archive multiple JSONL files.

    If paths is None, uses all archive-allowed files.
    """
    policy = get_jsonl_archive_policy()
    if paths is None:
        paths = policy["allowed_low_risk"]

    results = []
    for p in paths:
        result = archive_jsonl_file(
            p,
            archive_root=archive_root,
            threshold_lines=threshold_lines,
            keep_tail_lines=keep_tail_lines,
            dry_run=dry_run,
        )
        results.append(result)

    statuses = [r["status"] for r in results]
    return {
        "version": "v1",
        "dry_run": dry_run,
        "total": len(results),
        "results": results,
        "summary": {
            "archived": statuses.count("archived"),
            "planned": statuses.count("planned"),
            "skipped_below_threshold": statuses.count("skipped_below_threshold"),
            "skipped_protected": statuses.count("skipped_protected"),
            "skipped_unknown": statuses.count("skipped_unknown"),
            "error": statuses.count("error"),
        },
    }


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()