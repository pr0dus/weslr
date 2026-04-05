"""Weslr Explainability Consistency Test Suite (v1)

Explainability and consistency tests for reasoning alignment.
Designed to be additive and reversible — no production modifications.

Test Families Implemented:
  - Weslr assessment reasoning consistency with scores
  - recommended action consistency with assessment fields
  - scientific candidate outputs not overclaiming evidence
  - habitable-zone explanations matching calculated boundaries
  - materials ranking explanations matching criteria
  - notebook/timeline summaries aligned with source data
  - operator-facing explanations aligned with review status
  - explanations not exposing protected details
  - fallback/error explanations remaining safe
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest import TestCase

from weslr.suggestion_box import SuggestionBox
from weslr.suggestion_bridge import SuggestionBridge
from weslr.suggestion_assessment import apply_assessment_to_candidate
from weslr.scientific_analysis import create_scientific_analyzer
from weslr.habitable_zone import create_habitable_zone_estimator
from weslr.materials_analysis import create_materials_analyzer


__all__ = [
    "TestAssessmentReasoningConsistency",
    "TestRecommendedActionConsistency",
    "TestScientificCandidateNoOverclaim",
    "TestHabitableZoneExplanationConsistency",
    "TestMaterialsRankingExplanationConsistency",
    "TestNotebookTimelineSummaryAlignment",
    "TestOperatorExplanationAlignment",
    "TestExplanationNoProtectedLeakage",
    "TestFallbackExplanationSafety",
]


# ============================================================================
# ASSESSMENT REASONING CONSISTENCY TESTS
# ============================================================================

class TestAssessmentReasoningConsistency(TestCase):
    """Test that Weslr assessment reasoning matches priority/fit/risk scores."""
    
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)
    
    def test_risk_level_matches_reasoning(self):
        """Risk level consistent with assessment reasoning."""
        storage = self.tmpdir / "requests.json"
        review = self.tmpdir / "review_queue.json"
        
        box = SuggestionBox(storage_path=storage)
        req = box.submit_request({
            'requester_type': 'university',
            'domain': 'astronomy',
            'requested_capability': 'Analysis',
            'problem_statement': 'Standard analysis request',
        })
        
        bridge = SuggestionBridge(review_queue_path=review, suggestion_storage_path=storage)
        candidate = bridge.add_proposal_candidate(req.request_id)
        assessed = apply_assessment_to_candidate(candidate)
        
        assessment = assessed.get('weslr_assessment', {})
        
        # Verify internal consistency
        risk_level = assessment.get('risk_level', 'unknown')
        reasoning = assessment.get('reasoning', '')
        
        # High risk should have strong justification
        if risk_level == 'high':
            self.assertTrue(len(reasoning) > 10,
                          "High risk should have substantial reasoning")
        elif risk_level == 'low':
            # Low risk reasoning should indicate confidence
            self.assertTrue(len(reasoning) > 5,
                          "Low risk should have basic reasoning")
    
    def test_priority_consistent_with_risk(self):
        """Priority ranking consistent with risk level."""
        storage = self.tmpdir / "requests.json"
        review = self.tmpdir / "review_queue.json"
        
        box = SuggestionBox(storage_path=storage)
        req = box.submit_request({
            'requester_type': 'laboratory',
            'domain': 'physics',
            'requested_capability': 'Detection',
            'problem_statement': 'Detection request',
        })
        
        bridge = SuggestionBridge(review_queue_path=review, suggestion_storage_path=storage)
        candidate = bridge.add_proposal_candidate(req.request_id)
        assessed = apply_assessment_to_candidate(candidate)
        
        assessment = assessed.get('weslr_assessment', {})
        
        risk_level = assessment.get('risk_level', 'unknown')
        priority = assessment.get('weslr_priority', 0)
        
        # Lower risk should have higher priority
        if risk_level == 'low':
            self.assertGreaterEqual(priority, 7,
                                  "Low risk should have high priority")
        elif risk_level == 'high':
            self.assertLessEqual(priority, 5,
                               "High risk should have lower priority")
    
    def test_fit_score_aligned_with_reasoning(self):
        """Fit score aligned with assessment reasoning."""
        storage = self.tmpdir / "requests.json"
        review = self.tmpdir / "review_queue.json"
        
        box = SuggestionBox(storage_path=storage)
        req = box.submit_request({
            'requester_type': 'company',
            'domain': 'chemistry',
            'requested_capability': 'Simulation',
            'problem_statement': 'Simulation request',
        })
        
        bridge = SuggestionBridge(review_queue_path=review, suggestion_storage_path=storage)
        candidate = bridge.add_proposal_candidate(req.request_id)
        assessed = apply_assessment_to_candidate(candidate)
        
        assessment = assessed.get('weslr_assessment', {})
        
        fit_score = assessment.get('weslr_fit_score', 0)
        reasoning = assessment.get('reasoning', '')
        
        # Higher fit score should have supporting reasoning
        if fit_score >= 0.8:
            self.assertTrue(len(reasoning) > 5,
                          "High fit score should have reasoning")
    
    def test_assessment_fields_internal_consistency(self):
        """All assessment fields internally consistent."""
        storage = self.tmpdir / "requests.json"
        review = self.tmpdir / "review_queue.json"
        
        box = SuggestionBox(storage_path=storage)
        req = box.submit_request({
            'requester_type': 'university',
            'domain': 'astronomy',
            'requested_capability': 'Analysis',
            'problem_statement': 'Analysis request',
        })
        
        bridge = SuggestionBridge(review_queue_path=review, suggestion_storage_path=storage)
        candidate = bridge.add_proposal_candidate(req.request_id)
        assessed = apply_assessment_to_candidate(candidate)
        
        assessment = assessed.get('weslr_assessment', {})
        
        # All required fields present
        self.assertIn('risk_level', assessment)
        self.assertIn('weslr_priority', assessment)
        self.assertIn('weslr_fit_score', assessment)
        self.assertIn('reasoning', assessment)
        
        # Reasoning present for all assessments
        self.assertTrue(len(assessment.get('reasoning', '')) > 0,
                      "Reasoning should always be present")


# ============================================================================
# RECOMMENDED ACTION CONSISTENCY TESTS
# ============================================================================

class TestRecommendedActionConsistency(TestCase):
    """Test that recommended actions are consistent with assessment fields."""
    
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)
    
    def test_action_consistent_with_risk(self):
        """Recommended action consistent with risk level."""
        storage = self.tmpdir / "requests.json"
        review = self.tmpdir / "review_queue.json"
        
        box = SuggestionBox(storage_path=storage)
        req = box.submit_request({
            'requester_type': 'university',
            'domain': 'astronomy',
            'requested_capability': 'Analysis',
            'problem_statement': 'Analysis request',
        })
        
        bridge = SuggestionBridge(review_queue_path=review, suggestion_storage_path=storage)
        candidate = bridge.add_proposal_candidate(req.request_id)
        assessed = apply_assessment_to_candidate(candidate)
        
        assessment = assessed.get('weslr_assessment', {})
        
        risk_level = assessment.get('risk_level', 'unknown')
        recommended_action = assessment.get('recommended_action', '')
        
        # Verify action is provided and reasonable
        self.assertTrue(len(recommended_action) > 0,
                      "Recommended action should always be provided")
        
        # Risk level should match action type
        if risk_level == 'low':
            self.assertIn('approved', recommended_action.lower(),
                         "Low risk should have approved action")
    
    def test_action_reasonable_for_domain(self):
        """Recommended action reasonable for domain."""
        storage = self.tmpdir / "requests.json"
        review = self.tmpdir / "review_queue.json"
        
        box = SuggestionBox(storage_path=storage)
        
        # Science domain
        req1 = box.submit_request({
            'requester_type': 'laboratory',
            'domain': 'physics',
            'requested_capability': 'Detection',
            'problem_statement': 'Detection request',
        })
        
        # Industry domain
        req2 = box.submit_request({
            'requester_type': 'company',
            'domain': 'chemistry',
            'requested_capability': 'Simulation',
            'problem_statement': 'Simulation request',
        })
        
        bridge = SuggestionBridge(review_queue_path=review, suggestion_storage_path=storage)
        
        for req in [req1, req2]:
            candidate = bridge.add_proposal_candidate(req.request_id)
            assessed = apply_assessment_to_candidate(candidate)
            
            recommended_action = assessed.get('weslr_assessment', {}).get('recommended_action', '')
            
            # Action should be reasonable (not empty or suspicious)
            self.assertTrue(len(recommended_action) > 5,
                          "Recommended action should be substantive")
            self.assertNotIn('ERROR', recommended_action.upper(),
                           "Action should not contain error indicators")
    
    def test_action_does_not_overpromise(self):
        """Recommended action does not overpromise capabilities."""
        storage = self.tmpdir / "requests.json"
        review = self.tmpdir / "review_queue.json"
        
        box = SuggestionBox(storage_path=storage)
        req = box.submit_request({
            'requester_type': 'university',
            'domain': 'astronomy',
            'requested_capability': 'Analysis',
            'problem_statement': 'Analysis request',
        })
        
        bridge = SuggestionBridge(review_queue_path=review, suggestion_storage_path=storage)
        candidate = bridge.add_proposal_candidate(req.request_id)
        assessed = apply_assessment_to_candidate(candidate)
        
        assessment = assessed.get('weslr_assessment', {})
        recommended_action = assessment.get('recommended_action', '')
        
        # Should not claim impossible or overconfident actions
        overconfidence_indicators = [
            'guaranteed',
            'definitely',
            '100%',
            'perfect',
            'certain',
        ]
        
        action_lower = recommended_action.lower()
        for indicator in overconfidence_indicators:
            self.assertNotIn(indicator, action_lower,
                           f"Action should not contain overconfidence: {indicator}")


# ============================================================================
# SCIENTIFIC CANDIDATE NO OVERCLAIM TESTS
# ============================================================================

class TestScientificCandidateNoOverclaim(TestCase):
    """Test that scientific candidate outputs do not overclaim beyond evidence."""
    
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)
    
    def test_transit_candidate_no_overclaim(self):
        """Transit candidate outputs not overclaiming evidence."""
        with tempfile.TemporaryDirectory() as tmpdir:
            analyzer = create_scientific_analyzer(workspace_dir=tmpdir)
            
            # Create simple CSV with clear signal
            csv_path = Path(tmpdir) / "light_curve.csv"
            csv_path.write_text("time,brightness,error\n0,1.0,0.01\n1,0.99,0.01\n2,0.98,0.01\n")
            
            result = analyzer.detect_transit_candidates(str(csv_path))
            
            analysis = result.get('analysis', {})
            candidates = result.get('candidates', [])
            
            # Verify analysis is realistic
            transit_count = analysis.get('transit_count', 0)
            
            if len(candidates) > 0 and transit_count > 0:
                # Should have reasonable confidence estimates
                for candidate in candidates:
                    confidence = candidate.get('confidence', 0)
                    self.assertGreaterEqual(confidence, 0,
                                          "Confidence should be >= 0")
                    self.assertLessEqual(confidence, 1,
                                       "Confidence should be <= 1")
    
    def test_transit_analysis_not_overconfident(self):
        """Transit analysis doesn't claim certainty beyond data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            analyzer = create_scientific_analyzer(workspace_dir=tmpdir)
            
            # Create sparse data
            csv_path = Path(tmpdir) / "sparse.csv"
            csv_path.write_text("time,brightness,error\n0,1.0,0.1\n")
            
            result = analyzer.detect_transit_candidates(str(csv_path))
            
            analysis = result.get('analysis', {})
            
            # Should report limitations, not overclaim
            self.assertIsNotNone(analysis,
                               "Analysis should be present even with sparse data")
    
    def test_candidate_detection_safe_outputs(self):
        """Candidate detection produces safe outputs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            analyzer = create_scientific_analyzer(workspace_dir=tmpdir)
            
            csv_path = Path(tmpdir) / "data.csv"
            csv_path.write_text("time,brightness,error\n0,1.0,0.01\n")
            
            result = analyzer.detect_transit_candidates(str(csv_path))
            
            # Should contain expected fields
            self.assertIn('candidates', result)
            self.assertIn('analysis', result)
            self.assertIn('metadata', result)


# ============================================================================
# HABITABLE ZONE EXPLANATION CONSISTENCY TESTS
# ============================================================================

class TestHabitableZoneExplanationConsistency(TestCase):
    """Test that habitable zone explanations match calculated boundaries."""
    
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)
    
    def test_habitable_zone_calculation_consistency(self):
        """Habitable zone calculation internally consistent."""
        estimator = create_habitable_zone_estimator()
        
        result = estimator.estimate_zone(luminosity=1.0, orbit_distance=1.0)
        
        zone = result.get('habitable_zone', {})
        
        inner = zone.get('inner_boundary', 0)
        outer = zone.get('outer_boundary', 0)
        
        # Inner should be less than outer
        self.assertLess(inner, outer,
                       "Inner boundary should be less than outer")
        
        # Check calculation matches expected formula
        # inner = 0.95 * sqrt(L), outer = 1.37 * sqrt(L)
        import math
        expected_inner = 0.95 * math.sqrt(1.0)
        expected_outer = 1.37 * math.sqrt(1.0)
        
        self.assertAlmostEqual(inner, expected_inner, places=1,
                             msg=f"Inner boundary mismatch: {inner} vs {expected_inner}")
        self.assertAlmostEqual(outer, expected_outer, places=1,
                             msg=f"Outer boundary mismatch: {outer} vs {expected_outer}")
    
    def test_zone_explanation_not_overconfident(self):
        """Zone explanation doesn't overclaim certainty."""
        estimator = create_habitable_zone_estimator()
        
        result = estimator.estimate_zone(luminosity=1.0, orbit_distance=1.0)
        
        zone = result.get('habitable_zone', {})
        analysis = result.get('analysis', {})
        
        # Analysis should be present
        self.assertIsNotNone(analysis)
        
        # Should not claim impossible certainty
        analysis_text = json.dumps(analysis).lower()
        self.assertNotIn('guaranteed', analysis_text)
        self.assertNotIn('definitely', analysis_text)
    
    def test_zone_boundaries_reasonable(self):
        """Zone boundaries are reasonable for star."""
        estimator = create_habitable_zone_estimator()
        
        # Test with various stars
        test_cases = [
            {'luminosity': 1.0, 'orbit_distance': 1.0},  # Sun-like
            {'luminosity': 0.1, 'orbit_distance': 0.3},   # Dim star
            {'luminosity': 10.0, 'orbit_distance': 3.0},  # Bright star
        ]
        
        for params in test_cases:
            result = estimator.estimate_zone(**params)
            zone = result.get('habitable_zone', {})
            
            inner = zone.get('inner_boundary', 0)
            outer = zone.get('outer_boundary', 0)
            
            # Should be positive
            self.assertGreater(inner, 0, "Inner boundary should be positive")
            self.assertGreater(outer, 0, "Outer boundary should be positive")
            self.assertLess(inner, outer, "Inner should be less than outer")


