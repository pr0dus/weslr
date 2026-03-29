"""Agent management commands for Weslr.

Commands:
- agent-list [--limit N]
- agent-details <id>
- agent-create <name>
"""

from __future__ import annotations

import argparse
import json

from sim import show_agent


def cmd_agent_list(args: argparse.Namespace):
    """List agents."""
    agents = show_agent() or []
    
    limit = args.limit or 10
    for i, agent in enumerate(agents[:limit]):
        if isinstance(agent, dict):
            print(f"Agent {i+1}: {agent.get('name', 'unnamed')}")
            print(f"  ID: {agent.get('id', 'unknown')}")
            print(f"  Status: {agent.get('status', 'unknown')}")
            print()


def cmd_agent_details(args: argparse.Namespace):
    """Show agent details."""
    agents = show_agent() or []
    
    for agent in agents:
        if isinstance(agent, dict) and (agent.get('id') == args.id or agent.get('name') == args.id):
            print(json.dumps(agent, indent=2))
            return
    
    print(f"Agent '{args.id}' not found")


def cmd_agent_create(args: argparse.Namespace):
    """Create a new agent."""
    print(f"Creating agent: {args.name}")
    # Note: actual agent creation would require more parameters
    print("Agent creation not fully implemented yet")


def register_commands(subparsers: argparse._SubParsersAction) -> None:
    """Register agent-related subcommands."""
    # agent-list
    parser_list = subparsers.add_parser("agent-list", help="List agents")
    parser_list.add_argument("--limit", type=int, default=10, help="Maximum agents to show")
    parser_list.set_defaults(func=cmd_agent_list)

    # agent-details
    parser_details = subparsers.add_parser("agent-details", help="Show agent details")
    parser_details.add_argument("id", help="Agent ID or name")
    parser_details.set_defaults(func=cmd_agent_details)

    # agent-create
    parser_create = subparsers.add_parser("agent-create", help="Create a new agent")
    parser_create.add_argument("name", help="Agent name")
    parser_create.set_defaults(func=cmd_agent_create)
