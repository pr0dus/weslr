# WESLR Existing Public Pilot Feedback Implementation Surfaces Audit V1

## 1. Status

- audit-only
- no implementation
- no source/runtime/helper edits
- no data migration
- no queue creation
- no form creation
- no database creation
- no email sending
- no deployment changes
- no OCW bridge changes
- no `.weslr` IO
- no private data dump
- no user-data reads except safe source/schema/path inspection
- no runtime/chat/UI/voice changes
- no provider/model/search/advisor calls
- no final-answer generation
- no public/product/intelligence/Turing/certification claims
- no authority grant

## 2. Preflight Result

The public pilot/feedback/review design preflight stopped because related implementation already exists. This report maps the existing public pilot, feedback, review, suggestion, intake, queue, storage, and OCW/deployment-management surfaces for reuse/consolidation review instead of creating a duplicate public pilot boundary.

## 3. Surface Inventory Table

| Path | Type | Likely purpose | Behavior present | Storage present | User data risk | Public exposure risk | OCW/deployment relevance | Needs further audit |
|---|---|---|---:|---:|---|---|---:|---:|
| `weslr/user_signal_intake.py` | source | Public website signal classification and safe record construction | yes | no | low | medium | no | yes |
| `weslr/website_signal_integration.py` | source | Fire-and-forget website `/chat` metadata signal capture | yes | via `public_signal_store` | medium | medium | no | yes |
| `weslr/public_signal_store.py` | source | Append-only safe public signal JSONL store | yes | yes (`weslr/public_signals.jsonl`) | medium | medium | no | yes |
| `weslr/contract_observation.py` | source | Passive contract-observation storage from website metadata | yes | yes (`weslr/contract_observations.jsonl`) | medium | medium | no | yes |
| `.github/ISSUE_TEMPLATE/feedback_request.yml` | issue template | GitHub public feedback template | yes (GitHub issue form) | yes (GitHub issues) | medium | high | no | yes |
| `review_queue.json` | queue file | Legacy/general review queue indicator | unknown | yes/unknown | unknown | unknown | no | yes |
| `weslr/advisor_review_queue.py` | source | Advisor review queue schema and validation helpers | yes (schema/validation only) | no | low | low | no | yes |
| `weslr/advisor_review_queue_persistence.py` | source | Explicit-path JSONL advisor review queue persistence helpers | yes | yes, if called | medium | low | no | yes |
| `weslr/review_interface.py` | source | Read-only inspection of contract proposal review log | yes | reads `weslr/contract_proposal_review_log.jsonl` | medium | low | no | yes |
| `weslr/suggestion_box.py` | source | Capability/request intake with JSON persistence | yes | yes (`continuity/suggestion_box/*.json`) | high | medium | no | yes |
| `weslr/capability_intake.py` | source | Minimal capability object validation/ingestion | yes | no | low | low | no | yes |
| `weslr/consolidation_promotion.py` | source | Candidate promotion decision, audit logging, and optional auto-promotion writes | yes | yes, if enabled/called | medium | medium | no | yes |
| `weslr/PILOT_COHORT.md` | docs | Public test cohort, access rules, signal thresholds | no | no | low | medium | no | yes |
| `weslr/PILOT_DAY0_REPORT.md` | docs | Day 0 pilot activation/readiness report | no | no | low | medium | no | yes |
| `weslr/PILOT_LAUNCH_RUNBOOK.md` | docs | Operational pilot launch, invites, monitoring, rollback runbook | no | no | medium | medium | no | yes |
| `weslr/pilot_signal_logger.py` | source | Pilot cohort signal/event/intervention/red-team JSON logger | yes | yes (`continuity/pilot_signals/**`) | high | medium | no | yes |
| `weslr/deploy/WESLR_OCW_HANDOFF_CONTRACT_V1.json` | deployment contract | OCW deployment handoff invariants/tests | no | no | none | low | yes | yes |
| `weslr/docs/OCW_HANDOFF_V1.md` | docs | Ubuntu/website deployment agent handoff template | no | no | low | medium | yes | yes |
| `continuity/capability_suggestions.db` | data indicator | Capability suggestion database | unknown | yes (24,576 bytes) | high | unknown | no | yes |
| `continuity/pilot_signals/interventions.json` | data indicator | Pilot intervention records | unknown | yes (25 bytes) | high | unknown | no | yes |
| `continuity/pilot_signals/redteam_events.json` | data indicator | Pilot red-team event records | unknown | yes (18 bytes) | high | unknown | no | yes |
| `continuity/pilot_signals/user_events.json` | data indicator | Pilot user event records | unknown | yes (18 bytes) | high | unknown | no | yes |
| `continuity/pilot_signals/signals/trust_score.json` | data indicator | Pilot trust-score records | unknown | yes (18 bytes) | high | unknown | no | yes |
| `continuity/pilot_signals/signals/continuity_rate.json` | data indicator | Pilot continuity-rate records | unknown | yes (17 bytes) | medium | unknown | no | yes |
| `continuity/pilot_signals/signals/recovery_rate.json` | data indicator | Pilot recovery-rate records | unknown | yes (17 bytes) | medium | unknown | no | yes |
| `continuity/pilot_signals/signals/intervention_rate.json` | data indicator | Pilot intervention-rate records | unknown | yes (17 bytes) | medium | unknown | no | yes |
| `continuity/suggestion_box/requests.json` | data indicator | Stored suggestion requests | unknown | yes (3,618 bytes) | high | unknown | no | yes |
| `continuity/suggestion_box/continuity.json` | data indicator | Suggestion continuity/action log | unknown | yes (784,583 bytes) | high | unknown | no | yes |

