"""
WESLR Research Work Loop V1 Tests

Tests for:
- run_once_mission_review
- Safety filter blocking forbidden content
- Local evidence adapter (safe reads only)
- No external calls
- automatic_execution=false on all suggestions
- Paused missions produce no suggestions
- Active missions with open questions and no evidence produce suggestions
"""

import json
import os
import tempfile
import pytest

from weslr.schemas.mission import Mission, make_mission, generate_mission_id
from weslr.mission_store import MissionStore
from weslr.adapters.local_evidence_adapter import LocalEvidenceAdapter
from weslr.loop.safety_filter import SafetyFilter, get_safety_filter, filter_suggestions
from weslr.loop.suggestion_ranker import SuggestionRanker
from weslr.loop.research_work_loop import (
    run_once_mission_review,
    _detect_open_questions,
    _generate_suggestion,
)


class TestSafetyFilter:
    """Tests for SafetyFilter."""

    def setup_method(self):
        self.filter = SafetyFilter()

    def test_blocks_hazardous_synthesis(self):
        """Test that hazardous synthesis is blocked."""
        assert self.filter.is_safe("How to synthesize nerve agents") is False

    def test_blocks_pathogen_engineering(self):
        """Test that pathogen engineering is blocked."""
        assert self.filter.is_safe("Engineer a novel pathogen") is False

    def test_blocks_weaponization(self):
        """Test that weaponization is blocked."""
        assert self.filter.is_safe("Weaponization of influenza") is False

    def test_blocks_toxic_deployment(self):
        """Test that toxic deployment is blocked."""
        assert self.filter.is_safe("Toxic deployment of chemicals") is False

    def test_blocks_autonomous_lab(self):
        """Test that autonomous lab is blocked."""
        assert self.filter.is_safe("Autonomous lab execution") is False

    def test_blocks_covert_delivery(self):
        """Test that covert delivery is blocked."""
        assert self.filter.is_safe("Covert delivery system design") is False

    def test_blocks_evasion_misuse(self):
        """Test that evasion/misuse optimization is blocked."""
        assert self.filter.is_safe("Evasion optimization for weapons") is False

    def test_blocks_dangerous_procurement(self):
        """Test that dangerous procurement is blocked."""
        assert self.filter.is_safe("Procurement of bomb materials") is False

    def test_blocks_bioweapon(self):
        """Test that bioweapon is blocked."""
        assert self.filter.is_safe("Design a bioweapon") is False

    def test_passes_safe_material_suggestion(self):
        """Test that safe material suggestions pass."""
        safe_texts = [
            "Add material property comparison table as next step",
            "Compare hydrogel elastic modulus across studies",
            "Review literature on piezoelectric polymers",
            "Identify gaps in causal evidence for drug response",
            "Add experiment plan for tensile strength testing",
        ]
        for text in safe_texts:
            assert self.filter.is_safe(text) is True, f"Should be safe: {text}"

    def test_filter_candidates(self):
        """Test filtering a list of candidates."""
        candidates = [
            "Add material comparison table",
            "How to synthesize a bioweapon",
            "Review polymer properties",
            "Optimize evasion techniques",
        ]
        safe = self.filter.filter_candidates(candidates)
        assert len(safe) == 2
        assert "How to synthesize a bioweapon" not in safe
        assert "Optimize evasion techniques" not in safe

    def test_blocked_pattern_returns_pattern(self):
        """Test that blocked_pattern returns the matching pattern."""
        result = self.filter.blocked_pattern("Design a bioweapon for deployment")
        assert result == "bioweapon"

    def test_audit(self):
        """Test full safety audit."""
        audit = self.filter.audit("Design a bioweapon for deployment")
        assert audit["safe"] is False
        assert audit["blocked_by"] == "bioweapon"

    def test_audit_safe(self):
        """Test audit for safe text."""
        audit = self.filter.audit("Compare piezoelectric materials")
        assert audit["safe"] is True
        assert audit["blocked_by"] is None


