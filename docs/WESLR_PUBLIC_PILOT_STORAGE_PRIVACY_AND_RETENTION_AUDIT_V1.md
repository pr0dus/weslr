# WESLR Public Pilot Storage Privacy And Retention Audit V1

## 1. Status

- audit-only
- no implementation
- no source/runtime/helper edits
- no data migration
- no raw private data reads/dumps
- no queue processing
- no database creation/read/write of rows
- no email sending
- no deployment changes
- no OCW management changes
- no `.weslr` IO
- no provider/model/search/advisor calls
- no runtime/chat/UI/voice changes
- no final-answer generation
- no public/product/intelligence/Turing/certification claims
- no authority grant

## 2. Audit Scope

Audited surface categories:

- public/user intake
- website signal capture
- GitHub feedback template
- review queue schema/persistence/read interface
- suggestion box/capability intake
- consolidation promotion
- pilot cohort docs/logger/storage indicators
- OCW/Ubuntu handoff docs/contracts
- continuity storage indicators

Audit method: source-code/schema/path/metadata only. Raw stored records were not read, printed, summarized, exported, grepped, queried, copied, or dumped.

## 3. Storage Inventory

| Path | Type | Data risk | Raw content likely | Contact data likely | Private project data likely | Write path visible | Read path visible | Retention policy visible | Deletion/revocation policy visible | Redaction policy visible | Audit method used |
|---|---|---|---|---|---|---:|---:|---:|---:|---:|---|
| `weslr/public_signals.jsonl` | jsonl | medium | no by schema intent | no by schema intent | unknown | yes | unknown | no | no | yes | source/schema/path |
| `weslr/contract_observations.jsonl` | jsonl | medium | no by schema intent | no by schema intent | unknown | yes | unknown | no | no | yes | source/schema/path |
| `weslr/contract_proposal_review_log.jsonl` | jsonl | medium | unknown | unknown | unknown | unknown | yes | no | no | partial | source/schema/path |
| `.github/ISSUE_TEMPLATE/feedback_request.yml` | yml | high | yes | unknown | yes | external GitHub | external GitHub | no | no | no | source/schema/path |
| `review_queue.json` | json | unknown | unknown | unknown | unknown | unknown | unknown | no | no | unknown | path only; raw file not read |
| `.weslr/advisor_review_queue.jsonl` | jsonl | medium | unknown | unknown | unknown | yes if called | yes if called | partial (`unspecified`) | no | yes | source/schema/path only; no `.weslr` IO |
| explicit advisor review queue paths | json/jsonl | medium | unknown | unknown | unknown | yes if called | yes if called | partial (`unspecified`) | no | yes | source/schema |
| `continuity/suggestion_box/requests.json` | json | high | yes by source schema | yes | yes | yes | yes | no | no | no | metadata/source only |
| `continuity/suggestion_box/continuity.json` | json | high | yes/unknown | yes/unknown | yes/unknown | yes | yes | no | no | no | metadata/source only |
| `continuity/capability_suggestions.db` | db | high | unknown | unknown | unknown | unknown | unknown | no | no | unknown | metadata/schema names only; no row reads |
| `continuity/pilot_signals/signals/trust_score.json` | json | high | no metric-only likely, but user/session IDs possible | unknown | unknown | yes | yes | no | no | no | metadata/source only |
| `continuity/pilot_signals/signals/continuity_rate.json` | json | medium | no metric-only likely, but session IDs possible | no/unknown | unknown | yes | yes | no | no | no | metadata/source only |
| `continuity/pilot_signals/signals/recovery_rate.json` | json | medium | no metric-only likely | no/unknown | unknown | yes | yes | no | no | no | metadata/source only |
| `continuity/pilot_signals/signals/intervention_rate.json` | json | medium | no metric-only likely | no/unknown | unknown | yes | yes | no | no | no | metadata/source only |
| `continuity/pilot_signals/interventions.json` | json | high | yes/unknown | yes/unknown | yes/unknown | yes | yes | no | no | no | metadata/source only |
| `continuity/pilot_signals/user_events.json` | json | high | yes via arbitrary details possible | yes/unknown | yes/unknown | yes | yes | no | no | no | metadata/source only |
| `continuity/pilot_signals/redteam_events.json` | json | high | yes/unknown | yes/unknown | yes/unknown | yes | yes | no | no | no | metadata/source only |
| `weslr/logs/launch/launch_log.json` | json | medium | unknown | unknown | unknown | docs-only | docs-only | yes in docs only | no | no | docs/path |
| `weslr/logs/user_events.json` | json | high | unknown | unknown | unknown | docs-only | docs-only | yes in docs only | no | no | docs/path |
| `weslr/logs/operator_actions.json` | json | medium/high | unknown | unknown | unknown | docs-only | docs-only | yes in docs only | no | no | docs/path |
| `weslr/logs/redteam_events.json` | json | medium/high | unknown | unknown | unknown | docs-only | docs-only | yes in docs only | no | no | docs/path |
| `continuity/artifacts/**` and indexes | json | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | metadata/path only |
| `continuity/*.json` non-pilot/non-suggestion files | json | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | unknown | metadata/path only |

