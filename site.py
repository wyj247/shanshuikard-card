# -*- coding: utf-8 -*-
"""一笔山水 · 本地站点。

    python site.py [端口]

浏览器打开 http://127.0.0.1:8000 就能用；同一 WiFi 的手机用 http://<内网IP>:8000
打开同一页，名片上的二维码编的就是这个地址，扫一下就能在手机上看到同一座山。
"""

import sys, os, io, zlib, socket, threading, urllib.parse, http.server

import shanshui
import card

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE = os.path.join(HERE, "_cache")
PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000


def lan_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


# 有公网域名（反代/内网穿透）时设 SHANSHUI_BASE=https://你的域名，二维码就会编它
BASE = os.environ.get("SHANSHUI_BASE") or "http://%s:%d" % (lan_ip(), PORT)
_locks = {}


def cached(kind, name, make):
    os.makedirs(CACHE, exist_ok=True)
    path = os.path.join(CACHE, "%s_%08x.png" % (kind, zlib.crc32(name.encode("utf-8"))))
    if not os.path.exists(path):
        with _locks.setdefault(path, threading.Lock()):
            if not os.path.exists(path):
                tmp = "%s.%d.png" % (path, threading.get_ident())
                make(tmp)
                os.replace(tmp, path)
    return path


def shan_path(name):
    return cached("shan", name, lambda t: shanshui.render(name, t, None))


def card_path(name):
    return cached("card", name, lambda t: card.card(name, t, None, BASE + "/?n={q}"))


def norm(s):
    s = "".join(ch for ch in (s or "") if ch.isprintable()).strip()
    return s[:12]


def page(name):
    if name:
        body = """
  <section class="result">
    <figure>
      <img src="/api/shan?n=__Q__" alt="__NAME__ 的山">
      <figcaption>__NAME__ 的山</figcaption>
    </figure>
    <figure>
      <img src="/api/card?n=__Q__" alt="__NAME__ 的名片">
      <figcaption>名片：右下角二维码指向 <code>__BASE__/?n=__Q__</code></figcaption>
    </figure>
  </section>
  <p class="tip">手机和电脑连同一个 WiFi，用手机相机扫上面名片的二维码，就会在手机上打开同一座山。
    也可以直接下载：<a href="/api/shan?n=__Q__" download>山</a> ·
    <a href="/api/card?n=__Q__" download>名片</a></p>"""
        body = (body.replace("__Q__", urllib.parse.quote(name))
                    .replace("__NAME__", esc(name))
                    .replace("__BASE__", BASE))
    else:
        body = ('<p class="tip">在下面写一个名字：同名出同一座山，' +
                '因为名字本身就是这幅画的种子。</p>' +
                '<p class="tip small">试试：林清和 · 江雪 · 顾南枝 · 岳峰 · 沈砚秋 · 王曜军</p>')

    return """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>一笔山水</title>
<style>
  :root { color-scheme: light; }
  * { box-sizing: border-box; }
  body { margin: 0; background: #f3ecdd; color: #2b2f30;
         font-family: "KaiTi", "STKaiti", "Songti SC", serif; }
  .wrap { max-width: 1040px; margin: 0 auto; padding: 40px 20px 64px; }
  h1 { font-size: 30px; letter-spacing: .34em; font-weight: 400; margin: 0 0 6px; }
  .sub { color: #6f6a5c; letter-spacing: .18em; font-size: 13px; margin-bottom: 26px; }
  form { display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 26px; }
  input { flex: 1 1 220px; min-width: 0; padding: 12px 14px; font: inherit; font-size: 17px;
          background: #fbf7ee; border: 1px solid #c9bfa6; border-radius: 6px; color: inherit; }
  input:focus { outline: 2px solid #9c8f74; outline-offset: -1px; }
  button { padding: 12px 22px; font: inherit; font-size: 17px; letter-spacing: .2em;
           background: #2f3436; color: #f6f1e4; border: 0; border-radius: 6px; cursor: pointer; }
  button:active { transform: translateY(1px); }
  .result { display: grid; grid-template-columns: 1fr 1fr; gap: 18px; }
  @media (max-width: 760px) { .result { grid-template-columns: 1fr; } }
  figure { margin: 0; background: #fbf7ee; border: 1px solid #ddd3bd; border-radius: 8px; padding: 10px; }
  figure img { width: 100%; height: auto; display: block; border-radius: 4px; }
  figcaption { font-size: 12px; color: #6f6a5c; margin-top: 8px; word-break: break-all; }
  .tip { color: #5c5747; font-size: 14px; line-height: 1.9; margin: 18px 0 0; }
  .tip.small { font-size: 13px; color: #857e6b; }
  code { font-family: ui-monospace, Consolas, monospace; font-size: 11px; }
</style></head><body><div class="wrap">
  <h1>一笔山水</h1>
  <div class="sub">写一个名字，得一座山</div>
  <form method="get" action="/">
    <input name="n" value="__VAL__" placeholder="你的名字" maxlength="12" autocomplete="off">
    <button type="submit">画 山</button>
  </form>
  __BODY__
</div></body></html>""".replace("__VAL__", esc(name)).replace("__BODY__", body)


def esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
             .replace('"', "&quot;"))


class App(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "YiBiShanShui/1.0"

    def log_message(self, fmt, *args):
        sys.stderr.write("  %s %s\n" % (self.command, self.path.split("?")[0]))

    def _bytes(self, data, ctype, extra=""):
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "public, max-age=86400" + extra)
        self.end_headers()
        self.wfile.write(data)

    def _file(self, path, ctype):
        with open(path, "rb") as f:
            self._bytes(f.read(), ctype)

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        name = norm(urllib.parse.parse_qs(u.query).get("n", [""])[0])
        try:
            if u.path == "/api/shan" and name:
                return self._file(shan_path(name), "image/png")
            if u.path == "/api/card" and name:
                return self._file(card_path(name), "image/png")
            if u.path in ("/", "/index.html"):
                return self._bytes(page(name).encode("utf-8"), "text/html; charset=utf-8")
            if u.path == "/favicon.ico":
                self.send_response(204)
                self.send_header("Content-Length", "0")
                self.end_headers()
                return
            self.send_error(404)
        except Exception as e:                       # noqa: BLE001
            msg = ("出错了：%s" % e).encode("utf-8")
            self.send_response(500)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Content-Length", str(len(msg)))
            self.end_headers()
            self.wfile.write(msg)


class Server(http.server.ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True


if __name__ == "__main__":
    srv = Server(("0.0.0.0", PORT), App)
    print("")
    print("  一笔山水 · 本地站点已启动")
    print("    本机   http://127.0.0.1:%d" % PORT)
    print("    手机   %s   （要和电脑同一个 WiFi）" % BASE)
    print("    名片上的二维码就编这个地址。Ctrl+C 停止。")
    print("")
    try:
        srv.serve_forever()
    except KeyboardInterrupt:
        print("  已停止")
