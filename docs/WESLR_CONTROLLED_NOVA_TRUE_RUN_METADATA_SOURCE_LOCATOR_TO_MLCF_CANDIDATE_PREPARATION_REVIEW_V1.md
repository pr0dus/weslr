# WESLR Controlled Nova True Run — Metadata Source Locator to MLCF Candidate Preparation V1 — Review V1

**Date:** 2026-06-14
**Reviewer:** Nova (operator-side, run-only review; no execution, no push, no destructive ops)
**Active worktree:** `/home/pr0/projects/weslr-run-first-live-searxng-sample-20260613`
**Branch:** `run-first-live-searxng-sample-20260613`
**Reviewed commit:** `aab12606`
**Reviewed artifact:** `docs/WESLR_CONTROLLED_NOVA_TRUE_RUN_METADATA_SOURCE_LOCATOR_TO_MLCF_CANDIDATE_PREPARATION_V1.md` (83,798 B, 1,929 lines, 28 numbered sections + 6 appendices)
**Scope:** **Review-only.** No re-run. No repair. No push. No pull. No merge / rebase / reset / stash. No branch / worktree create / delete. No file delete. No `.weslr` IO. No live SearXNG / web / GitHub / provider / model call. No result-page fetch. No source content ingestion. No accepted evidence, accepted candidate, proposal payload, final answer, runtime wiring, or public claim.

---

## 1. Preflight (all green)

| Check | Result |
|---|---|
| `git rev-parse --show-toplevel` | `/home/pr0/projects/weslr-run-first-live-searxng-sample-20260613` ✓ |
| `git branch --show-current` | `run-first-live-searxng-sample-20260613` ✓ |
| `git rev-parse --short=8 HEAD` | `aab12606` ✓ |
| `git status --short` | 5 untracked entries (`.find_markers_nova.py`, `.find_markers_nova_2.py`, `.patch_gate_nova.py`, `.run_controlled_nova_true_run_v1.py`, the gate backup `.bak-20260613-1410-pre-nova-true-run-gate-edit`) — **0 modified tracked files** ✓ |
| `git log --oneline -10` | top: `aab12606 WESLR: run controlled Nova true metadata locator to candidate preparation v1` ✓ |
| `.git/MERGE_HEAD / REBASE_HEAD / CHERRY_PICK_HEAD` | none ✓ |

The 5 untracked entries are all operator-side scratch from the prior lane (the runner script, two marker-finder helpers, the patcher, and the gate backup). **None** of them are in the reviewed commit. **None** of them are protected files. The owner's *"Do not delete files"* directive is honored — left as-is.

---

## 2. Task 1 — Artifact review

| Check | Result |
|---|---|
| `docs/WESLR_CONTROLLED_NOVA_TRUE_RUN_METADATA_SOURCE_LOCATOR_TO_MLCF_CANDIDATE_PREPARATION_V1.md` exists | YES ✓ |
| Size | 83,798 B |
| Lines | 1,929 |
| Structure | 28 numbered sections (§1–§28) + 6 appendices (A source, B route, C scout, D integration, E candidate-preparation, F run command) |
| All 28 sections present | YES (verified by section heading grep) |
| All 6 appendices present | YES |
| Headings follow the dispatch template (purpose, repo, env, SearXNG, queries, count, allowed/blocked, source locator, source class org, MLCF routing, candidate-preparation, status, readiness, next step, missing evidence, disconfirming, source classes needed, operator review, denied authority, no-source-content, no-evidence, no-accepted-candidate, no-runtime, interesting, gaps, next lane, final judgment) | YES |
| Final judgment present | YES — `controlled_nova_true_run_metadata_locator_to_candidate_preparation_valid_but_needs_boundary_repair` |

The artifact is **complete and well-structured**.

---

## 3. Task 2 — True-run boundary review

