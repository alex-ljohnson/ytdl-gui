"""Provides redirection classes for textIO outputs"""
import sys
from tkinter import DISABLED, END, NORMAL, TclError, Text, messagebox


class _RedirectBase:
    def __init__(self, t: Text, interactive: bool = True):
        self.text_box = t
        self.interactive = interactive
        self.open = True

    def flush(self):
        pass

    def writelines(self, lines):
        self.text_box.config(state=NORMAL)
        self.text_box.insert(END, "\n".join(lines))
        self.text_box.see(END)
        self.text_box.config(state=DISABLED)

    def isatty(self):
        return self.interactive

    def _write_to_widget(self, s: str):
        self.text_box.config(state=NORMAL)
        if s.startswith("\r"):
            self.text_box.delete("end-1c linestart", "end")
            self.text_box.insert(END, f"\n{s}")
        else:
            self.text_box.insert(END, s)
        self.text_box.see(END)
        self.text_box.config(state=DISABLED)


class StderrRedirect(_RedirectBase):
    """Redirects sys.stderr into a Text widget. Call close() to restore."""

    def __init__(self, t: Text, interactive: bool = True, msgbox: bool = False, master=None):
        super().__init__(t, interactive)
        self.old_stderr = sys.stderr
        self.master = master
        self.msgbox = msgbox
        sys.stderr = self

    def write(self, s: str):
        try:
            self._write_to_widget(s)
        except (TclError, RuntimeError) as e:
            if "main thread is not in main loop" in str(e):
                return
            try:
                self.old_stderr.write(s)
            except Exception:  # pylint: disable=W0718
                pass
            if self.open:
                self.close()

    def close(self):
        if not self.open:
            return
        sys.stderr = self.old_stderr
        self.open = False


class StdoutRedirect(_RedirectBase):
    """Redirects sys.stdout into a Text widget. Call close() to restore."""

    def __init__(self, t: Text, interactive: bool = True):
        super().__init__(t, interactive)
        self.old_stdout = sys.stdout
        sys.stdout = self

    def write(self, s: str):
        try:
            self._write_to_widget(s)
        except TclError:
            try:
                self.old_stdout.write(s)
            except Exception:  # pylint: disable=W0718
                pass
            if self.open:
                self.close()

    def close(self):
        if not self.open:
            return
        sys.stdout = self.old_stdout
        self.open = False
