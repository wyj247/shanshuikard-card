# -*- coding: utf-8 -*-
"""一笔山水 —— 输入名字，生成一幅水墨山水，落款钤印。
用法: python shanshui.py 名字 输出.png [seed]
"""
import sys, os, math, random, zlib
import numpy as np
from PIL import Image, ImageDraw, ImageFont

W, H = 1600, 1000
PAPER = (245.0, 239.0, 226.0)

POEMS = [
    ("空山新雨后", "清泉石上流"), ("行到水穷处", "坐看云起时"),
    ("明月松间照", "清泉石上流"), ("山色有无中", "江流天地外"),
    ("白云回望合", "青霭入看无"), ("松风吹解带", "山月照弹琴"),
    ("孤舟蓑笠翁", "独钓寒江雪"), ("野旷天低树", "江清月近人"),
    ("山随平野尽", "江入大荒流"), ("泉声咽危石", "日色冷青松"),
    ("千山鸟飞绝", "万径人踪灭"), ("江流石不转", "山高月小"),
    ("星垂平野阔", "月涌大江流"), ("寒山转苍翠", "秋水日潺湲"),
    ("野径云俱黑", "江船火独明"), ("风鸣两岸叶", "月照一孤舟"),
    ("山光忽西落", "池月渐东上"), ("月下飞天镜", "云生结海楼"),
    ("春潮带雨晚来急", "野渡无人舟自横"), ("白云生处有人家", "远上寒山石径斜"),
]

PALETTES = [
    [(180, 182, 177), (152, 157, 152), (112, 120, 116), (76, 86, 86), (40, 48, 50)],
    [(190, 198, 189), (154, 172, 160), (106, 134, 122), (66, 98, 94), (34, 58, 60)],
    [(198, 188, 174), (174, 154, 134), (140, 114, 94), (104, 80, 62), (66, 50, 42)],
]


# 字象：名字里的字能认出什么，画面就跟着变；认不出的，交给种子。
TAG_CHARS = {
    "水": "江河水清溪涵泽涛波澜洲湖海源润滋沐沙沈温湘洛淮洋浦",
    "木": "林松柏梅枝桐杨柳枫楠椿榕槿杭楚柯棠森",
    "山": "山岳峰峦岭岩峻巍崖岚嶂崇岐",
    "日": "日昭曜晖昕晨曦阳旭晟熙暖照",
    "月": "月明朔望朗胧朦",
    "雪": "雪霜冰寒凝",
    "雨": "雨霖霏露霭",
    "云": "云霞雯霁雾",
    "舟": "舟帆航渡船",
    "鸟": "鸟雁鸿鹤鹏燕鸾鸢",
    "素": "白素玄墨",
    "秋": "秋",
    "春": "春",
}

# 每个意象偏好什么样的诗句
POEM_KEYS = {"水": "江河泉流雨水清", "木": "松林树", "山": "山", "日": "日",
             "月": "月明", "雪": "雪寒", "雨": "雨", "云": "云", "舟": "舟",
             "鸟": "鸟", "素": "白", "秋": "秋", "春": "春"}

# 字义越具体，越该压过泛泛的「水/木」——名字里有雪，就该落到雪诗上
TAG_WEIGHT = {"雪": 3, "秋": 3, "春": 3, "舟": 2, "日": 2, "月": 2,
              "鸟": 2, "雨": 1, "云": 1, "山": 1, "水": 1, "木": 1, "素": 1}


def imagery(name):
    return [t for t, chars in TAG_CHARS.items() if any(c in chars for c in name)]


