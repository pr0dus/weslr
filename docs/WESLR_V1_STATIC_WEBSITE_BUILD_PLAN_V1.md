# WESLR V1 Static Website Build Plan V1

Date: 2026-05-29
Status: build plan only — no implementation
Purpose: Define plan for WESLR V1 static public website build

---

## 1. Build Objective

### 1.1 Primary Goal

Build a **static public explanation website** for weslr.de.

This website is:
- A static HTML/CSS/JS website
- A public explanation surface
- An honest description of WESLR's architecture, governance, and roadmap
- A pilot-interest collection point
- A governance and trust explanation

### 1.2 What This Is NOT

This website is **NOT**:
- A public pilot launch
- Production runtime
- A backend service
- A database application
- User authentication
- A benchmark/Turing/intelligence claim
- An autonomous system interface
- A chatbot deployment

### 1.3 Language Strategy

**English-first for V1:**

| Decision | Status |
|----------|--------|
| Primary language | English |
| Multilingual pages | Future/roadmap |
| Localization trigger | Based on observed traffic |

**Rationale:**
- English is canonical source language
- Outreach is international
- Multilingual adds complexity
- Observe traffic before adding languages

**Future language paths (not for V1):**
- `/en` (English canonical)
- `/de` (German)
- `/it` (Italian)
- `/zh` (Chinese)
- `/ja` (Japanese)
- Others based on traffic data

**Localization requires separate owner approval.**

### 1.4 Business/Legal Status

| Item | Status |
|------|--------|
| Current business | Owner has Nebengewerbe under e-qubs name |
| Business change | Owner intends to update/change in coming weeks |
| Legal discussion | Later dedicated discussion |
| Public legal wording | **Not finalized yet** |
| Final Impressum/Privacy/Terms | **Owner-blocking before public launch** |

**Important:**
- Do NOT finalize public legal wording yet
- Do NOT confuse WESLR with e-qubs publicly
- e-qubs.de remains **OFF LIMITS** operationally
- Final legal text requires separate owner approval

### 1.5 Staging First

Build sequence:
1. Build locally first
2. Preview locally
3. Deploy to staging (staging.weslr.de) after owner approval
4. Staging must be protected (password/IP restriction)
5. Deploy to production (weslr.de) after owner approval
6. Configure www.weslr.de redirect

### 1.4 Constraints

- **No public DNS changes** until owner approves
- **No runtime/backend work**
- **No official benchmark/Turing/intelligence claims**
- **No production readiness claims**
- **No secrets committed**

---

## 2. Build Location

### 2.1 Decided: Build Folder and Stack

**Owner has delegated build folder and static stack decisions to Nova.**

**Decisions:**

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Build folder | `/home/pr0/projects/weslr-v1-ui-website/site/` | Isolated from existing code |
| Static stack | Plain static HTML/CSS/JS | Minimal risk, easy review |

**Why plain static HTML/CSS/JS:**
- No backend dependency
- No build step complexity
- Easy to audit for claims
- Fast to load
- Easy to stage locally
- Easy to migrate later
- No framework lock-in
- Easier staging deployment

### 2.2 Directory Structure

```
/home/pr0/projects/weslr-v1-ui-website/
├── docs/                          # Documentation (existing)
│   ├── WESLR_V1_MASTER_DEFINITION_AND_WEBSITE_STRUCTURE_V1.md
│   ├── WESLR_V1_UI_COMPONENT_AND_VISUAL_INTERACTION_SPEC_V1.md
│   └── ...
├── site/                          # Static website (new)
│   ├── index.html                 # Home
│   ├── about/                     # What is WESLR?
│   │   └── index.html
│   ├── how-it-works/
│   │   └── index.html
│   ├── product/
│   │   └── index.html
│   ├── governance/
│   │   └── index.html
│   ├── roadmap/
│   │   └── index.html
│   ├── use-cases/
│   │   └── index.html
│   ├── industrial-adaptation/
│   │   └── index.html
│   ├── pilot/
│   │   └── index.html
│   ├── about-weslr/
│   │   └── index.html
│   ├── contact/
│   │   └── index.html
│   ├── privacy/
│   │   └── index.html
│   ├── terms/
│   │   └── index.html
│   ├── license/
│   │   └── index.html
│   ├── impressum/
│   │   └── index.html
│   ├── assets/
│   │   ├── css/
│   │   │   ├── reset.css
│   │   │   ├── variables.css
│   │   │   └── main.css
│   │   ├── js/
│   │   │   └── main.js
│   │   ├── images/
│   │   │   ├── logo.svg
│   │   │   ├── logo-dark.svg
│   │   │   ├── favicon.ico
│   │   │   └── og-image.png
│   │   └── fonts/
│   └── robots.txt
└── weslr/                         # WESLR core (existing, untouched)
```

