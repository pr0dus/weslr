"""
local_bridge.py — Thin local interface bridge for Weslr

Routes all local input (text, STT transcript) through the canonical main door:
    weslr.ingress_adapter.route_request()

Does NOT implement its own cognition, routing, or governance.
Does NOT bypass the existing voice pipeline.

Usage:
    python3 weslr/voice_layer/local_bridge.py --text "Hello Weslr"
    python3 weslr/voice_layer/local_bridge.py --chat   # interactive REPL
    python3 weslr/voice_layer/local_bridge.py --chat --voice  # REPL + TTS response
    python3 weslr/voice_layer/local_bridge.py --stt | tee /dev/stderr
        # Pipe STT transcript to stdin of this script

Environment:
    WESLR_DOMAIN     Override domain (default: general)
    WESLR_PERSONA    Override persona (default: local operator)
    WESLR_HOME       Weslr home directory (default: ~/.weslr)
"""

from __future__ import annotations

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Optional

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from weslr.ingress_adapter import route_request
from weslr.voice_layer import TTSEngine, VoiceOutputLayer, PersonalityModulator


# ── Response renderer ────────────────────────────────────────────────────────

def _render_response(response) -> str:
    """Extract content from a Response object."""
    if hasattr(response, "content"):
        return response.content
    elif hasattr(response, "message"):
        return response.message
    elif isinstance(response, dict):
        return response.get("content", response.get("message", str(response)))
    return str(response)


# ── Main door call ───────────────────────────────────────────────────────────

def send_to_weslr(
    message: str,
    domain: str = "general",
    persona: str = "local operator",
    voice_response: bool = False,
) -> str:
    """
    Send a message through the canonical main door.
    Returns the response content as a string.
    """
    raw = {
        "message": message,
        "domain": domain,
        "persona": persona,
    }

    response = route_request(raw)
    content = _render_response(response)

    if voice_response:
        _speak_response(content)

    return content


def _speak_response(text: str) -> None:
    """Speak a text response via the voice layer."""
    try:
        tts = TTSEngine.detect()
        result = tts.speak(text)
        if result.success and result.audio_data:
            _try_playback(result.audio_data)
    except Exception as e:
        print(f"[local_bridge] TTS error: {e}", file=sys.stderr)


def _try_playback(audio_data: bytes) -> None:
    """Play audio via termux-media-player."""
    import tempfile, subprocess, os

    with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
        f.write(audio_data)
        path = f.name

    try:
        r = subprocess.run(
            ["termux-media-player", "play", path],
            capture_output=True, text=True, timeout=20,
        )
    finally:
        try:
            os.unlink(path)
        except Exception:
            pass


# ── Interactive REPL ─────────────────────────────────────────────────────────

def repl(voice_response: bool = False, domain: str = "general", persona: str = "local operator"):
    """Interactive REPL for local Weslr interaction."""
    print("Weslr Local Bridge")
    print("  Type your message and press Enter.")
    print("  :voice to toggle voice response")
    print("  :domain <name> to change domain")
    print("  :quit to exit")
    print()

    voice = voice_response
    while True:
        try:
            user_input = input("you: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not user_input:
            continue

        if user_input == ":quit":
            break
        elif user_input == ":voice":
            voice = not voice
            print(f"  voice {'ON' if voice else 'OFF'}")
            continue
        elif user_input.startswith(":domain "):
            domain = user_input[8:].strip()
            print(f"  domain → {domain}")
            continue

        print(f"weslr: ", end="", flush=True)
        try:
            reply = send_to_weslr(user_input, domain=domain, persona=persona, voice_response=voice)
            print(reply)
        except Exception as e:
            print(f"error: {e}")


# ── STT pipeline bridge ──────────────────────────────────────────────────────

def stt_bridge():
    """
    Read STT transcripts from stdin, one per line, and send to main door.
    Designed to pipe from an STT tool: mic → transcript → this → main door.

    Each line of input is treated as one message.
    """
    print("[local_bridge] STT bridge active — reading transcripts from stdin...", file=sys.stderr)
    for line in sys.stdin:
        transcript = line.strip()
        if not transcript:
            continue
        print(f"[local_bridge] → {transcript[:80]}", file=sys.stderr)
        try:
            reply = send_to_weslr(transcript)
            print(f"[local_bridge] weslr: {reply[:200]}")
        except Exception as e:
            print(f"[local_bridge] error: {e}", file=sys.stderr)


# ── CLI entry point ──────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Weslr Local Bridge")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--text", metavar="MSG", help="Send a single text message and print response")
    group.add_argument("--chat", action="store_true", help="Interactive REPL")
    group.add_argument("--stt", action="store_true", help="STT bridge mode (read transcripts from stdin)")

    parser.add_argument("--voice", action="store_true", help="Enable TTS voice response")
    parser.add_argument("--domain", default=os.environ.get("WESLR_DOMAIN", "general"),
                        help="Domain (default: general)")
    parser.add_argument("--persona", default=os.environ.get("WESLR_PERSONA", "local operator"),
                        help="Persona (default: local operator)")

    args = parser.parse_args()

    if args.text:
        reply = send_to_weslr(args.text, domain=args.domain, persona=args.persona, voice_response=args.voice)
        print(reply)
    elif args.chat:
        repl(voice_response=args.voice, domain=args.domain, persona=args.persona)
    elif args.stt:
        stt_bridge()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()