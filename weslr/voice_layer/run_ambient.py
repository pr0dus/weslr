#!/usr/bin/env python3
"""
run_ambient.py — WESLR Ambient Presence Loop Entry Point

Run the ambient presence loop for WESLR voice.

Default: ambient loop ON, voice ON, audio playback ON
Safe default for servers/headless: --once --text-only

Usage:
    python3 weslr/voice_layer/run_ambient.py                    # loop forever
    python3 weslr/voice_layer/run_ambient.py --once            # one tick, safe
    python3 weslr/voice_layer/run_ambient.py --once --text-only # one tick, audio suppressed
    python3 weslr/voice_layer/run_ambient.py --status         # show loop status
    python3 weslr/voice_layer/run_ambient.py --text-only      # loop, no audio
    python3 weslr/voice_layer/run_ambient.py --voice-off      # disable voice master switch
    python3 weslr/voice_layer/run_ambient.py --voice-on       # re-enable voice
    python3 weslr/voice_layer/run_ambient.py --mute 60         # mute for N minutes
    python3 weslr/voice_layer/run_ambient.py --daemon           # background, daemon mode

Author: pr0dus / Weslr
v1.0 — 2026-05-06
"""

import argparse
import signal
import sys
import os
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from weslr.voice_layer.voice_config import load_voice_config
from weslr.voice_layer.ambient_loop import AmbientPresenceLoop


# ── Signal handler for clean shutdown ───────────────────────────────────────

_loop: AmbientPresenceLoop = None


def signal_handler(signum, frame):
    print("\n[run_ambient] Received shutdown signal, stopping loop...")
    if _loop:
        _loop.stop()
    sys.exit(0)


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    global _loop

    parser = argparse.ArgumentParser(description="WESLR Ambient Presence Loop")
    parser.add_argument("--once", action="store_true",
                        help="Run one tick and exit (safe default for testing)")
    parser.add_argument("--text-only", action="store_true",
                        help="Suppress audio playback, show what WESLR would say")
    parser.add_argument("--status", action="store_true",
                        help="Show loop status and exit")
    parser.add_argument("--voice-off", action="store_true",
                        help="Disable voice master switch")
    parser.add_argument("--voice-on", action="store_true",
                        help="Re-enable voice master switch")
    parser.add_argument("--mute", type=int, metavar="MINUTES",
                        help="Mute WESLR for N minutes")
    parser.add_argument("--daemon", action="store_true",
                        help="Run as background daemon (fork)")
    parser.add_argument("--tick-interval", type=int, default=30, metavar="SECONDS",
                        help="Loop tick interval in seconds (default: 30)")
    parser.add_argument("--debug", action="store_true",
                        help="Print verbose tick output")
    args = parser.parse_args()

    # Load config
    config = load_voice_config()

    # Handle one-shot config changes
    if args.voice_off:
        config.set_voice_enabled(False)
        config.save()
        print("Voice disabled.")
        return

    if args.voice_on:
        config.set_voice_enabled(True)
        config.save()
        print("Voice enabled.")
        return

    if args.mute is not None:
        config.set_muted(args.mute)
        config.save()
        if args.mute > 0:
            print(f"WESLR muted for {args.mute} minute(s).")
        else:
            print("WESLR unmuted.")
        return

    # Status
    if args.status:
        loop = AmbientPresenceLoop(tenant_id="pr0dus")
        loop._init_components()
        st = loop.status()
        print("WESLR Ambient Loop Status")
        print("=" * 40)
        print(f"  Running:            {st['running']}")
        print(f"  Ticks:               {st['tick_count']}")
        print(f"  Utterances today:    {st['utterances_made']}")
        print(f"  Arrivals today:      {st['arrivals_today']}")
        print(f"  Last presence state: {st['last_presence_state']}")
        print(f"  Last spoke:          {st['last_speak_time'] or 'never'}")
        print()
        cfg = st['config']
        print("Voice Config:")
        print(f"  voice_enabled:           {cfg['voice_enabled']}")
        print(f"  audio_playback:          {cfg['audio_playback']}")
        print(f"  autonomous:              {cfg['autonomous']}")
        print(f"  ambient_loop:             {cfg['ambient_loop']}")
        print(f"  text_only:               {cfg['text_only']}")
        print(f"  muted:                   {cfg['muted']}")
        print(f"  quiet_hours:             {cfg['quiet_hours']}")
        print(f"  speaking_allowed:        {cfg['speaking_allowed']}")
        print(f"  autonomous_allowed:      {cfg['autonomous_allowed']}")
        print(f"  selected_engine:         {cfg['selected_engine']}")
        print()
        return

    # Text-only mode overrides audio playback
    if args.text_only:
        config.set_text_only(True)
        config.save()
        print("[run_ambient] Text-only mode enabled (audio suppressed)")

    # Create and run the loop
    loop = AmbientPresenceLoop(
        tenant_id="pr0dus",
        tick_interval_seconds=args.tick_interval,
    )
    _loop = loop

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    if args.daemon:
        # Fork to background
        pid = os.fork()
        if pid > 0:
            print(f"[run_ambient] Daemon started, PID {pid}")
            print(f"  Stop: kill {pid}")
            sys.exit(0)
        os.setsid()
        # Redirect stdout/stderr to log file
        log_path = Path.home() / ".weslr" / "ambient.log"
        log_path.parent.mkdir(parents=True, exist_ok=True)
        sys.stdout = open(log_path, "a")
        sys.stderr = sys.stdout

    print("WESLR Ambient Presence Loop")
    print("=" * 40)
    print(f"  Mode:      {'once' if args.once else 'continuous'}")
    print(f"  Text-only:  {args.text_only or config.text_only}")
    print(f"  Tick interval: {args.tick_interval}s")
    print()

    if args.once:
        # One safe tick
        print("[run_ambient] Running one tick...")
        result = loop.tick_once()
        _print_tick_result(result, debug=args.debug)
        print("[run_ambient] Done.")
    else:
        # Continuous loop
        print("[run_ambient] Starting loop. Ctrl+C to stop.")
        print()
        try:
            while True:
                result = loop.tick_once()
                _print_tick_result(result, debug=args.debug)
                time.sleep(args.tick_interval)
        except KeyboardInterrupt:
            print("\n[run_ambient] Interrupted.")
        finally:
            loop.stop()


def _print_tick_result(result, debug: bool = False) -> None:
    """Print structured tick result."""
    if result.error:
        print(f"  [tick:{result.tick_id}] ERROR: {result.error}")
        return

    changes = ", ".join(c.change_type for c in result.changes_detected) or "none"
    muted_str = " MUTED" if result.muted else ""
    quiet_str = " QUIET-HOURS" if result.quiet_hours else ""

    if result.utterances_made > 0:
        print(f"  [tick:{result.tick_id}] "
              f"changes={changes} "
              f"→ {result.utterances_made} utterance(s) made{muted_str}{quiet_str} "
              f"({result.duration_ms:.1f}ms)")
    elif debug:
        print(f"  [tick:{result.tick_id}] "
              f"changes={changes} "
              f"approved={result.utterances_approved} "
              f"made={result.utterances_made} "
              f"allowed={result.speaking_allowed}{muted_str}{quiet_str} "
              f"({result.duration_ms:.1f}ms)")


if __name__ == "__main__":
    main()
