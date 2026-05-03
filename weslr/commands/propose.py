"""
/propose pv_material — Rank non-perovskite photovoltaic materials by efficiency.

Queries fact store for efficiency-related facts, groups by material, 
computes trust-weighted efficiency, returns ranked proposal list.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from weslr.fact_extractor import load_facts

# Material class names to recognize
_PV_MATERIAL_KEYWORDS = [
    "kesterite", "czts", "cztsse", "cu2znsns4", "cu2zn",
    "bifeo3", "ferroelectric", "organic photovoltaic", "opv",
    "sb2se3", "perovskite-free", "non-perovskite", "quantum dot",
    "chalcogenide", "bifeocr", "cztse", "cdte", "amorphous silicon",
]

# Predicates that indicate efficiency data
_EFFICIENCY_PREDICATES = {
    "power_conversion_efficiency", "pce", "efficiency_mentioned",
    "champion_efficiency", "certified_efficiency", "record_efficiency",
    "pv_material_efficiency", "long_term_stability",
}


def _is_material_name(text: str) -> bool:
    t = text.lower().strip()
    for kw in _PV_MATERIAL_KEYWORDS:
        if kw in t:
            return True
    return False


def _extract_efficiency(fact: Dict[str, Any]) -> Optional[float]:
    """Extract efficiency percentage from a fact dict."""
    # From fact_data
    fd = fact.get("fact_data", {})
    for key in ("efficiency_pct", "efficiency", "value", "stability_pct"):
        val = fd.get(key, fd.get(key.replace("_", ""), None))
        if val is not None:
            try:
                f = float(val)
                if 0 < f <= 100:
                    return f
            except (ValueError, TypeError):
                pass
    
    # From object string
    obj = str(fact.get("object", ""))
    for m in re.findall(r"(\d+\.?\d*)\s*%", obj):
        try:
            f = float(m)
            if 0 < f <= 100:
                return f
        except ValueError:
            pass
    
    # From subject
    subj = str(fact.get("subject", ""))
    for m in re.findall(r"(\d+\.?\d*)\s*%", subj):
        try:
            f = float(m)
            if 0 < f <= 100:
                return f
        except ValueError:
            pass
    
    return None


def build_pv_material_proposals(
    tenant_id: Optional[str] = None,
    limit: int = 20,
) -> List[Dict[str, Any]]:
    """Build ranked PV material proposals from fact store.
    
    Groups all efficiency-related facts by material, computes average
    trust-weighted efficiency, sorts descending.
    """
    # Load all facts
    all_facts = load_facts(tenant_id=tenant_id, limit=500)
    
    # Filter to efficiency-relevant facts
    eff_facts = [
        f for f in all_facts
        if any(ep in f.get("predicate", "") for ep in _EFFICIENCY_PREDICATES)
        or f.get("predicate") == "kesterite_family"
        or f.get("predicate") == "non_perovskite_pv_material_class"
    ]
    
    # Also include facts from kesterite/foundry materials even without efficiency predicate
    # (they may have efficiency in object text)
    pv_material_facts = [
        f for f in all_facts
        if _is_material_name(f.get("subject", ""))
        or _is_material_name(f.get("object", ""))
        or _is_material_name(str(f.get("fact_data", {})))
    ]
    
    relevant = {id(f): f for f in eff_facts + pv_material_facts}.values()
    
    # Group by material name (normalized)
    materials: Dict[str, Dict[str, Any]] = {}
    for f in relevant:
        # Determine material name
        subj = f.get("subject", "")
        obj = f.get("object", "")
        fd_str = str(f.get("fact_data", {}))
        
        mat = None
        if _is_material_name(subj):
            mat = subj
        elif _is_material_name(obj):
            mat = obj
        elif "formula" in f.get("fact_data", {}):
            mat = f["fact_data"]["formula"]
        
        if not mat or len(mat) > 80:  # skip extraction artifacts
            continue
        
        mat_norm = mat.lower().strip()
        if mat_norm not in materials:
            materials[mat_norm] = {
                "name": mat,
                "facts": [],
                "efficiencies": [],
                "sources": set(),
                "predicates": set(),
            }
        
        materials[mat_norm]["facts"].append(f)
        materials[mat_norm]["predicates"].add(f.get("predicate", ""))
        
        eff = _extract_efficiency(f)
        if eff is not None:
            materials[mat_norm]["efficiencies"].append(eff)
        
        # Collect sources
        sr = f.get("source_reference", {})
        if isinstance(sr, dict) and sr.get("arxiv_id"):
            materials[mat_norm]["sources"].add(sr["arxiv_id"])
    
    # Build proposals
    proposals = []
    for mat_norm, data in materials.items():
        if not data["sources"]:  # skip orphaned facts without sources
            continue
        
        effs = data["efficiencies"]
        avg_eff = sum(effs) / len(effs) if effs else None
        max_eff = max(effs) if effs else None
        
        confs = [f.get("confidence", f.get("trust_score", 0.8)) for f in data["facts"]]
        avg_conf = sum(confs) / len(confs) if confs else 0.8
        
        # Estimate efficiency (prefer max, fallback to avg)
        estimated_eff = max_eff or avg_eff
        
        proposals.append({
            "material": data["name"],
            "estimated_efficiency": round(estimated_eff, 1) if estimated_eff else None,
            "max_efficiency": round(max_eff, 1) if max_eff else None,
            "efficiencies_mentioned": [round(e, 1) for e in effs],
            "trust_score": round(avg_conf, 2),
            "sources": sorted(data["sources"]),
            "predicates": sorted(data["predicates"]),
            "fact_count": len(data["facts"]),
        })
    
    # Sort: by estimated_efficiency desc, then by trust desc
    proposals.sort(key=lambda p: (
        p.get("estimated_efficiency") or 0,
        p.get("trust_score", 0),
    ), reverse=True)
    
    return proposals[:limit]


def format_proposal_list(proposals: List[Dict[str, Any]], limit: int = 5) -> str:
    """Format ranked proposals as readable string."""
    if not proposals:
        return (
            "No photovoltaic material proposals found in the ingested corpus.\n"
            "Try searching PubMed or arXiv for non-perovskite PV materials first."
        )
    
    lines = [
        f"Top {min(limit, len(proposals))} photovoltaic material proposals (based on extracted facts):",
        ""
    ]
    for i, p in enumerate(proposals[:limit], 1):
        eff_str = f"{p['estimated_efficiency']}% (max: {p['max_efficiency']}%)" if p.get("estimated_efficiency") else "efficiency extracted from text"
        lines.append(f"{i}. **{p['material']}** — {eff_str}  (trust={p['trust_score']})")
        
        if p.get("sources"):
            src_list = ", ".join(f"arXiv:{s}" for s in p['sources'][:3])
            lines.append(f"   Sources: {src_list}")
        
        if p.get("efficiencies_mentioned"):
            lines.append(f"   Efficiency values: {p['efficiencies_mentioned']}")
        
        preds = ", ".join(sorted(p["predicates"])[:4])
        lines.append(f"   Properties: {preds}")
        lines.append("")
    
    if len(proposals) > limit:
        lines.append(f"... and {len(proposals) - limit} more materials. Reply with /propose pv_material for full list.")
    
    return "\n".join(lines)


def handle_propose_pv_material(
    message: str = "",
    tenant_id: Optional[str] = None,
) -> str:
    """Handle /propose pv_material command."""
    proposals = build_pv_material_proposals(tenant_id=tenant_id, limit=10)
    return format_proposal_list(proposals, limit=5)
