"""
test_artifact_quality_feedback.py

Tests for ARTIFACT QUALITY FEEDBACK LOOP v1 — Slice 1.

Covers:
- quality_feedback attached to artifact metadata at generation time
- quality_feedback surfaced in artifact detail views
- no bridge events created
- no interests.json / threads.json mutated
- no routing regressions
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import shutil
from pathlib import Path

import pytest

# Ensure workspace is on path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from sim import (
    write_artifact_metadata,
    build_artifact_explainability,
    build_artifact_detail_views,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def minimal_agent(name: str = "test-agent") -> dict:
    return {"name": name, "reputation": 0.5, "storage": "memory"}


def minimal_opportunity() -> dict:
    return {
        "niche_theme": "testing",
        "target_user": "developers",
        "problem_statement": "automated testing of artifact quality feedback",
        "gap_reason": "quality signals not captured at generation time",
        "existing_solution_friction": "manual inspection required",
        "artifact_hypothesis": "structured quality metadata improves reviewability",
        "offer_hypothesis": "operators prefer self-assessed artifacts",
        "delivery_mode_guess": "internal_tool",
        "research_confidence": 0.5,
    }


# ---------------------------------------------------------------------------
# Test: build_artifact_explainability produces required fields
# ---------------------------------------------------------------------------

def test_explainability_has_required_fields():
    """build_artifact_explainability returns the four informational field sources."""
    meta = {
        "human_proposed_score": 0.3,
        "internal_score": 0.3,
        "opportunity_score": 0.3,
        "proof_signals": {"human_approvals": 0, "real_usage_hits": 0, "handoff_acceptances": 0},
    }
    result = build_artifact_explainability(meta)
    assert "internal_strength" in result
    assert "external_proof" in result
    assert "risks" in result
    assert "next_actions" in result


def test_explainability_internal_strength_when_high_score():
    """High internal_score contributes to internal_strength."""
    meta = {
        "internal_score": 0.7,
        "human_proposed_score": 0.3,
        "opportunity_score": 0.3,
        "proof_signals": {"human_approvals": 0, "real_usage_hits": 0, "handoff_acceptances": 0},
    }
    result = build_artifact_explainability(meta)
    assert any("internal quality" in s for s in result["internal_strength"])


def test_explainability_no_external_proof_adds_risk():
    """No proof signals adds a risk entry."""
    meta = {
        "internal_score": 0.7,
        "human_proposed_score": 0.7,
        "opportunity_score": 0.7,
        "deployment_effort_score": 0.3,
        "buyer_clarity_score": 0.6,
        "proof_signals": {"human_approvals": 0, "real_usage_hits": 0, "handoff_acceptances": 0},
    }
    result = build_artifact_explainability(meta)
    assert "weak external proof" in str(result["risks"])


def test_explainability_human_approval_adds_external_proof():
    """human_approvals >= 1 contributes to external_proof."""
    meta = {
        "internal_score": 0.5,
        "human_proposed_score": 0.5,
        "opportunity_score": 0.5,
        "proof_signals": {"human_approvals": 2, "real_usage_hits": 0, "handoff_acceptances": 0},
    }
    result = build_artifact_explainability(meta)
    assert any("human approval" in s for s in result["external_proof"])


def test_explainability_thin_artifact_adds_risk_and_action():
    """thin_artifact_penalty > 0 adds substance risk and a next-action."""
    meta = {
        "internal_score": 0.5,
        "human_proposed_score": 0.5,
        "opportunity_score": 0.5,
        "deployment_effort_score": 0.3,
        "buyer_clarity_score": 0.6,
        "thin_artifact_penalty": 0.15,
        "proof_signals": {"human_approvals": 0, "real_usage_hits": 0, "handoff_acceptances": 0},
    }
    result = build_artifact_explainability(meta)
    assert any("substance looks thin" in s for s in result["risks"])
    assert any("strengthen" in s.lower() for s in result["next_actions"])


# ---------------------------------------------------------------------------
# Test: write_artifact_metadata attaches quality_feedback
# ---------------------------------------------------------------------------

def test_write_artifact_metadata_attaches_quality_feedback(temp_dir):
    """write_artifact_metadata writes quality_feedback into the .meta.json file."""
    agent_dir = temp_dir / "test-agent"
    agent_dir.mkdir()
    agent = minimal_agent("test-agent")
    meta_name = write_artifact_metadata(
        agent=agent,
        agent_dir=agent_dir,
        artifact_slug="test_artifact",
        artifact_type="research_note",
        idea="Test artifact for quality feedback",
        explanation="Used to verify quality_feedback is attached at generation time.",
        purpose="Test quality feedback loop slice 1",
        destination="internal_review",
        future_directions=["verify", "extend"],
        combinable_with=["test_pack"],
        lineage={"action": "test", "parent_ids": []},
        category="testing",
        opportunity=minimal_opportunity(),
    )
    meta_path = agent_dir / "artifacts" / meta_name
    assert meta_path.exists(), f"Expected {meta_path} to exist"
    meta = json.loads(meta_path.read_text())
    assert "quality_feedback" in meta, "quality_feedback must be present in artifact meta"
    qf = meta["quality_feedback"]
    assert "quality_summary" in qf, "quality_summary must be present"
    assert "weakness_summary" in qf, "weakness_summary must be present"
    assert "recommended_next_action" in qf, "recommended_next_action must be present"
    assert "proof_summary" in qf, "proof_summary must be present"


def test_quality_feedback_quality_summary_is_string(temp_dir):
    """quality_summary is a non-empty string."""
    agent_dir = temp_dir / "test-agent"
    agent_dir.mkdir()
    meta_name = write_artifact_metadata(
        agent=minimal_agent(),
        agent_dir=agent_dir,
        artifact_slug="test_qs",
        artifact_type="research_note",
        idea="test",
        explanation="test",
        purpose="test",
        destination="internal_review",
        future_directions=[],
        combinable_with=[],
        lineage={},
        category="testing",
        opportunity=minimal_opportunity(),
    )
    meta = json.loads((agent_dir / "artifacts" / meta_name).read_text())
    qf = meta["quality_feedback"]
    assert isinstance(qf["quality_summary"], str)
    assert len(qf["quality_summary"]) > 0


def test_quality_feedback_weakness_summary_is_string(temp_dir):
    """weakness_summary is a string (may be empty if no risks)."""
    agent_dir = temp_dir / "test-agent2"
    agent_dir.mkdir()
    meta_name = write_artifact_metadata(
        agent=minimal_agent("test-agent2"),
        agent_dir=agent_dir,
        artifact_slug="test_ws",
        artifact_type="research_note",
        idea="test",
        explanation="test",
        purpose="test",
        destination="internal_review",
        future_directions=[],
        combinable_with=[],
        lineage={},
        category="testing",
        opportunity=minimal_opportunity(),
    )
    meta = json.loads((agent_dir / "artifacts" / meta_name).read_text())
    qf = meta["quality_feedback"]
    assert isinstance(qf["weakness_summary"], str)


def test_quality_feedback_recommended_next_action_is_string(temp_dir):
    """recommended_next_action is a non-empty string."""
    agent_dir = temp_dir / "test-agent3"
    agent_dir.mkdir()
    meta_name = write_artifact_metadata(
        agent=minimal_agent("test-agent3"),
        agent_dir=agent_dir,
        artifact_slug="test_rna",
        artifact_type="research_note",
        idea="test",
        explanation="test",
        purpose="test",
        destination="internal_review",
        future_directions=[],
        combinable_with=[],
        lineage={},
        category="testing",
        opportunity=minimal_opportunity(),
    )
    meta = json.loads((agent_dir / "artifacts" / meta_name).read_text())
    qf = meta["quality_feedback"]
    assert isinstance(qf["recommended_next_action"], str)
    assert len(qf["recommended_next_action"]) > 0


def test_quality_feedback_proof_summary_fields(temp_dir):
    """proof_summary contains the required proof signal fields."""
    agent_dir = temp_dir / "test-agent4"
    agent_dir.mkdir()
    meta_name = write_artifact_metadata(
        agent=minimal_agent("test-agent4"),
        agent_dir=agent_dir,
        artifact_slug="test_ps",
        artifact_type="research_note",
        idea="test",
        explanation="test",
        purpose="test",
        destination="internal_review",
        future_directions=[],
        combinable_with=[],
        lineage={},
        category="testing",
        opportunity=minimal_opportunity(),
    )
    meta = json.loads((agent_dir / "artifacts" / meta_name).read_text())
    qf = meta["quality_feedback"]
    ps = qf["proof_summary"]
    assert "human_approvals" in ps
    assert "real_usage_hits" in ps
    assert "handoff_acceptances" in ps
    assert "external_validation_state" in ps
    assert isinstance(ps["human_approvals"], int)
    assert isinstance(ps["real_usage_hits"], int)
    assert isinstance(ps["handoff_acceptances"], int)


# ---------------------------------------------------------------------------
# Test: quality_feedback is informational only — no bridge event created
# ---------------------------------------------------------------------------

def test_quality_feedback_no_bridge_event_on_generation(temp_dir):
    """Generating an artifact with quality_feedback does not create a bridge event.

    The feedback loop is informational in Slice 1. No call to record_inadequacy_event,
    no signal file written, no proposal generated.
    """
    agent_dir = temp_dir / "test-agent5"
    agent_dir.mkdir()
    meta_name = write_artifact_metadata(
        agent=minimal_agent("test-agent5"),
        agent_dir=agent_dir,
        artifact_slug="test_no_bridge",
        artifact_type="research_note",
        idea="test",
        explanation="test",
        purpose="test",
        destination="internal_review",
        future_directions=[],
        combinable_with=[],
        lineage={},
        category="testing",
        opportunity=minimal_opportunity(),
    )
    # No bridge signal file should exist
    bridge_signals = list(temp_dir.glob("**/*bridge_signal*")) + list(temp_dir.glob("**/weslr_inadequacy_events*"))
    assert len(bridge_signals) == 0, "No bridge signal files should exist after artifact generation"
    # No inadequacy events should be written
    inadequacy_files = list(temp_dir.glob("**/*inadequacy*"))
    assert len(inadequacy_files) == 0, "No inadequacy files should exist after artifact generation"


# ---------------------------------------------------------------------------
# Test: build_artifact_detail_views includes quality_feedback
# ---------------------------------------------------------------------------

def test_artifact_detail_view_includes_quality_feedback(temp_dir):
    """build_artifact_detail_views includes quality_feedback from source items."""
    artifact_item = {
        "id": "test-artifact-qf-001",
        "title": "Test Quality Feedback Artifact",
        "category": "testing",
        "family": "test-family",
        "target_user": "developers",
        "niche_theme": "testing",
        "problem_statement": "Test problem statement for quality feedback",
        "sellability_score": 0.55,
        "human_proposed_score": 0.50,
        "internal_score": 0.50,
        "opportunity_score": 0.50,
        "review_status": "unreviewed",
        "price_band_guess": "free",
        "delivery_mode": "internal_tool",
        "export_path": None,
        "quality_feedback": {
            "quality_summary": "newly created test artifact",
            "weakness_summary": "early-stage, substance still forming",
            "recommended_next_action": "run validate/use or validate/accept on a real artifact trial",
            "proof_summary": {
                "human_approvals": 0,
                "real_usage_hits": 0,
                "handoff_acceptances": 0,
                "external_validation_state": "unvalidated",
            },
        },
    }
    details = build_artifact_detail_views(
        export_queue=[artifact_item],
        review_queue=[],
        artifact_packs=[],
    )
    assert len(details) >= 1
    found = next((d for d in details if d["id"] == "test-artifact-qf-001"), None)
    assert found is not None, "Artifact should appear in detail views"
    assert "quality_feedback" in found, "quality_feedback must be in artifact detail view"
    assert found["quality_feedback"]["quality_summary"] == "newly created test artifact"


def test_artifact_detail_view_missing_quality_feedback_is_none(temp_dir):
    """Artifacts without quality_feedback field pass through cleanly (None)."""
    artifact_item = {
        "id": "test-artifact-no-qf-001",
        "title": "Legacy Artifact Without Quality Feedback",
        "category": "testing",
        "family": "test-family",
        "target_user": "developers",
        "niche_theme": "testing",
        "problem_statement": "A legacy artifact created before Slice 1.",
        "sellability_score": 0.55,
        "human_proposed_score": 0.50,
        "internal_score": 0.50,
        "opportunity_score": 0.50,
        "review_status": "unreviewed",
    }
    details = build_artifact_detail_views(
        export_queue=[artifact_item],
        review_queue=[],
        artifact_packs=[],
    )
    found = next((d for d in details if d["id"] == "test-artifact-no-qf-001"), None)
    assert found is not None
    # quality_feedback may be None for legacy artifacts — must not break rendering
    assert found.get("quality_feedback") is None or isinstance(found.get("quality_feedback"), dict)


# ---------------------------------------------------------------------------
# Test: no interests.json / threads.json mutated
# ---------------------------------------------------------------------------

def test_no_interests_json_mutated_on_artifact_write(temp_dir, monkeypatch):
    """write_artifact_metadata does not write to interests.json."""
    interests_path = temp_dir / "interests.json"
    interests_path.write_text("[]")
    monkeypatch.setenv("WESLR_INTERESTS_PATH", str(interests_path))
    agent_dir = temp_dir / "test-agent6"
    agent_dir.mkdir()
    write_artifact_metadata(
        agent=minimal_agent("test-agent6"),
        agent_dir=agent_dir,
        artifact_slug="test_interests",
        artifact_type="research_note",
        idea="test",
        explanation="test",
        purpose="test",
        destination="internal_review",
        future_directions=[],
        combinable_with=[],
        lineage={},
        category="testing",
        opportunity=minimal_opportunity(),
    )
    # interests.json must be unchanged
    assert interests_path.read_text() == "[]"


def test_no_threads_json_mutated_on_artifact_write(temp_dir, monkeypatch):
    """write_artifact_metadata does not write to threads.json."""
    threads_path = temp_dir / "threads.json"
    threads_path.write_text("[]")
    monkeypatch.setenv("WESLR_THREADS_PATH", str(threads_path))
    agent_dir = temp_dir / "test-agent7"
    agent_dir.mkdir()
    write_artifact_metadata(
        agent=minimal_agent("test-agent7"),
        agent_dir=agent_dir,
        artifact_slug="test_threads",
        artifact_type="research_note",
        idea="test",
        explanation="test",
        purpose="test",
        destination="internal_review",
        future_directions=[],
        combinable_with=[],
        lineage={},
        category="testing",
        opportunity=minimal_opportunity(),
    )
    # threads.json must be unchanged
    assert threads_path.read_text() == "[]"


# ---------------------------------------------------------------------------
# Test: no routing regressions
# ---------------------------------------------------------------------------

def test_write_artifact_metadata_returns_meta_filename(temp_dir):
    """write_artifact_metadata returns the meta filename, not the artifact body."""
    agent_dir = temp_dir / "test-agent8"
    agent_dir.mkdir()
    result = write_artifact_metadata(
        agent=minimal_agent("test-agent8"),
        agent_dir=agent_dir,
        artifact_slug="test_return",
        artifact_type="research_note",
        idea="test",
        explanation="test",
        purpose="test",
        destination="internal_review",
        future_directions=[],
        combinable_with=[],
        lineage={},
        category="testing",
        opportunity=minimal_opportunity(),
    )
    assert isinstance(result, str)
    assert result.endswith(".meta.json")
    assert (agent_dir / "artifacts" / result).exists()


def test_quality_feedback_not_incorrectly_copied_to_wrong_artifact(temp_dir):
    """Each artifact gets its own quality_feedback; no cross-contamination."""
    agent_dir = temp_dir / "test-agent9"
    agent_dir.mkdir()
    name_a = write_artifact_metadata(
        agent=minimal_agent("test-agent9"),
        agent_dir=agent_dir,
        artifact_slug="artifact_a",
        artifact_type="research_note",
        idea="Artifact A",
        explanation="Explanation A",
        purpose="Purpose A",
        destination="internal_review",
        future_directions=[],
        combinable_with=[],
        lineage={},
        category="category-a",
        opportunity=minimal_opportunity(),
    )
    name_b = write_artifact_metadata(
        agent=minimal_agent("test-agent9"),
        agent_dir=agent_dir,
        artifact_slug="artifact_b",
        artifact_type="tradable_component",
        idea="Artifact B",
        explanation="Explanation B",
        purpose="Purpose B",
        destination="shared_with_agents",
        future_directions=[],
        combinable_with=[],
        lineage={},
        category="category-b",
        opportunity=minimal_opportunity(),
    )
    meta_a = json.loads((agent_dir / "artifacts" / name_a).read_text())
    meta_b = json.loads((agent_dir / "artifacts" / name_b).read_text())
    assert meta_a["id"] != meta_b["id"]
    assert meta_a["idea"] == "Artifact A"
    assert meta_b["idea"] == "Artifact B"
    assert "quality_feedback" in meta_a
    assert "quality_feedback" in meta_b


# ---------------------------------------------------------------------------
# Test: Slice 2 — bridge_candidate_preview
# ---------------------------------------------------------------------------

def test_preview_absent_for_none_meta():
    """None meta returns None from candidate preview."""
    from sim import build_artifact_candidate_preview
    result = build_artifact_candidate_preview(None)
    assert result is None


def test_preview_absent_for_empty_meta():
    """Empty meta dict returns None."""
    from sim import build_artifact_candidate_preview
    result = build_artifact_candidate_preview({})
    assert result is None


def test_preview_absent_for_approved_artifact():
    """Approved artifacts do not produce a preview."""
    from sim import build_artifact_candidate_preview
    meta = {
        "id": "test-artifact-approved",
        "review_status": "approved",
        "quality_feedback": {
            "quality_summary": "solid artifact",
            "weakness_summary": "substance thin",
            "recommended_next_action": "continue validation",
            "proof_summary": {"human_approvals": 0, "real_usage_hits": 0, "handoff_acceptances": 0},
        },
    }
    result = build_artifact_candidate_preview(meta)
    assert result is None


def test_preview_absent_for_export_ready_artifact():
    """Export-ready artifacts do not produce a preview."""
    from sim import build_artifact_candidate_preview
    meta = {
        "id": "test-artifact-export-ready",
        "review_status": "export_ready",
        "quality_feedback": {
            "quality_summary": "substance thin",
            "weakness_summary": "thin substance",
            "recommended_next_action": "validate",
            "proof_summary": {"human_approvals": 0, "real_usage_hits": 0, "handoff_acceptances": 0},
        },
    }
    result = build_artifact_candidate_preview(meta)
    assert result is None


def test_preview_absent_when_no_quality_feedback():
    """Artifacts without quality_feedback do not produce a preview."""
    from sim import build_artifact_candidate_preview
    meta = {
        "id": "test-artifact-no-qf",
        "review_status": "unreviewed",
    }
    result = build_artifact_candidate_preview(meta)
    assert result is None


def test_preview_absent_for_low_urgency_no_weakness():
    """Artifacts with decent quality and no weakness indicators produce no preview."""
    from sim import build_artifact_candidate_preview
    meta = {
        "id": "test-artifact-good",
        "review_status": "unreviewed",
        "quality_feedback": {
            "quality_summary": "decent internal quality",
            "weakness_summary": "no major risks identified",
            "recommended_next_action": "continue validation",
            "proof_summary": {"human_approvals": 0, "real_usage_hits": 0, "handoff_acceptances": 0},
        },
    }
    result = build_artifact_candidate_preview(meta)
    assert result is None


def test_preview_present_for_high_urgency_thin_artifact():
    """Thin artifact with no proof signals produces a high-urgency preview."""
    from sim import build_artifact_candidate_preview
    meta = {
        "id": "test-artifact-thin-001",
        "review_status": "unreviewed",
        "internal_score": 0.55,
        "quality_feedback": {
            "quality_summary": "early-stage, substance still forming",
            "weakness_summary": "artifact substance looks thin relative to its framing",
            "recommended_next_action": "strengthen underlying artifact before promoting",
            "proof_summary": {"human_approvals": 0, "real_usage_hits": 0, "handoff_acceptances": 0},
        },
    }
    result = build_artifact_candidate_preview(meta)
    assert result is not None, "Preview should be present for thin artifact"
    assert result["candidate"] is True
    assert result["surface_type"] == "artifact_weakness"
    assert result["spine_target"] == "step1_inadequacy_signal"
    assert result["urgency"] == "high"
    assert result["urgency_note"] == "recurring limitation"
    assert result["requires_confirm"] is True
    assert "test-artifact-thin-001" in result["confirm_command"]
    assert "--confirm" in result["confirm_command"]
    assert "preview_source" in result
    assert "preview_generated_at" in result


def test_preview_present_for_early_stage_artifact():
    """Early-stage artifact with no proof produces a medium-urgency preview."""
    from sim import build_artifact_candidate_preview
    meta = {
        "id": "test-artifact-early-001",
        "review_status": "unreviewed",
        "internal_score": 0.50,
        "quality_feedback": {
            "quality_summary": "early-stage, substance still forming",
            "weakness_summary": "strong internal score but weak external proof",
            "recommended_next_action": "run validate/use or validate/accept on a real artifact trial",
            "proof_summary": {"human_approvals": 0, "real_usage_hits": 0, "handoff_acceptances": 0},
        },
    }
    result = build_artifact_candidate_preview(meta)
    assert result is not None
    assert result["candidate"] is True
    assert result["urgency"] == "medium"
    assert result["urgency_note"] == "early-stage artifact"


def test_preview_absent_for_approved_even_with_weakness():
    """Approved status takes precedence even if weakness signals exist."""
    from sim import build_artifact_candidate_preview
    meta = {
        "id": "test-artifact-approved-weak",
        "review_status": "approved",
        "quality_feedback": {
            "quality_summary": "early-stage",
            "weakness_summary": "substance looks thin",
            "recommended_next_action": "strengthen",
            "proof_summary": {"human_approvals": 1, "real_usage_hits": 0, "handoff_acceptances": 0},
        },
    }
    result = build_artifact_candidate_preview(meta)
    assert result is None


def test_preview_absent_for_bridged_artifact():
    """Artifact already confirmed through bridge does not get a new preview."""
    from sim import build_artifact_candidate_preview
    meta = {
        "id": "test-artifact-bridged",
        "review_status": "unreviewed",
        "bridge_confirmed": "2026-04-21T10:00:00Z",
        "quality_feedback": {
            "quality_summary": "early-stage",
            "weakness_summary": "thin substance",
            "recommended_next_action": "escalate",
            "proof_summary": {"human_approvals": 0, "real_usage_hits": 0, "handoff_acceptances": 0},
        },
    }
    result = build_artifact_candidate_preview(meta)
    assert result is None


def test_confirm_command_format():
    """confirm_command contains the correct artifact ID and --confirm flag."""
    from sim import build_artifact_candidate_preview
    meta = {
        "id": "agent-1-test_artifact-1234567890",
        "review_status": "unreviewed",
        "quality_feedback": {
            "quality_summary": "early-stage",
            "weakness_summary": "substance thin",
            "recommended_next_action": "strengthen",
            "proof_summary": {"human_approvals": 0, "real_usage_hits": 0, "handoff_acceptances": 0},
        },
    }
    result = build_artifact_candidate_preview(meta)
    assert result is not None
    cmd = result["confirm_command"]
    assert "weslr spine bridge" in cmd
    assert "--from-artifact agent-1-test_artifact-1234567890" in cmd
    assert "--confirm" in cmd


def test_requires_confirm_always_true():
    """requires_confirm is always True in all preview scenarios."""
    from sim import build_artifact_candidate_preview
    # Test both high and medium urgency paths
    for urgency, ws in [("high", "thin substance"), ("medium", "early-stage, substance forming")]:
        meta = {
            "id": f"test-{urgency}",
            "review_status": "unreviewed",
            "quality_feedback": {
                "quality_summary": ws,
                "weakness_summary": ws,
                "recommended_next_action": "validate",
                "proof_summary": {"human_approvals": 0, "real_usage_hits": 0, "handoff_acceptances": 0},
            },
        }
        result = build_artifact_candidate_preview(meta)
        assert result is not None
        assert result["requires_confirm"] is True, f"requires_confirm should be True for {urgency}"


def test_preview_absent_for_human_approved_no_weakness():
    """Human approval without weakness signals produces no preview."""
    from sim import build_artifact_candidate_preview
    meta = {
        "id": "test-artifact-humapproved",
        "review_status": "unreviewed",
        "quality_feedback": {
            "quality_summary": "solid artifact with human approval",
            "weakness_summary": "no major risks identified",
            "recommended_next_action": "continue validation",
            "proof_summary": {"human_approvals": 1, "real_usage_hits": 0, "handoff_acceptances": 0},
        },
    }
    result = build_artifact_candidate_preview(meta)
    # No weakness indicators = no preview
    assert result is None


def test_why_list_is_capped():
    """The why list is limited to 2 items."""
    from sim import build_artifact_candidate_preview
    meta = {
        "id": "test-artifact-why-cap",
        "review_status": "unreviewed",
        "internal_score": 0.5,
        "quality_feedback": {
            "quality_summary": "early-stage",
            "weakness_summary": "substance thin and weak external proof",
            "recommended_next_action": "validate",
            "proof_summary": {"human_approvals": 0, "real_usage_hits": 0, "handoff_acceptances": 0},
        },
    }
    result = build_artifact_candidate_preview(meta)
    assert result is not None
    assert len(result["why"]) <= 2


def test_preview_in_artifact_detail_view():
    """build_artifact_detail_views includes bridge_candidate_preview when eligible."""
    from sim import build_artifact_detail_views, build_artifact_candidate_preview
    eligible_artifact = {
        "id": "test-artifact-preview-detail",
        "title": "Test Preview Artifact",
        "category": "testing",
        "family": "test",
        "review_status": "unreviewed",
        "internal_score": 0.5,
        "quality_feedback": {
            "quality_summary": "early-stage",
            "weakness_summary": "substance thin",
            "recommended_next_action": "validate",
            "proof_summary": {"human_approvals": 0, "real_usage_hits": 0, "handoff_acceptances": 0},
        },
    }
    details = build_artifact_detail_views(
        export_queue=[eligible_artifact],
        review_queue=[],
        artifact_packs=[],
    )
    found = next((d for d in details if d["id"] == "test-artifact-preview-detail"), None)
    assert found is not None
    assert "bridge_candidate_preview" in found
    assert found["bridge_candidate_preview"] is not None
    assert found["bridge_candidate_preview"]["candidate"] is True


def test_preview_none_in_artifact_detail_view_for_good_artifact():
    """build_artifact_detail_views sets bridge_candidate_preview to None for non-candidates."""
    from sim import build_artifact_detail_views
    good_artifact = {
        "id": "test-artifact-good-detail",
        "title": "Good Artifact",
        "category": "testing",
        "family": "test",
        "review_status": "unreviewed",
        "quality_feedback": {
            "quality_summary": "decent internal quality",
            "weakness_summary": "no major risks identified",
            "recommended_next_action": "continue validation",
            "proof_summary": {"human_approvals": 0, "real_usage_hits": 0, "handoff_acceptances": 0},
        },
    }
    details = build_artifact_detail_views(
        export_queue=[good_artifact],
        review_queue=[],
        artifact_packs=[],
    )
    found = next((d for d in details if d["id"] == "test-artifact-good-detail"), None)
    assert found is not None
    assert "bridge_candidate_preview" in found
    assert found["bridge_candidate_preview"] is None


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def temp_dir():
    """Create a temporary directory for artifact writes, cleaned up after test."""
    d = tempfile.mkdtemp(prefix="wf_test_")
    yield Path(d)
    shutil.rmtree(d, ignore_errors=True)


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
