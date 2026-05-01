# WESLR Deterministic Anchor and Probabilistic Interpretation Canon V1

**Version:** 1.0
**Status:** DOCTRINE ONLY — no runtime implementation
**Date:** 2026-05-01

---

## Section 1 — Purpose

WESLR must not be understood as deterministic-only. Pure deterministic logic is too rigid for WESLR's long-term goals. This canon defines the correct architectural model: **deterministic-anchored**.

WESLR is deterministic-anchored:
- Deterministic authority governs safety, truth, governance, state, and approvals
- Probabilistic and model-assisted methods assist interpretation, uncertainty estimation, similarity, ranking, and exploration

These are two distinct layers with a clear authority boundary between them.

---

## Section 2 — Core Principle

**Canonical statement:**

> *"Determinism governs authority. Probability assists interpretation."*

**Deterministic core** = law, safety, state authority. The deterministic layer has final authority over all state changes, approvals, and truth.

**Probabilistic layer** = interpretation aid, not authority. Probabilistic methods may inform decisions but must route through the deterministic governance surface before any state change is committed.

There is no exception to this hierarchy. Probabilistic output never becomes truth directly.

---

## Section 3 — What Must Stay Deterministic

The following are non-negotiable deterministic boundaries. No probabilistic or model-assisted method may override, bypass, or substitute for these:

| # | Deterministic invariant |
|---|------------------------|-------------------------|
| D1 | Write permissions and access control |
| D2 | Privacy guarantees (raw prompt/PII rejection) |
| D3 | Append-only log append correctness |
| D4 | Proposal threshold logic (`proposal_ready`, `stable_across_checks >= 3`) |
| D5 | Operator approval gates |
| D6 | Contract modification permissions |
| D7 | Public/private mode rules |
| D8 | Production truth file integrity |
| D9 | Record schema enforcement (`safe_to_record=true`, `raw_prompt_stored=false`) |
| D10 | Governance surface authority over state changes |

---

## Section 4 — Where Probabilistic / Model-Assisted Methods Are Allowed

The following domains are open to probabilistic and model-assisted methods, always as advisory input to the deterministic layer:

| # | Domain | Role |
|---|---------|------|
| P1 | Vague intent classification | Assist interpretation when deterministic patterns are ambiguous |
| P2 | Semantic similarity | Rank candidate interpretations by relevance |
| P3 | Topic clustering | Group related queries for pattern analysis |
| P4 | Evidence comparison | Compare detected patterns against historical evidence |
| P5 | Uncertainty estimation | Provide confidence scores for interpretation routing |
| P6 | Ranking candidate interpretations | Order multiple possible interpretations by likelihood |
| P7 | Scientific/external evidence analysis | Assist evaluation of external data against known structures |
| P8 | Language expression and summarization | Help express deterministic outputs in natural language |
| P9 | Future multimodal analysis | Assist with image, audio, or structured data interpretation |
| P10 | Pattern grouping in insufficiency detection | Reduce rigidity in detecting repeated contract failures |

All P-domain outputs must feed into the deterministic governance surface. They do not bypass it.

---

## Section 5 — Forbidden Probabilistic Authority

Hard boundaries. No model, probabilistic system, or LLM output may:

| # | Forbidden |
|---|-----------|
| F1 | Become truth directly without deterministic verification |
| F2 | Write to Layer 0 (structured state / truth) |
| F3 | Approve proposals without operator authorization |
| F4 | Modify contract response text |
| F5 | Override governance surface decisions |
| F6 | Silently learn from public users (no persistent user-derived weights) |
| F7 | Bypass the forbidden-field schema enforcement |
| F8 | Trigger state changes without deterministic gate approval |

---

## Section 6 — Layer Placement

Future WESLR architectural placement:

```
Layer 0 — Structured State / Truth
  └── Production files, JSONL logs, contract schemas, inventory

Layer 1 — Deterministic Governance and Safety
  └── Write permissions, approval gates, PII filtering, schema enforcement,
      proposal thresholds, operator authorization, contract modification authority

Layer 2 — Probabilistic Interpretation Helpers
  └── Intent classification, semantic similarity, uncertainty estimation,
      language expression, model-assisted summarization

Layer 3 — Ranking, Distance, and Structural Filtering
  └── Candidate ranking, pattern grouping, structural distance measures

Layer 4 — Evidence Workspace and Model-Assisted Expression
  └── Evidence comparison, pattern clustering, expression assistance

Layer 5 — Operator-Approved Integration
  └── Final output to user; all Layer 2–4 outputs must pass Layer 1 before reaching Layer 5
```

**Critical rule:** Layers 2–4 are advisory only. All outputs from Layers 2–4 must feed into Layer 1 (governance) before any state change. Layer 5 is the user-visible output layer; it has no independent authority.

---

## Section 7 — Relationship to Current Observation Loop

The current observation loop remains valid:

```
/chat → public_signal → contract_observation → insufficiency_detector → proposal_bridge → review_queue
```

Current implementation is fully deterministic in its authority layer. This is correct and must be preserved.

