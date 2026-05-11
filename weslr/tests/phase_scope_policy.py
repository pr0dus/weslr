from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
APPROVAL_DOC = "docs/WESLR_LOGICAL_FORM_NORMALIZER_ATOMIC_HELPERS_APPROVAL_V1.md"

APPROVED_LOGICAL_FORM_NORMALIZER_ATOMIC_HELPER_FILES = {
    "weslr/logical_form_normalizer.py",
    "weslr/tests/phase_scope_policy.py",
    "weslr/tests/release_gate_v1.py",
    "weslr/tests/test_logical_form_normalizer_atomic_helpers_v1.py",
    "docs/WESLR_LOGICAL_FORM_NORMALIZER_ATOMIC_HELPERS_APPROVAL_V1.md",
    "weslr/tests/test_logical_form_normalizer_atomic_helpers_approval_v1.py",
    "weslr/tests/test_logical_form_normalizer_v1_1_revision.py",
    "weslr/tests/test_logical_form_normalizer_helper_diagnostic_v1.py",
    "weslr/tests/test_formal_logic_normalization_governed_proposal_v1.py",
    "weslr/tests/test_logical_form_normalizer_v1_1_schema_extension.py",
    "weslr/tests/test_logical_form_normalizer_schema_v1.py",
    "weslr/tests/test_logical_form_normalizer_helpers_v1.py",
}

FORBIDDEN_PATHS = {
    "weslr/formal_logic_parser.py",
    "weslr/formal_logic_solver.py",
    "weslr/mcq_answer_formatting.py",
    "weslr/evals/official_mcq_adapter.py",
}

FORBIDDEN_PREFIXES = (
    "runtime/",
    "chat/",
    "weslr/runtime/",
    "weslr/chat/",
    "tia",
    "c#/",
    "industrial",
)


def _git(*args: str) -> str:
    proc = subprocess.run(
        ["git", *args],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        check=True,
    )
    return proc.stdout


def _status_path_from_line(line: str) -> set[str]:
    payload = line[3:].strip()
    if not payload:
        return set()
    if " -> " in payload:
        left, right = payload.split(" -> ", 1)
        return {left.strip(), right.strip()}
    return {payload}


def read_changed_files() -> set[str]:
    changed = {line.strip() for line in _git("diff", "--name-only").splitlines() if line.strip()}
    status_output = _git("status", "--short")
    for line in status_output.splitlines():
        if not line.strip():
            continue
        changed.update(_status_path_from_line(line))
    return changed


def approval_doc_is_valid() -> bool:
    path = ROOT / APPROVAL_DOC
    if not path.exists():
        return False
    text = path.read_text(encoding="utf-8")
    required = {
        "APPROVE_ATOMIC_EXTRACTION_HELPERS_ONLY",
        "operator_approved_helper_phase",
        "execution_allowed = false",
        "official_score_claimed = false",
    }
    return all(term in text for term in required)


def assert_logical_form_normalizer_atomic_helper_phase_allowed(testcase):
    testcase.assertTrue(approval_doc_is_valid(), f"approval doc invalid: {APPROVAL_DOC}")
    changed = read_changed_files()
    forbidden_hits = {
        path
        for path in changed
        if path in FORBIDDEN_PATHS or any(path.lower().startswith(prefix) for prefix in FORBIDDEN_PREFIXES)
    }
    testcase.assertEqual(set(), forbidden_hits)
    disallowed = changed - APPROVED_LOGICAL_FORM_NORMALIZER_ATOMIC_HELPER_FILES
    testcase.assertEqual(set(), disallowed)
