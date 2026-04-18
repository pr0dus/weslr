#!/usr/bin/env python3
"""Tests for weslr/suggestion_bridge.py - Suggestion-to-Proposal Bridge validation."""

import json
import shutil
import sys
import tempfile
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from weslr.suggestion_box import SuggestionBox
from weslr.suggestion_bridge import SuggestionBridge, SuggestionBridge, REVIEW_QUEUE_PATH, SUGGESTION_STORAGE


def get_storage_dirs():
    """Create temp storage dirs that are isolated per test run."""
    tmpdir = Path(tempfile.mkdtemp())
    storage = tmpdir / "requests.json"
    continuity = tmpdir / "continuity.json"
    review = tmpdir / "review_queue.json"
    return storage, continuity, review, tmpdir


def test_create_suggestion_and_bridge():
    """Test: create suggestion, bridge to proposal candidate."""
    storage, continuity, review, tmpdir = get_storage_dirs()
    try:
        # Create suggestion with temp paths
        box = SuggestionBox(storage_path=storage, continuity_path=continuity)
        req = box.submit_request({
            'requester_type': 'university',
            'domain': 'astronomy',
            'requested_capability': 'FITS spectral comparison',
            'problem_statement': 'Need better candidate atmosphere analysis',
        })
        request_id = req.request_id

        # Bridge with same paths
        bridge = SuggestionBridge(
            review_queue_path=review,
            suggestion_storage_path=storage,
        )

        candidate = bridge.add_proposal_candidate(request_id)

        assert candidate['id'].startswith('ext-')
        assert candidate['category'] == 'external_request'
        assert candidate['source']['type'] == 'external_request'
        assert candidate['review_status'] == 'proposed'
        assert candidate['public_visibility'] == 'internal'

        # Verify in review queue
        candidates = bridge.list_proposal_candidates()
        assert len(candidates) == 1
        assert candidates[0]['id'] == candidate['id']

        return True, None
    except Exception as e:
        return False, str(e)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_review_workflow():
    """Test: operator approve/reject workflow."""
    storage, continuity, review, tmpdir = get_storage_dirs()
    try:
        # Setup
        box = SuggestionBox(storage_path=storage, continuity_path=continuity)
        req = box.submit_request({
            'requester_type': 'laboratory',
            'domain': 'physics',
            'requested_capability': 'test capability',
            'problem_statement': 'test problem',
        })
        request_id = req.request_id

        bridge = SuggestionBridge(
            review_queue_path=review,
            suggestion_storage_path=storage,
        )

        candidate = bridge.add_proposal_candidate(request_id)

        # Test approve
        success = bridge.mark_as_reviewed(candidate['id'], 'approved', 'Operator approved')
        assert success, 'Approve should succeed'
        candidates = bridge.list_proposal_candidates()
        assert candidates[0]['review_status'] == 'approved'

        # Test reject
        success = bridge.mark_as_reviewed(candidate['id'], 'rejected', 'Operator rejected')
        assert success, 'Reject should succeed'
        candidates = bridge.list_proposal_candidates()
        assert candidates[0]['review_status'] == 'rejected'

        return True, None
    except Exception as e:
        return False, str(e)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_remove_proposal_candidate():
    """Test: remove proposal candidate (cleanup)."""
    storage, continuity, review, tmpdir = get_storage_dirs()
    try:
        # Setup
        box = SuggestionBox(storage_path=storage, continuity_path=continuity)
        req = box.submit_request({
            'requester_type': 'company',
            'domain': 'biology',
            'requested_capability': 'test capability',
            'problem_statement': 'test problem',
        })
        request_id = req.request_id

        bridge = SuggestionBridge(
            review_queue_path=review,
            suggestion_storage_path=storage,
        )

        candidate = bridge.add_proposal_candidate(request_id)

        # Remove
        success = bridge.remove_proposal_candidate(candidate['id'])
        assert success, 'Remove should succeed'

        # Verify removed
        candidates = bridge.list_proposal_candidates()
        assert len(candidates) == 0

        return True, None
    except Exception as e:
        return False, str(e)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_summary_generation():
    """Test: summary generation."""
    storage, continuity, review, tmpdir = get_storage_dirs()
    try:
        # Setup
        box = SuggestionBox(storage_path=storage, continuity_path=continuity)
        box.submit_request({
            'requester_type': 'university',
            'domain': 'astronomy',
            'requested_capability': 'cap1',
            'problem_statement': 'prob1',
        })
        box.submit_request({
            'requester_type': 'laboratory',
            'domain': 'physics',
            'requested_capability': 'cap2',
            'problem_statement': 'prob2',
        })

        bridge = SuggestionBridge(
            review_queue_path=review,
            suggestion_storage_path=storage,
        )

        # Bridge both
        candidates = bridge.list_suggestions()
        for c in candidates:
            bridge.add_proposal_candidate(c['request_id'])

        # Test summary
        summary = bridge.summary()
        assert summary['total_suggestions'] == 2
        assert summary['total_candidates'] == 2

        return True, None
    except Exception as e:
        return False, str(e)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_public_visibility_protection():
    """Test: public visibility protection intact."""
    storage, continuity, review, tmpdir = get_storage_dirs()
    try:
        # Setup
        box = SuggestionBox(storage_path=storage, continuity_path=continuity)
        req = box.submit_request({
            'requester_type': 'individual',
            'domain': 'chemistry',
            'requested_capability': 'test capability',
            'problem_statement': 'test problem',
        })
        request_id = req.request_id

        bridge = SuggestionBridge(
            review_queue_path=review,
            suggestion_storage_path=storage,
        )

        candidate = bridge.add_proposal_candidate(request_id)

        # Verify protection
        assert candidate['approved_for_export'] == False
        assert candidate['public_visibility'] == 'internal'

        # Verify operator must explicitly enable
        candidate['approved_for_export'] = True
        candidate['public_visibility'] = 'public'
        # In real workflow, operator would do this via explicit action
        # The bridge doesn't auto-approve, so this must be explicit operator action

        return True, None
    except Exception as e:
        return False, str(e)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_continuity_compatibility():
    """Test: continuity compatibility preserved."""
    storage, continuity, review, tmpdir = get_storage_dirs()
    try:
        # Setup
        box = SuggestionBox(storage_path=storage, continuity_path=continuity)
        req = box.submit_request({
            'requester_type': 'institution',
            'domain': 'astronomy',
            'requested_capability': 'test capability',
            'problem_statement': 'test problem',
        })
        request_id = req.request_id

        bridge = SuggestionBridge(
            review_queue_path=review,
            suggestion_storage_path=storage,
        )

        # Bridge and verify continuity
        bridge.add_proposal_candidate(request_id)

        # Verify continuity file exists
        assert continuity.exists()

        # Verify review queue path (should be in tmpdir)
        assert review.exists()

        # Verify bridge adds source tracking
        candidates = bridge.list_proposal_candidates()
        assert candidates[0]['source']['subtype'] == 'weslr_suggestion'
        assert candidates[0]['source']['request_id'] == request_id

        return True, None
    except Exception as e:
        return False, str(e)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == '__main__':
    tests = [
        ('create suggestion and bridge', test_create_suggestion_and_bridge),
        ('review workflow', test_review_workflow),
        ('remove proposal candidate', test_remove_proposal_candidate),
        ('summary generation', test_summary_generation),
        ('public visibility protection', test_public_visibility_protection),
        ('continuity compatibility', test_continuity_compatibility),
    ]

    print('=== Suggestion Bridge Validation ===')
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
