"""
weslr/tests/test_collaboration.py
==================================
Phase 10 — Collaboration & Workspace tests (minimum 20).

Tests:
  - Workspace manager: share, library list, import
  - Jupyter stub: run_in_notebook returns structured output
  - Explanation generator: templates include title, confidence, evidence
  - Commands parse correctly
  - Cross-tenant isolation: Tenant A cannot see Tenant B's private hypotheses

Author: OCC (WESLR governed intelligence) — Phase 10
"""

import asyncio
import sys
import unittest

# Ensure modules are importable
sys.path.insert(0, str(__file__).rsplit("/tests/", 1)[0])

from weslr.modules.workspace import (
    WorkspaceManager,
    SHARED_HYPOTHESES,
    _make_shared_id,
    _anonymize_hypothesis,
    SharedHypothesis,
)
from weslr.modules.hypothesis_repository import (
    Hypothesis,
    HypothesisRepository,
    set_tenant_getter,
    get_current_tenant_id,
)
from weslr.modules.explanation_generator import (
    explain_hypothesis,
    explain_causal_link,
    explain_abduction,
    explain_hypothesis_dict,
)
from weslr.commands.collaboration_commands import (
    handle_workspace_command,
    handle_jupyter_command,
    handle_explain_command,
    handle_collaboration_command,
)


# ── Fixtures ─────────────────────────────────────────────────────────────────

def _make_hypothesis(title="Test hypothesis", domain="discovery", confidence=0.75) -> Hypothesis:
    return Hypothesis(
        title=title,
        description=f"Description for {title}",
        domain=domain,
        confidence=confidence,
        provenance=[{"source": "test", "action": "test_creation", "parameters": {}}],
        metadata={"evidence": [{"key": "test_ev", "value": 42}]},
    )


def _reset_shared_library():
    SHARED_HYPOTHESES.clear()


# ── Workspace Manager Tests ──────────────────────────────────────────────────

