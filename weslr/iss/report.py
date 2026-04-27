#!/usr/bin/env python3
"""ISS report — deterministic human-readable transformation of evaluator JSON."""

import json
import sys

COMPONENT_NAMES = {
    "git": "Git",
    "python": "Python",
    "node": "Node.js",
}

EXPLANATIONS = {
    "BROKEN": {
        "git": "Git is not executable (permission denied or missing). Repository operations will fail.",
        "python": "Python3 is not executable. Weslr Python modules will not run.",
        "node": "Node.js is not executable. NPM packages and JS-based tools will not run.",
    },
    "DEGRADED": {
        "git": "Git produced no output. Possible PATH issue or silent failure.",
        "python": "Python3 produced no output. Possible PATH issue or silent failure.",
        "node": "Node.js produced no output. Possible PATH issue or silent failure.",
    },
    "OK": {
        "git": "Git is executable and responding normally.",
        "python": "Python3 is executable and responding normally.",
        "node": "Node.js is executable and responding normally.",
    },
}


def build_report(evaluator_result: dict) -> str:
    system = evaluator_result.get("system", "unknown")
    overall = evaluator_result.get("overall_status", "UNKNOWN")
    broken = evaluator_result.get("broken", [])
    degraded = evaluator_result.get("degraded", [])
    evidence = evaluator_result.get("evidence", {})

    lines = []
    lines.append(f"System: {system}")
    lines.append(f"Status: {overall}")
    lines.append("")

    if overall == "OK":
        lines.append("All components operational.")
        return "\n".join(lines)

    if broken:
        lines.append(f"Broken components: {', '.join(broken)}")
        lines.append("")
        for comp in broken:
            lines.append(f"- {COMPONENT_NAMES.get(comp, comp)}: {EXPLANATIONS['BROKEN'].get(comp, 'Unknown failure')}")

    if degraded:
        lines.append(f"Degraded components: {', '.join(degraded)}")
        lines.append("")
        for comp in degraded:
            lines.append(f"- {COMPONENT_NAMES.get(comp, comp)}: {EXPLANATIONS['DEGRADED'].get(comp, 'Silent failure')}")

    lines.append("")
    if overall == "BROKEN":
        lines.append("Next step:")
        lines.append("- Operator review required")
    else:
        lines.append("Next step:")
        lines.append("- Operator review required")

    return "\n".join(lines)


def main():
    if len(sys.argv) > 1:
        try:
            with open(sys.argv[1]) as f:
                data = json.load(f)
        except Exception:
            data = json.loads(sys.argv[1])
    else:
        data = {
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

    print(build_report(data))


if __name__ == "__main__":
    main()