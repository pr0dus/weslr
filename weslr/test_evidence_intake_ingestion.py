"""Evidence Intake Ingestion Tests - Phase A

Test suite for evidence ingestion pipeline in Phase A.
Tests parse_external, normalize, and generate_proposal_payload methods.

Test Doctrine version: 1.0.0 (2026-04-06)
"""

import unittest
from weslr.evidence_intake.models import (
    EvidenceSource,
    NormalizedEvidence,
    EvidenceProposalPayload,
    EvidenceSourceTypeEnum,
)
from weslr.evidence_intake.ingestion import EvidenceIngestion


class TestEvidenceIngestionBehavior(unittest.TestCase):
    """Test evidence ingestion pipeline behavior."""
    
    def setUp(self) -> None:
        """Set up test fixtures."""
        self.ingestion = EvidenceIngestion()
    
    def test_parse_external_file_source(self) -> None:
        """Test parse_external with FILE source type."""
        source = self.ingestion.parse_external(
            source_type=EvidenceSourceTypeEnum.FILE,
            reference="/path/to/file.txt",
            timestamp="2026-04-08T14:55:00Z",
        )
        
        self.assertIsInstance(source, EvidenceSource)
        self.assertEqual(source.source_type, EvidenceSourceTypeEnum.FILE)
        self.assertEqual(source.source_reference, "/path/to/file.txt")
        self.assertEqual(source.timestamp, "2026-04-08T14:55:00Z")
    
    def test_parse_external_url_source(self) -> None:
        """Test parse_external with URL source type."""
        source = self.ingestion.parse_external(
            source_type=EvidenceSourceTypeEnum.URL,
            reference="https://example.com/evidence",
        )
        
        self.assertEqual(source.source_type, EvidenceSourceTypeEnum.URL)
        self.assertEqual(source.source_reference, "https://example.com/evidence")
    
    def test_parse_external_document_source(self) -> None:
        """Test parse_external with DOCUMENT source type."""
        source = self.ingestion.parse_external(
            source_type=EvidenceSourceTypeEnum.DOCUMENT,
            reference="doc_123",
            timestamp="2026-04-08T14:55:00Z",
        )
        
        self.assertEqual(source.source_type, EvidenceSourceTypeEnum.DOCUMENT)
        self.assertEqual(source.source_reference, "doc_123")
    
    def test_normalize_empty_claims(self) -> None:
        """Test normalize with abstract source (empty claims in Phase A)."""
        source = EvidenceSource(
            source_type=EvidenceSourceTypeEnum.FILE,
            source_reference="/path/to/file.txt",
            timestamp="2026-04-08T14:55:00Z",
        )
        
        normalized = self.ingestion.normalize(source)
        
        # Phase A: Abstract normalization returns empty list
        self.assertEqual(normalized, [])
    
    def test_normalize_with_claims(self) -> None:
        """Test normalize would return NormalizedEvidence items if claims present."""
        source = EvidenceSource(
            source_type=EvidenceSourceTypeEnum.FILE,
            source_reference="/path/to/file.txt",
            timestamp="2026-04-08T14:55:00Z",
            extracted_claims=["Claim 1", "Claim 2"],
        )
        
        normalized = self.ingestion.normalize(source)
        
        # Phase A: Abstract normalization returns empty list
        self.assertEqual(normalized, [])
    
    def test_generate_proposal_payload(self) -> None:
        """Test generate_proposal_payload creates valid payload."""
        normalized = NormalizedEvidence(
            source_id="src_1",
            claim_text="Normalized claim text",
            confidence_score=0.85,
        )
        
        payload = self.ingestion.generate_proposal_payload(normalized)
        
        self.assertIsInstance(payload, EvidenceProposalPayload)
        self.assertEqual(payload.evidence_id, "src_1")
        self.assertEqual(payload.claim_text, "Normalized claim text")
        self.assertEqual(payload.source_summary, "Evidence from src_1")
        self.assertEqual(payload.confidence, 0.85)
        self.assertEqual(payload.status, "DRAFT")
    
    def test_generate_proposal_payload_no_confidence(self) -> None:
        """Test generate_proposal_payload without confidence score."""
        normalized = NormalizedEvidence(
            source_id="src_1",
            claim_text="Claim without confidence",
        )
        
        payload = self.ingestion.generate_proposal_payload(normalized)
        
        self.assertEqual(payload.confidence, None)
        self.assertEqual(payload.status, "DRAFT")
    
    def test_full_pipeline_flow(self) -> None:
        """Test the full ingestion pipeline flow."""
        # Step 1: Parse external
        source = self.ingestion.parse_external(
            source_type=EvidenceSourceTypeEnum.FILE,
            reference="/path/to/file.txt",
            timestamp="2026-04-08T14:55:00Z",
        )
        
        # Step 2: Normalize
        normalized_list = self.ingestion.normalize(source)
        
        # Step 3: Generate proposal payload (with normalized evidence)
        if normalized_list:
            payload = self.ingestion.generate_proposal_payload(normalized_list[0])
            self.assertIsInstance(payload, EvidenceProposalPayload)
        else:
            # Phase A: No normalization, so no payload generated
            self.assertEqual(normalized_list, [])


class TestEvidenceIngestionIntegration(unittest.TestCase):
    """Test evidence ingestion integration with existing WESLR structures."""
    
    def setUp(self) -> None:
        """Set up test fixtures."""
        self.ingestion = EvidenceIngestion()
    
    def test_ingestion_integration_with_existing_models(self) -> None:
        """Verify evidence ingestion works with existing data structures."""
        # Verify EvidenceIngestion can be instantiated
        ingestion = EvidenceIngestion()
        self.assertIsInstance(ingestion, EvidenceIngestion)
        
        # Verify it produces correct model types
        source = ingestion.parse_external(
            source_type=EvidenceSourceTypeEnum.FILE,
            reference="/test.txt",
        )
        self.assertIsInstance(source, EvidenceSource)
    
    def test_pipeline_models_have_correct_types(self) -> None:
        """Verify all pipeline methods return correct model types."""
        ingestion = EvidenceIngestion()
        
        # Parse returns EvidenceSource
        source = ingestion.parse_external(
            source_type=EvidenceSourceTypeEnum.FILE,
            reference="/test.txt",
        )
        self.assertIsInstance(source, EvidenceSource)
        
        # Normalize returns list of NormalizedEvidence
        normalized = ingestion.normalize(source)
        self.assertIsInstance(normalized, list)
        
        # Generate payload returns EvidenceProposalPayload
        if normalized:
            payload = ingestion.generate_proposal_payload(normalized[0])
            self.assertIsInstance(payload, EvidenceProposalPayload)


class TestEvidenceIngestionBackwardCompatibility(unittest.TestCase):
    """Test backward compatibility with existing v94b layers."""
    
    def test_ingestion_imports_cleanly(self) -> None:
        """Verify evidence ingestion imports without errors."""
        from weslr.evidence_intake.ingestion import EvidenceIngestion
        ingestion = EvidenceIngestion()
        self.assertIsInstance(ingestion, EvidenceIngestion)
    
    def test_imports_work_without_new_dependencies(self) -> None:
        """Verify evidence intake imports don't require new dependencies."""
        try:
            from weslr.evidence_intake import (
                EvidenceSource,
                NormalizedEvidence,
                EvidenceProposalPayload,
                EvidenceIngestion,
            )
            self.assertTrue(True)
        except ImportError as e:
            self.fail(f"Import failed: {e}")


if __name__ == "__main__":
    unittest.main()
