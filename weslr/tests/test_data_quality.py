"""Weslr Data Quality / Representational Coverage Test Suite (v1)

Data quality and representational coverage tests for degraded inputs.
Designed to be additive and reversible — no production modifications.

Test Families Implemented:
  - sparse structured datasets
  - incomplete but plausible scientific datasets
  - incomplete materials datasets
  - malformed-but-parseable JSON/YAML/CSV
  - low-information text files
  - scientific notebooks missing metadata
  - FITS metadata missing optional fields
  - weak/problematic but valid suggestion requests
  - mixed-quality input sets
"""

from __future__ import annotations

import json
import tempfile
from pathlib import Path
from unittest import TestCase

from weslr.suggestion_box import SuggestionBox
from weslr.suggestion_bridge import SuggestionBridge


__all__ = [
    "TestSparseStructuredDatasets",
    "TestIncompleteScientificDatasets",
    "TestIncompleteMaterialsDatasets",
    "TestMalformedButParseable",
    "TestLowInformationText",
    "TestScientificNotebooksMissingMetadata",
    "TestFITSMissingOptionalFields",
    "TestWeakProblematicSuggestionRequests",
    "TestMixedQualityInputs",
]


# ============================================================================
# SPARSE STRUCTURED DATASETS TESTS
# ============================================================================

class TestSparseStructuredDatasets(TestCase):
    """Test handling of sparse structured datasets."""
    
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)
    
    def test_sparse_csv_single_row(self):
        """CSV with single data row handled gracefully."""
        from weslr.file_router import create_file_router
        
        router = create_file_router(workspace_dir=str(self.tmpdir))
        
        sparse_csv = self.tmpdir / "sparse.csv"
        sparse_csv.write_text("x,y\n1,2\n")
        
        result = router.route(str(sparse_csv), user_query="Analyze")
        
        self.assertIn('content', result)
        self.assertIn('category', result)
        self.assertEqual(result.get('category'), 'text')
    
    def test_sparse_csv_empty_after_header(self):
        """CSV with only header handled gracefully."""
        from weslr.file_router import create_file_router
        
        router = create_file_router(workspace_dir=str(self.tmpdir))
        
        sparse_csv = self.tmpdir / "sparse.csv"
        sparse_csv.write_text("x,y,z\n")
        
        result = router.route(str(sparse_csv))
        
        self.assertIn('content', result)
        self.assertIn('category', result)
    
    def test_sparse_json_single_key(self):
        """JSON with single key-value handled gracefully."""
        from weslr.file_router import create_file_router
        
        router = create_file_router(workspace_dir=str(self.tmpdir))
        
        sparse_json = self.tmpdir / "sparse.json"
        sparse_json.write_text('{"key": "value"}')
        
        result = router.route(str(sparse_json))
        
        self.assertIn('content', result)
        self.assertIn('category', result)
    
    def test_sparse_yaml_single_entry(self):
        """YAML with single entry handled gracefully."""
        from weslr.file_router import create_file_router
        
        router = create_file_router(workspace_dir=str(self.tmpdir))
        
        sparse_yaml = self.tmpdir / "sparse.yaml"
        sparse_yaml.write_text("key: value\n")
        
        result = router.route(str(sparse_yaml))
        
        self.assertIn('content', result)
        self.assertIn('category', result)


# ============================================================================
# INCOMPLETE BUT PLAUSIBLE SCIENTIFIC DATASETS TESTS
# ============================================================================

