"""
WESLR Consolidation Loop — Tests

Tests the consolidation_loop module and consolidation_commands CLI.
Uses temp dirs only. Does not touch real .weslr.
"""

from __future__ import annotations

import json
import os
import pathlib
import tempfile
import shutil
import sys

sys.path.insert(0, "/data/data/com.termux/files/home/.openclaw/workspace")

from weslr.consolidation_loop import (
    Trace,
    Cluster,
    ConsolidationCandidate,
    ConsolidationDigestResult,
    collect_traces,
    cluster_traces,
    score_cluster,
    classify_destination,
    make_candidate,
    write_digest,
    run_consolidation_digest,
    build_text_summary,
    _DIGEST_FILENAME,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def make_temp_weslr():
    """Create a temp .weslr directory."""
    td = tempfile.mkdtemp()
    weslr_dir = pathlib.Path(td) / ".weslr"
    weslr_dir.mkdir()
    return td, weslr_dir


def write_pending_messages(weslr_dir: pathlib.Path, records: list[dict]) -> None:
    p = weslr_dir / "pending_messages.jsonl"
    with open(p, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec) + "\n")


def write_missions(weslr_dir: pathlib.Path, records: list[dict]) -> None:
    p = weslr_dir / "missions.jsonl"
    with open(p, "w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec) + "\n")


NOW = "2026-05-07T12:00:00+00:00"
YESTERDAY = "2026-05-06T12:00:00+00:00"
OLD = "2026-04-01T12:00:00+00:00"


# ---------------------------------------------------------------------------
# Test 1: Missing files produce empty result
# ---------------------------------------------------------------------------

def test_missing_files_empty_result():
    td, weslr_dir = make_temp_weslr()
    try:
        traces = collect_traces(root=td, hours=24)
        assert traces == [], f"Expected empty, got {len(traces)} traces"
        clusters = cluster_traces([])
        assert clusters == []
        result = run_consolidation_digest(root=td, hours=24)
        assert result.traces_collected == 0
        assert result.clusters_found == 0
        assert result.candidates_written == 0
    finally:
        shutil.rmtree(td)


# ---------------------------------------------------------------------------
# Test 2: Collect pending_messages from temp .weslr
# ---------------------------------------------------------------------------

def test_collect_pending_messages():
    td, weslr_dir = make_temp_weslr()
    try:
        write_pending_messages(weslr_dir, [
            {
                "record_type": "mission_suggestion",
                "message_id": "msg_001",
                "mission_id": "m_aaa",
                "suggestion": "Add evidence for: bandgap of kesterite solar cells",
                "confidence": 0.8,
                "priority": "medium",
                "enqueued_at": NOW,
                "provenance": "run_once_mission_review @ 2026-05-07",
            },
            {
                "record_type": "pending_message_v1",
                "message_id": "msg_002",
                "queue_type": "proactive",
                "message": "Consider testing the continuity note bridge",
                "priority": "low",
                "enqueued_at": NOW,
            },
        ])
        traces = collect_traces(root=td, hours=24)
        assert len(traces) == 2, f"Expected 2, got {len(traces)}"
        themes = {t.theme for t in traces}
        assert "solar_materials" in themes, f"Missing solar_materials theme: {themes}"
        assert "continuity_memory" in themes, f"Missing continuity_memory theme: {themes}"
    finally:
        shutil.rmtree(td)


# ---------------------------------------------------------------------------
# Test 3: Collect missions from temp .weslr
# ---------------------------------------------------------------------------

def test_collect_missions():
    td, weslr_dir = make_temp_weslr()
    try:
        write_missions(weslr_dir, [
            {
                "mission_id": "m_test_001",
                "title": "Soft micro-robotics material candidates",
                "research_goal": "Identify safe materials for soft robotics actuators",
                "current_questions": ["What properties enable reversible actuation?"],
                "status": "active",
                "created_at": NOW,
                "last_reviewed_at": NOW,
            },
        ])
        traces = collect_traces(root=td, hours=48)
        assert len(traces) == 1, f"Expected 1, got {len(traces)}"
        assert traces[0].source_type == "mission"
        assert traces[0].mission_id == "m_test_001"
        assert traces[0].theme == "soft_robotics"
    finally:
        shutil.rmtree(td)


# ---------------------------------------------------------------------------
# Test 4: Cluster repeated themes
# ---------------------------------------------------------------------------

def test_cluster_repeated_themes():
    traces = [
        Trace("t1", "pm.jsonl", "mission_suggestion", "solar_materials", "research_question",
              mission_id="m1", created_at=NOW),
        Trace("t2", "pm.jsonl", "mission_suggestion", "solar_materials", "research_question",
              mission_id="m1", created_at=NOW),
        Trace("t3", "pm.jsonl", "mission_suggestion", "solar_materials", "research_question",
              mission_id="m1", created_at=YESTERDAY),
        Trace("t4", "pm.jsonl", "pending_message", "continuity_memory", "continuity",
              created_at=NOW),
    ]
    clusters = cluster_traces(traces)
    # Two clusters: solar_materials (all 3 with mission_id=m1), continuity_memory (1 trace)
    assert len(clusters) == 2, f"Expected 2 clusters, got {len(clusters)}"
    solar = next(c for c in clusters if "solar" in c.theme)
    assert len(solar.traces) == 3, f"solar_materials should have 3 traces, got {len(solar.traces)}"
    assert solar.first_seen == YESTERDAY
    assert solar.last_seen == NOW


# ---------------------------------------------------------------------------
# Test 5: Score includes frequency/recency/source_diversity
# ---------------------------------------------------------------------------

def test_score_includes_fields():
    traces = [
        Trace("t1", "pm.jsonl", "mission_suggestion", "solar_materials", "research_question",
              created_at=NOW, confidence=0.9),
        Trace("t2", "pm.jsonl", "mission_suggestion", "solar_materials", "research_question",
              created_at=YESTERDAY, confidence=0.7),
        Trace("t3", "pm.jsonl", "pending_message", "solar_materials", "research_question",
              created_at=NOW, confidence=0.5),
    ]
    clusters = cluster_traces(traces)
    scores = [score_cluster(c) for c in clusters]
    s = scores[0]
    assert "frequency" in s
    assert "recency" in s
    assert "source_diversity" in s
    assert "avg_confidence" in s
    assert "overall" in s
    assert s["frequency"] == 3
    assert s["source_diversity"] == 2  # mission_suggestion + pending_message
    assert s["avg_confidence"] == round((0.9 + 0.7 + 0.5) / 3, 3)


# ---------------------------------------------------------------------------
# Test 6: Classify mission cluster as mission_store
# ---------------------------------------------------------------------------

def test_classify_mission_cluster():
    traces = [
        Trace("t1", "missions.jsonl", "mission", "mission_tracking", "mission_progress",
              mission_id="m_test", created_at=NOW),
    ]
    clusters = cluster_traces(traces)
    dest, risk, note = classify_destination(clusters[0])
    assert dest == "mission_store", f"Expected mission_store, got {dest}"
    assert risk == "low"


# ---------------------------------------------------------------------------
# Test 7: Write digest JSONL
# ---------------------------------------------------------------------------

def test_write_digest_jsonl():
    td, weslr_dir = make_temp_weslr()
    try:
        traces = [
            Trace("t1", "pm.jsonl", "mission_suggestion", "solar_materials",
                  "research_question", created_at=NOW, confidence=0.8),
        ]
        clusters = cluster_traces(traces)
        candidates = [make_candidate(c) for c in clusters]
        out_dir, out_file, count = write_digest(candidates, root=td)
        assert out_file == _DIGEST_FILENAME
        assert count == 1
        digest_path = pathlib.Path(out_dir) / out_file
        assert digest_path.exists()
        with open(digest_path, encoding="utf-8") as f:
            records = [json.loads(line) for line in f if line.strip()]
        assert len(records) == 1
        assert records[0]["type"] == "consolidation_candidate"
        assert records[0]["theme"] == "solar_materials"
    finally:
        shutil.rmtree(td)


# ---------------------------------------------------------------------------
# Test 8: Digest records have automatic_execution=false
# ---------------------------------------------------------------------------

def test_digest_automatic_execution_false():
    td, weslr_dir = make_temp_weslr()
    try:
        write_pending_messages(weslr_dir, [
            {
                "record_type": "mission_suggestion",
                "message_id": "msg_999",
                "mission_id": "m_test",
                "suggestion": "Add evidence for: bandgap question",
                "confidence": 0.7,
                "enqueued_at": NOW,
                "provenance": "test",
            },
        ])
        result = run_consolidation_digest(root=td, hours=24)
        for rec in result.digest_records:
            assert rec["automatic_execution"] is False, \
                f"Expected False, got {rec['automatic_execution']}"
    finally:
        shutil.rmtree(td)


# ---------------------------------------------------------------------------
# Test 9: Digest records have promotion_performed=false
# ---------------------------------------------------------------------------

def test_digest_promotion_performed_false():
    td, weslr_dir = make_temp_weslr()
    try:
        write_pending_messages(weslr_dir, [
            {
                "record_type": "mission_suggestion",
                "message_id": "msg_888",
                "mission_id": "m_test2",
                "suggestion": "Research question",
                "confidence": 0.6,
                "enqueued_at": NOW,
                "provenance": "test",
            },
        ])
        result = run_consolidation_digest(root=td, hours=24)
        for rec in result.digest_records:
            assert rec["promotion_performed"] is False, \
                f"Expected False, got {rec['promotion_performed']}"
    finally:
        shutil.rmtree(td)


# ---------------------------------------------------------------------------
# Test 10: No writes to entity_memory / mission_store / doctrine
# ---------------------------------------------------------------------------

def test_no_promotion_side_effects():
    td, weslr_dir = make_temp_weslr()
    try:
        # Write a real-seeming pending message
        write_pending_messages(weslr_dir, [
            {
                "record_type": "mission_suggestion",
                "message_id": "msg_777",
                "mission_id": "m_sidefx",
                "suggestion": "Add evidence for: test question",
                "confidence": 0.7,
                "enqueued_at": NOW,
                "provenance": "test",
            },
        ])
        # Also create entity_memory and mission_store dirs to prove we don't touch them
        entity_mem_dir = weslr_dir / "entity_memory"
        entity_mem_dir.mkdir()
        real_mem_file = entity_mem_dir / "test_entity" / "memory.jsonl"
        real_mem_file.parent.mkdir(parents=True, exist_ok=True)
        real_mem_file.write_text('{"test": "original"}\n', encoding="utf-8")

        mission_file = weslr_dir / "missions.jsonl"
        mission_file.write_text('{"test": "original"}\n', encoding="utf-8")

        # Run consolidation
        result = run_consolidation_digest(root=td, hours=24)

        # Verify: entity_memory not modified
        with open(real_mem_file, encoding="utf-8") as f:
            content = f.read()
        assert content == '{"test": "original"}\n', \
            f"entity_memory was modified! Content: {content}"

        # Verify: mission_store not modified
        with open(mission_file, encoding="utf-8") as f:
            content = f.read()
        assert content == '{"test": "original"}\n', \
            f"mission_store was modified! Content: {content}"

        # Verify: consolidation_digest was created
        digest_path = weslr_dir / _DIGEST_FILENAME
        assert digest_path.exists()
    finally:
        shutil.rmtree(td)


# ---------------------------------------------------------------------------
# Test 11: Command help works
# ---------------------------------------------------------------------------

def test_command_help():
    from weslr.commands.consolidation_commands import handle_consolidation
    import io
    import sys as _sys

    old_stdout = _sys.stdout
    _sys.stdout = io.StringIO()
    try:
        rc = handle_consolidation(["help"])
    finally:
        output = _sys.stdout.getvalue()
        _sys.stdout = old_stdout
    assert rc == 0
    assert "consolidation" in output.lower()
    assert "run" in output.lower()


# ---------------------------------------------------------------------------
# Test 12: Command run writes digest
# ---------------------------------------------------------------------------

def test_command_run():
    from weslr.commands.consolidation_commands import handle_consolidation
    td, weslr_dir = make_temp_weslr()
    try:
        write_pending_messages(weslr_dir, [
            {
                "record_type": "mission_suggestion",
                "message_id": "msg_cli_001",
                "mission_id": "m_cli",
                "suggestion": "Add evidence for: what is kesterite efficiency?",
                "confidence": 0.8,
                "enqueued_at": NOW,
                "provenance": "test",
            },
        ])
        rc = handle_consolidation(["run", "--base-path", td])
        assert rc == 0
        digest_path = weslr_dir / _DIGEST_FILENAME
        assert digest_path.exists()
        with open(digest_path, encoding="utf-8") as f:
            records = [json.loads(line) for line in f if line.strip()]
        assert len(records) >= 1
        assert records[0]["promotion_performed"] is False
        assert records[0]["automatic_execution"] is False
    finally:
        shutil.rmtree(td)


# ---------------------------------------------------------------------------
# Test 13: Command status reports output path/count
# ---------------------------------------------------------------------------

def test_command_status_no_digest():
    from weslr.commands.consolidation_commands import handle_consolidation
    td, weslr_dir = make_temp_weslr()
    try:
        rc = handle_consolidation(["status", "--base-path", td])
        # No digest exists yet — should return non-zero
        assert rc == 1
    finally:
        shutil.rmtree(td)


# ---------------------------------------------------------------------------
# Test 14: Governance gate — doctrine theme flagged as high risk
# ---------------------------------------------------------------------------

def test_doctrine_theme_high_risk():
    traces = [
        Trace("t1", "pm.jsonl", "pending_message", "doctrine_governance",
              "governance", created_at=NOW),
    ]
    clusters = cluster_traces(traces)
    dest, risk, note = classify_destination(clusters[0])
    assert risk == "high", f"Expected high risk for doctrine theme, got {risk}"
    assert dest == "validation_gap"
    assert "no auto-promotion" in note.lower()


# ---------------------------------------------------------------------------
# Test 15: Evidence gap cluster → evidence_hypothesis destination
# ---------------------------------------------------------------------------

def test_evidence_gap_classification():
    traces = [
        Trace("t1", "pm.jsonl", "mission_suggestion", "evidence_gap",
              "evidence_gap", created_at=NOW, confidence=0.7),
    ]
    clusters = cluster_traces(traces)
    dest, risk, note = classify_destination(clusters[0])
    assert dest == "evidence_hypothesis"
    assert risk == "low"


# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import traceback

    tests = [
        t for t in globals().values()
        if callable(t) and t.__name__.startswith("test_")
    ]

    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            print(f"PASS  {test.__name__}")
            passed += 1
        except Exception as e:
            print(f"FAIL  {test.__name__}: {e}")
            traceback.print_exc()
            failed += 1

    print(f"\n{passed}/{passed+failed} passed, {failed} failed")
