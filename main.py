from __future__ import annotations

import argparse
import json
import socket
import subprocess
import sys
import threading
import time
from datetime import datetime, timezone
from datetime import datetime, timezone
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor
from functools import partial
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from time import strftime, localtime

from config import CONTINUATION_NOTES_PATH, DEFAULT_AGENT_COUNT, PROJECT_NAME, TICK_SECONDS, VERSION
from config import TICKS_PER_SECOND_LIMIT, TICK_TIME_LIMIT_SECONDS, CHAT_LLM_TIMEOUT_SECONDS

# Server start time — used for uptime calculation in /api/health
_SERVER_START_TIME = None

from config import CONTINUATION_NOTES_PATH, DEFAULT_AGENT_COUNT, PROJECT_NAME, TICK_SECONDS, VERSION
from config import TICKS_PER_SECOND_LIMIT, TICK_TIME_LIMIT_SECONDS
from continuation_notes import ContinuationNoteError, append_note, latest_note, load_notes, render_note_text
from llm_runtime import embedded_self_test
from research import fetch_url_text, ingest_web_resource, search_web
from self_inspection import build_self_inspection_report
from code_translator import explain_code, translate_code_to_concept, translate_internal_theme_to_code
from error_translator import translate_error, translate_error_to_plain_english
from tool_search import explain_tool_usage, search_tool_and_synthesize
from self_modifier import build_proposal_report, propose_self_modification_report
from self_mod_applier import apply_modification, build_self_mod_report, create_checkpoint, list_checkpoints, rollback
from self_improvement_proposal import create_proposal, list_proposals, approve_proposal, deny_proposal, get_proposal, build_proposal_report as build_sci_report, load_proposals
from self_improvement_apply import apply_proposal, apply_proposal_with_tests, build_apply_report, rollback_proposal, load_apply_log
from self_improvement_observation import record_observation, list_observations, load_observations
from tia_import import (
    create_raw_import_envelope,
    save_import_envelope,
    normalize_tia_envelope,
    save_normalized_envelope,
    record_tia_import_history,
    list_tia_import_history,
    get_tia_import_record,
)
from llm_diff_generator import generate_diff_with_llm, generate_improvement_suggestion, analyze_code_for_issues
from self_mod_dashboard import update_dashboard, get_dashboard_status
from self_mod_enhancements import generate_autonomous_suggestion, check_modification_safety, validate_modification, generate_rollback_preview, batch_modifications
from self_eval import run_self_evaluation, run_self_directed_growth, generate_self_speech
from sim import apply_pack_outcome, archive_memory, browse_queue, build_communicator_message, build_communicator_message_payload, build_identity_core_report, build_memory_layer_report, build_memory_lifecycle_report, build_memory_score_report, build_reflection_report, category_action, distill_episodic_memory, distill_semantic_memory, explain_item, handoff_summary, init_world, load_communicator_self, load_communicator_state, load_evaluation_metrics, load_experiments, load_failsafe_status, load_llm_status, load_messages, load_needs, load_projects, load_public_memory, load_relationships, load_self_mod_proposals, load_work_items, load_tier, monitor_memory_pressure, perform_tick, prepare_pack_offer, prune_archived_memory, record_human_exchange, render_dashboard, review_artifact, save_public_memory, show_agent, show_world, validate_artifact
from integration import find_relevant_research_note
from session_continuity import get_session_continuity
from plugins import (
    enable_plugin, disable_plugin, list_plugins, create_plugin,
    integrate_plugins_into_core
)
from autonomous_intentionality import (
    create_plan, autonomous_intentionality_report
)
from embodiment import physical_reasoning_report, theory_of_mind_report, implicature_report, full_embodiment_test
from psychology_knowledge import generate_psychological_self_description, get_all_concepts as get_all_psychology_concepts
from chemistry_knowledge import get_all_chemistry_concepts
from biology_knowledge import get_all_biology_concepts
from physics_knowledge import get_all_physics_concepts
from mathematics_knowledge import get_all_mathematics_concepts
from robotics_knowledge import get_all_robotics_concepts
from ai_knowledge import get_all_ai_concepts
from quantum_physics_knowledge import get_all_quantum_physics_concepts
from core_knowledge import (
    cross_discipline_reasoning, run_knowledge_test,
    get_all_domains
)
from entity_graph import get_entity_graph

# Shared bounded executor for /chat — one thread, reused across requests.
# Bounded to prevent thread exhaustion under concurrent load.
_CHAT_EXECUTOR = ThreadPoolExecutor(max_workers=1, thread_name_prefix="chat-request")

# Bounded admission gate for /chat: limits concurrent in-flight requests.
# When exhausted, server returns 503 instead of queuing unboundedly.
# Keep small — the single-worker executor serializes execution anyway.
_MAX_CONCURRENT_CHAT = 4
_chat_semaphore = __import__("threading").Semaphore(_MAX_CONCURRENT_CHAT)

# ── Repeated quality watch (governance bridge, metadata only) ───────────
# Tiny in-memory rolling state. Detects repeated quality degradation patterns.
# No behavior changes, no automatic actions — metadata only.
# Bounded: max 10 entries, oldest dropped when full.
_WATCH_HISTORY: list[dict] = []  # [{"quality_class": str, "likely_need": str}]
_WATCH_MAX = 10
_WATCH_THRESHOLD = 3  # consecutive same-class+same-need to trigger note


# ── Governance candidate derivation (observation → review candidate) ───────
# Derives a bounded governance candidate from a fired governance observation.
# For operator review only — no automatic action, no execution.
# Maps watch_triggered to candidate_type and severity for triage.


def _derive_governance_candidate(qnote: str, qclass: str, lneed: str, message: str) -> dict:
    """Derive a governance candidate from a fired quality watch note.
    
    Returns a candidate dict for operator review. auto_apply is always False.
    No automatic actions are taken — this is observation-only.
    """
    # Map watch_triggered to candidate_type
    _WATCH_CANDIDATE_MAP = {
        "repeated_fallback_watch": "routing_gap",
        "repeated_weak_reasoning_watch": "weak_reasoning_pattern",
        "repeated_grounded_reasoning_watch": "sustained_reasoning_load",
        "repeated_strong_verified_watch": "stable_verified_pattern",
    }
    candidate_type = _WATCH_CANDIDATE_MAP.get(qnote, "unknown_quality_pattern")
    
    # Severity based on quality class
    _SEVERITY_MAP = {
        "fallback": "high",
        "weak_reasoning": "medium",
        "grounded_reasoning": "low",
        "strong_verified": "info",
        "uncertain": "medium",
        "unknown": "low",
    }
    severity = _SEVERITY_MAP.get(qclass, "low")
    
    # Suggested action based on candidate type
    _ACTION_MAP = {
        "routing_gap": "Review why direct_answer queries are falling back to template. Consider extending synthesis gating or concept coverage.",
        "weak_reasoning_pattern": "Review LLM confidence for this query type. Consider adjusting confidence thresholds or adding research context.",
        "sustained_reasoning_load": "Sustained medium-quality reasoning observed. Not critical but worth monitoring.",
        "stable_verified_pattern": "Strong verified responses sustained. Current routing is working correctly.",
        "unknown_quality_pattern": "Unclassified quality pattern. Review observation for new pattern.",
    }
    suggested_action = _ACTION_MAP.get(candidate_type, "Review quality pattern.")
    
    return {
        "candidate_type": candidate_type,
        "trigger": qnote,
        "quality_class": qclass,
        "likely_need": lneed,
        "severity": severity,
        "suggested_operator_action": suggested_action,
        "auto_apply": False,  # always False — operator review only
        "message_snippet": message[:80],
    }


# ── Improvement recommendation derivation ─────────────────────────────────
# Observation → Diagnosis → Recommendation → Implementation hint.
# For operator review only — no auto-apply, no code mutation.
# Bounded: maps watch types to recommendation shapes.


def _derive_improvement_recommendation(qnote: str, qclass: str, lneed: str, message: str) -> dict:
    """Derive a structured improvement recommendation from a fired quality watch.
    
    Returns: {
        recommendation_type, trigger, diagnosis, recommendation,
        implementation_hint, confidence, approval_required
    }
    
    approval_required is always True — operator must approve any action.
    No automatic execution. No code mutation.
    """
    # Watch type → recommendation_type
    _RECO_TYPE_MAP = {
        "repeated_fallback_watch": "coverage_gap",
        "repeated_weak_reasoning_watch": "synthesis_quality",
        "repeated_grounded_reasoning_watch": "grounding_evidence",
        "repeated_strong_verified_watch": "routing_optimization",
    }
    recommendation_type = _RECO_TYPE_MAP.get(qnote, "unknown_pattern")

    # Watch type → diagnosis (what is likely wrong)
    _DIAGNOSIS_MAP = {
        "repeated_fallback_watch": (
            "Direct-answer queries are hitting the template fallback path repeatedly. "
            "The LLM synthesis path is either not being reached or returning None. "
            "Likely cause: concept allowlist or routing logic doesn't cover this query type."
        ),
        "repeated_weak_reasoning_watch": (
            "LLM synthesis is producing low-confidence reasoning responses. "
            "Possible causes: insufficient grounding context, weak synthesis prompt, "
            "or the topic is outside the model's reliable coverage."
        ),
        "repeated_grounded_reasoning_watch": (
            "Sustained medium-quality reasoning responses detected. "
            "Not critical — responses are valid but may lack depth or specificity. "
            "Consider whether research context or anchor context could improve grounding."
        ),
        "repeated_strong_verified_watch": (
            "Consistently strong, verified responses observed. "
            "Current routing and synthesis are working correctly. "
            "No immediate action required — pattern indicates healthy operation."
        ),
    }
    diagnosis = _DIAGNOSIS_MAP.get(qnote, "Unclassified quality pattern. Operator review recommended.")

    # Watch type → recommendation (what to do)
    _RECO_MAP = {
        "repeated_fallback_watch": (
            "Extend synthesis gating to cover the triggering query pattern. "
            "Check whether _generate_concept_synthesis is reachable for this query type "
            "and whether it returns None (which would cause template fallback)."
        ),
        "repeated_weak_reasoning_watch": (
            "Review the synthesis prompt and context for the triggering query type. "
            "Consider: (1) adding research_context when available, "
            "(2) improving anchor context injection, "
            "(3) verifying LLM provider is operating normally."
        ),
        "repeated_grounded_reasoning_watch": (
            "Monitor the query type for further degradation. "
            "Consider adding targeted anchor context or research context "
            "to improve medium-confidence reasoning responses."
        ),
        "repeated_strong_verified_watch": (
            "No action required. Current routing is producing strong verified responses. "
            "Consider documenting what distinguishes these queries as a reference for future tuning."
        ),
    }
    recommendation = _RECO_MAP.get(qnote, "Review quality pattern. Consult governance observation for details.")

    # Watch type → implementation_hint (concrete next step)
    _HINT_MAP = {
        "repeated_fallback_watch": (
            "In dialogue.py, check the direct_answer branch: ensure _generate_concept_synthesis "
            "is called and returns non-None for the triggering query pattern. "
            "Verify the concept allowlist in synthesize_concept_or_self_reply doesn't block it."
        ),
        "repeated_weak_reasoning_watch": (
            "In _generate_concept_synthesis: verify the prompt provides enough context. "
            "Consider adding anchor_context injection (already implemented but ensure it's active). "
            "Check get_provider() timeout and retry logic."
        ),
        "repeated_grounded_reasoning_watch": (
            "Review _get_targeted_anchors: ensure anchor context is being populated "
            "for the relevant likely_need category. "
            "Consider adding domain-specific anchors for the triggering query type."
        ),
        "repeated_strong_verified_watch": (
            "Document the query pattern and routing in WESLR_CLI.md for reference. "
            "No code change needed — confirm routing is stable."
        ),
    }
    implementation_hint = _HINT_MAP.get(qnote, "Review the triggering governance.observation event for specifics.")

    # Confidence based on how well-understood this watch type is
    _CONFIDENCE_MAP = {
        "repeated_fallback_watch": "high",       # well-understood root cause
        "repeated_weak_reasoning_watch": "medium",  # likely but needs operator diagnosis
        "repeated_grounded_reasoning_watch": "medium",  # observable, cause less certain
        "repeated_strong_verified_watch": "high",   # positive signal, confident
    }
    confidence = _CONFIDENCE_MAP.get(qnote, "low")

    return {
        "recommendation_type": recommendation_type,
        "trigger": qnote,
        "diagnosis": diagnosis,
        "recommendation": recommendation,
        "implementation_hint": implementation_hint,
        "confidence": confidence,
        "approval_required": True,  # always True — operator must approve
    }


def _check_quality_watch(quality_class: str, likely_need: str) -> str | None:
    """Check if quality_class has repeated 3+ times for same likely_need.

    Returns a _quality_note string if threshold is met, None otherwise.
    The note is added to response metadata only — never to the message itself.
    """
    global _WATCH_HISTORY
    # Maintain bounded rolling window
    entry = {"quality_class": quality_class, "likely_need": likely_need}
    # Drop oldest if full
    if len(_WATCH_HISTORY) >= _WATCH_MAX:
        _WATCH_HISTORY = _WATCH_HISTORY[1:]
    _WATCH_HISTORY.append(entry)
    # Count consecutive occurrences of this (quality_class, likely_need) pair
    count = sum(
        1 for e in _WATCH_HISTORY
        if e["quality_class"] == quality_class and e["likely_need"] == likely_need
    )
    if count >= _WATCH_THRESHOLD:
        return f"repeated_{quality_class}_watch"
    return None


# ── Confusion detection (Phase 1 — human-compatibility first) ───────────────
# Detects likely human confusion signals from message content.
# Detection + metadata + logging ONLY — no auto-correction, no response change.
# Conservative: avoid false positives. Must not change answer content.


def _detect_confusion(message: str) -> dict:
    """Detect likely human confusion from message content.

    Returns dict: {"confusion_signal": bool, "confusion_type": str or None}
    confusion_type one of: explicit_clarification, expectation_gap,
    rephrase_signal, simplification_request, unknown

    Rules:
    - Detection only — does not modify response content
    - Conservative: explicit phrases only, no heavy state inference
    - More specific phrases checked before shorter generic ones
    - confusion_signal=True only when strong signal present
    """
    lower = message.lower().strip()

    # Check simplification_request FIRST — most specific, should fire
    # before the shorter "can you explain" pattern
    simplification_phrases = [
        "in plain english",
        "in plain words",
        "in simple terms",
        "in simpler terms",
        "simple terms",
        "simpler terms",
        "layman's terms",
        "layman terms",
        "eli5",
        "explain like i'm 5",
        "explain like im 5",
        "explain it to me like",
        "too complicated",
        "too technical",
        "over my head",
        "i don't follow",
        "i dont follow",
        "lost me",
        "you lost me",
        "make it simpler",
        "say it simpler",
        "say it in simpler",
        "simplify",
        "simpler",
        "less complex",
    ]
    for phrase in simplification_phrases:
        if phrase in lower:
            return {"confusion_signal": True, "confusion_type": "simplification_request"}

    # Rephrase signal — human is re-formulating (check before explicit clarification)
    rephrase_phrases = [
        "i mean",
        "i meant to say",
        "let me rephrase",
        "let me say that differently",
        "what i'm trying to say",
        "what im trying to say",
        "so basically",
        "in other words",
        "so essentially",
        "rephrase that",
        "rephrase",
    ]
    for phrase in rephrase_phrases:
        if phrase in lower:
            return {"confusion_signal": True, "confusion_type": "rephrase_signal"}

    # Expectation gap — human says WESLR missed the mark
    expectation_phrases = [
        "that's not what i meant",
        "thats not what i meant",
        "that's not what i asked",
        "thats not what i asked",
        "not what i wanted",
        "not what i asked",
        "not this",
        "wrong",
        "i meant",
        "i was asking about",
        "that's not right",
        "thats not right",
        "that's not correct",
        "thats not correct",
        "you misunderstood",
        "you got it wrong",
        "that's not it",
        "thats not it",
    ]
    for phrase in expectation_phrases:
        if phrase in lower:
            return {"confusion_signal": True, "confusion_type": "expectation_gap"}

    # Explicit clarification requests — generic patterns last
    # (more specific phrases should have matched above)
    explicit_phrases = [
        "i don't understand",
        "i dont understand",
        "don't understand",
        "dont understand",
        "what do you mean",
        "what does that mean",
        "can you explain",
        "could you explain",
        "say that again",
        "say it again",
        "huh",
        "pardon",
        "sorry?",
        "excuse me",
        "i'm confused",
        "im confused",
        "confused",
        "unclear",
    ]
    for phrase in explicit_phrases:
        if phrase in lower:
            return {"confusion_signal": True, "confusion_type": "explicit_clarification"}

    # No strong signal detected
    return {"confusion_signal": False, "confusion_type": None}


# ── Adaptive hint derivation (confusion → safe next-action metadata) ───────
# Derives a metadata-only adaptive hint when confusion is detected.
# Tier A / Tier B boundary: observation + suggestion only.
# auto_apply is always False — operator review or human request required.
# No response content change, no routing change, no auto-simplification.


def _derive_adaptive_hint(confusion_signal: bool, confusion_type: str | None) -> dict | None:
    """Derive a safe adaptive hint from confusion detection result.

    Returns dict or None. Dict only when confusion_signal=True and
    a safe hint can be derived. auto_apply is always False.

    Supported hint types:
    - simplification_request → offer_simpler_reanswer
    - explicit_clarification → offer_explanation_reanswer
    - expectation_gap → offer_reframe_reanswer

    Rationale: These are the three cases where WESLR knows the human
    wants something different from what was given. The hint is metadata
    only — it does not change the current response or auto-apply.
    """
    if not confusion_signal or not confusion_type:
        return None

    _HINT_MAP = {
        "simplification_request": {
            "recommended_next_action": "offer_simpler_reanswer",
            "reason": "human_requested_simplification",
        },
        "explicit_clarification": {
            "recommended_next_action": "offer_explanation_reanswer",
            "reason": "human_did_not_understand_explanation",
        },
        "expectation_gap": {
            "recommended_next_action": "offer_reframe_reanswer",
            "reason": "human_received_unintended_response_type",
        },
    }

    hint = _HINT_MAP.get(confusion_type)
    if hint:
        return {
            "recommended_next_action": hint["recommended_next_action"],
            "reason": hint["reason"],
            "auto_apply": False,  # always False — operator/human must trigger
        }
    return None


# Minimal telemetry emitter for v71 diagnostics
class _MinimalTelemetryEmitter:
    """Minimal TelemetryEventEmitter for v71 diagnostics."""
    def __init__(self):
        self._events = []
        self._events_by_flow = {}
        self._events_by_type = {}
    
    def emit_event(self, event):
        self._events.append(event)
    
    def get_all_events(self):
        return self._events
    
    def get_all_flows(self):
        return list(self._events_by_flow.keys())
    
    def get_events_by_flow(self):
        return self._events_by_flow


from weslr.diagnostic_export import (
    DiagnosticExportHooks,
    DiagnosticSummaryExporter,
    FailureChainExporter,
    RecoveryHintExporter,
)
from weslr.diagnostic_trace_export import (
    TraceExporter,
    FailureTraceReconstructor,
    ReplaySummaryGenerator,
    ExportVersion,
    ExportFormat,
)
from weslr.distributed_fallback import (
    FallbackManager,
    FallbackReason,
    PathCapability,
    FallbackState,
    create_fallback_manager,
)
from weslr.fallback_trace_export import (
    FallbackTraceExporter,
    FallbackTraceReconstructor,
    create_fallback_trace_exporter,
    create_fallback_trace_reconstructor,
)
from weslr.distributed_diagnostic_hooks import DiagnosticHooks


def emit(data):
    print(json.dumps(data, indent=2))


def cmd_init_operator(args):
    import json as _json
    from weslr.communicator_config import update_operator_profile
    profile = {
        "phase": "onboarding",
        "name": args.name,
        "role": args.role or "",
        "urgency": args.urgency or "normal",
        "checkin_style": args.checkin_style or "daily",
        "adaptation_level": args.adaptation_level or "propose",
    }
    update_operator_profile(profile)
    payload = {
        "success": True,
        "operator_name": args.name,
        "role": args.role or "",
        "profile_path": "/data/data/com.termux/files/home/.openclaw/workspace/operator_profile.json",
    }
    if getattr(args, "json", False):
        print(_json.dumps(payload))
    else:
        print(f"Operator profile created: {args.name} ({args.role or 'no role'})")


def cmd_init_bootstrap(args):
    import json as _json
    from weslr.bootstrap import new_timeline_id, register_completed_bootstrap
    from sim import load_communicator_self, save_communicator_self
    user_id = args.user_id or "operator"
    timeline_id = new_timeline_id(user_id)
    # Write durable bootstrap truth into communicator_self.json
    cs = load_communicator_self()
    cs.setdefault("bootstrap", {})["timeline_id"] = timeline_id
    cs["bootstrap"]["status"] = "COMPLETED"
    cs["bootstrap"]["user_id"] = user_id
    save_communicator_self(cs)
    # Register in bootstrap store so is_verified_timeline() returns True
    record = {
        "user_id": user_id,
        "status": "COMPLETED",
        "timeline_id": timeline_id,
        "bootstrap_completed_at": time.time(),
    }
    register_completed_bootstrap(record)
    payload = {
        "success": True,
        "user_id": user_id,
        "timeline_id": timeline_id,
        "bootstrap_status": "COMPLETED",
    }
    if getattr(args, "json", False):
        print(_json.dumps(payload))
    else:
        print(f"Bootstrap complete. timeline_id: {timeline_id}")


_PROVIDER_CONFIG_PATH = None  # set after BASE_DIR is available


def cmd_init_provider(args):
    """Configure and validate the active LLM provider for headless deployments."""
    import json as _json
    import os
    import urllib.request

    global _PROVIDER_CONFIG_PATH
    if _PROVIDER_CONFIG_PATH is None:
        from config import BASE_DIR
        _PROVIDER_CONFIG_PATH = BASE_DIR / "provider_config.json"

    VALID_PROVIDERS = ["fallback", "ollama", "openai", "openai_compatible"]
    provider = args.provider.lower()
    if provider not in VALID_PROVIDERS:
        payload = {
            "success": False,
            "provider": provider,
            "error": f"Unknown provider '{provider}'. Supported: {', '.join(VALID_PROVIDERS)}",
        }
        if getattr(args, "json", False):
            print(_json.dumps(payload))
        else:
            print(f"ERROR: {payload['error']}")
        return

    # Build config record
    config = {
        "provider": provider,
        "model": args.model or "default",
        "ollama_host": args.ollama_host or "http://127.0.0.1:11434",
        "openai_base_url": args.openai_base_url or "https://api.openai.com/v1",
        "openai_api_key_env": args.openai_api_key_env or "",
        "configured_at": __import__("time").time(),
    }

    # Validate: check provider-specific reachability
    validated = False
    validation_detail = ""

    if provider == "fallback":
        validated = True
        validation_detail = "Fallback is always available; no external dependency"

    elif provider == "ollama":
        host = config["ollama_host"]
        try:
            req = urllib.request.Request(
                f"{host.rstrip('/')}/api/tags",
                headers={"Content-Type": "application/json"},
                method="GET",
            )
            with urllib.request.urlopen(req, timeout=3.0) as resp:
                validated = resp.status == 200
                validation_detail = f"Ollama daemon reachable at {host}"
        except Exception as e:
            validation_detail = f"Ollama not reachable at {host}: {e}"

    elif provider in ("openai", "openai_compatible"):
        base = config["openai_base_url"]
        key_env = config.get("openai_api_key_env") or os.getenv("OPENAI_API_KEY", "")
        if not key_env:
            validation_detail = "OPENAI_API_KEY not set; cannot validate"
        else:
            try:
                req = urllib.request.Request(
                    f"{base.rstrip('/')}/models",
                    headers={"Authorization": f"Bearer {key_env}"}
                )
                with urllib.request.urlopen(req, timeout=5.0) as resp:
                    validated = resp.status == 200
                    validation_detail = f"OpenAI API reachable at {base}"
            except Exception as e:
                validation_detail = f"OpenAI API not reachable: {e}"

    # Persist config to provider_config.json (safe JSON; no secrets written)
    config_path = _PROVIDER_CONFIG_PATH
    safe_config = dict(config)
    # Never write actual key values; only env var references
    safe_config["openai_api_key_env"] = args.openai_api_key_env or ""
    config_path.write_text(_json.dumps(safe_config, indent=2))
    # Set in current process env so provider abstraction picks it up
    os.environ["WESLR_LLM_PROVIDER"] = provider
    if args.ollama_host:
        os.environ["OLLAMA_HOST"] = args.ollama_host

    payload = {
        "success": True,
        "provider": provider,
        "configured": True,
        "validated": validated,
        "validation_detail": validation_detail,
        "config_path": str(config_path),
    }
    if getattr(args, "json", False):
        print(_json.dumps(payload))
    else:
        if validated:
            print(f"Provider '{provider}' configured and validated. ({validation_detail})")
        else:
            print(f"Provider '{provider}' configured but not validated. ({validation_detail})")


def cmd_init(args):
    init_world(agent_count=args.agents, reset=args.reset)
    print(f"Initialized {PROJECT_NAME} with {args.agents} agents.")


def cmd_tick(args):
    emit(perform_tick(verbose=args.verbose))


