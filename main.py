from __future__ import annotations

import argparse
import json
import socket
import subprocess
import sys
import time
from functools import partial
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from time import strftime, localtime

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
)
from llm_diff_generator import generate_diff_with_llm, generate_improvement_suggestion, analyze_code_for_issues
from self_mod_dashboard import update_dashboard, get_dashboard_status
from self_mod_enhancements import generate_autonomous_suggestion, check_modification_safety, validate_modification, generate_rollback_preview, batch_modifications
from self_eval import run_self_evaluation, run_self_directed_growth, generate_self_speech
from sim import apply_pack_outcome, archive_memory, browse_queue, build_communicator_message, build_communicator_message_payload, build_identity_core_report, build_memory_layer_report, build_memory_lifecycle_report, build_memory_score_report, build_reflection_report, category_action, distill_episodic_memory, distill_semantic_memory, explain_item, handoff_summary, init_world, load_communicator_self, load_communicator_state, load_evaluation_metrics, load_experiments, load_failsafe_status, load_llm_status, load_messages, load_needs, load_projects, load_public_memory, load_relationships, load_self_mod_proposals, load_work_items, monitor_memory_pressure, perform_tick, prepare_pack_offer, prune_archived_memory, record_human_exchange, render_dashboard, review_artifact, save_public_memory, show_agent, show_world, validate_artifact
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


def emit(data):
    print(json.dumps(data, indent=2))


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
    
    # Custom handler that adds /chat endpoint to existing static file serving
    class ChatHandler(SimpleHTTPRequestHandler):
        def do_POST(self):
            if self.path == "/chat":
                content_length = int(self.headers.get("Content-Length", 0))
                body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else ""
                try:
                    import json as _json
                    data = _json.loads(body) if body else {}
                    human_name = data.get("name", "human")
                    message = data.get("message", "")
                    
                    payload = build_communicator_message_payload(
                        narrative=load_communicator_self().get("narrative_state", {}),
                        relationships=load_relationships(),
                        active_thread="human_message",
                        latest_human={"message": message},
                        research_context=None,
                    )
                    
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(_json.dumps(payload).encode("utf-8"))
                except Exception as e:
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(_json.dumps({"error": str(e)}).encode("utf-8"))
            else:
                self.send_error(404, "Unknown endpoint")

        def do_GET(self):
            """Serve GET requests - add /tia-history endpoint for history JSON."""
            if self.path == "/tia-history":
                import json as _json
                from pathlib import Path as _Path
                try:
                    workspace_root = Path(__file__).resolve().parent
                    history_path = workspace_root / "tia_import_history.json"
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
            else:
                # Fall back to default handler for other GET requests
                super().do_GET()
        
        def log_message(self, format, *args):
            # Suppress default logging for cleaner output
            pass
    
    handler = partial(ChatHandler, directory=str(dashboard_dir))
    server = ThreadingHTTPServer((args.host, args.port), handler)
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


if __name__ == "__main__":
    main()