### 2.3 Alternative: Dedicated Website Repository

If owner prefers isolation:
- Create new repo: `/home/pr0/projects/weslr-site/`
- Same structure as above
- Requires owner approval

### 2.4 Off-Limits

**Do NOT touch:**
- `/home/pr0/projects/weslr/` (WESLR core)
- `/home/pr0/projects/weslr-ui/` (if exists)
- `/home/pr0/weslr-landing/` (existing landing page)
- `/home/pr0/projects/plantdelux-site/` (PlantDelux)
- Any e-qubs or PlantDelux directories

---

## 3. Technology Choice

### 3.1 Recommended: Plain Static HTML/CSS/JS

**Pros:**
- No build step complexity
- No framework dependencies
- Maximum simplicity
- Easy to audit for claims
- Fast to load
- Easy to deploy anywhere

**Cons:**
- More manual work for repeated elements
- No component hot-reload

### 3.2 Alternative: Minimal Vite/Static Build

If owner prefers:
- Use Vite for static build
- Keep dependencies minimal
- No backend framework
- No database
- No auth implementation

**Vite structure:**
```
site/
├── index.html
├── src/
│   ├── main.js
│   ├── styles/
│   │   └── main.css
│   └── components/
│       ├── header.js
│       ├── footer.js
│       └── ...
├── vite.config.js
└── package.json
```

### 3.3 Technology Constraints

| Allowed | Not Allowed |
|---------|-------------|
| Plain HTML5 | Backend frameworks |
| Plain CSS3 | Database connections |
| Vanilla JavaScript | User authentication |
| Minimal Vite build | Server-side rendering |
| Static hosting | API endpoints |

### 3.4 No Backend Dependency

- No Node.js server
- No Python backend
- No database
- No authentication
- No API endpoints
- No environment variables for secrets

---

## 4. Page Build Order

### 4.1 Phase 1: Core Pages (Build First)

| Order | Page | Path | Priority |
|-------|------|------|----------|
| 1 | Home | `/` | Critical |
| 2 | What is WESLR? | `/about/` | Critical |
| 3 | Governance & Trust | `/governance/` | Critical |
| 4 | Pilot Interest | `/pilot/` | Critical |

### 4.2 Phase 2: Explanation Pages

| Order | Page | Path | Priority |
|-------|------|------|----------|
| 5 | How WESLR Works | `/how-it-works/` | High |
| 6 | Product Experience | `/product/` | High |
| 7 | Evaluation Roadmap | `/roadmap/` | High |

### 4.3 Phase 3: Detail Pages

| Order | Page | Path | Priority |
|-------|------|------|----------|
| 8 | Use Cases | `/use-cases/` | Medium |
| 9 | Industrial Adaptation | `/industrial-adaptation/` | Medium |
| 10 | About | `/about-weslr/` | Medium |
| 11 | Contact | `/contact/` | Medium |

### 4.4 Phase 4: Legal Pages

| Order | Page | Path | Priority |
|-------|------|------|----------|
| 12 | Privacy Policy | `/privacy/` | Required |
| 13 | Terms of Use | `/terms/` | Required |
| 14 | Commercial License | `/license/` | Required |
| 15 | Impressum | `/impressum/` | Required |

---

## 5. Content Source Mapping

### 5.1 Home Page

