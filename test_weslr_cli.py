#!/usr/bin/env python3
"""Test the weslr CLI commands."""

import sys
import shutil
import tempfile
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from weslr.suggestion_box import SuggestionBox
from weslr.suggestion_bridge import SuggestionBridge
from weslr.suggestion_assessment import apply_assessment_to_candidate
from weslr.weslr_operator_views import build_operator_review_list


def get_storage_dirs():
    """Create temp storage dirs that are isolated per test run."""
    tmpdir = Path(tempfile.mkdtemp())
    storage = tmpdir / "requests.json"
    continuity = tmpdir / "continuity.json"
    review = tmpdir / "review_queue.json"
    return storage, continuity, review, tmpdir


def test_weslr_list():
    """Test: weslr list command functionality."""
    storage, continuity, review, tmpdir = get_storage_dirs()
    try:
        # Create some suggestions
        box = SuggestionBox(storage_path=storage, continuity_path=continuity)
        req1 = box.submit_request({
            'requester_type': 'university',
            'domain': 'astronomy',
            'requested_capability': 'FITS spectral comparison',
            'problem_statement': 'Need better candidate atmosphere analysis',
        })
        req2 = box.submit_request({
            'requester_type': 'laboratory',
            'domain': 'physics',
            'requested_capability': 'Particle detector calibration',
            'problem_statement': 'Calibration for high-precision particle detection',
        })

        # Bridge to candidates
        bridge = SuggestionBridge(review_queue_path=review, suggestion_storage_path=storage)
        c1 = bridge.add_proposal_candidate(req1.request_id)
        c2 = bridge.add_proposal_candidate(req2.request_id)

        # Apply assessment
        c1_assessed = apply_assessment_to_candidate(c1)
        c2_assessed = apply_assessment_to_candidate(c2)

        # Build list view (simulates what weslr list does)
        enhanced = build_operator_review_list([c1_assessed, c2_assessed])

        print(f"Total candidates: {len(enhanced)}")
        for c in enhanced:
            print(f"  - {c['id']}: {c.get('weslr_status', 'N/A')}")
            if 'weslr_fit_score' in c:
                print(f"      Fit: {c['weslr_fit_score']}")

        assert len(enhanced) == 2
        assert 'weslr_priority' in enhanced[0]
        assert 'weslr_fit_score' in enhanced[0]

        return True, None
    except Exception as e:
        return False, str(e)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_weslr_detail():
    """Test: weslr detail command functionality."""
    storage, continuity, review, tmpdir = get_storage_dirs()
    try:
        box = SuggestionBox(storage_path=storage, continuity_path=continuity)
        req = box.submit_request({
            'requester_type': 'company',
            'domain': 'chemistry',
            'requested_capability': 'Molecular dynamics simulation',
            'problem_statement': 'Simulating protein folding for drug discovery',
        })

        bridge = SuggestionBridge(review_queue_path=review, suggestion_storage_path=storage)
        candidate = bridge.add_proposal_candidate(req.request_id)
        assessed = apply_assessment_to_candidate(candidate)

        # Build detail view
        from weslr.weslr_operator_views import build_operator_review_detail
        detail = build_operator_review_detail(assessed)

        print(f"Detail available: {detail is not None}")
        print(f"  Candidate ID: {detail['candidate']['id']}")
        print(f"  Assessment priority: {detail['weslr_assessment']['priority']}")
        print(f"  Enhanced fit_score: {detail['enhanced']['fit_score']}")

        assert detail is not None
        assert 'candidate' in detail
        assert 'weslr_assessment' in detail
        assert 'enhanced' in detail

        return True, None
    except Exception as e:
        return False, str(e)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_weslr_format():
    """Test: weslr format command functionality."""
    storage, continuity, review, tmpdir = get_storage_dirs()
    try:
        box = SuggestionBox(storage_path=storage, continuity_path=continuity)
        req = box.submit_request({
            'requester_type': 'institution',
            'domain': 'astronomy',
            'requested_capability': 'Telescope scheduling',
            'problem_statement': 'Schedule multiple telescopes',
        })

        bridge = SuggestionBridge(review_queue_path=review, suggestion_storage_path=storage)
        candidate = bridge.add_proposal_candidate(req.request_id)
        assessed = apply_assessment_to_candidate(candidate)

        # Format for display
        from weslr.weslr_operator_views import format_assessment_for_display
        formatted = format_assessment_for_display(assessed)

        print("Formatted output:")
        print(formatted)
        print()

        assert "WESLR ASSESSMENT" in formatted
        assert "Priority:" in formatted
        assert "Fit Score:" in formatted
        assert "Reasoning:" in formatted

        return True, None
    except Exception as e:
        return False, str(e)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == '__main__':
    tests = [
        ('weslr list', test_weslr_list),
        ('weslr detail', test_weslr_detail),
        ('weslr format', test_weslr_format),
    ]

    print('=== Weslr CLI Test ===')
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
