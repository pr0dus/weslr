# NOVA WESLR Docs, Wiki, and Protected Chat Implementation Plan V1

**Date:** 2026-06-07  
**Repo:** `/home/pr0/projects/weslr-v1-ui-website`  
**Branch:** `ocw-weslr-v1-ui-20260529`  
**HEAD:** `9211434`

**Status:** Implementation plan only. No deployment, no access changes, no website code.

---

## 1. Current Website Structure Summary

| Area | Path | Status |
|------|------|--------|
| Home | `site/index.html` | ✅ Live |
| What is WESLR? | `site/about/index.html` | ✅ Live |
| About WESLR | `site/about-weslr/index.html` | ✅ Live |
| How It Works | `site/how-it-works/index.html` | ✅ Live |
| Governance | `site/governance/index.html` | ✅ Live |
| Product | `site/product/index.html` | ✅ Live |
| Roadmap | `site/roadmap/index.html` | ✅ Live |
| Pilot | `site/pilot/` | ✅ Live (access controlled) |
| Industrial Adaptation | `site/industrial-adaptation/index.html` | ✅ Live |
| Contact | `site/contact/` | ✅ Live |
| Privacy | `site/privacy/` | ✅ Live |
| Terms | `site/terms/` | ✅ Live |
| License | `site/license/` | ✅ Live |
| Impressum | `site/impressum/` | ✅ Live |
| Use Cases | `site/use-cases/` | ✅ Live |

**Navigation:**
- `/` → What is WESLR?
- `/about/` → What is WESLR?
- `/about-weslr/` → About
- `/how-it-works/` → How It Works
- `/governance/` → Governance
- `/product/` → Product
- `/roadmap/` → Roadmap
- `/pilot/` → Request Pilot Access

**Protected References (in current pages):**
- `staging.weslr.de` — password protected
- `chat.weslr.de` — password protected
- No public self-registration
- No open public pilot

---

## 2. Source Docs from Synced WESLR Core

**Source Path:** `/home/pr0/projects/weslr-core-source/docs/`

**Key Handoff Artifacts:**
| File | Purpose |
|------|---------|
| `NOVA_WESLR_DOCS_WIKI_AND_PROTECTED_CHAT_SOURCE_MAP_TO_PAGE_PLAN_V1.md` | Page-by-page plan with allowed/forbidden claims |
| `NOVA_WESLR_DOCS_WIKI_AND_PROTECTED_CHAT_SOURCE_MAP_TO_PAGE_PLAN_REVIEW_V1.md` | Review result (valid for review scope) |
| `NOVA_WESLR_HANDOFF_PACKET_V1.md` | Executive summary, responsibility split |
| `WESLR_NOVA_WIKI_INSTRUCTIONS_AND_PROTECTED_CHAT_HANDOFF_PLAN_V1.md` | Source map, source docs list |

**Public Identity Source Docs:**
- `WESLR_COGNITIVE_AI_POSITIONING_V1.md`
- `WESLR_PUBLIC_UX_CONTRACT_V1.md`
- `weslr/docs/WESLR_DOCTRINE_REGISTRY_V1.md`
- `WESLR_PUBLIC_UX_AUDIT_V1.md`

**Protected Chat Boundary:**
- `WESLR_PROJECT_CHAT_RUNTIME_BOUNDARY_V1.md`
- `WESLR_PROJECT_CHAT_RUNTIME_BOUNDARY_REVIEW_V1.md`
- `WESLR_PROJECT_CHAT_RUNTIME_BOUNDARY_HELPERS_REVIEW_V1.md`

**Claim Boundaries:**
- `WESLR_COGNITIVE_AI_POSITIONING_V1.md` — what WESLR is/is not
- `WESLR_PUBLIC_UX_CONTRACT_V1.md` — public site limits
- `WESLR_PUBLIC_PILOT_OCW_DEPLOYMENT_ACCESS_BOUNDARY_REVIEW_V1.md` — pilot access rules

---

## 3. Proposed Page/File Changes

### A. Reconcile `/about/` and `/about-weslr/`

**Recommendation:** **MERGE** — keep `/about/` as "What is WESLR?", remove `/about-weslr/`.

**Rationale:**
- `/about-weslr/` duplicates origin/mission content already present in `/about/`
- Current nav maps "What is WESLR?" to `/about/` — clear intent
- `/about-weslr/` adds redundant origin story with no unique content
- Cleaner structure: `/about/` for main explanation, `/contact/` for operator info

**Action in Implementation Lane:**
1. Move `/about-weslr/index.html` content into `/about/index.html` if any unique content exists
2. Update nav in all pages to remove `/about-weslr/` reference
3. Update footer links in all pages
4. Update `robots.txt` if needed

### B. Material Research Example Placement

**Recommendation:** **ADD TO `/about-weslr/` directory as a new subpage**, then redirect `/about-weslr/` to the example page.

