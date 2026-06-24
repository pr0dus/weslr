"""
WESLR chat.weslr.de Slice 7 — Billing/Abo Metadata Helper V1

Standalone, metadata-only billing/abo state/transition helper.

This module manages the 11 billing/abo statuses (mirrored from
Slice 5's entitlement-packet subscription_status enum) and their
state-transition graph. It does NOT:
  - import or call weslr.chat_responder, main, dialogue, chat_ui,
    backend server files, provider/model code, payment-provider
    code, or any protected runtime module
  - perform subprocess, network, or filesystem write operations
  - write to "/home/pr0/weslr_state/" (no real persistence)
  - wire itself to the entitlement helper, account-status helper,
    runtime wrapper, session manager, audit log, audit persistence,
    or ChatResponder
  - retain raw prompt text, raw reply text, credentials, PII,
    hidden prompts, system prompts, chain-of-thought traces,
    provider/LLM API responses, real shadow-call outputs, payment
    data (card numbers, IBANs, bank-account numbers, payment refs)
  - claim AGI / sentience / consciousness / benchmark /
    public-science / production-ready / live-public-runtime
  - call any payment provider (Stripe, Adyen, Klarna, etc.)
  - create invoices, charges, refunds, disputes, or payouts
  - store, process, or tokenize payment instruments

This slice implements the billing/abo status state/transition
logic only. Real persistence, operator-action wiring, dashboard
read-model wiring, billing-integration wiring, and payment-provider
calls are out of scope for this slice and await explicit operator
approval (Slices 8+).

Design reference: Customer Control Plane + Entitlements design
(§3.1 Subscription/Abo Statuses), plus the operator's transition
rules and Slice 6's destructive-target operator_approval pattern
(replicated here for parity: destructive billing/abo transitions
also require operator approval).

Wiring rule: this module does not import weslr.chat_responder,
weslr.runtime_wrapper, weslr.session_manager, weslr.audit_log,
weslr.audit_log_persistence, weslr.account_status (runtime),
weslr.entitlement_packet (runtime), or any UI/dialogue/main
module. It optionally imports canonical constant frozensets from
weslr.entitlement_packet (for parity on subscription-status
names) and weslr.account_status (for the 16-key forbidden-keys
contract). Both imports are try/excepted so this module is
self-contained even if the upstream helpers are absent.
"""

from __future__ import annotations

# Pure stdlib only.
import json
import uuid
from typing import Any, Dict, List, Optional, Set, Tuple


# Optional import: pull the canonical 11-subscription-status enum
# from the entitlement packet helper (Slice 5) to ensure this
# module's status set is the same. If unavailable, fall back to
# the local enum defined below.
try:
    from weslr.entitlement_packet import _VALID_SUBSCRIPTION_STATUSES as _EP_SUBSCRIPTION_STATUSES
    _EP_AVAILABLE = True
except ImportError:
    _EP_SUBSCRIPTION_STATUSES = frozenset()
    _EP_AVAILABLE = False


# Optional import: pull the canonical 16-key forbidden-keys contract
# from the account-status helper (Slice 6) so this module enforces
# the same forbidden-keys set. If unavailable, fall back to the
# local set defined below.
try:
    from weslr.account_status import ACCOUNT_STATUS_NEVER_INCLUDES as _AS_FORBIDDEN_KEYS
    _AS_AVAILABLE = True
except ImportError:
    _AS_FORBIDDEN_KEYS = frozenset()
    _AS_AVAILABLE = False


# ----------------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------------

BILLING_ABO_HELPER_VERSION = "weslr-billing-abo-status-helper-v1"

# 11 valid billing/abo statuses (per Customer Control Plane +
# Entitlements design §3.1, mirrored from Slice 5's
# _VALID_SUBSCRIPTION_STATUSES).
VALID_BILLING_ABO_STATUSES_V1: frozenset = frozenset({
    "no_subscription",
    "free_pilot",
    "trialing",
    "active",
    "past_due",
    "unpaid",
    "canceled",
    "refunded",
    "disputed",
    "grace_period",
    "disabled_for_nonpayment",
})

# Terminal-like statuses (the operator's strict spec
# uses "terminal-like" for these). All three have
# explicit allow-lists; transitions out of them are
# permitted but only to the listed next states.
# Per operator's spec:
#   - "canceled" may move to "trialing", "active", or
#     "disabled_for_nonpayment"
#   - "refunded" may move to "canceled" or
#     "disabled_for_nonpayment"
#   - "disabled_for_nonpayment" may move to "active",
#     "trialing", or "canceled"
TERMINAL_LIKE_BILLING_ABO_STATUSES_V1: frozenset = frozenset({
    "canceled",
    "refunded",
    "disabled_for_nonpayment",
})

