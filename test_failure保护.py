#!/usr/bin/env python3
"""Test failure handling with read-only signal file."""
import sys
sys.path.insert(0, '/home/pr0/projects/weslr')

from weslr.website_signal_integration import capture_website_signal

# This should silently fail without raising exception
capture_website_signal(
    message="test after chmod 000",
    session_id="test_session_failure",
    response_path="fallback_safe",
    quality_class=None,
    blocked_write=False,
    evidence_offer_shown=False,
    evidence_offer_accepted=False,
    topic_normalized="test",
    fallback_triggered=True
)
print("Failure test: capture completed without raising exception (expected)")