class TestWorkspaceManager(unittest.TestCase):

    def setUp(self):
        set_tenant_getter(lambda: "tenant_a")
        self.repo_a = HypothesisRepository()
        set_tenant_getter(lambda: "tenant_b")
        self.repo_b = HypothesisRepository()
        _reset_shared_library()

    def tearDown(self):
        set_tenant_getter(lambda: "default")

    def test_share_hypothesis_adds_to_shared_library(self):
        set_tenant_getter(lambda: "tenant_a")
        h = _make_hypothesis("Dose-response relationship")
        self.repo_a.add(h)
        ws = WorkspaceManager("tenant_a")
        shared_id = ws.share_hypothesis(h)
        self.assertIn(shared_id, SHARED_HYPOTHESES)
        self.assertEqual(SHARED_HYPOTHESES[shared_id]["title"], "Dose-response relationship")

    def test_share_hypothesis_returns_library_id(self):
        h = _make_hypothesis("PK hypothesis")
        self.repo_a.add(h)
        ws = WorkspaceManager("tenant_a")
        sid = ws.share_hypothesis(h)
        self.assertTrue(len(sid) > 20)
        self.assertTrue(sid.startswith("shared:") or len(sid) == 36)  # UUID

    def test_shared_library_contains_anonymized_version(self):
        h = _make_hypothesis("Enzyme kinetics")
        h.provenance.append({"source": "tenant_a", "action": "manual_creation", "notes": "private user note"})
        self.repo_a.add(h)
        ws = WorkspaceManager("tenant_a")
        ws.share_hypothesis(h)
        # Check anonymization: no tenant_a identifiers in shared entry
        for entry in SHARED_HYPOTHESES.values():
            self.assertNotIn("tenant_a", str(entry))
            self.assertIn("title", entry)
            self.assertIn("confidence", entry)
            self.assertIn("domain", entry)

    def test_list_shared_library_empty(self):
        _reset_shared_library()
        ws = WorkspaceManager("tenant_a")
        result = ws.list_shared_library()
        self.assertEqual(result, [])

    def test_list_shared_library_returns_all_tenants(self):
        # Tenant A shares
        set_tenant_getter(lambda: "tenant_a")
        h1 = _make_hypothesis("Hypothesis A", domain="discovery")
        self.repo_a.add(h1)
        ws_a = WorkspaceManager("tenant_a")
        ws_a.share_hypothesis(h1)
        # Tenant B shares
        set_tenant_getter(lambda: "tenant_b")
        h2 = _make_hypothesis("Hypothesis B", domain="causality")
        self.repo_b.add(h2)
        ws_b = WorkspaceManager("tenant_b")
        ws_b.share_hypothesis(h2)
        # Library lists both
        ws_a2 = WorkspaceManager("tenant_a")
        library = ws_a2.list_shared_library()
        self.assertEqual(len(library), 2)

    def test_list_shared_library_domain_filter(self):
        h_disc = _make_hypothesis("Discovery hypothesis", domain="discovery")
        h_caus = _make_hypothesis("Causality hypothesis", domain="causality")
        self.repo_a.add(h_disc)
        self.repo_a.add(h_caus)
        ws = WorkspaceManager("tenant_a")
        ws.share_hypothesis(h_disc)
        ws.share_hypothesis(h_caus)
        disc_only = ws.list_shared_library(domain="discovery")
        self.assertEqual(len(disc_only), 1)
        self.assertEqual(disc_only[0]["domain"], "discovery")

    def test_import_from_library_returns_dict(self):
        h = _make_hypothesis("Importable hypothesis")
        self.repo_a.add(h)
        ws = WorkspaceManager("tenant_a")
        shared_id = ws.share_hypothesis(h)
        # Import as tenant_b
        set_tenant_getter(lambda: "tenant_b")
        ws_b = WorkspaceManager("tenant_b")
        imported = ws_b.import_from_library(shared_id)
        self.assertIsNotNone(imported)
        self.assertEqual(imported["title"], "Importable hypothesis")
        self.assertEqual(imported["status"], "draft")
        self.assertIn("provenance", imported)

    def test_import_from_library_not_found(self):
        ws = WorkspaceManager("tenant_b")
        result = ws.import_from_library("nonexistent-shared-id")
        self.assertIsNone(result)

    def test_import_creates_new_hypothesis_in_repo(self):
        h = _make_hypothesis("To be imported")
        self.repo_a.add(h)
        ws_a = WorkspaceManager("tenant_a")
        shared_id = ws_a.share_hypothesis(h)
        # Import into tenant_b repo
        set_tenant_getter(lambda: "tenant_b")
        ws_b = WorkspaceManager("tenant_b")
        imported = ws_b.import_from_library(shared_id)
        self.assertIsNotNone(imported)
        # Verify it can be stored
        h_new = Hypothesis(
            title=imported["title"],
            description=imported["description"],
            domain=imported.get("domain", "mixed"),
            confidence=imported.get("confidence", 0.5),
            provenance=imported.get("provenance", []),
            metadata=imported.get("metadata", {}),
        )
        stored = self.repo_b.add(h_new)
        self.assertTrue(len(stored.id) > 0)
        self.assertEqual(stored.title, "To be imported")

    def test_cross_tenant_isolation_private_hypothesis_not_shared(self):
        h_private = _make_hypothesis("Private hypothesis")
        self.repo_a.add(h_private)
        # Tenant A does NOT share
        # Tenant B tries to access (via shared library - should not see private)
        library = WorkspaceManager("tenant_b").list_shared_library()
        private_titles = [e["title"] for e in library]
        self.assertNotIn("Private hypothesis", private_titles)

    def test_shared_id_is_deterministic(self):
        h = _make_hypothesis("Deterministic test")
        self.repo_a.add(h)
        sid1 = WorkspaceManager("tenant_a").share_hypothesis(h)
        _reset_shared_library()
        sid2 = WorkspaceManager("tenant_a").share_hypothesis(h)
        self.assertEqual(sid1, sid2)

    def test_shareable_flag_set_in_metadata(self):
        h = _make_hypothesis("Shareable test")
        self.repo_a.add(h)
        ws = WorkspaceManager("tenant_a")
        ws.share_hypothesis(h)
        # The original hypothesis should have shareable metadata
        found = self.repo_a.get(h.id)
        self.assertTrue(found.metadata.get("shareable", False))


# ── Explanation Generator Tests ───────────────────────────────────────────

