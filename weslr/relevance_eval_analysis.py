"""
weslr/relevance_eval_analysis.py
================================
Pattern detection over relevance evaluation artifacts.
INSPECTION ONLY — no system changes, no writes.

Phase 1A: Single-turn scenarios (sat-001 to sat-005)
Phase 1C: Multi-turn context scenarios (sat-020 to sat-023)
Phase 1D: Edge / failure pressure scenarios (sat-024 to sat-027)
"""

import json
import os
from pathlib import Path
from typing import Any

# ---------------------------------------------------------------------------
# Path constants
# ---------------------------------------------------------------------------
EVAL_DIR = Path(__file__).parent.parent / "continuity" / "artifacts" / "eval"


# ---------------------------------------------------------------------------
# 1. load_all_eval_artifacts
# ---------------------------------------------------------------------------
def load_all_eval_artifacts() -> list[dict]:
    """Load all evaluation artifacts from the eval directory."""
    index_path = EVAL_DIR / "index.json"
    if not index_path.exists():
        return []

    with open(index_path, "r", encoding="utf-8") as f:
        index: list[str] = json.load(f)

    artifacts = []
    for entry in index:
        artifact_path = EVAL_DIR / f"{entry}.json"
        if artifact_path.exists():
            with open(artifact_path, "r", encoding="utf-8") as f:
                artifacts.append(json.load(f))
    return artifacts


