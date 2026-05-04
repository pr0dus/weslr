"""
weslr/commands/advanced_commands.py
===================================
Phase 9 — Advanced reasoning commands: /abduce, /meta, /transfer

Author: OCC (WESLR governed intelligence) — Phase 9
"""

from __future__ import annotations

import re
from typing import Any, Optional

from weslr.modules.abductive_reasoner import (
    AbductiveReasoner,
    set_tenant_getter as set_abductive_tenant,
    _current_tenant_getter,
)
from weslr.modules.meta_analyst import (
    MetaAnalysis,
    set_tenant_getter as set_meta_tenant,
)
from weslr.modules.transfer_analogy import (
    AnalogyEngine,
    set_tenant_getter as set_transfer_tenant,
)
from weslr.modules.hypothesis_repository import Hypothesis, HypothesisRepository

# Shared tenant getter (set once at module load)
_tenant_getter: callable = lambda: "default"

def _sync_tenant_getters() -> None:
    """Sync all module-level tenant getters to the same function."""
    set_abductive_tenant(_tenant_getter)
    set_meta_tenant(_tenant_getter)
    # Patch abductive_reasoner's _current_tenant_getter so _tenant_rules() uses the shared one
    import modules.abductive_reasoner as _ar_mod
    _ar_mod._current_tenant_getter = _tenant_getter
    import modules.meta_analyst as _ma_mod
    _ma_mod._current_tenant_getter = _tenant_getter
    import modules.transfer_analogy as _ta_mod
    _ta_mod._current_tenant_getter = _tenant_getter
    set_transfer_tenant(_tenant_getter)

def set_shared_tenant_getter(fn: callable) -> None:
    global _tenant_getter
    _tenant_getter = fn
    _sync_tenant_getters()


# ── Shared state per tenant ────────────────────────────────────────────────────

_TENANT_REASONERS: dict[str, AbductiveReasoner] = {}
_TENANT_META_ANALYSES: dict[str, MetaAnalysis] = {}
_TENANT_ANALOGY_ENGINES: dict[str, AnalogyEngine] = {}

def _reasoner() -> AbductiveReasoner:
    tid = _tenant_getter()
    if tid not in _TENANT_REASONERS:
        _TENANT_REASONERS[tid] = AbductiveReasoner(max_depth=3, max_rules=200)
    return _TENANT_REASONERS[tid]

def _meta() -> MetaAnalysis:
    tid = _tenant_getter()
    if tid not in _TENANT_META_ANALYSES:
        _TENANT_META_ANALYSES[tid] = MetaAnalysis()
    return _TENANT_META_ANALYSES[tid]

def _analogy() -> AnalogyEngine:
    tid = _tenant_getter()
    if tid not in _TENANT_ANALOGY_ENGINES:
        _TENANT_ANALOGY_ENGINES[tid] = AnalogyEngine()
        _TENANT_ANALOGY_ENGINES[tid].preload_default_analogies()
    return _TENANT_ANALOGY_ENGINES[tid]


# ── /abduce ───────────────────────────────────────────────────────────────────

def handle_abduce(message: str, lowered: str) -> str:
    """
    Abductive reasoning: explain observations via backward chaining.

    /abduce <observation>                    — find explanations
    /abduce rule add <if> <then> [conf]     — add custom rule
    /abduce rules                            — list current rules
    /abduce clear                            — clear all rules
    """
    if not lowered.startswith("/abduce"):
        return _abduce_usage()

    body = lowered[len("/abduce"):].strip()

    # /abduce rules — list rules
    if body == "rules":
        return _abduce_list_rules()

    # /abduce clear — clear rules
    if body == "clear":
        _reasoner().clear_rules()
        return "Abduction rules cleared."

    # /abduce rule add <if> <then> [conf]
    rule_add_match = re.match(
        r"rule\s+add\s+(.+?)\s+(?:to|=>|->|=)\s+(.+?)(?:\s+(\d+\.?\d*))?\s*$",
        body,
    )
    if not rule_add_match:
        rule_add_match = re.match(r"rule\s+add\s+(.+?)\s+(.+?)(?:\s+(\d+\.?\d*))?\s*$", body)

    if "rule add" in body or "rule add" in lowered:
        # More careful parsing
        parts = body.split()
        if len(parts) >= 4 and parts[0] == "rule" and parts[1] == "add":
            antecedent = parts[2]
            # Find consequent: everything after the 3rd token until an optional float
            rest = parts[3:]
            conf = 0.8
            if rest and _isfloat(rest[-1]):
                conf = float(rest.pop())
            consequent = " ".join(rest)
            if not antecedent or not consequent:
                return _abduce_usage()
            r = _reasoner().add_rule(antecedent, consequent, conf, source="user")
            return f"Rule added: {r.antecedent} → {r.consequent} (conf={r.confidence:.2f})"

    # /abduce <observation>
    if body:
        return _abduce_explain(body)

    return _abduce_usage()

