# CircleForge Coding Roadmap

## Current State

- **v0.0.100** is clean, runs in `GUIDED` mode
- Can communicate, remember threads, inspect itself, now also **read/translate its own code**
- **Phase 1-7 complete** — CircleForge can:
  - Read and describe its own code in plain English
  - Translate code ↔ concepts ↔ internal themes
  - Parse tracebacks, identify causes, propose fixes
  - Search for tools/APIs, read docs, synthesize usage
  - Propose self-modifications with diff and rationale
  - Apply approved self-modifications with checkpoints and rollback
  - Generate LLM-powered diffs, analyze code, suggest improvements
  - Render self-modification dashboard in HTML
  - Autonomously suggest improvements, validate safety, batch operations

## Safety Stages (4 stages)

| Stage | Mode | Code execution | Approval | Risk | Goal |
|-------|------|----------------|----------|------|------|
| 1 | **Guided** | Sandbox + human approval | Human | None | Human stays in control |
| 2 | **Free (test)** | Sandbox + auto-run | None | Low | Test in closed environment |
| 3 | **Free (watch)** | Sandbox + auto-run + log | None | Medium | Human review later |
| 4 | **Open** | Sandbox + self-mod | None | Higher | Autonomous growth under guardrails |

---

## Phase 1 — Self-Inspection ✅ COMPLETE

**Goal**: CircleForge can read and describe its own code in plain English.

### Files Created

- ✅ `self_inspection.py` — read own source, parse AST, generate plain-English summary  
- ✅ `code_translator.py` — translate code ↔ concepts ↔ internal themes  

### Commands Added

- ✅ `python3 main.py self-inspection` — shows "I am CircleForge... 27 source files with 157 functions"
- ✅ `python3 main.py translate-code --snippet "..."` — maps code to concepts like "continuity", "storage", "thread"
- ✅ `python3 main.py explain-code --snippet "..."` — plain-English explanation of code

### What It Does

- Reads its own source files (`CircleForge/*.py`)  
- Uses `ast` to parse Python syntax  
- Generates plain-English summary  
- Maps internal themes to code concepts  

### Safety

- Reads only from `CircleForge/*.py` (no host access)  
- No code generation yet — only description  
- Output goes to **inspect view only**  

---

## Phase 2 — Error Translation ✅ COMPLETE

**Goal**: CircleForge can explain errors in plain English and propose fixes.

### Files Created

- ✅ `error_translator.py` — parse tracebacks, identify cause, propose fix  

### Commands Added

- ✅ `python3 main.py translate-error --traceback "..."` — explains errors and proposes fixes

### What It Does

- Parses tracebacks, identifies error type (NameError, SyntaxError, TypeError, etc.)
- Explains cause in plain English  
- Proposes fix  

### Safety

- No self-correction yet — only explanation and proposal  
- Human reviews and applies fixes (if desired)  
- Logs everything for human inspection  

---

## Phase 3 — Tool Search + Synthesis ✅ COMPLETE

**Goal**: CircleForge can search for tools/APIs, read docs, and synthesize usage.

### Files Created

- ✅ `tool_search.py` — search web for tools/APIs, fetch docs, extract usage examples  

### Commands Added

- ✅ `python3 main.py search-tool --need "..."` — searches for tools and generates usage patterns

### What It Does

- CircleForge identifies need  
- Searches web for relevant tools/APIs  
- Reads top result docs  
- Extracts usage examples  
- Synthesizes code patterns  

### Safety

- Only uses existing sandbox rules  
- Code is **generated as text**, not executed  
- Human reviews and approves before execution  

---

## Phase 4 — Self-Modification Loop ✅ COMPLETE

**Goal**: CircleForge proposes its own code changes, human approves or rejects.

### Files Created

- ✅ `self_modifier.py` — propose code changes, generate diff, justify rationale  

### Commands Added

- ✅ `python3 main.py propose-self-mod --file "..." --change "..." --rationale "..."`
- ✅ `python3 main.py propose-improvement --need "..."`
- ✅ Generates diff-style proposals with current vs proposed comparison