# Destructive-target statuses (require explicit operator
# approval via transition_request.operator_approved == True).
# A destructive target is a status that locks out, ends, or
# otherwise materially affects the user's billing relationship
# beyond a routine status change. Per operator's spec:
#   {unpaid, canceled, refunded, disputed, disabled_for_nonpayment}
# Mirrors Slice 6's pattern (account status also has a
# destructive-target operator_approval gate).
DESTRUCTIVE_BILLING_ABO_TARGETS_V1: frozenset = frozenset({
    "unpaid",
    "canceled",
    "refunded",
    "disputed",
    "disabled_for_nonpayment",
})

# Transition graph. Key: current status; Value: set of allowed
# next statuses. Per operator's transition rules (Slice 7 spec):
#   - default-deny unknown transitions
#   - terminal-like (allow-listed outgoing only):
#     canceled -> {trialing, active, disabled_for_nonpayment}
#     refunded -> {canceled, disabled_for_nonpayment}
#     disabled_for_nonpayment -> {active, trialing, canceled}
#   - normal examples:
#     no_subscription -> {free_pilot, trialing, active,
#                          disabled_for_nonpayment}
#     free_pilot -> {trialing, active, grace_period, canceled,
#                     disabled_for_nonpayment}
#     trialing -> {active, past_due, canceled, grace_period}
#     active -> {past_due, unpaid, canceled, refunded, disputed}
#     past_due -> {active, unpaid, grace_period, canceled,
#                   disabled_for_nonpayment}
#     unpaid -> {active, grace_period, canceled,
#                 disabled_for_nonpayment}
#     grace_period -> {active, unpaid, canceled,
#                       disabled_for_nonpayment}
#     disputed -> {active, refunded, canceled,
#                   disabled_for_nonpayment}
#   - destructive targets (unpaid, canceled, refunded,
#     disputed, disabled_for_nonpayment) require
#     operator_approved=True
#   - chat-access-allowing transitions into active/trialing/
#     free_pilot/grace_period do NOT require operator
#     approval (they are normal lifecycle transitions)
ALLOWED_BILLING_ABO_TRANSITIONS_V1: Dict[str, frozenset] = {
    "no_subscription": frozenset({
        "free_pilot", "trialing", "active", "disabled_for_nonpayment",
    }),
    "free_pilot": frozenset({
        "trialing", "active", "grace_period", "canceled",
        "disabled_for_nonpayment",
    }),
    "trialing": frozenset({
        "active", "past_due", "canceled", "grace_period",
    }),
    "active": frozenset({
        "past_due", "unpaid", "canceled", "refunded", "disputed",
    }),
    "past_due": frozenset({
        "active", "unpaid", "grace_period", "canceled",
        "disabled_for_nonpayment",
    }),
    "unpaid": frozenset({
        "active", "grace_period", "canceled",
        "disabled_for_nonpayment",
    }),
    "grace_period": frozenset({
        "active", "unpaid", "canceled", "disabled_for_nonpayment",
    }),
    "canceled": frozenset({
        "trialing", "active", "disabled_for_nonpayment",
    }),
    "refunded": frozenset({
        "canceled", "disabled_for_nonpayment",
    }),
    "disputed": frozenset({
        "active", "refunded", "canceled", "disabled_for_nonpayment",
    }),
    "disabled_for_nonpayment": frozenset({
        "active", "trialing", "canceled",
    }),
}

# Reason labels (machine-readable; safe to log).
REASON_OK = "ok"
REASON_INVALID_NOT_DICT = "invalid_record_not_dict"
REASON_INVALID_REQUEST_NOT_DICT = "invalid_transition_request_not_dict"
REASON_INVALID_BAD_STATUS = "invalid_billing_abo_status"
REASON_INVALID_BAD_TRANSITION = "invalid_billing_abo_transition"
REASON_INVALID_BAD_TIMESTAMP = "invalid_billing_abo_timestamp"
REASON_INVALID_BAD_VERSION = "invalid_billing_abo_version_mismatch"
REASON_INVALID_MISSING_FIELDS = "invalid_billing_abo_missing_required_fields"
REASON_INVALID_EMPTY_ACCOUNT_ID = "invalid_empty_account_id"
REASON_INVALID_SAME_STATUS = "invalid_transition_same_status"
REASON_INVALID_TERMINAL_TRANSITION = "invalid_transition_from_terminal_like_status"
REASON_INVALID_FORBIDDEN_KEY = "invalid_record_carries_forbidden_key"
REASON_INVALID_ACCOUNT_ID_MISMATCH = "invalid_record_and_request_account_id_mismatch"
REASON_INVALID_PROVIDER_REF_PAYLOAD = "invalid_provider_ref_metadata_raw_payload_rejected"

