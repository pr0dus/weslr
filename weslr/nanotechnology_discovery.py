"""Nanotechnology discovery — convenience wrapper around discovery_engine."""

from weslr.discovery.discovery_engine import (
    generate_candidates,
    rank_candidates,
    get_available_domains,
    format_discovery_result,
    load_domain,
)


def handle_propose_nanotechnology(
    tenant_id: str = None,
    limit: int = 10,
    min_trust: float = 0.5,
) -> str:
    """Handle /propose nanotechnology command."""
    # Check domain exists
    domains = get_available_domains()
    if "nanotechnology" not in domains:
        return "Nanotechnology domain not configured. Run discovery setup first."

    # Load domain config for descriptions
    config = load_domain("nanotechnology")

    # Generate candidates using building blocks (no fact store integration needed for V1)
    candidates = generate_candidates(
        domain="nanotechnology",
        existing_facts=None,
        min_trust=min_trust,
        limit=limit * 2,  # generate extra for ranking
    )

    # Rank by candidate_score
    ranked = rank_candidates(candidates, metric="candidate_score")

    # Format with nanotechnology-specific context
    return format_nanotechnology_result(ranked, limit=limit)


def format_nanotechnology_result(candidates, limit=10):
    if not candidates:
        return "No nanotechnology candidates generated. Check domain config."

    lines = [
        f"Nanoparticle discovery (top {min(limit, len(candidates))} of {len(candidates)} candidates)",
        "(rule-based nanoparticle formulation: core + shell + ligand)",
        "",
    ]

    for i, c in enumerate(candidates[:limit], 1):
        detail = c.get("transformation_detail", {})
        name = c.get("name", "unnamed")

        # Try to parse core/ligand/shell from name or transformation
        parent = c.get("parent", "")
        trans = c.get("transformation", "")
        prov = c.get("provenance", "")

        lines.append(f"{i}. **{name}**")
        if prov:
            lines.append(f"   {prov}")
        score = c.get("candidate_score", 0)
        lines.append(f"   Score: {score:.3f}  (rule conf={c.get('confidence', 0):.2f})")
        lines.append("")

    lines.append(f"[{len(candidates)} total candidates]")
    return "\n".join(lines)