def pick_poem(rng, tags, avoid=()):
    """按字象给每句诗打分，再在分数相近的句子里按种子抽——
    同一种意象（比如都带水字）也能出不同的诗，而不是全落在一句上。
    avoid 里的字不能出现在诗里：画上画了落日，就不该配「明月松间照」。"""
    pool = [p for p in POEMS if not any(c in p[0] + p[1] for c in avoid)] or POEMS
    scored = []
    for p in pool:
        text = set(p[0] + p[1])
        sc = sum(TAG_WEIGHT.get(t, 1) * len(text & set(POEM_KEYS.get(t, ""))) for t in tags)
        scored.append((sc, p))
    best = max(s for s, _ in scored)
    if best >= 2:
        cands = [(s, p) for s, p in scored if s >= best - 1]
    elif best == 1:
        cands = [(s, p) for s, p in scored if s == 1]
    else:
        cands = scored
    return rng.choices([p for _, p in cands], weights=[(s + 1) ** 3 for s, _ in cands])[0]


def smooth_noise(rng, n=40):
    vals = np.array([rng.random() for _ in range(n)])
    x = np.linspace(0, n - 1, W)
    i0 = np.floor(x).astype(int)
    i1 = np.minimum(i0 + 1, n - 1)
    f = x - i0
    f = f * f * (3 - 2 * f)
    v = vals[i0] * (1 - f) + vals[i1] * f
    return v - v.mean()


def noise2(rng, gh, gw, lo=0.0, hi=1.0):
    g = np.array([[rng.random() for _ in range(gw)] for _ in range(gh)])
    yi = np.linspace(0, gh - 1, H)
    xi = np.linspace(0, gw - 1, W)
    y0 = np.floor(yi).astype(int)
    y1 = np.minimum(y0 + 1, gh - 1)
    fy = yi - y0
    fy = fy * fy * (3 - 2 * fy)
    x0 = np.floor(xi).astype(int)
    x1 = np.minimum(x0 + 1, gw - 1)
    fx = xi - x0
    fx = fx * fx * (3 - 2 * fx)
    a = g[y0][:, x0]
    b = g[y0][:, x1]
    c = g[y1][:, x0]
    d = g[y1][:, x1]
    top = a * (1 - fx)[None, :] + b * fx[None, :]
    bot = c * (1 - fx)[None, :] + d * fx[None, :]
    v = top * (1 - fy)[:, None] + bot * fy[:, None]
    return v * (hi - lo) + lo


def massif(rng, base, count, hmax, side):
    """一组山峰的轮廓；side=-1 主体偏左，+1 偏右"""
    xs = np.arange(W, dtype=float)
    acc = np.zeros(W)
    if side < 0:
        mc = rng.uniform(-0.02, 0.34) * W
    else:
        mc = rng.uniform(0.66, 1.02) * W
    acc += np.exp(-np.abs((xs - mc) / rng.uniform(0.24, 0.42) * W) ** rng.uniform(1.5, 2.0))
    for _ in range(count):
        c = rng.uniform(-0.12, 1.12) * W
        wdt = rng.uniform(0.09, 0.28) * W
        hh = rng.uniform(0.32, 0.92)
        p = rng.uniform(1.5, 2.3)
        acc += hh * np.exp(-np.abs((xs - c) / wdt) ** p)
    acc = acc / acc.max()
    acc = np.clip(acc + 0.045 * smooth_noise(rng, 90), 0, 1)
    return base - hmax * acc ** 0.92


