# WESLR V1 Product UX and Operating Model V1

Date: 2026-05-29
Status: design / documentation only
Based on: `docs/WESLR_V1_PRODUCT_UX_AND_OPERATING_MODEL_DISCOVERY_REPORT_V1.md`

## 1. Product posture

WESLR V1 is a public-interest product surface and operating-model design, not a full public autonomous runtime.

What the V1 website may do:
- explain the product direction
- show safe mockups and wireframes
- present a read-only demo or guided preview if separately approved and safe
- explain hosted vs private deployment paths
- collect pilot interest

What V1 must not claim:
- unrestricted production runtime
- automatic memory for everyone
- unlimited uploads or unbounded storage
- public intelligence/Turing/benchmark/certification status
- silent adaptive UI or hidden operator behavior

Live production claims remain blocked unless separately approved.

## 2. User entry model

### User states

- **Public visitor** — sees landing pages, product explanation, trust boundaries, and mockups
- **Pilot-interest user** — requests access, contact, or demo slot
- **Invited hosted user** — signed-in hosted user with limited workspace access
- **Private/institution deployment user** — organization-scoped user in a controlled deployment
- **Operator/admin** — internal governance and support role
- **Blocked/unsupported user** — access denied, unsupported plan, unsafe context, or policy block

### Access policy for V1

- Anonymous browsing: **allowed**
- Anonymous chat demo: **allowed only if explicitly approved as read-only/safe**; otherwise mockup-only
- Account login: **allowed as optional invite/request flow**, not open signup
- Invite-only access: **allowed** for hosted/private pilots
- Paid hosted accounts: **planned**, not fully billed in V1 unless billing/auth is separately implemented
- Private deployment access: **allowed by contract/quote and operator provisioning**

## 3. Login/account flow

### V1 target flow

1. Landing page
2. Product explanation / trust pages
3. `Request pilot access`
4. Optional `Sign in` for invited users
5. Account pending / approval state
6. Workspace entry after approval

### Visible pages

- **Sign in**
- **Request access**
- **Account pending**
- **Account disabled / blocked**
- **Contact support**

### Rules

- No unrestricted public signup unless separately approved
- Account creation is deferred unless billing/auth is explicitly designed later
- Public website may route users to contact/pilot forms without creating a live account

## 4. Main app layout

Canonical WESLR app layout:

- **Left sidebar**
- **Main chat / work area**
- **Right context / governance panel**
- **Top status / header**
- **Bottom input / action bar**

### Left sidebar

- conversations
- projects
- files
- continuity snapshots

### Center work area

- chat
- answer cards
- file cards
- workspace responses
- clarification cards
- blocked/governance cards

### Right panel

- context used
- evidence status
- memory boundary
- approvals
- source status
- safe process summary

### Top header

- workspace/project/account label
- mode badge
- trust/status indicator
- access/plan state

### Bottom bar

- input
- attach
- mode selector
- send
- safety/status notice

## 5. Chat visual model

### Presentation

- primary format: **bubbles with supporting cards**
- answer cards for structured output
- clarification cards for follow-up needs
- blocked/governance cards for boundary stops
- uncertainty cards when WESLR cannot safely answer

### Metadata behavior

- timestamps: visible on hover or as compact metadata, not noisy by default
- copy: available per message
- share/export: gated; must not expose private context by default
- source/evidence markers: visible when safe and useful

### Interaction

- ask follow-up: supported
- clarification prompts: supported
- mobile: single-column, stack-first, compact panel behavior

## 6. WESLR processing / thinking states

Visible states:
- Reading input
- Reading file
- Checking context
- Checking evidence
- Checking governance
- Waiting for approval
- Needs clarification
- Blocked by boundary
- Ready to answer
- Answer generated / answer not generated

### Display rule

- show a small status stepper or compact status pill
- no chain-of-thought exposure
- process summary only
- source/evidence status may be shown

## 7. File upload UX

### File locations in the UI

- left sidebar: **Files**
- current chat attachment strip
- project workspace file area
- file detail card

### File states

- uploaded
- pending scan
- accepted
- reading
- indexed / summarized
- unsupported
- too large
- corrupted
- blocked
- deleted
- expired

### File actions

- view metadata
- ask about file
- summarize
- remove from chat
- delete from workspace
- export metadata
- request full deletion later if implemented

## 8. File type policy

### V1 categories

- **Text**: txt, md
- **Documents**: pdf, docx if parser exists or future planned
- **Structured**: csv, json, yaml
- **Images**: png, jpg, webp if vision is in scope later
- **Unsupported**: everything else by default
- **Dangerous/executable**: blocked by default

### Unknown file behavior

- do not crash
- show an unsupported file card
- explain accepted formats
- do not process beyond safe metadata unless policy permits

## 9. File size and storage limits

Conservative V1 limits:

