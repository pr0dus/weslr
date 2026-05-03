"""
/propose pv_material — Rank non-perovskite photovoltaic materials by efficiency.

Queries fact store for efficiency-related facts, groups by material,
computes trust-weighted efficiency, returns ranked proposal list.
"""
from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path
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

# High-confidence efficiency predicates — use for headline numbers
_HIGH_CONFidence_EFF = {
    "power_conversion_efficiency",  # confidence 0.88
    "champion_efficiency",          # confidence 0.92
    "certified_efficiency",         # confidence 0.95
    "record_efficiency",            # confidence 0.90
    "pv_material_efficiency",       # confidence 0.87
}

# Non-PCE percentage indicators — skip these when extracting efficiency values
_NON_PCE_KEYWORDS = {
    "voc", "v_oc", "open-circuit voltage", "open circuit voltage",
    "fill factor", "ff", "ff%", "fill-factor",
    "voltage ratio", "vbc", "vbs", "spectral response",
    "vocfs", "vocsq", "voc/sq",
}


def _is_likely_pce_value(fact: dict) -> bool:
    """Return True if the fact's percentage is a real PCE value (not VOC ratio/fill factor)."""
    pred = fact.get("predicate", "")
    eff = _extract_efficiency(fact)
    if eff is None:
        return True

    # High-confidence predicates — only reject physically impossible values (>40% for PCE)
    if pred in _HIGH_CONFidence_EFF:
        return eff <= 40

    # efficiency_mentioned — more aggressive filtering
    if pred == "efficiency_mentioned":
        # Skip if > 20% (no PCE material exceeds 30%, most are below 25%)
        # High values in this predicate are almost always VOC/fill-factor ratios
        if eff > 20:
            return False
        # Also skip if value is accompanied by "voc", "fill factor", "ratio" keywords in text
        obj = str(fact.get("object", "")).lower()
        subj = str(fact.get("subject", "")).lower()
        text = obj + " " + subj
        for kw in _NON_PCE_KEYWORDS:
            if kw.lower() in text:
                return False

    return True


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


def _build_doc_arxiv_map(tenant_id: Optional[str] = None) -> Dict[str, str]:
    """Build doc_id → arXiv ID mapping from document store.

    Facts store source_doc_id (pointing to doc store), not arxiv_id directly.
    We extract arXiv ID from the document's filename
    (e.g. 2404_00291.pdf → 2404.00291).
    """
    from weslr.tenant_context import resolve_path

    doc_store_path = resolve_path(str(Path(".weslr") / "documents.jsonl"), tenant_id)
    doc_map: Dict[str, str] = {}
    try:
        with open(doc_store_path) as f:
            for line in f:
                if line.strip():
                    d = json.loads(line)
                    doc_id = d.get("doc_id", "")
                    filename = d.get("filename", "")
                    # Extract arXiv ID from filename: 2404_00291.pdf → 2404.00291
                    arxiv_id = filename.replace(".pdf", "").replace("_", ".")
                    doc_map[doc_id] = arxiv_id
    except Exception:
        pass
    return doc_map