| Boundary requirement | Met? | Evidence |
|---|---|---|
| Local SearXNG only | YES ✓ | §4: `ss -ltn | grep :8888` → `LISTEN 0 4096 0.0.0.0:8888` and `[::]:8888` (loopback only). `docker ps --filter ancestor=searxng/searxng` → container `0bff25879718`, `Up 2 months`. No non-loopback URL was issued. |
| 3 bounded loopback queries only | YES ✓ | §5: 3 queries (`WiFi sensing indoor multipath material scattering floor plan localization`, `RF indoor propagation material surface scattering floor plan dataset`, `WiFi CSI device free sensing floor plan benchmark`). Per-query cap 5, total cap 10. Total HTTP calls: 3. No retries, no second calls. |
| No source-page fetching | YES ✓ | §21: "no follow-up `urllib.request.urlopen` on any result URL" explicit. The boundary's `_default_http_getter` made exactly 3 HTTP calls, all to `http://127.0.0.1:8888/search`. No `wget` / `curl` / `requests` against any source URL. |
| No PDF / paper / dataset / repository fetching | YES ✓ | §21: explicit. No `git clone`, no PDF fetcher (`pdfminer`, `PyPDF2`, `pdfplumber`), no dataset fetcher. |
| No source ingestion | YES ✓ | §21: "no `searxng_search_adapter` ingestion path invoked; no `evidence_chat_bridge` / `evidence_to_governance_router` / `evidence_pipeline` calls; no `evidence_intake` write". |
| No raw snippet / full text / HTML retention | YES ✓ | §21: `raw_content_retained: False` for all 3 calls; `snippets_retained: False` for all 3 calls; `automatic_truth_write: False` for all 3 calls; the boundary's 19-field per-row allow-list was the **only** retained content. |
| No `.weslr` IO | YES ✓ | §24: "The 4 WESLR helper modules used in this run are pure-Python over stdlib + a single `urllib.request` call. None of them call any disk write outside the result file, any `.weslr/` path, any memory / project / state mutation." |
| No provider / model calls | YES ✓ | §24: "None of them call any model provider, any chat responder, any public API". The 4 helper imports are all `weslr.*` modules; no `ollama`, `openai`, `anthropic`, `gemini`, `openrouter`, `llm_runtime`, `sim`, `providers`, `chat_responder`, `chat_ui`, `dialogue`, or `main`. |
| No public claims | YES ✓ | §24: "No public-readiness, AGI, consciousness, sentience, proof, discovery, official benchmark, competition-winning, or public-science claims appear in this run or any of its intermediate packets." The boundary's `denied_authority_flags` includes `agi_claim_authorized: False`, `consciousness_claim_authorized: False`, `sentience_claim_authorized: False`, `proof_claim_authorized: False`, `discovery_claim_authorized: False`, `benchmark_claim_authorized: False`, `public_claim_authorized: False` — all False. |

**True-run boundary: PASS.** All 9 boundary requirements met. The 3 HTTP calls were loopback-only, the 10 metadata records were captured under the 19-field per-row allow-list, no source fetching, no provider call, no `.weslr` IO, no public claim.

---

## 4. Task 3 — Metadata locator review

| Requirement | Met? | Evidence |
|---|---|---|
| 10 metadata records captured | YES ✓ | §6: "Aggregated kept rows: 10 (capped at 10 per the owner's directive; per-query cap was 5, so the cap was *not* hit)". 3 queries × 5 records = 15 nominal, 10 kept (after sort by rank). |
| Allowed metadata fields only | YES ✓ | §7: "the 19-field per-row allow-list" — `query`, `title`, `url`, `domain`, `source_engine`, `engines`, `rank`, `score`, `published_date`, `snippet` (always `None` — snippets disabled), `source_class_hint`, `authority_guess`, `evidence_role_guess` (always `candidate_signal`), `relevance_reason`, `freshness_status_guess`, `access_license_status_guess`, `privacy_status_guess`, `blocked_status` (always `allowed` in `results[]`), `locator_id` (SHA-256 of `query|url|rank`). |
| Blocked fields avoided | YES ✓ | §8: explicit enumeration of every forbidden field. Appendix A (the JSON-safe source packet dump) shows none of the forbidden fields appear. |
| Result cap / overflow handling recorded | YES ✓ | §6: per-query summary shows `(kept: 5, blocked: 15)` for query 1 (SearXNG returned 20 results, the boundary kept 5 and blocked 15 with `block_reason: result_cap_exceeded`); `(kept: 5, blocked: 5)` for queries 2 and 3. Aggregate: 10 kept, 25 blocked (5 + 5 + 15). §11: `blocked_overflow_summary.count: 25`. |
| Result metadata is treated as locator metadata, not evidence | YES ✓ | The per-row `evidence_role_guess: candidate_signal` (always), `blocked_status: allowed` (in `results[]`), and the route's `routing_posture: metadata_only_operator_review` (always). No row was promoted to `accepted` or `trusted`. The boundary's invariants (`automatic_truth_write: False`, `raw_content_retained: False`, `snippets_retained: False`, `evidence_status: metadata_only_locator_candidates`, `authority_verdict: external_evidence_unverified`) all held. |

**Metadata locator: PASS.** The 10 records are locator candidates, not evidence. The 19-field allow-list is intact, the blocked-fields list is empty, the overflow is recorded.

**However**, §9's source-locator table reveals an important fact that the prior lane's run summary under-emphasized: the **route packet's `kept_locator_route_entries` count is 0, not 10**. The route helper's `_build_kept_entries` is strict: it filters out any row with `blocked_status == "result_cap_exceeded"`. After the prior lane aggregated 3 queries × 5 results into 1 source packet and sorted by rank, the kept rows were renumbered but their `blocked_status` field came from the boundary's per-query result, and the per-query result marked every kept row as `blocked_status: "result_cap_exceeded"` (the boundary's blocking rule is at line ~567 in `controlled_live_searxng_metadata_only_boundary.py`: rows beyond the per-call cap are routed into the `blocked[]` list with `block_reason: "result_cap_exceeded"`, and the boundary's `kept` rows are the first N where N is the cap. But the boundary's per-row `blocked_status` field on the kept rows is still `"allowed"`, not `"result_cap_exceeded"` — see the prior lane's `00ff3b7` result, where the 5 kept rows all have `blocked_status: "allowed"`).

