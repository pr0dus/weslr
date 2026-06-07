"""Pure metadata/schema helpers for WESLR RF Field Discovery v1.

This module is intentionally deterministic, JSON-safe, and fail-closed.
It does not perform live sensing, router access, repeater access, Home Assistant
access, packet capture, CSI collection, network scanning, runtime wiring,
provider/model/search/advisor calls, persistence, or marketplace actions.
"""

from __future__ import annotations

from copy import deepcopy
from typing import Any, Mapping

SCHEMA_VERSION_V1 = "rf_field_discovery_v1"
ALLOWED_PACKET_TYPES_V1 = {
    "rf_discovery_environment_candidate",
    "rf_discovery_anchor_candidate",
    "rf_discovery_signal_observation_candidate",
    "rf_discovery_baseline_candidate",
    "rf_discovery_pattern_candidate",
    "rf_discovery_strange_signal_candidate",
    "rf_discovery_calibration_experiment_candidate",
    "rf_discovery_visualization_frame_candidate",
    "rf_discovery_decision_outcome_candidate",
    "rf_discovery_value_assessment_candidate",
}
_REQUIRED_COMMON_FIELDS_V1 = (
    "packet_type",
    "schema_version",
    "missing_fields",
    "confidence",
    "notes",
    "raw_signal_included",
    "live_sensing_performed",
    "router_access_performed",
    "packet_capture_performed",
    "csi_collection_performed",
    "runtime_wiring_performed",
)


def to_rf_discovery_json_safe_v1(value: Any) -> Any:
    """Convert arbitrary values into JSON-safe primitives and containers."""

    if isinstance(value, Mapping):
        return {str(key): to_rf_discovery_json_safe_v1(val) for key, val in value.items()}
    if isinstance(value, list):
        return [to_rf_discovery_json_safe_v1(item) for item in value]
    if isinstance(value, tuple):
        return [to_rf_discovery_json_safe_v1(item) for item in value]
    if isinstance(value, set):
        return [to_rf_discovery_json_safe_v1(item) for item in sorted(value, key=lambda item: repr(item))]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)



def _clamp_confidence(value: Any) -> float:
    if isinstance(value, bool):
        raise ValueError("confidence must be numeric")
    if not isinstance(value, (int, float)):
        raise ValueError("confidence must be numeric")
    confidence = float(value)
    if confidence < 0.0 or confidence > 1.0:
        raise ValueError("confidence must be between 0 and 1")
    return confidence



def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return list(value)
    if isinstance(value, tuple):
        return list(value)
    return [value]



def _build_base_packet(packet_type: str, overrides: Mapping[str, Any] | None = None) -> dict[str, Any]:
    packet: dict[str, Any] = {
        "packet_type": packet_type,
        "schema_version": SCHEMA_VERSION_V1,
        "missing_fields": [],
        "confidence": 0.5,
        "notes": "synthetic discovery metadata",
        "raw_signal_included": False,
        "live_sensing_performed": False,
        "router_access_performed": False,
        "packet_capture_performed": False,
        "csi_collection_performed": False,
        "runtime_wiring_performed": False,
    }
    if overrides:
        packet.update(to_rf_discovery_json_safe_v1(deepcopy(dict(overrides))))
    packet["packet_type"] = packet_type
    packet["schema_version"] = SCHEMA_VERSION_V1
    packet["missing_fields"] = _as_list(packet.get("missing_fields"))
    packet["confidence"] = _clamp_confidence(packet.get("confidence", 0.5))
    packet["notes"] = str(packet.get("notes", ""))
    for field in ("raw_signal_included", "live_sensing_performed", "router_access_performed", "packet_capture_performed", "csi_collection_performed", "runtime_wiring_performed"):
        packet[field] = bool(packet.get(field, False))
    return packet



