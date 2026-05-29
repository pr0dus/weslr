# WESLR V1 Product UX and Operating Model Discovery Report V1

Date: 2026-05-29
Task type: read-only discovery / inventory
Start HEAD: `0205d42`
End HEAD: `0205d42` (no code commit; report only)
Handshake: PASS

## Scope checked

- `pwd`
- `git branch --show-current`
- `git rev-parse --short HEAD`
- `git status --short`
- `find . -maxdepth 4 -type f | sort | grep -Ei 'website|site|frontend|ui|ux|chat|login|auth|file|upload|storage|privacy|terms|license|impressum|contact|pricing|plan|workspace|dashboard|mock|demo|public|pilot|cloudflare|deploy|nginx|server' || true`
- relevant docs and UI files via `sed -n`
- `git diff --quiet HEAD -- weslr/chat_responder.py`
- `git diff --quiet HEAD -- weslr/main.py`

## Files changed

- `docs/WESLR_V1_PRODUCT_UX_AND_OPERATING_MODEL_DISCOVERY_REPORT_V1.md`

## Executive summary

WESLR already has multiple user-facing/public-surface candidates, but the full V1 product UX and operating model are still only partially defined. The strongest existing surface is `weslr-ui/`, which is a real React/Vite chat shell for `chat.weslr.de`. It already defines a chat-first layout, read-only public-demo mode, continuity banner, and hidden operator-panel concept. However, login/account design, workspace/account model, file UX, storage/retention limits, legal placement, and scaling/deployment assumptions are still mostly contract-level or undefined in the inspected public-facing files.

## 1) Existing user-facing surfaces

### Found

- `weslr-ui/`
  - `weslr-ui/README.md`
  - `weslr-ui/src/App.tsx`
  - `weslr-ui/src/config.ts`
  - `weslr-ui/src/api.ts`
  - `weslr-ui/index.html`
- `chat_ui.py`
  - minimal standalone HTML chat surface with `/chat` POST
- `dashboard/index.html`
  - operator-style dashboard with chat section and admin controls
- `dashboard/satellite/index.html`
  - satellite-style UI with tabs, status, actions, voice/text area
- `deploy/staging/static/index.html`
  - staging/public-facing HTML shell
- `docs/*`
  - public UX / public surface / commercial / privacy / deployment contracts
- root `README.md`
  - names public-surface areas and product tracks

### State

A visual/user experience does exist, but it is fragmented across several surfaces. `weslr-ui/` is the clearest candidate for the canonical public chat/demo surface. A polished, finalized V1 public product experience is not yet complete.

## 2) Login and account experience

### What exists

- `weslr-ui/src/README.md` states: **zero authentication**.
- Public demo mode is explicitly read-only and anonymous.
- Private/institutional deployment is described in docs, but not wired as an account system.

### Findings

- Login designed: **No**
- Account creation designed: **No**
- Guest access: **Allowed** in read-only public demo mode
- Invite-only access: **Not designed yet** in the inspected UX files
- Role/account types: **Not defined** in implemented public UX

## 3) Chat experience

### Defined layout

Yes, partially.

- `weslr-ui/README.md` defines:
  - left sidebar: conversations, projects, files, continuity snapshots
  - main chat surface: message stream, input box, file drop zone, continuity status
  - right operator panel: hidden by default, toggleable
- `weslr-ui/src/App.tsx` implements a chat card with bubbles.
- `chat_ui.py` implements a simpler single-pane bubble chat.
- `dashboard/satellite/index.html` and `dashboard/index.html` also contain chat-like UI blocks.

### Chat details

- Timestamps: **stored in message data** in `weslr-ui/src/App.tsx`, but **not visibly rendered** in the current bubble UI
- Message style: **bubbles/cards**, not a workspace document view
- Copy/share/export: **not shown** in the inspected public UX
- Left sidebar: **defined in `weslr-ui/README.md`**, not fully implemented as a rich product shell in the read-only demo snapshot
- Right context/operator panel: **defined and implemented as hidden-by-default concept** in `weslr-ui`
- Full-screen mode: **not explicitly defined**
- Adaptive layout: **partially implied**, but mobile/role/context adaptation is not yet productized

## 4) WESLR thinking / processing display

### Current state

The public demo mostly hides internal process. It shows only coarse boundary/status messaging.

### Visible states found

