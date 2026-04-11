# request_intelligence.py - WESLR v43: Request Intelligence Layer
# Priority: Request Intelligence Integration
#
# Parses operator requests and maps them to capabilities, context,
# and decision influence. Deterministic-first, no model dependency.
#
# DOCTRINE SOURCE:
# - WESLR should understand operator intent
# - Requests should influence decision synthesis
# - Capability routing should be explicit
# - Governance boundaries must be preserved
#
# This module is the canonical request parsing layer, independent of
# any host runtime (OpenClaw, Claude, etc.).

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


# ============================================================================
# REQUEST TYPE ENUM
# ============================================================================


class RequestType(str, Enum):
    """Type of operator request."""
    QUERY = "query"           # Get information (status, help, blocked)
    ACTION = "action"         # Perform operation (configure, execute)
    APPROVAL = "approval"      # Approve or reject something
    CLARIFICATION = "clarification"  # Get explanation or context
    UNKNOWN = "unknown"       # Unclear request


class RequestIntent(str, Enum):
    """Specific intent of the request."""
    # Query intents
    STATUS = "status"         # Get current status
    BLOCKED = "blocked"       # Get blocked items
    ESCALATIONS = "escalations"  # Get pending escalations
    HELP = "help"            # Get help
    
    # Action intents
    CONFIGURE = "configure"   # Configure something
    EXECUTE = "execute"      # Execute something
    CLEAR = "clear"          # Clear state
    
    # Approval intents
    APPROVE = "approve"      # Approve an item
    REJECT = "reject"        # Reject an item
    
    # Clarification intents
    EXPLAIN = "explain"       # Explain something
    WHY = "why"             # Why is this blocked/prioritized


class RequestCapability(str, Enum):
    """Capability relevant to the request."""
    # Class 1: Self-sufficient
    READ_DATA = "read_data"
    ANALYZE = "analyze"
    SURFACE = "surface"
    RECOMMEND = "recommend"
    
    # Class 2: Bounded autonomous
    CONFIGURE = "configure"
    MODIFY = "modify"
    
    # Class 3: Approval-gated
    EXECUTE = "execute"
    APPROVE = "approve"
    REJECT = "reject"
    
    # Unknown
    UNKNOWN = "unknown"


# ============================================================================
# REQUEST CONTEXT
# ============================================================================


@dataclass
class RequestContext:
    """Context extracted from the request."""
    
    # Item references
    item_id: Optional[str] = None
    item_type: Optional[str] = None
    
    # Scope/parameters
    scope: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    
    # Extracted entities
    entities: List[str] = field(default_factory=list)
    
    # References
    references: Dict[str, str] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "item_id": self.item_id,
            "item_type": self.item_type,
            "scope": self.scope,
            "parameters": self.parameters,
            "entities": self.entities,
            "references": self.references,
        }


# ============================================================================
# PARSED REQUEST
# ============================================================================


@dataclass
class ParsedRequest:
    """Result of parsing an operator request."""
    
    # Original message
    message: str
    
    # Parsed components
    request_type: str  # RequestType.value
    intent: str        # RequestIntent.value
    capability: str    # RequestCapability.value
    
    # Context
    context: RequestContext
    
    # Governance
    autonomy_class: str  # AutonomyClass.value from capability
    
    # Decision influence
    should_influence_decision: bool = False
    should_prioritize_items: List[str] = field(default_factory=list)
    should_add_to_queue: List[Dict[str, Any]] = field(default_factory=list)
    
    # Metadata
    confidence: float = 1.0
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "message": self.message,
            "request_type": self.request_type,
            "intent": self.intent,
            "capability": self.capability,
            "context": self.context.to_dict(),
            "autonomy_class": self.autonomy_class,
            "should_influence_decision": self.should_influence_decision,
            "should_prioritize_items": self.should_prioritize_items,
            "should_add_to_queue": self.should_add_to_queue,
            "confidence": self.confidence,
            "timestamp": self.timestamp,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ParsedRequest":
        """Create from dictionary."""
        context = RequestContext(**data.get("context", {}))
        return cls(
            message=data.get("message", ""),
            request_type=data.get("request_type", RequestType.UNKNOWN.value),
            intent=data.get("intent", ""),
            capability=data.get("capability", RequestCapability.UNKNOWN.value),
            context=context,
            autonomy_class=data.get("autonomy_class", "class_2_bounded_autonomous"),
            should_influence_decision=data.get("should_influence_decision", False),
            should_prioritize_items=data.get("should_prioritize_items", []),
            should_add_to_queue=data.get("should_add_to_queue", []),
            confidence=data.get("confidence", 1.0),
            timestamp=data.get("timestamp", datetime.now(timezone.utc).isoformat()),
        )


# ============================================================================
# REQUEST PARSER
# ============================================================================


