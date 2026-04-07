"""Weslr CLI - Legacy commands.

Commands moved here from main.py:
- TIA import (cmd_tia_import, cmd_tia_history, cmd_tia_show)
- Modification commands (cmd_create_checkpoint, cmd_rollback, cmd_mod_log, cmd_checkpoints)
- LLM commands (cmd_llm_diff, cmd_llm_analyze, cmd_llm_suggest)
- Code translation commands (cmd_self_inspection, cmd_translate_code, cmd_explain_code, cmd_translate_error, cmd_search_tool)
- Propose/self-mod commands (cmd_propose_self_mod, cmd_propose_improvement, cmd_apply_mod)

This module holds legacy/out-of-scope commands that don't belong in the core Weslr CLI.
"""

from __future__ import annotations

import json
from pathlib import Path

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
from self_inspection import build_self_inspection_report
from code_translator import explain_code, translate_code_to_concept, translate_internal_theme_to_code
from error_translator import translate_error, translate_error_to_plain_english
from tool_search import explain_tool_usage, search_tool_and_synthesize
from self_modifier import build_proposal_report, propose_self_modification_report
from self_mod_applier import apply_modification, build_self_mod_report, create_checkpoint, list_checkpoints, rollback
from self_improvement_proposal import create_proposal, list_proposals, approve_proposal, deny_proposal, get_proposal, build_proposal_report as build_sci_proposal_report, load_proposals


def emit(data):
    """Emit JSON to stdout."""
    print(json.dumps(data, indent=2))


def register_commands(subparsers):
    """Register legacy command parsers."""
    
    # === TIA Import Commands ===
    tia_parser = subparsers.add_parser("tia-import", help="import TIA Openness export artifact")
    tia_parser.add_argument("--file", required=True, help="path to TIA export JSON")
    tia_parser.add_argument("--output", default="tia_import_result.json", help="output envelope JSON")
    tia_parser.set_defaults(func=cmd_tia_import)

    tia_history_parser = subparsers.add_parser("tia-history", help="list recent TIA import history records")
    tia_history_parser.add_argument("--limit", type=int, default=10, help="number of recent records to show")
    tia_history_parser.add_argument("--path", default="", help="override history file path")
    tia_history_parser.set_defaults(func=cmd_tia_history)

    tia_show_parser = subparsers.add_parser("tia-show", help="show detailed summary for one TIA import")
    tia_show_parser.add_argument("--path", default="", help="override history file path")
    tia_show_parser.add_argument("--index", type=int, default=None, help="record index (1-based, default: latest)")
    tia_show_parser.add_argument("--source", default=None, help="filter by source filename")
    tia_show_parser.set_defaults(func=cmd_tia_show)

    # === Checkpoint/Modification Commands ===
    checkpoint_parser = subparsers.add_parser("create-checkpoint", help="create a checkpoint of the current file state")
    checkpoint_parser.add_argument("--file", required=True, help="file to checkpoint")
    checkpoint_parser.set_defaults(func=cmd_create_checkpoint)

    rollback_parser = subparsers.add_parser("rollback", help="rollback a file to a previous checkpoint")
    rollback_parser.add_argument("--file", required=True, help="file to rollback")
    rollback_parser.add_argument("--checkpoint", required=True, help="checkpoint name to restore")
    rollback_parser.set_defaults(func=cmd_rollback)

    mod_log_parser = subparsers.add_parser("mod-log", help="show modification log and pending modifications")
    mod_log_parser.set_defaults(func=cmd_mod_log)

    checkpoints_parser = subparsers.add_parser("checkpoints", help="list available checkpoints")
    checkpoints_parser.add_argument("--file", default="", help="optional filter by file path")
    checkpoints_parser.set_defaults(func=cmd_checkpoints)

    # === LLM Commands ===
    llm_diff_parser = subparsers.add_parser("llm-diff", help="use LLM to generate better diff with explanation")
    llm_diff_parser.add_argument("--file", required=True, help="file to analyze")
    llm_diff_parser.add_argument("--change", required=True, help="proposed change")
    llm_diff_parser.add_argument("--rationale", default="", help="context for the change")
    llm_diff_parser.set_defaults(func=cmd_llm_diff)

    llm_analyze_parser = subparsers.add_parser("llm-analyze", help="use LLM to analyze code for issues")
    llm_analyze_parser.add_argument("--file", required=True, help="file to analyze")
    llm_analyze_parser.set_defaults(func=cmd_llm_analyze)

    llm_suggest_parser = subparsers.add_parser("llm-suggest", help="use LLM to suggest self-improvements")
    llm_suggest_parser.add_argument("--need", required=True, help="what needs improvement")
    llm_suggest_parser.set_defaults(func=cmd_llm_suggest)

    # === Self Inspection / Code Translation ===
    self_inspection_parser = subparsers.add_parser("self-inspection", help="run self-inspection and generate plain-English description of Weslr's code")
    self_inspection_parser.set_defaults(func=cmd_self_inspection)

    translate_code_parser = subparsers.add_parser("translate-code", help="translate code snippet to concepts and internal themes")
    translate_code_parser.add_argument("code", nargs="?", default="")
    translate_code_parser.add_argument("--snippet", default="", help="inline code snippet to translate")
    translate_code_parser.set_defaults(func=cmd_translate_code)

    explain_code_parser = subparsers.add_parser("explain-code", help="explain code snippet in plain English")
    explain_code_parser.add_argument("code", nargs="?", default="")
    explain_code_parser.add_argument("--snippet", default="", help="inline code snippet to explain")
    explain_code_parser.set_defaults(func=cmd_explain_code)

    translate_error_parser = subparsers.add_parser("translate-error", help="parse a Python traceback and explain the error")
    translate_error_parser.add_argument("--traceback", default="", help="inline traceback to translate")
    translate_error_parser.add_argument("--file", default="", help="file containing traceback text")
    translate_error_parser.set_defaults(func=cmd_translate_error)

    search_tool_parser = subparsers.add_parser("search-tool", help="search for tools/APIs and generate usage patterns")
    search_tool_parser.add_argument("--need", required=True, help="what you need to do (e.g., 'read web pages')")
    search_tool_parser.set_defaults(func=cmd_search_tool)

    # === Self-Modification Proposals ===
    propose_self_mod_parser = subparsers.add_parser("propose-self-mod", help="propose a self-modification with diff and rationale")
    propose_self_mod_parser.add_argument("--file", required=True, help="file to modify (relative to Weslr directory)")
    propose_self_mod_parser.add_argument("--change", required=True, help="what change to make")
    propose_self_mod_parser.add_argument("--rationale", required=True, help="why this change is needed")
    propose_self_mod_parser.set_defaults(func=cmd_propose_self_mod)

    propose_improvement_parser = subparsers.add_parser("propose-improvement", help="propose a self-improvement based on a need")
    propose_improvement_parser.add_argument("--need", required=True, help="what Weslr needs to do better")
    propose_improvement_parser.set_defaults(func=cmd_propose_improvement)

    apply_mod_parser = subparsers.add_parser("apply-mod", help="apply an approved self-modification (with checkpoint)")
    apply_mod_parser.add_argument("--file", required=True, help="file to modify")
    apply_mod_parser.add_argument("--change", required=True, help="what change to make")
    apply_mod_parser.add_argument("--rationale", required=True, help="why this change is needed")
    apply_mod_parser.add_argument("--approved-by", default="human", help="who approved the change")
    apply_mod_parser.set_defaults(func=cmd_apply_mod)


