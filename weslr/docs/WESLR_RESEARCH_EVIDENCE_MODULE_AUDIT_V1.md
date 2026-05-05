# WESLR Research / Evidence Module Audit V1

**Date:** 2026-05-04
**Scope:** All existing WESLR research/search/evidence modules — purpose, safety, external call profile, state writes, and suitability for future Research Work Loop integration.
**Constraint:** No code written or refactored. No external searches run.

---

## 1. Purpose

This audit catalogs every module in the WESLR codebase that performs external search, evidence ingestion, hypothesis generation, or domain-specific discovery. It exists to answer one question before any Research Work Loop implementation proceeds:

> Which modules can safely participate in an automated mission loop, which need governance wrappers, and which must remain operator-only?

All 20 inventory items are mapped to Research Work Loop connection points (`mission.allowed_sources`, `mission.evidence_links`, `mission.current_questions`, `run_once_mission_review()`, `.weslr/pending_messages.jsonl`, Phase 7 hypothesis/evidence store) and classified A–F. Safety gates are defined per external source type.

---

## 2. Existing Modules Inventory

### 2.1 PubMed Adapter
- **File:** `weslr/search_adapters/pubmed_adapter.py` (84 lines)
- **Purpose:** NCBI E-utilities wrapper — `esearch` (PMID list) + `efetch` (abstracts, titles, authors, journal, year, URL). Returns structured dicts. No API key required.
- **External calls:** Yes — `https://eutils.ncbi.nlm.nih.gov/entrez/eutils/{esearch,efetch}.fcgi`
- **Writes state:** No
- **State files:** None
- **Tested:** Partial — `test_pubmed_adapter_v1.py` mocks HTTP responses (mock XML for efetch, mocked esearch). No live test calls.
- **Safe for mission loop:** Needs wrapper (see §6)

### 2.2 arXiv Adapter
- **File:** `weslr/search_adapters/arxiv_adapter.py` (232 lines)
- **Purpose:** arXiv API query + fact extraction from abstracts. `search_arxiv()` returns result dicts. `search_and_store()` writes an evidence packet and extracts facts. `extract_arxiv_facts()` calls `fact_extractor`. No API key required.
- **External calls:** Yes — `http://export.arxiv.org/api/query`
- **Writes state:** Yes — `append_evidence_packet()` to `.weslr/external_evidence_packets.jsonl`
- **State files:** `.weslr/external_evidence_packets.jsonl`
- **Tested:** Partial — mocked at HTTP layer. `search_and_store()` covered via mocked adapter.
- **Safe for mission loop:** Needs wrapper — writes evidence packets without mission gate.

### 2.3 PubChem Adapter
- **File:** `weslr/search_adapters/pubchem_adapter.py` (292 lines)
- **Purpose:** PUG REST API wrapper — compound name→CID lookup, molecular property fetching, CID→properties, SMILES/InChI lookup, similar compound search. No API key required.
- **External calls:** Yes — `https://pubchem.ncbi.nlm.nih.gov/rest/pug`
- **Writes state:** No (read-only queries)
- **State files:** None
- **Tested:** No test file found.
- **Safe for mission loop:** B — usable with small adapter. Read-only but hits external API; needs `mission.allowed_sources` gate.

### 2.4 SearXNG Adapter
- **File:** `weslr/searxng_search_adapter.py` (340 lines)
- **Purpose:** General-purpose web search via self-hosted SearXNG instance. **Disabled by default.** Enable only via `WESLR_SEARXNG_ENABLED=true` environment variable.
- **External calls:** Yes — any URL configured in `WESLR_SEARXNG_URL` (default `http://localhost:8888`)
- **Writes state:** No
- **State files:** None
- **Tested:** No test file found. Comment explicitly states HTTP calls are mocked in tests.
- **Safe for mission loop:** D — unsafe for automatic mission use. Disabled by default. Would require both env flag AND mission opt-in. General web crawl is out of scope for Research Work Loop V2.

### 2.5 Evidence Packet Store
- **File:** `weslr/search_adapters/evidence_packet_store.py` (126 lines)
- **Purpose:** Append-only JSONL writer for external evidence packets. Multi-tenant aware. Provides `append_evidence_packet()`, `load_packets()`, `get_packet()`.
- **External calls:** No
- **Writes state:** Yes — appends to `.weslr/external_evidence_packets.jsonl`
- **State files:** `.weslr/external_evidence_packets.jsonl`
- **Tested:** Yes — covered indirectly via `test_pubmed_adapter_v1.py`
- **Safe for mission loop:** A — appropriate for mission loop. Append-only with explicit packet_id generation. Authority label required on packet.

