# test_narrative.py - Tests for Self-Architecture Core v9: Unified Operator Narrative Layer
# Narrative generation, precedent inclusion, risk/fit/timing, fallback behavior.

from __future__ import annotations

import unittest
import json
from narrative import (
    NarrativeEngine,
    UnifiedNarrative,
    NarrativeBlock,
    generate_narrative,
)


class TestNarrativeModel(unittest.TestCase):
    """Test narrative model classes."""

    def test_narrative_block(self):
        """Narrative block can be created and serialized."""
        block = NarrativeBlock(
            section="summary",
            title="Summary",
            content="Test content",
            confidence=0.8,
        )
        self.assertEqual(block.section, "summary")
        self.assertEqual(block.title, "Summary")
        self.assertEqual(block.content, "Test content")
        self.assertEqual(block.confidence, 0.8)

        # Test to_dict
        data = block.to_dict()
        self.assertEqual(data["section"], "summary")
        self.assertEqual(data["confidence"], 0.8)

    def test_unified_narrative(self):
        """Unified narrative can be created and serialized."""
        summary = NarrativeBlock("summary", "Summary", "Test summary")
        why = NarrativeBlock("why", "Why Surfaced", "Test why")
        impact = NarrativeBlock("impact", "Impact", "Test impact")
        risk = NarrativeBlock("risk", "Risk", "Test risk")
        fit = NarrativeBlock("fit", "Fit", "Test fit")
        memory = NarrativeBlock("memory", "Memory", "Test memory")
        consistency = NarrativeBlock("consistency", "Consistency", "Test consistency")
        recommendation = NarrativeBlock("recommendation", "Recommendation", "Test recommendation")
        timing = NarrativeBlock("timing", "Timing", "Test timing")

        narrative = UnifiedNarrative(
            narrative_id="test123",
            title="Test Narrative",
            domain="astronomy",
            summary=summary,
            why_surfaced=why,
            subsystem_impact=impact,
            risk_effort=risk,
            architectural_fit=fit,
            memory_precedent=memory,
            consistency=consistency,
            recommendation=recommendation,
            timing=timing,
        )

        data = narrative.to_dict()
        self.assertEqual(data["narrative_id"], "test123")
        self.assertEqual(data["title"], "Test Narrative")
        self.assertEqual(data["domain"], "astronomy")

    def test_from_dict(self):
        """Can create narrative from dict."""
        data = {
            "narrative_id": "abc123",
            "title": "Test from dict",
            "domain": "physics",
            "summary": {"section": "summary", "title": "Summary", "content": "Test"},
            "why_surfaced": {"section": "why", "title": "Why", "content": "Test"},
            "subsystem_impact": {"section": "impact", "title": "Impact", "content": "Test"},
            "risk_effort": {"section": "risk", "title": "Risk", "content": "Test"},
            "architectural_fit": {"section": "fit", "title": "Fit", "content": "Test"},
            "memory_precedent": {"section": "memory", "title": "Memory", "content": "Test"},
            "consistency": {"section": "consistency", "title": "Consistency", "content": "Test"},
            "recommendation": {"section": "rec", "title": "Rec", "content": "Test"},
            "timing": {"section": "timing", "title": "Timing", "content": "Test"},
        }

        narrative = UnifiedNarrative.from_dict(data)
        self.assertEqual(narrative.narrative_id, "abc123")
        self.assertEqual(narrative.title, "Test from dict")