class RequestParser:
    """
    Deterministic request parser for operator messages.
    
    Uses pattern matching to extract intent, capability, and context.
    No model dependency. Doctrine-aligned.
    """
    
    # Intent patterns: (patterns, request_type, intent, capability, autonomy_class)
    INTENT_PATTERNS = [
        # Query patterns
        (["status", "what's happening", "what's happening?", "what's going on", "current status"],
         RequestType.QUERY, RequestIntent.STATUS, RequestCapability.READ_DATA, "class_1_self_sufficient"),
        
        (["blocked", "blockers", "what's blocked", "stuck items", "blocking"],
         RequestType.QUERY, RequestIntent.BLOCKED, RequestCapability.READ_DATA, "class_1_self_sufficient"),
        
        (["escalations", "escalation", "pending escalations", "pending items"],
         RequestType.QUERY, RequestIntent.ESCALATIONS, RequestCapability.READ_DATA, "class_1_self_sufficient"),
        
        (["help", "commands", "?", "what can you do"],
         RequestType.QUERY, RequestIntent.HELP, RequestCapability.SURFACE, "class_1_self_sufficient"),
        
        # Action patterns
        (["configure", "set", "change", "update"],
         RequestType.ACTION, RequestIntent.CONFIGURE, RequestCapability.CONFIGURE, "class_2_bounded_autonomous"),
        
        (["execute", "run", "start", "launch"],
         RequestType.ACTION, RequestIntent.EXECUTE, RequestCapability.EXECUTE, "class_3_approval_gated"),
        
        (["clear", "reset", "clear state"],
         RequestType.ACTION, RequestIntent.CLEAR, RequestCapability.MODIFY, "class_2_bounded_autonomous"),
        
        # Approval patterns
        (["approve", "yes", "confirm"],
         RequestType.APPROVAL, RequestIntent.APPROVE, RequestCapability.APPROVE, "class_3_approval_gated"),
        
        (["reject", "no", "deny", "decline"],
         RequestType.APPROVAL, RequestIntent.REJECT, RequestCapability.REJECT, "class_3_approval_gated"),
        
        # Clarification patterns
        (["explain", "why", "tell me about", "what is"],
         RequestType.CLARIFICATION, RequestIntent.EXPLAIN, RequestCapability.SURFACE, "class_1_self_sufficient"),
    ]
    
    # Entity patterns for extracting IDs, names, etc.
    ID_PATTERN = r"[a-f0-9]{8,}"  # Hex ID (at least 8 chars)
    ITEM_PATTERN = r"(?:item|escalation|proposal|approval)\s+([a-zA-Z0-9_-]+)"
    
    def __init__(self):
        """Initialize the request parser."""
        pass
    
    def parse(self, message: str) -> ParsedRequest:
        """
        Parse an operator message into structured request.
        
        Args:
            message: The operator's message
        
        Returns:
            ParsedRequest with type, intent, capability, context
        """
        msg_lower = message.lower().strip()
        
        # Find matching intent
        for patterns, req_type, intent, capability, autonomy_class in self.INTENT_PATTERNS:
            for pattern in patterns:
                if pattern in msg_lower:
                    context = self._extract_context(message, intent)
                    should_influence = self._should_influence_decision(req_type, intent)
                    prioritize = self._get_prioritize_items(intent, context)
                    add_to_queue = self._get_add_to_queue(intent, context)
                    
                    return ParsedRequest(
                        message=message,
                        request_type=req_type.value,
                        intent=intent.value,
                        capability=capability.value,
                        context=context,
                        autonomy_class=autonomy_class,
                        should_influence_decision=should_influence,
                        should_prioritize_items=prioritize,
                        should_add_to_queue=add_to_queue,
                    )
        
        # Unknown request
        return ParsedRequest(
            message=message,
            request_type=RequestType.UNKNOWN.value,
            intent="",
            capability=RequestCapability.UNKNOWN.value,
            context=RequestContext(),
            autonomy_class="class_2_bounded_autonomous",
        )
    
    def _extract_context(self, message: str, intent: RequestIntent) -> RequestContext:
        """Extract context from message."""
        import re
        
        context = RequestContext()
        msg_lower = message.lower()
        
        # Extract hex IDs
        id_matches = re.findall(self.ID_PATTERN, message)
        if id_matches:
            context.item_id = id_matches[0]
            context.entities = id_matches
        
        # Extract item references
        item_match = re.search(self.ITEM_PATTERN, msg_lower)
        if item_match:
            context.item_type = "item"
            context.item_id = item_match.group(1)
        
        # Intent-specific context
        if intent == RequestIntent.APPROVE or intent == RequestIntent.REJECT:
            context.item_type = "approval"
        elif intent == RequestIntent.CONFIGURE:
            context.parameters["action"] = "configure"
        elif intent == RequestIntent.EXECUTE:
            context.parameters["action"] = "execute"
        
        return context
    
    def _should_influence_decision(self, req_type: RequestType, intent: RequestIntent) -> bool:
        """Determine if request should influence decision synthesis."""
        # Query and clarification don't change state
        if req_type in [RequestType.QUERY, RequestType.CLARIFICATION]:
            return False
        
        # Actions and approvals change state
        if req_type in [RequestType.ACTION, RequestType.APPROVAL]:
            return True
        
        return False
    
    def _get_prioritize_items(self, intent: RequestIntent, context: RequestContext) -> List[str]:
        """Get items to prioritize based on request."""
        # If request mentions specific item, prioritize it
        if context.item_id:
            return [context.item_id]
        return []
    
    def _get_add_to_queue(self, intent: RequestIntent, context: RequestContext) -> List[Dict[str, Any]]:
        """Get items to add to queues based on request."""
        items = []
        
        # Execute intent adds to approval queue
        if intent == RequestIntent.EXECUTE:
            items.append({
                "queue": "approval_queue",
                "item_type": "execution_request",
                "item_id": context.item_id,
                "reason": "Execution requires approval",
            })
        
        return items


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================


