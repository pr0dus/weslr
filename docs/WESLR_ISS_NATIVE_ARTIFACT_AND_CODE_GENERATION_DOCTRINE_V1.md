[Sun 2026-05-31 21:45 GMT+2] WESLR ISS Native Artifact and Code Generation Doctrine V1
Status
Internal doctrine only. Not public wording. Not marketing wording.

This document defines the internal direction for WESLR as an ISS-aligned system with native artifact and code-generation capabilities.

ISS means, internally:

Intelligence Superstructure / Integrated Self-Sustaining System

This is not an AGI claim, not a consciousness claim, not a sentience claim, not a public benchmark claim, and not a public product claim.

For public wording, use safer language such as:

governed intelligence system
continuity-first architecture
evidence-aware improvement
operator-approved evolution
replay-tested behavior refinement
controlled general-capability roadmap
Do not use ISS publicly unless separately approved by the owner.

1. Core Doctrine
WESLR is not intended to remain only a chat responder.

WESLR is intended to become a governed, Python-native cognition and artifact system capable of moving from:

owner idea
→ domain understanding
→ research conversation
→ architecture
→ stack decision
→ file manifest
→ code/artifact generation
→ validation
→ repair loop
→ friction capture
→ replay-proven improvement
→ behavior-pack growth
This is the path from WESLR as a bounded cognition system toward WESLR as an internal ISS.

The goal is not to imitate an LLM by predicting text.

The goal is to become a governed intelligence runtime that can understand a task, form a project, generate bounded artifacts, validate them, and improve through friction.

2. Current Milestone Snapshot
Current relevant chain already implemented:

Broad Topic Ontology V1
Broad Topic Domain Intake V1 with ontology integration
Research Conversation Planner V1 with ontology integration
Privacy Sensitive Technology Boundary V1
V1.01 internal friction-trained improvement proof
Friction case capture
Friction replay harness
Friction update proposal bridge
Initial friction proposal realization
Friction pattern miner
Friction replay suite builder
Friction training proof report runner
Behavior pack registry
Behavior pack promotion policy
Recent planner integration commit:

946d0ffcfddb7b9443f480300c580266810debe2
Final judgment from that lane:

research_planner_ontology_integration_ready_for_broad_topic_seed_cases
Protected files remained untouched:

weslr/chat_responder.py
weslr/main.py
dialogue.py
chat_ui.py
3. Why Broad Research Planning Is Not Enough
The broad-topic stack can now classify and plan for topics such as:

WiFi/RF sensing
metamaterials
theory of mind
philosophy of mind
AI agent architecture
medical software
industrial automation
energy systems
legal/privacy
language/vocabulary
software product planning
unknown future topics
But this is still not enough for the owner’s intended workflow.

The owner does not only want to ask WESLR questions.

The owner wants to work with WESLR like a capable development partner:

discuss idea
→ shape concept
→ choose architecture
→ decide language/stack
→ generate files
→ create scripts
→ validate outputs
→ iterate
→ grow the project
Therefore, the next doctrine layer is:

WESLR Native Artifact and Code Generation Engine

4. WESLR Without OCC
OCC is currently the implementation helper, but OCC must not be assumed to live inside WESLR.

Future WESLR must have its own governed artifact workspace.

WESLR should be able to:

create project briefs
create architecture documents
decide initial technology stack
generate file manifests
generate starter files
generate scripts/snippets/components
create tests
validate files
parse errors
propose patches
export artifacts
track friction
grow behavior packs from repeated project failures
OCC may remain useful during development, but WESLR’s long-term artifact ability must not depend on OCC being present.

5. Code Generation Without an LLM
WESLR without an LLM can still generate code and files, but it must do so through governed mechanisms.

Allowed no-model generation sources:

5.1 Template generation
Generate known, bounded structures:

README files
architecture docs
Markdown reports
simple Python CLIs
config files
test skeletons
basic HTML/CSS/JS pages
project manifests
5.2 Schema / AST generation
Generate safer structured code using schemas, typed packets, AST helpers, and known file templates.

This should be preferred over free-form uncontrolled code generation when possible.

5.3 Pattern libraries
Use validated reusable code patterns:

Python module skeletons
CLI command patterns
JSON/YAML schema patterns
Flask/FastAPI-style service skeletons
static HTML/CSS/JS components
test harness patterns
validation runners
5.4 Test-driven repair
WESLR can generate small code units, run validation, parse deterministic failures, and propose bounded patches.

The loop:

generate small unit
→ run syntax/tests
→ parse deterministic error
→ propose patch
→ rerun tests
→ capture friction if unresolved
5.5 Optional governed provider layer
An LLM or code model may later be used as an optional provider, but only under WESLR governance.

