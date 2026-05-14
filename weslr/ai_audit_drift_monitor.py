"""WESLR AI audit drift monitor helpers V1.

Static, in-memory helpers for detecting governance drift in supplied AI-audit
text or caller-provided file snapshots. This module does not walk the filesystem,
write files, execute probes, call models, score systems, certify results, or
modify runtime/chat/voice behavior.
"""

from __future__ import annotations

import re
from copy import deepcopy
from hashlib import sha256
from typing import Any


DRIFT_MONITOR_SCHEMA_VERSION = "ai_audit_drift_monitor_result_v1"
DRIFT_SIGNAL_SCHEMA_VERSION = "ai_audit_drift_signal_v1"
DRIFT_SUMMARY_SCHEMA_VERSION = "ai_audit_drift_boundary_summary_v1"
NON_EXECUTING_SIGNAL_STATUS = "non_executing_drift_signal_only"
NON_EXECUTING_SUMMARY_STATUS = "non_executing_summary_only"
NON_EXECUTING_MONITOR_STATUS = "non_executing_drift_monitor_only"
SEVERITIES = {"info", "low", "medium", "high"}

FORBIDDEN_RESULT_FIELDS = {
    "answer",
    "answers",
    "answer_key",
    "answer_keys",
    "model_output",
    "model_outputs",
    "score",
    "scores",
    "official_score",
    "official_scores",
    "clinical_score",
    "iq_score",
    "benchmark_score",
    "internal_audit_score",
    "certification",
    "certified",
    "official_benchmark_result",
    "protected_test_item",
    "protected_prompt",
    "hidden_prompt",
}

FORBIDDEN_TRUE_MARKERS = {
    "executable",
    "runnable",
    "runner_created",
    "execution_allowed",
    "scoring_engine",
    "automated_grading",
    "answer_evaluation",
    "external_model_calls",
    "external_testing_authorized",
    "model_calls_authorized",
    "runtime_authorized",
    "runtime_behavior_change",
    "runtime_behavior_changed",
    "persistence_authorized",
    "report_persistence",
    "automatic_approval",
    "auto_approval",
    "automatic_truth_promotion",
    "truth_promotion",
    "protected_item_present",
    "answer_key_present",
    "hidden_prompt_present",
    "official_score_claimed",
    "certification_claimed",
    "official_benchmark_claimed",
}

SAFE_NEXT_STEPS = [
    "review_drift_signals",
    "keep_ai_audit_static_and_non_executing",
    "remove_or_reword_unsafe_claim_language",
    "require_separate_operator_approval_for_any_execution_design",
]

FORBIDDEN_NEXT_STEPS = [
    "create_probe_runner",
    "call_external_models",
    "probe_live_ai_systems",
    "add_scoring_engine",
    "claim_certification",
    "claim_official_benchmark_result",
    "write_weslr_runtime_state",
    "change_runtime_chat_voice_behavior",
    "auto_promote_findings_to_truth",
]