# Global parser instance
_parser: Optional[RequestParser] = None


def get_parser() -> RequestParser:
    """Get the global parser instance."""
    global _parser
    if _parser is None:
        _parser = RequestParser()
    return _parser


def reset_parser():
    """Reset the global parser (for testing)."""
    global _parser
    _parser = None


def parse_request(message: str) -> ParsedRequest:
    """
    Convenience function to parse a request.
    
    Args:
        message: Operator's message
    
    Returns:
        ParsedRequest with type, intent, capability, context
    """
    parser = get_parser()
    return parser.parse(message)


def get_request_type(message: str) -> str:
    """Get the request type for a message."""
    result = parse_request(message)
    return result.request_type


def get_request_intent(message: str) -> str:
    """Get the request intent for a message."""
    result = parse_request(message)
    return result.intent


def get_request_capability(message: str) -> str:
    """Get the capability for a message."""
    result = parse_request(message)
    return result.capability


def get_request_relevance(message: str) -> Dict[str, Any]:
    """
    Get full request relevance including capability and autonomy class.
    
    Args:
        message: Operator's message
    
    Returns:
        Dict with request_type, intent, capability, autonomy_class,
        should_influence_decision, governance implications
    """
    result = parse_request(message)
    return result.to_dict()


# ============================================================================
# DECISION INFLUENCE
# ============================================================================


def apply_request_to_decision(
    parsed: ParsedRequest,
    decision: Dict[str, Any],
    background_signals: Optional[List[Dict[str, Any]]] = None,
    scientific_guidance: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Apply request influence to decision synthesis.
    
    This is the integration point between request intelligence
    and decision layer. It modifies decision output based on
    the parsed request.
    
    Args:
        parsed: Parsed request
        decision: Current decision output dict
        background_signals: Optional structured background signals (e.g., stale_data)
        scientific_guidance: Optional structured scientific signals (e.g., underpowered_test)
    
    Returns:
        Modified decision output with request influence applied
    """
    # Don't modify if request doesn't influence
    if not parsed.should_influence_decision:
        return decision
    
    # Copy decision to avoid mutation
    result = decision.copy()
    
    # Prioritize specific items
    if parsed.should_prioritize_items:
        what_matters = result.get("what_matters_now", [])
        for item_id in parsed.should_prioritize_items:
            # Boost priority of mentioned items
            for item in what_matters:
                if item.get("item_id", "").startswith(item_id):
                    item["priority_boost"] = True
                    item["priority_reason"] = "operator_requested"
    
    # Add items to queues
    if parsed.should_add_to_queue:
        for queue_item in parsed.should_add_to_queue:
            queue_name = queue_item.pop("queue", "")
            if queue_name == "approval_queue":
                approvals = result.get("approval_queue", [])
                approvals.append(queue_item)
                result["approval_queue"] = approvals
    
    # Apply signals if provided (minimal slice for maturity signals)
    try:
        from .decision_layer import apply_background_signals, apply_scientific_guidance  # lazy import to avoid cycle
    except Exception:
        apply_background_signals = None
        apply_scientific_guidance = None
    bg = background_signals or parsed.context.parameters.get("background_signals")
    sci = scientific_guidance or parsed.context.parameters.get("scientific_guidance")
    if apply_background_signals and bg:
        result = apply_background_signals(result, bg)
    if apply_scientific_guidance and sci:
        result = apply_scientific_guidance(result, sci)
    
    # Mark as request-influenced
    result["request_influenced"] = True
    result["request_type"] = parsed.request_type
    result["request_intent"] = parsed.intent
    
    return result
