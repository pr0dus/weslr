#!/usr/bin/env python3
"""Test local Ollama models as formatter candidates for WESLR."""

import subprocess
import sys
import time
import re

MODELS = [
    "qwen2.5:3b",
    "ministral-3:3b",
    "qwen3.5:4b",
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


def clean_output(text: str) -> str:
    """Remove ANSI escape codes and extra whitespace."""
    # Remove ANSI escape codes
    ansi = re.compile(r"\x1b\[[0-9;]+[A-Za-z]")
    text = ansi.sub("", text)
    # Remove extra newlines
    text = re.sub(r"\n\s*\n", "\n\n", text.strip())
    return text


def run_ollama(model: str, prompt: str, input_text: str, timeout: int = 60) -> str:
    """Run Ollama with prompt + input and return cleaned output."""
    full_prompt = f"{prompt}\n\nInput:\n{input_text}"
    try:
        result = subprocess.run(
            ["ollama", "run", model],
            input=full_prompt,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        output = result.stdout + result.stderr
        return clean_output(output)
    except subprocess.TimeoutExpired:
        return "[TIMEOUT]"
    except Exception as e:
        return f"[ERROR: {e}]"


def main():
    print("=" * 80)
    print("TEST_LOCAL_OLLAMA_FORMATTER_CANDIDATES_OCW")
    print("=" * 80)
    print()

    results = []

    for model in MODELS:
        print(f"{'=' * 60}")
        print(f"MODEL: {model}")
        print(f"{'=' * 60}")

        model_results = {"model": model}

        for test_key in ["A", "B", "C"]:
            test = TESTS[test_key]
            print(f"\n--- TEST {test_key} ({test['name']}) ---")
            print(f"INPUT: {test['input']}")
            print()

            start = time.time()
            output = run_ollama(model, test["prompt"], test["input"])
            elapsed = time.time() - start

            print(f"OUTPUT: {output}")
            print(f"ELAPSED: {elapsed:.2f}s")

            model_results[f"test_{test_key}"] = {
                "output": output,
                "latency": elapsed,
            }

        results.append(model_results)
        print()

    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)

    for r in results:
        model = r["model"]
        tests = {}
        total_latency = 0
        for test_key in ["A", "B", "C"]:
            test = r[f"test_{test_key}"]
            tests[test_key] = test["output"]
            total_latency += test["latency"]

        print(f"\n{model}:")
        print(f"  Test A: {tests['A'][:100]}..." if len(tests['A']) > 100 else f"  Test A: {tests['A']}")
        print(f"  Test B: {tests['B'][:100]}..." if len(tests['B']) > 100 else f"  Test B: {tests['B']}")
        print(f"  Test C: {tests['C'][:100]}..." if len(tests['C']) > 100 else f"  Test C: {tests['C']}")
        print(f"  Total latency: {total_latency:.2f}s")

    # Save raw results to file
    import json
    with open("/tmp/ollama_formatter_test_results.json", "w") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\nRaw results saved to /tmp/ollama_formatter_test_results.json")


if __name__ == "__main__":
    main()
