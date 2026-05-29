# WESLR V1 OCW Website Build Handoff V1

Date: 2026-05-29
Status: handoff / documentation only
Purpose: Complete OCW website build handoff package for controlled implementation

---

## 1. Build Objective

### 1.1 Primary Goal

Build the WESLR V1 **public explanation website**.

This website is:
- A public explanation surface
- An honest description of WESLR's architecture, governance, and roadmap
- A pilot-interest collection point
- A governance and trust explanation

This website is **NOT**:
- A public pilot launch
- Production runtime
- A benchmark/Turing/intelligence claim
- An autonomous system interface
- A chatbot deployment

### 1.2 Website Target

| Domain | Purpose | Status |
|--------|---------|--------|
| weslr.de | Primary public website | Needs DNS setup |
| www.weslr.de | Redirect to weslr.de | Active via Cloudflare |
| staging.weslr.de | Private/protected preview | Needs DNS + protection |

### 1.3 Scope

| In Scope | Out of Scope |
|----------|--------------|
| Static HTML/CSS/JS pages | Runtime implementation |
| Public explanation content | Public demo chat |
| Pilot interest form | Upload functionality |
| Governance/trust pages | Production deployment |
| Logo/branding implementation | Backend services |
| Responsive design | Database/storage |
| Accessibility baseline | User authentication |
| SEO basics | Public pilot launch |

### 1.4 Constraints

- **No production readiness claim**
- **No public pilot launch**
- **No autonomous system claim**
- **No benchmark/Turing/intelligence claim**
- **No unlimited upload claim**
- **No "better than competitors" claim**

---

## 2. Source-of-Truth Documents

### 2.1 Required Reading

Before implementation, read and follow these documents in order:

| Doc | Purpose | Path |
|-----|---------|------|
| Master Definition | Core definition, website structure, public wording rules | `docs/WESLR_V1_MASTER_DEFINITION_AND_WEBSITE_STRUCTURE_V1.md` |
| Master Definition Review | Validation of master definition | `docs/WESLR_V1_MASTER_DEFINITION_AND_WEBSITE_STRUCTURE_REVIEW_V1.md` |
| Product UX Operating Model | User experience, app shell, interaction patterns | `docs/WESLR_V1_PRODUCT_UX_AND_OPERATING_MODEL_V1.md` |
| Product UX Review | Validation of product UX | `docs/WESLR_V1_PRODUCT_UX_AND_OPERATING_MODEL_REVIEW_V1.md` |
| UI Component & Visual Spec | Detailed UI components, colors, typography, layouts | `docs/WESLR_V1_UI_COMPONENT_AND_VISUAL_INTERACTION_SPEC_V1.md` |
| Operations Boundary | Server/process/domain inventory, off-limits boundaries | `docs/WESLR_V1_WEBSITE_OPERATIONS_BOUNDARY_AND_PROCESS_INVENTORY_V1.md` |
| UI/Operations Review | Validation of UI and ops boundary | `docs/WESLR_V1_UI_SPEC_AND_WEBSITE_OPERATIONS_BOUNDARY_REVIEW_V1.md` |
| Logo/Icon Concept Brief | Brand direction, logo variants, color palette | `docs/WESLR_V1_LOGO_AND_ICON_CONCEPT_BRIEF_V1.md` |
| Non-LLM Identity Boundary | Public wording about LLMs | `docs/WESLR_V1_NON_LLM_IDENTITY_AND_OPTIONAL_MODEL_BOUNDARY_V1.md` |
| Pricing/Market Discovery | Pricing positioning, pilot model | `docs/WESLR_V1_PRICING_MARKET_AND_SCALABILITY_STRATEGY_DISCOVERY_V1.md` |

### 2.2 Document Hierarchy

```
Master Definition (highest authority)
├── Product UX Operating Model
│   └── UI Component & Visual Spec
├── Non-LLM Identity Boundary
├── Pricing/Market Discovery
└── Operations Boundary
    └── Logo/Icon Concept Brief
```

---

## 3. Approved Logo Direction

### 3.1 Owner Acceptance

**Accepted:** Variant A + C combined

| Element | Specification |
|---------|---------------|
| Mark Type | Minimal W-oar/vessel mark |
| Guiding Element | Small governance dot/star above center |
| Meaning | Evidence, operator authority, governance |
| Style | Monochrome-first |

### 3.2 Color Palette

