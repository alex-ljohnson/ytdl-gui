"""Structural integrity tests for modules.constants."""
from modules import constants


def test_enabled_themes_and_backgrounds_in_sync():
    assert set(constants.ENABLED_THEMES) == set(constants.BACKGROUNDS.keys())


def test_resolution_values_sorted_ascending():
    assert constants.RESOLUTION_VALUES == sorted(constants.RESOLUTION_VALUES)


def test_compatible_formats_keys_are_video_formats():
    video_formats_no_best = set(constants.VIDEO_FORMATS) - {"best"}
    for k in constants.COMPATIBLE_FORMATS:
        assert k in video_formats_no_best, f"{k!r} in COMPATIBLE_FORMATS is not a non-best VIDEO_FORMAT"


def test_audio_formats_contains_best():
    assert "best" in constants.AUDIO_FORMATS


def test_video_formats_contains_best():
    assert "best" in constants.VIDEO_FORMATS


def test_default_config_top_level_keys():
    for key in ("dir", "enabled_extensions", "prefs", "opts"):
        assert key in constants.DEFAULT_CONFIG, f"Missing top-level key: {key!r}"


def test_default_config_prefs_keys():
    prefs = constants.DEFAULT_CONFIG["prefs"]
    for key in ("font", "parallel", "print_log", "theme", "verbosity",
                "remove_success", "rerun", "update_launch", "disable_stats", "disable_percentage"):
        assert key in prefs, f"Missing prefs key: {key!r}"


def test_default_config_opts_keys():
    opts = constants.DEFAULT_CONFIG["opts"]
    for key in ("resolution", "subtitles", "metadata", "thumbnail",
                "audio", "video_format", "audio_format", "strict_format", "format_string", "output_template"):
        assert key in opts, f"Missing opts key: {key!r}"


def test_enabled_themes_has_no_duplicates():
    assert len(constants.ENABLED_THEMES) == len(set(constants.ENABLED_THEMES))
