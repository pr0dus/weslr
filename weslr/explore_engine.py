"""Goal-Driven Hypothesis Generation — /explore <goal> command engine."""

from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Optional

from weslr.goal_decomposer import decompose
from weslr.hypothesis_scorer import rank_hypotheses, format_hypothesis_list
from weslr.search_adapters.pubmed_adapter import search_pubmed
from weslr.search_adapters.arxiv_adapter import search_arxiv, search_and_store

# Optional SearXNG — imported lazily
_searxng_adapter = None


def _get_searxng():
    global _searxng_adapter
    if _searxng_adapter is None:
        try:
            from weslr.searxng_search_adapter import search_searxng
            _searxng_adapter = search_searxng
        except Exception:
            return None
    return _searxng_adapter


# ──────────────────────────────────────────────────────────────────────────────
# Domain Pattern Overrides (biology, chemistry, etc.)
# ──────────────────────────────────────────────────────────────────────────────

_BIOLOGY_PATTERNS = {
    "senolytic": ["senolytic", "senolytics", "dasatinib", "quercetin", "navitoclax", "fisetin"],
    "nad_boost": ["NAD+", "NMN", "NR", "nicotinamide riboside", "sirtuin", "mitochondrial"],
    "mrna": ["mRNA", "messenger RNA", "vaccine", "protein expression"],
    "gene_edit": ["CRISPR", "gene editing", "Cas9", "base editing"],
    "cell_aging": ["senescence", "p16", "p21", "senescent cells", "SASP"],
    "calcium_channel": ["TRPC", "calcium channel", "channel blocker"],
}


# ──────────────────────────────────────────────────────────────────────────────
# Experiment Protocol Templates
# ──────────────────────────────────────────────────────────────────────────────

_EXPERIMENT_TEMPLATES = {
    "in_vitro": (
        "Protocol (in vitro):\n"
        "  1. Culture target cells at ~70% confluence.\n"
        "  2. Treat with compound at graded concentrations (e.g., 0.1, 1, 10 µM).\n"
        "  3. Incubate for 24–72 h (timepoint based on mechanism).\n"
        "  4. Measure endpoint: cell viability (MTS/CCK-8), marker expression (Western / qPCR),\n"
        "     or functional assay (migration, invasion, etc.).\n"
        "  5. Includevehicle and positive controls.\n"
        "  6. n≥3 biological replicates; statistical test: t-test or ANOVA."
    ),
    "dft": (
        "Protocol (DFT calculation):\n"
        "  1. Build structural model from experimental CIF or theoretical geometry.\n"
        "  2. Optimize using DFT functional (e.g., PBE, HSE06) with plane-wave basis.\n"
        "  3. Compute band structure, density of states, and formation energy.\n"
        "  4. For doped systems, simulate defect configurations and calculate transition levels.\n"
        "  5. Verify convergence wrt k-point mesh and cutoff energy.\n"
        "  6. Compare with experimental data (bandgap, mobility)."
    ),
    "synthesis": (
        "Protocol (chemical synthesis):\n"
        "  1. Start from commercially available precursors (purity ≥ 95%).\n"
        "  2. Apply standard synthetic route:Schlenk line / inert atmosphere for air-sensitive reagents.\n"
        "  3. Monitor reaction progress by TLC or in-situ IR.\n"
        "  4. Purify product by column chromatography, recrystallization, or sublimation.\n"
        "  5. Confirm identity: 1H/13C NMR, HRMS, and melting point (if applicable).\n"
        "  6. Characterize purity by HPLC before biological testing."
    ),
    "in_vivo": (
        "Protocol (in vivo):\n"
        "  1. Obtain IACUC/ethics approval before study.\n"
        "  2. Use age-appropriate animal model (e.g., 18-month-old mice for aging studies).\n"
        "  3. Randomize animals into groups: vehicle, low dose, high dose.\n"
        "  4. Administer compound (route: oral/i.p.) for 4–12 weeks.\n"
        "  5. Measure endpoints: senescence markers (p16 reporter), organ function panels,\n"
        "     motor performance (rotarod, gait), and survival.\n"
        "  6. Blind analysis; statistical test: log-rank for survival, t-test for body weight."
    ),
    "pilot_screen": (
        "Protocol (pilot screening):\n"
        "  1. Compile library of compounds targeting hypothesis components.\n"
        "  2. Use in silico filtering: Lipinski rules, PAINS filter, similarity to known actives.\n"
        "  3. Score and rank by predicted activity (docking, QSAR, or上皮 viability assay).\n"
        "  4. Top 20 compounds advanced to experimental validation.\n"
        "  5. Report SAR (structure–activity relationship) summary."
    ),
}


