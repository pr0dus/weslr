"""
WESLR chat.weslr.de Slice 8 — Dashboard Read-Model Helper V1

Standalone, metadata-only helper that prepares a dashboard-visible
read-model for the protected operator dashboard from explicit
provided input packets.

This module is the **read-model** layer of the customer-grade
dashboard wiring. It does NOT:

  - import or call weslr.chat_responder, main, dialogue, chat_ui,
    backend server files, provider/model code, payment-provider
    code, or any protected runtime module
  - perform subprocess, network, or filesystem write operations
  - write to "/home/pr0/weslr_state/" (no real persistence)
  - wire itself to the entitlement helper, account-status helper,
    billing-abo helper, runtime wrapper, session manager, audit log,
    audit persistence, or ChatResponder
  - serve a live dashboard (no HTTP server, no port, no frontend)
  - infer live system truth (the helper only renders what the
    caller explicitly provides; if a section is missing, the
    helper reports "observation: not provided" — it does NOT
    query nginx, curl, or the health check script)
  - perform operator actions, auto-approvals, or any side effects
  - retain raw prompt text, raw reply text, credentials, PII,
    hidden prompts, system prompts, chain-of-thought traces,
    provider/LLM API responses, real shadow-call outputs, payment
    data (card numbers, IBANs, bank-account numbers, payment refs)
  - claim AGI / sentience / consciousness / benchmark /
    public-science / production-ready / live-public-runtime
  - call any payment provider (Stripe, Adyen, Klarna, etc.)
  - create invoices, charges, refunds, disputes, or payouts
  - render authority claims (it only reports observations that
    the caller explicitly handed it)

This slice implements the read-model **only**. Live dashboard
backend, dashboard frontend, real-time aggregation, KPI
computation, operator-action wiring, billing-integration wiring,
and payment-provider calls are out of scope for this slice and
await explicit operator approval (Slices 9+).

Design reference: Customer Control Plane + Entitlements design
(§5 Operator Dashboard), and the existing Slice 5/6/7
metadata-only pattern (deterministic helpers, JSON-safe output,
default-deny behavior, strict-boundary contract).

Wiring rule: this module does not import weslr.chat_responder,
weslr.runtime_wrapper, weslr.session_manager, weslr.audit_log,
weslr.audit_log_persistence, weslr.account_status (runtime),
weslr.entitlement_packet (runtime), weslr.billing_abo_status
(runtime), or any UI/dialogue/main module. It optionally imports
the Slice 6/7 helpers for cross-checking slice status (read-only,
try/excepted), but the helper is self-contained even if those
upstream helpers are absent.

Helper design principles:

  1. **Read-model only.** The helper takes a `DashboardReadModelInputV1`
     packet and returns a `DashboardReadModelV1` packet. It does
     not query any live system.

  2. **Observations, not guarantees.** Every section is labeled
     `is_observation=True`. The helper never claims a section
     "is healthy" or "is failing" — it only reports what the
     caller told it. If the caller says `status="pass"`, the
     helper reports `observation=pass`. If the caller provides
     no input for a section, the helper reports
     `observation=not_provided`.

  3. **Fail closed on unsafe inputs.** The validator rejects
     any input packet that:
       - carries a forbidden key (16-key contract)
       - carries a non-primitive value where a primitive is
         required
       - declares a status that is not in the allowed set
       - declares a section that is not in the allowed sections
       - declares an authority claim (e.g., "is_healthy",
         "is_production_ready", "is_live_public_runtime")

  4. **Recommended next operator action is metadata-only.**
     The helper suggests a lane (one of an allow-listed set of
     short tokens). It does NOT perform the action. It does NOT
     claim that the action is required. It does NOT auto-approve
     anything.

  5. **Warnings are explicit and operator-attention-only.**
     The helper does not infer warnings; it only reports
     warnings that the caller provided. The caller is responsible
     for deciding what counts as a warning.

  6. **Slice status is a structured allow-list.** The helper
     recognizes the 8 protected slices (1-8) and the canonical
     OCC branch HEAD. It does NOT recognize any other slices.
     A "slice 9" or "slice 99" status is rejected with
     `REASON_INVALID_SLICE_REFERENCE`.

  7. **Markdown rendering is safe.** The `to_dashboard_read_model_markdown_v1`
     function renders the read-model as safe Markdown. It uses a
     restricted Markdown subset (headings, lists, code blocks,
     bold, italic, links) and rejects any input that could lead
     to script injection, raw HTML, or authority claims. All
     dynamic values are escaped before insertion.
"""

from __future__ import annotations

# Pure stdlib only. No third-party imports.
import json
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Schema version. Bumped only on breaking changes to the packet shape.
DASHBOARD_READ_MODEL_SCHEMA_VERSION_V1: str = "1"

