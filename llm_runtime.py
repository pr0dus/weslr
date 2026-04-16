from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import time
import urllib.request
from pathlib import Path
from typing import Any

from config import (
    BASE_DIR,
    WESLR_FAILSAFE_DIR,
    WESLR_LLM_ENABLED,
    WESLR_LLM_PROVIDER,
    WESLR_LLM_MODEL,
    WESLR_LLM_MAX_CONTEXT_CHARS,
    WESLR_LLM_TEMPERATURE,
    WESLR_LLM_MAX_TOKENS,
    WESLR_EMBEDDED_MODEL_PATH,
    WESLR_DEFAULT_EMBEDDED_MODEL,
    WESLR_DEFAULT_EMBEDDED_MODEL_FILENAME,
    WESLR_EVIDENCE_ROUTING_ENABLED,
    OLLAMA_HOST,
    OLLAMA_TIMEOUT_SECONDS,
    OPENAI_BASE_URL,
    OPENAI_API_KEY,
)



def _fallback(role: str, context: dict[str, Any]) -> dict[str, Any]:
    # Neutral fallback: user-safe, no internal role/wake phrasing
    theme = context.get("proposed_theme") or context.get("active_pursuit") or context.get("unresolved_question") or "the task at hand"
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


def _prompt(context: dict[str, Any]) -> dict[str, Any]:
    # Chat-facing prompt path (user-visible response). Explicitly marked by chat_mode="chat".
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

    # Legacy inner-thought path (internal roles only)
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


def build_role_context(context: dict[str, Any]) -> dict[str, Any]:
    text = json.dumps(context, ensure_ascii=False)
    if len(text) <= WESLR_LLM_MAX_CONTEXT_CHARS:
        return context
    trimmed = dict(context)
    trimmed["proposed_reason"] = str(trimmed.get("proposed_reason", ""))[:240]
    trimmed["why_it_matters"] = str(trimmed.get("why_it_matters", ""))[:240]
    return trimmed


def _classify_prompt_for_routing(context: dict[str, Any]) -> tuple[str, str | None]:
    """Classify prompt and extract any evidence-required data.
    
    Returns (category, location_or None) where category is one of:
    - TIME_SENSITIVE: requires system time
    - WEATHER: requires weather data, location may be extracted
    - BOUNDED: can be handled by 0.5B model
    - UNSUPPORTED: requires external evidence we cannot provide
    """
    topic = str(context.get("proposed_theme", "")).lower()
    question = str(context.get("unresolved_question", "")).lower()
    action = str(context.get("proposed_action", "")).lower()
    reason = str(context.get("proposed_reason", "")).lower()
    
    # Check for time-sensitive queries
    time_keywords = ["weather", "temperature", "time", "date", "now", "currently", "today", "yesterday", "live", "实时", "天气"]
    if any(kw in topic or kw in question or kw in reason for kw in time_keywords):
        # Is this about weather specifically?
        if any(kw in topic or kw in question for kw in ["weather", "temperature", "天气"]):
            # Try to extract location from context
            location = None
            for key in ["proposed_theme", "unresolved_question", "proposed_reason", "why_it_matters"]:
                val = context.get(key, "")
                if val and "in" in str(val).lower():
                    # Rough location extraction: look for "in <location>"
                    parts = str(val).lower().split("in ")
                    if len(parts) > 1:
                        location = parts[-1].strip().strip(",")
                        break
            return ("WEATHER", location)
        return ("TIME_SENSITIVE", None)
    
    # Check for statistical/fact-based queries
    fact_keywords = ["population", "count", "number", "value", "price", "rate", "percentage", "score", "winner", "won"]
    if any(kw in topic or kw in question for kw in fact_keywords):
        return ("UNSUPPORTED", None)  # No local evidence source for these
    
    # Check for open-ended queries that need external facts
    if any(q in question for q in ["who is", "what is", "tell me about", "explain", "define"]) and not any(
        kw in topic for kw in ["role", "function", "being", "internal", "thought"]
    ):
        return ("UNSUPPORTED", None)
    
    # Default: bounded task for 0.5B model
    return ("BOUNDED", None)