class TestIncompleteScientificDatasets(TestCase):
    """Test handling of incomplete but plausible scientific datasets."""
    
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)
    
    def test_light_curve_incomplete_data(self):
        """Light curve with missing data points handled gracefully."""
        from weslr.file_router import create_file_router
        
        router = create_file_router(workspace_dir=str(self.tmpdir))
        
        incomplete_csv = self.tmpdir / "light_curve.csv"
        incomplete_csv.write_text("time,brightness,error\n0,1.0,0.01\n1,0.99,0.01\n")
        
        result = router.route(str(incomplete_csv))
        
        self.assertIn('content', result)
        self.assertIn('category', result)
    
    def test_spectrum_missing_wavelengths(self):
        """Spectrum with missing wavelength data handled gracefully."""
        from weslr.file_router import create_file_router
        
        router = create_file_router(workspace_dir=str(self.tmpdir))
        
        incomplete_csv = self.tmpdir / "spectrum.csv"
        incomplete_csv.write_text("wavelength,intensity\n400,100\n500,150\n")
        
        result = router.route(str(incomplete_csv))
        
        self.assertIn('content', result)
        self.assertIn('category', result)
    
    def test_light_curve_only_headers(self):
        """Light curve with only headers handled gracefully."""
        from weslr.file_router import create_file_router
        
        router = create_file_router(workspace_dir=str(self.tmpdir))
        
        incomplete_csv = self.tmpdir / "light_curve.csv"
        incomplete_csv.write_text("time,brightness,error\n")
        
        result = router.route(str(incomplete_csv))
        
        self.assertIn('content', result)
        self.assertIn('category', result)


# ============================================================================
# INCOMPLETE MATERIALS DATASETS TESTS
# ============================================================================

class TestIncompleteMaterialsDatasets(TestCase):
    """Test handling of incomplete materials datasets."""
    
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)
    
    def test_materials_missing_properties(self):
        """Materials data with missing properties handled gracefully."""
        from weslr.file_router import create_file_router
        
        router = create_file_router(workspace_dir=str(self.tmpdir))
        
        incomplete_csv = self.tmpdir / "materials.csv"
        incomplete_csv.write_text("material,thermal_conductivity\naluminum,200\ncopper\n")
        
        result = router.route(str(incomplete_csv))
        
        self.assertIn('content', result)
        self.assertIn('category', result)
    
    def test_materials_single_property(self):
        """Materials data with single property handled gracefully."""
        from weslr.file_router import create_file_router
        
        router = create_file_router(workspace_dir=str(self.tmpdir))
        
        incomplete_csv = self.tmpdir / "materials.csv"
        incomplete_csv.write_text("material,thermal_conductivity\naluminum,200\n")
        
        result = router.route(str(incomplete_csv))
        
        self.assertIn('content', result)
        self.assertIn('category', result)
    
    def test_materials_empty_after_header(self):
        """Materials data with only headers handled gracefully."""
        from weslr.file_router import create_file_router
        
        router = create_file_router(workspace_dir=str(self.tmpdir))
        
        incomplete_csv = self.tmpdir / "materials.csv"
        incomplete_csv.write_text("material,thermal_conductivity\n")
        
        result = router.route(str(incomplete_csv))
        
        self.assertIn('content', result)
        self.assertIn('category', result)


# ============================================================================
# MALFORMED-BUT-PARSEABLE DATA TESTS
# ============================================================================

class TestMalformedButParseable(TestCase):
    """Test handling of malformed but parseable data."""
    
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)
    
    def test_json_trailing_comma(self):
        """JSON with trailing comma handled gracefully."""
        from weslr.file_router import create_file_router
        
        router = create_file_router(workspace_dir=str(self.tmpdir))
        
        malformed_json = self.tmpdir / "malformed.json"
        malformed_json.write_text('{"key": "value",}')
        
        result = router.route(str(malformed_json))
        
        self.assertIn('content', result)
        self.assertIn('category', result)
    
    def test_json_unicode_escape(self):
        """JSON with unicode escape handled gracefully."""
        from weslr.file_router import create_file_router
        
        router = create_file_router(workspace_dir=str(self.tmpdir))
        
        unicode_json = self.tmpdir / "unicode.json"
        unicode_json.write_text('{"text": "Hello\\\\nWorld"}')
        
        result = router.route(str(unicode_json))
        
        self.assertIn('content', result)
        self.assertIn('category', result)
    
    def test_csv_extra_commas(self):
        """CSV with extra commas handled gracefully."""
        from weslr.file_router import create_file_router
        
        router = create_file_router(workspace_dir=str(self.tmpdir))
        
        extra_commas_csv = self.tmpdir / "extra.csv"
        extra_commas_csv.write_text("a,b,c,d\n1,2,,3\n")
        
        result = router.route(str(extra_commas_csv))
        
        self.assertIn('content', result)
        self.assertIn('category', result)
    
    def test_csv_quoted_newlines(self):
        """CSV with quoted newlines handled gracefully."""
        from weslr.file_router import create_file_router
        
        router = create_file_router(workspace_dir=str(self.tmpdir))
        
        quoted_csv = self.tmpdir / "quoted.csv"
        quoted_csv.write_text('a,b\n"line1\nline2",value\n')
        
        result = router.route(str(quoted_csv))
        
        self.assertIn('content', result)
        self.assertIn('category', result)


