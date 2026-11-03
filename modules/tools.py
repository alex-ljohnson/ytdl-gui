"""Locates external tools (ffmpeg, ffprobe, JS runtimes)

Each lookup tries the user's custom path, then the system PATH, then the bundled copy,
and only accepts a candidate that actually runs
"""

import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass

from modules.utils import log_debug, relative_path

BUNDLED_FFMPEG_DIR = os.path.join("tools", "ffmpeg", "bin")
BUNDLED_QUICKJS = os.path.join("tools", "quickjs", "qjs.exe")
# executable name -> yt-dlp js_runtimes name, in priority order
JS_RUNTIMES = {"deno": "deno", "bun": "bun", "node": "node", "qjs": "quickjs"}
PROBE_TIMEOUT = 10

_VERSION_RE = re.compile(r"version\s+(\S+)|v?(\d+(?:\.\d+)+)", re.IGNORECASE)
_probe_cache: dict[tuple[str, float], tuple[bool, str | None]] = {}


@dataclass(frozen=True)
class ResolvedTool:
    """A tool that was found and runs

    path is the executable, except for ffmpeg where it is the directory holding both ffmpeg and ffprobe
    source is one of custom, system or bundled
    """

    name: str
    path: str
    source: str
    version: str | None


def run_tool(args: list[str], **kwargs) -> subprocess.CompletedProcess:
    """subprocess.run with no console window, no inherited stdin and captured UTF-8 output"""
    if sys.platform == "win32":
        kwargs.setdefault("creationflags", subprocess.CREATE_NO_WINDOW)
    return subprocess.run(
        args,
        stdin=subprocess.DEVNULL,
        capture_output=True,
        encoding="utf-8",
        errors="replace",
        **kwargs,
    )


def _version_args(path: str) -> list[str]:
    stem = os.path.splitext(os.path.basename(path))[0].lower()
    if stem in ("ffmpeg", "ffprobe"):
        return ["-version"]
    if stem == "qjs":
        # qjs has no --version, -h prints the version on its first line
        return ["-h"]
    return ["--version"]


def _parse_version(output: str) -> str | None:
    lines = output.strip().splitlines()
    if not lines:
        return None
    match = _VERSION_RE.search(lines[0])
    if match is None:
        return None
    return match.group(1) or match.group(2)


def probe(path: str) -> tuple[bool, str | None]:
    """Run the tool once to check it works and read its version, cached by path and mtime"""
    try:
        key = (os.path.abspath(path), os.path.getmtime(path))
    except OSError:
        return False, None
    cached = _probe_cache.get(key)
    if cached is not None:
        return cached
    try:
        result = run_tool([path, *_version_args(path)], timeout=PROBE_TIMEOUT)
        outcome = (True, _parse_version(result.stdout or result.stderr))
    except (OSError, subprocess.TimeoutExpired) as ex:
        log_debug(f"[Tools] {path} failed to run: {ex}")
        outcome = (False, None)
    _probe_cache[key] = outcome
    return outcome


def _which(name: str) -> str | None:
    """shutil.which that also reads the Windows registry PATH when inherited PATH misses an entry.

    winget (and some installers) write to the registry PATH without updating running processes.
    Checking the registry ensures we find tools installed after this process started.
    """
    result = shutil.which(name)
    if result:
        return result
    if sys.platform != "win32":
        return None
    try:
        import winreg

        reg_paths: list[str] = []
        for hive, subkey in [
            (
                winreg.HKEY_LOCAL_MACHINE,
                r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment",
            ),
            (winreg.HKEY_CURRENT_USER, r"Environment"),
        ]:
            try:
                with winreg.OpenKey(hive, subkey) as key:
                    value, _ = winreg.QueryValueEx(key, "Path")
                    reg_paths.append(winreg.ExpandEnvironmentStrings(value))
            except OSError:
                pass
        if reg_paths:
            return shutil.which(name, path=os.pathsep.join(reg_paths))
    except Exception:
        pass
    return None


def _exe_in(directory: str, name: str) -> str | None:
    return shutil.which(name, path=directory)


def _bundled_ffmpeg_dir() -> str | None:
    try:
        return relative_path(BUNDLED_FFMPEG_DIR)
    except FileNotFoundError:
        return None


def _bundled_quickjs() -> str | None:
    try:
        return relative_path(BUNDLED_QUICKJS)
    except FileNotFoundError:
        return None


def _ffmpeg_candidates(custom: str):
    if custom:
        yield "custom", custom if os.path.isdir(custom) else os.path.dirname(custom)
    system = _which("ffmpeg")
    if system:
        yield "system", os.path.dirname(system)
    bundled = _bundled_ffmpeg_dir()
    if bundled:
        yield "bundled", bundled


def _ffmpeg_pair(directory: str, source: str) -> ResolvedTool | None:
    ffmpeg = _exe_in(directory, "ffmpeg")
    ffprobe = _exe_in(directory, "ffprobe")
    if ffmpeg is None or ffprobe is None:
        log_debug(
            f"[FFmpeg] Skipping {source} {directory}, needs both ffmpeg and ffprobe"
        )
        return None
    ok, version = probe(ffmpeg)
    if not ok or not probe(ffprobe)[0]:
        return None
    return ResolvedTool("ffmpeg", directory, source, version)


def resolve_ffmpeg(custom: str = "") -> ResolvedTool | None:
    """Find a directory holding a working ffmpeg and ffprobe pair

    custom may be the directory or the path to ffmpeg itself
    """
    for source, directory in _ffmpeg_candidates(custom):
        tool = _ffmpeg_pair(directory, source)
        if tool is not None:
            log_debug(f"[FFmpeg] Using {source} {directory}")
            return tool
    log_debug("[FFmpeg] No ffmpeg found")
    return None


def _js_candidates(custom: str):
    if custom:
        yield "custom", custom
    for exe in JS_RUNTIMES:
        path = _which(exe)
        if path:
            yield "system", path
    bundled = _bundled_quickjs()
    if bundled:
        yield "bundled", bundled


def resolve_js_runtime(custom: str = "") -> ResolvedTool | None:
    """Find a working JS runtime for yt-dlp, preferring deno, bun, node then qjs"""
    for source, path in _js_candidates(custom):
        name = JS_RUNTIMES.get(os.path.splitext(os.path.basename(path))[0].lower())
        if name is None:
            log_debug(f"[JSRuntime] Skipping {source} {path}, not a supported runtime")
            continue
        ok, version = probe(path)
        if ok:
            log_debug(f"[JSRuntime] Using {source} {name} {path}")
            return ResolvedTool(name, path, source, version)
    log_debug("[JSRuntime] No JS runtime found")
    return None


def find_ffmpeg_dir(custom: str = "") -> str | None:
    """Return the directory for yt-dlp's ffmpeg_location, or None if no working pair was found"""
    tool = resolve_ffmpeg(custom)
    return tool.path if tool else None


def find_ffprobe(custom: str = "") -> str | None:
    """Return the path to ffprobe from the same directory as ffmpeg, or None"""
    tool = resolve_ffmpeg(custom)
    return _exe_in(tool.path, "ffprobe") if tool else None


def find_js_runtime(custom: str = "") -> str | None:
    """Return the yt-dlp js_runtimes specifier as name:path, or None if no runtime was found"""
    tool = resolve_js_runtime(custom)
    return f"{tool.name}:{tool.path}" if tool else None
