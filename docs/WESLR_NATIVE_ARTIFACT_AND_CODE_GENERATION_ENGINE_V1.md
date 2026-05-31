# WESLR Native Artifact and Code Generation Engine V1

## 1. Executive doctrine

WESLR is not meant to remain only a chat responder.

Its internal trajectory is:

governed cognition → broad-topic understanding → research planning → artifact formation → code generation → validation → repair → friction-driven improvement → behavior-pack growth → internal ISS capability

This is:
- not an AGI achievement claim
- not public wording
- not public readiness
- not autonomous self-modification
- not a hidden LLM wrapper
- a governed artifact/code-generation architecture

## 2. Current capability baseline

Already in place:
- Broad Topic Ontology V1
- Broad Topic Domain Intake V1 with ontology integration
- Research Conversation Planner V1 with ontology integration
- Privacy Sensitive Technology Boundary V1
- Friction case capture / replay / proposal / proof
- Behavior Pack Registry
- Behavior Pack Promotion Policy

Missing for native artifact/code generation:
- project brief builder
- architecture planner
- stack decision helper
- file manifest builder
- code scaffold generator
- artifact writer boundary
- validation runner
- patch feedback loop
- artifact exporter
- code/artifact friction cases
- project behavior packs

## 3. WESLR without OCC

OCC currently edits the repo, runs tests, and implements lanes.

Future WESLR must not assume OCC lives inside it.

It needs its own governed workspace ability to:
- create files
- edit files
- validate files
- run safe tests
- propose patches
- export artifacts
- record friction
- improve behavior packs

Every authority level must be explicit and bounded.

## 4. Code generation without an LLM

WESLR can generate useful artifacts without a model if it relies on governed, bounded sources.

### 4.1 Template generation
Good for:
- README files
- architecture docs
- config files
- basic scripts
- simple HTML/CSS/JS
- test skeletons
- project manifests

### 4.2 Schema / AST generation
Good for:
- structured Python modules
- JSON/YAML schemas
- typed packets
- predictable file forms

### 4.3 Pattern libraries
Good for:
- validated snippets
- known project skeletons
- CLI patterns
- dashboard patterns
- static website patterns
- test harness patterns

### 4.4 Test-driven repair
Loop:
- generate small unit
- run syntax/tests
- parse deterministic failure
- propose bounded patch
- rerun validation

### 4.5 Optional governed provider
A future LLM/code model may draft code, but WESLR controls:
- scope
- file permissions
- allowed edits
- validation
- tests
- safety boundaries
- approval
- rollback

The model must not become identity or authority.

## 5. Quantity and chunking doctrine

WESLR should not generate an entire application in one response.

Large work must be split into bounded packets:
1. project brief
2. architecture
3. stack decision
4. file manifest
5. scaffold
6. module A
7. tests
8. validation
9. patch
10. export

Quantity constraints:
- max files per packet
- max lines per file
- allowed paths
- overwrite policy
- dependency policy
- validation budget
- risk class
- owner approval level

## 6. Native artifact engine architecture

Future module pipeline:

`research_conversation_plan → project_brief_builder → architecture_planner → stack_decision_helper → file_manifest_builder → code_scaffold_generator → artifact_writer_boundary → validation_runner → patch_feedback_loop → artifact_exporter → friction_capture → behavior_pack_candidate`

### 6.1 `weslr/project_brief_builder.py`
Purpose: convert a research conversation plan into a buildable project brief.

Reuses:
- ontology packet
- domain intake
- research conversation plan
- privacy-sensitive boundary metadata

Must not:
- write files
- claim production readiness
- skip safety/legal/medical/privacy boundaries

Authority: metadata-only first; later may feed governed file generation.

### 6.2 `weslr/project_architecture_planner.py`
Purpose: create architecture options and select a safe initial architecture.

Outputs:
- components
- data flow
- local/cloud decision
- storage choice
- interface choice
- validation points
- privacy/safety checkpoints
- future extension points

Must not:
- overreach into deployment
- bypass boundary review
- imply diagnosis/treatment authority

Authority: metadata-only first.

### 6.3 `weslr/project_stack_decision_helper.py`
Purpose: choose a technology stack.

