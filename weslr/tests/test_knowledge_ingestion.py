"""Tests for Scientific / Institutional Knowledge Ingestion Layer (v26)

Tests knowledge_ingestion.py data models, engine, and integration hooks.
"""

from __future__ import annotations

import unittest

from weslr.knowledge_ingestion import (
    SourceClass,
    IngestionStatus,
    EvidenceType,
    EvidenceClaim,
    KnowledgeIngestion,
    KnowledgeIngestionEngine,
    integrate_with_evidence_ontology,
    integrate_with_domain_ontology,
    integrate_with_governance_view,
    integrate_with_proposal_realization,
)


class TestIngestionModelModels(unittest.TestCase):
    """Test knowledge ingestion data models."""

    def test_evidence_claim_creation(self):
        """Test creating an evidence claim."""
        claim = EvidenceClaim(
            claim_id="claim-001",
            text="The system has a latency of less than 100ms",
            evidence_type=EvidenceType.RESULT.value,
            confidence=0.85,
            domain_tags=["performance", "latency"],
        )
        
        self.assertEqual(claim.claim_id, "claim-001")
        self.assertEqual(claim.text, "The system has a latency of less than 100ms")
        self.assertEqual(claim.evidence_type, EvidenceType.RESULT.value)
        self.assertEqual(claim.confidence, 0.85)
        self.assertEqual(len(claim.domain_tags), 2)

    def test_evidence_claim_serialization(self):
        """Test evidence claim to_dict/from_dict."""
        claim = EvidenceClaim(
            claim_id="claim-001",
            text="Test claim",
            evidence_type=EvidenceType.FACT.value,
        )
        
        claim_dict = claim.to_dict()
        claim2 = EvidenceClaim.from_dict(claim_dict)
        
        self.assertEqual(claim.claim_id, claim2.claim_id)
        self.assertEqual(claim.text, claim2.text)

    def test_knowledge_ingestion_creation(self):
        """Test creating a knowledge ingestion."""
        ingestion = KnowledgeIngestion(
            ingestion_id="ingest-001",
            source_class=SourceClass.PAPER.value,
            title="Test Paper",
            source_reference="https://example.com/paper",
            summary="Test summary",
            domain_tags=["machine-learning", "neural-networks"],
        )
        
        self.assertEqual(ingestion.ingestion_id, "ingest-001")
        self.assertEqual(ingestion.source_class, SourceClass.PAPER.value)
        self.assertEqual(ingestion.title, "Test Paper")
        self.assertEqual(len(ingestion.domain_tags), 2)
        self.assertEqual(ingestion.ingestion_status, IngestionStatus.PENDING.value)

    def test_knowledge_ingestion_generate_claim(self):
        """Test generating claims from ingestion."""
        ingestion = KnowledgeIngestion(
            ingestion_id="ingest-001",
            source_class=SourceClass.PAPER.value,
            title="Test Paper",
            source_reference="https://example.com/paper",
        )
        
        claim = ingestion.generate_claim("Finding: method X improves accuracy", EvidenceType.RESULT.value, 0.9)
        
        self.assertEqual(claim.text, "Finding: method X improves accuracy")
        self.assertEqual(len(ingestion.evidence_claims), 1)
        self.assertEqual(ingestion.evidence_claims[0]["claim_id"], claim.claim_id)

    def test_knowledge_ingestion_set_status(self):
        """Test setting ingestion status."""
        ingestion = KnowledgeIngestion(
            ingestion_id="ingest-001",
            source_class=SourceClass.PAPER.value,
            title="Test Paper",
            source_reference="https://example.com/paper",
        )
        
        ingestion.set_status(IngestionStatus.INGESTED.value)
        self.assertEqual(ingestion.ingestion_status, IngestionStatus.INGESTED.value)
        self.assertIsNotNone(ingestion.last_updated)
        
        ingestion.set_status(IngestionStatus.TRUSTED.value, "operator-001")
        self.assertEqual(ingestion.ingestion_status, IngestionStatus.TRUSTED.value)
        self.assertEqual(ingestion.reviewed_by, "operator-001")
        self.assertIsNotNone(ingestion.reviewed_at)

    def test_knowledge_ingestion_serialization(self):
        """Test knowledge ingestion to_dict/from_dict."""
        ingestion = KnowledgeIngestion(
            ingestion_id="ingest-001",
            source_class=SourceClass.PAPER.value,
            title="Test Paper",
            source_reference="https://example.com/paper",
            domain_tags=["test"],
        )
        
        ingestion_dict = ingestion.to_dict()
        ingestion2 = KnowledgeIngestion.from_dict(ingestion_dict)
        
        self.assertEqual(ingestion.ingestion_id, ingestion2.ingestion_id)
        self.assertEqual(ingestion.source_class, ingestion2.source_class)
        self.assertEqual(ingestion.domain_tags, ingestion2.domain_tags)


