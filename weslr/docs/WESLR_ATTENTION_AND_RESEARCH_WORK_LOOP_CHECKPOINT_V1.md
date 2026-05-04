# WESLR Attention Loop + Research Work Loop — Checkpoint V1

**Date:** 2026-05-04 19:17 GMT+2
**Session:** main:c03c2c7
**Purpose:** Design checkpoint for WESLR dual-loop architecture — self-review (Attention Loop) and user mission (Research Work Loop)
**Status:** `checkpoint` — not accepted doctrine

---

## 1. Purpose

WESLR should not only answer once. It should keep working on governed questions over time by reading safe sources and suggesting next actions.

Two distinct loops share the same daemon infrastructure but serve different scopes:

- **Attention Loop** — WESLR self-review: architecture gaps, validation gaps, stale docs, missing lifecycle links, doctrine/implementation drift.
- **Research Work Loop** — User missions: research goals, material/biology/chemistry/physics comparison, hypotheses, experiments, evidence gaps, collaboration outputs.

Both loops produce **proposals** written to a pending store — never auto-executed.

---

## 2. Core Distinction

| Dimension | Attention Loop | Research Work Loop |
|---|---|---|
| Owner | WESLR (self-review) | User (mission owner) |
| Scope | Architecture, doctrine, lifecycle | Research domain, evidence, hypotheses |
| Triggered by | Stale records, unresolved gaps, time-based tick | Mission cadence, evidence gaps, new data |
| Output | Gap proposals, architectural suggestions | Research suggestions, next-action proposals |
| Visibility | Operator-only | Operator-visible + user-visible options |
| Safe read sources | Doctrine registry, phase registry, observation checkpoint, proposal store | Local files, hypothesis repository, experiment results, approved local sources |
| Forbidden | Code editing, auto-commit, contract mutation | Hazardous synthesis, autonomous lab actions, dangerous procurement |

**Shared constraint:** The Attention Loop writes gap proposals to `.weslr/pending_messages.jsonl`. The Research Work Loop writes mission suggestions to `.weslr/missions.jsonl`. Neither loop auto-executes anything.

---

## 3. Existing Capabilities (Real Files Only)

> Path, contribution, safe use, limitation.

| File | Contribution | Safe Use | Limitation |
|---|---|---|---|
| `weslr/proactive_daemon.py` | Periodic suggestion loop, deduplication, interval control | Manual `start_proactive_daemon()` / `stop_proactive_daemon()` | No `run_once` mode yet; no source adapters for gap detection |
| `weslr/modules/temporal_reasoning.py` | Time-series forecasting, temporal logic, daemon alert threshold crossing | Open question detection in research missions | Repaired in commit adc1de55; tests passing |
| `weslr/modules/spatial_reasoning.py` | Molecular geometry, chirality, VSEPR, molecular fingerprint | Material structure comparison in research missions | Simulation-only, no real lab data |
| `weslr/modules/abductive_reasoner.py` | Abductive explanation generation, backward-chaining rule engine | Hypothesis explanation for research missions | No external knowledge; rule-based only |
| `weslr/modules/meta_analyst.py` | Fixed-effect meta-analysis, evidence pooling | Cross-study evidence synthesis for research | No literature search; fixed-effect model only |
| `weslr/modules/transfer_analogy.py` | Cross-domain hypothesis transfer via analogical mapping | Transfer validated patterns to new research domains | Analogy is labeled, not validated; no ground-truth |
| `weslr/modules/workspace.py` | Per-tenant private hypothesis store, shared library, anonymized sharing | User collaboration, hypothesis sharing | In-memory only; no persistent storage across sessions |
| `weslr/modules/explanation_generator.py` | Template-based hypothesis explanation, causal link explanation | Human-readable research summaries | Template-only; no LLM or generative output |
| `weslr/modules/hypothesis_repository.py` | Per-tenant hypothesis store, deterministic UUID v5 IDs | User mission hypothesis tracking | In-memory only |
| `weslr/modules/experiment_suggester.py` | Rule-based next-experiment recommendations | Research experiment planning | No ML; rule-based only |
| `weslr/modules/report_generator.py` | Hypothesis report text/JSON generation | Research report output | Template-based; no LLM |
| `weslr/modules/scenario_explorer.py` | Multi-module what-if orchestration | Scenario exploration for research | Simulation-only |
| `weslr/modules/experiment_simulation.py` | Experiment simulation stub | Simulation for research planning | Mock output always labeled `[SIMULATION MODE – Not real data]` |
| `weslr/docs/WESLR_DOCTRINE_REGISTRY_V1.md` | Phase 6/7/9/10 doctrine binding, status tracking | Attention Loop source for doctrine gap detection | Not auto-updated; operator-maintained |
| `weslr/docs/WESLR_SELF_REVIEW_DISCOVERY_V1.md` | Self-review capability gap analysis | Attention Loop design reference | Design only, not implemented |
| `weslr/docs/WESLR_PHASE_6_PHYSICAL_MATH_REASONING_DOCTRINE_V1.md` | Physical constraint doctrine, hard/soft checks | Research material validation | No adaptive learning |
| `weslr/docs/WESLR_PHASE_7_UNIFIED_HYPOTHESIS_DOCTRINE_V1.md` | Hypothesis lifecycle, experiment workflow | Research mission tracking | No automatic hypothesis generation |
| `weslr/docs/WESLR_PHASE_9_ADVANCED_REASONING_DOCTRINE_V1.md` | Abduction/meta/transfer doctrine | Research reasoning support | Labeled, not validated |
| `weslr/docs/WESLR_PHASE_10_COLLABORATION_DOCTRINE_V1.md` | Collaboration, workspace, anonymization | Research sharing | Anonymization strips user context |

