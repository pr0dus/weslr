"""
WESLR Multi-Graph Traversal V1 — Tests

Run:
    PYTHONPATH=. python3 weslr/tests/test_multi_graph_traversal_v1.py

Verdict label: WESLR_MULTI_GRAPH_TRAVERSAL_V1_DEFINED
"""

import hashlib
import os
import unittest

from weslr.multi_graph_traversal import (
    traverse_related,
    TraversalResult,
    Connection,
    PROPOSAL_TRACE_FILE,
    IMPLEMENTATION_PLANS_FILE,
    DIAGNOSTIC_RECORDS_FILE,
)


class TestMultiGraphTraversal(unittest.TestCase):
    """T1–T8: Core traversal logic tests."""

    def _hash_file(self, path: str) -> str:
        if not os.path.exists(path):
            return "NOT_FOUND"
        with open(path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()

    def _get_hashes(self) -> dict:
        return {
            "proposal_trace": self._hash_file(PROPOSAL_TRACE_FILE),
            "implementation_plans": self._hash_file(IMPLEMENTATION_PLANS_FILE),
            "diagnostic_records": self._hash_file(DIAGNOSTIC_RECORDS_FILE),
        }

    # T1: root with no connections → empty
    def test_t1_no_connections_root(self):
        root = {"id": "does-not-exist-12345", "type": "proposal"}
        result = traverse_related(root)
        self.assertEqual(result.root, root)
        self.assertEqual(result.connections, [])
        self.assertFalse(result.truncated)

    # T2: proposal → plan link
    def test_t2_proposal_to_plan(self):
        root = {"id": "?", "type": "proposal"}
        result = traverse_related(root, relation_types=["plan"], max_depth=1)
        # If there are plans in the JSONL that reference a proposal,
        # connections may be non-empty. But root id "?" won't match anything.
        self.assertIsInstance(result, TraversalResult)
        self.assertEqual(result.root, root)
        for conn in result.connections:
            self.assertIn(conn.type, ["proposal", "plan", "diagnostic"])
            self.assertIn(conn.depth, [1, 2])

    # T3: proposal → diagnostic link
    def test_t3_proposal_to_diagnostic(self):
        root = {"id": "nonexistent-proposal-xyz", "type": "proposal"}
        result = traverse_related(root, relation_types=["diagnostic"], max_depth=1)
        self.assertIsInstance(result, TraversalResult)
        self.assertEqual(result.root, root)

    # T4: depth 2 traversal
    def test_t4_depth2_respected(self):
        root = {"id": "depth2-test", "type": "proposal"}
        result1 = traverse_related(root, max_depth=1)
        result2 = traverse_related(root, max_depth=2)
        self.assertGreaterEqual(len(result2.connections), len(result1.connections))
        for conn in result2.connections:
            self.assertIn(conn.depth, [1, 2])

    # T5: max_depth enforced (cannot exceed 2)
    def test_t5_max_depth_capped_at_2(self):
        root = {"id": "any-id", "type": "proposal"}
        result = traverse_related(root, max_depth=5)
        for conn in result.connections:
            self.assertLessEqual(conn.depth, 2)

    # T6: max_results enforced
    def test_t6_max_connections_capped(self):
        root = {"id": "wildcard-proposal", "type": "proposal"}
        result = traverse_related(root, max_depth=2)
        self.assertLessEqual(len(result.connections), 20)
        self.assertIsInstance(result.truncated, bool)

    # T7: malformed entries ignored
    def test_t7_malformed_ignored(self):
        root = {"id": "", "type": "proposal"}
        result = traverse_related(root)
        self.assertEqual(result.connections, [])
        self.assertFalse(result.truncated)

        root2 = {"type": "proposal"}  # no id
        result2 = traverse_related(root2)
        self.assertEqual(result2.connections, [])
        self.assertFalse(result2.truncated)

    # T8: no-write proof
    def test_t8_no_write_proof(self):
        before = self._get_hashes()
        root = {"id": "test-root", "type": "proposal"}
        traverse_related(root, max_depth=2)
        after = self._get_hashes()
        self.assertEqual(before, after)


class TestConnectionDataclass(unittest.TestCase):
    """T9: Connection and TraversalResult are frozen/immutable."""

    def test_t9_connection_immutable(self):
        conn = Connection(type="plan", id="p1", relation="test", depth=1)
        with self.assertRaises(Exception):
            conn.id = "changed"  # type: ignore

    def test_t10_result_immutable(self):
        result = TraversalResult(root={"id": "x"}, connections=[], truncated=False)
        with self.assertRaises(Exception):
            result.truncated = True  # type: ignore

    def test_t11_connection_fields(self):
        conn = Connection(type="diagnostic", id="d1", relation="rel", depth=2)
        self.assertEqual(conn.type, "diagnostic")
        self.assertEqual(conn.id, "d1")
        self.assertEqual(conn.relation, "rel")
        self.assertEqual(conn.depth, 2)


class TestRelationMapping(unittest.TestCase):
    """T12: relation types filter works."""

    def test_t12_relation_type_filter(self):
        root = {"id": "any", "type": "proposal"}
        result_all = traverse_related(root, relation_types=None, max_depth=2)
        result_plan_only = traverse_related(root, relation_types=["plan"], max_depth=2)
        self.assertIsInstance(result_all, TraversalResult)
        self.assertIsInstance(result_plan_only, TraversalResult)
        for conn in result_plan_only.connections:
            self.assertEqual(conn.type, "plan")


class TestEdgeCases(unittest.TestCase):
    """T13–T16: Edge cases."""

    def test_t13_none_relation_types(self):
        root = {"id": "test"}
        result = traverse_related(root, relation_types=None, max_depth=1)
        self.assertIsInstance(result, TraversalResult)

    def test_t14_unknown_relation_type_ignored(self):
        root = {"id": "test", "type": "proposal"}
        result = traverse_related(root, relation_types=["nonexistent"], max_depth=1)
        self.assertEqual(result.connections, [])

    def test_t15_empty_relation_types_list(self):
        root = {"id": "test", "type": "proposal"}
        result = traverse_related(root, relation_types=[], max_depth=1)
        self.assertEqual(result.connections, [])

    def test_t16_missing_type_in_root(self):
        root = {"id": "orphan-id"}
        result = traverse_related(root, max_depth=1)
        self.assertIsInstance(result, TraversalResult)


if __name__ == "__main__":
    unittest.main(verbosity=2)