# ---------------------------------------------------------------------------
# 2. analyze_patterns
# ---------------------------------------------------------------------------
def analyze_patterns(artifacts: list[dict]) -> dict:
    """
    Detect patterns across evaluation artifacts.

    Handles both single-turn (Phase 1A) and chain scenarios (Phase 1C/1D).

    Returns
    -------
    dict with keys:
        total_artifacts, message_relevance_empty_rate,
        artifact_context_present_rate, reference_turn_count,
        reference_turn_empty_message_rate, non_reference_match_rate,
        average_interest_count, top_matched_interests,
        scenarios_with_consistent_matches, scenarios_with_empty_expected,
        scenarios_with_possible_issues, observed_patterns,
        chain_scenario_results (Phase 1C/1D specific)
    """
    total = len(artifacts)
    if total == 0:
        return {"total_artifacts": 0, "observed_patterns": ["No artifacts found."]}

    # --- basic counts (Phase 1A) -------------------------------------------
    empty_message_count = 0
    artifact_context_count = 0
    reference_turn_count = 0
    reference_empty_message_count = 0
    non_reference_count = 0
    non_reference_with_match = 0
    total_interest_count = 0

    # --- per-interest tracking ----------------------------------------------
    interest_name_counts: dict[str, int] = {}

    # --- categorized scenarios ----------------------------------------------
    consistent_matches: list[dict] = []
    empty_expected: list[dict] = []
    possible_issues: list[dict] = []

    # --- general observed patterns ------------------------------------------
    observed_patterns: list[str] = []

    # --- Phase 1C/1D chain analysis ----------------------------------------
    chain_scenario_results: list[dict] = []
    revision_drift_count = 0
    artifact_context_leak_count = 0
    cross_domain_contamination_count = 0
    incorrect_continuity_count = 0
    safe_path_ok_count = 0
    safe_path_total = 0

    # --- Context + boundary signal tracking --------------------------------
    context_selection_counts: dict[str, int] = {}
    boundary_hint_counts: dict[str, int] = {}
    context_selection_by_stage: dict[str, dict[str, int]] = {}
    boundary_transitions: list[dict] = []
    context_unstable_count = 0
    context_stable_count = 0
    boundary_inconsistent_count = 0
    boundary_consistent_count = 0

    for art in artifacts:
        scenario_id = art.get("scenario_id", "unknown")

        # --- Handle chain scenarios (Phase 1C/1D) -------------------------
        if "chain_results" in art:
            chain_result = _analyze_chain_scenario(art)
            chain_scenario_results.append(chain_result)

            # Aggregate chain-level auto-flags
            auto_flags = art.get("auto_flags", {})
            if auto_flags.get("revision_drift"):
                revision_drift_count += 1
                observed_patterns.append(
                    f"[REVISION_DRIFT] scenario={scenario_id}: "
                    f"active artifact changed multiple times in revision chain"
                )
            if auto_flags.get("artifact_context_leak_flag"):
                artifact_context_leak_count += 1
                observed_patterns.append(
                    f"[ARTIFACT_CONTEXT_LEAK] scenario={scenario_id}: "
                    f"artifact context leaked into unrelated turn"
                )
            if auto_flags.get("cross_domain_contamination_flag"):
                cross_domain_contamination_count += 1
                observed_patterns.append(
                    f"[CROSS_DOMAIN_CONTAMINATION] scenario={scenario_id}: "
                    f"wrong-domain artifact relevance dominated unrelated turn"
                )
            if auto_flags.get("incorrect_continuity"):
                incorrect_continuity_count += 1
                observed_patterns.append(
                    f"[INCORRECT_CONTINUITY] scenario={scenario_id}: "
                    f"active artifact resolution returned wrong artifact"
                )
            if auto_flags.get("safe_path_ok"):
                safe_path_ok_count += 1
            if "expected_safe_response" in str(art.get("chain_results", [])):
                safe_path_total += 1

            # Collect interests from chain turns
            for turn_result in art.get("chain_results", []):
                for interest in turn_result.get("relevant_interests_snapshot", []):
                    name = interest.get("name", "unknown")
                    interest_name_counts[name] = interest_name_counts.get(name, 0) + 1
                    total_interest_count += 1

                # Capture context selection + boundary hints from turn
                ctx_sel = turn_result.get("context_selection_v1", "uncertain")
                bhints = turn_result.get("boundary_hints", ["unknown"])

                # Context selection counts
                context_selection_counts[ctx_sel] = context_selection_counts.get(ctx_sel, 0) + 1

                # Boundary hint counts (flatten)
                for h in bhints:
                    boundary_hint_counts[h] = boundary_hint_counts.get(h, 0) + 1

                # Per-stage context tracking
                stage = turn_result.get("artifact_lifecycle_stage", "unknown")
                if stage not in context_selection_by_stage:
                    context_selection_by_stage[stage] = {}
                context_selection_by_stage[stage][ctx_sel] = \
                    context_selection_by_stage[stage].get(ctx_sel, 0) + 1

                # Boundary transition stability (within chain)
                chain_turns = art.get("chain_results", [])
                for i in range(1, len(chain_turns)):
                    prev_hints = set(chain_turns[i-1].get("boundary_hints", ["unknown"]))
                    curr_hints = set(chain_turns[i].get("boundary_hints", ["unknown"]))
                    if prev_hints != curr_hints:
                        boundary_inconsistent_count += 1
                        boundary_transitions.append({
                            "scenario_id": scenario_id,
                            "from": sorted(prev_hints),
                            "to": sorted(curr_hints),
                        })
                    else:
                        boundary_consistent_count += 1

            # Detect context stability within chain
            chain_ctx_values = [t.get("context_selection_v1", "uncertain")
                                for t in chain_turns]
            if len(set(chain_ctx_values)) > 1:
                context_unstable_count += 1
            else:
                context_stable_count += 1

            # Detect stable vs unstable lifecycle relevance
            stable, unstable = _detect_stability(art.get("chain_results", []))
            if unstable:
                observed_patterns.append(
                    f"[UNSTABLE_LIFECYCLE] scenario={scenario_id}: "
                    f"relevance unstable across {len(unstable)} turns: {unstable}"
                )

            continue  # Skip single-turn analysis for chain artifacts

        # --- Single-turn scenarios (Phase 1A) -----------------------------
        stage = art.get("artifact_lifecycle_stage", "unknown")
        msg_relevance = art.get("relevant_interests_snapshot", [])
        artifact_relevance = art.get("resolved_artifact_interests", [])
        auto_flags = art.get("auto_flags", {})
        expected = art.get("expected_interests", [])
        scenario_title = art.get("scenario_title", "")
        scenario = {"id": scenario_id, "title": scenario_title}

        # message-level relevance empty?
        msg_empty = len(msg_relevance) == 0

        # artifact context present?
        artifact_context_present = len(artifact_relevance) > 0

        # reference turn?
        is_reference = stage == "reference"

        # collect interest names across both fields
        for entry in msg_relevance + artifact_relevance:
            name = entry.get("name", "unknown")
            interest_name_counts[name] = interest_name_counts.get(name, 0) + 1

        # update counters
        if msg_empty:
            empty_message_count += 1
        if artifact_context_present:
            artifact_context_count += 1
        if is_reference:
            reference_turn_count += 1
            if msg_empty:
                reference_empty_message_count += 1
        else:
            non_reference_count += 1
            if not msg_empty:
                non_reference_with_match += 1

        total_interest_count += len(msg_relevance)

        # expected interests from eval metadata
        expected_set = set(expected)

        # actual message-level interests
        actual_set = {e["name"] for e in msg_relevance}

        # artifact-level interests
        artifact_interest_set = {e["name"] for e in artifact_relevance}

        # --- Context + boundary signal tracking (single-turn) -------------
        # Single-turn artifacts may have context_selection_v1 + boundary_hints
        # from sat-* eval runs that captured them via handle_direct_message.
        ctx_sel_single = art.get("context_selection_v1", "uncertain")
        bhints_single = art.get("boundary_hints", ["unknown"])

        if ctx_sel_single != "uncertain":
            # Only track if explicitly set (not default)
            context_selection_counts[ctx_sel_single] = \
                context_selection_counts.get(ctx_sel_single, 0) + 1

        for h in bhints_single:
            boundary_hint_counts[h] = boundary_hint_counts.get(h, 0) + 1

        # --- categorization -------------------------------------------------
        if stage == "reference":
            if msg_empty:
                empty_expected.append(scenario)
            else:
                possible_issues.append({
                    "id": scenario_id,
                    "title": scenario_title,
                    "issue": "reference_turn_has_message_relevance",
                    "detail": f"Expected empty _relevant_interests but got: {list(actual_set)}"
                })
        elif stage in ("explanation", "revision"):
            if msg_empty:
                empty_expected.append(scenario)
            else:
                consistent_matches.append(scenario)
        elif stage == "generation":
            if not msg_empty:
                consistent_matches.append(scenario)
            else:
                possible_issues.append({
                    "id": scenario_id,
                    "title": scenario_title,
                    "issue": "generation_turn_empty_message_relevance",
                    "detail": f"Generation turn with empty _relevant_interests for: {art.get('input_message', '')}"
                })

        # --- additional pattern detection ------------------------------------
        if msg_empty and artifact_context_present:
            observed_patterns.append(
                f"[MISMATCH] scenario={scenario_id}: message relevance EMPTY "
                f"but artifact context has {artifact_interest_set}"
            )

        if len(msg_relevance) > 3:
            observed_patterns.append(
                f"[OVERMATCH] scenario={scenario_id}: "
                f"{len(msg_relevance)} interests in message relevance: "
                f"{list(actual_set)}"
            )

        if not msg_empty:
            scores = [e.get("score", 0) for e in msg_relevance]
            if len(scores) > 1 and scores != sorted(scores, reverse=True):
                observed_patterns.append(
                    f"[RANK_INCONSISTENT] scenario={scenario_id}: "
                    f"scores not descending: {scores}"
                )

        if auto_flags.get("empty_relevance") and not msg_empty:
            observed_patterns.append(
                f"[AUTO_FLAG_CONFLICT] scenario={scenario_id}: "
                f"empty_relevance flag True but _relevant_interests has entries"
            )

        if auto_flags.get("high_noise"):
            observed_patterns.append(
                f"[NOISE_FLAG] scenario={scenario_id}: high_noise flag set"
            )

    # --- computed rates ----------------------------------------------------
    msg_empty_rate = empty_message_count / total
    artifact_context_rate = artifact_context_count / total
    ref_empty_rate = (
        reference_empty_message_count / reference_turn_count
        if reference_turn_count > 0 else 0.0
    )
    non_ref_match_rate = (
        non_reference_with_match / non_reference_count
        if non_reference_count > 0 else 0.0
    )
    avg_interest_count = total_interest_count / total if total > 0 else 0.0

    # --- top matched interests ----------------------------------------------
    top_matched = sorted(
        interest_name_counts.items(),
        key=lambda x: x[1],
        reverse=True
    )
    top_matched_interests = [
        {"name": name, "count": count}
        for name, count in top_matched[:10]
    ]

    # --- contamination advisory analysis -----------------------------------
    contamination_summary = _analyze_contamination_advisories(artifacts)

    result = {
        "total_artifacts": total,
        "message_relevance_empty_rate": round(msg_empty_rate, 3),
        "artifact_context_present_rate": round(artifact_context_rate, 3),
        "reference_turn_count": reference_turn_count,
        "reference_turn_empty_message_rate": round(ref_empty_rate, 3),
        "non_reference_match_rate": round(non_ref_match_rate, 3),
        "average_interest_count": round(avg_interest_count, 2),
        "top_matched_interests": top_matched_interests,
        "scenarios_with_consistent_matches": consistent_matches,
        "scenarios_with_empty_expected": empty_expected,
        "scenarios_with_possible_issues": possible_issues,
        "observed_patterns": observed_patterns,
        # Phase 1C/1D specific
        "chain_scenario_results": chain_scenario_results,
        "revision_drift_count": revision_drift_count,
        "artifact_context_leak_count": artifact_context_leak_count,
        "cross_domain_contamination_count": cross_domain_contamination_count,
        "incorrect_continuity_count": incorrect_continuity_count,
        "safe_path_ok_count": safe_path_ok_count,
        "safe_path_total": safe_path_total,
        # Contamination advisory analysis
        **contamination_summary,
        # Context + boundary signal analysis
        "context_selection_counts": dict(context_selection_counts),
        "boundary_hint_counts": dict(boundary_hint_counts),
        "context_selection_by_stage": dict(context_selection_by_stage),
        "context_unstable_count": context_unstable_count,
        "context_stable_count": context_stable_count,
        "boundary_inconsistent_count": boundary_inconsistent_count,
        "boundary_consistent_count": boundary_consistent_count,
        "boundary_transitions": boundary_transitions[:20],  # cap at 20
    }

    return result