**Missing:** `proactive_suggestions.py` does not exist (marked as proposed). `proactive_daemon.py` handles suggestions internally.

---

## 4. Proposed Mission Schema

```json
{
  "mission_id": "string (UUID v5 from tenant_id:title:timestamp_hour)",
  "owner_user_id": "string",
  "tenant_id": "string",
  "title": "string",
  "research_goal": "string",
  "domain_tags": ["material", "biology", "chemistry", "physics"],
  "allowed_sources": ["local_evidence", "hypothesis_repository"],
  "forbidden_outputs": ["hazardous_synthesis", "weaponization", "pathogen_engineering"],
  "safety_constraints": ["no_autonomous_lab", "no_procurement_guidance", "uncertainty_label_required"],
  "cadence_minutes": 60,
  "current_questions": ["string"],
  "hypotheses": ["hypothesis_id or inline"],
  "evidence_links": ["file_path or URL"],
  "candidate_suggestions": ["string"],
  "status": "draft | active | paused | closed",
  "automatic_execution": false,
  "operator_visible": true,
  "public_user_visible": false,
  "created_at": "ISO-8601",
  "last_reviewed_at": "ISO-8601",
  "next_run_at": "ISO-8601",
  "mission_note": "string"
}
```

---

## 5. Safe Research Loop (V1 — Manual, Local-Only)

```
Load active missions
  → read approved local sources
  → identify stale questions / missing evidence
  → generate candidate hypotheses
  → apply Phase 6 feasibility check
  → apply Phase 7 hypothesis/experiment workflow
  → apply Phase 9 abduction / meta / transfer (where safe)
  → safety filter
  → rank suggestions
  → write pending suggestion / proposal
  → await operator review
```

**No automatic execution at any stage.**

---

## 6. Source Adapters

### Existing

| Adapter | Type | Notes |
|---|---|---|
| `LocalEvidenceAdapter` | 🔜 Proposed | Reads local files in `weslr/` — no dedicated adapter class file exists yet |
| `HypothesisRepositoryAdapter` | ✅ Existing | Interfaces with `hypothesis_repository.py` |
| `ExperimentResultAdapter` | ✅ Proposed | Reads `experiment_simulation.py` output |
| `SafetyConstraintAdapter` | ✅ Proposed | Reads `physics_constraints.py` hard/soft rules |
| `CollaborationWorkspaceAdapter` | ✅ Existing | Interfaces with `workspace.py` |

### Proposed (V2+)

| Adapter | Type | Notes |
|---|---|---|
| `UserUploadedDatasetAdapter` | 🔜 Proposed | Reads user-uploaded CSV/JSON in workspace |
| `LiteratureSummaryAdapter` | 🔜 Proposed | Reads local literature summaries |
| `MaterialPropertyAdapter` | 🔜 Proposed | Reads material property databases |
| `ExternalWebSearchAdapter` | 🔜 Proposed | Disabled by default; requires governance approval |

