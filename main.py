from __future__ import annotations

import argparse
import json
import time

from config import DEFAULT_AGENT_COUNT, PROJECT_NAME, TICK_SECONDS, VERSION
from sim import init_world, perform_tick, review_artifact, show_agent, show_world


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


def cmd_reset(args):
    init_world(agent_count=args.agents, reset=True)
    print(f"Reset {PROJECT_NAME} with {args.agents} agents.")


def cmd_version(_args):
    print(f"{PROJECT_NAME} v{VERSION}")


def cmd_review(args):
    emit(review_artifact(args.id, args.action, note=args.note))


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

    p = sub.add_parser("show-world", help="show world state, demand board, export queue, review queue, and recent logs")
    p.set_defaults(func=cmd_show_world)

    p = sub.add_parser("show-agent", help="show one agent state")
    p.add_argument("name")
    p.set_defaults(func=cmd_show_agent)

    p = sub.add_parser("review", help="manually review an artifact by id")
    p.add_argument("id")
    p.add_argument("action", choices=["approve", "reject", "export", "note"])
    p.add_argument("--note", default="")
    p.set_defaults(func=cmd_review)

    p = sub.add_parser("reset", help="reset the world")
    p.add_argument("--agents", type=int, default=DEFAULT_AGENT_COUNT)
    p.set_defaults(func=cmd_reset)

    p = sub.add_parser("version", help="print release version")
    p.set_defaults(func=cmd_version)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
