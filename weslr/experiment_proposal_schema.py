"""
WESLR Experiment Proposal Schema V1

Provides schema validation and proposal ID generation for the experiment
proposal layer. Read-only inputs, no execution, no writes to existing JSONL.

Rules:
- No raw prompt storage (schema enforces raw_prompt_stored: false)
- No forbidden fields
- All proposals have automatic_execution: false
- physical_action always requires operator approval
- self_improvement_suggestion always requires operator approval
- No Ollama, no external calls

Author: OCC (WESLR governed intelligence)
Version: 1.0.0
"""

from __future__ import annotations

import json
import re
import time as _time
from typing import Any, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

VALID_TYPES = frozenset({
    "search_insight",
    "physical_action",
    "simulation_run",
    "self_improvement_suggestion",
})

VALID_STATUSES = frozenset({
    "pending",
    "approved",
    "executed",
    "failed",
    "rejected",
    "stale",
})

VALID_RISK_LEVELS = frozenset({
    "low",
    "medium",
    "high",
    "critical",
})

VALID_SOURCES = frozenset({
    "user_timeline",
    "proactive_suggestion",
    "contract_insufficiency",
    "manual",
    "aai",
})

_FORBIDDEN_FIELDS = frozenset({
    "raw_prompt",
    "transcript",
    "full_conversation",
    "secret",
    "credential",
    "password",
    "token",
    "api_key",
    "private_key",
})

_PROPOSAL_ID_DATE_RE = re.compile(r"^EXP-(\d{4})(\d{2})(\d{2})-(\d+)$")

# ---------------------------------------------------------------------------
# 1. Proposal ID generation
# ---------------------------------------------------------------------------

def generate_experiment_proposal_id(
    existing_records: Optional[List[Dict[str, Any]]] = None,
    now: Optional[float] = None,
) -> str:
    """Generate a deterministic proposal ID: EXP-YYYYMMDD-NNN.

    NNN starts at 001 and increments based on the highest existing
    proposal_id found for the same date. Malformed IDs are skipped safely.

    Args:
        existing_records: List of proposal dicts to scan. If None, counter starts at 1.
        now: Unix timestamp for date determination. If None, uses current time.

    Returns:
        proposal_id string, e.g. "EXP-20260502-001"
    """
    if now is None:
        now = _time.time()
    lt = _time.localtime(now)
    date_str = _time.strftime("%Y%m%d", lt)

    counter = 1
    if existing_records:
        for rec in existing_records:
            pid = rec.get("proposal_id", "")
            m = _PROPOSAL_ID_DATE_RE.match(pid)
            if m:
                y, mo, d, n = m.groups()
                if f"{y}{mo}{d}" == date_str:
                    num = int(n)
                    if num >= counter:
                        counter = num + 1

    return f"EXP-{date_str}-{counter:03d}"


# ---------------------------------------------------------------------------
# 2. Validation
# ---------------------------------------------------------------------------

