"""Options window class"""
from tkinter import BooleanVar, Misc, StringVar, Toplevel, ttk
from tkinter.constants import BOTH, BOTTOM, NW, TOP, S
from typing import TYPE_CHECKING

from modules.constants import AUDIO_FORMATS, RESOLUTION_VALUES, VIDEO_FORMATS
from modules.utils import relative_path

if TYPE_CHECKING:
    from modules.application import Application


class OptionsWindow(Toplevel):
    """Provides class for the download options window"""

    def __init__(self, master: Misc | None = None, *, background: str = None) -> None:
        super().__init__(master, background=background)

        self.master: Application
        self.title("Download Options")
        self.iconbitmap(relative_path("Resources\\YTDLv2_256.ico"))

        opts_book = ttk.Notebook(self)
        opts_book.enable_traversal()
        opts_book.pack(side=TOP, expand=True, fill=BOTH)
        opts_frm = ttk.Frame(opts_book)
        opts_frm.pack(expand=True, side=TOP, fill=BOTH)
        self.description = BooleanVar(self, value=self.master.app_config["opts"]["description"])
        description_box = ttk.Checkbutton(
            opts_frm,
            variable=self.description,
            command=self.update_opts,
            text=" - Download .description file",
        )
        self.subtitles = BooleanVar(self, value=self.master.app_config["opts"]["subtitles"])
        subtitles_box = ttk.Checkbutton(
            opts_frm, variable=self.subtitles, command=self.update_opts, text=" - Embed subtitles"
        )
        self.thumbnail = BooleanVar(self, value=self.master.app_config["opts"]["thumbnail"])
        thumb_box = ttk.Checkbutton(
            opts_frm, variable=self.thumbnail, command=self.update_opts, text=" - Embed Thumbnail"
        )
        self.metadata = BooleanVar(self, value=self.master.app_config["opts"]["metadata"])
        metadata_box = ttk.Checkbutton(
            opts_frm, variable=self.metadata, command=self.update_opts, text=" - Add metadata"
        )
        self.audio = BooleanVar(self, value=self.master.app_config["opts"]["audio"])
        audio_box = ttk.Checkbutton(opts_frm, variable=self.audio, command=self.update_opts, text=" - Extract audio")
        resol_frm = ttk.Frame(opts_frm)
        resol_lbl = ttk.Label(resol_frm, text=" - Max resolution")
        self.resol_box = ttk.Spinbox(resol_frm, values=RESOLUTION_VALUES, command=self.update_opts)
        self.resol_box.set(self.master.app_config["opts"]["resolution"])

        self.video_format = StringVar(self, value=self.master.app_config["opts"]["video_format"])
        video_format_frm = ttk.Frame(opts_frm)
        video_format_lbl = ttk.Label(video_format_frm, text=" - Preferred video extract format")
        video_format_box = ttk.OptionMenu(
            video_format_frm,
            self.video_format,
            self.video_format.get(),
            *VIDEO_FORMATS,
            command=self.update_opts,
        )
        self.audio_format = StringVar(self, value=self.master.app_config["opts"]["audio_format"])
        audio_format_frm = ttk.Frame(opts_frm)
        audio_format_lbl = ttk.Label(audio_format_frm, text=" - Preferred audio extract format")
        audio_format_box = ttk.OptionMenu(
            audio_format_frm,
            self.audio_format,
            self.audio_format.get(),
            *AUDIO_FORMATS,
            command=self.update_opts,
        )

        self.strict_format = BooleanVar(self, value=self.master.app_config["opts"]["strict_format"])
        strict_format_box = ttk.Checkbutton(
            opts_frm,
            variable=self.strict_format,
            command=self.update_opts,
            text=" - Selected format only",
        )
        self.audio_post = BooleanVar(self, value=self.master.app_config["opts"]["audio_post"])
        audio_post_box = ttk.Checkbutton(
            opts_frm,
            variable=self.audio_post,
            command=self.update_opts,
            text=" - Audio Postprocess (force format)",
        )
        description_box.grid(column=0, row=0, sticky=NW)
        subtitles_box.grid(column=0, row=1, sticky=NW)
        thumb_box.grid(column=0, row=2, sticky=NW)
        metadata_box.grid(column=0, row=3, sticky=NW)
        audio_box.grid(column=0, row=4, sticky=NW)
        resol_frm.grid(column=0, row=5, sticky=NW)
        self.resol_box.grid(column=0, row=0)
        resol_lbl.grid(column=1, row=0)
        video_format_frm.grid(column=0, row=6, sticky=NW)
        video_format_box.grid(column=0, row=0)
        video_format_lbl.grid(column=1, row=0)
        audio_format_frm.grid(column=0, row=7, sticky=NW)
        audio_format_box.grid(column=0, row=0)
        audio_format_lbl.grid(column=1, row=0)
        strict_format_box.grid(column=0, row=8, sticky=NW)
        audio_post_box.grid(column=0, row=9, sticky=NW)
        opts_book.add(opts_frm, text="General", underline=0)

        advanced_frm = ttk.Frame(opts_book)
        self.format_string = StringVar(self, value=self.master.app_config["opts"]["format_string"])
        format_frm = ttk.Frame(advanced_frm)
        format_lbl = ttk.Label(format_frm, text="Format selection string (empty=default): ")
        format_box = ttk.Entry(format_frm, textvariable=self.format_string)
        self.format_string.set(self.master.app_config["opts"]["format_string"])

        self.output = StringVar(self, value=self.master.app_config["opts"]["output_template"])
        output_frm = ttk.Frame(advanced_frm)
        output_lbl = ttk.Label(output_frm, text="Output template (empty=default): ")
        output_box = ttk.Entry(output_frm, textvariable=self.output)
        self.output.set(self.master.app_config["opts"]["output_template"])

        save_btn = ttk.Button(advanced_frm, command=self.update_opts, text="Save options")
        format_frm.grid(row=0, column=0, sticky=NW, columnspan=3)
        format_lbl.grid(row=0, column=0)
        format_box.grid(row=0, column=1, columnspan=2)
        output_frm.grid(row=1, column=0, sticky=NW, columnspan=3)
        output_lbl.grid(row=0, column=0)
        output_box.grid(row=0, column=1, columnspan=2)
        ttk.Label(
            advanced_frm,
            text="WARNING: Altering these options may affect the operation of other options and preferences!",
            foreground="red",
        ).grid(row=2, column=0, sticky=NW)
        ttk.Label(
            advanced_frm,
            text="For help with options, visit the help and instructions section of the app.",
        ).grid(row=3, column=0, sticky=NW)
        save_btn.grid(column=0, row=6, sticky=S)
        opts_book.add(advanced_frm, text="Pro mode", underline=0)

        ttk.Label(
            self,
            text="NOTE: Some options may cause undesirable behaviours on platforms other than YT.\nE.g. twitch's description is the stream JSON.",
        ).pack(side=BOTTOM, expand=True, fill=BOTH)

    def update_opts(self, arg=None):
        self.master.app_config["opts"]["description"] = self.description.get()
        self.master.app_config["opts"]["subtitles"] = self.subtitles.get()
        self.master.app_config["opts"]["metadata"] = self.metadata.get()
        self.master.app_config["opts"]["thumbnail"] = self.thumbnail.get()
        self.master.app_config["opts"]["audio"] = self.audio.get()
        self.master.app_config["opts"]["video_format"] = self.video_format.get()
        self.master.app_config["opts"]["audio_format"] = self.audio_format.get()
        self.master.app_config["opts"]["strict_format"] = self.strict_format.get()
        self.master.app_config["opts"]["audio_post"] = self.audio_post.get()
        self.master.app_config["opts"]["resolution"] = int(self.resol_box.get().strip())
        self.master.app_config["opts"]["format_string"] = self.format_string.get().strip()
        self.master.app_config["opts"]["output_template"] = self.output.get().strip()
        self.master.write_config()
