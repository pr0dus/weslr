#!/usr/bin/env python3
"""Tests for weslr/weslr_operator_views.py - Operator Review Enhancements validation."""

import json
import shutil
import sys
import tempfile
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from weslr.suggestion_box import SuggestionBox
from weslr.suggestion_bridge import SuggestionBridge
from weslr.suggestion_assessment import apply_assessment_to_candidate
from weslr.weslr_operator_views import (
    enhance_review_candidate_with_weslr_assessment,
    build_operator_review_detail,
    build_operator_review_list,
    format_assessment_for_display,
)


def get_storage_dirs():
    """Create temp storage dirs that are isolated per test run."""
    tmpdir = Path(tempfile.mkdtemp())
    storage = tmpdir / "requests.json"
    continuity = tmpdir / "continuity.json"
    review = tmpdir / "review_queue.json"
    return storage, continuity, review, tmpdir


def test_enhance_candidate_with_weslr_assessment():
    """Test: enhance candidate with Weslr assessment fields."""
    storage, continuity, review, tmpdir = get_storage_dirs()
    try:
        box = SuggestionBox(storage_path=storage, continuity_path=continuity)
        req = box.submit_request({
            'requester_type': 'university',
            'domain': 'astronomy',
            'requested_capability': 'FITS spectral comparison',
            'problem_statement': 'Need better candidate atmosphere analysis',
        })
        request_id = req.request_id

        bridge = SuggestionBridge(review_queue_path=review, suggestion_storage_path=storage)
        candidate = bridge.add_proposal_candidate(request_id)
        assessed = apply_assessment_to_candidate(candidate)

        enhanced = enhance_review_candidate_with_weslr_assessment(assessed)

        # Verify enhanced fields
        assert 'weslr_priority' in enhanced
        assert 'weslr_fit_score' in enhanced
        assert 'weslr_risk' in enhanced
        assert 'weslr_recommended_action' in enhanced
        assert 'weslr_reasoning' in enhanced
        assert 'weslr_status' in enhanced

        # Verify values
        a = assessed['weslr_assessment']
        assert enhanced['weslr_priority'] == a['priority']
        assert enhanced['weslr_fit_score'] == a['fit_score']
        assert enhanced['weslr_risk'] == a['implementation_risk']
        assert enhanced['weslr_recommended_action'] == a['recommended_action']
        assert a['reasoning'] in enhanced['weslr_reasoning']

        # Verify original candidate preserved
        assert 'source' in enhanced
        assert enhanced['source']['type'] == 'external_request'

        return True, None
    except Exception as e:
        return False, str(e)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_enhance_candidate_without_assessment():
    """Test: enhance candidate without assessment returns unchanged."""
    candidate = {
        'id': 'ext-test',
        'title': 'Test candidate',
        'review_status': 'proposed',
    }

    enhanced = enhance_review_candidate_with_weslr_assessment(candidate)

    # Should return original unchanged
    assert enhanced == candidate
    assert 'weslr_priority' not in enhanced

    return True, None