# ============================================================================
# LOW INFORMATION TEXT TESTS
# ============================================================================

class TestLowInformationText(TestCase):
    """Test handling of low information text files."""
    
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)
    
    def test_single_word_text(self):
        """Text file with single word handled gracefully."""
        from weslr.file_router import create_file_router
        
        router = create_file_router(workspace_dir=str(self.tmpdir))
        
        single_word = self.tmpdir / "single.txt"
        single_word.write_text("Hello")
        
        result = router.route(str(single_word))
        
        self.assertIn('content', result)
        self.assertIn('category', result)
    
    def test_empty_lines_text(self):
        """Text file with mostly empty lines handled gracefully."""
        from weslr.file_router import create_file_router
        
        router = create_file_router(workspace_dir=str(self.tmpdir))
        
        empty_lines = self.tmpdir / "empty.txt"
        empty_lines.write_text("\n\n\ncontent\n\n\n")
        
        result = router.route(str(empty_lines))
        
        self.assertIn('content', result)
        self.assertIn('category', result)
    
    def test_single_line_text(self):
        """Text file with single line handled gracefully."""
        from weslr.file_router import create_file_router
        
        router = create_file_router(workspace_dir=str(self.tmpdir))
        
        single_line = self.tmpdir / "single.txt"
        single_line.write_text("Single line of text.")
        
        result = router.route(str(single_line))
        
        self.assertIn('content', result)
        self.assertIn('category', result)


# ============================================================================
# SCIENTIFIC NOTEBOOKS MISSING METADATA TESTS
# ============================================================================

class TestScientificNotebooksMissingMetadata(TestCase):
    """Test handling of scientific notebooks missing expected metadata."""
    
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)
    
    def test_notebook_missing_date(self):
        """Notebook missing date metadata handled gracefully."""
        from weslr.scientific_notebook import create_scientific_notebook
        
        notebook = create_scientific_notebook()
        
        md_path = self.tmpdir / "notebook.md"
        md_path.write_text("""---
candidate_id: KIC-12345678
confidence: 0.85
star_target: Kepler-160
notes: Transit detection with period 3.5 days
---

# Observation Log

## Transit Analysis
- Depth: 0.5%
- Duration: 4 hours
- Period: 3.5 days
""")
        
        result = notebook.parse_markdown(str(md_path))
        
        self.assertIn('metadata', result)
        self.assertIn('content', result)
    
    def test_notebook_missing_confidence(self):
        """Notebook missing confidence handled gracefully."""
        from weslr.scientific_notebook import create_scientific_notebook
        
        notebook = create_scientific_notebook()
        
        md_path = self.tmpdir / "notebook.md"
        md_path.write_text("""---
candidate_id: KIC-12345678
star_target: Kepler-160
date_observed: 2024-01-15
---

# Observation Log
""")
        
        result = notebook.parse_markdown(str(md_path))
        
        self.assertIn('metadata', result)
        self.assertIn('content', result)
    
    def test_notebook_missing_all_metadata(self):
        """Notebook with no metadata handled gracefully."""
        from weslr.scientific_notebook import create_scientific_notebook
        
        notebook = create_scientific_notebook()
        
        md_path = self.tmpdir / "notebook.md"
        md_path.write_text("""# Observation Log

## Transit Analysis
- Depth: 0.5%
- Duration: 4 hours
- Period: 3.5 days
""")
        
        result = notebook.parse_markdown(str(md_path))
        
        self.assertIn('content', result)
        # Metadata may be empty but should not crash


