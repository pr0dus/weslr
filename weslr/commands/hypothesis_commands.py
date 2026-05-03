"""
weslr/commands/hypothesis_commands.py
======================================
Phase 7 — Hypothesis workflow commands: /hypothesis, /experiment, /scenario, /report.

Author: OCC (WESLR governed intelligence) — Phase 7
"""

from __future__ import annotations

import re
import uuid
from typing import Optional

from ..modules.hypothesis_repository import (
    Hypothesis,
    HypothesisRepository,
)
from ..modules.experiment_suggester import ExperimentSuggester
from ..modules.scenario_explorer import ScenarioExplorer
from ..modules.report_generator import ReportGenerator

# ── Module-level repository (shared across command calls) ───────────────────

_REPO: Optional[HypothesisRepository] = None
_SUGGESTER: Optional[ExperimentSuggester] = None
_EXPLORER: Optional[ScenarioExplorer] = None
_REPORT_GENERATOR: Optional[ReportGenerator] = None


def _repo() -> HypothesisRepository:
    global _REPO
    if _REPO is None:
        _REPO = HypothesisRepository()
    return _REPO


def _suggester() -> ExperimentSuggester:
    global _SUGGESTER
    if _SUGGESTER is None:
        _SUGGESTER = ExperimentSuggester()
    return _SUGGESTER


def _explorer() -> ScenarioExplorer:
    global _EXPLORER
    if _EXPLORER is None:
        _EXPLORER = ScenarioExplorer()
    return _EXPLORER


def _report_gen() -> ReportGenerator:
    global _REPORT_GENERATOR
    if _REPORT_GENERATOR is None:
        _REPORT_GENERATOR = ReportGenerator()
    return _REPORT_GENERATOR


# ── Command handlers ─────────────────────────────────────────────────────────

async def handle_hypothesis_command(message: str, lowered: str) -> str:
    """Route /hypothesis commands."""
    if _match(lowered, ("/hypothesis new", "hypothesis new")):
        return _handle_hypothesis_new(message, lowered)
    if _match(lowered, ("/hypothesis list", "hypothesis list")):
        return _handle_hypothesis_list(lowered)
    if _match(lowered, ("/hypothesis show", "hypothesis show")):
        return _handle_hypothesis_show(lowered)
    if _match(lowered, ("/hypothesis compare", "hypothesis compare")):
        return _handle_hypothesis_compare(lowered)
    if _match(lowered, ("/hypothesis promote", "hypothesis promote")):
        return _handle_hypothesis_promote(lowered)
    if _match(lowered, ("/hypothesis delete", "hypothesis delete")):
        return _handle_hypothesis_delete(lowered)
    if _match(lowered, ("/hypothesis", "hypothesis")):
        return _handle_hypothesis_help()
    return _unknown("hypothesis")


async def handle_experiment_command(message: str, lowered: str) -> str:
    """Route /experiment commands."""
    if _match(lowered, ("/experiment suggest", "experiment suggest")):
        return _handle_experiment_suggest()
    return _unknown("experiment")


async def handle_scenario_command(message: str, lowered: str) -> str:
    """Route /scenario commands."""
    if lowered.startswith("/scenario explore ") or lowered.startswith("scenario explore "):
        return _handle_scenario_explore(lowered)
    if _match(lowered, ("/scenario", "scenario")):
        return _scenario_help()
    return _unknown("scenario")


async def handle_report_command(message: str, lowered: str) -> str:
    """Route /report commands."""
    if lowered.startswith("/report generate ") or lowered.startswith("report generate "):
        return _handle_report_generate(message, lowered)
    if _match(lowered, ("/report", "report generate")):
        return _handle_report_generate(message, "report generate")
    return _unknown("report")


# ── Hypothesis sub-handlers ──────────────────────────────────────────────────

