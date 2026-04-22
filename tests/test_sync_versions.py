import pytest
from pathlib import Path
from scripts.sync_versions import (
    parse_version,
    to_numeric_version,
    to_file_version,
    update_grab_version,
    update_iss,
    read_app_version,
)

_GRAB_TEMPLATE = '''\
VSVersionInfo(
    ffi=FixedFileInfo(
        filevers=(2026, 1, 1, 1),
        prodvers=(2026, 1, 1, 1),
    ),
    kids=[StringFileInfo([StringTable("040904B0", [
        StringStruct("FileVersion", "2026.1.1.f1\\0"),
        StringStruct("ProductVersion", "2026.1.1.1\\0"),
    ])])]
)
'''

_ISS_TEMPLATE = '''\
#define MyAppVersion "2026.01.01.f1"
#define MyNumericVersion "2026.01.01.1"
'''


def test_parse_version():
    assert parse_version("2026.04.22.f2") == (2026, 4, 22, "f", 2)


def test_parse_version_special_release():
    assert parse_version("2026.04.22.s1") == (2026, 4, 22, "s", 1)


def test_parse_version_bad_variant():
    with pytest.raises(ValueError, match="Variant"):
        parse_version("2026.04.22.x2")


def test_parse_version_wrong_parts():
    with pytest.raises(ValueError, match="4-part"):
        parse_version("2026.04.22")


def test_to_numeric_version():
    assert to_numeric_version("2026.04.22.f2") == "2026.04.22.2"


def test_to_file_version():
    assert to_file_version("2026.04.22.f2") == "2026.4.22.f2"


def test_update_grab_version(tmp_path):
    grab = tmp_path / "GrabVersion.py"
    grab.write_text(_GRAB_TEMPLATE)
    update_grab_version("2026.04.22.f2", grab)
    content = grab.read_text()
    assert "filevers=(2026, 4, 22, 2)" in content
    assert "prodvers=(2026, 4, 22, 2)" in content
    assert 'StringStruct("FileVersion", "2026.4.22.f2\\0")' in content
    assert 'StringStruct("ProductVersion", "2026.4.22.2\\0")' in content


def test_update_iss(tmp_path):
    iss = tmp_path / "test.iss"
    iss.write_text(_ISS_TEMPLATE)
    update_iss("2026.04.22.f2", iss)
    content = iss.read_text()
    assert '#define MyAppVersion "2026.04.22.f2"' in content
    assert '#define MyNumericVersion "2026.04.22.2"' in content


def test_read_app_version(tmp_path):
    app_py = tmp_path / "application.py"
    app_py.write_text('APP_VERSION = "2026.04.22.f2"\n')
    assert read_app_version(app_py) == "2026.04.22.f2"