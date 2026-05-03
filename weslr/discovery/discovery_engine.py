"""Generic discovery engine for rule-based candidate generation across domains."""

from __future__ import annotations
import json
import random
from pathlib import Path
from typing import Any, Dict, List, Optional

# Base path for domain configs
DOMAIN_CONFIGS = Path(__file__).parent / "domain_configs"

# Time-series keywords that trigger temporal pattern detection
TEMPORAL_KEYWORDS = {
    "trend", "forecast", "sales", "temperature", "time series",
    "daily", "monthly", "seasonal", "seasonality", "stock", "price",
    "revenue", "quarterly", "annual", "index", "growth", "decline",
    "sequence", "temporal", "time-series", "timeseries",
}

def load_domain(domain_name: str) -> Dict[str, Any]:
    """Load building blocks and transformation rules for a domain."""
    domain_dir = DOMAIN_CONFIGS / domain_name
    config = {
        "domain": domain_name,
        "domain_dir": str(domain_dir),
    }

    # Load building blocks
    blocks_file = domain_dir / "building_blocks.json"
    if blocks_file.exists():
        with open(blocks_file) as f:
            config["building_blocks"] = json.load(f)
    else:
        config["building_blocks"] = {}

    # Load transformation rules
    rules_file = domain_dir / "transformation_rules.json"
    if rules_file.exists():
        with open(rules_file) as f:
            config["rules"] = json.load(f).get("rules", [])
    else:
        config["rules"] = []

    return config

def get_available_domains() -> List[str]:
    """Return list of domain names that have configs."""
    if not DOMAIN_CONFIGS.exists():
        return []
    return [d.name for d in DOMAIN_CONFIGS.iterdir() if d.is_dir() and (d / "building_blocks.json").exists()]


def detect_temporal_patterns_for_dataset(dataset_name: str) -> dict:
    """Run temporal analysis on a named dataset and return pattern annotations.

    Uses the temporal_commands registry to locate the dataset series,
    then runs temporal reasoning to detect trend, seasonality, and stationarity.

    Returns an empty dict if the dataset is not registered or temporal
    reasoning is unavailable.
    """
    try:
        from weslr.commands.temporal_commands import _DATASETS
        from weslr.modules.temporal_reasoning import detect_temporal_patterns
    except ImportError:
        return {}

    if dataset_name not in _DATASETS:
        return {}

    series = _DATASETS[dataset_name]
    patterns = detect_temporal_patterns(series)

    return {
        "trend_direction": patterns.trend_direction,
        "trend_label": {1: "upward", -1: "downward", 0: "flat"}.get(
            patterns.trend_direction, "unknown"
        ),
        "seasonality_present": patterns.seasonality_present,
        "seasonality_period": patterns.seasonality_period,
        "stationarity": patterns.stationarity_via_adf,
    }


def _contains_temporal_keyword(fact: Dict[str, Any]) -> bool:
    """Return True if any field of the fact contains a temporal keyword."""
    text = (
        str(fact.get("subject", "")) + " " +
        str(fact.get("predicate", "")) + " " +
        str(fact.get("object", ""))
    ).lower()
    return any(kw in text for kw in TEMPORAL_KEYWORDS)


def _dataset_name_from_fact(fact: Dict[str, Any]) -> Optional[str]:
    """Extract a plausible dataset name from a fact, or None."""
    # Try to find a field that looks like a dataset identifier
    for field in ("subject", "object", "source"):
        val = str(fact.get(field, ""))
        # Heuristic: dataset names are often lowercase with underscores or dashes
        if "_" in val or "-" in val:
            return val
    return None


