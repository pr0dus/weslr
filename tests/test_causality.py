# Tests for Phase 6.5 – Causality Detection
# Run with: python3 -m pytest tests/test_causality.py -v

import sys
import math
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from weslr.modules.causality import (
    correlation_test,
    time_order_heuristic,
    confounder_check,
    causal_confidence,
    suggest_intervention,
    register_dataset,
    get_dataset,
    list_datasets,
    clear_datasets,
    is_causal_topic,
    CAUSAL_KEYWORDS,
)


# ── Helpers ─────────────────────────────────────────────────────────────────────

def cclose(a, b, tol=1e-6):
    return abs(a - b) < tol


# ── Correlation Tests ─────────────────────────────────────────────────────────

def test_pearson_high_correlation():
    # y = 2x + noise-free
    x = [1.0, 2.0, 3.0, 4.0, 5.0]
    y = [2.1, 4.0, 6.1, 7.9, 10.2]
    r = correlation_test(x, y, test_type="pearson", seed=42)
    assert cclose(r["statistic"], 1.0, tol=0.05), f"r={r['statistic']}"
    assert r["significant"], f"should be significant: {r}"
    assert cclose(r["effect_size"], 1.0, tol=0.05)
    print("  pearson_high ok")


def test_pearson_no_correlation():
    x = [1.0, 2.0, 3.0, 4.0, 5.0]
    y = [100.0, -50.0, 200.0, -100.0, 150.0]
    r = correlation_test(x, y, test_type="pearson", seed=42)
    assert abs(r["statistic"]) < 0.5
    print("  pearson_no_correlation ok")


def test_pearson_negative():
    x = [1.0, 2.0, 3.0, 4.0, 5.0]
    y = [5.0, 4.0, 3.0, 2.0, 1.0]
    r = correlation_test(x, y, test_type="pearson", seed=42)
    assert r["statistic"] < -0.9
    assert r["significant"]
    print("  pearson_negative ok")


def test_chi2_significant():
    # Strong association: x and y both 0→0, 1→1
    x = [0, 0, 0, 1, 1, 1]
    y = [0, 0, 0, 1, 1, 1]
    r = correlation_test(x, y, test_type="chi2")
    assert r["significant"], f"chi2 should be significant: {r}"
    print("  chi2_significant ok")


def test_chi2_independent():
    x = [0, 0, 0, 1, 1, 1]
    y = [1, 1, 1, 0, 0, 0]
    r = correlation_test(x, y, test_type="chi2")
    # Perfect inverse relationship
    assert r["significant"], f"should be significant: {r}"
    print("  chi2_independent ok")


# ── Temporal Heuristic ──────────────────────────────────────────────────────

def test_temporal_a_before_b():
    timeline = [("A", 1.0), ("A", 2.0), ("B", 3.0), ("B", 4.0)]
    score = time_order_heuristic(timeline, "A", "B")
    assert score == 1, f"Expected 1, got {score}"
    print("  temporal_a_before_b ok")


def test_temporal_b_before_a():
    timeline = [("B", 1.0), ("B", 2.0), ("A", 3.0), ("A", 4.0)]
    score = time_order_heuristic(timeline, "A", "B")
    assert score == -1, f"Expected -1, got {score}"
    print("  temporal_b_before_a ok")


def test_temporal_missing():
    timeline = [("X", 1.0), ("X", 2.0)]
    score = time_order_heuristic(timeline, "A", "B")
    assert score == 0, f"Expected 0 for missing, got {score}"
    print("  temporal_missing ok")


def test_temporal_overlapping():
    timeline = [("A", 1.0), ("B", 2.0), ("A", 3.0), ("B", 4.0)]
    score = time_order_heuristic(timeline, "A", "B")
    assert score == 0, f"Expected 0 for overlap, got {score}"
    print("  temporal_overlapping ok")


# ── Confounder Check ──────────────────────────────────────────────────────────

def test_confounder_detected():
    # C causes both A and B (spurious correlation)
    # C: [1..8], A: C + small noise, B: C + small noise
    # Raw correlation A-B will be high, but after conditioning on C it should drop
    clear_datasets()
    register_dataset("test_conf", {
        "A": [1.1, 2.1, 3.1, 4.1, 5.1, 6.1, 7.1, 8.1],
        "B": [1.2, 2.2, 3.2, 4.2, 5.2, 6.2, 7.2, 8.2],
        "C": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0],
    })
    data = get_dataset("test_conf")
    result = confounder_check("A", "B", ["C"], data, seed=42)
    assert "C" in result["confounders_found"], f"C should be flagged: {result}"
    raw = result["raw_correlation"]
    adj = result["adjustments"]["C"]
    assert raw - adj > 0.2, f"Raw={raw:.3f}, adj={adj:.3f} should differ"
    print("  confounder_detected ok")


