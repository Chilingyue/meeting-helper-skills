"""键盘逐字输入（ASCII），或整段文字（--unicode，可含中文）。

两种模式：
    默认       按虚拟键逐字敲，只认 0-9 和 a-z；受输入法影响，输入法在中文态时
               字母会被当成拼音（会弹出候选条，还可能遮住按钮）
    --unicode  用 KEYEVENTF_UNICODE 直接注入字符编码，绕过输入法，中文/标点都能过

用法：
    python type.py 123456789
    python type.py abc-123 0.02
    python type.py "今晚七点开会" --unicode

注意：--unicode 走 SendInput 注入，个别程序（尤其是自绘控件的聊天输入框）可能
只认剪贴板粘贴；遇到不生效就改用 paste.py。
"""
import ctypes
import sys
import time

user32 = ctypes.windll.user32
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004
VK_OEM_MINUS = 0xBD
VK_OEM_PERIOD = 0xBE


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", ctypes.c_ushort), ("wScan", ctypes.c_ushort),
                ("dwFlags", ctypes.c_ulong), ("time", ctypes.c_ulong),
                ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]


class _INPUTunion(ctypes.Union):
    # 联合体必须按 64 位下最大的成员（MOUSEINPUT，32 字节）预留，否则 sizeof(INPUT)
    # 不等于 40，SendInput 会直接失败且不报错——踩过一次，表现为"什么都没输入"。
    _fields_ = [("ki", KEYBDINPUT), ("padding", ctypes.c_ubyte * 32)]


class INPUT(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong), ("u", _INPUTunion)]


def type_ascii(text, delay=0.05):
    for ch in text:
        c = ch.lower()
        if c == "-":
            vk = VK_OEM_MINUS
        elif c == ".":
            vk = VK_OEM_PERIOD
        elif c.isdigit() or ("a" <= c <= "z"):
            vk = ord(c.upper())
        else:
            continue                      # 非法字符直接跳过（中文请用 --unicode / paste.py）
        user32.keybd_event(vk, 0, 0, 0)
        time.sleep(0.02)
        user32.keybd_event(vk, 0, KEYEVENTF_KEYUP, 0)
        time.sleep(delay)


def type_unicode(text, delay=0.02):
    units = []
    for ch in text:
        code = ord(ch)
        if code > 0xFFFF:                 # 基本多文种平面之外的字符要拆成代理对
            code -= 0x10000
            units.append(0xD800 + (code >> 10))
            units.append(0xDC00 + (code & 0x3FF))
        else:
            units.append(code)
    for u in units:
        down = INPUT(type=1)
        down.u.ki = KEYBDINPUT(0, u, KEYEVENTF_UNICODE, 0, None)
        up = INPUT(type=1)
        up.u.ki = KEYBDINPUT(0, u, KEYEVENTF_UNICODE | KEYEVENTF_KEYUP, 0, None)
        user32.SendInput(1, ctypes.byref(down), ctypes.sizeof(INPUT))
        user32.SendInput(1, ctypes.byref(up), ctypes.sizeof(INPUT))
        time.sleep(delay)


if __name__ == "__main__":
    argv = sys.argv[1:]
    if not argv:
        print(__doc__)
        sys.exit(1)
    if argv[0] == "--unicode":
        text = argv[1] if len(argv) > 1 else ""
        type_unicode(text)
    else:
        text = argv[0]
        delay = float(argv[1]) if len(argv) > 1 else 0.05
        type_ascii(text, delay)
    print("typed", repr(text))
