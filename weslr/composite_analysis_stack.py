"""
WESLR Composite Analysis Stack V1 — read-only analytical layer.

Core statement:
  "Structure filters the signal. Ranking finds similarity.
   Probability estimates confidence. Governance decides authority.
   Models may explain, never rule."

Authority: analysis_only
Automatic change: false
No LLM. No Ollama. No JSONL writes. No /chat integration.
"""

import json
import os
from pathlib import Path
from typing import Any, Optional

# ---------------------------------------------------------------------------
# Source file paths (relative to weslr/ in workspace)
# ---------------------------------------------------------------------------

_WESLR_ROOT = Path(__file__).parent if '__file__' in globals() else Path("/data/data/com.termux/files/home/.openclaw/workspace/weslr")

_PUBLIC_SIGNALS_FILE = _WESLR_ROOT / "public_signals.jsonl"
_CONTRACT_OBSERVATIONS_FILE = _WESLR_ROOT / "contract_observations.jsonl"
_CONTRACT_INSUFFICIENCY_FILE = _WESLR_ROOT / "contract_insufficiency_log.jsonl"
_CONTRACT_PROPOSAL_REVIEW_FILE = _WESLR_ROOT / "contract_proposal_review_log.jsonl"

# ---------------------------------------------------------------------------
# 1. Structural classification
# ---------------------------------------------------------------------------

_RECORD_TYPE_TO_STRUCTURE = {
    "public_signal_v1": "operational_signal",
    "contract_observation_v1": "observation_signal",
    "contract_insufficiency_v1": "insufficiency_evidence",
    "contract_proposal_review_v1": "review_candidate",
    "aai_attention_summary_v1": "attention_summary",
}

_SOURCE_FAMILY_MAP = {
    "public_signal_v1": "signal",
    "contract_observation_v1": "contract",
    "contract_insufficiency_v1": "contract",
    "contract_proposal_review_v1": "contract",
    "aai_attention_summary_v1": "aai",
}


def classify_structure(item: dict) -> dict:
    """
    Classify a record by its structural family.

    Returns:
        {
          "record_type": "composite_structure_v1",
          "input_record_type": "...",
          "structural_class": "...",
          "source_family": "...",
          "authority": "analysis_only"
        }
    """
    record_type = item.get("record_type", "unknown")
    structural_class = _RECORD_TYPE_TO_STRUCTURE.get(record_type, "unknown_signal")
    source_family = _SOURCE_FAMILY_MAP.get(record_type, "unknown")

    return {
        "record_type": "composite_structure_v1",
        "input_record_type": record_type,
        "structural_class": structural_class,
        "source_family": source_family,
        "authority": "analysis_only",
    }


# ---------------------------------------------------------------------------
# 2. Similarity scoring
# ---------------------------------------------------------------------------

_SIMILARITY_FIELD_WEIGHTS = {
    "record_type": 0.20,
    "response_contract": 0.20,
    "pattern_type": 0.20,
    "response_path": 0.15,
    "proposal_status": 0.15,
    "attention_level": 0.10,
}


def compute_similarity_score(item: dict, reference: Optional[dict] = None) -> dict:
    """
    Compute a deterministic similarity score between item and reference.

    If reference is None, returns a baseline score based on item's own completeness.

    Returns:
        {
          "record_type": "composite_similarity_v1",
          "score": 0.0-1.0,
          "matched_fields": [...],
          "authority": "analysis_only"
        }
    """
    if reference is None:
        # Score based on structural completeness of the item itself
        matched_fields = [
            f for f in _SIMILARITY_FIELD_WEIGHTS
            if item.get(f) is not None
        ]
        score = sum(_SIMILARITY_FIELD_WEIGHTS[f] for f in matched_fields)
        return {
            "record_type": "composite_similarity_v1",
            "score": round(score, 3),
            "matched_fields": matched_fields,
            "authority": "analysis_only",
        }

    matched_fields = []
    for field, weight in _SIMILARITY_FIELD_WEIGHTS.items():
        if item.get(field) == reference.get(field):
            matched_fields.append(field)

    score = sum(_SIMILARITY_FIELD_WEIGHTS[f] for f in matched_fields)

    return {
        "record_type": "composite_similarity_v1",
        "score": round(score, 3),
        "matched_fields": matched_fields,
        "authority": "analysis_only",
    }


