#!/usr/bin/env python3
"""Regression tests for entity_graph import/load safety."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from entity_graph import EntityGraph


def test_entity_graph_load_fails_closed_on_invalid_json(tmp_path):
    path = tmp_path / "entity_graph.json"
    path.write_text("", encoding="utf-8")

    graph = EntityGraph.load(path)

    assert graph is not None
    assert graph.entities == {}
    assert graph.relationships == {}
    assert graph.validate_graph() is True


def test_entity_graph_load_fails_closed_on_corrupt_json(tmp_path):
    path = tmp_path / "entity_graph.json"
    path.write_text("{not valid json", encoding="utf-8")

    graph = EntityGraph.load(path)

    assert graph is not None
    assert graph.entities == {}
    assert graph.relationships == {}
    assert graph.validate_graph() is True


def test_entity_graph_load_succeeds_on_valid_json(tmp_path):
    path = tmp_path / "entity_graph.json"
    path.write_text(json.dumps({"entities": {}, "relationships": {}, "created_at": 1, "updated_at": 2, "version": "1.0", "validation_enabled": True}), encoding="utf-8")

    graph = EntityGraph.load(path)

    assert graph is not None
    assert graph.entities == {}
    assert graph.relationships == {}
    assert graph.validate_graph() is True
