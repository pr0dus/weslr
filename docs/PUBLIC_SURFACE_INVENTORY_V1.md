# WESLR Public Surface Inventory V1

Date: 2026-05-09
Status: public-surface inventory — no runtime/deployment changes
Scope: current frontend/app/public demo files inspected from GitHub

## Purpose

This inventory records what actually exists in the WESLR repo for public UX, before implementing the first frontend patch.

This document follows:

- `docs/PUBLIC_SURFACE_UX_AUDIT_V1.md`
- `docs/WESLR_UX_DOCTRINE_AND_ONBOARDING_V1.md`

The goal is to decide which surface is canonical, which surfaces are experimental, and what needs hardening before public deployment.

## Inventory summary

| Surface | Evidence status | Recommended role |
|---|---:|---|
| `weslr-ui/` | inspected directly | canonical candidate for `chat.weslr.de` |
| `front-door/` | named in README, not yet directly inspected | likely experimental/legacy until inventoried |
| `dashboard/satellite/` | named in README, search evidence only | experimental/specialized demo surface |
| `weslr-test-deployment/` | named in README | deployment/staging support, not product UX |
| `weslr/docs/*PUBLIC*` | inspected directly | safety/readiness/design contracts |
| root `README.md` | inspected directly | repo/product identity and surface map |

## Canonical decision for now

```text
canonical public app candidate: weslr-ui/
canonical public landing domain: weslr.de
canonical public chat/demo domain: chat.weslr.de
canonical staging domain: staging.weslr.de
```

This does not mean `weslr-ui/` is production-ready. It means future public UX implementation should start there unless a later inventory proves another surface is better.

## `weslr-ui/` evidence

### Package baseline

`weslr-ui/package.json` defines a Vite/React app:

```json
{
  "name": "weslr-ui",
  "version": "0.1.0",
  "private": true,
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0"
  },
  "devDependencies": {
    "vite": "^5.0.0",
    "@vitejs/plugin-react": "^4.2.0"
  }
}
```

Conclusion:

- frontend stack is lightweight and appropriate for rapid UX iteration
- no heavy framework lock-in
- build path exists

### App shell

`weslr-ui/src/App.tsx` contains a real app shell with:

- left sidebar
- main chat surface
- file drop zone
- chat input box
- continuity status indicator
- right operator panel
- backend calls through `./api`

This confirms `weslr-ui/` is not only a placeholder README. It has actual React implementation.

### API client

`weslr-ui/src/api.ts` currently contains development/default behavior:

- continuity returns simulated active status
- operator visibility returns visible by default
- operator summary returns empty proposals/candidates
- file upload simulates successful structured-data routing
- chat sends to `/api/chat`

Important current defaults:

```text
operator visibility: visible = true
file upload: simulated success
chat endpoint: /api/chat
```

### Config

`weslr-ui/src/config.ts` currently declares:

- structured data extension map
- file router map
- backend contract endpoints
- operator visibility default value: `true`
- continuity endpoints

Important current risk:

```text
operator.defaultValue = true
```

This is suitable for development but not public demo mode.

## Current UX readiness of `weslr-ui/`

| Area | Current status | Public readiness |
|---|---|---|
| React/Vite app shell | present | good baseline |
| Chat surface | present | needs UX hardening |
| `/api/chat` route | referenced | backend compatibility must be verified |
| File upload | present/simulated | should be hidden/disabled in public demo |
| Operator panel | present | must be hidden/unreachable in public demo |
| Continuity status | present/simulated | should be converted to user-friendly mode/status text |
| Mobile layout | not proven | needs mobile-first patch |
| Onboarding | not present | missing |
| Landing page | not present in `weslr-ui` | likely separate `weslr.de` task |
| Public copy | not centralized | missing |
| Feature flags | not explicit enough | required before public demo |

## Public-demo hardening requirements

Before `weslr-ui/` can be used as `chat.weslr.de` public demo, it must add a public mode contract.

Required public demo defaults:

```text
operator panel: hidden and unreachable
file upload: disabled or hidden
memory writes: unavailable
execution: unavailable
mode badge: visible
limitations: visible
example prompts: visible
backend errors: sanitized
mobile: chat-first
```

## Feature flag recommendation

Add explicit frontend mode flags before any deployment:

```typescript
publicDemo: {
  readOnly: true,
  fileUploadEnabled: false,
  operatorPanelEnabled: false,
  onboardingEnabled: false,
  showLimitationsFooter: true,
  showExamplePrompts: true,
}
```

These flags should control UI visibility only. Backend must still enforce safety independently.

## First coding patch recommendation

The next safe coding patch should be small and reversible:

```text
WESLR: harden weslr-ui public demo shell
```

Suggested files:

```text
weslr-ui/src/config.ts
weslr-ui/src/App.tsx
```

Suggested changes:

1. Add public demo config flags.
2. Set operator default visibility to false.
3. Hide/disable file upload when public demo mode is read-only.
4. Add a read-only demo banner.
5. Add safe example prompts.
6. Add limitations footer.
7. Replace raw `Error: ...` chat display with sanitized fallback text.
8. Keep all backend enforcement unchanged.

## What not to code yet

Do not implement these yet:

- full account onboarding
- organization invite flow
- persistent memory UI
- production auth
- operator proposal review public UI
- file upload for anonymous users
- deployment automation
- premium visual redesign from scratch

Reason: first public UX patch should reduce risk before adding complexity.

## `front-door/` status

The root README names `front-door/` as part of WESLR Public Surface. This inventory did not successfully inspect concrete `front-door/` files through the current GitHub search tooling.

Status:

```text
named but not inventoried
```

Recommendation:

- do not declare `front-door/` canonical yet
- inspect with local clone or a stronger file tree listing later
- treat as experimental/unknown until inspected

## `dashboard/satellite/` status

The root README names `dashboard/satellite/`. Search did not return direct app files, but memory/docs references indicate dashboard/satellite work exists historically.

Status:

```text
named, likely experimental/specialized, not canonical public UX yet
```

Recommendation:

- treat as demo/voice/satellite surface
- do not use as first public product face
- inspect separately when voice/satellite demo is prioritized

## `weslr-test-deployment/` status

The root README names `weslr-test-deployment/` under deployment/runtime forge.

Status:

```text
deployment/staging support, not user-facing product UX
```

Recommendation:

- keep separate from public UX decisions
- use later for staging/deployment validation

## Public UX decision

For the next implementation phase:

```text
Use weslr-ui/ as the canonical app candidate for chat.weslr.de.
Apply public-demo hardening first.
Delay full premium redesign until public copy and wireframe contracts exist.
```

## Next PR sequence

Recommended next PRs:

1. `WESLR: harden weslr-ui public demo shell`
   - small code patch
   - banner, limitations, examples, hidden operator panel, disabled upload

2. `WESLR: add public copy contract v1`
   - exact landing/demo/onboarding text

3. `WESLR: add public wireframe contract v1`
   - screens and responsive layout contract

4. `WESLR: begin premium visual system v1`
   - after the shell is safe

## V1 verdict

```text
PUBLIC_SURFACE_INVENTORY_V1_DEFINED
```

`weslr-ui/` is the right place to begin public UX coding, but it must be hardened from development mode into public read-only demo mode before styling or deployment work.