def _handle_hypothesis_new(message: str, lowered: str) -> str:
    """Handle /hypothesis new [title] [description]"""
    # Strip command prefix and parse remaining text
    for prefix in ("/hypothesis new ", "hypothesis new ", "/hypothesis new", "hypothesis new"):
        if lowered.startswith(prefix):
            body = message[len(prefix):].strip()
            break
    else:
        return "Usage: /hypothesis new <title> [description]"

    parts = body.split(None, 1)
    if not parts:
        return "Usage: /hypothesis new <title> [description]"
    title = parts[0]
    description = parts[1] if len(parts) > 1 else ""

    h = Hypothesis(
        title=title,
        description=description,
        provenance=[{
            "source": "hypothesis_commands",
            "action": "manual_creation",
            "parameters": {"title": title},
        }],
    )
    repo = _repo()
    repo.add(h)

    return (
        f"Hypothesis created: {h.id}\n"
        f"Title: {h.title}\n"
        f"Status: {h.status}  |  Confidence: {h.confidence:.2f}\n\n"
        f"Use /hypothesis promote {h.id} to set as active."
    )


def _handle_hypothesis_list(lowered: str) -> str:
    """Handle /hypothesis list [status]"""
    status = None
    for prefix in ("/hypothesis list ", "hypothesis list "):
        if lowered.startswith(prefix):
            status = lowered[len(prefix):].strip() or None
            break
    repo = _repo()
    hypotheses = repo.list(status=status)
    return HypothesisRepository.format_list(hypotheses)


def _handle_hypothesis_show(lowered: str) -> str:
    """Handle /hypothesis show <id>"""
    # Extract ID after command
    m = re.search(r"\/hypothesis\s+show\s+(\S+)", lowered)
    if not m:
        m = re.search(r"hypothesis\s+show\s+(\S+)", lowered)
    if not m:
        return "Usage: /hypothesis show <id>"
    hid = m.group(1)
    repo = _repo()
    h = repo.get(hid)
    if h is None:
        return f"Hypothesis '{hid}' not found."
    return HypothesisRepository.format_hypothesis(h)


def _handle_hypothesis_compare(lowered: str) -> str:
    """Handle /hypothesis compare <id1> <id2>"""
    m = re.findall(r"\b[\w\-]{20,}\b", lowered)
    if len(m) < 2:
        return "Usage: /hypothesis compare <id1> <id2>"
    id1, id2 = m[-2], m[-1]
    repo = _repo()
    cmp = repo.compare(id1, id2)
    if cmp is None:
        return f"One or both hypothesis IDs not found: {id1}, {id2}"
    return HypothesisRepository.format_comparison(cmp)


def _handle_hypothesis_promote(lowered: str) -> str:
    """Handle /hypothesis promote <id>"""
    m = re.search(r"\b[\w\-]{20,}\b", lowered)
    if not m:
        return "Usage: /hypothesis promote <id>"
    hid = m.group(0)
    repo = _repo()
    h = repo.get(hid)
    if h is None:
        return f"Hypothesis '{hid}' not found."
    updated = repo.set_active(hid)
    if updated is None:
        return f"Failed to promote '{hid}'."
    active = repo.get_active()
    return f"Active hypothesis set to: {active.id}\nTitle: {active.title}\nStatus: {active.status}"


def _handle_hypothesis_delete(lowered: str) -> str:
    """Handle /hypothesis delete <id>"""
    m = re.search(r"\b[\w\-]{20,}\b", lowered)
    if not m:
        return "Usage: /hypothesis delete <id>"
    hid = m.group(0)
    repo = _repo()
    h = repo.get(hid)
    if h is None:
        return f"Hypothesis '{hid}' not found."
    # Check confirmation in message
    if "confirm" not in lowered:
        return (
            f"Delete hypothesis '{hid}'?\nTitle: {h.title}\n\n"
            f"Use /hypothesis delete {hid} confirm"
        )
    deleted = repo.delete(hid)
    if deleted:
        return f"Deleted hypothesis '{hid}'."
    return f"Failed to delete '{hid}'."