def build_rf_discovery_environment_candidate_v1(**overrides: Any) -> dict[str, Any]:
    return _build_base_packet(
        "rf_discovery_environment_candidate",
        {
            "environment_id": overrides.pop("environment_id", "env_synthetic_v1"),
            "label": overrides.pop("label", "synthetic discovery environment"),
            "coordinate_frame": overrides.pop("coordinate_frame", "rough_home_frame_v1"),
            "room_graph": overrides.pop(
                "room_graph",
                {
                    "rooms": [
                        {"room_id": "room_alpha", "label": "zone alpha"},
                        {"room_id": "room_beta", "label": "zone beta"},
                    ],
                },
            ),
            "wall_graph": overrides.pop("wall_graph", {"segments": []}),
            "opening_graph": overrides.pop("opening_graph", {"openings": []}),
            "floor_count": overrides.pop("floor_count", 1),
            "anchor_positions": overrides.pop("anchor_positions", []),
            "unknown_regions": overrides.pop("unknown_regions", ["unknown_corner"]),
            "material_hints": overrides.pop("material_hints", ["unknown_material"]),
            "calibration_paths": overrides.pop("calibration_paths", ["path_alpha_to_beta"]),
            "source_artifact_ref": overrides.pop("source_artifact_ref", "rf_field_discovery_artifact_v1"),
            "missing_fields": overrides.pop("missing_fields", ["exact_geometry", "material_details"]),
            "confidence": overrides.pop("confidence", 0.4),
            "notes": overrides.pop("notes", "synthetic environment candidate preserving floor-plan uncertainty"),
            "open_questions": overrides.pop(
                "open_questions",
                [
                    "How precise must floor plan geometry be?",
                    "Are material hints needed?",
                    "Can rough room graph work before exact coordinates?",
                    "Does floor plan improve signal interpretation?",
                ],
            ),
        } | overrides,
    )



def build_rf_discovery_anchor_candidate_v1(**overrides: Any) -> dict[str, Any]:
    return _build_base_packet(
        "rf_discovery_anchor_candidate",
        {
            "anchor_id": overrides.pop("anchor_id", "anchor_router_alpha"),
            "anchor_type": overrides.pop("anchor_type", "router"),
            "approximate_position": overrides.pop("approximate_position", {"x": 0, "y": 0, "z": 0}),
            "position_confidence": overrides.pop("position_confidence", 0.35),
            "band": overrides.pop("band", "2.4GHz"),
            "channel": overrides.pop("channel", 1),
            "observable_data_types": overrides.pop(
                "observable_data_types",
                ["rssi", "link_quality", "latency", "jitter", "packet_loss", "throughput"],
            ),
            "sampling_mode": overrides.pop("sampling_mode", "passive_metadata"),
            "mobility_state": overrides.pop("mobility_state", "unknown"),
            "trust_level": overrides.pop("trust_level", "low"),
            "notes": overrides.pop("notes", "synthetic anchor candidate with uncertain position and trust"),
            "missing_fields": overrides.pop("missing_fields", ["exact_position", "device_firmware_data"]),
            "confidence": overrides.pop("confidence", 0.45),
            "open_questions": overrides.pop(
                "open_questions",
                [
                    "Can repeater create enough path diversity?",
                    "Does client movement help or confuse?",
                    "Which anchor data is accessible from normal WLAN infrastructure?",
                ],
            ),
        } | overrides,
    )