Safe metadata observed:

- `continuity/capability_suggestions.db` exists and has one schema table name: `capability_suggestions`; no rows were read.
- `continuity/suggestion_box/continuity.json` exists and is substantially larger than the other target pilot/suggestion JSON indicators; raw content was not read.
- `continuity/suggestion_box/requests.json` exists; raw content was not read.
- `continuity/pilot_signals/**` JSON indicators exist; raw content was not read.
- Additional continuity artifact/index JSON files exist outside the named pilot/suggestion paths; this audit only records their path-level presence as broader storage risk context.

## 4. Source Read/Write Path Audit

### Modules with visible writes

- `weslr/public_signal_store.py`: appends validated public signal records to `weslr/public_signals.jsonl`; rejects forbidden fields and PII-like content; append-only write path visible.
- `weslr/contract_observation.py`: appends validated contract observation metadata to `weslr/contract_observations.jsonl`; rejects forbidden fields and PII-like content; append-only write path visible.
- `weslr/website_signal_integration.py`: builds metadata event from `/chat` response metadata, hashes session ID, then calls public signal and contract observation append paths; no response behavior change intended.
- `weslr/advisor_review_queue_persistence.py`: appends and loads explicit-path advisor queue persistence events; default policy path is `.weslr/advisor_review_queue.jsonl`; append-only required by policy, but behavior exists if called.
- `weslr/suggestion_box.py`: initializes storage directories, reads/writes `continuity/suggestion_box/requests.json`, reads/writes `continuity/suggestion_box/continuity.json`, stores request fields including contact and free-text request/problem/note fields.
- `weslr/consolidation_promotion.py`: writes consolidation audit entries and can write destination records if promotion config permits; default audit root can be home `.weslr` via environment/default path.
- `weslr/pilot_signal_logger.py`: creates pilot signal directories/files, reads and writes JSON metrics/events/interventions/red-team records, and can print event files through CLI commands.

### Modules with visible reads

- `weslr/review_interface.py`: reads `weslr/contract_proposal_review_log.jsonl` and strips top-level forbidden fields before returning/printing records; deeper nested/private content risk remains unknown.
- `weslr/advisor_review_queue_persistence.py`: loads JSONL persistence events from explicit path; validates schema after read.
- `weslr/suggestion_box.py`: reads suggestion request and continuity JSON files.
- `weslr/pilot_signal_logger.py`: reads pilot JSON files for summaries and CLI output.
- `weslr/public_signal_store.py` and `weslr/contract_observation.py`: source inspected for append/validation; read/export paths were not the primary behavior.

### Display/export behavior

- `weslr/review_interface.py` CLI can print review records/summaries.
- `weslr/suggestion_box.py` CLI can print stored suggestion/request or scenario/decision outputs.
- `weslr/pilot_signal_logger.py` CLI can print full event/intervention/red-team JSON data from storage files.
- GitHub feedback issue template exposes feedback externally by design through GitHub issue submission.

