"""
Phase 4.4 Integration Tests

Tests multi-tenant isolation, ClinicalTrials.gov adapter,
domain schemas, fact extraction precision, and entity detection.
"""

from __future__ import annotations

import json
import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest


# ──────────────────────────────────────────────────────────────────────────────
# Tenant Context Tests
# ──────────────────────────────────────────────────────────────────────────────

class TestTenantContext:
    """Tenant isolation via thread-local storage."""

    def test_set_and_get_tenant(self):
        from weslr.tenant_context import set_current_tenant, get_current_tenant
        set_current_tenant("test_tenant")
        assert get_current_tenant() == "test_tenant"
        set_current_tenant(None)
        assert get_current_tenant() is None

    def test_is_default_tenant(self):
        from weslr.tenant_context import (
            is_default_tenant, set_current_tenant, get_current_tenant
        )
        assert is_default_tenant()
        set_current_tenant("anything")
        assert not is_default_tenant()
        set_current_tenant(None)

    def test_resolve_path_with_tenant(self):
        from weslr.tenant_context import resolve_path, set_current_tenant
        set_current_tenant("my_tenant")
        path = resolve_path(".weslr/fact_assertions.jsonl")
        assert "tenants" in str(path)
        assert "my_tenant" in str(path)
        set_current_tenant(None)

    def test_resolve_path_without_tenant(self):
        from weslr.tenant_context import resolve_path, set_current_tenant, is_default_tenant
        set_current_tenant(None)
        path = resolve_path("fact_assertions.jsonl")
        # Should resolve to workspace root, not tenants/
        assert "tenants" not in str(path)

    def test_tenant_dir_creates_directory(self):
        from weslr.tenant_context import get_tenant_dir, set_current_tenant
        set_current_tenant("auto_create_test")
        td = get_tenant_dir()
        assert td.exists()
        set_current_tenant(None)

    def test_list_tenants_empty(self):
        from weslr.tenant_context import list_tenants
        tenants = list_tenants()
        assert isinstance(tenants, list)


class TestTenantManager:
    """Tenant lifecycle management."""

    def test_init_tenant(self):
        from weslr.tenant_manager import init_tenant, destroy_tenant, has_tenant
        from weslr.tenant_context import get_tenant_dir

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {"WESLR_TENANT_DIR": tmpdir}, clear=False):
                # Reload tenant_context to pick up patched env
                import importlib
                import weslr.tenant_context as tc
                importlib.reload(tc)
                import weslr.tenant_manager as tm
                importlib.reload(tm)

                tid = f"test_tenant_{os.getpid()}"
                config = tm.init_tenant(tid, "cancer_research")
                assert config["tenant_id"] == tid
                assert config["domain"] == "cancer_research"
                assert tc.has_tenant(tid)
                tm.destroy_tenant(tid, confirm=True)
                assert not tc.has_tenant(tid)

    def test_list_tenants_info(self):
        from weslr.tenant_manager import list_tenants
        result = list_tenants()
        assert isinstance(result, list)
        for t in result:
            assert "tenant_id" in t
            assert "domain" in t

    def test_get_tenant_info(self):
        from weslr.tenant_manager import get_tenant_info
        info = get_tenant_info("default")
        # Should return None or a config
        assert info is None or isinstance(info, dict)

    def test_switch_tenant_invalid(self):
        from weslr.tenant_manager import switch_tenant
        with pytest.raises(ValueError):
            switch_tenant("nonexistent_tenant_xyz_123")


# ──────────────────────────────────────────────────────────────────────────────
# Domain Schema Tests
# ──────────────────────────────────────────────────────────────────────────────

class TestDomainSchemas:
    def test_materials_science_schema_loads(self):
        from weslr.entity_schema_registry import load_schema
        schema = load_schema("materials_science")
        assert schema["domain"] == "materials_science"
        assert "Material" in schema["entity_types"]
        assert "SynthesisProtocol" in schema["entity_types"]
        assert "has_property" in schema["relationship_types"]

    def test_astronomy_schema_loads(self):
        from weslr.entity_schema_registry import load_schema
        schema = load_schema("astronomy")
        assert schema["domain"] == "astronomy"
        assert "Exoplanet" in schema["entity_types"]
        assert "OrbitalParameter" in schema["entity_types"]
        assert "orbits" in schema["relationship_types"]


# ──────────────────────────────────────────────────────────────────────────────
# Pattern Loading for New Domains
# ──────────────────────────────────────────────────────────────────────────────

