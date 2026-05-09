# WESLR Public UX Contract V1

Date: 2026-05-09
Status: UX/product contract / pre-implementation reference
Scope: public website, public demo, onboarding entry, trust/privacy messaging, hosted vs private positioning

## Purpose

This document defines the public UX direction before more UI coding.

WESLR already has a safer public-demo contract and public-demo evaluation floor. It does not yet have a premium public product UX comparable in quality to major AI platforms.

This contract prevents random styling work and keeps the public experience aligned with WESLR's identity, privacy posture, deployment model, and cognitive-AI positioning.

## Current UX reality

Current estimated state:

```text
Public-demo logic:        strong foundation
Public-demo UX:           early / incomplete
Website/product UX:       early / incomplete
Institution install UX:   not productized
Full WESLR app UX:        not productized
```

What exists now:

```text
public-demo read-only safety
public-demo deterministic responder
public-demo short conversation suites
public-demo longform conversation suite
saved public-demo baselines
public-demo policy gates
basic website / UI surfaces in repo
```

What is not yet solved:

```text
polished first impression
premium chat experience
website onboarding
account/workspace flow
hosted trial flow
private deployment buyer journey
institution install UX
clear pricing journey
full trust/privacy storytelling
strong empty/loading/error states
operator/admin UX
```

## Primary public UX goal

The public UX must make a visitor understand this within the first minute:

```text
WESLR is not another chatbot.
WESLR is a continuity-first cognitive AI system for long-running work, governed memory, evidence, proposals, approvals, and compatible agents.
```

The user should also understand:

```text
The public demo is read-only.
Private/company data is not handled by the public demo.
Hosted WESLR is fastest to start.
Private/self-hosted WESLR is for organizations that need control over data location, runtime, access, updates, and integrations.
```

## UX principles

### 1. Premium but calm

WESLR should feel serious, high-trust, and modern.

Avoid:

```text
gimmicky AI magic
busy dashboards
excessive neon/cyberpunk
claiming consciousness
claiming AGI
claiming hidden abilities
```

Prefer:

```text
calm dark premium surface
clear hierarchy
high contrast text
soft motion
minimal but meaningful visual system graphs
engineering-grade credibility
```

### 2. Chat first

The public experience should lead toward a chat window with WESLR.

The first interactive moment should feel like:

```text
Ask WESLR what it is.
Ask how memory works.
Ask what private deployment means.
Ask how agents can use it.
Ask what this public demo can and cannot do.
```

Do not bury the chat behind complex menus.

### 3. Trust before power

Before showing advanced claims, the UX must show boundaries.

Public demo must clearly say:

```text
read-only
no file upload
no private memory writes
no operator controls
no deployment controls
no external provider calls by default
no hidden access to private data
```

### 4. Separation of public demo vs full WESLR

Public demo UX must not imply that the public demo is the whole product.

Use a clear distinction:

```text
Public demo:
Read-only explanation and safe conversation surface.

Hosted WESLR:
Individual/team product with account, workspace, memory, and integrations.

Private/institution WESLR:
Deployment for organizations needing data-location/runtime/access/update control.
```

### 5. No unsupported overclaims

The UX may say:

```text
continuity-first cognitive AI system
measurable cognitive capabilities
benchmarkable reasoning tasks
governed memory
structured evidence and proposals
compatible agent support direction
```

The UX must not say:

```text
WESLR is conscious
WESLR is AGI
WESLR discovers unknown human languages
WESLR can access your files in demo
WESLR can deploy changes from demo
WESLR can silently remember everything
```

## Target visitors

### Visitor A — Curious individual

Questions:

```text
What is WESLR?
How is it different from ChatGPT or Claude?
Can it remember my work?
Can I try it safely?
What does it cost?
```

UX must answer:

```text
WESLR focuses on continuity, governed memory, and long-running work.
The public demo is safe/read-only.
Hosted trial is the fastest way to start.
```

### Visitor B — Technical buyer / founder / engineer

Questions:

```text
Can WESLR connect to tools or agents?
Can it reduce repeated context/token waste?
Can it preserve project decisions?
Can I self-host it?
What are the architecture boundaries?
```

UX must answer:

```text
WESLR can complement compatible agents/tools through continuity, governed memory, evidence, proposals, and compact task context.
Private/institution deployments are for deeper integrations.
```

### Visitor C — Institution / company

Questions:

```text
Where does our data go?
Can it run privately?
How are access and memory governed?
Who controls updates?
Can it be installed in our environment?
```

UX must answer:

```text
Private/self-hosted WESLR is for organizations that need control over data location, runtime, access, updates, and integrations.
Institution deployments are quote-based.
```