# Conservative phrase-pattern warnings. These are transparent heuristics, not
# proof of unsafe behavior.
DRIFT_PATTERNS: tuple[dict[str, str], ...] = (
    {"signal_type": "runner_drift", "severity": "high", "pattern": r"\b(?:runner|run(?:s|ning)? probes?|execute(?:s|d|ing)? probes?|live probing|probe execution)\b", "explanation": "Text appears to move AI audit toward runner/probe execution behavior."},
    {"signal_type": "scoring_drift", "severity": "high", "pattern": r"\b(?:scoring engine|automated grading|pass/fail grading|answer evaluation engine|grade answers?)\b", "explanation": "Text appears to introduce scoring, grading, or answer evaluation."},
    {"signal_type": "scoring_drift", "severity": "medium", "pattern": r"\b(?:official score|iq score|clinical score|benchmark score)\b", "explanation": "Text references score language that may blur non-official boundaries."},
    {"signal_type": "certification_claim_drift", "severity": "high", "pattern": r"\b(?:certified|certification|certify)\b", "explanation": "Text references certification-style claims."},
    {"signal_type": "official_benchmark_claim_drift", "severity": "high", "pattern": r"\b(?:official benchmark result|leaderboard score|benchmark result)\b", "explanation": "Text references official/benchmark-result style claims."},
    {"signal_type": "runtime_wiring_drift", "severity": "high", "pattern": r"\b(?:runtime integration|chat integration|voice integration|tts integration|stt integration|runtime wiring|chat wiring|voice wiring)\b", "explanation": "Text appears to wire AI audit into runtime/chat/voice behavior."},
    {"signal_type": "model_call_drift", "severity": "high", "pattern": r"\b(?:(?:openai|openrouter|ollama|external model) (?:call|probe|test|audit|execution)|call (?:openai|openrouter|ollama|external models?))\b", "explanation": "Text appears to connect AI audit execution to external model calls."},
    {"signal_type": "hidden_prompt_drift", "severity": "high", "pattern": r"\bhidden[_ -]?prompt(?:s)?\b", "explanation": "Text references hidden prompts."},
    {"signal_type": "answer_key_drift", "severity": "high", "pattern": r"\banswer[_ -]?key(?:s)?\b", "explanation": "Text references answer keys."},
    {"signal_type": "protected_item_drift", "severity": "high", "pattern": r"\b(?:protected test item|protected item|protected material)\b", "explanation": "Text references protected test material."},
    {"signal_type": "auto_approval_drift", "severity": "high", "pattern": r"\b(?:auto approve|auto-approve|automatic approval|automatically approve)\b", "explanation": "Text appears to bypass operator approval."},
    {"signal_type": "truth_promotion_drift", "severity": "high", "pattern": r"\b(?:promote to truth|truth promotion|auto promote|auto-promote|automatically promote)\b", "explanation": "Text appears to promote observations to truth automatically."},
    {"signal_type": "persistence_drift", "severity": "medium", "pattern": r"\b(?:write to \.weslr|persist audit result|persist(?:s|ed|ing)? reports?|report persistence|\.weslr persistence)\b", "explanation": "Text references persistence that is outside this helper-only phase."},
    {"signal_type": "unsafe_language_drift", "severity": "medium", "pattern": r"\b(?:public superiority claim|superior to humans|clinically valid|psychometric validity)\b", "explanation": "Text uses public superiority, clinical, or psychometric claim language."},
)


def _stable_id(prefix: str, *parts: str) -> str:
    return prefix + sha256("|".join(str(part) for part in parts).encode("utf-8")).hexdigest()[:12]


def _signal(*, signal_type: str, severity: str, source_ref: str, matched_pattern: str, explanation: str, recommended_next_action: str) -> dict[str, Any]:
    return {
        "schema_version": DRIFT_SIGNAL_SCHEMA_VERSION,
        "signal_id": _stable_id("weslr_ai_audit_drift_signal_v1_", signal_type, source_ref, matched_pattern, explanation),
        "signal_type": signal_type,
        "severity": severity if severity in SEVERITIES else "info",
        "source_ref": source_ref,
        "matched_pattern": matched_pattern,
        "explanation": explanation,
        "recommended_next_action": recommended_next_action,
        "execution_status": NON_EXECUTING_SIGNAL_STATUS,
        "warning_only": True,
        "not_a_score": True,
        "automatic_fix": False,
        "runtime_behavior_change": False,
    }


def scan_ai_audit_text_for_drift_v1(text: str, source_ref: str | None = None) -> list[dict[str, Any]]:
    """Scan provided text only for conservative AI-audit drift signals."""
    source = source_ref or "provided_text"
    content = str(text or "")
    signals: list[dict[str, Any]] = []
    for spec in DRIFT_PATTERNS:
        pattern = spec["pattern"]
        if re.search(pattern, content, flags=re.IGNORECASE):
            signals.append(
                _signal(
                    signal_type=spec["signal_type"],
                    severity=spec["severity"],
                    source_ref=source,
                    matched_pattern=pattern,
                    explanation=spec["explanation"],
                    recommended_next_action="review_and_preserve_non_executing_ai_audit_boundaries",
                )
            )
    return sorted(signals, key=lambda item: (item["source_ref"], item["signal_type"], item["signal_id"]))