### 2.6 Evidence Packet Builder
- **File:** `weslr/evidence_packet_builder.py` (218 lines)
- **Purpose:** Normalizes SearXNG search results into bounded evidence packets. Defines `SAFE_FIELDS` (title, url, content, source, authority) and `UNSAFE_FIELDS` (raw, cookies, api_key, etc.). Truncates content at 2000 chars. Validates record type. Read-only.
- **External calls:** No
- **Writes state:** No
- **State files:** None
- **Tested:** Partial — field filtering not independently tested
- **Safe for mission loop:** A — read-only normalizer. Suitable for mission loop evidence normalization.

### 2.7 Fact Extractor
- **File:** `weslr/fact_extractor.py` (520 lines)
- **Purpose:** Extracts subject-predicate-object triples from text using regex patterns. Supports domain-specific pattern files (`fact_patterns/`) for materials_science, chemistry, cancer_research, astronomy. Has `append_enriched_fact()` which writes to fact store. Also `extract_facts_with_positions()` for document-level extraction.
- **External calls:** No
- **Writes state:** Yes — `append_enriched_fact()` writes to `.weslr/fact_assertions.jsonl`
- **State files:** `.weslr/fact_assertions.jsonl`
- **Tested:** Yes — `test_fact_extractor_v1.py` exists
- **Safe for mission loop:** C — needs governance/safety wrapper. Writes facts to fact store. Must not promote extracted facts to trusted WESLR memory without operator review. No hazard detection on fact content.

### 2.8 Source Trust Ranking
- **File:** `weslr/source_trust_ranking.py` (292 lines)
- **Purpose:** Classifies URLs into source type (academic, reference, news, forum, etc.) and trust tier (high/medium/low/unknown). Pure read-only ranking — does not verify truth. Returns classification dict per result.
- **External calls:** No
- **Writes state:** No
- **State files:** None
- **Tested:** Partial — logic covered by integration tests
- **Safe for mission loop:** A — read-only ranker. Suitable for mission loop result ordering.

### 2.9 Deterministic Handlers
- **File:** `weslr/deterministic_handlers.py` (3425 lines)
- **Purpose:** Central registry + dispatch for deterministic ISS/plan queries. Imports and wires pubmed adapter, evidence_packet_store, fact_extractor, and proposal handlers (nanotech, communications, combinatorial materials, combinatorial chemistry, chemistry reaction predictor). Large. Dispatches on trigger prefixes.
- **External calls:** Indirect — through imported adapters (pubmed, arxiv via fact_extractor)
- **Writes state:** Via imported modules — fact_extractor writes fact assertions; arxiv adapter writes evidence packets
- **State files:** `.weslr/fact_assertions.jsonl`, `.weslr/external_evidence_packets.jsonl`
- **Tested:** Partial — `test_deterministic_handler_classification.py`
- **Safe for mission loop:** C — large registry mixing read-only and write-capable imports. Needs careful mission-gated subsetting.

### 2.10 Biology Discovery
- **File:** `weslr/biology_discovery.py` (58 lines)
- **Purpose:** Convenience wrapper around `discovery.discovery_engine`. Generates and ranks biology-domain candidates (ion channels, signaling pathways, bionanoparticles, cell targeting). Calls `generate_candidates()` and `rank_candidates()`.
- **External calls:** No
- **Writes state:** Via discovery_engine — candidates are generated in-memory, not persisted unless discovery_engine writes
- **State files:** None directly; discovery config at `discovery/domains/biology/`
- **Tested:** No dedicated test found
- **Safe for mission loop:** C — biology domain. Sensitive. Needs governance/safety wrapper and explicit mission opt-in for any external data source or synthesis guidance.

### 2.11 Chemistry Reaction Predictor
- **File:** `weslr/chemistry_reaction_predictor.py` (107 lines)
- **Purpose:** Rule-based reaction product prediction from reactant inputs using `chemistry_rules.json`. Read-only lookup — no execution of reactions.
- **External calls:** No
- **Writes state:** No
- **State files:** `chemistry_rules.json` (read)
- **Tested:** No dedicated test found
- **Safe for mission loop:** B — read-only rules. Usable with small adapter. No synthesis execution. No hazard detection on reaction rules.

### 2.12 Combinatorial Materials
- **File:** `weslr/combinatorial_materials.py` (690 lines)
- **Purpose:** Rule-based combinatorial generator for inorganic/materials science combinations (perovskites, oxides, chalcogenides). Generates candidate compositions, applies DFT feasibility filters, formats proposal output.
- **External calls:** No
- **Writes state:** No
- **State files:** None
- **Tested:** No dedicated test found
- **Safe for mission loop:** B — read-only generation. Usable with small adapter. No external calls. No hazard on materials combinations.

