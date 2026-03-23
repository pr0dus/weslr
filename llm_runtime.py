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
    CIRCLEFORGE_FAILSAFE_DIR,
    CIRCLEFORGE_LLM_ENABLED,
    CIRCLEFORGE_LLM_PROVIDER,
    CIRCLEFORGE_LLM_MODEL,
    CIRCLEFORGE_LLM_MAX_CONTEXT_CHARS,
    CIRCLEFORGE_LLM_TEMPERATURE,
    CIRCLEFORGE_LLM_MAX_TOKENS,
    CIRCLEFORGE_EMBEDDED_MODEL_PATH,
    CIRCLEFORGE_DEFAULT_EMBEDDED_MODEL,
    CIRCLEFORGE_DEFAULT_EMBEDDED_MODEL_FILENAME,
    OLLAMA_HOST,
    OLLAMA_TIMEOUT_SECONDS,
    OPENAI_BASE_URL,
    OPENAI_API_KEY,
)


def _fallback(role: str, context: dict[str, Any]) -> dict[str, Any]:
    return {
        "kind": "inner_thought",
        "role": role,
        "summary": f"{role} woke on {context.get('wake_reason', 'unknown')} around {context.get('proposed_theme') or context.get('active_pursuit') or 'current continuity pressure'}.",
        "concern": context.get("proposed_theme") or context.get("active_pursuit") or context.get("unresolved_question") or "continuity",
        "intent": context.get("proposed_action") or "reflect",
        "should_speak": role == "communicator",
        "self_mod_hint": "consider tiny additive change" if role == "builder" else "",
        "source": "fallback",
        "provider": "fallback",
    }


def _prompt(context: dict[str, Any]) -> dict[str, Any]:
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
    if len(text) <= CIRCLEFORGE_LLM_MAX_CONTEXT_CHARS:
        return context
    trimmed = dict(context)
    trimmed["proposed_reason"] = str(trimmed.get("proposed_reason", ""))[:240]
    trimmed["why_it_matters"] = str(trimmed.get("why_it_matters", ""))[:240]
    return trimmed


def generate_inner_thought(role: str, context: dict[str, Any]) -> dict[str, Any]:
    fallback = _fallback(role, context)
    if not CIRCLEFORGE_LLM_ENABLED:
        return fallback
    provider = (CIRCLEFORGE_LLM_PROVIDER or "fallback").strip().lower()
    try:
        if provider == "ollama":
            return _generate_via_ollama(role, context, fallback)
        if provider in {"openai", "openai_compatible", "oauth"}:
            return _generate_via_openai_compatible(role, context, fallback)
        if provider in {"embedded", "llama_cpp", "embedded_llama_cpp"}:
            return _generate_via_embedded(role, context, fallback)
        return fallback
    except Exception:
        return fallback


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


def _normalize(parsed: dict[str, Any], role: str, fallback: dict[str, Any], provider: str) -> dict[str, Any]:
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


def _generate_via_ollama(role: str, context: dict[str, Any], fallback: dict[str, Any]) -> dict[str, Any]:
    body = json.dumps({
        "model": CIRCLEFORGE_LLM_MODEL,
        "prompt": json.dumps(_prompt(build_role_context(context)), ensure_ascii=False),
        "stream": False,
        "format": "json",
        "options": {"temperature": CIRCLEFORGE_LLM_TEMPERATURE, "num_predict": CIRCLEFORGE_LLM_MAX_TOKENS},
    }).encode("utf-8")
    req = urllib.request.Request(
        f"{OLLAMA_HOST.rstrip('/')}/api/generate",
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=OLLAMA_TIMEOUT_SECONDS) as resp:
        payload = json.loads(resp.read().decode("utf-8"))
    parsed = json.loads(payload.get("response", "{}"))
    return _normalize(parsed, role, fallback, "ollama")


