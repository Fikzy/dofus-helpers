import ctypes
from typing import Any

import psutil
import pywinauto
import win32con
import win32gui
import win32process
import win32ui
from pywinauto import win32structures


class ExecHandler:

    window: pywinauto.WindowSpecification
    id: Any  # PyCWnd

    def __init__(self, title_regex: str):

        app = pywinauto.Application()
        try:
            app.connect(title_re=title_regex)
        except Exception:
            raise SystemExit(f"Failed to find executable using regex: '{title_regex}'")

        self.window = app.top_window()
        window_title = self.window.window_text()
        self.id = win32gui.FindWindow(None, window_title)

    def get_rect(self, standard=False) -> win32structures.RECT:
        rect = win32structures.RECT()
        DWMWA_EXTENDED_FRAME_BOUNDS = 9
        ctypes.windll.dwmapi.DwmGetWindowAttribute(
            ctypes.wintypes.HWND(self.id),
            ctypes.wintypes.DWORD(DWMWA_EXTENDED_FRAME_BOUNDS),
            ctypes.byref(rect),
            ctypes.sizeof(rect),
        )
        if standard:
            return (rect.left, rect.top, rect.right - rect.left, rect.bottom - rect.top)
        return rect

    def draw_rect(self, rect: win32structures.RECT):
        dc_handle = win32gui.GetDC(self.id)
        dc = win32ui.CreateDCFromHandle(dc_handle)
        dc.Rectangle(rect)

    def get_path(self) -> str:
        _, pid = win32process.GetWindowThreadProcessId(self.id)
        process = psutil.Process(pid)
        return process.exe()

    def focus(self):
        self.window.set_focus()

    def minimize(self):
        win32gui.ShowWindow(self.id, win32con.SW_MINIMIZE)

    def screenshot(self, file_path: str):
        self.focus()
        rect = self.get_rect()
        capture = self.window.capture_as_image(rect)
        capture.save(file_path)
        print(f'screenshot saved at: "{file_path}"')
