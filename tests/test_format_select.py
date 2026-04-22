"""Tests for Downloader.format_select — the yt-dlp format selection generator."""
import pytest
from modules.download import Downloader


def _make_downloader(opts):
    d = Downloader.__new__(Downloader)
    d.download_options = opts
    return d


def _fmt(format_id, ext, *, acodec="none", vcodec="none", height=720, protocol="https", format_note=""):
    return {
        "format_id": format_id,
        "ext": ext,
        "acodec": acodec,
        "vcodec": vcodec,
        "height": height,
        "protocol": protocol,
        "format_note": format_note,
    }


def _select(opts, formats):
    d = _make_downloader(opts)
    return list(d.format_select({"formats": formats}))


_VIDEO_OPTS = dict(audio=False, video_format="mp4", audio_format="best", resolution=1080, strict_format=False)
_AUDIO_OPTS = dict(audio=True, audio_format="mp3", video_format="best", resolution=1080, strict_format=False)
_BEST_OPTS = dict(audio=False, video_format="best", audio_format="best", resolution=1080, strict_format=False)


# ---------------------------------------------------------------------------
# Audio-only mode
# ---------------------------------------------------------------------------

def test_audio_only_preferred_format_selected():
    formats = [
        _fmt("1", "m4a", acodec="aac", height=0),
        _fmt("2", "mp3", acodec="mp3", height=0),
    ]
    result = _select(_AUDIO_OPTS, formats)
    assert len(result) == 1
    assert result[0]["ext"] == "mp3"
    assert result[0]["format_id"] == "2"


def test_audio_only_falls_back_to_m4a_when_preferred_absent():
    formats = [
        _fmt("1", "m4a", acodec="aac", height=0),
        _fmt("2", "webm", acodec="opus", height=0),
    ]
    # audio_format="mp3" not available → fall back to m4a
    result = _select(_AUDIO_OPTS, formats)
    assert len(result) == 1
    assert result[0]["ext"] == "m4a"
    assert result[0]["format_id"] == "1"


def test_audio_only_no_audio_at_all_yields_nothing():
    formats = [
        _fmt("1", "mp4", vcodec="h264", height=720),
    ]
    result = _select(_AUDIO_OPTS, formats)
    assert result == []


# ---------------------------------------------------------------------------
# Video mode — specific format
# ---------------------------------------------------------------------------

def test_video_specific_format_merges_video_and_audio():
    formats = [
        _fmt("a1", "m4a", acodec="aac", height=0),
        _fmt("v1", "mp4", vcodec="h264", height=720),
    ]
    result = _select(_VIDEO_OPTS, formats)
    assert len(result) == 1
    r = result[0]
    assert r["ext"] == "mp4"
    assert "v1" in r["format_id"] and "a1" in r["format_id"]
    assert len(r["requested_formats"]) == 2


def test_video_with_embedded_audio_yields_as_single_stream():
    formats = [
        _fmt("v1", "mp4", vcodec="h264", acodec="aac", height=720),
    ]
    result = _select(_VIDEO_OPTS, formats)
    assert len(result) == 1
    assert result[0]["format_id"] == "v1"
    assert result[0]["ext"] == "mp4"
    assert len(result[0]["requested_formats"]) == 1


# ---------------------------------------------------------------------------
# Video mode — "best"
# ---------------------------------------------------------------------------

def test_video_best_merges_into_mkv():
    formats = [
        _fmt("a1", "m4a", acodec="aac", height=0),
        _fmt("v1", "webm", vcodec="vp9", height=1080),
    ]
    result = _select(_BEST_OPTS, formats)
    assert len(result) == 1
    r = result[0]
    assert r["ext"] == "mkv"
    assert "v1" in r["format_id"] and "a1" in r["format_id"]


def test_video_best_video_only_no_audio_available():
    formats = [
        _fmt("v1", "webm", vcodec="vp9", height=1080),
    ]
    result = _select(_BEST_OPTS, formats)
    assert len(result) == 1
    assert result[0]["format_id"] == "v1"


# ---------------------------------------------------------------------------
# Resolution limiting
# ---------------------------------------------------------------------------

def test_resolution_limit_picks_highest_within_cap():
    formats = [
        _fmt("a1", "m4a", acodec="aac", height=0),
        _fmt("v360", "mp4", vcodec="h264", height=360),
        _fmt("v720", "mp4", vcodec="h264", height=720),
        _fmt("v1080", "mp4", vcodec="h264", height=1080),
    ]
    opts = dict(_VIDEO_OPTS, resolution=720)
    result = _select(opts, formats)
    assert len(result) == 1
    # formats are worst→best; after reversal best is first; first within cap is 720p
    assert result[0]["format_id"] == "v720+a1"


def test_resolution_limit_exact_match_allowed():
    formats = [
        _fmt("a1", "m4a", acodec="aac", height=0),
        _fmt("v720", "mp4", vcodec="h264", height=720),
    ]
    opts = dict(_VIDEO_OPTS, resolution=720)
    result = _select(opts, formats)
    assert len(result) == 1
    assert result[0]["format_id"] == "v720+a1"


# ---------------------------------------------------------------------------
# Strict format
# ---------------------------------------------------------------------------

def test_strict_format_no_fallback_yields_nothing():
    formats = [
        _fmt("a1", "m4a", acodec="aac", height=0),
        _fmt("v1", "webm", vcodec="vp9", height=720),
    ]
    opts = dict(_VIDEO_OPTS, strict_format=True)  # wants mp4, only webm available
    result = _select(opts, formats)
    assert result == []


def test_strict_format_exact_match_succeeds():
    formats = [
        _fmt("a1", "m4a", acodec="aac", height=0),
        _fmt("v1", "mp4", vcodec="h264", height=720),
    ]
    opts = dict(_VIDEO_OPTS, strict_format=True)
    result = _select(opts, formats)
    assert len(result) == 1
    assert result[0]["ext"] == "mp4"


# ---------------------------------------------------------------------------
# No video at all
# ---------------------------------------------------------------------------

def test_no_video_format_yields_nothing():
    formats = [_fmt("a1", "m4a", acodec="aac", height=0)]
    result = _select(_VIDEO_OPTS, formats)
    assert result == []


def test_empty_format_list_yields_nothing():
    result = _select(_VIDEO_OPTS, [])
    assert result == []
