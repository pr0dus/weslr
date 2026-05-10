# WESLR Enrichment Target Map V1

**Status:** Planning/doctrine document  
**Date:** 2026-05-10  
**Scope:** Map intelligence-growth needs onto existing WESLR substrates  
**Implementation status:** Documentation and tests only. No runtime behavior changes.

## 1. Purpose

The target map connects intelligence gaps to existing WESLR substrates.

Its job is to make future growth legible and non-fragmented. Instead of adding isolated handlers or inventing new graph systems too early, WESLR should first decide which existing substrate is responsible for carrying a new capability, failure pattern, evaluation signal, or knowledge expansion.

This map operationalizes WESLR Intelligence Enrichment Doctrine V1.

## 2. Existing substrates and intended responsibility

### Concept graph

Primary responsibility:

- structured concept/entity representation
- typed links between concepts
- attached evidence on nodes and links
- cross-domain knowledge structure
- extensible semantic relation storage

Use first when WESLR needs legible knowledge structure, domain linkage, or evidence-bearing concept relations.

### Internal reasoning graph

Primary responsibility:

- reasoning gaps
- proposal candidates
- workflow state
- refinement/failure structure
- governance-safe reasoning traces
- task/gap/impact representation

Use first when WESLR needs to represent reasoning bottlenecks, task decomposition, refinement loops, gap structure, operator-reviewed proposals, or hypothesis-like internal task states.

### Evidence substrate

Primary responsibility:

- provenance
- confidence and calibration hooks
- traceable evidence packets
- source-backed vs inferred distinctions
- evidence attachment and review

Use first when WESLR needs calibration, uncertainty records, source traceability, evidence aggregation, or verification surfaces.

### Capability registry/router

Primary responsibility:

- capability taxonomy
- request-family classification
- deterministic routing categories
- capability labels, triggers, and boundaries

Use first when WESLR needs to add or refine skill families, benchmark task families, route categories, or explicit capability coverage maps.

### Meaning / response-obligation substrate

Primary responsibility:

- linguistic meaning interpretation
- relational and safety framing
- response obligation determination
- bounded state needs
- human-facing interaction structure

Use first when WESLR needs richer conversational intelligence, ordinary explanation/reasoning framing, psychology-aware interaction boundaries, or conversation-shape distinctions that still remain human-legible.

### Entity / memory graph

Primary responsibility:

- entity-scoped memory
- timeline continuity
- role and relationship context
- person/project/institution context separation
- bounded longitudinal human/institution knowledge

Use first when WESLR needs durable human/institution/project context rather than free-floating task semantics.

### Eval / scorecard substrate

Primary responsibility:

- gap detection
- comparative coverage checks
- scorecards
- failure observation
- regression protection
- readiness tracking

Use first when WESLR needs measurable evidence that an enrichment helped, failed, regressed, or still lacks coverage.

### Cognitive legibility doctrine

Primary responsibility:

- upper-bound governance rule for all enrichment
- translation requirement for internal abstractions
- operator inspectability and teachability requirement
- ban on private authority

This is not a graph substrate, but it governs all of them. Every enrichment path must remain compatible with the Cognitive Legibility Boundary.

## 3. Enrichment target matrix

