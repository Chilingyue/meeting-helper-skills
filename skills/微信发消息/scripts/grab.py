"""按窗口截图 → 1:1 PNG（纯 ctypes + 标准库，不装任何第三方包）。

为什么不用全屏截图：全屏图 1920 宽会被各种看图工具缩放到 ~1092 再显示，目测出来的
坐标要乘 1.758 才准，这是"点空"的头号原因。窗口图通常 ~1000 宽，不被缩放，
**图上的坐标 + origin 就是屏幕坐标**，不用换算。

两种抓法，自动选择：
  print  : PrintWindow(PW_RENDERFULLCONTENT) 让窗口自己渲染一份，被别的窗口压住也能截到
  screen : 从屏幕上抠窗口矩形，需要窗口在前台（print 拿到空白图时自动回退）

坐标一致性：Windows 10/11 的窗口有约 7px 不可见边框，GetWindowRect 含它而屏幕上看不到。
本脚本用 DwmGetWindowAttribute(EXTENDED_FRAME_BOUNDS) 取"可见边框"，并把 print 结果
按同样的偏移裁掉多余边缘，所以两种抓法得到的图与 origin 完全对齐。

用法：
    python grab.py 微信 shot.png             # 截标题含"微信"的窗口
    python grab.py 微信 shot.png --scale 2   # 放大 2 倍（看小字/图标状态）
    python grab.py 微信 shot.png --screen    # 强制从屏幕抠（要求窗口在前台）
    python grab.py 微信 shot.png --no-raise  # 不抢前台
    python grab.py full shot.png             # 整个虚拟桌面
"""
import ctypes
import sys
import time
from ctypes import wintypes

import pngio
import winutil

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32

PW_RENDERFULLCONTENT = 0x00000002
SRCCOPY = 0x00CC0020
DIB_RGB_COLORS = 0
BI_RGB = 0
DWMWA_EXTENDED_FRAME_BOUNDS = 9
SM_XVIRTUALSCREEN, SM_YVIRTUALSCREEN = 76, 77
SM_CXVIRTUALSCREEN, SM_CYVIRTUALSCREEN = 78, 79


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [("biSize", wintypes.DWORD), ("biWidth", wintypes.LONG),
                ("biHeight", wintypes.LONG), ("biPlanes", wintypes.WORD),
                ("biBitCount", wintypes.WORD), ("biCompression", wintypes.DWORD),
                ("biSizeImage", wintypes.DWORD), ("biXPelsPerMeter", wintypes.LONG),
                ("biYPelsPerMeter", wintypes.LONG), ("biClrUsed", wintypes.DWORD),
                ("biClrImportant", wintypes.DWORD)]


def frame_bounds(hwnd):
    """窗口的可见边框 (x,y,w,h)。取不到就退回 GetWindowRect。"""
    r = wintypes.RECT()
    try:
        hr = ctypes.windll.dwmapi.DwmGetWindowAttribute(
            wintypes.HWND(hwnd), ctypes.c_uint(DWMWA_EXTENDED_FRAME_BOUNDS),
            ctypes.byref(r), ctypes.sizeof(r))
        if hr == 0 and r.right > r.left and r.bottom > r.top:
            return r.left, r.top, r.right - r.left, r.bottom - r.top
    except Exception:
        pass
    return winutil.rect_of(hwnd)


def _to_rgb(buf, w, h):
    """32bit BGRA（自顶向下）→ RGB bytes。"""
    mv = memoryview(buf.raw if hasattr(buf, "raw") else buf)
    rgb = bytearray(w * h * 3)
    rgb[0::3] = bytes(mv[2::4])
    rgb[1::3] = bytes(mv[1::4])
    rgb[2::3] = bytes(mv[0::4])
    return bytes(rgb)


def _blit(src_dc, hwnd, w, h, sx, sy, use_print):
    hdc_mem = gdi32.CreateCompatibleDC(src_dc)
    hbm = gdi32.CreateCompatibleBitmap(src_dc, w, h)
    old = gdi32.SelectObject(hdc_mem, hbm)
    try:
        if use_print:
            ok = user32.PrintWindow(hwnd, hdc_mem, PW_RENDERFULLCONTENT)
        else:
            ok = gdi32.BitBlt(hdc_mem, 0, 0, w, h, src_dc, sx, sy, SRCCOPY)

        bi = BITMAPINFOHEADER()
        bi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        bi.biWidth = w
        bi.biHeight = -h
        bi.biPlanes = 1
        bi.biBitCount = 32
        bi.biCompression = BI_RGB
        buf = ctypes.create_string_buffer(w * h * 4)
        gdi32.GetDIBits(hdc_mem, hbm, 0, h, buf, ctypes.byref(bi), DIB_RGB_COLORS)
        return bool(ok), _to_rgb(buf, w, h)
    finally:
        if old:
            gdi32.SelectObject(hdc_mem, old)
        gdi32.DeleteObject(hbm)
        gdi32.DeleteDC(hdc_mem)