class TestExplanationGenerator(unittest.TestCase):

    def test_explain_hypothesis_contains_title(self):
        h = Hypothesis(
            title="Dose-response relationship",
            description="Increasing dose raises response",
            domain="pharmacology",
            confidence=0.76,
            metadata={
                "evidence": [
                    {"key": "correlation", "value": "r=0.82"},
                    {"key": "temporal_precedence", "value": "dose before response"},
                ],
                "causal_graph": {("dose", "response"): 0.8},
            },
        )
        result = explain_hypothesis(h)
        self.assertIn("Dose-response relationship", result)
        self.assertIn("76%", result)
        self.assertIn("pharmacology", result)

    def test_explain_hypothesis_contains_confidence(self):
        h = Hypothesis(title="Test", confidence=0.65)
        result = explain_hypothesis(h)
        self.assertIn("65%", result)

    def test_explain_hypothesis_contains_evidence(self):
        h = Hypothesis(
            title="Evidence test",
            metadata={
                "evidence": [
                    {"key": "ev1", "value": 1},
                    {"key": "ev2", "value": 2},
                ]
            },
        )
        result = explain_hypothesis(h)
        self.assertIn("2 piece", result)

    def test_explain_hypothesis_empty_evidence(self):
        h = Hypothesis(title="No evidence", metadata={})
        result = explain_hypothesis(h)
        self.assertIn("No evidence", result)

    def test_explain_hypothesis_with_dict(self):
        d = {
            "title": "Dict hypothesis",
            "description": "A hypothesis from a dict",
            "domain": "discovery",
            "confidence": 0.55,
            "metadata": {},
        }
        result = explain_hypothesis(d)
        self.assertIn("Dict hypothesis", result)

    def test_explain_causal_link(self):
        result = explain_causal_link("dose", "response", 0.82)
        self.assertIn("dose", result)
        self.assertIn("response", result)
        self.assertIn("82%", result)
        self.assertIn("Causal Link", result)

    def test_explain_abduction(self):
        result = explain_abduction(
            observation="Elevated enzyme activity",
            explanation="Gene upregulation",
        )
        self.assertIn("Elevated enzyme activity", result)
        self.assertIn("Gene upregulation", result)

    def test_explain_abduction_with_alternative(self):
        result = explain_abduction(
            observation="Elevated enzyme",
            explanation="Gene upregulation",
            alternative="Post-translational modification",
        )
        self.assertIn("alternative", result.lower())

    def test_explain_hypothesis_suggestion_based_on_domain(self):
        for domain in ("discovery", "causality", "simulation", "spatial", "temporal", "quantum", "mixed"):
            h = Hypothesis(title=f"{domain} test", domain=domain)
            result = explain_hypothesis(h)
            self.assertIn("Suggested next step", result)


# ── Jupyter Stub Tests ───────────────────────────────────────────────────────

class TestJupyterStub(unittest.TestCase):

    def test_run_in_notebook_returns_dict(self):
        from weslr.jupyter_kernel_stub import run_in_notebook
        result = run_in_notebook("/hypothesis list")
        self.assertIsInstance(result, dict)
        self.assertIn("output", result)
        self.assertIn("kernel", result)
        self.assertEqual(result["kernel"], "weslr")

    def test_run_in_notebook_empty_command(self):
        from weslr.jupyter_kernel_stub import run_in_notebook
        result = run_in_notebook("")
        self.assertEqual(result["returncode"], -1)
        self.assertIn("Empty command", result["error"])

    def test_run_in_notebook_has_images_key(self):
        from weslr.jupyter_kernel_stub import run_in_notebook
        result = run_in_notebook("/hypothesis list")
        self.assertIn("images", result)
        self.assertIsInstance(result["images"], list)

    def test_run_in_notebook_command_echoed_back(self):
        from weslr.jupyter_kernel_stub import run_in_notebook
        result = run_in_notebook("/hypothesis list")
        self.assertEqual(result["command"], "/hypothesis list")

    def test_get_connection_info(self):
        from weslr.jupyter_kernel_stub import get_connection_info
        info = get_connection_info()
        self.assertEqual(info["kernel_name"], "weslr")
        self.assertIn("usage", info)

    def test_print_info_returns_string(self):
        from weslr.jupyter_kernel_stub import print_info
        info = print_info()
        self.assertIsInstance(info, str)
        self.assertIn("Jupyter", info)
        self.assertIn("run_in_notebook", info)


# ── Command Handler Tests ────────────────────────────────────────────────────

