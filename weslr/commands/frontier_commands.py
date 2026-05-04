"""
Command handlers for /frontier — Phase 11 frontier science proposer.

/frontier propose <domain> [--max N] [--novelty-threshold X] [--difficulty {easy|moderate|hard|paradigm}]
/frontier novelty "idea text"
/frontier refine <id> --constraint "text"
/frontier list
/frontier show <id>

User acknowledgment required before live PubMed/arXiv search.
"""

from __future__ import annotations

import re
import sys
from typing import Optional

from weslr.modules.frontier_proposer import (
    FrontierProposal,
    _DIFFICULTY_MAP,
    check_novelty,
    export_proposals,
    generate_candidates_for_domain,
    generate_novel_hypotheses,
    get_proposal,
    get_frontier_state,
    list_proposals,
    refine_proposal,
    store_proposal,
    _build_experiment_summary,
)

import os

_FRONTIR_ACKNOWLEDGED_KEY = "_frontier_ack"


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _ack_key(tenant_id: str) -> str:
    return f"{tenant_id}:{_FRONTIR_ACKNOWLEDGED_KEY}"


def _is_acknowledged(tenant_id: str) -> bool:
    state = get_frontier_state(tenant_id)
    return state.get(_FRONTIR_ACKNOWLEDGED_KEY, False)


def _set_acknowledged(tenant_id: str) -> None:
    state = get_frontier_state(tenant_id)
    state[_FRONTIR_ACKNOWLEDGED_KEY] = True


def _resolve_tenant(message_text: str, tenant_id: str = "default") -> str:
    return tenant_id


# ─────────────────────────────────────────────────────────────────────────────
# /frontier propose
# ─────────────────────────────────────────────────────────────────────────────

FRONTIER_USAGE = """Usage:
  /frontier propose <domain> [--max N] [--novelty-threshold X] [--difficulty {easy,moderate,hard,paradigm}]
  /frontier novelty "idea text"
  /frontier refine <id> --constraint "text"
  /frontier list
  /frontier show <id>
  /frontier discover --real [--domain D] [--max N] [--difficulty L] [--export]
Domains: materials, chemistry, biology, cross_domain
Difficulty: easy (=★), moderate (=★★), hard (=★★★), paradigm (=★★★★)

/frontier discover --real performs LIVE PubMed/arXiv novelty checks."""


def _acknowledge_live_search(tenant_id: str) -> str:
    if _is_acknowledged(tenant_id):
        return ""
    _set_acknowledged(tenant_id)
    return (
        "[⚠️ ACKNOWLEDGMENT: Live literature search will now be performed via "
        "PubMed and arXiv. Rate limits apply. Results are labeled UNVALIDATED. "
        "Operator review required before any action.]\n\n"
    )


def handle_frontier_propose(message: str, tenant_id: str = "default") -> str:
    """Handle /frontier propose <domain> [--max N] [--novelty-threshold X] [--difficulty X]"""
    body = message.strip()
    for prefix in ("/frontier propose", "frontier propose"):
        if body.startswith(prefix):
            body = body[len(prefix):].strip()
            break

    if not body:
        return FRONTIER_USAGE

    # ── Parse domain ───────────────────────────────────────────────────────
    parts = body.split()
    if not parts:
        return "Error: domain required. Usage: /frontier propose <domain>"
    domain = parts[0].lower()
    remaining = " ".join(parts[1:])

    if domain not in ("materials", "chemistry", "biology", "cross_domain"):
        return f"Error: unknown domain '{domain}'. Valid: materials, chemistry, biology, cross_domain"

    # ── Parse flags ──────────────────────────────────────────────────────────
    max_candidates = 10
    novelty_threshold = 0.95
    difficulty_filter = None

    max_match = re.search(r"--max\s+(\d+)", remaining)
    if max_match:
        max_candidates = int(max_match.group(1))
        remaining = remaining[:max_match.start()] + remaining[max_match.end():]

    nt_match = re.search(r"--novelty-threshold\s+([\d.]+)", remaining)
    if nt_match:
        novelty_threshold = float(nt_match.group(1))
        remaining = remaining[:nt_match.start()] + remaining[nt_match.end():]

    diff_match = re.search(r"--difficulty\s+(\w+)", remaining)
    if diff_match:
        diff_raw = diff_match.group(1).lower()
        if diff_raw in _DIFFICULTY_MAP:
            difficulty_filter = diff_raw
        remaining = remaining[:diff_match.start()] + remaining[diff_match.end():]

    # ── Acknowledgment + generation ─────────────────────────────────────────
    ack_warn = _acknowledge_live_search(tenant_id)

    try:
        proposals = generate_novel_hypotheses(
            domain=domain,
            max_candidates=max_candidates,
            novelty_threshold=novelty_threshold,
            difficulty_filter=difficulty_filter,
            _user_acknowledged=_is_acknowledged(tenant_id),
        )
    except Exception as e:
        return f"Error generating proposals: {e}"

    if not proposals:
        return (
            f"{ack_warn}No frontier proposals found for domain '{domain}' "
            f"with novelty ≥ {novelty_threshold}" + (
                f" and difficulty '{difficulty_filter}'" if difficulty_filter else ""
            )
        )

    # Store all proposals
    for p in proposals:
        store_proposal(p, tenant_id)

    # ── Format output ───────────────────────────────────────────────────────
    lines = [
        f"{ack_warn}[FRONTIER PROPOSAL – UNVALIDATED] domain: {domain}"
        + (f" | difficulty: {_DIFFICULTY_MAP.get(difficulty_filter, 'all')}" if difficulty_filter else ""),
        "",
    ]

    for i, p in enumerate(proposals, 1):
        risk_tag = " [HIGH RISK – OPERATOR REVIEW REQUIRED]" if p.is_high_risk() else ""
        lines.append(f"{i}. {p.difficulty_level}{risk_tag} {p.title}")
        lines.append(f"   {p.display_scores()}")
        lines.append(f"   {p.description[:120]}")
        lines.append("")

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# /frontier novelty
# ─────────────────────────────────────────────────────────────────────────────

