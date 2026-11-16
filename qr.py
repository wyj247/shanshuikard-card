# -*- coding: utf-8 -*-
"""最小 QR 编码器：字节模式，版本 1-10，纠错 L/M/Q/H，纯标准库实现。
附解码自检：重读模块矩阵 -> 去掩码 -> 反交织 -> 每块 RS 校验子和为零 -> 解析原文。"""

EC_BITS = {"L": 0b01, "M": 0b00, "Q": 0b11, "H": 0b10}

# 版本 -> {等级: (第一组块数, 第一组数据码字, 第二组块数, 第二组数据码字, 每块纠错码字)}
SPEC = {
    1:  {"L": (1, 19, 0, 0, 7),  "M": (1, 16, 0, 0, 10), "Q": (1, 13, 0, 0, 13), "H": (1, 9, 0, 0, 17)},
    2:  {"L": (1, 34, 0, 0, 10), "M": (1, 28, 0, 0, 16), "Q": (1, 22, 0, 0, 22), "H": (1, 16, 0, 0, 28)},
    3:  {"L": (1, 55, 0, 0, 15), "M": (1, 44, 0, 0, 26), "Q": (2, 17, 0, 0, 18), "H": (2, 13, 0, 0, 22)},
    4:  {"L": (1, 80, 0, 0, 20), "M": (2, 32, 0, 0, 18), "Q": (2, 24, 0, 0, 26), "H": (4, 9, 0, 0, 16)},
    5:  {"L": (1, 108, 0, 0, 26), "M": (2, 43, 0, 0, 24), "Q": (2, 15, 2, 16, 18), "H": (2, 11, 2, 12, 22)},
    6:  {"L": (2, 68, 0, 0, 18), "M": (4, 27, 0, 0, 16), "Q": (4, 19, 0, 0, 24), "H": (4, 15, 0, 0, 28)},
    7:  {"L": (2, 78, 0, 0, 20), "M": (4, 31, 0, 0, 18), "Q": (2, 14, 4, 15, 18), "H": (4, 13, 0, 0, 26)},
    8:  {"L": (2, 97, 0, 0, 24), "M": (2, 38, 2, 39, 22), "Q": (4, 18, 2, 19, 22), "H": (4, 14, 2, 15, 26)},
    9:  {"L": (2, 116, 0, 0, 30), "M": (3, 36, 2, 37, 22), "Q": (4, 16, 4, 17, 20), "H": (4, 12, 4, 13, 24)},
    10: {"L": (2, 68, 2, 69, 18), "M": (4, 43, 1, 44, 26), "Q": (6, 19, 2, 20, 24), "H": (6, 15, 2, 16, 28)},
}

ALIGN = {1: [], 2: [6, 18], 3: [6, 22], 4: [6, 26], 5: [6, 30], 6: [6, 34],
         7: [6, 22, 38], 8: [6, 24, 42], 9: [6, 26, 46], 10: [6, 28, 50]}

# ---------------- GF(256) ----------------
EXP = [0] * 512
LOG = [0] * 256
_x = 1
for _i in range(255):
    EXP[_i] = _x
    LOG[_x] = _i
    _x <<= 1
    if _x & 0x100:
        _x ^= 0x11D
for _i in range(255, 512):
    EXP[_i] = EXP[_i - 255]


def gmul(a, b):
    if a == 0 or b == 0:
        return 0
    return EXP[LOG[a] + LOG[b]]


def rs_generator(n):
    g = [1]
    for i in range(n):
        ng = [0] * (len(g) + 1)
        for j, c in enumerate(g):
            ng[j] ^= c
            ng[j + 1] ^= gmul(c, EXP[i])
        g = ng
    return g


def rs_encode(data, n):
    g = rs_generator(n)
    buf = list(data) + [0] * n
    for i in range(len(data)):
        c = buf[i]
        if c:
            for j in range(len(g)):
                buf[i + j] ^= gmul(g[j], c)
    return buf[len(data):]


def rs_syndrome(block, n):
    """block 含数据+校验，n 为校验码字数；返回全部为 0 才是合法码字。"""
    synd = []
    for i in range(n):
        s = 0
        for b in block:
            s = gmul(s, EXP[i]) ^ b
        synd.append(s)
    return synd