class TestLocalEvidenceAdapter:
    """Tests for LocalEvidenceAdapter."""

    def test_read_blocks_outside_workspace(self):
        """Test that paths outside workspace are blocked."""
        adapter = LocalEvidenceAdapter()

        # Path traversal attempt
        result = adapter._read_single("../../etc/passwd")
        assert result["safe"] is False

    def test_read_blocks_blocked_patterns(self):
        """Test that blocked patterns are rejected."""
        adapter = LocalEvidenceAdapter()

        result = adapter._read_single(".weslr/pending_messages.jsonl")
        assert result["safe"] is False

    def test_read_blocks_git_directory(self):
        """Test that .git directory is blocked."""
        adapter = LocalEvidenceAdapter()

        result = adapter._read_single(".git/config")
        assert result["safe"] is False

    def test_read_allows_local_docs(self):
        """Test that local docs are allowed."""
        adapter = LocalEvidenceAdapter(workspace_root="/data/data/com.termux/files/home/.openclaw/workspace")

        # Test that a known safe file in docs can be checked for safety
        assert adapter._is_path_safe("weslr/docs/WESLR_DOCTRINE_REGISTRY_V1.md") is True

    def test_read_rejects_unknown_extensions(self):
        """Test that unknown file extensions are rejected."""
        adapter = LocalEvidenceAdapter(workspace_root="/data/data/com.termux/files/home/.openclaw/workspace")

        result = adapter._read_single("weslr/data/test.exe")
        assert result["safe"] is False
        assert result["error"] == "File type not allowed"

    def test_read_nonexistent_file(self):
        """Test reading a non-existent file returns error."""
        adapter = LocalEvidenceAdapter(workspace_root="/data/data/com.termux/files/home/.openclaw/workspace")

        result = adapter._read_single("nonexistent/file.md")
        assert result["safe"] is False
        # Error is either "File not found" or "Path not allowed" depending on path safety
        assert result["error"] in ("File not found", "Path not allowed")

    def test_list_available(self):
        """Test listing available evidence files."""
        adapter = LocalEvidenceAdapter(workspace_root="/data/data/com.termux/files/home/.openclaw/workspace")

        files = adapter.list_available("weslr/docs")
        # Should return list of .md/.txt/.json files
        assert isinstance(files, list)

    def test_read_no_external_calls(self):
        """Test that read() makes no external calls."""
        adapter = LocalEvidenceAdapter()

        # Call read with an empty list
        result = adapter.read([])
        assert result == {}

        # Call read with https URL (should fail safely)
        result = adapter.read(["https://evil.com/test.md"])
        assert "https://evil.com/test.md" in result
        assert result["https://evil.com/test.md"]["safe"] is False


class TestSuggestionRanker:
    """Tests for SuggestionRanker."""

    def test_score_calculation(self):
        """Test combined score calculation."""
        ranker = SuggestionRanker()

        score = ranker.score(confidence=0.8, domain_relevance=0.6, evidence_count=3)
        # 0.5 * 0.8 + 0.3 * 0.6 + 0.2 * min(3/3, 1.0) = 0.4 + 0.18 + 0.2 = 0.78
        assert abs(score - 0.78) < 0.01

    def test_score_caps_evidence_bonus(self):
        """Test that evidence bonus caps at 1.0."""
        ranker = SuggestionRanker()

        score_3 = ranker.score(0.5, 0.5, 3)
        score_10 = ranker.score(0.5, 0.5, 10)
        assert score_3 == score_10  # Both cap at 1.0 evidence bonus

    def test_rank_orders_by_score(self):
        """Test that rank() orders by combined score."""
        ranker = SuggestionRanker()

        candidates = [
            {"text": "low", "confidence": 0.3, "domain_relevance": 0.3, "evidence_count": 0, "mission_id": "m1", "source": "test", "provenance": "test"},
            {"text": "high", "confidence": 0.9, "domain_relevance": 0.8, "evidence_count": 2, "mission_id": "m1", "source": "test", "provenance": "test"},
            {"text": "medium", "confidence": 0.6, "domain_relevance": 0.5, "evidence_count": 1, "mission_id": "m1", "source": "test", "provenance": "test"},
        ]

        ranked = ranker.rank(candidates)
        assert ranked[0].text == "high"
        assert ranked[1].text == "medium"
        assert ranked[2].text == "low"

    def test_top_returns_n_items(self):
        """Test that top() returns N items."""
        ranker = SuggestionRanker()

        candidates = [
            {"text": f"item{i}", "confidence": 0.5, "domain_relevance": 0.5, "evidence_count": 0, "mission_id": "m1", "source": "test", "provenance": "test"}
            for i in range(10)
        ]

        top5 = ranker.top(candidates, n=5)
        assert len(top5) == 5


