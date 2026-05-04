"""
weslr/commands/collaboration_commands.py
=========================================
Phase 10 — Collaboration commands:
  /workspace share <hypothesis_id>
  /workspace library list
  /workspace import <shared_hypothesis_id>
  /jupyter info
  /explain hypothesis <id>
  /explain cause <cause> <effect>
  /explain abduce <observation>

Author: OCC (WESLR governed intelligence) — Phase 10
"""

from __future__ import annotations

import re
from typing import Optional

from ..modules.hypothesis_repository import HypothesisRepository
from ..modules.workspace import WorkspaceManager, SHARED_HYPOTHESES
from ..modules.explanation_generator import (
    explain_hypothesis,
    explain_hypothesis_by_id,
    explain_causal_link,
    explain_abduction,
)
from ..modules.abductive_reasoner import AbductiveReasoner

# ── Module-level managers ─────────────────────────────────────────────────

_WS_MANAGER: Optional[WorkspaceManager] = None
_ABDUCTIVE: Optional[AbductiveReasoner] = None


def _ws() -> WorkspaceManager:
    global _WS_MANAGER
    if _WS_MANAGER is None:
        from ..modules.hypothesis_repository import get_current_tenant_id
        _WS_MANAGER = WorkspaceManager(tenant_id=get_current_tenant_id())
    return _WS_MANAGER


def _repo():
    from .hypothesis_commands import _repo as _h_repo
    return _h_repo()


# ── /workspace commands ─────────────────────────────────────────────────────

async def handle_workspace_command(message: str, lowered: str) -> str:
    """Route /workspace sub-commands."""
    if _match(lowered, ("/workspace share", "workspace share")):
        return _handle_workspace_share(message, lowered)
    if _match(lowered, ("/workspace library list", "workspace library list")):
        return _handle_workspace_library_list(lowered)
    if _match(lowered, ("/workspace import", "workspace import")):
        return _handle_workspace_import(message, lowered)
    if _match(lowered, ("/workspace", "workspace")):
        return _workspace_help()
    return _unknown("workspace")


def _handle_workspace_share(message: str, lowered: str) -> str:
    """Handle /workspace share <hypothesis_id>"""
    # Extract hypothesis ID
    m = re.search(r"\b[\w\-]{20,}\b", lowered)
    if not m:
        return "Usage: /workspace share <hypothesis_id>"
    hid = m.group(0)
    repo = _repo()
    h = repo.get(hid)
    if h is None:
        return f"Hypothesis '{hid}' not found in your workspace."

    ws = _ws()
    shared_id = ws.share_hypothesis(h)

    return (
        f"Hypothesis '{hid}' shared to library.\n"
        f"Library ID: {shared_id}"
    )


def _handle_workspace_library_list(lowered: str) -> str:
    """Handle /workspace library list [domain]"""
    domain = None
    for prefix in ("/workspace library list ", "workspace library list "):
        if lowered.startswith(prefix):
            domain = lowered[len(prefix):].strip() or None
            break

    ws = _ws()
    entries = ws.list_shared_library(domain=domain)

    if not entries:
        if domain:
            return f"No shared hypotheses in domain '{domain}'."
        return "Shared library is empty."

    lines = ["Shared Library", "=" * 60]
    for entry in entries:
        title = entry.get("title", "Untitled")
        shared_id = entry.get("shared_id", "?")
        domain = entry.get("domain", "unknown")
        confidence = entry.get("confidence", 0.0)
        lines.append(
            f"[{shared_id[:16]}] {title} "
            f"(domain={domain}, confidence {confidence:.2f})"
        )
    return "\n".join(lines)


def _handle_workspace_import(message: str, lowered: str) -> str:
    """Handle /workspace import <shared_hypothesis_id>"""
    m = re.search(r"\b[\w\-]{20,}\b", lowered)
    if not m:
        return "Usage: /workspace import <shared_hypothesis_id>"
    shared_id = m.group(0)

    ws = _ws()
    imported = ws.import_from_library(shared_id)
    if imported is None:
        return f"Shared hypothesis '{shared_id}' not found in library."

    # Add to tenant's repository
    from ..modules.hypothesis_repository import Hypothesis
    h = Hypothesis(
        title=imported["title"],
        description=imported["description"],
        domain=imported.get("domain", "mixed"),
        confidence=imported.get("confidence", 0.5),
        status="draft",
        provenance=imported.get("provenance", []),
        metadata=imported.get("metadata", {}),
    )
    repo = _repo()
    stored = repo.add(h)

    return (
        f"Imported from library as new hypothesis: {stored.id}\n"
        f"Title: {stored.title}\n"
        f"Status: {stored.status}  |  Confidence: {stored.confidence:.2f}"
    )


def _workspace_help() -> str:
    return (
        "/workspace — Collaboration commands\n"
        "Usage:\n"
        "  /workspace share <hypothesis_id>   — share a hypothesis to the library\n"
        "  /workspace library list            — list all shared hypotheses\n"
        "  /workspace import <shared_id>      — import a shared hypothesis\n"
    )


# ── /jupyter commands ──────────────────────────────────────────────────────

async def handle_jupyter_command(message: str, lowered: str) -> str:
    """Route /jupyter commands."""
    if _match(lowered, ("/jupyter info", "jupyter info")):
        return _handle_jupyter_info(lowered)
    if _match(lowered, ("/jupyter", "jupyter")):
        return _handle_jupyter_info(lowered)
    return _unknown("jupyter")