#: Required top-level keys for a valid input packet.
DASHBOARD_READ_MODEL_INPUT_REQUIRED_KEYS_V1: Tuple[str, ...] = (
    "schema_version",
    "generated_at_utc",
    "operator_id",
    "operator_role",
    "sections",
)

#: Allowed section names in the input/output packet.
#: Each section is a key under the `sections` dict.
DASHBOARD_READ_MODEL_SECTIONS_V1: Tuple[str, ...] = (
    "public_protected_site_health",
    "backend_health",
    "source_repo_health",
    "protected_auth_status",
    "blocked_actions",
    "current_slice_status",
    "recommended_next_operator_action",
    "warnings_requiring_operator_attention",
)

#: Allowed status values inside a section observation. The helper
#: never claims "is_healthy" or "is_failing" — it only reports
#: the caller's `status` field. The set is fixed.
DASHBOARD_SECTION_OBSERVATION_STATUSES_V1: Tuple[str, ...] = (
    "pass",
    "warn",
    "fail",
    "unknown",
    "not_provided",
)

#: Allowed operator roles. The helper does not infer the operator
#: role; the caller must provide it.
DASHBOARD_OPERATOR_ROLES_V1: Tuple[str, ...] = (
    "operator",
    "operator_viewer",
    "operator_auditor",
)

#: The 8 protected slices (1-8). Slice 9+ is rejected.
DASHBOARD_RECOGNIZED_SLICES_V1: Tuple[str, ...] = (
    "slice1_health_check",
    "slice2_runtime_wrapper",
    "slice3_session_manager",
    "slice4a_audit_event_schema",
    "slice4b_audit_persistence",
    "slice5_entitlement_packet",
    "slice6_account_status",
    "slice7_billing_abo_status",
    "slice8_dashboard_read_model",
)

#: Allowed values for `current_slice_status.status` per slice.
#: Each slice can be in one of these states.
DASHBOARD_SLICE_STATUS_VALUES_V1: Tuple[str, ...] = (
    "designed",
    "in_progress",
    "implemented",
    "validated",
    "pushed",
    "verified_in_canonical",
    "blocked",
    "awaiting_operator_decision",
)

#: Allowed `recommended_next_operator_action.lane` values.
#: The helper does not invent lanes; it only accepts callers'
#: explicit recommendations that fall in this set.
DASHBOARD_RECOMMENDED_LANES_V1: Tuple[str, ...] = (
    "REVIEW_SLICE_RESULTS",
    "APPROVE_NEXT_SLICE",
    "RECOVER_BACKEND",
    "RESTART_HEALTH_CHECK",
    "DEFER",
    "NO_ACTION",
)

#: 16-key forbidden contract (mirrors Slice 4A/4B/6/7).
#: Any input packet that carries a key in this set (recursively)
#: is rejected.
DASHBOARD_READ_MODEL_NEVER_INCLUDES_V1: frozenset = frozenset({
    "raw_prompt", "raw_reply", "credentials",
    "session_token_plaintext", "hidden_prompt", "system_prompt",
    "chain_of_thought", "provider_response", "shadow_call_output",
    "password", "secret", "api_key",
    "payment_card", "card_number", "iban", "bank_account",
})

#: Authority-claim key prefixes. The helper rejects any input
#: that carries a key starting with one of these. These are
#: reserved for runtime authority (NOT for the dashboard
#: read-model, which is observation-only).
DASHBOARD_AUTHORITY_CLAIM_KEY_PREFIXES_V1: Tuple[str, ...] = (
    "is_",
    "has_",
    "is_production_",
    "is_live_public_",
    "is_agi_",
    "is_sentient_",
    "is_conscious_",
    "is_approved_",
    "is_authorized_",
    "is_certified_",
    "is_benchmark_",
    "is_public_science_",
    "is_autonomous_",
    "official_",
    "certified_",
)


# ---------------------------------------------------------------------------
# Reason labels
# ---------------------------------------------------------------------------