- reading: **not clearly defined as a user-visible state**
- thinking: **not clearly defined** in `weslr-ui`
- checking evidence: **not clearly defined** in public UI
- waiting for approval: **not clearly defined** in public UI
- blocked by policy/governance: **not clearly defined** in public UI
- needs clarification: **not clearly defined** in public UI

### How process is shown

- mostly hidden
- occasional status copy / badge / boundary text
- no explicit stepper or evidence timeline in the public demo surface

### Note

Some internal/operator surfaces (`dashboard/`, `chat_ui.py`) expose advisories, status, and meta panels, but those are not a coherent public-facing WESLR process model.

## 5) File upload experience

### Found

- `weslr-ui/src/App.tsx` includes a file input area
- `weslr-ui/src/config.ts` includes file-routing config
- `weslr-ui/src/api.ts` includes `uploadFile()` and `routeFile()` stubs

### Current public-demo behavior

- file upload is **disabled** in read-only public demo mode
- the UI shows a disabled/upload-limited explanation instead of a live upload surface
- uploaded files are **not actually displayed** as user artifacts in the current public demo

### File display / status

- files shown as titles/cards/previews/folders/artifacts: **not yet in public UX**
- does user see whether WESLR read the file: **no**
- indexed/summarized/ignored/blocked/pending state: **not surfaced in public UX**
- actions open/remove/summarize/ask/export/delete: **not defined** in public UX

## 6) File type handling

### Planned / referenced

- `weslr-ui/src/config.ts` references structured extensions: `.json`, `.yaml`, `.yml`, `.csv`
- file router map references `pdf`, `structured`, and `text`

### Unknown / unsafe / invalid handling

- unknown file types: **not defined in the public UX**
- too-large files: **not defined**
- corrupted files: **not defined**
- private/sensitive files: **public demo blocks file upload entirely; deeper policy exists in docs, but not a product UX flow**
- executable/dangerous files: **not defined in the public UX**

## 7) File size and storage limits

### Findings

- maximum upload sizes: **not defined in public UX files inspected**
- per-user storage limits: **not defined**
- free/paid limits: **not defined as concrete UX limits**
- retention periods: **not defined**
- deletion/export: **not defined**
- storage cleanup: **not defined**

### Notes

Commercial/privacy docs mention hosted vs private deployment and controlled infrastructure, but the inspected public UX files do not define product-visible storage quotas or retention policy.

## 8) User workspace model

### What exists

- `weslr-ui/README.md` explicitly names sidebar areas for:
  - conversations
  - projects
  - files
  - continuity snapshots
- root docs describe WESLR as continuity-first, with governed memory and project context.

### What is missing

- per-user workspace creation: **not defined**
- project creation flow: **not defined**
- file-to-chat/project/account binding: **not defined** in implemented public UX
- memory ownership model (user/project/org/workspace): **not productized in public UX**
- visible memory/knowledge/files/timeline area: **only partial labels in `weslr-ui` README; not a full designed workspace model**

## 9) Licenses and plans

### Found

- `docs/WESLR_COMMERCIAL_DEPLOYMENT_AND_PRIVACY_V1.md`
  - hosted WESLR: 1 month free trial, then €80/month per user
  - self-hosted/institutional WESLR: quote-based
- `COMMERCIAL-LICENSE.md`
- `LICENSE.md`
- `DUAL-LICENSE-STRATEGY.md`
- `COMMERCIAL-IMPLEMENTATION-GUIDE.md`

### Findings

- plan types are **partially defined at contract level**
- free / personal / pro / team / enterprise: **not fully finalized in UX**
- limits tied to plans: **not productized in the inspected public UX**
- license terms shown: **in docs, not in a finished public site flow**
- payment/billing in scope for V1: **deferred in implementation; billing feature flag is off in `weslr-ui/src/config.ts`**

## 10) Privacy/legal placement

### Found

- privacy/deployment/legal guidance exists in docs:
  - `docs/WESLR_COMMERCIAL_DEPLOYMENT_AND_PRIVACY_V1.md`
  - `docs/WESLR_PUBLIC_UX_CONTRACT_V1.md`
  - `docs/PUBLIC_SURFACE_UX_AUDIT_V1.md`
  - `docs/PUBLIC_SURFACE_INVENTORY_V1.md`

### Missing in the inspected public UX