def _handle_jupyter_info(lowered: str) -> str:
    """Handle /jupyter info — print connection instructions."""
    from ..jupyter_kernel_stub import print_info
    return print_info()


# ── /explain commands ──────────────────────────────────────────────────────

async def handle_explain_command(message: str, lowered: str) -> str:
    """Route /explain sub-commands."""
    if lowered.startswith("/explain hypothesis ") or lowered.startswith("explain hypothesis "):
        return _handle_explain_hypothesis(message, lowered)
    if lowered.startswith("/explain cause ") or lowered.startswith("explain cause "):
        return _handle_explain_cause(message, lowered)
    if lowered.startswith("/explain abduce ") or lowered.startswith("explain abduce "):
        return _handle_explain_abduce(message, lowered)
    if _match(lowered, ("/explain", "explain")):
        return _explain_help()
    return _unknown("explain")


def _handle_explain_hypothesis(message: str, lowered: str) -> str:
    """Handle /explain hypothesis <id>"""
    # Extract hypothesis ID (last long token in the command)
    m = re.search(r"\b[\w\-]{20,}\b", lowered)
    if not m:
        return "Usage: /explain hypothesis <hypothesis_id>"
    hid = m.group(0)
    repo = _repo()
    return explain_hypothesis_by_id(hid, repo)


def _handle_explain_cause(message: str, lowered: str) -> str:
    """Handle /explain cause <cause> <effect>"""
    # Extract two quoted or long tokens
    tokens = lowered.split()
    # Find the two concepts after "explain cause"
    parts = message.split("cause")[1].strip() if "cause" in message else ""
    if not parts:
        return "Usage: /explain cause <cause_concept> <effect_concept>"
    parts = parts.split(None, 1)
    if len(parts) < 2:
        return "Usage: /explain cause <cause_concept> <effect_concept>"
    cause, effect = parts[0], parts[1]
    # Look up causal link in hypothesis repository
    # Default confidence if not found
    confidence = 0.5
    repo = _repo()
    active = repo.get_active()
    if active:
        cg = active.metadata.get("causal_graph", {})
        for (c, e), conf in cg.items():
            if c == cause and e == effect:
                confidence = conf
                break
    return explain_causal_link(cause, effect, confidence)


def _handle_explain_abduce(message: str, lowered: str) -> str:
    """Handle /explain abduce <observation>"""
    # Extract the observation text after "abduce"
    abduce_match = re.search(r"abduce\s+(.+)$", lowered)
    if not abduce_match:
        return "Usage: /explain abduce <observation text>"
    observation = abduce_match.group(1).strip()
    if not observation:
        return "Usage: /explain abduce <observation text>"

    # Run abduction
    from ..modules.abductive_reasoner import AbductiveReasoner
    ab = AbductiveReasoner()
    ab.add_observation(observation)
    results = ab.get_explanations(max_explanations=1)

    if not results:
        return explain_abduction(
            observation=observation,
            explanation="No explanation could be derived from current rules.",
        )

    best = results[0]
    explanation = best.get("explanation", str(best))
    alt_results = ab.get_explanations(max_explanations=2)
    alternative = alt_results[1].get("explanation") if len(alt_results) > 1 else None

    return explain_abduction(observation, explanation, alternative=alternative)


def _explain_help() -> str:
    return (
        "/explain — Hypothesis explanation commands\n"
        "Usage:\n"
        "  /explain hypothesis <id>   — narrative explanation of a hypothesis\n"
        "  /explain cause <cause> <effect>  — explain a causal link\n"
        "  /explain abduce <observation>    — explain an observation via abduction\n"
    )


# ── Routing entrypoint ──────────────────────────────────────────────────────

async def handle_collaboration_command(message: str, lowered: str) -> str:
    """Top-level router for Phase 10 collaboration commands.

    Handles /workspace, /jupyter, and /explain commands.
    Returns help text for unknown sub-commands.
    """
    if lowered.startswith("/workspace") or lowered.startswith("workspace"):
        return await handle_workspace_command(message, lowered)
    if lowered.startswith("/jupyter") or lowered.startswith("jupyter"):
        return await handle_jupyter_command(message, lowered)
    if lowered.startswith("/explain") or lowered.startswith("explain"):
        return await handle_explain_command(message, lowered)
    return _collaboration_help()


def _collaboration_help() -> str:
    return (
        "Collaboration commands:\n"
        "  /workspace share <id>   — share a hypothesis to the library\n"
        "  /workspace library list — view all shared hypotheses\n"
        "  /workspace import <id>  — import a shared hypothesis\n"
        "  /jupyter info            — Jupyter stub connection info\n"
        "  /explain hypothesis <id> — explain a hypothesis\n"
        "  /explain cause <c> <e>   — explain a causal link\n"
        "  /explain abduce <obs>    — explain via abduction\n"
    )


# ── Internal helpers ────────────────────────────────────────────────────────

def _match(lowered: str, prefixes: tuple[str, ...]) -> bool:
    return any(lowered.startswith(p) for p in prefixes)


def _unknown(cmd: str) -> str:
    return f"Unknown /{cmd} command. Type /{cmd} for help."