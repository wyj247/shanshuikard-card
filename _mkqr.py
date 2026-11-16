
# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, r"C:\Users\ASUS\Documents\deepseek-harness\default-workspace\shanshui")
import make_qr, card

URL = "https://wyj247.github.io/shanshuikard-card/"
res = make_qr.qr_only(URL, scale=12, border=4)
im = res[0] if isinstance(res, tuple) else res
out = r"C:\Users\ASUS\Documents\deepseek-harness\default-workspace\shanshui\qr_app.png"
im.save(out)
print("qr", im.size, out)
info = card.card("林清和", r"C:\Users\ASUS\Documents\deepseek-harness\default-workspace\shanshui\card_app.png", url=URL)
print("card", info["version"], info["modules"], info["module_px"], info["payload"])