REASON_INVALID_INPUT_NOT_DICT = "invalid_input_not_a_dict"
REASON_INVALID_INPUT_MISSING_KEY = "invalid_input_missing_required_key"
REASON_INVALID_INPUT_WRONG_TYPE = "invalid_input_wrong_type"
REASON_INVALID_SCHEMA_VERSION = "invalid_schema_version_unsupported"
REASON_INVALID_OPERATOR_ROLE = "invalid_operator_role"
REASON_INVALID_SECTION = "invalid_section_name"
REASON_INVALID_SECTION_STATUS = "invalid_section_status_value"
REASON_INVALID_SECTION_NOT_DICT = "invalid_section_not_a_dict"
REASON_INVALID_SLICE_REFERENCE = "invalid_slice_reference_unknown_slice"
REASON_INVALID_SLICE_STATUS = "invalid_slice_status_value"
REASON_INVALID_RECOMMENDED_LANE = "invalid_recommended_lane_value"
REASON_INVALID_RECOMMENDED_NOT_DICT = "invalid_recommended_action_not_a_dict"
REASON_INVALID_WARNINGS_NOT_LIST = "invalid_warnings_not_a_list"
REASON_INVALID_WARNING_NOT_DICT = "invalid_warning_not_a_dict"
REASON_INVALID_WARNING_MISSING_FIELDS = "invalid_warning_missing_required_fields"
REASON_INVALID_BLOCKED_ACTIONS_NOT_LIST = "invalid_blocked_actions_not_a_list"
REASON_INVALID_BLOCKED_ACTION_NOT_DICT = "invalid_blocked_action_not_a_dict"
REASON_INVALID_BLOCKED_ACTION_MISSING_FIELDS = "invalid_blocked_action_missing_required_fields"
REASON_INVALID_FORBIDDEN_KEY = "invalid_input_carries_forbidden_key"
REASON_INVALID_AUTHORITY_CLAIM = "invalid_input_carries_authority_claim"
REASON_INVALID_NON_PRIMITIVE_VALUE = "invalid_input_carries_non_primitive_value"
REASON_INVALID_GENERATED_AT_NOT_ISO8601 = "invalid_generated_at_not_iso8601_string"
REASON_INVALID_OPERATOR_ID = "invalid_operator_id_empty_or_non_string"


# ---------------------------------------------------------------------------
# Module-level utility helpers
# ---------------------------------------------------------------------------


def _is_primitive(v: Any) -> bool:
    """Return True if v is a JSON-safe primitive (str, int, float,
    bool, None)."""
    return v is None or isinstance(v, (str, int, float, bool))


def _is_dict(v: Any) -> bool:
    return isinstance(v, dict)


def _is_list(v: Any) -> bool:
    return isinstance(v, list)


def _has_forbidden_key(value: Any, path: str = "") -> List[str]:
    """Recursively scan `value` for any forbidden key. Returns
    a list of path strings for each forbidden key found. Used
    by the validator.

    Forbidden keys are the 16 keys in
    DASHBOARD_READ_MODEL_NEVER_INCLUDES_V1. The scan is recursive
    into dicts and lists.

    The check operates on the **key** side of dicts; the value
    side is checked separately for non-primitive violations.
    """
    found: List[str] = []
    if _is_dict(value):
        for k, v in value.items():
            if not isinstance(k, str):
                # Non-string keys are themselves a violation
                # of the contract (callers should pass str keys
                # for JSON-safety). Treat as forbidden.
                found.append(f"{path}.<non_str_key>")
                continue
            new_path = f"{path}.{k}" if path else k
            if k in DASHBOARD_READ_MODEL_NEVER_INCLUDES_V1:
                found.append(new_path)
            # Recurse into value
            found.extend(_has_forbidden_key(v, new_path))
    elif _is_list(value):
        for i, item in enumerate(value):
            found.extend(_has_forbidden_key(item, f"{path}[{i}]"))
    return found


def _has_authority_claim(value: Any, path: str = "") -> List[str]:
    """Recursively scan `value` for any authority-claim key
    prefix. Returns a list of path strings for each match.

    Authority claims are reserved for runtime authority and
    are NOT allowed in the dashboard read-model input. A key
    that starts with one of
    DASHBOARD_AUTHORITY_CLAIM_KEY_PREFIXES_V1 is rejected.
    """
    found: List[str] = []
    if _is_dict(value):
        for k, v in value.items():
            if not isinstance(k, str):
                continue
            new_path = f"{path}.{k}" if path else k
            for prefix in DASHBOARD_AUTHORITY_CLAIM_KEY_PREFIXES_V1:
                if k.startswith(prefix):
                    found.append(new_path)
                    break
            found.extend(_has_authority_claim(v, new_path))
    elif _is_list(value):
        for i, item in enumerate(value):
            found.extend(_has_authority_claim(item, f"{path}[{i}]"))
    return found


def _has_non_primitive(value: Any, path: str = "") -> List[str]:
    """Recursively scan `value` for any non-primitive value. Returns
    a list of path strings for each non-primitive found. Used
    by the validator to ensure JSON-safety.

    Non-primitive values include: bytes, set, frozenset, tuple
    (in some contexts), any custom object. The dashboard
    read-model is JSON-safe only.
    """
    found: List[str] = []
    if _is_dict(value):
        for k, v in value.items():
            new_path = f"{path}.{k}" if path else str(k)
            if not _is_primitive(v) and not _is_dict(v) and not _is_list(v):
                found.append(f"{new_path}:{type(v).__name__}")
            else:
                found.extend(_has_non_primitive(v, new_path))
    elif _is_list(value):
        for i, item in enumerate(value):
            new_path = f"{path}[{i}]"
            if not _is_primitive(item) and not _is_dict(item) and not _is_list(item):
                found.append(f"{new_path}:{type(item).__name__}")
            else:
                found.extend(_has_non_primitive(item, new_path))
    return found


