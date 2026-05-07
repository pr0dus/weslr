"""
weslr/meaning_state_context.py

Gathers minimal state required to fulfill a ResponseObligation.
Does NOT write anything. Does NOT crash on missing sources.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class MeaningStateContext:
    sender_identity: Optional[str]
    known_user_status: str
    sender_confidence: float
    identity_evidence: list[dict]
    onboarding_profile_summary: Optional[str]
    relationship_depth: float
    memory_available: bool
    memory_summary: Optional[str]
    memory_sources_checked: list[str]
    self_model_summary: Optional[str]
    capability_summary: Optional[str]
    continuity_summary: Optional[str]
    timeline_summary: Optional[str]
    sources_used: list[str]
    sources_failed: list[dict]
    state_confidence: float
    # Entity-scoped memory fields
    memory_scope_used: Optional[str] = None
    entity_memory_available: Optional[str] = None
    entity_relationships_used: list[str] = field(default_factory=list)
    memory_access_limitations: list[str] = field(default_factory=list)


def gather_meaning_state(
    obligation,
    communicator_self: Optional[dict] = None,
    test_metadata: Optional[dict] = None,
    l2_session: Optional[dict] = None,
    l0_identity: Optional[dict] = None,
) -> MeaningStateContext:
    """
    Retrieve minimal state needed for the given obligation.
    Reads only what is required by the obligation type.
    """
    cs = communicator_self or {}
    meta = test_metadata or {}
    identity_state = cs.get("identity_state", {}) or {}
    continuity = (l2_session or {}).get("continuity", {}) or {}
    anchors = continuity.get("continuity_anchors", [])

    sources_used: list[str] = []
    sources_failed: list[dict] = []

    required = set(obligation.required_state)

    # ── Identity state ──────────────────────────────────────────────────────
    sender_identity = meta.get("sender_identity") or identity_state.get("_test_sender_identity")
    known_user_status = meta.get("known_user_status") or identity_state.get("_test_known_user_status") or "unknown"
    sender_confidence = float(meta.get("sender_confidence", 0.0))
    identity_evidence = meta.get("known_user_evidence") or identity_state.get("_test_known_user_evidence") or []

    if "identity_state" in required or "self_model" in required or "capability_model" in required:
        if sender_identity is not None:
            sources_used.append("test_identity_context")
        if identity_state:
            sources_used.append("identity_state")
        if meta:
            sources_used.append("test_metadata")

    # ── Session/profile ──────────────────────────────────────────────────────
    onboarding_profile: Optional[dict] = None
    onboarding_profile_summary: Optional[str] = None
    _profile_source: Optional[str] = None
    up = None
    if "session_profile" in required or "identity_state" in required:
        try:
            from weslr.user_profile import load_user_profile, summarize_user_profile
            up = load_user_profile()
            if up:
                onboarding_profile = up.to_dict()
                onboarding_profile_summary = summarize_user_profile(up)
                _profile_source = "user_profile"
                sources_used.append("user_profile")
        except Exception:
            pass
        if not onboarding_profile:
            onboarding_profile = meta.get("onboarding_profile") or identity_state.get("onboarding_profile") or cs.get("onboarding_profile")
            if onboarding_profile:
                sources_used.append("onboarding_profile")
                if not onboarding_profile_summary:
                    onboarding_profile_summary = f"role={onboarding_profile.get('role', 'unknown')}, project={onboarding_profile.get('project', 'unknown')}"

    # ── Upgrade known_user_status if profile exists but no verified channel ──
    if known_user_status == "unknown" and _profile_source == "user_profile":
        known_user_status = "onboarded_unverified"

    # ── Channel binding integration ──────────────────────────────────────────
    _channel_binding_status = meta.get("known_user_status") or identity_state.get("_test_known_user_status")
    _channel_confidence = float(meta.get("sender_confidence", 0.0))

    verified_statuses = {"channel_verified", "device_verified", "test_verified"}
    if _channel_binding_status in verified_statuses:
        known_user_status = _channel_binding_status
        if _channel_confidence > sender_confidence:
            sender_confidence = _channel_confidence
        if not sender_identity and meta.get("sender_identity"):
            sender_identity = meta["sender_identity"]
    elif _channel_binding_status == "claimed" and _profile_source == "user_profile":
        if known_user_status in ("claimed", "unknown"):
            known_user_status = "onboarded_unverified"
        sender_confidence = min(sender_confidence, 0.4)

    # ── Relationship depth ───────────────────────────────────────────────────
    relationship_depth = float(meta.get("relationship_depth", cs.get("relationship_depth", 0.0)))

    # ── Memory/continuity ───────────────────────────────────────────────────
    memory_available = False
    memory_summary: Optional[str] = None
    memory_sources_checked: list[str] = []
    memory_scope_used: Optional[str] = None
    entity_memory_available: Optional[str] = None
    entity_relationships_used: list[str] = []
    memory_access_limitations: list[str] = []
    continuity_summary: Optional[str] = None

    if "memory_state" in required or "continuity" in required:
        _fallback_ok = True

        if up is not None or onboarding_profile is not None:
            try:
                from weslr.entity_memory import (
                    resolve_memory_scopes,
                    load_scoped_memories,
                    resolve_person_memberships,
                    person_memory_id,
                    format_memory_response,
                )

                profile_user_id = (up.user_id if up else None) or (onboarding_profile.get("user_id") if onboarding_profile else None) or ""
                primary_projects = (up.primary_projects if up else []) or (onboarding_profile.get("primary_projects", []) if onboarding_profile else [])

                rels = resolve_person_memberships(profile_user_id)
                entity_relationships_used = [
                    f"{r.entity_type}/{r.entity_id} ({r.role})" for r in rels
                ]
                verified_from_rels = [r for r in rels if r.verified]

                scopes = resolve_memory_scopes(
                    identity_status=known_user_status,
                    user_id=profile_user_id,
                    primary_projects=primary_projects,
                    memberships=verified_from_rels,
                )
                scope_names = list(scopes.keys())
                memory_sources_checked.extend(scope_names)

                scoped_results = load_scoped_memories(scopes)
                scope_summaries: list[str] = []

                for scope_name, scope_data in scoped_results.items():
                    if scope_data["records_count"] > 0:
                        summary = scope_data["summary"]
                        scope_label = scope_data.get("scope_label", scope_name)
                        memory_available = True
                        _fallback_ok = False

                        if scope_name == "personal":
                            entity_memory_available = f"personal memory for {profile_user_id}"
                            memory_scope_used = "personal"
                            person_name = (up.preferred_name or up.display_name) if up else None
                            scope_summaries.append(
                                format_memory_response(summary, scope_label, person_name=person_name)
                            )
                        else:
                            entity_memory_available = f"{scope_label} memory available"
                            scope_summaries.append(format_memory_response(summary, scope_label))

                if scope_summaries:
                    memory_summary = " ".join(scope_summaries)
                    memory_sources_checked.extend(scope_names)

            except Exception as e:
                sources_failed.append({"source": "entity_memory", "reason": str(e)})
                _fallback_ok = True

        if memory_available:
            pass
        elif anchors and len(anchors) > 0:
            memory_available = True
            memory_summary = f"{len(anchors)} continuity anchors found"
            continuity_summary = memory_summary
            memory_sources_checked.append("continuity_anchors")
            sources_used.append("continuity_anchors")
            _fallback_ok = False
        elif _fallback_ok:
            memory_sources_checked.append("continuity_anchors")
            sources_failed.append({"source": "continuity_anchors", "reason": "no anchors found"})

        if not memory_available and _fallback_ok:
            try:
                import os
                import re
                mem_path = "/data/data/com.termux/files/home/.openclaw/workspace/memory"
                if os.path.isdir(mem_path):
                    files = sorted([f for f in os.listdir(mem_path) if f.endswith(".md")])
                    if files:
                        latest = files[-1]
                        with open(os.path.join(mem_path, latest)) as f:
                            raw = f.read()
                        date_match = re.search(r"(202[0-9]-[0-9]{2}-[0-9]{2})", latest)
                        date_str = date_match.group(1) if date_match else None
                        lines = [l.strip().lstrip("#-* ") for l in raw.split("\n") if l.strip()]
                        topic_lines = [
                            l for l in lines
                            if (
                                l and len(l) > 30
                                and not l.startswith("##")
                                and "**" not in l
                                and not l.startswith("-")
                                and not l.startswith("```")
                                and "session" not in l.lower()
                                and "source" not in l.lower()
                                and l not in ("Memory", "Notes", "Summary", "Date", "Time", "ID", "Key")
                                and not l.endswith("**")
                                and not re.match(r'^assistant:', l)
                                and not re.match(r'^user:', l)
                                and not re.match(r'^NO_REPLY', l)
                                and not re.match(r'^\{', l)
                                and not re.match(r'^\[?(Mon|Tue|Wed|Thu|Fri|Sat|Sun)', l)
                            )
                        ]
                        topic_lines = [
                            l for l in topic_lines
                            if not (re.match(r'^\{', l) or re.match(r'^\\}', l))
                            and not (':' in l and re.match(r'^[^:]+:', l) and l.strip()[-1] in (',', '}') and not l.startswith('http'))
                            and not re.match(r'^\d+\\.\\s', l)
                        ]
                        topic_str = " / ".join(topic_lines[:3]) if topic_lines else None
                        parts = []
                        if date_str:
                            parts.append(f"date: {date_str}")
                        if topic_str:
                            parts.append(f"topics: {topic_str}")
                        if parts:
                            memory_summary = "; ".join(parts)
                        else:
                            memory_summary = f"stored information from {latest}"
                        memory_available = True
                        memory_sources_checked.append(f"memory/{latest}")
                        sources_used.append(f"memory/{latest}")
            except Exception:
                sources_failed.append({"source": "memory_files", "reason": "read failed or not accessible"})

    # ── Self-model summary ───────────────────────────────────────────────────
    self_model_summary: Optional[str] = None
    if "self_model" in required:
        try:
            for fname in ["IDENTITY.md", "SOUL.md"]:
                path = f"/data/data/com.termux/files/home/.openclaw/workspace/{fname}"
                with open(path) as f:
                    content = f.read()[:400]
                    if content:
                        self_model_summary = f"{fname}: {content[:200]}..."
                        sources_used.append(fname)
                        break
        except Exception:
            sources_failed.append({"source": "self_model_files", "reason": "read failed"})

    # ── Capability summary ──────────────────────────────────────────────────
    capability_summary: Optional[str] = None
    if "capability_model" in required:
        if l0_identity:
            tier_desc = l0_identity.get("identity_state", {}).get("declared_name", "WESLR")
            capability_summary = f"WESLR entity intelligence system — {tier_desc}"
            sources_used.append("l0_identity")
        else:
            capability_summary = "WESLR entity intelligence system"
            sources_used.append("default_capability")

    # ── State confidence ────────────────────────────────────────────────────
    state_confidence = 0.0
    if known_user_status in ("verified", "channel_verified", "device_verified", "test_verified"):
        state_confidence += 0.4
    if memory_available:
        state_confidence += 0.2
    if sender_identity:
        state_confidence += 0.2
    if self_model_summary:
        state_confidence += 0.1
    if capability_summary:
        state_confidence += 0.1
    state_confidence = min(1.0, state_confidence)

    return MeaningStateContext(
        sender_identity=sender_identity,
        known_user_status=known_user_status,
        sender_confidence=sender_confidence,
        identity_evidence=identity_evidence,
        onboarding_profile_summary=onboarding_profile_summary,
        relationship_depth=relationship_depth,
        memory_available=memory_available,
        memory_summary=memory_summary,
        memory_sources_checked=memory_sources_checked,
        self_model_summary=self_model_summary,
        capability_summary=capability_summary,
        continuity_summary=continuity_summary,
        timeline_summary=None,
        sources_used=sources_used,
        sources_failed=sources_failed,
        state_confidence=state_confidence,
        memory_scope_used=memory_scope_used,
        entity_memory_available=entity_memory_available,
        entity_relationships_used=entity_relationships_used,
        memory_access_limitations=memory_access_limitations,
    )