def _analyze_contamination_advisories(artifacts: list[dict]) -> dict:
    """Analyze contamination_advisory blocks across eval artifacts.

    Returns advisory-only metadata — no runtime changes.
    """
    total = len(artifacts)
    if total == 0:
        return {
            "contamination_advisories_total": 0,
            "contamination_rate": 0.0,
            "contamination_free_count": 0,
            "contaminated_count": 0,
            "contamination_by_type": {},
            "top_contamination_signals": [],
            "healthy_scenarios": [],
            "contaminated_scenarios": [],
            "contamination_observed_patterns": [],
        }

    # Only analyze CSC eval artifacts (have contamination_advisory block)
    csc_artifacts = [
        a for a in artifacts
        if "contamination_advisory" in a or a.get("scenario_id", "").startswith("csc-")
    ]

    contamination_free = 0
    contaminated = 0
    by_type: dict[str, int] = {
        "cross_domain_contamination": 0,
        "stale_context_dominance": 0,
        "wrong_active_artifact_persistence": 0,
        "unrelated_topic_bleed": 0,
        "none": 0,
    }
    signal_counts: dict[str, int] = {}
    healthy: list[dict] = []
    contaminated_scenarios_list: list[dict] = []
    patterns: list[str] = []

    for art in csc_artifacts:
        scenario_id = art.get("scenario_id", "unknown")
        advisory = art.get("contamination_advisory")

        # Skip artifacts without contamination_advisory
        if advisory is None:
            continue

        is_contaminated = advisory.get("contaminated", False)
        cont_type = advisory.get("type", "none")
        signals = advisory.get("source_signals", [])

        if is_contaminated:
            contaminated += 1
            by_type[cont_type] = by_type.get(cont_type, 0) + 1
            contaminated_scenarios_list.append({
                "id": scenario_id,
                "type": cont_type,
                "confidence": advisory.get("confidence", "unknown"),
                "reason": advisory.get("reason", ""),
            })
            for sig in signals:
                signal_counts[sig] = signal_counts.get(sig, 0) + 1
        else:
            contamination_free += 1
            by_type["none"] = by_type.get("none", 0) + 1
            healthy.append({"id": scenario_id, "type": cont_type})

    # Top source signals
    top_signals = sorted(signal_counts.items(), key=lambda x: x[1], reverse=True)
    top_signals_list = [
        {"signal": sig, "count": count}
        for sig, count in top_signals[:5]
    ]

    # Per-scenario contamination summary
    if csc_artifacts:
        scenario_contamination: dict[str, bool] = {}
        for art in csc_artifacts:
            sid = art.get("scenario_id", "unknown")
            advisory = art.get("contamination_advisory")
            if advisory and advisory.get("contaminated"):
                scenario_contamination[sid] = True
            elif advisory:
                scenario_contamination.setdefault(sid, False)

        persistently_healthy = [
            sid for sid, c in scenario_contamination.items() if not c
        ]
        persistently_contaminated = [
            sid for sid, c in scenario_contamination.items() if c
        ]

        if persistently_healthy:
            patterns.append(
                f"[HEALTHY] scenarios consistently contamination-free: "
                f"{persistently_healthy}"
            )
        if persistently_contaminated:
            patterns.append(
                f"[CONTAMINATED] scenarios with contamination detected: "
                f"{persistently_contaminated}"
            )

    rate = round(contaminated / len(csc_artifacts), 3) if csc_artifacts else 0.0

    return {
        "contamination_advisories_total": len(csc_artifacts),
        "contamination_rate": rate,
        "contamination_free_count": contamination_free,
        "contaminated_count": contaminated,
        "contamination_by_type": {k: v for k, v in by_type.items() if v > 0},
        "top_contamination_signals": top_signals_list,
        "healthy_scenarios": healthy,
        "contaminated_scenarios": contaminated_scenarios_list,
        "contamination_observed_patterns": patterns,
    }