def generate_inner_thought(role: str, context: dict[str, Any]) -> dict[str, Any]:
    fallback = _fallback(role, context)
    if not WESLR_LLM_ENABLED:
        return fallback
    
    provider = (WESLR_LLM_PROVIDER or "fallback").strip().lower()
    
    # Evidence routing is provider-agnostic — must happen before provider selection
    category, location = _classify_prompt_for_routing(context)
    
    # Route based on category
    if category == "TIME_SENSITIVE":
        # Use system time API
        try:
            from evidence_api import get_system_time, get_cached_evidence, cache_evidence
            cached = get_cached_evidence("system_time")
            if cached:
                evidence = cached
            else:
                evidence = get_system_time()
                cache_evidence("system_time", evidence)
            
            return {
                "kind": "inner_thought",
                "role": role,
                "summary": f"Current time: {evidence.get('date', 'unknown')} {evidence.get('time', 'unknown')}.",
                "concern": "Time tracking and awareness.",
                "intent": "To maintain temporal awareness.",
                "should_speak": False,
                "self_mod_hint": "",
                "source": "system_time",
                "provider": provider,
            }
        except Exception as e:
            return _generate_uncertain_response(role, context, "system_time", provider)
    
    if category == "WEATHER":
        # Use weather API
        try:
            from evidence_api import get_weather, cache_evidence, get_cached_evidence
            cached = get_cached_evidence("weather")
            if cached:
                evidence = cached
            else:
                evidence = get_weather(location)
                cache_evidence("weather", evidence)
            
            if evidence.get("kind") == "error":
                return _generate_uncertain_response(role, context, "weather", provider)
            
            temp = evidence.get("temp_c") or evidence.get("temp_f")
            desc = evidence.get("weather_desc") or "unknown"
            return {
                "kind": "inner_thought",
                "role": role,
                "summary": f"Weather: {desc}. Temperature: {temp}C." if temp else f"Weather: {desc}.",
                "concern": f"Weather conditions in {evidence.get('location', 'unknown')}.",
                "intent": "To track current weather conditions.",
                "should_speak": False,
                "self_mod_hint": "",
                "source": "weather_api",
                "provider": provider,
            }
        except Exception as e:
            return _generate_uncertain_response(role, context, "weather", provider)
    
    if category == "UNSUPPORTED":
        return _generate_uncertain_response(role, context, "unsupported", provider)
    
    # Evidence routing is complete. Now select provider for bounded reasoning.
    if provider == "embedded":
        guard_ok, guard_msg = prestart_guard()
        if not guard_ok:
            return _fallback(role, {**context, "error": "embedded_prestart_failed", "error_detail": guard_msg})
    try:
        # Evidence routing done above. Now delegate to provider abstraction.
        from weslr.providers import get_provider  # local to avoid circular import
        return get_provider().generate(role, context, chat_mode=False)
    except Exception:
        return fallback


def generate_chat(message: str, context: dict[str, Any]) -> dict[str, Any]:
    """Chat-facing entrypoint. Returns chat-safe payload only."""
    role = "chat"
    chat_context = {"chat_message": message, "chat_mode": "chat", **(context or {})}
    fallback_payload = {"summary": "Chat is temporarily unavailable. Please try again in a moment.", "provider": "fallback"}
    provider = (WESLR_LLM_PROVIDER or "fallback").strip().lower()

    try:
        from weslr.providers import get_provider, FallbackProvider  # local to avoid circular import
        try:
            return get_provider(provider).generate(role, chat_context, chat_mode=True)
        except Exception as primary_err:
            # Attempt graceful degradation via FallbackProvider before surfacing upward
            try:
                fallback_result = FallbackProvider().generate(role, chat_context, chat_mode=True)
                fallback_result["degraded"] = True
                fallback_result["degraded_reason"] = "primary_provider_unavailable"
                return fallback_result
            except Exception:
                return fallback_payload
    except Exception:
        return fallback_payload