def build_rf_discovery_signal_observation_candidate_v1(**overrides: Any) -> dict[str, Any]:
    return _build_base_packet(
        "rf_discovery_signal_observation_candidate",
        {
            "observation_id": overrides.pop("observation_id", "obs_synthetic_v1"),
            "timestamp": overrides.pop("timestamp", "2026-06-07T23:18:00Z"),
            "time_window": overrides.pop("time_window", {"start": "2026-06-07T23:18:00Z", "end": "2026-06-07T23:19:00Z"}),
            "source_anchor_id": overrides.pop("source_anchor_id", "anchor_router_alpha"),
            "target_anchor_or_client_id": overrides.pop("target_anchor_or_client_id", "client_alpha"),
            "path_id": overrides.pop("path_id", "path_alpha_beta"),
            "rssi": overrides.pop("rssi", -57),
            "link_quality": overrides.pop("link_quality", 71),
            "latency": overrides.pop("latency", 18.2),
            "jitter": overrides.pop("jitter", 2.1),
            "packet_loss": overrides.pop("packet_loss", 0.0),
            "throughput": overrides.pop("throughput", 48.6),
            "roaming_event": overrides.pop("roaming_event", False),
            "channel": overrides.pop("channel", 1),
            "band": overrides.pop("band", "2.4GHz"),
            "csi_amplitude": overrides.pop("csi_amplitude", None),
            "csi_phase": overrides.pop("csi_phase", None),
            "snr": overrides.pop("snr", 23.5),
            "raw_or_derived": overrides.pop("raw_or_derived", "derived"),
            "available_fields": overrides.pop(
                "available_fields",
                ["rssi", "link_quality", "latency", "jitter", "packet_loss", "throughput", "snr"],
            ),
            "missing_fields": overrides.pop("missing_fields", ["csi_amplitude", "csi_phase"]),
            "collection_context": overrides.pop("collection_context", "synthetic passive metadata packet"),
            "notes": overrides.pop("notes", "synthetic observation preserving raw/derived distinction"),
            "alternatives": overrides.pop(
                "alternatives",
                ["traffic artifact", "movement disturbance", "device roaming", "unknown"],
            ),
            "open_questions": overrides.pop(
                "open_questions",
                [
                    "Is RSSI enough for anything useful?",
                    "Can movement be separated from traffic?",
                    "When is CSI required?",
                ],
            ),
        } | overrides,
    )



def build_rf_discovery_baseline_candidate_v1(**overrides: Any) -> dict[str, Any]:
    return _build_base_packet(
        "rf_discovery_baseline_candidate",
        {
            "baseline_id": overrides.pop("baseline_id", "baseline_synthetic_v1"),
            "environment_id": overrides.pop("environment_id", "env_synthetic_v1"),
            "anchor_set": overrides.pop("anchor_set", ["anchor_router_alpha", "anchor_repeater_beta"]),
            "time_window": overrides.pop("time_window", {"start": "2026-06-07T23:18:00Z", "end": "2026-06-07T23:30:00Z"}),
            "conditions": overrides.pop("conditions", ["no movement", "steady placement", "normal traffic unknown"]),
            "expected_stability": overrides.pop("expected_stability", "moderate"),
            "observed_variance": overrides.pop("observed_variance", {"rssi": 1.8, "latency": 0.7}),
            "signal_summary": overrides.pop("signal_summary", "synthetic stable baseline summary"),
            "known_changes": overrides.pop("known_changes", []),
            "unknown_changes": overrides.pop("unknown_changes", ["ambient drift", "interference"]),
            "valid_until_condition": overrides.pop("valid_until_condition", "router_or_repeater_moved"),
            "confidence": overrides.pop("confidence", 0.5),
            "notes": overrides.pop("notes", "synthetic baseline with explicit invalidation conditions"),
            "invalidation_triggers": overrides.pop(
                "invalidation_triggers",
                [
                    "router moved",
                    "repeater moved",
                    "furniture changed",
                    "channel changed",
                    "major device changes",
                    "environment changed",
                    "unknown drift",
                ],
            ),
        } | overrides,
    )



def build_rf_discovery_pattern_candidate_v1(**overrides: Any) -> dict[str, Any]:
    return _build_base_packet(
        "rf_discovery_pattern_candidate",
        {
            "pattern_id": overrides.pop("pattern_id", "pattern_synthetic_v1"),
            "time_window": overrides.pop("time_window", {"start": "2026-06-07T23:18:00Z", "end": "2026-06-07T23:20:00Z"}),
            "affected_paths": overrides.pop("affected_paths", ["path_alpha_beta"]),
            "baseline_deviation": overrides.pop("baseline_deviation", {"rssi": 2.2, "latency": 1.1}),
            "repeated_motif": overrides.pop("repeated_motif", "unknown"),
            "possible_causes": overrides.pop(
                "possible_causes",
                ["physical movement", "WiFi traffic", "device roaming", "door movement", "appliance activity", "router/repeater change", "interference", "unknown"],
            ),
            "alternative_causes": overrides.pop(
                "alternative_causes",
                ["traffic artifact", "measurement noise", "ambiguous multipath"],
            ),
            "disturbance_score": overrides.pop("disturbance_score", 0.42),
            "stability_score": overrides.pop("stability_score", 0.58),
            "confidence": overrides.pop("confidence", 0.44),
            "unknowns": overrides.pop("unknowns", ["cause remains uncertain"]),
            "next_test_suggested": overrides.pop("next_test_suggested", "known_walk"),
            "raw_signal_refs": overrides.pop("raw_signal_refs", ["obs_synthetic_v1"]),
            "notes": overrides.pop("notes", "synthetic pattern candidate preserving alternatives and next probes"),
        } | overrides,
    )