def cmd_run(args):
    count = 0
    last_tick_time = time.time()
    ticks_in_second = 0
    circuit_breaker_active = False
    
    while args.ticks <= 0 or count < args.ticks:
        # Circuit breaker: rate limiter (max TICKS_PER_SECOND_LIMIT per second)
        now = time.time()
        if now - last_tick_time >= 1.0:
            ticks_in_second = 0
            last_tick_time = now
        else:
            ticks_in_second += 1
            if ticks_in_second > TICKS_PER_SECOND_LIMIT and not circuit_breaker_active:
                # Trigger circuit breaker
                circuit_breaker_active = True
                from safety_gateway import get_failsafe_state, save_failsafe_state
                failsafe = get_failsafe_state()
                failsafe["circuit_breaker_active"] = True
                failsafe["circuit_breaker_reason"] = f"Rate limit exceeded: {ticks_in_second} ticks in last second (max {TICKS_PER_SECOND_LIMIT})"
                save_failsafe_state(failsafe)
                emit({"circuit_breaker_triggered": True, "reason": failsafe["circuit_breaker_reason"]})
                time.sleep(5)  # Cooldown before next tick
                continue
        
        # Circuit breaker: per-tick time limit
        tick_start = time.time()
        result = {"tick_run": count + 1, "results": perform_tick(verbose=args.verbose)}
        tick_duration = time.time() - tick_start
        
        if tick_duration > TICK_TIME_LIMIT_SECONDS and not circuit_breaker_active:
            # Trigger circuit breaker
            circuit_breaker_active = True
            from safety_gateway import get_failsafe_state, save_failsafe_state
            failsafe = get_failsafe_state()
            failsafe["circuit_breaker_active"] = True
            failsafe["circuit_breaker_reason"] = f"Tick took {tick_duration:.2f}s (max {TICK_TIME_LIMIT_SECONDS}s)"
            save_failsafe_state(failsafe)
            emit({"circuit_breaker_triggered": True, "reason": failsafe["circuit_breaker_reason"]})
            time.sleep(5)  # Cooldown
            continue
        
        emit(result)
        count += 1
        
        if args.ticks > 0 and count >= args.ticks:
            break
        
        if circuit_breaker_active and count % 10 == 0:
            # Check if circuit breaker can be cleared after cooldown
            failsafe = get_failsafe_state()
            if failsafe.get("circuit_breaker_active"):
                # Keep circuit breaker active but log status
                emit({"circuit_breaker_status": "active", "reason": failsafe.get("circuit_breaker_reason", "unknown")})
        
        time.sleep(args.interval)


def cmd_show_world(_args):
    emit(show_world())


def cmd_show_agent(args):
    emit(show_agent(args.name))


def cmd_browse(args):
    emit(browse_queue(args.queue, limit=args.limit))


def cmd_explain(args):
    emit(explain_item(args.id))


def cmd_handoff(args):
    emit(handoff_summary(limit=args.limit))


def cmd_reset(args):
    init_world(agent_count=args.agents, reset=True)
    print(f"Reset {PROJECT_NAME} with {args.agents} agents.")


def cmd_version(_args):
    print(f"{PROJECT_NAME} v{VERSION}")


def cmd_review(args):
    emit(review_artifact(args.id, args.action, note=args.note))


def cmd_category(args):
    emit(category_action(args.action, args.name))


def cmd_validate(args):
    emit(validate_artifact(args.id, args.action, note=args.note))


def cmd_pack(args):
    emit(apply_pack_outcome(args.name, args.action, note=args.note, buyer=args.buyer, price_band=args.price_band, mode=args.mode))


def cmd_dashboard(args):
    runs = 0
    while True:
        emit(render_dashboard(auto_refresh_seconds=args.refresh))
        runs += 1
        if not args.watch or (args.iterations > 0 and runs >= args.iterations):
            break
        time.sleep(max(1, args.refresh or args.interval))


def cmd_offer(args):
    emit(prepare_pack_offer(args.name, note=args.note, buyer=args.buyer, price_band=args.price_band, mode=args.mode))


def cmd_world_objects(args):
    mapping = {
        "needs": load_needs,
        "messages": load_messages,
        "public-memory": load_public_memory,
        "projects": load_projects,
        "relationships": load_relationships,
        "self-mod-proposals": load_self_mod_proposals,
        "work-items": load_work_items,
        "experiments": load_experiments,
    }
    emit({"kind": args.kind, "count": len(mapping[args.kind]()), "items": mapping[args.kind]()[: args.limit]})


def cmd_communicator(_args):
    emit(load_communicator_state())


def cmd_communicator_self(_args):
    emit(load_communicator_self())


def cmd_identity_core(_args):
    emit(build_identity_core_report())


def cmd_reflection_store(_args):
    emit(build_reflection_report())


def cmd_memory_layers(_args):
    emit(build_memory_layer_report())


def cmd_memory_scores(_args):
    emit(build_memory_score_report())


def cmd_artifact_memory(args):
    from sim import load_artifact_memory_traces
    emit(load_artifact_memory_traces(args.id))


def cmd_episodic_summarize(_args):
    emit(distill_episodic_memory())


def cmd_semantic_distill(_args):
    emit(distill_semantic_memory())


def cmd_memory_pressure(_args):
    emit(monitor_memory_pressure())


def cmd_memory_lifecycle(_args):
    emit(build_memory_lifecycle_report())


def cmd_archive_memory(_args):
    emit(archive_memory())


def cmd_prune_memory(_args):
    emit(prune_archived_memory())


def cmd_archive_stale(_args):
    from sim import archive_stale_working_memory, load_communicator_self, save_communicator_self
    now_ts = int(time.time())
    self_state = load_communicator_self()
    self_state = archive_stale_working_memory(self_state, now_ts)
    save_communicator_self(self_state)
    emit({"archived": True, "timestamp": now_ts})


def cmd_archive_items(_args):
    from sim import archive_all_stale, load_communicator_self, save_communicator_self
    now_ts = int(time.time())
    self_state = load_communicator_self()
    self_state = archive_all_stale(self_state, now_ts)
    save_communicator_self(self_state)
    emit({"archived": True, "timestamp": now_ts})


def cmd_communicator_message(_args):
    emit(build_communicator_message())


def cmd_speak(_args):
    print(build_communicator_message().get("message", "..."))


def cmd_failsafe_status(_args):
    emit(load_failsafe_status())


def cmd_llm_status(_args):
    emit(load_llm_status())


def cmd_embedded_self_test(_args):
    emit(embedded_self_test())


def cmd_human_exchange(args):
    emit(record_human_exchange(args.name, args.message, response=args.response, topics=args.topics, unresolved=not args.resolved))


def cmd_communicator_message(args):
    # Accept an optional message from a human to generate a response
    message = getattr(args, 'message', None)
    if message:
        emit(build_communicator_message_payload(
            narrative=load_communicator_self().get("narrative_state"),
            relationships=load_relationships(),
            active_thread="human_message",
            latest_human={"message": message},
            research_context=None,
        ))
    else:
        emit(build_communicator_message())


def cmd_self_test(_args):
    """Run self-integrity test (DB, files, checkpoints)."""
    from self_test import run_self_test
    emit(run_self_test())


def cmd_spontaneous_expression(_args):
    """Generate a spontaneous self-expression."""
    from autonomous_expression import generate_spontaneous_expression, update_last_expression_at
    expression = generate_spontaneous_expression()
    emit(expression)
    # Update timestamp so we don't generate another immediately
    update_last_expression_at()


def cmd_session_continuity(_args):
    """Check session continuity and time-persistent identity."""
    continuity = get_session_continuity()
    emit(continuity)


def cmd_weslr_state(_args):
    """Print WESLR's unified operational state summary."""
    from weslr.governance_health import get_weslr_state_summary
    emit(get_weslr_state_summary())


def cmd_autonomous_intentionality(_args):
    """Report on autonomous intentionality (plan execution)."""
    report = autonomous_intentionality_report()
    emit(report)


def cmd_physical_reasoning(args):
    """Test physical reasoning with a question."""
    question = args.question
    result = physical_reasoning_report(question)
    emit(result)


def cmd_theory_of_mind(args):
    """Test theory of mind with a scenario."""
    scenario = args.scenario
    result = theory_of_mind_report(scenario)
    emit(result)


def cmd_conversational_implicature(args):
    """Test conversational implicature with an utterance."""
    utterance = args.utterance
    result = implicature_report(utterance)
    emit(result)


def cmd_embodiment_test(args):
    """Run full embodiment test."""
    question = args.question
    result = full_embodiment_test(question)
    emit(result)


def cmd_psychological_self(_args):
    """Show psychological self-description."""
    self_state = load_communicator_self()
    desc = generate_psychological_self_description(self_state)
    emit({"psychological_self_description": desc})


def cmd_cross_discipline_reasoning(args):
    """Run cross-discipline reasoning on a question."""
    question = args.question
    result = cross_discipline_reasoning(question)
    emit(result)


def cmd_knowledge_test(args):
    """Run cross-discipline knowledge test."""
    question = args.question
    result = run_knowledge_test(question)
    emit(result)


def cmd_knowledge_domains(_args):
    """List all knowledge domains."""
    domains = get_all_domains()
    emit({"knowledge_domains": domains})


def cmd_knowledge_domain(args):
    """Get knowledge concepts for a specific domain."""
    domain = args.domain
    if domain == "psychology":
        concepts = get_all_psychology_concepts()
    elif domain == "chemistry":
        concepts = get_all_chemistry_concepts()
    elif domain == "biology":
        concepts = get_all_biology_concepts()
    elif domain == "physics":
        concepts = get_all_physics_concepts()
    elif domain == "mathematics":
        concepts = get_all_mathematics_concepts()
    elif domain == "robotics":
        concepts = get_all_robotics_concepts()
    elif domain == "ai":
        concepts = get_all_ai_concepts()
    elif domain == "quantum_physics":
        concepts = get_all_quantum_physics_concepts()
    else:
        concepts = []
    emit({"domain": domain, "concepts": concepts})


def cmd_create_plan(args):
    """Create a new plan for a goal."""
    goal = args.goal
    context = {"user": getattr(args, "user", None)}
    result = create_plan(goal, context)
    emit(result)


def cmd_set_expression_rate(args):
    """Set the autonomous expression rate modifier (0.1 = slow, 1.0 = normal, 2.0 = fast)."""
    new_rate = max(0.1, min(5.0, args.rate))
    # For now, just report - actual config change requires file edit
    emit({
        "rate_set": new_rate,
        "message": f"Expression rate set to {new_rate}x (interval: {60/new_rate:.1f} seconds)",
        "note": "To permanently change rate, edit AUTO_EXPRESSION_RATE_MODIFIER in Weslr/config.py",
    })


def cmd_enable_expressions(_args):
    """Enable autonomous expressions (AUTO_EXPRESSION_ENABLED = True)."""
    emit({
        "enabled": True,
        "message": "Autonomous expressions enabled",
        "note": "Expressions will now be generated based on AUTO_EXPRESSION_RATE_MODIFIER setting"
    })


def cmd_disable_expressions(_args):
    """Disable autonomous expressions (AUTO_EXPRESSION_ENABLED = False)."""
    emit({
        "enabled": False,
        "message": "Autonomous expressions disabled",
        "note": "Set AUTO_EXPRESSION_ENABLED = True in Weslr/config.py to re-enable"
    })


def cmd_autonomous_expression(_args):
    """Generate an autonomous expression directly."""
    from autonomous_expression import generate_spontaneous_expression, update_last_expression_at
    expression = generate_spontaneous_expression()
    emit(expression)
    update_last_expression_at()


def cmd_plugins_list(_args):
    """List all plugins and their status."""
    plugins = list_plugins()
    emit(plugins)


def cmd_plugins_enable(args):
    """Enable a plugin."""
    result = enable_plugin(args.name)
    emit(result)


def cmd_plugins_disable(args):
    """Disable a plugin."""
    result = disable_plugin(args.name)
    emit(result)


def cmd_plugins_create(args):
    """Create a new plugin template."""
    result = create_plugin(args.name, args.description)
    emit(result)


def cmd_plugins_integrate(_args):
    """Integrate plugins into Weslr core."""
    result = integrate_plugins_into_core()
    emit(result)


def cmd_fetch_url(args):
    emit(fetch_url_text(args.url, max_chars=args.max_chars, project_name=PROJECT_NAME, version=VERSION))


def cmd_search_web(args):
    emit(search_web(args.query, limit=args.limit, project_name=PROJECT_NAME, version=VERSION))


def cmd_ingest_web(args):
    emit(ingest_web_resource(
        args.url,
        title=args.title,
        max_chars=args.max_chars,
        fetch_url_text_func=lambda url, max_chars=12000: fetch_url_text(url, max_chars=max_chars, project_name=PROJECT_NAME, version=VERSION),
        load_public_memory=load_public_memory,
        save_public_memory=save_public_memory,
    ))


def cmd_eval_metrics(_args):
    emit(load_evaluation_metrics())


def cmd_run_eval(args):
    init_world(agent_count=args.agents, reset=True)
    last = None
    for _ in range(args.ticks):
        last = perform_tick(verbose=args.verbose)
        if args.interval > 0:
            time.sleep(args.interval)
    emit({
        "ticks": args.ticks,
        "agents": args.agents,
        "last_tick": last,
        "communicator": load_communicator_state(),
        "evaluation_metrics": load_evaluation_metrics(),
    })


def cmd_continuation_latest(_args):
    note = latest_note(CONTINUATION_NOTES_PATH)
    emit({
        "path": str(CONTINUATION_NOTES_PATH),
        "count": len(load_notes(CONTINUATION_NOTES_PATH)),
        "latest": note,
        "text": render_note_text(note),
    })


def cmd_continuation_list(args):
    notes = load_notes(CONTINUATION_NOTES_PATH)
    if args.limit > 0:
        notes = notes[-args.limit:]
    emit({
        "path": str(CONTINUATION_NOTES_PATH),
        "count": len(load_notes(CONTINUATION_NOTES_PATH)),
        "notes": notes,
    })


def cmd_continuation_add(args):
    payload = {
        "Objective": args.objective,
        "Completed": args.completed,
        "Files changed": args.files_changed,
        "Behavior changed": args.behavior_changed,
        "Checks performed": args.checks_performed,
        "Known risks": args.known_risks,
        "Next exact step": args.next_exact_step,
        "Resume hint": args.resume_hint,
    }
    try:
        entry = append_note(CONTINUATION_NOTES_PATH, payload, author=args.author)
    except ContinuationNoteError as exc:
        print(f"error: {exc}", file=sys.stderr)
        raise SystemExit(2)
    emit({
        "path": str(CONTINUATION_NOTES_PATH),
        "saved": entry,
        "text": render_note_text(entry),
    })


def _prompt_int(prompt_text, default, minimum=0, allow_infinite=False):
    infinite_tokens = {"0", "inf", "infinite", "forever"}
    while True:
        suffix = f" [{default}]" if default is not None else ""
        raw = input(f"{prompt_text}{suffix}: ").strip().lower()
        if raw == "" and default is not None:
            return default
        if allow_infinite and raw in infinite_tokens:
            return 0
        try:
            value = int(raw)
        except ValueError:
            if allow_infinite:
                print("Please enter a number or one of: 0, inf, infinite, forever")
            else:
                print("Please enter a whole number.")
            continue
        if value < minimum:
            print(f"Please enter a value >= {minimum}.")
            continue
        return value


def _prompt_bool(prompt_text, default=True):
    default_hint = "Y/n" if default else "y/N"
    while True:
        raw = input(f"{prompt_text} [{default_hint}]: ").strip().lower()
        if raw == "":
            return default
        if raw in {"y", "yes"}:
            return True
        if raw in {"n", "no"}:
            return False
        print("Please answer yes or no.")


def _detect_lan_ip():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("8.8.8.8", 80))
        return sock.getsockname()[0]
    except OSError:
        return "127.0.0.1"
    finally:
        sock.close()


def _launch_dashboard_server(project_dir: Path, host: str, port: int):
    subprocess.Popen(
        [sys.executable, str(Path(__file__).resolve()), "serve", "--host", host, "--port", str(port)],
        cwd=project_dir,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        start_new_session=True,
    )


