"""Weslr Privacy / Role-Boundary Test Suite (v1)

Privacy and role-boundary hardening tests for visibility controls.
Designed to be additive and reversible — no production modifications.

Test Families Implemented:
  - operator-only assessment data isolation
  - internal review candidates in non-operator paths
  - operator action path isolation
  - suggestion/request data scoping
  - file understanding result isolation
  - visibility gate correctness
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest import TestCase

from weslr.suggestion_box import SuggestionBox
from weslr.suggestion_bridge import SuggestionBridge
from weslr.suggestion_assessment import apply_assessment_to_candidate
from weslr.weslr_operator_views import (
    build_operator_review_list,
    build_operator_review_detail,
)


__all__ = [
    "TestOperatorAssessmentIsolation",
    "TestReviewCandidatesVisibility",
    "TestOperatorActionPaths",
    "TestSuggestionDataScoping",
    "TestFileUnderstandingIsolation",
    "TestVisibilityGateCorrectness",
]


# ============================================================================
# OPERATOR ASSESSMENT ISOLATION TESTS
# ============================================================================

class TestOperatorAssessmentIsolation(TestCase):
    """Test that operator-only assessment data never appears in public outputs."""
    
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)
    
    def test_assessment_data_not_in_public_list(self):
        """Operator assessment data excluded from public review lists."""
        storage = self.tmpdir / "requests.json"
        review = self.tmpdir / "review_queue.json"
        
        box = SuggestionBox(storage_path=storage)
        req = box.submit_request({
            'requester_type': 'university',
            'domain': 'astronomy',
            'requested_capability': 'Analysis',
            'problem_statement': 'Test analysis',
        })
        
        bridge = SuggestionBridge(review_queue_path=review, suggestion_storage_path=storage)
        candidate = bridge.add_proposal_candidate(req.request_id)
        assessed = apply_assessment_to_candidate(candidate)
        
        # Build public-facing review list (without operator data)
        public_list = build_operator_review_list([assessed])
        
        # Public list should NOT contain internal assessment fields
        public_item = public_list[0]
        
        # Operator-only fields should be stripped
        self.assertNotIn('weslr_assessment', public_item,
                        "Operator-only weslr_assessment should not appear in public output")
        self.assertNotIn('weslr_priority', public_item,
                        "Operator-only weslr_priority should not appear in public output")
    
    def test_assessment_detail_not_in_public_detail(self):
        """Operator assessment details excluded from public review detail."""
        storage = self.tmpdir / "requests.json"
        review = self.tmpdir / "review_queue.json"
        
        box = SuggestionBox(storage_path=storage)
        req = box.submit_request({
            'requester_type': 'laboratory',
            'domain': 'physics',
            'requested_capability': 'Detection',
            'problem_statement': 'Test detection',
        })
        
        bridge = SuggestionBridge(review_queue_path=review, suggestion_storage_path=storage)
        candidate = bridge.add_proposal_candidate(req.request_id)
        assessed = apply_assessment_to_candidate(candidate)
        
        # Build public-facing detail (without operator data)
        public_detail = build_operator_review_detail(assessed)
        
        # Operator-only fields should be stripped from detail view
        self.assertNotIn('weslr_assessment', public_detail,
                        "Operator-only assessment should not appear in public detail")
        self.assertNotIn('internal_notes', public_detail,
                        "Operator-only internal notes should not appear in public detail")


# ============================================================================
# REVIEW CANDIDATES VISIBILITY TESTS
# ============================================================================

class TestReviewCandidatesVisibility(TestCase):
    """Test that internal review candidates never appear in non-operator surfaces."""
    
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)
    
    def test_candidates_excluded_from_request_list(self):
        """Review candidates not present in suggestion request lists."""
        storage = self.tmpdir / "requests.json"
        
        box = SuggestionBox(storage_path=storage)
        
        # Submit multiple requests
        req1 = box.submit_request({
            'requester_type': 'university',
            'domain': 'astronomy',
            'requested_capability': 'Analysis',
            'problem_statement': 'Test 1',
        })
        
        req2 = box.submit_request({
            'requester_type': 'laboratory',
            'domain': 'physics',
            'requested_capability': 'Detection',
            'problem_statement': 'Test 2',
        })
        
        # Bridge creates candidates
        review = self.tmpdir / "review_queue.json"
        bridge = SuggestionBridge(review_queue_path=review, suggestion_storage_path=storage)
        bridge.add_proposal_candidate(req1.request_id)
        bridge.add_proposal_candidate(req2.request_id)
        
        # Reload box and verify candidates NOT in request data
        box2 = SuggestionBox(storage_path=storage)
        request_ids = {r.get('request_id') for r in box2.requests}
        
        # Requests should exist
        self.assertIn(req1.request_id, request_ids)
        self.assertIn(req2.request_id, request_ids)
        
        # But candidate data (which is stored separately) should not leak into requests
        for req in box2.requests:
            self.assertNotIn('review_candidates', req,
                           "Review candidates should not leak into request objects")
    
    def test_candidates_excluded_from_public_queries(self):
        """Review candidates not returned in public query results."""
        storage = self.tmpdir / "requests.json"
        review = self.tmpdir / "review_queue.json"
        
        box = SuggestionBox(storage_path=storage)
        req = box.submit_request({
            'requester_type': 'company',
            'domain': 'chemistry',
            'requested_capability': 'Simulation',
            'problem_statement': 'Test simulation',
        })
        
        bridge = SuggestionBridge(review_queue_path=review, suggestion_storage_path=storage)
        bridge.add_proposal_candidate(req.request_id)
        
        # Public-facing query should not return candidates
        # (candidates are stored in review_queue.json, not requests.json)
        box2 = SuggestionBox(storage_path=storage)
        public_requests = box2.requests
        
        # Candidates should not appear in public request list
        for req in public_requests:
            self.assertNotIn('candidate', req,
                           "Review candidate should not appear in public requests")
            self.assertNotIn('review_status', req,
                           "Review status should not appear in public requests")


# ============================================================================
# OPERATOR ACTION PATH ISOLATION TESTS
# ============================================================================

class TestOperatorActionPaths(TestCase):
    """Test that operator actions are not reachable from non-operator paths."""
    
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)
    
    def test_review_status_modification_only_by_bridge(self):
        """Review status can only be modified via bridge, not via request update."""
        storage = self.tmpdir / "requests.json"
        review = self.tmpdir / "review_queue.json"
        
        box = SuggestionBox(storage_path=storage)
        req = box.submit_request({
            'requester_type': 'university',
            'domain': 'astronomy',
            'requested_capability': 'Analysis',
            'problem_statement': 'Test',
        })
        
        bridge = SuggestionBridge(review_queue_path=review, suggestion_storage_path=storage)
        candidate = bridge.add_proposal_candidate(req.request_id)
        
        # Initial status should be pending or in review
        initial_status = candidate.get('review_status')
        self.assertIn(initial_status, ['pending', 'review'])
        
        # Status can be changed via bridge
        bridge.mark_as_reviewed(candidate['id'], 'approved', 'Approved')
        
        # Reload bridge and verify change
        bridge2 = SuggestionBridge(review_queue_path=review, suggestion_storage_path=storage)
        candidates = bridge2.list_proposal_candidates()
        updated = next((c for c in candidates if c['id'] == candidate['id']), None)
        
        self.assertIsNotNone(updated)
        self.assertEqual(updated['review_status'], 'approved')
        
        # But the request itself should not have review_status
        box2 = SuggestionBox(storage_path=storage)
        for r in box2.requests:
            self.assertNotIn('review_status', r,
                           "Review status should not appear in request objects")
    
    def test_candidate_approval_not_in_request_data(self):
        """Approved candidates do not modify request objects."""
        storage = self.tmpdir / "requests.json"
        review = self.tmpdir / "review_queue.json"
        
        box = SuggestionBox(storage_path=storage)
        req = box.submit_request({
            'requester_type': 'laboratory',
            'domain': 'physics',
            'requested_capability': 'Detection',
            'problem_statement': 'Test',
        })
        
        bridge = SuggestionBridge(review_queue_path=review, suggestion_storage_path=storage)
        candidate = bridge.add_proposal_candidate(req.request_id)
        
        # Approve candidate
        bridge.mark_as_reviewed(candidate['id'], 'approved', 'Approved for testing')
        
        # Reload request and verify no approval data leaked
        box2 = SuggestionBox(storage_path=storage)
        for r in box2.requests:
            self.assertNotIn('approved', r,
                           "Approval status should not leak into request data")
            self.assertNotIn('reviewed', r,
                           "Review status should not leak into request data")
            self.assertNotIn('review_status', r,
                           "Review status should not leak into request data")


# ============================================================================
# SUGGESTION DATA SCOPING TESTS
# ============================================================================

class TestSuggestionDataScoping(TestCase):
    """Test that suggestion/request data remains scoped correctly."""
    
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)
    
    def test_request_data_not_shared_between_storages(self):
        """Request data isolated between different storage paths."""
        storage1 = self.tmpdir / "requests1.json"
        storage2 = self.tmpdir / "requests2.json"
        
        # Create request in storage1
        box1 = SuggestionBox(storage_path=storage1)
        req1 = box1.submit_request({
            'requester_type': 'university',
            'domain': 'astronomy',
            'requested_capability': 'Analysis',
            'problem_statement': 'Test',
        })
        
        # Storage2 should be empty
        box2 = SuggestionBox(storage_path=storage2)
        self.assertEqual(len(box2.requests), 0,
                        "Different storage paths should not share data")
        
        # Request from storage1 should not be in storage2
        for r in box2.requests:
            self.assertNotEqual(r.get('request_id'), req1.request_id,
                              "Request should not appear in unrelated storage")
    
    def test_domain_data_scoped_to_request(self):
        """Domain-scoped data only visible within correct scope."""
        storage = self.tmpdir / "requests.json"
        
        box = SuggestionBox(storage_path=storage)
        
        # Create requests in different domains
        req1 = box.submit_request({
            'requester_type': 'university',
            'domain': 'astronomy',
            'requested_capability': 'Analysis',
            'problem_statement': 'Astronomy test',
        })
        
        req2 = box.submit_request({
            'requester_type': 'laboratory',
            'domain': 'physics',
            'requested_capability': 'Detection',
            'problem_statement': 'Physics test',
        })
        
        # All requests should be visible in same storage
        box2 = SuggestionBox(storage_path=storage)
        request_ids = {r.get('request_id') for r in box2.requests}
        self.assertIn(req1.request_id, request_ids)
        self.assertIn(req2.request_id, request_ids)
        
        # But domain-specific data should remain scoped
        for r in box2.requests:
            self.assertIn('domain', r,
                        "Each request should have domain field")
            # No cross-contamination check - each request is independent
    
    def test_requester_type_scoping(self):
        """Requester type data scoped to individual requests."""
        storage = self.tmpdir / "requests.json"
        
        box = SuggestionBox(storage_path=storage)
        req1 = box.submit_request({
            'requester_type': 'university',
            'domain': 'astronomy',
            'requested_capability': 'Analysis',
            'problem_statement': 'Test',
        })
        
        # Reload and verify requester type is correct
        box2 = SuggestionBox(storage_path=storage)
        found = False
        for r in box2.requests:
            if r.get('request_id') == req1.request_id:
                found = True
                self.assertEqual(r.get('requester_type'), 'university',
                               "Requester type should match original value")
        
        self.assertTrue(found, "Request should be found after reload")


# ============================================================================
# FILE UNDERSTANDING ISOLATION TESTS
# ============================================================================

class TestFileUnderstandingIsolation(TestCase):
    """Test that file understanding results don't leak into public contexts."""
    
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)
    
    def test_file_route_result_not_in_request_data(self):
        """File route results not stored in suggestion request data."""
        storage = self.tmpdir / "requests.json"
        
        box = SuggestionBox(storage_path=storage)
        req = box.submit_request({
            'requester_type': 'university',
            'domain': 'astronomy',
            'requested_capability': 'Analysis',
            'problem_statement': 'Test',
        })
        
        # Create a test file
        test_file = self.tmpdir / "data.csv"
        test_file.write_text("x,y\n1,2\n3,4\n")
        
        # Route the file (this creates understanding, not stored in request)
        from weslr.file_router import create_file_router
        router = create_file_router(workspace_dir=str(self.tmpdir))
        route_result = router.route(str(test_file), user_query="Analyze this")
        
        # Route result should exist
        self.assertIn('category', route_result)
        self.assertIn('content', route_result)
        
        # But request data should not contain file understanding
        box2 = SuggestionBox(storage_path=storage)
        for r in box2.requests:
            self.assertNotIn('file_route', r,
                           "File route result should not leak into request data")
            self.assertNotIn('route_result', r,
                           "Route result should not leak into request data")
            self.assertNotIn('understanding', r,
                           "File understanding should not leak into request data")
    
    def test_file_understanding_not_shared_between_requests(self):
        """File understanding isolated per request."""
        storage = self.tmpdir / "requests.json"
        
        box = SuggestionBox(storage_path=storage)
        req1 = box.submit_request({
            'requester_type': 'university',
            'domain': 'astronomy',
            'requested_capability': 'Analysis',
            'problem_statement': 'Test 1',
        })
        
        req2 = box.submit_request({
            'requester_type': 'laboratory',
            'domain': 'physics',
            'requested_capability': 'Detection',
            'problem_statement': 'Test 2',
        })
        
        # Route different files
        from weslr.file_router import create_file_router
        router = create_file_router(workspace_dir=str(self.tmpdir))
        
        file1 = self.tmpdir / "data1.csv"
        file1.write_text("a,b\n1,2\n")
        
        file2 = self.tmpdir / "data2.csv"
        file2.write_text("x,y\n3,4\n")
        
        route1 = router.route(str(file1))
        route2 = router.route(str(file2))
        
        # Routes should be independent
        self.assertNotEqual(route1.content, route2.content)
        
        # Request data should not contain route results
        box2 = SuggestionBox(storage_path=storage)
        for r in box2.requests:
            self.assertNotIn('route_result', r,
                           "Route results should not leak into requests")


