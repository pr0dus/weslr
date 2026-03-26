# CircleForge - Commercial Module Implementation Guide

This is a template for implementing new commercial modules.

## Module Template

```python
"""
CircleForge - [ModuleName] Module
[Description of module functionality]
"""

from __future__ import annotations

import time
from typing import Dict, Any, Optional

# Import core CircleForge
from circleforge.sim import load_communicator_self
from circleForge.config import TICK_DURATION


class CommercialModule:
    """Base class for all commercial add-ons."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize with user configuration."""
        self.config = config
        self.enabled = True
        self.last_interaction = time.time()
        self.interaction_count = 0
    
    def interact(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process input and return module-specific output."""
        raise NotImplementedError("Subclasses must implement interact()")
    
    def get_features(self) -> list:
        """Return list of available features."""
        return []
    
    def get_cost(self) -> Dict[str, Any]:
        """Return pricing information."""
        return {"free_trial": True, "monthly": 299, "one_time": 999}
    
    def _update_stats(self):
        """Update interaction statistics."""
        self.interaction_count += 1
        self.last_interaction = time.time()


# Example: Medical Compliance Module Template
class MedicalCompliance(CommercialModule):
    """Medical compliance tracking and audit support."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.consent_required = config.get("consent_required", True)
        self.audit_enabled = config.get("audit_enabled", True)
        self.encryption_level = config.get("encryption_level", "AES-256")
    
    def interact(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process medical input with compliance checks."""
        self._update_stats()
        
        output = {
            "status": "ok",
            "compliance": {
                "consent_verified": self.consent_required,
                "audit_trail": self.audit_enabled,
                "encryption": self.encryption_level
            }
        }
        
        return output
    
    def get_features(self) -> list:
        """Return medical module features."""
        return [
            "Patient consent tracking",
            "HIPAA/GDPR compliance audit",
            "Medical data encryption",
            "Clinical outcome monitoring",
            "FDA documentation support"
        ]
    
    def get_cost(self) -> Dict[str, Any]:
        """Return medical module pricing."""
        return {
            "free_trial": True,
            "monthly": 299,
            "one_time": 999,
            "features": self.get_features()
        }


# Example: Education Module Template
class CurriculumAdapter(CommercialModule):
    """Education curriculum alignment and tracking."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.grade_level = config.get("grade_level", "5th")
        self.subject = config.get("subject", "Mathematics")
        self.learning_objectives = config.get("learning_objectives", [])
    
    def interact(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process educational input with curriculum alignment."""
        self._update_stats()
        
        output = {
            "status": "ok",
            "curriculum": {
                "grade_level": self.grade_level,
                "subject": self.subject,
                "objectives_aligned": len(self.learning_objectives)
            }
        }
        
        return output
    
    def get_features(self) -> list:
        """Return education module features."""
        return [
            "Age-appropriate learning paths",
            "Subject-specific curriculum alignment",
            "Progress tracking per grade",
            "Assessment generation",
            "Parent/teacher dashboard"
        ]
    
    def get_cost(self) -> Dict[str, Any]:
        """Return education module pricing."""
        return {
            "free_trial": True,
            "monthly": 199,
            "one_time": 599,
            "features": self.get_features()
        }


# Example: Space Agency Module Template
class MissionSupport(CommercialModule):
    """Space mission support and coordination."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.orbit_type = config.get("orbit_type", "LEO")
        self.crew_size = config.get("crew_size", 4)
        self.emergency_protocols = config.get("emergency_protocols", True)
    
    def interact(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process space mission input."""
        self._update_stats()
        
        output = {
            "status": "ok",
            "mission": {
                "orbit_type": self.orbit_type,
                "crew_size": self.crew_size,
                "emergency_protocols": self.emergency_protocols
            }
        }
        
        return output
    
    def get_features(self) -> list:
        """Return space module features."""
        return [
            "Orbital mechanics calculations",
            "Mission timeline planning",
            "Telemetry monitoring",
            "Emergency protocol integration",
            "Team coordination",
            "Documentation generation"
        ]
    
    def get_cost(self) -> Dict[str, Any]:
        """Return space module pricing."""
        return {
            "free_trial": True,
            "monthly": 499,
            "one_time": 1499,
            "features": self.get_features()
        }


# Example: Premium Support Module Template
class PremiumSupport(CommercialModule):
    """Premium support tier management."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.tier = config.get("tier", "enterprise")
        self.sla_hours = config.get("sla_hours", 24)
        self.priority_support = config.get("priority_support", True)
    
    def interact(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process support request."""
        self._update_stats()
        
        output = {
            "status": "ok",
            "support": {
                "tier": self.tier,
                "response_time": f"<{self.sla_hours}h",
                "priority": self.priority_support
            }
        }
        
        return output
    
    def get_features(self) -> list:
        """Return support tier features."""
        return [
            "Priority email support (24h response)",
            "Dedicated account manager",
            "Custom feature requests",
            "Training & onboarding",
            "SLA guarantees",
            "Quarterly strategy sessions"
        ]
    
    def get_cost(self) -> Dict[str, Any]:
        """Return support tier pricing."""
        return {
            "free_trial": True,
            "monthly": [99, 299, 499],  # Tiered pricing
            "features": self.get_features()
        }
```

## Module Registration

Add your module to `COMMERCIAL-FILES/__init__.py`:

```python
from circleforge.commercial.medical import MedicalCompliance
from circleforge.commercial.education import CurriculumAdapter
from circleforge.commercial.space import MissionSupport
from circleforge.commercial.premium_support import PremiumSupport

__all__ = [
    "MedicalCompliance",
    "CurriculumAdapter", 
    "MissionSupport",
    "PremiumSupport"
]
```

## Integration with CircleForge

In `CircleForge/main.py`, add commercial module support:

```python
def forge_with_commercial(action: str, commercial_module: Optional[CommercialModule] = None, **kwargs):
    """Run CircleForge with optional commercial module."""
    result = forge(action, **kwargs)
    
    if commercial_module:
        commercial_result = commercial_module.interact(result)
        result["commercial"] = commercial_result
    
    return result
```

## Testing Modules

Each module should have unit tests in `COMMERCIAL-TESTS/`:

```python
# tests/test_medical.py
from circleforge.commercial.medical import MedicalCompliance

def test_medical_compliance():
    module = MedicalCompliance({"consent_required": True, "audit_enabled": True})
    result = module.interact({"input": "test"})
    assert result["status"] == "ok"
    assert result["compliance"]["consent_verified"] == True
```

## Pricing Structure

Keep pricing consistent across modules:

| Price Point | Use Case |
|-------------|----------|
| Free trial | Evaluation period (7-14 days) |
| $99-199/month | Small organizations, individuals |
| $299-499/month | Medium organizations, teams |
| $999-1499一次性 | One-time deployment |
| Custom quote | Enterprise, agencies, large orgs |

## Support Tiers

| Tier | Price | Response Time | Features |
|------|-------|---------------|----------|
| Community | Free | 72h | Forum, docs |
| Basic | $99/month | 48h | Email, docs |
| Priority | $299/month | 24h | Email + phone |
| Enterprise | $499/month | 4h | Dedicated manager, SLA |

## Next Steps

1. Implement module class following template
2. Add unit tests
3. Document features in `COMMERCIAL-MODULES.md`
4. Add pricing to module `get_cost()` method
5. Create integration in `main.py`
6. Test end-to-end