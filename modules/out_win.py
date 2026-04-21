"""Provides output window class"""

import threading
from tkinter import Misc, StringVar, Text, Toplevel, font, messagebox, ttk
from tkinter.constants import BOTH, DISABLED, FLAT, RIGHT, TOP, W, Y
from typing import TYPE_CHECKING

# from DownloaderGUI import Application
from modules.redirects import StderrRedirect, StdoutRedirect
from modules.utils import log_debug, relative_path

if TYPE_CHECKING:
    from modules.application import Application


class OutputWindow(Toplevel):
    """Defines a window to which outputs can be written."""

    def __init__(
        self,
        master: Misc | None = None,
        title="New window",
        block=True,
        *,
        background: str = "white",
        **kwargs,
    ) -> None:
        super().__init__(master, background=background, **kwargs)
        self.master: Application  # type: ignore
        self.thread: threading.Thread | None = None
        self.title(title)
        self.iconbitmap(relative_path("Resources\\YTDLv2_256.ico"))

        self.block = block
        text_frm = ttk.Frame(self)
        y_scroll = ttk.Scrollbar(text_frm)
        self.out_text = Text(
            text_frm,
            font=self.master.curr_font,
            yscrollcommand=y_scroll.set,
            relief=FLAT,
            state=DISABLED,
        )
        y_scroll.config(command=self.out_text.yview)
        text_frm.pack(side=TOP, expand=True, fill=BOTH)
        y_scroll.pack(fill=Y, side=RIGHT)
        self.out_text.pack(expand=True, fill=BOTH)

        progress_frm = ttk.Frame(self)
        self.progress = ttk.Progressbar(progress_frm, length=600, mode="determinate", maximum=1, value=0)
        self.progress.grid(column=0, row=0, padx=3, sticky=W)
        self.stat_string = StringVar(progress_frm, value="0MiB/0MiB @ 0MiB/s")
        ttk.Label(progress_frm, textvariable=self.stat_string, font=font.Font(size=14)).grid(column=1, row=0, padx=3)
        self.info = StringVar(progress_frm, value="0 / 0 Completed")
        ttk.Label(progress_frm, textvariable=self.info, font=font.Font(size=14)).grid(column=0, row=1, sticky=W)
        self.percent = StringVar(progress_frm, value=f"{self.progress['value']*100}%")
        ttk.Label(progress_frm, font=font.Font(size=10), textvariable=self.percent).grid(column=0, row=0)
        progress_frm.pack(side=TOP, pady=7.5)

        if self.master.app_config["prefs"]["print_log"]:
            self.out_redir = StdoutRedirect(self.out_text, interactive=False)
            self.err_redir = StderrRedirect(self.out_text, interactive=False)

        self.protocol("WM_DELETE_WINDOW", self.win_close)
        self.focus_set()
        self.grab_set()

    def win_close(self, event=None):
        if self.master.running and self.block:
            messagebox.showerror(
                "Cannot close",
                "Unable to close window while download is in progress.",
                parent=self,
            )
            return
        self.grab_release()
        for attr in ("out_redir", "err_redir"):
            redir = getattr(self, attr, None)
            if redir is not None:
                redir.close()
        self.master.focus_set()
        self.destroy()
        log_debug("[Outwin] Closed")

    def task(self):
        if self.thread is not None:
            self.thread.start()
