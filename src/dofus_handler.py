import pytesseract
import win32api
import win32con
import win32gui
from PIL import ImageOps
from pywinauto import win32structures

import exec_handler

GAME_REF_WIDTH = 1350
GAME_REF_HEIGHT = 1080

MOVE_ZONE_LATERAL_COEF = 32 / GAME_REF_WIDTH
MOVE_ZONE_TOP_COEF = 18 / GAME_REF_HEIGHT
MOVE_ZONE_BOTTOM_COEF = 145 / GAME_REF_HEIGHT
MOVE_ZONE_BOTTOM_CLICKABLE_COEF = 24 / GAME_REF_HEIGHT

MAP_COORD_TL_COEFS = (18 / GAME_REF_WIDTH, 53 / GAME_REF_HEIGHT)
MAP_COORD_BR_COEFS = (131 / GAME_REF_WIDTH, 79 / GAME_REF_HEIGHT)

GAME_REF_RATIO = 1.25
GAME_EXTENDED_REF_RATIO = 1.93


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
        aspect_ratio = rect.width() / rect.height()

        if aspect_ratio > GAME_REF_RATIO:
            width = rect.height() * GAME_REF_RATIO
            w_diff = rect.width() - width
            bounds = (w_diff / 2, 0, rect.width() - w_diff / 2, rect.height())
        else:
            height = rect.width() / GAME_REF_RATIO
            h_diff = rect.height() - height
            bounds = (0, h_diff / 2, rect.width(), rect.height() - h_diff / 2)

        return win32structures.RECT(*bounds)

    def get_game_extended_bounds(self):
        rect = win32structures.RECT(*win32gui.GetClientRect(self.hwnd))
        aspect_ratio = rect.width() / rect.height()

        if aspect_ratio > GAME_EXTENDED_REF_RATIO:
            bounds = win32structures.RECT(rect)
            width = int(rect.height() * GAME_EXTENDED_REF_RATIO)
            w_diff = rect.width() - width
            bounds.left = w_diff // 2
            bounds.right -= w_diff // 2
            return bounds

        return rect

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

    def get_map_coordinates_bounds(self) -> win32structures.RECT:
        bounds = self.get_game_bounds()
        extended_bounds = self.get_game_extended_bounds()
        return win32structures.RECT(
            extended_bounds.left + bounds.width() * MAP_COORD_TL_COEFS[0],
            bounds.top + bounds.height() * MAP_COORD_TL_COEFS[1],
            extended_bounds.left + bounds.width() * MAP_COORD_BR_COEFS[0],
            bounds.top + bounds.height() * MAP_COORD_BR_COEFS[1],
        )

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

    def read_map_coordinates(self):
        """
        Read map coordinates from screen using Tesseract.
        Not perfect but usable for now. WIP.
        """
        img = self.capture_client(self.get_map_coordinates_bounds())

        img = ImageOps.grayscale(img)
        img = img.point(lambda p: 255 if p >= 228 else 0)  # threshold

        # pad image to center text
        img = ImageOps.pad(img, size=(img.width, img.height + 9), centering=(0, 0.75))
        img = ImageOps.pad(img, size=(img.width + 10, img.height), centering=(1, 0))

        return pytesseract.image_to_string(img)

    def go_to_dest(self, map_id: str, dest: tuple[str, str]):
        print(f"map_id: {map_id}, dest: {dest}")
