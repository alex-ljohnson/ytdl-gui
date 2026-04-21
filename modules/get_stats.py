import json
import os
import subprocess
import threading

from modules.utils import find_ffprobe


class GetStats:
    """Gets basic stats about a file or folder. Only folder video contents length currently.

    Params
    ------------
    pathname: str
      The folder path to get statistics for.
        Can include shell variables in form of '$var', '${var}' and '%var%'

    quiet: bool
      If True, suppresses non-vital messages

    silent: bool
      If True, suppresses all messages"""

    def __init__(self, pathname, quiet=False, silent=False):
        self.pathname = os.path.realpath(os.path.expandvars(pathname))
        self.quiet = quiet
        self.silent = silent
        self.totTime = 0
        self.__dots__ = 0
        self._tot_lock = threading.Lock()
        self._ffprobe: str | None = None

    def write(self, text: str, importance=0, long=0):
        stages = ["|", "/", "-", "\\"]
        if not self.quiet or (importance == 1 and self.silent == False):
            print(text)
        elif self.silent and importance > 1:
            print(text)
        elif self.silent and importance <= 1:
            pass
        elif self.quiet and long == 1:
            self.__dots__ = 0
            print("Processing", end="")
        elif self.quiet and long == 2:
            self.__dots__ += 1
            print(f"\rProcessing  {stages[self.__dots__%4]}", end="")

    def get_length(self, filename) -> float | None:
        if not os.path.exists(filename) or self._ffprobe is None:
            return None
        try:
            result = subprocess.run(
                [self._ffprobe, "-v", "error", "-show_entries", "format=duration", "-of", "json", filename],
                capture_output=True,
                text=True,
                check=True,
            )
            return float(json.loads(result.stdout)["format"]["duration"])
        except Exception as ex:
            print(f"Could not read duration of {filename}: {ex}")
            return None

    def file_time(self, i):
        if i.count(".temp") != 0:
            return
        if not i.endswith((".mp4", ".mov", ".mkv", ".webm", ".avi", ".mpeg", ".mp3", ".opus", ".m4a", ".aac", ".wav")):
            return
        t = self.get_length(os.path.join(self.pathname, i))
        if t is None:
            return
        iname = str(i).strip().strip("\r\n")
        self.write(f"{iname}: {t}s\n--------------------\n", 2)
        with self._tot_lock:
            self.totTime += t

    def folder_length(self) -> dict:
        tlis: list[str] = os.listdir(self.pathname)
        self.write("Gathered folder contents.")
        self.totTime = 0
        self._ffprobe = find_ffprobe()
        if self._ffprobe is None:
            self.write("ffprobe not found; duration scan unavailable", importance=1)
        self.write("<Video name>: <seconds>\n\n--------------------", 1)
        threads: list[threading.Thread] = []
        for fn in tlis:
            t = threading.Thread(target=self.file_time, args=(fn,))
            t.start()
            threads.append(t)
        for x in threads:
            x.join()
        self.write(f"{len(threads)} done out of {len(tlis)}")
        seconds = self.totTime % 60
        minutes = int((self.totTime / 60) % 60)
        hours = int(self.totTime / 3600)
        self.write(f"Total video time: {hours}h:{minutes}m:{seconds}s\n\n", importance=1)
        return {"hours": hours, "minutes": minutes, "seconds": seconds}