**Rationale:**
- Current `/about-weslr/` page has placeholder content ("Origin", "Mission", "Development Posture")
- OCC source docs suggest material research as a **candidate workflow example**, not production-ready
- "Example: Evaluating a Candidate Material Idea" is public-safe phrasing
- Use `/about-weslr/` as the example page location (already exists, low public traffic)

**Content to Add:**
```html
<!-- Material Research Example Snippet -->
<div class="card">
  <h3 class="card-title">Example: Evaluating a Candidate Material Idea</h3>
  <p class="card-text">
    WESLR can help explore candidate material ideas using domain adapters. This is a planned direction, not a production feature.
  </p>
  <ul>
    <li>Concept → Proposal → Screening → Candidate Selection</li>
    <li>Domain-specific adapters (chemistry, physics, materials science)</li>
    <li>Traceable screening rules and candidate scoring</li>
  </ul>
  <div class="disclaimer">
    <strong>Status:</strong> Domain-specific adapters are a planned direction. No production adapters are currently available.
  </div>
</div>
```

**Files to Create:**
- `site/about-weslr/candidate-material-example/index.html`

**Files to Update:**
- `site/about-weslr/index.html` — rewrite as example引导 page with link to subpage

### C. What WESLR is Not Page

**Recommendation:** **ADD TO `/about/`** (as a subsection or new page under `/about/not/`).

**Rationale:**
- OCC source docs explicitly require "What WESLR is not" page
- Already implied in `/about/index.html` ("What WESLR Is Not" section)
- Standalone page improves clarity and SEO

**Action:**
- Create `/about/not/index.html` with clear forbidden claims list
- Update nav in `/about/index.html` to link to `/about/not/`

### D. Docs/Wiki Page Structure

**Recommendation:** Mirror `weslr/docs/` structure under `/docs/` directory.

**Proposed Structure:**
```
docs/
├── index.html                    # Overview / welcome
├── doctrine/                     # doctrine docs
│   ├── registry/index.html
│   └── ...
├── architecture/                 # architecture docs
│   ├── api/
│   ├── state/
│   └── ...
├── phases/                       # phase docs
│   ├── phase-1-chat-control/
│   ├── phase-2-governance/
│   └── ...
├── testing/                      # testing docs
│   ├── test-lane-audit/
│   └── ...
├── internal/                     # internal-use docs
│   └── ...
└── operator/                     # operator docs
    ├── observation/
    └── ...
```

**Public-Only Rule:**
- All pages under `/docs/` must be public-safe (no secrets, no `.weslr` state, no provider credentials)
- Private docs remain in `weslr/docs/` (not served via static site)

---

## 4. Files That Should Not Be Changed

### Absolutely Protected:
- `site/privacy/index.html` — legal pages require separate approval
- `site/terms/index.html` — legal pages require separate approval
- `site/license/index.html` — legal pages require separate approval
- `site/impressum/index.html` — legal pages require separate approval
- Any Cloudflare config or DNS records
- Any `.git` metadata files
- Any secrets, API keys, credentials in any file

### Legal Pages (Require Separate Approval):
- `site/privacy/` — must be reviewed by legal before any changes
- `site/terms/` — must be reviewed by legal before any changes
- `site/license/` — must be reviewed by legal before any changes

### Protected Routes (No Change):
- `staging.weslr.de` — password protected, owner-only
- `chat.weslr.de` — password protected, invited users only

---

## 5. Protected-Chat Boundary

### Allowed:
- Protected invite-only website chat surface
- Public-facing UI wiring behind access control
- Private owner preview flows
- Operator-controlled review surfaces
- Gated chat planning for invited users only

### Forbidden:
- Open public chat accessible to uninvited users
- Unauthenticated website chat
- Public self-registration
- 50-user pilot access unless separately owner-approved
- Production/public-ready claim
- Provider/model/search/tool execution claims

### Current State:
- `staging.weslr.de` — password protected ✅
- `chat.weslr.de` — password protected ✅
- No uninvited access ✅
- No public self-registration ✅

### Plan Requirement:
- Any new chat UI must preserve invite-only access
- No changes to `staging.weslr.de` or `chat.weslr.de` access controls
- No claims about production chat availability

---

## 6. Content/Claims Checklist

| Claim Type | Allowed? | Requirement |
|------------|----------|-------------|
| "WESLR is a governed intelligence system" | ✅ Yes | Must include "models are optional capability providers" |
| "WESLR maintains continuity across conversations" | ✅ Yes | Must specify "bounded memory" |
| "WESLR is conscious/AGI/beyond science" | ❌ No | Forbidden by `WESLR_COGNITIVE_AI_POSITIONING_V1.md` |
| "WESLR is production-ready" | ❌ No | Forbidden by `WESLR_PUBLIC_UX_CONTRACT_V1.md` |
| "WESLR has 50+ users" | ❌ No | Forbidden unless separately owner-approved |
| "WESLR discovered unknown intelligence" | ❌ No | Forbidden overclaim |
| "WESLR proves artificial general intelligence" | ❌ No | Forbidden overclaim |
| "WESLR uses LLMs" | ✅ Yes | Must clarify "models are optional" |
| "WESLR is for industrial domains" | ✅ Yes | With "planned direction, not production" disclaimer |

