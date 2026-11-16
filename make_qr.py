# -*- coding: utf-8 -*-
"""只出二维码：单张 码_<名字>.png，以及一张 10 格的总表 二维码集.png。

    python make_qr.py 王曜军 邓涛 ...
"""

import sys, zlib
from PIL import Image, ImageDraw, ImageFont
import qr

BASE = "https://cdn.jsdelivr.net/gh/wyj247/shanshuikard-card@main/docs/img/%s.jpg"
PAPER = (245, 239, 226)
INK = (43, 47, 48)
RED = (176, 58, 46)
FONT = "C:\\Windows\\Fonts\\simkai.ttf"


def pid(name):
    return "%08x" % (zlib.crc32(name.encode("utf-8")) & 0xffffffff)


def qr_only(payload, scale=10, border=4):
    info = qr.build(payload, "Q")
    m = info["matrix"]
    n = len(m)
    dot = Image.new("L", (n, n), 255)
    px = dot.load()
    for i in range(n):
        for j in range(n):
            if m[i][j]:
                px[j, i] = 0
    full = Image.new("L", ((n + 2 * border) * scale, (n + 2 * border) * scale), 255)
    full.paste(dot.resize((n * scale, n * scale), Image.NEAREST),
               (border * scale, border * scale))
    return full.convert("RGB"), info


def sheet(names, out="二维码集.png", cell=320, qsize=236):
    cols = 5
    rows = (len(names) + cols - 1) // cols
    W, H = cols * cell, rows * (cell + 40) + 60
    im = Image.new("RGB", (W, H), PAPER)
    dr = ImageDraw.Draw(im)
    f_title = ImageFont.truetype(FONT, 30)
    f_name = ImageFont.truetype(FONT, 26)
    dr.text((30, 16), "扫 码 见 山", font=f_title, fill=INK)
    for i, name in enumerate(names):
        c, r = i % cols, i // cols
        x0, y0 = c * cell, 60 + r * (cell + 40)
        q, _ = qr_only(BASE % pid(name), scale=4, border=4)
        q = q.resize((qsize, qsize), Image.LANCZOS)
        im.paste(q, (x0 + (cell - qsize) // 2, y0))
        tw = dr.textlength(name, font=f_name)
        dr.text((x0 + (cell - tw) / 2, y0 + qsize + 10), name, font=f_name, fill=INK)
    im.save(out, "PNG")
    return out, im.size


if __name__ == "__main__":
    names = sys.argv[1:]
    for n in names:
        im, info = qr_only(BASE % pid(n), scale=12)
        p = "码_%s.png" % n
        im.save(p, "PNG")
        print("%s -> %s  v%d %d模块 %s" % (n, p, info["version"], info["size"], BASE % pid(n)))
    print(sheet(names))
