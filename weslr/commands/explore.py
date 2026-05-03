"""Command handler for /explore <goal> — goal-driven hypothesis generation."""

from __future__ import annotations

import re
from typing import Any, Optional

from weslr.explore_engine import explore
from weslr.hypothesis_scorer import format_hypothesis_list

_STOP_WORDS_SET = {
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
    "out", "off", "over", "under", "again", "further", "your", "my", "our", "their",
}


def handle_explore(message: str, lowered: str) -> str:
    """Handle /explore <goal> [--domain <domain>] [--top N] [--dry-run] command.

    Parses flags then calls explore_engine.explore().
    --dry-run: use built-in mock data without live search API calls.
    """
    # Strip the /explore prefix
    body = lowered
    for prefix in ("/explore", "explore"):
        if body.startswith(prefix):
            body = body[len(prefix):].strip()
            break

    if not body:
        return _usage()

    # Parse optional flags
    domain: Optional[str] = None
    top_n = 5
    dry_run = False
    remaining = body

    # --domain <domain>
    domain_match = re.search(r"--domain\s+(\w+)", remaining)
    if domain_match:
        domain = domain_match.group(1)
        remaining = remaining[:domain_match.start()] + remaining[domain_match.end():]

    # --top N
    top_match = re.search(r"--top\s+(\d+)", remaining)
    if top_match:
        top_n = int(top_match.group(1))
        remaining = remaining[:top_match.start()] + remaining[top_match.end():]

    # --dry-run
    dry_match = re.search(r"--dry-run", remaining)
    if dry_match:
        dry_run = True
        remaining = remaining[:dry_match.start()] + remaining[dry_match.end():]

    goal = remaining.strip()
    if not goal:
        return _usage()

    top_n = max(1, min(top_n, 20))

    if dry_run:
        result = _explore_dry_run(goal, domain, top_n)
    else:
        result = explore(
            goal=goal,
            domain=domain,
            max_results_per_adapter=8,
            top_n=top_n,
            timeout_per_adapter=12.0,
        )

    hypotheses = result["hypotheses"]
    search_summary = result.get("search_summary", {})
    detected_domain = result["goal_decomposition"].get("domain", domain or "auto")

    summary_parts = [f"{k}:{v}" for k, v in search_summary.items() if v > 0]
    summary_str = "  |  ".join(summary_parts) if summary_parts else "no live results"
    if dry_run:
        summary_str += " (dry-run)"

    header = (
        f"🔍 Exploring: {goal}\n"
        f"   Domain: {detected_domain}  |  Search: {summary_str}  |  {len(hypotheses)} hypotheses generated\n"
    )

    formatted = format_hypothesis_list(hypotheses, goal, domain=detected_domain, limit=top_n)

    lines = formatted.split("\n", 1)
    if len(lines) > 1:
        output = header + "\n" + lines[1]
    else:
        output = header

    return output


def _explore_dry_run(goal: str, domain: Optional[str], top_n: int) -> dict:
    """Return pre-computed mock hypotheses without making live API calls."""
    from weslr.explore_engine import build_entity_graph, generate_hypotheses
    from weslr.hypothesis_scorer import rank_hypotheses

    mock_results = [
        {
            "arxiv_id": "2401.00001",
            "title": "Dasatinib and quercetin as senolytics",
            "abstract": (
                "Dasatinib and quercetin (D+Q) are senolytic agents that clear senescent cells. "
                "NAD+ boosters like NMN improve mitochondrial function and reduce SASP."
            ),
        },
        {
            "arxiv_id": "2401.00002",
            "title": "mTOR inhibition and autophagy",
            "abstract": (
                "Rapamycin inhibits mTOR and promotes autophagy. "
                "TRPC5 calcium channel modulates cellular senescence signaling."
            ),
        },
        {
            "pmid": "12345678",
            "title": "NMN improves mitochondrial function in aged cells",
            "abstract": (
                "Nicotinamide mononucleotide (NMN) boosts NAD+ levels and restores "
                "mitochondrial function in senescent human fibroblasts."
            ),
        },
        {
            "arxiv_id": "2403.09999",
            "title": "Gold nanoparticle delivery of CRISPR for glioblastoma",
            "abstract": (
                "Gold nanoparticles enable targeted delivery of CRISPR-Cas9 to glioblastoma cells "
                "with minimal off-target effects. The blood-brain barrier is a key delivery challenge."
            ),
        },
        {
            "arxiv_id": "2402.05555",
            "title": "Kesterite Cu2ZnSnSe4 for sustainable photovoltaics",
            "abstract": (
                "Cu2ZnSnSe4 (kesterite) is an earth-abundant thin-film absorber. "
                "Bandgap grading improves carrier collection and open-circuit voltage."
            ),
        },
        {
            "pmid": "98765432",
            "title": "Targeted drug delivery using folate-conjugated nanoparticles",
            "abstract": "Folate-conjugated polymeric nanoparticles improve uptake in tumor cells.",
        },
    ]

    decomp = {
        "raw_keywords": [w for w in goal.lower().split() if w not in _STOP_WORDS_SET],
        "keywords": [],
        "query_components": [goal.lower().strip()],
        "domain": domain or "biology",
        "original_goal": goal,
    }

    entities = build_entity_graph(mock_results)
    detected = domain or decomp["domain"]
    raw_hyps = generate_hypotheses(
        entities, goal, domain=detected, max_hypotheses=top_n * 3
    )
    scored = rank_hypotheses(raw_hyps)

    return {
        "hypotheses": scored,
        "search_summary": {"arxiv": 3, "pubmed": 2, "searxng": 0},
        "goal_decomposition": decomp,
        "entities": entities,
        "total_results": 5,
    }


def _usage() -> str:
    return (
        "**Usage:** `/explore <goal> [--domain <domain>] [--top N] [--dry-run]`\n\n\n"
        "**Examples:**\n"
        "  `/explore slow down human cell aging`\n"
        "  `/explore design targeted drug delivery for glioblastoma`\n"
        "  `/explore create more efficient photovoltaic material`\n"
        "  `/explore slow down aging --domain biology --top 5`\n"
        "  `/explore aging --dry-run`  *(use built-in mock data, no live search)*\n\n"
        "**Flags:**\n"
        "  `--domain <domain>` — restrict to biology | chemistry | materials_science\n"
        "  `--top N` — return top N hypotheses (default 5, max 20)\n"
        "  `--dry-run` — use built-in mock data (no live PubMed/arXiv calls)"
    )
