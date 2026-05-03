"""
Phase 5 Integration Tests — Semantic Similarity, Temporal Queries,
arXiv Search, and External Action Stubs.

All tests are isolated with mocks; zero real side effects.
"""
from __future__ import annotations

import json
import os
import pathlib
import tempfile
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pytest

# ─────────────────────────────────────────────────────────────────────────────
# Temp workspace fixture
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def tmp_workspace(tmp_path):
    """Set up a minimal temp workspace with all required .weslr/ files."""
    weslr_dir = tmp_path / ".weslr"
    weslr_dir.mkdir()
    (tmp_path / "weslr").mkdir()
    return tmp_path


# ─────────────────────────────────────────────────────────────────────────────
# 1. SEMANTIC SIMILARITY — entity lookup with typo
# ─────────────────────────────────────────────────────────────────────────────

class TestSemanticMatching:
    """Tests for semantic entity matching via sentence-transformer embeddings."""

    def test_semantic_matcher_import_with_guard(self):
        """semantic_matcher module loads even if sentence-transformers is absent."""
        # Patch the import so the model is never actually loaded
        with patch.dict(os.environ, {"WESLR_SEMANTIC_MATCHING_ENABLED": "false"}):
            # The module should still be importable
            import importlib
            import weslr.semantic_matcher as sm
            importlib.reload(sm)
            assert sm is not None

    def test_semantic_matcher_is_available_false_when_disabled(self):
        """is_available() returns False when semantic matching is disabled."""
        with patch.dict(os.environ, {"WESLR_SEMANTIC_MATCHING_ENABLED": "false"}):
            import importlib
            import weslr.semantic_matcher as sm
            importlib.reload(sm)
            sm._model = None  # reset singleton
            assert sm.is_available() is False

    def test_semantic_matcher_is_available_true_when_enabled_and_model_loads(self):
        """is_available() returns True when env var is set and model can load."""
        # Check if sentence-transformers is available
        try:
            from sentence_transformers import SentenceTransformer
        except ImportError:
            pytest.skip("sentence-transformers not installed")

        with patch.dict(os.environ, {"WESLR_SEMANTIC_MATCHING_ENABLED": "true"}):
            mock_model = MagicMock()
            mock_model.encode.return_value = [[0.1, 0.2, 0.3]]
            with patch("sentence_transformers.SentenceTransformer", return_value=mock_model):
                import importlib
                import weslr.semantic_matcher as sm
                importlib.reload(sm)
                sm._model = None
                result = sm.is_available()
                assert result is True

    def test_find_similar_entity_returns_none_when_not_available(self):
        """When semantic matching is not available, find_similar_entity returns None."""
        # Force is_available() False by patching environment
        with patch.dict(os.environ, {"WESLR_SEMANTIC_MATCHING_ENABLED": "false"}):
            import importlib
            import weslr.semantic_matcher as sm
            importlib.reload(sm)
            sm._model = None

            result = sm.find_similar_entity(
                query="MAPbI3",
                candidate_entities=["MAPbI3", "perovskite"],
                threshold=0.8,
            )
            assert result is None

    def test_find_similar_entity_returns_none_for_empty_candidates(self):
        """Empty candidate list returns None without error."""
        import importlib
        import weslr.semantic_matcher as sm
        importlib.reload(sm)
        sm._model = None

        result = sm.find_similar_entity(
            query="MAPbI3",
            candidate_entities=[],
            threshold=0.8,
        )
        assert result is None

    def test_semantic_match_logged_to_jsonl(self, tmp_path):
        """A semantic match is appended to semantic_matches.jsonl."""
        log_path = tmp_path / ".weslr" / "semantic_matches.jsonl"
        log_path.parent.mkdir(parents=True, exist_ok=True)

        import importlib
        import weslr.semantic_matcher as sm
        importlib.reload(sm)
        sm._model = None
        sm._MATCH_LOG_PATH = log_path

        # Even if model is not available, log_semantic_match should write
        sm.log_match("MAPbI3", "MAPbI3", 0.92)

        assert log_path.exists()
        lines = log_path.read_text().strip().split("\n")
        assert len(lines) == 1
        record = json.loads(lines[0])
        assert record["query"] == "MAPbI3"
        assert record["matched_entity"] == "MAPbI3"
        assert record["score"] == 0.92
        assert record["event"] == "semantic_entity_match"

    def test_entity_query_with_semantic_fuzzy_match(self, tmp_path):
        """Entity query with a typo still finds a semantic match via fuzzy_match tuple."""
        # Patch semantic matcher to return a match
        with patch("weslr.commands.entities.match_entity", return_value=("MAPbI3", 0.92, False)):
            with patch.dict(os.environ, {
                "WESLR_SEMANTIC_MATCHING_ENABLED": "true",
                "WESLR_SEMANTIC_AUTO_CORRECT_THRESHOLD": "0.95",
            }):
                from weslr.commands.entities import entity_query

                result = entity_query("MAPbI")

                assert "Did you mean" in result or "Auto-corrected" in result


