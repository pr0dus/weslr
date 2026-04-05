"""Weslr Metamorphic Test Suite (v1)

Non-deterministic and metamorphic test family for stability evaluation.
Designed to be additive and reversible — no production modifications.

Test Families Implemented:
  - paraphrased user asks (materially similar intent handling)
  - structured data reordering (column order variations)
  - formatting differences (text/markdown variations)
  - repeated runs (semantic stability)
  - continuity state preservation (benign variations)
"""

from __future__ import annotations

import json
import re
import tempfile
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from unittest import TestCase

from weslr.suggestion_box import SuggestionBox
from weslr.suggestion_bridge import SuggestionBridge
from weslr.suggestion_assessment import apply_assessment_to_candidate
from weslr.file_router import create_file_router


__all__ = [
    "TestParaphrasedUserAsks",
    "TestStructuredDataReordering",
    "TestFormattingDifferences",
    "TestRepeatedRunStability",
    "TestContinuityStatePreservation",
]


def _normalize_text(text: str) -> str:
    """Normalize text for comparison (lowercase, remove extra whitespace)."""
    text = text.lower().strip()
    text = re.sub(r'\s+', ' ', text)
    return text


def _assert_materially_equivalent(
    self: TestCase,
    result1: str,
    result2: str,
    tolerance: float = 0.85,
) -> None:
    """Assert that two results are materially equivalent within tolerance.
    
    Uses fuzzy matching rather than exact string equality.
    """
    norm1 = _normalize_text(result1)
    norm2 = _normalize_text(result2)
    
    # Simple token-based similarity
    tokens1 = set(norm1.split())
    tokens2 = set(norm2.split())
    
    if not tokens1 or not tokens2:
        # If either is empty, check if both are essentially empty
        self.assertLessEqual(abs(len(norm1) - len(norm2)), 10, 
                           f"Length difference too large: {len(norm1)} vs {len(norm2)}")
        return
    
    intersection = tokens1 & tokens2
    union = tokens1 | tokens2
    
    similarity = len(intersection) / len(union) if union else 0
    
    self.assertGreaterEqual(similarity, tolerance,
                          f"Results not materially equivalent: {similarity:.2f} < {tolerance}")
    self.assertGreaterEqual(len(intersection), 3,
                          f"Not enough shared tokens for material equivalence")


# ============================================================================
# PARAPHRASED USER ASKS TESTS
# ============================================================================

class TestParaphrasedUserAsks(TestCase):
    """Test that paraphrased user asks produce materially similar intent handling."""
    
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)
    
    def test_paraphrased_analysis_requests(self):
        """Different phrasings of analysis requests yield similar routing."""
        # Create test file
        test_file = self.tmpdir / "data.csv"
        test_file.write_text("x,y\n1,2\n3,4\n")
        
        # Paraphrased queries
        queries = [
            "Analyze this CSV file for patterns",
            "Can you examine this data file and find patterns?",
            "Look at this file and detect any patterns in the data",
            "Process this CSV and identify patterns",
        ]
        
        router = create_file_router(workspace_dir=str(self.tmpdir))
        
        results = []
        for query in queries:
            result = router.route(str(test_file), user_query=query)
            results.append(result.category)
        
        # All should route to the same category
        unique_categories = set(results)
        self.assertLessEqual(len(unique_categories), 2,
                           f"Paraphrased queries resulted in too many different categories: {unique_categories}")
    
    def test_paraphrased_request_submissions(self):
        """Paraphrased request submissions maintain consistent structure."""
        storage = self.tmpdir / "requests.json"
        box = SuggestionBox(storage_path=storage)
        
        # Original request
        original = box.submit_request({
            'requester_type': 'university',
            'domain': 'astronomy',
            'requested_capability': 'Spectral analysis',
            'problem_statement': 'I need to analyze stellar spectra',
        })
        
        # Paraphrased variant
        box2 = SuggestionBox(storage_path=storage)
        paraphrased = box2.submit_request({
            'requester_type': 'university',
            'domain': 'astronomy',
            'requested_capability': 'Spectral analysis',
            'problem_statement': 'I want to examine stellar spectra to understand their properties',
        })
        
        # Both should have same requester_type and domain
        self.assertEqual(original.requester_type, paraphrased.requester_type)
        self.assertEqual(original.domain, paraphrased.domain)
        
        # Both should have same capability
        self.assertEqual(original.requested_capability, paraphrased.requested_capability)
    

