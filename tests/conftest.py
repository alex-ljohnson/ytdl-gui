"""Shared pytest fixtures for ytdl-gui unit tests."""
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest

# Make the repo root importable so `import modules.xxx` works.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


@pytest.fixture(autouse=True)
def _silence_tk(monkeypatch):
    """Replace Tk messagebox calls with no-ops for unit tests that touch GUI code paths."""
    import tkinter.messagebox as mb

    for name in ("showinfo", "showwarning", "showerror", "askyesno", "askyesnocancel"):
        monkeypatch.setattr(mb, name, MagicMock(return_value=True))
