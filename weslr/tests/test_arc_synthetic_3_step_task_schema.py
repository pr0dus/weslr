import pytest
from weslr.arc_synthetic_3_step_task_schema import (
    CORE_FAMILIES,
    generate_3_step_pilot_tasks,
    validate_task_schema,
)

def test_core_families_count():
    assert len(CORE_FAMILIES) == 8, "There should be exactly 8 core families"

def test_generate_20_tasks():
    tasks = generate_3_step_pilot_tasks()
    assert len(tasks) == 20, "Pilot must contain exactly 20 tasks"
    # Count occurrences per family
    family_counts = {f["family_id"]: 0 for f in CORE_FAMILIES}
    for t in tasks:
        family_counts[t["family_id"]] += 1
        validate_task_schema(t)
    for idx, family in enumerate(CORE_FAMILIES):
        expected = 3 if idx < 4 else 2
        assert family_counts[family["family_id"]] == expected, (
            f"Family {family['family_id']} should appear {expected} times"
        )

def test_primitive_sequence_length_and_flags():
    for task in generate_3_step_pilot_tasks():
        assert len(task["primitive_sequence"]) == 3
        # Verify no forbidden shortcut values are present in the dict keys
        for shortcut in task["forbidden_shortcuts"]:
            assert shortcut in ["expected_test_output", "task_id_shortcut", "generator_note_shortcut"]
        # Leakage flags must all be False
        for flag, val in task["leakage_flags"].items():
            assert val is False, f"Leakage flag {flag} must be False"
        # Trace requirements must all be True
        for req, val in task["expected_trace_requirements"].items():
            assert val is True, f"Trace requirement {req} must be True"

# End of test file
