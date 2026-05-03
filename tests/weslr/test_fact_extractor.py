"""
test_fact_extractor.py

Tests for WESLR Fact Extractor V1.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from weslr.fact_extractor import (
    extract_triples_from_summary,
    append_fact_assertion,
    load_facts,
    _normalize_entity,
    DEFAULT_FACT_STORE_PATH,
)


# ─── Helpers ─────────────────────────────────────────────────────────────────

@pytest.fixture
def temp_store():
    fd, path = tempfile.mkstemp(suffix=".jsonl")
    os.close(fd)
    yield path
    os.unlink(path)


# ─── extract_triples_from_summary ─────────────────────────────────────────────

class TestExtractTriples:
    def test_discussed_pattern(self):
        result = extract_triples_from_summary(
            "We discussed the robotic arm's gripper calibration"
        )
        assert len(result) == 1
        assert result[0]["predicate"] == "discussed"

    def test_discussed_pattern_user_prefix(self):
        result = extract_triples_from_summary(
            "Arthur discussed the robotic arm's gripper calibration"
        )
        assert len(result) == 1
        assert result[0]["predicate"] == "discussed"
        assert result[0]["subject"] == "arthur"

    def test_said_about_pattern(self):
        result = extract_triples_from_summary(
            "Arthur said the calibration was a priority about the robotic arm"
        )
        assert len(result) == 1
        assert result[0]["predicate"] == "said_about"

    def test_worked_on_pattern(self):
        result = extract_triples_from_summary("We worked on the Jarvis memory experiment")
        assert len(result) == 1
        assert result[0]["predicate"] == "worked_on"

    def test_important_for_pattern(self):
        result = extract_triples_from_summary(
            "Calibration is important for the robotic arm"
        )
        assert len(result) == 1
        assert result[0]["predicate"] == "has_importance"
        assert result[0]["subject"] == "the_robotic_arm"
        assert result[0]["object"] == "calibration"

    def test_depends_on_pattern(self):
        result = extract_triples_from_summary(
            "Project Phoenix depends on the evidence search bridge"
        )
        assert len(result) == 1
        assert result[0]["predicate"] == "depends_on"

    def test_part_of_pattern(self):
        result = extract_triples_from_summary(
            "The gripper is part of the robotic arm assembly"
        )
        assert len(result) == 1
        assert result[0]["predicate"] == "part_of"

    def test_uses_pattern(self):
        result = extract_triples_from_summary("WESLR uses entity timelines for memory")
        assert len(result) == 1
        assert result[0]["predicate"] == "uses"

    def test_created_pattern(self):
        result = extract_triples_from_summary("Arthur created a new fact extraction module")
        assert len(result) == 1
        assert result[0]["predicate"] == "created"

    def test_tested_pattern(self):
        result = extract_triples_from_summary("We tested the arbiter context builder today")
        assert len(result) == 1
        assert result[0]["predicate"] == "tested"

    def test_upgraded_pattern(self):
        result = extract_triples_from_summary("Arthur upgraded the entity timeline memory")
        assert len(result) == 1
        assert result[0]["predicate"] == "upgraded"

    def test_no_match_returns_empty(self):
        result = extract_triples_from_summary(
            "The weather is nice today and we had coffee"
        )
        assert result == []

    def test_empty_text_returns_empty(self):
        assert extract_triples_from_summary("") == []
        assert extract_triples_from_summary(None) == []

    def test_normalizes_entities(self):
        result = extract_triples_from_summary("We discussed Project Phoenix")
        assert len(result) == 1
        assert "project_phoenix" in result[0]["object"]


# ─── append_fact_assertion ────────────────────────────────────────────────────

class TestAppendFactAssertion:
    def test_appends_jsonl(self, temp_store):
        triple = {"subject": "arthur", "predicate": "discussed", "object": "robotic_arm"}
        result = append_fact_assertion(
            triple,
            source_event_ref="user_arthur:2026-05-02T14:48:20Z",
            fact_store_path=temp_store,
        )
        assert result["status"] == "appended"
        # Read back
        with open(temp_store) as f:
            record = json.loads(f.readline())
        assert record["record_type"] == "fact_assertion_v1"
        assert record["subject"] == "arthur"
        assert record["authority"] == "extracted_from_timeline"
        assert record["automatic_action"] is False
        assert record["hidden_learning"] is False
        assert record["raw_prompt_stored"] is False

    def test_missing_triple_keys_raises(self, temp_store):
        with pytest.raises(ValueError):
            append_fact_assertion(
                {"subject": "x"},
                source_event_ref="ref",
                fact_store_path=temp_store,
            )


# ─── load_facts ────────────────────────────────────────────────────────────────

class TestLoadFacts:
    def test_load_by_subject(self, temp_store):
        t1 = {"subject": "arthur", "predicate": "discussed", "object": "robotic_arm"}
        t2 = {"subject": "arthur", "predicate": "worked_on", "object": "project_phoenix"}
        append_fact_assertion(t1, "ref1", fact_store_path=temp_store)
        append_fact_assertion(t2, "ref2", fact_store_path=temp_store)

        results = load_facts(subject="arthur", fact_store_path=temp_store)
        assert len(results) == 2

    def test_load_by_predicate(self, temp_store):
        t1 = {"subject": "arthur", "predicate": "discussed", "object": "robotic_arm"}
        t2 = {"subject": "arthur", "predicate": "discussed", "object": "project_phoenix"}
        append_fact_assertion(t1, "ref1", fact_store_path=temp_store)
        append_fact_assertion(t2, "ref2", fact_store_path=temp_store)

        results = load_facts(predicate="discussed", fact_store_path=temp_store)
        assert len(results) == 2

    def test_load_by_object(self, temp_store):
        t1 = {"subject": "arthur", "predicate": "discussed", "object": "robotic_arm"}
        append_fact_assertion(t1, "ref1", fact_store_path=temp_store)

        results = load_facts(obj="robotic_arm", fact_store_path=temp_store)
        assert len(results) == 1
        assert results[0]["object"] == "robotic_arm"

    def test_limit(self, temp_store):
        for i in range(5):
            append_fact_assertion(
                {"subject": "user", "predicate": f"pred_{i}", "object": "obj"},
                f"ref{i}",
                fact_store_path=temp_store,
            )
        results = load_facts(limit=3, fact_store_path=temp_store)
        assert len(results) == 3

    def test_nonexistent_path_returns_empty(self):
        results = load_facts(fact_store_path="/nonexistent/path/facts.jsonl")
        assert results == []

    def test_no_filters_returns_all(self, temp_store):
        append_fact_assertion(
            {"subject": "a", "predicate": "b", "object": "c"},
            "ref",
            fact_store_path=temp_store,
        )
        results = load_facts(fact_store_path=temp_store)
        assert len(results) == 1

    def test_filter_by_project_id(self, temp_store):
        t1 = {"subject": "arthur", "predicate": "discussed", "object": "robotic_arm"}
        t2 = {"subject": "arthur", "predicate": "worked_on", "object": "project_phoenix"}
        append_fact_assertion(t1, "ref1", project_id="PRJ-001", fact_store_path=temp_store)
        append_fact_assertion(t2, "ref2", project_id="PRJ-002", fact_store_path=temp_store)

        results = load_facts(project_id="PRJ-001", fact_store_path=temp_store)
        assert len(results) == 1
        assert results[0]["project_id"] == "PRJ-001"

    def test_filter_by_project_id_no_match(self, temp_store):
        t1 = {"subject": "arthur", "predicate": "discussed", "object": "robotic_arm"}
        append_fact_assertion(t1, "ref1", project_id="PRJ-001", fact_store_path=temp_store)

        results = load_facts(project_id="PRJ-999", fact_store_path=temp_store)
        assert len(results) == 0

    def test_filter_project_id_with_subject(self, temp_store):
        t1 = {"subject": "arthur", "predicate": "discussed", "object": "robotic_arm"}
        t2 = {"subject": "bob", "predicate": "discussed", "object": "robotic_arm"}
        append_fact_assertion(t1, "ref1", project_id="PRJ-001", fact_store_path=temp_store)
        append_fact_assertion(t2, "ref2", project_id="PRJ-001", fact_store_path=temp_store)

        results = load_facts(subject="arthur", project_id="PRJ-001", fact_store_path=temp_store)
        assert len(results) == 1

    def test_append_with_project_id_round_trip(self, temp_store):
        triple = {"subject": "arthur", "predicate": "discussed", "object": "robotic_arm"}
        result = append_fact_assertion(
            triple,
            source_event_ref="user_arthur:2026-05-02T14:48:20Z",
            project_id="PRJ-20260503-001",
            fact_store_path=temp_store,
        )
        assert result["status"] == "appended"
        with open(temp_store) as f:
            record = json.loads(f.readline())
        assert record["project_id"] == "PRJ-20260503-001"