def strokes(rng, ridge, base, n):
    """沿山坡方向的皴擦短线"""
    out = np.zeros((H, W))
    for _ in range(n):
        sx = rng.uniform(6, W - 6)
        i = int(sx)
        sy = float(ridge[i]) + rng.uniform(6, 240)
        if sy > base + 10 or sy > H - 30:
            continue
        slope = (ridge[min(W - 1, i + 10)] - ridge[max(0, i - 10)]) / 20.0
        ang = math.atan(np.clip(slope, -1.6, 1.6)) + rng.uniform(-0.35, 0.35)
        L = rng.uniform(12, 34)
        x2 = sx + math.cos(ang) * L
        y2 = sy + abs(math.sin(ang)) * L + rng.uniform(3, 12)
        w = rng.uniform(1.3, 2.4)
        x0 = max(0, int(min(sx, x2) - 6))
        x1 = min(W, int(max(sx, x2) + 7))
        y0 = max(0, int(min(sy, y2) - 6))
        y1 = min(H, int(max(sy, y2) + 7))
        if x1 <= x0 or y1 <= y0:
            continue
        yy = np.arange(y0, y1, dtype=float)[:, None]
        xx = np.arange(x0, x1, dtype=float)[None, :]
        vx, vy = x2 - sx, y2 - sy
        L2 = vx * vx + vy * vy + 1e-6
        t = np.clip(((xx - sx) * vx + (yy - sy) * vy) / L2, 0, 1)
        dd = np.sqrt((xx - (sx + t * vx)) ** 2 + (yy - (sy + t * vy)) ** 2)
        out[y0:y1, x0:x1] += np.exp(-(dd / w) ** 2) * rng.uniform(0.5, 1.0)
    return out


def over(img, color, alpha):
    a = np.clip(alpha, 0, 1)[..., None]
    return img * (1 - a) + np.array(color, dtype=float) * a


def load_font(size):
    for p in (r"C:\Windows\Fonts\simkai.ttf", r"C:\Windows\Fonts\STKAITI.TTF",
              r"C:\Windows\Fonts\simsun.ttc", r"C:\Windows\Fonts\msyh.ttc"):
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                pass
    return ImageFont.load_default()


def pine(dr, x, y, h, col, rng):
    pts = [(x, y)]
    for i in range(1, 6):
        pts.append((x + math.sin(i * 1.1 + rng.random()) * h * 0.045, y - h * i / 5.0))
    dr.line(pts, fill=col, width=2)
    for i in range(4):
        yy = y - h * (0.30 + 0.17 * i)
        span = h * (0.36 - 0.06 * i)
        if span < 3:
            continue
        for sgn in (-1, 1):
            ex, ey = x + sgn * span, yy + span * 0.30
            dr.line([(x, yy), (ex, ey)], fill=col, width=2 if sgn > 0 else 1)
            for t in np.linspace(0.3, 1.0, 7):
                bx, by = x + sgn * span * t, yy + span * 0.30 * t
                L = 7 + rng.uniform(0, 4)
                dr.line([(bx, by), (bx + sgn * 1.5, by - L)], fill=col, width=1)


