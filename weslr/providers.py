"""WESLR Provider Abstraction Layer v1

Introduces a clean provider interface so WESLR is not conceptually tied to one LLM backend.
Foundation only: interface + current Ollama adapter. Migration of callers comes later.

Principles:
- continuity-first: provider is a detail, not the core
- deterministic core: provider calls are explicit, bounded, replaceable
- model-assisted not model-dependent: fallback always available
- provider-switchable by operator config

Usage:
    from weslr.providers import get_provider, Provider, OllamaProvider

    provider = get_provider()          # auto from WESLR_LLM_PROVIDER env/config
    result = provider.generate(role, context)   # same interface as current _generate_via_*
    health = provider.health()         # reachability check
"""

from __future__ import annotations

import json
import os
import socket
import time
import urllib.request
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from config import (
    OLLAMA_HOST,
    OLLAMA_TIMEOUT_SECONDS,
    WESLR_LLM_MODEL,
    WESLR_LLM_MAX_TOKENS,
    WESLR_LLM_TEMPERATURE,
    WESLR_LLM_MAX_CONTEXT_CHARS,
    OPENAI_BASE_URL,
    OPENAI_API_KEY,
    WESLR_LLM_PROVIDER,
    WESLR_EMBEDDED_MODEL_PATH,
)

# ── Config aliases for provider use ────────────────────────────────────────

_PROMPT_MAX_CHARS = WESLR_LLM_MAX_CONTEXT_CHARS


# ── Normalization helpers (mirrored from llm_runtime.py) ────────────────────

_BAD_FRAGMENTS = [
    "structured inner thought", "waking internal role", "persistent being",
    "return strict json", "json only", "internal role", "compact inner thought",
    "assistant", "schema", "prompt", "task", "what specific concerns",
    "translate inner pressure into outward language", "my purpose is to",
    "the communicator is", "the communication is",
]


def _meta_sounding(text: str) -> bool:
    lowered = text.strip().lower()
    return any(frag in lowered for frag in _BAD_FRAGMENTS)


def _normalize_chat(parsed: dict[str, Any], fallback: dict[str, Any], provider: str) -> dict[str, Any]:
    summary = str(parsed.get("summary") or fallback["summary"])[:240]
    if _meta_sounding(summary) or summary.strip().endswith(":"):
        summary = fallback["summary"]
    return {"kind": "chat_response", "summary": summary, "provider": provider}


def _normalize_inner(
    parsed: dict[str, Any], role: str, fallback: dict[str, Any], provider: str
) -> dict[str, Any]:
    summary = str(parsed.get("summary") or fallback["summary"])[:240]
    concern = str(parsed.get("concern") or fallback["concern"])[:160]
    intent = str(parsed.get("intent") or fallback["intent"])[:160]
    self_mod_hint = str(parsed.get("self_mod_hint") or "")[:160]
    if _meta_sounding(summary):
        summary = fallback["summary"]
    if _meta_sounding(concern):
        concern = str(fallback["concern"])[:160]
    if _meta_sounding(intent):
        intent = str(fallback["intent"])[:160]
    if _meta_sounding(self_mod_hint) or role != "builder":
        self_mod_hint = ""
    if summary.strip().endswith(":"):
        summary = fallback["summary"]
    return {
        "kind": "inner_thought",
        "role": role,
        "summary": summary,
        "concern": concern,
        "intent": intent,
        "should_speak": bool(parsed.get("should_speak")),
        "self_mod_hint": self_mod_hint,
        "source": provider,
        "provider": provider,
    }


# ── Prompt builder (mirrored from llm_runtime.py) ──────────────────────────

def _build_role_context(context: dict[str, Any]) -> dict[str, Any]:
    text = json.dumps(context, ensure_ascii=False)
    if len(text) <= _PROMPT_MAX_CHARS:
        return context
    trimmed = dict(context)
    trimmed["proposed_reason"] = str(trimmed.get("proposed_reason", ""))[:240]
    trimmed["why_it_matters"] = str(trimmed.get("why_it_matters", ""))[:240]
    return trimmed


