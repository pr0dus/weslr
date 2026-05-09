# WESLR Public UX Audit V1

Date: 2026-05-09
Status: UX audit / product surface gap report / pre-implementation reference
Scope: public website, public demo chat, onboarding, continuity proof, workspace, institution onboarding

## Purpose

This document audits the current public-facing WESLR UX against `WESLR_PUBLIC_UX_CONTRACT_V1`.

It does not replace the UX contract. It translates the contract into a practical gap report and implementation sequence.

## Important correction

Onboarding is not obsolete.

Onboarding is strategically important because it is one of WESLR's core continuity mechanisms.

Correct framing:

```text
Public visitor UX ≠ onboarding UX
```

The public demo should be read-only and anonymous.

Onboarding should exist for users who want WESLR to know them, preserve continuity, personalize answers, and later prove what it knows through questions like:

```text
Who am I?
What do you know about me?
What are we working on?
What are my goals?
What are my red lines?
What should you avoid?
What kind of answers do I prefer?
```

So the issue is not that onboarding exists. The issue is that onboarding must be placed in the correct product flow.

## Correct UX architecture

Recommended public-to-continuity progression:

```text
1. Public demo
   Unknown visitor, read-only, no identity, no memory writes.

2. User onboarding
   Known user, creates profile and continuity anchors.

3. Workspace
   Uses identity, goals, preferences, red lines, projects, and remembered work.

4. Institution onboarding
   Adds company/team/project scopes, roles, permissions, deployment mode, and data-location choices.
```

This keeps privacy safe while preserving WESLR's actual value: continuity through identity, memory, goals, projects, and governance.

## Current surface audit

### Surface A — `weslr-ui`

Observed files:

```text
weslr-ui/src/App.tsx
weslr-ui/src/config.ts
weslr-ui/src/api.ts
```

Current strengths:

```text
public_demo_readonly mode exists
read-only banner exists
chat surface exists
example prompts exist
file upload is disabled by config
operator panel is disabled by config
public-demo API client is conservative
no memory/write actions are enabled in public mode
```

Current weaknesses:

```text
visual design is functional but not premium
layout feels like an internal app shell, not a public product landing/demo experience
left sidebar shows Projects / Files / Continuity even though those are not active public-demo capabilities
hero/storytelling is missing from the app shell
hosted vs private deployment is not visually explained
pricing/trial path is not prominent
public trust/privacy story is present but not emotionally/visually strong
starter prompts are useful but limited
mobile-first experience is not yet proven
loading/error states are basic
empty states are utilitarian
```

Verdict:

```text
`weslr-ui` is the best candidate for Public Demo Experience V1, but it needs a product-grade landing/chat redesign.
```

### Surface B — `front-door/index.html`

Observed characteristics:

```text
onboarding-style flow
dark premium visual direction
asks profile / mission / constraints / metrics / urgency / capability boundaries
mentions bounded autonomy, operator authority, red lines, audit, and governance
```

Current strengths:

```text
strong continuity/onboarding relevance
captures user identity and role
captures outcomes, red lines, legal/policy constraints, success metrics, urgency
supports future proof questions like who are you / what are we working on / what are my red lines
fits WESLR's continuity-first identity
```

Current weaknesses:

```text
not appropriate as the anonymous public landing page
too heavy for first visitor experience
not clearly separated from public demo mode
could make new visitors worry data is being collected before trust is established
does not present hosted trial / private deployment path clearly enough
uses wording closer to internal/operator setup than public product onboarding
```

Corrected verdict:

```text
`front-door/index.html` should not be discarded.
It should become or inspire User Onboarding V1 / Continuity Setup V1.
It should not be the first anonymous public demo screen.
```

## Product flow recommendation

### Phase 1 — Anonymous public demo

Purpose:

```text
explain WESLR
build trust
answer privacy/deployment questions
show WESLR is not another chatbot
offer trial/private-deployment next steps
```

Must stay:

```text
read-only
no identity capture required
no memory writes
no file upload
no operator controls
no deployment controls
```

Primary surfaces:

```text
public landing hero
read-only chat
starter prompts
hosted/private cards
pricing/trial card
trust/privacy section
contact/private deployment CTA
```

### Phase 2 — User onboarding

Purpose:

```text
create continuity anchors
establish user identity/profile
capture goals and answer preferences
capture red lines and constraints
prepare WESLR to answer continuity proof questions
```

Should be entered only after user chooses:

```text
Start trial
Create workspace
Set up WESLR for me
```

Key onboarding questions:

```text
What should WESLR call you?
What is your role/context?
What are you working on?
What kind of answers do you prefer?
What are your goals?
What are your red lines?
What should WESLR remember?
What should WESLR never do without approval?
```

### Phase 3 — Workspace

Purpose:

```text
turn onboarding into usable continuity
show current projects/goals/red lines
show what WESLR knows and why
allow user to correct or remove memory
provide continuity proof answers
```

Continuity proof questions:

```text
Who am I?
What do you know about me?
What are we working on?
What are my goals?
What are my red lines?
What did I correct before?
What do you remember from onboarding?
```

### Phase 4 — Institution onboarding

Purpose:

```text
map organization identity
set deployment model
set data-location expectations
set team/project/company scopes
set role-based access
set governance and approval flows
```

Institution-specific questions:

```text
What organization is this for?
Hosted or private/self-hosted?
Where must data reside?
Who owns the workspace?
Who can invite users?
What teams/projects exist?
What memories are personal vs shared?
What actions require approval?
Who controls updates?
```

## UX gaps by priority

### P0 — Public trust clarity

Current gap:

```text
The public UX has safe mechanics, but the trust story is not visually and narratively strong enough.
```

Needed:

```text
read-only demo badge always visible
clear boundary panel
plain-language privacy copy
hosted/private distinction
public demo limitations stated before interaction
```

### P0 — Public demo first-minute comprehension

Current gap:

```text
A visitor may not understand WESLR within 60 seconds from the current app shell alone.
```

Needed:

```text
hero sentence
short explanation
starter prompt cards
chat example
'not another chatbot' positioning
trial/private CTA
```

### P0 — Public demo vs onboarding separation

Current gap:

```text
Onboarding and public-demo entry are conceptually mixed across surfaces.
```

Needed:

```text
Public demo = anonymous/read-only
Onboarding = opted-in continuity setup
Workspace = personalized continuity
Institution onboarding = scoped organizational continuity
```

### P1 — Premium visual quality

Current gap:

```text
The UI is functional but not yet premium.
```

Needed:

```text
dark premium layout
clean hierarchy
better typography
better spacing
trust badges
polished chat bubbles
mobile layout
meaningful status indicators
```

### P1 — Better starter prompts

Current starter prompts are useful but incomplete.

Recommended public prompts:

```text
What is WESLR?
Are you just another chatbot?
Can WESLR remember me?
Where does company data go?
Can this demo upload files or run tools?
Can Claude or OpenClaw use WESLR?
Can WESLR improve itself automatically?
What does WESLR cost?
```

### P1 — Pricing/trial flow

Current gap:

```text
Pricing exists in public-demo response logic, but it is not yet a product-grade UX path.
```

Needed:

```text
1-month free trial card
€80/month per user after trial
private/institution quote CTA
explain why private pricing is quote-based
```

### P1 — Onboarding continuity proof

Current gap:

```text
The onboarding surface collects useful information, but the product flow does not yet prove continuity back to the user.
```

Needed:

```text
post-onboarding summary
'What WESLR learned' screen
editable memory/profile preview
sample questions: Who am I? What are my goals? What are my red lines?
clear delete/edit controls
```

### P2 — Institution install UX

Current gap:

```text
Private/institution deployment is explained conceptually, but not yet productized as a buyer journey.
```

Needed:

```text
Request private deployment form
deployment checklist
data-location options
role/access model explanation
support/wiki path
installation command path later
```

## Recommended implementation sequence

### Step 1 — Public Demo Experience V1 plan

Create a UI implementation plan for:

```text
landing hero
read-only chat panel
starter prompt cards
trust/privacy boundary box
hosted/private deployment cards
pricing/trial card
request private deployment CTA
```

### Step 2 — Public demo UI PRs

Small PRs only:

```text
PR A: improve starter prompts and boundary banner
PR B: add hero/trust/CTA layout around chat
PR C: polish chat surface and mobile layout
PR D: add hosted/private/pricing cards
```

### Step 3 — Onboarding V1 plan

Use `front-door/index.html` as inspiration for:

```text
User Onboarding V1
Continuity Setup V1
What WESLR learned summary
Continuity proof prompts
```

### Step 4 — Onboarding implementation

Only after public demo UX is clear.

### Step 5 — Institution onboarding plan

Design separate flow for:

```text
company/team/project scopes
data-location choices
roles and access
private deployment inquiry
```

## Do not do yet

```text
do not merge public demo and onboarding into one first screen
do not expose file upload in public demo
do not expose operator controls in public demo
do not imply memory writes before onboarding consent
do not begin whole-WESLR cognition UI until public demo UX is clear
do not start full institution install UX before public trust flow is understandable
```

## V1 verdict

```text
WESLR_PUBLIC_UX_AUDIT_V1_DEFINED
```

Summary:

```text
The public demo surface is safe but not yet premium.
The onboarding surface is strategically valuable, but belongs after trust and opt-in.
The next UX work should improve public demo first-minute comprehension while preserving onboarding as the continuity entry point.
```