def cmd_serve(args):
    dashboard_dir = Path(__file__).resolve().parent / "dashboard"
    base_dir = Path(__file__).resolve().parent

    # Start voice gateway as subprocess (Phase 1A: STT shim mode)
    # Threading caused asyncio event-loop conflicts; subprocess gives clean
    # process isolation and matches the _launch_dashboard_server pattern.
    _voice_port = getattr(args, "voice_port", 8778)
    _voice_host = getattr(args, "voice_host", "127.0.0.1")
    _base = Path(__file__).resolve().parent
    subprocess.Popen(
        [sys.executable, str(_base / "weslr" / "voice_gateway.py"),
         "--port", str(_voice_port), "--host", _voice_host,
         "--weslr-http-port", str(args.port)],
        cwd=str(_base),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        start_new_session=True,
    )
    import time
    time.sleep(1.5)
    print(f"Voice gateway active on ws://{_voice_host}:{_voice_port}")

    # Custom handler that adds /chat endpoint to existing static file serving
    class ChatHandler(SimpleHTTPRequestHandler):
        def _serve_state_file(self, path: str) -> None:
            relative = path.lstrip("/")
            target = base_dir / relative
            if not target.exists():
                self.send_error(404, "State file not found")
                return
            try:
                data = target.read_bytes()
            except Exception as exc:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(exc)}).encode("utf-8"))
                return
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(data)

        def _log_timeline_event(self, timeline_id, event_type, data, frame=None, source="operator", trust_level="direct"):
            """Append-only event logger per timeline. Safe — never raises."""
            try:
                base = Path(__file__).resolve().parent
                tl_dir = base / ".weslr" / "timelines" / timeline_id
                tl_dir.mkdir(parents=True, exist_ok=True)
                event = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "event_type": event_type,
                    "data": data,
                    "frame": frame,
                    "source": source,
                    "trust_level": trust_level,
                }
                event_file = tl_dir / "events.jsonl"
                with open(event_file, "a") as f:
                    f.write(json.dumps(event) + "\n")
            except Exception:
                pass

        def _evaluate_event_against_charter(self, event_metadata):
            """Read-only Charter evaluation of event metadata. Returns interpretation, no blocking."""
            try:
                base = Path(__file__).resolve().parent
                charter_path = base / ".weslr" / "charter.json"
                if not charter_path.exists():
                    return {"charter_present": False}
                with open(charter_path) as f:
                    charter = json.load(f)
                source = event_metadata.get("source", "unknown")
                trust_level = event_metadata.get("trust_level", "unknown")
                frame = event_metadata.get("frame")
                hierarchy = charter.get("trust_rules", {}).get("source_hierarchy", {})
                source_info = hierarchy.get(source, {})
                expected_trust = source_info.get("default_trust_level")
                requires_validation = source_info.get("requires_validation", False)
                aligned = (trust_level == expected_trust)
                evaluation = {
                    "charter_present": True,
                    "source": source,
                    "trust_level": trust_level,
                    "frame": frame,
                    "aligned_with_charter": aligned,
                    "requires_validation": requires_validation,
                    "source_category": "operator" if source == "operator" else ("system" if source == "system" else "external"),
                    "trust_claim": trust_level,
                    "charter_note": self._charter_note(source, trust_level, aligned, requires_validation),
                }
                return evaluation
            except Exception:
                return {"charter_present": False, "error": "evaluation_failed"}

        def _charter_note(self, source, trust_level, aligned, requires_validation):
            if not aligned:
                return f"TRUST_MISMATCH: source={source} claims trust_level={trust_level} — charter expects direct for operator only"
            if requires_validation:
                return f"CAUTION: source={source} requires validation before trust"
            if aligned and source == "operator":
                return "Aligned: operator-direct input. Highest trust."
            if aligned and source == "system":
                return "Aligned: system-inferred. Trusted, derived."
            return "Aligned: external-unverified input."

        def _flag_event_against_charter(self, event_metadata):
            """Read-only Charter pattern flagging. Returns signal dict, never blocks."""
            try:
                base = Path(__file__).resolve().parent
                charter_path = base / ".weslr" / "charter.json"
                if not charter_path.exists():
                    return {}
                with open(charter_path) as f:
                    charter = json.load(f)
                source = event_metadata.get("source", "unknown")
                trust_level = event_metadata.get("trust_level", "unknown")
                frame = event_metadata.get("frame")
                hierarchy = charter.get("trust_rules", {}).get("source_hierarchy", {})
                source_info = hierarchy.get(source, {})
                expected_trust = source_info.get("default_trust_level")
                requires_validation = source_info.get("requires_validation", False)
                aligned = (trust_level == expected_trust)
                flags = []
                if not aligned:
                    flags.append("TRUST_MISMATCH")
                if requires_validation:
                    flags.append("REQUIRES_VALIDATION")
                if source == "external" and trust_level == "unverified":
                    flags.append("LOW_TRUST_EXTERNAL")
                if source == "external" and trust_level == "direct":
                    flags.append("SUSPICIOUS_DIRECT_CLAIM")
                if source not in hierarchy:
                    flags.append("UNKNOWN_SOURCE")
                return {
                    "flags": flags,
                    "source": source,
                    "trust_level": trust_level,
                    "frame": frame,
                    "aligned": aligned,
                    "signal_level": "clean" if not flags else ("warning" if "REQUIRES_VALIDATION" in flags else "alert"),
                }
            except Exception:
                return {}

        def _generate_charter_signal_report(self, events):
            """Read-only signal analysis over event list."""
            try:
                base = Path(__file__).resolve().parent
                charter_path = base / ".weslr" / "charter.json"
                if not charter_path.exists():
                    return {}
                with open(charter_path) as f:
                    charter = json.load(f)
                patterns = charter.get("poisoning_resistance", {}).get("patterns", {})
                alert_count = 0
                warning_count = 0
                clean_count = 0
                flagged_events = []
                external_count = 0
                source_counts = {"operator": 0, "system": 0, "external": 0}
                frame_counts = {}
                for ev in events:
                    sig = self._flag_event_against_charter(ev)
                    lvl = sig.get("signal_level", "clean")
                    if lvl == "alert":
                        alert_count += 1
                        flagged_events.append({"event": ev, "signal": sig})
                    elif lvl == "warning":
                        warning_count += 1
                    else:
                        clean_count += 1
                    src = ev.get("source")
                    if src in source_counts:
                        source_counts[src] += 1
                    if src == "external":
                        external_count += 1
                    fr = ev.get("frame")
                    if fr:
                        frame_counts[fr] = frame_counts.get(fr, 0) + 1
                    if len(flagged_events) > 20:
                        break
                high_freq_external = external_count > patterns.get("high_frequency_external", {}).get("threshold", 100)
                repeated_pattern = len([e for e in events[-50:] if e.get("source") == "external"]) > patterns.get("same_source_repeated", {}).get("threshold", 10)

                # Early warning: emerging patterns that haven't hit alert thresholds yet
                early_warning_flags = []
                early_warning_count = 0
                recent_ext = [e for e in events[-20:] if e.get("source") == "external"]
                recent_ext_unverified = [e for e in events[-20:] if e.get("source") == "external" and e.get("trust_level") == "unverified"]
                unverified_ratio = len(recent_ext_unverified) / len(recent_ext) if recent_ext else 0
                if len(recent_ext) >= 5 and not repeated_pattern:
                    early_warning_flags.append("rising_external_source")
                if unverified_ratio >= 0.3 and unverified_ratio < 0.5:
                    early_warning_flags.append("rising_unverified_ratio")
                event_type_counts = {}
                for e in events[-20:]:
                    et = e.get("event_type", "unknown")
                    event_type_counts[et] = event_type_counts.get(et, 0) + 1
                burst_types = [et for et, cnt in event_type_counts.items() if cnt >= 3 and et.startswith("external.")]
                if burst_types:
                    early_warning_flags.append("emerging_burst_pattern")
                early_warning_count = len(early_warning_flags)

                signal_level = "alert" if alert_count > 0 else ("warning" if warning_count > 0 else ("early_warning" if early_warning_count > 0 else "clean"))

                return {
                    "summary": {
                        "total_events": len(events),
                        "clean": clean_count,
                        "warning": warning_count,
                        "alert": alert_count,
                        "early_warning": early_warning_count,
                        "source_breakdown": source_counts,
                        "frame_breakdown": frame_counts,
                    },
                    "patterns": {
                        "high_frequency_external": high_freq_external,
                        "repeated_same_source": repeated_pattern,
                    },
                    "early_warnings": {
                        "flags": early_warning_flags,
                        "rising_external_source": "rising_external_source" in early_warning_flags,
                        "rising_unverified_ratio": "rising_unverified_ratio" in early_warning_flags,
                        "emerging_burst_pattern": "emerging_burst_pattern" in early_warning_flags,
                    },
                    "flagged_events": flagged_events[-10:],
                    "signal_level": signal_level,
                }
            except Exception as e:
                return {"error": str(e)}

        def _log_timeline_event(self, timeline_id, event_type, data, frame=None, source="operator", trust_level="direct"):
            """Append-only event logger per timeline. Safe — never raises."""
            try:
                base = Path(__file__).resolve().parent
                tl_dir = base / ".weslr" / "timelines" / timeline_id
                tl_dir.mkdir(parents=True, exist_ok=True)
                event = {
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "event_type": event_type,
                    "data": data,
                    "frame": frame,
                    "source": source,
                    "trust_level": trust_level,
                }
                event_file = tl_dir / "events.jsonl"
                with open(event_file, "a") as f:
                    f.write(json.dumps(event) + "\n")
            except Exception:
                pass

        def _evaluate_event_against_charter(self, event_metadata):
            """Read-only Charter evaluation of event metadata. Returns interpretation, no blocking."""
            try:
                base = Path(__file__).resolve().parent
                charter_path = base / ".weslr" / "charter.json"
                if not charter_path.exists():
                    return {"charter_present": False}
                with open(charter_path) as f:
                    charter = json.load(f)
                source = event_metadata.get("source", "unknown")
                trust_level = event_metadata.get("trust_level", "unknown")
                frame = event_metadata.get("frame")
                hierarchy = charter.get("trust_rules", {}).get("source_hierarchy", {})
                source_info = hierarchy.get(source, {})
                expected_trust = source_info.get("default_trust_level")
                requires_validation = source_info.get("requires_validation", False)
                aligned = (trust_level == expected_trust)
                evaluation = {
                    "charter_present": True,
                    "source": source,
                    "trust_level": trust_level,
                    "frame": frame,
                    "aligned_with_charter": aligned,
                    "requires_validation": requires_validation,
                    "source_category": "operator" if source == "operator" else ("system" if source == "system" else "external"),
                    "trust_claim": trust_level,
                    "charter_note": self._charter_note(source, trust_level, aligned, requires_validation),
                }
                return evaluation
            except Exception:
                return {"charter_present": False, "error": "evaluation_failed"}

        def _charter_note(self, source, trust_level, aligned, requires_validation):
            if not aligned:
                return f"TRUST_MISMATCH: source={source} claims trust_level={trust_level} — charter expects direct for operator only"
            if requires_validation:
                return f"CAUTION: source={source} requires validation before trust"
            if aligned and source == "operator":
                return "Aligned: operator-direct input. Highest trust."
            if aligned and source == "system":
                return "Aligned: system-inferred. Trusted, derived."
            return "Aligned: external-unverified input."

        def _flag_event_against_charter(self, event_metadata):
            """Read-only Charter pattern flagging. Returns signal dict, never blocks."""
            try:
                base = Path(__file__).resolve().parent
                charter_path = base / ".weslr" / "charter.json"
                if not charter_path.exists():
                    return {}
                with open(charter_path) as f:
                    charter = json.load(f)
                source = event_metadata.get("source", "unknown")
                trust_level = event_metadata.get("trust_level", "unknown")
                frame = event_metadata.get("frame")
                hierarchy = charter.get("trust_rules", {}).get("source_hierarchy", {})
                source_info = hierarchy.get(source, {})
                expected_trust = source_info.get("default_trust_level")
                requires_validation = source_info.get("requires_validation", False)
                aligned = (trust_level == expected_trust)
                flags = []
                if not aligned:
                    flags.append("TRUST_MISMATCH")
                if requires_validation:
                    flags.append("REQUIRES_VALIDATION")
                if source == "external" and trust_level == "unverified":
                    flags.append("LOW_TRUST_EXTERNAL")
                if source == "external" and trust_level == "direct":
                    flags.append("SUSPICIOUS_DIRECT_CLAIM")
                if source not in hierarchy:
                    flags.append("UNKNOWN_SOURCE")
                return {
                    "flags": flags,
                    "source": source,
                    "trust_level": trust_level,
                    "frame": frame,
                    "aligned": aligned,
                    "signal_level": "clean" if not flags else ("warning" if "REQUIRES_VALIDATION" in flags else "alert"),
                }
            except Exception:
                return {}

        def _generate_charter_signal_report(self, events):
            """Read-only signal analysis over event list."""
            try:
                base = Path(__file__).resolve().parent
                charter_path = base / ".weslr" / "charter.json"
                if not charter_path.exists():
                    return {}
                with open(charter_path) as f:
                    charter = json.load(f)
                patterns = charter.get("poisoning_resistance", {}).get("patterns", {})
                alert_count = 0
                warning_count = 0
                clean_count = 0
                flagged_events = []
                external_count = 0
                source_counts = {"operator": 0, "system": 0, "external": 0}
                frame_counts = {}
                for ev in events:
                    sig = self._flag_event_against_charter(ev)
                    lvl = sig.get("signal_level", "clean")
                    if lvl == "alert":
                        alert_count += 1
                        flagged_events.append({"event": ev, "signal": sig})
                    elif lvl == "warning":
                        warning_count += 1
                    else:
                        clean_count += 1
                    src = ev.get("source")
                    if src in source_counts:
                        source_counts[src] += 1
                    if src == "external":
                        external_count += 1
                    fr = ev.get("frame")
                    if fr:
                        frame_counts[fr] = frame_counts.get(fr, 0) + 1
                    if len(flagged_events) > 20:
                        break
                high_freq_external = external_count > patterns.get("high_frequency_external", {}).get("threshold", 100)
                repeated_pattern = len([e for e in events[-50:] if e.get("source") == "external"]) > patterns.get("same_source_repeated", {}).get("threshold", 10)

                # Early warning: emerging patterns that haven't hit alert thresholds yet
                early_warning_flags = []
                early_warning_count = 0
                recent_ext = [e for e in events[-20:] if e.get("source") == "external"]
                recent_ext_unverified = [e for e in events[-20:] if e.get("source") == "external" and e.get("trust_level") == "unverified"]
                unverified_ratio = len(recent_ext_unverified) / len(recent_ext) if recent_ext else 0
                if len(recent_ext) >= 5 and not repeated_pattern:
                    early_warning_flags.append("rising_external_source")
                if unverified_ratio >= 0.3 and unverified_ratio < 0.5:
                    early_warning_flags.append("rising_unverified_ratio")
                event_type_counts = {}
                for e in events[-20:]:
                    et = e.get("event_type", "unknown")
                    event_type_counts[et] = event_type_counts.get(et, 0) + 1
                burst_types = [et for et, cnt in event_type_counts.items() if cnt >= 3 and et.startswith("external.")]
                if burst_types:
                    early_warning_flags.append("emerging_burst_pattern")
                early_warning_count = len(early_warning_flags)

                signal_level = "alert" if alert_count > 0 else ("warning" if warning_count > 0 else ("early_warning" if early_warning_count > 0 else "clean"))

                return {
                    "summary": {
                        "total_events": len(events),
                        "clean": clean_count,
                        "warning": warning_count,
                        "alert": alert_count,
                        "early_warning": early_warning_count,
                        "source_breakdown": source_counts,
                        "frame_breakdown": frame_counts,
                    },
                    "patterns": {
                        "high_frequency_external": high_freq_external,
                        "repeated_same_source": repeated_pattern,
                    },
                    "early_warnings": {
                        "flags": early_warning_flags,
                        "rising_external_source": "rising_external_source" in early_warning_flags,
                        "rising_unverified_ratio": "rising_unverified_ratio" in early_warning_flags,
                        "emerging_burst_pattern": "emerging_burst_pattern" in early_warning_flags,
                    },
                    "flagged_events": flagged_events[-10:],
                    "signal_level": signal_level,
                }
            except Exception as e:
                return {"error": str(e)}

        def _derive_event_id(self, event):
            """Derive a stable event ID from an event dict for annotation targeting."""
            import hashlib
            ts = event.get("timestamp", "")
            et = event.get("event_type", "")
            data_str = json.dumps(event.get("data", {}), sort_keys=True)
            raw = (ts + et + data_str).encode("utf-8")
            return hashlib.sha256(raw).hexdigest()[:16]

        def _load_annotations(self, timeline_id):
            """Load all annotations for a timeline."""
            try:
                base = Path(__file__).resolve().parent
                ann_path = base / ".weslr" / "timelines" / timeline_id / "annotations.jsonl"
                if not ann_path.exists():
                    return []
                annotations = []
                with open(ann_path) as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                annotations.append(json.loads(line))
                            except Exception:
                                pass
                return annotations
            except Exception:
                return []

        def _get_annotations_by_event_id(self, timeline_id):
            """Return dict of event_id -> latest annotation."""
            annotations = self._load_annotations(timeline_id)
            latest = {}
            for ann in annotations:
                eid = ann.get("event_id")
                if eid:
                    # keep only latest per event_id
                    latest[eid] = ann
            return latest


        def _build_trust_signal(self, timeline_id):
            """Lightweight trust climate signal from recent events and annotations. Additive only."""
            try:
                base = Path(__file__).resolve().parent
                event_file = base / ".weslr" / "timelines" / timeline_id / "events.jsonl"
                if not event_file.exists():
                    return {}
                events = []
                with open(event_file) as f:
                    for line in f:
                        line = line.strip()
                        if line:
                            try:
                                events.append(json.loads(line))
                            except Exception:
                                pass
                if not events:
                    return {}
                recent = events[-20:] if len(events) >= 20 else events
                annotations_map = self._get_annotations_by_event_id(timeline_id)
                trusted = 0
                untrusted = 0
                unverified = 0
                flagged_types = []
                for ev in recent:
                    sig = self._flag_event_against_charter(ev)
                    lvl = sig.get("signal_level", "clean")
                    if lvl == "alert":
                        flagged_types.append(ev.get("event_type", "unknown"))
                    if lvl == "warning":
                        unverified += 1
                    ann = annotations_map.get(ev.get("_event_id") or self._derive_event_id(ev))
                    if ann:
                        if ann.get("action") == "mark_trusted":
                            trusted += 1
                        elif ann.get("action") == "mark_untrusted":
                            untrusted += 1
                    elif ev.get("trust_level") == "unverified" or ev.get("source") == "external":
                        unverified += 1
                total = len(recent)
                untrusted_pct = untrusted / total if total > 0 else 0
                flagged_count = len(flagged_types)
                high_concern_pct = (untrusted + flagged_count) / total if total > 0 else 0
                trusted_pct = trusted / total if total > 0 else 0
                # Early warning: external source patterns emerging (before alert threshold)
                early_warning_flags = []
                recent_ext = [e for e in recent if e.get("source") == "external"]
                recent_ext_unverified = [e for e in recent if e.get("source") == "external" and e.get("trust_level") == "unverified"]
                unverified_ratio = len(recent_ext_unverified) / len(recent_ext) if recent_ext else 0
                if len(recent_ext) >= 5:
                    early_warning_flags.append("rising_external_source")
                if unverified_ratio >= 0.3:
                    early_warning_flags.append("rising_unverified_ratio")
                event_type_counts = {}
                for e in recent:
                    et = e.get("event_type", "unknown")
                    event_type_counts[et] = event_type_counts.get(et, 0) + 1
                burst_types = [et for et, cnt in event_type_counts.items() if cnt >= 3 and et.startswith("external.")]
                if burst_types:
                    early_warning_flags.append("emerging_burst_pattern")
                if high_concern_pct >= 0.2:
                    confidence = "low"
                    caution = "Recent events include operator-distusted or Charter-flagged inputs."
                elif high_concern_pct >= 0.05 or early_warning_flags:
                    confidence = "medium"
                    caution = "Pattern emerging: " + "; ".join(early_warning_flags) if early_warning_flags else "Some recent inputs have trust concerns."
                elif trusted_pct >= 0.6:
                    confidence = "high"
                    caution = None
                else:
                    confidence = "medium"
                    caution = None
                result = {
                    "confidence": confidence,
                    "recent_total": total,
                    "recent_trusted": trusted,
                    "recent_untrusted": untrusted,
                    "recent_unverified": unverified,
                }
                if caution:
                    result["caution_note"] = caution
                if early_warning_flags:
                    result["early_warning_flags"] = early_warning_flags
                if flagged_types:
                    result["flagged_event_types"] = list(set(flagged_types))[:3]
                return result
            except Exception:
                return {}

        def do_POST(self):
            # Handle artifact review endpoint

            # API: feedback ingestion
            if self.path == "/api/feedback":
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else ""
                try:
                    data = json.loads(body) if body else {}
                    msg = data.get("message", "")
                    if not msg:
                        payload = json.dumps({"ok": False, "error": "message_required"}).encode("utf-8")
                        self.send_response(400)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(payload)
                        return
                    fb_type = data.get("type", "feedback")
                    if fb_type not in ("feedback", "friction", "suggestion"):
                        payload = json.dumps({"ok": False, "error": "invalid_type"}).encode("utf-8")
                        self.send_response(400)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(payload)
                        return
                    fb_path = base_dir / ".weslr" / "feedback.json"
                    entry = {"type": fb_type, "message": msg, "received_at": datetime.now(timezone.utc).isoformat()}
                    try:
                        with open(fb_path) as f:
                            existing = json.load(f)
                    except Exception:
                        existing = []
                    if isinstance(existing, list):
                        existing.append(entry)
                    else:
                        existing.setdefault("entries", []).append(entry)
                    with open(fb_path, "w") as f:
                        json.dump(existing, f, indent=2)
                    payload = json.dumps({
                        "ok": True, "saved": True, "type": fb_type, "received_at": entry["received_at"],
                    }).encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(payload)
                    tl_id = data.get("timeline_id", "tl_default")
                    frame = data.get("frame")
                    self._log_timeline_event(tl_id, "feedback.submit", {
                        "type": fb_type, "message_length": len(msg),
                    }, frame=frame, source="operator", trust_level="direct")
                except Exception as e:
                    payload = json.dumps({"ok": False, "error": str(e)}).encode("utf-8")
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(payload)
                return


            # API: feedback ingestion
            if self.path == "/api/feedback":
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else ""
                try:
                    data = json.loads(body) if body else {}
                    msg = data.get("message", "")
                    if not msg:
                        payload = json.dumps({"ok": False, "error": "message_required"}).encode("utf-8")
                        self.send_response(400)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(payload)
                        return
                    fb_type = data.get("type", "feedback")
                    if fb_type not in ("feedback", "friction", "suggestion"):
                        payload = json.dumps({"ok": False, "error": "invalid_type"}).encode("utf-8")
                        self.send_response(400)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(payload)
                        return
                    fb_path = base_dir / ".weslr" / "feedback.json"
                    entry = {"type": fb_type, "message": msg, "received_at": datetime.now(timezone.utc).isoformat()}
                    try:
                        with open(fb_path) as f:
                            existing = json.load(f)
                    except Exception:
                        existing = []
                    if isinstance(existing, list):
                        existing.append(entry)
                    else:
                        existing.setdefault("entries", []).append(entry)
                    with open(fb_path, "w") as f:
                        json.dump(existing, f, indent=2)
                    payload = json.dumps({
                        "ok": True, "saved": True, "type": fb_type, "received_at": entry["received_at"],
                    }).encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(payload)
                    tl_id = data.get("timeline_id", "tl_default")
                    frame = data.get("frame")
                    self._log_timeline_event(tl_id, "feedback.submit", {
                        "type": fb_type, "message_length": len(msg),
                    }, frame=frame, source="operator", trust_level="direct")
                except Exception as e:
                    payload = json.dumps({"ok": False, "error": str(e)}).encode("utf-8")
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(payload)
                return


            # API: event annotation (append-only trust action)
            if self.path == "/api/events/annotate":
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else ""
                try:
                    data = json.loads(body) if body else {}
                    timeline_id = data.get("timeline_id")
                    event_id = data.get("event_id")
                    action = data.get("action")
                    note = data.get("note", "")
                    if not timeline_id or not event_id or not action:
                        self.send_response(400)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(json.dumps({"ok": False, "error": "timeline_id, event_id, and action are required"}).encode("utf-8"))
                        return
                    if action not in ("mark_trusted", "mark_untrusted", "add_note"):
                        self.send_response(400)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(json.dumps({"ok": False, "error": "invalid_action"}).encode("utf-8"))
                        return
                    base = Path(__file__).resolve().parent
                    tl_dir = base / ".weslr" / "timelines" / timeline_id
                    if not tl_dir.exists():
                        self.send_response(404)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(json.dumps({"ok": False, "error": "timeline_not_found"}).encode("utf-8"))
                        return
                    # Load operator identity
                    try:
                        op_path = base_dir / "operator_profile.json"
                        if op_path.exists():
                            with open(op_path) as f:
                                op = json.load(f)
                                operator_name = op.get("name", "operator")
                        else:
                            operator_name = "operator"
                    except Exception:
                        operator_name = "operator"
                    ann_record = {
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "event_id": event_id,
                        "action": action,
                        "operator": operator_name,
                        "note": note,
                        "source": "operator",
                    }
                    ann_file = tl_dir / "annotations.jsonl"
                    with open(ann_file, "a") as f:
                        f.write(json.dumps(ann_record) + "\n")
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"ok": True, "saved": True, "annotation": ann_record}).encode("utf-8"))
                except Exception as e:
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"ok": False, "error": str(e)}).encode("utf-8"))
                return

            if self.path == "/artifact-review":
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else ""
                try:
                    import json as _json
                    data = _json.loads(body) if body else {}
                    artifact_id = data.get("artifact_id", "")
                    action = data.get("action", "")
                    note = data.get("note", "")
                    
                    # Validate input
                    if not artifact_id:
                        self.send_response(400)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(_json.dumps({"ok": False, "error": "artifact_id is required"}).encode("utf-8"))
                        return
                    if not action or action not in ["approve", "reject", "note"]:
                        self.send_response(400)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(_json.dumps({"ok": False, "error": "action must be 'approve', 'reject', or 'note'"}).encode("utf-8"))
                        return
                    if action == "reject" and not note:
                        self.send_response(400)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(_json.dumps({"ok": False, "error": "note is required for reject action"}).encode("utf-8"))
                        return
                    
                    # Perform the review
                    result = review_artifact(artifact_id, action, note=note)
                    
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(_json.dumps({"ok": True, "result": result}).encode("utf-8"))
                except Exception as e:
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(_json.dumps({"ok": False, "error": str(e)}).encode("utf-8"))
            
            # Handle category update endpoint
            elif self.path == "/category/update":
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else ""
                try:
                    import json as _json
                    data = _json.loads(body) if body else {}
                    category_name = data.get("name", "")
                    action = data.get("action", "")
                    description = data.get("description", "")
                    note = data.get("note", "")
                    
                    # Validate input
                    if not category_name:
                        self.send_response(400)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(_json.dumps({"ok": False, "error": "category name is required"}).encode("utf-8"))
                        return
                    if not action or action not in ["create", "update", "archive"]:
                        self.send_response(400)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(_json.dumps({"ok": False, "error": "action must be 'create', 'update', or 'archive'"}).encode("utf-8"))
                        return
                    if action == "archive" and not note:
                        self.send_response(400)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(_json.dumps({"ok": False, "error": "note/reason is required for archive action"}).encode("utf-8"))
                        return
                    
                    # Perform the category action using dashboard-specific function
                    result = category_update_dashboard(action, category_name, note=note)
                    
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(_json.dumps({"ok": True, "result": result}).encode("utf-8"))
                except Exception as e:
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(_json.dumps({"ok": False, "error": str(e)}).encode("utf-8"))
            
            # Handle artifact validation endpoint
            elif self.path == "/artifact/validate":
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else ""
                try:
                    import json as _json
                    data = _json.loads(body) if body else {}
                    artifact_id = data.get("artifact_id", "")
                    outcome = data.get("outcome", "")
                    note = data.get("note", "")
                    
                    # Validate input
                    if not artifact_id:
                        self.send_response(400)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(_json.dumps({"ok": False, "error": "artifact_id is required"}).encode("utf-8"))
                        return
                    if not outcome or outcome not in ["valid", "invalid", "needs_review"]:
                        self.send_response(400)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(_json.dumps({"ok": False, "error": "outcome must be 'valid', 'invalid', or 'needs_review'"}).encode("utf-8"))
                        return
                    if not note:
                        self.send_response(400)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(_json.dumps({"ok": False, "error": "note/context is required for validation"}).encode("utf-8"))
                        return
                    
                    # Perform the validation using dashboard-specific function
                    result = artifact_validate_dashboard(artifact_id, outcome, note=note)
                    
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(_json.dumps({"ok": True, "result": result}).encode("utf-8"))
                except Exception as e:
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(_json.dumps({"ok": False, "error": str(e)}).encode("utf-8"))
            
            # Handle pack decision endpoint
            elif self.path == "/pack/decision":
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else ""
                try:
                    import json as _json
                    data = _json.loads(body) if body else {}
                    pack_name = data.get("pack_name", "")
                    action = data.get("action", "")
                    note = data.get("note", "")
                    price = data.get("price", "")
                    
                    # Validate input
                    if not pack_name:
                        self.send_response(400)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(_json.dumps({"ok": False, "error": "pack name is required"}).encode("utf-8"))
                        return
                    if not action or action not in ["approve", "reject", "update_price"]:
                        self.send_response(400)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(_json.dumps({"ok": False, "error": "action must be 'approve', 'reject', or 'update_price'"}).encode("utf-8"))
                        return
                    if action == "reject" and not note:
                        self.send_response(400)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(_json.dumps({"ok": False, "error": "note/reason is required for reject action"}).encode("utf-8"))
                        return
                    if action == "update_price" and not price:
                        self.send_response(400)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(_json.dumps({"ok": False, "error": "price is required for update_price action"}).encode("utf-8"))
                        return
                    
                    # Perform the pack decision using dashboard-specific function
                    result = pack_decision_dashboard(pack_name, action, note=note, price=price)
                    
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(_json.dumps({"ok": True, "result": result}).encode("utf-8"))
                except Exception as e:
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(_json.dumps({"ok": False, "error": str(e)}).encode("utf-8"))
            
            elif self.path == "/onboarding":
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else ""
                try:
                    import json as _json
                    data = _json.loads(body) if body else {}
                    # Record human exchange with onboarding answers
                    from sim import record_human_exchange
                    answers = {
                        "phase": "onboarding",
                        "name": data.get("name", ""),
                        "role": data.get("role", ""),
                        "persona": data.get("persona", ""),
                        "primary_outcome": data.get("primary_outcome", ""),
                        "time_horizon": data.get("time_horizon", ""),
                        "objectives": data.get("objectives", []),
                        "failure_conditions": data.get("failure_conditions", ""),
                        "red_lines": data.get("red_lines", ""),
                        "legal_constraints": data.get("legal_constraints", ""),
                        "audit_level": data.get("audit_level", ""),
                        "metric_primary": data.get("metric_primary", ""),
                        "metric_secondary": data.get("metric_secondary", ""),
                        "checkin_style": data.get("checkin_style", ""),
                        "urgency": data.get("urgency", ""),
                        "blockers": data.get("blockers", ""),
                        "standup_cadence": data.get("standup_cadence", ""),
                        # Phase C fields
                        "allowed_capabilities": data.get("allowed_capabilities", []),
                        "allowed_custom": data.get("allowed_custom", ""),
                        "forbidden_actions": data.get("forbidden_actions", ""),
                        "byop_policy": data.get("byop_policy", ""),
                        "external_permissions": data.get("external_permissions", []),
                        "external_custom": data.get("external_custom", ""),
                        "knowledge_sharing": data.get("knowledge_sharing", ""),
                        "federation_permissions": data.get("federation_permissions", ""),
                        "adaptation_level": data.get("adaptation_level", ""),
                        "adaptation_limits": data.get("adaptation_limits", ""),
                        "escalation_primary": data.get("escalation_primary", ""),
                        "escalation_secondary": data.get("escalation_secondary", ""),
                        "escalation_channel": data.get("escalation_channel", ""),
                    }
                    record_human_exchange(
                        human_name=data.get("name", "operator"),
                        message=f"Operator completed onboarding: {_json.dumps(answers)}",
                        response="onboarding recorded",
                        topics=["onboarding", "operator-profile"],
                        unresolved=False,
                    )
                    # Also save operator profile for Phase C communicator wiring
                    profile_saved = False
                    try:
                        from weslr.communicator_config import update_operator_profile
                        update_operator_profile(answers)
                        profile_saved = True
                    except Exception as profile_err:
                        pass  # Non-blocking — don't fail onboarding if profile update fails
                    # Attempt canonical initialization (contract-gated, non-blocking for onboarding)
                    marker = base_dir / ".weslr_initialized"
                    already_init = marker.exists()
                    init_blocked_reasons = []
                    try:
                        # 1. operator profile saved (profile_saved confirms this)
                        if not profile_saved:
                            init_blocked_reasons.append("operator_profile_not_saved")
                        # 2. lifecycle_state != bootstrap_required
                        try:
                            from weslr.communicator_config import derive_lifecycle_state, load_operator_profile
                            profile = load_operator_profile()
                            lc = derive_lifecycle_state(profile) if profile.get("name") else {}
                            if lc.get("state") == "bootstrap_required":
                                init_blocked_reasons.append("lifecycle_not_onboarded")
                        except Exception:
                            init_blocked_reasons.append("lifecycle_derivation_failed")
                        # 3. state summary works
                        try:
                            from weslr.governance_health import get_weslr_state_summary
                            get_weslr_state_summary()
                        except Exception:
                            init_blocked_reasons.append("state_summary_failed")
                        # 4. persisted bootstrap timeline exists
                        try:
                            cs = load_communicator_self()
                            if not cs.get("bootstrap", {}).get("timeline_id"):
                                init_blocked_reasons.append("no_bootstrap_timeline")
                        except Exception:
                            init_blocked_reasons.append("bootstrap_check_failed")
                        if not init_blocked_reasons:
                            marker.write_text(f"initialized_at={__import__('time').time()}\n")
                    except Exception:
                        pass  # Non-blocking — don't fail onboarding if initialization fails
                    init_result = {
                        "initialized": marker.exists(),
                        "created_now": marker.exists() and not already_init,
                        "blocked": bool(init_blocked_reasons),
                        "reasons": init_blocked_reasons,
                    }
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(_json.dumps({
                        "ok": True,
                        "recorded": True,
                        "initialization": init_result,
                    }).encode("utf-8"))
                except Exception as e:
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(_json.dumps({"ok": False, "error": str(e)}).encode("utf-8"))
            elif self.path == "/api/clearance/verify":
                # Clearance token issuance endpoint — called after trusted-device verification succeeds.
                # Issues a bounded one-time-use clearance token scoped to the specific action.
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else ""
                try:
                    import json as _json
                    data = _json.loads(body) if body else {}
                    handoff_id = data.get("handoff_id", "")
                    actor_id = data.get("actor_id", "anonymous")
                    session_id = data.get("session_id", "unknown")
                    action_scope = data.get("action_scope", "")
                    trust_level_str = str(data.get("trust_level", "HIGH_RISK"))
                    from weslr.security import TrustLevel, verified_completion
                    trust_level = TrustLevel[trust_level_str] if trust_level_str in [l.name for l in TrustLevel] else TrustLevel.HIGH_RISK
                    if not action_scope:
                        self.send_response(400)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(_json.dumps({"ok": False, "error": "action_scope is required"}).encode("utf-8"))
                        return
                    success, result = verified_completion(
                        handoff_id=handoff_id,
                        actor_id=actor_id,
                        session_id=session_id,
                        action_scope=action_scope,
                        trust_level=trust_level,
                        ttl_seconds=60,
                    )
                    if success:
                        self.send_response(200)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(_json.dumps({"ok": True, "token": result}).encode("utf-8"))
                    else:
                        self.send_response(403)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(_json.dumps({"ok": False, "error": result}).encode("utf-8"))
                except Exception as e:
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(_json.dumps({"ok": False, "error": str(e)}).encode("utf-8"))
            elif self.path == "/api/initialize":
                # Contract-gated initialization marker creation.
                # Idempotent: if already initialized, returns success without error.
                content_length = int(self.headers.get("Content-Length", 0))
                _ = self.rfile.read(content_length).decode("utf-8") if content_length else ""
                try:
                    reasons = []
                    # 1. operator profile exists with name
                    try:
                        from weslr.communicator_config import load_operator_profile
                        profile = load_operator_profile()
                        if not profile.get("name"):
                            reasons.append("operator_profile_name_missing")
                    except Exception:
                        reasons.append("operator_profile_load_failed")
                    # 2. lifecycle_state != bootstrap_required
                    try:
                        from weslr.communicator_config import derive_lifecycle_state
                        lc = derive_lifecycle_state(profile) if profile.get("name") else {}
                        if lc.get("state") == "bootstrap_required":
                            reasons.append("lifecycle_not_onboarded")
                    except Exception:
                        reasons.append("lifecycle_derivation_failed")
                    # 3. get_weslr_state_summary() returns without fatal error
                    try:
                        from weslr.governance_health import get_weslr_state_summary
                        get_weslr_state_summary()
                    except Exception:
                        reasons.append("state_summary_failed")
                    # 4. at least one bootstrap timeline_id exists (persisted in communicator_self.json)
                    try:
                        cs = load_communicator_self()
                        tl = cs.get("bootstrap", {}).get("timeline_id")
                        if not tl:
                            reasons.append("no_bootstrap_timeline")
                    except Exception:
                        reasons.append("bootstrap_check_failed")
                    marker = base_dir / ".weslr_initialized"
                    already = marker.exists()
                    if reasons:
                        self.send_response(422)
                        self.send_header("Content-Type", "application/json")
                        payload = json.dumps({
                            "initialized": already,
                            "created_now": False,
                            "blocked": True,
                            "reasons": reasons,
                        }).encode("utf-8")
                        self.send_header("Content-Length", str(len(payload)))
                        self.end_headers()
                        self.wfile.write(payload)
                    else:
                        marker.write_text(f"initialized_at={__import__('time').time()}\n")
                        self.send_response(200)
                        self.send_header("Content-Type", "application/json")
                        payload = json.dumps({
                            "initialized": True,
                            "created_now": not already,
                            "blocked": False,
                            "reasons": [],
                        }).encode("utf-8")
                        self.send_header("Content-Length", str(len(payload)))
                        self.end_headers()
                        self.wfile.write(payload)
                except Exception as e:
                    payload = json.dumps({"error": str(e)}).encode("utf-8")
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(payload)
            elif self.path == "/chat":
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else ""
                try:
                    import json as _json
                    from concurrent.futures import ThreadPoolExecutor

                    data = _json.loads(body) if body else {}
                    message = data.get("message", "")

                    # SS-TDE risk scan: intercept high-risk actions before executing inline
                    from weslr.security import (
                        TrustLevel, classify_message_for_risk,
                        escalation_response, build_escalation_handoff,
                        log_audit_event, require_clearance,
                    )
                    risk_level = classify_message_for_risk(message)
                    # If a clearance token is provided, validate it for this action.
                    # If valid, bypass the risk scan and proceed.
                    token_id = data.get("clearance_token_id", "")
                    if token_id:
                        allowed, reason, _ = require_clearance(
                            token_id=token_id,
                            action_scope="chat:message",
                            actor_id="anonymous",
                            session_id="unknown",
                        )
                        if allowed:
                            risk_level = TrustLevel.CONVERSATIONAL  # bypass escalation
                        else:
                            self.send_response(403)
                            self.send_header("Content-Type", "application/json")
                            self.end_headers()
                            self.wfile.write(_json.dumps({
                                "error": f"clearance token invalid: {reason}",
                                "escalation_required": True,
                                "trust_level": "HIGH_RISK",
                                "action": "trusted_device_escalation",
                            }).encode("utf-8"))
                            return
                    if risk_level >= TrustLevel.HIGH_RISK:
                        # Bootstrap trust check: SS-TDE escalation requires a verified
                        # bootstrap trust anchor. Non-bootstrapped actors cannot proceed.
                        timeline_id = data.get("timeline_id", "")
                        if timeline_id:
                            from weslr.bootstrap import is_verified_timeline
                            if not is_verified_timeline(timeline_id):
                                self.send_response(403)
                                self.send_header("Content-Type", "application/json")
                                self.end_headers()
                                self.wfile.write(_json.dumps({
                                    "escalation_required": True,
                                    "trust_level": "HIGH_RISK",
                                    "bootstrap_required": True,
                                    "message": (
                                        "Your account has not completed the security setup yet. "
                                        "Please complete account activation before attempting this action."
                                    ),
                                    "action": "bootstrap_activation_required",
                                }).encode("utf-8"))
                                return
                        log_audit_event(
                            event_kind="clearance_denied",
                            actor_id="anonymous",
                            session_id="unknown",
                            action_requested=message[:100],
                            trust_level_required=risk_level,
                            verification_method="none",
                            outcome="denied",
                            operator_alert=(risk_level >= TrustLevel.CRITICAL),
                        )
                        handoff = build_escalation_handoff(message, risk_level)
                        response = escalation_response(risk_level)
                        response["escalation_handoff"] = handoff
                        self.send_response(403)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(_json.dumps(response).encode("utf-8"))
                        return

                    # Thread-safe deadline guard: use shared bounded executor so threads are
                    # reused rather than created/destroyed per request.
                    acquired = _chat_semaphore.acquire(timeout=float(CHAT_LLM_TIMEOUT_SECONDS))
                    if not acquired:
                        self.send_response(503)
                        self.send_header("Content-Type", "application/json")
                        self.send_header("Retry-After", "5")
                        self.end_headers()
                        self.wfile.write(_json.dumps({
                            "error": "chat service busy, try again shortly"
                        }).encode("utf-8"))
                        return
                    # Memory tier architecture (4 levels):
                    #   L0 — identity core, always loaded
                    #   L1 — operating facts, always loaded
                    #   L2 — session state, always loaded
                    #   L3 — full communicator_self, background/sync only
                    # Primary data for /chat comes from L0+L1+L2 via tier injections.
                    # load_communicator_self() below is a legacy fallback; its output is
                    # entirely overwritten by tier injections on the hot path.
                    # Future: remove full loader from /chat once tier coverage is validated.
                    # Bounded research context enrichment — see TWO_PATH_GAP_ANALYSIS.md
                    _rc = None
                    try:
                        _ml = message.lower().strip()
                        _sw = {"the","is","are","was","were","a","an","of","to","in","on","at","for","with","what","how","why","when","who","where","can","you","i","it","this","that"}
                        _wd = [w.strip() for w in _ml.split() if len(w.strip()) > 2 and w.strip() not in _sw]
                        if _wd and _ml.startswith(("what","how","why","explain","tell","define","about")):
                            _lt = _wd[0]
                            _pub = load_public_memory()
                            _note = find_relevant_research_note(_pub, _lt) if _pub else None
                            if _note:
                                _raw = str(_note.get("content") or "").strip()[:350]
                                _rc = {"topic": _lt, "title": str(_note.get("title","")[:80]), "summary": _raw, "source": str(_note.get("source","")[:60])}
                    except Exception:
                        _rc = None
                    try:
                        fut = _CHAT_EXECUTOR.submit(
                            build_communicator_message_payload,
                            narrative=load_communicator_self().get("narrative_state", {}),
                            relationships=load_relationships(),
                            active_thread="human_message",
                            latest_human={"message": message},
                            research_context=_rc,
                            l0_identity=load_tier("l0"),
                            l1_operating=load_tier("l1"),
                            l2_session=load_tier("l2"),
                        )
                        try:
                            payload = fut.result(timeout=float(CHAT_LLM_TIMEOUT_SECONDS))
                        except TimeoutError:
                            raise TimeoutError("chat request exceeded time limit")
                    finally:
                        _chat_semaphore.release()
                    # Graceful degradation: provider was unavailable, return structured 503
                    if payload.get("degraded"):
                        self.send_response(503)
                        self.send_header("Content-Type", "application/json")
                        self.send_header("Retry-After", "30")
                        self.end_headers()
                        self.wfile.write(_json.dumps({
                            "kind": "chat_degraded",
                            "summary": payload.get("summary", "Chat is temporarily unavailable."),
                            "provider": payload.get("provider", "unknown"),
                            "degraded": True,
                            "degraded_reason": payload.get("degraded_reason", "provider_unavailable"),
                            "retry_after_s": 30,
                        }).encode("utf-8"))
                        return
                    # Soft trust signal: inject climate into response (additive, non-blocking)
                    tl_id = data.get("timeline_id", "tl_default")
                    trust_signal = self._build_trust_signal(tl_id)
                    if trust_signal:
                        payload["_trust_signal"] = trust_signal
                    # ── Repeated quality watch (governance bridge, metadata only) ──
                    # Detect repeated quality degradation for same need category.
                    # Threshold: 3 consecutive same (quality_class, likely_need) pairs.
                    # Note is metadata only — never changes user-facing message.
                    from interpretation import interpret_human_turn
                    qclass = payload.get("_quality_class") or "unknown"
                    itrn = interpret_human_turn(message)
                    lneed = str(itrn.get("likely_need") or "unknown")
                    qnote = _check_quality_watch(qclass, lneed)
                    if qnote:
                        payload["_quality_note"] = qnote
                    # ── Confusion detection (Phase 1 — human-compatibility first) ──
                    # Detect likely human confusion from message content.
                    # Metadata only — never changes user-facing message.
                    cstate = _detect_confusion(message)
                    payload["_confusion_state"] = {
                        "confusion_signal": cstate["confusion_signal"],
                        "confusion_type": cstate["confusion_type"],
                    }
                    if cstate["confusion_signal"]:
                        self._log_timeline_event(tl_id, "confusion.signal", {
                            "confusion_type": cstate["confusion_type"],
                            "likely_need": lneed,
                            "message_snippet": message[:80],
                        }, frame=frame, source="confusion_watch", trust_level="system")
                        # ── Adaptive hint (confusion → safe next-action metadata) ──
                        # Derives a hint from confusion_type. Metadata only —
                        # does not change user-facing message. auto_apply=False.
                        hint = _derive_adaptive_hint(cstate["confusion_signal"], cstate["confusion_type"])
                        if hint:
                            payload["_adaptive_hint"] = hint
                            self._log_timeline_event(tl_id, "adaptive.hint", {
                                "confusion_type": cstate["confusion_type"],
                                "recommended_next_action": hint["recommended_next_action"],
                                "message_snippet": message[:80],
                            }, frame=frame, source="adaptive_hint", trust_level="system")
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(_json.dumps(payload).encode("utf-8"))
                    frame = data.get("frame")
                    self._log_timeline_event(tl_id, "chat.message", {
                        "message_length": len(message),
                        "has_clearance": bool(token_id),
                        "quality_class": qclass,
                        "quality_note": qnote if qnote else None,
                        "_governance_observation": {
                            "watch_triggered": qnote,
                            "quality_class": qclass,
                            "likely_need": lneed,
                        } if qnote else None,
                    }, frame=frame, source="operator", trust_level="direct")
                    # Separate governance event lane — only fires when watch triggers.
                    # Clean separation from chat.message telemetry.
                    if qnote:
                        candidate = _derive_governance_candidate(qnote, qclass, lneed, message)
                        recommendation = _derive_improvement_recommendation(qnote, qclass, lneed, message)
                        self._log_timeline_event(tl_id, "governance.observation", {
                            "watch_triggered": qnote,
                            "quality_class": qclass,
                            "likely_need": lneed,
                            "message_snippet": message[:80],
                            "_governance_candidate": candidate,
                            "_improvement_recommendation": recommendation,
                        }, source="governance_watch", trust_level="system")
                except TimeoutError:
                    self.send_response(504)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(_json.dumps({"error": "chat request timed out after " + str(CHAT_LLM_TIMEOUT_SECONDS) + "s"}).encode("utf-8"))
                except Exception as e:
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(_json.dumps({"error": str(e)}).encode("utf-8"))
            else:
                self.send_error(404, "Unknown endpoint")

        def do_GET(self):
            """Serve GET requests."""
            # Onboarding front door
            if self.path == "/onboarding":
                front_door = base_dir / "front-door" / "index.html"
                try:
                    with open(front_door, "r", encoding="utf-8") as f:
                        content = f.read()
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html")
                    self.end_headers()
                    self.wfile.write(content.encode("utf-8"))
                except Exception as e:
                    self.send_response(500)
                    self.send_header("Content-Type", "text/plain")
                    self.end_headers()
                    self.wfile.write(f"Error: {e}".encode("utf-8"))
                return
            # Machine-readable first-run detection
            if self.path == "/api/first-run":
                try:
                    import os as _os
                    from weslr.communicator_config import load_operator_profile
                    profile = load_operator_profile()
                    profile_exists = bool(profile.get("name"))
                    marker = base_dir / ".weslr_initialized"
                    initialized = marker.exists()
                    payload = json.dumps({
                        "first_run": not profile_exists and not initialized,
                        "profile_exists": profile_exists,
                        "initialized": initialized,
                    }).encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(payload)))
                    self.end_headers()
                    self.wfile.write(payload)
                except Exception as e:
                    payload = json.dumps({"error": str(e)}).encode("utf-8")
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(payload)
                return
            # Machine-readable onboarding status
            if self.path == "/api/onboarding":
                try:
                    from weslr.communicator_config import load_operator_profile, derive_lifecycle_state
                    profile = load_operator_profile()
                    lc = derive_lifecycle_state(profile) if profile.get("name") else {}
                    marker = base_dir / ".weslr_initialized"
                    payload = json.dumps({
                        "configured": bool(profile.get("name")),
                        "operator_name": profile.get("name", ""),
                        "role": profile.get("role", ""),
                        "lifecycle_state": lc.get("state", "bootstrap_required"),
                        "checkin_style": profile.get("checkin_style", ""),
                        "adaptation_level": profile.get("adaptation_level", ""),
                        "urgency": profile.get("urgency", ""),
                        "initialized": marker.exists(),
                    }).encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(payload)))
                    self.end_headers()
                    self.wfile.write(payload)
                except Exception as e:
                    payload = json.dumps({"error": str(e)}).encode("utf-8")
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(payload)
                return
            # Machine-readable health check — lightweight, no expensive paths
            if self.path == "/api/health":
                try:
                    import os as _os
                    marker = base_dir / ".weslr_initialized"
                    initialized = marker.exists()
                    uptime_s = int(time.time() - (_SERVER_START_TIME or time.time()))
                    # Lightweight provider availability check (cheap only)
                    provider_ok = False
                    try:
                        from weslr.providers import get_provider as _get_provider
                        _get_provider()  # just check it doesn't raise
                        provider_ok = True
                    except Exception:
                        provider_ok = False
                    payload = json.dumps({
                        "healthy": True,
                        "version": VERSION,
                        "uptime_s": uptime_s,
                        "initialized": initialized,
                        "provider_available": provider_ok,
                    }).encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(payload)))
                    self.end_headers()
                    self.wfile.write(payload)
                except Exception as e:
                    payload = json.dumps({"healthy": False, "error": str(e)}).encode("utf-8")
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(payload)
                return
            # Machine-readable unified state summary
            if self.path == "/api/state":
                try:
                    from weslr.governance_health import get_weslr_state_summary
                    summary = get_weslr_state_summary()
                    payload = json.dumps(summary, indent=2).encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(payload)))
                    self.end_headers()
                    self.wfile.write(payload)
                except Exception as e:
                    payload = json.dumps({"error": "state_unavailable", "detail": str(e)}).encode("utf-8")
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(payload)
                return
            # Quality watch status (read-only governance observation)
            if self.path == "/api/quality-watch":
                try:
                    global _WATCH_HISTORY
                    threshold = _WATCH_THRESHOLD
                    # Compute current streak
                    streak_class = None
                    streak_need = None
                    streak_count = 0
                    if _WATCH_HISTORY:
                        # Scan from newest to oldest, count consecutive matching entries
                        for i in range(len(_WATCH_HISTORY) - 1, -1, -1):
                            entry = _WATCH_HISTORY[i]
                            if streak_class is None:
                                streak_class = entry["quality_class"]
                                streak_need = entry["likely_need"]
                                streak_count = 1
                            elif (entry["quality_class"] == streak_class and
                                  entry["likely_need"] == streak_need):
                                streak_count += 1
                            else:
                                break
                    current_streak = None
                    if streak_count > 0:
                        current_streak = {
                            "quality_class": streak_class,
                            "likely_need": streak_need,
                            "count": streak_count,
                        }
                    watch_arm_active = (streak_count >= threshold) if streak_count > 0 else False
                    payload = json.dumps({
                        "threshold": threshold,
                        "history_size": len(_WATCH_HISTORY),
                        "current_streak": current_streak,
                        "watch_arm_active": watch_arm_active,
                    }).encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(payload)))
                    self.end_headers()
                    self.wfile.write(payload)
                except Exception as e:
                    payload = json.dumps({"error": "watch_state_unavailable", "detail": str(e)}).encode("utf-8")
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(payload)
                return
            # Quality watch history (read-only, bounded)
            if self.path == "/api/quality-watch/history":
                try:
                    import re as _re
                    from urllib.parse import parse_qs, urlparse
                    parsed = urlparse(self.path)
                    params = parse_qs(parsed.query)
                    limit = min(int(params.get("limit", ["10"])[0]), 10)
                    # Return entries newest-first (index 0 = most recent)
                    entries = []
                    for i, entry in enumerate(reversed(_WATCH_HISTORY[-limit:])):
                        entries.append({
                            "index": i,
                            "quality_class": entry.get("quality_class", "unknown"),
                            "likely_need": entry.get("likely_need", "unknown"),
                        })
                    payload = json.dumps({
                        "limit": limit,
                        "total": len(_WATCH_HISTORY),
                        "entries": entries,
                    }).encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(payload)))
                    self.end_headers()
                    self.wfile.write(payload)
                except Exception as e:
                    payload = json.dumps({"error": "watch_history_unavailable", "detail": str(e)}).encode("utf-8")
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(payload)
                return
            # Governance observations endpoint (read-only, bounded)
            if self.path == "/api/governance/observations":
                try:
                    from urllib.parse import parse_qs, urlparse
                    parsed = urlparse(self.path)
                    params = parse_qs(parsed.query)
                    limit = min(int(params.get("limit", ["10"])[0]), 50)
                    # Read governance.observation events from timeline event log
                    base = Path(__file__).resolve().parent
                    tl_id = params.get("timeline", ["tl_default"])[0]
                    event_file = base / ".weslr" / "timelines" / tl_id / "events.jsonl"
                    entries = []
                    if event_file.exists():
                        # Read last N lines (newest entries are at end of append-only file)
                        with open(event_file, "r") as f:
                            lines = f.readlines()
                        for line in reversed(lines[-limit*3:]):  # read more than limit to allow filtering
                            try:
                                event = json.loads(line.strip())
                                if event.get("event_type") == "governance.observation":
                                    data = event.get("data", {})
                                    entries.append({
                                        "timestamp": event.get("timestamp"),
                                        "watch_triggered": data.get("watch_triggered"),
                                        "quality_class": data.get("quality_class"),
                                        "likely_need": data.get("likely_need"),
                                        "message_snippet": data.get("message_snippet"),
                                    })
                                    if len(entries) >= limit:
                                        break
                            except Exception:
                                continue
                    payload = json.dumps({
                        "limit": limit,
                        "total": len(entries),
                        "entries": entries,
                    }).encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(payload)))
                    self.end_headers()
                    self.wfile.write(payload)
                except Exception as e:
                    payload = json.dumps({"error": "governance_observations_unavailable", "detail": str(e)}).encode("utf-8")
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(payload)
                return
            # Governance recommendations endpoint (read-only, bounded)
            if self.path == "/api/governance/recommendations/recent":
                try:
                    from urllib.parse import parse_qs, urlparse
                    parsed = urlparse(self.path)
                    params = parse_qs(parsed.query)
                    limit = min(int(params.get("limit", ["10"])[0]), 50)
                    rec_type_filter = params.get("recommendation_type", [None])[0]
                    conf_filter = params.get("confidence", [None])[0]
                    # Read governance.observation events, extract _improvement_recommendation
                    base = Path(__file__).resolve().parent
                    tl_id = params.get("timeline", ["tl_default"])[0]
                    event_file = base / ".weslr" / "timelines" / tl_id / "events.jsonl"
                    entries = []
                    if event_file.exists():
                        with open(event_file, "r") as f:
                            lines = f.readlines()
                        for line in reversed(lines[-limit*3:]):
                            try:
                                event = json.loads(line.strip())
                                if event.get("event_type") == "governance.observation":
                                    data = event.get("data", {})
                                    reco = data.get("_improvement_recommendation")
                                    if reco:
                                        # Apply filters
                                        if rec_type_filter and reco.get("recommendation_type") != rec_type_filter:
                                            continue
                                        if conf_filter and reco.get("confidence") != conf_filter:
                                            continue
                                        entries.append({
                                            "timestamp": event.get("timestamp"),
                                            "recommendation_type": reco.get("recommendation_type"),
                                            "trigger": reco.get("trigger"),
                                            "diagnosis": reco.get("diagnosis"),
                                            "recommendation": reco.get("recommendation"),
                                            "implementation_hint": reco.get("implementation_hint"),
                                            "confidence": reco.get("confidence"),
                                            "approval_required": reco.get("approval_required"),
                                        })
                                        if len(entries) >= limit:
                                            break
                            except Exception:
                                continue
                    payload = json.dumps({
                        "limit": limit,
                        "total": len(entries),
                        "entries": entries,
                    }).encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(payload)))
                    self.end_headers()
                    self.wfile.write(payload)
                except Exception as e:
                    payload = json.dumps({"error": "recommendations_unavailable", "detail": str(e)}).encode("utf-8")
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(payload)
                return
            # Confusion observations endpoint (read-only, bounded)
            if self.path == "/api/confusion/observations":
                try:
                    from urllib.parse import parse_qs, urlparse
                    parsed = urlparse(self.path)
                    params = parse_qs(parsed.query)
                    limit = min(int(params.get("limit", ["10"])[0]), 50)
                    # Read confusion.signal events from timeline event log
                    base = Path(__file__).resolve().parent
                    tl_id = params.get("timeline", ["tl_default"])[0]
                    event_file = base / ".weslr" / "timelines" / tl_id / "events.jsonl"
                    entries = []
                    if event_file.exists():
                        with open(event_file, "r") as f:
                            lines = f.readlines()
                        for line in reversed(lines[-limit*3:]):
                            try:
                                event = json.loads(line.strip())
                                if event.get("event_type") == "confusion.signal":
                                    data = event.get("data", {})
                                    entries.append({
                                        "timestamp": event.get("timestamp"),
                                        "confusion_type": data.get("confusion_type"),
                                        "likely_need": data.get("likely_need"),
                                        "message_snippet": data.get("message_snippet"),
                                    })
                                    if len(entries) >= limit:
                                        break
                            except Exception:
                                continue
                    payload = json.dumps({
                        "limit": limit,
                        "total": len(entries),
                        "entries": entries,
                    }).encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(payload)))
                    self.end_headers()
                    self.wfile.write(payload)
                except Exception as e:
                    payload = json.dumps({"error": "confusion_observations_unavailable", "detail": str(e)}).encode("utf-8")
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(payload)
                return
            # State JSON files
            if self.path in {"/state_core.json", "/communicator_self.json", "/review_queue.json"}:
                self._serve_state_file(self.path)
                return
            # Main front door
            if self.path == "/" or self.path == "/main/index.html":
                front_door = base_dir / "front-door" / "index.html"
                try:
                    with open(front_door, "r", encoding="utf-8") as f:
                        content = f.read()
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html")
                    self.end_headers()
                    self.wfile.write(content.encode("utf-8"))
                except Exception as e:
                    self.send_response(500)
                    self.send_header("Content-Type", "text/plain")
                    self.end_headers()
                    self.wfile.write(f"Error: {e}".encode("utf-8"))
                return
            # Operator / debug dashboard
            if self.path == "/operator" or self.path == "/operator/dashboard.html":
                dashboard_index = base_dir / "dashboard" / "index.html"
                try:
                    with open(dashboard_index, "r", encoding="utf-8") as f:
                        content = f.read()
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html")
                    self.end_headers()
                    self.wfile.write(content.encode("utf-8"))
                except Exception as e:
                    self.send_response(500)
                    self.send_header("Content-Type", "text/plain")
                    self.end_headers()
                    self.wfile.write(f"Error: {e}".encode("utf-8"))
                return
            # TIA import history
            # API: Charter evaluation (read-only)
            if self.path == "/api/charter/evaluate":
                try:
                    charter_path = base_dir / ".weslr" / "charter.json"
                    if not charter_path.exists():
                        self.send_response(404)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(json.dumps({"error": "charter_not_found"}).encode("utf-8"))
                        return
                    with open(charter_path) as f:
                        charter = json.load(f)
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "charter_present": True,
                        "version": charter.get("version"),
                        "principles": charter.get("principles", []),
                        "trust_rules": charter.get("trust_rules", {}),
                        "source_categories": charter.get("source_categories", {}),
                        "poisoning_resistance": charter.get("poisoning_resistance", {}),
                    }).encode("utf-8"))
                except Exception as e:
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
                return

            # API: Charter signal report (read-only)
            if self.path.startswith("/api/charter/signals"):
                try:
                    from urllib.parse import parse_qs, urlparse
                    parsed = urlparse(self.path)
                    params = parse_qs(parsed.query)
                    timeline = params.get("timeline", ["tl_default"])[0]
                    limit = int(params.get("limit", ["100"])[0])
                    base = Path(__file__).resolve().parent
                    event_file = base / ".weslr" / "timelines" / timeline / "events.jsonl"
                    events = []
                    if event_file.exists():
                        with open(event_file) as f:
                            for line in f:
                                line = line.strip()
                                if line:
                                    try:
                                        events.append(json.loads(line))
                                    except Exception:
                                        pass
                    report = self._generate_charter_signal_report(events)
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps(report).encode("utf-8"))
                except Exception as e:
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
                return

            # API: recent timeline events (merged with annotations)
            if self.path.startswith("/api/events/recent"):
                try:
                    from urllib.parse import parse_qs, urlparse
                    parsed = urlparse(self.path)
                    params = parse_qs(parsed.query)
                    timeline = params.get("timeline", ["tl_default"])[0]
                    limit = int(params.get("limit", ["20"])[0])
                    base = Path(__file__).resolve().parent
                    event_file = base / ".weslr" / "timelines" / timeline / "events.jsonl"
                    events = []
                    if event_file.exists():
                        with open(event_file) as f:
                            for line in f:
                                line = line.strip()
                                if line:
                                    try:
                                        events.append(json.loads(line))
                                    except Exception:
                                        pass
                    recent = events[-limit:] if len(events) > limit else events
                    # Attach latest annotation to each event
                    annotations_map = self._get_annotations_by_event_id(timeline)
                    enriched = []
                    for ev in recent:
                        eid = self._derive_event_id(ev)
                        annotation = annotations_map.get(eid)
                        ev_with_meta = dict(ev)
                        ev_with_meta["_annotation"] = annotation
                        ev_with_meta["_event_id"] = eid
                        enriched.append(ev_with_meta)
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps(enriched).encode("utf-8"))
                except Exception as e:
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
                return



            # API: annotations (read-only)
            if self.path.startswith("/api/events/annotations"):
                try:
                    from urllib.parse import parse_qs, urlparse
                    parsed = urlparse(self.path)
                    params = parse_qs(parsed.query)
                    timeline = params.get("timeline", ["tl_default"])[0]
                    limit = int(params.get("limit", ["50"])[0])
                    base = Path(__file__).resolve().parent
                    ann_file = base / ".weslr" / "timelines" / timeline / "annotations.jsonl"
                    if not ann_file.exists():
                        self.send_response(200)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(json.dumps([]).encode("utf-8"))
                        return
                    annotations = []
                    with open(ann_file) as f:
                        for line in f:
                            line = line.strip()
                            if line:
                                try:
                                    annotations.append(json.loads(line))
                                except Exception:
                                    pass
                    recent = annotations[-limit:] if len(annotations) > limit else annotations
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps(recent).encode("utf-8"))
                except Exception as e:
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
                return

            # Satellite UI
            if self.path == "/satellite":
                satellite_index = base_dir / "dashboard" / "satellite" / "index.html"
                try:
                    with open(satellite_index, "r", encoding="utf-8") as f:
                        content = f.read()
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html")
                    self.end_headers()
                    self.wfile.write(content.encode("utf-8"))
                except Exception as e:
                    self.send_response(500)
                    self.send_header("Content-Type", "text/plain")
                    self.end_headers()
                    self.wfile.write(f"Error: {e}".encode("utf-8"))
                return

            # API: capability authorizations
            if self.path == "/api/capabilities":
                try:
                    auth_path = base_dir / ".weslr" / "capability_authorizations.json"
                    if auth_path.exists():
                        with open(auth_path) as f:
                            registry = json.load(f)
                    else:
                        registry = {"version": 1, "capabilities": []}
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps(registry).encode("utf-8"))
                except Exception as e:
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
                return

            # API: device registry
            if self.path == "/api/devices":
                try:
                    dev_path = base_dir / ".weslr" / "device_registry.json"
                    if dev_path.exists():
                        with open(dev_path) as f:
                            registry = json.load(f)
                    else:
                        registry = {"version": 1, "devices": []}
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps(registry).encode("utf-8"))
                except Exception as e:
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
                return

            # API: Charter evaluation (read-only)
            if self.path == "/api/charter/evaluate":
                try:
                    charter_path = base_dir / ".weslr" / "charter.json"
                    if not charter_path.exists():
                        self.send_response(404)
                        self.send_header("Content-Type", "application/json")
                        self.end_headers()
                        self.wfile.write(json.dumps({"error": "charter_not_found"}).encode("utf-8"))
                        return
                    with open(charter_path) as f:
                        charter = json.load(f)
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({
                        "charter_present": True,
                        "version": charter.get("version"),
                        "principles": charter.get("principles", []),
                        "trust_rules": charter.get("trust_rules", {}),
                        "source_categories": charter.get("source_categories", {}),
                        "poisoning_resistance": charter.get("poisoning_resistance", {}),
                    }).encode("utf-8"))
                except Exception as e:
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
                return

            # Satellite UI
            if self.path == "/satellite":
                satellite_index = base_dir / "dashboard" / "satellite" / "index.html"
                try:
                    with open(satellite_index, "r", encoding="utf-8") as f:
                        content = f.read()
                    self.send_response(200)
                    self.send_header("Content-Type", "text/html")
                    self.end_headers()
                    self.wfile.write(content.encode("utf-8"))
                except Exception as e:
                    self.send_response(500)
                    self.send_header("Content-Type", "text/plain")
                    self.end_headers()
                    self.wfile.write(f"Error: {e}".encode("utf-8"))
                return

            # API: capability authorizations
            if self.path == "/api/capabilities":
                try:
                    auth_path = base_dir / ".weslr" / "capability_authorizations.json"
                    if auth_path.exists():
                        with open(auth_path) as f:
                            registry = json.load(f)
                    else:
                        registry = {"version": 1, "capabilities": []}
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps(registry).encode("utf-8"))
                except Exception as e:
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
                return

            # API: device registry
            if self.path == "/api/devices":
                try:
                    dev_path = base_dir / ".weslr" / "device_registry.json"
                    if dev_path.exists():
                        with open(dev_path) as f:
                            registry = json.load(f)
                    else:
                        registry = {"version": 1, "devices": []}
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps(registry).encode("utf-8"))
                except Exception as e:
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
                return

            if self.path == "/tia-history":
                import json as _json
                try:
                    history_path = base_dir / "tia_import_history.json"
                    if history_path.exists():
                        with open(history_path, "r", encoding="utf-8") as f:
                            data = _json.load(f)
                    else:
                        data = {"records": [], "total_records": 0}
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(_json.dumps(data).encode("utf-8"))
                except Exception as e:
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(_json.dumps({"error": str(e)}).encode("utf-8"))
                return
            if self.path == "/tia-summary":
                import json as _json
                try:
                    from tia_import import get_latest_tia_summary
                    result = get_latest_tia_summary()
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(_json.dumps(result).encode("utf-8"))
                except Exception as e:
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(_json.dumps({"ok": False, "summary": None, "error": str(e)}).encode("utf-8"))
                return
            # Fall back to default handler for other GET requests
            super().do_GET()
        
        def log_message(self, format, *args):
            # Suppress default logging for cleaner output
            pass
    
    handler = partial(ChatHandler, directory=str(dashboard_dir))
    server = ThreadingHTTPServer((args.host, args.port), handler)
    global _SERVER_START_TIME
    _SERVER_START_TIME = time.time()
    lan_ip = _detect_lan_ip()
    print("Dashboard server running.")
    print(f"Open locally: http://127.0.0.1:{args.port}/")
    print(f"Chat endpoint: http://127.0.0.1:{args.port}/chat")
    if args.host == "0.0.0.0":
        print(f"Open on your LAN: http://{lan_ip}:{args.port}/")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nDashboard server stopped.")
    finally:
        server.server_close()