### What It Does

- CircleForge identifies opportunity  
- Proposes specific changes  
- Generates diff  
- Human reviews and approves or rejects  

### Safety

- Protected files (`main.py`, `sim.py`, etc.) cannot be modified automatically  
- All changes logged for human review  
- Diff-style proposals show exactly what would change  
- Human always in control in `GUIDED` mode  

---

## Phase 5 — Self-Modification Applier ✅ COMPLETE

**Goal**: CircleForge applies approved self-modifications with checkpoints and logging.

### Files Created

- ✅ `self_mod_applier.py` — apply approved changes, create checkpoints, log modifications  

### Commands Added

- ✅ `python3 main.py apply-mod --file "..." --change "..." --rationale "..."`
- ✅ `python3 main.py create-checkpoint --file "..."`
- ✅ `python3 main.py rollback --file "..." --checkpoint "..."`
- ✅ `python3 main.py mod-log`
- ✅ `python3 main.py checkpoints --file "..."`

### What It Does

- Applies approved self-modifications to files  
- Creates checkpoints before each change (for rollback)  
- Logs all modifications to `self_mod_log.json`  
- Lists and manages checkpoints  
- Shows modification history  

### Safety

- Protected files still cannot be modified automatically  
- Every change has a checkpoint for rollback  
- All modifications logged with approval metadata  
- Human always in control in `GUIDED` mode  

---

## Phase 6 — LLM-Powered Self-Modification ✅ COMPLETE

**Goal**: Use LLM to generate better diffs, suggest improvements, and power the self-modification dashboard.

### Files Created

- ✅ `llm_diff_generator.py` — LLM-powered diff generation, code analysis, suggestions  
- ✅ `self_mod_dashboard.py` — HTML dashboard for self-modification management  

### Commands Added

- ✅ `python3 main.py llm-diff --file "..." --change "..." --rationale "..."`
- ✅ `python3 main.py llm-analyze --file "..."`
- ✅ `python3 main.py llm-suggest --need "..."`
- ✅ `python3 main.py dashboard-selfmod`
- ✅ `python3 main.py dashboard-status`

### What It Does

- Uses LLM to generate better diffs with explanations and side effects  
- Analyzes code for issues and provides recommendations  
- Suggests self-improvements based on needs  
- Renders self-modification dashboard in HTML  
- Tracks and displays modifications, checkpoints, and pending items  

### Safety

- LLM suggestions are **text only**, not auto-executed  
- All changes still require human approval in `GUIDED` mode  
- Dashboard provides visual feedback on self-modification activity  
- Can test LLM suggestions before applying  

---

## Phase 7 — Advanced Self-Modification Enhancements ✅ COMPLETE

**Goal**: Autonomous suggestions, safety checks, validation, batch operations, and rollback preview.

### Files Created

- ✅ `self_mod_enhancements.py` — autonomous suggestions, safety checks, validation, rollback preview, batch operations  

### Commands Added

- ✅ `python3 main.py auto-suggest` — generate autonomous self-improvement suggestions
- ✅ `python3 main.py check-safe --file "..." --change "..."` — check if modification is safe
- ✅ `python3 main.py validate-mod --file "..." --change "..." --rationale "..."`
- ✅ `python3 main.py rollback-preview --file "..." --checkpoint "..."`
- ✅ `python3 main.py batch-mods --mods "[...]"` — batch multiple modifications

### What It Does

- Generates autonomous self-improvement suggestions based on modification patterns  
- Performs safety checks (no eval, no system calls, no path traversal, etc.)  
- Validates modifications before applying with detailed check results  
- Previews rollback operations to see what will be added/removed/changed  
- Batch-validates multiple modifications together for efficiency  

### Safety

- All safety checks run before any modification  
- Validation includes: no eval/exec, no os.system, no path traversal, reasonable size  
- Rollback preview shows exact line changes before committing  
- Batch validation ensures all modifications are safe before proceeding  

