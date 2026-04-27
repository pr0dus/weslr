#!/usr/bin/env python3
"""ISS probe — check exec tool integrity across git, python, node."""

import subprocess

COMMANDS = {
    "git": ["git", "--version"],
    "python": ["python3", "--version"],
    "node": ["node", "-v"],
}


def run_command(cmd):
    result = {"stdout": "", "stderr": "", "exit_code": None, "status": "OK"}
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        result["stdout"] = p.stdout
        result["stderr"] = p.stderr
        result["exit_code"] = p.returncode
    except Exception as e:
        result["stderr"] = str(e)
        result["status"] = "BROKEN"
        return result

    if "Permission denied" in result["stderr"] or "Permission denied" in result["stdout"]:
        result["status"] = "BROKEN"
    elif not result["stdout"].strip() and not result["stderr"].strip():
        result["status"] = "DEGRADED"
    else:
        result["status"] = "OK"
    return result


def main():
    out = {}
    for key, cmd in COMMANDS.items():
        out[key] = run_command(cmd)

    statuses = [v["status"] for v in out.values()]
    if "BROKEN" in statuses:
        overall = "BROKEN"
    elif "DEGRADED" in statuses:
        overall = "DEGRADED"
    else:
        overall = "OK"

    out["overall_status"] = overall
    print(__import__("json").dumps(out, indent=2))


if __name__ == "__main__":
    main()