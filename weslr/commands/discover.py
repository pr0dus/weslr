"""Unified discovery command — /propose discover <domain>."""

from weslr.discovery.discovery_engine import get_available_domains

# ── Discovery Session State (last candidate tracking) ──────────────────────
_last_candidate: dict | None = None
_last_candidate_domain: str | None = None
_last_candidate_provenance: list[dict] = []

def store_discovery_session(candidate: dict, domain: str, provenance: list[dict]):
    """Store the last proposed candidate and its provenance chain."""
    global _last_candidate, _last_candidate_domain, _last_candidate_provenance
    _last_candidate = candidate
    _last_candidate_domain = domain
    _last_candidate_provenance = provenance

def get_last_candidate() -> tuple[dict | None, str | None, list[dict]]:
    """Return (candidate, domain, provenance_chain) or (None, None, [])."""
    return _last_candidate, _last_candidate_domain, _last_candidate_provenance


# Builtin domains that have dedicated handlers (but aren't in discovery configs)
BUILTIN_DOMAINS = {
    "pv_material": "weslr.commands.propose",
    "chemistry": "weslr.combinatorial_chemistry",
    "nanotechnology": "weslr.nanotechnology_discovery",
    "communications": "weslr.communications_discovery",
    "biology": "weslr.biology_discovery",
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
        result, candidates = dispatch_to_domain(domain_lower, tenant_id, limit)
        # Store top candidate for later refinement
        if candidates:
            top = candidates[0]
            store_discovery_session(top, domain_lower, [{
                "name": top.get("name", "unknown"),
                "transformation": "origin",
                "provenance": "initial_proposal",
            }])
        return result

    # Check discovery engine domains
    available = get_available_domains()
    if domain_lower in available:
        result, candidates = dispatch_to_domain(domain_lower, tenant_id, limit)
        # Store top candidate for later refinement
        if candidates:
            top = candidates[0]
            store_discovery_session(top, domain_lower, [{
                "name": top.get("name", "unknown"),
                "transformation": "origin",
                "provenance": "initial_proposal",
            }])
        return result

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


def dispatch_to_domain(domain: str, tenant_id: str, limit: int) -> tuple[str, list[dict]]:
    """Dispatch to the appropriate domain handler.

    Returns (result_str, candidates_list).
    """
    if domain == "nanotechnology":
        from weslr.nanotechnology_discovery import handle_propose_nanotechnology
        result = handle_propose_nanotechnology(tenant_id=tenant_id, limit=limit)
        return result, []
    elif domain == "communications":
        from weslr.communications_discovery import handle_propose_communication
        result = handle_propose_communication(tenant_id=tenant_id, limit=limit)
        return result, []
    elif domain == "chemistry":
        from weslr.combinatorial_chemistry import handle_propose_chemistry
        result = handle_propose_chemistry(tenant_id=tenant_id, limit=limit)
        return result, []
    elif domain == "pv_material":
        from weslr.commands.propose import handle_propose_pv_material
        result = handle_propose_pv_material(tenant_id=tenant_id)
        return result, []
    else:
        # Generic discovery engine domain (includes biology)
        from weslr.discovery.discovery_engine import generate_candidates, rank_candidates, format_discovery_result
        candidates = generate_candidates(domain=domain, existing_facts=None, limit=limit)
        ranked = rank_candidates(candidates)
        result = format_discovery_result(domain, ranked, limit=limit)
        return result, ranked


# ── Interactive Refinement System ────────────────────────────────────────────

# Keyword → biology rule mapping (deterministic, no LLM)
_BIOLOGY_REFINE_KEYWORDS = {
    "sodium": {"rule": "channel_substitution", "target": "Na_channel"},
    "potassium": {"rule": "channel_substitution", "target": "K_channel"},
    "calcium": {"rule": "channel_substitution", "target": "Ca_channel"},
    "chloride": {"rule": "channel_substitution", "target": "Cl_channel"},
    "cancer": {"rule": "cell_targeting", "target": "antibody"},
    "tumor": {"rule": "cell_targeting", "target": "antibody"},
    "neurons": {"rule": "cell_targeting", "target": "neurotransmitter"},
    "neuron": {"rule": "cell_targeting", "target": "neurotransmitter"},
    "folate": {"rule": "cell_targeting", "target": "folate"},
    "mitochondrion": {"rule": "organelle_engineering", "target": "mitochondrion"},
    "chloroplast": {"rule": "organelle_engineering", "target": "chloroplast"},
    "peg": {"rule": "nanoparticle_coating", "target": "PEG"},
    "pegylation": {"rule": "nanoparticle_coating", "target": "PEG"},
    "antibody": {"rule": "nanoparticle_coating", "target": "antibody"},
    "drug": {"rule": "cell_targeting", "target": "drug"},
    "doxorubicin": {"rule": "cell_targeting", "target": "drug"},
}

def parse_refinement_instruction(instruction: str, domain: str) -> dict | None:
    """Parse a natural language refinement instruction and return a rule directive.

    Returns dict with keys: rule_name, target_value, or None if no rule matched.
    """
    instruction_lower = instruction.lower()

    # Check biology-specific keywords
    if domain == "biology" or domain is None:
        for keyword, directive in _BIOLOGY_REFINE_KEYWORDS.items():
            if keyword in instruction_lower:
                return directive

        # Phrase-based matching
        if "selective for sodium" in instruction_lower or "na+" in instruction_lower:
            return {"rule": "channel_substitution", "target": "Na_channel"}
        if "selective for potassium" in instruction_lower or "k+" in instruction_lower:
            return {"rule": "channel_substitution", "target": "K_channel"}
        if "target neuron" in instruction_lower or "target nerve" in instruction_lower:
            return {"rule": "cell_targeting", "target": "neurotransmitter"}
        if "add folate" in instruction_lower or "folate targeting" in instruction_lower:
            return {"rule": "cell_targeting", "target": "folate"}
        if "add mitochondri" in instruction_lower:
            return {"rule": "organelle_engineering", "target": "mitochondrion"}

    return None

def apply_refinement(candidate: dict, directive: dict, domain: str) -> dict:
    """Apply a refinement directive to a candidate. Returns modified candidate."""
    rule_name = directive.get("rule", "")
    target = directive.get("target", "")

    name = candidate.get("name", "")

    # For biology rules
    if rule_name in ("channel_substitution", "ion_channel_redesign"):
        new_name = f"{name}_with_{target}"
        if "channel" not in new_name.lower():
            new_name = f"{name}_{target}"
    elif rule_name == "cell_targeting":
        new_name = f"{name}+{target}"
    elif rule_name == "organelle_engineering":
        new_name = f"{name}_with_{target}"
    elif rule_name == "nanoparticle_coating":
        new_name = f"{name}_{target}"
    elif rule_name == "ligand_swap":
        # Replace any existing ligand
        parts = name.split("+")
        new_parts = [p for p in parts if p.lower() not in ("antibody", "folate", "aptamer", "neurotransmitter", "drug")]
        new_parts.append(target)
        new_name = "+".join(new_parts)
    else:
        new_name = f"{name}_{target}"

    refined = dict(candidate)
    refined["name"] = new_name
    refined["parent"] = name  # Previous candidate becomes parent
    refined["transformation"] = rule_name
    refined["description"] = f"Refined: {rule_name} with {target}"
    refined["provenance"] = f"Refined via {rule_name} → {target}"
    refined["candidate_score"] = round((candidate.get("candidate_score", 0.5) + 0.8) / 2, 3)
    refined["refined_from"] = name

    return refined

def build_provenance_chain(provenance: list[dict], new_step: dict) -> list[dict]:
    """Append a new refinement step to the provenance chain."""
    return provenance + [new_step]

def format_provenance(chain: list[dict]) -> str:
    """Format a provenance chain for display."""
    if not chain:
        return "  (origin)"

    lines = []
    for i, step in enumerate(chain):
        if i == 0:
            lines.append(f"  0. {step.get('name', 'unknown')} — origin")
        else:
            trans = step.get("transformation", "")
            prov = step.get("provenance", "")
            lines.append(f"  {i}. {step.get('name', 'unknown')} — {trans} ({prov})")
    return "\n".join(lines)

def handle_refine(instruction: str) -> str:
    """Handle /refine <instruction> command.


    Refines the last proposed discovery candidate based on a natural language instruction.
    """
    candidate, domain, provenance = get_last_candidate()

    if candidate is None:
        return ("No previous candidate to refine. "
                "Use /propose discover <domain> first to generate a candidate.")

    # Parse instruction to find matching rule
    directive = parse_refinement_instruction(instruction, domain)

    if directive is None:
        # Return available refinements
        available = list(_BIOLOGY_REFINE_KEYWORDS.keys())
        return (f"Could not understand refinement request: '{instruction}'\n\n"
                f"Available refinements for biology: {', '.join(sorted(set(available)))}\n"
                f"Try: 'make it target neurons', 'add folate', 'add a mitochondrion', 'change to sodium channel'")

    # Apply refinement
    refined = apply_refinement(candidate, directive, domain)

    # Update provenance chain
    new_step = {
        "name": refined["name"],
        "transformation": directive["rule"],
        "provenance": f"{directive['rule']} with {directive['target']}",
        "instruction": instruction,
        "parent": candidate.get("name", ""),
    }
    new_provenance = build_provenance_chain(provenance, new_step)

    # Store updated session
    store_discovery_session(refined, domain, new_provenance)

    # Format response
    lines = [
        f"Refined candidate: **{refined['name']}**",
        f"Transformation: {directive['rule']} → {directive['target']}",
        f"Provenance: {refined.get('provenance', '')}",
        f"Candidate score: {refined.get('candidate_score', 0):.3f}",
        "",
        "Provenance chain:",
        format_provenance(new_provenance),
    ]

    return "\n".join(lines)

def handle_show_history() -> str:
    """Handle /discovery history — show provenance chain of last candidate."""
    _, domain, provenance = get_last_candidate()

    if not provenance:
        return "No candidate history. Use /propose discover first."

    lines = [
        f"Discovery history ({domain or 'unknown domain'}):",
        "",
        "Provenance chain:",
        format_provenance(provenance),
    ]

    return "\n".join(lines)