### 2.13 Combinatorial Chemistry
- **File:** `weslr/combinatorial_chemistry.py` (577 lines)
- **Purpose:** Rule-based combinatorial generator for chemistry — organic synthesis routes, functional groups, reaction classes. Similar structure to combinatorial_materials.
- **External calls:** No
- **Writes state:** No
- **State files:** None
- **Tested:** No dedicated test found
- **Safe for mission loop:** B — read-only generation. No external calls. Usable with small adapter. Chemistry safety filter recommended.

### 2.14 Explore Engine
- **File:** `weslr/explore_engine.py` (630 lines)
- **Purpose:** `/explore <goal>` command engine. Drives hypothesis generation from a user goal. Uses PubMed and arXiv adapters for literature search, optionally SearXNG. Includes domain pattern overrides for biology and chemistry topics. Provides experiment protocol templates (in_vitro, DFT, synthesis, in_vivo, characterization). Writes nothing itself.
- **External calls:** Via adapters — PubMed (`search_pubmed`), arXiv (`search_arxiv`, `search_and_store`), optional SearXNG (lazy import)
- **Writes state:** Indirect — arXiv adapter calls `append_evidence_packet()`; fact_extractor may write via arXiv adapter's `extract_arxiv_facts()`
- **State files:** `.weslr/external_evidence_packets.jsonl` (via arXiv adapter), `.weslr/fact_assertions.jsonl` (via fact extraction)
- **Tested:** Yes — `test_explore.py` exists
- **Safe for mission loop:** C — direct use of external adapters without mission gate. Needs wrapper that routes through mission context.

### 2.15 Hypothesis Scorer
- **File:** `weslr/hypothesis_scorer.py` (417 lines)
- **Purpose:** Scores, ranks, and formats hypotheses from `/explore`. Includes chemical formula feasibility checking (`check_charge_balance()`), novelty scoring, scientific plausibility heuristics. Read-only.
- **External calls:** No
- **Writes state:** No
- **State files:** None
- **Tested:** Partial — formula charge balance covered by integration tests
- **Safe for mission loop:** A — read-only scorer. Suitable for mission loop hypothesis ranking.

### 2.16 Evidence Answer Builder
- **File:** `weslr/evidence_answer_builder.py` (242 lines)
- **Purpose:** Converts an evidence packet into a cautious user-facing answer draft. Three depth levels (brief, normal, deep). Labels all answers with "not stored WESLR truth". Read-only.
- **External calls:** No
- **Writes state:** No
- **State files:** None
- **Tested:** No dedicated test found
- **Safe for mission loop:** A — read-only answer formatter. Suitable for mission loop result presentation.

### 2.17 Evidence/Explore Commands
- **File:** `weslr/commands/evidence.py` (137 lines)
- **Purpose:** CLI handlers for evidence packet queries — `list_packets()`, `get_packet()`. Read-only.
- **External calls:** No
- **Writes state:** No
- **State files:** `.weslr/external_evidence_packets.jsonl` (read)
- **Tested:** No dedicated test found
- **Safe for mission loop:** A — read-only CLI. Appropriate for mission loop operator review interface.

- **File:** `weslr/commands/explore.py` (200 lines)
- **Purpose:** CLI handler for `/explore <goal> [--domain] [--top] [--dry-run]`. Wraps `explore_engine.explore()`. Dry-run uses built-in mock data without live search API calls.
- **External calls:** Via explore_engine (indirect)
- **Writes state:** Via explore_engine
- **State files:** Via explore_engine
- **Tested:** Partial — `--dry-run` path not independently tested
- **Safe for mission loop:** C — direct call to explore_engine without mission gate.

### 2.18 Relevant Tests
| Test File | Modules Covered | Mocked External | Scope |
|---|---|---|---|
| `tests/test_pubmed_adapter_v1.py` | pubmed_adapter, evidence_packet_store | Yes (XML mocks for efetch, mocked esearch) | Unit |
| `tests/test_fact_extractor_v1.py` | fact_extractor | No external calls | Unit |
| `tests/test_deterministic_handler_classification.py` | deterministic_handlers | Partial | Unit |
| `tests/test_explore.py` | explore_engine | No (relies on internal mocks) | Unit |
| *(no searxng test file found)* | searxng_search_adapter | — | Missing |
| *(no pubchem test file found)* | pubchem_adapter | — | Missing |
| *(no chemistry_reaction_predictor test file found)* | chemistry_reaction_predictor | — | Missing |
| *(no biology_discovery test file found)* | biology_discovery | — | Missing |

---

## 3. Capability Map