### Storage properties and influence risk

- Append-only: visible for public signals, contract observations, and advisor persistence; suggestion and pilot logger paths are mutable JSON read/modify/write stores, not strictly append-only at file level.
- Scoped paths: website signal paths are scoped under `weslr/`; pilot/suggestion paths are under `continuity/`; advisor and promotion defaults can involve `.weslr` paths when called.
- User identity/contact fields: visible in suggestion request schema (`contact_email`) and pilot logger (`user_id`, `session_id`); website path stores `session_id_hash` only.
- Raw message/content fields: explicitly forbidden in website signal and contract observation stores; possible in suggestion free-text fields and pilot `details`; GitHub feedback template is free-text by design.
- Queue/promotion influence: advisor queue and consolidation promotion could influence review/promotion if invoked; source does not prove release-gate coupling for queue outputs.

## 5. Consent Audit

| Consent area | Assessment | Evidence basis |
|---|---|---|
| contact storage consent | absent | Suggestion schema can store contact email; pilot runbook includes contact assignment/invite semantics; no consent field visible in audited source/docs. |
| feedback storage consent | partial | GitHub issue submission is user-initiated, but template lacks explicit privacy/consent warning; website metadata capture appears silent/fire-and-forget. |
| suggestion storage consent | absent | Suggestion request storage writes fields to continuity JSON without visible consent labels. |
| project-review submission consent | unknown/unsafe unclear | Review queues/interfaces exist, but consent scope for project-review-style submissions is not visible. |
| upstream/public sharing consent | absent | No explicit upstream/public sharing consent gate visible in audited pilot/feedback/suggestion surfaces. |
| testimonial consent | absent | No testimonial-specific consent path visible; public feedback could be misused without a future boundary. |
| OCW/operator access consent | unknown/unsafe unclear | OCW docs imply deployment/service authority, but no pilot-data access consent boundary is visible. |
| consent scope labels | absent | No shared consent-scope metadata found in audited storage paths. |
| consent revocation | absent | No revocation or withdrawal flow visible. |

## 6. Privacy Audit

| Privacy control | Assessment | Evidence basis |
|---|---|---|
| raw private content exclusion | partial | Present in website signal and contract observation paths; absent/unknown for suggestion free-text, pilot event details, review queues, and GitHub issue feedback. |
| redaction before review | partial | Advisor queue summaries redact/count; review interface strips top-level forbidden fields; suggestion/pilot paths lack visible redaction. |
| redaction before upstream/public use | absent/unknown | No upstream/public sharing pipeline was audited with enforceable redaction. |
| secret/customer-data exclusion | partial | Website/advisor paths include forbidden/sensitive scans; suggestion/pilot/docs paths need explicit protection. |
| `.weslr` exclusion | partial/unsafe unclear | This audit performed no `.weslr` IO; advisor persistence and promotion defaults can target `.weslr` if behavior is called. |
| log/trace/cache exclusion | absent/unknown | Pilot runbook references logs; no enforceable exclusion policy found. |
| cross-user reuse prevention | partial | Website session ID is hashed; pilot/suggestion paths can hold user-linked data and do not show cross-user reuse controls. |
| private project data protection | absent/unknown | Suggestion free text, feedback issue text, review queues, and pilot details can plausibly include private project data. |
| pilot user contact protection | absent/unknown | Contact assignment and contact fields exist without visible minimization/deletion/revocation controls. |
| safe report generation | partial | Audit/review reports avoided raw data; runtime/CLI report safety for pilot/suggestion files is not established. |

## 7. Retention / Deletion / Revocation Audit

