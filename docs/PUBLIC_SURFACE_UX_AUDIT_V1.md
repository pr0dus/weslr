# WESLR Public Surface + UX Audit V1

Date: 2026-05-08
Scope: public-facing WESLR surfaces, UX direction, website/demo readiness

## Purpose

This audit defines what WESLR's public surface should be, what already exists in the repository, what is missing from the user experience, and what should remain operator-only.

This is a documentation/audit pass only. It does not deploy anything, change runtime behavior, expose endpoints, or modify frontend code.

## Evidence reviewed

### Root README

The root README now defines WESLR as a continuity-first entity intelligence platform and names the public surface as a dedicated area intended to become the canonical public face of WESLR.

It lists current public-surface repo areas:

```text
front-door/
weslr-ui/
dashboard/satellite/
weslr-test-deployment/
```

It also states that the repo mixes core runtime code, experimental reasoning modules, industrial MVP assets, public surface prototypes, scientific discovery workflows, docs, doctrine, and historical memory artifacts.

### `weslr-ui/README.md`

`weslr-ui` is described as an App Shell V1 for `chat.weslr.de`.

It defines a three-panel UI:

1. left sidebar — conversations, projects, files, continuity snapshots
2. main chat surface — message stream, input box, file drop zone, continuity status
3. right operator panel — hidden by default, toggleable, proposal summary, review state

The README also states that it uses React 18 + Vite, has zero authentication and zero backend dependencies, and connects to backend routes later through `vite.config.js` and `config.ts`.

### `weslr/docs/SAFE_PUBLIC_DEMO_ARCHITECTURE_V1.md`

This document defines the public demo as read-only, anonymous, deterministic, LLM-disabled by default, rate-limited, and protected by an operator off-switch.

It also defines safe website claims and forbidden claims.

### `weslr/docs/PUBLIC_READINESS_PLAN_V1.md`

This document says WESLR is not ready for unrestricted public exposure. It defines the first safe public mode as `public_demo_readonly` and lists risks such as prompt injection, memory poisoning, cost abuse, harmful inputs, malformed input crashes, and write-path triggering.

It also defines public readiness gates for release, security, poisoning, continuity, latency, rate limiting, safe public mode, and rollback/off-switch.

### `weslr/docs/WESLR_WEBSITE_INTEGRATION_PLAN_V1.md`

This document defines website integration as safe signal capture after `/chat` response generation, with no raw prompts, no PII, no behavior adaptation, and no real-time feedback loop.

It is currently marked spec-only and does not affect runtime.

## Current public-surface reality

WESLR has several public-surface pieces, but they are not yet unified into one product experience.

Current evidence suggests these roles:

| Surface | Current role | UX status |
|---|---|---|
| `weslr-ui/` | likely canonical future chat app shell for `chat.weslr.de` | promising but shell-level |
| `front-door/` | likely ingress/front-door experiment or public entry surface | needs inventory |
| `dashboard/satellite/` | likely voice/text/satellite dashboard experiment | useful for demos, not primary public UX yet |
| `weslr-test-deployment/` | deployment/staging experiment | deployment support, not user-facing product |
| `weslr/docs/*PUBLIC*` | safety/readiness/demo design contracts | strong guardrails, not UX implementation |
| root README | product identity and state map | now clear enough for repo visitors |

## Primary UX conclusion

The canonical public product surface should be:

```text
weslr.de        → public landing / explanation / trust / pilot contact
chat.weslr.de   → interactive WESLR demo or app shell
staging.weslr.de → private/staged validation before public exposure
```

Inside the repo, `weslr-ui/` should be treated as the leading candidate for `chat.weslr.de` because it already describes a chat-first layout with sidebar, main chat, continuity status, file drop zone, and hidden operator panel.

However, `weslr-ui/` should not yet be considered production-ready until it is audited against the public-readiness and safe-demo architecture documents.

## UX principle: user-first, operator-hidden

Public users should see WESLR as a clear, calm, trustworthy interactive system.

They should not see internal architecture, governance mechanics, proposal queues, release gates, or self-improvement machinery unless a specific operator/admin view is intentionally opened.

Operator surfaces must remain behind explicit controls and should not appear by default in public demos.

## Recommended public UX layers

### Layer 1 — Landing page / public face

Purpose: explain WESLR without exposing internals.

Must answer quickly:

- What is WESLR?
- Why is it different from a chatbot?
- What can I try safely?
- What is still experimental?
- How do I contact / request pilot access?

Safe public message:

```text
WESLR is a continuity-first reasoning platform for long-running work, governed memory, evidence, proposals, and domain workflows.
```

Avoid claims like AGI, autonomous self-improvement, consciousness, unhackable security, or replacing experts.

### Layer 2 — Public read-only demo

Purpose: let visitors experience WESLR safely.

Mode:

```text
public_demo_readonly
```

UX expectations:

- simple chat input
- clear mode label: read-only demo
- visible limitations
- no file upload in first public mode unless fully gated
- no account creation in first mode
- no raw prompt storage
- no hidden learning claim
- no write/execution actions
- graceful fallback when unsupported

### Layer 3 — Private operator/developer surface

Purpose: review proposals, diagnostics, traces, and deployment readiness.

Must remain:

- hidden by default
- unavailable to anonymous users
- separate from public visitor UX
- protected by identity/auth later

The right operator panel described in `weslr-ui/README.md` is good for development and operator mode, but it should not be visible by default on a public route.

### Layer 4 — Domain demos

Purpose: show product tracks without confusing users.

Potential future demos:

- Industrial/TIA read-only demo
- Scatti/materials screening report demo
- continuity/project memory demo

Each domain demo should be opt-in and clearly labeled as a track, not mixed into the first generic chat experience.

## UX gaps

### Gap 1 — No canonical public-surface decision

The repo names multiple surfaces but does not yet declare which one is canonical for:

- `weslr.de`
- `chat.weslr.de`
- `staging.weslr.de`

Recommendation:

```text
Make weslr-ui/ the canonical candidate for chat.weslr.de after audit.
Treat dashboard/satellite as experimental/specialized.
Treat weslr-test-deployment as deployment support, not product UX.
```

### Gap 2 — No user journey

Existing docs are strong on architecture and safety, but not on the user's first 60 seconds.

Missing:

- first screen
- first message
- example prompts
- error/fallback wording
- explanation of read-only mode
- transition from landing page to demo

### Gap 3 — Operator panel risk

`weslr-ui` includes a right operator panel with proposal summary and review state. This is useful, but risky if visible to the public.

Recommendation:

- keep hidden by default
- require operator mode flag later
- do not fetch proposal/review data for anonymous sessions
- never expose self-improvement suggestions to public testers by default

### Gap 4 — File drop zone too early for public demo

`weslr-ui` includes a file drop zone and future file routing.

For first public UX, file upload should be disabled or visually marked as unavailable unless upload handling is fully audited.

Reason:

- file upload expands attack surface
- structured-data routing may imply capabilities not yet productized
- public demo should be read-only and low-risk first

### Gap 5 — Public copy is not centralized

Safe/forbidden website claims exist in safety docs, but there is no single product copy contract for landing/demo text.

Recommendation:

Create:

```text
docs/PUBLIC_COPY_CONTRACT_V1.md
```

This should define hero copy, allowed claims, forbidden claims, demo disclaimers, and short descriptions for Core WESLR, Industrial/TIA, Scatti, and Deployment Forge.

### Gap 6 — No UX status badge model

Public UX needs simple visible state labels:

- Read-only demo
- No memory writes
- No LLM in this mode
- No file upload yet
- Experimental
- Operator-reviewed changes only

This reduces user confusion and protects against overclaiming.

### Gap 7 — No mobile-first check

Many visitors will use mobile. The three-panel layout can be excellent on desktop, but mobile needs a different hierarchy.

Recommendation:

Mobile order:

1. chat first
2. mode/status drawer
3. projects/files later
4. operator panel inaccessible unless authenticated/operator mode

## Recommended UX structure for `chat.weslr.de`

### Public mode layout

```text
Header:
  WESLR Demo · Read-only · Experimental

Main:
  Short intro card
  Example prompts
  Chat thread
  Input box

Footer/status:
  No memory writes · No execution · No file upload · Operator-reviewed evolution
```

### Public example prompts

Use safe, deterministic, non-overclaiming prompts:

```text
What is WESLR?
Show system overview.
What can this demo do?
Explain governed memory.
What is a proposal in WESLR?
Why is this read-only?
```

Avoid prompts that imply unrestricted intelligence or execution:

```text
Improve yourself now.
Change your memory.
Run this command.
Use my API key.
Deploy to production.
```

### Unsupported input UX

Do not show raw errors. Use bounded language:

```text
This public demo is read-only and only exposes selected deterministic routes. I can explain WESLR, show safe status information, or describe governed workflows.
```

## Public landing page recommendation

`weslr.de` should not immediately look like an internal control panel.

Recommended sections:

1. Hero: continuity-first reasoning platform
2. What makes WESLR different
3. Governed memory and traceable state
4. Product tracks
   - Core WESLR
   - Industrial/TIA
   - Scatti/materials research
5. Public demo / pilot access CTA
6. Safety and governance statement
7. Contact / pilot request

## Product-track separation

The public surface should not mix all tracks into one confusing interface.

Use clear tabs or cards:

| Track | Public wording |
|---|---|
| Core WESLR | continuity-first reasoning and governed memory |
| Industrial/TIA | engineering data normalization and industrial memory track |
| Scatti/materials | screening support for computational materials candidates |
| Deployment Forge | controlled staging/runtime deployment track |

## Governance UX rule

Public users may see that WESLR is governed. They should not see internal governance machinery unless it is intentionally simplified.

Good public wording:

```text
WESLR can propose changes, but system-changing actions require operator review.
```

Bad public wording:

```text
Here is my internal self-improvement queue and how to alter it.
```

## First implementation recommendation

Do not start with a big redesign.

Recommended next PR:

```text
PUBLIC_SURFACE_INVENTORY_V1
```

It should inspect and document actual files under:

- `weslr-ui/`
- `front-door/`
- `dashboard/satellite/`
- `weslr-test-deployment/`

Then choose:

```text
canonical public app candidate: weslr-ui/
experimental surfaces: dashboard/satellite/, front-door/
deployment support: weslr-test-deployment/
```

After inventory, implement a small UX patch in `weslr-ui/`:

1. Add read-only demo banner.
2. Hide/disable file upload in public mode.
3. Keep operator panel hidden and unreachable by default.
4. Add safe example prompts.
5. Add limitations footer.

## V1 verdict

```text
PUBLIC_SURFACE_UX_AUDIT_V1_DEFINED
```

WESLR has enough safety architecture to begin public-surface UX work, but not enough UX clarity yet.

The next safest move is not deployment. It is to inventory existing frontend folders, declare `weslr-ui/` as the likely canonical `chat.weslr.de` candidate, and then make one small UX hardening patch for public read-only mode.
