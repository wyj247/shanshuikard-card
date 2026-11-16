
const fs = require('fs'), zlib = require('zlib');
const S = require('./core.js');

const TBL = (() => { const t = new Int32Array(256);
  for (let n = 0; n < 256; n++) { let c = n;
    for (let k = 0; k < 8; k++) c = c & 1 ? 0xEDB88320 ^ (c >>> 1) : c >>> 1;
    t[n] = c; } return t; })();
function crc(buf) { let c = 0xFFFFFFFF;
  for (let i = 0; i < buf.length; i++) c = TBL[(c ^ buf[i]) & 0xFF] ^ (c >>> 8);
  return (c ^ 0xFFFFFFFF) >>> 0; }
function chunk(type, data) {
  const len = Buffer.alloc(4); len.writeUInt32BE(data.length);
  const td = Buffer.concat([Buffer.from(type, 'ascii'), data]);
  const cr = Buffer.alloc(4); cr.writeUInt32BE(crc(td));
  return Buffer.concat([len, td, cr]);
}
function writePNG(path, w, h, rgb) {
  const raw = Buffer.alloc((w * 3 + 1) * h);
  for (let y = 0; y < h; y++) {
    raw[y * (w * 3 + 1)] = 0;
    for (let x = 0; x < w; x++) {
      const i = (y * w + x) * 3, o = y * (w * 3 + 1) + 1 + x * 3;
      raw[o] = rgb[i]; raw[o + 1] = rgb[i + 1]; raw[o + 2] = rgb[i + 2];
    }
  }
  const ihdr = Buffer.alloc(13);
  ihdr.writeUInt32BE(w, 0); ihdr.writeUInt32BE(h, 4);
  ihdr[8] = 8; ihdr[9] = 2; ihdr[10] = 0; ihdr[11] = 0; ihdr[12] = 0;
  fs.writeFileSync(path, Buffer.concat([
    Buffer.from([0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A]),
    chunk('IHDR', ihdr), chunk('IDAT', zlib.deflateSync(raw, { level: 6 })),
    chunk('IEND', Buffer.alloc(0))]));
}

function stubCanvas() {
  const calls = {};
  const ctx = new Proxy({}, {
    get(t, k) {
      if (k === 'createImageData') return (w, h) => ({ width: w, height: h, data: new Uint8ClampedArray(w * h * 4) });
      if (k === 'getImageData') return (x, y, w, h) => ({ width: w, height: h, data: new Uint8ClampedArray(w * h * 4) });
      if (k === 'putImageData') return () => {};
      if (k in t) return t[k];
      return () => { calls[k] = (calls[k] || 0) + 1; };
    },
    set(t, k, v) { t[k] = v; return true; }
  });
  return { canvas: { width: 0, height: 0, getContext: () => ctx }, calls };
}

const names = ['林清和', '沈砚秋', '顾南枝', '江照野', '温故', '江雪', '王曜军', '邓涛', '刘宇', '周叙白'];
if (process.argv[2] === 'png') {
  const name = process.argv[3] || '林清和';
  const seed = process.argv[4] ? parseInt(process.argv[4], 10) : S.crc32(name) % 100000;
  const t0 = Date.now();
  const D = S.numeric(name, seed);
  const ms = Date.now() - t0;
  const out = new Uint8Array(D.W * D.H * 3);
  for (let i = 0; i < D.W * D.H * 3; i++) out[i] = Math.max(0, Math.min(255, D.img[i]));
  writePNG(process.argv[5] || '_js.png', D.W, D.H, out);
  console.log(JSON.stringify({ name, seed, size: D.W + 'x' + D.H, ms, st: D.st }));
} else {
  const t0 = Date.now();
  for (const n of names) {
    const sc = stubCanvas();
    const D = S.render(sc.canvas, n, S.crc32(n) % 100000);
    process.stdout.write(n + ':' + D.W + 'x' + D.H + ' ');
  }
  console.log('\nall ok, ' + (Date.now() - t0) + 'ms');
}
