"""Tests for Updater.check_update."""
import pytest
import requests
from unittest.mock import MagicMock, patch

from modules.update import Updater


def _make_updater(version="1.0.0"):
    u = Updater.__new__(Updater)
    u.app_version = version
    u.master = MagicMock()
    u.open_window = None
    return u


def _ok_response(tag):
    r = MagicMock()
    r.status_code = 200
    r.raise_for_status.return_value = None
    r.json.return_value = {"tag_name": tag}
    return r


# ---------------------------------------------------------------------------
# Normal update paths
# ---------------------------------------------------------------------------

def test_newer_version_returns_true():
    u = _make_updater("1.0.0")
    u.open_update_window = MagicMock()
    with patch("modules.update.requests.get", return_value=_ok_response("v2.0.0")):
        result = u.check_update()
    assert result is True
    u.open_update_window.assert_called_once_with("v2.0.0")


def test_same_version_quiet_returns_false_no_messagebox():
    import tkinter.messagebox as mb
    u = _make_updater("1.0.0")
    with patch("modules.update.requests.get", return_value=_ok_response("v1.0.0")):
        result = u.check_update(quiet=True)
    assert result is False
    mb.showinfo.assert_not_called()


def test_same_version_not_quiet_shows_info():
    import tkinter.messagebox as mb
    u = _make_updater("1.0.0")
    with patch("modules.update.requests.get", return_value=_ok_response("v1.0.0")):
        result = u.check_update(quiet=False)
    assert result is False
    mb.showinfo.assert_called()


def test_older_version_preview_user_accepts_returns_true():
    """Running a preview build; user clicks Yes to install the last release."""
    u = _make_updater("2.0.0")
    u.open_update_window = MagicMock()
    # askyesno is already mocked to True by _silence_tk autouse fixture
    with patch("modules.update.requests.get", return_value=_ok_response("v1.0.0")):
        result = u.check_update(quiet=False)
    assert result is True
    u.open_update_window.assert_called_once()


def test_older_version_preview_quiet_returns_false():
    u = _make_updater("2.0.0")
    with patch("modules.update.requests.get", return_value=_ok_response("v1.0.0")):
        result = u.check_update(quiet=True)
    assert result is False


# ---------------------------------------------------------------------------
# Error paths
# ---------------------------------------------------------------------------

def test_network_error_returns_none():
    u = _make_updater("1.0.0")
    with patch("modules.update.requests.get", side_effect=requests.RequestException("timeout")):
        result = u.check_update()
    assert result is None


def test_404_returns_none():
    r = MagicMock()
    r.status_code = 404
    u = _make_updater("1.0.0")
    with patch("modules.update.requests.get", return_value=r):
        result = u.check_update()
    assert result is None


def test_invalid_tag_format_returns_none():
    # Tag "v1.0" vs app version "1.0.0" — different segment count → ValueError in version_compare
    u = _make_updater("1.0.0")
    with patch("modules.update.requests.get", return_value=_ok_response("v1.0")):
        result = u.check_update()
    assert result is None