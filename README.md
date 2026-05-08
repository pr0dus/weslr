# WESLR — Continuity-First Entity Intelligence Platform

WESLR is a continuity-first intelligence platform for structured reasoning over people, projects, entities, evidence, memory, proposals, and domain-specific workflows.

This repository is the main WESLR development repository. It is no longer only a Siemens/TIA plugin repository. The Siemens/TIA work remains important, but it is now one product track inside the broader WESLR platform.

## Current product identity

WESLR is being developed as a governed intelligence system with these core principles:

- continuity over isolated chat turns
- structured state over prompt-only memory
- deterministic authority layers with model assistance where useful
- explicit governance for system-changing actions
- safe, inspectable memory and relationship modeling
- domain expansion through bounded modules and evidence-backed workflows

WESLR should not be treated as a normal chatbot or an uncontrolled autonomous agent. The intended direction is a high-trust reasoning platform that can remember, compare, inspect, propose, and help operate across long-running work.

## Current state map

### 1. Core WESLR runtime

The core runtime contains the main reasoning, memory, identity, relationship, proposal, and consolidation layers.

Key areas include:

- meaning-vector response path
- channel identity binding
- entity-scoped memory namespaces
- relationship depth and relationship observation capture
- safe memory capture
- cognitive weight guardrails
- consolidation loop and promotion governance
- interpretation, dialogue, continuity, semantic memory, research, and integration modules

Primary documentation:

- `weslr/README.md`
- `ARCHITECTURE.md`
- `weslr/docs/WESLR_DOCTRINE_REGISTRY_V1.md`

### 2. WESLR Public Surface

The public surface is the user-facing and website-facing layer of WESLR.

Current repo areas include:

- `front-door/`
- `weslr-ui/`
- `dashboard/satellite/`
- `weslr-test-deployment/`

This area is intended to become the canonical public face of WESLR, including website, demo surfaces, operator-friendly views, and future product presentation.

### 3. Industrial / Siemens TIA track

The Siemens/TIA work is the industrial MVP track. It focuses on extracting engineering data from Siemens TIA Portal projects and mapping it into WESLR-compatible entity structures.

Canonical documentation:

- `docs/tia-bridge/README.md`
- `normalizer/siemens_to_weslr/README.md`
- `schemas/`
- `examples/`

This track is important commercially, but it is not the whole WESLR product.

### 4. Frontier science / Scatti track

WESLR also contains frontier science and materials-discovery tooling, including the unified matter generator and novelty-checking workflows.

Relevant areas include:

- `weslr/modules/unified_matter_generator.py`
- `weslr/docs/WESLR_PHASE_8.5_UNIFIED_MATTER_GENERATOR_DOCTRINE.md`
- `weslr/docs/unified matter generator.md`
- frontier proposal and novelty-checking commands documented in `weslr/README.md`

This track includes candidate-generation workflows such as the CaSc2TiO6 / "Scatti" materials-discovery line. These outputs are screening candidates for validation, not final scientific proof.

### 5. Deployment / runtime forge

Deployment and runtime work covers staging, test deployments, self-hosted or local environments, and future Ubuntu/OCW deployment paths.

Relevant areas include:

- `weslr-test-deployment/`
- `dashboard/`
- service/deployment documentation where present
- future GitHub Actions or self-hosted runner workflows

## Install and test status

This repository now has a root `pyproject.toml` packaging baseline for editable installs and smoke validation.

Current baseline install:

```bash
pip install -e .[test]
```

Current minimal validation:

```bash
python -m compileall -q weslr
python - <<'PY'
import weslr
print("WESLR import smoke OK")
PY
```

The first GitHub CI workflow is intentionally conservative. It verifies installability, compilation, and package import. Full test execution is deferred until dependency requirements, local state requirements, and integration/runtime assumptions are audited.

Some tests and modules may require a specific local environment, optional dependencies, API keys, or local state. Future repo hardening should add:

- audited runtime dependencies
- dependency groups / test extras beyond the current minimal pytest extra
- separate unit, integration, local runtime, Scatti/materials, and deployment test lanes
- explicit GitHub Actions workflows for each lane

## Repository maturity warning

WESLR contains many implemented internal layers, but not every layer is productized or exposed through a polished UI. The repo currently mixes:

- core runtime code
- experimental reasoning modules
- industrial MVP assets
- public surface prototypes
- scientific discovery workflows
- docs, doctrine, and historical memory artifacts

For development, prefer small, bounded, reversible changes with explicit tests and clear scope.

## Development rule of thumb

Before changing behavior:

1. Identify the affected layer.
2. Check whether the layer is governed, memory-related, identity-related, public-facing, or deployment-related.
3. Prefer additive changes.
4. Preserve auditability and rollback paths.
5. Do not silently change identity, memory, governance, or public behavior.

## Historical note

Earlier versions of this README described the repository as a TIA Portal V20 plugin. That is now treated as historical and has been moved into the industrial/TIA product track documentation.