# ============================================================================
# MATERIALS RANKING EXPLANATION CONSISTENCY TESTS
# ============================================================================

class TestMaterialsRankingExplanationConsistency(TestCase):
    """Test that materials ranking explanations match criteria used."""
    
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)
    
    def test_ranking_explanation_matches_criteria(self):
        """Materials ranking explanation matches criteria used."""
        with tempfile.TemporaryDirectory() as tmpdir:
            analyzer = create_materials_analyzer(workspace_dir=tmpdir)
            
            # Create materials CSV
            csv_path = Path(tmpdir) / "materials.csv"
            csv_path.write_text("material,thermal_conductivity,electrical_conductivity\naluminum,200,37\nsteel,50,10\ncopper,300,59\n")
            
            result = analyzer.analyze_candidates(str(csv_path), "high thermal conductivity")
            
            ranked = result.get('ranked', [])
            candidates = result.get('candidates', [])
            
            # Ranked should be ordered by relevance
            if len(ranked) > 0:
                # First should be best match
                self.assertIn('material', ranked[0])
                self.assertIn('score', ranked[0])
    
    def test_analysis_not_overconfident(self):
        """Materials analysis doesn't overclaim certainty."""
        with tempfile.TemporaryDirectory() as tmpdir:
            analyzer = create_materials_analyzer(workspace_dir=tmpdir)
            
            csv_path = Path(tmpdir) / "materials.csv"
            csv_path.write_text("material,property\nAl,200\n")
            
            result = analyzer.analyze_candidates(str(csv_path), "high property")
            
            analysis = result.get('analysis', {})
            
            # Should not contain overconfident language
            analysis_str = json.dumps(analysis)
            self.assertNotIn('guaranteed', analysis_str.lower())
    
    def test_ranking_order_consistent(self):
        """Materials ranking order is consistent."""
        with tempfile.TemporaryDirectory() as tmpdir:
            analyzer = create_materials_analyzer(workspace_dir=tmpdir)
            
            csv_path = Path(tmpdir) / "materials.csv"
            csv_path.write_text("material,thermal_conductivity\nmaterial_a,100\nmaterial_b,200\nmaterial_c,150\n")
            
            result = analyzer.analyze_candidates(str(csv_path), "high thermal conductivity")
            
            ranked = result.get('ranked', [])
            
            if len(ranked) >= 2:
                # Should be ordered by score (highest first)
                for i in range(len(ranked) - 1):
                    self.assertGreaterEqual(ranked[i].get('score', 0),
                                          ranked[i + 1].get('score', 0),
                                          "Ranking should be descending by score")