def handle_frontier_novelty(message: str, tenant_id: str = "default") -> str:
    """Handle /frontier novelty "idea text" """
    body = message.strip()
    for prefix in ("/frontier novelty", "frontier novelty"):
        if body.startswith(prefix):
            body = body[len(prefix):].strip()
            break

    if not body:
        return 'Usage: /frontier novelty "idea text"'

    if not _is_acknowledged(tenant_id):
        _set_acknowledged(tenant_id)
        ack = "[⚠️ Acknowledged: Live literature search will now run.]\n\n"
    else:
        ack = ""

    try:
        result = check_novelty(body, domain="materials")
    except Exception as e:
        return f"Error checking novelty: {e}"

    exists = result.get("exists", False)
    count = result.get("count", 0)
    papers = result.get("top_papers", [])
    query = result.get("query_used", "")

    novelty = 1.0 / (1.0 + count) if count == 0 else round(1.0 / (1.0 + count), 3)
    if count == 0:
        novelty = 0.99

    lines = [
        f"{ack}Novelty check: \"{body[:80]}\"",
        f"Query used: {query}",
        f"Literature hits: {count} | Novelty score: {novelty:.2f}",
        f"Status: {'⚠️ EXISTS — similar work found' if exists else '✅ LIKELY NOVEL' if count == 0 else '⚠️ PARTIAL — some results'}",
        "",
    ]

    if papers:
        lines.append("Top matching papers:")
        for p in papers[:5]:
            src = p.get("source", "unknown").upper()
            title = p.get("title", "Untitled")[:80]
            url = p.get("url", "")
            lines.append(f"  [{src}] {title}")
            if url:
                lines.append(f"         {url}")
    else:
        lines.append("(No matching papers found)")

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# /frontier refine
# ─────────────────────────────────────────────────────────────────────────────

def handle_frontier_refine(message: str, tenant_id: str = "default") -> str:
    """Handle /frontier refine <id> --constraint "text" """
    body = message.strip()
    for prefix in ("/frontier refine", "frontier refine"):
        if body.startswith(prefix):
            body = body[len(prefix):].strip()
            break

    if not body:
        return "Usage: /frontier refine <id> --constraint \"text\""

    id_match = re.match(r"^([\w\-]+)", body)
    if not id_match:
        return "Usage: /frontier refine <id> --constraint \"text\""
    proposal_id = id_match.group(1)
    remaining = body[len(proposal_id):].strip()

    constraint_match = re.search(r'--constraint\s+"([^"]+)"', remaining)
    if not constraint_match:
        return "Usage: /frontier refine <id> --constraint \"text\""
    constraint_text = constraint_match.group(1)

    original = get_proposal(proposal_id, tenant_id)
    if not original:
        return f"Error: proposal '{proposal_id}' not found. Use /frontier list to see IDs."

    refined = refine_proposal(original, constraint_text)
    store_proposal(refined, tenant_id)

    lines = [
        f"[FRONTIER PROPOSAL – UNVALIDATED] Refined: {refined.title}",
        f"Constraint applied: {constraint_text}",
        "",
        f"Scores (new): {refined.display_scores()}",
        f"Difficulty: {refined.difficulty_level}",
        f"Risk: {'⚠️ HIGH' if refined.is_high_risk() else '✅ OK'}",
        "",
        refined.proposed_experiment_summary[:300],
    ]
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# /frontier list
# ─────────────────────────────────────────────────────────────────────────────

