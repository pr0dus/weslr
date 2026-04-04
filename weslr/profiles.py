"""Weslr Deployment Profiles (v1)

Governance contract for Weslr deployment modes.
Each profile defines:
- Security posture
- Self-improvement visibility
- Feature access
- Audit requirements

Only ONE canonical active profile should be active at a time.
"""

from __future__ import annotations

import os
from enum import Enum
from typing import Dict, List, Optional


# ============================================================================
# PROFILE DEFINITIONS
# ============================================================================

class Profile(Enum):
    """Deployment profile enum."""
    
    PUBLIC_TEST = "public_test"
    MANAGED_CUSTOMER = "managed_customer"
    OWNER_SOVEREIGN = "owner_sovereign"
    DEVELOPMENT = "development"


class ProfileConfig:
    """Configuration for a deployment profile."""
    
    def __init__(
        self,
        name: str,
        public_mode: bool = True,
        self_improvement_visible_to_public: bool = False,
        read_only_tools: bool = True,
        max_input_length: int = 10000,
        max_response_size: int = 102400,
        rate_limit_requests: int = 10,
        rate_limit_window_minutes: int = 1,
        debug_mode: bool = False,
    ):
        self.name = name
        self.public_mode = public_mode
        self.self_improvement_visible_to_public = self_improvement_visible_to_public
        self.read_only_tools = read_only_tools
        self.max_input_length = max_input_length
        self.max_response_size = max_response_size
        self.rate_limit_requests = rate_limit_requests
        self.rate_limit_window_minutes = rate_limit_window_minutes
        self.debug_mode = debug_mode
    
    def to_dict(self) -> Dict[str, any]:
        return {
            "name": self.name,
            "public_mode": self.public_mode,
            "self_improvement_visible_to_public": self.self_improvement_visible_to_public,
            "read_only_tools": self.read_only_tools,
            "max_input_length": self.max_input_length,
            "max_response_size": self.max_response_size,
            "rate_limit_requests": self.rate_limit_requests,
            "rate_limit_window_minutes": self.rate_limit_window_minutes,
            "debug_mode": self.debug_mode,
        }
    
    def to_env_vars(self) -> Dict[str, str]:
        """Convert to environment variable strings."""
        return {
            "WESLR_PUBLIC_MODE": str(self.public_mode).lower(),
            "WESLR_SELF_IMPROVEMENT_PUBLIC": str(self.self_improvement_visible_to_public).lower(),
            "WESLR_READ_ONLY_TOOLS": str(self.read_only_tools).lower(),
            "WESLR_MAX_INPUT_LENGTH": str(self.max_input_length),
            "WESLR_MAX_RESPONSE_SIZE": str(self.max_response_size),
            "WESLR_RATE_LIMIT_REQUESTS": str(self.rate_limit_requests),
            "WESLR_RATE_LIMIT_WINDOW_MINUTES": str(self.rate_limit_window_minutes),
            "WESLR_DEBUG_MODE": str(self.debug_mode).lower(),
        }


# ============================================================================
# PROFILE DEFINITIONS
# ============================================================================

PROFILES: Dict[str, ProfileConfig] = {
    Profile.PUBLIC_TEST.value: ProfileConfig(
        name="public_test",
        public_mode=True,
        self_improvement_visible_to_public=False,
        read_only_tools=True,
        max_input_length=10000,
        max_response_size=102400,
        rate_limit_requests=10,
        rate_limit_window_minutes=1,
        debug_mode=False,
    ),
    Profile.MANAGED_CUSTOMER.value: ProfileConfig(
        name="managed_customer",
        public_mode=True,
        self_improvement_visible_to_public=False,
        read_only_tools=True,
        max_input_length=10000,
        max_response_size=102400,
        rate_limit_requests=50,
        rate_limit_window_minutes=5,
        debug_mode=False,
    ),
    Profile.OWNER_SOVEREIGN.value: ProfileConfig(
        name="owner_sovereign",
        public_mode=False,
        self_improvement_visible_to_public=False,
        read_only_tools=False,
        max_input_length=100000,
        max_response_size=1024000,
        rate_limit_requests=1000,
        rate_limit_window_minutes=60,
        debug_mode=False,
    ),
    Profile.DEVELOPMENT.value: ProfileConfig(
        name="development",
        public_mode=False,
        self_improvement_visible_to_public=False,
        read_only_tools=False,
        max_input_length=1000000,
        max_response_size=10485760,
        rate_limit_requests=10000,
        rate_limit_window_minutes=60,
        debug_mode=True,
    ),
}


# ============================================================================
# CURRENT PROFILE
# ============================================================================

def get_active_profile() -> ProfileConfig:
    """Get the currently active profile.
    
    Priority order:
    1. Environment variable: WESLR_ACTIVE_PROFILE
    2. Default: public_test
    """
    env_profile = os.getenv("WESLR_ACTIVE_PROFILE")
    if env_profile and env_profile in PROFILES:
        return PROFILES[env_profile]
    
    return PROFILES[Profile.PUBLIC_TEST.value]


def get_profile_by_name(name: str) -> Optional[ProfileConfig]:
    """Get profile by name."""
    return PROFILES.get(name)


def get_profile_list() -> List[str]:
    """Get list of available profile names."""
    return list(PROFILES.keys())


def is_public_mode() -> bool:
    """Check if current profile is in public mode."""
    return get_active_profile().public_mode


def is_self_improvement_public() -> bool:
    """Check if self-improvement suggestions are visible to public."""
    return get_active_profile().self_improvement_visible_to_public


def get_profile_summary() -> Dict[str, any]:
    """Get summary of current profile."""
    profile = get_active_profile()
    return {
        "active_profile": profile.name,
        "public_mode": profile.public_mode,
        "self_improvement_visible_to_public": profile.self_improvement_visible_to_public,
        "read_only_tools": profile.read_only_tools,
        "debug_mode": profile.debug_mode,
    }
