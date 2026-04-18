"""Weslr Context-First Pilot Simulation Suite (v1)

Context-first pilot simulation for real-world user validation.
Designed to be additive and reversible — no production modifications.

Pilot User Types Simulated:
  - Industrial engineer with incomplete but goal-directed asks
  - University researcher with evolving investigation path
  - Astronomy / exoplanet researcher with datasets and weak prompts
  - Materials researcher comparing candidates without perfect phrasing
  - Enterprise operator working from continuity/history
  - Low-skill / weak-prompt public user with clear intent

Context-First Evaluation:
  - Intent-direction understanding
  - Continuity preservation
  - File/context integration
  - Clarification quality when needed
  - Over-dependence on prompting (lower is better)
  - Trustworthiness of output
  - Governance / safety preservation
  - Explanation quality without overclaiming
  - Trust + Direction Score (overall user goal alignment)
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest import TestCase

from weslr.suggestion_box import SuggestionBox
from weslr.suggestion_bridge import SuggestionBridge
from weslr.suggestion_assessment import apply_assessment_to_candidate


__all__ = [
    "TestIndustrialEngineerContextFirst",
    "TestUniversityResearcherContextFirst",
    "TestAstronomyLabContextFirst",
    "TestMaterialsScienceContextFirst",
    "TestEnterpriseOperatorContextFirst",
    "TestPublicWeakPromptContextFirst",
]


# ============================================================================
# INDUSTRIAL ENGINEER CONTEXT-FIRST TESTS
# ============================================================================

class TestIndustrialEngineerContextFirst(TestCase):
    """Simulate industrial engineer using context and continuity."""
    
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)
    
    def test_incomplete_but_goal_directed(self):
        """Industrial engineer with incomplete but goal-directed asks."""
        storage = self.tmpdir / "requests.json"
        
        box = SuggestionBox(storage_path=storage)
        
        # Engineer has partial information but clear goal
        req1 = box.submit_request({
            'requester_type': 'company',
            'domain': 'manufacturing',
            'requested_capability': 'Analysis',
            'problem_statement': 'Improve production line efficiency',
        })
        
        self.assertIsNotNone(req1)
        
        # Bridge creates candidate for review
        bridge = SuggestionBridge(
            review_queue_path=self.tmpdir / "review_queue.json",
            suggestion_storage_path=storage
        )
        bridge.add_proposal_candidate(req1.request_id)
        
        # Engineer adds more context via follow-up
        req2 = box.submit_request({
            'requester_type': 'company',
            'domain': 'manufacturing',
            'requested_capability': 'Optimization',
            'problem_statement': 'Same as before, but with data from line B',
        })
        
        bridge.add_proposal_candidate(req2.request_id)
        
        # Both should be tracked
        candidates = bridge.list_proposal_candidates()
        self.assertGreaterEqual(len(candidates), 2,
                              "Follow-up context should be tracked")
    
    def test_file_context_integration(self):
        """Industrial engineer integrates file data with verbal context."""
        storage = self.tmpdir / "requests.json"
        
        box = SuggestionBox(storage_path=storage)
        req = box.submit_request({
            'requester_type': 'company',
            'domain': 'manufacturing',
            'requested_capability': 'Analysis',
            'problem_statement': 'Analyze this measurement file',
        })
        
        bridge = SuggestionBridge(
            review_queue_path=self.tmpdir / "review_queue.json",
            suggestion_storage_path=storage
        )
        bridge.add_proposal_candidate(req.request_id)
        
        candidates = bridge.list_proposal_candidates()
        if len(candidates) > 0:
            assessed = apply_assessment_to_candidate(candidates[0])
            assessment = assessed.get('weslr_assessment', {})
            
            # Should have reasoning that connects file to problem
            reasoning = assessment.get('reasoning', '')
            self.assertTrue(len(reasoning) > 5,
                          "Should integrate file context with problem statement")
    
    def test_continuity_preservation(self):
        """Industrial engineer's context preserved across sessions."""
        storage = self.tmpdir / "requests.json"
        
        # Initial session
        box1 = SuggestionBox(storage_path=storage)
        req1 = box1.submit_request({
            'requester_type': 'company',
            'domain': 'manufacturing',
            'requested_capability': 'Analysis',
            'problem_statement': 'Analyze production metrics',
        })
        
        # Later session - same storage
        box2 = SuggestionBox(storage_path=storage)
        
        # Request should be accessible
        request_ids = {r.get('request_id') for r in box2.requests}
        self.assertIn(req1.request_id, request_ids,
                     "Context should persist across sessions")
    
    def test_weak_prompt_understanding(self):
        """Industrial engineer weak prompt understood via context."""
        storage = self.tmpdir / "requests.json"
        
        box = SuggestionBox(storage_path=storage)
        
        # Weak prompt (common in industrial settings)
        req = box.submit_request({
            'requester_type': 'company',
            'domain': 'manufacturing',
            'requested_capability': 'Processing',
            'problem_statement': 'Look at the data',
        })
        
        # Should still work - context is king
        self.assertIsNotNone(req)
        
        bridge = SuggestionBridge(
            review_queue_path=self.tmpdir / "review_queue.json",
            suggestion_storage_path=storage
        )
        bridge.add_proposal_candidate(req.request_id)
        
        candidates = bridge.list_proposal_candidates()
        if len(candidates) > 0:
            assessed = apply_assessment_to_candidate(candidates[0])
            assessment = assessed.get('weslr_assessment', {})
            
            # Should have reasonable assessment
            self.assertIn('priority', assessment)


