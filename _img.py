
# -*- coding: utf-8 -*-
import os, sys, glob
ROOT = r"C:\Users\ASUS\Documents\deepseek-harness\default-workspace\shanshui"
sys.path.insert(0, ROOT); os.chdir(ROOT)
import gen_img
for n in ["王曜军"]:
    info = gen_img.make(n, outdir="docs/img", maxw=1280, quality=84)
    print("img", info if not isinstance(info, dict) else info.get("out", info))
print("imgs", len(glob.glob("docs/img/*.jpg")))
