from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from weslr.internal_reasoning_graph.store import InternalReasoningGraphStore


SOURCE_EVAL = "official_mcq_adapter_v0"
LOW_CONFIDENCE_THRESHOLD = 0.5
HIGH_UNCERTAINTY_VALUES = {"high", "unknown"}

REQUIRED_SKILL_TO_MISSING_SKILL = {
    "science_explanation": "science_mechanism_explanation",
    "language_explanation": "semantic_explanation",
    "semantic_explanation": "semantic_explanation",
    "ordinary_reasoning": "ordinary_reasoning",
    "ethics_reasoning": "ethics_tradeoff_reasoning",
    "ethics_tradeoff_reasoning": "ethics_tradeoff_reasoning",
    "materials_boundary_reasoning": "materials_evidence_boundary_reasoning",
    "governance_reasoning": "weslr_routing_and_governance_reasoning",
    "weslr_routing_and_governance_reasoning": "weslr_routing_and_governance_reasoning",
}

TARGET_SUBSTRATE_MAP = {
    "science_mechanism_explanation": "concept_graph_and_evidence_substrate",
    "materials_evidence_boundary_reasoning": "concept_graph_and_evidence_substrate",
    "semantic_explanation": "meaning_obligation_and_capability_taxonomy",
    "ordinary_reasoning": "internal_reasoning_graph_and_eval_scorecard",
    "ethics_tradeoff_reasoning": "internal_reasoning_graph_and_governance_surface",
    "weslr_routing_and_governance_reasoning": "internal_reasoning_graph_and_governance_surface",
}


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def _read_json(path: str | Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    _require(isinstance(data, dict), "MCQ result payload must be a JSON object.")
    return data


def load_mcq_result(path: str | Path) -> dict[str, Any]:
    payload = _read_json(path)
    _require(bool(str(payload.get("suite_id") or "").strip()), "MCQ result must include suite_id.")
    _require(payload.get("official_score") is False, "official_score=true is not allowed for MCQ gap bridging.")

    sample_only = bool(payload.get("sample_only", False))
    internal_eval = bool(payload.get("internal_eval", False))
    _require(sample_only or internal_eval, "MCQ result must be sample_only=true or internal_eval=true.")

    results = payload.get("results")
    _require(isinstance(results, list), "MCQ result must include results as a list.")
    return payload


def is_weak_mcq_result(item: dict[str, Any]) -> bool:
    if item.get("correct") is False:
        return True
    if item.get("selected_label") is None:
        return True
    if bool(item.get("failure_mode")):
        return True

    confidence = item.get("confidence")
    if isinstance(confidence, (int, float)) and float(confidence) < LOW_CONFIDENCE_THRESHOLD:
        return True

    uncertainty = str(item.get("uncertainty") or "").strip().lower()
    if uncertainty in HIGH_UNCERTAINTY_VALUES:
        return True

    return False


def map_required_skill_to_missing_skill(required_skill: str) -> str:
    normalized = str(required_skill or "").strip().lower()
    return REQUIRED_SKILL_TO_MISSING_SKILL.get(normalized, "unknown_benchmark_skill_gap")


def map_missing_skill_to_target_substrate(missing_skill: str) -> str:
    normalized = str(missing_skill or "").strip().lower()
    if normalized in TARGET_SUBSTRATE_MAP:
        return TARGET_SUBSTRATE_MAP[normalized]
    if "science" in normalized or "material" in normalized:
        return "concept_graph_and_evidence_substrate"
    if "semantic" in normalized or "language" in normalized:
        return "meaning_obligation_and_capability_taxonomy"
    if "ordinary_reasoning" in normalized:
        return "internal_reasoning_graph_and_eval_scorecard"
    if "ethic" in normalized or "governance" in normalized or "weslr" in normalized:
        return "internal_reasoning_graph_and_governance_surface"
    return "internal_reasoning_graph_and_eval_scorecard"


def _question_fingerprint(question: str) -> str | None:
    text = str(question or "").strip()
    if not text:
        return None
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _score_before(result: dict[str, Any]) -> float:
    if result.get("correct") is False or result.get("selected_label") is None:
        return 0.0
    confidence = result.get("confidence")
    if isinstance(confidence, (int, float)):
        value = float(confidence)
        return max(0.0, min(1.0, value))
    return 0.0


def _general_enrichment_text(missing_skill: str, domain: str) -> str:
    if missing_skill == "semantic_explanation":
        return "Improve semantic explanation answer selection under MCQ format without item-specific heuristics or answer memorization."
    if missing_skill == "science_mechanism_explanation":
        return "Improve science mechanism explanation and answer selection under MCQ format using general evidence-grounded reasoning, not item-specific shortcuts."
    if missing_skill == "ordinary_reasoning":
        return "Improve ordinary reasoning answer selection under MCQ format through general reasoning refinement, not benchmark-item tuning."
    if missing_skill == "ethics_tradeoff_reasoning":
        return "Improve ethics and tradeoff reasoning under MCQ format while preserving governance review and avoiding benchmark-specific phrase rules."
    if missing_skill == "materials_evidence_boundary_reasoning":
        return "Improve materials and evidence-boundary reasoning under MCQ format without encoding answer keys or item-specific rules."
    if missing_skill == "weslr_routing_and_governance_reasoning":
        return "Improve governance and WESLR routing reasoning under MCQ format through general substrate enrichment, not benchmark gaming."
    return (
        f"Improve general benchmark-relevant skill coverage for domain '{domain}' under MCQ format "
        "without answer-key memorization, item-specific phrase rules, or benchmark gaming."
    )


def build_gap_kwargs_from_mcq_result(result: dict[str, Any], suite_metadata: dict[str, Any], include_sensitive: bool = False) -> dict[str, Any]:
    item_id = str(result.get("id") or "unknown_item")
    domain = str(result.get("domain") or "unknown")
    required_skill = str(result.get("required_skill") or "unknown")
    missing_skill = map_required_skill_to_missing_skill(required_skill)
    target_substrate = map_missing_skill_to_target_substrate(missing_skill)
    failure_mode = str(result.get("failure_mode") or "incorrect_answer")
    fingerprint = _question_fingerprint(str(result.get("question") or ""))
    proposed_enrichment = _general_enrichment_text(missing_skill, domain)

    selected_label = result.get("selected_label")
    confidence = result.get("confidence")
    uncertainty = str(result.get("uncertainty") or "unknown")
    description = (
        f"Weak MCQ eval result for domain '{domain}' on item '{item_id}' with failure mode '{failure_mode}'. "
        f"Selected_label_present={selected_label is not None}; correct={bool(result.get('correct'))}; "
        f"confidence={confidence}; uncertainty={uncertainty}. "
        "Track as a general skill gap only; do not store answer keys or derive item-specific heuristics."
    )
    legibility_summary = (
        f"{SOURCE_EVAL} surfaced a weak {domain} MCQ result for required skill '{required_skill}'. "
        f"Represent it as a general enrichment gap for '{missing_skill}' in '{target_substrate}', "
        "with operator review required, no automatic execution, and no benchmark-item memorization."
    )

    evidence_refs = [
        f"suite_id:{suite_metadata.get('suite_id') or suite_metadata.get('id') or 'unknown_suite'}",
        f"dataset_name:{suite_metadata.get('dataset_name') or 'unknown'}",
        f"dataset_version:{suite_metadata.get('dataset_version') or 'unknown'}",
        f"subset_name:{suite_metadata.get('subset_name') or 'unknown'}",
        f"item_id:{item_id}",
        f"required_skill:{required_skill}",
    ]
    if fingerprint:
        evidence_refs.append(f"question_fingerprint:{fingerprint}")

    kwargs = {
        "name": f"{domain} MCQ gap via {failure_mode}",
        "description": description,
        "source_eval": SOURCE_EVAL,
        "prompt_fingerprint": fingerprint,
        "category": domain,
        "current_path": "official_mcq_result -> weak_item -> enrichment_gap_record -> internal_reasoning_graph",
        "failure_mode": failure_mode,
        "missing_skill": missing_skill,
        "target_substrate": target_substrate,
        "proposed_enrichment": proposed_enrichment,
        "legibility_summary": legibility_summary,
        "evidence_refs": evidence_refs,
        "before_score": _score_before(result),
    }
    if include_sensitive:
        question = str(result.get("question") or "").strip()
        if question:
            kwargs["source_prompt"] = question
    return kwargs


def create_gap_records_from_mcq_result_file(
    path: str | Path,
    store: InternalReasoningGraphStore,
    max_records: int = 10,
    link: bool = False,
    include_sensitive: bool = False,
) -> list[Any]:
    payload = load_mcq_result(path)
    suite_metadata = dict(payload.get("metadata") or {})
    suite_metadata.setdefault("suite_id", payload.get("suite_id"))

    created: list[Any] = []
    for result in payload.get("results", []):
        if not isinstance(result, dict) or not is_weak_mcq_result(result):
            continue
        gap = store.create_enrichment_gap_record(**build_gap_kwargs_from_mcq_result(result, suite_metadata, include_sensitive=include_sensitive))
        if link:
            store.link_enrichment_gap_to_graph(gap.id)
        created.append(gap)
        if len(created) >= max(0, int(max_records)):
            break
    return created


def _candidate_summary(result: dict[str, Any], suite_metadata: dict[str, Any]) -> dict[str, Any]:
    kwargs = build_gap_kwargs_from_mcq_result(result, suite_metadata, include_sensitive=False)
    return {
        "item_id": result.get("id"),
        "domain": result.get("domain"),
        "required_skill": result.get("required_skill"),
        "failure_mode": kwargs["failure_mode"],
        "missing_skill": kwargs["missing_skill"],
        "target_substrate": kwargs["target_substrate"],
        "before_score": kwargs["before_score"],
        "question_fingerprint": kwargs.get("prompt_fingerprint"),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Bridge official-style MCQ eval weaknesses into enrichment gap records")
    parser.add_argument("--result", required=True, help="Path to saved MCQ adapter result JSON.")
    parser.add_argument("--graph-dir", type=str, default=None, help="Optional graph dir for persistent writes.")
    parser.add_argument("--max-records", type=int, default=10)
    parser.add_argument("--link", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--include-sensitive", action="store_true")
    args = parser.parse_args(argv)

    payload = load_mcq_result(args.result)
    suite_metadata = dict(payload.get("metadata") or {})
    suite_metadata.setdefault("suite_id", payload.get("suite_id"))
    weak_results = [item for item in payload.get("results", []) if isinstance(item, dict) and is_weak_mcq_result(item)]
    limited = weak_results[: max(0, int(args.max_records))]

    if args.dry_run or not args.graph_dir:
        dry_payload = {
            "mode": "dry_run",
            "graph_dir": args.graph_dir,
            "candidate_count": len(weak_results),
            "would_create": len(limited),
            "max_records": args.max_records,
            "link": bool(args.link),
            "candidate_summaries": [_candidate_summary(item, suite_metadata) for item in limited],
        }
        if args.json:
            print(json.dumps(dry_payload, indent=2, ensure_ascii=False))
        else:
            print(
                f"Official MCQ gap bridge dry-run: candidates={len(weak_results)}, "
                f"would_create={len(limited)}, link={bool(args.link)}"
            )
        return 0

    store = InternalReasoningGraphStore(graph_dir=Path(args.graph_dir))
    created = create_gap_records_from_mcq_result_file(
        path=args.result,
        store=store,
        max_records=args.max_records,
        link=args.link,
        include_sensitive=bool(args.include_sensitive),
    )
    write_payload = {
        "mode": "write",
        "graph_dir": args.graph_dir,
        "created": len(created),
        "max_records": args.max_records,
        "link": bool(args.link),
        "include_sensitive": bool(args.include_sensitive),
        "gap_ids": [gap.id for gap in created],
    }
    if args.json:
        print(json.dumps(write_payload, indent=2, ensure_ascii=False))
    else:
        print(
            f"Official MCQ gap bridge wrote {len(created)} records to {args.graph_dir} "
            f"(link={bool(args.link)}, include_sensitive={bool(args.include_sensitive)})"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
