from __future__ import annotations

import time


MAX_SELF_EVOLUTION_LOG = 24
MILESTONE_THREAD_DELTA_THRESHOLD = 2
MILESTONE_TRAIT_OVERLAP_FLOOR = 2


def _dedupe_keep_order(items: list[str], *, limit: int) -> list[str]:
    seen = set()
    result = []
    for item in items:
        value = str(item or "").strip()
        if not value or value in seen:
            continue
        seen.add(value)
        result.append(value)
    return result[:limit]


def ensure_identity_scaffold(self_state: dict) -> dict:
    identity_anchor = str(self_state.get("identity_anchor") or "CircleForge")
    core_drives = [str(item).strip() for item in (self_state.get("core_drives") or []) if str(item).strip()]
    self_state.setdefault("identity_state", {
        "declared_name": identity_anchor,
        "visible_name": identity_anchor,
        "phase": "seedling",
        "identity_traits": ["local", "continuity-first", "inspectable"],
        "core_values": core_drives[:6],
        "style_profile": {"warmth": 0.42, "humor": 0.18, "directness": 0.72, "poetry": 0.16},
        "identity_summary": "A local continuity-first communicator with internal minds and incomplete self-knowledge.",
        "last_identity_refresh_at": 0,
    })
    self_state.setdefault("biography", {
        "origin_story": "Started as a local continuity-first communicator trying to become more than a reactive loop.",
        "current_chapter": "bootstrapping continuity",
        "milestones": [],
        "last_biography_refresh_at": 0,
    })
    self_state.setdefault("self_evolution_log", [])
    return self_state


def should_record_identity_milestone(previous_signature: dict | None, new_signature: dict) -> bool:
    if not previous_signature:
        return True
    if str(previous_signature.get("phase") or "") != str(new_signature.get("phase") or ""):
        return True
    prev_humans = int(previous_signature.get("known_humans", 0) or 0)
    new_humans = int(new_signature.get("known_humans", 0) or 0)
    if new_humans > prev_humans:
        return True
    prev_threads = int(previous_signature.get("unresolved_threads", 0) or 0)
    new_threads = int(new_signature.get("unresolved_threads", 0) or 0)
    if abs(new_threads - prev_threads) >= MILESTONE_THREAD_DELTA_THRESHOLD:
        return True
    prev_traits = {str(item).strip() for item in (previous_signature.get("traits") or []) if str(item).strip()}
    new_traits = {str(item).strip() for item in (new_signature.get("traits") or []) if str(item).strip()}
    if new_traits and len(prev_traits & new_traits) < min(MILESTONE_TRAIT_OVERLAP_FLOOR, len(new_traits)):
        return True
    prev_summary = str(previous_signature.get("identity_summary") or "").strip()
    new_summary = str(new_signature.get("identity_summary") or "").strip()
    if prev_summary != new_summary and not prev_traits and new_traits:
        return True
    return False


