"""从 PNG 截图里裁一块（可选整数倍放大），用于看小字、看图标状态、做 CV 模板。

用法：
    python crop.py shot.png 820 940 150 90 out.png      # 裁 (820,940) 起 150x90
    python crop.py shot.png 820 940 150 90 out.png 3    # 再放大 3 倍

x/y 都是**截图内坐标**；脚本会打印 origin，所以换算公式始终是：
    屏幕坐标 = origin + 截图内坐标
"""
import sys

import pngio

if __name__ == "__main__":
    argv = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(argv) < 6:
        print(__doc__)
        sys.exit(1)

    src, x, y, w, h, out = argv[0], int(argv[1]), int(argv[2]), int(argv[3]), int(argv[4]), argv[5]
    scale = int(argv[6]) if len(argv) > 6 else 1

    W, H, rgb = pngio.read_png(src)
    cw, ch, piece = pngio.crop_rgb(W, H, rgb, x, y, w, h)
    if scale != 1:
        cw, ch, piece = pngio.scale_rgb(cw, ch, piece, scale)
    pngio.write_png(out, cw, ch, piece)
    print("cropped", out, "%dx%d" % (cw, ch), "from", src, "src %dx%d at" % (W, H), x, y,
          "| scale", scale)