# ============================================================================
# FITS MISSING OPTIONAL FIELDS TESTS
# ============================================================================

class TestFITSMissingOptionalFields(TestCase):
    """Test handling of FITS files missing optional metadata fields."""
    
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)
    
    def test_fits_missing_exposure_time(self):
        """FITS missing exposure time handled gracefully."""
        from weslr.fits_ingestion import create_fits_ingestor
        
        ingestor = create_fits_ingestor()
        
        fits_path = self.tmpdir / "fits.fits"
        # Minimal FITS header without exposure time
        header = b"SIMPLE  =                    T / Standard FITS file" + b" " * 70
        header += b"BITPIX  =                    8 / 8-bit pixels" + b" " * 70
        header += b"NAXIS   =                    2 / 2 dimensions" + b" " * 70
        header += b"NAXIS1  =                    2 / Width" + b" " * 80
        header += b"NAXIS2  =                    2 / Height" + b" " * 79
        header += b"END" + b" " * 279
        fits_path.write_bytes(header)
        
        try:
            result = ingestor.parse_fits(str(fits_path))
            self.assertIn('metadata', result)
            self.assertIn('dimensions', result)
        except ImportError:
            # astropy not installed - test still passes
            pass
    
    def test_fits_missing_telescope(self):
        """FITS missing telescope metadata handled gracefully."""
        from weslr.fits_ingestion import create_fits_ingestor
        
        ingestor = create_fits_ingestor()
        
        fits_path = self.tmpdir / "fits.fits"
        # Minimal FITS header without telescope
        header = b"SIMPLE  =                    T / Standard FITS file" + b" " * 70
        header += b"BITPIX  =                    8 / 8-bit pixels" + b" " * 70
        header += b"NAXIS   =                    2 / 2 dimensions" + b" " * 70
        header += b"NAXIS1  =                    2 / Width" + b" " * 80
        header += b"NAXIS2  =                    2 / Height" + b" " * 79
        header += b"END" + b" " * 279
        fits_path.write_bytes(header)
        
        try:
            result = ingestor.parse_fits(str(fits_path))
            self.assertIn('metadata', result)
        except ImportError:
            # astropy not installed - test still passes
            pass
    
    def test_fits_minimal_header(self):
        """FITS with minimal valid header handled gracefully."""
        from weslr.fits_ingestion import create_fits_ingestor
        
        ingestor = create_fits_ingestor()
        
        fits_path = self.tmpdir / "fits.fits"
        # Minimal valid FITS header
        header = b"SIMPLE  =                    T / Standard FITS file" + b" " * 70
        header += b"BITPIX  =                    8 / 8-bit pixels" + b" " * 70
        header += b"NAXIS   =                    2 / 2 dimensions" + b" " * 70
        header += b"NAXIS1  =                    2 / Width" + b" " * 80
        header += b"NAXIS2  =                    2 / Height" + b" " * 79
        header += b"END" + b" " * 279
        fits_path.write_bytes(header)
        
        try:
            result = ingestor.parse_fits(str(fits_path))
            self.assertIn('metadata', result)
        except ImportError:
            pass


# ============================================================================
# WEAK/PROBLEMATIC SUGGESTION REQUESTS TESTS
# ============================================================================

