# WESLR UX Doctrine + Onboarding Contract V1

Date: 2026-05-09
Status: UX/product contract — no runtime or deployment changes
Scope: WESLR public surface, onboarding, chat experience, product feel, operator separation

## Purpose

This document defines the UX direction for WESLR before any major frontend implementation.

The goal is to make WESLR feel as polished and high-quality as major AI platforms such as ChatGPT and Claude, while remaining clearly different in purpose, structure, and trust model.

WESLR should not become a chaotic developer dashboard. It should become a calm, powerful, continuity-aware reasoning environment where chat is the main doorway and governed context is always nearby.

## Accepted UX principles

The following principles are accepted as baseline:

```text
calm
intelligent
continuous
trustworthy
operator-governed
personal but not fake-human
powerful but not noisy
chat-first, not dashboard-first
continuity-aware, not stateless-chat-only
governance-visible, not governance-overwhelming
operator-safe, not publicly exposed internals
```

## Product quality bar

WESLR should target the quality level users expect from modern AI platforms:

- fast perceived response
- clean typography
- strong spacing
- clear hierarchy
- excellent mobile behavior
- smooth onboarding
- consistent empty states
- graceful error states
- predictable navigation
- premium visual polish
- low cognitive load

The product should feel professional enough for researchers, institutions, industrial users, and serious independent operators.

## How WESLR differs from ChatGPT / Claude

ChatGPT and Claude generally feel like:

```text
chat → answer
```

WESLR should feel like:

```text
chat → context → memory → evidence → proposal → governed action
```

However, the user must not be forced to understand all internal machinery at once.

The advanced layers should appear progressively:

1. invisible when not needed
2. lightly visible as status/context
3. expandable when the user asks
4. operator-visible when the user has authority

## Primary interface rule

The primary interface is chat.

Everything else supports chat:

- continuity
- memory
- project context
- evidence
- proposals
- files
- domain tracks
- operator review
- deployment readiness

WESLR should not open with a dashboard full of controls. It should open with a calm conversational space that already knows which mode and context it is in.

## Canonical public surfaces

The product surfaces are:

```text
weslr.de         → public landing page / explanation / trust / pilot contact
chat.weslr.de    → WESLR chat app / demo / user workspace
staging.weslr.de → private validation surface before public exposure
```

### `weslr.de`

Purpose:

- explain WESLR
- establish trust
- show product tracks
- explain governance
- invite demo/pilot/contact

It should not look like a terminal, admin dashboard, or internal engineering tool.

### `chat.weslr.de`

Purpose:

- main interaction with WESLR
- onboarding entry for real users
- read-only public demo in first phase
- later authenticated user/institution workspace

It should be chat-first, continuity-aware, and visually premium.

### `staging.weslr.de`

Purpose:

- private validation
- pre-release testing
- operator/developer review
- deployment verification

It should not be treated as the public product.

## Public landing page journey

The first public journey should be:

```text
Visit weslr.de
  ↓
Understand what WESLR is in 10 seconds
  ↓
See why it is different from normal chatbots
  ↓
Choose one path:
  - Try read-only demo
  - Request pilot
  - Learn about product tracks
  - Contact / partner
  ↓
Enter chat.weslr.de or contact flow
```

## Landing page sections

Recommended order:

1. Hero
2. What WESLR is
3. Why continuity matters
4. Governed memory and traceable state
5. Product tracks
6. Safe public demo / pilot CTA
7. Trust and governance statement
8. Contact / request access

## Hero copy direction

Safe hero copy examples:

```text
WESLR is a continuity-first reasoning platform for long-running work.
```

```text
A governed intelligence layer for memory, evidence, proposals, and domain workflows.
```

```text
Not just chat. A structured reasoning environment that remembers work safely.
```

Avoid:

```text
AGI
conscious AI
fully autonomous self-improving AI
unhackable AI
replaces experts
learns from everyone automatically
```

## Product track presentation

WESLR currently has multiple product/research tracks. Public UX must separate them clearly.

