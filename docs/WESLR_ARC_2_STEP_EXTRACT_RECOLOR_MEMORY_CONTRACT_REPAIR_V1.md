# WESLR ARC 2‑Step Extract→Recolor Memory Contract Repair V1

- **Dispatch**: `REPAIR_BOUNDED_ARC_2_STEP_EXTRACT_RECOLOR_MEMORY_CONTRACT_V1`
- **Repo**: `/data/data/com.termux/files/home/weslr-pr47-clean`
- **Branch**: `occ-discovery-doctrine-implementation-20260613`
- **Start HEAD**: `6edd6dbceb0a27fe85f8536362b60b31b82f06d1`

## Goal
Repair the bounded memory contract for the 2‑step task
`pilot_2_step_easy_gen_03_extract_recolor_large_grid_v1`
which currently fails with `parameter_carryover_failure`.

## Investigation
The diagnostic trace for the failing candidate (extract → recolor) shows:

```json
"step_1_exports": [
  {
    "background_value": 4,
    "object_value": 7,
    "intermediate_non_background_values": [7],
    "extracted_object_value": 7
  },
  {
    "background_value": 4,
    "object_value": 0,
    "intermediate_non_background_values": [0],
    "extracted_object_value": 0
  }
]
"step_2_imports": [["background_value"], ["background_value"]]
"carried_parameters": [{"background_value": 4, "from_value": 7}, {"background_value": 4}]
"dropped_parameters": ["from_value", "object_value", "to_value"]
"parameter_origin_by_key": {"background_value": "mixed"}
"carryover_success": true
```
Key observations:
- The **recolor_symbol** primitive requires three parameters: `background_value`, `from_value`, `to_value`.
- The current carry‑over logic only matches `background_value`; `from_value`/`to_value` are dropped because they are not present in the step‑1 exports for `recolor_symbol`.
- For the **extract_largest_object → recolor_symbol** pair, the logical value to carry is the **extracted object colour** (`extracted_object_value`).
- The runner’s `_build_carryover_trace` does **not** consider `extracted_object_value` when building `carried_parameters` for `recolor_symbol`.

## Why a simple repair is not possible under current constraints
1. **Parameter semantics** – `recolor_symbol` expects a source colour (`from_value`) and a target colour (`to_value`). The extraction primitive only provides a *single* colour (the colour of the extracted object). Mapping a single colour to both `from_value` and `to_value` would change the intended visual effect (the task expects recoloring the extracted object to a *different* colour).
2. **No existing reference** – The task specification (`large_color = 4`, `target_color = 9`) indicates that the recolor step should change the extracted colour **to 9**. The extracted object colour is `7` (or `0` in the alternate training pair). There is no deterministic rule in the current codebase that maps `extracted_object_value` → `to_value` while preserving `from_value`.
3. **Bounded repair policy** – The lane forbids introducing new inference rules or altering the generator’s primitive signatures. Adding a rule that automatically sets `to_value` = `target_color` from the task spec would require modifying the **generator** or **solver** logic, which is explicitly disallowed.
4. **Safety** – Any automatic mapping would need to be justified by a higher‑level design decision (e.g., a new “extract‑to‑recolor” contract). Such a design change is outside the scope of this bounded repair.

## Conclusion
The missing memory contract cannot be resolved by a *localized* fix within the existing runner code while respecting the lane’s constraints. The failure is intrinsic to the mismatch between the **single‑value export** of `extract_largest_object` and the **dual‑value import** of `recolor_symbol`.

### Recommended next steps
- **Create a dedicated contract lane** (`DESIGN_EXTRACT_RECOLOR_MEMORY_CONTRACT_V1`) to explicitly define how an extracted colour should be mapped to `from_value`/`to_value` in subsequent recolor steps.
- Once the contract is approved, implement the necessary changes in `_build_carryover_trace` (or a higher‑level adaptor) to carry the appropriate values.
- Re‑run the 2‑step 80 continuity test after the contract is in place.

Until such a contract is formalized, the current `partial` status for
`pilot_2_step_easy_gen_03_extract_recolor_large_grid_v1` remains the correct and safe representation.
