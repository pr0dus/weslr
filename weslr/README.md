# Weslr — Entity Intelligence Platform with Consciousness Signatures

**Weslr** is an OpenClaw-powered entity intelligence platform that detects, tracks, and reasons about consciousness signatures across domains. It combines causal reasoning, meta-analysis, cross-domain analogy transfer, and temporal/spatial reasoning into a unified queryable system.

---

## Installation

```bash
# Clone the repository
git clone https://github.com/pr0dus/weslr.git
cd weslr

# Install dependencies
pip install -e .

# Run tests
python -m pytest tests/ -v
```

**Requirements:** Python 3.10+

---

## Command Reference

### Phase 1–4: Core Entity & Causality

| Command | Description |
|---------|-------------|
| `/entity <name>` | Query entity by name |
| `/cause <effect>` | Find causes of an effect |
| `/consciousness <entity>` | Check consciousness signature |
| `/graph` | Entity relationship graph |
| `/introspect` | Internal model inspection |

### Phase 5–6: Hypothesis & Evidence

| Command | Description |
|---------|-------------|
| `/hypothesis add <title> [confidence]` | Create new hypothesis |
| `/hypothesis list` | List all hypotheses |
| `/hypothesis get <id>` | Get hypothesis details |
| `/hypothesis revise <id> <field> <value>` | Update hypothesis |
| `/evidence add <hyp_id> <content>` | Add evidence to hypothesis |
| `/evidence list <hyp_id>` | List evidence for hypothesis |
| `/signal <query>` | Query signal store |

### Phase 7–8: Spatial & Temporal Reasoning

| Command | Description |
|---------|-------------|
| `/molecule <smiles>` | Analyze molecular geometry |
| `/propose shape <description>` | Propose 3D shape |
| `/timeseries <entity>` | Temporal analysis |
| `/forecast <entity> [horizon]` | Forecast future states |
| `/plan <goal>` | Create reasoning plan |
| `/plan explain <plan_id>` | Explain a plan |
| `/compare <a> <b>` | Compare two entities |

### Phase 9: Advanced Reasoning (Abduction, Meta-Analysis, Transfer Analogy)

| Command | Description |
|---------|-------------|
| `/abduce <observation>` | Generate plausible explanations from configured rules and observations |
| `/abduce rule add <if> <then> [confidence]` | Add abduction rule (default conf=0.8) |
| `/abduce rules` | List all current abduction rules |
| `/abduce clear` | Clear all abduction rules |
| `/meta add <id> <effect> <se> [n]` | Add study to meta-analysis pool |
| `/meta list` | Show all studies in pool |
| `/meta run [fixed\|random]` | Run meta-analysis (fixed-effect or random-effects DerSimonian-Laird) |
| `/meta remove <id>` | Remove a study from pool |
| `/meta clear` | Clear all studies |
| `/meta from_hypotheses <id1> <id2> ...` | Import studies from hypothesis repository |
| `/transfer analogies` | List all cross-domain analogies |
| `/transfer add <src_domain> <src> <tgt_domain> <tgt> [weight]` | Add custom analogy (default weight=0.8) |
| `/transfer apply <hyp_id> <target_domain>` | Transfer hypothesis to new domain via analogy |

---

## Example Outputs

### `/abduce`

```
/abduce rule add high_dose response_increase 0.85
→ Rule added: high_dose → response_increase (conf=0.85)

/abduce rule add low_sodium BP_down 0.9

/abduce BP_down
→ Possible explanations for: "BP_down"
  1. low_sodium  (confidence 0.9000)
     Rules: low_sodium→BP_down
  2. Unknown (if no rules match)
```

### `/meta`

```
/meta add study1 0.5 0.1 30
→ Study 'study1' added: effect=0.5000, SE=0.1000, n=30

/meta add study2 0.6 0.12 35
→ Study 'study2' added: effect=0.6000, SE=0.1200, n=35

/meta run fixed
→ **Meta-analysis — Fixed-effect (inverse-variance)**
   Pooled effect: 0.5300
   95% CI: [0.4120, 0.6480]
   z = 7.230, p = 0.0000 ***
   Heterogeneity:
     Cochran's Q = 0.580
     I² = 0.0% (low)
   ⚠️ *Synthesized from simulated/demo data – not for clinical decision making*
```

