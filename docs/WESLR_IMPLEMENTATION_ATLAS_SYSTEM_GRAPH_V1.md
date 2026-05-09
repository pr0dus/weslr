# WESLR Implementation Atlas / System Graph V1

Date: 2026-05-09
Status: definitive implementation navigation file / routing and flow reference / anti-duplication guard
Scope: current repo reality, README claims, implemented modules, partial modules, docs-only doctrine, loops, gates, CI, routing, and next-work discipline

## Purpose

This atlas is the definitive navigation file for WESLR implementation reality.

It answers:

```text
What exists?
Where does it live?
How does it route?
What calls what?
Which parts are implemented, partially wired, docs-only, or unknown?
What must be checked before changing anything?
```

It does not replace `README.md`, `weslr/README.md`, or `weslr/docs/WESLR_DOCTRINE_REGISTRY_V1.md`. It connects them into one routing and flow map.

Its purpose is to prevent duplicate architecture, repeated reinvention, and unsafe assumptions such as adding a new doctrine, loop, daemon, API surface, or UI path before checking what already exists.

## Required pre-change check

Before proposing or coding a new WESLR subsystem, future work must check:

```text
1. README.md
2. weslr/README.md
3. weslr/docs/WESLR_DOCTRINE_REGISTRY_V1.md
4. docs/WESLR_IMPLEMENTATION_ATLAS_SYSTEM_GRAPH_V1.md
5. Existing files/tests matching the intended area
```

If something already exists:

```text
extend, wire, document, test, repair, or deprecate the existing path first.
```

Do not create a parallel system unless the existing path cannot safely support the requirement.

## Routing reference rule

For future development, this atlas is the first routing reference.

When adding or changing behavior, update this file when any of the following changes:

```text
entry point
API route
UI surface
policy gate
loop/daemon
memory path
promotion path
deployment path
CI/test gate
doctrine-to-code mapping
implemented vs partial status
```

If this atlas and implementation disagree, treat that as a repo inconsistency to repair.

## README reality anchor

Root `README.md` defines WESLR as:

```text
Continuity-first entity intelligence platform.
```

It also states that the repo is no longer only a Siemens/TIA plugin repository. Siemens/TIA is one product track inside the broader WESLR platform.

README current state map:

```text
1. Core WESLR runtime
2. WESLR Public Surface
3. Industrial / Siemens TIA track
4. Frontier science / Scatti track
5. Deployment / runtime forge
```

This atlas follows that structure.

## Legend

| Status | Meaning |
|---|---|
| implemented | Concrete code exists and appears wired or directly callable |
| partially wired | Code exists but not fully connected end-to-end |
| doctrine/checkpoint | Documented and tracked, may not be runtime complete |
| docs-only | Product/architecture contract only; no runtime behavior |
| guard | Safety or policy boundary |
| test-covered | Tests exist and/or CI includes it |
| unknown | Needs deeper repo inspection |

## High-level system graph

```text
Human / public visitor / operator / agent
  ↓
Entry surface
  ├─ weslr-ui public demo shell
  ├─ test deployment API server
  ├─ backend contract module
  ├─ CLI command modules
  └─ future hosted/private deployment surfaces
  ↓
Product mode / policy gates
  ├─ public_demo_readonly
  ├─ hosted_trial
  ├─ hosted_paid_individual
  ├─ hosted_team
  ├─ private_institution
  ├─ self_hosted_admin
  ├─ operator_dev
  └─ staging
  ↓
Allowed work lanes
  ├─ public demo explanation/chat lane
  ├─ continuity / context lane
  ├─ memory / entity scope lane
  ├─ observation / insufficiency / proposal lane
  ├─ consolidation / green-zone promotion lane
  ├─ research mission loop lane
  ├─ materials / Scatti research lane
  ├─ industrial / Siemens TIA lane
  ├─ agent/API future lane
  └─ deployment/update lane
```

## Public demo routing graph

```text
Browser
  ↓
weslr-ui/src/App.tsx
  ↓
weslr-ui/src/api.ts
  ↓
POST /api/chat
  ↓
weslr-test-deployment/api_server.py
  ↓
if WESLR_PRODUCT_MODE unset or public_demo_readonly:
    weslr/public_demo_chat.py::public_demo_chat()
else:
    weslr_backend_contract.py::chat()
```

