"""纯标准库的 PNG 读写 / 裁剪 / 缩放。

只用 zlib + struct，不依赖 Pillow、numpy、opencv。
这样别人拿到这套脚本，只要有 Python 3.8+ 就能跑，不需要 pip install 任何东西。

对外接口：
    write_png(path, w, h, rgb_bytes)          rgb_bytes: w*h*3，RGB 顺序
    read_png(path) -> (w, h, rgb_bytes)
    crop_rgb(w, h, rgb, x, y, cw, ch) -> (cw, ch, rgb)
    scale_rgb(w, h, rgb, factor)      -> (w*factor, h*factor, rgb)  最近邻整数放大
    mean_and_range(w, h, rgb)         -> (mean, min, max, distinct)  用来判断是不是截到空白
"""
import struct
import zlib

PNG_SIG = b"\x89PNG\r\n\x1a\n"
CHANNELS = {0: 1, 2: 3, 4: 2, 6: 4}


def write_png(path, width, height, rgb, level=6):
    """写 8bit RGB PNG。逐行 filter=0（最快），zlib 压缩。"""
    width = int(width)
    height = int(height)
    stride = width * 3
    if len(rgb) != stride * height:
        raise ValueError("rgb size mismatch: got %d, want %d" % (len(rgb), stride * height))

    raw = bytearray()
    for y in range(height):
        raw.append(0)                                   # filter type 0
        raw += rgb[y * stride:(y + 1) * stride]

    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data +
                struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    with open(path, "wb") as f:
        f.write(PNG_SIG)
        f.write(chunk(b"IHDR", ihdr))
        f.write(chunk(b"IDAT", zlib.compress(bytes(raw), level)))
        f.write(chunk(b"IEND", b""))


def _unfilter(raw, width, height, ch):
    stride = width * ch
    out = bytearray(stride * height)
    prev = bytearray(stride)
    p = 0
    for y in range(height):
        ft = raw[p]
        p += 1
        line = bytearray(raw[p:p + stride])
        p += stride
        if ft == 1:
            for i in range(ch, stride):
                line[i] = (line[i] + line[i - ch]) & 0xFF
        elif ft == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 0xFF
        elif ft == 3:
            for i in range(stride):
                a = line[i - ch] if i >= ch else 0
                line[i] = (line[i] + ((a + prev[i]) >> 1)) & 0xFF
        elif ft == 4:
            for i in range(stride):
                a = line[i - ch] if i >= ch else 0
                b = prev[i]
                c = prev[i - ch] if i >= ch else 0
                pa = abs(b - c)
                pb = abs(a - c)
                pc = abs(a + b - 2 * c)
                if pa <= pb and pa <= pc:
                    pr = a
                elif pb <= pc:
                    pr = b
                else:
                    pr = c
                line[i] = (line[i] + pr) & 0xFF
        elif ft != 0:
            raise ValueError("bad filter type %d" % ft)
        out[y * stride:(y + 1) * stride] = line
        prev = line
    return out


def read_png(path):
    """读 8bit 非隔行 PNG（灰度 / 灰度+alpha / RGB / RGBA），统一转成 RGB。"""
    with open(path, "rb") as f:
        data = f.read()
    if not data.startswith(PNG_SIG):
        raise ValueError("not a PNG: %s（本工具只认 PNG，BMP 请先用截图脚本重截）" % path)

    pos = len(PNG_SIG)
    idat = bytearray()
    w = h = bitdepth = colortype = interlace = 0
    palette = b""
    while pos + 8 <= len(data):
        length = struct.unpack(">I", data[pos:pos + 4])[0]
        tag = data[pos + 4:pos + 8]
        body = data[pos + 8:pos + 8 + length]
        pos += 12 + length
        if tag == b"IHDR":
            w, h, bitdepth, colortype, _comp, _filt, interlace = struct.unpack(">IIBBBBB", body)
        elif tag == b"IDAT":
            idat += body
        elif tag == b"PLTE":
            palette = body
        elif tag == b"IEND":
            break

    if bitdepth != 8:
        raise ValueError("只支持 8bit PNG，当前 %dbit" % bitdepth)
    if interlace != 0:
        raise ValueError("不支持隔行 PNG，请用 --scale 或其它工具重新导出")
    if colortype == 3:
        raise ValueError("不支持调色板 PNG，请另存为 RGB")

    ch = CHANNELS[colortype]
    pix = _unfilter(zlib.decompress(bytes(idat)), w, h, ch)

    if colortype == 2:
        return w, h, bytes(pix)
    stride = w * ch
    out = bytearray(w * h * 3)
    if colortype == 0:                      # 灰度
        out[0::3] = pix[0::1]
        out[1::3] = pix[0::1]
        out[2::3] = pix[0::1]
    elif colortype == 4:                    # 灰度 + A
        for i in range(w * h):
            g = pix[i * 2]
            out[i * 3] = g
            out[i * 3 + 1] = g
            out[i * 3 + 2] = g
    elif colortype == 6:                    # RGBA
        for c in range(3):
            out[c::3] = pix[c::4]
    return w, h, bytes(out)


def crop_rgb(w, h, rgb, x, y, cw, ch):
    x = max(0, min(int(x), w - 1))
    y = max(0, min(int(y), h - 1))
    cw = max(1, min(int(cw), w - x))
    ch = max(1, min(int(ch), h - y))
    out = bytearray(cw * ch * 3)
    sstride = w * 3
    dstride = cw * 3
    for row in range(ch):
        s = (y + row) * sstride + x * 3
        out[row * dstride:(row + 1) * dstride] = rgb[s:s + dstride]
    return cw, ch, bytes(out)


def scale_rgb(w, h, rgb, factor):
    factor = int(factor)
    if factor <= 1:
        return w, h, rgb
    nw, nh = w * factor, h * factor
    out = bytearray(nw * nh * 3)
    sstride = w * 3
    dstride = nw * 3
    # 先把每行按整数倍横向展开，再纵向复制 factor 次
    rows = []
    for y in range(h):
        line = rgb[y * sstride:(y + 1) * sstride]
        wide = bytearray(dstride)
        for x in range(w):
            px = line[x * 3:x * 3 + 3]
            wide[x * factor * 3:(x + 1) * factor * 3] = px * factor
        rows.append(bytes(wide))
    for y in range(h):
        for k in range(factor):
            out[(y * factor + k) * dstride:(y * factor + k + 1) * dstride] = rows[y]
    return nw, nh, bytes(out)


def stats(w, h, rgb, step=7):
    """抽样统计亮度均值 / 极差 / 不同颜色数，用来判断截图是不是一片空白。"""
    total = 0
    n = 0
    lo, hi = 255, 0
    seen = set()
    for i in range(0, w * h, step):
        r = rgb[i * 3]
        g = rgb[i * 3 + 1]
        b = rgb[i * 3 + 2]
        v = (r + g + b) // 3
        total += v
        n += 1
        lo = min(lo, v)
        hi = max(hi, v)
        if len(seen) < 3000:
            seen.add((r, g, b))
    return (total / n if n else 0), lo, hi, len(seen)
