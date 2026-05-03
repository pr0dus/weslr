"""Communications discovery — convenience wrapper around discovery_engine."""

from weslr.discovery.discovery_engine import (
    generate_candidates,
    rank_candidates,
    get_available_domains,
    load_domain,
)

def estimate_spectral_efficiency(modulation_order: int, code_rate: float) -> float:
    """Estimate spectral efficiency in bits/s/Hz."""
    return round(modulation_order.bit_length() * code_rate, 2)

def handle_propose_communication(
    tenant_id: str = None,
    limit: int = 10,
    min_trust: float = 0.5,
) -> str:
    """Handle /propose communication command."""
    domains = get_available_domains()
    if "communications" not in domains:
        return "Communications domain not configured."
    
    config = load_domain("communications")
    
    # Generate candidates
    candidates = generate_candidates(
        domain="communications",
        existing_facts=None,
        min_trust=min_trust,
        limit=limit * 3,
    )
    
    # Enhance with spectral efficiency estimates
    blocks = config.get("building_blocks", {})
    
    def _get_mod_order(name: str) -> int:
        for m in blocks.get("modulation", []):
            if m.get("name") == name:
                return m.get("order", 1)
        return 1
    
    def _get_code_rate(name: str) -> float:
        for c in blocks.get("coding", []):
            if c.get("name") == name:
                return c.get("rate", 1.0)
        return 1.0
    
    for c in candidates:
        # Estimate spectral efficiency from the candidate name or transformation
        # For combinations, look at the components
        name = c.get("name", "")
        detail = c.get("transformation_detail", {})
        
        mod_name = detail.get("component_a") or detail.get("to") or c.get("parent", "")
        code_name = detail.get("component_b") or ""
        
        # Try to extract modulation and coding from names
        for m in blocks.get("modulation", []):
            if m["name"] in name or m["name"] in c.get("parent", ""):
                mod_name = m["name"]
                break
        
        for co in blocks.get("coding", []):
            if co["name"] in name or co["name"] in detail.get("combine_with", []):
                code_name = co["name"]
                break
        
        mod_order = _get_mod_order(mod_name) if mod_name else 1
        code_rate = _get_code_rate(code_name) if code_name else 1.0
        
        c["spectral_efficiency"] = estimate_spectral_efficiency(mod_order, code_rate)
    
    # Rank by spectral efficiency
    ranked = rank_candidates(candidates, metric="spectral_efficiency")
    
    return format_communications_result(ranked, limit=limit)

def format_communications_result(candidates, limit=10):
    if not candidates:
        return "No communication scheme candidates generated."
    
    lines = [
        f"Communication scheme discovery (top {min(limit, len(candidates))} of {len(candidates)} candidates)",
        "(rule-based: modulation + coding + multiple access)",
        "",
    ]
    
    for i, c in enumerate(candidates[:limit], 1):
        name = c.get("name", "unnamed")
        prov = c.get("provenance", "")
        se = c.get("spectral_efficiency", 0)
        score = c.get("candidate_score", 0)
        
        lines.append(f"{i}. **{name}**")
        if prov:
            lines.append(f"   {prov}")
        if se:
            lines.append(f"   Est. spectral efficiency: {se:.2f} bits/s/Hz")
        lines.append(f"   Score: {score:.3f}")
        lines.append("")
    
    lines.append(f"[{len(candidates)} total candidates]")
    return "\n".join(lines)