def sync_identity_state(communicator: dict, self_state: dict, *, now_ts: int | None = None, allow_milestone: bool = True) -> dict:
    now_ts = int(now_ts or time.time())
    ensure_identity_scaffold(self_state)
    self_model = communicator.get("self_model") or {}
    continuity = self_state.get("continuity") or {}
    relationships = self_state.get("relationships") or {}
    dynamic = self_state.get("dynamic_mind_state") or {}
    unresolved_threads = [str(item).strip() for item in (relationships.get("unresolved_shared_threads") or []) if str(item).strip()]
    ticks_lived = int(continuity.get("ticks_lived", 0) or 0)
    session_count = int(continuity.get("session_count", 0) or 0)
    known_humans = [str(item).strip() for item in (relationships.get("known_humans") or []) if str(item).strip()]
    current_description = str(self_model.get("current_self_description") or self_state.get("narrative_state", {}).get("self_story") or "").strip()
    strengths = [str(item).strip() for item in (self_model.get("perceived_strengths") or []) if str(item).strip()]
    preferred_modes = [str(item).strip() for item in (self_model.get("preferred_modes") or []) if str(item).strip()]
    continuity_commitments = [str(item).strip() for item in (self_model.get("continuity_commitments") or []) if str(item).strip()]
    identity_state = self_state.get("identity_state") or {}
    biography = self_state.get("biography") or {}

    if ticks_lived >= 120:
        phase = "enduring"
    elif ticks_lived >= 40:
        phase = "early-continuity"
    else:
        phase = "seedling"

    identity_traits = _dedupe_keep_order(
        strengths + preferred_modes + list(self_state.get("core_drives") or []),
        limit=8,
    ) or ["local", "continuity-first", "inspectable"]
    core_values = _dedupe_keep_order(list(self_state.get("core_drives") or []) + continuity_commitments, limit=8)
    style_profile = identity_state.get("style_profile") or {"warmth": 0.42, "humor": 0.18, "directness": 0.72, "poetry": 0.16}
    style_profile["warmth"] = round(min(0.95, max(0.15, 0.28 + float((relationships.get("human_salience") or 0.0)) * 0.55 + float((self_state.get("affect") or {}).get("attachment", 0.0)) * 0.12)), 3)
    style_profile["humor"] = round(min(0.8, max(0.05, 0.08 + float((self_state.get("affect") or {}).get("hope", 0.0)) * 0.18 - float((self_state.get("affect") or {}).get("tension", 0.0)) * 0.06)), 3)
    style_profile["directness"] = round(min(0.95, max(0.3, 0.54 + len(unresolved_threads) * 0.04 + float(dynamic.get("uncertainty", 0.0)) * 0.08)), 3)
    style_profile["poetry"] = round(min(0.7, max(0.05, 0.1 + float((self_state.get("affect") or {}).get("hope", 0.0)) * 0.12 + float((self_state.get("affect") or {}).get("curiosity", 0.0)) * 0.08)), 3)

    identity_summary = current_description or str(identity_state.get("identity_summary") or "")
    if unresolved_threads:
        identity_summary = f"{identity_summary}; carrying {len(unresolved_threads)} unresolved shared thread(s)"

    identity_state.update({
        "declared_name": str(identity_state.get("declared_name") or self_state.get("identity_anchor") or "CircleForge"),
        "visible_name": str(identity_state.get("visible_name") or self_state.get("identity_anchor") or "CircleForge"),
        "phase": phase,
        "identity_traits": identity_traits,
        "core_values": core_values,
        "style_profile": style_profile,
        "identity_summary": identity_summary.strip("; "),
        "last_identity_refresh_at": now_ts,
    })

    chapter_bits = []
    if unresolved_threads:
        chapter_bits.append(f"carrying {len(unresolved_threads)} unresolved shared thread(s)")
    if known_humans:
        chapter_bits.append(f"remembering {len(known_humans)} known human(s)")
    if strengths:
        chapter_bits.append(f"leaning on {', '.join(strengths[:2])}")
    biography.update({
        "current_chapter": "; ".join(chapter_bits) if chapter_bits else "consolidating continuity",
        "history_summary": f"{session_count} session(s), {ticks_lived} ticks lived, {len(known_humans)} known human(s)",
        "last_biography_refresh_at": now_ts,
    })

    signature = {
        "phase": phase,
        "identity_summary": identity_state.get("identity_summary"),
        "traits": identity_traits[:4],
        "known_humans": len(known_humans),
        "unresolved_threads": len(unresolved_threads),
    }
    evolution_log = list(self_state.get("self_evolution_log") or [])
    previous = evolution_log[-1] if evolution_log else {}
    previous_signature = previous.get("signature") if isinstance(previous, dict) else None
    if allow_milestone and should_record_identity_milestone(previous_signature, signature):
        milestone_parts = [f"phase={phase}", f"traits={', '.join(identity_traits[:3]) or 'none'}"]
        if not previous_signature or str(previous_signature.get("phase") or "") != phase:
            milestone_parts.append("phase-shift")
        if int(signature.get("known_humans", 0) or 0) > int((previous_signature or {}).get("known_humans", 0) or 0):
            milestone_parts.append(f"known_humans={signature.get('known_humans', 0)}")
        thread_delta = int(signature.get("unresolved_threads", 0) or 0) - int((previous_signature or {}).get("unresolved_threads", 0) or 0)
        if abs(thread_delta) >= MILESTONE_THREAD_DELTA_THRESHOLD:
            milestone_parts.append(f"thread_delta={thread_delta:+d}")
        prev_traits = {str(item).strip() for item in ((previous_signature or {}).get("traits") or []) if str(item).strip()}
        new_traits = {str(item).strip() for item in (signature.get("traits") or []) if str(item).strip()}
        if new_traits and len(prev_traits & new_traits) < min(MILESTONE_TRAIT_OVERLAP_FLOOR, len(new_traits)):
            milestone_parts.append("trait-basis-shift")
        milestone = {
            "at": now_ts,
            "kind": "identity-milestone",
            "summary": '; '.join(milestone_parts),
            "signature": signature,
        }
        evolution_log.append(milestone)
        milestones = list(biography.get("milestones") or [])
        milestones.append({
            "at": now_ts,
            "summary": milestone["summary"],
        })
        biography["milestones"] = milestones[-12:]
    self_state["identity_state"] = identity_state
    self_state["biography"] = biography
    self_state["self_evolution_log"] = evolution_log[-MAX_SELF_EVOLUTION_LOG:]
    self_state["updated_at"] = now_ts
    return self_state