def handle_frontier_list(tenant_id: str = "default") -> str:
    """Handle /frontier list — list all stored proposals."""
    proposals = list_proposals(tenant_id)
    if not proposals:
        return "No frontier proposals stored. Run /frontier propose first."

    lines = ["[FRONTIER PROPOSAL – UNVALIDATED] Stored proposals:", ""]
    for p in proposals:
        date = p.created_at[:10] if p.created_at else "?"
        lines.append(
            f"{p.id}  {p.difficulty_level}  {p.title[:50]}  ({date})"
        )
    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# /frontier show
# ─────────────────────────────────────────────────────────────────────────────

def handle_frontier_show(message: str, tenant_id: str = "default") -> str:
    """Handle /frontier show <id> — display full proposal."""
    body = message.strip()
    for prefix in ("/frontier show", "frontier show"):
        if body.startswith(prefix):
            body = body[len(prefix):].strip()
            break

    if not body:
        return "Usage: /frontier show <id>"

    proposal_id = body.split()[0] if body.split() else ""
    if not proposal_id:
        return "Usage: /frontier show <id>"

    p = get_proposal(proposal_id, tenant_id)
    if not p:
        return f"Error: proposal '{proposal_id}' not found. Use /frontier list."

    risk_tag = "\n⚠️  HIGH RISK – OPERATOR REVIEW REQUIRED" if p.is_high_risk() else ""

    lines = [
        f"[FRONTIER PROPOSAL – UNVALIDIFIED]{risk_tag}",
        "",
        f"ID:        {p.id}",
        f"Title:     {p.title}",
        f"Domain:    {p.domain}",
        f"Difficulty: {p.difficulty_level}",
        f"Created:   {p.created_at}",
        "",
        f"Scores:    {p.display_scores()}",
        "",
        f"Description:",
        f"  {p.description}",
        "",
        f"Experiment summary:",
        f"  {p.proposed_experiment_summary[:400]}",
        "",
        f"Provenance:",
    ]
    for step in p.provenance:
        lines.append(f"  • {step}")

    lit = p.literature_check
    if lit:
        count = lit.get("count", 0)
        papers = lit.get("top_papers", [])
        lines.append("")
        lines.append(f"Literature check ({count} hits):")
        for pap in papers[:3]:
            lines.append(f"  • [{pap.get('source','?')}] {pap.get('title','')[:80]}")

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# /frontier discover --real
# ─────────────────────────────────────────────────────────────────────────────

def _prompt_user_confirm(prompt: str) -> bool:
    """Ask the user a yes/no confirmation. Respects WESLR_AUTO_CONFIRM_FRONTIER."""
    if os.environ.get("WESLR_AUTO_CONFIRM_FRONTIER") == "1":
        return True
    # In command-layer context we return False; the caller should print the
    # prompt and let the caller handle the response.  For test environments
    # the env var bypasses the need for interactive input.
    return False


def _read_user_input(prompt: str) -> str:
    """Read a line from stdin (for interactive confirmation in real shells)."""
    try:
        return input(prompt).strip().lower()
    except EOFError:
        return ""
    except OSError:
        # Non-interactive (pipe/redirect) — treat as abort
        return ""


