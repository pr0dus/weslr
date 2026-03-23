# CircleForge embedded models

This directory is for bundled or user-supplied embedded model files.

## Current default target

CircleForge currently expects this first embedded model by default:
- **Qwen2.5-0.5B-Instruct**
- filename:
  - `qwen2.5-0.5b-instruct.gguf`

Expected full path:
- `CircleForge/models/qwen2.5-0.5b-instruct.gguf`

## Notes

- The model is not included yet just by this scaffold.
- Once the GGUF file exists at the expected path and the embedded runtime binding is available, CircleForge can use the `embedded` provider path.
- Other model files can be used later by overriding:
  - `CIRCLEFORGE_EMBEDDED_MODEL_PATH`
  - `CIRCLEFORGE_LLM_MODEL`