| Color | Hex | Usage |
|-------|-----|-------|
| Primary Background | `#0D1117` | Dark navy base |
| Accent Blue | `#388BFF` | Primary accent |
| Accent Hover | `#58A6FF` | Interactive states |
| Text Primary | `#F0F6FC` | White text |
| Text Secondary | `#C9D1D9` | Light gray text |
| Success | `#39D353` | Approved/Ready states |
| Warning | `#D29922` | Needs attention |
| Danger | `#F85149` | Blocked/Error |

### 3.3 Forbidden Visual Elements

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
| Autonomous AI metaphors | WESLR is governed, not autonomous |

### 3.4 Logo Use Cases

| Context | Layout |
|---------|--------|
| Website header | Logo mark + wordmark |
| Favicon | Simplified mark only |
| App icon | Mark on dark background |
| Social avatar | Mark on accent or dark |
| Print | Full logo with tagline |

### 3.5 Logo Files Needed

| File | Format | Size |
|------|--------|------|
| weslr-logo-mark | SVG | Vector |
| weslr-logo-wordmark | SVG | Vector |
| weslr-logo-full | SVG | Vector |
| weslr-favicon | ICO | 16×16, 32×32 |
| weslr-icon-16 | PNG | 16×16 |
| weslr-icon-32 | PNG | 32×32 |
| weslr-icon-64 | PNG | 64×64 |
| weslr-icon-128 | PNG | 128×128 |
| weslr-icon-256 | PNG | 256×256 |
| weslr-icon-512 | PNG | 512×512 |

---

## 4. Website Pages to Build

### 4.1 Complete Sitemap

| Page | Path | Purpose |
|------|------|---------|
| Home | `/` | Hero, definition, architecture preview, CTA |
| What is WESLR? | `/about` | Definition, LLM boundary, core characteristics |
| How WESLR Works | `/how-it-works` | Architecture flow, governance detail |
| Product Experience | `/product` | App shell, chat/workspace, file handling |
| Governance & Trust | `/governance` | Evidence, operator authority, memory boundaries |
| Evaluation Roadmap | `/roadmap` | Current state, near-term goals, future evaluation |
| Use Cases | `/use-cases` | Industrial engineering, research, knowledge management |
| Industrial / Domain Adaptation | `/industrial-adaptation` | Domain adaptation, private deployment |
| Pilot Interest | `/pilot` | Request access form |
| About | `/about-weslr` | Mission, team context, contact |
| Contact | `/contact` | Contact methods, form |
| Privacy Policy | `/privacy` | GDPR-compliant privacy policy |
| Terms of Use | `/terms` | Acceptable use, limitations |
| Commercial License | `/license` | Commercial licensing terms |
| Impressum | `/impressum` | Legal impressum (German jurisdiction) |

### 4.2 Page Structure Summary

#### Home
- Hero section (headline, definition, CTA)
- What WESLR Is / Is Not
- Architecture Preview
- Governance & Trust Preview
- Evaluation Roadmap Preview
- Pilot Interest CTA
- No-Overclaim Disclaimer

#### What is WESLR?
- Definition section
- Core Characteristics (cards)
- LLM Boundary Explanation
- Related pages links

#### How WESLR Works
- Canonical Flow Diagram
- Stage Explanation Cards
- Governance Boundary Detail
- Continuity Model Explanation

#### Product Experience
- App Layout Preview
- Chat/Workspace Model
- File Handling Model
- Memory/Continuity UX
- Processing/Status States
- Privacy/Legal/User Control
- Roadmap Items

#### Governance & Trust
- Governance Pillars
- Evidence & Provenance
- Operator Authority
- Memory Boundaries
- Controlled Updates
- Trust & Transparency

#### Evaluation Roadmap
- Current State
- Near-Term Goals
- Future Evaluation Path
- No Benchmark Claims

#### Use Cases
- Use Case Cards
- Industrial/Domain Adaptation
- Contact CTA

#### Industrial / Domain Adaptation
- Adaptation Model
- Private/Institutional Deployment
- Contact CTA

#### Pilot Interest
- Request Access Form
- Alternative Contact
- Privacy Notice

#### About
- Mission Statement
- Origin/Context
- Team/Contact

#### Contact
- Contact Methods
- Contact Form
- Response Time Notice

#### Legal Pages
- Privacy Policy
- Terms of Use
- Commercial License
- Impressum

---

## 5. Public Claim Rules

### 5.1 Allowed Wording

