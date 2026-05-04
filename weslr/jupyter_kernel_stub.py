"""
weslr/jupyter_kernel_stub.py
=============================
Phase 10 — Jupyter notebook integration stub.

Provides a simple `run_in_notebook(command_string)` function that
executes Weslr CLI commands and returns results as JSON-compatible dicts.

Usage from a Jupyter cell:
    from weslr.jupyter_kernel_stub import run_in_notebook
    result = run_in_notebook("/hypothesis list")
    print(result["output"])

No LLM. Deterministic. In-memory only.

Author: OCC (WESLR governed intelligence) — Phase 10
"""

from __future__ import annotations

import json
import subprocess
import sys
import threading
from pathlib import Path
from typing import Optional

# ── Constants ────────────────────────────────────────────────────────────────

WESLR_CLI_COMMAND = [sys.executable, "-m", "weslr.cli.main"]
KERNEL_NAME = "weslr"

# ── Output capture ────────────────────────────────────────────────────────────

def _run_cli_command(command: str) -> tuple[str, str, int]:
    """Run a Weslr CLI command via subprocess, capture output.

    Returns (stdout, stderr, returncode).
    """
    # Strip leading "/" if present (Jupyter users may type "/hypothesis list")
    cmd_clean = command.strip()
    if cmd_clean.startswith("/"):
        cmd_clean = cmd_clean[1:]

    # Build the full argv
    # The main.py uses argparse; pass words split from the command
    argv = cmd_clean.split()

    try:
        result = subprocess.run(
            [sys.executable, "-m", "weslr.cli.main"] + argv,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(Path(__file__).resolve().parent.parent),
        )
        return result.stdout, result.stderr, result.returncode
    except subprocess.TimeoutExpired:
        return "", "Command timed out after 30 seconds.", -1
    except FileNotFoundError:
        return "", f"Weslr CLI not found at {sys.executable} -m weslr.cli.main", -1
    except Exception as exc:
        return "", f"Execution error: {exc}", -1


# ── Main entry point ──────────────────────────────────────────────────────────

def run_in_notebook(command: str) -> dict:
    """Execute a Weslr command from a Jupyter notebook cell.

    Parameters
    ----------
    command : str
        The full command string, e.g. "/hypothesis list" or
        "hypothesis list" or "/explore drug dose".

    Returns
    -------
    dict with keys:
        - output : str  — stdout (or error message)
        - error  : str or None — stderr or None if success
        - returncode : int — subprocess return code
        - kernel : str — "weslr"
        - command : str — the command that was run
        - images : list — reserved for future plot outputs (currently [])

    Example
    -------
    >>> result = run_in_notebook("/hypothesis list")
    >>> print(result["output"])
    """
    if not command or not command.strip():
        return {
            "output": "",
            "error": "Empty command.",
            "returncode": -1,
            "kernel": KERNEL_NAME,
            "command": command,
            "images": [],
        }

    output, error, returncode = _run_cli_command(command)

    return {
        "output": output,
        "error": error if error and returncode != 0 else None,
        "returncode": returncode,
        "kernel": KERNEL_NAME,
        "command": command,
        "images": [],
    }


# ── Async variant (for async Jupyter kernels) ─────────────────────────────────

def run_in_notebook_async(command: str, callback=None):
    """Run a command asynchronously, optionally call callback with result."""
    def _bg():
        result = run_in_notebook(command)
        if callback:
            callback(result)
        return result
    t = threading.Thread(target=_bg, daemon=True)
    t.start()
    return {"status": "dispatched", "kernel": KERNEL_NAME, "command": command}


# ── Jupyter connection info ───────────────────────────────────────────────────

def get_connection_info() -> dict:
    """Return connection info for Jupyter kernel registration."""
    return {
        "kernel_name": KERNEL_NAME,
        "implementation": "WESLR Phase 10 Jupyter Stub",
        "implementation_version": "0.1.0",
        "language": "python",
        "language_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "description": (
            "WESLR Jupyter kernel stub — executes Weslr CLI commands "
            "from notebook cells and returns structured output."
        ),
        "usage": (
            "from weslr.jupyter_kernel_stub import run_in_notebook\n"
            "result = run_in_notebook('/hypothesis list')\n"
            "print(result['output'])"
        ),
    }


# ── CLI /jupyter info command output ─────────────────────────────────────────

def print_info():
    """Print Jupyter stub connection instructions to stdout."""
    info = get_connection_info()
    lines = [
        "WESLR Jupyter Stub — Connection Instructions",
        "=" * 50,
        "",
        "Step 1: In a Jupyter cell, import the stub:",
        "    from weslr.jupyter_kernel_stub import run_in_notebook",
        "",
        "Step 2: Execute Weslr commands directly:",
        "    result = run_in_notebook('/hypothesis list')",
        "    print(result['output'])",
        "",
        "Step 3: For async execution:",
        "    def my_callback(result): print(result['output'])",
        "    run_in_notebook_async('/explore drug dose', callback=my_callback)",
        "",
        f"Kernel name: {info['kernel_name']}",
        f"Implementation: {info['implementation']}",
        f"Language: {info['language']}",
        "",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    print(print_info())