def _abduce_explain(observation: str) -> str:
    r = _reasoner()
    explanations = r.explain(observation, max_explanations=3)

    if not explanations:
        return (
            f"No explanations found for: \"{observation}\"\n"
            "Tips:\n"
            "  • Add rules first: /abduce rule add <cause> <effect> [confidence]\n"
            "  • Load causal graph from hypotheses: load_causal_rules\n"
            "  • Use broader terms (e.g., 'BP_down' not 'systolic_bp_reduced_2mmHg')"
        )

    lines = [f"**Possible explanations for:** \"{observation}\""]
    for i, e in enumerate(explanations, 1):
        conf_str = f"{e.confidence:.4f}" if e.confidence < 1 else f"{e.confidence:.2f}"
        chain_str = " ← ".join([f"{a}→{c}" for a, c, _ in e.rule_chain])
        lines.append(
            f"\n{i}. {e.hypothesis}  (confidence {conf_str})\n"
            f"   Rules: {chain_str}"
        )

    lines.append("\n⚠️ *Plausible explanations – requires experimental validation*")
    return "\n".join(lines)

def _abduce_list_rules() -> str:
    rules = _reasoner().list_rules()
    if not rules:
        return "No abduction rules loaded."
    lines = [f"**Abduction rules ({len(rules)}):**"]
    for r in rules[:30]:
        lines.append(f"  • {r.antecedent} → {r.consequent} [conf={r.confidence:.2f}, src={r.source}]")
    if len(rules) > 30:
        lines.append(f"  ... and {len(rules) - 30} more")
    return "\n".join(lines)

def _abduce_usage() -> str:
    return (
        "**Usage:**\n"
        "  `/abduce <observation>`                      — find explanations\n"
        "  `/abduce rule add <if> <then> [confidence]`  — add rule (default conf=0.8)\n"
        "  `/abduce rules`                             — list rules\n"
        "  `/abduce clear`                             — clear all rules\n\n"
        "**Examples:**\n"
        "  `/abduce BP_down`\n"
        "  `/abduce rule add high_dose response_increase 0.85`\n"
        "  `/abduce rule add low_sodium BP_down 0.9`"
    )


# ── /meta ─────────────────────────────────────────────────────────────────────

def handle_meta(message: str, lowered: str) -> str:
    """
    Meta-analysis: pool evidence from multiple hypotheses/studies.

    /meta add <study_id> <effect_size> <se> [n]     — add a study
    /meta list                                       — show all studies
    /meta clear                                      — clear all studies
    /meta remove <study_id>                          — remove a study
    /meta run [random|fixed]                        — run analysis
    /meta from_hypotheses <id1> <id2> ...           — import from repo
    """
    if not lowered.startswith("/meta"):
        return _meta_usage()

    body = lowered[len("/meta"):].strip()

    if body == "list":
        return _meta_list()

    if body.startswith("remove "):
        study_id = body[7:].strip()
        ok = _meta().remove_study(study_id)
        return f"Study '{study_id}' removed." if ok else f"Study '{study_id}' not found."

    if body == "clear":
        _meta().clear_studies()
        return "Meta-analysis pool cleared."

    if body == "run" or body.startswith("run "):
        mode = "random" if "random" in body else "fixed"
        return _meta_run(mode)

    if body.startswith("from_hypotheses "):
        return _meta_from_hypotheses(body)

    # /meta add <study_id> <effect_size> <se> [n]
    m = re.match(r"add\s+(\S+)\s+(-?\d+\.?\d*)\s+(-?\d+\.?\d*)\s*(\d*)", body)
    if m:
        study_id, effect_str, se_str, n_str = m.groups()
        try:
            effect = float(effect_str)
            se = float(se_str)
            n = int(n_str) if n_str else 30
            s = _meta().add_study(effect, se, n, study_id)
            return f"Study '{s.study_id}' added: effect={effect:.4f}, SE={se:.4f}, n={n}"
        except Exception as e:
            return f"Error: {e}"

    return _meta_usage()