def get_experiment_template(method: str) -> str:
    """Return a formatted experimental protocol template."""
    tpl = _EXPERIMENT_TEMPLATES.get(method.lower().replace("-", "_").replace(" ", "_"), "")
    if not tpl:
        return (
            f"Protocol ({method}):\n"
            "  1. Define readout based on mechanism of action.\n"
            "  2. Set appropriate controls (positive + negative).\n"
            "  3. Run assay in triplicate, ≥3 biological replicates.\n"
            "  4. Apply statistical test and report p-value.\n"
            "  5. Replicate in independent cohort before drawing conclusions."
        )
    return tpl


# ──────────────────────────────────────────────────────────────────────────────
# Knowledge Graph Builder
# ──────────────────────────────────────────────────────────────────────────────

def build_entity_graph(search_results: list[dict]) -> dict[str, dict]:
    """Build a temporary in-memory entity graph from search results.

    Returns dict: entity_name → {type, description, sources, relationships}
    """
    entities: dict[str, dict] = {}
    relationships: list[tuple[str, str, str]] = []  # (entity_a, entity_b, relationship)

    for result in search_results:
        text = result.get("title", "") + " " + result.get("abstract", result.get("summary", ""))
        result_id = result.get("arxiv_id", result.get("pmid", ""))

        # Simple keyword co-occurrence relationships
        rel_pairs = [
            ("senolytic", "senescent cells"),
            ("NAD+", "mitochondria"),
            ("NMN", "sirtuin"),
            ("TRPC", "calcium"),
            ("rapamycin", "mTOR"),
            ("dasatinib", "quercetin"),
            ("mTOR", "autophagy"),
            ("autophagy", "mitochondrial"),
            ("CRISPR", "gene editing"),
            ("gene editing", "base editing"),
            ("senolytic", "SASP"),
            ("SASP", "inflammation"),
            ("inflammation", "chronic disease"),
            ("nanoparticle", "drug delivery"),
            ("quantum dot", "photovoltaic"),
            ("bandgap", "efficiency"),
            ("kesterite", "Cu2ZnSn"),
            ("perovskite", "solar cell"),
            ("catalyst", "hydrogen"),
            ("electrolyzer", "hydrogen"),
        ]

        for a, b in rel_pairs:
            if a.lower() in text.lower() and b.lower() in text.lower():
                relationships.append((a, b, "co-occurs"))

        # Extract entities (named tokens)
        for match in _ENTITY_PATTERNS.findall(text):
            entity_name = match.strip()
            if len(entity_name) > 2 and len(entity_name) < 60:
                if entity_name not in entities:
                    entities[entity_name] = {
                        "type": _infer_entity_type(entity_name),
                        "description": result.get("title", "")[:100],
                        "sources": [result_id] if result_id else [],
                        "relationships": [],
                    }
                else:
                    if result_id and result_id not in entities[entity_name]["sources"]:
                        entities[entity_name]["sources"].append(result_id)

    # Build relationship lists into entity dicts
    for a, b, rel in relationships:
        if a in entities:
            entities[a]["relationships"].append({"target": b, "type": rel})
        if b in entities:
            entities[b]["relationships"].append({"target": a, "type": rel})

    return entities


