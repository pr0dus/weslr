"""Tests for Evidence Ontology / Trust Anchor Layer (v20)

Tests evidence_ontology.py data models, factory functions, and integration hooks.
"""

from __future__ import annotations

import unittest

from weslr.evidence_ontology import (
    AttestationStatus,
    AttestationType,
    EvidenceChain,
    EvidenceClaim,
    EvidenceAttestation,
    EvidenceSource,
    EvidenceStatus,
    EvidenceType,
    create_evidence_claim,
    create_attestation,
    create_evidence_chain,
    integrate_with_change_proposal,
    integrate_with_governance_view,
    integrate_with_operator_review,
)


class TestEvidenceOntology(unittest.TestCase):
    """Test evidence ontology data models and factory functions."""

    def test_create_evidence_claim_defaults(self):
        """Test creating an evidence claim with defaults."""
        claim = create_evidence_claim(
            text="System startup completed successfully.",
            summary="Startup check passed.",
        )
        
        self.assertIsNotNone(claim.claim_id)
        self.assertEqual(claim.text, "System startup completed successfully.")
        self.assertEqual(claim.summary, "Startup check passed.")
        self.assertEqual(claim.evidence_type, EvidenceType.OTHER.value)
        self.assertEqual(claim.evidence_source, EvidenceSource.OTHER.value)
        self.assertEqual(claim.status, EvidenceStatus.DRAFT.value)
        self.assertEqual(claim.domain_tags, [])
        self.assertIsNone(claim.author)
        self.assertIsNone(claim.source_ref)
        self.assertIsNone(claim.confidence_score)
        self.assertIsNotNone(claim.created_at)

    def test_create_evidence_claim_full(self):
        """Test creating an evidence claim with all fields."""
        claim = create_evidence_claim(
            text="Temperature reading exceeded threshold.",
            summary="Threshold breach detected.",
            evidence_type=EvidenceType.MEASUREMENT.value,
            evidence_source=EvidenceSource.AUTOMATED_SENSOR.value,
            status=EvidenceStatus.UNDER_REVIEW.value,
            domain_tags=["hospital", "patient_wing"],
            author="sensor-001",
            source_ref="temp-reading-12345",
            confidence_score=0.95,
        )
        
        self.assertEqual(claim.evidence_type, EvidenceType.MEASUREMENT.value)
        self.assertEqual(claim.evidence_source, EvidenceSource.AUTOMATED_SENSOR.value)
        self.assertEqual(claim.status, EvidenceStatus.UNDER_REVIEW.value)
        self.assertEqual(claim.domain_tags, ["hospital", "patient_wing"])
        self.assertEqual(claim.author, "sensor-001")
        self.assertEqual(claim.source_ref, "temp-reading-12345")
        self.assertEqual(claim.confidence_score, 0.95)

    def test_create_evidence_claim_to_dict_roundtrip(self):
        """Test to_dict and from_dict roundtrip."""
        claim = create_evidence_claim(text="Test claim")
        claim_dict = claim.to_dict()
        claim2 = EvidenceClaim.from_dict(claim_dict)
        
        self.assertEqual(claim.claim_id, claim2.claim_id)
        self.assertEqual(claim.text, claim2.text)
        self.assertEqual(claim.status, claim2.status)

    def test_evidence_claim_update(self):
        """Test updating an evidence claim."""
        claim = create_evidence_claim(text="Initial text")
        original_created = claim.created_at
        original_updated = claim.updated_at
        
        import time as time_module
        time_module.sleep(0.02)  # Larger delay to ensure timestamp change
        
        claim.update(text="Updated text", status=EvidenceStatus.PROPOSED.value)
        
        self.assertEqual(claim.text, "Updated text")
        self.assertEqual(claim.status, EvidenceStatus.PROPOSED.value)
        self.assertEqual(claim.created_at, original_created)
        self.assertNotEqual(claim.updated_at, original_updated)

    def test_evidence_claim_add_domain(self):
        """Test adding domain tags."""
        claim = create_evidence_claim(text="Test")
        self.assertEqual(claim.domain_tags, [])
        
        claim.add_domain("hospital")
        self.assertEqual(claim.domain_tags, ["hospital"])
        
        claim.add_domain("education")
        self.assertEqual(claim.domain_tags, ["hospital", "education"])

    def test_evidence_claim_set_status(self):
        """Test updating status."""
        claim = create_evidence_claim(text="Test", status=EvidenceStatus.DRAFT.value)
        self.assertEqual(claim.status, EvidenceStatus.DRAFT.value)
        
        claim.set_status(EvidenceStatus.PROPOSED.value)
        self.assertEqual(claim.status, EvidenceStatus.PROPOSED.value)

    def test_create_attestation(self):
        """Test creating an attestation."""
        claim = create_evidence_claim(text="Test claim")
        attestation = create_attestation(
            claim_id=claim.claim_id,
            attestation_type=AttestationType.VERIFICATION.value,
            attested_by="operator-001",
            evidence="Verified by manual inspection.",
            rationale="All checks passed.",
        )
        
        self.assertIsNotNone(attestation.attestation_id)
        self.assertEqual(attestation.claim_id, claim.claim_id)
        self.assertEqual(attestation.attestation_type, AttestationType.VERIFICATION.value)
        self.assertEqual(attestation.attestation_status, AttestationStatus.PENDING.value)
        self.assertEqual(attestation.attested_by, "operator-001")
        self.assertEqual(attestation.evidence, "Verified by manual inspection.")
        self.assertEqual(attestation.rationale, "All checks passed.")

    def test_attestation_activate(self):
        """Test activating an attestation."""
        attestation = create_attestation(claim_id="claim-123")
        self.assertEqual(attestation.attestation_status, AttestationStatus.PENDING.value)
        
        attestation.activate(attested_by="operator-001", evidence="Validated")
        
        self.assertEqual(attestation.attestation_status, AttestationStatus.ACTIVE.value)
        self.assertIsNotNone(attestation.attested_at)

    def test_attestation_revoke(self):
        """Test revoking an attestation."""
        attestation = create_attestation(claim_id="claim-123")
        attestation.activate(attested_by="operator-001")
        
        attestation.revoke(revoked_by="operator-002", rationale="Invalid evidence.")
        
        self.assertEqual(attestation.attestation_status, AttestationStatus.REVOKED.value)
        self.assertEqual(attestation.revoked_by, "operator-002")
        self.assertEqual(attestation.rationale, "Invalid evidence.")

    def test_create_evidence_chain(self):
        """Test creating an evidence chain."""
        claim = create_evidence_claim(text="Root claim")
        chain = create_evidence_chain(claim, author="author-001")
        
        self.assertIsNotNone(chain.chain_id)
        self.assertEqual(chain.root_claim_id, claim.claim_id)
        self.assertEqual(len(chain.claims), 1)
        self.assertEqual(chain.claims[0].claim_id, claim.claim_id)
        self.assertEqual(chain.author, "author-001")

    def test_evidence_chain_add_claim_and_attestation(self):
        """Test adding claims and attestations to a chain."""
        claim1 = create_evidence_claim(text="Root claim")
        chain = create_evidence_chain(claim1)
        
        claim2 = create_evidence_claim(text="Derived claim")
        claim2.parent_claim_id = claim1.claim_id  # Set after creation
        chain.add_claim(claim2)
        
        attestation = create_attestation(claim_id=claim2.claim_id)
        chain.add_attestation(attestation)
        
        self.assertEqual(len(chain.claims), 2)
        self.assertEqual(len(chain.attestations), 1)
        self.assertEqual(chain.claims[1].parent_claim_id, claim1.claim_id)


