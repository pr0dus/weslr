"""test_deterministic_handler_classification.py
Targeted test: pubmed/arxiv handlers are not registered as pure read-only.
Handlers that write evidence packets are classified honestly.
No public behavior changes.
"""
import pytest


class TestHandlerClassification:
    """Verify registry classification is honest about write behavior."""

    def test_pubmed_not_read_only(self):
        """pubmed_search must not be registered read_only=True."""
        from weslr.deterministic_handlers import HANDLER_REGISTRY
        entry = next((h for h in HANDLER_REGISTRY if h["id"] == "pubmed_search"), None)
        assert entry is not None, "pubmed_search handler not found in registry"
        assert entry["read_only"] is False, (
            "pubmed_search is NOT read-only — it writes evidence packets and facts. "
            "Classification must be honest."
        )
        assert ".weslr/external_evidence_packets.jsonl" in entry.get("writes", []), (
            "pubmed_search writes to external_evidence_packets.jsonl"
        )
        assert ".weslr/fact_assertions.jsonl" in entry.get("writes", []), (
            "pubmed_search writes to fact_assertions.jsonl"
        )

    def test_arxiv_not_read_only(self):
        """arxiv_search must not be registered read_only=True."""
        from weslr.deterministic_handlers import HANDLER_REGISTRY
        entry = next((h for h in HANDLER_REGISTRY if h["id"] == "arxiv_search"), None)
        assert entry is not None, "arxiv_search handler not found in registry"
        assert entry["read_only"] is False, (
            "arxiv_search is NOT read-only — it writes evidence packets and facts. "
            "Classification must be honest."
        )
        assert ".weslr/external_evidence_packets.jsonl" in entry.get("writes", []), (
            "arxiv_search writes to external_evidence_packets.jsonl"
        )
        assert ".weslr/fact_assertions.jsonl" in entry.get("writes", []), (
            "arxiv_search writes to fact_assertions.jsonl"
        )

    def test_pubchem_not_read_only(self):
        """pubchem_search must not be registered read_only=True."""
        from weslr.deterministic_handlers import HANDLER_REGISTRY
        entry = next((h for h in HANDLER_REGISTRY if h["id"] == "pubchem_search"), None)
        assert entry is not None, "pubchem_search handler not found in registry"
        assert entry["read_only"] is False, (
            "pubchem_search writes facts to fact_assertions.jsonl — not read-only."
        )
        assert ".weslr/fact_assertions.jsonl" in entry.get("writes", []), (
            "pubchem_search writes to fact_assertions.jsonl"
        )

    def test_no_handler_claims_read_only_but_writes(self):
        """No handler in the registry should claim read_only=True while listing writes."""
        from weslr.deterministic_handlers import HANDLER_REGISTRY

        mismatches = []
        for h in HANDLER_REGISTRY:
            has_writes = bool(h.get("writes"))
            claims_read_only = h.get("read_only") is True
            if has_writes and claims_read_only:
                mismatches.append(h["id"])

        assert not mismatches, (
            f"Handlers claiming read_only=True but having non-empty writes: {mismatches}"
        )

    def test_registry_entries_have_required_fields(self):
        """Every registry entry has the fields needed for dispatch safety decisions."""
        from weslr.deterministic_handlers import HANDLER_REGISTRY

        required = {"id", "read_only", "writes", "write_paths", "side_effects"}
        for h in HANDLER_REGISTRY:
            missing = required - set(h.keys())
            assert not missing, f"Handler {h['id']} missing fields: {missing}"
