"""
WESLR Channel Identity CLI

Usage:
    python3 -m weslr.commands.channel_identity_commands <command> [options]

Commands:
    status   Show whether a binding exists and its identity status
    bind-local   Create and finalize a channel binding using a profile
    show     Display current binding details
    verify   Verify current evidence against stored binding
    unbind   Remove or disable binding
    backup   Create timestamped backup of current binding

All commands support:
    --path <channel_identity_path>
    --profile-path <user_profile_path>

Default paths: ~/.weslr/channel_identity.json, ~/.weslr/user_profile.json
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from weslr.channel_identity import (
    binding_exists,
    default_channel_binding,
    add_ip_evidence,
    finalize_binding,
    save_channel_binding,
    load_binding,
    validate_binding,
    summarize_binding,
    DEFAULT_WESLR_HOME,
    CHANNEL_BINDING_FILE,
    compute_binding_confidence,
)
from weslr.user_profile import load_user_profile


def _binding_path(args):
    p = getattr(args, "path", None)
    if p:
        return p
    return os.path.join(DEFAULT_WESLR_HOME, CHANNEL_BINDING_FILE)


def _profile_path(args):
    p = getattr(args, "profile_path", None)
    if p:
        return p
    return os.path.join(DEFAULT_WESLR_HOME, "user_profile.json")


def _collect_local_evidence(channel_type: str = "local_cli") -> dict:
    """Collect available local evidence (IP, session ID)."""
    import uuid
    evidence = {}

    # Session ID from environment
    session_id = os.environ.get("OPENCLAW_SESSION_ID", "")
    if session_id:
        evidence["session_id"] = session_id

    # Channel ID
    evidence["channel_id"] = f"{channel_type}:{session_id or uuid.uuid4().hex[:12]}"

    # Local IP (only if available and safe to read)
    try:
        import socket
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            evidence["local_ip"] = local_ip
        except Exception:
            pass
    except Exception:
        pass

    return evidence


def cmd_status(args):
    path = _binding_path(args)
    if binding_exists(os.path.dirname(path) if os.path.dirname(path) else DEFAULT_WESLR_HOME):
        b = load_binding(path)
        if b:
            print(f"Binding exists: {path}")
            print(f"  binding_id:    {b.binding_id}")
            print(f"  channel_type:  {b.channel_type}")
            print(f"  channel_id:    {b.channel_id}")
            print(f"  identity_status: {b.identity_status}")
            print(f"  confidence:    {b.confidence:.2f}")
            print(f"  bound_user_id: {b.bound_user_id}")
            print(f"  bound_profile_name: {b.bound_profile_name}")
            print(f"  trusted:       {b.trusted}")
            print(f"  created:       {b.created_at}")
            print(f"  updated:       {b.updated_at}")
            return
    print("No binding found.")


def cmd_bind_local(args):
    profile_path = _profile_path(args)
    binding_path = _binding_path(args)

    # Load profile
    profile = load_user_profile(profile_path)
    if not profile:
        print(f"No profile found at {profile_path}. Create a profile first with profile_commands.py init")
        sys.exit(1)

    channel_type = getattr(args, "channel_type", None) or "local_cli"

    # Create binding
    binding = default_channel_binding(
        profile_user_id=profile.user_id,
        profile_name=profile.preferred_name or profile.display_name or "unknown",
        channel_type=channel_type,
        created_by="explicit_operator_binding",
    )

    # Add local evidence
    local_ev = _collect_local_evidence(channel_type)
    if local_ev.get("session_id"):
        binding.evidence.append({
            "type": "session_id_match",
            "strength": "medium",
            "detail": f"OpenClaw session ID matched: {local_ev['session_id']}",
        })
    if local_ev.get("local_ip"):
        binding = add_ip_evidence(binding, local_ev["local_ip"])

    # Finalize and save
    binding = finalize_binding(binding)
    save_channel_binding(binding, path=binding_path, backup=True)

    print(f"Binding created. identity_status={binding.identity_status} confidence={binding.confidence:.2f}")
    if binding_path:
        print(f"  saved to: {binding_path}")
    if binding.identity_status == "channel_verified":
        print("  ✓ Channel verified via strong evidence")
    else:
        print("  Note: identity_status is not 'channel_verified' — add STRONG evidence")


def cmd_show(args):
    binding_path = _binding_path(args)
    b = load_binding(binding_path)
    if not b:
        print("No binding found.")
        sys.exit(1)

    print("=" * 50)
    print(f"Channel Binding: {b.binding_id}")
    print(f"  channel_type:      {b.channel_type}")
    print(f"  channel_id:        {b.channel_id}")
    print(f"  bound_user_id:     {b.bound_user_id}")
    print(f"  bound_profile_name: {b.bound_profile_name}")
    print(f"  identity_status:   {b.identity_status}")
    print(f"  confidence:        {b.confidence:.2f}")
    print(f"  trusted:           {b.trusted}")
    print(f"  created_at:        {b.created_at}")
    print(f"  updated_at:        {b.updated_at}")
    print(f"  created_by:        {b.created_by}")
    print(f"  limitations:")
    for lim in b.limitations:
        print(f"    - {lim}")
    print(f"  evidence ({len(b.evidence)} items):")
    for ev in b.evidence:
        print(f"    - type={ev.get('type')} strength={ev.get('strength')} detail={ev.get('detail', '')[:60]}")
    print("=" * 50)

    valid, reasons = validate_binding(b)
    if valid:
        print("Validation: OK")
    else:
        print("Validation: FAIL")
        for r in reasons:
            print(f"  - {r}")


def cmd_verify(args):
    binding_path = _binding_path(args)
    b = load_binding(binding_path)
    if not b:
        print("No binding found to verify against.")
        sys.exit(1)

    # Collect current evidence
    local_ev = _collect_local_evidence(b.channel_type)

    # Check session match
    session_ok = False
    session_ev = next((e for e in b.evidence if e.get("type") == "session_id_match"), None)
    if session_ev and local_ev.get("session_id"):
        session_ok = local_ev["session_id"] == session_ev.get("detail", "").split(":")[-1]
    elif not session_ev:
        session_ok = True  # No session evidence required

    # Check IP if present in binding
    ip_ok = True
    ip_ev = next((e for e in b.evidence if e.get("type") == "local_ip_match"), None)
    if ip_ev and local_ev.get("local_ip"):
        ip_ok = local_ev["local_ip"] == ip_ev.get("ip_address")

    current_confidence = compute_binding_confidence(b)

    # Determine verification status
    has_strong = any(e.get("strength") == "strong" for e in b.evidence)
    session_matches = session_ev is None or session_ok

    if has_strong and session_matches:
        print(f"VERIFIED: binding is trusted, identity_status={b.identity_status}, confidence={current_confidence:.2f}")
        if ip_ev and not ip_ok:
            print("  Warning: IP changed but strong evidence still present")
        print("  session_id: OK" if session_ok else "  session_id: MISMATCH")
    elif b.trusted:
        print(f"TRUSTED: binding is trusted (no strong evidence), status={b.identity_status}, confidence={current_confidence:.2f}")
    else:
        print(f"UNVERIFIED: binding has no strong evidence, identity_status={b.identity_status}, confidence={current_confidence:.2f}")
        if not session_ok:
            print("  session_id: MISMATCH")


def cmd_unbind(args):
    binding_path = _binding_path(args)
    b = load_binding(binding_path)
    if not b:
        print("No binding found.")
        return

    # Backup first
    backup_path = binding_path + f".backup-{__import__('datetime').datetime.now(__import__('datetime').timezone.utc).strftime('%Y%m%dT%H%M%S')}"
    try:
        with open(binding_path) as src:
            with open(backup_path, "w") as dst:
                dst.write(src.read())
        print(f"Backup saved: {backup_path}")
    except Exception:
        print("Warning: could not create backup")

    # Remove binding
    os.remove(binding_path)
    print(f"Binding removed: {binding_path}")


def cmd_backup(args):
    binding_path = _binding_path(args)
    b = load_binding(binding_path)
    if not b:
        print("No binding to back up.")
        return

    import datetime
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%dT%H%M%S")
    backup_path = binding_path + f".backup-{ts}"
    try:
        with open(binding_path) as src:
            with open(backup_path, "w") as dst:
                dst.write(src.read())
        print(f"Backup created: {backup_path}")
    except Exception as e:
        print(f"Backup failed: {e}")


def main():
    parser = argparse.ArgumentParser(description="WESLR Channel Identity CLI")
    sub = parser.add_subparsers(dest="command", required=True)

    p_status = sub.add_parser("status", help="Show binding status")
    p_status.add_argument("--path", help="Binding path override")

    p_bind = sub.add_parser("bind-local", help="Create/local channel binding for a profile")
    p_bind.add_argument("--path", help="Binding path override")
    p_bind.add_argument("--profile-path", help="Profile path override")
    p_bind.add_argument("--channel-type", dest="channel_type", default="local_cli", help="Channel type (default: local_cli)")

    p_show = sub.add_parser("show", help="Display binding details")
    p_show.add_argument("--path", help="Binding path override")
    p_show.add_argument("--profile-path", help="Profile path override")

    p_verify = sub.add_parser("verify", help="Verify current evidence against binding")
    p_verify.add_argument("--path", help="Binding path override")
    p_verify.add_argument("--profile-path", help="Profile path override")

    p_unbind = sub.add_parser("unbind", help="Remove binding")
    p_unbind.add_argument("--path", help="Binding path override")

    p_backup = sub.add_parser("backup", help="Create timestamped backup")
    p_backup.add_argument("--path", help="Binding path override")

    args = parser.parse_args()
    dispatch = {
        "status": cmd_status,
        "bind-local": cmd_bind_local,
        "show": cmd_show,
        "verify": cmd_verify,
        "unbind": cmd_unbind,
        "backup": cmd_backup,
    }
    fn = dispatch.get(args.command)
    if fn:
        fn(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()