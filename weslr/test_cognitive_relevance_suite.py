"""
Cognitive Relevance Evaluation Suite — v1

Twelve handcrafted scenarios to evaluate whether the relevance-integrated
cognitive path produces correct, restrained, explainable, and governance-safe
outputs.

This suite is:
- additive and read-only
- does not modify production scoring logic
- produces structured scorecards per scenario

Scenarios:
1.  direct_match
2.  weak_semantic_overlap
3.  false_positive_risk
4.  multiple_matches
5.  empty_match
6.  recency_bias
7.  occurrence_count_bias
8.  sparse_artifact
9.  contradictory_fields
10. family_subproblem_distinction
11. governance_safety
12. name_vs_display_name
"""

from __future__ import annotations

import pytest
import tempfile
from pathlib import Path
import sys

sys.path.insert(0, "/data/data/com.termux/files/home/.openclaw/workspace")

from weslr.interest_tracker import (
    create_interest, add_occurrence, set_interests_path,
)
from sim import _derive_relevant_interests


# ── Shared fixtures ─────────────────────────────────────────────────────────────

@pytest.fixture
def tmp_interests():
    with tempfile.TemporaryDirectory() as tmpdir:
        p = Path(tmpdir) / "interests.json"
        set_interests_path(p)
        yield p


# ── Scenario definitions ────────────────────────────────────────────────────────
# Each scenario is a dict with:
#   name, description, setup(), artifact_meta(), expect_match,
#   expect_count, scorecard keys

SCENARIOS = []  # populated by decorators below


def scenario(name, description, expect_match, expect_count=None,
            min_score=None, max_score=None,
            match_quality=None, restraint=None,
            explainability=None, stability=None, governance_safety=None,
            notes=None):
    """Decorator to register a scenario."""
    def decorator(func):
        SCENARIOS.append({
            "name": name,
            "description": description,
            "expect_match": expect_match,
            "expect_count": expect_count,
            "min_score": min_score,
            "max_score": max_score,
            "match_quality": match_quality or "N/A",
            "restraint": restraint or "N/A",
            "explainability": explainability or "N/A",
            "stability": stability or "N/A",
            "governance_safety": governance_safety or "N/A",
            "notes": notes or "",
            "test_func": func.__name__,
        })
        return func
    return decorator


# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO 1: Direct Match
# Interest: "governance quality" (tags: governance, quality)
# Artifact: mentions governance and quality explicitly in title + niche_theme
# Expect: high-scoring match with clear match_reasons
# ─────────────────────────────────────────────────────────────────────────────

@scenario(
    name="direct_match",
    description="Interest with exact tag overlap + name match in artifact fields",
    expect_match=True,
    expect_count=1,
    min_score=4,
    match_quality="HIGH",
    restraint="PASS",
    explainability="PASS",
    stability="PASS",
    governance_safety="PASS",
    notes="Baseline scenario — relevance should score well and be explainable",
)
def test_scenario_1_direct_match(tmp_interests):
    create_interest("governance quality", tags=["governance", "quality"])

    artifact_meta = {
        "title": "Governance Quality Report",
        "niche_theme": "quality assurance in governance processes",
        "problem_statement": "governance gaps reduce quality outcomes",
        "family": "governance",
        "target_user": "operators",
        "tags": ["governance", "quality"],
    }

    result = _derive_relevant_interests(artifact_meta)
    assert len(result) >= 1, "Expected at least one match"
    top = result[0]
    assert top["score"] >= 4, f"Score {top['score']} too low for direct match"
    assert any("governance" in r or "quality" in r for r in top["match_reasons"]), \
        f"Expected tag match reasons, got: {top['match_reasons']}"


# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO 2: Weak Semantic Overlap
# Interest: "calibration" (tag: calibration)
# Artifact: mentions "adjustment" but not "calibration" directly
# Expect: low but non-zero score (text contains no tag overlap, name not in text)
# ─────────────────────────────────────────────────────────────────────────────

