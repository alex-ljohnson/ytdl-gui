"""Tests for modules.get_stats.GetStats."""
import os
from unittest.mock import patch

import pytest

from modules.get_stats import GetStats


@pytest.fixture
def sample_folder(tmp_path):
    for name in ["a.mp4", "b.mp4", "c.mp4", "d.mp4", "e.mp4"]:
        (tmp_path / name).write_bytes(b"")
    return tmp_path


def test_folder_length_processes_each_file_exactly_once(sample_folder):
    seen = []

    def fake_get_length(self, filename, video=True):
        seen.append(os.path.basename(filename))
        return 10.0

    with patch.object(GetStats, "get_length", fake_get_length):
        stats = GetStats(str(sample_folder), quiet=True, silent=True)
        result = stats.folder_length()

    assert sorted(seen) == ["a.mp4", "b.mp4", "c.mp4", "d.mp4", "e.mp4"]
    assert result["hours"] == 0
    assert result["minutes"] == 0
    assert result["seconds"] == 50
