"""
WESLR Entity Timeline Memory V1 — Tests

Covers:
  - normalize_entity_id
  - get_entity_timeline_path
  - append_entity_event → read back
  - load_entity_events (empty, limit, most_recent_first)
  - list_entity_timelines
  - extract_entities_from_summary (V1 stub)
  - suggest_entity_for_context
  - write_entity_from_user_message
  - build_entity_continuity_note
  - Context builder integration

Authority: entity_memory_only — no execution, no external calls.
"""

import json
import os
import pathlib
import shutil
import tempfile
import unittest


class TestNormalizeEntityId(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(normalize_entity_id("Robotic Arm"), "robotic_arm")

    def test_already_normalized(self):
        self.assertEqual(normalize_entity_id("robotic_arm"), "robotic_arm")

    def test_person_name(self):
        self.assertEqual(normalize_entity_id("Sarah Connor"), "sarah_connor")

    def test_project_name(self):
        self.assertEqual(normalize_entity_id("Project Phoenix"), "project_phoenix")

    def test_whitespace_collapse(self):
        self.assertEqual(normalize_entity_id("Robotic   Arm"), "robotic_arm")

    def test_empty_input(self):
        self.assertEqual(normalize_entity_id(""), "")
        self.assertEqual(normalize_entity_id(None), "")

    def test_hyphen_to_underscore(self):
        self.assertEqual(normalize_entity_id("project-name"), "project_name")

    def test_mixed_separators(self):
        self.assertEqual(normalize_entity_id("person::sarah"), "person_sarah")


class TestGetEntityTimelinePath(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_path_format(self):
        path = get_entity_timeline_path("robotic_arm", base_dir=self.tmpdir)
        self.assertEqual(path.name, "events.jsonl")
        self.assertEqual(path.parent.name, "tl_entity_robotic_arm")

    def test_nested_base(self):
        nested = pathlib.Path(self.tmpdir) / "subdir"
        path = get_entity_timeline_path("phoenix", base_dir=nested)
        self.assertTrue(path.parent.exists())


class TestAppendEntityEvent(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_append_creates_dir(self):
        result = append_entity_event(
            "robotic_arm", "arthur",
            "We discussed gripper calibration",
            source="user_message",
            base_dir=self.tmpdir,
        )
        self.assertEqual(result["status"], "appended")
        self.assertTrue(pathlib.Path(result["path"]).exists())

    def test_append_read_back(self):
        append_entity_event(
            "robotic_arm", "arthur",
            "Arthur mentioned the robotic arm",
            source="user_message",
            base_dir=self.tmpdir,
        )
        events = load_entity_events("robotic_arm", limit=10, base_dir=self.tmpdir)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0]["summary"], "Arthur mentioned the robotic arm")

    def test_multiple_events(self):
        for i in range(3):
            append_entity_event("arm", "arthur", f"Event {i}", source="user_message", base_dir=self.tmpdir)
        events = load_entity_events("arm", limit=10, base_dir=self.tmpdir)
        self.assertEqual(len(events), 3)

    def test_normalize_on_append(self):
        append_entity_event("Robotic Arm", "arthur", "Test", source="user_message", base_dir=self.tmpdir)
        events = load_entity_events("robotic_arm", base_dir=self.tmpdir)
        self.assertEqual(len(events), 1)

    def test_event_structure(self):
        result = append_entity_event("robotic_arm", "arthur",
                                      "We discussed gripper calibration",
                                      source="user_message", base_dir=self.tmpdir)
        self.assertEqual(result["event"]["record_type"], "entity_timeline_event_v1")
        self.assertEqual(result["event"]["entity_id"], "robotic_arm")
        self.assertEqual(result["event"]["user_id"], "arthur")
        self.assertEqual(result["event"]["summary"], "We discussed gripper calibration")
        self.assertEqual(result["event"]["source"], "user_message")
        self.assertEqual(result["event"]["authority"], "entity_memory_only")
        self.assertFalse(result["event"]["automatic_action"])
        self.assertFalse(result["event"]["hidden_learning"])
        self.assertFalse(result["event"]["raw_prompt_stored"])
        self.assertIn("timestamp", result["event"])

    def test_summary_truncated_at_500(self):
        long_summary = "x" * 600
        result = append_entity_event("test", "u", long_summary, source="user_message", base_dir=self.tmpdir)
        self.assertEqual(len(result["event"]["summary"]), 500)

    def test_metadata_passed_through(self):
        meta = {"experiment_id": "exp_001"}
        result = append_entity_event("test", "u", "summary", source="user_message",
                                     metadata=meta, base_dir=self.tmpdir)
        self.assertEqual(result["event"]["metadata"], meta)


class TestLoadEntityEvents(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_empty_for_nonexistent(self):
        events = load_entity_events("nonexistent", base_dir=self.tmpdir)
        self.assertEqual(events, [])

    def test_limit(self):
        for i in range(5):
            append_entity_event("arm", "u", f"Event {i}", source="user_message", base_dir=self.tmpdir)
        events = load_entity_events("arm", limit=2, base_dir=self.tmpdir)
        self.assertEqual(len(events), 2)

    def test_most_recent_first(self):
        # Append 3 events: Event 0, Event 1, Event 2 (in order)
        for i in range(3):
            append_entity_event("arm", "u", f"Event {i}", source="user_message", base_dir=self.tmpdir)
        events = load_entity_events("arm", limit=3, base_dir=self.tmpdir)
        # Most recent event (last written) is returned first
        self.assertEqual(events[0]["summary"], "Event 2")
        self.assertEqual(events[1]["summary"], "Event 1")
        self.assertEqual(events[2]["summary"], "Event 0")


class TestListEntityTimelines(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_empty(self):
        result = list_entity_timelines(base_dir=self.tmpdir)
        self.assertEqual(result, [])

    def test_lists_created(self):
        append_entity_event("robotic_arm", "u", "One", source="user_message", base_dir=self.tmpdir)
        append_entity_event("phoenix", "u", "Two", source="user_message", base_dir=self.tmpdir)
        result = list_entity_timelines(base_dir=self.tmpdir)
        self.assertEqual(sorted(result), ["phoenix", "robotic_arm"])

    def test_does_not_include_user_timelines(self):
        base = pathlib.Path(self.tmpdir)
        (base / "tl_user_arthur").mkdir()
        (base / "tl_entity_robotic_arm").mkdir()
        result = list_entity_timelines(base_dir=self.tmpdir)
        self.assertEqual(result, ["robotic_arm"])


class TestExtractEntitiesFromSummary(unittest.TestCase):
    def test_v1_stub_returns_empty(self):
        result = extract_entities_from_summary(
            "We worked on the robotic arm today",
            ["robotic_arm"],
        )
        self.assertEqual(result, [])


class TestSuggestEntityForContext(unittest.TestCase):
    def test_match_from_tags(self):
        entity_ids = ["robotic_arm"]
        result = suggest_entity_for_context("Tell me about the robotic arm", entity_ids)
        self.assertEqual(result, "robotic_arm")

    def test_match_from_metadata(self):
        entity_ids = ["robotic_arm"]
        result = suggest_entity_for_context("What about the robotic arm?", entity_ids)
        self.assertEqual(result, "robotic_arm")

    def test_no_match(self):
        entity_ids = ["robotic_arm"]
        result = suggest_entity_for_context("What is entropy?", entity_ids)
        self.assertIsNone(result)

    def test_no_events(self):
        result = suggest_entity_for_context("Tell me about robots", [])
        self.assertIsNone(result)

    def test_partial_word_match(self):
        # "robotics" is not "robotic" so it shouldn't match robotic_arm
        entity_ids = ["robotic_arm"]
        result = suggest_entity_for_context("Tell me about robotics", entity_ids)
        self.assertIsNone(result)

    def test_best_score_wins(self):
        entity_ids = ["robotic_arm", "robotic"]
        result = suggest_entity_for_context("Tell me about the robotic arm", entity_ids)
        self.assertEqual(result, "robotic_arm")  # 2-word match beats 1-word


class TestBuildEntityContinuityNote(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_no_events(self):
        note = build_entity_continuity_note("nonexistent", base_dir=self.tmpdir)
        self.assertEqual(note["record_type"], "entity_continuity_note_v1")
        self.assertEqual(note["events_used"], 0)
        self.assertIn("don't have any recorded history", note["message"])

    def test_single_event(self):
        append_entity_event("robotic_arm", "arthur", "Arthur mentioned gripper calibration",
                            source="user_message", base_dir=self.tmpdir)
        note = build_entity_continuity_note("robotic_arm", limit=3, base_dir=self.tmpdir)
        self.assertEqual(note["events_used"], 1)
        self.assertIn("gripper calibration", note["message"])
        self.assertEqual(note["authority"], "entity_memory_only")

    def test_multiple_events(self):
        for i in range(3):
            append_entity_event("robotic_arm", "arthur", f"Event {i}",
                                source="user_message", base_dir=self.tmpdir)
        note = build_entity_continuity_note("robotic_arm", limit=3, base_dir=self.tmpdir)
        self.assertEqual(note["events_used"], 3)
        # Should contain all 3 event summaries
        self.assertIn("Event 0", note["message"])
        self.assertIn("Event 1", note["message"])
        self.assertIn("Event 2", note["message"])


class TestWriteEntityFromUserMessage(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_writes_to_file(self):
        result = write_entity_from_user_message(
            "Robotic Arm", "arthur",
            "We discussed picking up the calibration block",
            source="user_message",
            base_dir=self.tmpdir,
        )
        self.assertEqual(result["status"], "appended")
        self.assertTrue(pathlib.Path(result["path"]).exists())

    def test_normalizes_name(self):
        result = write_entity_from_user_message(
            "Robotic Arm", "arthur", "Test", source="user_message", base_dir=self.tmpdir
        )
        self.assertEqual(result["event"]["entity_id"], "robotic_arm")


class TestContextBuilderIntegration(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        # Write a user timeline file so user_timeline_memory doesn't fail
        user_dir = pathlib.Path(self.tmpdir) / "tl_user_arthur"
        user_dir.mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_context_builder_returns_entity_events(self):
        append_entity_event("robotic_arm", "arthur",
                            "Arthur asked about gripper calibration",
                            source="user_message",
                            base_dir=self.tmpdir)

        from weslr.arbiter_context_builder import build_arbiter_context
        ctx = build_arbiter_context(
            user_id="arthur",
            current_message="What do we know about the robotic arm?",
            timeline_base_dir=self.tmpdir,
        )
        entity_evts = ctx.get("entity_timeline_events", [])
        self.assertGreater(len(entity_evts), 0)
        found = any(e.get("_entity_id") == "robotic_arm" for e in entity_evts)
        self.assertTrue(found)

    def test_entity_events_have_required_fields(self):
        append_entity_event("robotic_arm", "arthur",
                            "Arthur mentioned gripper",
                            source="user_message",
                            base_dir=self.tmpdir)

        from weslr.arbiter_context_builder import build_arbiter_context
        ctx = build_arbiter_context(
            user_id="arthur",
            current_message="robotic arm",
            timeline_base_dir=self.tmpdir,
        )
        for evt in ctx.get("entity_timeline_events", []):
            self.assertEqual(evt["record_type"], "entity_timeline_event_v1")
            self.assertEqual(evt["authority"], "entity_memory_only")
            self.assertFalse(evt["automatic_action"])
            self.assertFalse(evt["hidden_learning"])
            self.assertFalse(evt["raw_prompt_stored"])
            self.assertIn("summary", evt)
            self.assertIn("timestamp", evt)


# ─── Import everything from the module under test ─────────────────────────────
from weslr.entity_timeline_memory import (
    normalize_entity_id,
    get_entity_timeline_path,
    append_entity_event,
    load_entity_events,
    list_entity_timelines,
    extract_entities_from_summary,
    suggest_entity_for_context,
    write_entity_from_user_message,
    build_entity_continuity_note,
)


if __name__ == "__main__":
    unittest.main()