Public demo blocked route graph:

```text
Browser or caller
  ↓
/api/contract/upload-file
/api/contract/file-route
/api/contract/operator/summary
/api/contract/operator/visibility
  ↓
weslr-test-deployment/api_server.py
  ↓
weslr/public_demo_policy.py
  ↓
public_demo_block_response() or operator_visibility_response()
```

## 1. Core WESLR runtime

README key areas:

```text
meaning-vector response path
channel identity binding
entity-scoped memory namespaces
relationship depth and relationship observation capture
safe memory capture
cognitive weight guardrails
consolidation loop and promotion governance
interpretation, dialogue, continuity, semantic memory, research, and integration modules
```

Primary docs:

```text
weslr/README.md
ARCHITECTURE.md
weslr/docs/WESLR_DOCTRINE_REGISTRY_V1.md
```

Status:

```text
implemented and broad, but not all surfaces are productized.
Before changes, inspect exact module files and tests.
```

## 2. WESLR Public Surface

README public areas:

```text
front-door/
weslr-ui/
dashboard/satellite/
weslr-test-deployment/
```

### Frontend public demo shell

Status: implemented + test-covered

Files:

```text
weslr-ui/src/config.ts
weslr-ui/src/api.ts
weslr-ui/src/App.tsx
weslr-ui/scripts/check-public-demo-contract.mjs
.github/workflows/weslr-ui-build.yml
```

Current behavior:

```text
productMode = public_demo_readonly
fileUpload = false
operatorPanel = false
memoryWrites = false
deploymentControls = false
```

UI includes:

```text
read-only banner
safe example prompts
read-only welcome text
upload disabled notice
hidden operator panel
limitations footer
sanitized fallback text
```

Regression guard:

```text
npm run check:public-demo
npm run build
```

### Backend public demo policy

Status: implemented + test-covered

Files:

```text
weslr/public_demo_policy.py
weslr-test-deployment/api_server.py
weslr/tests/test_public_demo_policy.py
```

Default:

```text
WESLR_PRODUCT_MODE unset → public_demo_readonly
```

Blocked in public demo:

```text
file_upload
file_route
operator_panel
operator_summary
operator_review
deployment_controls
memory_writes
api_key_workflows
```

### Public demo chat

Status: implemented + test-covered

Files:

```text
weslr/public_demo_chat.py
weslr-test-deployment/api_server.py
weslr/tests/test_public_demo_chat.py
```

Route:

```text
POST /api/chat
```

In public mode:

```text
/api/chat → public_demo_chat()
```

Public demo chat covers:

```text
what WESLR is
governed memory
hosted vs private deployment
public demo limitations
agent/API ecosystem positioning
pricing/trial copy
safe read-only fallback
```

Explicitly blocked:

```text
memory writes
file upload
operator controls
deployment controls
external provider calls
private state exposure
```

## 3. Industrial / Siemens TIA track

README canonical areas:

```text
docs/tia-bridge/README.md
normalizer/siemens_to_weslr/README.md
schemas/
examples/
```

Status:

```text
important commercial product track.
Not the whole WESLR product.
Needs separate implementation map before major TIA changes.
```

Rule:

```text
Do not assume public WESLR, Scatti, or core memory changes belong in TIA track.
Keep industrial/TIA scope explicit.
```

## 4. Frontier science / Scatti track

README relevant areas:

```text
weslr/modules/unified_matter_generator.py
weslr/docs/WESLR_PHASE_8.5_UNIFIED_MATTER_GENERATOR_DOCTRINE.md
weslr/docs/unified matter generator.md
frontier proposal and novelty-checking commands documented in weslr/README.md
```

Additional contract:

```text
docs/WESLR_MATERIALS_RESEARCH_WORKFLOW_V1.md
```

Status:

```text
some scientific/materials reasoning exists.
Materials workflow and Scatti map are not yet a polished end-to-end product.
```

Important boundaries:

```text
candidate pre-screening, not discovery
zero hits means not found in enabled databases, not confirmed novel
Materials Project values are computational predictions, not experimental proof
heuristic fallback is not DFT
public outputs must use candidate language
```

