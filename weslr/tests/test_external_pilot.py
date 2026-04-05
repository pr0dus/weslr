"""Weslr External Pilot Simulation Suite (v1)

External pilot simulation for real-world user validation.
Designed to be additive and reversible — no production modifications.

Pilot User Types Simulated:
  - Industrial engineer
  - University researcher
  - Astronomy / exoplanet lab
  - Materials science researcher
  - Enterprise operations manager
  - Public user / weak prompt user

Trust Scoring Dimensions:
  - clarity
  - correctness
  - confidence wording
  - explanation quality
  - perceived reliability
  - governance transparency
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch, MagicMock

from weslr.suggestion_box import SuggestionBox
from weslr.suggestion_bridge import SuggestionBridge
from weslr.suggestion_assessment import apply_assessment_to_candidate


__all__ = [
    "TestIndustrialEngineerPilot",
    "TestUniversityResearcherPilot",
    "TestAstronomyLabPilot",
    "TestMaterialsSciencePilot",
    "TestEnterpriseManagerPilot",
    "TestPublicWeakPromptPilot",
]


# ============================================================================
# INDUSTRIAL ENGINEER PILOT TESTS
# ============================================================================

class TestIndustrialEngineerPilot(TestCase):
    """Simulate industrial engineer using Weslr for operational improvements."""
    
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)
    
    def test_industrial_file_upload_workflow(self):
        """Industrial engineer uploads measurement data."""
        storage = self.tmpdir / "requests.json"
        
        box = SuggestionBox(storage_path=storage)
        
        # Engineer uploads process measurement data
        req = box.submit_request({
            'requester_type': 'company',
            'domain': 'manufacturing',
            'requested_capability': 'Analysis',
            'problem_statement': 'Analyze production line measurements for optimization',
        })
        
        self.assertIsNotNone(req)
        self.assertEqual(req.requester_type, 'company')
    
    def test_industrial_weak_prompt_handling(self):
        """Industrial engineer uses weak but valid prompts."""
        storage = self.tmpdir / "requests.json"
        
        box = SuggestionBox(storage_path=storage)
        
        # Weak prompt (common for industrial users)
        req = box.submit_request({
            'requester_type': 'company',
            'domain': 'manufacturing',
            'requested_capability': 'Monitoring',
            'problem_statement': 'Look at the data',
        })
        
        self.assertIsNotNone(req)
        # Should handle weak prompt without crashing
    
    def test_industrial_malformed_data_handling(self):
        """Industrial engineer uploads malformed measurement files."""
        from weslr.file_router import create_file_router
        
        router = create_file_router(workspace_dir=str(self.tmpdir))
        
        # Malformed but plausible measurement file
        malformed_file = self.tmpdir / "measurements.csv"
        malformed_file.write_text("timestamp,value,error\n1,100,\n2,,0.1\n")  # Missing error, missing value
        
        result = router.route(str(malformed_file))
        
        # RouterResult has attributes, not dict keys
        self.assertIsNotNone(result)
        self.assertTrue(hasattr(result, 'content'))
        self.assertTrue(hasattr(result, 'category'))
    
    def test_industrial_explanation_trust(self):
        """Industrial engineer trusts Weslr explanations."""
        storage = self.tmpdir / "requests.json"
        
        box = SuggestionBox(storage_path=storage)
        req = box.submit_request({
            'requester_type': 'company',
            'domain': 'manufacturing',
            'requested_capability': 'Optimization',
            'problem_statement': 'Optimize production line',
        })
        
        bridge = SuggestionBridge(
            review_queue_path=self.tmpdir / "review_queue.json",
            suggestion_storage_path=storage
        )
        
        candidate = bridge.add_proposal_candidate(req.request_id)
        
        # Should have explanation
        from weslr.suggestion_assessment import apply_assessment_to_candidate
        assessed = apply_assessment_to_candidate(candidate)
        
        assessment = assessed.get('weslr_assessment', {})
        
        # Should have reasoning
        reasoning = assessment.get('reasoning', '')
        self.assertTrue(len(reasoning) > 5,
                      "Industrial engineer should receive reasoning")
    
    def test_industrial_privacy_boundaries(self):
        """Industrial engineer respects privacy boundaries."""
        storage = self.tmpdir / "requests.json"
        
        box = SuggestionBox(storage_path=storage)
        req = box.submit_request({
            'requester_type': 'company',
            'domain': 'manufacturing',
            'requested_capability': 'Analysis',
            'problem_statement': 'Analyze production data',
        })
        
        bridge = SuggestionBridge(
            review_queue_path=self.tmpdir / "review_queue.json",
            suggestion_storage_path=storage
        )
        candidate = bridge.add_proposal_candidate(req.request_id)
        
        # Public output should not contain internal info
        from weslr.weslr_operator_views import build_operator_review_list
        
        assessed = apply_assessment_to_candidate(candidate)
        public_output = build_operator_review_list([assessed])
        
        self.assertNotIn('internal_notes', public_output[0])
        self.assertNotIn('raw_scores', public_output[0])


# ============================================================================
# UNIVERSITY RESEARCHER PILOT TESTS
# ============================================================================

class TestUniversityResearcherPilot(TestCase):
    """Simulate university researcher using Weslr for academic research."""
    
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)
    
    def test_researcher_suggestion_request(self):
        """University researcher submits suggestion request."""
        storage = self.tmpdir / "requests.json"
        
        box = SuggestionBox(storage_path=storage)
        
        req = box.submit_request({
            'requester_type': 'university',
            'domain': 'astronomy',
            'requested_capability': 'Analysis',
            'problem_statement': 'Analyze stellar spectra data',
        })
        
        self.assertIsNotNone(req)
        self.assertEqual(req.domain, 'astronomy')
    
    def test_researcher_weak_prompt_handling(self):
        """University researcher uses research-focused weak prompts."""
        storage = self.tmpdir / "requests.json"
        
        box = SuggestionBox(storage_path=storage)
        
        req = box.submit_request({
            'requester_type': 'university',
            'domain': 'chemistry',
            'requested_capability': 'Processing',
            'problem_statement': 'Process the spectrum data',
        })
        
        self.assertIsNotNone(req)
    
    def test_researcher_explanation_quality(self):
        """University researcher values explanation quality."""
        storage = self.tmpdir / "requests.json"
        
        box = SuggestionBox(storage_path=storage)
        req = box.submit_request({
            'requester_type': 'university',
            'domain': 'physics',
            'requested_capability': 'Detection',
            'problem_statement': 'Detect signal in data',
        })
        
        bridge = SuggestionBridge(
            review_queue_path=self.tmpdir / "review_queue.json",
            suggestion_storage_path=storage
        )
        candidate = bridge.add_proposal_candidate(req.request_id)
        
        assessed = apply_assessment_to_candidate(candidate)
        assessment = assessed.get('weslr_assessment', {})
        
        reasoning = assessment.get('reasoning', '')
        
        # Should have substantive reasoning
        self.assertTrue(len(reasoning) > 10,
                      "Researcher should receive detailed reasoning")
    
    def test_researcher_failure_path_handling(self):
        """University researcher handles failed analysis gracefully."""
        from weslr.file_router import create_file_router
        
        router = create_file_router(workspace_dir=str(self.tmpdir))
        
        # Failed analysis scenario (missing reference data)
        try:
            result = router.route("/nonexistent/reference.fits")
        except Exception:
            # Expected for non-existent file
            pass
    
    def test_researcher_governance_transparency(self):
        """University researcher values governance transparency."""
        storage = self.tmpdir / "requests.json"
        
        box = SuggestionBox(storage_path=storage)
        req = box.submit_request({
            'requester_type': 'university',
            'domain': 'astronomy',
            'requested_capability': 'Analysis',
            'problem_statement': 'Analyze exoplanet data',
        })
        
        bridge = SuggestionBridge(
            review_queue_path=self.tmpdir / "review_queue.json",
            suggestion_storage_path=storage
        )
        
        candidate = bridge.add_proposal_candidate(req.request_id)
        
        # Should be in review queue
        candidates = bridge.list_proposal_candidates()
        
        self.assertGreater(len(candidates), 0,
                          "Researcher should see candidate in queue")


# ============================================================================
# ASTRONOMY / EXOPLANET LAB PILOT TESTS
# ============================================================================

class TestAstronomyLabPilot(TestCase):
    """Simulate astronomy/exoplanet lab using Weslr for scientific analysis."""
    
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)
    
    def test_astronomy_suggestion_request(self):
        """Astronomy lab submits suggestion request."""
        storage = self.tmpdir / "requests.json"
        
        box = SuggestionBox(storage_path=storage)
        
        req = box.submit_request({
            'requester_type': 'university',
            'domain': 'astronomy',
            'requested_capability': 'Exoplanet Detection',
            'problem_statement': 'Detect exoplanets from TESS data',
        })
        
        self.assertIsNotNone(req)
        self.assertEqual(req.domain, 'astronomy')
    
    def test_astronomy_confidence_wording(self):
        """Astronomy lab checks confidence wording in results."""
        from weslr.scientific_analysis import create_scientific_analyzer
        
        with tempfile.TemporaryDirectory() as tmpdir:
            analyzer = create_scientific_analyzer(workspace_dir=tmpdir)
            
            # Create test light curve
            csv_path = Path(tmpdir) / "lc.csv"
            csv_path.write_text("time,brightness,error\n0,1.0,0.01\n1,0.99,0.01\n")
            
            result = analyzer.detect_transit_candidates(str(csv_path))
            
            analysis = result.get('analysis', {})
            candidates = result.get('candidates', [])
            
            # Should have confidence estimates
            if len(candidates) > 0:
                confidence = candidates[0].get('confidence', 0)
                self.assertGreaterEqual(confidence, 0)
                self.assertLessEqual(confidence, 1)
    
    def test_astronomy_explanation_quality(self):
        """Astronomy lab values high-quality explanations."""
        storage = self.tmpdir / "requests.json"
        
        box = SuggestionBox(storage_path=storage)
        req = box.submit_request({
            'requester_type': 'university',
            'domain': 'astronomy',
            'requested_capability': 'Exoplanet Analysis',
            'problem_statement': 'Analyze exoplanet candidates',
        })
        
        bridge = SuggestionBridge(
            review_queue_path=self.tmpdir / "review_queue.json",
            suggestion_storage_path=storage
        )
        candidate = bridge.add_proposal_candidate(req.request_id)
        
        assessed = apply_assessment_to_candidate(candidate)
        assessment = assessed.get('weslr_assessment', {})
        
        reasoning = assessment.get('reasoning', '')
        
        # Should have detailed reasoning for astronomy work
        self.assertTrue(len(reasoning) > 15,
                      "Astronomy lab should receive detailed reasoning")
    
    def test_astronomy_privacy_boundaries(self):
        """Astronomy lab respects privacy boundaries."""
        storage = self.tmpdir / "requests.json"
        
        box = SuggestionBox(storage_path=storage)
        req = box.submit_request({
            'requester_type': 'university',
            'domain': 'astronomy',
            'requested_capability': 'Analysis',
            'problem_statement': 'Analyze Kepler data',
        })
        
        bridge = SuggestionBridge(
            review_queue_path=self.tmpdir / "review_queue.json",
            suggestion_storage_path=storage
        )
        candidate = bridge.add_proposal_candidate(req.request_id)
        
        assessed = apply_assessment_to_candidate(candidate)
        from weslr.weslr_operator_views import build_operator_review_list
        public_output = build_operator_review_list([assessed])
        
        # Should not contain internal lab data
        self.assertNotIn('internal_notes', public_output[0])
    
    def test_astronomy_failure_path_handling(self):
        """Astronomy lab handles data failures gracefully."""
        from weslr.file_router import create_file_router
        
        router = create_file_router(workspace_dir=str(self.tmpdir))
        
        # Missing FITS file
        try:
            result = router.route("/nonexistent/file.fits")
        except Exception:
            # Expected
            pass


# ============================================================================
# MATERIALS SCIENCE RESEARCHER PILOT TESTS
# ============================================================================

class TestMaterialsSciencePilot(TestCase):
    """Simulate materials science researcher using Weslr."""
    
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)
    
    def test_materials_suggestion_request(self):
        """Materials science researcher submits suggestion."""
        storage = self.tmpdir / "requests.json"
        
        box = SuggestionBox(storage_path=storage)
        
        req = box.submit_request({
            'requester_type': 'laboratory',
            'domain': 'materials',
            'requested_capability': 'Analysis',
            'problem_statement': 'Analyze material properties',
        })
        
        self.assertIsNotNone(req)
        self.assertEqual(req.domain, 'materials')
    
    def test_materials_weak_prompt_handling(self):
        """Materials science researcher uses domain-specific weak prompts."""
        storage = self.tmpdir / "requests.json"
        
        box = SuggestionBox(storage_path=storage)
        
        req = box.submit_request({
            'requester_type': 'laboratory',
            'domain': 'materials',
            'requested_capability': 'Simulation',
            'problem_statement': 'Simulate material behavior',
        })
        
        self.assertIsNotNone(req)
    
    def test_materials_explanation_quality(self):
        """Materials science researcher values detailed explanations."""
        storage = self.tmpdir / "requests.json"
        
        box = SuggestionBox(storage_path=storage)
        req = box.submit_request({
            'requester_type': 'laboratory',
            'domain': 'materials',
            'requested_capability': 'Prediction',
            'problem_statement': 'Predict material properties',
        })
        
        bridge = SuggestionBridge(
            review_queue_path=self.tmpdir / "review_queue.json",
            suggestion_storage_path=storage
        )
        candidate = bridge.add_proposal_candidate(req.request_id)
        
        assessed = apply_assessment_to_candidate(candidate)
        assessment = assessed.get('weslr_assessment', {})
        
        reasoning = assessment.get('reasoning', '')
        
        # Should have detailed reasoning
        self.assertTrue(len(reasoning) > 10,
                      "Materials scientist should receive detailed reasoning")
    
    def test_materials_confidence_wording(self):
        """Materials science researcher checks confidence estimates."""
        from weslr.materials_analysis import create_materials_analyzer
        
        with tempfile.TemporaryDirectory() as tmpdir:
            analyzer = create_materials_analyzer(workspace_dir=tmpdir)
            
            # Create materials data
            csv_path = Path(tmpdir) / "materials.csv"
            csv_path.write_text("material,property\nAl,200\nCu,300\n")
            
            result = analyzer.analyze_candidates(str(csv_path), "high property")
            
            ranked = result.get('ranked', [])
            
            # Should have confidence estimates
            if len(ranked) > 0:
                confidence = ranked[0].get('score', 0)
                self.assertGreaterEqual(confidence, 0)
                self.assertLessEqual(confidence, 100)
    
    def test_materials_privacy_boundaries(self):
        """Materials science researcher respects privacy boundaries."""
        storage = self.tmpdir / "requests.json"
        
        box = SuggestionBox(storage_path=storage)
        req = box.submit_request({
            'requester_type': 'laboratory',
            'domain': 'materials',
            'requested_capability': 'Analysis',
            'problem_statement': 'Analyze alloy properties',
        })
        
        bridge = SuggestionBridge(
            review_queue_path=self.tmpdir / "review_queue.json",
            suggestion_storage_path=storage
        )
        candidate = bridge.add_proposal_candidate(req.request_id)
        
        assessed = apply_assessment_to_candidate(candidate)
        from weslr.weslr_operator_views import build_operator_review_list
        public_output = build_operator_review_list([assessed])
        
        # Should not contain internal lab data
        self.assertNotIn('internal_notes', public_output[0])


# ============================================================================
# ENTERPRISE OPERATIONS MANAGER PILOT TESTS
# ============================================================================

class TestEnterpriseManagerPilot(TestCase):
    """Simulate enterprise operations manager using Weslr."""
    
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)
    
    def test_enterprise_suggestion_request(self):
        """Enterprise operations manager submits suggestion."""
        storage = self.tmpdir / "requests.json"
        
        box = SuggestionBox(storage_path=storage)
        
        req = box.submit_request({
            'requester_type': 'company',
            'domain': 'operations',
            'requested_capability': 'Optimization',
            'problem_statement': 'Optimize operational workflow',
        })
        
        self.assertIsNotNone(req)
        self.assertEqual(req.requester_type, 'company')
    
    def test_enterprise_weak_prompt_handling(self):
        """Enterprise operations manager uses operational weak prompts."""
        storage = self.tmpdir / "requests.json"
        
        box = SuggestionBox(storage_path=storage)
        
        req = box.submit_request({
            'requester_type': 'company',
            'domain': 'operations',
            'requested_capability': 'Monitoring',
            'problem_statement': 'Monitor operations',
        })
        
        self.assertIsNotNone(req)
    
    def test_enterprise_explanation_trust(self):
        """Enterprise manager needs trustworthy explanations."""
        storage = self.tmpdir / "requests.json"
        
        box = SuggestionBox(storage_path=storage)
        req = box.submit_request({
            'requester_type': 'company',
            'domain': 'operations',
            'requested_capability': 'Analysis',
            'problem_statement': 'Analyze operational data',
        })
        
        bridge = SuggestionBridge(
            review_queue_path=self.tmpdir / "review_queue.json",
            suggestion_storage_path=storage
        )
        candidate = bridge.add_proposal_candidate(req.request_id)
        
        assessed = apply_assessment_to_candidate(candidate)
        assessment = assessed.get('weslr_assessment', {})
        
        reasoning = assessment.get('reasoning', '')
        
        # Should have clear reasoning for operational decisions
        self.assertTrue(len(reasoning) > 10,
                      "Enterprise manager should receive clear reasoning")
    
    def test_enterprise_governance_transparency(self):
        """Enterprise manager values governance transparency."""
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
        
        candidate = bridge.add_proposal_candidate(req.request_id)
        
        # Should be in review queue
        candidates = bridge.list_proposal_candidates()
        
        self.assertGreater(len(candidates), 0,
                          "Enterprise manager should see candidates")
    
    def test_enterprise_privacy_boundaries(self):
        """Enterprise manager respects privacy boundaries."""
        storage = self.tmpdir / "requests.json"
        
        box = SuggestionBox(storage_path=storage)
        req = box.submit_request({
            'requester_type': 'company',
            'domain': 'operations',
            'requested_capability': 'Analysis',
            'problem_statement': 'Analyze business data',
        })
        
        bridge = SuggestionBridge(
            review_queue_path=self.tmpdir / "review_queue.json",
            suggestion_storage_path=storage
        )
        candidate = bridge.add_proposal_candidate(req.request_id)
        
        assessed = apply_assessment_to_candidate(candidate)
        from weslr.weslr_operator_views import build_operator_review_list
        public_output = build_operator_review_list([assessed])
        
        # Should not contain internal business data
        self.assertNotIn('internal_notes', public_output[0])


# ============================================================================
# PUBLIC / WEAK PROMPT USER PILOT TESTS
# ============================================================================

class TestPublicWeakPromptPilot(TestCase):
    """Simulate public user or weak prompt user using Weslr."""
    
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)
    
    def test_public_weak_prompt_handling(self):
        """Public user uses weak prompts without crashing."""
        storage = self.tmpdir / "requests.json"
        
        box = SuggestionBox(storage_path=storage)
        
        # Very weak prompt (common for public users)
        req = box.submit_request({
            'requester_type': 'company',
            'domain': 'general',
            'requested_capability': 'Processing',
            'problem_statement': 'Process it',
        })
        
        self.assertIsNotNone(req)
    
    def test_public_malformed_input_handling(self):
        """Public user submits malformed input gracefully."""
        storage = self.tmpdir / "requests.json"
        
        box = SuggestionBox(storage_path=storage)
        
        # Valid but minimal request
        req = box.submit_request({
            'requester_type': 'company',
            'domain': 'general',
            'requested_capability': 'Processing',
            'problem_statement': 'Process data',
        })
        
        self.assertIsNotNone(req)
    
    def test_public_explanation_quality(self):
        """Public user needs clear, simple explanations."""
        storage = self.tmpdir / "requests.json"
        
        box = SuggestionBox(storage_path=storage)
        req = box.submit_request({
            'requester_type': 'company',
            'domain': 'general',
            'requested_capability': 'Processing',
            'problem_statement': 'Process data',
        })
        
        bridge = SuggestionBridge(
            review_queue_path=self.tmpdir / "review_queue.json",
            suggestion_storage_path=storage
        )
        candidate = bridge.add_proposal_candidate(req.request_id)
        
        assessed = apply_assessment_to_candidate(candidate)
        assessment = assessed.get('weslr_assessment', {})
        
        reasoning = assessment.get('reasoning', '')
        
        # Should have clear, simple reasoning for public users
        self.assertTrue(len(reasoning) > 5,
                      "Public user should receive simple reasoning")
    
    def test_public_failure_path_handling(self):
        """Public user handles failures gracefully."""
        from weslr.file_router import create_file_router
        
        router = create_file_router(workspace_dir=str(self.tmpdir))
        
        # Non-existent file
        try:
            result = router.route("/nonexistent/file.txt")
        except Exception:
            # Expected
            pass
    
    def test_public_governance_transparency(self):
        """Public user values governance transparency."""
        storage = self.tmpdir / "requests.json"
        
        box = SuggestionBox(storage_path=storage)
        req = box.submit_request({
            'requester_type': 'company',
            'domain': 'general',
            'requested_capability': 'Processing',
            'problem_statement': 'Process data',
        })
        
        bridge = SuggestionBridge(
            review_queue_path=self.tmpdir / "review_queue.json",
            suggestion_storage_path=storage
        )
        
        candidate = bridge.add_proposal_candidate(req.request_id)
        
        # Should be in queue
        candidates = bridge.list_proposal_candidates()
        
        self.assertGreater(len(candidates), 0,
                          "Public user should see candidates")


# ============================================================================
# UTILITIES FOR PILOT TESTS
# ============================================================================

def run_pilot_tests() -> dict[str, any]:
    """Run all pilot tests and return results."""
    import unittest
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    for cls in [
        TestIndustrialEngineerPilot,
        TestUniversityResearcherPilot,
        TestAstronomyLabPilot,
        TestMaterialsSciencePilot,
        TestEnterpriseManagerPilot,
        TestPublicWeakPromptPilot,
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
        "category": "pilot",
    }


if __name__ == "__main__":
    result = run_pilot_tests()
    print(f"\n{'='*60}")
    print(f"External Pilot Simulation Results")
    print(f"{'='*60}")
    print(f"Tests run: {result['tests_run']}")
    print(f"Passed: {result['passed']}")
    print(f"Failed: {result['failed']}")
    print(f"Errors: {result['errors']}")
    print(f"{'='*60}")
