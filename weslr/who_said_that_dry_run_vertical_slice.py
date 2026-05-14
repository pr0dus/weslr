"""WESLR Who Said That Dry-Run Vertical Slice V1.

In-memory helper-only dry-run slice for who-said-that attribution flow. This
module does not modify chat responders, implement live runtime routing, touch
voice gateway/ambient/TTS/STT, read or write attribution logs, write queues,
mutate memory/config/runtime, call models/advisors, select benchmark answers,
or claim truth/soundness/official scores.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from weslr.who_said_that_chat_routing import simulate_who_said_that_chat_integration_from_metadata
from weslr.who_said_that_query_surface import create_who_said_that_query_intent_from_text_metadata, resolve_who_said_that_from_provided_records
from weslr.who_said_that_runtime_query import (
    create_missing_runtime_query_result,
    create_runtime_query_request_from_metadata,
    create_runtime_query_result_from_answer,
)


@dataclass
class WhoSaidThatDryRunResult:
    schema_version: str = "1.0"
    dry_run_id: str = ""
    input_channel: str = "unknown"
    message_hash: str = ""
    phrase_family: str = "unknown"
    should_route: bool = False
    fallthrough: bool = False
    runtime_query_created: bool = False
    answer_created: bool = False
    answer_id: str = ""
    ownership_category: str = "unknown_unattributed"
    attribution_found: bool = False
    attribution_partial: bool = False
    llm_assisted: bool = False
    model_provider: str = ""
    model_name: str = ""
    missing_attribution_reason: str = ""
    redacted_summary: str = ""
    runtime_integration_performed: bool = False
    log_read_performed: bool = False
    log_write_performed: bool = False
    queue_write_performed: bool = False
    memory_mutation_performed: bool = False
    external_model_call_performed: bool = False
    answer_selection_performed: bool = False
    truth_claim_made: bool = False
    official_score_claimed: bool = False


def _safe_result(**overrides: Any) -> WhoSaidThatDryRunResult:
    item = WhoSaidThatDryRunResult()
    for key, value in overrides.items():
        if not hasattr(item, key):
            raise ValueError(f"unknown who-said-that dry-run result field: {key}")
        setattr(item, key, value)
    return item


def run_who_said_that_dry_run_vertical_slice(
    dry_run_id: str,
    input_channel: str,
    message_hash: str,
    transient_phrase: str = "",
    confidence: str = "high",
    attribution_records: list[Any] | None = None,
    log_events: list[Any] | None = None,
    requested_trace_ref: str = "",
    requested_utterance_id: str = "",
    **metadata: Any,
) -> WhoSaidThatDryRunResult:
    """Run an in-memory dry-run vertical slice using provided records only."""
    if "raw_text" in metadata or "message_text" in metadata or "raw_message_text" in metadata:
        raise ValueError("raw text metadata is not accepted")

    integration = simulate_who_said_that_chat_integration_from_metadata(
        integration_result_id=f"{dry_run_id}:integration",
        request_id=f"{dry_run_id}:chat_request",
        input_channel=input_channel,
        message_text_hash=message_hash,
        confidence=confidence,
        transient_phrase=transient_phrase,
        runtime_query_request_id=f"{dry_run_id}:runtime_request",
    )
    decision = integration["chat_routing_decision"]
    phrase_family = str(decision.get("matched_phrase_family", "unknown"))
    should_route = bool(decision.get("should_route", False))

    if not should_route:
        return _safe_result(
            dry_run_id=dry_run_id,
            input_channel=input_channel,
            message_hash=message_hash,
            phrase_family=phrase_family,
            should_route=False,
            fallthrough=True,
            runtime_query_created=False,
            answer_created=False,
            missing_attribution_reason="fallthrough to normal chat; no clear attribution intent",
            redacted_summary="Dry-run fallthrough: no clear attribution intent; no runtime action performed.",
        )

    intent_type = str(decision.get("detected_attribution_intent", "who_said_that"))
    lookup_mode = "most_recent"
    if requested_utterance_id:
        lookup_mode = "by_utterance_id"
    elif requested_trace_ref:
        lookup_mode = "by_trace_ref"

    runtime_request = create_runtime_query_request_from_metadata(
        request_id=f"{dry_run_id}:runtime_request",
        input_channel=input_channel,
        query_text_hash=requested_trace_ref or message_hash,
        detected_intent_type=intent_type,
        lookup_mode=lookup_mode,
        requested_utterance_id=requested_utterance_id,
        requested_trace_ref=requested_trace_ref,
        routing_allowed=False,
    )
    query_intent = create_who_said_that_query_intent_from_text_metadata(
        query_id=runtime_request.request_id,
        intent_type=runtime_request.detected_intent_type,
        query_text_hash=runtime_request.requested_trace_ref or runtime_request.query_text_hash,
        input_channel=runtime_request.input_channel,
        requested_utterance_id=runtime_request.requested_utterance_id,
        lookback_mode=runtime_request.lookup_mode,
    )
    answer = resolve_who_said_that_from_provided_records(
        query_intent,
        attribution_records=attribution_records or [],
        log_events=log_events or [],
        requested_trace_ref=requested_trace_ref,
        answer_id=f"{dry_run_id}:answer",
    )
    create_runtime_query_result_from_answer(runtime_request, answer, result_id=f"{dry_run_id}:runtime_result")
    if not answer.attribution_found:
        create_missing_runtime_query_result(runtime_request, result_id=f"{dry_run_id}:runtime_missing_result")

    return _safe_result(
        dry_run_id=dry_run_id,
        input_channel=input_channel,
        message_hash=message_hash,
        phrase_family=phrase_family,
        should_route=True,
        fallthrough=False,
        runtime_query_created=True,
        answer_created=True,
        answer_id=answer.answer_id,
        ownership_category=answer.ownership_category,
        attribution_found=answer.attribution_found,
        attribution_partial=answer.attribution_partial,
        llm_assisted=answer.llm_assisted,
        model_provider=answer.model_provider,
        model_name=answer.model_name,
        missing_attribution_reason=answer.missing_attribution_reason,
        redacted_summary="Dry-run who-said-that answer created from provided in-memory attribution records only.",
    )


def summarize_who_said_that_dry_run_result(item: WhoSaidThatDryRunResult) -> dict[str, Any]:
    """Return a redacted/count-only summary for one dry-run result."""
    return {
        "schema_version": item.schema_version,
        "has_dry_run_id": bool(item.dry_run_id),
        "input_channel": item.input_channel,
        "phrase_family": item.phrase_family,
        "should_route": item.should_route,
        "fallthrough": item.fallthrough,
        "runtime_query_created": item.runtime_query_created,
        "answer_created": item.answer_created,
        "has_answer_id": bool(item.answer_id),
        "ownership_category": item.ownership_category,
        "attribution_found": item.attribution_found,
        "attribution_partial": item.attribution_partial,
        "llm_assisted": item.llm_assisted,
        "model_provider_present": bool(item.model_provider),
        "model_name_present": bool(item.model_name),
        "missing_attribution": bool(item.missing_attribution_reason),
        "runtime_integration_performed": item.runtime_integration_performed,
        "log_read_performed": item.log_read_performed,
        "log_write_performed": item.log_write_performed,
        "queue_write_performed": item.queue_write_performed,
        "memory_mutation_performed": item.memory_mutation_performed,
        "external_model_call_performed": item.external_model_call_performed,
        "answer_selection_performed": item.answer_selection_performed,
        "truth_claim_made": item.truth_claim_made,
        "official_score_claimed": item.official_score_claimed,
        "summary_mode": "redacted_count_only",
    }


def summarize_who_said_that_dry_run_results(items: list[WhoSaidThatDryRunResult]) -> dict[str, Any]:
    """Return redacted aggregate counts for dry-run results."""
    by_phrase_family: dict[str, int] = {}
    by_ownership_category: dict[str, int] = {}
    for item in items:
        by_phrase_family[item.phrase_family] = by_phrase_family.get(item.phrase_family, 0) + 1
        by_ownership_category[item.ownership_category] = by_ownership_category.get(item.ownership_category, 0) + 1
    return {
        "result_count": len(items),
        "route_count": sum(1 for item in items if item.should_route),
        "fallthrough_count": sum(1 for item in items if item.fallthrough),
        "runtime_query_created_count": sum(1 for item in items if item.runtime_query_created),
        "answer_created_count": sum(1 for item in items if item.answer_created),
        "attribution_found_count": sum(1 for item in items if item.attribution_found),
        "missing_attribution_count": sum(1 for item in items if not item.attribution_found),
        "llm_assisted_count": sum(1 for item in items if item.llm_assisted),
        "by_phrase_family": by_phrase_family,
        "by_ownership_category": by_ownership_category,
        "runtime_integration_performed": False,
        "log_reads_performed": False,
        "log_writes_performed": False,
        "queue_writes_performed": False,
        "memory_mutations_performed": False,
        "external_model_calls_performed": False,
        "answer_selection_performed": False,
        "truth_claims_made": False,
        "official_scores_claimed": False,
        "summary_mode": "redacted_count_only",
    }


def who_said_that_dry_run_result_to_dict(item: WhoSaidThatDryRunResult) -> dict[str, Any]:
    return asdict(item)