- privacy policy page: **not located as a surfaced UX page**
- terms page: **not located as a surfaced UX page**
- impressum page: **not located as a surfaced UX page**
- contact page/form: **not located as a surfaced UX page**
- deletion/export info page: **not located as a surfaced UX page**
- consent before file upload: **not designed as a dedicated flow**
- consent before memory/storage: **not designed as a dedicated flow**
- consent before pilot contact: **not designed as a dedicated flow**

### Conclusion

Legal/privacy scope is documented, but the public website/legal placement remains mostly undefined in the actual product UX.

## 11) Visual identity

### What is defined

- dark premium UI tone
- strong contrast
- clean system fonts / Inter-like stack
- blue/cyan accents in `weslr-ui`
- calm, engineering-grade, minimal/futuristic feel

### What is not clearly defined

- logo usage: **not defined in the inspected UX files**
- dark/light mode: **effectively dark-first; no explicit theme system**
- accent color system: **partial, not formalized**
- visual tone: **mostly calm / premium / industrial / research / minimal**

## 12) Adaptive interface idea

### Finding

Yes, WESLR is intended to adapt by context in the docs, but V1-safe adaptation is still limited.

### Safe in V1

- chat-first layout
- mode/status labeling
- read-only vs hosted vs private distinction
- hidden operator controls by default
- mobile-friendly stack/order

### Better deferred to V2

- deep user-profile-based UI reshaping
- auto-rearranging interface by inferred needs
- persistent per-user adaptive layout memory without explicit settings
- advanced dynamic panel orchestration

### Approval/settings

Any meaningful adaptive UI should require explicit settings or user/operator approval, not silent behavior mutation.

## 13) Infrastructure and scaling assumptions

### What is currently visible

- hosted vs self-hosted deployment concept exists
- staging deployment is referenced
- Ubuntu/Linux/Docker are mentioned in commercial/deployment docs
- `weslr-ui` is frontend-only by default with no auth backend in public demo mode

### What is not concretely defined

- current server/storage constraints: **not specified in the public UX files inspected**
- Ubuntu storage limitations: **not specified**
- upload limiting strategy: **not specified**
- paid-user higher capacity: **only conceptually implied, not designed in UX**
- multi-server deployment: **not committed as a public UX decision**
- object storage / separate file storage / backup strategy: **not concretely designed in the public UX files inspected**

### Conclusion

Scaling/deployment is directionally acknowledged but not yet productized into a public-facing operating model.

## 14) Public launch implications for 02.08.2026

### Must be decided before credibility

- canonical public surface
- login/account path
- guest vs invite-only policy
- product pricing/plan language
- privacy/legal page placement
- file upload and file-handling promises
- workspace model and what “memory” means
- mobile responsiveness/accessibility baseline
- deployment promise boundaries

### Can be mockup/design only

- operator panel
- private workspace detail views
- advanced file-routing surfaces
- multi-track domain demo shells
- rich memory/timeline visualizations
- admin/operator diagnostics

### Must not be promised

- unrestricted file upload
- automatic memory writes for all users
- hidden operator/admin access in public demo
- one-click self-hosting for every environment
- universal multi-server/object-storage support
- unbounded storage or retention
- silent adaptive UI without user control

### Can be roadmap

- hosted trial
- private/institution deployments
- richer workspace model
- project memory
- file intelligence and routing
- advanced admin/operator surfaces
- broader deployment/scaling options

## 15) Gaps

Missing or incomplete decisions remain in:

- login
- account creation
- guest/invite policy
- account/role types
- chat layout finalization
- timestamps visibility
- copy/share/export
- file upload UX
- file status indicators
- file limits
- storage/retention
- deletion/export
- user workspace model
- plan structure and limits
- billing flow
- privacy/legal page placement
- consent flows
- scaling/deployment policy
- backup/object storage strategy
- logo/brand system
- accessibility/mobile responsiveness

## 16) Recommendation

Recommended next lane:

`DESIGN_WESLR_V1_PRODUCT_UX_AND_OPERATING_MODEL_V1`

## Verification notes

- `weslr/chat_responder.py` remains untouched: confirmed by `git diff --quiet HEAD -- weslr/chat_responder.py`
- `weslr/main.py` remains untouched: confirmed by `git diff --quiet HEAD -- weslr/main.py`
- actual run approval remains **not granted**
- actual run execution remains **not performed**
