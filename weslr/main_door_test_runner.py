from __future__ import annotations
import json
import time
from pathlib import Path
from typing import List, Dict, Any

from weslr.ingress_adapter import route_request

TRANSCRIPT_DIR = Path("transcripts")
TRANSCRIPT_DIR.mkdir(exist_ok=True)


def run_persona(persona: Dict[str, Any], exchanges: int = 5, run_id: str = "pilot"):
    persona_id = persona["id"]
    prompts: List[str] = persona.get("prompts", [])
    out_path = TRANSCRIPT_DIR / f"{run_id}_{persona_id}.jsonl"
    records = []
    for idx in range(min(exchanges, len(prompts))):
        user_input = prompts[idx]
        ts = time.time()
        resp = route_request({
            "message": user_input,
            "persona": persona.get("label", persona_id),
            "domain": persona.get("domain", "general"),
        })
        record = {
            "persona_id": persona_id,
            "persona_summary": persona.get("summary"),
            "exchange_index": idx,
            "timestamp": ts,
            "user_input": user_input,
            "response_content": resp.content,
            "response_metadata": resp.metadata,
        }
        records.append(record)
    with out_path.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return records


def run_pilot():
    personas = [
        {
            "id": "engineer_mid",
            "label": "engineer",
            "summary": "Mid-level software engineer, concise, task-focused",
            "domain": "technical",
            "prompts": [
                "Hey, I need to debug a failing unit test in a Python service.",
                "It fails only on CI, not locally. Any quick checks?",
                "We use pytest; logs show a timeout on a network call.",
                "Should I mock the network dependency?",
                "Can you summarize the steps I should try first?",
            ],
        },
        {
            "id": "teacher_supportive",
            "label": "teacher",
            "summary": "High school teacher, supportive tone, planning a lesson",
            "domain": "education",
            "prompts": [
                "Hi, I’m planning a lesson on photosynthesis for 10th graders.",
                "Need a simple analogy to explain light-dependent reactions.",
                "Any quick in-class activity that fits 15 minutes?",
                "How do I assess understanding quickly at the end?",
                "Summarize the plan in two sentences, please.",
            ],
        },
    ]
    all_records = []
    for p in personas:
        all_records.extend(run_persona(p, exchanges=5, run_id="pilot"))
    return all_records


if __name__ == "__main__":
    run_pilot()
