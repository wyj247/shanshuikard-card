
# -*- coding: utf-8 -*-
import os, sys, glob, shutil
ROOT = r"C:\Users\ASUS\Documents\deepseek-harness\default-workspace\shanshui"
sys.path.insert(0, ROOT); os.chdir(ROOT)
import build_site, make_qr, card, shanshui, zlib

BASE = "https://wyj247.github.io/shanshuikard-card"
NAMES = ["王曜军", "林清和", "沈砚秋", "顾南枝", "周叙白", "江照野", "温故", "江雪"]
def pid(n): return "%08x" % (zlib.crc32(n.encode("utf-8")) & 0xffffffff)

tmp = "site_tmp"
if os.path.isdir(tmp): shutil.rmtree(tmp)
build_site.build(tmp, BASE, NAMES)
os.makedirs("docs/n", exist_ok=True)
for f in glob.glob(os.path.join(tmp, "n", "*.html")):
    shutil.copy2(f, os.path.join("docs/n", os.path.basename(f)))
shutil.copy2(os.path.join(tmp, "names.json"), "docs/names.json")
shutil.copy2(os.path.join(tmp, "index.html"), "docs/gallery.html")
shutil.rmtree(tmp)

n = "王曜军"
shanshui.render(n, n + ".png", shanshui.seed_of(n) if hasattr(shanshui, "seed_of") else zlib.crc32(n.encode()) % 100000)
im, _i = make_qr.qr_only("%s/%s" % (BASE, "n/%s.html" % pid(n)), scale=12, border=4)
im.save("码_%s.png" % n)
card.card(n, "卡_%s.png" % n, url="%s/n/%s.html" % (BASE, pid(n)))
make_qr.sheet(NAMES, out="二维码集.png")
print("pages", len(glob.glob("docs/n/*.html")), "imgs", len(glob.glob("docs/img/*.jpg")),
      "rows", open("docs/gallery.html", encoding="utf-8").read().count("<li>"))
