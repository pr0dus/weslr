"""Tests for WESLR who-said-that foundation canon docs V1.

Lightweight document checks only. This file intentionally avoids subprocesses.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FOUNDATION = ROOT / "docs" / "WESLR_WHO_SAID_THAT_FOUNDATION_CANON_V1.md"
DRY_RUN = ROOT / "docs" / "WESLR_WHO_SAID_THAT_DRY_RUN_VERTICAL_SLICE_CHECKPOINT_V1.md"
READINESS = ROOT / "docs" / "WESLR_WHO_SAID_THAT_RUNTIME_READINESS_REVIEW_V1.md"
DOCS = (FOUNDATION, DRY_RUN, READINESS)


def _read(path: Path) -> str:
    assert path.exists(), f"missing required doc: {path}"
    return path.read_text(encoding="utf-8")


def _lower(text: str) -> str:
    return text.lower().replace("’", "'").replace("“", '"').replace("”", '"')


def test_all_three_docs_exist() -> None:
    for path in DOCS:
        assert path.exists(), f"missing doc: {path}"


def test_foundation_canon_classifies_scope_and_components() -> None:
    text = _read(FOUNDATION)
    lowered = _lower(text)

    assert "canon_checkpoint" in text
    assert "foundation_only" in text
    assert "WhoSaidThatQueryIntent" in text
    assert "WhoSaidThatAnswer" in text
    assert "parserless resolver" in lowered
    assert "no_runtime_integration" in text or "no runtime integration" in lowered
    assert "no unsupported \"i said it\"" in lowered


def test_vertical_slice_checkpoint_classifies_dry_run_and_chain() -> None:
    text = _read(DRY_RUN)
    lowered = _lower(text)

    assert "dry_run_only" in text
    assert "fake chat metadata → chat routing helper → runtime query helper" in text
    assert "parserless resolver → WhoSaidThatAnswer → dry-run result" in text
    assert "unclear messages fall through" in lowered
    assert "fake llm-assisted records disclose provider/model" in lowered
    assert "unknown_unattributed" in text


def test_readiness_review_lists_ready_not_ready_and_risks() -> None:
    text = _read(READINESS)
    lowered = _lower(text)

    assert "readiness_review_only" in text
    assert "## What is ready" in text
    assert "## What is not ready" in text
    assert "schemas" in lowered
    assert "helpers" in lowered
    assert "dry-run vertical slice" in lowered
    assert "live chat responder routing" in lowered
    assert "real attribution log runtime lookup" in lowered
    assert "false ownership claims" in lowered


def test_all_docs_forbid_log_and_queue_writes_in_this_phase() -> None:
    for path in DOCS:
        lowered = _lower(_read(path))
        assert "no log writes" in lowered or "no_log_writes" in lowered
        assert "no queue writes" in lowered or "no_queue_writes" in lowered


def test_all_docs_forbid_answer_truth_soundness_and_official_score_claims() -> None:
    for path in DOCS:
        lowered = _lower(_read(path))
        assert "no answer selection/truth/soundness/official score claims" in lowered


def test_docs_remain_foundation_or_readiness_only_without_live_claims() -> None:
    foundation = _lower(_read(FOUNDATION))
    dry_run = _lower(_read(DRY_RUN))
    readiness = _lower(_read(READINESS))

    assert "cannot yet answer live runtime" in foundation
    assert "not live runtime behavior" in dry_run
    assert "does not authorize wiring" in readiness
    assert "no live runtime capability should be claimed" in readiness
