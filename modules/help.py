"""Provides HelpWindow class"""

# pylint: disable=E0611
from tkinter import BOTH, BOTTOM, DISABLED, INSERT, TOP, Misc, Text, Toplevel, ttk

from modules.utils import link, relative_path


class HelpWindow(Toplevel):
    """Toplevel window for providing help to user"""

    def __init__(self, master: Misc | None = None, *, background: str = "white") -> None:
        super().__init__(master, background=background)

        self.title("Youtube-dl GUI - Help")
        self.iconbitmap(relative_path("Resources\\YTDLv2_256.ico"))

        help_book = ttk.Notebook(self)
        help_book.enable_traversal()
        help_book.pack(side=TOP, fill=BOTH, expand=True)
        common_error_frm = ttk.Frame(help_book)
        common_error_box = Text(common_error_frm)
        common_error_box.insert(
            INSERT,
            """Error - Download freezes mid-way, then I get \"urlopen error timeout\"
Cause - This is caused by a slow connection or a connection drop-out, and the download timing out.
Solution - If the error box says \"retrying\", press ok and the downloader will try to re-establish the connection.""",
        )
        common_error_box.config(state=DISABLED)
        common_error_frm.pack(side=TOP, fill=BOTH, expand=True)
        common_error_box.pack(side=TOP, fill=BOTH, expand=True)
        help_book.add(common_error_frm, text="Common errors", underline=0)

        custom_format_frm = ttk.Frame(help_book)
        custom_format_box = Text(custom_format_frm)
        custom_format_box.insert(
            INSERT,
            """Custom format selection strings allow you to choose the way in which video+audio quality, file type, codec and more are selected in the download.
    For help with the format selection available, it is recommended that you use the button below to view the yt-dlp documentation on this subject with examples.
    By default the format string isn't used, and the best available format is selected automatically based on the options selected, but would look like this:
        b[height<=?{resolution}][ext={video_format}]/w[ext={video_format}]/bv*[height<=?{resolution}]+ba/b[height<=?{resolution}]/wv*+ba/w""",
        )
        custom_format_link = ttk.Button(
            custom_format_frm,
            text="Formatting Help",
            command=lambda: link("https://github.com/yt-dlp/yt-dlp#format-selection"),
        )
        custom_format_box.config(state=DISABLED)
        custom_format_frm.pack(side=TOP, fill=BOTH, expand=True)
        custom_format_box.pack(side=TOP, fill=BOTH, expand=True)
        custom_format_link.pack(side=BOTTOM)
        help_book.add(custom_format_frm, text="Custom format selection", underline=0)

        output_template_frame = ttk.Frame(help_book)
        output_template_box = Text(output_template_frame)
        output_template_box.insert(
            INSERT,
            """Output templates allow you to customise the filename of the download.
    Documentation is available on the yt-dlp github page, and is recommended to be viewed using the button below.
    The default template used is
        %(title)s-%(uploader)s-%(upload_date)s.%(ext)s
    The main variables available are in the format %(variable)s, and are as follows:
        title: The title of the video
        uploader: The uploader of the video
        upload_date: The date the video was uploaded
        ext: The file extension of the video
        id: The video identifier
        description: The description of the video""",
        )
        output_template_link = ttk.Button(
            output_template_frame,
            text="Output Template Help",
            command=lambda: link("https://github.com/yt-dlp/yt-dlp#output-template"),
        )
        output_template_box.config(state=DISABLED)
        output_template_frame.pack(side=TOP, fill=BOTH, expand=True)
        output_template_box.pack(side=TOP, fill=BOTH, expand=True)
        output_template_link.pack(side=BOTTOM)
        help_book.add(output_template_frame, text="Output template", underline=0)
