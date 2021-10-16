import ctypes
from typing import Any
import cv2
import numpy
from numpy.core.fromnumeric import ptp
import win32api
import win32con
import win32gui
import win32ui

from dataclasses import dataclass
from pywinauto.win32structures import RECT
from pywinauto.application import Application


SCREENSHOT_FILE = 'tmp\screenshot.png'
TEMPLATE_FILE = 'templates\inventory_icon.png'
# TEMPLATE_FILE = 'templates\inventory_full_template.png'

TITLE_BAR_H = 30


@dataclass
class App:

    id: int
    window: Any

    def __post_init__(self):
        _dc = win32gui.GetDC(self.id)
        self.dc = win32ui.CreateDCFromHandle(_dc)
        print('app_id:', self.id)

    def focus(self):
        self.window.set_focus()

    def minimize(self):
        win32gui.ShowWindow(self.id, win32con.SW_MINIMIZE)

    def get_rect(self, standard=False):
        rect = RECT()
        DWMWA_EXTENDED_FRAME_BOUNDS = 9
        ctypes.windll.dwmapi.DwmGetWindowAttribute(
            ctypes.wintypes.HWND(self.id),
            ctypes.wintypes.DWORD(DWMWA_EXTENDED_FRAME_BOUNDS),
            ctypes.byref(rect),
            ctypes.sizeof(rect)
        )
        if standard:
            return (rect.left, rect.top, rect.right - rect.left, rect.bottom - rect.top)
        return rect

    def take_screen(self, path='screenshot.png'):
        self.focus()
        rect = self.get_rect()
        capture = self.window.capture_as_image(rect)
        capture.save(path)
        print(f'screenshot saved: "{path}"')


def get_app(app_title_regex):

    try:
        app = Application().connect(title_re=app_title_regex)
    except Exception:
        return None

    hwin = app.top_window()
    window_title = hwin.window_text()
    hwnd = win32gui.FindWindow(None, window_title)

    return App(hwnd, hwin)


def find_inventory_loc(img, template):

    res = cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED)

    threshold = 0.9

    loc = numpy.where(res >= threshold)

    if len(loc[0]) == 0:
        print('inventory not found')
        return None

    return loc


def draw_temaplate_loc_on_img(img, template, loc):

    w, h = template.shape[::-1]

    for pt in zip(*loc[::-1]):
        cv2.rectangle(img, pt, (pt[0] + w, pt[1] + h), (0, 255, 255), 2)

    cv2.imwrite('tmp\detected.png', img)
    # cv2.imshow('detected', img)
    # cv2.waitKey(0)


def draw_temaplate_loc_on_screen(app_id, template, loc):

    w, h = template.shape[::-1]
    y, x = numpy.min(loc[0]), numpy.min(loc[1])
    y -= TITLE_BAR_H

    rect = (x, y, x + w, y + h)
    print(rect)

    # window_rect = win32gui.GetWindowRect(app_id)
    # print(window_rect)

    dc = win32gui.GetDC(app_id)
    dc_obj = win32ui.CreateDCFromHandle(dc)

    while(True):

        dc_obj.Rectangle(rect)
        # Refresh the entire monitor
        win32gui.InvalidateRect(app_id, rect, False)

        win32api.Sleep(1)


def draw_rect_on_app(app_id, rect):

    dc = win32gui.GetDC(app_id)
    dc_obj = win32ui.CreateDCFromHandle(dc)
    dc_obj.Rectangle(rect)


if __name__ == '__main__':

    app = get_app(app_title_regex='Fikzy - Dofus.*')

    if app is None:
        raise SystemExit('App not found!')

    app.take_screen()

    # img = cv2.imread(SCREENSHOT_FILE, 0)
    # template = cv2.imread(TEMPLATE_FILE, 0)

    # loc = find_inventory_loc(img, template)

    # if loc:

    #     # draw_temaplate_loc_on_img(img, template, loc)
    #     draw_temaplate_loc_on_screen(app_id, template, loc)
