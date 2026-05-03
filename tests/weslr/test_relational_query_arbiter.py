"""
test_relational_query_arbiter.py

Tests for relational query detection and routing in hybrid_turn_arbiter.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from weslr.hybrid_turn_arbiter import analyze_turn


class TestRelationalQueryDetection:
    """Phase 3 tests: relational query detection and fact_engine routing."""

    def test_what_did_x_say_about_y(self):
        result = analyze_turn("What did Arthur say about the robotic arm?")
        assert result["turn_kind"] == "relational_query"
        assert result["selected_layer"] == "fact_engine"

    def test_what_x_said_about_y(self):
        result = analyze_turn("What Arthur said about calibration")
        assert result["turn_kind"] == "relational_query"
        assert result["selected_layer"] == "fact_engine"

    def test_relationship_between_x_and_y(self):
        result = analyze_turn("What's the relationship between Project Phoenix and the evidence search bridge?")
        assert result["turn_kind"] == "relational_query"
        assert result["selected_layer"] == "fact_engine"

    def test_how_are_x_and_y_connected(self):
        result = analyze_turn("How are the robotic arm and the gripper connected?")
        assert result["turn_kind"] == "relational_query"
        assert result["selected_layer"] == "fact_engine"

    def test_how_is_x_related_to_y(self):
        result = analyze_turn("How is the TIA bridge related to the entity intelligence platform?")
        assert result["turn_kind"] == "relational_query"
        assert result["selected_layer"] == "fact_engine"

    def test_tell_me_about_x_and_y(self):
        result = analyze_turn("Tell me about the robotic arm and the calibration system")
        assert result["turn_kind"] == "relational_query"
        assert result["selected_layer"] == "fact_engine"

    def test_timeline_of_x_regarding_y(self):
        result = analyze_turn("Timeline of the robotic arm regarding calibration")
        assert result["turn_kind"] == "relational_query"
        assert result["selected_layer"] == "fact_engine"

    def test_timeline_for_x_related_to_y(self):
        result = analyze_turn("Timeline for the gripper related to the new materials")
        assert result["turn_kind"] == "relational_query"
        assert result["selected_layer"] == "fact_engine"

    def test_project_knows_about(self):
        result = analyze_turn("What does project Phoenix know about robotic arm?")
        assert result["turn_kind"] == "relational_query"
        assert result["selected_layer"] == "fact_engine"

    def test_project_knows_all(self):
        result = analyze_turn("What does project Phoenix know?")
        assert result["turn_kind"] == "relational_query"
        assert result["selected_layer"] == "fact_engine"

    def test_relational_query_requires_memory(self):
        result = analyze_turn("What did we discuss about the robotic arm?")
        assert result["requires_memory"] is True

    def test_regular_question_still_routes_to_evidence(self):
        result = analyze_turn("What is the weather today?")
        # Not relational — should go to external topic detection
        assert result["turn_kind"] != "relational_query"

    def test_workplace_question_not_relational(self):
        result = analyze_turn("What are we working on?")
        assert result["turn_kind"] == "workplace"

    def test_continuity_question_not_relational(self):
        result = analyze_turn("What did we do last time?")
        assert result["turn_kind"] == "continuity"

    def test_turn_kind_values_valid(self):
        from weslr.hybrid_turn_arbiter import _VALID_TURN_KINDS
        result = analyze_turn("What did Arthur say about the robotic arm?")
        assert result["turn_kind"] in _VALID_TURN_KINDS

    def test_selected_layer_is_fact_engine(self):
        result = analyze_turn("What did Arthur say about the robotic arm?")
        assert result["selected_layer"] == "fact_engine"

    def test_no_confidence_regression(self):
        result = analyze_turn("What did Arthur say about the robotic arm?")
        assert result["confidence"] >= 0.85

    def test_no_ambiguity_on_clear_relational(self):
        result = analyze_turn("What did Arthur say about the robotic arm?")
        assert result["ambiguity"] == "none"

    def test_authority_routing_only(self):
        result = analyze_turn("What did Arthur say about the robotic arm?")
        assert result["authority"] == "routing_analysis_only"
        assert result["automatic_action"] is False

    def test_no_raw_prompt_stored(self):
        result = analyze_turn("What did Arthur say about the robotic arm?")
        # check the returned dict has no raw_prompt_stored=True
        assert result.get("raw_prompt_stored", False) is False

    def test_relational_query_with_context(self):
        ctx = {"user_id": "arthur", "recent_timeline_events": [{"summary": "test"}]}
        result = analyze_turn("What did Arthur say about calibration?", context=ctx)
        assert result["turn_kind"] == "relational_query"
        assert result["selected_layer"] == "fact_engine"

    def test_Arbiter_no_automatic_action(self):
        result = analyze_turn("What did Arthur say about the robotic arm?")
        assert result["automatic_action"] is False