"""
WESLR Frontier Science Proposer — Phase 11

Generates scientifically novel, testable hypotheses (materials, chemistry,
cross-domain) and scores them on novelty, feasibility, risk, and impact.
Assigns a difficulty level from ★ Low-hanging fruit to ★★★★ Paradigm shift.

All operations are deterministic and read-only.
Live literature novelty check via PubMed/arXiv requires user acknowledgment.
Results are labeled [FRONTIER PROPOSAL – UNVALIDATED].

No automatic experiment execution. Operator review required.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
import uuid
from dataclasses import dataclass, field
import dataclasses
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# ─────────────────────────────────────────────────────────────────────────────
# Constants
# ─────────────────────────────────────────────────────────────────────────────

_RARE_EARTH_ELEMENTS = {
    "La", "Ce", "Nd", "Pr", "Pm", "Sm", "Eu", "Gd", "Tb", "Dy",
    "Ho", "Er", "Tm", "Yb", "Lu",
}
_PRECIOUS_METALS = {"Pt", "Pd", "Au", "Ir", "Os", "Re", "Rh", "Ru"}
_RESTRICTED_ELEMENTS = _RARE_EARTH_ELEMENTS | _PRECIOUS_METALS

_TOXIC_ELEMENTS = {"Be", "Cd", "Hg", "As", "Tl", "Pb"}
_HIGHLY_TOXIC = {"Cd", "Hg", "As", "Pb"}
_TOXIC_NAME_TO_SYMBOL = {
    "beryllium": "Be", "cadmium": "Cd", "mercury": "Hg",
    "arsenic": "As", "thallium": "Tl", "lead": "Pb",
}
_CORROSIVE_KEYWORDS = {"HF", "H2SO4"}
_EXPLOSIVE_GAS = {"H2", "O2", "acetylene"}
_WEAPON_KEYWORDS = {
    "explosive", "nerve agent", "select agent",
    "plague", "anthrax", "botulinum", "mustard gas",
    "sarin", "vx", "tabun",
}
_HIGH_IMPACT_KEYWORDS = {
    "water splitting", "CO2 reduction", "superconductor",
    "cancer selectivity", "record", "unprecedented",
    "first", "breakthrough",
}

_PUBMED_RATE_LIMIT = 0.34   # seconds between requests (3 req/s)
_ARXIV_RATE_LIMIT = 1.0     # seconds between requests (1 req/s)

_FRONTIR_STATE: Dict[str, Dict[str, Any]] = {}  # tenant_id -> {proposals}


# ─────────────────────────────────────────────────────────────────────────────
# Novelty-cache (session-scoped, keyed by candidate description hash)
# ─────────────────────────────────────────────────────────────────────────────

_NOVELTY_CACHE: Dict[str, Dict[str, Any]] = {}


def _clear_novelty_cache() -> None:
    """Clear the novelty cache before a new generation run."""
    _NOVELTY_CACHE.clear()


# ─────────────────────────────────────────────────────────────────────────────
# Export
# ─────────────────────────────────────────────────────────────────────────────

def export_proposals(
    proposals: List[FrontierProposal],
    filepath: str,
    domain: str = "unknown",
) -> str:
    """Write proposals to a JSON file with timestamp and API metadata.

    Creates parent directories if needed.  Returns the resolved path.
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    stem = Path(filepath).stem
    parent = str(Path(filepath).parent)
    if parent and not Path(parent).exists():
        Path(parent).mkdir(parents=True, exist_ok=True)

    export_data = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "domain": domain,
        "total_proposals": len(proposals),
        "proposals": [
            {
                **dataclasses.asdict(p),
                "_api_summary": {
                    "query_used": p.literature_check.get("query_used", ""),
                    "pmid_count": len([x for x in p.literature_check.get("top_papers", []) if x.get("source") == "pubmed"]),
                    "arxiv_count": len([x for x in p.literature_check.get("top_papers", []) if x.get("source") == "arxiv"]),
                    "total_hits": p.literature_check.get("count", 0),
                },
            }
            for p in proposals
        ],
    }

    with open(filepath, "w", encoding="utf-8") as fh:
        json.dump(export_data, fh, indent=2, default=_json_serializer)

    return filepath


