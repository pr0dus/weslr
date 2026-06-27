# WESLR MICRO‑THEORY TRACE PACKET SCHEMA PLANNING V1

## 1. Executive summary
**Verdict:** trace_packet_schema_planning_ready

## 2. Scope and non‑scope
- **Planning only** – no executable JSON schema, no validators, no runtime wiring.
- No changes to the ledger, activation‑gate, or alias‑policy implementations.
- No provider/model calls, no public ARC/Kaggle data, no benchmark claims.
- No final‑answer generation, no behavior‑pack promotion, no AGI‑related claims.
- No modifications to the solver or its code.
- No persistence or `.weslr` writes.

## 3. Design inheritance
The packet planning inherits concepts from the completed Micro‑Theory work:
- **Solver design** – how pressures are computed.
- **Ledger design** – structured trace entries for each synthetic mock.
- **Ledger mock trials** – mixed absence, salience, overfit, certainty‑channel cases.
- **Ablation confident‑wrong mock** – handling of intentionally wrong confident predictions.
- **Adversarial bidirectional mocks** – rival‑grammar and contradiction handling.
- **Activation‑gate** – canonical families activated before any alias use.
- **Broader activation‑gate trials** – validation of gate behavior.
- **Collapse experiment** – category‑collapse safety analysis.
- **Alias policy** – optional reporting shorthand (`absence_of_expected_change_pressure`, `salience_distractor_pressure`).
- **Broader alias‑policy review** – confirmed safety, auditability, and fail‑open behavior.

## 4. Proposed future packet sections (conceptual)
| Section | Conceptual purpose |
|--------|-------------------|
| A. Packet identity | Unique ID, version, timestamp. |
| B. Boundary metadata | Repo/branch/HEAD, lane, reviewer, timestamp. |
| C. Synthetic case identity | Name, type (e.g., mixed‑absence), synthetic‑only flag. |
| D. Solver‑visible train material | Train inputs, expected train outputs (canonical pressures). |
| E. Solver‑visible test material | Test input (synthetic case) for inference. |
| F. Evaluator‑only post‑check material | Intended rule, expected test output, audit notes. |
| G. Activation‑gate result | Gate mode, activated canonical families, dormant families, fail‑open triggers. |
| H. Canonical pressure families | List of all activated canonical categories (role‑stability, absence, distractor‑rejection, etc.). |
| I. Alias/reporting shorthand | Optional alias names, canonical expansions, sub‑notes, fail‑open status. |
| J. Certainty channels | Separate target, action, representation certainty values, evidence, disagreement flags. |
| K. Rival grammar / ambiguity state | Flags for rival‑grammar pressures, unresolved ambiguity, contradiction/precedence. |
| L. Contradiction & precedence | Explicit representation of contradictory pressures and precedence ordering. |
| M. Absence / exception / non‑change | Capture `absence_of_expected_change_pressure` semantics when used. |
| N. Overfit diagnostics | Explicit `concept‑bloat` and `coordinate‑overfit` families (never aliased). |
| O. Rejected‑output audit | Record which output was rejected, why, and supporting canonical pressures. |
| P. Why‑not‑other‑output reasoning | Explain alternative plausible outputs and why they were discarded. |
| Q. Inevitability / safe‑failure summary | Summarize inevitability label, safe‑failure status, and any required evidence. |
| R. Auditability notes | Links to original mock definitions, gate activation logs, alias expansion checklist. |
| S. Ceremony / compactness notes | Note if alias shorthand reduced prose and any trade‑offs. |
| T. Schema‑readiness notes | Indicate that this is a design plan; future work may encode as optional display‑labels after review. |

## 5. Required conceptual fields (selected examples)
- **packet_id** – string, required, solver‑visible, unique identifier.
- **lane_name** – string, required, reviewer‑only, indicates current lane.
- **case_type** – enum, required, solver‑visible (e.g., mixed‑absence, salience‑real‑role).
- **train_inputs** – dict, required, solver‑visible, maps feature names to values.
- **train_outputs_canonical** – list of canonical pressure names, required, solver‑visible.
- **test_input** – dict, required, solver‑visible.
- **intended_rule** – string, evaluator‑only, describes expected reasoning.
- **expected_test_output** – list of canonical pressures, evaluator‑only.
- **gate_mode** – enum (full, focused, safe‑failure), required, solver‑visible.
- **activated_families** – list, required, canonical.
- **dormant_families** – list, optional, canonical.
- **alias_used** – enum (absence_of_expected_change_pressure, salience_distractor_pressure, none), optional, report‑only.
- **alias_expansion** – list, required if alias_used, canonical.
- **certainty_target / certainty_action / certainty_representation** – float 0‑1, required, separate channels.
- **rival_grammar** – bool, required, canonical.
- **contradiction_precedence** – bool, required, canonical.
- **overfit_concept_bloat** – bool, required, canonical (must stay false for alias use).
- **overfit_coordinate_overfit** – bool, required, canonical.
- **rejected_output** – string, required, audit.
- **why_not_other_output** – string, required, audit.
- **inevitability_label** – enum (inevitable, possible, uncertain), required, audit.
- **safe_failure** – bool, required, audit.