| Content | Source Doc |
|---------|------------|
| Hero headline | Master Definition |
| What WESLR Is / Is Not | Master Definition |
| Architecture Preview | Product UX |
| Governance & Trust Preview | UI Spec Section 3.6 |
| Evaluation Roadmap Preview | UI Spec Section 3.7 |
| Pilot Interest CTA | Pricing Discovery |
| Homepage Disclaimer | Claim Rules |

### 5.2 What is WESLR? Page

| Content | Source Doc |
|---------|------------|
| Definition | Master Definition |
| Core Characteristics | Master Definition |
| LLM Boundary | Non-LLM Identity |
| What WESLR Is Not | Master Definition |

### 5.3 How WESLR Works Page

| Content | Source Doc |
|---------|------------|
| Canonical Flow Diagram | Product UX |
| Stage Explanations | Product UX |
| Governance Boundary | UI Spec |
| Continuity Model | Product UX |

### 5.4 Product Experience Page

| Content | Source Doc |
|---------|------------|
| App Layout Preview | UI Spec |
| Chat/Workspace Model | UI Spec |
| File Handling Model | UI Spec |
| Memory/Continuity UX | UI Spec |
| Processing/Status States | UI Spec |

### 5.5 Governance & Trust Page

| Content | Source Doc |
|---------|------------|
| Governance Pillars | Master Definition |
| Evidence & Provenance | Product UX |
| Operator Authority | Product UX |
| Memory Boundaries | Product UX |
| Trust & Transparency | Master Definition |

### 5.6 Evaluation Roadmap Page

| Content | Source Doc |
|---------|------------|
| Current State | Master Definition |
| Near-Term Goals | Master Definition |
| Future Evaluation | Master Definition |
| No Benchmark Claims | Claim Rules |

### 5.7 Use Cases Page

| Content | Source Doc |
|---------|------------|
| Use Case Cards | Master Definition |
| Industrial Adaptation | Master Definition |

### 5.8 Industrial Adaptation Page

| Content | Source Doc |
|---------|------------|
| Adaptation Model | Master Definition |
| Private Deployment | Pricing Discovery |

### 5.9 Pilot Interest Page

| Content | Source Doc |
|---------|------------|
| Request Access Form | UI Spec Section 3.10 |
| Privacy Notice | Claim Rules |
| Pilot Consent | Pricing Discovery |

### 5.10 About Page

| Content | Source Doc |
|---------|------------|
| Mission Statement | Master Definition |
| Origin/Context | Master Definition |
| Contact Link | UI Spec |

### 5.11 Contact Page

| Content | Source Doc |
|---------|------------|
| Contact Methods | UI Spec |
| Contact Form | UI Spec |
| Response Time | UI Spec |

### 5.12 Legal Pages

| Content | Source Doc |
|---------|------------|
| Privacy Policy | UI Spec Section 3.13 |
| Terms of Use | UI Spec Section 3.13 |
| Commercial License | UI Spec Section 3.13 |
| Impressum | UI Spec Section 3.13 |

### 5.13 Logo/Visuals

| Content | Source Doc |
|---------|------------|
| Logo Mark | Logo Concept Brief |
| Color Palette | UI Spec Section 2.2 |
| Typography | UI Spec Section 2.3 |
| Forbidden Visuals | Logo Concept Brief |

---

## 6. Claim Validation Checklist

### 6.1 Forbidden Claims

Every page must avoid these phrases:

| Forbidden | Why |
|-----------|-----|
| "WESLR is an LLM" | Not an LLM |
| "WESLR is a better LLM" | Not an LLM |
| "WESLR is certified intelligence" | Not certified |
| "WESLR is Turing-test ready" | Not tested |
| "WESLR is benchmark-proven" | Not benchmarked |
| "WESLR is production-ready" | Not production-ready |
| "WESLR is public pilot live now" | Invite-only |
| "WESLR is fully autonomous" | Governed, not autonomous |
| "WESLR improves itself without approval" | Requires approval |
| "WESLR has unlimited upload" | Has limits |
| "WESLR is more reliable than competitors" | No comparison evidence |
| "WESLR never makes mistakes" | Unsupported |
| "WESLR is AI that never fails" | Unsupported |

### 6.2 Required Disclaimer

Every page must include in footer:

> "WESLR is in internal evaluation. No official test results claimed. No production guarantee. Pilot access by invitation."

