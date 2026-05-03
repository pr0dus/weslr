# Weslr Phase 4 — Research Intelligence Design Document

**Version:** 1.0  
**Date:** 2026-05-03  
**Author:** OCC (Weslr Architect)  
**Status:** Design only — no implementation  
**Domain template:** Cancer research (clinical trial reports, research papers, lab notes)  
**Reusable for:** Oncology wards, materials labs, astronomy teams, universities

---

## 1. Overview and Motivation

Weslr Phases 1–3 delivered entity timeline memory, structured fact extraction, project registry, reminder orchestration, and a proactive daemon. The system now maintains persistent memory, can act proactively, and routes voice cleanly.

Phase 4 adds **research-grade document intelligence**. The goal is to evolve Weslr into a general institutional research assistant: one that can ingest documents, extract provenance-tracked facts, search external literature, and support domain-specific entity schemas — all with multi-tenant isolation.

**Why this matters:** Current Weslr knows what it has processed in conversation. Phase 4 makes it know what the world has published.

### Target Deployments

| Deployment | Domain | Example Entity Types |
|---|---|---|
| Hospital oncology ward | Cancer research | ClinicalTrial, DrugCompound, Protein, Biomarker |
| University lab | Materials science | Material, CrystalStructure, SynthesisProtocol |
| Astronomy team | Exoplanet research | Exoplanet, Star, OrbitalParameter, Observatory |
| Private research group | General | Project, Dataset, Experiment, Hypothesis |

Each deployment is a **tenant** with its own isolated data directory.

---

## 2. Document Ingestion Layer

### 2.1 Supported Input Formats

| Format | Library | Notes |
|---|---|---|
| PDF | `pypdf` | Text extraction, page/line tracking |
| Plain text | built-in | UTF-8, line numbering |
| Markdown | built-in | Frontmatter parsed as metadata |
| CSV / Excel | `openpyxl` | Tabular fact candidates |
| PPT | `python-pptx` | Slide text extraction |

All libraries are pure Python, open-source, no external API calls.

### 2.2 Process Flow

```
Upload → Convert → Segment → Extract Facts → Store
```

**Step 1 — Upload**
- Operator-only endpoint `POST /ingest` accepts a file upload
- Alternative: watched folder (`WESLR_WATCH_DIR`) processed by proactive daemon
- Computes SHA-256 hash of file to detect duplicates
- Rejects if hash already exists (idempotent)

**Step 2 — Convert to plain text**
- Each format yields: raw text + positional metadata (page, line, char offset)
- Stored in `weslr/documents.jsonl` as metadata record (see §3 for schema)

**Step 3 — Segment into sections**
- PDF/PPT: headings detected via font size heuristics or slide titles
- Plain text/Markdown: section headers detected via regex (`^#{1,3}\s`, all-caps lines)
- Segments tagged: `abstract`, `methods`, `results`, `conclusion`, `discussion`, `unknown`

**Step 4 — Fact extraction**
- Existing `fact_extractor.py` provides 10 base patterns
- Add 10–15 clinical-trial-specific patterns (see §2.5)
- Each fact stores: raw text, page, line range, extraction pattern ID, confidence

**Step 5 — Storage**
- `weslr/documents.jsonl` — one record per ingested document
- `weslr/fact_assertions.jsonl` — extended schema with provenance fields (see §3)

### 2.3 Duplication Handling

- Hash-based deduplication: same file hash = same document, skip re-ingest
- Operator notified via queue message: "Document already ingested as {doc_id}"

### 2.4 Full Document Text Storage — Decision

**Config flag:** `WESLR_STORE_DOCUMENT_TEXT` (default: `false`)

| Setting | Behavior | Use case |
|---|---|---|
| `false` (default) | Only metadata + extracted facts stored | Privacy-sensitive environments, storage savings |
| `true` | Full plain-text content stored alongside metadata | Legal discovery, full-text search later |

The flag is per-tenant. Even when `true`, the raw text is stored in the tenant directory only — never leaves the tenant.

### 2.5 Clinical Trial Fact Patterns (Domain Extension)

These extend `fact_extractor.py` with domain-specific regex + heuristics:

| Pattern ID | Example raw text | Extracted fact |
|---|---|---|
| `ct.patients_assigned` | "42 patients were assigned to the treatment arm" | ` arm = treatment; n = 42 ` |
| `ct.survival_rate` | "overall survival was 68% at 24 months" | `survival_rate = 0.68; timeframe = 24 months` |
| `ct.p_value` | "p-value = 0.003" | `p_value = 0.003; significant = true` |
| `ct.hazard_ratio` | "hazard ratio 0.71 (95% CI 0.54–0.93)" | `hazard_ratio = 0.71; ci_low = 0.54; ci_high = 0.93` |
| `ct.response_rate` | "objective response rate was 34%" | `response_rate = 0.34` |
| `ct.drug_dose` | "Nivolumab 3 mg/kg IV every 2 weeks" | `drug = nivolumab; dose = 3 mg/kg; freq = q2w` |
| `ct.adverse_event` | "grade 3 pneumonitis occurred in 5 patients" | `event = pneumonitis; grade = 3; n = 5` |
| `ct.biomarker` | "PD-L1 TPS ≥ 50% required for enrollment" | `biomarker = PD-L1; threshold = 0.50` |
| `ct.phase` | "phase II trial" | `phase = 2` |
| `ct.enrollment` | "90 patients enrolled across 12 sites" | `enrollment = 90; sites = 12` |
| `ct.followup` | "median follow-up 18.5 months" | `followup_median = 18.5 months` |
| `ct.control_arm` | "control arm received placebo" | `control_arm = placebo` |
| `ct.primary_endpoint` | "primary endpoint was progression-free survival" | `endpoint = progression_free_survival` |
| `ct.manufacturer` | "study drug provided by Pfizer" | `manufacturer = Pfizer` |
| `ct.trial_id` | "ClinicalTrials.gov NCT04551452" | `trial_id = NCT04551452` |

Patterns are defined in `weslr/schemas/fact_patterns/<domain>.json`. Adding a new domain = adding a new pattern file.

**Implementation status:** Phase 4.2 refinement (2026-05-03) wired these patterns into the extraction pipeline. `fact_extractor.py` now loads patterns dynamically from `fact_patterns/<domain>.json`. The `extract_facts_with_positions()` function accepts a `domain` parameter (default: `cancer_research`) and iterates over loaded patterns.

---

## 3. Data Schema Changes

### 3.1 New File: `weslr/documents.jsonl`

One JSON record per ingested document:

```jsonl
{"doc_id":"doc_abc123","filename":"zhang_et_al_2023_brca1.pdf","hash":"sha256:...","upload_date":"2026-05-03T10:00:00Z","source_type":"paper","domain":"cancer_research","trust_baseline":0.9,"page_count":14,"abstract":"..."," INGEST_method":"pypdf","store_text":false}
```

**Fields:**

| Field | Type | Description |
|---|---|---|
| `doc_id` | string | Auto-generated UUID, prefixed `doc_` |
| `filename` | string | Original filename |
| `hash` | string | `sha256:<hex>` of file content |
| `upload_date` | ISO-8601 | When document was ingested |
| `source_type` | enum | `paper`, `clinical_trial`, `internal_note`, `external_database`, `conference_abstract`, `preprint`, `lab_note` |
| `domain` | string | Deployment domain, e.g. `cancer_research` |
| `trust_baseline` | float | From source-type heuristic (§4) |
| `page_count` | int | Number of pages/slides |
| `abstract` | string | Extracted abstract (if available) |
| `ingest_method` | string | Library used: `pypdf`, `pdfplumber`, `python-pptx`, `openpyxl` |
| `store_text` | bool | Whether full plain-text content is stored |

### 3.2 Modified File: `weslr/fact_assertions.jsonl`

Add provenance fields to existing schema:

```jsonl
{"fact_id":"f_001"," assertion ":"survival rate improved by 15%","subject":"BRCA1 mutation cohort","predicate":"survival_rate_delta","value":0.15,"unit":"percent","extracted_at":"2026-05-03T10:05:00Z","source_doc_id":"doc_abc123","source_reference":{"type":"paper","citation":"Zhang et al. (2023) Nature Medicine","page":5,"line_range":[12,18]},"source_type":"paper","trust_score":0.92,"domains":["cancer_research"],"extraction_pattern":"ct.survival_rate","project_id":"proj_oncology"}
```

**New/extended fields:**

