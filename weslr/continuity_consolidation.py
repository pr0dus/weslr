from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class ConsolidationConfig:
    max_items: int = 100
    dedupe: bool = True
    drop_empty: bool = True


def consolidate(entries: List[Dict[str, Any]], config: ConsolidationConfig | None = None) -> List[Dict[str, Any]]:
    """Bounded consolidation: dedupe, drop empty, trim to max_items.

    This is a minimal runtime slice aligned to consolidation doctrine; no external IO.
    """
    cfg = config or ConsolidationConfig()
    seen = set()
    output: List[Dict[str, Any]] = []
    for entry in entries:
        if cfg.drop_empty and not entry:
            continue
        key = str(entry)
        if cfg.dedupe and key in seen:
            continue
        seen.add(key)
        output.append(entry)
        if len(output) >= cfg.max_items:
            break
    return output
