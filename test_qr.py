# -*- coding: utf-8 -*-
"""qr.py 的自检。不联网。
1) v1-v10 的数据模块数必须等于规范值（验证功能图形与铺放几何）
2) 编解码往返
3) 格式信息 / 版本信息 BCH 常数、RS 生成多项式，与公开表比对
历史上还用 api.qrserver.com 的 SVG 逐模块比对过 v1/v5/v7，均完全一致。
"""

import qr

MODULES = {1: 208, 2: 359, 3: 567, 4: 807, 5: 1079, 6: 1383,
           7: 1568, 8: 1936, 9: 2336, 10: 2768}


def main():
    ok = True
    for v in range(1, 11):
        info = qr.build("A", "M", version=v)
        good = info["data_modules"] == MODULES[v]
        ok &= good
        print("v%-2d 模块 %4d / %4d  %s" % (v, info["data_modules"], MODULES[v], "OK" if good else "FAIL"))

    for txt, ecc in [("a", "L"), ("shanshui7", "L"), ("山" * 6, "M"), ("x" * 90, "H")]:
        info = qr.build(txt, ecc)
        d = qr.decode(info)
        good = d["ok_rs"] and d["text"] == txt
        ok &= good
        print("%-10s %s v%d rs=%s 往返=%s" % (txt[:10], ecc, info["version"], d["ok_rs"], d["text"] == txt))

    fmt = {("M", 0): 0x5412, ("L", 0): 0x77C4, ("Q", 0): 0x355F, ("H", 0): 0x1689}
    for (e, m), want in fmt.items():
        got = qr._fmt_bits(e, m)
        ok &= got == want
        print("格式 %s%d %04X / %04X %s" % (e, m, got, want, "OK" if got == want else "FAIL"))
    ok &= qr._ver_bits(7) == 0x07C94 and qr._ver_bits(8) == 0x085BC
    ok &= [qr.LOG[c] for c in qr.rs_generator(7)] == [0, 87, 229, 146, 149, 238, 102, 21]
    ok &= [qr.LOG[c] for c in qr.rs_generator(10)] == [0, 251, 67, 46, 61, 118, 70, 64, 94, 32, 45]
    print("版本码 / RS 生成多项式 比对完成")
    print("全部通过" if ok else "有失败项")


if __name__ == "__main__":
    main()