def build_pv_material_proposals(
    tenant_id: Optional[str] = None,
    limit: int = 20,
) -> List[Dict[str, Any]]:
    """Build ranked PV material proposals from fact store.

    Groups efficiency-related facts by material using page-level co-occurrence
    (materials and their efficiencies appear on the same document page).
    Sorts descending by estimated efficiency.
    """
    # Load all facts
    all_facts = load_facts(tenant_id=tenant_id, limit=500)

    # Build doc_id → arxiv_id mapping from document store
    doc_arxiv_map = _build_doc_arxiv_map(tenant_id)

    # ── Phase 1: Map (doc_id, page) → materials present on that page ──
    page_materials: Dict[tuple, List[str]] = defaultdict(list)
    for f in all_facts:
        subj = f.get("subject", "")
        obj = f.get("object", "")
        doc_id = f.get("source_doc_id", "")
        page = f.get("source_reference", {}).get("page", 0)
        key = (doc_id, page)

        for candidate in (subj, obj):
            if _is_material_name(candidate) and candidate not in page_materials[key]:
                page_materials[key].append(candidate)

    # ── Phase 2: Collect efficiency facts ──
    efficiency_facts = [
        f for f in all_facts
        if any(ep in f.get("predicate", "") for ep in _EFFICIENCY_PREDICATES)
    ]

    # ── Phase 3: Build materials dict ──
    materials: Dict[str, Dict[str, Any]] = {}

    def _ensure_material(mat: str) -> Dict[str, Any]:
        mat_norm = mat.lower().strip()
        if mat_norm not in materials:
            materials[mat_norm] = {
                "name": mat,
                "facts": [],
                "efficiencies": [],      # high-confidence only (for ranking)
                "all_efficiencies": [],  # all values (for transparency)
                "sources": set(),
                "predicates": set(),
            }
        return materials[mat_norm]

    def _add_source(mat_data: Dict[str, Any], fact: Dict[str, Any]):
        sr = fact.get("source_reference", {})
        if isinstance(sr, dict) and sr.get("arxiv_id"):
            mat_data["sources"].add(sr["arxiv_id"])
        else:
            doc_id = fact.get("source_doc_id", "")
            arxiv_id = doc_arxiv_map.get(doc_id, "")
            if arxiv_id:
                mat_data["sources"].add(arxiv_id)

    # Process efficiency facts via page co-occurrence
    for f in efficiency_facts:
        pred = f.get("predicate", "")

        # Skip low-confidence efficiency_mentioned with values > 40%
        # (these are VOC ratio percentages, not solar cell PCE values)
        if pred == "efficiency_mentioned":
            try:
                val = float(f.get("subject", "0") or "0")
                if val > 40:
                    continue
            except (ValueError, TypeError):
                pass

        doc_id = f.get("source_doc_id", "")
        page = f.get("source_reference", {}).get("page", 0)

        # Find materials on the same page (and ±1 page for nearby context)
        mats_on_page = list(page_materials.get((doc_id, page), []))
        if not mats_on_page:
            for delta in (-1, 1):
                mats_on_page = page_materials.get((doc_id, page + delta), [])
                if mats_on_page:
                    break

        if not mats_on_page:
            continue

        eff = _extract_efficiency(f)
        if eff is None:
            continue

        if not _is_likely_pce_value(f):
            continue

        for mat in mats_on_page:
            mat_data = _ensure_material(mat)
            mat_data["facts"].append(f)
            mat_data["predicates"].add(pred)
            _add_source(mat_data, f)

            # Track all efficiency values for transparency
            mat_data["all_efficiencies"].append(eff)

            # Only use high-confidence predicates for headline efficiency ranking
            if pred in _HIGH_CONFidence_EFF:
                mat_data["efficiencies"].append(eff)

    # Also process material-specific facts that may carry their own efficiencies
    material_predicates = {"kesterite_family", "non_perovskite_pv_material_class"}
    for f in all_facts:
        if f.get("predicate") not in material_predicates:
            continue
        subj = f.get("subject", "")
        obj = f.get("object", "")
        mat = obj if _is_material_name(obj) else (subj if _is_material_name(subj) else None)
        if not mat:
            continue

        mat_data = _ensure_material(mat)
        if f not in mat_data["facts"]:
            mat_data["facts"].append(f)
        mat_data["predicates"].add(f.get("predicate", ""))
        _add_source(mat_data, f)

        # Also try to extract efficiency from the object string itself
        eff = _extract_efficiency(f)
        if eff is not None and eff not in mat_data["all_efficiencies"]:
            mat_data["all_efficiencies"].append(eff)

    # ── Phase 4: Build proposals ──
    proposals = []
    for mat_norm, data in materials.items():
        if not data["sources"]:
            continue

        # Use high-confidence efficiencies for ranking; fall back to all_efficiencies
        effs = data["efficiencies"] if data["efficiencies"] else data["all_efficiencies"]
        if not effs:
            continue

        max_eff = max(effs)
        avg_eff = sum(effs) / len(effs)

        confs = [f.get("confidence", f.get("trust_score", 0.8)) for f in data["facts"]]
        avg_conf = sum(confs) / len(confs) if confs else 0.8

        # Use max high-confidence efficiency as headline; prefer max_eff > avg_eff
        estimated_eff = max_eff

        proposals.append(
            {
                "material": data["name"],
                "estimated_efficiency": round(estimated_eff, 1),
                "max_efficiency": round(max_eff, 1),
                # Show all efficiency values for transparency
                "efficiencies_mentioned": sorted(set(round(e, 1) for e in data["all_efficiencies"])),
                "trust_score": round(avg_conf, 2),
                "sources": sorted(data["sources"]),
                "predicates": sorted(data["predicates"]),
                "fact_count": len(data["facts"]),
            }
        )

    # Sort: by estimated_efficiency desc, then by trust desc
    proposals.sort(
        key=lambda p: (p.get("estimated_efficiency") or 0, p.get("trust_score", 0)),
        reverse=True,
    )

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
        "",
    ]
    for i, p in enumerate(proposals[:limit], 1):
        eff_str = (
            f"{p['estimated_efficiency']}% (max: {p['max_efficiency']}%)"
            if p.get("estimated_efficiency")
            else "efficiency extracted from text"
        )
        lines.append(f"{i}. **{p['material']}** — {eff_str}  (trust={p['trust_score']})")

        if p.get("sources"):
            src_list = ", ".join(f"arXiv:{s}" for s in p["sources"][:3])
            lines.append(f"   Sources: {src_list}")

        if p.get("efficiencies_mentioned"):
            lines.append(f"   Efficiency values: {p['efficiencies_mentioned']}")

        preds = ", ".join(sorted(p["predicates"])[:4])
        lines.append(f"   Properties: {preds}")
        lines.append("")

    if len(proposals) > limit:
        lines.append(
            f"... and {len(proposals) - limit} more materials. Reply with /propose pv_material for full list."
        )

    return "\n".join(lines)


def handle_propose_pv_material(
    message: str = "",
    tenant_id: Optional[str] = None,
) -> str:
    """Handle /propose pv_material command."""
    proposals = build_pv_material_proposals(tenant_id=tenant_id, limit=10)
    return format_proposal_list(proposals, limit=5)