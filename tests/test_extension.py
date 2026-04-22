"""Tests for extension base classes and Downloader.apply_extensions."""
import pytest
from unittest.mock import MagicMock

from modules.extension import (
    DownloadExtension,
    Extension,
    ExtensionManager,
    PlatformExtension,
)
from modules.download import Downloader


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _reset_extension_manager():
    original = ExtensionManager.instance
    try:
        yield
    finally:
        ExtensionManager.instance = original


def _make_downloader():
    d = Downloader.__new__(Downloader)
    d.download_window = None
    return d


# ---------------------------------------------------------------------------
# Extension base class
# ---------------------------------------------------------------------------

def test_extension_default_name_is_class_name():
    class MyPlugin(Extension):
        pass
    assert MyPlugin().get_name() == "MyPlugin"


def test_extension_custom_name():
    ext = Extension(name="Spotify")
    assert ext.get_name() == "Spotify"


def test_extension_initially_not_ready():
    assert not Extension().ready


def test_extension_enable_sets_ready():
    ext = Extension()
    ext.enable()
    assert ext.ready


def test_extension_disable_clears_ready():
    ext = Extension()
    ext.enable()
    ext.disable()
    assert not ext.ready


# ---------------------------------------------------------------------------
# PlatformExtension
# ---------------------------------------------------------------------------

def test_platform_extension_check_type_empty_string():
    assert not PlatformExtension().check_type("")


def test_platform_extension_check_type_non_empty():
    assert PlatformExtension().check_type("https://example.com")


def test_platform_extension_get_items_passthrough():
    ext = PlatformExtension()
    assert ext.get_items("https://example.com") == ["https://example.com"]


# ---------------------------------------------------------------------------
# DownloadExtension
# ---------------------------------------------------------------------------

def test_download_extension_initially_not_running():
    assert not DownloadExtension().is_running()


def test_download_extension_starting_sets_running():
    ext = DownloadExtension()
    result = ext.download_starting(["a", "b"])
    assert ext.is_running()
    assert result == ["a", "b"]


def test_download_extension_finished_clears_running():
    ext = DownloadExtension()
    ext.download_starting(["a"])
    ext.download_finished(["a"])
    assert not ext.is_running()


def test_download_extension_starting_returns_items_unchanged():
    ext = DownloadExtension()
    items = ["x", "y", "z"]
    assert ext.download_starting(items) is items


# ---------------------------------------------------------------------------
# Downloader.apply_extensions
# ---------------------------------------------------------------------------

def test_apply_extensions_no_manager_returns_filtered_lines():
    ExtensionManager.instance = None
    d = _make_downloader()
    result = d.apply_extensions(["https://example.com", "# comment", "  ", "https://other.com"])
    assert result == ["https://example.com", "https://other.com"]


def test_apply_extensions_strips_comments_and_blanks():
    ExtensionManager.instance = None
    d = _make_downloader()
    assert d.apply_extensions(["# only a comment"]) == []
    assert d.apply_extensions(["   "]) == []


def test_apply_extensions_platform_extension_expands_items():
    class _SpotifyLike(PlatformExtension):
        def check_type(self, item):
            return item.startswith("spotify:")

        def get_items(self, urn):
            return ["track1", "track2"]

    ext = _SpotifyLike()
    ext.enable()

    manager = MagicMock()
    manager.extensions = {"_SpotifyLike": ext}
    ExtensionManager.instance = manager

    d = _make_downloader()
    result = d.apply_extensions(["spotify:track:abc", "https://youtube.com"])
    assert "track1" in result
    assert "track2" in result
    assert "https://youtube.com" in result


def test_apply_extensions_unmatched_item_passes_through():
    class _NeverMatch(PlatformExtension):
        def check_type(self, item):
            return False

    manager = MagicMock()
    manager.extensions = {"_NeverMatch": _NeverMatch()}
    ExtensionManager.instance = manager

    d = _make_downloader()
    result = d.apply_extensions(["https://example.com"])
    assert result == ["https://example.com"]


def test_apply_extensions_download_extension_transforms_items():
    class _Uppercaser(DownloadExtension):
        def download_starting(self, items):
            super().download_starting(items)
            return [i.upper() for i in items]

    ext = _Uppercaser()
    ext.enable()

    manager = MagicMock()
    manager.extensions = {"_Uppercaser": ext}
    ExtensionManager.instance = manager

    d = _make_downloader()
    result = d.apply_extensions(["https://example.com"])
    assert result == ["HTTPS://EXAMPLE.COM"]


def test_apply_extensions_not_ready_platform_extension_user_enables(monkeypatch):
    """_silence_tk autouse fixture mocks askyesnocancel to return True (yes → enable)."""

    class _Lazy(PlatformExtension):
        def check_type(self, item):
            return item.startswith("lazy:")

        def get_items(self, urn):
            return ["expanded"]

    ext = _Lazy()  # ready=False

    manager = MagicMock()
    manager.extensions = {"_Lazy": ext}
    ExtensionManager.instance = manager

    d = _make_downloader()
    result = d.apply_extensions(["lazy:item"])
    # askyesnocancel returns True → enable() called → ext.ready=True → expanded
    assert result == ["expanded"]


def test_apply_extensions_not_ready_user_cancels_returns_none(monkeypatch):
    import tkinter.messagebox as mb

    class _Lazy(PlatformExtension):
        def check_type(self, item):
            return True

    ext = _Lazy()  # ready=False
    manager = MagicMock()
    manager.extensions = {"_Lazy": ext}
    ExtensionManager.instance = manager

    monkeypatch.setattr(mb, "askyesnocancel", MagicMock(return_value=None))

    d = _make_downloader()
    assert d.apply_extensions(["item"]) is None