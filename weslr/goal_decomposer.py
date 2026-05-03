"""Goal Decomposer — keyword expansion and query formulation for /explore."""

from __future__ import annotations

import json
import re
import pathlib
from typing import Optional

# ──────────────────────────────────────────────────────────────────────────────
# Stop Words
# ──────────────────────────────────────────────────────────────────────────────

_STOP_WORDS: set[str] = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "as", "is", "was", "are", "were", "been",
    "be", "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "must", "shall", "can", "need",
    "dare", "ought", "used", "it", "its", "this", "that", "these", "those",
    "i", "you", "he", "she", "we", "they", "what", "which", "who", "whom",
    "where", "when", "why", "how", "all", "each", "every", "both", "few",
    "more", "most", "other", "some", "such", "no", "not", "only", "same",
    "so", "than", "too", "very", "just", "also", "now", "here", "there",
    "then", "once", "if", "however", "therefore", "thus", "hence", "although",
    "because", "until", "while", "about", "against", "between", "into",
    "through", "during", "before", "after", "above", "below", "up", "down",
    "out", "off", "over", "under", "again", "further", "then", "once", "any",
    "my", "your", "his", "her", "our", "their", "whose", "me", "him", "us",
    "them", "myself", "yourself", "himself", "herself", "itself", "ourselves",
    "themselves", "make", "made", "find", "found", "give", "gave",
}


# ──────────────────────────────────────────────────────────────────────────────
# Domain Thesaurus (operator-editable)
# ──────────────────────────────────────────────────────────────────────────────

_THESAURUS_CACHE: dict[str, dict[str, list[str]]] = {}

def _get_thesaurus_path() -> pathlib.Path:
    """Path to the operator-editable thesaurus file."""
    return pathlib.Path(__file__).parent.parent / "goal_thesaurus.json"


def load_thesaurus() -> dict[str, list[str]]:
    """Load domain synonym mappings from the thesaurus file.

    File format:
      {
        "biology": {
          "aging": ["senescence", "cell aging", "cellular aging"],
          ...
        },
        "chemistry": { ... }
      }
    """
    global _THESAURUS_CACHE

    path = _get_thesaurus_path()
    if not path.exists():
        return {}

    if "file" in _THESAURUS_CACHE:
        return _THESAURUS_CACHE["file"]

    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
        _THESAURUS_CACHE["file"] = data
        return data
    except Exception:
        return {}


def _get_default_thesaurus() -> dict[str, list[str]]:
    """Built-in thesaurus with essential domain synonyms."""
    return {
        "biology": {
            "aging": ["senescence", "cellular senescence", "cell aging", "organism aging"],
            "slow down": ["anti-aging", "longevity", "geroprotective", "life extension"],
            "cell": ["cellular", "cell-based", "in vitro", "in vivo"],
            "cancer": ["tumor", "carcinoma", "neoplasm", "malignant", "oncology"],
            "drug": ["therapeutic", "pharmacological", "compound", "agent"],
            "targeted": ["selective", "specific", "precision"],
            "glioblastoma": ["glioma", "brain tumor", "central nervous system cancer"],
            "inflammation": ["inflammatory", "pro-inflammatory", "chronic inflammation"],
            "mitochondria": ["mitochondrial", "mitochondrial function"],
            "stem cell": ["stem-cell", "progenitor cell", "pluripotent"],
            "gene": ["genetic", "genomic", "gene expression", "transcription"],
            "protein": ["proteomic", "protein-based", "peptide"],
            "nanoparticle": ["nanomaterial", "nanostructure", "nanocarrier"],
        },
        "chemistry": {
            "efficient": ["high-yield", "catalytic efficiency", "selectivity"],
            "material": ["compound", "molecule", "chemical species"],
            "photovoltaic": ["solar cell", "PV", "photovoltaic material"],
            "catalyst": ["catalytic", "enzyme", "photocatalyst"],
            "stable": ["stability", "long-term stability", "degradation resistance"],
            "cheap": ["low-cost", "economical", "earth-abundant"],
            "non-toxic": ["biocompatible", "safe", "low toxicity", "eco-friendly"],
            "membrane": ["polymer membrane", "selective membrane", "barrier"],
            "fuel cell": ["hydrogen fuel cell", "electrode", "electrolyte"],
        },
        "physics": {
            "efficient": ["high-efficiency", "optimized", "maximized output"],
            "material": ["semiconductor", "material system"],
            "photovoltaic": ["solar cell", "photovoltaic cell", "thin-film"],
            "quantum": ["quantum dot", "quantum well", "quantum confinement"],
            "superconductor": ["superconducting", "zero resistance"],
        },
    }


