"""Unit tests for SystemAccount."""
from __future__ import annotations

from src.core.services.base_service import SupportsPermissionCheck
from src.core.services.system_account import SystemAccount


def test_system_account_has_permission_always_true():
    actor = SystemAccount()
    assert actor.has_permission("sale", "sale", "create") is True
    assert actor.has_permission("anything", "goes", "here") is True
    assert actor.has_permission("", "", "") is True


def test_system_account_satisfies_permission_check_protocol():
    actor: SupportsPermissionCheck = SystemAccount()
    assert actor.has_permission("stock", "item", "update") is True