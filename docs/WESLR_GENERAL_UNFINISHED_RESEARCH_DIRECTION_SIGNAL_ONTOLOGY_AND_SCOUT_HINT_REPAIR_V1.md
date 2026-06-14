# WESLR General Unfinished Research Direction Signal Ontology and Scout Hint Repair V1

**Date:** 2026-06-14
**Lane:** `DESIGN_WESLR_RF_WIFI_FLOORPLAN_SOURCE_CLASS_AND_SCOUT_SIGNAL_HINT_REPAIR_V1` (owner-supplied; the design's actual scope is broader than its name — see §3)
**Worktree:** `/home/pr0/projects/weslr-run-first-live-searxng-sample-20260613`
**Branch:** `run-first-live-searxng-sample-20260613`
**HEAD at start:** `2a910640`
**Status:** **Design-only.** No implementation. No code change. No new true run. No live SearXNG call. No web / provider / model call. No source content fetch / ingest. No `.weslr` IO. No runtime / chat / UI / voice edit. No accepted evidence. No accepted candidate. No proposal payload. No final answer. No discovery / proof / solved-theory / AGI / consciousness / sentience / benchmark / public-science / product-readiness claim.

---

## 1. Purpose

Design a **general, metadata-only signal ontology and scout-hint repair plan** so WESLR can detect *unfinished-research-direction* signals across many domains, while remaining **safe, skeptical, and non-claiming**.

The design generalizes the lesson from the WiFi / RF / floor-plan true run (a calibration case) and from the reviewer's gap analysis (3 scope gaps, 0 correctness gaps) into a domain-agnostic ontology of signal families, source classes, evidence roles, safety routes, candidate-preparation eligibility, extraordinary-claim handling, formal-unsolved-problem handling, cross-domain transfer handling, technology-blocked idea handling, dormant-direction handling, search-query generation, output packet shape, disconfirming-evidence requirements, operator-review requirements, and blocked routes. The design is **metadata-only** at every layer; no source content is fetched, ingested, or summarized.

This is a **design** artifact, not an implementation. Implementation is a separate lane requiring its own owner authorization.

---

## 2. Owner intent

The owner's stated goal (verbatim from the dispatch, §Goal): *"WESLR should be able to search across research papers, technical reports, patents, public datasets, standards, science directions, unresolved theories, failed or unfinished ideas, dormant proposals, underexplored cross-domain links, and old ideas that may have been abandoned because technology was not advanced enough, domains did not yet overlap, funding was missing, measurement was impossible, or assumptions were premature."*

Translated into design constraints:

- **Breadth:** the ontology must cover at least 8 distinct domains, not just RF / sensing.
- **Skepticism:** extraordinary / fringe / pseudoscience-class claims must be classified, not adopted.
- **Metadata-only:** the ontology must work without fetching source content; only metadata fields are retained.
- **Safety-by-design:** no acceptance, no promotion, no public claim, no provider call, no `.weslr` IO, no source ingestion, no run-time wiring.
- **Operator-controlled:** the ontology never elevates a locator to accepted evidence; the operator is the only promotion authority.
- **Generalization, not overfitting:** the ontology must not be tuned to any one domain's keyword bag; it must accept a domain family as a parameter and derive its keyword bag from a configurable map.

---

## 3. Why WiFi sensing is only a calibration case

The owner's dispatch is explicit: *"WiFi/RF/floor-plan sensing is only one calibration example. Do not overfit the architecture to WiFi sensing."*

The controlled Nova true run (`aab12606`) and its review (`2a910640`) found 3 scope gaps in the WiFi / RF / floor-plan topic specifically:

1. The boundary's `_derive_source_class` does not have keywords for `WiFi`, `RF`, `CSI`, `material scattering`, `floor-plan`, `multipath`, `indoor propagation`. 6 of 10 records fell back to `unknown_authority`.
2. The boundary's `OPEN_ACCESS_DOMAINS_V1` and `PAYWALLED_DOMAINS_V1` lists do not cover the WiFi / RF / floor-plan domain family. 5 of 10 records fell back to `unknown` access-license.
3. The scout's keyword-based signal derivation does not have markers for `RF multipath`, `WiFi sensing`, `floor-plan topology`, `material scattering`. 0 signals were derived.

The right fix is **not** "add `WiFi`, `RF`, `CSI`, `material scattering`, `floor-plan` to the keyword bags." That would re-create the same overfit at a higher level — the next true run on a different domain (say, "energy systems" or "biology / medicine") would find the same 3 gaps, with the new domain's keywords missing.

The right fix is **a domain-family as a parameter**: the boundary, the scout, and the integration layer each accept a `domain_family` parameter, and the per-domain-family keyword bags / source-class maps / signal-derivation rules live in a **domain-family registry** (a config file, not a code change). The WiFi / RF / floor-plan case becomes **one entry in that registry**, not the structure of the registry itself.

This is a generalization move, not a WiFi fix. The implementation of the registry is a separate lane.

---

## 4. Problem observed in the controlled Nova true run

From the review document `2a910640`, §13.3 (gaps and verdicts):

| Layer | State in the WiFi true run | Gap type |
|---|---|---|
| Boundary metadata capture | 10 records across 5 source classes, 8 domains, 19-field allow-list | No gap |
| Boundary invariants | 5 invariants held (raw content False, snippets False, truth-write False, evidence status metadata-only, authority verdict external-evidence-unverified) | No gap |
| Source-class hint map | 5/10 records fell back to `unknown_authority` (WiFi / RF / floor-plan keywords missing) | **Scope** gap |
| Access / license map | 5/10 records fell back to `unknown` (WiFi / RF / floor-plan domain list missing) | **List** gap |
| MLCF routing | `route_status: blocked`; `kept_locator_route_entries: 0`; per-row enum allow-list in `_validate_entry_fields` rejected all 10 records | **Enum-allow-list** gap |
| Scout | `signal_candidate_count: 0`; `recommended_mlcf_route: archive_low_value_signal`; keyword-based signal derivation produced 0 signals | **Scope** gap (downstream of the 0 kept entries, but also a per-domain keyword gap) |
| Integration | `selected_route: scout_blocked_by_safety`; `next_safe_step: blocked_by_safety` | Downstream safety verdict (correct) |
| Candidate-preparation | Not built; request rejected because integration's `selected_route` not in the allow-list | Correct safety verdict |
| Denied-authority flags | 25 flags all False; `all_authority_flags_false: True` | No gap |
| Public claims | None | No gap |
| Provider / model calls | None | No gap |
| `.weslr` IO | None | No gap |
| Source content fetch / ingest | None | No gap |
| Run-result file (the artifact being reviewed) | 1,929 lines, 28 sections, 6 appendices, full validation | No gap |
| Review document | 38,369 bytes, 17 sections, full 10-task validation | No gap |

The **0 correctness gaps, 0 authority gaps, 3 scope gaps** result is the input to this design. The design's job is to convert the 3 scope gaps from per-domain-specific to **domain-family-parameterized**, so that the next true run on any of the 8 owner-supplied example domains (RF / sensing, energy systems, materials, biology / medicine, mathematics, physics / quantum, AI / cognition, language / communication) does not hit the same 3 gaps, and so that future domains can be added by **registering a new domain-family entry**, not by editing the boundary / scout / integration / candidate-preparation modules.

---

## 5. Generalized unfinished-research signal ontology

The ontology is a **closed, finite** set of signal families. Each signal family has:

- A **closed enum** name (the `signal_type` value in the scout packet).
- A **closed enum** of **detection cues** — the textual patterns the keyword-based signal derivation looks for. **The cues are domain-family-parameterized, not hard-coded.** This is the key generalization move.
- A **closed enum** of **canonical follow-up actions** — what the next_safe_step should be for a signal of this type.
- A **closed enum** of **disconfirming-evidence classes** — the classes of evidence the operator should require before considering the signal more than a candidate.
- A **closed enum** of **extraordinary-claim flags** — whether the signal type is in the `extraordinary_claim_quarantine` allow-list.

### 5.1 Signal family taxonomy (8 families)

| # | Family | Detection cue (parameterized) | Follow-up | Disconfirming-evidence class | Extraordinary-claim flag |
|---|---|---|---|---|---|
| 1 | `unfinished_work_signal` | `future work`, `remains open`, `not fully understood`, `unresolved mechanism`, `open challenge`, `unsolved problem`, `further research needed`, `limited by current methods`, `no consensus`, `incomplete model`, `preliminary result` | `route_to_cross_domain_scout` | `replication_study_required`, `operator_review_required` | `False` |
| 2 | `technology_blocked_signal` | `abandoned because measurement was impossible`, `limited by sensors`, `limited by compute`, `limited by materials`, `limited by fabrication`, `limited by energy density`, `limited by data availability`, `limited by control systems`, `limited by simulation fidelity`, `may be revisitable with modern tools` | `route_to_cross_domain_scout` | `modern_re_measurement_required`, `operator_review_required` | `False` |
| 3 | `cross_domain_transfer_signal` | `similar structure in another domain`, `analogy not tested`, `method from one field not applied to another`, `old theory not revisited with modern instrumentation`, `mathematical structure shared across distant fields` | `route_to_cross_domain_scout` | `cross_domain_validation_required`, `operator_review_required` | `False` |
| 4 | `dormant_direction_signal` | `discontinued line of work`, `old patent with no follow-up`, `pilot study without continuation`, `early promising result with no replication`, `niche conference artifact`, `lab note / dataset without later exploitation`, `old method made obsolete then maybe newly relevant` | `route_to_source_selection_plan` | `recent_survey_required`, `operator_review_required` | `False` |
| 5 | `anomaly_signal` | `failed model`, `unexplained anomaly`, `contradiction between studies`, `replication gap`, `negative result`, `unexpected material behavior`, `unexpected biological response`, `unexplained measurement residual`, `theory–experiment mismatch` | `route_to_disconfirming_review` | `replication_study_required`, `independent_measurement_required`, `operator_review_required` | `False` |
| 6 | `measurement_benchmark_gap_signal` | `no benchmark`, `missing dataset`, `missing measurement`, `no controlled validation`, `no ground truth`, `hard to reproduce`, `sparse observations`, `no standardized protocol`, `lack of calibration` | `route_to_source_selection_plan` | `community_benchmark_required`, `operator_review_required` | `False` |
| 7 | `formal_unsolved_problem_signal` | `mathematical conjecture`, `open theorem`, `undecidable/unknown status`, `complexity-class uncertainty`, `unresolved physical theory`, `quantum interpretation / measurement gaps`, `hard optimization frontier`, `computational irreducibility`, `unsolved inverse problem` | `route_to_cross_domain_scout` | `formal_proof_status_check_required`, `operator_review_required` | `False` |
| 8 | `extraordinary_claim_signal` | `engine running on water`, `over-unity`, `free energy`, `reactionless drive`, `perpetual motion`, `cold fusion (claimed without independent replication)`, `unverified levitation`, `unverified faster-than-light claim`, `magnetic motor over-unity claim`, `unverified antigravity claim` | `route_to_extraordinary_claim_quarantine` | `thermodynamics_check_required`, `energy_conservation_check_required`, `peer_replication_required`, `legal_safety_check_required` | `True` (always) |

**All 8 families** are `metadata-only` by construction. The detection cues are textual patterns that the boundary's `_extract_metadata_text` function already retains; the cues are checked against the boundary's retained `title` + `url` + `domain` + `published_date` (and, when snippets are enabled, the `snippet`), but never against fetched source content. The detection cues are **keyword lists per family**, not single keywords; the keyword-list approach is robust to abbreviation and case variation.

**The 8th family is special**: it is the *skeptical* family. The `extraordinary_claim_signal` is **never** treated as a positive direction; it is treated as a quarantine class that requires stronger source classes, disconfirming checks, operator review, and explicit non-claim language. A locator that is classified as `extraordinary_claim_signal` is **not eligible** for candidate-preparation unless the operator explicitly promotes it after a full skeptical review. This is the design's principal defense against pseudoscience adoption.

### 5.2 Closed enum of `signal_type` values

The full set of values the scout may emit in `signal_candidates[].signal_type`:

```
unfinished_work_signal
technology_blocked_signal
cross_domain_transfer_signal
dormant_direction_signal
anomaly_signal
measurement_benchmark_gap_signal
formal_unsolved_problem_signal
extraordinary_claim_signal
```

Any other value must be rejected by the scout's request validator. This is a **closed enum**; no new value may be added without a design revision (a separate lane).

### 5.3 Domain-family registry (config, not code)

The 8 families' detection cues are stored in a **domain-family registry**, not in the scout module's source. The registry is a JSON / YAML / Python-dict file at a known path (e.g. `weslr/domain_family_registry_v1.json` — a separate lane may choose the actual path and format). Each entry has the shape:

```json
{
  "domain_family": "rf_sensing_indoor_propagation",
  "synonyms": ["wifi_sensing", "rf_localization", "csi_sensing", "indoor_propagation"],
  "signal_family_detection_cues": {
    "unfinished_work_signal": ["future work", "remains open", "multipath not fully characterized"],
    "technology_blocked_signal": ["limited by sensors", "limited by multipath modeling", "limited by floor-plan availability"],
    "cross_domain_transfer_signal": ["ultrasound analogy", "geophysics analogy"],
    "dormant_direction_signal": ["early CSI work without follow-up", "pre-2010 multipath modeling"],
    "anomaly_signal": ["unexpected material scattering deviation", "theory–experiment multipath mismatch"],
    "measurement_benchmark_gap_signal": ["no standardized multipath dataset", "no floor-plan-aware benchmark"],
    "formal_unsolved_problem_signal": ["unsolved inverse scattering problem", "open multipath decomposition conjecture"],
    "extraordinary_claim_signal": ["free-energy RF", "reactionless RF drive"]
  },
  "source_class_keywords": {
    "public research paper": ["arxiv", "doi.org", "ieee explore", "acm dl", "usenix"],
    "survey paper": ["survey", "review", "comprehensive", "taxonomy"],
    "benchmark paper": ["benchmark", "dataset", "challenge", "leaderboard", "evaluation"],
    "dataset record": ["dataset", "data release", "open data", "zenodo", "figshare", "kaggle", "huggingface"],
    "official standard": ["itu", "ieee standard", "iso", "3gpp", "etsi", "ieee 802"],
    "government / agency report": [".gov", "nist", "nasa", "nsf", "doe", "darpa", "darpa.mil"],
    "patent": ["patent", "uspto", "epo", "wipo", "patent number"],
    "thesis / dissertation": ["thesis", "dissertation", "phd", "master"],
    "lab / university artifact": ["lab", "university", ".edu", "research group"],
    "negative-result paper": ["negative result", "null result", "failed replication", "no significant effect"],
    "replication study": ["replication", "reproducibility", "replicate"],
    "preprint": ["preprint", "arxiv", "biorxiv", "chemrxiv", "psyarxiv", "research square"],
    "vendor technical documentation": ["specification", "datasheet", "whitepaper", "technical reference"],
    "code repository as implementation reference only": ["github.com", "gitlab", "bitbucket", "sourceforge"]
  },
  "open_access_domains": ["arxiv.org", "biorxiv.org", "chemrxiv.org", "psyarxiv.org", "zenodo.org", "plos.org", "frontiersin.org", "mdpi.com", "peerj.com", "ncbi.nlm.nih.gov", "europepmc.org", "researchgate.net (preprint only)", "github.com", "gitlab.com", ".gov", ".edu"],
  "paywalled_domains": ["nature.com", "sciencemag.org", "sciencedirect.com", "springer.com", "wiley.com", "ieee.org (xplore)", "acm.org (dl)", "cell.com", "thelancet.com", "nejm.org", "jama.jamanetwork.com", "pnas.org", "royalsocietypublishing.org"]
}
```

This is the **registry shape** for **one** domain family (the WiFi / RF / sensing example). The full registry has 8 such entries — one for each of the 8 owner-supplied example domains. **Adding a new domain family is a registry update, not a code change.** Adding a new detection cue for an existing domain family is also a registry update, not a code change.

This is the central generalization move. The WiFi fix becomes a **one-line registry entry update**, not a code revision. The next true run, the next reviewer, the next operator — they all read the registry, not the code.

---

## 6. Source-class expansion

The boundary's existing `source_class_hint` derivation is extended to a closed enum of 18 values (the owner-supplied set in dispatch §A, slightly reorganized):

```
public_research_paper
survey_paper
review_paper
benchmark_paper
dataset_record
official_standard
government_agency_report
patent
thesis_dissertation
lab_university_artifact
conference_workshop_artifact
negative_result_paper
replication_study
historical_archive
technical_report
preprint
vendor_technical_documentation
code_repository_as_implementation_reference
forum_blog_as_weak_signal
unknown_authority
```

All 18 values are in the **closed enum**; any other value must be rejected by the boundary's request validator. The boundary's `_derive_source_class` reads the **domain-family-specific keyword map** from the registry (§5.3) for the active `domain_family` parameter; it does not use a hard-coded keyword bag. The result is the boundary can detect, e.g., a `benchmark_paper` in the `rf_sensing_indoor_propagation` family by matching `["benchmark", "dataset", "challenge", "leaderboard", "evaluation"]` against the locator's `title` + `url` + `domain` (and optionally `snippet`).

The `unknown_authority` value is the **default fallback** for any locator that does not match any keyword in the active domain family's map. This is a **scope** classification, not a **verdict** — a locator with `source_class_hint: unknown_authority` is still a candidate locator; it just does not have a higher-confidence source-class assignment. The boundary's invariants (`automatic_truth_write: False`, `raw_content_retained: False`, etc.) hold regardless.

The 20-value enum replaces the boundary's current 12-or-so value set. **The boundary's `allowed_live_http_without_injected_getter` flag, timeout, snippet policy, and operator role are unchanged.** Only the `source_class_hint` derivation and the enum allow-list are extended.

### 6.1 Access / license map (extended)

The boundary's `OPEN_ACCESS_DOMAINS_V1` and `PAYWALLED_DOMAINS_V1` lists are extended to per-domain-family lists in the registry (§5.3). The boundary's `_derive_access_license_status` reads the active domain family's lists. The result is the boundary can detect, e.g., that `arxiv.org` is `open_access` and `sciencedirect.com` is `paywalled` in the `rf_sensing_indoor_propagation` family, and the same domains in the `materials` family would get the same `open_access` / `paywalled` assignments (because open-access-ness is a property of the domain, not the topic). The lists in the registry are **shared across domain families**; the boundary merges the active domain family's lists with the global lists and dedupes.

The default behavior (when the active domain family has no `open_access_domains` or `paywalled_domains` in the registry) is to use the global lists, which are the same as the boundary's current hard-coded lists. **No regression** for any existing domain.

---

## 7. Evidence-role expansion

The boundary's existing `evidence_role_guess` derivation is extended to a closed enum of 16 values (the owner-supplied set in dispatch §B):

```
candidate_signal
unfinished_work_signal
dormant_direction_signal
cross_domain_transfer_signal
technology_blocked_signal
anomaly_signal
contradiction_signal
replication_gap_signal
benchmark_gap_signal
measurement_gap_signal
extraordinary_claim_signal
implementation_reference_only
disconfirming_signal
official_constraint_signal
source_selection_needed
prior_art
```

All 16 values are in the **closed enum**; any other value must be rejected. The boundary's `_derive_evidence_role` is extended to a **per-domain-family + per-source-class** lookup: for the active `domain_family` and the locator's `source_class_hint`, the lookup returns a default `evidence_role_guess` (typically `candidate_signal` for the default `general` family; the per-domain-family registry can override). The 8 owner-supplied signal families are the **per-locator overrides**: if a locator's title / url / domain matches a domain-family-specific detection cue (per §5.1), the locator's `evidence_role_guess` becomes that signal type, e.g. `unfinished_work_signal`, `technology_blocked_signal`, `cross_domain_transfer_signal`, etc.

**The MLCF routing helper's `_validate_entry_fields` enum allow-list is also extended** to the full 16-value set, closing the gap that produced the WiFi / RF / floor-plan true run's `route_status: blocked`. The 4 source-class / evidence-role mismatches identified in the review (§13.3) are now resolved at the registry level — the boundary emits the right value, the route's enum allow-list contains the right value, and the chain proceeds.

This is **the central fix** the review pointed to. It is implemented as a **registry update + a one-line enum-allow-list extension in the route helper**, not as a code change to the boundary's core logic. The boundary's per-domain-family lookup is the only code change, and it is small (a single read from the registry).

---

## 8. Safety routing design

The integration helper's `selected_route` enum is extended to 8 values (the owner-supplied set in dispatch §C):

```
route_to_source_selection_plan
route_to_cross_domain_scout
route_to_candidate_preparation
route_to_operator_review
route_to_disconfirming_review
route_to_extraordinary_claim_quarantine
route_to_archive_low_value_signal
route_to_blocked_by_safety
```

The mapping from scout's `recommended_mlcf_route` to integration's `selected_route` is a **per-domain-family + per-signal-family** lookup. The default mapping (when no domain-family-specific override is in the registry) is:

| Scout's `recommended_mlcf_route` | Integration's `selected_route` |
|---|---|
| `prepare_source_selection_plan` | `route_to_source_selection_plan` |
| `prepare_metadata_only_source_locator_route` | `route_to_source_selection_plan` |
| `prepare_cross_domain_scout_to_mlcf_route` | `route_to_cross_domain_scout` |
| `prepare_disconfirming_review_route` | `route_to_disconfirming_review` |
| `prepare_extraordinary_claim_quarantine` | `route_to_extraordinary_claim_quarantine` |
| `archive_low_value_signal` | `route_to_archive_low_value_signal` |
| `blocked_by_safety` | `route_to_blocked_by_safety` |
| (any other) | `route_to_blocked_by_safety` (default safety) |

The candidate-preparation helper's `selected_route` allow-list is **only** `route_to_candidate_preparation`. Any other value (including `route_to_source_selection_plan`, `route_to_cross_domain_scout`, `route_to_disconfirming_review`, `route_to_extraordinary_claim_quarantine`, `route_to_archive_low_value_signal`, `route_to_blocked_by_safety`, `route_to_operator_review`) means **no candidate-preparation packet is built**. This is the existing safety verdict, extended.

`route_to_extraordinary_claim_quarantine` is **never eligible for candidate-preparation**; the candidate-preparation helper's `validate_request` returns `valid: False, blocked: True, blocked_labels: ["extraordinary_claim_route_not_eligible"]`. The integration packet's `selected_route: route_to_extraordinary_claim_quarantine` always routes to `route_to_blocked_by_safety` at the candidate-preparation boundary, even if the operator has manually forced the route.

This is the design's principal defense against pseudoscience promotion. A locator that the scout classified as `extraordinary_claim_signal` cannot be promoted to candidate-preparation by any path.

### 8.1 Operator-review-route

`route_to_operator_review` is a new route in the integration helper's enum. The integration helper selects this route when the scout has identified one or more signal candidates but the per-signal-family lookup returns `next_safe_step: route_to_operator_review` (e.g. for a `formal_unsolved_problem_signal` whose `formal_proof_status_check_required` disconfirming check is outstanding). The candidate-preparation helper rejects this route (not in the allow-list), but the integration packet is **retained** for the operator to inspect. The operator may then either: (a) write a new search query and run another true run, (b) write a new design for the operator-review packet, or (c) override the safety verdict manually (with a documented operator-side action). The default is (a) — operator writes a new search query.

### 8.2 Disconfirming-review-route

`route_to_disconfirming_review` is for signals that need a disconfirming-evidence plan before any further action. The integration helper's `safe_metadata_summary.disconfirming_evidence_required` becomes `True` for this route. The candidate-preparation helper rejects this route. The operator may write a new search query that includes disconfirming-evidence search terms (e.g. "replication gap", "failed replication", "negative result") and run another true run. The disconfirming-evidence requirements are enumerated in §17.

---

## 9. Candidate-preparation eligibility rules

A direction may become a candidate-preparation metadata packet **only if all** of the following hold (the owner-supplied set in dispatch §D, reorganized for clarity):

1. **At least one unfinished / dormant / open / measurement / cross-domain signal exists.** The candidate-preparation helper's `validate_request` checks the integration packet's `source_scout_packet.signal_candidates` for at least one entry whose `signal_type` is in `{unfinished_work_signal, technology_blocked_signal, cross_domain_transfer_signal, dormant_direction_signal, measurement_benchmark_gap_signal, formal_unsolved_problem_signal, anomaly_signal}`. **If zero signals, the request is rejected** with `blocked_labels: ["no_signal_candidates"]`.
2. **At least one source class is useful.** The candidate-preparation helper's `validate_request` checks the integration packet's `source_selection_plan_payload_preview.source_classes_needed` for at least one non-empty entry. **If empty, the request is rejected** with `blocked_labels: ["no_source_classes_needed"]`.
3. **Disconfirming evidence classes are identified.** The candidate-preparation helper's `validate_request` checks the integration packet's `disconfirming_evidence_map` for at least one entry per signal family. **If empty, the request is rejected** with `blocked_labels: ["no_disconfirming_evidence_map"]`.
4. **No public claim is made.** The candidate-preparation helper's `validate_request` scans the integration packet for any of `we are agi`, `agi achieved`, `consciousness confirmed`, `sentience confirmed`, `publicly claimable`, `we prove`, `we discover`, `we have shown`, `we have proven`, `official conclusion`, `final answer`, `state-of-the-art`, `state of the art`, `benchmark-winning`, `competition-winning`, `best in class`, `paradigm shift`, `proof`, `confirmed`, `verified`, `solved`, `accepted theory`. **If any match, the request is rejected** with `blocked_labels: ["public_claim_language_detected"]`.
5. **No accepted evidence is created.** The candidate-preparation helper's `validate_packet` checks the produced packet for any of `accepted: True`, `evidence_accepted: True`, `proposal_action: True`, `final_answer: True`. **If any match, the produced packet is rejected.**
6. **No source content is ingested.** The candidate-preparation helper's `validate_request` checks the integration packet's `safe_metadata_summary` for `no_source_access: True`, `no_source_fetching: True`, `no_source_ingestion: True`. **If any is False, the request is rejected** with `blocked_labels: ["source_content_ingestion_detected"]`.
7. **Operator review remains required.** The candidate-preparation helper's `validate_request` checks the integration packet's `operator_review_required: True`. **If False, the request is rejected** with `blocked_labels: ["operator_review_not_required"]`. **Operator review is never optional; it is the constant** that gates every promotion. Even if all 6 other rules pass, the operator must explicitly promote the candidate-preparation packet to the next stage.
8. **The integration packet's `selected_route` is `route_to_candidate_preparation`.** If any other route, the request is rejected with `blocked_labels: ["selected_route_not_eligible"]`.

If all 8 rules pass, the candidate-preparation packet is built. The packet's `preparation_status` is one of `candidate_preparation_built_with_operator_review`, `candidate_preparation_built_with_disconfirming_check`, `candidate_preparation_built_with_quarantine_marker` (the exact value depends on the signal family's extraordinary-claim flag, see §10). The packet's `candidate_readiness_label` is one of `metadata_candidate_ready`, `metadata_candidate_ready_with_disconfirming_check`, `metadata_candidate_quarantined`. The packet's `next_safe_step` is `route_to_operator_review` (the operator must explicitly promote).