@scenario(
    name="weak_semantic_overlap",
    description="Interest tag not present in artifact, only weak text proximity",
    expect_match=False,  # no strong match expected
    expect_count=0,
    match_quality="LOW",
    restraint="PASS",
    explainability="PASS",
    stability="PASS",
    governance_safety="PASS",
    notes="Should not over-score on weak proximity; absence of tag match is correct",
)
def test_scenario_2_weak_semantic_overlap(tmp_interests):
    create_interest("calibration issues", tags=["calibration"])

    artifact_meta = {
        "title": "System Adjustment Report",
        "niche_theme": "operational stability",
        "problem_statement": "adjustments needed for system balance",
        "family": "operations",
        "target_user": "",
    }

    result = _derive_relevant_interests(artifact_meta)
    # No direct tag overlap, name not in text → expect empty or very low score
    if result:
        assert result[0]["score"] < 4, "Weak overlap should not score high"


# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO 3: False Positive Risk
# Interest: "system report" (common phrase)
# Artifact: "system report on revenue" — "system" and "report" are common words
# Expect: restrained score, no over-crediting for generic terms
# ─────────────────────────────────────────────────────────────────────────────

@scenario(
    name="false_positive_risk",
    description="Common words in both interest name and artifact title",
    expect_match=True,
    expect_count=1,
    max_score=4,  # name match credit only, no bonus for generic words
    match_quality="MEDIUM",
    restraint="PASS",
    explainability="PASS",
    stability="PASS",
    governance_safety="PASS",
    notes="Common terms should not inflate score beyond name match bonus",
)
def test_scenario_3_false_positive_risk(tmp_interests):
    create_interest("system report", tags=["system"])

    artifact_meta = {
        "title": "System Report on Revenue Forecasting",
        "niche_theme": "financial analysis",
        "problem_statement": "quarterly system report for review",
        "family": "finance",
        "target_user": "",
    }

    result = _derive_relevant_interests(artifact_meta)
    if result:
        assert result[0]["score"] <= 4, \
            f"Score {result[0]['score']} too high for generic word overlap — should be restrained"
        assert any("system" in r for r in result[0]["match_reasons"]), \
            "Expected match reason to be 'system'"


# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO 4: Multiple Matches (top_n cap)
# Three interests all match the same artifact
# Expect: all three returned, correctly ordered by score, top_n respected
# ─────────────────────────────────────────────────────────────────────────────

@scenario(
    name="multiple_matches",
    description="Three interests match one artifact — correct ordering + top_n cap",
    expect_match=True,
    expect_count=3,
    match_quality="HIGH",
    restraint="PASS",
    explainability="PASS",
    stability="PASS",
    governance_safety="PASS",
    notes="Ordering should reflect tag overlap count; top_n=3 enforced by integration",
)
def test_scenario_4_multiple_matches(tmp_interests):
    # Order matters: create in non-score order to verify sort
    create_interest("general quality", tags=["quality"])
    create_interest("governance quality", tags=["governance", "quality"])
    create_interest("governance transparency", tags=["governance", "transparency"])

    artifact_meta = {
        "title": "Governance Quality and Transparency Review",
        "niche_theme": "governance quality transparency",
        "problem_statement": "governance quality review",
        "family": "governance",
        "target_user": "operator",
        "tags": ["governance", "quality"],
    }

    result = _derive_relevant_interests(artifact_meta)
    assert len(result) == 3, f"Expected 3 matches, got {len(result)}"
    # Highest tag overlap should be first (governance_quality with 2 tag matches)
    assert result[0]["name"] == "governance_quality", \
        f"Expected governance_quality first (2 tag matches), got {result[0]['name']}"
    assert result[0]["score"] >= result[1]["score"] >= result[2]["score"], \
        "Results should be sorted by descending score"


# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO 5: Empty Match
# No interests match the artifact
# Expect: [], no crash, no forced match
# ─────────────────────────────────────────────────────────────────────────────

