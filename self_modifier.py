# self_modifier.py - Weslr proposes its own code changes
# LEGACY/EXPERIMENTAL: Not the canonical improvement/governance lane.
# Canonical lane: adequacy → CDI proposal (with lineage/evidence) → operator approve/deny/refine → execution eligibility (governed).
# Keep this isolated; do not treat as protected-core improvement.
from __future__ import annotations

import time
from pathlib import Path


PROTECTED_FILES = {
    "main.py",
    "sim.py",
    "agent_runtime.py",
    "llm_runtime.py",
    "continuity.py",
    "relational.py",
    "perception.py",
}

PROTECTED_PATHS = {
    "Weslr/agents/",
    "Weslr/dashboard/",
    "Weslr/models/",
    "Weslr/docs/",
}


def is_protected_file(filepath: str) -> bool:
    """Check if a file is protected from modification."""
    filename = Path(filepath).name
    if filename in PROTECTED_FILES:
        return True
    for protected in PROTECTED_PATHS:
        if filepath.startswith(protected):
            return True
    return False


def propose_self_modification(file_path: str, change_description: str, rationale: str) -> dict:
    """Propose a self-modification with full context."""
    file_path = str(file_path).strip()
    change_description = str(change_description).strip()
    rationale = str(rationale).strip()

    if not file_path or not change_description or not rationale:
        return {
            "ok": False,
            "error": "Missing required fields: file_path, change_description, and rationale are required.",
        }

    # Check if file is protected
    if is_protected_file(file_path):
        return {
            "ok": False,
            "error": f"Protected file: {file_path}. You must override manually to modify this file.",
            "protected": True,
        }

    # Get current file content (read-only)
    circleforge_dir = Path(__file__).parent
    full_path = circleforge_dir / file_path

    if not full_path.exists():
        return {
            "ok": False,
            "error": f"File not found: {full_path}",
        }

    try:
        with open(full_path, "r", encoding="utf-8") as f:
            current_content = f.read()
    except Exception as e:
        return {
            "ok": False,
            "error": f"Could not read file: {e}",
        }

    # Generate a proposed change (textual, not applied yet)
    # In Phase 4, this would eventually use LLM to generate a real diff
    proposed_change = f"// TODO: Auto-generated change for {change_description}\n// Rationale: {rationale}\n"

    return {
        "ok": True,
        "file_path": file_path,
        "change_description": change_description,
        "rationale": rationale,
        "current_size": len(current_content),
        "proposed_addition": proposed_change,
        "protected": False,
        "generated_at": int(time.time()),
    }


def generate_diff_proposal(current: str, proposed: str, file_path: str) -> dict:
    """Generate a unified diff-style proposal."""
    current_lines = current.splitlines()
    proposed_lines = (proposed + "\n" + current).splitlines()

    # Simple diff: find first line that differs
    diff_lines = []
    for i, (c, p) in enumerate(zip(current_lines, proposed_lines)):
        if c != p:
            diff_lines.append(f"- {c}")
            diff_lines.append(f"+ {p}")
            break

    return {
        "file": file_path,
        "diff": diff_lines[:10] if diff_lines else ["No changes detected"],
        "proposed": proposed,
        "current_length": len(current),
        "proposed_length": len(proposed + current),
    }


def propose_improvement(need: str) -> dict:
    """Propose a self-improvement based on a need."""
    need = str(need).strip()

    if not need:
        return {
            "ok": False,
            "error": "No need specified. Example: 'I need to read web pages faster' or 'I want better error messages'.",
        }

    # Heuristic: match common needs to likely files
    proposals = {
        "web pages": {
            "file": "config.py",
            "change": "Increase READ_TIMEOUT_SECONDS from 20 to 30 for better reliability on slow connections.",
            "rationale": "Some web pages take longer to load. Increasing timeout prevents premature failures.",
        },
        "timeout": {
            "file": "config.py",
            "change": "Add READ_TIMEOUT_SECONDS = 30 to allow longer web fetch times.",
            "rationale": "Current hardcoded timeout may be too short for some use cases.",
        },
        "logging": {
            "file": "config.py",
            "change": "Add DEBUG_LOGGING = True to enable verbose output for troubleshooting.",
            "rationale": "Better logging helps diagnose issues during development.",
        },
        "speed": {
            "file": "config.py",
            "change": "Reduce CODE_TIMEOUT_SECONDS from 60 to 30 to catch slow operations faster.",
            "rationale": "Shorter timeouts help identify bottlenecks earlier.",
        },
        "output": {
            "file": "config.py",
            "change": "Increase MAX_STDOUT_CHARS from 12000 to 24000 for larger outputs.",
            "rationale": "Some operations generate more output than the current limit allows.",
        },
    }

    # Find best match
    for key, proposal in proposals.items():
        if key in need.lower():
            return {
                "ok": True,
                "need": need,
                "best_match": key,
                "proposed": {
                    "file_path": proposal["file"],
                    "change_description": proposal["change"],
                    "rationale": proposal["rationale"],
                },
                "generated_at": int(time.time()),
            }

    # Generic proposal
    return {
        "ok": True,
        "need": need,
        "best_match": None,
        "proposed": {
            "file_path": "config.py",
            "change_description": "Review current configuration and add relevant settings.",
            "rationale": f"Current configuration doesn't seem to address this need: '{need}'.",
        },
        "generated_at": int(time.time()),
    }


def build_proposal_report(need: str) -> dict:
    """Full workflow: propose improvement → generate diff → return report."""
    improvement = propose_improvement(need)
    if not improvement.get("ok"):
        return improvement

    file_path = improvement["proposed"]["file_path"]
    change_desc = improvement["proposed"]["change_description"]
    rationale = improvement["proposed"]["rationale"]

    # Get current content for diff
    circleforge_dir = Path(__file__).parent
    full_path = circleforge_dir / file_path

    try:
        with open(full_path, "r", encoding="utf-8") as f:
            current_content = f.read()
    except Exception as e:
        return {
            "ok": False,
            "error": f"Could not read file for diff: {e}",
        }

    # Generate diff-style proposal
    diff_proposal = generate_diff_proposal(
        current_content,
        f"# Improvement proposal: {change_desc}\n# Rationale: {rationale}\n",
        file_path,
    )

    return {
        "ok": True,
        "need": need,
        "improvement": improvement,
        "diff": diff_proposal,
        "generated_at": int(time.time()),
    }


def propose_self_modification_report(file_path: str, change: str, rationale: str) -> dict:
    """Public interface: propose a specific self-modification."""
    proposal = propose_self_modification(file_path, change, rationale)

    if not proposal.get("ok"):
        return proposal

    # Get current content
    circleforge_dir = Path(__file__).parent
    full_path = circleforge_dir / file_path

    try:
        with open(full_path, "r", encoding="utf-8") as f:
            current_content = f.read()
    except Exception as e:
        return {
            "ok": False,
            "error": f"Could not read file: {e}",
        }

    # Generate diff
    diff = generate_diff_proposal(current_content, change, file_path)

    return {
        "ok": True,
        "file_path": file_path,
        "change_description": change,
        "rationale": rationale,
        "protected": False,
        "diff": diff,
        "generated_at": int(time.time()),
    }
