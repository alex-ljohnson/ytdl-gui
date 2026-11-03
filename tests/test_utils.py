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

@pytest.mark.skipif(sys.platform != "win32", reason="os.startfile is Windows-only")
def test_link_calls_startfile(monkeypatch):
    from unittest.mock import MagicMock
    import os
    mock_startfile = MagicMock()
    monkeypatch.setattr(os, "startfile", mock_startfile)
    _utils.link("https://example.com")
    mock_startfile.assert_called_once_with("https://example.com")

