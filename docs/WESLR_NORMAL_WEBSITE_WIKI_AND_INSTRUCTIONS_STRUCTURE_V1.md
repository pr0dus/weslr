# WESLR Normal Website Wiki and Instructions Structure V1

Date: 2026-06-07  
Repo: `/data/data/com.termux/files/home/weslr-pr47-clean`  
Branch: `master`

## Status

Planning only. No website code, deployment, or access changes.

## Purpose

This document turns the internal Nova handoff into a normal documentation structure a serious software/company website could use.

It is meant to help with:

- public explanation pages
- protected invite-only user guidance
- developer documentation
- operator/admin documentation
- internal source mapping for claims and page ownership

It keeps public-facing pages plain, accurate, and non-internal.

## 1. Documentation layers

### Layer A — Public explanation pages
For visitors who want to understand WESLR.

### Layer B — Protected invite-only user guide
For invited users/testers behind access control.

### Layer C — Developer documentation
For technical readers and integrators.

### Layer D — Operator/admin documentation
For owner/operator use and review.

### Layer E — Internal source map
For Nova/OCC only; maps website pages to repo sources and claim boundaries.

## 2. Public explanation pages

These pages should use plain language and avoid internal lane/commit/HEAD language.

| Page title | Target reader | Label | Purpose | Source docs | Allowed wording | Forbidden wording | First draft status |
|---|---|---|---|---|---|---|---|
| What is WESLR? | Visitors | public | Explain WESLR in one clear page | `docs/WESLR_COGNITIVE_AI_POSITIONING_V1.md`, `weslr/docs/WESLR_DOCTRINE_REGISTRY_V1.md`, `docs/WESLR_PUBLIC_UX_CONTRACT_V1.md` | continuity-first, governed memory, evidence-based | consciousness, AGI, certified intelligence | draft |
| What WESLR is not | Visitors | public | Set hard claim boundaries | `docs/WESLR_COGNITIVE_AI_POSITIONING_V1.md`, `weslr/docs/WESLR_DOCTRINE_REGISTRY_V1.md` | not a normal chatbot, not a proof engine, not a launch claim | hidden magic, guaranteed intelligence, public-ready | draft |
| Why WESLR exists | Visitors | public | Explain the product purpose | `docs/WESLR_COGNITIVE_AI_POSITIONING_V1.md`, `docs/WESLR_PUBLIC_UX_CONTRACT_V1.md` | long-running work, continuity, evidence, bounded help | grandiose AI claims | draft |
| How WESLR differs from a normal chatbot | Visitors | public | Clarify the structural difference | `docs/WESLR_PROJECT_CHAT_RUNTIME_BOUNDARY_V1.md`, `docs/WESLR_PROJECT_STATE_MODEL_V1.md`, `docs/WESLR_MEMORY_STATE_MODEL_V1.md` | project state, memory, continuity, corrections | hidden memory, perfect continuity | draft |
| Current status | Visitors | public | Say what is live vs planned | `docs/WESLR_PUBLIC_UX_CONTRACT_V1.md`, `docs/WESLR_PUBLIC_READINESS_PLAN_V1.md` | planned / not live / preview | production-ready, open-public | draft |
| Roadmap | Visitors | public | Show near-term planned work | `docs/WESLR_PUBLIC_READINESS_PLAN_V1.md`, `docs/WESLR_PUBLIC_UX_CONTRACT_V1.md` | planned, next, preview, staged | guaranteed delivery dates | draft |
| FAQ | Visitors | public | Answer common questions safely | All public-facing source groups | short truthful answers | overclaims, guarantees, secrets | draft |
| Glossary | Visitors | public | Define WESLR terms simply | `weslr/docs/WESLR_DOCTRINE_REGISTRY_V1.md`, state/memory docs | precise, plain definitions | internal jargon without explanation | draft |

## 3. Protected invite-only user guide

This section is for invited users/testers and must be access-controlled.