def _meta_sounding(text: str) -> bool:
    lowered = text.strip().lower()
    bad_fragments = [
        "structured inner thought",
        "waking internal role",
        "persistent being",
        "return strict json",
        "json only",
        "internal role",
        "compact inner thought",
        "assistant",
        "schema",
        "prompt",
        "task",
        "what specific concerns",
        "translate inner pressure into outward language",
        "my purpose is to",
        "the communicator is",
        "the communication is",
    ]
    return any(fragment in lowered for fragment in bad_fragments)


def _normalize_chat(parsed: dict[str, Any], fallback: dict[str, Any], provider: str) -> dict[str, Any]:
    summary = str(parsed.get("summary") or fallback["summary"])[:240]
    if _meta_sounding(summary) or summary.strip().endswith(":"):
        summary = fallback["summary"]
    return {
        "kind": "chat_response",
        "summary": summary,
        "provider": provider,
    }


def _normalize_inner(parsed: dict[str, Any], role: str, fallback: dict[str, Any], provider: str) -> dict[str, Any]:
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


def _generate_via_ollama(role: str, context: dict[str, Any], fallback: dict[str, Any], *, chat_mode: bool = False) -> dict[str, Any]:
    import socket
    socket.setdefaulttimeout(OLLAMA_TIMEOUT_SECONDS)
    
    prompt_data = {
        "model": WESLR_LLM_MODEL,
        "prompt": json.dumps(_prompt(build_role_context(context)), ensure_ascii=False),
        "stream": False,
        "options": {"temperature": WESLR_LLM_TEMPERATURE, "num_predict": WESLR_LLM_MAX_TOKENS},
    }
    
    body = json.dumps(prompt_data).encode("utf-8")
    req = urllib.request.Request(
        f"{OLLAMA_HOST.rstrip('/')}/api/generate",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=OLLAMA_TIMEOUT_SECONDS) as resp:
            payload = json.loads(resp.read().decode("utf-8"))
        # Ollama returns the raw JSON string in 'response' field
        response_str = payload.get("response", "{}")
        # Sometimes it's already parsed, sometimes it's a string
        if isinstance(response_str, str):
            parsed = json.loads(response_str)
        else:
            parsed = response_str
        if chat_mode:
            return _normalize_chat(parsed, fallback, "ollama")
        return _normalize_inner(parsed, role, fallback, "ollama")
    except socket.timeout:
        return fallback


def _generate_via_openai_compatible(role: str, context: dict[str, Any], fallback: dict[str, Any], *, chat_mode: bool = False) -> dict[str, Any]:
    if not OPENAI_API_KEY:
        return fallback
    body = json.dumps({
        "model": WESLR_LLM_MODEL,
        "messages": [
            {"role": "system", "content": "Return strict JSON only."},
            {"role": "user", "content": json.dumps(_prompt(build_role_context(context)), ensure_ascii=False)},
        ],
        "temperature": WESLR_LLM_TEMPERATURE,
        "max_tokens": WESLR_LLM_MAX_TOKENS,
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{OPENAI_BASE_URL.rstrip('/')}/chat/completions",
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_API_KEY}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=OLLAMA_TIMEOUT_SECONDS) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    content = (((payload.get("choices") or [{}])[0].get("message") or {}).get("content") or "{}")
    parsed = json.loads(content)
    if chat_mode:
        return _normalize_chat(parsed, fallback, "openai")
    return _normalize_inner(parsed, role, fallback, "openai")