- Public demo: **no file upload**
- Pilot hosted trial: **10 MB per file**, **100 MB total per user** until policy is finalized
- Paid/pro hosted: higher limits only after storage policy exists
- Private deployment: customer-specific limit
- Enterprise/private: quote-based

### Limit rules

- max file size: product setting, conservative default first
- max files per workspace: defined by plan/contract
- max total storage per user: defined by plan/contract
- retention period: defined by plan/contract
- deletion policy: user-initiated, operator-compliant, auditable
- export policy: metadata/export where implemented
- cleanup policy: automatic cleanup only with explicit retention rules

### At limit

- block new uploads
- show quota notice
- offer deletion/export options where available
- do not silently discard data

## 10. Workspace model

### Core workspace objects

- user workspace
- projects
- conversations
- files
- continuity snapshots
- memory / knowledge area
- timeline / activity log

### Binding rules

- files belong to the workspace and may be attached to projects/conversations
- memory belongs to user/project/org only if explicitly approved
- public demo has no persistent workspace

## 11. Memory / continuity UX

Visible memory labels:
- Context used
- Continuity snapshot
- Project knowledge
- Remembered / not remembered
- Needs approval to remember

### Rules

- memory is bounded context, not automatic truth
- user can inspect context before trusting it
- memory write requires consent or an approved setting
- deletion/export only claimed if implemented and approved

## 12. Plans / licensing UX

### V1 public language

- Public website: information only
- Pilot interest: request access
- Hosted trial: possible future offer
- Private/institution deployment: contact
- Commercial license: contact

### Placeholder plan names

- Public demo: read-only / no upload / no memory
- Hosted pilot: invite-only / limited storage
- Professional/private: controlled deployment
- Enterprise/institution: custom deployment / governance

### Billing rule

Do not promise working billing unless it is implemented.

## 13. Privacy / legal placement

Required public pages / sections:

- Privacy Policy
- Terms of Use
- Commercial License
- Impressum
- Contact
- Data deletion / export request page or policy section
- Pilot interest consent notice
- File upload consent notice

### Placement

- footer
- signup / request-access page
- upload modal
- workspace settings
- account settings

## 14. Visual identity

### Direction

- dark-first premium interface
- calm industrial / research tone
- blue/cyan accent
- high contrast
- minimal motion
- no childish mascot/chatbot styling
- WESLR as serious governed intelligence infrastructure

### UI system

- logo placeholder/usage: small wordmark or text-lockup until final brand asset exists
- typography: clean sans-serif, strong hierarchy
- spacing: generous, calm, readable
- cards/panels: clear separation, soft borders, subtle elevation
- status colors: neutral, approved, warning, blocked, pending
- accessibility: contrast-first, readable at small sizes
- mobile: responsive baseline required

## 15. Adaptive interface

### Safe V1 adaptation

- user-selectable layout density
- show/hide context panel
- compact/detailed process view
- project-specific workspace labels
- accessibility settings

### Defer to V2

- silent auto-rearranging UI
- personality-based layout mutation
- persistent adaptive UI memory without explicit setting
- deep agentic interface changes

## 16. Deployment / scaling operating model

### Operating model

- public website: static hosting
- public demo: read-only
- app surface separated from backend
- uploads disabled until storage policy exists
- hosted users: quota enforced
- private deployments: separate storage possible
- future scaling: multiple app/backend instances and external object storage
- no unbounded Ubuntu local-disk upload model

### Rules

- storage quota rule: enforce per-plan/per-deployment quotas
- backup rule: backups required before retention changes or deletion policies
- retention rule: explicit retention window per deployment class
- server expansion principle: scale by adding capacity, not by removing safeguards
- monitoring/support principle: track quota, errors, latency, and upload failures

## 17. Mobile / accessibility baseline

- responsive layout required
- sidebar collapses on small screens
- right panel becomes a drawer or stacked section
- file cards remain readable on mobile
- keyboard navigation target
- contrast target must be high enough for readability
- no essential info should be conveyed by color alone

## 18. What V1 can show on website

### Allowed

- mockup screenshots / wireframes
- public explanation of planned UX
- read-only demo if safe
- pilot interest form
- architecture diagrams
- governance boundaries

### Forbidden

- unrestricted login / signup claims
- unlimited file upload
- production-ready workspace claims
- automatic memory claims
- official intelligence / Turing / benchmark claims
- public pilot live unless separately approved

## 19. Open decisions

Owner decisions still needed:

- exact pricing
- exact storage limits
- whether public demo chat is enabled
- whether invite-only login exists for 02.08.2026
- whether upload is entirely disabled until pilot
- whether to publish mockups or only concept diagrams
- legal text language: German / English / bilingual
- brand color / logo finalization

## 20. Recommended next lane

`REVIEW_WESLR_V1_PRODUCT_UX_AND_OPERATING_MODEL_V1`

## Boundary reminders

- `weslr/chat_responder.py` untouched
- `weslr/main.py` untouched
- no runtime behavior changes
- no controlled real answer sample execution
- no approval granted
