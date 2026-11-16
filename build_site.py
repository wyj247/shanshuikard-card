# -*- coding: utf-8 -*-
"""把一批名字打包成一个纯静态站点，直接丢到 GitHub Pages。

    python build_site.py 站点目录 https://用户名.github.io/仓库名 名字1 名字2 ...

生成：
    站点目录/index.html        名字目录页
    站点目录/n/<crc32>.html    一个人的山（图内嵌，扫码就能看）
    站点目录/names.json        索引，方便以后增量

每个页面里的二维码指向**这个页面自己的地址**，所以名片发给谁都扫得开，
不依赖本机是否开机、是否和对方在同一个 WiFi。
"""

import sys, os, json, zlib, html
import export

INDEX = """<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>名字是一座山</title>
<style>
  :root { color-scheme: light; }
  body { margin: 0; background: #ece4d3; color: #2b2f30;
         font-family: "KaiTi","STKaiti","Songti SC",serif; }
  .wrap { max-width: 720px; margin: 0 auto; padding: 48px 22px 72px; }
  h1 { font-weight: 400; font-size: 26px; letter-spacing: .34em; margin: 0 0 6px; }
  .sub { color: #6d6552; font-size: 13px; letter-spacing: .12em; margin: 0 0 30px; }
  ul { list-style: none; padding: 0; margin: 0; }
  li { border-top: 1px solid rgba(70,64,50,.16); }
  li:last-child { border-bottom: 1px solid rgba(70,64,50,.16); }
  a { display: flex; justify-content: space-between; align-items: baseline;
      padding: 15px 4px; text-decoration: none; color: #2b2f30; font-size: 18px; letter-spacing: .1em; }
  a:hover { background: rgba(255,255,255,.42); }
  a em { font-style: normal; }
  a span { font-size: 12px; color: #8a8270; letter-spacing: .06em; }
  .foot { margin-top: 34px; color: #6d6552; font-size: 13px; line-height: 2; }
  .foot code { background: rgba(255,255,255,.5); padding: 1px 5px; border-radius: 3px; }
</style></head><body><div class="wrap">
  <h1>名字是一座山</h1>
  <p class="sub">__COUNT__ 座 · 同一个名字，永远是同一座山</p>
  <ul>
__ITEMS__
  </ul>
  <div class="foot">
    二维码里编的就是这个页面的地址，别人用手机扫，看到的和这里一样。<br>
    站点根地址：<code>__BASE__</code>
  </div>
</div></body></html>"""

ROW = '<li><a href="%s"><em>%s</em><span>看山 →</span></a></li>'


def page_id(name):
    return "%08x" % (zlib.crc32(name.encode("utf-8")) & 0xffffffff)


def build(outdir, base, names):
    base = base.rstrip("/")
    os.makedirs(os.path.join(outdir, "n"), exist_ok=True)
    rows = []
    for name in names:
        page = "n/%s.html" % page_id(name)
        url = "%s/%s" % (base, page)
        info = export.export(name, os.path.join(outdir, page), url=url)
        rows.append({"name": name, "page": page, "url": url, "bytes": info["bytes"]})
        print("%-10s %8d B  %s" % (name, info["bytes"], url))
    with open(os.path.join(outdir, "names.json"), "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=1)
    items = "\n".join(ROW % (r["page"], html.escape(r["name"])) for r in rows)
    with open(os.path.join(outdir, "index.html"), "w", encoding="utf-8") as f:
        f.write(INDEX.replace("__BASE__", html.escape(base))
                     .replace("__ITEMS__", items)
                     .replace("__COUNT__", str(len(rows))))
    print("\n%d 页 -> %s" % (len(rows), os.path.abspath(outdir)))
    return rows


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(1)
    build(sys.argv[1], sys.argv[2], sys.argv[3:])