Materials Project key rule:

```text
Allowed for research/staging Scatti work while data is gathered.
Must not be deployed into public production by default.
Private/institution deployments should configure their own keys explicitly.
```

## 5. Deployment / runtime forge

README relevant areas:

```text
weslr-test-deployment/
dashboard/
service/deployment documentation where present
future GitHub Actions or self-hosted runner workflows
```

Status:

```text
partially wired.
Current public-demo backend is test deployment API, not full production backend.
```

Deployment still missing:

```text
production mode source
auth/account system
tenant/workspace ownership runtime
rate limiting
logging/audit for hosted use
reverse proxy / Cloudflare route
staging/production split
```

## Product mode / account / deployment contracts

Status: docs-only contracts

Files:

```text
docs/WESLR_PRODUCT_MODE_MATRIX_V1.md
docs/WESLR_ACCOUNT_TENANT_AND_DATA_OWNERSHIP_V1.md
docs/WESLR_UPDATE_AND_RELEASE_PROPAGATION_CONTRACT_V1.md
docs/WESLR_AGENT_API_AND_ECOSYSTEM_POSITIONING_V1.md
docs/WESLR_MATERIALS_RESEARCH_WORKFLOW_V1.md
```

Meaning:

```text
These documents define product behavior and boundaries.
They do not by themselves implement accounts, billing, private deployment, agent API, or materials scripts.
```

Do not treat these as runtime-complete.

## Consolidation / green-zone system

Status: accepted doctrine + implemented code + tests exist

This already exists. Do not duplicate it.

Doctrine/checkpoint:

```text
weslr/docs/WESLR_DOCTRINE_REGISTRY_V1.md
weslr/docs/WESLR_CONSOLIDATION_LOOP_CHECKPOINT_V1.md
```

Implementation files:

```text
weslr/consolidation_loop.py
weslr/consolidation_config.py
weslr/consolidation_promotion.py
weslr/commands/consolidation_commands.py
weslr/tests/test_consolidation_loop.py
weslr/tests/test_consolidation_promotion.py
```

Existing graph:

```text
safe traces
  ↓
collect_traces()
  ↓
cluster_traces()
  ↓
score_cluster()
  ↓
classify_destination()
  ↓
write_digest()
  ↓
consolidation_digest.jsonl
```

Promotion graph:

```text
candidate cluster
  ↓
classify_zone()
  ├─ green
  ├─ yellow
  └─ red
  ↓
decide_promotion()
  ↓
auto_promote() only if config gates allow
  ↓
audit_log()
```

Config gates:

```text
consolidation_auto_enabled = false by default
green_zone_auto_promotion_enabled = false by default
enabled_zones = [green]
require_provenance = true
require_audit_log = true
```

Allowed green destinations currently:

```text
continuity_summary
attention_memory
digest_archive_marker
procedural_note
```

Red/blocked destination families include:

```text
doctrine
identity
governance
entity_memory
mission_store
code
external_action
research_truth
safety
alignment
```

Important correction:

```text
Do not add another green-zone refinement doctrine without first extending or reconciling this existing consolidation/green-zone system.
```

## Observation pipeline

Status: checkpoint + implemented files referenced

Files referenced in doctrine registry:

```text
contract_observation.py
contract_insufficiency_detector.py
contract_improvement_proposal_bridge.py
review_interface.py
workplace_review_surface.py
```

Graph:

```text
/chat interaction metadata
  ↓
observe
  ↓
detect insufficiency
  ↓
proposal-ready records
  ↓
review surface
```

Known boundary:

```text
Observation does not mutate behavior directly.
Insufficiency flows to proposal/review, not automatic behavior change.
```

Open issue:

```text
Post-review lifecycle is not fully defined.
Pending review records need a clear accepted/rejected/write-back path.
```

## Attention loop / proactive daemon

Status: checkpoint + daemon exists

Files referenced in doctrine registry:

```text
weslr/proactive_daemon.py
weslr/docs/WESLR_SELF_REVIEW_DISCOVERY_V1.md
weslr/docs/WESLR_ATTENTION_AND_RESEARCH_WORK_LOOP_CHECKPOINT_V1.md
```