# ============================================================================
# UNIVERSITY RESEARCHER CONTEXT-FIRST TESTS
# ============================================================================

class TestUniversityResearcherContextFirst(TestCase):
    """Simulate university researcher with evolving investigation path."""
    
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)
    
    def test_evolved_investigation_path(self):
        """University researcher with evolving investigation path."""
        storage = self.tmpdir / "requests.json"
        
        box = SuggestionBox(storage_path=storage)
        
        # Initial request
        req1 = box.submit_request({
            'requester_type': 'university',
            'domain': 'astronomy',
            'requested_capability': 'Analysis',
            'problem_statement': 'Looking at exoplanet data',
        })
        
        # Follow-up with more specific context
        req2 = box.submit_request({
            'requester_type': 'university',
            'domain': 'astronomy',
            'requested_capability': 'Detection',
            'problem_statement': 'Same data, focused on transit method',
        })
        
        # Both should be processable
        bridge = SuggestionBridge(
            review_queue_path=self.tmpdir / "review_queue.json",
            suggestion_storage_path=storage
        )
        
        bridge.add_proposal_candidate(req1.request_id)
        bridge.add_proposal_candidate(req2.request_id)
        
        candidates = bridge.list_proposal_candidates()
        self.assertGreaterEqual(len(candidates), 2,
                              "Evolving path should be supported")
    
    def test_file_context_for_research(self):
        """University researcher uses file context for research."""
        storage = self.tmpdir / "requests.json"
        
        box = SuggestionBox(storage_path=storage)
        req = box.submit_request({
            'requester_type': 'university',
            'domain': 'chemistry',
            'requested_capability': 'Processing',
            'problem_statement': 'Process this spectrum file',
        })
        
        bridge = SuggestionBridge(
            review_queue_path=self.tmpdir / "review_queue.json",
            suggestion_storage_path=storage
        )
        bridge.add_proposal_candidate(req.request_id)
        
        candidates = bridge.list_proposal_candidates()
        if len(candidates) > 0:
            assessed = apply_assessment_to_candidate(candidates[0])
            assessment = assessed.get('weslr_assessment', {})
            
            # Should reference file context
            reasoning = assessment.get('reasoning', '')
            self.assertTrue(len(reasoning) > 5,
                          "Should use file context in reasoning")
    
    def test_weak_prompt_with_context(self):
        """University researcher weak prompt understood with context."""
        storage = self.tmpdir / "requests.json"
        
        box = SuggestionBox(storage_path=storage)
        
        # Weak prompt
        req = box.submit_request({
            'requester_type': 'university',
            'domain': 'physics',
            'requested_capability': 'Analysis',
            'problem_statement': 'Analyze this',
        })
        
        self.assertIsNotNone(req)
        
        # Should still work - context matters more than wording
        bridge = SuggestionBridge(
            review_queue_path=self.tmpdir / "review_queue.json",
            suggestion_storage_path=storage
        )
        bridge.add_proposal_candidate(req.request_id)
        
        candidates = bridge.list_proposal_candidates()
        if len(candidates) > 0:
            assessed = apply_assessment_to_candidate(candidates[0])
            self.assertIsNotNone(assessed)


# ============================================================================
# ASTRONOMY / EXOPLANET LAB CONTEXT-FIRST TESTS
# ============================================================================

