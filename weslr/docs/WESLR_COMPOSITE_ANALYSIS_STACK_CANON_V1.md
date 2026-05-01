# WESLR COMPOSITE ANALYSIS STACK CANON V1

**Version:** 1.0
**Status:** ACTIVE DOCTRINE
**Date:** 2026-05-01
**Owner:** operator + system architect

---

## SECTION 1 — Purpose

The Composite Analysis Stack is WESLR's internal reasoning layer. It does not generate user-facing responses — it provides structural analysis, ranking, confidence estimation, and attention classification for all WESLR signal sources.

**Core statement:**

> *"Structure filters the signal. Ranking finds similarity. Probability estimates confidence. Governance decides authority. Models may explain, never rule."*

The stack is a read-only analytical instrument. It observes, classifies, measures, and summarizes — but it does not write, approve, modify, or act on its own conclusions.

---

## SECTION 2 — Why WESLR Must Not Be Deterministic-Only

WESLR processes diverse signal sources: public user messages, contract observations, insufficiency patterns, proposal reviews, attention summaries. Deterministic rules alone cannot handle this diversity — record types differ, confidence varies, attention priorities shift.

A pure deterministic-only model would:
- Treat every record identically regardless of type
- Assign uniform confidence to all records
- Ignore the structural differences between a live proposal and a fire-and-forget observation
- Collapse the meaningful distinctions that operator attention depends on

The Composite Analysis Stack preserves those distinctions without introducing non-determinism. It analyzes structure, measures similarity, estimates confidence, and defers all authority to the operator.

---

## SECTION 3 — Composite Layers

### 3.1 Structural Filtering

Each WESLR record has a `record_type`. The stack reads this and classifies it into a structural family:

| record_type | structural_class |
|-------------|------------------|
| `public_signal_v1` | `operational_signal` |
| `contract_observation_v1` | `observation_signal` |
| `contract_insufficiency_v1` | `insufficiency_evidence` |
| `contract_proposal_review_v1` | `review_candidate` |
| `aai_attention_summary_v1` | `attention_summary` |
| (unknown) | `unknown_signal` |

Structural class determines what operations are valid and what the record can be compared against.

### 3.2 Ranking / Distance Scoring

Similarity scoring compares records against reference templates. The score is based on field overlap:

- `record_type` match → +weight
- `response_contract` match → +weight
- `pattern_type` match → +weight
- `response_path` match → +weight
- `proposal_status` match → +weight
- `attention_level` match → +weight

The score is deterministic — same inputs always produce the same score. No probability distribution used.

### 3.3 Confidence Estimation

Confidence is derived from metadata completeness and structural indicators:

**Increases confidence:**
- `proposal_ready: true`
- `stable_across_checks >= 3`
- all expected fields present
- known `record_type`

**Decreases confidence:**
- missing `record_type`
- malformed structure
- `validation_errors` present
- unknown source family

Confidence bands: `low` (0.0–0.4), `medium` (0.4–0.75), `high` (0.75–1.0)

### 3.4 AAI Attention Classification

The stack feeds into AAI (Artificial Analysis Index) by providing richer analysis:

- AAI already classifies attention level (0–4) based on source and content
- Composite stack adds structure class, confidence band, and similarity context
- AAI remains the authoritative attention router; composite stack enriches AAI's input

AAI classification takes precedence. Composite stack does not override AAI decisions.

### 3.5 Governance Boundary

The stack enforces a hard governance boundary. Every output carries an explicit list of allowed and forbidden actions.

**Allowed:** analyze, summarize, rank, classify_structure, estimate_confidence

**Forbidden:** approve, modify_contract, write_truth, trigger_external_action, change_governance, write_memory, auto-apply_proposal

**Operator required for:** any write action, any proposal state transition, any contract modification.

### 3.6 Optional Model Explanation (Future)

When models are used in WESLR, they may explain their reasoning — but they do not rule. An explanation is one input to the composite stack, not a decision.

Rule: *"Models may explain, never rule."*

---

## SECTION 4 — Authority Boundary

The composite stack may:
- ✅ analyze a record's structure
- ✅ summarize patterns across records
- ✅ rank records by similarity or confidence
- ✅ recommend attention level for AAI
- ✅ provide confidence estimates to the operator
- ✅ read from any Pass 1 source

The composite stack may not:
- ❌ approve or reject a proposal
- ❌ modify a contract
- ❌ write truth to any record
- ❌ trigger external actions
- ❌ change its own governance rules
- ❌ write to user or session memory
- ❌ automatically apply a proposal

All substantive decisions remain with the operator.

---

## SECTION 5 — Relationship to AAI

AAI (Artificial Analysis Index) is the attention router. The composite stack is the analysis engine that feeds it.

```
Signal Source → Composite Stack (structure + confidence + similarity) → AAI (rank + classify + surface)
```

AAI classifies attention level (0–4). Composite stack provides the richer context that allows AAI to classify accurately:
- `improvement_explanation_query` + `proposal_ready: true` + `confidence: high` → AAI level 2 summary
- `contract_proposal_review_v1` + `attention_level: 3` → AAI level 3 ask operator

Composite stack without AAI: analytical only.
AAI without composite stack: still functional, but with less contextual richness.

---

## SECTION 6 — Relationship to Future Experiments

The stack is the foundation for future state-grounded conversations and learning experiments. V1 establishes the analysis infrastructure; future passes will extend into experiment recording and visible learning.

**Future experiments must be:**
- Explicit — both user and WESLR know an experiment is happening
- Evidence-based — learning is recorded as evidence, not applied silently
- Recorded — experiment outcomes go to a visible log, not to hidden state
- Operator-reviewed — no automatic self-modification based on experiments

**WESLR and users may learn together** through visible experiment records. This is different from WESLR silently modifying itself based on interaction patterns.

No silent self-modification. No hidden learning. All changes are evidence-backed and operator-reviewed.

---

## SECTION 7 — V1 Scope

**What V1 does:**
- Read-only analysis of Pass 1 sources
- Structural classification
- Confidence estimation
- Similarity scoring
- AAI attention enrichment
- Composite summary building
- Governance boundary enforcement

**What V1 does not do:**
- No /chat integration
- No LLM integration
- No Ollama calls
- No JSONL writes
- No proposal state changes
- No contract modifications
- No write actions

**V1 sources (Pass 1):**
- `public_signals.jsonl`
- `contract_observations.jsonl`
- `contract_insufficiency_log.jsonl`
- `contract_proposal_review_log.jsonl`
- `aai_attention_summary_v1` (in-memory from AAI run)

---

## SECTION 8 — Verdict

**`WESLR_COMPOSITE_ANALYSIS_STACK_CANON_V1_DEFINED`**

The Composite Analysis Stack is the analytical core of WESLR. It observes, measures, and summarizes — but it does not rule. Every output carries its governance classification. Every analysis defers to the operator for substantive action.

*No runtime behavior implemented. Doctrine only until implementation passes.*