### `/transfer`

```
/transfer analogies
→ **Cross-domain analogies:**
   Built-in seed analogies:
     • enzyme[biology] → catalyst[chemistry] (w=0.90)
     • receptor[biology] → binding_site[chemistry] (w=0.85)
     ...

/transfer add biology enzyme chemistry catalyst 0.85
→ Analogy added: enzyme[biology] → catalyst[chemistry] (w=0.85)

/transfer apply hypo_abc chemistry
→ **Transferred hypothesis created**
   New ID: <generated>
   Title: Catalyst accelerates process
   Domain: chemistry
   Confidence: 0.8500 (from 1.0000 × adjustment)
   Provenance: transferred from hypo_abc
   ⚠️ *Analogous hypothesis – not experimentally validated*
```

---

### Phase 10: Collaboration & Explanation

| Command | Description |
|---------|-------------|
| `/workspace share <hypothesis_id>` | Share a hypothesis to the tenant-anonymized shared library |
| `/workspace library list` | List hypotheses available in the shared library |
| `/workspace import <shared_hypothesis_id>` | Import a hypothesis from the shared library |
| `/jupyter info` | Show Jupyter kernel connection status |
| `/explain hypothesis <id>` | Generate deterministic explanation for a hypothesis |
| `/explain cause <cause> <effect>` | Explain causal mechanism between cause and effect |
| `/explain abduce <observation>` | Explain why an abductive explanation was generated |

**Collaboration principles:** Shared hypotheses are tenant-anonymized. Explicit sharing is required. The shared library is deterministic and read-only for all observers.

---

### Phase 11: Frontier Science Proposer

| Command | Description |
|---------|-------------|
| `/frontier propose <domain>` | Generate novel hypotheses with multi-axis scoring and difficulty tiers |
| `/frontier propose <domain> --max N` | Limit to N proposals |
| `/frontier propose <domain> --novelty-threshold X` | Minimum novelty score (0–1) |
| `/frontier propose <domain> --difficulty {easy,moderate,hard,paradigm}` | Filter by difficulty level |
| `/frontier novelty "idea text"` | Check idea novelty via live PubMed/arXiv search |
| `/frontier refine <id> --constraint "text"` | Re-score proposal with additional constraints |
| `/frontier list` | List all stored proposals with IDs and difficulty |
| `/frontier show <id>` | Display full proposal with scores, experiment summary, and provenance |
| `/frontier generate --mode {plausible\|strangeness} [--domain D] [--max N] [--novelty-check] [--exhaustive] [--novelty-threshold X] [--min-stability {stable\|metastable\|any}] [--export]` | Generate candidates via unified matter generator; `--novelty-check` enables PubMed/arXiv; `--exhaustive` adds COD/OQMD/AFLOW/NOMAD/MP structural DB check (discards found candidates); `--min-stability` filters candidates by thermodynamic stability (requires `--exhaustive`); thermodynamic summary printed for each passing candidate |
| `/frontier novelty-exhaustive <formula>` | Exhaustive multi-source structural novelty check: queries COD, OQMD, AFLOW, NOMAD, and Materials Project (if API key set); returns hit counts per source and thermodynamic stability (energy above hull, formation energy, decomposition products, stability rating); use to verify a specific formula before synthesis |
| `/frontier discover --real [--domain D] [--max N] [--difficulty L] [--export]` | Live discovery: generates candidates and performs real PubMed/arXiv novelty checks; prompts for confirmation; exports proposals to JSON |
| `/frontier daemon status` | Show frontier daemon running state, last run time, and configuration |
| `/frontier daemon start` | Start the background frontier daemon (generates candidates periodically) |
| `/frontier daemon stop` | Stop the background frontier daemon |

