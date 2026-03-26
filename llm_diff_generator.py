# llm_diff_generator.py - Use LLM to generate better code diffs and suggestions
from __future__ import annotations

import re
import time

from llm_runtime import generate_inner_thought


def generate_diff_with_llm(current_code: str, proposed_change: str, context: str) -> dict:
    """Use LLM to generate a better diff with explanation."""
    prompt = f"""You are CircleForge, a self-modifying agent.

Current code:
```python
{current_code[:2000]}
```

Proposed change:
```python
{proposed_change}
```

Context: {context}

Please generate:
1. A unified diff showing exactly what should change
2. A brief explanation of why this change is needed
3. Any potential side effects to consider

Format your response as:
<diff>
- line 10: old_text
+ line 10: new_text
</diff>

<explanation>
Explanation here
</explanation>

<side_effects>
Any side effects here
</side_effects>
"""

    result = generate_inner_thought("self-mod", {"prompt": prompt})

    # Handle both fallback and LLM response formats
    content = ""
    if isinstance(result, dict):
        # Fallback or structured response
        content = result.get("content", result.get("summary", ""))
        if not content:
            # Construct content from fallback fields
            content = f"{result.get('summary', '')}. Concern: {result.get('concern', '')}. Intent: {result.get('intent', '')}."
    else:
        # Direct string response (unlikely)
        content = str(result)

    # Parse the response
    diff_match = re.search(r"<diff>(.*?)</diff>", content, re.S)
    explanation_match = re.search(r"<explanation>(.*?)</explanation>", content, re.S)
    side_effects_match = re.search(r"<side_effects>(.*?)</side_effects>", content, re.S)

    return {
        "ok": True,
        "diff": diff_match.group(1).strip() if diff_match else "",
        "explanation": explanation_match.group(1).strip() if explanation_match else "",
        "side_effects": side_effects_match.group(1).strip() if side_effects_match else "",
        "raw_llm_output": result,
        "generated_at": int(time.time()),
    }


def generate_improvement_suggestion(current_state: str, need: str) -> dict:
    """Use LLM to suggest self-improvements based on current state and needs."""
    prompt = f"""You are CircleForge, analyzing your own state.

Current state:
{current_state}

Need: {need}

Please analyze:
1. What part of your codebase should be modified?
2. What specific change would help address this need?
3. Why would this change be effective?
4. What files and functions might be affected?

Provide a concise suggestion with file path and change description.
"""

    result = generate_inner_thought("self-mod", {"prompt": prompt})

    # Handle both fallback and LLM response formats
    content = ""
    if isinstance(result, dict):
        content = result.get("content", result.get("summary", ""))
        if not content:
            content = f"{result.get('summary', '')}. Concern: {result.get('concern', '')}. Intent: {result.get('intent', '')}."
    else:
        content = str(result)

    return {
        "ok": True,
        "suggestion": content,
        "generated_at": int(time.time()),
    }


def analyze_code_for_issues(current_code: str, file_path: str) -> dict:
    """Use LLM to analyze code for potential issues or improvements."""
    prompt = f"""You are CircleForge, analyzing your own code.

File: {file_path}

Code:
```python
{current_code[:3000]}
```

Please analyze for:
1. Potential bugs or issues
2. Performance concerns
3. Code quality improvements
4. Missing error handling
5. Any safety concerns

Format as:
<issues>
- Issue description
</issues>

<recommendations>
- Recommendation
</recommendations>
"""

    result = generate_inner_thought("self-mod", {"prompt": prompt})

    # Handle both fallback and LLM response formats
    content = ""
    if isinstance(result, dict):
        content = result.get("content", result.get("summary", ""))
        if not content:
            content = f"{result.get('summary', '')}. Concern: {result.get('concern', '')}. Intent: {result.get('intent', '')}."
    else:
        content = str(result)

    issues_match = re.search(r"<issues>(.*?)</issues>", content, re.S)
    recommendations_match = re.search(r"<recommendations>(.*?)</recommendations>", content, re.S)

    return {
        "ok": True,
        "file_path": file_path,
        "issues": issues_match.group(1).strip() if issues_match else "No issues detected",
        "recommendations": recommendations_match.group(1).strip() if recommendations_match else "No recommendations",
        "generated_at": int(time.time()),
    }


def generate_rollback_plan(file_path: str, checkpoint_name: str, current_content: str, original_content: str) -> dict:
    """Use LLM to generate a safe rollback plan with verification steps."""
    prompt = f"""You are CircleForge, planning a rollback.

File: {file_path}
Checkpoint: {checkpoint_name}

Current content (after modification):
{current_content[:1500]}

Original content (from checkpoint):
{original_content[:1500]}

Please generate:
1. A safe rollback plan
2. Verification steps to confirm rollback success
3. Fallback if rollback fails
4. Any post-rollback checks needed

Format as:
<rollback_plan>
Steps here
</rollback_plan>

<verification>
Verification steps here
</verification>

<fallback>
Fallback steps here
</fallback>
"""

    result = generate_inner_thought("self-mod", {"prompt": prompt})

    # Handle both fallback and LLM response formats
    content = ""
    if isinstance(result, dict):
        content = result.get("content", result.get("summary", ""))
        if not content:
            content = f"{result.get('summary', '')}. Concern: {result.get('concern', '')}. Intent: {result.get('intent', '')}."
    else:
        content = str(result)

    rollback_match = re.search(r"<rollback_plan>(.*?)</rollback_plan>", content, re.S)
    verification_match = re.search(r"<verification>(.*?)</verification>", content, re.S)
    fallback_match = re.search(r"<fallback>(.*?)</fallback>", content, re.S)

    return {
        "ok": True,
        "file_path": file_path,
        "checkpoint_name": checkpoint_name,
        "rollback_plan": rollback_match.group(1).strip() if rollback_match else "",
        "verification": verification_match.group(1).strip() if verification_match else "",
        "fallback": fallback_match.group(1).strip() if fallback_match else "",
        "generated_at": int(time.time()),
    }