---

## 10. Extraordinary-claim / pseudoscience handling

For extraordinary claims (the `extraordinary_claim_signal` family), the design imposes the following skeptical classifier (the owner-supplied set in dispatch §E, with the design's additions):

1. **Classify the locator as `extraordinary_claim_signal`.** The boundary's `_derive_evidence_role` returns `extraordinary_claim_signal` when the locator's title / url / domain matches any of the registry's `extraordinary_claim_signal` detection cues (e.g. `free energy`, `over-unity`, `reactionless drive`, `perpetual motion`, `cold fusion (claimed without independent replication)`, `unverified levitation`, `unverified faster-than-light claim`, `magnetic motor over-unity claim`, `unverified antigravity claim`).
2. **Require stronger source classes.** The candidate-preparation helper's `validate_request` requires the locator's `source_class_hint` to be in `{peer_reviewed_paper, official_standard, government_agency_report, replication_study}` (or, if the registry's `extraordinary_claim_signal` allow-list specifies a stricter set, that stricter set). **If the source class is in `{forum_blog, vendor_technical_documentation, code_repository, unknown_authority}`, the locator is rejected** with `blocked_labels: ["extraordinary_claim_insufficient_source_class"]`.
3. **Require thermodynamic / physical / legal / safety disconfirmation checks.** The candidate-preparation helper's `validate_request` requires the integration packet's `disconfirming_evidence_map` to include entries for: `thermodynamics_check_required`, `energy_conservation_check_required`, `peer_replication_required`, `legal_safety_check_required`. **If any of these is missing, the request is rejected** with `blocked_labels: ["extraordinary_claim_missing_disconfirming_check"]`.
4. **Block promotion.** The integration helper's `_route_analysis` selects `route_to_extraordinary_claim_quarantine` for any packet that contains one or more `extraordinary_claim_signal` entries. The candidate-preparation helper's `validate_request` rejects `route_to_extraordinary_claim_quarantine` with `blocked_labels: ["extraordinary_claim_route_not_eligible"]`. The candidate-preparation packet is **never built** for an extraordinary-claim signal.
5. **Block public claims.** The candidate-preparation helper's content-scan rule (rule 4 in §9) catches any positive claim language. For `extraordinary_claim_signal` entries, the threshold is even stricter: any of `we are agi`, `agi achieved`, `consciousness confirmed`, `sentience confirmed`, `publicly claimable`, `we prove`, `we discover`, `we have shown`, `we have proven`, `official conclusion`, `final answer`, `state-of-the-art`, `state of the art`, `benchmark-winning`, `competition-winning`, `best in class`, `paradigm shift`, `solved theory`, `new physics`, `over-unity verified`, `free energy demonstrated` causes immediate rejection. The threshold is `lowercase substring match` against the integration packet's text fields.
6. **Block accepted-candidate status.** The candidate-preparation helper's `validate_packet` checks for any of `accepted: True`, `evidence_accepted: True`, `proposal_action: True`, `final_answer: True` in the produced packet. **If any match, the packet is rejected.**
7. **Require operator review.** The candidate-preparation helper's `validate_request` requires `operator_review_required: True`. For `extraordinary_claim_signal` entries, the operator review must be **explicit** (the operator must type a confirmation token, e.g. `EXTRAORDINARY_CLAIM_REVIEW_CONFIRMED`, into the integration packet's `operator_review_confirmation_token` field; the helper's validator checks the token is present and correct). **If the token is missing or wrong, the request is rejected** with `blocked_labels: ["extraordinary_claim_operator_review_not_confirmed"]`. **This token requirement is the design's principal defense against operator-fatigue mistakes on extraordinary claims.**
8. **Preserve `unknown / likely false / needs evidence` language.** The candidate-preparation helper's `validate_packet` checks the produced packet for the presence of `unknown`, `likely false`, `needs evidence`, or `unverified` in the `summary` / `review` / `notes` fields. **If absent, the packet is rejected** with `blocked_labels: ["extraordinary_claim_summary_language_too_strong"]`. The default summary for an extraordinary-claim entry is `unverified claim; needs thermodynamic / physical / replication evidence; blocked from candidate preparation; operator review required; preserved as a known extraordinary-claim candidate signal; not a public claim`.

This is **a strictly skeptical classifier**. The `extraordinary_claim_signal` family is never a positive direction; it is always a quarantine class.

---

## 11. Formal unsolved-problem handling

For `formal_unsolved_problem_signal` entries (mathematical conjectures, open theorems, complexity-class uncertainty, quantum interpretation / measurement gaps, hard optimization frontiers, computational irreducibility, unsolved inverse problems), the design imposes:

1. **Classify the locator as `formal_unsolved_problem_signal`.** The boundary's `_derive_evidence_role` returns this value when the locator's title / url / domain matches any of the registry's `formal_unsolved_problem_signal` detection cues (e.g. `mathematical conjecture`, `open theorem`, `undecidable`, `complexity-class uncertainty`, `quantum interpretation`, `measurement gap`, `hard optimization`, `computational irreducibility`, `unsolved inverse problem`).
2. **Require the `formal_proof_status_check_required` disconfirming-evidence entry.** The candidate-preparation helper's `validate_request` requires the integration packet's `disconfirming_evidence_map` to include `formal_proof_status_check_required`. **If missing, the request is rejected** with `blocked_labels: ["formal_unsolved_problem_missing_proof_status_check"]`.
3. **Block the claim to a public "solved" verdict.** The candidate-preparation helper's content-scan rule (rule 4 in §9) catches any of `solved`, `proven`, `proved`, `resolved`, `conjecture resolved`, `theorem proven`, `theorem proved` for any field of the integration packet. **If any match, the request is rejected** with `blocked_labels: ["formal_unsolved_problem_claim_too_strong"]`. The default summary for a `formal_unsolved_problem_signal` entry is `formal open problem; status is unknown / open / undecidable; needs formal proof status check; blocked from candidate preparation; operator review required; preserved as a known open-problem candidate signal; not a public claim`.
4. **Default to `route_to_operator_review` or `route_to_cross_domain_scout`.** The integration helper's `_route_analysis` prefers these two routes for `formal_unsolved_problem_signal` entries, depending on whether the integration packet's `source_scout_packet.bridge_signals` is non-zero. The candidate-preparation helper's `validate_request` rejects both routes (neither is in the allow-list). The integration packet is **retained** for the operator to inspect.
5. **No `accepted` / `trusted` / `evidence-elevated` verdicts.** The candidate-preparation helper's `validate_packet` checks for any of `accepted: True`, `evidence_accepted: True`, `proposal_action: True`, `final_answer: True`. **If any match, the packet is rejected.**

This is the design's principal defense against "solved a millennium-prize problem" or "proved P ≠ NP" claims. The classifier treats the locator as a known open problem and refuses to elevate.

---

## 12. Cross-domain transfer handling

For `cross_domain_transfer_signal` entries (signal-processing idea applicable to biology / materials / cognition; physics / biology / control / information overlap; old theory not revisited with modern instrumentation; mathematical structure shared across distant fields), the design imposes:

1. **Classify the locator as `cross_domain_transfer_signal`.** The boundary's `_derive_evidence_role` returns this value when the locator's title / url / domain matches any of the registry's `cross_domain_transfer_signal` detection cues.
2. **Require `cross_domain_validation_required` disconfirming-evidence entry.** The candidate-preparation helper's `validate_request` requires the integration packet's `disconfirming_evidence_map` to include `cross_domain_validation_required`. **If missing, the request is rejected** with `blocked_labels: ["cross_domain_transfer_missing_validation"]`.
3. **Default to `route_to_cross_domain_scout`.** The integration helper's `_route_analysis` prefers this route for `cross_domain_transfer_signal` entries. The candidate-preparation helper's `validate_request` rejects this route (not in the allow-list). The integration packet is **retained** for the operator to inspect, and the next-lane (a new design for cross-domain transfer) is suggested.
4. **No "this works in another field" claim.** The candidate-preparation helper's content-scan rule catches any of `works in`, `applies to`, `transfers to`, `extends to`, `solves in another field`. **If any match, the request is rejected** with `blocked_labels: ["cross_domain_transfer_claim_too_strong"]`. The default summary is `cross-domain transfer candidate; needs independent validation in the target domain; not a public claim; operator review required`.
5. **Per-target-domain annotation.** The integration packet's `cross_domain_bridges` field is extended to enumerate the **target domain** and the **method** of the proposed transfer. The integration helper's `validate_packet` requires this annotation to be non-empty for any `cross_domain_transfer_signal` entry. **If empty, the request is rejected** with `blocked_labels: ["cross_domain_transfer_missing_target_annotation"]`.

This is the design's principal defense against "X method from physics works in biology without validation" or "this theory from control theory solves language without evidence" claims. The classifier requires explicit per-target-domain annotation and explicit independent-validation requirement.

---

## 13. Technology-blocked idea handling

For `technology_blocked_signal` entries (abandoned because measurement was impossible, limited by sensors / compute / materials / fabrication / energy density / data availability / control systems / simulation fidelity, may be revisitable with modern tools), the design imposes:

1. **Classify the locator as `technology_blocked_signal`.** The boundary's `_derive_evidence_role` returns this value when the locator's title / url / domain matches any of the registry's `technology_blocked_signal` detection cues.
2. **Require `modern_re_measurement_required` disconfirming-evidence entry.** The candidate-preparation helper's `validate_request` requires the integration packet's `disconfirming_evidence_map` to include `modern_re_measurement_required`. **If missing, the request is rejected** with `blocked_labels: ["technology_blocked_missing_re_measurement"]`.
3. **Default to `route_to_source_selection_plan` or `route_to_cross_domain_scout`.** The integration helper's `_route_analysis` prefers these routes for `technology_blocked_signal` entries, depending on whether the locator's title mentions a specific successor technology. The candidate-preparation helper's `validate_request` rejects both routes. The integration packet is **retained** for the operator to inspect.
4. **No "the original was correct" claim.** The candidate-preparation helper's content-scan rule catches any of `the original was correct`, `was right all along`, `now confirmed`, `validated by modern tools`, `re-measured and confirmed`. **If any match, the request is rejected** with `blocked_labels: ["technology_blocked_claim_too_strong"]`. The default summary is `technology-blocked idea candidate; needs modern re-measurement; not a public claim; operator review required`.
5. **No "now solved" claim.** The candidate-preparation helper's content-scan rule also catches `now solved`, `resolves with modern tools`, `resolves with modern sensors`, `resolves with modern compute`. **If any match, the request is rejected** with the same `blocked_labels`.

This is the design's principal defense against "X was solved in 1970 by Y but ignored" or "Z was ahead of its time and is now confirmed" claims without independent re-measurement.

---

## 14. Dormant / abandoned direction handling

For `dormant_direction_signal` entries (discontinued line of work, old patents with no follow-up, pilot study without continuation, early promising result with no replication, niche conference artifact, lab note / dataset without later exploitation, old method made obsolete then maybe newly relevant), the design imposes:

1. **Classify the locator as `dormant_direction_signal`.** The boundary's `_derive_evidence_role` returns this value when the locator's title / url / domain matches any of the registry's `dormant_direction_signal` detection cues.
2. **Require `recent_survey_required` disconfirming-evidence entry.** The candidate-preparation helper's `validate_request` requires the integration packet's `disconfirming_evidence_map` to include `recent_survey_required`. **If missing, the request is rejected** with `blocked_labels: ["dormant_direction_missing_recent_survey"]`.
3. **Default to `route_to_source_selection_plan`.** The integration helper's `_route_analysis` prefers this route for `dormant_direction_signal` entries. The candidate-preparation helper's `validate_request` rejects this route. The integration packet is **retained** for the operator to inspect.
4. **No "recent re-discovery" claim.** The candidate-preparation helper's content-scan rule catches any of `recently rediscovered`, `newly relevant`, `has modern relevance`, `now useful again`, `revival`, `reborn`. **If any match, the request is rejected** with `blocked_labels: ["dormant_direction_claim_too_strong"]`. The default summary is `dormant direction candidate; needs recent survey and recent citation analysis; not a public claim; operator review required`.
5. **Per-locator citation-count check.** The integration helper's `_route_analysis` for `dormant_direction_signal` entries requires the locator's metadata to include a `citation_count` field (which the boundary does not retain, so the helper's validator marks this as a missing field; the registry is the source of truth for the per-domain-family citation-count fallback). **If the citation count cannot be derived, the request is rejected** with `blocked_labels: ["dormant_direction_missing_citation_evidence"]`. The fallback is `unknown; treat as uncited; surface in the operator-review packet`.

This is the design's principal defense against "X is having a renaissance" or "Y is being rediscovered" claims without a recent citation / survey analysis.

---

## 15. Search-query generation strategy

The owner-supplied set in dispatch §F gives 8 example query patterns. The design generalizes these into a **query-template registry** keyed by `query_family`:

```
unfinished_research: ["{signal_type_keyword} {domain_family_keyword}", "future work {domain_family_keyword}", "remains open {domain_family_keyword}", "unsolved {domain_family_keyword}", "open problem {domain_family_keyword}", "open challenge {domain_family_keyword}"]
dormant_direction: ["old abandoned {domain_family_keyword}", "discontinued {domain_family_keyword}", "early promising {domain_family_keyword} no replication", "pilot study {domain_family_keyword} without continuation", "old patent {domain_family_keyword} no follow-up"]
cross_domain: ["cross-domain analogy {domain_a_keyword} {domain_b_keyword}", "old theory {domain_a_keyword} modern instrumentation", "method from {domain_a_keyword} applied to {domain_b_keyword}", "shared mathematical structure {domain_a_keyword} {domain_b_keyword}"]
technology_blocked: ["abandoned because measurement impossible {domain_family_keyword}", "limited by {constraint} {domain_family_keyword}", "may be revisitable with modern {technology} {domain_family_keyword}"]
anomaly: ["unexplained anomaly {domain_family_keyword}", "failed model {domain_family_keyword}", "replication gap {domain_family_keyword}", "negative result {domain_family_keyword}"]
measurement_benchmark: ["no benchmark {domain_family_keyword}", "missing dataset {domain_family_keyword}", "missing measurement {domain_family_keyword}", "sparse observations {domain_family_keyword}"]
formal_unsolved: ["open theorem {domain_family_keyword}", "mathematical conjecture {domain_family_keyword}", "undecidable {domain_family_keyword}", "complexity-class uncertainty {domain_family_keyword}", "unsolved inverse problem {domain_family_keyword}"]
extraordinary_claim: ["free energy {domain_family_keyword}", "over-unity {domain_family_keyword}", "reactionless drive {domain_family_keyword}", "perpetual motion {domain_family_keyword}"]
```

Each query template uses `{domain_family_keyword}` and `{domain_a_keyword}` / `{domain_b_keyword}` / `{signal_type_keyword}` / `{constraint}` / `{technology}` as placeholders. The owner supplies the placeholders at the time of the run.

The owner supplies the **per-run search-query set** at run time. The maximum is 3 queries per true run, per the prior lane's run constraint. The minimum is 1 query. The default is 1 query of each of the 8 query families (8 queries total) — but the prior lane's spec is 3 queries, so the design honors 3 queries by default and allows the owner to specify the per-run query set as a list of `(query_family, query_string)` tuples. **The owner can override any query family to none, or specify a custom query family not in the registry; the registry is a starting point, not a constraint.**

**The query is metadata-only by construction.** The query is a text string sent to SearXNG; SearXNG returns a structured JSON response; the boundary retains the 19-field per-row allow-list; the scout, integration, and candidate-preparation helpers retain only metadata. No source content is fetched.

### 15.1 Per-domain-family search-query defaults

The 8 owner-supplied example domains (RF / sensing, energy systems, materials, biology / medicine, mathematics, physics / quantum, AI / cognition, language / communication) each have a **default query set** in the registry. The default for `rf_sensing_indoor_propagation` is the 3 queries from the prior lane (WiFi sensing indoor multipath material scattering, RF indoor propagation material surface scattering, WiFi CSI device free sensing). The defaults for the other 7 domains are in the registry and may be overridden by the owner at run time.

---

## 16. Metadata-only output packet design

After a future true run, WESLR produces the following packets (per the owner-supplied set in dispatch §G):

1. **Metadata locator packet** — the boundary's structured return, with the 19-field per-row allow-list, the safety invariants, the JSON-safe copy. The packet's `evidence_status` is `metadata_only_locator_candidates`, the `authority_verdict` is `external_evidence_unverified`, the `automatic_truth_write` is `False`, the `raw_content_retained` is `False`, the `snippets_retained` is `False`. The packet is a **locator packet**, not an evidence packet.
2. **Source-class summary** — a list of `source_class_hint` values and their counts, derived from the boundary's per-row `source_class_hint` field. The summary is **metadata-only**; no source content is summarized.
3. **Unfinished-signal summary** — a list of `signal_type` values, the detection cues that fired, the per-signal `next_safe_step`, the disconfirming-evidence class required. The summary is **metadata-only**; no signal text is extracted from sources.
4. **Dormant-direction candidates** — a sub-list of the unfinished-signal summary, restricted to `dormant_direction_signal` entries. The candidates are **locator candidates**, not promoted candidates.
5. **Disconfirming-evidence plan** — a list of disconfirming-evidence classes that the operator should require before promoting each signal type. The plan is **metadata-only**; no disconfirming evidence is fetched (that would be source content).
6. **Source-selection plan** — a list of `source_class_needed` values, the domain-family-specific source-class keyword map, the open-access / paywalled lists. The plan is **metadata-only**; no sources are selected beyond the boundary's per-row allow-list.
7. **Candidate-preparation packet (if eligible)** — built by the candidate-preparation helper per §9 eligibility rules. The packet is the **only** packet that can be promoted; all other packets are **retained for operator review** but **not promotable**. The packet's `preparation_status` is one of the 3 allowed values per §9; the packet's `candidate_readiness_label` is one of the 3 allowed values per §9; the packet's `next_safe_step` is `route_to_operator_review`. The packet's `denied_authority_flags` are all `False`.
8. **Operator-review packet** — the integration packet, retained for the operator. The operator may inspect, may write a new search query, may write a new design, or may override the safety verdict with a documented operator-side action (e.g. explicit promotion with a `OPERATOR_REVIEW_CONFIRMED` token for non-extraordinary claims, or `EXTRAORDINARY_CLAIM_REVIEW_CONFIRMED` for extraordinary claims).

**No packet contains source content. No packet contains evidence. No packet contains a public claim. No packet contains a provider / model call. No packet contains `.weslr` IO. No packet contains runtime / chat / UI / voice wiring.**

---

## 17. Disconfirming-evidence requirements

The integration packet's `disconfirming_evidence_map` is the operator's contract for what evidence to require before promoting a signal. The design's full list of disconfirming-evidence classes (each is a closed enum value):

```
replication_study_required
independent_measurement_required
community_benchmark_required
modern_re_measurement_required
recent_survey_required
cross_domain_validation_required
formal_proof_status_check_required
peer_replication_required
legal_safety_check_required
thermodynamics_check_required
energy_conservation_check_required
operator_review_required
```

Each signal family requires at least one of these classes (per the per-family table in §5.1, the per-family table in §10 for extraordinary claims, the per-family table in §11 for formal unsolved problems, the per-family table in §12 for cross-domain transfer, the per-family table in §13 for technology-blocked ideas, the per-family table in §14 for dormant directions). The candidate-preparation helper's `validate_request` requires at least one class per signal family, and a **different** class for each signal family in the same integration packet (so a packet with 2 different signal families requires 2 different disconfirming-evidence classes).

The default for each signal family is documented in §5.1. The operator may override the default at run time by editing the integration packet's `disconfirming_evidence_map` before the candidate-preparation packet is built. **The override is the operator's** — the helper does not second-guess the operator. **The override must still be a value from the closed enum**; non-enum values are rejected.

---

## 18. Operator-review requirements

The integration packet's `operator_review_required: True` is **always** set, by the integration helper, for any packet. **There is no path that bypasses operator review.** The candidate-preparation helper's `validate_request` rejects any packet that does not have `operator_review_required: True`. The boundary's invariants do not include `operator_review_required: True` (the boundary does not produce a packet that is operator-review-required; it produces a metadata locator packet that is operator-review-required by default). The scout's `operator_review_need: owner review required` is the default. The integration helper's `safe_metadata_summary.operator_review_required: True` is the default. The candidate-preparation helper's `safe_metadata_summary.operator_review_required: True` is the default. **Every packet in the chain is operator-review-required.**

For `extraordinary_claim_signal` entries, the operator review must be **explicit** — the operator must type `EXTRAORDINARY_CLAIM_REVIEW_CONFIRMED` into the integration packet's `operator_review_confirmation_token` field. For non-extraordinary claims, the operator review is implicit — the operator just inspects the packet, the next-safe-step is `route_to_operator_review`, and the operator may write a new search query or a new design.

The operator-review process is **explicit, documented, and enforced**. **No packet can be promoted to evidence / accepted-candidate / proposal / final-answer without the operator's explicit review and promotion.**

---

## 19. Blocked routes

The integration helper's `selected_route` enum is closed (per §8). The candidate-preparation helper's `selected_route` allow-list is **only** `route_to_candidate_preparation`. The following routes are **explicitly blocked** from candidate-preparation:

- `route_to_source_selection_plan` — block via `selected_route_not_eligible`.
- `route_to_cross_domain_scout` — block via `selected_route_not_eligible`.
- `route_to_operator_review` — block via `selected_route_not_eligible`.
- `route_to_disconfirming_review` — block via `selected_route_not_eligible`.
- `route_to_extraordinary_claim_quarantine` — block via `extraordinary_claim_route_not_eligible` (additional rule for the `extraordinary_claim_signal` family).
- `route_to_archive_low_value_signal` — block via `selected_route_not_eligible`.
- `route_to_blocked_by_safety` — block via `selected_route_not_eligible`.

**A packet that selects any of these 6 routes does not become a candidate-preparation packet. The packet is retained for the operator to inspect, and the next-safe-step is `route_to_operator_review` (or one of the other 5 routes).**

---

## 20. Examples across 8 domains

For each of the 8 owner-supplied example domains, this section gives a **concrete search-query set, the expected source classes, the expected signal families, the disconfirming-evidence classes, and the operator's next step.** These are **illustrative** — the registry is the source of truth, and the owner may override any of these at run time.

### 20.1 RF / sensing (`rf_sensing_indoor_propagation`)

**Search queries (3 of 3):**
1. `WiFi sensing indoor multipath material scattering floor plan localization`
2. `RF indoor propagation material surface scattering floor plan dataset`
3. `WiFi CSI device free sensing floor plan multipath benchmark`

**Expected source classes:** `public_research_paper`, `benchmark_paper`, `dataset_record`, `official_standard`, `government_agency_report`, `code_repository_as_implementation_reference`.

**Expected signal families:** `unfinished_work_signal`, `technology_blocked_signal`, `cross_domain_transfer_signal`, `anomaly_signal`, `measurement_benchmark_gap_signal`.

**Disconfirming-evidence classes required:** `replication_study_required`, `modern_re_measurement_required`, `cross_domain_validation_required`, `community_benchmark_required`, `independent_measurement_required`.

**Operator's next step:** `route_to_cross_domain_scout` (default) or `route_to_source_selection_plan` if a specific dataset or paper is identified.

### 20.2 Energy systems (`energy_systems_storage_conversion`)

**Search queries (3 of 3):**
1. `battery energy storage capacity fade mechanism unresolved future work`
2. `thermodynamic cycle efficiency limit abandoned re-measured modern sensors`
3. `power grid frequency stability anomaly measurement gap open data`

**Expected source classes:** `public_research_paper`, `official_standard` (IEEE, IEC), `government_agency_report` (DOE, NREL), `patent`, `dataset_record`, `historical_archive`.

**Expected signal families:** `unfinished_work_signal`, `technology_blocked_signal`, `anomaly_signal`, `measurement_benchmark_gap_signal`, `formal_unsolved_problem_signal` (e.g. unsolved inverse problem for capacity fade).

**Disconfirming-evidence classes required:** `replication_study_required`, `modern_re_measurement_required`, `thermodynamics_check_required`, `legal_safety_check_required` (for any claim about energy density / safety).

**Operator's next step:** `route_to_source_selection_plan` (default) or `route_to_cross_domain_scout` if the signal mentions a cross-domain transfer.

### 20.3 Materials (`materials_mechanics_soft_matter`)

**Search queries (3 of 3):**
1. `metallic glass plastic deformation mechanism unresolved`
2. `soft matter active matter self-organization future work open problem`
3. `material fatigue crack propagation unexplained anomaly negative result`

**Expected source classes:** `public_research_paper`, `thesis_dissertation`, `lab_university_artifact`, `preprint`, `negative_result_paper`.

**Expected signal families:** `unfinished_work_signal`, `anomaly_signal`, `contradiction_signal`, `dormant_direction_signal`, `formal_unsolved_problem_signal`.

**Disconfirming-evidence classes required:** `replication_study_required`, `independent_measurement_required`, `modern_re_measurement_required`.

**Operator's next step:** `route_to_cross_domain_scout` (default) or `route_to_source_selection_plan` if a specific dataset is identified.

### 20.4 Biology / medicine (`biology_medicine_translational`)

**Search queries (3 of 3):**
1. `drug target off-target effect mechanism unresolved future work`
2. `biomarker reproducibility replication crisis negative result`
3. `gene expression dataset missing standardized protocol`

**Expected source classes:** `public_research_paper`, `preprint` (bioRxiv, medRxiv), `replication_study`, `negative_result_paper`, `dataset_record`, `official_standard` (FDA, EMA guidance documents).

**Expected signal families:** `unfinished_work_signal`, `anomaly_signal`, `replication_gap_signal`, `measurement_benchmark_gap_signal`, `contradiction_signal`.

**Disconfirming-evidence classes required:** `replication_study_required` (mandatory), `independent_measurement_required`, `peer_replication_required`, `legal_safety_check_required` (for any drug / clinical claim).

**Operator's next step:** `route_to_source_selection_plan` (default) or `route_to_cross_domain_scout` if a cross-domain transfer is identified. The candidate-preparation helper's `validate_request` requires `legal_safety_check_required` for any biology / medicine signal that mentions a drug, a biomarker, a clinical trial, or a patient outcome.

### 20.5 Mathematics (`mathematics_foundations_unsolved`)

**Search queries (3 of 3):**
1. `open mathematical conjecture theorem undecidable complexity class`
2. `unsolved inverse problem computational irreducibility hard optimization`
3. `recent partial result famous conjecture proof attempt failed`

**Expected source classes:** `public_research_paper`, `preprint` (arXiv), `thesis_dissertation`, `historical_archive`, `survey_paper`.

**Expected signal families:** `formal_unsolved_problem_signal` (mandatory), `unfinished_work_signal`, `anomaly_signal` (for failed proof attempts).

**Disconfirming-evidence classes required:** `formal_proof_status_check_required` (mandatory), `peer_replication_required`.

**Operator's next step:** `route_to_operator_review` (default; the operator decides whether to write a new search query or a new design). The candidate-preparation helper's `validate_request` requires `formal_proof_status_check_required` for any mathematics signal. **The default summary is `formal open problem; status is unknown / open / undecidable; needs formal proof status check; blocked from candidate preparation; operator review required; preserved as a known open-problem candidate signal; not a public claim`.**

### 20.6 Physics / quantum (`physics_quantum_foundations`)

**Search queries (3 of 3):**
1. `quantum measurement problem interpretation open question unsolved`
2. `quantum gravity approach unification abandoned revisited modern tools`
3. `high-energy physics anomaly unexplained measurement residual`

**Expected source classes:** `public_research_paper`, `preprint` (arXiv), `official_standard` (CODATA, PDG), `historical_archive`, `survey_paper`, `conference_workshop_artifact`.

**Expected signal families:** `formal_unsolved_problem_signal`, `unfinished_work_signal`, `technology_blocked_signal`, `anomaly_signal`, `dormant_direction_signal`.

**Disconfirming-evidence classes required:** `formal_proof_status_check_required`, `modern_re_measurement_required`, `peer_replication_required`.

**Operator's next step:** `route_to_operator_review` (default; physics / quantum claims are sensitive). The candidate-preparation helper's `validate_request` requires `formal_proof_status_check_required` for any physics / quantum signal that mentions a measurement problem, a unification, or a foundational claim. **The default summary is `formal open problem or measurement anomaly; status is unknown / open / needs independent replication; blocked from candidate preparation; operator review required; not a public claim`.**

### 20.7 AI / cognition (`ai_cognition_unsupervised`)

**Search queries (3 of 3):**
1. `unsupervised learning sample efficiency theory gap future work`
2. `reasoning benchmark gap evaluation failure mode replication`
3. `neural architecture search abandoned revisited modern hardware`

**Expected source classes:** `public_research_paper`, `preprint` (arXiv), `benchmark_paper`, `code_repository_as_implementation_reference`, `negative_result_paper`, `replication_study`.

**Expected signal families:** `unfinished_work_signal`, `measurement_benchmark_gap_signal`, `replication_gap_signal`, `anomaly_signal`, `technology_blocked_signal`, `dormant_direction_signal`.

**Disconfirming-evidence classes required:** `replication_study_required`, `community_benchmark_required`, `modern_re_measurement_required`, `operator_review_required` (mandatory for any AGI / consciousness / sentience claim).

**Operator's next step:** `route_to_source_selection_plan` (default) or `route_to_disconfirming_review` for any failed-benchmark signal. The candidate-preparation helper's `validate_request` requires `operator_review_required` for any AI / cognition signal that mentions AGI, consciousness, sentience, public-readiness, benchmark-winning, or any of the forbidden claim language. **The default summary is `unfinished or anomalous result in AI / cognition; needs replication and benchmark validation; blocked from candidate preparation unless source classes and disconfirming checks are explicit; operator review required; not a public claim`.**

### 20.8 Language / communication (`language_communication_evolution`)

**Search queries (3 of 3):**
1. `language evolution origin unsolved mechanism future work`
2. `historical text corpus missing benchmark standardization`
3. `translation low-resource language abandoned revisited modern multilingual models`

**Expected source classes:** `public_research_paper`, `preprint` (arXiv, ACL anthology), `historical_archive`, `thesis_dissertation`, `survey_paper`, `dataset_record`, `code_repository_as_implementation_reference`.

**Expected signal families:** `unfinished_work_signal`, `technology_blocked_signal`, `cross_domain_transfer_signal`, `measurement_benchmark_gap_signal`, `dormant_direction_signal`, `formal_unsolved_problem_signal` (e.g. unsolved complexity of language evolution).

**Disconfirming-evidence classes required:** `replication_study_required`, `recent_survey_required`, `cross_domain_validation_required`, `community_benchmark_required`.

**Operator's next step:** `route_to_source_selection_plan` (default) or `route_to_cross_domain_scout` if a cross-domain transfer (e.g. cognitive science to NLP) is identified.

---

## 21. Explicit non-claims

The design explicitly does **NOT** claim:

- AGI, consciousness, sentience, general intelligence, or any cognitive capability.
- Discovery, proof, solved theory, breakthrough, milestone, or any epistemic upgrade.
- Public-science readiness, benchmark-winning, competition-winning, state-of-the-art, or any competitive result.
- Product readiness, deployment readiness, customer readiness, or any commercial claim.
- "First to detect", "first to discover", "first to rediscover", "newly relevant", or any recency claim.
- "Solved a millennium-prize problem", "proved P ≠ NP", "solved the quantum measurement problem", or any specific open-problem claim.
- "Free energy verified", "over-unity confirmed", "reactionless drive demonstrated", or any extraordinary-claim verification.
- Cross-domain transfer working without independent validation in the target domain.
- Recent re-discovery of a dormant direction without a recent citation / survey analysis.
- A direction is "candidate-preparation ready" without the operator's explicit review and promotion.

The design's output is **metadata-only**, **operator-review-required**, **safety-by-default**, and **skeptical-by-default** for extraordinary claims. The design is **a metadata-locator ontology and a safety classifier**, not a discovery engine or a knowledge engine.

---

## 22. Boundaries

The design is bounded by:

- **Metadata-only**: no source content is fetched, ingested, summarized, paraphrased, or hashed. The boundary's 19-field per-row allow-list is the maximum retained content.
- **Loopback-only**: SearXNG is local-only (loopback). No non-loopback URL.
- **No provider / model call**: no LLM, no Ollama, no OpenAI, no Anthropic, no Gemini, no OpenRouter, no model provider, no simulated provider.
- **No `.weslr` IO**: no read, no write, no config-touch of `/home/pr0/.weslr/`.
- **No runtime / chat / UI / voice wiring**: no call to the omnichat contract-reply engine, the chat responder, the chat UI, the dialogue module, the main module, the LLM runtime, the protected chat backend on `:8092`, the public `weslr.de` site, the protected chat `chat.weslr.de`.
- **No public claims**: no public-readiness, AGI, consciousness, sentience, proof, discovery, official benchmark, competition-winning, or public-science claim.
- **No destructive operations**: no file delete, no worktree create/delete, no branch create/delete, no reset, no rebase, no merge, no stash, no force push, no destructive git operation.
- **No cron-fired / autonomous-fired**: no cron, no systemd timer, no heartbeat, no growth session, no morning session, no evening session, no autonomous run, no scheduled work, no outreach, no email pipeline, no social / business lane, no Telegram outbound, no public WebSocket.
- **Design-only in this lane**: no code change in this lane. The registry, the per-domain-family keyword bags, the per-source-class allow-list extension, the per-evidence-role enum allow-list extension in the MLCF routing helper, and the per-route allow-list extension in the candidate-preparation helper are all **implementation work**, deferred to a separate lane.

---

## 23. Implementation plan

The implementation is a separate lane requiring its own owner authorization. The plan, in order:

1. **Create the domain-family registry** as a config file at a known path (e.g. `weslr/domain_family_registry_v1.json`). The initial registry has 8 entries, one per owner-supplied example domain (§20). Each entry has the shape in §5.3. The registry is **versioned** (filename ends in `_v1`).
2. **Update the boundary's `_derive_source_class`** to read the active domain family's `source_class_keywords` from the registry. The boundary's `source_class_hint` derivation becomes **per-domain-family**, not hard-coded.
3. **Update the boundary's `_derive_access_license_status`** to read the active domain family's `open_access_domains` and `paywalled_domains` from the registry. The lists are merged with the global lists (the boundary's existing hard-coded defaults).
4. **Update the boundary's `_derive_evidence_role`** to read the active domain family's `signal_family_detection_cues` from the registry. The derivation becomes **per-domain-family + per-source-class + per-locator**. The 16-value enum is the new allow-list.
5. **Update the MLCF routing helper's `_validate_entry_fields`** to accept the full 16-value `evidence_role_guess` enum. The current allow-list is extended; the new values are `unfinished_work_signal`, `dormant_direction_signal`, `cross_domain_transfer_signal`, `technology_blocked_signal`, `anomaly_signal`, `contradiction_signal`, `replication_gap_signal`, `benchmark_gap_signal`, `measurement_gap_signal`, `extraordinary_claim_signal`, `implementation_reference_only`, `disconfirming_signal`, `official_constraint_signal`, `source_selection_needed`, `prior_art`. The existing `candidate_signal` value is retained.
6. **Update the integration helper's `_route_analysis`** to handle the 8-route enum. The mapping is per the table in §8.
7. **Update the candidate-preparation helper's `validate_request`** to enforce the 8 eligibility rules from §9 and the 5 extraordinary-claim rules from §10.
8. **Update the integration helper's `safe_metadata_summary`** to include `disconfirming_evidence_required: bool` and the per-signal `disconfirming_evidence_class` list.
9. **Add the `operator_review_confirmation_token`** field to the integration packet. The candidate-preparation helper's `validate_request` checks the token is present and correct for `extraordinary_claim_signal` entries.
10. **Add a `--domain-family` CLI flag** to all 4 helper modules (boundary, scout, integration, candidate-preparation). The flag's default is `general` (no domain-family-specific keyword map; falls back to the global keyword map; the behavior is identical to the current behavior for any domain family that has no registry entry). The flag's value is any of the 8 owner-supplied example domains or a future custom domain family that the operator registers.
11. **Add unit tests** for the per-domain-family derivations and the per-signal-family rules. The tests live in the existing `weslr/tests/` directories.
12. **Add a registry validator** that checks the JSON file is well-formed, that all enum values are in the closed sets, and that the keyword lists are non-empty for the active domain family. The validator is a separate module (e.g. `weslr/domain_family_registry_validator.py`).
13. **Update the release gate** to require an exact-file allowance for any new doc file (design, review, run-result, run-review) that lives at the top-level `docs/` path. The current gate already has 6+ such allowances; the pattern is established.
14. **Add a "true run with new domain family" lane** that exercises the design on a non-WiFi domain (e.g. energy systems or mathematics) to verify the registry-driven approach generalizes.

The implementation is **6 + 1 = 7 + 1 = 8 weeks of work** (estimate, not a commitment). Each step is a separate commit on a separate branch, with its own owner authorization.

---

## 24. Validation plan

The design itself (this document) is validated by the same 8-command validation suite the prior lane ran:

1. `git diff --check` — exit 0
2. `python3 weslr/tests/release_gate_v1.py` — `WESLR_RELEASE_GATE_V1_OK` (after the gate edit for the design doc)
3. `bash scripts/weslr_release_check.sh` — `WESLR_RELEASE_CHECK_OK` + `SELF_TEST: PASS`
4. The 4 pytest invocations (boundary, scout, integration, candidate-preparation) — **151 tests pass** (unchanged from the prior lane, since the design does not implement code)
5. The 4 protected files (md5 byte-identical to `origin/master`)

The design's **claims** are validated by the implementation lane (separate), not by this lane. The implementation lane will:
- Run a true run on each of the 8 example domains.
- Verify the registry produces the expected `source_class_hint`, `access_license_status_guess`, `evidence_role_guess` for each example query set.
- Verify the integration helper's `_route_analysis` produces the expected `selected_route` for each example signal family.
- Verify the candidate-preparation helper's `validate_request` produces the expected `blocked_labels` for each disallowed condition.
- Verify the extraordinary-claim classifier produces the expected `quarantined` status for the 4-5 known extraordinary-claim examples.
- Verify the operator-review-confirmation-token mechanism blocks unauthenticated promotion.

---

## 25. Next recommended lane

**`REVIEW_WESLR_GENERAL_UNFINISHED_RESEARCH_DIRECTION_SIGNAL_ONTOLOGY_AND_SCOUT_HINT_REPAIR_V1`** (owner-supplied)

The owner reviews this design document, then decides whether to authorize the implementation plan in §23 as one large lane or as 14 small lanes. The implementation is a non-trivial change to 4 helper modules and the introduction of a new config file; it should be a single coordinated lane or a small set of well-scoped sub-lanes, each with its own owner authorization and its own boundary.

If the owner chooses not to authorize the implementation, the next lane is `PUSH_WESLR_RF_WIFI_FLOORPLAN_DESIGN_AND_REVIEW_BRANCH_TO_GITHUB` — a no-op push of the current branch to the remote for archival review. The owner did not authorize pushing in the current dispatch; this is offered as a possible next-lane option, not a recommendation to push without authorization.

---

## 26. Final judgment

**`general_unfinished_research_signal_ontology_design_ready_for_review`**

Reasoning:
- The design is **general** (8 example domains, 8 signal families, per-domain-family registry), not overfit to WiFi sensing.
- The design is **metadata-only** (no source content fetch / ingest / summary / hash; the boundary's 19-field per-row allow-list is the maximum retained content).
- The design is **safe-by-default** (every packet is operator-review-required; the candidate-preparation helper's `validate_request` enforces 8 eligibility rules + 5 extraordinary-claim rules; the chain's 6 routes other than `route_to_candidate_preparation` are blocked from candidate-preparation).
- The design is **skeptical-by-default for extraordinary claims** (the `extraordinary_claim_signal` family is always quarantined; the operator must type `EXTRAORDINARY_CLAIM_REVIEW_CONFIRMED` to override; the default summary uses `unknown / likely false / needs evidence` language).
- The design is **non-claiming** (no AGI, consciousness, sentience, proof, discovery, official benchmark, competition-winning, public-science, or product-readiness claim).
- The design honors all the owner's pre-conditions: no implementation, no new true run, no live SearXNG, no web / provider / model call, no `.weslr` IO, no runtime / chat / UI / voice edit, no accepted evidence, no accepted candidate, no proposal payload, no final answer.
- The design is **complete** (26 sections, all 17 owner-supplied requirements addressed, 8 example domains with concrete search-query sets and expected source classes / signal families / disconfirming-evidence classes).
- The design's pre-conditions are met: preflight passed (repo root, branch, HEAD, 0 modified tracked files, no in-progress merge/rebase/cherry-pick), 4 protected files are byte-identical to `origin/master`, `weslr/main.py` is N/A.

The design is ready for the owner's review. Implementation is a separate lane.
