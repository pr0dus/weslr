"""
WESLR Graph Context Selector V1 — Tests

Run:
    PYTHONPATH=. python3 weslr/tests/test_context_selector_graph_v1.py

Verdict label: WESLR_GRAPH_CONTEXT_SELECTOR_V1_DEFINED
"""

import hashlib
import os
import unittest

from weslr.omnichat.context_selector import (
    select_context_for_graph_query,
    select_context_for_graph_query_dict,
    GraphContextBundle,
    GraphContext,
    SOURCE_REFS,
    MODULE_MAX_DEPTH,
    MAX_CONNECTIONS,
    VALID_MODES,
)
from weslr.multi_graph_traversal import (
    traverse_related,
    TraversalResult,
    PROPOSAL_TRACE_FILE,
    IMPLEMENTATION_PLANS_FILE,
    DIAGNOSTIC_RECORDS_FILE,
)


class TestContextSchema(unittest.TestCase):
    """T1: context bundle schema valid."""

    def test_t1_schema_valid(self):
        root = {"id": "test-root", "type": "proposal"}
        result = select_context_for_graph_query(root, mode="private_dev")

        self.assertIsInstance(result, GraphContextBundle)
        self.assertEqual(result.context_type, "graph")
        self.assertEqual(result.truth_status, "structured_truth")
        self.assertIn(result.mode, VALID_MODES)
        self.assertEqual(result.scope, "minimal")
        self.assertIsInstance(result.allowed_for_llm, bool)
        self.assertIsInstance(result.expires_after_turn, bool)
        self.assertIsInstance(result.source_refs, tuple)
        self.assertIsInstance(result.selection_reason, str)
        self.assertIsInstance(result.graph_context, GraphContext)

    def test_t1_dict_output_schema(self):
        root = {"id": "test-root", "type": "proposal"}
        result = select_context_for_graph_query_dict(root, mode="private_dev")

        self.assertIsInstance(result, dict)
        required_keys = [
            "context_type", "truth_status", "mode", "scope",
            "allowed_for_llm", "expires_after_turn", "source_refs",
            "selection_reason", "graph_context",
        ]
        for key in required_keys:
            self.assertIn(key, result, f"Missing key: {key}")

        gc = result["graph_context"]
        self.assertIn("root", gc)
        self.assertIn("connections", gc)
        self.assertIn("truncated", gc)


class TestGraphContextIntegration(unittest.TestCase):
    """T2: graph context includes traversal result."""

    def test_t2_includes_traversal_result(self):
        root = {"id": "test-id", "type": "proposal"}
        result = select_context_for_graph_query(root, relation_types=["plan", "diagnostic"])

        self.assertIsInstance(result.graph_context, GraphContext)
        self.assertIsInstance(result.graph_context.root, dict)
        self.assertIn("id", result.graph_context.root)
        self.assertIsInstance(result.graph_context.connections, tuple)
        self.assertIsInstance(result.graph_context.truncated, bool)

    def test_t2_dict_graph_context_fields(self):
        root = {"id": "another-id", "type": "plan"}
        result = select_context_for_graph_query_dict(root, mode="private_dev")

        gc = result["graph_context"]
        self.assertIsInstance(gc["root"], dict)
        self.assertIsInstance(gc["connections"], list)
        self.assertIsInstance(gc["truncated"], bool)
        for conn in gc["connections"]:
            self.assertIn("type", conn)
            self.assertIn("id", conn)
            self.assertIn("relation", conn)
            self.assertIn("depth", conn)


class TestMaxDepthClamp(unittest.TestCase):
    """T3: max_depth clamped to 2."""

    def test_t3_depth_clamped_to_2(self):
        root = {"id": "depth-test", "type": "proposal"}
        result = select_context_for_graph_query(root, max_depth=99)

        # All connection depths must be <= 2
        for conn in result.graph_context.connections:
            self.assertLessEqual(conn.depth, 2)

    def test_t3_depth_clamped_exactly_at_2(self):
        root = {"id": "depth-test", "type": "proposal"}
        result = select_context_for_graph_query(root, max_depth=2)

        for conn in result.graph_context.connections:
            self.assertLessEqual(conn.depth, MODULE_MAX_DEPTH)

    def test_t3_depth_1_works(self):
        root = {"id": "depth1-test", "type": "proposal"}
        result = select_context_for_graph_query(root, max_depth=1)

        for conn in result.graph_context.connections:
            self.assertEqual(conn.depth, 1)


class TestPublicMode(unittest.TestCase):
    """T4: public_demo_readonly allowed_for_llm false."""

    def test_t4_public_mode_llm_false(self):
        root = {"id": "test", "type": "proposal"}
        result = select_context_for_graph_query(root, mode="public_demo_readonly")
        self.assertFalse(result.allowed_for_llm)

    def test_t4_private_dev_llm_false(self):
        root = {"id": "test", "type": "proposal"}
        result = select_context_for_graph_query(root, mode="private_dev")
        self.assertFalse(result.allowed_for_llm)

    def test_t4_all_modes_llm_false_v1(self):
        for mode in VALID_MODES:
            root = {"id": f"test-{mode}", "type": "proposal"}
            result = select_context_for_graph_query(root, mode=mode)
            self.assertFalse(result.allowed_for_llm)


