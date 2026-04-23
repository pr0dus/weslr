#!/usr/bin/env python3
"""Validate _context_selection_v1 and _boundary_hints implementation."""

import sys
import os

# Ensure workspace is on path
sys.path.insert(0, "/data/data/com.termux/files/home/.openclaw/workspace")

from dialogue import (
    _compute_context_selection,
    _compute_boundary_hints,
)

PASS = "\033[92m✓\033[0m"
FAIL = "\033[91m✗\033[0m"

def check(label, got, expected):
    ok = got == expected
    status = f"{PASS} {label}" if ok else f"{FAIL} {label}"
    detail = f" | got={got!r} expected={expected!r}" if not ok else ""
    print(f"  {status}{detail}")
    return ok

all_pass = True

print("\n── _context_selection_v1 ──\n")

# 1. Artifact reference turn → resolved_artifact
rc = {"_has_active_artifact": True}
got = _compute_context_selection("improve this", rc, None)
all_pass &= check("Artifact ref → resolved_artifact", got, "resolved_artifact")

# 2. Thread continuation without artifact → current_thread
got = _compute_context_selection("tell me more", {}, ("some topic", {}))
all_pass &= check("Thread + no ref phrase → current_thread", got, "current_thread")

# 3. Clearly new topic → new_topic
got = _compute_context_selection("what is an entity graph", {}, None)
all_pass &= check("New topic (what is...) → new_topic", got, "new_topic")

# 3b. New topic via how does
got = _compute_context_selection("how does memory work", {}, None)
all_pass &= check("New topic (how does...) → new_topic", got, "new_topic")

# 4. Reference phrase in thread → uncertain (has active_thread + reference phrase)
got = _compute_context_selection("improve this", {}, ("some topic", {}))
all_pass &= check("Thread + ref phrase → uncertain", got, "uncertain")

# 5. Ambiguous / no signal → uncertain
got = _compute_context_selection("hello there", {}, None)
all_pass &= check("Ambiguous / no signal → uncertain", got, "uncertain")

got = _compute_context_selection("", {}, None)
all_pass &= check("Empty message → uncertain", got, "uncertain")

# 6. No thread, no artifact, new-topic signal → new_topic
got = _compute_context_selection("explain the difference", {}, None)
all_pass &= check("explain the difference → new_topic", got, "new_topic")

print("\n── _boundary_hints ──\n")

# 7. system keyword
got = _compute_context_selection("tell me about the system", {}, None)
bh = _compute_boundary_hints("tell me about the system")
all_pass &= check("system keyword → system", "system" in bh, True)

# 8. module/plugin keyword
bh = _compute_boundary_hints("the plugin module is loaded")
all_pass &= check("module/plugin keyword → module", "module" in bh, True)

# 9. tool/cli keyword
bh = _compute_boundary_hints("run the tool")
all_pass &= check("tool keyword → tool", "tool" in bh, True)

# 10. runtime/engine keyword
bh = _compute_boundary_hints("the runtime engine is running")
all_pass &= check("runtime/engine keyword → runtime", "runtime" in bh, True)

# 11. role keywords
bh = _compute_boundary_hints("the user and operator are connected")
all_pass &= check("role keywords → role", "role" in bh, True)

# 12. interface keywords
bh = _compute_boundary_hints("the API endpoint and UI")
all_pass &= check("ui/api keywords → interface", "interface" in bh, True)

# 13. data keywords
bh = _compute_boundary_hints("the artifact and state are stored")
all_pass &= check("artifact/state keywords → data", "data" in bh, True)

# 14. Multiple hints
bh = _compute_boundary_hints("the plugin module exposes an API endpoint for the user")
hints_found = sorted(bh)
expected_multi = sorted(["module", "interface", "role"])
all_pass &= check("multi hint", hints_found, expected_multi)

# 15. No matches → unknown
bh = _compute_boundary_hints("hello world")
all_pass &= check("no matches → unknown", bh, ["unknown"])

# 16. Empty → unknown
bh = _compute_boundary_hints("")
all_pass &= check("empty → unknown", bh, ["unknown"])

print()
if all_pass:
    print(f"{PASS} All checks passed")
    sys.exit(0)
else:
    print(f"{FAIL} Some checks failed")
    sys.exit(1)
