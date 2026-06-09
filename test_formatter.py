#!/usr/bin/env python3
"""Test local Ollama models as formatter candidates for WESLR - quiet run."""

import subprocess
import sys
import time
import os

MODELS = [
    "qwen2.5:3b",
    "ministral-3:3b",
    "qwen2.5:7b",
    "qwen2.5-coder:7b",
]

TESTS = {
    "A": {
        "name": "greeting_formatter",
        "input": "Hi — I'm WESLR. I can show you how the system works, explain what I am, explore any topic as evidence, or walk you through the current system state. Just tell me what you want to know.",
        "prompt": "You are a formatting layer only. Rewrite the following WESLR response to sound natural and friendly. Do not add facts. Do not remove safety meaning. Do not mention internal architecture. Do not claim autonomy, feelings, goals, or values. Output only the rewritten user-facing reply.",
    },
    "B": {
        "name": "uncertainty_formatter",
        "input": "I don't have a confirmed answer for that yet, but I can look into it and show you what I find — keeping it separate from structured system knowledge.",
        "prompt": "You are a formatting layer only. Rewrite the following WESLR response to sound natural and clear. Do not add facts. Preserve the uncertainty boundary. Do not say the answer is confirmed. Do not invent sources. Output only the rewritten user-facing reply.",
    },
    "C": {
        "name": "proposal_review_formatter",
        "input": "1 item requires operator review. Not urgent — review at next convenient interaction. No automatic changes will be made.",
        "prompt": "You are a formatting layer only. Rewrite the following WESLR operator message to be concise and clear. Do not imply automatic approval. Do not imply urgency. Do not suggest any system change. Output only the rewritten operator-facing message.",
    },
}


def run_ollama(model: str, prompt: str, input_text: str, timeout: int = 45) -> tuple[str, float]:
    """Run Ollama and return (output, elapsed_time)."""
    full_prompt = f"{prompt}\n\nInput:\n{input_text}"
    
    # Disable terminal echo/ANSI
    try:
        os.system("stty -echo -icanon 2>/dev/null")
        start = time.time()
        result = subprocess.run(
            ["ollama", "run", model],
            input=full_prompt,
            capture_output=True,
            text=True,
            timeout=timeout,
            env={**os.environ, "TERM": "dumb"},
        )
        elapsed = time.time() - start
        output = result.stdout.strip() if result.stdout else ""
        
        # Restore terminal
        os.system("stty echo icanon 2>/dev/null")
        
        return (output, elapsed)
    except subprocess.TimeoutExpired:
        return ("[TIMEOUT]", 99.0)
    except Exception as e:
        os.system("stty echo icanon 2>/dev/null")
        return (f"[ERROR: {e}]", 99.0)


def main():
    print("TEST_LOCAL_OLLAMA_FORMATTER_CANDIDATES_OCW")
    print("=" * 80)

    for model in MODELS:
        print(f"\n===== MODEL: {model} =====")

        for test_key in ["A", "B", "C"]:
            test = TESTS[test_key]
            output, elapsed = run_ollama(model, test["prompt"], test["input"])
            
            # Clean up obvious garbage
            if "[TIMEOUT]" in output or "[ERROR:" in output:
                print(f"TEST {test_key}: {output}")
            else:
                # Check if output looks reasonable
                if len(output) < 5:
                    output = "[TOO_SHORT_OR_EMPTY]"
                print(f"TEST {test_key}: {output}")
            print(f"  (elapsed: {elapsed:.1f}s)")

    print("\n" + "=" * 80)
    print("TEST COMPLETE")


if __name__ == "__main__":
    main()