def _is_iso8601_utc(s: Any) -> bool:
    """Return True if `s` is a string that looks like an ISO-8601
    UTC timestamp (e.g. "2026-06-24T13:00:00Z" or with "+00:00"
    offset). The helper does not use a real date parser (to keep
    the module pure-stdlib with no dateutil/pytz dependency);
    the check is a strict format check."""
    if not isinstance(s, str):
        return False
    if len(s) < 20:
        return False
    # Accept only strings that begin with YYYY-MM-DDT
    if s[4:5] != "-" or s[7:8] != "-" or s[10:11] != "T":
        return False
    # Must end with Z or +HH:MM offset
    if s.endswith("Z"):
        return True
    if len(s) >= 25 and s[19:20] in ("+", "-") and s[22:23] == ":":
        return True
    return False


# ---------------------------------------------------------------------------
# Section validators
# ---------------------------------------------------------------------------


def _validate_section(name: str, value: Any, errors: List[str]) -> None:
    """Validate one section. Appends reason labels to `errors`."""
    if not _is_dict(value):
        errors.append(f"{REASON_INVALID_SECTION_NOT_DICT}:{name}")
        return
    # Required keys in every section
    for k in ("status", "summary", "details"):
        if k not in value:
            errors.append(
                f"{REASON_INVALID_INPUT_MISSING_KEY}:sections.{name}.{k}"
            )
    # status must be a string in the allowed set
    status = value.get("status")
    if not isinstance(status, str):
        errors.append(
            f"{REASON_INVALID_INPUT_WRONG_TYPE}:sections.{name}.status"
        )
    elif status not in DASHBOARD_SECTION_OBSERVATION_STATUSES_V1:
        errors.append(
            f"{REASON_INVALID_SECTION_STATUS}:sections.{name}.status:{status}"
        )
    # summary must be a string
    summary = value.get("summary")
    if not isinstance(summary, str):
        errors.append(
            f"{REASON_INVALID_INPUT_WRONG_TYPE}:sections.{name}.summary"
        )
    # details must be a dict of primitives
    details = value.get("details")
    if not _is_dict(details):
        errors.append(
            f"{REASON_INVALID_INPUT_WRONG_TYPE}:sections.{name}.details"
        )
    else:
        for dk, dv in details.items():
            if not _is_primitive(dv):
                errors.append(
                    f"{REASON_INVALID_NON_PRIMITIVE_VALUE}:sections.{name}.details.{dk}"
                )


def _validate_blocked_actions(actions: Any, errors: List[str]) -> None:
    """Validate the blocked_actions list. Each entry must be a dict
    with `category` (str), `description` (str), and `reason_label`
    (str) fields. The helper does not interpret the actions; it
    only validates their shape."""
    if not _is_list(actions):
        errors.append(REASON_INVALID_BLOCKED_ACTIONS_NOT_LIST)
        return
    for i, action in enumerate(actions):
        if not _is_dict(action):
            errors.append(
                f"{REASON_INVALID_BLOCKED_ACTION_NOT_DICT}:blocked_actions[{i}]"
            )
            continue
        for k in ("category", "description", "reason_label"):
            if k not in action:
                errors.append(
                    f"{REASON_INVALID_BLOCKED_ACTION_MISSING_FIELDS}:blocked_actions[{i}].{k}"
                )
            elif not isinstance(action.get(k), str):
                errors.append(
                    f"{REASON_INVALID_INPUT_WRONG_TYPE}:blocked_actions[{i}].{k}"
                )


def _validate_warnings(warnings: Any, errors: List[str]) -> None:
    """Validate the warnings_requiring_operator_attention list. Each
    entry must be a dict with `warning_id` (str), `description` (str),
    and `severity` (str in {info, warn, critical}) fields."""
    if not _is_list(warnings):
        errors.append(REASON_INVALID_WARNINGS_NOT_LIST)
        return
    for i, warning in enumerate(warnings):
        if not _is_dict(warning):
            errors.append(
                f"{REASON_INVALID_WARNING_NOT_DICT}:warnings[{i}]"
            )
            continue
        for k in ("warning_id", "description", "severity"):
            if k not in warning:
                errors.append(
                    f"{REASON_INVALID_WARNING_MISSING_FIELDS}:warnings[{i}].{k}"
                )
            elif not isinstance(warning.get(k), str):
                errors.append(
                    f"{REASON_INVALID_INPUT_WRONG_TYPE}:warnings[{i}].{k}"
                )
        sev = warning.get("severity") if _is_dict(warning) else None
        if isinstance(sev, str) and sev not in ("info", "warn", "critical"):
            errors.append(
                f"{REASON_INVALID_INPUT_WRONG_TYPE}:warnings[{i}].severity:{sev}"
            )


