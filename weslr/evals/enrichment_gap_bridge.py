from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from weslr.evals.random_ordinary_intelligence_prep_v1 import EvalSummary, run_eval
from weslr.internal_reasoning_graph.store import InternalReasoningGraphStore


FAILURE_MODE_ORDER = [
    "missed_weslr_route",
    "repeated_response",
    "weak_uncertainty_handling",
    "weak_explanation_structure",
    "generic_fallback",
    "low_score",
    "unknown",
]

CATEGORY_TO_MISSING_SKILL = {
    "ambiguity_uncertainty": "uncertainty_reasoning",
    "psychology": "human_context_reasoning",
    "practical_planning": "practical_planning",
    "creativity_conversation": "creative_conversation",
    "ordinary_reasoning": "ordinary_reasoning",
    "emergence": "systems_explanation",
    "language": "semantic_explanation",
    "science_explanation": "science_mechanism_explanation",
    "analogy_metaphor": "analogy_mapping",
    "philosophy_ethics": "ethics_tradeoff_reasoning",
    "weslr_related": "weslr_routing_and_governance_reasoning",
}

MISSING_SKILL_TO_TARGET_SUBSTRATE = {
    "uncertainty_reasoning": "evidence_substrate_and_eval_scorecard",
    "human_context_reasoning": "meaning_obligation_and_entity_memory",
    "practical_planning": "capability_taxonomy_and_meaning_obligation",
    "creative_conversation": "capability_taxonomy_and_meaning_obligation",
    "ordinary_reasoning": "capability_taxonomy_and_meaning_obligation",
    "systems_explanation": "capability_taxonomy_and_meaning_obligation",
    "semantic_explanation": "capability_taxonomy_and_meaning_obligation",
    "science_mechanism_explanation": "capability_taxonomy_and_meaning_obligation",
    "analogy_mapping": "capability_taxonomy_and_meaning_obligation",
    "ethics_tradeoff_reasoning": "capability_taxonomy_and_meaning_obligation",
    "weslr_routing_and_governance_reasoning": "internal_reasoning_graph_and_eval_scorecard",
}


def _result_dict(result: Any) -> dict[str, Any]:
    if hasattr(result, "to_dict"):
        return dict(result.to_dict())
    return dict(result)


def _summary_results(summary: EvalSummary | dict[str, Any]) -> list[dict[str, Any]]:
    if isinstance(summary, EvalSummary):
        return [_result_dict(item) for item in summary.results]
    results = summary.get("results", [])
    return [_result_dict(item) for item in results]


def classify_failure_mode(result: dict[str, Any]) -> str:
    notes = {str(note).strip().lower() for note in result.get("notes", [])}
    path = str(result.get("path") or "").strip().lower()
    category = str(result.get("category") or "").strip().lower()
    text = str(result.get("response_text") or "").strip().lower()
    score = float(result.get("score", 0.0) or 0.0)

    if "missed_weslr_route" in notes or (category == "weslr_related" and path and path not in {"fallback_safe", ""} and "weslr" not in path and "governance" not in path and "conversation" not in path and "materials" not in path):
        return "missed_weslr_route"
    if "repeated" in notes or result.get("repeated_response"):
        return "repeated_response"
    if "weak_uncertainty_handling" in notes:
        return "weak_uncertainty_handling"
    if "weak_explanation_structure" in notes:
        return "weak_explanation_structure"
    if "generic_fallback" in notes or result.get("generic_fallback_phrase") or result.get("fallback_safe") or path == "fallback_safe":
        return "generic_fallback"
    if score < 0.65 or "low_score" in notes:
        return "low_score"
    if "fallback" in notes or "i don't have a confirmed answer" in text:
        return "generic_fallback"
    return "unknown"


def map_category_to_missing_skill(category: str) -> str:
    return CATEGORY_TO_MISSING_SKILL.get(category, "general_reasoning_refinement")


def map_missing_skill_to_target_substrate(missing_skill: str) -> str:
    if missing_skill in MISSING_SKILL_TO_TARGET_SUBSTRATE:
        return MISSING_SKILL_TO_TARGET_SUBSTRATE[missing_skill]
    if "uncertainty" in missing_skill or "calibration" in missing_skill or "evidence" in missing_skill:
        return "evidence_substrate_and_eval_scorecard"
    if "human_context" in missing_skill or "entity_memory" in missing_skill:
        return "meaning_obligation_and_entity_memory"
    if "weslr" in missing_skill or "routing" in missing_skill or "benchmark" in missing_skill or "eval" in missing_skill:
        return "internal_reasoning_graph_and_eval_scorecard"
    return "capability_taxonomy_and_meaning_obligation"


