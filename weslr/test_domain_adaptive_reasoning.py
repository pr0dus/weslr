# test_domain_adaptive_reasoning.py - Behavioral tests for domain_adaptive_reasoning layer
# WESLR v55: Domain Adaptive Reasoning Hardening Layer
# Test Doctrine v1.0.0 (2026-04-06)

from __future__ import annotations

import json
import unittest

from weslr import domain_adaptive_reasoning


class TestDomainDefinitionModel(unittest.TestCase):
    """Model tests for DomainDefinition data class."""

    def test_creation(self):
        """Test basic DomainDefinition creation with all fields."""
        domain = domain_adaptive_reasoning.DomainDefinition(
            domain_id="tech-1",
            domain_type="technical",
            domain_name="Technical Domain",
            description="Technical reasoning domain",
            complexity_level=7.0,
            rate_of_change=5.0,
            safety_criticality=3.0,
            max_evidence_required=4,
            min_confidence_threshold=0.6,
            transfer_strategy="abstract",
            transfer_target_domains=["ops-1", "strat-1"]
        )

        self.assertEqual(domain.domain_id, "tech-1")
        self.assertEqual(domain.domain_type, "technical")
        self.assertEqual(domain.domain_name, "Technical Domain")
        self.assertEqual(domain.complexity_level, 7.0)
        self.assertEqual(domain.rate_of_change, 5.0)
        self.assertEqual(domain.safety_criticality, 3.0)
        self.assertEqual(domain.max_evidence_required, 4)
        self.assertEqual(domain.min_confidence_threshold, 0.6)
        self.assertEqual(domain.transfer_strategy, "abstract")
        self.assertEqual(domain.transfer_target_domains, ["ops-1", "strat-1"])

    def test_default_values(self):
        """Test DomainDefinition with default values."""
        domain = domain_adaptive_reasoning.DomainDefinition(domain_id="default-1")

        self.assertEqual(domain.domain_type, "general")
        self.assertEqual(domain.domain_name, "default")
        self.assertEqual(domain.complexity_level, 5.0)
        self.assertEqual(domain.rate_of_change, 5.0)
        self.assertEqual(domain.safety_criticality, 5.0)
        self.assertEqual(domain.max_evidence_required, 3)
        self.assertEqual(domain.min_confidence_threshold, 0.5)
        self.assertEqual(domain.transfer_strategy, "abstract")
        self.assertEqual(domain.transfer_target_domains, [])

    def test_to_dict(self):
        """Test DomainDefinition to_dict serialization."""
        domain = domain_adaptive_reasoning.DomainDefinition(
            domain_id="test-1",
            domain_type="operational",
            domain_name="Operational Domain"
        )
        result = domain.to_dict()

        self.assertEqual(result["domain_id"], "test-1")
        self.assertEqual(result["domain_type"], "operational")
        self.assertEqual(result["domain_name"], "Operational Domain")
        self.assertEqual(result["max_evidence_required"], 3)
        self.assertEqual(result["min_confidence_threshold"], 0.5)

    def test_from_dict(self):
        """Test DomainDefinition from_dict deserialization."""
        data = {
            "domain_id": "from-dict-1",
            "domain_type": "strategic",
            "domain_name": "Strategic Domain",
            "description": "Strategic reasoning domain",
            "complexity_level": 8.0,
            "rate_of_change": 7.0,
            "safety_criticality": 9.0,
            "max_evidence_required": 5,
            "min_confidence_threshold": 0.7,
            "transfer_strategy": "generalize",
            "transfer_target_domains": ["target-1", "target-2"]
        }
        domain = domain_adaptive_reasoning.DomainDefinition.from_dict(data)

        self.assertEqual(domain.domain_id, "from-dict-1")
        self.assertEqual(domain.domain_type, "strategic")
        self.assertEqual(domain.complexity_level, 8.0)
        self.assertEqual(domain.transfer_target_domains, ["target-1", "target-2"])

    def test_to_json(self):
        """Test DomainDefinition JSON serialization."""
        domain = domain_adaptive_reasoning.DomainDefinition(
            domain_id="json-test",
            domain_type="technical",
            domain_name="JSON Test Domain"
        )
        json_str = domain.to_json()
        self.assertIn("json-test", json_str)
        self.assertIn("technical", json_str)

    def test_from_json(self):
        """Test DomainDefinition JSON deserialization."""
        data = {
            "domain_id": "json-from-1",
            "domain_type": "general",
            "domain_name": "From JSON Domain"
        }
        json_str = json.dumps(data)
        domain = domain_adaptive_reasoning.DomainDefinition.from_json(json_str)

        self.assertEqual(domain.domain_id, "json-from-1")
        self.assertEqual(domain.domain_type, "general")


