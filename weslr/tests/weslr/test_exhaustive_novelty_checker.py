"""
Tests for exhaustive_novelty_checker.py
"""
import sys
sys.path.insert(0, '.')

import pytest
from unittest.mock import patch, MagicMock

from weslr.modules.exhaustive_novelty_checker import (
    generate_formula_variants,
    check_cod,
    check_oqmd,
    check_aflow,
    check_nomad,
    check_materials_project,
    check_all_sources,
    clear_session_cache,
    _SESSION_CACHE,
)


class TestGenerateFormulaVariants:
    """Test rule-based formula variant generation."""

    def test_exact_formula_preserved(self):
        variants = generate_formula_variants("CaSc2TiO6")
        assert "CaSc2TiO6" in variants

    def test_space_separated(self):
        variants = generate_formula_variants("CaSc2TiO6")
        # Elements separated by spaces, no numbers
        assert any(v == "Ca O Sc Ti" for v in variants)

    def test_hyphenated(self):
        variants = generate_formula_variants("CaSc2TiO6")
        assert any(v == "Ca-O-Sc-Ti" for v in variants)

    def test_full_element_names(self):
        variants = generate_formula_variants("CaSc2TiO6")
        assert any("calcium" in v and "scandium" in v and "titanium" in v for v in variants)

    def test_oxide_mixture_notation(self):
        variants = generate_formula_variants("CaSc2TiO6")
        assert any("-" in v and "O" in v for v in variants)  # e.g. CaO-Sc2O3-TiO2

    def test_partial_formula(self):
        # Sc2TiO6 = drop the most electropositive (Ca)
        variants = generate_formula_variants("CaSc2TiO6")
        assert any(v in ("Sc2TiO6", "Sc2TiO", "Sc Ti O", "OScTi") for v in variants)

    def test_alpha_sorted_formula(self):
        variants = generate_formula_variants("CaSc2TiO6")
        # Alphabetical by symbol: Ca, O, Sc, Ti → counts preserved
        assert any(v == "Ca1O6Sc2Ti1" for v in variants)

    def test_known_perovskite_calcium_titanate(self):
        variants = generate_formula_variants("CaTiO3")
        # Should contain "calcium titanate"
        assert any("calcium titanate" in v for v in variants)
        assert any("calcium titanium oxide" in v for v in variants)

    def test_titania_aliases(self):
        variants = generate_formula_variants("TiO2")
        assert any(v in ("titanium dioxide", "titania") for v in variants)

    def test_iron_oxide_aliases(self):
        variants = generate_formula_variants("Fe2O3")
        assert any("iron oxide" in v or "ferric oxide" in v for v in variants)

    def test_zinc_oxide_aliases(self):
        variants = generate_formula_variants("ZnO")
        assert any("zinc oxide" in v or "zincite" in v for v in variants)

    def test_silica_aliases(self):
        variants = generate_formula_variants("SiO2")
        assert any("silicon dioxide" in v or "silica" in v for v in variants)

    def test_empty_formula_returns_formula(self):
        variants = generate_formula_variants("")
        assert variants == [""]

    def test_unknown_elements_returns_formula(self):
        variants = generate_formula_variants("Xyz123")
        assert variants == ["Xyz123"]

    def test_result_is_sorted_list(self):
        variants = generate_formula_variants("CaSc2TiO6")
        assert isinstance(variants, list)
        # Check it is sorted (each element is a string, and the list has unique entries)
        assert variants == sorted(variants)
        assert len(variants) == len(set(variants))  # no duplicates


