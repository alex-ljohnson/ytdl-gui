"""Static utility functions for the program"""

import os
import shutil
import sys
from tkinter import DISABLED, NORMAL, Text

from modules import constants


def link(url):
    os.startfile(url)


def log_debug(value: object, default_stdout: bool = True):
    if constants.DEBUG:
        if default_stdout:
            constants.STDOUT_DEF.write(f"{value}\n")
        else:
            print(value)


def version_compare(ver1: str, ver2: str) -> str:
    def _parts(v: str) -> list:
        out = []
        for token in v.lstrip("v").split("."):
            try:
                out.append((0, int(token)))
            except ValueError:
                out.append((1, token))
        return out

    a, b = _parts(ver1), _parts(ver2)
    if len(a) != len(b):
        raise ValueError(f"Version formats of {ver1} and {ver2} aren't the same.")
    if a > b:
        return ">"
    if a < b:
        return "<"
    return "="


# def add_to_queue(l: list, value: Any):
#     l.pop(0)
#     l.append(value)


def disable_insert(text: Text, index, chars, *args):
    text.config(state=NORMAL)
    text.insert(index, chars, args)
    text.config(state=DISABLED)


def relative_path(path: str, create: bool = False, unbundled_prefix: str = "", bundled_prefix: str = ""):
    try:
        base = os.path.abspath(os.path.join(sys._MEIPASS, bundled_prefix))  # type: ignore # pylint: disable=protected-access
        res = os.path.abspath(os.path.join(base, path))
    except (AttributeError, TypeError):
        base = os.path.abspath(os.path.join(os.path.abspath("."), unbundled_prefix))
        res = os.path.abspath(os.path.join(base, path))
    if not os.path.exists(res):
        if create:
            os.makedirs(res, exist_ok=True)
        else:
            raise FileNotFoundError(f"File {res} isn't an existing local file.")
    log_debug(f"[File] Path {str(res)} found")
    return res


def relative_data(path: str, should_exist: bool = True):
    base = constants.DATA_PATH
    res = os.path.abspath(os.path.join(base, path))
    if not os.path.exists(res) and should_exist:
        raise FileNotFoundError(f"File {res} isn't an existing data file.")
    log_debug(f"[File] Path {str(res)} found")
    return res


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
            (winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"),
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


def _bundled_ffmpeg_dir() -> str | None:
    try:
        probe = relative_path(os.path.join("ffmpeg-7.1-essentials_build", "bin", "ffprobe.exe"))
        return os.path.dirname(probe)
    except FileNotFoundError:
        return None


def find_ffprobe() -> str | None:
    """Return the absolute path to ffprobe, or None if not found.

    Checks system PATH first, then the bundled build.
    """
    which = _which("ffprobe")
    if which:
        return which
    d = _bundled_ffmpeg_dir()
    if d:
        return os.path.join(d, "ffprobe.exe")
    return None


def find_ffmpeg_dir() -> str | None:
    """Return the ffmpeg directory for yt-dlp's ffmpeg_location.

    Returns None when ffmpeg is on PATH (yt-dlp will use PATH automatically).
    Returns the bundled build directory otherwise.
    """
    path = _which("ffmpeg")
    if path:
        log_debug("[FFmpeg] Using system PATH")
        return None
    d = _bundled_ffmpeg_dir()
    if d:
        log_debug(f"[FFmpeg] Using bundled build: {d}")
        return d
    log_debug("[FFmpeg] No ffmpeg found")
    return None


def _bundled_quickjs() -> str | None:
    try:
        return relative_path(os.path.join("quickjs", "qjs.exe"))
    except FileNotFoundError:
        return None


def find_js_runtime() -> str | None:
    """Return the JS runtime specifier for yt-dlp, or None if not found.

    Checks system PATH in priority order (deno → bun → node → qjs),
    then falls back to the bundled QuickJS build. Returns ``"quickjs:path"``
    for the bundled case so yt-dlp can locate the executable.
    """
    for name in ("deno", "bun", "node", "qjs"):
        if shutil.which(name):
            log_debug(f"[JSRuntime] Using system {name}")
            return name if name != "qjs" else "quickjs"
    path = _bundled_quickjs()
    if path:
        log_debug(f"[JSRuntime] Using bundled QuickJS: {path}")
        return f"quickjs:{path}"
    log_debug("[JSRuntime] No JS runtime found")
    return None
