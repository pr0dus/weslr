# NOVA WESLR Docs, Wiki, and Protected Chat Source Map to Page Plan V1

Date: 2026-06-07  
Repo: `/data/data/com.termux/files/home/weslr-pr47-clean`  
Branch: `master`

## Status

Page plan only. No deployment, no access changes, no website code.

## Purpose

Create a normal website/docs/wiki page plan for WESLR that OCC and the owner can review before any implementation.

This plan uses the internal Nova handoff packet and the normal website/wiki structure as inputs, then breaks them into page-by-page work items with clear claim boundaries.

## Scope boundaries

Allowed:
- protected invite-only website chat planning
- page planning for public website, docs, wiki, protected user guide, developer docs, and operator docs

Forbidden:
- open public chat
- unauthenticated chat
- self-registration
- 50-user access claim
- production/public-ready claim
- provider/model/search/tool execution claims
- live retrieval claims
- raw private data
- `.weslr` state
- hidden prompts
- secrets

## 1. Public website pages

| Page title | Target reader | Label | Purpose | Source docs | Allowed claims | Forbidden claims | Draft priority | Website area |
|---|---|---|---|---|---|---|---|---|
| What is WESLR? | Visitors | public | Explain WESLR in plain language | `docs/NOVA_WESLR_HANDOFF_PACKET_V1.md`, `docs/WESLR_NORMAL_WEBSITE_WIKI_AND_INSTRUCTIONS_STRUCTURE_V1.md`, `docs/WESLR_COGNITIVE_AI_POSITIONING_V1.md`, `weslr/docs/WESLR_DOCTRINE_REGISTRY_V1.md` | continuity-first, governed memory, evidence-based | consciousness, AGI, certified intelligence | high | main website |
| What WESLR is not | Visitors | public | Set hard claim boundaries | same as above | not a normal chatbot, not a proof engine, not a launch claim | hidden magic, guaranteed intelligence, public-ready | high | main website |
| Why WESLR exists | Visitors | public | Explain product purpose | same as above | long-running work, continuity, evidence, bounded help | grandiose AI claims | high | main website |
| How WESLR works | Visitors | public | Explain system structure at a high level | `docs/WESLR_NORMAL_WEBSITE_WIKI_AND_INSTRUCTIONS_STRUCTURE_V1.md`, `docs/WESLR_PROJECT_CHAT_RUNTIME_BOUNDARY_V1.md`, `docs/WESLR_PROJECT_STATE_MODEL_V1.md`, `docs/WESLR_MEMORY_STATE_MODEL_V1.md` | project state, memory, continuity, corrections | hidden memory, perfect continuity, runtime certainty | high | main website |
| Current status | Visitors | public | Say what is live vs planned | `docs/WESLR_NORMAL_WEBSITE_WIKI_AND_INSTRUCTIONS_STRUCTURE_V1.md`, `docs/WESLR_PUBLIC_UX_CONTRACT_V1.md`, `docs/WESLR_PUBLIC_READINESS_PLAN_V1.md` | planned / not live / preview | production-ready, open-public | high | main website |
| Roadmap | Visitors | public | Show staged next steps | same as above | planned, next, preview, staged | guaranteed delivery dates | medium | main website |
| FAQ | Visitors | public | Answer common questions safely | all public-facing source groups | short truthful answers | overclaims, guarantees, secrets | medium | main website / docs |
| Glossary | Visitors | public | Define WESLR terms simply | `weslr/docs/WESLR_DOCTRINE_REGISTRY_V1.md`, state/memory docs | precise plain definitions | internal jargon without explanation | medium | docs/wiki |
| Contact / Request invite | Visitors | public | Offer a controlled path to access | `docs/WESLR_PUBLIC_UX_CONTRACT_V1.md`, `docs/WESLR_PUBLIC_PILOT_OCW_DEPLOYMENT_ACCESS_BOUNDARY_REVIEW_V1.md` | invite request, access-controlled preview | open access, public self-registration | high | main website |

## 2. Protected invite-only user guide