## 4. Behavior Classification

- intake behavior: `weslr/user_signal_intake.py`, `weslr/website_signal_integration.py`, `weslr/capability_intake.py`, `weslr/suggestion_box.py`
- feedback behavior: `.github/ISSUE_TEMPLATE/feedback_request.yml`, `weslr/website_signal_integration.py`, `weslr/public_signal_store.py`, `weslr/contract_observation.py`
- suggestion behavior: `weslr/suggestion_box.py`, `weslr/capability_intake.py`, related docs under `docs/*SUGGESTION*` discovered by filename search
- review queue behavior: `weslr/advisor_review_queue.py`, `weslr/advisor_review_queue_persistence.py`, `weslr/review_interface.py`, `review_queue.json`
- persistence/storage behavior: `weslr/public_signal_store.py`, `weslr/contract_observation.py`, `weslr/advisor_review_queue_persistence.py`, `weslr/suggestion_box.py`, `weslr/pilot_signal_logger.py`, `continuity/*` storage indicators
- promotion behavior: `weslr/consolidation_promotion.py`
- pilot cohort behavior: `weslr/pilot_signal_logger.py`; cohort policy/runbook exists in `weslr/PILOT_COHORT.md`, `weslr/PILOT_DAY0_REPORT.md`, `weslr/PILOT_LAUNCH_RUNBOOK.md`
- website integration behavior: `weslr/website_signal_integration.py`, `weslr/public_signal_store.py`, `weslr/contract_observation.py`
- OCW/deployment management behavior: docs/contracts only in inspected files: `weslr/deploy/WESLR_OCW_HANDOFF_CONTRACT_V1.json`, `weslr/docs/OCW_HANDOFF_V1.md`
- docs/runbook only: `weslr/PILOT_COHORT.md`, `weslr/PILOT_DAY0_REPORT.md`, `weslr/PILOT_LAUNCH_RUNBOOK.md`, `weslr/docs/OCW_HANDOFF_V1.md`
- unknown/stale: `review_queue.json`, broad historical docs discovered by filename search, `export_queue.json`, memory files, and existing untracked docs/scripts in the working tree were not audited deeply in this lane

## 5. Public Pilot Readiness Map