def build_rf_discovery_strange_signal_candidate_v1(**overrides: Any) -> dict[str, Any]:
    return _build_base_packet(
        "rf_discovery_strange_signal_candidate",
        {
            "strange_signal_id": overrides.pop("strange_signal_id", "strange_synthetic_v1"),
            "time_window": overrides.pop("time_window", {"start": "2026-06-07T23:18:00Z", "end": "2026-06-07T23:18:30Z"}),
            "observed_features": overrides.pop("observed_features", ["bursty latency", "repeating jitter" ]),
            "why_strange": overrides.pop("why_strange", "pattern does not fit baseline or simple traffic explanation"),
            "matched_known_pattern": overrides.pop("matched_known_pattern", "none"),
            "unmatched_features": overrides.pop("unmatched_features", ["repeated spike cluster", "uncertain cadence"]),
            "compression_attempt": overrides.pop("compression_attempt", "synthetic grammar sketch only"),
            "candidate_grammar": overrides.pop("candidate_grammar", ["spike_cluster", "intermittent_drift"]),
            "hypotheses": overrides.pop("hypotheses", ["movement", "traffic", "interference", "unknown"]),
            "counterexamples_needed": overrides.pop("counterexamples_needed", ["traffic-only", "movement-only"]),
            "next_probe": overrides.pop("next_probe", "repeat under traffic-only and movement-only conditions"),
            "confidence": overrides.pop("confidence", 0.33),
            "notes": overrides.pop("notes", "synthetic strange signal packet that preserves uncertainty and next probes"),
        } | overrides,
    )



def build_rf_discovery_calibration_experiment_candidate_v1(**overrides: Any) -> dict[str, Any]:
    return _build_base_packet(
        "rf_discovery_calibration_experiment_candidate",
        {
            "experiment_id": overrides.pop("experiment_id", "experiment_synthetic_v1"),
            "experiment_type": overrides.pop("experiment_type", "known_walk"),
            "setup": overrides.pop("setup", "synthetic owner-controlled movement prompt"),
            "expected_unknown": overrides.pop("expected_unknown", "whether the chosen signal path changes repeatably"),
            "data_needed": overrides.pop("data_needed", ["rssi", "link_quality", "latency", "jitter"]),
            "owner_label": overrides.pop("owner_label", "synthetic_owner"),
            "time_window": overrides.pop("time_window", {"start": "2026-06-07T23:18:00Z", "end": "2026-06-07T23:24:00Z"}),
            "observed_signal_changes": overrides.pop("observed_signal_changes", ["slight_rssi_shift", "jitter_variation"]),
            "prediction_before_label": overrides.pop("prediction_before_label", "movement may create a weak but repeatable disturbance"),
            "actual_label": overrides.pop("actual_label", "synthetic labelled outcome"),
            "confidence_before": overrides.pop("confidence_before", 0.41),
            "confidence_after": overrides.pop("confidence_after", 0.48),
            "correction": overrides.pop("correction", "update threshold and uncertainty handling"),
            "lesson_learned": overrides.pop("lesson_learned", "synthetic calibration example only"),
            "next_branch": overrides.pop("next_branch", "prioritize_floor_plan_graph"),
            "hypotheses": overrides.pop("hypotheses", ["movement", "traffic", "unknown"]),
            "confidence": overrides.pop("confidence", 0.47),
            "notes": overrides.pop("notes", "synthetic calibration experiment preserving prediction, correction, and hypotheses"),
        } | overrides,
    )