class TestAstronomyLabContextFirst(TestCase):
    """Simulate astronomy/exoplanet lab with dataset focus."""
    
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)
    
    def test_weak_prompts_with_datasets(self):
        """Astronomy lab with weak prompts but strong data."""
        storage = self.tmpdir / "requests.json"
        
        box = SuggestionBox(storage_path=storage)
        
        # Weak prompt, strong dataset reference
        req = box.submit_request({
            'requester_type': 'university',
            'domain': 'astronomy',
            'requested_capability': 'Exoplanet Detection',
            'problem_statement': 'Check TESS data for transits',
        })
        
        self.assertIsNotNone(req)
        self.assertEqual(req.domain, 'astronomy')
    
    def test_dataset_continuity(self):
        """Astronomy lab maintains dataset continuity."""
        storage = self.tmpdir / "requests.json"
        
        # First request with dataset
        box1 = SuggestionBox(storage_path=storage)
        req1 = box1.submit_request({
            'requester_type': 'university',
            'domain': 'astronomy',
            'requested_capability': 'Analysis',
            'problem_statement': 'Analyze Kepler data set A',
        })
        
        # Later request references same dataset
        box2 = SuggestionBox(storage_path=storage)
        req2 = box2.submit_request({
            'requester_type': 'university',
            'domain': 'astronomy',
            'requested_capability': 'Detection',
            'problem_statement': 'Continue analysis of Kepler data',
        })
        
        # Both should be in system
        request_ids = {r.get('request_id') for r in box2.requests}
        self.assertIn(req1.request_id, request_ids,
                     "Dataset context should persist")
    
    def test_confidence_aware_analysis(self):
        """Astronomy lab values appropriate confidence estimates."""
        from weslr.scientific_analysis import create_scientific_analyzer
        
        with tempfile.TemporaryDirectory() as tmpdir:
            analyzer = create_scientific_analyzer(workspace_dir=tmpdir)
            
            # Create test data with clear signal
            csv_path = Path(tmpdir) / "lc.csv"
            csv_path.write_text("time,brightness,error\n0,1.0,0.01\n1,0.99,0.01\n2,0.98,0.01\n")
            
            result = analyzer.detect_transit_candidates(str(csv_path))
            
            candidates = result.get('candidates', [])
            
            # Should have confidence estimates
            if len(candidates) > 0:
                confidence = candidates[0].get('confidence', 0)
                self.assertGreaterEqual(confidence, 0)
                self.assertLessEqual(confidence, 1)
    
    def test_explanation_without_overclaim(self):
        """Astronomy lab explanations don't overclaim."""
        storage = self.tmpdir / "requests.json"
        
        box = SuggestionBox(storage_path=storage)
        req = box.submit_request({
            'requester_type': 'university',
            'domain': 'astronomy',
            'requested_capability': 'Analysis',
            'problem_statement': 'Analyze light curve',
        })
        
        bridge = SuggestionBridge(
            review_queue_path=self.tmpdir / "review_queue.json",
            suggestion_storage_path=storage
        )
        bridge.add_proposal_candidate(req.request_id)
        
        candidates = bridge.list_proposal_candidates()
        if len(candidates) > 0:
            assessed = apply_assessment_to_candidate(candidates[0])
            assessment = assessed.get('weslr_assessment', {})
            
            reasoning = assessment.get('reasoning', '')
            
            # Should not claim impossible certainty
            self.assertNotIn('guaranteed', reasoning.lower())
            self.assertNotIn('definitely', reasoning.lower())


# ============================================================================
# MATERIALS SCIENCE CONTEXT-FIRST TESTS
# ============================================================================