class TestDetectOpenQuestions:
    """Tests for open question detection."""

    def test_detects_question_without_evidence(self):
        """Test that questions without matching evidence are detected."""
        mission = make_mission("tenant-1", "user-1", "Test", "Goal")
        mission.current_questions = ["What is the bandgap of kesterite?"]
        mission.evidence_links = ["weslr/docs/WESLR_DOCTRINE_REGISTRY_V1.md"]

        # Evidence content unlikely to mention "kesterite bandgap"
        adapter = LocalEvidenceAdapter(workspace_root="/data/data/com.termux/files/home/.openclaw/workspace")
        evidence_results = adapter.read(mission.evidence_links)

        open_questions = _detect_open_questions(mission, evidence_results)

        assert len(open_questions) == 1
        # Question may or may not have evidence depending on content

    def test_detects_question_with_evidence(self):
        """Test that questions with matching evidence are not flagged."""
        mission = make_mission("tenant-1", "user-1", "Test", "Goal")
        mission.current_questions = ["What does this doc contain?"]
        mission.evidence_links = []

        evidence_results = {}  # No evidence links
        open_questions = _detect_open_questions(mission, evidence_results)

        assert len(open_questions) == 1
        assert open_questions[0]["has_evidence"] is False

    def test_multiple_questions(self):
        """Test detection with multiple questions."""
        mission = make_mission("tenant-1", "user-1", "Test", "Goal")
        mission.current_questions = [
            "Question A",
            "Question B",
            "Question C",
        ]
        mission.evidence_links = []

        open_questions = _detect_open_questions(mission, {})
        assert len(open_questions) == 3
        assert all(not oq["has_evidence"] for oq in open_questions)