_ENTITY_PATTERNS = __import__("re").compile(
    r"\b([A-Z][A-Za-z0-9]*(?:\s+[A-Z][A-Za-z0-9]+){0,3})\b"
)


def _infer_entity_type(name: str) -> str:
    """Infer the type of an entity from its name."""
    name_lower = name.lower()
    if any(k in name_lower for k in ["protein", "gene", "crispr", "cas", "mrna"]):
        return "biomolecule"
    if any(k in name_lower for k in ["cell", "tissue", "organ", "fibroblast", "neuron"]):
        return "cell_type"
    if any(k in name_lower for k in ["disease", "cancer", "tumor", "carcinoma", "glioma"]):
        return "disease"
    if any(k in name_lower for k in ["compound", "drug", "agent", "inhibitor", "activator"]):
        return "compound"
    if any(k in name_lower for k in ["reaction", "synthesis", "pathway", "cascade"]):
        return "pathway"
    return "concept"


# ──────────────────────────────────────────────────────────────────────────────
# Combinatorial Hypothesis Generator
# ──────────────────────────────────────────────────────────────────────────────

def generate_hypotheses(
    entities: dict,
    goal: str,
    domain: Optional[str] = None,
    max_hypotheses: int = 10,
) -> list[dict]:
    """Generate novel hypotheses by recombining entities from the knowledge graph.

    Combines entities that co-occur in literature but have not been explicitly
    tested together in a single study.
    """
    hypotheses: list[dict] = []

    # Domain-specific combination rules
    rules = _DOMAIN_COMBINATION_RULES.get(domain or "generic", [])

    for rule in rules:
        rule_name = rule.get("name", "unnamed")
        desc = rule.get("description", "")
        components = rule.get("components", [])

        for entity_name, entity_data in entities.items():
            for comp in components:
                comp_lower = comp.lower()
                # Check if comp appears in entity name or its relationships
                if comp_lower in entity_name.lower():
                    continue

                # Try to create a hypothesis combining entity with component
                hyp_name = f"{entity_name} + {comp}"
                hyp_desc = desc.format(entity=entity_name, component=comp)

                # Check if components are independently supported in sources
                entity_sources = entity_data.get("sources", [])
                supporting = []
                for src_id in entity_sources:
                    supporting.append({
                        "id": src_id,
                        "title": entity_data.get("description", ""),
                        "trust_score": 0.65,
                    })

                hypotheses.append({
                    "name": hyp_name,
                    "description": hyp_desc,
                    "components": [entity_name, comp],
                    "predicted_effect": _predict_effect(entity_name, comp, domain),
                    "supporting_sources": supporting,
                    "suggested_next_step": _suggest_next_step(entity_name, comp, domain),
                    "rule": rule_name,
                    "domain": domain,
                    "formula": "",
                })

    # If no domain rules matched, fall back to generic co-occurrence combinations
    if not hypotheses:
        hypotheses = _generic_cooccurrence_hypotheses(entities, goal, domain)

    # Deduplicate by name
    seen: set[str] = set()
    unique = []
    for h in hypotheses:
        if h["name"] not in seen:
            seen.add(h["name"])
            unique.append(h)

    return unique[:max_hypotheses]