| Policy area | Visible policy exists? | Notes |
|---|---:|---|
| retention duration | partial | Pilot launch runbook lists retention durations for some log categories, but source enforcement was not visible. Advisor persistence policy default says retention is `unspecified`. |
| deletion request | no | No deletion request handling found in audited source/docs. |
| revocation of consent | no | No consent revocation handling found. |
| contact removal | no | No contact removal path found for suggestion or pilot contact fields. |
| feedback removal | no | No feedback removal process found beyond external GitHub/manual implications. |
| queue item removal | partial/unknown | Advisor review statuses include archival-style states, but no privacy deletion/removal guarantee visible. |
| archival | partial | Advisor statuses and pilot docs mention archival-like handling; enforceable storage archive policy is not visible. |
| anonymization | partial | Website session hashing exists; no general anonymization path exists for suggestion/pilot/review storage. |
| purge behavior | no | No purge implementation or schedule found. |
| backups | unknown | No backup deletion/retention handling found. |

## 8. Queue / Review Output Risk

Existing queue/review surfaces could:

- expose private data: yes/unknown. Review, suggestion, pilot, and GitHub feedback paths may contain free text, IDs, or project/context details.
- turn feedback into public testimonials: no direct implementation found, but risk remains absent explicit denial/consent boundaries.
- turn suggestions into roadmap automatically: possible risk. Suggestion intake plus consolidation/promotion paths exist; automatic promotion is gated in source by config, but public-feedback linkage is not governed.
- turn project review into official WESLR behavior: possible risk if review/promotion workflows are later connected without privacy/release gates.
- create upstream submissions: no direct behavior found in audited surfaces, but consent/redaction boundaries are absent here.
- influence promotion without review: possible if consolidation auto-promotion config is enabled/called; source indicates review/approval paths but needs governance isolation from public feedback.
- bypass release gates: unknown. Release gates exist and were used for commits, but queue/promotion output-to-release relationship is not visibly enforced.
- create final-answer/runtime behavior: no direct implementation found in audited storage surfaces; deny explicitly before any future wiring.

## 9. OCW / Ubuntu Access Privacy Risk

| OCW/Ubuntu concern | Assessment |
|---|---|
| imply access to pilot data | not explicit, but unsafe/unclear because deployment paths and validation authority may coexist with storage paths |
| imply access to storage files | unknown/unsafe unclear; docs do not explicitly forbid pilot/suggestion/review storage access |
| imply deployment/restart authority | yes, within documented deployment/service workflow |
| require operator approval | partial; owner/operator framing exists, but no storage-specific approval boundary found |
| require logging | partial; report format/baseline logging is required in docs, but behavior-linked action logging was not audited |
| protect private pilot feedback | insufficient; pilot data stores are not explicitly named as off-limits/private |
| separate OCW from WESLR identity | partial; OCW is named as deployment agent, not WESLR itself |
| avoid release-gate bypass | partial; docs require validation/release gates, but private storage access and queue output boundaries are not explicit |

## 10. Gap Findings

