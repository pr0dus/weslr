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
  G5 — Handler registry metadata completeness
"""

import subprocess
import sys
import pathlib
import re

_workspace = pathlib.Path(__file__).resolve().parents[2]
_harness = _workspace / "weslr" / "tests" / "test_harness_v1.py"
_atomic_helper_approval_doc = "docs/WESLR_LOGICAL_FORM_NORMALIZER_ATOMIC_HELPERS_APPROVAL_V1.md"
_atomic_helper_required_markers = {
    "APPROVE_ATOMIC_EXTRACTION_HELPERS_ONLY",
    "operator_approved_helper_phase",
    "execution_allowed = false",
    "official_score_claimed = false",
}
_predicate_helper_approval_doc = "docs/WESLR_LOGICAL_FORM_NORMALIZER_PREDICATE_HELPERS_APPROVAL_V1.md"
_predicate_helper_required_markers = {
    "APPROVE_PREDICATE_DECOMPOSITION_HELPERS_ONLY",
    "operator_approved_helper_phase",
    "execution_allowed = false",
    "official_score_claimed = false",
}


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


def _doc_with_markers_is_valid(doc_rel_path, required_markers):
    doc_path = _workspace / doc_rel_path
    if not doc_path.exists():
        return False
    try:
        text = doc_path.read_text(encoding="utf-8")
    except Exception:
        return False
    return all(marker in text for marker in required_markers)


def _atomic_helper_approval_doc_is_valid():
    return _doc_with_markers_is_valid(_atomic_helper_approval_doc, _atomic_helper_required_markers)


def _predicate_helper_approval_doc_is_valid():
    return _doc_with_markers_is_valid(_predicate_helper_approval_doc, _predicate_helper_required_markers)


def _check_git_scope():
    """Gate 2 — Check that staged files are within allowed scope.
    
    Allowed paths:
      - weslr/** (any file inside weslr/)
      - interpretation.py
      - docs/WESLR_LOGICAL_FORM_NORMALIZER_ATOMIC_HELPERS_APPROVAL_V1.md only when
        the operator-approved helper-phase markers are present
      - docs/WESLR_LOGICAL_FORM_NORMALIZER_PREDICATE_HELPERS_APPROVAL_V1.md only when
        the operator-approved predicate-helper markers are present
    
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
    approval_doc_valid = _atomic_helper_approval_doc_is_valid()
    predicate_approval_doc_valid = _predicate_helper_approval_doc_is_valid()
    for path in staged:
        for prefix in FORBIDDEN_PREFIXES:
            if path.startswith(prefix):
                violations.append(f"  forbidden prefix {prefix!r}: {path}")
        if any(path.endswith(ext) for ext in FORBIDDEN_EXTENSIONS):
            violations.append(f"  forbidden extension: {path}")

        allowed = path.startswith("weslr/") or path == "interpretation.py"
        if path == _atomic_helper_approval_doc:
            allowed = approval_doc_valid
            if not approval_doc_valid:
                violations.append(f"  approval doc missing required markers: {path}")
        if path == _predicate_helper_approval_doc:
            allowed = predicate_approval_doc_valid
            if not predicate_approval_doc_valid:
                violations.append(f"  approval doc missing required markers: {path}")

        if not allowed:
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


def _check_handler_registry():
    """Gate 5 — Handler registry has complete write-metadata fields.
    
    Verifies every registry entry has write_paths, side_effects, write_guard.
    For entries with read_only=True, write_paths and side_effects must be empty.
    """
    import sys as _sys
    handlers_path = _workspace / "weslr" / "deterministic_handlers.py"
    # Use separate import path so we don't pollute the gate's sys.path permanently
    _gate_path = str(_workspace)
    _orig_path = sys.path.copy()
    if _gate_path not in sys.path:
        sys.path.insert(0, _gate_path)
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("deterministic_handlers", str(handlers_path))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        registry = mod.HANDLER_REGISTRY
    except Exception as e:
        print(f"GATE 5 FAILED: could not import HANDLER_REGISTRY: {e}")
        return False
    finally:
        sys.path[:] = _orig_path

    violations = []
    for entry in registry:
        entry_id = entry.get("id", "<unknown>")
        read_only = entry.get("read_only", False)

        for field in ("write_paths", "side_effects", "write_guard"):
            if field not in entry:
                violations.append(f"  {entry_id}: missing field {field!r}")

        if read_only:
            if entry.get("write_paths", []) != []:
                violations.append(f"  {entry_id}: read_only=True but write_paths={entry.get('write_paths')}")
            if entry.get("side_effects", []) != []:
                violations.append(f"  {entry_id}: read_only=True but side_effects={entry.get('side_effects')}")

    if violations:
        print("GATE 5 FAILED: handler registry metadata issues:")
        for v in violations:
            print(v)
        return False

    print(f"GATE 5: {len(registry)} registry entries — all have write_paths, side_effects, write_guard")
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
    g5 = _check_handler_registry()
    print()
    print("=" * 50)

    if g1 and g2 and g3 and g4 and g5:
        print("WESLR_RELEASE_GATE_V1_OK")
        return 0
    else:
        print("RELEASE_GATE_V1_FAILED")
        return 1


if __name__ == "__main__":
    sys.exit(main())