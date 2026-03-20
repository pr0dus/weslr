from __future__ import annotations

import json
import subprocess
import tempfile
from pathlib import Path

from config import CODE_TIMEOUT_SECONDS, MAX_STDOUT_CHARS


SANDBOX_PREAMBLE = r'''
import builtins
import json
from pathlib import Path

ALLOWED_IMPORTS = {"json", "math", "random", "statistics", "itertools", "collections", "pathlib", "time"}
_real_import = builtins.__import__

def limited_import(name, globals=None, locals=None, fromlist=(), level=0):
    root = name.split(".")[0]
    if root not in ALLOWED_IMPORTS:
        raise ImportError(f"Import blocked: {name}")
    return _real_import(name, globals, locals, fromlist, level)

builtins.__import__ = limited_import
'''


def run_python(code: str, working_dir: Path) -> dict:
    working_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, dir=working_dir) as f:
        script_path = Path(f.name)
        f.write(SANDBOX_PREAMBLE)
        f.write("\n")
        f.write(code)

    try:
        proc = subprocess.run(
            ["python", str(script_path)],
            cwd=str(working_dir),
            capture_output=True,
            text=True,
            timeout=CODE_TIMEOUT_SECONDS,
        )
        return {
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "stdout": proc.stdout[:MAX_STDOUT_CHARS],
            "stderr": proc.stderr[:MAX_STDOUT_CHARS],
            "script": str(script_path),
        }
    except subprocess.TimeoutExpired as e:
        return {
            "ok": False,
            "returncode": -1,
            "stdout": (e.stdout or "")[:MAX_STDOUT_CHARS],
            "stderr": ((e.stderr or "") + "\nTIMEOUT")[:MAX_STDOUT_CHARS],
            "script": str(script_path),
        }