# ============================================================================
# TIA Import Commands
# ============================================================================

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

    output_path = Path(__file__).resolve().parent.parent / args.output
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
        output_stem = output_path.stem
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

        print(f"\nNormalized Summary:")
        print(f"  Project: {project_name}")
        print(f"  Total items: {total}")
        print(f"  Devices: {devices}")
        print(f"  PLCs: {plcs}")
        print(f"  CPUs: {cpus}")
    except Exception as e:
        print(f"\n⚠️  Normalization error: {e}")


def cmd_tia_history(args):
    """List recent TIA import history records."""
    records = list_tia_import_history()
    if args.limit > 0:
        records = records[-args.limit:]
    emit({
        "path": args.path if args.path else "tia_import_history.json",
        "count": len(records),
        "records": records,
    })


def cmd_tia_show(args):
    """Show detailed summary for one TIA import."""
    records = list_tia_import_history()
    
    if args.source:
        records = [r for r in records if args.source in r.get("source", "")]

    if args.index is not None:
        idx = args.index - 1  # 1-based index
        if 0 <= idx < len(records):
            record = records[idx]
            emit(record)
            return
        print(f"Index {args.index} out of range (1-{len(records)})")
        return

    if not records:
        print("No TIA import records found.")
        return

    # Show latest by default
    record = records[-1]
    emit(record)


# ============================================================================
# Checkpoint/Modification Commands
# ============================================================================

def cmd_create_checkpoint(args):
    """Create a checkpoint of the current file state."""
    result = create_checkpoint(args.file)
    emit(result)


def cmd_rollback(args):
    """Rollback a file to a previous checkpoint."""
    result = rollback(file=args.file, checkpoint=args.checkpoint)
    emit(result)


def cmd_mod_log(args):
    """Show modification log and pending modifications."""
    result = build_self_mod_report()
    emit(result)


def cmd_checkpoints(args):
    """List available checkpoints."""
    result = list_checkpoints(args.file if args.file else None)
    emit(result)


# ============================================================================
# LLM Commands
# ============================================================================

def cmd_llm_diff(args):
    """Use LLM to generate better diff with explanation."""
    result = generate_diff_with_llm(
        file=args.file,
        change=args.change,
        rationale=args.rationale,
    )
    emit(result)


def cmd_llm_analyze(args):
    """Use LLM to analyze code for issues."""
    result = analyze_code_for_issues(args.file)
    emit(result)


def cmd_llm_suggest(args):
    """Use LLM to suggest self-improvements."""
    need = args.need
    result = generate_improvement_suggestion(need=need)
    emit(result)


# ============================================================================
# Self Inspection / Code Translation Commands
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


# ============================================================================
# Self-Modification Proposal Commands
# ============================================================================

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
    emit(result)

    if result.get("ok"):
        print(f"\n✅ Applied: {file_path}")
        print(f"   Approved by: {approved_by}")
    else:
        print(f"\n❌ Apply failed: {result.get('error', 'unknown error')}")