class TestNarrativeEngine(unittest.TestCase):
    """Test narrative engine."""

    def test_generate_narrative_basic(self):
        """Basic narrative generation works."""
        engine = NarrativeEngine()
        engine.set_decision_sources({
            "radar": {"decision_score": 0.7},
            "assessment": {
                "fit_score": 0.75,
                "priority": "high",
                "implementation_risk": "low",
                "affected_subsystems": ["state"],
            },
        })
        engine.set_memory_context({
            "prior_accepted": [],
            "prior_denied": [],
            "consistency_type": "consistent",
        })

        narrative = engine.generate_narrative(
            title="Add logging",
            domain="astronomy",
            suggestion_id="sugg001",
        )

        self.assertEqual(narrative.title, "Add logging")
        self.assertEqual(narrative.domain, "astronomy")
        self.assertIsNotNone(narrative.summary)
        self.assertIsNotNone(narrative.recommendation)
        self.assertIsNotNone(narrative.timing)

    def test_generate_narrative_with_memory(self):
        """Narrative includes memory context when available."""
        engine = NarrativeEngine()
        engine.set_decision_sources({
            "radar": {},
            "assessment": {
                "fit_score": 0.5,
                "priority": "medium",
                "implementation_risk": "medium",
            },
        })
        engine.set_memory_context({
            "prior_accepted": [
                {"id": "d1", "title": "Logging added", "status": "accepted"}
            ],
            "prior_denied": [],
            "consistency_type": "consistent",
        })

        narrative = engine.generate_narrative("New logging", "astronomy")

        # Should mention memory precedent
        self.assertIn("prior", narrative.memory_precedent.content.lower())
        # Should have consistency info
        self.assertIn("consistent", narrative.consistency.content.lower())

    def test_generate_narrative_with_tradeoff(self):
        """Narrative includes tradeoff context when available."""
        engine = NarrativeEngine()
        engine.set_decision_sources({
            "assessment": {"fit_score": 0.6, "priority": "medium"},
        })
        engine.set_memory_context({
            "prior_accepted": [],
            "prior_denied": [],
            "consistency_type": "divergent",
        })
        engine.set_tradeoff_context({
            "better_scenario": "scenario_b",
            "tradeoffs": ["effort: B better", "risk: B better"],
            "timing_recommendation": "Phased rollout",
        })

        narrative = engine.generate_narrative("Scenario A", "astronomy")

        self.assertIsNotNone(narrative.tradeoff)
        self.assertIn("tradeoffs", narrative.tradeoff.content.lower())

    def test_generate_narrative_low_priority(self):
        """Low priority suggestions get appropriate recommendation."""
        engine = NarrativeEngine()
        engine.set_decision_sources({
            "assessment": {
                "fit_score": 0.3,
                "priority": "low",
                "implementation_risk": "low",
            },
        })
        engine.set_memory_context({
            "prior_accepted": [],
            "prior_denied": [],
        })

        narrative = engine.generate_narrative("Low priority", "astronomy")

        self.assertIn("delay", narrative.recommendation.content.lower())
        self.assertIn("delayed", narrative.timing.content.lower())

    def test_generate_narrative_high_priority(self):
        """High priority suggestions get accept recommendation."""
        engine = NarrativeEngine()
        engine.set_decision_sources({
            "assessment": {
                "fit_score": 0.8,
                "priority": "high",
                "implementation_risk": "low",
            },
        })
        engine.set_memory_context({
            "prior_accepted": [],
            "prior_denied": [],
        })

        narrative = engine.generate_narrative("High priority", "astronomy")

        self.assertIn("accept", narrative.recommendation.content.lower())

    def test_json_generation(self):
        """Can generate narrative as JSON."""
        engine = NarrativeEngine()
        engine.set_decision_sources({
            "radar": {"decision_score": 0.7},
            "assessment": {
                "fit_score": 0.75,
                "priority": "high",
                "implementation_risk": "low",
            },
        })
        engine.set_memory_context({
            "prior_accepted": [],
            "prior_denied": [],
        })

        json_output = engine.generate_narrative_json(
            title="Test JSON",
            domain="astronomy",
        )

        # Should be valid JSON
        data = json.loads(json_output)
        self.assertEqual(data["title"], "Test JSON")
        self.assertEqual(data["domain"], "astronomy")

    def test_convenience_function(self):
        """Convenience generate_narrative function works."""
        narrative = generate_narrative(
            title="Convenience test",
            domain="physics",
            decision_sources={
                "radar": {},
                "assessment": {
                    "fit_score": 0.6,
                    "priority": "medium",
                    "implementation_risk": "medium",
                },
            },
            memory_context={
                "prior_accepted": [],
                "prior_denied": [],
            },
            suggestion_id="conv001",
        )

        self.assertEqual(narrative.title, "Convenience test")
        self.assertEqual(narrative.domain, "physics")


