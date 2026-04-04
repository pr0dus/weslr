"""Human-in-the-Loop Integration for Weslr.

Provides CLI commands for entity curation, dashboard visualization,
self-improvement proposal review, and consciousness evidence logging.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import entity_graph as eg
import introspection as ins
import valence_system as vs
import metacognition as met
import self_referential as sr
import belief_system as bs
import self_improvement_proposal as sip
import weslr.pdf_text as pdf_text
import weslr.pdf_context as pdf_context
import weslr.file_ingestion as file_ingestion
import weslr.file_router as file_router

BASE_DIR = Path(__file__).resolve().parent


def print_entity_list(limit: int = 10):
    """List entities in the entity graph."""
    graph = eg.get_entity_graph()
    entities = graph.get_all_entities()[:limit]

    for entity in entities:
        ghost_marker = " (GHOST)" if entity.is_ghost else ""
        print(f"{entity.id}: {entity.name} ({entity.type}) - {entity.confidence:.2f}{ghost_marker}")


def print_entity_details(entity_id: str):
    """Show details for a specific entity."""
    graph = eg.get_entity_graph()
    entity = graph.get_entity(entity_id)

    if not entity:
        print(f"Entity {entity_id} not found")
        return

    print(json.dumps(entity.to_dict(), indent=2))


def print_relationship_list(limit: int = 10):
    """List relationships in the entity graph."""
    graph = eg.get_entity_graph()
    relationships = graph.get_all_relationships()[:limit]

    for rel in relationships:
        source = graph.get_entity(rel.source_id)
        target = graph.get_entity(rel.target_id)
        source_name = source.name if source else rel.source_id
        target_name = target.name if target else rel.target_id
        print(f"{rel.id}: {source_name} -> {target_name} ({rel.type}) - {rel.strength:.2f}")


def entity_merge(id1: str, id2: str):
    """Merge two entities."""
    graph = eg.get_entity_graph()
    e1 = graph.get_entity(id1)
    e2 = graph.get_entity(id2)

    if not e1 or not e2:
        print("✗ One or both entities not found")
        return False

    # Merge e2 into e1
    e1.aliases.extend(a for a in e2.aliases if a not in e1.aliases)
    e1.evidence.extend(e2.evidence)
    e1.confidence = min(1.0, e1.confidence + e2.confidence * 0.3)

    # Remove e2 and its relationships
    graph.delete_entity(id2)
    graph.update_entity(id1, aliases=e1.aliases, confidence=e1.confidence)

    print(f"✓ Merged '{e2.name}' into '{e1.name}'")
    return True


def entity_promote(entity_id: str):
    """Promote ghost entity to authoritative."""
    graph = eg.get_entity_graph()
    entity = graph.promote_entity(entity_id)

    if entity:
        print(f"✓ Promoted entity '{entity.name}' to authoritative")
        return True

    print(f"✗ Could not promote entity {entity_id}")
    return False


def print_self_evidence():
    """Print full self-evidence structure."""
    with open(BASE_DIR / "self_evidence.json", "r") as f:
        evidence = json.load(f)

    print(json.dumps(evidence, indent=2))


def print_weslr_status():
    """Print comprehensive Weslr status."""
    print("=" * 60)
    print("WESLR STATUS REPORT")
    print("=" * 60)

    # Entity graph stats
    graph = eg.get_entity_graph()
    stats = graph.get_entity_stats()
    print(f"\n📊 Entity Graph:")
    print(f"  Total entities: {stats['total_entities']}")
    print(f"  Authoritative: {stats['authoritative_entities']}")
    print(f"  Ghost: {stats['ghost_entities']}")
    print(f"  Total relationships: {stats['total_relationships']}")

    # Introspection
    monitor = ins.get_introspection_monitor()
    introspection = monitor.get_self_evidence()
    print(f"\n🧠 Introspection:")
    print(f"  Detected perturbations: {introspection['introspection']['total_perturbations']}")
    print(f"  Confidence signals: {introspection['introspection']['confidence_signals']}")

    # Metacognition
    meta = met.get_metacognitive_monitor()
    metacognition = meta.get_self_evidence()
    print(f"\n⚙️  Metacognition:")
    print(f"  Meta thoughts: {metacognition['meta_thoughts']}")
    print(f"  Attention shifts: {metacognition['attention_shares']}")
    print(f"  Self-referential: {metacognition['self_referential_count']}")

    # Valence
    valence = vs.get_valence_system()
    valence_evidence = valence.get_valence_evidence()
    print(f"\n⚖️  Valence:")
    print(f"  Pain avoided: {valence_evidence['valence']['avoided_pain']}")
    print(f"  Pleasure sought: {valence_evidence['valence']['sought_pleasure']}")
    print(f"  Total tradeoffs: {valence_evidence['valence']['total_tradeoffs']}")

    # Self-referential
    self_ref = sr.get_self_referential_processor()
    self_ref_evidence = self_ref.get_self_referential_evidence()
    print(f"\n🔄 Self-Referential:")
    print(f"  Events: {self_ref_evidence['total_events']}")
    print(f"  With markers: {self_ref_evidence['self_referential_events']}")

    # Belief system
    belief = bs.get_belief_system()
    belief_evidence = belief.get_self_evidence()
    print(f"\n🤔 Belief System:")
    print(f"  Total beliefs: {belief_evidence['total_beliefs']}")
    print(f"  Avg confidence: {belief_evidence['avg_confidence']:.3f}")
    print(f"  Avg coherence: {belief_evidence['avg_coherence']:.3f}")

    print("\n" + "=" * 60)


def main():
    """CLI entry point for Human-in-the-Loop Integration."""
    if len(sys.argv) < 2:
        print("Weslr Human-in-the-Loop CLI")
        print("\nCommands:")
        print("  entity-list [--limit N]      List entities")
        print("  entity-details <id>          Show entity details")
        print("  rel-list [--limit N]         List relationships")
        print("  entity-merge <id1> <id2>     Merge two entities")
        print("  entity-promote <id>          Promote ghost to authoritative")
        print("  evidence                     Show self-evidence structure")
        print("  status                       Show comprehensive Weslr status")
        print("")
        print("  operator <action> [args]     Self-improvement proposal review")
        print("    Available actions:")
        print("      list                       List all proposals (operator-only)")
        print("      review <id> <action>       Review a proposal")
        print("        Actions: approve, deny, mark-eligible")
        print("")
        print("  pdf-extract <file>         Extract text from PDF (operator-only)")
        print("    --mode <summary|excerpts|full>  Output mode (default: summary)")
        print("")
        print("  file-ingest <file>         Ingest text-based file (operator-only)")
        print("    Supports: .txt, .md, .json, .yaml, .yml, .py, .js, .ts, etc.")
        print("")
        print("  file-route <file>          Unified file routing (operator-only)")
        print("    Routes: PDF → PDF understanding, Text → Generic ingestion")
        print("")
        print("    Examples:")
        print("      weslr_cli.py operator list")
        print("      weslr_cli.py operator detail prop-123")
        print("      weslr_cli.py operator review prop-123 approve")
        print("      weslr_cli.py operator review prop-123 deny 'Missing tests'")
        print("      weslr_cli.py operator review prop-123 mark-eligible")
        print("      weslr_cli.py pdf-extract /path/to/file.pdf --mode summary")
        print("      weslr_cli.py pdf-extract /path/to/file.pdf --mode excerpts")
        print("      weslr_cli.py pdf-extract /path/to/file.pdf --mode full")
        print("      weslr_cli.py file-ingest /path/to/file.txt")
        print("      weslr_cli.py file-ingest /path/to/file.md")
        print("      weslr_cli.py file-route /path/to/file.pdf")
        print("      weslr_cli.py file-route /path/to/file.txt")
        print("")
        print("Usage: python weslr_cli.py <command> [args]")
        return

    command = sys.argv[1]

    if command == "entity-list":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        print_entity_list(limit)

    elif command == "entity-details":
        if len(sys.argv) < 3:
            print("Usage: weslr_cli.py entity-details <entity_id>")
            return
        print_entity_details(sys.argv[2])

    elif command == "rel-list":
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        print_relationship_list(limit)

    elif command == "entity-merge":
        if len(sys.argv) < 4:
            print("Usage: weslr_cli.py entity-merge <id1> <id2>")
            return
        entity_merge(sys.argv[2], sys.argv[3])

    elif command == "entity-promote":
        if len(sys.argv) < 3:
            print("Usage: weslr_cli.py entity-promote <entity_id>")
            return
        entity_promote(sys.argv[2])

    elif command == "evidence":
        print_self_evidence()

    elif command == "status":
        print_weslr_status()

    elif command == "operator":
        handle_operator_command()

    elif command == "pdf-extract":
        if len(sys.argv) < 3:
            print("Usage: python weslr_cli.py pdf-extract <pdf_file_path> [--mode summary|excerpts|full]")
            return
        # Parse arguments
        pdf_path = sys.argv[2]
        mode = "summary"  # default
        for i, arg in enumerate(sys.argv):
            if arg == "--mode" and i + 1 < len(sys.argv):
                mode = sys.argv[i + 1]
        handle_pdf_extract(pdf_path, mode)

    elif command == "file-ingest":
        if len(sys.argv) < 3:
            print("Usage: python weslr_cli.py file-ingest <file_path>")
            return
        file_path = sys.argv[2]
        handle_file_ingest(file_path)

    elif command == "file-route":
        if len(sys.argv) < 3:
            print("Usage: python weslr_cli.py file-route <file_path>")
            return
        file_path = sys.argv[2]
        handle_file_route(file_path)

    else:
        print(f"Unknown command: {command}")
        print("Run 'weslr_cli.py' for help")


def handle_operator_command():
    """Handle operator-only self-improvement proposal review actions.
    
    This is the single operator-facing entry point for proposal review actions.
    All actions are operator-only and do NOT expose anything to public-facing output.
    """
    if len(sys.argv) < 3:
        print("Operator Self-Improvement Proposal Review")
        print("")
        print("Commands:")
        print("  list                       List all proposals")
        print("  detail <id>                Show proposal details")
        print("  review <id> <action>       Review a proposal")
        print("    Actions: approve, deny, mark-eligible")
        print("")
        print("Usage: python weslr_cli.py operator <command> [args]")
        return

    subcommand = sys.argv[2]

    if subcommand == "list":
        handle_operator_list()

    elif subcommand == "detail":
        if len(sys.argv) < 4:
            print("Usage: python weslr_cli.py operator detail <proposal_id>")
            return
        proposal_id = sys.argv[3]
        handle_operator_detail(proposal_id)

    elif subcommand == "review":
        if len(sys.argv) < 5:
            print("Usage: python weslr_cli.py operator review <proposal_id> <action> [reason]")
            print("Actions: approve, deny, mark-eligible")
            return
        proposal_id = sys.argv[3]
        action = sys.argv[4]
        reason = sys.argv[5] if len(sys.argv) > 5 else None
        handle_operator_review(proposal_id, action, reason)

    else:
        print(f"Unknown operator command: {subcommand}")
        print("Run 'weslr_cli.py operator' for help")


def handle_operator_list():
    """List all proposals (operator-only, bypasses public visibility)."""
    result = sip.list_proposals_operator()
    
    if not result.get("ok"):
        print(f"✗ Error: {result.get('error', 'Unknown error')}")
        return
    
    proposals = result.get("proposals", [])
    total = result.get("total", 0)
    
    print(f"Proposals: {total}")
    print("=" * 60)
    
    for p in proposals:
        review_state = p.get("review", {}).get("state", "unknown")
        status = p.get("status", "unknown")
        print(f"[{p.get('id')}] {p.get('title')}")
        print(f"    Status: {status} | Review: {review_state}")
        print(f"    Risk: {p.get('risk_level', 'unknown')}")
        print()
    
    if not proposals:
        print("(No proposals)")


def handle_pdf_extract(pdf_path: str, mode: str = "summary"):
    """Extract and analyze PDF context (operator-only).
    
    This is a context-aware PDF extraction function that:
    - Validates the path is within workspace
    - Extracts only text content (no images, no code)
    - Connects to user query and task context
    - Returns formatted output with relevance assessment
    
    Args:
        pdf_path: Path to PDF file (must be within workspace)
        mode: Output mode - summary (compact), excerpts (relevant sections), full (all text)
    """
    workspace_dir = str(Path(__file__).resolve().parent)
    
    # Default user query for context (will be replaced by actual query in future)
    user_query = "What is in this document?"
    task_context = {"type": "document_analysis", "focus": "content"}
    
    # Validate mode
    valid_modes = ["summary", "excerpts", "full"]
    if mode not in valid_modes:
        mode = "summary"  # Default
    
    try:
        # Read PDF bytes first (for context_aware_pdf)
        with open(pdf_path, 'rb') as f:
            pdf_bytes = f.read()
        
        # Create context-aware PDF analysis using bytes
        pdf_ctx = pdf_context.create_pdf_context(
            pdf_bytes,
            user_query=user_query,
            task_context=task_context,
            max_chars=50000,  # 50KB for chat context
        )
        
        # Get formatted output
        output = pdf_context.context_aware_pdf(
            pdf_bytes,
            user_query=user_query,
            task_context=task_context,
            max_chars=50000,
        )
        
        # Generate mode-specific output
        if mode == "summary":
            output = pdf_context.context_aware_pdf_summary(
                pdf_bytes,
                user_query=user_query,
                task_context=task_context,
                max_chars=1500,
            )
        elif mode == "excerpts":
            output = pdf_context.context_aware_pdf_excerpts(
                pdf_bytes,
                user_query=user_query,
                task_context=task_context,
                max_chars=5000,
            )
        else:  # full
            output = pdf_context.context_aware_pdf(
                pdf_bytes,
                user_query=user_query,
                task_context=task_context,
                max_chars=50000,
            )
        
        # Also show raw extracted text for review
        raw_text = pdf_text.sanitize_extracted_text(pdf_ctx.extracted_text)
        
        print(f"{'=' * 60}")
        print(f"PDF CONTEXT ANALYSIS")
        print(f"{'=' * 60}")
        print(f"File: {pdf_path}")
        print(f"Relevance: {pdf_ctx.relevance}")
        print(f"Relevance Reason: {pdf_ctx.relevance_reason}")
        print(f"Content Length: {len(pdf_ctx.extracted_text)} chars")
        print(f"{'=' * 60}")
        print()
        
        # Show main output (context-aware)
        print(output[:8000])
        if len(output) > 8000:
            print(f"\n... [truncated, total: {len(output)} chars]")
        
        print()
        print(f"{'=' * 60}")
        print("RAW EXTRACTED TEXT (for operator review)")
        print(f"{'=' * 60}")
        print(raw_text[:3000])
        if len(raw_text) > 3000:
            print(f"\n... [{len(raw_text)} chars total]")
        print(f"{'=' * 60}")

        
    except pdf_context.PDFContextExtractionError as e:
        print(f"✗ PDF context extraction error: {e}")
        return
    except pdf_text.PDFTextExtractionError as e:
        print(f"✗ PDF text extraction error: {e}")
        return
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return



def handle_operator_detail(proposal_id: str):
    """Show detailed proposal info for operator review.
    
    This is an operator-only view that bypasses public visibility.
    Public-facing code paths should NOT use this.
    """
    result = sip.get_proposal_operator(proposal_id)
    
    if not result:
        print(f"✗ Proposal not found: {proposal_id}")
        return
    
    print(f"{'=' * 60}")
    print(f"PROPOSAL DETAILS: {proposal_id}")
    print(f"{'=' * 60}")
    
    print(f"\nTitle: {result.get('title')}")
    print(f"ID: {result.get('id')}")
    print(f"\nStatus: {result.get('status', 'unknown')}")
    print(f"Review State: {result.get('review', {}).get('state', 'unknown')}")
    print(f"Risk Level: {result.get('risk_level', 'unknown')}")
    
    # Timeline
    created_at = result.get('created_at', 0)
    if created_at:
        from datetime import datetime
        dt = datetime.fromtimestamp(created_at / 1000)
        print(f"Created: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Review info
    review = result.get('review', {})
    if review.get('reviewed_by'):
        reviewed_at = review.get('reviewed_at', 0)
        if reviewed_at:
            dt = datetime.fromtimestamp(reviewed_at)
            print(f"Reviewed by: {review.get('reviewed_by')} on {dt.strftime('%Y-%m-%d %H:%M:%S')}")
        else:
            print(f"Reviewed by: {review.get('reviewed_by')}")
    else:
        print("Review: Pending")


def handle_file_ingest(file_path: str):
    """Ingest a text-based file (operator-only).
    
    This is a text-based file ingestion function that:
    - Validates the path is within workspace
    - Only supports text-based formats (.txt, .md, .json, .yaml, etc.)
    - Returns formatted output with relevance assessment
    
    Args:
        file_path: Path to file (must be within workspace)
    """
    workspace_dir = str(Path(__file__).resolve().parent)
    
    # Default user query for context
    user_query = "What is in this file?"
    task_context = {"type": "file_analysis", "focus": "content"}
    
    try:
        # Create file ingestor
        ingestor = file_ingestion.create_file_ingestor(workspace_dir=workspace_dir)
        
        # Ingest file
        result = ingestor.ingest(file_path, user_query=user_query, task_context=task_context)
        
        print(f"{'=' * 60}")
        print(f"FILE INGESTION RESULT")
        print(f"{'=' * 60}")
        print(f"File: {file_path}")
        print(f"File Type: {result.file_type}")
        print(f"Content Type: {result.content_type}")
        print(f"Relevance: {result.relevance}")
        print(f"Relevance Reason: {result.relevance_reason}")
        print(f"Content Length: {len(result.content)} chars")
        print(f"{'=' * 60}")
        print()
        
        # Show content (truncated if needed)
        print(result.content[:5000])
        if len(result.content) > 5000:
            print(f"\n... [{len(result.content)} chars total]")
        
        print()
        print(f"{'=' * 60}")
        
    except file_ingestion.IngestionError as e:
        print(f"✗ File ingestion error: {e}")
        return
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return


def handle_file_route(file_path: str):
    """Route a file through unified file router (operator-only).
    
    This routes files to appropriate understanding modules:
    - PDF files → PDF understanding
    - Text-based files → Generic ingestion
    
    Args:
        file_path: Path to file (must be within workspace)
    """
    workspace_dir = str(Path(__file__).resolve().parent)
    
    # Default user query for context
    user_query = "What is in this file?"
    task_context = {"type": "file_analysis", "focus": "content"}
    
    try:
        # Create file router
        router = file_router.create_file_router(workspace_dir=workspace_dir)
        
        # Route file
        result = router.route(file_path, user_query=user_query, task_context=task_context)
        
        print(f"{'=' * 60}")
        print(f"FILE ROUTE RESULT")
        print(f"{'=' * 60}")
        print(f"File: {file_path}")
        print(f"Category: {result.category}")
        print(f"File Type: {result.file_type}")
        print(f"Content Type: {result.content_type}")
        print(f"Relevance: {result.relevance}")
        print(f"Relevance Reason: {result.relevance_reason}")
        print(f"Content Length: {len(result.content)} chars")
        print(f"{'=' * 60}")
        print()
        
        # Show content (truncated if needed)
        print(result.content[:5000])
        if len(result.content) > 5000:
            print(f"\n... [{len(result.content)} chars total]")
        
        print()
        print(f"{'=' * 60}")
        
    except file_router.FileRouterError as e:
        print(f"✗ File routing error: {e}")
        return
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return


def handle_operator_detail(proposal_id: str):
    print(f"  {result.get('problem', '(none)')}")
    print(f"\nLikely Cause:")
    print(f"  {result.get('likely_cause', '(none)')}")
    
    # Files to change
    files = result.get('files_to_change', [])
    if files:
        print(f"\nFiles to Change ({len(files)}):")
        for f in files:
            print(f"  - {f}")
    
    # Expected benefit
    print(f"\nExpected Benefit:")
    print(f"  {result.get('expected_benefit', '(none)')}")
    
    # Observations
    obs_ids = result.get('observation_ids', [])
    if obs_ids:
        print(f"\nObservation IDs: {', '.join(obs_ids)}")
    
    # Phase 1B fields
    if result.get('test_prompts'):
        print(f"\nTest Prompts: {len(result.get('test_prompts'))} test(s)")
    if result.get('rollback_command'):
        print(f"\nRollback Command:")
        print(f"  {result.get('rollback_command')}")
    if result.get('patch_plan'):
        print(f"\nPatch Plan: Available")
    
    # Test exemption
    if result.get('test_exempt'):
        print(f"\nTest Exempt: Yes")
        if result.get('test_exempt_justification'):
            print(f"  Justification: {result.get('test_exempt_justification')}")
    
    # Approval log
    approval = result.get('approval', {})
    if approval.get('denial_reason'):
        print(f"\nDenial Reason:")
        print(f"  {approval.get('denial_reason')}")
    
    print(f"\n{'=' * 60}")


def handle_operator_review(proposal_id: str, action: str, reason: str | None = None):
    """Handle a single proposal review action.
    
    Args:
        proposal_id: ID of proposal to review
        action: One of: approve, deny, mark-eligible
        reason: Optional reason for deny action
    """
    action = action.lower()
    
    if action not in ("approve", "deny", "mark-eligible"):
        print(f"Unknown action: {action}")
        print("Valid actions: approve, deny, mark-eligible")
        return
    
    # Get operator identity (for audit trail)
    # In production, this would come from auth - for now, use placeholder
    reviewed_by = "human-operator"
    
    if action == "approve":
        result = sip.approve_proposal(proposal_id, reviewed_by)
        
    elif action == "deny":
        if not reason:
            print("Deny action requires a reason. Usage:")
            print("  weslr_cli.py operator review <id> deny <reason>")
            return
        result = sip.deny_proposal(proposal_id, reason)
        
    elif action == "mark-eligible":
        result = sip.mark_as_eligible(proposal_id, reviewed_by)
    
    # Report result
    if result.get("ok"):
        print(f"✓ Action successful: {action}")
        if action == "approve":
            print(f"  Proposal {proposal_id} approved")
        elif action == "deny":
            print(f"  Proposal {proposal_id} denied")
        elif action == "mark-eligible":
            print(f"  Proposal {proposal_id} marked eligible for application")
    else:
        print(f"✗ Action failed: {result.get('error', 'Unknown error')}")


if __name__ == "__main__":
    main()