| Page title | Target reader | Label | Purpose | Source docs | Allowed claims | Forbidden claims | Draft priority | Website area |
|---|---|---|---|---|---|---|---|---|
| Invite-only access | Invited user | protected | Explain how access works | `docs/WESLR_PUBLIC_UX_CONTRACT_V1.md`, `docs/WESLR_PUBLIC_PILOT_OCW_DEPLOYMENT_ACCESS_BOUNDARY_REVIEW_V1.md` | invite-only, access-controlled, approved preview | open access, self-registration | high | protected area |
| How to sign in | Invited user | protected | Explain entry flow | same as above | sign-in, approved access, gated entry | unauthenticated access | high | protected area |
| How to start a project | Invited user | protected | Explain project start flow | `docs/WESLR_PROJECT_STATE_MODEL_V1.md`, `docs/WESLR_PROJECT_CHAT_RUNTIME_BOUNDARY_V1.md` | project setup, project context, candidate state | hidden persistence, automatic saving claims | high | protected area |
| How to use project chat | Invited user | protected | Explain project chat usage | `docs/WESLR_PROJECT_CHAT_RUNTIME_BOUNDARY_V1.md`, `docs/WESLR_PROJECT_CHAT_ASSEMBLY_ORCHESTRATION_PACKET_HELPERS_REVIEW_V1.md` | project context, clarifying questions, bounded support | open chat, unscoped chat | high | protected area |
| How WESLR uses project context | Invited user | protected | Explain continuity | `docs/WESLR_PROJECT_STATE_MODEL_V1.md`, `docs/WESLR_MEMORY_STATE_MODEL_V1.md` | scoped continuity, visible correction paths | perfect continuity, hidden memory | medium | protected area |
| How corrections work | Invited user | protected | Show correction/update flow | same as above | correction path, deprecation, updated state | silent override, unreviewed mutation | medium | protected area |
| What WESLR can and cannot do | Invited user | protected | Set support boundaries | `docs/WESLR_PROJECT_CHAT_RUNTIME_BOUNDARY_V1.md`, `weslr/docs/WESLR_DOCTRINE_REGISTRY_V1.md` | bounded help, evidence-based support | tool execution claims, certainty claims | high | protected area |
| How to report problems | Invited user | protected | Explain support reporting | `docs/WESLR_PUBLIC_UX_CONTRACT_V1.md`, `docs/WESLR_PUBLIC_PILOT_STORAGE_PRIVACY_AND_RETENTION_AUDIT_V1.md` | issue reporting, preview limitations, privacy-aware handling | raw logs, private data dumps | medium | protected area |
| Data/privacy basics | Invited user | protected | Summarize privacy posture | `docs/WESLR_PUBLIC_PILOT_STORAGE_PRIVACY_AND_RETENTION_AUDIT_V1.md`, `docs/WESLR_PUBLIC_PILOT_STORAGE_PRIVACY_RETENTION_GOVERNANCE_BOUNDARY_V1.md` | privacy, retention, access control | open data access, raw storage claims | medium | protected area |

## 3. Developer documentation

| Page title | Target reader | Label | Purpose | Source docs | Allowed claims | Forbidden claims | Draft priority | Website area |
|---|---|---|---|---|---|---|---|---|
| Architecture overview | Developer | public | Explain system structure | `docs/WESLR_PROJECT_STATE_MODEL_V1.md`, `docs/WESLR_MEMORY_STATE_MODEL_V1.md`, `docs/WESLR_PROJECT_CHAT_RUNTIME_BOUNDARY_V1.md` | modules, boundaries, pipeline overview | hidden data, runtime certainty | high | docs/wiki |
| Project chat pipeline | Developer | public | Explain chat flow at a high level | `docs/WESLR_PROJECT_CHAT_METADATA_CHAIN_NEXT_LANE_SELECTION_V1.md`, `docs/WESLR_PROJECT_CHAT_RUNTIME_BOUNDARY_V1.md` | intake, context, state, answer-plan boundaries | live execution claims | high | docs/wiki |
| Evidence/provenance model | Developer | public | Explain source/evidence tracking | `docs/WESLR_PROJECT_STATE_MODEL_V1.md`, `docs/WESLR_MEMORY_STATE_MODEL_V1.md`, `docs/WESLR_PROJECT_CHAT_RAG_AND_EVIDENCE_RETRIEVAL_BOUNDARY_V1.md` | provenance, status, correction path | certainty without evidence | high | docs/wiki |
| Memory/state model | Developer | public | Describe memory/state semantics | `docs/WESLR_MEMORY_STATE_MODEL_V1.md`, `docs/WESLR_PROJECT_STATE_MODEL_V1.md` | scoped continuity, reviewable memory | hidden memory, perfect memory | medium | docs/wiki |
| Runtime boundary model | Developer | public | Define what runtime may not do yet | `docs/WESLR_PROJECT_CHAT_RUNTIME_BOUNDARY_V1.md`, `docs/WESLR_PROJECT_CHAT_RUNTIME_BOUNDARY_REVIEW_V1.md` | metadata-only, bounded future runtime | deployment, live answer authority | high | docs/wiki |
| API/configuration method | Developer | public | Explain safe external API configuration | `docs/API_KEY_GREEN_ZONE_V1.md`, `docs/WESLR_MATERIALS_RESEARCH_WORKFLOW_V1.md` | env vars, placeholders, redaction | literal secrets, unguarded keys | high | docs/wiki |
| Environment variables | Developer | public | List env vars and meaning | same as above | secret-backed env vars, unset defaults | secret values, inline credentials | medium | docs/wiki |
| Secret handling | Developer | public | Show safe secret rules | same as above | never commit keys, never log values | leakage, direct key printing | high | docs/wiki |
| Local/private preview limitations | Developer | public | Clarify preview boundaries | `docs/WESLR_PROJECT_CHAT_RUNTIME_BOUNDARY_V1.md`, `docs/WESLR_PUBLIC_UX_CONTRACT_V1.md` | preview-only, not live/public | production-ready claims | medium | docs/wiki |
| Known limitations | Developer | public | State what is not implemented | `docs/WESLR_PROJECT_CHAT_RUNTIME_BOUNDARY_V1.md`, `weslr/docs/WESLR_DOCTRINE_REGISTRY_V1.md` | not live, not public, not final | overpromising | medium | docs/wiki |

