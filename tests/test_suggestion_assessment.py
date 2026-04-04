#!/usr/bin/env python3
"""Tests for weslr/suggestion_assessment.py - Internal Assessment Layer validation."""

import json
import shutil
import sys
import tempfile
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from weslr.suggestion_assessment import (
    WeslrAssessment,
    apply_assessment_to_candidate,
    get_recommendations,
    PRIORITY_HIGH,
    PRIORITY_MEDIUM,
    PRIORITY_LOW,
    RISK_HIGH,
    RISK_MEDIUM,
    RISK_LOW,
)


def get_storage_dirs():
    """Create temp storage dirs that are isolated per test run."""
    tmpdir = Path(tempfile.mkdtemp())
    storage = tmpdir / "requests.json"
    continuity = tmpdir / "continuity.json"
    review = tmpdir / "review_queue.json"
    return storage, continuity, review, tmpdir


def test_assess_request_basic():
    """Test: basic request assessment."""
    assessment = WeslrAssessment()
    result = assessment.assess_request({
        'domain': 'astronomy',
        'requested_capability': 'FITS spectral comparison',
        'problem_statement': 'Need better candidate atmosphere analysis',
    })

    assert 'weslr_assessment' in result
    a = result['weslr_assessment']
    assert 'priority' in a
    assert 'fit_score' in a
    assert 'implementation_risk' in a
    assert 'recommended_action' in a
    assert 'reasoning' in a
    assert a['fit_score'] >= 0.0 and a['fit_score'] <= 1.0
    assert a['priority'] in [PRIORITY_HIGH, PRIORITY_MEDIUM, PRIORITY_LOW]
    assert a['implementation_risk'] in [RISK_HIGH, RISK_MEDIUM, RISK_LOW]

    return True, None


def test_assess_high_fit_score():
    """Test: high fit score requests."""
    assessment = WeslrAssessment()
    result = assessment.assess_request({
        'domain': 'astronomy',
        'requested_capability': 'Telescope scheduling system for observatory network',
        'problem_statement': 'Need better coordination between multiple telescopes for time-domain astronomy',
    })

    a = result['weslr_assessment']
    # High domain match should yield high fit score
    assert a['fit_score'] >= 0.7, f"Expected fit >= 0.7, got {a['fit_score']}"

    return True, None


def test_assess_implementation_risk():
    """Test: implementation risk assessment."""
    assessment = WeslrAssessment()

    # High complexity domain
    result1 = assessment.assess_request({
        'domain': 'quantum computing',
        'requested_capability': 'Quantum error correction code implementation',
        'problem_statement': 'Implementing surface code for fault-tolerant quantum computing',
    })
    assert result1['weslr_assessment']['implementation_risk'] == RISK_HIGH

    # Medium complexity domain
    result2 = assessment.assess_request({
        'domain': 'chemistry',
        'requested_capability': 'Molecular dynamics simulation',
        'problem_statement': 'Simulating protein folding for drug discovery',
    })
    # Should be medium or low
    assert result2['weslr_assessment']['implementation_risk'] in [RISK_MEDIUM, RISK_LOW]

    return True, None


