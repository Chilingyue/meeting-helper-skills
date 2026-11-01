"""按键 / 组合键。

用法：
    python key.py enter
    python key.py ctrl a          # 全选
    python key.py ctrl v          # 粘贴
    python key.py alt v           # 例：腾讯会议 开/关视频
    python key.py alt m           # 例：腾讯会议 静音/解除静音
    python key.py ctrl shift s

支持：单字母 a-z、数字 0-9，以及 enter/esc/tab/space/back/delete/up/down/left/right/home/end。
修饰键：ctrl / shift / alt。
"""
import ctypes
import sys
import time

user32 = ctypes.windll.user32
KEYEVENTF_KEYUP = 0x0002
VK_CONTROL, VK_SHIFT, VK_MENU = 0x11, 0x10, 0x12

SPECIAL = {
    "enter": 0x0D, "esc": 0x1B, "escape": 0x1B, "tab": 0x09, "space": 0x20,
    "back": 0x08, "backspace": 0x08, "delete": 0x2E, "del": 0x2E,
    "up": 0x26, "down": 0x28, "left": 0x25, "right": 0x27,
    "home": 0x24, "end": 0x23, "pageup": 0x21, "pagedown": 0x22,
}
MODS = {"ctrl": VK_CONTROL, "control": VK_CONTROL, "shift": VK_SHIFT, "alt": VK_MENU}


def _vk(name):
    if name in SPECIAL:
        return SPECIAL[name]
    if len(name) == 1 and name.isalnum():
        return ord(name.upper())
    return None


def tap(vk, mods=()):
    for m in mods:
        user32.keybd_event(m, 0, 0, 0)
        time.sleep(0.04)
    user32.keybd_event(vk, 0, 0, 0)
    time.sleep(0.05)
    user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)
    for m in reversed(mods):
        time.sleep(0.04)
        user32.keybd_event(m, 0, KEYEVENTF_KEYUP, 0)


if __name__ == "__main__":
    names = [a.lower() for a in sys.argv[1:]]
    if not names:
        print(__doc__)
        sys.exit(1)

    mods, key = [], None
    for n in names:
        if n in MODS:
            mods.append(MODS[n])
        else:
            vk = _vk(n)
            if vk is None:
                print("unknown key:", n)
                sys.exit(1)
            key = vk
    if key is None:
        print("需要一个主键，例如: python key.py ctrl a")
        sys.exit(1)

    tap(key, mods)
    print("key", "+".join(names))