def _predict_effect(entity: str, component: str, domain: Optional[str]) -> str:
    """Generate a qualitative predicted effect statement."""
    e = entity.lower()
    c = component.lower()

    # Normalize compound names for senolytic recognition
    senolytics = {"dasatinib", "quercetin", "fisetin", "navitoclax", "abt-263",
                  "azd-1152", "umbelliferone", "piperlongumine"}
    nad_boosters = {"nmn", "nr", "nicotinamide riboside", "nad+", "nad"}
    entities_combined = e + " " + c

    if domain == "biology":
        entity_is_senolytic = any(s in e for s in senolytics)
        comp_is_senolytic = any(s in c for s in senolytics)
        entity_is_nad = any(s in e for s in nad_boosters)
        comp_is_nad = any(s in c for s in nad_boosters)

        if entity_is_senolytic and comp_is_senolytic:
            return "may reduce senescent cell burden, lowering SASP-associated inflammation"
        if (entity_is_nad or comp_is_nad) and (entity_is_senolytic or comp_is_senolytic):
            return "may reduce senescent cell burden while restoring NAD+/mitochondrial function"
        if entity_is_nad or comp_is_nad:
            return "may improve mitochondrial function and energy metabolism"
        if entity_is_senolytic or comp_is_senolytic:
            return "may reduce senescent cell burden, lowering SASP-associated inflammation"
        if "mtr" in e or "mtr" in c or "rapamycin" in e or "rapamycin" in c:
            return "may inhibit mTOR signaling, promoting autophagy and longevity"
        if "crispr" in e or "crispr" in c:
            return "may enable precise gene editing to correct disease-associated mutations"
        if "trpc" in e or "trpc" in c or "calcium channel" in entities_combined:
            return "may modulate calcium influx, reducing pathological signaling"
        if "nanoparticle" in e or "nanoparticle" in c:
            return "may improve drug delivery specificity to target tissue"
        if "folate" in e or "folate" in c:
            return "may improve targeted uptake in tumor cells via folate receptor"
        if "gold nanoparticle" in entities_combined or "au nanoparticle" in entities_combined:
            return "may enable targeted nanomedicine delivery across the blood-brain barrier"
        if "glioblastoma" in entities_combined or "glioma" in entities_combined:
            return "may improve therapeutic efficacy against glioblastoma"

    if domain == "materials_science":
        if "bandgap" in e or "bandgap" in c:
            return "may increase power conversion efficiency by optimizing light absorption"
        if "kesterite" in e or "kesterite" in c:
            return "may improve open-circuit voltage and stability of kesterite solar cells"
        if "perovskite" in e or "perovskite" in c:
            return "may enhance efficiency and reduce lead content in perovskite cells"
        if "catalyst" in e or "catalyst" in c:
            return "may improve catalytic activity and selectivity for target reaction"

    return "predicted to improve outcome based on known mechanisms"


def _suggest_next_step(entity: str, component: str, domain: Optional[str]) -> str:
    """Suggest a concrete next experimental step."""
    e = entity.lower()
    c = component.lower()
    combined = e + " " + c
    senolytics = {"dasatinib", "quercetin", "fisetin", "navitoclax", "abt-263", "azd-1152"}
    nad_boosters = {"nmn", "nr", "nicotinamide riboside", "nad+", "nad"}

    entity_is_senolytic = any(s in e for s in senolytics)
    comp_is_senolytic = any(s in c for s in senolytics)
    entity_is_nad = any(s in e for s in nad_boosters)
    comp_is_nad = any(s in c for s in nad_boosters)

    if domain == "biology":
        if entity_is_senolytic or comp_is_senolytic:
            return "In vitro assay on aged fibroblasts; measure SA-β-gal and SASP markers"
        if entity_is_nad or comp_is_nad:
            return "Measure mitochondrial oxygen consumption rate (OCR) in treated cells"
        if "crispr" in combined:
            return "Design guide RNA, deliver RNP complex, assay editing efficiency"
        if "trpc" in combined or "calcium channel" in combined:
            return "Patch-clamp electrophysiology on target cells with and without blocker"
        if "folate" in combined:
            return "Test folate-conjugated compound on folate-receptor-positive tumor cells; measure uptake by flow cytometry"
        if "gold nanoparticle" in combined or "au nanoparticle" in combined:
            return "Synthesize gold nanoparticle conjugates; test blood-brain barrier penetration in transwell model"
        if "glioblastoma" in combined or "glioma" in combined:
            return "Test in glioblastoma cell lines (U87, LN229); measure IC50 and apoptosis markers"
        return "In vitro viability assay with multiple concentrations; include positive control"

    if domain == "materials_science":
        if any(k in combined for k in ["kesterite", "perovskite", "solar"]):
            return "Synthesize and fabricate thin-film device; measure J-V curve under AM1.5"
        if "catalyst" in combined:
            return "Run DFT calculation to optimize binding energy; test turnover frequency"
        if "bandgap" in combined:
            return "Compute band structure via DFT; fabricate device and measure EQE"
        return "Run DFT structural optimization; fabricate and test in device"

    return "Review literature for similar studies; design pilot experiment with controls"


