#!/usr/bin/env python3
"""TabAPI 竞品侦察：traffic（月访问/来源/top关键词）+ backlinks（域名评级/外链来源）"""
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

BASE_URL = os.environ.get("TABAPI_BASE_URL", "https://tabapi.com/api/v1")
PROXY = "http://127.0.0.1:7897"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "outputs" / "seo-audit" / "keywords"
OUT.mkdir(parents=True, exist_ok=True)

COMPETITORS = [
    "alconlighting.com",   # 美国商业建筑照明
    "grnled.com",          # 磁吸轨道照明 + 指南内容
    "tendalighting.com",   # 中国批发制造商（wholesale downlight）
    "waclighting.com",     # 大牌基准
]


def load_key():
    key = os.environ.get("TABAPI_API_KEY", "")
    if key:
        return key
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line.startswith("TABAPI_API_KEY="):
                return line.split("=", 1)[1].strip()
    print("❌ 未找到 TABAPI_API_KEY")
    sys.exit(1)


def get(path, key):
    url = f"{BASE_URL}{path}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {key}", "User-Agent": UA})
    proxy = urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    opener = urllib.request.build_opener(proxy)
    with opener.open(req, timeout=45) as resp:
        return json.loads(resp.read().decode("utf-8"))


def main():
    key = load_key()
    result = {}
    for d in COMPETITORS:
        entry = {}
        for ep, name in [(f"/domains/{d}/traffic?months=3", "traffic"),
                         (f"/domains/{d}/backlinks", "backlinks")]:
            try:
                entry[name] = get(ep, key)
                print(f"[{d}] {name}: OK")
            except Exception as e:
                entry[name] = {"error": str(e)[:150]}
                print(f"[{d}] {name}: ❌ {str(e)[:100]}")
            time.sleep(0.6)
        result[d] = entry
    (OUT / "competitor-recon.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    print("\n保存: outputs/seo-audit/keywords/competitor-recon.json")

    # 摘要打印
    for d, entry in result.items():
        print(f"\n===== {d} =====")
        t = entry.get("traffic") or {}
        if t.get("error"):
            print("  traffic:", t["error"])
        else:
            ov = t.get("overview") or {}
            print(f"  流量: global_rank={ov.get('global_rank')} monthly_visits={ov.get('monthly_visits')}")
            kw = (t.get("keywords") or t.get("top_keywords")) or []
            if kw:
                print("  top 关键词:", [k if isinstance(k, str) else (k.get("keyword") or k.get("query")) for k in kw[:8]])
        b = entry.get("backlinks") or {}
        if b.get("error"):
            print("  backlinks:", b["error"])
        else:
            bo = b.get("overview") or {}
            print(f"  外链: domain_rating={bo.get('domain_rating')} backlinks={bo.get('backlinks')} referring_domains={bo.get('referring_domains')}")
            tops = b.get("top_backlinks") or b.get("backlinks_sample") or []
            for tb in tops[:5]:
                print("    ↳", (tb.get("url") or tb.get("source") or tb.get("domain") or "")[:90])


if __name__ == "__main__":
    main()
