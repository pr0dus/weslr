"""Self-improvement hook for discovery engine — learn frequent refinement sequences."""

from __future__ import annotations
import json
from collections import defaultdict
from pathlib import Path
from typing import Optional

_SELF_IMPROVEMENT_DIR = Path(__file__).parent.parent / ".self_improvement"
_SELF_IMPROVEMENT_DIR.mkdir(exist_ok=True)
_REFINE_COUNTS_FILE = _SELF_IMPROVEMENT_DIR / "refinement_sequences.json"
_PROPOSED_RULES_FILE = _SELF_IMPROVEMENT_DIR / "proposed_rules.json"
_MIN_SEQUENCE_COUNT = 3  # Propose rule after 3 identical sequences

def _load_refine_counts() -> dict:
    if _REFINE_COUNTS_FILE.exists():
        with open(_REFINE_COUNTS_FILE) as f:
            return json.load(f)
    return {}

def _save_refine_counts(counts: dict):
    with open(_REFINE_COUNTS_FILE, "w") as f:
        json.dump(counts, f, indent=2)

def record_refinement_sequence(domain: str, sequence: list[str]) -> Optional[dict]:
    """Record a refinement sequence (list of rule names). If count >= MIN_SEQUENCE_COUNT,
    return a proposed combined rule."""
    counts = _load_refine_counts()
    key = f"{domain}:{'->'.join(sequence)}"
    counts[key] = counts.get(key, 0) + 1
    _save_refine_counts(counts)

    if counts[key] == _MIN_SEQUENCE_COUNT:
        # Propose a combined rule
        rule_name = f"combined_{sequence[0]}_then_{sequence[-1]}"
        proposed = {
            "rule_id": f"learned.{rule_name}",
            "description": f"Combined rule from frequent sequence: {' -> '.join(sequence)}",
            "sequence": sequence,
            "count": counts[key],
            "domain": domain,
            "confidence": 0.6,  # Lower confidence for learned rules
        }

        # Save proposed rule
        proposed_rules = {}
        if _PROPOSED_RULES_FILE.exists():
            with open(_PROPOSED_RULES_FILE) as f:
                proposed_rules = json.load(f)
        proposed_rules[rule_name] = proposed
        with open(_PROPOSED_RULES_FILE, "w") as f:
            json.dump(proposed_rules, f, indent=2)

        return proposed

    return None

def get_proposed_rules() -> dict:
    """Return all proposed rules from frequent sequences."""
    if _PROPOSED_RULES_FILE.exists():
        with open(_PROPOSED_RULES_FILE) as f:
            return json.load(f)
    return {}

def format_proposed_rules() -> str:
    """Format proposed rules for display."""
    rules = get_proposed_rules()
    if not rules:
        return "No learned rules yet. Refinements are tracked after 3 identical sequences."

    lines = ["Proposed combined rules (from frequent refinement sequences):", ""]
    for name, rule in rules.items():
        lines.append(f"  {name}: {rule['description']}")
        lines.append(f"    Domain: {rule['domain']}, Sequence: {' -> '.join(rule['sequence'])}, Count: {rule['count']}")
        lines.append("")

    return "\n".join(lines)