| Field | Type | Description |
|---|---|---|
| `source_doc_id` | string | Reference to `documents.jsonl` entry |
| `source_reference.type` | enum | `paper`, `clinical_trial`, `internal_note`, `external_database` |
| `source_reference.citation` | string | Human-readable citation |
| `source_reference.page` | int | Page number |
| `source_reference.line_range` | array | `[start, end]` line numbers |
| `source_type` | enum | Duplicated for filtering convenience |
| `trust_score` | float | Computed: `trust_baseline * pattern_confidence` |
| `domains` | array | Applicable domains |
| `project_id` | string | Optional: associate fact with a project |

### 3.3 New File: `weslr/trust_tiers.json` (operator-maintained)

```json
{"tier1":["NEJM","Lancet","Nature Medicine","JAMA","BMJ"],"tier2":["JCO","Cancer Research","Blood","Gastroenterology"],"tier3":[]}
```

Tier bonuses applied on top of `trust_baseline` when citation matches a journal in the list.

### 3.4 New File: `weslr/external_evidence_packets.jsonl`

Written by search adapters (PubMed, arXiv, etc.):

```jsonl
{"packet_id":"ev_001","source":"pubmed","source_url":"https://pubmed.ncbi.nlm.nih.gov/123456/","query":"BRCA1 mutation breast cancer survival","retrieved_at":"2026-05-03T10:10:00Z","result_count":5,"results":[{"pmid":"123456","title":"...","authors":"...","journal":"Nature Medicine","year":2023,"abstract":"..."}]}
```

These packets are **raw evidence**, not facts. They feed the evidence pipeline for later fact extraction.

---

## 4. Trust Scoring & Provenance

### 4.1 Deterministic Trust Heuristics

Base trust score from source type:

| Source Type | Base Trust |
|---|---|
| Clinical trial registry (ClinicalTrials.gov) | 0.95 |
| Peer-reviewed journal article | 0.90 |
| Preprint (arXiv, bioRxiv, medRxiv) | 0.50 |
| Conference abstract | 0.40 |
| Internal lab note | 0.30 |
| User-entered note | 0.20 |

### 4.2 Journal Reputation Tiers

From `trust_tiers.json`:

| Tier | Bonus | Example Journals |
|---|---|---|
| Tier 1 | +0.05 | NEJM, Lancet, Nature Medicine, JAMA |
| Tier 2 | +0.03 | JCO, Cancer Research, Blood |
| Tier 3 | +0.00 | All others |

Final trust score: `min(1.0, base_trust + tier_bonus)`

### 4.3 Pattern Confidence

Each extraction pattern has an internal confidence weight (0.5–1.0). Final fact trust:

```
trust_score = trust_baseline * pattern_confidence
```

Examples:
- Zhang et al. (Nature Medicine, peer-reviewed, Tier 1): `0.90 * 1.0 + 0.05 = 0.95`
- Internal lab note, pattern with 0.7 confidence: `0.30 * 0.7 = 0.21`

### 4.4 Aggregate Trust (Multiple Sources)

When multiple facts support the same claim (matched by subject + predicate), aggregate:

```
aggregated_trust = sum(trust_i * confidence_i) / sum(confidence_i)
```

Weighted average. Display shows "Based on 3 sources, estimated confidence 87%."

### 4.5 Provenance Display

When Weslr answers a query requiring a source:

> "According to **Zhang et al. (2023)**, *Nature Medicine*, survival rate improved by 15% in the BRCA1 mutation cohort (trust: 92%). Source: doc_abc123, p.5 ll.12–18."

Format: `[citation], [assertion] (trust: X%). Source: [doc_id], p.[page] ll.[range]`

---

## 5. Domain-Specific Entity Schemas

### 5.1 Registry Architecture

```
weslr/
  entity_schema_registry.py   # Loader + validator
  schemas/
    base.json                # Minimal fallback schema
    cancer_research.json     # Clinical trials, drugs, biomarkers
    materials_science.json   # Materials, crystal structures
    astronomy.json           # Exoplanets, stars, orbital parameters
```

### 5.2 Schema Format

`weslr/schemas/cancer_research.json`:

```json
{
  "domain": "cancer_research",
  "version": "1.0",
  "entity_types": {
    "ClinicalTrial": {
      "extends": "event",
      "required": ["trial_id", "phase", "status"],
      "attributes": ["trial_id", "phase", "enrollment", "primary_endpoint", "status", "sponsor"],
      "relationships": ["has_drug", "has_biomarker", "has_site"]
    },
    "DrugCompound": {
      "extends": "concept",
      "required": ["name", "mechanism"],
      "attributes": ["name", "generic_name", "manufacturer", "mechanism", "route"],
      "relationships": ["treats", "has_adverse_event", "used_in"]
    },
    "Protein": {
      "extends": "concept",
      "required": ["name", "gene_symbol"],
      "attributes": ["name", "gene_symbol", "function", "mutation"]
    },
    "Biomarker": {
      "extends": "concept",
      "required": ["name", "detection_method"],
      "attributes": ["name", "type", "threshold", "detection_method"],
      "relationships": ["associated_with", "predicts"]
    },
    "Mutation": {
      "extends": "concept",
      "required": ["gene", "type"],
      "attributes": ["gene", "type", "functional_impact"]
    }
  },
  "relationship_types": [
    "treats", "associated_with", "predicts", "used_in", "has_adverse_event"
  ]
}
```

### 5.3 Schema Loading

- Tenant config specifies `entity_schema` field, e.g. `"cancer_research"`
- `entity_schema_registry.py` loads `schemas/<domain>.json` at startup
- Falls back to `schemas/base.json` if domain not found
- Entity graph validator checks new entities against active schema
- Invalid entities flagged for human review via queue

### 5.4 Base Schema (Minimal Fallback)

`weslr/schemas/base.json`:

```json
{
  "domain": "base",
  "version": "1.0",
  "entity_types": {
    "person": {"required": ["name"], "attributes": ["name"]},
    "organization": {"required": ["name"], "attributes": ["name"]},
    "concept": {"required": ["name"], "attributes": ["name"]},
    "event": {"required": ["name"], "attributes": ["name"]},
    "object": {"required": ["name"], "attributes": ["name"]},
    "location": {"required": ["name"], "attributes": ["name"]}
  }
}
```

---

## 6. Literature Search Integration

### 6.1 Supported External Sources

| Source | API | Access | Rate Limit |
|---|---|---|---|
| PubMed | NCBI E-utilities | Free, no API key | 3 req/s, 10k/day |
| arXiv | arXiv API | Free | 1 req/s |
| ClinicalTrials.gov | CT API v2 | Free | No strict limit stated |
| NASA Exoplanet Archive | TAP/HTTP | Free | Polite pool |
| Materials Project | REST API | Free key required | 1000 req/month |

### 6.2 Adapter Pattern

All adapters follow the same interface as `evidence_pipeline.py`:

```
weslr/
  search_adapters/
    pubmed_adapter.py      # NCBI E-utilities
    arxiv_adapter.py       # arXiv API
    clinicaltrials_adapter.py  # ClinicalTrials.gov v2
    astronomy_adapter.py   # NASA Exoplanet Archive
    materials_adapter.py   # Materials Project
```

Each adapter:
- Takes a query string + optional filters
- Returns `external_evidence_packet_v1` written to `weslr/external_evidence_packets.jsonl`
- Includes: source name, query, timestamp, result count, raw results
- All are **read-only** — no writes to external systems

### 6.3 PubMed Adapter Details

Using NCBI E-utilities (free, no API key):

```
Endpoint: https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi
Parameters: db=pubmed&term=<query>&retmax=20&sort=relevance

Fetch abstracts:
Endpoint: https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi
Parameters: db=pubmed&id=<pmid>&rettype=abstract&retmode=xml
```

**Search flow:**
1. `esearch.fcgi` returns list of PMIDs
2. `efetch.fcgi` retrieves abstracts in batch (up to 200 IDs per request)
3. Results written to `external_evidence_packets.jsonl`
4. Facts extracted from abstracts via `fact_extractor.py`
5. Operator notified: "PubMed search returned 20 papers. 12 new facts extracted."

### 6.4 Command Handler: `/search`

```
/search pubmed "BRCA1 mutation and breast cancer survival"
/search arxiv "metal-organic framework battery"
/search trials "CAR-T cell lymphoma"
```

Response format:
```
PubMed search: "BRCA1 mutation and breast cancer survival"
Returned: 20 papers (top 5 shown)
  1. Zhang et al. (2023) Nature Medicine — "BRCA1 mutation carriers showed..." [trust: 95%]
  2. ...
  → 12 facts extracted and stored. Ask me about specific findings.
```

### 6.5 Proactive Daemon Background Search

For a given project, daemon can periodically query PubMed:

- Trigger: Project has `"monitor_literature": true` in registry
- Interval: configurable per project (default: daily)
- Query: derived from project topic keywords
- Action: write results to `external_evidence_packets.jsonl`, notify operator via queue