class TestDomainConstraintModel(unittest.TestCase):
    """Model tests for DomainConstraint data class."""

    def test_creation(self):
        """Test DomainConstraint creation."""
        constraint = domain_adaptive_reasoning.DomainConstraint(
            constraint_id="constraint-1",
            constraint_type="safety",
            constraint_value="critical",
            domain_scope="local",
            applies_to_subdomains=True,
            min_evidence_required=5,
            min_confidence_threshold=0.8
        )

        self.assertEqual(constraint.constraint_id, "constraint-1")
        self.assertEqual(constraint.constraint_type, "safety")
        self.assertEqual(constraint.constraint_value, "critical")
        self.assertEqual(constraint.domain_scope, "local")
        self.assertTrue(constraint.applies_to_subdomains)
        self.assertEqual(constraint.min_evidence_required, 5)
        self.assertEqual(constraint.min_confidence_threshold, 0.8)

    def test_default_subdomains(self):
        """Test DomainConstraint default applies_to_subdomains."""
        constraint = domain_adaptive_reasoning.DomainConstraint(
            constraint_id="constraint-1",
            constraint_type="performance",
            constraint_value="high"
        )

        self.assertTrue(constraint.applies_to_subdomains)


class TestDomainAdaptiveContextModel(unittest.TestCase):
    """Model tests for DomainAdaptiveContext data class."""

    def test_creation(self):
        """Test DomainAdaptiveContext creation."""
        context = domain_adaptive_reasoning.DomainAdaptiveContext(
            current_domain="default",
            active_domains=["tech-1", "ops-1"],
            adaptation_mode="active",
            knowledge_transfer_enabled=True,
            transfer_strategies=["direct", "abstract"]
        )

        self.assertEqual(context.current_domain, "default")
        self.assertEqual(context.active_domains, ["tech-1", "ops-1"])
        self.assertEqual(context.adaptation_mode, "active")
        self.assertTrue(context.knowledge_transfer_enabled)
        self.assertEqual(context.transfer_strategies, ["direct", "abstract"])

    def test_empty_defaults(self):
        """Test DomainAdaptiveContext with defaults."""
        context = domain_adaptive_reasoning.DomainAdaptiveContext(current_domain="default")

        self.assertEqual(context.active_domains, [])
        self.assertEqual(context.adaptation_mode, "passive")
        self.assertFalse(context.knowledge_transfer_enabled)
        self.assertEqual(context.transfer_strategies, [])
        self.assertEqual(context.domain_definitions, {})
        self.assertEqual(context.domain_states, {})
        self.assertEqual(context.constraints, [])

    def test_to_dict(self):
        """Test DomainAdaptiveContext to_dict serialization."""
        context = domain_adaptive_reasoning.DomainAdaptiveContext(
            current_domain="tech-1",
            active_domains=["tech-1"],
            adaptation_mode="active"
        )
        result = context.to_dict()

        self.assertEqual(result["current_domain"], "tech-1")
        self.assertEqual(result["active_domains"], ["tech-1"])
        self.assertEqual(result["adaptation_mode"], "active")
        self.assertEqual(result["domain_definitions"], {})


