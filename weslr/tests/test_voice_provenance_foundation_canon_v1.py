"""Tests for WESLR voice provenance foundation canon docs V1.

Lightweight document checks only. This file intentionally avoids subprocesses.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOC1 = ROOT / "docs" / "WESLR_VOICE_PROVENANCE_FOUNDATION_CANON_V1.md"
DOC2 = ROOT / "docs" / "WESLR_OUTPUT_PROVENANCE_AND_SOURCE_ATTRIBUTION_CHECKPOINT_V1.md"


def _read(path: Path) -> str:
    assert path.exists(), f"missing required doc: {path}"
    return path.read_text(encoding="utf-8")


def _lower(text: str) -> str:
    return text.lower().replace("’", "'").replace("“", '"').replace("”", '"')


def test_voice_provenance_foundation_canon_doc_exists_and_classifies_scope() -> None:
    text = _read(DOC1)

    assert "canon_checkpoint" in text
    assert "foundation_only" in text
    assert "no_runtime_integration" in text
    assert "VoiceSourceAttributionRecord" in text
    assert "VoiceAttributionLogEvent" in text


def test_voice_provenance_foundation_canon_safety_limits() -> None:
    text = _read(DOC1)
    lowered = _lower(text)

    assert "no raw spoken text by default" in lowered
    assert "no hidden llm/provider authority" in lowered
    assert "no unsupported \"i said it\"" in lowered
    assert "no_log_writes" in text or "no log writes" in lowered
    assert "cannot yet answer live spoken events" in lowered


def test_output_provenance_checkpoint_doc_exists_and_sets_authority_boundary() -> None:
    text = _read(DOC2)
    lowered = _lower(text)

    assert "canon_checkpoint" in text
    assert "OutputProvenanceEnvelope" in text
    assert "source registry dependency" in lowered
    assert "provenance records describe source, authority, and trigger" in lowered
    assert "they do not make truth claims by themselves" in lowered
    assert "unknown or unregistered source remains operator-review required" in lowered


def test_both_docs_forbid_answer_truth_soundness_and_official_score_claims() -> None:
    for path in (DOC1, DOC2):
        lowered = _lower(_read(path))
        assert "no answer selection/truth/soundness/official score claims" in lowered


def test_docs_remain_documentation_only_without_implementation_targets() -> None:
    for path in (DOC1, DOC2):
        lowered = _lower(_read(path))
        assert "no runtime integration" in lowered or "no_runtime_integration" in lowered
        assert "no voice wiring" in lowered or "no_voice_wiring" in lowered
        assert "no log writes" in lowered or "no_log_writes" in lowered
        assert "foundation-only" in lowered or "foundation_only" in lowered