class TestKnowledgeIngestionEngine(unittest.TestCase):
    """Test knowledge ingestion engine."""

    def test_register_ingestion(self):
        """Test registering an ingestion."""
        engine = KnowledgeIngestionEngine()
        ingestion = KnowledgeIngestion(
            ingestion_id="ingest-001",
            source_class=SourceClass.PAPER.value,
            title="Test Paper",
            source_reference="https://example.com/paper",
        )
        
        engine.register_ingestion(ingestion)
        self.assertEqual(engine.get_ingestion("ingest-001"), ingestion)

    def test_create_ingestion(self):
        """Test creating an ingestion via engine."""
        engine = KnowledgeIngestionEngine()
        ingestion = engine.create_ingestion(
            source_class=SourceClass.PAPER.value,
            title="Test Paper",
            source_reference="https://example.com/paper",
            summary="Summary text",
            domain_tags=["test-domain"],
        )
        
        self.assertEqual(ingestion.source_class, SourceClass.PAPER.value)
        self.assertEqual(ingestion.title, "Test Paper")
        self.assertEqual(ingestion.summary, "Summary text")
        self.assertEqual(ingestion.domain_tags, ["test-domain"])

    def test_generate_claims_from_ingestion(self):
        """Test generating claims from an ingestion."""
        engine = KnowledgeIngestionEngine()
        ingestion = engine.create_ingestion(
            source_class=SourceClass.PAPER.value,
            title="Test Paper",
            source_reference="https://example.com/paper",
        )
        
        claims_data = [
            {"text": "Claim 1", "evidence_type": EvidenceType.FACT.value, "confidence": 0.8},
            {"text": "Claim 2", "evidence_type": EvidenceType.RESULT.value, "confidence": 0.9},
        ]
        
        claims = engine.generate_claims_from_ingestion(ingestion.ingestion_id, claims_data)
        
        self.assertEqual(len(claims), 2)
        self.assertEqual(len(ingestion.evidence_claims), 2)

    def test_get_trusted_claims(self):
        """Test getting trusted claims."""
        engine = KnowledgeIngestionEngine()
        
        # Create trusted ingestion
        ingestion1 = engine.create_ingestion(
            source_class=SourceClass.PAPER.value,
            title="Trusted Paper",
            source_reference="https://example.com/paper1",
        )
        ingestion1.set_status(IngestionStatus.TRUSTED.value)
        ingestion1.generate_claim("Trusted fact", EvidenceType.FACT.value)
        
        # Create reviewed (not trusted) ingestion
        ingestion2 = engine.create_ingestion(
            source_class=SourceClass.PAPER.value,
            title="Reviewed Paper",
            source_reference="https://example.com/paper2",
        )
        ingestion2.set_status(IngestionStatus.REVIEWED.value)
        ingestion2.generate_claim("Review claim", EvidenceType.FACT.value)
        
        trusted = engine.get_trusted_claims()
        self.assertEqual(len(trusted), 1)
        self.assertEqual(trusted[0].text, "Trusted fact")

    def test_get_trusted_claims_with_domain_filter(self):
        """Test getting trusted claims with domain filter."""
        engine = KnowledgeIngestionEngine()
        
        # Create trusted ingestion in "performance" domain
        ingestion1 = engine.create_ingestion(
            source_class=SourceClass.PAPER.value,
            title="Performance Paper",
            source_reference="https://example.com/paper1",
            domain_tags=["performance"],
        )
        ingestion1.set_status(IngestionStatus.TRUSTED.value)
        ingestion1.generate_claim("Latency < 100ms", EvidenceType.RESULT.value)
        
        # Create trusted ingestion in "accuracy" domain
        ingestion2 = engine.create_ingestion(
            source_class=SourceClass.PAPER.value,
            title="Accuracy Paper",
            source_reference="https://example.com/paper2",
            domain_tags=["accuracy"],
        )
        ingestion2.set_status(IngestionStatus.TRUSTED.value)
        ingestion2.generate_claim("Accuracy > 95%", EvidenceType.RESULT.value)
        
        # Filter by "performance"
        trusted = engine.get_trusted_claims(domain_tags=["performance"])
        self.assertEqual(len(trusted), 1)
        self.assertIn("Latency", trusted[0].text)
        
        # Filter by "accuracy"
        trusted = engine.get_trusted_claims(domain_tags=["accuracy"])
        self.assertEqual(len(trusted), 1)
        self.assertIn("Accuracy", trusted[0].text)