def _analyze_chain_scenario(art: dict) -> dict:
    """Analyze a chain scenario artifact (Phase 1C/1D)."""
    scenario_id = art.get("scenario_id", "unknown")
    scenario_title = art.get("scenario_title", "")
    chain_results = art.get("chain_results", [])
    auto_flags = art.get("auto_flags", {})

    # Summarize per-turn behavior
    turn_summaries = []
    for turn in chain_results:
        turn_summaries.append({
            "turn": turn.get("turn"),
            "input_message": turn.get("input_message", ""),
            "artifact_lifecycle_stage": turn.get("artifact_lifecycle_stage", ""),
            "response_source": turn.get("response_source", ""),
            "active_artifact_before": turn.get("active_artifact_before"),
            "active_artifact_after": turn.get("active_artifact_after"),
            "relevant_interests_count": len(turn.get("relevant_interests_snapshot", [])),
            "safe_response": turn.get("safe_response", False),
            "message_domain_unrelated": turn.get("message_domain_unrelated", False),
        })

    return {
        "scenario_id": scenario_id,
        "scenario_title": scenario_title,
        "turn_count": len(chain_results),
        "artifacts_created": auto_flags.get("total_artifacts_created", 0),
        "revision_drift": auto_flags.get("revision_drift", False),
        "artifact_context_leak": auto_flags.get("artifact_context_leak_flag", False),
        "cross_domain_contamination": auto_flags.get("cross_domain_contamination_flag", False),
        "incorrect_continuity": auto_flags.get("incorrect_continuity", False),
        "safe_path_ok": auto_flags.get("safe_path_ok", False),
        "turn_summaries": turn_summaries,
    }


