"""用模板匹配精确定位界面元素（可选增强，需要 opencv + numpy）。

没装 opencv 时本脚本会明确提示缺失；截图、裁剪、点击等主流程都不依赖它。

为什么要它：靠人眼在图上看坐标会有几像素误差，模板匹配给的是像素级中心，
还能顺带告诉你"匹配了 0.99 分，确实就是这个按钮"，而不是猜。

用法：
    # 1) 先截窗口图
    python grab.py 微信 shot.png
    # 2) 从图里裁一个模板（换成你要点的东西）
    python crop.py shot.png 872 972 62 30 tpl/send.png
    # 3) 在新截图里找它
    python cvfind.py --shot 微信 tpl/send.png
    python cvfind.py --shot 微信 tpl/send.png --click --title 微信
    python cvfind.py --shot 微信 tpl/send.png --dump marked.png   # 画框，肉眼复核

常用参数：
    --thr 0.85        相似度阈值（TM_CCOEFF_NORMED，1.0 完全一致）
    --top 3           输出前几个不同位置的匹配（内部做 NMS 去重）
    --scales 1,0.9,1.1  多尺度（窗口被缩放/换 DPI 时用，慢几倍）
    --click           点第一个匹配的中心
    --title 微信      配合 --click：点击前做命中测试
"""
import sys

try:
    import numpy as np
    import cv2
except ImportError as e:
    print("缺少依赖：", e)
    print("本脚本需要 opencv + numpy，安装：pip install opencv-python-headless numpy")
    print("不装也能用整套流程——截图/裁剪/点击都不依赖它，只是坐标要自己从图上量。")
    sys.exit(5)

import pngio
import winutil


def load_bgr(path):
    w, h, rgb = pngio.read_png(path)
    arr = np.frombuffer(rgb, dtype=np.uint8).reshape(h, w, 3)
    return np.ascontiguousarray(arr[:, :, ::-1])          # RGB → BGR


def shoot(target=None, path=None, raise_window=True):
    """返回 (BGR 图, origin)。target=None 时从已有 PNG 读（origin 需自己给）。"""
    if path:
        return load_bgr(path), (0, 0)
    import grab
    w, h, rgb, origin, info = grab.capture(target, raise_window=raise_window)
    if w is None:
        return None, None
    print("window:", info["hwnd"], repr(info["title"]), "rect", info["rect"],
          "origin", origin, "| method", info["method"])
    arr = np.frombuffer(rgb, dtype=np.uint8).reshape(h, w, 3)
    return np.ascontiguousarray(arr[:, :, ::-1]), origin


def match(shot, tpl, thr, scales):
    best = []
    sh, sw = shot.shape[:2]
    for sc in scales:
        t = tpl if sc == 1.0 else cv2.resize(
            tpl, (max(1, int(tpl.shape[1] * sc)), max(1, int(tpl.shape[0] * sc))),
            interpolation=cv2.INTER_AREA)
        th, tw = t.shape[:2]
        if th > sh or tw > sw:
            continue
        res = cv2.matchTemplate(shot, t, cv2.TM_CCOEFF_NORMED)
        ys, xs = np.where(res >= thr)
        for y, x in zip(ys, xs):
            best.append((float(res[y, x]), int(x), int(y), tw, th))

    best.sort(key=lambda r: -r[0])
    kept = []
    for score, x, y, w, h in best:                       # NMS：中心太近的视为同一个
        cx, cy = x + w // 2, y + h // 2
        if all(abs(cx - (kx + kw // 2)) > max(kw, kh) // 2 or
               abs(cy - (ky + kh // 2)) > max(kw, kh) // 2
               for _, kx, ky, kw, kh in kept):
            kept.append((score, x, y, w, h))
    return kept


if __name__ == "__main__":
    argv = sys.argv[1:]
    flags, opts, pos = set(), {}, []
    takes = {"--origin": 2, "--scales": 1, "--thr": 1, "--top": 1,
             "--title": 1, "--dump": 1, "--shot": 1}
    i = 0
    while i < len(argv):
        a = argv[i]
        if a in takes:
            n = takes[a]
            opts[a] = argv[i + 1:i + 1 + n]
            i += 1 + n
            continue
        if a.startswith("--"):
            flags.add(a)
        else:
            pos.append(a)
        i += 1

    thr = float(opts.get("--thr", ["0.85"])[0])
    top = int(opts.get("--top", ["3"])[0])
    scales = [float(s) for s in opts.get("--scales", ["1"])[0].split(",")]

    if "--shot" in opts:
        shot, origin = shoot(target=opts["--shot"][0])
        if shot is None:
            print("no window matched:", opts["--shot"][0])
            sys.exit(2)
    else:
        shot, _ = shoot(path=pos.pop(0))
        o = opts.get("--origin", ["0", "0"])
        origin = (int(o[0]), int(o[1]))

    tpl = load_bgr(pos[0])
    hits = match(shot, tpl, thr, scales)[:top]
    if not hits:
        print("没有超过阈值 %.2f 的匹配（换个模板，或降低 --thr）" % thr)
        sys.exit(1)

    for score, x, y, w, h in hits:
        print("score %.3f  center(%d,%d)  screen(%d,%d)  box %dx%d"
              % (score, x + w // 2, y + h // 2,
                 origin[0] + x + w // 2, origin[1] + y + h // 2, w, h))
    if len(hits) > 1:
        print("注意：有 %d 个候选，按 screen 坐标挑想点的那个，别直接点第一个" % len(hits))

    if "--dump" in opts:
        vis = shot.copy()
        for score, x, y, w, h in hits:
            cv2.rectangle(vis, (x, y), (x + w, y + h), (0, 0, 255), 2)
            cv2.putText(vis, "%.2f" % score, (x, max(12, y - 4)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.45, (255, 0, 0), 1)
        cv2.imwrite(opts["--dump"][0], vis)
        print("dumped", opts["--dump"][0])

    if "--click" in flags:
        _, x, y, w, h = hits[0]
        sx, sy = origin[0] + x + w // 2, origin[1] + y + h // 2
        must = opts.get("--title", [None])[0]
        if must:
            ok, under, _ = winutil.point_is_on(sx, sy, must)
            if not ok:
                print("abort click: 该点最上层是", repr(under))
                sys.exit(3)
        import click as _click
        _click.click(sx, sy)
