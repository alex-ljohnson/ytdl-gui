"""Propagate APP_VERSION from modules/application.py to GrabVersion.py and YTDLGUISetupScript.iss."""

import re
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
APP_PY = REPO_ROOT / "modules" / "application.py"
GRAB_VERSION = REPO_ROOT / "GrabVersion.py"
ISS_FILE = REPO_ROOT / "YTDLGUISetupScript.iss"


def read_app_version(path: Path = APP_PY) -> str:
    text = path.read_text(encoding="utf-8")
    m = re.search(r'^APP_VERSION\s*=\s*"([^"]+)"', text, re.MULTILINE)

    if not m:
        raise ValueError(f"APP_VERSION not found in {path}")
    return m.group(1)


def parse_version(version: str) -> tuple[int, int, int, str, int]:
    parts = version.split(".")
    if len(parts) != 4:
        raise ValueError(f"Expected 4-part version, got: {version!r}")
    year, month, day, variant = parts
    if not variant or variant[0] not in ("f", "s"):
        raise ValueError(f"Variant must start with 'f' or 's', got: {variant!r}")
    return int(year), int(month), int(day), variant[0], int(variant[1:])


def to_numeric_version(version: str) -> str:
    parts = version.split(".")
    build_num = int(parts[3][1:])
    return f"{parts[0]}.{parts[1]}.{parts[2]}.{build_num}"


def to_file_version(version: str) -> str:
    # Windows VERSIONINFO string fields use unpadded integers, not zero-padded dates
    year, month, day, variant = version.split(".")
    return f"{int(year)}.{int(month)}.{int(day)}.{variant}"


def update_grab_version(version: str, path: Path = GRAB_VERSION) -> None:
    year, month, day, _flag, build_num = parse_version(version)
    tup = f"({year}, {month}, {day}, {build_num})"
    file_ver = to_file_version(version)
    prod_ver = f"{year}.{month}.{day}.{build_num}"

    text = path.read_text(encoding="utf-8")
    text = re.sub(r"filevers=\([^)]+\)", f"filevers={tup}", text)
    text = re.sub(r"prodvers=\([^)]+\)", f"prodvers={tup}", text)
    text = re.sub(
        r'(StringStruct\("FileVersion",\s*")[^"]*(")',
        lambda m: f"{m.group(1)}{file_ver}\\0{m.group(2)}",
        text,
    )
    text = re.sub(
        r'(StringStruct\("ProductVersion",\s*")[^"]*(")',
        lambda m: f"{m.group(1)}{prod_ver}\\0{m.group(2)}",
        text,
    )
    path.write_text(text, encoding="utf-8")


def update_iss(version: str, path: Path = ISS_FILE) -> None:
    numeric = to_numeric_version(version)
    text = path.read_text(encoding="utf-8")
    text = re.sub(
        r'(#define MyAppVersion\s+")[^"]+"',
        lambda m: f'{m.group(1)}{version}"',
        text,
    )
    text = re.sub(
        r'(#define MyNumericVersion\s+")[^"]+"',
        lambda m: f'{m.group(1)}{numeric}"',
        text,
    )
    path.write_text(text, encoding="utf-8")


def main() -> None:
    version = read_app_version()
    parse_version(version)  # validate format before touching any files
    print(f"Syncing version: {version}")
    update_grab_version(version)
    print("  Updated GrabVersion.py")
    update_iss(version)
    print("  Updated YTDLGUISetupScript.iss")


if __name__ == "__main__":
    main()