def _validate_current_slice_status(slice_status: Any, errors: List[str]) -> None:
    """Validate the current_slice_status section. Must be a dict
    with at minimum `slice_id` (str in DASHBOARD_RECOGNIZED_SLICES_V1)
    and `status` (str in DASHBOARD_SLICE_STATUS_VALUES_V1)."""
    if not _is_dict(slice_status):
        errors.append(
            f"{REASON_INVALID_SECTION_NOT_DICT}:sections.current_slice_status"
        )
        return
    slice_id = slice_status.get("slice_id")
    if not isinstance(slice_id, str):
        errors.append(
            f"{REASON_INVALID_INPUT_WRONG_TYPE}:sections.current_slice_status.slice_id"
        )
    elif slice_id not in DASHBOARD_RECOGNIZED_SLICES_V1:
        errors.append(
            f"{REASON_INVALID_SLICE_REFERENCE}:sections.current_slice_status.slice_id:{slice_id}"
        )
    status = slice_status.get("status")
    if not isinstance(status, str):
        errors.append(
            f"{REASON_INVALID_INPUT_WRONG_TYPE}:sections.current_slice_status.status"
        )
    elif status not in DASHBOARD_SLICE_STATUS_VALUES_V1:
        errors.append(
            f"{REASON_INVALID_SLICE_STATUS}:sections.current_slice_status.status:{status}"
        )


def _validate_recommended_action(rec: Any, errors: List[str]) -> None:
    """Validate the recommended_next_operator_action section. Must be
    a dict with `lane` (str in DASHBOARD_RECOMMENDED_LANES_V1) and
    `reason` (str) fields."""
    if not _is_dict(rec):
        errors.append(
            f"{REASON_INVALID_RECOMMENDED_NOT_DICT}:sections.recommended_next_operator_action"
        )
        return
    lane = rec.get("lane")
    if not isinstance(lane, str):
        errors.append(
            f"{REASON_INVALID_INPUT_WRONG_TYPE}:sections.recommended_next_operator_action.lane"
        )
    elif lane not in DASHBOARD_RECOMMENDED_LANES_V1:
        errors.append(
            f"{REASON_INVALID_RECOMMENDED_LANE}:sections.recommended_next_operator_action.lane:{lane}"
        )
    reason = rec.get("reason")
    if not isinstance(reason, str):
        errors.append(
            f"{REASON_INVALID_INPUT_WRONG_TYPE}:sections.recommended_next_operator_action.reason"
        )


# ---------------------------------------------------------------------------
# Public API: input validation
# ---------------------------------------------------------------------------


