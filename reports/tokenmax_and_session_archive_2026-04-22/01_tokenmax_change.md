# Tokenmax Change — Primary Model

## Before

```json
{
  "contextWindow": 196608,
  "id": "minimax-m2.7:cloud",
  "maxTokens": 8192,
  "reasoning": true
}
```

## After

```json
{
  "contextWindow": 196608,
  "id": "minimax-m2.7:cloud",
  "maxTokens": 16384,
  "reasoning": true
}
```

## Why This Increase Is Reasonable

- Context window is 196,608 tokens — maxTokens of 8,192 was conservative (~4% of context)
- Raising to 16,384 is still conservative (~8% of context), leaves room for system prompt + context
- Reasoning models benefit from higher output ceiling during long reasoning chains
- No change to contextWindow, model family, or provider

## Why This Does NOT Solve History Growth

- maxTokens controls output ceiling, not input/context size
- The context growth issue is about unbounded session history accumulation (input side)
- This change helps the model produce longer outputs but does not reduce input context pressure
- The real fix for growth would require session compaction or history truncation, not maxTokens