def capture_window(hwnd, raise_window=True, force_screen=False):
    """截一个窗口，返回 (w, h, rgb, (origin_x, origin_y), info)。"""
    if raise_window:
        winutil.focus_verified(hwnd, tries=4)
        time.sleep(0.15)

    wx, wy, ww, wh = winutil.rect_of(hwnd)
    fx, fy, fw, fh = frame_bounds(hwnd)
    dx, dy = fx - wx, fy - wy                 # 不可见边框的偏移

    method = "screen"
    if force_screen:
        hdc_screen = user32.GetDC(0)
        try:
            _ok, rgb_full = _blit(hdc_screen, hwnd, ww, wh, wx, wy, use_print=False)
        finally:
            user32.ReleaseDC(0, hdc_screen)
        w, h, rgb = pngio.crop_rgb(ww, wh, rgb_full, dx, dy, fw, fh)
    else:
        hdc_screen = user32.GetDC(0)
        try:
            _ok, rgb_full = _blit(hdc_screen, hwnd, ww, wh, wx, wy, use_print=True)
        finally:
            user32.ReleaseDC(0, hdc_screen)
        w, h, rgb = pngio.crop_rgb(ww, wh, rgb_full, dx, dy, fw, fh)
        _mean, lo, hi, colors = pngio.stats(w, h, rgb)
        if hi - lo < 4 or colors <= 2:        # 全黑/全白 = PrintWindow 没渲染出来
            method = "screen(fallback)"
            hdc_screen = user32.GetDC(0)
            try:
                _ok, rgb_full = _blit(hdc_screen, hwnd, ww, wh, wx, wy, use_print=False)
            finally:
                user32.ReleaseDC(0, hdc_screen)
            w, h, rgb = pngio.crop_rgb(ww, wh, rgb_full, dx, dy, fw, fh)
        else:
            method = "print"

    info = {"hwnd": hwnd, "title": winutil.title_of(hwnd),
            "visible": bool(user32.IsWindowVisible(hwnd)),
            "rect": (fx, fy, fw, fh), "method": method,
            "dpi_scale": winutil.dpi_scale()}
    return w, h, rgb, (fx, fy), info


def capture(substr, raise_window=True, force_screen=False):
    """按标题片段截窗口，返回 (w, h, rgb, origin, info)；找不到返回 (None,)*5。"""
    hits = winutil.find(substr)
    if not hits:
        return None, None, None, None, None
    return capture_window(hits[0][0], raise_window, force_screen)


def capture_screen():
    x = user32.GetSystemMetrics(SM_XVIRTUALSCREEN)
    y = user32.GetSystemMetrics(SM_YVIRTUALSCREEN)
    w = user32.GetSystemMetrics(SM_CXVIRTUALSCREEN)
    h = user32.GetSystemMetrics(SM_CYVIRTUALSCREEN)
    hdc_screen = user32.GetDC(0)
    try:
        _ok, rgb = _blit(hdc_screen, 0, w, h, x, y, use_print=False)
    finally:
        user32.ReleaseDC(0, hdc_screen)
    return w, h, rgb, (x, y), {"hwnd": 0, "title": "<virtual screen>", "visible": True,
                               "rect": (x, y, w, h), "method": "screen",
                               "dpi_scale": winutil.dpi_scale()}


def save(path, w, h, rgb, scale=1):
    if scale != 1:
        w, h, rgb = pngio.scale_rgb(w, h, rgb, scale)
    pngio.write_png(path, w, h, rgb)
    return w, h


if __name__ == "__main__":
    argv = sys.argv[1:]
    scale = 1
    flags = set()
    pos = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--scale":
            scale = int(argv[i + 1])
            i += 2
            continue
        if a.startswith("--"):
            flags.add(a)
        else:
            pos.append(a)
        i += 1

    target = pos[0] if pos else "微信"
    out = pos[1] if len(pos) > 1 else "shot.png"

    if target.lower() == "full":
        w, h, rgb, origin, info = capture_screen()
    else:
        w, h, rgb, origin, info = capture(
            target,
            raise_window=("--no-raise" not in flags),
            force_screen=("--screen" in flags))
        if w is None:
            print("no window matched:", target)
            print("可见窗口如下，可用其中任意片段重试：")
            for h_, t, vis, r in winutil.list_titled():
                if vis and r[2] > 80:
                    print("  ", h_, repr(t), r)
            sys.exit(2)

    nw, nh = save(out, w, h, rgb, scale)
    print("window:", info["hwnd"], repr(info["title"]),
          "visible" if info["visible"] else "hidden",
          "rect", info["rect"], "dpi", info["dpi_scale"])
    print("saved", out, "%dx%d" % (nw, nh), "origin", origin[0], origin[1],
          "| method", info["method"])
    if scale != 1:
        print("注意：--scale 只用于人眼看图；图上坐标要先除 %d 再加 origin" % scale)
