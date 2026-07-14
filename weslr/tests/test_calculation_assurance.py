"""Tests for calculation_assurance.py."""

import hashlib
import json
import sys
import unittest

sys.path.insert(0, ".")

from weslr.modules.calculation_assurance import (
    CalculationInput, CalculationResult, VerificationResult,
    InvariantResult, CalculationCertificate, make_certificate,
    determine_final_status, VERIFIED, REJECTED_BY_INVARIANT,
    PROPOSER_VERIFIER_DISAGREEMENT, VERIFIER_UNAVAILABLE,
    INVALID_INPUT, INSUFFICIENT_EVIDENCE,
    ABSTAIN_DUE_TO_VERIFICATION_DISAGREEMENT,
)


class TestStatusConstants(unittest.TestCase):
    def test_all_statuses_defined(self):
        expected = {
            VERIFIED, REJECTED_BY_INVARIANT, PROPOSER_VERIFIER_DISAGREEMENT,
            VERIFIER_UNAVAILABLE, INVALID_INPUT, INSUFFICIENT_EVIDENCE,
            ABSTAIN_DUE_TO_VERIFICATION_DISAGREEMENT,
        }
        self.assertEqual(len(expected), 7)


class TestInvariantResult(unittest.TestCase):
    def test_passed_invariant(self):
        ir = InvariantResult(invariant_name="test", passed=True, details={"value": 42})
        d = ir.to_dict()
        self.assertTrue(d["passed"])
        self.assertEqual(d["invariant_name"], "test")
        self.assertEqual(d["details"]["value"], 42)

    def test_failed_invariant(self):
        ir = InvariantResult(invariant_name="test", passed=False)
        d = ir.to_dict()
        self.assertFalse(d["passed"])


class TestDetermineFinalStatus(unittest.TestCase):
    def test_verified(self):
        status = determine_final_status(VERIFIED, VERIFIED, [], True)
        self.assertEqual(status, VERIFIED)

    def test_rejected_by_invariant(self):
        ir = InvariantResult(invariant_name="residual", passed=False)
        status = determine_final_status(VERIFIED, VERIFIED, [ir], True)
        self.assertEqual(status, REJECTED_BY_INVARIANT)

    def test_abstain_on_disagreement(self):
        status = determine_final_status(VERIFIED, VERIFIED, [], False)
        self.assertEqual(status, ABSTAIN_DUE_TO_VERIFICATION_DISAGREEMENT)

    def test_verifier_unavailable(self):
        status = determine_final_status(VERIFIED, VERIFIER_UNAVAILABLE, [], True)
        self.assertEqual(status, VERIFIER_UNAVAILABLE)

    def test_invalid_input(self):
        status = determine_final_status(INVALID_INPUT, VERIFIED, [], True)
        self.assertEqual(status, INVALID_INPUT)

    def test_insufficient_evidence(self):
        status = determine_final_status("unknown", "unknown", [], True)
        self.assertEqual(status, INSUFFICIENT_EVIDENCE)


class TestCertificateHash(unittest.TestCase):
    def test_deterministic_hash(self):
        cert1 = make_certificate(
            calculation_id="test-001",
            calculation_type="test",
            normalized_inputs={"a": 1, "b": 2},
            proposer_name="proposer",
            proposer_result={"balanced": True},
            verifier_name="verifier",
            verifier_result={"balanced": True},
            invariant_results=[InvariantResult("residual", True)],
            agreement=True,
            final_status=VERIFIED,
            exact_arithmetic=True,
            tool_versions={"python": "3.13"},
            source_paths=["test.py"],
            source_hashes=["abc"],
        )
        cert2 = make_certificate(
            calculation_id="test-001",
            calculation_type="test",
            normalized_inputs={"a": 1, "b": 2},
            proposer_name="proposer",
            proposer_result={"balanced": True},
            verifier_name="verifier",
            verifier_result={"balanced": True},
            invariant_results=[InvariantResult("residual", True)],
            agreement=True,
            final_status=VERIFIED,
            exact_arithmetic=True,
            tool_versions={"python": "3.13"},
            source_paths=["test.py"],
            source_hashes=["abc"],
        )
        self.assertEqual(cert1.certificate_sha256, cert2.certificate_sha256)

    def test_changed_input_changes_hash(self):
        cert1 = make_certificate(
            calculation_id="test-001",
            calculation_type="test",
            normalized_inputs={"a": 1},
            proposer_name="proposer",
            proposer_result={"balanced": True},
            verifier_name="verifier",
            verifier_result={"balanced": True},
            invariant_results=[InvariantResult("residual", True)],
            agreement=True,
            final_status=VERIFIED,
            exact_arithmetic=True,
            tool_versions={"python": "3.13"},
            source_paths=["test.py"],
            source_hashes=["abc"],
        )
        cert2 = make_certificate(
            calculation_id="test-001",
            calculation_type="test",
            normalized_inputs={"a": 2},  # Changed
            proposer_name="proposer",
            proposer_result={"balanced": True},
            verifier_name="verifier",
            verifier_result={"balanced": True},
            invariant_results=[InvariantResult("residual", True)],
            agreement=True,
            final_status=VERIFIED,
            exact_arithmetic=True,
            tool_versions={"python": "3.13"},
            source_paths=["test.py"],
            source_hashes=["abc"],
        )
        self.assertNotEqual(cert1.certificate_sha256, cert2.certificate_sha256)

    def test_certificate_to_dict_includes_hash(self):
        cert = make_certificate(
            calculation_id="test-001",
            calculation_type="test",
            normalized_inputs={},
            proposer_name="proposer",
            proposer_result={},
            verifier_name="verifier",
            verifier_result={},
            invariant_results=[],
            agreement=True,
            final_status=VERIFIED,
            exact_arithmetic=True,
            tool_versions={},
            source_paths=[],
            source_hashes=[],
        )
        d = cert.to_dict()
        self.assertIn("certificate_sha256", d)
        self.assertTrue(len(d["certificate_sha256"]) > 0)

    def test_repeated_runs_identical(self):
        results = []
        for _ in range(5):
            cert = make_certificate(
                calculation_id="test-002",
                calculation_type="test",
                normalized_inputs={"x": 10},
                proposer_name="p",
                proposer_result={"ok": True},
                verifier_name="v",
                verifier_result={"ok": True},
                invariant_results=[InvariantResult("r", True)],
                agreement=True,
                final_status=VERIFIED,
                exact_arithmetic=True,
                tool_versions={"py": "3"},
                source_paths=["a.py"],
                source_hashes=["h"],
            )
            results.append(cert.certificate_sha256)
        for i in range(1, len(results)):
            self.assertEqual(results[0], results[i])


class TestCalculationInput(unittest.TestCase):
    def test_normalized_json(self):
        inp = CalculationInput(
            calculation_type="test",
            parameters={"a": 1, "b": 2},
            formulas=["CaSc2TiO6"],
        )
        j1 = inp.normalized_json()
        j2 = inp.normalized_json()
        self.assertEqual(j1, j2)

    def test_json_parseable(self):
        inp = CalculationInput(calculation_type="test")
        j = inp.normalized_json()
        parsed = json.loads(j)
        self.assertEqual(parsed["calculation_type"], "test")


if __name__ == "__main__":
    unittest.main()