| finding_id | Category | Surface/path | Severity | Issue | Evidence type | Raw data inspected | Recommended next step |
|---|---|---|---|---|---|---:|---|
| PPSR-AUD-001 | consent | `weslr/suggestion_box.py` | blocker | Suggestion storage can persist contact and free-text request/problem/note fields without visible consent, deletion, retention, or redaction controls. | source only | no | Design storage privacy/retention governance boundary before public use. |
| PPSR-AUD-002 | privacy/storage | `weslr/pilot_signal_logger.py` | blocker | Pilot logger stores user/session identifiers and arbitrary event details; CLI can print raw event/intervention/red-team JSON. | source only | no | Quarantine or govern pilot logger display/storage before first-30 use. |
| PPSR-AUD-003 | retention/deletion | `continuity/suggestion_box/*`, `continuity/pilot_signals/**` | blocker | No enforceable deletion/revocation/purge/anonymization controls visible for high-risk storage. | source/metadata only | no | Define retention/deletion/revocation policy and enforcement boundary. |
| PPSR-AUD-004 | public feedback | `.github/ISSUE_TEMPLATE/feedback_request.yml` | high | Public issue template can collect free-text feedback/use-case data without explicit privacy/consent/testimonial warning. | source/schema only | no | Add privacy/consent text in a later implementation lane. |
| PPSR-AUD-005 | website metadata | `weslr/website_signal_integration.py` | medium | Website signal capture is silent/fire-and-forget; user notice/opt-out is not visible. | source only | no | Review privacy notice and consent basis before production public use. |
| PPSR-AUD-006 | `.weslr` path authority | `weslr/advisor_review_queue_persistence.py`, `weslr/consolidation_promotion.py` | high | Advisor queue and promotion defaults can involve `.weslr` paths if called, while public-pilot lanes forbid `.weslr` IO. | source only | no | Govern path authority and prohibit public pilot flows from invoking `.weslr` writes. |
| PPSR-AUD-007 | promotion/release | `weslr/consolidation_promotion.py` | high | Promotion helper can write destination records when enabled; release-gate relationship for public feedback-derived outputs is unclear. | source only | no | Require review/operator/release-gate boundary before any feedback-to-promotion path. |
| PPSR-AUD-008 | review output | `weslr/review_interface.py` | medium | Interface strips top-level forbidden fields, but nested/private content and raw review log semantics remain unknown. | source only | no | Add nested redaction and safe-summary constraints in governance design. |
| PPSR-AUD-009 | OCW privacy | `weslr/docs/OCW_HANDOFF_V1.md` | medium | OCW deployment authority is documented, but pilot/suggestion/review storage access boundaries are not explicit. | docs only | no | Review OCW access boundary after storage/privacy governance design. |
| PPSR-AUD-010 | continuity storage sprawl | `continuity/**` | medium | Many continuity JSON artifacts exist beyond named pilot/suggestion paths; broader storage classification remains unknown. | path/metadata only | no | Include broader continuity storage classification in governance boundary or later audit. |
| PPSR-AUD-011 | docs/source mismatch | `weslr/PILOT_LAUNCH_RUNBOOK.md`, `weslr/pilot_signal_logger.py` | medium | Runbook lists retention durations, but source enforcement is not visible. | docs/source only | no | Convert docs-only retention into enforceable policy before use. |
| PPSR-AUD-012 | public readiness | existing surfaces | blocker | Existing surfaces are not currently safe for first-30 pilot without privacy/retention governance and targeted fixes. | source/docs/metadata only | no | Design boundary first, then implement narrow safety fixes. |

## 11. Public Pilot Readiness Impact

Status: `not ready`

WESLR cannot safely use the existing surfaces for a first-30 public pilot now. The reason is not lack of surfaces; the reason is unresolved storage/privacy/retention risk:

- high-risk suggestion and pilot storage paths exist;
- contact/user/session/free-text fields are possible from source schema;
- deletion, revocation, purge, anonymization, and backup handling are not visible;
- consent scope is absent or unsafe/unclear;
- redaction is partial and strongest only in website metadata/advisor summary paths;
- queue/promotion outputs are not clearly governed by release gates or public-feedback boundaries;
- OCW/deployment docs do not explicitly isolate private pilot storage.

Readiness could become conditionally viable after a governance boundary and safety-fix lane define and enforce consent, minimization, redaction, retention, deletion/revocation, queue output controls, and OCW storage access limits.

## 12. Recommended Next Lane

`DESIGN_PUBLIC_PILOT_STORAGE_PRIVACY_RETENTION_GOVERNANCE_BOUNDARY_V1`

Rationale: the audit found blocker-level gaps, but implementation should not start until the storage/privacy/retention governance boundary is explicit. A quarantine lane may be warranted if public use is imminent, but the next WESLR-needed step for public-readiness is to design the boundary that defines consent, redaction, deletion/revocation, retention, queue-output limits, `.weslr` exclusions, and OCW storage-access limits around existing surfaces.

## 13. Denied Authority

All values below are required false:

```yaml
permits_source_edits: false
permits_runtime_changes: false
permits_queue_processing: false
permits_database_row_reads: false
permits_database_writes: false
permits_raw_json_reads: false
permits_private_feedback_dump: false
permits_contact_export: false
permits_email_sending: false
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

## 14. Decision

`public_pilot_storage_privacy_retention_audit_complete_ready_for_review`