class TestDomainAdaptiveReasoningBehavior(unittest.TestCase):
    """Behavior tests for DomainAdaptiveReasoningEngine."""

    def setUp(self):
        self.engine = domain_adaptive_reasoning.DomainAdaptiveReasoningEngine()

    def test_register_domain(self):
        """Test domain registration with characteristics."""
        domain = domain_adaptive_reasoning.DomainDefinition(
            domain_id="tech-1",
            domain_type="technical",
            domain_name="Technical Domain",
            complexity_level=7.0,
            safety_criticality=9.0,
            max_evidence_required=4,
            min_confidence_threshold=0.7
        )
        self.engine.register_domain(domain)

        self.assertIn("tech-1", self.engine.context.active_domains)
        self.assertIn("tech-1", self.engine.context.domain_definitions)
        self.assertIn("tech-1", self.engine.context.domain_states)

    def test_set_adaptation_mode(self):
        """Test setting adaptation mode for domains."""
        domain = domain_adaptive_reasoning.DomainDefinition(domain_id="tech-1")
        self.engine.register_domain(domain)

        self.engine.set_adaptation_mode("active", "tech-1")

        self.assertEqual(self.engine.context.adaptation_mode, "active")
        self.assertEqual(self.engine.context.domain_states["tech-1"].active_adaptation_mode, "active")

    def test_adapt_reasoning_safety_critical(self):
        """Test reasoning adaptation for safety-critical domains."""
        domain = domain_adaptive_reasoning.DomainDefinition(
            domain_id="safety-1",
            domain_type="operational",
            safety_criticality=9.0,
            max_evidence_required=3,
            min_confidence_threshold=0.6
        )
        self.engine.register_domain(domain)

        state = self.engine.adapt_reasoning("safety-1")

        self.assertIsNotNone(state)
        self.assertLess(state.confidence_adjustment, 1.0)  # Reduced confidence for safety
        self.assertIn("safety_criticality_high", state.adjustment_reasons)

    def test_adapt_reasoning_complex_domain(self):
        """Test reasoning adaptation for complex domains."""
        domain = domain_adaptive_reasoning.DomainDefinition(
            domain_id="complex-1",
            complexity_level=9.0,
            rate_of_change=8.0,
            min_confidence_threshold=0.5
        )
        self.engine.register_domain(domain)

        state = self.engine.adapt_reasoning("complex-1")

        self.assertIsNotNone(state)
        self.assertLess(state.confidence_adjustment, 1.0)
        self.assertIn("complexity_high", state.adjustment_reasons)
        self.assertIn("rate_of_change_high", state.adjustment_reasons)

    def test_adapt_reasoning_standard_domain(self):
        """Test reasoning adaptation for standard domain."""
        domain = domain_adaptive_reasoning.DomainDefinition(
            domain_id="standard-1",
            complexity_level=5.0,
            rate_of_change=5.0,
            safety_criticality=5.0
        )
        self.engine.register_domain(domain)

        state = self.engine.adapt_reasoning("standard-1")

        self.assertIsNotNone(state)
        self.assertEqual(state.confidence_adjustment, 1.0)  # No reduction for standard
        self.assertEqual(state.adjustment_reasons, [])

    def test_get_current_domain_context(self):
        """Test getting current domain adaptive context."""
        context = self.engine.get_current_domain_context()

        self.assertIsInstance(context, domain_adaptive_reasoning.DomainAdaptiveContext)
        self.assertEqual(context.current_domain, "default")

    def test_get_current_domain_context_after_registration(self):
        """Test context after domain registration."""
        domain = domain_adaptive_reasoning.DomainDefinition(
            domain_id="tech-1",
            domain_type="technical"
        )
        self.engine.register_domain(domain)

        context = self.engine.get_current_domain_context()

        self.assertIn("tech-1", context.active_domains)
        self.assertIn("tech-1", context.domain_definitions)