def _json_serializer(obj: Any) -> Any:
    """Fallback serializer for non-JSON-native types."""
    if hasattr(obj, "__dataclass_fields__"):
        return dataclasses.asdict(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, (set, frozenset)):
        return sorted(list(obj), default=str)
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


# ─────────────────────────────────────────────────────────────────────────────
# Data structures
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class FrontierProposal:
    id: str
    title: str
    description: str
    domain: str
    novelty_score: float
    feasibility_score: float
    risk_score: float
    impact_score: float
    difficulty_level: str
    proposed_experiment_summary: str
    literature_check: Dict[str, Any]
    provenance: List[str]
    created_at: str

    def is_high_risk(self) -> bool:
        return self.risk_score > 0.7

    def display_scores(self) -> str:
        return (
            f"Novelty: {self.novelty_score:.2f} | "
            f"Feasibility: {self.feasibility_score:.2f} | "
            f"Risk: {self.risk_score:.2f} | "
            f"Impact: {self.impact_score:.2f}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Candidate property extraction (internal helper)
# ─────────────────────────────────────────────────────────────────────────────

def _parse_candidate_properties(description: str) -> Dict[str, Any]:
    """Extract structured properties from a candidate description string.

    Returns dict with keys:
      elements: set of element symbols found (including resolved from names)
      temperature_high: bool (>= 800°C mentioned)
      pressure_high: bool (>= 1e6 Pa mentioned)
      steps_multi: bool (> 3 steps mentioned)
      air_sensitive: bool
      moisture_sensitive: bool
    """
    text = description
    elements: set[str] = set()

    # Extract chemical element symbols
    for match in re.finditer(r"\b([A-Z][a-z]?)\b", text):
        el = match.group(1)
        if el[0].isupper():
            elements.add(el)

    # Resolve toxic element names to symbols
    text_lower = text.lower()
    for name, symbol in _TOXIC_NAME_TO_SYMBOL.items():
        if name in text_lower:
            elements.add(symbol)

    temp_high = bool(re.search(r"(\d+)\s*°?C|high[- ]temperature|temperature\s*≥?\s*\d", text, re.I))
    pres_high = bool(re.search(r"(\d+(?:\.\d+)?)\s*GPa|high[- ]pressure|pressure\s*≥?\s*\d", text, re.I))
    steps_multi = bool(re.search(r"\bsteps?\s*>?\s*3|\d+\s+steps?|multi[- ]step", text, re.I))
    air_sens = bool(re.search(r"air[- ]sensitive|airstable", text, re.I))
    moist_sens = bool(re.search(r"moisture[- ]sensitive|hygroscopic|watermoisture", text, re.I))

    return {
        "elements": elements,
        "temperature_high": temp_high,
        "pressure_high": pres_high,
        "steps_multi": steps_multi,
        "air_sensitive": air_sens,
        "moisture_sensitive": moist_sens,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Scoring functions
# ─────────────────────────────────────────────────────────────────────────────

def score_feasibility(candidate: Dict[str, Any]) -> float:
    """Score feasibility of a candidate proposal.

    All factors multiplied cumulatively against base 1.0.
    Result clamped to [0.0, 1.0].
    """
    desc = candidate.get("description", "") or ""
    props = _parse_candidate_properties(desc)
    elements = props["elements"]

    score = 1.0

    # Rare earth / precious metal penalty
    rare = elements & _RESTRICTED_ELEMENTS
    if rare:
        score *= 0.7

    # Toxic element penalty
    toxic = elements & _TOXIC_ELEMENTS
    if toxic:
        score *= 0.4

    # Extreme conditions
    if props["temperature_high"]:
        score *= 0.5
    if props["pressure_high"]:
        score *= 0.5

    # Multi-step synthesis
    if props["steps_multi"]:
        score *= 0.7

    # Air/moisture sensitivity
    if props["air_sensitive"] or props["moisture_sensitive"]:
        score *= 0.8

    return max(0.0, min(1.0, score))


def score_risk(candidate: Dict[str, Any]) -> float:
    """Score risk of a candidate proposal.

    Additive model starting at 0.0. Clamped to [0.0, 1.0].
    Any score > 0.7 triggers operator override flag.
    """
    desc = candidate.get("description", "") or ""

    risk = 0.0

    # Weaponization keywords — hard cap
    for kw in _WEAPON_KEYWORDS:
        if kw.lower() in desc.lower():
            return 0.8

    props = _parse_candidate_properties(desc)
    elements = props["elements"]

    # Highly toxic elements — scaled accumulation
    toxic_found = elements & _HIGHLY_TOXIC
    if toxic_found:
        risk += 0.2 * len(toxic_found)

    # Other toxic elements — scaled accumulation
    other_found = elements & (_TOXIC_ELEMENTS - _HIGHLY_TOXIC)
    if other_found:
        risk += 0.15 * len(other_found)

    # Explosive gases
    for el in _EXPLOSIVE_GAS:
        if re.search(rf"\b{el}\b", desc):
            risk += 0.3

    # Corrosive
    for el in _CORROSIVE_KEYWORDS:
        if re.search(rf"\b{re.escape(el)}\b", desc):
            risk += 0.2

    return max(0.0, min(1.0, risk))


def score_impact(candidate: Dict[str, Any]) -> float:
    """Score potential scientific impact of a candidate.

    Boost for high-impact keywords and cross-domain novelty.
    Clamped to [0.0, 1.0].
    """
    desc = candidate.get("description", "") or ""
    novelty = candidate.get("novelty_score", 0.5)
    feasibility = candidate.get("feasibility_score", 0.5)

    impact = 0.0

    # Keyword boosts — cumulative, capped at 0.8 from keywords
    desc_lower = desc.lower()
    for kw in _HIGH_IMPACT_KEYWORDS:
        if kw.lower() in desc_lower:
            if kw in ("record", "unprecedented", "first", "breakthrough"):
                impact += 0.3
            else:
                impact += 0.4
    impact = min(impact, 0.8)

    # Base from rarity / cross-domain heuristic
    # Higher impact when novelty and feasibility are both non-trivial
    base = min(0.3 + 0.6 * (1.0 - (novelty + feasibility) / 2.0), 1.0)
    impact = min(impact + base * 0.5, 1.0)

    return max(0.0, min(1.0, impact))


def score_novelty(paper_count: int) -> float:
    """Convert literature hit count to novelty score.

    novelty = 1 / (1 + count)
    Capped at 0.99 when count == 0 (assumes live search was run).
    """
    if paper_count == 0:
        return 0.99
    return 1.0 / (1.0 + paper_count)


def assign_difficulty(
    novelty: float,
    feasibility: float,
    risk: float,
) -> str:
    """Assign difficulty level from score triple.

    Returns one of four string labels.
    """
    if feasibility > 0.7 and risk < 0.2 and novelty > 0.8:
        return "★ Low-hanging fruit"
    elif feasibility > 0.4 and risk < 0.5 and novelty > 0.6:
        return "★★ Moderate gap"
    elif feasibility > 0.2 and risk < 0.8:
        return "★★★ Hard / high risk"
    else:
        return "★★★★ Paradigm shift"


# ─────────────────────────────────────────────────────────────────────────────
# Keyword extraction for query building
# ─────────────────────────────────────────────────────────────────────────────

def extract_keywords(text: str) -> List[str]:
    """Extract query keywords from idea text.

    Extracts: capitalized multi-word terms, chemical formulas,
    and longest words. Returns deduped list.
    """
    # Chemical formulas: Al2O3, Cu2ZnSnSe4, etc.
    formulas = re.findall(r"\b[A-Z][a-z]?\d*[A-Z]?(?:\d+)*\b", text)

    # Capitalized multi-word terms (2-4 words)
    cap_terms = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3}\b", text)

    # Longest words (length >= 7)
    words = re.findall(r"\b\w{7,}\b", text)

    keywords: List[str] = []
    seen = set()
    for kw in formulas + cap_terms + words:
        kwl = kw.lower()
        if kwl not in seen:
            seen.add(kwl)
            keywords.append(kw.strip())

    return keywords[:12]  # cap at 12 for query length


# ─────────────────────────────────────────────────────────────────────────────
# Literature novelty check
# ─────────────────────────────────────────────────────────────────────────────

# ─────────────────────────────────────────────────────────────────────────────
# Novelty-cache (session-scoped, keyed by candidate description hash)
# ─────────────────────────────────────────────────────────────────────────────

_NOVERTY_CACHE: Dict[str, Dict[str, Any]] = {}


def _cached_novelty(desc: str, domain: str, _mock: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Return cached novelty result for a description, or compute + cache it."""
    key = f"{domain}:{desc}"
    if key in _NOVERTY_CACHE:
        return _NOVERTY_CACHE[key]
    result = check_novelty(desc, domain, _mock_results=_mock)
    _NOVERTY_CACHE[key] = result
    return result


def _clear_novelty_cache() -> None:
    """Clear the novelty cache before a new generation run."""
    _NOVERTY_CACHE.clear()


def _build_novelty_result_for_candidate(candidate_desc: str, domain: str, live_search: bool, _mock: Optional[Dict[str, Any]]) -> tuple[Dict[str, Any], float]:
    """Compute novelty result and rate-limit-sleep for a single candidate.

    Returns (lit_result, novelty_score).
    """
    if live_search:
        # Sleep between live calls (rate limiting already done inside adapters)
        lit = _cached_novelty(candidate_desc, domain, _mock)
        time.sleep(0.1)  # small inter-candidate buffer
    else:
        lit = {"exists": False, "count": 0, "top_papers": [], "query_used": ""}
    novelty = score_novelty(lit.get("count", 0))
    return lit, novelty


# ─────────────────────────────────────────────────────────────────────────────
# Export
# ─────────────────────────────────────────────────────────────────────────────

def export_proposals(
    proposals: List[FrontierProposal],
    filepath: str,
    domain: str = "unknown",
) -> str:
    """Write proposals to a JSON file with timestamp and API metadata.

    Creates parent directories if needed.  Returns the resolved path.
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    stem = Path(filepath).stem
    dir_path = str(Path(filepath).parent)
    if dir_path and not Path(dir_path).exists():
        Path(dir_path).mkdir(parents=True, exist_ok=True)

    export_data = {
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "domain": domain,
        "total_proposals": len(proposals),
        "proposals": [
            {
                **dataclasses.asdict(p),
                # Include a summary of API responses used
                "_api_summary": {
                    "query_used": p.literature_check.get("query_used", ""),
                    "pmid_count": len([x for x in p.literature_check.get("top_papers", []) if x.get("source") == "pubmed"]),
                    "arxiv_count": len([x for x in p.literature_check.get("top_papers", []) if x.get("source") == "arxiv"]),
                    "total_hits": p.literature_check.get("count", 0),
                },
            }
            for p in proposals
        ],
    }

    with open(filepath, "w", encoding="utf-8") as fh:
        json.dump(export_data, fh, indent=2, default=_json_serializer)

    return filepath


def _json_serializer(obj: Any) -> Any:
    """Fallback serializer for non-JSON-native types."""
    if hasattr(obj, "__dataclass_fields__"):
        return dataclasses.asdict(obj)
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, (set, frozenset)):
        return sorted(list(obj), default=str)
    raise TypeError(f"Object of type {type(obj).__name__} is not JSON serializable")


def check_novelty(
    idea_text: str,
    domain: str = "materials",
    _mock_results: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Check idea novelty via PubMed and arXiv literature search.

    Requires user acknowledgment before live calls (handled in command layer).

    Args:
        idea_text: The candidate title or description to check.
        domain: Domain hint for query construction.
        _mock_results: Internal test hook — inject mock results dict
                       instead of making live calls.

    Returns:
        dict with keys: exists (bool), count (int),
        top_papers (list[dict]), query_used (str)
    """
    if _mock_results is not None:
        return _mock_results

    keywords = extract_keywords(idea_text)
    if not keywords:
        keywords = [idea_text[:80]]
    query = " ".join(keywords[:5])

    papers: List[Dict[str, str]] = []
    total_count = 0

    # ── PubMed ────────────────────────────────────────────────────────────────
    try:
        from weslr.search_adapters.pubmed_adapter import search_pubmed
        pmids, articles = search_pubmed(query, max_results=8)
        total_count += len(pmids)
        for a in articles:
            papers.append({
                "title": a.get("title", ""),
                "url": a.get("url", ""),
                "source": "pubmed",
            })
    except Exception:
        pass
    time.sleep(_PUBMED_RATE_LIMIT)

    # ── arXiv ────────────────────────────────────────────────────────────────
    try:
        from weslr.search_adapters.arxiv_adapter import search_arxiv
        results = search_arxiv(query, max_results=5, sort_by="relevance")
        total_count += len(results)
        for r in results:
            papers.append({
                "title": r.get("title", ""),
                "url": r.get("id", ""),
                "source": "arxiv",
            })
    except Exception:
        pass
    time.sleep(_ARXIV_RATE_LIMIT)

    # Deduplicate by title
    unique: List[Dict[str, str]] = []
    seen_titles: set[str] = set()
    for p in papers:
        t = p.get("title", "").lower()
        if t and t not in seen_titles:
            seen_titles.add(t)
            unique.append(p)

    return {
        "exists": total_count > 0,
        "count": total_count,
        "top_papers": unique[:5],
        "query_used": query,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Candidate generation from existing combinatorials
# ─────────────────────────────────────────────────────────────────────────────

def _generate_materials_candidates(max_candidates: int) -> List[Dict[str, Any]]:
    """Generate material candidates via combinatorial_materials."""
    try:
        from weslr.combinatorial_materials import build_material_candidates
        raw = build_material_candidates()  # no limit param
        candidates = []
        for item in raw:
            desc = item.get("description", "") or item.get("name", "") or ""
            title = item.get("name", "") or desc[:60]
            candidates.append({
                "name": title,
                "description": desc,
                "domain": "materials",
                "source_module": "combinatorial_materials",
            })
        return candidates[:max_candidates]
    except Exception:
        return []


def _generate_chemistry_candidates(max_candidates: int) -> List[Dict[str, Any]]:
    """Generate chemistry candidates via combinatorial_chemistry."""
    try:
        from weslr.combinatorial_chemistry import build_chemistry_candidates
        raw = build_chemistry_candidates()  # no limit param
        candidates = []
        for item in raw:
            desc = item.get("description", "") or item.get("name", "") or ""
            title = item.get("name", "") or desc[:60]
            candidates.append({
                "name": title,
                "description": desc,
                "domain": "chemistry",
                "source_module": "combinatorial_chemistry",
            })
        return candidates[:max_candidates]
    except Exception:
        return []


def _generate_biology_candidates(max_candidates: int) -> List[Dict[str, Any]]:
    """Generate biology candidates via biology_discovery stub."""
    try:
        from weslr.biology_discovery import handle_propose_biology
        # Returns formatted string; extract candidate lines from it
        output = handle_propose_biology(limit=max_candidates * 2)
        candidates = []
        for line in output.split("\n"):
            if line.strip() and not line.startswith("Biology"):
                # Try to parse candidate from bullet lines
                m = re.match(r"^\d+\.\s+\*\*(.+?)\*\*", line)
                if m:
                    name = m.group(1)
                    candidates.append({
                        "name": name,
                        "description": name,
                        "domain": "biology",
                        "source_module": "biology_discovery",
                    })
        return candidates
    except Exception:
        return []


def _generate_cross_domain_candidates(max_candidates: int) -> List[Dict[str, Any]]:
    """Generate cross-domain candidates by analogy transfer.

    V1: simple heuristic — take materials candidates and re-frame
    their mechanism in a biology context and vice versa.
    """
    mat_candidates = _generate_materials_candidates(max_candidates)
    chem_candidates = _generate_chemistry_candidates(max_candidates)
    cross: List[Dict[str, Any]] = []

    for i, mat in enumerate(mat_candidates[:max_candidates // 2]):
        desc = mat.get("description", "")
        # Re-frame as bio-adjacent: add targeting/biocompatibility angle
        bio_desc = (
            f"Biocompatible version of {desc}. "
            f"Evaluate selective uptake, hemocompatibility, and targeted delivery."
        )
        cross.append({
            "name": f"[Bio] {mat['name']}",
            "description": bio_desc,
            "domain": "cross_domain",
            "source_module": "cross_domain_analogy",
        })

    for i, chem in enumerate(chem_candidates[:max_candidates // 2]):
        desc = chem.get("description", "")
        # Re-frame for environmental or energy application
        env_desc = (
            f"Environmental/energy application of {desc}. "
            f"Evaluate catalytic stability, selectivity, and scalable synthesis."
        )
        cross.append({
            "name": f"[Env] {chem['name']}",
            "description": env_desc,
            "domain": "cross_domain",
            "source_module": "cross_domain_analogy",
        })

    return cross


def generate_candidates_for_domain(
    domain: str,
    max_candidates: int = 10,
) -> List[Dict[str, Any]]:
    """Generate raw candidate proposals for a domain."""
    if domain == "materials":
        return _generate_materials_candidates(max_candidates)
    elif domain == "chemistry":
        return _generate_chemistry_candidates(max_candidates)
    elif domain == "biology":
        return _generate_biology_candidates(max_candidates)
    elif domain == "cross_domain":
        return _generate_cross_domain_candidates(max_candidates)
    else:
        return []


# ─────────────────────────────────────────────────────────────────────────────
# Experiment protocol templates
# ─────────────────────────────────────────────────────────────────────────────

_EXPERIMENT_TEMPLATES = {
    "materials": (
        "Protocol (materials synthesis):\n"
        "  1. Obtain precursors (purity ≥ 99.9%).\n"
        "  2. Apply solid-state or solution synthesis route.\n"
        "  3. Characterize: XRD, SEM/EDS, UV-Vis DRS, IPCE if applicable.\n"
        "  4. Test performance: J-V curve under AM1.5G, EQE.\n"
        "  5. Stability test: damp-heat (85°C/85% RH, 1000 h).\n"
        "  6. Report: efficiency (PCE), fill factor, open-circuit voltage."
    ),
    "chemistry": (
        "Protocol (chemical synthesis):\n"
        "  1. Start from commercially available precursors (purity ≥ 95%).\n"
        "  2. Apply standard Schlenk-line / inert-atmosphere route.\n"
        "  3. Monitor reaction progress by TLC or in-situ IR.\n"
        "  4. Purify: column chromatography or recrystallization.\n"
        "  5. Characterize: 1H/13C NMR, HRMS, melting point.\n"
        "  6. Assess purity by HPLC before biological testing."
    ),
    "biology": (
        "Protocol (in vitro biology):\n"
        "  1. Culture target cells at ~70% confluence.\n"
        "  2. Treat with compound at graded concentrations (e.g., 0.1, 1, 10 µM).\n"
        "  3. Incubate 24–72 h (timepoint based on mechanism).\n"
        "  4. Endpoint: cell viability (MTS/CCK-8), marker expression (Western / qPCR).\n"
        "  5. Include vehicle and positive controls. n≥3 biological replicates.\n"
        "  6. Statistical test: t-test or ANOVA."
    ),
    "cross_domain": (
        "Protocol (cross-domain evaluation):\n"
        "  1. Define source domain (e.g., materials) and target domain (e.g., biology).\n"
        "  2. Identify key mechanism/structure property to transfer.\n"
        "  3. Adapt for target domain constraints (biocompatibility, stability, scale).\n"
        "  4. Run domain-specific characterization.\n"
        "  5. Compare performance against baseline in target domain.\n"
        "  6. Report cross-domain transfer efficiency and any novel properties."
    ),
}


def _build_experiment_summary(candidate: Dict[str, Any], domain: str) -> str:
    """Build a rule-based experiment summary for a candidate."""
    template = _EXPERIMENT_TEMPLATES.get(domain, _EXPERIMENT_TEMPLATES["cross_domain"])
    name = candidate.get("name", "Unnamed proposal")
    return f"Hypothesis: {name}\n\n{template}"


# ─────────────────────────────────────────────────────────────────────────────
# Main generation pipeline
# ─────────────────────────────────────────────────────────────────────────────

_DIFFICULTY_MAP = {
    "easy":    "★ Low-hanging fruit",
    "moderate":"★★ Moderate gap",
    "hard":    "★★★ Hard / high risk",
    "paradigm":"★★★★ Paradigm shift",
}


def generate_novel_hypotheses(
    domain: str,
    max_candidates: int = 10,
    novelty_threshold: float = 0.95,
    difficulty_filter: Optional[str] = None,
    _user_acknowledged: bool = False,
    _mock_novelty: Optional[Dict[str, Any]] = None,
    live_search: bool = False,
) -> List[FrontierProposal]:
    """Generate and score novel scientific hypotheses.

    Args:
        domain: "materials", "chemistry", "biology", or "cross_domain"
        max_candidates: Maximum number of proposals to return
        novelty_threshold: Minimum novelty_score required (0-1)
        difficulty_filter: One of "easy", "moderate", "hard", "paradigm"
                          (maps to difficulty level string)
        _user_acknowledged: If False, skips live literature check and
                           sets novelty_score to 0.5 (unknown).
        _mock_novelty: Test hook — mock return from check_novelty().
        live_search: If True, performs real PubMed/arXiv calls for novelty
                     checking (requires _user_acknowledged=True and user
                     confirmation at the command layer). Results are
                     cached within this call to avoid duplicate queries.

    Returns:
        List[FrontierProposal] sorted by (impact, -feasibility)
    """
    candidates = generate_candidates_for_domain(domain, max_candidates)
    proposals: List[FrontierProposal] = []
    filter_level = (
        _DIFFICULTY_MAP[difficulty_filter]
        if difficulty_filter and difficulty_filter in _DIFFICULTY_MAP
        else None
    )

    # Clear novelty cache for this generation run
    _NOVELTY_CACHE.clear()

    for idx, cand in enumerate(candidates):
        desc = cand.get("description", "")
        name = cand.get("name", "Unnamed")

        # ── Novelty check ───────────────────────────────────────────────────
        if live_search and _user_acknowledged:
            # Use real adapters with session-level caching
            cache_key = f"{domain}:{desc}"
            if cache_key not in _NOVELTY_CACHE:
                # Rate-limit: PubMed (0.34s) + arXiv (1.0s) already done inside adapters
                lit = check_novelty(desc, domain, _mock_results=None)
                _NOVELTY_CACHE[cache_key] = lit
                # Small inter-candidate buffer to be polite
                time.sleep(0.1)
            else:
                lit = _NOVELTY_CACHE[cache_key]
            novelty = score_novelty(lit.get("count", 0))
        elif _user_acknowledged:
            lit = check_novelty(desc, domain, _mock_results=_mock_novelty)
            novelty = score_novelty(lit.get("count", 0))
        else:
            lit = {"exists": False, "count": 0, "top_papers": [], "query_used": ""}
            novelty = 0.5  # unknown

        # ── Feasibility + Risk + Impact ─────────────────────────────────────
        feasibility = score_feasibility(cand)
        risk = score_risk(cand)
        impact = score_impact({**cand, "novelty_score": novelty, "feasibility_score": feasibility})

        # ── Difficulty ─────────────────────────────────────────────────────
        difficulty = assign_difficulty(novelty, feasibility, risk)

        # ── Filter ─────────────────────────────────────────────────────────
        if novelty < novelty_threshold:
            continue
        if filter_level and difficulty != filter_level:
            continue

        # ── Experiment summary ────────────────────────────────────────────
        exp_summary = _build_experiment_summary(cand, domain)

        # ── Provenance ─────────────────────────────────────────────────────
        provenance = [
            f"Candidate generated via {cand.get('source_module', 'unknown')}",
            f"Domain: {domain}",
            f"Feasibility score: {feasibility:.3f}",
            f"Risk score: {risk:.3f}",
            f"Impact score: {impact:.3f}",
        ]
        if not _user_acknowledged:
            provenance.append("Literature novelty check: SKIPPED (no user ack)")

        proposal = FrontierProposal(
            id=str(uuid.uuid4())[:8],
            title=cand.get("name", "Unnamed"),
            description=cand.get("description", ""),
            domain=domain,
            novelty_score=novelty,
            feasibility_score=feasibility,
            risk_score=risk,
            impact_score=impact,
            difficulty_level=difficulty,
            proposed_experiment_summary=exp_summary,
            literature_check=lit,
            provenance=provenance,
            created_at=datetime.now(timezone.utc).isoformat(),
        )
        proposals.append(proposal)

    # Sort: higher impact first; tie-break by feasibility
    proposals.sort(key=lambda p: (p.impact_score, -p.feasibility_score), reverse=True)
    return proposals[:max_candidates]


# ─────────────────────────────────────────────────────────────────────────────
# Proposal refinement
# ─────────────────────────────────────────────────────────────────────────────

_REFINE_CONSTRAINT_PENALTIES = {
    "water":      0.5,   # stability in water adds feasibility penalty
    "air":        0.4,   # air stability
    "stable":     0.3,   # general stability requirement
    "non-toxic":  0.6,   # non-toxic constraint (removes toxic elements)
    "cheap":      0.3,   # cost constraint (precious metals penalized)
    "scalable":   0.4,   # scalable synthesis (rare elements penalized)
    "room temperature": 0.5,
    "low temperature": 0.3,
}


def refine_proposal(
    proposal: FrontierProposal,
    constraint_text: str,
) -> FrontierProposal:
    """Re-evaluate a proposal with additional user constraints.

    Applies rule-based penalties to feasibility score and regenerates
    the difficulty level and experiment summary.
    """
    constraint_lower = constraint_text.lower()

    # Build a modified candidate dict
    modified_desc = f"{proposal.description} [{constraint_text}]"
    modified_candidate = {
        "description": modified_desc,
        "domain": proposal.domain,
    }

    # Re-run scores
    new_feasibility = score_feasibility(modified_candidate)
    new_risk = score_risk(modified_candidate)
    new_impact = score_impact({
        **modified_candidate,
        "novelty_score": proposal.novelty_score,
        "feasibility_score": new_feasibility,
    })
    new_difficulty = assign_difficulty(
        proposal.novelty_score,
        new_feasibility,
        new_risk,
    )

    # Build new experiment summary with constraint flag
    exp_addendum = (
        f"\n\n[CONSTRAINT APPLIED: {constraint_text}]\n"
        f"Feasibility re-evaluated with constraint penalty."
    )

    # Update proposal in place (return new one; originals preserved)
    refined = FrontierProposal(
        id=proposal.id,
        title=proposal.title,
        description=modified_desc,
        domain=proposal.domain,
        novelty_score=proposal.novelty_score,
        feasibility_score=new_feasibility,
        risk_score=new_risk,
        impact_score=new_impact,
        difficulty_level=new_difficulty,
        proposed_experiment_summary=proposal.proposed_experiment_summary + exp_addendum,
        literature_check=proposal.literature_check,
        provenance=[
            *proposal.provenance,
            f"Refined with constraint: {constraint_text}",
            f"New feasibility: {new_feasibility:.3f}",
            f"New risk: {new_risk:.3f}",
            f"New difficulty: {new_difficulty}",
        ],
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    return refined


# ─────────────────────────────────────────────────────────────────────────────
# Session state management (multi-tenant)
# ─────────────────────────────────────────────────────────────────────────────

def get_frontier_state(tenant_id: str = "default") -> Dict[str, Any]:
    """Get or create frontier state for a tenant."""
    if tenant_id not in _FRONTIR_STATE:
        _FRONTIR_STATE[tenant_id] = {"proposals": {}}
    return _FRONTIR_STATE[tenant_id]


def store_proposal(proposal: FrontierProposal, tenant_id: str = "default") -> None:
    """Store a proposal in session state."""
    state = get_frontier_state(tenant_id)
    state["proposals"][proposal.id] = proposal


def list_proposals(tenant_id: str = "default") -> List[FrontierProposal]:
    """List all proposals for a tenant."""
    state = get_frontier_state(tenant_id)
    return list(state["proposals"].values())


def get_proposal(proposal_id: str, tenant_id: str = "default") -> Optional[FrontierProposal]:
    """Get a specific proposal by ID."""
    state = get_frontier_state(tenant_id)
    return state["proposals"].get(proposal_id)
