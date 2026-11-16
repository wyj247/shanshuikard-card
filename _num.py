# -*- coding: utf-8 -*-
import sys, zlib
sys.path.insert(0, r"C:\Users\ASUS\Documents\deepseek-harness\default-workspace\shanshui")
import numpy as np
from PIL import Image
import shanshui

orig = Image.fromarray
state = {"n": 0}
def patched(arr, *a, **k):
    state["n"] += 1
    if state["n"] == 1:
        orig(arr).save(r"C:\Users\ASUS\Documents\deepseek-harness\default-workspace\shanshui\_pnum7.png")
    return orig(arr, *a, **k)
Image.fromarray = patched
shanshui.render("林清和", r"C:\Users\ASUS\Documents\deepseek-harness\default-workspace\shanshui\_x.png", 7)
print("ok", state["n"])