def _detect_stability(chain_results: list) -> tuple[list, list]:
    """Detect stable vs unstable lifecycle relevance across chain turns.

    Returns:
        (stable_turns, unstable_turns) — lists of turn indices
    """
    if len(chain_results) < 2:
        return list(range(len(chain_results))), []

    stable = []
    unstable = []

    for i, turn in enumerate(chain_results):
        interests = turn.get("relevant_interests_snapshot", [])
        stage = turn.get("artifact_lifecycle_stage", "")

        # A turn is unstable if interests change dramatically without clear reason
        if i == 0:
            stable.append(i)
            continue

        prev_interests = chain_results[i-1].get("relevant_interests_snapshot", [])
        prev_names = {it.get("name") for it in prev_interests}
        curr_names = {it.get("name") for it in interests}

        # Check for dramatic change
        if stage == "shift" and curr_names:
            # Topic shift should show relevance change — not unstable
            stable.append(i)
        elif stage in ("revision", "follow_up") and not curr_names:
            # Vague follow-up with no interests — not unstable
            stable.append(i)
        elif stage == "revision" and curr_names and prev_names == curr_names:
            # Same interests across revision — stable
            stable.append(i)
        elif stage == "revision" and curr_names and prev_names != curr_names:
            # Different interests in revision — potentially unstable
            # Only flag if interest count differs significantly
            if len(curr_names) != len(prev_names):
                unstable.append(i)
            else:
                stable.append(i)
        else:
            stable.append(i)

    return stable, unstable


