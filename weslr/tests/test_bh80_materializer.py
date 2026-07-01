"""Tests for the BH80 scene materializer."""

import pytest
from weslr.arc_bh80_materializer import materialize_scene


class TestMaterializerBasic:
    def test_empty_scene(self):
        spec = {"grid_size": [5, 5], "background": 0, "initial_objects": []}
        grid = materialize_scene(spec)
        assert len(grid) == 5
        assert all(len(row) == 5 for row in grid)
        assert all(v == 0 for row in grid for v in row)

    def test_single_rectangle(self):
        spec = {
            "grid_size": [6, 6], "background": 0,
            "initial_objects": [
                {"object_id": "o1", "type": "rectangle", "attributes": {"color": 1, "position": [1, 1], "size": [2, 2]}},
            ],
        }
        grid = materialize_scene(spec)
        assert grid[1][1] == 1 and grid[1][2] == 1
        assert grid[2][1] == 1 and grid[2][2] == 1
        assert grid[0][0] == 0

    def test_not_default_one(self):
        """Materializer must not return [[1]] unless scene demands it."""
        spec = {"grid_size": [4, 4], "background": 0, "initial_objects": [
            {"object_id": "o1", "type": "rectangle", "attributes": {"color": 2, "position": [0, 0], "size": [1, 1]}},
        ]}
        grid = materialize_scene(spec)
        assert grid != [[1]]
        assert grid[0][0] == 2

    def test_color_name_mapping(self):
        spec = {"grid_size": [3, 3], "background": 0, "initial_objects": [
            {"object_id": "o1", "type": "rectangle", "attributes": {"color": "red", "position": [0, 0], "size": [1, 1]}},
        ]}
        grid = materialize_scene(spec)
        assert grid[0][0] == 1  # red → 1

    def test_edge_clipping(self):
        spec = {"grid_size": [3, 3], "background": 0, "initial_objects": [
            {"object_id": "o1", "type": "rectangle", "attributes": {"color": 1, "position": [2, 2], "size": [3, 3]}},
        ]}
        grid = materialize_scene(spec)
        assert grid[2][2] == 1
        assert all(grid[r][c] == 0 for r in range(3) for c in range(3) if (r, c) != (2, 2))


class TestMaterializerShapes:
    def test_l_shape(self):
        spec = {"grid_size": [5, 5], "background": 0, "initial_objects": [
            {"object_id": "o1", "type": "l_shape", "attributes": {"color": 1, "position": [0, 0]}},
        ]}
        grid = materialize_scene(spec)
        assert grid[0][0] == 1 and grid[1][0] == 1 and grid[2][0] == 1
        assert grid[2][1] == 1 and grid[2][2] == 1
        assert grid[0][1] == 0  # not part of L

    def test_cross(self):
        spec = {"grid_size": [5, 5], "background": 0, "initial_objects": [
            {"object_id": "o1", "type": "cross", "attributes": {"color": 1, "position": [0, 0]}},
        ]}
        grid = materialize_scene(spec)
        assert grid[0][1] == 1 and grid[1][0] == 1 and grid[1][1] == 1 and grid[1][2] == 1 and grid[2][1] == 1
        assert grid[0][0] == 0

    def test_donut(self):
        spec = {"grid_size": [6, 6], "background": 0, "initial_objects": [
            {"object_id": "o1", "type": "donut", "attributes": {"color": 1, "position": [1, 1], "size": [4, 4]}},
        ]}
        grid = materialize_scene(spec)
        assert grid[1][1] == 1  # border
        assert grid[2][2] == 0  # hole

    def test_disconnected(self):
        spec = {"grid_size": [5, 8], "background": 0, "initial_objects": [
            {"object_id": "o1", "type": "disconnected", "attributes": {"color": 1, "position": [0, 0], "size": [2, 4]}},
        ]}
        grid = materialize_scene(spec)
        assert grid[0][0] == 1
        assert grid[0][1] == 1  # right edge of left part (half_w=2)
        # gap at column 2-3
        assert grid[0][2] == 0
        assert grid[0][4] == 1  # right part starts at col 4

    def test_distractors(self):
        spec = {
            "grid_size": [6, 6], "background": 0,
            "initial_objects": [
                {"object_id": "o1", "type": "rectangle", "attributes": {"color": 1, "position": [0, 0], "size": [2, 2]}},
            ],
            "distractors": [
                {"object_id": "d1", "type": "rectangle", "attributes": {"color": 1, "position": [4, 4], "size": [1, 1]}},
            ],
        }
        grid = materialize_scene(spec)
        assert grid[0][0] == 1 and grid[4][4] == 1


class TestMaterializerDeterminism:
    def test_deterministic_noise(self):
        spec = {
            "grid_size": [10, 10], "background": 0,
            "initial_objects": [],
            "noise_pixels": 5,
        }
        g1 = materialize_scene(spec, "BH80_001")
        g2 = materialize_scene(spec, "BH80_001")
        assert g1 == g2  # deterministic

    def test_different_task_ids_different_noise(self):
        spec = {
            "grid_size": [10, 10], "background": 0,
            "initial_objects": [],
            "noise_pixels": 5,
        }
        g1 = materialize_scene(spec, "BH80_001")
        g2 = materialize_scene(spec, "BH80_002")
        assert g1 != g2  # different seeds

    def test_reads_scene_spec(self):
        """Prove materializer reads scene_spec, not returning defaults."""
        spec1 = {"grid_size": [3, 3], "background": 0, "initial_objects": [
            {"object_id": "o1", "type": "rectangle", "attributes": {"color": 5, "position": [0, 0], "size": [1, 1]}},
        ]}
        spec2 = {"grid_size": [5, 5], "background": 0, "initial_objects": [
            {"object_id": "o1", "type": "rectangle", "attributes": {"color": 7, "position": [2, 2], "size": [2, 2]}},
        ]}
        g1 = materialize_scene(spec1)
        g2 = materialize_scene(spec2)
        assert g1 != g2
        assert g1[0][0] == 5
        assert g2[2][2] == 7