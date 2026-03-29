"""Tool search commands for Weslr.

Commands:
- tool-search <query>
- tool-explain <tool>
- tool-lookup <query>
"""

from __future__ import annotations

import argparse
import json

from tool_search import explain_tool_usage, search_tool_and_synthesize, search_for_tool


def cmd_tool_search(args: argparse.Namespace):
    """Search for tools."""
    results = search_for_tool(args.query)
    print(f"Search results for '{args.query}':")
    if isinstance(results, dict):
        print(json.dumps(results, indent=2))
    else:
        print(json.dumps(results, indent=2) if results else "No results found")


def cmd_tool_explain(args: argparse.Namespace):
    """Explain a tool's usage."""
    explanation = explain_tool_usage(args.tool)
    print(f"Explanation for '{args.tool}':")
    print(explanation)


def cmd_tool_lookup(args: argparse.Namespace):
    """Look up tool usage."""
    result = search_tool_and_synthesize(args.query)
    print(f"Lookup result for '{args.query}':")
    if isinstance(result, dict):
        print(json.dumps(result, indent=2))
    else:
        print(result)


def register_commands(subparsers: argparse._SubParsersAction) -> None:
    """Register tool-related subcommands."""
    # tool-search
    parser_search = subparsers.add_parser("tool-search", help="Search for tools")
    parser_search.add_argument("query", help="Search query")
    parser_search.set_defaults(func=cmd_tool_search)

    # tool-explain
    parser_explain = subparsers.add_parser("tool-explain", help="Explain tool usage")
    parser_explain.add_argument("tool", help="Tool name")
    parser_explain.set_defaults(func=cmd_tool_explain)

    # tool-lookup
    parser_lookup = subparsers.add_parser("tool-lookup", help="Look up tool usage")
    parser_lookup.add_argument("query", help="Search query")
    parser_lookup.set_defaults(func=cmd_tool_lookup)
