# error_translator.py - Parse tracebacks, identify cause, propose fix
from __future__ import annotations

import re
import time


def parse_traceback(traceback: str) -> dict:
    """Parse a Python traceback and extract error info."""
    traceback = str(traceback or "").strip()
    if not traceback:
        return {
            "ok": False,
            "error": "No traceback provided.",
        }

    # Extract last error line
    lines = traceback.splitlines()
    error_lines = []
    for line in reversed(lines):
        line = line.strip()
        if line:
            error_lines.insert(0, line)
            if line.startswith(("Traceback", "File ", "Exception", "SyntaxError", "NameError", "TypeError", "ValueError", "AttributeError", "ImportError", "KeyError", "IndexError", "ZeroDivisionError")):
                break

    # Find the exception type and message
    exception_type = "UnknownError"
    exception_message = ""
    
    # Look for the actual exception line (not File lines)
    exc_line = None
    for line in reversed(lines):
        stripped = line.strip()
        if stripped and not stripped.startswith("File "):
            exc_line = stripped
            break
    
    if exc_line:
        # Try to extract from the exception line: "ExceptionType: Message"
        match = re.match(r"^([A-Za-z]+)\s*:\s*(.*)$", exc_line)
        if match:
            exception_type = match.group(1)
            exception_message = match.group(2)
    
    if not exception_type or not exception_message:
        # Fallback: use last non-empty line
        for line in reversed(lines):
            if line.strip() and not line.strip().startswith("File "):
                exception_message = line.strip()
                break

    # Find file and line info
    file_info = None
    for line in lines:
        file_match = re.search(r'File "([^"]+)", line (\d+)', line)
        if file_match:
            file_info = {
                "file": file_match.group(1),
                "line": int(file_match.group(2)),
                "context": line.strip(),
            }
            break

    return {
        "ok": True,
        "exception_type": exception_type,
        "exception_message": exception_message,
        "file_info": file_info,
        "traceback_preview": "\n".join(lines[-6:]),
    }


def identify_error_type(error_info: dict) -> dict:
    """Identify common error types and their causes."""
    exc_type = str(error_info.get("exception_type", "")).strip()
    exc_msg = str(error_info.get("exception_message", "")).strip()

    patterns = {
        "NameError": {
            "category": "variable",
            "cause": "You tried to use a variable that hasn't been defined yet.",
            "common_causes": [
                "Typo in variable name",
                "Variable used before assignment",
                "Scope issue (defined inside function, used outside)",
            ],
            "fix": "Check the variable name spelling and ensure it's defined before use.",
        },
        "SyntaxError": {
            "category": "syntax",
            "cause": "The code doesn't follow Python's grammar rules.",
            "common_causes": [
                "Missing closing parenthesis, bracket, or quote",
                "Indentation mismatch",
                "Invalid keyword or operator placement",
            ],
            "fix": "Check the line mentioned in the traceback for missing symbols or wrong indentation.",
        },
        "TypeError": {
            "category": "type",
            "cause": "You're doing something with the wrong type (e.g., adding string + int).",
            "common_causes": [
                "Operation between incompatible types",
                "Wrong number of arguments to a function",
                "Calling a non-callable object",
            ],
            "fix": "Check the types involved and convert/normalize before the operation.",
        },
        "AttributeError": {
            "category": "attribute",
            "cause": "You tried to access an attribute or method that doesn't exist on that object.",
            "common_causes": [
                "Typo in attribute name",
                "Object is None (null) but you accessed it",
                "Wrong object type for the operation",
            ],
            "fix": "Check the object type and attribute name. Use dir(obj) to see available attributes.",
        },
        "IndexError": {
            "category": "index",
            "cause": "You tried to access a list/dict index that doesn't exist.",
            "common_causes": [
                "Off-by-one error (using len() as index)",
                "Empty list/dict access",
                "Negative index out of range",
            ],
            "fix": "Check the length before indexing. Use safe access patterns.",
        },
        "KeyError": {
            "category": "key",
            "cause": "You tried to access a dictionary key that doesn't exist.",
            "common_causes": [
                "Typo in key name",
                "Key was never added",
                "Different key format (string vs int)",
            ],
            "fix": "Use dict.get(key, default) or check 'if key in dict' first.",
        },
        "ImportError": {
            "category": "import",
            "cause": "You tried to import something that doesn't exist or can't be found.",
            "common_causes": [
                "Module not installed",
                "Typo in import path",
                "Circular import",
            ],
            "fix": "Install the missing module or fix the import path.",
        },
        "ZeroDivisionError": {
            "category": "math",
            "cause": "You tried to divide by zero.",
            "common_causes": ["Division where denominator could be 0"],
            "fix": "Add a check: if denominator != 0: ...",
        },
    }

    # Match exception type to patterns
    for pattern_name, info in patterns.items():
        if pattern_name.lower() == exc_type.lower() or pattern_name.lower() in exc_msg.lower():
            return info

    # Fallback
    return {
        "category": "unknown",
        "cause": "An unexpected error occurred.",
        "common_causes": ["Unknown"],
        "fix": "Check the traceback and identify what went wrong.",
    }


def propose_fix(error_info: dict, error_type: dict) -> str:
    """Propose a specific fix based on error type."""
    cause = error_type.get("cause", "")
    fixes = error_type.get("common_causes", [])
    fix_suggestion = error_type.get("fix", "")

    parts = [
        f"**Cause**: {cause}",
        f"**Most likely**: {fixes[0] if fixes else 'Unknown'}",
        f"**Quick fix**: {fix_suggestion}",
    ]

    # Add context-specific suggestions
    file_info = error_info.get("file_info", {})
    if file_info:
        parts.append(f"**Location**: `{file_info.get('file', '')}:{file_info.get('line', '?')}`")

    return "\n".join(parts)


def translate_error(traceback: str) -> dict:
    """Full error translation: parse → identify → propose fix."""
    error_info = parse_traceback(traceback)
    if not error_info.get("ok"):
        return error_info

    error_type = identify_error_type(error_info)
    fix_proposal = propose_fix(error_info, error_type)

    return {
        "ok": True,
        "error_info": error_info,
        "error_type": error_type,
        "fix_proposal": fix_proposal,
        "generated_at": int(time.time()),
    }


def translate_error_to_plain_english(traceback: str) -> str:
    """Generate human-readable error explanation."""
    result = translate_error(traceback)
    if not result.get("ok"):
        return "I couldn't parse that traceback."

    info = result.get("error_info", {})
    error_type = result.get("error_type", {})
    fix = result.get("fix_proposal", "")

    parts = [
        f"**Error**: {info.get('exception_type', 'UnknownError')}",
        f"**Message**: {info.get('exception_message', 'No message')}",
        "",
        f"**What went wrong**: {error_type.get('cause', 'Unknown')}",
        "",
        "I think you should:",
        fix,
    ]

    return "\n".join(parts)


def explain_error(traceback: str) -> dict:
    """Public interface: explain an error in plain English."""
    explanation = translate_error_to_plain_english(traceback)
    return {
        "explanation": explanation,
        "generated_at": int(time.time()),
    }