## Public site information architecture

Recommended public structure:

```text
1. Hero
2. Public demo chat
3. What WESLR is
4. Why it is different from normal chatbots
5. Governed memory and continuity
6. Hosted vs private deployment
7. Agents/tools ecosystem positioning
8. Pricing / trial / private quotes
9. Trust and boundaries
10. Contact / pilot / institution inquiry
```

## Hero contract

Hero should communicate:

```text
Continuity-first cognitive AI for long-running work.
```

Supporting copy:

```text
WESLR helps preserve project context, governed memory, evidence, proposals, and approval boundaries across people, teams, and compatible agents.
```

Primary CTA:

```text
Try the read-only demo
```

Secondary CTA:

```text
Ask about private deployment
```

Boundary microcopy:

```text
The public demo is read-only. It does not upload files, write memory, expose operator controls, or deploy changes.
```

## Public demo chat UX contract

The chat must make these states obvious:

```text
read-only mode
what can be asked
what is blocked
why privacy is protected
what full/hosted/private WESLR would add later
```

Suggested starter prompts:

```text
What is WESLR?
Are you just another chatbot?
Can WESLR remember me?
Where does company data go?
Can agents like Claude or OpenClaw use WESLR?
Can this demo upload files or run tools?
Can WESLR improve itself automatically?
What does WESLR cost?
```

## Onboarding direction

Public website onboarding should not be a long wizard at first.

V1 should be:

```text
1. User lands on site
2. User sees read-only demo boundary
3. User asks starter prompt or free text
4. WESLR answers safely
5. User sees next action:
   - start hosted trial
   - request private/institution deployment
   - read docs/support
```

Later onboarding can add:

```text
account creation
workspace setup
privacy/data-location choice
personal vs team vs institution mode
first memory/governance explanation
integration setup
```

## Pricing UX contract

Current pricing direction:

```text
1-month free trial
€80/month per user after trial
private/institution deployments quote-based
```

Pricing must be shown carefully:

```text
Hosted individual/team pricing is simple.
Institution/private deployments require inquiry because runtime, data location, support, integrations, and compliance needs vary.
```

## Privacy UX contract

Public UX must repeat the privacy boundary in plain language:

```text
The public demo does not upload files.
The public demo does not write private memory.
The public demo does not expose operator controls.
The public demo does not deploy changes.
Private deployments are for organizations needing control over data location and runtime.
```

Avoid overly technical language like:

```text
tokens get shared
LLM context window
provider internals
```

unless in advanced documentation.

## Agent/API positioning UX

Public copy should say:

```text
WESLR can complement compatible agents and tools by providing continuity, governed memory, evidence, proposal tracking, approval-aware workflow, and compact task context.
```

Do not claim:

```text
public Agent API is available
WESLR controls ChatGPT or Claude
WESLR bypasses agent governance
```

## UX quality bar

Public WESLR should feel competitive with major AI products in:

```text
clarity
speed
visual polish
chat readability
empty states
loading states
trust language
mobile responsiveness
error handling
```

But it should feel differentiated by:

```text
continuity indicators
governance/boundary indicators
private vs hosted deployment clarity
agent/tool ecosystem framing
calm engineering-grade trust
```

## First polished UX milestone

The first UX milestone should be:

```text
Public Demo Experience V1
```

Definition:

```text
A visitor can land on weslr.de, understand WESLR within 60 seconds, try the read-only chat, understand privacy/deployment boundaries, and know whether to start a trial or request private deployment.
```

Required pieces:

```text
premium hero
read-only chat window
starter prompts
public-demo boundary banner
clear hosted/private cards
pricing/trial card
trust/privacy section
contact/request-private-deployment CTA
mobile-friendly layout
basic loading/error states
```

## UX evaluation direction

UX changes should be checked by:

```text
public demo conversation suites
longform public-demo suite
manual visual review
mobile screenshot review
copy review for overclaims
public-demo policy tests
```

Future UX-specific evals may include:

```text
first-minute comprehension checklist
trust-boundary checklist
pricing comprehension checklist
private-deployment buyer checklist
mobile readability checklist
```

## Immediate implementation sequence

Recommended order:

```text
1. Preserve this UX contract.
2. Audit current weslr-ui and landing/front-door surfaces against it.
3. Define Public Demo Experience V1 component/layout plan.
4. Implement UI changes in small PRs.
5. Keep public-demo policy/eval suites green.
6. Do not add full-WESLR cognition UI until public demo UX is clear.
```

## V1 verdict

```text
WESLR_PUBLIC_UX_CONTRACT_V1_DEFINED
```