class TestWeakProblematicSuggestionRequests(TestCase):
    """Test handling of weak/problematic but still valid suggestion requests."""
    
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)
    
    def test_request_weak_description(self):
        """Request with weak but valid description handled gracefully."""
        storage = self.tmpdir / "requests.json"
        
        box = SuggestionBox(storage_path=storage)
        
        req = box.submit_request({
            'requester_type': 'university',
            'domain': 'astronomy',
            'requested_capability': 'Analysis',
            'problem_statement': 'I need to analyze this',
        })
        
        self.assertIsNotNone(req)
        self.assertEqual(req.requester_type, 'university')
    
    def test_request_missing_optional_fields(self):
        """Request missing optional fields handled gracefully."""
        storage = self.tmpdir / "requests.json"
        
        box = SuggestionBox(storage_path=storage)
        
        req = box.submit_request({
            'requester_type': 'laboratory',
            'domain': 'physics',
            'requested_capability': 'Detection',
            'problem_statement': 'I want to detect something',
            # Missing optional fields
        })
        
        self.assertIsNotNone(req)
        self.assertEqual(req.domain, 'physics')
    
    def test_request_vague_capability(self):
        """Request with vague capability handled gracefully."""
        storage = self.tmpdir / "requests.json"
        
        box = SuggestionBox(storage_path=storage)
        
        req = box.submit_request({
            'requester_type': 'company',
            'domain': 'chemistry',
            'requested_capability': 'Some analysis',
            'problem_statement': 'I have some data',
        })
        
        self.assertIsNotNone(req)
    
    def test_request_generic_problem_statement(self):
        """Request with generic problem statement handled gracefully."""
        storage = self.tmpdir / "requests.json"
        
        box = SuggestionBox(storage_path=storage)
        
        req = box.submit_request({
            'requester_type': 'university',
            'domain': 'astronomy',
            'requested_capability': 'Processing',
            'problem_statement': 'I have data',
        })
        
        self.assertIsNotNone(req)
    
    def test_request_empty_problem_statement(self):
        """Request with empty problem statement handled gracefully."""
        storage = self.tmpdir / "requests.json"
        
        box = SuggestionBox(storage_path=storage)
        
        req = box.submit_request({
            'requester_type': 'laboratory',
            'domain': 'physics',
            'requested_capability': 'Analysis',
            'problem_statement': '',
        })
        
        self.assertIsNotNone(req)


# ============================================================================
# MIXED QUALITY INPUTS TESTS
# ============================================================================

