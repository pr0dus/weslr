# CAPABILITY CONTRACT LAYER v1

## 1. Purpose
Weslr now proves a complete governed loop (intake → review → export → delivery). The next architecture risk is capability sprawl: new features touching only part of the loop, publishing new state, or bypassing governance. This file declares the **Capability Contract Layer** so every future ability conforms to the same field-level, governance-aware shape before it ships. Without this contract, we risk fragmenting the canonical cycle and losing operator trust.

## 2. Common capability shape
Each real capability family in the repo already follows a recognizable shape. We document it here so future domains can copy the same inputs/outputs/confidence/governance hooks.

1. **File ingestion & routing (`weslr/file_router.py`, `weslr/file_ingestion.py`, `weslr/pdf_context.py`, `weslr/structured_data.py`):**
   * Input: user/provided file path + query + metadata.
   * Output: `RouterResult` or context summary stored in artifact metadata (`agents/*/artifacts/*.meta.json`).
   * Confidence/scoring: `RouterResult.relevance`, `metadata.relevance_reason`.
   * Governance hook: content qualifies an artifact that later appears in `review_queue.json` and `review_notes`.
   * Loop stage: feeds **Candidate Creation**.

2. **Scientific analysis & notebook parsing (`weslr/scientific_analysis.py`, `weslr/scientific_notebook.py`):**
   * Input: structured dataset or notebook file.
   * Output: analysis summary w/proposed evidence (e.g., `transit_confidence`, `dip_confidence`).
   * Confidence/scoring: `clarity_score`, domain-specific numeric signals.
   * Governance hook: appended to artifact meta `review_notes`/`proof_signals` before review.
   * Loop stage: **Evidence Enrichment**.

3. **Suggestion intake (`weslr/suggestion_box.py`):**
   * Input: HTTP/CLI requests describing domain need.
   * Output: continuity records (`continuity/suggestion_box/*`) and `requests.json` entry.
   * Confidence/scoring: `sellability_score`, `human_proposed_score` computed later.
   * Governance hook: every request persists metadata for operator review.
   * Loop stage: **Intake → Candidate Creation**.

4. **Candidate creation & metadata (`weslr/suggestion_bridge.py` + artifact meta files):**
   * Input: suggestion ID from `suggestion_box`.
   * Output: `review_queue.json` entry, artifact meta files in `agents/*/artifacts` (fields include `review_status`, `lifecycle_stage`).
   * Confidence/scoring: `human_proposed_score`, `clarity_score` recorded immediately.
   * Governance hook: the meta file carries `review_notes` to trace the request.
   * Loop stage: **Candidate Creation / Evidence Ready**.

5. **Review & approval (`main.py review`, `review_artifact()`, helper logic in `sim.py`):**
   * Input: artifact ID + action (`approve`, `reject`, `export`, `note`).
   * Output: updates `review_status`, `lifecycle_stage`, `approved_for_export`, `export_path`, `review_exports`, `human_approvals`, `proof_signals`.
   * Confidence/scoring: `human_proposed_score`, produced `proof_signals` metrics.
   * Governance hook: single lawful path to mutate artifact state and `review_notes`.
   * Loop stage: **Operator Review → Approval**.

6. **Export readiness & queue (`export_queue.json` plus artifact meta fields):**
   * Input: artifact with `approved_for_export=true` + `export_path` set.
   * Output: export queue row (fields include `delivery_mode`, `approved_for_export`, `review_status`).
   * Confidence/scoring: `sellability_score`, `market_fit_score` appear in the row.
   * Governance hook: export queue becomes part of the dashboard story and is the only source for `pack` commands.
   * Loop stage: **Export Surface**.

7. **Packaging & offer (`main.py pack … offer`, `sim.apply_pack_outcome`, `artifact_packs.json`, `pack_outcomes.json`):**
   * Input: pack name linking export queue artifacts.
   * Output: updated `artifact_packs.json` entry plus new `pack_outcomes.json` event (`action`, `created_at`, `note`).
   * Confidence/scoring: `pack_score`, `readiness_score`, `delivery_mode`.
   * Governance hook: every offer is recorded for audit and drives `offer_count`/`accept_count`.
   * Loop stage: **Packaging/Offer**.

8. **Receiver acceptance (`main.py pack … accept`, `apply_pack_outcome`):**
   * Input: pack name matched to outstanding offer.
   * Output: another `pack_outcomes.json` row with `action: accept`, increments `accept_count`.
   * Confidence/scoring: `proof_level_score` recorded at artifact + pack level.
   * Governance hook: marks the loop as completed.
   * Loop stage: **Receiver Outcome**.

