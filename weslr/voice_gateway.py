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
from urllib.parse import parse_qs

from weslr.user_timeline_memory import normalize_user_id

logger = logging.getLogger("voice_gateway")

# ── Config ─────────────────────────────────────────────────────────────────────

_weslr_http_port: int = 8001

def set_weslr_http_port(port: int):
    """Call this before start_voice_gateway() to tell the gateway which port
    the WESLR HTTP server is on. Defaults to 8001."""
    global _weslr_http_port
    _weslr_http_port = port


# ── STT Shim Interface ────────────────────────────────────────────────────────

# whisper-cli path — set once at module load
_whisper_cli_path: str | None = None
_whisper_model_path: str | None = None


def _find_whisper_cli() -> tuple[str, str] | tuple[None, None]:
    """Locate whisper-cli binary and a model. Cached after first call."""
    global _whisper_cli_path, _whisper_model_path
    if _whisper_cli_path is not None:
        return _whisper_cli_path, _whisper_model_path

    import os
    candidates = [
        "/data/data/com.termux/files/home/whisper.cpp/build/bin/whisper-cli",
        "/usr/local/bin/whisper-cli",
        "whisper-cli",
    ]
    model_candidates = [
        "/data/data/com.termux/files/home/whisper.cpp/models/ggml-base.bin",
        "/data/data/com.termux/files/home/whisper.cpp/models/ggml-tiny.en.bin",
    ]
    cli = next((c for c in candidates if os.path.isfile(c)), None)
    model = next((m for m in model_candidates if os.path.isfile(m)), None)
    _whisper_cli_path = cli
    _whisper_model_path = model
    return cli, model