| Capability | Assessment |
|---|---|
| coming soon / first-30-pilot concept | absent |
| pilot cohort handling | docs-only plus implementation exists but unreviewed (`PilotSignalLogger`) |
| first-come-first-served handling | absent |
| consent handling | unsafe/unknown |
| contact permission handling | partial/unsafe unknown (`suggestion_box.py` stores optional `contact_email`; runbook invite template includes operator contact placeholders) |
| feedback intake | partial (`feedback_request.yml`; website metadata signals) |
| suggestion intake | implementation exists but unreviewed (`suggestion_box.py`) |
| project review intake | partial/unknown (`review_interface.py`, GitHub feedback template, review queue indicators) |
| review queue | implementation exists but unreviewed (`advisor_review_queue*`, `review_queue.json`) |
| redaction | partial (`user_signal_intake.py`, `public_signal_store.py`, `contract_observation.py`, advisor persistence summaries) |
| privacy protection | partial; strongest in website signal path, weak/unknown in suggestion and pilot logger paths |
| deletion/revocation | absent/unsafe unknown |
| operator review | present in docs and queue schemas; behavior linkage unreviewed |
| OCW/Ubuntu management | docs-only/present handoff template |
| UX feedback capture | partial (`feedback_request.yml`, public signal metadata) |
| release/promotion path | partial/implementation exists but unreviewed (`consolidation_promotion.py`; release gates exist separately) |

## 6. Privacy and Consent Audit

- consent before contact storage: unsafe/unknown. `SuggestionRequest` includes optional `contact_email` and `SuggestionBox.submit_request()` persists it; no consent field was visible in inspected source.
- consent before feedback storage: partial/unknown. GitHub feedback issues are user-submitted publicly, but the template does not show explicit privacy/consent warnings. Website metadata signal storage states no raw prompt/PII storage.
- consent before upstream/public sharing: unsafe/unknown. No explicit upstream/public-sharing consent gate was visible in inspected surfaces.
- raw private content exclusion: present in `user_signal_intake.py`, `public_signal_store.py`, `contract_observation.py`; absent/unknown for `suggestion_box.py` and `pilot_signal_logger.py`.
- project-review privacy: partial/unknown. `review_interface.py` strips forbidden top-level fields before returning records, but it may read a review log if present.
- deletion/revocation: absent/unknown in inspected source.
- cross-user reuse prevention: partial/unknown. Website signals hash session IDs; pilot/suggestion storage may include user/requester identifiers.
- `.weslr` exclusion: partial. Advisor persistence policy defaults to `.weslr/advisor_review_queue.jsonl`; this lane did no `.weslr` IO. `consolidation_promotion.py` uses `$WESLR_ROOT` or home `.weslr` for audit/destination writes if promotion behavior is called.
- secrets/customer-data exclusion: partial. Several source validators scan for secrets/private data; suggestion/pilot logger paths need deeper review.

No raw stored records were read or dumped.

## 7. Queue and Storage Audit

| Surface | Queue/storage paths | Format | Writes possible | Reads possible | Schema visible from source | May contain private user content | Retention/deletion visible | Redaction visible | Release gates govern outputs |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| `public_signal_store.py` | `weslr/public_signals.jsonl` | JSONL | yes | not in inspected snippet | yes | medium | no | yes | unknown |
| `contract_observation.py` | `weslr/contract_observations.jsonl` | JSONL | yes (append helper exists beyond inspected builder/validator) | unknown | yes | medium | no | yes | unknown |
| `advisor_review_queue_persistence.py` | default `.weslr/advisor_review_queue.jsonl`; explicit path accepted | JSONL/JSON policy | yes | yes | yes | medium | retention field is `unspecified` by default | yes, summaries redact/count | unknown |
| `review_interface.py` | `weslr/contract_proposal_review_log.jsonl` | JSONL | no | yes | partial | medium | no | strips forbidden top-level fields | unknown |
| `suggestion_box.py` | `continuity/suggestion_box/requests.json`, `continuity/suggestion_box/continuity.json` | JSON | yes | yes | yes | high | no | no | unknown |
| `pilot_signal_logger.py` | `continuity/pilot_signals/**.json` | JSON | yes | yes | yes | high | no | no | unknown |
| `continuity/capability_suggestions.db` | `continuity/capability_suggestions.db` | SQLite DB indicator | unknown | unknown | no, not inspected | high | unknown | unknown | unknown |
| `review_queue.json` | `review_queue.json` | JSON queue indicator | unknown | unknown | no, raw file not read | unknown | unknown | unknown | unknown |