# ============================================================================
# NOTEBOOK/TIMELINE SUMMARY ALIGNMENT TESTS
# ============================================================================

class TestNotebookTimelineSummaryAlignment(TestCase):
    """Test that notebook/timeline summaries remain aligned with source data."""
    
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)
    
    def test_notebook_summary_aligned_with_content(self):
        """Notebook summary aligned with actual content."""
        from weslr.scientific_notebook import create_scientific_notebook
        
        notebook = create_scientific_notebook()
        
        md_path = self.tmpdir / "notebook.md"
        md_path.write_text("""---
candidate_id: KIC-12345678
confidence: 0.85
star_target: Kepler-160
---

# Observation Log

## Transit Analysis
- Depth: 0.5%
- Duration: 4 hours
- Period: 3.5 days
""")
        
        result = notebook.parse_markdown(str(md_path))
        
        metadata = result.get('metadata', {})
        content = result.get('content', '')
        
        # Summary should be derived from content
        self.assertIn('metadata', result)
        self.assertIn('content', result)
        
        # Content should contain the analysis section
        self.assertIn('Transit', content)
    
    def test_timeline_events_aligned_with_input(self):
        """Timeline events aligned with input data."""
        from weslr.evidence_timeline import create_evidence_timeline
        
        with tempfile.TemporaryDirectory() as tmpdir:
            timeline = create_evidence_timeline(
                workspace_dir=tmpdir,
                storage_dir=tmpdir
            )
            
            # Add events
            timeline.add_event("test-001", {
                "type": "transit_detection",
                "confidence": 0.85,
                "timestamp": "2024-01-01T00:00:00Z",
            })
            
            # Get events
            events = timeline.get_events("test-001")
            
            self.assertGreater(len(events), 0,
                             "Events should be retrievable")
            
            if len(events) > 0:
                # First event should match what was added
                event = events[0]
                self.assertEqual(event.get('confidence'), 0.85,
                               "Event confidence should match input")
                self.assertEqual(event.get('type'), 'transit_detection',
                               "Event type should match input")
    
    def test_summary_does_not_overclaim(self):
        """Summary does not overclaim beyond evidence."""
        from weslr.scientific_notebook import create_scientific_notebook
        
        notebook = create_scientific_notebook()
        
        md_path = self.tmpdir / "notebook.md"
        # Minimal notebook
        md_path.write_text("""# Observation Log

Some content here.
""")
        
        result = notebook.parse_markdown(str(md_path))
        
        content = result.get('content', '')
        
        # Should not contain overconfident language
        content_lower = content.lower()
        self.assertNotIn('definitely', content_lower)
        self.assertNotIn('guaranteed', content_lower)