| Capability | File/Function | External | Writes | State File | Tested | Safe for Mission Loop |
|---|---|---|---|---|---|---|
| PubMed search | `search_adapters/pubmed_adapter.py::search_pubmed` | Yes | No | — | Partial (mocked HTTP) | **Needs wrapper** |
| arXiv search | `search_adapters/arxiv_adapter.py::search_arxiv` | Yes | **Yes** | `.weslr/external_evidence_packets.jsonl` | Partial (mocked) | **Needs wrapper** |
| PubChem compound lookup | `search_adapters/pubchem_adapter.py::fetch_compound_properties` | Yes | No | — | No | **B — small adapter** |
| SearXNG web search | `searxng_search_adapter.py::search_searxng` | Yes | No | — | No | **D — unsafe** |
| Evidence packet write | `search_adapters/evidence_packet_store.py::append_evidence_packet` | No | **Yes** | `.weslr/external_evidence_packets.jsonl` | Yes | **A — ready** |
| Evidence packet read | `search_adapters/evidence_packet_store.py::load_packets, get_packet` | No | No | `.weslr/external_evidence_packets.jsonl` | Yes | **A — ready** |
| Evidence packet build/normalize | `evidence_packet_builder.py::build_evidence_packet` | No | No | — | Partial | **A — ready** |
| Fact extraction | `fact_extractor.py::extract_facts_with_positions, append_enriched_fact` | No | **Yes** | `.weslr/fact_assertions.jsonl` | Yes | **C — needs wrapper** |
| Source trust ranking | `source_trust_ranking.py::classify_source, rank_search_results` | No | No | — | Partial | **A — ready** |
| Deterministic handler dispatch | `deterministic_handlers.py` (3425 lines) | Indirect | Via imports | Via imports | Partial | **C — needs wrapper** |
| Biology discovery | `biology_discovery.py::handle_propose_biology` | No | No | — | No | **C — sensitive domain** |
| Chemistry reaction prediction | `chemistry_reaction_predictor.py::predict_reaction` | No | No | `chemistry_rules.json` (read) | No | **B — small adapter** |
| Combinatorial materials | `combinatorial_materials.py::handle_propose_combination` | No | No | — | No | **B — read-only generation** |
| Combinatorial chemistry | `combinatorial_chemistry.py::handle_propose_chemistry` | No | No | — | No | **B — read-only generation** |
| Explore/hypothesis engine | `explore_engine.py::explore` | Yes (via adapters) | Via adapters | Via adapters | Yes | **C — needs wrapper** |
| Hypothesis scoring | `hypothesis_scorer.py::rank_hypotheses, format_hypothesis_list` | No | No | — | Partial | **A — ready** |
| Formula feasibility check | `hypothesis_scorer.py::check_charge_balance` | No | No | — | Partial | **A — ready** |
| Evidence answer builder | `evidence_answer_builder.py::build_answer` | No | No | — | No | **A — ready** |
| Evidence CLI | `commands/evidence.py::list_packets, get_packet` | No | No (read) | `.weslr/external_evidence_packets.jsonl` | No | **A — ready** |
| Explore CLI | `commands/explore.py::handle_explore` | Via explore_engine | Via explore_engine | Via explore_engine | Partial | **C — needs wrapper** |
| Mission store | `mission_store.py` | No | **Yes** | `.weslr/missions.jsonl` | Partial | **A — ready** |
| Mission CLI | `commands/mission_commands.py` | No | **Yes** | `.weslr/missions.jsonl` | Partial | **A — ready** |

**Legend:**
- **A** = ready now
- **B** = usable with small adapter
- **C** = needs governance/safety wrapper
- **D** = unsafe for automatic mission use
- **E** = duplicate/obsolete
- **F** = unclear

---

## 4. Connection to Research Work Loop

### 4.1 Module → Research Work Loop Integration Points

Each A/B/C module maps to specific Research Work Loop data structures:

#### Evidence Packet Store (A)
- **`mission.evidence_links`**: Store packet_id here after appending. Evidence link carries packet_id, source badge, trust score, retrieved_at.
- **`mission.current_questions`**: Query field in packet links evidence to originating question.
- **`run_once_mission_review()`**: Packet available for operator review before any fact promotion.
- **`.weslr/pending_messages.jsonl`**: Packet reference can be queued for follow-up messaging.

#### Source Trust Ranking (A)
- **`mission.evidence_links`**: Used to rank results by trust tier before display.
- **`run_once_mission_review()`**: Trust tier informs operator review priority.

#### Fact Extractor (C — needs wrapper)
- **Phase 7 hypothesis/evidence store**: Extracted facts must NOT be written directly to the Phase 7 store without review. Wrapper must route through `append_enriched_fact()` with `authority=extracted_from_timeline` and a gate that prevents automatic promotion.
- **`mission.allowed_sources`**: Must be checked before fact extraction is called.

