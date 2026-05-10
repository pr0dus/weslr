# WESLR Benchmark Reasoning Engine V1

**Status:** design only  
**Date:** 2026-05-10  
**Scope:** doctrine and architecture for a general benchmark reasoning engine for official-style intelligence tests  
**Implementation status:** documentation and tests only. No runtime behavior changes.

## 1. Purpose

WESLR must stop relying on isolated keyword scorers as the central route for benchmark-style reasoning.

The next architecture should be a general Benchmark Reasoning Engine that can accept official-style reasoning tasks, classify them, decompose them, select appropriate solver families, produce human-readable explanations, and convert failures into general enrichment records.

The purpose is reusable reasoning intelligence, not another local patch.

## 2. Why subject scorers are insufficient

Subject scorers are useful helper tools, but they are insufficient as the main intelligence layer.

Reasons:

- keyword scorers are brittle
- keyword scorers overfit easily
- keyword scorers miss hidden structure
- keyword scorers do not scale to MMLU, GPQA, or ARC-style breadth
- subject scorers should become helper tools, not the central intelligence layer

A scorer that looks only for local phrase patterns may appear to work on small synthetic tests while failing on real reasoning tasks whose structure is implicit rather than lexically obvious.

## 3. Core engine pipeline

### Input

The engine should accept:

- question
- choices
- domain
- required_skill
- provenance metadata

### Pipeline

A. task classification  
B. question decomposition  
C. constraint extraction  
D. answer-choice representation  
E. candidate reasoning paths  
F. solver/tool selection  
G. option scoring  
H. contradiction/evidence check  
I. confidence calibration  
J. human-readable explanation  
K. failure-to-enrichment record

The pipeline should remain legible, inspectable, and modular. Each stage should be explainable in human terms.

## 4. Solver families

The Benchmark Reasoning Engine should use pluggable solver families, not one-off handlers.

Initial solver families:

- formal logic solver
- ethics/tradeoff solver
- science mechanism solver
- semantic/language solver
- mathematical reasoning solver
- factual/evidence retrieval solver
- analogy/abstraction solver
- uncertainty/calibration solver

These are solver families, not isolated patches. The engine should decide when each family is appropriate.

## 5. Intermediate representation

The engine should use a common ReasoningTrace object with fields such as:

- task_type
- parsed_question
- constraints
- assumptions
- choice_representations
- reasoning_steps
- solver_outputs
- selected_answer
- confidence
- uncertainty
- explanation
- failure_modes
- provenance
- anti_gaming_flags

This intermediate representation should support both successful answer selection and failure analysis.

## 6. Cognitive Legibility Boundary

The Cognitive Legibility Boundary applies without exception.

Rules:

- every internal representation must be translatable
- no private symbolic authority
- no hidden benchmark tuning
- no answer-key memorization
- explanations must remain human-teachable

Internal symbolic structure is allowed only if it remains translatable, inspectable, teachable, and auditable.

## 7. Anti-benchmark-gaming boundary

The Benchmark Reasoning Engine must preserve strict anti-benchmark-gaming boundaries:

- no item IDs
- no answer-label learning
- no raw benchmark memorization
- no official-score claims
- no leaderboard inference
- no benchmark-specific shortcuts
- failures become general skill gaps only

The engine may learn from failure patterns only by enriching general reasoning capability, not by memorizing benchmark content.

## 8. Relationship to existing WESLR substrates

The Benchmark Reasoning Engine should extend existing WESLR substrates rather than replacing them.

Mapping:

- internal_reasoning_graph = reasoning traces, failures, proposals
- concept_graph = domain concepts and evidence
- capability_registry = task and skill taxonomy
- eval/scorecard = measurement only
- existing scorers = helper modules, not core intelligence
- MCQ adapter = input/output shell, not reasoning engine

This keeps the architecture aligned with WESLR Intelligence Enrichment Doctrine V1.

## 9. Why this is bigger

WESLR should not become a bag of deterministic patches.

Instead:

- WESLR should develop a reusable reasoning substrate
- subject helpers should be selected by the engine
- failed evals should enrich the engine generally

The architectural shift is from local benchmark patching to a reusable reasoning layer that can support many official-style tasks.

## 10. Future implementation phases

A. ReasoningTrace schema  
B. Task classifier  
C. Solver registry  
D. Formal logic solver as first real solver  
E. Ethics/tradeoff solver migration into solver registry  
F. MCQ adapter calls reasoning engine  
G. failure bridge records solver-level failures  
H. scorecard compares before/after  
I. no official claim

These phases are ordered to preserve doctrine-first growth and to keep measurement separated from marketing or benchmark theater.

## 11. Success criteria

Success means:

- fewer no-answer failures across multiple subjects
- improved answer selection on internal subsets
- reusable reasoning traces
- explanations remain human-readable
- failures become general improvements
- official_score remains false

Success does not mean any official benchmark claim. It does not mean ranked benchmark-status language. It does not mean memorized benchmark behavior.
