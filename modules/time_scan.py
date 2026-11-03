"""Provides the window for time duration scans"""

import threading
from tkinter import messagebox
from tkinter.constants import END
from typing import TYPE_CHECKING

from modules.get_stats import GetStats
from modules.out_win import OutputWindow
from modules.utils import disable_insert, log_debug

if TYPE_CHECKING:
    from modules.application import Application


class TimeWindow(OutputWindow):
    """Window for time scans"""

    def __init__(
        self,
        master,
        title="New window",
        block=True,
        *,
        background: str | None = None,
        **kwargs,
    ):
        super().__init__(master, title, block, background=background, **kwargs)

        self.master: Application
        self.stats = GetStats(
            self.master.app_config["dir"],
            ffmpeg_custom=self.master.app_config["tools"]["ffmpeg"],
        )

    def start_scan(self):
        self.out_text.delete("1.0", END)
        print("Please be patient while the scan runs...")
        l = self.stats.folder_length()
        disable_insert(
            self.out_text,
            "1.0",
            f"Total folder duration for {self.master.app_config['dir']}:\n{l['hours']}hrs, {l['minutes']}mins, {l['seconds']}secs\n\nLogs:\n",
        )
        self.out_text.see("1.0")
        messagebox.showinfo(
            "Completed Duration Scan!",
            f"Total folder duration for {self.master.app_config['dir']}:\n{l['hours']}hrs, {l['minutes']}mins, {l['seconds']}secs",
            parent=self,
        )

    def win_close(self, event=None):
        super().win_close(event)
        self.master.time_window = None
        log_debug("[Window] Deleted time window")

    def task(self):
        self.thread = threading.Thread(target=self.start_scan)
        return super().task()