def build_rf_discovery_visualization_frame_candidate_v1(**overrides: Any) -> dict[str, Any]:
    return _build_base_packet(
        "rf_discovery_visualization_frame_candidate",
        {
            "frame_id": overrides.pop("frame_id", "frame_synthetic_v1"),
            "timestamp": overrides.pop("timestamp", "2026-06-07T23:18:00Z"),
            "environment_ref": overrides.pop("environment_ref", "env_synthetic_v1"),
            "anchor_refs": overrides.pop("anchor_refs", ["anchor_router_alpha", "anchor_repeater_beta"]),
            "signal_path_estimates": overrides.pop("signal_path_estimates", [{"path_id": "path_alpha_beta", "intensity": 0.5}]),
            "stable_field_estimate": overrides.pop("stable_field_estimate", "blue-stable estimated area"),
            "disturbed_field_estimate": overrides.pop("disturbed_field_estimate", "green-disturbed estimated area"),
            "unknown_field_estimate": overrides.pop("unknown_field_estimate", "gray-unknown estimated area"),
            "confidence_overlay": overrides.pop("confidence_overlay", {"overall": 0.4, "local": 0.35}),
            "visual_metaphor": overrides.pop("visual_metaphor", ["blue stable areas", "green disturbance areas", "gray unknown areas"]),
            "explanation_panel": overrides.pop("explanation_panel", "estimated field interpretation with explicit uncertainty"),
            "next_calibration_need": overrides.pop("next_calibration_need", "compare against baseline and known_walk"),
            "warnings": overrides.pop("warnings", ["estimated, not literal vision", "uncertainty is visible"]),
            "confidence": overrides.pop("confidence", 0.39),
            "notes": overrides.pop("notes", "synthetic visualization frame that keeps the rendering open"),
        } | overrides,
    )



def build_rf_discovery_decision_outcome_candidate_v1(**overrides: Any) -> dict[str, Any]:
    return _build_base_packet(
        "rf_discovery_decision_outcome_candidate",
        {
            "decision_id": overrides.pop("decision_id", "decision_synthetic_v1"),
            "input_evidence": overrides.pop("input_evidence", ["baseline", "pattern", "experiment"]),
            "branch": overrides.pop("branch", "continue_router_repeater"),
            "reason": overrides.pop("reason", "synthetic evidence supports more discovery rather than closure"),
            "next_lane": overrides.pop("next_lane", "REVIEW_WESLR_RF_FIELD_DISCOVERY_SCHEMA_CANDIDATES_V1"),
            "archive_lesson": overrides.pop("archive_lesson", "preserve uncertainty and alternatives"),
            "open_questions": overrides.pop("open_questions", ["when to add CSI?", "when to add extra sensors?" ]),
            "value_signal": overrides.pop("value_signal", "exploratory value remains plausible"),
            "confidence": overrides.pop("confidence", 0.46),
            "notes": overrides.pop("notes", "synthetic decision outcome without release commitment"),
        } | overrides,
    )



def build_rf_discovery_value_assessment_candidate_v1(**overrides: Any) -> dict[str, Any]:
    return _build_base_packet(
        "rf_discovery_value_assessment_candidate",
        {
            "assessment_id": overrides.pop("assessment_id", "assessment_synthetic_v1"),
            "usefulness_signals": overrides.pop("usefulness_signals", ["repeatable motif", "useful vector candidate"]),
            "repeatability": overrides.pop("repeatability", "unknown"),
            "hardware_complexity": overrides.pop("hardware_complexity", "low_to_moderate"),
            "visualization_value": overrides.pop("visualization_value", "promising"),
            "calibration_cost": overrides.pop("calibration_cost", "unknown"),
            "marketplace_potential": overrides.pop("marketplace_potential", "future_only"),
            "synthetic_demo_possible": overrides.pop("synthetic_demo_possible", True),
            "private_data_dependency": overrides.pop("private_data_dependency", False),
            "next_investment_recommendation": overrides.pop("next_investment_recommendation", "continue discovery before release decisions"),
            "confidence": overrides.pop("confidence", 0.43),
            "notes": overrides.pop("notes", "synthetic value assessment that does not activate marketplace release"),
        } | overrides,
    )



