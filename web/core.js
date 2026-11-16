
/* 一笔山水 —— 浏览器端渲染器（与 shanshui.py 同一套参数）
   用法： ShanShui.render(canvas, name, seed) */
(function (global) {
'use strict';
var PAPER = [245, 239, 226];

var POEMS = [
  ["空山新雨后", "清泉石上流"], ["行到水穷处", "坐看云起时"],
  ["明月松间照", "清泉石上流"], ["山色有无中", "江流天地外"],
  ["白云回望合", "青霭入看无"], ["松风吹解带", "山月照弹琴"],
  ["孤舟蓑笠翁", "独钓寒江雪"], ["野旷天低树", "江清月近人"],
  ["山随平野尽", "江入大荒流"], ["泉声咽危石", "日色冷青松"],
  ["千山鸟飞绝", "万径人踪灭"], ["江流石不转", "山高月小"],
  ["星垂平野阔", "月涌大江流"], ["寒山转苍翠", "秋水日潺湲"],
  ["野径云俱黑", "江船火独明"], ["风鸣两岸叶", "月照一孤舟"],
  ["山光忽西落", "池月渐东上"], ["月下飞天镜", "云生结海楼"],
  ["春潮带雨晚来急", "野渡无人舟自横"], ["白云生处有人家", "远上寒山石径斜"]
];

var PALETTES = [
  [[180,182,177],[152,157,152],[112,120,116],[76,86,86],[40,48,50]],
  [[190,198,189],[154,172,160],[106,134,122],[66,98,94],[34,58,60]],
  [[198,188,174],[174,154,134],[140,114,94],[104,80,62],[66,50,42]]
];

var TAG_CHARS = {
  "水":"江河水清溪涵泽涛波澜洲湖海源润滋沐沙沈温湘洛淮洋浦",
  "木":"林松柏梅枝桐杨柳枫楠椿榕槿杭楚柯棠森",
  "山":"山岳峰峦岭岩峻巍崖岚嶂崇岐",
  "日":"日昭曜晖昕晨曦阳旭晟熙暖照",
  "月":"月明朔望朗胧朦",
  "雪":"雪霜冰寒凝",
  "雨":"雨霖霏露霭",
  "云":"云霞雯霁雾",
  "舟":"舟帆航渡船",
  "鸟":"鸟雁鸿鹤鹏燕鸾鸢",
  "素":"白素玄墨",
  "秋":"秋",
  "春":"春"
};

var POEM_KEYS = {"水":"江河泉流雨水清","木":"松林树","山":"山","日":"日",
  "月":"月明","雪":"雪寒","雨":"雨","云":"云","舟":"舟",
  "鸟":"鸟","素":"白","秋":"秋","春":"春"};

var TAG_WEIGHT = {"雪":3,"秋":3,"春":3,"舟":2,"日":2,"月":2,
  "鸟":2,"雨":1,"云":1,"山":1,"水":1,"木":1,"素":1};

/* ---------- CPython 的 random.Random(seed) ---------- */
function MT(seed) {
  var N = 624, mt = new Uint32Array(N), mti = N + 1;
  function initGenrand(s) {
    mt[0] = s >>> 0;
    for (mti = 1; mti < N; mti++) {
      var p = mt[mti - 1] ^ (mt[mti - 1] >>> 30);
      mt[mti] = (Math.imul(1812433253, p) + mti) >>> 0;
    }
  }
  function initByArray(key) {
    var i, j, k, N1 = N - 1;
    initGenrand(19650218);
    i = 1; j = 0;
    k = Math.max(N, key.length);
    for (; k; k--) {
      var p = mt[i - 1] ^ (mt[i - 1] >>> 30);
      mt[i] = ((mt[i] ^ Math.imul(p, 1664525)) + key[j] + j) >>> 0;
      i++; j++;
      if (i >= N) { mt[0] = mt[N1]; i = 1; }
      if (j >= key.length) j = 0;
    }
    for (k = N1; k; k--) {
      var q = mt[i - 1] ^ (mt[i - 1] >>> 30);
      mt[i] = ((mt[i] ^ Math.imul(q, 1566083941)) - i) >>> 0;
      i++;
      if (i >= N) { mt[0] = mt[N1]; i = 1; }
    }
    mt[0] = 0x80000000;
  }
  function genrand() {
    var y, mag01 = [0, 0x9908b0df];
    if (mti >= N) {
      var kk;
      for (kk = 0; kk < N - 397; kk++) {
        y = (mt[kk] & 0x80000000) | (mt[kk + 1] & 0x7fffffff);
        mt[kk] = mt[kk + 397] ^ (y >>> 1) ^ mag01[y & 1];
      }
      for (; kk < N - 1; kk++) {
        y = (mt[kk] & 0x80000000) | (mt[kk + 1] & 0x7fffffff);
        mt[kk] = mt[kk + (397 - N)] ^ (y >>> 1) ^ mag01[y & 1];
      }
      y = (mt[N - 1] & 0x80000000) | (mt[0] & 0x7fffffff);
      mt[N - 1] = mt[397 - 1] ^ (y >>> 1) ^ mag01[y & 1];
      mti = 0;
    }
    y = mt[mti++];
    y ^= (y >>> 11);
    y ^= (y << 7) & 0x9d2c5680;
    y ^= (y << 15) & 0xefc60000;
    y ^= (y >>> 18);
    return y >>> 0;
  }
  // seed 为 <2^32 的非负整数 → key=[seed]
  initByArray([seed >>> 0]);
  var api = {
    random: function () {
      var a = genrand() >>> 5, b = genrand() >>> 6;
      return (a * 67108864 + b) / 9007199254740992;
    },
    getrandbits: function (k) {
      return k <= 32 ? (genrand() >>> (32 - k)) : genrand();
    },
    randbelow: function (n) {
      var k = 0, c = n;
      while (c) { k++; c >>>= 1; }
      for (;;) {
        var r = api.getrandbits(k);
        if (r < n) return r;
      }
    },
    uniform: function (a, b) { return a + (b - a) * api.random(); },
    choice: function (seq) { return seq[api.randbelow(seq.length)]; },
    choices: function (pop, weights) {
      var cum = [], t = 0, i;
      for (i = 0; i < pop.length; i++) { t += weights[i]; cum.push(t); }
      var r = api.random() * t, lo = 0, hi = cum.length;
      while (lo < hi) {
        var mid = (lo + hi) >>> 1;
        if (cum[mid] > r) hi = mid; else lo = mid + 1;
      }
      if (lo >= pop.length) lo = pop.length - 1;
      return pop[lo];
    },
    randint: function (a, b) { return a + api.randbelow(b - a + 1); }
  };
  return api;
}

/* ---------- 字象 ---------- */
function imagery(name) {
  var out = [];
  for (var t in TAG_CHARS) {
    var chars = TAG_CHARS[t];
    for (var i = 0; i < name.length; i++) {
      if (chars.indexOf(name[i]) >= 0) { out.push(t); break; }
    }
  }
  return out;
}

function pickPoem(rng, tags, avoid) {
  var pool = POEMS.filter(function (p) {
    var txt = p[0] + p[1];
    for (var i = 0; i < avoid.length; i++) if (txt.indexOf(avoid[i]) >= 0) return false;
    return true;
  });
  if (!pool.length) pool = POEMS;
  var scored = pool.map(function (p) {
    var text = {};
    for (var i = 0; i < p[0].length; i++) text[p[0][i]] = 1;
    for (var j = 0; j < p[1].length; j++) text[p[1][j]] = 1;
    var sc = 0;
    for (var t = 0; t < tags.length; t++) {
      var keys = POEM_KEYS[tags[t]] || "", n = 0;
      for (var ch in text) if (keys.indexOf(ch) >= 0) n++;
      sc += (TAG_WEIGHT[tags[t]] || 1) * n;
    }
    return { sc: sc, p: p };
  });
  var best = -1;
  scored.forEach(function (s) { if (s.sc > best) best = s.sc; });
  var cands;
  if (best >= 2) cands = scored.filter(function (s) { return s.sc >= best - 1; });
  else if (best === 1) cands = scored.filter(function (s) { return s.sc === 1; });
  else cands = scored;
  return rng.choices(cands.map(function (s) { return s.p; }),
                     cands.map(function (s) { return Math.pow(s.sc + 1, 3); }));
}

/* ---------- 噪声 ---------- */
function smoothNoise(rng, W, n) {
  n = n || 40;
  var vals = new Float64Array(n), i;
  for (i = 0; i < n; i++) vals[i] = rng.random();
  var out = new Float64Array(W), mean = 0;
  for (i = 0; i < W; i++) {
    var x = (n - 1) * i / (W - 1);
    var i0 = Math.floor(x), i1 = Math.min(i0 + 1, n - 1);
    var f = x - i0; f = f * f * (3 - 2 * f);
    out[i] = vals[i0] * (1 - f) + vals[i1] * f;
    mean += out[i];
  }
  mean /= W;
  for (i = 0; i < W; i++) out[i] -= mean;
  return out;
}

function noise2(rng, W, H, gh, gw) {
  var g = new Float64Array(gh * gw), i;
  for (i = 0; i < gh * gw; i++) g[i] = rng.random();
  var x0 = new Int32Array(W), x1 = new Int32Array(W), fx = new Float64Array(W);
  for (i = 0; i < W; i++) {
    var xi = (gw - 1) * i / (W - 1);
    var a = Math.floor(xi), b = Math.min(a + 1, gw - 1);
    var f = xi - a; f = f * f * (3 - 2 * f);
    x0[i] = a; x1[i] = b; fx[i] = f;
  }
  return { g: g, gh: gh, gw: gw, x0: x0, x1: x1, fx: fx };
}

function massif(rng, W, H, base, count, hmax, side) {
  var xs = new Float64Array(W), i;
  for (i = 0; i < W; i++) xs[i] = i;
  var acc = new Float64Array(W);
  var mc = (side < 0 ? rng.uniform(-0.02, 0.34) : rng.uniform(0.66, 1.02)) * W;
  var u0 = rng.uniform(0.24, 0.42);
  var p0 = rng.uniform(1.5, 2.0);
  for (i = 0; i < W; i++) acc[i] += Math.exp(-Math.pow(Math.abs((xs[i] - mc) / u0) * W, p0));
  for (var k = 0; k < count; k++) {
    var c = rng.uniform(-0.12, 1.12) * W;
    var wdt = rng.uniform(0.09, 0.28) * W;
    var hh = rng.uniform(0.32, 0.92);
    var p = rng.uniform(1.5, 2.3);
    for (i = 0; i < W; i++) acc[i] += hh * Math.exp(-Math.pow(Math.abs((xs[i] - c) / wdt), p));
  }
  var mx = 0;
  for (i = 0; i < W; i++) if (acc[i] > mx) mx = acc[i];
  var jitter = smoothNoise(rng, W, 90);
  var ridge = new Float64Array(W);
  for (i = 0; i < W; i++) {
    var a = Math.min(1, Math.max(0, acc[i] / mx + 0.045 * jitter[i]));
    ridge[i] = base - hmax * Math.pow(a, 0.92);
  }
  return ridge;
}

function strokes(rng, W, H, ridge, base, n, S) {
  var out = new Float64Array(W * H);
  for (var q = 0; q < n; q++) {
    var sx = rng.uniform(6, W - 6);
    var i = Math.trunc(sx);
    var sy = ridge[i] + rng.uniform(6, 240);
    if (sy > base + 10 || sy > H - 30) continue;
    var slope = (ridge[Math.min(W - 1, i + 10)] - ridge[Math.max(0, i - 10)]) / 20.0;
    slope = Math.min(1.6, Math.max(-1.6, slope));
    var ang = Math.atan(slope) + rng.uniform(-0.35, 0.35);
    var L = rng.uniform(12, 34);
    var x2 = sx + Math.cos(ang) * L;
    var y2 = sy + Math.abs(Math.sin(ang)) * L + rng.uniform(3, 12);
    var w = rng.uniform(1.3, 2.4);
    var x0 = Math.max(0, Math.trunc(Math.min(sx, x2) - 6));
    var x1 = Math.min(W, Math.trunc(Math.max(sx, x2) + 7));
    var y0 = Math.max(0, Math.trunc(Math.min(sy, y2) - 6));
    var y1 = Math.min(H, Math.trunc(Math.max(sy, y2) + 7));
    if (x1 <= x0 || y1 <= y0) continue;
    var vx = x2 - sx, vy = y2 - sy, L2 = vx * vx + vy * vy + 1e-6;
    var ww = w * w, amp = rng.uniform(0.5, 1.0);
    for (var yy = y0; yy < y1; yy++) {
      for (var xx = x0; xx < x1; xx++) {
        var t = ((xx - sx) * vx + (yy - sy) * vy) / L2;
        t = t < 0 ? 0 : (t > 1 ? 1 : t);
        var dx = xx - (sx + t * vx), dy = yy - (sy + t * vy);
        var dd = dx * dx + dy * dy;
        out[yy * W + xx] += Math.exp(-dd / ww) * amp;
      }
    }
  }
  return out;
}

/* ---------- 数值主体：天、日月、五层山、水 ---------- */
function numeric(name, seed, rngIn) {
  var rng = rngIn || MT(seed >>> 0);
  var fmt = rng.choices(["横", "方", "立"], [55, 25, 20]);
  var WH = { "横": [1600, 1000], "方": [1250, 1250], "立": [1000, 1400] }[fmt];
  var W = WH[0], H = WH[1];
  var S = Math.min(W, H) / 1000;
  var tags = imagery(name);

  var forceMoon = null, avoid = [];
  if (tags.indexOf("日") >= 0) { forceMoon = "日"; avoid = ["月"]; }
  else if (tags.indexOf("月") >= 0) { forceMoon = "月"; avoid = ["日"]; }
  else if (tags.indexOf("雪") >= 0) { forceMoon = "无"; avoid = ["日", "月"]; }

  var poem = pickPoem(rng, tags, avoid), l1 = poem[0], l2 = poem[1];
  var ptxt = l1 + l2;

  var pal;
  if (tags.indexOf("春") >= 0) pal = PALETTES[1];
  else if (tags.indexOf("秋") >= 0) pal = PALETTES[2];
  else if (tags.indexOf("雪") >= 0) pal = PALETTES[0];
  else pal = rng.choices(PALETTES, [0.58, 0.26, 0.16]);

  if (tags.indexOf("雪") >= 0) {
    pal = pal.map(function (c) {
      return [Math.trunc(c[0] + (252 - c[0]) * 0.42),
              Math.trunc(c[1] + (252 - c[1]) * 0.42),
              Math.trunc(c[2] + (252 - c[2]) * 0.42)];
    });
  }

  var weather;
  if (tags.indexOf("雨") >= 0 || ptxt.indexOf("雨") >= 0) weather = "雨";
  else if (tags.indexOf("云") >= 0 || tags.indexOf("雪") >= 0) weather = "雾";
  else weather = rng.choices(["晴", "雾", "雨"], [0.58, 0.27, 0.15]);

  var side = rng.choice([-1, 1]);

  var moon;
  if (forceMoon) moon = forceMoon;
  else if (ptxt.indexOf("月") >= 0) moon = "月";
  else if (ptxt.indexOf("日") >= 0) moon = "日";
  else moon = rng.choices(["日", "月", "无"], [0.42, 0.36, 0.22]);

  var withBoat = tags.indexOf("舟") >= 0 || ptxt.indexOf("舟") >= 0 ? true
    : tags.indexOf("水") >= 0 ? rng.random() < 0.85 : rng.random() < 0.62;
  var withPines = tags.indexOf("木") >= 0 ? true : rng.random() < 0.70;
  var withBirds = tags.indexOf("雪") >= 0 ? false
    : (tags.indexOf("鸟") >= 0 || ptxt.indexOf("鸟") >= 0) ? true : rng.random() < 0.70;

  var img = new Float32Array(W * H * 3);
  var x, y, i;
  var skyA = [250, 246, 235], skyB = [234, 229, 215];
  for (y = 0; y < H; y++) {
    var t = Math.min(1, Math.max(0, y / (H * 0.9)));
    var r0 = skyA[0] * (1 - t) + skyB[0] * t;
    var g0 = skyA[1] * (1 - t) + skyB[1] * t;
    var b0 = skyA[2] * (1 - t) + skyB[2] * t;
    for (x = 0; x < W; x++) {
      i = (y * W + x) * 3;
      img[i] = r0; img[i + 1] = g0; img[i + 2] = b0;
    }
  }

  if (moon !== "无") {
    var mx = rng.uniform(0.50, 0.84) * W;
    if (Math.abs(mx - (side < 0 ? 0.86 : 0.14) * W) < 0.20 * W) mx = W - mx;
    var my = rng.uniform(0.10, 0.19) * H;
    var mr = rng.uniform(0.036, 0.052) * Math.min(W, H) * 1.6;
    for (y = 0; y < H; y++) {
      var dy0 = y - my;
      if (dy0 > mr + 3 * S || dy0 < -mr - 3 * S) continue;
      for (x = 0; x < W; x++) {
        var dx0 = x - mx;
        var d = Math.sqrt(dx0 * dx0 + dy0 * dy0);
        if (d > mr + 6 * S) continue;
        i = (y * W + x) * 3;
        if (moon === "日") {
          var soft = Math.min(1, Math.max(0, (mr - d) / (2.0 * S))) * 0.38;
          img[i] = img[i] * (1 - soft) + 198 * soft;
          img[i + 1] = img[i + 1] * (1 - soft) + 104 * soft;
          img[i + 2] = img[i + 2] * (1 - soft) + 88 * soft;
        } else {
          var s1 = Math.min(1, Math.max(0, (mr - d) / (2.0 * S))) * 0.85;
          img[i] = img[i] * (1 - s1) + 236 * s1;
          img[i + 1] = img[i + 1] * (1 - s1) + 234 * s1;
          img[i + 2] = img[i + 2] * (1 - s1) + 226 * s1;
          var e = Math.exp(-Math.pow((d - mr) / (2.2 * S), 2)) * 0.22;
          img[i] = img[i] * (1 - e) + 150 * e;
          img[i + 1] = img[i + 1] * (1 - e) + 152 * e;
          img[i + 2] = img[i + 2] * (1 - e) + 148 * e;
        }
      }
    }
  }

  var baseF = [0.360, 0.455, 0.560, 0.680, 0.800];
  var hmaxF = [0.235, 0.305, 0.350, 0.385, 0.365];
  var alphas = [0.34, 0.48, 0.64, 0.82, 0.94];
  var mistBase = { "晴": 0.54, "雾": 0.68, "雨": 0.64 }[weather] + (tags.indexOf("雪") >= 0 ? 0.10 : 0);
  var peak = tags.indexOf("山") >= 0 ? 1.13 : 1.0;
  var ridges = [];

  for (var layer = 0; layer < 5; layer++) {
    var base = baseF[layer] * H;
    var ridge = massif(rng, W, H, base, layer < 4 ? 3 : 4, hmaxF[layer] * H * peak, layer >= 2 ? side : -side);
    ridges.push(ridge);
    var tex = noise2(rng, W, H, 26, 16);
    var col = pal[layer];
    var cr = col[0], cg = col[1], cb = col[2];
    var dr2 = cr * 0.62, dg2 = cg * 0.62, db2 = cb * 0.62;
    var br = cr * 0.55, bg = cg * 0.55, bb = cb * 0.55;
    var al = alphas[layer];
    var texLo = 0.64, texHi = 1.36;

    for (y = 0; y < H; y++) {
      var yi = (tex.gh - 1) * y / (H - 1);
      var ya = Math.floor(yi), yb = Math.min(ya + 1, tex.gh - 1);
      var fy = yi - ya; fy = fy * fy * (3 - 2 * fy);
      var rowA = ya * tex.gw, rowB = yb * tex.gw;
      for (x = 0; x < W; x++) {
        var dd = y - ridge[x];
        if (dd < -2 * S) continue;
        var edge = dd / (2.5 * S); edge = edge > 1 ? 1 : edge;
        var fxf = tex.fx[x], xa = tex.x0[x], xb2 = tex.x1[x];
        var top = tex.g[rowA + xa] * (1 - fxf) + tex.g[rowA + xb2] * fxf;
        var bot = tex.g[rowB + xa] * (1 - fxf) + tex.g[rowB + xb2] * fxf;
        var tv = (top * (1 - fy) + bot * fy) * (texHi - texLo) + texLo;
        var fade = 1 - 0.50 * Math.min(1, Math.max(0, (dd - 30 * S) / (300 * S)));
        var a = al * edge * fade * tv;
        if (a > 0.0005) {
          i = (y * W + x) * 3;
          img[i] = img[i] * (1 - a) + cr * a;
          img[i + 1] = img[i + 1] * (1 - a) + cg * a;
          img[i + 2] = img[i + 2] * (1 - a) + cb * a;
        }
        var sp = (dd - 1.5 * S) / (3.2 * S);
        var ar = al * 0.45 * Math.exp(-sp * sp);
        if (ar > 0.0005) {
          img[i] = img[i] * (1 - ar) + dr2 * ar;
          img[i + 1] = img[i + 1] * (1 - ar) + dg2 * ar;
          img[i + 2] = img[i + 2] * (1 - ar) + db2 * ar;
        }
      }
    }

    var brush = strokes(rng, W, H, ridge, base, layer === 4 ? 170 : 70, S);
    for (y = 0; y < H; y++) {
      for (x = 0; x < W; x++) {
        var bv = brush[y * W + x];
        if (bv <= 0.001) continue;
        var dd2 = y - ridge[x];
        var e2 = dd2 / (2.5 * S); e2 = Math.min(1, Math.max(0, e2));
        var k2 = Math.min(1, Math.max(0, 1 - (dd2 - 16 * S) / (260 * S)));
        var a2 = bv * al * e2 * k2 * 0.60;
        if (a2 > 0.0005) {
          i = (y * W + x) * 3;
          img[i] = img[i] * (1 - a2) + br * a2;
          img[i + 1] = img[i + 1] * (1 - a2) + bg * a2;
          img[i + 2] = img[i + 2] * (1 - a2) + bb * a2;
        }
      }
    }

    var cen = smoothNoise(rng, W, 26);
    var sig = rng.uniform(40, 62) * S * (weather === "雾" ? 1.25 : 1);
    var band = noise2(rng, W, H, 9, 7);
    var twoSig = 2 * sig * sig;
    for (y = 0; y < H; y++) {
      var yi2 = (band.gh - 1) * y / (H - 1);
      var ya2 = Math.floor(yi2), yb3 = Math.min(ya2 + 1, band.gh - 1);
      var fy2 = yi2 - ya2; fy2 = fy2 * fy2 * (3 - 2 * fy2);
      var rA = ya2 * band.gw, rB = yb3 * band.gw;
      for (x = 0; x < W; x++) {
        var c = cen[x] * 40 * S + base + 14 * S;
        var ex = y - c;
        var bnd = Math.exp(-(ex * ex) / twoSig);
        var f2 = band.fx[x], x2 = band.x0[x], x3 = band.x1[x];
        var tx2 = band.g[rA + x2] * (1 - f2) + band.g[rA + x3] * f2;
        var bx2 = band.g[rB + x2] * (1 - f2) + band.g[rB + x3] * f2;
        var nv = (tx2 * (1 - fy2) + bx2 * fy2) * 1.05 + 0.42;
        var am = Math.min(1, Math.max(0, bnd * nv)) * mistBase;
        if (am > 0.0005) {
          i = (y * W + x) * 3;
          img[i] = img[i] * (1 - am) + PAPER[0] * am;
          img[i + 1] = img[i + 1] * (1 - am) + PAPER[1] * am;
          img[i + 2] = img[i + 2] * (1 - am) + PAPER[2] * am;
        }
      }
    }
  }

  if (weather === "雾") {
    var cy = smoothNoise(rng, W, 12);
    var fogN = noise2(rng, W, H, 6, 5);
    var sig2 = 0.13 * H;
    for (y = 0; y < H; y++) {
      var yi3 = (fogN.gh - 1) * y / (H - 1);
      var ya3 = Math.floor(yi3), yb4 = Math.min(ya3 + 1, fogN.gh - 1);
      var fy3 = yi3 - ya3; fy3 = fy3 * fy3 * (3 - 2 * fy3);
      var rA2 = ya3 * fogN.gw, rB2 = yb4 * fogN.gw;
      for (x = 0; x < W; x++) {
        var cc = 0.60 * H + 40 * S * cy[x];
        var ex2 = y - cc;
        var fg = Math.exp(-(ex2 * ex2) / (2 * sig2 * sig2));
        var f3 = fogN.fx[x], x4 = fogN.x0[x], x5 = fogN.x1[x];
        var t3 = fogN.g[rA2 + x4] * (1 - f3) + fogN.g[rA2 + x5] * f3;
        var b3 = fogN.g[rB2 + x4] * (1 - f3) + fogN.g[rB2 + x5] * f3;
        var nv2 = (t3 * (1 - fy3) + b3 * fy3) * 0.6 + 0.5;
        var am2 = Math.min(1, Math.max(0, fg * nv2)) * 0.32;
        if (am2 > 0.0005) {
          i = (y * W + x) * 3;
          img[i] = img[i] * (1 - am2) + PAPER[0] * am2;
          img[i + 1] = img[i + 1] * (1 - am2) + PAPER[1] * am2;
          img[i + 2] = img[i + 2] * (1 - am2) + PAPER[2] * am2;
        }
      }
    }
  }

  var wyBase = tags.indexOf("水") >= 0 ? 0.760 : (tags.indexOf("山") >= 0 ? 0.815 : 0.800);
  var wyU = rng.uniform(0.0, 0.045);
  var wyN = smoothNoise(rng, W, 18);
  var wy = new Float64Array(W);
  for (x = 0; x < W; x++) wy[x] = (wyBase + wyU) * H + 7.0 * wyN[x];

  for (y = 0; y < H; y++) {
    for (x = 0; x < W; x++) {
      var wd = y - wy[x];
      if (wd < -3 * S) continue;
      var wa = Math.min(1, Math.max(0, wd / (24 * S))) * 0.88;
      if (wa <= 0.0005) continue;
      var wt = Math.min(1, Math.max(0, wd / (H - wy[x])));
      var wr = 209 + (189 - 209) * wt;
      var wg = 214 + (195 - 214) * wt;
      var wb = 210 + (192 - 210) * wt;
      i = (y * W + x) * 3;
      img[i] = img[i] * (1 - wa) + wr * wa;
      img[i + 1] = img[i + 1] * (1 - wa) + wg * wa;
      img[i + 2] = img[i + 2] * (1 - wa) + wb * wa;
      var we = Math.exp(-(wd * wd) / (2 * (24 * S) * (24 * S))) * 0.55;
      if (we > 0.0005) {
        img[i] = img[i] * (1 - we) + PAPER[0] * we;
        img[i + 1] = img[i + 1] * (1 - we) + PAPER[1] * we;
        img[i + 2] = img[i + 2] * (1 - we) + PAPER[2] * we;
      }
    }
  }

  return {
    W: W, H: H, S: S, img: img, ridges: ridges, wy: wy,
    rng: rng,
    st: {
      fmt: fmt, tags: tags, l1: l1, l2: l2, pal: pal, weather: weather,
      side: side, moon: moon, boat: withBoat, pines: withPines, birds: withBirds, seed: seed
    }
  };
}

/* ---------- 纸上的墨：雨、水纹、舟、松、苔、鸟、题款、印 ---------- */
function paintInk(ctx, D, name, rng) {
  var W = D.W, H = D.H, S = D.S, st = D.st, wy = D.wy;

  if (st.weather === "雨") {
    ctx.lineWidth = 1;
    ctx.strokeStyle = "rgba(92,102,100,0.10)";
    for (var q = 0; q < 170; q++) {
      var x0 = rng.uniform(-0.1 * W, W);
      var y0 = rng.uniform(0, H * 0.95);
      var L = rng.uniform(18, 40) * S;
      ctx.beginPath();
      ctx.moveTo(x0, y0);
      ctx.lineTo(x0 - L * 0.45, y0 + L);
      ctx.stroke();
    }
  }

  ctx.lineWidth = 1;
  ctx.strokeStyle = "rgba(108,120,118,0.12)";
  for (var r2 = 0; r2 < 14; r2++) {
    var yy = rng.uniform(wy[0] + 22 * S, H - 12 * S);
    var xx = rng.uniform(0, W * 0.6);
    var x2 = xx + rng.uniform(W * 0.08, W * 0.30);
    ctx.beginPath(); ctx.moveTo(xx, yy); ctx.lineTo(x2, yy); ctx.stroke();
  }

  if (st.boat) {
    var bx = rng.uniform(0.16, 0.72) * W;
    var by = wy[0] + rng.uniform(52, 88) * S;
    var bs = 46 * S;
    ctx.strokeStyle = "rgba(36,42,40,0.84)";
    ctx.lineWidth = Math.max(2, Math.round(3 * S));
    ctx.beginPath();
    ctx.ellipse(bx, by, bs, 12 * S, 0, 0, Math.PI);
    ctx.stroke();
    ctx.strokeStyle = "rgba(36,42,40,0.75)";
    ctx.lineWidth = Math.max(1, Math.round(2 * S));
    ctx.beginPath(); ctx.moveTo(bx - bs, by); ctx.lineTo(bx + bs, by); ctx.stroke();
    ctx.lineWidth = 2;
    ctx.beginPath(); ctx.moveTo(bx - 6 * S, by - 2 * S); ctx.lineTo(bx - 6 * S, by - 46 * S); ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(bx - 6 * S, by - 46 * S);
    ctx.lineTo(bx + 28 * S, by - 20 * S);
    ctx.lineTo(bx - 6 * S, by - 18 * S);
    ctx.closePath();
    ctx.stroke();
  }

  var nr = D.ridges[4];
  if (st.pines) {
    for (var p = 0; p < 18; p++) {
      var tx = rng.uniform(0, W * 0.95);
      var ty = nr[Math.trunc(tx)] + rng.uniform(-4, 8) * S;
      if (ty < wy[0] - 120 * S || rng.random() < 0.42) continue;
      pine(ctx, tx, ty, rng.uniform(22, 44) * S, rng);
    }
  }

  ctx.fillStyle = "rgba(28,34,34,0.43)";
  for (var d2 = 0; d2 < 46; d2++) {
    var px = rng.uniform(0, W);
    var py = nr[Math.trunc(px)] + rng.uniform(2, 90) * S;
    if (py > wy[0] - 8 * S) continue;
    var rr = rng.uniform(1.2, 2.6) * S;
    ctx.beginPath(); ctx.ellipse(px, py, rr, rr, 0, 0, Math.PI * 2); ctx.fill();
  }

  if (st.birds) {
    var nb = rng.randint(2, 4);
    ctx.strokeStyle = "rgba(45,50,48,0.67)";
    ctx.lineWidth = 2;
    for (var b = 0; b < nb; b++) {
      var bx2 = rng.uniform(0.18, 0.82) * W;
      var by2 = rng.uniform(0.09, 0.20) * H;
      var bs2 = rng.uniform(7, 13) * S;
      ctx.beginPath();
      ctx.ellipse(bx2 - bs2 / 2, by2 - bs2 * 0.2, bs2 / 2, bs2 * 0.6, 0, 200 * Math.PI / 180, 340 * Math.PI / 180);
      ctx.stroke();
      ctx.beginPath();
      ctx.ellipse(bx2 + bs2 / 2, by2 - bs2 * 0.2, bs2 / 2, bs2 * 0.6, 0, 200 * Math.PI / 180, 340 * Math.PI / 180);
      ctx.stroke();
    }
  }

  var fs = Math.round(46 * S);
  var gap = Math.round(12 * S);
  var px1, px2, tx1;
  if (st.side < 0) { px1 = 0.872 * W; px2 = 0.812 * W; tx1 = 0.06 * W; }
  else { px1 = 0.128 * W; px2 = 0.188 * W; tx1 = 0.94 * W; }
  var top = 0.126 * H;
  ctx.textAlign = "center";
  ctx.textBaseline = "middle";
  ctx.lineJoin = "round";
  ctx.lineWidth = Math.max(2, Math.round(4 * S)) * 2;
  ctx.strokeStyle = "rgba(245,239,226,0.65)";
  ctx.fillStyle = "rgba(32,38,36,0.89)";
  ctx.font = fs + "px KaiTi, STKaiti, Kaiti SC, serif";
  vtext(ctx, st.l1, px1, top, fs, gap);
  vtext(ctx, st.l2, px2, top, fs, gap);

  var ft = Math.round(36 * S);
  ctx.font = ft + "px KaiTi, STKaiti, Kaiti SC, serif";
  ctx.fillStyle = "rgba(56,52,44,0.78)";
  ctx.strokeStyle = "rgba(245,239,226,0.61)";
  ctx.lineWidth = Math.max(2, Math.round(4 * S)) * 2;
  var title = (name || "山水") + "图";
  for (var i = 0; i < title.length; i++) {
    var ty2 = 0.118 * H + i * (ft + Math.round(10 * S)) + ft / 2;
    ctx.strokeText(title[i], tx1, ty2);
    ctx.fillText(title[i], tx1, ty2);
  }

  var ss = Math.round(54 * S);
  var sx = px1 + (st.side < 0 ? 10 * S : -10 * S);
  var sy = top + 5 * (fs + gap) + 56 * S;
  ctx.fillStyle = "rgba(170,54,44,0.91)";
  ctx.fillRect(sx - ss / 2, sy, ss, ss);
  ctx.font = Math.round(33 * S) + "px KaiTi, STKaiti, Kaiti SC, serif";
  ctx.fillStyle = "rgba(246,240,227,0.96)";
  ctx.fillText((name || "山").slice(-1), sx, sy + ss / 2);
  ctx.font = Math.round(22 * S) + "px KaiTi, STKaiti, Kaiti SC, serif";
  ctx.fillStyle = "rgba(62,57,46,0.69)";
  ctx.strokeStyle = "rgba(245,239,226,0.78)";
  ctx.lineWidth = 4;
  var dy = sy + ss + 30 * S + 11 * S;
  ctx.strokeText("丙午冬", sx, dy);
  ctx.fillText("丙午冬", sx, dy);
}

function vtext(ctx, txt, x, y, fs, gap) {
  for (var i = 0; i < txt.length; i++) {
    var cy = y + i * (fs + gap) + fs / 2;
    ctx.strokeText(txt[i], x, cy);
    ctx.fillText(txt[i], x, cy);
  }
}

function pine(ctx, x, y, h, rng) {
  ctx.strokeStyle = "rgba(28,34,34,0.84)";
  ctx.beginPath();
  ctx.moveTo(x, y);
  var px = x, py = y;
  for (var i = 1; i <= 5; i++) {
    var nx = x + Math.sin(i * 1.1 + rng.random()) * h * 0.045;
    var ny = y - h * i / 5.0;
    ctx.lineTo(nx, ny);
    px = nx; py = ny;
  }
  ctx.lineWidth = 2;
  ctx.stroke();
  for (var k = 0; k < 4; k++) {
    var yy = y - h * (0.30 + 0.17 * k);
    var span = h * (0.36 - 0.06 * k);
    if (span < 3) continue;
    for (var sgn = -1; sgn <= 1; sgn += 2) {
      var ex = x + sgn * span, ey = yy + span * 0.30;
      ctx.lineWidth = sgn > 0 ? 2 : 1;
      ctx.beginPath(); ctx.moveTo(x, yy); ctx.lineTo(ex, ey); ctx.stroke();
      for (var t = 0; t < 7; t++) {
        var f = 0.3 + (1.0 - 0.3) * t / 6;
        var bx = x + sgn * span * f, by = yy + span * 0.30 * f;
        var L = 7 + rng.uniform(0, 4);
        ctx.lineWidth = 1;
        ctx.beginPath(); ctx.moveTo(bx, by); ctx.lineTo(bx + sgn * 1.5, by - L); ctx.stroke();
      }
    }
  }
}

/* ---------- 纸纹 + 暗角 ---------- */
function finish(canvas, D, seed) {
  var ctx = canvas.getContext("2d");
  var W = D.W, H = D.H;
  var id = ctx.getImageData(0, 0, W, H);
  var d = id.data;
  var s = (seed >>> 0) || 1;
  function rnd() {
    s ^= s << 13; s >>>= 0; s ^= s >>> 17; s ^= s << 5; s >>>= 0;
    return (s & 0xffff) / 65535;
  }
  for (var y = 0; y < H; y++) {
    var vy = (y - H / 2) / (H * 0.62);
    for (var x = 0; x < W; x++) {
      var vx = (x - W / 2) / (W * 0.62);
      var vg = Math.sqrt(vx * vx + vy * vy);
      var vf = 1 - Math.min(1, Math.max(0, (vg - 0.55) / 0.75)) * 0.22;
      var i = (y * W + x) * 4;
      var g = (rnd() + rnd() + rnd() - 1.5) * 2.4;
      d[i] = Math.max(0, Math.min(255, d[i] * vf + g));
      d[i + 1] = Math.max(0, Math.min(255, d[i + 1] * vf + g));
      d[i + 2] = Math.max(0, Math.min(255, d[i + 2] * vf + g));
    }
  }
  ctx.putImageData(id, 0, 0);
}

function crc32(str) {
  var c, crc = 0xFFFFFFFF;
  for (var i = 0; i < str.length; i++) {
    c = (crc ^ str.charCodeAt(i)) & 0xFF;
    for (var k = 0; k < 8; k++) c = c & 1 ? (c >>> 1) ^ 0xEDB88320 : c >>> 1;
    crc = (crc >>> 8) ^ c;
  }
  return (crc ^ 0xFFFFFFFF) >>> 0;
}

function render(canvas, name, seed) {
  if (seed === undefined || seed === null) seed = crc32(name) % 100000;
  var rng0 = MT(seed >>> 0);
  var D = numeric(name, seed, rng0);
  canvas.width = D.W; canvas.height = D.H;
  var ctx = canvas.getContext("2d");
  var id = ctx.createImageData(D.W, D.H);
  var d = id.data;
  for (var i = 0, n = D.W * D.H; i < n; i++) {
    d[i * 4] = D.img[i * 3];
    d[i * 4 + 1] = D.img[i * 3 + 1];
    d[i * 4 + 2] = D.img[i * 3 + 2];
    d[i * 4 + 3] = 255;
  }
  ctx.putImageData(id, 0, 0);
  paintInk(ctx, D, name, D.rng);
  finish(canvas, D, seed);
  return D;
}

var API = { render: render, numeric: numeric, crc32: crc32, MT: MT, PAPER: PAPER, massif: massif, strokes: strokes };
if (typeof module !== "undefined" && module.exports) module.exports = API;
else global.ShanShui = API;
})(typeof globalThis !== "undefined" ? globalThis : this);