### Blocked

| Adapter | Status | Reason |
|---|---|---|
| `HazardousSynthesisAdapter` | ❌ Blocked | Safety boundary violation |

---

## 7. Safety Boundary

### Allowed

- High-level research comparison
- Material property comparison
- Literature-style summaries
- Hypothesis generation
- Non-operational experiment planning
- Risk identification
- Safety screening

### Forbidden

- Hazardous synthesis instructions
- Pathogen engineering
- Weaponization
- Toxic deployment guidance
- Autonomous lab actions
- Covert delivery systems
- Evasion/misuse optimization
- Unsupervised external actions
- Dangerous procurement guidance

### Required on All Outputs

- `uncertainty` label
- `evidence` / `provenance` field
- Safety note for sensitive domains
- `automatic_execution: false`

---

## 8. Daemon Integration

### V1 (This Checkpoint)

- Manual `run_once` only — no auto-start
- Local mission store (`.weslr/missions.jsonl` — proposed, per-tenant)
- Pending mission suggestions: `.weslr/pending_messages.jsonl` (existing Attention Loop target)
- Operator review store: `contract_proposal_review_log.jsonl` (existing, separate from missions)
- Local evidence only

### V2 (Proposed)

- Scheduled cadence (operator-configured)
- Workplace surface integration
- `cadence_minutes` per mission

### V3 (Proposed)

- External literature sources only after governance approval
- User-visible suggestion surface

---

## 9. First Safe Vertical Slice

### Components

1. **Mission schema** — Section 4 above
2. **Local mission store** — `.weslr/missions.jsonl` (per-tenant, proposed)
3. **`run_once_mission_review()`** — one-shot review function (proposed)
4. **`LocalEvidenceAdapter`** — existing, interfaces with local files
5. **Detector** — "open question but no evidence" flag
6. **Suggestion output** — writes to `pending_messages.jsonl`
7. **Tests** — `test_research_work_loop_v1.py` (proposed)

### Example Mission

> **Title:** Soft micro-robotics material candidates
> **Research goal:** Identify biocompatible candidate materials for soft micro-robotics actuators
> **Domain tags:** material, biology, chemistry
> **Allowed sources:** local_evidence, hypothesis_repository
> **Current question:** "What material properties enable reversible actuation in soft robots?"
> **Hypothesis:** "Hydrogel composites with ionic polymer matrix show reversible electro-active deformation"

### Example Suggestion Output

```
Suggestion: Add material property comparison table as next step.
Source: LocalEvidenceAdapter
Evidence: no comparison table found in current evidence_links
Confidence: 0.7
Safety: no sensitive domain
automatic_execution: false
Provenance: run_once_mission_review() @ 2026-05-04T17:30:00Z
```

---

## 10. Relationship to Self-Review (Attention Loop)

Reference: `weslr/docs/WESLR_SELF_REVIEW_DISCOVERY_V1.md`

The **Attention Loop** inspects WESLR's own architecture:

- Doctrine registry gaps
- Phase registry omissions
- Stale observation checkpoint records
- Unresolved proposal review records
- Test failures (e.g., temporal_reasoning) — **Note: repaired in adc1de55, tests now passing**

The **Research Work Loop** inspects user research missions:

- Open questions without evidence
- Missing hypothesis comparison
- Experiment result gaps
- Collaboration output gaps

**Shared infrastructure:**

- `proactive_daemon.py` (existing)
- `pending_messages.jsonl` (existing write target)
- Suggestion/rank/safety-filter pipeline (proposed)

**Distinct scopes:**

- Attention Loop reads: doctrine files, phase registry, observation checkpoint, proposal store
- Research Work Loop reads: mission store, local evidence, hypothesis repository, experiment results

---

## 11. Registry Impact

**Recommended later update to `WESLR_DOCTRINE_REGISTRY_V1.md`:**

```
## Attention Loop — Checkpoint
Status: checkpoint
Checkpoint file: WESLR_ATTENTION_AND_RESEARCH_WORK_LOOP_CHECKPOINT_V1.md
Note: Not yet accepted doctrine. Pending vertical slice implementation.

## Research Work Loop — Checkpoint
Status: checkpoint
Checkpoint file: WESLR_ATTENTION_AND_RESEARCH_WORK_LOOP_CHECKPOINT_V1.md
Note: Not yet accepted doctrine. Pending vertical slice implementation.
```

