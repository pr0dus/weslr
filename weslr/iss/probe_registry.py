"""ISS probe registry — declarative probe stubs only. No execution."""


def get_probe_registry() -> list[dict]:
    """
    Return static ISS probe definitions.
    All probes have execution_allowed=False — execution is never automated.
    """
    return [
        {
            "probe_id": "probe.front_door.chat",
            "target": "/chat deterministic routing",
            "category": "routing",
            "status": "defined",
            "execution_allowed": False,
            "description": "Checks whether deterministic C1-C6 routing is active before LLM fallback.",
        },
        {
            "probe_id": "probe.trace.proposals",
            "target": "proposal_trace.jsonl",
            "category": "traceability",
            "status": "defined",
            "execution_allowed": False,
            "description": "Checks whether proposal and decision trace records exist.",
        },
        {
            "probe_id": "probe.plans.non_executing",
            "target": "implementation_plans.jsonl",
            "category": "planning",
            "status": "defined",
            "execution_allowed": False,
            "description": "Checks whether implementation plans remain non-executing.",
        },
        {
            "probe_id": "probe.iss.diagnostics",
            "target": "iss_diagnostic_records.jsonl",
            "category": "diagnostics",
            "status": "defined",
            "execution_allowed": False,
            "description": "Checks whether ISS diagnostic records exist and are readable.",
        },
    ]