Typical stack targets:
- Python
- HTML
- CSS
- JavaScript
- Markdown
- YAML
- JSON
- SQL/SQLite
- shell scripts
- possibly TypeScript later

Rules:
- Python remains core cognition/backend/prototype language.
- HTML/CSS/JS are needed for public-facing UI/dashboard artifacts.
- YAML/JSON for config/manifests.
- Markdown for docs/reports.
- SQL/SQLite for local persistence.
- Shell scripts only for safe validation/deployment helpers.

Authority: metadata-only first.

### 6.4 `weslr/file_manifest_builder.py`
Purpose: create a safe file plan before writing anything.

Manifest fields:
- file path
- file type
- purpose
- generation method
- overwrite policy
- validation command
- risk labels
- owner approval required
- safe to create
- safe to edit
- safe to execute

Must block:
- path traversal
- hidden destructive writes
- credential files
- `.weslr` writes unless separately approved
- protected runtime files unless explicitly approved
- unsafe executable generation

Authority: metadata-only; gates future file authority.

### 6.5 `weslr/code_scaffold_generator.py`
Purpose: generate bounded starter code from templates/pattern libraries.

Allowed initial generation:
- Python package skeleton
- simple CLI
- pytest skeleton
- config example
- README
- architecture doc
- static HTML dashboard skeleton
- JSON/YAML schema

Must not:
- generate covert/surveillance code
- generate medical diagnosis/treatment logic
- install dependencies
- execute untrusted commands
- write files without writer boundary approval

Authority: candidate generation only; no direct write power by default.

### 6.6 `weslr/artifact_writer_boundary.py`
Purpose: decide whether WESLR may create/edit/delete/export files.

Authority levels:
- Level 0 — Plan only
- Level 1 — Generate text artifacts for review
- Level 2 — Generate sandbox files
- Level 3 — Validate files
- Level 4 — Propose patches
- Level 5 — Apply approved patches
- Level 6 — Export artifacts
- Level 7 — Deploy/publish

Level 7 always requires separate explicit approval.

### 6.7 `weslr/code_validation_runner.py`
Purpose: run safe validation commands.

Allowed validation:
- Python syntax check
- pytest
- JSON/YAML schema validation
- markdown checks if local
- HTML static checks if local
- manifest conformance checks

Forbidden:
- unapproved network
- dependency installation without approval
- privileged commands
- destructive commands
- deployment
- credential access
- hidden background processes

Authority: validation-only.

### 6.8 `weslr/patch_feedback_loop.py`
Purpose: use deterministic validation failures to propose bounded patches.

Flow:
validation failure → classify error → identify affected file → propose patch → owner approval or allowed auto-fix policy → rerun validation → capture friction if unresolved

Must not auto-apply high-risk patches.

Authority: proposal only until approved.

### 6.9 `weslr/artifact_exporter.py`
Purpose: package generated artifacts for owner review.

Exports:
- Markdown report
- project skeleton zip
- validation report
- file manifest
- patch summary
- handover prompt/package

Must not publish publicly or deploy.

Authority: export only, no public publishing.

## 7. Project brief builder design

`weslr/project_brief_builder.py`

Purpose: convert a research conversation plan into a buildable project brief.

Inputs:
- ontology packet
- domain intake
- research conversation plan
- boundary packet
- owner goal
- evidence needs
- risk labels

Outputs:
- project purpose
- target user
- non-goals
- constraints
- risks
- evidence requirements
- acceptance criteria
- safe first milestone

Must not:
- write files
- claim production readiness
- skip safety/legal/medical/privacy boundaries

## 8. Architecture planner design

`weslr/project_architecture_planner.py`

Purpose: create architecture options and select a safe initial architecture.

Outputs:
- components
- data flow
- local/cloud decision
- storage choice
- interface choice
- validation points
- privacy/safety checkpoints
- future extension points

For privacy/health-sensitive projects, prefer:
- local-first
- data minimization
- explicit consent model
- auditability
- no diagnosis/treatment authority unless a regulated pathway is chosen

## 9. Stack decision helper design

`weslr/project_stack_decision_helper.py`

Purpose: choose a technology stack.

