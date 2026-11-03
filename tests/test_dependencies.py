"""Tests for the pure helpers in modules.dependencies."""

import pytest

from modules import dependencies
from modules.dependencies import ToolRow, diagnostics_text, resolve_rows, tool_row
from modules.tools import ResolvedTool


class TestToolRow:
    def test_not_found(self):
        assert tool_row("ffmpeg", None, "") == ToolRow(
            "ffmpeg", "FFmpeg", "", "not found", ""
        )

    def test_not_found_with_bad_custom(self):
        row = tool_row("ffmpeg", None, "/bad/ffmpeg.exe")
        assert row.source == "not found (custom path unusable)"

    def test_custom_in_use(self):
        tool = ResolvedTool("ffmpeg", "/opt/ffmpeg", "custom", "7.1")
        assert tool_row("ffmpeg", tool, "/opt/ffmpeg") == ToolRow(
            "ffmpeg", "FFmpeg", "7.1", "custom", "/opt/ffmpeg"
        )

    def test_custom_unusable_falls_back(self):
        tool = ResolvedTool("ffmpeg", "/usr/bin", "system", "9.0")
        assert (
            tool_row("ffmpeg", tool, "/bad").source == "system (custom path unusable)"
        )

    def test_js_runtime_version_names_the_runtime(self):
        tool = ResolvedTool("bun", "/usr/bin/bun", "system", "1.3.14")
        assert tool_row("js_runtime", tool, "").version == "bun 1.3.14"

    def test_unknown_version(self):
        tool = ResolvedTool("ffmpeg", "/usr/bin", "system", None)
        assert tool_row("ffmpeg", tool, "").version == "unknown"


def test_resolve_rows_passes_custom_paths(monkeypatch):
    seen = {}

    def fake(key):
        def resolve(custom):
            seen[key] = custom

        return resolve

    monkeypatch.setattr(
        dependencies,
        "TOOLS",
        {
            "ffmpeg": ("FFmpeg", fake("ffmpeg")),
            "js_runtime": ("JS runtime", fake("js_runtime")),
        },
    )
    monkeypatch.setattr(dependencies, "YT_DLP_VERSION", "2026.10.01")
    rows = resolve_rows({"ffmpeg": "/opt/ffmpeg", "js_runtime": ""})
    assert seen == {"ffmpeg": "/opt/ffmpeg", "js_runtime": ""}
    assert rows[0] == ToolRow(None, "yt-dlp", "2026.10.01", "built in", "")
    assert [r.key for r in rows] == [None, "ffmpeg", "js_runtime"]


def test_diagnostics_text_lists_app_and_tools(monkeypatch):
    monkeypatch.setattr(
        dependencies.platform, "platform", lambda: "Windows-11-10.0.26300-SP0"
    )
    rows = [
        ToolRow(None, "yt-dlp", "2026.10.01", "built in", ""),
        ToolRow("ffmpeg", "FFmpeg", "9.0", "system", r"C:\ffmpeg\bin"),
        ToolRow("js_runtime", "JS runtime", "", "not found", ""),
    ]
    text = diagnostics_text("2026.04.22.f8", rows)
    lines = text.splitlines()
    assert lines[0] == "Youtube-dl GUI v2026.04.22.f8"
    assert lines[1] == "OS: Windows-11-10.0.26300-SP0"
    assert "yt-dlp: 2026.10.01 [built in]" in lines
    assert r"FFmpeg: 9.0 [system] C:\ffmpeg\bin" in lines
    assert "JS runtime: - [not found]" in lines


@pytest.mark.parametrize("key", list(dependencies.TOOLS))
def test_every_configurable_tool_has_config_default_and_browse_title(key):
    from modules.constants import DEFAULT_CONFIG

    assert key in DEFAULT_CONFIG["tools"]
    assert key in dependencies.BROWSE_TITLES
