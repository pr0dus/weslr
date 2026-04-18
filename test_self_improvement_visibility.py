#!/usr/bin/env python3
"""Test self-improvement visibility filtering in operator-only mode.

This test verifies that proposals are hidden from public in public_test mode.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path


def test_visibility_filtering():
    """Test that proposals are hidden in public_test mode."""
    print("Testing self-improvement visibility filtering...")
    print("=" * 60)
    
    # Set profile to public_test
    os.environ["WESLR_ACTIVE_PROFILE"] = "public_test"
    
    # Import after setting env var
    from weslr.profiles import get_active_profile, is_self_improvement_public
    from self_improvement_proposal import (
        _is_public_visible,
        _filter_for_visibility,
        list_proposals,
        build_proposal_report,
    )
    
    # Verify profile settings
    profile = get_active_profile()
    print(f"Active profile: {profile.name}")
    print(f"Public mode: {profile.public_mode}")
    print(f"Self-improvement public: {profile.self_improvement_visible_to_public}")
    
    assert profile.public_mode, "public_test should be public mode"
    
    # Test visibility check
    visible = _is_public_visible()
    print(f"Proposals visible to public: {visible}")
    assert not visible, "Proposals should NOT be visible to public in public_test mode"
    
    # Test filter function
    test_proposals = [
        {"id": "prop-1", "title": "Test proposal 1"},
        {"id": "prop-2", "title": "Test proposal 2"},
    ]
    
    filtered = _filter_for_visibility(test_proposals)
    print(f"Filtered proposals: {filtered}")
    assert filtered == [], "Filter should return empty list in operator-only mode"
    
    # Test list_proposals
    result = list_proposals()
    print(f"list_proposals() result: {json.dumps(result, indent=2)}")
    assert result.get("proposals") == [], "list_proposals should return empty list"
    assert not result.get("public_visible", True), "public_visible should be False"
    
    # Test build_proposal_report
    report = build_proposal_report()
    print(f"build_proposal_report() public_visible: {report.get('public_visible')}")
    print(f"build_proposal_report() summary_only: {report.get('summary_only')}")
    assert not report.get("public_visible", True), "public_visible should be False"
    assert report.get("summary_only") == True, "summary_only should be True in operator-only mode"
    assert "proposals" not in report, "proposals should not be in report"
    
    print("\n" + "=" * 60)
    print("✅ All visibility tests passed!")
    print("=" * 60)


def test_operator_access():
    """Test that operators can still access proposals directly."""
    print("\nTesting operator access to proposals...")
    print("=" * 60)
    
    from self_improvement_proposal import get_proposal_operator, load_proposals
    
    # Load all proposals directly (bypassing visibility filter)
    proposals = load_proposals()
    print(f"Total proposals in storage: {len(proposals)}")
    
    if proposals:
        first_proposal = proposals[0]
        print(f"First proposal ID: {first_proposal.get('id')}")
        print(f"First proposal title: {first_proposal.get('title')}")
        
        # Test operator access
        operator_proposal = get_proposal_operator(first_proposal.get("id"))
        assert operator_proposal is not None, "Operator should be able to access proposal"
        assert operator_proposal.get("id") == first_proposal.get("id")
        print(f"Operator access: OK")
    
    print("=" * 60)
    print("✅ Operator access test passed!")
    print("=" * 60)


if __name__ == "__main__":
    try:
        test_visibility_filtering()
        test_operator_access()
        print("\n" + "=" * 60)
        print("ALL TESTS PASSED ✅")
        print("=" * 60)
        sys.exit(0)
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
