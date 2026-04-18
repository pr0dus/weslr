"""Evidence-to-Candidate Mapping Tests - Phase B

Test suite for evidence-to-candidate mapping in Phase B.
Tests candidate evidence models, candidate proposal generation, and backward compatibility.

Test Doctrine version: 1.0.0 (2026-04-06)
"""

import unittest
from weslr.evidence_intake.evidence_to_candidate import (
    CandidateEvidence,
    CandidateProvenance,
    ProposalPayloadWithCandidate,
)
from weslr.evidence_intake.models import NormalizedEvidence, EvidenceProposalPayload


class TestCandidateEvidenceModel(unittest.TestCase):
    """Test data models for evidence-to-candidate mapping."""
    
    def test_candidate_provenance_creation(self) -> None:
        """Test CandidateProvenance creation and basic properties."""
        provenance = CandidateProvenance(
            source_id="src_1",
            source_timestamp="2026-04-08T15:00:00Z",
            normalized_timestamp="2026-04-08T15:01:00Z",
            confidence_score=0.85,
        )
        
        self.assertEqual(provenance.source_id, "src_1")
        self.assertEqual(provenance.source_timestamp, "2026-04-08T15:00:00Z")
        self.assertEqual(provenance.normalized_timestamp, "2026-04-08T15:01:00Z")
        self.assertEqual(provenance.confidence_score, 0.85)
    
    def test_candidate_provenance_serialization(self) -> None:
        """Test CandidateProvenance to_dict and from_dict."""
        provenance = CandidateProvenance(
            source_id="src_1",
            source_timestamp="2026-04-08T15:00:00Z",
            normalized_timestamp="2026-04-08T15:01:00Z",
            confidence_score=0.85,
        )
        
        data = provenance.to_dict()
        restored = CandidateProvenance.from_dict(data)
        
        self.assertEqual(provenance.source_id, restored.source_id)
        self.assertEqual(provenance.source_timestamp, restored.source_timestamp)
        self.assertEqual(provenance.normalized_timestamp, restored.normalized_timestamp)
        self.assertEqual(provenance.confidence_score, restored.confidence_score)
    
    def test_candidate_evidence_creation(self) -> None:
        """Test CandidateEvidence creation with candidate references."""
        evidence = CandidateEvidence(
            source_id="norm_1",
            claim_text="Normalized claim",
            confidence_score=0.85,
            candidate_node_id="candidate_node_123",
            candidate_node_type="capability",
        )
        
        self.assertEqual(evidence.source_id, "norm_1")
        self.assertEqual(evidence.claim_text, "Normalized claim")
        self.assertEqual(evidence.confidence_score, 0.85)
        self.assertEqual(evidence.candidate_node_id, "candidate_node_123")
        self.assertEqual(evidence.candidate_node_type, "capability")
        self.assertIsNone(evidence.candidate_provenance)
    
    def test_candidate_evidence_with_provenance(self) -> None:
        """Test CandidateEvidence with full provenance."""
        provenance = CandidateProvenance(
            source_id="src_1",
            source_timestamp="2026-04-08T15:00:00Z",
            normalized_timestamp="2026-04-08T15:01:00Z",
            confidence_score=0.85,
        )
        
        evidence = CandidateEvidence(
            source_id="norm_1",
            claim_text="Normalized claim",
            candidate_node_id="candidate_node_123",
            candidate_node_type="capability",
            candidate_provenance=provenance,
        )
        
        self.assertIsNotNone(evidence.candidate_provenance)
        self.assertEqual(evidence.candidate_provenance.source_id, "src_1")
    
    def test_candidate_evidence_from_normalized(self) -> None:
        """Test CandidateEvidence.from_normalized_evidence classmethod."""
        normalized = NormalizedEvidence(
            source_id="norm_1",
            claim_text="Normalized claim",
            confidence_score=0.85,
        )
        
        evidence = CandidateEvidence.from_normalized_evidence(
            normalized,
            candidate_node_id="candidate_node_123",
            candidate_node_type="capability",
        )
        
        self.assertEqual(evidence.source_id, "norm_1")
        self.assertEqual(evidence.claim_text, "Normalized claim")
        self.assertEqual(evidence.confidence_score, 0.85)
        self.assertEqual(evidence.candidate_node_id, "candidate_node_123")
        self.assertEqual(evidence.candidate_node_type, "capability")
    
    def test_candidate_evidence_serialization(self) -> None:
        """Test CandidateEvidence to_dict and from_dict."""
        provenance = CandidateProvenance(
            source_id="src_1",
            source_timestamp="2026-04-08T15:00:00Z",
            normalized_timestamp="2026-04-08T15:01:00Z",
            confidence_score=0.85,
        )
        
        evidence = CandidateEvidence(
            source_id="norm_1",
            claim_text="Normalized claim",
            candidate_node_id="candidate_node_123",
            candidate_node_type="capability",
            candidate_provenance=provenance,
        )
        
        data = evidence.to_dict()
        restored = CandidateEvidence.from_dict(data)
        
        self.assertEqual(evidence.source_id, restored.source_id)
        self.assertEqual(evidence.candidate_node_id, restored.candidate_node_id)
        self.assertEqual(evidence.candidate_node_type, restored.candidate_node_type)


