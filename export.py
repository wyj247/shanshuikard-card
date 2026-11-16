# -*- coding: utf-8 -*-
"""把一座山导出成一个「单文件网页」：图是内嵌的 base64，双击就能看，也可以随手发人。

    python export.py 江雪 江雪.html https://你的域名

第三个参数是站点根地址，用来生成二维码（扫码打开 站点/?n=江雪）。
不给的话二维码不画，只出单文件页面。
"""

import sys, os, io, base64, tempfile, zlib
from urllib.parse import quote
from PIL import Image
import shanshui
import card as cardmod


def _b64(data):
    return base64.b64encode(data).decode("ascii")


def export(name, out, base=None, maxw=1280, quality=84, seed=None, url=None):
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

    w, h = im.size
    if max(w, h) > maxw:
        s = maxw / float(max(w, h))
        im = im.resize((int(w * s), int(h * s)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=quality, optimize=True)
    jpg = _b64(buf.getvalue())

    qr_html = ""
    payload = ""
    if url:
        payload = url
        base = base or url
    if base:
        if not payload:
            payload = "%s/?n=%s" % (base.rstrip("/"), quote(name))
        info = __import__("qr").build(payload, "Q")
        qbuf = io.BytesIO()
        _qr_png(info, qbuf)
        qr_html = ('<figure class="qr"><img alt="扫码见山" src="data:image/png;base64,%s">'
                   '<figcaption>%s</figcaption></figure>' % (_b64(qbuf.getvalue()), payload))

    html = TEMPLATE.replace("__NAME__", name).replace("__IMG__", jpg).replace("__QR__", qr_html)
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    return {"out": out, "seed": seed, "payload": payload,
            "bytes": os.path.getsize(out), "size": im.size}


def _qr_png(info, fp, scale=6, border=4):
    m = info["matrix"]
    n = len(m)
    dot = Image.new("L", (n, n), 255)
    px = dot.load()
    for i in range(n):
        for j in range(n):
            if m[i][j]:
                px[j, i] = 0
    full = Image.new("L", ((n + 2 * border) * scale, (n + 2 * border) * scale), 255)
    full.paste(dot.resize((n * scale, n * scale), Image.NEAREST), (border * scale, border * scale))
    full.save(fp, "PNG")


TEMPLATE = """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>__NAME__ 的山</title>
<style>
  body { margin: 0; background: #efe7d6; color: #2b2f30;
         font-family: "KaiTi","STKaiti","Songti SC",serif; }
  .wrap { max-width: 1100px; margin: 0 auto; padding: 28px 18px 60px; }
  h1 { font-weight: 400; letter-spacing: .3em; font-size: 22px; margin: 0 0 16px; }
  .pic img { width: 100%; height: auto; display: block; border-radius: 6px;
             box-shadow: 0 6px 24px rgba(40,34,24,.18); }
  .qr { margin: 22px 0 0; display: inline-block; background: #fbf7ee; padding: 10px;
        border-radius: 6px; border: 1px solid #ddd3bd; }
  .qr img { width: 190px; height: 190px; display: block; }
  .qr figcaption { font-size: 11px; color: #6f6a5c; word-break: break-all; max-width: 190px; }
  p { color: #5c5747; line-height: 1.9; font-size: 14px; }
</style></head><body><div class="wrap">
  <h1>__NAME__ 的山</h1>
  <div class="pic"><img alt="__NAME__ 的山" src="data:image/jpeg;base64,__IMG__"></div>
  __QR__
  <p>这幅画由名字算出：同样的名字永远得到同一座山。页面里的图是内嵌的，
     断网、换个地方、发给别人，看到的都是它。</p>
</div></body></html>"""


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    name, out = sys.argv[1], sys.argv[2]
    base = sys.argv[3] if len(sys.argv) > 3 else None
    print(export(name, out, base))