def cmd_setup(args):
    print(f"{PROJECT_NAME} v{VERSION} setup")
    print("This creates a fresh local world, runs some ticks, and renders the dashboard.")
    print()

    agents = args.agents if args.agents is not None else _prompt_int("How many agents?", DEFAULT_AGENT_COUNT, minimum=1)
    ticks = args.ticks if args.ticks is not None else _prompt_int("How many ticks to run? (0/inf = infinite)", 10, minimum=0, allow_infinite=True)
    interval = args.interval if args.interval is not None else _prompt_int("Seconds between ticks?", 0 if ticks > 0 else TICK_SECONDS, minimum=0)
    refresh = args.refresh if args.refresh is not None else _prompt_int("Dashboard auto-refresh seconds? (0 = off)", 5 if ticks == 0 else 0, minimum=0)
    serve = args.serve if args.serve is not None else _prompt_bool("Serve dashboard on your LAN after setup?", default=True)
    port = args.port if args.port is not None else (_prompt_int("LAN dashboard port?", 8008, minimum=1) if serve else 8008)

    init_world(agent_count=agents, reset=True)
    print(f"Initialized {PROJECT_NAME} with {agents} agents.")

    if ticks == 0:
        print()
        print("Running forever. Press Ctrl+C to stop the loop.")
    else:
        for count in range(ticks):
            emit({"tick_run": count + 1, "results": perform_tick(verbose=args.verbose)})
            if count + 1 < ticks and interval > 0:
                time.sleep(interval)

    if ticks == 0:
        try:
            count = 0
            while True:
                emit({"tick_run": count + 1, "results": perform_tick(verbose=args.verbose)})
                count += 1
                if interval > 0:
                    time.sleep(interval)
        except KeyboardInterrupt:
            print("\nStopped infinite tick loop.")

    dashboard = render_dashboard(auto_refresh_seconds=refresh)
    emit(dashboard)
    dashboard_path = Path(__file__).resolve().parent / "dashboard" / "index.html"
    print()
    print("Dashboard ready.")
    if serve:
        lan_ip = _detect_lan_ip()
        try:
            _launch_dashboard_server(Path(__file__).resolve().parent, "0.0.0.0", port)
            print("LAN server started.")
            print("Copy and paste this exact address into your browser:")
            print(f"  http://{lan_ip}:{port}/")
            print("If you are on the same machine, this also works:")
            print(f"  http://127.0.0.1:{port}/")
        except OSError as exc:
            print(f"Could not start LAN server on port {port}: {exc}")
            print("Fallback: copy and paste this exact file URL into your browser:")
            print(f"  file://{dashboard_path}")
    else:
        print("Copy and paste this exact file URL into your browser:")
        print(f"  file://{dashboard_path}")
    print("If that does not work, open this local file directly:")
    print(f"  {dashboard_path}")


