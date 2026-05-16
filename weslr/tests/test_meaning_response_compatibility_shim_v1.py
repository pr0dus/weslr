"""Tests for the legacy meaning/obligation aggregate import shim."""

from pathlib import Path


def test_compatibility_shim_reexports_callable_functions():
    from weslr.meaning_vector_response_obligation import (
        analyze_meaning,
        determine_response_obligation,
    )

    assert callable(analyze_meaning)
    assert callable(determine_response_obligation)


def test_compatibility_shim_can_analyze_meaning_and_determine_obligation():
    from weslr.meaning_vector_response_obligation import (
        analyze_meaning,
        determine_response_obligation,
    )

    meaning = analyze_meaning("What are you?")
    obligation = determine_response_obligation(meaning)

    assert meaning is not None
    assert hasattr(meaning, "primary_speech_act")
    assert hasattr(meaning, "confidence")
    assert obligation is not None
    assert hasattr(obligation, "obligation_type")
    assert hasattr(obligation, "required_state")


def test_split_modules_still_import_directly():
    from weslr.linguistic_meaning import analyze_meaning
    from weslr.response_obligation import determine_response_obligation

    assert callable(analyze_meaning)
    assert callable(determine_response_obligation)


def test_shim_does_not_create_weslr_state_or_persist_raw_text(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    from weslr.meaning_vector_response_obligation import (
        analyze_meaning,
        determine_response_obligation,
    )

    meaning = analyze_meaning("What are you?")
    determine_response_obligation(meaning)

    assert not (tmp_path / ".weslr").exists()
    persisted_files = [p for p in tmp_path.rglob("*") if p.is_file()]
    assert persisted_files == []


def test_shim_file_contains_no_model_search_or_advisor_imports():
    root = Path(__file__).resolve().parents[2]
    shim_text = (root / "weslr" / "meaning_vector_response_obligation.py").read_text()

    forbidden_markers = [
        "openai",
        "anthropic",
        "advisor",
        "web_search",
        "requests",
        "subprocess",
        "score_candidate",
        "rank",
    ]
    lowered = shim_text.lower()

    for marker in forbidden_markers:
        assert marker not in lowered
