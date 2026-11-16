
# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, r"C:\Users\ASUS\Documents\deepseek-harness\default-workspace\shanshui")
from PIL import Image
import verify_scan
URL = "https://wyj247.github.io/shanshuikard-card/"
im = Image.open(r"C:\Users\ASUS\Documents\deepseek-harness\default-workspace\shanshui\qr_app.png").convert("L")
m = verify_scan.sample(im, 33, 4, 12)
res = verify_scan.read_back(m, 33, want=URL)
print("decode:", res if not isinstance(res, dict) else {k: res[k] for k in list(res)[:4]})