class TestCollaborationCommands(unittest.TestCase):

    def setUp(self):
        set_tenant_getter(lambda: "test_tenant")
        _reset_shared_library()

    def tearDown(self):
        set_tenant_getter(lambda: "default")

    def test_workspace_help(self):
        async def run():
            result = await handle_workspace_command("/workspace", "workspace")
            self.assertIn("share", result)
            self.assertIn("library list", result)
        asyncio.run(run())

    def test_workspace_share_unknown_hypothesis(self):
        async def run():
            result = await handle_workspace_command(
                "/workspace share unknown-id-123456789012",
                "/workspace share unknown-id-123456789012",
            )
            self.assertIn("not found", result)
        asyncio.run(run())

    def test_workspace_library_list_empty(self):
        _reset_shared_library()
        async def run():
            result = await handle_workspace_command(
                "/workspace library list",
                "/workspace library list",
            )
            self.assertIn("empty", result.lower())
        asyncio.run(run())

    def test_explain_help(self):
        async def run():
            result = await handle_explain_command("/explain", "explain")
            self.assertIn("hypothesis", result)
        asyncio.run(run())

    def test_explain_hypothesis_unknown_id(self):
        async def run():
            result = await handle_explain_command(
                "/explain hypothesis unknown-id-123456789012",
                "/explain hypothesis unknown-id-123456789012",
            )
            self.assertIn("not found", result)
        asyncio.run(run())

    def test_jupyter_info(self):
        async def run():
            result = await handle_jupyter_command("/jupyter info", "/jupyter info")
            self.assertIn("Jupyter", result)
            self.assertIn("run_in_notebook", result)
        asyncio.run(run())

    def test_collaboration_unknown_command_returns_help(self):
        async def run():
            result = await handle_collaboration_command("/unknown-cmd", "/unknown-cmd")
            self.assertIn("workspace", result)
            self.assertIn("jupyter", result)
        asyncio.run(run())

    def test_workspace_share_and_library_roundtrip(self):
        async def run():
            from weslr.commands.hypothesis_commands import handle_hypothesis_command
            create_result = await handle_hypothesis_command(
                "/hypothesis new Roundtrip hypothesis",
                "hypothesis new roundtrip hypothesis",
            )
            self.assertIn("Hypothesis created", create_result)
            import re
            m = re.search(r"Hypothesis created: (\S+)", create_result)
            self.assertIsNotNone(m)
            hid = m.group(1)
            share_result = await handle_workspace_command(
                f"/workspace share {hid}",
                f"/workspace share {hid}",
            )
            self.assertIn("shared", share_result.lower())
            list_result = await handle_workspace_command(
                "/workspace library list",
                "/workspace library list",
            )
            self.assertIn("Roundtrip", list_result)
        asyncio.run(run())


# ── Cross-tenant isolation test ──────────────────────────────────────────────

class TestCrossTenantIsolation(unittest.TestCase):

    def setUp(self):
        _reset_shared_library()

    def tearDown(self):
        set_tenant_getter(lambda: "default")

    def test_tenant_a_private_not_visible_to_tenant_b_via_shared_library(self):
        # Tenant A creates private hypothesis (NOT shared)
        set_tenant_getter(lambda: "tenant_a")
        repo_a = HypothesisRepository()
        h_private = _make_hypothesis("Private for A only")
        repo_a.add(h_private)
        # Tenant B lists shared library - should be empty
        set_tenant_getter(lambda: "tenant_b")
        ws_b = WorkspaceManager("tenant_b")
        library = ws_b.list_shared_library()
        titles = [e["title"] for e in library]
        self.assertNotIn("Private for A only", titles)

    def test_tenant_a_shared_visible_to_tenant_b_via_shared_library(self):
        # Tenant A creates and shares hypothesis
        set_tenant_getter(lambda: "tenant_a")
        repo_a = HypothesisRepository()
        h_shared = _make_hypothesis("Shared from A")
        repo_a.add(h_shared)
        ws_a = WorkspaceManager("tenant_a")
        ws_a.share_hypothesis(h_shared)
        # Tenant B can see it in shared library
        set_tenant_getter(lambda: "tenant_b")
        ws_b = WorkspaceManager("tenant_b")
        library = ws_b.list_shared_library()
        titles = [e["title"] for e in library]
        self.assertIn("Shared from A", titles)


if __name__ == "__main__":
    unittest.main()