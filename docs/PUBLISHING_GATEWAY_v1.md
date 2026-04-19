# PUBLISHING GATEWAY — Phase 6 Architecture
**Version:** 1.0
**Date:** 2026-04-19
**Status:** Design — operator-approved external sharing only
**Bounded to:** Research artifact pipeline (R1–R5), not general `/chat` outputs

---

## 1. Target Use Cases

### 1.1 Universities
- Share research findings with academic collaborators for peer review
- WESLR acts as a research assistant: generates artifacts from observed governance data
- Recipient evaluates quality; WESLR does not claim peer-review status
- Artifact carries `draft_status: operator_review_required` until operator approves sharing

### 1.2 Laboratories
- Transfer structured technical memos to engineering teams
- Use researcher-mode render for technical accuracy
- Include confidence matrix so recipients can assess reliability
- Governance timeline provides methodological transparency

### 1.3 Collaborators
- Share working memos with trusted individuals for feedback
- Include plain-language summary so non-technical collaborators can engage
- Operator explicitly selects which memos to share

### 1.4 Public Readers
- One-directional read-only sharing: operator publishes a static artifact
- No live system access granted; no API exposure
- Always a fixed snapshot (PDF/HTML/JSON export), not a live session

**Invariants:**
- WESLR never initiates external sharing autonomously
- All sharing is operator-intentional and operator-approved
- No bulk broadcast or automated distribution

---

## 2. Publishing Package

### 2.1 Artifact Bundle Schema

A publishable bundle is a structured JSON document:

```json
{
  "bundle_id": "uuid-v4",
  "generated_at": "ISO-8601",
  "exported_at": "ISO-8601 or null",
  "exported_by": "operator_username or null",

  "research_question": "string",
  "draft_status": "operator_review_required | approved_for_collaborator | approved_for_public",
  "approval": {
    "approved_by": "operator username or null",
    "approved_at": "ISO-8601 or null",
    "output_mode": "collaborator | public | seminar",
    "note": "string or null"
  },

  "canonical_memo": { ... },
  "rendered_memo": {
    "mode": "researcher | student | seminar",
    "content": "string (rendered text)"
  },
  "confidence_matrix": {
    "meta": "string",
    "content": "string (Mermaid)"
  },
  "governance_timeline": {
    "meta": "string",
    "content": "string (Mermaid)"
  },
  "plain_language_summary": "string",

  "confidence_statement": "string (mandatory, e.g. 'This is a working draft. WESLR confidence: medium. Human review required before external use.')",
  "limitations_section": "string",
  "source_systems": ["weslr", "governance_watch", "event_timeline"],
  "weslr_version": "0.8.x"
}
```

### 2.2 What Is Included

| Component | Always | Collaborator | Public | Seminar |
|---|---|---|---|---|
| Canonical memo | ✅ | ✅ | ❌ (use rendered) | ✅ |
| Rendered memo | ✅ (researcher) | ✅ (mode selected) | ✅ (student/simplified) | ✅ (seminar slides) |
| Plain-language summary | ✅ | ✅ | ✅ | ✅ |
| Confidence matrix (Mermaid) | ✅ | ✅ | ❌ | ✅ |
| Governance timeline (Mermaid) | ✅ | ✅ | ❌ | ✅ |
| Approval block | ✅ | ✅ | ✅ | ✅ |
| Confidence statement | ✅ | ✅ | ✅ | ✅ |
| Limitations section | ✅ | ✅ | ✅ | ✅ |

---

## 3. Approval Gate

### 3.1 The Invariant

**No artifact bundle exits the system without explicit operator approval.**

This is architectural, not procedural. The system design enforces it.

### 3.2 Gate Stages

```
[Artifact Generated]
       ↓
[Operator Reviews Bundle]
       ↓
[Operator Selects Output Mode: collaborator | public | seminar]
       ↓
[Operator Adds Approval Note (optional)]
       ↓
[System Records Approval in Bundle]
  - approved_by (operator identity)
  - approved_at (timestamp)
  - output_mode
  - note
       ↓
[System Sets draft_status:
  approved_for_collaborator |
  approved_for_public]
       ↓
[System Enables Export Action]
       ↓
[Bundle Downloaded / Sent]
       ↓
[Audit Event Written: publish.exported
  with bundle_id, approved_by, output_mode, exported_at]
```

### 3.3 What the Gate Checks

1. **draft_status** — must not be `operator_review_required`
2. **approval block** — must have `approved_by` and `approved_at` non-null
3. **output_mode** — must match the intended recipient category
4. **confidence_statement** — must be present and non-empty
5. **export requested** — operator must have clicked an explicit export/send action

### 3.4 What the Gate Does NOT Do

- Does not automatically publish
- Does not send to recipients
- Does not grant access to live WESLR systems
- Does not modify the artifact after approval

### 3.5 Approval Storage

- Approval record stored inside the bundle JSON (not in a separate system)
- Written once, immutable after export
- An `audit.publish.exported` event written to `events.jsonl` with:
  - `bundle_id`
  - `approved_by`
  - `output_mode`
  - `exported_at`
  - `research_question` (hash if sensitive)

---

## 4. Output Modes

### 4.1 `internal_draft`
- Output: JSON bundle, all fields
- Status: `draft_status: operator_review_required`
- No approval required to generate
- Export blocked until operator reviews and approves

