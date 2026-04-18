import pytest
from types import SimpleNamespace
from weslr.lineage.permissions import assert_can_view, assert_can_change_status


def test_view_permission_denied():
    backend = SimpleNamespace(can_view_lineage=lambda u, w: False)
    with pytest.raises(PermissionError):
        assert_can_view(backend, "u1", "ws1")


def test_view_permission_allowed():
    backend = SimpleNamespace(can_view_lineage=lambda u, w: True)
    assert_can_view(backend, "u1", "ws1")


def test_status_permission_denied():
    backend = SimpleNamespace(can_change_status=lambda u, w: False)
    with pytest.raises(PermissionError):
        assert_can_change_status(backend, "u1", "ws1")


def test_status_permission_allowed():
    backend = SimpleNamespace(can_change_status=lambda u, w: True)
    assert_can_change_status(backend, "u1", "ws1")