# ============================================================================
# STRUCTURED DATA REORDERING TESTS
# ============================================================================

class TestStructuredDataReordering(TestCase):
    """Test that structured data with reordered columns produces materially similar routing."""
    
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)
    
    def test_csv_column_reordering(self):
        """CSV files with reordered columns route consistently."""
        router = create_file_router(workspace_dir=str(self.tmpdir))
        
        # Original CSV
        csv1 = self.tmpdir / "data1.csv"
        csv1.write_text("name,value,timestamp\nA,1,2024-01-01\nB,2,2024-01-02\n")
        
        # Reordered columns
        csv2 = self.tmpdir / "data2.csv"
        csv2.write_text("timestamp,name,value\n2024-01-01,A,1\n2024-01-02,B,2\n")
        
        # Route both files
        result1 = router.route(str(csv1), user_query="Analyze this data")
        result2 = router.route(str(csv2), user_query="Analyze this data")
        
        # Should route to same category
        self.assertEqual(result1.category, result2.category)
        
        # Both should have content (not empty)
        self.assertTrue(len(result1.content) > 10)
        self.assertTrue(len(result2.content) > 10)
    
    def test_json_key_reordering(self):
        """JSON objects with reordered keys route consistently."""
        router = create_file_router(workspace_dir=str(self.tmpdir))
        
        # Original JSON
        json1 = self.tmpdir / "data1.json"
        json1.write_text(json.dumps({"name": "test", "value": 42, "category": "science"}))
        
        # Reordered keys
        json2 = self.tmpdir / "data2.json"
        json2.write_text(json.dumps({"category": "science", "name": "test", "value": 42}))
        
        # Route both
        result1 = router.route(str(json1), user_query="Parse this")
        result2 = router.route(str(json2), user_query="Parse this")
        
        # Categories should match
        self.assertEqual(result1.category, result2.category)
    
    def test_yaml_structure_reordering(self):
        """YAML files with reordered keys parse consistently."""
        router = create_file_router(workspace_dir=str(self.tmpdir))
        
        # Original YAML
        yaml1 = self.tmpdir / "data1.yaml"
        yaml1.write_text("name: test\nvalue: 42\ncategory: science\n")
        
        # Reordered
        yaml2 = self.tmpdir / "data2.yaml"
        yaml2.write_text("category: science\nname: test\nvalue: 42\n")
        
        # Route both
        result1 = router.route(str(yaml1), user_query="Parse YAML")
        result2 = router.route(str(yaml2), user_query="Parse YAML")
        
        # Should be same category
        self.assertEqual(result1.category, result2.category)


# ============================================================================
# FORMATTING DIFFERENCES TESTS
# ============================================================================

class TestFormattingDifferences(TestCase):
    """Test that harmless formatting differences don't change core interpretation."""
    
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)
    
    def test_markdown_whitespace_variations(self):
        """Markdown with different whitespace parses consistently."""
        router = create_file_router(workspace_dir=str(self.tmpdir))
        
        # Original markdown
        md1 = self.tmpdir / "doc1.md"
        md1.write_text("""# Title

Some content here.

- Item 1
- Item 2
""")
        
        # With extra whitespace
        md2 = self.tmpdir / "doc2.md"
        md2.write_text("""

# Title


Some content here.


- Item 1
- Item 2


""")
        
        # Route both
        result1 = router.route(str(md1), user_query="Read this")
        result2 = router.route(str(md2), user_query="Read this")
        
        # Categories should match
        self.assertEqual(result1.category, result2.category)
        
        # Content should be materially equivalent (extra whitespace normalized)
        content1 = _normalize_text(result1.content)
        content2 = _normalize_text(result2.content)
        
        _assert_materially_equivalent(self, content1, content2, tolerance=0.9)
    
    def test_code_block_formatting_variations(self):
        """Code blocks with different formatting route consistently."""
        router = create_file_router(workspace_dir=str(self.tmpdir))
        
        # Original
        code1 = self.tmpdir / "code1.txt"
        code1.write_text("""def hello():
    print("Hello")

def world():
    print("World")
""")
        
        # With extra blank lines
        code2 = self.tmpdir / "code2.txt"
        code2.write_text("""def hello():
    print("Hello")


def world():
    print("World")
""")
        
        # Route both
        result1 = router.route(str(code1), user_query="Analyze code")
        result2 = router.route(str(code2), user_query="Analyze code")
        
        # Should be same category
        self.assertEqual(result1.category, result2.category)
    
    def test_html_whitespace_variations(self):
        """HTML with different whitespace is interpreted consistently."""
        router = create_file_router(workspace_dir=str(self.tmpdir))
        
        # Original
        html1 = self.tmpdir / "page1.html"
        html1.write_text("""<html><body><p>Test content</p></body></html>""")
        
        # Formatted
        html2 = self.tmpdir / "page2.html"
        html2.write_text("""<html>
  <body>
    <p>Test content</p>
  </body>
</html>""")
        
        # Route both
        result1 = router.route(str(html1), user_query="Parse HTML")
        result2 = router.route(str(html2), user_query="Parse HTML")
        
        # Should be same category
        self.assertEqual(result1.category, result2.category)