def test_confounder_not_detected():
    clear_datasets()
    register_dataset("test_noconf", {
        "A": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0],
        "B": [2.1, 4.1, 6.0, 7.9, 10.1, 12.0, 14.0, 16.1],
        "C": [100.0, 101.0, 99.0, 102.0, 100.0, 101.0, 99.0, 102.0],  # weak C
    })
    data = get_dataset("test_noconf")
    result = confounder_check("A", "B", ["C"], data, seed=42)
    assert len(result["confounders_found"]) == 0 or result["confounders_found"] == []
    print("  confounder_not_detected ok")


# ── Causal Confidence ─────────────────────────────────────────────────────────

def test_confidence_high():
    corr = {"statistic": 0.9, "p_value": 0.001, "effect_size": 0.9, "significant": True, "n": 50}
    temporal = 1
    conf = {"raw_correlation": 0.9, "confounders_found": [], "adjustments": {}}
    result = causal_confidence(corr, temporal, conf, literature_support=0.0)
    assert result["level"] == "high", f"Should be high: {result['level']}"
    assert result["score"] > 0.7
    print("  confidence_high ok")


def test_confidence_low():
    corr = {"statistic": 0.2, "p_value": 0.3, "effect_size": 0.2, "significant": False, "n": 20}
    temporal = 0
    conf = {"confounders_found": [], "adjustments": {}}
    result = causal_confidence(corr, temporal, conf, literature_support=0.0)
    assert result["level"] == "low"
    print("  confidence_low ok")


def test_confidence_medium():
    corr = {"statistic": 0.5, "p_value": 0.01, "effect_size": 0.5, "significant": True, "n": 30}
    temporal = 0
    conf = {"confounders_found": [], "adjustments": {}}
    result = causal_confidence(corr, temporal, conf, literature_support=0.0)
    assert result["level"] == "medium"
    print("  confidence_medium ok")


def test_confidence_with_confounder():
    corr = {"statistic": 0.8, "p_value": 0.001, "effect_size": 0.8, "significant": True, "n": 50}
    temporal = 1
    conf = {"confounders_found": ["age"], "adjustments": {"age": 0.4}}
    result = causal_confidence(corr, temporal, conf, literature_support=0.0)
    assert result["level"] in ("medium", "low"), f"Should be med/low not {result['level']}"
    print("  confidence_with_confounder ok")


def test_confidence_literature_boost():
    corr = {"statistic": 0.4, "p_value": 0.05, "effect_size": 0.4, "significant": True, "n": 30}
    temporal = 0
    conf = {"confounders_found": [], "adjustments": {}}
    # With literature support
    result = causal_confidence(corr, temporal, conf, literature_support=0.8)
    assert result["score"] > 0.4
    print("  confidence_literature_boost ok")


# ── Intervention Simulation ──────────────────────────────────────────────────

def test_intervention_slope():
    clear_datasets()
    register_dataset("test_interv", {
        "A": [10.0, 20.0, 30.0, 40.0, 50.0],
        "B": [22.0, 42.0, 60.0, 82.0, 98.0],
    })
    data = get_dataset("test_interv")
    graph = {("A", "B"): 0.9}
    result = suggest_intervention("A", "B", graph, data, intervention_value=100.0, seed=42)
    assert result["intervention_value"] == 100.0
    assert "change_pct" in result
    assert "interpretation" in result
    print("  intervention_slope ok")


def test_intervention_default_value():
    clear_datasets()
    register_dataset("test_interv2", {
        "X": [1.0, 2.0, 3.0, 4.0, 5.0],
        "Y": [3.0, 5.0, 7.0, 9.0, 11.0],
    })
    data = get_dataset("test_interv2")
    graph = {("X", "Y"): 0.99}
    result = suggest_intervention("X", "Y", graph, data, seed=42)
    assert result["intervention_value"] == 3.0  # median of [1..5]
    print("  intervention_default_value ok")