def _handle_hypothesis_help() -> str:
    return (
        "Hypothesis commands:\n"
        "  /hypothesis new <title> [description]\n"
        "  /hypothesis list [status]\n"
        "  /hypothesis show <id>\n"
        "  /hypothesis compare <id1> <id2>\n"
        "  /hypothesis promote <id>\n"
        "  /hypothesis delete <id> [confirm]\n\n"
        "  /experiment suggest\n"
        "  /scenario explore param=value ...\n"
        "  /report generate [id] [format=text|json]"
    )


# ── Experiment suggest ──────────────────────────────────────────────────────

def _handle_experiment_suggest() -> str:
    repo = _repo()
    active = repo.get_active()
    if active is None:
        return "No active hypothesis. Use /hypothesis promote <id> first."
    suggester = _suggester()
    suggestions = suggester.suggest_next_experiments(active)
    return ExperimentSuggester.format_suggestions(suggestions)


# ── Scenario explore ────────────────────────────────────────────────────────

def _handle_scenario_explore(lowered: str) -> str:
    """Handle /scenario explore param=value ..."""
    for prefix in ("/scenario explore ", "scenario explore "):
        if lowered.startswith(prefix):
            body = lowered[len(prefix):].strip()
            break
    else:
        return _scenario_help()

    # Parse key=value pairs
    params: dict = {}
    for token in body.split():
        if "=" in token:
            k, v = token.split("=", 1)
            # Try numeric
            try:
                v = float(v)
                if v.is_integer():
                    v = int(v)
            except ValueError:
                pass
            params[k.strip()] = v

    if not params:
        return _scenario_help()

    repo = _repo()
    active = repo.get_active()
    if active is None:
        return "No active hypothesis. Use /hypothesis promote <id> first."

    explorer = _explorer()
    result = explorer.explore_scenario(active, params)
    return ScenarioExplorer.format_result(result)


def _scenario_help() -> str:
    return (
        "Usage: /scenario explore <param>=<value> ...\n"
        "Example: /scenario explore dose=50 time_horizon=14\n\n"
        "Requires an active hypothesis (/hypothesis promote <id>)"
    )


# ── Report generate ──────────────────────────────────────────────────────────

def _handle_report_generate(message: str, lowered: str) -> str:
    """Handle /report generate [id] [format=text|json]"""
    # Extract id and format
    tokens = lowered.split()
    report_format = "text"
    hid = None

    for tok in tokens[2:]:  # skip "report generate"
        if tok in ("text", "json"):
            report_format = tok
        elif re.match(r"[\w\-]{20,}", tok):
            hid = tok
        else:
            pass  # ignore unknown

    repo = _repo()
    # If no ID given, use active
    if hid is None:
        active = repo.get_active()
        if active is None:
            return "No hypothesis ID given and no active hypothesis."
        h = active
    else:
        h = repo.get(hid)
        if h is None:
            return f"Hypothesis '{hid}' not found."

    gen = _report_gen()
    return gen.generate_report(h, format=report_format)


# ── Utilities ───────────────────────────────────────────────────────────────

def _match(lowered: str, prefixes: tuple[str, ...]) -> bool:
    return any(lowered.startswith(p) for p in prefixes)


def _unknown(cmd: str) -> str:
    return f"Unknown /{cmd} command. Try '/{cmd}' for usage."


# ── Auto-hypothesis creation (called by discovery engine) ──────────────────

def auto_create_hypothesis(
    title: str,
    description: str,
    domain: str,
    confidence: float,
    metadata: Optional[dict] = None,
) -> Hypothesis:
    """Create a draft hypothesis (auto-called by discovery engine)."""
    h = Hypothesis(
        title=title,
        description=description,
        domain=domain,
        confidence=confidence,
        provenance=[{
            "source": "discovery_engine",
            "action": "auto_created_from_discovery",
            "parameters": {"domain": domain},
        }],
        metadata=metadata or {},
    )
    _repo().add(h)
    return h