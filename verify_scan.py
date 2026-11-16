# -*- coding: utf-8 -*-
"""扫码自检：把名片上印出来的二维码当成一张照片去读。

流程：裁下二维码 -> 降采样 + 高斯模糊 + JPEG 压缩（模拟手机远距离拍照）->
按模块中心取像素重建矩阵 -> 按 RS 校验挑出正确的 (纠错级, 掩码) -> 比对载荷。
不借助任何二维码识别库，能读回来靠的是 qr.py 的 Reed-Solomon 校验。
"""

import os, io, sys, tempfile
from PIL import Image, ImageFilter
import shanshui, card, qr

ECCS = ("L", "M", "Q", "H")


def shoot(path, box, scale=0.55, blur=0.7, jpeg=55):
    im = Image.open(path).convert("L")
    qx, qy, qrs = box
    crop = im.crop((qx, qy, qx + qrs, qy + qrs))
    w = max(1, int(qrs * scale))
    small = crop.resize((w, w), Image.LANCZOS)
    small = small.filter(ImageFilter.GaussianBlur(blur))
    buf = io.BytesIO()
    small.save(buf, "JPEG", quality=jpeg)
    buf.seek(0)
    return Image.open(buf).convert("L").resize((qrs, qrs), Image.BILINEAR)


def sample(im, n, border, mod, jx=0.0, jy=0.0):
    m = []
    for i in range(n):
        row = []
        for j in range(n):
            cx = int((border + j + 0.5 + jx) * mod)
            cy = int((border + i + 0.5 + jy) * mod)
            cx = max(0, min(im.width - 1, cx))
            cy = max(0, min(im.height - 1, cy))
            row.append(im.getpixel((cx, cy)) < 128)
        m.append(row)
    return m


def read_back(m, n, ecc_hint=None, want=None):
    """按 (纠错级, 掩码) 逐个试。注意：RS 只查前 ecw 个根，
    高纠错级的合法码字在低纠错级下可能「前缀根全零」而误通过，
    所以真正的判据是解出来的载荷对不对，这里要求严格 UTF-8 且（给了 want 时）完全一致。"""
    version = (n - 17) // 4
    fallback = None
    for ecc in ((ecc_hint,) if ecc_hint else ECCS):
        for mk in range(8):
            try:
                d = qr.decode({"matrix": m, "size": n, "version": version,
                               "ecc": ecc, "mask": mk})
            except Exception:
                continue
            if not d["ok_rs"]:
                continue
            text = d["text"]
            if "\ufffd" in text:
                continue
            if want is not None and text == want:
                return ecc, mk, text
            if fallback is None:
                fallback = (ecc, mk, text)
    return fallback


def quiet_ok(path, box, border, mod):
    """静区最外一圈必须干净：取四条 1 模块宽的边带，看最暗点是否足够浅。"""
    im = Image.open(path).convert("L")
    qx, qy, qrs = box
    band = max(1, mod // 2)
    worst = 255
    for i in range(0, qrs, 3):
        for (x, y) in ((qx + i, qy + band), (qx + i, qy + qrs - band),
                       (qx + band, qy + i), (qx + qrs - band, qy + i)):
            worst = min(worst, im.getpixel((min(x, im.width - 1), min(y, im.height - 1))))
    return worst


def run(names, url="http://demo.local/?n={q}"):
    rows = []
    for name in names:
        fd, path = tempfile.mkstemp(suffix=".png")
        os.close(fd)
        info = card.card(name, path, None, url)
        n, box, mod = info["modules"], info["qr_box"], info["module_px"]
        band = info["quiet"]
        q_ok = quiet_ok(path, box, band, mod)
        grid = []
        for scale in (0.45, 0.55, 0.70):
            shot = shoot(path, box, scale=scale)
            for jx, jy in ((-0.22, 0.0), (0.0, 0.0), (0.22, -0.18)):
                m = sample(shot, n, band, mod, jx, jy)
                got = read_back(m, n, info["ecc"])
                ok = bool(got) and got[2] == info["payload"]
                grid.append("ok" if ok else "FAIL")
        rows.append({"name": name, "payload": info["payload"], "version": info["version"],
                     "modules": n, "module_px": mod, "quiet_px": band * mod,
                     "quiet_min_px": q_ok, "grid": grid,
                     "all_ok": all(g == "ok" for g in grid)})
        os.remove(path)
    return rows


if __name__ == "__main__":
    names = sys.argv[1:] or ["林清和", "江雪", "王曜军"]
    print("逐行 3 档清晰度 × 3 种对位偏移，共 9 格；FAIL 表示这次没读出来。")
    print()
    for r in run(names):
        print("%-6s %s  v%d  %d 模块  %dpx/模块  静区 %dpx（最暗 %d）"
              % (r["name"], "PASS" if r["all_ok"] else "FAIL", r["version"],
                 r["modules"], r["module_px"], r["quiet_px"], r["quiet_min_px"]))
        print("       载荷 %s" % r["payload"])
        print("       " + " ".join(r["grid"]))
    ok = all(r["all_ok"] for r in run(names))
    print()
    print("结论：", "全部读回，载荷一致" if ok else "有格子没读出来")
    sys.exit(0 if ok else 1)