| Page title | Target reader | Label | Purpose | Source docs | Allowed wording | Forbidden wording | First draft status |
|---|---|---|---|---|---|---|---|
| Invite-only access | Invited user | protected | Explain how access works | `docs/WESLR_PUBLIC_UX_CONTRACT_V1.md`, `docs/WESLR_PUBLIC_PILOT_OCW_DEPLOYMENT_ACCESS_BOUNDARY_REVIEW_V1.md` | invite-only, access-controlled, approved preview | open access, self-registration | draft |
| How to sign in | Invited user | protected | Explain entry flow at a high level | `docs/WESLR_PUBLIC_UX_CONTRACT_V1.md`, `docs/WESLR_PROJECT_CHAT_RUNTIME_BOUNDARY_V1.md` | sign-in, access control, approved access | unauthenticated access | draft |
| How to start a project | Invited user | protected | Explain project start flow | `docs/WESLR_PROJECT_STATE_MODEL_V1.md`, `docs/WESLR_PROJECT_CHAT_RUNTIME_BOUNDARY_V1.md` | project setup, project context, candidate state | hidden persistence, automatic saving claims | draft |
| How to use project chat | Invited user | protected | Explain project chat usage | `docs/WESLR_PROJECT_CHAT_RUNTIME_BOUNDARY_V1.md`, `docs/WESLR_PROJECT_CHAT_ASSEMBLY_ORCHESTRATION_PACKET_HELPERS_REVIEW_V1.md` | project context, clarifying questions, bounded support | open chat, unscoped chat | draft |
| How WESLR uses project context | Invited user | protected | Explain continuity at a simple level | `docs/WESLR_PROJECT_STATE_MODEL_V1.md`, `docs/WESLR_MEMORY_STATE_MODEL_V1.md` | scoped continuity, visible correction paths | perfect continuity, hidden memory | draft |
| How corrections work | Invited user | protected | Show how users can correct state | `docs/WESLR_PROJECT_STATE_MODEL_V1.md`, `docs/WESLR_MEMORY_STATE_MODEL_V1.md` | correction path, deprecation, updated state | silent override, unreviewed mutation | draft |
| What WESLR can and cannot do | Invited user | protected | Set support boundaries | `docs/WESLR_PROJECT_CHAT_RUNTIME_BOUNDARY_V1.md`, `weslr/docs/WESLR_DOCTRINE_REGISTRY_V1.md` | bounded help, evidence-based support | tool execution claims, certainty claims | draft |
| How to report problems | Invited user | protected | Explain support reporting | `docs/WESLR_PUBLIC_UX_CONTRACT_V1.md`, `docs/WESLR_PUBLIC_PILOT_STORAGE_PRIVACY_AND_RETENTION_AUDIT_V1.md` | report issues, preview limitations, privacy-aware | raw internal logs, private data dumps | draft |
| Data/privacy basics | Invited user | protected | Summarize privacy posture | `docs/WESLR_PUBLIC_PILOT_STORAGE_PRIVACY_AND_RETENTION_AUDIT_V1.md`, `docs/WESLR_PUBLIC_PILOT_STORAGE_PRIVACY_RETENTION_GOVERNANCE_BOUNDARY_V1.md` | privacy, retention, access control | open data access, raw storage claims | draft |

## 4. Developer documentation