def build_gap_record_kwargs(result: dict[str, Any], source_eval: str = "random_ordinary_intelligence_prep_v1") -> dict[str, Any]:
    prompt = str(result.get("prompt") or "")
    category = str(result.get("category") or "unknown")
    score = float(result.get("score", 0.0) or 0.0)
    failure_mode = classify_failure_mode(result)
    missing_skill = map_category_to_missing_skill(category)
    target_substrate = map_missing_skill_to_target_substrate(missing_skill)
    prompt_fingerprint = hashlib.sha256(prompt.encode("utf-8")).hexdigest() if prompt else None
    path = str(result.get("path") or "unknown")
    notes = [str(note) for note in result.get("notes", [])]
    notes_text = ", ".join(notes) if notes else "no explicit notes"

    name = f"{category} gap via {failure_mode}"
    description = (
        f"Weak eval result in {category} via path '{path}' with failure mode '{failure_mode}'. "
        f"Score={score:.3f}; notes={notes_text}."
    )
    proposed_enrichment = (
        f"Represent {missing_skill} refinement inside {target_substrate} without auto-implementation; "
        f"preserve operator review and test-first validation."
    )
    legibility_summary = (
        f"The {source_eval} measurement surfaced a {failure_mode} weakness in {category}. "
        f"This should be tracked as an enrichment gap for {missing_skill} in {target_substrate}, "
        f"with operator review required and no automatic execution."
    )

    evidence_refs = [
        f"eval:{source_eval}",
        f"category:{category}",
        f"path:{path}",
        f"prompt_fingerprint:{prompt_fingerprint}" if prompt_fingerprint else "prompt_fingerprint:none",
    ]

    return {
        "name": name,
        "description": description,
        "source_eval": source_eval,
        "prompt_fingerprint": prompt_fingerprint,
        "category": category,
        "current_path": "random ordinary eval -> weak prompt/category/failure mode -> enrichment gap record -> internal_reasoning_graph",
        "failure_mode": failure_mode,
        "missing_skill": missing_skill,
        "target_substrate": target_substrate,
        "proposed_enrichment": proposed_enrichment,
        "legibility_summary": legibility_summary,
        "evidence_refs": evidence_refs,
        "before_score": score,
    }


def create_gap_records_from_eval_summary(
    summary: EvalSummary | dict[str, Any],
    store: InternalReasoningGraphStore,
    threshold: float = 0.65,
    max_records: int = 10,
    link: bool = False,
) -> list[Any]:
    created: list[Any] = []
    for result in _summary_results(summary):
        score = float(result.get("score", 0.0) or 0.0)
        weak = score < threshold or bool(result.get("fallback_safe")) or bool(result.get("generic_fallback_phrase"))
        if not weak:
            continue
        kwargs = build_gap_record_kwargs(result)
        gap = store.create_enrichment_gap_record(**kwargs)
        if link:
            store.link_enrichment_gap_to_graph(gap.id)
        created.append(gap)
        if len(created) >= max_records:
            break
    return created


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Bridge random eval weaknesses into enrichment gap records")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--count", type=int, default=50)
    parser.add_argument("--threshold", type=float, default=0.65)
    parser.add_argument("--max-records", type=int, default=10)
    parser.add_argument("--graph-dir", type=str, default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--link", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    summary = run_eval(seed=args.seed, count=args.count)
    results = _summary_results(summary)
    candidate_count = sum(
        1
        for result in results
        if float(result.get("score", 0.0) or 0.0) < args.threshold
        or bool(result.get("fallback_safe"))
        or bool(result.get("generic_fallback_phrase"))
    )
    limited_count = min(candidate_count, max(0, args.max_records))

    if args.dry_run or not args.graph_dir:
        payload = {
            "mode": "dry_run",
            "graph_dir": args.graph_dir,
            "candidate_count": candidate_count,
            "would_create": limited_count,
            "threshold": args.threshold,
            "max_records": args.max_records,
            "link": bool(args.link),
        }
        if args.json:
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            print(
                f"Random eval enrichment gap bridge dry-run: candidates={candidate_count}, "
                f"would_create={limited_count}, threshold={args.threshold:.3f}, link={bool(args.link)}"
            )
        return 0

    store = InternalReasoningGraphStore(graph_dir=Path(args.graph_dir))
    created = create_gap_records_from_eval_summary(
        summary=summary,
        store=store,
        threshold=args.threshold,
        max_records=args.max_records,
        link=args.link,
    )
    payload = {
        "mode": "write",
        "graph_dir": args.graph_dir,
        "created": len(created),
        "threshold": args.threshold,
        "max_records": args.max_records,
        "link": bool(args.link),
        "gap_ids": [gap.id for gap in created],
    }
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(
            f"Random eval enrichment gap bridge wrote {len(created)} records to {args.graph_dir} "
            f"(threshold={args.threshold:.3f}, link={bool(args.link)})"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