---

## 7. Multi-Tenant Isolation

### 7.1 Directory Structure

```
/data/weslr/
  tenants/
    hospital_a/           # Tenant: hospital_a
      documents.jsonl
      fact_assertions.jsonl
      external_evidence_packets.jsonl
      entity_graph.json
      projects.jsonl
      tenant_config.json
    university_b/          # Tenant: university_b
      documents.jsonl
      fact_assertions.jsonl
      ...
  global/
    trust_tiers.json      # Shared: operator-maintained tier list
    schemas/               # Shared: domain schemas
    search_adapters/      # Shared: adapter code (read-only per tenant)
```

### 7.2 Tenant Configuration

`weslr/tenants/<tenant_id>/tenant_config.json`:

```json
{
  "tenant_id": "hospital_a",
  "domain": "cancer_research",
  "entity_schema": "cancer_research",
  "monitor_literature": true,
  "monitor_interval_hours": 24,
  "store_document_text": false,
  "created_at": "2026-05-03T00:00:00Z"
}
```

### 7.3 Startup Isolation

- Environment variable `WESLR_TENANT_ID` at process start
- All file paths rooted in `/data/weslr/tenants/<tenant_id>/`
- If `WESLR_TENANT_ID` is empty or unset: fall back to legacy `.weslr/` path (single-tenant mode for existing deployments)
- Separate process per tenant for complete isolation (future; not in Phase 4 scope)

### 7.4 Phase 4 Scope Note

Phase 4.1–4.3 implement single-tenant (your own lab/project). Multi-tenant isolation is designed here but deferred to Phase 4.4.

---

## 8. API Endpoints and Command Handlers

### 8.1 New Endpoints (Operator-Only)

| Endpoint | Method | Description |
|---|---|---|
| `/ingest` | `POST` | Upload document, returns `doc_id` |
| `/search` | `GET` | `?source=pubmed&query=<q>` — trigger literature search |
| `/documents` | `GET` | List ingested documents |
| `/documents/<doc_id>` | `GET` | Get document metadata |
| `/facts` | `GET` | Query facts with filters (domain, doc_id, trust_min) |
| `/trust-breakdown/<fact_id>` | `GET` | Show trust computation for a fact |

### 8.2 New Deterministic Handlers

| Handler | Description |
|---|---|
| `/search pubmed <query>` | Search PubMed, return top results + fact count |
| `/search arxiv <query>` | Search arXiv |
| `/search trials <query>` | Search ClinicalTrials.gov |
| `/ingest <file_path>` | Ingest document from local path |
| `/documents` | List all ingested documents |
| `/documents <doc_id>` | Show document metadata + abstract |
| `/facts about <entity>` | Show all facts about an entity with trust scores |
| `/trust <fact_id>` | Show provenance and trust breakdown |
| `/schema` | Show active entity schema types |
| `/schema <domain>` | Show schema for a specific domain |

### 8.3 State-Grounded Dialogue Integration

Update `state_grounded_dialogue` to handle:

| User Question | Weslr Answer |
|---|---|
| "What papers have you ingested?" | List from `documents.jsonl` with citations and trust scores |
| "What facts do you know about BRCA1?" | Facts from `fact_assertions.jsonl` filtered by subject, with provenance |
| "How confident are you about X?" | Trust score breakdown: sources, tiers, aggregation |
| "Show me the evidence for Y" | Full provenance: doc_id, page, line range, citation |
| "Search PubMed for Z" | Trigger `/search pubmed Z`, report results |

---

## 9. Implementation Roadmap

### Phase 4.1 — Single-Domain Document Ingestion + Provenance
**Estimated effort:** 3–5 days

- [ ] `weslr/document_ingestor.py` — pure Python, supports PDF/plain text
- [ ] `weslr/schemas/fact_patterns/cancer_research.json` — 15 clinical trial patterns
- [ ] Extend `fact_extractor.py` to load domain pattern files
- [ ] Update `weslr/fact_assertions.jsonl` schema with provenance fields
- [ ] Update `weslr/documents.jsonl` schema
- [ ] `POST /ingest` endpoint (operator-only)
- [ ] Update `state_grounded_dialogue` for document/fact queries
- [ ] Tests: ingestion idempotency, fact extraction accuracy, trust score computation

### Phase 4.2 — External Literature Search (PubMed)
**Estimated effort:** 2–3 days