# Forbidden-keys contract. Mirrored from Slice 4A/4B and Slice 6.
# No raw prompts/replies/credentials/payment data in
# billing/abo records. This helper is metadata-only.
BILLING_ABO_STATUS_NEVER_INCLUDES: frozenset = frozenset({
    "raw_prompt", "raw_reply", "credentials",
    "session_token_plaintext", "hidden_prompt", "system_prompt",
    "chain_of_thought", "provider_response", "shadow_call_output",
    "password", "secret", "api_key",
    "payment_card", "card_number", "iban", "bank_account",
})

# Chat-access-allowing statuses (per the operator's strict spec
# for Slice 7). At the BILLING/ABO level (this slice's pre-check),
# only statuses that are clearly "currently subscribed or in
# good standing" return allows_chat_access=True. The billing/abo
# level pre-check is intentionally more conservative than the
# account-status-level pre-check (Slice 6); the runtime wrapper
# combines BOTH checks (account-status chat-enabled AND
# billing-abo allows-chat-access) before granting chat access.
# Per the operator's Slice 7 spec:
#   - allows_chat_access for: free_pilot, trialing, active, grace_period
#   - does NOT allow chat access for: no_subscription, past_due,
#     unpaid, canceled, refunded, disputed, disabled_for_nonpayment
# Rationale: past_due and unpaid are payment-failing statuses;
# the user may still have an active subscription in our metadata
# but the billing relationship is impaired, so chat access must
# be gated at the runtime-wrapper layer.
BILLING_ABO_CHAT_ACCESS_ALLOWED_V1: frozenset = frozenset({
    "free_pilot", "trialing", "active", "grace_period",
})


# ----------------------------------------------------------------------------
# Record construction
# ----------------------------------------------------------------------------

