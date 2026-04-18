# UNIVERSAL GOVERNED CYCLE CONTRACT v1

## 1. Purpose
This document crisply captures the *proven* loop that turned the WESLR front door from a waiting shell into a closed, governed delivery pipeline. It is not a proposal; it is a field-level contract. Every stage below reflects an existing module, file, field, and transition already operating in the repo. The goal is to make that reality reusable everywhere.

## 2. Universal doctrine / universal loop stages
1. **Suggestion intake (signal)** ─ `weslr/suggestion_box.py::SuggestionBox.submit_request` + `continuity/suggestion_box/requests.json` capture external requests (forms, laboratories, partners).
2. **Candidate creation (proposal)** ─ `weslr/suggestion_bridge.py` bridges request IDs into `review_queue.json` entries and writes artifact metadata under `agents/<agent>/artifacts/*.meta.json`.
3. **Evidence enrichment** ─ `main.py review ... note` → `main.review_artifact()` (with helpers in `sim.py`) appends `review_notes`, improves `proof_signals`, and persists enriched metadata.
4. **Operator review** ─ `main.py review <id> {approve,reject,export}` drives `review_status` transitions plus `human_approvals`, `review_exports`, and resets `lifecycle_stage`.
5. **Approval / export readiness** ─ `review_status` moves `proposed` → `approved` → `export_ready`, `approved_for_export` flips true, `export_path` records the export slot, and `export_queue.json` gains the entry.
6. **Export queue surface** ─ `export_queue.json` lists export-ready artifacts (fields include `delivery_mode`, `pack_name` linkage, scoring, and `approved_for_export`).
7. **Packaging / offer** ─ `main.py pack <pack> offer ...` calls `sim.apply_pack_outcome()`, which updates `artifact_packs.json` (`pack_name`, `delivery_mode`, `offer_count`, `recent_events`) and appends to `pack_outcomes.json` (`action`, `created_at`).
8. **Receiver outcome** ─ `main.py pack <pack> accept`/`reject` routes through `apply_pack_outcome()`, increasing `accept_count` or adding a revision event, and logs the acceptance details into `pack_outcomes.json`.
9. **Dashboard surfacing** ─ `main.py cmd_serve` exposes `dashboard/index.html`; the UI fetches the canonical JSONs (`state_core.json`, `communicator_self.json`, `review_queue.json`, `export_queue.json`, `pack_outcomes.json`) and highlights the closed loop in the new “Closed Loop Story” card.

## 3. Exact file ownership
- Intake: `weslr/suggestion_box.py`, `continuity/suggestion_box/{requests.json,continuity.json}`.
- Candidate creation: `weslr/suggestion_bridge.py`, `agents/*/artifacts/*.meta.json`.
- Evidence enrichment / operator review: `main.py review` → `main.review_artifact()` (bridges into `sim.py` helpers).
- Export readiness: `export_queue.json` plus artifacts’ `approved_for_export`, `export_path`, `review_status`.
- Packaging/offer: `main.py pack ... offer`, `sim.apply_pack_outcome()`, `artifact_packs.json`, `pack_outcomes.json`.
- Receiver acceptance: `main.py pack ... accept` through `apply_pack_outcome()`.
- Dashboard: `main.py cmd_serve`, `dashboard/index.html` (plus new closed-loop card logic and JSON fetches).

## 4. Exact field contract
- `review_notes`, `review_status`, `lifecycle_stage`, `approved_for_export`, `export_path`, `review_exports`, `human_approvals` (artifact meta + `review_queue.json`).
- `export_queue.json` uses the same fields plus `destination`, `distribution`, `delivery_mode`, `approved_for_export`.
- `artifact_packs.json` entries contain `pack_name`, `delivery_mode`, `offer_count`, `accept_count`, `recent_events`, embedded `artifacts` list.
- `pack_outcomes.json` events have `pack_name`, `action` (`offer`/`accept`/`reject`), `note`, `buyer`, `price_band`, `group_kind`, `niche_theme`, `category`, `created_at`.
- Dashboard hooks: `review_queue`, `export_queue`, `pack_outcomes`, `state_core.json` (status bits pulled into cards).

## 5. Exact transition table
- `review_status`: `proposed` → `approved` → `export_ready`.
- `lifecycle_stage`: `prototype` → `approved` → `packed`.
- `approved_for_export`: `false` → `true` when `review_status` hits `export_ready`.
- `export_queue` entry appears once `approved_for_export` is true and `export_path` is set.
- `pack_outcomes.action`: `offer` → `accept` (or `reject/revise` if not accepted).
- `artifact_packs.<pack>.offer_count` increments on `offer`, `accept_count` increments on `accept`, `recent_events` logs each action.

## 6. Universal vs domain-specific boundary
- Universal logic: suggestion → review → export → pack offer → receiver outcome (fields/flows above). These can be reused exactly as-is.
- Domain-specific logic: scoring heuristics, pack names, narrator text (“Closed Loop Story”), and dashboard framing are specific to the observability/governance story.

## 7. Forbidden shortcuts
- Do not hand-edit `review_queue.json`, `export_queue.json`, `artifact_packs.json`, or `pack_outcomes.json` to fake transitions.
- Do not skip `review_artifact()` or `apply_pack_outcome()` — they are the only lawful operators.
- Do not create new artifact fields outside the documented contract without explicit alignment with this file.

## 8. Current stopping point
- The loop currently stops after the `pack_outcomes` entry with `action: accept` (last event recorded: `observability-signals-opportunity-pack` accepted). The next repeat will begin when a new suggestion enters `suggestion_box` and the cycle replays.
