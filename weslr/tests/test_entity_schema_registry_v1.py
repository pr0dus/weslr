"""Tests for entity_schema_registry + entity query commands — Phase 4.3."""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from weslr.entity_schema_registry import (
    DEFAULT_DOMAIN,
    get_entity_schema,
    list_entity_types,
    list_relationship_types,
    load_schema,
)
from weslr.commands.entities import (
    detect_entity_type,
    entity_query,
    format_entity_response,
    get_entity_facts,
    get_entity_summary,
    get_inferred_types_for_name,
    group_facts_by_predicate,
    list_entities_of_type,
)


class TestSchemaLoading(unittest.TestCase):
    def test_cancer_research_schema_loads(self):
        """cancer_research schema loads with correct structure."""
        schema = load_schema("cancer_research")
        self.assertEqual(schema["domain"], "cancer_research")
        self.assertIn("entity_types", schema)
        self.assertIn("relationship_types", schema)

    def test_base_schema_loads(self):
        """Nonexistent domain falls back to base schema."""
        schema = load_schema("nonexistent_domain")
        self.assertEqual(schema["domain"], "base")
        self.assertIn("entity_types", schema)

    def test_entity_types_known(self):
        """cancer_research defines 5 entity types."""
        types = list_entity_types("cancer_research")
        self.assertEqual(len(types), 5)
        self.assertIn("ClinicalTrial", types)
        self.assertIn("DrugCompound", types)
        self.assertIn("Protein", types)
        self.assertIn("Biomarker", types)
        self.assertIn("Mutation", types)

    def test_relationship_types_known(self):
        """cancer_research defines expected relationship types."""
        rels = list_relationship_types("cancer_research")
        self.assertIn("treats", rels)
        self.assertIn("has_adverse_event", rels)
        self.assertIn("associated_with", rels)

    def test_get_entity_schema_clinical_trial(self):
        """get_entity_schema returns correct ClinicalTrial definition."""
        schema = get_entity_schema("ClinicalTrial", "cancer_research")
        self.assertIn("attributes", schema)
        self.assertIn("relationships", schema)
        self.assertIn("trial_id", schema["attributes"])
        self.assertIn("has_drug", schema["relationships"])


class TestEntityTypeDetection(unittest.TestCase):
    def test_clinical_trial_nct(self):
        """NCT + 8 digits detected as ClinicalTrial."""
        for name in ["NCT04551452", "nct04551452", "NCT12345678"]:
            self.assertEqual(detect_entity_type(name), "ClinicalTrial", f"Failed: {name}")

    def test_drug_compound_suffixes(self):
        """Drug names ending in -mab or -ib detected as DrugCompound."""
        for name in ["Olaparib", "Sotorasib", "Lenvatinib", "Trastuzumab", "Pembrolizumab"]:
            self.assertEqual(detect_entity_type(name), "DrugCompound", f"Failed: {name}")

    def test_protein_gene_symbol(self):
        """All-caps gene symbols detected as Protein."""
        for name in ["BRCA1", "KRAS", "EGFR", "ALK", "ROS1", "MET", "TMB"]:
            self.assertEqual(detect_entity_type(name), "Protein", f"Failed: {name}")

    def test_biomarker_hybrid(self):
        """Hyphenated biomarker names detected as Biomarker."""
        for name in ["PD-L1", "KRAS-G12C"]:
            self.assertEqual(detect_entity_type(name), "Biomarker", f"Failed: {name}")

    def test_mutation(self):
        """Name containing 'mutation' detected as Mutation."""
        self.assertEqual(detect_entity_type("BRCA1 mutation"), "Mutation")
        self.assertEqual(detect_entity_type("p53 mutation"), "Mutation")

    def test_unknown_returns_none(self):
        """Unrecognizable name returns None."""
        for name in ["study", "patient", "overall survival", ""]:
            self.assertIsNone(detect_entity_type(name), f"Failed: {name}")

    def test_multiple_types(self):
        """get_inferred_types_for_name returns all matching types."""
        types = get_inferred_types_for_name("PD-L1")
        self.assertIn("Biomarker", types)

    def test_protein_not_biomarker(self):
        """Gene symbols without hyphen are Protein, not Biomarker."""
        self.assertEqual(detect_entity_type("HER2"), "Protein")
        self.assertEqual(detect_entity_type("BRCA1"), "Protein")