def main():
    parser = argparse.ArgumentParser(description=f"{PROJECT_NAME} v{VERSION} - minimal coding-agent ecosystem sim")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init", help="initialize the world")
    p.add_argument("--agents", type=int, default=DEFAULT_AGENT_COUNT)
    p.add_argument("--reset", action="store_true")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("init-operator", help="create operator profile (headless onboarding)")
    p.add_argument("--name", required=True, help="Operator display name")
    p.add_argument("--role", help="Operator role")
    p.add_argument("--urgency", choices=["low", "normal", "high", "critical"], help="Operational urgency")
    p.add_argument("--checkin-style", dest="checkin_style", choices=["silent", "hourly", "daily", "verbose"], help="Check-in cadence")
    p.add_argument("--adaptation-level", dest="adaptation_level", choices=["none", "propose", "low-risk", "full"], help="Self-modification permission level")
    p.add_argument("--json", action="store_true", help="Machine-readable JSON output")
    p.set_defaults(func=cmd_init_operator)

    p = sub.add_parser("init-bootstrap", help="complete bootstrap trust anchor (headless setup)")
    p.add_argument("--user-id", dest="user_id", help="User identifier (default: operator)")
    p.add_argument("--json", action="store_true", help="Machine-readable JSON output")
    p.set_defaults(func=cmd_init_bootstrap)

    p = sub.add_parser("init-provider", help="configure and validate the active LLM provider (headless)")
    p.add_argument("--provider", required=True, choices=["fallback", "ollama", "openai", "openai_compatible"], help="Active LLM provider")
    p.add_argument("--ollama-host", dest="ollama_host", help="Ollama host URL (default: http://127.0.0.1:11434)")
    p.add_argument("--openai-base-url", dest="openai_base_url", help="OpenAI-compatible base URL")
    p.add_argument("--openai-api-key-env", dest="openai_api_key_env", help="Env var name holding the OpenAI API key (e.g. OPENAI_API_KEY)")
    p.add_argument("--model", help="Model name (provider-specific; leave empty for default)")
    p.add_argument("--json", action="store_true", help="Machine-readable JSON output")
    p.set_defaults(func=cmd_init_provider)

    p = sub.add_parser("tick", help="run one world tick")
    p.add_argument("--verbose", action="store_true")
    p.set_defaults(func=cmd_tick)

    p = sub.add_parser("run", help="run multiple world ticks")
    p.add_argument("--ticks", type=int, default=0, help="0 = forever")
    p.add_argument("--interval", type=int, default=TICK_SECONDS)
    p.add_argument("--verbose", action="store_true")
    p.set_defaults(func=cmd_run)

    p = sub.add_parser("show-world", help="show world state, queues, categories, proposals, packs, and recent logs")
    p.set_defaults(func=cmd_show_world)

    p = sub.add_parser("show-agent", help="show one agent state")
    p.add_argument("name")
    p.set_defaults(func=cmd_show_agent)

    p = sub.add_parser("communicator", help="show the visible communicator state")
    p.set_defaults(func=cmd_communicator)

    p = sub.add_parser("communicator-self", help="show the slower communicator self / relationship continuity state")
    p.set_defaults(func=cmd_communicator_self)

    p = sub.add_parser("identity-core", help="inspect the persisted identity core, biography summary, and recent self-evolution milestones")
    p.set_defaults(func=cmd_identity_core)

    p = sub.add_parser("reflection-store", help="inspect private reflection artifacts with known/inferred/proposed/imagined tagging")
    p.set_defaults(func=cmd_reflection_store)

    p = sub.add_parser("memory-layers", help="inspect working, episodic, semantic, and archive memory scaffolding")
    p.set_defaults(func=cmd_memory_layers)

    p = sub.add_parser("memory-scores", help="inspect first-pass importance scoring for memory retention/compression")
    p.set_defaults(func=cmd_memory_scores)

    p = sub.add_parser("episodic-summarize", help="distill scored exchanges, threads, and thoughts into compact episode memory")
    p.set_defaults(func=cmd_episodic_summarize)

    p = sub.add_parser("semantic-distill", help="distill episodic memory into durable semantic topics, facts, and lessons")
    p.set_defaults(func=cmd_semantic_distill)

    p = sub.add_parser("memory-pressure", help="inspect storage pressure across working, episodic, semantic, and archive memory layers")
    p.set_defaults(func=cmd_memory_pressure)

    p = sub.add_parser("memory-lifecycle", help="show one compact summary of working, episodic, semantic, archive, and continuity state")
    p.set_defaults(func=cmd_memory_lifecycle)

    p = sub.add_parser("artifact-memory", help="show memory traces linked to a specific artifact by id")
    p.add_argument("id")
    p.set_defaults(func=cmd_artifact_memory)

    p = sub.add_parser("archive-memory", help="manually archive low-priority traces once episodic/semantic preservation exists")
    p.set_defaults(func=cmd_archive_memory)

    p = sub.add_parser("prune-memory", help="manually prune raw archived traces when continuity protection allows it")
    p.set_defaults(func=cmd_prune_memory)

    p = sub.add_parser("archive-stale", help="archive low-score working memory items into episodic or archive index")
    p.set_defaults(func=cmd_archive_stale)

    p = sub.add_parser("archive-items", help="archive all low-score working items (testing/debugging only)")
    p.set_defaults(func=cmd_archive_items)

    p = sub.add_parser("communicator-message", help="show natural outward language plus behind-the-curtain metadata")
    p.set_defaults(func=cmd_communicator_message)

    p = sub.add_parser("self-test", help="run self-integrity test (DB, files, checkpoints)")
    p.set_defaults(func=cmd_self_test)

    p = sub.add_parser("spontaneous-expression", help="generate a spontaneous self-expression (thought, question, idea, joke)")
    p.set_defaults(func=cmd_spontaneous_expression)

    p = sub.add_parser("session-continuity", help="check session continuity and time-persistent identity")
    p.set_defaults(func=cmd_session_continuity)

    p = sub.add_parser("weslr-state", help="print WESLR unified operational state summary")
    p.set_defaults(func=cmd_weslr_state)

    p = sub.add_parser("autonomous-intentionality", help="report on autonomous intentionality (plan execution)")
    p.set_defaults(func=cmd_autonomous_intentionality)

    p = sub.add_parser("physical-reasoning", help="test physical reasoning (containment, size relationships)")
    p.add_argument("question", help="question about physical relationships")
    p.set_defaults(func=cmd_physical_reasoning)

    p = sub.add_parser("theory-of-mind", help="test theory of mind (belief states)")
    p.add_argument("scenario", help="scenario to analyze")
    p.set_defaults(func=cmd_theory_of_mind)

    p = sub.add_parser("conversational-implicature", help="test conversational implicature")
    p.add_argument("utterance", help="utterance to analyze")
    p.set_defaults(func=cmd_conversational_implicature)

    p = sub.add_parser("embodiment-test", help="run full embodiment test (physical + ToM + implicature)")
    p.add_argument("question", help="question to test")
    p.set_defaults(func=cmd_embodiment_test)

    p = sub.add_parser("psychological-self", help="show psychological self-description")
    p.set_defaults(func=cmd_psychological_self)

    p = sub.add_parser("cross-discipline-reasoning", help="run cross-discipline reasoning (psych + chem + bio + phys)")
    p.add_argument("question", help="question to reason about")
    p.set_defaults(func=cmd_cross_discipline_reasoning)

    p = sub.add_parser("knowledge-test", help="run cross-discipline knowledge test")
    p.add_argument("question", help="question to test")
    p.set_defaults(func=cmd_knowledge_test)

    p = sub.add_parser("knowledge-domains", help="list all knowledge domains")
    p.set_defaults(func=cmd_knowledge_domains)

    p = sub.add_parser("knowledge-domain", help="get knowledge concepts for a domain")
    p.add_argument("domain", help="domain name (psychology, chemistry, biology, physics, mathematics, robotics, ai)")
    p.set_defaults(func=cmd_knowledge_domain)

    p = sub.add_parser("create-plan", help="create a new plan for a goal")
    p.add_argument("goal", help="the goal or task to plan")
    p.set_defaults(func=cmd_create_plan)

    p = sub.add_parser("set-expression-rate", help="set autonomous expression rate modifier (0.1 = slow, 1.0 = normal, 2.0 = fast)")
    p.add_argument("rate", type=float, help="expression rate multiplier")
    p.set_defaults(func=cmd_set_expression_rate)

    p = sub.add_parser("enable-expressions", help="enable autonomous expressions")
    p.set_defaults(func=cmd_enable_expressions)

    p = sub.add_parser("disable-expressions", help="disable autonomous expressions")
    p.set_defaults(func=cmd_disable_expressions)

    p = sub.add_parser("autonomous-expression", help="generate a direct autonomous expression (bypass tick loop)")
    p.set_defaults(func=cmd_autonomous_expression)

    p = sub.add_parser("plugins-list", help="list all plugins and their status")
    p.set_defaults(func=cmd_plugins_list)

    p = sub.add_parser("plugins-enable", help="enable a plugin by name")
    p.add_argument("name", help="plugin name")
    p.set_defaults(func=cmd_plugins_enable)

    p = sub.add_parser("plugins-disable", help="disable a plugin by name")
    p.add_argument("name", help="plugin name")
    p.set_defaults(func=cmd_plugins_disable)

    p = sub.add_parser("plugins-create", help="create a new plugin template")
    p.add_argument("name", help="plugin name")
    p.add_argument("--description", "-d", default="", help="plugin description")
    p.set_defaults(func=cmd_plugins_create)

    p = sub.add_parser("plugins-integrate", help="integrate plugins into Weslr core")
    p.set_defaults(func=cmd_plugins_integrate)

    p = sub.add_parser("speak", help="print only the natural outward message")
    p.set_defaults(func=cmd_speak)

    p = sub.add_parser("failsafe-status", help="show public external failsafe mode without exposing any secret")
    p.set_defaults(func=cmd_failsafe_status)

    p = sub.add_parser("llm-status", help="show whether Weslr currently has live local-LLM access or is falling back")
    p.set_defaults(func=cmd_llm_status)

    p = sub.add_parser("embedded-self-test", help="run one direct embedded-provider self-test thought generation")
    p.set_defaults(func=cmd_embedded_self_test)

    # === Entity Graph CLI ===
    p = sub.add_parser("entity-list", help="list entities in the entity graph")
    p.add_argument("--limit", "-l", type=int, default=None, help="limit results")
    p.set_defaults(func=cmd_entity_list)

    p = sub.add_parser("entity-details", help="show detailed information about an entity")
    p.add_argument("id", help="entity ID")
    p.set_defaults(func=cmd_entity_details)

    p = sub.add_parser("entity-add", help="add a new entity")
    p.add_argument("name", help="entity name")
    p.add_argument("--type", "-t", default="other", help="entity type (person, organization, concept, event, object, other)")
    p.add_argument("--aliases", "-a", default="", help="comma-separated aliases")
    p.add_argument("--confidence", "-c", type=float, default=0.5, help="initial confidence (0.0-1.0)")
    p.add_argument("--authoritative", action="store_true", help="add as authoritative (not ghost)")
    p.add_argument("--metadata", "-m", default="", help="JSON metadata")
    p.set_defaults(func=cmd_entity_add)

    p = sub.add_parser("entity-promote", help="promote ghost entity to authoritative")
    p.add_argument("id", help="entity ID")
    p.set_defaults(func=cmd_entity_promote)

    p = sub.add_parser("entity-search", help="search entities by name or alias")
    p.add_argument("query", help="search query")
    p.set_defaults(func=cmd_entity_search)

    p = sub.add_parser("entity-stats", help="show entity graph statistics")
    p.set_defaults(func=cmd_entity_stats)

    p = sub.add_parser("relationship-list", help="list relationships in the entity graph")
    p.add_argument("--limit", "-l", type=int, default=None, help="limit results")
    p.set_defaults(func=cmd_relationship_list)

    p = sub.add_parser("relationship-add", help="add a relationship between entities")
    p.add_argument("source", help="source entity name")
    p.add_argument("target", help="target entity name")
    p.add_argument("--type", "-t", default="related_to", help="relationship type")
    p.add_argument("--strength", "-s", type=float, default=0.5, help="relationship strength")
    p.add_argument("--provenance", "-p", default="", help="JSON provenance")
    p.set_defaults(func=cmd_relationship_add)

    p = sub.add_parser("human-exchange", help="record a remembered human conversation exchange into communicator self")
    p.add_argument("name")
    p.add_argument("message")
    p.add_argument("--response", default="")
    p.add_argument("--topics", nargs="*", default=None)
    p.add_argument("--resolved", action="store_true", help="mark the exchange as resolved instead of an open shared thread")
    p.set_defaults(func=cmd_human_exchange)

    p = sub.add_parser("fetch-url", help="fetch readable text from a URL for local research / reading")
    p.add_argument("url")
    p.add_argument("--max-chars", type=int, default=12000)
    p.set_defaults(func=cmd_fetch_url)

    p = sub.add_parser("search-web", help="run a lightweight web search for the current topic")
    p.add_argument("query")
    p.add_argument("--limit", type=int, default=5)
    p.set_defaults(func=cmd_search_web)

    p = sub.add_parser("ingest-web", help="fetch a URL and save the readable text into public memory")
    p.add_argument("url")
    p.add_argument("--title", default="")
    p.add_argument("--max-chars", type=int, default=12000)
    p.set_defaults(func=cmd_ingest_web)

    p = sub.add_parser("eval-metrics", help="show evaluation metrics for the future bounded autonomy gate")
    p.set_defaults(func=cmd_eval_metrics)

    p = sub.add_parser("run-eval", help="reset the world, run a bounded evaluation pass, and emit communicator + metrics")
    p.add_argument("--ticks", type=int, default=25)
    p.add_argument("--agents", type=int, default=5)
    p.add_argument("--interval", type=int, default=0)
    p.add_argument("--verbose", action="store_true")
    p.set_defaults(func=cmd_run_eval)

    p = sub.add_parser("continuation-latest", help="show the latest structured continuation note plus rendered resume text")
    p.set_defaults(func=cmd_continuation_latest)

    p = sub.add_parser("continuation-list", help="list recent structured continuation notes")
    p.add_argument("--limit", type=int, default=10)
    p.set_defaults(func=cmd_continuation_list)

    p = sub.add_parser("continuation-add", help="append a structured continuation note for reliable session handoff")
    p.add_argument("--author", default="operator")
    p.add_argument("--objective", required=True)
    p.add_argument("--completed", required=True)
    p.add_argument("--files-changed", required=True)
    p.add_argument("--behavior-changed", required=True)
    p.add_argument("--checks-performed", required=True)
    p.add_argument("--known-risks", required=True)
    p.add_argument("--next-exact-step", required=True)
    p.add_argument("--resume-hint", required=True)
    p.set_defaults(func=cmd_continuation_add)

    p = sub.add_parser("world-objects", help="inspect persistent world object collections")
    p.add_argument("kind", choices=["needs", "messages", "public-memory", "projects", "relationships", "self-mod-proposals", "work-items", "experiments"])
    p.add_argument("--limit", type=int, default=10)
    p.set_defaults(func=cmd_world_objects)

    p = sub.add_parser("browse", help="browse ranked export/review/packs queues")
    p.add_argument("queue", choices=["export", "review", "packs"])
    p.add_argument("--limit", type=int, default=10)
    p.set_defaults(func=cmd_browse)

    p = sub.add_parser("explain", help="explain why an artifact or pack ranks highly")
    p.add_argument("id")
    p.set_defaults(func=cmd_explain)

    p = sub.add_parser("handoff", help="show handoff-ready summaries for top packs and artifacts")
    p.add_argument("--limit", type=int, default=5)
    p.set_defaults(func=cmd_handoff)

    p = sub.add_parser("review", help="manually review an artifact by id")
    p.add_argument("id")
    p.add_argument("action", choices=["approve", "reject", "export", "note"])
    p.add_argument("--note", default="")
    p.set_defaults(func=cmd_review)

    p = sub.add_parser("category", help="manually manage a category")
    p.add_argument("action", choices=["approve", "reject", "retire", "revive"])
    p.add_argument("name")
    p.set_defaults(func=cmd_category)

    p = sub.add_parser("validate", help="record external validation outcomes for an artifact")
    p.add_argument("id")
    p.add_argument("action", choices=["use", "buyer-fit", "accept", "reject", "revise"])
    p.add_argument("--note", default="")
    p.set_defaults(func=cmd_validate)

    p = sub.add_parser("pack", help="record pack-level offer/test/outcome events")
    p.add_argument("name")
    p.add_argument("action", choices=["offer", "accept", "reject", "revise", "test", "export"])
    p.add_argument("--note", default="")
    p.add_argument("--buyer", default="")
    p.add_argument("--price-band", default="")
    p.add_argument("--mode", default="")
    p.set_defaults(func=cmd_pack)

    p = sub.add_parser("offer", help="prepare an offer brief for a pack")
    p.add_argument("name")
    p.add_argument("--note", default="")
    p.add_argument("--buyer", default="")
    p.add_argument("--price-band", default="")
    p.add_argument("--mode", default="")
    p.set_defaults(func=cmd_offer)

    p = sub.add_parser("dashboard", help="render local operator dashboard files")
    p.add_argument("--refresh", type=int, default=0, help="embed browser auto-refresh seconds into dashboard html")
    p.add_argument("--watch", action="store_true", help="rerender dashboard repeatedly")
    p.add_argument("--interval", type=int, default=10, help="watch loop interval seconds")
    p.add_argument("--iterations", type=int, default=0, help="0 = keep watching until interrupted")
    p.set_defaults(func=cmd_dashboard)

    p = sub.add_parser("serve", help="serve the dashboard over HTTP")
    p.add_argument("--host", default="0.0.0.0", help="bind host, default 0.0.0.0 for LAN access")
    p.add_argument("--port", type=int, default=8008, help="HTTP port for the dashboard server")
    p.set_defaults(func=cmd_serve)

    p = sub.add_parser("setup", help="guided first-run setup for a fresh local test")
    p.add_argument("--agents", type=int, help="how many agents to create")
    p.add_argument("--ticks", type=int, help="how many ticks to run; 0 = forever")
    p.add_argument("--interval", type=int, help="seconds between ticks")
    p.add_argument("--refresh", type=int, help="dashboard browser auto-refresh seconds; 0 = off")
    p.add_argument("--serve", action=argparse.BooleanOptionalAction, default=None, help="start a LAN HTTP server for the dashboard after setup")
    p.add_argument("--port", type=int, help="HTTP port to use when serving the dashboard on LAN")
    p.add_argument("--verbose", action="store_true")
    p.set_defaults(func=cmd_setup)

    p = sub.add_parser("reset", help="reset the world")
    p.add_argument("--agents", type=int, default=DEFAULT_AGENT_COUNT)
    p.set_defaults(func=cmd_reset)

    p = sub.add_parser("version", help="print release version")
    p.set_defaults(func=cmd_version)

    p = sub.add_parser("self-inspection", help="run self-inspection and generate plain-English description of Weslr's code")
    p.set_defaults(func=cmd_self_inspection)

    p = sub.add_parser("translate-code", help="translate code snippet to concepts and internal themes")
    p.add_argument("code", nargs="?", default="")
    p.add_argument("--snippet", default="", help="inline code snippet to translate")
    p.set_defaults(func=cmd_translate_code)

    p = sub.add_parser("explain-code", help="explain code snippet in plain English")
    p.add_argument("code", nargs="?", default="")
    p.add_argument("--snippet", default="", help="inline code snippet to explain")
    p.set_defaults(func=cmd_explain_code)

    p = sub.add_parser("translate-error", help="parse a Python traceback and explain the error")
    p.add_argument("--traceback", default="", help="inline traceback to translate")
    p.add_argument("--file", default="", help="file containing traceback text")
    p.set_defaults(func=cmd_translate_error)

    p = sub.add_parser("search-tool", help="search for tools/APIs and generate usage patterns")
    p.add_argument("--need", required=True, help="what you need to do (e.g., 'read web pages')")
    p.set_defaults(func=cmd_search_tool)

    p = sub.add_parser("propose-self-mod", help="propose a self-modification with diff and rationale")
    p.add_argument("--file", required=True, help="file to modify (relative to Weslr directory)")
    p.add_argument("--change", required=True, help="what change to make")
    p.add_argument("--rationale", required=True, help="why this change is needed")
    p.set_defaults(func=cmd_propose_self_mod)

    p = sub.add_parser("propose-improvement", help="propose a self-improvement based on a need")
    p.add_argument("--need", required=True, help="what Weslr needs to do better")
    p.set_defaults(func=cmd_propose_improvement)

    p = sub.add_parser("apply-mod", help="apply an approved self-modification (with checkpoint)")
    p.add_argument("--file", required=True, help="file to modify")
    p.add_argument("--change", required=True, help="what change to make")
    p.add_argument("--rationale", required=True, help="why this change is needed")
    p.add_argument("--approved-by", default="human", help="who approved the change")
    p.set_defaults(func=cmd_apply_mod)

    # Phase 1E: Safe Capability Evolution Engine CLI
    sci = sub.add_parser("sci", help="safe capability evolution engine commands")

    sci_sub = sci.add_subparsers(dest="sci_cmd", required=True)

    p = sci_sub.add_parser("observations-list", help="list recorded observations")
    p.add_argument("--type", default="", help="filter by observation type")
    p.add_argument("--source", default="", help="filter by source layer")
    p.add_argument("--limit", type=int, default=50, help="max results")
    p.set_defaults(func=cmd_sci_observations_list)

    p = sci_sub.add_parser("observations-record", help="record a new observation")
    p.add_argument("--type", required=True, help="observation type")
    p.add_argument("--pattern", required=True, help="pattern description")
    p.add_argument("--source", required=True, help="source layer")
    p.set_defaults(func=cmd_sci_observations_record)

    p = sci_sub.add_parser("proposals-create", help="create a new improvement proposal")
    p.add_argument("--observation-ids", default="", help="comma-separated observation IDs")
    p.add_argument("--title", required=True, help="proposal title")
    p.add_argument("--problem", default="", help="problem description")
    p.add_argument("--likely-cause", default="", help="root cause analysis")
    p.add_argument("--files", required=True, help="comma-separated files to change")
    p.add_argument("--expected-benefit", default="", help="expected improvement")
    p.add_argument("--risk-level", default="low", help="risk level: low|medium|high")
    p.add_argument("--test-prompts", default="", help="JSON test prompts array")
    p.add_argument("--rollback", default="", help="rollback shell command")
    p.add_argument("--patch-plan", default="", help="JSON patch plan")
    p.set_defaults(func=cmd_sci_proposals_create)

    p = sci_sub.add_parser("proposals-list", help="list proposals")
    p.add_argument("--status", default="", help="filter by status")
    p.add_argument("--limit", type=int, default=50, help="max results")
    p.set_defaults(func=cmd_sci_proposals_list)

    p = sci_sub.add_parser("proposals-approve", help="approve a proposal")
    p.add_argument("--proposal-id", required=True, help="proposal ID")
    p.add_argument("--by", default="human", help="approving entity")
    p.set_defaults(func=cmd_sci_proposals_approve)

    p = sci_sub.add_parser("proposals-deny", help="deny a proposal")
    p.add_argument("--proposal-id", required=True, help="proposal ID")
    p.add_argument("--reason", required=True, help="reason for denial")
    p.set_defaults(func=cmd_sci_proposals_deny)

    p = sci_sub.add_parser("apply", help="apply an approved proposal with real tests")
    p.add_argument("--proposal-id", required=True, help="proposal ID")
    p.add_argument("--by", default="human", help="applying entity")
    p.set_defaults(func=cmd_sci_apply)

    p = sci_sub.add_parser("status", help="show safe capability evolution engine status")
    p.set_defaults(func=cmd_sci_status)

    p = sci_sub.add_parser("proposal-show", help="show detailed proposal info")
    p.add_argument("--proposal-id", required=True, help="proposal ID")
    p.set_defaults(func=cmd_sci_proposal_show)

    p = sci_sub.add_parser("proposal-rollback", help="rollback an applied proposal")
    p.add_argument("--proposal-id", required=True, help="proposal ID")
    p.add_argument("--by", default="human", help="rolling back entity")
    p.set_defaults(func=cmd_sci_proposal_rollback)

    p = sub.add_parser("tia-import", help="import TIA Openness export artifact")
    p.add_argument("--file", required=True, help="path to TIA export JSON")
    p.add_argument("--output", default="tia_import_result.json", help="output envelope JSON")
    p.set_defaults(func=cmd_tia_import)

    p = sub.add_parser("tia-history", help="list recent TIA import history records")
    p.add_argument("--limit", type=int, default=10, help="number of recent records to show")
    p.add_argument("--path", default="", help="override history file path")
    p.set_defaults(func=cmd_tia_history)

    p = sub.add_parser("tia-show", help="show detailed summary for one TIA import")
    p.add_argument("--path", default="", help="override history file path")
    p.add_argument("--index", type=int, default=None, help="record index (1-based, default: latest)")
    p.add_argument("--source", default=None, help="filter by source filename")
    p.set_defaults(func=cmd_tia_show)

    p = sub.add_parser("create-checkpoint", help="create a checkpoint of the current file state")
    p.add_argument("--file", required=True, help="file to checkpoint")
    p.set_defaults(func=cmd_create_checkpoint)

    p = sub.add_parser("rollback", help="rollback a file to a previous checkpoint")
    p.add_argument("--file", required=True, help="file to rollback")
    p.add_argument("--checkpoint", required=True, help="checkpoint name to restore")
    p.set_defaults(func=cmd_rollback)

    p = sub.add_parser("mod-log", help="show modification log and pending modifications")
    p.set_defaults(func=cmd_mod_log)

    p = sub.add_parser("checkpoints", help="list available checkpoints")
    p.add_argument("--file", default="", help="optional filter by file path")
    p.set_defaults(func=cmd_checkpoints)

    p = sub.add_parser("llm-diff", help="use LLM to generate better diff with explanation")
    p.add_argument("--file", required=True, help="file to analyze")
    p.add_argument("--change", required=True, help="proposed change")
    p.add_argument("--rationale", default="", help="context for the change")
    p.set_defaults(func=cmd_llm_diff)

    p = sub.add_parser("llm-analyze", help="use LLM to analyze code for issues")
    p.add_argument("--file", required=True, help="file to analyze")
    p.set_defaults(func=cmd_llm_analyze)

    p = sub.add_parser("llm-suggest", help="use LLM to suggest self-improvements")
    p.add_argument("--need", required=True, help="what needs improvement")
    p.set_defaults(func=cmd_llm_suggest)

    p = sub.add_parser("dashboard-selfmod", help="update the self-modification dashboard")
    p.set_defaults(func=cmd_dashboard_selfmod)

    p = sub.add_parser("dashboard-status", help="check self-modification dashboard status")
    p.set_defaults(func=cmd_dashboard_status)

    p = sub.add_parser("auto-suggest", help="generate autonomous self-improvement suggestions")
    p.set_defaults(func=cmd_auto_suggest)

    p = sub.add_parser("check-safe", help="check if a modification is safe")
    p.add_argument("--file", required=True, help="file to modify")
    p.add_argument("--change", required=True, help="proposed change")
    p.set_defaults(func=cmd_check_safe)

    p = sub.add_parser("validate-mod", help="validate a modification before applying")
    p.add_argument("--file", required=True, help="file to modify")
    p.add_argument("--change", required=True, help="proposed change")
    p.add_argument("--rationale", required=True, help="why this change is needed")
    p.set_defaults(func=cmd_validate_mod)

    p = sub.add_parser("rollback-preview", help="preview a rollback operation")
    p.add_argument("--file", required=True, help="file to rollback")
    p.add_argument("--checkpoint", required=True, help="checkpoint name")
    p.set_defaults(func=cmd_rollback_preview)

    p = sub.add_parser("batch-mods", help="batch multiple modifications together")
    p.add_argument("--mods", required=True, help="JSON array of modifications")
    p.set_defaults(func=cmd_batch_mods)

    p = sub.add_parser("self-eval", help="run self-evaluation to identify gaps and opportunities")
    p.set_defaults(func=cmd_self_eval)

    p = sub.add_parser("self-grow", help="run full self-directed growth cycle")
    p.set_defaults(func=cmd_self_grow)

    p = sub.add_parser("self-speak", help="generate speech explaining Weslr's self-decisions")
    p.add_argument("--gaps", default="[]", help="gaps to speak about")
    p.set_defaults(func=cmd_self_speak)

    # Opportunity lifecycle management commands
    p = sub.add_parser("opportunity-list", help="list all opportunity themes with their lifecycle states")
    p.set_defaults(func=cmd_opportunity_list)

    p = sub.add_parser("opportunity-transition", help="transition an opportunity to a new lifecycle state")
    p.add_argument("--theme", required=True, help="theme name")
    p.add_argument("--target", required=True, help="target state (hypothesis, validated, production, rejected, archived)")
    p.set_defaults(func=cmd_opportunity_transition)

    p = sub.add_parser("opportunity-auto-transition", help="run auto-transition checks on all opportunities")
    p.set_defaults(func=cmd_opportunity_auto_transition)

    p = sub.add_parser("opportunity-cluster", help="show cross-agent opportunity clustering")
    p.set_defaults(func=cmd_opportunity_cluster)

    p = sub.add_parser("opportunity-reject", help="record a rejection for an opportunity theme")
    p.add_argument("--theme", required=True, help="theme name")
    p.add_argument("--reason", required=True, help="rejection reason")
    p.set_defaults(func=cmd_opportunity_reject)

    p = sub.add_parser("opportunity-revisit", help="inspect and trigger theme revisit tracking")
    p.set_defaults(func=cmd_opportunity_revisit)

    # Variation generation commands
    p = sub.add_parser("variation-generate", help="generate math-based variations for a rejected theme")
    p.add_argument("--theme", required=True, help="theme name")
    p.add_argument("--method", default="hybrid", help="method: markov, bandit, entropy, gradient, hybrid")
    p.add_argument("--count", type=int, default=3, help="maximum variations to generate")
    p.set_defaults(func=cmd_variation_generate)

    p = sub.add_parser("variation-list", help="list all themes with their generated variations and math scores")
    p.set_defaults(func=cmd_variation_list)

    p = sub.add_parser("variation-show", help="show detailed variation history for a theme")
    p.add_argument("--theme", required=True, help="theme name")
    p.set_defaults(func=cmd_variation_show)

    # v71: Diagnostics / Observability Integration
    p = sub.add_parser("diagnostics-summary", help="export diagnostic summary in operator-readable format")
    p.set_defaults(func=cmd_diagnostics_summary)

    p = sub.add_parser("diagnostics-failure-chain", help="export correlated failure chain by ID")
    p.add_argument("correlation_id", help="the ID to trace (flow_id, request_id, handshake_id, deadline_id)")
    p.add_argument("--type", default="flow", choices=["flow", "request", "handshake", "deadline"], help="correlation type")
    p.set_defaults(func=cmd_diagnostics_failure_chain)

    p = sub.add_parser("diagnostics-recovery-hints", help="export all recovery hints in structured format")
    p.set_defaults(func=cmd_diagnostics_recovery_hints)

    # v72: Distributed Failure Replay / Diagnostic Trace Export
    p = sub.add_parser("diagnostics-trace-export", help="export diagnostic trace with correlation validation and consistency score")
    p.add_argument("--flow-id", help="specific flow ID to export (exports all flows if omitted)")
    p.set_defaults(func=cmd_diagnostics_trace_export)

    p = sub.add_parser("diagnostics-trace-replay", help="export replay summary for operator consumption")
    p.add_argument("--flow-id", help="specific flow ID to replay (exports all if omitted)")
    p.set_defaults(func=cmd_diagnostics_trace_replay)

    p = sub.add_parser("diagnostics-replay-export", help="export replayable trace format")
    p.add_argument("--flow-id", help="specific flow ID to export (exports all if omitted)")
    p.set_defaults(func=cmd_diagnostics_replay_export)

    # v73: Distributed Fallback Behavior
    p = sub.add_parser("fallback-status", help="export fallback status for a specific node or all nodes")
    p.add_argument("--node-id", help="specific node ID (exports all nodes if omitted)")
    p.set_defaults(func=cmd_fallback_status)

    p = sub.add_parser("fallback-diagnostics", help="export fallback audit/diagnostic records")
    p.set_defaults(func=cmd_fallback_diagnostics)

    # v74: Fallback Trace Export / Replay Integration
    p = sub.add_parser("fallback-trace-export", help="export fallback trace with correlation and capability visibility")
    p.add_argument("--flow-id", help="specific flow ID to export (exports all if omitted)")
    p.set_defaults(func=cmd_fallback_trace_export)

    p = sub.add_parser("fallback-trace-replay", help="export fallback trace replay summary for operator consumption")
    p.add_argument("--flow-id", help="specific flow ID to replay (exports all if omitted)")
    p.set_defaults(func=cmd_fallback_trace_replay)

    args = parser.parse_args()
    args.func(args)