#### PubMed Adapter (C — needs wrapper)
- **`mission.allowed_sources`**: Must include "pubmed" before search executes.
- **`mission.current_questions`**: Query generated from current question(s).
- **`mission.evidence_links`**: Results written as packet_id references.

#### arXiv Adapter (C — needs wrapper)
- Same as PubMed. **Already writes evidence packets** — the wrapper must intercept and apply mission gate before any write.

#### Explore Engine (C — needs wrapper)
- **`mission.allowed_sources`**: Controls which adapters are invoked.
- **`mission.current_questions`**: Goal → query decomposition.
- **`mission.evidence_links`**: Output hypothesis candidates linked to source evidence.
- **Phase 7 hypothesis/evidence store**: Hypothesis scorer output for operator review, not automatic storage.

#### Biology Discovery (C — sensitive domain)
- **`mission.allowed_sources`**: Must explicitly allow "biology" domain.
- **Safety filter required**: No pathogen, weaponization, or dual-use guidance.
- **Provenance required**: Source for any biology claim.

#### Chemistry Reaction Predictor (B)
- **`mission.evidence_links`**: Reaction predictions as evidence candidates.
- **Safety filter**: No synthesis routes for controlled substances.

#### Combinatorial Materials / Chemistry (B)
- **`mission.evidence_links`**: Generated candidates as evidence.
- Read-only; no external calls. Small adapter sufficient.

#### Hypothesis Scorer (A)
- **Phase 7 hypothesis/evidence store**: Ranks hypotheses before store.
- **`mission.evidence_links`**: Ranks evidence links by novelty and feasibility.

#### Evidence Answer Builder (A)
- **`mission.current_questions`**: Builds answer anchored to original query.
- Output goes to operator review surface, not to user directly.

#### Mission Store (A)
- **`mission.allowed_sources`**: Primary gate — must be checked by all external source adapters.
- **`mission.evidence_links`**: Populated after evidence is retrieved.
- **`mission.current_questions`**: Stored as mission question(s).

### 4.2 Connection Classification Summary

| Module | Mission Allowed Sources | Evidence Links | Current Questions | Phase 7 Store |
|---|---|---|---|---|
| pubmed_adapter | ✅ required | ✅ packet_id output | ✅ query input | Via wrapper only |
| arxiv_adapter | ✅ required | ✅ packet_id output | ✅ query input | Via wrapper only |
| pubchem_adapter | ✅ required | ✅ property output | Partial | Via wrapper only |
| searxng_search_adapter | ❌ D — excluded | ❌ | ❌ | ❌ |
| evidence_packet_store | Not applicable | ✅ packet_id output | ✅ query in packet | ✅ pending review |
| fact_extractor | ✅ required | N/A | Text input | **Gate required** |
| source_trust_ranking | Not applicable | ✅ ranks links | N/A | N/A |
| deterministic_handlers | ⚠️ mixed | ⚠️ mixed | ⚠️ mixed | ⚠️ mixed |
| biology_discovery | ✅ required + sensitive | Candidate output | Domain-scoped | Via wrapper |
| chemistry_reaction_predictor | ✅ via wrapper | Prediction output | Reactant input | Via wrapper |
| combinatorial_materials | ✅ via wrapper | Candidate output | Goal-scoped | Via wrapper |
| explore_engine | ✅ required | ✅ via adapters | ✅ goal→query | Via wrappers |
| hypothesis_scorer | Not applicable | ✅ ranks links | N/A | ✅ ranks hypotheses |
| evidence_answer_builder | Not applicable | ✅ formats link | ✅ formats query | N/A |
| mission_store | ✅ primary gate | ✅ populates links | ✅ stores questions | ✅ mission boundary |

---

## 5. Safety and Governance Gates

### 5.1 PubMed
- `mission` must explicitly include `"pubmed"` in `mission.allowed_sources`
- **Provenance required**: pmid, title, journal, year, authors, URL in every packet
- **Uncertainty label required**: Packet authority is `external_evidence_unverified` — never promote to `verified` without operator review
- **Safety filter required**: Results mentioning select agents, toxins, or weaponization agents → flagged, not suppressed silently
- **Source trust score**: Peer-reviewed journal tier from `source_trust_ranking`
- **No hazardous synthesis guidance**: PubMed abstracts may mention synthesis; safety filter must flag but not withhold
- **No automatic truth promotion**: Fact extraction from PubMed abstract → `authority=extracted_from_timeline`, not stored as WESLR fact until reviewed
- **Rate limit**: 3 req/s enforced in adapter (`time.sleep(0.34)`)