---

## 7. Material Research Example Placement Recommendation

**Location:** `/about-weslr/` (redirect/rename to example page)

**Content Title:** "Example: Evaluating a Candidate Material Idea"

**Key Phrases:**
- "planned direction, not production-ready"
- "candidate workflow example"
- "domain-specific adapters (planned)"
- "no production adapters currently available"

**No Claims About:**
- Discovery
- Proof
- Validation
- Confirmed material performance
- Production availability

**Wording Rule:** Use "Example:" prefix to clarify this is illustrative, not production.

---

## 8. `/about/` vs `/about-weslr/` Reconciliation Recommendation

**Decision:** **MERGE — keep `/about/` as main explanation, remove `/about-weslr/`**

**Reasoning:**
1. Current nav maps "What is WESLR?" to `/about/` — clear intent
2. `/about-weslr/` adds redundant origin story
3. `/about/index.html` already has origin, mission, development posture
4. Cleaner structure: `/about/` for explanation, `/contact/` for operator info

**Implementation Steps:**
1. Review `/about-weslr/index.html` for any unique content not in `/about/index.html`
2. If unique content exists, merge into `/about/index.html`
3. Remove `/about-weslr/` directory
4. Update all nav links from `../about-weslr/` to `../about/`
5. Update all footer links from `../about-weslr/` to `../about/`

---

## 9. Later Implementation Steps

### Phase 1: Site Restructure
- [ ] Reconcile `/about/` and `/about-weslr/`
- [ ] Add `/about/not/` (What WESLR is not)
- [ ] Add `/about/candidate-material-example/`
- [ ] Update all nav links
- [ ] Update all footer links
- [ ] Test with local `python3 -m http.server 8081`

### Phase 2: Docs/Wiki Pages
- [ ] Create `/docs/` directory structure
- [ ] Add `/docs/index.html`
- [ ] Add `/docs/doctrine/registry/index.html`
- [ ] Add `/docs/architecture/` pages
- [ ] Add `/docs/phases/` pages
- [ ] Add `/docs/testing/` pages
- [ ] Add `/docs/operator/` pages

### Phase 3: Protected Chat UI Planning
- [ ] Review `WESLR_PROJECT_CHAT_RUNTIME_BOUNDARY_V1.md`
- [ ] Draft protected chat UI flow
- [ ] Draft access control flow
- [ ] Draft invite-only user flow
- [ ] Draft owner/operator preview flow

### Phase 4: Telegram File Delivery (Every Lane)
**Rule:** For every lane that creates/edits files, send file over Telegram using:
```bash
openclaw message send \
  --channel telegram \
  --target <chat_id> \
  --media <path> \
  --force-document \
  --message "<lane_name> - <file_description>"
```

**Required Fields:**
- File path
- Command used (target redacted)
- Exit status
- Telegram message ID

**Do Not Claim Delivery Unless:**
- Exit status is `0`
- Telegram returns `✅ Sent via Telegram. Message ID: <id>`

---

## 10. Telegram File-Delivery Rule for Future Created Files

**Command Pattern:**
```bash
openclaw message send \
  --channel telegram \
  --target <chat_id> \
  --media <path> \
  --force-document \
  --message "<lane_name> - <file_description>"
```

**Verification:**
- Exit status must be `0`
- Must see `✅ Sent via Telegram. Message ID: <id>`
- Report: file path, command, exit status, message ID

**Do Not Claim Success Unless:**
- Telegram returns success message ID
- File exists at path
- No errors in stdout/stderr

---

## 11. Explicit Note: No Website Implementation Was Done in This Lane

**This lane is IMPLEMENTATION PLAN ONLY.**

**What Was Done:**
- Inspected current website structure
- Read latest source docs from `/home/pr0/projects/weslr-core-source/docs/`
- Identified reconciliation needs (`/about/` vs `/about-weslr/`)
- Identified material research example placement
- Documented protected-chat boundary
- Documented content/claims checklist
- Documented later implementation steps
- Documented Telegram file-delivery rule

**What Was NOT Done:**
- No website files were created or edited
- No HTML pages were modified
- No content was added to the site
- No deployment was attempted
- No Cloudflare changes were made
- No protected chat was accessed or modified
- No public access was opened

**Next Lane:** `SELECT_NOVA_WESLR_FIRST_DOCS_WIKI_PAGE_DRAFT_TARGET_V1` (or owner-approved alternative)

---

**Final Judgment:** `nova_weslr_docs_wiki_and_protected_chat_implementation_plan_ready_for_review`

**Recommended Next Lane:** `SELECT_NOVA_WESLR_FIRST_DOCS_WIKI_PAGE_DRAFT_TARGET_V1`

---

*Plan generated by Nova (MAIN_DISPATCHER) on 2026-06-07*  
*Source: OCC handoff packet, WESLR source docs, current website state*