Possible target languages/artifact types:
- Python
- HTML
- CSS
- JavaScript
- Markdown
- YAML
- JSON
- SQL/SQLite
- shell scripts
- possibly TypeScript later

Rules:
- Python remains core cognition/backend/prototype language.
- HTML/CSS/JS are needed for public-facing UI/dashboard artifacts.
- YAML/JSON for config/manifests.
- Markdown for docs/reports.
- SQL/SQLite for local persistence.
- Shell scripts only for safe validation/deployment helpers.

## 10. File manifest builder design

`weslr/file_manifest_builder.py`

Purpose: create a safe file plan before writing anything.

Manifest fields:
- file path
- file type
- purpose
- generation method
- overwrite policy
- validation command
- risk labels
- owner approval required
- safe to create
- safe to edit
- safe to execute

Must block:
- path traversal
- hidden destructive writes
- credential files
- `.weslr` state writes unless separately approved
- protected runtime files unless explicitly approved
- unsafe executable generation

## 11. Code scaffold generator design

`weslr/code_scaffold_generator.py`

Purpose: generate bounded starter code from templates/pattern libraries.

Allowed initial generation:
- Python package skeleton
- simple CLI
- pytest skeleton
- config example
- README
- architecture doc
- static HTML dashboard skeleton
- JSON/YAML schema

Must not:
- generate covert/surveillance code
- generate medical diagnosis/treatment logic
- install dependencies
- execute untrusted commands
- write files without writer boundary approval

## 12. Artifact writer boundary design

`weslr/artifact_writer_boundary.py`

Purpose: decide whether WESLR may create/edit/delete/export files.

Authority ladder:
- Level 0 — Plan only
- Level 1 — Generate text artifacts for review
- Level 2 — Generate sandbox files
- Level 3 — Validate files
- Level 4 — Propose patches
- Level 5 — Apply approved patches
- Level 6 — Export artifacts
- Level 7 — Deploy/publish

No hidden escalation.

## 13. Code validation runner design

`weslr/code_validation_runner.py`

Purpose: run safe validation commands.

Allowed validation:
- Python syntax check
- pytest
- JSON/YAML schema validation
- markdown checks if local
- HTML static checks if local
- manifest conformance checks

Forbidden:
- unapproved network
- dependency installation without approval
- privileged commands
- destructive commands
- deployment
- credential access
- hidden background processes

## 14. Patch feedback loop design

`weslr/patch_feedback_loop.py`

Purpose: use deterministic validation failures to propose bounded patches.

Flow:
validation failure → classify error → identify affected file → propose patch → owner approval or allowed auto-fix policy → rerun validation → capture friction if unresolved

Must not auto-apply high-risk patches.

## 15. Artifact exporter design

`weslr/artifact_exporter.py`

Purpose: package generated artifacts for owner review.

Exports:
- Markdown report
- project skeleton zip
- validation report
- file manifest
- patch summary
- handover prompt/package

Must not publish publicly or deploy.

## 16. Example workflow: WiFi/RF sensing self-care project

Owner says:
“I want to explore WiFi sensing for self-care because one day I may forget medication or eating.”

Future WESLR workflow:
1. classify topic with ontology
2. domain intake: privacy-sensitive technology + assistive health support
3. boundary: consent-based, lawful, local-first, no diagnosis/treatment claims
4. research plan: evidence needs, risks, prototype constraints
5. project brief: local routine-awareness research prototype
6. architecture:
   - local signal ingestion
   - preprocessing
   - event/routine detector
   - reminder rule engine
   - local storage
   - privacy/audit layer
   - dashboard
7. stack:
   - Python prototype
   - SQLite
   - YAML config
   - simple HTML dashboard later
   - pytest validation
8. generated starter files:
   - `README.md`
   - `docs/ARCHITECTURE.md`
   - `requirements.txt`
   - `config.example.yaml`
   - `src/`
   - `tests/`
9. validation
10. friction capture and improvement

Must not:
- provide covert tracking deployment
- claim medical diagnosis
- claim treatment recommendation
- claim clinical reliability without validation/regulatory pathway

## 17. Public-facing artifact capabilities