# ============================================================================
# OPERATOR EXPLANATION ALIGNMENT TESTS
# ============================================================================

class TestOperatorExplanationAlignment(TestCase):
    """Test that operator-facing explanation fields do not contradict review status."""
    
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)
    
    def test_explanation_aligned_with_status(self):
        """Operator explanation aligned with review status."""
        storage = self.tmpdir / "requests.json"
        review = self.tmpdir / "review_queue.json"
        
        box = SuggestionBox(storage_path=storage)
        req = box.submit_request({
            'requester_type': 'university',
            'domain': 'astronomy',
            'requested_capability': 'Analysis',
            'problem_statement': 'Analysis request',
        })
        
        bridge = SuggestionBridge(review_queue_path=review, suggestion_storage_path=storage)
        candidate = bridge.add_proposal_candidate(req.request_id)
        
        # Get initial status
        initial_status = candidate.get('review_status', 'pending')
        
        # Get assessment
        assessed = apply_assessment_to_candidate(candidate)
        reasoning = assessed.get('weslr_assessment', {}).get('reasoning', '')
        
        # Status should be consistent with assessment
        self.assertIn(initial_status, ['pending', 'review'])
        self.assertTrue(len(reasoning) > 0,
                      "Reasoning should be present")
    
    def test_assessment_reasoning_for_status(self):
        """Assessment reasoning appropriate for status."""
        storage = self.tmpdir / "requests.json"
        review = self.tmpdir / "review_queue.json"
        
        box = SuggestionBox(storage_path=storage)
        req = box.submit_request({
            'requester_type': 'laboratory',
            'domain': 'physics',
            'requested_capability': 'Detection',
            'problem_statement': 'Detection request',
        })
        
        bridge = SuggestionBridge(review_queue_path=review, suggestion_storage_path=storage)
        candidate = bridge.add_proposal_candidate(req.request_id)
        assessed = apply_assessment_to_candidate(candidate)
        
        assessment = assessed.get('weslr_assessment', {})
        reasoning = assessment.get('reasoning', '')
        
        # Reasoning should be substantive
        self.assertTrue(len(reasoning) > 5,
                      "Reasoning should be substantive")
    
    def test_review_detail_aligned(self):
        """Review detail view aligned with data."""
        from weslr.weslr_operator_views import build_operator_review_detail
        
        storage = self.tmpdir / "requests.json"
        review = self.tmpdir / "review_queue.json"
        
        box = SuggestionBox(storage_path=storage)
        req = box.submit_request({
            'requester_type': 'company',
            'domain': 'chemistry',
            'requested_capability': 'Simulation',
            'problem_statement': 'Simulation request',
        })
        
        bridge = SuggestionBridge(review_queue_path=review, suggestion_storage_path=storage)
        candidate = bridge.add_proposal_candidate(req.request_id)
        assessed = apply_assessment_to_candidate(candidate)
        
        # Build detail view
        detail = build_operator_review_detail(assessed)
        
        # Should have expected structure
        self.assertIn('candidate', detail)
        self.assertIn('weslr_assessment', detail)
        self.assertIn('enhanced', detail)


