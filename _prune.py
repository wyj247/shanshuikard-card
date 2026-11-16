
# -*- coding: utf-8 -*-
import os, sys, glob, shutil
ROOT = r"C:\Users\ASUS\Documents\deepseek-harness\default-workspace\shanshui"
sys.path.insert(0, ROOT)
os.chdir(ROOT)
import build_site, make_qr, zlib

BASE = "https://wyj247.github.io/shanshuikard-card"
DROP = ["王曜军", "邓涛", "刘宇"]
KEEP = ["林清和", "沈砚秋", "顾南枝", "周叙白", "江照野", "温故", "江雪"]

def pid(n): return "%08x" % (zlib.crc32(n.encode("utf-8")) & 0xffffffff)

tmp = "site_tmp"
if os.path.isdir(tmp): shutil.rmtree(tmp)
build_site.build(tmp, BASE, KEEP)

os.makedirs("docs/n", exist_ok=True)
for f in glob.glob(os.path.join(tmp, "n", "*.html")):
    shutil.copy2(f, os.path.join("docs/n", os.path.basename(f)))
shutil.copy2(os.path.join(tmp, "names.json"), "docs/names.json")
shutil.copy2(os.path.join(tmp, "index.html"), "docs/gallery.html")
shutil.rmtree(tmp)

removed = []
for n in DROP:
    for p in ("docs/n/%s.html" % pid(n), "docs/img/%s.jpg" % pid(n),
              "%s.png" % n, "卡_%s.png" % n, "码_%s.png" % n):
        if os.path.exists(p):
            os.remove(p); removed.append(p)

make_qr.sheet(KEEP, out="二维码集.png")
print("removed:", len(removed))
print("pages:", len(glob.glob("docs/n/*.html")), "imgs:", len(glob.glob("docs/img/*.jpg")))
print("gallery rows:", open("docs/gallery.html", encoding="utf-8").read().count("<li>"))
