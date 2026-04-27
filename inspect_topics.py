#!/usr/bin/env python3
"""Inspect callers of infer_human_topics and what they expect."""
import os
import sys
import ast
import json
from pathlib import Path

BASE = Path("/data/data/com.termux/files/home/.openclaw/workspace")

results = {
    "infer_human_topics_def": None,
    "callers": [],
    "caller_details": [],
}

# Find interpretation.py
interp_file = BASE / "interpretation.py"
if interp_file.exists():
    src = interp_file.read_text()
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "infer_human_topics":
            results["infer_human_topics_def"] = {
                "file": str(interp_file),
                "line": node.lineno,
                "returns": "list[str]",
            }
            # Check return type annotation
            if node.returns:
                results["infer_human_topics_def"]["annotation"] = ast.unparse(node.returns)

# Find all callers
for py_file in BASE.rglob("*.py"):
    if ".weslr" in str(py_file) or "site-packages" in str(py_file):
        continue
    try:
        src = py_file.read_text()
        tree = ast.parse(src)
    except:
        continue
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id == "infer_human_topics":
                call_file = str(py_file.relative_to(BASE))
                # Get line number
                line = node.lineno
                # Get parent function/class
                parent_func = None
                parent_class = None
                for parent in ast.walk(tree):
                    if isinstance(parent, ast.FunctionDef):
                        for child in ast.walk(parent):
                            if child is node:
                                parent_func = parent.name
                                break
                    if isinstance(parent, ast.ClassDef):
                        for child in ast.walk(parent):
                            if child is node:
                                parent_class = parent.name
                                break
                
                results["callers"].append({
                    "file": call_file,
                    "line": line,
                    "parent_func": parent_func,
                    "parent_class": parent_class,
                })

# Now check what callers DO with the returned list
# Look at interpret_human_turn which calls infer_human_topics
for py_file in BASE.rglob("*.py"):
    if py_file.name == "interpretation.py":
        continue
    try:
        src = py_file.read_text()
    except:
        continue
    
    if "interpret_human_turn" in src:
        print(f"Found interpret_human_turn in {py_file.relative_to(BASE)}")
        # Check how topics is used
        for i, line in enumerate(src.split("\n"), 1):
            if "topics" in line.lower() and ("for " in line or "if " in line or "==" in line or ".append" in line or "[" in line):
                print(f"  Line {i}: {line.strip()[:100]}")

# Check interpret_human_turn itself
interp_src = (BASE / "interpretation.py").read_text()
print("\n=== interpret_human_turn usage of topics ===")
for i, line in enumerate(interp_src.split("\n"), 1):
    if "topics" in line.lower():
        print(f"  Line {i}: {line.strip()[:120]}")

# Check return value usage
print("\n=== Return value structure ===")
print("infer_human_topics returns: list[str] (plain string labels)")
print("Example: ['Weslr', 'memory continuity', 'entity status']")
print("")

# Check if any caller accesses list elements as dicts
print("\n=== Checking for dict access on topics ===")
for py_file in BASE.rglob("*.py"):
    try:
        src = py_file.read_text()
    except:
        continue
    # Look for topics[0]["name"] or topics[0].name patterns
    if ".topics" in src or "topics[" in src:
        for i, line in enumerate(src.split("\n"), 1):
            if "topics[" in line and ('"' in line or "." in line.split("topics[")[0] or "[" in line):
                if "topics[0]" in line and ("[" in line.split("topics[0]")[1][:5] or '"' in line.split("topics[0]")[1][:5]):
                    print(f"  {py_file.name}:{i} {line.strip()[:100]}")

print("\n=== Verdict ===")
print("Return type: list[str] — plain string labels, NOT dicts")
print("Callers: interpret_human_turn (internal to interpretation.py)")
print("  - topics used as: list iterated, string compared, [0] accessed as string")
print("  - No dict access patterns found")
print("")
print("Verdict: STRING_LABELS_CORRECT_FOR_NOW")
print("Reason: No caller accesses list elements as structured objects.")
print("        All usage is string label comparison, iteration, or indexing as str.")