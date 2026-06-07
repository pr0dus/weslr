# NOVA WESLR Deployment and Integration Discovery V1

**Date:** 2026-06-07  
**Repo:** `/home/pr0/projects/weslr-v1-ui-website`  
**Branch:** `ocw-weslr-v1-ui-20260529`  
**HEAD:** `6a96986`

**Status:** Discovery only. No deployment, no access changes, no website code.

---

## 1. Current Website Deployment Mechanism

### Detectable Services

| Port | Service | Purpose | Status |
|------|---------|---------|--------|
| 80 | nginx | Reverse proxy to Ollama | Active |
| 8080 | python3 | WESLR static site (weslr-v1-ui-website) | Active |
| 8082 | python3 | Ollama proxy (fallback) | Active |
| 8083 | python3 | PlantDelux site (e-qubs) | Active |
| 8091 | nginx | Staging area (requires auth) | Active |
| 8092 | python3 | Custom backend | Active |
| 8093 | python3 | Custom backend | Active |
| 8097 | python3 | e-qubs main site (PROTECTED) | Active |

### Current WESLR Serving Path
```
weslr.de → Cloudflare → nginx port 80 → port 8080 → weslr-v1-ui-website/
```

**Evidence:**
- `curl http://127.0.0.1:8080/` returns WESLR landing page
- `curl http://127.0.0.1:80/` returns "Ollama is running" (nginx proxy)
- WESLR static HTML files served from `/home/pr0/projects/weslr-v1-ui-website/site/`

### Deployment Type
**Static-first** — Current site serves pre-built static HTML files via Python HTTP server.

No build step detected:
- No `dist/` or `build/` directory
- No Vite/React production build in use
- Raw `site/` directory served directly

---

## 2. Is `site/` the Deploy Root?

✅ **YES** — `site/` is the static HTML deploy root.

**Evidence:**
- All public pages served from `site/`
- Static HTML files with embedded CSS (reset.css, variables.css, main.css)
- No middleware or templating layer detected
- Simple directory structure: `site/`, `site/about/`, `site/how-it-works/`, etc.

---

## 3. Is `weslr-ui/` React/Vite Active?

❌ **NO** — React/Vite is **planned**, not active.

**Evidence:**
- `weslr-ui/` exists but no `dist/` output
- `vite build` has not been run
- Current public site serves `site/` (static HTML), not React output
- Vite configured but unused in production

### Current State
- `weslr-ui/` = experimental/future React/Vite frontend
- `site/` = current production static HTML
- No React deployment yet

---

## 4. Docs: Static HTML or Generated Later?

### Recommendation: **Static HTML under `/docs/` for now**

**Rationale:**
- Current deployment is static HTML-first
- No build step exists yet
- Wiki markdown (`docs/WESLR_WHAT_WESLR_IS_NOT.md`) already created
- Future: consider generating docs from markdown to static HTML

### Current Docs Strategy
- **Markdown:** `/home/pr0/projects/weslr-core-source/docs/` (source of truth)
- **Static:** `/home/pr0/projects/weslr-v1-ui-website/site/` (public-facing)
- **Hybrid:** Keep markdown in `weslr/docs/`, create static HTML in `site/docs/`

### Proposed Structure
```
docs/                  # Markdown source (private, OCC)
site/docs/             # Generated static HTML (public)
  ├── index.html
  ├── doctrine/
  ├── architecture/
  ├── phases/
  └── operator/
```

---

## 5. Protected Chat UI at chat.weslr.de

### Current State
- `chat.weslr.de` → protected, requires password
- `staging.weslr.de` → protected, requires password
- No uninvited access
- No public self-registration

### Recommended Safe Path

**Phase 1: Planning Only**
- Review `WESLR_PROJECT_CHAT_RUNTIME_BOUNDARY_V1.md`
- Document access control requirements
- Design invite-only flow
- No active code deployment yet

**Phase 2: Static UI Wireframe**
- Create `site/chat/index.html` (invite-only entry point)
- Explain protected chat, invite process, access controls
- Link to protected routes (`staging.weslr.de`, `chat.weslr.de`)

**Phase 3: Future Integration**
- React/Vite chat UI (when `weslr-ui/` is built)
- OAuth/invite token system
- Signed-in/locked states
- No unauthenticated access

### Key Rule
**Any chat UI must:**
- Show invite-only status clearly
- Lock chat when user not authenticated
- No public self-registration links
- No open-public chat paths

---

## 6. Configs That Exist vs. Missing

### Existing Configs
| Config | Path | Status |
|--------|------|--------|
| nginx main | `/etc/nginx/nginx.conf` | Active |
| Python HTTP server | `python3 -m http.server 8080` | Active |
| Ollama proxy | nginx → port 11434 | Active |
| Cloudflare | DNS + proxy (external) | Active |

### Missing Configs
| Missing | Reason |
|---------|--------|
| Cloudflare page rules for `/docs/` | Future: redirect to static HTML |
| Vite build config for `weslr-ui/` | Future: React production build |
| chat.weslr.de proxy config | Future: integrate with chat UI |
| docs.weslr.de redirect rule | Future: if separate docs subdomain needed |

---

## 7. What Must Not Be Changed Without Owner Approval

### Absolutely Protected
| File/Service | Reason |
|--------------|--------|
| `site/privacy/` | Legal pages require separate approval |
| `site/terms/` | Legal pages require separate approval |
| `site/license/` | Legal pages require separate approval |
| `site/impressum/` | Legal pages require separate approval |
| `staging.weslr.de` | Protected route (password protected) |
| `chat.weslr.de` | Protected route (password protected) |
| Cloudflare config | DNS/access changes require approval |
| nginx config | Proxy rules may affect protected routes |
| `e-qubs.de` (port 8097) | User's main site, must not be touched |

### Access Requirements
- **No public self-registration** unless approved
- **No 50+ user claims** unless approved
- **No production-ready claims** unless approved
- **No open public pilot** unless approved
- **No provider/model/search/tool execution** unless approved

---

## 8. Next Safest Implementation Step

### Recommended: **Create `/docs/WESLR_WHAT_WESLR_IS_NOT.md` (wiki)**

**Already Done:**
- ✅ Created `docs/WESLR_WHAT_WESLR_IS_NOT.md`

### Optional: **Create static HTML entry for docs**

**If static HTML desired:**
- Create `site/docs/index.html` (docs home page)
- Link to markdown files (if public-safe)
- Or defer to future build step

### Recommended Action
**Do nothing more in this discovery lane.**

**Next safe step after owner review:**
1. If owner prefers static HTML docs: create `site/docs/` skeleton
2. If owner prefers wiki markdown: no action needed (already done)
3. Protected chat: planning only, no deployment

---

## Final Judgment

✅ `nova_weslr_deployment_and_integration_discovery_ready_for_first_safe_website_implementation`

**Recommended Next Lane:**
- `IMPLEMENT_NOVA_WESLR_DOCS_WIKI_SKELETON_V1` (if static HTML docs desired)
- `IMPLEMENT_NOVA_WESLR_PROTECTED_CHAT_PLANNING_V1` (planning only, no deployment)
- `IMPLEMENT_NOVA_WESLR_MATERIAL_EXAMPLE_V1` (add `/about-weslr/candidate-material-example/`)

---

*Discovery by Nova (MAIN_DISPATCHER) on 2026-06-07*  
*Based on local inspection, nginx configs, port mapping, and repo structure*