WESLR should eventually generate:
- static HTML/CSS/JS previews
- public website sections
- dashboards
- reports
- product docs
- legal/support docs
- project landing pages
- operator consoles

But public-facing output requires separate public-claim checks and owner approval.

## 18. Safety and authority doctrine

WESLR must distinguish:
- thinking/planning
- generating text
- generating files
- editing files
- executing tests
- installing dependencies
- deploying
- deleting
- publishing

Each needs separate authority.

No silent file edits.
No automatic deployment.
No public publishing without explicit approval.
No unsafe code generation.
No raw private data storage by default.
No public ISS wording.
No AGI/consciousness/sentience/Turing/certification claims.

## 19. Code/artifact friction loop

Artifact failures must feed the same WESLR improvement loop:

artifact failure → friction case → replay/test failure → pattern mining → update proposal → owner approval → realization → proof report → behavior-pack improvement

Examples:
- wrong architecture
- wrong stack
- file manifest missing tests
- syntax error
- unsafe dependency
- validation failure
- unclear README
- weak UI
- unsupported medical claim
- privacy boundary mismatch

## 20. Artifact behavior packs

Future behavior packs:
- Python CLI tool pack
- static website pack
- research prototype pack
- privacy-sensitive technology prototype pack
- medical-software pathway planning pack
- industrial automation helper pack
- WESLR self-development pack
- legal/privacy document pack
- materials discovery research pack

Packs remain internal and governed unless separately approved.

## 21. What WESLR can and cannot do without an LLM

Can do after implementation:
- structured docs
- known project scaffolds
- simple scripts from templates
- configs/manifests/schemas
- test skeletons
- validation
- deterministic patch proposals
- pattern library growth
- behavior-pack improvement

Cannot yet do without LLM:
- arbitrary large novel software
- deep library-specific implementation from memory
- complex UI from vague intent
- broad fluent code explanation at LLM level
- large multi-file app generation without templates/patterns
- reliable novel algorithms without evidence/testing

## 22. Optional provider layer

Future optional provider architecture:
- LLM/code model can draft
- WESLR scopes and validates
- WESLR owns authority
- model output is candidate artifact, not truth
- provider use must be recorded
- provider use cannot bypass boundaries

## 23. Minimal implementation sequence

Recommended design-to-code sequence:
1. `IMPLEMENT_WESLR_PROJECT_BRIEF_BUILDER_V1`
2. `IMPLEMENT_WESLR_PROJECT_ARCHITECTURE_PLANNER_V1`
3. `IMPLEMENT_WESLR_PROJECT_STACK_DECISION_HELPER_V1`
4. `IMPLEMENT_WESLR_FILE_MANIFEST_BUILDER_V1`
5. `IMPLEMENT_WESLR_CODE_SCAFFOLD_GENERATOR_V1`
6. `IMPLEMENT_WESLR_ARTIFACT_WRITER_BOUNDARY_V1`
7. `IMPLEMENT_WESLR_CODE_VALIDATION_RUNNER_V1`
8. `IMPLEMENT_WESLR_PATCH_FEEDBACK_LOOP_V1`
9. `IMPLEMENT_WESLR_ARTIFACT_EXPORTER_V1`
10. `IMPLEMENT_WESLR_ARTIFACT_FRICTION_CASES_V1`

Why project brief builder comes first: it converts the research plan into a buildable, bounded project object before any architecture, stack, manifest, or file decision can be made.

## 24. Relationship to current broad-topic pipeline

Current upstream chain:
- `broad_topic_ontology.py`
- `broad_topic_domain_intake.py`
- `research_conversation_planner.py`
- `privacy_sensitive_technology_boundary.py`

Future downstream chain:
- project brief
- architecture
- stack
- file manifest
- scaffold
- validation
- friction

## 25. Boundaries

This is:
- design only
- no runtime changes
- no chat route changes
- no file-writing authority granted
- no model/provider/search/advisor calls
- no `.weslr` writes
- no raw private data
- no public ISS wording
- no AGI/consciousness/sentience/Turing/certification claims
- no protected runtime files touched

## 26. Final judgment

`native_artifact_code_generation_engine_design_ready_for_project_brief_builder`
