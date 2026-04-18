"""
WESLR Voice Gateway — Phase 1A

WebSocket-based voice interaction gateway.
Handles audio streaming from browser client, STT transcription,
WESLR /chat integration, and timeline event logging.

STT is implemented as a shim (text injection) for Phase 1A.
Replace stt_transcribe() with the actual STT engine (whisper.cpp,
openai-whisper, or Groq Whisper) without changing the interface.

Architecture:
    [Browser] --WebSocket--> [VoiceGateway] --HTTP POST--> [WESLR /chat]
                       |
                       +-- timeline event --> [.weslr/timelines/]
                       |
                       +-- transcript JSON --> [Browser]

Transport: WebSocket (binary audio / JSON control)
STT shim: text injection (Phase 1A)
TTS: Web Speech API (browser-native, not server-side)
"""

import asyncio
import json
import logging
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import websockets

logger = logging.getLogger("voice_gateway")

# ── Config ─────────────────────────────────────────────────────────────────────

_weslr_http_port: int = 8001

def set_weslr_http_port(port: int):
    """Call this before start_voice_gateway() to tell the gateway which port
    the WESLR HTTP server is on. Defaults to 8001."""
    global _weslr_http_port
    _weslr_http_port = port


# ── STT Shim Interface ────────────────────────────────────────────────────────

async def stt_transcribe(audio_bytes: bytes, format: str = "wav") -> dict:
    """Transcribe audio to text.

    Phase 1A: This is a SHIM that accepts text injection from the browser.
    The browser sends a JSON control message with the transcript directly,
    bypassing STT. This proves the full transport and integration loop.

    Replace this function with the actual STT engine:
        - faster-whisper or openai-whisper (local)
        - whisper.cpp CLI subprocess
        - Groq Whisper API

    Returns:
        dict with keys:
            text: str — transcription text
            language: str — detected or assumed language
            confidence: float — confidence 0.0–1.0
            duration_s: float — audio duration in seconds
    """
    return {
        "text": "",
        "language": "en",
        "confidence": 1.0,
        "duration_s": 0.0,
        "shim_mode": True,
    }


# ── Chat Integration ──────────────────────────────────────────────────────────