def expand_keywords(keywords: list[str], domain: Optional[str] = None) -> list[str]:
    """Expand keywords using domain thesaurus.

    Args:
        keywords: list of cleaned (non-stopword) keywords
        domain: optional domain hint ("biology", "chemistry", etc.)

    Returns:
        expanded keyword list including synonyms
    """
    thesaurus = load_thesaurus() or _get_default_thesaurus()

    # If no domain specified, check all
    domains_to_check = [domain] if domain else list(thesaurus.keys())

    expanded: set[str] = set(keywords)

    for kw in keywords:
        kw_lower = kw.lower()
        for d in domains_to_check:
            if d not in thesaurus:
                continue
            synonyms = thesaurus[d].get(kw_lower, [])
            for syn in synonyms:
                # Split compound synonyms
                for part in syn.split():
                    if part not in _STOP_WORDS and len(part) > 1:
                        expanded.add(part.lower())
                expanded.add(syn.lower())

    return sorted(expanded)


def decompose(goal: str, domain: Optional[str] = None) -> dict:
    """Decompose a natural-language goal into structured search components.

    Args:
        goal: natural language goal string
        domain: optional domain hint

    Returns:
        dict with keys:
          - raw_keywords: original non-stopword tokens
          - keywords: expanded keywords after synonym expansion
          - query_components: list of query strings for multi-target search
          - domain: detected or specified domain
    """
    goal_clean = re.sub(r"[^\w\s\-]", " ", goal.lower())
    tokens = goal_clean.split()

    raw_keywords = [t for t in tokens if t not in _STOP_WORDS and len(t) > 2]

    expanded = expand_keywords(raw_keywords, domain=domain)

    # Build query components:
    # 1. Full goal as a query
    # 2. Bigrams for two-word concepts
    # 3. Expanded single terms
    queries = [goal.lower().strip()]
    for i in range(len(raw_keywords) - 1):
        bigram = f"{raw_keywords[i]} {raw_keywords[i+1]}"
        if len(bigram) > 4:
            queries.append(bigram)

    # Add expanded keywords as separate queries (top 5 by length)
    for kw in sorted(expanded, key=len, reverse=True)[:5]:
        if kw not in [q.lower() for q in queries] and len(kw) > 4:
            queries.append(kw)

    # Detect domain from keywords if not specified
    detected = domain
    if not detected:
        bio_keywords = {"aging", "cancer", "cell", "gene", "protein", "drug", "therapy",
                        "mitochondria", "organ", "tissue", "brain", "liver", "kidney",
                        "senolytic", "senescence", "inflammation", "immune"}
        chem_keywords = {"material", "catalyst", "reaction", "synthesis", "compound",
                         "molecule", "polymer", "photovoltaic", "electrolyte", "polymer"}
        mat_keywords = {"solar", "photovoltaic", "semiconductor", "efficiency", "bandgap",
                        "thin-film", "absorber", "kesterite", "perovskite"}

        kw_set = set(raw_keywords)
        if kw_set & bio_keywords:
            detected = "biology"
        elif kw_set & chem_keywords:
            detected = "chemistry"
        elif kw_set & mat_keywords:
            detected = "materials_science"

    return {
        "raw_keywords": raw_keywords,
        "keywords": expanded,
        "query_components": queries[:8],  # cap at 8 queries
        "domain": detected,
        "original_goal": goal,
    }