class TestFallbackBehavior(unittest.TestCase):
    """Test fallback behavior for missing data."""

    def test_missing_radar_data(self):
        """Handles missing radar data gracefully."""
        engine = NarrativeEngine()
        engine.set_decision_sources({
            "assessment": {
                "fit_score": 0.5,
                "priority": "medium",
                "implementation_risk": "medium",
            },
        })
        engine.set_memory_context({
            "prior_accepted": [],
            "prior_denied": [],
        })

        narrative = engine.generate_narrative("Missing radar", "astronomy")
        self.assertIn("assessment", narrative.why_surfaced.content.lower())

    def test_missing_memory_data(self):
        """Handles missing memory data gracefully."""
        engine = NarrativeEngine()
        engine.set_decision_sources({
            "assessment": {
                "fit_score": 0.5,
                "priority": "medium",
            },
        })
        # No memory context set

        narrative = engine.generate_narrative("No memory", "astronomy")
        self.assertIn("no prior", narrative.memory_precedent.content.lower())

    def test_missing_assessment_data(self):
        """Handles missing assessment data gracefully."""
        engine = NarrativeEngine()
        engine.set_decision_sources({
            "radar": {"decision_score": 0.5},
        })
        engine.set_memory_context({
            "prior_accepted": [],
            "prior_denied": [],
        })

        narrative = engine.generate_narrative("Missing assessment", "astronomy")
        # Should still generate with defaults
        self.assertIsNotNone(narrative.summary)


class TestBackwardCompatibility(unittest.TestCase):
    """Test backward compatibility with existing code."""

    def test_existing_engine_usage(self):
        """Existing code using NarrativeEngine still works."""
        engine = NarrativeEngine()
        engine.set_decision_sources({
            "radar": {"decision_score": 0.6},
            "assessment": {
                "fit_score": 0.65,
                "priority": "medium",
                "implementation_risk": "low",
                "affected_subsystems": ["state", "continuity"],
            },
        })
        engine.set_memory_context({
            "prior_accepted": [],
            "prior_denied": [],
            "consistency_type": "consistent",
        })

        narrative = engine.generate_narrative("Existing usage", "astronomy")
        self.assertEqual(narrative.title, "Existing usage")

        # Verify all required sections exist
        self.assertIsNotNone(narrative.summary)
        self.assertIsNotNone(narrative.why_surfaced)
        self.assertIsNotNone(narrative.subsystem_impact)
        self.assertIsNotNone(narrative.risk_effort)
        self.assertIsNotNone(narrative.architectural_fit)
        self.assertIsNotNone(narrative.memory_precedent)
        self.assertIsNotNone(narrative.consistency)
        self.assertIsNotNone(narrative.recommendation)
        self.assertIsNotNone(narrative.timing)


class TestNarrativeStructure(unittest.TestCase):
    """Test narrative structure completeness."""

    def test_all_sections_present(self):
        """All required sections are present in narrative."""
        narrative = generate_narrative(
            title="Complete narrative",
            domain="astronomy",
            decision_sources={
                "radar": {"decision_score": 0.7},
                "assessment": {
                    "fit_score": 0.75,
                    "priority": "high",
                    "implementation_risk": "low",
                },
            },
            memory_context={
                "prior_accepted": [],
                "prior_denied": [],
                "consistency_type": "consistent",
            },
        )

        # Verify all NarrativeSection values are present as keys
        narrative_dict = narrative.to_dict()
        self.assertIn("summary", narrative_dict)
        self.assertIn("why_surfaced", narrative_dict)
        self.assertIn("subsystem_impact", narrative_dict)
        self.assertIn("risk_effort", narrative_dict)
        self.assertIn("architectural_fit", narrative_dict)
        self.assertIn("memory_precedent", narrative_dict)
        self.assertIn("consistency", narrative_dict)
        self.assertIn("recommendation", narrative_dict)
        self.assertIn("timing", narrative_dict)

    def test_metadata_preserved(self):
        """Metadata (author, suggestion_id) is preserved."""
        engine = NarrativeEngine()
        engine.set_decision_sources({
            "assessment": {"fit_score": 0.5},
        })
        engine.set_memory_context({})

        narrative = engine.generate_narrative(
            "With metadata",
            "astronomy",
            suggestion_id="meta001",
        )
        narrative.author = "operator"
        narrative.source = "radar"

        data = narrative.to_dict()
        self.assertEqual(data.get("author"), "operator")
        self.assertEqual(data.get("source"), "radar")
        self.assertEqual(data.get("suggestion_id"), "meta001")


if __name__ == "__main__":
    unittest.main()
