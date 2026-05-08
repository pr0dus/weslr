# WESLR Industrial Track — Siemens TIA Bridge

The Siemens TIA Bridge is the industrial automation product track of WESLR.

It is not the whole WESLR product and should not be used as the root identity of the main repository. It is a domain-specific bridge for extracting and normalizing Siemens TIA Portal engineering data into WESLR-compatible entity structures.

## Purpose

The TIA Bridge extracts engineering data from Siemens TIA Portal V20 projects on Windows and prepares it for later ingestion into the WESLR entity intelligence system.

The intended workflow is:

```text
TIA Portal V20 project
  -> read-only collector / export
  -> raw JSON envelope
  -> normalized graph JSON
  -> WESLR entity graph / industrial reasoning layer
```

## What it should do

1. Read TIA Portal V20 project data in a read-only/offline manner.
2. Extract engineering objects such as PLCs, CPUs, devices, tags, alarms, topology, and network configuration.
3. Export raw engineering data to a stable JSON envelope.
4. Normalize raw exports into a WESLR-compatible graph format.
5. Preserve provenance from source project to normalized entities.
6. Avoid changing or executing anything inside the original TIA project.

## Non-goals and safety boundaries

The TIA Bridge must not:

- modify the original TIA Portal project
- communicate with live PLC/SPS/IO systems
- execute or change control logic
- upload customer engineering data to external servers by default
- bypass operator approval for customer data handling

The bridge is an engineering-data extraction and normalization pathway, not a live-control system.

## Current repository state

The main WESLR repository contains industrial/TIA-related schemas, examples, normalizer direction, and documentation.

Relevant areas may include:

```text
schemas/
examples/
normalizer/siemens_to_weslr/
docs/tia-bridge/
src/collector/
plugins/
```

The actual Windows/TIA Openness collector may live in a separate private repository or may be integrated later through a bounded plugin interface. Treat this track as partially implemented until the collector, normalizer, tests, and import path are verified end-to-end.

## Current expected artifacts

### Raw export

A read-only JSON export representing the source TIA project and its engineering objects.

Expected content categories:

- project metadata
- PLC/CPU information
- devices and modules
- tags
- alarms
- network/topology data
- collector diagnostics

### Normalized graph

A WESLR-compatible graph representation generated from the raw export.

Expected content categories:

- entities
- relationships
- source references
- schema version
- normalization diagnostics

## Relation to WESLR core

The TIA Bridge should feed WESLR with structured industrial engineering context. WESLR core should then be able to reason over:

- machines and automation systems
- PLC/CPU/device topology
- tag relationships
- alarms and operational semantics
- engineering changes over time
- project-level industrial memory

This makes the TIA Bridge a commercial/industrial wedge under the larger WESLR platform.

## Product status

Current status: **industrial track / partial implementation**.

Polish still needed:

- verify actual collector implementation status
- verify normalizer implementation status
- verify schema compatibility with current WESLR entity memory / graph layers
- add repeatable test fixture exports
- add end-to-end import test
- document installation and Windows/TIA Openness requirements
- separate public-safe marketing language from private customer implementation details

## Private repository note

Historical notes referenced a private repository:

```text
pr0dus/weslr-tia-openness-bridge
```

That repository may contain or later contain Windows-specific collector work. The main WESLR repo should reference it only as an implementation detail or commercial module, not as the identity of WESLR itself.

## Commercial positioning

The TIA Bridge is a possible first commercial wedge for WESLR in industrial automation.

Possible users:

- Siemens/TIA integrators
- PLC programmers
- machine builders
- factories and maintenance teams
- industrial engineering teams

Possible value:

- structured project memory
- engineering change understanding
- faster project review
- safer handoff between engineers
- future industrial reasoning and diagnostics

## License and data handling

Customer project exports may contain sensitive industrial information. Any commercial version must define:

- local-only processing guarantees where applicable
- customer data retention rules
- export deletion and audit policy
- license boundary between WESLR core and premium industrial modules

---

This document is the canonical home for the Siemens/TIA industrial bridge track inside the main WESLR repository.
