# -*- coding: utf-8 -*-
"""把名字生成的山导出成 docs/img/<id>.jpg —— 手机上直接打开就是一张图。

    python gen_img.py 王曜军 邓涛 刘宇

为什么要这个：GitHub Pages 只能在网页后台点开，而 CDN（jsDelivr）能直接读仓库里的
文件、并且对图片给的是 image/jpeg，手机浏览器会当图片显示，不会显示成源码。
"""

import sys, os, zlib
import shanshui
from PIL import Image


def page_id(name):
    return "%08x" % (zlib.crc32(name.encode("utf-8")) & 0xffffffff)


def make(name, outdir="docs/img", maxw=1280, quality=84):
    os.makedirs(outdir, exist_ok=True)
    seed = zlib.crc32(name.encode("utf-8")) % 100000
    tmp = os.path.join(outdir, "_tmp.png")
    shanshui.render(name, tmp, seed)
    im = Image.open(tmp).convert("RGB")
    os.remove(tmp)
    w, h = im.size
    if max(w, h) > maxw:
        s = maxw / float(max(w, h))
        im = im.resize((int(w * s), int(h * s)), Image.LANCZOS)
    out = os.path.join(outdir, page_id(name) + ".jpg")
    im.save(out, "JPEG", quality=quality, optimize=True)
    return out


if __name__ == "__main__":
    for n in sys.argv[1:]:
        p = make(n)
        print("%s -> %s (%d KB)" % (n, p, os.path.getsize(p) // 1024))