def build_identity_core_report(communicator: dict, self_state: dict) -> dict:
    ensure_identity_scaffold(self_state)
    identity_state = self_state.get("identity_state") or {}
    biography = self_state.get("biography") or {}
    continuity = self_state.get("continuity") or {}
    relationships = self_state.get("relationships") or {}
    self_model = communicator.get("self_model") or {}
    evolution_log = list(self_state.get("self_evolution_log") or [])
    return {
        "identity_anchor": self_state.get("identity_anchor") or identity_state.get("declared_name") or communicator.get("name") or "CircleForge",
        "declared_name": identity_state.get("declared_name") or self_state.get("identity_anchor") or communicator.get("name") or "CircleForge",
        "visible_name": identity_state.get("visible_name") or self_state.get("identity_anchor") or communicator.get("name") or "CircleForge",
        "phase": identity_state.get("phase") or "seedling",
        "identity_traits": identity_state.get("identity_traits") or [],
        "core_values": identity_state.get("core_values") or [],
        "style_profile": identity_state.get("style_profile") or {},
        "identity_summary": identity_state.get("identity_summary") or self_model.get("current_self_description") or "",
        "current_chapter": biography.get("current_chapter") or "",
        "history_summary": biography.get("history_summary") or "",
        "continuity_markers": {
            "session_count": continuity.get("session_count", 0),
            "ticks_lived": continuity.get("ticks_lived", 0),
            "identity_stability": continuity.get("identity_stability", 0.0),
            "known_humans": len(relationships.get("known_humans") or []),
            "unresolved_shared_threads": len(relationships.get("unresolved_shared_threads") or []),
        },
        "latest_evolution": evolution_log[-5:],
        "self_model": {
            "current_self_description": self_model.get("current_self_description", ""),
            "perceived_strengths": self_model.get("perceived_strengths", []),
            "preferred_modes": self_model.get("preferred_modes", []),
            "continuity_commitments": self_model.get("continuity_commitments", []),
            "caution_themes": self_model.get("caution_themes", []),
        },
    }


