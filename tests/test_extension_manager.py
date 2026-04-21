"""Tests for modules.extension.ExtensionManager singleton semantics."""
import pytest
from unittest.mock import MagicMock

from modules.extension import ExtensionManager


@pytest.fixture(autouse=True)
def _reset_extension_manager():
    original = ExtensionManager.instance
    try:
        yield
    finally:
        ExtensionManager.instance = original


def test_extension_manager_initialises_once(monkeypatch):
    ExtensionManager.instance = None  # reset for test
    calls = []

    def fake_load(self):
        calls.append(self)

    monkeypatch.setattr(ExtensionManager, "load_extensions", fake_load)
    first = ExtensionManager(MagicMock())
    second = ExtensionManager(MagicMock())
    assert first is second
    assert len(calls) == 1
