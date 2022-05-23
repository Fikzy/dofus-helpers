import ctypes
from typing import Any

import psutil
import pywinauto
import win32api
import win32con
import win32gui
import win32process
import win32ui
from pywinauto import win32structures


class ExecHandler:

    window: pywinauto.WindowSpecification
    hwnd: Any  # PyCWnd

    def __init__(self, title_regex: str):

        app = pywinauto.Application()
        try:
            app.connect(title_re=title_regex)
        except Exception:
            raise SystemExit(f"Failed to find executable using regex: '{title_regex}'")

        self.window = app.top_window()
        window_title = self.window.window_text()
        self.hwnd = win32gui.FindWindow(None, window_title)

    def __get_rect(self) -> win32structures.RECT:
        rect = win32structures.RECT()
        DWMWA_EXTENDED_FRAME_BOUNDS = 9
        ctypes.windll.dwmapi.DwmGetWindowAttribute(
            ctypes.wintypes.HWND(self.hwnd),
            ctypes.wintypes.DWORD(DWMWA_EXTENDED_FRAME_BOUNDS),
            ctypes.byref(rect),
            ctypes.sizeof(rect),
        )
        return rect
        # return win32structures.RECT(*win32gui.GetWindowRect(self.hwnd))

    def __get_restore_rect(self):
        placements = win32gui.GetWindowPlacement(self.hwnd)
        rect = win32structures.RECT(*placements[4])
        if rect.left == -1 and rect.top == -1:
            rect.left += 1
            rect.top += 1
            rect.right -= 15
            rect.bottom -= 15
        else:
            rect.left += 7
            rect.right -= 7
            rect.bottom -= 7
        return rect

    def get_rect(self):
        if self.is_maximized():
            return self.__get_rect()
        return self.__get_restore_rect()

    def get_title_bar_height(self):
        client_rect = win32structures.RECT(*win32gui.GetClientRect(self.hwnd))
        return self.get_rect().height() - client_rect.height()

    def draw_rect(self, rect: win32structures.RECT, color: tuple[int, int, int]):
        dc_handle = win32gui.GetDC(self.hwnd)
        brush = win32gui.CreateSolidBrush(win32api.RGB(*color))
        win32gui.SelectObject(dc_handle, brush)
        win32gui.FrameRect(
            dc_handle, (rect.left, rect.top, rect.right, rect.bottom), brush
        )

    def get_path(self) -> str:
        _, pid = win32process.GetWindowThreadProcessId(self.hwnd)
        process = psutil.Process(pid)
        return process.exe()

    def focus(self):
        remote_thread, _ = win32process.GetWindowThreadProcessId(self.hwnd)
        win32process.AttachThreadInput(
            win32api.GetCurrentThreadId(), remote_thread, True
        )
        win32gui.SetForegroundWindow(self.hwnd)
        # win32gui.SetFocus(self.id)
        # win32gui.SendMessage(
        #     self.id,
        #     win32con.WM_UPDATEUISTATE,
        #     win32api.MAKELONG(win32ui.UIS_CLEAR, win32con.UISF_HIDEFOCUS),
        #     0,
        # )

    def is_minimized(self):
        return win32gui.IsIconic(self.hwnd)

    def is_maximized(self):
        return not self.is_minimized()

    def minimize(self):
        win32gui.ShowWindow(self.hwnd, win32con.SW_MINIMIZE)

    def maximize(self):
        win32gui.ShowWindow(self.hwnd, win32con.SW_RESTORE)

    def screenshot(self, file_path: str):
        self.focus()
        rect = self.get_rect()
        capture = self.window.capture_as_image(rect)
        capture.save(file_path)
        print(f'screenshot saved at: "{file_path}"')