def _generate_via_openai_compatible(role: str, context: dict[str, Any], fallback: dict[str, Any]) -> dict[str, Any]:
    if not OPENAI_API_KEY:
        return fallback
    body = json.dumps({
        "model": CIRCLEFORGE_LLM_MODEL,
        "messages": [
            {"role": "system", "content": "Return strict JSON only."},
            {"role": "user", "content": json.dumps(_prompt(build_role_context(context)), ensure_ascii=False)},
        ],
        "temperature": CIRCLEFORGE_LLM_TEMPERATURE,
        "max_tokens": CIRCLEFORGE_LLM_MAX_TOKENS,
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
    return _normalize(parsed, role, fallback, "openai")


def _generate_via_embedded(role: str, context: dict[str, Any], fallback: dict[str, Any]) -> dict[str, Any]:
    model_path = CIRCLEFORGE_EMBEDDED_MODEL_PATH
    if not model_path.exists():
        return fallback
    prompt_payload = _prompt(build_role_context(context))
    prompt = json.dumps(prompt_payload, ensure_ascii=False)
    try:
        from llama_cpp import Llama  # type: ignore
    except Exception:
        server_result = _generate_via_embedded_server(role, prompt_payload, fallback)
        if server_result.get("provider") == "embedded":
            return server_result
        return _generate_via_embedded_cli(role, prompt, fallback)
    llm = Llama(model_path=str(model_path), n_ctx=2048, verbose=False)
    out = llm.create_completion(
        prompt=prompt,
        max_tokens=CIRCLEFORGE_LLM_MAX_TOKENS,
        temperature=CIRCLEFORGE_LLM_TEMPERATURE,
        stop=["\n\n"],
    )
    text = ((out.get("choices") or [{}])[0].get("text") or "{}").strip()
    parsed = json.loads(text)
    return _normalize(parsed, role, fallback, "embedded")


def _embedded_server_base() -> str:
    return os.getenv("CIRCLEFORGE_EMBEDDED_SERVER_URL", "http://127.0.0.1:18081/v1").rstrip("/")


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
    if not llama_server or not CIRCLEFORGE_EMBEDDED_MODEL_PATH.exists():
        return False
    state_dir = CIRCLEFORGE_FAILSAFE_DIR
    state_dir.mkdir(parents=True, exist_ok=True)
    log_path = state_dir / "embedded-llama-server.log"
    with open(log_path, "ab") as log_file:
        subprocess.Popen(
            [
                llama_server,
                "-m",
                str(CIRCLEFORGE_EMBEDDED_MODEL_PATH),
                "--host",
                host,
                "--port",
                str(port),
                "-c",
                "2048",
                "-n",
                str(max(CIRCLEFORGE_LLM_MAX_TOKENS, 128)),
                "--threads",
                os.getenv("CIRCLEFORGE_EMBEDDED_SERVER_THREADS", "4"),
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


def _generate_via_embedded_server(role: str, prompt_payload: dict[str, Any], fallback: dict[str, Any]) -> dict[str, Any]:
    server_base = _embedded_server_base()
    if not _ensure_embedded_server():
        return fallback
    body = json.dumps({
        "model": Path(CIRCLEFORGE_EMBEDDED_MODEL_PATH).name,
        "messages": [
            {"role": "system", "content": "Return strict JSON only."},
            {"role": "user", "content": json.dumps(prompt_payload, ensure_ascii=False)},
        ],
        "temperature": CIRCLEFORGE_LLM_TEMPERATURE,
        "max_tokens": max(CIRCLEFORGE_LLM_MAX_TOKENS, 220),
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
        except Exception:
            if attempt == 5:
                return fallback
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
        str(CIRCLEFORGE_EMBEDDED_MODEL_PATH),
        "-c",
        "2048",
        "-n",
        str(CIRCLEFORGE_LLM_MAX_TOKENS),
        "--temp",
        str(CIRCLEFORGE_LLM_TEMPERATURE),
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
        "why_it_matters": "CircleForge should know whether it has real direct local cognition or only fallback.",
    }
    result = generate_inner_thought("communicator", context)
    status_payload = status()
    return {
        "status": status_payload,
        "thought": result,
        "ok": result.get("provider") == "embedded",
    }


def status() -> dict[str, Any]:
    provider = (CIRCLEFORGE_LLM_PROVIDER or "fallback").strip().lower()
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
        "enabled": bool(CIRCLEFORGE_LLM_ENABLED),
        "provider": provider,
        "model": CIRCLEFORGE_LLM_MODEL,
        "embedded_default_model": CIRCLEFORGE_DEFAULT_EMBEDDED_MODEL,
        "embedded_default_filename": CIRCLEFORGE_DEFAULT_EMBEDDED_MODEL_FILENAME,
        "embedded_model_path": str(CIRCLEFORGE_EMBEDDED_MODEL_PATH),
        "embedded_model_exists": CIRCLEFORGE_EMBEDDED_MODEL_PATH.exists(),
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
    else:
        result["live"] = False
    return result