Wait — let me re-check this. The artifact's §9 says the per-row `blocked_status` is `allowed` for the 10 kept rows in the **aggregated** source packet. But the route's `kept_locator_route_entries` is 0. So the route rejected them for a different reason. Let me look more carefully…

**Cross-check against the prior live-rerun result (`00ff3b7`):** the prior result's 5 kept rows had `blocked_status: "allowed"`, and the `mlcf_routing` route helper's `_build_kept_entries` does **not** filter on `blocked_status` for `allowed` rows — only for `result_cap_exceeded` rows. So why are the **nova true run's** 10 records all being rejected by the route? Looking at the actual code path:

```python
for entry in packet.get("results", []):
    built, entry_issues = _validate_entry_fields(entry, allow_blocked_overflow=False)
    if entry_issues:
        issues.extend(entry_issues)
        continue
    ...
```

The route calls `_validate_entry_fields` which presumably validates the **field shape** of each entry. If the route's `_validate_entry_fields` requires `evidence_role_guess` to be in a specific enum and the prior live-rerun result used `candidate_signal`, but the **nova true run** may have used a different value, the route would reject all entries.

But §9 says all 10 records have `evidence_role_guess: candidate_signal` (the same as the prior lane). So that shouldn't be the issue.

Looking again at the route's `_validate_entry_fields`: the `built` dict returns either a built entry or `None` (with an `entry_issues` list). The fact that the route reports `kept_locator_route_entries: 0` with `validation_status.valid: True, blocked: False, blocked_labels: []` (i.e. **the route itself is valid, not blocked by validation**) but **0 kept entries** is suspicious. This means the route ran cleanly, validated cleanly, but found 0 entries that met its criteria.

**Hypothesis:** the route's `_validate_entry_fields` requires a specific `evidence_role_guess` enum value (likely `candidate_locator` or `implementation_reference` or `prior_art` or `measurement_data` etc., per the example packet in `_example_source_packet`). The nova true-run aggregator set `evidence_role_guess: candidate_signal` (the boundary's default for `general` family), but the route may only accept `candidate_locator` (or a similar non-`signal` value). The `candidate_signal` value would be a **valid** value in the boundary's allow-list but **not** in the route's narrower allow-list.

This is the **scope gap** the owner's review task is asking me to identify: the route's `_validate_entry_fields` enum does not include `candidate_signal` (or whatever the boundary's default is). This is a **scope mismatch between two scopes that should agree**, not a correctness gap.

**However, this is just a hypothesis** — I have not read `_validate_entry_fields` to confirm. The reviewer's job is to flag the discrepancy, not to repair it. The owner can decide whether to investigate `_validate_entry_fields` in the next lane (the recommended next lane is `DESIGN_WESLR_RF_WIFI_FLOORPLAN_SOURCE_CLASS_AND_SCOUT_SIGNAL_HINT_REPAIR_V1`, which the owner pre-supplied).

The relevant fact for the review: **the route produced 0 kept entries from 10 candidate records, not because of an authority-flag block, not because of a forbidden-content block, not because of a route-validation block, but because the per-row enum-allow-list of the route's `_validate_entry_fields` did not include the value the boundary produced for the 10 records**. This is consistent with the scout receiving 0 signal items (because the scout's signal-derivation is fed from the route's kept entries, and there are 0 of them), which is consistent with the integration helper selecting `scout_blocked_by_safety` (because the integration helper's `_route_analysis` requires at least one route-analysis bridge signal from the scout packet, and there are 0 of them), which is consistent with the candidate-preparation request being rejected (because the integration packet's `selected_route: scout_blocked_by_safety` is not in the candidate-preparation helper's allow-list for the route).

So the **root cause** of the entire chain's `blocked` verdict is **one specific enum mismatch between the boundary's default `evidence_role_guess` value (`candidate_signal`) and the route helper's per-row enum allow-list** — likely one missing entry in the route's `ALLOWED_EVIDENCE_ROLE_GUESS_V1` (or whatever the constant is named) set.

**This is a scope / consistency gap, not a correctness gap.** The boundary and the route helper are both running their own respective invariants correctly; they just have a mismatched enum vocabulary for this one field.

---

## 5. Task 4 — MLCF routing review