### 4.2 `collaborator`
- Output: JSON bundle or formatted Markdown
- Status: `draft_status: approved_for_collaborator`
- Requires approval gate completion
- Includes: researcher-mode render, all diagrams, full detail
- Confidence statement: "This is a working draft shared with collaborators. WESLR confidence: [level]. Please review before citing."

### 4.3 `public`
- Output: Simplified JSON or HTML page
- Status: `draft_status: approved_for_public`
- Requires approval gate completion
- Includes: student-mode render (simplified language), plain-language summary, confidence statement
- Excludes: Mermaid diagrams (technical), raw governance data
- Confidence statement prominently displayed: "This summary was generated by WESLR, an entity intelligence system. Confidence: [level]. This is not peer-reviewed research."

### 4.4 `seminar`
- Output: Slide package (Markdown or HTML)
- Status: `draft_status: approved_for_collaborator` or `approved_for_public` (operator choice)
- Requires approval gate completion
- Includes: seminar-mode render (6 slides), plain-language summary, confidence statement
- Speaker notes preserved
- Designed for presentation context

---

## 5. Risks

### 5.1 Accidental Leakage
**Risk:** An artifact in `draft` status is exported and shared before operator review.
**Mitigation:** Export button is disabled until `draft_status` is `approved_for_collaborator` or `approved_for_public`. The button never becomes active for `operator_review_required`.

### 5.2 Unreviewed Drafts Leaving System
**Risk:** Someone uses the API directly to fetch artifacts without going through the UI gate.
**Mitigation:** API endpoints check `draft_status` before returning exportable data. Unapproved bundles return `{error: "requires_approval"}` on export endpoints.

### 5.3 Unsupported Claims Presented as Fact
**Risk:** WESLR-generated claims are treated as verified conclusions.
**Mitigation:** Every artifact bundle includes a mandatory `confidence_statement` and `limitations_section`. The statement is non-optional and appears at the top of any formatted output.

### 5.4 Hidden Self-Publication
**Risk:** WESLR autonomously publishes artifacts to external services.
**Mitigation:** There is no publishing destination configured by default. Any external destination must be explicitly configured by the operator. No scheduled publishing exists. No webhook or API push is automatic.

### 5.5 Confidence Inflation
**Risk:** WESLR assigns itself high confidence to appear more authoritative.
**Mitigation:** Confidence levels are derived from evidence quality classes (strong_verified, grounded_reasoning, etc.), not self-assessed. The `confidence_matrix` in every bundle shows the evidence base transparently.

### 5.6 Operator Identity Confusion
**Risk:** Approval records don't clearly identify who approved.
**Mitigation:** Approval block requires operator username. If identity is unknown, approval is rejected. Authentication integration is operator-configured (future phase).

---

## 6. Build Order

### Phase 6.1 — Approval State Machine
**Files:** `main.py`, `dashboard/index.html`
- Add `draft_status` field to canonical memo (default: `operator_review_required`)
- Add `approval` block to bundle schema
- Add `GET /api/research/bundle/status?bundle_id=...` endpoint
- **Constraint:** No external transmission yet

### Phase 6.2 — Export Gate Enforcement
**Files:** `main.py`
- Block `POST /api/research/bundle/export` when `draft_status == operator_review_required`
- Return `{error: "requires_approval", draft_status: "operator_review_required"}`
- Enable export only when status is `approved_for_collaborator` or `approved_for_public`
- Write `audit.publish.exported` event to `events.jsonl` after successful export

### Phase 6.3 — Approval UI in Dashboard
**Files:** `dashboard/index.html`
- After generateMemo: show "Review & Approve" section
- Operator can inspect canonical memo, rendered output, diagrams
- "Approve for Collaborator" and "Approve for Public" buttons
- Each button sets `draft_status` and records `approved_by` + `approved_at`
- After approval: "Export Bundle" button becomes active

### Phase 6.4 — Bundle Generation
**Files:** `main.py`
- `POST /api/research/bundle/generate` — assembles canonical memo + current rendered output + diagrams into bundle JSON
- Applies output_mode transform (strip diagrams for public, etc.)
- Adds mandatory `confidence_statement` and `limitations_section`
- Validates all required fields present

### Phase 6.5 — Output Format Transforms
**Files:** `main.py`
- `POST /api/research/bundle/export?format=json` — raw JSON bundle
- `POST /api/research/bundle/export?format=markdown` — formatted Markdown
- `POST /api/research/bundle/export?format=html` — standalone HTML page
- All formats include the mandatory confidence statement

### Phase 6.6 — External Destination (Future/Optional)
**Files:** TBD
- Explicit webhook URL configured by operator in `publishing_config.json`
- Requires operator to explicitly enter destination URL
- No auto-discovery, no address book
- Operator must confirm before each send
- **Out of scope for initial Phase 6 build**

---

## 7. Key Invariants

1. **Operator approval is always required before external sharing.**
2. **No automatic publishing.** The system generates; the operator distributes.
3. **Evidence-first.** Artifacts are derived from governance observations, not invented.
4. **Confidence transparency.** Every artifact shows its evidence quality, limitations, and uncertainty.
5. **Audit trail.** Every export is recorded as `audit.publish.exported` in `events.jsonl`.
6. **Draft status is persistent.** An artifact remains in `operator_review_required` until explicitly upgraded by the operator.
7. **No live system access for external recipients.** Artifacts are static snapshots.