class TestMalformedRoot(unittest.TestCase):
    """T5: malformed root returns empty connections."""

    def test_t5_empty_id(self):
        root = {"id": "", "type": "proposal"}
        result = select_context_for_graph_query(root)
        self.assertEqual(result.graph_context.connections, ())

    def test_t5_no_id_key(self):
        root = {"type": "proposal", "data": "value"}
        result = select_context_for_graph_query(root)
        self.assertEqual(result.graph_context.connections, ())

    def test_t5_wrong_type(self):
        root = "not-a-dict"
        result = select_context_for_graph_query(root)
        self.assertEqual(result.graph_context.connections, ())

    def test_t5_none_root(self):
        result = select_context_for_graph_query(None)
        self.assertEqual(result.graph_context.connections, ())

    def test_t5_dict_with_empty_id_string(self):
        root = {"id": "   ", "type": "proposal"}
        result = select_context_for_graph_query(root)
        self.assertEqual(len(result.graph_context.connections), 0)


class TestSourceRefsLabelsOnly(unittest.TestCase):
    """T6: source_refs labels only, no raw paths."""

    def test_t6_labels_no_file_extensions(self):
        root = {"id": "test", "type": "proposal"}
        result = select_context_for_graph_query(root)

        for ref in result.source_refs:
            # No raw filesystem paths
            self.assertNotIn("/data/", ref)
            self.assertNotIn("\\", ref)
            # No internal paths
            self.assertNotIn(".openclaw", ref)
            self.assertNotIn("weslr/", ref)
            # Only the known labels
            self.assertIn(ref, SOURCE_REFS)

    def test_t6_dict_output_labels_only(self):
        root = {"id": "test", "type": "diagnostic"}
        result = select_context_for_graph_query_dict(root)

        for ref in result["source_refs"]:
            self.assertNotIn("/data/", ref)
            self.assertNotIn("\\", ref)


class TestNoWriteProof(unittest.TestCase):
    """T7: no-write proof."""

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

    def test_t7_no_write_proof(self):
        before = self._get_hashes()
        root = {"id": "no-write-test", "type": "proposal"}
        select_context_for_graph_query(root, max_depth=2)
        after = self._get_hashes()
        self.assertEqual(before, after)

    def test_t7_repeated_calls_no_write(self):
        hashes_before = self._get_hashes()
        for i in range(5):
            root = {"id": f"iter-{i}", "type": "proposal"}
            select_context_for_graph_query(root, max_depth=2)
        hashes_after = self._get_hashes()
        self.assertEqual(hashes_before, hashes_after)


class TestRelationFilter(unittest.TestCase):
    """T8: relation filter respected."""

    def test_t8_plan_only_filter(self):
        root = {"id": "test", "type": "proposal"}
        result = select_context_for_graph_query(
            root,
            relation_types=["plan"],
            max_depth=2,
        )
        for conn in result.graph_context.connections:
            self.assertEqual(conn.type, "plan")

    def test_t8_diagnostic_only_filter(self):
        root = {"id": "test", "type": "proposal"}
        result = select_context_for_graph_query(
            root,
            relation_types=["diagnostic"],
            max_depth=1,
        )
        for conn in result.graph_context.connections:
            self.assertEqual(conn.type, "diagnostic")

    def test_t8_unknown_filter_ignored(self):
        root = {"id": "test", "type": "proposal"}
        result = select_context_for_graph_query(
            root,
            relation_types=["nonexistent_type"],
            max_depth=1,
        )
        self.assertEqual(len(result.graph_context.connections), 0)

    def test_t8_empty_filter_returns_empty(self):
        root = {"id": "test", "type": "proposal"}
        result = select_context_for_graph_query(
            root,
            relation_types=[],
            max_depth=1,
        )
        self.assertEqual(len(result.graph_context.connections), 0)


class TestBundleImmutability(unittest.TestCase):
    """T9: bundle is frozen/immutable."""

    def test_t9_bundle_immutable(self):
        root = {"id": "test", "type": "proposal"}
        bundle = select_context_for_graph_query(root)
        with self.assertRaises(Exception):
            bundle.mode = "changed"  # type: ignore

    def test_t9_graph_context_immutable(self):
        root = {"id": "test", "type": "proposal"}
        bundle = select_context_for_graph_query(root)
        with self.assertRaises(Exception):
            bundle.graph_context.truncated = True  # type: ignore


class TestTruncationFlag(unittest.TestCase):
    """T10: truncated flag correctly set."""

    def test_t10_truncated_false_when_empty(self):
        root = {"id": "nonexistent-id-12345", "type": "proposal"}
        result = select_context_for_graph_query(root, max_depth=2)
        self.assertFalse(result.graph_context.truncated)

    def test_t10_truncated_reflected_in_dict(self):
        root = {"id": "test", "type": "proposal"}
        result = select_context_for_graph_query_dict(root)
        self.assertIn("truncated", result["graph_context"])
        self.assertIsInstance(result["graph_context"]["truncated"], bool)


if __name__ == "__main__":
    unittest.main(verbosity=2)