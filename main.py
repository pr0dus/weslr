from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from config import DEFAULT_AGENT_COUNT, PROJECT_NAME, TICK_SECONDS, VERSION
from sim import apply_pack_outcome, browse_queue, category_action, explain_item, handoff_summary, init_world, perform_tick, prepare_pack_offer, render_dashboard, review_artifact, show_agent, show_world, validate_artifact


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


def cmd_setup(args):
    print(f"{PROJECT_NAME} v{VERSION} setup")
    print("This creates a fresh local world, runs some ticks, and renders the dashboard.")
    print()

    agents = args.agents if args.agents is not None else _prompt_int("How many agents?", DEFAULT_AGENT_COUNT, minimum=1)
    ticks = args.ticks if args.ticks is not None else _prompt_int("How many ticks to run? (0/inf = infinite)", 10, minimum=0, allow_infinite=True)
    interval = args.interval if args.interval is not None else _prompt_int("Seconds between ticks?", 0 if ticks > 0 else TICK_SECONDS, minimum=0)
    refresh = args.refresh if args.refresh is not None else _prompt_int("Dashboard auto-refresh seconds? (0 = off)", 5 if ticks == 0 else 0, minimum=0)

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
    print("Open this file in your browser:")
    print(f"  {dashboard_path}")
    print("If your browser prefers file URLs, open:")
    print(f"  file://{dashboard_path}")


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

    p = sub.add_parser("setup", help="guided first-run setup for a fresh local test")
    p.add_argument("--agents", type=int, help="how many agents to create")
    p.add_argument("--ticks", type=int, help="how many ticks to run; 0 = forever")
    p.add_argument("--interval", type=int, help="seconds between ticks")
    p.add_argument("--refresh", type=int, help="dashboard browser auto-refresh seconds; 0 = off")
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
