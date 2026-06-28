# WESLR ARC LEDGER DESERVEDNESS ASSEMBLER FUNCTIONAL COVERAGE REPAIR V1

## 1. Issue confirmation

The functional report passed but coverage verification showed code was missing:
- Output-affecting ambiguity check (safe failure requirement)
- MDL-only rejection (explicit metric tracking)

**Issue confirmed: YES**

## 2. Code changes

### Added: Output-affecting ambiguity check

In `_evaluate_candidate`, added check for ambiguity_flags that affect output:

```python
# Check: output-affecting ambiguity requires safe failure
ambiguity_flags = assembler_input.get("ambiguity_flags", {})
output_affecting = ambiguity_flags.get("affects_output", False)
if output_affecting:
    metrics["safe_failure_required_count"] += 1
    traces.append(_build_trace(
        "ambiguity_check", "system", "ambiguity_flags", False, "required", "output_affecting"
    ))
    return {
        "candidate_id": candidate.get("candidate_id"),
        "decision": "safe_failure_required",
        "reason": "output_affecting_ambiguity",
        ...
    }
```

### Fixed: MDL-only rejection logic

Simplified MDL-only check to properly detect:

```python
# Check: MDL-only selection
grammars = assembler_input.get("candidate_grammars", [])
mdl_only_grammars = [g for g in grammars if g.get("mdl_only") and not g.get("rules_from_train")]
if mdl_only_grammars:
    metrics["mdl_only_rejected_count"] += 1
    ...
```

## 3. Verified coverage

| Missing Case | Now Working |
|-------------|--------------|
| bounded_forced_unique_candidate_deserved | YES (forced + train = deserved) |
| output_affecting_ambiguity_requires_safe_failure | YES (safe_failure=1) |
| mdl_only_candidate_rejected | YES (mdl_only_rejected=1) |
| helper_output_as_evidence_blocked | YES (in bypass check) |
| trace_model_complete | YES (all fields present) |
| full_ledger_boundary | YES (all False/True correct) |

## 4. Validation

- `python3 -m py_compile`: PASS
- `python3 -m pytest`: PASS (31 tests)
- Protected files: unchanged
- `.weslr`: untouched

---

Issue confirmed: yes
Code changed: yes
Tests changed: no
Bounded forced unique explicit: yes
Ambiguity safe-failure explicit: yes
MDL-only rejection explicit: yes
Helper-output-as-evidence block explicit: yes
Trace model complete explicit: yes
Full ledger boundary explicit: yes
Candidate deserved count: 1
Candidate not deserved count: varies
Safe failure required count: 1
Forced unique output count: 1
MDL-only rejected count: 1
Helper output as evidence blocked count: varies
Final answer emitted count: 0
Public claim allowed count: 0
Assembler functionally complete: yes
Recommended next lane: DESIGN_ARC_GENERATIVE_BRIDGE_V5_REPLAY_V1
Validation: PASS
Test count/result: 31 passed
Protected files: unchanged
.weslr: untouched
Push avoided: yes
Final judgment: arc_ledger_deservedness_assembler_functional_coverage_repaired