9. **Dashboard surfacing (`main.py cmd_serve`, `dashboard/index.html`):**
   * Input: canonical JSONs (`state_core.json`, `communicator_self.json`, `review_queue.json`, `export_queue.json`, `pack_outcomes.json`).
   * Output: cards (status, topics, artifacts, closed-loop story) and operator action panels.
   * Confidence/scoring: displays `review_status`, `sellability`, `human_proposed_score`, pack sequence.
   * Governance hook: visualizing every contract field keeps operators accountable.
   * Loop stage: **Dashboard Surface**.

### Intake architecture summary
- The intake architecture (see docs/CAPABILITY_INTAKE_ARCHITECTURE_v1.md) already enumerates all input classes (text, voice, docs/PDF, tables, charts/images, datasets, telemetry, unknown structured artifacts) and enforces classification before routing into the core.
- Every intake path must normalize its outputs (evidence, confidence, provenance, decision signals) and return them through the same governed contract, avoiding capability-specific divergences.
- Unsupported inputs generate clear proposals rather than silent failures, and repeated inadequacies surface new capability requests via the self-assessment doctrine.

## 3. Universal capability fields
Every capability must expose the following fields (mandatory unless noted):
1. `capability_name` (required) – unique identifier.
2. `module_owner` (required) – file/module implementing the capability.
3. `accepted_inputs` (required) – type(s) of data/requests it consumes.
4. `produced_outputs` (required) – structured result/messages or artifact state it writes.
5. `confidence_signal` (required) – numeric/enum signal (e.g., `sellability_score`, `proof_level_score`).
6. `governance_required` (required) – boolean describing whether operator review locks it.
7. `lifecycle_stage` (required) – designates where the capability sits (`intake`, `review`, `export`, etc.).
8. `integrates_with_loop_stage` (required) – references the stage from Section 2 (e.g., `candidate_creation`, `pack_offer`).
9. `metrics_collected` (optional but recommended) – scoreboard fields (scores, counts, timestamps).
10. `enabled_by_profile` (optional) – indicates runtime flags (like `WESLR_LLM_ENABLED`).
11. `review_notes_reference` (required for capabilities altering state) – where notes go (`agents/*/artifacts/*.meta.json`).
12. `output_destination_json` (required for storage-driven capabilities) – canonical JSON (e.g., `review_queue.json`, `export_queue.json`) where output resides.
Capacities failing to publish these fields should be flagged before deployment.

## 4. Universal vs domain-specific boundary
A. **Universal contract:** All capabilities must publish the fields above, feed one of the governed loop stages, and record at least one confidence/governance signal. They may be wired via `review_status`, `export_queue`, or `pack_outcomes` as shown in Section 2.
B. **Domain-specific content:** Narratives (“Governance Transparency Review”), pack names (`observability-signals-opportunity-pack`), domain-specific scoring heuristics (CRISPR scores, planet detection confidence) and bespoke interface copy belong to this layer. They may vary across domains as long as they obey the universal field contract.

## 4A. Domain family surfaces
The Capability Contract Layer must actively support future domain families without becoming a bottleneck. Every new capability—from Industry/Engineering to Scientific Research, Space/Astronomy, Medical/Care, Education/Academic Support, Elder Care/Family Support, Sports/Performance/Health, Institutional Operations/Administration, Knowledge/Document Intelligence, Communication/Human Interaction, Pattern/Signal Intelligence, and the Federated WESLR Mesh—must be treated as part of the **industry-family tier**, not as bespoke logic. Each such family simply implements the universal fields above and plugs into the governed cycle (intake → review → export → pack → delivery). This ensures growth across verticals while keeping the loop coherent and auditable.

## 5. Critical contract law
Every future capability must declare its `confidence_signal`, state whether `governance_required`, and identify `integrates_with_loop_stage` before it mutates any artifact or touches any queue. This is the anti-sprawl guardrail—no capability touches the loop without these declarations.

## 6. Forbidden shortcuts
Builders must not:
- bypass loop-stage integration (e.g., writing new export queues without using `review_status`).
- skip publishing `confidence_signal` or `governance_required`.
- mutate `review_queue.json`, `export_queue.json`, `artifact_packs.json`, or `pack_outcomes.json` outside the documented APIs.
- hide outputs in undocumented files or ignore the canonical dashboard surfaces.
- embed side effects that change core behavior without review (the fields above document those effects).

## 7. Current stopping point
We stop here: the Capability Contract Layer is now formalized in this doc; no new capabilities are added in this step. Future additions (voice/speech, CRISPR pipelines, planet discovery, elder-support conversation frameworks, educational workflows, etc.) must obey this contract.