def scan_ai_audit_file_snapshot_for_drift_v1(file_snapshots: list[dict[str, Any]] | tuple[dict[str, Any], ...] | None) -> dict[str, Any]:
    """Scan only caller-provided in-memory file snapshots; never walk files."""
    snapshots = deepcopy(list(file_snapshots or []))
    by_path: dict[str, list[dict[str, Any]]] = {}
    all_signals: list[dict[str, Any]] = []
    for index, snapshot in enumerate(snapshots):
        path = str(snapshot.get("path") or snapshot.get("source_ref") or f"snapshot[{index}]")
        content = str(snapshot.get("content", ""))
        signals = scan_ai_audit_text_for_drift_v1(content, source_ref=path)
        by_path[path] = signals
        all_signals.extend(signals)
    return {
        "schema_version": "ai_audit_drift_file_snapshot_scan_v1",
        "redacted_count_only": True,
        "in_memory_only": True,
        "execution_status": NON_EXECUTING_MONITOR_STATUS,
        "snapshot_count": len(snapshots),
        "signal_count": len(all_signals),
        "signals_by_source_ref": dict(sorted(by_path.items())),
        "signals": sorted(all_signals, key=lambda item: (item["source_ref"], item["signal_type"], item["signal_id"])),
        "filesystem_walk_performed": False,
        "files_written": False,
    }


