#!/usr/bin/env python3
"""
WESLR Release Gate V1
Runs pre-commit checks before any WESLR commit.
Exits 0 only if all gates pass.

Usage:
  python3 weslr/tests/release_gate_v1.py

Gates:
  G1 — Test harness passes (TEST_HARNESS_V1_OK)
  G2 — Staged files are within allowed scope
  G3 — No execution_allowed=True in production weslr/*.py
  G4 — No OpenClaw core or TIA C# in staged scope
"""

import subprocess
import sys
import pathlib
import re

_workspace = pathlib.Path(__file__).resolve().parents[2]
_harness = _workspace / "weslr" / "tests" / "test_harness_v1.py"


def _run_harness():
    """Gate 1 — Run test harness, require TEST_HARNESS_V1_OK."""
    result = subprocess.run(
        ["python3", str(_harness)],
        capture_output=True,
        text=True,
        cwd=str(_workspace)
    )
    combined = result.stdout + result.stderr
    if "TEST_HARNESS_V1_OK" not in combined:
        print("GATE 1 FAILED: test harness did not pass")
        print("Output:", combined[-500:])
        return False
    print("GATE 1: test harness passed")
    return True


def _get_staged_files():
    """Get files currently staged in the index (git add-ed but not yet committed)."""
    diff_cached = subprocess.run(
        ["git", "diff", "--name-only", "--cached"],
        capture_output=True, text=True, cwd=str(_workspace)
    )
    return [p.strip() for p in diff_cached.stdout.strip().split("\n") if p.strip()]


def _check_git_scope():
    """Gate 2 — Check that staged files are within allowed scope.
    
    Allowed paths:
      - weslr/** (any file inside weslr/)
      - interpretation.py
    
    Forbidden:
      - openclaw/, plugins/, memory/, continuity/
      - any .cs file
      - any path outside the allowed list above
    
    Files not yet staged are not checked — operator must `git add` them first.
    """
    staged = _get_staged_files()

    FORBIDDEN_PREFIXES = ["openclaw/", "plugins/", "memory/", "continuity/"]
    FORBIDDEN_EXTENSIONS = {".cs"}

    violations = []
    for path in staged:
        for prefix in FORBIDDEN_PREFIXES:
            if path.startswith(prefix):
                violations.append(f"  forbidden prefix {prefix!r}: {path}")
        if any(path.endswith(ext) for ext in FORBIDDEN_EXTENSIONS):
            violations.append(f"  forbidden extension: {path}")
        if not (path.startswith("weslr/") or path == "interpretation.py"):
            violations.append(f"  outside allowed scope: {path}")

    if violations:
        print("GATE 2 FAILED: staged files contain forbidden paths:")
        for v in violations:
            print(v)
        return False

    if staged:
        print(f"GATE 2: {len(staged)} staged file(s) — all in allowed scope")
    else:
        print("GATE 2: no files staged — nothing to check")
    return True


def _check_execution_allowed():
    """Gate 3 — No execution_allowed=True in production weslr/*.py files.
    
    Skips test files (test_harness_v1.py, release_gate_v1.py) since they
    intentionally set execution_allowed=True in test data (bad_plan dict).
    """
    weslr_dir = _workspace / "weslr"
    pattern = re.compile(r"execution_allowed\s*=\s*True", re.IGNORECASE)

    violations = []
    for py_file in weslr_dir.rglob("*.py"):
        if py_file.name in ("test_harness_v1.py", "release_gate_v1.py"):
            continue
        try:
            content = py_file.read_text()
            for lineno, line in enumerate(content.splitlines(), 1):
                if pattern.search(line):
                    rel = py_file.relative_to(_workspace)
                    violations.append(f"  {rel}:{lineno}")
        except Exception:
            pass

    if violations:
        print("GATE 3 FAILED: execution_allowed=True found in production code:")
        for v in violations:
            print(v)
        return False

    print("GATE 3: no execution_allowed=True in production weslr/*.py")
    return True


def _check_openclaw_tia():
    """Gate 4 — No OpenClaw core or TIA C# files in staged scope."""
    staged = _get_staged_files()

    violations = []
    for path in staged:
        if path.startswith("openclaw/") or path.startswith("plugins/"):
            violations.append(f"  OpenClaw core: {path}")
        if path.endswith(".cs"):
            violations.append(f"  TIA C#: {path}")
        if "tia-bridge" in path.lower() and "weslr/docs/tia-bridge" not in path:
            violations.append(f"  TIA bridge: {path}")

    if violations:
        print("GATE 4 FAILED: OpenClaw core or TIA bridge in staged scope:")
        for v in violations:
            print(v)
        return False

    print("GATE 4: no OpenClaw core or TIA C# in staged scope")
    return True


def main():
    print("=" * 50)
    print("WESLR Release Gate V1")
    print("=" * 50)
    print()

    g1 = _run_harness()
    print()
    g2 = _check_git_scope()
    print()
    g3 = _check_execution_allowed()
    print()
    g4 = _check_openclaw_tia()
    print()
    print("=" * 50)

    if g1 and g2 and g3 and g4:
        print("WESLR_RELEASE_GATE_V1_OK")
        return 0
    else:
        print("RELEASE_GATE_V1_FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())