Purpose:

```text
self-review loop for architecture gaps, validation gaps, stale checkpoints, missing lifecycle links, doctrine/implementation drift, and operator attention routing
```

Known safety rule:

```text
WESLR may observe, detect, prioritize, and suggest.
WESLR may not silently mutate, execute, self-code, approve, commit, push, or change doctrine/contracts.
```

Open questions:

```text
source adapter model
suggestion store path
operator-visible review surface
eventual scheduling policy
```

## Research work loop / mission system

Status: implemented V1 with tests, but some surfaces incomplete

Files referenced in doctrine registry:

```text
weslr/schemas/mission.py
weslr/mission_store.py
weslr/adapters/local_evidence_adapter.py
weslr/loop/safety_filter.py
weslr/loop/suggestion_ranker.py
weslr/loop/research_work_loop.py
weslr/commands/mission_commands.py
weslr/tests/test_mission_store.py
weslr/tests/test_research_work_loop_v1.py
weslr/tests/test_mission_commands_v1.py
```

Graph:

```text
mission definition
  ↓
MissionStore
  ↓
LocalEvidenceAdapter
  ↓
SafetyFilter
  ↓
SuggestionRanker
  ↓
run_once_mission_review()
  ↓
pending_messages.jsonl
```

Status notes:

```text
manual run_once only
local evidence only
no automatic execution
safety filter active
tenant isolation enforced
suggestions written for operator review
```

Not complete:

```text
workplace surface integration
V2 cadence scheduling
external literature adapter
full review lifecycle
```

## Agent/API lane

Status: docs-only product direction

File:

```text
docs/WESLR_AGENT_API_AND_ECOSYSTEM_POSITIONING_V1.md
```

Positioning:

```text
Use WESLR directly.
Deploy WESLR privately.
Connect compatible agents/tools to WESLR.
```

Current state:

```text
No public Agent API implementation should be claimed.
Agent/API integrations are planned mostly for private/institution deployments.
```

## CI / quality gates

Status: implemented

Workflows:

```text
.github/workflows/ci.yml
.github/workflows/weslr-ui-build.yml
```

Python minimal CI:

```text
compile WESLR package
import core package
Lane 1 pure unit pilot
```

Current Lane 1 includes:

```text
weslr/request_intelligence/tests/test_classifier.py
weslr/tests/test_safety_contract.py
weslr/tests/test_fact_extractor_v1.py
weslr/tests/test_public_demo_policy.py
weslr/tests/test_public_demo_chat.py
```

UI CI includes:

```text
npm install
npm run check:public-demo
npm run build
```

## Recent public-product PR sequence

Merged:

```text
PR #25 — harden weslr-ui public demo shell
PR #26 — add weslr-ui build CI
PR #27 — add weslr-ui public demo contract check
PR #28 — enforce backend public demo policy
PR #29 — add public demo chat contract
```

Closed intentionally:

```text
PR #30 — Green-Zone Intelligence Refinement V1
Reason: duplicate-risk; existing consolidation/green-zone doctrine and implementation already exists.
```

## Anti-duplication checklist

Before proposing a new feature or doctrine, answer:

```text
1. Does README.md already name this as a track?
2. Does weslr/README.md document commands/modules for this?
3. Does the Doctrine Registry already define this?
4. Is there a checkpoint document for it?
5. Is there already a Python module or command for it?
6. Are tests already present?
7. Is it implemented, partially wired, docs-only, or unknown?
8. Should the right move be wire/test/repair instead of add?
```

## Current best next deep-work targets

Recommended next targets should be chosen from known gaps, not guessed.

High-value options:

```text
1. Expand this atlas with generated module inventory by directory.
2. Map public demo live deployment path to chat.weslr.de.
3. Inspect existing cognitive weight / refinement files specifically.
4. Define review lifecycle for observation/proposal records.
5. Wire research work loop suggestions into workplace/public-private UI surface.
6. Build Scatti materials source/tool/script map from existing modules.
7. Create a visual graph artifact from this atlas.
```

## V1 verdict

```text
WESLR_IMPLEMENTATION_ATLAS_SYSTEM_GRAPH_V1_DEFINED
```
