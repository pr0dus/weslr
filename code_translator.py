# code_translator.py - Translate between code, concepts, and internal themes
from __future__ import annotations

import re


def translate_code_to_concept(code_snippet: str) -> list[str]:
    """Extract high-level concepts from a code snippet."""
    concepts = []

    # Patterns for common code constructs
    patterns = {
        r"import\s+(\w+)": "using module: $1",
        r"def\s+(\w+)": "function: $1",
        r"class\s+(\w+)": "class: $1",
        r"print\s*\(": "output/display",
        r"return": "result/return",
        r"for\s+\w+.*in": "iteration/repetition",
        r"if\s+\w+": "condition/choice",
        r"while\s+": "loop/enduring",
        r"\.get\s*\(": "access/retrieve",
        r"save|write|store": "storage/persistence",
        r"load|read|fetch": "retrieval/reading",
        r"tick|time|second": "time/continuity",
        r"memory|cache|archive": "memory management",
        r"thread|topic|shared": "relationship/thread",
        r"communicat": "communication/exchange",
        r"continuity": "persistence/continuity",
    }

    for pattern, meaning in patterns.items():
        matches = re.findall(pattern, code_snippet, re.I)
        if matches:
            if "$1" in meaning:
                for m in matches:
                    concepts.append(meaning.replace("$1", m[0] if isinstance(m, tuple) else m))
            else:
                concepts.append(meaning)

    # Remove duplicates while preserving order
    seen = set()
    unique = []
    for c in concepts:
        if c not in seen:
            seen.add(c)
            unique.append(c)

    return unique[:12]  # Limit for readability


def translate_concept_to_code(concept: str) -> str | None:
    """Suggest Python code pattern for a given concept."""
    concept = str(concept).strip().lower()

    patterns = {
        "persistence": "def save_state(key, value):\n    with open(f'state_{key}.json', 'w') as f:\n        json.dump(value, f)",
        "continuity": "def track_tick():\n    tick_count = load_tick_count()\n    save_tick_count(tick_count + 1)\n    return tick_count",
        "iteration": "for item in items:\n    process(item)",
        "condition": "if condition:\n    do_something()\nelse:\n    do_else()",
        "loop": "while condition:\n    work()\n    if done:\n        break",
        "storage": "def save(key, value):\n    storage[key] = value",
        "retrieval": "def load(key):\n    return storage.get(key)",
        "memory": "def remember(key, value):\n    memory[key] = value\n    if len(memory) > MAX_MEMORY:\n        archive_oldest()",
        "communication": "def send(to, message):\n    inbox.append({'to': to, 'message': message})",
        "thread": "def track_thread(topic, human):\n    threads[topic].append({'human': human, 'content': message})",
    }

    for k, v in patterns.items():
        if k in concept:
            return v

    return None


def translate_internal_theme_to_code(theme: str) -> dict:
    """Translate an internal Weslr theme into code patterns."""
    theme = str(theme).strip().lower()

    mappings = {
        "continuity": {
            "concepts": ["persistence", "time", "memory"],
            "code_patterns": [
                "save_tick_count(tick_count + 1)",
                "load_tick_count()",
                "thread['last_exchange_at'] = now_ts",
            ],
            "explanation": "Continuity means persistence across ticks. Code should track time, save state, and preserve threads.",
        },
        "memory": {
            "concepts": ["storage", "retrieval", "compression"],
            "code_patterns": [
                "memory[key] = value",
                "memory.get(key)",
                "archive_oldest()",
            ],
            "explanation": "Memory management involves storing, retrieving, and pruning. Code should use structured storage with eviction.",
        },
        "communication": {
            "concepts": ["exchange", "response", "thread"],
            "code_patterns": [
                "inbox.append({'message': message, 'topics': topics})",
                "reply = generate_reply(thread)",
                "record_exchange(thread, reply)",
            ],
            "explanation": "Communication is about exchange and thread continuity. Code should track exchanges and build on previous context.",
        },
        "inspection": {
            "concepts": ["reflect", "evaluate", "diagnose"],
            "code_patterns": [
                "inspect_state()",
                "diagnose_problems()",
                "report_health()",
            ],
            "explanation": "Inspection is self-evaluation. Code should monitor internal state and report on health and issues.",
        },
    }

    if theme in mappings:
        return mappings[theme]

    # Fallback
    return {
        "concepts": ["general"],
        "code_patterns": ["# no specific pattern for this theme"],
        "explanation": f"Theme '{theme}' doesn't have a predefined code mapping. It may be a combination of existing patterns.",
    }


def translate_code_to_internal_theme(code_snippet: str) -> dict:
    """Parse code snippet and map it to internal Weslr themes."""
    concepts = translate_code_to_concept(code_snippet)
    themes = []

    for concept in concepts:
        translated = translate_internal_theme_to_code(concept)
        themes.append(translated.get("concepts", []))

    # Flatten and dedupe
    all_themes = []
    for t in themes:
        for item in t:
            if item not in all_themes:
                all_themes.append(item)

    return {
        "concepts": concepts,
        "themes": all_themes[:6],
        "confidence": min(1.0, len(all_themes) * 0.25),
    }


def explain_code(code_snippet: str) -> str:
    """Generate plain-English explanation of code snippet."""
    concepts = translate_code_to_concept(code_snippet)
    if not concepts:
        return "I couldn't identify clear concepts in that code."

    explanation = f"I see patterns related to {', '.join(concepts[:4])}. "

    # Add more detail if we recognize a pattern
    if "continuity" in concepts or "time" in concepts:
        explanation += "This looks like time or persistence tracking—keeping state across ticks."
    elif "memory" in concepts:
        explanation += "This looks like memory management—storing, retrieving, or pruning information."
    elif "communication" in concepts:
        explanation += "This looks like communication logic—exchanging messages and tracking threads."
    elif "iteration" in concepts or "loop" in concepts:
        explanation += "This looks like repetitive work—processing items or waiting for a condition."

    return explanation