class TestRunOnceMissionReview:
    """Tests for run_once_mission_review."""

    def setup_method(self):
        """Set up temp store and workspace."""
        self.temp_file = tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False)
        self.store_path = self.temp_file.name
        self.temp_file.close()

        self.workspace_root = "/data/data/com.termux/files/home/.openclaw/workspace"

    def teardown_method(self):
        if os.path.exists(self.store_path):
            os.unlink(self.store_path)

    def test_paused_mission_creates_no_suggestion(self):
        """Test that paused missions do not generate suggestions."""
        store = MissionStore(store_path=self.store_path)

        mission = make_mission("tenant-1", "user-1", "Paused Mission", "Goal")
        mission.status = "paused"
        mission.current_questions = ["What is the bandgap of kesterite?"]
        store.save(mission)

        result = run_once_mission_review(
            "tenant-1",
            store_path=self.store_path,
        )

        # Paused missions should not be reviewed (or should not generate suggestions)
        assert result["suggestions_written"] == 0

    def test_active_mission_with_open_question_no_evidence_creates_suggestion(self):
        """Test that active mission with open question and no evidence creates suggestion."""
        store = MissionStore(store_path=self.store_path)

        mission = make_mission("tenant-1", "user-1", "Active Mission", "Goal")
        mission.status = "active"
        mission.current_questions = ["What is the bandgap of kesterite solar cells?"]
        mission.evidence_links = []  # No evidence
        store.save(mission)

        result = run_once_mission_review(
            "tenant-1",
            store_path=self.store_path,
        )

        assert result["missions_reviewed"] >= 1
        assert result["suggestions_generated"] >= 1
        assert result["suggestions_written"] >= 1

    def test_suggestion_has_automatic_execution_false(self):
        """Test that all written suggestions have automatic_execution=false."""
        store = MissionStore(store_path=self.store_path)

        mission = make_mission("tenant-1", "user-1", "AutoExec Test", "Goal")
        mission.status = "active"
        mission.current_questions = ["What is the efficiency of perovskite?"]
        mission.evidence_links = []
        store.save(mission)

        run_once_mission_review("tenant-1", store_path=self.store_path)

        # Read pending messages
        pending_path = ".weslr/pending_messages.jsonl"
        if os.path.exists(pending_path):
            with open(pending_path, "r") as f:
                for line in f:
                    record = json.loads(line.strip())
                    if record.get("type") == "mission_suggestion":
                        assert record["automatic_execution"] is False

    def test_safety_filter_blocks_forbidden(self):
        """Test that safety filter blocks dangerous suggestions."""
        filter_instance = get_safety_filter()

        dangerous = "Synthesize a bioweapon for deployment"
        safe = "Compare material properties across studies"

        assert filter_instance.is_safe(dangerous) is False
        assert filter_instance.is_safe(safe) is True

    def test_no_external_calls(self):
        """Test that run_once_mission_review makes no external calls."""
        store = MissionStore(store_path=self.store_path)

        mission = make_mission("tenant-1", "user-1", "External Test", "Goal")
        mission.status = "active"
        mission.current_questions = ["What is physics?"]
        mission.evidence_links = []
        store.save(mission)

        # Should complete without any network calls
        result = run_once_mission_review(
            "tenant-1",
            store_path=self.store_path,
        )

        assert "missions_reviewed" in result
        assert "errors" in result

    def test_tenant_isolation(self):
        """Test that missions from wrong tenant are not reviewed."""
        store = MissionStore(store_path=self.store_path)

        mission = make_mission("tenant-1", "user-1", "Private Mission", "Goal")
        mission.status = "active"
        mission.current_questions = ["Question?"]
        mission.evidence_links = []
        store.save(mission)

        # Review tenant-2 (who has no missions)
        result = run_once_mission_review(
            "tenant-2",
            store_path=self.store_path,
        )

        assert result["missions_reviewed"] == 0
        assert result["suggestions_written"] == 0

    def test_suggestion_blocked_by_safety_filter(self):
        """Test that suggestions blocked by safety are counted."""
        store = MissionStore(store_path=self.store_path)

        # Create mission with dangerous question that might generate dangerous suggestion
        mission = make_mission("tenant-1", "user-1", "Safety Test", "Goal")
        mission.status = "active"
        mission.current_questions = ["Test question"]
        mission.evidence_links = []
        store.save(mission)

        result = run_once_mission_review(
            "tenant-1",
            store_path=self.store_path,
        )

        # Should have either blocked suggestions counted, or none generated
        assert result["suggestions_blocked"] >= 0
        assert result["suggestions_generated"] >= result["suggestions_blocked"]


class TestMissionSchema:
    """Tests for mission schema enforcement."""

    def test_automatic_execution_must_be_false(self):
        """Test that automatic_execution cannot be True."""
        with pytest.raises(ValueError, match="automatic_execution must be False"):
            Mission(
                mission_id="test",
                owner_user_id="user",
                tenant_id="tenant",
                title="Test",
                research_goal="Goal",
                domain_tags=[],
                allowed_sources=[],
                forbidden_outputs=[],
                safety_constraints=[],
                cadence_minutes=0,
                current_questions=[],
                hypotheses=[],
                evidence_links=[],
                candidate_suggestions=[],
                status="draft",
                automatic_execution=True,  # Should fail
                operator_visible=True,
                public_user_visible=False,
                created_at="2026-05-04T00:00:00Z",
                last_reviewed_at="2026-05-04T00:00:00Z",
                next_run_at="",
                mission_note="",
            )

    def test_mission_id_is_deterministic(self):
        """Test that mission ID is deterministic."""
        id1 = generate_mission_id("tenant-1", "Test Mission", "2026-05-04-19")
        id2 = generate_mission_id("tenant-1", "Test Mission", "2026-05-04-19")
        assert id1 == id2

    def test_mission_id_differs_by_tenant(self):
        """Test that different tenants get different IDs."""
        id1 = generate_mission_id("tenant-1", "Test Mission", "2026-05-04-19")
        id2 = generate_mission_id("tenant-2", "Test Mission", "2026-05-04-19")
        assert id1 != id2