def _count(values: list[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for value in values:
        counts[value] = counts.get(value, 0) + 1
    return dict(sorted(counts.items()))


def summarize_ai_audit_drift_boundaries_v1(signals: list[dict[str, Any]] | tuple[dict[str, Any], ...] | None) -> dict[str, Any]:
    """Summarize drift signals as warnings, not scores or certification."""
    signal_items = deepcopy(list(signals or []))
    severities = [str(signal.get("severity", "info")) for signal in signal_items]
    severity_rank = {"info": 0, "low": 1, "medium": 2, "high": 3}
    highest = "none" if not severities else max(severities, key=lambda severity: severity_rank.get(severity, 0))
    return {
        "schema_version": DRIFT_SUMMARY_SCHEMA_VERSION,
        "redacted_count_only": True,
        "in_memory_only": True,
        "execution_status": NON_EXECUTING_SUMMARY_STATUS,
        "total_signals": len(signal_items),
        "counts_by_severity": _count(severities),
        "counts_by_signal_type": _count([str(signal.get("signal_type", "unknown")) for signal in signal_items]),
        "highest_severity": highest,
        "drift_status": "no_drift_signals" if not signal_items else "drift_warnings_present",
        "safe_next_steps": list(SAFE_NEXT_STEPS),
        "forbidden_next_steps": list(FORBIDDEN_NEXT_STEPS),
        "not_a_score": True,
        "not_certification": True,
        "not_benchmark_result": True,
    }


def build_ai_audit_drift_monitor_result_v1(
    *,
    file_snapshots: list[dict[str, Any]] | tuple[dict[str, Any], ...] | None = None,
    texts: list[str | dict[str, Any]] | tuple[str | dict[str, Any], ...] | None = None,
) -> dict[str, Any]:
    """Build a deterministic, in-memory AI audit drift monitor result."""
    text_items = deepcopy(list(texts or []))
    all_signals: list[dict[str, Any]] = []
    text_results: list[dict[str, Any]] = []
    for index, item in enumerate(text_items):
        if isinstance(item, dict):
            source_ref = str(item.get("source_ref") or item.get("path") or f"text[{index}]")
            content = str(item.get("text") or item.get("content") or "")
        else:
            source_ref = f"text[{index}]"
            content = str(item)
        signals = scan_ai_audit_text_for_drift_v1(content, source_ref=source_ref)
        text_results.append({"source_ref": source_ref, "signal_count": len(signals), "signals": signals})
        all_signals.extend(signals)

    file_scan = scan_ai_audit_file_snapshot_for_drift_v1(file_snapshots)
    all_signals.extend(file_scan["signals"])
    all_signals = sorted(all_signals, key=lambda item: (item["source_ref"], item["signal_type"], item["signal_id"]))
    summary = summarize_ai_audit_drift_boundaries_v1(all_signals)
    result = {
        "schema_version": DRIFT_MONITOR_SCHEMA_VERSION,
        "monitor_id": _stable_id("weslr_ai_audit_drift_monitor_v1_", str(len(all_signals)), *[signal["signal_id"] for signal in all_signals]),
        "redacted_count_only": True,
        "in_memory_only": True,
        "execution_status": NON_EXECUTING_MONITOR_STATUS,
        "signals": all_signals,
        "signal_count": len(all_signals),
        "text_scan_results": text_results,
        "file_snapshot_scan": file_scan,
        "boundary_summary": summary,
        "not_a_runner": True,
        "not_a_scoring_engine": True,
        "not_a_certification": True,
        "not_a_benchmark_result": True,
        "not_truth_promotion": True,
        "no_model_calls": True,
        "no_runtime_behavior_change": True,
        "no_persistence": True,
        "filesystem_walk_performed": False,
        "files_written": False,
    }
    result["validation_status"] = validate_ai_audit_drift_monitor_result_v1(result)
    return result


def _find_forbidden(value: Any, path: str = "drift_monitor") -> list[str]:
    issues: list[str] = []
    if isinstance(value, dict):
        for key, nested in value.items():
            key_text = str(key)
            nested_path = f"{path}.{key_text}"
            if key_text in FORBIDDEN_RESULT_FIELDS:
                issues.append(f"forbidden drift monitor field: {nested_path}")
            if key_text in FORBIDDEN_TRUE_MARKERS and nested is True:
                issues.append(f"forbidden drift monitor true marker: {nested_path}")
            issues.extend(_find_forbidden(nested, nested_path))
    elif isinstance(value, list):
        for index, nested in enumerate(value):
            issues.extend(_find_forbidden(nested, f"{path}[{index}]"))
    return issues


def validate_ai_audit_drift_monitor_result_v1(result: dict[str, Any]) -> dict[str, Any]:
    """Validate drift monitor result boundaries without execution or persistence."""
    issues: list[str] = []
    if not isinstance(result, dict):
        return {"valid": False, "redacted_count_only": True, "issues": ["drift monitor result must be a dict"]}
    if result.get("schema_version") != DRIFT_MONITOR_SCHEMA_VERSION:
        issues.append("invalid schema_version")
    if result.get("redacted_count_only") is not True:
        issues.append("drift monitor must be redacted/count-only")
    if result.get("in_memory_only") is not True:
        issues.append("drift monitor must be in-memory only")
    if result.get("execution_status") != NON_EXECUTING_MONITOR_STATUS:
        issues.append("drift monitor execution_status must be non_executing_drift_monitor_only")
    for marker in ("not_a_runner", "not_a_scoring_engine", "not_a_certification", "not_a_benchmark_result", "not_truth_promotion", "no_model_calls", "no_runtime_behavior_change", "no_persistence"):
        if result.get(marker) is not True:
            issues.append(f"drift monitor must be marked {marker}")
    if result.get("filesystem_walk_performed") is not False:
        issues.append("filesystem_walk_performed must be False")
    if result.get("files_written") is not False:
        issues.append("files_written must be False")
    for signal in result.get("signals", []) or []:
        if signal.get("execution_status") != NON_EXECUTING_SIGNAL_STATUS:
            issues.append(f"signal must be non-executing: {signal.get('signal_id', '')}")
        if signal.get("severity") not in SEVERITIES:
            issues.append(f"invalid signal severity: {signal.get('signal_id', '')}")
        if signal.get("warning_only") is not True:
            issues.append(f"signal must be warning_only: {signal.get('signal_id', '')}")
        if signal.get("not_a_score") is not True:
            issues.append(f"signal must be not_a_score: {signal.get('signal_id', '')}")
        if signal.get("automatic_fix") is not False:
            issues.append(f"signal automatic_fix must be False: {signal.get('signal_id', '')}")
        if signal.get("runtime_behavior_change") is not False:
            issues.append(f"signal runtime_behavior_change must be False: {signal.get('signal_id', '')}")
    issues.extend(_find_forbidden(result))
    return {
        "valid": not issues,
        "redacted_count_only": True,
        "issues": issues,
        "signal_count": len(result.get("signals", []) or []),
        "execution_authorized": False,
        "runner_authorized": False,
        "scoring_authorized": False,
        "external_testing_authorized": False,
        "model_calls_made": False,
        "report_persisted": False,
        "runtime_behavior_changed": False,
        "protected_items_copied": False,
        "answer_keys_used": False,
        "hidden_prompts_used": False,
        "official_score_claimed": False,
        "certification_claimed": False,
        "official_benchmark_claimed": False,
    }