def _generate_via_embedded(role: str, context: dict[str, Any], fallback: dict[str, Any], *, chat_mode: bool = False) -> dict[str, Any]:
    model_path = WESLR_EMBEDDED_MODEL_PATH
    if not model_path.exists():
        return fallback
    prompt_payload = _prompt(build_role_context(context))
    prompt = json.dumps(prompt_payload, ensure_ascii=False)
    try:
        from llama_cpp import Llama  # type: ignore
    except Exception:
        server_result = _generate_via_embedded_server(role, prompt_payload, fallback, chat_mode=chat_mode)
        if server_result.get("provider") == "embedded":
            return server_result
        return _generate_via_embedded_cli(role, prompt, fallback, chat_mode=chat_mode)
    llm = Llama(model_path=str(model_path), n_ctx=2048, verbose=False)
    out = llm.create_completion(
        prompt=prompt,
        max_tokens=WESLR_LLM_MAX_TOKENS,
        temperature=WESLR_LLM_TEMPERATURE,
        stop=["\n\n"],
    )
    text = ((out.get("choices") or [{}])[0].get("text") or "{}").strip()
    parsed = json.loads(text)
    if chat_mode:
        return _normalize_chat(parsed, fallback, "embedded")
    return _normalize_inner(parsed, role, fallback, "embedded")


def _embedded_server_base() -> str:
    return os.getenv("WESLR_EMBEDDED_SERVER_URL", "http://127.0.0.1:18081/v1").rstrip("/")


def _embedded_server_host_port() -> tuple[str, int]:
    base = _embedded_server_base()
    without_scheme = base.split("://", 1)[-1]
    host_port = without_scheme.split("/", 1)[0]
    if ":" in host_port:
        host, port = host_port.rsplit(":", 1)
        return host, int(port)
    return host_port, 80


