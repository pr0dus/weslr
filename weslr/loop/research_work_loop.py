"""
WESLR Research Work Loop V1

One-shot manual mission review for the Research Work Loop.
Loads active missions, reads local evidence, detects open questions,
generates safe candidate suggestions, applies safety filter,
ranks by confidence, writes to .weslr/pending_messages.jsonl.

V1 constraints:
- Manual run_once only (no auto-start, no scheduled cadence)
- Local evidence only (no external calls, no web requests)
- No automatic execution (all suggestions have automatic_execution=false)
- Safety filter blocks all forbidden categories
- Per-tenant mission isolation
"""

import json
import os
from datetime import datetime, timezone
from typing import Optional

from ..mission_store import MissionStore
from ..adapters.local_evidence_adapter import LocalEvidenceAdapter
from .safety_filter import get_safety_filter
from .suggestion_ranker import SuggestionRanker

# Path to pending messages store
PENDING_MESSAGES_PATH = ".weslr/pending_messages.jsonl"


def _write_pending_message(record: dict) -> None:
    """Append a record to the pending messages store."""
    directory = os.path.dirname(PENDING_MESSAGES_PATH)
    if directory and not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)

    with open(PENDING_MESSAGES_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")


def _detect_open_questions(
    mission,
    evidence_results: dict,
) -> list[dict]:
    """
    Detect open questions that have no matching evidence.

    Args:
        mission: Mission object
        evidence_results: Dict from LocalEvidenceAdapter.read()

    Returns:
        List of dicts with keys: question, has_evidence (bool), evidence_links (list)
    """
    open_questions = []

    for question in mission.current_questions:
        question_lower = question.lower()

        # Check if any evidence content mentions this question
        has_evidence = False
        matching_links = []

        for link, result in evidence_results.items():
            if result.get("safe") and result.get("content"):
                content_lower = result["content"].lower()
                # Simple keyword overlap check
                question_keywords = set(question_lower.split())
                content_words = set(content_lower.split())

                # If more than 30% of question keywords appear in content, consider it evidence
                if question_keywords and len(question_keywords & content_words) / len(question_keywords) > 0.3:
                    has_evidence = True
                    matching_links.append(link)

        open_questions.append({
            "question": question,
            "has_evidence": has_evidence,
            "evidence_links": matching_links,
        })

    return open_questions


def _generate_suggestion(
    mission,
    open_question: dict,
    evidence_results: dict,
    provenance: str,
) -> Optional[dict]:
    """
    Generate a suggestion for an open question with no evidence.

    Args:
        mission: Mission object
        open_question: Dict from _detect_open_questions
        evidence_results: Dict from LocalEvidenceAdapter.read()
        provenance: Provenance string for the suggestion

    Returns:
        Suggestion dict or None if no suggestion can be generated
    """
    if open_question["has_evidence"]:
        return None

    question = open_question["question"]
    evidence_links = open_question.get("evidence_links", [])

    # V1: Generate suggestion text based on what's missing
    # This is a rule-based suggestion, not generative AI
    domain_tags = mission.domain_tags
    domain_str = ", ".join(domain_tags) if domain_tags else "general"

    # Rule-based suggestion templates
    if evidence_links:
        suggestion_text = (
            f"Explore evidence gap for question: '{question}'. "
            f"Domain: {domain_str}. "
            f"Consider adding a material property comparison or experiment plan."
        )
    else:
        suggestion_text = (
            f"Add evidence for open question: '{question}'. "
            f"Domain: {domain_str}. "
            f"Suggest adding local evidence files or hypothesis comparison table."
        )

    return {
        "text": suggestion_text,
        "confidence": 0.7,
        "domain_relevance": 0.8 if domain_tags else 0.5,
        "evidence_count": len(evidence_links),
        "mission_id": mission.mission_id,
        "source": "local_evidence_adapter",
        "provenance": provenance,
    }


def run_once_mission_review(
    tenant_id: str,
    mission_id: Optional[str] = None,
    store_path: Optional[str] = None,
) -> dict:
    """
    Run one-shot mission review for a tenant.

    Loads active missions, reads local evidence, detects open questions
    with no evidence, generates safe suggestions, filters and ranks them,
    writes to pending messages store.

    Args:
        tenant_id: Tenant identifier
        mission_id: Optional specific mission ID to review (default: all active)
        store_path: Optional path to mission store (default: .weslr/missions.jsonl)

    Returns:
        Dict with keys: missions_reviewed, suggestions_generated, suggestions_written, errors
    """
    now = datetime.now(timezone.utc)
    timestamp = now.isoformat()
    provenance = f"run_once_mission_review @ {timestamp}"

    mission_store = MissionStore(store_path=store_path or ".weslr/missions.jsonl")
    evidence_adapter = LocalEvidenceAdapter()
    safety_filter = get_safety_filter()
    ranker = SuggestionRanker()

    result = {
        "missions_reviewed": 0,
        "suggestions_generated": 0,
        "suggestions_written": 0,
        "suggestions_blocked": 0,
        "errors": [],
    }

    # Load missions
    if mission_id:
        mission = mission_store.get(mission_id, tenant_id)
        missions = [mission] if mission else []
    else:
        missions = mission_store.load_active(tenant_id)

    for mission in missions:
        if not mission.is_active():
            continue

        result["missions_reviewed"] += 1

        try:
            # Read evidence for this mission
            evidence_results = evidence_adapter.read(mission.evidence_links)

            # Detect open questions with no evidence
            open_questions = _detect_open_questions(mission, evidence_results)

            # Generate candidate suggestions
            candidates = []
            for oq in open_questions:
                suggestion = _generate_suggestion(mission, oq, evidence_results, provenance)
                if suggestion:
                    candidates.append(suggestion)

            result["suggestions_generated"] += len(candidates)

            # Apply safety filter
            safe_candidates = []
            for c in candidates:
                if safety_filter.is_safe(c["text"]):
                    safe_candidates.append(c)
                else:
                    result["suggestions_blocked"] += 1

            if not safe_candidates:
                continue

            # Rank suggestions
            ranked = ranker.rank(safe_candidates, domain_tags=mission.domain_tags)
            top_suggestions = ranked[:5]  # Top 5 per mission

            # Write to pending messages
            for scored in top_suggestions:
                pending_record = {
                    "type": "mission_suggestion",
                    "mission_id": scored.mission_id,
                    "tenant_id": tenant_id,
                    "suggestion": scored.text,
                    "confidence": scored.confidence,
                    "domain_relevance": scored.domain_relevance,
                    "source": scored.source,
                    "evidence": mission.evidence_links,
                    "safety": "passed",
                    "provenance": scored.provenance,
                    "automatic_execution": False,
                    "operator_visible": True,
                    "public_user_visible": False,
                    "created_at": timestamp,
                }
                _write_pending_message(pending_record)
                result["suggestions_written"] += 1

        except Exception as e:
            result["errors"].append({
                "mission_id": mission.mission_id,
                "error": str(e),
            })

    return result


def get_last_review_summary(tenant_id: str) -> dict:
    """
    Get a summary of the last mission review for a tenant.

    Args:
        tenant_id: Tenant identifier

    Returns:
        Dict with last run info and suggestion counts
    """
    pending_path = PENDING_MESSAGES_PATH

    if not os.path.exists(pending_path):
        return {
            "last_run": None,
            "total_suggestions": 0,
            "missions_with_suggestions": [],
        }

    # Read last N mission suggestion records
    records = []
    with open(pending_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    record = json.loads(line)
                    if record.get("type") == "mission_suggestion" and record.get("tenant_id") == tenant_id:
                        records.append(record)
                except json.JSONDecodeError:
                    continue

    if not records:
        return {
            "last_run": None,
            "total_suggestions": 0,
            "missions_with_suggestions": [],
        }

    # Get last run timestamp
    timestamps = []
    for r in records:
        created = r.get("created_at", "")
        if created:
            timestamps.append(created)

    last_run = max(timestamps) if timestamps else None

    # Group by mission
    mission_ids = set(r.get("mission_id") for r in records)

    return {
        "last_run": last_run,
        "total_suggestions": len(records),
        "missions_with_suggestions": list(mission_ids),
    }