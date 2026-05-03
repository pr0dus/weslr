"""Tests for fact_extractor.py — Phase 4.2 refinement."""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).parent.parent))

from weslr.fact_extractor import (
    _get_fallback_patterns,
    append_enriched_fact,
    extract_facts_with_positions,
    load_facts,
    load_patterns,
)


class TestLoadPatterns(unittest.TestCase):
    def test_cancer_research_loads_15_patterns(self):
        """cancer_research domain loads 15 clinical trial patterns."""
        patterns = load_patterns("cancer_research")
        self.assertEqual(len(patterns), 15)
        ids = [p["pattern_id"] for p in patterns]
        self.assertIn("ct.survival_rate", ids)
        self.assertIn("ct.hazard_ratio", ids)
        self.assertIn("ct.phase", ids)

    def test_fallback_returns_10_generic(self):
        """Nonexistent domain falls back to 10 generic session-summary patterns."""
        patterns = load_patterns("nonexistent_domain")
        self.assertEqual(len(patterns), 10)
        self.assertTrue(all(p["pattern_id"].startswith("generic.") for p in patterns))

    def test_fallback_patterns_have_correct_structure(self):
        """Fallback patterns have required keys: pattern_id, regex, confidence, groups."""
        fallbacks = _get_fallback_patterns()
        for p in fallbacks:
            self.assertIn("pattern_id", p)
            self.assertIn("regex", p)
            self.assertIn("confidence", p)
            self.assertIn("groups", p)
            self.assertIsInstance(p["groups"], dict)


class TestExtractFactsWithPositions(unittest.TestCase):
    def test_survival_rate_pattern(self):
        """Survival rate pattern extracts rate and timeframe."""
        import re

        patterns = load_patterns("cancer_research")
        hr_pat = next(p["regex"] for p in patterns if p["pattern_id"] == "ct.survival_rate")
        m = re.search(hr_pat, "Overall survival was 68% at 24 months.", re.IGNORECASE)
        self.assertIsNotNone(m)
        self.assertEqual(m.group(1), "68")
        self.assertEqual(m.group(2), "24")

    def test_hazard_ratio_pattern_both_ci_formats(self):
        """Hazard ratio pattern handles '0.54-0.93' and '0.54 - 0.93' CI formats."""
        import re

        patterns = load_patterns("cancer_research")
        hr_pat = next(p["regex"] for p in patterns if p["pattern_id"] == "ct.hazard_ratio")

        for ci_str in ["0.54-0.93", "0.54 - 0.93"]:
            text = f"Hazard ratio 0.71 (95% CI {ci_str})"
            m = re.search(hr_pat, text, re.IGNORECASE)
            self.assertIsNotNone(m, f"Failed on: {ci_str}")
            self.assertEqual(m.group(1), "0.71")
            self.assertEqual(m.group(2), "0.54")
            self.assertEqual(m.group(3), "0.93")

    def test_phase_pattern(self):
        """Phase pattern extracts Roman/Arabic numerals."""
        import re

        patterns = load_patterns("cancer_research")
        phase_pat = next(p["regex"] for p in patterns if p["pattern_id"] == "ct.phase")
        for text, expected in [("phase III trial", "III"), ("phase 2 study", "2"), ("Phase II", "II")]:
            m = re.search(phase_pat, text, re.IGNORECASE)
            self.assertIsNotNone(m, f"Failed on: {text}")
            self.assertEqual(m.group(1), expected)

    def test_full_pipeline_from_abstract(self):
        """extract_facts_with_positions returns enriched facts with correct schema."""
        abstract = (
            "In a phase III randomized trial, 248 patients were assigned to treatment arm. "
            "Overall survival was 72% at 24 months. p-value = 0.002. "
            "Hazard ratio 0.65 (95% CI 0.48-0.87). Primary endpoint was progression-free survival."
        )
        facts = extract_facts_with_positions(abstract, page=1, line_start=0, domain="cancer_research")
        self.assertGreaterEqual(len(facts), 4)

        # Verify enriched fact structure
        phase_fact = next((f for f in facts if f["pattern_id"] == "ct.phase"), None)
        self.assertIsNotNone(phase_fact)
        self.assertIn("pattern_id", phase_fact)
        self.assertIn("confidence", phase_fact)
        self.assertIn("char_start", phase_fact)
        self.assertIn("char_end", phase_fact)
        self.assertIn("fact_data", phase_fact)
        self.assertIn("subject", phase_fact)
        self.assertIn("predicate", phase_fact)
        self.assertIn("object", phase_fact)

        hr_fact = next((f for f in facts if f["pattern_id"] == "ct.hazard_ratio"), None)
        self.assertIsNotNone(hr_fact)
        self.assertEqual(hr_fact["fact_data"]["hazard_ratio"], "0.65")
        self.assertEqual(hr_fact["fact_data"]["ci_low"], "0.48")
        self.assertEqual(hr_fact["fact_data"]["ci_high"], "0.87")

    def test_no_abstract_yields_no_facts(self):
        """Empty/invalid text returns empty list."""
        for text in ["", None, 123]:
            facts = extract_facts_with_positions(text, domain="cancer_research")
            self.assertEqual(facts, [])


class TestAppendEnrichedFact(unittest.TestCase):
    def test_appends_to_jsonl(self):
        """append_enriched_fact writes a valid JSONL record."""
        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as tmp:
            path = tmp.name

        try:
            fact = {
                "subject": "test_subject",
                "predicate": "survival_rate",
                "object": "72",
                "source_type": "pubmed_abstract",
                "source_reference": {"pmid": "12345"},
                "trust_score": 0.63,
                "extraction_pattern": "ct.survival_rate",
                "fact_data": {"survival_rate": "72", "timeframe": "24"},
            }
            result = append_enriched_fact(fact, fact_store_path=path)
            self.assertEqual(result["status"], "appended")
            self.assertIn("fact_id", result)

            with open(path) as f:
                records = [json.loads(line) for line in f]
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0]["subject"], "test_subject")
            self.assertEqual(records[0]["record_type"], "fact_assertion_v1")
            self.assertIn("timestamp", records[0])
            self.assertTrue(records[0]["hidden_learning"] is False)
            self.assertTrue(records[0]["raw_prompt_stored"] is False)
        finally:
            os.unlink(path)


class TestLoadFacts(unittest.TestCase):
    def test_load_facts_with_filters(self):
        """load_facts returns filtered results from JSONL store."""
        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as tmp:
            path = tmp.name

        try:
            # Write two test records
            records = [
                {
                    "record_type": "fact_assertion_v1",
                    "subject": "brca1",
                    "predicate": "survival_rate",
                    "object": "72",
                    "source_type": "pubmed_abstract",
                    "extraction_pattern": "ct.survival_rate",
                    "timestamp": "2026-05-03T00:00:00Z",
                },
                {
                    "record_type": "fact_assertion_v1",
                    "subject": "brca1",
                    "predicate": "phase",
                    "object": "phase_iii",
                    "source_type": "pubmed_abstract",
                    "extraction_pattern": "ct.phase",
                    "timestamp": "2026-05-03T00:00:01Z",
                },
            ]
            with open(path, "w") as f:
                for r in records:
                    f.write(json.dumps(r) + "\n")

            # Filter by predicate
            result = load_facts(predicate="survival_rate", fact_store_path=path)
            self.assertEqual(len(result), 1)
            self.assertEqual(result[0]["predicate"], "survival_rate")

            # Filter by source_type
            result2 = load_facts(source_type="pubmed_abstract", fact_store_path=path)
            self.assertEqual(len(result2), 2)
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()