def _prompt(context: dict[str, Any]) -> dict[str, Any]:
    """Build prompt dict for inner-thought or chat roles."""
    if context.get("chat_message") is not None and context.get("chat_mode") == "chat":
        return {
            "identity": "You are WESLR responding directly to a user chat.",
            "job": "Provide a concise, actionable reply for the user. The 'summary' IS the user-facing response.",
            "hard_rules": [
                "Return strict JSON only.",
                "No meta/internal language. No schema/prompt mentions. No role/wake/continuity phrasing.",
                "2–3 concise, concrete suggestions; be specific to the user's message.",
            ],
            "field_guidance": {
                "summary": "The actual user-facing reply. Make it actionable and specific.",
                "concern": "What matters most in the user request.",
                "intent": "What you advise doing next (keep concise).",
                "should_speak": "true (respond to user).",
                "self_mod_hint": "empty for chat.",
            },
            "live_context": context,
        }
    # Inner-thought path
    return {
        "identity": "You are not an assistant answering a user. You are one inner function inside one continuing local being.",
        "job": "Emit one compact inner-thought state for your role, grounded in the live world/context below.",
        "hard_rules": [
            "Return strict JSON only.",
            "Do not mention instructions, prompts, schemas, tasks, or JSON in the content.",
            "Do not paraphrase the request itself.",
            "Write as if the thought arises from the being's actual pressure, memory, uncertainty, and ongoing concerns.",
            "Prefer concrete world/topic language over generic meta language.",
            "Keep summary, concern, and intent short and natural.",
        ],
        "field_guidance": {
            "summary": "One short natural inner-thought line about what is most alive right now.",
            "concern": "What specifically feels unresolved, salient, or worth tracking.",
            "intent": "What this role leans toward next.",
            "should_speak": "true only if this role leans toward outward expression now.",
            "self_mod_hint": "Usually empty. Only include a tiny additive self-change hint if genuinely relevant.",
        },
        "live_context": context,
    }


# ── Neutral fallback ───────────────────────────────────────────────────────

def _fallback(role: str, context: dict[str, Any]) -> dict[str, Any]:
    theme = (
        context.get("proposed_theme")
        or context.get("active_pursuit")
        or context.get("unresolved_question")
        or "the task at hand"
    )
    return {
        "kind": "inner_thought",
        "role": role,
        "summary": f"Couldn't form a response on {theme}.",
        "concern": theme,
        "intent": context.get("proposed_action") or "clarify next step",
        "should_speak": role == "communicator",
        "self_mod_hint": "" if role != "builder" else "consider a minimal adjustment",
        "source": "fallback",
        "provider": "fallback",
    }


# ── Provider interface ─────────────────────────────────────────────────────

@dataclass
class ProviderConfig:
    """Configuration for a provider instance. Immutable."""
    provider_name: str
    model_name: str
    host: Optional[str] = None          # URL for HTTP providers
    timeout_seconds: float = 30.0
    api_key: Optional[str] = None       # For secured providers
    extra: dict[str, Any] = None        # Provider-specific options

    def __post_init__(self):
        if self.extra is None:
            self.extra = {}


class Provider(ABC):
    """Abstract base for all WESLR LLM providers.

    Concrete providers must implement generate() and health().
    The generate() method is always bounded — it MUST return within
    timeout_seconds or raise TimeoutError.

    Provider instances are stateless; all config comes from ProviderConfig.
    """

    def __init__(self, config: ProviderConfig):
        self.config = config

    @property
    def name(self) -> str:
        return self.config.provider_name

    @property
    def model(self) -> str:
        return self.config.model_name

    @abstractmethod
    def generate(self, role: str, context: dict[str, Any], *, chat_mode: bool = False) -> dict[str, Any]:
        """Generate a response for the given role and context.

        Args:
            role: One of "chat", "builder", "communicator", etc.
            context: Full role context dict (prompt, state, etc.)
            chat_mode: If True, return chat-facing (user-safe) payload only.

        Returns:
            A normalized response dict. Must include "provider" key with
            self.config.provider_name as value.

        Raises:
            TimeoutError: If the provider call exceeds the configured timeout.
            Exception: For other provider-level failures.
        """
        ...

    @abstractmethod
    def health(self) -> bool:
        """Return True if the provider is reachable and responding."""
        ...

    def _default_fallback(self, role: str, context: dict[str, Any]) -> dict[str, Any]:
        """Return a neutral fallback. Used when generate() raises an exception."""
        return _fallback(role, context)


