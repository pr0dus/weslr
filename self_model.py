from __future__ import annotations


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
