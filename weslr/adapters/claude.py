"""Weslr Model Adapter: Claude Provider (v1)

Claude model adapter for Weslr platform.
This adapter provides access to Anthropic's Claude models.

Architecture: Layer 2 of 3-layer adapter architecture
Purpose: Provider-agnostic AI model interaction via Claude API

Adapter Pattern:
  - ModelAdapter base class defines interface
  - ClaudeModel implements Claude-specific API interaction
  - Weslr core uses adapter, never calls provider API directly

API Configuration:
  - Endpoint: https://api.anthropic.com/v1/messages
  - API Key: ANTHROPIC_API_KEY environment variable
  - Default model: claude-3-5-sonnet-20241022

Note: This is a stub reference implementation. Real use requires:
  - Valid Anthropic API key
  - Network access to Anthropic API
  - Claude API integration (not implemented yet)

Claude-Specific Considerations:
  - Claude uses different API endpoint structure than OpenAI
  - Claude has specific tool calling format
  - Claude has different token calculation
  - Claude supports system prompts as top-level parameter
"""

from __future__ import annotations

import os
import time
from typing import Any, Dict, List, Optional

from ..safety import scrub_secrets
from ..contracts import RunResult
from . import ModelAdapter


class ClaudeModel(ModelAdapter):
    """Claude model adapter for Weslr.
    
    This adapter works with Anthropic's Claude API (v1/messages).
    
    Provider Identity:
    - provider_name(): Returns 'claude'
    - Model ID defaults to claude-3-5-sonnet-20241022
    
    API Configuration:
    - API Key: ANTHROPIC_API_KEY environment variable (required)
    - Default Model: claude-3-5-sonnet-20241022
    
    Claude-Specific Features:
    - System prompts via top-level 'system' parameter
    - Tool calling with Claude-specific format
    - Different token calculation (input/output)
    
    Note: This is a stub. Real API integration requires valid API key.
    """
    
    # Claude-specific default endpoint and model
    DEFAULT_ENDPOINT = "https://api.anthropic.com/v1/messages"
    DEFAULT_MODEL = "claude-3-5-sonnet-20241022"
    
    def __init__(
        self,
        provider: str = None,
        model_id: str = None,
        endpoint: str = None,
        api_key: str = None
    ):
        """Initialize Claude model adapter.
        
        Args:
            provider: Provider name (should be 'claude')
            model_id: Claude model identifier
            endpoint: API endpoint URL (override from env)
            api_key: Anthropic API key (override from env)
        """
        # Provider name
        self._provider = provider or "claude"
        
        # Model ID
        self._model_id = model_id or os.getenv("CLAUDE_MODEL", self.DEFAULT_MODEL)
        
        # Endpoint
        self._endpoint = endpoint or os.getenv("CLAUDE_ENDPOINT", self.DEFAULT_ENDPOINT)
        
        # API Key
        self._api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        
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
        """Send messages to the Claude API.
        
        Note: This is a stub implementation. Real API integration requires:
        - Valid Anthropic API key
        - Network access to Anthropic API
        
        For now, this returns a synthetic response for testing.
        
        Args:
            messages: List of message dicts with role/content
            tools: Optional list of tool schemas for tool calling
            system_prompt: Optional system prompt to inject
            **kwargs: Claude-specific arguments (max_tokens, temperature, etc.)
        
        Returns:
            Response dict matching Claude API format
        """
        # Build the response data (placeholder for now)
        response_data = {
            "id": f"msg_{self._created_at}_{int(time.time() * 1000) % 100000}",
            "type": "message",
            "role": "assistant",
            "model": self._model_id,
            "content": [
                {
                    "type": "text",
                    "text": "This is a placeholder response from ClaudeModel stub."
                }
            ],
            "stop_reason": "end_turn",
            "usage": {
                "input_tokens": len(str(messages)),
                "output_tokens": 10,
                "total_tokens": len(str(messages)) + 10
            }
        }
        
        # If tools were provided and tool calling is supported, include placeholder
        if tools and self.supports_tool_calling():
            response_data["content"] = [
                {
                    "type": "tool_use",
                    "id": f"toolu_{int(time.time() * 1000) % 100000}",
                    "name": tools[0]["name"] if tools else "unknown",
                    "input": {}
                }
            ]
            response_data["stop_reason"] = "tool_use"
        
        return response_data
    
    def parse_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Parse and normalize a Claude response to Weslr format.
        
        Claude returns different format than OpenAI:
        - Content is in 'content' array
        - Each item has 'type' and payload
        
        This normalizes to Weslr format.
        
        Args:
            response: Raw response from send_message
        
        Returns:
            Normalized response with:
            - content: str (from Claude content array)
            - tool_calls: List[Dict] (from Claude tool_use items)
            - provider_data: Dict (raw response)
        """
        # Extract content from Claude's content array
        content_items = response.get("content", [])
        text_content = ""
        tool_calls = []
        
        for item in content_items:
            item_type = item.get("type", "")
            
            if item_type == "text":
                text_content += item.get("text", "")
            elif item_type == "tool_use":
                tool_calls.append({
                    "id": item.get("id", ""),
                    "type": "function",
                    "function": {
                        "name": item.get("name", ""),
                        "arguments": str(item.get("input", {}))
                    }
                })
        
        return {
            "content": text_content,
            "tool_calls": tool_calls,
            "provider_data": response
        }
    
    def _scrub_sensitive(self, text: str) -> str:
        """Scrub sensitive data from text."""
        return scrub_secrets(text)
    
    # ===== Capability Flags =====
    
    def supports_tool_calling(self) -> bool:
        """Whether this model supports native tool calling.
        
        Claude supports tool calling via tool_use tool type.
        Set CLAUDE_SUPPORTS_TOOL_CALLING=false to disable.
        """
        env_value = os.getenv("CLAUDE_SUPPORTS_TOOL_CALLING", "true")
        return env_value.lower() not in ("false", "0", "no")
    
    def supports_vision(self) -> bool:
        """Whether this model supports image input.
        
        Claude models support images via content array with 'image' type.
        Set CLAUDE_SUPPORTS_VISION=true to enable.
        """
        env_value = os.getenv("CLAUDE_SUPPORTS_VISION", "true")
        return env_value.lower() in ("true", "1", "yes")
    
    def supports_system_prompt(self) -> bool:
        """Whether this model supports system prompt injection.
        
        Claude supports system prompts via top-level 'system' parameter.
        Set CLAUDE_SUPPORTS_SYSTEM_PROMPT=false to disable.
        """
        env_value = os.getenv("CLAUDE_SUPPORTS_SYSTEM_PROMPT", "true")
        return env_value.lower() not in ("false", "0", "no")
    
    def get_max_tokens(self) -> int:
        """Return maximum output tokens supported by this model.
        
        Claude has different token limits than input tokens.
        Override via CLAUDE_MAX_TOKENS environment variable.
        """
        env_value = os.getenv("CLAUDE_MAX_TOKENS")
        if env_value:
            try:
                return int(env_value)
            except ValueError:
                pass
        return 8192  # Claude's typical max output tokens
    
    def get_context_window(self) -> int:
        """Return context window size in tokens.
        
        Claude models have different context windows.
        Override via CLAUDE_CONTEXT_WINDOW environment variable.
        """
        env_value = os.getenv("CLAUDE_CONTEXT_WINDOW")
        if env_value:
            try:
                return int(env_value)
            except ValueError:
                pass
        return 200000  # Claude 3.x context window
    
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
def create_claude(
    provider: str = "claude",
    model_id: str = "claude-3-5-sonnet-20241022",
    endpoint: str = None,
    api_key: str = None
) -> ModelAdapter:
    """Create a Claude model adapter.
    
    Args:
        provider: Provider name (should be 'claude')
        model_id: Claude model identifier (e.g., 'claude-3-5-sonnet')
        endpoint: API endpoint URL (optional, uses env or default)
        api_key: Anthropic API key (optional, uses env if not provided)
    
    Returns:
        ClaudeModel adapter instance
    """
    return ClaudeModel(
        provider=provider,
        model_id=model_id,
        endpoint=endpoint,
        api_key=api_key
    )


def create_claude_sonnet(
    endpoint: str = None,
    api_key: str = None
) -> ModelAdapter:
    """Create a Claude 3.5 Sonnet-specific adapter.
    
    Args:
        endpoint: API endpoint URL (optional, uses env or default)
        api_key: Anthropic API key (optional, uses env if not provided)
    
    Returns:
        ClaudeModel adapter configured for Claude 3.5 Sonnet
    """
    return ClaudeModel(
        provider="claude",
        model_id="claude-3-5-sonnet-20241022",
        endpoint=endpoint,
        api_key=api_key
    )
