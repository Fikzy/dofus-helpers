import os
import threading
import time

import cv2
import numpy
import pytesseract
import win32api
import win32con
import win32gui
from PIL import Image
from pywinauto import win32structures

import exec_handler
import pathfinding
from world_graph import WorlGraph

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

MOVE_TIMEOUT = 15


class DofusHandler(exec_handler.ExecHandler):

    world_graph: WorlGraph

    def __init__(self):
        super().__init__(".* - Dofus .*")

        exec_path = self.get_path()
        game_directory = os.path.dirname(exec_path)
        self.world_graph = WorlGraph(game_directory)

        os.environ["TESSDATA_PREFIX"] = "./tesseract-data"

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

    def read_map_coordinates(self) -> tuple[int, int]:
        """
        Read map coordinates from screen using Tesseract.

        Subject to failure against white backgrounds: example at (-10,-19)
        """
        img = self.capture_client(self.get_map_coordinates_bounds())

        img = cv2.cvtColor(numpy.array(img), cv2.COLOR_RGB2GRAY)  # convert to cv2

        # threshold, keep values in [228; 229]
        img[img < 228] = 0
        img[img > 229] = 0

        # pad to help Tesseract
        img = cv2.copyMakeBorder(img, 10, 5, 10, 0, cv2.BORDER_CONSTANT)

        # remove noise
        img = cv2.morphologyEx(
            img, cv2.MORPH_OPEN, cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        )

        # invert, better for Tesseract?
        img = 255 - img

        # convert back to PIL image
        img = Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))

        config = (
            "--psm 7 "  # treat image as single text line
            "-c tessedit_char_whitelist=0123456789-, "
        )

        text: str = pytesseract.image_to_string(img, lang="fra-tahoma", config=config)
        text_elements = text.split(",")

        try:
            return int(text_elements[0].strip()), int(text_elements[1].strip())
        except:
            print("Failed to read map coordinates from screen.")

        return None

    def __move_to_adjacent_pos(self, curr: tuple[int, int], dest: tuple[int, int]):

        dx = dest[0] - curr[0]
        dy = dest[1] - curr[1]

        if dx == -1:
            print("moving left")
            self.move_left()
        elif dx == 1:
            print("moving right")
            self.move_right()
        elif dy == -1:
            print("moving up")
            self.move_up()
        elif dy == 1:
            print("moving down")
            self.move_down()
        else:
            print("Can only move to an adjacent map.")

    def __go_to_dest(self, map_id: int, dest: tuple[int, int]):

        print(f"Auto travel map_id: {map_id}, dest: {dest}")

        path = pathfinding.find_path(self.world_graph, map_id, (dest[0], dest[1]))
        print(path)

        if not path:
            return

        path.reverse()
        goal_pos = path.pop()

        last_move_time = time.time()

        while len(path) > 0:
            read_pos = self.read_map_coordinates()
            elapsed_since_last_move = time.time() - last_move_time

            if goal_pos == read_pos or elapsed_since_last_move > MOVE_TIMEOUT:

                if elapsed_since_last_move > MOVE_TIMEOUT:
                    print(
                        "Move timed out. Make sure map coordinates are visible (settings) "
                        "and not obstructed by any UI elements."
                    )

                prev_pos = goal_pos
                goal_pos = path.pop()
                last_move_time = time.time()
                self.__move_to_adjacent_pos(prev_pos, goal_pos)

            time.sleep(1)

        print("Destination reached!")

    def go_to_dest(self, map_id: str, dest: tuple[str, str]):

        if not map_id or not dest[0] or not dest[1]:
            return

        thread = threading.Thread(
            target=self.__go_to_dest, args=(int(map_id), (int(dest[0]), int(dest[1])))
        )
        thread.start()
