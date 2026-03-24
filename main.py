from __future__ import annotations

import argparse
import json
import socket
import subprocess
import sys
import time
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from config import DEFAULT_AGENT_COUNT, PROJECT_NAME, TICK_SECONDS, VERSION
from llm_runtime import embedded_self_test
from sim import apply_pack_outcome, archive_memory, browse_queue, build_communicator_message, build_memory_layer_report, build_memory_score_report, category_action, distill_episodic_memory, distill_semantic_memory, explain_item, handoff_summary, init_world, load_communicator_self, load_communicator_state, load_evaluation_metrics, load_experiments, load_failsafe_status, load_llm_status, load_messages, load_needs, load_projects, load_public_memory, load_relationships, load_self_mod_proposals, load_work_items, monitor_memory_pressure, perform_tick, prepare_pack_offer, record_human_exchange, render_dashboard, review_artifact, show_agent, show_world, validate_artifact


def emit(data):
    print(json.dumps(data, indent=2))


def cmd_init(args):
    init_world(agent_count=args.agents, reset=args.reset)
    print(f"Initialized {PROJECT_NAME} with {args.agents} agents.")


def cmd_tick(args):
    emit(perform_tick(verbose=args.verbose))


def cmd_run(args):
    count = 0
    while args.ticks <= 0 or count < args.ticks:
        emit({"tick_run": count + 1, "results": perform_tick(verbose=args.verbose)})
        count += 1
        if args.ticks > 0 and count >= args.ticks:
            break
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


def cmd_memory_layers(_args):
    emit(build_memory_layer_report())


def cmd_memory_scores(_args):
    emit(build_memory_score_report())


def cmd_episodic_summarize(_args):
    emit(distill_episodic_memory())


def cmd_semantic_distill(_args):
    emit(distill_semantic_memory())


def cmd_memory_pressure(_args):
    emit(monitor_memory_pressure())


def cmd_archive_memory(_args):
    emit(archive_memory())


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
    handler = partial(SimpleHTTPRequestHandler, directory=str(dashboard_dir))
    server = ThreadingHTTPServer((args.host, args.port), handler)
    lan_ip = _detect_lan_ip()
    print("Dashboard server running.")
    print(f"Open locally: http://127.0.0.1:{args.port}/")
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

    p = sub.add_parser("archive-memory", help="manually archive low-priority traces once episodic/semantic preservation exists")
    p.set_defaults(func=cmd_archive_memory)

    p = sub.add_parser("communicator-message", help="show natural outward language plus behind-the-curtain metadata")
    p.set_defaults(func=cmd_communicator_message)

    p = sub.add_parser("speak", help="print only the natural outward message")
    p.set_defaults(func=cmd_speak)

    p = sub.add_parser("failsafe-status", help="show public external failsafe mode without exposing any secret")
    p.set_defaults(func=cmd_failsafe_status)

    p = sub.add_parser("llm-status", help="show whether CircleForge currently has live local-LLM access or is falling back")
    p.set_defaults(func=cmd_llm_status)

    p = sub.add_parser("embedded-self-test", help="run one direct embedded-provider self-test thought generation")
    p.set_defaults(func=cmd_embedded_self_test)

    p = sub.add_parser("human-exchange", help="record a remembered human conversation exchange into communicator self")
    p.add_argument("name")
    p.add_argument("message")
    p.add_argument("--response", default="")
    p.add_argument("--topics", nargs="*", default=None)
    p.add_argument("--resolved", action="store_true", help="mark the exchange as resolved instead of an open shared thread")
    p.set_defaults(func=cmd_human_exchange)

    p = sub.add_parser("eval-metrics", help="show evaluation metrics for the future bounded autonomy gate")
    p.set_defaults(func=cmd_eval_metrics)

    p = sub.add_parser("run-eval", help="reset the world, run a bounded evaluation pass, and emit communicator + metrics")
    p.add_argument("--ticks", type=int, default=25)
    p.add_argument("--agents", type=int, default=5)
    p.add_argument("--interval", type=int, default=0)
    p.add_argument("--verbose", action="store_true")
    p.set_defaults(func=cmd_run_eval)

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

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
