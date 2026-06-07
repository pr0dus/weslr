# NOVA WESLR Docs Wiki Implementation Target Selection V1

**Date:** 2026-06-07  
**Repo:** `/home/pr0/projects/weslr-v1-ui-website`  
**Branch:** `ocw-weslr-v1-ui-20260529`  
**HEAD:** `f5a2615`

**Status:** Selection only. No website HTML created or edited.

---

## Selected Implementation Target

**Target:** Add `/about/not/` — "What WESLR is not"

**Priority:** First implementation target

**Rationale:**
- Reinforces public claim boundaries before adding examples or docs expansion
- Uses existing `/about/not/` suggestion in plan Section 3.C
- Clear forbidden claims list from OCC source docs
- Low risk — no access changes, no protected routes touched
- SEO and UX benefit — standalone page for "What WESLR is not"

---

## Files Expected to be Created/Changed in Next Lane

| File | Action | Purpose |
|------|--------|---------|
| `site/about/not/index.html` | Create | New "What WESLR is not" page |
| `site/about/index.html` | Optional edit | Add link to `/about/not/` |

**No other files expected to change in this lane.**

---

## Files That Must Not Be Changed

| File | Reason |
|------|--------|
| `site/privacy/index.html` | Legal pages require separate approval |
| `site/terms/index.html` | Legal pages require separate approval |
| `site/license/index.html` | Legal pages require separate approval |
| `site/impressum/index.html` | Legal pages require separate approval |
| `staging.weslr.de` | Protected route (no change) |
| `chat.weslr.de` | Protected route (no change) |
| Cloudflare config | No access changes |
| `.git` metadata | No modification |
| Secrets/API keys | No exposure |

---

## Source Docs to Use

**Source Path:** `/home/pr0/projects/weslr-core-source/docs/`

**Primary Docs:**
- `WESLR_COGNITIVE_AI_POSITIONING_V1.md` — forbidden claims list
- `WESLR_PUBLIC_UX_CONTRACT_V1.md` — public site limits
- `docs/WESLR_COGNITIVE_AI_POSITIONING_V1.md` — OCC positioning doctrine

**From Source:**
- WESLR is not conscious
- WESLR is not AGI/beyond science
- WESLR is not production-ready
- WESLR does not claim certified intelligence
- WESLR is not a benchmark-proven system

---

## Allowed Claims (for `/about/not/` page)

✅ "WESLR is not a normal chatbot wrapper"
✅ "WESLR is not consciousness/AGI/beyond science"
✅ "WESLR is not production-ready"
✅ "WESLR does not claim certified intelligence"
✅ "WESLR is not a benchmark-proven system"
✅ "WESLR does not claim 50+ users without approval"

---

## Forbidden Claims (must NOT appear on `/about/not/`)

❌ "WESLR is conscious"
❌ "WESLR discovered unknown intelligence"
❌ "WESLR is beyond science"
❌ "WESLR proves artificial general intelligence"
❌ "WESLR uses provider/model/search/tool execution"
❌ "WESLR has live retrieval"
❌ "WESLR is self-improving"
❌ "WESLR has .weslr state exposed"
❌ "WESLR has hidden prompts"
❌ "WESLR has secrets or API keys"

---

## Telegram Delivery Requirement

**Command:**
```bash
openclaw message send \
  --channel telegram \
  --target 2096877071 \
  --media docs/NOVA_WESLR_DOCS_WIKI_IMPLEMENTATION_TARGET_SELECTION_V1.md \
  --force-document \
  --message "NOVA_WESLR_DOCS_WIKI_IMPLEMENTATION_TARGET_SELECTION_V1 - Implementation target selected"
```

**Verification:**
- Exit status must be `0`
- Must see `✅ Sent via Telegram. Message ID: <id>`

---

## Validation Requirements

- ✅ `git diff --check` → pass
- ✅ `git status --short` → checked
- ✅ No website HTML edited yet
- ✅ No Cloudflare/DNS access changed
- ✅ No protected routes accessed

---

## Recommended Next Lane

**Next Lane:** `IMPLEMENT_NOVA_WESLR_WHAT_WESLR_IS_NOT_PAGE_V1`

**What This Lane Does:**
- Create `site/about/not/index.html`
- Optionally update `site/about/index.html` to link to `/about/not/`
- Keep legal pages untouched
- Keep protected routes untouched

---

**Final Judgment:** `nova_weslr_docs_wiki_implementation_target_selected_ready_for_first_page_implementation`

---

*Selection by Nova (MAIN_DISPATCHER) on 2026-06-07*  
*Based on plan from OCC handoff packet and owner corrections*