def _meta_list() -> str:
    studies = _meta().list_studies()
    if not studies:
        return "No studies in meta-analysis pool.\nAdd with: /meta add <id> <effect> <se> [n]"
    lines = [f"**Meta-analysis pool ({len(studies)} studies):**"]
    for s in studies:
        lines.append(f"  • {s.study_id}: effect={s.effect_size:.4f}, SE={s.standard_error:.4f}, n={s.sample_size}")
    return "\n".join(lines)

def _meta_run(mode: str = "fixed") -> str:
    m = _meta()
    try:
        if mode == "random":
            result = m.random_effect_pooled()
        else:
            result = m.fixed_effect_pooled()
    except RuntimeError as e:
        return f"Error: {e}"

    sig = "***" if result.p < 0.001 else "**" if result.p < 0.01 else "*" if result.p < 0.05 else "n.s."
    type_label = "Random-effects (DerSimonian-Laird)" if mode == "random" else "Fixed-effect (inverse-variance)"

    lines = [
        f"**Meta-analysis — {type_label}**",
        f"",
        f"Pooled effect: {result.pooled_effect:.4f}",
        f"95% CI: [{result.ci_lower:.4f}, {result.ci_upper:.4f}]",
        f"z = {result.z:.3f}, p = {result.p:.4f} {sig}",
        f"",
        f"Heterogeneity:",
        f"  Cochran's Q = {result.q_statistic:.3f}",
        f"  I² = {result.i_squared:.1f}% {'(low)' if result.i_squared < 25 else '(moderate)' if result.i_squared < 75 else '(high)'}",
    ]
    if result.tau_sq > 0:
        lines.append(f"  τ² = {result.tau_sq:.4f} (between-study variance)")

    lines.extend([
        "",
        "⚠️ *Synthesized from simulated/demo data – not for clinical decision making*",
    ])
    return "\n".join(lines)

def _meta_from_hypotheses(body: str) -> str:
    # Extract hypothesis ids
    ids = body.replace("from_hypotheses", "").strip().split()
    if not ids:
        return "Provide hypothesis IDs: /meta from_hypotheses <id1> <id2> ..."
    # Get repo
    try:
        from weslr.modules.hypothesis_repository import HypothesisRepository, get_current_tenant_id
        repo = HypothesisRepository()
        count = _meta().from_hypotheses(ids, repo)
        return f"Imported {count} studies from hypothesis repository."
    except Exception as e:
        return f"Error: {e}"

def _meta_usage() -> str:
    return (
        "**Usage:**\n"
        "  `/meta add <id> <effect> <se> [n]`    — add study\n"
        "  `/meta list`                           — show pool\n"
        "  `/meta run [fixed|random]`             — run analysis\n"
        "  `/meta from_hypotheses <id1> <id2>`    — import from repo\n"
        "  `/meta remove <id>`                    — remove study\n"
        "  `/meta clear`                          — clear pool\n\n"
        "**Example:**\n"
        "  /meta add study1 0.5 0.1 30\n"
        "  /meta add study2 0.6 0.12 35\n"
        "  /meta run random"
    )


# ── /transfer ─────────────────────────────────────────────────────────────────

def handle_transfer(message: str, lowered: str) -> str:
    """
    Cross-domain transfer via analogy.

    /transfer analogies                        — list all analogies
    /transfer add <src_domain> <src> <tgt_domain> <tgt> [weight]
    /transfer apply <hypothesis_id> <target_domain>
    """
    if not lowered.startswith("/transfer"):
        return _transfer_usage()

    body = lowered[len("/transfer"):].strip()

    if body == "analogies":
        return _transfer_list()

    if body.startswith("add "):
        return _transfer_add(body)

    if body.startswith("apply "):
        return _transfer_apply(body)

    return _transfer_usage()