def validate_experiment_proposal(record: dict) -> Tuple[bool, List[str]]:
    """Validate a proposal record against the schema.

    Returns (is_valid, list_of_errors). Empty errors list means valid.

    Checks:
    - Required fields present and non-null
    - record_type = experiment_proposal_v1
    - type in VALID_TYPES
    - execution_status in VALID_STATUSES
    - risk_level in VALID_RISK_LEVELS
    - source in VALID_SOURCES
    - confidence is float 0.0-1.0
    - confidence_reasons is list
    - source_refs is list
    - result_refs is list
    - params is dict
    - No forbidden fields
    - automatic_execution is False
    - hidden_learning is False
    - raw_prompt_stored is False
    - physical_action forces requires_operator_approval=True
    - self_improvement_suggestion forces requires_operator_approval=True
    """
    errors: List[str] = []

    # record_type
    if record.get("record_type") != "experiment_proposal_v1":
        errors.append('record_type must be "experiment_proposal_v1"')

    # required string fields
    for field, field_type in [
        ("proposal_id", str),
        ("created_at", str),
        ("type", str),
        ("title", str),
        ("description", str),
        ("source", str),
    ]:
        val = record.get(field)
        if val is None or not isinstance(val, field_type) or not val:
            errors.append(f"required field '{field}' is missing, null, or empty")

    # params must be dict
    params = record.get("params")
    if params is None or not isinstance(params, dict):
        errors.append("required field 'params' must be a non-null dict")

    # confidence
    conf = record.get("confidence")
    if conf is None:
        errors.append("required field 'confidence' is missing")
    elif not isinstance(conf, (int, float)):
        errors.append("confidence must be a number")
    elif not (0.0 <= conf <= 1.0):
        errors.append("confidence must be between 0.0 and 1.0")

    # confidence_reasons
    cr = record.get("confidence_reasons")
    if cr is None:
        errors.append("required field 'confidence_reasons' is missing")
    elif not isinstance(cr, list):
        errors.append("confidence_reasons must be a list")
    elif not all(isinstance(r, str) for r in cr):
        errors.append("confidence_reasons must be a list of strings")

    # source_refs
    srefs = record.get("source_refs")
    if srefs is None:
        errors.append("required field 'source_refs' is missing")
    elif not isinstance(srefs, list):
        errors.append("source_refs must be a list")

    # result_refs
    rrefs = record.get("result_refs")
    if rrefs is None:
        errors.append("required field 'result_refs' is missing")
    elif not isinstance(rrefs, list):
        errors.append("result_refs must be a list")

    # execution_status
    status = record.get("execution_status")
    if status is None:
        errors.append("required field 'execution_status' is missing")
    elif status not in VALID_STATUSES:
        errors.append(f"execution_status must be one of: {', '.join(sorted(VALID_STATUSES))}")

    # type
    rec_type = record.get("type")
    if rec_type is None:
        errors.append("required field 'type' is missing")
    elif rec_type not in VALID_TYPES:
        errors.append(f"type must be one of: {', '.join(sorted(VALID_TYPES))}")

    # risk_level
    rl = record.get("risk_level")
    if rl is None:
        errors.append("required field 'risk_level' is missing")
    elif rl not in VALID_RISK_LEVELS:
        errors.append(f"risk_level must be one of: {', '.join(sorted(VALID_RISK_LEVELS))}")

    # source
    src = record.get("source")
    if src is None:
        errors.append("required field 'source' is missing")
    elif src not in VALID_SOURCES:
        errors.append(f"source must be one of: {', '.join(sorted(VALID_SOURCES))}")

    # authority must be experiment_proposal_only
    if record.get("authority") != "experiment_proposal_only":
        errors.append("authority must be 'experiment_proposal_only'")

    # safety flags
    if record.get("automatic_execution") is not False:
        errors.append("automatic_execution must be False")
    if record.get("hidden_learning") is not False:
        errors.append("hidden_learning must be False")
    if record.get("raw_prompt_stored") is not False:
        errors.append("raw_prompt_stored must be False")

    # operator_approval_required bool
    if not isinstance(record.get("operator_approval_required"), bool):
        errors.append("operator_approval_required must be a boolean")

    # type-specific rules
    if rec_type == "physical_action":
        if record.get("requires_operator_approval") is not True:
            errors.append("physical_action proposals must have requires_operator_approval=True")
        if record.get("operator_approval_required") is not True:
            errors.append("physical_action proposals must have operator_approval_required=True")
        if record.get("automatic_execution") is not False:
            errors.append("physical_action proposals must have automatic_execution=False")

    if rec_type == "self_improvement_suggestion":
        if record.get("requires_operator_approval") is not True:
            errors.append("self_improvement_suggestion proposals must have requires_operator_approval=True")
        if record.get("operator_approval_required") is not True:
            errors.append("self_improvement_suggestion proposals must have operator_approval_required=True")

    # forbidden fields
    for field in _FORBIDDEN_FIELDS:
        if field in record:
            errors.append(f"forbidden field '{field}' must not be present")

    return len(errors) == 0, errors


# ---------------------------------------------------------------------------
# 3. Proposal builder
# ---------------------------------------------------------------------------

def build_experiment_proposal(
    type: str,
    title: str,
    description: str,
    params: Dict[str, Any],
    confidence: float,
    confidence_reasons: List[str],
    source: str,
    source_refs: Optional[List[str]] = None,
    timeline_id: Optional[str] = None,
    related_capability: Optional[str] = None,
    risk_level: str = "low",
    requires_operator_approval: bool = True,
    existing_records: Optional[List[Dict[str, Any]]] = None,
    now: Optional[float] = None,
) -> dict:
    """Build a complete experiment_proposal_v1 record.

    Args:
        type: search_insight | physical_action | simulation_run | self_improvement_suggestion
        title: Short descriptive title
        description: Full description of the proposed experiment
        params: Dict of experiment parameters
        confidence: 0.0-1.0
        confidence_reasons: List of strings explaining confidence score
        source: Source identifier
        source_refs: List of source references
        timeline_id: Optional timeline reference
        related_capability: Optional capability ID
        risk_level: low | medium | high | critical
        requires_operator_approval: Bool; overridden to True for physical_action and self_improvement
        existing_records: Existing proposals for ID counter
        now: Unix timestamp for date/ID

    Returns:
        dict proposal record
    """
    if source_refs is None:
        source_refs = []
    if now is None:
        now = _time.time()

    # Enforce approval for type-specific rules
    if type == "physical_action":
        requires_operator_approval = True
    if type == "self_improvement_suggestion":
        requires_operator_approval = True

    proposal_id = generate_experiment_proposal_id(existing_records, now)
    created_at = _time.strftime("%Y-%m-%dT%H:%M:%SZ", _time.gmtime(now))

    return {
        "record_type": "experiment_proposal_v1",
        "proposal_id": proposal_id,
        "created_at": created_at,
        "type": type,
        "title": title,
        "description": description,
        "params": params,
        "confidence": confidence,
        "confidence_reasons": confidence_reasons,
        "source": source,
        "source_refs": source_refs,
        "requires_operator_approval": requires_operator_approval,
        "operator_approval_required": requires_operator_approval,
        "execution_status": "pending",
        "result_summary": None,
        "result_refs": [],
        "timeline_id": timeline_id,
        "related_capability": related_capability,
        "risk_level": risk_level,
        "authority": "experiment_proposal_only",
        "automatic_execution": False,
        "hidden_learning": False,
        "raw_prompt_stored": False,
    }
