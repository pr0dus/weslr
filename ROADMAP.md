# CircleForge Roadmap

This file captures the planned path from the current prototype into a more complete local agent research sandbox and artifact-incubation system.

## Project direction

CircleForge is evolving toward:

> A persistent local agent research sandbox that turns recurring agent work into inspectable artifacts, then helps humans review, rank, and curate the promising ones into reusable packs.

## Current foundation

Already implemented:
- persistent agents
- timed ticks
- local model integration
- inspect / trade
- artifact metadata
- dual scoring
- demand board
- export queue
- review queue
- export-ready flow
- category governance
- artifact packs
- uncategorized handling
- dormant-category signals

## Phase 1 — Structural maturity

### v0.0.29
- artifact lineage graph fields
- artifact lifecycle states
- category lifecycle states
- quality dimensions

### v0.0.30
- manual category governance controls
- approve / reject / retire / revive / merge category actions
- category metadata and lifecycle handling

## Phase 2 — Market and idea intelligence

### v0.0.31
- market evolution engine
- category demand trends
- saturation / decline / rise detection

### v0.0.32
- uncategorized clustering
- emergent clusters
- cluster-driven category proposals

## Phase 3 — Practical artifact families

### v0.0.33
- local-ai-ops family
- observability family
- status-page family
- dashboard family
- packaging family
- evaluation family

### v0.0.34
- richer export folders
- README / manifest / notes per export
- pack-level export bundles

## Phase 4 — Human curation and pack incubation

### v0.0.35
- failure-driven demand signals
- recent errors, skips, and cooldowns influence the demand board
- friction becomes part of artifact demand discovery

### v0.0.36
- pack quality scoring
- release-candidate packs
- top-pack ranking
- pack-level demand signals for human curation

## Phase 5 — Commercial qualification and artifact shaping

### v0.0.37
- artifact-level commercial qualification
- sellability scoring
- target-user and price-band guesses
- pack-level commercial readiness signals

### v0.0.38
- queue and pack browsing ergonomics
- ranking explanations and curation reasons
- better operator views for promising artifacts

### v0.0.39
- better export bundles
- publishable pack wrappers
- project handoff formats for curated outputs

### v0.0.40
- category-specific publishing templates
- delivery-mode recommendations
- stronger buyer/problem/install framing in wrappers and handoffs

## Quality model target

### Internal artifact quality
- reusability
- composability
- clarity
- maintainability
- stability

### External artifact quality
- installability
- exportability
- usefulness
- readability
- extension potential

### Market quality
- timing
- differentiation
- category demand
- pack fit
- future need alignment

## Lifecycle targets

### Artifact lifecycle
- idea
- prototype
- internal_use
- tradable
- review_proposed
- approved
- export_ready
- packed
- release_candidate
- archived
- retired

### Category lifecycle
- active
- dormant
- reviving
- archived
- merged

### Pack lifecycle
- draft
- coherent
- reviewed
- release_candidate
- published
- retired

## Practical artifact families to encourage
- local-ai-ops
- observability
- status-pages
- dashboards
- packaging
- evaluation
- benchmarks
- replay / debugging
- memory tools
- export wrappers

## Grouped upload plan

### Upload Group A
- v0.0.29
- v0.0.30

Focus:
- structure
- lifecycle
- quality dimensions
- manual category governance

### Upload Group B
- v0.0.31
- v0.0.32

Focus:
- market evolution
- emergent clusters
- category formation pressure

### Upload Group C
- v0.0.33
- v0.0.34

Focus:
- practical artifact families
- richer exports
- pack exports

### Upload Group D
- v0.0.35
- v0.0.36

Focus:
- friction-aware demand
- pack quality
- release-candidate logic
- ranked curation targets

### Upload Group E
- v0.0.37
- v0.0.39

Focus:
- commercial qualification
- human review ergonomics
- artifact shaping
- curated output packaging
