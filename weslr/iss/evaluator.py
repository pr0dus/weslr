#!/usr/bin/env python3
"""ISS evaluator — classify probe_exec.py output."""

import json


def evaluate(probe_result: dict) -> dict:
    broken = []
    degraded = []
    evidence = {}

    for key in ("git", "python", "node"):
        status = probe_result.get(key, {}).get("status", "BROKEN")
        evidence[key] = {
            "status": status,
            "exit_code": probe_result[key]["exit_code"],
        }
        if status == "BROKEN":
            broken.append(key)
        elif status == "DEGRADED":
            degraded.append(key)

    if broken:
        overall = "BROKEN"
        recommended = "operator_review_required"
    elif degraded:
        overall = "DEGRADED"
        recommended = "operator_review_required"
    else:
        overall = "OK"
        recommended = "observe_only"

    return {
        "system": "exec",
        "overall_status": overall,
        "broken": broken,
        "degraded": degraded,
        "evidence": evidence,
        "recommended_next_step": recommended,
    }


def main():
    sample = {
        "git": {"status": "OK", "exit_code": 0},
        "python": {"status": "OK", "exit_code": 0},
        "node": {"status": "OK", "exit_code": 0},
    }
    # allow file path or JSON string as argument
    import sys
    if len(sys.argv) > 1:
        try:
            with open(sys.argv[1]) as f:
                probe_result = json.load(f)
        except Exception:
            probe_result = json.loads(sys.argv[1])
    else:
        probe_result = sample

    print(json.dumps(evaluate(probe_result), indent=2))


if __name__ == "__main__":
    main()