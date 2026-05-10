# WESLR Intelligence Enrichment Doctrine V1

**Status:** CANONICAL doctrine document  
**Date:** 2026-05-10  
**Scope:** Intelligence enrichment policy for graph, knowledge, evidence, capability, and reasoning substrates  
**Implementation status:** Documentation and tests only. No runtime behavior changes.

## 1. Purpose

WESLR enrichment means improving existing knowledge, graph, skill, evidence, and reasoning structures rather than adding isolated response patches.

This doctrine exists to stop handler sprawl. WESLR should become more capable by enriching its existing substrates, tightening evidence, extending routing/capability structure, and improving graph-connected reasoning. It should not grow by accumulating one-off response patches.

Doctrine first: before any new intelligence layer, WESLR must inspect what already exists, identify the real substrate gap, and prefer extension over parallel architecture.

## 2. Existing substrate

The current audit shows that WESLR already has multiple enrichment-capable substrates.

### Meaning / linguistic meaning

Existing meaning and obligation surfaces already exist:

- `weslr/linguistic_meaning.py` provides a weighted linguistic meaning vector with speech-act, relational, state-query, and safety dimensions.
- `weslr/response_obligation.py` maps meaning into bounded response obligations rather than free-form handler growth.
- `weslr/meaning_state_context.py` gathers minimal required state and already integrates identity, relationship depth, memory scope, continuity, self-model, and capability summaries.

These files show that WESLR already has a legible meaning substrate that can be enriched before inventing new response-specific layers.

### Evidence pipeline

Existing evidence surfaces already exist:

- `weslr/evidence_pipeline.py` is a read-only evidence orchestration path.
- `weslr/adapters/local_evidence_adapter.py` provides bounded local evidence access.
- `weslr/concept_graph/models.py` defines evidence-bearing graph primitives.
- `weslr/concept_graph/bridge/evidence.py` attaches traceable evidence to concepts and links.

This means WESLR already has evidence structures, provenance categories, confidence fields, and traceability surfaces that should be extended before adding separate evidence abstractions.

### Capability registry/router

Existing capability structures already exist:

- `weslr/capability_registry.py` is a read-only capability map.
- `weslr/capability_router.py` performs deterministic routing into capability IDs.
- Capability classification already separates registry, routing, and execution boundaries.

This gives WESLR a natural place to enrich skill categories, capability families, routing triggers, and evidence/capability alignment without adding ad hoc request handlers.

### Internal reasoning / proposal graph

An internal reasoning graph is present:

- `weslr/internal_reasoning_graph/models.py`
- `weslr/internal_reasoning_graph/reasoning_engine.py`
- `weslr/internal_reasoning_graph/proposal_workflow.py`

This substrate already models nodes, edges, proposal candidates, governance-safe reasoning results, validation, workflow state, and operator review boundaries. It is already suitable for representing gaps, proposals, conflicts, dependencies, and refinement structure.

### Entity / memory graphs

Existing memory and entity substrates already exist:

- `weslr/entity_memory.py` defines entity-scoped memory namespaces, relationships, scopes, and access levels.
- `weslr/entity_timeline_memory.py` provides per-entity timelines.
- `weslr/concept_graph/models.py` defines typed concepts, links, and evidence.
- `weslr/concept_graph/bridge/entity_graph.py` explicitly bridges existing entity graph data into concept graph structures instead of replacing them.

This is strong evidence that WESLR should prefer extending node types, edge types, memory scopes, and annotations rather than creating a parallel memory-intelligence graph by default.

### Materials graph / data if present

Materials-research doctrine and workflow surfaces are present:

- `docs/WESLR_MATERIALS_RESEARCH_WORKFLOW_V1.md`
- `weslr/combinatorial_materials.py` and adjacent materials-oriented modules discovered in audit

The current repo shows a materials lane and research workflow substrate, but the audit does not yet prove that it requires a standalone graph separate from concept, entity, evidence, and internal reasoning graphs.

### Eval and scorecard infrastructure

Existing eval and benchmark-adjacent surfaces already exist:

- `weslr/tests/test_random_ordinary_intelligence_prep_v1.py`
- `weslr/tests/test_ordinary_reasoning_guidance_v1.py`
- `weslr/tests/test_governance_benchmark_integration.py`
- release gate and repository validation scripts invoked by current workflow

WESLR already has evaluation surfaces, test surfaces, and benchmark-adjacent governance integration. Enrichment should connect to these existing validation surfaces before creating new benchmark-facing adapters.

### Cognitive legibility doctrine

The active canonical doctrine already establishes the Cognitive Legibility Boundary in `docs/WESLR_CANONICAL_SELF_MODEL_V1.md`.

