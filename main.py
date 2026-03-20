from __future__ import annotations

import argparse
import json
import time

from config import DEFAULT_AGENT_COUNT, TICK_SECONDS
from sim import init_world, perform_tick, show_agent, show_world


def cmd_init(args):
    init_world(agent_count=args.agents, reset=args.reset)
    print(f"Initialized world with {args.agents} agents.")


def cmd_tick(args):
    rows = perform_tick(verbose=args.verbose)
    print(json.dumps(rows, indent=2))


def cmd_run(args):
    count = 0
    while args.ticks <= 0 or count < args.ticks:
        rows = perform_tick(verbose=args.verbose)
        print(json.dumps({"tick": count + 1, "results": rows}, indent=2))
        count += 1
        if args.ticks > 0 and count >= args.ticks:
            break
        time.sleep(args.interval)


def cmd_show_world(_args):
    print(json.dumps(show_world(), indent=2))


def cmd_show_agent(args):
    print(json.dumps(show_agent(args.name), indent=2))


def cmd_reset(args):
    init_world(agent_count=args.agents, reset=True)
    print(f"Reset world with {args.agents} agents.")


def main():
    parser = argparse.ArgumentParser(description="CircleForge v0.0.1 - minimal coding-agent ecosystem sim")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init")
    p.add_argument("--agents", type=int, default=DEFAULT_AGENT_COUNT)
    p.add_argument("--reset", action="store_true")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("tick")
    p.add_argument("--verbose", action="store_true")
    p.set_defaults(func=cmd_tick)

    p = sub.add_parser("run")
    p.add_argument("--ticks", type=int, default=0, help="0 = forever")
    p.add_argument("--interval", type=int, default=TICK_SECONDS)
    p.add_argument("--verbose", action="store_true")
    p.set_defaults(func=cmd_run)

    p = sub.add_parser("show-world")
    p.set_defaults(func=cmd_show_world)

    p = sub.add_parser("show-agent")
    p.add_argument("name")
    p.set_defaults(func=cmd_show_agent)

    p = sub.add_parser("reset")
    p.add_argument("--agents", type=int, default=DEFAULT_AGENT_COUNT)
    p.set_defaults(func=cmd_reset)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