# ============================================================================
# REPEATED RUN STABILITY TESTS
# ============================================================================

class TestRepeatedRunStability(TestCase):
    """Test that repeated runs produce semantically acceptable/stable results."""
    
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)
    
    def test_repeated_file_routing_stability(self):
        """Repeated routing of same file produces stable category."""
        router = create_file_router(workspace_dir=str(self.tmpdir))
        
        test_file = self.tmpdir / "data.csv"
        test_file.write_text("x,y\n1,2\n3,4\n")
        
        categories = []
        for _ in range(5):
            result = router.route(str(test_file), user_query="Analyze")
            categories.append(result.category)
        
        # All categories should be the same
        unique_cats = set(categories)
        self.assertEqual(len(unique_cats), 1,
                        f"Category varied across runs: {unique_cats}")
    
    def test_repeated_suggestion_assessment_stability(self):
        """Repeated assessments of same suggestion are stable."""
        storage = self.tmpdir / "requests.json"
        review = self.tmpdir / "review_queue.json"
        
        box = SuggestionBox(storage_path=storage)
        req = box.submit_request({
            'requester_type': 'university',
            'domain': 'physics',
            'requested_capability': 'Analysis',
            'problem_statement': 'Test analysis',
        })
        
        bridge = SuggestionBridge(review_queue_path=review, suggestion_storage_path=storage)
        
        # Create candidate once
        candidate = bridge.add_proposal_candidate(req.request_id)
        
        # Apply assessment multiple times
        assessments = []
        for _ in range(3):
            assessed = apply_assessment_to_candidate(candidate)
            assessments.append(assessed.get('weslr_assessment', {}).get('risk_level', 'unknown'))
        
        # Risk levels should be consistent
        unique_risks = set(assessments)
        self.assertEqual(len(unique_risks), 1,
                        f"Risk level varied: {unique_risks}")
    
    def test_repeated_continuity_load_stability(self):
        """Repeated continuity loads return stable data."""
        storage = self.tmpdir / "requests.json"
        continuity = self.tmpdir / "continuity.json"
        
        # Create initial state
        box1 = SuggestionBox(storage_path=storage, continuity_path=continuity)
        req1 = box1.submit_request({
            'requester_type': 'laboratory',
            'domain': 'chemistry',
            'requested_capability': 'Test',
            'problem_statement': 'Test',
        })
        
        # Reload multiple times
        for _ in range(3):
            box2 = SuggestionBox(storage_path=storage, continuity_path=continuity)
            request_ids = {r.get('request_id') for r in box2.requests}
            self.assertIn(req1.request_id, request_ids)
    
    def test_request_id_stability(self):
        """Request IDs remain stable across reloads."""
        storage = self.tmpdir / "requests.json"
        box1 = SuggestionBox(storage_path=storage)
        req = box1.submit_request({
            'requester_type': 'company',
            'domain': 'astronomy',
            'requested_capability': 'Analysis',
            'problem_statement': 'Test',
        })
        
        req_id = req.request_id
        
        # Reload
        box2 = SuggestionBox(storage_path=storage)
        
        # Find same request
        found = False
        for r in box2.requests:
            if r.get('request_id') == req_id:
                found = True
                break
        
        self.assertTrue(found, f"Request {req_id} not found after reload")


# ============================================================================
# CONTINUITY STATE PRESERVATION TESTS
# ============================================================================

