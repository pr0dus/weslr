import os
import shutil
from pathlib import Path
from weslr.worktree_hygiene import inspect_worktree, clean_safe_noise, HygieneReport


def make_file(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("temp")


def test_clean_worktree(tmp_path, monkeypatch):
    def fake_status():
        return []
    monkeypatch.setattr("weslr.worktree_hygiene._git_status_porcelain", fake_status)
    report = inspect_worktree()
    assert report.clean is True
    assert not report.safe_noise
    assert not report.risky_untracked


def test_safe_noise_classification_and_cleanup(tmp_path, monkeypatch):
    pyc = tmp_path / "foo.pyc"
    cache_dir = tmp_path / "__pycache__"
    make_file(pyc)
    cache_dir.mkdir()
    make_file(cache_dir / "bar.pyc")
    def fake_status():
        return [f"?? {pyc}", f"?? {cache_dir}"]
    monkeypatch.setattr("weslr.worktree_hygiene._git_status_porcelain", fake_status)
    monkeypatch.chdir(tmp_path)
    report = inspect_worktree()
    assert report.safe_noise == [str(pyc), str(cache_dir)]
    removed = clean_safe_noise(report)
    assert str(pyc) in removed and str(cache_dir) in removed
    assert not pyc.exists()
    assert not cache_dir.exists()


def test_risky_untracked(tmp_path, monkeypatch):
    unknown = tmp_path / "unknown.txt"
    make_file(unknown)
    def fake_status():
        return [f"?? {unknown}"]
    monkeypatch.setattr("weslr.worktree_hygiene._git_status_porcelain", fake_status)
    report = inspect_worktree()
    assert report.risky_untracked == [str(unknown)]
    assert not report.safe_noise


def test_modified_tracked(monkeypatch):
    def fake_status():
        return [" M weslr/core.py"]
    monkeypatch.setattr("weslr.worktree_hygiene._git_status_porcelain", fake_status)
    report = inspect_worktree()
    assert report.modified_tracked == ["weslr/core.py"]


def test_merge_conflicts(monkeypatch):
    def fake_status():
        return ["UU weslr/conflict.py"]
    monkeypatch.setattr("weslr.worktree_hygiene._git_status_porcelain", fake_status)
    report = inspect_worktree()
    assert report.merge_conflicts == ["weslr/conflict.py"]


def test_cleanup_does_not_touch_risky(tmp_path, monkeypatch):
    pyc = tmp_path / "foo.pyc"
    make_file(pyc)
    unknown = tmp_path / "unknown.txt"
    make_file(unknown)
    def fake_status():
        return [f"?? {pyc}", f"?? {unknown}"]
    monkeypatch.setattr("weslr.worktree_hygiene._git_status_porcelain", fake_status)
    monkeypatch.chdir(tmp_path)
    report = inspect_worktree()
    removed = clean_safe_noise(report)
    assert str(pyc) in removed
    assert unknown.exists()
