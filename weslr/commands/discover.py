"""Unified discovery command — /propose discover <domain>."""

from weslr.discovery.discovery_engine import get_available_domains

# Builtin domains that have dedicated handlers (but aren't in discovery configs)
BUILTIN_DOMAINS = {
    "pv_material": "weslr.commands.propose",
    "chemistry": "weslr.combinatorial_chemistry",
    "nanotechnology": "weslr.nanotechnology_discovery",
    "communications": "weslr.communications_discovery",
}


def handle_discover(domain: str = None, tenant_id: str = None, limit: int = 10) -> str:
    """Handle /propose discover [domain] command.

    If domain is None, list all available discovery domains.
    If domain is specified, delegate to the appropriate handler.
    """
    if domain is None:
        return list_discovery_domains()

    domain_lower = domain.lower().strip()

    # Check builtin handlers first
    if domain_lower in BUILTIN_DOMAINS:
        return dispatch_to_domain(domain_lower, tenant_id, limit)

    # Check discovery engine domains
    available = get_available_domains()
    if domain_lower in available:
        return dispatch_to_domain(domain_lower, tenant_id, limit)

    # Unknown domain — show available
    return f"Unknown domain: '{domain_lower}'\n\n{list_discovery_domains()}"


def list_discovery_domains() -> str:
    """Return formatted list of all available discovery domains."""
    available = get_available_domains()
    builtin = list(BUILTIN_DOMAINS.keys())

    all_domains = sorted(set(available + builtin))

    lines = [
        "Available discovery domains:",
        "",
    ]

    for d in all_domains:
        lines.append(f"  • {d}")

    lines.append("")
    lines.append("Usage: /propose discover <domain>")
    lines.append("Example: /propose discover nanotechnology")

    return "\n".join(lines)


def dispatch_to_domain(domain: str, tenant_id: str, limit: int) -> str:
    """Dispatch to the appropriate domain handler."""
    if domain == "nanotechnology":
        from weslr.nanotechnology_discovery import handle_propose_nanotechnology
        return handle_propose_nanotechnology(tenant_id=tenant_id, limit=limit)
    elif domain == "communications":
        from weslr.communications_discovery import handle_propose_communication
        return handle_propose_communication(tenant_id=tenant_id, limit=limit)
    elif domain == "chemistry":
        from weslr.combinatorial_chemistry import handle_propose_chemistry
        return handle_propose_chemistry(tenant_id=tenant_id, limit=limit)
    elif domain == "pv_material":
        from weslr.commands.propose import handle_propose_pv_material
        return handle_propose_pv_material(tenant_id=tenant_id)
    else:
        # Generic discovery engine domain
        from weslr.discovery.discovery_engine import generate_candidates, rank_candidates, format_discovery_result
        candidates = generate_candidates(domain=domain, existing_facts=None, limit=limit)
        ranked = rank_candidates(candidates)
        return format_discovery_result(domain, ranked, limit=limit)