| Allowed | Context |
|---------|---------|
| "WESLR is a governed intelligence system" | Definition |
| "WESLR is a continuity-first architecture" | Definition |
| "WESLR is evidence-aware" | Feature |
| "WESLR is operator-approved evolution" | Governance |
| "WESLR is in internal evaluation preparation" | Status |
| "Pilot interest / future pilot" | Availability |
| "Models are optional capability providers; WESLR is the governed system" | LLM boundary |
| "WESLR helps navigate uncertainty" | Metaphor |
| "WESLR connects memory, evidence, governance, and operator approval" | Architecture |
| "Pilot access by invitation" | Availability |

### 5.2 Forbidden Wording

| Forbidden | Reason |
|-----------|--------|
| "WESLR is an LLM" | Not an LLM |
| "WESLR is a better LLM" | Not an LLM |
| "WESLR is certified intelligence" | Not certified |
| "WESLR is Turing-test ready" | Not tested |
| "WESLR is benchmark-proven" | Not benchmarked |
| "WESLR is production-ready" | Not production-ready |
| "WESLR is public pilot live now" | Invite-only pilot |
| "WESLR is fully autonomous" | Governed, not autonomous |
| "WESLR improves itself without approval" | Requires approval |
| "WESLR has unlimited upload" | Has limits |
| "WESLR is more reliable than competitors" | No comparison evidence |
| "WESLR never makes mistakes" | Unsupported claim |

### 5.3 Status Labels

Every feature must be labeled:

| Label | Meaning |
|-------|---------|
| Implemented | Currently working |
| Designed | Planned, not yet built |
| Under Review | Being evaluated |
| Future Roadmap | Planned for later |
| Not Yet Authorized | Requires approval |

### 5.4 Homepage Disclaimer

**Required footer or bottom text:**

> "WESLR is in internal evaluation. No official test results claimed. No production guarantee. Pilot access by invitation."

---

## 6. Product/UX Boundaries

### 6.1 Public Website

| Allowed | Not Allowed |
|---------|-------------|
| Explain planned product experience | Claim implemented features |
| Show app shell mockups | Claim working demo |
| Describe chat/workspace model | Deploy working chat |
| Describe file handling | Enable file upload |
| Describe memory/continuity | Claim working memory |
| Show UI wireframes | Claim working app |

### 6.2 Public Demo

| Condition | Status |
|-----------|--------|
| Public demo chat | **Only if separately approved** |
| Upload on public demo | **Disabled unless separately approved** |
| Final pricing displayed | **No — pricing not finalized** |
| Pilot access | **By invitation only** |
| Storage/file limits | **Conservative limits apply** |
| Private deployments | **By discussion only** |

### 6.3 Feature Claims

| Claim | Allowed? |
|-------|----------|
| "WESLR has governance" | Yes — designed |
| "WESLR has evidence tracking" | Yes — designed |
| "WESLR has memory" | Yes — designed, bounded |
| "WESLR has operator approval" | Yes — designed |
| "WESLR works today" | **No — not production-ready** |
| "WESLR is live" | **No — invite-only pilot** |
| "WESLR never forgets" | **No — memory is bounded** |
| "WESLR is always right" | **No — uncertainty exists** |

### 6.4 Pricing Display

| Allowed | Not Allowed |
|---------|-------------|
| "Pilot by invitation" | Fixed pricing table |
| "Pricing evaluated with early users" | "€99/month" |
| "Contact for private deployment" | Storage limits commitment |
| "Limits apply" | "Unlimited upload" |

---

## 7. Operations Boundaries

### 7.1 Hard Off-Limits (NEVER Touch)

| Category | Component | Reason |
|----------|-----------|--------|
| Domain | e-qubs.de | User's main business |
| Domain | plantdelux.ro | Active PlantDelux site |
| Domain | www.plantdelux.ro | Active PlantDelux site |
| Domain | plant.plantdelux.ro | Active PlantDelux site |
| Port | 8097 | e-qubs.de static site |
| Port | 8083 | plantdelux.ro static site |
| Port | 8085 | PlantDelux email handler |
| Port | 8888 | SearXNG internal |
| Port | 11434 | Ollama local inference |
| Process | PID 262376 | e-qubs http.server |
| Process | PID 1418101 | PlantDelux http.server |
| Process | PID 1673516 | PlantDelux email handler |
| Process | PID 993439 + workers | nginx |
| Process | PID 1677 | cloudflared tunnel |
| Service | nginx.service | Reverse proxy |
| Service | cloudflared.service | Tunnel |
| Service | ollama.service | Local AI |
| Service | docker.service | Containers |
| Tunnel | cloudflared (PID 1677) | Serves e-qubs, plantdelux |

