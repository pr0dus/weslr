"""Tests for WESLR source registry foundation canon docs V1.

Lightweight document checks only. This file intentionally avoids subprocesses.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
REGISTRY = ROOT / "docs" / "WESLR_SOURCE_REGISTRY_FOUNDATION_CANON_V1.md"
DETECTION = ROOT / "docs" / "WESLR_UNREGISTERED_SOURCE_DETECTION_CHECKPOINT_V1.md"
MAPPING = ROOT / "docs" / "WESLR_SOURCE_REGISTRY_REVIEW_QUEUE_MAPPING_CHECKPOINT_V1.md"
DOCS = (REGISTRY, DETECTION, MAPPING)


def _read(path: Path) -> str:
    assert path.exists(), f"missing required doc: {path}"
    return path.read_text(encoding="utf-8")


def _lower(text: str) -> str:
    return text.lower().replace("’", "'").replace("“", '"').replace("”", '"')


def test_all_three_docs_exist() -> None:
    for path in DOCS:
        assert path.exists(), f"missing doc: {path}"


def test_source_registry_canon_classifies_scope_and_components() -> None:
    text = _read(REGISTRY)
    lowered = _lower(text)

    assert "canon_checkpoint" in text
    assert "foundation_only" in text
    assert "ProvenanceSourceEntry" in text
    assert "ProvenanceSourceSafetyFlags" in text
    assert "initial source registry seed" in lowered
    assert "unknown/unregistered sources require operator review" in lowered
    assert "no automatic activation" in lowered


def test_detection_checkpoint_classifies_detection_foundation() -> None:
    text = _read(DETECTION)
    lowered = _lower(text)

    assert "detection_foundation_only" in text
    assert "unregistered source detection schema" in lowered
    assert "local helper classifiers" in lowered
    assert "finding/report summaries" in lowered
    assert "no repo scan automation" in lowered
    assert "no registry mutation" in lowered


def test_mapping_checkpoint_classifies_mapping_foundation() -> None:
    text = _read(MAPPING)
    lowered = _lower(text)

    assert "mapping_foundation_only" in text
    assert "maps unregistered-source findings to in-memory advisor review queue proposals" in lowered
    assert "suggestions only" in lowered
    assert "operator review" in lowered
    assert "no queue writes" in lowered


def test_all_docs_forbid_truth_soundness_and_official_score_authority() -> None:
    for path in DOCS:
        lowered = _lower(_read(path))
        assert "truth/soundness/official score" in lowered


def test_all_docs_forbid_runtime_persistence_queue_and_activation() -> None:
    for path in DOCS:
        lowered = _lower(_read(path))
        assert "no_runtime_integration" in lowered or "no runtime" in lowered
        assert "no_registry_persistence" in lowered or "no registry persistence" in lowered
        assert "no_queue_writes" in lowered or "no queue writes" in lowered
        assert "automatic activation" in lowered or "auto-activate" in lowered or "activation" in lowered


def test_docs_remain_foundation_only_without_live_claims() -> None:
    registry = _lower(_read(REGISTRY))
    detection = _lower(_read(DETECTION))
    mapping = _lower(_read(MAPPING))

    assert "does not activate providers" in registry
    assert "does not perform repo scan automation" in detection
    assert "not a source registration" in mapping
    assert "not an implementation of persistent queues" in mapping