async def stt_transcribe(audio_bytes: bytes, format: str = "ogg") -> dict:
    """Transcribe audio to text using whisper-cli subprocess with ffmpeg normalization.

    Accepts: raw audio bytes from browser (ogg, webm, mp3, flac)
    Returns: {"text": str, "language": str, "confidence": float, "duration_s": float}

    All audio is converted to 16kHz mono WAV via ffmpeg before transcription.
    This ensures whisper-cli receives a known-compatible format regardless of
    the browser's actual output (ogg/webm/opus/vorbis/etc.).

    Falls back to empty text if whisper-cli or ffmpeg is unavailable or fails.
    The gateway will return a "couldn't understand" response.
    """
    import os
    import tempfile
    import json as _json
    import shutil

    cli_path, model_path = _find_whisper_cli()
    if not cli_path or not model_path:
        logger.warning("whisper-cli or model not found — shim fallback")
        return {"text": "", "language": "en", "confidence": 0.0, "duration_s": 0.0, "shim_mode": True}

    ffmpeg_path = shutil.which("ffmpeg")
    if not ffmpeg_path:
        logger.warning("ffmpeg not found — shim fallback")
        return {"text": "", "language": "en", "confidence": 0.0, "duration_s": 0.0, "shim_mode": True}

    # Write raw audio to a temp file with the detected extension
    suffix = f".{format}" if format in ("ogg", "wav", "mp3", "flac") else ".ogg"
    try:
        with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp_in:
            tmp_in.write(audio_bytes)
            tmp_in_path = tmp_in.name
    except Exception as e:
        logger.error(f"Failed to write audio temp file: {e}")
        return {"text": "", "language": "en", "confidence": 0.0, "duration_s": 0.0, "shim_mode": True}

    # Convert to 16kHz mono WAV via ffmpeg, then transcribe with whisper-cli
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_wav:
            tmp_wav_path = tmp_wav.name

        conv_proc = await asyncio.create_subprocess_exec(
            ffmpeg_path,
            "-i", tmp_in_path,
            "-ar", "16000",
            "-ac", "1",
            "-c:a", "pcm_s16le",
            "-y",
            "-hide_banner",
            "-loglevel", "error",
            tmp_wav_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        _, _ = await asyncio.wait_for(conv_proc.communicate(), timeout=30)
        if conv_proc.returncode != 0:
            logger.warning(f"ffmpeg conversion failed (code {conv_proc.returncode})")
            return {"text": "", "language": "en", "confidence": 0.0, "duration_s": 0.0, "shim_mode": True}

        proc = await asyncio.create_subprocess_exec(
            cli_path,
            "-t", "4",
            "-m", model_path,
            "-l", "en",
            "-oj",
            "-np",
            "-nt",
            "-f", tmp_wav_path,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
        stdout, _ = await asyncio.wait_for(proc.communicate(), timeout=60)

        if proc.returncode != 0:
            logger.warning(f"whisper-cli exited code {proc.returncode}")
            return {"text": "", "language": "en", "confidence": 0.0, "duration_s": 0.0, "shim_mode": True}

        raw = stdout.decode("utf-8", errors="replace").strip()
        if not raw:
            return {"text": "", "language": "en", "confidence": 0.0, "duration_s": 0.0, "shim_mode": False}

        try:
            result = _json.loads(raw)
            text = (
                result.get("transcription")
                or result.get("text", "")
                or "\n".join(
                    ln.get("transcription", ln.get("text", ""))
                    for ln in (result if isinstance(result, list) else [result])
                    if ln.get("transcription") or ln.get("text")
                )
            ).strip()
        except _json.JSONDecodeError:
            text = raw.strip()

        duration_s = os.path.getsize(tmp_wav_path) / 32000

        return {
            "text": text,
            "language": "en",
            "confidence": 1.0 if text else 0.0,
            "duration_s": duration_s,
            "shim_mode": False,
        }

    except asyncio.TimeoutError:
        logger.warning("STT timed out")
        return {"text": "", "language": "en", "confidence": 0.0, "duration_s": 0.0, "shim_mode": True}
    except Exception as e:
        logger.error(f"STT error: {e}")
        return {"text": "", "language": "en", "confidence": 0.0, "duration_s": 0.0, "shim_mode": True}
    finally:
        for p in (tmp_in_path, tmp_wav_path):
            try:
                os.unlink(p)
            except Exception:
                pass


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
    timeline_id: str,  # no default — caller must provide explicit timeline
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

    Timeline routing (V1):
        - Connect with ?user_id=<normalized_user> to use per-user timeline
          (e.g. ws://host:8778/ws/voice?user_id=arthur → tl_user_arthur)
        - Without user_id: falls back to "tl_default" for backward compatibility
        - Per-user timelines enable voice session continuity across sessions
    """
    connection_id = str(uuid.uuid4())[:8]

    # ── Timeline routing (V1) ────────────────────────────────────────────
    timeline_id = "tl_default"
    if path:
        try:
            qs = parse_qs(path.split("?", 1)[1] if "?" in path else "")
            raw_user_id = qs.get("user_id", [None])[0]
            if raw_user_id:
                normalized = normalize_user_id(raw_user_id)
                timeline_id = f"tl_user_{normalized}"
                logger.info(f"Voice timeline routed: {timeline_id}")
            else:
                logger.info("Voice connection: no user_id, using tl_default")
        except Exception as e:
            logger.warning(f"Failed to parse voice URL query params: {e}")

    logger.info(f"Voice connection opened: {connection_id} | timeline={timeline_id}")
    turn_id = None

    try:
        await ws.send(json.dumps({"type": "ready", "connection_id": connection_id}))

        async for raw_msg in ws:
            if isinstance(raw_msg, bytes):
                # Binary audio — call STT (shim in Phase 1B, real engine later)
                audio_data = raw_msg
                logger.debug(f"Received {len(audio_data)} bytes of audio — calling STT")
                try:
                    stt_result = await stt_transcribe(audio_data, format="webm")
                    transcript = stt_result.get("text", "").strip()
                    language = stt_result.get("language", "en")
                    confidence = stt_result.get("confidence", 1.0)
                    duration_s = stt_result.get("duration_s", 0.0)
                except Exception as e:
                    logger.error(f"STT failed: {e}")
                    transcript = ""

                if not transcript:
                    await ws.send(json.dumps({
                        "type": "response",
                        "text": "I couldn't understand that. Could you try again?",
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
                    stt_provider=stt_result.get("shim_mode") and "shim" or "unknown",
                    confidence=confidence,
                    duration_s=duration_s,
                )
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

            elif msg_type == "chat_text":
                # ── Phase 2: lightweight JSON text-chat ────────────────────────
                text = msg.get("text", "").strip()
                if not text:
                    await ws.send(json.dumps({
                        "type": "error",
                        "message": "chat_text requires a non-empty 'text' field",
                    }))
                else:
                    logger.info(f"WS text chat: {text[:60]}")
                    chat_response = weslr_chat(text, timeline_id=timeline_id)
                    response_text = chat_response.get("message", "")
                    source = chat_response.get("source", "weslr")
                    await ws.send(json.dumps({
                        "type": "chat_text_response",
                        "text": response_text,
                        "source": source,
                    }))

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
        # Keep event loop alive so background tasks keep running after serve() returns
        await asyncio.Event().wait()

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
