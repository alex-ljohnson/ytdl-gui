"""Dependencies window, shows which external tools are in use and lets the user point at their own"""

import os
import platform
import sys
import threading
from dataclasses import dataclass
from tkinter import (
    Misc,
    StringVar,
    TclError,
    Toplevel,
    filedialog,
    font,
    messagebox,
    ttk,
)
from tkinter.constants import DISABLED, LEFT, NORMAL, W
from typing import TYPE_CHECKING

from yt_dlp.version import __version__ as YT_DLP_VERSION

from modules.tools import ResolvedTool, resolve_ffmpeg, resolve_js_runtime
from modules.utils import log_debug, relative_path

if TYPE_CHECKING:
    from modules.application import Application

TOOLS = {
    "ffmpeg": ("FFmpeg", resolve_ffmpeg),
    "js_runtime": ("JS runtime", resolve_js_runtime),
}
BROWSE_TITLES = {
    "ffmpeg": "Select ffmpeg.exe (ffprobe.exe must be in the same folder)",
    "js_runtime": "Select deno, bun, node or qjs",
}


@dataclass(frozen=True)
class ToolRow:
    """One line of the dependencies table, key is the config tools key or None when not configurable"""

    key: str | None
    label: str
    version: str
    source: str
    path: str


def tool_row(key: str, tool: ResolvedTool | None, custom: str) -> ToolRow:
    label = TOOLS[key][0]
    if tool is None:
        source = "not found (custom path unusable)" if custom else "not found"
        return ToolRow(key, label, "", source, "")
    version = tool.version or "unknown"
    if key == "js_runtime":
        version = f"{tool.name} {version}"
    source = tool.source
    if custom and tool.source != "custom":
        source = f"{tool.source} (custom path unusable)"
    return ToolRow(key, label, version, source, tool.path)


def resolve_rows(custom_paths: dict[str, str]) -> list[ToolRow]:
    """Resolve every tool, runs external processes so call it off the Tk thread"""
    rows = [ToolRow(None, "yt-dlp", YT_DLP_VERSION, "built in", "")]
    for key, (_, resolve) in TOOLS.items():
        custom = custom_paths[key]
        rows.append(tool_row(key, resolve(custom), custom))
    return rows


def diagnostics_text(app_version: str, rows: list[ToolRow]) -> str:
    frozen = bool(getattr(sys, "frozen", False))
    lines = [
        f"Youtube-dl GUI v{app_version}",
        f"OS: {platform.platform()}",
        f"Python: {platform.python_version()} ({'installed' if frozen else 'source'})",
        "",
    ]
    for row in rows:
        detail = " ".join(
            part for part in (row.version or "-", f"[{row.source}]", row.path) if part
        )
        lines.append(f"{row.label}: {detail}")
    return "\n".join(lines)


class DependenciesWindow(Toplevel):
    """Lists external tools with their version, where they came from and their path"""

    COLUMNS = ("Tool", "Version", "Source", "Path")

    def __init__(
        self, master: Misc | None = None, *, background: str | None = None
    ) -> None:
        super().__init__(master, background=background)  # type: ignore
        self.master: Application  # type: ignore
        self.title("Dependencies")
        self.iconbitmap(relative_path("Resources\\YTDLv2_256.ico"))
        self.protocol("WM_DELETE_WINDOW", self.win_close)
        self.rows: list[ToolRow] = []
        self._verify_key: str | None = None

        self.table = ttk.Frame(self)
        self.table.pack(padx=10, pady=10)
        bold = font.nametofont("TkDefaultFont").copy()
        bold.configure(weight="bold")
        for col, heading in enumerate(self.COLUMNS):
            ttk.Label(self.table, text=heading, font=bold).grid(
                row=0, column=col, sticky=W, padx=6, pady=(0, 4)
            )

        bottom = ttk.Frame(self)
        bottom.pack(fill="x", padx=10, pady=(0, 10))
        self.status = StringVar(self, value="Checking tools...")
        ttk.Label(bottom, textvariable=self.status, justify=LEFT).pack(side=LEFT)
        self.copy_btn = ttk.Button(
            bottom,
            text="Copy diagnostics",
            command=self.copy_diagnostics,
            state=DISABLED,
        )
        self.copy_btn.pack(side="right")
        self.refresh_btn = ttk.Button(
            bottom, text="Refresh", command=self.refresh, state=DISABLED
        )
        self.refresh_btn.pack(side="right", padx=6)
        self.refresh()

    def refresh(self):
        self.status.set("Checking tools...")
        self.refresh_btn.config(state=DISABLED)
        self.copy_btn.config(state=DISABLED)
        custom_paths = dict(self.master.app_config["tools"])
        threading.Thread(
            target=self._resolve, args=(custom_paths,), daemon=True
        ).start()

    def _resolve(self, custom_paths: dict[str, str]):
        rows = resolve_rows(custom_paths)
        try:
            self.after(0, self._show_rows, rows)
        except RuntimeError, TclError:
            log_debug("[Dependencies] Window closed before tools resolved")

    def _show_rows(self, rows: list[ToolRow]):
        if not self.winfo_exists():
            return
        self.rows = rows
        for child in self.table.grid_slaves():
            if int(child.grid_info()["row"]) > 0:
                child.destroy()
        for r, row in enumerate(rows, start=1):
            for col, text in enumerate((row.label, row.version, row.source, row.path)):
                ttk.Label(self.table, text=text or "-").grid(
                    row=r, column=col, sticky=W, padx=6, pady=2
                )
            if row.key is None:
                continue
            ttk.Button(
                self.table, text="Browse...", command=lambda k=row.key: self.browse(k)
            ).grid(row=r, column=4, padx=(12, 2))
            reset = ttk.Button(
                self.table, text="Reset", command=lambda k=row.key: self.reset(k)
            )
            reset.grid(row=r, column=5, padx=2)
            if not self.master.app_config["tools"][row.key]:
                reset.config(state=DISABLED)
        self.status.set("")
        self.refresh_btn.config(state=NORMAL)
        self.copy_btn.config(state=NORMAL)
        self._warn_if_unusable()

    def _warn_if_unusable(self):
        key, self._verify_key = self._verify_key, None
        row = next((r for r in self.rows if r.key == key), None)
        if row is None or row.source == "custom":
            return
        messagebox.showwarning(
            "Custom path not used",
            f"The selected {row.label} didn't run, so it isn't being used.\n\nCurrently using: {row.source}",
            parent=self,
        )

    def browse(self, key: str):
        path = filedialog.askopenfilename(
            parent=self,
            title=BROWSE_TITLES[key],
            filetypes=[("Programs", "*.exe"), ("All files", "*.*")],
        )
        if not path:
            return
        self.master.app_config["tools"][key] = os.path.abspath(path)
        self.master.write_config()
        self._verify_key = key
        self.refresh()

    def reset(self, key: str):
        self.master.app_config["tools"][key] = ""
        self.master.write_config()
        self.refresh()

    def copy_diagnostics(self):
        self.clipboard_clear()
        self.clipboard_append(diagnostics_text(self.master.app_version, self.rows))
        self.status.set("Copied to clipboard")

    def win_close(self):
        self.master.dependencies_window = None
        self.destroy()