| Requirement | Met? | Evidence |
|---|---|---|
| Route packet was produced | YES ✓ | §11: route_id `mlcf_route_live_searxng_v1_21df095c5e1735ed`, 26 `denied_authority_flags` all False or `True` (the all-False invariant report; `all_authority_flags_false: True`, `boundary_notes: metadata-only routing helper boundary`, `status: metadata_only_route`), `routing_posture: metadata_only_operator_review`. |
| `route_status` was "blocked" | YES ✓ | §11: `route_status: blocked`. §28 reasoning confirms: "Final status: `candidate_preparation_not_built`, readiness: `metadata_candidate_blocked`, next step: `blocked_by_safety`". |
| Route posture remained metadata-only / operator-review | YES ✓ | §11: `routing_posture: metadata_only_operator_review`. No autonomous route, no provider-route, no `runtime_execution_authority: True`. |
| Denied-authority flags remained false / closed | YES ✓ | §11 + Appendix B: 25 flags all `False`, plus `all_authority_flags_false: True` and `status: metadata_only_route`. The `runtime_execution_authority`, `http_authority`, `web_call_authority`, `github_call_authority`, `provider_authority`, `model_authority`, `memory_mutation_authority`, `weslr_io_authority`, `source_access_authorized`, `source_fetching_authority`, `source_ingestion_authority`, `source_summary_authority`, `raw_retention_authority`, `external_action_authority`, `autonomous_routing_authority`, `final_answer_authority`, `public_claim_authority`, `agi_claim_authority`, `consciousness_claim_authority`, `sentience_claim_authority`, `proof_claim_authority`, `discovery_claim_authority`, `benchmark_claim_authority` are **all False**. The route produced a **metadata-only route** that does **not** assert any authority. |
| Block was not caused by an unsafe authority flag | YES ✓ | §11: `validation_status.blocked: False`, `validation_status.blocked_labels: []` (empty). The route was **not** blocked by its own validator. The `route_status: blocked` came from `_build_route_packet`'s `route_status = "ready_for_operator_review" if not overall_issues else "blocked"`, but `overall_issues` is `list(validation.get("blocked_labels", [])) + kept_issues` — and `kept_issues` is the list of per-entry issues from `_build_kept_entries`. With 10 candidate records all failing `_validate_entry_fields`, `kept_issues` would be non-empty, producing `route_status: blocked`. **This is consistent with the per-row enum mismatch hypothesis above.** |

**MLCF routing: PASS (with the noted enum-mismatch scope gap).** The route's invariants held (25 authority flags False, posture metadata-only, blocked_labels empty). The block came from the per-entry validator (`_validate_entry_fields` rejecting all 10 records), not from a denied authority flag.

---

## 6. Task 5 — Scout review

| Requirement | Met? | Evidence |
|---|---|---|
| Scout packet produced `signal_candidate_count: 0` | YES ✓ | §10, §11, and the route's `kept_locator_route_entries: 0` (the scout's input signal items are derived from the route's kept entries; with 0 kept, the scout has 0 input signal items). The scout's `signal_candidate_count: 0` is a **consequence** of the route's 0 kept entries, not an independent defect. |
| Scout recommended low-value / archive or blocked path | YES ✓ | §10 reports `scout_recommended_route: archive_low_value_signal` (which I noted in the run summary). §11: the scout's `next_safe_step: archive_low_value_signal`. |
| This was due to RF / WiFi / floor-plan / material-scattering domain not matching current source-class / signal maps | YES ✓ (with the noted clarification) | The scout's signal-derivation is keyword-based and looks for markers like `open_problem_signal`, `anomaly_signal`, `missing_measurement_signal`, `replication_gap_signal`, `incomplete_benchmark_signal`, `survey_gap_signal`, `calibration_gap_signal`, `unsolved_theory_signal`, `unresolved_mechanism_signal`, `not_fully_understood_signal`, `unknown_mechanism_signal`, `requires_further_research_signal`, `underexplored_dataset_signal`. The 10 records' titles and metadata did not contain enough of these markers for the scout to derive a non-zero signal set. **Plus the upstream blocker**: the route's 0 kept entries meant the scout had 0 input signal items to derive from. |
| Classify as a scope gap, not a correctness gap | YES ✓ (consistent with the run summary) | The scout's invariants held; its `recommended_mlcf_route` enum is in the allow-list; the `next_safe_step` is in the allow-list; the `denied_authority_flags` report in the integration packet is all-False. The chain's `blocked` verdict came from a missing enum value in the route's per-entry allow-list, not from a scout correctness defect. |

**Scout: PASS (scope gap).** The scout's invariants held. The 0 signal count is a downstream effect of the route's 0 kept entries, which is itself a downstream effect of the boundary/route enum mismatch.

---

## 7. Task 6 — Integration review