### 6.3 Status Labels

Every feature must be labeled:

| Label | Usage |
|-------|-------|
| Implemented | Currently working |
| Designed | Planned, not yet built |
| Under Review | Being evaluated |
| Future Roadmap | Planned for later |
| Not Yet Authorized | Requires approval |

### 6.4 Claim Validation Process

Before each page deployment:
1. Read page content
2. Check against Forbidden Claims list
3. Check against Allowed Claims list
4. Verify Required Disclaimer present
5. Verify Status Labels correct
6. Document any exceptions

---

## 7. Legal/Privacy Placeholder Plan

### 7.1 Required Legal Pages

| Page | Required | Placeholder Until |
|------|----------|-------------------|
| Privacy Policy | **Yes** | Owner provides final text |
| Terms of Use | **Yes** | Owner provides final text |
| Commercial License | **Yes** | Owner provides final text |
| Impressum | **Yes** | Owner provides final text |

### 7.2 Placeholder Text

If final legal text is not ready, use placeholder:

**Privacy Policy (placeholder):**
> "Privacy Policy content is being finalized. Contact [contact email] for questions about data handling."

**Terms of Use (placeholder):**
> "Terms of Use content is being finalized. This website is for informational purposes only."

**Commercial License (placeholder):**
> "Commercial licensing terms are being finalized. Contact [contact email] for licensing inquiries."

**Impressum (placeholder):**
> "Impressum content is being finalized. Contact [contact email] for legal inquiries."

### 7.3 Blocking Before Public Launch

Legal placeholders are acceptable for:
- Local preview
- Staging preview (protected)
- Internal review

Legal placeholders are **NOT acceptable** for:
- Public launch
- Production deployment

**Owner must provide final legal text before public launch.**

### 7.4 Contact Page

| Element | Content |
|---------|---------|
| Contact email | Owner provides |
| Contact form | Optional (mailto: link is acceptable) |
| Response time | "We'll respond as soon as possible." |

### 7.5 Pilot Interest Consent

**Required consent text:**
> "I understand WESLR is in internal evaluation and pilot access is by invitation only. My information will be used to evaluate pilot interest."

**Links:** Privacy Policy, Terms of Use

---

## 8. Logo/Visual Plan

### 8.1 Accepted Logo Direction

| Element | Specification |
|---------|---------------|
| Variant | A + C combined |
| Mark Type | Minimal W-oar/vessel mark |
| Guiding Element | Small governance dot/star above center |
| Meaning | Evidence, operator authority, governance |
| Style | Monochrome-first |

### 8.2 Color Palette

| Color | Hex | Usage |
|-------|-----|-------|
| Primary Background | `#0D1117` | Dark navy base |
| Accent Blue | `#388BFF` | Primary accent |
| Accent Hover | `#58A6FF` | Interactive states |
| Text Primary | `#F0F6FC` | White text |
| Text Secondary | `#C9D1D9` | Light gray text |
| Success | `#39D353` | Approved/Ready |
| Warning | `#D29922` | Needs attention |
| Danger | `#F85149` | Blocked/Error |

### 8.3 Logo Files Needed

| File | Format | Size | Priority |
|------|--------|------|----------|
| weslr-logo-mark.svg | SVG | Vector | Critical |
| weslr-logo-mark-dark.svg | SVG | Vector | Critical |
| weslr-logo-wordmark.svg | SVG | Vector | High |
| weslr-logo-full.svg | SVG | Vector | High |
| weslr-favicon.ico | ICO | 16×16, 32×32 | Critical |
| weslr-icon-16.png | PNG | 16×16 | High |
| weslr-icon-32.png | PNG | 32×32 | High |
| weslr-icon-64.png | PNG | 64×64 | Medium |
| weslr-icon-128.png | PNG | 128×128 | Medium |
| weslr-icon-256.png | PNG | 256×256 | Low |
| weslr-icon-512.png | PNG | 512×512 | Low |

### 8.4 Logo Placeholder

If final logo files are not ready:
- Use text logo: "WESLR" in Inter or similar sans-serif
- Use placeholder SVG with "W" letter
- Mark as "Logo placeholder — final logo pending"