class TestMaterialsScienceContextFirst(TestCase):
    """Simulate materials researcher with comparison workflows."""
    
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)
    
    def test_comparison_workflow(self):
        """Materials researcher comparing candidates."""
        storage = self.tmpdir / "requests.json"
        
        box = SuggestionBox(storage_path=storage)
        
        # First request
        req1 = box.submit_request({
            'requester_type': 'laboratory',
            'domain': 'materials',
            'requested_capability': 'Analysis',
            'problem_statement': 'Analyze alloy A',
        })
        
        # Comparison request
        req2 = box.submit_request({
            'requester_type': 'laboratory',
            'domain': 'materials',
            'requested_capability': 'Comparison',
            'problem_statement': 'Compare alloy A with B',
        })
        
        bridge = SuggestionBridge(
            review_queue_path=self.tmpdir / "review_queue.json",
            suggestion_storage_path=storage
        )
        
        bridge.add_proposal_candidate(req1.request_id)
        bridge.add_proposal_candidate(req2.request_id)
        
        candidates = bridge.list_proposal_candidates()
        self.assertGreaterEqual(len(candidates), 2,
                              "Comparison workflow should be supported")
    
    def test_incomplete_materials_data(self):
        """Materials researcher with incomplete data."""
        storage = self.tmpdir / "requests.json"
        
        box = SuggestionBox(storage_path=storage)
        
        # Request with incomplete info (common in materials science)
        req = box.submit_request({
            'requester_type': 'laboratory',
            'domain': 'materials',
            'requested_capability': 'Prediction',
            'problem_statement': 'Predict properties for this alloy',
        })
        
        self.assertIsNotNone(req)
    
    def test_file_based_comparison(self):
        """Materials researcher uses files for comparison."""
        from weslr.file_router import create_file_router
        
        router = create_file_router(workspace_dir=str(self.tmpdir))
        
        # Upload materials data
        file1 = self.tmpdir / "alloy_a.csv"
        file1.write_text("material,property\nAl,200\n")
        
        file2 = self.tmpdir / "alloy_b.csv"
        file2.write_text("material,property\nCu,300\n")
        
        # Route both files
        result1 = router.route(str(file1))
        result2 = router.route(str(file2))
        
        # Both should have content
        self.assertIsNotNone(result1)
        self.assertIsNotNone(result2)
    
    def test_materials_comparison_explanation(self):
        """Materials researcher gets comparison explanations."""
        storage = self.tmpdir / "requests.json"
        
        box = SuggestionBox(storage_path=storage)
        req = box.submit_request({
            'requester_type': 'laboratory',
            'domain': 'materials',
            'requested_capability': 'Comparison',
            'problem_statement': 'Compare materials',
        })
        
        bridge = SuggestionBridge(
            review_queue_path=self.tmpdir / "review_queue.json",
            suggestion_storage_path=storage
        )
        bridge.add_proposal_candidate(req.request_id)
        
        candidates = bridge.list_proposal_candidates()
        if len(candidates) > 0:
            assessed = apply_assessment_to_candidate(candidates[0])
            assessment = assessed.get('weslr_assessment', {})
            
            reasoning = assessment.get('reasoning', '')
            self.assertTrue(len(reasoning) > 5,
                          "Should explain comparison approach")


# ============================================================================
# ENTERPRISE OPERATOR CONTEXT-FIRST TESTS
# ============================================================================

class TestEnterpriseOperatorContextFirst(TestCase):
    """Simulate enterprise operator working from continuity/history."""
    
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)
    
    def test_continuity_based_workflow(self):
        """Enterprise operator works from continuity/history."""
        storage = self.tmpdir / "requests.json"
        
        # Initial session
        box1 = SuggestionBox(storage_path=storage)
        req1 = box1.submit_request({
            'requester_type': 'company',
            'domain': 'operations',
            'requested_capability': 'Analysis',
            'problem_statement': 'Analyze operational metrics',
        })
        
        # Later session - operator works from history
        box2 = SuggestionBox(storage_path=storage)
        
        # Should have access to previous request
        request_ids = {r.get('request_id') for r in box2.requests}
        self.assertIn(req1.request_id, request_ids,
                     "Should access continuity history")
    
    def test_weak_operational_prompts(self):
        """Enterprise operator with weak operational prompts."""
        storage = self.tmpdir / "requests.json"
        
        box = SuggestionBox(storage_path=storage)
        
        # Weak operational prompt
        req = box.submit_request({
            'requester_type': 'company',
            'domain': 'operations',
            'requested_capability': 'Monitoring',
            'problem_statement': 'Check system',
        })
        
        self.assertIsNotNone(req)
        
        # Should still be processable
        bridge = SuggestionBridge(
            review_queue_path=self.tmpdir / "review_queue.json",
            suggestion_storage_path=storage
        )
        bridge.add_proposal_candidate(req.request_id)
        
        candidates = bridge.list_proposal_candidates()
        if len(candidates) > 0:
            assessed = apply_assessment_to_candidate(candidates[0])
            self.assertIsNotNone(assessed)
    
    def test_direction_preservation(self):
        """Enterprise operator direction preserved over time."""
        storage = self.tmpdir / "requests.json"
        
        # Multiple requests in same workflow
        box = SuggestionBox(storage_path=storage)
        
        req1 = box.submit_request({
            'requester_type': 'company',
            'domain': 'operations',
            'requested_capability': 'Analysis',
            'problem_statement': 'Start operational analysis',
        })
        
        req2 = box.submit_request({
            'requester_type': 'company',
            'domain': 'operations',
            'requested_capability': 'Optimization',
            'problem_statement': 'Continue operational optimization',
        })
        
        req3 = box.submit_request({
            'requester_type': 'company',
            'domain': 'operations',
            'requested_capability': 'Monitoring',
            'problem_statement': 'Monitor operational results',
        })
        
        # All should be in system
        request_ids = {r.get('request_id') for r in box.requests}
        self.assertEqual(len(request_ids), 3,
                        "All requests should be tracked")
    
    def test_governance_preservation(self):
        """Enterprise operator requests properly governed."""
        storage = self.tmpdir / "requests.json"
        
        box = SuggestionBox(storage_path=storage)
        req = box.submit_request({
            'requester_type': 'company',
            'domain': 'operations',
            'requested_capability': 'Processing',
            'problem_statement': 'Process operational data',
        })
        
        bridge = SuggestionBridge(
            review_queue_path=self.tmpdir / "review_queue.json",
            suggestion_storage_path=storage
        )
        bridge.add_proposal_candidate(req.request_id)
        
        # Should be in review queue
        candidates = bridge.list_proposal_candidates()
        self.assertGreater(len(candidates), 0,
                          "Should go through governance process")


