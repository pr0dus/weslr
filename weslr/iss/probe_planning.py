"""ISS probe planning — declarative plans only. No execution."""


def create_probe_plan(probe: dict) -> dict:
    """
    Build a structured probe plan from a probe definition.
    Returns only a plan dict — does not execute or write anything.
    """
    return {
        "type": "probe_plan",
        "probe_id": probe["probe_id"],
        "target": probe["target"],
        "steps": [
            "locate target",
            "validate existence",
            "inspect expected structure",
            "report status",
        ],
        "execution_allowed": False,
        "operator_approval_required": True,
    }