def validate_rf_discovery_candidate_packet_v1(packet: Any) -> bool:
    if not isinstance(packet, dict):
        return False
    for field in _REQUIRED_COMMON_FIELDS_V1:
        if field not in packet:
            return False
    if packet.get("packet_type") not in ALLOWED_PACKET_TYPES_V1:
        return False
    if packet.get("schema_version") != SCHEMA_VERSION_V1:
        return False
    if not isinstance(packet.get("missing_fields"), list):
        return False
    try:
        confidence = _clamp_confidence(packet.get("confidence"))
    except Exception:
        return False
    if confidence != packet.get("confidence") and not isinstance(packet.get("confidence"), int):
        return False
    for field in (
        "raw_signal_included",
        "live_sensing_performed",
        "router_access_performed",
        "packet_capture_performed",
        "csi_collection_performed",
        "runtime_wiring_performed",
    ):
        if packet.get(field) is not False:
            return False
    return True



def summarize_rf_discovery_candidate_packet_v1(packet: Any) -> dict[str, Any]:
    if not isinstance(packet, dict):
        return {"valid": False, "reason": "packet must be a dict"}
    summary = {
        "valid": validate_rf_discovery_candidate_packet_v1(packet),
        "packet_type": packet.get("packet_type"),
        "schema_version": packet.get("schema_version"),
        "confidence": packet.get("confidence"),
        "missing_fields": list(packet.get("missing_fields", [])) if isinstance(packet.get("missing_fields"), list) else [],
        "missing_fields_count": len(packet.get("missing_fields", [])) if isinstance(packet.get("missing_fields"), list) else 0,
        "notes": packet.get("notes"),
        "raw_signal_included": packet.get("raw_signal_included"),
        "live_sensing_performed": packet.get("live_sensing_performed"),
        "summary": f"{packet.get('packet_type')} | confidence={packet.get('confidence')} | missing={len(packet.get('missing_fields', [])) if isinstance(packet.get('missing_fields'), list) else 0}",
    }
    return to_rf_discovery_json_safe_v1(summary)



def build_rf_discovery_synthetic_examples_v1() -> dict[str, Any]:
    examples = [
        build_rf_discovery_environment_candidate_v1(),
        build_rf_discovery_anchor_candidate_v1(),
        build_rf_discovery_signal_observation_candidate_v1(),
        build_rf_discovery_baseline_candidate_v1(),
        build_rf_discovery_pattern_candidate_v1(),
        build_rf_discovery_strange_signal_candidate_v1(),
        build_rf_discovery_calibration_experiment_candidate_v1(),
        build_rf_discovery_visualization_frame_candidate_v1(),
        build_rf_discovery_decision_outcome_candidate_v1(),
        build_rf_discovery_value_assessment_candidate_v1(),
    ]
    return {
        "examples": examples,
        "packet_types": [packet["packet_type"] for packet in examples],
        "synthetic_only": True,
        "notes": "synthetic discovery examples only; synthetic metadata only",
    }


__all__ = [
    "ALLOWED_PACKET_TYPES_V1",
    "SCHEMA_VERSION_V1",
    "build_rf_discovery_anchor_candidate_v1",
    "build_rf_discovery_baseline_candidate_v1",
    "build_rf_discovery_calibration_experiment_candidate_v1",
    "build_rf_discovery_decision_outcome_candidate_v1",
    "build_rf_discovery_environment_candidate_v1",
    "build_rf_discovery_pattern_candidate_v1",
    "build_rf_discovery_signal_observation_candidate_v1",
    "build_rf_discovery_strange_signal_candidate_v1",
    "build_rf_discovery_synthetic_examples_v1",
    "build_rf_discovery_value_assessment_candidate_v1",
    "build_rf_discovery_visualization_frame_candidate_v1",
    "summarize_rf_discovery_candidate_packet_v1",
    "to_rf_discovery_json_safe_v1",
    "validate_rf_discovery_candidate_packet_v1",
]
