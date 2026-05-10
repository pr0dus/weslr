import contextlib
import io
import os
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from weslr.evals import random_ordinary_intelligence_prep_v1 as roi  # noqa: E402


class RandomOrdinaryIntelligencePrepTests(unittest.TestCase):
    def test_prompt_mix_is_roughly_80_20(self):
        prompts = roi.build_prompt_run(seed=42, count=50)
        ordinary = sum(1 for category, _ in prompts if category != roi.WESLR_CATEGORY)
        weslr = sum(1 for category, _ in prompts if category == roi.WESLR_CATEGORY)
        self.assertEqual(len(prompts), 50)
        self.assertEqual(ordinary, 40)
        self.assertEqual(weslr, 10)

    def test_deterministic_seed_is_stable(self):
        prompts_a = roi.build_prompt_run(seed=42, count=20)
        prompts_b = roi.build_prompt_run(seed=42, count=20)
        prompts_c = roi.build_prompt_run(seed=7, count=20)
        self.assertEqual(prompts_a, prompts_b)
        self.assertNotEqual(prompts_a, prompts_c)

    def test_small_run_summary_contains_required_sections(self):
        summary = roi.run_eval(seed=42, count=10)
        data = summary.to_dict()
        self.assertEqual(data["count"], 10)
        self.assertIn("path_counts", data)
        self.assertIn("weak_prompts", data)
        self.assertIn("category_scores", data)
        self.assertEqual(len(data["weak_prompts"]), min(10, len(data["results"])))

    def test_main_writes_no_files_by_default(self):
        before = set(os.listdir(Path.cwd()))
        with tempfile.TemporaryDirectory() as tmpdir:
            old_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    rc = roi.main([])
                self.assertEqual(rc, 0)
                self.assertEqual(os.listdir(tmpdir), [])
            finally:
                os.chdir(old_cwd)
        after = set(os.listdir(Path.cwd()))
        self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
