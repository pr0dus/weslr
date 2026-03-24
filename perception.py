from __future__ import annotations


def build_human_exchange_payload(human_name: str, display_name: str, message: str, response: str, topic_list: list[str], interpreted_turn: dict, now_ts: int) -> tuple[dict, dict]:
    message_text = str(message or "")
    response_text = str(response or "")
    exchange = {
        "id": f"hx-{now_ts}",
        "human": human_name,
        "human_label": display_name,
        "topics": topic_list,
        "message_summary": (message_text[:96] + ("…" if len(message_text) > 96 else "")),
        "response_summary": (response_text[:96] + ("…" if len(response_text) > 96 else "")),
        "created_at": now_ts,
        "source": "human_exchange",
    }
    recent_message = {
        "human": human_name,
        "human_label": display_name,
        "topics": topic_list,
        "message": message_text[:240],
        "response": response_text[:240],
        "turn_type": interpreted_turn.get("turn_type", "statement"),
        "intent": interpreted_turn.get("intent", ""),
        "stance": interpreted_turn.get("stance", "neutral"),
        "reply_shape": interpreted_turn.get("reply_shape", "answer_directly"),
        "created_at": now_ts,
    }
    return exchange, recent_message