def _generic_cooccurrence_hypotheses(
    entities: dict,
    goal: str,
    domain: Optional[str],
) -> list[dict]:
    """Generate hypotheses from generic entity co-occurrence patterns."""
    hypotheses: list[dict] = []

    # Build co-occurrence pairs from entity relationship lists
    pairs: list[tuple[str, str]] = []
    for entity_name, entity_data in entities.items():
        for rel in entity_data.get("relationships", []):
            target = rel.get("target", "")
            if target and target in entities:
                pairs.append((entity_name, target))

    # Remove duplicate and reversed pairs
    unique_pairs = list({frozenset([a, b]): (a, b) for a, b in pairs}.values())

    for a, b in unique_pairs[:10]:
        data_a = entities.get(a, {})
        data_b = entities.get(b, {})
        sources = [
            {"id": src, "title": data_a.get("description", ""), "trust_score": 0.65}
            for src in data_a.get("sources", [])[:2]
        ]
        sources += [
            {"id": src, "title": data_b.get("description", ""), "trust_score": 0.65}
            for src in data_b.get("sources", [])[:2]
        ]

        hyp_name = f"{a} + {b}"
        hyp_desc = (
            f"Co-occurring entities '{a}' and '{b}' suggest a potential synergistic "
            f"interaction that has not been explicitly tested in the same study."
        )

        hypotheses.append({
            "name": hyp_name,
            "description": hyp_desc,
            "components": [a, b],
            "predicted_effect": _predict_effect(a, b, domain),
            "supporting_sources": sources[:4],
            "suggested_next_step": _suggest_next_step(a, b, domain),
            "rule": "generic_cooccurrence",
            "domain": domain,
            "formula": "",
        })

    return hypotheses


_DOMAIN_COMBINATION_RULES: dict[str, list[dict]] = {
    "biology": [
        {
            "name": "senolytic_nad_combination",
            "description": "Combine senolytic {component} with NAD+ booster {entity} for synergistic anti-aging effect",
            "components": ["dasatinib", "quercetin", "fisetin", "navitoclax", "NMN", "NR"],
        },
        {
            "name": "trpc_calcium_blocker",
            "description": "TRPC calcium channel blocker {component} may reduce pathological calcium overload in {entity}",
            "components": ["TRPC5 blocker", "SKF-96365", "Gd3+", "carvacrol"],
        },
        {
            "name": "mtdna_mtor_combo",
            "description": "Inhibit mTOR with {component} while upregulating NAD+ in {entity} for synergistic autophagy",
            "components": ["rapamycin", "everolimus", "NMN", "resveratrol"],
        },
        {
            "name": "crispr_nanov",
            "description": "Deliver CRISPR gene editor {component} via nanoparticle {entity} for targeted in vivo editing",
            "components": ["gold nanoparticle", "lipid nanoparticle", "polymer nanoparticle"],
        },
        {
            "name": "immune_checkpoint_aging",
            "description": "Combine immune checkpoint modulation ({component}) with senolytic {entity} to boost immune surveillance",
            "components": ["anti-PD1", "anti-CTLA4", "fisetin", "dasatinib+quercetin"],
        },
    ],
    "materials_science": [
        {
            "name": "bandgap_optimization",
            "description": "Adjust bandgap of {entity} by alloying with {component} to improve carrier separation",
            "components": ["S", "Se", "Te", "Ga", "In"],
        },
        {
            "name": "interface_engineering",
            "description": "Modify interface between {entity} and transport layer using {component}",
            "components": ["TiO2", "Spiro-OMeTAD", "PTAA", "PCBM"],
        },
        {
            "name": "nanostructure_perovskite",
            "description": "Add nanostructured {component} to {entity} to increase light absorption and charge collection",
            "components": ["nanorods", "nanowires", "quantum dots", "plasmons"],
        },
    ],
}