# ── is_causal_topic ─────────────────────────────────────────────────────────

def test_is_causal_topic_positive():
    assert is_causal_topic("does drug dose cause response?")
    assert is_causal_topic("causal graph for heart disease")
    assert is_causal_topic("confounder analysis")
    print("  is_causal_topic_positive ok")


def test_is_causal_topic_negative():
    assert not is_causal_topic("population growth logistic equation")
    assert not is_causal_topic("symbolic integration x**2")
    print("  is_causal_topic_negative ok")


# ── Command Integration ──────────────────────────────────────────────────────

def test_propose_cause_handler():
    from weslr.commands.causality_commands import handle_causal_propose

    clear_datasets()
    r = handle_causal_propose(
        "/propose cause drug_dose response clinical_dose_response",
        "/propose cause drug_dose response clinical_dose_response"
    )
    assert "Causal Analysis" in r
    assert "Confidence" in r or "confidence" in r
    print("  propose_cause_handler ok")


def test_causal_graph_empty():
    from weslr.commands.causality_commands import handle_causal_propose, _USER_SESSIONS

    # Reset session
    _USER_SESSIONS.clear()
    r = handle_causal_propose("/causal graph", "/causal graph")
    assert "no causal graph" in r.lower() or "no graph" in r.lower()
    print("  causal_graph_empty ok")


def test_causal_intervene():
    from weslr.commands.causality_commands import handle_causal_propose

    clear_datasets()
    r = handle_causal_propose(
        "/causal intervene drug_dose=50 --dataset clinical_dose_response",
        "/causal intervene drug_dose=50 --dataset clinical_dose_response"
    )
    assert "Intervention" in r or "intervention" in r
    print("  causal_intervene ok")


def test_refine_cause():
    from weslr.commands.causality_commands import handle_causal_propose

    clear_datasets()
    r = handle_causal_propose(
        "/refine cause confounder age for drug_dose response --dataset clinical_dose_response",
        "/refine cause confounder age for drug_dose response --dataset clinical_dose_response"
    )
    assert "Refined" in r or "confidence" in r.lower()
    print("  refine_cause ok")


def test_causal_unknown_dataset():
    from weslr.commands.causality_commands import handle_causal_propose

    r = handle_causal_propose(
        "/propose cause A B nonexistent_dataset",
        "/propose cause A B nonexistent_dataset"
    )
    assert "not found" in r
    print("  causal_unknown_dataset ok")


# ── Dataset Registry ─────────────────────────────────────────────────────────

def test_dataset_list():
    datasets = list_datasets()
    assert "clinical_dose_response" in datasets
    assert "confounded_demo" in datasets
    print("  dataset_list ok")


def test_get_dataset():
    data = get_dataset("clinical_dose_response")
    assert "drug_dose" in data
    assert "response" in data
    assert len(data["drug_dose"]) == len(data["response"])
    print("  get_dataset ok")


def test_register_dataset():
    clear_datasets()
    register_dataset("my_ds", {"X": [1, 2, 3], "Y": [4, 5, 6]})
    data = get_dataset("my_ds")
    assert data["X"] == [1, 2, 3]
    print("  register_dataset ok")


# ── Run all ───────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    tests = [
        # Correlation
        test_pearson_high_correlation,
        test_pearson_no_correlation,
        test_pearson_negative,
        test_chi2_significant,
        test_chi2_independent,
        # Temporal
        test_temporal_a_before_b,
        test_temporal_b_before_a,
        test_temporal_missing,
        test_temporal_overlapping,
        # Confounder
        test_confounder_detected,
        test_confounder_not_detected,
        # Confidence
        test_confidence_high,
        test_confidence_low,
        test_confidence_medium,
        test_confidence_with_confounder,
        test_confidence_literature_boost,
        # Intervention
        test_intervention_slope,
        test_intervention_default_value,
        # Topic
        test_is_causal_topic_positive,
        test_is_causal_topic_negative,
        # Commands
        test_propose_cause_handler,
        test_causal_graph_empty,
        test_causal_intervene,
        test_refine_cause,
        test_causal_unknown_dataset,
        # Dataset
        test_dataset_list,
        test_get_dataset,
        test_register_dataset,
    ]
    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            print(f"  FAIL {t.__name__}: {e}")
            failed += 1
    print(f"\n=== {passed}/{passed+failed} passed ===")
    if failed:
        sys.exit(1)