### 8.5 Forbidden Visual Elements

| Forbidden | Reason |
|-----------|--------|
| Robot heads | Generic AI cliché |
| Neural networks | Overused, misleading |
| Circuit boards | Wrong category |
| Sparkles/glitter | Not serious |
| Chatbot bubbles | WESLR is not a chatbot |
| Floating orbs | Generic tech |
| 3D effects | Not minimal |
| Neon colors | Not professional |
| Autonomous AI metaphors | WESLR is governed |

---

## 9. Staging Plan

### 9.1 Build Sequence

| Step | Description | Approval Required |
|------|-------------|-------------------|
| 1 | Build HTML/CSS/JS locally | No |
| 2 | Preview locally (localhost) | No |
| 3 | Owner reviews local preview | Yes |
| 4 | Deploy to staging.weslr.de | Yes |
| 5 | Owner reviews staging | Yes |
| 6 | Deploy to weslr.de | Yes |
| 7 | Configure www.weslr.de redirect | Yes |

### 9.2 Local Preview

| Tool | Command |
|------|---------|
| Python http.server | `python3 -m http.server 8080 --directory site/` |
| Node serve | `npx serve site/` |
| Vite preview | `npm run preview` (if using Vite) |

### 9.3 Staging Protection

**Required before staging deployment:**

| Method | Implementation |
|--------|----------------|
| Password protection | HTTP Basic Auth or Cloudflare Access |
| IP restriction | Allow owner IPs only |
| robots.txt | `User-agent: * Disallow: /` |
| Meta noindex | `<meta name="robots" content="noindex, nofollow">` |
| No public links | Do not share staging URL |

### 9.4 Staging DNS

Staging DNS configuration:
- Requires Cloudflare token
- Requires owner approval
- Do NOT configure without approval

---

## 10. Cloudflare/DNS Plan

### 10.1 DNS Targets

| Domain | Purpose | Current Status |
|--------|---------|----------------|
| weslr.de | Primary public website | NXDOMAIN — needs setup |
| www.weslr.de | Redirect to weslr.de | Active via Cloudflare |
| staging.weslr.de | Protected preview | Not configured |

### 10.2 DNS Configuration Plan

**weslr.de:**
- Option A: A record pointing to hosting IP
- Option B: CNAME to Cloudflare Pages
- Option C: Cloudflare tunnel
- **Requires:** Owner decision + Cloudflare token

**www.weslr.de:**
- Already active via Cloudflare
- Redirect to weslr.de (if not already)
- **Requires:** Cloudflare token

**staging.weslr.de:**
- Create DNS record after owner approval
- Protect with password/IP restriction
- **Requires:** Owner approval + Cloudflare token

### 10.3 Cloudflare Token Rules

| Rule | Status |
|------|--------|
| Use scoped token only | Required |
| weslr.de zone only | Required |
| No global API key | Forbidden |
| No PlantDelux access | Forbidden |
| No e-qubs access | Forbidden |
| Do not print token | Required |
| Do not commit token | Required |
| Store in local secrets | `/home/pr0/secrets/weslr_cloudflare.env` |

### 10.4 DNS Actions Require Owner Approval

| Action | Approval Required |
|--------|-------------------|
| Create A record for weslr.de | **Yes** |
| Create CNAME for weslr.de | **Yes** |
| Configure www.weslr.de redirect | **Yes** |
| Create staging.weslr.de record | **Yes** |
| Configure Cloudflare tunnel | **Yes** |

---

## 11. Off-Limits Boundary

### 11.1 Domains OFF LIMITS

| Domain | Reason |
|--------|--------|
| e-qubs.de | User's main business |
| www.e-qubs.de | User's main business |
| plantdelux.ro | Active PlantDelux site |
| www.plantdelux.ro | Active PlantDelux site |
| plant.plantdelux.ro | Active PlantDelux site |

### 11.2 Ports OFF LIMITS

| Port | Process | Reason |
|------|---------|--------|
| 8097 | e-qubs http.server | OFF LIMITS |
| 8083 | plantdelux http.server | OFF LIMITS |
| 8085 | PlantDelux email handler | OFF LIMITS |
| 8888 | SearXNG | OFF LIMITS |
| 11434 | Ollama | OFF LIMITS |

