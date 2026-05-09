# WESLR Materials Research Workflow V1

Date: 2026-05-09
Status: research/coding workflow contract — no runtime implementation
Scope: Scatti/CaSc2TiO6, Materials Project key handling, materials validation workflow, tool installation guidance, script generation, coding boundaries

## Purpose

This document defines how WESLR should support materials research workflows such as Scatti/CaSc2TiO6 while keeping API keys, generated scripts, scientific claims, and coding actions governed.

WESLR should eventually help users and researchers:

- map what databases/tools to use
- identify what to install
- generate validation scripts
- run safe read-only checks
- produce screening reports
- track evidence and limitations
- propose next computational or experimental steps

But WESLR must not overclaim scientific discovery, expose secrets, or execute unsafe code without governance.

## Current key decision

The `MATERIALS_PROJECT_API_KEY` may remain available for the Scatti/materials research lane while more data is gathered.

However:

```text
The key must not be deployed into public production by default.
```

Production deployments must either:

1. remove/disable the key, or
2. require an explicit customer/operator configuration for a materials research lane.

## API key lifecycle

### Research/staging lane

Allowed:

- read-only Materials Project lookups
- manually triggered validation workflows
- formula/system checks
- thermodynamic metadata retrieval
- screening report support

Required:

- secret-backed key storage
- no logging key value
- no committing key
- no frontend/browser exposure
- no automatic publication
- operator-reviewed results

### Hosted public demo

Blocked:

- public API key access
- user-triggered Materials Project calls through anonymous public demo
- browser-side key exposure
- automatic Scatti claims

### Hosted paid/user mode

Future optional feature only.

Rules:

- server-side only
- quota/rate limits
- audit trail
- no key leakage
- outputs labeled as screening/research support

### Private/institutional deployment

Customer may configure their own keys.

Rules:

- customer-owned secret storage
- customer deployment policy
- no bundled WESLR research key by default
- explicit setup documentation

### Production deployment rule

Before production deployment, deployment checks should eventually verify:

```text
MATERIALS_PROJECT_API_KEY is absent or explicitly enabled for the intended research mode.
```

## Materials research map

WESLR should maintain a map of what to test, where to search, and what tools/scripts are needed.

### Database / knowledge sources

Potential source categories:

- crystallographic databases
- computed materials repositories
- literature databases
- preprint servers
- code repositories
- synthesis/protocol references

Examples:

- Materials Project
- COD
- OQMD
- AFLOW
- NOMAD
- PubMed
- arXiv
- Google Scholar manual fallback
- repository/source-code references for CSP or DFT workflows

### Computational tools

Potential tool categories:

- formula parsing and chemistry checks
- structure generation / crystal structure prediction
- structure relaxation
- DFT calculation setup
- thermodynamic stability analysis
- bandgap/property estimation
- report generation

Possible tools/libraries:

- pymatgen
- ASE
- pyxtal
- spglib
- numpy/scipy
- matplotlib for plots
- Quantum ESPRESSO or VASP for serious DFT when available
- workflow scripts for database lookups and report generation

## What WESLR should generate

WESLR should be able to propose or create scripts for:

1. formula normalization
2. charge-balance checks
3. oxidation-state checks
4. database lookup wrappers
5. exact/variant formula search
6. materials system search
7. candidate evidence table generation
8. structure-generation input preparation
9. DFT input template generation
10. screening report generation
11. benchmark/log capture
12. reproducibility metadata capture

## Coding capability requirement

For materials workflows, WESLR must eventually be able to generate code similarly to a coding agent, but with stricter governance.

WESLR coding should be:

```text
contract-first
repo-scoped
reversible
tested
operator-reviewed for risky actions
secret-safe
scientific-claim-safe
```

WESLR may generate scripts, but it must distinguish:

- generating code
- running code
- calling external APIs
- writing memory
- publishing reports
- deploying services

Each has different risk.

## Coding mode boundaries

### Green coding actions

Allowed with low friction:

- generate local read-only scripts
- add documentation
- add tests
- create dry-run tools
- parse public/static files
- produce non-public draft reports

### Yellow coding actions

Require operator review:

- external API calls
- dependency changes
- scripts that write files
- report generation used for public claims
- memory writes from research results
- workflow automation

### Red coding actions

Blocked unless explicitly approved with strong safeguards:

- publishing scientific claims automatically
- exposing API keys
- committing secrets
- destructive file operations
- uncontrolled background scraping
- production deployment changes
- running expensive compute without budget/approval

## Scientific claim boundaries

Allowed wording:

```text
screening candidate
predicted candidate
no match found in checked sources
requires DFT/experimental validation
research-support artifact
```

Forbidden without validation:

```text
proven new material
confirmed stable compound
guaranteed synthesizable
final bandgap
scientific proof
```

## Scatti/CaSc2TiO6 workflow lane

The Scatti workflow should be treated as a governed materials research lane.

Suggested pipeline:

```text
candidate formula
  ↓
formula normalization
  ↓
charge/oxidation sanity check
  ↓
public database/literature search
  ↓
variant search
  ↓
source/evidence table
  ↓
structure hypothesis generation
  ↓
DFT/CSP preparation
  ↓
operator-reviewed screening report
  ↓
optional external expert / experimental validation
```

## Installation guidance requirement

WESLR should eventually provide setup guides for materials workflows, but must not imply every tool is always available.

Good install docs should include:

- supported OS/environment
- Python version
- dependency list
- optional tools
- external binary requirements
- expected runtime cost
- GPU/CPU requirements when relevant
- API key setup
- verification command
- uninstall/cleanup notes

## Script generation requirements

Any generated script should include:

- purpose header
- required environment variables
- no secret printing
- read-only default mode
- timeout/rate-limit handling where relevant
- output path declaration
- reproducibility metadata
- error handling
- confidence/limitation labels

## Testing requirements

Materials workflow scripts should be tested with:

- known formula examples
- invalid formula examples
- no-key mode
- mocked API responses
- timeout/error behavior
- no secret leakage checks
- output schema checks

## Context/token efficiency benchmark link

Materials workflows are a good candidate for testing WESLR's context efficiency theory.

Baseline:

- agent repeatedly receives raw Scatti history, database notes, formula variants, and manual operator reminders

WESLR-assisted:

- agent receives compact WESLR materials context packet with candidate formula, checked sources, evidence table, known limitations, next tasks, and governance rules

Measure:

- input tokens
- repeated explanations
- missed constraints
- task success
- quality of generated scripts/report

## V1 decisions

```text
1. The Materials Project key may remain for research/staging Scatti work while data is gathered.
2. The key must not be deployed into public production by default.
3. Production deployments should remove/disable research keys unless explicitly configured.
4. WESLR should maintain a materials research map of sources, tools, installs, scripts, and validation steps.
5. WESLR may generate code/scripts for materials workflows, but code generation, execution, API calls, memory writes, and publication are separate risk levels.
6. Scientific outputs must remain screening/research-support artifacts until validated.
7. Materials workflows are a strong benchmark for WESLR context/token efficiency testing.
```

## V1 verdict

```text
WESLR_MATERIALS_RESEARCH_WORKFLOW_V1_DEFINED
```
