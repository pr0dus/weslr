#!/usr/bin/env python3
"""Tests for weslr/suggestion_box.py - WESLR Capability Slice validation."""

import json
import shutil
import sys
import tempfile
from pathlib import Path

# Add weslr to path
sys.path.insert(0, str(Path(__file__).parent.parent / "weslr"))

from suggestion_box import SuggestionBox, VALID_REQUESTER_TYPES


def get_storage_dirs():
    """Create temp storage dirs that are isolated per test run."""
    tmpdir = Path(tempfile.mkdtemp())
    storage = tmpdir / "requests.json"
    continuity = tmpdir / "continuity.json"
    return storage, continuity, tmpdir


def clean_storage(storage, continuity):
    """Remove storage files."""
    if storage.exists():
        storage.unlink()
    if continuity.exists():
        continuity.unlink()


def test_valid_request_submission():
    """Test 1: valid request submission"""
    storage, continuity, tmpdir = get_storage_dirs()
    try:
        box = SuggestionBox(storage_path=storage, continuity_path=continuity)
        req = box.submit_request({
            'requester_type': 'university',
            'domain': 'astronomy',
            'requested_capability': 'FITS spectral comparison',
            'problem_statement': 'Need better candidate atmosphere analysis',
        })
        assert req.request_id.startswith('req-')
        assert req.domain == 'astronomy'
        assert req.status == 'submitted'
        return True, None
    except Exception as e:
        return False, str(e)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_invalid_requester_type_rejection():
    """Test 2: invalid requester type rejection"""
    storage, continuity, tmpdir = get_storage_dirs()
    try:
        box = SuggestionBox(storage_path=storage, continuity_path=continuity)
        try:
            box.submit_request({
                'requester_type': 'invalid_type',
                'domain': 'physics',
                'requested_capability': 'test',
                'problem_statement': 'test',
            })
            return False, 'No error raised for invalid requester_type'
        except ValueError as e:
            if 'Invalid requester_type' in str(e):
                return True, None
            return False, f'Wrong error: {e}'
    except Exception as e:
        return False, str(e)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_domain_filtering():
    """Test 3: domain filtering"""
    storage, continuity, tmpdir = get_storage_dirs()
    try:
        box = SuggestionBox(storage_path=storage, continuity_path=continuity)
        box.submit_request({
            'requester_type': 'laboratory',
            'domain': 'astronomy',
            'requested_capability': 'test1',
            'problem_statement': 'test1',
        })
        box.submit_request({
            'requester_type': 'company',
            'domain': 'physics',
            'requested_capability': 'test2',
            'problem_statement': 'test2',
        })
        filtered = box.list_requests(domain='astronomy')
        if len(filtered) != 1:
            return False, f'Expected 1, got {len(filtered)}'
        if filtered[0]['domain'] != 'astronomy':
            return False, f'Expected astronomy, got {filtered[0]["domain"]}'
        return True, None
    except Exception as e:
        return False, str(e)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_summary_generation():
    """Test 4: summary generation"""
    storage, continuity, tmpdir = get_storage_dirs()
    try:
        box = SuggestionBox(storage_path=storage, continuity_path=continuity)
        summary = box.summarize_requests()
        assert 'total_requests' in summary
        assert 'by_status' in summary
        assert 'by_domain' in summary
        assert 'by_requester_type' in summary
        return True, None
    except Exception as e:
        return False, str(e)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_malformed_request_fallback():
    """Test 5: malformed request fallback"""
    storage, continuity, tmpdir = get_storage_dirs()
    try:
        box = SuggestionBox(storage_path=storage, continuity_path=continuity)
        try:
            box.submit_request({
                'requester_type': 'individual',
                'domain': 'biology',
                'problem_statement': 'test',
            })
            return False, 'No error raised for missing field'
        except ValueError as e:
            if 'Missing required fields' in str(e):
                return True, None
            return False, f'Wrong error: {e}'
    except Exception as e:
        return False, str(e)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_continuity_persistence():
    """Test 6: continuity persistence"""
    storage, continuity, tmpdir = get_storage_dirs()
    try:
        box = SuggestionBox(storage_path=storage, continuity_path=continuity)
        box.submit_request({
            'requester_type': 'laboratory',
            'domain': 'astronomy',
            'requested_capability': 't1',
            'problem_statement': 's1',
        })
        box.submit_request({
            'requester_type': 'company',
            'domain': 'physics',
            'requested_capability': 't2',
            'problem_statement': 's2',
        })
        # Check continuity file
        if not continuity.exists():
            return False, 'Continuity file not created'
        with open(continuity, 'r') as f:
            continuity_data = json.load(f)
        if 'actions' not in continuity_data:
            return False, 'actions key not in continuity'
        if len(continuity_data['actions']) < 2:
            return False, f'Expected at least 2 actions, got {len(continuity_data["actions"])}'
        return True, None
    except Exception as e:
        return False, str(e)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


def test_rollback_behavior():
    """Test 7: rollback behavior"""
    storage, continuity, tmpdir = get_storage_dirs()
    try:
        box = SuggestionBox(storage_path=storage, continuity_path=continuity)
        # First add a request so we have something to rollback
        box.submit_request({
            'requester_type': 'individual',
            'domain': 'biology',
            'requested_capability': 'test',
            'problem_statement': 'test',
        })
        initial_count = len(box.requests)
        box.rollback()
        after_count = len(box.requests)
        if after_count != initial_count - 1:
            return False, f'Rollback did not reduce count: {initial_count} -> {after_count}'
        return True, None
    except Exception as e:
        return False, str(e)
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == '__main__':
    tests = [
        ('valid request submission', test_valid_request_submission),
        ('invalid requester type rejection', test_invalid_requester_type_rejection),
        ('domain filtering', test_domain_filtering),
        ('summary generation', test_summary_generation),
        ('malformed request fallback', test_malformed_request_fallback),
        ('continuity persistence', test_continuity_persistence),
        ('rollback behavior', test_rollback_behavior),
    ]

    print('=== WESLR SuggestionBox Full Validation ===')
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
