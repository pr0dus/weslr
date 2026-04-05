"""Weslr Model Adapter: OpenAI-Compatible Provider (v1)

OpenAI-compatible model adapter for Weslr platform.
This adapter provides access to any OpenAI-compatible API endpoint.

Architecture: Layer 2 of 3-layer adapter architecture
Purpose: Provider-agnostic AI model interaction via OpenAI-compatible APIs

Adapter Pattern:
  - ModelAdapter base class defines interface
  - OpenAICompatibleModel implements OpenAI-compatible API interaction
  - Weslr core uses adapter, never calls provider API directly

API Endpoint Configuration:
  - Default endpoint: http://localhost:11434/v1/chat/completions (Ollama)
  - Override via environment: OPENAI_COMPATIBLE_ENDPOINT
  - API key via environment: OPENAI_COMPATIBLE_API_KEY (optional)

Note: This is a stub reference implementation. Real use requires:
  - Actual OpenAI-compatible API endpoint
  - Valid API key (if required by provider)
  - Network access to the API endpoint
"""

from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional

from ..safety import scrub_secrets
from ..contracts import RunResult
from . import ModelAdapter


class OpenAICompatibleModel(ModelAdapter):
    """OpenAI-compatible model adapter for Weslr.
    
    This adapter works with any OpenAI-compatible API endpoint,
    including Ollama, LM Studio, vLLM, and other compatible services.
    
    Provider Identity:
    - provider_name(): Returns provider name from config or default
    - Model ID is configurable via environment or constructor
    
    API Configuration:
    - Endpoint: OPENAI_COMPATIBLE_ENDPOINT (default: http://localhost:11434/v1/chat/completions)
    - API Key: OPENAI_COMPATIBLE_API_KEY (optional)
    
    Note: This is a stub. Real API integration requires valid endpoint and API key.
    """
    
    # Default OpenAI-compatible endpoint
    DEFAULT_ENDPOINT = "http://localhost:11434/v1/chat/completions"
    
    def __init__(
        self,
        provider: str = None,
        model_id: str = None,
        endpoint: str = None,
        api_key: str = None
    ):
        """Initialize OpenAI-compatible model adapter.
        
        Args:
            provider: Provider name (e.g., 'openai', 'ollama', 'custom')
            model_id: Model identifier (e.g., 'gpt-4', 'llama3', 'mistral')
            endpoint: API endpoint URL (override from env)
            api_key: API key for authentication (override from env)
        """
        # Provider name
        self._provider = provider or os.getenv("OPENAI_COMPATIBLE_PROVIDER", "openai")
        
        # Model ID
        self._model_id = model_id or os.getenv("OPENAI_COMPATIBLE_MODEL", "gpt-3.5-turbo")
        
        # Endpoint
        self._endpoint = endpoint or os.getenv("OPENAI_COMPATIBLE_ENDPOINT", self.DEFAULT_ENDPOINT)
        
        # API Key
        self._api_key = api_key or os.getenv("OPENAI_COMPATIBLE_API_KEY")
        
        # Creation timestamp for debugging
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
        """Send messages to the OpenAI-compatible API.
        
        Note: This is a stub implementation. Real API integration requires:
        - Valid endpoint URL
        - Valid API key (if required)
        - Network access to the API
        
        For now, this returns a synthetic response for testing.
        
        Args:
            messages: List of message dicts with role/content
            tools: Optional list of tool schemas for tool calling
            system_prompt: Optional system prompt to inject
            **kwargs: Provider-specific arguments (temperature, max_tokens, etc.)
        
        Returns:
            Response dict matching OpenAI API format
        """
        # Build the response data (placeholder for now)
        response_data = {
            "id": f"chatcmpl_{self._created_at}_{int(time.time() * 1000) % 100000}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": self._model_id,
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "This is a placeholder response from OpenAICompatibleModel stub.",
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
        """Parse and normalize a provider response to Weslr format.
        
        This expects OpenAI-compatible response format and normalizes it.
        
        Args:
            response: Raw response from send_message
        
        Returns:
            Normalized response with:
            - content: str
            - tool_calls: List[Dict]
            - provider_data: Dict (raw response, if available)
        """
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
        """Whether this model supports native tool calling.
        
        OpenAI-compatible APIs typically support tool calling.
        Set OPENAI_COMPATIBLE_SUPPORTS_TOOL_CALLING=false to disable.
        """
        env_value = os.getenv("OPENAI_COMPATIBLE_SUPPORTS_TOOL_CALLING", "true")
        return env_value.lower() not in ("false", "0", "no")
    
    def supports_vision(self) -> bool:
        """Whether this model supports image input.
        
        Set OPENAI_COMPATIBLE_SUPPORTS_VISION=true to enable.
        """
        env_value = os.getenv("OPENAI_COMPATIBLE_SUPPORTS_VISION", "false")
        return env_value.lower() in ("true", "1", "yes")
    
    def supports_system_prompt(self) -> bool:
        """Whether this model supports system prompt injection.
        
        OpenAI-compatible APIs typically support system prompts.
        Set OPENAI_COMPATIBLE_SUPPORTS_SYSTEM_PROMPT=false to disable.
        """
        env_value = os.getenv("OPENAI_COMPATIBLE_SUPPORTS_SYSTEM_PROMPT", "true")
        return env_value.lower() not in ("false", "0", "no")
    
    def get_max_tokens(self) -> int:
        """Return maximum tokens supported by this model.
        
        Override via OPENAI_COMPATIBLE_MAX_TOKENS environment variable.
        """
        env_value = os.getenv("OPENAI_COMPATIBLE_MAX_TOKENS")
        if env_value:
            try:
                return int(env_value)
            except ValueError:
                pass
        return 128000  # Default reasonable value for OpenAI-compatible models
    
    def get_context_window(self) -> int:
        """Return context window size in tokens.
        
        Override via OPENAI_COMPATIBLE_CONTEXT_WINDOW environment variable.
        """
        env_value = os.getenv("OPENAI_COMPATIBLE_CONTEXT_WINDOW")
        if env_value:
            try:
                return int(env_value)
            except ValueError:
                pass
        return 200000  # Default reasonable value
    
    # ===== Utility Methods =====
    
    def get_model_id(self) -> str:
        """Return the model identifier."""
        return self._model_id
    
    def get_endpoint(self) -> str:
        """Return the API endpoint URL."""
        return self._endpoint
    
    def get_created_at(self) -> int:
        """Return when this adapter was created."""
        return self._created_at
    
    # ===== Debug Methods =====
    
    def get_config(self) -> Dict[str, Any]:
        """Get current configuration for debugging."""
        return {
            "provider": self._provider,
            "model_id": self._model_id,
            "endpoint": self._endpoint,
            "api_key_set": self._api_key is not None,
            "supports_tool_calling": self.supports_tool_calling(),
            "supports_vision": self.supports_vision(),
            "supports_system_prompt": self.supports_system_prompt(),
            "max_tokens": self.get_max_tokens(),
            "context_window": self.get_context_window(),
        }


# Convenience factory functions
def create_openai_compatible(
    provider: str = "openai",
    model_id: str = "gpt-3.5-turbo",
    endpoint: str = None,
    api_key: str = None
) -> ModelAdapter:
    """Create an OpenAI-compatible model adapter.
    
    Args:
        provider: Provider name (e.g., 'openai', 'ollama', 'custom')
        model_id: Model identifier (e.g., 'gpt-4', 'llama3')
        endpoint: API endpoint URL (optional, uses env or default)
        api_key: API key (optional, uses env if not provided)
    
    Returns:
        OpenAICompatibleModel adapter instance
    """
    return OpenAICompatibleModel(
        provider=provider,
        model_id=model_id,
        endpoint=endpoint,
        api_key=api_key
    )


def create_ollama_adapter(
    model_id: str = "llama3",
    endpoint: str = "http://localhost:11434/v1/chat/completions"
) -> ModelAdapter:
    """Create an Ollama-specific adapter (OpenAI-compatible).
    
    Args:
        model_id: Ollama model name (e.g., 'llama3', 'mistral')
        endpoint: Ollama API endpoint (default: standard Ollama port)
    
    Returns:
        OpenAICompatibleModel adapter configured for Ollama
    """
    return OpenAICompatibleModel(
        provider="ollama",
        model_id=model_id,
        endpoint=endpoint,
        api_key=None  # Ollama typically doesn't require API key
    )
