"""Win32 窗口工具：找窗口 / 置前 / 命中测试。仅依赖 ctypes（随 Python 自带）。

所有脚本共用的唯一底层模块，改这里就够，不用在别处重复实现。
"""
import ctypes
import time
from ctypes import wintypes

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# 进程级 DPI 感知：不做这一步，高缩放下 GetWindowRect 返回的是逻辑坐标，
# 与真实像素差一个缩放倍数，点哪都偏。必须在任何窗口 API 之前调用。
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)      # PER_MONITOR_AWARE_V2
except Exception:
    try:
        user32.SetProcessDPIAware()
    except Exception:
        pass

EnumProc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
GA_ROOT = 2
SW_RESTORE = 9


def dpi_scale():
    """当前主显示器缩放倍数（1.0 = 100%），只用来在日志里提示，不影响坐标。"""
    try:
        dpi = user32.GetDpiForSystem()
        return round(dpi / 96.0, 2)
    except Exception:
        hdc = user32.GetDC(0)
        try:
            return round(ctypes.windll.gdi32.GetDeviceCaps(hdc, 88) / 96.0, 2)
        finally:
            user32.ReleaseDC(0, hdc)


def title_of(hwnd):
    n = user32.GetWindowTextLengthW(hwnd)
    if not n:
        return ""
    buf = ctypes.create_unicode_buffer(n + 1)
    user32.GetWindowTextW(hwnd, buf, n + 1)
    return buf.value


def rect_of(hwnd):
    r = wintypes.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(r))
    return r.left, r.top, r.right - r.left, r.bottom - r.top


def client_rect_of(hwnd):
    """客户区（不含标题栏边框）在屏幕上的位置，某些窗口要用它算坐标。"""
    r = wintypes.RECT()
    user32.GetClientRect(hwnd, ctypes.byref(r))
    pt = wintypes.POINT(0, 0)
    user32.ClientToScreen(hwnd, ctypes.byref(pt))
    return pt.x, pt.y, r.right - r.left, r.bottom - r.top


def find(substr, include_hidden=True):
    """按标题片段找窗口，返回 [(hwnd, title, visible, (x,y,w,h))]，可见的排前面、大的排前面。"""
    hits = []

    def cb(h, _):
        t = title_of(h)
        if t and substr in t:
            vis = bool(user32.IsWindowVisible(h))
            if include_hidden or vis:
                hits.append((h, t, vis, rect_of(h)))
        return True

    user32.EnumWindows(EnumProc(cb), 0)
    hits.sort(key=lambda x: (not x[2], -(x[3][2] * x[3][3])))
    return hits


def list_titled():
    """列出所有有标题的窗口，找不到目标时用它排查。"""
    out = []

    def cb(h, _):
        t = title_of(h)
        if t:
            out.append((h, t, bool(user32.IsWindowVisible(h)), rect_of(h)))
        return True

    user32.EnumWindows(EnumProc(cb), 0)
    return out


def foreground_hwnd():
    return user32.GetForegroundWindow()


def foreground_title():
    return title_of(foreground_hwnd())


def focus(hwnd):
    """恢复 + 抢前台。AttachThreadInput 是为了绕开 Windows 的前台锁。"""
    if not user32.IsWindowVisible(hwnd):
        user32.ShowWindow(hwnd, SW_RESTORE)
        time.sleep(0.25)
    if user32.IsIconic(hwnd):
        user32.ShowWindow(hwnd, SW_RESTORE)
        time.sleep(0.25)

    fg = user32.GetForegroundWindow()
    if fg == hwnd:
        return True

    cur = kernel32.GetCurrentThreadId()
    fg_tid = user32.GetWindowThreadProcessId(fg, None)
    tg_tid = user32.GetWindowThreadProcessId(hwnd, None)
    user32.AttachThreadInput(cur, fg_tid, True)
    user32.AttachThreadInput(cur, tg_tid, True)
    user32.BringWindowToTop(hwnd)
    user32.SetForegroundWindow(hwnd)
    user32.AttachThreadInput(cur, fg_tid, False)
    user32.AttachThreadInput(cur, tg_tid, False)
    time.sleep(0.2)
    return user32.GetForegroundWindow() == hwnd


def focus_verified(hwnd, tries=8):
    """置前后校验前台确实是它，被别的窗口抢回就重试。返回尝试次数，0 = 失败。"""
    for i in range(tries):
        if focus(hwnd):
            return i + 1
        time.sleep(0.15)
    return 0


def ensure_focus(substr, tries=8):
    """按标题找窗口并抢前台，成功返回 hwnd，失败返回 0。"""
    hits = find(substr)
    if not hits:
        return 0
    h = hits[0][0]
    return h if focus_verified(h, tries) else 0


def wait_window(substr, timeout=25.0, include_hidden=True):
    """等窗口出现（启动客户端后用它代替裸 sleep）。"""
    deadline = time.time() + timeout
    while time.time() < deadline:
        hits = find(substr, include_hidden)
        if hits:
            return hits[0][0]
        time.sleep(0.4)
    return 0


def title_under_point(x, y):
    """点 (x,y) 处最上层窗口的顶层标题——判断这一下会点到谁，比看前台准。"""
    h = user32.WindowFromPoint(wintypes.POINT(int(x), int(y)))
    if not h:
        return "", 0
    root = user32.GetAncestor(h, GA_ROOT) or h
    return title_of(root), root


def point_is_on(x, y, substr):
    t, h = title_under_point(x, y)
    return (substr in t), t, h
