"""Tests for WESLR ambient voice hook foundation canon docs V1.

Lightweight document checks only. This file intentionally avoids subprocesses.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CANON = ROOT / "docs" / "WESLR_AMBIENT_VOICE_PROVENANCE_HOOK_FOUNDATION_CANON_V1.md"
CHECKPOINT = ROOT / "docs" / "WESLR_AMBIENT_VOICE_PRE_POST_SPEAK_HOOK_CHECKPOINT_V1.md"
DOCS = (CANON, CHECKPOINT)


def _read(path: Path) -> str:
    assert path.exists(), f"missing required doc: {path}"
    return path.read_text(encoding="utf-8")


def _lower(text: str) -> str:
    return text.lower().replace("’", "'").replace("“", '"').replace("”", '"')


def test_both_docs_exist() -> None:
    for path in DOCS:
        assert path.exists(), f"missing doc: {path}"


def test_foundation_canon_classifies_scope_and_names_hooks() -> None:
    text = _read(CANON)
    lowered = _lower(text)

    assert "canon_checkpoint" in text
    assert "foundation_only" in text
    assert "no_runtime_integration" in text
    assert "no_voice_wiring" in text
    assert "pre-speak hook" in lowered
    assert "post-speak hook" in lowered


def test_foundation_canon_forbids_speech_and_log_behavior() -> None:
    lowered = _lower(_read(CANON))

    assert "no attribution log writes" in lowered
    assert "no actual speech triggering" in lowered
    assert "not wired into voice gateway" in lowered
    assert "not wired into ambient loop" in lowered
    assert "not wired into tts/stt" in lowered
    assert "cannot yet produce live attribution records" in lowered


def test_pre_post_checkpoint_records_required_behaviors() -> None:
    text = _read(CHECKPOINT)
    lowered = _lower(text)

    assert "pre_post_hook_foundation" in text
    assert "pre-speak blocks missing attribution/provenance/trace refs" in lowered
    assert "records success/failure/blocked state" in lowered
    assert "forbids ownership claim when speech was not emitted" in lowered
    assert "future live attribution log can later feed the who-said-that lookup/resolver stack" in lowered


def test_both_docs_forbid_answer_truth_soundness_and_official_score_claims() -> None:
    for path in DOCS:
        lowered = _lower(_read(path))
        assert "no answer selection/truth/soundness/official score claims" in lowered


def test_both_docs_forbid_log_queue_runtime_and_voice_wiring() -> None:
    for path in DOCS:
        lowered = _lower(_read(path))
        assert "no log writes" in lowered or "no_log_writes" in lowered
        assert "no attribution log writes" in lowered
        assert "no queue writes" in lowered or "no_queue_writes" in lowered
        assert "no runtime" in lowered or "no_runtime_integration" in lowered
        assert "no voice" in lowered or "no_voice_wiring" in lowered


def test_docs_remain_foundation_only_without_live_claims() -> None:
    canon = _lower(_read(CANON))
    checkpoint = _lower(_read(CHECKPOINT))

    assert "foundation-only" in canon or "foundation_only" in canon
    assert "in-memory only" in checkpoint
    assert "does not authorize live voice capability" in checkpoint
    assert "live voice gateway wiring" in canon