**Difficulty tiers:** ★ Low-hanging fruit → ★★★★ Paradigm shift. All proposals labeled [FRONTIER PROPOSAL – UNVALIDATED]. High-risk proposals (risk > 0.7) flagged for operator review.
**Acknowledgment:** Live PubMed/arXiv search requires user acknowledgment on first call per session.

**Live discovery mode** (`/frontier discover --real`): Performs real, rate-limited PubMed/arXiv API calls to verify novelty of generated candidates. Requires interactive confirmation (or `WESLR_AUTO_CONFIRM_FRONTIER=1` env var). Output includes per-candidate progress indicators and exports proposals to `frontier_proposals_{domain}_{timestamp}.json`. Expected runtime: ~10–30 seconds depending on `--max`.

Example:
```
/frontier discover --real --domain materials --max 3 --export
⚠️  This will query live PubMed and arXiv APIs to check novelty. Continue? (y/n): y
🔄  Checking novelty for candidate 1/9 (FeNiCoCrMn sulfidation)...
   📡  PubMed: 1 paper | arXiv: 0 papers → novelty 0.50 (below threshold 0.95) → discarded.
🔄  Checking novelty for candidate 2/9 (LaTiO2N:Fe)...
   📡  PubMed: 0 papers | arXiv: 0 papers → novel!  ✅
✅ Proposal #1: LaTiO2N:Fe...
...
📁  Exported 2 proposals to frontier_proposals_materials_20260504_143022.json
```

---


## Architecture

```
weslr/
├── commands/          # CLI command handlers
│   └── advanced_commands.py   # Phase 9: /abduce, /meta, /transfer
├── modules/           # Core reasoning modules
│   ├── abductive_reasoner.py   # Backward-chaining explanation engine
│   ├── meta_analyst.py         # Fixed/random-effect meta-analysis
│   ├── transfer_analogy.py     # Cross-domain analogy engine
│   ├── hypothesis_repository.py
│   └── ...
├── deterministic_handlers.py   # Handler registry & dispatch
└── tests/
    └── test_advanced_reasoning.py
```

**Tenant isolation:** All modules are tenant-aware. The shared `_tenant_getter` defaults to `"default"` but can be swapped for multi-tenant deployments.

---

---

### Documentation Note

README is a user/developer help surface, not the authoritative doctrine source. Doctrine is tracked in `weslr/docs/WESLR_DOCTRINE_REGISTRY_V1.md`.

## Disclaimer

**All outputs are deterministic/rule-based.**

- Meta-analysis results: *Synthesized from simulated/demo data – not for clinical decision making.*
- Transfer hypotheses: *Analogous hypothesis – not experimentally validated.*
- Abduction explanations: *Plausible explanations – requires experimental validation.*

Results should be reviewed by a subject-matter expert before use in real-world decisions.

---

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `MATERIALS_PROJECT_API_KEY` | *(unset)* | API key for Materials Project. MP source is disabled if unset. |
| `WESLR_EXHAUSTIVE_TIMEOUT` | `10` | Timeout in seconds per API call during exhaustive structural checks. |
| `WESLR_AUTO_CONFIRM_FRONTIER` | `0` | Set to `1` to auto-confirm live PubMed/arXiv and exhaustive DB queries. |

**Doctrine:** All frontier science outputs are candidate pre-screening signals, not discovery claims. See `weslr/docs/WESLR_FRONTIER_EXHAUSTIVE_NOVELTY_THERMODYNAMICS_CANON_V1.md` for limitations on structural novelty, Materials Project stability ratings, and heuristic thermodynamics. Structure classification by stoichiometry is not crystallographic proof. Outputs must use "candidate for validation" language.

---

## Meaning-Vector Response Obligation Layer

**Canonical as of:** commit `18172135` (2026-05-07)

WESLR's main-door chat path now has a non-LLM Plan A for identity, memory, first-contact, and self-model questions.

**Architecture:**