def generate_candidates(
    domain: str,
    existing_facts: Optional[List[Dict[str, Any]]] = None,
    min_trust: float = 0.5,
    limit: int = 20,
    seed: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Generate novel candidates by applying transformation rules to high-trust entities.

    Args:
        domain: domain name (e.g., "nanotechnology", "chemistry")
        existing_facts: list of fact dicts from the fact store (optional)
        min_trust: minimum trust score for entities to use as parents
        limit: max candidates to return
        seed: random seed for reproducibility

    Returns:
        list of candidate dicts with: name, description, transformation, parent,
        provenance, confidence, candidate_score.  When existing_facts contain
        time-series keywords, temporal pattern annotations are attached to
        candidates that reference a registered dataset.
    """
    if seed is not None:
        random.seed(seed)

    config = load_domain(domain)
    blocks = config.get("building_blocks", {})
    rules = config.get("rules", [])

    if not rules:
        return []

    candidates = []

    # Build parent entities from existing facts if provided
    # Otherwise use bootstrapped building block instances
    if existing_facts:
        parent_entities = _build_parents_from_facts(existing_facts, min_trust, blocks)
    else:
        parent_entities = _bootstrap_parents(blocks)

    # Detect whether the incoming facts contain time-series data
    has_temporal = existing_facts and any(_contains_temporal_keyword(f) for f in existing_facts)

    # Collect temporal annotations from all registered datasets once
    temporal_annotations: Dict[str, dict] = {}
    if has_temporal:
        try:
            from weslr.commands.temporal_commands import _DATASETS
            from weslr.modules.temporal_reasoning import detect_temporal_patterns

            for ds_name in _DATASETS:
                patterns = detect_temporal_patterns(_DATASETS[ds_name])
                temporal_annotations[ds_name] = {
                    "trend_direction": patterns.trend_direction,
                    "trend_label": {1: "upward", -1: "downward", 0: "flat"}.get(
                        patterns.trend_direction, "unknown"
                    ),
                    "seasonality_present": patterns.seasonality_present,
                    "seasonality_period": patterns.seasonality_period,
                    "stationarity": patterns.stationarity_via_adf,
                }
        except ImportError:
            has_temporal = False

    # Apply each rule
    for rule in rules:
        rule_name = rule.get("name", "unnamed")
        rule_confidence = rule.get("confidence", 0.5)

        for parent in parent_entities:
            result = _apply_rule(rule, parent, blocks)
            if result:
                candidate = {
                    "name": result.get("name", f"candidate_{len(candidates)}"),
                    "description": result.get("description", ""),
                    "transformation": rule_name,
                    "parent": parent.get("name", "unknown"),
                    "parent_trust": parent.get("trust", 0.5),
                    "provenance": result.get("provenance", f"Rule: {rule_name}"),
                    "confidence": rule_confidence,
                    "candidate_score": round((parent.get("trust", 0.5) + rule_confidence) / 2, 3),
                    "domain": domain,
                }
                candidate.update(result)

                # Attach temporal annotations when facts contain time-series keywords
                if has_temporal and temporal_annotations:
                    # Try to match the candidate's parent or name to a known dataset
                    parent_name = parent.get("name", "")
                    for ds_name, annotation in temporal_annotations.items():
                        if ds_name in parent_name or parent_name in ds_name:
                            candidate["temporal_pattern"] = annotation
                            break
                    # Fallback: attach all annotations as metadata when any dataset matches
                    if "temporal_pattern" not in candidate:
                        # Check if any annotation key appears in the candidate name/description
                        for ds_name, annotation in temporal_annotations.items():
                            if ds_name in candidate.get("name", "") or ds_name in candidate.get("description", ""):
                                candidate["temporal_pattern"] = annotation
                                break

                candidates.append(candidate)

    # Deduplicate by name
    seen = set()
    unique = []
    for c in candidates:
        if c["name"] not in seen:
            seen.add(c["name"])
            unique.append(c)

    return unique[:limit]


def _build_parents_from_facts(facts: List[Dict], min_trust: float, blocks: Dict) -> List[Dict]:
    """Build parent entities from fact store facts."""
    parents = []
    for f in facts:
        trust = f.get("trust_score", f.get("confidence", 0.5))
        if trust < min_trust:
            continue
        subj = f.get("subject", "")
        if subj and len(subj) > 1:
            parents.append({
                "name": subj,
                "trust": trust,
                "predicate": f.get("predicate", ""),
                "source": "fact_store",
            })
    # Deduplicate by name
    seen = set()
    for p in parents:
        if p["name"] not in seen:
            seen.add(p["name"])
    return [{"name": p["name"], "trust": p["trust"]} for p in parents if p["name"] not in seen]


def _bootstrap_parents(blocks: Dict) -> List[Dict]:
    """Build parent entities from building blocks (when no fact store data)."""
    parents = []
    for category, values in blocks.items():
        if isinstance(values, list):
            for v in values:
                if isinstance(v, dict) and "name" in v:
                    parents.append({"name": v["name"], "trust": v.get("trust", 0.7), "category": category})
                elif isinstance(v, str):
                    parents.append({"name": v, "trust": 0.7, "category": category})
    return parents


def _apply_rule(rule: Dict, parent: Dict, blocks: Dict) -> Optional[Dict]:
    """Apply a single rule to a parent entity. Returns candidate dict or None."""
    rule_type = rule.get("type", "substitution")

    if rule_type == "substitution":
        return _apply_substitution_rule(rule, parent, blocks)
    elif rule_type == "combination":
        return _apply_combination_rule(rule, parent, blocks)
    elif rule_type == "addition":
        return _apply_addition_rule(rule, parent, blocks)
    return None


def _apply_substitution_rule(rule: Dict, parent: Dict, blocks: Dict) -> Optional[Dict]:
    """Apply a substitution rule: replace X with Y."""
    description = rule.get("description", "Substitution")
    from_list = rule.get("from_values", [])
    to_values = rule.get("to_values", [])

    if not from_list or not to_values:
        return None

    # Pick a random from/to pair
    from_val = random.choice(from_list) if isinstance(from_list, list) else from_list
    to_val = random.choice(to_values) if isinstance(to_values, list) else to_values

    parent_name = parent.get("name", "")

    # Simple string substitution in parent name
    new_name = parent_name.replace(from_val, to_val) if from_val in parent_name else f"{parent_name}_{to_val}"

    return {
        "name": new_name,
        "description": f"{description}: {from_val} → {to_val} in {parent_name}",
        "provenance": f"Substituted {from_val} with {to_val} ({rule.get('name')})",
        "transformation_detail": {"from": from_val, "to": to_val, "parent": parent_name},
    }


def _apply_combination_rule(rule: Dict, parent: Dict, blocks: Dict) -> Optional[Dict]:
    """Apply a combination rule: combine two components."""
    description = rule.get("description", "Combination")
    combine_with = rule.get("combine_with", [])

    if not combine_with:
        return None

    parent_name = parent.get("name", "")
    partner = random.choice(combine_with) if isinstance(combine_with, list) else combine_with

    # Create combined name
    separators = ["_", "-", "+"]
    sep = random.choice(separators)
    new_name = f"{parent_name}{sep}{partner}"

    return {
        "name": new_name,
        "description": f"{description}: {parent_name} + {partner}",
        "provenance": f"Combined {parent_name} with {partner} ({rule.get('name')})",
        "transformation_detail": {"component_a": parent_name, "component_b": partner},
    }


def _apply_addition_rule(rule: Dict, parent: Dict, blocks: Dict) -> Optional[Dict]:
    """Apply an addition rule: add a component."""
    description = rule.get("description", "Addition")
    add_values = rule.get("add_values", [])

    if not add_values:
        return None

    parent_name = parent.get("name", "")
    add_val = random.choice(add_values) if isinstance(add_values, list) else add_values

    new_name = f"{parent_name}_{add_val}"

    return {
        "name": new_name,
        "description": f"{description}: add {add_val} to {parent_name}",
        "provenance": f"Added {add_val} to {parent_name} ({rule.get('name')})",
        "transformation_detail": {"parent": parent_name, "added": add_val},
    }


def rank_candidates(candidates: List[Dict], metric: str = "candidate_score") -> List[Dict]:
    """Rank candidates by the specified metric (descending)."""
    return sorted(candidates, key=lambda c: c.get(metric, 0), reverse=True)


def format_discovery_result(domain: str, candidates: List[Dict], limit: int = 10) -> str:
    """Format a discovery result for display."""
    if not candidates:
        return f"No candidates generated for domain '{domain}'. Check that the domain config exists."

    lines = [
        f"Discovery: {domain} (top {min(limit, len(candidates))} of {len(candidates)} candidates)",
        "",
    ]

    for i, c in enumerate(candidates[:limit], 1):
        lines.append(f"{i}. **{c.get('name', 'unnamed')}**")
        desc = c.get("description", "")
        if desc:
            lines.append(f"   {desc}")
        prov = c.get("provenance", "")
        if prov:
            lines.append(f"   Provenance: {prov}")
        score = c.get("candidate_score", c.get("confidence", 0))
        lines.append(f"   Score: {score:.3f}  (rule conf={c.get('confidence', 0):.2f}, parent trust={c.get('parent_trust', 0):.2f})")

        # Include temporal pattern annotations if present
        if "temporal_pattern" in c:
            tp = c["temporal_pattern"]
            lines.append(
                f"   Temporal: trend={tp.get('trend_label','?')}  "
                f"seasonality={'yes' if tp.get('seasonality_present') else 'no'}  "
                f"period={tp.get('seasonality_period','?')}  "
                f"stationary={'yes' if tp.get('stationarity') else 'no'}"
            )
        lines.append("")

    lines.append(f"[{len(candidates)} total candidates for {domain}]")
    return "\n".join(lines)