# ---------------------------------------------------------------------------
# 3. Confidence estimation
# ---------------------------------------------------------------------------

def estimate_confidence(item: dict) -> dict:
    """
    Estimate confidence based on metadata completeness and structural indicators.

    Returns:
        {
          "record_type": "composite_confidence_v1",
          "confidence": 0.0-1.0,
          "confidence_band": "low|medium|high",
          "reasons": [...],
          "authority": "analysis_only"
        }
    """
    reasons = []
    score = 0.0

    record_type = item.get("record_type")
    if record_type and record_type != "unknown":
        score += 0.20
        reasons.append("known_record_type")
    else:
        reasons.append("missing_or_unknown_record_type")

    # proposal_ready: true adds confidence
    if item.get("proposal_ready") is True:
        score += 0.25
        reasons.append("proposal_ready_true")

    # stable_across_checks >= 3 adds confidence
    stable = item.get("stable_across_checks", 0)
    if isinstance(stable, int) and stable >= 3:
        score += 0.20
        reasons.append(f"stable_across_checks_{stable}")
    elif isinstance(stable, int) and stable >= 1:
        score += 0.10
        reasons.append(f"stable_across_checks_{stable}")

    # Count non-null fields as a basic completeness metric
    non_null_fields = sum(1 for v in item.values() if v is not None)
    field_count_ratio = min(non_null_fields / 10.0, 1.0)  # normalize against 10 fields
    score += field_count_ratio * 0.15
    if field_count_ratio > 0.5:
        reasons.append("high_field_completeness")

    # Penalize validation errors
    if item.get("validation_errors"):
        score -= 0.15
        reasons.append("has_validation_errors")

    # Penalize malformed/unknown source
    if item.get("record_type") == "unknown" or not item.get("record_type"):
        score -= 0.10
        reasons.append("malformed_record")

    score = max(0.0, min(1.0, score))

    if score >= 0.75:
        band = "high"
    elif score >= 0.40:
        band = "medium"
    else:
        band = "low"

    return {
        "record_type": "composite_confidence_v1",
        "confidence": round(score, 3),
        "confidence_band": band,
        "reasons": reasons,
        "authority": "analysis_only",
    }


# ---------------------------------------------------------------------------
# 4. Governance boundary
# ---------------------------------------------------------------------------

_ALLOWED_ACTIONS = ["analyze", "summarize", "rank", "classify_structure", "estimate_confidence"]
_FORBIDDEN_ACTIONS = [
    "approve",
    "modify_contract",
    "write_truth",
    "trigger_external_action",
    "change_governance",
    "write_memory",
    "auto_apply_proposal",
]
_OPERATOR_REQUIRED_FOR = [
    "approve_proposal",
    "reject_proposal",
    "modify_contract",
    "write_to_any_log",
    "change_response_contract",
    "trigger_deployment",
]


def governance_boundary(item: Optional[dict] = None) -> dict:
    """
    Return the governance boundary for composite analysis output.

    Returns:
        {
          "record_type": "composite_governance_boundary_v1",
          "allowed_actions": [...],
          "forbidden_actions": [...],
          "operator_required_for": [...],
          "authority": "analysis_only"
        }
    """
    return {
        "record_type": "composite_governance_boundary_v1",
        "allowed_actions": _ALLOWED_ACTIONS[:],
        "forbidden_actions": _FORBIDDEN_ACTIONS[:],
        "operator_required_for": _OPERATOR_REQUIRED_FOR[:],
        "authority": "analysis_only",
    }


# ---------------------------------------------------------------------------
# 5. Combined item analysis
# ---------------------------------------------------------------------------

# Local import to avoid circular issues — AAI may not be in sys.path at import time
_aa_index = None


def _get_aai():
    global _aa_index
    if _aa_index is None:
        try:
            from weslr.artificial_analysis_index import ArtificialAnalysisIndex
            _aa_index = ArtificialAnalysisIndex()
        except Exception:
            _aa_index = False  # signal that AAI unavailable
    return _aa_index if _aa_index else None