class TestCandidateProposalGenerationBehavior(unittest.TestCase):
    """Test candidate proposal generation behavior."""
    
    def setUp(self) -> None:
        """Set up test fixtures."""
        from weslr.evidence_intake.ingestion import EvidenceIngestion
        self.ingestion = EvidenceIngestion()
    
    def test_proposal_payload_with_candidate_creation(self) -> None:
        """Test ProposalPayloadWithCandidate creation with candidate references."""
        payload = ProposalPayloadWithCandidate(
            evidence_id="norm_1",
            claim_text="Proposed claim",
            source_summary="Source summary",
            candidate_reference="candidate_node_123",
            candidate_node_type="capability",
            candidate_confidence=0.85,
            candidate_recency="recent",
        )
        
        self.assertEqual(payload.evidence_id, "norm_1")
        self.assertEqual(payload.claim_text, "Proposed claim")
        self.assertEqual(payload.candidate_reference, "candidate_node_123")
        self.assertEqual(payload.candidate_node_type, "capability")
        self.assertEqual(payload.candidate_confidence, 0.85)
        self.assertEqual(payload.candidate_recency, "recent")
    
    def test_proposal_payload_with_candidate_from_base(self) -> None:
        """Test ProposalPayloadWithCandidate.from_payload_and_candidate classmethod."""
        base_payload = EvidenceProposalPayload(
            evidence_id="norm_1",
            claim_text="Proposed claim",
            source_summary="Source summary",
            confidence=0.85,
            status="DRAFT",
        )
        
        payload = ProposalPayloadWithCandidate.from_payload_and_candidate(
            base_payload,
            candidate_reference="candidate_node_123",
            candidate_node_type="capability",
            candidate_confidence=0.85,
            candidate_recency="recent",
        )
        
        # Base fields preserved
        self.assertEqual(payload.evidence_id, "norm_1")
        self.assertEqual(payload.claim_text, "Proposed claim")
        self.assertEqual(payload.source_summary, "Source summary")
        self.assertEqual(payload.confidence, 0.85)
        self.assertEqual(payload.status, "DRAFT")
        
        # Candidate fields added
        self.assertEqual(payload.candidate_reference, "candidate_node_123")
        self.assertEqual(payload.candidate_node_type, "capability")
        self.assertEqual(payload.candidate_confidence, 0.85)
        self.assertEqual(payload.candidate_recency, "recent")
    
    def test_generate_candidate_proposal(self) -> None:
        """Test EvidenceIngestion.generate_candidate_proposal."""
        normalized = NormalizedEvidence(
            source_id="norm_1",
            claim_text="Normalized claim",
            confidence_score=0.85,
        )
        
        payload = self.ingestion.generate_candidate_proposal(
            normalized,
            candidate_reference="candidate_node_123",
            candidate_node_type="capability",
            candidate_confidence=0.85,
            candidate_recency="recent",
        )
        
        self.assertIsInstance(payload, ProposalPayloadWithCandidate)
        self.assertEqual(payload.evidence_id, "norm_1")
        self.assertEqual(payload.candidate_reference, "candidate_node_123")
        self.assertEqual(payload.candidate_node_type, "capability")
    
    def test_candidate_proposal_serialization(self) -> None:
        """Test ProposalPayloadWithCandidate to_dict and from_dict."""
        payload = ProposalPayloadWithCandidate(
            evidence_id="norm_1",
            claim_text="Proposed claim",
            source_summary="Source summary",
            candidate_reference="candidate_node_123",
            candidate_node_type="capability",
            candidate_confidence=0.85,
            candidate_recency="recent",
        )
        
        data = payload.to_dict()
        restored = ProposalPayloadWithCandidate.from_dict(data)
        
        self.assertEqual(payload.evidence_id, restored.evidence_id)
        self.assertEqual(payload.candidate_reference, restored.candidate_reference)
        self.assertEqual(payload.candidate_node_type, restored.candidate_node_type)