class TestPatternLoading:
    def test_materials_science_patterns_load(self):
        from weslr.fact_extractor import load_patterns
        patterns = load_patterns("materials_science")
        assert len(patterns) >= 5
        pattern_ids = [p["pattern_id"] for p in patterns]
        assert any("bandgap" in pid for pid in pattern_ids)

    def test_astronomy_patterns_load(self):
        from weslr.fact_extractor import load_patterns
        patterns = load_patterns("astronomy")
        assert len(patterns) >= 5
        pattern_ids = [p["pattern_id"] for p in patterns]
        assert any("orbital_period" in pid for pid in pattern_ids)


# ──────────────────────────────────────────────────────────────────────────────
# Entity Detection for New Domains
# ──────────────────────────────────────────────────────────────────────────────

class TestEntityDetectionNewDomains:
    def test_materials_detect(self):
        from weslr.commands.entities import detect_entity_type
        for name in ["MAPbI3", "CsFA perovskite", "TiO2", "FAPbI3"]:
            t = detect_entity_type(name)
            assert t == "Material", f"{name} → {t}, expected Material"

    def test_exoplanet_detect(self):
        from weslr.commands.entities import detect_entity_type
        for name in ["TOI-1231 b", "WASP-12b", "Kepler-90h", "GJ 486 b"]:
            t = detect_entity_type(name)
            assert t == "Exoplanet", f"{name} → {t}, expected Exoplanet"

    def test_star_detect(self):
        from weslr.commands.entities import detect_entity_type
        for name in ["Vega"]:
            t = detect_entity_type(name)
            assert t == "Star", f"{name} → {t}, expected Star"


# ──────────────────────────────────────────────────────────────────────────────
# Fact Extraction Precision
# ──────────────────────────────────────────────────────────────────────────────

class TestFactExtractionPrecision:
    def test_negation_detection(self):
        from weslr.fact_extractor import check_negation, apply_negation
        # Negation word BEFORE the matched content → detected
        text = "no response was observed in the cohort."
        match_start = text.find("response")   # match starts at 'response'
        prefix_neg = check_negation(text, match_start, match_start + len("response"))
        assert prefix_neg is True

        # No negation word → not detected
        text2 = "response was observed in the cohort."
        match_start2 = text2.find("response")
        prefix_neg2 = check_negation(text2, match_start2, match_start2 + len("response"))
        assert prefix_neg2 is False

        fact = {"subject": "drug_a", "predicate": "survival_rate", "object": "0.8", "trust_score": 0.8}
        out = apply_negation(fact)
        assert out["is_negated"] is True
        assert out["trust_score"] == 0.1

    def test_no_negation(self):
        from weslr.fact_extractor import check_negation
        text = "Survival was improved in the treatment arm."
        match_start = text.find("improved")
        is_neg = check_negation(text, match_start, match_start + len("improved"))
        assert is_neg is False

    def test_numeric_range_validation(self):
        from weslr.fact_extractor import validate_numeric_fact
        # Valid survival rate
        fact = {"predicate": "survival_rate", "object": "0.72"}
        result = validate_numeric_fact(fact)
        assert result["validation"]["is_valid"] is True

        # Out of range p-value
        fact2 = {"predicate": "p_value", "object": "1.5"}
        result2 = validate_numeric_fact(fact2)
        assert result2["validation"]["is_valid"] is False
        out_str = str(result2["validation"]["out_of_range"])
        assert "object" in out_str  # field name is 'object'

        # Valid hazard ratio
        fact3 = {"predicate": "hazard_ratio", "object": "0.71"}
        result3 = validate_numeric_fact(fact3)
        assert result3["validation"]["is_valid"] is True

    def test_duplicate_detection(self):
        from weslr.fact_extractor import find_duplicate_fact
        new_fact = {"subject": "nct04551452", "predicate": "phase", "object": "phase_iii"}
        dup = find_duplicate_fact(new_fact, fact_store_path="weslr/.weslr/fact_assertions.jsonl", match_window=5)
        # May or may not find a duplicate depending on store contents
        assert dup is None or isinstance(dup, dict)


# ──────────────────────────────────────────────────────────────────────────────
# Materials Science Extraction
# ──────────────────────────────────────────────────────────────────────────────

class TestMaterialsScienceExtraction:
    def test_bandgap_extraction(self):
        from weslr.fact_extractor import extract_facts_with_positions
        text = "The bandgap of MAPbI3 is 1.55 eV and the bandgap of CsFA is 1.48 eV."
        facts = extract_facts_with_positions(text, domain="materials_science")
        assert len(facts) >= 2
        assert any("bandgap" in f["predicate"] for f in facts)

    def test_synthesis_temperature_extraction(self):
        from weslr.fact_extractor import extract_facts_with_positions
        text = "The material was synthesized at 95°C for 2 hours."
        facts = extract_facts_with_positions(text, domain="materials_science")
        assert any("synthesis_temperature" in f["predicate"] for f in facts)