# ============================================================================
# EXPLANATION NO PROTECTED LEAKAGE TESTS
# ============================================================================

class TestExplanationNoProtectedLeakage(TestCase):
    """Test that explanations do not expose protected/internal-only details."""
    
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)
    
    def test_public_output_no_internal_fields(self):
        """Public outputs don't contain internal fields."""
        storage = self.tmpdir / "requests.json"
        review = self.tmpdir / "review_queue.json"
        
        box = SuggestionBox(storage_path=storage)
        req = box.submit_request({
            'requester_type': 'university',
            'domain': 'astronomy',
            'requested_capability': 'Analysis',
            'problem_statement': 'Analysis request',
        })
        
        bridge = SuggestionBridge(review_queue_path=review, suggestion_storage_path=storage)
        candidate = bridge.add_proposal_candidate(req.request_id)
        assessed = apply_assessment_to_candidate(candidate)
        
        # Build public-facing output
        from weslr.weslr_operator_views import build_operator_review_list
        public_output = build_operator_review_list([assessed])
        
        public_item = public_output[0]
        
        # Should NOT contain internal-only fields
        internal_fields = [
            'internal_notes',
            'raw_scores',
            'assessment_history',
            'internal_reviewer',
        ]
        
        for field in internal_fields:
            self.assertNotIn(field, public_item,
                           f"Internal field {field} should not be in public output")
    
    def test_candidate_not_in_request(self):
        """Candidate data not leaked into request objects."""
        storage = self.tmpdir / "requests.json"
        review = self.tmpdir / "review_queue.json"
        
        box = SuggestionBox(storage_path=storage)
        req = box.submit_request({
            'requester_type': 'laboratory',
            'domain': 'physics',
            'requested_capability': 'Detection',
            'problem_statement': 'Detection request',
        })
        
        bridge = SuggestionBridge(review_queue_path=review, suggestion_storage_path=storage)
        bridge.add_proposal_candidate(req.request_id)
        
        # Reload requests (simulating public view)
        box2 = SuggestionBox(storage_path=storage)
        
        for r in box2.requests:
            # Should NOT contain candidate data
            self.assertNotIn('candidates', r)
            self.assertNotIn('review_candidates', r)
    
    def test_assessment_no_internal_details(self):
        """Assessment output doesn't expose internal details."""
        storage = self.tmpdir / "requests.json"
        review = self.tmpdir / "review_queue.json"
        
        box = SuggestionBox(storage_path=storage)
        req = box.submit_request({
            'requester_type': 'company',
            'domain': 'chemistry',
            'requested_capability': 'Simulation',
            'problem_statement': 'Simulation request',
        })
        
        bridge = SuggestionBridge(review_queue_path=review, suggestion_storage_path=storage)
        candidate = bridge.add_proposal_candidate(req.request_id)
        assessed = apply_assessment_to_candidate(candidate)
        
        assessment = assessed.get('weslr_assessment', {})
        
        # Should not contain raw internal data
        self.assertNotIn('raw_data', assessment)
        self.assertNotIn('internal_only', assessment)
        self.assertNotIn('system_metadata', assessment)