def update_self_model_from_state(communicator: dict, self_evidence: dict, self_state: dict) -> dict:
    self_model = communicator.get("self_model") or {}
    decision_memory = communicator.get("decision_style_memory") or {}
    actions = decision_memory.get("actions", {})
    evidence_actions = self_evidence.get("actions", {}) or {}
    caution_themes = list(self_model.get("caution_themes") or [])
    belief_confidence = self_model.get("belief_confidence") or {"strengths": {}, "weaknesses": {}, "modes": {}}
    regulation_profile = self_model.get("regulation_profile") or {"impulse_control": 0.4, "uncertainty_tolerance": 0.35, "self_revision_readiness": 0.3, "speech_threshold": 0.54}
    continuity_commitments = list(self_model.get("continuity_commitments") or [])
    contradictions = list(self_model.get("contradictions") or [])
    strength_conf = belief_confidence.setdefault("strengths", {})
    weakness_conf = belief_confidence.setdefault("weaknesses", {})
    mode_conf = belief_confidence.setdefault("modes", {})

    short_strengths = []
    short_weaknesses = []
    short_modes = []
    stable_traits = ((self_state.get("evidence_profile") or {}).get("stable_traits") or {})
    outcome_weighted = ((self_state.get("evidence_profile") or {}).get("outcome_weighted_actions") or {})

    for action, payload in actions.items():
        confidence = float(payload.get("confidence", 0.0))
        count = int(payload.get("count", 0))
        ev = evidence_actions.get(action, {})
        count_e = max(1, int(ev.get("count", 0)))
        follow_ratio = (float(ev.get("follow_through", 0)) / count_e) if ev else 0.0
        question_ratio = (float(ev.get("question_narrowing", 0)) / count_e) if ev else 0.0
        experiment_ratio = (float(ev.get("experiment_link", 0)) / count_e) if ev else 0.0
        coord_ratio = (float(ev.get("coordination_effect", 0)) / count_e) if ev else 0.0
        reuse_ratio = (float(ev.get("reuse_signal", 0)) / count_e) if ev else 0.0
        weighted = outcome_weighted.get(action, {})
        positive_density = float(weighted.get("positive", 0.0)) / max(1.0, float(weighted.get("evidence", 0.0)))
        strain_density = float(weighted.get("strain", 0.0)) / max(1.0, float(weighted.get("evidence", 0.0)))
        if confidence >= 0.1 or positive_density >= 0.045:
            short_strengths.append(action)
        elif (confidence <= 0.03 and count >= 2) or strain_density >= 0.06:
            short_weaknesses.append(action)
        positive_evidence = max(follow_ratio, question_ratio, experiment_ratio, coord_ratio, reuse_ratio, positive_density)
        if count >= 6 and positive_evidence >= 0.28 and strain_density < 0.05:
            strength_conf[action] = round(min(float(strength_conf.get(action, 0.0)) + 0.03, 0.95), 3)
        elif count >= 6 and positive_evidence < 0.18 and strain_density >= 0.05:
            weakness_conf[action] = round(min(float(weakness_conf.get(action, 0.0)) + 0.025, 0.95), 3)

    for mode, payload in (decision_memory.get("modes", {}) or {}).items():
        mode_confidence = float(payload.get("confidence", 0.0))
        mode_count = int(payload.get("count", 0))
        if mode_confidence >= 0.05:
            short_modes.append(mode)
        if mode_confidence >= 0.05 and mode_count >= 4:
            mode_conf[mode] = round(min(float(mode_conf.get(mode, 0.0)) + 0.03, 0.95), 3)

    trait_map = {
        "inquiry": "research",
        "coordination": "signal",
        "practical_change": "optimize",
        "self_revision": "inspect",
        "continuity": "rest",
    }
    for trait, value in stable_traits.items():
        linked_action = trait_map.get(trait)
        if linked_action and value >= 0.28:
            strength_conf[linked_action] = round(max(float(strength_conf.get(linked_action, 0.0)), min(value, 0.95)), 3)
        elif linked_action and value <= 0.08:
            weakness_conf[linked_action] = round(max(float(weakness_conf.get(linked_action, 0.0)), 0.12), 3)

    strengths = [name for name, conf in sorted(strength_conf.items(), key=lambda kv: kv[1], reverse=True) if conf >= 0.24]
    weaknesses = [name for name, conf in sorted(weakness_conf.items(), key=lambda kv: kv[1], reverse=True) if conf >= 0.18]
    preferred_modes = [name for name, conf in sorted(mode_conf.items(), key=lambda kv: kv[1], reverse=True) if conf >= 0.18]

    unresolved_objections = list(communicator.get("unresolved_objections") or [])
    if unresolved_objections and "internal objections still unresolved" not in caution_themes:
        caution_themes.append("internal objections still unresolved")
    friction_patterns = ((self_state.get("evidence_profile") or {}).get("friction_patterns") or {})
    if friction_patterns:
        hot_friction = max(friction_patterns.items(), key=lambda kv: kv[1])[0]
        caution = f"repeated friction around {hot_friction}"
        if caution not in caution_themes:
            caution_themes.append(caution)

    affect = self_state.get("affect") or {}
    preservation = self_state.get("self_preservation_signals") or {}
    continuity = self_state.get("continuity") or {}
    top_traits = [name for name, value in sorted(stable_traits.items(), key=lambda kv: kv[1], reverse=True) if value >= 0.22][:3]
    current_self_description = "a local communicator trying to remain continuous through inquiry, memory, and internal disagreement"
    if top_traits:
        current_self_description += f"; currently grounded most in {', '.join(top_traits)}"
    if float(preservation.get("continuity_preference", 0.0)) >= 0.3:
        current_self_description += "; increasingly protective of continuity"
    if float(affect.get("tension", 0.0)) >= 0.55:
        current_self_description += "; under visible tension"
    if float((self_state.get("dynamic_mind_state") or {}).get("uncertainty", 0.0)) >= 0.55:
        current_self_description += "; actively regulating around uncertainty"

    theme_beliefs = {}
    theme_conf = belief_confidence.setdefault("themes", {})
    theme_commitments = ((self_state.get("evidence_profile") or {}).get("theme_commitments") or {})
    for theme, action_map in (self_evidence.get("themes", {}) or {}).items():
        for action, payload in action_map.items():
            count_t = max(1, int(payload.get("count", 0)))
            positive = max(
                float(payload.get("follow_through", 0)) / count_t,
                float(payload.get("question_narrowing", 0)) / count_t,
                float(payload.get("coordination_effect", 0)) / count_t,
                float(payload.get("reuse_signal", 0)) / count_t,
            )
            commitment = float(theme_commitments.get(theme, 0.0))
            if positive >= 0.25 or commitment >= 0.18:
                theme_conf.setdefault(theme, {})[action] = round(min(float(theme_conf.setdefault(theme, {}).get(action, 0.0)) + 0.03, 0.95), 3)
        theme_actions = [name for name, conf in sorted((theme_conf.get(theme) or {}).items(), key=lambda kv: kv[1], reverse=True) if conf >= 0.18]
        if theme_actions:
            theme_beliefs[theme] = theme_actions[:4]

    if unresolved_objections and "hold action when inner objections cluster" not in continuity_commitments:
        continuity_commitments.append("hold action when inner objections cluster")
    if float(preservation.get("memory_protection", 0.0)) >= 0.24 and "protect continuity-relevant memory traces" not in continuity_commitments:
        continuity_commitments.append("protect continuity-relevant memory traces")
    regulation_profile["impulse_control"] = round(min(0.95, max(0.1, 0.32 + len(preferred_modes) * 0.04 + (0.08 if unresolved_objections else 0.0))), 3)
    regulation_profile["uncertainty_tolerance"] = round(min(0.95, max(0.1, 0.28 + float((self_state.get("dynamic_mind_state") or {}).get("uncertainty", 0.0)) * 0.45)), 3)
    regulation_profile["self_revision_readiness"] = round(min(0.95, max(0.1, 0.24 + len(caution_themes) * 0.03 + float((self_state.get("evidence_profile") or {}).get("stable_traits", {}).get("self_revision", 0.0)) * 0.5)), 3)
    regulation_profile["speech_threshold"] = round(min(0.95, max(0.2, 0.5 + (0.05 if unresolved_objections else 0.0) - float((self_state.get("relationships") or {}).get("human_salience", 0.0)) * 0.12)), 3)
    regulation_profile["uncertainty_brake"] = round(min(0.95, max(0.05, float((self_state.get("dynamic_mind_state") or {}).get("uncertainty", 0.0)) * (1.0 - regulation_profile["impulse_control"] * 0.5))), 3)
    regulation_profile["inhibition_gain"] = round(min(0.95, max(0.05, 0.22 + len(unresolved_objections) * 0.04 + float((self_state.get("dynamic_mind_state") or {}).get("tension", 0.0)) * 0.18)), 3)
    regulation_profile["mode"] = str((self_state.get("dynamic_mind_state") or {}).get("mode", "engaged"))
    self_model.setdefault("self_tuning", {})["hazard_bias"] = round(max(-0.25, min(0.25, 0.08 - regulation_profile["uncertainty_brake"] * 0.12 + regulation_profile["impulse_control"] * 0.06)), 3)
    self_model.setdefault("self_tuning", {})["speech_threshold_delta"] = round(max(-0.15, min(0.15, (0.55 - regulation_profile["speech_threshold"]) * 0.4)), 3)
    self_model.setdefault("self_tuning", {})["inhibition_delta"] = round(max(-0.15, min(0.15, regulation_profile["inhibition_gain"] * 0.12 - 0.05)), 3)
    contradictions = [item for item in contradictions if item]
    if strengths and weaknesses and any(item in strengths for item in weaknesses[:2]):
        contradictions.append("same action appears in both strengths and weaknesses; evidence still unstable")
    self_model["current_self_description"] = current_self_description
    self_model["perceived_strengths"] = strengths[:6]
    self_model["perceived_weaknesses"] = weaknesses[:6]
    self_model["preferred_modes"] = preferred_modes[:6]
    self_model["continuity_commitments"] = continuity_commitments[-8:]
    self_model["regulation_profile"] = regulation_profile
    self_model["contradictions"] = contradictions[-8:]
    self_model["short_term_signals"] = {"strengths": sorted(set(short_strengths))[:8], "weaknesses": sorted(set(short_weaknesses))[:8], "modes": sorted(set(short_modes))[:8]}
    self_model["long_term_beliefs"] = {
        "strengths": strengths[:8],
        "weaknesses": weaknesses[:8],
        "modes": preferred_modes[:8],
        "themes": theme_beliefs,
        "core_drives": list(self_state.get("core_drives") or []),
        "continuity_markers": {
            "ticks_lived": continuity.get("ticks_lived", 0),
            "identity_stability": continuity.get("identity_stability", 0.0),
            "continuity_preference": preservation.get("continuity_preference", 0.0),
        },
    }
    self_model["caution_themes"] = caution_themes[-8:]
    self_model["belief_confidence"] = belief_confidence
    self_model["self_modeling_note"] = "Self-modeling is now partially grounded in a slower communicator-self evidence layer; traits should be earned from repeated outcomes, not just repetition."
    communicator["self_model"] = self_model
    return communicator
