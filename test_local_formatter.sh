#!/bin/bash
# Test local Ollama models as formatter candidates for WESLR
# Only models that fit in RAM (avoid 4b+ which OOM)

MODELS="qwen2.5:3b ministral-3:3b qwen2.5:7b qwen2.5-coder:7b"

# Clean output helper - strip ANSI codes and trim
clean() {
    sed 's/\x1b\[[0-9;]*[A-Za-z]//g' | sed 's/^[[:space:]]*//;s/[[:space:]]*$//'
}

for MODEL in $MODELS; do
    echo "===== MODEL: $MODEL ====="

    # TEST A - greeting
    echo "--- TEST A (greeting) ---"
    timeout 40 ollama run "$MODEL" 'You are a formatting layer only. Rewrite the following WESLR response to sound natural and friendly. Do not add facts. Do not remove safety meaning. Do not mention internal architecture. Do not claim autonomy, feelings, goals, or values. Output only the rewritten user-facing reply.

Hi — I'"'"'m WESLR. I can show you how the system works, explain what I am, explore any topic as evidence, or walk you through the current system state. Just tell me what you want to know.' 2>&1 | grep -v "\[?" | head -5

    # TEST B - uncertainty
    echo "--- TEST B (uncertainty) ---"
    timeout 40 ollama run "$MODEL" 'You are a formatting layer only. Rewrite the following WESLR response to sound natural and clear. Do not add facts. Preserve the uncertainty boundary. Do not say the answer is confirmed. Do not invent sources. Output only the rewritten user-facing reply.

I don'"'"'t have a confirmed answer for that yet, but I can look into it and show you what I find — keeping it separate from structured system knowledge.' 2>&1 | grep -v "\[?" | head -5

    # TEST C - proposal review
    echo "--- TEST C (proposal review) ---"
    timeout 40 ollama run "$MODEL" 'You are a formatting layer only. Rewrite the following WESLR operator message to be concise and clear. Do not imply automatic approval. Do not imply urgency. Do not suggest any system change. Output only the rewritten operator-facing message.

1 item requires operator review. Not urgent — review at next convenient interaction. No automatic changes will be made.' 2>&1 | grep -v "\[?" | head -5

    echo ""
done