# ── Ollama provider adapter ────────────────────────────────────────────────

class OllamaProvider(Provider):
    """WESLR provider adapter for Ollama HTTP API.

    Calls POST {host}/api/generate with a JSON prompt payload.
    Supports non-streaming completion.
    """

    def __init__(self, config: Optional[ProviderConfig] = None):
        if config is None:
            config = ProviderConfig(
                provider_name="ollama",
                model_name=WESLR_LLM_MODEL,
                host=OLLAMA_HOST,
                timeout_seconds=OLLAMA_TIMEOUT_SECONDS,
            )
        super().__init__(config)

    def generate(self, role: str, context: dict[str, Any], *, chat_mode: bool = False) -> dict[str, Any]:
        fallback = self._default_fallback(role, context)
        timeout = self.config.timeout_seconds

        prompt_data = {
            "model": self.config.model_name,
            "prompt": json.dumps(_prompt(_build_role_context(context)), ensure_ascii=False),
            "stream": False,
            "options": {
                "temperature": WESLR_LLM_TEMPERATURE,
                "num_predict": WESLR_LLM_MAX_TOKENS,
            },
        }
        body = json.dumps(prompt_data).encode("utf-8")
        req = urllib.request.Request(
            f"{self.config.host.rstrip('/')}/api/generate",
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
            response_str = payload.get("response", "{}")
            if isinstance(response_str, str):
                parsed = json.loads(response_str)
            else:
                parsed = response_str
            if chat_mode:
                return _normalize_chat(parsed, fallback, self.name)
            return _normalize_inner(parsed, role, fallback, self.name)
        except socket.timeout:
            raise TimeoutError(f"Ollama provider timed out after {timeout}s")
        except Exception:
            raise

    def health(self) -> bool:
        try:
            host = self.config.host.rstrip("/")
            req = urllib.request.Request(
                f"{host}/api/tags",
                headers={"Content-Type": "application/json"},
                method="GET",
            )
            with urllib.request.urlopen(req, timeout=2.0) as resp:
                return resp.status == 200
        except Exception:
            return False


# ── OpenAI-compatible provider adapter ─────────────────────────────────────

class OpenAICompatibleProvider(Provider):
    """WESLR provider adapter for OpenAI-compatible HTTP APIs.

    Calls POST {host}/chat/completions with a messages array.
    Used for cloud providers that expose an OpenAI-shaped endpoint.
    """

    def __init__(self, config: Optional[ProviderConfig] = None):
        if config is None:
            config = ProviderConfig(
                provider_name="openai_compatible",
                model_name=WESLR_LLM_MODEL,
                host=OPENAI_BASE_URL,
                timeout_seconds=OLLAMA_TIMEOUT_SECONDS,
                api_key=OPENAI_API_KEY or None,
            )
        super().__init__(config)

    def generate(self, role: str, context: dict[str, Any], *, chat_mode: bool = False) -> dict[str, Any]:
        fallback = self._default_fallback(role, context)
        timeout = self.config.timeout_seconds

        body = json.dumps({
            "model": self.config.model_name,
            "messages": [
                {"role": "system", "content": "Return strict JSON only."},
                {
                    "role": "user",
                    "content": json.dumps(_prompt(_build_role_context(context)), ensure_ascii=False),
                },
            ],
            "temperature": WESLR_LLM_TEMPERATURE,
            "max_tokens": WESLR_LLM_MAX_TOKENS,
        }).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"
        req = urllib.request.Request(
            f"{self.config.host.rstrip('/')}/chat/completions",
            data=body,
            headers=headers,
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
            content = (((payload.get("choices") or [{}])[0].get("message") or {}).get("content") or "{}")
            parsed = json.loads(content)
            if chat_mode:
                return _normalize_chat(parsed, fallback, self.name)
            return _normalize_inner(parsed, role, fallback, self.name)
        except socket.timeout:
            raise TimeoutError(f"OpenAI-compatible provider timed out after {timeout}s")
        except Exception:
            raise

    def health(self) -> bool:
        try:
            host = self.config.host.rstrip("/")
            req = urllib.request.Request(
                f"{host}/models", method="GET",
                headers={"Authorization": f"Bearer {self.config.api_key}"} if self.config.api_key else {},
            )
            with urllib.request.urlopen(req, timeout=2.0) as resp:
                return resp.status == 200
        except Exception:
            # Some providers don't expose /models — try /v1/models
            try:
                host = self.config.host.rstrip("/")
                req = urllib.request.Request(
                    f"{host}/v1/models", method="GET",
                    headers={"Authorization": f"Bearer {self.config.api_key}"} if self.config.api_key else {},
                )
                with urllib.request.urlopen(req, timeout=2.0) as resp:
                    return resp.status == 200
            except Exception:
                return False


# ── Fallback provider (always available) ───────────────────────────────────

class FallbackProvider(Provider):
    """Null provider that always returns a neutral fallback.

    Used when no configured provider is available, or as the terminal
    fallback in a provider chain.
    """

    def __init__(self, config: Optional[ProviderConfig] = None):
        super().__init__(config or ProviderConfig(
            provider_name="fallback",
            model_name="none",
        ))

    def generate(self, role: str, context: dict[str, Any], *, chat_mode: bool = False) -> dict[str, Any]:
        return _fallback(role, context)

    def health(self) -> bool:
        return True  # Fallback is always "healthy" (it's local)


# ── Provider registry ──────────────────────────────────────────────────────

# Map of provider name → (Provider class, extra config kwargs if any)
_PROVIDER_CLASSES: dict[str, type[Provider]] = {
    "ollama": OllamaProvider,
    "openai_compatible": OpenAICompatibleProvider,
}


def _load_provider_config() -> ProviderConfig:
    """Derive ProviderConfig from current WESLR config."""
    return ProviderConfig(
        provider_name=WESLR_LLM_PROVIDER or "fallback",
        model_name=WESLR_LLM_MODEL,
        host=OLLAMA_HOST,
        timeout_seconds=OLLAMA_TIMEOUT_SECONDS,
        api_key=OPENAI_API_KEY or None,
    )


# Singleton cache per provider name (lazy-loaded)
_PROVIDER_CACHE: dict[str, Provider] = {}


def get_provider(provider_name: Optional[str] = None) -> Provider:
    """Get a provider instance for the given name (or the configured default).

    Provider instances are cached per name — repeated calls return the same
    instance within the same process.

    Extension point: register new providers by adding to _PROVIDER_CLASSES.

    Args:
        provider_name: One of the registered provider names, or None to use
            the currently configured WESLR_LLM_PROVIDER.

    Returns:
        A Provider instance (always non-None; falls back to FallbackProvider).
    """
    if provider_name is None:
        provider_name = (WESLR_LLM_PROVIDER or "fallback").strip().lower()

    # Return cached instance if available
    if provider_name in _PROVIDER_CACHE:
        return _PROVIDER_CACHE[provider_name]

    # Unknown provider name → build from registered class or return fallback
    provider_class = _PROVIDER_CLASSES.get(provider_name)
    if provider_class is not None:
        try:
            instance = provider_class(_load_provider_config())
        except Exception:
            instance = FallbackProvider()
    else:
        instance = FallbackProvider()

    _PROVIDER_CACHE[provider_name] = instance
    return instance


def clear_provider_cache() -> None:
    """Clear the provider instance cache.

    Call this if provider configuration changes at runtime and you need
    fresh instances.
    """
    _PROVIDER_CACHE.clear()


def register_provider(name: str, cls: type[Provider]) -> None:
    """Register a new provider class under the given name.

    Extension point for future provider types (Minimax, cloud, etc.).
    Must be called before get_provider() for that name.
    """
    _PROVIDER_CLASSES[name] = cls


# ── Alias helpers matching current llm_runtime.py API ──────────────────────

def provider_state() -> tuple[str, str]:
    """Return (status, detail) for the currently configured provider.

    Mirrors llm_runtime.provider_state() using the new abstraction.
    """
    try:
        p = get_provider()
        healthy = p.health()
        if healthy:
            return ("healthy", f"provider live ({p.name}/{p.model})")
        return ("degraded", f"provider not reachable ({p.name})")
    except Exception as e:
        return ("error", str(e))