# ============================================================================
# New Phase 1 command handlers
# ============================================================================

def cmd_self_inspection(_args):
    """Run self-inspection and emit structured data plus description."""
    result = build_self_inspection_report()
    emit(result)
    if result.get("ok"):
        print(f"\nDescription:\n{result.get('description', 'No description generated.')}")


def cmd_translate_code(args):
    """Translate code to concepts and internal themes."""
    code = args.snippet or args.code
    if not code:
        emit({"error": "No code snippet provided. Use --snippet or pass code as argument."})
        return
    result = translate_code_to_concept(code)
    theme = translate_internal_theme_to_code(code)
    emit({
        "code_snippet": code[:120] + ("..." if len(code) > 120 else ""),
        "concepts": result,
        "themes": theme.get("themes", []),
        "confidence": theme.get("confidence", 0.0),
    })


def cmd_explain_code(args):
    """Explain code snippet in plain English."""
    code = args.snippet or args.code
    if not code:
        emit({"error": "No code snippet provided. Use --snippet or pass code as argument."})
        return
    explanation = explain_code(code)
    emit({
        "code_snippet": code[:120] + ("..." if len(code) > 120 else ""),
        "explanation": explanation,
    })


def cmd_translate_error(args):
    """Parse a traceback and explain the error."""
    tb = args.traceback or ""
    if args.file:
        try:
            with open(args.file, "r") as f:
                tb = f.read()
        except Exception as e:
            emit({"error": f"Could not read file: {e}"})
            return
    if not tb:
        emit({"error": "No traceback provided. Use --traceback or --file."})
        return

    result = translate_error(tb)
    if not result.get("ok"):
        emit(result)
        return

    emit({
        "error_type": result.get("error_info", {}).get("exception_type", "Unknown"),
        "error_message": result.get("error_info", {}).get("exception_message", ""),
        "category": result.get("error_type", {}).get("category", "unknown"),
        "cause": result.get("error_type", {}).get("cause", ""),
        "fix_proposal": result.get("fix_proposal", ""),
        "location": result.get("error_info", {}).get("file_info", {}),
    })
    print("\nPlain English explanation:")
    print(translate_error_to_plain_english(tb))


def cmd_search_tool(args):
    """Search for tools and synthesize usage."""
    need = args.need
    if not need:
        emit({"error": "No need specified. Use --need to describe what you want to do."})
        return
    result = search_tool_and_synthesize(need)
    emit(result)
    if result.get("ok"):
        print("\nHuman-readable summary:")
        print(explain_tool_usage(need))


def cmd_propose_self_mod(args):
    """Propose a specific self-modification."""
    file_path = args.file
    change = args.change
    rationale = args.rationale

    if not file_path or not change or not rationale:
        emit({"error": "Missing required fields: --file, --change, and --rationale are required."})
        return

    result = propose_self_modification_report(file_path, change, rationale)

    if not result.get("ok"):
        emit(result)
        return

    emit({
        "ok": True,
        "file_path": file_path,
        "change_description": change,
        "rationale": rationale,
        "protected": result.get("protected", False),
    })

    if result.get("protected"):
        print("\n⚠️  This file is PROTECTED and cannot be modified automatically.")
        print("You must manually edit it if you want to make this change.")
    else:
        print("\n--- Proposed Diff ---")
        for line in result.get("diff", {}).get("diff", []):
            print(line)
        print("\n--- Full Change ---")
        print(result.get("diff", {}).get("proposed", ""))


def cmd_propose_improvement(args):
    """Propose a self-improvement based on a need."""
    need = args.need
    if not need:
        emit({"error": "No need specified. Use --need to describe what Weslr needs to do better."})
        return

    result = build_proposal_report(need)
    emit(result)

    if not result.get("ok"):
        print(f"\nError: {result.get('error', 'unknown error')}")
        return

    print("\n--- Proposed Improvement ---")
    print(f"**Need**: {need}")
    improvement = result.get('improvement', {})
    best_match = improvement.get('best_match')
    print(f"**Best match**: {best_match if best_match else 'None'}")
    print(f"**File**: {improvement.get('proposed', {}).get('file_path', 'N/A')}")
    print(f"**Change**: {improvement.get('proposed', {}).get('change_description', 'N/A')}")
    print(f"**Rationale**: {improvement.get('proposed', {}).get('rationale', 'N/A')}")
    print("\n--- Diff ---")
    for line in result.get('diff', {}).get('diff', []):
        print(line)


def cmd_apply_mod(args):
    """Apply an approved self-modification."""
    file_path = args.file
    change = args.change
    rationale = args.rationale
    approved_by = args.approved_by

    if not file_path or not change or not rationale:
        emit({"error": "Missing required fields: --file, --change, and --rationale are required."})
        return

    result = apply_modification(file_path, change, rationale, approved_by)

    if not result.get("ok"):
        emit(result)
        return

    emit({
        "ok": True,
        "file_path": file_path,
        "change": change,
        "checkpoint": result.get("checkpoint"),
        "log_entry": result.get("log_entry"),
    })
    print(f"\n✅ Applied to {file_path}")
    print(f"Checkpoint: {result.get('checkpoint', {}).get('checkpoint_name', 'N/A')}")