### 11.3 Processes OFF LIMITS

| PID | Process | Reason |
|-----|---------|--------|
| 262376 | e-qubs http.server | OFF LIMITS |
| 1418101 | plantdelux http.server | OFF LIMITS |
| 1673516 | PlantDelux email handler | OFF LIMITS |
| 993439 + workers | nginx | OFF LIMITS |
| 1677 | cloudflared | OFF LIMITS |

### 11.4 Services OFF LIMITS

| Service | Reason |
|---------|--------|
| nginx.service | Infrastructure |
| cloudflared.service | Infrastructure |
| ollama.service | Infrastructure |
| docker.service | Infrastructure |
| plantdelux-site.service | OFF LIMITS |

### 11.5 Safe Actions (Require Owner Approval)

| Action | Approval Required |
|--------|-------------------|
| Create DNS for weslr.de | **Yes** |
| Create Cloudflare tunnel for WESLR | **Yes** |
| Deploy to new port (8081, 8084, 8086) | **Yes** |
| Create nginx config for WESLR domain | **Yes** |

---

## 12. Pre-Build Owner Decisions

### 12.1 Decided by Owner

| Decision | Resolution |
|----------|------------|
| Build folder | `/home/pr0/projects/weslr-v1-ui-website/site/` |
| Static stack | Plain HTML/CSS/JS |
| Language strategy | English-first, localization future/roadmap |
| Business/legal status | Not finalized, separate discussion later |

### 12.2 Blocking Decisions (Require Owner Approval)

| Decision | Must Decide Before | Status |
|----------|-------------------|--------|
| DNS target/hosting location | Production deployment | ⏳ Open |
| Staging protection method | Staging deployment | ⏳ Open |
| Final legal language (Impressum, Privacy, Terms) | Public launch | ⏳ Open |
| Contact email for site | Build start | ⏳ Open |

### 12.3 Non-Blocking Decisions (Can Proceed with Defaults)

| Decision | Default | Can Change Later |
|----------|---------|------------------|
| Mockup vs text diagrams | Text diagrams | Yes |
| Contact form vs mailto | mailto link | Yes |
| Demo chat shown as disabled | Shown as "Not available" | Yes |
| Logo placeholder vs final | Placeholder | Yes |
| Multilingual support | English-only for V1 | Yes |

### 12.4 Decisions That Can Wait

| Decision | Can Wait Until |
|----------|----------------|
| Exact file/storage limits | After launch |
| Pricing wording | After launch |
| Demo chat enablement | Separate project |
| Invite login implementation | Separate project |
| Localization | Based on traffic data |

---

## 13. Scalability and Traffic Architecture

### 13.1 Beyond One Ubuntu Box

This plan thinks beyond a single Ubuntu server:

| Consideration | Approach |
|---------------|----------|
| Static assets behind Cloudflare | Yes, for V1 |
| Separate app/backend from website | Future stage |
| No unbounded uploads on local disk | Yes, never |
| Object storage or separate file storage | Future stage |
| Multiple backend origins | Future stage |
| Health checks | Future stage |
| Load balancing / traffic steering | Future stage |
| Staging separate from production | Yes, required |

### 13.2 Staged Architecture

**Stage 0: Static Local Preview**
- Build HTML/CSS/JS locally
- Preview on localhost
- No network deployment
- No DNS changes

**Stage 1: Protected Staging**
- Deploy to staging.weslr.de
- Password/IP protection required
- No public access
- No search engine indexing
- Owner review before production

**Stage 2: Public Static Site**
- Deploy to weslr.de
- Configure www.weslr.de redirect
- Static assets via Cloudflare
- No app/backend yet

**Stage 3: Invite-Only App/Backend (Separate)**
- Separate from public website
- app.weslr.de or chat.weslr.de
- Invite-only pilot
- Not part of V1 static website

**Stage 4: Object Storage + Backup/Retention**
- If file storage needed later
- Separate from web server
- Backup/retention policy defined
- Not part of V1

