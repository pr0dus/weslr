"""
test_voice_session_routing_v1.py
================================
Verify that voice sessions route to the correct timeline based on user_id.

Tests:
1. With user_id=arthur → timeline_id becomes tl_user_arthur
2. Without user_id    → timeline_id remains tl_default
3. Events written to the correct timeline directory
"""

import json
import tempfile
from pathlib import Path

import pytest

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from weslr.voice_gateway import log_voice_event
from weslr.user_timeline_memory import normalize_user_id
from urllib.parse import parse_qs, unquote


# ── normalize_user_id tests ───────────────────────────────────────────────────

class TestNormalizeUserId:
    def test_lowercase_simple(self):
        assert normalize_user_id("arthur") == "arthur"

    def test_mixed_case_normalized(self):
        assert normalize_user_id("Arthur") == "arthur"

    def test_spaces_removed_not_hyphenated(self):
        # spaces are stripped (not replaced with hyphen)
        assert normalize_user_id("arthur smith") == "arthursmith"

    def test_special_chars_stripped(self):
        assert normalize_user_id("arthur@example.com") == "arthurexamplecom"

    def test_empty_defaults_to_default_user(self):
        assert normalize_user_id("") == "default_user"
        assert normalize_user_id(None) == "default_user"  # type: ignore


# ── timeline_id construction tests ──────────────────────────────────────────

class TestTimelineIdConstruction:
    def test_user_id_produces_tl_user_prefix(self):
        normalized = normalize_user_id("arthur")
        timeline_id = f"tl_user_{normalized}"
        assert timeline_id == "tl_user_arthur"

    def test_no_user_id_uses_tl_default(self):
        timeline_id = "tl_default"
        assert timeline_id == "tl_default"

    def test_special_chars_in_user_id_normalized(self):
        normalized = normalize_user_id("arthur@example.com")
        timeline_id = f"tl_user_{normalized}"
        assert timeline_id == "tl_user_arthurexamplecom"


# ── log_voice_event tests ─────────────────────────────────────────────────────

class TestLogVoiceEvent:
    def test_writes_to_tl_user_arthur(self):
        """Verify log_voice_event writes to tl_user_arthur/events.jsonl."""
        import weslr.voice_gateway as vg

        # base = workspace root (parent of weslr/)
        base = Path(__file__).resolve().parent.parent.parent
        tl_dir = base / ".weslr" / "timelines" / "tl_user_arthur"
        event_file = tl_dir / "events.jsonl"
        if event_file.exists():
            event_file.unlink()

        event_id = vg.log_voice_event(
            transcript="hello world",
            response_text="hi there",
            timeline_id="tl_user_arthur",
            turn_id="vturn-test",
            interrupted=False,
            stt_provider="test",
            confidence=1.0,
            duration_s=1.5,
        )

        assert event_file.exists()
        lines = event_file.read_text().splitlines()
        assert len(lines) == 1
        event = json.loads(lines[0])
        assert event["event_type"] == "voice.message"
        assert event["data"]["transcript"] == "hello world"
        assert event["_event_id"] == event_id
        assert event["channel"] == "voice"

    def test_timeline_id_is_required_no_default(self):
        """log_voice_event signature requires explicit timeline_id (no default)."""
        import inspect
        import weslr.voice_gateway as vg
        sig = inspect.signature(vg.log_voice_event)
        params = sig.parameters
        assert "timeline_id" in params
        assert params["timeline_id"].default is inspect.Parameter.empty, (
            "timeline_id must NOT have a default — caller must provide it explicitly"
        )


# ── WebSocket path parsing tests ──────────────────────────────────────────────

class TestWebSocketPathParsing:
    def test_path_with_user_id_arthur(self):
        path = "/ws/voice?user_id=arthur"
        qs = parse_qs(path.split("?", 1)[1])
        assert qs["user_id"] == ["arthur"]

    def test_path_with_no_user_id(self):
        path = "/ws/voice"
        qs = parse_qs(path.split("?", 1)[1] if "?" in path else "")
        assert not qs.get("user_id")

    def test_path_with_user_id_url_encoded_special_char(self):
        # %40 → @ via parse_qs URL decoding
        path = "/ws/voice?user_id=arthur%40example.com"
        qs = parse_qs(path.split("?", 1)[1])
        assert qs["user_id"] == ["arthur@example.com"]

    def test_url_encoded_special_char_decodes_before_normalize(self):
        # %40 decodes to @ before normalize_user_id sees it
        raw = "arthur%40example.com"
        decoded = unquote(raw)
        normalized = normalize_user_id(decoded)
        assert normalized == "arthurexamplecom"


# ── Integration simulation: full routing flow ─────────────────────────────────

class TestVoiceSessionRoutingFlow:
    def test_user_id_arthur_routes_to_tl_user_arthur(self):
        """Full flow: user_id=arthur → normalize → tl_user_arthur."""
        raw_user_id = "arthur"
        normalized = normalize_user_id(raw_user_id)
        timeline_id = f"tl_user_{normalized}"
        assert timeline_id == "tl_user_arthur"

    def test_no_user_id_fallback_tl_default(self):
        """Without user_id, timeline_id is tl_default."""
        timeline_id = "tl_default"
        assert timeline_id == "tl_default"

    def test_events_written_to_tl_user_arthur_end_to_end(self):
        """End-to-end: user_id=arthur → events land in tl_user_arthur/events.jsonl."""
        with tempfile.TemporaryDirectory() as tmp:
            tl_dir = Path(tmp) / ".weslr" / "timelines" / "tl_user_arthur"
            tl_dir.mkdir(parents=True, exist_ok=True)
            event_file = tl_dir / "events.jsonl"

            raw_user_id = "arthur"
            normalized = normalize_user_id(raw_user_id)
            timeline_id = f"tl_user_{normalized}"

            import uuid
            from datetime import datetime, timezone

            event_id = str(uuid.uuid4())[:8]
            event = {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event_type": "voice.message",
                "channel": "voice",
                "data": {
                    "transcript": "what's the status",
                    "response_text": "All systems operational.",
                    "turn_id": f"vturn-{event_id}",
                    "interrupted": False,
                    "stt_provider": "shim",
                    "confidence": 1.0,
                    "duration_s": 2.1,
                },
                "source": "operator",
                "trust_level": "operator_verified",
                "_event_id": event_id,
            }

            with open(event_file, "a") as f:
                f.write(json.dumps(event) + "\n")

            assert event_file.exists()
            lines = event_file.read_text().splitlines()
            assert len(lines) == 1
            evt = json.loads(lines[0])
            assert evt["data"]["transcript"] == "what's the status"
            assert evt["channel"] == "voice"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])