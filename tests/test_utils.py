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


from modules.utils import _bundled_quickjs, find_js_runtime


class TestBundledQuickjs:
    def test_returns_path_when_found(self, monkeypatch):
        monkeypatch.setattr("modules.utils.relative_path", lambda p, **kw: r"C:\app\quickjs\qjs.exe")
        assert _bundled_quickjs() == r"C:\app\quickjs\qjs.exe"

    def test_returns_none_when_not_found(self, monkeypatch):
        def _raise(p, **kw):
            raise FileNotFoundError
        monkeypatch.setattr("modules.utils.relative_path", _raise)
        assert _bundled_quickjs() is None


class TestFindJsRuntime:
    def _which(self, found: str | None):
        return lambda name: (f"C:\\tools\\{name}.exe" if name == found else None)

    def test_prefers_deno_on_path(self, monkeypatch):
        monkeypatch.setattr("modules.utils.shutil.which", self._which("deno"))
        assert find_js_runtime() == "deno"

    def test_uses_bun_when_no_deno(self, monkeypatch):
        monkeypatch.setattr("modules.utils.shutil.which", self._which("bun"))
        assert find_js_runtime() == "bun"

    def test_uses_node_when_no_deno_or_bun(self, monkeypatch):
        monkeypatch.setattr("modules.utils.shutil.which", self._which("node"))
        assert find_js_runtime() == "node"

    def test_maps_qjs_on_path_to_quickjs_name(self, monkeypatch):
        monkeypatch.setattr("modules.utils.shutil.which", self._which("qjs"))
        assert find_js_runtime() == "quickjs"

    def test_falls_back_to_bundled_qjs(self, monkeypatch):
        monkeypatch.setattr("modules.utils.shutil.which", lambda name: None)
        monkeypatch.setattr("modules.utils.relative_path", lambda p, **kw: r"C:\app\quickjs\qjs.exe")
        assert find_js_runtime() == r"quickjs:C:\app\quickjs\qjs.exe"

    def test_returns_none_when_nothing_found(self, monkeypatch):
        monkeypatch.setattr("modules.utils.shutil.which", lambda name: None)
        def _raise(p, **kw):
            raise FileNotFoundError
        monkeypatch.setattr("modules.utils.relative_path", _raise)
        assert find_js_runtime() is None
