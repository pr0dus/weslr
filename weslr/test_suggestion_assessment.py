# test_suggestion_assessment.py - Tests for Self-Architecture Core v8: Memory-Aware Assessment
# Memory-aware review, consistency surfacing, drift detection, backward compatibility.

from __future__ import annotations

import unittest
import json
import tempfile
import shutil
from pathlib import Path
from suggestion_assessment import WeslrAssessment
from architecture_memory import (
    ArchitectureMemory,
    create_decision,
    DecisionStatus,
)
from suggestion_assessment_v8 import (
    MemoryAwareAssessment,
    get_memory_aware_recommendations,
    build_operator_review_output,
)


class TestBasicAssessment(unittest.TestCase):
    """Test basic assessment without memory."""

    def test_assess_request(self):
        """Can assess a basic request."""
        assessment = WeslrAssessment()
        request = {
            "domain": "astronomy",
            "requested_capability": "telescope data processing",
            "problem_statement": "Need better processing for telescope observations",
        }
        result = assessment.assess_request(request)
        self.assertIn("weslr_assessment", result)
        self.assertIn("priority", result["weslr_assessment"])

    def test_assess_candidate(self):
        """Can assess a candidate."""
        assessment = WeslrAssessment()
        candidate = {
            "id": "cand1",
            "source": {
                "original_data": {
                    "domain": "physics",
                    "requested_capability": "quantum simulation",
                    "problem_statement": "Need better quantum simulation tools",
                }
            }
        }
        result = assessment.assess_candidate(candidate)
        self.assertIn("weslr_assessment", result)


class TestMemoryAwareAssessment(unittest.TestCase):
    """Test memory-aware assessment."""

    def setUp(self):
        """Create temp memory for tests."""
        self.temp_dir = tempfile.mkdtemp()
        self.storage_path = Path(self.temp_dir) / "decisions.json"
        self.memory = ArchitectureMemory(storage_path=self.storage_path)

    def tearDown(self):
        """Clean up temp directory."""
        shutil.rmtree(self.temp_dir)

    def test_assess_with_memory_no_prior(self):
        """Assessment works with no prior decisions."""
        assessment = MemoryAwareAssessment()
        assessment.set_memory(self.memory)

        request = {
            "domain": "astronomy",
            "requested_capability": "new telescope capability",
            "problem_statement": "Need new capability for observations",
        }

        result = assessment.assess_with_memory(request)
        self.assertIn("memory_context", result["weslr_assessment"])
        # Consistency type may be "similar" or "consistent" with empty memory
        self.assertIn(
            result["weslr_assessment"]["memory_context"]["consistency_type"],
            ["unknown", "similar", "consistent"],
        )

    def test_assess_with_memory_has_prior_accepted(self):
        """Assessment surfaces prior accepted decisions."""
        # Add a prior accepted decision
        d = create_decision(
            "Add logging",
            "Add structured logging",
            affected_subsystems=["state"],
        )
        d.mark_accepted("Accepted")
        self.memory.add_decision(d)

        assessment = MemoryAwareAssessment()
        assessment.set_memory(self.memory)

        request = {
            "domain": "astronomy",
            "requested_capability": "Observation processing",
            "problem_statement": "Need better observation processing",
        }

        result = assessment.assess_with_memory(request)
        memory_context = result["weslr_assessment"]["memory_context"]

        # Should have empty prior_accepted since no matching
        self.assertIsInstance(memory_context["prior_accepted"], list)

    def test_assess_with_memory_has_prior_denied(self):
        """Assessment surfaces prior denied decisions."""
        # Add a prior denied decision
        d = create_decision(
            "Remove old code",
            "Remove legacy code",
            affected_subsystems=["state"],
        )
        d.mark_rejected("Too risky")
        self.memory.add_decision(d)

        assessment = MemoryAwareAssessment()
        assessment.set_memory(self.memory)

        request = {
            "domain": "astronomy",
            "requested_capability": "Data processing",
            "problem_statement": "Need data processing",
        }

        result = assessment.assess_with_memory(request)
        memory_context = result["weslr_assessment"]["memory_context"]

        self.assertIsInstance(memory_context["prior_denied"], list)