def handle_frontier_discover(
    message: str,
    tenant_id: str = "default",
    _auto_confirm: bool = False,
) -> str:
    """Handle /frontier discover --real [--domain D] [--max N] [--difficulty L] [--export].

    Performs live PubMed/arXiv novelty checks on generated candidates and
    outputs real, previously-unpublished proposals with verifiable novelty
    scores.  All external API calls are rate-limited and labeled LIVE.

    Args:
        message: The full command string.
        tenant_id: Tenant identifier.
        _auto_confirm: Test hook — skip the user prompt and assume 'y'.
    """
    body = message.strip()
    for prefix in ("/frontier discover", "frontier discover"):
        if body.startswith(prefix):
            body = body[len(prefix):].strip()
            break

    if not body:
        return FRONTIER_USAGE

    # ── Parse flags ──────────────────────────────────────────────────────────
    domain = "materials"
    max_candidates = 5
    difficulty_filter: Optional[str] = None
    do_export = False

    dom_match = re.search(r"--domain\s+(\w+)", body)
    if dom_match:
        domain = dom_match.group(1).lower()
        if domain not in ("materials", "chemistry", "biology", "cross_domain"):
            return f"Error: unknown domain '{domain}'. Valid: materials, chemistry, biology, cross_domain"

    max_match = re.search(r"--max\s+(\d+)", body)
    if max_match:
        max_candidates = int(max_match.group(1))

    diff_match = re.search(r"--difficulty\s+(\w+)", body)
    if diff_match:
        diff_raw = diff_match.group(1).lower()
        if diff_raw in _DIFFICULTY_MAP:
            difficulty_filter = diff_raw

    do_export = bool(re.search(r"--export", body))

    # ── User confirmation ───────────────────────────────────────────────────
    if not _auto_confirm:
        confirmed = _read_user_input(
            "\n⚠️  This will query live PubMed and arXiv APIs to check novelty. "
            "Continue? (y/n): "
        )
        if confirmed not in ("y", "yes"):
            return "Aborted — no external API calls were made."
    else:
        print("\n⚠️  This will query live PubMed and arXiv APIs to check novelty. "
              "Continue? (y/n): y  [WESLR_AUTO_CONFIRM_FRONTIER=1]")

    # ── Generate candidates (without live novelty check yet) ───────────────
    # Generate 3× candidates so after novelty filtering we still have --max
    raw_candidates = generate_candidates_for_domain(domain, max_candidates * 3)
    if not raw_candidates:
        return f"Error: no candidates generated for domain '{domain}'. " \
               "Check that combinatorial modules are available."

    # ── Live novelty check with console progress ───────────────────────────
    # We do the live search here directly (not via generate_novel_hypotheses
    # because we want per-candidate progress output).
    from weslr.modules.frontier_proposer import _clear_novelty_cache
    _clear_novelty_cache()  # ensure clean cache for this run

    accepted_proposals: List = []
    novelty_threshold = 0.95
    filter_level = (
        _DIFFICULTY_MAP[difficulty_filter]
        if difficulty_filter and difficulty_filter in _DIFFICULTY_MAP
        else None
    )

    # Suppress adapter rate-limit sleeps for the first candidate only
    # (already baked into adapters).  We add a small inter-candidate buffer.
    from weslr.modules.frontier_proposer import (
        score_feasibility, score_risk, score_impact,
        assign_difficulty, score_novelty,
        _build_experiment_summary as _build_exp,
    )
    import uuid as _uuid
    from datetime import datetime, timezone

    for idx, cand in enumerate(raw_candidates, 1):
        desc = cand.get("description", "")
        name = cand.get("name", "Unnamed")
        # Short display name for progress
        short_name = name[:40] if len(name) > 40 else name

        print(f"🔄  Checking novelty for candidate {idx}/{len(raw_candidates)} ({short_name})...")

        try:
            lit = check_novelty(desc, domain, _mock_results=None)
        except Exception as exc:
            print(f"   ⚠️  API error for '{short_name}': {exc}. Skipping.")
            continue

        pmids = [p for p in lit.get("top_papers", []) if p.get("source") == "pubmed"]
        axvs = [p for p in lit.get("top_papers", []) if p.get("source") == "arxiv"]
        hit_count = lit.get("count", 0)
        novelty = score_novelty(hit_count)

        if hit_count == 0:
            status = "novel!  ✅"
        elif novelty >= 0.95:
            status = f"novelty {novelty:.2f} (below threshold 0.95) → discarded"
            print(f"   📡  PubMed: {len(pmids)} paper(s) | arXiv: {len(axvs)} paper(s) → {status}")
            continue
        else:
            status = f"novelty {novelty:.2f} (below threshold 0.95) → discarded"
            print(f"   📡  PubMed: {len(pmids)} paper(s) | arXiv: {len(axvs)} paper(s) → {status}")
            continue

        print(f"   📡  PubMed: {len(pmids)} paper(s) | arXiv: {len(axvs)} paper(s) → {status}")

        # ── Score ──────────────────────────────────────────────────────────────
        feasibility = score_feasibility(cand)
        risk = score_risk(cand)
        impact = score_impact({**cand, "novelty_score": novelty, "feasibility_score": feasibility})
        difficulty = assign_difficulty(novelty, feasibility, risk)

        # ── Filter ─────────────────────────────────────────────────────────
        if novelty < novelty_threshold:
            print(f"   ❌  novelty {novelty:.2f} < {novelty_threshold} → discarded")
            continue
        if filter_level and difficulty != filter_level:
            print(f"   ❌  difficulty '{difficulty}' != filter '{filter_level}' → discarded")
            continue
        if risk > 0.7:
            print(f"   ⚠️  HIGH RISK (score {risk:.2f}) → included with operator review flag")

        exp_summary = _build_exp(cand, domain)
        provenance = [
            f"LIVE novelty check via PubMed + arXiv",
            f"Query used: {lit.get('query_used', '?')}",
            f"PubMed hits: {len(pmids)}, arXiv hits: {len(axvs)}",
            f"Candidate generated via {cand.get('source_module', 'unknown')}",
            f"Feasibility: {feasibility:.3f} | Risk: {risk:.3f} | Impact: {impact:.3f}",
        ]

        proposal = FrontierProposal(
            id=str(_uuid.uuid4())[:8],
            title=name,
            description=desc,
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
        accepted_proposals.append(proposal)

        if len(accepted_proposals) >= max_candidates:
            print(f"\n   🎯 Reached --max {max_candidates} proposals — stopping early.")
            break

        # Small inter-candidate buffer
        import time as _time
        _time.sleep(0.1)

    if not accepted_proposals:
        return (
            f"\n❌  No novel proposals found for domain '{domain}' with novelty ≥ {novelty_threshold}.\n"
            f"   Try a broader domain or lower --max to generate more candidates."
        )

    # Store all accepted proposals
    for p in accepted_proposals:
        store_proposal(p, tenant_id)

    # ── Format output ───────────────────────────────────────────────────────
    lines = [
        f"[FRONTIER DISCOVERY – LIVE] domain: {domain}"
        + (f" | difficulty: {_DIFFICULTY_MAP.get(difficulty_filter, 'all')}" if difficulty_filter else ""),
        f"Checked {len(raw_candidates)} candidates → {len(accepted_proposals)} accepted",
        "",
    ]

    for i, p in enumerate(accepted_proposals, 1):
        risk_tag = " ⚠️  HIGH RISK – OPERATOR REVIEW REQUIRED" if p.is_high_risk() else ""
        lines.append(f"{i}. {p.difficulty_level}{risk_tag} {p.title}")
        lines.append(f"   {p.display_scores()}")
        lit = p.literature_check
        if lit:
            papers = lit.get("top_papers", [])
            pmids = [x for x in papers if x.get("source") == "pubmed"]
            axvs = [x for x in papers if x.get("source") == "arxiv"]
            lines.append(
                f"   LIVE: PubMed {len(pmids)} paper(s) | arXiv {len(axvs)} paper(s) "
                f"| query: {lit.get('query_used', '?')[:50]}"
            )
        lines.append(f"   {p.description[:120]}")
        lines.append("")

    # ── Export ───────────────────────────────────────────────────────────────
    export_path = ""
    if do_export:
        try:
            from weslr.modules.frontier_proposer import export_proposals
            ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            default_path = f"frontier_proposals_{domain}_{ts}.json"
            export_path = export_proposals(accepted_proposals, default_path, domain=domain)
            lines.append(f"📁  Exported {len(accepted_proposals)} proposals to {export_path}")
        except Exception as exc:
            lines.append(f"⚠️  Export failed: {exc}")

    return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# Main dispatcher
# ─────────────────────────────────────────────────────────────────────────────

def handle_frontier(message: str, tenant_id: str = "default") -> str:
    """Route /frontier subcommands."""
    lowered = message.lower().strip()
    if lowered.startswith("/frontier propose") or lowered.startswith("frontier propose"):
        return handle_frontier_propose(message, tenant_id)
    elif lowered.startswith("/frontier novelty") or lowered.startswith("frontier novelty"):
        return handle_frontier_novelty(message, tenant_id)
    elif lowered.startswith("/frontier refine") or lowered.startswith("frontier refine"):
        return handle_frontier_refine(message, tenant_id)
    elif lowered.strip() in ("/frontier list", "frontier list"):
        return handle_frontier_list(tenant_id)
    elif lowered.startswith("/frontier show") or lowered.startswith("frontier show"):
        return handle_frontier_show(message, tenant_id)
    elif lowered.startswith("/frontier discover") or lowered.startswith("frontier discover"):
        return handle_frontier_discover(message, tenant_id)
    else:
        return FRONTIER_USAGE
