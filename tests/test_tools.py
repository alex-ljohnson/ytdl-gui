"""Tests for modules.tools, external tool discovery."""

import os
import subprocess
import sys
from types import SimpleNamespace

import pytest

from modules import tools
from modules.tools import (
    ResolvedTool,
    find_ffmpeg_dir,
    find_ffprobe,
    find_js_runtime,
    probe,
    resolve_ffmpeg,
    resolve_js_runtime,
)


@pytest.fixture(autouse=True)
def _clear_probe_cache():
    tools._probe_cache.clear()
    yield
    tools._probe_cache.clear()


@pytest.fixture
def fake_tools(monkeypatch):
    """Fake filesystem of tool dirs, PATH lookups and probe results

    dirs maps a directory to the executables in it, path maps a name to its PATH hit,
    broken holds executables whose probe fails
    """
    state = SimpleNamespace(
        dirs={}, path={}, broken=set(), bundled_ffmpeg=None, bundled_qjs=None
    )

    def exe_in(directory, name):
        return (
            os.path.join(directory, name)
            if name in state.dirs.get(directory, ())
            else None
        )

    monkeypatch.setattr(tools, "_exe_in", exe_in)
    monkeypatch.setattr(tools, "_which", lambda name: state.path.get(name))
    monkeypatch.setattr(tools, "_bundled_ffmpeg_dir", lambda: state.bundled_ffmpeg)
    monkeypatch.setattr(tools, "_bundled_quickjs", lambda: state.bundled_qjs)
    monkeypatch.setattr(tools, "probe", lambda path: (path not in state.broken, "1.0"))
    return state


class TestResolveFfmpeg:
    def test_custom_dir_takes_priority(self, fake_tools, tmp_path):
        custom = str(tmp_path)
        fake_tools.dirs = {
            custom: {"ffmpeg", "ffprobe"},
            "/usr/bin": {"ffmpeg", "ffprobe"},
        }
        fake_tools.path = {"ffmpeg": "/usr/bin/ffmpeg"}
        assert resolve_ffmpeg(custom) == ResolvedTool("ffmpeg", custom, "custom", "1.0")

    def test_custom_exe_path_uses_its_dir(self, fake_tools, tmp_path):
        exe = tmp_path / "ffmpeg.exe"
        exe.write_bytes(b"")
        fake_tools.dirs = {str(tmp_path): {"ffmpeg", "ffprobe"}}
        assert resolve_ffmpeg(str(exe)).path == str(tmp_path)

    def test_system_used_when_no_custom(self, fake_tools):
        fake_tools.dirs = {"/usr/bin": {"ffmpeg", "ffprobe"}}
        fake_tools.path = {"ffmpeg": "/usr/bin/ffmpeg"}
        fake_tools.bundled_ffmpeg = "/bundled/bin"
        assert resolve_ffmpeg().source == "system"

    def test_system_without_ffprobe_falls_back_to_bundled(self, fake_tools):
        fake_tools.dirs = {
            "/usr/bin": {"ffmpeg"},
            "/bundled/bin": {"ffmpeg", "ffprobe"},
        }
        fake_tools.path = {"ffmpeg": "/usr/bin/ffmpeg"}
        fake_tools.bundled_ffmpeg = "/bundled/bin"
        assert resolve_ffmpeg() == ResolvedTool(
            "ffmpeg", "/bundled/bin", "bundled", "1.0"
        )

    def test_broken_custom_falls_back_to_system(self, fake_tools, tmp_path):
        custom = str(tmp_path)
        fake_tools.dirs = {
            custom: {"ffmpeg", "ffprobe"},
            "/usr/bin": {"ffmpeg", "ffprobe"},
        }
        fake_tools.path = {"ffmpeg": "/usr/bin/ffmpeg"}
        fake_tools.broken = {os.path.join(custom, "ffmpeg")}
        assert resolve_ffmpeg(custom).source == "system"

    def test_broken_ffprobe_skips_pair(self, fake_tools):
        fake_tools.dirs = {
            "/usr/bin": {"ffmpeg", "ffprobe"},
            "/bundled/bin": {"ffmpeg", "ffprobe"},
        }
        fake_tools.path = {"ffmpeg": "/usr/bin/ffmpeg"}
        fake_tools.bundled_ffmpeg = "/bundled/bin"
        fake_tools.broken = {os.path.join("/usr/bin", "ffprobe")}
        assert resolve_ffmpeg().source == "bundled"

    def test_nothing_found_returns_none(self, fake_tools):
        assert resolve_ffmpeg() is None
        assert find_ffmpeg_dir() is None
        assert find_ffprobe() is None

    def test_find_wrappers_use_the_same_dir(self, fake_tools):
        fake_tools.dirs = {"/usr/bin": {"ffmpeg", "ffprobe"}}
        fake_tools.path = {"ffmpeg": "/usr/bin/ffmpeg"}
        assert find_ffmpeg_dir() == "/usr/bin"
        assert find_ffprobe() == os.path.join("/usr/bin", "ffprobe")