# ---------------- 数据码字 ----------------
def make_codewords(payload, version, ecc):
    g1, d1, g2, d2, ecw = SPEC[version][ecc]
    cap_words = g1 * d1 + g2 * d2
    cap_bits = cap_words * 8
    cc = 8 if version < 10 else 16
    bits = []

    def put(v, n):
        for i in range(n - 1, -1, -1):
            bits.append((v >> i) & 1)

    put(0b0100, 4)
    put(len(payload), cc)
    for b in payload:
        put(b, 8)
    if len(bits) > cap_bits:
        raise ValueError("payload too long for this version")
    bits += [0] * min(4, cap_bits - len(bits))
    while len(bits) % 8:
        bits.append(0)
    data = [int("".join(map(str, bits[i:i + 8])), 2) for i in range(0, len(bits), 8)]
    k = 0
    while len(data) < cap_words:
        data.append(0xEC if k % 2 == 0 else 0x11)
        k += 1

    blocks, pos = [], 0
    for _ in range(g1):
        blocks.append(data[pos:pos + d1]); pos += d1
    for _ in range(g2):
        blocks.append(data[pos:pos + d2]); pos += d2
    ecs = [rs_encode(b, ecw) for b in blocks]

    out = []
    for i in range(max(len(b) for b in blocks)):
        for b in blocks:
            if i < len(b):
                out.append(b[i])
    for i in range(ecw):
        for e in ecs:
            out.append(e[i])
    return out, blocks, ecs


def pick_version(nbytes, ecc):
    for v in range(1, 11):
        g1, d1, g2, d2, _ = SPEC[v][ecc]
        cc = 8 if v < 10 else 16
        if 4 + cc + 8 * nbytes <= (g1 * d1 + g2 * d2) * 8:
            return v
    raise ValueError("payload too long")


# ---------------- 矩阵 ----------------
def _fmt_bits(ecc, mask):
    d = (EC_BITS[ecc] << 3) | mask
    rem = d << 10
    for i in range(14, 9, -1):
        if rem >> i & 1:
            rem ^= 0x537 << (i - 10)
    return ((d << 10) | rem) ^ 0x5412


def _ver_bits(version):
    rem = version << 12
    for i in range(17, 11, -1):
        if rem >> i & 1:
            rem ^= 0x1F25 << (i - 12)
    return (version << 12) | rem


