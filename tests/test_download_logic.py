"""Tests for pure logic in modules/download.py."""
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from modules.download import Downloader
from modules.extension import ExtensionManager, PlatformExtension


class _FakePlatform(PlatformExtension):
    _name = "Fake"

    def __init__(self, matches, expansion):
        super().__init__()
        self._matches = matches
        self._expansion = expansion
        self.ready = True

    def check_type(self, item):
        return item in self._matches

    def get_items(self, urn):
        return list(self._expansion)


@pytest.fixture(autouse=True)
def _reset_extension_manager():
    original = ExtensionManager.instance
    try:
        yield
    finally:
        ExtensionManager.instance = original


@pytest.fixture
def downloader():
    master = MagicMock()
    master.app_config = {"prefs": {"verbosity": False}}
    d = Downloader({}, "C:/tmp", master)
    d.download_window = MagicMock()
    return d


def test_apply_extensions_returns_plain_lines_untouched(downloader, monkeypatch):
    ExtensionManager.instance = SimpleNamespace(extensions={})
    result = downloader.apply_extensions(["https://youtu.be/x", "  ", "# comment"])
    assert result == ["https://youtu.be/x"]


def test_apply_extensions_expands_via_platform_extension(downloader):
    fake = _FakePlatform(matches={"spotify:track:abc"}, expansion=["Song - Artist"])
    ExtensionManager.instance = SimpleNamespace(extensions={"fake": fake})
    result = downloader.apply_extensions(["spotify:track:abc", "https://youtu.be/x"])
    assert result == ["Song - Artist", "https://youtu.be/x"]


def test_apply_extensions_tolerates_none_from_extension(downloader):
    fake = _FakePlatform(matches={"bad"}, expansion=[])
    fake.get_items = lambda urn: None  # simulate SpotifyExtension failure path
    ExtensionManager.instance = SimpleNamespace(extensions={"fake": fake})
    result = downloader.apply_extensions(["bad", "ok"])
    assert result == ["ok"]


def test_get_js_runtime_delegates_to_find_js_runtime(downloader, monkeypatch):
    monkeypatch.setattr("modules.download.find_js_runtime", lambda: "deno")
    assert downloader.get_js_runtime() == "deno"


def test_get_js_runtime_returns_none_when_no_runtime(downloader, monkeypatch):
    monkeypatch.setattr("modules.download.find_js_runtime", lambda: None)
    assert downloader.get_js_runtime() is None


def test_download_includes_js_runtimes_when_runtime_found(monkeypatch, tmp_path):
    captured_opts = {}

    class FakeYtdl:
        def __init__(self, opts):
            captured_opts.update(opts)
        def download(self, items):
            pass

    archive = tmp_path / "archive.txt"
    archive.touch()

    master = MagicMock()
    master.app_config = {"prefs": {"verbosity": False, "disable_stats": True}}

    download_options = {
        "video_format": "mp4", "audio_format": "m4a", "resolution": 1080,
        "audio": False, "strict_format": False, "format_string": "",
        "output_template": "", "audio_post": False, "metadata": False,
        "thumbnail": False, "subtitles": False, "description": False,
    }

    d = Downloader(download_options, "C:/tmp", master)
    d.download_window = MagicMock()

    monkeypatch.setattr("modules.download.YoutubeDL", FakeYtdl)
    monkeypatch.setattr("modules.download.relative_data", lambda p, **kw: str(archive))
    monkeypatch.setattr("modules.download.relative_path", lambda p, *a, **kw: str(tmp_path / "cookies.txt"))
    monkeypatch.setattr(d, "get_js_runtime", lambda: "deno")
    monkeypatch.setattr(d, "apply_extensions", lambda lines: lines)

    d.download(["https://youtu.be/test"], parallel=False, print_log=True)
    assert captured_opts.get("js_runtimes") == ["deno"]


def test_download_omits_js_runtimes_when_no_runtime(monkeypatch, tmp_path):
    captured_opts = {}

    class FakeYtdl:
        def __init__(self, opts):
            captured_opts.update(opts)
        def download(self, items):
            pass

    archive = tmp_path / "archive.txt"
    archive.touch()

    master = MagicMock()
    master.app_config = {"prefs": {"verbosity": False, "disable_stats": True}}

    download_options = {
        "video_format": "mp4", "audio_format": "m4a", "resolution": 1080,
        "audio": False, "strict_format": False, "format_string": "",
        "output_template": "", "audio_post": False, "metadata": False,
        "thumbnail": False, "subtitles": False, "description": False,
    }

    d = Downloader(download_options, "C:/tmp", master)
    d.download_window = MagicMock()

    monkeypatch.setattr("modules.download.YoutubeDL", FakeYtdl)
    monkeypatch.setattr("modules.download.relative_data", lambda p, **kw: str(archive))
    monkeypatch.setattr("modules.download.relative_path", lambda p, *a, **kw: str(tmp_path / "cookies.txt"))
    monkeypatch.setattr(d, "get_js_runtime", lambda: None)
    monkeypatch.setattr(d, "apply_extensions", lambda lines: lines)

    d.download(["https://youtu.be/test"], parallel=False, print_log=True)
    assert "js_runtimes" not in captured_opts