def _transfer_list() -> str:
    analogies = _analogy().list_analogies()
    if not analogies:
        return "No analogies loaded."
    lines = ["**Cross-domain analogies:**"]
    builtin = [a for a in analogies if a.provenance == "builtin"]
    user = [a for a in analogies if a.provenance == "user"]
    if builtin:
        lines.append(f"\nBuilt-in ({len(builtin)}):")
        for a in builtin[:20]:
            lines.append(f"  • {a.source_concept}[{a.source_domain}] → {a.target_concept}[{a.target_domain}] (w={a.similarity_weight:.2f})")
    if user:
        lines.append(f"\nUser-defined ({len(user)}):")
        for a in user:
            lines.append(f"  • {a.source_concept}[{a.source_domain}] → {a.target_concept}[{a.target_domain}] (w={a.similarity_weight:.2f})")
    if len(analogies) > 20:
        lines.append(f"  ... {len(analogies) - 20} more (use /transfer analogies to see all)")
    return "\n".join(lines)

def _transfer_add(body: str) -> str:
    # /transfer add <src_domain> <src_concept> <tgt_domain> <tgt_concept> [weight]
    parts = body.split()[1:]  # skip "add"
    if len(parts) < 4:
        return _transfer_usage()
    src_domain, src_concept, tgt_domain, tgt_concept = parts[0], parts[1], parts[2], parts[3]
    weight = 0.8
    if len(parts) >= 5 and _isfloat(parts[4]):
        weight = float(parts[4])
    try:
        a = _analogy().add_analogy(src_domain, src_concept, tgt_domain, tgt_concept, weight)
        return f"Analogy added: {src_concept}[{src_domain}] → {tgt_concept}[{tgt_domain}] (w={weight:.2f})"
    except Exception as e:
        return f"Error: {e}"

def _transfer_apply(body: str) -> str:
    # /transfer apply <hypothesis_id> <target_domain>
    parts = body.split()[1:]  # skip "apply"
    if len(parts) < 2:
        return _transfer_usage()
    hyp_id = parts[0]
    target_domain = parts[1]

    try:
        from weslr.modules.hypothesis_repository import HypothesisRepository, get_current_tenant_id
        repo = HypothesisRepository()
        h = repo.get(hyp_id)
        if h is None:
            return f"Hypothesis '{hyp_id}' not found in repository."

        transferred = _analogy().transfer_hypothesis(h, target_domain)
        if transferred is None:
            return f"No applicable analogy found for domain '{h.domain}' → '{target_domain}'"

        # Save as new hypothesis in repo
        from datetime import datetime, timezone
        new_h = Hypothesis(
            title=transferred.transferred_title,
            description=transferred.transferred_description,
            domain=transferred.transferred_domain,
            confidence=transferred.adjusted_confidence,
            provenance=[{
                "source": "transfer_analogy",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "original_id": transferred.original_id,
                "analogy_rules": transferred.analogy_rules_used,
                "adjustment_factor": transferred.adjusted_confidence / h.confidence if h.confidence else 1.0,
            }],
        )
        new_h.metadata["derived_from"] = transferred.original_id
        new_h.metadata["transfer_analogy_ids"] = transferred.analogy_rules_used
        repo.add(new_h)

        return (
            f"**Transferred hypothesis created**\n"
            f"  New ID: {new_h.id}\n"
            f"  Title: {new_h.title}\n"
            f"  Domain: {new_h.domain}\n"
            f"  Confidence: {new_h.confidence:.4f} (from {h.confidence:.4f} × adjustment)\n"
            f"  Provenance: transferred from {transferred.original_id}\n\n"
            f"⚠️ *Analogous hypothesis – not experimentally validated*"
        )
    except Exception as e:
        return f"Error: {e}"

def _transfer_usage() -> str:
    return (
        "**Usage:**\n"
        "  `/transfer analogies`                              — list analogies\n"
        "  `/transfer add biology enzyme chemistry catalyst`   — add analogy\n"
        "  `/transfer add biology enzyme chemistry catalyst 0.9` — with weight\n"
        "  `/transfer apply <hyp_id> chemistry`               — transfer hypothesis\n\n"
        "**Examples:**\n"
        "  /transfer add biology receptor chemistry binding_site 0.85\n"
        "  /transfer apply hypo_abc chemistry"
    )


# ── Helpers ───────────────────────────────────────────────────────────────────

def _isfloat(s: str) -> bool:
    try:
        float(s)
        return True
    except Exception:
        return False