MASK_FN = [
    lambda i, j: (i + j) % 2 == 0,
    lambda i, j: i % 2 == 0,
    lambda i, j: j % 3 == 0,
    lambda i, j: (i + j) % 3 == 0,
    lambda i, j: (i // 2 + j // 3) % 2 == 0,
    lambda i, j: (i * j) % 2 + (i * j) % 3 == 0,
    lambda i, j: ((i * j) % 2 + (i * j) % 3) % 2 == 0,
    lambda i, j: ((i + j) % 2 + (i * j) % 3) % 2 == 0,
]


def build(payload, ecc="M", version=None, mask=None):
    if isinstance(payload, str):
        payload = payload.encode("utf-8")
    if version is None:
        version = pick_version(len(payload), ecc)
    size = 17 + 4 * version
    codewords, _, _ = make_codewords(payload, version, ecc)

    mat = [[0] * size for _ in range(size)]
    func = [[False] * size for _ in range(size)]

    def setf(i, j, v):
        mat[i][j] = v
        func[i][j] = True

    # 定位图形 + 分隔符
    for r, c in ((0, 0), (0, size - 7), (size - 7, 0)):
        for i in range(-1, 8):
            for j in range(-1, 8):
                ii, jj = r + i, c + j
                if 0 <= ii < size and 0 <= jj < size:
                    inside = 0 <= i <= 6 and 0 <= j <= 6
                    dark = inside and (i in (0, 6) or j in (0, 6) or (2 <= i <= 4 and 2 <= j <= 4))
                    setf(ii, jj, 1 if dark else 0)
    # 时序图形
    for i in range(size):
        if not func[6][i]:
            setf(6, i, 1 if i % 2 == 0 else 0)
        if not func[i][6]:
            setf(i, 6, 1 if i % 2 == 0 else 0)
    # 校正图形
    cen = ALIGN[version]
    finders = [(0, 0), (0, size - 7), (size - 7, 0)]

    def hits_finder(r, c):
        for fr, fc in finders:
            if r - 2 <= fr + 7 and fr - 1 <= r + 2 and c - 2 <= fc + 7 and fc - 1 <= c + 2:
                return True
        return False

    for r in cen:
        for c in cen:
            if hits_finder(r, c):
                continue
            for i in range(-2, 3):
                for j in range(-2, 3):
                    dark = max(abs(i), abs(j)) != 1
                    setf(r + i, c + j, 1 if dark else 0)
    # 预留格式区
    for i in range(9):
        if not func[8][i]:
            setf(8, i, 0)
        if not func[i][8]:
            setf(i, 8, 0)
    for i in range(8):
        if not func[8][size - 1 - i]:
            setf(8, size - 1 - i, 0)
        if not func[size - 1 - i][8]:
            setf(size - 1 - i, 8, 0)
    setf(size - 8, 8, 1)  # 固定黑模块
    # 版本信息（>=7）
    if version >= 7:
        vb = _ver_bits(version)
        for i in range(18):
            bit = (vb >> i) & 1
            setf(size - 11 + i % 3, i // 3, bit)
            setf(i // 3, size - 11 + i % 3, bit)

    # 数据铺放
    data = []
    for cw in codewords:
        for k in range(7, -1, -1):
            data.append((cw >> k) & 1)
    idx = 0
    col = size - 1
    upward = True
    while col > 0:
        if col == 6:
            col -= 1
        rows = range(size - 1, -1, -1) if upward else range(size)
        for r in rows:
            for c in (col, col - 1):
                if not func[r][c]:
                    mat[r][c] = data[idx] if idx < len(data) else 0
                    idx += 1
        upward = not upward
        col -= 2

    def place_format(mm, m):
        f = _fmt_bits(ecc, m)
        for i in range(15):
            bit = (f >> i) & 1
            if i < 6:
                mm[i][8] = bit
            elif i < 8:
                mm[i + 1][8] = bit
            else:
                mm[size - 15 + i][8] = bit
        for i in range(15):
            bit = (f >> i) & 1
            if i < 8:
                mm[8][size - i - 1] = bit
            elif i < 9:
                mm[8][15 - i - 1 + 1] = bit
            else:
                mm[8][15 - i - 1] = bit
        mm[size - 8][8] = 1

    best, best_score = None, None
    for m in (range(8) if mask is None else [mask]):
        cand = [row[:] for row in mat]
        for r in range(size):
            for c in range(size):
                if not func[r][c] and MASK_FN[m](r, c):
                    cand[r][c] ^= 1
        place_format(cand, m)
        sc = penalty(cand)
        if best_score is None or sc < best_score:
            best, best_score = (cand, m), sc
    return {"matrix": best[0], "mask": best[1], "version": version, "ecc": ecc,
            "size": size, "payload": payload, "data_modules": idx}


def penalty(m):
    size = len(m)
    score = 0
    for line in list(m) + [list(col) for col in zip(*m)]:
        run, prev = 1, line[0]
        for v in line[1:]:
            if v == prev:
                run += 1
            else:
                if run >= 5:
                    score += 3 + run - 5
                run, prev = 1, v
        if run >= 5:
            score += 3 + run - 5
        s = "".join(map(str, line))
        score += 40 * (s.count("10111010000") + s.count("00001011101"))
    for i in range(size - 1):
        for j in range(size - 1):
            if m[i][j] == m[i][j + 1] == m[i + 1][j] == m[i + 1][j + 1]:
                score += 3
    dark = sum(map(sum, m))
    pct = dark * 100.0 / (size * size)
    score += 10 * int(abs(pct - 50) // 5)
    return score


# ---------------- 自检解码 ----------------
def decode(info):
    mat, size = info["matrix"], info["size"]
    version, ecc, mask = info["version"], info["ecc"], info["mask"]
    func = [[False] * size for _ in range(size)]

    def mark(i, j):
        if 0 <= i < size and 0 <= j < size:
            func[i][j] = True
    for r, c in ((0, 0), (0, size - 7), (size - 7, 0)):
        for i in range(-1, 8):
            for j in range(-1, 8):
                mark(r + i, c + j)
    for i in range(size):
        mark(6, i); mark(i, 6)
    cen = ALIGN[version]
    finders = [(0, 0), (0, size - 7), (size - 7, 0)]

    def hits_finder(r, c):
        for fr, fc in finders:
            if r - 2 <= fr + 7 and fr - 1 <= r + 2 and c - 2 <= fc + 7 and fc - 1 <= c + 2:
                return True
        return False

    for r in cen:
        for c in cen:
            if hits_finder(r, c):
                continue
            for i in range(-2, 3):
                for j in range(-2, 3):
                    mark(r + i, c + j)
    for i in range(9):
        mark(8, i); mark(i, 8)
    for i in range(8):
        mark(8, size - 1 - i); mark(size - 1 - i, 8)
    if version >= 7:
        for i in range(18):
            mark(size - 11 + i % 3, i // 3); mark(i // 3, size - 11 + i % 3)
    for r, c in ((8, size - 8), (size - 8, 8)):
        mark(r, c)

    bits, col, upward = [], size - 1, True
    while col > 0:
        if col == 6:
            col -= 1
        rows = range(size - 1, -1, -1) if upward else range(size)
        for r in rows:
            for c in (col, col - 1):
                if not func[r][c]:
                    bits.append(mat[r][c] ^ (1 if MASK_FN[mask](r, c) else 0))
        upward = not upward
        col -= 2
    cws = [int("".join(map(str, bits[i:i + 8])), 2) for i in range(0, len(bits) - 7, 8)]

    g1, d1, g2, d2, ecw = SPEC[version][ecc]
    nb = g1 + g2
    datas = [[0] * d1 for _ in range(g1)] + [[0] * d2 for _ in range(g2)]
    ecs = [[0] * ecw for _ in range(nb)]
    p = 0
    for i in range(max(d1, d2)):
        for b in range(nb):
            if i < len(datas[b]):
                datas[b][i] = cws[p]; p += 1
    for i in range(ecw):
        for b in range(nb):
            ecs[b][i] = cws[p]; p += 1

    synds = [rs_syndrome(datas[b] + ecs[b], ecw) for b in range(nb)]
    ok_rs = all(all(s == 0 for s in sy) for sy in synds)

    stream = [b for d in datas for b in d]
    bb = "".join(format(x, "08b") for x in stream)
    mode = int(bb[0:4], 2)
    cc = 8 if version < 10 else 16
    length = int(bb[4:4 + cc], 2)
    raw = bytes(int(bb[4 + cc + 8 * i:4 + cc + 8 * i + 8], 2) for i in range(length))
    return {"ok_rs": ok_rs, "mode": mode, "text": raw.decode("utf-8", "replace"),
            "syndromes_zero": sum(1 for s in synds if all(x == 0 for x in s)), "blocks": nb}


def to_png(info, path, scale=10, border=4):
    from PIL import Image
    m = info["matrix"]
    n = len(m)
    dot = Image.new("L", (n, n), 255)
    px = dot.load()
    for i in range(n):
        for j in range(n):
            if m[i][j]:
                px[j, i] = 0
    full = Image.new("L", ((n + 2 * border) * scale, (n + 2 * border) * scale), 255)
    big = dot.resize((n * scale, n * scale), Image.NEAREST)
    full.paste(big, (border * scale, border * scale))
    full.save(path)
    return path


if __name__ == "__main__":
    import sys
    text = sys.argv[1] if len(sys.argv) > 1 else "https://shanshui.local/?n=%E6%9E%97%E6%B8%85%E5%92%8C"
    info = build(text, "M")
    d = decode(info)
    print("version", info["version"], "mask", info["mask"], "size", info["size"])
    print("rs_ok", d["ok_rs"], "blocks_ok", d["syndromes_zero"], "/", d["blocks"], "mode", d["mode"])
    print("decoded == input:", d["text"] == text)
    to_png(info, "qr_test.png")