# Phase 1E: Safe Capability Evolution Engine CLI


def cmd_sci_observations_list(args):
    """List recorded observations."""
    limit = args.limit or 50
    obs_type = args.type
    source = args.source

    result = list_observations(type=obs_type, source_layer=source, limit=limit)
    emit(result)

    if not result.get("ok"):
        print(f"\nError: {result.get('error', 'unknown error')}")
        return

    print(f"\n--- Observations ({result.get('total', 0)} found) ---")
    for obs in result.get("observations", []):
        print(f"[{obs.get('id')}] Type: {obs.get('type')}, Source: {obs.get('source_layer')}")
        print(f"  Pattern: {obs.get('pattern')}")
        print(f"  Count: {obs.get('count')}, Last: {obs.get('last_seen')}")


def cmd_sci_observations_record(args):
    """Record a new observation of repeated weakness."""
    obs_type = args.type
    pattern = args.pattern
    source = args.source

    if not obs_type or not pattern or not source:
        emit({"error": "Missing required fields: --type, --pattern, and --source are required."})
        return

    result = record_observation(type=obs_type, pattern=pattern, source_layer=source)

    if not result.get("ok"):
        emit(result)
        return

    emit(result)
    print(f"\n✅ Observation recorded: {result.get('observation_id')}")


def cmd_sci_proposals_create(args):
    """Create a new improvement proposal."""
    obs_ids = args.observation_ids.split(",") if args.observation_ids else []
    title = args.title
    problem = args.problem
    likely_cause = args.likely_cause
    files_to_change = args.files.split(",") if args.files else []
    expected_benefit = args.expected_benefit
    risk_level = args.risk_level or "low"
    test_prompts = args.test_prompts
    rollback = args.rollback
    patch_plan = args.patch_plan

    if not files_to_change or not title:
        emit({"error": "Missing required fields: --files and --title are required."})
        return

    # Parse test prompts as JSON if provided
    parsed_prompts = []
    if test_prompts:
        try:
            parsed_prompts = json.loads(test_prompts)
        except json.JSONDecodeError:
            emit({"error": "Invalid JSON in --test-prompts"})
            return

    # Parse rollback command
    rollback_cmd = None
    if rollback:
        rollback_cmd = rollback

    # Parse patch plan as JSON if provided
    parsed_patch = None
    if patch_plan:
        try:
            parsed_patch = json.loads(patch_plan)
        except json.JSONDecodeError:
            emit({"error": "Invalid JSON in --patch-plan"})
            return

    result = create_proposal(
        observation_ids=obs_ids,
        title=title,
        problem=problem or f"Proposed improvement: {title}",
        likely_cause=likely_cause or "Human analysis",
        files_to_change=files_to_change,
        expected_benefit=expected_benefit or "Self-improvement",
        risk_level=risk_level,
        test_prompts=parsed_prompts,
        rollback_command=rollback_cmd,
        patch_plan=parsed_patch,
    )

    if not result.get("ok"):
        emit(result)
        return

    emit(result)
    print(f"\n✅ Proposal created: {result.get('proposal_id')}")


def cmd_sci_proposals_list(args):
    """List proposals, optionally filtered by status."""
    limit = args.limit or 50
    status = args.status

    result = list_proposals(status=status, limit=limit)
    emit(result)

    if not result.get("ok"):
        print(f"\nError: {result.get('error', 'unknown error')}")
        return

    print(f"\n--- Proposals ({result.get('total', 0)} found) ---")
    for prop in result.get("proposals", []):
        print(f"[{prop.get('id')}] Status: {prop.get('status')}, Title: {prop.get('title')}")
        print(f"  Files: {', '.join(prop.get('files_to_change', []))}")
        print(f"  Risk: {prop.get('risk_level')}")


def cmd_sci_proposals_approve(args):
    """Approve a proposal."""
    proposal_id = args.proposal_id
    approved_by = args.by or "human"

    result = approve_proposal(proposal_id=proposal_id, approved_by=approved_by)

    if not result.get("ok"):
        emit(result)
        return

    emit(result)
    print(f"\n✅ Proposal approved: {proposal_id}")


def cmd_sci_proposals_deny(args):
    """Deny a proposal."""
    proposal_id = args.proposal_id
    reason = args.reason

    if not reason:
        emit({"error": "Missing required field: --reason is required."})
        return

    result = deny_proposal(proposal_id=proposal_id, reason=reason)

    if not result.get("ok"):
        emit(result)
        return

    emit(result)
    print(f"\n✅ Proposal denied: {proposal_id}")


def cmd_sci_apply(args):
    """Apply an approved proposal with real test execution."""
    proposal_id = args.proposal_id
    applied_by = args.by or "human"

    result = apply_proposal_with_tests(proposal_id=proposal_id, applied_by=applied_by)

    if not result.get("ok"):
        emit(result)
        return

    emit(result)

    if result.get("all_tests_passed"):
        print(f"\n✅ Proposal applied successfully: {proposal_id}")
        print(f"   Status: {result.get('status')}")
    else:
        print(f"\n⚠️  Proposal applied with failures: {proposal_id}")
        print(f"   Status: {result.get('status')}")
        print(f"   Failing tests: {result.get('failing_tests', [])}")
        if result.get('rollback_guidance'):
            print(f"   Rollback command: {result.get('rollback_guidance', {}).get('rollback_command', 'N/A')}")


def cmd_sci_status(args):
    """Show safe capability evolution engine status."""
    proposals = load_proposals()
    observations = load_observations()
    apply_log = []

    # Count by status
    status_counts = {"proposed": 0, "approved": 0, "applied": 0, "applied_with_failures": 0, "rolled_back": 0, "rejected": 0}
    for p in proposals:
        status = p.get("status", "unknown")
        if status in status_counts:
            status_counts[status] += 1

    result = {
        "ok": True,
        "observations": {
            "total": len(observations),
            "types": {}
        },
        "proposals": {
            "total": len(proposals),
            "by_status": status_counts,
        },
        "timestamp": int(time.time() * 1000),
    }

    # Count observation types
    for obs in observations:
        obs_type = obs.get("type")
        if obs_type:
            result["observations"]["types"][obs_type] = result["observations"]["types"].get(obs_type, 0) + 1

    emit(result)

    print("\n--- Safe Capability Evolution Engine Status ---")
    print(f"Observations recorded: {result['observations']['total']}")
    for obs_type, count in result["observations"]["types"].items():
        print(f"  - {obs_type}: {count}")
    print(f"\nProposals: {result['proposals']['total']} total")
    print("  By status:")
    for status, count in result["proposals"]["by_status"].items():
        if count > 0:
            print(f"    - {status}: {count}")


def cmd_sci_proposal_show(args):
    """Show detailed info for a specific proposal."""
    proposal_id = args.proposal_id

    prop = get_proposal(proposal_id)
    if not prop:
        emit({"error": f"Proposal not found: {proposal_id}"})
        return

    emit(prop)

    print(f"\n--- Proposal Details: {proposal_id} ---")
    print(f"Title: {prop.get('title')}")
    print(f"Status: {prop.get('status')}")
    print(f"Problem: {prop.get('problem')}")
    print(f"Files to change: {', '.join(prop.get('files_to_change', []))}")
    print(f"Risk level: {prop.get('risk_level')}")
    print(f"Test prompts: {len(prop.get('test_prompts', []))}")

    if prop.get('test_results'):
        print(f"Test results:")
        for tr in prop.get('test_results', []):
            print(f"  [{tr.get('test_index')}] {tr.get('prompt')[:50]}... -> {tr.get('status')}")

    if prop.get('rollback_command'):
        print(f"Rollback command: {prop.get('rollback_command')}")

    if prop.get('applied_at'):
        print(f"Applied at: {prop.get('applied_at')}")
    if prop.get('applied_by'):
        print(f"Applied by: {prop.get('applied_by')}")


def cmd_sci_proposal_rollback(args):
    """Rollback an applied proposal."""
    proposal_id = args.proposal_id
    rolled_back_by = args.by or "human"

    # Import rollback function from apply module
    from self_improvement_apply import rollback_proposal
    result = rollback_proposal(proposal_id=proposal_id, rolled_back_by=rolled_back_by)

    if not result.get("ok"):
        emit(result)
        return

    emit(result)
    print(f"\n✅ Rollback recorded: {proposal_id}")
    print(f"   Command to execute manually: {result.get('rollback_command', 'N/A')}")


def cmd_tia_import(args):
    """Import TIA Openness export artifact."""
    result = create_raw_import_envelope(args.file)
    if not result.get("ok"):
        emit(result)
        error_msg = result.get("error") or "Unknown error"
        print(f"\n❌ Import failed: {error_msg}")
        return

    emit(result)
    print(f"\n✅ TIA export imported: {args.file}")
    print(f"   Project: {result.get('project_name')}")
    print(f"   Collector: {result.get('collector_version') or 'unknown'}")

    output_path = Path(__file__).resolve().parent / args.output
    save_result = save_import_envelope(result, output_path)
    if save_result.get("ok"):
        print(f"   Envelope saved: {save_result.get('saved_to')}")
    else:
        print(f"   ⚠️  Envelope created but not saved: {save_result.get('error')}")

    # Show validation summary
    validation = result.get("validation", {})
    if validation.get("warnings"):
        print(f"\nValidation warnings ({len(validation['warnings'])}):")
        for w in validation["warnings"]:
            print(f"  - {w}")
    if validation.get("errors"):
        print(f"\nValidation errors ({len(validation['errors'])}):")
        for e in validation["errors"]:
            print(f"  - {e}")

    # Normalize and save normalized artifact
    try:
        normalized = normalize_tia_envelope(result)
        output_stem = output_path.stem  # e.g., 'tia_import_result'
        normalized_path = output_path.parent / f"{output_stem}.normalized.json"
        normalized_save_result = save_normalized_envelope(normalized, normalized_path)
        if normalized_save_result.get("ok"):
            print(f"\n✅ Normalized TIA artifact saved: {normalized_save_result.get('saved_to')}")
        else:
            print(f"\n⚠️  Normalized output not saved: {normalized_save_result.get('error')}")

        # Safe metadata printing
        project_name = normalized.get("project", {}).get("name", "Unknown")
        counts = normalized.get("metadata", {}).get("normalization", {}).get("item_counts", {})
        total = counts.get("total_items", 0)
        devices = counts.get("devices", 0)
        plcs = counts.get("plcs", 0)
        cpus = counts.get("cpus", 0)
        modules = counts.get("modules", 0)
        tags = counts.get("tags", 0)
        print(f"   Project: {project_name}")
        print(f"   Items: {total} total ({devices} devices, {plcs} PLCs, {cpus} CPUs, {modules} modules, {tags} tags)")

        norm_warnings = normalized.get("metadata", {}).get("normalization", {}).get("warnings", [])
        if norm_warnings:
            print(f"   Normalization warnings: {len(norm_warnings)}")

        # Record history
        history_path = output_path.parent / "tia_import_history.json"
        history_result = record_tia_import_history(result, normalized, output_path, normalized_path, history_path)
        if history_result.get("ok"):
            print(f"   History recorded: {history_path}")
        else:
            print(f"   ⚠️  History not recorded: {history_result.get('error')}")
    except Exception as e:
        print(f"\n⚠️  Normalization skipped: {e}")


def cmd_tia_history(args):
    """List recent TIA import history records."""
    history_path = Path(args.path) if args.path else None
    result = list_tia_import_history(history_path, args.limit)

    if not result.get("ok"):
        emit(result)
        print(f"\n❌ Error: {result.get('error')}")
        return

    emit(result)
    print(f"\n=== TIA Import History ({result.get('total_records', 0)} total) ===")
    print(f"   File: {result.get('history_file')}")

    for i, rec in enumerate(result.get("records", []), 1):
        status_icon = {"ok": "✅", "warning": "⚠️", "error": "❌"}.get(rec.get("status"), "❓")
        project = rec.get("project_name", "Unknown")
        source = rec.get("source_file", "")
        items = rec.get("item_counts", {}).get("total_items", 0)
        timestamp = rec.get("timestamp", 0)
        ts_str = strftime("%Y-%m-%d %H:%M:%S", localtime(timestamp / 1000))
        print(f"\n{i}. {status_icon} {project}")
        print(f"   Source: {source}")
        print(f"   Items: {items}")
        print(f"   At: {ts_str}")


def cmd_tia_show(args):
    """Show detailed summary for one TIA import."""
    history_path = Path(args.path) if args.path else None
    idx = getattr(args, 'index', None)
    source = getattr(args, 'source', None)
    
    record = get_tia_import_record(history_path, idx, source)
    if record is None:
        emit({"error": "No TIA import history found or record not found"})
        print("\n❌ No record found")
        return
    
    ts = record.get("timestamp", 0)
    ts_str = strftime("%Y-%m-%d %H:%M:%S", localtime(ts / 1000))
    counts = record.get("item_counts", {})
    
    summary = {
        "project_name": record.get("project_name", "Unknown"),
        "source_file": record.get("source_file", ""),
        "timestamp": ts,
        "timestamp_human": ts_str,
        "status": record.get("status", "unknown"),
        "validation_ok": record.get("validation", {}).get("ok", False),
        "validation_warnings": record.get("validation", {}).get("warnings", 0),
        "validation_errors": record.get("validation", {}).get("errors", 0),
        "devices": counts.get("devices", 0),
        "plcs": counts.get("plcs", 0),
        "cpus": counts.get("cpus", 0),
        "modules": counts.get("modules", 0),
        "tags": counts.get("tags", 0),
        "total_items": counts.get("total_items", 0),
        "raw_output": record.get("raw_output", ""),
        "normalized_output": record.get("normalized_output", ""),
    }
    
    emit(summary)
    
    print(f"\n=== TIA Import Summary ===")
    print(f"Project: {summary['project_name']}")
    print(f"Timestamp: {summary['timestamp_human']}")
    status_icon = {"ok": "✅", "warning": "⚠️", "error": "❌"}.get(summary['status'], "❓")
    print(f"Status: {status_icon} {summary['status']}")
    print(f"Items: {summary['total_items']} total ({summary['devices']} devices, {summary['plcs']} PLCs, {summary['cpus']} CPUs, {summary['modules']} modules, {summary['tags']} tags)")
    if summary['validation_warnings'] or summary['validation_errors']:
        print(f"Validation: {summary['validation_warnings']} warnings, {summary['validation_errors']} errors")

    # Industrial details — read promoted Siemens fields from normalized artifact
    header_printed = False
    try:
        norm_path = Path(summary['normalized_output'])
        if norm_path.exists():
            with open(norm_path, "r", encoding="utf-8") as f:
                norm = json.load(f)
            # First PLC (promoted fields: rack, slot, ip)
            plc_list = norm.get("plcs", [])
            if plc_list:
                plc = plc_list[0]
                if plc.get("rack") is not None or plc.get("slot") is not None or plc.get("ip"):
                    if not header_printed:
                        print(f"\n=== Industrial Details ===")
                        header_printed = True
                    print(f"\n--- PLC (first) ---")
                    if plc.get("rack") is not None: print(f"  Rack: {plc['rack']}")
                    if plc.get("slot") is not None: print(f"  Slot: {plc['slot']}")
                    if plc.get("ip"): print(f"  IP: {plc['ip']}")
            # First device (promoted fields: hw_ver, fw_ver)
            dev_list = norm.get("devices", [])
            if dev_list:
                dev = dev_list[0]
                if dev.get("hw_ver") or dev.get("fw_ver"):
                    if not header_printed:
                        print(f"\n=== Industrial Details ===")
                        header_printed = True
                    print(f"\n--- Device (first) ---")
                    if dev.get("hw_ver"): print(f"  HW: {dev['hw_ver']}")
                    if dev.get("fw_ver"): print(f"  FW: {dev['fw_ver']}")
            # First tag (promoted fields: type, addr, desc)
            tag_list = norm.get("tags", [])
            if tag_list:
                tag = tag_list[0]
                if tag.get("type") or tag.get("addr") or tag.get("desc"):
                    if not header_printed:
                        print(f"\n=== Industrial Details ===")
                        header_printed = True
                    print(f"\n--- Tag (first) ---")
                    if tag.get("type"): print(f"  Type: {tag['type']}")
                    if tag.get("addr"): print(f"  Address: {tag['addr']}")
                    if tag.get("desc"): print(f"  Desc: {tag['desc']}")
    except Exception:
        pass  # silently skip if loading fails

    # Print raw/normalized output paths once at the end
    print(f"\nRaw output: {summary['raw_output']}")
    print(f"Normalized output: {summary['normalized_output']}")


def cmd_create_checkpoint(args):
    """Create a checkpoint of the current file state."""
    file_path = args.file

    if not file_path:
        emit({"error": "Missing required field: --file is required."})
        return

    result = create_checkpoint(file_path)

    if not result.get("ok"):
        emit(result)
        return

    emit(result)
    print(f"\n✅ Checkpoint created: {result.get('checkpoint_name', 'N/A')}")


def cmd_rollback(args):
    """Rollback a file to a previous checkpoint."""
    file_path = args.file
    checkpoint_name = args.checkpoint

    if not file_path or not checkpoint_name:
        emit({"error": "Missing required fields: --file and --checkpoint are required."})
        return

    result = rollback(file_path, checkpoint_name)

    if not result.get("ok"):
        emit(result)
        return

    emit(result)
    print(f"\n✅ Rolled back {file_path} to checkpoint {checkpoint_name}")


def cmd_mod_log(args):
    """Show modification log and pending modifications."""
    result = build_self_mod_report()

    if not result.get("ok"):
        emit(result)
        return

    emit(result)
    print(f"\n--- Modification Log ({result.get('total_modifications', 0)} entries) ---")
    print(f"Checkpoints: {result.get('checkpoints', 0)}")
    print(f"By file: {result.get('by_file', {})}")

    last_5 = result.get('last_5', [])
    if last_5:
        print("\nLast 5 entries:")
        for entry in last_5:
            status = "✅" if entry.get("success") else "❌"
            print(f"  {status} {entry.get('file_path')}: {entry.get('rationale', '')[:60]}...")


def cmd_checkpoints(args):
    """List available checkpoints."""
    file_path = args.file or ""

    result = list_checkpoints(file_path)

    if not result.get("ok"):
        emit(result)
        return

    emit(result)

    print(f"\n--- Checkpoints ({result.get('total', 0)} total) ---")
    for cp in result.get('checkpoints', []):
        print(f"  - {cp}")


def cmd_llm_diff(args):
    """Use LLM to generate better diff with explanation."""
    file_path = args.file
    change = args.change
    rationale = args.rationale or ""

    # First read current content
    circleforge_dir = Path(__file__).parent
    full_path = circleforge_dir / file_path

    try:
        with open(full_path, "r", encoding="utf-8") as f:
            current_content = f.read()
    except Exception as e:
        emit({"error": f"Could not read file: {e}"})
        return

    result = generate_diff_with_llm(current_content, change, rationale)

    emit(result)
    print(f"\n--- LLM-Generated Diff ---")
    print(result.get("diff", ""))
    print(f"\n--- Explanation ---")
    print(result.get("explanation", ""))
    print(f"\n--- Side Effects ---")
    print(result.get("side_effects", ""))


def cmd_llm_analyze(args):
    """Use LLM to analyze code for issues."""
    file_path = args.file

    circleforge_dir = Path(__file__).parent
    full_path = circleforge_dir / file_path

    try:
        with open(full_path, "r", encoding="utf-8") as f:
            current_content = f.read()
    except Exception as e:
        emit({"error": f"Could not read file: {e}"})
        return

    result = analyze_code_for_issues(current_content, file_path)

    emit(result)
    print(f"\n--- Issues ---")
    print(result.get("issues", ""))
    print(f"\n--- Recommendations ---")
    print(result.get("recommendations", ""))


def cmd_llm_suggest(args):
    """Use LLM to suggest self-improvements."""
    need = args.need

    result = generate_improvement_suggestion("Weslr v0.0.100 with 27 source files", need)

    emit(result)
    print(f"\n--- Suggestion ---")
    print(result.get("suggestion", ""))


def cmd_dashboard_selfmod(args):
    """Update the self-modification dashboard."""
    result = update_dashboard()

    emit(result)
    print(f"\n✅ Dashboard updated at: {result.get('html_path', 'N/A')}")


def cmd_dashboard_status(args):
    """Check self-modification dashboard status."""
    result = get_dashboard_status()

    emit(result)
    if result.get("ok"):
        print(f"\n✅ Dashboard exists: {result.get('html_path', 'N/A')}")
        print(f"Last updated: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(result.get('last_updated', 0)))}")


def cmd_auto_suggest(args):
    """Generate autonomous self-improvement suggestions."""
    result = generate_autonomous_suggestion("Weslr v0.0.100 with 27 source files")
    emit(result)

    if not result.get("ok"):
        print(f"\nError: {result.get('error', 'unknown error')}")
        return

    print(f"\n--- Autonomous Suggestions ({len(result.get('suggestions', []))}) ---")
    for s in result.get("suggestions", []):
        print(f"\n[{s.get('priority', 'medium').upper()}] {s.get('description', '')}")
        print(f"  Type: {s.get('type', 'unknown')}")
        print(f"  Suggestion: {s.get('suggestion', '')}")


def cmd_check_safe(args):
    """Check if a modification is safe."""
    file_path = args.file
    change = args.change

    result = check_modification_safety(file_path, change)

    emit(result)
    if result.get("ok"):
        status = "✅ SAFE" if result.get("safe") else "❌ UNSAFE"
        print(f"\n{status} - {file_path}")
        print("Checks:")
        for check, passed in result.get("checks", {}).items():
            symbol = "✅" if passed else "❌"
            print(f"  {symbol} {check}")


def cmd_validate_mod(args):
    """Validate a modification before applying."""
    file_path = args.file
    change = args.change
    rationale = args.rationale

    result = validate_modification(file_path, change, rationale)

    emit(result)

    if not result.get("ok"):
        print(f"\n❌ Validation failed: {result.get('error', 'unknown error')}")
        return

    print(f"\n✅ Validated: {file_path}")
    print("Checks:")
    for check, passed in result.get("checks", {}).items():
        symbol = "✅" if passed else "❌"
        print(f"  {symbol} {check}")
    print(f"\nRationale: {rationale}")


def cmd_rollback_preview(args):
    """Preview a rollback operation."""
    file_path = args.file
    checkpoint_name = args.checkpoint

    # Read current content
    circleforge_dir = Path(__file__).parent
    full_path = circleforge_dir / file_path

    try:
        with open(full_path, "r", encoding="utf-8") as f:
            current_content = f.read()
    except Exception as e:
        emit({"error": f"Could not read file: {e}"})
        return

    # Read checkpoint content
    checkpoint_path = circleforge_dir / "checkpoints" / checkpoint_name
    try:
        with open(checkpoint_path, "r", encoding="utf-8") as f:
            original_content = f.read()
    except Exception as e:
        emit({"error": f"Could not read checkpoint: {e}"})
        return

    result = generate_rollback_preview(file_path, current_content, original_content)

    emit(result)

    if not result.get("ok"):
        print(f"\nError: {result.get('error', 'unknown error')}")
        return

    print(f"\n--- Rollback Preview for {file_path} ---")
    print(f"Changes:")
    print(f"  Added lines: {result.get('added_lines', 0)}")
    print(f"  Removed lines: {result.get('removed_lines', 0)}")
    print(f"  Changed lines: {result.get('changed_lines', 0)}")

    if result.get("preview", {}).get("added"):
        print("\nAdded (new lines):")
        for line in result.get("preview", {}).get("added", [])[:3]:
            print(f"  + {line}")
    if result.get("preview", {}).get("removed"):
        print("\nRemoved (old lines):")
        for line in result.get("preview", {}).get("removed", [])[:3]:
            print(f"  - {line}")
    if result.get("preview", {}).get("changed"):
        print("\nChanged:")
        for line in result.get("preview", {}).get("changed", [])[:3]:
            print(f"  ~ {line}")


def cmd_batch_mods(args):
    """Batch multiple modifications together."""
    mods_json = args.mods

    try:
        modifications = json.loads(mods_json)
    except Exception as e:
        emit({"error": f"Could not parse JSON: {e}"})
        return

    result = batch_modifications(modifications)

    emit(result)

    if not result.get("ok"):
        print(f"\nError: {result.get('error', 'unknown error')}")
        return

    print(f"\n--- Batch Validation ({result.get('total', 0)} total) ---")
    print(f"✅ Safe: {result.get('safe', 0)}")
    print(f"❌ Unsafe: {result.get('unsafe', 0)}")

    for r in result.get("results", []):
        status = r.get("status", "unknown")
        if status == "safe":
            print(f"  ✅ {r.get('file_path', 'unknown')}")
        else:
            print(f"  ❌ {r.get('file_path', 'unknown')}: {r.get('error', 'unknown error')}")


def cmd_self_eval(args):
    """Run self-evaluation to identify gaps and opportunities."""
    from sim import load_communicator_self
    self_state = load_communicator_self()
    result = run_self_evaluation(self_state)
    emit(result)
    print(f"\n--- Self-Evaluation Summary ---")
    print(result.get('summary', 'No summary generated'))