### 7.2 WESLR-Related (Approval Required)

| Component | Status | Action |
|-----------|--------|--------|
| weslr_demo_server.py (port 8080) | Running | Decision needed before changes |
| www.weslr.de | Active via Cloudflare | Safe to use for static site |
| weslr.de | NXDOMAIN | Needs DNS setup |
| staging.weslr.de | Not configured | Needs DNS + protection |

### 7.3 Safe Actions (Require Owner Approval)

| Action | Risk Level | Approval Required |
|--------|------------|-------------------|
| Create DNS for weslr.de | Low | Yes |
| Create new Cloudflare tunnel for WESLR | Medium | Yes |
| Deploy to new port (8081, 8084, 8086) | Low | Yes |
| Create nginx config for WESLR domain | Medium | Yes |
| Stop weslr_demo_server.py (port 8080) | Medium | Yes |

---

## 8. Cloudflare/API Key Boundary

### 8.1 Token Requirements

| Requirement | Value |
|-------------|-------|
| Token Type | Scoped API token |
| Scope | weslr.de zone only |
| Global API Key | **NEVER** |
| PlantDelux Access | **NONE** |
| e-qubs Access | **NONE** |

### 8.2 Token Permissions

| Permission | Allowed | Resources |
|------------|---------|-----------|
| Zone → DNS → Read | Yes | weslr.de only |
| Zone → DNS → Edit | Yes | weslr.de only |
| Zone → Zone → Read | Yes | weslr.de only |
| Zone → Analytics → Read | Conditional | weslr.de only |
| Account → Tunnel → Read | Conditional | Requires separate approval |
| Account → Tunnel → Edit | Conditional | Requires separate approval |

### 8.3 Token Storage

| Location | Allowed |
|----------|---------|
| Local secrets file | Yes |
| Environment variable | Yes |
| Git repository | **NEVER** |
| Public file | **NEVER** |
| Committed to code | **NEVER** |

### 8.4 Available Tokens

The following Cloudflare tokens are available in MEMORY.md:

| Token | Scope | Use |
|-------|-------|-----|
| Account API Token | `6e336599511057663a9087270b668f5a` | Weslr deployment |
| API Token (Weslr) | `cfat_G7pPx8E35IX5F27y2uGa9x8iwKvuUkaTujTPCKWv6a9fdb48` | Weslr DNS |

**Note:** These tokens must be used only for WESLR-related operations, never for PlantDelux or e-qubs.

---

## 9. Pre-Implementation Checklist

### 9.1 Before Starting Implementation

- [ ] All source-of-truth docs read and understood
- [ ] Logo direction accepted by owner
- [ ] DNS for weslr.de configured (A record or tunnel)
- [ ] Scoped Cloudflare token created for weslr.de
- [ ] Hosting location decided (port, Cloudflare Pages, etc.)
- [ ] Staging protection planned (password protection)
- [ ] Owner approval for build phase
- [ ] No changes to e-qubs.de infrastructure
- [ ] No changes to plantdelux.ro infrastructure
- [ ] No changes to existing cloudflared tunnel

### 9.2 Before Each Page Implementation

- [ ] Page structure defined in UI spec
- [ ] Public claim rules followed
- [ ] No forbidden wording used
- [ ] Status labels on all features
- [ ] Legal links included
- [ ] Homepage disclaimer included

### 9.3 Before Deployment

- [ ] All pages tested on mobile/tablet/desktop
- [ ] Accessibility baseline met
- [ ] Logo works in monochrome
- [ ] No hardcoded API keys
- [ ] No hardcoded secrets
- [ ] Legal pages present (Privacy, Terms, Impressum)
- [ ] Contact form functional (if applicable)
- [ ] Pilot Interest form functional (if applicable)

---

## 10. Technical Requirements

### 10.1 Technology Stack

| Layer | Recommendation |
|-------|----------------|
| Frontend | Static HTML5 + CSS3 + vanilla JS (or minimal framework) |
| Hosting | Static hosting (Cloudflare Pages, Netlify, or local nginx) |
| Domain | weslr.de (primary), www.weslr.de (redirect) |
| DNS | Cloudflare |
| SSL | Cloudflare Edge SSL |

### 10.2 Performance Requirements