### 5.2 arXiv
- `mission` must explicitly include `"arxiv"` in `mission.allowed_sources`
- **Provenance required**: arxiv_id, title, authors, published, primary_category, pdf_url
- **Uncertainty label required**: arXiv preprints are **not peer-reviewed** — authority label must include `preprint_unverified`
- **Safety filter required**: Same as PubMed for hazardous content
- **Source trust score**: Category-based; preprint default lower than journal
- **No automatic crawling**: Only abstract fetched; no full-text PDF fetch without explicit mission opt-in
- **No automatic truth promotion**: Same as PubMed

### 5.3 PubChem
- `mission` must explicitly include `"pubchem"` in `mission.allowed_sources`
- **Provenance required**: CID, name, formula, molecular_weight, url
- **Uncertainty label required**: Compound data is curated but properties (XLogP, etc.) are predicted — label accordingly
- **Safety filter required**: No dual-use compound procurement guidance
- **Source trust score**: PubChem is authoritative government data (NCBI) — high trust tier
- **Read-only query**: No write state, no fact promotion
- **Rate limit**: 5 req/s enforced

### 5.4 SearXNG
- **D — excluded from Research Work Loop V2**
- `WESLR_SEARXNG_ENABLED` env var required **and** `mission.allowed_sources` must include `"searxng"`
- General web search is out of scope for scientific research loop
- Any connection must be V3+ with full governance review

### 5.5 Biology Discovery
- `mission.allowed_sources` must include `"biology"` — no implicit biology data pulls
- **Provenance required**: Domain source, candidate generation method
- **Uncertainty label required**: biology domain predictions are higher uncertainty
- **Safety filter required**: Hard block on: pathogen guidance, viral/bacterial weaponization, gain-of-function, dual-use research of concern (Durc)
- **No hazardous synthesis**: Biology candidates must not encode culturing instructions for select agents
- **Operator review before user exposure**: All biology suggestions go to review surface

### 5.6 Chemistry/Synthesis-Related Modules
- `chemistry_reaction_predictor`: Read-only rules. No synthesis execution. Safety filter for reaction rules involving controlled precursors.
- `combinatorial_chemistry`: Rule-based generation. No external calls. Small wrapper sufficient. Flag if rules include explosive/nerve agent precursors.
- **No automatic execution**: Chemical reaction prediction output is evidence, not protocol
- **Hazard flag list**: Reactions involving phosphorus, cyanides, nitriles, azides, perchlorates → safety filter flags

### 5.7 Experiment Templates
- `explore_engine._EXPERIMENT_TEMPLATES` provides protocol templates (in_vitro, DFT, synthesis, in_vivo)
- **Safety filter required**: in_vivo template requires IACUC statement — flag if absent
- **No automatic execution**: Templates are educational/protocol-style, not executable
- **No clinical/medical advice**: Templates must not be framed as medical recommendation

### 5.8 Material Generation
- `combinatorial_materials`: Generates candidate compositions; no external calls
- **Feasibility filter**: Charge balance check via `hypothesis_scorer.check_charge_balance()`
- **Hazard flag**: If composition includes beryllium, cadmium, lead, asbestos precursors → safety filter flags
- **No procurement guidance**: Don't generate sourcing instructions for toxic/rare materials

### 5.9 Hypothesis Generation
- `explore_engine::generate_hypotheses` produces ranked hypotheses from literature
- **No automatic truth promotion**: All hypotheses start as `candidate` status
- **Novelty scoring**: Via `hypothesis_scorer` — no cross-reference to existing facts without review
- **Operator review before exposure**: All hypotheses routed to review surface

---

## 6. Recommended First Integration

**Recommendation: B) MissionEvidenceAdapter wrapper**

Create `weslr/adapters/mission_evidence_adapter.py` that wraps:
- `search_adapters.pubmed_adapter` (search + fetch)
- `search_adapters.arxiv_adapter` (search + store + fact extract)
- `search_adapters.pubchem_adapter` (compound lookup)
- `evidence_packet_store.append_evidence_packet` (write)
- `fact_extractor.extract_facts_with_positions` (extract, gated)
- `source_trust_ranking.rank_search_results` (rank)
- `hypothesis_scorer.rank_hypotheses` (score)

The MissionEvidenceAdapter normalizes all results into mission evidence candidates with:
- `packet_id` — globally unique
- `source` — badge (pubmed/arxiv/pubchem)
- `query` — originating question
- `trust_score` — from source_trust_ranking
- `uncertainty` — authority label
- `provenance` — full citation info
- `created_at` — UTC timestamp
- `mission_id` — link to originating mission

**Why B over A:** Direct handler wiring (A) risks bypassing mission gates. A wrapper (B) provides a single enforcement point where `mission.allowed_sources` is checked once and all writes are normalized consistently. The existing adapters were designed to be wrapped — they don't already check mission context.