class TestDomainAdaptiveReasoningIntegration(unittest.TestCase):
    """Integration tests for domain_adaptive_reasoning layer."""

    def test_engine_with_domain_and_constraint(self):
        """Test engine with domain definition and constraint together."""
        engine = domain_adaptive_reasoning.DomainAdaptiveReasoningEngine()

        domain = domain_adaptive_reasoning.DomainDefinition(
            domain_id="integ-1",
            domain_type="technical",
            max_evidence_required=4,
            min_confidence_threshold=0.7
        )
        engine.register_domain(domain)

        constraint = domain_adaptive_reasoning.DomainConstraint(
            constraint_id="integ-constraint-1",
            constraint_type="safety",
            constraint_value="high",
            domain_scope="global",
            min_evidence_required=5,
            min_confidence_threshold=0.8
        )
        engine.context.constraints.append(constraint)

        # Verify domain is registered
        self.assertIn("integ-1", engine.context.active_domains)

        # Verify constraint is added
        self.assertEqual(len(engine.context.constraints), 1)

    def test_engine_state_after_multiple_domains(self):
        """Test engine state with multiple registered domains."""
        engine = domain_adaptive_reasoning.DomainAdaptiveReasoningEngine()

        domains = [
            domain_adaptive_reasoning.DomainDefinition(domain_id=f"dom-{i}", domain_type="general")
            for i in range(3)
        ]
        for domain in domains:
            engine.register_domain(domain)

        # Verify all domains registered
        self.assertEqual(len(engine.context.active_domains), 3)
        self.assertEqual(len(engine.context.domain_definitions), 3)
        self.assertEqual(len(engine.context.domain_states), 3)


class TestDomainAdaptiveReasoningBackwardCompatibility(unittest.TestCase):
    """Backward compatibility tests for domain_adaptive_reasoning layer."""

    def test_empty_engine_creation(self):
        """Test engine can be created without any domains (backward compat)."""
        engine = domain_adaptive_reasoning.DomainAdaptiveReasoningEngine()

        # Should work with no domains
        context = engine.get_current_domain_context()
        self.assertEqual(context.current_domain, "default")

    def test_missing_domain_handling(self):
        """Test handling of missing domains (backward compat)."""
        engine = domain_adaptive_reasoning.DomainAdaptiveReasoningEngine()

        # Adapt reasoning for unregistered domain should return state
        state = engine.adapt_reasoning("nonexistent-1")

        self.assertIsNotNone(state)
        self.assertEqual(state.domain_id, "nonexistent-1")

    def test_missing_context_handling(self):
        """Test handling of missing context data."""
        engine = domain_adaptive_reasoning.DomainAdaptiveReasoningEngine()

        # Apply constraints for unregistered domain
        result = engine.apply_constraints("nonexistent-1", evidence_count=2, confidence=0.5)

        # Should return default result
        self.assertTrue(result["applied"])
        self.assertEqual(result["original_evidence"], 2)
        self.assertEqual(result["original_confidence"], 0.5)


class TestDomainConstraintPropagation(unittest.TestCase):
    """Tests for domain constraint propagation behavior."""

    def test_apply_constraints_evidence_threshold(self):
        """Test constraint application when evidence is below threshold."""
        engine = domain_adaptive_reasoning.DomainAdaptiveReasoningEngine()

        domain = domain_adaptive_reasoning.DomainDefinition(
            domain_id="constraint-test",
            max_evidence_required=5,
            min_confidence_threshold=0.7
        )
        engine.register_domain(domain)

        # Apply with insufficient evidence
        result = engine.apply_constraints("constraint-test", evidence_count=3, confidence=0.6)

        self.assertTrue(result["applied"])
        self.assertEqual(result["adjusted_evidence"], 5)  # Elevated to threshold
        self.assertEqual(result["adjusted_confidence"], 0.7)  # Elevated to threshold

    def test_apply_constraints_confidence_below_threshold(self):
        """Test constraint application when confidence is below threshold."""
        engine = domain_adaptive_reasoning.DomainAdaptiveReasoningEngine()

        domain = domain_adaptive_reasoning.DomainDefinition(
            domain_id="confidence-test",
            max_evidence_required=3,
            min_confidence_threshold=0.8
        )
        engine.register_domain(domain)

        result = engine.apply_constraints("confidence-test", evidence_count=5, confidence=0.6)

        self.assertTrue(result["applied"])
        self.assertEqual(result["adjusted_evidence"], 5)  # Unchanged
        self.assertEqual(result["adjusted_confidence"], 0.8)  # Elevated to threshold

    def test_apply_constraints_within_thresholds(self):
        """Test constraint application when within all thresholds."""
        engine = domain_adaptive_reasoning.DomainAdaptiveReasoningEngine()

        domain = domain_adaptive_reasoning.DomainDefinition(
            domain_id="within-test",
            max_evidence_required=3,
            min_confidence_threshold=0.6
        )
        engine.register_domain(domain)

        result = engine.apply_constraints("within-test", evidence_count=5, confidence=0.8)

        self.assertTrue(result["applied"])
        self.assertEqual(result["adjusted_evidence"], 5)  # Unchanged
        self.assertEqual(result["adjusted_confidence"], 0.8)  # Unchanged