def test_build_operator_review_detail():
    """Test: build detailed operator review view."""
    storage, continuity, review, tmpdir = get_storage_dirs()
    try:
        box = SuggestionBox(storage_path=storage, continuity_path=continuity)
        req = box.submit_request({
            'requester_type': 'laboratory',
            'domain': 'physics',
            'requested_capability': 'Particle detector calibration',
            'problem_statement': 'Calibration for high-precision particle detection',
        })
        request_id = req.request_id

        bridge = SuggestionBridge(review_queue_path=review, suggestion_storage_path=storage)
        candidate = bridge.add_proposal_candidate(request_id)
        assessed = apply_assessment_to_candidate(candidate)

        detail = build_operator_review_detail(assessed)

        # Verify structure
        assert 'candidate' in detail
        assert 'weslr_assessment' in detail
        assert 'enhanced' in detail

        # Verify content
        assert detail['candidate']['id'] == assessed['id']
        assert detail['weslr_assessment']['priority'] == 'high'
        assert 'priority' in detail['enhanced']
        assert 'fit_score' in detail['enhanced']
        assert 'risk' in detail['enhanced']
        assert 'recommended_action' in detail['enhanced']
        assert 'reasoning' in detail['enhanced']
        assert 'status' in detail['enhanced']

        return True, None
    except Exception as e:
        return False, str(e)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_build_operator_review_list():
    """Test: build list view for operator review."""
    storage, continuity, review, tmpdir = get_storage_dirs()
    try:
        box = SuggestionBox(storage_path=storage, continuity_path=continuity)
        req1 = box.submit_request({
            'requester_type': 'company',
            'domain': 'chemistry',
            'requested_capability': 'cap1',
            'problem_statement': 'prob1',
        })
        req2 = box.submit_request({
            'requester_type': 'institution',
            'domain': 'biology',
            'requested_capability': 'cap2',
            'problem_statement': 'prob2',
        })

        bridge = SuggestionBridge(review_queue_path=review, suggestion_storage_path=storage)
        c1 = bridge.add_proposal_candidate(req1.request_id)
        c2 = bridge.add_proposal_candidate(req2.request_id)

        c1_assessed = apply_assessment_to_candidate(c1)
        c2_assessed = apply_assessment_to_candidate(c2)

        list_view = build_operator_review_list([c1_assessed, c2_assessed])

        assert len(list_view) == 2
        assert 'weslr_priority' in list_view[0]
        assert 'weslr_priority' in list_view[1]

        return True, None
    except Exception as e:
        return False, str(e)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_format_assessment_for_display():
    """Test: format assessment for human-readable display."""
    storage, continuity, review, tmpdir = get_storage_dirs()
    try:
        box = SuggestionBox(storage_path=storage, continuity_path=continuity)
        req = box.submit_request({
            'requester_type': 'individual',
            'domain': 'astronomy',
            'requested_capability': 'Telescope scheduling',
            'problem_statement': 'Schedule multiple telescopes',
        })
        request_id = req.request_id

        bridge = SuggestionBridge(review_queue_path=review, suggestion_storage_path=storage)
        candidate = bridge.add_proposal_candidate(request_id)
        assessed = apply_assessment_to_candidate(candidate)

        formatted = format_assessment_for_display(assessed)

        # Verify format contains expected sections
        assert 'WESLR ASSESSMENT' in formatted
        assert 'Priority:' in formatted
        assert 'Fit Score:' in formatted
        assert 'Implementation Risk:' in formatted
        assert 'Recommended Action:' in formatted
        assert 'Reasoning:' in formatted

        return True, None
    except Exception as e:
        return False, str(e)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_internal_only_visibility():
    """Test: Weslr assessment is internal-only (not in public-facing output)."""
    storage, continuity, review, tmpdir = get_storage_dirs()
    try:
        box = SuggestionBox(storage_path=storage, continuity_path=continuity)
        req = box.submit_request({
            'requester_type': 'university',
            'domain': 'astronomy',
            'requested_capability': 'FITS spectral comparison',
            'problem_statement': 'Need better candidate atmosphere analysis',
        })
        request_id = req.request_id

        bridge = SuggestionBridge(review_queue_path=review, suggestion_storage_path=storage)
        candidate = bridge.add_proposal_candidate(request_id)
        assessed = apply_assessment_to_candidate(candidate)

        # Get enhanced view
        enhanced = enhance_review_candidate_with_weslr_assessment(assessed)

        # Verify Weslr-specific fields exist
        assert 'weslr_priority' in enhanced

        # Verify source tracking preserved (internal operator visibility)
        assert enhanced['source']['type'] == 'external_request'
        assert enhanced['source']['subtype'] == 'weslr_suggestion'

        return True, None
    except Exception as e:
        return False, str(e)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_no_autonomous_action():
    """Test: assessment does NOT enable autonomous action."""
    storage, continuity, review, tmpdir = get_storage_dirs()
    try:
        box = SuggestionBox(storage_path=storage, continuity_path=continuity)
        req = box.submit_request({
            'requester_type': 'laboratory',
            'domain': 'physics',
            'requested_capability': 'cap',
            'problem_statement': 'prob',
        })
        request_id = req.request_id

        bridge = SuggestionBridge(review_queue_path=review, suggestion_storage_path=storage)
        candidate = bridge.add_proposal_candidate(request_id)
        assessed = apply_assessment_to_candidate(candidate)
        enhanced = enhance_review_candidate_with_weslr_assessment(assessed)

        # Verify review_status is still "proposed" (not auto-approved)
        assert enhanced['review_status'] == 'proposed'

        # Verify approved_for_export is False (protected)
        assert enhanced['approved_for_export'] == False

        # Verify public_visibility is internal
        assert enhanced['public_visibility'] == 'internal'

        return True, None
    except Exception as e:
        return False, str(e)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_continuity_compatibility():
    """Test: enhancement is compatible with continuity storage."""
    storage, continuity, review, tmpdir = get_storage_dirs()
    try:
        box = SuggestionBox(storage_path=storage, continuity_path=continuity)
        req = box.submit_request({
            'requester_type': 'institution',
            'domain': 'engineering',
            'requested_capability': 'System architecture optimization',
            'problem_statement': 'Optimize system architecture for better performance',
        })
        request_id = req.request_id

        bridge = SuggestionBridge(review_queue_path=review, suggestion_storage_path=storage)
        candidate = bridge.add_proposal_candidate(request_id)
        assessed = apply_assessment_to_candidate(candidate)

        # Test JSON serialization (continuity storage)
        json_str = json.dumps(assessed)
        loaded = json.loads(json_str)

        # Verify assessment data round-trips
        assert 'weslr_assessment' in loaded
        assert loaded['weslr_assessment']['fit_score'] is not None
        assert loaded['weslr_assessment']['reasoning'] is not None

        return True, None
    except Exception as e:
        return False, str(e)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == '__main__':
    tests = [
        ('enhance candidate with Weslr assessment', test_enhance_candidate_with_weslr_assessment),
        ('enhance candidate without assessment', test_enhance_candidate_without_assessment),
        ('build operator review detail', test_build_operator_review_detail),
        ('build operator review list', test_build_operator_review_list),
        ('format assessment for display', test_format_assessment_for_display),
        ('internal-only visibility', test_internal_only_visibility),
        ('no autonomous action', test_no_autonomous_action),
        ('continuity compatibility', test_continuity_compatibility),
    ]

    print('=== Weslr Operator Views Validation ===')
    print()

    passed = []
    failed = []

    for name, test_fn in tests:
        success, error = test_fn()
        if success:
            passed.append(name)
            print(f'  ✓ {name}')
        else:
            failed.append((name, error))
            print(f'  ✗ {name}: {error}')

    print()
    print('=== VALIDATION RESULTS ===')
    total = len(passed) + len(failed)
    print(f'PASSED: {len(passed)}/{total}')

    if not failed:
        print()
        print('All scenarios passed!')
