"""像素级差异对比：判断"点完之后某个小区域有没有变化"，比肉眼看图更确定。

用法：
    python diff.py before.png after.png
    python diff.py shot.png --rect1 820 940 150 90 --rect2 430 940 150 90   # 同图两块比

判读（经验值）：
    changed_pixels < 1%   基本没变化 → 多半是没点中
    changed_pixels > 5%   确实变了 → 状态已切换
"""
import sys

import pngio


def load(path, rect=None):
    w, h, rgb = pngio.read_png(path)
    if rect:
        return pngio.crop_rgb(w, h, rgb, *rect)
    return w, h, rgb


def compare(wa, ha, a, wb, hb, b):
    if (wa, ha) != (wb, hb):                     # 尺寸不同就按左上角对齐取交集
        w, h = min(wa, wb), min(ha, hb)
        a = pngio.crop_rgb(wa, ha, a, 0, 0, w, h)[2]
        b = pngio.crop_rgb(wb, hb, b, 0, 0, w, h)[2]
        wa, ha = w, h

    changed = 0
    total = wa * ha
    sum_a = sum_b = 0
    for i in range(0, total * 3, 3):
        d = abs(a[i] - b[i]) + abs(a[i + 1] - b[i + 1]) + abs(a[i + 2] - b[i + 2])
        sum_a += a[i] + a[i + 1] + a[i + 2]
        sum_b += b[i] + b[i + 1] + b[i + 2]
        if d > 30:
            changed += 1
    pct = 100.0 * changed / max(1, total)
    print("size %dx%d  changed_pixels %.2f%%" % (wa, ha, pct))
    print("mean rgb A %.0f  B %.0f" % (sum_a / 3.0 / max(1, total), sum_b / 3.0 / max(1, total)))
    return pct


if __name__ == "__main__":
    argv = sys.argv[1:]
    rects, pos = {}, []
    i = 0
    while i < len(argv):
        if argv[i] in ("--rect1", "--rect2"):
            rects[argv[i]] = [int(v) for v in argv[i + 1:i + 5]]
            i += 5
            continue
        pos.append(argv[i])
        i += 1

    if len(rects) == 2:
        compare(*load(pos[0], rects["--rect1"]), *load(pos[0], rects["--rect2"]))
    elif len(pos) >= 2:
        compare(*load(pos[0]), *load(pos[1]))
    else:
        print(__doc__)
        sys.exit(1)
