"""
WESLR Relationship Depth CLI Commands

python3 -m weslr.commands.relationship_commands \\
  record --subject-type person --subject-id user_abc \\
  --signal shared_work_completed --weight 0.05 --verified

python3 -m weslr.commands.relationship_commands \\
  status --subject-type person --subject-id user_abc

python3 -m weslr.commands.relationship_commands \\
  observations --subject-type person --subject-id user_abc

python3 -m weslr.commands.relationship_commands \\
  summarize --subject-type person --subject-id user_abc
"""

import argparse
import json
import os
import sys

# Add workspace to path for imports
sys.path.insert(0, "/data/data/com.termux/files/home/.openclaw/workspace")

from weslr.relationship_depth import (
    RelationshipObservation,
    RelationshipState,
    InteractionSignal,
    record_interaction_outcome,
    load_relationship_observations,
    compute_relationship_state,
    classify_relationship_stage,
    summarize_relationship_state,
    get_relationship_tone,
    DEFAULT_WESLR_HOME,
)


SIGNAL_CHOICES = [s.value for s in InteractionSignal]


def cmd_record(args):
    base = args.base_path or DEFAULT_WESLR_HOME
    obs = record_interaction_outcome(
        subject_entity_type=args.subject_type,
        subject_entity_id=args.subject_id,
        signal=args.signal,
        verified=args.verified,
        weight=args.weight,
        target_entity_type=args.target_type or "system",
        target_entity_id=args.target_id or "weslr",
        channel_id=args.channel_id or "",
        source="cli",
        base_path=base,
    )
    print(f"Recorded: {obs.observation_id}  signal={obs.interaction_signal}  weight={obs.weight}  verified={obs.verified}")
    print(f"  subject={obs.subject_entity_type}:{obs.subject_entity_id}")
    print(f"  target={obs.target_entity_type}:{obs.target_entity_id}")
    print(f"  timestamp={obs.timestamp}")
    if obs.metadata:
        print(f"  metadata={obs.metadata}")


def cmd_status(args):
    base = args.base_path or DEFAULT_WESLR_HOME
    obs_list = load_relationship_observations(
        subject_entity_type=args.subject_type,
        subject_entity_id=args.subject_id,
        target_entity_type=args.target_type,
        target_entity_id=args.target_id,
        base_path=base,
    )
    if not obs_list:
        print(f"No relationship observations for {args.subject_type}:{args.subject_id}")
        if args.target_type or args.target_id:
            print(f"  (scoped to {args.target_type}:{args.target_id})")
        return

    state = compute_relationship_state(
        obs_list,
        identity_status=args.identity_status or "unknown",
    )
    print(f"Relationship state for {args.subject_type}:{args.subject_id}")
    if args.target_type or args.target_id:
        print(f"  target={args.target_type}:{args.target_id}")
    print(f"  depth={state.relationship_depth:.4f}  stage={state.relationship_stage}")
    print(f"  confidence={state.confidence:.4f}")
    print(f"  verified_interactions={state.verified_interaction_count}")
    print(f"  positive={state.positive_signal_count}  negative={state.negative_signal_count}")
    print(f"  first={state.first_interaction_at or 'n/a'}  last={state.last_interaction_at or 'n/a'}")
    if state.evidence:
        print(f"  evidence signals: {', '.join(state.evidence[:10])}")
    if state.limitations:
        print("  ⚠️  " + "  ".join(state.limitations[:3]))


def cmd_observations(args):
    base = args.base_path or DEFAULT_WESLR_HOME
    obs_list = load_relationship_observations(
        subject_entity_type=args.subject_type,
        subject_entity_id=args.subject_id,
        target_entity_type=args.target_type,
        target_entity_id=args.target_id,
        base_path=base,
        limit=args.limit or 50,
    )
    if not obs_list:
        print(f"No observations for {args.subject_type}:{args.subject_id}")
        return
    print(f"Observations ({len(obs_list)}):")
    for obs in obs_list:
        flag = "✓" if obs.verified else " "
        print(f"  [{flag}] {obs.timestamp[:19]}  {obs.interaction_signal}  w={obs.weight:+.3f}")


def cmd_summarize(args):
    base = args.base_path or DEFAULT_WESLR_HOME
    obs_list = load_relationship_observations(
        subject_entity_type=args.subject_type,
        subject_entity_id=args.subject_id,
        target_entity_type=args.target_type,
        target_entity_id=args.target_id,
        base_path=base,
    )
    if not obs_list:
        print(f"No observations for {args.subject_type}:{args.subject_id}")
        return

    state = compute_relationship_state(
        obs_list,
        identity_status=args.identity_status or "unknown",
    )
    tone = get_relationship_tone(state.relationship_depth, state.relationship_stage)

    print(f"=== Relationship Summary ===")
    print(f"subject: {args.subject_type}:{args.subject_id}")
    if args.target_type or args.target_id:
        print(f"target: {args.target_type}:{args.target_id}")
    print(f"depth: {state.relationship_depth:.4f} → {state.relationship_stage}")
    print(f"confidence: {state.confidence:.4f}")
    print(f"signals: +{state.positive_signal_count}/-{state.negative_signal_count}/±{state.neutral_signal_count}")
    print(f"first: {state.first_interaction_at or 'n/a'}  last: {state.last_interaction_at or 'n/a'}")
    print()
    print(f"=== Tone (expression only) ===")
    for k, v in tone.items():
        print(f"  {k}: {v}")


def main():
    parser = argparse.ArgumentParser(prog="weslr.relationship_commands")
    sub = parser.add_subparsers(dest="cmd")

    r = sub.add_parser("record", help="Record a relationship observation")
    r.add_argument("--subject-type", required=True, help="e.g. person, company, project")
    r.add_argument("--subject-id", required=True, help="Entity ID")
    r.add_argument("--signal", required=True, choices=SIGNAL_CHOICES, help="Interaction signal")
    r.add_argument("--verified", action="store_true", help="Mark as verified")
    r.add_argument("--weight", type=float, default=None, help="Override signal weight")
    r.add_argument("--target-type", default="system")
    r.add_argument("--target-id", default="weslr")
    r.add_argument("--channel-id", default="")
    r.add_argument("--base-path", default=None)

    s = sub.add_parser("status", help="Show relationship state")
    s.add_argument("--subject-type", required=True)
    s.add_argument("--subject-id", required=True)
    s.add_argument("--target-type", default=None)
    s.add_argument("--target-id", default=None)
    s.add_argument("--identity-status", default="unknown")
    s.add_argument("--base-path", default=None)

    o = sub.add_parser("observations", help="List observations")
    o.add_argument("--subject-type", required=True)
    o.add_argument("--subject-id", required=True)
    o.add_argument("--target-type", default=None)
    o.add_argument("--target-id", default=None)
    o.add_argument("--limit", type=int, default=50)
    o.add_argument("--base-path", default=None)

    m = sub.add_parser("summarize", help="Human-readable relationship summary")
    m.add_argument("--subject-type", required=True)
    m.add_argument("--subject-id", required=True)
    m.add_argument("--target-type", default=None)
    m.add_argument("--target-id", default=None)
    m.add_argument("--identity-status", default="unknown")
    m.add_argument("--base-path", default=None)

    args = parser.parse_args()
    if not args.cmd:
        parser.print_help()
        return

    if args.cmd == "record":
        cmd_record(args)
    elif args.cmd == "status":
        cmd_status(args)
    elif args.cmd == "observations":
        cmd_observations(args)
    elif args.cmd == "summarize":
        cmd_summarize(args)


if __name__ == "__main__":
    main()