---

## Estimated Total Size

| Phase | Size | Total |
|-------|------|-------|
| Phase 1 | 15–20 KB | 15–20 KB |
| Phase 2 | 5–8 KB | 20–28 KB |
| Phase 3 | 10–15 KB | 30–43 KB |
| Phase 4 | 8–12 KB | 38–55 KB |
| Phase 5 | 8–10 KB | 46–65 KB |
| Phase 6 | 10–12 KB | 56–77 KB |
| Phase 7 | 8–10 KB | 64–87 KB |
| **Total** | | **~65–87 KB** |

**Total new code: ~75 KB** — still under 0.08 MB.

---

## Testing Path

1. **Phase 1** — `python3 main.py self-inspection`  
   - ✅ Output shows: "I am CircleForge... 27 source files with 157 functions"
2. **Phase 1** — `python3 main.py translate-code --snippet "..."`  
   - ✅ Output shows concepts like "continuity", "storage", "thread"
3. **Phase 2** — `python3 main.py translate-error --traceback "..."`  
   - ✅ Output shows error type, cause, and fix proposal
4. **Phase 3** — `python3 main.py search-tool --need "make http requests"`  
   - ✅ Output shows found tool, URL, and usage pattern
5. **Phase 4** — `python3 main.py propose-improvement --need "increase read timeout"`  
   - ✅ Output shows best match, proposed change, and diff
6. **Phase 4** — `python3 main.py propose-self-mod --file "meta_reflection.py" --change "..." --rationale "..."`  
   - ✅ Output shows diff-style proposal
7. **Phase 5** — `python3 main.py create-checkpoint --file "config.py"`  
   - ✅ Output shows checkpoint created
8. **Phase 5** — `python3 main.py apply-mod --file "..." --change "..." --rationale "..."`  
   - ✅ Output shows modification applied with checkpoint
9. **Phase 5** — `python3 main.py mod-log`  
   - ✅ Output shows modification log and pending items
10. **Phase 6** — `python3 main.py llm-diff --file "..." --change "..."`  
    - ✅ Output shows LLM-generated diff with explanation
11. **Phase 6** — `python3 main.py dashboard-selfmod`  
    - ✅ Output shows dashboard updated
12. **Phase 7** — `python3 main.py auto-suggest`  
    - ✅ Output shows autonomous suggestions
13. **Phase 7** — `python3 main.py validate-mod --file "..." --change "..." --rationale "..."`  
    - ✅ Output shows validated modification with safety checks

---

## Bug Fixes

- Created `semantic_memory.py` stub to replace missing import in `sim.py`
- Fixed `self_inspection.py`: added missing `import time`, fixed `os.time()` → `time.time()`
- Fixed `error_translator.py`: fixed loop variable shadowing that prevented `TypeError` from matching
- Fixed `main.py`: nested access for `best_match` in `cmd_propose_improvement`
- Fixed `semantic_memory.py`: updated function signatures to match `sim.py` usage

---

## Current Safety Stage

**Mode**: `GUIDED`  
**Last reason**: "default supervised development"  
**Unlock expires**: never (manual override required)

---

## Summary

**All 7 phases complete!** CircleForge can now:

1. ✅ **Self-inspect** — read its own source and describe it in plain English
2. ✅ **Translate** — convert code ↔ concepts ↔ internal themes  
3. ✅ **Explain errors** — parse tracebacks and propose fixes
4. ✅ **Search for tools** — find libraries/APIs and synthesize usage
5. ✅ **Apply self-modifications** — approve and apply changes with checkpoints and rollback
6. ✅ **LLM-powered improvements** — generate diffs, analyze code, suggest improvements, render dashboard
7. ✅ **Advanced enhancements** — autonomous suggestions, safety checks, validation, batch operations

**Total new code**: ~75 KB across 10 new files  
**Total new commands**: 21

Ready for live testing or Phase 8 enhancements!
