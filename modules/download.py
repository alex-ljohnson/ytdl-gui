"""Provides window and logic for downloading"""

import os
import threading
from tkinter import Misc, messagebox
from tkinter.constants import END
from typing import TYPE_CHECKING, Callable

from yt_dlp import YoutubeDL

from modules.constants import (
    COMPATIBLE_FORMATS,
    THUMBNAIL_AUDIO_FORMATS,
    THUMBNAIL_VIDEO_FORMATS,
)
from modules.extension import ExtensionManager, PlatformExtension
from modules.out_win import OutputWindow
from modules.utils import disable_insert, log_debug, relative_data, relative_path

if TYPE_CHECKING:
    from modules.application import Application


class Downloader:
    """Provides functionality for file downloading"""

    def __init__(self, download_options: dict, output_directory: str, master: "Application") -> None:
        self.master: "Application" = master
        self.download_options = download_options
        self.output_directory = output_directory
        self.download_window = None
        self.running = False

    def open_download(self):
        if self.master.ask_save() is None:
            return

        if self.download_window is not None:
            self.download_window.deiconify()
            log_debug("Unwithdrawn yt win")
        else:
            self.download_window = DownloadWindow(
                self.master,
                f"Download Output - {self.output_directory}",
                block=False,
            )
            log_debug("Created yt win")

    def format_select(self, ctx: dict[str, list[dict]]):
        """Select the best video and the best audio that won't result in an mkv."""
        # formats are already sorted worst to best
        video_ext = self.download_options["video_format"]
        audio_ext = self.download_options["audio_format"]
        resolution = self.download_options["resolution"]
        do_audio = self.download_options["audio"]
        strict_format = self.download_options["strict_format"]
        formats: list[dict] = ctx["formats"][::-1]  # type: ignore

        best_audio: dict[str, str] | None = None
        best_video: dict[str, str] | None = None

        if do_audio:
            best_audio = next(
                (
                    f
                    for f in formats
                    if f.get("acodec", "none") != "none" and f.get("vcodec", "none") == "none" and f["ext"] == audio_ext
                ),
                None,
            )
            if best_audio is None:
                best_audio = next(
                    (
                        f
                        for f in formats
                        if f.get("acodec", "none") != "none" and f.get("vcodec", "none") == "none" and f["ext"] == "m4a"
                    ),
                    None,
                )
                print("Requested format not available, falling back to m4a.")
            if best_audio is not None:
                print(
                    f"[Format Selection] Using {best_audio['ext']} ({best_audio.get('format_note', 'Empty') or 'Empty'}) audio only"
                )
                yield {
                    "format_id": best_audio["format_id"],
                    "ext": best_audio["ext"],
                    "requested_formats": [best_audio],
                    "protocol": best_audio["protocol"],
                }
        else:
            has_audio = False
            if video_ext != "best":
                best_video = next(
                    (
                        f
                        for f in formats
                        if f.get("vcodec", "none") != "none"
                        and f.get("acodec", "none") == "none"
                        and f["ext"] == video_ext
                        and f["height"] <= resolution
                    ),
                    None,
                )
                if best_video is None:
                    best_video = next(
                        (
                            f
                            for f in formats
                            if f.get("vcodec", "none") != "none"
                            and f.get("acodec", "none") != "none"
                            and f["ext"] == video_ext
                            and f["height"] <= resolution
                        ),
                        None,
                    )
                    has_audio = True
            if not strict_format or video_ext == "best":
                if best_video is None:
                    best_video = next(
                        (
                            f
                            for f in formats
                            if f.get("vcodec", "none") != "none"
                            and f.get("acodec", "none") == "none"
                            and f["height"] <= resolution
                        ),
                        None,
                    )
                if best_video is None:
                    best_video = next(
                        (
                            f
                            for f in formats
                            if f.get("vcodec", "none") != "none"
                            and f.get("acodec", "none") != "none"
                            and f["height"] <= resolution
                        ),
                        None,
                    )
                    has_audio = True
                if best_video is None:
                    best_video = next(
                        (
                            f
                            for f in formats[::-1]
                            if f.get("vcodec", "none") != "none" and f.get("acodec", "none") == "none"
                        ),
                        None,
                    )
                if best_video is None:
                    best_video = next(
                        (
                            f
                            for f in formats[::-1]
                            if f.get("vcodec", "none") != "none" and f.get("acodec", "none") != "none"
                        ),
                        None,
                    )
                    has_audio = True

            if best_video is None:
                print("No supported video format found")
                return

            if best_video is not None:
                if not has_audio and video_ext != "best":
                    audio_ext = COMPATIBLE_FORMATS[best_video["ext"]]
                    best_audio = next(
                        f
                        for f in formats
                        if (
                            f.get("acodec", "none") != "none"
                            and f.get("vcodec", "none") == "none"
                            and f["ext"] in audio_ext
                        )
                    )
                elif not has_audio:
                    best_audio = next(
                        (f for f in formats if f.get("acodec", "none") != "none" and f.get("vcodec", "none") == "none"),
                        None,
                    )

                if best_audio is not None and video_ext != "best":
                    print(
                        f"[Format Selection] Merging {best_video['ext']} ({best_video.get('format_note', 'Empty')}) and {best_audio['ext']} ({best_audio.get('format_note', 'Empty')})"
                    )
                    # These are the minimum required fields for a merged format
                    yield {
                        "format_id": f'{best_video["format_id"]}+{best_audio["format_id"]}',
                        "ext": best_video["ext"],
                        "requested_formats": [best_video, best_audio],
                        "protocol": f'{best_video["protocol"]}+{best_audio["protocol"]}',
                    }
                elif best_audio is not None:
                    print(
                        f"[Format Selection] Merging {best_video['ext']} ({best_video.get('format_note', 'Empty')}) and {best_audio['ext']} ({best_audio.get('format_note', 'Empty')}) into mkv"
                    )
                    yield {
                        "format_id": f'{best_video["format_id"]}+{best_audio["format_id"]}',
                        "ext": "mkv",
                        "requested_formats": [best_video, best_audio],
                        "protocol": f'{best_video["protocol"]}+{best_audio["protocol"]}',
                    }

                else:
                    print(
                        f"[Format Selection] Using {best_video['ext']} ({best_video.get('format_note', 'Empty')}) only"
                    )
                    yield {
                        "format_id": best_video["format_id"],
                        "ext": best_video["ext"],
                        "requested_formats": [best_video],
                        "protocol": best_video["protocol"],
                    }

    def download(self, lines, parallel: bool, print_log: bool):
        def progress_hook(d: dict):
            if self.download_window is None:
                return
            status = d.get("status")
            if status == "downloading":
                total_bytes = d.get("total_bytes")
                total = total_bytes if total_bytes is not None else (d.get("total_bytes_estimate") or 0)
                downloaded = d.get("downloaded_bytes", 0)
                pct_str = d.get("_percent_str")
                stat_str = d.get("_default_template")

                def apply_downloading():
                    if self.download_window is None:
                        return
                    if total:
                        self.download_window.progress["value"] = downloaded / total
                    if pct_str is not None:
                        self.download_window.percent.set(pct_str)
                    if stat_str is not None:
                        self.download_window.stat_string.set(str(stat_str))

                self.download_window.after(0, apply_downloading)
            elif status == "finished":
                total_str = d.get("_total_bytes_str", "unknown")
                elapsed = d.get("elapsed")
                if elapsed is not None:
                    print(f"Finished downloading {total_str} in {elapsed} seconds\n")
                else:
                    print("Download finished\n")

                def apply_finished():
                    if self.download_window is None:
                        return
                    self.download_window.progress["value"] = 0
                    self.download_window.percent.set("Download Complete! - Finishing up")
                    self.download_window.stat_string.set(f"{total_str}/{total_str} @ 0MiB/s")

                self.download_window.after(0, apply_finished)

        archive_path = relative_data("archive.txt")
        if not os.path.exists(archive_path):
            open(archive_path, "w", encoding="utf-8").close()  # Create archive if it doesn't exist

        can_embed = (
            not self.download_options["audio"] and self.download_options["video_format"] in THUMBNAIL_VIDEO_FORMATS
        ) or (self.download_options["audio"] and self.download_options["audio_format"] in THUMBNAIL_AUDIO_FORMATS)
        opts = {
            "default_search": "auto",
            "outtmpl": f"{self.output_directory}\\%(title)s-%(uploader)s-%(upload_date)s.%(ext)s",
            "format": self.format_select,
            # "ffmpeg_location": relative_path("ffmpeg-20200115-0dc0837-win64-static\\bin"),
            "ffmpeg_location": relative_path(
                "imageio_ffmpeg\\binaries\\ffmpeg-win64-v4.2.2.exe", unbundled_prefix=".venv\\Lib\\site-packages"
            ),
            "cookiefile": relative_path("Logs\\cookies.txt", True),
            "writethumbnail": self.download_options["thumbnail"],
            # "writethumbnail": False,
            "writesubtitles": self.download_options["subtitles"],
            "writeautomaticsub": self.download_options["subtitles"],
            "writedescription": self.download_options["description"],
            "retries": 2,
            "ignoreerrors": True,
            "download_archive": archive_path,
            "progress_hooks": [],
            "postprocessors": [],
            "verbose": self.master.app_config["prefs"]["verbosity"],
        }
        if self.download_options["format_string"].strip() != "":
            opts["format"] = self.download_options["format_string"]  #
            log_debug("[Format] Using custom format " + self.download_options["format_string"])
        # elif self.appConfig['opts']['audio']:
        #     opts['format'] = f"ba[ext={self.appConfig['opts']['audio_format']}]/ba"
        #     if self.appConfig['opts']['audio_format'] == "best":
        #         opts['format'] = "ba"

        # elif self.appConfig['opts']['video_format'] == "best":
        #     opts['format'] = f"bv*[height<=?{self.appConfig['opts']['resolution']}]+ba/b[height<=?{self.appConfig['opts']['resolution']}]/wv*+ba/w"
        # elif not self.appConfig['opts']['strict_format']:
        #     opts['format'] = opts['format'] + f"bv*[height<=?{self.appConfig['opts']['resolution']}]+ba/b[height<=?{self.appConfig['opts']['resolution']}]/wv*+ba/w"
        if self.download_options["output_template"].strip() != "":
            opts["outtmpl"] = self.download_options["output_template"]
            log_debug(opts["outtmpl"])
        if self.download_options["audio_post"]:
            opts["postprocessors"].append(
                {"key": "FFmpegExtractAudio", "preferredcodec": self.download_options["audio_format"]}
            )
        if self.download_options["metadata"]:
            opts["postprocessors"].append({"key": "FFmpegMetadata"})
            log_debug("Added metadata postprocess")
        if self.download_options["thumbnail"]:
            if can_embed:
                opts["postprocessors"].append(
                    {
                        "key": "EmbedThumbnail",
                        "already_have_thumbnail": False,
                    }
                )
                log_debug("Added thumbnail postprocess")
            else:
                print("Chosen format doesn't support thumbnail embedding, leaving file on disk")
        if self.download_options["subtitles"]:
            opts["postprocessors"].append({"key": "FFmpegEmbedSubtitle"})
        if not self.master.app_config["prefs"]["disable_stats"]:
            log_debug("Added progress hook")
            opts["progress_hooks"].append(progress_hook)
        ytdl = YoutubeDL(opts)  # type: ignore

        items = [i.strip() for i in items if (s := i.strip()) and not s.startswith("#")]
        items = self.apply_extensions(lines)
        if items is None:
            return
        if items[-1].strip() == "":
            items = items[:-1]
        self.running = True
        if not print_log:
            if self.download_window is not None:
                disable_insert(
                    self.download_window.out_text,
                    END,
                    "Check console window if you want to see output",
                )
        if not parallel:
            ytdl.download(items)
        else:
            threads: list[threading.Thread] = []
            for i in items:
                th = threading.Thread(target=ytdl.download, args=[[i]])
                th.start()
                threads.append(th)
            for i in threads:
                if i.is_alive():
                    i.join()

        with open(archive_path, "w", encoding="utf-8") as f:
            f.truncate(0)
            f.close()
        self.running = False
        if self.download_window is not None:
            self.download_window.percent.set("All videos downloaded successfully (window may be closed)")
            print("Process finished successfully\nWindow may be closed...", end="")
            messagebox.showinfo(
                "Download finished",
                "Download finished successfully",
                parent=self.download_window,  # type: ignore
            )

    def apply_extensions(self, lines: list[str]) -> list[str] | None:
        if ExtensionManager.instance is None:
            log_debug("Extension manager not initialised, skipping extension checks")
            return [i for i in lines if not i.startswith("#")]
        platform_extensions = [
            e for e in ExtensionManager.instance.extensions.values() if isinstance(e, PlatformExtension)
        ]
        items: list[str] = []
        for i in lines:
            extension_found = False
            for extension in platform_extensions:
                if not extension.check_type(i):
                    continue
                if not extension.ready:
                    ans = messagebox.askyesnocancel(
                        f"{extension.get_name()} not enabled",
                        f"{extension.get_name()} support is an optional extra.\n"
                        "To enable it either go to Tools > Manage extensions...\n"
                        "Or click 'Yes' to enable it now.\n"
                        "Click no to continue without enabling the extension.",
                        parent=self.download_window,  # type: ignore
                    )
                    if ans is None:
                        return None
                    if ans:
                        extension.enable()
                if extension.ready:
                    expanded = extension.get_items(i)
                    if expanded:
                        items.extend(expanded)
                extension_found = True
                break
            if not extension_found and i and not i.startswith("#"):
                items.append(i)
        return items


class DownloadWindow(OutputWindow):
    """Provides UI for file downloading"""

    def __init__(
        self,
        master: Misc | None = None,
        title="New window",
        download_function: Callable = None,  # type: ignore
        block=True,
        *,
        background: str | None = None,
        **kwargs,
    ) -> None:
        super().__init__(master, title, block, background=background, **kwargs)

        self.master: Application
        self.download = download_function
        self.task()

    def win_close(self, event=None):
        super().win_close(event)
        log_debug("Deleted yt win")