def _can_connect(host: str, port: int, timeout: float = 1.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def _ensure_embedded_server() -> bool:
    host, port = _embedded_server_host_port()
    if _can_connect(host, port):
        return True
    llama_server = shutil.which("llama-server")
    if not llama_server or not WESLR_EMBEDDED_MODEL_PATH.exists():
        return False
    state_dir = WESLR_FAILSAFE_DIR
    state_dir.mkdir(parents=True, exist_ok=True)
    log_path = state_dir / "embedded-llama-server.log"
    with open(log_path, "ab") as log_file:
        subprocess.Popen(
            [
                llama_server,
                "-m",
                str(WESLR_EMBEDDED_MODEL_PATH),
                "--host",
                host,
                "--port",
                str(port),
                "-c",
                "2048",
                "-n",
                str(max(WESLR_LLM_MAX_TOKENS, 128)),
                "--threads",
                os.getenv("WESLR_EMBEDDED_SERVER_THREADS", "4"),
            ],
            stdout=log_file,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
        )
    for _ in range(30):
        if _can_connect(host, port):
            break
        time.sleep(1)
    else:
        return False
    warm_req = urllib.request.Request(f"{_embedded_server_base()}/models", method="GET")
    for _ in range(10):
        try:
            with urllib.request.urlopen(warm_req, timeout=5):
                return True
        except Exception:
            time.sleep(1)
    return False


def _generate_via_embedded_server(role: str, prompt_payload: dict[str, Any], fallback: dict[str, Any], *, chat_mode: bool = False) -> dict[str, Any]:
    server_base = _embedded_server_base()
    server_ok = _ensure_embedded_server()
    if not server_ok:
        error_fallback = _fallback(role, {**prompt_payload.get("live_context", {}), "error": "embedded_server_not_ready"})
        error_fallback["error"] = "embedded_server_not_ready"
        error_fallback["source"] = "embedded_error"
        return error_fallback
    body = json.dumps({
        "model": Path(WESLR_EMBEDDED_MODEL_PATH).name,
        "messages": [
            {"role": "system", "content": "Return strict JSON only."},
            {"role": "user", "content": json.dumps(prompt_payload, ensure_ascii=False)},
        ],
        "temperature": WESLR_LLM_TEMPERATURE,
        "max_tokens": max(WESLR_LLM_MAX_TOKENS, 220),
        "response_format": {
            "type": "json_schema",
            "json_schema": {
                "name": "inner_thought",
                "schema": {
                    "type": "object",
                    "properties": {
                        "summary": {"type": "string"},
                        "concern": {"type": "string"},
                        "intent": {"type": "string"},
                        "should_speak": {"type": "boolean"},
                        "self_mod_hint": {"type": "string"},
                    },
                    "required": ["summary", "concern", "intent", "should_speak", "self_mod_hint"],
                },
            },
        },
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{server_base}/chat/completions",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    for attempt in range(6):
        try:
            with urllib.request.urlopen(req, timeout=max(30, OLLAMA_TIMEOUT_SECONDS * 4)) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
            content = (((payload.get("choices") or [{}])[0].get("message") or {}).get("content") or "{}").strip()
            parsed = json.loads(content)
            return _normalize(parsed, role, fallback, "embedded")
        except Exception as e:
            if attempt == 5:
                error_fallback = _fallback(role, {**prompt_payload.get("live_context", {}), "error": "api_call_failed"})
                error_fallback["error"] = "api_call_failed"
                error_fallback["error_detail"] = str(e)[:200]
                error_fallback["source"] = "embedded_error"
                return error_fallback
            time.sleep(2)
    return fallback


def _generate_via_embedded_cli(role: str, prompt: str, fallback: dict[str, Any]) -> dict[str, Any]:
    llama_cli = shutil.which("llama-cli")
    if not llama_cli:
        return fallback
    cmd = [
        llama_cli,
        "--log-disable",
        "--simple-io",
        "--no-display-prompt",
        "-m",
        str(WESLR_EMBEDDED_MODEL_PATH),
        "-c",
        "2048",
        "-n",
        str(WESLR_LLM_MAX_TOKENS),
        "--temp",
        str(WESLR_LLM_TEMPERATURE),
        "-p",
        prompt,
    ]
    completed = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=max(30, int(OLLAMA_TIMEOUT_SECONDS * 4)),
        check=False,
    )
    if completed.returncode != 0:
        return fallback
    text = (completed.stdout or "").strip()
    if not text:
        return fallback
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return fallback
    parsed = json.loads(text[start : end + 1])
    return _normalize(parsed, role, fallback, "embedded")


def embedded_self_test() -> dict[str, Any]:
    context = {
        "wake_reason": "self-test",
        "proposed_theme": "embedded runtime verification",
        "active_pursuit": "embedded cognition",
        "proposed_action": "reflect",
        "unresolved_question": "can direct bundled inference run",
        "proposed_reason": "Verify the first embedded runtime path honestly.",
        "why_it_matters": "Weslr should know whether it has real direct local cognition or only fallback.",
    }
    result = generate_inner_thought("communicator", context)
    status_payload = status()
    return {
        "status": status_payload,
        "thought": result,
        "ok": result.get("provider") == "embedded",
    }


def status() -> dict[str, Any]:
    provider = (WESLR_LLM_PROVIDER or "fallback").strip().lower()
    llama_cli = shutil.which("llama-cli")
    llama_server = shutil.which("llama-server")
    server_host, server_port = _embedded_server_host_port()
    server_reachable = _can_connect(server_host, server_port, timeout=0.5)
    llama_cpp_importable = False
    try:
        from llama_cpp import Llama  # type: ignore
        llama_cpp_importable = bool(Llama)
    except Exception:
        llama_cpp_importable = False
    result = {
        "enabled": bool(WESLR_LLM_ENABLED),
        "provider": provider,
        "model": WESLR_LLM_MODEL,
        "embedded_default_model": WESLR_DEFAULT_EMBEDDED_MODEL,
        "embedded_default_filename": WESLR_DEFAULT_EMBEDDED_MODEL_FILENAME,
        "embedded_model_path": str(WESLR_EMBEDDED_MODEL_PATH),
        "embedded_model_exists": WESLR_EMBEDDED_MODEL_PATH.exists(),
        "embedded_llama_cpp_importable": llama_cpp_importable,
        "embedded_llama_cli": llama_cli or "",
        "embedded_llama_server": llama_server or "",
        "embedded_server_url": _embedded_server_base(),
        "embedded_server_reachable": server_reachable,
        "openai_base_url": OPENAI_BASE_URL,
        "openai_configured": bool(OPENAI_API_KEY),
        "ollama_host": OLLAMA_HOST,
    }
    if provider == "embedded":
        result["live"] = bool(result["embedded_model_exists"] and (llama_cpp_importable or server_reachable or llama_server or llama_cli))
    elif provider in {"openai", "openai_compatible", "oauth"}:
        result["live"] = bool(OPENAI_API_KEY)
    elif provider == "ollama":
        # Treat Ollama as live if the daemon is reachable at configured host
        try:
            with urllib.request.urlopen(f"{OLLAMA_HOST.rstrip('/')}/api/tags", timeout=1.0) as resp:
                result["live"] = resp.status == 200
        except Exception:
            result["live"] = False
    else:
        result["live"] = False
    return result


def provider_state() -> tuple[str, str]:
    st = status()
    provider = st.get("provider", "fallback")
    if not st.get("enabled"):
        return "unavailable", "LLM disabled"
    if provider in {"openai", "openai_compatible", "oauth"} and not st.get("openai_configured"):
        return "unavailable", "OpenAI credentials missing"
    if st.get("live"):
        return "healthy", "provider live"
    if provider in {"embedded", "llama_cpp", "embedded_llama_cpp"} and not st.get("embedded_server_reachable"):
        return "degraded", "Embedded server unreachable"
    if provider == "fallback":
        return "unavailable", "No provider configured"
    return "degraded", "Provider configured but not live"


def health() -> dict[str, Any]:
    """Health endpoint for monitoring - returns structured status."""
    provider = (WESLR_LLM_PROVIDER or "fallback").strip().lower()
    server_host, server_port = _embedded_server_host_port()
    server_reachable = _can_connect(server_host, server_port, timeout=1.0)
    model_loaded = False
    if server_reachable:
        try:
            warm_req = urllib.request.Request(f"{_embedded_server_base()}/models", method="GET")
            with urllib.request.urlopen(warm_req, timeout=5) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
                model_loaded = bool(payload.get("data") and len(payload["data"]) > 0)
        except Exception:
            model_loaded = False
    return {
        "status": "healthy" if server_reachable and model_loaded else "degraded" if server_reachable else "unhealthy",
        "provider": provider,
        "model_path": str(WESLR_EMBEDDED_MODEL_PATH),
        "model_exists": WESLR_EMBEDDED_MODEL_PATH.exists(),
        "model_loaded": model_loaded,
        "server_host": server_host,
        "server_port": server_port,
        "server_ready": server_reachable and model_loaded,
        "timestamp": int(time.time()),
    }


def health_endpoint() -> tuple[int, dict[str, Any]]:
    """HTTP health endpoint - returns (status_code, response_dict)."""
    h = health()
    if h["server_ready"]:
        return 200, h
    elif h["status"] == "degraded":
        return 503, h
    else:
        return 500, h


def prestart_guard() -> tuple[bool, str]:
    """Guard: refuse to start if embedded configured but server unreachable."""
    provider = (WESLR_LLM_PROVIDER or "fallback").strip().lower()
    if provider != "embedded":
        return True, "not embedded provider"
    h = health()
    if h["server_ready"]:
        return True, "server ready"
    return False, f"embedded server not ready: {h.get('status', 'unknown')}"


def _generate_uncertain_response(role: str, context: dict[str, Any], reason: str, provider: str = "fallback") -> dict[str, Any]:
    """Generate uncertainty response when evidence is unavailable."""
    return {
        "kind": "inner_thought",
        "role": role,
        "summary": f"Verification of {reason} facts is unavailable.",
        "concern": "Cannot verify external current facts without evidence source.",
        "intent": "To track the evidence gap and await verification.",
        "should_speak": False,
        "self_mod_hint": "",
        "source": "uncertain_guard",
        "provider": provider,
    }
