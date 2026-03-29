# Commercial Module Structure

This document outlines the file structure for commercial add-on modules.

## Directory Layout

```
Weslr/
├── main.py                    # Core entry point
├── config.py                  # Configuration
├── sim.py                     # Simulation engine
├── behavioral_mathematics.py  # 49 trait dynamics
├── self_model.py              # Identity & self
├── perception.py              # Input processing
├── relational.py              # Relationships
├── sandbox.py                 # Agent sandbox
├── meta_reflection.py         # Meta-cognition
├── LICENSE                    # MIT + Commercial notice
├── COMMERCIAL-MODULES.md      # Module descriptions
├── COMMERCIAL-FILES/          # Commercial modules (gitignored)
│   ├── __init__.py
│   ├── medical.py             # Medical Compliance Module
│   ├── education.py           # Education Module
│   ├── space.py               # Space Agency Module
│   └── premium_support.py     # Support tier module
├── models/                    # Local models (gitignored)
├── dashboard/                 # Generated dashboard
├── memory/                    # Session memory
└── README.md
```

## Commercial Module Interface

Each commercial module follows this interface:

```python
class CommercialModule:
    """Base class for all commercial add-ons."""
    
    def __init__(self, config: dict):
        """Initialize with user configuration."""
        self.config = config
        self.enabled = True
    
    def interact(self, input_data: dict) -> dict:
        """Process input and return module-specific output."""
        raise NotImplementedError
    
    def get_features(self) -> list:
        """Return list of available features."""
        return []
    
    def get_cost(self) -> dict:
        """Return pricing information."""
        return {"free_trial": True, "monthly": 299, "one_time": 999}
```

## Medical Compliance Module

### Features
- Patient consent tracking
- HIPAA/GDPR compliance audit
- Medical data encryption
- Clinical outcome monitoring
- FDA documentation support

### Integration Example
```python
from circleforge.medical import MedicalCompliance

# Initialize
medical = MedicalCompliance(
    consent_required=True,
    audit_enabled=True,
    encryption_level="AES-256"
)

# Use with Weslr
circle.forge(
    action="communicator-message",
    medical_compliance=medical
)
```

## Education Module

### Features
- Age-appropriate learning paths
- Subject-specific curriculum alignment
- Progress tracking per grade
- Assessment generation
- Parent/teacher dashboard

### Integration Example
```python
from circleforge.education import CurriculumAdapter

# Initialize for specific grade
curriculum = CurriculumAdapter(
    grade_level="5th",
    subject="Mathematics",
    learning_objectives=["fractions", "decimals"]
)

# Use with Weslr
circle.forge(
    action="educator-assistant",
    curriculum=curriculum
)
```

## Space Agency Module

### Features
- Orbital mechanics calculations
- Mission timeline planning
- Telemetry monitoring
- Emergency protocol integration
- Team coordination
- Documentation generation

### Integration Example
```python
from circleforge.space import MissionSupport

# Initialize for specific mission
mission = MissionSupport(
    orbit_type="LEO",
    crew_size=4,
    emergency_protocols=True
)

# Use with Weslr
circle.forge(
    action="mission-control",
    mission=mission
)
```

## Premium Support Tier

### Features
- Priority email support (24h response)
- Dedicated account manager
- Custom feature requests
- Training & onboarding
- SLA guarantees
- Quarterly strategy sessions

### Integration Example
```python
from circleforge.premium_support import PremiumSupport

# Initialize support tier
support = PremiumSupport(
    tier="enterprise",
    sla_hours=24,
    priority_support=True
)

# Use with Weslr
circle.forge(
    action="support-connection",
    support_tier=support
)
```

## Commercial Module Development

### Adding New Modules
1. Create module file in `COMMERCIAL-FILES/`
2. Implement `CommercialModule` interface
3. Add to `COMMERCIAL-FILES/__init__.py`
4. Update `COMMERCIAL-MODULES.md` with feature description
5. Add to pricing table

### Module Requirements
- Must extend `CommercialModule` base class
- Must have `interact()`, `get_features()`, `get_cost()` methods
- Should integrate with Weslr core
- Must document pricing and use cases
- Code should be clean, documented, and tested

## Licensing Notice

This Weslr installation includes commercial modules that extend the free core.

- **Core**: MIT License (free, attribution required)
- **Modules**: Proprietary Commercial License (paid, no attribution)
- **Full commercial use**: Contact for proprietary license

See `LICENSE` for full license text.
See `COMMERCIAL-MODULES.md` for module descriptions.