Safe metadata observed:
- `continuity/capability_suggestions.db` exists: 24,576 bytes.
- `continuity/suggestion_box/continuity.json` exists: 784,583 bytes.
- `continuity/suggestion_box/requests.json` exists: 3,618 bytes.
- `continuity/pilot_signals/*.json` and `continuity/pilot_signals/signals/*.json` exist with small initialized sizes.

## 8. OCW / Ubuntu Deployment Management Audit

- OCW handoff docs/contracts exist: `weslr/deploy/WESLR_OCW_HANDOFF_CONTRACT_V1.json` and `weslr/docs/OCW_HANDOFF_V1.md`.
- The handoff doc defines OCW as the WESLR Ubuntu server / website deployment agent and says OCW may deploy website files, manage services, and run validation commands.
- It implies deployment/restart authority only within documented deployment tasks; it requires baseline recording, fast-forward-only pull, release gate execution, and structured report output.
- It explicitly forbids production public exposure until public readiness gates pass and forbids secrets, credentials, API keys, TIA bridge/private commercial IP, and non-WESLR domains.
- It does not specifically mention private pilot data beyond general secrets/private IP and readiness-gate protection.
- It requires operator ownership in status/owner fields and STOP behavior on release gate failure.
- It logs actions by requiring a report format, but no behavior-linked logging implementation was inspected.
- It does not appear to bypass release gates; the JSON contract lists release gate tests and invariants, and the handoff doc requires `python3 weslr/tests/release_gate_v1.py` after pull.
- In inspected surfaces, OCW/deployment management is docs/contract-only, not directly behavior-linked.

## 9. Duplication Risk

A new public pilot boundary would duplicate existing surfaces in these areas:

- website metadata intake: reuse/review `weslr/user_signal_intake.py`, `weslr/website_signal_integration.py`, `weslr/public_signal_store.py`, and `weslr/contract_observation.py` instead of creating another signal path.
- feedback collection: reuse/review `.github/ISSUE_TEMPLATE/feedback_request.yml` and website signal storage instead of adding a parallel feedback form.
- suggestion/request intake: reuse/review `weslr/suggestion_box.py` and `weslr/capability_intake.py` instead of creating a second suggestion queue.
- review queues: reuse/review `weslr/advisor_review_queue.py`, `weslr/advisor_review_queue_persistence.py`, `weslr/review_interface.py`, and existing queue indicators instead of adding another queue.
- pilot logging: reuse/review `weslr/pilot_signal_logger.py` and pilot docs instead of creating another pilot signal logger.
- deployment handoff: reuse/review OCW docs/contracts instead of adding a separate Ubuntu/deployment authority boundary.

Shortest consolidation path: review and govern the existing surfaces, especially privacy/consent/retention around suggestion and pilot storage, before designing or implementing any new public boundary.

## 10. Gap/Risk Findings

