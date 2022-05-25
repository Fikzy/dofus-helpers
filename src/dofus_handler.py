from numpy import rec
import win32api
import win32con
import win32gui
from pywinauto import win32structures

import exec_handler

MOVE_ZONE_LATERAL_COEF = 32 / 1350
MOVE_ZONE_TOP_COEF = 18 / 1080
MOVE_ZONE_BOTTOM_COEF = 145 / 1080
MOVE_ZONE_BOTTOM_CLICKABLE_COEF = 24 / 1080


class DofusHandler(exec_handler.ExecHandler):

    title_bar_height: int

    def __init__(self):
        super().__init__(".* - Dofus .*")

    def click(self, x: int, y: int, button: str = "left"):
        l_param = win32api.MAKELONG(int(x), int(y))
        if button == "left":
            win32gui.SendMessage(
                self.hwnd, win32con.WM_LBUTTONDOWN, win32con.MK_LBUTTON, l_param
            )
            win32gui.SendMessage(
                self.hwnd, win32con.WM_LBUTTONUP, win32con.MK_LBUTTON, l_param
            )
        elif button == "right":
            win32gui.SendMessage(self.hwnd, win32con.WM_RBUTTONDOWN, 0, l_param)
            win32gui.SendMessage(self.hwnd, win32con.WM_RBUTTONUP, 0, l_param)

    def get_game_bounds(self) -> win32structures.RECT:
        rect = win32structures.RECT(*win32gui.GetClientRect(self.hwnd))
        ref_ratio = 1.25
        aspect_ratio = rect.width() / rect.height()

        if aspect_ratio > ref_ratio:
            width = rect.height() * 1.25
            w_diff = rect.width() - width
            bounds = (w_diff / 2, 0, rect.width() - w_diff / 2, rect.height())
        else:
            height = rect.width() / 1.25
            h_diff = rect.height() - height
            bounds = (0, h_diff / 2, rect.width(), rect.height() - h_diff / 2)

        return win32structures.RECT(*bounds)

    def get_move_zones(self) -> win32structures.RECT:
        bounds = self.get_game_bounds()
        lateral = int(bounds.width() * MOVE_ZONE_LATERAL_COEF)
        top = int(bounds.height() * MOVE_ZONE_TOP_COEF)
        bottom = int(bounds.height() * MOVE_ZONE_BOTTOM_COEF)

        zones = win32structures.RECT(bounds)
        zones.left += lateral
        zones.right -= lateral
        zones.top += top
        zones.bottom -= bottom

        return zones

    def move_left(self):
        bounds = self.get_game_bounds()
        lateral_zone = int(bounds.width() * MOVE_ZONE_LATERAL_COEF)
        self.click(
            bounds.left + lateral_zone / 2,
            bounds.top + bounds.height() / 2,
        )

    def move_right(self):
        bounds = self.get_game_bounds()
        lateral_zone = int(bounds.width() * MOVE_ZONE_LATERAL_COEF)
        self.click(
            bounds.right - lateral_zone / 2,
            bounds.top + bounds.height() / 2,
        )

    def move_up(self):
        bounds = self.get_game_bounds()
        top_zone = int(bounds.height() * MOVE_ZONE_TOP_COEF)
        self.click(
            bounds.left + bounds.width() / 2,
            bounds.top + top_zone / 2,
        )

    def move_down(self):
        bounds = self.get_game_bounds()
        bottom_zone = int(bounds.height() * MOVE_ZONE_BOTTOM_COEF)
        clickable_zone = int(bounds.height() * MOVE_ZONE_BOTTOM_CLICKABLE_COEF)
        self.click(
            bounds.left + bounds.width() / 2,
            bounds.bottom - bottom_zone + clickable_zone / 2,
        )

    def go_to_dest(self, map_id: str, dest: tuple[str, str]):
        print(f"map_id: {map_id}, dest: {dest}")
