# ARC Synthetic 3‑Step – Broad Hard‑80 Design Review (V1)

**Repository**: `/data/data/com.termux/files/home/weslr-pr47-clean`
**Branch**: `occ-discovery-doctrine-implementation-20260613`
**Lane**: `REVIEW_ARC_SYNTHETIC_3_STEP_BROAD_HARD_80_DESIGN_V1`
**Start HEAD**: `c2f9a4e7`

## Summary of findings
| Check | Result |
|-------|--------|
| All 80 task IDs `BH80_001` – `BH80_080` defined exactly once | **FAIL** – the current design document only contains an excerpt and does not list the full 80 tasks. |
| Every task declares exactly 3 primitives | **PASS** for the excerpt, but cannot be verified for missing tasks. |
| Exactly 8 families (BH‑A … BH‑H) with 10 tasks each | **PASS** in description, but actual task‑to‑family mapping is missing for many IDs. |
| Difficulty distribution (0 easy, 16 medium, 48 hard, 16 adversarial) | **PASS** in description, but not verifiable without the full list. |
| Broad primitive inventory (13 primitives) present | **PASS** – the excerpt shows a wide set of primitives. |
| Each task includes required fields (task_id, family_id, difficulty, primitive_sequence, scene_spec, hardness reason, shortcut trap, leakage flags, trace requirements) | **PASS** for the excerpt; missing for the rest. |
| No expected‑output leakage | **PASS** – design explicitly forbids leakage. |
| No public ARC data / hidden private data | **PASS** – all scenes are synthetic. |
| Hard‑40 relationship clarified | **FAIL** – the design states that Hard‑40 is used for families BH‑A and BH‑B, but only the first *20* Hard‑40 tasks are referenced (first 10 for BH‑A, next 10 for BH‑B). The remaining 20 Hard‑40 tasks are not accounted for. |
| Overall hardness – sufficiently hard? | **PARTIAL** – the excerpt contains many genuinely hard/adversarial tasks, but without the full 80‑task list we cannot confirm that the overall set avoids too many easy direct‑primitive applications. |
| All primitives supported by current dispatch | **PASS** – all listed primitives have wrappers in `weslr.arc_synthetic_3_step_real_dispatch`. |

## Required repairs
1. **Provide the complete 80‑task table** – list every `BH80_001` … `BH80_080` with:
   - `family_id` (BH‑A … BH‑H, 10 tasks each)
   - `difficulty`
   - `primitive_sequence` (exact three primitives)
   - `hardness_reason`
   - `shortcut_trap`
   - `scene_spec` summary (grid size, number of objects, key attributes)
2. **Clarify Hard‑40 seeding** – either:
   * Use **all 40 Hard‑40 tasks**, assigning the first 20 to BH‑A and the remaining 20 to BH‑B, **or**
   * State explicitly that **only the first 20 Hard‑40 tasks** are reused and the other 20 are new designs. The current wording is ambiguous and must be corrected. 
3. **Verify family sizes** – ensure that each family has exactly 10 tasks after the full table is built. 
4. **Confirm difficulty counts** – after the table is complete, count tasks per difficulty and ensure they match the target (16 medium, 48 hard, 16 adversarial). 
5. **Add a short validation checklist** to the design (e.g., unit‑test stub name, schema validation steps). 
6. **Include a note** that the design does not rely on any public ARC data or hidden data, reinforcing the leakage‑prevention rule. 

## Suggested next steps
- Update the design document to include the full task specification table and the clarified Hard‑40 relationship.
- Once the design is complete, run a quick static‑analysis script to confirm:
  * 80 unique IDs
  * 3 primitives per task
  * 8 families with 10 tasks each
  * Correct difficulty distribution
  * All leakage flags set to `false`.
- After the repaired design passes these checks, the next lane can proceed to **implementation** of the generator.

---
**Verdict**: `needs_design_repair_before_generator`

---
**Recommended next lane**: `IMPLEMENT_ARC_SYNTHETIC_3_STEP_BROAD_HARD_80_GENERATOR_V1` (once the design is repaired).