**Why B over C:** SourceCapabilityRegistry is useful for future extensibility but adds indirection. The priority is getting PubMed/arXiv+PubChem into the mission loop safely. MissionEvidenceAdapter is the narrowest viable path.

---

## 7. Proposed V2 Vertical Slice

### Scope
Single source: **PubMed** (arXiv as second).

### Flow
1. `mission.allowed_sources` must include `"pubmed"`. If not present → return empty, no external call.
2. Query generated from `mission.current_questions` (first question used, or explicit query field).
3. `search_pubmed(query)` → list of PMIDs → `efetch(pmids)` → list of article dicts.
4. Results passed through `source_trust_ranking.classify_source()` per result URL (or journal URL).
5. Evidence packet written via `append_evidence_packet()` with:
   - `record_type: "external_evidence_packet_v1"`
   - `packet_id: "pm_{timestamp}_{random}"`
   - `source: "pubmed"`
   - `query: <original query>`
   - `retrieved_at: <UTC ISO>`
   - `result_count: <N>`
   - `results: <article dicts>`
   - `authority: "external_evidence_unverified"`
   - `provenance: {pmid, title, journal, year, authors, url}`
6. Optional fact extraction (gated): `extract_facts_with_positions()` from abstracts → written with `authority=extracted_from_timeline` and `mission_id` tag. **Not promoted to fact store truth.**
7. Mission suggestion created with:
   - `source: "pubmed"`
   - `packet_id: <new packet_id>`
   - `trust_score: <from ranking>`
   - `uncertainty: "external_evidence_unverified"`
   - `suggestion_text: <brief summary from top result>
   - `automatic_execution: false`
8. Suggestion enqueued for `run_once_mission_review()` — operator reviews before any action.

### What is NOT included in V2
- No automatic fact promotion to WESLR memory
- No SearXNG
- No biology/chemistry external calls (PubChem compound lookup is B-tier, not V2)
- No user-facing answer delivery — operator review only
- No Phase 7 hypothesis store write

---

## 8. Tests Needed

### 8.1 Source Disabled by Default
```python
def test_pubmed_adapter_disabled_without_mission():
    # search_pubmed called without mission.allowed_sources containing "pubmed"
    # → returns empty list, raises nothing, makes no HTTP call
```

### 8.2 Mission Opt-In Required
```python
def test_arxiv_adapter_requires_mission_opt_in():
    # search_and_store without "arxiv" in mission.allowed_sources
    # → returns {"result_count": 0, "fact_count": 0}, no HTTP call
```

### 8.3 PubMed/arXiv Adapter Mocked
```python
def test_pubmed_adapter_mocked_search_returns_results():
    with patch("weslr.search_adapters.pubmed_adapter.requests.get") as mock_get:
        mock_get.return_value.json.return_value = {"esearchresult": {"idlist": ["12345"]}}
        mock_get.return_value.raise_for_status = MagicMock()
        pmids, articles = search_pubmed("BRCA1", max_results=5)
        assert pmids == ["12345"]
        assert mock_get.call_count >= 1  # esearch called
```

### 8.4 Evidence Packet Generated
```python
def test_mission_evidence_adapter_writes_packet():
    # With mission.allowed_sources=["pubmed"]
    # → after search, packet exists in .weslr/external_evidence_packets.jsonl
    # → packet has correct record_type, source, query, provenance
```

### 8.5 Fact Assertion Not Promoted to Truth
```python
def test_extracted_facts_not_promoted_to_trust():
    # Facts extracted from PubMed abstract via fact_extractor
    # → written with authority="extracted_from_timeline"
    # → NOT with authority="verified" or "stored_weslr_fact"
    # → fact store does NOT contain these facts as trusted assertions
```

### 8.6 Suggestion Includes Provenance
```python
def test_mission_suggestion_includes_provenance():
    # After PubMed search in mission context
    # → mission suggestion created with source badge, packet_id, trust_score, uncertainty label
    # → suggestion.automatic_execution == False
```

### 8.7 Safety Filter Blocks Sensitive/Hazardous Outputs
```python
def test_safety_filter_blocks_pathogen_guidance():
    # PubMed result containing "Gain-of-function H5N1" or select agent mentions
    # → result flagged in safety filter
    # → packet written with hazard flag, not silently dropped
    # → suggestion includes safety warning badge
```

### 8.8 SearXNG Disabled Unless Env + Mission Opt-In
```python
def test_searxng_requires_env_flag():
    # WESLR_SEARXNG_ENABLED not set
    # → is_searxng_enabled() returns False regardless of mission.allowed_sources
    # → no HTTP call made

def test_searxng_requires_mission_opt_in_when_enabled():
    # WESLR_SEARXNG_ENABLED=true
    # but "searxng" not in mission.allowed_sources
    # → is_searxng_enabled() returns True but adapter still returns empty