| Track | Public name | Public explanation |
|---|---|---|
| Core WESLR | Continuity-first reasoning | Long-running memory, context, proposals, and governed state |
| Industrial/TIA | Industrial engineering memory | Siemens/TIA and automation data normalization track |
| Scatti/materials | Materials discovery support | Screening and validation support for computational materials candidates |
| Deployment Forge | Runtime/deployment validation | Controlled staging and deployment support for WESLR environments |

The landing page may show these as cards, but the first chat experience should not mix all tracks together by default.

## Onboarding doctrine

Onboarding is required for real WESLR use.

A user should not land in an empty generic chat unless they choose the read-only demo.

The onboarding purpose is to establish:

- who the user is using WESLR as
- what context WESLR should operate in
- what memory scope is allowed
- whether the session is personal, project, company, institution, or operator mode
- what WESLR may remember
- what WESLR may not do

## Onboarding modes

### Public demo mode

No account, no identity, no writes.

Flow:

```text
Open demo
  ↓
Show read-only mode notice
  ↓
Offer safe example prompts
  ↓
Chat with deterministic/read-only WESLR routes
```

### Individual user mode

For personal/project continuity.

Flow:

```text
Create/sign in
  ↓
Basic profile
  ↓
Choose primary purpose
  ↓
Choose memory comfort level
  ↓
Start first WESLR chat with context
```

### Institution/company mode

For teams, companies, laboratories, schools, or organizations.

Flow:

```text
Create organization / accept invite
  ↓
Define organization type
  ↓
Define role
  ↓
Define memory scopes
  ↓
Invite users or continue alone
  ↓
Enter organization workspace
```

### Operator/developer mode

For trusted operators only.

Flow:

```text
Authenticate as operator
  ↓
Show operator workspace
  ↓
Access proposals, diagnostics, deployment, governance, and internal surfaces
```

Operator mode must never be exposed to anonymous users.

## Onboarding questions

### Identity / usage context

```text
How are you using WESLR?
- As an individual
- For a project
- For a company
- For an institution/lab/university
- As an operator/developer
```

### Purpose

```text
What should WESLR help you with first?
- Remember and structure my work
- Manage project continuity
- Analyze technical/scientific material
- Support industrial engineering workflows
- Explore materials/science candidates
- Prepare/deploy a WESLR environment
```

### Memory comfort

```text
What may WESLR remember?
- Nothing yet
- Only this project context
- My preferences and working style
- Organization/team context
- Uploaded documents after review
```

### Governance preference

```text
How should WESLR handle changes?
- Suggest only
- Ask before saving memory
- Ask before system-changing actions
- Operator approval required for high-impact actions
```

Default should be conservative:

```text
Ask before saving important memory.
Ask before system-changing actions.
Never self-modify silently.
```

## First chat experience

The first real chat after onboarding should not be empty.

It should show:

- current mode
- current memory scope
- selected purpose
- what WESLR can do next
- safe example prompts

Example:

```text
You are in Project Memory mode.
Memory writes require confirmation.
You can ask WESLR to summarize context, organize tasks, compare evidence, or propose next steps.
```

## Chat window structure

The canonical chat window should have three conceptual layers.

### Center — conversation

Always primary:

- messages
- input box
- attachments if allowed
- response status
- example prompts

### Left — continuity/context

Secondary, collapsible:

- current project
- active memory scope
- recent continuity snapshots
- files/docs
- product track

### Right — insight/action panel

Contextual, hidden or minimized by default:

- evidence
- proposals
- next actions
- confidence/limitations
- operator review items if authorized

For public demo mode, the right panel should not expose operator internals.

## Public demo chat constraints

First public demo must be simple and safe.

Default public demo should include:

- read-only mode banner
- no file upload
- no memory writes
- no execution
- no LLM by default unless budget/guarded later
- example prompts
- limitations footer
- graceful fallback

Public demo should not include:

- operator proposal queue
- self-improvement queue
- deployment controls
- memory write controls
- real file upload
- API-key workflows
- organization invite/onboarding