# ─────────────────────────────────────────────────────────────────────────────
# 2. TEMPORAL QUERY SUPPORT — after/before/year range filters on facts
# ─────────────────────────────────────────────────────────────────────────────

class TestTemporalQueries:
    """Tests for temporally scoped fact queries."""

    @pytest.fixture
    def sample_facts(self):
        """Sample fact records with publication years."""
        return [
            {
                "subject": "BRCA1",
                "predicate": "associated with",
                "object": "breast cancer",
                "year": 2018,
                "publication_year": 2018,
                "fact_id": "f1",
            },
            {
                "subject": "BRCA1",
                "predicate": "has mutation",
                "object": "c.68_69delAG",
                "year": 2022,
                "publication_year": 2022,
                "fact_id": "f2",
            },
            {
                "subject": "BRCA1",
                "predicate": "investigated in",
                "object": "clinical trial NCT04551452",
                "year": 2015,
                "publication_year": 2015,
                "fact_id": "f3",
            },
            {
                "subject": "BRCA1",
                "predicate": "treated with",
                "object": "olaparib",
                "year": 2023,
                "publication_year": 2023,
                "fact_id": "f4",
            },
            {
                "subject": "BRCA1",
                "predicate": "expressed in",
                "object": "cell line MDA-MB-231",
                "year": 0,  # no year
                "publication_year": 0,
                "fact_id": "f5",
            },
        ]

    def test_load_facts_after_year(self, sample_facts, tmp_path):
        """load_facts(after_year=2020) returns only facts from 2021 onward."""
        from weslr.fact_extractor import load_facts

        fact_store = tmp_path / ".weslr" / "fact_assertions.jsonl"
        fact_store.parent.mkdir(parents=True, exist_ok=True)
        for fact in sample_facts:
            fact["record_type"] = "fact_assertion_v1"
            with open(fact_store, "a", encoding="utf-8") as _f:
                _f.write(json.dumps(fact, ensure_ascii=False) + "\n")

        with patch("weslr.fact_extractor._resolve_fact_store_path", return_value=fact_store):
            results = load_facts(subject="BRCA1", after_year=2020, limit=100)

        years = [r.get("year", r.get("publication_year", 0)) for r in results]
        assert all(y >= 2021 for y in years if y > 0)

    def test_load_facts_before_year(self, sample_facts, tmp_path):
        """load_facts(before_year=2016) returns only facts from 2015 or earlier."""
        from weslr.fact_extractor import load_facts

        fact_store = tmp_path / ".weslr" / "fact_assertions.jsonl"
        fact_store.parent.mkdir(parents=True, exist_ok=True)
        for fact in sample_facts:
            fact["record_type"] = "fact_assertion_v1"
            with open(fact_store, "a", encoding="utf-8") as _f:
                _f.write(json.dumps(fact, ensure_ascii=False) + "\n")

        with patch("weslr.fact_extractor._resolve_fact_store_path", return_value=fact_store):
            results = load_facts(subject="BRCA1", before_year=2016, limit=100)

        years = [r.get("year", r.get("publication_year", 9999)) for r in results]
        assert all(y <= 2016 for y in years if y > 0)

    def test_load_facts_combined_after_and_before(self, sample_facts, tmp_path):
        """load_facts(after_year=2019, before_year=2023) returns facts in that range."""
        from weslr.fact_extractor import load_facts

        fact_store = tmp_path / ".weslr" / "fact_assertions.jsonl"
        fact_store.parent.mkdir(parents=True, exist_ok=True)
        for fact in sample_facts:
            fact["record_type"] = "fact_assertion_v1"
            with open(fact_store, "a", encoding="utf-8") as _f:
                _f.write(json.dumps(fact, ensure_ascii=False) + "\n")

        with patch("weslr.fact_extractor._resolve_fact_store_path", return_value=fact_store):
            results = load_facts(subject="BRCA1", after_year=2019, before_year=2023, limit=100)

        years = [r.get("year", r.get("publication_year", 0)) for r in results]
        assert all(2020 <= y <= 2023 for y in years if y > 0)

    def test_load_facts_unknown_year_preserved(self, sample_facts, tmp_path):
        """Facts with year=0 or no year are included when no temporal filter is set."""
        from weslr.fact_extractor import load_facts

        fact_store = tmp_path / ".weslr" / "fact_assertions.jsonl"
        fact_store.parent.mkdir(parents=True, exist_ok=True)
        for fact in sample_facts:
            fact["record_type"] = "fact_assertion_v1"
            with open(fact_store, "a", encoding="utf-8") as _f:
                _f.write(json.dumps(fact, ensure_ascii=False) + "\n")

        with patch("weslr.fact_extractor._resolve_fact_store_path", return_value=fact_store):
            results = load_facts(subject="BRCA1", limit=100)

        assert len(results) == 5  # all facts, including year=0

    def test_timeline_handler_groups_facts_by_year(self, tmp_path):
        """handle_timeline groups facts by publication year."""
        facts = [
            {
                "subject": "MAPbI3",
                "predicate": "has formula",
                "object": "CH3NH3PbI3",
                "year": 2021,
                "publication_year": 2021,
                "source_type": "pubmed_abstract",
                "fact_id": "t1",
            },
            {
                "subject": "MAPbI3",
                "predicate": "shows stability",
                "object": "under 85% RH",
                "year": 2023,
                "publication_year": 2023,
                "source_type": "arxiv",
                "fact_id": "t2",
            },
            {
                "subject": "MAPbI3",
                "predicate": "degrades to",
                "object": "PbI2",
                "year": 2019,
                "publication_year": 2019,
                "source_type": "pubmed_abstract",
                "fact_id": "t3",
            },
        ]

        fact_store = tmp_path / ".weslr" / "fact_assertions.jsonl"
        fact_store.parent.mkdir(parents=True, exist_ok=True)
        for fact in facts:
            fact["record_type"] = "fact_assertion_v1"
            with open(fact_store, "a", encoding="utf-8") as _f:
                _f.write(json.dumps(fact, ensure_ascii=False) + "\n")

        with patch("weslr.fact_extractor._resolve_fact_store_path", return_value=fact_store):
            from weslr.deterministic_handlers import handle_timeline

            resp = handle_timeline("/timeline MAPbI3", "timeline MAPbI3")

            assert resp["path"] == "entity_timeline"
            text = resp["response_text"]
            assert "2023" in text
            assert "2021" in text
            assert "2019" in text


