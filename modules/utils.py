"""Static utility functions for the program"""

import os
import sys
from tkinter import DISABLED, NORMAL, Text

from modules import constants


def link(url):
    os.startfile(url)


def log_debug(value: object, default_stdout: bool = True):
    if constants.DEBUG:
        if default_stdout:
            constants.STDOUT_DEF.write(f"{value}\n")
        else:
            print(value)


def version_compare(ver1: str, ver2: str):
    sp1 = ver1.split(".")
    sp2 = ver2.split(".")
    if len(sp1) != len(sp2):
        raise ValueError(f"Version formats of {ver1} and {ver2} aren't the same.")
    for i, v in enumerate(sp1):
        if v > sp2[i]:
            return ">"
        elif v < sp2[i]:
            return "<"
        elif v == sp2[i] and i == ver1.count("."):
            return "="
    raise ValueError("Something went wrong and the comparisons didn't match.")


# def add_to_queue(l: list, value: Any):
#     l.pop(0)
#     l.append(value)


def disable_insert(text: Text, index, chars, *args):
    text.config(state=NORMAL)
    text.insert(index, chars, args)
    text.config(state=DISABLED)


def relative_path(path: str, create: bool = False, unbundled_prefix: str = "", bundled_prefix: str = ""):
    try:
        base = os.path.abspath(os.path.join(sys._MEIPASS, bundled_prefix))  # type: ignore # pylint: disable=protected-access
        res = os.path.abspath(os.path.join(base, path))
    except (AttributeError, TypeError):
        base = os.path.abspath(os.path.join(os.path.abspath("."), unbundled_prefix))
        res = os.path.abspath(os.path.join(base, path))
    if not os.path.exists(res):
        if create:
            os.makedirs(res, exist_ok=True)
        else:
            raise FileNotFoundError(f"File {res} isn't an existing local file.")
    log_debug(f"[File] Path {str(res)} found")
    return res


def relative_data(path: str, should_exist: bool = True):
    base = constants.DATA_PATH
    res = os.path.abspath(os.path.join(base, path))
    if not os.path.exists(res) and should_exist:
        raise FileNotFoundError(f"File {res} isn't an existing data file.")
    log_debug(f"[File] Path {str(res)} found")
    return res
