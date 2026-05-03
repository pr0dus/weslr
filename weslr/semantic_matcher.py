"""
Semantic Matcher — Entity similarity using sentence-transformer embeddings.

Doctrine P11: low-risk probabilistic assistant (local model, no external API).

Guarded import: if sentence-transformers is not installed, falls back to exact matching.
"""
from __future__ import annotations

import json
import pathlib
import os
from typing import List, Optional, Tuple

# Optional dependency — guarded
_SENTENCE_TRANSFORMERS_AVAILABLE = False
try:
    import numpy as np
    from sentence_transformers import SentenceTransformer

    _SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    np = None  # type: ignore

# Config
_ENABLED = os.environ.get("WESLR_SEMANTIC_MATCHING_ENABLED", "true").lower() in ("true", "1", "yes")
_THRESHOLD = float(os.environ.get("WESLR_SEMANTIC_THRESHOLD", "0.8"))
_AUTO_CORRECT_THRESHOLD = float(os.environ.get("WESLR_SEMANTIC_AUTO_CORRECT_THRESHOLD", "0.95"))
_MODEL_NAME = os.environ.get("WESLR_SEMANTIC_MODEL", "all-MiniLM-L6-v2")
_MATCH_LOG_PATH = ".weslr/semantic_matches.jsonl"

# Module-level model singleton (lazy)
_model: Optional["SentenceTransformer"] = None


def _get_model() -> Optional["SentenceTransformer"]:
    """Lazily load and cache the sentence-transformer model."""
    global _model
    if not _SENTENCE_TRANSFORMERS_AVAILABLE:
        return None
    if _model is None:
        try:
            _model = SentenceTransformer(_MODEL_NAME)
        except Exception:
            return None
    return _model


def is_available() -> bool:
    """True if sentence-transformers is installed and model can be loaded."""
    if not _ENABLED:
        return False
    return _get_model() is not None


def get_embedding(text: str) -> Optional["np.ndarray"]:
    """Return embedding vector for text using cached model, or None."""
    model = _get_model()
    if model is None or np is None:
        return None
    try:
        embedding = model.encode(text, normalize_embeddings=True)
        return embedding
    except Exception:
        return None


def similarity(a: str, b: str) -> float:
    """Compute cosine similarity between two strings (0.0 to 1.0)."""
    emb_a = get_embedding(a)
    emb_b = get_embedding(b)
    if emb_a is None or emb_b is None:
        return 0.0
    # Both normalized → dot product = cosine similarity
    sim = float(np.dot(emb_a, emb_b))
    return max(0.0, min(1.0, sim))


def find_similar_entity(
    query: str,
    candidate_entities: List[str],
    threshold: float = _THRESHOLD,
) -> Optional[Tuple[str, float]]:
    """Find best matching entity above threshold.

    Args:
        query: the entity name as typed by the user
        candidate_entities: list of known entity names to match against
        threshold: minimum cosine similarity to return a match

    Returns:
        (matched_name, similarity_score) if found above threshold, else None.
    """
    if not candidate_entities or not is_available():
        return None

    query_embedding = get_embedding(query)
    if query_embedding is None:
        return None

    best_name = None
    best_score = 0.0

    for name in candidate_entities:
        emb = get_embedding(name)
        if emb is None:
            continue
        score = float(np.dot(query_embedding, emb))
        if score > best_score:
            best_score = score
            best_name = name

    if best_name is not None and best_score >= threshold:
        return (best_name, round(best_score, 4))
    return None


def should_auto_correct(score: float) -> bool:
    """Return True if similarity is high enough to auto-correct without asking."""
    return score >= _AUTO_CORRECT_THRESHOLD


def log_match(query: str, matched_entity: str, score: float) -> None:
    """Append a semantic match event to the match log (append-only JSONL)."""
    if not _ENABLED:
        return
    log_path = pathlib.Path(_MATCH_LOG_PATH)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "event": "semantic_entity_match",
        "query": query,
        "matched_entity": matched_entity,
        "score": score,
        "threshold": _THRESHOLD,
    }
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def get_candidate_entities_from_fact_store(
    fact_store_path: str = ".weslr/fact_assertions.jsonl",
) -> List[str]:
    """Collect all unique entity names (subjects, objects) from fact store."""
    candidates: set = set()
    path = pathlib.Path(fact_store_path)
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                    sub = rec.get("subject", "").strip()
                    obj = rec.get("object", "").strip()
                    pred = rec.get("predicate", "").strip()
                    if sub:
                        candidates.add(sub)
                    if obj:
                        candidates.add(obj)
                    if pred:
                        candidates.add(pred)
                except json.JSONDecodeError:
                    continue
    except OSError:
        pass
    return sorted(candidates)


def get_candidate_entities_from_entity_graph(
    entity_graph_path: str = ".weslr/entity_graph.json",
) -> List[str]:
    """Collect all entity names and aliases from the entity graph."""
    candidates: set = set()
    path = pathlib.Path(entity_graph_path)
    if not path.exists():
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for entity in data.get("entities", []):
            name = entity.get("name", "").strip()
            if name:
                candidates.add(name)
            for alias in entity.get("aliases", []):
                if alias.strip():
                    candidates.add(alias.strip())
    except (OSError, json.JSONDecodeError):
        pass
    return sorted(candidates)


def match_entity(query: str) -> Optional[Tuple[str, float, bool]]:
    """Main entry point: try to match query against all known entities.

    Returns:
        (matched_name, score, auto_correct) if match found above threshold, else None.
        auto_correct=True means score >= _AUTO_CORRECT_THRESHOLD.
    """
    fact_entities = get_candidate_entities_from_fact_store()
    graph_entities = get_candidate_entities_from_entity_graph()
    all_candidates = list(set(fact_entities + graph_entities))

    result = find_similar_entity(query, all_candidates)
    if result is None:
        return None

    matched_name, score = result
    auto_correct = should_auto_correct(score)
    log_match(query, matched_name, score)
    return (matched_name, score, auto_correct)