def analyze_item(item: dict) -> dict:
    """
    Combine structure classification, confidence estimation, governance boundary,
    and optionally AAI attention classification.

    Returns:
        {
          "record_type": "composite_analysis_v1",
          "structure": {...},
          "confidence": {...},
          "attention": {...},
          "governance": {...},
          "automatic_change": false,
          "authority": "analysis_only"
        }
    """
    structure = classify_structure(item)
    confidence = estimate_confidence(item)
    governance = governance_boundary(item)

    attention = {"available": False}
    aai = _get_aai()
    if aai is not None:
        try:
            aai_result = aai.classify_attention_item(item)
            if aai_result:
                attention = {
                    "available": True,
                    "level": aai_result.get("attention_level", "unknown"),
                    "recommended_action": aai_result.get("recommended_action", "track"),
                    "authority": "attention_only",
                }
        except Exception:
            pass

    return {
        "record_type": "composite_analysis_v1",
        "structure": structure,
        "confidence": confidence,
        "attention": attention,
        "governance": governance,
        "automatic_change": False,
        "authority": "analysis_only",
    }


# ---------------------------------------------------------------------------
# 6. Composite summary across Pass 1 sources
# ---------------------------------------------------------------------------

def _safe_read_jsonl(path: Path) -> list:
    """Read a JSONL file, skipping malformed lines. Returns list of dicts."""
    if not path.exists():
        return []
    records = []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    except Exception:
        pass
    return records


def _count_by_type(records: list) -> dict:
    counts = {}
    for r in records:
        rt = r.get("record_type", "unknown")
        counts[rt] = counts.get(rt, 0) + 1
    return counts


def build_composite_summary() -> dict:
    """
    Build a composite summary from all Pass 1 sources.

    Returns:
        {
          "record_type": "composite_summary_v1",
          "authority": "analysis_only",
          "automatic_change": false,
          "aai_summary": {...},
          "source_counts": {...},
          "high_confidence_items": [...],
          "operator_relevant_items": [...],
          "recommended_next_step": "..."
        }
    """
    # Read all sources
    public_signals = _safe_read_jsonl(_PUBLIC_SIGNALS_FILE)
    contract_observations = _safe_read_jsonl(_CONTRACT_OBSERVATIONS_FILE)
    insufficiency_log = _safe_read_jsonl(_CONTRACT_INSUFFICIENCY_FILE)
    proposal_reviews = _safe_read_jsonl(_CONTRACT_PROPOSAL_REVIEW_FILE)

    source_counts = {
        "public_signals": len(public_signals),
        "contract_observations": len(contract_observations),
        "contract_insufficiency_log": len(insufficiency_log),
        "contract_proposal_review_log": len(proposal_reviews),
    }

    # Analyze all records for confidence and operator relevance
    all_records = (
        public_signals
        + contract_observations
        + insufficiency_log
        + proposal_reviews
    )

    high_confidence_items = []
    operator_relevant_items = []

    for record in all_records:
        analysis = analyze_item(record)
        conf = analysis.get("confidence", {})
        attn = analysis.get("attention", {})

        if conf.get("confidence_band") == "high":
            high_confidence_items.append({
                "record_type": record.get("record_type", "unknown"),
                "confidence": conf.get("confidence"),
                "structural_class": analysis.get("structure", {}).get("structural_class"),
            })

        if attn.get("available") and attn.get("level", 0) >= 3:
            operator_relevant_items.append({
                "record_type": record.get("record_type", "unknown"),
                "attention_level": attn.get("level"),
                "recommended_action": attn.get("recommended_action"),
            })
        elif record.get("proposal_ready") is True:
            operator_relevant_items.append({
                "record_type": record.get("record_type", "unknown"),
                "proposal_ready": True,
                "reason": "proposal_ready_true",
            })

    # Build AAI summary if available
    aai_summary = {"available": False}
    aai = _get_aai()
    if aai is not None:
        try:
            summary = aai.summarize_attention()
            if summary:
                aai_summary = {
                    "available": True,
                    "summary": summary,
                }
        except Exception:
            pass

    # Recommend next step
    if operator_relevant_items:
        recommended = "Operator attention required — review pending items."
    elif high_confidence_items:
        recommended = "High-confidence items available for review."
    else:
        recommended = "System nominal. Continue monitoring."

    return {
        "record_type": "composite_summary_v1",
        "authority": "analysis_only",
        "automatic_change": False,
        "aai_summary": aai_summary,
        "source_counts": source_counts,
        "high_confidence_items": high_confidence_items[:10],  # cap at 10
        "operator_relevant_items": operator_relevant_items[:10],
        "recommended_next_step": recommended,
    }