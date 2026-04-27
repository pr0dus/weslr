"""ISS probe execution — simulated only. No real commands, filesystem, or network access."""

from weslr.iss.diagnostic_records import make_probe_result, record_iss_diagnostic


def execute_probe_simulated(probe: dict) -> dict:
    """
    Simulate a probe execution and record one ISS diagnostic result.
    No subprocess, no os.system, no pathlib inspection, no network access.
    """
    result = make_probe_result(
        probe_id=probe["probe_id"],
        target=probe["target"],
        status="ok",
        evidence={
            "mode": "simulated",
            "probe_id": probe["probe_id"],
            "note": "No real commands, filesystem inspection, or network access were performed.",
        },
        confidence="medium",
    )
    record_iss_diagnostic(result)
    return result