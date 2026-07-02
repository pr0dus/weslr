# WESLR ARC-AGI-1/ARC-AGI-2 Source-Grounded Architecture Discovery Packet (V1)

**Repository**: `/data/data/com.termux/files/home/weslr-pr47-clean`
**Branch**: `occ-discovery-doctrine-implementation-20260613`
**Lane**: `DESIGN_ARC_AGI_1_2_SOURCE_GROUNDED_ARCHITECTURE_DISCOVERY_PACKET_V1`
**Start HEAD**: `da4becee9c36df20a55c66f13579ec78bc0f2d33`
**actual preflight HEAD**: `da4becee9c36df20a55c66f13579ec78bc0f2d33`
**End HEAD**: pending commit
**Commit**: pending

## Purpose

Define how WESLR/OCC should learn the correct ARC-AGI-1 and ARC-AGI-2 architecture for this year from official/public documentation without guessing, without touching hidden/private data, and without importing/running official datasets yet.

This packet is a discovery and approval plan only. It does not infer official architecture from memory or from prior synthetic WESLR work.

## 1) Source classes

Treat these source classes separately:

- official ARC Prize competition pages
- official ARC Prize rules/policy pages
- official ARC-AGI-1 benchmark/documentation pages
- official ARC-AGI-2 benchmark/documentation pages
- official GitHub repositories
- Kaggle competition pages, if relevant
- papers/blogs as secondary explanatory sources only
- WESLR synthetic docs as internal architecture only, not source of official truth

Rules:

- official/public sources may inform the architecture map
- secondary explanatory sources may clarify, but not override official/public sources
- WESLR synthetic docs may describe internal implementation patterns only
- no synthetic doc may be treated as the official ARC truth source

## 2) Source approval protocol

Before OCC may use a source packet, the owner must approve at minimum:

- source URL or local document path
- source type
- source version/date observed
- checksum or captured snapshot hash if local
- whether the source is documentation only or dataset-bearing
- whether dataset files are forbidden to open in this lane

Discovery packet rule:

- documentation pages may be read only if approved
- dataset-bearing sources remain closed in this lane unless the owner separately authorizes them
- repository metadata may be inspected only when explicitly approved and only if task files stay unopened

## 3) No-data rule

This architecture discovery packet may inspect documentation/rules only.

It must not:

- open official task JSON files
- inspect public evaluation examples
- inspect hidden/private data
- download datasets
- run tasks
- score tasks
- extract answer examples
- copy official grids into WESLR docs
- mix official examples with synthetic WESLR examples

If a source packet includes dataset files, those files are out of scope unless the owner separately authorizes opening them for a different lane.

## 4) Architecture questions to answer from sources

### ARC-AGI-1 questions

- current role this year: baseline/archive/active competition/supporting benchmark?
- public dataset structure
- train/test JSON shape
- expected answer format
- candidate output requirements
- scoring rule
- local evaluation expectations
- source/provenance/checksum requirements

### ARC-AGI-2 questions

- active 2026 competition role
- public/private split
- train/evaluation/test structure
- task JSON format
- expected answer format
- exactly-two-output rule if applicable
- scoring rule
- Kaggle or official runtime/efficiency limits
- allowed/disallowed compute/network/model/tool behavior
- submission or local-run format
- claim boundaries

These questions are the required source-grounding checklist before any implementation report or adapter/scorer work begins.

## 5) Architecture map output

Future report file:

- `docs/WESLR_ARC_AGI_1_2_SOURCE_GROUNDED_ARCHITECTURE_MAP_V1.md`

It should contain:

- source inventory
- citation/provenance table
- ARC-AGI-1 architecture summary
- ARC-AGI-2 architecture summary
- shared architecture components
- differences between ARC-AGI-1 and ARC-AGI-2
- unknowns that need owner/source clarification
- implementation implications for WESLR
- explicit `no official data touched` statement
- explicit `official percentage remains none/0` statement

The map should be citation-first and should separate what is observed in sources from what is merely inferred for WESLR implementation planning.

## 6) Implementation implications to map later

The source-grounded architecture map should inform future WESLR files, including:

- public data adapter
- public scorer
- two-output emitter
- local run harness
- offline runner
- runtime logger
- contamination audit
- claim report
- ARC-AGI-1/ARC-AGI-2 separation layer

Implication rule:

- the architecture map may guide file design, but it may not authorize implementation by itself
- any implementation lane must preserve the no-data rule and source-approval constraints

## 7) Stop conditions

Stop the discovery packet if any of the following occurs:

- a source is unofficial but treated as official
- a source contains dataset files and owner did not approve opening
- hidden/private data is encountered
- official grid examples would be copied into docs
- checksum/provenance is missing for a local source packet
- architecture cannot be resolved from sources
- OCC would need to guess
- any web/network/dataset access is needed but not approved

If a stop condition occurs, the report should name the blocked source class and the missing approval rather than attempting to fill the gap from memory.

## 8) Owner information request

Before source collection begins, the owner should provide:

- approved official ARC Prize pages
- approved official GitHub repository links
- approved Kaggle page links if needed
- whether OCC may read documentation pages only
- whether OCC may inspect repository metadata but not task JSON files
- whether ARC-AGI-1 is in scope as baseline only or as a target local run
- whether ARC-AGI-2 is the primary target

## 9) Summary stance

- no official data touched
- official percentage remains none/0
- architecture is unresolved until grounded in approved sources
- this packet is a source-approval and question-framing plan, not a benchmark claim

## Receipt

- Start HEAD / End HEAD / Commit: `da4becee9c36df20a55c66f13579ec78bc0f2d33` / `da4becee9c36df20a55c66f13579ec78bc0f2d33` / `no`
- actual preflight HEAD: `da4becee9c36df20a55c66f13579ec78bc0f2d33`
- discovery packet created: yes
- source classes defined: yes
- source approval protocol defined: yes
- no-data rule defined: yes
- ARC-AGI-1 architecture questions defined: yes
- ARC-AGI-2 architecture questions defined: yes
- architecture map output defined: yes
- implementation implications defined: yes
- stop conditions defined: yes
- owner information request listed: yes
- official data untouched: yes
- official percentage claimable remains none/0: yes
- validation: pending
- unrelated dirty files left uncommitted: yes
- push avoided: yes
- recommended next lane: `Await owner direction`
