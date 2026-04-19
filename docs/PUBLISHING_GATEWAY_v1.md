# PUBLISHING GATEWAY — Phase 6 Review & Seal
**Version:** 1.1
**Date:** 2026-04-19
**Status:** ✅ SEALED — All phases implemented
**Bounded to:** Research artifact pipeline (R1–R5), not general `/chat` outputs

---

## 1. What Was Built

### Implemented Endpoints

| Endpoint | Method | Description |
|---|---|---|
| `/api/research/memos/generate` | GET | Generate canonical research memo from governance observations |
| `/api/research/memos/render` | POST | Render memo in researcher/student/seminar mode |
| `/api/research/diagrams/confidence-matrix` | POST | Confidence matrix Mermaid diagram |
| `/api/research/diagrams/governance-timeline` | GET | Governance timeline Mermaid diagram |
| `/api/research/memos/plain-language-summary` | POST | Plain-language version of memo |
| `/api/research/bundle/status` | GET | Bundle registration status lookup |
| `/api/research/bundle/generate` | POST | One-step full bundle generation |
| `/api/research/bundle/approve` | POST | Approve bundle for export |
| `/api/research/bundle/export` | POST | Export approved bundle (format可选) |

---

## 2. Approval State Machine

### States

```
operator_review_required  →  (approval required before export)
approved_for_collaborator →  (collaborator mode export allowed)
approved_for_public       →  (public mode export allowed)
```

### Transitions

| From | To | Trigger |
|---|---|---|
| `operator_review_required` | `approved_for_collaborator` | `POST /api/research/bundle/approve` with `output_mode=collaborator` |
| `operator_review_required` | `approved_for_public` | `POST /api/research/bundle/approve` with `output_mode=public` |

**No other transitions exist.** Registry is in-memory (max 20 entries), oldest evicted on overflow.

---

## 3. Bundle Registration

- `_BUNDLE_REGISTRY`: in-memory dict, max 20 entries, ring-buffer eviction
- Registered by: `_generate_research_memo()` (on LLM-success and fallback paths)
- Updated by: `/api/research/bundle/approve` (in-place mutation of registry entry)
- No persistence to disk (intentional — artifacts are generated on demand)
- Audit events written to `events.jsonl` via `_log_artifact_export_event()`

---

## 4. Hard Safety Invariants

These must NEVER be broken:

1. **Approval always required before export** — `/api/research/bundle/export` returns HTTP 403 `requires_approval` for any bundle with `draft_status == operator_review_required`
2. **No auto-approval** — generated bundles always start as `operator_review_required`
3. **No auto-publish** — no external destination, no webhook, no scheduled send
4. **Confidence statement mandatory** — every export bundle includes `confidence_statement`
5. **Limitations preserved** — `limitations_section` included in all format outputs
6. **Mode restrictions** — `public` output mode excludes Mermaid diagrams; only `collaborator` and `seminar` include diagrams
7. **Audit trail** — every successful export writes `governance.artifact.exported` to events.jsonl with bundle_id, output_mode, approved_by, research_question

---

## 5. Output Format Transforms

| Format | Content-Type | Description |
|---|---|---|
| `json` (default) | `application/json` | Full structured bundle |
| `markdown` | `text/markdown` | Readable document: summary, hypothesis, confidence, limitations, next steps |
| `slides` | `text/markdown` | Presentation-ready markdown with numbered slides and speaker structure |
| `collaborator_report` | `text/markdown` | Structured technical report: observations, evidence, confidence, diagrams |

**Mode restrictions apply to all formats:** diagrams only for `collaborator`/`seminar`, not `public`.

---

## 6. Mode Restrictions

| Component | Collaborator | Public | Seminar |
|---|---|---|---|
| Canonical memo | ✅ | ❌ (use student render) | ✅ |
| Student render | ❌ | ✅ | ❌ |
| Researcher render | ✅ | ❌ | ❌ |
| Seminar slides | ❌ | ❌ | ✅ |
| Plain-language summary | ✅ | ✅ | ✅ |
| Confidence matrix (Mermaid) | ✅ | ❌ | ✅ |
| Governance timeline (Mermaid) | ✅ | ❌ | ✅ |
| Confidence statement | ✅ | ✅ | ✅ |
| Limitations section | ✅ | ✅ | ✅ |

