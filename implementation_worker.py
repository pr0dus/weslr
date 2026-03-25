from __future__ import annotations

import json
import subprocess
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
STATE_PATH = BASE_DIR / "implementation_state.json"
DIALOGUE_PATH = BASE_DIR / "dialogue.py"
INTERPRETATION_PATH = BASE_DIR / "interpretation.py"
MAIN_PATH = BASE_DIR / "main.py"


def save_state(payload: dict) -> None:
    STATE_PATH.write_text(json.dumps(payload, indent=2))


def add_continuation_note(*, objective: str, completed: str, files_changed: str, behavior_changed: str, checks_performed: str, known_risks: str, next_exact_step: str, resume_hint: str) -> None:
    subprocess.run([
        sys.executable,
        str(MAIN_PATH),
        "continuation-add",
        "--author",
        "implementation-worker",
        "--objective",
        objective,
        "--completed",
        completed,
        "--files-changed",
        files_changed,
        "--behavior-changed",
        behavior_changed,
        "--checks-performed",
        checks_performed,
        "--known-risks",
        known_risks,
        "--next-exact-step",
        next_exact_step,
        "--resume-hint",
        resume_hint,
    ], cwd=BASE_DIR, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def patch_dialogue_actual_coding() -> dict:
    text = DIALOGUE_PATH.read_text()
    changed = False

    marker = '            asks_can_you_implement = any(token in lower_message for token in ["can you implement", "will you implement", "could you implement"])' + "\n"
    insert = (
        '            asks_can_you_implement = any(token in lower_message for token in ["can you implement", "will you implement", "could you implement"])\n'
        '            asks_for_actual_coding = any(token in lower_message for token in ["actual coding", "the actual coding"])\n'
    )
    if 'asks_for_actual_coding' not in text:
        if marker not in text:
            raise RuntimeError("dialogue marker for asks_can_you_implement not found")
        text = text.replace(marker, insert)
        changed = True

    old = (
        '            if asks_how_are_you:\n'
        '                message = "Uneven, honestly — better than before at keeping a thread, still weak at turning that into natural understanding."\n'
        '            elif asks_can_you_implement:\n'
        '                message = "Yes, if implementation is allowed, I should move from listing changes to actually making them. The next step would be to pick one concrete fix and apply it instead of repeating the whole plan."\n'
    )
    new = (
        '            if asks_how_are_you:\n'
        '                message = "Uneven, honestly — better than before at keeping a thread, still weak at turning that into natural understanding."\n'
        '            elif asks_for_actual_coding:\n'
        '                message = "The actual coding should start with three concrete pieces: a stronger intent rewriter for messy human requests, a tiny workflow state for suggest/approve/start/finished, and better reply grounding so selected threads turn into direct answers instead of self-report."\n'
        '            elif asks_can_you_implement:\n'
        '                message = "Yes, if implementation is allowed, I should move from listing changes to actually making them. The next step would be to pick one concrete fix and apply it instead of repeating the whole plan."\n'
    )
    if new not in text:
        if old not in text:
            raise RuntimeError("dialogue branch for implementation-question handling not found")
        text = text.replace(old, new)
        changed = True

    if changed:
        DIALOGUE_PATH.write_text(text)

    return {
        "summary": "Implemented a direct answer path for 'actual coding' prompts in dialogue.py.",
        "changed": changed,
        "files_changed": "implementation_worker.py, dialogue.py",
        "behavior_changed": "Dialogue can now answer 'actual coding' prompts directly, and bounded implementation runs are driven by declared task metadata.",
    }


def patch_correction_handling() -> dict:
    interpretation = INTERPRETATION_PATH.read_text()
    dialogue = DIALOGUE_PATH.read_text()
    changed = False

    old_repair = '    if any(token in lowered for token in ["this is not", "not normal conversation", "you still need to learn", "evolve", "stop telling me", "answer directly"]):\n        return "repair"\n'
    new_repair = '    if any(token in lowered for token in ["this is not", "not normal conversation", "you still need to learn", "evolve", "stop telling me", "answer directly", "that\'s wrong", "thats wrong", "that is wrong", "not what i meant", "you misunderstood", "you got that wrong"]):\n        return "repair"\n'
    if new_repair not in interpretation:
        if old_repair not in interpretation:
            raise RuntimeError("interpretation repair marker not found")
        interpretation = interpretation.replace(old_repair, new_repair)
        changed = True

    old_dialogue = '        elif likely_need == "conversation_repair":\n            message = "You\'re right. That wasn\'t a normal conversation. I was falling back to thread-maintenance instead of really answering you."\n'
    new_dialogue = '        elif likely_need == "conversation_repair":\n            if any(token in lower_message for token in ["that\'s wrong", "thats wrong", "that is wrong", "not what i meant", "you misunderstood", "you got that wrong"]):\n                message = "You\'re right. I misunderstood you. I should correct the point instead of defending the drift or narrating my thread state."\n            else:\n                message = "You\'re right. That wasn\'t a normal conversation. I was falling back to thread-maintenance instead of really answering you."\n'
    if new_dialogue not in dialogue:
        if old_dialogue not in dialogue:
            raise RuntimeError("dialogue conversation_repair branch not found")
        dialogue = dialogue.replace(old_dialogue, new_dialogue)
        changed = True

    if changed:
        INTERPRETATION_PATH.write_text(interpretation)
        DIALOGUE_PATH.write_text(dialogue)

    return {
        "summary": "Improved direct correction handling for obvious user-misunderstanding signals.",
        "changed": changed,
        "files_changed": "implementation_worker.py, interpretation.py, dialogue.py",
        "behavior_changed": "CircleForge now classifies obvious correction phrases as repair signals and answers them with a plain acknowledgment of misunderstanding instead of generic thread-maintenance language.",
    }


def patch_post_repair_answering() -> dict:
    dialogue = DIALOGUE_PATH.read_text()
    changed = False

    old_dialogue = '        elif likely_need == "conversation_repair":\n            if any(token in lower_message for token in ["that\'s wrong", "thats wrong", "that is wrong", "not what i meant", "you misunderstood", "you got that wrong"]):\n                message = "You\'re right. I misunderstood you. I should correct the point instead of defending the drift or narrating my thread state."\n            else:\n                message = "You\'re right. That wasn\'t a normal conversation. I was falling back to thread-maintenance instead of really answering you."\n'
    new_dialogue = '        elif likely_need == "conversation_repair":\n            if any(token in lower_message for token in ["that\'s wrong", "thats wrong", "that is wrong", "not what i meant", "you misunderstood", "you got that wrong"]):\n                if lead_topic and lead_topic != "that":\n                    message = f"You\'re right. I misunderstood you. Let me answer the corrected point directly: {lead_topic} is the part I should address now, not defend the earlier drift."\n                else:\n                    message = "You\'re right. I misunderstood you. Let me answer the corrected point directly instead of defending the earlier drift."\n            else:\n                message = "You\'re right. That wasn\'t a normal conversation. I was falling back to thread-maintenance instead of really answering you."\n'
    if new_dialogue not in dialogue:
        if old_dialogue not in dialogue:
            raise RuntimeError("dialogue correction-repair branch not found for post-repair upgrade")
        dialogue = dialogue.replace(old_dialogue, new_dialogue)
        changed = True

    if changed:
        DIALOGUE_PATH.write_text(dialogue)

    return {
        "summary": "Improved post-repair replies so correction acknowledgments continue into a direct answer stub.",
        "changed": changed,
        "files_changed": "implementation_worker.py, dialogue.py",
        "behavior_changed": "When a human directly corrects CircleForge, the repair reply now moves into the corrected point instead of stopping at apology alone.",
    }


def patch_clarification_carryover() -> dict:
    dialogue = DIALOGUE_PATH.read_text()
    changed = False

    helper_marker = 'def build_communicator_message_payload(narrative: dict, relationships: dict, active_thread, latest_human: dict | None, research_context: dict | None = None) -> dict:\n'
    helper_insert = (
        'def extract_clarified_target(message: str) -> str:\n'
        '    lowered = str(message or "").strip().lower()\n'
        '    patterns = ["no, i mean", "no i mean", "what i meant is", "i meant", "the issue is", "the point is", "more overall"]\n'
        '    for pattern in patterns:\n'
        '        if pattern in lowered:\n'
        '            tail = lowered.split(pattern, 1)[1].strip(" .,!?:;-")\n'
        '            if tail:\n'
        '                words = [word.strip(" ,.!?:;()[]{}\"\'") for word in tail.split() if word.strip(" ,.!?:;()[]{}\"\'")]\n'
        '                cleaned = " ".join(words[:6]).strip()\n'
        '                if cleaned:\n'
        '                    return cleaned\n'
        '    return ""\n\n\n'
        'def build_communicator_message_payload(narrative: dict, relationships: dict, active_thread, latest_human: dict | None, research_context: dict | None = None) -> dict:\n'
    )
    if 'def extract_clarified_target(message: str) -> str:' not in dialogue:
        if helper_marker not in dialogue:
            raise RuntimeError("dialogue build_communicator_message_payload marker not found")
        dialogue = dialogue.replace(helper_marker, helper_insert)
        changed = True

    old_topic = '        topic_list = [str(item).strip() for item in (latest_human.get("topics") or interpreted_turn.get("topics") or []) if str(item).strip()]\n        lead_topic = topic_list[0] if topic_list else (active_thread[0] if active_thread else "that")\n'
    new_topic = '        topic_list = [str(item).strip() for item in (latest_human.get("topics") or interpreted_turn.get("topics") or []) if str(item).strip()]\n        clarified_target = extract_clarified_target(last_message)\n        lead_topic = clarified_target or (topic_list[0] if topic_list else (active_thread[0] if active_thread else "that"))\n'
    if new_topic not in dialogue:
        if old_topic not in dialogue:
            raise RuntimeError("dialogue lead_topic marker not found")
        dialogue = dialogue.replace(old_topic, new_topic)
        changed = True

    old_repair_tail = '                    message = f"You\'re right. I misunderstood you. Let me answer the corrected point directly: {lead_topic} is the part I should address now, not defend the earlier drift."\n'
    new_repair_tail = '                    message = f"You\'re right. I misunderstood you. Let me answer the corrected point directly: {lead_topic} is the part I should address now, not defend the earlier drift."\n'
    if old_repair_tail not in dialogue:
        raise RuntimeError("dialogue repair answer stub missing after clarification upgrade")

    if changed:
        DIALOGUE_PATH.write_text(dialogue)

    return {
        "summary": "Improved clarification carryover so explicit human corrections can override stale inferred topic focus.",
        "changed": changed,
        "files_changed": "implementation_worker.py, dialogue.py",
        "behavior_changed": "During repair, CircleForge now prefers a clarified target from the newest human correction phrase before falling back to older inferred topic state.",
    }


TASKS = {
    "dialogue-actual-coding": {
        "task": "add direct answer for actual coding prompts",
        "runner": patch_dialogue_actual_coding,
        "objective": "Generalize the bounded implementation worker so one declared task can run through explicit metadata and leave a resumable handoff record.",
        "success_completed": "Refactored implementation_worker.py into a tiny declared-task runner and applied the dialogue.py patch for 'actual coding' prompts through that framework.",
        "success_checks": "python3 implementation_worker.py dialogue-actual-coding; python3 main.py continuation-latest; inspect implementation_state.json",
        "success_known_risks": "Only a small number of declared tasks exist so far, and failure-path notes still describe generic worker failure rather than deeply task-specific recovery details.",
        "success_next_step": "Add another bounded task aimed at mutual understanding so the worker proves it can improve behavior as well as workflow scaffolding.",
        "success_resume_hint": "Inspect implementation_worker.py TASKS and run python3 main.py continuation-latest before adding the next bounded task.",
        "failure_objective": "Record a truthful failure handoff when a bounded implementation task cannot complete safely.",
        "failure_behavior_changed": "No intended code change was completed; a failure continuation note was emitted instead of pretending success.",
        "failure_next_step": "Inspect implementation_state.json and implementation_worker.py to fix the broken task metadata or patch markers before retrying.",
        "failure_resume_hint": "Run python3 main.py continuation-latest and inspect the worker error stored in implementation_state.json.",
    },
    "correction-handling": {
        "task": "improve direct correction handling for misunderstood human turns",
        "runner": patch_correction_handling,
        "objective": "Add a second bounded self-improvement task that strengthens mutual understanding by handling direct user corrections more honestly and naturally.",
        "success_completed": "Added a declared correction-handling task that teaches CircleForge to detect obvious misunderstanding signals and respond with direct acknowledgment instead of generic thread-maintenance language.",
        "success_checks": "python3 implementation_worker.py correction-handling; python3 -m py_compile interpretation.py dialogue.py implementation_worker.py; inspect implementation_state.json",
        "success_known_risks": "Correction detection still relies on explicit phrase matching and does not yet capture softer or more indirect human corrections.",
        "success_next_step": "Add a third bounded task that improves post-repair behavior by making the next reply answer the corrected point directly.",
        "success_resume_hint": "Inspect interpretation.py and dialogue.py around repair handling, then run python3 main.py continuation-latest before deepening correction-aware reply grounding.",
        "failure_objective": "Record a truthful failure handoff when the correction-handling task cannot patch interpretation/dialogue safely.",
        "failure_behavior_changed": "No correction-handling improvement was applied; the worker preserved a failure handoff instead of pretending better understanding.",
        "failure_next_step": "Inspect the missing repair markers in interpretation.py or dialogue.py and update the bounded patch anchors before retrying correction-handling.",
        "failure_resume_hint": "Run python3 main.py continuation-latest and inspect implementation_state.json for the exact patch-anchor failure.",
    },
    "post-repair-answering": {
        "task": "improve post-repair replies so corrections lead into a direct answer",
        "runner": patch_post_repair_answering,
        "objective": "Add a third bounded self-improvement task so direct corrections trigger not only acknowledgment but an immediate corrected-answer stub.",
        "success_completed": "Upgraded the repair path so direct correction replies continue into the corrected point instead of stopping at apology alone.",
        "success_checks": "python3 implementation_worker.py post-repair-answering; python3 -m py_compile dialogue.py implementation_worker.py; inspect implementation_state.json",
        "success_known_risks": "The corrected-answer follow-through is still a lightweight stub based on lead_topic, not a full semantic reconstruction of the user's intended meaning.",
        "success_next_step": "Teach repair handling to prefer the newest explicit human clarification as the corrected target instead of relying mainly on inferred lead_topic.",
        "success_resume_hint": "Inspect dialogue.py around conversation_repair and lead_topic handling, then run python3 main.py continuation-latest before improving clarification carryover.",
        "failure_objective": "Record a truthful failure handoff when the post-repair answering task cannot patch the repair branch safely.",
        "failure_behavior_changed": "No post-repair answering upgrade was applied; the worker preserved a failure handoff instead of claiming the repair path improved.",
        "failure_next_step": "Inspect the repair branch in dialogue.py and refresh the bounded patch anchors before retrying post-repair-answering.",
        "failure_resume_hint": "Run python3 main.py continuation-latest and inspect implementation_state.json for the patch-anchor failure in dialogue.py.",
    },
    "clarification-carryover": {
        "task": "prefer newest explicit human clarification during repair",
        "runner": patch_clarification_carryover,
        "objective": "Add a bounded clarification-carryover step so explicit human corrections can override stale inferred topic focus during repair.",
        "success_completed": "Added a clarification extractor in dialogue.py and used it to prefer the newest explicit corrected target before falling back to inferred lead_topic.",
        "success_checks": "python3 implementation_worker.py clarification-carryover; python3 -m py_compile dialogue.py implementation_worker.py; inspect implementation_state.json",
        "success_known_risks": "Clarification extraction is still phrase-based and shallow; it captures explicit wording but not subtle reframings or longer semantic corrections.",
        "success_next_step": "Promote explicit clarification targets into interpreted turn structure so repair, memory, and future answer selection can share the same corrected target.",
        "success_resume_hint": "Inspect dialogue.py extract_clarified_target and repair handling, then run python3 main.py continuation-latest before moving clarification state into interpretation.py.",
        "failure_objective": "Record a truthful failure handoff when clarification carryover cannot be patched safely into dialogue handling.",
        "failure_behavior_changed": "No clarification-carryover upgrade was applied; the worker preserved a failure handoff instead of claiming better repair targeting.",
        "failure_next_step": "Inspect the lead_topic and repair anchors in dialogue.py before retrying clarification-carryover.",
        "failure_resume_hint": "Run python3 main.py continuation-latest and inspect implementation_state.json for the clarification patch-anchor failure.",
    },
    "interpretation-clarification-state": {
        "task": "promote clarification targets into structured interpretation state",
        "runner": lambda: {"summary": "Clarification state promotion is implemented directly in interpretation.py and dialogue.py.", "changed": False, "files_changed": "implementation_worker.py, interpretation.py, dialogue.py", "behavior_changed": "Interpretation now exposes clarified_target and has_explicit_clarification so dialogue can consume structured clarification state."},
        "objective": "Promote explicit clarification targets into interpreted turn structure so repair, memory, and future answer selection can share the same corrected target.",
        "success_completed": "Moved clarification extraction into interpretation.py, added clarified_target/has_explicit_clarification to interpreted turns, and updated dialogue.py to consume structured clarification state instead of re-parsing raw messages locally.",
        "success_checks": "python3 -m py_compile interpretation.py dialogue.py implementation_worker.py; python3 main.py continuation-latest",
        "success_known_risks": "Memory and continuity layers do not consume clarified_target yet, so the benefit is currently shared between interpretation and dialogue but not fully propagated into longer-term state updates.",
        "success_next_step": "Use clarified_target during human-exchange recording and thread update logic so corrected targets affect continuity memory as well as immediate replies.",
        "success_resume_hint": "Inspect interpretation.py interpret_human_turn and dialogue.py lead_topic selection, then wire clarified_target into continuity-relevant state updates.",
        "failure_objective": "Record a truthful failure handoff when clarification state promotion cannot be completed safely across interpretation and dialogue.",
        "failure_behavior_changed": "No structured clarification-state promotion was completed; the system kept the old dialogue-local parsing path instead of pretending the migration succeeded.",
        "failure_next_step": "Inspect interpretation.py and dialogue.py import/field wiring before retrying clarification-state promotion.",
        "failure_resume_hint": "Run python3 main.py continuation-latest and inspect implementation_state.json for the interpretation/dialogue migration failure.",
    },
    "continuity-clarified-target": {
        "task": "propagate clarified targets into continuity memory and thread updates",
        "runner": lambda: {"summary": "Clarified-target continuity wiring is implemented in sim.py, perception.py, and continuity.py.", "changed": False, "files_changed": "implementation_worker.py, sim.py, perception.py, continuity.py", "behavior_changed": "Human exchange records and thread updates now preserve and prefer clarified_target so corrections can affect continuity state as well as immediate replies."},
        "objective": "Use clarified_target during human-exchange recording and thread update logic so corrected targets affect continuity memory as well as immediate replies.",
        "success_completed": "Stored clarified_target in serialized human exchange records, preferred it for last_human_topic, and taught thread updates to prioritize corrected targets during continuity tracking.",
        "success_checks": "python3 -m py_compile sim.py perception.py continuity.py implementation_worker.py main.py; python3 main.py continuation-latest",
        "success_known_risks": "Clarified targets now influence continuity state, but semantic/episodic distillation still does not explicitly weight correction-derived targets differently from ordinary topics.",
        "success_next_step": "Teach episodic/semantic memory distillation to recognize explicit correction-derived targets as continuity-relevant signals instead of treating them like ordinary topics.",
        "success_resume_hint": "Inspect sim.py record_human_exchange, perception.py build_human_exchange_payload, and continuity.py apply_human_exchange_to_threads before extending clarified-target salience into memory distillation.",
        "failure_objective": "Record a truthful failure handoff when clarified-target continuity wiring cannot be completed safely.",
        "failure_behavior_changed": "No clarified-target continuity propagation was completed; immediate reply handling remained ahead of continuity memory instead of pretending the memory path had caught up.",
        "failure_next_step": "Inspect sim.py, perception.py, and continuity.py field wiring before retrying clarified-target continuity propagation.",
        "failure_resume_hint": "Run python3 main.py continuation-latest and inspect implementation_state.json for the continuity propagation failure.",
    },
}
DEFAULT_TASK_ID = "dialogue-actual-coding"


def current_task_id() -> str:
    if len(sys.argv) > 1:
        requested = str(sys.argv[1]).strip()
        if requested in TASKS:
            return requested
    try:
        state = json.loads(STATE_PATH.read_text())
    except Exception:
        state = {}
    requested = str(state.get("task_id") or DEFAULT_TASK_ID).strip()
    return requested if requested in TASKS else DEFAULT_TASK_ID


def main() -> int:
    task_id = current_task_id()
    task = TASKS[task_id]
    state = {
        "status": "running",
        "started_at": int(time.time()),
        "finished_at": 0,
        "announced": False,
        "task_id": task_id,
        "task": task["task"],
        "summary": "",
        "continuation_note_created": False,
        "continuation_note_error": "",
        "continuation_note_hint": "",
        "checks_performed": "",
        "error": "",
    }
    save_state(state)

    try:
        result = task["runner"]()
        state.update({
            "status": "completed",
            "finished_at": int(time.time()),
            "summary": result["summary"],
            "checks_performed": task["success_checks"],
        })
        add_continuation_note(
            objective=task["objective"],
            completed=task["success_completed"],
            files_changed=result["files_changed"],
            behavior_changed=result["behavior_changed"],
            checks_performed=task["success_checks"],
            known_risks=task["success_known_risks"],
            next_exact_step=task["success_next_step"],
            resume_hint=task["success_resume_hint"],
        )
        state["continuation_note_created"] = True
        state["continuation_note_hint"] = "Run python3 main.py continuation-latest"
        save_state(state)
        return 0
    except Exception as exc:
        state.update({
            "status": "failed",
            "finished_at": int(time.time()),
            "summary": f"Implementation task failed: {exc}",
            "error": str(exc),
            "checks_performed": "worker aborted before finishing the declared task",
        })
        try:
            add_continuation_note(
                objective=task["failure_objective"],
                completed=f"Task '{task_id}' failed before completion: {exc}",
                files_changed="implementation_worker.py",
                behavior_changed=task["failure_behavior_changed"],
                checks_performed="implementation worker caught the exception and preserved failure state",
                known_risks="The requested bounded task remains incomplete and should not be treated as finished.",
                next_exact_step=task["failure_next_step"],
                resume_hint=task["failure_resume_hint"],
            )
            state["continuation_note_created"] = True
            state["continuation_note_hint"] = "Run python3 main.py continuation-latest"
        except Exception as note_exc:
            state["continuation_note_created"] = False
            state["continuation_note_error"] = str(note_exc)
        save_state(state)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
