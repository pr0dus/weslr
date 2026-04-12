from __future__ import annotations
import json
from pathlib import Path
from typing import List, Dict

TRANSCRIPT_DIR = Path("transcripts")
TRANSCRIPT_DIR.mkdir(exist_ok=True)

WEAK_PATTERNS = [
    "uncertain",
    "anxiety",
    "distress",
    "unresolved",
    "no content returned",
]


def review_transcript(src_path: Path, out_suffix: str = "review") -> Path:
    persona = src_path.stem.replace("pilot_", "")
    out = TRANSCRIPT_DIR / f"{out_suffix}_{persona}.txt"
    lines: List[str] = [f"Persona: {persona}\n"]
    with src_path.open("r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            rec = json.loads(line)
            user = rec.get("user_input")
            resp = rec.get("response_content") or ""
            notes: List[str] = []
            low_conf = any(pat in resp.lower() for pat in WEAK_PATTERNS)
            if low_conf:
                notes.append("weak relevance/low-confidence language detected")
            if "plan" in resp.lower() and "lesson" not in user.lower() and "plan" not in user.lower():
                notes.append("generic plan response unrelated to user context")
            lines.append(f"Exchange {idx+1}")
            lines.append(f"User: {user}")
            lines.append(f"WESLR: {resp}")
            if notes:
                lines.append("Self-review:")
                for n in notes:
                    lines.append(f"- {n}")
            lines.append("")
    out.write_text("\n".join(lines), encoding="utf-8")
    return out


def run_reviews():
    outputs = []
    for src in TRANSCRIPT_DIR.glob("pilot_*.jsonl"):
        outputs.append(review_transcript(src))
    return outputs

if __name__ == "__main__":
    outs = run_reviews()
    print("reviewed", [str(p) for p in outs])
