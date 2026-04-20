"""Provides a base for extensions"""
import importlib
import pkgutil
from tkinter import BooleanVar, Misc, Toplevel, messagebox, ttk
from types import ModuleType
from typing import TYPE_CHECKING

import modules.extensions
from modules.utils import log_debug, relative_path

if TYPE_CHECKING:
    from modules.application import Application


class Extension:
    """Extend to add plugins to app"""

    _name: str | None = None
    # _REQUIRED_PACKAGES: set[str] = set()

    def __init__(self):
        self.ready = False
        # installed = {pkg.key for pkg in pkg_resources.working_set}  # pylint: disable=E1133
        # missing = self._REQUIRED_PACKAGES - installed
        # if missing:
        #     python = sys.executable
        #     subprocess.check_call([python, "-m", "pip", "install", *missing], stdout=subprocess.DEVNULL)
        #     pip.main(["install", "--user", *missing])
        # for package in self._REQUIRED_PACKAGES:
        #     importlib.import_module(package)

    def get_name(self):
        return self._name or self.__class__.__name__

    def enable(self):
        self.ready = True

    def disable(self):
        self.ready = False


class PlatformExtension(Extension):
    """Class which can be extended to provide support for new platforms"""

    def __init__(self):
        super().__init__()
        self.ready = False

    def get_items(self, urn: str) -> list[str]:
        return [urn]

    def check_type(self, item: str) -> bool:
        if item:
            return True
        return False


class ExtensionManager:
    """Holds all extensions for the application"""

    instance = None

    def __new__(cls, *args):
        if cls.instance is None:
            log_debug("Creating extension singleton")
            cls.instance = super(ExtensionManager, cls).__new__(cls)
            cls.instance._initialised = False
        return cls.instance

    def __init__(self, master) -> None:
        if getattr(self, "_initialised", False):
            return
        self.master: "Application" = master
        self.extensions = {}
        self.load_extensions()
        self._initialised = True

    def iter_namespace(self, ns_pkg: ModuleType):
        return pkgutil.walk_packages(ns_pkg.__path__, ns_pkg.__name__ + ".")

    def load_extensions(self):
        discovered_extensions = {
            name: importlib.import_module(name) for finder, name, ispkg in self.iter_namespace(modules.extensions)
        }
        for module in discovered_extensions.values():
            for attr in [getattr(module, x) for x in dir(module)]:
                if isinstance(attr, type):
                    if issubclass(attr, Extension) and attr not in (Extension, PlatformExtension):
                        try:
                            self.extensions[attr.__name__] = attr()
                        except Exception as ex:  # pylint: disable=W0718
                            messagebox.showerror("Module not loaded", f"A module could not load.\n{ex}")

    def register(self, cls: type[Extension]):
        new_ext = cls()
        self.extensions[cls.__name__] = new_ext


class ExtensionWindow(Toplevel):
    """Provides a window for managing extensions"""

    def __init__(self, master: Misc | None = None, *, background: str | None = None) -> None:
        super().__init__(master, background=background)  # type: ignore

        self.master: Application
        self.title("Manage Extensions")
        self.iconbitmap(relative_path("Resources\\YTDLv2_256.ico"))
        self.protocol("WM_DELETE_WINDOW", self.win_close)
        self.grab_set()
        ttk.Label(self, text="Use checkboxes below to enable or disable extensions loaded.").grid(column=0, row=0)
        count = 0
        for ext in ExtensionManager(self.master).extensions.values():
            ext: Extension
            self.new_var = BooleanVar(self, value=ext.ready)
            self.check = ttk.Checkbutton(
                self,
                variable=self.new_var,
                command=lambda e=ext: self.toggle_ext(e),
                text=f" - {ext.get_name()}",
            )
            self.check.grid(column=count % 3, row=1 + int(count / 3))
            count += 1

    def toggle_ext(self, extension: Extension):
        try:
            if extension.ready:
                self.master.app_config["enabled_extensions"].remove(extension.__class__.__name__)
                extension.disable()
            else:
                self.master.app_config["enabled_extensions"].append(extension.__class__.__name__)
                extension.enable()
        except Exception as ex:  # pylint: disable=W0718
            messagebox.showerror("Module error", f"Module could not load.\n{ex}")
        self.master.write_config()

    def win_close(self, event=None):
        self.grab_release()
        self.master.focus_set()
        self.destroy()