## 6. Alias representation plan
- Aliases are **optional display/report labels only**.
- When present, the packet must contain:
  - `alias_name`
  - `canonical_expansion` (full list of canonical families the alias replaces).
  - `sub_notes` (e.g., expected‑but‑missing effect, color‑bait).
  - `fail_open_trigger` flag (true if safety required expansion).
- Aliases **must never replace** `concept‑bloat` or `coordinate‑overfit` families.
- Aliases are **disabled** for overfit families and any future alias merging that would hide them.

## 7. Pressure‑family representation plan
All **canonical categories** listed in section 4(H) must be present when active. Optional alias mapping only for:
- `absence_of_expected_change_pressure` → expands to `negative‑evidence` + `non‑change`.
- `salience_distractor_pressure` → expands to `distractor‑rejection` + `color‑bait`.
All other families (role stability, rival grammar, contradiction, overfit, etc.) must remain explicit.

## 8. Certainty‑channel representation plan
Three separate certainty fields must be recorded for each packet:
- `certainty_target`
- `certainty_action`
- `certainty_representation`
Each includes a numeric value, evidence notes, and a `disagreement` boolean. Fail‑open may promote a certainty channel to `unknown` when safety requires.

## 9. Activation‑gate representation plan
Packet must capture the gate decision:
- `gate_mode` – e.g., `full`, `focused`, `safe_failure`.
- Lists of `activated_families` and `dormant_families`.
- Any `fail_open_triggers` (e.g., when a salient feature is real).
- Reviewer‑note explaining why a particular mode was chosen.

## 10. Solver‑visible / evaluator‑only split plan
- **Solver‑visible** sections (D, E, G‑N) are used by the inference engine.
- **Evaluator‑only** sections (F, P‑Q, R‑S) are for post‑run verification and audit; they must never influence the solver.
- The packet design enforces that `expected_test_output` is **not** consulted during inference.

## 11. Rejected‑output and why‑not‑other‑output plan
- `rejected_output` records the output the model rejected.
- `why_not_other_output` explains the rival output(s) and the canonical pressures that caused rejection.
- Must include certainty impact and any safe‑failure reasoning.

## 12. Safe‑failure and inevitability plan
- `inevitability_label` (inevitable / possible / uncertain).
- `safe_failure` boolean – true when the model must fall back to a safe default.
- If `safe_failure` is true, include `required_evidence` notes and `rival_grammar_effect`.

## 13. Overfit protection plan
- `overfit_specificity_pressure` remains **forbidden**; no alias may map to it.
- `concept‑bloat` and `coordinate‑overfit` families are always listed separately.
- Any packet that would otherwise hide these must set `fail_open_trigger = true` to expand them.

## 14. Auditability and review plan
- Every alias entry must be expandable to its canonical list.
- The packet includes a `audit_log_url` (or identifier) pointing to the original mock definition.
- Reviewers can verify:
  - Activation‑gate activation order.
  - Certainty values and disagreements.
  - That no forbidden overfit alias was used.
  - That fail‑open behavior was correctly recorded.

## 15. What not to encode yet
- Executable JSON schema, validators, data‑class definitions.
- Runtime parser or solver integration code.
- Learned‑scorer or scoring functions.
- ChatResponder or UI wiring.
- Public benchmark or Kaggle integration.
- Provider/model calls, persistence, or `.weslr` writes.

## 16. Future implementation readiness criteria
- **Planning reviewed** and approved by governance.
- **Field list stabilized** (no further additions needed).
- **Alias expansion** fully documented and reviewed.
- **Overfit separation** confirmed in all review cases.
- **Evaluator‑only boundary** defined and verified.
- **Fail‑open representation** agreed upon.
- **Release‑gate** path allowances finalized.
- **Explicit authorization** for any executable schema work.

## 17. Recommended next safe local follow‑up
**REVIEW_MICRO_THEORY_TRACE_PACKET_SCHEMA_PLANNING_V1** – a governance review of this planning document before any implementation.

## 18. Hand‑off update (post‑artifact)
- Current verified WESLR HEAD: 7d3694de48ea83077338012b2d0077e8e0c9a1ac
- Last pushed remote milestone HEAD: 4e92ed3b2d1043e80e27568990a5c4ae8add7119
- Completed lane: DESIGN_MICRO_THEORY_TRACE_PACKET_SCHEMA_PLANNING_V1
- Executive verdict: trace_packet_schema_planning_ready
- Recommended next lane: REVIEW_MICRO_THEORY_TRACE_PACKET_SCHEMA_PLANNING_V1
- Push policy: "no routine pushes until Kaggle intake/test milestone or Nova need"

---
*All validation steps passed. No protected files changed. No .weslr files touched.*