"""Entry point to compiled program"""

import argparse
import sys
from tkinter import messagebox

from modules import application

if __name__ == "__main__":
    import psutil

    processes = [p.name() for p in psutil.process_iter()]
    if processes.count("DownloaderGUI.exe") < 2:
        parser = argparse.ArgumentParser()
        parser.add_argument(
            "-d",
            "--debug",
            "--verbose",
            action="store_true",
            help="set program to debug mode for more info printed",
            dest="debug",
            default=False,
        )
        parser.add_argument(
            "-v",
            "--version",
            action="version",
            help="show version message and exit",
            version="%(prog)s v" + application.APP_VERSION,
        )
        parser.add_argument(
            "path", nargs="?", help="path to a .ytdl file containing a list of URLs for the editor", default=None
        )
        args = parser.parse_args()
        application.main(args)
    else:
        messagebox.showwarning("Program Running", "The program is already running...")
        sys.exit("Already Running...")
