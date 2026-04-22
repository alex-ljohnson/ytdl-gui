"""This is a script to generate an easy to use GUI for the youtube-dl package.

This is usually bundled into an executable with pyinstaller (or similar) for ease of use to non-python users.
This also implements some additional features on top of what youtube-dl provides, such as, total length calculation of videos in a folder, spotify support (eventually) and more...
"""

import argparse
import copy
import json
import os
import sys
import threading
from tkinter import Menu, Text, filedialog, font, messagebox, ttk
from tkinter.constants import BOTH, BOTTOM, END, FLAT, HORIZONTAL, RIGHT, TOP, X, Y

from ttkthemes import ThemedTk

import modules.constants
from modules.about import AboutWindow
from modules.constants import (
    APP_CONFIG_JSON,
    BACKGROUNDS,
    DATA_PATH,
    DEFAULT_CONFIG,
    ENABLED_THEMES,
)
from modules.download import Downloader
from modules.extension import ExtensionManager, ExtensionWindow
from modules.font_wm import FontWm
from modules.help import HelpWindow
from modules.options import OptionsWindow
from modules.preferences import PreferenceWindow
from modules.time_scan import TimeWindow
from modules.update import Updater
from modules.utils import link, log_debug, relative_data, relative_path


class Application(ThemedTk):
    """Base application window and functions for the Youtube-dl GUI

    Attributes
    ------
        title: The title of the window
        size: Form of "``x_size``x``y_size``"
        debug: Whether to put the app in debug mode. Prints additional info.
        path: Path-like string determining the path of the `.ytdl` or other file to open. Leave as ```None``` for default `ToDownload.ytdl` file
        version: Version info if applicable.
    """

    def __init__(self, size, path=None, version_info=None):
        print("Loading preferences and settings...")

        self.app_config = {}
        self.exe = bool(getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"))
        self.load_config()

        super().__init__(
            theme=self.app_config["prefs"]["theme"],
            toplevel=BACKGROUNDS[self.app_config["prefs"]["theme"]],  # type: ignore
            themebg=BACKGROUNDS[self.app_config["prefs"]["theme"]],  # type: ignore
        )

        self.running = False
        self.path = path
        self.app_version = version_info
        self.updater = Updater(self.app_version, self)
        self.downloader = Downloader(self.app_config["opts"], self.app_config["dir"], self)
        self.time_window = None
        self.help_window = None
        self.about_window = None
        self.options_window = None
        self.prefs_window = None
        self.extension_window = None

        # Load themes
        self.tk.call("lappend", "auto_path", relative_path("awthemes-10.3.0"))
        self.tk.call("package", "require", "awthemes")
        self.tk.call("lappend", "auto_path", relative_path("tksvg0.7"))
        self.tk.call("package", "require", "tksvg")
        loaded_themes = self.get_themes()
        loaded_themes.sort()
        log_debug(f"THEMES PRESENT: {loaded_themes == ENABLED_THEMES}")
        log_debug(f"EXE: {self.exe}")
        if loaded_themes != ENABLED_THEMES:
            difference = list(set(loaded_themes) ^ set(ENABLED_THEMES))
            messagebox.showerror(
                "Themes unavailable",
                f"The themes: {difference} aren't available\nThis may require a reinstall of the software to fix this issue.\nOtherwise, please report an issue.",
                parent=self,
            )
            if self.app_config["prefs"]["theme"] in difference:
                sys.exit(f"Themes: {', '.join(difference)} \nare unavailable")
        self.update_theme(self.app_config["prefs"]["theme"])

        if self.path is None:
            self.path = relative_data("ToDownload.ytdl", False)
            log_debug("Loading default .ytdl", True)
            if not os.path.exists(self.path):
                open(self.path, "x", encoding="utf-8").close()  # Create if it doesn't exist
                log_debug("Creating ToDownload.ytdl")
        elif not (
            os.path.exists(self.path)
            and os.path.isfile(self.path)
            and (str(self.path).endswith(".ytdl") or str(self.path).endswith(".vdl"))
        ):
            raise OSError("File specified must be an existing file of type .ytdl (or .vdl for legacy files)")

        if str(self.app_config["dir"]).strip() == "":
            messagebox.showinfo(
                "No download target selected",
                "Please select a folder to download your files into.",
            )
            ans = filedialog.askdirectory(parent=self, title="Select Download Directory...")
            if ans.strip() == "":
                sys.exit("No Directory given...")
            else:
                self.app_config["dir"] = os.path.abspath(ans)

        # Extensions
        self.extension_manager = ExtensionManager(self)
        for name, extension in self.extension_manager.extensions.items():
            if list(self.app_config["enabled_extensions"]).__contains__(name):
                extension.enable()

        self.title(f"Youtube-dl GUI - {str(self.app_config['dir'])}")
        self.iconbitmap(relative_path("Resources\\YTDLv2_256.ico"))
        self.geometry(size)
        self.saved = True
        confont = self.app_config["prefs"]["font"]
        self.curr_font = font.Font(
            family=confont[0],
            size=confont[1],
            weight=confont[2],
            slant=confont[3],
            underline=confont[4],
            overstrike=confont[5],
        )
        self.write_config()
        self.btn_frm = ttk.Frame(self)
        self.btn_frm.pack(side=BOTTOM, fill=X, expand=True)
        ttk.Frame(self.btn_frm).grid(row=0, column=0)
        mid = ttk.Frame(self.btn_frm)
        mid.grid(row=0, column=1)
        self.yt_button = ttk.Button(mid, text="Start Download...", command=self.open_download)
        self.time_button = ttk.Button(mid, text="List Time...", command=self.open_time)
        self.yt_button.grid(row=0, column=0, padx=3, pady=5)
        self.time_button.grid(row=0, column=1, padx=3, pady=5)
        ttk.Frame(self.btn_frm).grid(row=0, column=2)
        self.btn_frm.grid_columnconfigure(0, weight=1)
        self.btn_frm.grid_columnconfigure(1, weight=1)
        self.btn_frm.grid_columnconfigure(2, weight=1)
        self.text_frame = ttk.Frame(self)
        self.y_scroll = ttk.Scrollbar(self.text_frame)
        self.x_scroll = ttk.Scrollbar(self.text_frame, orient=HORIZONTAL)
        self.main_text = Text(
            self.text_frame,
            xscrollcommand=self.x_scroll.set,
            yscrollcommand=self.y_scroll.set,
            relief=FLAT,
            font=self.curr_font,
            undo=True,
            maxundo=-1,
        )
        self.y_scroll.config(command=self.main_text.yview)
        self.x_scroll.config(command=self.main_text.xview)
        self.f = open(self.path, "r+", encoding="utf-8")
        log_debug(f"[File IO] Opened file {self.f.name} || Encoding is {self.f.encoding}")
        try:
            self.f.seek(0)
            lines_in = self.f.readlines()
            log_debug(f"[File IO] Read {lines_in} from {self.f.name}")
        except UnicodeDecodeError:
            lines_in = [""]
            messagebox.showerror("Bad encoding", "The encoding of the file isn't supported", parent=self)
        if len(lines_in) > 0:
            if lines_in[-1][-1:] == "\n":
                lines_in[-1] = lines_in[-1][:-1]
            for i in lines_in:
                if i.strip() in ("", "\n"):
                    lines_in.remove(i)
        self.main_text.insert("1.0", "".join(lines_in))
        self.main_text.edit_reset()
        self.text_frame.pack(side=TOP, expand=True, fill=BOTH, padx=5)
        self.y_scroll.pack(side=RIGHT, fill=Y)
        self.x_scroll.pack(side=BOTTOM, fill=X)
        self.main_text.pack(side=TOP, expand=True, fill=BOTH)
        self.menu = Menu(self, relief=FLAT)

        self.file_menu = Menu(self.menu, tearoff=0)
        self.file_menu.add_command(label="New (CTRL+N)", command=self.new)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Save (CTRL+S)", command=self.save)
        self.file_menu.add_command(label="Save As (CTRL+SHIFT+S)...", command=self.save_as)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Open (CTRL+O)...", command=self.open)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Preferences...", command=self.open_prefs)

        self.edit_menu = Menu(self.menu, tearoff=0)
        self.edit_menu.add_command(label="Undo (CTRL+Z)", command=self.main_text.edit_undo)
        self.edit_menu.add_command(label="Redo (CTRL+Y)", command=self.main_text.edit_redo)

        self.view_menu = Menu(self.menu, tearoff=0)
        self.view_menu.add_command(label="Font...", command=self.font)

        self.tool_menu = Menu(self.menu, tearoff=0)
        self.tool_menu.add_command(label="Current File", command=self.curr_file)
        self.tool_menu.add_command(label="Current Directory", command=self.curr_dir)
        self.tool_menu.add_command(label="Change Directory...", command=self.change_dir)
        self.tool_menu.add_command(label="Clear archive", command=self.clear_archive)
        self.tool_menu.add_separator()
        self.tool_menu.add_command(label="Download Options...", command=self.open_options)
        self.tool_menu.add_separator()
        self.tool_menu.add_command(label="Manage extensions...", command=self.open_extensions)

        self.help_menu = Menu(self.menu, tearoff=0)
        self.help_menu.add_command(label="About Youtube-dl GUI", command=self.open_about)
        self.help_menu.add_command(label="Help & Instructions", command=self.open_help)
        self.help_menu.add_separator()
        self.help_menu.add_command(label="Report Bug", command=self.bug)
        self.help_menu.add_command(label="Check for updates...", command=self.updater.check_update)

        self.menu.add_cascade(label="File", menu=self.file_menu, underline=0)
        self.menu.add_cascade(label="Edit", menu=self.edit_menu, underline=0)
        self.menu.add_cascade(label="View", menu=self.view_menu, underline=0)
        self.menu.add_cascade(label="Tools", menu=self.tool_menu, underline=0)
        self.menu.add_cascade(label="Help", menu=self.help_menu, underline=0)
        self.config(menu=self.menu)

        self.bind_all("<Control-n>", self.new)
        self.bind_all("<Control-s>", self.save)
        self.bind_all("<Control-Shift-S>", self.save_as)
        self.bind_all("<Control-o>", self.open)
        self.main_text.bind("<Control-Shift-Z>", lambda _: self.main_text.edit_redo())
        self.main_text.bind("<<Modified>>", self.modified)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Update Check
        if self.app_config["prefs"]["update_launch"]:
            if not self.updater.check_update(True):
                log_debug("[Update Check] No updates")

    def load_config(self):
        def _apply_defaults(config, defaults):
            for k, v in defaults.items():
                if config.get(k) is None:
                    config[k] = copy.deepcopy(v)
                elif isinstance(v, dict):
                    _apply_defaults(config[k], v)

        if not os.path.exists(DATA_PATH):
            log_debug("Creating '%appdata/Youtube-dl_GUI' folder")
            os.mkdir(DATA_PATH)
        if not os.path.exists(APP_CONFIG_JSON):
            open(APP_CONFIG_JSON, "x", encoding="utf-8").close()
            log_debug("Creating 'appConfig.json'")
        with open(APP_CONFIG_JSON, "r", encoding="utf-8") as f:
            try:
                self.app_config = json.load(f)
                if not isinstance(self.app_config, dict):
                    print("Error in config. Setting default config...")
                    self.app_config = {}
            except json.decoder.JSONDecodeError:
                print("Error in config. Setting default config...")
                self.app_config = {}
        if not self.app_config:
            self.app_config = copy.deepcopy(DEFAULT_CONFIG)
            self.write_config()
            return
        _apply_defaults(self.app_config, DEFAULT_CONFIG)

    def write_config(self):
        log_debug("[App Config] Written config", True)
        with open(APP_CONFIG_JSON, "w", encoding="utf-8") as f:
            json.dump(self.app_config, f)
            f.close()

    def new(self, event=None) -> None:
        log_debug("New file")
        if self.ask_save() is None:
            return
        self.main_text.delete("1.0", END)
        if self.f is not None:
            self.f.close()
            self.f = None

    def save(self, event=None) -> bool:
        if self.f is None:
            log_debug("Save as from save")
            return self.save_as()
        self.saved = True
        self.title(self.title().replace("*", ""))
        log_debug("[Data] Save")
        s = self.main_text.get("1.0", END)[:-1]
        self.f.truncate(0)
        self.f.seek(0)
        self.f.write(s)
        self.f.flush()
        os.fsync(self.f.fileno())
        return True

    def save_as(self, event=None) -> bool:
        path = filedialog.asksaveasfilename(
            confirmoverwrite=True,
            defaultextension=".ytdl",
            initialfile="downloads.ytdl",
            filetypes=[
                ("Youtube-dl File (*.ytdl)", "*.ytdl"),
            ],
            title="Save As...",
            parent=self,
        )
        if not path:
            log_debug("Save as cancelled")
            return False
        log_debug("Save as")
        if self.f is not None:
            self.f.close()
        self.f = open(path, "w+", encoding="utf-8")
        self.title(f"Youtube-dl GUI - {path}")
        return self.save()

    def ask_save(self):
        """Ask user if they want to save.

        Ask user if they want to save. Returns `True` and auto-saves if they do want to save, `False` if they don't and `None` if they cancel.

        Returns:
            True: if yes is selected
            False: if no is selected
            None: if cancel is selected"""
        if not self.saved:
            log_debug("Asking save")
            sv = messagebox.askyesnocancel("Save Changes?", "Do you want to save your changes?", parent=self)
            if sv:
                if not self.save():
                    return None
            return sv
        else:
            log_debug("Already saved.")
            return True

    def open(self, event=None):
        path = filedialog.askopenfilename(
            defaultextension=".ytdl",
            filetypes=[
                ("Youtube-dl File (*.ytdl)", "*.ytdl"),
                ("Legacy Downloader File (*.vdl)", "*.vdl"),
            ],
            parent=self,
            title="Open...",
        )
        if path:
            log_debug("Open")
            if self.f is not None:
                self.f.close()
            self.f = open(path, "r+", encoding="utf-8")
            try:
                lines_in = self.f.readlines()
                self.main_text.delete("1.0", END)
                log_debug(f"Read {lines_in} from {self.f.name}")
            except UnicodeDecodeError:
                lines_in = [""]
                messagebox.showerror(
                    "Bad encoding",
                    "The encoding of the file isn't supported",
                    parent=self,
                )
            if len(lines_in) > 0:
                if lines_in[-1][-1:] == "\n":
                    lines_in[-1] = lines_in[-1][:-1]
                for i in lines_in:
                    if i.strip() in ("", "\n"):
                        lines_in.remove(i)
            self.title(f"Youtube-dl GUI - {path}")
            self.main_text.insert("1.0", "".join(lines_in))
            self.main_text.edit_reset()
            self.main_text.edit_modified(False)
            self.saved = True

    def curr_dir(self):
        messagebox.showinfo(
            "Current Directory",
            f"Current directory is: {self.app_config['dir']}",
            parent=self,
        )

    def curr_file(self):
        messagebox.showinfo(
            "Current File",
            f"Current file is: {self.f.name if self.f is not None else None}",
            parent=self,
        )

    def clear_archive(self):
        with open(relative_data("archive.txt"), "w", encoding="utf-8") as f:
            f.truncate(0)
            f.close()

    def change_dir(self):
        ans = filedialog.askdirectory(parent=self, title="Select Download Directory...")
        if ans.strip() != "":
            self.app_config["dir"] = os.path.abspath(ans)
        self.write_config()
        self.title(f"Youtube-dl GUI - {str(self.app_config['dir'])}")

    def open_download(self):
        self.downloader = Downloader(self.app_config["opts"], self.app_config["dir"], self)
        self.downloader.open_download()

        lines = []
        if self.f is None:
            lines = self.main_text.get("1.0", END).split("\n")
        else:
            self.f.seek(0)
            lines = [i.replace("\n", "") for i in self.f.readlines()]
        thread = threading.Thread(
            target=self.downloader.download,
            args=(
                lines,
                self.app_config["prefs"]["parallel"],
                self.app_config["prefs"]["print_log"],
            ),
        )
        thread.start()

        if self.app_config["prefs"]["remove_success"]:
            ltext: list = self.main_text.get("1.0", END).split("\n")
            text_copy = ltext.copy()
            archive_path = relative_data("archive.txt")
            if not os.path.exists(archive_path):
                open(archive_path, "x", encoding="utf-8").close()
            with open(archive_path, "r", encoding="utf-8") as f:
                success = f.readlines()
                f.close()
            success = [i[i.index(" ") + 1 : -1] for i in success]
            log_debug(success)
            for i in ltext:
                for x in success:
                    if x in i:
                        text_copy.remove(i)

            self.main_text.delete("1.0", END)
            self.main_text.insert("1.0", "\n".join(text_copy))

    def open_time(self):
        self.time_window = TimeWindow(self, f"List Time Output - {self.app_config['dir']}", block=False)
        log_debug("Created time win")
        self.time_window.task()

    def open_about(self):
        self.about_window = AboutWindow(self, background=BACKGROUNDS[self.app_config["prefs"]["theme"]])

    def open_help(self):
        self.help_window = HelpWindow(self, background=BACKGROUNDS[self.app_config["prefs"]["theme"]])

    def open_options(self):
        self.options_window = OptionsWindow(self)

    def open_prefs(self):
        self.prefs_window = PreferenceWindow(self, background=BACKGROUNDS[self.app_config["prefs"]["theme"]])

    def open_extensions(self):
        self.extension_window = ExtensionWindow(self, background=BACKGROUNDS[self.app_config["prefs"]["theme"]])

    def update_theme(self, theme):
        ttk.Style().theme_use(theme)
        self.set_theme(theme, BACKGROUNDS[theme], BACKGROUNDS[theme])  # type: ignore
        self.config(bg=BACKGROUNDS[self.app_config["prefs"]["theme"]])
        try:
            self.main_text.config(bg=BACKGROUNDS[theme])
        except AttributeError:
            pass
        if self.downloader is not None and self.downloader.download_window is not None:
            self.downloader.download_window.config(bg=BACKGROUNDS[theme])
            self.downloader.download_window.out_text.config(bg=BACKGROUNDS[theme])
        if self.options_window is not None:
            self.options_window.config(bg=BACKGROUNDS[theme])
        if self.time_window is not None:
            self.time_window.config(bg=BACKGROUNDS[theme])
        if self.prefs_window is not None:
            self.prefs_window.config(bg=BACKGROUNDS[theme])

    def bug(self):
        ans = messagebox.askyesnocancel(
            "Report via Github?",
            "Would you like to report the bug online via Github.\nYes: report by Github\nNo: report via email",
            parent=self,
        )
        if ans is None:
            log_debug("Cancelled report.")
        elif ans:
            link("https://github.com/alex-ljohnson/ytdl-gui/issues/new")
            log_debug("Github report.")
        else:
            link("mailto:16JohnA28@gmail.com")
            log_debug("Email report.")

    def font(self, event=None):
        fw = FontWm(my_font=self.curr_font)
        fw.transient(self)
        fw.grab_set()
        self.wait_window(fw)
        self.font_to_list()

    def on_closing(self, event=None):
        self.font_to_list()
        if not self.saved:
            sv = messagebox.askyesnocancel("Save Changes?", "Do you want to save your changes?", parent=self)
            if sv is None:
                return
            if sv and not self.save():
                return  # user cancelled the save-as dialog
        self.destroy()
        sys.exit(0)

    def modified(self, event=None):
        if self.saved:
            self.saved = False
            self.title(f"*{self.title()}*")
        self.main_text.edit_modified(False)

    def font_to_list(self):
        self.app_config["prefs"]["font"] = [
            self.curr_font.actual("family"),
            self.curr_font.actual("size"),
            self.curr_font.actual("weight"),
            self.curr_font.actual("slant"),
            self.curr_font.actual("underline"),
            self.curr_font.actual("overstrike"),
        ]
        self.write_config()


APP_VERSION = "2026.04.22.f3"


def main(args: argparse.Namespace):
    """Entry point for the program"""
    if args.path is None:
        path = None
    elif not os.path.exists(os.path.abspath(args.path)):
        sys.exit(f"File {args.path} doesn't exist")
    else:
        path = os.path.abspath(args.path)
    print("Loading Modules...")
    if args.debug:
        print(sys.argv)
        modules.constants.DEBUG = True
    app = Application("1080x600", path, APP_VERSION)
    try:
        app.mainloop()
    except RuntimeError as e:
        sys.exit(str(e))