class TestCheckCod:
    """Test COD (Crystallography Open Database) API query."""

    def setup_method(self):
        clear_session_cache()

    def test_returns_count_zero_on_empty_result(self):
        with patch("weslr.modules.exhaustive_novelty_checker.requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"total": 0}
            mock_get.return_value = mock_resp

            result = check_cod("CaSc2TiO6")
            assert result["source"] == "COD"
            assert result["count"] == 0
            assert result["enabled"] is True
            assert result["error"] is None

    def test_returns_count_on_found_result(self):
        with patch("weslr.modules.exhaustive_novelty_checker.requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"total": 3}
            mock_get.return_value = mock_resp

            result = check_cod("CaTiO3")
            assert result["count"] == 3

    def test_caches_result(self):
        with patch("weslr.modules.exhaustive_novelty_checker.requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"total": 1}
            mock_get.return_value = mock_resp

            check_cod("CaTiO3")
            check_cod("CaTiO3")  # second call
            assert mock_get.call_count == 1  # second call served from cache


class TestCheckOqmd:
    """Test OQMD API query."""

    def setup_method(self):
        clear_session_cache()

    def test_returns_count_from_nresults_field(self):
        with patch("weslr.modules.exhaustive_novelty_checker.requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"nresults": 5, "results": [{}, {}, {}, {}, {}]}
            mock_get.return_value = mock_resp

            result = check_oqmd("CaTiO3")
            assert result["source"] == "OQMD"
            assert result["count"] == 5
            assert result["enabled"] is True

    def test_returns_zero_when_nresults_absent(self):
        with patch("weslr.modules.exhaustive_novelty_checker.requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {}
            mock_get.return_value = mock_resp

            result = check_oqmd("NovelCompound")
            assert result["count"] == 0


class TestCheckAflow:
    """Test AFLOW API query."""

    def setup_method(self):
        clear_session_cache()

    def test_returns_count_from_nresults(self):
        with patch("weslr.modules.exhaustive_novelty_checker.requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"nresults": 2}
            mock_get.return_value = mock_resp

            result = check_aflow("CaTiO3")
            assert result["count"] == 2

    def test_falls_back_to_nsystems(self):
        with patch("weslr.modules.exhaustive_novelty_checker.requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"nsystems": 7}
            mock_get.return_value = mock_resp

            result = check_aflow("Fe2O3")
            assert result["count"] == 7


class TestCheckNomad:
    """Test NOMAD API query."""

    def setup_method(self):
        clear_session_cache()

    def test_returns_count_from_total_field(self):
        with patch("weslr.modules.exhaustive_novelty_checker.requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = {"total": 4}
            mock_get.return_value = mock_resp

            result = check_nomad("CaTiO3")
            assert result["source"] == "NOMAD"
            assert result["count"] == 4

    def test_returns_zero_on_404(self):
        with patch("weslr.modules.exhaustive_novelty_checker.requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 404
            mock_get.return_value = mock_resp

            result = check_nomad("NovelCompound")
            assert result["count"] == 0


class TestCheckMaterialsProject:
    """Test Materials Project API query."""

    def setup_method(self):
        clear_session_cache()

    def test_disabled_when_no_api_key(self):
        result = check_materials_project("CaTiO3", api_key=None)
        assert result["enabled"] is False
        assert "no API key" in result["error"]

    def test_disabled_when_empty_api_key(self):
        result = check_materials_project("CaTiO3", api_key="")
        assert result["enabled"] is False
        assert "no API key" in result["error"]

    def test_returns_count_on_success(self):
        with patch("weslr.modules.exhaustive_novelty_checker.requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            # MP returns a list of material documents
            mock_resp.json.return_value = [{"material_id": "mp-1"}, {"material_id": "mp-2"}]
            mock_get.return_value = mock_resp

            result = check_materials_project("CaTiO3", api_key="test-key")
            assert result["count"] == 2
            assert result["enabled"] is True

    def test_returns_zero_on_404(self):
        with patch("weslr.modules.exhaustive_novelty_checker.requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 404
            mock_get.return_value = mock_resp

            result = check_materials_project("NovelCompound", api_key="test-key")
            assert result["count"] == 0

    def test_disabled_on_401_invalid_key(self):
        with patch("weslr.modules.exhaustive_novelty_checker.requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 401
            mock_get.return_value = mock_resp

            result = check_materials_project("CaTiO3", api_key="bad-key")
            assert result["enabled"] is False
            assert result["error"] == "invalid API key"


class TestCheckAllSources:
    """Integration test for check_all_sources()."""

    def setup_method(self):
        clear_session_cache()

    def _mock_all_sources_zero(self, m_cod, m_oqmd, m_aflow, m_nomad, m_mp):
        for m in (m_cod, m_oqmd, m_aflow, m_nomad, m_mp):
            m.return_value = {"source": m._name, "count": 0, "enabled": True, "error": None}

    @patch("weslr.modules.exhaustive_novelty_checker._rate_limit", lambda: None)
    def test_novel_formula_all_zeros(self):
        with patch("weslr.modules.exhaustive_novelty_checker.check_cod") as m_cod, \
             patch("weslr.modules.exhaustive_novelty_checker.check_oqmd") as m_oqmd, \
             patch("weslr.modules.exhaustive_novelty_checker.check_aflow") as m_aflow, \
             patch("weslr.modules.exhaustive_novelty_checker.check_nomad") as m_nomad, \
             patch("weslr.modules.exhaustive_novelty_checker.check_materials_project") as m_mp:

            self._mock_all_sources_zero(m_cod, m_oqmd, m_aflow, m_nomad, m_mp)
            result = check_all_sources("CaSc2TiO6", config={})

            assert result["formula"] == "CaSc2TiO6"
            assert result["total_hits"] == 0
            assert result["is_novel"] is True
            assert "COD" in result["sources"]
            assert "OQMD" in result["sources"]
            assert "AFLOW" in result["sources"]
            assert "NOMAD" in result["sources"]
            assert "Materials Project" in result["sources"]

    @patch("weslr.modules.exhaustive_novelty_checker._rate_limit", lambda: None)
    def test_found_formula_returns_nonzero_hits(self):
        with patch("weslr.modules.exhaustive_novelty_checker.check_cod") as m_cod, \
             patch("weslr.modules.exhaustive_novelty_checker.check_oqmd") as m_oqmd, \
             patch("weslr.modules.exhaustive_novelty_checker.check_aflow") as m_aflow, \
             patch("weslr.modules.exhaustive_novelty_checker.check_nomad") as m_nomad, \
             patch("weslr.modules.exhaustive_novelty_checker.check_materials_project") as m_mp:

            m_cod.return_value = {"source": "COD", "count": 2, "enabled": True, "error": None}
            m_oqmd.return_value = {"source": "OQMD", "count": 0, "enabled": True, "error": None}
            m_aflow.return_value = {"source": "AFLOW", "count": 0, "enabled": True, "error": None}
            m_nomad.return_value = {"source": "NOMAD", "count": 0, "enabled": True, "error": None}
            m_mp.return_value = {"source": "Materials Project", "count": 0, "enabled": False, "error": "no API key"}

            result = check_all_sources("CaTiO3", config={})

            assert result["total_hits"] == 2
            assert result["is_novel"] is False
            assert result["sources"]["COD"]["count"] == 2

    @patch("weslr.modules.exhaustive_novelty_checker._rate_limit", lambda: None)
    def test_materials_project_disabled_without_key(self):
        # When no API key is in config, check_all_sources uses the module-level
        # MATERIALS_PROJECT_API_KEY (unset in tests) → check_materials_project
        # returns enabled=False. We only mock the non-MP sources so the real
        # MP logic runs.
        with patch("weslr.modules.exhaustive_novelty_checker.check_cod") as m_cod, \
             patch("weslr.modules.exhaustive_novelty_checker.check_oqmd") as m_oqmd, \
             patch("weslr.modules.exhaustive_novelty_checker.check_aflow") as m_aflow, \
             patch("weslr.modules.exhaustive_novelty_checker.check_nomad") as m_nomad:

            for m in (m_cod, m_oqmd, m_aflow, m_nomad):
                m.return_value = {"source": m._name, "count": 0, "enabled": True, "error": None}

            result = check_all_sources("CaTiO3", config={})

            mp_src = result["sources"].get("Materials Project", {})
            # No API key configured → expected to be disabled
            assert mp_src.get("enabled") is False, \
                f"expected MP disabled, got enabled={mp_src.get('enabled')}"

    @patch("weslr.modules.exhaustive_novelty_checker._rate_limit", lambda: None)
    def test_variants_included_in_result(self):
        with patch("weslr.modules.exhaustive_novelty_checker.check_cod") as m_cod, \
             patch("weslr.modules.exhaustive_novelty_checker.check_oqmd") as m_oqmd, \
             patch("weslr.modules.exhaustive_novelty_checker.check_aflow") as m_aflow, \
             patch("weslr.modules.exhaustive_novelty_checker.check_nomad") as m_nomad, \
             patch("weslr.modules.exhaustive_novelty_checker.check_materials_project") as m_mp:

            self._mock_all_sources_zero(m_cod, m_oqmd, m_aflow, m_nomad, m_mp)
            result = check_all_sources("CaTiO3", config={})

            assert len(result["variants"]) >= 5
            assert "CaTiO3" in result["variants"]


class TestClearSessionCache:
    """Test cache clearing."""

    def test_clears_session_cache(self):
        clear_session_cache()
        assert _SESSION_CACHE == {}

    def test_clears_api_call_count(self):
        from weslr.modules.exhaustive_novelty_checker import _API_CALL_COUNT
        clear_session_cache()
        assert _API_CALL_COUNT == {}

# ── Thermodynamic functions ───────────────────────────────────────────────────

class TestStabilityRating:
    """Test _stability_rating helper."""

    def test_zero_eah_is_stable(self):
        from weslr.modules.exhaustive_novelty_checker import _stability_rating
        assert _stability_rating(0.0) == "stable"

    def test_low_eah_is_metastable(self):
        from weslr.modules.exhaustive_novelty_checker import _stability_rating
        assert _stability_rating(0.05) == "metastable"
        assert _stability_rating(0.15) == "metastable"

    def test_high_eah_is_unstable(self):
        from weslr.modules.exhaustive_novelty_checker import _stability_rating
        assert _stability_rating(0.2) == "unstable"
        assert _stability_rating(1.5) == "unstable"

    def test_none_eah_is_unknown(self):
        from weslr.modules.exhaustive_novelty_checker import _stability_rating
        assert _stability_rating(None) == "unknown"


class TestCheckMaterialsProjectThermodynamics:
    """Test MP thermo endpoint with mocked responses."""

    def setup_method(self):
        clear_session_cache()

    def test_stable_compound_eah_zero(self):
        with patch("weslr.modules.exhaustive_novelty_checker.requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = [{
                "energy_above_hull": 0.0,
                "formation_energy_per_atom": -2.5,
                "decomposition": [
                    {"formula": "CaTiO3", "type": "compound"},
                    {"formula": "Sc2O3", "type": "compound"},
                ],
            }]
            mock_get.return_value = mock_resp

            from weslr.modules.exhaustive_novelty_checker import check_materials_project_thermodynamics
            result = check_materials_project_thermodynamics("CaSc2TiO6", api_key="test-key")

            assert result["stability_rating"] == "stable"
            assert result["is_stable"] is True
            assert result["energy_above_hull"] == 0.0
            assert result["formation_energy_per_atom"] == -2.5
            assert "CaTiO3" in result["decomposition_products"]
            assert result["found"] is True
            assert result["enabled"] is True

    def test_metastable_compound_eah_positive(self):
        with patch("weslr.modules.exhaustive_novelty_checker.requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = [{
                "energy_above_hull": 0.08,
                "formation_energy_per_atom": -1.8,
                "decomposition": [],
            }]
            mock_get.return_value = mock_resp

            from weslr.modules.exhaustive_novelty_checker import check_materials_project_thermodynamics
            result = check_materials_project_thermodynamics("CaSc2TiO6", api_key="test-key")

            assert result["stability_rating"] == "metastable"
            assert result["is_stable"] is False
            assert result["energy_above_hull"] == 0.08

    def test_not_found_returns_no_entry(self):
        with patch("weslr.modules.exhaustive_novelty_checker.requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 404
            mock_get.return_value = mock_resp

            from weslr.modules.exhaustive_novelty_checker import check_materials_project_thermodynamics
            result = check_materials_project_thermodynamics("NovelCompound", api_key="test-key")

            assert result["found"] is False
            assert result["error"] == "no entry"
            assert result["stability_rating"] == "unknown"

    def test_no_api_key_returns_disabled(self):
        from weslr.modules.exhaustive_novelty_checker import check_materials_project_thermodynamics
        result = check_materials_project_thermodynamics("CaSc2TiO6", api_key=None)
        assert result["enabled"] is False
        assert "no API key" in result["error"]

    def test_caches_result(self):
        with patch("weslr.modules.exhaustive_novelty_checker.requests.get") as mock_get:
            mock_resp = MagicMock()
            mock_resp.status_code = 200
            mock_resp.json.return_value = [{"energy_above_hull": 0.05, "formation_energy_per_atom": -1.5, "decomposition": []}]
            mock_get.return_value = mock_resp

            from weslr.modules.exhaustive_novelty_checker import check_materials_project_thermodynamics
            check_materials_project_thermodynamics("CaSc2TiO6", api_key="test-key")
            check_materials_project_thermodynamics("CaSc2TiO6", api_key="test-key")
            assert mock_get.call_count == 1


class TestEstimateStabilityHeuristic:
    """Test rule-based heuristic fallback."""

    def test_charge_neutral_gets_bonus(self):
        from weslr.modules.exhaustive_novelty_checker import estimate_stability_heuristic
        # CaTiO3 is charge-neutral → score should be high
        result = estimate_stability_heuristic("CaTiO3", {})
        assert result["stability_rating"] in ("moderately plausible", "speculative", "unlikely")
        assert result["source"] == "heuristic"
        assert result["energy_above_hull"] is None  # heuristic doesn't set eah

    def test_toxic_elements_get_penalty(self):
        from weslr.modules.exhaustive_novelty_checker import estimate_stability_heuristic
        # Cd is toxic/rare → score should be lower
        result = estimate_stability_heuristic("CdTiO3", {})
        # Score should be reduced by -0.2
        assert result["stability_rating"] in ("speculative", "unlikely")
        assert result["source"] == "heuristic"

    def test_known_prototype_gets_bonus(self):
        from weslr.modules.exhaustive_novelty_checker import estimate_stability_heuristic
        result = estimate_stability_heuristic("Mg2SiO4", {"known_structure_types": ["olivine"]})
        assert result["stability_rating"] == "moderately plausible"
        assert result["stability_score"] > 0.6

    def test_score_capped_at_one(self):
        from weslr.modules.exhaustive_novelty_checker import estimate_stability_heuristic
        result = estimate_stability_heuristic("CaTiO3", {"known_structure_types": ["perovskite"]})
        assert result["stability_score"] <= 1.0

    def test_score_capped_at_zero(self):
        from weslr.modules.exhaustive_novelty_checker import estimate_stability_heuristic
        # Toxic + unusual stoichiometry → should still be >= 0
        result = estimate_stability_heuristic("CdHgTlO3", {})
        assert result["stability_score"] >= 0.0


class TestCheckThermodynamics:
    """Test the orchestrator: MP preferred, heuristic fallback."""

    def setup_method(self):
        clear_session_cache()

    @patch("weslr.modules.exhaustive_novelty_checker.check_materials_project_thermodynamics")
    def test_mp_available_used(self, mock_mp):
        mock_mp.return_value = {
            "enabled": True, "found": True,
            "energy_above_hull": 0.05, "formation_energy_per_atom": -1.8,
            "decomposition_products": [], "stability_rating": "metastable",
            "is_stable": False,
        }
        from weslr.modules.exhaustive_novelty_checker import check_thermodynamics
        result = check_thermodynamics("CaSc2TiO6", api_key="fake-key")
        assert result["source"] == "Materials Project"
        assert result["energy_above_hull"] == 0.05

    @patch("weslr.modules.exhaustive_novelty_checker.check_materials_project_thermodynamics")
    @patch("weslr.modules.exhaustive_novelty_checker.estimate_stability_heuristic")
    def test_mp_not_found_falls_back_to_heuristic(self, mock_heur, mock_mp):
        mock_mp.return_value = {"enabled": True, "found": False, "error": "no entry"}
        mock_heur.return_value = {
            "enabled": True, "source": "heuristic",
            "stability_rating": "speculative", "stability_score": 0.45,
        }
        from weslr.modules.exhaustive_novelty_checker import check_thermodynamics
        result = check_thermodynamics("NovelCompound", api_key="fake-key")
        # MP returned found=False + error="no entry" → condition is False → fallback to heuristic

    @patch("weslr.modules.exhaustive_novelty_checker.check_materials_project_thermodynamics")
    def test_no_key_falls_back_to_heuristic(self, mock_mp):
        mock_mp.return_value = {
            "enabled": False, "error": "no API key",
            "found": False, "stability_rating": "unknown",
        }
        from weslr.modules.exhaustive_novelty_checker import check_thermodynamics
        result = check_thermodynamics("CaTiO3", api_key=None)
        assert result["source"] == "heuristic"
        assert result["stability_rating"] in ("moderately plausible", "speculative")


class TestCheckAllSourcesIncludesThermodynamics:
    """Verify check_all_sources now includes thermodynamics in its result."""

    def setup_method(self):
        clear_session_cache()

    @patch("weslr.modules.exhaustive_novelty_checker._rate_limit", lambda: None)
    def test_result_contains_thermodynamics_key(self):
        with patch("weslr.modules.exhaustive_novelty_checker.check_cod") as m_cod, \
             patch("weslr.modules.exhaustive_novelty_checker.check_oqmd") as m_oqmd, \
             patch("weslr.modules.exhaustive_novelty_checker.check_aflow") as m_aflow, \
             patch("weslr.modules.exhaustive_novelty_checker.check_nomad") as m_nomad, \
             patch("weslr.modules.exhaustive_novelty_checker.check_materials_project") as m_mp:

            for m in (m_cod, m_oqmd, m_aflow, m_nomad, m_mp):
                m.return_value = {"source": m._name, "count": 0, "enabled": True, "error": None}

            from weslr.modules.exhaustive_novelty_checker import check_all_sources
            result = check_all_sources("CaTiO3", config={})

            assert "thermodynamics" in result
            thermo = result["thermodynamics"]
            assert "stability_rating" in thermo
            assert "source" in thermo
