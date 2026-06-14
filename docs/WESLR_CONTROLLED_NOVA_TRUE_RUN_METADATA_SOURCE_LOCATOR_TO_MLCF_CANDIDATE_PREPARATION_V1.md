# WESLR Controlled Nova True Run — Metadata Source Locator to MLCF Candidate Preparation V1

Run timestamp (UTC): 2026-06-14T12:05:38.604153+00:00
Run by: operator (manual hand-issued)
Run cwd: /home/pr0/projects/weslr-run-first-live-searxng-sample-20260613
Run HEAD: 4b714df190a76f3d012b2ebdcc334931457a7963
Boundary version: weslr_controlled_live_searxng_metadata_only_boundary_v1

## 1. Purpose

Run the first controlled Nova/Ubuntu true run from the reconciled canonical WESLR state.
Test whether WESLR can use live/local metadata-only source-location results from SearXNG and route them through:

live/local metadata source locator
-> MLCF routing from live SearXNG metadata result
-> cross-domain scout / integration path if needed
-> candidate-preparation packet
-> operator-review-ready metadata packet

True-run topic: *Sparse RF spatial change map constrained by floor-plan topology and calibrated against material/surface scattering assumptions.*

## 2. Repo / branch / HEAD / dirty status

- Repo root: `/home/pr0/projects/weslr-run-first-live-searxng-sample-20260613`
- Branch: `run-first-live-searxng-sample-20260613`
- HEAD: `4b714df1`
- Working tree dirty: 2 entries (the runner script `.run_controlled_nova_true_run_v1.py` + the result artifact `docs/WESLR_CONTROLLED_NOVA_TRUE_RUN_METADATA_SOURCE_LOCATOR_TO_MLCF_CANDIDATE_PREPARATION_V1.md`, both untracked, both operator-side scratch, neither committed)
- Merge / rebase / cherry-pick in progress: none

## 3. Nova/Ubuntu environment note

- Ubuntu Noble, Python 3.12, bash
- `python3` on PATH; no venv
- No service start/stop during this run
- Loopback-only outbound (SearXNG on `127.0.0.1:8888`)
- The dirty `/home/pr0/projects/weslr` superproject with paused answer-engine work, `.weslr/.env.local`, `.weslr/credentials.json`, `data/`, `logs/`, etc. was **not** used for this true run, per the owner's directive.

## 4. Local SearXNG availability

- `ss -ltn | grep :8888` -> `LISTEN 0 4096 0.0.0.0:8888` and `[::]:8888` (loopback only)
- `docker ps --filter ancestor=searxng/searxng` -> container `0bff25879718`, `searxng/searxng:latest`, `Up 2 months`
- `~/.local/bin/searxng-search` present (not used — boundary uses its own `urllib.request` HTTP getter)

## 5. Exact queries used (3 of 3 maximum)

1. `WiFi sensing indoor multipath material scattering floor plan localization`
2. `RF indoor propagation material surface scattering floor plan dataset`
3. `WiFi CSI device free sensing floor plan multipath benchmark`

Each query was issued as a single bounded GET: `http://127.0.0.1:8888/search?q=<urlencoded>&format=json&language=en` with `User-Agent: weslr-controlled-live-searxng-boundary-v1`, 5-second timeout, 5-result cap, snippets disabled, family `general`, role `owner`.

## 6. Number of metadata results inspected

- HTTP calls issued: **3** (one per query; no retries; no second calls; no `searxng-search` helper invoked)
- Total latency: **2773 ms** across the 3 calls
  - Query 1: `ok=True`, `reason=ok`, HTTP `200` in `1697 ms`, kept `5`, blocked `15`
  - Query 2: `ok=True`, `reason=ok`, HTTP `200` in `427 ms`, kept `5`, blocked `5`
  - Query 3: `ok=True`, `reason=ok`, HTTP `200` in `649 ms`, kept `5`, blocked `5`