That canon already states that internal abstractions may grow, but they must remain translatable, inspectable, teachable, and non-governing unless legible to the operator. This enrichment doctrine inherits that boundary directly.

## 3. Enrichment before expansion

Before adding a new intelligence layer, WESLR must ask:

- Can this be represented in an existing graph?
- Can this extend an existing skill/category map?
- Can this improve an existing evidence or capability route?
- Can this be measured by an existing eval?
- Can this remain legible to humans?

Existing graph/substrate must be audited before adding new graph systems.

If the answer is yes for an existing substrate, enrichment must happen there first. Expansion is justified only after the audit shows a genuine representation failure.

## 4. Graph extension principle

New graphs are allowed only when existing structures cannot represent the relation.

Prefer:

- extend node types
- extend edge types
- extend annotations
- extend scoring/evidence fields
- extend capability categories
- extend proposal/refinement links

Over:

- creating isolated new graph files
- adding standalone handlers
- adding unconnected doctrine
- creating parallel architecture when existing structures already fit

Do not create a parallel graph unless the audit proves existing graphs are insufficient.

## 5. Required enrichment dimensions

Each enrichment should state:

- domain knowledge added
- cognitive skill added
- evidence requirement
- routing/capability impact
- eval impact
- human-legibility explanation
- rollback/reversibility

No enrichment proposal is complete without all seven dimensions. This keeps enrichment inspectable, testable, and reversible.

## 6. Cognitive legibility boundary

Cognitive Legibility Boundary applies here without exception.

- internal abstractions may grow
- they must remain translatable, inspectable, teachable, auditable
- no private authority
- no unteachable internal graph/language

WESLR may use richer internal graph structure, internal tags, refinement markers, capability clusters, or reasoning annotations. But none of these may become hidden governing authority. Human operators must be able to inspect what was added, what relation it represents, why it exists, and how it affects reasoning.

If an enrichment cannot be translated into operator-legible explanation, it cannot govern runtime claims, self-change, memory writes, evaluation claims, or scientific claims.

## 7. Benchmark readiness connection

Official external tests will eventually require WESLR to represent several benchmark-relevant structures in legible form:

- knowledge domain graph
- cognitive skill graph
- benchmark task graph
- evidence calibration graph
- failure refinement graph
- legibility translation graph

This doctrine does **not** assume those must all become new standalone modules.

Instead, doctrine requires an audit decision for each one:

- Does the concept graph already cover it?
- Does the internal reasoning graph already cover it?
- Does entity/memory structure already cover part of it?
- Does the capability registry/router already cover skill/task mapping?
- Does the evidence substrate already cover calibration/provenance fields?

Only the remainder, if any, may justify a new formal graph module.

This doctrine makes no benchmark-passage claim, no superintelligence claim, and no leaderboard-performance claim.

## 8. Enrichment loop

Canonical enrichment loop:

**eval → gap graph → existing-substrate audit → enrichment proposal → tests → implementation → re-eval → doctrine update if needed**

Interpretation:

1. Run evals or inspect failures.
2. Express the failure as a gap graph or gap structure.
3. Audit existing substrate before writing new architecture.
4. Propose enrichment against the best-fit existing substrate.
5. Add tests first or alongside doctrine/doc changes.
6. Implement only after doctrine and tests are clear.
7. Re-evaluate the affected surface.
8. Update doctrine only when a new recurring rule is actually learned.

## 9. Anti-patterns

The following are forbidden anti-patterns:

- one handler per prompt
- benchmark gaming
- hidden self-modification
- unconnected graphs
- unverifiable private abstractions
- adding knowledge without evals
- adding evals without failure analysis
- creating parallel architecture when existing structures can be extended

These anti-patterns are forbidden because they reduce legibility, weaken auditability, and make WESLR appear smarter by fragmentation instead of by structured enrichment.

## 10. Next recommended step

Do not implement benchmark adapters yet.

Next step:

- map existing graph substrates into an enrichment target map
- decide which existing graph should receive:
  - ordinary explanation skills
  - ordinary reasoning skills
  - benchmark task types
  - failure/refinement records

Recommendation from current audit:

- ordinary explanation skills should likely enrich capability taxonomy and meaning/obligation-linked capability routing
- ordinary reasoning skills should likely enrich capability taxonomy plus internal reasoning graph refinement/proposal structure
- benchmark task types should likely first map onto capability categories and internal reasoning graph task/gap structures
- failure/refinement records should likely extend internal reasoning graph and evidence-bearing evaluation records before any new graph is introduced

## Canonical decision

WESLR enrichment prefers extending existing graphs.

New graph systems are a last resort, not a first reflex. Existing graph/substrate must be audited before adding new graph systems, and new graphs are allowed only when existing structures cannot represent the relation.
