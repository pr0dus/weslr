"""Tests for the BH80 independent oracle."""

import pytest
from weslr.arc_bh80_oracle import reference_primitive, run_oracle_pipeline
from weslr.arc_bh80_materializer import materialize_scene

# Import solver dispatch to prove oracle does NOT use it
import weslr.arc_synthetic_3_step_real_dispatch as disp


class TestOracleIndependence:
    def test_oracle_module_does_not_import_solver_dispatch(self):
        """Static check: oracle module must not import run_primitive."""
        import weslr.arc_bh80_oracle as oracle_mod
        mod_source = open(oracle_mod.__file__).read()
        # The oracle may mention these strings in comments/asserts but must not CALL them
        assert "from weslr.arc_synthetic_3_step_real_dispatch import" not in mod_source
        assert "import weslr.arc_synthetic_3_step_real_dispatch" not in mod_source

    def test_oracle_does_not_call_run_primitive(self):
        """Dynamic check: monkey-patch run_primitive to raise, oracle should still work."""
        original = disp.run_primitive
        def bomb(*args, **kwargs):
            raise RuntimeError("Oracle called solver dispatch — FORBIDDEN")
        disp.run_primitive = bomb
        try:
            grid = [[0, 1, 0], [1, 1, 1], [0, 1, 0]]
            supported, out, trace = reference_primitive("extract", grid)
            assert supported
        finally:
            disp.run_primitive = original


class TestOraclePrimitives:
    def test_extract(self):
        grid = [[0, 0, 0, 0], [0, 1, 1, 0], [0, 1, 1, 0], [0, 0, 0, 0]]
        supported, out, trace = reference_primitive("extract", grid)
        assert supported
        assert out == [[1, 1], [1, 1]]

    def test_mirror_object(self):
        grid = [[1, 0, 0], [0, 0, 0]]
        supported, out, _ = reference_primitive("mirror_object", grid)
        assert supported
        assert out == [[0, 0, 1], [0, 0, 0]]

    def test_rotate(self):
        grid = [[1, 0], [0, 0]]
        supported, out, _ = reference_primitive("rotate", grid)
        assert supported
        assert out == [[0, 1], [0, 0]]

    def test_crop(self):
        grid = [[0, 0, 0, 0], [0, 1, 1, 0], [0, 1, 1, 0], [0, 0, 0, 0]]
        supported, out, _ = reference_primitive("crop", grid)
        assert supported
        assert out == [[1, 1], [1, 1]]

    def test_recolor(self):
        grid = [[0, 1, 0], [0, 0, 0]]
        supported, out, _ = reference_primitive("recolor", grid)
        assert supported
        assert out == [[0, 2, 0], [0, 0, 0]]

    def test_fill_region(self):
        grid = [[0, 0], [0, 0]]
        supported, out, _ = reference_primitive("fill_region", grid)
        assert supported
        assert out == [[1, 1], [1, 1]]

    def test_isolate_largest(self):
        grid = [[0, 1, 0, 0], [0, 1, 0, 0], [0, 1, 0, 2]]
        supported, out, _ = reference_primitive("isolate_largest", grid)
        assert supported
        # Largest component is the 3-cell vertical at column 1
        assert out[0][1] == 1 and out[1][1] == 1 and out[2][1] == 1
        assert out[2][3] == 0  # smaller component removed

    def test_transform(self):
        grid = [[1, 0], [0, 0]]
        supported, out, _ = reference_primitive("transform", grid)
        assert supported
        assert out == [[0, 0], [1, 0]]  # vertical flip

    def test_remove_noise(self):
        grid = [[0, 1, 0], [0, 0, 0], [0, 0, 1]]
        supported, out, _ = reference_primitive("remove_noise", grid)
        assert supported
        assert out[0][1] == 0  # isolated pixel removed
        assert out[2][2] == 0  # isolated pixel removed

    def test_count_objects(self):
        grid = [[1, 0, 0], [0, 0, 2], [0, 0, 2]]
        supported, out, trace = reference_primitive("count_objects", grid)
        assert supported
        assert trace["count"] == 2  # two components

    def test_unsupported_primitive(self):
        grid = [[1, 0], [0, 0]]
        supported, out, trace = reference_primitive("fake_primitive", grid)
        assert not supported
        assert "not implemented" in trace.get("unsupported_reason", "")


class TestOraclePipeline:
    def test_full_pipeline(self):
        grid = [[0, 0, 0, 0], [0, 1, 1, 0], [0, 1, 1, 0], [0, 0, 0, 0]]
        supported, out, traces = run_oracle_pipeline(["extract", "rotate", "recolor"], grid)
        assert supported
        assert len(traces) == 3
        # extract → [[1,1],[1,1]], rotate → [[1,1],[1,1]] (square is symmetric)
        # recolor: bg=1 (most common in [[1,1],[1,1]]), so all cells == bg → no change
        assert out == [[1, 1], [1, 1]]

    def test_unsupported_in_pipeline(self):
        grid = [[1, 0], [0, 0]]
        supported, out, traces = run_oracle_pipeline(["extract", "fake_prim", "recolor"], grid)
        assert not supported
        assert len(traces) == 2