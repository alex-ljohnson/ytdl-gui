"""Provides classes & functionality for the programs auto updater"""
import os
import threading
from tkinter import Misc, StringVar, TclError, Toplevel, messagebox, ttk
from tkinter.constants import BOTTOM, CENTER, DISABLED, LEFT, NORMAL, X
from typing import TYPE_CHECKING, Callable

import requests

from modules.constants import BACKGROUNDS
from modules.utils import relative_path, version_compare

if TYPE_CHECKING:
    from modules.application import Application


class Updater:
    """Logic and networking to download and install the new update"""

    def __init__(self, my_version, master: Misc | None = None) -> None:
        self.app_version = my_version
        self.master: Application = master
        self.open_window: UpdateWindow | None = None

    def check_update(self, quiet: bool = False):
        try:
            latest = requests.get(
                "https://api.github.com/repos/MrTransparentBox/ytdl-gui/releases/latest",
                headers={
                    "accept": "application/vnd.github.v3+json",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
                timeout=60,
            )
            if latest.status_code == 404:
                messagebox.showinfo(
                    "No releases found",
                    "There are no releases for this program.\nIf you think this is an error please report it.",
                    parent=self.master,
                )
                return None
            latest.raise_for_status()
            tag = latest.json()["tag_name"]
        except (TimeoutError, requests.RequestException) as ex:
            messagebox.showerror(
                "Unable to check for update",
                f"{ex}\n\nTry checking your internet connection, and try again.",
                parent=self.master,
            )
            return None
        comp = version_compare(tag, f"v{self.app_version}")
        if comp == "=":
            if not quiet:
                messagebox.showinfo("Up-to-date", "No updates found", parent=self.master)
            return False
        if comp == ">":
            messagebox.showinfo("Update available!", f"New version found: {tag}", parent=self.master)
            self.open_update_window(tag)
            return True
        if comp == "<" and not quiet:
            ans = messagebox.askyesno(
                "Preview",
                "Looks like you have a special preview or pre-release version! "
                "Do you want to install the last full release?",
                parent=self.master,
            )
            if ans:
                self.open_update_window(tag)
                return True
        return False

    def open_update_window(self, version_tag):
        self.open_window = UpdateWindow(
            version_tag,
            self.start_update,
            self.master,
            background=BACKGROUNDS[self.master.app_config["prefs"]["theme"]],
        )

    def start_update(self):
        filename = self.download_setup()
        if filename is None:
            return
        if self.open_window is not None:
            self.open_window.destroy()
        self.open_window = None
        os.execv(
            filename,
            [
                filename,
                "/NOCANCEL",
                "/RESTARTAPPLICATIONS",
                "/SP-",
                "/SILENT",
                "/NOICONS",
                "/DIR=expand:{autopf}\\Youtube-dl GUI",
            ],
        )

    def download_setup(self):
        with requests.Session() as s:
            response = s.get(
                "https://github.com/MrTransparentBox/ytdl-gui/releases/latest/download/Youtube-dl_GUI_Setup.exe",
                headers={
                    "Accept": "application/octet-stream",
                    "X-GitHub-Api-Version": "2022-11-28",
                },
                stream=True,
            )
            try:
                response.raise_for_status()
            except requests.HTTPError as e:
                messagebox.showerror("HTTP Error occurred", str(e), parent=self.master)
                return None

            tmp_dir = os.environ.get("TEMP") or os.environ.get("TMP") or os.path.expandvars("%tmp%")
            cd = response.headers.get("content-disposition", "")
            if "filename=" in cd:
                name = cd[cd.index("filename=") + len("filename=") :].strip('"')
            else:
                name = "Youtube-dl_GUI_Setup.exe"
            filename = os.path.join(tmp_dir, name)

            length = response.headers.get("content-length")
            try:
                length = int(length) if length else None
            except ValueError:
                length = None
            downloaded = 0

            try:
                with open(filename, "wb") as f:
                    for data in response.iter_content(chunk_size=524288):
                        downloaded += len(data)
                        f.write(data)
                        if self.open_window is None:
                            continue
                        if length:
                            pct = downloaded / length
                            self.open_window.after(
                                0,
                                lambda p=pct: (
                                    self.open_window.progress.configure(value=p),
                                    self.open_window.progress_text.set(f"Downloaded: {round(p * 100, 1)}%"),
                                ),
                            )
                        else:
                            self.open_window.after(
                                0,
                                lambda d=downloaded: self.open_window.progress_text.set(f"Downloaded: {d} bytes"),
                            )
            except (TclError, AttributeError):
                return None
        return filename


class UpdateWindow(Toplevel):
    """Basic window to display new version info"""

    def __init__(
        self, version_tag, update_function: Callable, master: Misc | None = None, *, background: str = ...
    ) -> None:
        super().__init__(master, background=background)
        self.update_function = update_function
        self.master: Application
        self.iconbitmap(relative_path("Resources\\YTDLv2_256.ico"))
        self.title("Youtube-dl GUI - Update")
        ttk.Label(
            self,
            text="A new version of Youtube-dl GUI is available!\nAn update is recommended.",
            justify=LEFT,
        ).pack(padx=5, pady=5)
        ttk.Label(
            self,
            text=f"\tNew version: {version_tag}\n\tYour Version: v{self.master.app_version}",
            justify=LEFT,
        ).pack(pady=10)
        ttk.Label(
            self,
            text="Click update to download the new version.",
            justify=LEFT,
        ).pack()
        update_thread = threading.Thread(target=self.start_update)
        self.update_btn = ttk.Button(self, text="Update", command=update_thread.start)
        self.update_btn.pack(side=BOTTOM, pady=15)
        self.progress = ttk.Progressbar(self, maximum=1, mode="determinate", length=200)
        self.progress.pack(side=BOTTOM, fill=X, expand=True)
        self.progress_text = StringVar(self.progress, value="Downloaded: 0%")
        ttk.Label(self, textvariable=self.progress_text, justify=CENTER).pack(side=BOTTOM)
        self.focus_set()

    def start_update(self):
        if self.master.ask_save() is None:
            return
        self.focus_set()
        self.update_btn.config(state=DISABLED)
        self.update_function()
        self.update_btn.config(state=NORMAL)
