# self_inspection.py - Weslr can read and describe its own code in plain English
from __future__ import annotations

import ast
import time
from pathlib import Path


def list_circlegeforge_files() -> list[str]:
    """Return list of Weslr source files to inspect."""
    circleforge_dir = Path(__file__).parent
    files = []
    for f in circleforge_dir.glob("*.py"):
        # Skip test/debug files, skip __pycache__
        name = f.name
        if name.startswith("test_") or name.startswith("_") or name == "__init__.py":
            continue
        if "cache" in str(f).lower():
            continue
        files.append(str(f))
    return sorted(files)


def parse_python_file(filepath: str) -> dict:
    """Parse a Python file and extract key structural info."""
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        tree = ast.parse(content)
    except Exception as e:
        return {
            "file": filepath,
            "ok": False,
            "error": str(e),
        }

    # Extract top-level info
    functions = []
    classes = []
    imports = []
    docstring = None

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            functions.append({
                "name": node.name,
                "line": node.lineno,
                "args": [a.arg for a in node.args.args],
            })
        elif isinstance(node, ast.ClassDef):
            classes.append({
                "name": node.name,
                "line": node.lineno,
            })
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            names = [alias.name for alias in node.names]
            imports.append(f"from {module} import {', '.join(names)}")
        elif isinstance(node, ast.Import):
            names = [alias.name for alias in node.names]
            imports.append(f"import {', '.join(names)}")
        elif isinstance(node, ast.Module) and node.body and isinstance(node.body[0], ast.Expr):
            if isinstance(node.body[0].value, ast.Str):
                docstring = node.body[0].value.s

    # Extract file-level metadata from comments
    lines = content.splitlines()
    header_lines = []
    for line in lines[:10]:
        if line.strip().startswith("#") or line.strip().startswith("from __future__"):
            header_lines.append(line.strip())

    return {
        "file": filepath,
        "ok": True,
        "docstring": docstring,
        "functions": functions[:12],  # limit for readability
        "classes": classes[:8],
        "imports": imports[:20],
        "header_lines": header_lines,
        "line_count": len(lines),
    }


def generate_self_description(inspections: list[dict]) -> str:
    """Generate plain-English summary of Weslr's structure."""
    if not inspections:
        return "I couldn't inspect myself because no source files were found."

    # Count what we have
    total_files = len(inspections)
    total_functions = sum(len(i.get("functions", [])) for i in inspections)
    total_classes = sum(len(i.get("classes", [])) for i in inspections)
    files_ok = sum(1 for i in inspections if i.get("ok"))
    files_with_errors = [i for i in inspections if not i.get("ok")]

    # Build description
    parts = []

    parts.append(
        f"I am Weslr, a local continuous system written in Python. "
        f"I consists of {total_files} source files with {total_functions} functions and {total_classes} classes."
    )

    # Core modules
    core_modules = []
    for insp in inspections:
        if not insp.get("ok"):
            continue
        filename = Path(insp.get("file", "")).name
        funcs = insp.get("functions", [])
        if any(f.get("name") in ["perform_tick", "init_world", "render_dashboard"] for f in funcs):
            core_modules.append(f"{filename} (core runtime)")
        elif any(f.get("name") in ["build_communicator_message", "generate_from_self_state"] for f in funcs):
            core_modules.append(f"{filename} (communication)")
        elif any(f.get("name") in ["monitor_memory_pressure", "build_memory_score_report"] for f in funcs):
            core_modules.append(f"{filename} (memory management)")
        elif any(f.get("name") in ["fetch_url_text", "search_web"] for f in funcs):
            core_modules.append(f"{filename} (web research)")
        elif filename == "config.py":
            core_modules.append("config.py (configuration)")

    if core_modules:
        parts.append(f"My main roles are covered by: {', '.join(core_modules[:5])}.")

    # Self-model and continuity
    has_self_model = any(
        insp.get("file", "").endswith("self_model.py")
        for insp in inspections
        if insp.get("ok")
    )
    has_continuity = any(
        insp.get("file", "").endswith("continuity.py")
        for insp in inspections
        if insp.get("ok")
    )
    if has_self_model:
        parts.append("I have modules for self-modeling and internal regulation.")
    if has_continuity:
        parts.append("I have modules for persistence across ticks and session continuity.")

    # Errors (if any)
    if files_with_errors:
        parts.append(f"However, {len(files_with_errors)} file(s) failed to parse due to syntax or formatting issues.")

    return " ".join(parts)


def inspect_self() -> dict:
    """Run self-inspection and return structured data plus human-readable description."""
    files = list_circlegeforge_files()
    inspections = [parse_python_file(f) for f in files]
    description = generate_self_description(inspections)

    return {
        "files_inspected": len(inspections),
        "files_ok": sum(1 for i in inspections if i.get("ok")),
        "files_error": sum(1 for i in inspections if not i.get("ok")),
        "inspections": inspections,
        "description": description,
        "generated_at": int(time.time()),
    }


def build_self_inspection_report() -> dict:
    """Public interface: run self-inspection and return a clean report."""
    result = inspect_self()
    return {
        "ok": result.get("files_ok", 0) > 0,
        "description": result.get("description", "I couldn't generate a self-description."),
        "files": result.get("files_inspected", 0),
        "functions_found": sum(
            len(i.get("functions", []))
            for i in result.get("inspections", [])
            if i.get("ok")
        ),
        "classes_found": sum(
            len(i.get("classes", []))
            for i in result.get("inspections", [])
            if i.get("ok")
        ),
        "files_with_errors": result.get("files_error", 0),
    }