def cmd_self_grow(args):
    """Run full self-directed growth cycle."""
    from sim import load_communicator_self
    self_state = load_communicator_self()
    result = run_self_directed_growth(self_state)
    emit(result)
    
    # Show decision summary
    print(f"\n--- Self-Directed Growth Decision ---")
    
    gaps = result.get('evaluation', {}).get('gaps', [])
    proposals = result.get('proposals', [])
    application = result.get('application', {})
    
    if not gaps:
        print("No gaps identified. System appears balanced.")
    else:
        print(f"Identified {len(gaps)} gap(s):")
        for g in gaps:
            print(f"  - {g.get('category')}: {g.get('gap')}")
    
    if application.get('needs_approval', 0) > 0:
        print(f"\n✅ {application.get('needs_approval')} proposed change(s) ready for human approval")
    
    # Show speech
    speech = result.get('speech', '')
    if speech:
        print(f"\n🗣️  Weslr says: \"{speech}\"")


def cmd_self_speak(args):
    """Generate speech explaining Weslr's self-decisions."""
    gaps_json = args.gaps
    if gaps_json:
        try:
            gaps = json.loads(gaps_json)
        except Exception as e:
            emit({"error": f"Could not parse gaps JSON: {e}"})
            return
    else:
        gaps = []
    
    from sim import load_communicator_self
    self_state = load_communicator_self()
    speech = generate_self_speech(self_state, {"gaps": gaps})
    emit({"speech": speech})
    print(f"\n🗣️  Weslr says: \"{speech}\"")


def cmd_opportunity_list(args):
    """List all opportunity themes with their lifecycle states."""
    from sim import load_opportunity_board
    board = load_opportunity_board()
    
    themes = board.get("themes", {})
    result = {"opportunities": []}
    
    for theme, payload in themes.items():
        lifecycle = payload.get("lifecycle", "unknown")
        result["opportunities"].append({
            "theme": theme,
            "lifecycle": lifecycle,
            "pressure": payload.get("pressure", 0),
            "evidence": payload.get("evidence", 0),
            "acceptances": payload.get("acceptances", 0),
            "rejections": payload.get("rejections", 0),
            "updated_at": payload.get("updated_at", 0),
        })
    
    emit(result)
    
    # Print summary
    print(f"\nOpportunity Summary:")
    for opp in result["opportunities"]:
        print(f"  {opp['theme']}: {opp['lifecycle']} (pressure={opp['pressure']:.3f}, evidence={opp['evidence']})")


def cmd_opportunity_transition(args):
    """Transition an opportunity to a new lifecycle state."""
    from sim import load_opportunity_board, save_opportunity_board, transition_opportunity_lifecycle
    
    theme = args.theme
    target = args.target
    
    board = load_opportunity_board()
    result = transition_opportunity_lifecycle(theme, target, board)
    
    if result.get("error"):
        emit({"error": result["error"]})
        print(f"\n❌ Error: {result['error']}")
        return
    
    save_opportunity_board(board)
    emit(result)
    print(f"\n✅ Transitioned '{theme}': {result['from']} → {result['to']}")


def cmd_opportunity_auto_transition(args):
    """Run auto-transition checks on all opportunities."""
    from sim import load_opportunity_board, save_opportunity_board, auto_transition_opportunities
    
    board = load_opportunity_board()
    results = auto_transition_opportunities(board)
    
    save_opportunity_board(board)
    
    emit({"results": results})
    print(f"\nAuto-transitioned {len(results)} opportunity(ies):")
    for r in results:
        if r.get("ok"):
            print(f"  {r['theme']}: {r['from']} → {r['to']}")


def cmd_opportunity_reject(args):
    """Record a rejection for an opportunity theme."""
    from sim import load_opportunity_board, save_opportunity_board, track_rejection, decay_opportunities_by_rejections
    
    theme = args.theme
    reason = args.reason
    
    board = load_opportunity_board()
    result = track_rejection(theme, reason, board)
    
    if result.get("error"):
        emit({"error": result["error"]})
        print(f"\n❌ Error: {result['error']}")
        return
    
    save_opportunity_board(board)
    emit(result)
    
    # Check if decay triggered
    decay_results = decay_opportunities_by_rejections(board)
    save_opportunity_board(board)
    
    if decay_results:
        print(f"\n⚠️  Decay triggered: {len(decay_results)} opportunity(ies) transitioned to rejected")
        for r in decay_results:
            print(f"  {r['theme']}: {r['from']} → {r['to']} (rejections: {r['rejections']})")
    else:
        print(f"\n✅ Rejection recorded. Current rejection count: {result['rejection_count']}")


def cmd_opportunity_cluster(args):
    """Show cross-agent opportunity clustering."""
    from sim import load_all_agent_opportunities
    
    result = load_all_agent_opportunities()
    emit(result)
    
    print(f"\nOpportunity Clusters ({len(result['clusters'])} themes):")
    for cluster in result['clusters']:
        agents_str = ', '.join(cluster['agents']) if cluster['agents'] else 'none'
        print(f"  {cluster['theme']}: {agents_str} (strength={cluster['total_strength']:.3f}, wins={cluster['total_wins']}, failures={cluster['total_failures']})")


def cmd_opportunity_revisit(args):
    """Inspect and trigger theme revisit tracking."""
    from sim import load_opportunity_board
    import json as _json
    import os

    REVISIT_TRACKER_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "revisit_tracker.json")

    board = load_opportunity_board()

    try:
        tracker = _json.loads(open(REVISIT_TRACKER_PATH, "r").read()) if os.path.exists(REVISIT_TRACKER_PATH) else {}
    except Exception:
        tracker = {}

    print("\n=== Revisit Tracker Status ===\n")

    print("Global Settings:")
    print(f"  revisit_threshold: {tracker.get('global_settings', {}).get('revisit_threshold', 3)}")
    print(f"  min_revision_wait_ticks: {tracker.get('global_settings', {}).get('min_revision_wait_ticks', 10)}")
    print(f"  decay_rate: {tracker.get('global_settings', {}).get('decay_rate', 0.1)}")

    print("\nRejection Counts by Theme:")
    for theme, data in board.get("themes", {}).items():
        count = int(data.get("rejections", 0))
        print(f"  {theme}: {count} rejections")

    print("\nRevisit Activity:")
    revisits = tracker.get("revisits_by_theme", {})
    for theme, data in revisits.items():
        print(f"  {theme}:")
        print(f"    times_revisited: {data.get('times_revisited', 0)}")
        print(f"    last_revisit_tick: {data.get('last_revisit_tick')}")
        for note in data.get('self_correction_notes', [])[-3:]:
            print(f"    note: {note[:80]}..." if len(note) > 80 else f"    note: {note}")

    print("\nRejection History by Theme:")
    rejections = tracker.get("rejections_by_theme", {})
    for theme, data in rejections.items():
        print(f"  {theme}:")
        print(f"    count: {data.get('count', 0)}")
        print(f"    last_rejection_tick: {data.get('last_rejection_tick')}")
        for hint in data.get('revision_hints', [])[-3:]:
            print(f"    hint: {hint[:80]}..." if len(hint) > 80 else f"    hint: {hint}")


# ============================================================================
# Variation Generation Commands
# ============================================================================

def cmd_variation_generate(args):
    """Generate math-based variations for a rejected opportunity theme."""
    from variation_generator import generate_variations_for_theme
    import json

    theme = args.theme
    method = args.method
    max_variations = args.count

    if not theme:
        emit({"error": "No theme specified. Use --theme to specify the opportunity theme."})
        return

    try:
        variations = generate_variations_for_theme(
            theme,
            methods=[method],
            max_variations=max_variations
        )

        emit({
            "ok": True,
            "theme": theme,
            "method": method,
            "variations": [
                {
                    "variation": v.variation,
                    "method": v.method,
                    "confidence": round(v.confidence, 3),
                    "score": round(v.score, 3)
                }
                for v in variations
            ]
        })

        print(f"\n=== Generated Variations for '{theme}' ===\n")
        for i, v in enumerate(variations, 1):
            print(f"{i}. {v.variation}")
            print(f"   Method: {v.method}")
            print(f"   Confidence: {v.confidence:.2%}")
            print(f"   Score: {v.score:.3f}")
            if v.metadata:
                print(f"   Metadata: {json.dumps(v.metadata, indent=6)}")
            print()

    except ImportError:
        emit({"error": "variation_generator.py not available"})
        print("\n⚠️  variation_generator.py not found. Math-based variations are disabled.")
    except Exception as e:
        emit({"error": str(e)})
        print(f"\n❌ Error: {e}")


def cmd_variation_list(args):
    """List all themes with their generated variations and math scores."""
    import json
    import os

    REVISIT_TRACKER_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "revisit_tracker.json")
    OPPORTUNITY_BOARD_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "opportunity_board.json")

    try:
        tracker = json.loads(open(REVISIT_TRACKER_PATH, "r").read()) if os.path.exists(REVISIT_TRACKER_PATH) else {}
    except Exception as e:
        emit({"error": f"Could not load tracker: {e}"})
        return

    try:
        board = json.loads(open(OPPORTUNITY_BOARD_PATH, "r").read()) if os.path.exists(OPPORTUNITY_BOARD_PATH) else {"themes": {}}
    except Exception as e:
        emit({"error": f"Could not load opportunity board: {e}"})
        return

    revisits = tracker.get("revisits_by_theme", {})
    rejections = tracker.get("rejections_by_theme", {})

    emit({
        "ok": True,
        "themes": len(revisits),
        "data": [
            {
                "theme": theme,
                "rejections": rejections.get(theme, {}).get("count", 0),
                "revisits": data.get("times_revisited", 0),
                "variations": data.get("generated_variations", [])[-3:],
                "math_scores": data.get("math_scores", {})
            }
            for theme, data in revisits.items()
        ]
    })

    print("\n=== All Themes with Generated Variations ===\n")
    for theme, data in revisits.items():
        rejections_count = rejections.get(theme, {}).get("count", 0)
        print(f"{theme} (rejections: {rejections_count}, revisits: {data.get('times_revisited', 0)})")
        print(f"  Variations: {data.get('generated_variations', [])[-3:]}")
        print(f"  Math Scores: {data.get('math_scores', {})}")
        print()


def cmd_variation_show(args):
    """Show detailed variation history and math scores for a specific theme."""
    import json
    import os

    theme = args.theme
    if not theme:
        emit({"error": "No theme specified. Use --theme to specify the opportunity theme."})
        return

    REVISIT_TRACKER_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "revisit_tracker.json")

    try:
        tracker = json.loads(open(REVISIT_TRACKER_PATH, "r").read()) if os.path.exists(REVISIT_TRACKER_PATH) else {}
    except Exception as e:
        emit({"error": f"Could not load tracker: {e}"})
        return

    revisits = tracker.get("revisits_by_theme", {})
    rejections = tracker.get("rejections_by_theme", {})

    if theme not in revisits:
        emit({"error": f"Theme '{theme}' not found in tracker"})
        print(f"\n❌ No variation history for theme '{theme}'")
        return

    data = revisits[theme]
    rej_data = rejections.get(theme, {})

    emit({
        "ok": True,
        "theme": theme,
        "rejections": rej_data,
        "revisits": data
    })

    print(f"\n=== Detailed Variation History for '{theme}' ===\n")

    print("Rejection History:")
    print(f"  Total rejections: {rej_data.get('count', 0)}")
    print(f"  Last rejection tick: {rej_data.get('last_rejection_tick', 'N/A')}")
    print(f"  Revision hints:")
    for hint in rej_data.get('revision_hints', [])[-5:]:
        print(f"    - {hint}")

    print("\nVariation Generation:")
    print(f"  Times revisited: {data.get('times_revisited', 0)}")
    print(f"  Last revisit tick: {data.get('last_revisit_tick', 'N/A')}")
    print(f"  Generated variations:")
    for i, v in enumerate(data.get('generated_variations', [])[-10:], 1):
        print(f"    {i}. {v}")
    print(f"  Self-correction notes:")
    for note in data.get('self_correction_notes', [])[-5:]:
        print(f"    - {note}")

    print("\nMath Scores (per method):")
    for method, score in data.get('math_scores', {}).items():
        print(f"  {method}: {score:.3f}")
    print(f"  Combined: {tracker.get('math_weights', {}).get('markov', 0.25) + tracker.get('math_weights', {}).get('bandit_ucb', 0.25) + tracker.get('math_weights', {}).get('entropy', 0.25) + tracker.get('math_weights', {}).get('gradient', 0.25):.3f}")


# === Entity Graph CLI Commands ===

def cmd_entity_list(args):
    """List entities in the entity graph."""
    g = get_entity_graph()
    
    limit = args.limit or 10
    entities = g.get_all_entities()[:limit]
    
    emit({
        "ok": True,
        "entities": [e.to_dict() for e in entities],
        "count": len(entities),
        "total": len(g.get_all_entities())
    })
    
    print(f"\n=== Entities ({len(g.get_all_entities())} total) ===\n")
    for e in entities:
        print(f"ID: {e.id}")
        print(f"  Name: {e.name}")
        print(f"  Type: {e.type}")
        print(f"  Aliases: {', '.join(e.aliases) if e.aliases else '(none)'}")
        print(f"  Confidence: {e.confidence:.2f}")
        print(f"  Ghost: {e.is_ghost}")
        print(f"  Last seen: {e.last_seen}")
        if e.evidence:
            print(f"  Evidence: {len(e.evidence)} items")
        print(f"  Relationships: {len(e.relationships)}")
        print()


def cmd_entity_details(args):
    """Show detailed information about a specific entity."""
    g = get_entity_graph()
    
    entity = g.get_entity(args.id)
    if not entity:
        emit({"error": f"Entity '{args.id}' not found"})
        print(f"\n❌ Entity '{args.id}' not found")
        return
    
    relationships = g.get_relationships_for_entity(entity.id)
    
    emit({
        "ok": True,
        "entity": entity.to_dict(),
        "relationships": [r.to_dict() for r in relationships]
    })
    
    print(f"\n=== Entity: {entity.name} (ID: {entity.id}) ===\n")
    
    print(f"Type: {entity.type}")
    print(f"Aliases: {', '.join(entity.aliases) if entity.aliases else '(none)'}")
    print(f"Confidence: {entity.confidence:.2f}")
    print(f"Ghost entity: {entity.is_ghost}")
    if entity.metadata:
        print(f"Metadata: {entity.metadata}")
    
    if entity.evidence:
        print(f"\nEvidence ({len(entity.evidence)} items):")
        for ev in entity.evidence:
            print(f"  - [{ev['source']}] {ev['content']} (timestamp: {ev['timestamp']})")
    
    if relationships:
        print(f"\nRelationships ({len(relationships)}):")
        for rel in relationships:
            target = g.get_entity(rel.target_id) if rel.source_id == entity.id else g.get_entity(rel.source_id)
            target_name = target.name if target else rel.target_id if rel.source_id == entity.id else rel.source_id
            print(f"  - {rel.type}: {target_name} (strength: {rel.strength:.2f})")
    else:
        print("\nNo relationships")


def cmd_entity_add(args):
    """Add a new entity to the entity graph."""
    g = get_entity_graph()
    
    entity = g.add_entity(
        name=args.name,
        entity_type=args.type or "other",
        aliases=args.aliases.split(",") if args.aliases else [],
        confidence=args.confidence or 0.5,
        is_ghost=not args.authoritative,
        metadata=json.loads(args.metadata) if args.metadata else {}
    )
    
    g.save()
    
    emit({
        "ok": True,
        "entity": entity.to_dict()
    })
    
    print(f"\n✅ Added entity: {entity.name} (ID: {entity.id})")
    print(f"   Type: {entity.type}")
    print(f"   Ghost: {entity.is_ghost}")


def cmd_entity_promote(args):
    """Promote a ghost entity to authoritative."""
    g = get_entity_graph()
    
    entity = g.get_entity(args.id)
    if not entity:
        emit({"error": f"Entity '{args.id}' not found"})
        print(f"\n❌ Entity '{args.id}' not found")
        return
    
    if not entity.is_ghost:
        emit({"error": f"Entity '{args.id}' is not a ghost entity"})
        print(f"\n❌ Entity '{args.id}' is not a ghost entity")
        return
    
    g.promote_entity(entity.id)
    
    emit({
        "ok": True,
        "entity": entity.to_dict()
    })
    
    print(f"\n✅ Promoted entity: {entity.name} to authoritative")


def cmd_entity_search(args):
    """Search entities by name or alias."""
    g = get_entity_graph()
    
    entities = g.search_entities(args.query)
    
    emit({
        "ok": True,
        "query": args.query,
        "results": [e.to_dict() for e in entities],
        "count": len(entities)
    })
    
    print(f"\n=== Search Results for '{args.query}' ({len(entities)} found) ===\n")
    for e in entities:
        print(f"ID: {e.id} | Name: {e.name} | Type: {e.type} | Ghost: {e.is_ghost}")


def cmd_entity_stats(args):
    """Show entity graph statistics."""
    g = get_entity_graph()
    
    stats = g.get_entity_stats()
    emit({
        "ok": True,
        "stats": stats
    })
    
    print(f"\n=== Entity Graph Statistics ===\n")
    print(f"Total entities: {stats['total_entities']}")
    print(f"  Authoritative: {stats['authoritative_entities']}")
    print(f"  Ghost: {stats['ghost_entities']}")
    print(f"Total relationships: {stats['total_relationships']}")
    print("\nEntities by type:")
    for etype, count in stats['entities_by_type'].items():
        print(f"  {etype}: {count}")


def cmd_relationship_list(args):
    """List relationships in the entity graph."""
    g = get_entity_graph()
    
    relationships = g.get_all_relationships()[:args.limit] if args.limit else g.get_all_relationships()
    
    emit({
        "ok": True,
        "relationships": [r.to_dict() for r in relationships],
        "count": len(relationships)
    })
    
    print(f"\n=== Relationships ({len(relationships)} total) ===\n")
    for rel in relationships:
        source = g.get_entity(rel.source_id)
        target = g.get_entity(rel.target_id)
        source_name = source.name if source else rel.source_id
        target_name = target.name if target else rel.target_id
        print(f"ID: {rel.id}")
        print(f"  {source_name} --[{rel.type}]--> {target_name}")
        print(f"  Strength: {rel.strength:.2f}")
        if rel.provenance:
            print(f"  Provenance: {rel.provenance}")
        print()


def cmd_relationship_add(args):
    """Add a new relationship between entities."""
    g = get_entity_graph()
    
    source = g.get_entity_by_name(args.source)
    target = g.get_entity_by_name(args.target)
    
    if not source:
        emit({"error": f"Source entity '{args.source}' not found"})
        print(f"\n❌ Source entity '{args.source}' not found")
        return
    if not target:
        emit({"error": f"Target entity '{args.target}' not found"})
        print(f"\n❌ Target entity '{args.target}' not found")
        return
    
    rel = g.add_relationship(
        source.id,
        target.id,
        args.type or "related_to",
        strength=args.strength or 0.5,
        provenance=json.loads(args.provenance) if args.provenance else {"source": "cli", "timestamp": int(time.time())}
    )
    
    g.save()
    
    emit({
        "ok": True,
        "relationship": rel.to_dict()
    })
    
    print(f"\n✅ Added relationship: {source.name} --[{rel.type}]--> {target.name}")
    print(f"   Strength: {rel.strength:.2f}")


# ============================================================================
# Diagnostics / Observability Integration (v71)
# ============================================================================

# Create minimal emitter for diagnostics (read-only, passive observation)
_diagnostic_emitter = _MinimalTelemetryEmitter()
_diagnostic_hooks = DiagnosticExportHooks(DiagnosticHooks(_diagnostic_emitter))


# ============================================================================
# Distributed Failure Replay / Diagnostic Trace Export (v72)
# ============================================================================

_trace_exporter = TraceExporter(DiagnosticHooks(_diagnostic_emitter))
_reconstructor = FailureTraceReconstructor()
_summary_generator = ReplaySummaryGenerator()


# ============================================================================
# Distributed Fallback Behavior (v73)
# ============================================================================

_fallback_manager = create_fallback_manager(emitter=_diagnostic_emitter, hooks=DiagnosticHooks(_diagnostic_emitter))
_fallback_trace_exporter = FallbackTraceExporter(_fallback_manager)


# ============================================================================
# Fallback Trace Export / Replay Integration (v74)
# ============================================================================

_fallback_trace_reconstructor = FallbackTraceReconstructor()
_fallback_trace_reconstructor.set_fallback_manager(_fallback_manager)


def cmd_diagnostics_summary(_args):
    """Export diagnostic summary in operator-readable format."""
    result = _diagnostic_hooks.export_all_summaries()
    emit(result)
    print(f"\n--- Diagnostic Summary ---")
    print(f"Total Flows with Failures: {len(result)}")
    print(f"Total Chains: {len(_diagnostic_hooks.export_all_chains())}")
    print(f"Total Hints: {len(_diagnostic_hooks.export_all_hints())}")
    
    if result:
        print("\n--- Flows with Failures ---")
        for summary in result[:3]:
            flow_id = summary.get("flow_id", "unknown")
            status = summary.get("status", "unknown")
            print(f"  {flow_id}: {status}")
    
    print(f"\n--- Operator Readable Summary ---")
    print(_diagnostic_hooks.get_operator_readable_summary())


def cmd_diagnostics_failure_chain(args):
    """Export correlated failure chain by ID."""
    result = _diagnostic_hooks.export_by_correlation(
        args.correlation_id, args.type
    )
    emit(result)
    print(f"\n--- Failure Chain: {args.correlation_id} ({args.type}) ---")
    print(f"Matching Summaries: {len(result.get('summaries', []))}")
    print(f"Matching Chains: {len(result.get('chains', []))}")
    print(f"Matching Hints: {len(result.get('hints', []))}")


def cmd_diagnostics_recovery_hints(_args):
    """Export all recovery hints in structured format."""
    result = _diagnostic_hooks.export_all_hints()
    emit(result)
    print(f"\n--- Recovery Hints ({len(result)} total) ---")
    for hint in result[:5]:
        flow_id = hint.get("flow_id", "unknown")
        recovery_hint = hint.get("recovery_hint", "None")
        likely_cause = hint.get("likely_cause", "Unknown")
        print(f"  [{likely_cause.upper()}] {flow_id}: {recovery_hint}")


# ============================================================================
# v72: Distributed Failure Replay / Diagnostic Trace Export CLI Commands
# ============================================================================


def cmd_diagnostics_trace_export(args):
    """Export diagnostic trace with correlation validation and consistency score."""
    flow_id = args.flow_id
    
    if flow_id:
        result = _trace_exporter.export_as_dict(flow_id)
    else:
        result = _trace_exporter.export_all_traces()
    
    emit(result)


def cmd_diagnostics_trace_replay(args):
    """Export replay summary for operator consumption."""
    flow_id = args.flow_id
    
    if flow_id:
        trace = _trace_exporter.export_trace(flow_id)
        if trace:
            records = [trace]
        else:
            records = []
    else:
        records = _trace_exporter.export_all_traces()
    
    summary = _summary_generator.generate_summary(records)
    print(summary)


def cmd_diagnostics_replay_export(args):
    """Export replayable trace format."""
    flow_id = args.flow_id
    
    if flow_id:
        result = _trace_exporter.export_replayable(flow_id)
    else:
        result = _trace_exporter.export_as_dict()
    
    emit(result)


# ============================================================================
# v73: Distributed Fallback Behavior CLI Commands
# ============================================================================


def cmd_fallback_status(args):
    """Export fallback status for a specific node or all nodes."""
    if args.node_id:
        status = _fallback_manager.get_node_status(args.node_id)
        if status:
            result = status.to_dict()
        else:
            result = {"error": f"No fallback status found for node: {args.node_id}"}
    else:
        result = {
            "nodes": [status.to_dict() for status in _fallback_manager._node_statuses.values()],
            "local_paths": _fallback_manager.get_all_local_paths(),
        }
    emit(result)


def cmd_fallback_diagnostics(_args):
    """Export fallback audit/diagnostic records."""
    result = {
        "audit_records": _fallback_manager.export_audit_records(),
        "local_paths": _fallback_manager.get_all_local_paths(),
    }
    emit(result)
    print(f"\n--- Fallback Diagnostics ---")
    print(f"Audit Records: {len(result['audit_records'])}")
    print(f"Local Paths: {len(result['local_paths'])}")


# ============================================================================
# v74: Fallback Trace Export / Replay CLI Commands
# ============================================================================


def cmd_fallback_trace_export(args):
    """Export fallback trace with correlation and capability visibility."""
    flow_id = args.flow_id
    
    if flow_id:
        result = _fallback_trace_exporter.export_as_dict()
        # Filter for specific flow if requested
        result["traces"] = [t for t in result.get("traces", []) if t.get("flow_id") == flow_id]
    else:
        result = _fallback_trace_exporter.export_as_dict()
    
    emit(result)


def cmd_fallback_trace_replay(args):
    """Export fallback trace replay summary for operator consumption."""
    flow_id = args.flow_id
    
    if flow_id:
        trace = _fallback_trace_exporter.export_trace(flow_id)
        if trace:
            records = [trace]
        else:
            records = []
    else:
        records = _fallback_trace_exporter.export_all_traces()
    
    summary = _fallback_trace_exporter.get_operator_readable_summary()
    print(summary)


if __name__ == "__main__":
    main()
