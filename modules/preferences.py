"""Preferences window class"""
import copy
from tkinter import BooleanVar, Misc, StringVar, Toplevel, messagebox, ttk
from tkinter.constants import BOTH, BOTTOM, FLAT, NW, TOP
from typing import TYPE_CHECKING

from modules.constants import DEFAULT_CONFIG, ENABLED_THEMES
from modules.utils import relative_path

if TYPE_CHECKING:
    from modules.application import Application


class PreferenceWindow(Toplevel):
    """Window for changing preferences"""

    def __init__(self, master: Misc | None = None, background: str = None) -> None:
        super().__init__(master, background=background)

        self.master: Application
        self.title("Preferences")
        self.iconbitmap(relative_path("Resources\\YTDLv2_256.ico"))

        reset_btn = ttk.Button(self, text="Reset Prefs", command=self.reset_prefs)
        reset_btn.pack(side=BOTTOM)
        pref_book = ttk.Notebook(self)
        pref_book.enable_traversal()
        pref_book.pack(side=TOP, expand=True, fill=BOTH)
        pref_frm = ttk.Frame(pref_book)
        pref_frm.pack(expand=True, fill=BOTH, side=TOP)
        self.parallel = BooleanVar(self, value=self.master.app_config["prefs"]["parallel"])
        parallel_box = ttk.Checkbutton(
            pref_frm,
            variable=self.parallel,
            command=self.warn_para,
            text=" - Download in parallel (Much Faster, lower readability)",
        )
        self.log = BooleanVar(self, value=self.master.app_config["prefs"]["print_log"])
        log_box = ttk.Checkbutton(
            pref_frm,
            variable=self.log,
            command=self.update_prefs,
            text=" - Print download log to output (defaults to console window)",
        )
        self.check_update = BooleanVar(self, value=self.master.app_config["prefs"]["update_launch"])
        check_up_box = ttk.Checkbutton(
            pref_frm,
            variable=self.check_update,
            command=self.update_prefs,
            text=" - Check for updates on app launch",
        )

        theme_frm = ttk.Frame(pref_frm)
        self.theme = StringVar(self, value=self.master.app_config["prefs"]["theme"])
        theme_box = ttk.OptionMenu(
            theme_frm,
            self.theme,
            self.theme.get(),
            *ENABLED_THEMES,
            command=self.update_prefs,
        )
        parallel_box.grid(column=0, row=0, sticky=NW)
        log_box.grid(column=0, row=1, sticky=NW)
        check_up_box.grid(column=0, row=2, sticky=NW)
        theme_frm.grid(column=0, row=3, sticky=NW)
        theme_box.grid(column=0, row=0, sticky=NW)
        ttk.Label(theme_frm, text=" - Theme").grid(column=1, row=0, sticky=NW)
        pref_book.add(pref_frm, text="General", underline=0)

        advanced_frm = ttk.Frame(pref_book, relief=FLAT)
        advanced_frm.pack(expand=True, fill=BOTH, side=TOP, padx=2.5)
        self.verbosity = BooleanVar(self, value=self.master.app_config["prefs"]["verbosity"])
        verb_box = ttk.Checkbutton(
            advanced_frm,
            variable=self.verbosity,
            command=self.update_prefs,
            text=" - Add download verbosity (Shows extra info in output window)",
        )
        self.rerun = BooleanVar(self, value=self.master.app_config["prefs"]["rerun"])
        rerun_box = ttk.Checkbutton(
            advanced_frm,
            variable=self.rerun,
            command=self.update_prefs,
            text=" - Runs downloader twice as sometimes errors can occur in post processing",
        )
        self.remove = BooleanVar(self, value=self.master.app_config["prefs"]["remove_success"])
        remove_box = ttk.Checkbutton(
            advanced_frm,
            variable=self.remove,
            command=self.update_prefs,
            text=" - Remove successful downloads from list",
        )
        self.disable_stat = BooleanVar(self, self.master.app_config["prefs"]["disable_stats"])
        disable_stat_box = ttk.Checkbutton(
            advanced_frm,
            variable=self.disable_stat,
            command=self.update_prefs,
            text=" - Disable download statistics (improves download speed)",
        )
        verb_box.grid(column=0, row=0, sticky=NW)
        rerun_box.grid(column=0, row=1, sticky=NW)
        remove_box.grid(column=0, row=2, sticky=NW)
        disable_stat_box.grid(column=0, row=3, sticky=NW)
        pref_book.add(advanced_frm, text="Advanced", underline=0)

        self.focus_set()
        self.grab_set()

    def warn_para(self, arg=None):
        self.update_prefs()
        if self.parallel.get():
            messagebox.showwarning(
                "Parallel Download Warning",
                "Downloading in parallel may affect output readability",
                parent=self,
            )

    def update_prefs(self, arg=None):
        self.master.app_config["prefs"]["parallel"] = self.parallel.get()
        self.master.app_config["prefs"]["print_log"] = self.log.get()
        self.master.app_config["prefs"]["theme"] = self.theme.get()
        self.master.app_config["prefs"]["update_launch"] = self.check_update.get()
        self.master.app_config["prefs"]["verbosity"] = self.verbosity.get()
        self.master.app_config["prefs"]["rerun"] = self.rerun.get()
        self.master.app_config["prefs"]["remove_success"] = self.remove.get()
        self.master.app_config["prefs"]["disable_stats"] = self.disable_stat.get()
        self.master.update_theme(self.theme.get())
        self.master.write_config()

    def reset_prefs(self, arg=None):
        self.master.app_config["prefs"] = copy.deepcopy(DEFAULT_CONFIG["prefs"])
        self.parallel.set(self.master.app_config["prefs"]["parallel"])
        self.theme.set(self.master.app_config["prefs"]["theme"])
        self.log.set(self.master.app_config["prefs"]["print_log"])
        self.check_update.set(self.master.app_config["prefs"]["update_launch"])
        self.verbosity.set(self.master.app_config["prefs"]["verbosity"])
        self.rerun.set(self.master.app_config["prefs"]["rerun"])
        self.remove.set(self.master.app_config["prefs"]["remove_success"])
        self.disable_stat.set(self.master.app_config["prefs"]["disable_stats"])
        self.master.update_theme(self.theme.get())
        self.master.write_config()

    def win_close(self):
        self.grab_release()
        self.master.focus_set()
        self.destroy()
