# -*- coding: utf-8 -*-
"""山水名片：一幅山 + 右下角二维码。扫码回到站点，看这个名字的那座山。"""

import sys, os, zlib, tempfile
from urllib.parse import quote
from PIL import Image, ImageDraw, ImageFilter
import shanshui
import qr

# 没有站点时，二维码写离线串；传 url 时换成真链接（{q} 是 URL 编码后的名字）。
TOKEN = "SHANSHUI/{name}/{seed}"


def card(name, out, seed=None, url=None, ecc="Q", quiet=4):
    if seed is None:
        seed = zlib.crc32(name.encode("utf-8")) % 100000

    fd, tmp = tempfile.mkstemp(suffix=".png")
    os.close(fd)
    try:
        shanshui.render(name, tmp, seed)
        im = Image.open(tmp).convert("RGB")
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)

    W, H = im.size
    short = min(W, H)

    payload = url.format(q=quote(name)) if url else TOKEN.format(name=name, seed=seed)
    info = qr.build(payload, ecc)
    n = info["size"]
    border = quiet                      # 静区至少 4 模块
    cells = n + 2 * border
    mod = max(2, int(short * 0.300) // cells)   # 让二维码占短边的约 30%
    qrs = cells * mod

    fs = max(12, int(short * 0.017))
    padx = int(short * 0.022)
    pady = int(short * 0.016)
    cap_h = fs + int(short * 0.022)
    panel_w = qrs + 2 * padx
    panel_h = pady + qrs + cap_h
    margin = int(short * 0.038)

    px0 = W - margin - panel_w
    py0 = H - margin - panel_h
    qx = px0 + padx                     # 二维码（含静区）左上角
    qy = py0 + pady

    # 投影
    sh = Image.new("L", (W, H), 0)
    ImageDraw.Draw(sh).rounded_rectangle(
        [px0 + 6, py0 + 10, px0 + panel_w + 6, py0 + panel_h + 10],
        radius=int(short * 0.012), fill=110)
    sh = sh.filter(ImageFilter.GaussianBlur(short * 0.012))
    im = Image.composite(Image.new("RGB", (W, H), (26, 24, 22)), im,
                         sh.point(lambda v: int(v * 0.55)))

    dr = ImageDraw.Draw(im, "RGBA")
    dr.rounded_rectangle([px0, py0, px0 + panel_w, py0 + panel_h],
                         radius=int(short * 0.012), fill=(248, 244, 234, 250),
                         outline=(126, 114, 92, 90), width=max(1, int(short * 0.0015)))

    # 二维码本体：逐行合并连续黑块，画成矩形
    m = info["matrix"]
    ink = (24, 27, 28)
    for i in range(n):
        row = m[i]
        j = 0
        while j < n:
            if row[j]:
                k = j
                while k < n and row[k]:
                    k += 1
                x1 = qx + (border + j) * mod
                y1 = qy + (border + i) * mod
                dr.rectangle([x1, y1, x1 + (k - j) * mod - 1, y1 + mod - 1], fill=ink)
                j = k
            else:
                j += 1

    # 说明文字放在二维码下方，绝不压在静区上
    dr.text((px0 + panel_w / 2, py0 + pady + qrs + cap_h * 0.42), "扫 码 见 山",
            font=shanshui.load_font(fs), fill=(82, 72, 56, 215), anchor="mm")

    im.save(out)
    return {"out": out, "seed": seed, "version": info["version"], "ecc": ecc,
            "size": im.size, "payload": payload, "modules": n, "module_px": mod,
            "quiet": border, "qr_box": [qx, qy, qrs]}


if __name__ == "__main__":
    name = sys.argv[1] if len(sys.argv) > 1 else "林清和"
    out = sys.argv[2] if len(sys.argv) > 2 else "card.png"
    seed = int(sys.argv[3]) if len(sys.argv) > 3 else None
    url = sys.argv[4] if len(sys.argv) > 4 else None
    print(card(name, out, seed, url))