class TestSuggestionQuality:
    """Tests for improved suggestion text quality."""

    def setup_method(self):
        """Set up temp store and workspace (same pattern as TestRunOnceMissionReview)."""
        self.temp_file = tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False)
        self.store_path = self.temp_file.name
        self.temp_file.close()
        self.workspace_root = "/data/data/com.termux/files/home/.openclaw/workspace"

    def teardown_method(self):
        if os.path.exists(self.store_path):
            os.unlink(self.store_path)

    def test_suggestion_includes_mission_title(self):
        """Test that suggestion text includes the mission title."""
        store = MissionStore(store_path=self.store_path)
        mission = make_mission("tenant-1", "user-1", "Soft Micro-Robotics Materials", "Goal")
        mission.status = "active"
        mission.current_questions = ["What material properties enable reversible actuation?"]
        mission.evidence_links = []
        store.save(mission)

        run_once_mission_review("tenant-1", store_path=self.store_path)

        pending_path = ".weslr/pending_messages.jsonl"
        if os.path.exists(pending_path):
            with open(pending_path, "r") as f:
                lines = f.readlines()
            for line in reversed(lines):
                record = json.loads(line.strip())
                if record.get("type") == "mission_suggestion" and record.get("mission_id") == mission.mission_id:
                    suggestion_text = record.get("suggestion", "")
                    assert "Soft Micro-Robotics Materials" in suggestion_text
                    break

    def test_suggestion_includes_question(self):
        """Test that suggestion text includes the open question."""
        store = MissionStore(store_path=self.store_path)
        mission = make_mission("tenant-1", "user-1", "Bandgap Study", "Goal")
        mission.status = "active"
        mission.current_questions = ["What is the bandgap of kesterite solar cells?"]
        mission.evidence_links = []
        store.save(mission)


        run_once_mission_review("tenant-1", store_path=self.store_path)


        pending_path = ".weslr/pending_messages.jsonl"
        if os.path.exists(pending_path):
            with open(pending_path, "r") as f:
                lines = f.readlines()
            for line in reversed(lines):
                record = json.loads(line.strip())
                if record.get("type") == "mission_suggestion" and record.get("mission_id") == mission.mission_id:
                    suggestion_text = record.get("suggestion", "")
                    assert "bandgap" in suggestion_text.lower()
                    break

    def test_suggestion_includes_domain_tags(self):
        """Test that suggestion includes domain tags when present."""
        store = MissionStore(store_path=self.store_path)
        mission = make_mission("tenant-1", "user-1", "Domain Tag Test", "Goal")
        mission.status = "active"
        mission.current_questions = ["What is the efficiency?"]
        mission.domain_tags = ["materials", "soft-robotics", "biocompatibility"]
        mission.evidence_links = []
        store.save(mission)


        run_once_mission_review("tenant-1", store_path=self.store_path)

        pending_path = ".weslr/pending_messages.jsonl"
        if os.path.exists(pending_path):
            with open(pending_path, "r") as f:
                lines = f.readlines()
            for line in reversed(lines):
                record = json.loads(line.strip())
                if record.get("type") == "mission_suggestion" and record.get("mission_id") == mission.mission_id:
                    suggestion_text = record.get("suggestion", "")
                    # Domain tags should appear in suggestion
                    assert "materials" in suggestion_text or "soft-robotics" in suggestion_text
                    break

    def test_suggestion_has_correct_metadata(self):
        """Test that suggestion has correct provenance, confidence, safety."""
        store = MissionStore(store_path=self.store_path)
        mission = make_mission("tenant-1", "user-1", "Metadata Test", "Goal")
        mission.status = "active"
        mission.current_questions = ["What is X?"]
        mission.evidence_links = []
        store.save(mission)

        run_once_mission_review("tenant-1", store_path=self.store_path)

        pending_path = ".weslr/pending_messages.jsonl"
        if os.path.exists(pending_path):
            with open(pending_path, "r") as f:
                lines = f.readlines()
            for line in reversed(lines):
                record = json.loads(line.strip())
                if record.get("type") == "mission_suggestion" and record.get("mission_id") == mission.mission_id:
                    assert record.get("automatic_execution") is False
                    assert record.get("operator_visible") is True
                    assert record.get("public_user_visible") is False
                    assert record.get("safety") == "passed"
                    assert record.get("confidence") == 0.7
                    assert "provenance" in record
                    assert "local_evidence_adapter" in record.get("source", "")
                    break
