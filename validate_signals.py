#!/usr/bin/env python3
"""Validate cleanup: legacy _context_selection removed, only generic signals remain."""
import sys
sys.path.insert(0, '.')

from dialogue import _compute_context_selection, _compute_boundary_hints

def test_context_selection_v1():
    print("=== _context_selection_v1 (generic) ===")
    cases = [
        ("improve this", {"_has_active_artifact": True}, None, "resolved_artifact"),
        ("continue with that", {}, ("topic", {}), "current_thread"),
        ("What is entity extraction?", {}, None, "new_topic"),
        ("hmm about that thing", {}, None, "uncertain"),
        ("", {}, None, "uncertain"),
    ]
    for msg, rc, thread, expected in cases:
        result = _compute_context_selection(msg, rc, thread)
        assert result == expected, f"FAIL: {expected}, got {result}"
        print(f"  ✓ '{msg[:30]}' → {result}")

def test_boundary_hints():
    print("=== _boundary_hints (generic) ===")
    cases = [
        ("the plugin module uses the runtime engine", {"module", "runtime", "tool"}),
        ("the system exposes an API endpoint for the user operator", {"interface", "role", "system"}),
        ("the artifact memory state", {"data"}),
        ("flurb gibbon wizzle", {"unknown"}),
        ("", {"unknown"}),
    ]
    for msg, expected in cases:
        result = set(_compute_boundary_hints(msg))
        assert result == expected, f"FAIL: {expected}, got {result}"
        print(f"  ✓ '{msg[:30]}' → {sorted(result)}")

def test_no_legacy_context_selection():
    print("=== No product-name-coupled _context_selection ===")
    # Verify _classify_context is not defined (removed)
    try:
        from dialogue import _classify_context
        print("  FAIL: _classify_context still exists in module")
        return False
    except ImportError:
        print("  ✓ _classify_context not in module (removed)")
    # Verify CONTEXT_KEYWORDS not in module
    try:
        from dialogue import CONTEXT_KEYWORDS
        print("  FAIL: CONTEXT_KEYWORDS still in module")
        return False
    except ImportError:
        print("  ✓ CONTEXT_KEYWORDS not in module (removed)")
    return True

if __name__ == "__main__":
    test_context_selection_v1()
    test_boundary_hints()
    if test_no_legacy_context_selection():
        print()
        print("All validations passed ✓")
    else:
        print("Legacy cleanup incomplete — see above")
