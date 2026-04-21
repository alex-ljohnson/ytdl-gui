import os
from tkinter import Misc, Text, Toplevel, font, ttk
from tkinter.constants import BOTH, DISABLED, GROOVE, INSERT, LEFT, NW, RIGHT, TOP, W, Y
from typing import TYPE_CHECKING

from modules.utils import _bundled_ffmpeg_dir, link, relative_path

if TYPE_CHECKING:
    from modules.application import Application


class AboutWindow(Toplevel):
    def __init__(self, master: Misc | None = None, *, background: str = "white") -> None:
        super().__init__(master, background=background)

        self.master: Application  # type: ignore
        self.title("Youtube-dl GUI - About")
        self.iconbitmap(relative_path("Resources\\YTDLv2_256.ico"))

        self.about_note = ttk.Notebook(self)
        self.about_note.enable_traversal()
        self.about_note.pack(side=TOP, expand=True, fill=BOTH)
        self.main_frm = ttk.Frame(self)
        ver_lbl = ttk.Label(self.main_frm, text=f"Youtube-dl GUI v{self.master.app_version}", justify=LEFT, anchor=NW)
        ver_lbl.grid(column=0, row=0, sticky=NW, padx=10, pady=2, columnspan=2)
        und_fnt = font.Font(ver_lbl, font=ver_lbl.cget("font"), underline=True, size=9)
        ttk.Label(self.main_frm, text="Author: ", justify=LEFT).grid(column=0, row=1, sticky=NW, padx=10, pady=2)
        ttk.Label(self.main_frm, text="Alex Johnson", justify=LEFT).grid(column=1, row=1, sticky=NW, padx=10, pady=2)
        ttk.Label(self.main_frm, text="Contact: ", justify=LEFT).grid(column=0, row=2, sticky=NW, padx=10, pady=2)

        con2_lbl = ttk.Label(
            self.main_frm,
            text="email",
            foreground="#00A7FF",
            font=und_fnt,
            cursor="hand2",
            justify=LEFT,
        )
        con2_lbl.bind("<Button-1>", lambda e: link("mailto:16JohnA28@gmail.com"))
        con2_lbl.grid(column=1, row=2, sticky=NW, padx=10, pady=2)
        ttk.Label(self.main_frm, text="Github: ", justify=LEFT).grid(column=0, row=3, sticky=NW, padx=10, pady=2)
        git2_lbl = ttk.Label(
            self.main_frm,
            text="https://github.com/alex-ljohnson/ytdl-gui",
            foreground="#00A7FF",
            font=und_fnt,
            cursor="hand2",
            justify=LEFT,
        )
        git2_lbl.bind(
            "<Button-1>",
            lambda e: link("https://github.com/alex-ljohnson/ytdl-gui"),
        )
        git2_lbl.grid(column=1, row=3, sticky=NW, padx=10, pady=2)
        ttk.Label(self.main_frm, text="Copyright © 2021 Alexander Johnson", justify=LEFT).grid(
            column=0, row=4, columnspan=3, pady=5
        )
        ttk.Label(
            self.main_frm,
            text='THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,\nEXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF\nMERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.\nIN NO EVENT SHALL THE AUTHORS BE LIABLE FOR ANY CLAIM, DAMAGES OR\nOTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,\nARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR\nOTHER DEALINGS IN THE SOFTWARE.\n',
            justify=LEFT,
            relief=GROOVE,
        ).grid(column=0, row=5, columnspan=3)
        ttk.Label(self.main_frm, text="Refer to ").grid(column=0, row=6, sticky=W)
        loc_lbl = ttk.Label(
            self.main_frm,
            text="LICENSE",
            foreground="#00A7FF",
            font=und_fnt,
            cursor="hand2",
            justify=LEFT,
        )
        loc_lbl.bind("<Button-1>", lambda e: link(relative_path("LICENSE")))
        loc_lbl.grid(column=1, row=6, sticky=W)
        ttk.Label(
            self.main_frm,
            text=" for information regarding distribution, modification and use",
            justify=LEFT,
        ).grid(column=2, row=6, sticky=W)
        self.about_note.add(self.main_frm, text="About Youtube-dl GUI")

        ff_bin = _bundled_ffmpeg_dir()
        if ff_bin:
            ff_license = os.path.join(os.path.dirname(ff_bin), "LICENSE")
            ffmpeg_frm = ttk.Frame(self)
            ff_lic_txt = Text(ffmpeg_frm)
            with open(ff_license, "r", encoding="utf-8") as f:
                ff_lic_txt.insert(INSERT, "".join(f.readlines()))
            ff_lic_txt.config(state=DISABLED)
            ff_lic_y = ttk.Scrollbar(ffmpeg_frm, command=ff_lic_txt.yview)
            ff_lic_y.pack(side=RIGHT, fill=Y, expand=True)
            ff_lic_txt.config(yscrollcommand=ff_lic_y.set)
            ff_lic_txt.pack(side=LEFT, fill=BOTH, expand=True)
            self.about_note.add(ffmpeg_frm, text="FFmpeg License")

        atomic_frm = ttk.Frame(self)
        at_lic_txt = Text(atomic_frm)
        with open(relative_path("AtomicParsleyWindows\\COPYING.txt"), "r", encoding="utf-8") as f:
            at_lic_txt.insert(INSERT, "".join(f.readlines()))
        at_lic_txt.config(state=DISABLED)
        at_lic_y = ttk.Scrollbar(atomic_frm, command=at_lic_txt.yview)
        at_lic_y.pack(side=RIGHT, fill=Y, expand=True)
        at_lic_txt.config(yscrollcommand=at_lic_y.set)
        at_lic_txt.pack(side=LEFT, fill=BOTH, expand=True)
        self.about_note.add(atomic_frm, text="Atomic Parsley License")

        awtheme_frm = ttk.Frame(self)
        aw_lic_txt = Text(awtheme_frm)
        with open(relative_path("awthemes-10.3.0\\LICENSE"), "r", encoding="utf-8") as f:
            aw_lic_txt.insert(INSERT, "".join(f.readlines()))
        aw_lic_txt.config(state=DISABLED)
        aw_lic_y = ttk.Scrollbar(awtheme_frm, command=aw_lic_txt.yview)
        aw_lic_y.pack(side=RIGHT, fill=Y, expand=True)
        aw_lic_txt.config(yscrollcommand=aw_lic_y.set)
        aw_lic_txt.pack(side=LEFT, fill=BOTH, expand=True)
        self.about_note.add(awtheme_frm, text="Awthemes License")