```
raw text
  → analyze_meaning()          [linguistic_meaning.py]
    → MeaningVector (speech_act_scores, relational_scores, state_query_scores…)
  → determine_response_obligation()  [response_obligation.py]
    → ResponseObligation (obligation_type, required_state, disclosure_level…)
  → gather_meaning_state()     [meaning_state_context.py]
    → MeaningStateContext (sender_identity, memory_summary, self_model_summary…)
  → form_meaning_response()    [meaning_response.py]
    → MeaningResponseResult (content, candidate_type, confidence…)
```

**Candidate types:** `NEW_CONTACT_ORIENTATION`, `VERIFIED_CONTACT_ORIENTATION`, `IDENTITY_VERIFICATION`, `MEMORY_STATE_REPORT`, `SELF_MODEL_DESCRIPTION`, `CAPABILITY_ORIENTATION`, `CLARIFYING_QUESTION`, `BOUNDED_UNCERTAINTY`

**Integration points:**
- `chat_responder.respond_chat()` — chat-mode main door (local_bridge path)
- `dialogue.py Part 4` — communicator layer (communicator payload path)

**LLM is last resort.** Falls through to `_model_chat_response()` only when meaning-vector confidence thresholds are not met.

---

## Cognitive Weight Refinement System

**Canonical as of:** commit `2ed6b9d` (2026-05-07)

Governed framework for modifying WESLR's cognitive weights without drift or uncontrolled self-improvement.

**Architecture:**

```
Observation (safe_to_learn=True)
  → WeightProposal.create()  [status=proposed]
  → run_simulation()          [against 18 eval phrases]
  → operator reviews → approve / reject
  → WeightProposal.approve()  [status=approved]
  → weight_commands apply → GuardrailResult.check()
  → registry.set_pending() → save → old_value stored for rollback
```

**Files:**
- `cognitive_weights.py` — 22-weight registry with zone fields
- `weight_proposal.py` — proposal lifecycle
- `weight_simulation.py` — simulation against eval phrases
- `weight_observation.py` — observation capture
- `commands/weight_commands.py` — CLI

**Guardrail zones:**

| Zone | Description | Auto-apply | Manual-apply |
|---|---|---|---|
| `green` | Future low-risk lane | Blocked (global off) | Delta-limited |
| `yellow` | Meaning/obligation/ranking/memory weights | Blocked | Approval + delta limit |
| `red` | Identity verification weights | Blocked | Blocked in this phase |

**Global auto-apply:** `DISABLED` — requires explicit opt-in per weight.

**CLI:**
```
weight_commands.py status          # zone counts, global flag
weight_commands.py list --group <x> # zone, delta limits, locked
weight_commands.py propose --key <k> --value <v> --reason <r>
weight_commands.py proposals        # guardrail analysis per proposal
weight_commands.py approve <id>
weight_commands.py apply <id>       # requires approved + guardrail pass
weight_commands.py reset --key <k>
```

**Tests:** G1–G7 (refinement), H1–H12 (guardrails) in `test_cognitive_weight_refinement.py`

---

### What needs to be added (Next Steps)

| Priority | Item | File(s) |
|---|---|---|
| 1 | **Memory response quality** — replace raw memory file dump with structured session summary (date, topics, outcome) | `meaning_state_context.py`, `meaning_response.py` |
| 2 | **Self-model response quality** — replace `IDENTITY.md` raw dump with composed 2–3 sentence self-description | `meaning_state_context.py`, `meaning_response.py` |
| 3 | **Verified identity flow** — pass actual `test_identity_context` through `chat_responder.respond_chat()` so verified-identity responses fire in local_bridge path | `chat_responder.py` |
| 4 | **NEW_CONTACT_ORIENTATION** — remove "I'll note it" (no write path yet) or implement lightweight write handler | `meaning_response.py` |
| 5 | **Phrase family expansion** — grow `SPEECH_ACT_KEYWORDS` / `RELATIONAL_KEYWORDS` from observed messages rather than hand-authoring | `linguistic_meaning.py` |
| 6 | **Channel-level identity binding** — bind `sender_confidence` to device/channel metadata so identity persists across sessions | `ingress_adapter.py`, `chat_responder.py` |

**Documentation:** `docs/routing_diagnosis.md` covers root cause and resolution for the meaning-vector integration.
