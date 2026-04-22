"""Tests for StdoutRedirect and StderrRedirect."""
import sys
from tkinter import TclError
from unittest.mock import MagicMock

import pytest

from modules.redirects import StderrRedirect, StdoutRedirect


def _mock_text():
    return MagicMock()


# ---------------------------------------------------------------------------
# StdoutRedirect
# ---------------------------------------------------------------------------

class TestStdoutRedirect:
    def test_init_replaces_stdout(self):
        t = _mock_text()
        saved = sys.stdout
        redir = StdoutRedirect(t)
        try:
            assert sys.stdout is redir
        finally:
            redir.close()

    def test_close_restores_stdout(self):
        saved = sys.stdout
        redir = StdoutRedirect(_mock_text())
        redir.close()
        assert sys.stdout is saved

    def test_close_is_idempotent(self):
        saved = sys.stdout
        redir = StdoutRedirect(_mock_text())
        redir.close()
        redir.close()
        assert sys.stdout is saved

    def test_write_calls_text_insert(self):
        t = _mock_text()
        redir = StdoutRedirect(t)
        try:
            redir.write("hello")
            t.insert.assert_called()
        finally:
            redir.close()

    def test_write_carriage_return_deletes_current_line(self):
        t = _mock_text()
        redir = StdoutRedirect(t)
        try:
            redir.write("\rhello")
            t.delete.assert_called_once()
        finally:
            redir.close()

    def test_isatty_interactive(self):
        redir = StdoutRedirect(_mock_text(), interactive=True)
        try:
            assert redir.isatty() is True
        finally:
            redir.close()

    def test_isatty_non_interactive(self):
        redir = StdoutRedirect(_mock_text(), interactive=False)
        try:
            assert redir.isatty() is False
        finally:
            redir.close()

    def test_writelines_joins_and_inserts(self):
        t = _mock_text()
        redir = StdoutRedirect(t)
        try:
            redir.writelines(["line1", "line2"])
            t.insert.assert_called()
        finally:
            redir.close()

    def test_tclerror_falls_back_and_closes(self):
        t = _mock_text()
        t.config.side_effect = TclError("bad window path")
        saved = sys.stdout
        redir = StdoutRedirect(t)
        redir.write("hello")
        assert sys.stdout is saved
        assert not redir.open

    def test_flush_does_not_raise(self):
        redir = StdoutRedirect(_mock_text())
        try:
            redir.flush()
        finally:
            redir.close()


# ---------------------------------------------------------------------------
# StderrRedirect
# ---------------------------------------------------------------------------

class TestStderrRedirect:
    def test_init_replaces_stderr(self):
        saved = sys.stderr
        redir = StderrRedirect(_mock_text())
        try:
            assert sys.stderr is redir
        finally:
            redir.close()

    def test_close_restores_stderr(self):
        saved = sys.stderr
        redir = StderrRedirect(_mock_text())
        redir.close()
        assert sys.stderr is saved

    def test_close_is_idempotent(self):
        saved = sys.stderr
        redir = StderrRedirect(_mock_text())
        redir.close()
        redir.close()
        assert sys.stderr is saved

    def test_write_calls_text_insert(self):
        t = _mock_text()
        redir = StderrRedirect(t)
        try:
            redir.write("error msg")
            t.insert.assert_called()
        finally:
            redir.close()

    def test_main_thread_tclerror_silently_returns_no_close(self):
        t = _mock_text()
        t.config.side_effect = TclError("main thread is not in main loop")
        redir = StderrRedirect(t)
        redir.write("some error")
        assert sys.stderr is redir
        assert redir.open
        redir.close()

    def test_other_tclerror_falls_back_and_closes(self):
        t = _mock_text()
        t.config.side_effect = TclError("application has been destroyed")
        saved = sys.stderr
        redir = StderrRedirect(t)
        redir.write("error")
        assert sys.stderr is saved
        assert not redir.open