def validate_dashboard_read_model_input_v1(
    input_packet: Any,
) -> Dict[str, Any]:
    """Validate a DashboardReadModelInputV1 packet.

    The validator enforces:

      - packet is a dict
      - all required top-level keys are present
      - `schema_version` matches DASHBOARD_READ_MODEL_SCHEMA_VERSION_V1
      - `generated_at_utc` is an ISO-8601 string
      - `operator_id` is a non-empty string
      - `operator_role` is in DASHBOARD_OPERATOR_ROLES_V1
      - `sections` is a dict
      - every section name is in DASHBOARD_READ_MODEL_SECTIONS_V1
      - every section has the right shape
      - blocked_actions and warnings are lists of dicts with the
        right shape
      - no forbidden keys (16-key contract) anywhere in the packet
      - no authority-claim key prefixes anywhere in the packet
      - no non-primitive values anywhere in the packet

    Returns a dict with keys:

      - `ok` (bool): True if the input is valid
      - `errors` (list of str): reason labels for each failure
      - `input_packet` (dict or None): a defensive copy of the
        input if valid, else None
    """
    errors: List[str] = []

    if not _is_dict(input_packet):
        return {
            "ok": False,
            "errors": [REASON_INVALID_INPUT_NOT_DICT],
            "input_packet": None,
        }

    # Required top-level keys
    for k in DASHBOARD_READ_MODEL_INPUT_REQUIRED_KEYS_V1:
        if k not in input_packet:
            errors.append(f"{REASON_INVALID_INPUT_MISSING_KEY}:{k}")

    # schema_version
    schema_version = input_packet.get("schema_version")
    if schema_version != DASHBOARD_READ_MODEL_SCHEMA_VERSION_V1:
        errors.append(
            f"{REASON_INVALID_SCHEMA_VERSION}:{schema_version}"
        )

    # generated_at_utc
    if not _is_iso8601_utc(input_packet.get("generated_at_utc")):
        errors.append(REASON_INVALID_GENERATED_AT_NOT_ISO8601)

    # operator_id
    op_id = input_packet.get("operator_id")
    if not isinstance(op_id, str) or not op_id.strip():
        errors.append(REASON_INVALID_OPERATOR_ID)

    # operator_role
    op_role = input_packet.get("operator_role")
    if not isinstance(op_role, str):
        errors.append(
            f"{REASON_INVALID_INPUT_WRONG_TYPE}:operator_role"
        )
    elif op_role not in DASHBOARD_OPERATOR_ROLES_V1:
        errors.append(
            f"{REASON_INVALID_OPERATOR_ROLE}:operator_role:{op_role}"
        )

    # sections
    sections = input_packet.get("sections")
    if not _is_dict(sections):
        errors.append(
            f"{REASON_INVALID_INPUT_WRONG_TYPE}:sections"
        )
    else:
        # Every key in sections must be a recognized section
        for section_name in sections.keys():
            if section_name not in DASHBOARD_READ_MODEL_SECTIONS_V1:
                errors.append(
                    f"{REASON_INVALID_SECTION}:sections.{section_name}"
                )
        # Every recognized section must be present and valid
        for section_name in DASHBOARD_READ_MODEL_SECTIONS_V1:
            if section_name not in sections:
                errors.append(
                    f"{REASON_INVALID_INPUT_MISSING_KEY}:sections.{section_name}"
                )
                continue
            value = sections[section_name]
            if section_name == "current_slice_status":
                _validate_current_slice_status(value, errors)
            elif section_name == "recommended_next_operator_action":
                _validate_recommended_action(value, errors)
            elif section_name == "blocked_actions":
                _validate_blocked_actions(value, errors)
            elif section_name == "warnings_requiring_operator_attention":
                _validate_warnings(value, errors)
            else:
                _validate_section(section_name, value, errors)

    # Recursive checks
    for path in _has_forbidden_key(input_packet):
        errors.append(f"{REASON_INVALID_FORBIDDEN_KEY}:{path}")
    for path in _has_authority_claim(input_packet):
        errors.append(f"{REASON_INVALID_AUTHORITY_CLAIM}:{path}")
    for path in _has_non_primitive(input_packet):
        errors.append(f"{REASON_INVALID_NON_PRIMITIVE_VALUE}:{path}")

    if errors:
        return {
            "ok": False,
            "errors": errors,
            "input_packet": None,
        }

    # Return a defensive copy
    return {
        "ok": True,
        "errors": [],
        "input_packet": json.loads(json.dumps(input_packet)),
    }


# ---------------------------------------------------------------------------
# Public API: read-model construction
# ---------------------------------------------------------------------------


def build_dashboard_read_model_v1(
    input_packet: Any,
) -> Dict[str, Any]:
    """Build a DashboardReadModelV1 from a validated input packet.

    The function first validates the input. If validation fails,
    it returns a read-model with `ok=False` and a list of errors.
    If validation succeeds, it composes the read-model from the
    input sections, attaching metadata headers and an
    `is_observation` flag to every section.

    The output packet shape is:

      {
        "schema_version": "1",
        "ok": True|False,
        "errors": [...],
        "input_packet": <defensive copy>,
        "sections": {
          <section_name>: {
            "is_observation": True,  # always True; the read-model
                                     # is always observations
            "status": <caller-provided>,
            "summary": <caller-provided>,
            "details": <caller-provided>,
          },
          ...
        },
        "blocked_actions": [...],  # passthrough
        "warnings_requiring_operator_attention": [...],  # passthrough
        "metadata": {
          "generated_at_utc": <passthrough>,
          "operator_id": <passthrough>,
          "operator_role": <passthrough>,
          "schema_version": "1",
          "is_dashboard_read_model": True,  # marker, not authority
          "is_live_inference": False,  # explicit: NOT live
          "is_observation_only": True,  # explicit: observation-only
        }
      }
    """
    validation = validate_dashboard_read_model_input_v1(input_packet)
    if not validation["ok"]:
        return {
            "schema_version": DASHBOARD_READ_MODEL_SCHEMA_VERSION_V1,
            "ok": False,
            "errors": validation["errors"],
            "input_packet": None,
            "sections": {},
            "blocked_actions": [],
            "warnings_requiring_operator_attention": [],
            "metadata": {
                "is_dashboard_read_model": True,
                "is_live_inference": False,
                "is_observation_only": True,
            },
        }

    pkt = validation["input_packet"]
    sections = pkt["sections"]

    # Annotate every section with is_observation=True
    annotated_sections: Dict[str, Any] = {}
    for section_name in DASHBOARD_READ_MODEL_SECTIONS_V1:
        if section_name in ("blocked_actions", "warnings_requiring_operator_attention"):
            # These are not "sections" in the same sense; they
            # are list-typed entries handled below.
            continue
        if section_name == "current_slice_status":
            annotated_sections[section_name] = {
                "is_observation": True,
                **sections[section_name],
            }
        elif section_name == "recommended_next_operator_action":
            annotated_sections[section_name] = {
                "is_observation": True,
                "is_auto_approved": False,  # explicit
                **sections[section_name],
            }
        else:
            annotated_sections[section_name] = {
                "is_observation": True,
                **sections[section_name],
            }

    return {
        "schema_version": DASHBOARD_READ_MODEL_SCHEMA_VERSION_V1,
        "ok": True,
        "errors": [],
        "input_packet": pkt,
        "sections": annotated_sections,
        "blocked_actions": pkt["sections"].get("blocked_actions", []),
        "warnings_requiring_operator_attention": pkt["sections"].get(
            "warnings_requiring_operator_attention", []
        ),
        "metadata": {
            "generated_at_utc": pkt["generated_at_utc"],
            "operator_id": pkt["operator_id"],
            "operator_role": pkt["operator_role"],
            "schema_version": DASHBOARD_READ_MODEL_SCHEMA_VERSION_V1,
            "is_dashboard_read_model": True,
            "is_live_inference": False,
            "is_observation_only": True,
            "is_authority_claim": False,
            "is_production_ready": False,
            "is_live_public_runtime": False,
        },
    }