- [x] `weslr/search_adapters/pubmed_adapter.py`
- [ ] `GET /search` endpoint
- [ ] `/search pubmed <query>` deterministic handler
- [ ] Write results to `external_evidence_packets.jsonl`
- [ ] Fact extraction from retrieved abstracts
- [ ] Operator notification with result summary
- [ ] Tests: API response parsing, packet schema validation

> **Note:** Phase 4.2 partial — cancer research patterns wired (15 clinical trial patterns active)

### Phase 4.3 — Entity Schema Registry + Custom Types
**Estimated effort:** 2 days

- [ ] `weslr/entity_schema_registry.py`
- [ ] `weslr/schemas/base.json`
- [ ] `weslr/schemas/cancer_research.json`
- [ ] Entity graph validation against active schema
- [ ] Schema loading at tenant startup
- [ ] `/schema` and `/schema <domain>` handlers
- [ ] Tests: valid/invalid entity enforcement

### Phase 4.4 — Multi-Tenant Isolation
**Estimated effort:** 3–4 days (deferred)

- [ ] `WESLR_TENANT_ID` environment variable handling
- [ ] Tenant directory creation and path rooting
- [ ] Tenant config file schema
- [ ] Fallback to legacy path for existing single-tenant deployments
- [ ] `/tenants` management commands (list, create, switch)
- [ ] Tests: isolation verification (no cross-tenant file access)

---

## 10. Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Large PDFs exceed memory | Medium | Medium | Stream processing, page-by-page extraction, config max file size |
| PubMed rate limiting | Medium | Low | 3 req/s cap, queue-based retry, polite pool usage |
| Fact extraction false positives | Medium | Medium | Trust score propagates uncertainty; operator review for low-trust facts |
| Storing full document text balloons storage | Medium | Low | `WESLR_STORE_DOCUMENT_TEXT=false` default; operator opts in |
| Schema validation too strict for early-stage research | Low | Low | Fallback to base schema; custom schemas operator-maintained |
| Duplicate document re-ingestion | Low | Low | SHA-256 hash deduplication |
| External search returns irrelevant results | Medium | Low | Fact extraction post-filter; operator can dismiss packets |

---

## 11. Governance & Safety Compliance

### Existing rules preserved:

- **No raw prompt storage** — document text stored only in tenant directory; never sent to external APIs except search queries (query text only)
- **No hidden learning** — all facts are explicitly extracted via pattern matching or search, not inferred by LLM
- **No automatic action without operator approval** — search is read-only; ingestion requires operator-only endpoint
- **Trust scoring is heuristic** — always displayed as "estimated confidence"; no claim of absolute truth

### Phase 4 additions:

- **`WESLR_STORE_DOCUMENT_TEXT`** — off by default; operator explicitly opts in per tenant
- **External search queries** — only query text sent to external APIs; no document content sent
- **Provenance is always visible** — every sourced answer shows document ID, page, line range
- **Trust score is per-fact** — operator can filter facts by minimum trust threshold
- **Multi-tenant isolation** — no read access across tenants; enforcement at path resolution

---

## 12. Open Questions

| # | Question | Options | Recommendation |
|---|---|---|---|
| 1 | **Store full document text?** | Yes (necessary for full-text search) / No (privacy + storage) | Default `false`; operator opts in. Full-text index as separate Phase 5 item |
| 2 | **Handling very large PDFs (>50MB)?** | Streaming extraction / page limit / reject | Stream with page limit (200 pages default); warn operator |
| 3 | **Async ingestion for large batches?** | Sync now / async queue | Sync for < 10 files; batch > 10 via background job in Phase 5 |
| 4 | **Fact deduplication across documents?** | Treat as separate facts / merge by subject+predicate | Separate facts with separate source_doc_id; trust aggregation handles weight |
| 5 | **Operator review workflow for low-trust facts?** | Silent / queue notification / pending queue | Queue notification; operator can dismiss or promote facts |
| 6 | **Schema evolution — how to update a domain schema without breaking existing entities?** | Version field / migration script / additive only | Additive only in same version; major changes bump version |
| 7 | **arXiv full-text fetching?** | Direct PDF download / abstract only | Abstract only for Phase 4; full PDF as Phase 5 (PDF parsing is heavy) |
| 8 | **Search adapter auth (NASA, Materials Project)?** | Per-tenant API keys / shared global keys | Global shared keys in `search_adapters/`; tenant config holds per-tenant override |
