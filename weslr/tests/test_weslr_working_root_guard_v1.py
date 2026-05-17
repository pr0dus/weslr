"""Test WESLR working root guard artifacts.

Lightweight tests that verify the guard files exist and contain
the expected markers.  Does not depend on current git state.
"""

from __future__ import annotations

import sys
from pathlib import Path

_repo_root = Path(__file__).resolve().parents[2]
if str(_repo_root) not in sys.path:
    sys.path.insert(0, str(_repo_root))

import pytest


def _read_text(path: Path) -> str:
    if not path.exists():
        pytest.fail(f"Required guard file missing: {path}")
    return path.read_text(encoding="utf-8")


class TestGuardScript:
    """Tests for scripts/weslr_assert_correct_repo.sh"""

    def test_script_exists(self) -> None:
        path = _repo_root / "scripts" / "weslr_assert_correct_repo.sh"
        assert path.exists(), f"Guard script missing: {path}"

    def test_script_contains_expected_repo_path(self) -> None:
        text = _read_text(_repo_root / "scripts" / "weslr_assert_correct_repo.sh")
        assert "weslr-pr47-clean" in text
        assert "/data/data/com.termux/files/home/weslr-pr47-clean" in text

    def test_script_contains_blocked_by_boundary(self) -> None:
        text = _read_text(_repo_root / "scripts" / "weslr_assert_correct_repo.sh")
        assert "BLOCKED_BY_BOUNDARY" in text

    def test_script_contains_ok_message(self) -> None:
        text = _read_text(_repo_root / "scripts" / "weslr_assert_correct_repo.sh")
        assert "WESLR_CORRECT_REPO_OK" in text

    def test_script_contains_branch_override_env(self) -> None:
        text = _read_text(_repo_root / "scripts" / "weslr_assert_correct_repo.sh")
        assert "WESLR_EXPECTED_BRANCH" in text

    def test_script_uses_set_euo(self) -> None:
        text = _read_text(_repo_root / "scripts" / "weslr_assert_correct_repo.sh")
        assert "set -euo pipefail" in text

    def test_script_is_executable(self) -> None:
        path = _repo_root / "scripts" / "weslr_assert_correct_repo.sh"
        import stat

        mode = path.stat().st_mode
        assert mode & stat.S_IXUSR, f"Guard script is not executable: {path}"


class TestGuardDoc:
    """Tests for WESLR_WORKING_ROOT.md"""

    def test_doc_exists(self) -> None:
        path = _repo_root / "WESLR_WORKING_ROOT.md"
        assert path.exists(), f"Guard doc missing: {path}"

    def test_doc_mentions_openclaw_workspace_is_not_repo(self) -> None:
        text = _read_text(_repo_root / "WESLR_WORKING_ROOT.md")
        assert ".openclaw/workspace" in text
        assert "NOT" in text or "not" in text.lower()

    def test_doc_mentions_correct_repo_path(self) -> None:
        text = _read_text(_repo_root / "WESLR_WORKING_ROOT.md")
        assert "/data/data/com.termux/files/home/weslr-pr47-clean" in text

    def test_doc_mentions_master_branch(self) -> None:
        text = _read_text(_repo_root / "WESLR_WORKING_ROOT.md")
        assert "master" in text

    def test_doc_mentions_bd7a54f_accident(self) -> None:
        text = _read_text(_repo_root / "WESLR_WORKING_ROOT.md")
        assert "bd7a54f" in text
