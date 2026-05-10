"""WESLR Standalone Runtime Status V1.

Read-only helpers for assessing whether the current WESLR checkout can operate
as a standalone runtime candidate without OpenClaw as a required dependency.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

_RUNTIME_FILES = [
    "main.py",
    "run.sh",
    "weslr_main.py",
    "weslr-test-deployment/api_server.py",
    "deploy/staging/weslr_demo_server.py",
]

_ABSOLUTE_OPENCLAW_PATH = "/data/data/com.termux/files/home/.openclaw/workspace"


def find_repo_root(start: str | Path | None = None) -> Path:
    """Find the WESLR repo root using only local repo indicators."""
    origin = Path(start) if start is not None else Path(__file__).resolve()
    current = origin.resolve()
    if current.is_file():
        current = current.parent

    for candidate in (current, *current.parents):
        if (candidate / "main.py").is_file() and (candidate / "weslr").is_dir():
            return candidate
    raise RuntimeError(f"Could not locate WESLR repo root from: {origin}")


def scan_runtime_openclaw_coupling(repo_root: str | Path) -> dict[str, Any]:
    """Scan only runnable runtime files for hardcoded OpenClaw workspace paths."""
    root = Path(repo_root).resolve()
    checked_files: list[str] = []
    hardcoded_openclaw_paths: list[dict[str, str]] = []

    for rel_path in _RUNTIME_FILES:
        path = root / rel_path
        checked_files.append(rel_path)
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        coupling_patterns = (
            rf"sys\.path\.insert\([^\n]*{re.escape(_ABSOLUTE_OPENCLAW_PATH)}",
            rf"cwd\s*=\s*[\"']{re.escape(_ABSOLUTE_OPENCLAW_PATH)}",
            rf"WORKSPACE(?:_DIR)?\s*=\s*[\"']{re.escape(_ABSOLUTE_OPENCLAW_PATH)}",
        )
        if any(re.search(pattern, text) for pattern in coupling_patterns):
            hardcoded_openclaw_paths.append(
                {
                    "file": rel_path,
                    "match": _ABSOLUTE_OPENCLAW_PATH,
                }
            )

    return {
        "checked_files": checked_files,
        "hardcoded_openclaw_paths": hardcoded_openclaw_paths,
        "clean": not hardcoded_openclaw_paths,
    }


def get_standalone_runtime_status(start: str | Path | None = None) -> dict[str, Any]:
    """Return a read-only standalone readiness status summary."""
    runtime_warnings: list[str] = []
    standalone_blockers: list[str] = []
    recommendations: list[str] = []

    try:
        repo_root = find_repo_root(start)
        repo_root_detected = True
    except Exception as exc:
        repo_root = Path(start).resolve() if start is not None else Path(__file__).resolve().parent
        repo_root_detected = False
        runtime_warnings.append(f"repo_root_detection_failed: {exc}")
        standalone_blockers.append("repo_root_detection_unavailable")
        recommendations.append("add or repair repo-root detection before relying on standalone probes")

    openclaw_runtime_detected = ".openclaw" in str(repo_root)
    coupling_scan = scan_runtime_openclaw_coupling(repo_root) if repo_root_detected else {
        "checked_files": [],
        "hardcoded_openclaw_paths": [],
        "clean": False,
    }

    if not coupling_scan["clean"]:
        standalone_blockers.append("hardcoded_openclaw_runtime_paths_present")
        runtime_warnings.append("runnable runtime files still contain OpenClaw workspace coupling")
        recommendations.append("remove hardcoded OpenClaw workspace paths from runnable runtime files")

    subsystems = {
        "interpretation": _module_status("interpretation.py", repo_root),
        "file_router": _module_status("weslr/file_router.py", repo_root),
        "eval_harness": _module_status("weslr/evals/run_conversation_eval.py", repo_root),
        "state_checkpoint": _module_status("weslr/state_checkpoint.py", repo_root),
        "governance_health": _module_status("weslr/governance_health.py", repo_root),
        "public_demo_chat": _module_status("weslr/public_demo_chat.py", repo_root),
    }

    if not subsystems["public_demo_chat"]["available"]:
        runtime_warnings.append("public_demo_chat module not present")
        recommendations.append("confirm whether public demo chat should be part of the standalone runtime surface")

    if not recommendations:
        recommendations.extend(
            [
                "keep runnable runtime files free of absolute workspace paths",
                "expand this surface with a canonical health endpoint once runtime consolidation begins",
            ]
        )

    return {
        "runtime_mode": "standalone_candidate",
        "read_only": True,
        "repo_root": str(repo_root),
        "repo_root_detected": repo_root_detected,
        "openclaw_runtime_required": False,
        "openclaw_runtime_detected": openclaw_runtime_detected,
        "runtime_warnings": runtime_warnings,
        "subsystems": subsystems,
        "standalone_blockers": standalone_blockers,
        "recommendations": recommendations,
        "runtime_coupling_scan": coupling_scan,
    }


def _module_status(rel_path: str, repo_root: Path) -> dict[str, Any]:
    path = repo_root / rel_path
    return {
        "available": path.exists(),
        "path": rel_path,
    }
