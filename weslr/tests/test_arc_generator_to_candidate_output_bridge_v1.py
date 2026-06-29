import json

def test_bridge_adds_candidate_output_surface():
    from weslr.arc_generative_bridge_v5_replay import (
        build_generative_bridge_v5_replay_tasks_v1,
        run_generative_bridge_v5_replay_v1,
    )
    tasks = build_generative_bridge_v5_replay_tasks_v1()
    packet = run_generative_bridge_v5_replay_v1(tasks)
    records = packet['per_task_records']
    # All records should have a candidate_output_surface field (may be None)
    assert all('candidate_output_surface' in r for r in records)
    # No record should have status "unscorable_due_to_missing_expected_output"
    statuses = [r['post_ledger_scoring_status'] for r in records]
    assert not any(s == 'unscorable_due_to_missing_expected_output' for s in statuses)
    # All should be "unscorable_due_to_missing_candidate_output"
    assert all(s == 'unscorable_due_to_missing_candidate_output' for s in statuses)

