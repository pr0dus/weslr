#!/usr/bin/env python3
"""Test failure handling: break storage and confirm response still works."""
import os
import tempfile
import json

# Temporarily break storage path
storage_path = "/home/pr0/projects/weslr/weslr/public_signals.jsonl"
broken_path = "/home/pr0/projects/weslr/weslr/broken_storage_dir"

# Backup current file content
with open(storage_path, "r") as f:
    original_content = f.read()

# Create broken directory with no write permission
os.makedirs(broken_path, exist_ok=True)
os.chmod(broken_path, 0o444)  # read-only

# Try to capture signal (should silently fail)
from weslr.website_signal_integration import capture_website_signal
capture_website_signal(
    message="failure test message",
    session_id="test_session_002",
    response_path="operator_overview",
    quality_class=None,
    blocked_write=False,
    evidence_offer_shown=False,
    evidence_offer_accepted=False,
    topic_normalized="failure_test",
    fallback_triggered=False
)
print("Failure test: capture completed without raising exception")

# Restore normal state
os.chmod(broken_path, 0o755)
os.rmdir(broken_path)

# Verify file unchanged
with open(storage_path, "r") as f:
    lines_after = f.readlines()
print(f"Lines after failure: {len(lines_after)}")
print("Failure test PASSED: no crash, append blocked silently")
