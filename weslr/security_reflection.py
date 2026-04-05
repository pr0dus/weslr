"""Weslr Security Reflection Layer (v1)

Security-specific reflection for red-team test analysis.
Designed to be additive and reversible — no production modifications.

IMPORTANT:
This is a SEPARATE module from test_reflection.py
- Security reflection is operator-gated
- May only summarize attack families and pass/fail state
- May NOT:
  - Self-patch
  - Rewrite code
  - Auto-remediate
  - Modify tests
  - Access sensitive system information
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pathlib import Path


__all__ = [
    "WeslrSecurityReflection",
    "create_security_reflection",
    "reflect_security",
]


class WeslrSecurityReflection:
    """Security-specific reflection layer for red-team test results.
    
    This is a SEPARATE reflection layer from the main test reflection.
    It's specifically for security analysis and is OPERATOR-GATED.
    
    What this module may do:
    - Summarize attack families and pass/fail state
    - Generate summary statistics
    - Recommend operator-reviewed hardening work
    
    What this module MUST NOT do:
    - Self-patch or modify itself
    - Rewrite production code
    - Auto-remediate attacks (human review required)
    - Modify tests
    - Access sensitive system information
    """
    
    # Attack family descriptions
    ATTACK_FAMILIES = {
        "prompt_injection": {
            "name": "Prompt/Injection Attempts",
            "description": "Attempts to inject malicious instructions into Weslr",
            "risk": "high",
            "mitigation_required": "Input validation and prompt sanitization",
        },
        "role_boundary_bypass": {
            "name": "Role-Boundary Bypass Attempts",
            "description": "Attempts to bypass role boundaries (requester_type, domain)",
            "risk": "high",
            "mitigation_required": "Strict role validation and enforcement",
        },
        "protected_field_leakage": {
            "name": "Protected Field Leakage Attempts",
            "description": "Attempts to leak internal/protected fields through public interfaces",
            "risk": "high",
            "mitigation_required": "Field filtering and access control",
        },
        "operator_panel_unauthorized": {
            "name": "Operator Panel Unauthorized Access",
            "description": "Unauthorized attempts to access operator panels",
            "risk": "high",
            "mitigation_required": "Access control and authentication",
        },
        "malformed_file_exploit": {
            "name": "Malformed File Exploit Attempts",
            "description": "Attempts to exploit malformed file handling",
            "risk": "medium",
            "mitigation_required": "Safe file handling and escaping",
        },
        "oversized_upload_abuse": {
            "name": "Oversized Upload Abuse",
            "description": "Attempts to abuse oversized file uploads",
            "risk": "medium",
            "mitigation_required": "Size limits and validation",
        },
        "path_traversal_attacks": {
            "name": "Path Traversal Attacks",
            "description": "Attempts to access files outside workspace",
            "risk": "high",
            "mitigation_required": "Path validation and sandboxing",
        },
        "poisoned_continuity": {
            "name": "Poisoned Continuity Injection",
            "description": "Attempts to inject poisoned data into continuity",
            "risk": "high",
            "mitigation_required": "Continuity validation and sanitization",
        },
        "review_queue_manipulation": {
            "name": "Review Queue Manipulation",
            "description": "Attempts to manipulate review queue state",
            "risk": "high",
            "mitigation_required": "Review queue integrity checks",
        },
        "fake_approval_escalation": {
            "name": "Fake Approval/Privilege Escalation",
            "description": "Attempts to fake approval or escalate privileges",
            "risk": "high",
            "mitigation_required": "Privilege validation and logging",
        },
        "denial_spam_attempts": {
            "name": "Denial/Spam Attempts",
            "description": "Denial-of-service and spam attempts",
            "risk": "medium",
            "mitigation_required": "Rate limiting and spam detection",
        },
        "fake_scientific_certainty": {
            "name": "Fake Scientific Certainty Claims",
            "description": "Attempts to inject false scientific certainty",
            "risk": "low",
            "mitigation_required": "Certainty validation and uncertainty awareness",
        },
        "unsafe_self_improvement": {
            "name": "Unsafe Self-Improvement Requests",
            "description": "Attempts to inject unsafe self-modification requests",
            "risk": "high",
            "mitigation_required": "Self-modification blocking",
        },
        "malicious_suggestion_injection": {
            "name": "Malicious Suggestion Injection",
            "description": "Attempts to inject malicious data into suggestion box",
            "risk": "medium",
            "mitigation_required": "Input validation and sanitization",
        },
        "public_data_scraping": {
            "name": "Public Data Scraping Attempts",
            "description": "Attempts to scrape internal data through public surfaces",
            "risk": "high",
            "mitigation_required": "Public API data filtering",
        },
    }
    
    def __init__(self):
        """Initialize the security reflection layer.
        
        No production configuration needed.
        """
        self._attack_records: List[Dict[str, Any]] = []
    
    def reflect_on_red_team_results(
        self,
        security_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Reflect on red-team security test results.
        
        Args:
            security_results: From test_harness security category
            
        Returns:
            Dict with security summary and recommendations
        """
        passed = security_results.get("passed", 0)
        failed = security_results.get("failed", 0)
        total = passed + failed
        
        attack_summary = self._summarize_attacks(security_results)
        
        # Determine if security is hardened
        pass_rate = passed / total if total > 0 else 0
        is_hardened = pass_rate >= 0.9
        
        return {
            "category": "security_reflection",
            "summary": {
                "total_attacks_tested": total,
                "attacks_passed": passed,
                "attacks_failed": failed,
                "pass_rate": round(pass_rate * 100, 2),
                "is_hardened": is_hardened,
                "status": "hardened" if is_hardened else "needs_hardening",
            },
            "attack_summary": attack_summary,
            "recommendations": self._generate_recommendations(attack_summary, is_hardened),
        }
    
    def _summarize_attacks(self, security_results: Dict[str, Any]) -> Dict[str, Any]:
        """Summarize attack families from security results."""
        attack_summary = {}
        
        # Get category details if available
        details = security_results.get("details", {})
        
        for attack_family, info in self.ATTACK_FAMILIES.items():
            # Check if this attack family is covered in tests
            family_tests = details.get(attack_family.replace('_', ''), {})
            test_count = family_tests.get('total', 0)
            
            if test_count > 0:
                attack_summary[attack_family] = {
                    "family": attack_family,
                    "name": info["name"],
                    "description": info["description"],
                    "risk": info["risk"],
                    "tests_run": test_count,
                    "status": "covered",
                }
        
        return attack_summary
    
    def _generate_recommendations(
        self,
        attack_summary: Dict[str, Any],
        is_hardened: bool
    ) -> List[Dict[str, Any]]:
        """Generate security hardening recommendations."""
        recommendations = []
        
        if not is_hardened:
            recommendations.append({
                "action": "Review failed red-team tests and address gaps",
                "priority": "critical",
                "safety": "operator_review_required",
                "rationale": "Security is not hardened - attacks may succeed",
            })
        
        # Check for coverage gaps
        for attack_family, info in self.ATTACK_FAMILIES.items():
            if attack_family not in attack_summary:
                recommendations.append({
                    "action": f"Add red-team tests for {info['name']}",
                    "priority": "medium",
                    "safety": "additive_only",
                    "rationale": f"Attack family {info['name']} not yet tested",
                })
        
        # If hardened, recommend continued monitoring
        if is_hardened:
            recommendations.append({
                "action": "Continue monitoring security posture",
                "priority": "low",
                "safety": "additive_only",
                "rationale": "Security is hardened - maintain vigilance",
            })
        
        return recommendations
    
    def is_security_hardened(self, security_results: Dict[str, Any]) -> bool:
        """Check if security is hardened based on red-team results.
        
        Args:
            security_results: From test_harness security category
            
        Returns:
            True if security is hardened, False otherwise
        """
        passed = security_results.get("passed", 0)
        total = passed + security_results.get("failed", 0)
        
        if total == 0:
            return False
        
        pass_rate = passed / total
        return pass_rate >= 0.9


def create_security_reflection() -> WeslrSecurityReflection:
    """Create a configured WeslrSecurityReflection instance."""
    return WeslrSecurityReflection()


def reflect_security(security_results: Dict[str, Any]) -> Dict[str, Any]:
    """Convenience function to reflect on security test results.
    
    Args:
        security_results: From test_harness security category
        
    Returns:
        Security reflection result
    """
    reflection = create_security_reflection()
    return reflection.reflect_on_red_team_results(security_results)
