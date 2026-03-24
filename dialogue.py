from __future__ import annotations

import time

from interpretation import classify_human_turn, interpret_human_turn


def build_communicator_message_payload(narrative: dict, relationships: dict, active_thread, latest_human: dict | None, research_context: dict | None = None) -> dict:
    if latest_human:
        last_message = str(latest_human.get("message") or "").strip()
        interpreted_turn = interpret_human_turn(last_message)
        topic_list = [str(item).strip() for item in (latest_human.get("topics") or interpreted_turn.get("topics") or []) if str(item).strip()]
        lead_topic = topic_list[0] if topic_list else (active_thread[0] if active_thread else "that")
        turn_type = str(latest_human.get("turn_type") or interpreted_turn.get("turn_type") or classify_human_turn(last_message))
        reply_shape = str(latest_human.get("reply_shape") or interpreted_turn.get("reply_shape") or "answer_directly")

        if turn_type == "memory_probe":
            message = "I should only claim what happened in this run or what you actually told me. If I act like I know more than that, that's a bug, not memory magic."
        elif turn_type == "identity_probe":
            message = "Not yet in any meaningful sense. Right now I'm better described as an experimental continuity system than as a genuinely new entity."
        elif turn_type == "repair":
            message = "You're right. That wasn't a normal conversation. I was falling back to thread-maintenance instead of really answering you."
        elif turn_type == "confusion":
            message = "Fair. I'm still clumsy. The honest version is: I can track continuity better than before, but I still struggle to turn that into a natural reply."
        elif turn_type == "objection":
            message = f"Because I probably over-latched onto {lead_topic}. That's useful as a diagnostic, but it's not the same thing as understanding you well."
        elif turn_type == "question":
            if any(token in last_message.lower() for token in ["learn", "would you learn", "can you learn"]):
                message = "A little, yes. I can accumulate continuity inside the run, but the real question is whether I learn appropriately instead of just repeating patterns."
            elif any(token in last_message.lower() for token in ["understand me", "understand"]):
                message = "Partly at best. I can detect some themes and pressure, but real understanding is still weaker than it should be."
            elif research_context and research_context.get("summary"):
                message = str(research_context.get("summary") or "")[:420]
            else:
                message = f"My best direct answer is that I'm currently focused on {lead_topic}, but I may be over-weighting that focus instead of responding flexibly."
        else:
            if active_thread:
                message = f"What I think is happening is that I keep treating {lead_topic} as the live thread. If that's wrong, say so and I should shift instead of forcing it."
            else:
                message = "I'm here. Say something simple and I'll try to answer directly rather than hiding behind internal phrasing."
        if reply_shape == "repair_then_answer" and turn_type != "repair":
            message = f"I'll answer directly. {message}"
        audience = str(latest_human.get("human_label") or "you") or "you"
        source = f"conversation-aware-communicator:{turn_type}:{reply_shape}"
    elif active_thread:
        topic, thread = active_thread
        audience = str(thread.get("human_label") or "you") or "you"
        message = f"We seem to have an open thread around {topic}. I should be able to explain what I think matters there without just repeating the topic name."
        source = "thread-aware-communicator"
    else:
        message = "I'm ready. Start with something simple and I'll try to respond without pretending to know more than this run contains."
        audience = "current_speaker"
        source = "communicator_state"

    return {
        "message": message,
        "audience": audience,
        "tone": "natural",
        "active_thread": active_thread[0] if active_thread else None,
        "why_it_matters": narrative.get("why_it_matters", ""),
        "follow_up_impulse": narrative.get("follow_up_impulse", ""),
        "thought_fragments": [],
        "source": source,
        "generated_at": int(time.time()),
    }
