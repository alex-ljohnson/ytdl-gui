"""Tests for modules.utils."""
import os
import sys

import pytest

from modules import constants
from modules.utils import version_compare


@pytest.mark.parametrize(
    "a,b,expected",
    [
        ("v2024.01.23.f1", "v2024.01.23.f1", "="),
        ("v2024.02.01.f1", "v2024.01.23.f1", ">"),
        ("v2023.12.28.f1", "v2024.01.23.f1", "<"),
        ("v1.10.0", "v1.9.0", ">"),   # numeric, not lexical
        ("v1.9.0", "v1.10.0", "<"),
    ],
)
def test_version_compare(a, b, expected):
    assert version_compare(a, b) == expected


def test_version_compare_mismatched_depth_raises():
    with pytest.raises(ValueError):
        version_compare("1.0", "1.0.0")


# ---------------------------------------------------------------------------
# relative_path
# ---------------------------------------------------------------------------

from modules import utils as _utils


def test_relative_path_unbundled_existing(tmp_path, monkeypatch):
    (tmp_path / "asset.txt").write_text("data")
    monkeypatch.delattr(sys, "_MEIPASS", raising=False)
    monkeypatch.chdir(tmp_path)
    result = _utils.relative_path("asset.txt")
    assert os.path.exists(result)


def test_relative_path_unbundled_missing_raises(tmp_path, monkeypatch):
    monkeypatch.delattr(sys, "_MEIPASS", raising=False)
    monkeypatch.chdir(tmp_path)
    with pytest.raises(FileNotFoundError):
        _utils.relative_path("ghost.txt")


def test_relative_path_create_makes_directory(tmp_path, monkeypatch):
    monkeypatch.delattr(sys, "_MEIPASS", raising=False)
    monkeypatch.chdir(tmp_path)
    result = _utils.relative_path("new_subdir", create=True)
    assert os.path.isdir(result)


def test_relative_path_bundled(tmp_path, monkeypatch):
    (tmp_path / "bundled.txt").write_text("data")
    monkeypatch.setattr(sys, "_MEIPASS", str(tmp_path), raising=False)
    result = _utils.relative_path("bundled.txt")
    assert os.path.exists(result)


# ---------------------------------------------------------------------------
# relative_data
# ---------------------------------------------------------------------------

def test_relative_data_existing(tmp_path, monkeypatch):
    (tmp_path / "config.json").write_text("{}")
    monkeypatch.setattr(constants, "DATA_PATH", str(tmp_path))
    result = _utils.relative_data("config.json")
    assert result.endswith("config.json")
    assert os.path.exists(result)


def test_relative_data_missing_should_exist_raises(tmp_path, monkeypatch):
    monkeypatch.setattr(constants, "DATA_PATH", str(tmp_path))
    with pytest.raises(FileNotFoundError):
        _utils.relative_data("missing.json", should_exist=True)


def test_relative_data_missing_should_not_exist_returns_path(tmp_path, monkeypatch):
    monkeypatch.setattr(constants, "DATA_PATH", str(tmp_path))
    result = _utils.relative_data("new.json", should_exist=False)
    assert result.endswith("new.json")


# ---------------------------------------------------------------------------
# find_ffprobe / find_ffmpeg_dir
# ---------------------------------------------------------------------------

from modules.utils import find_ffprobe, find_ffmpeg_dir


class TestFindFfprobe:
    def test_system_path_takes_priority(self, monkeypatch):
        monkeypatch.setattr("modules.utils.shutil.which", lambda x: "/usr/bin/ffprobe" if x == "ffprobe" else None)
        assert find_ffprobe() == "/usr/bin/ffprobe"

    def test_bundled_fallback(self, monkeypatch):
        monkeypatch.setattr("modules.utils.shutil.which", lambda x: None)
        monkeypatch.setattr("modules.utils._bundled_ffmpeg_dir", lambda: "/bundled/bin")
        assert find_ffprobe() == os.path.join("/bundled/bin", "ffprobe.exe")

    def test_not_found_returns_none(self, monkeypatch):
        monkeypatch.setattr("modules.utils.shutil.which", lambda x: None)
        monkeypatch.setattr("modules.utils._bundled_ffmpeg_dir", lambda: None)
        assert find_ffprobe() is None


class TestFindFfmpegDir:
    def test_system_ffmpeg_returns_none(self, monkeypatch):
        monkeypatch.setattr("modules.utils.shutil.which", lambda x: "/usr/bin/ffmpeg" if x == "ffmpeg" else None)
        assert find_ffmpeg_dir() is None

    def test_bundled_fallback(self, monkeypatch):
        monkeypatch.setattr("modules.utils.shutil.which", lambda x: None)
        monkeypatch.setattr("modules.utils._bundled_ffmpeg_dir", lambda: "/bundled/bin")
        assert find_ffmpeg_dir() == "/bundled/bin"

    def test_not_found_returns_none(self, monkeypatch):
        monkeypatch.setattr("modules.utils.shutil.which", lambda x: None)
        monkeypatch.setattr("modules.utils._bundled_ffmpeg_dir", lambda: None)
        assert find_ffmpeg_dir() is None


