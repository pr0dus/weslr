from __future__ import annotations
from typing import Protocol


class PermissionBackend(Protocol):
    def can_view_lineage(self, user_id: str, workspace_id: str) -> bool: ...
    def can_change_status(self, user_id: str, workspace_id: str) -> bool: ...


def assert_can_view(backend: PermissionBackend, user_id: str, workspace_id: str):
    if not backend.can_view_lineage(user_id, workspace_id):
        raise PermissionError("view not permitted")


def assert_can_change_status(backend: PermissionBackend, user_id: str, workspace_id: str):
    if not backend.can_change_status(user_id, workspace_id):
        raise PermissionError("status change not permitted")
