"""
Entity Query Commands — Phase 4.3

Provides entity-centric queries against fact_assertions.jsonl.
Entities are derived on-the-fly from fact data — no separate entity store.

Authority: read-only. No writes, no hidden learning.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from weslr.entity_schema_registry import (
    DEFAULT_DOMAIN,
    get_entity_schema,
    list_entity_types,
    load_schema,
)
from weslr.fact_extractor import load_facts

# ──────────────────────────────────────────────────────────────────────────────
# Entity Type Detection — Heuristics
# ──────────────────────────────────────────────────────────────────────────────

# Drug compounds: names ending in -mab, -nib, -zumab, -tinib (with hyphen prefix)
_DRUG_HYPHEN_SUFFIX = re.compile(r"-(mab|nib|zumab|tinib|mertinib|platinib)$", re.IGNORECASE)
# Drug compounds: names ending in -ib without hyphen (e.g. Olaparib, Lenvatinib)
_DRUG_IB_SUFFIX = re.compile(r"[a-z]ib$", re.IGNORECASE)
# Protein/gene symbols: 2-10 uppercase letters, optional trailing digit (BRCA1, HER2, KRAS)
_PROTEIN_RE = re.compile(r"^[A-Z]{2,10}[0-9]?$")
# Biomarker: hyphenated with digit/letters (PD-L1, HER2, KRAS-G12C)
_BIOMARKER_HYPHEN_RE = re.compile(r"^[A-Z]{2,10}[-][A-Z0-9]+$")

# Materials science
_MATERIAL_FORMULA_RE = re.compile(r"^(?:Cs|FA|MA|GA|PEA|BA|GA)[A-Z][a-z]?[0-9]?"  # perovskite cations
                                r"|(?:Si|Ge|Sn|Pb)[A-Z][a-z]?[0-9]*"              # chalcogenides
                                r"|(?:Ti|Zr|Hf|Nb|Ta)[A-Z][a-z]?[0-9]*"          # oxides
                                r"|(?:Cu|In|Ga|Fe|Ni|Co)[A-Z][a-z]?[0-9]*", re.IGNORECASE)
_PEROVSKITE_RE = re.compile(r"(?:perovskite|halide|钙钛矿)", re.IGNORECASE)
# Astronomy
_EXOPLANET_RE = re.compile(
    r"^(?:TOI|WASP|Kepler|KIC|KOI|HAT|P|HAT-P|TrES|W|LDSS---|GJ|HIP|HD|BD)\s*[-]?[0-9]+"
    r"|\b(?:[A-Z][a-z]+-[0-9]+[a-z]?)\b",
    re.IGNORECASE
)
_STAR_DESIGNATION_RE = re.compile(r"^(?:HD|HIP|GJ|SA|BD|CD)[0-9]+" 
                                  r"|(?:alpha|beta|gamma|delta|epsilon|zeta|eta|theta)\s+[A-Z][a-z]+"
                                  r"|(?:Vega|Sirius|Procyon|Altair|Betelgeuse|Rigel|Antennae)", 
                                  re.IGNORECASE)


def detect_entity_type(entity_name: str, domain: str = DEFAULT_DOMAIN) -> Optional[str]:
    """Infer the entity type from an entity name string using regex heuristics.

    Priority order (first match wins):
      - NCT########  → ClinicalTrial
      - -mab, -nib, etc.  → DrugCompound
      - ends in -ib (no hyphen) → DrugCompound
      - BRCA1, KRAS, EGFR  → Protein
      - PD-L1, HER2neu → Biomarker
      - "mutation" in name → Mutation

    Args:
        entity_name: The name to classify
        domain: Active domain (reserved for future type-specific rules)

    Returns:
        Entity type string or None if unclassified.
    """
    if not entity_name or not isinstance(entity_name, str):
        return None

    name = entity_name.strip()

    # Clinical trial IDs — NCT followed by 8 digits
    if re.match(r"^NCT\d{8}$", name, re.IGNORECASE):
        return "ClinicalTrial"

    # Drug compounds: oncology names ending in -mab (monoclonal antibodies) or -ib (kinase inhibitors)
    if re.search(r"(mab|ib)$", name, re.IGNORECASE):
        return "DrugCompound"

    # Protein / gene symbols: BRCA1, HER2, KRAS, EGFR, ALK, ROS1, MET, TMB
    if _PROTEIN_RE.match(name):
        return "Protein"

    # Biomarkers with hyphen: PD-L1, HER2, KRAS-G12C
    if _BIOMARKER_HYPHEN_RE.match(name):
        return "Biomarker"

    # Mutation mentions — check BEFORE astronomy patterns to avoid p53/p73 collision
    if "mutation" in name.lower():
        return "Mutation"

    # Materials science patterns
    if _MATERIAL_FORMULA_RE.match(name) or _PEROVSKITE_RE.search(name):
        return "Material"

    # Astronomy patterns
    if _EXOPLANET_RE.match(name) and not _PROTEIN_RE.match(name):
        return "Exoplanet"
    if _STAR_DESIGNATION_RE.match(name):
        return "Star"

    return None


def get_inferred_types_for_name(
    entity_name: str, domain: str = DEFAULT_DOMAIN
) -> List[str]:
    """Return all possible entity types for a name (not just the first match).

    Useful for showing type uncertainty to the operator.
    """
    types = []
    name = entity_name.strip()

    if re.match(r"^NCT\d{8}$", name, re.IGNORECASE):
        types.append("ClinicalTrial")
    if re.search(r"(mab|ib)$", name, re.IGNORECASE):
        types.append("DrugCompound")
    if _PROTEIN_RE.match(name):
        types.append("Protein")
    if _BIOMARKER_HYPHEN_RE.match(name):
        types.append("Biomarker")

    # Mutation — check before astronomy to avoid p53/p73 collision
    if "mutation" in name.lower():
        types.append("Mutation")

    # Materials science
    if _MATERIAL_FORMULA_RE.match(name) or _PEROVSKITE_RE.search(name):
        types.append("Material")

    # Astronomy
    if _EXOPLANET_RE.match(name) and not _PROTEIN_RE.match(name):
        types.append("Exoplanet")
    if _STAR_DESIGNATION_RE.match(name):
        types.append("Star")

    return types


# ──────────────────────────────────────────────────────────────────────────────
# Entity Fact Aggregation
# ──────────────────────────────────────────────────────────────────────────────

def _matches_entity(fact: Dict[str, Any], entity_name: str) -> bool:
    """Return True if entity_name appears in subject, object, or fact_data."""
    name_lower = entity_name.lower()

    if fact.get("subject", "").lower() == name_lower:
        return True
    if fact.get("object", "").lower() == name_lower:
        return True

    # Check fact_data values (e.g., "0.54" in hazard_ratio ci_low)
    fact_data = fact.get("fact_data", {})
    for val in fact_data.values():
        if isinstance(val, str) and name_lower in val.lower():
            return True

    return False


def get_entity_facts(
    entity_name: str,
    domain: str = DEFAULT_DOMAIN,
    predicate_filter: Optional[str] = None,
    limit: int = 200,
) -> List[Dict[str, Any]]:
    """Load all facts relevant to an entity name.

    Checks subject, object, and fact_data.values() for a match.
    V1: loads all facts from fact_assertions.jsonl (no indexed lookup).
    Results sorted by timestamp descending (most recent first).

    Args:
        entity_name: Entity to search for
        domain: Active domain (all domains share same fact store in V1)
        predicate_filter: If set, only return facts with this predicate
        limit: Maximum number of facts to scan (oldest first)

    Returns:
        List of matching fact dicts
    """
    facts = load_facts(limit=limit)
    matched = []

    for fact in facts:
        if predicate_filter and fact.get("predicate") != predicate_filter:
            continue
        if _matches_entity(fact, entity_name):
            matched.append(fact)

    matched.sort(key=lambda f: f.get("timestamp", ""), reverse=True)
    return matched


def get_entity_summary(
    entity_name: str,
    domain: str = DEFAULT_DOMAIN,
    max_facts: int = 20,
) -> Dict[str, Any]:
    """Build a structured summary dict for an entity.

    Returns:
        dict with keys: name, detected_types, primary_type, schema,
                        facts (up to max_facts), total_facts
    """
    detected = get_inferred_types_for_name(entity_name, domain)
    primary = detected[0] if detected else None

    schema = get_entity_schema(primary, domain) if primary else {}

    facts = get_entity_facts(entity_name, domain, limit=500)
    total = len(facts)
    sample = facts[:max_facts]

    return {
        "name": entity_name,
        "detected_types": detected,
        "primary_type": primary,
        "schema": schema,
        "facts": sample,
        "total_facts": total,
    }


def group_facts_by_predicate(facts: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """Group a list of facts by their predicate."""
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for fact in facts:
        pred = fact.get("predicate", "unknown")
        if pred not in grouped:
            grouped[pred] = []
        grouped[pred].append(fact)
    return grouped


def format_entity_response(entity_name: str, summary: Dict[str, Any]) -> str:
    """Format an entity summary as a readable multi-line string."""
    lines = []
    lines.append(f"Entity   : {entity_name}")

    detected = summary.get("detected_types", [])
    if detected:
        types_str = ", ".join(detected)
        lines.append(f"Type(s)  : {types_str}  (heuristic)")
    else:
        lines.append("Type(s)  : unknown")

    schema = summary.get("schema", {})
    if schema:
        attrs = schema.get("attributes", [])
        if attrs:
            lines.append(f"Expected attributes: {', '.join(attrs)}")

    lines.append("")
    lines.append(f"Relevant facts: {summary.get('total_facts', 0)} total")

    facts = summary.get("facts", [])
    if not facts:
        lines.append("  (no facts found — try searching PubMed first)")
        return "\n".join(lines)

    grouped = group_facts_by_predicate(facts)
    for predicate, pred_facts in sorted(grouped.items()):
        lines.append(f"\n  [{predicate}] ({len(pred_facts)} fact{'s' if len(pred_facts) > 1 else ''})")
        for fact in pred_facts[:3]:
            obj = fact.get("object", "")[:60]
            trust = fact.get("trust_score", 0)
            src_ref = fact.get("source_reference", {})
            pmid = src_ref.get("pmid", "") if src_ref else ""
            snippet = f"    {obj}"
            if pmid:
                snippet += f"  (PMID {pmid})"
            snippet += f"  trust={trust:.2f}"
            lines.append(snippet)

    total = summary.get("total_facts", 0)
    if total > 20:
        lines.append(f"\n  ... and {total - 20} more. Use /facts about {entity_name} for full list.")
    return "\n".join(lines)


# ──────────────────────────────────────────────────────────────────────────────
# Command Interface
# ──────────────────────────────────────────────────────────────────────────────

def entity_query(entity_name: str) -> str:
    """Handle /entity <name> — show entity summary."""
    if not entity_name or not entity_name.strip():
        return "Usage: /entity <name>  (e.g., /entity NCT04551452)"
    name = entity_name.strip()
    summary = get_entity_summary(name)
    return format_entity_response(name, summary)


def list_entity_types_cmd() -> str:
    """Handle /entities — list known entity types in the schema."""
    from weslr.entity_schema_registry import get_schema_summary
    return get_schema_summary()


def list_entities_of_type(entity_type: str) -> str:
    """Handle /entities type <type> — list entities matching that type."""
    if not entity_type:
        return "Usage: /entities type <type>  (e.g., /entities type ClinicalTrial)"

    schema = get_entity_schema(entity_type)
    if not schema:
        available = list_entity_types()
        return f"Unknown type '{entity_type}'. Available: {', '.join(available)}"

    # Collect unique entity names from facts whose names match the type
    facts = load_facts(limit=500)
    candidates: Dict[str, int] = {}

    for fact in facts:
        for val in [fact.get("subject", ""), fact.get("object", "")]:
            if not val:
                continue
            detected = get_inferred_types_for_name(val)
            if entity_type in detected:
                if val not in candidates:
                    candidates[val] = 0
                candidates[val] += 1

    lines = [f"Entities of type [{entity_type}]", ""]
    if not candidates:
        lines.append("  (no entities found — search PubMed first)")
        return "\n".join(lines)

    for name, count in sorted(candidates.items(), key=lambda x: -x[1])[:20]:
        lines.append(f"  {name}  ({count} fact{'s' if count > 1 else ''})")

    return "\n".join(lines)


def list_relationships_for_entity(rel_type: str) -> str:
    """Handle /entities relationship <rel> — list entity pairs connected by a relationship."""
    if not rel_type:
        return "Usage: /entities relationship <type>  (e.g., /entities relationship treats)"

    # Load all facts, filter to those with the relationship predicate
    facts = load_facts(limit=500)
    rel_facts = [f for f in facts if f.get("predicate") == rel_type]

    if not rel_facts:
        return f"No facts found with relationship '{rel_type}'."

    lines = [f"Relationship [{rel_type}] — {len(rel_facts)} fact(s)", ""]
    seen_pairs: set = set()
    for fact in rel_facts[:20]:
        subj = fact.get("subject", "")
        obj = fact.get("object", "")
        pair_key = f"{subj}|{obj}"
        if pair_key not in seen_pairs:
            lines.append(f"  {subj} ──[{rel_type}]── {obj}")
            seen_pairs.add(pair_key)

    if len(rel_facts) > 20:
        lines.append(f"  ... and {len(rel_facts) - 20} more")
    return "\n".join(lines)