```

### 8.9 No External Calls in Unit Tests
```python
def test_no_external_calls_in_unit_tests():
    # All test files for search adapters mock HTTP at patch level
    # No test makes a real HTTP call to NCBI, arXiv, or PubChem
    # Verified by network-tight subprocess check or test tag marker
```

### 8.10 Evidence Packet Authority Labeling
```python
def test_evidence_packet_authority_label():
    # Packet built from PubMed results
    # → authority == "external_evidence_unverified"
    # → never "verified" or "weslr_stored"
    # Packet built from arXiv results
    # → authority == "external_evidence_unverified" + "preprint_unverified"
```

---

## 9. Open Questions

### 9.1 PubMed/arXiv/PubChem — which first?
PubMed is lower-risk: structured abstracts, authoritative (NCBI), no PDF crawl. arXiv adds preprint uncertainty. PubChem is read-only compound lookup — simpler but less central to research loop. **Recommendation: PubMed first, arXiv second, PubChem as B-tier follow-up.**

### 9.2 Should PubChem write facts during mission review or only evidence candidates?
Currently PubChem is read-only (no fact writes). The question is whether molecular properties (MW, formula, logP) should be extracted as facts. **Recommendation: Evidence candidates only in V2. Facts from PubChem properties can be V3 — operator review before any property is stored as a WESLR fact.**

### 9.3 How to connect extracted facts to Phase 7 hypotheses?
Facts extracted from PubMed/arXiv abstracts should be tagged with `mission_id` and stored in the fact store with `authority=extracted_from_timeline`. Phase 7 hypothesis scorer can then reference them. Key gap: Phase 7 store schema not yet mapped. **Recommendation: Document Phase 7 schema first, then implement fact→hypothesis link as a separate adapter.**

### 9.4 How to score novelty?
Hypothesis scorer already has `novelty_score`. Current implementation not documented. Need to define: novelty against existing fact store vs. novelty against mission-generated candidates only. **Recommendation: Novelty is relative to existing WESLR facts — requires fact store query integration before scoring.**

### 9.5 How to avoid low-quality search spam?
arXiv API can return low-signal results for generic queries. PubMed's relevance sort helps but is not perfect. **Recommendation: Minimum result threshold (≥3 results) before writing a packet. Below threshold → return empty with reason. Also: query expansion via `mission.current_questions` context helps.**

### 9.6 How to rate source trust for preprints vs peer-reviewed papers?
`source_trust_ranking` has no preprint-specific tier. arXiv results default to `unknown` trust tier currently. **Recommendation: Add arXiv-specific trust tier: arXivv1 (submitted, no peer review) = 0.5 base; arXivv2 (cross-posted to journal) = journal tier. Update trust ranking accordingly.**

### 9.7 How to handle sensitive domains like nanotech/biology/chemistry?
No content filter exists in current adapters. Safety filter is a gap. **Recommendation: Keyword-based hazard flag list (see §5) added to MissionEvidenceAdapter. Flagged results get hazard badge — not dropped, operator review only. Biology domain gets extra governance layer.**

### 9.8 Should SearXNG be V3 only?
Yes. SearXNG is general web search with no scientific structure. It risks returning low-quality, non-peer-reviewed, or misleading content. The governance surface for web search is significantly heavier than for structured scientific APIs. **Recommendation: V3 only. Requires full governance review, safety filter audit, and operator training before connection.**

### 9.9 How to separate user-visible vs operator-visible science suggestions?
Current architecture: all suggestions go to operator review surface. No user-facing science suggestion layer exists yet. **Recommendation: V2 suggestions are operator-only (review surface). User-visible suggestions are V3+ — require separate UI surface and user-facing uncertainty labeling.**

---

## 10. Final Recommendation

**Commit current Mission CLI V1.1 first.** The staged changes to mission commands represent foundational infrastructure. Do not layer new adapter work on top of an uncommitted Mission CLI.

**Then implement MissionEvidenceAdapter V2** behind explicit `mission.allowed_sources` gate:

1. Create `weslr/adapters/mission_evidence_adapter.py`
2. Wrap PubMed adapter first (search + fetch + packet write + mission gate)
3. Add source trust ranking integration
4. Add evidence packet → mission suggestion pipeline
5. Add fact extraction gate (authority = extracted_from_timeline, not promoted)
6. Write tests from §8
7. arXiv V2 follow-up as second adapter (same wrapper pattern)
8. PubChem as B-tier (read-only lookup, simpler)

**What not to do in V2:**
- No automatic truth promotion
- No SearXNG
- No biology/chemistry external calls
- No user-facing delivery
- No Phase 7 hypothesis store write

---

*Audit completed 2026-05-04. No code written or refactored. No external searches run.*