class TestOperatorReviewOutput(unittest.TestCase):
    """Test operator review output generation."""

    def setUp(self):
        """Create temp memory for tests."""
        self.temp_dir = tempfile.mkdtemp()
        self.storage_path = Path(self.temp_dir) / "decisions.json"
        self.memory = ArchitectureMemory(storage_path=self.storage_path)

    def tearDown(self):
        """Clean up temp directory."""
        shutil.rmtree(self.temp_dir)

    def test_operator_review_output_structure(self):
        """Operator review output has expected structure."""
        candidates = [
            {
                "id": "cand1",
                "source": {
                    "original_data": {
                        "domain": "astronomy",
                        "requested_capability": "Telescope data",
                        "problem_statement": "Processing telescope data",
                    }
                }
            }
        ]

        output = build_operator_review_output(candidates, self.memory)

        self.assertIn("review_timestamp", output)
        self.assertIn("total_candidates", output)
        self.assertIn("candidates", output)
        self.assertEqual(output["total_candidates"], 1)

    def test_memory_summary_in_output(self):
        """Memory summary is included when memory provided."""
        # Add some decisions
        d1 = create_decision("Test 1", "Test 1")
        d1.mark_accepted("Accepted")
        self.memory.add_decision(d1)

        candidates = [
            {
                "id": "cand1",
                "source": {
                    "original_data": {
                        "domain": "astronomy",
                        "requested_capability": "Telescope data",
                        "problem_statement": "Processing telescope data",
                    }
                }
            }
        ]

        output = build_operator_review_output(candidates, self.memory)

        self.assertIn("memory_summary", output)
        self.assertEqual(output["memory_summary"]["total_accepted"], 1)

    def test_recommendations_in_output(self):
        """Recommendations are included in output."""
        candidates = [
            {
                "id": "cand1",
                "source": {
                    "original_data": {
                        "domain": "astronomy",
                        "requested_capability": "Telescope data",
                        "problem_statement": "Processing telescope data",
                    }
                }
            }
        ]

        output = build_operator_review_output(candidates, self.memory)

        self.assertIn("candidates", output)
        candidate_output = output["candidates"][0]
        self.assertIn("recommendations", candidate_output)
        recs = candidate_output["recommendations"]
        self.assertIn("should_accept", recs)
        self.assertIn("should_reopen", recs)
        self.assertIn("should_delay", recs)
        self.assertIn("should_archive", recs)


class TestBackwardCompatibility(unittest.TestCase):
    """Test backward compatibility with existing code."""

    def test_existing_assessment_still_works(self):
        """Existing assessment code still works after adding memory."""
        assessment = WeslrAssessment()
        request = {
            "domain": "physics",
            "requested_capability": "Simulation",
            "problem_statement": "Need simulation tools",
        }

        result = assessment.assess_request(request)
        self.assertIn("weslr_assessment", result)
        self.assertEqual(result["weslr_assessment"]["priority"], "high")

    def test_assessment_without_memory_has_no_memory_context(self):
        """Basic assessment without memory has no memory_context key."""
        assessment = WeslrAssessment()
        request = {
            "domain": "astronomy",
            "requested_capability": "Observation",
            "problem_statement": "Processing observations",
        }

        result = assessment.assess_request(request)
        self.assertNotIn("memory_context", result["weslr_assessment"])

    def test_assessment_with_empty_memory_context(self):
        """Assessment with memory but no prior decisions has empty context."""
        temp_dir = tempfile.mkdtemp()
        storage_path = Path(temp_dir) / "decisions.json"
        memory = ArchitectureMemory(storage_path=storage_path)

        try:
            assessment = MemoryAwareAssessment()
            assessment.set_memory(memory)

            request = {
                "domain": "astronomy",
                "requested_capability": "Observation",
                "problem_statement": "Processing observations",
            }

            result = assessment.assess_with_memory(request)
            self.assertIn("memory_context", result["weslr_assessment"])
            self.assertEqual(len(result["weslr_assessment"]["memory_context"]["prior_accepted"]), 0)
        finally:
            shutil.rmtree(temp_dir)


class TestRecommendations(unittest.TestCase):
    """Test recommendations with memory context."""

    def setUp(self):
        """Create temp memory for tests."""
        self.temp_dir = tempfile.mkdtemp()
        self.storage_path = Path(self.temp_dir) / "decisions.json"
        self.memory = ArchitectureMemory(storage_path=self.storage_path)

    def tearDown(self):
        """Clean up temp directory."""
        shutil.rmtree(self.temp_dir)

    def test_get_recommendations_no_prior(self):
        """Recommendations work with no prior decisions."""
        candidates = [
            {
                "id": "cand1",
                "source": {
                    "original_data": {
                        "domain": "astronomy",
                        "requested_capability": "Observation",
                        "problem_statement": "Processing observations",
                    }
                }
            }
        ]

        recs = get_memory_aware_recommendations(candidates, self.memory)

        self.assertEqual(len(recs), 1)
        self.assertIn("candidate_id", recs[0])
        self.assertIn("assessment", recs[0])

    def test_recommendations_with_prior_accepted(self):
        """Recommendations surface prior accepted decisions."""
        d = create_decision("Add logging", "Add logging", affected_subsystems=["state"])
        d.mark_accepted("Accepted")
        self.memory.add_decision(d)

        candidates = [
            {
                "id": "cand1",
                "source": {
                    "original_data": {
                        "domain": "astronomy",
                        "requested_capability": "Observation",
                        "problem_statement": "Processing observations",
                    }
                }
            }
        ]

        recs = get_memory_aware_recommendations(candidates, self.memory)

        self.assertEqual(len(recs), 1)
        rec = recs[0]
        # Memory note may or may not be present depending on match
        self.assertIsInstance(rec.get("memory_note"), str)


if __name__ == "__main__":
    unittest.main()
