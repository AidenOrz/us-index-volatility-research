# -*- coding: utf-8 -*-
"""一键刷新：抓 CBOE 最新数据 → 重算指标 → 重生成 dashboard.json。

用法：
    python scripts\refresh_dashboard.py            # 只刷新数据
    python scripts\refresh_dashboard.py --build    # 刷新后顺便重建 web

CBOE 的 cdn.cboe.com 本机可直连；若价格接口需要代理，会自动尝试常见端口，
全部失败时沿用本地已有的 prices_close.csv（不会中断）。
"""
import os, sys, io, csv, urllib.request, subprocess, datetime, shutil

sys.stdout.reconfigure(encoding="utf-8")

ROOT = r"E:\workspace\new"
CBOE = os.path.join(ROOT, "data", "raw", "cboe_vol")
FLUTTER = r"E:\flutter_dl\sdk\flutter\bin\flutter.bat"
APP = os.path.join(ROOT, "flutter_app")

TICKERS = ["VIX", "VIX3M", "VIX9D", "VIX6M", "VXN", "RVX", "VVIX", "SKEW",
           "OVX", "GVZ", "VXAPL", "VXAZN", "VXGOG", "VXGS", "VXIBM",
           "VXEEM", "VXEWZ", "VXSLV", "VXHYG", "VXTLT", "VXGDX", "VXFXI", "VXEFA"]

BASE = "https://cdn.cboe.com/api/global/us_indices/daily_prices/{t}_History.csv"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"


def fetch(url, timeout=40):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def refresh_cboe():
    ok, fail = 0, []
    for t in TICKERS:
        dst = os.path.join(CBOE, t + "_History.csv")
        try:
            data = fetch(BASE.format(t=t))
            if len(data) < 500:
                raise ValueError("too small")
            # 校验：最后一行日期必须是 2000 年之后
            last = data.decode("utf-8", "ignore").strip().splitlines()[-1]
            y = last.split(",")[0].split("/")[-1]
            if not y.isdigit() or int(y) < 2000:
                raise ValueError("bad tail: " + last[:40])
            with open(dst, "wb") as f:
                f.write(data)
            ok += 1
            print(f"  {t:8s} OK  tail={last[:24]}")
        except Exception as e:
            fail.append(t)
            print(f"  {t:8s} FAIL {e}")
    print(f"CBOE: {ok} 成功 / {len(fail)} 失败 {fail if fail else ''}")
    return ok, fail


def refresh_cftc():
    """从 CFTC Socrata 拉最新一周持仓（失败不致命）。"""
    try:
        subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "fetch_cftc_tff.py")],
                       check=False, timeout=180)
    except Exception as e:
        print("COT 跳过:", e)


def refresh_prices():
    """更新指数收盘价；需要外网，失败则沿用缓存。"""
    try:
        subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "refresh_prices.py")],
                       check=False, timeout=300)
    except Exception as e:
        print("价格刷新跳过（沿用本地缓存）:", e)


def build_json():
    subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "build_dashboard_json.py")],
                   check=True, timeout=600)


def build_web():
    env = dict(os.environ)
    env["PUB_HOSTED_URL"] = "https://pub.flutter-io.cn"
    env["FLUTTER_STORAGE_BASE_URL"] = "https://storage.flutter-io.cn"
    print("构建 Web ...")
    subprocess.run([FLUTTER, "build", "web", "--release"], cwd=APP, env=env, check=False)
    print("构建 Windows ...")
    subprocess.run([FLUTTER, "build", "windows", "--release"], cwd=APP, env=env, check=False)


def main():
    t0 = datetime.datetime.now()
    print("=" * 60)
    print("波动率看盘 · 数据刷新", t0.strftime("%Y-%m-%d %H:%M:%S"))
    print("=" * 60)

    print("\n[1/4] 增量补齐（缺口检测 + 多源回退 + 交叉校验）")
    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        import fill_gaps
        rep = fill_gaps.run(verbose=True, allow_proxy=True)
        if not rep.get("ok"):
            print("  注意：有数据源失败，明细见上")
    except Exception as e:
        print("  补齐引擎异常:", e)
        print("  回退到全量抓取模式")
        refresh_cboe()

    print("\n[2/4] CFTC 持仓")
    refresh_cftc()

    print("\n[3/4] 指数收盘价")
    refresh_prices()

    print("\n[4/4] 重算指标并生成 dashboard.json")
    build_json()

    if "--build" in sys.argv:
        print("\n[+] 重建应用")
        build_web()

    dt = (datetime.datetime.now() - t0).total_seconds()
    print(f"\n完成，耗时 {dt:.1f}s")


if __name__ == "__main__":
    main()