## 4. Operator/admin documentation

| Page title | Target reader | Label | Purpose | Source docs | Allowed claims | Forbidden claims | Draft priority | Website area |
|---|---|---|---|---|---|---|---|---|
| Invite management | Owner/operator | internal | Explain invite handling | `docs/WESLR_PUBLIC_PILOT_OCW_DEPLOYMENT_ACCESS_BOUNDARY_REVIEW_V1.md` | invite-only, approved access | open registration, uninvited access | high | internal operator docs |
| Access-control checklist | Owner/operator | internal | Check access gates before release | same as above, `docs/WESLR_PUBLIC_UX_CONTRACT_V1.md` | gated access, approval required | public launch, silent enablement | high | internal operator docs |
| Protected chat status checklist | Owner/operator | internal | Confirm protected chat is still bounded | `docs/WESLR_PROJECT_CHAT_RUNTIME_BOUNDARY_V1.md`, `docs/WESLR_PUBLIC_PILOT_OCW_DEPLOYMENT_ACCESS_BOUNDARY_REVIEW_V1.md` | protected, invite-only, approved preview | open/public status | high | internal operator docs |
| Before-publish checklist | Owner/operator | internal | Prevent bad public wording | `weslr/docs/WESLR_DOCTRINE_REGISTRY_V1.md`, `docs/WESLR_PUBLIC_UX_CONTRACT_V1.md` | candidate, planned, not live | guarantee, proof, certainty | high | internal operator docs |
| Claims/wording checklist | Owner/operator | internal | Keep claims conservative | `docs/WESLR_COGNITIVE_AI_POSITIONING_V1.md`, `docs/WESLR_PUBLIC_UX_CONTRACT_V1.md` | evidence-based, bounded, preview | AGI, conscious, certified | high | internal operator docs |
| Incident/secret handling | Owner/operator | internal | Handle leaks or risk | `docs/API_KEY_GREEN_ZONE_V1.md`, `docs/WESLR_MATERIALS_RESEARCH_WORKFLOW_V1.md` | redact, rotate, revoke, review | expose, print, preserve unsafe values | high | internal operator docs |
| Deployment readiness checklist | Owner/operator | internal | Distinguish planning from release | `docs/WESLR_PUBLIC_READINESS_PLAN_V1.md`, `docs/WESLR_PUBLIC_PILOT_OCW_DEPLOYMENT_ACCESS_BOUNDARY_REVIEW_V1.md` | planned, gated, not live | ready, launched, open-public | high | internal operator docs |

## 5. Internal source map

This is the compact source map for Nova/OCC review.

| Group | Core source docs | What to extract | What to avoid claiming | Visibility |
|---|---|---|---|---|
| Public pages | identity, doctrine, public UX, frontier doctrine | simple product explanation | AGI, certainty, launch readiness | public |
| Protected user guide | runtime boundary, project state, memory, privacy docs | access-controlled preview guidance | open/public access, unauthenticated use | protected |
| Developer docs | state models, runtime boundary, API config docs | architecture and safe integration guidance | secret values, live execution claims | public |
| Operator docs | privacy, access, deployment readiness docs | checklists, boundaries, approvals | silent enablement, public launch claims | internal |
| Legal/company mapping | public UX, privacy, readiness docs | source-linked claims only | unsupported guarantees | public/internal mix |

## 6. Navigation map

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

## 7. Normal status labels

Use these labels on pages:

- public
- protected
- internal
- draft
- planned
- not live
- preview
- gated

Avoid internal process labels on public pages.

## 8. Packaging guidance

This page plan should be readable by:

- OCC
- the owner
- Nova
- future writers or implementers

It should not be used to open access or approve deployment.

## 9. Next step

This page plan is ready for review and can be used as the source map for the next Nova documentation-planning task.