**Stage 5: Multiple Origins/Load Balancing**
- If traffic grows beyond single server
- Requires traffic data first
- Requires cost/benefit analysis
- Not part of V1

**Stage 6: Regional/Localized Expansion**
- If international traffic justifies
- Requires traffic/language data
- Requires localization approval
- Not part of V1

### 13.3 Traffic Observation

**Before buying another server, measure:**

| Metric | Tool |
|--------|------|
| Visits | Cloudflare Analytics |
| Countries/languages | Cloudflare Analytics |
| Page engagement | Cloudflare Analytics |
| Pilot requests | Form submissions |
| Bandwidth | Cloudflare Analytics |
| Failed requests | Cloudflare Analytics |
| Bot/spam traffic | Cloudflare Analytics |
| App/backend usage | If enabled later |

**Cloudflare Analytics Rules:**
- Use scoped WESLR token only
- Read-only access
- No DNS/tunnel writes
- No changes without owner approval

### 13.4 Scaling Triggers

| Trigger | Action |
|---------|--------|
| Traffic exceeds single server capacity | Evaluate Stage 5 |
| International traffic > 20% | Evaluate localization |
| Pilot requests exceed capacity | Evaluate backend scaling |
| Storage needs exceed local disk | Evaluate object storage |

---

## 14. Staging Protection Methods

### 14.1 Possible Methods (Not Implemented Yet)

| Method | Pros | Cons |
|--------|------|------|
| HTTP Basic Auth | Simple, widely supported | Credentials in URL, shared password |
| Cloudflare Access | No password management | Requires Cloudflare plan |
| IP Restriction | No password needed | Must know all IPs, dynamic IPs |
| VPN Required | High security | Requires VPN infrastructure |
| Obscure URL | Simple | Not real security |

### 14.2 Implementation Rules

**If password or access protection is needed:**
- Nova must ask owner at that moment
- Do NOT invent or commit passwords
- Do NOT print secrets
- Do NOT store secrets in repo
- Store credentials in local secrets file only

### 14.3 Staging Protection Approval

| Action | Owner Approval Required |
|--------|------------------------|
| Choose protection method | **Yes** |
| Set up password/auth | **Yes** |
| Configure IP restrictions | **Yes** |
| Deploy to staging | **Yes** |

---

## 15. Proposed Implementation Lane
| Mockup screenshots vs text diagrams | Text diagrams | ⏳ Open |
| Contact form vs mailto link | mailto link | ⏳ Open |
| Demo chat shown as disabled | Shown as "Not available" | ⏳ Open |
| Logo placeholder vs final logo | Placeholder | ⏳ Open |

### 12.3 Decisions That Can Wait

| Decision | Can Wait Until |
|----------|----------------|
| Exact file/storage limits | After launch |
| Pricing wording | After launch |
| Demo chat enablement | Separate project |
| Invite login implementation | Separate project |

---

## 13. Proposed Implementation Lane

## 15. Proposed Implementation Lane

### 15.1 Lane Name

`BUILD_OCW_WESLR_V1_STATIC_WEBSITE_PREVIEW_V1`

### 15.2 Lane Scope

| In Scope | Out of Scope |
|----------|--------------|
| Build static HTML/CSS/JS | Backend services |
| Create all 15 pages | Database/storage |
| Implement logo/visuals | User authentication |
| Local preview | Production deployment |
| Staging deployment (after approval) | DNS changes (without approval) |
| Legal placeholders | Final legal text (owner provides) |

### 15.3 Lane Prerequisites

Before implementation:
- [x] Owner approves build folder → **Decided: `/home/pr0/projects/weslr-v1-ui-website/site/`**
- [x] Owner approves static stack → **Decided: Plain HTML/CSS/JS**
- [ ] Owner approves logo direction
- [ ] Owner approves claim rules
- [ ] Owner approves staging protection method
- [ ] Owner provides contact email
- [ ] Owner provides or approves legal placeholders

### 15.4 Lane Dependencies