# ---------------------------------------------------------------------------
# resolve_js_runtime
# ---------------------------------------------------------------------------


class TestResolveJsRuntime:
    @pytest.mark.parametrize(
        "on_path,expected",
        [
            ({"deno", "bun", "node", "qjs"}, "deno"),
            ({"bun", "node", "qjs"}, "bun"),
            ({"node", "qjs"}, "node"),
            ({"qjs"}, "quickjs"),
        ],
    )
    def test_priority_order(self, fake_tools, on_path, expected):
        fake_tools.path = {name: f"/usr/bin/{name}" for name in on_path}
        assert resolve_js_runtime().name == expected

    def test_custom_takes_priority(self, fake_tools):
        fake_tools.path = {"deno": "/usr/bin/deno"}
        tool = resolve_js_runtime("/opt/node/node.exe")
        assert tool == ResolvedTool("node", "/opt/node/node.exe", "custom", "1.0")

    def test_unsupported_custom_is_skipped(self, fake_tools):
        fake_tools.path = {"deno": "/usr/bin/deno"}
        assert resolve_js_runtime("/opt/python3").name == "deno"

    def test_broken_runtime_is_skipped(self, fake_tools):
        fake_tools.path = {"deno": "/usr/bin/deno", "node": "/usr/bin/node"}
        fake_tools.broken = {"/usr/bin/deno"}
        assert resolve_js_runtime().name == "node"

    def test_falls_back_to_bundled_quickjs(self, fake_tools):
        fake_tools.bundled_qjs = "/app/tools/quickjs/qjs.exe"
        tool = resolve_js_runtime()
        assert (tool.name, tool.source) == ("quickjs", "bundled")
        assert find_js_runtime() == "quickjs:/app/tools/quickjs/qjs.exe"

    def test_find_js_runtime_includes_system_path(self, fake_tools):
        fake_tools.path = {"deno": "/usr/bin/deno"}
        assert find_js_runtime() == "deno:/usr/bin/deno"

    def test_nothing_found_returns_none(self, fake_tools):
        assert resolve_js_runtime() is None
        assert find_js_runtime() is None


class TestProbe:
    def _fake_run(self, monkeypatch, output="ffmpeg version 7.1 Copyright", exc=None):
        calls = []

        def run_tool(args, **kwargs):
            calls.append(args)
            if exc is not None:
                raise exc
            return SimpleNamespace(stdout=output, stderr="")

        monkeypatch.setattr(tools, "run_tool", run_tool)
        return calls

    def test_reads_version_and_caches(self, monkeypatch, tmp_path):
        exe = tmp_path / "ffmpeg.exe"
        exe.write_bytes(b"")
        calls = self._fake_run(monkeypatch)
        assert probe(str(exe)) == (True, "7.1")
        assert probe(str(exe)) == (True, "7.1")
        assert calls == [[str(exe), "-version"]]

    def test_reprobes_when_file_changes(self, monkeypatch, tmp_path):
        exe = tmp_path / "deno.exe"
        exe.write_bytes(b"")
        calls = self._fake_run(monkeypatch, output="deno 2.1.4 (stable)")
        probe(str(exe))
        os.utime(exe, (1, 1))
        probe(str(exe))
        assert len(calls) == 2

    def test_failure_to_run_is_cached(self, monkeypatch, tmp_path):
        exe = tmp_path / "node.exe"
        exe.write_bytes(b"")
        calls = self._fake_run(monkeypatch, exc=OSError("bad exe"))
        assert probe(str(exe)) == (False, None)
        assert probe(str(exe)) == (False, None)
        assert len(calls) == 1

    def test_timeout_counts_as_failure(self, monkeypatch, tmp_path):
        exe = tmp_path / "bun.exe"
        exe.write_bytes(b"")
        self._fake_run(monkeypatch, exc=subprocess.TimeoutExpired("bun", 10))
        assert probe(str(exe)) == (False, None)

    def test_missing_file_fails_without_running(self, monkeypatch, tmp_path):
        calls = self._fake_run(monkeypatch)
        assert probe(str(tmp_path / "ghost.exe")) == (False, None)
        assert calls == []

    def test_qjs_probed_with_help(self, monkeypatch, tmp_path):
        exe = tmp_path / "qjs.exe"
        exe.write_bytes(b"")
        calls = self._fake_run(
            monkeypatch, output="QuickJS version 2025-09-13\nusage: qjs"
        )
        assert probe(str(exe)) == (True, "2025-09-13")
        assert calls == [[str(exe), "-h"]]


