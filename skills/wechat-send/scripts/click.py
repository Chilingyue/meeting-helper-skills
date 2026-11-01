"""鼠标点击（坐标 = 截图上的坐标 + origin）。

用法：
    python click.py 1185 74
    python click.py 1185 74 --double
    python click.py 1185 74 --title 微信        # 推荐：先做命中测试，点到别的窗口就拒绝

--title 会先问 Windows "这个点最上层是谁"（WindowFromPoint），不是目标窗口就尝试把它
抢到前台再问一次，仍然不对就 exit 3 什么都不点。挡的是真事故：被别的窗口盖住时，
裸点击会点穿到上层窗口，配合粘贴会把内容写进别的程序。
"""
import ctypes
import sys
import time

import winutil

user32 = ctypes.windll.user32
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004


def click(x, y, double=False, delay=0.12):
    user32.SetCursorPos(int(x), int(y))
    time.sleep(delay)
    for _ in range(2 if double else 1):
        user32.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        time.sleep(0.06)
        user32.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
        if double:
            time.sleep(0.08)
    print("clicked", int(x), int(y))


if __name__ == "__main__":
    argv = sys.argv[1:]
    must = None
    nums = []
    i = 0
    while i < len(argv):
        if argv[i] == "--title":
            must = argv[i + 1] if i + 1 < len(argv) else ""
            i += 2
            continue
        if not argv[i].startswith("--"):
            nums.append(argv[i])
        i += 1

    if len(nums) < 2:
        print("usage: python click.py x y [--double] [--title 窗口标题片段]")
        sys.exit(1)

    x, y = int(nums[0]), int(nums[1])

    if must:
        ok, under, _h = winutil.point_is_on(x, y, must)
        if not ok:
            if winutil.ensure_focus(must):
                time.sleep(0.3)
                ok, under, _h = winutil.point_is_on(x, y, must)
        if not ok:
            print("abort: 该点最上层窗口是 %r，不匹配 %r，未点击" % (under, must))
            sys.exit(3)

    click(x, y, "--double" in argv)