| Dependency | Owner Action |
|------------|--------------|
| DNS for weslr.de | Owner approves DNS configuration |
| DNS for staging.weslr.de | Owner approves DNS configuration |
| Hosting location | Owner decides: port, Cloudflare Pages, etc. |
| Staging protection | Owner decides: password, IP restriction, etc. |
| Cloudflare token | Owner approves token usage |

---

## 16. Validation Plan for Future Build

### 16.1 Pre-Deployment Validation

| Check | Method |
|-------|--------|
| No forbidden claims | Grep for forbidden phrases |
| Legal links present | Crawl for Privacy, Terms, Impressum |
| Homepage disclaimer | Manual review |
| Mobile layout | Test on mobile viewport |
| Accessibility | Keyboard navigation test |
| No hardcoded secrets | Grep for API keys, tokens, passwords |
| No runtime changes | Verify no weslr/chat_responder.py edits |
| No main.py changes | Verify no weslr/main.py edits |

### 16.2 Pre-Staging Validation

| Check | Method |
|-------|--------|
| Local preview works | Manual review |
| All pages load | Link checker |
| No broken links | Link checker |
| Forms submit (if applicable) | Manual test |
| Disclaimer visible | Manual review |
| Staging protection configured | Manual verification |

### 16.3 Pre-Production Validation

| Check | Method |
|-------|--------|
| Staging reviewed by owner | Manual review |
| DNS configured for weslr.de | Manual verification |
| No off-limits domain changes | Verify e-qubs, plantdelux untouched |
| No process changes | Verify processes still running |
| No secrets committed | Grep for secrets in git |

### 16.4 Post-Deployment Validation

| Check | Method |
|-------|--------|
| weslr.de loads | Manual review |
| www.weslr.de redirects | Manual review |
| All pages accessible | Crawl check |
| HTTPS working | Manual verification |
| No search engine indexing (staging) | robots.txt check |

---

## 17. Validation Commands

```bash
# Validate no Python syntax errors
python3 -m py_compile weslr/tests/release_gate_v1.py

# Run release gate
python3 weslr/tests/release_gate_v1.py

# Run release check
bash scripts/weslr_release_check.sh

# Verify chat_responder.py unchanged
git diff --quiet HEAD -- weslr/chat_responder.py

# Verify main.py unchanged
git diff --quiet HEAD -- weslr/main.py
```

---

## 18. Boundary Confirmations

- This is build plan only ✅
- No website code implemented ✅
- No site/ folder created ✅
- No weslr-ui/ changes ✅
- No dashboard changes ✅
- No runtime changes ✅
- No processes stopped ✅
- No cronjobs deleted ✅
- No DNS changes ✅
- No Cloudflare tunnel changes ✅
- No secrets committed ✅
- e-qubs.de untouched ✅
- plantdelux.ro untouched ✅
- weslr/chat_responder.py unchanged ✅
- weslr/main.py unchanged ✅

---

## 19. Recommended Next Lane

`REVIEW_OCW_WESLR_V1_STATIC_WEBSITE_BUILD_PLAN_V1`

---

## 20. Document Status

**Status:** Build plan only — no implementation
**Implementation:** Requires owner approval
**Changes Made:** Documentation update only

---

*End of WESLR V1 Static Website Build Plan V1*
git diff --quiet HEAD -- weslr/chat_responder.py

# Verify main.py unchanged
git diff --quiet HEAD -- weslr/main.py
```

---

## 16. Boundary Confirmations

- This is build plan only ✅
- No website code implemented ✅
- No weslr-ui/ changes ✅
- No dashboard changes ✅
- No runtime changes ✅
- No processes stopped ✅
- No cronjobs deleted ✅
- No DNS changes ✅
- No Cloudflare tunnel changes ✅
- No secrets committed ✅
- e-qubs.de untouched ✅
- plantdelux.ro untouched ✅
- weslr/chat_responder.py unchanged ✅
- weslr/main.py unchanged ✅

---

## 17. Recommended Next Lane

`REVIEW_OCW_WESLR_V1_STATIC_WEBSITE_BUILD_PLAN_V1`

---

## 18. Document Status

**Status:** Build plan only — no implementation
**Implementation:** Requires owner approval
**Changes Made:** None (documentation only)

---

*End of WESLR V1 Static Website Build Plan V1*