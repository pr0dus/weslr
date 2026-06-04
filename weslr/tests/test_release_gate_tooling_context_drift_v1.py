#!/usr/bin/env python3
"""Tests for release-gate tooling context drift hardening V1."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from weslr.tests.release_gate_v1 import (
    _is_broad_allowlist_pattern_v1,
    _public_doc_tooling_reference_cleanup_docs,
    _validate_exact_file_allowlist_entries_v1,
)

ROOT = Path(__file__).resolve().parents[2]
RELEASE_GATE = ROOT / "weslr" / "tests" / "release_gate_v1.py"

BROAD_ALLOWLIST_PATTERNS = [
    "docs/*",
    "docs/**",
    "docs/",
    "weslr/*",
    "weslr/**",
    "weslr/",
    "tests/*",
    "tests/**",
    "weslr/tests/*",
    "weslr/tests/**",
    "*.md",
    "*.py",
    "**/*.md",
    "**/*.py",
    "docs/one?",
    "docs/[abc].md",
    "docs/file].md",
]

EXACT_FILE_ALLOWLIST_ENTRIES = [
    "docs/WESLR_RELEASE_GATE_TOOLING_CONTEXT_DRIFT_HARDENING_V1.md",
    "docs/WESLR_RELEASE_GATE_TOOLING_CONTEXT_DRIFT_HARDENING_REVIEW_V1.md",
    "docs/WESLR_RELEASE_GATE_TOOLING_CONTEXT_DRIFT_HARDENING_IMPLEMENTATION_PLAN_V1.md",
    "docs/WESLR_RELEASE_GATE_TOOLING_CONTEXT_DRIFT_HARDENING_IMPLEMENTATION_PLAN_REVIEW_V1.md",
    "weslr/tests/release_gate_v1.py",
]


def test_current_release_gate_exact_allowlist_entries_remain_exact():
    assert _validate_exact_file_allowlist_entries_v1(_public_doc_tooling_reference_cleanup_docs) == []


@pytest.mark.parametrize("entry", BROAD_ALLOWLIST_PATTERNS)
def test_broad_allowlist_patterns_are_rejected(entry: str):
    assert _is_broad_allowlist_pattern_v1(entry)


@pytest.mark.parametrize("entry", EXACT_FILE_ALLOWLIST_ENTRIES)
def test_exact_file_allowlist_entries_are_accepted(entry: str):
    assert not _is_broad_allowlist_pattern_v1(entry)


@pytest.mark.parametrize("entry", [
    "docs/*",
    "weslr/**",
    "*.md",
    "docs/",
])
def test_validator_reports_broad_entries(entry: str):
    assert _validate_exact_file_allowlist_entries_v1([entry]) == [entry]


def test_release_gate_file_contains_protected_boundary_terms():
    text = RELEASE_GATE.read_text(encoding="utf-8")
    for phrase in ("hidden prompt", "answer keys", "protected material"):
        assert phrase in text


def test_current_repository_release_gate_still_passes():
    gate = subprocess.run(
        [sys.executable, "weslr/tests/release_gate_v1.py"],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
        check=True,
    )
    assert "WESLR_RELEASE_GATE_V1_OK" in gate.stdout

    release_check = subprocess.run(
        ["bash", "scripts/weslr_release_check.sh"],
        cwd=str(ROOT),
        text=True,
        capture_output=True,
        check=True,
    )
    assert "WESLR_RELEASE_CHECK_OK" in release_check.stdout