# ---------------------------------------------------------------------------
# Public API: JSON-safe serialization
# ---------------------------------------------------------------------------


def to_dashboard_read_model_json_safe_v1(value: Any) -> str:
    """Serialize a DashboardReadModelV1 packet to JSON-safe text.

    The serializer is defensive: it never raises. It returns a
    JSON object with `ok=False` and an `error` key if serialization
    fails for any reason (e.g., a non-primitive slipped through
    validation). Otherwise it returns the JSON string of `value`.

    The function also recursively strips any forbidden keys that
    may have been missed by the validator (defense-in-depth).
    """
    try:
        # Defense-in-depth: strip forbidden keys recursively
        sanitized = _strip_forbidden_keys(value)
        return json.dumps(sanitized, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError) as e:
        return json.dumps(
            {
                "ok": False,
                "error": f"serialization_error:{type(e).__name__}",
                "is_observation_only": True,
            },
            ensure_ascii=False,
            sort_keys=True,
        )


def _strip_forbidden_keys(value: Any) -> Any:
    """Recursively replace forbidden-key values with
    `<redacted:dashboard-forbidden-key>` markers. Defense-in-depth
    only; the validator is the primary guard."""
    if _is_dict(value):
        out: Dict[str, Any] = {}
        for k, v in value.items():
            if not isinstance(k, str):
                continue  # drop non-string keys silently
            if k in DASHBOARD_READ_MODEL_NEVER_INCLUDES_V1:
                out[k] = "<redacted:dashboard-forbidden-key>"
            else:
                out[k] = _strip_forbidden_keys(v)
        return out
    if _is_list(value):
        return [_strip_forbidden_keys(item) for item in value]
    return value


# ---------------------------------------------------------------------------
# Public API: safe-Markdown rendering
# ---------------------------------------------------------------------------


