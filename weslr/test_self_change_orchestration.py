from weslr.self_change_orchestration import SelfChangeState, orchestrate_self_change


def test_self_change_flow_passes_and_commits():
    change = SelfChangeState(
        change_id="chg1",
        description="enable reflection toggle",
        approval_ref="app1",
        checkpoint_ref="ckpt0",
        rollback_ref="ckpt0",
        validation_plan="run adequacy + hook + reflection tests",
    )

    def apply_change():
        return True

    def run_validation():
        return "pass"

    def record_lineage():
        return "lineage-ref-1"

    result = orchestrate_self_change(change, apply_change=apply_change, run_validation=run_validation, record_lineage=record_lineage)
    assert result.state == "committed"
    assert result.lineage_ref == "lineage-ref-1"


def test_self_change_flow_rolls_back_on_fail():
    change = SelfChangeState(
        change_id="chg2",
        description="enable reflection toggle",
        approval_ref="app2",
        checkpoint_ref="ckpt0",
        rollback_ref="ckpt0",
        validation_plan="run adequacy + hook + reflection tests",
    )

    def apply_change():
        return True

    def run_validation():
        return "fail"

    def record_lineage():
        return "lineage-ref-2"

    result = orchestrate_self_change(change, apply_change=apply_change, run_validation=run_validation, record_lineage=record_lineage)
    assert result.state == "rolled_back"
    assert result.lineage_ref is None
