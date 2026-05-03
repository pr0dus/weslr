"""Biology discovery — convenience wrapper around discovery_engine."""

from weslr.discovery.discovery_engine import (
    generate_candidates,
    rank_candidates,
    get_available_domains,
    load_domain,
)


def handle_propose_biology(
    tenant_id: str = None,
    limit: int = 10,
    min_trust: float = 0.5,
) -> str:
    """Handle /propose biology command."""
    domains = get_available_domains()
    if "biology" not in domains:
        return "Biology domain not configured. Run discovery setup first."

    config = load_domain("biology")

    candidates = generate_candidates(
        domain="biology",
        existing_facts=None,
        min_trust=min_trust,
        limit=limit * 2,
    )

    ranked = rank_candidates(candidates, metric="candidate_score")
    return format_biology_result(ranked, limit=limit)


def format_biology_result(candidates, limit=10):
    if not candidates:
        return "No biology candidates generated. Check domain config."

    lines = [
        f"Biology discovery (top {min(limit, len(candidates))} of {len(candidates)} candidates)",
        "(rule-based: ion channels, signaling pathways, bionanoparticles, cell targeting)",
        "",
    ]

    for i, c in enumerate(candidates[:limit], 1):
        name = c.get("name", "unnamed")
        prov = c.get("provenance", "")
        desc = c.get("description", "")
        score = c.get("candidate_score", 0)

        lines.append(f"{i}. **{name}**")
        if prov:
            lines.append(f"   {prov}")
        if desc:
            lines.append(f"   {desc}")
        lines.append(f"   Score: {score:.3f}")
        lines.append("")

    lines.append(f"[{len(candidates)} total candidates]")
    return "\n".join(lines)