"""
WESLR Graph Response Expansion V1 — Tests

Run:
    PYTHONPATH=. python3 weslr/tests/test_graph_response_expansion_v1.py

Verdict label: WESLR_GRAPH_RESPONSE_EXPANSION_V1_DEFINED
"""

import hashlib
import os
import unittest

from weslr.omnichat.response_expander import (
    expand_response,
    _expand_graph_context,
    MAX_DISPLAY_CONNECTIONS,
    _GRAPH_SUMMARY_NOTE,
)
from weslr.omnichat.context_selector import (
    select_context_for_graph_query,
    SOURCE_REFS,
)
from weslr.multi_graph_traversal import (
    PROPOSAL_TRACE_FILE,
    IMPLEMENTATION_PLANS_FILE,
    DIAGNOSTIC_RECORDS_FILE,
)


class TestGraphSummaryAddition(unittest.TestCase):
    """T1: valid graph context adds graph_summary."""

    def test_t1_graph_summary_added(self):
        root = {"id": "test-root", "type": "proposal"}
        bundle = select_context_for_graph_query(root, mode="private_dev")
        response = {
            "response_text": "Test response.",
            "_selected_context": {
                "context_type": "graph",
                "truth_status": "structured_truth",
                "mode": "private_dev",
                "source_refs": list(bundle.source_refs),
                "graph_context": {
                    "root": bundle.graph_context.root,
                    "connections": [
                        {"type": c.type, "id": c.id, "relation": c.relation, "depth": c.depth}
                        for c in bundle.graph_context.connections
                    ],
                    "truncated": bundle.graph_context.truncated,
                },
            },
        }
        policy = {"final_response_type": "deterministic", "path": "test"}
        result = expand_response(response, policy, "test message")

        self.assertIn("expanded_response", result)
        self.assertIn("graph_summary", result["expanded_response"])

        gs = result["expanded_response"]["graph_summary"]
        self.assertIn("root_id", gs)
        self.assertIn("connection_count", gs)
        self.assertIn("connections", gs)
        self.assertIn("truncated", gs)
        self.assertIn("display_truncated", gs)

    def test_t1_no_graph_context_no_summary(self):
        response = {"response_text": "No context.", "_selected_context": None}
        policy = {"final_response_type": "deterministic", "path": "test"}
        result = expand_response(response, policy, "test")

        self.assertNotIn("graph_summary", result.get("expanded_response", {}))


class TestDisplayLimit(unittest.TestCase):
    """T2: max 5 displayed connections. T3: display_truncated."""

    def test_t2_max_5_connections(self):
        # Build a graph context with 10 connections
        many_connections = [
            {"type": "plan", "id": f"plan-{i}", "relation": f"rel-{i}", "depth": 1}
            for i in range(10)
        ]
        response = {
            "response_text": "Test.",
            "_selected_context": {
                "context_type": "graph",
                "graph_context": {
                    "root": {"id": "root"},
                    "connections": many_connections,
                    "truncated": True,
                },
            },
        }
        expanded: dict = {}
        _expand_graph_context(response, expanded)

        gs = expanded["graph_summary"]
        self.assertEqual(len(gs["connections"]), MAX_DISPLAY_CONNECTIONS)
        self.assertTrue(gs["display_truncated"])
        self.assertTrue(gs["truncated"])

    def test_t3_first_5_only(self):
        connections = [
            {"type": "diagnostic", "id": f"diag-{i}", "relation": f"rel-{i}", "depth": 1}
            for i in range(7)
        ]
        response = {"response_text": "Test.", "_selected_context": {
            "context_type": "graph",
            "graph_context": {"root": {"id": "x"}, "connections": connections, "truncated": False},
        }}
        expanded: dict = {}
        _expand_graph_context(response, expanded)

        displayed_ids = [c["id"] for c in expanded["graph_summary"]["connections"]]
        self.assertEqual(len(displayed_ids), 5)
        self.assertTrue(displayed_ids[0] == "diag-0")
        self.assertTrue(displayed_ids[4] == "diag-4")
        self.assertNotIn("diag-5", displayed_ids)
        self.assertTrue(expanded["graph_summary"]["display_truncated"])

    def test_t3_under_limit_no_truncation(self):
        connections = [
            {"type": "proposal", "id": f"prop-{i}", "relation": f"rel-{i}", "depth": 2}
            for i in range(3)
        ]
        response = {"response_text": "Test.", "_selected_context": {
            "context_type": "graph",
            "graph_context": {"root": {"id": "x"}, "connections": connections, "truncated": False},
        }}
        expanded: dict = {}
        _expand_graph_context(response, expanded)

        gs = expanded["graph_summary"]
        self.assertEqual(len(gs["connections"]), 3)
        self.assertFalse(gs["display_truncated"])


