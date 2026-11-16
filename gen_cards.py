# -*- coding: utf-8 -*-
"""批量出名片：二维码指向 CDN 上那张图，并当场做扫码自检。

    python gen_cards.py 王曜军 邓涛 ...
"""

import sys, zlib
import card as cardmod
import verify_scan as vs

BASE = "https://cdn.jsdelivr.net/gh/wyj247/shanshuikard-card@main/docs/img/%s.jpg"


def page_id(name):
    return "%08x" % (zlib.crc32(name.encode("utf-8")) & 0xffffffff)


def build(name, outdir=""):
    url = BASE % page_id(name)
    out = (outdir + "卡_" + name + ".png") if outdir else ("卡_" + name + ".png")
    info = cardmod.card(name, out, url=url)
    box, n, mod, border = info["qr_box"], info["modules"], info["module_px"], info["quiet"]
    res = []
    for scale in (0.45, 0.55, 0.70):
        im = vs.shoot(out, box, scale=scale)
        m = vs.sample(im, n, border, mod)
        res.append("PASS" if vs.read_back(m, n, want=url) else "FAIL")
    return {"name": name, "out": out, "url": url, "version": info["version"],
            "modules": n, "module_px": mod, "quiet": border,
            "tests": res, "quiet_worst": vs.quiet_ok(out, box, border, mod)}


if __name__ == "__main__":
    for name in sys.argv[1:]:
        r = build(name)
        print("%-8s v%-2d %2d模块 %dpx %s 静区最暗=%s" % (
            r["name"], r["version"], r["modules"], r["module_px"],
            " ".join(r["tests"]), r["quiet_worst"]))
