from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict
import subprocess
import os


SAFE_PATTERNS = ["__pycache__", ".pyc"]


def _git_status_porcelain() -> List[str]:
    try:
        out = subprocess.check_output(["git", "status", "--short"], text=True)
        return [line.strip() for line in out.splitlines() if line.strip()]
    except Exception:
        return []


def _matches_safe(path: str) -> bool:
    return path.endswith(".pyc") or "__pycache__" in path


@dataclass
class HygieneReport:
    clean: bool
    safe_noise: List[str] = field(default_factory=list)
    risky_untracked: List[str] = field(default_factory=list)
    modified_tracked: List[str] = field(default_factory=list)
    merge_conflicts: List[str] = field(default_factory=list)


def inspect_worktree() -> HygieneReport:
    lines = _git_status_porcelain()
    safe_noise: List[str] = []
    risky_untracked: List[str] = []
    modified_tracked: List[str] = []
    merge_conflicts: List[str] = []
    for line in lines:
        code, path = line[:2].strip(), line[3:].strip()
        # Merge conflict markers
        if "UU" in line[:2]:
            merge_conflicts.append(path)
            continue
        # Untracked
        if code == "??":
            if _matches_safe(path):
                safe_noise.append(path)
            else:
                risky_untracked.append(path)
            continue
        # Modified tracked
        modified_tracked.append(path)
    clean = not (safe_noise or risky_untracked or modified_tracked or merge_conflicts)
    return HygieneReport(
        clean=clean,
        safe_noise=safe_noise,
        risky_untracked=risky_untracked,
        modified_tracked=modified_tracked,
        merge_conflicts=merge_conflicts,
    )


def clean_safe_noise(report: HygieneReport) -> List[str]:
    """Remove allowlisted safe noise files. Returns list of removed paths."""
    removed = []
    for path in report.safe_noise:
        if path.endswith(".pyc") and os.path.exists(path):
            os.remove(path)
            removed.append(path)
        elif "__pycache__" in path and os.path.isdir(path):
            # remove directory tree
            for root, dirs, files in os.walk(path, topdown=False):
                for f in files:
                    os.remove(os.path.join(root, f))
                for d in dirs:
                    os.rmdir(os.path.join(root, d))
            os.rmdir(path)
            removed.append(path)
    return removed