class TestKnowledgeTransferRules(unittest.TestCase):
    """Tests for knowledge transfer rules."""

    def setUp(self):
        self.engine = domain_adaptive_reasoning.DomainAdaptiveReasoningEngine()

        # Register source domain with transfer enabled
        self.source_domain = domain_adaptive_reasoning.DomainDefinition(
            domain_id="source-1",
            domain_type="technical",
            transfer_strategy="abstract"
        )
        self.engine.register_domain(self.source_domain)

        # Register target domain
        self.target_domain = domain_adaptive_reasoning.DomainDefinition(
            domain_id="target-1",
            domain_type="operational"
        )
        self.engine.register_domain(self.target_domain)

    def test_transfer_knowledge_to_unknown_domain(self):
        """Test knowledge transfer to unregistered domain."""
        result = self.engine.transfer_knowledge("source-1", "nonexistent-1")

        self.assertIsNone(result)

    def test_transfer_knowledge_enabled_strategy(self):
        """Test knowledge transfer with enabled strategy."""
        result = self.engine.transfer_knowledge("source-1", "target-1")

        self.assertIsNotNone(result)
        self.assertEqual(result["from_domain"], "source-1")
        self.assertEqual(result["to_domain"], "target-1")
        self.assertEqual(result["strategy"], "abstract")
        self.assertIn("constraint_patterns", result["transferred_features"])

    def test_transfer_knowledge_disabled_strategy(self):
        """Test knowledge transfer with disabled strategy."""
        # Set source domain to none
        self.source_domain.transfer_strategy = "none"
        result = self.engine.transfer_knowledge("source-1", "target-1")

        self.assertIsNone(result)

    def test_target_domain_updated_after_transfer(self):
        """Test that target domain state is updated after transfer."""
        self.engine.transfer_knowledge("source-1", "target-1")

        state = self.engine.context.domain_states.get("target-1")
        self.assertIsNotNone(state)
        self.assertIn("knowledge_transfer_from_source-1", state.adjustment_reasons)


class TestDomainAdaptiveReasoningEndToEnd(unittest.TestCase):
    """End-to-end flow tests for domain_adaptive_reasoning."""

    def test_full_workflow(self):
        """Test complete workflow: register, adapt, transfer, apply constraints."""
        engine = domain_adaptive_reasoning.DomainAdaptiveReasoningEngine()

        # Register domains
        source_domain = domain_adaptive_reasoning.DomainDefinition(
            domain_id="source-1",
            domain_type="technical",
            complexity_level=7.0,
            safety_criticality=6.0,
            transfer_strategy="abstract"
        )
        target_domain = domain_adaptive_reasoning.DomainDefinition(
            domain_id="target-1",
            domain_type="operational"
        )
        engine.register_domain(source_domain)
        engine.register_domain(target_domain)

        # Set adaptation mode
        engine.set_adaptation_mode("active", "source-1")
        engine.set_adaptation_mode("active", "target-1")

        # Adapt reasoning for source domain
        source_state = engine.adapt_reasoning("source-1")
        self.assertIsNotNone(source_state)
        self.assertLess(source_state.confidence_adjustment, 1.0)

        # Transfer knowledge to target domain
        transfer_result = engine.transfer_knowledge("source-1", "target-1")
        self.assertIsNotNone(transfer_result)

        # Adapt reasoning for target domain
        target_state = engine.adapt_reasoning("target-1")
        self.assertIsNotNone(target_state)

        # Apply constraints
        constraint_result = engine.apply_constraints("target-1", evidence_count=2, confidence=0.5)
        self.assertTrue(constraint_result["applied"])

        # Verify final state
        final_context = engine.get_current_domain_context()
        self.assertIn("source-1", final_context.active_domains)
        self.assertIn("target-1", final_context.active_domains)


if __name__ == "__main__":
    unittest.main()