@pytest.mark.parametrize(
    "output,expected",
    [
        (
            "ffmpeg version 7.1-essentials_build-www.gyan.dev Copyright (c) 2000-2024",
            "7.1-essentials_build-www.gyan.dev",
        ),
        ("deno 2.1.4 (stable, release, x86_64-pc-windows-msvc)\nv8 13.0", "2.1.4"),
        ("v22.11.0\n", "22.11.0"),
        ("1.1.38", "1.1.38"),
        ("QuickJS version 2025-09-13", "2025-09-13"),
        ("", None),
        ("no digits here", None),
    ],
)
def test_parse_version(output, expected):
    assert tools._parse_version(output) == expected


def test_run_tool_detaches_stdin_and_captures_utf8(monkeypatch):
    captured = {}
    monkeypatch.setattr(
        subprocess, "run", lambda args, **kw: captured.update(kw, args=args)
    )
    tools.run_tool(["ffprobe", "-v"], check=True)
    assert captured["args"] == ["ffprobe", "-v"]
    assert captured["stdin"] is subprocess.DEVNULL
    assert captured["capture_output"] is True
    assert captured["encoding"] == "utf-8"
    assert captured["check"] is True


@pytest.mark.skipif(sys.platform != "win32", reason="CREATE_NO_WINDOW is Windows-only")
def test_run_tool_hides_console_on_windows(monkeypatch):
    captured = {}
    monkeypatch.setattr(subprocess, "run", lambda args, **kw: captured.update(kw))
    tools.run_tool(["ffprobe"])
    assert captured["creationflags"] == subprocess.CREATE_NO_WINDOW


class TestBundled:
    def test_ffmpeg_dir_found(self, monkeypatch):
        monkeypatch.setattr(tools, "relative_path", lambda p, **kw: "/app/" + p)
        assert tools._bundled_ffmpeg_dir() == "/app/" + os.path.join(
            "tools", "ffmpeg", "bin"
        )

    def test_quickjs_found(self, monkeypatch):
        monkeypatch.setattr(tools, "relative_path", lambda p, **kw: "/app/" + p)
        assert tools._bundled_quickjs() == "/app/" + os.path.join(
            "tools", "quickjs", "qjs.exe"
        )

    def test_missing_returns_none(self, monkeypatch):
        def _raise(p, **kw):
            raise FileNotFoundError

        monkeypatch.setattr(tools, "relative_path", _raise)
        assert tools._bundled_ffmpeg_dir() is None
        assert tools._bundled_quickjs() is None


def test_real_bundled_tools_resolve_on_windows():
    """The committed binaries under tools/ resolve as the bundled fallback from the repo root"""
    if sys.platform != "win32":
        pytest.skip("bundled binaries are Windows executables")
    if not os.path.isdir(os.path.join("tools", "ffmpeg", "bin")):
        pytest.skip("run from the repo root")
    assert tools._bundled_ffmpeg_dir() is not None
    assert tools._bundled_quickjs() is not None