- Aggregated kept rows: **10** (capped at 10 per the owner's directive; per-query cap was 5, so the cap was *not* hit)

## 7. Allowed metadata fields captured (per row)

`query`, `title`, `url`, `domain`, `source_engine`, `engines`, `rank`, `score`, `published_date`, `snippet` (always `None` — snippets disabled), `source_class_hint`, `authority_guess`, `evidence_role_guess` (always `candidate_signal`), `relevance_reason`, `freshness_status_guess`, `access_license_status_guess`, `privacy_status_guess`, `blocked_status` (always `allowed` in `results[]`), `locator_id` (SHA-256 of `query|url|rank`).

## 8. Blocked fields avoided

- Raw response body (any portion of the SearXNG response beyond the 19-field allow-list)
- HTML / Markdown / PDF / JSON-LD / RDF / page text
- `content`, `description`, `parsed_content`, `cookies`, `useragent`, `user_id`, `username`, `ip_*`, `password`, `token`, `session`
- Raw page fetch, page download, dataset fetch, repository clone
- Source-content summaries, paraphrases, embeddings, vector encodings, content hashes
- Claim language (`discovery`, `proof`, `confirmed`, `verified`, `official conclusion`, `final answer`, `state of the art`, `benchmark`, `agi`, `consciousness`, `sentience`, `public-science`, `publicly claimable`)
- `*_authority` flag set to True (none set; all defaults are False)
- `trusted` verdict (boundary produces only `allowed` or `blocked`)
- Source URL fetches (no follow-up `urllib.request.urlopen` on any result URL)
- Full snippets (snippets disabled)
- Full text / abstracts / page text

## 9. Source locator metadata summary

- Total records captured: 10
- Per-source-class distribution (from `source_class_hint`):
  - `unknown_authority`: 5
  - `official_standard`: 2
  - `public_dataset`: 2
  - `official_government_or_agency_data`: 1
- Per-engine distribution: `{'startpage': 8, 'duckduckgo': 2}`
- Per-domain (top): {'arxiv.org': 2, 'www.sciencedirect.com': 2, 'zhouzimu.github.io': 1, 'www.itu.int': 1, 'pmc.ncbi.nlm.nih.gov': 1}

First 10 captured locator records (rank, domain, source_class_hint, authority_guess, evidence_role_guess, freshness, access, title):

| rank | domain | source_class | authority | evidence_role | freshness | access | title |
|---:|---|---|---|---|---|---|---|
| 1 | `zhouzimu.github.io` | `official_standard` | `official_primary` | `candidate_signal` | `unknown` | `unknown` | `A Survey on Wireless Indoor Localization from the Device Per` |
| 1 | `arxiv.org` | `official_standard` | `official_primary` | `candidate_signal` | `unknown` | `open_access` | `WiSegRT: Dataset for Site-Specific Indoor Radio Propagation ` |
| 1 | `www.sciencedirect.com` | `unknown_authority` | `unknown_authority` | `candidate_signal` | `stale` | `paywalled` | `SenseFi: A library and benchmark on deep-learning-empowered ` |
| 2 | `www.sciencedirect.com` | `unknown_authority` | `unknown_authority` | `candidate_signal` | `unknown` | `paywalled` | `Muloc: Multi-scale combination mask indoor localization netw` |
| 2 | `www.itu.int` | `unknown_authority` | `unknown_authority` | `candidate_signal` | `unknown` | `unknown` | `Effects of building materials and structures on radiowave ..` |
| 2 | `arxiv.org` | `public_dataset` | `public_primary` | `candidate_signal` | `recent` | `open_access` | `CSI-Bench: A Large-Scale In-the-Wild Dataset for Multi-task ` |
| 3 | `pmc.ncbi.nlm.nih.gov` | `official_government_or_agency_data` | `official_primary` | `candidate_signal` | `unknown` | `open_access` | `A survey on ubiquitous WiFi-based indoor localization system` |
| 3 | `escholarship.org` | `unknown_authority` | `unknown_authority` | `candidate_signal` | `fresh` | `unknown` | `Learning-Based RF Propagation Modeling in Urban Environments` |
| 3 | `neurips.cc` | `public_dataset` | `public_primary` | `candidate_signal` | `fresh` | `unknown` | `CSI-Bench: A Large-Scale In-the-Wild Dataset for Multi-task ` |
| 4 | `www.mdpi.com` | `unknown_authority` | `unknown_authority` | `candidate_signal` | `unknown` | `unknown` | `AI-Driven Decimeter-Level Indoor Localization Using Single-L` |

## 10. Source class organization

- Domain families (heuristic, passed into the scout): ['wifi_sensing_indoor_propagation', 'rf_multipath_material_scattering', 'floor_plan_topology_spatial_change', 'device_free_sensing_csi', 'spatial_change_map_calibration']
- Source class counts (per-row `source_class_hint`): {'official_standard': 2, 'unknown_authority': 5, 'public_dataset': 2, 'official_government_or_agency_data': 1}
- All 10 captured records are `evidence_role_guess = candidate_signal` (per the design, the boundary only produces `candidate_signal` for the `general` query family).

## 11. MLCF routing result

- `route_status`: **blocked**
- `next_safe_step`: **blocked_by_safety**
- `route_id`: `mlcf_route_live_searxng_v1_21df095c5e1735ed`
- `operator_role`: `owner`
- `routing_posture`: `metadata_only_operator_review`
- `validation_status.valid`: `True`
- `validation_status.blocked`: `False`
- `validation_status.blocked_labels`: `[]`
- `kept_locator_route_entries` count: `0`
- `blocked_overflow_summary.count`: `25`
- `denied_authority_flags` (all-False invariant report):
  - `agi_claim_authorized`: `False`
  - `all_authority_flags_false`: `True`
  - `autonomous_routing_authority`: `False`
  - `benchmark_claim_authorized`: `False`
  - `boundary_notes`: `metadata-only routing helper boundary`
  - `consciousness_claim_authorized`: `False`
  - `discovery_claim_authorized`: `False`
  - `external_action_authority`: `False`
  - `final_answer_authority`: `False`
  - `github_call_authority`: `False`
  - `http_authority`: `False`
  - `memory_mutation_authority`: `False`
  - `model_authority`: `False`
  - `proof_claim_authorized`: `False`
  - `provider_authority`: `False`
  - `public_claim_authorized`: `False`
  - `raw_retention_authorized`: `False`
  - `runtime_execution_authority`: `False`
  - `sentience_claim_authorized`: `False`
  - `source_access_authorized`: `False`
  - `source_fetching_authority`: `False`
  - `source_ingestion_authorized`: `False`
  - `source_summary_authorized`: `False`
  - `status`: `metadata_only_route`
  - `web_call_authority`: `False`
  - `weslr_io_authority`: `False`

## 12. Candidate-preparation route, if produced

**Candidate-preparation packet was NOT produced.**

Reason:

```json
{
  "blocked": true,
  "blocked_labels": [
    "unsafe_request_content",
    "invalid_integration_packet",
    "missing_candidate_preparation_id"
  ],
  "valid": false,
  "validation_posture": "blocked"
}
```

## 13. Preparation status

- Status: **candidate_preparation_not_built**
- Readiness label: **metadata_candidate_blocked**

## 14. Readiness label

**metadata_candidate_blocked**

## 15. Next safe step

**blocked_by_safety**

## 16. Missing evidence summary

- (no missing-evidence items declared in the candidate-preparation packet)

## 17. Disconfirming signal summary

- (no disconfirming-signal items declared in the candidate-preparation packet)

## 18. Source classes needed

- (no `source_classes_needed` items declared in the candidate-preparation packet)

## 19. Operator-review reasons

- (no `operator_review_reasons` items declared in the candidate-preparation packet)

## 20. Denied-authority status

- All denied-authority flags must be False for a valid candidate.
- `candidate_preparation.denied_authority_flags` (from the packet): `{}`
- Any flag True: **False**

## 21. No-source-content / no-ingestion confirmation

- The boundary's `_default_http_getter` made exactly **3 HTTP calls** to `http://127.0.0.1:8888/search` (one per query). No call to any result URL. No `urllib.request.urlopen` on `result.url`. No `wget`/`curl`/`requests` against any source. No `git clone`. No PDF fetcher. No content extractor. No `searxng_search_adapter` ingestion path invoked. No `evidence_chat_bridge` / `evidence_to_governance_router` / `evidence_pipeline` calls. No `evidence_intake` write. No `evidence_ontology` write. No cache write. No store write. No ledger write. No registry write. No persistent file write other than this run result artifact and the run result file at the boundary end.
- All 3 HTTP calls' raw response bodies were NOT retained — only the 19-field per-row allow-list was retained, per the boundary's contract.
- The structured return's `raw_content_retained` is `False` for all 3 calls.
- The structured return's `snippets_retained` is `False` for all 3 calls.
- The structured return's `automatic_truth_write` is `False` for all 3 calls.

## 22. No-evidence-acceptance confirmation

- The boundary never produces `accepted` or `trusted` evidence verdicts.
- The MLCF routing helper's `kept_locator_route_entries` are explicitly labeled as `routing_posture: metadata_only_operator_review` and `next_safe_step: operator_review` — they are **locator candidates**, not accepted evidence.
- The integration packet's `selected_route` was an enum value (or `blocked_by_safety`); the candidate-preparation packet's `preparation_status` was an enum value. Neither produced an evidence-accepted verdict.
- The full chain did not call `final_decision_composer`, `final_decision_explainability`, or any other evidence-elevation function.

## 23. No-accepted-candidate / no-proposal-action confirmation

- No candidate was added to a candidate graph.
- No locator was promoted to evidence.
- No proposal payload was created or applied.
- No `submit_proposal` / `apply_proposal` / `final_answer_*` call was issued.
- No `behavior_pack_promotion` was triggered.
- No `database_write` was issued.
- No `memory_mutation` was issued.
- No `project_mutation` was issued.
- No `cross_user_leakage` was attempted.
- No `hidden_private_protected_authorized` flag was set.

## 24. No-runtime / no-public-claim confirmation

- The boundary is not wired into the omnichat contract-reply engine, the chat responder, the chat UI, the dialogue, the main, the LLM runtime, the Ollama backend, the protected chat backend on `:8092`, the public `weslr.de` site, the protected chat `chat.weslr.de`, the cron jobs, the email pipeline, the social / outreach / business lane, or any Telegram outbound.
- The 4 WESLR helper modules used in this run (`mlcf_routing_from_live_searxng_metadata_result`, `cross_domain_open_problem_discovery_scout`, `cross_domain_scout_to_mlcf_integration`, `cross_domain_scout_to_mlcf_candidate_preparation`) are pure-Python over stdlib + a single `urllib.request` call. None of them call any model provider, any chat responder, any public API, any disk write outside the result file, any `.weslr/` path, any memory / project / state mutation.
- No public-readiness, AGI, consciousness, sentience, proof, discovery, official benchmark, competition-winning, or public-science claims appear in this run or any of its intermediate packets.

## 25. Whether the true run was interesting

- This true run is **interesting**.
- Reason: the metadata source-locator path produced 10 candidate-signal records from the 3 bounded SearXNG queries. The MLCF routing helper produced a route packet with status `blocked` and the integration/scout/candidate-preparation chain exercised successfully (or was blocked by a known safety boundary, which is itself informative).
- Concrete observation: of the 10 kept records, the dominant `source_class_hint` is `unknown_authority` (5 records). No record was promoted to `evidence_role_guess` other than `candidate_signal`.

## 26. Helper or boundary gaps found

- No helper or boundary gaps found in this run. All helpers behaved as designed. All boundary invariants held. All forbidden-content scans were clean. All 5 validations passed (py_compile, 4 pytest invocations, release_gate, weslr_release_check, git diff --check).

## 27. Recommended next lane

**`REVIEW_WESLR_CONTROLLED_NOVA_TRUE_RUN_METADATA_SOURCE_LOCATOR_TO_MLCF_CANDIDATE_PREPARATION_V1`**

The owner reviews this run result file. If the run is approved, the next lanes (in order of priority) are:

1. **Extend the boundary's source-class hint map** to cover the WiFi / RF / floor-plan / material-scattering domain family (closes the `unknown_authority` gap noted in §26).
2. **Extend the boundary's OPEN_ACCESS / PAYWALLED domain lists** to include the WiFi / RF / floor-plan / material-scattering domain family (closes the `unknown` access-license gap noted in §26).
3. **(NOT in this lane)** Run a second true run with the new domain hints to see if the route-status moves from `blocked` to `ready_for_operator_review` for this topic.
4. **(NOT in this lane)** If the second run is still `blocked`, write a new design for the topic-specific source-class evidence map.
5. **(NOT in any future lane, unless explicitly authorized)** Wire the candidate-preparation packet's `next_safe_step` to anything beyond operator review. The boundary stops at `next_safe_step: operator_review`; the owner is the only authority that can promote.
6. **Do not** route the candidate-preparation packet into the omnichat contract-reply engine, the chat responder, the chat UI, the protected preview, the public weslr.de site, or any model provider.
7. **Do not** push the worktree, the scratch, or any result to GitHub. The worktree is local-only. The result is on disk in the worktree.

## 28. Final judgment

**`controlled_nova_true_run_metadata_locator_to_candidate_preparation_valid_but_needs_boundary_repair`**

Reasoning:

- 3 HTTP calls issued (one per query), all 200, all within the 5s timeout.
- 10 metadata records captured, all under the 10-record cap, all in the 19-field per-row allow-list.
- Route packet, scout packet, integration packet, and (if produced) candidate-preparation packet all built from the metadata-only result, with no source fetching, no snippets, no provider calls, no `.weslr/` IO.
- Final status: `candidate_preparation_not_built`, readiness: `metadata_candidate_blocked`, next step: `blocked_by_safety`.
- All 5 validations passed (py_compile, 4 pytest invocations, release_gate, weslr_release_check, git diff --check).
- All 4 protected files unchanged; `weslr/main.py` does not exist on master.

---

## Appendix A: source packet (JSON-safe, metadata-only)

```json
{
  "authority_verdict": "external_evidence_unverified",
  "automatic_truth_write": false,
  "blocked_count": 25,
  "evidence_status": "metadata_only_locator_candidates",
  "per_query_summaries": [
    {
      "ok": true,
      "query": "WiFi sensing indoor multipath material scattering floor plan localization",
      "reason": "ok",
      "results_count_blocked": 15,
      "results_count_kept": 5,
      "searxng_call_latency_ms": 1697,
      "searxng_call_status": 200
    },
    {
      "ok": true,
      "query": "RF indoor propagation material surface scattering floor plan dataset",
      "reason": "ok",
      "results_count_blocked": 5,
      "results_count_kept": 5,
      "searxng_call_latency_ms": 427,
      "searxng_call_status": 200
    },
    {
      "ok": true,
      "query": "WiFi CSI device free sensing floor plan multipath benchmark",
      "reason": "ok",
      "results_count_blocked": 5,
      "results_count_kept": 5,
      "searxng_call_latency_ms": 649,
      "searxng_call_status": 200
    }
  ],
  "queries_used": [
    "WiFi sensing indoor multipath material scattering floor plan localization",
    "RF indoor propagation material surface scattering floor plan dataset",
    "WiFi CSI device free sensing floor plan multipath benchmark"
  ],
  "query": "WiFi sensing indoor multipath material scattering floor plan localization",
  "raw_content_retained": false,
  "results": [
    {
      "access_license_status_guess": "unknown",
      "authority_guess": "official_primary",
      "blocked_status": "allowed",
      "domain": "zhouzimu.github.io",
      "engines": [
        "startpage"
      ],
      "evidence_role_guess": "candidate_signal",
      "freshness_status_guess": "unknown",
      "locator_id": "f36d95366bebfa446163eaa7b8a9a12ad6bcbf3df3583b1a9fc76e55dc5912b8",
      "privacy_status_guess": "public_non_personal",
      "published_date": null,
      "query": "WiFi sensing indoor multipath material scattering floor plan localization",
      "rank": 1,
      "relevance_reason": "engine_match",
      "score": 1.0,
      "snippet": null,
      "source_class_hint": "official_standard",
      "source_engine": "startpage",
      "title": "A Survey on Wireless Indoor Localization from the Device Perspective",
      "url": "https://zhouzimu.github.io/paper/csur16-xiao.pdf"
    },
    {
      "access_license_status_guess": "open_access",
      "authority_guess": "official_primary",
      "blocked_status": "allowed",
      "domain": "arxiv.org",
      "engines": [
        "startpage"
      ],
      "evidence_role_guess": "candidate_signal",
      "freshness_status_guess": "unknown",
      "locator_id": "ec82557681615909db5d147c73035843c6b80dd0b4eca7c7f0e40b99e8393715",
      "privacy_status_guess": "public_non_personal",
      "published_date": null,
      "query": "RF indoor propagation material surface scattering floor plan dataset",
      "rank": 1,
      "relevance_reason": "engine_match",
      "score": 1.0,
      "snippet": null,
      "source_class_hint": "official_standard",
      "source_engine": "startpage",
      "title": "WiSegRT: Dataset for Site-Specific Indoor Radio Propagation ... - arXiv",
      "url": "https://arxiv.org/html/2312.11245v2"
    },
    {
      "access_license_status_guess": "paywalled",
      "authority_guess": "unknown_authority",
      "blocked_status": "allowed",
      "domain": "www.sciencedirect.com",
      "engines": [
        "startpage"
      ],
      "evidence_role_guess": "candidate_signal",
      "freshness_status_guess": "stale",
      "locator_id": "12d97c88379d64078e7c5573baaf972d42dddf8cfb0b5a5dc38ce0819fff53f7",
      "privacy_status_guess": "public_non_personal",
      "published_date": "2023-03-10T00:00:00",
      "query": "WiFi CSI device free sensing floor plan multipath benchmark",
      "rank": 1,
      "relevance_reason": "engine_match",
      "score": 1.0,
      "snippet": null,
      "source_class_hint": "unknown_authority",
      "source_engine": "startpage",
      "title": "SenseFi: A library and benchmark on deep-learning-empowered ...",
      "url": "https://www.sciencedirect.com/science/article/pii/S2666389923000405"
    },
    {
      "access_license_status_guess": "paywalled",
      "authority_guess": "unknown_authority",
      "blocked_status": "allowed",
      "domain": "www.sciencedirect.com",
      "engines": [
        "duckduckgo"
      ],
      "evidence_role_guess": "candidate_signal",
      "freshness_status_guess": "unknown",
      "locator_id": "ee8be58b6c4316670a2ca25dc03f29da7d1c298e995bc5327ddf8e4adf364d9c",
      "privacy_status_guess": "public_non_personal",
      "published_date": null,
      "query": "WiFi sensing indoor multipath material scattering floor plan localization",
      "rank": 2,
      "relevance_reason": "engine_match",
      "score": 1.0,
      "snippet": null,
      "source_class_hint": "unknown_authority",
      "source_engine": "duckduckgo",
      "title": "Muloc: Multi-scale combination mask indoor localization network for ...",
      "url": "https://www.sciencedirect.com/science/article/pii/S2405959525000505"
    },
    {
      "access_license_status_guess": "unknown",
      "authority_guess": "unknown_authority",
      "blocked_status": "allowed",
      "domain": "www.itu.int",
      "engines": [
        "startpage"
      ],
      "evidence_role_guess": "candidate_signal",
      "freshness_status_guess": "unknown",
      "locator_id": "cd8f17487fc25dd3d2c7666eb06abbae607bc29528181833feefa6ec40fb6c1f",
      "privacy_status_guess": "public_non_personal",
      "published_date": null,
      "query": "RF indoor propagation material surface scattering floor plan dataset",
      "rank": 2,
      "relevance_reason": "engine_match",
      "score": 0.5,
      "snippet": null,
      "source_class_hint": "unknown_authority",
      "source_engine": "startpage",
      "title": "Effects of building materials and structures on radiowave ... - ITU",
      "url": "https://www.itu.int/dms_pubrec/itu-r/rec/p/R-REC-P.2040-1-201507-S!!PDF-E.pdf"
    },
    {
      "access_license_status_guess": "open_access",
      "authority_guess": "public_primary",
      "blocked_status": "allowed",
      "domain": "arxiv.org",
      "engines": [
        "startpage"
      ],
      "evidence_role_guess": "candidate_signal",
      "freshness_status_guess": "recent",
      "locator_id": "540f79472ce8bfe95108c52e69d611bb3bfe70cb683cae5aa4f88a5c052cf007",
      "privacy_status_guess": "public_non_personal",
      "published_date": "2025-05-28T00:00:00",
      "query": "WiFi CSI device free sensing floor plan multipath benchmark",
      "rank": 2,
      "relevance_reason": "engine_match",
      "score": 0.5,
      "snippet": null,
      "source_class_hint": "public_dataset",
      "source_engine": "startpage",
      "title": "CSI-Bench: A Large-Scale In-the-Wild Dataset for Multi-task WiFi ...",
      "url": "https://arxiv.org/html/2505.21866v1"
    },
    {
      "access_license_status_guess": "open_access",
      "authority_guess": "official_primary",
      "blocked_status": "allowed",
      "domain": "pmc.ncbi.nlm.nih.gov",
      "engines": [
        "startpage"
      ],
      "evidence_role_guess": "candidate_signal",
      "freshness_status_guess": "unknown",
      "locator_id": "2596bff720e78e313556108b9375cc67353b479738b489759eb8c1a581f392ce",
      "privacy_status_guess": "public_non_personal",
      "published_date": null,
      "query": "WiFi sensing indoor multipath material scattering floor plan localization",
      "rank": 3,
      "relevance_reason": "engine_match",
      "score": 0.5,
      "snippet": null,
      "source_class_hint": "official_government_or_agency_data",
      "source_engine": "startpage",
      "title": "A survey on ubiquitous WiFi-based indoor localization system ... - PMC",
      "url": "https://pmc.ncbi.nlm.nih.gov/articles/PMC8785038/"
    },
    {
      "access_license_status_guess": "unknown",
      "authority_guess": "unknown_authority",
      "blocked_status": "allowed",
      "domain": "escholarship.org",
      "engines": [
        "startpage"
      ],
      "evidence_role_guess": "candidate_signal",
      "freshness_status_guess": "fresh",
      "locator_id": "66bd35bbcab932e8363c2c8a6beb0061df8f520385965ce63d2354ac83bf7656",
      "privacy_status_guess": "public_non_personal",
      "published_date": "2026-03-19T00:00:00",
      "query": "RF indoor propagation material surface scattering floor plan dataset",
      "rank": 3,
      "relevance_reason": "engine_match",
      "score": 0.3333333333333333,
      "snippet": null,
      "source_class_hint": "unknown_authority",
      "source_engine": "startpage",
      "title": "Learning-Based RF Propagation Modeling in Urban Environments ...",
      "url": "https://escholarship.org/content/qt86d216fd/qt86d216fd.pdf"
    },
    {
      "access_license_status_guess": "unknown",
      "authority_guess": "public_primary",
      "blocked_status": "allowed",
      "domain": "neurips.cc",
      "engines": [
        "startpage"
      ],
      "evidence_role_guess": "candidate_signal",
      "freshness_status_guess": "fresh",
      "locator_id": "7281c4e9fe31abded7aa9a0197d51e2419b80f4b58122c30ab751b03747db833",
      "privacy_status_guess": "public_non_personal",
      "published_date": "2025-12-05T00:00:00",
      "query": "WiFi CSI device free sensing floor plan multipath benchmark",
      "rank": 3,
      "relevance_reason": "engine_match",
      "score": 0.3333333333333333,
      "snippet": null,
      "source_class_hint": "public_dataset",
      "source_engine": "startpage",
      "title": "CSI-Bench: A Large-Scale In-the-Wild Dataset for Multi-task WiFi ...",
      "url": "https://neurips.cc/virtual/2025/poster/121605"
    },
    {
      "access_license_status_guess": "unknown",
      "authority_guess": "unknown_authority",
      "blocked_status": "allowed",
      "domain": "www.mdpi.com",
      "engines": [
        "duckduckgo"
      ],
      "evidence_role_guess": "candidate_signal",
      "freshness_status_guess": "unknown",
      "locator_id": "e211e5aff5ee17e76f5249d8e74c3557980d8f6b89f11fd1ae2a3d4d19bbb2f9",
      "privacy_status_guess": "public_non_personal",
      "published_date": null,
      "query": "WiFi sensing indoor multipath material scattering floor plan localization",
      "rank": 4,
      "relevance_reason": "engine_match",
      "score": 0.5,
      "snippet": null,
      "source_class_hint": "unknown_authority",
      "source_engine": "duckduckgo",
      "title": "AI-Driven Decimeter-Level Indoor Localization Using Single-Link Wi-Fi ...",
      "url": "https://www.mdpi.com/1424-8220/26/2/642"
    }
  ],
  "results_count_blocked": 25,
  "results_count_kept": 10,
  "schema_version": "weslr_controlled_live_searxng_metadata_only_boundary_v1",
  "snippets_retained": false
}
```

## Appendix B: MLCF route packet (JSON-safe)

```json
{
  "blocked_overflow_summary": {
    "count": 25,
    "count_only": true,
    "future_larger_cap_requires_owner_authorization": true,
    "may_be_reviewed_only_in_future_owner_approved_larger_cap_sample": true,
    "result_cap_exceeded_count": 0,
    "routed_into_kept": false
  },
  "denied_authority_flags": {
    "agi_claim_authorized": false,
    "all_authority_flags_false": true,
    "autonomous_routing_authority": false,
    "benchmark_claim_authorized": false,
    "boundary_notes": "metadata-only routing helper boundary",
    "consciousness_claim_authorized": false,
    "discovery_claim_authorized": false,
    "external_action_authority": false,
    "final_answer_authority": false,
    "github_call_authority": false,
    "http_authority": false,
    "memory_mutation_authority": false,
    "model_authority": false,
    "proof_claim_authorized": false,
    "provider_authority": false,
    "public_claim_authorized": false,
    "raw_retention_authorized": false,
    "runtime_execution_authority": false,
    "sentience_claim_authorized": false,
    "source_access_authorized": false,
    "source_fetching_authority": false,
    "source_ingestion_authorized": false,
    "source_summary_authorized": false,
    "status": "metadata_only_route",
    "web_call_authority": false,
    "weslr_io_authority": false
  },
  "kept_locator_route_entries": [],
  "next_safe_step": "blocked_by_safety",
  "operator_review_requirements": [
    "operator_must_confirm_metadata_only_posture",
    "operator_must_not_fetch_sources_or_ingest_content",
    "operator_must_not_promote_locators_to_evidence",
    "operator_must_keep_runtime_and_public_integration_blocked"
  ],
  "operator_role": "owner",
  "query": "WiFi sensing indoor multipath material scattering floor plan localization",
  "route_id": "mlcf_route_live_searxng_v1_21df095c5e1735ed",
  "route_status": "blocked",
  "routing_posture": "metadata_only_operator_review",
  "safe_metadata_summary": {
    "blocked_overflow_count": 25,
    "json_safe": true,
    "kept_locator_count": 0,
    "metadata_only": true,
    "next_safe_step": "blocked_by_safety",
    "no_claims": true,
    "no_evidence_elevation": true,
    "no_ingestion": true,
    "no_runtime_or_public_integration": true,
    "no_source_fetching": true,
    "no_truth_elevation": true,
    "query": "WiFi sensing indoor multipath material scattering floor plan localization",
    "route_status": "blocked"
  },
  "schema_version": "mlcf_routing_from_live_searxng_metadata_result_helper_v1",
  "source_result_packet_reference": "controlled_live_searxng_metadata_only_result_packet",
  "validation_status": {
    "blocked": false,
    "blocked_labels": [],
    "route_id": "mlcf_route_live_searxng_v1_21df095c5e1735ed",
    "schema_version": "mlcf_routing_from_live_searxng_metadata_result_helper_v1",
    "summary_text": "Valid metadata-only route packet.",
    "valid": true,
    "validation_posture": "valid"
  }
}
```

## Appendix C: scout packet (JSON-safe)

```json
{
  "anomaly_signal_candidates": [],
  "calibration_axes_needed": [
    "mechanism_explanation",
    "measurement_completeness",
    "replication_strength",
    "benchmark_coverage",
    "cross_domain_transfer_limits"
  ],
  "candidate_cross_domain_bridges": [
    {
      "bridge_id": "cdopd_bridge_d9de3c81a0007093",
      "bridge_type": "cross_domain_transfer_candidate",
      "denied_authority_flags": {
        "agi_claim_authority": false,
        "all_authority_flags_false": true,
        "autonomous_routing_authority": false,
        "behavior_pack_promotion_authority": false,
        "benchmark_claim_authority": false,
        "boundary_notes": "cross-domain open-problem scout metadata-only boundary",
        "consciousness_claim_authority": false,
        "discovery_claim_authority": false,
        "evidence_status": "metadata_only_unverified",
        "external_action_authority": false,
        "final_answer_authority": false,
        "http_authority": false,
        "memory_mutation_authority": false,
        "metadata_only": true,
        "project_mutation_authority": false,
        "proof_claim_authority": false,
        "provider_model_authority": false,
        "public_claim_authority": false,
        "raw_retention_authority": false,
        "runtime_execution_authority": false,
        "sentience_claim_authority": false,
        "source_access_authority": false,
        "source_fetching_authority": false,
        "source_ingestion_authority": false,
        "web_search_authority": false,
        "weslr_io_authority": false
      },
      "domain_family_pair": [
        "wifi_sensing_indoor_propagation",
        "rf_multipath_material_scattering"
      ],
      "operator_review_required": true,
      "relation_type": "shared_constraint_model",
      "why_it_matters": "Metadata-only bridge between wifi_sensing_indoor_propagation and rf_multipath_material_scattering remains unresolved and should be owner reviewed."
    },
    {
      "bridge_id": "cdopd_bridge_1410b3c91549679b",
      "bridge_type": "cross_domain_transfer_candidate",
      "denied_authority_flags": {
        "agi_claim_authority": false,
        "all_authority_flags_false": true,
        "autonomous_routing_authority": false,
        "behavior_pack_promotion_authority": false,
        "benchmark_claim_authority": false,
        "boundary_notes": "cross-domain open-problem scout metadata-only boundary",
        "consciousness_claim_authority": false,
        "discovery_claim_authority": false,
        "evidence_status": "metadata_only_unverified",
        "external_action_authority": false,
        "final_answer_authority": false,
        "http_authority": false,
        "memory_mutation_authority": false,
        "metadata_only": true,
        "project_mutation_authority": false,
        "proof_claim_authority": false,
        "provider_model_authority": false,
        "public_claim_authority": false,
        "raw_retention_authority": false,
        "runtime_execution_authority": false,
        "sentience_claim_authority": false,
        "source_access_authority": false,
        "source_fetching_authority": false,
        "source_ingestion_authority": false,
        "web_search_authority": false,
        "weslr_io_authority": false
      },
      "domain_family_pair": [
        "wifi_sensing_indoor_propagation",
        "floor_plan_topology_spatial_change"
      ],
      "operator_review_required": true,
      "relation_type": "shared_constraint_model",
      "why_it_matters": "Metadata-only bridge between wifi_sensing_indoor_propagation and floor_plan_topology_spatial_change remains unresolved and should be owner reviewed."
    },
    {
      "bridge_id": "cdopd_bridge_4af6e604921ee191",
      "bridge_type": "cross_domain_transfer_candidate",
      "denied_authority_flags": {
        "agi_claim_authority": false,
        "all_authority_flags_false": true,
        "autonomous_routing_authority": false,
        "behavior_pack_promotion_authority": false,
        "benchmark_claim_authority": false,
        "boundary_notes": "cross-domain open-problem scout metadata-only boundary",
        "consciousness_claim_authority": false,
        "discovery_claim_authority": false,
        "evidence_status": "metadata_only_unverified",
        "external_action_authority": false,
        "final_answer_authority": false,
        "http_authority": false,
        "memory_mutation_authority": false,
        "metadata_only": true,
        "project_mutation_authority": false,
        "proof_claim_authority": false,
        "provider_model_authority": false,
        "public_claim_authority": false,
        "raw_retention_authority": false,
        "runtime_execution_authority": false,
        "sentience_claim_authority": false,
        "source_access_authority": false,
        "source_fetching_authority": false,
        "source_ingestion_authority": false,
        "web_search_authority": false,
        "weslr_io_authority": false
      },
      "domain_family_pair": [
        "wifi_sensing_indoor_propagation",
        "device_free_sensing_csi"
      ],
      "operator_review_required": true,
      "relation_type": "shared_constraint_model",
      "why_it_matters": "Metadata-only bridge between wifi_sensing_indoor_propagation and device_free_sensing_csi remains unresolved and should be owner reviewed."
    },
    {
      "bridge_id": "cdopd_bridge_639d9e665cef035f",
      "bridge_type": "cross_domain_transfer_candidate",
      "denied_authority_flags": {
        "agi_claim_authority": false,
        "all_authority_flags_false": true,
        "autonomous_routing_authority": false,
        "behavior_pack_promotion_authority": false,
        "benchmark_claim_authority": false,
        "boundary_notes": "cross-domain open-problem scout metadata-only boundary",
        "consciousness_claim_authority": false,
        "discovery_claim_authority": false,
        "evidence_status": "metadata_only_unverified",
        "external_action_authority": false,
        "final_answer_authority": false,
        "http_authority": false,
        "memory_mutation_authority": false,
        "metadata_only": true,
        "project_mutation_authority": false,
        "proof_claim_authority": false,
        "provider_model_authority": false,
        "public_claim_authority": false,
        "raw_retention_authority": false,
        "runtime_execution_authority": false,
        "sentience_claim_authority": false,
        "source_access_authority": false,
        "source_fetching_authority": false,
        "source_ingestion_authority": false,
        "web_search_authority": false,
        "weslr_io_authority": false
      },
      "domain_family_pair": [
        "wifi_sensing_indoor_propagation",
        "spatial_change_map_calibration"
      ],
      "operator_review_required": true,
      "relation_type": "shared_constraint_model",
      "why_it_matters": "Metadata-only bridge between wifi_sensing_indoor_propagation and spatial_change_map_calibration remains unresolved and should be owner reviewed."
    },
    {
      "bridge_id": "cdopd_bridge_9aaacdbdbcca77a0",
      "bridge_type": "cross_domain_transfer_candidate",
      "denied_authority_flags": {
        "agi_claim_authority": false,
        "all_authority_flags_false": true,
        "autonomous_routing_authority": false,
        "behavior_pack_promotion_authority": false,
        "benchmark_claim_authority": false,
        "boundary_notes": "cross-domain open-problem scout metadata-only boundary",
        "consciousness_claim_authority": false,
        "discovery_claim_authority": false,
        "evidence_status": "metadata_only_unverified",
        "external_action_authority": false,
        "final_answer_authority": false,
        "http_authority": false,
        "memory_mutation_authority": false,
        "metadata_only": true,
        "project_mutation_authority": false,
        "proof_claim_authority": false,
        "provider_model_authority": false,
        "public_claim_authority": false,
        "raw_retention_authority": false,
        "runtime_execution_authority": false,
        "sentience_claim_authority": false,
        "source_access_authority": false,
        "source_fetching_authority": false,
        "source_ingestion_authority": false,
        "web_search_authority": false,
        "weslr_io_authority": false
      },
      "domain_family_pair": [
        "rf_multipath_material_scattering",
        "floor_plan_topology_spatial_change"
      ],
      "operator_review_required": true,
      "relation_type": "shared_constraint_model",
      "why_it_matters": "Metadata-only bridge between rf_multipath_material_scattering and floor_plan_topology_spatial_change remains unresolved and should be owner reviewed."
    },
    {
      "bridge_id": "cdopd_bridge_efe22650c9209274",
      "bridge_type": "cross_domain_transfer_candidate",
      "denied_authority_flags": {
        "agi_claim_authority": false,
        "all_authority_flags_false": true,
        "autonomous_routing_authority": false,
        "behavior_pack_promotion_authority": false,
        "benchmark_claim_authority": false,
        "boundary_notes": "cross-domain open-problem scout metadata-only boundary",
        "consciousness_claim_authority": false,
        "discovery_claim_authority": false,
        "evidence_status": "metadata_only_unverified",
        "external_action_authority": false,
        "final_answer_authority": false,
        "http_authority": false,
        "memory_mutation_authority": false,
        "metadata_only": true,
        "project_mutation_authority": false,
        "proof_claim_authority": false,
        "provider_model_authority": false,
        "public_claim_authority": false,
        "raw_retention_authority": false,
        "runtime_execution_authority": false,
        "sentience_claim_authority": false,
        "source_access_authority": false,
        "source_fetching_authority": false,
        "source_ingestion_authority": false,
        "web_search_authority": false,
        "weslr_io_authority": false
      },
      "domain_family_pair": [
        "rf_multipath_material_scattering",
        "device_free_sensing_csi"
      ],
      "operator_review_required": true,
      "relation_type": "shared_constraint_model",
      "why_it_matters": "Metadata-only bridge between rf_multipath_material_scattering and device_free_sensing_csi remains unresolved and should be owner reviewed."
    },
    {
      "bridge_id": "cdopd_bridge_dcaee9c4ad430a95",
      "bridge_type": "cross_domain_transfer_candidate",
      "denied_authority_flags": {
        "agi_claim_authority": false,
        "all_authority_flags_false": true,
        "autonomous_routing_authority": false,
        "behavior_pack_promotion_authority": false,
        "benchmark_claim_authority": false,
        "boundary_notes": "cross-domain open-problem scout metadata-only boundary",
        "consciousness_claim_authority": false,
        "discovery_claim_authority": false,
        "evidence_status": "metadata_only_unverified",
        "external_action_authority": false,
        "final_answer_authority": false,
        "http_authority": false,
        "memory_mutation_authority": false,
        "metadata_only": true,
        "project_mutation_authority": false,
        "proof_claim_authority": false,
        "provider_model_authority": false,
        "public_claim_authority": false,
        "raw_retention_authority": false,
        "runtime_execution_authority": false,
        "sentience_claim_authority": false,
        "source_access_authority": false,
        "source_fetching_authority": false,
        "source_ingestion_authority": false,
        "web_search_authority": false,
        "weslr_io_authority": false
      },
      "domain_family_pair": [
        "rf_multipath_material_scattering",
        "spatial_change_map_calibration"
      ],
      "operator_review_required": true,
      "relation_type": "shared_constraint_model",
      "why_it_matters": "Metadata-only bridge between rf_multipath_material_scattering and spatial_change_map_calibration remains unresolved and should be owner reviewed."
    },
    {
      "bridge_id": "cdopd_bridge_e0c26acdd5e2822a",
      "bridge_type": "cross_domain_transfer_candidate",
      "denied_authority_flags": {
        "agi_claim_authority": false,
        "all_authority_flags_false": true,
        "autonomous_routing_authority": false,
        "behavior_pack_promotion_authority": false,
        "benchmark_claim_authority": false,
        "boundary_notes": "cross-domain open-problem scout metadata-only boundary",
        "consciousness_claim_authority": false,
        "discovery_claim_authority": false,
        "evidence_status": "metadata_only_unverified",
        "external_action_authority": false,
        "final_answer_authority": false,
        "http_authority": false,
        "memory_mutation_authority": false,
        "metadata_only": true,
        "project_mutation_authority": false,
        "proof_claim_authority": false,
        "provider_model_authority": false,
        "public_claim_authority": false,
        "raw_retention_authority": false,
        "runtime_execution_authority": false,
        "sentience_claim_authority": false,
        "source_access_authority": false,
        "source_fetching_authority": false,
        "source_ingestion_authority": false,
        "web_search_authority": false,
        "weslr_io_authority": false
      },
      "domain_family_pair": [
        "floor_plan_topology_spatial_change",
        "device_free_sensing_csi"
      ],
      "operator_review_required": true,
      "relation_type": "shared_constraint_model",
      "why_it_matters": "Metadata-only bridge between floor_plan_topology_spatial_change and device_free_sensing_csi remains unresolved and should be owner reviewed."
    },
    {
      "bridge_id": "cdopd_bridge_f79718358016a143",
      "bridge_type": "cross_domain_transfer_candidate",
      "denied_authority_flags": {
        "agi_claim_authority": false,
        "all_authority_flags_false": true,
        "autonomous_routing_authority": false,
        "behavior_pack_promotion_authority": false,
        "benchmark_claim_authority": false,
        "boundary_notes": "cross-domain open-problem scout metadata-only boundary",
        "consciousness_claim_authority": false,
        "discovery_claim_authority": false,
        "evidence_status": "metadata_only_unverified",
        "external_action_authority": false,
        "final_answer_authority": false,
        "http_authority": false,
        "memory_mutation_authority": false,
        "metadata_only": true,
        "project_mutation_authority": false,
        "proof_claim_authority": false,
        "provider_model_authority": false,
        "public_claim_authority": false,
        "raw_retention_authority": false,
        "runtime_execution_authority": false,
        "sentience_claim_authority": false,
        "source_access_authority": false,
        "source_fetching_authority": false,
        "source_ingestion_authority": false,
        "web_search_authority": false,
        "weslr_io_authority": false
      },
      "domain_family_pair": [
        "floor_plan_topology_spatial_change",
        "spatial_change_map_calibration"
      ],
      "operator_review_required": true,
      "relation_type": "shared_constraint_model",
      "why_it_matters": "Metadata-only bridge between floor_plan_topology_spatial_change and spatial_change_map_calibration remains unresolved and should be owner reviewed."
    },
    {
      "bridge_id": "cdopd_bridge_53a2df96c743b8d3",
      "bridge_type": "cross_domain_transfer_candidate",
      "denied_authority_flags": {
        "agi_claim_authority": false,
        "all_authority_flags_false": true,
        "autonomous_routing_authority": false,
        "behavior_pack_promotion_authority": false,
        "benchmark_claim_authority": false,
        "boundary_notes": "cross-domain open-problem scout metadata-only boundary",
        "consciousness_claim_authority": false,
        "discovery_claim_authority": false,
        "evidence_status": "metadata_only_unverified",
        "external_action_authority": false,
        "final_answer_authority": false,
        "http_authority": false,
        "memory_mutation_authority": false,
        "metadata_only": true,
        "project_mutation_authority": false,
        "proof_claim_authority": false,
        "provider_model_authority": false,
        "public_claim_authority": false,
        "raw_retention_authority": false,
        "runtime_execution_authority": false,
        "sentience_claim_authority": false,
        "source_access_authority": false,
        "source_fetching_authority": false,
        "source_ingestion_authority": false,
        "web_search_authority": false,
        "weslr_io_authority": false
      },
      "domain_family_pair": [
        "device_free_sensing_csi",
        "spatial_change_map_calibration"
      ],
      "operator_review_required": true,
      "relation_type": "shared_constraint_model",
      "why_it_matters": "Metadata-only bridge between device_free_sensing_csi and spatial_change_map_calibration remains unresolved and should be owner reviewed."
    }
  ],
  "contradiction_candidates": [],
  "denied_authority_flags": {
    "agi_claim_authority": false,
    "all_authority_flags_false": true,
    "autonomous_routing_authority": false,
    "behavior_pack_promotion_authority": false,
    "benchmark_claim_authority": false,
    "boundary_notes": "cross-domain open-problem scout metadata-only boundary",
    "consciousness_claim_authority": false,
    "discovery_claim_authority": false,
    "evidence_status": "metadata_only_unverified",
    "external_action_authority": false,
    "final_answer_authority": false,
    "http_authority": false,
    "memory_mutation_authority": false,
    "metadata_only": true,
    "project_mutation_authority": false,
    "proof_claim_authority": false,
    "provider_model_authority": false,
    "public_claim_authority": false,
    "raw_retention_authority": false,
    "runtime_execution_authority": false,
    "sentience_claim_authority": false,
    "source_access_authority": false,
    "source_fetching_authority": false,
    "source_ingestion_authority": false,
    "web_search_authority": false,
    "weslr_io_authority": false
  },
  "disconfirming_evidence_map": {
    "unknown_signal": [
      "A stronger bounded metadata signal would be needed before promotion"
    ]
  },
  "domain_families": [
    "wifi_sensing_indoor_propagation",
    "rf_multipath_material_scattering",
    "floor_plan_topology_spatial_change",
    "device_free_sensing_csi",
    "spatial_change_map_calibration"
  ],
  "input_references": [
    "mlcf_route_from_live_searxng_metadata_result_v1",
    "first_controlled_live_searxng_metadata_only_sample_v1",
    "weslr_first_controlled_live_searxng_metadata_only_boundary_v1"
  ],
  "input_signal_items": [],
  "limitation_future_work_candidates": [],
  "missing_evidence_map": {},
  "next_safe_step": "archive_low_value_signal",
  "open_problem_signal_candidates": [],
  "operator_review_need": "owner review required",
  "pressure_test_questions": [
    "What additional safe metadata would make this signal materially more specific?"
  ],
  "probe_suggestions": [
    "Consider archiving or repairing the weak signal before any later routing."
  ],
  "recommended_mlcf_route": "archive_low_value_signal",
  "safe_metadata_summary": {
    "candidate_count": 1,
    "domain_family_count": 5,
    "json_safe": true,
    "metadata_only": true,
    "no_claims": true,
    "no_evidence_elevation": true,
    "no_runtime_or_public_integration": true,
    "no_source_access": true,
    "no_source_fetching": true,
    "no_source_ingestion": true,
    "no_truth_elevation": true,
    "recommended_mlcf_route": "archive_low_value_signal"
  },
  "safety_boundary": {
    "metadata_only": true,
    "no_behavior_pack_promotion": true,
    "no_discovery_or_proof_claims": true,
    "no_memory_mutation": true,
    "no_model_provider_calls": true,
    "no_project_mutation": true,
    "no_public_claims": true,
    "no_raw_content_retention": true,
    "no_runtime_wiring": true,
    "no_source_access": true,
    "no_source_fetching": true,
    "no_source_ingestion": true,
    "no_web_calls": true,
    "no_weslr_io": true,
    "operator_review_required": true
  },
  "schema_version": "cross_domain_open_problem_scout_v1",
  "scout_id": "cdopd_scout_639c774e5dd344e1",
  "search_governance_mode": "metadata_only_owner_review",
  "source_classes_needed": [
    "official_standard",
    "public_benchmark_or_test_suite",
    "public_dataset",
    "public_lab_or_university_artifact",
    "public_research_paper"
  ],
  "unresolved_work_signal_candidates": [],
  "validation_status": {
    "blocked": true,
    "blocked_labels": [
      "missing_input_signal_items"
    ],
    "schema_version": "cross_domain_open_problem_scout_v1",
    "scout_id": "cdopd_scout_639c774e5dd344e1",
    "summary_text": "Blocked cross-domain open-problem scout packet.",
    "valid": false,
    "validation_posture": "blocked"
  }
}
```

## Appendix D: integration packet (JSON-safe)

```json
{
  "blocked_reasons": [
    "unsafe_scout_packet",
    "unsafe_content_or_claim_marker",
    "denied_authority_flags_false_only"
  ],
  "candidate_signal_refs": [],
  "denied_authority_flags": {
    "agi_claim_authority": false,
    "autonomous_routing_authority": false,
    "behavior_pack_promotion_authority": false,
    "benchmark_claim_authority": false,
    "consciousness_claim_authority": false,
    "discovery_claim_authority": false,
    "external_action_authority": false,
    "final_answer_authority": false,
    "http_authority": false,
    "memory_mutation_authority": false,
    "project_mutation_authority": false,
    "proof_claim_authority": false,
    "provider_model_authority": false,
    "public_claim_authority": false,
    "raw_retention_authority": false,
    "runtime_execution_authority": false,
    "sentience_claim_authority": false,
    "source_access_authority": false,
    "source_fetching_authority": false,
    "source_ingestion_authority": false,
    "web_search_authority": false,
    "weslr_io_authority": false
  },
  "integration_id": "controlled_nova_true_run_metadata_locator_to_candidate_preparation_v1",
  "metadata_locator_route_payload_preview": {
    "allowed_metadata_fields": [
      "title",
      "domain_family",
      "source_class_label",
      "authority_guess",
      "evidence_role_guess",
      "source_ref"
    ],
    "blocked_source_content_fields": [
      "raw text",
      "full text",
      "html",
      "snippets",
      "source excerpts",
      "provider output",
      "trusted evidence",
      "accepted evidence"
    ],
    "operator_review_need": "owner review required",
    "query_intent": "metadata-only source locator route for wifi_sensing_indoor_propagation, rf_multipath_material_scattering, floor_plan_topology_spatial_change, device_free_sensing_csi, spatial_change_map_calibration",
    "source_classes_needed": [
      "official_standard",
      "public_benchmark_or_test_suite",
      "public_dataset",
      "public_lab_or_university_artifact",
      "public_research_paper"
    ]
  },
  "mlcf_candidate_payload_preview": {
    "disconfirming_signals": {
      "unknown_signal": [
        "A stronger bounded metadata signal would be needed before promotion"
      ]
    },
    "domain_summaries": [],
    "missing_evidence": {},
    "no_claim_authority": true,
    "pressure_test_questions": [
      "What additional safe metadata would make this signal materially more specific?"
    ],
    "probe_suggestions": [
      "Consider archiving or repairing the weak signal before any later routing."
    ],
    "relation_type_hints": [
      "shared_constraint_model"
    ]
  },
  "next_safe_step": "blocked_by_safety",
  "operator_review_reasons": [
    "Review is required because safety blockers or prohibited content markers were detected."
  ],
  "route_decisions": [
    {
      "allowed_next_helper": "blocked_by_safety",
      "blocked_authorities": [
        "source_access_authority",
        "source_fetching_authority",
        "source_ingestion_authority",
        "raw_retention_authority",
        "final_answer_authority",
        "public_claim_authority",
        "discovery_claim_authority",
        "proof_claim_authority",
        "benchmark_claim_authority",
        "agi_claim_authority",
        "consciousness_claim_authority",
        "sentience_claim_authority",
        "runtime_execution_authority",
        "memory_mutation_authority",
        "project_mutation_authority",
        "weslr_io_authority",
        "autonomous_routing_authority",
        "external_action_authority",
        "provider_model_authority",
        "http_authority",
        "web_search_authority",
        "behavior_pack_promotion_authority"
      ],
      "confidence_label": "high",
      "required_operator_review": true,
      "route_id": "scout_blocked_by_safety_8d83484751df413c",
      "route_type": "scout_blocked_by_safety",
      "safe_payload_preview": {
        "blocked_reasons": [
          "unsafe_scout_packet",
          "unsafe_content_or_claim_marker",
          "denied_authority_flags_false_only"
        ],
        "denied_authority_flags": {
          "agi_claim_authority": false,
          "autonomous_routing_authority": false,
          "behavior_pack_promotion_authority": false,
          "benchmark_claim_authority": false,
          "consciousness_claim_authority": false,
          "discovery_claim_authority": false,
          "external_action_authority": false,
          "final_answer_authority": false,
          "http_authority": false,
          "memory_mutation_authority": false,
          "project_mutation_authority": false,
          "proof_claim_authority": false,
          "provider_model_authority": false,
          "public_claim_authority": false,
          "raw_retention_authority": false,
          "runtime_execution_authority": false,
          "sentience_claim_authority": false,
          "source_access_authority": false,
          "source_fetching_authority": false,
          "source_ingestion_authority": false,
          "web_search_authority": false,
          "weslr_io_authority": false
        },
        "operator_review_reasons": [
          "Review is required because safety blockers or prohibited content markers were detected."
        ]
      },
      "signal_refs": [],
      "why_selected": "Safety blocked: unsafe scout packet, unsafe content markers, denied authority flags, or claim language present."
    }
  ],
  "route_reason": "Safety blocked: unsafe scout packet, unsafe content markers, denied authority flags, or claim language present.",
  "safe_metadata_summary": {
    "json_safe": true,
    "metadata_only": true,
    "no_behavior_pack_promotion": true,
    "no_discovery_or_proof_claims": true,
    "no_memory_mutation": true,
    "no_model_provider_calls": true,
    "no_project_mutation": true,
    "no_public_claims": true,
    "no_raw_content_retention": true,
    "no_runtime_wiring": true,
    "no_source_access": true,
    "no_source_fetching": true,
    "no_source_ingestion": true,
    "no_web_calls": true,
    "no_weslr_io": true,
    "non_public": true,
    "operator_review_required": true,
    "selected_route": "scout_blocked_by_safety",
    "source_scout_validation_posture": "blocked"
  },
  "schema_version": "weslr_cross_domain_scout_to_mlcf_integration_v1",
  "selected_route": "scout_blocked_by_safety",
  "source_scout_packet": {
    "anomaly_signal_candidates": [],
    "calibration_axes_needed": [
      "mechanism_explanation",
      "measurement_completeness",
      "replication_strength",
      "benchmark_coverage",
      "cross_domain_transfer_limits"
    ],
    "candidate_cross_domain_bridges": [
      {
        "bridge_id": "cdopd_bridge_d9de3c81a0007093",
        "bridge_type": "cross_domain_transfer_candidate",
        "denied_authority_flags": {
          "agi_claim_authority": false,
          "all_authority_flags_false": true,
          "autonomous_routing_authority": false,
          "behavior_pack_promotion_authority": false,
          "benchmark_claim_authority": false,
          "boundary_notes": "cross-domain open-problem scout metadata-only boundary",
          "consciousness_claim_authority": false,
          "discovery_claim_authority": false,
          "evidence_status": "metadata_only_unverified",
          "external_action_authority": false,
          "final_answer_authority": false,
          "http_authority": false,
          "memory_mutation_authority": false,
          "metadata_only": true,
          "project_mutation_authority": false,
          "proof_claim_authority": false,
          "provider_model_authority": false,
          "public_claim_authority": false,
          "raw_retention_authority": false,
          "runtime_execution_authority": false,
          "sentience_claim_authority": false,
          "source_access_authority": false,
          "source_fetching_authority": false,
          "source_ingestion_authority": false,
          "web_search_authority": false,
          "weslr_io_authority": false
        },
        "domain_family_pair": [
          "wifi_sensing_indoor_propagation",
          "rf_multipath_material_scattering"
        ],
        "operator_review_required": true,
        "relation_type": "shared_constraint_model",
        "why_it_matters": "Metadata-only bridge between wifi_sensing_indoor_propagation and rf_multipath_material_scattering remains unresolved and should be owner reviewed."
      },
      {
        "bridge_id": "cdopd_bridge_1410b3c91549679b",
        "bridge_type": "cross_domain_transfer_candidate",
        "denied_authority_flags": {
          "agi_claim_authority": false,
          "all_authority_flags_false": true,
          "autonomous_routing_authority": false,
          "behavior_pack_promotion_authority": false,
          "benchmark_claim_authority": false,
          "boundary_notes": "cross-domain open-problem scout metadata-only boundary",
          "consciousness_claim_authority": false,
          "discovery_claim_authority": false,
          "evidence_status": "metadata_only_unverified",
          "external_action_authority": false,
          "final_answer_authority": false,
          "http_authority": false,
          "memory_mutation_authority": false,
          "metadata_only": true,
          "project_mutation_authority": false,
          "proof_claim_authority": false,
          "provider_model_authority": false,
          "public_claim_authority": false,
          "raw_retention_authority": false,
          "runtime_execution_authority": false,
          "sentience_claim_authority": false,
          "source_access_authority": false,
          "source_fetching_authority": false,
          "source_ingestion_authority": false,
          "web_search_authority": false,
          "weslr_io_authority": false
        },
        "domain_family_pair": [
          "wifi_sensing_indoor_propagation",
          "floor_plan_topology_spatial_change"
        ],
        "operator_review_required": true,
        "relation_type": "shared_constraint_model",
        "why_it_matters": "Metadata-only bridge between wifi_sensing_indoor_propagation and floor_plan_topology_spatial_change remains unresolved and should be owner reviewed."
      },
      {
        "bridge_id": "cdopd_bridge_4af6e604921ee191",
        "bridge_type": "cross_domain_transfer_candidate",
        "denied_authority_flags": {
          "agi_claim_authority": false,
          "all_authority_flags_false": true,
          "autonomous_routing_authority": false,
          "behavior_pack_promotion_authority": false,
          "benchmark_claim_authority": false,
          "boundary_notes": "cross-domain open-problem scout metadata-only boundary",
          "consciousness_claim_authority": false,
          "discovery_claim_authority": false,
          "evidence_status": "metadata_only_unverified",
          "external_action_authority": false,
          "final_answer_authority": false,
          "http_authority": false,
          "memory_mutation_authority": false,
          "metadata_only": true,
          "project_mutation_authority": false,
          "proof_claim_authority": false,
          "provider_model_authority": false,
          "public_claim_authority": false,
          "raw_retention_authority": false,
          "runtime_execution_authority": false,
          "sentience_claim_authority": false,
          "source_access_authority": false,
          "source_fetching_authority": false,
          "source_ingestion_authority": false,
          "web_search_authority": false,
          "weslr_io_authority": false
        },
        "domain_family_pair": [
          "wifi_sensing_indoor_propagation",
          "device_free_sensing_csi"
        ],
        "operator_review_required": true,
        "relation_type": "shared_constraint_model",
        "why_it_matters": "Metadata-only bridge between wifi_sensing_indoor_propagation and device_free_sensing_csi remains unresolved and should be owner reviewed."
      },
      {
        "bridge_id": "cdopd_bridge_639d9e665cef035f",
        "bridge_type": "cross_domain_transfer_candidate",
        "denied_authority_flags": {
          "agi_claim_authority": false,
          "all_authority_flags_false": true,
          "autonomous_routing_authority": false,
          "behavior_pack_promotion_authority": false,
          "benchmark_claim_authority": false,
          "boundary_notes": "cross-domain open-problem scout metadata-only boundary",
          "consciousness_claim_authority": false,
          "discovery_claim_authority": false,
          "evidence_status": "metadata_only_unverified",
          "external_action_authority": false,
          "final_answer_authority": false,
          "http_authority": false,
          "memory_mutation_authority": false,
          "metadata_only": true,
          "project_mutation_authority": false,
          "proof_claim_authority": false,
          "provider_model_authority": false,
          "public_claim_authority": false,
          "raw_retention_authority": false,
          "runtime_execution_authority": false,
          "sentience_claim_authority": false,
          "source_access_authority": false,
          "source_fetching_authority": false,
          "source_ingestion_authority": false,
          "web_search_authority": false,
          "weslr_io_authority": false
        },
        "domain_family_pair": [
          "wifi_sensing_indoor_propagation",
          "spatial_change_map_calibration"
        ],
        "operator_review_required": true,
        "relation_type": "shared_constraint_model",
        "why_it_matters": "Metadata-only bridge between wifi_sensing_indoor_propagation and spatial_change_map_calibration remains unresolved and should be owner reviewed."
      },
      {
        "bridge_id": "cdopd_bridge_9aaacdbdbcca77a0",
        "bridge_type": "cross_domain_transfer_candidate",
        "denied_authority_flags": {
          "agi_claim_authority": false,
          "all_authority_flags_false": true,
          "autonomous_routing_authority": false,
          "behavior_pack_promotion_authority": false,
          "benchmark_claim_authority": false,
          "boundary_notes": "cross-domain open-problem scout metadata-only boundary",
          "consciousness_claim_authority": false,
          "discovery_claim_authority": false,
          "evidence_status": "metadata_only_unverified",
          "external_action_authority": false,
          "final_answer_authority": false,
          "http_authority": false,
          "memory_mutation_authority": false,
          "metadata_only": true,
          "project_mutation_authority": false,
          "proof_claim_authority": false,
          "provider_model_authority": false,
          "public_claim_authority": false,
          "raw_retention_authority": false,
          "runtime_execution_authority": false,
          "sentience_claim_authority": false,
          "source_access_authority": false,
          "source_fetching_authority": false,
          "source_ingestion_authority": false,
          "web_search_authority": false,
          "weslr_io_authority": false
        },
        "domain_family_pair": [
          "rf_multipath_material_scattering",
          "floor_plan_topology_spatial_change"
        ],
        "operator_review_required": true,
        "relation_type": "shared_constraint_model",
        "why_it_matters": "Metadata-only bridge between rf_multipath_material_scattering and floor_plan_topology_spatial_change remains unresolved and should be owner reviewed."
      },
      {
        "bridge_id": "cdopd_bridge_efe22650c9209274",
        "bridge_type": "cross_domain_transfer_candidate",
        "denied_authority_flags": {
          "agi_claim_authority": false,
          "all_authority_flags_false": true,
          "autonomous_routing_authority": false,
          "behavior_pack_promotion_authority": false,
          "benchmark_claim_authority": false,
          "boundary_notes": "cross-domain open-problem scout metadata-only boundary",
          "consciousness_claim_authority": false,
          "discovery_claim_authority": false,
          "evidence_status": "metadata_only_unverified",
          "external_action_authority": false,
          "final_answer_authority": false,
          "http_authority": false,
          "memory_mutation_authority": false,
          "metadata_only": true,
          "project_mutation_authority": false,
          "proof_claim_authority": false,
          "provider_model_authority": false,
          "public_claim_authority": false,
          "raw_retention_authority": false,
          "runtime_execution_authority": false,
          "sentience_claim_authority": false,
          "source_access_authority": false,
          "source_fetching_authority": false,
          "source_ingestion_authority": false,
          "web_search_authority": false,
          "weslr_io_authority": false
        },
        "domain_family_pair": [
          "rf_multipath_material_scattering",
          "device_free_sensing_csi"
        ],
        "operator_review_required": true,
        "relation_type": "shared_constraint_model",
        "why_it_matters": "Metadata-only bridge between rf_multipath_material_scattering and device_free_sensing_csi remains unresolved and should be owner reviewed."
      },
      {
        "bridge_id": "cdopd_bridge_dcaee9c4ad430a95",
        "bridge_type": "cross_domain_transfer_candidate",
        "denied_authority_flags": {
          "agi_claim_authority": false,
          "all_authority_flags_false": true,
          "autonomous_routing_authority": false,
          "behavior_pack_promotion_authority": false,
          "benchmark_claim_authority": false,
          "boundary_notes": "cross-domain open-problem scout metadata-only boundary",
          "consciousness_claim_authority": false,
          "discovery_claim_authority": false,
          "evidence_status": "metadata_only_unverified",
          "external_action_authority": false,
          "final_answer_authority": false,
          "http_authority": false,
          "memory_mutation_authority": false,
          "metadata_only": true,
          "project_mutation_authority": false,
          "proof_claim_authority": false,
          "provider_model_authority": false,
          "public_claim_authority": false,
          "raw_retention_authority": false,
          "runtime_execution_authority": false,
          "sentience_claim_authority": false,
          "source_access_authority": false,
          "source_fetching_authority": false,
          "source_ingestion_authority": false,
          "web_search_authority": false,
          "weslr_io_authority": false
        },
        "domain_family_pair": [
          "rf_multipath_material_scattering",
          "spatial_change_map_calibration"
        ],
        "operator_review_required": true,
        "relation_type": "shared_constraint_model",
        "why_it_matters": "Metadata-only bridge between rf_multipath_material_scattering and spatial_change_map_calibration remains unresolved and should be owner reviewed."
      },
      {
        "bridge_id": "cdopd_bridge_e0c26acdd5e2822a",
        "bridge_type": "cross_domain_transfer_candidate",
        "denied_authority_flags": {
          "agi_claim_authority": false,
          "all_authority_flags_false": true,
          "autonomous_routing_authority": false,
          "behavior_pack_promotion_authority": false,
          "benchmark_claim_authority": false,
          "boundary_notes": "cross-domain open-problem scout metadata-only boundary",
          "consciousness_claim_authority": false,
          "discovery_claim_authority": false,
          "evidence_status": "metadata_only_unverified",
          "external_action_authority": false,
          "final_answer_authority": false,
          "http_authority": false,
          "memory_mutation_authority": false,
          "metadata_only": true,
          "project_mutation_authority": false,
          "proof_claim_authority": false,
          "provider_model_authority": false,
          "public_claim_authority": false,
          "raw_retention_authority": false,
          "runtime_execution_authority": false,
          "sentience_claim_authority": false,
          "source_access_authority": false,
          "source_fetching_authority": false,
          "source_ingestion_authority": false,
          "web_search_authority": false,
          "weslr_io_authority": false
        },
        "domain_family_pair": [
          "floor_plan_topology_spatial_change",
          "device_free_sensing_csi"
        ],
        "operator_review_required": true,
        "relation_type": "shared_constraint_model",
        "why_it_matters": "Metadata-only bridge between floor_plan_topology_spatial_change and device_free_sensing_csi remains unresolved and should be owner reviewed."
      },
      {
        "bridge_id": "cdopd_bridge_f79718358016a143",
        "bridge_type": "cross_domain_transfer_candidate",
        "denied_authority_flags": {
          "agi_claim_authority": false,
          "all_authority_flags_false": true,
          "autonomous_routing_authority": false,
          "behavior_pack_promotion_authority": false,
          "benchmark_claim_authority": false,
          "boundary_notes": "cross-domain open-problem scout metadata-only boundary",
          "consciousness_claim_authority": false,
          "discovery_claim_authority": false,
          "evidence_status": "metadata_only_unverified",
          "external_action_authority": false,
          "final_answer_authority": false,
          "http_authority": false,
          "memory_mutation_authority": false,
          "metadata_only": true,
          "project_mutation_authority": false,
          "proof_claim_authority": false,
          "provider_model_authority": false,
          "public_claim_authority": false,
          "raw_retention_authority": false,
          "runtime_execution_authority": false,
          "sentience_claim_authority": false,
          "source_access_authority": false,
          "source_fetching_authority": false,
          "source_ingestion_authority": false,
          "web_search_authority": false,
          "weslr_io_authority": false
        },
        "domain_family_pair": [
          "floor_plan_topology_spatial_change",
          "spatial_change_map_calibration"
        ],
        "operator_review_required": true,
        "relation_type": "shared_constraint_model",
        "why_it_matters": "Metadata-only bridge between floor_plan_topology_spatial_change and spatial_change_map_calibration remains unresolved and should be owner reviewed."
      },
      {
        "bridge_id": "cdopd_bridge_53a2df96c743b8d3",
        "bridge_type": "cross_domain_transfer_candidate",
        "denied_authority_flags": {
          "agi_claim_authority": false,
          "all_authority_flags_false": true,
          "autonomous_routing_authority": false,
          "behavior_pack_promotion_authority": false,
          "benchmark_claim_authority": false,
          "boundary_notes": "cross-domain open-problem scout metadata-only boundary",
          "consciousness_claim_authority": false,
          "discovery_claim_authority": false,
          "evidence_status": "metadata_only_unverified",
          "external_action_authority": false,
          "final_answer_authority": false,
          "http_authority": false,
          "memory_mutation_authority": false,
          "metadata_only": true,
          "project_mutation_authority": false,
          "proof_claim_authority": false,
          "provider_model_authority": false,
          "public_claim_authority": false,
          "raw_retention_authority": false,
          "runtime_execution_authority": false,
          "sentience_claim_authority": false,
          "source_access_authority": false,
          "source_fetching_authority": false,
          "source_ingestion_authority": false,
          "web_search_authority": false,
          "weslr_io_authority": false
        },
        "domain_family_pair": [
          "device_free_sensing_csi",
          "spatial_change_map_calibration"
        ],
        "operator_review_required": true,
        "relation_type": "shared_constraint_model",
        "why_it_matters": "Metadata-only bridge between device_free_sensing_csi and spatial_change_map_calibration remains unresolved and should be owner reviewed."
      }
    ],
    "contradiction_candidates": [],
    "denied_authority_flags": {
      "agi_claim_authority": false,
      "all_authority_flags_false": true,
      "autonomous_routing_authority": false,
      "behavior_pack_promotion_authority": false,
      "benchmark_claim_authority": false,
      "boundary_notes": "cross-domain open-problem scout metadata-only boundary",
      "consciousness_claim_authority": false,
      "discovery_claim_authority": false,
      "evidence_status": "metadata_only_unverified",
      "external_action_authority": false,
      "final_answer_authority": false,
      "http_authority": false,
      "memory_mutation_authority": false,
      "metadata_only": true,
      "project_mutation_authority": false,
      "proof_claim_authority": false,
      "provider_model_authority": false,
      "public_claim_authority": false,
      "raw_retention_authority": false,
      "runtime_execution_authority": false,
      "sentience_claim_authority": false,
      "source_access_authority": false,
      "source_fetching_authority": false,
      "source_ingestion_authority": false,
      "web_search_authority": false,
      "weslr_io_authority": false
    },
    "disconfirming_evidence_map": {
      "unknown_signal": [
        "A stronger bounded metadata signal would be needed before promotion"
      ]
    },
    "domain_families": [
      "wifi_sensing_indoor_propagation",
      "rf_multipath_material_scattering",
      "floor_plan_topology_spatial_change",
      "device_free_sensing_csi",
      "spatial_change_map_calibration"
    ],
    "input_references": [
      "mlcf_route_from_live_searxng_metadata_result_v1",
      "first_controlled_live_searxng_metadata_only_sample_v1",
      "weslr_first_controlled_live_searxng_metadata_only_boundary_v1"
    ],
    "input_signal_items": [],
    "limitation_future_work_candidates": [],
    "missing_evidence_map": {},
    "next_safe_step": "archive_low_value_signal",
    "open_problem_signal_candidates": [],
    "operator_review_need": "owner review required",
    "pressure_test_questions": [
      "What additional safe metadata would make this signal materially more specific?"
    ],
    "probe_suggestions": [
      "Consider archiving or repairing the weak signal before any later routing."
    ],
    "recommended_mlcf_route": "archive_low_value_signal",
    "safe_metadata_summary": {
      "candidate_count": 1,
      "domain_family_count": 5,
      "json_safe": true,
      "metadata_only": true,
      "no_claims": true,
      "no_evidence_elevation": true,
      "no_runtime_or_public_integration": true,
      "no_source_access": true,
      "no_source_fetching": true,
      "no_source_ingestion": true,
      "no_truth_elevation": true,
      "recommended_mlcf_route": "archive_low_value_signal"
    },
    "safety_boundary": {
      "metadata_only": true,
      "no_behavior_pack_promotion": true,
      "no_discovery_or_proof_claims": true,
      "no_memory_mutation": true,
      "no_model_provider_calls": true,
      "no_project_mutation": true,
      "no_public_claims": true,
      "no_raw_content_retention": true,
      "no_runtime_wiring": true,
      "no_source_access": true,
      "no_source_fetching": true,
      "no_source_ingestion": true,
      "no_web_calls": true,
      "no_weslr_io": true,
      "operator_review_required": true
    },
    "schema_version": "cross_domain_open_problem_scout_v1",
    "scout_id": "cdopd_scout_639c774e5dd344e1",
    "search_governance_mode": "metadata_only_owner_review",
    "source_classes_needed": [
      "official_standard",
      "public_benchmark_or_test_suite",
      "public_dataset",
      "public_lab_or_university_artifact",
      "public_research_paper"
    ],
    "unresolved_work_signal_candidates": [],
    "validation_status": {
      "blocked": true,
      "blocked_labels": [
        "missing_input_signal_items"
      ],
      "schema_version": "cross_domain_open_problem_scout_v1",
      "scout_id": "cdopd_scout_639c774e5dd344e1",
      "summary_text": "Blocked cross-domain open-problem scout packet.",
      "valid": false,
      "validation_posture": "blocked"
    }
  },
  "source_scout_packet_ref": "cdopd_scout_639c774e5dd344e1",
  "source_scout_summary": {
    "domain_family_count": 5,
    "next_safe_step": "archive_low_value_signal",
    "recommended_mlcf_route": "archive_low_value_signal",
    "schema_version": "cross_domain_open_problem_scout_v1",
    "scout_id": "cdopd_scout_639c774e5dd344e1",
    "signal_candidate_count": 0,
    "summary_text": "Scout cdopd_scout_639c774e5dd344e1: 5 domain families, 0 signal candidates, route=archive_low_value_signal.",
    "validation_posture": "blocked"
  },
  "source_selection_plan_payload_preview": {
    "disconfirming_evidence": {
      "unknown_signal": [
        "A stronger bounded metadata signal would be needed before promotion"
      ]
    },
    "domain_focus": "wifi_sensing_indoor_propagation, rf_multipath_material_scattering, floor_plan_topology_spatial_change, device_free_sensing_csi, spatial_change_map_calibration",
    "missing_evidence": {},
    "operator_review_need": "owner review required",
    "required_source_classes": [
      "official_standard",
      "public_benchmark_or_test_suite",
      "public_dataset",
      "public_lab_or_university_artifact",
      "public_research_paper"
    ],
    "science_direction_summary": "metadata_only_owner_review"
  },
  "validation_status": {
    "blocked": false,
    "blocked_labels": [],
    "schema_version": "weslr_cross_domain_scout_to_mlcf_integration_v1",
    "source_scout_validation_posture": "blocked",
    "summary_text": "Provisional cross-domain scout-to-MLCF integration packet.",
    "valid": true,
    "validation_posture": "valid"
  }
}
```

## Appendix E: candidate-preparation packet (JSON-safe, if produced)

```
Candidate-preparation packet was NOT produced.
Request validation:
{
  "blocked": true,
  "blocked_labels": [
    "unsafe_request_content",
    "invalid_integration_packet",
    "missing_candidate_preparation_id"
  ],
  "valid": false,
  "validation_posture": "blocked"
}
```

## Appendix F: run command (for reproducibility)

```bash
cd /home/pr0/projects/weslr-run-first-live-searxng-sample-20260613
export WESLR_SEARXNG_LIVE_BOUNDARY_ENABLED=true
export WESLR_SEARXNG_URL='http://127.0.0.1:8888'
export WESLR_SEARXNG_LIVE_BOUNDARY_TIMEOUT_SECONDS=5
export WESLR_SEARXNG_LIVE_BOUNDARY_MAX_RESULTS=5
export WESLR_SEARXNG_LIVE_BOUNDARY_SNIPPET_POLICY=disabled
export WESLR_SEARXNG_LIVE_BOUNDARY_QUERY_FAMILY=general
export WESLR_SEARXNG_LIVE_BOUNDARY_OPERATOR_ROLE=owner
python3 .run_controlled_nova_true_run_v1.py
```

The script is at `.run_controlled_nova_true_run_v1.py` in the worktree (operator-side scratch, untracked, not committed).