---

## 7. What Was Intentionally Excluded

These are NOT implemented and must not be added without a new design phase:

- **External destination sending** — no webhook URL, no email, no API push to external services
- **Bulk publishing** — one artifact at a time, operator-initiated only
- **Scheduled/automated dissemination** — no cron, no trigger-based export
- **External recipient management** — no address book, no contact storage
- **Status endpoint surfacing full approval object** — the status endpoint currently shows `draft_status` correctly but the `approval` block inside the status response returns nulls (display-only gap, non-blocking)
- **Persistence layer beyond in-memory registry** — bundle state is not written to disk; approval records are in-memory only
- **Approval revocation** — once approved, a bundle cannot be programmatically un-approved via the current API

---

## 8. Dashboard UI (Phase 6.3)

Located in `dashboard/index.html` — Research Panel:
- **Generate Memo** button → calls `/api/research/memos/generate`
- Plain-language summary displayed prominently
- Memo fields shown (hypothesis, confidence, limitations, next experiment)
- Render mode selector (Researcher / Student / Seminar)
- **Approval Status** display (unapproved/approved state)
- **Approve for Collaborator** and **Approve for Public** buttons → call `/api/research/bundle/approve`
- **Approval note** field (optional)
- **Export Bundle** button → disabled until approval succeeds, calls `/api/research/bundle/export`

**Note:** Export button gating is client-side only. The authoritative enforcement is server-side (HTTP 403 for unapproved bundles).

---

## 9. Known Gaps (Non-Blocking)

| Gap | Impact | Workaround |
|---|---|---|
| Status endpoint `approval` block returns nulls despite registry being correct | Display-only; export works correctly | Query the bundle via export to see full approval metadata |
| Registry is in-memory only — restart clears all registered bundles | Bundles lost on server restart | Regenerate bundles after restart; operator approval records not persisted |
| Approval revocation not available | Once approved, cannot programmatically un-approve | Restart server to clear registry (development) or add revocation endpoint in Phase 7 |
| No external destination — export is download-only | Operator must manually distribute files | Operator downloads and distributes via their own channel |

---

## 10. Regression Evidence

- **9/9 tests** pass in `weslr/test_chat_internal_routing.py`
- All 5 phases validated end-to-end:
  - Unapproved export → HTTP 403 `requires_approval` ✅
  - Approval → HTTP 200, registry updated ✅
  - Export after approval → HTTP 200, full bundle ✅
  - Audit event written → `governance.artifact.exported` in events.jsonl ✅
  - All 4 format transforms → HTTP 200, correct content ✅

---

## 11. Phase 7 Candidates

Bounded options for future work (not yet committed):

1. **External destination connector** — operator-configured webhook URL; explicit confirmation before each send; audit event includes destination
2. **Approval revocation endpoint** — `DELETE /api/research/bundle/approve?bundle_id=...` to revert to `operator_review_required`
3. **Persistent registry** — write bundle state to disk so approvals survive server restart
4. **Status endpoint fix** — surface full approval object in the status endpoint response body
5. **Collaborator report template** — refine the collaborator_report format based on operator feedback; potentially add PDF export

---

## 12. Invariants That Must Not Change

Without a new design document and operator review, these cannot be changed:

1. `operator_review_required` is the only valid initial state for a generated bundle
2. Export is always blocked for `operator_review_required` bundles (403 only, no bypass)
3. No automatic external sending — operator must always click an explicit export action
4. `confidence_statement` is always included in every format output
5. `limitations_section` is always included in every format output
6. Diagram content is only included for `collaborator` and `seminar` modes (not `public`)
7. `governance.artifact.exported` is written on every successful export

---

_Evolves when architecture is sealed, not on impulse. When this file changes, the operator knows a design decision has been made._