class TestIntegrationHooks(unittest.TestCase):
    """Test integration hooks for change proposals, governance views, and operator reviews."""

    def test_integrate_with_change_proposal_adds_fields(self):
        """Test that integration adds evidence fields without breaking existing data."""
        proposal_dict = {
            "proposal_id": "prop-001",
            "title": "Test proposal",
            "description": "Test description",
            "existing_field": "existing_value",
        }
        
        result = integrate_with_change_proposal(proposal_dict)
        
        self.assertIn("evidence_claim_ids", result)
        self.assertIn("evidence_chain_ids", result)
        self.assertEqual(result["evidence_claim_ids"], [])
        self.assertEqual(result["evidence_chain_ids"], [])
        self.assertEqual(result["existing_field"], "existing_value")

    def test_integrate_with_change_proposal_preserves_existing(self):
        """Test that integration preserves existing fields."""
        proposal_dict = {
            "proposal_id": "prop-001",
            "title": "Test proposal",
            "description": "Test description",
            "existing_field": "existing_value",
            "evidence_claim_ids": ["claim-001"],
        }
        
        result = integrate_with_change_proposal(proposal_dict)
        
        self.assertEqual(result["existing_field"], "existing_value")
        self.assertEqual(result["evidence_claim_ids"], ["claim-001"])

    def test_integrate_with_governance_view_adds_fields(self):
        """Test that integration adds evidence fields."""
        governance_dict = {
            "proposal_id": "prop-001",
            "title": "Test proposal",
            "description": "Test description",
        }
        
        result = integrate_with_governance_view(governance_dict)
        
        self.assertIn("evidence_summary", result)
        self.assertIn("evidence_confidence", result)
        self.assertEqual(result["evidence_summary"], "")
        self.assertEqual(result["evidence_confidence"], 0.0)

    def test_integrate_with_operator_review_adds_fields(self):
        """Test that integration adds evidence fields."""
        review_dict = {
            "proposal_id": "prop-001",
            "title": "Test proposal",
            "description": "Test description",
        }
        
        result = integrate_with_operator_review(review_dict)
        
        self.assertIn("evidence_claim_ids", result)
        self.assertIn("evidence_chain_ids", result)
        self.assertIn("evidence_summary", result)
        self.assertIn("evidence_confidence", result)
        self.assertEqual(result["evidence_claim_ids"], [])
        self.assertEqual(result["evidence_chain_ids"], [])
        self.assertEqual(result["evidence_summary"], "")
        self.assertEqual(result["evidence_confidence"], 0.0)