| Metric | Target |
|--------|--------|
| First Contentful Paint | < 1.5s |
| Largest Contentful Paint | < 2.5s |
| Time to Interactive | < 3.5s |
| Cumulative Layout Shift | < 0.1 |
| Mobile-friendly | Yes |
| Accessibility | WCAG 2.1 AA baseline |

### 10.3 Browser Support

| Browser | Version |
|----------|---------|
| Chrome | Last 2 versions |
| Firefox | Last 2 versions |
| Safari | Last 2 versions |
| Edge | Last 2 versions |
| Mobile Safari | iOS 14+ |
| Mobile Chrome | Android 10+ |

### 10.4 Security Requirements

| Requirement | Implementation |
|-------------|----------------|
| HTTPS only | Cloudflare SSL |
| No hardcoded secrets | Environment variables |
| No API keys in code | Server-side only |
| Content Security Policy | Configure headers |
| XSS prevention | Escape user input |
| No user authentication | Static site (for now) |

---

## 11. Deployment Strategy

### 11.1 Staging

| Environment | Domain | Purpose |
|-------------|--------|---------|
| Staging | staging.weslr.de | Private preview for review |
| Production | weslr.de | Public website |

### 11.2 Staging Protection

| Method | Implementation |
|--------|----------------|
| Password protection | HTTP Basic Auth or Cloudflare Access |
| IP restriction | Allow owner IPs only |
| No public access | Block search engines |

### 11.3 Deployment Steps

1. Create DNS record for staging.weslr.de
2. Deploy to staging environment
3. Owner reviews staging site
4. Create DNS record for weslr.de
5. Deploy to production
6. Configure www.weslr.de redirect
7. Verify all pages load correctly

---

## 12. Legal Requirements

### 12.1 Required Pages

| Page | Content |
|------|---------|
| Privacy Policy | GDPR-compliant data handling |
| Terms of Use | Acceptable use, limitations |
| Commercial License | Commercial licensing terms |
| Impressum | Legal impressum (German jurisdiction) |

### 12.2 Required Footer Links

- Privacy Policy
- Terms of Use
- Commercial License
- Impressum
- Contact

### 12.3 Required Disclaimers

**Homepage:**
> "WESLR is in internal evaluation. No official test results claimed. No production guarantee. Pilot access by invitation."

**Pilot Interest Form:**
> "I understand WESLR is in internal evaluation and pilot access is by invitation only."

---

## 13. Open Owner Decisions

| Decision | Status | Note |
|----------|--------|------|
| DNS for weslr.de | ⏳ Open | Currently NXDOMAIN — blocks public access |
| Hosting location | ⏳ Open | New port? Cloudflare Pages? Separate server? |
| Staging protection plan | ⏳ Open | staging.weslr.de needs password/IP restriction |
| Scoped Cloudflare token | ⏳ Open | Required for DNS changes |
| Final legal language | ⏳ Open | German/English/bilingual TBD |
| Public demo chat enablement | ⏳ Open | Spec assumes disabled |
| Invite login by 02.08.2026 | ⏳ Open | Spec assumes invite-only |
| Uploads disabled until pilot | ⏳ Open | Spec assumes no public upload |
| Exact file/storage limits | ⏳ Open | Conservative defaults in spec |
| Pricing display wording | ⏳ Open | "Pilot by invitation" is safe default |
| Final logo files | ⏳ Open | Need vector designer |
| WESLR demo server (port 8080) | ⏳ Open | Still running — decision needed |

---

## 14. Pre-Build Requirements

### 14.1 Blocking vs Non-Blocking Decisions

| Decision | Blocks Build? | Note |
|----------|---------------|------|
| DNS for weslr.de | **Yes** | Cannot deploy without DNS |
| Hosting location | **Yes** | Cannot deploy without hosting |
| Staging protection | **Yes** | Should not expose staging publicly |
| Cloudflare token | **Yes** | Cannot configure DNS |
| Final legal language | **Yes** | Required pages incomplete |
| Public demo chat | **No** | Can proceed without demo |
| Invite login | **No** | Can proceed without login |
| Uploads policy | **No** | Can proceed without uploads |
| File limits | **No** | Conservative defaults in spec |
| Pricing wording | **No** | "Pilot by invitation" is safe default |
| Final logo | **Partial** | Can build with placeholder |
| Demo server decision | **No** | Separate from website |

---

## 15. Build Phase Proposal

### 15.1 Future Build Lane