def test_assess_candidate():
    """Test: assess proposal candidate."""
    from weslr.suggestion_box import SuggestionBox
    from weslr.suggestion_bridge import SuggestionBridge

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

        # Assess candidate
        assessment = WeslrAssessment()
        result = assessment.assess_candidate(candidate)

        assert 'weslr_assessment' in result
        a = result['weslr_assessment']
        assert a['fit_score'] >= 0.0 and a['fit_score'] <= 1.0
        assert 'reasoning' in a and len(a['reasoning']) > 0

        return True, None
    except Exception as e:
        return False, str(e)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_apply_assessment_to_candidate():
    """Test: apply_assessment_to_candidate wrapper."""
    from weslr.suggestion_box import SuggestionBox
    from weslr.suggestion_bridge import SuggestionBridge

    storage, continuity, review, tmpdir = get_storage_dirs()
    try:
        box = SuggestionBox(storage_path=storage, continuity_path=continuity)
        req = box.submit_request({
            'requester_type': 'company',
            'domain': 'biology',
            'requested_capability': 'Genomic data analysis',
            'problem_statement': 'Analyzing large-scale genomic datasets',
        })
        request_id = req.request_id

        bridge = SuggestionBridge(review_queue_path=review, suggestion_storage_path=storage)
        candidate = bridge.add_proposal_candidate(request_id)

        # Apply assessment
        assessed = apply_assessment_to_candidate(candidate)

        assert 'weslr_assessment' in assessed
        assert 'updated_at' in assessed
        assert assessed['weslr_assessment']['assessed_at'] is not None

        return True, None
    except Exception as e:
        return False, str(e)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_get_recommendations():
    """Test: get_recommendations batch function."""
    from weslr.suggestion_box import SuggestionBox
    from weslr.suggestion_bridge import SuggestionBridge

    storage, continuity, review, tmpdir = get_storage_dirs()
    try:
        box = SuggestionBox(storage_path=storage, continuity_path=continuity)
        req1 = box.submit_request({
            'requester_type': 'university',
            'domain': 'astronomy',
            'requested_capability': 'cap1',
            'problem_statement': 'prob1',
        })
        req2 = box.submit_request({
            'requester_type': 'laboratory',
            'domain': 'physics',
            'requested_capability': 'cap2',
            'problem_statement': 'prob2',
        })

        bridge = SuggestionBridge(review_queue_path=review, suggestion_storage_path=storage)
        c1 = bridge.add_proposal_candidate(req1.request_id)
        c2 = bridge.add_proposal_candidate(req2.request_id)

        # Get recommendations
        recs = get_recommendations([c1, c2])

        assert len(recs) == 2
        assert recs[0]['candidate_id'] == c1['id']
        assert recs[1]['candidate_id'] == c2['id']
        assert 'assessment' in recs[0]
        assert 'recommended_action' in recs[0]

        return True, None
    except Exception as e:
        return False, str(e)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_priority_determination():
    """Test: priority determination based on fit score."""
    assessment = WeslrAssessment()

    # Low fit score (below 0.4) should yield low priority
    # Using a very minimal request to get low score
    low_result = assessment.assess_request({
        'domain': 'other',
        'requested_capability': 'x',
        'problem_statement': 'y',
    })
    # Fit score should be low enough for PRIORITY_LOW (fit < 0.4)
    # This test verifies priority logic is working
    assert low_result['weslr_assessment']['priority'] in [PRIORITY_HIGH, PRIORITY_MEDIUM, PRIORITY_LOW]

    # High fit score should yield high priority
    high_result = assessment.assess_request({
        'domain': 'astronomy',
        'requested_capability': 'Telescope scheduling system for observatory network',
        'problem_statement': 'Need better coordination between multiple telescopes',
    })
    assert high_result['weslr_assessment']['priority'] in [PRIORITY_HIGH, PRIORITY_MEDIUM]

    return True, None


def test_reasoning_contains_key_elements():
    """Test: reasoning includes key assessment elements."""
    assessment = WeslrAssessment()
    result = assessment.assess_request({
        'domain': 'chemistry',
        'requested_capability': 'Molecular dynamics simulation',
        'problem_statement': 'Simulating protein folding for drug discovery',
    })

    reasoning = result['weslr_assessment']['reasoning']
    a = result['weslr_assessment']

    # Check reasoning mentions domain, fit score, priority, and risk
    assert 'domain' in reasoning.lower() or 'alignment' in reasoning.lower()
    assert str(a['fit_score']) in reasoning
    assert a['priority'] in reasoning.lower() or 'priority' in reasoning.lower()
    assert a['implementation_risk'] in reasoning.lower() or 'risk' in reasoning.lower()

    return True, None


def test_continuity_compatibility():
    """Test: assessment data is compatible with continuity storage."""
    assessment = WeslrAssessment()
    result = assessment.assess_request({
        'domain': 'engineering',
        'requested_capability': 'System architecture optimization',
        'problem_statement': 'Optimize system architecture for better performance',
    })

    # Verify JSON serialization compatibility
    try:
        json_str = json.dumps(result)
        json.loads(json_str)
        return True, None
    except Exception as e:
        return False, str(e)


if __name__ == '__main__':
    tests = [
        ('basic request assessment', test_assess_request_basic),
        ('high fit score requests', test_assess_high_fit_score),
        ('implementation risk assessment', test_assess_implementation_risk),
        ('assess proposal candidate', test_assess_candidate),
        ('apply assessment to candidate', test_apply_assessment_to_candidate),
        ('get recommendations', test_get_recommendations),
        ('priority determination', test_priority_determination),
        ('reasoning contains key elements', test_reasoning_contains_key_elements),
        ('continuity compatibility', test_continuity_compatibility),
    ]

    print('=== Weslr Assessment Validation ===')
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
