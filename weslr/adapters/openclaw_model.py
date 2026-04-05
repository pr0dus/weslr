"""Weslr Model Adapter: OpenClaw Reference Implementation (v1)

OpenClaw model adapter for Weslr platform.
This adapter demonstrates the ModelAdapter interface.

Architecture: Layer 2 of 3-layer adapter architecture
Purpose: Provider-agnostic AI model interaction

Note: This is a placeholder. Real provider implementations (Claude, DeepSeek, etc.)
will subclass ModelAdapter and implement actual API calls.

Adapter Pattern:
  - ModelAdapter base class defines interface
  - OpenClawModel implements OpenClaw-specific model interaction
  - Weslr core uses adapter, never calls provider API directly
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from ..safety import scrub_secrets
from . import ModelAdapter


class OpenClawModel(ModelAdapter):
    """OpenClaw placeholder model adapter.
    
    This is a minimal implementation that demonstrates the ModelAdapter interface.
    It provides stub methods for future provider-specific implementations.
    
    Real implementations should override:
    - send_message() to call actual AI provider API
    - parse_response() to normalize provider responses
    - Capability flags based on actual provider capabilities
    """
    
    def __init__(self, provider: str = "openclaw", model_id: str = "placeholder"):
        """Initialize model adapter with provider identity."""
        self._provider = provider
        self._model_id = model_id
        self._created_at = int(time.time())
    
    # ===== ModelAdapter Interface =====
    
    def provider_name(self) -> str:
        """Return the provider name."""
        return self._provider
    
    def send_message(
        self,
        messages: List[Dict[str, Any]],
        tools: List[Dict[str, Any]] = None,
        system_prompt: str = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Send messages to the model and receive response.
        
        This is a placeholder implementation. Real providers will:
        - Call their API endpoint
        - Parse the response
        - Return normalized result
        
        For now, this returns a synthetic response for testing.
        """
        # Build the response data (placeholder)
        response_data = {
            "id": f"msg_{self._created_at}_{int(time.time() * 1000) % 100000}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": self._model_id,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "This is a placeholder response from OpenClawModel.",
                        "tool_calls": []
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": len(str(messages)),
                "completion_tokens": 10,
                "total_tokens": len(str(messages)) + 10
            }
        }
        
        # If tools were provided and tool calling is supported, include placeholder
        if tools and self.supports_tool_calling():
            response_data["choices"][0]["message"]["tool_calls"] = [
                {
                    "id": f"call_{int(time.time() * 1000) % 100000}",
                    "type": "function",
                    "function": {
                        "name": tools[0]["name"] if tools else "unknown",
                        "arguments": "{}"
                    }
                }
            ]
            response_data["choices"][0]["finish_reason"] = "tool_calls"
        
        return response_data
    
    def parse_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Parse and normalize a provider response to Weslr format."""
        # Extract content from first choice
        choices = response.get("choices", [])
        if not choices:
            return {
                "content": "",
                "tool_calls": [],
                "provider_data": response
            }
        
        choice = choices[0]
        message = choice.get("message", {})
        
        return {
            "content": message.get("content", ""),
            "tool_calls": message.get("tool_calls", []),
            "provider_data": response
        }
    
    def _scrub_sensitive(self, text: str) -> str:
        """Scrub sensitive data from text."""
        return scrub_secrets(text)
    
    # ===== Capability Flags =====
    
    def supports_tool_calling(self) -> bool:
        """Whether this model supports native tool calling."""
        return True
    
    def supports_vision(self) -> bool:
        """Whether this model supports image input."""
        return False
    
    def supports_system_prompt(self) -> bool:
        """Whether this model supports system prompt injection."""
        return True
    
    def get_max_tokens(self) -> int:
        """Return maximum tokens supported by this model."""
        return 128000
    
    def get_context_window(self) -> int:
        """Return context window size in tokens."""
        return 200000
    
    # ===== Debug/Utility Methods =====
    
    def get_model_id(self) -> str:
        """Return the model identifier."""
        return self._model_id
    
    def get_created_at(self) -> int:
        """Return when this adapter was created."""
        return self._created_at


# Convenience factory functions
def create_model(provider: str = "openclaw", model_id: str = "placeholder") -> ModelAdapter:
    """Create a model adapter instance.
    
    This is a convenience function for getting a model adapter.
    """
    return OpenClawModel(provider=provider, model_id=model_id)


def create_default_model() -> ModelAdapter:
    """Create a default model adapter.
    
    This is a convenience function for getting a default model adapter.
    """
    return OpenClawModel()