# ---------------------------------------------------------------------------
# _bundled_ffmpeg_dir
# ---------------------------------------------------------------------------

from modules.utils import _bundled_ffmpeg_dir


class TestBundledFfmpegDir:
    def test_returns_dirname_when_ffprobe_found(self, monkeypatch):
        monkeypatch.setattr("modules.utils.relative_path",
                            lambda p, **kw: "/bundled/ffmpeg/bin/ffprobe.exe")
        assert _bundled_ffmpeg_dir() == "/bundled/ffmpeg/bin"

    def test_returns_none_when_not_found(self, monkeypatch):
        def _raise(p, **kw):
            raise FileNotFoundError
        monkeypatch.setattr("modules.utils.relative_path", _raise)
        assert _bundled_ffmpeg_dir() is None


# ---------------------------------------------------------------------------
# log_debug
# ---------------------------------------------------------------------------

from modules.utils import log_debug


def test_log_debug_does_nothing_when_debug_disabled(monkeypatch, capsys):
    monkeypatch.setattr(constants, "DEBUG", False)
    log_debug("should not appear", default_stdout=False)
    assert capsys.readouterr().out == ""


def test_log_debug_prints_when_debug_enabled(monkeypatch, capsys):
    monkeypatch.setattr(constants, "DEBUG", True)
    log_debug("hello debug", default_stdout=False)
    assert "hello debug" in capsys.readouterr().out


def test_log_debug_writes_to_stdout_def_when_default_stdout(monkeypatch):
    from unittest.mock import MagicMock
    fake_stdout = MagicMock()
    monkeypatch.setattr(constants, "DEBUG", True)
    monkeypatch.setattr(constants, "STDOUT_DEF", fake_stdout)
    log_debug("msg", default_stdout=True)
    fake_stdout.write.assert_called_once_with("msg\n")


# ---------------------------------------------------------------------------
# disable_insert
# ---------------------------------------------------------------------------

from modules.utils import disable_insert
from tkinter import DISABLED, NORMAL


def test_disable_insert_enables_inserts_then_disables():
    from unittest.mock import MagicMock, call
    t = MagicMock()
    disable_insert(t, "end", "hello")
    assert t.config.call_args_list[0] == call(state=NORMAL)
    t.insert.assert_called_once_with("end", "hello", ())
    assert t.config.call_args_list[1] == call(state=DISABLED)


# ---------------------------------------------------------------------------
# link
# ---------------------------------------------------------------------------

def test_link_calls_startfile(monkeypatch):
    from unittest.mock import MagicMock
    import os
    mock_startfile = MagicMock()
    monkeypatch.setattr(os, "startfile", mock_startfile)
    _utils.link("https://example.com")
    mock_startfile.assert_called_once_with("https://example.com")


from modules.utils import _bundled_quickjs, find_js_runtime


class TestBundledQuickjs:
    def test_returns_path_when_found(self, monkeypatch):
        monkeypatch.setattr("modules.utils.relative_path", lambda p, **kw: r"C:\app\quickjs\qjs.exe")
        assert _bundled_quickjs() == r"C:\app\quickjs\qjs.exe"

    def test_returns_none_when_not_found(self, monkeypatch):
        def _raise(p, **kw):
            raise FileNotFoundError
        monkeypatch.setattr("modules.utils.relative_path", _raise)
        assert _bundled_quickjs() is None


class TestFindJsRuntime:
    def _which(self, found: str | None):
        return lambda name: (f"C:\\tools\\{name}.exe" if name == found else None)

    def test_prefers_deno_on_path(self, monkeypatch):
        monkeypatch.setattr("modules.utils.shutil.which", self._which("deno"))
        assert find_js_runtime() == "deno"

    def test_uses_bun_when_no_deno(self, monkeypatch):
        monkeypatch.setattr("modules.utils.shutil.which", self._which("bun"))
        assert find_js_runtime() == "bun"

    def test_uses_node_when_no_deno_or_bun(self, monkeypatch):
        monkeypatch.setattr("modules.utils.shutil.which", self._which("node"))
        assert find_js_runtime() == "node"

    def test_maps_qjs_on_path_to_quickjs_name(self, monkeypatch):
        monkeypatch.setattr("modules.utils.shutil.which", self._which("qjs"))
        assert find_js_runtime() == "quickjs"

    def test_falls_back_to_bundled_qjs(self, monkeypatch):
        monkeypatch.setattr("modules.utils.shutil.which", lambda name: None)
        monkeypatch.setattr("modules.utils._bundled_quickjs", lambda: r"C:\app\quickjs\qjs.exe")
        assert find_js_runtime() == r"quickjs:C:\app\quickjs\qjs.exe"

    def test_returns_none_when_nothing_found(self, monkeypatch):
        monkeypatch.setattr("modules.utils.shutil.which", lambda name: None)
        monkeypatch.setattr("modules.utils._bundled_quickjs", lambda: None)
        assert find_js_runtime() is None
