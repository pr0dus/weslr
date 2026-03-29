"""Commands for Weslr Steuer (German tax law)."""

from __future__ import annotations

import sys
from pathlib import Path

# Add workspace to path
WORKSPACE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(WORKSPACE_DIR))

from commands import register_command


def cmd_steuer_list(args):
    """List all tax domains."""
    import steuerwesen_integration as si
    domains = si.get_steuerwesen_domains()
    print(f"Available tax domains ({len(domains)}):")
    for domain in domains:
        print(f"  - {domain}")


def cmd_steuer_search(args):
    """Search across tax law documentation."""
    import steuerwesen_integration as si
    query = args.query
    domain = getattr(args, 'domain', None)
    
    results = si.search_tax_laws(query, domain=domain)
    print(f"Search results for '{query}'{f' in {domain}' if domain else ''}:")
    print(f"  Found {len(results)} matches")
    
    for i, result in enumerate(results[:10], 1):
        print(f"  {i}. {result['law_file']} ({result['match_count']} matches)")
    
    if len(results) > 10:
        print(f"  ... and {len(results) - 10} more")


def cmd_steuer_laws(args):
    """List laws in a domain."""
    import steuerwesen_integration as si
    from steuerwesen import DOMAINS, LAW_FILES
    
    domain = args.domain
    if domain not in DOMAINS:
        print(f"Unknown domain: {domain}")
        print(f"Available domains: {', '.join(DOMAINS.keys())}")
        return
    
    domain_obj = DOMAINS[domain]
    print(f"Laws in '{domain}':")
    print(f"  Title: {domain_obj.title}")
    print(f"  Description: {domain_obj.description}")
    print(f"  Files: {len(domain_obj.laws)}")
    
    for law_file in domain_obj.laws:
        law_data = LAW_FILES.get(law_file, {})
        print(f"    - {law_file}: {law_data.get('title', 'N/A')}")


def cmd_steuer_translation(args):
    """Get translation for a key."""
    import steuerwesen_integration as si
    
    lang = args.lang
    key = args.key
    
    # Import steuerwesen module directly for translations
    import steuerwesen
    translation = steuerwesen.get_translation(lang, key, key)
    
    print(f"Translation ({lang} -> {key}): {translation}")


def register_commands(subparsers):
    """Register Steuerwesen CLI commands."""
    # steuer list
    parser_list = subparsers.add_parser("steuer-list", help="List all tax domains")
    parser_list.set_defaults(func=cmd_steuer_list)
    
    # steuer search
    parser_search = subparsers.add_parser("steuer-search", help="Search across tax law files")
    parser_search.add_argument("query", help="Search query")
    parser_search.add_argument("--domain", "-d", help="Filter by domain")
    parser_search.set_defaults(func=cmd_steuer_search)
    
    # steuer laws
    parser_laws = subparsers.add_parser("steuer-laws", help="List laws in a domain")
    parser_laws.add_argument("domain", help="Domain name")
    parser_laws.set_defaults(func=cmd_steuer_laws)
    
    # steuer translation
    parser_trans = subparsers.add_parser("steuer-translation", help="Get translation for a key")
    parser_trans.add_argument("lang", help="Language code (de, en)")
    parser_trans.add_argument("key", help="Translation key")
    parser_trans.set_defaults(func=cmd_steuer_translation)


# CLI entry point
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Weslr Steuer CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    register_commands(subparsers)
    
    args = parser.parse_args()
    if args.command:
        args.func(args)
    else:
        parser.print_help()
