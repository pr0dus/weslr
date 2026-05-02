"""
JSONL Archive Policy V1 — WESLR
Defines which JSONL files are safe to archive and under what thresholds.
Operator-run only. No runtime wiring.
"""

from __future__ import annotations
from pathlib import Path
import hashlib


_ARCHIVE_ROOT = Path("weslr/archive/jsonl")
_ARCHIVE_ROOT.mkdir(parents=True, exist_ok=True)


def get_jsonl_archive_policy() -> dict:
    """Return the V1 archive policy."""
    return {
        "version": "v1",
        "archive_root": str(_ARCHIVE_ROOT),
        "default_threshold_lines": 1000,
        "default_keep_tail_lines": 300,
        "allowed_low_risk": [
            "weslr/public_signals.jsonl",
            "weslr/contract_observations.jsonl",
            "weslr/operator_feedback_log.jsonl",
            "weslr/iss/iss_diagnostic_records.jsonl",
        ],
        "protected_governance": [
            "weslr/contract_insufficiency_log.jsonl",
            "weslr/contract_proposal_review_log.jsonl",
            "weslr/proposal_trace.jsonl",
            "weslr/implementation_plans.jsonl",
        ],
        "protected_reason": (
            "governance-critical: records formal system decisions, "
            "proposals, and insufficiencies that require full audit trail"
        ),
    }


def classify_jsonl_file(path: str) -> dict:
    """Classify a JSONL file as archive-allowed, protected, or unknown.

    path can be relative ("weslr/public_signals.jsonl", "iss/records.jsonl")
    or absolute ("/tmp/xxx/weslr/iss/records.jsonl").
    Classification strips any leading prefix so the file is identified by
    its relative path within the weslr/ directory tree.
    """
    policy = get_jsonl_archive_policy()
    full = str(Path(path).as_posix())

    # Strip any leading prefix to get the weslr-relative path.
    # e.g. "/tmp/xxx/weslr/iss/records.jsonl" -> "weslr/iss/records.jsonl"
    # e.g. "weslr/public_signals.jsonl" -> "weslr/public_signals.jsonl"
    rel = full
    for marker in ["weslr/", "iss/"]:
        idx = full.rfind(marker)
        if idx != -1:
            rel = full[idx:]
            break

    normalized = rel.lstrip("/")

    for allowed_path in policy["allowed_low_risk"]:
        if normalized == allowed_path:
            return {
                "path": normalized,
                "archive_allowed": True,
                "reason": "allowed_low_risk",
                "threshold_lines": policy["default_threshold_lines"],
                "keep_tail_lines": policy["default_keep_tail_lines"],
            }

    for protected_path in policy["protected_governance"]:
        if normalized == protected_path:
            return {
                "path": normalized,
                "archive_allowed": False,
                "reason": "protected_governance",
                "threshold_lines": policy["default_threshold_lines"],
                "keep_tail_lines": policy["default_keep_tail_lines"],
            }

    return {
        "path": normalized,
        "archive_allowed": False,
        "reason": "unknown_file",
        "threshold_lines": policy["default_threshold_lines"],
        "keep_tail_lines": policy["default_keep_tail_lines"],
    }


def plan_jsonl_archives(
    root: str = "weslr",
    threshold_lines: int | None = None,
    keep_tail_lines: int | None = None,
) -> dict:
    """
    Scan JSONL files under root and return an archive plan.
    Read-only — no files are modified.
    """
    from datetime import datetime, timezone

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

    root_path = Path(root)
    if not root_path.exists():
        return {"error": f"Root does not exist: {root}"}

    jsonl_files: list[Path] = []
    for p in root_path.rglob("*.jsonl"):
        # Accept root/weslr/*.jsonl or root/weslr/iss/*.jsonl only
        # (depth 1 below root, name "weslr" or "iss")
        if len(p.parent.relative_to(root_path).parts) == 1 and p.parent.name in ("weslr", "iss"):
            jsonl_files.append(p)

    plans = []
    for fp in sorted(jsonl_files):
        # Compute relative path for classification and plan output.
        # e.g. "weslr/public_signals.jsonl" or "weslr/iss/iss_diagnostic_records.jsonl"
        rel = fp.relative_to(root_path).as_posix()
        classification = classify_jsonl_file(rel)

        if not classification["archive_allowed"]:
            plans.append(
                {
                    "path": rel,
                    "status": "skipped",
                    "skip_reason": classification["reason"],
                }
            )
            continue

        lines: list[str] = []
        try:
            with open(fp, "r", encoding="utf-8") as fh:
                lines = [line.strip() for line in fh if line.strip()]
        except Exception:
            plans.append({"path": rel, "status": "error", "error": "could not read file"})
            continue

        line_count = len(lines)

        if line_count <= threshold:
            plans.append(
                {
                    "path": rel,
                    "status": "skipped",
                    "skip_reason": "below_threshold",
                    "line_count": line_count,
                    "threshold": threshold,
                }
            )
            continue

        lines_to_archive = line_count - keep
        sha256_before = _sha256(fp)

        plans.append(
            {
                "path": rel,
                "status": "planned",
                "line_count": line_count,
                "lines_to_archive": lines_to_archive,
                "lines_to_keep": keep,
                "threshold": threshold,
                "sha256_before": sha256_before,
            }
        )

    return {
        "version": "v1",
        "policy": policy["version"],
        "scanned_root": str(root),
        "threshold": threshold,
        "keep_tail_lines": keep,
        "archive_root": policy["archive_root"],
        "plans": plans,
    }


def _sha256(path: Path) -> str:
    """Compute SHA256 of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        h.update(fh.read())
    return h.hexdigest()