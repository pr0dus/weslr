#!/usr/bin/env python3
"""Simulate signal capture for staging validation."""
import json
import sys
sys.path.insert(0, '/home/pr0/projects/weslr')

# Simulate 3 chat requests with different paths
test_cases = [
    {"message": "hello", "response_path": "fallback_safe", "evidence_offer_shown": True},
    {"message": "asdasd123", "response_path": "fallback_safe", "evidence_offer_shown": False},
    {"message": "tell me something unclear", "response_path": "fallback_safe", "evidence_offer_shown": True},
]

from weslr.website_signal_integration import capture_website_signal
from weslr.public_signal_store import append_public_signal_record
from weslr.user_signal_intake import classify_public_signal, build_public_signal_record

print("=== Simulating 3 chat requests ===")

for tc in test_cases:
    event = {
        "session_id_hash": "simulated_hash_001",
        "message_length_bucket": "short",
        "response_path": tc["response_path"],
        "fallback_triggered": True,
        "evidence_offer_shown": tc["evidence_offer_shown"],
        "evidence_offer_accepted": False,
        "blocked_write": False,
        "topic_normalized": "test",
        "timestamp": "2026-04-30T13:00:00+00:00",
    }
    
    classification = classify_public_signal(event)
    record = build_public_signal_record(event)
    result = append_public_signal_record(record)
    print(f"Request: {tc['message'][:10]:10} → stored={result['stored']}, signal_type={record.get('signal_type')}")

print("\n=== Signal file contents ===")
with open('/home/pr0/projects/weslr/weslr/public_signals.jsonl', 'r') as f:
    lines = f.readlines()
    for line in lines[-5:]:
        data = json.loads(line.strip())
        print(f"{data['signal_type']:3} {data['response_path']:20} safe={data['safe_to_record']}")