| Need / capability | Existing substrate to extend | Why this substrate | Required enrichment | Evidence/eval check | Legibility requirement | New graph needed? yes/no |
|---|---|---|---|---|---|---|
| ordinary explanation skills | capability registry/router + meaning/response-obligation + eval/scorecard | explanation is partly routing/taxonomy, partly interaction framing, and must be measured | expand explanation skill taxonomy, obligation categories, explanation-quality eval coverage | explanation tests, conversation evals, scorecard deltas | explainable categories and teachable explanation patterns | no |
| ordinary reasoning skills | capability registry/router + meaning/response-obligation + internal reasoning graph + eval/scorecard | ordinary reasoning spans capability type, interaction framing, and gap/refinement tracking | enrich reasoning categories, obligation hooks, reasoning-gap records, eval coverage | ordinary reasoning tests, gap/failure review, scorecard trends | reasoning path must remain human-auditable | no |
| psychology / human context | meaning/response-obligation + entity/memory graph | human context needs safe relational interpretation plus bounded memory context | richer human-context dimensions, safety boundaries, relationship-aware context retrieval | interaction evals, safety review, bounded-memory checks | no private inference authority; explain what context was used | no |
| creativity / conversation | meaning/response-obligation + eval/scorecard | conversational creativity is first an interaction-quality issue, not a new graph | enrich conversational modes, resilience markers, creative-response eval coverage | conversation evals, repetition/fallback tracking | style changes must still be teachable and bounded | no |
| materials/scientific reasoning | concept graph + evidence substrate + internal reasoning graph | science needs evidence-backed concepts plus reasoning/refinement structure | domain concepts, scientific relation types, evidence calibration, hypothesis/refinement traces | materials evals, claim-boundary tests, evidence trace checks | scientific claims must remain source-traceable | no |
| unknown file understanding | capability registry/router + evidence substrate + internal reasoning graph | this is task routing plus evidence extraction plus reasoning about unknown structure | file-understanding capability families, evidence extraction patterns, gap/task records | file interpretation tests, failure analysis, scorecards | must explain what was read and what remains uncertain | no |
| MMLU/GPQA-style multiple choice tasks | capability registry/router + internal reasoning graph + eval/scorecard | benchmark task forms are task taxonomy plus reasoning/error tracking | add multiple-choice task taxonomy, choice-reasoning gap records, benchmark-facing eval labels | benchmark-style evals, calibration checks, wrong-answer analysis | choice rationale must be inspectable | no |
| HELM-style multi-metric evaluation | eval/scorecard + evidence substrate | multi-metric evaluation is primarily measurement and evidence accounting | add metric families, calibration summaries, failure slices, score aggregation doctrine | scorecards, metric consistency checks, calibration reports | metric definitions must be transparent and teachable | no |
| SWE-bench/OCC coding task workflow | capability registry/router + internal reasoning graph + eval/scorecard | coding tasks need explicit task taxonomy, workflow/gap records, and measurable outcome tracking | add coding-task types, workflow/gap states, failure/refinement records, scorecard coverage | coding workflow tests, release gates, regression tracking | task states and failure reasons must stay operator-readable | no |
| ARC-AGI-style abstract task reasoning | internal reasoning graph first + eval/scorecard | abstraction tasks may need hypothesis/task-state representation, but first test existing reasoning graph | encode task-state, hypothesis, transformation, and abstraction-gap records | abstract-task evals, failure clustering, reasoning-path review | abstractions must remain translatable into human task descriptions | no, unless proof of representation failure |
| failure/refinement records | internal reasoning graph + eval/scorecard + evidence substrate | failures are reasoning/refinement objects with evidence and measurable recurrence | add refinement-linked failure nodes/edges or equivalent records, evidence links, recurrence summaries | failure-analysis tests, regression trend checks | failure chain must be inspectable | no |
| calibration/uncertainty tracking | evidence substrate + eval/scorecard | calibration belongs with confidence, provenance, and outcome checking | add uncertainty fields, calibration summaries, evidence-confidence comparisons | calibration evals, confidence-vs-outcome review | uncertainty must be explicitly reportable | no |
| legibility translation records | doctrine/eval first, then internal reasoning graph if needed | first prove the need through doctrine and eval, not architecture inflation | define translation checks, teachability checks, audit examples | cognitive legibility tests, translation review | must directly satisfy Cognitive Legibility Boundary | no initially |
| domain knowledge expansion | concept graph + evidence substrate + capability taxonomy | knowledge growth should connect concepts, evidence, and capability coverage | extend domain concepts, relation types, evidence categories, capability/domain maps | domain evals, provenance checks, coverage tracking | domain additions must be human-readable and source-linked | no |

