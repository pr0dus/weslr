# test_surface_to_spine_bridge.py — Tests for Surface-to-Spine Bridge, Slice 1
# Artifact-originated weakness signal -> Step 1 inadequacy event
#
# What tests verify:
# - Preview mode: no writes (reads only, no record_inadequacy_event called)
# - Confirm mode: one inadequacy event recorded in events JSONL
# - Invalid artifact ID: rejected
# - Bridge object shape: correct structure and field values
# - No side effects: interests.json, threads.json unchanged after run
# - Preservation: existing thread/relevance/suggestion/interest tests still pass

from __future__ import annotations

import json
import tempfile
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

# Add BASE_DIR for imports
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

import pytest

from weslr.surface_to_spine_bridge import (
    BRIDGE_VERSION,
    SURFACE_TYPE,
    URGENCY_RUNTIME_STATE_MAP,
    SurfaceBridgeObject,
    ArtifactWeaknessPayload,
    ProvenanceRecord,
    BridgeValidationError,
    build_artifact_bridge_object,
    validate_bridge_object,
    bridge_to_inadequacy_metadata,
    preview_bridge,
    confirm_bridge,
    main as bridge_main,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def temp_inadequacy_events(tmp_path):
    """Temp inadequacy events file for isolation."""
    from weslr import inadequacy_persistence as isp
    original_path = isp.STORAGE_PATH
    temp_path = tmp_path / "test_inadequacy_events.jsonl"
    isp.STORAGE_PATH = temp_path
    yield temp_path
    isp.STORAGE_PATH = original_path


@pytest.fixture
def empty_artifact_meta(tmp_path):
    """Minimal artifact metadata for testing without real artifact files."""
    return {
        "id": "test-artifact-001",
        "title": "Test Research Artifact",
        "category": "research",
        "niche_theme": "governance",
        "internal_score": 0.6,
        "human_proposed_score": 0.6,
        "opportunity_score": 0.6,
        "deployment_effort_score": 0.3,
        "buyer_clarity_score": 0.7,
        "thin_artifact_penalty": 0.0,
        "description_mismatch_penalty": 0.0,
        "proof_signals": {
            "human_approvals": 0,
            "handoff_acceptances": 0,
            "real_usage_hits": 0,
        },
        "external_validation_state": "unvalidated",
    }


# ---------------------------------------------------------------------------
# Test: Bridge object shape
# ---------------------------------------------------------------------------

def test_bridge_object_to_dict_roundtrip():
    """SurfaceBridgeObject serializes and deserializes correctly."""
    provenance = ProvenanceRecord(
        original_item_id="artifact-001",
        original_item_type="artifact",
        confidence=0.7,
        urgency="high",
    )
    payload = ArtifactWeaknessPayload(
        artifact_id="artifact-001",
        internal_strength=["strong internal quality 0.65"],
        external_proof=[],
        risk_count=1,
        recurring_limitation="no durable external proof",
    )
    bridge = SurfaceBridgeObject(
        signal_id="bridge_abc12345",
        source_surface=SURFACE_TYPE,
        surface_ref="artifact-001",
        created_at="2026-04-21T10:00:00Z",
        operator_triggered=True,
        operator_trigger_id="test-operator",
        payload=payload,
        provenance=provenance,
    )

    d = bridge.to_dict()
    restored = SurfaceBridgeObject.from_dict(d)

    assert restored.signal_id == bridge.signal_id
    assert restored.source_surface == bridge.source_surface
    assert restored.surface_ref == bridge.surface_ref
    assert restored.operator_triggered == bridge.operator_triggered
    assert restored.payload.artifact_id == bridge.payload.artifact_id
    assert restored.provenance.confidence == bridge.provenance.confidence
    assert restored.provenance.urgency == bridge.provenance.urgency


def test_bridge_version_is_1():
    """BRIDGE_VERSION constant is '1.0'."""
    assert BRIDGE_VERSION == "1.0"


def test_surface_type_is_artifact_weakness():
    """SURFACE_TYPE constant is 'artifact_weakness'."""
    assert SURFACE_TYPE == "artifact_weakness"


def test_urgency_runtime_state_map():
    """URGENCY_RUNTIME_STATE_MAP has correct mappings."""
    assert URGENCY_RUNTIME_STATE_MAP == {
        "high": "unavailable",
        "medium": "degraded",
        "low": "fallback_used",
    }


# ---------------------------------------------------------------------------
# Test: Validation rules
# ---------------------------------------------------------------------------

def test_validation_requires_signal_id():
    """Validation rejects bridge object missing signal_id."""
    provenance = ProvenanceRecord(
        original_item_id="a",
        original_item_type="artifact",
        confidence=0.5,
        urgency="medium",
    )
    bridge = SurfaceBridgeObject(
        signal_id="",  # Empty — should fail
        source_surface=SURFACE_TYPE,
        surface_ref="artifact-001",
        created_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        operator_triggered=True,
        operator_trigger_id="test",
        provenance=provenance,
    )
    errors = validate_bridge_object(bridge, "test")
    assert any("signal_id" in e for e in errors)


def test_validation_rejects_auto_trigger():
    """Validation rejects if operator_triggered is False."""
    provenance = ProvenanceRecord(
        original_item_id="a",
        original_item_type="artifact",
        confidence=0.5,
        urgency="medium",
    )
    bridge = SurfaceBridgeObject(
        signal_id="bridge_abc12345",
        source_surface=SURFACE_TYPE,
        surface_ref="artifact-001",
        created_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        operator_triggered=False,  # Auto-triggered — should fail
        operator_trigger_id="test",
        provenance=provenance,
    )
    errors = validate_bridge_object(bridge, "test")
    assert any("automatic" in e.lower() or "triggered" in e.lower() for e in errors)


def test_validation_rejects_unknown_source_surface():
    """Validation rejects unknown source_surface."""
    provenance = ProvenanceRecord(
        original_item_id="a",
        original_item_type="artifact",
        confidence=0.5,
        urgency="medium",
    )
    bridge = SurfaceBridgeObject(
        signal_id="bridge_abc12345",
        source_surface="unknown_surface",  # Not allowed in Slice 1
        surface_ref="artifact-001",
        created_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        operator_triggered=True,
        operator_trigger_id="test",
        provenance=provenance,
    )
    errors = validate_bridge_object(bridge, "test")
    assert any("source_surface" in e for e in errors)


def test_validation_rejects_stale_timestamp():
    """Validation rejects bridge object with timestamp older than 30 days."""
    provenance = ProvenanceRecord(
        original_item_id="a",
        original_item_type="artifact",
        confidence=0.5,
        urgency="medium",
    )
    bridge = SurfaceBridgeObject(
        signal_id="bridge_abc12345",
        source_surface=SURFACE_TYPE,
        surface_ref="artifact-001",
        created_at="2026-01-01T00:00:00Z",  # Stale — >30 days old
        operator_triggered=True,
        operator_trigger_id="test",
        provenance=provenance,
    )
    errors = validate_bridge_object(bridge, "test")
    assert any("stale" in e.lower() for e in errors)


def test_validation_rejects_invalid_confidence():
    """Validation rejects confidence outside 0.0-1.0."""
    provenance = ProvenanceRecord(
        original_item_id="a",
        original_item_type="artifact",
        confidence=1.5,  # Out of range
        urgency="medium",
    )
    bridge = SurfaceBridgeObject(
        signal_id="bridge_abc12345",
        source_surface=SURFACE_TYPE,
        surface_ref="artifact-001",
        created_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        operator_triggered=True,
        operator_trigger_id="test",
        provenance=provenance,
    )
    errors = validate_bridge_object(bridge, "test")
    assert any("confidence" in e.lower() for e in errors)


def test_validation_rejects_invalid_urgency():
    """Validation rejects urgency not in {low, medium, high}."""
    provenance = ProvenanceRecord(
        original_item_id="a",
        original_item_type="artifact",
        confidence=0.5,
        urgency="super-high",  # Invalid
    )
    bridge = SurfaceBridgeObject(
        signal_id="bridge_abc12345",
        source_surface=SURFACE_TYPE,
        surface_ref="artifact-001",
        created_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        operator_triggered=True,
        operator_trigger_id="test",
        provenance=provenance,
    )
    errors = validate_bridge_object(bridge, "test")
    assert any("urgency" in e.lower() for e in errors)


# ---------------------------------------------------------------------------
# Test: bridge_to_inadequacy_metadata mapping
# ---------------------------------------------------------------------------

def test_bridge_to_inadequacy_high_urgency():
    """High urgency maps to runtime_state='unavailable'."""
    provenance = ProvenanceRecord(
        original_item_id="artifact-001",
        original_item_type="artifact",
        confidence=0.6,
        urgency="high",
    )
    payload = ArtifactWeaknessPayload(
        artifact_id="artifact-001",
        internal_strength=["strong internal quality 0.65"],
        external_proof=[],
        risk_count=2,
        recurring_limitation="weak external proof",
    )
    bridge = SurfaceBridgeObject(
        signal_id="bridge_abc12345",
        source_surface=SURFACE_TYPE,
        surface_ref="artifact-001",
        created_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        operator_triggered=True,
        operator_trigger_id="test-op",
        payload=payload,
        provenance=provenance,
    )
    metadata = bridge_to_inadequacy_metadata(bridge)
    assert metadata["runtime_state"] == "unavailable"
    assert metadata["source"] == "surface_bridge"
    assert metadata["_bridge_source_surface"] == SURFACE_TYPE
    assert metadata["_bridge_operator_trigger_id"] == "test-op"


def test_bridge_to_inadequacy_medium_urgency():
    """Medium urgency maps to runtime_state='degraded'."""
    provenance = ProvenanceRecord(
        original_item_id="artifact-001",
        original_item_type="artifact",
        confidence=0.5,
        urgency="medium",
    )
    payload = ArtifactWeaknessPayload(
        artifact_id="artifact-001",
        internal_strength=["strong internal quality 0.65"],
        external_proof=["human approval recorded"],
        risk_count=0,
        recurring_limitation=None,
    )
    bridge = SurfaceBridgeObject(
        signal_id="bridge_abc12345",
        source_surface=SURFACE_TYPE,
        surface_ref="artifact-001",
        created_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        operator_triggered=True,
        operator_trigger_id="test-op",
        payload=payload,
        provenance=provenance,
    )
    metadata = bridge_to_inadequacy_metadata(bridge)
    assert metadata["runtime_state"] == "degraded"


def test_bridge_to_inadequacy_low_urgency():
    """Low urgency maps to runtime_state='fallback_used'."""
    provenance = ProvenanceRecord(
        original_item_id="artifact-001",
        original_item_type="artifact",
        confidence=0.3,
        urgency="low",
    )
    payload = ArtifactWeaknessPayload(
        artifact_id="artifact-001",
        internal_strength=["early artifact with partial internal signals"],
        external_proof=["no durable external proof yet"],
        risk_count=0,
        recurring_limitation=None,
    )
    bridge = SurfaceBridgeObject(
        signal_id="bridge_abc12345",
        source_surface=SURFACE_TYPE,
        surface_ref="artifact-001",
        created_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        operator_triggered=True,
        operator_trigger_id="test-op",
        payload=payload,
        provenance=provenance,
    )
    metadata = bridge_to_inadequacy_metadata(bridge)
    assert metadata["runtime_state"] == "fallback_used"


# ---------------------------------------------------------------------------
# Test: Preview mode — no writes
# ---------------------------------------------------------------------------

def test_preview_mode_no_file_writes(temp_inadequacy_events, empty_artifact_meta):
    """Preview mode must not write any inadequacy events."""
    from unittest.mock import patch, MagicMock

    # Mock artifact loading to return our test metadata
    with patch("weslr.surface_to_spine_bridge.load_artifact_metadata") as mock_load:
        with patch("weslr.surface_to_spine_bridge.get_artifact_evaluation") as mock_eval:
            mock_load.return_value = empty_artifact_meta
            mock_eval.return_value = {
                "meta": empty_artifact_meta,
                "scored": empty_artifact_meta,
                "explainability": {
                    "internal_strength": ["strong internal quality 0.65"],
                    "external_proof": [],
                    "risks": ["no durable external proof yet"],
                    "next_actions": ["run validate/use"],
                },
                "proof": {"human_approvals": 0, "handoff_acceptances": 0, "real_usage_hits": 0},
            }

            # Read event count before
            before_count = temp_inadequacy_events.read_text().count("\n") if temp_inadequacy_events.exists() else 0

            result = preview_bridge("test-artifact-001", operator_trigger_id="test-op", urgency="high")

            # Read event count after
            after_count = temp_inadequacy_events.read_text().count("\n") if temp_inadequacy_events.exists() else 0

            assert result["mode"] == "preview"
            assert result["writes"] == []
            assert after_count == before_count, "Preview mode should not write any events"


# ---------------------------------------------------------------------------
# Test: Confirm mode — one event written
# ---------------------------------------------------------------------------

def test_confirm_mode_writes_one_event(temp_inadequacy_events, empty_artifact_meta):
    """Confirm mode must write exactly one inadequacy event."""
    from unittest.mock import patch, MagicMock

    with patch("weslr.surface_to_spine_bridge.load_artifact_metadata") as mock_load:
        with patch("weslr.surface_to_spine_bridge.get_artifact_evaluation") as mock_eval:
            mock_load.return_value = empty_artifact_meta
            mock_eval.return_value = {
                "meta": empty_artifact_meta,
                "scored": empty_artifact_meta,
                "explainability": {
                    "internal_strength": ["strong internal quality 0.65"],
                    "external_proof": [],
                    "risks": ["no durable external proof yet"],
                    "next_actions": ["run validate/use"],
                },
                "proof": {"human_approvals": 0, "handoff_acceptances": 0, "real_usage_hits": 0},
            }

            before_count = temp_inadequacy_events.read_text().count("\n") if temp_inadequacy_events.exists() else 0

            result = confirm_bridge("test-artifact-001", operator_trigger_id="test-op", urgency="high")

            after_count = temp_inadequacy_events.read_text().count("\n") if temp_inadequacy_events.exists() else 0

            assert result["mode"] == "confirmed"
            assert result["event_recorded"] is True
            assert after_count == before_count + 1, "Confirm mode should write exactly one event"

            # Verify the event content
            # Note: record_inadequacy_event hardcodes source="protected_core"
            # — this is the existing function behavior, not bridge behavior
            lines = temp_inadequacy_events.read_text().strip().split("\n")
            last_event = json.loads(lines[-1])
            assert last_event["source"] == "protected_core"  # existing function hardcodes this
            assert last_event["runtime_state"] == "unavailable"
            assert "request_fingerprint" in last_event  # signal_id stored for audit


# ---------------------------------------------------------------------------
# Test: No side effects on interests.json or threads.json
# ---------------------------------------------------------------------------

def test_no_side_effects_on_interests_json(temp_inadequacy_events, empty_artifact_meta, tmp_path):
    """Bridge must not write to interests.json or threads.json."""
    from unittest.mock import patch
    import shutil

    # Create temp copies of interests.json and threads.json to protect real files
    interests_path = Path("weslr/interests.json")
    threads_path = Path("weslr/threads.json")

    # Read originals if they exist
    interests_backup = interests_path.read_bytes() if interests_path.exists() else None
    threads_backup = threads_path.read_bytes() if threads_path.exists() else None

    try:
        with patch("weslr.surface_to_spine_bridge.load_artifact_metadata") as mock_load:
            with patch("weslr.surface_to_spine_bridge.get_artifact_evaluation") as mock_eval:
                mock_load.return_value = empty_artifact_meta
                mock_eval.return_value = {
                    "meta": empty_artifact_meta,
                    "scored": empty_artifact_meta,
                    "explainability": {
                        "internal_strength": ["strong internal quality 0.65"],
                        "external_proof": [],
                        "risks": ["no durable external proof yet"],
                        "next_actions": ["run validate/use"],
                    },
                    "proof": {"human_approvals": 0, "handoff_acceptances": 0, "real_usage_hits": 0},
                }

                # Read timestamps before
                interests_mtime_before = interests_path.stat().st_mtime if interests_path.exists() else None
                threads_mtime_before = threads_path.stat().st_mtime if threads_path.exists() else None

                # Run preview
                preview_bridge("test-artifact-001", operator_trigger_id="test-op", urgency="high")

                # Run confirm
                confirm_bridge("test-artifact-001", operator_trigger_id="test-op", urgency="high")

                # Check timestamps unchanged (or file not created if it didn't exist)
                interests_mtime_after = interests_path.stat().st_mtime if interests_path.exists() else None
                threads_mtime_after = threads_path.stat().st_mtime if threads_path.exists() else None

                assert interests_mtime_before == interests_mtime_after, "interests.json was modified"
                assert threads_mtime_before == threads_mtime_after, "threads.json was modified"

    finally:
        # Restore originals
        if interests_backup is not None:
            interests_path.write_bytes(interests_backup)
        else:
            interests_path.unlink(missing_ok=True)
        if threads_backup is not None:
            threads_path.write_bytes(threads_backup)
        else:
            threads_path.unlink(missing_ok=True)


# ---------------------------------------------------------------------------
# Test: CLI main entry
# ---------------------------------------------------------------------------

def test_cli_preview_mode(empty_artifact_meta, capsys):
    """CLI in preview mode (no --confirm) returns 0 and prints output."""
    from unittest.mock import patch

    with patch("weslr.surface_to_spine_bridge.load_artifact_metadata") as mock_load:
        with patch("weslr.surface_to_spine_bridge.get_artifact_evaluation") as mock_eval:
            mock_load.return_value = empty_artifact_meta
            mock_eval.return_value = {
                "meta": empty_artifact_meta,
                "scored": empty_artifact_meta,
                "explainability": {
                    "internal_strength": ["strong internal quality 0.65"],
                    "external_proof": [],
                    "risks": ["no durable external proof yet"],
                    "next_actions": ["run validate/use"],
                },
                "proof": {"human_approvals": 0, "handoff_acceptances": 0, "real_usage_hits": 0},
            }

            rc = bridge_main(["--from-artifact", "test-artifact-001"])
            assert rc == 0
            output = capsys.readouterr().out
            assert "PREVIEW" in output or "preview" in output.lower()


def test_cli_confirm_mode(empty_artifact_meta, temp_inadequacy_events, capsys):
    """CLI in confirm mode (--confirm) returns 0 and records event."""
    from unittest.mock import patch

    with patch("weslr.surface_to_spine_bridge.load_artifact_metadata") as mock_load:
        with patch("weslr.surface_to_spine_bridge.get_artifact_evaluation") as mock_eval:
            mock_load.return_value = empty_artifact_meta
            mock_eval.return_value = {
                "meta": empty_artifact_meta,
                "scored": empty_artifact_meta,
                "explainability": {
                    "internal_strength": ["strong internal quality 0.65"],
                    "external_proof": [],
                    "risks": ["no durable external proof yet"],
                    "next_actions": ["run validate/use"],
                },
                "proof": {"human_approvals": 0, "handoff_acceptances": 0, "real_usage_hits": 0},
            }

            before = temp_inadequacy_events.read_text().count("\n") if temp_inadequacy_events.exists() else 0
            rc = bridge_main(["--from-artifact", "test-artifact-001", "--confirm"])
            after = temp_inadequacy_events.read_text().count("\n") if temp_inadequacy_events.exists() else 0

            assert rc == 0
            assert after == before + 1


def test_cli_invalid_artifact_rejected(empty_artifact_meta, capsys):
    """CLI with non-existent artifact ID returns 1 and prints error."""
    from unittest.mock import patch, MagicMock

    with patch("weslr.surface_to_spine_bridge.load_artifact_metadata") as mock_load:
        mock_load.side_effect = BridgeValidationError("No artifact found with id: nonexistent-artifact")
        rc = bridge_main(["--from-artifact", "nonexistent-artifact"])
        assert rc == 1
        output = capsys.readouterr().err
        assert "nonexistent-artifact" in output


# ---------------------------------------------------------------------------
# Test: Preservation check — existing test files still pass
# ---------------------------------------------------------------------------

def test_preservation_no_threads_json_mutated(temp_inadequacy_events, empty_artifact_meta, tmp_path):
    """threads.json must not be created or mutated by bridge operations."""
    from unittest.mock import patch

    threads_path = Path("weslr/threads.json")
    threads_backup = threads_path.read_bytes() if threads_path.exists() else None

    try:
        with patch("weslr.surface_to_spine_bridge.load_artifact_metadata") as mock_load:
            with patch("weslr.surface_to_spine_bridge.get_artifact_evaluation") as mock_eval:
                mock_load.return_value = empty_artifact_meta
                mock_eval.return_value = {
                    "meta": empty_artifact_meta,
                    "scored": empty_artifact_meta,
                    "explainability": {
                        "internal_strength": ["strong internal quality 0.65"],
                        "external_proof": [],
                        "risks": [],
                        "next_actions": [],
                    },
                    "proof": {"human_approvals": 0, "handoff_acceptances": 0, "real_usage_hits": 0},
                }

                preview_bridge("test-artifact-001", operator_trigger_id="test-op")
                confirm_bridge("test-artifact-001", operator_trigger_id="test-op")

                # threads.json unchanged
                if threads_backup is not None:
                    assert threads_path.read_bytes() == threads_backup
                else:
                    assert not threads_path.exists()

    finally:
        if threads_backup is not None:
            threads_path.write_bytes(threads_backup)


# ---------------------------------------------------------------------------
# Test: No routing regressions
# ---------------------------------------------------------------------------

def test_no_routing_change_surface_type_equals_artifact_weakness():
    """SURFACE_TYPE must be artifact_weakness for Slice 1. No routing changes."""
    assert SURFACE_TYPE == "artifact_weakness"


def test_allowed_source_surfaces_in_slice1():
    """Slice 1 only allows artifact_weakness as source_surface."""
    allowed = {"artifact_weakness"}
    provenance = ProvenanceRecord(
        original_item_id="a",
        original_item_type="artifact",
        confidence=0.5,
        urgency="medium",
    )
    bridge = SurfaceBridgeObject(
        signal_id="bridge_abc12345",
        source_surface="suggestion_approval",  # Not allowed in Slice 1
        surface_ref="artifact-001",
        created_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        operator_triggered=True,
        operator_trigger_id="test",
        provenance=provenance,
    )
    errors = validate_bridge_object(bridge, "test")
    assert any("source_surface" in e for e in errors)


# ---------------------------------------------------------------------------
# Test: Proof-aware urgency
# ---------------------------------------------------------------------------

def test_urgency_lowered_by_human_approval(empty_artifact_meta):
    """human_approvals >= 1 lowers urgency from medium to low."""
    from unittest.mock import patch

    with patch("weslr.surface_to_spine_bridge.load_artifact_metadata") as mock_load:
        with patch("weslr.surface_to_spine_bridge.get_artifact_evaluation") as mock_eval:
            mock_load.return_value = empty_artifact_meta
            mock_eval.return_value = {
                "meta": empty_artifact_meta,
                "scored": empty_artifact_meta,
                "explainability": {
                    "internal_strength": ["strong internal quality 0.65"],
                    "external_proof": ["human approval recorded"],
                    "risks": [],
                    "next_actions": ["run validate/use"],
                },
                "proof": {"human_approvals": 1, "handoff_acceptances": 0, "real_usage_hits": 0},
            }
            # No recurring limitation risk → medium base, human_approval → low
            result = preview_bridge("test-artifact-001")
            assert result["urgency"] == "low"
            assert "human approval" in result.get("urgency_note", "")


def test_urgency_lowered_by_handoff_acceptance(empty_artifact_meta):
    """handoff_acceptances >= 1 lowers urgency from medium to low."""
    from unittest.mock import patch

    with patch("weslr.surface_to_spine_bridge.load_artifact_metadata") as mock_load:
        with patch("weslr.surface_to_spine_bridge.get_artifact_evaluation") as mock_eval:
            mock_load.return_value = empty_artifact_meta
            mock_eval.return_value = {
                "meta": empty_artifact_meta,
                "scored": empty_artifact_meta,
                "explainability": {
                    "internal_strength": ["strong internal quality 0.65"],
                    "external_proof": ["handoff acceptance recorded"],
                    "risks": [],
                    "next_actions": [],
                },
                "proof": {"human_approvals": 0, "handoff_acceptances": 1, "real_usage_hits": 0},
            }
            # No recurring limitation risk → medium base, handoff_acceptance → low
            result = preview_bridge("test-artifact-001")
            assert result["urgency"] == "low"
            assert "handoff acceptance" in result.get("urgency_note", "")


def test_urgency_lowered_by_real_usage(empty_artifact_meta):
    """real_usage_hits >= 1 lowers urgency from medium to low."""
    from unittest.mock import patch

    with patch("weslr.surface_to_spine_bridge.load_artifact_metadata") as mock_load:
        with patch("weslr.surface_to_spine_bridge.get_artifact_evaluation") as mock_eval:
            mock_load.return_value = empty_artifact_meta
            mock_eval.return_value = {
                "meta": empty_artifact_meta,
                "scored": empty_artifact_meta,
                "explainability": {
                    "internal_strength": ["strong internal quality 0.65"],
                    "external_proof": ["real usage recorded"],
                    "risks": [],
                    "next_actions": [],
                },
                "proof": {"human_approvals": 0, "handoff_acceptances": 0, "real_usage_hits": 1},
            }
            # No recurring limitation risk → medium base, real_usage → low
            result = preview_bridge("test-artifact-001")
            assert result["urgency"] == "low"
            assert "real usage" in result.get("urgency_note", "")


def test_urgency_not_lowered_for_no_proof_artifact(empty_artifact_meta):
    """Artifact with no proof signals and no recurring risk keeps medium urgency."""
    from unittest.mock import patch

    with patch("weslr.surface_to_spine_bridge.load_artifact_metadata") as mock_load:
        with patch("weslr.surface_to_spine_bridge.get_artifact_evaluation") as mock_eval:
            mock_load.return_value = empty_artifact_meta
            mock_eval.return_value = {
                "meta": empty_artifact_meta,
                "scored": empty_artifact_meta,
                "explainability": {
                    "internal_strength": ["strong internal quality 0.65"],
                    "external_proof": [],
                    "risks": [],
                    "next_actions": [],
                },
                "proof": {"human_approvals": 0, "handoff_acceptances": 0, "real_usage_hits": 0},
            }
            result = preview_bridge("test-artifact-001")
            # No recurring risk, no proof signals → medium urgency, no note
            assert result["urgency"] == "medium"
            assert result.get("urgency_note") in ("", None)


def test_urgency_medium_with_approval_lowered_to_low(empty_artifact_meta):
    """Medium urgency + proof signal → low (one level lower)."""
    from unittest.mock import patch

    with patch("weslr.surface_to_spine_bridge.load_artifact_metadata") as mock_load:
        with patch("weslr.surface_to_spine_bridge.get_artifact_evaluation") as mock_eval:
            mock_load.return_value = empty_artifact_meta
            mock_eval.return_value = {
                "meta": empty_artifact_meta,
                "scored": empty_artifact_meta,
                "explainability": {
                    "internal_strength": ["strong internal quality 0.65"],
                    "external_proof": ["human approval recorded"],
                    "risks": [],
                    "next_actions": [],
                },
                "proof": {"human_approvals": 1, "handoff_acceptances": 0, "real_usage_hits": 0},
            }
            result = preview_bridge("test-artifact-001")
            # no thin risk → medium base, human_approval → low
            assert result["urgency"] == "low"
            assert "human approval" in result.get("urgency_note", "")


def test_preview_shows_urgency_note(empty_artifact_meta, capsys):
    """Preview output includes urgency_note when urgency was lowered by proof."""
    from unittest.mock import patch

    with patch("weslr.surface_to_spine_bridge.load_artifact_metadata") as mock_load:
        with patch("weslr.surface_to_spine_bridge.get_artifact_evaluation") as mock_eval:
            mock_load.return_value = empty_artifact_meta
            mock_eval.return_value = {
                "meta": empty_artifact_meta,
                "scored": empty_artifact_meta,
                "explainability": {
                    "internal_strength": ["strong internal quality 0.65"],
                    "external_proof": ["human approval recorded"],
                    "risks": [],
                    "next_actions": [],
                },
                "proof": {"human_approvals": 1, "handoff_acceptances": 0, "real_usage_hits": 0},
            }
            rc = bridge_main(["--from-artifact", "test-artifact-001"])
            assert rc == 0
            output = capsys.readouterr().out
            assert "human approval" in output


def test_confidence_increases_with_proof_signals(empty_artifact_meta):
    """Confidence is boosted when proof signals are present."""
    from unittest.mock import patch

    with patch("weslr.surface_to_spine_bridge.load_artifact_metadata") as mock_load:
        with patch("weslr.surface_to_spine_bridge.get_artifact_evaluation") as mock_eval:
            mock_load.return_value = empty_artifact_meta
            mock_eval.return_value = {
                "meta": empty_artifact_meta,
                "scored": empty_artifact_meta,
                "explainability": {
                    "internal_strength": ["strong internal quality 0.65"],
                    "external_proof": [],
                    "risks": [],
                    "next_actions": [],
                },
                "proof": {"human_approvals": 1, "handoff_acceptances": 0, "real_usage_hits": 0},
            }
            result = preview_bridge("test-artifact-001")
            # base 0.5 + internal quality 0.1 + human approval 0.15 = 0.75
            assert result["confidence"] > 0.5


# ---------------------------------------------------------------------------
# Test: Urgency override
# ---------------------------------------------------------------------------

def test_explicit_urgency_override(empty_artifact_meta):
    """Explicit --urgency flag overrides auto-derived urgency."""
    from unittest.mock import patch

    with patch("weslr.surface_to_spine_bridge.load_artifact_metadata") as mock_load:
        with patch("weslr.surface_to_spine_bridge.get_artifact_evaluation") as mock_eval:
            mock_load.return_value = empty_artifact_meta
            mock_eval.return_value = {
                "meta": empty_artifact_meta,
                "scored": empty_artifact_meta,
                "explainability": {
                    "internal_strength": ["strong internal quality 0.65"],
                    "external_proof": ["human approval recorded"],
                    "risks": [],
                    "next_actions": [],
                },
                "proof": {"human_approvals": 1, "handoff_acceptances": 0, "real_usage_hits": 0},
            }

            result = preview_bridge("test-artifact-001", urgency="high")
            assert result["urgency"] == "high"

            result = preview_bridge("test-artifact-001", urgency="low")
            assert result["urgency"] == "low"