class TestNoRawPathsExposed(unittest.TestCase):
    """T4: no raw JSONL paths exposed."""

    def test_t4_no_raw_paths_in_summary(self):
        root = {"id": "test", "type": "proposal"}
        bundle = select_context_for_graph_query(root)
        response = {
            "response_text": "Test.",
            "_selected_context": {
                "context_type": "graph",
                "source_refs": list(bundle.source_refs),
                "graph_context": {
                    "root": {"id": "test"},
                    "connections": [
                        {"type": "plan", "id": "p1", "relation": "test", "depth": 1}
                    ],
                    "truncated": False,
                },
            },
        }
        policy = {"final_response_type": "deterministic", "path": "test"}
        result = expand_response(response, policy, "test")

        import json
        result_str = json.dumps(result)

        # graph_summary must not contain raw filesystem paths
        gs = result["expanded_response"]["graph_summary"]
        gs_str = json.dumps(gs)
        self.assertNotIn("/data/", gs_str)
        self.assertNotIn(".openclaw", gs_str)
        # source_refs labels (source_trace.jsonl etc.) are allowed in _selected_context
        # but graph_summary itself must not reveal internal paths
        self.assertNotIn("weslr/", gs_str)
        self.assertNotIn("\\", gs_str)

        # Ensure source_refs are label-only in the context (not full paths)
        for ref in result["_selected_context"]["source_refs"]:
            self.assertNotIn("/", ref)  # just the label, no slash


class TestMalformedContextSafety(unittest.TestCase):
    """T5: malformed context does not crash."""

    def test_t5_none_context(self):
        response = {"response_text": "Test.", "_selected_context": None}
        expanded: dict = {}
        _expand_graph_context(response, expanded)
        self.assertEqual(expanded, {})

    def test_t5_wrong_type(self):
        response = {"response_text": "Test.", "_selected_context": {
            "context_type": "governance",
        }}
        expanded: dict = {}
        _expand_graph_context(response, expanded)
        self.assertEqual(expanded, {})

    def test_t5_missing_graph_context_key(self):
        response = {"response_text": "Test.", "_selected_context": {
            "context_type": "graph",
            # graph_context missing
        }}
        expanded: dict = {}
        _expand_graph_context(response, expanded)
        # Should set count=0, not crash
        self.assertEqual(expanded.get("graph_summary", {}).get("connection_count"), 0)

    def test_t5_empty_string_context_type(self):
        response = {"response_text": "Test.", "_selected_context": {
            "context_type": "",
            "graph_context": {},
        }}
        expanded: dict = {}
        _expand_graph_context(response, expanded)
        self.assertEqual(expanded, {})

    def test_t5_corrupted_selected_context(self):
        response = {"response_text": "Test.", "_selected_context": "not-a-dict"}
        expanded: dict = {}
        _expand_graph_context(response, expanded)
        self.assertEqual(expanded, {})