class TestBackwardCompatibility(unittest.TestCase):
    """Test that new fields are optional via dataclass defaults.
    
    Manual verification (in-place):
    - ChangeProposal: evidence_claim_ids, evidence_chain_ids, evidence_summary, evidence_confidence all default
    - ProposalGovernanceView: evidence_summary, evidence_confidence, evidence_claim_count all default
    - OperatorReviewOutput: evidence_claim_ids, evidence_chain_ids, evidence_summary, evidence_confidence all default
    """
    
    def test_dataclass_default_fields(self):
        """Verify dataclasses have default values for new evidence fields."""
        # EvidenceClaim
        claim = create_evidence_claim(text="Test")
        self.assertEqual(claim.evidence_type, EvidenceType.OTHER.value)
        self.assertEqual(claim.evidence_source, EvidenceSource.OTHER.value)
        self.assertEqual(claim.status, EvidenceStatus.DRAFT.value)
        self.assertEqual(claim.domain_tags, [])
        self.assertIsNone(claim.notes)  # New field, defaults to None
        
        # EvidenceAttestation
        attestation = create_attestation(claim_id="claim-123")
        self.assertEqual(attestation.attestation_status, AttestationStatus.PENDING.value)
        self.assertIsNone(attestation.attested_by)
        self.assertEqual(attestation.evidence, "")  # Default empty string
        self.assertEqual(attestation.rationale, "")  # Default empty string
        
        # EvidenceChain
        claim = create_evidence_claim(text="Root")
        chain = create_evidence_chain(claim)
        self.assertEqual(len(chain.claims), 1)
        self.assertEqual(len(chain.attestations), 0)
        self.assertIsNone(chain.author)  # New field, defaults to None


if __name__ == "__main__":
    unittest.main()
