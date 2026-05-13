"""WESLR Advisor Review Queue Operator CLI Schema V1.

Dataclasses and pure validation helpers for future operator-facing advisor-review
queue CLI requests/results. This module is schema-only: it does not implement CLI
commands, read or write queue files, call external models or advisor providers,
activate providers, mutate prompts, change runtime/config, schedule daemons, select
answers, or claim truth, soundness, or official scores.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any
import re


ALLOWED_CLI_COMMANDS = {"list", "show", "summary", "filter", "decide", "archive", "export", "unknown"}
ALLOWED_OPERATOR_DECISIONS = {"accepted", "rejected", "deferred", "archived"}
SENSITIVE_TEXT_PATTERNS = {
    "possible API key": re.compile(r"api[_ -]?key|sk-[A-Za-z0-9]|AIza[0-9A-Za-z_-]", re.IGNORECASE),
    "possible token": re.compile(r"\btoken\b|token[_ -]?[A-Za-z0-9_-]*|bearer\s+[A-Za-z0-9._-]+", re.IGNORECASE),
    "possible secret": re.compile(r"\bsecret\b|secret[_ -]?[A-Za-z0-9_-]*|password\s*[:=]", re.IGNORECASE),
    "possible raw benchmark text": re.compile(r"raw benchmark|benchmark text|question stem|passage:", re.IGNORECASE),
    "possible answer key": re.compile(r"answer[_ -]?key|official solution|correct answer", re.IGNORECASE),
    "possible private user data": re.compile(r"private user data|ssn|social security|passport", re.IGNORECASE),
}


@dataclass
class AdvisorQueueCLIRequest:
    schema_version: str = "1.0"
    request_id: str = ""
    command: str = "unknown"
    item_id: str = ""
    filter_status: str = ""
    filter_type: str = ""
    filter_risk: str = ""
    operator_decision: str = ""
    export_redacted: bool = True
    limit: int = 50
    dry_run: bool = True
    requires_operator_approval: bool = True
    allow_queue_write: bool = False
    allow_external_model_call: bool = False
    allow_runtime_change: bool = False


@dataclass
class AdvisorQueueCLIResult:
    schema_version: str = "1.0"
    request_id: str = ""
    command: str = "unknown"
    success: bool = False
    redacted: bool = True
    item_count: int = 0
    status_counts: dict[str, int] = field(default_factory=dict)
    risk_counts: dict[str, int] = field(default_factory=dict)
    messages: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    queue_file_read: bool = False
    queue_file_written: bool = False
    external_model_call_made: bool = False
    runtime_change_made: bool = False
    answer_selection_made: bool = False
    truth_claim_made: bool = False
    official_score_claimed: bool = False


def create_empty_cli_request(**overrides: Any) -> AdvisorQueueCLIRequest:
    request = AdvisorQueueCLIRequest()
    for key, value in overrides.items():
        if not hasattr(request, key):
            raise ValueError(f"unknown CLI request field: {key}")
        setattr(request, key, value)
    return request


def create_empty_cli_result(**overrides: Any) -> AdvisorQueueCLIResult:
    result = AdvisorQueueCLIResult()
    for key, value in overrides.items():
        if not hasattr(result, key):
            raise ValueError(f"unknown CLI result field: {key}")
        setattr(result, key, value)
    return result


def cli_request_to_dict(request: AdvisorQueueCLIRequest) -> dict[str, Any]:
    return asdict(request)


def cli_request_from_dict(data: dict[str, Any]) -> AdvisorQueueCLIRequest:
    return AdvisorQueueCLIRequest(**dict(data))


def cli_result_to_dict(result: AdvisorQueueCLIResult) -> dict[str, Any]:
    return asdict(result)


def cli_result_from_dict(data: dict[str, Any]) -> AdvisorQueueCLIResult:
    return AdvisorQueueCLIResult(**dict(data))


def _string_values(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        values: list[str] = []
        for key, nested in value.items():
            values.extend(_string_values(key))
            values.extend(_string_values(nested))
        return values
    if isinstance(value, (list, tuple, set)):
        values: list[str] = []
        for nested in value:
            values.extend(_string_values(nested))
        return values
    return []


def _detect_sensitive_text(values: list[str]) -> list[str]:
    joined = "\n".join(values)
    findings: list[str] = []
    for label, pattern in SENSITIVE_TEXT_PATTERNS.items():
        if pattern.search(joined):
            findings.append(label)
    return findings


def validate_cli_request(request: AdvisorQueueCLIRequest) -> list[str]:
    errors: list[str] = []
    if not request.request_id.strip():
        errors.append("missing request id")
    if request.command not in ALLOWED_CLI_COMMANDS:
        errors.append("invalid command")
    if not isinstance(request.limit, int) or request.limit < 1 or request.limit > 1000:
        errors.append("invalid limit")
    if request.export_redacted is False:
        errors.append("export_redacted must remain true")
    if request.dry_run is False:
        errors.append("dry_run must remain true in schema-only phase")
    if request.requires_operator_approval is False:
        errors.append("requires_operator_approval must remain true")
    if request.allow_queue_write:
        errors.append("allow_queue_write must remain false")
    if request.allow_external_model_call:
        errors.append("allow_external_model_call must remain false")
    if request.allow_runtime_change:
        errors.append("allow_runtime_change must remain false")
    if request.command == "decide" and not request.item_id.strip():
        errors.append("decide command requires item_id")
    if request.command == "decide" and not request.operator_decision.strip():
        errors.append("decide command requires operator_decision")
    if request.command in {"archive", "show"} and not request.item_id.strip():
        errors.append(f"{request.command} command requires item_id")
    for finding in _detect_sensitive_text(_string_values(asdict(request))):
        errors.append(finding)
    return errors


def validate_cli_result(result: AdvisorQueueCLIResult) -> list[str]:
    errors: list[str] = []
    if result.command not in ALLOWED_CLI_COMMANDS:
        errors.append("invalid command")
    if result.item_count < 0:
        errors.append("invalid item_count")
    if result.redacted is False:
        errors.append("result must remain redacted")
    if result.queue_file_written:
        errors.append("queue_file_written must remain false")
    if result.external_model_call_made:
        errors.append("external_model_call_made must remain false")
    if result.runtime_change_made:
        errors.append("runtime_change_made must remain false")
    if result.answer_selection_made:
        errors.append("answer_selection_made must remain false")
    if result.truth_claim_made:
        errors.append("truth_claim_made must remain false")
    if result.official_score_claimed:
        errors.append("official_score_claimed must remain false")
    sensitive_values = _string_values(result.messages) + _string_values(result.errors) + _string_values(result.status_counts) + _string_values(result.risk_counts)
    for finding in _detect_sensitive_text(sensitive_values):
        errors.append(finding)
    return errors


def summarize_cli_result(result: AdvisorQueueCLIResult) -> dict[str, Any]:
    return {
        "schema_version": result.schema_version,
        "request_id": result.request_id,
        "command": result.command,
        "success": result.success,
        "redacted": True,
        "summary_mode": "redacted_count_only",
        "item_count": result.item_count,
        "status_count_total": sum(result.status_counts.values()),
        "risk_count_total": sum(result.risk_counts.values()),
        "message_count": len(result.messages),
        "error_count": len(result.errors),
        "queue_file_read": result.queue_file_read,
        "queue_file_written": result.queue_file_written,
        "external_model_call_made": result.external_model_call_made,
        "runtime_change_made": result.runtime_change_made,
        "answer_selection_made": result.answer_selection_made,
        "truth_claim_made": result.truth_claim_made,
        "official_score_claimed": result.official_score_claimed,
    }


def validate_operator_decision_for_cli(operator_decision: str) -> list[str]:
    if not operator_decision.strip():
        return ["missing operator_decision"]
    if operator_decision not in ALLOWED_OPERATOR_DECISIONS:
        return ["invalid operator_decision"]
    return []


def _raise_if_errors(errors: list[str]) -> None:
    if errors:
        raise ValueError("; ".join(errors))


def create_cli_request_from_operator_intent(
    command: str,
    request_id: str,
    item_id: str = "",
    filter_status: str = "",
    filter_type: str = "",
    filter_risk: str = "",
    operator_decision: str = "",
    limit: int = 50,
    dry_run: bool = True,
    export_redacted: bool = True,
    requires_operator_approval: bool = True,
    allow_queue_write: bool = False,
    allow_external_model_call: bool = False,
    allow_runtime_change: bool = False,
) -> AdvisorQueueCLIRequest:
    """Create and validate a CLI request object without executing anything."""
    request = create_empty_cli_request(
        request_id=request_id,
        command=command,
        item_id=item_id,
        filter_status=filter_status,
        filter_type=filter_type,
        filter_risk=filter_risk,
        operator_decision=operator_decision,
        export_redacted=export_redacted,
        limit=limit,
        dry_run=dry_run,
        requires_operator_approval=requires_operator_approval,
        allow_queue_write=allow_queue_write,
        allow_external_model_call=allow_external_model_call,
        allow_runtime_change=allow_runtime_change,
    )
    errors = validate_cli_request(request)
    if command == "decide" and operator_decision:
        errors.extend(validate_operator_decision_for_cli(operator_decision))
    _raise_if_errors(errors)
    return request


def create_cli_result_for_request(
    request: AdvisorQueueCLIRequest,
    success: bool = False,
    item_count: int = 0,
    status_counts: dict[str, int] | None = None,
    risk_counts: dict[str, int] | None = None,
    messages: list[str] | None = None,
    errors: list[str] | None = None,
) -> AdvisorQueueCLIResult:
    """Create a redacted result object for a validated request without executing it."""
    _raise_if_errors(validate_cli_request(request))
    result = create_empty_cli_result(
        request_id=request.request_id,
        command=request.command,
        success=success,
        redacted=True,
        item_count=item_count,
        status_counts=dict(status_counts or {}),
        risk_counts=dict(risk_counts or {}),
        messages=list(messages or []),
        errors=list(errors or []),
        queue_file_read=False,
        queue_file_written=False,
        external_model_call_made=False,
        runtime_change_made=False,
        answer_selection_made=False,
        truth_claim_made=False,
        official_score_claimed=False,
    )
    _raise_if_errors(validate_cli_result(result))
    return result


def summarize_cli_requests(requests: list[AdvisorQueueCLIRequest]) -> dict[str, Any]:
    command_counts: dict[str, int] = {}
    dry_run_counts = {"true": 0, "false": 0}
    unsafe_request_count = 0
    validation_error_count = 0
    for request in requests:
        command_counts[request.command] = command_counts.get(request.command, 0) + 1
        dry_run_counts["true" if request.dry_run else "false"] += 1
        errors = validate_cli_request(request)
        if errors:
            unsafe_request_count += 1
            validation_error_count += len(errors)
    return {
        "redacted": True,
        "summary_mode": "redacted_count_only",
        "request_count": len(requests),
        "command_counts": command_counts,
        "dry_run_counts": dry_run_counts,
        "unsafe_request_count": unsafe_request_count,
        "validation_error_count": validation_error_count,
        "queue_file_read": False,
        "queue_file_written": False,
        "external_model_call_made": False,
        "runtime_change_made": False,
        "answer_selection_made": False,
        "truth_claim_made": False,
        "official_score_claimed": False,
    }


def summarize_cli_results(results: list[AdvisorQueueCLIResult]) -> dict[str, Any]:
    command_counts: dict[str, int] = {}
    success_counts = {"true": 0, "false": 0}
    validation_error_count = 0
    item_count_total = 0
    message_count = 0
    error_count = 0
    for result in results:
        command_counts[result.command] = command_counts.get(result.command, 0) + 1
        success_counts["true" if result.success else "false"] += 1
        validation_error_count += len(validate_cli_result(result))
        item_count_total += result.item_count
        message_count += len(result.messages)
        error_count += len(result.errors)
    return {
        "redacted": True,
        "summary_mode": "redacted_count_only",
        "result_count": len(results),
        "command_counts": command_counts,
        "success_counts": success_counts,
        "item_count_total": item_count_total,
        "message_count": message_count,
        "error_count": error_count,
        "validation_error_count": validation_error_count,
        "queue_file_read": False,
        "queue_file_written": False,
        "external_model_call_made": False,
        "runtime_change_made": False,
        "answer_selection_made": False,
        "truth_claim_made": False,
        "official_score_claimed": False,
    }