class TestEmptyGraphContext(unittest.TestCase):
    """T6: empty graph context adds count 0."""

    def test_t6_empty_connections_count_zero(self):
        response = {"response_text": "Test.", "_selected_context": {
            "context_type": "graph",
            "graph_context": {
                "root": {"id": "empty-root"},
                "connections": [],
                "truncated": False,
            },
        }}
        expanded: dict = {}
        _expand_graph_context(response, expanded)

        gs = expanded["graph_summary"]
        self.assertEqual(gs["connection_count"], 0)
        self.assertEqual(gs["connections"], [])
        self.assertFalse(gs["truncated"])
        self.assertFalse(gs["display_truncated"])

    def test_t6_empty_no_text_append(self):
        response = {"response_text": "Test response.", "_selected_context": {
            "context_type": "graph",
            "graph_context": {"root": {"id": "x"}, "connections": [], "truncated": False},
        }}
        expanded: dict = {}
        _expand_graph_context(response, expanded)

        # Note should NOT be appended when connections is empty
        self.assertNotIn(_GRAPH_SUMMARY_NOTE, response.get("response_text", ""))


class TestResponseTextAppend(unittest.TestCase):
    """T7: response_text append happens once."""

    def test_t7_append_once(self):
        response = {"response_text": "Original text.", "_selected_context": {
            "context_type": "graph",
            "graph_context": {
                "root": {"id": "x"},
                "connections": [{"type": "plan", "id": "p1", "relation": "rel", "depth": 1}],
                "truncated": False,
            },
        }}
        expanded: dict = {}
        _expand_graph_context(response, expanded)

        text = response["response_text"]
        count = text.count(_GRAPH_SUMMARY_NOTE)
        self.assertEqual(count, 1)

    def test_t7_idempotent(self):
        response = {"response_text": "Original.", "_selected_context": {
            "context_type": "graph",
            "graph_context": {
                "root": {"id": "x"},
                "connections": [{"type": "plan", "id": "p1", "relation": "rel", "depth": 1}],
                "truncated": False,
            },
        }}
        expanded1: dict = {}
        expanded2: dict = {}
        _expand_graph_context(response, expanded1)
        _expand_graph_context(response, expanded2)

        text = response["response_text"]
        self.assertEqual(text.count(_GRAPH_SUMMARY_NOTE), 1)

    def test_t7_no_append_without_response_text(self):
        response = {"response_text": None, "_selected_context": {
            "context_type": "graph",
            "graph_context": {
                "root": {"id": "x"},
                "connections": [{"type": "plan", "id": "p1", "relation": "rel", "depth": 1}],
                "truncated": False,
            },
        }}
        expanded: dict = {}
        _expand_graph_context(response, expanded)
        # Should not crash, text stays None
        self.assertIsNone(response.get("response_text"))


class TestNoWriteProof(unittest.TestCase):
    """T8: no-write proof."""

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

    def test_t8_no_write_proof(self):
        before = self._get_hashes()
        root = {"id": "no-write-test", "type": "proposal"}
        bundle = select_context_for_graph_query(root)

        response = {
            "response_text": "Test.",
            "_selected_context": {
                "context_type": "graph",
                "graph_context": {
                    "root": bundle.graph_context.root,
                    "connections": [
                        {"type": c.type, "id": c.id, "relation": c.relation, "depth": c.depth}
                        for c in bundle.graph_context.connections
                    ],
                    "truncated": bundle.graph_context.truncated,
                },
            },
        }
        policy = {"final_response_type": "deterministic", "path": "test"}
        expand_response(response, policy, "test")

        after = self._get_hashes()
        self.assertEqual(before, after)

    def test_t8_repeated_expansion_no_write(self):
        hashes_before = self._get_hashes()
        for i in range(3):
            root = {"id": f"iter-{i}", "type": "proposal"}
            bundle = select_context_for_graph_query(root)
            response = {
                "response_text": "Test.",
                "_selected_context": {
                    "context_type": "graph",
                    "graph_context": {
                        "root": bundle.graph_context.root,
                        "connections": [
                            {"type": c.type, "id": c.id, "relation": c.relation, "depth": c.depth}
                            for c in bundle.graph_context.connections
                        ],
                        "truncated": bundle.graph_context.truncated,
                    },
                },
            }
            policy = {"final_response_type": "deterministic", "path": "test"}
            expand_response(response, policy, f"msg-{i}")

        hashes_after = self._get_hashes()
        self.assertEqual(hashes_before, hashes_after)


if __name__ == "__main__":
    unittest.main(verbosity=2)