"""Tests for modules.utils."""
import pytest

from modules.utils import version_compare


@pytest.mark.parametrize(
    "a,b,expected",
    [
        ("v2024.01.23.f1", "v2024.01.23.f1", "="),
        ("v2024.02.01.f1", "v2024.01.23.f1", ">"),
        ("v2023.12.28.f1", "v2024.01.23.f1", "<"),
        ("v1.10.0", "v1.9.0", ">"),   # numeric, not lexical
        ("v1.9.0", "v1.10.0", "<"),
    ],
)
def test_version_compare(a, b, expected):
    assert version_compare(a, b) == expected
