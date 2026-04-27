#!/usr/bin/env python3
"""ISS record — append evaluator result to JSONL log."""

import json
import os
import sys
from datetime import datetime, timezone

LOG_PATH = "/data/data/com.termux/files/home/.openclaw/workspace/memory/iss_records.jsonl"


def record(evaluator_result: dict) -> dict:
    record = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "system": evaluator_result.get("system", "unknown"),
        "overall_status": evaluator_result.get("overall_status", "UNKNOWN"),
        "broken": evaluator_result.get("broken", []),
        "degraded": evaluator_result.get("degraded", []),
        "recommended_next_step": evaluator_result.get("recommended_next_step", "observe_only"),
        "evidence": evaluator_result.get("evidence", {}),
    }

    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(record) + "\n")

    return record


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--sample":
        sample = {
            "system": "exec",
            "overall_status": "OK",
            "broken": [],
            "degraded": [],
            "recommended_next_step": "observe_only",
            "evidence": {
                "git": {"status": "OK", "exit_code": 0},
                "python": {"status": "OK", "exit_code": 0},
                "node": {"status": "OK", "exit_code": 0},
            },
        }
        result = record(sample)
    elif len(sys.argv) > 1:
        try:
            with open(sys.argv[1]) as f:
                evaluator_result = json.load(f)
        except Exception:
            evaluator_result = json.loads(sys.argv[1])
        result = record(evaluator_result)
    else:
        print("Usage: record.py [--sample|<file>|<json>]")
        sys.exit(1)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()