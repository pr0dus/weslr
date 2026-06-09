#!/usr/bin/env python3
"""Test signal capture."""
from weslr.website_signal_integration import capture_website_signal

capture_website_signal(
    message="test message",
    session_id="test_session_001",
    response_path="fallback_safe",
    quality_class=None,
    blocked_write=False,
    evidence_offer_shown=False,
    evidence_offer_accepted=False,
    topic_normalized="test_topic",
    fallback_triggered=False
)
print("capture_website_signal completed")