| Page title | Target reader | Label | Purpose | Source docs | Allowed wording | Forbidden wording | First draft status |
|---|---|---|---|---|---|---|---|
| Architecture overview | Developer | public | Explain system structure | `docs/WESLR_PROJECT_STATE_MODEL_V1.md`, `docs/WESLR_MEMORY_STATE_MODEL_V1.md`, `docs/WESLR_PROJECT_CHAT_RUNTIME_BOUNDARY_V1.md` | modules, boundaries, pipeline overview | hidden data, runtime certainty | draft |
| Project chat pipeline overview | Developer | public | Explain the project-chat flow | `docs/WESLR_PROJECT_CHAT_METADATA_CHAIN_NEXT_LANE_SELECTION_V1.md`, `docs/WESLR_PROJECT_CHAT_RUNTIME_BOUNDARY_V1.md` | intake, context, state, answer-plan boundaries | live execution claims | draft |
| Evidence/provenance model | Developer | public | Explain source and evidence tracking | `docs/WESLR_PROJECT_STATE_MODEL_V1.md`, `docs/WESLR_MEMORY_STATE_MODEL_V1.md`, `docs/WESLR_PROJECT_CHAT_RAG_AND_EVIDENCE_RETRIEVAL_BOUNDARY_V1.md` | provenance, status, correction path | certainty without evidence | draft |
| Memory/state model | Developer | public | Describe memory/state semantics | `docs/WESLR_MEMORY_STATE_MODEL_V1.md`, `docs/WESLR_PROJECT_STATE_MODEL_V1.md` | scoped continuity, reviewable memory | hidden memory, perfect memory | draft |
| Runtime boundary model | Developer | public | Define what runtime may not do yet | `docs/WESLR_PROJECT_CHAT_RUNTIME_BOUNDARY_V1.md`, `docs/WESLR_PROJECT_CHAT_RUNTIME_BOUNDARY_REVIEW_V1.md` | metadata-only, bounded future runtime | deployment, live answer authority | draft |
| API/configuration method | Developer | public | Explain safe external API configuration | `docs/API_KEY_GREEN_ZONE_V1.md`, `docs/WESLR_MATERIALS_RESEARCH_WORKFLOW_V1.md` | env vars, placeholders, redaction | literal secrets, unguarded keys | draft |
| Environment variables | Developer | public | List required env vars and meaning | `docs/API_KEY_GREEN_ZONE_V1.md`, `weslr/README.md` | secret-backed env vars, unset defaults | secret values, inline credentials | draft |
| Secret handling | Developer | public | Show safe secret rules | `docs/API_KEY_GREEN_ZONE_V1.md`, `docs/WESLR_MATERIALS_RESEARCH_WORKFLOW_V1.md` | never commit keys, never log values | leakage, direct key printing | draft |
| Local/private preview limitations | Developer | public | Clarify preview boundaries | `docs/WESLR_PROJECT_CHAT_RUNTIME_BOUNDARY_V1.md`, `docs/WESLR_PUBLIC_UX_CONTRACT_V1.md` | preview-only, not live/public | production-ready claims | draft |
| Known limitations | Developer | public | State what is not implemented | `docs/WESLR_PROJECT_CHAT_RUNTIME_BOUNDARY_V1.md`, `weslr/docs/WESLR_DOCTRINE_REGISTRY_V1.md` | not live, not public, not final | overpromising | draft |

## 5. Operator/admin documentation