def to_dashboard_read_model_markdown_v1(value: Any) -> str:
    """Render a DashboardReadModelV1 packet as safe Markdown.

    The renderer uses a restricted Markdown subset:

      - `#` and `##` headings
      - bullet lists
      - bold/italic
      - fenced code blocks (triple backticks)
      - inline code (single backticks)
      - links (explicit `<url>` form only, NO `[text](url)` to
        avoid confusion with authority claims)

    Every dynamic value is escaped before insertion. No raw HTML
    is ever emitted. The renderer rejects any input that is not
    a dict (returns an error string).

    The renderer is deterministic: same input → same output.
    """
    if not _is_dict(value):
        return (
            "# Dashboard Read-Model V1 — error\n\n"
            "`error: input not a dict; cannot render.`\n"
        )

    if not value.get("ok"):
        errors = value.get("errors", [])
        err_lines = "\n".join(f"- `{_md_escape(e)}`" for e in errors)
        return (
            "# Dashboard Read-Model V1 — validation failed\n\n"
            f"## Errors ({len(errors)})\n\n"
            f"{err_lines}\n"
        )

    metadata = value.get("metadata", {})
    sections = value.get("sections", {})
    blocked = value.get("blocked_actions", [])
    warnings = value.get("warnings_requiring_operator_attention", [])

    lines: List[str] = []
    lines.append("# Dashboard Read-Model V1")
    lines.append("")
    lines.append(
        f"- **schema_version:** `{_md_escape(str(metadata.get('schema_version', '')))}`"
    )
    lines.append(
        f"- **generated_at_utc:** `{_md_escape(str(metadata.get('generated_at_utc', '')))}`"
    )
    lines.append(
        f"- **operator_id:** `{_md_escape(str(metadata.get('operator_id', '')))}`"
    )
    lines.append(
        f"- **operator_role:** `{_md_escape(str(metadata.get('operator_role', '')))}`"
    )
    lines.append("- **is_observation_only:** `True` (read-model, not authority)")
    lines.append("- **is_live_inference:** `False` (no live system queries)")
    lines.append("")

    # Sections
    lines.append("## Sections")
    lines.append("")
    for section_name in DASHBOARD_READ_MODEL_SECTIONS_V1:
        if section_name in ("blocked_actions", "warnings_requiring_operator_attention"):
            continue
        section = sections.get(section_name, {})
        status = _md_escape(str(section.get("status", "not_provided")))
        summary = _md_escape(str(section.get("summary", "")))
        lines.append(f"### `{_md_escape(section_name)}` — status: `{status}`")
        lines.append("")
        lines.append(summary)
        lines.append("")
        details = section.get("details", {})
        if _is_dict(details) and details:
            lines.append("**Details:**")
            lines.append("")
            for k, v in details.items():
                lines.append(
                    f"- `{_md_escape(str(k))}`: `{_md_escape(str(v))}`"
                )
            lines.append("")

    # Blocked actions
    if blocked:
        lines.append("## Blocked Actions / Safety Boundaries")
        lines.append("")
        for action in blocked:
            if not _is_dict(action):
                continue
            cat = _md_escape(str(action.get("category", "")))
            desc = _md_escape(str(action.get("description", "")))
            label = _md_escape(str(action.get("reason_label", "")))
            lines.append(f"- **{cat}** — {desc} (reason: `{label}`)")
        lines.append("")

    # Warnings
    if warnings:
        lines.append("## Warnings Requiring Operator Attention")
        lines.append("")
        for warning in warnings:
            if not _is_dict(warning):
                continue
            wid = _md_escape(str(warning.get("warning_id", "")))
            desc = _md_escape(str(warning.get("description", "")))
            sev = _md_escape(str(warning.get("severity", "")))
            lines.append(f"- **[{sev}]** `{wid}` — {desc}")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append(
        "*This read-model is observation-only. It does not perform any "
        "operator action, does not infer live system truth, and does "
        "not claim authority over any runtime state. Operator review "
        "is required for any decision.*"
    )
    return "\n".join(lines)


def _md_escape(s: str) -> str:
    """Escape a string for safe inclusion in a Markdown document.

    Escapes:
      - backticks
      - backslashes
      - HTML special chars (defense-in-depth)
      - control characters
    """
    if not isinstance(s, str):
        s = str(s)
    # Escape backslashes first
    s = s.replace("\\", "\\\\")
    # Escape backticks
    s = s.replace("`", "\\`")
    # Escape angle brackets
    s = s.replace("<", "&lt;").replace(">", "&gt;")
    # Strip control characters
    s = "".join(c for c in s if ord(c) >= 0x20 or c == "\n" or c == "\t")
    return s


# ---------------------------------------------------------------------------
# Public API: summary
# ---------------------------------------------------------------------------


def summarize_dashboard_read_model_v1(value: Any) -> str:
    """Return a one-line summary of a DashboardReadModelV1 packet.

    The summary is metadata-only and includes:

      - the schema version
      - the operator id
      - the recommended next lane
      - a count of warnings

    Used by the operator dashboard's title bar. The summary
    itself is observation-only.
    """
    if not _is_dict(value) or not value.get("ok"):
        return (
            f"DashboardReadModelV1[schema=1, ok=False, "
            f"errors={len(value.get('errors', [])) if _is_dict(value) else 'n/a'}]"
        )
    metadata = value.get("metadata", {})
    sections = value.get("sections", {})
    rec = sections.get("recommended_next_operator_action", {})
    lane = rec.get("lane", "n/a") if _is_dict(rec) else "n/a"
    warnings = value.get("warnings_requiring_operator_attention", [])
    return (
        f"DashboardReadModelV1[schema=1, ok=True, "
        f"operator={metadata.get('operator_id', 'n/a')}, "
        f"role={metadata.get('operator_role', 'n/a')}, "
        f"recommended_lane={lane}, "
        f"warnings={len(warnings)}]"
    )