def build_billing_abo_status_record_v1(
    *,
    account_id: str,
    billing_abo_status: str,
    previous_billing_abo_status: str = "",
    billing_abo_record_id: Optional[str] = None,
    billing_abo_version: Optional[str] = None,
    billing_abo_updated_at: Optional[str] = None,
    billing_abo_updated_by: Optional[str] = "",
    billing_abo_reason_label: Optional[str] = "",
    billing_abo_transition_ref: Optional[str] = "",
    billing_provider_ref_metadata: Optional[Dict[str, Any]] = None,
    entitlement_recompute_required: bool = True,
    audit_log_ref: Optional[str] = "",
    billing_abo_reason_labels: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Build a billing/abo status record (metadata-only).

    The record is a defensive dict; it is NOT persisted by this
    helper. The caller is responsible for any persistence
    (currently forbidden by Slice 7's strict boundary).

    Field names are exactly the operator-specified names (14
    fields + raw_content_retained + billing_abo_reason_labels).
    """
    if billing_abo_record_id is None:
        billing_abo_record_id = (
            "billing-abo-record-" + uuid.uuid4().hex
        )
    if billing_abo_version is None:
        billing_abo_version = BILLING_ABO_HELPER_VERSION

    # billing_provider_ref_metadata is a metadata-only dict that
    # may carry NON-PAYMENT provider reference identifiers (e.g.,
    # an external reference ID number that points to a payment
    # provider's invoice ID). It must NOT contain raw payment
    # data. The validator scans this dict recursively for
    # forbidden keys, so any nested sensitive key will be caught.
    if billing_provider_ref_metadata is None:
        billing_provider_ref_metadata = {}

    if billing_abo_reason_labels is None:
        billing_abo_reason_labels = []

    record: Dict[str, Any] = {
        "billing_abo_record_id": str(billing_abo_record_id),
        "account_id": str(account_id),
        "billing_abo_version": str(billing_abo_version),
        "billing_abo_status": str(billing_abo_status),
        "previous_billing_abo_status": str(previous_billing_abo_status),
        "billing_abo_updated_at": (
            str(billing_abo_updated_at) if billing_abo_updated_at is not None else ""
        ),
        "billing_abo_updated_by": str(billing_abo_updated_by),
        "billing_abo_reason_label": str(billing_abo_reason_label),
        "billing_abo_transition_ref": str(billing_abo_transition_ref),
        "billing_provider_ref_metadata": dict(billing_provider_ref_metadata),
        "entitlement_recompute_required": bool(entitlement_recompute_required),
        "audit_log_ref": str(audit_log_ref),
        "raw_content_retained": False,
        "billing_abo_reason_labels": list(billing_abo_reason_labels),
    }
    return record


# ----------------------------------------------------------------------------
# Record validation
# ----------------------------------------------------------------------------

def _find_forbidden_keys(value: Any) -> Set[str]:
    """
    Recursively scan a value for any forbidden key.

    Returns the set of forbidden keys found (empty if none).
    Scans dict keys at every level. Lists/tuples are traversed
    element-by-element. Cycles are not possible in JSON-safe
    structures, so we do not guard against them here.
    """
    hits: Set[str] = set()
    if isinstance(value, dict):
        for k, v in value.items():
            if k in BILLING_ABO_STATUS_NEVER_INCLUDES:
                hits.add(k)
            hits |= _find_forbidden_keys(v)
    elif isinstance(value, (list, tuple)):
        for item in value:
            hits |= _find_forbidden_keys(item)
    return hits


def _validate_provider_ref_value(value: Any) -> Tuple[bool, List[str]]:
    """
    Validate that a provider_event_ref_metadata value is
    metadata-only (primitives or nested dicts/lists of
    primitives). Raw provider payloads (e.g., nested Stripe
    response objects, raw HTTP request bodies, raw payment
    objects) are rejected.

    Allowed leaf types: str, int, float, bool, None.
    Allowed container types: dict (with str keys), list, tuple.
    Forbidden: bytes, set, custom objects, anything else.

    This is in addition to the 16-key forbidden-keys contract;
    it enforces that the SHAPE of the value is safe metadata,
    not just that the KEYS don't carry sensitive names.
    """
    errors: List[str] = []

    def _walk(v: Any, path: str) -> None:
        if isinstance(v, (str, int, float, bool)) or v is None:
            return
        if isinstance(v, dict):
            for k, item in v.items():
                if not isinstance(k, str):
                    errors.append(
                        f"{REASON_INVALID_PROVIDER_REF_PAYLOAD}:{path}:non_str_key"
                    )
                    continue
                _walk(item, f"{path}.{k}" if path else k)
            return
        if isinstance(v, (list, tuple)):
            for i, item in enumerate(v):
                _walk(item, f"{path}[{i}]")
            return
        # Anything else (bytes, set, custom objects, raw
        # provider payloads) is rejected.
        errors.append(
            f"{REASON_INVALID_PROVIDER_REF_PAYLOAD}:{path}:{type(v).__name__}"
        )

    _walk(value, "")
    return (len(errors) == 0, errors)


def validate_billing_abo_status_record_v1(
    record: Any,
) -> Tuple[bool, List[str]]:
    """
    Validate a billing/abo status record.

    Returns (ok, errors). On success, ok=True and errors is [].
    On failure, ok=False and errors is a list of reason labels
    (machine-readable, safe to log).
    """
    errors: List[str] = []

    if not isinstance(record, dict):
        return (False, [REASON_INVALID_NOT_DICT])

    # Required field presence (operator-specified 14 fields +
    # raw_content_retained + billing_abo_reason_labels).
    required_fields = (
        "billing_abo_record_id",
        "account_id",
        "billing_abo_version",
        "billing_abo_status",
        "previous_billing_abo_status",
        "billing_abo_updated_at",
        "billing_abo_updated_by",
        "billing_abo_reason_label",
        "billing_abo_transition_ref",
        "billing_provider_ref_metadata",
        "entitlement_recompute_required",
        "audit_log_ref",
        "raw_content_retained",
        "billing_abo_reason_labels",
    )
    for field_name in required_fields:
        if field_name not in record:
            errors.append(
                f"{REASON_INVALID_MISSING_FIELDS}:{field_name}"
            )

    # Field type checks.
    if "billing_abo_status" in record and record["billing_abo_status"] not in VALID_BILLING_ABO_STATUSES_V1:
        errors.append(
            f"{REASON_INVALID_BAD_STATUS}:{record['billing_abo_status']}"
        )
    if "billing_abo_record_id" in record and not isinstance(record["billing_abo_record_id"], str):
        errors.append(f"{REASON_INVALID_BAD_STATUS}:billing_abo_record_id_not_str")
    if "account_id" in record:
        if not isinstance(record["account_id"], str):
            errors.append(f"{REASON_INVALID_MISSING_FIELDS}:account_id_not_str")
        elif record["account_id"] == "":
            errors.append(REASON_INVALID_EMPTY_ACCOUNT_ID)
    if "billing_abo_version" in record and record["billing_abo_version"] != BILLING_ABO_HELPER_VERSION:
        errors.append(f"{REASON_INVALID_BAD_VERSION}:{record['billing_abo_version']}")
    if "raw_content_retained" in record and record["raw_content_retained"] is not False:
        errors.append("raw_content_retained_must_be_false")
    if "entitlement_recompute_required" in record and not isinstance(record["entitlement_recompute_required"], bool):
        errors.append("entitlement_recompute_required_must_be_bool")
    if "billing_abo_reason_labels" in record and not isinstance(record["billing_abo_reason_labels"], list):
        errors.append("billing_abo_reason_labels_not_list")
    if "billing_provider_ref_metadata" in record and not isinstance(record["billing_provider_ref_metadata"], dict):
        errors.append("billing_provider_ref_metadata_not_dict")
    # Provider ref metadata must be metadata-only (primitives
    # or nested dicts/lists of primitives). Raw provider
    # payloads (bytes, sets, custom objects) are rejected.
    if "billing_provider_ref_metadata" in record and isinstance(record["billing_provider_ref_metadata"], dict):
        prov_ok, prov_errs = _validate_provider_ref_value(record["billing_provider_ref_metadata"])
        if not prov_ok:
            errors.extend(prov_errs)

    # Recursive scan for forbidden keys.
    forbidden_hits = _find_forbidden_keys(record)
    for k in sorted(forbidden_hits):
        errors.append(f"{REASON_INVALID_FORBIDDEN_KEY}:{k}")

    return (len(errors) == 0, errors)


# ----------------------------------------------------------------------------
# Transition request construction
# ----------------------------------------------------------------------------

def build_billing_abo_transition_request_v1(
    *,
    account_id: str,
    from_status: str,
    to_status: str,
    transition_request_id: Optional[str] = None,
    requested_at: Optional[str] = None,
    requested_by: Optional[str] = "",
    reason_label: Optional[str] = "",
    operator_approved: bool = False,
    provider_event_ref_metadata: Optional[Dict[str, Any]] = None,
    audit_log_ref: Optional[str] = "",
    reason_labels: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Build a billing/abo transition request packet.

    The request describes a single proposed status change. It
    is a defensive dict; this helper does NOT apply the
    transition (call apply_billing_abo_transition_v1 for that).
    """
    if transition_request_id is None:
        transition_request_id = (
            "billing-abo-transition-" + uuid.uuid4().hex
        )

    if provider_event_ref_metadata is None:
        provider_event_ref_metadata = {}
    if reason_labels is None:
        reason_labels = []

    request: Dict[str, Any] = {
        "transition_request_id": str(transition_request_id),
        "account_id": str(account_id),
        "from_status": str(from_status),
        "to_status": str(to_status),
        "requested_at": (
            str(requested_at) if requested_at is not None else ""
        ),
        "requested_by": str(requested_by),
        "reason_label": str(reason_label),
        "operator_approved": bool(operator_approved),
        "provider_event_ref_metadata": dict(provider_event_ref_metadata),
        "audit_log_ref": str(audit_log_ref),
        "raw_content_retained": False,
        "reason_labels": list(reason_labels),
    }
    return request


# ----------------------------------------------------------------------------
# Transition request validation
# ----------------------------------------------------------------------------

def validate_billing_abo_transition_request_v1(
    request: Any,
) -> Tuple[bool, List[str]]:
    """
    Validate a billing/abo transition request packet.

    Returns (ok, errors). On success, ok=True and errors is [].
    On failure, ok=False and errors is a list of reason labels.
    """
    errors: List[str] = []

    if not isinstance(request, dict):
        return (False, [REASON_INVALID_REQUEST_NOT_DICT])

    required_fields = (
        "transition_request_id",
        "account_id",
        "from_status",
        "to_status",
        "requested_at",
        "requested_by",
        "reason_label",
        "operator_approved",
        "provider_event_ref_metadata",
        "audit_log_ref",
        "raw_content_retained",
    )
    for field_name in required_fields:
        if field_name not in request:
            errors.append(
                f"{REASON_INVALID_MISSING_FIELDS}:{field_name}"
            )

    if "account_id" in request:
        if not isinstance(request["account_id"], str):
            errors.append(f"{REASON_INVALID_MISSING_FIELDS}:account_id_not_str")
        elif request["account_id"] == "":
            errors.append(REASON_INVALID_EMPTY_ACCOUNT_ID)
    if "from_status" in request and request["from_status"] not in VALID_BILLING_ABO_STATUSES_V1:
        errors.append(
            f"{REASON_INVALID_BAD_STATUS}:from_status:{request['from_status']}"
        )
    if "to_status" in request and request["to_status"] not in VALID_BILLING_ABO_STATUSES_V1:
        errors.append(
            f"{REASON_INVALID_BAD_STATUS}:to_status:{request['to_status']}"
        )
    if "operator_approved" in request and not isinstance(request["operator_approved"], bool):
        errors.append("operator_approved_must_be_bool")
    if "raw_content_retained" in request and request["raw_content_retained"] is not False:
        errors.append("raw_content_retained_must_be_false")
    if "provider_event_ref_metadata" in request and not isinstance(request["provider_event_ref_metadata"], dict):
        errors.append("provider_event_ref_metadata_not_dict")
    if "provider_event_ref_metadata" in request and isinstance(request["provider_event_ref_metadata"], dict):
        prov_ok, prov_errs = _validate_provider_ref_value(request["provider_event_ref_metadata"])
        if not prov_ok:
            errors.extend(prov_errs)

    # Recursive scan for forbidden keys.
    forbidden_hits = _find_forbidden_keys(request)
    for k in sorted(forbidden_hits):
        errors.append(f"{REASON_INVALID_FORBIDDEN_KEY}:{k}")

    return (len(errors) == 0, errors)


# ----------------------------------------------------------------------------
# Apply transition
# ----------------------------------------------------------------------------

def apply_billing_abo_transition_v1(
    record: Dict[str, Any],
    request: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Apply a billing/abo transition to a record, returning a new
    record (defensive copy) and a result envelope.

    The result envelope has the shape:
      {
        "ok": bool,
        "record": dict or None,
        "reason_labels": list[str],
        "summary": str,
        "suggested_audit_metadata": dict,  # NEVER applied to a log
        "requires_operator_approval": bool,
      }

    The transition policy is:
      1. Same-status (from == to) is rejected.
      2. Destructive transitions (target in
         DESTRUCTIVE_BILLING_ABO_TARGETS_V1) require
         request.operator_approved == True.
      3. Default-deny: any transition not in
         ALLOWED_BILLING_ABO_TRANSITIONS_V1 is rejected.
      4. Terminal from-status (refunded) is rejected.
      5. Restricted terminal-like from-status requires the
         transition to be in its narrow allow-list.

    The helper does NOT write to any log; the suggested audit
    metadata is returned to the caller for optional persistence.
    """
    base = {
        "ok": False,
        "record": None,
        "reason_labels": [],
        "summary": "",
        "suggested_audit_metadata": {},
        "requires_operator_approval": False,
    }

    # 1. Validate the record first.
    record_ok, record_errors = validate_billing_abo_status_record_v1(record)
    if not record_ok:
        return {
            **base,
            "reason_labels": [
                f"record_invalid:{e}" for e in record_errors
            ],
            "summary": "apply denied: record validation failed",
        }

    # 2. Validate the request.
    request_ok, request_errors = validate_billing_abo_transition_request_v1(request)
    if not request_ok:
        return {
            **base,
            "reason_labels": [
                f"request_invalid:{e}" for e in request_errors
            ],
            "summary": "apply denied: request validation failed",
        }

    from_status = request["from_status"]
    to_status = request["to_status"]

    # 3. Account-ID mismatch rejection. The request's
    #    account_id MUST match the record's account_id;
    #    otherwise the transition would corrupt the
    #    cross-account transition log.
    record_account_id = str(record.get("account_id", ""))
    request_account_id = str(request.get("account_id", ""))
    if record_account_id != request_account_id:
        return {
            **base,
            "reason_labels": [REASON_INVALID_ACCOUNT_ID_MISMATCH],
            "summary": (
                f"apply denied: account_id mismatch "
                f"(record={record_account_id!r}, request={request_account_id!r})"
            ),
        }

    # 4. Same-status rejection.
    if from_status == to_status:
        return {
            **base,
            "reason_labels": [REASON_INVALID_SAME_STATUS],
            "summary": f"apply denied: from_status and to_status are both '{from_status}'",
        }

    # 5. Destructive-target operator approval gate.
    if to_status in DESTRUCTIVE_BILLING_ABO_TARGETS_V1:
        if not bool(request.get("operator_approved", False)):
            return {
                **base,
                "reason_labels": [
                    "destructive_billing_abo_transition_requires_operator_approval"
                ],
                "summary": (
                    f"apply denied: transition to '{to_status}' requires operator approval"
                ),
                "requires_operator_approval": True,
            }

    # 6. Default-deny: any transition not in
    #    ALLOWED_BILLING_ABO_TRANSITIONS_V1 is rejected.
    allowed_next = ALLOWED_BILLING_ABO_TRANSITIONS_V1.get(from_status, frozenset())
    if to_status not in allowed_next:
        # Terminal-like from-status: still has outgoing
        # transitions in its narrow allow-list, but anything
        # outside that list is rejected.
        if from_status in TERMINAL_LIKE_BILLING_ABO_STATUSES_V1:
            return {
                **base,
                "reason_labels": [REASON_INVALID_TERMINAL_TRANSITION],
                "summary": (
                    f"apply denied: '{from_status}' is terminal-like; "
                    f"only specific next states allowed (not '{to_status}')"
                ),
            }
        return {
            **base,
            "reason_labels": [REASON_INVALID_BAD_TRANSITION],
            "summary": (
                f"apply denied: transition '{from_status} -> {to_status}' is not allowed"
            ),
        }

    # 6. Apply the transition: build a new record with the
    #    updated status and metadata from the request. Do NOT
    #    mutate the input record; return a defensive copy.
    new_record = dict(record)
    new_record["previous_billing_abo_status"] = from_status
    new_record["billing_abo_status"] = to_status
    new_record["billing_abo_updated_at"] = request.get("requested_at", "") or record.get("billing_abo_updated_at", "")
    new_record["billing_abo_updated_by"] = request.get("requested_by", "") or record.get("billing_abo_updated_by", "")
    new_record["billing_abo_reason_label"] = request.get("reason_label", "") or record.get("billing_abo_reason_label", "")
    new_record["billing_abo_transition_ref"] = request.get("transition_request_id", "") or record.get("billing_abo_transition_ref", "")
    new_record["audit_log_ref"] = request.get("audit_log_ref", "") or record.get("audit_log_ref", "")
    new_record["entitlement_recompute_required"] = True
    # Carry forward any provider ref metadata from the request
    # (non-sensitive; validator scans recursively).
    provider_ref_meta = request.get("provider_event_ref_metadata", {})
    if isinstance(provider_ref_meta, dict) and provider_ref_meta:
        # Merge with the record's existing billing_provider_ref_metadata;
        # the request's metadata takes precedence (it's the new event).
        merged = dict(record.get("billing_provider_ref_metadata", {}))
        merged.update(provider_ref_meta)
        new_record["billing_provider_ref_metadata"] = merged
    # Append a reason_label if a transition reason was provided.
    transition_reasons: List[str] = []
    if request.get("reason_label"):
        transition_reasons.append(request["reason_label"])
    if to_status in DESTRUCTIVE_BILLING_ABO_TARGETS_V1 and bool(request.get("operator_approved", False)):
        transition_reasons.append("destructive_billing_abo_transition_operator_approved")
    if transition_reasons:
        existing = list(record.get("billing_abo_reason_labels", []))
        new_record["billing_abo_reason_labels"] = existing + transition_reasons

    # 7. Suggested audit metadata (returned to caller, NOT written
    #    by this helper).
    suggested_audit_metadata = {
        "audit_category": "billing_abo_status_transition",
        "audit_account_id": record.get("account_id", ""),
        "audit_from_status": from_status,
        "audit_to_status": to_status,
        "audit_request_id": request.get("transition_request_id", ""),
        "audit_requested_at": request.get("requested_at", ""),
        "audit_requested_by": request.get("requested_by", ""),
        "audit_operator_approved": bool(request.get("operator_approved", False)),
        "audit_destructive_target": to_status in DESTRUCTIVE_BILLING_ABO_TARGETS_V1,
        "audit_record_id": new_record.get("billing_abo_record_id", ""),
    }

    return {
        "ok": True,
        "record": new_record,
        "reason_labels": [REASON_OK],
        "summary": f"applied transition: {from_status} -> {to_status}",
        "suggested_audit_metadata": suggested_audit_metadata,
        "requires_operator_approval": False,
    }


# ----------------------------------------------------------------------------
# Chat-access pre-check
# ----------------------------------------------------------------------------

def billing_status_allows_chat_access_v1(
    record: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Determine whether the billing/abo status allows chat access
    (metadata-only pre-check; runtime wrapper combines this with
    the account-status-level pre-check from Slice 6 before
    granting chat access).

    Returns an envelope:
      {
        "ok": bool,                       # validation passed
        "billing_status": str or None,
        "allows_chat_access": bool,
        "reason_labels": list[str],
        "summary": str,
      }

    If the record is invalid, ok=False and allows_chat_access=False.
    If valid, ok=True and allows_chat_access reflects the
    BILLING_ABO_CHAT_ACCESS_ALLOWED_V1 set membership.

    This is a STATUS-LEVEL pre-check only. The runtime wrapper
    must additionally verify the account_status (Slice 6) is
    chat-enabled AND the entitlement packet (Slice 5) grants
    chat capability before granting chat access.
    """
    record_ok, record_errors = validate_billing_abo_status_record_v1(record)
    if not record_ok:
        return {
            "ok": False,
            "billing_status": None,
            "allows_chat_access": False,
            "reason_labels": [
                f"record_invalid:{e}" for e in record_errors
            ],
            "summary": "billing_status check denied: record invalid",
        }

    billing_status = record.get("billing_abo_status", "")
    allows = billing_status in BILLING_ABO_CHAT_ACCESS_ALLOWED_V1

    return {
        "ok": True,
        "billing_status": billing_status,
        "allows_chat_access": allows,
        "reason_labels": [REASON_OK if allows else "billing_status_does_not_allow_chat_access"],
        "summary": (
            f"billing_status={billing_status} allows_chat_access={allows}"
        ),
    }


# ----------------------------------------------------------------------------
# Summarize
# ----------------------------------------------------------------------------

def summarize_billing_abo_status_record_v1(
    record: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Produce a short metadata-only summary of a billing/abo
    record. Strips any field that is not in the canonical
    summary set; returns ok=True with a summary envelope.

    Summary fields (8 fields; metadata-only):
      - summary_version
      - account_id
      - billing_abo_status
      - previous_billing_abo_status
      - billing_abo_updated_at
      - billing_abo_updated_by
      - billing_abo_reason_label
      - entitlement_recompute_required
      - allows_chat_access

    The summary NEVER carries raw prompts/replies, credentials,
    payment data, billing provider tokens, or any of the
    16 forbidden keys.
    """
    record_ok, record_errors = validate_billing_abo_status_record_v1(record)
    if not record_ok:
        return {
            "ok": False,
            "summary": None,
            "reason_labels": [
                f"record_invalid:{e}" for e in record_errors
            ],
        }

    chat_access = billing_status_allows_chat_access_v1(record)

    summary = {
        "summary_version": BILLING_ABO_HELPER_VERSION + ":summary",
        "account_id": record.get("account_id", ""),
        "billing_abo_status": record.get("billing_abo_status", ""),
        "previous_billing_abo_status": record.get("previous_billing_abo_status", ""),
        "billing_abo_updated_at": record.get("billing_abo_updated_at", ""),
        "billing_abo_updated_by": record.get("billing_abo_updated_by", ""),
        "billing_abo_reason_label": record.get("billing_abo_reason_label", ""),
        "entitlement_recompute_required": bool(record.get("entitlement_recompute_required", False)),
        "allows_chat_access": bool(chat_access.get("allows_chat_access", False)),
    }

    return {
        "ok": True,
        "summary": summary,
        "reason_labels": [REASON_OK],
    }


# ----------------------------------------------------------------------------
# JSON-safe serialization
# ----------------------------------------------------------------------------

def to_billing_abo_status_json_safe_v1(value: Any) -> str:
    """
    Serialize a billing/abo value to JSON with all 16 forbidden
    keys recursively redacted (replaced with the sentinel
    string "<redacted:billing-abo-forbidden-key>").

    Forbidden keys are scanned recursively (dicts, lists, tuples).
    Cycles are detected via a seen-set; cyclic values get the
    sentinel string "<cyclic>". On any other serialization
    failure, the helper returns
    '{"serialization_error": true}' rather than raising.

    The output is safe to log: it never carries payment data,
    raw prompts/replies, credentials, hidden prompts, system
    prompts, chain-of-thought traces, provider responses, or
    real shadow-call outputs.
    """
    def _scrub(v: Any, seen: Set[int]) -> Any:
        vid = id(v)
        if vid in seen:
            return "<cyclic>"
        if isinstance(v, dict):
            seen.add(vid)
            out: Dict[Any, Any] = {}
            for k, val in v.items():
                if isinstance(k, str) and k in BILLING_ABO_STATUS_NEVER_INCLUDES:
                    out[k] = "<redacted:billing-abo-forbidden-key>"
                else:
                    out[k] = _scrub(val, seen)
            return out
        if isinstance(v, (list, tuple)):
            seen.add(vid)
            return [_scrub(item, seen) for item in v]
        return v

    try:
        safe_value = _scrub(value, set())
        return json.dumps(safe_value, sort_keys=True, default=str, ensure_ascii=False)
    except (TypeError, ValueError):
        return json.dumps({"serialization_error": True}, ensure_ascii=False)


# ----------------------------------------------------------------------------
# Self-test (sanity check; runs only when executed directly)
# ----------------------------------------------------------------------------

if __name__ == "__main__":  # pragma: no cover
    rec = build_billing_abo_status_record_v1(
        account_id="acct-test",
        billing_abo_status="free_pilot",
    )
    ok, errs = validate_billing_abo_status_record_v1(rec)
    print("record ok:", ok, "errors:", errs)
    req = build_billing_abo_transition_request_v1(
        account_id="acct-test",
        from_status="free_pilot",
        to_status="active",
    )
    res = apply_billing_abo_transition_v1(rec, req)
    print("apply ok:", res["ok"], "summary:", res["summary"])
    chat = billing_status_allows_chat_access_v1(rec)
    print("chat access (free_pilot):", chat["allows_chat_access"])
    summary = summarize_billing_abo_status_record_v1(rec)
    print("summary ok:", summary["ok"])
    j = to_billing_abo_status_json_safe_v1(rec)
    print("json_safe:", j)
