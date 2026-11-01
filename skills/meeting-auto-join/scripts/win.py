"""找窗口 / 置前 / 列出所有窗口。

用法：
    python win.py 微信              # 列出匹配项，并把第一个置前
    python win.py 微信 --list       # 只列不置前
    python win.py "" --list         # 列出所有有标题的窗口（找不到目标时排查用）
    python win.py 微信 --wait 15    # 最多等 15 秒，等窗口出现（启动客户端后用）
"""
import sys

import winutil

if __name__ == "__main__":
    argv = sys.argv[1:]
    sub = ""
    flags = set()
    wait = 0.0
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--wait":
            wait = float(argv[i + 1])
            i += 2
            continue
        if a.startswith("--"):
            flags.add(a)
        elif not sub:
            sub = a
        i += 1

    if wait:
        hwnd = winutil.wait_window(sub, timeout=wait)
        if not hwnd:
            print("等了 %.0f 秒，标题含 %r 的窗口仍未出现" % (wait, sub))
            sys.exit(2)
        print("window appeared:", hwnd)

    hits = winutil.find(sub)
    if not hits:
        print("no window matched:", repr(sub))
        print("--- 当前可见窗口（标题, 位置尺寸）---")
        for h, t, vis, r in winutil.list_titled():
            if vis and r[2] > 80:
                print("  hwnd", h, repr(t), r)
        sys.exit(2)

    for h, t, vis, r in hits:
        print("hwnd", h, "title", repr(t), "visible" if vis else "hidden", "rect", r,
              "size %dx%d" % (r[2], r[3]))
    print("dpi scale", winutil.dpi_scale())

    if "--list" in flags:
        sys.exit(0)

    tries = winutil.focus_verified(hits[0][0])
    if not tries:
        print("focus FAILED: 前台仍是", repr(winutil.foreground_title()))
        sys.exit(4)
    print("focused after %d try(s); foreground =" % tries, repr(winutil.foreground_title()))