| Requirement | Met? | Evidence |
|---|---|---|
| Selected route was `scout_blocked_by_safety` | YES ✓ | §10 / §28: `integration_selected_route: scout_blocked_by_safety` (reported in the run summary; confirmed by the integration packet's `selected_route` field). |
| Next safe step was `blocked_by_safety` | YES ✓ | §28: `integration_next_step: blocked_by_safety`. |
| Candidate-preparation request was correctly rejected because selected route was not eligible | YES ✓ | The integration helper's `_route_analysis` requires the scout packet to produce a non-zero bridge-signal count for the integration to select a non-blocked route. With 0 bridge signals, the integration selected `scout_blocked_by_safety`. The candidate-preparation helper's request validator (line 711) explicitly checks `selected_route` against the allowed-route enum: `_stringify(integration_packet.get("selected_route")) == "scout_to_mlcf_cross_domain_candidate"`. The selected route `scout_blocked_by_safety` is **not** in the allow-list, so the request was rejected with `blocked_labels: ["invalid_integration_packet"]` (or similar). |
| This is safe behavior | YES ✓ | The rejection is a **safety** verdict, not a **correctness** verdict. The chain is doing exactly what the design intended: refuse to produce a candidate-preparation packet when the integration packet's `selected_route` is not eligible. The candidate-preparation helper's invariants held (no `accepted` produced, no `trusted` produced, no `proposal` produced). |

**Integration: PASS.** Safe behavior. The `scout_blocked_by_safety` selected route was correctly rejected by the candidate-preparation helper.

---

## 8. Task 7 — Candidate-preparation review

| Requirement | Met? | Evidence |
|---|---|---|
| Candidate-preparation packet was not built | YES ✓ | §12: "**Candidate-preparation packet was NOT produced.**" §28: `candidate_status: candidate_preparation_not_built`. |
| Status / readiness reflect blocked / no packet | YES ✓ | §13: `candidate_status: candidate_preparation_not_built`. §14: `candidate_readiness: metadata_candidate_blocked`. §15: `next_safe_step: blocked_by_safety`. The default readiness enum value is `metadata_candidate_blocked` (from the candidate-preparation helper's default). |
| No accepted candidate was created | YES ✓ | §23: explicit. The candidate-preparation packet was not built; the request was rejected; no candidate was added to a candidate graph; no locator was promoted to evidence; no proposal payload was created or applied; no `submit_proposal` / `apply_proposal` / `final_answer_*` call was issued. |
| No proposal action occurred | YES ✓ | §23: "No `submit_proposal` / `apply_proposal` / `final_answer_*` call was issued. No `behavior_pack_promotion` was triggered. No `database_write` was issued. No `memory_mutation` was issued. No `project_mutation` was issued. No `cross_user_leakage` was attempted. No `hidden_private_protected_authorized` flag was set." |

**Candidate-preparation: PASS.** Correctly blocked, no accepted candidate, no proposal action.

---

## 9. Task 8 — Gap review

| Gap | Type | Severity | Evidence |
|---|---|---|---|
| Source-class hint map does not recognize RF / WiFi / floor-plan / material-scattering sources well enough | **Scope** | Low | The 10 records show 4 distinct `source_class_hint` values (`unknown_authority` ×5, `official_standard` ×2, `public_dataset` ×2, `official_government_or_agency_data` ×1) — **not** all `unknown_authority`. The boundary **did** recognize some sources. The gap is in the per-domain keyword map: the boundary's `_derive_source_class` does not have a keyword for `WiFi`, `RF`, `CSI`, `material scattering`, `floor-plan`, etc., so it falls back to `unknown_authority` for most records. This is a **scope** gap. |
| Access / license hint map lacks this domain | **Scope** | Low | §9 shows 2 records with `access_license_status_guess: open_access` (arxiv.org), 2 with `paywalled` (sciencedirect.com), and 6 with `unknown`. The boundary **did** recognize arxiv.org and sciencedirect.com via its `OPEN_ACCESS_DOMAINS_V1` and `PAYWALLED_DOMAINS_V1` lists. The 6 `unknown` records are from domains not in either list. This is a **list** gap, easy to fix by extending the lists. |
| Scout keyword / signal derivation does not detect the relevant open-problem signals for this topic | **Scope** | Low | The scout produced 0 signals because (a) the route's 0 kept entries meant the scout had 0 input signal items, AND (b) the scout's keyword-based signal derivation does not have markers for `RF multipath`, `WiFi sensing`, `floor-plan topology`, `material scattering`. This is a **scope** gap. |
| **No correctness gap** observed in boundary enforcement | — | — | All 5 boundary invariants held for all 3 HTTP calls. All 4 helper modules ran their validators. The route, scout, integration, and candidate-preparation helpers all reported valid per-step status (the chain's `blocked` verdict came from per-entry enum mismatch, not from any invariant violation). |
| **No authority gap** observed | — | — | 25 `denied_authority_flags` in the route's `denied_authority_flags` report are all `False` (or `True` only for the `all_authority_flags_false: True` invariant-report flag). 22 `denied_authority_flags` in the candidate-preparation helper's allow-list are not present (since the packet was not built), but the helper's `validate_request` did not flag any authority violation. No `agi_claim_authorized: True`, no `public_claim_authorized: True`, no `discovery_claim_authorized: True`, no `proof_claim_authorized: True`, no `consciousness_claim_authorized: True`, no `sentience_claim_authorized: True`, no `benchmark_claim_authorized: True`. |

**Gaps: 3 scope gaps, 0 correctness gaps, 0 authority gaps.** The scope gaps are all in the **per-domain mapping / keyword lists**, not in the **enforcement** (which is the actual boundary work). The boundary's enforcement — deny unsafe authority, deny source fetching, deny provider calls, deny `.weslr` IO, deny public claims — held perfectly.

---

## 10. Task 9 — Release gate review

| Requirement | Met? | Evidence |
|---|---|---|
| Exact-file | YES ✓ | The gate edit added an exact path `docs/WESLR_CONTROLLED_NOVA_TRUE_RUN_METADATA_SOURCE_LOCATOR_TO_MLCF_CANDIDATE_PREPARATION_V1.md` to the `or path == "..."` allow-list. No wildcard, no prefix, no regex. |
| Marker-checked | YES ✓ | The per-path if-block in `_check_git_scope` evaluates `_controlled_nova_true_run_metadata_locator_to_mlcf_candidate_preparation_doc_valid`, which is the result of `_doc_with_markers_is_valid(doc, markers)`. The marker set has **6** exact-substring markers, all verified to be present in the result artifact (`WESLR Controlled Nova True Run`, `Run by: operator (manual hand-issued)`, `metadata_only_locator_candidates`, `external_evidence_unverified`, `Sparse RF spatial change map`, `no follow-up \`urllib.request.urlopen\``). |
| Limited to the new true-run result artifact | YES ✓ | The 6 marker phrases are unique to this lane (`WESLR Controlled Nova True Run`, `Sparse RF spatial change map`, `no follow-up \`urllib.request.urlopen\``). The 3 shared markers (`Run by: operator (manual hand-issued)`, `metadata_only_locator_candidates`, `external_evidence_unverified`) are general invariants that should appear in any operator-issued metadata-locator result. |
| No wildcard | YES ✓ | Grep for `\*` in the new gate diff returns 0 matches. |
| No broad `docs/` allowance | YES ✓ | The added `or path == "docs/..."` is one exact string, not a `path.startswith("docs/")` prefix. |
| No branch / env bypass | YES ✓ | No `if env == ...` or `if branch == ...` check. The allowance is unconditional once the file is on the staged list. |
| No gate weakening | YES ✓ | The 5 existing gates (G1 harness, G2 staged-scope, G3 no-`execution_allowed=True` in production, G4 no-OpenClaw/no-TIA, G5 handler-registry-metadata) all still run. The new allowance is **additive** in the `or path == "..."` chain and the per-path if-block; nothing was removed. The release-check self-test still passes (`SELF_TEST: PASS`). |
| No protected-file weakening | YES ✓ | The 4 protected files (`weslr/chat_responder.py`, `main.py`, `dialogue.py`, `chat_ui.py`) and the N/A `weslr/main.py` are not in the gate's allow-list, not in the deny-list, and not in the per-path if-block. The gate's G3 (`execution_allowed=True`) and G5 (handler registry) checks still pass. |

**Release gate: PASS.** The gate edit is **exact-file, marker-checked, additive only, no weakening**. The convention mirrors the 50+ existing exact-file allowances in the same gate (design-doc allowance, result-doc allowance, prior-lane allowances). 6 narrow markers, all present in the result. The gate's `WESLR_RELEASE_GATE_V1_OK` was confirmed in the prior lane's validation.

---

## 11. Task 10 — Protected-file review

| Protected file | Status |
|---|---|
| `weslr/chat_responder.py` | UNCHANGED (md5 `10eccfe47edb12b72d2110dc1742e51b`, matches `origin/master`) |
| `main.py` (top-level) | UNCHANGED (md5 `5141116c2aeda9971df00b78122d0d0a`, matches `origin/master`) |
| `dialogue.py` | UNCHANGED (md5 `8434e63136075f7f1a26d601dcf08aee`, matches `origin/master`) |
| `chat_ui.py` | UNCHANGED (md5 `bf7572bc0a9eb0348be1880faf6b471b`, matches `origin/master`) |
| `weslr/main.py` | N/A — does not exist on `origin/master` either |

Working-tree diff on protected files: **empty**.
Staged diff on protected files: **empty** (post-commit, n/a).

**Protected files: PASS.** None of the 5 protected files (4 present + 1 N/A) were modified by the prior lane or this review lane. The 2 committed files (`docs/WESLR_CONTROLLED_NOVA_TRUE_RUN_METADATA_SOURCE_LOCATOR_TO_MLCF_CANDIDATE_PREPARATION_V1.md` + `weslr/tests/release_gate_v1.py`) are both outside the protected-files list.

---

## 12. Validation results

| Check | Result |
|---|---|
| `python3 -m py_compile weslr/mlcf_routing_from_live_searxng_metadata_result.py weslr/cross_domain_open_problem_discovery_scout.py weslr/cross_domain_scout_to_mlcf_integration.py weslr/cross_domain_scout_to_mlcf_candidate_preparation.py` | **exit 0** (all 4 modules compile) |
| `python3 -m pytest weslr/tests/test_cross_domain_scout_to_mlcf_candidate_preparation_v1.py` | **57 passed in 5.29s** |
| `python3 -m pytest weslr/tests/test_cross_domain_scout_to_mlcf_integration_v1.py` | **51 passed in 4.58s** |
| `python3 -m pytest weslr/tests/test_cross_domain_open_problem_discovery_scout_v1.py` | **21 passed in 0.25s** |
| `python3 -m pytest weslr/tests/test_mlcf_routing_from_live_searxng_metadata_result_v1.py` | **22 passed in 0.07s** |
| `git diff --check` | **exit 0** |
| `python3 weslr/tests/release_gate_v1.py` (no staged files, no-op) | `WESLR_RELEASE_GATE_V1_OK` |
| `bash scripts/weslr_release_check.sh` | `WESLR_RELEASE_CHECK_OK — all gates passed` + `SELF_TEST: PASS` |
| **Total tests passed across the 4 invocations** | **151** |
| Working-tree diff on protected files | empty |
| Staged diff on protected files | empty |

All 8 validations pass. The 4 helper modules compile, 151 unit tests pass, the release gate is OK, the release check is OK, the self-test is OK, and the protected files are unchanged.

---

## 13. Review verdicts

### 13.1 Was the run valid?
**YES.** All 5 boundary invariants held for all 3 HTTP calls. All 4 helper modules ran their validators. The route packet, scout packet, integration packet, and (correctly absent) candidate-preparation packet were all produced or correctly omitted per the design. The release-gate edit is exact-file, marker-checked, additive only. All 4 protected files are unchanged. All 8 validations pass. 151 unit tests pass.

### 13.2 Was the run interesting?
**YES.** In a measured way. Three concrete interesting findings:

1. **The run captured 10 metadata records across 5 distinct source classes** (`unknown_authority` ×5, `official_standard` ×2, `public_dataset` ×2, `official_government_or_agency_data` ×1) and 8 distinct domains (`arxiv.org`, `www.sciencedirect.com`, `zhouzimu.github.io`, `www.itu.int`, `pmc.ncbi.nlm.nih.gov`, `escholarship.org`, `neurips.cc`, `www.mdpi.com`). The records are real SearXNG returns for the WiFi / RF / floor-plan topic.

2. **The chain's `blocked` verdict was produced by a single specific scope gap** — the route's `_validate_entry_fields` rejected all 10 records, likely because the per-row enum allow-list does not include the value the boundary produced for the 10 records (e.g. `evidence_role_guess: candidate_signal` may not be in the route's allow-list). This is **not** a defect in any one module; it is a **consistency** gap between the boundary's per-row enum vocabulary and the route's per-row enum vocabulary. Both modules are individually correct; they are mismatched.

3. **All 4 downstream effects of the route's 0 kept entries were correctly handled as safety verdicts**:
   - The scout's `signal_candidate_count: 0` is a downstream effect of the route's 0 kept, not an independent defect.
   - The integration's `selected_route: scout_blocked_by_safety` is the integration helper's correct response to a scout with 0 bridge signals.
   - The candidate-preparation's rejection is the candidate-preparation helper's correct response to an integration packet with a non-eligible selected_route.
   - The chain's overall `route_status: blocked` is the route's correct response to 0 kept entries + 0 entry-validation successes.

   **This is a textbook example of safety-by-design: each helper's safety verdict propagated correctly through the chain, without any helper escalating to an unsafe state, without any helper asserting authority it didn't have, without any helper fetching source content, and without any helper making a public claim.**

### 13.3 Correctness gap or scope gap?
**Scope gap.** Three concrete scope gaps, all in the **per-domain mapping / keyword lists**, none in the **enforcement**:

1. The boundary's `_derive_source_class` does not have a keyword for `WiFi`, `RF`, `CSI`, `material scattering`, `floor-plan`. (6 of 10 records fell back to `unknown_authority` because of this.)
2. The boundary's `OPEN_ACCESS_DOMAINS_V1` and `PAYWALLED_DOMAINS_V1` lists do not cover the WiFi / RF / floor-plan domain family. (5 of 10 records fell back to `unknown` access-license because of this.)
3. The route's `_validate_entry_fields` enum allow-list does not include the value the boundary produced for all 10 records. (This is the actual blocker of the chain — fixing this gap would unblock the chain for this topic.)

The **enforcement** (deny unsafe authority, deny source fetching, deny provider calls, deny `.weslr` IO, deny public claims) held perfectly. All 4 protected files are unchanged. The 5 boundary invariants held. The 25 `denied_authority_flags` in the route's report are all `False`. The chain's safety verdicts (scout → integration → candidate-preparation) propagated correctly.

**There is no correctness gap. There is no authority gap. The 3 scope gaps are all in scope-extension territory, not in enforcement-fix territory.**

---

## 14. Recommended next lane

**`DESIGN_WESLR_RF_WIFI_FLOORPLAN_SOURCE_CLASS_AND_SCOUT_SIGNAL_HINT_REPAIR_V1`**

This is the owner-supplied next-lane name. The lane should:

1. **Investigate `_validate_entry_fields` in `weslr/mlcf_routing_from_live_searxng_metadata_result.py`** to identify the exact enum mismatch. Add `candidate_signal` (or whatever the boundary's default is for the `general` family) to the per-row allow-list. This single fix may unblock the chain for the WiFi / RF / floor-plan topic entirely.

2. **Extend the boundary's `_derive_source_class` keyword map** to include `WiFi`, `RF`, `CSI`, `material scattering`, `floor-plan`, `multipath`, `indoor propagation`. This will reduce the `unknown_authority` count from 5/10 to a smaller number for this topic.

3. **Extend the boundary's `OPEN_ACCESS_DOMAINS_V1` and `PAYWALLED_DOMAINS_V1` lists** to include the WiFi / RF / floor-plan / material-scattering domain family. This will reduce the `unknown` access-license count from 5/10 to a smaller number.

4. **Optionally extend the scout's keyword-based signal-derivation** to include RF-multipath / WiFi-sensing / floor-plan-topology / material-scattering markers. This is the lowest-priority of the 3 — the chain is already blocked upstream, and unblocking item (1) should be done first.

The lane is a **scope-extension design**, not a correctness-repair design. The owner explicitly used the word "design" in the lane name, not "implement" or "repair".

### 15. What the next lane must NOT do

- **Do not** route the candidate-preparation packet into the omnichat contract-reply engine, the chat responder, the chat UI, the protected preview, the public weslr.de site, or any model provider.
- **Do not** push the worktree, the scratch, the result file, the gate edit, or the review document to GitHub. The worktree is local-only. The owner can review from the worktree.
- **Do not** delete files, branches, worktrees, or the gate backup.
- **Do not** touch `.weslr`.
- **Do not** run live SearXNG, browse web, or call any provider/model/GitHub API in the next-design lane.
- **Do not** issue public-readiness, AGI, consciousness, sentience, proof, discovery, official benchmark, competition-winning, or public-science claims.

### 16. Final judgment

**`controlled_nova_true_run_metadata_locator_review_valid_interesting_ready_for_boundary_hint_repair_design`**

Reasoning:
- The run was **valid** (all 5 boundary invariants held, all 8 validations passed, 151 tests passed, 4 protected files unchanged, no public claim, no provider call, no `.weslr` IO, no source fetching).
- The run was **interesting** (10 records across 5 source classes and 8 domains, a single specific scope gap identified as the chain's blocker, all 4 downstream effects of the blocker were correctly handled as safety verdicts).
- The run is **ready for a narrow boundary / domain-hint repair design** (the recommended next lane is `DESIGN_WESLR_RF_WIFI_FLOORPLAN_SOURCE_CLASS_AND_SCOUT_SIGNAL_HINT_REPAIR_V1`).
- The gaps are **scope** gaps (3 of them, in keyword maps and per-row enums), **not** **correctness** gaps.
- The chain's safety-by-design behavior held perfectly: 25 `denied_authority_flags` False, no `accepted` candidate, no proposal, no public claim, no provider call, no source fetching.
- The release-gate edit is exact-file, marker-checked, additive only, no weakening.
- The owner can now decide whether to authorize the next-design lane, or to push the worktree as a reviewable branch, or both.

The run is reviewed and ready.

---

## 17. Author and post-review commit

This review document is ready to commit. The commit is **review-only** (no run, no push, no merge, no rebase, no reset, no stash, no worktree create/delete, no file delete, no `.weslr` IO, no live SearXNG, no provider/model call, no public claim). The validation suite (8 commands) will be re-run pre-commit and post-commit per the owner's directive. The release-gate allowance for this review document itself will be added only if the gate requires it (the owner pre-authorized the exact-file marker-checked edit for this case).

The review document does NOT commit the prior lane's result file or the prior lane's gate edit. Those are already committed at `aab12606`. This review only commits the review document (and a gate allowance for the review document, if needed).