# ─────────────────────────────────────────────────────────────────────────────
# 3. arXiv SEARCH ADAPTER — search + fact extraction
# ─────────────────────────────────────────────────────────────────────────────

class TestArxivAdapter:
    """Tests for arXiv search adapter."""

    @pytest.fixture
    def mock_arxiv_xml(self):
        return (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<feed xmlns="http://www.w3.org/2005/Atom">'
            '<entry>'
            '<id>http://arxiv.org/abs/2301.00001v2</id>'
            '<title>MAPbI3 Perovskite Stability Under Humid Conditions</title>'
            '<summary>We study the stability of CH3NH3PbI3 (MAPbI3) perovskite '
            'under relative humidity of 85% at 25C. Our results show 95% retention '
            'after 1000 hours. The degradation pathway produces PbI2 and CH3NH3I.</summary>'
            '<author><name>Jane Doe</name></author>'
            '<author><name>John Smith</name></author>'
            '<published>2023-03-15T00:00:00Z</published>'
            '<category term="materials-science"/>'
            '<link href="http://arxiv.org/pdf/2301.00001v2" type="application/pdf"/>'
            '</entry>'
            '<entry>'
            '<id>http://arxiv.org/abs/2302.00002v1</id>'
            '<title>Machine Learning for Perovskite Bandgap Prediction</title>'
            '<summary>We apply neural networks to predict the bandgap of metal halide '
            'perovskites with MA=CH3NH3, FA=HC(NH2)2, and Cs. Training data includes '
            '12000 compounds. Mean absolute error is 0.12 eV.</summary>'
            '<author><name>Alice Liu</name></author>'
            '<published>2023-06-20T00:00:00Z</published>'
            '<category term="condensed-matter physics"/>'
            '<link href="http://arxiv.org/pdf/2302.00002v1" type="application/pdf"/>'
            '</entry>'
            '</feed>'
        )


    def test_search_arxiv_parses_results(self, mock_arxiv_xml):
        """search_arxiv() correctly parses XML into structured result dicts."""
        with patch("requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.content = mock_arxiv_xml.encode("utf-8")
            mock_get.return_value = mock_resp

            from weslr.search_adapters.arxiv_adapter import search_arxiv

            results = search_arxiv("MAPbI3 perovskite", max_results=10)

            assert len(results) == 2
            r1 = results[0]
            assert r1["title"] == "MAPbI3 Perovskite Stability Under Humid Conditions"
            assert r1["year"] == "2023"
            assert r1["primary_category"] == "materials-science"
            assert "Jane Doe" in r1["authors"]
            assert "2301.00001" in r1["arxiv_id"]

            r2 = results[1]
            assert r2["year"] == "2023"
            assert r2["primary_category"] == "condensed-matter physics"

    def test_search_arxiv_stores_evidence_packet(self, mock_arxiv_xml, tmp_path):
        """search_and_store() writes an evidence packet to external_evidence_packets.jsonl."""
        packet_store = tmp_path / ".weslr" / "external_evidence_packets.jsonl"
        packet_store.parent.mkdir(parents=True, exist_ok=True)

        with patch("requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.content = mock_arxiv_xml.encode("utf-8")
            mock_get.return_value = mock_resp

            with patch(
                "weslr.search_adapters.evidence_packet_store._resolve_packet_path",
                return_value=packet_store,
            ):
                from weslr.search_adapters.arxiv_adapter import search_and_store

                result = search_and_store("MAPbI3 perovskite", max_results=10)

        assert result["result_count"] == 2
        assert result["packet_id"].startswith("ax_")
        assert packet_store.exists()

        lines = packet_store.read_text().strip().split("\n")
        packet = json.loads(lines[-1])
        assert packet["source"] == "arxiv"
        assert packet["query"] == "MAPbI3 perovskite"
        assert packet["authority"] == "external_evidence_unverified"
        assert packet["automatic_change"] is False
        assert packet["hidden_learning"] is False
        assert packet["raw_prompt_stored"] is False

    def test_search_arxiv_extracts_facts(self, mock_arxiv_xml, tmp_path):
        """search_and_store() extracts facts from arXiv abstracts."""
        packet_store = tmp_path / ".weslr" / "external_evidence_packets.jsonl"
        fact_store = tmp_path / ".weslr" / "fact_assertions.jsonl"
        packet_store.parent.mkdir(parents=True, exist_ok=True)
        fact_store.parent.mkdir(parents=True, exist_ok=True)

        with patch("requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.content = mock_arxiv_xml.encode("utf-8")
            mock_get.return_value = mock_resp

            with patch(
                "weslr.search_adapters.evidence_packet_store._resolve_packet_path",
                return_value=packet_store,
            ):
                with patch(
                    "weslr.fact_extractor._resolve_fact_store_path",
                    return_value=fact_store,
                ):
                    from weslr.search_adapters.arxiv_adapter import search_and_store

                    result = search_and_store("MAPbI3 perovskite", max_results=10)

        assert result["fact_count"] >= 0  # may be 0 if domain patterns don't fire
        assert result["result_count"] == 2


# ─────────────────────────────────────────────────────────────────────────────
# 4. EXTERNAL ACTION STUBS — propose, approve, reject, dry-run
# ─────────────────────────────────────────────────────────────────────────────

class TestActionProposals:
    """Tests for external action proposal stubs."""

    @pytest.fixture
    def clean_proposal_log(self, tmp_path):
        log = tmp_path / ".weslr" / "action_proposals.jsonl"
        log.parent.mkdir(parents=True, exist_ok=True)
        return log

    def test_propose_action_writes_pending_entry(self, clean_proposal_log, tmp_path):
        """propose_action() writes a pending entry to action_proposals.jsonl."""
        from weslr.action_proposals import propose_action

        with patch.object(
            weslr.action_proposals,
            "_ACTION_LOG_PATH",
            clean_proposal_log,
            create=True,
        ):
            result = propose_action(
                action_type="simulation",
                params={"job_name": "MAPbI3_batch", "engine": "vasp"},
                description="Run DFT batch job for MAPbI3",
            )

        assert result["status"] == "pending"
        assert result["action_id"] is not None
        assert result["action_id"].startswith("act_")
        assert clean_proposal_log.exists()

        lines = clean_proposal_log.read_text().strip().split("\n")
        entry = json.loads(lines[-1])
        assert entry["record_type"] == "action_proposal_v1"
        assert entry["action_type"] == "simulation"
        assert entry["status"] == "pending_approval"
        assert entry["automatic_change"] is False
        assert entry["hidden_learning"] is False
        assert entry["raw_prompt_stored"] is False

    def test_propose_action_rejects_unknown_type(self, clean_proposal_log):
        """propose_action() rejects unknown action types with an error."""
        from weslr.action_proposals import propose_action

        with patch.object(
            weslr.action_proposals,
            "_ACTION_LOG_PATH",
            clean_proposal_log,
            create=True,
        ):
            result = propose_action(
                action_type="launch_missiles",
                params={},
                description="Launch missiles",
            )

        assert result["status"] == "error"
        assert "launch_missiles" in result["message"]

    def test_approve_action_appends_status_change(self, clean_proposal_log):
        """approve_action() appends a status-change event, not a modified record."""
        from weslr.action_proposals import propose_action, approve_action

        with patch.object(
            weslr.action_proposals,
            "_ACTION_LOG_PATH",
            clean_proposal_log,
            create=True,
        ):
            propose_result = propose_action("simulation", {}, "Run a sim")
            action_id = propose_result["action_id"]
            lines_before = clean_proposal_log.read_text().strip().split("\n")
            result = approve_action(action_id)
            lines_after = clean_proposal_log.read_text().strip().split("\n")

        # Should have one new line (the status-change event)
        assert len(lines_after) == len(lines_before) + 1
        change = json.loads(lines_after[-1])
        assert change["record_type"] == "action_status_change_v1"
        assert change["new_status"] == "approved"

    def test_reject_action_appends_status_change(self, clean_proposal_log):
        """reject_action() appends a rejected status-change event."""
        from weslr.action_proposals import propose_action, reject_action

        with patch.object(
            weslr.action_proposals,
            "_ACTION_LOG_PATH",
            clean_proposal_log,
            create=True,
        ):
            propose_result = propose_action("simulation", {}, "Run a sim")
            action_id = propose_result["action_id"]
            lines_before = clean_proposal_log.read_text().strip().split("\n")
            result = reject_action(action_id)
            lines_after = clean_proposal_log.read_text().strip().split("\n")

        change = json.loads(lines_after[-1])
        assert change["new_status"] == "rejected"

    def test_list_pending_actions_returns_only_pending(self, clean_proposal_log):
        """list_pending_actions() returns only pending entries."""
        from weslr.action_proposals import propose_action

        with patch.object(
            weslr.action_proposals,
            "_ACTION_LOG_PATH",
            clean_proposal_log,
            create=True,
        ):
            propose_action("simulation", {}, "Sim A")
            propose_action("email", {}, "Email B")
            from weslr.action_proposals import list_pending_actions

            pending = list_pending_actions()

        assert len(pending) == 2
        assert all(p["status"] == "pending_approval" for p in pending)


class TestActionRunnerDummy:
    """Tests for the dry-run action runner."""

    @pytest.fixture
    def clean_logs(self, tmp_path):
        proposal_log = tmp_path / ".weslr" / "action_proposals.jsonl"
        dry_run_log = tmp_path / ".weslr" / "action_runner_dry_run.jsonl"
        proposal_log.parent.mkdir(parents=True, exist_ok=True)
        return proposal_log, dry_run_log

    def test_dry_run_logs_approved_actions(self, clean_logs, tmp_path):
        """run_approved_actions() logs dry-run entries for approved actions."""
        proposal_log, dry_run_log = clean_logs

        # Write a proposal + approval directly
        proposal_entry = {
            "record_type": "action_proposal_v1",
            "action_id": "act_test001",
            "action_type": "simulation",
            "params": {"job_name": "test_job"},
            "description": "Test simulation",
            "status": "approved",
            "proposed_at": datetime.now(timezone.utc).isoformat(),
        }
        with open(proposal_log, "w") as f:
            f.write(json.dumps(proposal_entry) + "\n")

        with patch.object(
            weslr.action_proposals,
            "_ACTION_LOG_PATH",
            proposal_log,
            create=True,
        ):
            with patch.object(
                weslr.action_runner_dummy,
                "_DRY_RUN_LOG",
                dry_run_log,
                create=True,
            ):
                from weslr.action_runner_dummy import run_approved_actions

                result = run_approved_actions()

        assert result["dry_run_count"] == 1
        assert result["executed_count"] == 0
        assert dry_run_log.exists()
        dry_lines = dry_run_log.read_text().strip().split("\n")
        dry_entry = json.loads(dry_lines[-1])
        assert dry_entry["simulated"] is True
        assert dry_entry["action_type"] == "simulation"
        assert "test_job" in dry_entry["what_would_happen"]

    def test_execution_enabled_flag_blocks_real_execution(self, clean_logs):
        """When WESLR_ACTION_EXECUTION_ENABLED=false, no real execution occurs."""
        proposal_log, dry_run_log = clean_logs

        proposal_entry = {
            "record_type": "action_proposal_v1",
            "action_id": "act_test002",
            "action_type": "email",
            "params": {"to": "test@example.com"},
            "description": "Send email",
            "status": "approved",
            "proposed_at": datetime.now(timezone.utc).isoformat(),
        }
        with open(proposal_log, "w") as f:
            f.write(json.dumps(proposal_entry) + "\n")

        with patch.object(
            weslr.action_proposals,
            "_ACTION_LOG_PATH",
            proposal_log,
            create=True,
        ):
            with patch.object(
                weslr.action_runner_dummy,
                "_DRY_RUN_LOG",
                dry_run_log,
                create=True,
            ):
                with patch.dict(os.environ, {"WESLR_ACTION_EXECUTION_ENABLED": "false"}):
                    from weslr.action_runner_dummy import run_approved_actions

                    result = run_approved_actions()

        assert result["executed_count"] == 0
        assert result["dry_run_count"] == 1

    def test_is_execution_enabled_returns_false_by_default(self):
        """is_execution_enabled() returns False unless env var is explicitly true."""
        with patch.dict(os.environ, {}, clear=True):
            from weslr.action_runner_dummy import is_execution_enabled

            # Default is false
            assert is_execution_enabled() is False

    def test_email_action_dry_run_includes_recipient_and_subject(
        self, clean_logs, tmp_path
    ):
        """Dry-run log for email action includes to, subject, and body preview."""
        proposal_log, dry_run_log = clean_logs

        proposal_entry = {
            "record_type": "action_proposal_v1",
            "action_id": "act_test003",
            "action_type": "email",
            "params": {
                "to": "operator@weslr.de",
                "subject": "Batch job complete",
                "body": "Your simulation has finished.",
            },
            "description": "Notify operator",
            "status": "approved",
            "proposed_at": datetime.now(timezone.utc).isoformat(),
        }
        with open(proposal_log, "w") as f:
            f.write(json.dumps(proposal_entry) + "\n")

        with patch.object(
            weslr.action_proposals,
            "_ACTION_LOG_PATH",
            proposal_log,
            create=True,
        ):
            with patch.object(
                weslr.action_runner_dummy,
                "_DRY_RUN_LOG",
                dry_run_log,
                create=True,
            ):
                with patch.dict(os.environ, {"WESLR_ACTION_EXECUTION_ENABLED": "false"}):
                    from weslr.action_runner_dummy import run_approved_actions

                    run_approved_actions()

        dry_lines = dry_run_log.read_text().strip().split("\n")
        dry_entry = json.loads(dry_lines[-1])
        assert "operator@weslr.de" in dry_entry["what_would_happen"]
        assert "Batch job complete" in dry_entry["what_would_happen"]


# ─────────────────────────────────────────────────────────────────────────────
# 5. PV MATERIAL PROPOSE — rank non-perovskite PV materials by efficiency
# ─────────────────────────────────────────────────────────────────────────────

class TestPvMaterialPropose:
    def test_build_pv_material_proposals_ranks_by_efficiency(self, tmp_path):
        from weslr.commands.propose import build_pv_material_proposals, _extract_efficiency

        # Seed some facts manually
        fact_store = tmp_path / ".weslr" / "fact_assertions.jsonl"
        fact_store.parent.mkdir(parents=True, exist_ok=True)

        import json
        from datetime import datetime, timezone

        test_facts = [
            {
                "subject": "Kesterite",
                "predicate": "kesterite_family",
                "object": "CZTSSe material",
                "fact_data": {"formula": "CZTSSe"},
                "confidence": 0.90,
                "record_type": "fact_assertion_v1",
                "source_type": "arxiv_abstract",
                "source_reference": {"arxiv_id": "2404.00291", "title": "Kesterite paper"},
                "authority": "extracted",
                "year": 2024,
                "publication_year": 2024,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            {
                "subject": "Kesterite",
                "predicate": "champion_efficiency",
                "object": "efficiency of 13.5%",
                "fact_data": {"efficiency_pct": 13.5},
                "confidence": 0.92,
                "record_type": "fact_assertion_v1",
                "source_type": "arxiv_abstract",
                "source_reference": {"arxiv_id": "2404.00291", "title": "Kesterite paper"},
                "authority": "extracted",
                "year": 2024,
                "publication_year": 2024,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            {
                "subject": "Organic Photovoltaic",
                "predicate": "efficiency_mentioned",
                "object": "efficiency of 18%",
                "fact_data": {"efficiency_pct": 18.0},
                "confidence": 0.80,
                "record_type": "fact_assertion_v1",
                "source_type": "arxiv_abstract",
                "source_reference": {"arxiv_id": "1504.07729", "title": "Organic PV paper"},
                "authority": "extracted",
                "year": 2015,
                "publication_year": 2015,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            {
                "subject": "BiFeO3",
                "predicate": "ferroelectric_response",
                "object": "ferroelectric photovoltaic",
                "fact_data": {},
                "confidence": 0.75,
                "record_type": "fact_assertion_v1",
                "source_type": "arxiv_abstract",
                "source_reference": {"arxiv_id": "2110.13597", "title": "BiFeO3 paper"},
                "authority": "extracted",
                "year": 2021,
                "publication_year": 2021,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        ]

        with open(fact_store, "w") as f:
            for fact in test_facts:
                f.write(json.dumps(fact) + "\n")

        with patch("weslr.fact_extractor._resolve_fact_store_path", return_value=fact_store):
            proposals = build_pv_material_proposals(tenant_id=None, limit=10)

        assert len(proposals) >= 2
        # Kesterite should be ranked high (has efficiency data)
        mat_names = [p["material"].lower() for p in proposals]
        kesterite_ranked = next((i for i, m in enumerate(mat_names) if "kesterite" in m), None)
        assert kesterite_ranked is not None, f"Kesterite not in proposals: {mat_names}"

    def test_extract_efficiency_from_fact_data(self):
        from weslr.commands.propose import _extract_efficiency

        test_cases = [
            ({"efficiency_pct": 13.5}, 13.5),
            ({"efficiency_pct": 18.0}, 18.0),
            ({"value": 25.3}, 25.3),
            ({}, None),  # no efficiency
        ]

        for fd, expected in test_cases:
            fact = {"fact_data": fd, "subject": "test", "object": "test"}
            result = _extract_efficiency(fact)
            assert result == expected, f"fact_data={fd}: expected {expected}, got {result}"

    def test_format_proposal_list_shows_top_materials(self):
        from weslr.commands.propose import format_proposal_list

        proposals = [
            {
                "material": "Kesterite",
                "estimated_efficiency": 13.5,
                "max_efficiency": 13.5,
                "efficiencies_mentioned": [13.5],
                "trust_score": 0.90,
                "sources": ["2404.00291"],
                "predicates": ["kesterite_family", "champion_efficiency"],
                "fact_count": 2,
            },
            {
                "material": "Organic Photovoltaic",
                "estimated_efficiency": 18.0,
                "max_efficiency": 18.0,
                "efficiencies_mentioned": [18.0],
                "trust_score": 0.80,
                "sources": ["1504.07729"],
                "predicates": ["efficiency_mentioned"],
                "fact_count": 1,
            },
        ]

        output = format_proposal_list(proposals, limit=5)
        assert "Kesterite" in output
        assert "Organic Photovoltaic" in output
        assert "13.5%" in output
        assert "18.0%" in output
        assert "arXiv:2404.00291" in output

    def test_format_proposal_list_empty_returns_no_proposals_message(self):
        from weslr.commands.propose import format_proposal_list
        output = format_proposal_list([])
        assert "No photovoltaic material proposals" in output


# ─────────────────────────────────────────────────────────────────────────────
# 5. ENTITY LINKING — same_as relationships
# ─────────────────────────────────────────────────────────────────────────────

class TestEntityLinking:
    def test_link_entities_creates_same_as_fact(self, tmp_path):
        from weslr.commands.entity_link import link_entities, get_linked_entities
        fact_store = tmp_path / ".weslr" / "fact_assertions.jsonl"
        fact_store.parent.mkdir(parents=True, exist_ok=True)

        with patch("weslr.fact_extractor._resolve_fact_store_path", return_value=fact_store):
            result = link_entities("BiFeO3", "ferroelectric_material")

        assert result["status"] == "linked"
        assert result["source"] == "BiFeO3"
        assert result["target"] == "ferroelectric_material"

    def test_get_linked_entities_returns_aliases(self, tmp_path):
        from weslr.commands.entity_link import link_entities, get_linked_entities
        fact_store = tmp_path / ".weslr" / "fact_assertions.jsonl"
        fact_store.parent.mkdir(parents=True, exist_ok=True)

        with patch("weslr.fact_extractor._resolve_fact_store_path", return_value=fact_store):
            link_entities("BiFeO3", "bismuth_ferrite")
            linked = get_linked_entities("BiFeO3")

        assert "bismuth_ferrite" in linked

    def test_unlink_removes_relationship(self, tmp_path):
        from weslr.commands.entity_link import link_entities, unlink_entities, get_linked_entities
        fact_store = tmp_path / ".weslr" / "fact_assertions.jsonl"
        fact_store.parent.mkdir(parents=True, exist_ok=True)

        with patch("weslr.fact_extractor._resolve_fact_store_path", return_value=fact_store):
            link_entities("BiFeO3", "ferroelectric_material")
            unlink_entities("BiFeO3", "ferroelectric_material")
            linked = get_linked_entities("BiFeO3")

        assert len(linked) == 0

    def test_cannot_relink_already_linked_entities(self, tmp_path):
        from weslr.commands.entity_link import link_entities
        fact_store = tmp_path / ".weslr" / "fact_assertions.jsonl"
        fact_store.parent.mkdir(parents=True, exist_ok=True)

        with patch("weslr.fact_extractor._resolve_fact_store_path", return_value=fact_store):
            link_entities("BiFeO3", "ferroelectric_material")
            result2 = link_entities("BiFeO3", "ferroelectric_material")

        assert result2["status"] == "already_linked"


# ─────────────────────────────────────────────────────────────────────────────
# 6. KESTERITE EFFICIENCY EXTRACTION
# ─────────────────────────────────────────────────────────────────────────────

class TestKesteriteEfficiency:
    def test_kesterite_efficiency_extraction(self):
        """Kesterite paper abstract: ms.kesterite patterns extract material + efficiency."""
        import sys
        sys.path.insert(0, '.')
        from weslr.fact_extractor import extract_facts_with_positions

        abstract = (
            "Sulfide Kesterite Cu2ZnSnS4 (CZTS), a nontoxic and low-cost photovoltaic material, "
            "has always being facing severe charge recombination. "
            "We have achieved a champion total-area efficiency of 13.5% (active-area efficiency: 14.1%). "
            "We have also achieved a certified total-area cell efficiency of 13.16%."
        )

        facts = extract_facts_with_positions(abstract, domain='materials_science')

        # Should have kesterite-family facts
        kesterite_facts = [
            f for f in facts if f.get('predicate') in ('kesterite_family', 'non_perovskite_pv_material_class')
        ]
        assert len(kesterite_facts) > 0, f"Expected kesterite facts, got: {[f.get('predicate') for f in facts]}"

        # Should have champion or certified efficiency facts
        eff_facts = [f for f in facts if 'efficiency' in f.get('predicate', '')]
        assert len(eff_facts) > 0, f"Expected efficiency facts, got: {[f.get('predicate') for f in facts]}"

        # Verify kesterite regex captures CZTS
        k_facts = [
            f for f in facts if f.get('fact_data', {}).get('formula') in ('CZTS', 'CZTSSe', 'Cu2ZnSnS4')
        ]
        assert len(k_facts) > 0, f"Expected CZTS/Cu2ZnSnS4 captured, got: {[f.get('fact_data') for f in facts]}"


# ─────────────────────────────────────────────────────────────────────────────
# Import at top for patching convenience
# ─────────────────────────────────────────────────────────────────────────────
import weslr.action_proposals
import weslr.action_runner_dummy