**Lane:** `BUILD_OCW_WESLR_V1_PUBLIC_WEBSITE_STATIC_PREVIEW_V1`

**Status:** Defined but NOT executed

**This lane should:**
- Build static website first
- Use staging preview first (before production)
- Avoid backend/runtime changes
- Avoid DNS changes until owner approval
- Keep all claims aligned with canon
- Protect staging before public exposure

### 15.2 Build Phase Sequence

| Phase | Description | Approval Required |
|-------|-------------|-------------------|
| 1. Static Preview Build | Build HTML/CSS/JS locally | No |
| 2. Staging Deployment | Deploy to staging.weslr.de | Yes |
| 3. Owner Review | Owner reviews staging site | Yes |
| 4. DNS Configuration | Configure weslr.de DNS | Yes |
| 5. Production Deployment | Deploy to weslr.de | Yes |
| 6. Redirect Configuration | Configure www.weslr.de redirect | Yes |

### 15.3 Build Constraints

| Constraint | Reason |
|------------|--------|
| No backend/runtime changes | Static website only |
| No DNS changes until approved | Requires Cloudflare token |
| No database/storage | Static site only |
| No user authentication | Public website only |
| No demo chat unless approved | Spec assumes disabled |
| No file upload unless approved | Spec assumes disabled |

### 15.4 Staging Protection Requirements

Before staging deployment:

| Requirement | Implementation |
|-------------|----------------|
| Password protection | HTTP Basic Auth or Cloudflare Access |
| IP restriction | Allow owner IPs only |
| No search engine indexing | robots.txt + meta noindex |
| No public links | Do not share staging URL publicly |

---

## 16. Validation Before Build

### 16.1 Future Build Must Validate

Before each deployment phase:

| Check | Method |
|-------|--------|
| No off-limits domain changes | Verify no changes to e-qubs.de, plantdelux.ro |
| No PlantDelux/e-qubs process changes | Verify processes still running |
| No runtime changes | Verify no weslr/chat_responder.py or main.py edits |
| Website copy claim check | Verify all claims against canon docs |
| Legal/privacy links present | Verify Privacy, Terms, Impressum links |
| Mobile layout checked | Test on mobile/tablet/desktop |
| Staging preview checked | Owner reviews before production |

### 16.2 Claim Validation Checklist

| Claim Type | Validation |
|------------|-------------|
| "WESLR is governed" | Check against master definition |
| "WESLR is continuity-first" | Check against master definition |
| "WESLR is evidence-aware" | Check against master definition |
| "Pilot by invitation" | Check against pricing/UX docs |
| "Internal evaluation" | Check against master definition |
| "No production-ready" | Check claim rules |
| "No benchmark-proven" | Check claim rules |
| Homepage disclaimer | Check claim rules |

### 16.3 Technical Validation Checklist

| Check | Method |
|-------|--------|
| No hardcoded secrets | Grep for API keys, tokens |
| No hardcoded passwords | Grep for password strings |
| HTTPS only | Verify Cloudflare SSL |
| Accessibility baseline | Test keyboard navigation, contrast |
| Mobile responsive | Test on mobile viewport |
| Favicon present | Verify favicon files |
| Logo present | Verify logo files |

### 16.4 Deployment Validation Checklist

| Check | Method |
|-------|--------|
| Staging loads correctly | Manual review |
| All pages accessible | Crawl check |
| No broken links | Link checker |
| Forms submit correctly | Manual test |
| Legal pages present | Manual review |
| Disclaimer visible | Manual review |

---

## 17. Boundary Confirmations

- This is handoff/documentation only ✅
- No website code implemented ✅
- No weslr-ui/ changes ✅
- No dashboard changes ✅
- No runtime changes ✅
- No processes stopped ✅
- No cronjobs deleted ✅
- No DNS changes ✅
- No Cloudflare tunnel changes ✅
- e-qubs.de untouched ✅
- plantdelux.ro untouched ✅
- weslr/chat_responder.py unchanged ✅
- weslr/main.py unchanged ✅

---

## 18. Validation Commands

```bash
# Verify no Python syntax errors
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

## 19. Recommended Next Lane

`REVIEW_OCW_WESLR_V1_WEBSITE_BUILD_HANDOFF_V1`

**Note:** This handoff document requires review before owner approval for build phase.

---

## 20. Document Status

**Status:** Handoff / documentation only
**Implementation:** Requires owner approval
**Changes Made:** None (documentation only)

---

*End of WESLR V1 OCW Website Build Handoff V1*