def weslr_chat(text: str, timeline_id: str = "tl_default") -> dict:
    """Send text to WESLR /chat endpoint and return the response.

    Uses HTTP POST to the local WESLR server.
    """
    import urllib.request
    import urllib.error

    payload = json.dumps({
        "message": text,
        "timeline_id": timeline_id,
        "channel": "voice",
    }).encode("utf-8")

    req = urllib.request.Request(
        f"http://127.0.0.1:{_weslr_http_port}/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except Exception as e:
        logger.error(f"/chat call failed: {e}")
        return {"error": str(e), "message": "Voice gateway could not reach WESLR."}


# ── Timeline Event Logging ────────────────────────────────────────────────────

def log_voice_event(
    transcript: str,
    response_text: str,
    timeline_id: str = "tl_default",
    turn_id: Optional[str] = None,
    interrupted: bool = False,
    stt_provider: str = "shim",
    confidence: float = 1.0,
    duration_s: float = 0.0,
) -> str:
    """Write a voice.message event to the timeline.

    Returns the event_id.
    """
    event_id = str(uuid.uuid4())[:8]
    ts = datetime.now(timezone.utc).isoformat()

    event = {
        "timestamp": ts,
        "event_type": "voice.message",
        "channel": "voice",
        "data": {
            "transcript": transcript,
            "response_text": response_text,
            "language": "en",
            "confidence": confidence,
            "duration_s": duration_s,
            "turn_id": turn_id or f"vturn-{event_id}",
            "channel": "voice",
            "interrupted": interrupted,
            "client_id": "browser",
            "stt_provider": stt_provider,
            "tts_used": True,
        },
        "frame": None,
        "source": "operator",
        "trust_level": "operator_verified",
        "_event_id": event_id,
        "_annotation": None,
    }

    try:
        base = Path(__file__).resolve().parent.parent
        tl_dir = base / ".weslr" / "timelines" / timeline_id
        tl_dir.mkdir(parents=True, exist_ok=True)
        event_file = tl_dir / "events.jsonl"
        with open(event_file, "a") as f:
            f.write(json.dumps(event) + "\n")
        logger.info(f"Voice event logged: {event_id}")
    except Exception as e:
        logger.error(f"Failed to log voice event: {e}")

    return event_id


# ── WebSocket Message Types ───────────────────────────────────────────────────

# Browser → Gateway:
#   audio       — binary audio data (Phase 1A: not processed in shim mode)
#   transcript  — [Phase 1A shim] text transcript from browser
#   start       — session start signal
#   end         — session end signal

# Gateway → Browser:
#   transcript  — STT result (echo back in shim mode, real STT in production)
#   response    — WESLR /chat response text
#   ready       — gateway ready signal
#   error       — error message


# ── WebSocket Gateway ────────────────────────────────────────────────────────

async def voice_connection(ws, path=None):
    """Handle a single voice WebSocket connection.

    Phase 1A flow:
        1. Browser sends {"type": "transcript", "text": "what's the status"}
        2. Gateway calls weslr_chat(text)
        3. Gateway sends {"type": "response", "text": "...", "should_speak": true}
        4. Browser speaks via Web Speech API
        5. Gateway logs voice.event to timeline
    """
    connection_id = str(uuid.uuid4())[:8]
    logger.info(f"Voice connection opened: {connection_id}")
    timeline_id = "tl_default"
    turn_id = None

    try:
        await ws.send(json.dumps({"type": "ready", "connection_id": connection_id}))

        async for raw_msg in ws:
            if isinstance(raw_msg, bytes):
                # Binary audio — in shim mode, discarded
                # In production, pass to stt_transcribe()
                logger.debug(f"Received {len(raw_msg)} bytes of audio (shim mode — discarded)")
                continue

            try:
                msg = json.loads(raw_msg)
            except json.JSONDecodeError:
                await ws.send(json.dumps({"type": "error", "message": "Invalid JSON"}))
                continue

            msg_type = msg.get("type")

            if msg_type == "start":
                turn_id = f"vturn-{uuid.uuid4().hex[:8]}"
                await ws.send(json.dumps({"type": "ready", "turn_id": turn_id}))

            elif msg_type == "transcript":
                transcript = msg.get("text", "").strip()
                language = msg.get("language", "en")
                confidence = msg.get("confidence", 1.0)
                duration_s = msg.get("duration_s", 0.0)

                if not transcript:
                    await ws.send(json.dumps({
                        "type": "response",
                        "text": "I didn't catch that. Could you try again?",
                        "should_speak": True,
                    }))
                    continue

                logger.info(f"Voice transcript: {transcript[:60]}")

                chat_response = weslr_chat(transcript, timeline_id=timeline_id)
                response_text = chat_response.get("message", "")
                source = chat_response.get("source", "weslr")
                should_speak = bool(response_text)

                await ws.send(json.dumps({
                    "type": "response",
                    "text": response_text,
                    "should_speak": should_speak,
                    "source": source,
                }))

                log_voice_event(
                    transcript=transcript,
                    response_text=response_text,
                    timeline_id=timeline_id,
                    turn_id=turn_id,
                    interrupted=False,
                    stt_provider="shim",
                    confidence=confidence,
                    duration_s=duration_s,
                )

            elif msg_type == "end":
                logger.info(f"Voice session ended: {connection_id}")
                await ws.send(json.dumps({"type": "ready"}))

            else:
                await ws.send(json.dumps({
                    "type": "error",
                    "message": f"Unknown message type: {msg_type}",
                }))

    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Voice connection closed: {connection_id}")
    except Exception as e:
        logger.error(f"Voice gateway error [{connection_id}]: {e}")
        try:
            await ws.send(json.dumps({"type": "error", "message": str(e)}))
        except Exception:
            pass


# ── Server Launcher ──────────────────────────────────────────────────────────

_voice_server: Optional["websockets.WebSocketServer"] = None
_voice_thread: Optional[threading.Thread] = None


def start_voice_gateway(port: int = 8778, host: str = "127.0.0.1"):
    """Start the voice gateway WebSocket server in a background thread.

    Voice gateway runs on a separate port from WESLR's HTTP server.
    Browser connects to ws://host:port/ws/voice.
    """
    global _voice_server, _voice_thread

    if _voice_server is not None:
        logger.warning("Voice gateway already running")
        return

    async def run():
        global _voice_server
        _voice_server = await websockets.serve(
            voice_connection,
            host,
            port,
        )
        logger.info(f"Voice gateway started on ws://{host}:{port}")

    def run_async():
        asyncio.run(run())

    _voice_thread = threading.Thread(target=run_async, daemon=True, name="voice-gateway")
    _voice_thread.start()


def stop_voice_gateway():
    global _voice_server, _voice_thread
    if _voice_server is not None:
        _voice_server.close()
        _voice_server = None
    if _voice_thread is not None:
        _voice_thread = None
    logger.info("Voice gateway stopped")


if __name__ == "__main__":
    import argparse
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(levelname)s %(message)s")

    parser = argparse.ArgumentParser(description="WESLR Voice Gateway")
    parser.add_argument("--port", type=int, default=8778, help="WebSocket port")
    parser.add_argument("--host", default="127.0.0.1", help="bind host")
    parser.add_argument("--weslr-http-port", type=int, default=8001,
                        help="WESLR HTTP server port for /chat calls")
    args = parser.parse_args()

    if args.weslr_http_port:
        set_weslr_http_port(args.weslr_http_port)

    print(f"Starting WESLR Voice Gateway on ws://{args.host}:{args.port}")
    start_voice_gateway(port=args.port, host=args.host)
    try:
        threading.Event().wait()
    except KeyboardInterrupt:
        stop_voice_gateway()
