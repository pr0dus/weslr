"""
Tests for frontier_store + material graph integration.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import tempfile
import uuid
from datetime import datetime, timezone

from weslr.modules.frontier_proposer import FrontierProposal


def test_store_add_get():
    """Store and retrieve a proposal."""
    from weslr.modules.frontier_store import FrontierProposalStore
    store = FrontierProposalStore(tenant_id="test_tenant")
    proposal = FrontierProposal(
        id="test123",
        title="CaTiO3",
        description="Test proposal",
        domain="materials",
        novelty_score=0.99,
        feasibility_score=0.8,
        risk_score=0.1,
        impact_score=0.7,
        difficulty_level="★★★ Hard / high risk",
        proposed_experiment_summary="Test",
        literature_check={"exists": False, "count": 0, "top_papers": [], "query_used": "test"},
        provenance=["test"],
        created_at=datetime.now(timezone.utc).isoformat(),
        status="new",
    )
    pid = store.add(proposal)
    assert pid is not None
    retrieved = store.get(pid)
    assert retrieved is not None
    assert retrieved.title == "CaTiO3"
    print("  ✓ store add/get — PASS")


def test_store_status_update():
    """Status update persists across store reload."""
    from weslr.modules.frontier_store import FrontierProposalStore
    store = FrontierProposalStore(tenant_id="test_status")
    proposal = FrontierProposal(
        id="test456",
        title="SrTiO3",
        description="Status test",
        domain="materials",
        novelty_score=0.95,
        feasibility_score=0.7,
        risk_score=0.2,
        impact_score=0.6,
        difficulty_level="★★ Moderate gap",
        proposed_experiment_summary="Test",
        literature_check={},
        provenance=[],
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    pid = store.add(proposal)
    assert store.update_status(pid, "under_review")
    # Reload
    store2 = FrontierProposalStore(tenant_id="test_status")
    items = store2.list(status_filter="under_review")
    assert any(i["proposal_id"] == pid for i in items)
    print("  ✓ store status update — PASS")


def test_graph_duplicate_suppression():
    """Known formula in graph is skipped by generator."""
    from weslr.modules.unified_matter_generator import MatterGenerator
    import json

    graph = {
        "metadata": {"version": "1.0"},
        "nodes": {
            "CaTiO3": {
                "prototype": "perovskite", "bandgap_ev": 3.2, "conductivity": "insulator",
                "a_site": "Ca", "b_site": "Ti", "x_anion": "O",
                "substitutions": {"A": ["Sr", "Ba"], "B": ["Zr"], "X": ["S"]}
            }
        }
    }
    fd, path = tempfile.mkstemp(suffix=".json")
    os.write(fd, json.dumps(graph).encode())
    os.close(fd)
    try:
        gen = MatterGenerator(seed=42, graph_path=path)
        cands = gen.generate_candidates(mode="strangeness", max_candidates=30, constraints={"min_abundance": 0.0})
        formulas = [c.composition_string() for c in cands]
        # CaTiO3 in conventional order should be suppressed
        # CaO3Ti (Hill order) is the same — both should be suppressed
        suppressed = [f for f in formulas if f.replace("CaO3Ti", "") == "" or f == "CaTiO3"]
        assert "CaTiO3" not in formulas and "CaO3Ti" not in formulas, \
            f"CaTiO3/CaO3Ti should be suppressed as known: {formulas}"
        print(f"  ✓ graph duplicate suppression: CaTiO3/CaO3Ti suppressed — PASS")
    finally:
        os.unlink(path)


def test_gap_detection():
    """Generator outputs compositions that fill graph gaps."""
    from weslr.modules.unified_matter_generator import MatterGenerator
    import json

    # Graph has CaTiO3 (A=Sr) and BaTiO3 but not SrTiO3
    graph = {
        "metadata": {"version": "1.0"},
        "nodes": {
            "CaTiO3": {
                "prototype": "perovskite", "bandgap_ev": 3.2, "conductivity": "insulator",
                "a_site": "Ca", "b_site": "Ti", "x_anion": "O",
                "substitutions": {"A": ["Sr", "Ba"], "B": [], "X": []}
            },
            "BaTiO3": {
                "prototype": "perovskite", "bandgap_ev": 3.0, "conductivity": "insulator",
                "a_site": "Ba", "b_site": "Ti", "x_anion": "O",
                "substitutions": {"A": ["Ca", "Sr"], "B": [], "X": []}
            }
        }
    }
    fd, path = tempfile.mkstemp(suffix=".json")
    os.write(fd, json.dumps(graph).encode())
    os.close(fd)
    try:
        gen = MatterGenerator(seed=42, graph_path=path)
        cands = gen.generate_candidates(mode="strangeness", max_candidates=30, constraints={"min_abundance": 0.0})
        formulas = [c.composition_string() for c in cands]
        # SrTiO3 (conventional order) or O3SrTi (Hill order) should appear as gap-filler
        has_sr_tio3 = "SrTiO3" in formulas or "O3SrTi" in formulas
        assert has_sr_tio3, f"SrTiO3/O3SrTi (gap) not generated. Formulas: {formulas}"
        print(f"  ✓ gap detection: SrTiO3 gap-filler generated — PASS")
    finally:
        os.unlink(path)


def test_graph_load_failure_graceful():
    """Missing graph file → generator works as before (no crash)."""
    from weslr.modules.unified_matter_generator import MatterGenerator
    gen = MatterGenerator(seed=99, graph_path="/nonexistent/path/graph.json")
    try:
        cands = gen.generate_candidates(mode="plausible", max_candidates=5, constraints={"min_abundance": 0.0})
        assert len(cands) >= 0
        print(f"  ✓ graph load failure graceful: {len(cands)} candidates generated — PASS")
    except Exception as e:
        raise AssertionError(f"Should not raise on missing graph: {e}")


def test_store_persistence():
    """Proposals survive store reload (append-only JSONL)."""
    from weslr.modules.frontier_store import FrontierProposalStore
    store1 = FrontierProposalStore(tenant_id="test_persist")
    p = FrontierProposal(
        id="persist1",
        title="Fe3O4",
        description="Persistence test",
        domain="materials",
        novelty_score=0.99,
        feasibility_score=0.9,
        risk_score=0.05,
        impact_score=0.6,
        difficulty_level="★ Low-hanging fruit",
        proposed_experiment_summary="Test",
        literature_check={},
        provenance=[],
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    pid = store1.add(p)
    # Simulate restart with new store instance
    store2 = FrontierProposalStore(tenant_id="test_persist")
    retrieved = store2.get(pid)
    assert retrieved is not None
    assert retrieved.title == "Fe3O4"
    print("  ✓ store persistence across reload — PASS")


if __name__ == "__main__":
    print("\n=== frontier_store + material_graph tests ===\n")
    test_store_add_get()
    test_store_status_update()
    test_graph_duplicate_suppression()
    test_gap_detection()
    test_graph_load_failure_graceful()
    test_store_persistence()
    print("\n✅ All tests passed.\n")