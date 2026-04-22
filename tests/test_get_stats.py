"""Tests for modules.get_stats.GetStats."""
import json
import os
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from modules.get_stats import GetStats


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_folder(tmp_path):
    for name in ["a.mp4", "b.mp4", "c.mp4", "d.mp4", "e.mp4"]:
        (tmp_path / name).write_bytes(b"")
    return tmp_path


@pytest.fixture
def stats(tmp_path):
    return GetStats(str(tmp_path), quiet=True, silent=True)


# ---------------------------------------------------------------------------
# folder_length — happy path (existing test, preserved)
# ---------------------------------------------------------------------------

def test_folder_length_processes_each_file_exactly_once(sample_folder):
    seen = []

    def fake_get_length(self, filename):
        seen.append(os.path.basename(filename))
        return 10.0

    with patch.object(GetStats, "get_length", fake_get_length):
        s = GetStats(str(sample_folder), quiet=True, silent=True)
        result = s.folder_length()

    assert sorted(seen) == ["a.mp4", "b.mp4", "c.mp4", "d.mp4", "e.mp4"]
    assert result["hours"] == 0
    assert result["minutes"] == 0
    assert result["seconds"] == 50


# ---------------------------------------------------------------------------
# folder_length — ffprobe not found
# ---------------------------------------------------------------------------

def test_folder_length_when_ffprobe_missing(tmp_path, monkeypatch):
    monkeypatch.setattr("modules.get_stats.find_ffprobe", lambda: None)
    s = GetStats(str(tmp_path), quiet=True, silent=True)
    result = s.folder_length()
    assert s._ffprobe is None
    assert result == {"hours": 0, "minutes": 0, "seconds": 0}


# ---------------------------------------------------------------------------
# get_length
# ---------------------------------------------------------------------------

def test_get_length_returns_float_on_success(tmp_path, monkeypatch):
    f = tmp_path / "video.mp4"
    f.write_bytes(b"fake")
    mock_result = MagicMock()
    mock_result.stdout = json.dumps({"format": {"duration": "12.345"}})
    monkeypatch.setattr(subprocess, "run", lambda *a, **kw: mock_result)
    s = GetStats(str(tmp_path), quiet=True, silent=True)
    s._ffprobe = "/fake/ffprobe"
    assert s.get_length(str(f)) == pytest.approx(12.345)


def test_get_length_returns_none_on_subprocess_error(tmp_path, monkeypatch):
    f = tmp_path / "video.mp4"
    f.write_bytes(b"fake")

    def _raise(*a, **kw):
        raise subprocess.CalledProcessError(1, "ffprobe")

    monkeypatch.setattr(subprocess, "run", _raise)
    s = GetStats(str(tmp_path), quiet=True, silent=True)
    s._ffprobe = "/fake/ffprobe"
    assert s.get_length(str(f)) is None


def test_get_length_returns_none_when_file_missing(tmp_path):
    s = GetStats(str(tmp_path), quiet=True, silent=True)
    s._ffprobe = "/fake/ffprobe"
    assert s.get_length(str(tmp_path / "ghost.mp4")) is None


def test_get_length_returns_none_when_ffprobe_none(tmp_path):
    f = tmp_path / "video.mp4"
    f.write_bytes(b"fake")
    s = GetStats(str(tmp_path), quiet=True, silent=True)
    s._ffprobe = None
    assert s.get_length(str(f)) is None


# ---------------------------------------------------------------------------
# file_time branches
# ---------------------------------------------------------------------------

def test_file_time_skips_temp_files(stats):
    stats.file_time("video.temp.mp4")
    assert stats.totTime == 0


def test_file_time_skips_non_media_extension(stats):
    stats.file_time("document.pdf")
    assert stats.totTime == 0


def test_file_time_skips_when_get_length_returns_none(stats, monkeypatch):
    monkeypatch.setattr(GetStats, "get_length", lambda self, f: None)
    stats.file_time("video.mp4")
    assert stats.totTime == 0


def test_file_time_accumulates_duration(stats, monkeypatch):
    monkeypatch.setattr(GetStats, "get_length", lambda self, f: 30.0)
    stats.file_time("video.mp4")
    assert stats.totTime == pytest.approx(30.0)


# ---------------------------------------------------------------------------
# write branches
# ---------------------------------------------------------------------------

def test_write_not_quiet_prints(capsys):
    s = GetStats(".", quiet=False, silent=False)
    s.write("hello world")
    assert "hello world" in capsys.readouterr().out


def test_write_quiet_long_1_shows_processing(capsys):
    s = GetStats(".", quiet=True, silent=False)
    s.write("text", long=1)
    out = capsys.readouterr().out
    assert "Processing" in out
    assert s.__dots__ == 0


def test_write_quiet_long_2_shows_spinner(capsys):
    s = GetStats(".", quiet=True, silent=False)
    s.write("text", long=2)
    out = capsys.readouterr().out
    assert "Processing" in out
    assert s.__dots__ == 1
