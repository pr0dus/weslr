from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from weslr.internal_reasoning_graph.models import GovernanceStatus, NodeFactory
from weslr.internal_reasoning_graph.query import InternalReasoningGraphQuery
from weslr.internal_reasoning_graph.reasoning_engine import (
    ReasoningEngine,
    create_enrichment_gap_record,
    link_enrichment_gap_to_graph,
    mark_enrichment_gap_status,
    summarize_enrichment_gap_record,
)
from weslr.internal_reasoning_graph.store import InternalReasoningGraphStore


class InternalReasoningEnrichmentRecordTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.graph_dir = Path(self.tempdir.name) / "irg"
        self.store = InternalReasoningGraphStore(graph_dir=self.graph_dir)

        self.capability = NodeFactory.create_capability(
            id="cap_reasoning",
            name="Ordinary Reasoning",
            description="Handles ordinary reasoning tasks.",
            node_subtype="analysis",
            confidence=0.7,
        )
        self.store.save_node(self.capability)

    def tearDown(self):
        self.tempdir.cleanup()

    def test_can_create_enrichment_gap_record_from_eval_failure_with_required_fields(self):
        gap = create_enrichment_gap_record(
            self.store,
            name="Ordinary reasoning gap",
            description="Reasoning quality drops on multi-step ordinary tasks.",
            source_eval="random_ordinary_intelligence_prep_v1",
            source_prompt="Why does this multi-step ordinary reasoning task fail?",
            category="ordinary_reasoning",
            current_path="eval -> gap graph -> internal_reasoning_graph",
            failure_mode="multi_step_drop",
            missing_skill="ordinary multi-step reasoning repair",
            target_substrate="internal_reasoning_graph",
            proposed_enrichment="Add enrichment gap records and explicit refinement links",
            legibility_summary="The eval failure points to missing repair reasoning that should be represented in the internal reasoning graph.",
            evidence_refs=["eval:random_ordinary_intelligence_prep_v1#case-3"],
            before_score=0.42,
            after_score=None,
            affected_node_ids=[self.capability.id],
            store_raw_prompt=False,
            confidence=0.78,
        )

        self.assertEqual(gap.node_type, "bottleneck")
        self.assertEqual(gap.node_subtype, "analysis")
        self.assertEqual(gap.metadata["record_type"], "enrichment_gap")
        self.assertEqual(gap.metadata["source_eval"], "random_ordinary_intelligence_prep_v1")
        self.assertEqual(gap.metadata["category"], "ordinary_reasoning")
        self.assertEqual(gap.metadata["failure_mode"], "multi_step_drop")
        self.assertEqual(gap.metadata["missing_skill"], "ordinary multi-step reasoning repair")
        self.assertEqual(gap.metadata["target_substrate"], "internal_reasoning_graph")
        self.assertTrue(gap.metadata["operator_review_required"])
        self.assertTrue(gap.metadata["read_only"])
        self.assertEqual(gap.metadata["status"], "observed")
        self.assertEqual(gap.metadata["before_score"], 0.42)
        self.assertIsNone(gap.metadata["after_score"])
        self.assertTrue(gap.metadata["source_prompt_fingerprint"])
        self.assertIsNone(gap.metadata["source_prompt"])
        self.assertIn("internal reasoning graph", gap.metadata["legibility_summary"].lower())
        self.assertFalse(gap.metadata["execution_allowed"])

        edges = self.store.find_edges_for_node(self.capability.id)
        self.assertTrue(any(e.edge_type == "bottleneck_for" and e.target_id == gap.id for e in edges))

    def test_record_allows_raw_prompt_only_in_temp_fixtures(self):
        gap = create_enrichment_gap_record(
            self.store,
            name="Fixture prompt gap",
            description="Temporary in-memory fixture allows raw prompt storage.",
            source_eval="fixture_eval_v1",
            source_prompt="Raw prompt allowed in temp fixtures.",
            category="fixture",
            current_path="eval -> gap graph -> internal_reasoning_graph",
            failure_mode="fixture_case",
            missing_skill="fixture handling",
            target_substrate="internal_reasoning_graph",
            proposed_enrichment="Store raw prompt only when explicitly allowed",
            legibility_summary="This fixture proves raw prompt storage stays opt-in.",
            before_score=0.2,
            after_score=0.4,
            store_raw_prompt=True,
        )

        summary = summarize_enrichment_gap_record(self.store, gap.id, include_sensitive=False)
        self.assertNotIn("source_prompt", summary)
        sensitive = summarize_enrichment_gap_record(self.store, gap.id, include_sensitive=True)
        self.assertEqual(sensitive["source_prompt"], "Raw prompt allowed in temp fixtures.")
        self.assertEqual(sensitive["after_score"], 0.4)

    def test_linking_represents_required_graph_relationships(self):
        gap = create_enrichment_gap_record(
            self.store,
            name="Calibration gap",
            description="Confidence estimates drift under ambiguous prompts.",
            source_eval="calibration_suite_v1",
            category="calibration",
            current_path="eval -> gap graph -> internal_reasoning_graph",
            failure_mode="confidence_drift",
            missing_skill="confidence calibration repair",
            target_substrate="internal_reasoning_graph",
            proposed_enrichment="Add calibration gap enrichment records",
            legibility_summary="Calibration failures should remain legible as graph-linked enrichment records.",
            before_score=0.31,
            after_score=0.31,
            affected_node_ids=[self.capability.id],
            confidence=0.81,
        )
        links = link_enrichment_gap_to_graph(self.store, gap.id)

        query = InternalReasoningGraphQuery(self.store)
        gaps = query.detect_architecture_gaps()
        explicit = [g for g in gaps if g.gap_id == gap.id]

        self.assertEqual(len(explicit), 1)
        self.assertEqual(explicit[0].gap_type, "calibration")
        self.assertEqual(
            explicit[0].suggested_proposals[0]["source_eval"],
            "calibration_suite_v1",
        )
        self.assertEqual(
            explicit[0].suggested_proposals[0]["before_score"],
            0.31,
        )
        self.assertEqual(links["gap_record_id"], gap.id)

        edges = {(edge.source_id, edge.target_id, edge.edge_type) for edge in self.store.list_edges()}
        self.assertIn((gap.id, links["missing_skill_node_id"], "depends_on"), edges)
        self.assertIn((links["missing_skill_node_id"], links["target_substrate_node_id"], "depends_on"), edges)
        self.assertIn((links["target_substrate_node_id"], links["proposed_enrichment_node_id"], "strengthens"), edges)
        self.assertIn((links["proposed_enrichment_node_id"], links["target_substrate_node_id"], "proposes_change_to"), edges)
        self.assertIn((links["proposed_enrichment_node_id"], links["tests_required_node_id"], "validated_by"), edges)
        self.assertIn((links["proposed_enrichment_node_id"], links["operator_review_node_id"], "governed_by"), edges)

        summary = summarize_enrichment_gap_record(self.store, gap.id)
        relations = {item["relation"] for item in summary["graph_relationships"]}
        self.assertIn("eval_failure_to_missing_skill", relations)
        self.assertIn("missing_skill_to_target_substrate", relations)
        self.assertIn("target_substrate_to_proposed_enrichment", relations)
        self.assertIn("proposed_enrichment_to_tests_required", relations)
        self.assertIn("proposed_enrichment_to_operator_review", relations)

    def test_status_transitions_are_explicit_and_non_executing(self):
        gap = create_enrichment_gap_record(
            self.store,
            name="Conversation resilience gap",
            description="Conversation quality degrades after repair turns.",
            source_eval="conversation_resilience_eval_v1",
            category="conversation_resilience",
            current_path="eval -> gap graph -> internal_reasoning_graph",
            failure_mode="repair_turn_degradation",
            missing_skill="repair-turn resilience",
            target_substrate="internal_reasoning_graph",
            proposed_enrichment="Extend reasoning metadata and eval linkage for repair turns",
            legibility_summary="Repair-turn degradation should be represented as a pending enrichment, not auto-implemented.",
            confidence=0.74,
        )
        self.assertEqual(gap.metadata["status"], "observed")
        self.assertEqual(gap.governance_status, GovernanceStatus.PENDING.value)
        self.assertFalse(gap.metadata["execution_allowed"])

        proposed = mark_enrichment_gap_status(self.store, gap.id, "proposed")
        self.assertEqual(proposed.metadata["status"], "proposed")
        self.assertEqual(proposed.governance_status, GovernanceStatus.PENDING.value)

        accepted = mark_enrichment_gap_status(self.store, gap.id, "accepted", decided_by="operator")
        self.assertEqual(accepted.metadata["status"], "accepted")
        self.assertEqual(accepted.governance_status, GovernanceStatus.APPROVED.value)
        self.assertFalse(accepted.metadata["execution_allowed"])
        self.assertNotEqual(accepted.metadata["status"], "implemented")

    def test_reasoning_engine_and_store_keep_eval_measurement_only_and_registry_unused(self):
        gap = create_enrichment_gap_record(
            self.store,
            name="Legibility translation gap",
            description="Internal reasoning traces need better operator-legible translation.",
            source_eval="legibility_review_v1",
            category="legibility_translation",
            current_path="eval -> gap graph -> internal_reasoning_graph",
            failure_mode="opaque_reasoning_trace",
            missing_skill="operator-legible translation",
            target_substrate="internal_reasoning_graph",
            proposed_enrichment="Add explicit legibility translation summaries to gap records",
            legibility_summary="The eval is only the measurement source; lifecycle stays in internal_reasoning_graph.",
            evidence_refs=["eval:legibility_review_v1#trace-2"],
            confidence=0.83,
        )
        links = link_enrichment_gap_to_graph(self.store, gap.id)

        engine = ReasoningEngine(self.store)
        proposals = engine.generate_proposals_from_gaps()

        self.assertEqual(len(proposals), 1)
        self.assertEqual(proposals[0].proposal_type, "legibility_translation")
        self.assertEqual(proposals[0].required_governance, "operator_review")

        valid, reason = engine.validate_proposal_governance(proposals[0])
        self.assertTrue(valid, reason)

        proposal_node = self.store.load_node(links["proposed_enrichment_node_id"], include_edges=True)
        self.assertIsNotNone(proposal_node)
        self.assertEqual(proposal_node.governance_status, GovernanceStatus.PENDING.value)
        self.assertEqual(gap.metadata["source_eval"], "legibility_review_v1")
        self.assertEqual(gap.metadata["target_substrate"], "internal_reasoning_graph")
        self.assertIsNone(self.store.find_node_by_name("capability_registry"))
        self.assertIsNone(self.store.find_node_by_name("legibility_review_v1"))


if __name__ == "__main__":
    unittest.main()