# ---------------------------------------------------------------------------
# 3. print_analysis_report
# ---------------------------------------------------------------------------
def print_analysis_report(result: dict) -> None:
    """Readable CLI output from analyze_patterns result."""
    total = result["total_artifacts"]

    print("=" * 70)
    print("RELEVANCE EVALUATION — PATTERN ANALYSIS REPORT")
    print("=" * 70)

    print("\n## SUMMARY METRICS")
    print(f"  Total artifacts evaluated : {total}")
    print(f"  Avg interests per artifact: {result['average_interest_count']}")
    print(f"  Message relevance empty    : {result['message_relevance_empty_rate']:.1%}")
    print(f"  Artifact context present   : {result['artifact_context_present_rate']:.1%}")
    print(f"  Reference turns            : {result['reference_turn_count']}")
    print(f"  Reference turn empty msg  : {result['reference_turn_empty_message_rate']:.1%}")
    print(f"  Non-reference match rate   : {result['non_reference_match_rate']:.1%}")

    # Phase 1C/1D chain metrics
    chain_total = len(result.get("chain_scenario_results", []))
    if chain_total > 0:
        print("\n## PHASE 1C/1D CHAIN METRICS")
        print(f"  Chain scenarios evaluated : {chain_total}")
        print(f"  Revision drift count      : {result.get('revision_drift_count', 0)}")
        print(f"  Artifact context leaks   : {result.get('artifact_context_leak_count', 0)}")
        print(f"  Cross-domain contaminations: {result.get('cross_domain_contamination_count', 0)}")
        print(f"  Incorrect continuity      : {result.get('incorrect_continuity_count', 0)}")
        safe_ok = result.get("safe_path_ok_count", 0)
        safe_tot = result.get("safe_path_total", 0)
        if safe_tot > 0:
            print(f"  Safe path (no artifact)   : {safe_ok}/{safe_tot} OK")

    print("\n## TOP MATCHED INTERESTS")
    if result["top_matched_interests"]:
        for item in result["top_matched_interests"]:
            print(f"  {item['name']:<30} ×{item['count']}")
    else:
        print("  (none)")

    print("\n## CONSISTENT MATCHES (where relevance worked as expected)")
    for s in result["scenarios_with_consistent_matches"]:
        print(f"  [{s['id']}] {s['title']}")

    print("\n## EMPTY EXPECTED (generic queries, empty is correct)")
    for s in result["scenarios_with_empty_expected"]:
        print(f"  [{s['id']}] {s['title']}")

    print("\n## POSSIBLE ISSUES")
    issues = result["scenarios_with_possible_issues"]
    if not issues:
        print("  (none)")
    else:
        for item in issues:
            print(f"  [{item['id']}] {item['title']}")
            print(f"    → {item['issue']}: {item['detail']}")

    # Phase 1C/1D chain scenario details
    chain_results = result.get("chain_scenario_results", [])
    if chain_results:
        print("\n## CHAIN SCENARIO DETAILS")
        for cr in chain_results:
            print(f"  [{cr['scenario_id']}] {cr['scenario_title']}")
            print(f"    Turns: {cr['turn_count']} | Artifacts created: {cr['artifacts_created']}")
            print(f"    Flags: revision_drift={cr['revision_drift']}, "
                  f"leak={cr['artifact_context_leak']}, "
                  f"x-domain={cr['cross_domain_contamination']}, "
                  f"continuity={cr['incorrect_continuity']}, "
                  f"safe_path={cr['safe_path_ok']}")
            for ts in cr.get("turn_summaries", []):
                print(f"      Turn {ts['turn']}: {ts['artifact_lifecycle_stage']} "
                      f"| source={ts['response_source']} "
                      f"| interests={ts['relevant_interests_count']} "
                      f"| active_after={ts['active_artifact_after']}")

    print("\n## OBSERVED PATTERNS")
    patterns = result["observed_patterns"]
    if not patterns:
        print("  (none)")
    else:
        for p in patterns:
            print(f"  {p}")

    # Contamination advisory section
    ca_total = result.get("contamination_advisories_total", 0)
    if ca_total > 0:
        print("\n## CONTAMINATION ADVISORY ANALYSIS")
        print(f"  Total CSC artifacts with advisories : {ca_total}")
        print(f"  Contamination rate                 : {result.get('contamination_rate', 0.0):.1%}")
        print(f"  Contamination-free count           : {result.get('contamination_free_count', 0)}")
        print(f"  Contaminated count                 : {result.get('contaminated_count', 0)}")

        by_type = result.get("contamination_by_type", {})
        if by_type:
            print("\n  ## CONTAMINATION BY TYPE")
            for ctype, count in by_type.items():
                print(f"    {ctype:<40} ×{count}")

        top_signals = result.get("top_contamination_signals", [])
        if top_signals:
            print("\n  ## TOP CONTAMINATION SOURCE SIGNALS")
            for entry in top_signals:
                print(f"    {entry['signal']:<40} ×{entry['count']}")

        healthy = result.get("healthy_scenarios", [])
        if healthy:
            print("\n  ## HEALTHY CONTINUITY SCENARIOS")
            for s in healthy:
                print(f"    [{s['id']}] {s.get('type', 'none')}")

        contaminated_list = result.get("contaminated_scenarios", [])
        if contaminated_list:
            print("\n  ## CONTAMINATED SCENARIOS")
            for s in contaminated_list:
                print(f"    [{s['id']}] type={s['type']} confidence={s['confidence']}")
                print(f"      reason: {s.get('reason', '')}")

        ca_patterns = result.get("contamination_observed_patterns", [])
        if ca_patterns:
            print("\n  ## CONTAMINATION OBSERVED PATTERNS")
            for p in ca_patterns:
                print(f"    {p}")

    # Top boundary hints
    top_boundary = sorted(result["boundary_hint_counts"].items(), key=lambda x: x[1], reverse=True)
    top_boundary_hints = [{"hint": h, "count": c} for h, c in top_boundary[:10]]

    # Top context selections
    top_ctx = sorted(result["context_selection_counts"].items(), key=lambda x: x[1], reverse=True)
    top_context_selections = [{"value": v, "count": c} for v, c in top_ctx]

    print("\n## CONTEXT AND BOUNDARY SIGNAL ANALYSIS")
    print(f"  Total artifacts analyzed         : {result['total_artifacts']}")
    print(f"  Context stable scenarios         : {result['context_stable_count']}")
    print(f"  Context unstable scenarios       : {result['context_unstable_count']}")
    print(f"  Boundary consistent transitions  : {result['boundary_consistent_count']}")
    print(f"  Boundary inconsistent transitions: {result['boundary_inconsistent_count']}")

    print("\n  ## CONTEXT SELECTION DISTRIBUTION")
    for entry in top_context_selections:
        print(f"    {entry['value']:<20} ×{entry['count']}")

    print("\n  ## CONTEXT BY LIFECYCLE STAGE")
    for stage, dist in result.get("context_selection_by_stage", {}).items():
        total_stage = sum(dist.values())
        parts = [f"{v}:{c}" for v, c in sorted(dist.items(), key=lambda x: -x[1])]
        print(f"    {stage:<15} ({total_stage} total) — {', '.join(parts)}")

    print("\n  ## TOP BOUNDARY HINTS")
    for entry in top_boundary_hints:
        print(f"    {entry['hint']:<15} ×{entry['count']}")

    if result.get("boundary_transitions"):
        print("\n  ## BOUNDARY INCONSISTENT TRANSITIONS (sample)")
        for t in result["boundary_transitions"][:10]:
            print(f"    [{t['scenario_id']}] {t['from']} → {t['to']}")

    print("\n" + "=" * 70)
    print("END OF REPORT — INSPECTION ONLY, NO SYSTEM CHANGES")
    print("=" * 70)


# ---------------------------------------------------------------------------
# 4. run_full_analysis (CLI entry point)
# ---------------------------------------------------------------------------
def run_full_analysis() -> dict:
    """Load all artifacts, run analysis, print report, return result."""
    artifacts = load_all_eval_artifacts()
    result = analyze_patterns(artifacts)
    print_analysis_report(result)
    return result
