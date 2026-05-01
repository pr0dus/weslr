"""
External Evidence Pipeline V1

Read-only orchestrator connecting:
  Evidence Needed Detector → SearXNG Search Adapter
  → Evidence Packet Builder → Evidence Answer Builder

Search is disabled by default. No truth writes. No /chat integration.
"""

from weslr.evidence_needed_detector import classify_evidence_need
from weslr.searxng_search_adapter import is_searxng_enabled, search_searxng
from weslr.evidence_packet_builder import build_evidence_packet
from weslr.evidence_answer_builder import build_evidence_answer, build_no_evidence_answer


RECORD_TYPE = "external_evidence_pipeline_v1"


def run_evidence_pipeline(query: str, depth: str = "normal", config=None) -> dict:
    """
    Run the evidence pipeline for a query.

    Steps:
      1. Classify whether evidence is needed
      2. If yes and search enabled: perform search → build packet → build answer
      3. If search disabled: return search_disabled reason
      4. If no evidence needed: return no_evidence_needed

    Args:
        query: The user query string
        depth: "brief" | "normal" | "deep" (passed to answer builder)
        config: Optional dict to override adapter behavior (for testing)

    Returns:
        A dict with record_type "external_evidence_pipeline_v1".
    """
    try:
        # Step 1: Classify evidence need
        classification = classify_evidence_need(query)

        # Step 2: No evidence needed
        if not classification.get("evidence_needed", False):
            answer = build_no_evidence_answer(query, reason="no_evidence")
            return {
                "record_type": RECORD_TYPE,
                "query": query,
                "classification": classification,
                "search_response": None,
                "evidence_packet": None,
                "answer": answer,
                "authority": "external_evidence_unverified",
                "truth_status": "unverified",
                "automatic_truth_write": False,
                "search_attempted": False,
                "safe_for_user": answer.get("safe_for_user", True),
                "reason": "no_evidence_needed",
            }

        # Step 3: Evidence needed — check if search is enabled
        search_enabled = is_searxng_enabled()
        if config and "force_search_enabled" in config:
            search_enabled = config["force_search_enabled"]

        if not search_enabled:
            answer = build_no_evidence_answer(query, reason="adapter_disabled")
            return {
                "record_type": RECORD_TYPE,
                "query": query,
                "classification": classification,
                "search_response": None,
                "evidence_packet": None,
                "answer": answer,
                "authority": "external_evidence_unverified",
                "truth_status": "unverified",
                "automatic_truth_write": False,
                "search_attempted": False,
                "safe_for_user": answer.get("safe_for_user", True),
                "reason": "search_disabled",
            }

        # Step 4: Search enabled — attempt search
        try:
            search_response = search_searxng(query)
        except Exception:
            answer = build_no_evidence_answer(query, reason="search_failed")
            return {
                "record_type": RECORD_TYPE,
                "query": query,
                "classification": classification,
                "search_response": None,
                "evidence_packet": None,
                "answer": answer,
                "authority": "external_evidence_unverified",
                "truth_status": "unverified",
                "automatic_truth_write": False,
                "search_attempted": True,
                "safe_for_user": answer.get("safe_for_user", True),
                "reason": "search_failed",
            }

        # Step 5: Build evidence packet
        evidence_packet = build_evidence_packet(query, search_response)

        if not evidence_packet.get("safe_for_answer_builder", False):
            answer = build_no_evidence_answer(query, reason="search_failed")
            return {
                "record_type": RECORD_TYPE,
                "query": query,
                "classification": classification,
                "search_response": search_response,
                "evidence_packet": evidence_packet,
                "answer": answer,
                "authority": "external_evidence_unverified",
                "truth_status": "unverified",
                "automatic_truth_write": False,
                "search_attempted": True,
                "safe_for_user": answer.get("safe_for_user", True),
                "reason": "packet_failed",
            }

        # Step 6: Build answer
        try:
            answer = build_evidence_answer(query, evidence_packet, depth=depth)
        except Exception:
            answer = build_no_evidence_answer(query, reason="search_failed")
            return {
                "record_type": RECORD_TYPE,
                "query": query,
                "classification": classification,
                "search_response": search_response,
                "evidence_packet": evidence_packet,
                "answer": answer,
                "authority": "external_evidence_unverified",
                "truth_status": "unverified",
                "automatic_truth_write": False,
                "search_attempted": True,
                "safe_for_user": answer.get("safe_for_user", True),
                "reason": "answer_failed",
            }

        return {
            "record_type": RECORD_TYPE,
            "query": query,
            "classification": classification,
            "search_response": search_response,
            "evidence_packet": evidence_packet,
            "answer": answer,
            "authority": "external_evidence_unverified",
            "truth_status": "unverified",
            "automatic_truth_write": False,
            "search_attempted": True,
            "safe_for_user": answer.get("safe_for_user", False),
            "reason": "ok",
        }

    except Exception:
        # Catch-all: return safe failure
        answer = build_no_evidence_answer(query, reason="search_failed")
        return {
            "record_type": RECORD_TYPE,
            "query": query,
            "classification": None,
            "search_response": None,
            "evidence_packet": None,
            "answer": answer,
            "authority": "external_evidence_unverified",
            "truth_status": "unverified",
            "automatic_truth_write": False,
            "search_attempted": False,
            "safe_for_user": True,
            "reason": "search_failed",
        }