| finding_id | Surface/path | Severity | Issue | Evidence from source/docs only | Recommended next step | Do not fix in this lane |
|---|---|---|---|---|---|---:|
| PPF-AUD-001 | `weslr/suggestion_box.py` | blocker | Suggestion intake persists contact/user-provided fields without visible consent, redaction, retention, or deletion controls. | `SuggestionRequest` includes `contact_email`, `requested_capability`, `problem_statement`, `additional_notes`; `_save_requests()` writes JSON. | Review and add governance/privacy boundary around existing suggestion storage. | yes |
| PPF-AUD-002 | `weslr/pilot_signal_logger.py` | blocker | Pilot logger writes user/session IDs and arbitrary `details` to continuity JSON without visible redaction/consent/retention controls. | `log_user_event()` stores `user_id`, `session_id`, `details`; CLI can print user events/interventions/redteam data. | Quarantine or review pilot logger before public use. | yes |
| PPF-AUD-003 | `.github/ISSUE_TEMPLATE/feedback_request.yml` | high | Public feedback issue form may collect use-case/background information without explicit privacy warning. | Template asks for feedback, concerns, next improvement, and optional background/use case. | Add privacy/consent wording in a future allowed lane. | yes |
| PPF-AUD-004 | `weslr/website_signal_integration.py` | medium | Integration hashes session ID and stores metadata, but consent/user notice is not visible in inspected source. | `capture_website_signal()` builds event and calls append store silently; comments say fire-and-forget. | Review website privacy notice and opt-out posture. | yes |
| PPF-AUD-005 | `weslr/advisor_review_queue_persistence.py` | medium | Default queue path points into `.weslr`, conflicting with lanes that forbid `.weslr` IO unless tightly authorized. | `AdvisorQueuePersistencePathPolicy.queue_path = ".weslr/advisor_review_queue.jsonl"`; append/load helpers can read/write explicit paths. | Review storage authority and path policy before queue processing. | yes |
| PPF-AUD-006 | `weslr/consolidation_promotion.py` | high | Promotion helper can write destination records/audit logs if enabled/called; public pilot flow must not accidentally activate promotion. | `auto_promote()` calls `_write_destination_record()` when config permits; `_AUDIT_PATH` is under `$WESLR_ROOT` or home `.weslr`. | Keep promotion isolated from public feedback until governance boundary is reviewed. | yes |
| PPF-AUD-007 | `weslr/PILOT_LAUNCH_RUNBOOK.md` | high | Runbook includes invite email and operator contact placeholders; public launch semantics exist as docs but consent/privacy wording is incomplete. | Invite template includes selected pilot language and contact placeholders; log retention table exists but source retention enforcement was not visible. | Review pilot launch docs for consent, deletion, and data-minimization before use. | yes |
| PPF-AUD-008 | `weslr/docs/OCW_HANDOFF_V1.md` | medium | OCW may manage services/deployment paths, but pilot private-data handling is not explicitly covered. | OCW hard boundaries mention secrets/private IP and production exposure gates, but not pilot data stores. | Add pilot-data non-access/non-export clauses in future OCW governance review. | yes |
| PPF-AUD-009 | `review_queue.json` and continuity indicators | medium | Queue/data files exist or are referenced, but raw content was intentionally not inspected; schema/content risk remains unknown. | Safe metadata only: queue/data indicators and sizes; privacy rule prevented raw reads. | Run dedicated storage privacy/retention audit with explicit safe metadata tooling. | yes |
| PPF-AUD-010 | broad discovered docs/surfaces | low | Many related docs/surfaces exist; this audit covered the named surfaces and filename/search indicators, not full semantic review of every historical doc. | Filename search found many review/suggestion/pilot/OCW docs. | Use a focused review lane, not implementation. | yes |

## 11. Consolidation Recommendation

Primary next lane: `REVIEW_EXISTING_PUBLIC_PILOT_FEEDBACK_SURFACES_V1`

Rationale: implementation already exists across intake, feedback, suggestion, queue, pilot logging, and OCW handoff surfaces. The shortest safe path is a review/consolidation lane over existing surfaces before any design or safety-fix implementation. The most urgent questions are consent, retention/deletion, raw content exclusion, `.weslr` path authority, and whether public/OCW flows can reach storage/promotion behavior.

## 12. Denied Authority

All values below are required false:

```yaml
permits_source_edits: false
permits_runtime_changes: false
permits_queue_creation: false
permits_queue_processing: false
permits_database_creation: false
permits_database_reads: false
permits_database_writes: false
permits_email_sending: false
permits_user_contact_export: false
permits_private_feedback_dump: false
permits_upstream_submission: false
permits_public_testimonials: false
permits_ocw_management_changes: false
permits_ubuntu_deployment_changes: false
permits_service_restart: false
permits_provider_calls: false
permits_model_calls: false
permits_search_calls: false
permits_advisor_calls: false
permits_dot_weslr_reads: false
permits_dot_weslr_writes: false
permits_final_answer_generation: false
permits_public_launch: false
permits_product_readiness_claims: false
permits_intelligence_claims: false
permits_turing_claims: false
permits_certification_claims: false
```

## 13. Decision

`existing_public_pilot_feedback_surfaces_audit_complete_ready_for_review`