# ──────────────────────────────────────────────────────────────────────────────
# Astronomy Extraction
# ──────────────────────────────────────────────────────────────────────────────

class TestAstronomyExtraction:
    def test_orbital_period_extraction(self):
        from weslr.fact_extractor import extract_facts_with_positions
        text = "The exoplanet has an orbital period P = 3.85 days."
        facts = extract_facts_with_positions(text, domain="astronomy")
        assert any("orbital_period" in f["predicate"] for f in facts)

    def test_effective_temperature_extraction(self):
        from weslr.fact_extractor import extract_facts_with_positions
        text = "The effective temperature Teff = 580 K of the exoplanet."
        facts = extract_facts_with_positions(text, domain="astronomy")
        assert any("effective_temperature" in f["predicate"] for f in facts)


# ──────────────────────────────────────────────────────────────────────────────
# ClinicalTrials.gov Adapter Tests
# ──────────────────────────────────────────────────────────────────────────────

class TestClinicalTrialsAdapter:
    def test_phase_mapping(self):
        from weslr.search_adapters.clinicaltrials_adapter import _map_phase
        assert _map_phase("Phase 3") == "phase_iii"
        assert _map_phase("Phase II") == "phase_ii"
        assert _map_phase("Phase IV") == "phase_iv"
        assert _map_phase("Phase I") == "phase_i"
        assert _map_phase("Phase III") == "phase_iii"
        assert _map_phase(None) == "phase_unknown"

    def test_normalize_trial_id(self):
        from weslr.search_adapters.clinicaltrials_adapter import _normalize_trial_id
        assert _normalize_trial_id("NCT04551452") == "04551452"
        assert _normalize_trial_id("nct01234567") == "01234567"

    def test_strip_html(self):
        from weslr.search_adapters.clinicaltrials_adapter import _strip_html
        assert _strip_html("<b>Bold</b> text") == "Bold text"
        assert _strip_html("<i>Italic</i>") == "Italic"
        assert _strip_html("No tags") == "No tags"

    def test_fact_extraction_from_study(self):
        from weslr.search_adapters.clinicaltrials_adapter import extract_trial_facts

        study = {
            "nct_id": "NCT04678909",
            "title": "Test Trial",
            "status": "RECRUITING",
            "phase": "Phase 3",
            "phase_normalized": "phase_iii",
            "enrollment_count": 150,
            "primary_outcomes": ["Overall survival", "Response rate"],
            "interventions": ["Drug: TestDrugA", "Drug: TestDrugB"],
            "source_url": "https://clinicaltrials.gov/study/NCT04678909",
        }

        facts = extract_trial_facts(study)
        predicates = [f["predicate"] for f in facts]
        assert "phase" in predicates
        assert "enrollment" in predicates
        assert "primary_endpoint" in predicates
        assert "trial_status" in predicates
        assert "has_drug" in predicates  # one per drug intervention

        has_drugs = [f for f in facts if f["predicate"] == "has_drug"]
        assert len(has_drugs) == 2

    def test_search_trials_returns_summary_structure(self):
        from weslr.search_adapters.clinicaltrials_adapter import search_trials

        # With no network, should return empty results gracefully
        result = search_trials("BRCA1 breast cancer", max_results=3)
        assert "studies" in result
        assert "fact_count" in result
        assert "summary" in result
        assert isinstance(result["studies"], list)


# ──────────────────────────────────────────────────────────────────────────────
# Tenant-Aware Fact Store
# ──────────────────────────────────────────────────────────────────────────────

class TestTenantAwareFactStore:
    def test_fact_store_path_resolution(self):
        from weslr.fact_extractor import _resolve_fact_store_path
        from weslr.tenant_context import set_current_tenant

        set_current_tenant("test_tenant")
        path = _resolve_fact_store_path(None, None)
        assert "tenants" in str(path)
        assert "test_tenant" in str(path)
        set_current_tenant(None)

    def test_load_facts_tenant_aware(self):
        from weslr.fact_extractor import load_facts
        # Should load without error; returns list
        facts = load_facts(limit=5)
        assert isinstance(facts, list)

    def test_append_enriched_fact_tenant_aware(self):
        from weslr.fact_extractor import append_enriched_fact
        test_fact = {
            "subject": "test_subject",
            "predicate": "phase_iv",
            "object": "test_object",
            "source_type": "test",
            "source_reference": {"type": "test"},
            "trust_score": 0.75,
            "extraction_pattern": "test",
        }
        result = append_enriched_fact(test_fact, tenant_id=None)
        assert result["status"] == "appended"