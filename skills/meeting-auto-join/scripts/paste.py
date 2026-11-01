"""剪贴板粘贴（中文 / 标点 / 表情唯一稳妥的输入方式）。

用法：
    python paste.py "收到，我七点到"
    python paste.py "新内容" --replace          # 先 Ctrl+A 覆盖原有内容
    python paste.py "内容" --title 微信         # 推荐：粘之前确认前台是目标窗口
    python paste.py --get                       # 读当前剪贴板
    python paste.py "abc" --set-only            # 只写剪贴板，不按 Ctrl+V

--title 的安全闸很重要：Ctrl+V 只会发给**当前前台窗口**，如果前台已经不是目标程序，
内容会粘到别的窗口里（实测过一次，粘进了宿主程序的输入框）。
"""
import ctypes
import sys
import time

import winutil

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

kernel32.GlobalAlloc.restype = ctypes.c_void_p
kernel32.GlobalAlloc.argtypes = [ctypes.c_uint, ctypes.c_size_t]
kernel32.GlobalLock.restype = ctypes.c_void_p
kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
user32.SetClipboardData.restype = ctypes.c_void_p
user32.SetClipboardData.argtypes = [ctypes.c_uint, ctypes.c_void_p]
user32.GetClipboardData.restype = ctypes.c_void_p
user32.GetClipboardData.argtypes = [ctypes.c_uint]

CF_UNICODETEXT = 13
GMEM_MOVEABLE = 0x0002
KEYEVENTF_KEYUP = 0x0002
VK_CONTROL, VK_V, VK_A = 0x11, 0x56, 0x41


def set_clipboard(text):
    for _ in range(6):
        if user32.OpenClipboard(0):
            break
        time.sleep(0.15)
    else:
        raise SystemExit("剪贴板被别的程序占用，稍后重试")
    user32.EmptyClipboard()
    size = (len(text) + 1) * 2
    h = kernel32.GlobalAlloc(GMEM_MOVEABLE, size)
    p = kernel32.GlobalLock(h)
    ctypes.memmove(p, ctypes.create_unicode_buffer(text), size)
    kernel32.GlobalUnlock(h)
    user32.SetClipboardData(CF_UNICODETEXT, h)   # 交给系统后不要再 GlobalFree
    user32.CloseClipboard()


def get_clipboard():
    if not user32.OpenClipboard(0):
        return None
    try:
        h = user32.GetClipboardData(CF_UNICODETEXT)
        if not h:
            return None
        p = kernel32.GlobalLock(ctypes.c_void_p(h))
        text = ctypes.wstring_at(p)
        kernel32.GlobalUnlock(ctypes.c_void_p(h))
        return text
    finally:
        user32.CloseClipboard()


def tap(vk, ctrl=False):
    if ctrl:
        user32.keybd_event(VK_CONTROL, 0, 0, 0)
        time.sleep(0.04)
    user32.keybd_event(vk, 0, 0, 0)
    time.sleep(0.05)
    user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)
    if ctrl:
        time.sleep(0.04)
        user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)


if __name__ == "__main__":
    argv = sys.argv[1:]
    args, flags, must = [], set(), None
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--title":
            must = argv[i + 1] if i + 1 < len(argv) else ""
            i += 2
            continue
        if a.startswith("--"):
            flags.add(a)
        else:
            args.append(a)
        i += 1

    text = args[0] if args else ""

    if "--get" in flags:
        print(repr(get_clipboard()))
        sys.exit(0)

    if must and must not in winutil.foreground_title():
        if winutil.ensure_focus(must):
            time.sleep(0.3)
    if must and must not in winutil.foreground_title():
        print("abort: 前台是 %r，不匹配 %r，未粘贴" % (winutil.foreground_title(), must))
        sys.exit(3)

    set_clipboard(text)
    time.sleep(0.2)

    if "--set-only" in flags:
        print("clipboard set:", repr(get_clipboard()))
        sys.exit(0)

    if "--replace" in flags:
        tap(VK_A, ctrl=True)
        time.sleep(0.1)

    tap(VK_V, ctrl=True)
    time.sleep(0.2)
    print("pasted:", text)