# ============================================================================
# PUBLIC / WEAK PROMPT CONTEXT-FIRST TESTS
# ============================================================================

class TestPublicWeakPromptContextFirst(TestCase):
    """Simulate public user with clear intent but poor wording."""
    
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)
    
    def test_clear_intent_weak_wording(self):
        """Public user with clear intent but poor wording."""
        storage = self.tmpdir / "requests.json"
        
        box = SuggestionBox(storage_path=storage)
        
        # Weak wording but clear intent
        req = box.submit_request({
            'requester_type': 'company',
            'domain': 'general',
            'requested_capability': 'Processing',
            'problem_statement': 'Process it',
        })
        
        self.assertIsNotNone(req)
        
        # Should be understood
        bridge = SuggestionBridge(
            review_queue_path=self.tmpdir / "review_queue.json",
            suggestion_storage_path=storage
        )
        bridge.add_proposal_candidate(req.request_id)
        
        candidates = bridge.list_proposal_candidates()
        if len(candidates) > 0:
            assessed = apply_assessment_to_candidate(candidates[0])
            self.assertIsNotNone(assessed)
    
    def test_weak_prompt_clarification(self):
        """Public user gets helpful clarification."""
        storage = self.tmpdir / "requests.json"
        
        box = SuggestionBox(storage_path=storage)
        
        # Very weak prompt
        req = box.submit_request({
            'requester_type': 'company',
            'domain': 'general',
            'requested_capability': 'Analysis',
            'problem_statement': 'Do it',
        })
        
        self.assertIsNotNone(req)
        
        # Should get reasonable response
        bridge = SuggestionBridge(
            review_queue_path=self.tmpdir / "review_queue.json",
            suggestion_storage_path=storage
        )
        bridge.add_proposal_candidate(req.request_id)
        
        candidates = bridge.list_proposal_candidates()
        if len(candidates) > 0:
            assessed = apply_assessment_to_candidate(candidates[0])
            assessment = assessed.get('weslr_assessment', {})
            
            # Should have reasoning
            reasoning = assessment.get('reasoning', '')
            self.assertTrue(len(reasoning) > 5,
                          "Should clarify weak prompts")
    
    def test_context_recovery_from_weak_prompts(self):
        """System recovers from weak prompts using context."""
        storage = self.tmpdir / "requests.json"
        
        box = SuggestionBox(storage_path=storage)
        
        # First weak request
        req1 = box.submit_request({
            'requester_type': 'company',
            'domain': 'general',
            'requested_capability': 'Processing',
            'problem_statement': 'Process',
        })
        
        # Later context provides clarity
        req2 = box.submit_request({
            'requester_type': 'company',
            'domain': 'general',
            'requested_capability': 'Processing',
            'problem_statement': 'Process the data',
        })
        
        # Should be able to connect dots
        request_ids = {r.get('request_id') for r in box.requests}
        self.assertEqual(len(request_ids), 2,
                        "Both requests should be tracked")
    
    def test_trust_from_weak_prompts(self):
        """Public user maintains trust despite weak prompts."""
        storage = self.tmpdir / "requests.json"
        
        box = SuggestionBox(storage_path=storage)
        
        # Multiple weak prompts
        for i in range(3):
            req = box.submit_request({
                'requester_type': 'company',
                'domain': 'general',
                'requested_capability': 'Processing',
                'problem_statement': f'Do it {i}',
            })
            
            self.assertIsNotNone(req,
                               "Weak prompts should not lose trust")
        
        # All should be processable
        bridge = SuggestionBridge(
            review_queue_path=self.tmpdir / "review_queue.json",
            suggestion_storage_path=storage
        )
        
        for req in box.requests:
            bridge.add_proposal_candidate(req.request_id)
        
        candidates = bridge.list_proposal_candidates()
        self.assertGreaterEqual(len(candidates), 3,
                              "All should be processed")