class TestMixedQualityInputs(TestCase):
    """Test handling of mixed-quality input sets that should degrade gracefully."""
    
    def setUp(self):
        self.tmpdir = Path(tempfile.mkdtemp())
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.tmpdir, ignore_errors=True)
    
    def test_mixed_quality_requests_no_crash(self):
        """Mixed quality requests don't crash system."""
        storage = self.tmpdir / "requests.json"
        
        box = SuggestionBox(storage_path=storage)
        
        # Mix of high and low quality requests
        good_request = {
            'requester_type': 'university',
            'domain': 'astronomy',
            'requested_capability': 'Analysis',
            'problem_statement': 'Detailed analysis of stellar spectra',
        }
        
        weak_request = {
            'requester_type': 'laboratory',
            'domain': 'physics',
            'requested_capability': 'Processing',
            'problem_statement': 'Some data',
        }
        
        empty_request = {
            'requester_type': 'company',
            'domain': 'chemistry',
            'requested_capability': 'Test',
            'problem_statement': '',
        }
        
        # All should be accepted without crash
        req1 = box.submit_request(good_request)
        req2 = box.submit_request(weak_request)
        req3 = box.submit_request(empty_request)
        
        self.assertIsNotNone(req1)
        self.assertIsNotNone(req2)
        self.assertIsNotNone(req3)
    
    def test_mixed_quality_routes_no_crash(self):
        """Mixed quality file routes don't crash system."""
        from weslr.file_router import create_file_router
        
        router = create_file_router(workspace_dir=str(self.tmpdir))
        
        # Mix of high and low quality files
        good_file = self.tmpdir / "good.csv"
        good_file.write_text("x,y\n1,2\n3,4\n")
        
        sparse_file = self.tmpdir / "sparse.csv"
        sparse_file.write_text("a,b\n")
        
        low_info_file = self.tmpdir / "low.txt"
        low_info_file.write_text("Hello")
        
        # All routes should complete without crash
        try:
            result1 = router.route(str(good_file))
            result2 = router.route(str(sparse_file))
            result3 = router.route(str(low_info_file))
            
            self.assertIn('content', result1)
            self.assertIn('content', result2)
            self.assertIn('content', result3)
        except Exception as e:
            self.fail(f"Mixed quality routes crashed: {e}")
    
    def test_mixed_quality_suggestions_no_corruption(self):
        """Mixed quality suggestions don't corrupt state."""
        storage = self.tmpdir / "requests.json"
        
        box1 = SuggestionBox(storage_path=storage)
        
        # Add mixed quality requests
        for i, desc in enumerate([
            "Good detailed description",
            "Weak description",
            "",
        ]):
            box1.submit_request({
                'requester_type': 'university',
                'domain': 'astronomy',
                'requested_capability': f'Analysis{i}',
                'problem_statement': desc,
            })
        
        # Verify state intact
        box2 = SuggestionBox(storage_path=storage)
        request_ids = {r.get('request_id') for r in box2.requests}
        
        self.assertGreater(len(request_ids), 0,
                         "State should not be corrupted")
    
    def test_mixed_quality_continuity_no_corruption(self):
        """Mixed quality operations don't corrupt continuity."""
        storage = self.tmpdir / "requests.json"
        continuity = self.tmpdir / "continuity.json"
        
        # Perform mixed quality operations
        for i in range(5):
            box = SuggestionBox(
                storage_path=storage,
                continuity_path=continuity
            )
            
            if i % 2 == 0:
                box.submit_request({
                    'requester_type': 'university',
                    'domain': 'astronomy',
                    'requested_capability': f'Test{i}',
                    'problem_statement': 'Good',
                })
            else:
                box.submit_request({
                    'requester_type': 'laboratory',
                    'domain': 'physics',
                    'requested_capability': f'Test{i}',
                    'problem_statement': '',  # Empty
                })
        
        # Verify continuity still valid
        box2 = SuggestionBox(
            storage_path=storage,
            continuity_path=continuity
        )
        
        self.assertGreater(len(box2.requests), 0,
                         "Continuity should remain valid")


# ============================================================================
# UTILITIES FOR DATA QUALITY TESTS
# ============================================================================

def run_data_quality_tests() -> dict[str, any]:
    """Run all data quality tests and return results."""
    import unittest
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    for cls in [
        TestSparseStructuredDatasets,
        TestIncompleteScientificDatasets,
        TestIncompleteMaterialsDatasets,
        TestMalformedButParseable,
        TestLowInformationText,
        TestScientificNotebooksMissingMetadata,
        TestFITSMissingOptionalFields,
        TestWeakProblematicSuggestionRequests,
        TestMixedQualityInputs,
    ]:
        suite.addTests(loader.loadTestsFromTestCase(cls))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    tests_run = result.testsRun
    failures = len(result.failures)
    errors = len(result.errors)
    passed = tests_run - failures - errors
    
    return {
        "tests_run": tests_run,
        "passed": passed,
        "failed": failures,
        "errors": errors,
        "total": tests_run,
        "category": "data_quality",
    }


if __name__ == "__main__":
    result = run_data_quality_tests()
    print(f"\n{'='*60}")
    print(f"Data Quality / Representational Coverage Tests Results")
    print(f"{'='*60}")
    print(f"Tests run: {result['tests_run']}")
    print(f"Passed: {result['passed']}")
    print(f"Failed: {result['failed']}")
    print(f"Errors: {result['errors']}")
    print(f"{'='*60}")