class TestIntegrationHooks(unittest.TestCase):
    """Test integration hooks for evidence ontology, domain ontology, governance, and realization."""

    def test_integrate_with_evidence_ontology_adds_metadata(self):
        """Test that integration adds ingestion metadata to evidence ontology."""
        ontology_dict = {
            "ontology_id": "evidence",
            "name": "Evidence Ontology",
        }
        
        result = integrate_with_evidence_ontology(ontology_dict)
        
        self.assertIn("source_classes", result)
        self.assertIn("ingestion_status_values", result)
        self.assertIn("knowledge_ingestions", result)
        self.assertEqual(result["source_classes"], [sc.value for sc in SourceClass])
        self.assertEqual(result["ingestion_status_values"], [s.value for s in IngestionStatus])

    def test_integrate_with_evidence_ontology_preserves_existing(self):
        """Test that integration preserves existing ingestion metadata."""
        ontology_dict = {
            "ontology_id": "evidence",
            "knowledge_ingestions": ["ingest-001"],
        }
        
        result = integrate_with_evidence_ontology(ontology_dict)
        
        self.assertEqual(result["knowledge_ingestions"], ["ingest-001"])

    def test_integrate_with_domain_ontology_adds_ingestion_fields(self):
        """Test that integration adds ingestion fields to domain ontology."""
        ontology_dict = {
            "domain_id": "home",
            "name": "Home",
        }
        
        result = integrate_with_domain_ontology(ontology_dict)
        
        self.assertIn("knowledge_sources", result)
        self.assertIn("trusted_sources", result)
        self.assertIn("ingestion_requirements", result)
        self.assertEqual(result["knowledge_sources"], [])

    def test_integrate_with_domain_ontology_preserves_existing(self):
        """Test that integration preserves existing domain ingestion fields."""
        ontology_dict = {
            "domain_id": "home",
            "trusted_sources": ["source-001"],
        }
        
        result = integrate_with_domain_ontology(ontology_dict)
        
        self.assertEqual(result["trusted_sources"], ["source-001"])

    def test_integrate_with_governance_view_adds_ingestion_context(self):
        """Test that integration adds ingestion context to governance."""
        governance_dict = {
            "proposal_id": "prop-001",
            "title": "Test proposal",
        }
        
        result = integrate_with_governance_view(governance_dict)
        
        self.assertIn("knowledge_ingestion_id", result)
        self.assertIn("knowledge_status", result)
        self.assertFalse(result["knowledge_trusted"])
        self.assertIsNone(result["knowledge_ingestion_id"])

    def test_integrate_with_governance_view_preserves_existing(self):
        """Test that integration preserves existing governance ingestion context."""
        governance_dict = {
            "proposal_id": "prop-001",
            "knowledge_status": "trusted",
            "knowledge_trusted": True,
        }
        
        result = integrate_with_governance_view(governance_dict)
        
        self.assertEqual(result["knowledge_status"], "trusted")
        self.assertTrue(result["knowledge_trusted"])

    def test_integrate_with_proposal_realization_adds_ingestion_context(self):
        """Test that integration adds ingestion context to proposal realization."""
        realization_dict = {
            "plan_id": "plan-001",
        }
        
        result = integrate_with_proposal_realization(realization_dict)
        
        self.assertIn("knowledge_ingestion_id", result)
        self.assertIn("knowledge_confidence", result)
        self.assertEqual(result["knowledge_confidence"], 0.0)
        self.assertEqual(result["knowledge_claims"], [])

    def test_integrate_with_proposal_realization_preserves_existing(self):
        """Test that integration preserves existing realization ingestion context."""
        realization_dict = {
            "plan_id": "plan-001",
            "knowledge_confidence": 0.8,
            "knowledge_claims": ["claim-001"],
        }
        
        result = integrate_with_proposal_realization(realization_dict)
        
        self.assertEqual(result["knowledge_confidence"], 0.8)
        self.assertEqual(result["knowledge_claims"], ["claim-001"])


if __name__ == "__main__":
    unittest.main()
