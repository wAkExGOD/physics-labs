"""Capture the supplied Windows executable without modifying its files.

Only windows belonging to the
newly launched example process are inspected; screenshots are window crops.
"""
from pathlib import Path
import ctypes as ct
from ctypes import wintypes as wt
import json
import subprocess
import sys
import time

from PIL import ImageGrab

OUT = Path(__file__).resolve().parent
LAB = OUT.parent
U = ct.WinDLL("user32", use_last_error=True)
CALLBACK = ct.WINFUNCTYPE(wt.BOOL, wt.HWND, wt.LPARAM)
U.EnumWindows.argtypes = [CALLBACK, wt.LPARAM]
U.EnumChildWindows.argtypes = [wt.HWND, CALLBACK, wt.LPARAM]
U.GetWindowThreadProcessId.argtypes = [wt.HWND, ct.POINTER(wt.DWORD)]
U.GetWindowTextW.argtypes = [wt.HWND, wt.LPWSTR, ct.c_int]
U.GetClassNameW.argtypes = [wt.HWND, wt.LPWSTR, ct.c_int]
U.GetWindowRect.argtypes = [wt.HWND, ct.POINTER(wt.RECT)]
U.GetClientRect.argtypes = [wt.HWND, ct.POINTER(wt.RECT)]
U.GetParent.argtypes = [wt.HWND]
U.GetParent.restype = wt.HWND
U.SendMessageW.argtypes = [wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM]
U.SendMessageW.restype = ct.c_ssize_t
U.PostMessageW.argtypes = [wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM]
U.ShowWindow.argtypes = [wt.HWND, ct.c_int]
U.MoveWindow.argtypes = [wt.HWND, ct.c_int, ct.c_int, ct.c_int, ct.c_int, wt.BOOL]
U.GetMenu.argtypes = [wt.HWND]
U.GetMenu.restype = wt.HMENU
U.GetSubMenu.argtypes = [wt.HMENU, ct.c_int]
U.GetSubMenu.restype = wt.HMENU
U.GetMenuItemCount.argtypes = [wt.HMENU]
U.GetMenuItemID.argtypes = [wt.HMENU, ct.c_int]
U.GetMenuStringW.argtypes = [wt.HMENU, wt.UINT, wt.LPWSTR, ct.c_int, wt.UINT]
U.IsWindowVisible.argtypes = [wt.HWND]
try:
    U.SetProcessDPIAware()
except AttributeError:
    pass


def info(hwnd):
    name, cls = ct.create_unicode_buffer(1024), ct.create_unicode_buffer(256)
    U.GetWindowTextW(hwnd, name, len(name))
    U.GetClassNameW(hwnd, cls, len(cls))
    rect = wt.RECT()
    U.GetWindowRect(hwnd, ct.byref(rect))
    return {"hwnd": int(hwnd), "class": cls.value, "text": name.value,
            "rect": [rect.left, rect.top, rect.right, rect.bottom],
            "parent": int(U.GetParent(hwnd) or 0), "visible": bool(U.IsWindowVisible(hwnd))}


def windows(pid):
    result = []
    @CALLBACK
    def visit(hwnd, _):
        owner = wt.DWORD()
        U.GetWindowThreadProcessId(hwnd, ct.byref(owner))
        if owner.value == pid:
            result.append(info(hwnd))
        return True
    U.EnumWindows(visit, 0)
    return result


def children(hwnd):
    result = []
    @CALLBACK
    def visit(child, _):
        result.append(info(child))
        return True
    U.EnumChildWindows(hwnd, visit, 0)
    return result


def menus(menu):
    result = []
    for i in range(U.GetMenuItemCount(menu)):
        text = ct.create_unicode_buffer(256)
        U.GetMenuStringW(menu, i, text, len(text), 0x400)
        sub = U.GetSubMenu(menu, i)
        result.append({"text": text.value, "id": U.GetMenuItemID(menu, i),
                       "children": menus(sub) if sub else []})
    return result


def set_text(hwnd, text):
    value = ct.create_unicode_buffer(str(text))
    U.SendMessageW(hwnd, 0xC, 0, ct.cast(value, ct.c_void_p).value)


def click(hwnd):
    U.PostMessageW(hwnd, 0xF5, 0, 0)


def click_at(hwnd, x, y):
    packed = (int(y) << 16) | int(x)
    U.PostMessageW(hwnd, 0x201, 1, packed)
    U.PostMessageW(hwnd, 0x202, 0, packed)


def capture(hwnd, name):
    time.sleep(0.25)
    path = OUT / name
    ImageGrab.grab(window=hwnd).save(path)
    return str(path)


def find_window(pid, cls, timeout=8):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        match = [w for w in windows(pid) if w["class"] == cls and w["visible"]]
        if match:
            return match[0]["hwnd"]
        time.sleep(0.1)
    raise RuntimeError(f"Window {cls} not found: {windows(pid)}")


def launch():
    startup = subprocess.STARTUPINFO()
    startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startup.wShowWindow = 0
    # The source allows a non-"noquest" argument to skip the entrance quiz.
    process = subprocess.Popen([str(LAB / "app-example" / "difraction.exe"), "comparison"],
                               cwd=LAB / "app-example", startupinfo=startup)
    # Main form may explicitly maximize itself; do not change other instances.
    end = time.monotonic() + 10
    while time.monotonic() < end:
        current = windows(process.pid)
        about = [w for w in current if w["class"] == "TAboutDlg" and w["visible"]]
        if about:
            buttons = [w for w in children(about[0]["hwnd"]) if w["class"] in ("TButton", "TBitBtn")]
            if buttons:
                click(buttons[0]["hwnd"])
            else:
                U.PostMessageW(about[0]["hwnd"], 0x100, 0xD, 0)
            time.sleep(0.25)
        match = [w for w in current if w["class"] == "TMainForm"]
        if match:
            hwnd = match[0]["hwnd"]
            U.ShowWindow(hwnd, 1)
            U.ShowWindow(hwnd, 9)
            U.MoveWindow(hwnd, 20, 20, 1260, 960, True)
            time.sleep(0.3)
            return process, hwnd
        time.sleep(0.1)
    state = windows(process.pid)
    process.terminate()
    raise RuntimeError(f"Example failed to start: {state}")