| Page title | Target reader | Label | Purpose | Source docs | Allowed wording | Forbidden wording | First draft status |
|---|---|---|---|---|---|---|---|
| Invite management | Owner/operator | internal | Explain invite handling | `docs/WESLR_PUBLIC_PILOT_OCW_DEPLOYMENT_ACCESS_BOUNDARY_REVIEW_V1.md` | invite-only, approved access | open registration, uninvited access | draft |
| Access-control checklist | Owner/operator | internal | Check access gates before release | `docs/WESLR_PUBLIC_PILOT_OCW_DEPLOYMENT_ACCESS_BOUNDARY_REVIEW_V1.md`, `docs/WESLR_PUBLIC_UX_CONTRACT_V1.md` | gated access, approval required | public launch, silent enablement | draft |
| Protected chat status checklist | Owner/operator | internal | Confirm protected chat is still bounded | `docs/WESLR_PROJECT_CHAT_RUNTIME_BOUNDARY_V1.md`, `docs/WESLR_PUBLIC_PILOT_OCW_DEPLOYMENT_ACCESS_BOUNDARY_REVIEW_V1.md` | protected, invite-only, approved preview | open/public status | draft |
| Before-publish checklist | Owner/operator | internal | Prevent bad public wording | `weslr/docs/WESLR_DOCTRINE_REGISTRY_V1.md`, `docs/WESLR_PUBLIC_UX_CONTRACT_V1.md` | candidate, planned, not live | guarantee, proof, certainty | draft |
| Claims/wording checklist | Owner/operator | internal | Keep claims conservative | `docs/WESLR_COGNITIVE_AI_POSITIONING_V1.md`, `docs/WESLR_PUBLIC_UX_CONTRACT_V1.md` | evidence-based, bounded, preview | AGI, conscious, certified | draft |
| Incident/secret handling | Owner/operator | internal | Handle leaks or risk | `docs/API_KEY_GREEN_ZONE_V1.md`, `docs/WESLR_MATERIALS_RESEARCH_WORKFLOW_V1.md` | redact, rotate, revoke, review | expose, print, preserve unsafe values | draft |
| Deployment readiness checklist | Owner/operator | internal | Distinguish planning from release | `docs/WESLR_PUBLIC_READINESS_PLAN_V1.md`, `docs/WESLR_PUBLIC_PILOT_OCW_DEPLOYMENT_ACCESS_BOUNDARY_REVIEW_V1.md` | planned, gated, not live | ready, launched, open-public | draft |

## 6. Internal source map

This section is for Nova/OCC only.

| Page group | Supported by | Allowed claims | Forbidden claims | Visibility |
|---|---|---|---|---|
| Public explanation pages | identity, doctrine, public UX, frontier doctrine | plain-language product explanation | AGI, certainty, launch readiness | public |
| Protected invite-only user guide | runtime boundary, project state, memory, privacy docs | access-controlled preview guidance | open/public access, unauthenticated use | protected |
| Developer docs | state models, runtime boundary, API config docs | architecture and safe integration guidance | secret values, live execution claims | public |
| Operator docs | privacy, access, deployment readiness docs | checklists, boundaries, approvals | silent enablement, public launch claims | internal |
| Legal/company mapping | public UX, privacy, readiness docs | source-linked claims only | unsupported guarantees | public/internal mix |

## 7. Recommended website/docs navigation

### Main website nav
- What is WESLR?
- Why WESLR
- How WESLR works
- Current status
- Roadmap
- FAQ
- Contact / Request invite

### Docs nav
- Overview
- Architecture
- Project chat
- State & memory
- API & configuration
- Security & secrets
- Limitations
- Changelog

### Wiki nav
- Concepts
- Glossary
- Workflows
- Pages map
- FAQs
- Status notes

### Protected user guide nav
- Invite-only access
- Sign in
- Start a project
- Project chat
- Corrections
- Privacy basics
- Report a problem

### Developer docs nav
- Architecture overview
- Pipeline overview
- Evidence model
- Memory/state model
- Runtime boundary
- API/configuration
- Environment variables
- Secret handling
- Known limitations

### Operator docs nav
- Invite management
- Access-control checklist
- Protected chat status
- Before-publish checklist
- Claims/wording checklist
- Incident/secret handling
- Deployment readiness checklist

## 8. Normal status labels

Use these labels on website/wiki pages:

- public
- protected
- internal
- draft
- planned
- not live
- preview
- gated

Avoid internal process labels on public pages.

## 9. What this structure must keep out of public pages

- lane names
- HEAD or commit references
- OCC workflow language
- internal judgments
- raw private data
- raw `.weslr` state
- secrets
- live execution claims
- open/public access claims

## 10. Outcome

This is a normal documentation structure for a serious software/company website:

- simple enough for visitors
- clear enough for invited users
- technical enough for developers
- strict enough for operators
- mapped enough for Nova/OCC handoff

It is planning only.
