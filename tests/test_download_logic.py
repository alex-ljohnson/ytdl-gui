"""Tests for pure logic in modules/download.py."""
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from modules.download import Downloader
from modules.extension import ExtensionManager, PlatformExtension


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _opts(**overrides):
    base = {
        "video_format": "mp4", "audio_format": "m4a", "resolution": 1080,
        "audio": False, "strict_format": False, "format_string": "",
        "output_template": "", "audio_post": False, "metadata": False,
        "thumbnail": False, "subtitles": False, "description": False,
    }
    base.update(overrides)
    return base


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
    assert captured_opts.get("js_runtimes") == {"deno": {"path": None}}


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


# ---------------------------------------------------------------------------
# Shared fixture for opts-construction tests
# ---------------------------------------------------------------------------

@pytest.fixture
def dl_capture(monkeypatch, tmp_path):
    """Yields (make_downloader, captured_opts) for yt-dlp opts construction tests."""
    captured = {}

    class _FakeYtdl:
        def __init__(self, opts):
            captured.update(opts)
        def download(self, items):
            pass

    archive = tmp_path / "archive.txt"
    archive.touch()
    monkeypatch.setattr("modules.download.YoutubeDL", _FakeYtdl)
    monkeypatch.setattr("modules.download.relative_data", lambda p, **kw: str(archive))
    monkeypatch.setattr("modules.download.relative_path", lambda p, *a, **kw: str(tmp_path / "cookies.txt"))

    def make_downloader(opts, *, js_runtime="deno", disable_stats=True, verbosity=False):
        master = MagicMock()
        master.app_config = {"prefs": {"verbosity": verbosity, "disable_stats": disable_stats}}
        d = Downloader(opts, "C:/tmp", master)
        d.download_window = None
        monkeypatch.setattr(d, "get_js_runtime", lambda: js_runtime)
        monkeypatch.setattr(d, "apply_extensions", lambda lines: lines)
        return d

    return make_downloader, captured


_RUN = ["https://youtu.be/test"]


# ---------------------------------------------------------------------------
# js_runtimes — bundled QuickJS (the bug that prompted this test class)
# ---------------------------------------------------------------------------

def test_download_js_runtimes_bundled_quickjs(dl_capture):
    make, captured = dl_capture
    d = make(_opts(), js_runtime="quickjs:/fake/qjs.exe")
    d.download(_RUN, parallel=False, print_log=True)
    assert captured["js_runtimes"] == {"quickjs": {"path": "/fake/qjs.exe"}}


# ---------------------------------------------------------------------------
# Postprocessors
# ---------------------------------------------------------------------------

def test_download_postprocessor_audio_post(dl_capture):
    make, captured = dl_capture
    d = make(_opts(audio_post=True, audio_format="mp3"))
    d.download(_RUN, parallel=False, print_log=True)
    assert {"key": "FFmpegExtractAudio", "preferredcodec": "mp3"} in captured["postprocessors"]


def test_download_postprocessor_metadata(dl_capture):
    make, captured = dl_capture
    d = make(_opts(metadata=True))
    d.download(_RUN, parallel=False, print_log=True)
    assert {"key": "FFmpegMetadata"} in captured["postprocessors"]


def test_download_postprocessor_subtitles(dl_capture):
    make, captured = dl_capture
    d = make(_opts(subtitles=True))
    d.download(_RUN, parallel=False, print_log=True)
    assert {"key": "FFmpegEmbedSubtitle"} in captured["postprocessors"]


def test_download_postprocessor_thumbnail_embedded_for_mp4(dl_capture):
    make, captured = dl_capture
    d = make(_opts(thumbnail=True, video_format="mp4"))
    d.download(_RUN, parallel=False, print_log=True)
    assert {"key": "EmbedThumbnail", "already_have_thumbnail": False} in captured["postprocessors"]


def test_download_postprocessor_thumbnail_not_embedded_for_webm(dl_capture):
    make, captured = dl_capture
    d = make(_opts(thumbnail=True, video_format="webm"))
    d.download(_RUN, parallel=False, print_log=True)
    keys = [p["key"] for p in captured["postprocessors"]]
    assert "EmbedThumbnail" not in keys


# ---------------------------------------------------------------------------
# Format / template overrides
# ---------------------------------------------------------------------------

def test_download_opts_custom_format_string_overrides_format_select(dl_capture):
    make, captured = dl_capture
    d = make(_opts(format_string="bestvideo+bestaudio/best"))
    d.download(_RUN, parallel=False, print_log=True)
    assert captured["format"] == "bestvideo+bestaudio/best"


def test_download_opts_custom_output_template(dl_capture):
    make, captured = dl_capture
    d = make(_opts(output_template="%(title)s.%(ext)s"))
    d.download(_RUN, parallel=False, print_log=True)
    assert captured["outtmpl"] == "%(title)s.%(ext)s"


# ---------------------------------------------------------------------------
# Progress hooks and verbosity
# ---------------------------------------------------------------------------

def test_download_opts_progress_hook_added_when_stats_enabled(dl_capture):
    make, captured = dl_capture
    d = make(_opts(), disable_stats=False)
    d.download(_RUN, parallel=False, print_log=True)
    assert len(captured["progress_hooks"]) == 1


def test_download_opts_verbosity_propagated(dl_capture):
    make, captured = dl_capture
    d = make(_opts(), verbosity=True)
    d.download(_RUN, parallel=False, print_log=True)
    assert captured["verbose"] is True