**Future extension:** Insufficiency detectors may use probabilistic grouping or ranking (Layer 2–3) to reduce rigidity in pattern detection — e.g., semantically grouping similar queries across different surface forms. However:
- Thresholds remain deterministic (`stable_across_checks >= 3`)
- `proposal_ready` logic remains deterministic
- Operator approval remains the only authority for contract changes
- No probabilistic output becomes truth without deterministic verification

---

## Section 8 — Implementation Implications

Future work may add:

| # | Future capability | Layer |
|---|-----------------|-------|
| FI1 | Semantic grouping of similar queries | P2 / L3 |
| FI2 | Probabilistic uncertainty score per interpretation | P5 / L3 |
| FI3 | Ranking-based pattern grouping in insufficiency detection | P3 / L3 |
| FI4 | Evidence confidence score | P4 / L4 |
| FI5 | Model-assisted summarization of evidence for review | P8 / L4 |
| FI6 | Language-aware intent disambiguation | P1 / L2 |

All future implementation requires:
1. Separate specification document
2. Separate test suite
3. Deterministic governance surface integration
4. No bypass of Layer 1 authority

---

## Section 9 — Non-Goals

This canon does NOT implement:

- LLM runtime answering
- Autonomous learning from user interactions
- Model-based truth generation
- Automatic contract updates
- Probabilistic governance decisions
- Public-user memory or persistent user-derived state
- Any Layer 2–4 output that bypasses Layer 1

---

## Section X — Operator Burden Boundary

**Canonical principle:**

> *"Less operator micromanagement, not more."*

### Purpose

Probabilistic and model-assisted interpretation is allowed partly to **reduce operator burden** — not increase it. WESLR must not develop a culture of requiring operator approval for every interpretation, grouping, or summary. The operator's time and attention are the scarcest resource in the system.

Probabilistic methods exist to help WESLR:
- Classify signals more intelligently
- Group related patterns without rigid exact matching
- Summarize evidence for faster review
- Prioritize signals by likely impact
- Express outputs in readable language

They must not become a new class of mandatory approval loops for every minor uncertainty.


### High-Impact Transitions — Operator Review Required

Operator review and authorization is the required gate for:


| # | Transition type | Why operator required |
|---|----------------|---------------------|
| HR1 | Contract response changes | Affects all users, permanent until reverted |
| HR2 | State / truth file changes | Changes production record of fact |
| HR3 | Governance rule changes | Alters the authority structure itself |
| HR4 | Memory integration | Permanent record that survives session reset |
| HR5 | External actions | Side effects outside WESLR's control |
| HR6 | Public-facing behavior changes | Visible to all users, cannot be selectively undone |


### Low-Risk Outputs — Automatable

The following outputs may be automated without operator review when they are:

- **Read-only** — no write to production state
- **Reversible** — can be reverted without permanent consequence
- **Non-authoritative** — advisory only, not binding on the system
- **Clearly labeled internally** — annotated as probabilistic/assisted, not presented as fact
- **Not changing state or contracts** — zero production impact
- **Not exposed as truth** — not returned to users as definitive fact

Examples of automatable low-risk outputs:
- Semantic grouping of similar signals for pattern analysis (Layer 3)
- Uncertainty score on an interpretation (Layer 2)
- Model-assisted summarization of evidence for the review queue (Layer 4)
- Ranking of candidate contract patterns by likelihood (Layer 3)
- Language-aware re-expression of an already-determined fact (Layer 2)


### Boundary Rule

**Probabilistic output that assists a high-impact transition must route through the operator gate.**

**Probabilistic output that assists a low-risk, read-only, internal task need not create an operator review loop.**


The distinction is not about the method (deterministic vs. probabilistic). It is about the impact of the output:
- High-impact → operator gate required
- Low-risk read-only → automatable with internal annotation

---


## Section 10 — Verdict

```
WESLR_DETERMINISTIC_ANCHOR_AND_PROBABILISTIC_INTERPRETATION_CANON_V1_DEFINED
```

---

## Section 11 — Inventory Update

Update: `weslr/docs/WESLR_IMPLEMENTED_REALITY_INVENTORY_V1.md`

Add under SPEC / DOCTRINE ONLY:
- **Deterministic Anchor + Probabilistic Interpretation Canon**
  - Status: doctrine only, no runtime implementation
  - This document: `WESLR_DETERMINISTIC_ANCHOR_AND_PROBABILISTIC_INTERPRETATION_CANON_V1.md`

---

## Section 12 — Validation

Run:
```
git diff --name-only
```

Expected: only `weslr/docs/` files changed. No Python files, no JSONL files.

```
python3 weslr/tests/release_gate_v1.py
python3 weslr/tests/public_readiness_tests.py
```

Expected: both pass.

---

## Section 13 — Report

- **File created:** `weslr/docs/WESLR_DETERMINISTIC_ANCHOR_AND_PROBABILISTIC_INTERPRETATION_CANON_V1.md`
- **Inventory updated:** `weslr/docs/WESLR_IMPLEMENTED_REALITY_INVENTORY_V1.md` — added canon entry in SPEC / DOCTRINE ONLY section
- **Runtime files changed:** 0
- **JSONL files changed:** 0
- **Tests changed:** 0
- **Commit:** `2cfc23a` (observation loop phase 1 canon)
- **New commit:** separate commit for canon doc + inventory update
