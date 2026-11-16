import random, sys
sys.path.insert(0, r"C:\\Users\\ASUS\\Documents\\deepseek-harness\\default-workspace\\shanshui")
r = random.Random(7)
print("stream", [round(r.random(), 9) for _ in range(5)])
r2 = random.Random(7)
print("choice", r2.choice([-1, 1]), r2.choice([-1, 1]), r2.choice([-1, 1]))
r3 = random.Random(7)
print("choices", r3.choices(["日", "月", "无"], weights=[0.42, 0.36, 0.22]))
import numpy as np
import shanshui
shanshui.W, shanshui.H = 1600, 1000
r4 = random.Random(7)
ridge = shanshui.massif(r4, 360.0, 3, 235.0, -1)
print("ridge", [round(float(ridge[i]), 2) for i in (0, 100, 400, 800, 1200, 1599)])
print("minmax", round(float(ridge.min()), 2), round(float(ridge.max()), 2))
