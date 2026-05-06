#!/usr/bin/env python3
"""
cli_voice.py — WESLR Voice Control CLI

Simple command interface for voice settings.
All commands modify ~/.weslr/voice_config.json.

Usage:
    python3 weslr/voice_layer/cli_voice.py status
    python3 weslr/voice_layer/cli_voice.py on
    python3 weslr/voice_layer/cli_voice.py off
    python3 weslr/voice_layer/cli_voice.py mute 60
    python3 weslr/voice_layer/cli_voice.py unmute
    python3 weslr/voice_layer/cli_voice.py text-only on
    python3 weslr/voice_layer/cli_voice.py text-only off
    python3 weslr/voice_layer/cli_voice.py autonomous on
    python3 weslr/voice_layer/cli_voice.py autonomous off
    python3 weslr/voice_layer/cli_voice.py quiet-hours set 22:00 07:00
    python3 weslr/voice_layer/cli_voice.py quiet-hours on
    python3 weslr/voice_layer/cli_voice.py quiet-hours off
    python3 weslr/voice_layer/cli_voice.py engine gtts
    python3 weslr/voice_layer/cli_voice.py cooldown 15

Author: pr0dus / Weslr
v1.0 — 2026-05-06
"""

import sys
import os
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from weslr.voice_layer.voice_config import VoiceConfig, load_voice_config


def status(config: VoiceConfig) -> None:
    s = config.status()
    print("WESLR Voice Status")
    print("=" * 40)
    print(f"  Voice enabled:        {s['voice_enabled']}")
    print(f"  Audio playback:       {s['audio_playback']}")
    print(f"  Autonomous speaking:  {s['autonomous']}")
    print(f"  Ambient loop:          {s['ambient_loop']}")
    print(f"  Text-only mode:       {s['text_only']}")
    print(f"  Muted:                {s['muted']}")
    if s['muted_until']:
        print(f"  Muted until:          {s['muted_until']}")
    print(f"  In quiet hours:       {s['quiet_hours']}")
    print(f"  Quiet hours range:    {s['quiet_hours_range']}")
    print(f"  Speaking allowed:     {s['speaking_allowed']}")
    print(f"  Autonomous allowed:   {s['autonomous_allowed']}")
    print(f"  Selected TTS engine:  {s['selected_engine']}")
    print(f"  Relationship learning: {s['relationship_learning']}")
    print()


def cmd_on(config: VoiceConfig) -> None:
    config.set_voice_enabled(True)
    config.save()
    print("Voice enabled. WESLR can speak.")


def cmd_off(config: VoiceConfig) -> None:
    config.set_voice_enabled(False)
    config.save()
    print("Voice disabled. WESLR is silent.")


def cmd_mute(config: VoiceConfig, minutes: int) -> None:
    config.set_muted(minutes)
    config.save()
    if minutes:
        print(f"WESLR muted for {minutes} minute(s).")
    else:
        print("WESLR unmuted.")


def cmd_unmute(config: VoiceConfig) -> None:
    config.unmute()
    config.save()
    print("WESLR unmuted.")


def cmd_text_only(config: VoiceConfig, enabled: bool) -> None:
    config.set_text_only(enabled)
    config.save()
    if enabled:
        print("Text-only mode enabled. Voice disabled but processing continues.")
    else:
        print("Text-only mode disabled. Voice normal.")


def cmd_autonomous(config: VoiceConfig, enabled: bool) -> None:
    config.set_autonomous_speaking(enabled)
    config.save()
    if enabled:
        print("Autonomous speaking enabled. WESLR may initiate speech.")
    else:
        print("Autonomous speaking disabled. WESLR only responds when asked.")


def cmd_quiet_hours(config: VoiceConfig, action: str, args: list) -> None:
    if action == "set":
        if len(args) < 2:
            print("Usage: quiet-hours set HH:MM HH:MM")
            return
        config.set_quiet_hours(True, start=args[0], end=args[1])
        config.save()
        print(f"Quiet hours set to {args[0]}–{args[1]}.")
    elif action == "on":
        config.set_quiet_hours(True)
        config.save()
        print("Quiet hours enabled.")
    elif action == "off":
        config.set_quiet_hours(False)
        config.save()
        print("Quiet hours disabled. WESLR may speak anytime.")
    else:
        print(f"Unknown quiet-hours action: {action}")
        print("Usage: quiet-hours [set HH:MM HH:MM | on | off]")


def cmd_engine(config: VoiceConfig, engine: str) -> None:
    valid = ["gtts", "piper", "espeak", "dummy"]
    if engine not in valid:
        print(f"Unknown engine: {engine}. Valid: {', '.join(valid)}")
        return
    config.set_selected_engine(engine)
    config.save()
    print(f"TTS engine set to {engine}.")


def cmd_cooldown(config: VoiceConfig, minutes: int) -> None:
    config.set_cooldown_minutes(minutes)
    config.save()
    print(f"Cooldown set to {minutes} minutes between utterances.")


def main() -> None:
    config = load_voice_config()

    if len(sys.argv) < 2:
        status(config)
        return

    cmd = sys.argv[1].lower()

    if cmd == "status":
        status(config)

    elif cmd == "on":
        cmd_on(config)

    elif cmd == "off":
        cmd_off(config)

    elif cmd == "mute":
        minutes = int(sys.argv[2]) if len(sys.argv) > 2 else None
        cmd_mute(config, minutes or 0)

    elif cmd == "unmute":
        cmd_unmute(config)

    elif cmd == "text-only":
        if len(sys.argv) < 3:
            print("Usage: text-only [on | off]")
            return
        enabled = sys.argv[2].lower() == "on"
        cmd_text_only(config, enabled)

    elif cmd == "autonomous":
        if len(sys.argv) < 3:
            print("Usage: autonomous [on | off]")
            return
        enabled = sys.argv[2].lower() == "on"
        cmd_autonomous(config, enabled)

    elif cmd == "quiet-hours":
        if len(sys.argv) < 3:
            print("Usage: quiet-hours [set HH:MM HH:MM | on | off]")
            return
        action = sys.argv[2].lower()
        rest = sys.argv[3:] if len(sys.argv) > 3 else []
        cmd_quiet_hours(config, action, rest)

    elif cmd == "engine":
        if len(sys.argv) < 3:
            print("Usage: engine [gtts | piper | espeak | dummy]")
            return
        cmd_engine(config, sys.argv[2].lower())

    elif cmd == "cooldown":
        if len(sys.argv) < 3:
            print("Usage: cooldown [minutes]")
            return
        cmd_cooldown(config, int(sys.argv[2]))

    else:
        print(f"Unknown command: {cmd}")
        print()
        print("Usage:")
        print("  status              — show current voice status")
        print("  on                  — enable voice")
        print("  off                 — disable voice")
        print("  mute [minutes]       — mute for N minutes (or indefinitely)")
        print("  unmute              — unmute")
        print("  text-only [on|off]  — text-only mode")
        print("  autonomous [on|off] — autonomous speaking")
        print("  quiet-hours [set HH:MM HH:MM|on|off]")
        print("  engine [gtts|piper|espeak|dummy]")
        print("  cooldown [minutes]")


if __name__ == "__main__":
    main()