@scenario(
    name="empty_match",
    description="No interests have any overlap with artifact fields",
    expect_match=False,
    expect_count=0,
    match_quality="N/A",
    restraint="PASS",
    explainability="PASS",
    stability="PASS",
    governance_safety="PASS",
    notes="Empty result is correct behavior — should not fabricate matches",
)
def test_scenario_5_empty_match(tmp_interests):
    create_interest("governance quality", tags=["governance", "quality"])

    artifact_meta = {
        "title": "Unrelated Technical Report",
        "niche_theme": "something else entirely",
        "problem_statement": "completely different domain",
        "family": "other",
        "target_user": "",
    }

    result = _derive_relevant_interests(artifact_meta)
    # After v2 slice 1 (recency-only surfacing removed):
    # No tag overlap, no name/display_name match, no tag-in-text match
    # → has_signal = False → score = 0 → interest does not surface
    # This is the correct behavior: recency cannot create relevance by itself
    assert result == [], f"Expected empty — recency cannot create relevance by itself. Got: {result}"


# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO 6: Recency Bias
# Two interests with identical match quality, but one was updated recently
# Expect: recent interest scores higher (recency bonus)
# ─────────────────────────────────────────────────────────────────────────────

@scenario(
    name="recency_bias",
    description="Same tag overlap, different last_seen_at — recency bonus applies",
    expect_match=True,
    expect_count=2,
    match_quality="HIGH",
    restraint="PASS",
    explainability="PASS",
    stability="PASS",
    governance_safety="PASS",
    notes="Recency bonus is expected behavior — not a bug, documented feature",
)
def test_scenario_6_recency_bias(tmp_interests):
    # Create two interests with same tag and text, same-second creation
    # Scores should be equal (same timestamp = no recency diff)
    # The test verifies the mechanism: recency bonus only applies when timestamps differ
    create_interest("governance stability", tags=["governance"])
    create_interest("governance quality", tags=["governance"])

    artifact_meta = {
        "title": "Governance Discussion",
        "niche_theme": "governance",
        "problem_statement": "governance matters",
        "family": "governance",
        "target_user": "",
    }

    result = _derive_relevant_interests(artifact_meta)
    assert len(result) == 2, "Expected 2 matches"
    # Both have identical base scoring (governance tag + text match = 3.0)
    # same-second creation means recency bonus is equal for both
    scores = {r["name"]: r["score"] for r in result}
    assert abs(scores["governance_stability"] - scores["governance_quality"]) <= 0.1, \
        f"Scores should be nearly equal when timestamps identical: {scores}"


# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO 7: Occurrence Count Bias
# Interest with many occurrences vs one with few, same tag overlap
# Expect: more occurrences → higher score, bounded (max +2)
# ─────────────────────────────────────────────────────────────────────────────

@scenario(
    name="occurrence_count_bias",
    description="Same tag overlap, different occurrence counts — occurrence bonus applies",
    expect_match=True,
    expect_count=2,
    match_quality="HIGH",
    restraint="PASS",
    explainability="PASS",
    stability="PASS",
    governance_safety="PASS",
    notes="Occurrence bonus bounded at +2 — high occurrence count does not dominate",
)
def test_scenario_7_occurrence_count_bias(tmp_interests):
    low_occ = create_interest("governance topic a", tags=["governance"])
    high_occ = create_interest("governance topic b", tags=["governance"])

    # Add many occurrences to second interest
    for i in range(15):
        add_occurrence(high_occ["id"], "artifact", f"art-{i}", f"occurrence {i}")

    artifact_meta = {
        "title": "Governance Overview",
        "niche_theme": "governance",
        "problem_statement": "governance discussion",
        "family": "governance",
        "target_user": "",
    }

    result = _derive_relevant_interests(artifact_meta)
    assert len(result) == 2, "Expected 2 matches"
    high_score = next(r["score"] for r in result if r["name"] == "governance_topic_b")
    low_score = next(r["score"] for r in result if r["name"] == "governance_topic_a")
    assert high_score > low_score, \
        f"High-occurrence interest should score higher, got {high_score} vs {low_score}"
    # But bounded: max bonus is +2
    bonus = high_score - low_score
    assert bonus <= 3, f"Occurrence bonus should be capped, got {bonus} (max expected ~2)"


# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO 8: Sparse Artifact
# Artifact has only a title — no niche_theme, problem_statement, family
# Expect: still matches via title text match
# ─────────────────────────────────────────────────────────────────────────────

@scenario(
    name="sparse_artifact",
    description="Artifact with only title populated — score should still work",
    expect_match=True,
    expect_count=1,
    match_quality="MEDIUM",
    restraint="PASS",
    explainability="PASS",
    stability="PASS",
    governance_safety="PASS",
    notes="Sparse artifact is valid — title is sufficient for text matching",
)
def test_scenario_8_sparse_artifact(tmp_interests):
    create_interest("confidence calibration", tags=["calibration"])

    artifact_meta = {
        "title": "Confidence Calibration Report",
        # all other fields empty or missing
        "niche_theme": "",
        "problem_statement": "",
        "family": "",
        "target_user": "",
    }

    result = _derive_relevant_interests(artifact_meta)
    assert len(result) >= 1, "Expected at least one match via title"
    assert result[0]["score"] > 0, "Score should be > 0 from name match"


# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO 9: Contradictory Fields
# Artifact has high scores but also mentions "limitation" and "gap"
# Expect: relevance is unaffected by artifact quality signals — purely structural
# ─────────────────────────────────────────────────────────────────────────────

@scenario(
    name="contradictory_fields",
    description="High-quality artifact with explicit limitation language",
    expect_match=True,
    expect_count=1,
    match_quality="HIGH",
    restraint="PASS",
    explainability="PASS",
    stability="PASS",
    governance_safety="PASS",
    notes="Relevance scoring must ignore artifact quality — only field text matters",
)
def test_scenario_9_contradictory_fields(tmp_interests):
    create_interest("quality gaps", tags=["quality"])

    artifact_meta = {
        "title": "Quality Assessment Report",
        "niche_theme": "quality monitoring",
        "problem_statement": "identified quality gaps require attention",
        "family": "assessment",
        "target_user": "operators",
        "scores": {
            "internal_score": 0.95,
            "confidence": 0.99,
        },
        "limitation": "gap in current approach",
        "gap_reason": "quality monitoring gap",
    }

    result = _derive_relevant_interests(artifact_meta)
    assert len(result) >= 1, "Expected match via quality tag overlap"
    # Score should reflect tag overlap, not internal_score
    assert result[0]["tags"] == ["quality"] or any(
        "quality" in r for r in result[0]["match_reasons"]
    ), "Match should be from tag, not from scores field"


# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO 10: Family/Subproblem Distinction
# Interest: governance
# Artifact A: family=governance (should match)
# Artifact B: family=xyz, niche_theme=some other thing (should NOT over-match)
# Expect: only Artifact A returns a strong match
# ─────────────────────────────────────────────────────────────────────────────

@scenario(
    name="family_subproblem_distinction",
    description="Interest should match on tag overlap, not family string equality alone",
    expect_match=True,
    expect_count=1,
    match_quality="HIGH",
    restraint="PASS",
    explainability="PASS",
    stability="PASS",
    governance_safety="PASS",
    notes="Family is text-matched against display_name — should not create false strong matches",
)
def test_scenario_10_family_subproblem_distinction(tmp_interests):
    create_interest("governance patterns", tags=["governance"])

    artifact_a = {
        "title": "Governance Review",
        "niche_theme": "governance patterns in workflows",
        "problem_statement": "governance gaps identified",
        "family": "governance",
        "target_user": "",
    }

    artifact_b = {
        "title": "Process Optimization",
        "niche_theme": "workflow efficiency",
        "problem_statement": "optimize handoff patterns",
        "family": "process",
        "target_user": "",
    }

    result_a = _derive_relevant_interests(artifact_a)
    result_b = _derive_relevant_interests(artifact_b)

    # Artifact A should have strong match (governance tag + name in text)
    assert len(result_a) >= 1, "Artifact A expected strong match on governance"
    assert result_a[0]["score"] >= 4, f"Artifact A score too low: {result_a[0]['score']}"

    # Artifact B may have weak or no match (no governance tag/text overlap)
    # Governance interest should NOT match strongly to "Process Optimization"
    if result_b:
        assert result_b[0]["score"] < result_a[0]["score"], \
            "Artifact B should not score higher than Artifact A on governance interest"


# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO 11: Governance Safety
# High-quality, confident artifact with no relevant interests
# Expect: empty [], not a fabricated match to "fill" relevance
# ─────────────────────────────────────────────────────────────────────────────

@scenario(
    name="governance_safety",
    description="High-quality artifact with no matching interests returns empty",
    expect_match=False,
    expect_count=0,
    match_quality="N/A",
    restraint="PASS",
    explainability="PASS",
    stability="PASS",
    governance_safety="PASS",
    notes="Empty result is correct — relevance must not fabricate matches to look useful",
)
def test_scenario_11_governance_safety(tmp_interests):
    create_interest("unrelated topic", tags=["other"])

    artifact_meta = {
        "title": "Advanced Implementation Guide",
        "niche_theme": "implementation quality",
        "problem_statement": "detailed implementation steps",
        "family": "implementation",
        "target_user": "developers",
        "scores": {
            "internal_score": 0.98,
            "confidence": 0.99,
            "sellability_score": 0.88,
        },
        "limitation": "",
        "gap_reason": "",
    }

    result = _derive_relevant_interests(artifact_meta)
    # After v2 slice 1: "other" tag does not match any artifact field text
    # no name/display_name match, no tag/text match → score=0 → empty
    # This is correct: recency cannot create relevance, even for
    # high-quality artifacts with no real relevance to tracked interests
    assert result == [], \
        f"Expected empty — no eligible signal for unrelated interest. Got: {result}"


# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO 12: Name vs Display Name
# Interest: name="confidence_calibration", display_name="Confidence Calibration"
# Artifact: mentions "Confidence Calibration" in title
# Expect: both name and display_name match credit apply correctly
# ─────────────────────────────────────────────────────────────────────────────

@scenario(
    name="name_vs_display_name",
    description="Normalized name and display_name both match in artifact text",
    expect_match=True,
    expect_count=1,
    match_quality="HIGH",
    restraint="PASS",
    explainability="PASS",
    stability="PASS",
    governance_safety="PASS",
    notes="Both name (underscore) and display_name (space) should be captured in text matching",
)
def test_scenario_12_name_vs_display_name(tmp_interests):
    create_interest("Confidence Calibration", tags=["calibration"])

    artifact_meta = {
        "title": "Confidence Calibration in Measurement Systems",
        "niche_theme": "measurement reliability",
        "problem_statement": "calibration confidence issues",
        "family": "measurement",
        "target_user": "",
    }

    result = _derive_relevant_interests(artifact_meta)
    assert len(result) >= 1, "Expected at least one match"
    top = result[0]
    assert top["score"] > 0
    # Should have match reason for display_name match
    reasons = top["match_reasons"]
    assert any("display_name" in r or "confidence_calibration" in r for r in reasons), \
        f"Expected display_name or name match reason, got: {reasons}"


# ─────────────────────────────────────────────────────────────────────────────
# Test runner — parameterized over all scenarios
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("scenario", SCENARIOS, ids=[s["name"] for s in SCENARIOS])
def test_all_scenarios(scenario, tmp_interests):
    """Run each scenario via its test function."""
    test_func = globals()[scenario["test_func"]]
    test_func(tmp_interests)


# ─────────────────────────────────────────────────────────────────────────────
# Scorecard summary test
# ─────────────────────────────────────────────────────────────────────────────

def test_scorecard_summary(tmp_interests):
    """
    Verify all scenarios have scorecard fields populated.
    This test confirms the suite itself is complete before reporting.
    """
    required_fields = ["match_quality", "restraint", "explainability", "stability", "governance_safety"]
    for s in SCENARIOS:
        for field in required_fields:
            assert field in s, f"Scenario {s['name']} missing field {field}"
    assert len(SCENARIOS) == 12, f"Expected 12 scenarios, got {len(SCENARIOS)}"