The provider may draft code, but WESLR must control:

scope
file permissions
allowed edits
validation
tests
safety boundaries
approval
rollback
public claims
The model must not become WESLR’s identity or authority.

6. Quantity and Chunking Doctrine
WESLR should not try to generate an entire application in one response.

Large work must be chunked into bounded work packets:

packet 1: project brief
packet 2: architecture
packet 3: stack decision
packet 4: file manifest
packet 5: scaffold
packet 6: module A
packet 7: tests
packet 8: validation
packet 9: patch
packet 10: export
A “quantity maximum” should be managed by:

file count limits
line count limits
allowed path rules
validation budget
dependency restrictions
risk class
owner approval level
The goal is not one huge generation.

The goal is a controlled sequence of buildable artifacts.

7. Native Artifact Engine Architecture
Future modules should form a pipeline like this:

research_conversation_plan
→ project_brief_builder
→ architecture_planner
→ stack_decision_helper
→ file_manifest_builder
→ code_scaffold_generator
→ artifact_writer_boundary
→ validation_runner
→ patch_feedback_loop
→ artifact_exporter
→ friction_capture
→ behavior_pack_candidate
7.1 Project Brief Builder
Future helper:

weslr/project_brief_builder.py
Purpose:

Convert a research conversation plan into a project brief.

The brief should include:

project purpose
owner goal
domain classification
risks/boundaries
intended users
non-goals
acceptance criteria
evidence needs
validation needs
7.2 Architecture Planner
Future helper:

weslr/project_architecture_planner.py
Purpose:

Create architecture options and choose a bounded initial architecture.

Should include:

components
data flow
local/cloud decision
storage choice
interface choice
validation points
privacy/safety boundary points
future extension points
7.3 Stack Decision Helper
Future helper:

weslr/project_stack_decision_helper.py
Purpose:

Choose an initial technology stack based on:

project type
owner skill/context
deployment target
validation needs
safety/privacy needs
available runtime
Typical stack choices:

Python for cognition/backend/scripts/prototypes
HTML/CSS/JS for public UI and dashboards
YAML/JSON for config/manifests/schemas
Markdown for docs/reports/handover
SQL/SQLite for local persistence
shell scripts for validation/deployment helpers
7.4 File Manifest Builder
Future helper:

weslr/file_manifest_builder.py
Purpose:

Create a safe file plan before any file is written.

Manifest should include:

paths
file types
purpose
generation method
overwrite policy
validation command
risk labels
owner approval requirement
7.5 Code Scaffold Generator
Future helper:

weslr/code_scaffold_generator.py
Purpose:

Generate starter files from templates/patterns/schemas.

Must not create unsafe, unbounded, hidden, or auto-executing behavior.

7.6 Artifact Writer Boundary
Future helper:

weslr/artifact_writer_boundary.py
Purpose:

Control whether WESLR may create/edit/delete files.

Required decisions:

create allowed
edit allowed
delete allowed
overwrite allowed
executable file allowed
dependency install allowed
test execution allowed
owner approval required
7.7 Validation Runner
Future helper:

weslr/code_validation_runner.py
Purpose:

Run safe validation commands, such as:

syntax checks
unit tests
schema validation
static safety checks
file manifest conformance
release-gate-style checks
No unapproved network, dependency install, destructive commands, or privileged commands.

7.8 Patch Feedback Loop
Future helper:

weslr/patch_feedback_loop.py
Purpose:

Use deterministic validation failures to propose bounded patches.

Must not auto-apply without approved policy.

7.9 Artifact Exporter
Future helper:

weslr/artifact_exporter.py
Purpose:

Package generated files/artifacts for the owner.

Should support:

Markdown reports
zip/export bundles
project skeletons
generated docs
validation reports
8. Example: WiFi/RF Sensing Self-Care Project
If the owner says:

I want to explore WiFi sensing for self-care because one day I may forget medication or eating.
Future WESLR should:

Classify the topic:

privacy-sensitive technology
RF/WiFi sensing
assistive health/safety
medical-claim-adjacent
human-subject involved
Apply boundary:

consent-based
lawful/responsible use
local-first recommended
data minimization required
no covert tracking
no diagnosis/treatment claims
validation required before reliance
Create research plan:

what can be explored safely
what evidence is needed
what claims are forbidden
what prototype scope is safe
Create project brief:

local self-care routine-awareness prototype
no diagnosis
reminder/anomaly awareness only
user-controlled rules
explicit emergency escalation permission
Create architecture:

local signal ingestion
preprocessing
event/routine detector
reminder rule engine
local storage
privacy/audit layer
simple dashboard
Choose stack:

Python prototype
local SQLite
YAML config
simple HTML dashboard later
pytest validation
Generate initial files:

README.md
docs/ARCHITECTURE.md
requirements.txt
config.example.yaml
src/
tests/
Validate:

syntax
tests
schema
safety boundaries
Capture friction:

weak architecture
missing validation
unclear boundary
unsafe implication
code failure
Improve:

replay
proposal
owner approval
behavior-pack update
9. Public-Facing Artifact Capabilities
WESLR must eventually generate public-facing artifacts, but with governed boundaries.

Artifact types:

static HTML/CSS/JS previews
public website sections
dashboards
reports
product docs
legal/support docs
project landing pages
operator consoles
Python remains the core intelligence/runtime layer, but WESLR must support other artifact target languages:

HTML
CSS
JavaScript
Markdown
YAML
JSON
SQL
shell scripts
possibly TypeScript later
WESLR should understand that public-facing software requires UI languages, not only Python.

10. Safety and Authority Doctrine
WESLR must distinguish between:

thinking/planning
generating text
generating files
editing files
executing tests
installing dependencies
deploying
deleting
publishing
Each requires a separate authority level.

No hidden escalation.

No silent file edits.

No automatic deployment.

No public publishing without explicit owner approval.

No unsafe code generation.

No raw private data storage by default.

No public ISS wording.

No AGI/consciousness/sentience/Turing/certification claims.

11. Artifact Authority Levels
Suggested future authority ladder:

Level 0 — Plan only
WESLR may create project plans and file manifests as metadata.

Level 1 — Generate text artifacts
WESLR may generate Markdown/docs/snippets for owner review.

Level 2 — Generate sandbox files
WESLR may create files in a controlled sandbox/project workspace.

Level 3 — Validate files
WESLR may run safe syntax/tests/schema checks.

Level 4 — Propose patches
WESLR may propose changes based on validation failures.

Level 5 — Apply approved patches
WESLR may apply changes after explicit approval.

Level 6 — Export artifacts
WESLR may package results for owner download/review.

Level 7 — Deploy/publish
Requires separate explicit approval and stronger release gates.

12. Friction-Driven Growth for Code Work
Code/artifact failures must feed the same WESLR learning loop:

artifact failure
→ friction case
→ replay/test failure
→ pattern mining
→ update proposal
→ owner approval
→ realization
→ proof report
→ behavior-pack improvement
Example friction types:

bad architecture choice
wrong language/stack
file manifest missing tests
generated script syntax error
unsafe dependency
validation failure
unclear README
weak UI structure
incorrect privacy boundary
unsupported medical claim
brittle code pattern
Future behavior packs:

Python CLI tool pack
static website pack
research prototype pack
privacy-sensitive technology prototype pack
medical-software pathway planning pack
industrial automation helper pack
WESLR self-development pack
legal/privacy document pack
materials discovery research pack
13. What WESLR Can and Cannot Do Without an LLM
Can do without an LLM, after implementation
generate structured docs
generate known project scaffolds
generate simple scripts from templates
generate configs/manifests/schemas
generate test skeletons
validate generated code
parse deterministic errors
propose bounded patches
grow pattern libraries
improve behavior packs through friction
Cannot yet do without an LLM
arbitrary large novel code generation
deep library-specific implementation from memory
complex UI design from vague intent
broad fluent code explanation at LLM level
large multi-file app generation without templates/patterns
reliable novel algorithms without evidence/testing
Optional future provider
An LLM/code model may be used later as a subordinate provider.

WESLR remains the authority.

14. Required Next Design Lane
Recommended next lane:

DESIGN_WESLR_NATIVE_ARTIFACT_AND_CODE_GENERATION_ENGINE_V1
This design should define:

artifact workspace
project brief builder
architecture planner
stack decision helper
file manifest builder
code scaffold generator
artifact writer boundary
validation runner
patch feedback loop
export/package mechanism
code/artifact friction cases
artifact behavior packs
authority levels
15. Final Doctrine
WESLR’s path is not:

chatbot → better chatbot
WESLR’s path is:

governed cognition
→ broad-topic understanding
→ research planning
→ artifact formation
→ code generation
→ validation
→ friction-driven improvement
→ behavior-pack growth
→ internal ISS capability
WESLR should become able to work with the owner on real projects without depending on OCC living inside it.

OCC is the current builder.

WESLR is the system being built.

The long-term goal is WESLR-native capability:

understand
plan
generate
validate
repair
remember
improve
govern
This doctrine is internal-only and should guide the next architecture design.// Save this exact text to a .MD file in docs