class TestCandidateEvidenceIntegration(unittest.TestCase):
    """Test evidence-to-candidate integration with existing structures."""
    
    def test_candidate_evidence_extends_normalized_evidence(self) -> None:
        """Verify CandidateEvidence extends NormalizedEvidence structure."""
        normalized = NormalizedEvidence(
            source_id="norm_1",
            claim_text="Normalized claim",
            confidence_score=0.85,
        )
        evidence = CandidateEvidence.from_normalized_evidence(normalized)
        
        # All normalized fields preserved
        self.assertEqual(evidence.source_id, normalized.source_id)
        self.assertEqual(evidence.claim_text, normalized.claim_text)
        self.assertEqual(evidence.confidence_score, normalized.confidence_score)
    
    def test_candidate_proposal_extends_base_payload(self) -> None:
        """Verify ProposalPayloadWithCandidate extends EvidenceProposalPayload structure."""
        base_payload = EvidenceProposalPayload(
            evidence_id="norm_1",
            claim_text="Proposed claim",
            source_summary="Source summary",
            confidence=0.85,
        )
        payload = ProposalPayloadWithCandidate.from_payload_and_candidate(
            base_payload,
            candidate_reference="candidate_node_123",
            candidate_node_type="capability",
        )
        
        # All base fields preserved
        self.assertEqual(payload.evidence_id, base_payload.evidence_id)
        self.assertEqual(payload.claim_text, base_payload.claim_text)
        self.assertEqual(payload.source_summary, base_payload.source_summary)
        self.assertEqual(payload.confidence, base_payload.confidence)
        self.assertEqual(payload.status, base_payload.status)


class TestCandidateEvidenceBackwardCompatibility(unittest.TestCase):
    """Test backward compatibility with existing evidence intake tests."""
    
    def test_normalized_evidence_unchanged(self) -> None:
        """Verify NormalizedEvidence is unchanged."""
        normalized = NormalizedEvidence(
            source_id="norm_1",
            claim_text="Claim",
        )
        self.assertEqual(normalized.source_id, "norm_1")
    
    def test_evidence_proposal_payload_unchanged(self) -> None:
        """Verify EvidenceProposalPayload is unchanged."""
        payload = EvidenceProposalPayload(
            evidence_id="norm_1",
            claim_text="Proposed",
            source_summary="Summary",
        )
        self.assertEqual(payload.evidence_id, "norm_1")
        self.assertEqual(payload.status, "DRAFT")
    
    def test_candidate_models_dont_break_existing_tests(self) -> None:
        """Verify candidate models don't break existing evidence intake tests."""
        from weslr.evidence_intake.ingestion import EvidenceIngestion
        from weslr.evidence_intake.models import EvidenceSourceTypeEnum
        ingestion = EvidenceIngestion()
        
        # Phase A methods still work
        source = ingestion.parse_external(
            source_type=EvidenceSourceTypeEnum.FILE,
            reference="/test.txt",
        )
        self.assertIsNotNone(source)
        
        # Phase B methods also available
        normalized = ingestion.normalize(source)
        self.assertIsInstance(normalized, list)


if __name__ == "__main__":
    unittest.main()