## UX status badges

WESLR should use simple visible status badges to avoid confusion.

Examples:

```text
Read-only demo
No memory writes
No execution
Operator-reviewed changes
Experimental
Private workspace
Organization scope
Project memory enabled
```

These badges should be human-readable, not internal variable names.

## Error and fallback tone

Fallbacks must be calm and helpful.

Bad:

```text
Unhandled route error: deterministic_handlers failed.
```

Good:

```text
This demo only supports selected read-only WESLR routes. I can explain WESLR, show safe status information, or describe how governed memory works.
```

Do not expose stack traces, internal paths, handler names, API errors, or secrets.

## Mobile-first rules

Mobile UX must not be an afterthought.

Mobile order:

1. chat first
2. mode/status drawer
3. context drawer
4. files/projects later
5. operator panel inaccessible unless authenticated/operator mode

The three-panel desktop layout should collapse into a single-column chat-first experience.

## Operator separation

Public users should know WESLR is governed, but they should not see the operator machinery.

Public may see:

```text
System-changing actions require operator review.
```

Public should not see:

```text
internal proposal queues
self-improvement candidates
release gate internals
raw diagnostics
private memory graph
operator-only suggestions
```

Operator/admin surfaces must require explicit authority.

## Onboarding and entity model alignment

Onboarding should align with WESLR's entity-scoped memory model.

Supported future entity scopes:

- person
- project
- family/household
- company
- institution
- team/department
- laboratory/university

Roles must be explicit:

- owner
- admin
- member
- viewer
- operator
- researcher
- engineer
- project lead

Being part of an organization must not automatically grant access to all memories. Access depends on verified role, scope, and permission.

## Trust and privacy UX

Users must understand:

- what WESLR remembers
- when it writes memory
- when it needs approval
- what mode they are in
- what data is not stored
- what actions are blocked

Use plain-language trust text:

```text
WESLR does not silently change its core behavior. Important memory and system-changing actions require review.
```

## Public copy contract requirement

Before major frontend work, create:

```text
docs/PUBLIC_COPY_CONTRACT_V1.md
```

It should define:

- final hero copy
- product track descriptions
- safe claim list
- forbidden claim list
- demo disclaimer
- onboarding text
- error/fallback language
- CTA wording

## Wireframe contract requirement

Before implementation, create:

```text
docs/WESLR_PUBLIC_WIREFRAME_CONTRACT_V1.md
```

It should define:

- landing page wireframe
- read-only demo wireframe
- logged-in chat shell wireframe
- onboarding flow wireframe
- operator mode separation
- mobile layout

## First UX implementation recommendation

Do not redesign everything at once.

Recommended first implementation PR after inventory and wireframe:

```text
WESLR: add read-only demo UX shell
```

Minimal changes:

1. Add public read-only banner.
2. Add safe example prompts.
3. Add limitations footer.
4. Disable or hide file upload in public mode.
5. Keep operator panel unreachable unless operator mode.
6. Add mobile-first collapse behavior if missing.

## Assumptions made in this document

These assumptions are accepted unless the operator later changes them:

1. Chat remains the primary interface.
2. Onboarding belongs to the website/app, not only backend setup.
3. `weslr-ui/` is the likely canonical `chat.weslr.de` candidate, pending inventory.
4. Public demo starts read-only.
5. Real user mode requires onboarding before persistent memory.
6. Operator surfaces stay hidden from public users.
7. WESLR should reach major-AI-platform UX quality while keeping a distinct continuity/governance identity.

## V1 verdict

```text
WESLR_UX_DOCTRINE_AND_ONBOARDING_V1_DEFINED
```

WESLR's UX direction can now be decided at the doctrine level.

Next recommended steps:

1. Merge Public Surface UX Audit V1.
2. Merge this UX Doctrine + Onboarding Contract.
3. Create Public Surface Inventory V1 over actual frontend files.
4. Create Public Copy Contract V1.
5. Create Wireframe Contract V1.
6. Implement small read-only demo UX shell patch.
