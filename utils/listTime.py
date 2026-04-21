#!/usr/bin/env D:\propertyofalexjohnson\vscode\python\YTDL\.venv\Scripts\python.exe
import os
import sys
from tkinter import END, Text, filedialog
from typing import Union

from moviepy import editor


# find why moviepy causes error when compiled to exe.
#    AttributeError: module 'moviepy.audio.fx.all' has no attribute 'audio_fadein'
# ALSO INSTALL UPX! TO make exes smaller
# To CHANGE:
# ADD threaded delay with "This may take some time" through use of datetime check in self.write
class GetStats:
    """Gets basic stats about a file or folder. Only folder video contents lenth currently."""

    def __init__(self, pathname, quiet=False, silent=False, doLog=False, out: Union[str, Text] = "default"):
        self.pathname = os.path.realpath(os.path.expandvars(pathname))
        self.quiet = quiet
        self.silent = silent
        self.log = doLog
        self.out = out
        self.lis = []
        self.takeTime = False
        print("Start Of program...", file=open("..\\Logs\\timeLogs.txt", "w"))
        self.__dots__ = 0

    def wrtToSTDOUT(self, text, end="\n"):
        if type(self.out) == Text:
            self.out.insert(END, text + str(end))
        elif type(self.out) == str:
            if self.out.lower() == "default":
                print(text, end=end)

    def write(self, text: str, long=0, importance=0):
        stages = ["|", "/", "-", "\\"]
        if not self.quiet or (importance == 1 and self.silent == False):
            self.wrtToSTDOUT(text)
        elif self.silent and importance > 1:
            self.wrtToSTDOUT(text)
        elif self.silent and importance <= 1:
            pass
        elif self.quiet and long == 1:
            self.__dots__ = 0
            self.wrtToSTDOUT("Processing", end="")
        elif self.quiet and long == 2:
            self.__dots__ += 1
            # print(f"\rProcessing{'.'*self.__dots__}", end="")
            self.wrtToSTDOUT(f"\rProcessing  {stages[self.__dots__%4]}", end="")

        if self.log:
            self.wrtToSTDOUT(text, file=open("..\\Logs\\timeLogs.txt", "a"))

    def get_length(self, filename):
        if not os.path.exists(filename):
            return None
        try:
            vid = editor.VideoFileClip(filename)
            dur = vid.duration
        except Exception as ex:
            print(f"vv Error occurred getting video duration vv.\n\n{str(ex)}\n")
            sys.exit(f"vv Error occurred getting video duration vv.\n\n{str(ex)}\n")
        return dur

    def folder_length(self):
        sDir = self.pathname
        tlis = os.listdir(sDir)
        for i in tlis:
            if (
                i.endswith(".mp4")
                or i.endswith(".mov")
                or i.endswith(".mkv")
                or i.endswith(".webm")
                or i.endswith(".avi")
            ) and i.count(".temp") == 0:
                self.lis.append(i)
        self.write("Gathered folder contents.")
        totTime = 0
        self.write("<Video name>: <seconds.microseconds>\n\n--------------------", 1)
        for i in self.lis:
            t = self.get_length(os.path.join(self.pathname, i))
            if t == None:
                continue
            self.write(f"{i}: {t}s\n--------------------", 2)
            totTime += t
        seconds = totTime % 60
        minutes = int((totTime / 60) % 60)
        hours = int(totTime / 3600)
        self.write(f"Total video time: {hours}h:{minutes}m:{seconds}s\n\n", importance=1)
        return {"hours": hours, "minutes": minutes, "seconds": seconds}


if __name__ == "__main__":
    args = sys.argv
    q = True
    d = ""
    if len(args) > 1:
        d = args[1]
        if args[2].lower() == "false":
            q = False
        elif args[2].lower() == "true":
            q = True
    if not os.path.isdir(d):
        d = filedialog.askdirectory()
        if not os.path.exists(d):
            print("Path doesn't exist...\nEnding program")
            sys.exit("Path doesn't exist")
    else:
        d = os.path.realpath(d)
    print(d)
    myStats = GetStats(d, q)
    print("Gathering data now...\nThis could take some time...")
    l = myStats.folder_length()