def render(name, out, seed):
    global W, H
    rng = random.Random(seed)

    # ── 画幅
    fmt = rng.choices(["横", "方", "立"], weights=[0.55, 0.25, 0.20])[0]
    W, H = {"横": (1600, 1000), "方": (1250, 1250), "立": (1000, 1400)}[fmt]
    s = min(W, H) / 1000.0
    k = H / 1000.0

    tags = imagery(name)

    # ── 日月先定死（字象强制），诗再避开矛盾的意象
    if "日" in tags:
        force_moon, avoid = "日", ("月",)
    elif "月" in tags:
        force_moon, avoid = "月", ("日",)
    elif "雪" in tags:
        force_moon, avoid = "无", ("日", "月")
    else:
        force_moon, avoid = None, ()

    l1, l2 = pick_poem(rng, tags, avoid)   # 先定诗，画面再照着诗意补
    ptxt = l1 + l2

    # ── 配色：春青绿、秋赭石、雪水墨，其余交给种子
    if "春" in tags:
        pal = PALETTES[1]
    elif "秋" in tags:
        pal = PALETTES[2]
    elif "雪" in tags:
        pal = PALETTES[0]
    else:
        pal = rng.choices(PALETTES, weights=[0.58, 0.26, 0.16])[0]

    # 雪景：整体提亮，像落了雪
    if "雪" in tags:
        pal = [tuple(int(c + (252 - c) * 0.42) for c in col) for col in pal]

    # ── 天气：雨字下雨，云/雪起雾
    if "雨" in tags or "雨" in ptxt:
        weather = "雨"
    elif "云" in tags or "雪" in tags:
        weather = "雾"
    else:
        weather = rng.choices(["晴", "雾", "雨"], weights=[0.58, 0.27, 0.15])[0]

    side = rng.choice([-1, 1])                      # 山的主体在左 / 右

    # ── 日月：日字有日，月字有月，雪景留白无日月
    if force_moon:
        moon = force_moon
    elif "月" in ptxt:
        moon = "月"
    elif "日" in ptxt:
        moon = "日"
    else:
        moon = rng.choices(["日", "月", "无"], weights=[0.42, 0.36, 0.22])[0]

    # ── 点缀：舟/木送树/鸟，雪景不画鸟
    if "舟" in tags or "舟" in ptxt:
        with_boat = True
    elif "水" in tags:
        with_boat = rng.random() < 0.85
    else:
        with_boat = rng.random() < 0.62
    with_pines = True if "木" in tags else rng.random() < 0.70
    with_birds = False if "雪" in tags else (
        True if ("鸟" in tags or "鸟" in ptxt) else rng.random() < 0.70)

    ys = np.arange(H, dtype=float)[:, None]
    xs = np.arange(W, dtype=float)[None, :]

    # ── 天
    t = np.clip(ys / (H * 0.9), 0, 1)
    sky = np.array([250.0, 246.0, 235.0]) * (1 - t) + np.array([234.0, 229.0, 215.0]) * t
    img = np.broadcast_to(sky[:, None, :], (H, W, 3)).copy()

    # ── 日月
    if moon != "无":
        mx = rng.uniform(0.50, 0.84) * W
        if abs(mx - (0.86 if side < 0 else 0.14) * W) < 0.20 * W:
            mx = W - mx
        my = rng.uniform(0.10, 0.19) * H
        mr = rng.uniform(0.036, 0.052) * min(W, H) * 1.6
        d = np.sqrt((xs - mx) ** 2 + (ys - my) ** 2)
        soft = np.clip((mr - d) / (2.0 * s), 0, 1)
        if moon == "日":
            img = over(img, (198, 104, 88), soft * 0.38)
        else:
            img = over(img, (236, 234, 226), soft * 0.85)
            img = over(img, (150, 152, 148), np.exp(-((d - mr) / (2.2 * s)) ** 2) * 0.22)

    # ── 层叠山体
    base_f = [0.360, 0.455, 0.560, 0.680, 0.800]
    hmax_f = [0.235, 0.305, 0.350, 0.385, 0.365]
    alphas = [0.34, 0.48, 0.64, 0.82, 0.94]
    mist_alpha = {"晴": 0.54, "雾": 0.68, "雨": 0.64}[weather] + (0.10 if "雪" in tags else 0.0)
    peak = 1.13 if "山" in tags else 1.0
    ridges = []
    for i in range(5):
        base = base_f[i] * H
        r = massif(rng, base, 3 if i < 4 else 4, hmax_f[i] * H * peak, side if i >= 2 else -side)
        ridges.append(r)
        dd = ys - r[None, :]
        edge = np.clip(dd / (2.5 * s), 0, 1)
        tex = noise2(rng, 26, 16, 0.64, 1.36)
        fade = 1.0 - 0.50 * np.clip((dd - 30 * s) / (300.0 * s), 0, 1)
        col = pal[i]
        img = over(img, col, alphas[i] * edge * fade * tex)
        img = over(img, tuple(c * 0.62 for c in col),
                   alphas[i] * 0.45 * np.exp(-((dd - 1.5 * s) / (3.2 * s)) ** 2))
        brush = strokes(rng, r, base, 170 if i == 4 else 70)
        img = over(img, tuple(c * 0.55 for c in col),
                   brush * alphas[i] * edge *
                   np.clip(1 - (dd - 16 * s) / (260.0 * s), 0, 1) * 0.60)
        cen = base + 14 * s + 40 * s * smooth_noise(rng, 26)
        sig = rng.uniform(40, 62) * s * (1.25 if weather == "雾" else 1.0)
        band = np.exp(-((ys - cen[None, :]) ** 2) / (2 * sig ** 2))
        band = band * (0.42 + 1.05 * noise2(rng, 9, 7))
        img = over(img, PAPER, np.clip(band, 0, 1) * mist_alpha)

    # ── 雾天：再压一层大雾，吞掉远山
    if weather == "雾":
        cy = 0.60 * H + 40 * s * smooth_noise(rng, 12)
        fog = np.exp(-((ys - cy[None, :]) ** 2) / (2 * (0.13 * H) ** 2))
        img = over(img, PAPER, np.clip(fog * noise2(rng, 6, 5, 0.5, 1.1), 0, 1) * 0.32)

    # ── 水
    wy_base = 0.760 if "水" in tags else (0.815 if "山" in tags else 0.800)
    wy = (wy_base + rng.uniform(0.0, 0.045)) * H + 7.0 * smooth_noise(rng, 18)
    wa = np.clip((ys - wy[None, :]) / (24.0 * s), 0, 1) * 0.88
    _wt = np.clip((ys - wy[None, :]) / (H - wy[None, :]), 0, 1)[..., None]
    wcol = np.array([209.0, 214.0, 210.0]) * (1 - _wt) + np.array([189.0, 195.0, 192.0]) * _wt
    img = img * (1 - wa[..., None]) + np.broadcast_to(wcol, img.shape) * wa[..., None]
    img = over(img, PAPER, np.exp(-((ys - wy[None, :]) ** 2) / (2 * (24.0 * s) ** 2)) * 0.55)

    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    dr = ImageDraw.Draw(im, "RGBA")

    # ── 雨
    if weather == "雨":
        for _ in range(170):
            x0 = rng.uniform(-0.1 * W, W)
            y0 = rng.uniform(0, H * 0.95)
            L = rng.uniform(18, 40) * s
            dr.line([(x0, y0), (x0 - L * 0.45, y0 + L)], fill=(92, 102, 100, 26), width=1)

    # ── 水纹
    for _ in range(14):
        y0 = rng.uniform(wy[0] + 22 * s, H - 12 * s)
        x0 = rng.uniform(0, W * 0.6)
        x1 = x0 + rng.uniform(W * 0.08, W * 0.30)
        dr.line([(x0, y0), (x1, y0)], fill=(108, 120, 118, 30), width=1)

    # ── 舟
    if with_boat:
        bx = rng.uniform(0.16, 0.72) * W
        by = float(wy[0]) + rng.uniform(52, 88) * s
        bs = 46 * s
        dr.arc([bx - bs, by - 12 * s, bx + bs, by + 12 * s], 0, 180,
               fill=(36, 42, 40, 215), width=max(2, int(3 * s)))
        dr.line([(bx - bs, by), (bx + bs, by)], fill=(36, 42, 40, 190), width=max(1, int(2 * s)))
        dr.line([(bx - 6 * s, by - 2 * s), (bx - 6 * s, by - 46 * s)], fill=(36, 42, 40, 200), width=2)
        dr.polygon([(bx - 6 * s, by - 46 * s), (bx + 28 * s, by - 20 * s), (bx - 6 * s, by - 18 * s)],
                   outline=(36, 42, 40, 200))

    # ── 近树
    nr = ridges[-1]
    if with_pines:
        for _ in range(18):
            tx = rng.uniform(0, W * 0.95)
            ty = float(nr[int(tx)]) + rng.uniform(-4, 8) * s
            if ty < wy[0] - 120 * s or rng.random() < 0.42:
                continue
            pine(dr, tx, ty, rng.uniform(22, 44) * s, (28, 34, 34, 215), rng)

    # ── 苔点
    for _ in range(46):
        px = rng.uniform(0, W)
        py = float(nr[int(px)]) + rng.uniform(2, 90) * s
        if py > wy[0] - 8 * s:
            continue
        rr = rng.uniform(1.2, 2.6) * s
        dr.ellipse([px - rr, py - rr, px + rr, py + rr], fill=(28, 34, 34, 110))

    # ── 飞鸟
    if with_birds:
        for _ in range(rng.randint(2, 4)):
            bx2 = rng.uniform(0.18, 0.82) * W
            by2 = rng.uniform(0.09, 0.20) * H
            bs2 = rng.uniform(7, 13) * s
            dr.arc([bx2 - bs2, by2 - bs2 * 0.8, bx2, by2 + bs2 * 0.4], 200, 340,
                   fill=(45, 50, 48, 170), width=2)
            dr.arc([bx2, by2 - bs2 * 0.8, bx2 + bs2, by2 + bs2 * 0.4], 200, 340,
                   fill=(45, 50, 48, 170), width=2)

    # ── 题款：诗在山对面，名字在上首
    fs = int(46 * s)
    f46 = load_font(fs)
    ink = (32, 38, 36, 228)

    def vtext(txt, x, y, font, gap):
        for i, ch in enumerate(txt):
            dr.text((x, y + i * (font.size + gap)), ch, font=font, fill=ink,
                    anchor="ma", stroke_width=max(2, int(4 * s)),
                    stroke_fill=(245, 239, 226, 165))

    if side < 0:
        px1, px2 = 0.872 * W, 0.812 * W
        tx = 0.06 * W
    else:
        px1, px2 = 0.128 * W, 0.188 * W
        tx = 0.94 * W
    top = 0.126 * H
    vtext(l1, int(px1), int(top), f46, int(12 * s))
    vtext(l2, int(px2), int(top), f46, int(12 * s))

    ft = load_font(int(36 * s))
    title = (name if name else "山水") + "图"
    for i, ch in enumerate(title):
        dr.text((int(tx), int(0.118 * H) + i * (ft.size + int(10 * s))), ch, font=ft,
                fill=(56, 52, 44, 200), anchor="ma",
                stroke_width=max(2, int(4 * s)), stroke_fill=(245, 239, 226, 155))

    # ── 印
    ss = int(54 * s)
    sx = int(px1 + (10 * s if side < 0 else -10 * s))
    sy = int(top + 5 * (fs + 12 * s) + 56 * s)
    dr.rectangle([sx - ss // 2, sy, sx + ss // 2, sy + ss], fill=(170, 54, 44, 232))
    dr.text((sx, sy + ss // 2 - 1), (name[-1] if name else "山"), font=load_font(int(33 * s)),
            fill=(246, 240, 227, 245), anchor="mm")
    dr.text((sx, sy + ss + 30 * s), "丙午冬", font=load_font(int(22 * s)),
            fill=(62, 57, 46, 175), anchor="ma",
            stroke_width=2, stroke_fill=(245, 239, 226, 200))

    # ── 纸纹 + 暗角
    arr = np.asarray(im).astype(np.float64)
    arr = np.clip(arr + np.random.default_rng(seed).normal(0, 3.0, arr.shape), 0, 255)
    vg = np.sqrt(((xs - W / 2) / (W * 0.62)) ** 2 + ((ys - H / 2) / (H * 0.62)) ** 2)
    arr = arr * (1 - np.clip((vg - 0.55) / 0.75, 0, 1)[..., None] * 0.22)
    Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).save(out)
    print(f"[{name}] 字象={'、'.join(tags) or '无'} · 诗={l1}／{l2} · "
          f"{W}×{H} · {weather} · {moon}", flush=True)
    return out


if __name__ == "__main__":
    name = sys.argv[1] if len(sys.argv) > 1 else "山水"
    out = sys.argv[2] if len(sys.argv) > 2 else "out.png"
    seed = int(sys.argv[3]) if len(sys.argv) > 3 else zlib.crc32(name.encode("utf-8")) % 100000
    render(name, out, seed)
