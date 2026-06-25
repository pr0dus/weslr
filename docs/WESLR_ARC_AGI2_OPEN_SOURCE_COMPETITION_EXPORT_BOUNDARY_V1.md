# WESLR ARC-AGI2 Open Source Competition Export Boundary V1

## Status
Design only. No export package created. No files moved. No Kaggle data downloaded. No ARC data ingested. No score claims.

## Purpose
Define what would belong in a future public, reproducible ARC-AGI-2 competition package, and what must stay private in WESLR.

## 1) Private WESLR core
Keep private unless separately approved. This private WESLR core includes private WESLR state and .weslr state.

- WESLR chat/runtime layers
- website/admin/deployment code
- owner workflows
- private memory/context systems
- OpenClaw/OCC/Nova operational infrastructure
- `.weslr` state
- private logs
- private business material
- personal data
- provider/model/payment integrations
- any non-competition internal orchestration

## 2) Future public competition package candidate
Potentially exportable later:

- ARC grid schema helpers
- ARC-AGI-2 challenge/solution/sample-submission parsers
- synthetic task-family generators
- primitive registry
- object extraction
- candidate rule/program generator
- top-2 attempt packet / ranker
- submission serializer
- offline execution validator
- no-leakage validators
- reproducibility scripts
- tests using synthetic fixtures only
- README / method description / license / reproducibility notes

## 3) Export criteria
A module is exportable only if it satisfies all of these:

- no private data
- no `.weslr` dependency
- no website/runtime dependency
- no provider/API/network dependency
- no private memory/context dependency
- no OpenClaw/Nova/OCC dependency
- no secrets/tokens
- no benchmark answer keys
- no hidden/private benchmark data
- no public score/certification claims
- deterministic/reproducible where possible
- compatible with offline Kaggle notebook execution

## 4) Non-exportable criteria
A module is not exportable if it requires any of these:

- private WESLR state
- raw private logs
- owner-specific context
- private runtime services
- payment/provider credentials
- website/chat infrastructure
- external API calls during evaluation
- hidden benchmark data
- solution leakage
- answer-key-derived logic

## 5) Proposed package shape
Future package candidate:

```text
weslr-arc-agi2-solver/
  solver/
  data_contract/
  synthetic_generators/
  submission/
  validation/
  tests/
  notebooks/
  README.md
  LICENSE
  REPRODUCIBILITY.md
```

### Package intent
- `solver/` — ARC-AGI-2 solver logic
- `data_contract/` — parsers, schema, manifest handling
- `synthetic_generators/` — public-safe synthetic task families
- `submission/` — top-2 attempt packets and JSON serialization
- `validation/` — offline/no-leakage/reproducibility checks
- `tests/` — synthetic-fixture-only tests
- `notebooks/` — offline Kaggle notebook examples later, if approved

## 6) Current module classification
| Current module | Classification | Why |
|---|---|---|
| `weslr/arc_style_grid_schema_helpers.py` | needs-refactor-before-export | Strongest schema candidate, but still synthetic-first and missing ARC-AGI-2 parsers / submission contract pieces. |
| `weslr/arc_style_grid_adapter_phase2.py` | needs-refactor-before-export | Useful registry/object-extraction substrate, but still internal-phase and not packaged for export. |
| `weslr/arc_style_grid_solver_dry_run.py` | needs-refactor-before-export | Bounded dry-run logic is export-relevant, but still embedded in WESLR internal phases. |
| `weslr/arc_style_grid_generalization_stress.py` | needs-refactor-before-export | Good synthetic stress harness, but still internal-only and tied to WESLR phase conventions. |

## 7) Required future refactors before any export
- remove private imports
- isolate ARC solver package
- ensure offline-only execution
- add license decision
- add reproducibility notes
- add data path policy
- add no-leakage validation
- add top-2 submission contract
- add synthetic fixtures only in public tests
- separate public package code from WESLR private runtime code
- remove any dependency on `.weslr`, private logs, or owner context

## 8) Current WESLR modules: export boundary view
### Export-candidate after refactor
- schema helpers / data-contract code
- synthetic task-family generators
- primitive registry / object extraction / candidate ranking logic
- no-leakage validators
- offline validators
- synthetic-fixture tests

### Internal-only
- chat/runtime layers
- website/admin/deployment code
- private memory/context systems
- OpenClaw/OCC/Nova operational infrastructure
- `.weslr` state
- private logs and owner workflows
- provider/model/payment integration code

### Not yet implemented
- ARC-AGI-2 challenge parser
- ARC-AGI-2 solution parser
- sample-submission parser
- top-2 attempt packet builder
- submission JSON serializer
- offline Kaggle notebook boundary validator

## 9) Next implementation recommendation
Choose **A** first:
- schema-only ARC-AGI-2 top-2 attempt / submission helpers using synthetic data only
- keep them inside the future export boundary, but do not export/package them yet

Then:
- expand synthetic task-family generators
- only later create the export-package skeleton

## 10) Final boundary summary
The future public competition package should be a small, reproducible, offline-safe ARC-AGI-2 solver bundle. WESLR’s private runtime, owner context, and operational infrastructure must stay out of it entirely.