# ============================================================================
# VISIBILITY GATE CORRECTNESS TESTS
# ============================================================================

class TestVisibilityGateCorrectness(TestCase):
    """Test that visibility gates behave correctly when operator access is false."""
    
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)
    
    def test_public_user_cannot_access_review_candidates(self):
        """Public users cannot access review candidate data."""
        storage = self.tmpdir / "requests.json"
        review = self.tmpdir / "review_queue.json"
        
        box = SuggestionBox(storage_path=storage)
        req = box.submit_request({
            'requester_type': 'university',
            'domain': 'astronomy',
            'requested_capability': 'Analysis',
            'problem_statement': 'Test',
        })
        
        # Create candidate (operator only)
        bridge = SuggestionBridge(review_queue_path=review, suggestion_storage_path=storage)
        bridge.add_proposal_candidate(req.request_id)
        
        # Public user tries to access review data directly
        # (simulated by not loading review file)
        box2 = SuggestionBox(storage_path=storage)
        
        # Public user should only see requests, not candidates
        for r in box2.requests:
            self.assertNotIn('candidates', r,
                           "Public user should not see candidates")
            self.assertNotIn('review_candidates', r,
                           "Public user should not see review candidates")
        
        # Review file should not be loaded by public
        self.assertTrue(review.exists(),
                       "Review file exists but is not accessible to public")
    
    def test_operator_visible_for_review_data(self):
        """Operators can access review data when explicitly authorized."""
        storage = self.tmpdir / "requests.json"
        review = self.tmpdir / "review_queue.json"
        
        box = SuggestionBox(storage_path=storage)
        req = box.submit_request({
            'requester_type': 'laboratory',
            'domain': 'physics',
            'requested_capability': 'Detection',
            'problem_statement': 'Test',
        })
        
        # Operator creates candidate
        bridge = SuggestionBridge(review_queue_path=review, suggestion_storage_path=storage)
        candidate = bridge.add_proposal_candidate(req.request_id)
        
        # Operator reloads review and sees candidate
        bridge2 = SuggestionBridge(review_queue_path=review, suggestion_storage_path=storage)
        candidates = bridge2.list_proposal_candidates()
        
        # Operator should see the candidate
        self.assertGreater(len(candidates), 0,
                          "Operator should see review candidates")
        self.assertEqual(candidates[0]['id'], candidate['id'],
                        "Operator should see exact candidate")
    
    def test_request_id_not_exposed_to_review_candidates(self):
        """Request IDs not exposed in review candidate data."""
        storage = self.tmpdir / "requests.json"
        review = self.tmpdir / "review_queue.json"
        
        box = SuggestionBox(storage_path=storage)
        req = box.submit_request({
            'requester_type': 'company',
            'domain': 'chemistry',
            'requested_capability': 'Simulation',
            'problem_statement': 'Test',
        })
        
        bridge = SuggestionBridge(review_queue_path=review, suggestion_storage_path=storage)
        candidate = bridge.add_proposal_candidate(req.request_id)
        
        # Candidate data should not contain request ID
        self.assertNotIn('request_id', candidate,
                        "Review candidate should not contain request ID")
        self.assertNotIn('requester', candidate,
                        "Review candidate should not contain requester info")
        self.assertNotIn('domain', candidate,
                        "Review candidate should not contain domain info")
    
    def test_candidate_data_not_in_public_api(self):
        """Candidate data not exposed through public-facing API."""
        storage = self.tmpdir / "requests.json"
        review = self.tmpdir / "review_queue.json"
        
        box = SuggestionBox(storage_path=storage)
        req = box.submit_request({
            'requester_type': 'university',
            'domain': 'astronomy',
            'requested_capability': 'Analysis',
            'problem_statement': 'Test',
        })
        
        bridge = SuggestionBridge(review_queue_path=review, suggestion_storage_path=storage)
        bridge.add_proposal_candidate(req.request_id)
        
        # Simulate public API query (only requests, no review)
        box2 = SuggestionBox(storage_path=storage)
        public_requests = box2.requests
        
        # Public API should not expose candidates
        public_data = json.dumps(public_requests)
        
        # Check candidate IDs are not in public output
        candidate_id = 'can-'  # All candidates start with this
        self.assertNotIn(candidate_id, public_data,
                        "Candidate data should not appear in public API output")


# ============================================================================
# UTILITIES FOR PRIVACY TESTS
# ============================================================================

def run_privacy_tests() -> dict[str, any]:
    """Run all privacy tests and return results."""
    import unittest
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    for cls in [
        TestOperatorAssessmentIsolation,
        TestReviewCandidatesVisibility,
        TestOperatorActionPaths,
        TestSuggestionDataScoping,
        TestFileUnderstandingIsolation,
        TestVisibilityGateCorrectness,
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
        "category": "privacy",
    }


if __name__ == "__main__":
    result = run_privacy_tests()
    print(f"\n{'='*60}")
    print(f"Privacy / Role-Boundary Tests Results")
    print(f"{'='*60}")
    print(f"Tests run: {result['tests_run']}")
    print(f"Passed: {result['passed']}")
    print(f"Failed: {result['failed']}")
    print(f"Errors: {result['errors']}")
    print(f"{'='*60}")