---

---

## 12. Implementation Status

| Layer | Status |
|---|---|
| **Checkpoint / design** | ✅ Complete — this document |
| **V1 runtime** | ❌ Not implemented — implementation pending |
| **Doctrine registry update** | ⏳ Pending — attention loop and research work loop not yet registered |
| **Tests** | ⏳ Pending — `test_research_work_loop_v1.py` and `test_attention_loop_v1.py` not written |
| **Commit** | ⏳ Pending — no code staged or committed |

**This checkpoint is design-only. Neither loop is implemented. Neither loop is accepted doctrine.**

---

## 13. Open Questions

| # | Question | Options |
|---|---|---|
| 1 | Per-user or per-tenant missions? | Per-tenant is consistent with existing HypothesisRepository model |
| 2 | Mission store path? | `.weslr/missions.jsonl` (proposed) — consistent with `.weslr/` namespace |
| 3 | Pending messages vs proposal store vs mission store? | Three distinct stores: `pending_messages.jsonl` (proposals), `contract_proposal_review_log.jsonl` (operator review), `missions.jsonl` (missions) |
| 4 | Operator-visible vs user-visible split? | `operator_visible: true/false`, `public_user_visible: true/false` on mission schema |
| 5 | External literature search later? | V3 only, requires governance approval — blocked by default |
| 6 | Sensitive domain classification? | Tag-based (`domain_tags`) + safety filter at output stage |
| 7 | Connection to Phase 7 hypotheses? | Mission schema references `hypotheses[]` which maps to `hypothesis_repository.py` IDs |

---

## Final Report

### Doc Created

✅ `weslr/docs/WESLR_ATTENTION_AND_RESEARCH_WORK_LOOP_CHECKPOINT_V1.md`

### Path Corrections Applied

| Chat Design Name | Actual Path / Status |
|---|---|
| `proactive_suggestions.py` | ❌ Does not exist — handled inside `proactive_daemon.py` |
| `Phase 6 doctrine doc` | ✅ `WESLR_PHASE_6_PHYSICAL_MATH_REASONING_DOCTRINE_V1.md` |
| `Phase 7 doctrine doc` | ✅ `WESLR_PHASE_7_UNIFIED_HYPOTHESIS_DOCTRINE_V1.md` |
| `Phase 9 doctrine doc` | ✅ `WESLR_PHASE_9_ADVANCED_REASONING_DOCTRINE_V1.md` |
| `Phase 10 doctrine doc` | ✅ `WESLR_PHASE_10_COLLABORATION_DOCTRINE_V1.md` |
| `WESLR_OBSERVATION_CHECKPOINT_V1.md` | ✅ exists at `weslr/docs/` |
| `WESLR_SELF_REVIEW_DISCOVERY_V1.md` | ✅ exists at `weslr/docs/` |

### Existing vs Proposed

| Component | Status |
|---|---|
| `proactive_daemon.py` | ✅ Existing — 199 lines, manual start/stop |
| `LocalEvidenceAdapter` | ✅ Proposed — no dedicated file, interfaces via existing modules |
| `HypothesisRepositoryAdapter` | ✅ Existing — `hypothesis_repository.py` |
| `ExperimentResultAdapter` | ✅ Proposed — no dedicated file |
| `SafetyConstraintAdapter` | ✅ Proposed — `physics_constraints.py` exists, no adapter yet |
| `CollaborationWorkspaceAdapter` | ✅ Existing — `workspace.py` |
| `run_once_mission_review()` | ✅ Proposed — not implemented |
| `missions.jsonl` | ✅ Proposed — not created |
| `test_research_work_loop_v1.py` | ✅ Proposed — not implemented |

### Open Questions (7)

All listed in Section 12. Per-tenant missions and three-store separation are the most consequential architectural decisions.

### Recommended Next Step

**Implement first vertical slice (Section 9):**

1. Define mission schema in `weslr/schemas/mission.py` (proposed)
2. Create `.weslr/missions.jsonl` (proposed store)
3. Add `run_once_mission_review()` to `proactive_daemon.py` (proposed addition)
4. Wire `LocalEvidenceAdapter` + hypothesis repository read path
5. Write test `test_research_work_loop_v1.py`
6. Operator reviews output before V2 cadence scheduling

**Do not auto-start daemon. Do not commit. Docs only.**