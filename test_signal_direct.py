#!/usr/bin/env python3
"""Test signal capture with mock response."""
import sys
sys.path.insert(0, '/home/pr0/projects/weslr')

from weslr.website_signal_integration import capture_website_signal

# Test 1: Simple fallback_safe response
response1 = {
    "response_text": "I can respond to open-ended chat",
    "path": "fallback_safe",
    "confidence": "low",
    "_omnichat_policy": {
        "evidence_offer": True,
        "final_response_type": "fallback"
    }
}

capture_website_signal(
    message="hello",
    session_id="test_session_001",
    response_path="fallback_safe",
    quality_class=None,
    blocked_write=False,
    evidence_offer_shown=True,
    evidence_offer_accepted=False,
    topic_normalized="greeting",
    fallback_triggered=True
)
print("Signal capture test 1 passed")
