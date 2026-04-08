"""Evidence Intake Model Tests - Phase A

Test suite for evidence assimilation models in Phase A.
Tests data structures, serialization, and backward compatibility.

Test Doctrine version: 1.0.0 (2026-04-06)
"""

import unittest
from weslr.evidence_intake.models import (
    EvidenceSource,
    NormalizedEvidence,
    EvidenceProposalPayload,
    EvidenceSourceTypeEnum,
)


class TestEvidenceModel(unittest.TestCase):
    """Test data models for evidence assimilation."""
    
    def test_evidence_source_creation(self) -> None:
        """Test EvidenceSource creation and basic properties."""
        source = EvidenceSource(
            source_type=EvidenceSourceTypeEnum.FILE,
            source_reference="/path/to/evidence.txt",
            timestamp="2026-04-08T14:55:00Z",
            extracted_claims=["Claim 1", "Claim 2"],
        )
        
        self.assertEqual(source.source_type, EvidenceSourceTypeEnum.FILE)
        self.assertEqual(source.source_reference, "/path/to/evidence.txt")
        self.assertEqual(source.timestamp, "2026-04-08T14:55:00Z")
        self.assertEqual(len(source.extracted_claims), 2)
        self.assertEqual(source.source_metadata, {})
    
    def test_evidence_source_default_claims(self) -> None:
        """Test EvidenceSource with default empty claims list."""
        source = EvidenceSource(
            source_type=EvidenceSourceTypeEnum.URL,
            source_reference="https://example.com/evidence",
            timestamp="2026-04-08T14:55:00Z",
        )
        
        self.assertEqual(source.extracted_claims, [])
    
    def test_evidence_source_serialization(self) -> None:
        """Test EvidenceSource to_dict and from_dict."""
        source = EvidenceSource(
            source_type=EvidenceSourceTypeEnum.FILE,
            source_reference="/path/to/file.txt",
            timestamp="2026-04-08T14:55:00Z",
            extracted_claims=["Test claim"],
            source_metadata={"key": "value"},
        )
        
        data = source.to_dict()
        restored = EvidenceSource.from_dict(data)
        
        self.assertEqual(source.source_type, restored.source_type)
        self.assertEqual(source.source_reference, restored.source_reference)
        self.assertEqual(source.timestamp, restored.timestamp)
        self.assertEqual(source.extracted_claims, restored.extracted_claims)
        self.assertEqual(source.source_metadata, restored.source_metadata)
    
    def test_normalized_evidence_creation(self) -> None:
        """Test NormalizedEvidence creation and basic properties."""
        evidence = NormalizedEvidence(
            source_id="src_1",
            claim_text="This is a normalized claim",
            confidence_score=0.85,
            dependency_ids=["dep_1", "dep_2"],
        )
        
        self.assertEqual(evidence.source_id, "src_1")
        self.assertEqual(evidence.claim_text, "This is a normalized claim")
        self.assertEqual(evidence.confidence_score, 0.85)
        self.assertEqual(len(evidence.dependency_ids), 2)
    
    def test_normalized_evidence_optional_fields(self) -> None:
        """Test NormalizedEvidence with optional fields not set."""
        evidence = NormalizedEvidence(
            source_id="src_1",
            claim_text="Simple claim",
        )
        
        self.assertIsNone(evidence.confidence_score)
        self.assertEqual(evidence.dependency_ids, [])
    
    def test_normalized_evidence_serialization(self) -> None:
        """Test NormalizedEvidence to_dict and from_dict."""
        evidence = NormalizedEvidence(
            source_id="src_1",
            claim_text="Normalized claim",
            confidence_score=0.9,
            dependency_ids=["dep_1"],
            normalized_metadata={"key": "value"},
        )
        
        data = evidence.to_dict()
        restored = NormalizedEvidence.from_dict(data)
        
        self.assertEqual(evidence.source_id, restored.source_id)
        self.assertEqual(evidence.claim_text, restored.claim_text)
        self.assertEqual(evidence.confidence_score, restored.confidence_score)
        self.assertEqual(evidence.dependency_ids, restored.dependency_ids)
    
    def test_evidence_proposal_payload_creation(self) -> None:
        """Test EvidenceProposalPayload creation."""
        payload = EvidenceProposalPayload(
            evidence_id="norm_1",
            claim_text="Proposed claim",
            source_summary="Summary of source",
            confidence=0.75,
            status="DRAFT",
        )
        
        self.assertEqual(payload.evidence_id, "norm_1")
        self.assertEqual(payload.claim_text, "Proposed claim")
        self.assertEqual(payload.source_summary, "Summary of source")
        self.assertEqual(payload.confidence, 0.75)
        self.assertEqual(payload.status, "DRAFT")
    
    def test_evidence_proposal_payload_default_status(self) -> None:
        """Test EvidenceProposalPayload default status is DRAFT."""
        payload = EvidenceProposalPayload(
            evidence_id="norm_1",
            claim_text="Proposed claim",
            source_summary="Summary",
        )
        
        self.assertEqual(payload.status, "DRAFT")
    
    def test_evidence_proposal_payload_serialization(self) -> None:
        """Test EvidenceProposalPayload to_dict and from_dict."""
        payload = EvidenceProposalPayload(
            evidence_id="norm_1",
            claim_text="Proposed claim",
            source_summary="Source summary",
            confidence=0.8,
            status="DRAFT",
        )
        
        data = payload.to_dict()
        restored = EvidenceProposalPayload.from_dict(data)
        
        self.assertEqual(payload.evidence_id, restored.evidence_id)
        self.assertEqual(payload.claim_text, restored.claim_text)
        self.assertEqual(payload.source_summary, restored.source_summary)
        self.assertEqual(payload.confidence, restored.confidence)
        self.assertEqual(payload.status, restored.status)


class TestEvidenceBackwardCompatibility(unittest.TestCase):
    """Test backward compatibility with existing v94b layers."""
    
    def test_models_import_without_error(self) -> None:
        """Verify evidence models import without errors."""
        # If this test runs, it means evidence intake modules import cleanly
        from weslr.evidence_intake.models import (
            EvidenceSource,
            NormalizedEvidence,
            EvidenceProposalPayload,
            EvidenceSourceTypeEnum,
        )
        self.assertTrue(True)
    
    def test_ingestion_import_without_error(self) -> None:
        """Verify evidence ingestion module imports without errors."""
        from weslr.evidence_intake.ingestion import EvidenceIngestion
        self.assertTrue(True)


if __name__ == "__main__":
    unittest.main()