## 4. Recommended substrate decisions

### Ordinary explanation/reasoning skills

Extend capability taxonomy + meaning/obligation + eval records first.

Explanation and ordinary reasoning are not separate mini-systems. They are coverage categories that should be visible in routing, interaction framing, and evaluation before any deeper graph formalization is attempted.

### Psychology/human context

Extend meaning/obligation + entity/memory context, with safety boundaries.

Human context should remain bounded, explicit, and inspectable. It should not become hidden psychological profiling.

### Creativity/conversation

Extend meaning/obligation + conversation resilience/eval substrate.

Creativity should be measured as conversational adequacy, flexibility, and non-repetitiveness before any new structural graph is proposed.

### Benchmark task types

Extend capability taxonomy + internal reasoning graph task/gap records.

Task types belong first in explicit capability/task families and reasoning-gap structures, not in a premature benchmark-only graph module.

### Failure/refinement

Extend internal reasoning graph + evidence/eval records.

Failure and refinement should be attached to reasoning structure and validated by evidence and scorecards.

### Evidence calibration

Extend evidence substrate and eval scorecards.

Calibration is first a provenance/confidence discipline, then an evaluation discipline.

### Legibility translation

Extend doctrine/eval first; formal graph only if needed later.

If translation failures recur and cannot be represented cleanly in evals or reasoning records, only then consider a dedicated formal structure.

### ARC-style abstraction

Likely needs a task-state/hypothesis representation, but first test whether internal reasoning graph can represent it.

No new graph is justified until the internal reasoning graph demonstrably fails to encode the needed abstraction states or transformations.

## 5. New graph decision table

| Proposed graph | Decision now | Extend existing substrate first | Formalize as new graph only if needed | Proof that would justify new graph |
|---|---|---|---|---|
| knowledge domain graph | defer standalone graph | concept graph + evidence substrate | yes | repeated domain-relation needs cannot be expressed cleanly through concept/link/evidence extensions |
| cognitive skill graph | defer standalone graph | capability registry/router + eval/scorecard + internal reasoning graph | yes | skill interactions, dependencies, and failure links become too awkward or lossy in existing taxonomy/graph forms |
| benchmark task graph | defer standalone graph | capability taxonomy + internal reasoning graph task/gap records | yes | benchmark task/state structure requires relations not representable in current task/gap/proposal forms |
| evidence calibration graph | defer standalone graph | evidence substrate + eval/scorecard | yes | calibration dependencies require persistent relational structure beyond evidence packets, confidence fields, and scorecards |
| failure refinement graph | defer standalone graph | internal reasoning graph + eval/scorecard + evidence links | yes | refinement cycles and failure causality cannot be represented legibly in existing reasoning/failure structures |
| legibility translation graph | defer standalone graph | doctrine + eval + internal reasoning graph if necessary | yes | repeated translation/audit objects require stable structured relations that doctrine/tests alone cannot carry |

New graphs require proof and justification. The default policy is: extend existing substrate first.

## 6. Next implementation recommendation

Do not jump to official benchmark datasets yet.

Recommended next:

- add enrichment records / gap records into existing internal reasoning graph or eval substrate
- create a benchmark-task taxonomy adapter as data/doctrine first, not full runner

That next step preserves doctrine-first sequencing and avoids premature benchmark theater.

## 7. Anti-pattern reminders

- no one handler per prompt
- no benchmark gaming
- no hidden self-modification
- no unconnected graphs
- no unteachable private abstractions

All future enrichment work remains bound by the Cognitive Legibility Boundary.

## Canonical reading of this map

This map says WESLR should grow by enriching existing substrates, measuring the result, and only escalating to a new graph when there is concrete proof that current structures cannot represent the needed relation without losing legibility, auditability, or teachability.

This document makes no benchmark-passage claim, no superintelligence claim, and no leaderboard-performance claim.