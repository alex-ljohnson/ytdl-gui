"""Contains constant values for the program"""
import os
import sys

STDOUT_DEF = sys.stdout
DEBUG = False
DEFAULT_CONFIG: dict = {
    "dir": "",
    "enabled_extensions": [],
    # custom tool locations, empty means search PATH then the bundled copy
    "tools": {
        "ffmpeg": "",
        "js_runtime": "",
    },
    "prefs": {
        "font": ["Arial", 14, "normal", "roman", 0, 0],
        "parallel": False,
        "print_log": True,
        "theme": "vista",
        "verbosity": False,
        "remove_success": False,
        "rerun": False,
        "update_launch": True,
        "disable_stats": False,
        "disable_percentage": False,
    },
    "opts": {
        "resolution": 1080,
        "subtitles": True,
        "metadata": True,
        "thumbnail": True,
        "description": False,
        "audio": False,
        "audio_post": True,
        "video_format": "best",
        "audio_format": "best",
        "strict_format": False,
        "format_string": "",
        "output_template": "",
    },
}

DATA_PATH = os.path.abspath(os.path.expandvars("%appdata%\\Youtube-dl_GUI"))

APP_CONFIG_JSON = os.path.abspath(os.path.join(DATA_PATH, "appConfig.json"))

THUMBNAIL_VIDEO_FORMATS = ["best", "avi", "mkv", "mov", "mp4"]

THUMBNAIL_AUDIO_FORMATS = ["best", "flac", "ogg", "opus", "m4a", "mka", "mp3"]

RESOLUTION_VALUES = [144, 240, 480, 720, 1080, 1440, 2160, 4320]

VIDEO_FORMATS = [
    "best",
    "mp4",
    "mkv",
    "webm",
]

AUDIO_FORMATS = [
    "best",
    "mp3",
    "m4a",
    "wav",
    "ogg",
]

COMPATIBLE_FORMATS = {
    "mp4": ["m4a", "mp3"],
    "webm": ["ogg", "opus", "webm"],
    "mkv": ["mka", "m4a", "opus", "flac", "mp3", "wav", "webm"],
}

ENABLED_THEMES = [
    "adapta",
    "alt",
    "aquativo",
    "arc",
    "awarc",
    "awblack",
    "awbreeze",
    "awbreezedark",
    "awclearlooks",
    "awdark",
    "awlight",
    "awtemplate",
    "awwinxpblue",
    "black",
    "blue",
    "breeze",
    "clam",
    "classic",
    "clearlooks",
    "default",
    "elegance",
    "equilux",
    "itft1",
    "keramik",
    "kroc",
    "plastik",
    "radiance",
    "scidblue",
    "scidgreen",
    "scidgrey",
    "scidmint",
    "scidpink",
    "scidpurple",
    "scidsand",
    "smog",
    "ubuntu",
    "vista",
    "winnative",
    "winxpblue",
    "xpnative",
    "yaru",
]

BACKGROUNDS = {
    "adapta": "#FAFBFC",
    "alt": "#D9D9D9",
    "aquativo": "#FAFAFA",
    "arc": "#F5F6F7",
    "awarc": "#F5F6F7",
    "awblack": "#424242",
    "awbreeze": "#EFF0F1",
    "awbreezedark": "#2F3336",
    "awclearlooks": "#EFEBE7",
    "awdark": "#33393B",
    "awlight": "#E8E8E7",
    "awtemplate": "#424242",
    "awwinxpblue": "#ECE9D8",
    "black": "#424242",
    "blue": "#6699CC",
    "breeze": "#EFF0F1",
    "clam": "#DCDAD5",
    "classic": "#D9D9D9",
    "clearlooks": "#EFEBE7",
    "default": "#D9D9D9",
    "elegance": "#D8D8D8",
    "equilux": "#464646",
    "itft1": "#DAEFFD",
    "keramik": "#CCCCCC",
    "kroc": "#FCB64F",
    "plastik": "#EFEFEF",
    "radiance": "#EFEFEF",
    "scidblue": "#D8D8D8",
    "scidgreen": "#D8D8D8",
    "scidgrey": "#D8D8D8",
    "scidmint": "#D8D8D8",
    "scidpink": "#D8D8D8",
    "scidpurple": "#D8D8D8",
    "scidsand": "#D8D8D8",
    "smog": "#E7EAF0",
    "ubuntu": "#F6F4F2",
    "vista": "#F0F0F0",
    "winnative": "#F0F0F0",
    "winxpblue": "#ECE9D8",
    "xpnative": "#F0F0F0",
    "yaru": "#F0F0F0",
}