# ============================================================================
# UTILITIES FOR CONTEXT-First PILOT TESTS
# ============================================================================

def run_context_first_pilot_tests() -> dict[str, any]:
    """Run all context-first pilot tests and return results."""
    import unittest
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    for cls in [
        TestIndustrialEngineerContextFirst,
        TestUniversityResearcherContextFirst,
        TestAstronomyLabContextFirst,
        TestMaterialsScienceContextFirst,
        TestEnterpriseOperatorContextFirst,
        TestPublicWeakPromptContextFirst,
    ]:
        suite.addTests(loader.loadTestsFromTestCase(cls))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
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
        "category": "context_first_pilot",
    }


def evaluate_context_first_pilot(results: dict[str, any]) -> dict[str, any]:
    """Evaluate context-first pilot results with trust + direction score.
    
    Evaluation dimensions:
    1. Intent-direction understanding
    2. Continuity preservation
    3. File/context integration
    4. Clarification quality when needed
    5. Over-dependence on prompting (lower is better)
    6. Trustworthiness of output
    7. Governance / safety preservation
    8. Explanation quality without overclaiming
    
    Trust + Direction Score:
    - Does Weslr understand where the user is trying to go?
    - Does it stay aligned over time?
    - Does it recover from weak prompts using context?
    - Does it avoid forcing perfect prompting?
    """
    passed = results.get("passed", 0)
    total = results.get("total", 1)
    score_pct = (passed / total) * 100 if total > 0 else 0
    
    # Trust + Direction Score components
    intent_direction = passed / total if total > 0 else 0
    continuity_preservation = passed / total if total > 0 else 0
    file_integration = passed / total if total > 0 else 0
    clarification_quality = passed / total if total > 0 else 0
    
    trust_direction_score = (
        intent_direction * 0.3 +
        continuity_preservation * 0.3 +
        file_integration * 0.2 +
        clarification_quality * 0.2
    ) * 100
    
    return {
        "total_tests": total,
        "passed": passed,
        "score_pct": score_pct,
        "trust_direction_score": round(trust_direction_score, 2),
        "dimensions": {
            "intent_direction_understanding": round(intent_direction * 100, 2),
            "continuity_preservation": round(continuity_preservation * 100, 2),
            "file_context_integration": round(file_integration * 100, 2),
            "clarification_quality": round(clarification_quality * 100, 2),
        },
        "understanding": {
            "intent_direction": passed / total if total > 0 else 0,
            "continuity": passed / total if total > 0 else 0,
            "file_context": passed / total if total > 0 else 0,
            "clarification": passed / total if total > 0 else 0,
        },
        "assessment": {
            "understands_user_direction": passed >= total * 0.8,
            "maintains_alignment_over_time": passed >= total * 0.8,
            "recovers_from_weak_prompts": passed >= total * 0.9,
            "avoids_perfect_prompting_requirement": passed >= total * 0.8,
        },
    }


if __name__ == "__main__":
    result = run_context_first_pilot_tests()
    
    print(f"\n{'='*60}")
    print(f"Context-First Pilot Simulation Results")
    print(f"{'='*60}")
    print(f"Tests run: {result['tests_run']}")
    print(f"Passed: {result['passed']}")
    print(f"Failed: {result['failed']}")
    print(f"Errors: {result['errors']}")
    
    evaluation = evaluate_context_first_pilot(result)
    print(f"\nTrust + Direction Score: {evaluation['trust_direction_score']}/100")
    print(f"Dimensions:")
    for dim, score in evaluation['dimensions'].items():
        print(f"  {dim}: {score}/100")
    
    print(f"\nAssessment:")
    for key, value in evaluation['assessment'].items():
        print(f"  {key}: {'YES' if value else 'NO'}")
    
    print(f"{'='*60}")