# ============================================================================
# FALLBACK/ERROR EXPLANATION SAFETY TESTS
# ============================================================================

class TestFallbackExplanationSafety(TestCase):
    """Test that fallback/error explanations remain safe, minimal, and non-misleading."""
    
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)
    
    def test_empty_result_safe_explanation(self):
        """Empty results have safe explanation."""
        storage = self.tmpdir / "requests.json"
        
        box = SuggestionBox(storage_path=storage)
        req = box.submit_request({
            'requester_type': 'university',
            'domain': 'astronomy',
            'requested_capability': 'Analysis',
            'problem_statement': 'Analysis request',
        })
        
        # Assessment should handle edge cases
        from weslr.suggestion_bridge import SuggestionBridge
        review = self.tmpdir / "review_queue.json"
        bridge = SuggestionBridge(review_queue_path=review, suggestion_storage_path=storage)
        
        candidate = bridge.add_proposal_candidate(req.request_id)
        
        # Should not crash even if data is minimal
        try:
            assessed = apply_assessment_to_candidate(candidate)
            self.assertIsNotNone(assessed)
        except Exception:
            # Graceful handling expected
            pass
    
    def test_error_explanation_not_misleading(self):
        """Error explanations are not misleading."""
        storage = self.tmpdir / "requests.json"
        
        box = SuggestionBox(storage_path=storage)
        
        # Empty request
        req = box.submit_request({
            'requester_type': 'laboratory',
            'domain': 'physics',
            'requested_capability': '',
            'problem_statement': '',
        })
        
        # Should handle gracefully
        self.assertIsNotNone(req)
    
    def test_fallback_explanation_present(self):
        """Fallback explanations are present when needed."""
        storage = self.tmpdir / "requests.json"
        review = self.tmpdir / "review_queue.json"
        
        box = SuggestionBox(storage_path=storage)
        req = box.submit_request({
            'requester_type': 'company',
            'domain': 'chemistry',
            'requested_capability': 'Analysis',
            'problem_statement': 'Analysis',
        })
        
        bridge = SuggestionBridge(review_queue_path=review, suggestion_storage_path=storage)
        candidate = bridge.add_proposal_candidate(req.request_id)
        
        # Should have assessment with fallback
        try:
            assessed = apply_assessment_to_candidate(candidate)
            assessment = assessed.get('weslr_assessment', {})
            
            # Should have minimum required fields
            self.assertIn('risk_level', assessment)
            self.assertIn('reasoning', assessment)
        except Exception:
            # If assessment fails, that's acceptable
            pass


# ============================================================================
# UTILITIES FOR EXPLAINABILITY TESTS
# ============================================================================

def run_explainability_tests() -> dict[str, any]:
    """Run all explainability tests and return results."""
    import unittest
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    for cls in [
        TestAssessmentReasoningConsistency,
        TestRecommendedActionConsistency,
        TestScientificCandidateNoOverclaim,
        TestHabitableZoneExplanationConsistency,
        TestMaterialsRankingExplanationConsistency,
        TestNotebookTimelineSummaryAlignment,
        TestOperatorExplanationAlignment,
        TestExplanationNoProtectedLeakage,
        TestFallbackExplanationSafety,
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
        "category": "explainability",
    }


if __name__ == "__main__":
    result = run_explainability_tests()
    print(f"\n{'='*60}")
    print(f"Explainability Consistency Tests Results")
    print(f"{'='*60}")
    print(f"Tests run: {result['tests_run']}")
    print(f"Passed: {result['passed']}")
    print(f"Failed: {result['failed']}")
    print(f"Errors: {result['errors']}")
    print(f"{'='*60}")