# ──────────────────────────────────────────────────────────────────────────────
# Main Explore Function
# ──────────────────────────────────────────────────────────────────────────────

def explore(
    goal: str,
    domain: Optional[str] = None,
    max_results_per_adapter: int = 8,
    top_n: int = 5,
    timeout_per_adapter: float = 15.0,
) -> dict[str, Any]:
    """Run goal-driven hypothesis generation.

    Steps:
    1. Decompose goal into keywords and queries
    2. Run parallel searches across all available adapters
    3. Build temporary entity graph from results
    4. Generate hypotheses via combinatorial rules + co-occurrence
    5. Score hypotheses
    6. Return ranked results

    Returns dict with keys:
      - hypotheses: list of scored hypothesis dicts
      - search_summary: dict of adapter → result counts
      - goal_decomposition: dict from goal_decomposer
      - entities: dict of extracted entities
    """
    # ── Step 1: Decompose ────────────────────────────────────────────────────
    decomp = decompose(goal, domain=domain)
    detected_domain = decomp["domain"] or domain or "generic"
    queries = decomp["query_components"]

    # ── Step 2: Parallel Search ─────────────────────────────────────────────
    search_results: list[dict] = []
    search_summary: dict[str, int] = {}

    # arXiv search
    arxiv_start = time.time()
    arxiv_results: list[dict] = []
    for q in queries[:4]:  # cap at 4 queries for arXiv
        if time.time() - arxiv_start > timeout_per_adapter:
            break
        try:
            res = search_arxiv(q, max_results=max_results_per_adapter, sort_by="relevance")
            arxiv_results.extend(res)
        except Exception:
            pass
    # Deduplicate by arXiv ID
    seen_arxiv = set()
    for r in arxiv_results:
        if r["arxiv_id"] not in seen_arxiv:
            seen_arxiv.add(r["arxiv_id"])
            r["source_adapter"] = "arxiv"
            search_results.append(r)
    search_summary["arxiv"] = len(seen_arxiv)

    # PubMed search
    pubmed_start = time.time()
    pubmed_results: list[dict] = []
    for q in queries[:3]:  # cap at 3 for PubMed
        if time.time() - pubmed_start > timeout_per_adapter:
            break
        try:
            _, articles = search_pubmed(q, max_results=max_results_per_adapter)
            for a in articles:
                a["source_adapter"] = "pubmed"
                pubmed_results.append(a)
        except Exception:
            pass
    seen_pmid = set()
    for r in pubmed_results:
        if r["pmid"] not in seen_pmid:
            seen_pmid.add(r["pmid"])
            search_results.append(r)
    search_summary["pubmed"] = len(seen_pmid)

    # SearXNG search (optional, lazy import)
    searxng_count = 0
    searxng_fn = _get_searxng()
    if searxng_fn:
        try:
            for q in queries[:2]:
                sx_results = searxng_fn(q, max_results=max_results_per_adapter)
                for r in sx_results:
                    r["source_adapter"] = "searxng"
                    search_results.append(r)
                    searxng_count += 1
            search_summary["searxng"] = searxng_count
        except Exception:
            search_summary["searxng"] = 0

    # ── Step 3: Build Entity Graph ─────────────────────────────────────────
    entities = build_entity_graph(search_results)

    # ── Step 4: Generate Hypotheses ───────────────────────────────────────
    raw_hypotheses = generate_hypotheses(
        entities,
        goal,
        domain=detected_domain,
        max_hypotheses=top_n * 3,  # generate more than needed for scoring
    )

    # ── Step 5: Score Hypotheses ───────────────────────────────────────────
    scored = rank_hypotheses(raw_hypotheses)

    return {
        "hypotheses": scored,
        "search_summary": search_summary,
        "goal_decomposition": decomp,
        "entities": entities,
        "total_results": sum(search_summary.values()),
    }