class TestGetEntityFacts(unittest.TestCase):
    def test_matches_subject(self):
        """Entity fact match checks subject field."""
        mock_facts = [
            {"subject": "brca1", "predicate": "survival_rate", "object": "72", "timestamp": "2026-05-03T00:00:00Z"},
        ]
        with patch("weslr.commands.entities.load_facts", return_value=mock_facts):
            results = get_entity_facts("brca1", limit=100)
            self.assertGreaterEqual(len(results), 1)
            self.assertTrue(any(r["subject"] == "brca1" for r in results))

    def test_matches_object(self):
        """Entity fact match checks object field."""
        mock_facts = [
            {"subject": "phase_iii", "predicate": "trial_id", "object": "nct04662710", "timestamp": "2026-05-03T00:00:00Z"},
        ]
        with patch("weslr.commands.entities.load_facts", return_value=mock_facts):
            results = get_entity_facts("nct04662710", limit=100)
            self.assertGreaterEqual(len(results), 1)

    def test_matches_fact_data(self):
        """Entity fact match checks fact_data values."""
        mock_facts = [
            {
                "subject": "phase_iii",
                "predicate": "hazard_ratio",
                "object": "0.71",
                "fact_data": {"hazard_ratio": "0.71", "ci_low": "0.54", "ci_high": "0.93"},
                "timestamp": "2026-05-03T00:00:00Z",
            },
        ]
        with patch("weslr.commands.entities.load_facts", return_value=mock_facts):
            results = get_entity_facts("0.54", limit=100)
            self.assertGreaterEqual(len(results), 1)

    def test_predicate_filter(self):
        """predicate_filter only returns facts with that predicate."""
        mock_facts = [
            {"subject": "brca1", "predicate": "survival_rate", "object": "72", "timestamp": "2026-05-03T00:00:00Z"},
            {"subject": "brca1", "predicate": "phase", "object": "phase_iii", "timestamp": "2026-05-03T00:00:01Z"},
        ]
        with patch("weslr.commands.entities.load_facts", return_value=mock_facts):
            results = get_entity_facts("brca1", predicate_filter="phase", limit=100)
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0]["predicate"], "phase")


class TestGroupFactsByPredicate(unittest.TestCase):
    def test_groups_by_predicate(self):
        """Facts are grouped by predicate correctly."""
        facts = [
            {"predicate": "phase", "object": "III"},
            {"predicate": "survival_rate", "object": "72"},
            {"predicate": "phase", "object": "II"},
            {"predicate": "survival_rate", "object": "68"},
        ]
        grouped = group_facts_by_predicate(facts)
        self.assertEqual(len(grouped["phase"]), 2)
        self.assertEqual(len(grouped["survival_rate"]), 2)


class TestFormatEntityResponse(unittest.TestCase):
    def test_format_with_known_entity(self):
        """format_entity_response produces readable output for a known entity."""
        summary = {
            "name": "NCT04551452",
            "detected_types": ["ClinicalTrial"],
            "primary_type": "ClinicalTrial",
            "schema": {"attributes": ["trial_id", "phase"], "relationships": ["has_drug"]},
            "facts": [
                {
                    "predicate": "phase",
                    "object": "phase_iii",
                    "trust_score": 0.68,
                    "source_reference": {"pmid": "12345"},
                },
            ],
            "total_facts": 1,
        }
        output = format_entity_response("NCT04551452", summary)
        self.assertIn("NCT04551452", output)
        self.assertIn("ClinicalTrial", output)
        self.assertIn("phase_iii", output)
        self.assertIn("PMID 12345", output)


if __name__ == "__main__":
    unittest.main()