class TestContinuityStatePreservation(TestCase):
    """Test that continuity reports preserve essential state under benign variations."""
    
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)
    
    def test_state_preservation_across_reload(self):
        """State is preserved when continuity is reloaded."""
        storage = self.tmpdir / "requests.json"
        continuity = self.tmpdir / "continuity.json"
        
        # Create and save
        box1 = SuggestionBox(storage_path=storage, continuity_path=continuity)
        req1 = box1.submit_request({
            'requester_type': 'university',
            'domain': 'astronomy',
            'requested_capability': 'Analysis',
            'problem_statement': 'Test',
        })
        
        # Reload and verify state
        box2 = SuggestionBox(storage_path=storage, continuity_path=continuity)
        
        # Check essential state
        request_ids = {r.get('request_id') for r in box2.requests}
        self.assertIn(req1.request_id, request_ids)
        self.assertGreater(len(box2.requests), 0)
    
    def test_state_preservation_with_new_requests(self):
        """New requests don't corrupt existing state."""
        storage = self.tmpdir / "requests.json"
        
        # Create initial request
        box1 = SuggestionBox(storage_path=storage)
        req1 = box1.submit_request({
            'requester_type': 'laboratory',
            'domain': 'physics',
            'requested_capability': 'Test1',
            'problem_statement': 'Test1',
        })
        
        # Add another request
        req2 = box1.submit_request({
            'requester_type': 'laboratory',
            'domain': 'chemistry',
            'requested_capability': 'Test2',
            'problem_statement': 'Test2',
        })
        
        # Reload and verify both exist
        box2 = SuggestionBox(storage_path=storage)
        request_ids = {r.get('request_id') for r in box2.requests}
        
        self.assertIn(req1.request_id, request_ids)
        self.assertIn(req2.request_id, request_ids)
        self.assertEqual(len(request_ids), 2)
    
    def test_continuity_state_consistency(self):
        """Continuity state remains consistent."""
        storage = self.tmpdir / "requests.json"
        continuity = self.tmpdir / "continuity.json"
        
        # Create initial requests
        box = SuggestionBox(
            storage_path=storage,
            continuity_path=continuity
        )
        
        req1 = box.submit_request({
            'requester_type': 'company',
            'domain': 'chemistry',
            'requested_capability': 'Simulation',
            'problem_statement': 'Simulation',
        })
        
        # Reload and verify state
        box2 = SuggestionBox(
            storage_path=storage,
            continuity_path=continuity
        )
        
        # Continuity should exist
        self.assertTrue(continuity.exists())
        
        # Requests should be loaded
        request_ids = {r.get('request_id') for r in box2.requests}
        self.assertIn(req1.request_id, request_ids)
    
    def test_continuity_without_corruption(self):
        """Continuity remains valid after multiple operations."""
        storage = self.tmpdir / "requests.json"
        continuity = self.tmpdir / "continuity.json"
        
        # Perform multiple operations
        for i in range(5):
            box = SuggestionBox(storage_path=storage, continuity_path=continuity)
            req = box.submit_request({
                'requester_type': 'university',
                'domain': 'physics',
                'requested_capability': f'Test{i}',
                'problem_statement': f'Test{i}',
            })
        
        # Verify continuity file is still valid JSON and exists
        self.assertTrue(continuity.exists())
        
        with open(continuity) as f:
            content = f.read().strip()
            if content:
                try:
                    json.loads(content)
                except json.JSONDecodeError:
                    self.fail(f"Continuity file is invalid JSON: {content[:200]}...")
        
        # Verify all requests are loadable
        box = SuggestionBox(storage_path=storage, continuity_path=continuity)
        self.assertGreater(len(box.requests), 0)


# ============================================================================
# UTILITIES FOR METAMORPHIC TESTING
# ============================================================================

def run_metamorphic_tests() -> Dict[str, Any]:
    """Run all metamorphic tests and return results."""
    import unittest
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all metamorphic test classes
    for cls in [
        TestParaphrasedUserAsks,
        TestStructuredDataReordering,
        TestFormattingDifferences,
        TestRepeatedRunStability,
        TestContinuityStatePreservation,
    ]:
        suite.addTests(loader.loadTestsFromTestCase(cls))
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Format results
    tests_run = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    passed = tests_run - failures - errors
    
    return {
        "tests_run": tests_run,
        "passed": passed,
        "failed": failures,
        "errors": errors,
        "total": tests_run,
        "category": "non_deterministic",
    }


if __name__ == "__main__":
    result = run_metamorphic_tests()
    print(f"\n{'='*60}")
    print(f"Metamorphic Tests Results")
    print(f"{'='*60}")
    print(f"Tests run: {result['tests_run']}")
    print(f"Passed: {result['passed']}")
    print(f"Failed: {result['failed']}")
    print(f"Errors: {result['errors']}")
    print(f"{'='*60}")
